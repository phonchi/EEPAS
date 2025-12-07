#!/usr/bin/env python3
"""
EEPAS Earthquake Forecasting

Generate EEPAS model forecasts combining PPE background rate with
precursory signals from historical earthquakes.

Final forecast: λ = μ·λ₀ + Σ wᵢ·ηᵢ·λᵢ

Each historical earthquake contributes a precursory kernel with temporal
(lognormal), magnitude (Gaussian), and spatial (exponential) distributions.
"""
import numpy as np
import scipy.io as sio
import argparse
import os
import sys
from scipy.special import erf
from scipy.integrate import quad, quad_vec
from numba import jit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.catalog_processor import CatalogProcessor
from utils.region_manager import RegionManager
from utils.get_paths import get_paths
from calculate_earthquake_weights import calculate_earthquake_weights


@jit(nopython=True, cache=True)
def compute_spatial_contribution_fast(X1, X2, Y1, Y2, xee, yee, sigma_spatial,
                                       qq_other, W_use):
    """
    Compute spatial contributions for all grid cells using Numba acceleration.

    Args:
        X1, X2, Y1, Y2: Grid boundary arrays (celln,)
        xee, yee: Event coordinate arrays (n_events,)
        sigma_spatial: Spatial standard deviation array (n_events,)
        qq_other: Product of other contribution terms (scale×magnitude×time×weight) (n_events,)
        W_use: Weight array (n_events,)

    Returns:
        numpy.ndarray: Expected number of events in each grid cell (celln,)
    """
    celln = len(X1)
    n_events = len(xee)
    ExpE = np.zeros(celln)
    sqrt_2 = np.sqrt(2.0)

    for i in range(celln):
        # For each grid cell, compute spatial contribution from all events
        total = 0.0
        for j in range(n_events):
            # EEPAS spatial distribution: 2D Gaussian integral over rectangle
            # Use erf function to compute cumulative distribution function differences
            sigma = sigma_spatial[j]

            # erf function is available in Numba
            F = (
                np.math.erf((X1[i] - xee[j]) / (sqrt_2 * sigma)) *
                np.math.erf((Y1[i] - yee[j]) / (sqrt_2 * sigma)) -
                np.math.erf((X1[i] - xee[j]) / (sqrt_2 * sigma)) *
                np.math.erf((Y2[i] - yee[j]) / (sqrt_2 * sigma)) -
                np.math.erf((X2[i] - xee[j]) / (sqrt_2 * sigma)) *
                np.math.erf((Y1[i] - yee[j]) / (sqrt_2 * sigma)) +
                np.math.erf((X2[i] - xee[j]) / (sqrt_2 * sigma)) *
                np.math.erf((Y2[i] - yee[j]) / (sqrt_2 * sigma))
            ) / 4.0

            total += qq_other[j] * F

        ExpE[i] = total

    return ExpE


# ===== Shared functions moved to unified module =====
# fast_magnitude_integral moved to utils/numerical_integration.py
# Import shared function to avoid code duplication
from utils.numerical_integration import fast_magnitude_integral


def eepas_make_forecast(config_file='config.json', catalog_start_year=None,
                       forecast_start_year=None, forecast_end_year=None,
                       celln=None, m0=None, weight_flag=None, delay=None,
                       use_causal_ew=None, forecast_period_days=None,
                       use_fast_mode=True, magnitude_samples=50, ppe_ref_mag='mT'):
    """
    Main function for EEPAS model earthquake forecasting.

    Workflow:

        1. Load all parameters from three learning stages:

           - PPE parameters (a,d,s): Step 1
           - Aftershock parameters (ν,κ): Step 2
           - EEPAS parameters (am,bm,Sm,at,bt,St,ba,Sa,u): Step 3

        2. Calculate weights wᵢ for each historical earthquake (aftershock down-weighting)
        3. For each forecast time window:

           - Calculate precursory signal contribution for each grid cell
           - Add PPE background rate
           - Generate complete seismicity rate map

        4. Save in MATLAB format

    Args:
        config_file: Path to configuration file
        catalog_start_year: Starting year of earthquake catalog
        forecast_start_year: Starting year of forecast period
        forecast_end_year: Ending year of forecast period
        celln: Number of spatial grid cells (uses CELLE count if not specified)
        m0: Completeness magnitude
        weight_flag: Weight calculation mode
            0 = Uniform weights (wᵢ=1, no aftershock consideration)
            1 = Compute weights (aftershock down-weighting using ETAS model)
        delay: Delay in days (how long after an earthquake before counting precursory signal)
        use_causal_ew: EW weight calculation mode
            1 (dynamic): Each period uses all events up to (t1-delay) to compute EW
            0 (fixed): Each period uses all events up to (t2) to compute EW (fixed within period)
            Both modes are causal, source events restricted to before t1-delay
        forecast_period_days: Length of each forecast window (days, default 91.31≈3 months)
        use_fast_mode: Whether to use fast mode (default True)
            True: Use Numba JIT-accelerated midpoint rectangle method (fast)
            False: Use exact quad_vec integration (slow but precise)
        magnitude_samples: Number of samples for fast mode (default 20, increase for higher accuracy)
        ppe_ref_mag: PPE reference magnitude selection ('m0' or 'mT', default uses mT)

    Returns:
        np.ndarray: EEPAS forecast rate matrix with shape (N_rows, N_cols+1) where:

            - N_rows = num_time_windows × num_magnitude_bins (e.g., 40 periods × 25 mag bins = 1000)
            - N_cols = num_spatial_cells (e.g., 177 grid cells for Italy)
            - Column 0: Time window index (1, 2, 3, ...)
            - Columns 1 to N_cols: Earthquake rate for each spatial cell

            Each rate value represents expected number of earthquakes in that
            spatiotemporal-magnitude bin during the forecast period.
    """

    # Load configuration and parameters
    cfg = DataLoader.load_config(config_file)
    params = DataLoader.load_model_params(config_file)

    catalog_start_year = catalog_start_year or cfg['catalogStartYear']
    forecast_start_year = forecast_start_year or cfg['forecastStartYear']
    forecast_end_year = forecast_end_year or cfg['forecastEndYear']

    # Get file paths
    paths = get_paths(cfg, cfg['learnStartYear'], cfg['learnEndYear'],
                      forecast_start_year, forecast_end_year)
    data_path = paths['dataPath']
    eepas_out = paths['eepasOut']
    ppe_out = paths['ppeOut']
    eepas_param = paths['eepasParam']
    ppe_param = paths['ppeParam']

    m0 = m0 or params['m0']
    weight_flag = weight_flag if weight_flag is not None else params.get('weightFlag', 1)
    delay = delay or params['delay']
    use_causal_ew = use_causal_ew if use_causal_ew is not None else params.get('useCausalEW', 1)
    forecast_period_days = forecast_period_days or params.get('forecastPeriodDays', 91.31)

    # Handle PPE reference magnitude
    if ppe_ref_mag is None:
        params['ppe_ref_mag_value'] = params['mT']  # Default to mT
    elif ppe_ref_mag == 'm0':
        params['ppe_ref_mag_value'] = params['m0']
        print(f'Using PPE reference magnitude: m0 = {params["m0"]}')
    elif ppe_ref_mag == 'mT':
        params['ppe_ref_mag_value'] = params['mT']
        print(f'Using PPE reference magnitude: mT = {params["mT"]}')
    else:
        params['ppe_ref_mag_value'] = ppe_ref_mag  # Use numerical value directly

    # Validate parameter logic
    if forecast_start_year <= catalog_start_year:
        raise ValueError('Forecast start year must be greater than catalog start year')
    if forecast_end_year <= forecast_start_year:
        raise ValueError('Forecast end year must be greater than forecast start year')

    # Load earthquake catalogs
    print('Loading earthquake catalogs...')
    HORUS, _, CELLE = DataLoader.load_catalogs(config_file)

    # Load spatial region configuration (optional for spatial filtering)
    try:
        regions = DataLoader.load_spatial_regions(config_file)
        # Create RegionManager
        region_manager = RegionManager(
            regions['testing_region'],
            regions['neighborhood_region'],
            regions['testing_type'],
            regions['neighborhood_type']
        )
        print(f'Spatial region configuration:')
        print(f'  Testing Region: {regions["testing_type"]}')
        print(f'  Neighborhood Region: {regions["neighborhood_type"]}')

        # CELLE is the grid for testing region
        if regions['testing_type'] == 'grid':
            celln = celln or len(CELLE)
        else:
            raise NotImplementedError('Testing region must be in grid format')

    except Exception as e:
        # Backward compatibility: if region configuration cannot be loaded, no spatial filtering applied
        print(f'Region configuration not loaded (no spatial filtering): {e}')
        region_manager = None
        celln = celln or len(CELLE)

    print(f'Debug: Using {celln} regions for EEPAS forecast')

    # Preprocessing: quality control, time conversion, magnitude filtering
    HORUS, _, _ = CatalogProcessor.preprocess_catalog(
        HORUS, catalog_start_year, catalog_start_year, forecast_end_year,
        completeness_threshold=m0
    )

    # Apply spatial filtering (if region_manager exists)
    # Use events within neighborhood region to compute forecasts (boundary compensation)
    if region_manager is not None:
        print(f'Applying spatial filtering (neighborhood region) for historical events...')
        HORUS_filtered = CatalogProcessor.filter_by_region(
            HORUS, region_manager, region_type='neighborhood'
        )
        print(f'  Filtered event count: {len(HORUS_filtered)}')
        HORUS = HORUS_filtered

    # Create model-specific catalogs
    CatE = HORUS.copy()  # EEPAS complete catalog
    CatI_filter = HORUS[:, 9] >= params['mT']  # PPE catalog filter condition (note: Python is 0-based)
    CatI = HORUS[CatI_filter, :]  # PPE catalog (M≥mT)

    # Ensure time series is strictly increasing (required for prospective calculation)
    if len(CatE) > 0 and np.any(np.diff(CatE[:, 10]) <= 0):
        sort_idx = np.argsort(CatE[:, 10])
        CatE = CatE[sort_idx, :]
        print('Warning: EEPAS catalog not time-sorted, sorted by time column')

    if len(CatI) > 0 and np.any(np.diff(CatI[:, 10]) < 0):
        CatI = CatI[np.argsort(CatI[:, 10]), :]
        print('Warning: PPE catalog not time-sorted, sorted by time column')

    bin_width = 0.1  # Magnitude bin width

    # Load fitted model parameters
    print('Loading EEPAS parameters...')
    fitted_par = np.genfromtxt(eepas_param, delimiter=',', names=True)
    am = fitted_par['am']  # Magnitude distribution mean parameter
    bm = fitted_par['bm']  # Magnitude distribution slope parameter
    Sm = fitted_par['Sm']  # Magnitude distribution standard deviation
    at = fitted_par['at']  # Time distribution constant
    bt = fitted_par['bt']  # Time distribution slope
    St = fitted_par['St']  # Time distribution standard deviation
    ba = fitted_par['ba']  # Spatial decay parameter
    Sa = fitted_par['Sa']  # Spatial distribution standard deviation
    u = fitted_par['u']    # EEPAS-PPE mixing weight

    print('Loading PPE parameters...')
    fitted_par_ppe = np.genfromtxt(ppe_param, delimiter=',', names=True)
    a = fitted_par_ppe['a']  # Magnitude-dependent intensity
    d = fitted_par_ppe['d']  # Spatial decay parameter
    s = fitted_par_ppe['s']  # Background seismicity rate

    B = params['B'] * np.log(10)  # Gutenberg-Richter β parameter

    # Calculate earthquake weights
    print('Calculating earthquake weights...')
    params['a'] = a
    params['d'] = d
    params['s'] = s
    W, EW, CatE = calculate_earthquake_weights(CatE, CatI, params, weight_flag, delay, config_file, ppe_ref_mag)

    # Ensure catalog and weights are aligned
    if len(CatE) > 0 and np.any(np.diff(CatE[:, 10]) <= 0):
        sort_idx = np.argsort(CatE[:, 10])
        CatE = CatE[sort_idx, :]
        W = W[sort_idx]

    # Extract earthquake attribute vectors (Python is 0-based, so index-1)
    me = CatE[:, 9]   # Magnitude
    te = CatE[:, 10]  # Time
    ye = CatE[:, 6]   # Y coordinate
    xe = CatE[:, 7]   # X coordinate

    # EEPAS magnitude conditional distribution g(m|me): conditional Gaussian, normalized to [m0,∞)
    # Formula: N(am+bm*me, Sm²) / [1 - Φ((m0-am-bm*me)/Sm)]
    def fGme(m, mee_val):
        """Magnitude conditional distribution function - truncated Gaussian"""
        # Numerator: Gaussian PDF
        numerator = (1.0 / (Sm * np.sqrt(2.0 * np.pi))) * \
                   np.exp((-1.0/2.0) * ((m - am - bm * mee_val) / Sm)**2)

        # Denominator: normalization factor = P(m >= m0 | me)
        # Note: MATLAB's erf implementation is consistent with scipy
        # 0.5 * (erf(x) + 1) = Φ(x * sqrt(2)), where Φ is standard normal CDF
        denominator = 0.5 * (erf((m - am - bm * m0 - Sm**2 * B) / (np.sqrt(2) * Sm)) + 1)

        return numerator / denominator

    # Spatial grid boundaries
    X1 = CELLE[:, 0]
    X2 = CELLE[:, 1]
    Y1 = CELLE[:, 2]
    Y2 = CELLE[:, 3]

    # Flexible time window forecast settings
    T3dec = (forecast_start_year - catalog_start_year) * 365.2425  # Forecast start time (relative days)
    Time_test = (forecast_end_year - forecast_start_year) * 365.2425  # Total forecast duration
    Tre_M = forecast_period_days  # Forecast window length
    N_tre_M = int(Time_test / Tre_M)  # Total number of forecast windows

    ExpE = np.zeros(celln)  # Expected events per grid cell
    PREVISIONI_3m_less = np.zeros((int(N_tre_M * 25), celln + 1))  # Result matrix

    Nrow = 0  # Result matrix row index

    print(f'\nStarting forecast: {N_tre_M} time windows, {Tre_M} days each')

    # Main loop for time window forecasting
    for time_s in range(1, N_tre_M + 1):
        print(f'Processing forecast window {time_s}/{N_tre_M}...', flush=True)

        # Current window time range [t1, t2)
        t1 = T3dec + (time_s - 1) * Tre_M
        t2 = T3dec + time_s * Tre_M

        # Prospective constraint: only use source events before t1-delay (snapshot mode)
        sources_idx = np.where(te < t1 - delay)[0]
        L = len(sources_idx)

        m1 = 5.0  # Lower magnitude bound for forecast

        # If no historical sources: all magnitude bins for current window forecast to zero
        if L == 0:
            for j in range(25):
                PREVISIONI_3m_less[Nrow, 0] = time_s
                PREVISIONI_3m_less[Nrow, 1:celln+1] = 0
                Nrow += 1
            continue

        # Weight calculation mode selection
        if use_causal_ew == 1:
            # Causal mode: both EW and W based only on past events, ensuring strict prospectiveness
            past_filter = sources_idx
            W_past = W[past_filter]

            if len(W_past) == 0:
                for j in range(25):
                    PREVISIONI_3m_less[Nrow, 0] = time_s
                    PREVISIONI_3m_less[Nrow, 1:celln+1] = 0
                    Nrow += 1
                continue

            EW_use = np.mean(W_past)  # Empirical average of past weights
            CatE_past = CatE[past_filter, :]
            me_past = CatE_past[:, 9]
            te_past = CatE_past[:, 10]
            ye_past = CatE_past[:, 6]
            xe_past = CatE_past[:, 7]

            # Ensure past events are time-sorted
            if np.any(np.diff(te_past) <= 0):
                ordE = np.argsort(te_past)
                me_past = me_past[ordE]
                te_past = te_past[ordE]
                ye_past = ye_past[ordE]
                xe_past = xe_past[ordE]
                W_past = W_past[ordE]

            # Use past data for forecasting
            mee = me_past
            past_te = te_past
            xee = xe_past
            yee = ye_past
            W_use = W_past
        else:
            # Revised causal mode: EW uses all events up to current period end (fixed within period)
            # Select all events before current period end (t2) to compute EW
            period_filter = np.where(te < t2)[0]
            W_period = W[period_filter]

            if len(W_period) == 0:
                # If no events before current period, skip this period
                for j in range(25):
                    PREVISIONI_3m_less[Nrow, 0] = time_s
                    PREVISIONI_3m_less[Nrow, 1:celln+1] = 0
                    Nrow += 1
                continue

            # Use weight average up to current period (causal, fixed within period)
            EW_use = np.mean(W_period)

            # Source events still use before t1-delay (maintain original logic)
            mee = me[sources_idx]
            past_te = te[sources_idx]
            xee = xe[sources_idx]
            yee = ye[sources_idx]
            W_use = W[sources_idx]

        # Prospective consistency check: ensure all seed events satisfy delay condition
        assert np.all(past_te + delay <= t1), 'Prospectiveness violation: found seed events initiated within window'

        # Precompute matrix: store various contributions [scale term, magnitude integral, time integral, spatial integral, weight, total contribution]
        qq = np.zeros((len(mee), 7))

        # EEPAS time distribution integral: lognormal probability mass on [t1,t2]
        # f(τ|te,me) = lognormal distribution, parameters μ=at+bt*me, σ=St
        tau_l = t1 - past_te  # Lower integration limit (guaranteed > delay)
        tau_u = np.maximum(t2 - past_te, np.finfo(float).eps)  # Upper integration limit
        mu_t = at + bt * mee  # Time distribution location parameter

        mask = (tau_u > tau_l)
        IT1 = np.zeros(len(past_te))
        IT1[mask] = 0.5 * (
            erf((np.log10(tau_u[mask]) - mu_t[mask]) / (np.sqrt(2) * St)) -
            erf((np.log10(tau_l[mask]) - mu_t[mask]) / (np.sqrt(2) * St))
        )

        # Magnitude binning loop: compute forecast rate for each 0.1 magnitude bin
        for j in range(25):
            m2 = m1 + bin_width  # Current magnitude bin [m1, m2)

            # EEPAS scale contribution term: includes mixing weight (1-u) and normalization factor
            qq[:, 0] = ((bm * (1 - u)) / EW_use) * \
                      np.exp(-B * (am + (bm - 1) * mee + (B * Sm**2) / 2))

            # Magnitude conditional distribution integral: probability mass of g(m|me) on [m1,m2]
            # Use vectorized integration (corresponds to MATLAB's 'ArrayValued', true)
            # ∫[m1,m2] fGme(m, me) dm, computed simultaneously for all me

            if use_fast_mode:
                # Fast mode: use Numba-accelerated midpoint rectangle method
                result = fast_magnitude_integral(m1, m2, mee, am, bm, Sm, m0, B, magnitude_samples)
            else:
                # Exact mode: use scipy.quad_vec numerical integration
                # Define vectorized integrand: m is scalar, returns vector of length len(mee)
                def fGme_vec(m):
                    # Numerator: Gaussian PDF, m is scalar, mee is vector, result is vector
                    numerator = (1.0 / (Sm * np.sqrt(2.0 * np.pi))) * \
                               np.exp((-1.0/2.0) * ((m - am - bm * mee) / Sm)**2)
                    # Denominator: normalization factor, computed for each me
                    denominator = 0.5 * (erf((m - am - bm * m0 - Sm**2 * B) / (np.sqrt(2) * Sm)) + 1)
                    return numerator / denominator

                # Use quad_vec for vectorized integration, compute all me integrals at once
                result, _ = quad_vec(fGme_vec, m1, m2)

            qq[:, 1] = result

            # Time distribution contribution
            qq[:, 2] = IT1

            # Spatial contribution calculation
            # Precompute spatial standard deviation
            sigma_spatial = Sa / (10.0 ** (ba * mee / 2.0))

            # Precompute product of other contribution terms (scale×magnitude×time×weight)
            qq_other = qq[:, 0] * qq[:, 1] * qq[:, 2] * W_use

            # Use Numba-accelerated function to compute spatial contribution for all grid cells
            if use_fast_mode:
                ExpE = compute_spatial_contribution_fast(X1, X2, Y1, Y2, xee, yee,
                                                          sigma_spatial, qq_other, W_use)
            else:
                # Original Python loop version (retained for verification)
                for i in range(celln):
                    F = (
                        erf((X1[i] - xee) / (np.sqrt(2) * sigma_spatial)) *
                        erf((Y1[i] - yee) / (np.sqrt(2) * sigma_spatial)) -
                        erf((X1[i] - xee) / (np.sqrt(2) * sigma_spatial)) *
                        erf((Y2[i] - yee) / (np.sqrt(2) * sigma_spatial)) -
                        erf((X2[i] - xee) / (np.sqrt(2) * sigma_spatial)) *
                        erf((Y1[i] - yee) / (np.sqrt(2) * sigma_spatial)) +
                        erf((X2[i] - xee) / (np.sqrt(2) * sigma_spatial)) *
                        erf((Y2[i] - yee) / (np.sqrt(2) * sigma_spatial))
                    ) / 4.0
                    ExpE[i] = np.sum(qq_other * F)

            # Record forecast results for current magnitude bin
            PREVISIONI_3m_less[Nrow, 0] = time_s
            PREVISIONI_3m_less[Nrow, 1:celln+1] = ExpE
            Nrow += 1
            m1 = m1 + bin_width  # Move to next magnitude bin

    # Combine EEPAS-PPE hybrid model
    # Mixing formula: λ_total = (1-u)×λ_EEPAS + u×λ_PPE
    # Current matrix stores (1-u)×λ_EEPAS, need to add u×λ_PPE
    print('Mixing EEPAS and PPE forecast results...')
    S = sio.loadmat(ppe_out)
    if 'PREVISIONI_3m' not in S:
        raise ValueError(f'PPE output file {ppe_out} missing variable PREVISIONI_3m')

    # Perform mixing: current result already includes (1-u) weight, add u×PPE result
    PREVISIONI_3m_less[:, 1:] = (S['PREVISIONI_3m'][:, 1:] * u) + PREVISIONI_3m_less[:, 1:]

    # Create output directory and save results
    output_dir = os.path.dirname(eepas_out)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f'Created output directory: {output_dir}')

    sio.savemat(eepas_out, {'PREVISIONI_3m_less': PREVISIONI_3m_less})
    print(f'EEPAS forecast results saved to: {eepas_out}')

    return PREVISIONI_3m_less


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EEPAS Earthquake Forecasting')
    parser.add_argument('--config', default='../src/config_decluster_include921.json')
    parser.add_argument('--test', action='store_true', help='Test mode (forecast only 1 month)')
    parser.add_argument('--accurate', action='store_true',
                        help='Use accurate mode (quad_vec integration, slower but more precise)')
    parser.add_argument('--magnitude-samples', type=int, default=50,
                        help='Number of samples for fast mode (default 50, increase for higher accuracy)')
    parser.add_argument('--ppe-ref-mag', choices=['m0', 'mT'], default='mT',
                        help='PPE reference magnitude: m0 or mT (default: mT, paper version)')
    args = parser.parse_args()

    # Determine which mode to use
    use_fast_mode = not args.accurate
    if args.accurate:
        print('Using accurate mode (quad_vec), slower but higher precision', flush=True)
    else:
        print(f'Using fast mode (magnitude_samples={args.magnitude_samples})', flush=True)

    print(f'Using PPE reference magnitude: {args.ppe_ref_mag}', flush=True)

    if args.test:
        # Test mode: forecast only 1 month in 2016
        eepas_make_forecast(args.config, forecast_start_year=2016, forecast_end_year=2016.08,
                          use_fast_mode=use_fast_mode, magnitude_samples=args.magnitude_samples, ppe_ref_mag=args.ppe_ref_mag)
    else:
        eepas_make_forecast(args.config, use_fast_mode=use_fast_mode, magnitude_samples=args.magnitude_samples, ppe_ref_mag=args.ppe_ref_mag)
