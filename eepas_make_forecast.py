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
import math

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
                math.erf((X1[i] - xee[j]) / (sqrt_2 * sigma)) *
                math.erf((Y1[i] - yee[j]) / (sqrt_2 * sigma)) -
                math.erf((X1[i] - xee[j]) / (sqrt_2 * sigma)) *
                math.erf((Y2[i] - yee[j]) / (sqrt_2 * sigma)) -
                math.erf((X2[i] - xee[j]) / (sqrt_2 * sigma)) *
                math.erf((Y1[i] - yee[j]) / (sqrt_2 * sigma)) +
                math.erf((X2[i] - xee[j]) / (sqrt_2 * sigma)) *
                math.erf((Y2[i] - yee[j]) / (sqrt_2 * sigma))
            ) / 4.0

            total += qq_other[j] * F

        ExpE[i] = total

    return ExpE


# ===== Shared functions moved to unified module =====
# fast_magnitude_integral moved to utils/numerical_integration.py
# Import shared function to avoid code duplication
from utils.numerical_integration import fast_magnitude_integral


def apply_time_compensation(ppe_rate, eepas_rate_with_eta, u, time_comp_config,
                           forecast_start_time, catalog_end_time, N_tre_M, eepas_params,
                           forecast_period_days=91.31, catalog_start_time=None):
    """
    Apply time compensation to EEPAS forecast.

    Implements LEEPAS (Lead-time compensated EEPAS) method from Rhoades et al. (2019).

    Args:
        ppe_rate: PPE background rate λ₀ (N_rows, N_cells)
        eepas_rate_with_eta: EEPAS time-varying rate Σ η(mᵢ)λᵢ (N_rows, N_cells)
                            where η(mᵢ) already includes (1-μ) for magnitude completeness
        u: Failure-to-predict rate (μ parameter)
        time_comp_config: Time compensation configuration dict
        forecast_start_time: Forecast start time (decimal years)
        catalog_end_time: Catalog end time (decimal years)
        N_tre_M: Number of time windows
        eepas_params: EEPAS parameters dict
        forecast_period_days: Length of each forecast window (days, default 91.31)
        catalog_start_time: Catalog start time (decimal years). If provided,
                           Lead Time (L) is automatically calculated as the full
                           catalog history length (forecast_start_time - catalog_start_time).
                           This is the RECOMMENDED way to use LEEPAS, as EEPAS precursors
                           can occur years to decades before target earthquakes.
                           If not provided, falls back to config's lead_time_days.

    Returns:
        compensated_rate: Compensated forecast rate (N_rows, N_cells)

    Formulas (from Rhoades et al. 2019, Equations 12-14):
        Mode A (background compensated):
            λ_A = [μ + (1-μ)(1-p)] λ₀ + Σ η(mᵢ)λᵢ

        Mode B (time-varying compensated):
            λ_B = μ λ₀ + (1/p) Σ η(mᵢ)λᵢ

        Mode C (optimal mixture):
            λ_C = ω λ_A + (1-ω) λ_B

    where:
        p(T,L,m) = completeness function (0-1)
        η(mᵢ) = magnitude scaling function, includes (1-μ) for magnitude completeness

    Note:
        The (1-μ) in η is for ensuring Gutenberg-Richter distribution (magnitude completeness),
        NOT the same as the mixing weight in standard EEPAS formula.

        Per-period time-lag: Each forecast period may have a different time-lag T in
        non-rolling update mode. This function correctly handles varying T across periods.
    """
    import numpy as np
    from utils.time_compensation import TimeCompensation

    # Check if time compensation is enabled
    if not time_comp_config.get('enable', False):
        # No compensation: use standard EEPAS formula
        # λ = μ·λ₀ + Σ η(mᵢ)λᵢ
        return ppe_rate * u + eepas_rate_with_eta

    print("\n" + "="*80)
    print("Applying Time Compensation (LEEPAS)")
    print("="*80)

    # Extract configuration
    mode = time_comp_config.get('mode', 'B')
    omega = time_comp_config.get('omega', 0.0)

    # Lead time (L): should be the full catalog history length
    # If catalog_start_time is provided, calculate L automatically
    # Otherwise fall back to config value (for backward compatibility)
    config_lead_time_days = time_comp_config.get('lead_time_days', 90)

    if catalog_start_time is not None:
        # Automatic calculation: L = catalog length
        # L is from catalog start to the target earthquake time
        # For each forecast period, the target could be anywhere in that period
        # Use forecast_start_time as reference point
        lead_time_years = forecast_start_time - catalog_start_time
        lead_time_days = lead_time_years * 365.2425

        if config_lead_time_days != 90 and abs(config_lead_time_days - lead_time_days) > 365:
            print(f"  ⚠️  Warning: Config lead_time_days={config_lead_time_days:.0f} differs from "
                  f"actual catalog length={lead_time_days:.0f} days")
            print(f"     Using full catalog length (recommended for EEPAS precursor detection)")
    else:
        # Backward compatibility: use config value
        lead_time_days = config_lead_time_days
        lead_time_years = lead_time_days / 365.2425
        print(f"  ⚠️  Warning: catalog_start_time not provided, using config lead_time_days={lead_time_days:.0f}")

    # Calculate base time-lag (for Period 1) and period length
    base_time_lag = forecast_start_time - catalog_end_time
    period_length_years = forecast_period_days / 365.2425

    # Determine if using rolling update mode (T ≈ 0 for all periods)
    is_rolling = abs(base_time_lag) < 1e-6

    print(f"  Mode: {mode}")
    print(f"  Base time-lag (T₀): {base_time_lag:.4f} years")
    if is_rolling:
        print(f"  Update mode: Rolling (all periods use T=0)")
    else:
        print(f"  Update mode: Non-rolling (T increases per period)")
        print(f"  Period length: {period_length_years:.4f} years ({forecast_period_days:.2f} days)")
        if N_tre_M > 1:
            final_time_lag = base_time_lag + (N_tre_M - 1) * period_length_years
            print(f"  Time-lag range: T={base_time_lag:.4f}yr (P1) → T={final_time_lag:.4f}yr (P{N_tre_M})")
    print(f"  Lead time (L): {lead_time_years:.2f} years ({lead_time_days:.0f} days)")
    if mode == 'C':
        print(f"  Mixing parameter (ω): {omega:.4f}")

    # Initialize time compensation calculator
    compensator = TimeCompensation(
        aT=eepas_params['at'],
        bT=eepas_params['bt'],
        sigma_T=eepas_params['St'],
        aM=eepas_params['am'],
        bM=eepas_params['bm'],
        sigma_M=eepas_params['Sm'],
        m0=eepas_params['m0'],
        mu=u,
        bGR=eepas_params['B'],
        params={'mu_upper': 10.05}
    )

    # Magnitude bin configuration
    mag_min = 5.0
    mag_step = 0.1
    num_mag_bins = 25

    # Build per-period completeness matrix
    N_rows, N_cells = ppe_rate.shape
    completeness_matrix = np.zeros((N_rows, N_cells))

    print(f"\n  Computing per-period completeness p(T,L,m):")
    print(f"  {'Period':>8} {'Time-lag (yr)':>15} {'Avg p(T,L,m)':>15}")
    print("  " + "-"*42)

    for period_idx in range(N_tre_M):
        # Calculate time-lag for this period
        if is_rolling:
            # Rolling update: catalog updates to each period start, so T=0 always
            period_time_lag = 0.0
        else:
            # Non-rolling update: catalog fixed, T increases with period
            period_time_lag = base_time_lag + period_idx * period_length_years

        # Calculate completeness for all magnitude bins in this period
        period_completeness = np.zeros(num_mag_bins)
        for mag_idx in range(num_mag_bins):
            mag_center = mag_min + mag_idx * mag_step + mag_step / 2.0
            p_TLm = compensator.compute_completeness(
                T=period_time_lag,
                L=lead_time_years,
                m=mag_center
            )
            period_completeness[mag_idx] = p_TLm

        # Fill completeness matrix for this period
        start_row = period_idx * num_mag_bins
        end_row = (period_idx + 1) * num_mag_bins
        completeness_matrix[start_row:end_row, :] = np.tile(
            period_completeness[:, np.newaxis],
            (1, N_cells)
        )

        # Print summary for this period
        avg_completeness = np.mean(period_completeness)
        print(f"  {period_idx+1:>8} {period_time_lag:>15.4f} {avg_completeness:>15.4f}")

    # Print detailed completeness for first period
    print(f"\n  Detailed completeness for Period 1 (T={base_time_lag:.4f}yr, L={lead_time_years:.2f}yr):")
    print(f"  {'Mag Range':>12} {'Mag Center':>12} {'p(T,L,m)':>12}")
    print("  " + "-"*40)

    period_1_completeness = completeness_matrix[:num_mag_bins, 0]
    for i in range(num_mag_bins):
        if i < 3 or i == num_mag_bins - 1:
            mag_center = mag_min + i * mag_step + mag_step / 2.0
            print(f"  [{mag_min + i*mag_step:.1f}, {mag_min + (i+1)*mag_step:.1f}) "
                  f"{mag_center:12.2f} {period_1_completeness[i]:12.4f}")
        elif i == 3:
            print("  ...")

    # Apply compensation based on mode
    # Input: eepas_rate_with_eta = Σ η(mᵢ)λᵢ (η already includes (1-μ))

    if mode == 'A':
        # Mode A: λ_A = [μ + (1-μ)(1-p)] λ₀ + Σ η(mᵢ)λᵢ
        background_factor = u + (1 - u) * (1 - completeness_matrix)
        compensated_rate = ppe_rate * background_factor + eepas_rate_with_eta

        print(f"\n  Mode A: Background compensated")
        print(f"    λ_A = [μ + (1-μ)(1-p)] λ₀ + Σ η(mᵢ)λᵢ")
        print(f"    Average background factor: {np.mean(background_factor):.4f}")

    elif mode == 'B':
        # Mode B: λ_B = μ λ₀ + (1/p) Σ η(mᵢ)λᵢ
        p_safe = np.maximum(completeness_matrix, 1e-6)
        compensated_rate = ppe_rate * u + eepas_rate_with_eta / p_safe

        print(f"\n  Mode B: Time-varying compensated")
        print(f"    λ_B = μ λ₀ + (1/p) Σ η(mᵢ)λᵢ")
        print(f"    Average scaling factor (1/p): {np.mean(1/p_safe):.4f}")

    elif mode == 'C':
        # Mode C: λ_C = ω λ_A + (1-ω) λ_B
        background_factor = u + (1 - u) * (1 - completeness_matrix)
        p_safe = np.maximum(completeness_matrix, 1e-6)

        lambda_A = ppe_rate * background_factor + eepas_rate_with_eta
        lambda_B = ppe_rate * u + eepas_rate_with_eta / p_safe

        compensated_rate = omega * lambda_A + (1 - omega) * lambda_B

        print(f"\n  Mode C: Optimal mixture (ω={omega:.4f})")
        print(f"    λ_C = {omega:.4f}·λ_A + {1-omega:.4f}·λ_B")

    else:
        raise ValueError(f"Unknown time compensation mode: {mode}")

    # Print statistics
    original_total = np.sum(ppe_rate * u + eepas_rate_with_eta)
    compensated_total = np.sum(compensated_rate)

    print(f"\n  Forecast Statistics:")
    print(f"    Original expected events:    {original_total:.2f}")
    print(f"    Compensated expected events: {compensated_total:.2f}")
    print(f"    Compensation factor:         {compensated_total/original_total:.4f}x")
    print("="*80 + "\n")

    return compensated_rate


def eepas_make_forecast(config_file='config.json', catalog_start_year=None,
                       forecast_start_year=None, forecast_end_year=None,
                       celln=None, m0=None, weight_flag=None, delay=None,
                       use_causal_ew=None, use_rolling_update=None,
                       forecast_period_days=None,
                       use_fast_mode=True, magnitude_samples=50, ppe_ref_mag='mT',
                       lead_time_days=None,
                       override_at=None, override_Sa=None, output_suffix=None,
                       _hybrid_submodel=False):
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
        use_rolling_update: Whether to use rolling update for source event selection
            True (default): Each time window dynamically uses all events up to (t1-delay)
            False: All time windows use the same snapshot of events (up to T3dec-delay)
            Note: This is independent of use_causal_ew which controls EW weight calculation
        forecast_period_days: Length of each forecast window (days, default 91.31≈3 months)
        use_fast_mode: Whether to use fast mode (default True)
            True: Use Numba JIT-accelerated midpoint rectangle method (fast)
            False: Use exact quad_vec integration (slow but precise)
        magnitude_samples: Number of samples for fast mode (default 20, increase for higher accuracy)
        ppe_ref_mag: PPE reference magnitude selection ('m0' or 'mT', default uses mT)
        lead_time_days: Fixed lead time L in days for FLEEPAS (default None)
            - None: Use all historical earthquakes as precursors (original EEPAS)
            - float: Only use earthquakes within [t-L, t-delay] as precursors (FLEEPAS)
        override_at: Override fitted at (a_T) parameter for Hybrid EEPAS (default None)
            - None: Use fitted value from Fitted_par_EEPAS_*.csv
            - float: Override with specified value
        override_Sa: Override fitted Sa (σ_A) parameter for Hybrid EEPAS (default None)
            - None: Use fitted value from Fitted_par_EEPAS_*.csv
            - float: Override with specified value
        output_suffix: Suffix for output filename for Hybrid EEPAS (default None)
            - None: Use default output filename
            - str: Append suffix to output filename (e.g., '_model1')
        _hybrid_submodel: Internal flag to prevent recursive hybrid calls (default False)
            - False: Normal execution, will check config for hybrid settings
            - True: Running as submodel, skip hybrid processing

    Hybrid EEPAS Config (in modelParams.hybrid):
        {
            "enable": true,
            "delta_aT_values": [-0.5, 0.0, 0.5],  // Offsets along trade-off line
            "weights": "equal"                    // Or array like [0.33, 0.34, 0.33]
        }

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

    # =========================================================================
    # Hybrid EEPAS: Check if hybrid mode is enabled in config
    # =========================================================================
    hybrid_config = params.get('hybrid', {})
    hybrid_enabled = hybrid_config.get('enable', False)

    if hybrid_enabled and not _hybrid_submodel:
        print('=' * 70)
        print('Hybrid EEPAS Mode (from config)')
        print('=' * 70)

        # Get hybrid parameters
        delta_aT_values = hybrid_config.get('delta_aT_values', [-0.5, 0.0, 0.5])
        weights_config = hybrid_config.get('weights', 'equal')

        if weights_config == 'equal':
            weights = [1.0 / len(delta_aT_values)] * len(delta_aT_values)
        else:
            weights = weights_config

        print(f'  Δa_T values: {delta_aT_values}')
        print(f'  Weights: {weights}')

        # Get file paths for loading EEPAS parameters
        paths = get_paths(cfg, cfg['learnStartYear'], cfg['learnEndYear'],
                          cfg['forecastStartYear'], cfg['forecastEndYear'])
        eepas_param = paths['eepasParam']
        eepas_out = paths['eepasOut']

        # Load fitted EEPAS parameters
        import pandas as pd
        eepas_df = pd.read_csv(eepas_param)
        base_at = eepas_df['at'].values[0]
        base_Sa = eepas_df['Sa'].values[0]

        # Calculate trade-off constant: C = σ_A² × 10^(a_T)
        C = base_Sa**2 * (10 ** base_at)
        print(f'  Base a_T = {base_at:.4f}')
        print(f'  Base σ_A = {base_Sa:.4f}')
        print(f'  Trade-off constant C = {C:.6f}')

        # Generate forecasts for each model
        print(f'\nGenerating {len(delta_aT_values)} forecasts along trade-off line...')
        forecasts = []

        for i, delta_aT in enumerate(delta_aT_values):
            new_at = base_at + delta_aT
            new_Sa = np.sqrt(C / (10 ** new_at))

            print(f'\n>>> Model {i+1}: Δa_T={delta_aT:+.2f}, a_T={new_at:.4f}, σ_A={new_Sa:.6f}')

            # Recursively call with override parameters
            result = eepas_make_forecast(
                config_file=config_file,
                use_fast_mode=use_fast_mode,
                magnitude_samples=magnitude_samples,
                ppe_ref_mag=ppe_ref_mag,
                override_at=new_at,
                override_Sa=new_Sa,
                output_suffix=f'_model{i+1}',
                _hybrid_submodel=True  # Prevent recursive hybrid processing
            )
            forecasts.append(result)

        # Mix forecasts
        print(f'\nMixing {len(forecasts)} forecasts...')
        mixed_forecast = np.zeros_like(forecasts[0])
        for i, (forecast, weight) in enumerate(zip(forecasts, weights)):
            mixed_forecast += weight * forecast

        # Save mixed forecast
        output_dir = os.path.dirname(eepas_out)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        sio.savemat(eepas_out, {'PREVISIONI_3m_less': mixed_forecast})
        print(f'\n✅ Hybrid EEPAS forecast saved to: {eepas_out}')

        # Calculate total expected events
        total_expected = np.sum(mixed_forecast[:, 1:])
        print(f'   Total expected events: {total_expected:.2f}')

        return mixed_forecast
    # =========================================================================

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

    # Hybrid EEPAS: Modify output filename if suffix specified
    if output_suffix is not None:
        # Insert suffix before .mat extension
        # e.g., PREVISIONI_3m_EEPAS_2024_2026.mat -> PREVISIONI_3m_EEPAS_2024_2026_model1.mat
        base, ext = os.path.splitext(eepas_out)
        eepas_out = f"{base}{output_suffix}{ext}"
        print(f'  Hybrid EEPAS: Output file modified to {eepas_out}')

    m0 = m0 or params['m0']
    weight_flag = weight_flag if weight_flag is not None else params.get('weightFlag', 1)
    delay = delay or params['delay']
    use_causal_ew = use_causal_ew if use_causal_ew is not None else params.get('useCausalEW', 1)
    use_rolling_update = use_rolling_update if use_rolling_update is not None else params.get('useRollingUpdate', True)
    forecast_period_days = forecast_period_days or params.get('forecastPeriodDays', 91.31)

    # FLEEPAS: Read fixed lead time from config if not specified
    # lead_time_days limits precursor selection to [t-L, t-delay] window
    if lead_time_days is None:
        time_comp_config = params.get('timeComp', {})
        if time_comp_config.get('enable', False):
            lead_time_days = time_comp_config.get('lead_time_days', None)

    if lead_time_days is not None:
        print(f'FLEEPAS mode: Using fixed lead time L = {lead_time_days} days')
        print(f'  Precursor window: [t-{lead_time_days}, t-{delay}] for each forecast time t')

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

    # Hybrid EEPAS: Override at and Sa if specified
    # This enables running multiple models along the space-time trade-off line
    # Reference: Rastin et al. (2021) "Space-time trade-off of precursory seismicity"
    if override_at is not None:
        print(f'  Hybrid EEPAS: Overriding at = {at:.4f} -> {override_at:.4f}')
        at = override_at
    if override_Sa is not None:
        print(f'  Hybrid EEPAS: Overriding Sa = {Sa:.4f} -> {override_Sa:.4f}')

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

    # ===== Select update mode for source event selection =====
    if use_rolling_update:
        # Rolling update: each time window dynamically selects all historical earthquakes up to that time
        print('Rolling update mode (each forecast window uses all historical earthquakes up to that time)')
        static_sources_idx = None
    else:
        # Static snapshot: all forecast windows use the same historical data (snapshot at forecast start)
        print('Static snapshot mode (all forecast windows use fixed historical data)')
        # FLEEPAS: If lead_time_days specified, also limit to [T3dec-L, T3dec-delay]
        if lead_time_days is not None:
            static_sources_idx = np.where((te < T3dec - delay) & (te >= T3dec - lead_time_days))[0]
        else:
            static_sources_idx = np.where(te < T3dec - delay)[0]

    # Main loop for time window forecasting
    for time_s in range(1, N_tre_M + 1):
        print(f'Processing forecast window {time_s}/{N_tre_M}...', flush=True)

        # Current window time range [t1, t2)
        t1 = T3dec + (time_s - 1) * Tre_M
        t2 = T3dec + time_s * Tre_M

        # Prospective constraint: select source events based on update mode
        # FLEEPAS: If lead_time_days specified, limit precursors to [t1-L, t1-delay]
        if use_rolling_update:
            if lead_time_days is not None:
                sources_idx = np.where((te < t1 - delay) & (te >= t1 - lead_time_days))[0]
            else:
                sources_idx = np.where(te < t1 - delay)[0]
        else:
            sources_idx = static_sources_idx
        n_sources = len(sources_idx)

        m1 = 5.0  # Lower magnitude bound for forecast

        # If no historical sources: all magnitude bins for current window forecast to zero
        if n_sources == 0:
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

        # FLEEPAS: Cap upper integration bound at lead_time_days
        # This ensures we only count contributions within the lead time window
        if lead_time_days is not None:
            tau_u = np.minimum(tau_u, lead_time_days)

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

    # ===== Apply Time Compensation (LEEPAS) =====
    # Extract time compensation configuration from cfg.modelParams
    time_comp_config = cfg.get('modelParams', {}).get('timeComp', {'enable': False})

    # Load PPE forecast
    print('Loading PPE forecast results...')
    S = sio.loadmat(ppe_out)
    if 'PREVISIONI_3m' not in S:
        raise ValueError(f'PPE output file {ppe_out} missing variable PREVISIONI_3m')

    ppe_rate = S['PREVISIONI_3m'][:, 1:]  # PPE background rate λ₀
    eepas_rate_with_eta = PREVISIONI_3m_less[:, 1:]  # EEPAS rate Σ η(mᵢ)λᵢ

    # Calculate catalog end time (last earthquake in training data)
    # In rolling update mode, use the time just before forecast start
    # In non-rolling mode, use training period end time (learn_end_year)
    if use_rolling_update:
        catalog_end_time = forecast_start_year
    else:
        # Non-rolling: use training period end (learn_end_year)
        # NOT the last earthquake time, as catalog may contain test period data
        catalog_end_time = cfg.get('learnEndYear', forecast_start_year)

    # Prepare EEPAS parameters dict for TimeCompensation class
    # Note: Some parameters may be per-cell arrays, extract scalar values
    def extract_scalar(param):
        """Extract scalar from parameter (handle both array and scalar cases)"""
        if isinstance(param, np.ndarray):
            return float(np.mean(param))  # Use mean value for spatial averaging
        return float(param)

    eepas_params_dict = {
        'am': extract_scalar(am),
        'bm': extract_scalar(bm),
        'Sm': extract_scalar(Sm),
        'at': extract_scalar(at),
        'bt': extract_scalar(bt),
        'St': extract_scalar(St),
        'ba': extract_scalar(ba),
        'Sa': extract_scalar(Sa),
        'u': extract_scalar(u),
        'm0': extract_scalar(m0),
        'B': extract_scalar(B / np.log(10))  # Convert back to base-10
    }

    # Apply time compensation (or standard mixing if disabled)
    print('Applying EEPAS-PPE mixing with time compensation...')
    PREVISIONI_3m_less[:, 1:] = apply_time_compensation(
        ppe_rate=ppe_rate,
        eepas_rate_with_eta=eepas_rate_with_eta,
        u=eepas_params_dict['u'],  # Use extracted scalar value
        time_comp_config=time_comp_config,
        forecast_start_time=forecast_start_year,
        catalog_end_time=catalog_end_time,
        N_tre_M=N_tre_M,
        eepas_params=eepas_params_dict,
        forecast_period_days=Tre_M,  # Forecast window length
        catalog_start_time=catalog_start_year  # For automatic L calculation
    )

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
    # Hybrid EEPAS parameters (for running multiple models along space-time trade-off line)
    parser.add_argument('--override-at', type=float, default=None,
                        help='Override at (a_T) parameter for Hybrid EEPAS')
    parser.add_argument('--override-Sa', type=float, default=None,
                        help='Override Sa (σ_A) parameter for Hybrid EEPAS')
    parser.add_argument('--output-suffix', type=str, default=None,
                        help='Suffix for output filename (e.g., "_model1")')
    args = parser.parse_args()

    # Determine which mode to use
    use_fast_mode = not args.accurate
    if args.accurate:
        print('Using accurate mode (quad_vec), slower but higher precision', flush=True)
    else:
        print(f'Using fast mode (magnitude_samples={args.magnitude_samples})', flush=True)

    print(f'Using PPE reference magnitude: {args.ppe_ref_mag}', flush=True)

    # Hybrid EEPAS info
    if args.override_at is not None or args.override_Sa is not None:
        print(f'Hybrid EEPAS mode enabled:', flush=True)
        if args.override_at is not None:
            print(f'  Override at (a_T): {args.override_at}', flush=True)
        if args.override_Sa is not None:
            print(f'  Override Sa (σ_A): {args.override_Sa}', flush=True)
        if args.output_suffix is not None:
            print(f'  Output suffix: {args.output_suffix}', flush=True)

    if args.test:
        # Test mode: forecast only 1 month in 2016
        eepas_make_forecast(args.config, forecast_start_year=2016, forecast_end_year=2016.08,
                          use_fast_mode=use_fast_mode, magnitude_samples=args.magnitude_samples,
                          ppe_ref_mag=args.ppe_ref_mag,
                          override_at=args.override_at, override_Sa=args.override_Sa,
                          output_suffix=args.output_suffix)
    else:
        eepas_make_forecast(args.config, use_fast_mode=use_fast_mode,
                          magnitude_samples=args.magnitude_samples, ppe_ref_mag=args.ppe_ref_mag,
                          override_at=args.override_at, override_Sa=args.override_Sa,
                          output_suffix=args.output_suffix)
