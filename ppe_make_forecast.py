#!/usr/bin/env python3
"""
PPE Earthquake Forecasting

Generate PPE model seismicity rate forecasts for testing region grid cells.

Uses learned PPE parameters (a, d, s) to calculate background earthquake
occurrence rate λ₀(t,x,y) based on proximity to past earthquakes.
"""

import numpy as np
import scipy.io as sio
import argparse
import os
import sys
from joblib import Parallel, delayed
from numba import jit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.catalog_processor import CatalogProcessor
from utils.region_manager import RegionManager
from utils.get_paths import get_paths


# ===== Shared functions moved to unified module =====
# fast_kernel_sum_2d, trapezoidal_2d, ppe_spatial_integral_accurate moved to utils/numerical_integration.py
# Import shared functions to avoid code duplication
from utils.numerical_integration import fast_kernel_sum_2d, trapezoidal_2d


def compute_grid_integral_fast(x_bounds, y_bounds, event_x, event_y, event_m,
                                a, d, s, ppe_ref_mag, coeff, spatial_samples=20):
    """
    Fast computation of PPE integral using trapezoidal integration (replaces dblquad).

    Args:
        x_bounds: Grid x range [x_min, x_max]
        y_bounds: Grid y range [y_min, y_max]
        event_x, event_y, event_m: Event coordinates and magnitudes
        a, d, s, ppe_ref_mag: PPE parameters
        coeff: Temporal and magnitude integration coefficient
        spatial_samples: Number of sampling points per dimension (default 20, adjustable for precision)

    Returns:
        float: Integral value

    Note:
        Refactored to use fast_kernel_sum_2d and trapezoidal_2d from unified module
    """
    x_min, x_max = x_bounds
    y_min, y_max = y_bounds

    # Create 2D grid
    x_edges = np.linspace(x_min, x_max, spatial_samples)
    y_edges = np.linspace(y_min, y_max, spatial_samples)
    dx = x_edges[1] - x_edges[0]
    dy = y_edges[1] - y_edges[0]
    x_grid, y_grid = np.meshgrid(x_edges, y_edges, indexing='ij')

    # Calculate weights (excludes temporal integration coefficient, multiplied later)
    weights = a * (event_m - ppe_ref_mag)

    # Compute kernel superposition using unified module function
    kernel_grid = fast_kernel_sum_2d(x_grid, y_grid, d, event_x, event_y, weights)

    # Add constant term s
    h_grid = kernel_grid + s

    # Apply trapezoidal integration from unified module
    spatial_integral = trapezoidal_2d(h_grid, dx, dy)

    # Multiply by temporal and magnitude integration coefficient
    return spatial_integral * coeff


def ppe_make_forecast(config_file='config.json', catalog_start_year=None,
                     forecast_start_year=None, forecast_end_year=None,
                     celln=None, m0=None, mT=None, delay=None,
                     use_rolling_update=None, forecast_period_days=None, ppe_ref_mag='mT',
                     use_fast_mode=True, spatial_samples=50):
    """
    Main function for PPE model earthquake forecasting.

    Workflow:

        1. Load PPE parameters (a, d, s) from the learning phase
        2. Load historical earthquake catalog
        3. For each forecast time point:

           - Calculate seismic kernel contribution for each grid cell
           - Add background seismicity rate
           - Generate seismicity rate map for that time point

        4. Save results in MATLAB format for subsequent analysis

    Args:
        config_file: Configuration file path
        catalog_start_year: Catalog start year
        forecast_start_year: Forecast start year
        forecast_end_year: Forecast end year
        celln: Number of spatial grid cells
        m0: Completeness magnitude
        mT: Target magnitude (for calculating seismic kernel)
        delay: Delay in days (how long after an earthquake before it is counted)
        use_rolling_update: Whether to use rolling update
            True: Each time point uses the latest data (default)
            False: All time points use the same historical data
        forecast_period_days: Forecast period length (days, default 91.31 ≈ 3 months)
        use_fast_mode: Whether to use fast mode (default True)
            True: Use Numba JIT accelerated grid integration (60-70x faster)
            False: Use accurate dblquad numerical integration (slow but precise)
        spatial_samples: Number of sampling points for fast mode (default 20)
            Increasing improves precision but reduces speed

    Returns:
        Forecast results saved as .mat file
    """

    # ===== Load configuration =====
    cfg = DataLoader.load_config(config_file)
    params = DataLoader.load_model_params(config_file)

    # Set time ranges (use config file if not specified)
    catalog_start_year = catalog_start_year or cfg['catalogStartYear']
    forecast_start_year = forecast_start_year or cfg['forecastStartYear']
    forecast_end_year = forecast_end_year or cfg['forecastEndYear']
    m0 = m0 or params['m0']
    mT = mT or params['mT']
    delay = delay or params['delay']
    use_rolling_update = use_rolling_update if use_rolling_update is not None else params.get('useRollingUpdate', True)
    forecast_period_days = forecast_period_days or params.get('forecastPeriodDays', 91.31)

    # Handle PPE reference magnitude
    if ppe_ref_mag is None:
        ppe_ref_mag_value = mT  # Default to mT
    elif ppe_ref_mag == 'm0':
        ppe_ref_mag_value = m0
        print(f'Using PPE reference magnitude: m0 = {m0}')
    elif ppe_ref_mag == 'mT':
        ppe_ref_mag_value = mT
        print(f'Using PPE reference magnitude: mT = {mT}')
    else:
        ppe_ref_mag_value = ppe_ref_mag  # Use numerical value directly

    # Check time logic
    if forecast_start_year <= catalog_start_year:
        raise ValueError('Forecast start year must be greater than catalog start year')
    if forecast_end_year <= forecast_start_year:
        raise ValueError('Forecast end year must be greater than forecast start year')

    # Load data
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

        # With region filtering: CELLE is the testing region grid
        # celln should be the number of testing region grid cells
        if regions['testing_type'] == 'grid':
            # CELLE is already the testing region grid
            celln = celln or len(CELLE)
        else:
            raise NotImplementedError('Testing region must be in grid format')

    except Exception as e:
        # Backward compatibility: if unable to load region config, no spatial filtering applied
        print(f'Region configuration not loaded (no spatial filtering): {e}')
        region_manager = None
        celln = celln or len(CELLE)

    HORUS, _, _ = CatalogProcessor.preprocess_catalog(
        HORUS, catalog_start_year, catalog_start_year, forecast_end_year,
        completeness_threshold=m0, filter_target_mag=True,
        target_magnitude=mT, verbose=True
    )

    # Apply spatial filtering (if region_manager exists)
    # Use events within neighborhood region for forecasting (boundary compensation)
    if region_manager is not None:
        print(f'Applying spatial filtering (neighborhood region) for historical events...')
        HORUS = CatalogProcessor.filter_by_region(
            HORUS, region_manager, region_type='neighborhood'
        )
        print(f'  Number of events after filtering: {len(HORUS)}')

    mi, ti, yi, xi = HORUS[:, 9], HORUS[:, 10], HORUS[:, 6], HORUS[:, 7]

    # ===== Load PPE parameters from learning phase =====
    paths = get_paths(cfg, cfg['learnStartYear'], cfg['learnEndYear'],
                      forecast_start_year, forecast_end_year)
    ppe_params = np.genfromtxt(paths['ppeParam'], delimiter=',', names=True)
    a, d, s = ppe_params['a'], ppe_params['d'], ppe_params['s']
    B = params['B'] * np.log(10)  # Gutenberg-Richter b-value, converted to natural log base

    # ===== Prepare spatial grid =====
    # Organize grid cell boundaries into rectangular vertex coordinates
    # Xpol: [x_left, x_left, x_right, x_right]
    # Ypol: [y_bottom, y_top, y_top, y_bottom]
    Xpol = np.column_stack([CELLE[:, 0], CELLE[:, 0], CELLE[:, 1], CELLE[:, 1]])
    Ypol = np.column_stack([CELLE[:, 2], CELLE[:, 3], CELLE[:, 3], CELLE[:, 2]])

    # ===== Time window setup =====
    T3dec = (forecast_start_year - catalog_start_year) * 365.2425  # Forecast start time (relative to catalog start)
    Time_test = (forecast_end_year - forecast_start_year) * 365.2425  # Total forecast period length
    N_tre_M = int(Time_test / forecast_period_days)  # Number of forecast windows

    # ===== Initialize forecast result matrix =====
    # Each forecast window × 25 magnitude bins, each row records [time window number, seismicity rate for each grid]
    PREVISIONI_3m = np.zeros((N_tre_M * 25, celln + 1))

    # ===== Select update mode =====
    if use_rolling_update:
        # Rolling update: each time point uses the latest historical data
        print('Rolling update mode (each forecast window uses all historical earthquakes up to that time)')
        static_idx = None
    else:
        # Static snapshot: all forecast windows use the same historical data (as of forecast start)
        print('Static snapshot mode (all forecast windows use fixed historical data)')
        static_idx = np.where(ti < T3dec - delay)[0]

    bin_width = 0.1  # Magnitude bin width (0.1 magnitude units)
    Nrow = 0  # Current row being filled

    # ===== Main forecast loop =====
    # For each forecast time window, calculate seismicity rate for each grid cell during that time period
    for time_s in range(1, N_tre_M + 1):
        print(f'Processing forecast window {time_s}/{N_tre_M}...', flush=True)

        # Time range [t1, t2) of current forecast window (units: days)
        t1 = T3dec + (time_s - 1) * forecast_period_days
        t2 = T3dec + time_s * forecast_period_days

        # Select available historical earthquakes (excluding delay period)
        idx = np.where(ti < t1 - delay)[0] if use_rolling_update else static_idx
        log_time_diff = np.log(t2) - np.log(t1)  # Integral of PPE time function f₀(t) = 1/t

        # ===== Prepare historical earthquake data =====
        if len(idx) > 0:
            # Numba requires numpy arrays
            event_x = xi[idx]
            event_y = yi[idx]
            event_m = mi[idx]
        else:
            event_x = np.array([])
            event_y = np.array([])
            event_m = np.array([])

        # ===== Calculate forecast for each magnitude bin =====
        m1 = mT  # Starting magnitude
        for j in range(25):  # 25 magnitude bins, covering mT ~ mT+2.5
            m2 = m1 + bin_width  # Upper bound of magnitude bin

            # Integral of PPE magnitude function g₀(m) = β·exp(-β(m-ppe_ref_mag)) over [m1,m2]
            exp_mag_diff = -np.exp(-(m2 - ppe_ref_mag_value) * B) + np.exp(-(m1 - ppe_ref_mag_value) * B)
            coeff = log_time_diff * exp_mag_diff  # Joint integration coefficient for time × magnitude

            # ===== Integrate over each spatial grid cell =====
            ExpE = np.zeros(celln)
            if len(event_x) > 0:
                if use_fast_mode:
                    # Fast mode: Use Numba JIT accelerated grid integration (60-70x faster)
                    for i in range(celln):
                        x_bounds = (Xpol[i, 0], Xpol[i, 2])
                        y_bounds = (Ypol[i, 0], Ypol[i, 2])
                        ExpE[i] = compute_grid_integral_fast(
                            x_bounds, y_bounds, event_x, event_y, event_m,
                            a, d, s, ppe_ref_mag_value, coeff, spatial_samples=spatial_samples
                        )
                else:
                    # Accurate mode: Use ppe_spatial_integral_accurate from unified module (slow but precise)
                    from utils.numerical_integration import ppe_spatial_integral_accurate

                    # Preprocess event data (weight already contains a)
                    event_data = [(a * (event_m[k] - ppe_ref_mag_value), event_x[k], event_y[k])
                                  for k in range(len(event_x))]

                    def compute_cell_integral(i):
                        """Compute integral for a single grid cell"""
                        result = ppe_spatial_integral_accurate(
                            (Xpol[i, 0], Xpol[i, 2]),  # x range
                            (Ypol[i, 0], Ypol[i, 2]),  # y range
                            event_data, d, s,
                            s_coeff=1.0,   # PPE Forecast: s_coeff outside integral
                            a_coeff=1.0    # PPE Forecast: weight already contains a
                        )
                        return result * coeff  # Multiply by coeff outside integral

                    # Parallel computation for all grid cells
                    ExpE = np.array(Parallel(n_jobs=-1)(delayed(compute_cell_integral)(i) for i in range(celln)))

            # Record forecast results for current magnitude bin
            PREVISIONI_3m[Nrow, 0] = time_s
            PREVISIONI_3m[Nrow, 1:] = ExpE
            Nrow += 1
            m1 = m2  # Move to next magnitude bin

    # ===== Save forecast results =====
    output_file = paths['ppeOut']
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    sio.savemat(output_file, {'PREVISIONI_3m': PREVISIONI_3m})
    print(f'✅ PPE forecast results saved to: {output_file}')
    print(f'   Forecast matrix shape: {PREVISIONI_3m.shape} (windows×magnitude bins={N_tre_M}×25, grid cells={celln})')

    return PREVISIONI_3m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PPE Earthquake Forecasting')
    parser.add_argument('--config', default='../src/config_decluster_include921.json')
    parser.add_argument('--test', action='store_true', help='Test mode (forecast only 1 month)')
    parser.add_argument('--accurate', action='store_true',
                        help='Use accurate mode (dblquad integration, slower but more precise)')
    parser.add_argument('--spatial-samples', type=int, default=50,
                        help='Number of sampling points for fast mode (default 50, increasing improves precision)')
    parser.add_argument('--ppe-ref-mag', choices=['m0', 'mT'], default='mT',
                        help='PPE reference magnitude: m0 or mT (default: mT, paper version)')
    args = parser.parse_args()

    # Decide which mode to use
    use_fast_mode = not args.accurate
    if args.accurate:
        print('⚠️  Using accurate mode (dblquad), slower but higher precision', flush=True)
    else:
        print(f'✅ Using fast mode (spatial_samples={args.spatial_samples})', flush=True)

    print(f'Using PPE reference magnitude: {args.ppe_ref_mag}', flush=True)

    if args.test:
        # Test mode: forecast only 1 month in 2016
        ppe_make_forecast(args.config, forecast_start_year=2016, forecast_end_year=2016.08,
                         use_fast_mode=use_fast_mode, spatial_samples=args.spatial_samples, ppe_ref_mag=args.ppe_ref_mag)
    else:
        ppe_make_forecast(args.config, use_fast_mode=use_fast_mode, spatial_samples=args.spatial_samples, ppe_ref_mag=args.ppe_ref_mag)
