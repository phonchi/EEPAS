#!/usr/bin/env python3
"""
PPE Model Parameter Learning

Learn PPE (Proximity to Past Earthquakes) model parameters using Maximum Likelihood Estimation.

The PPE model decomposes earthquake occurrence rate into:
- Influence of historical earthquakes (seismic kernels)
- Uniform background seismicity

Parameters learned: a (intensity), d (distance decay, km), s (background rate)
"""

import numpy as np
import pandas as pd
import argparse
import os
import sys

# Add current directory to Python path for importing utils module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.catalog_processor import CatalogProcessor
from utils.region_manager import RegionManager
from utils.get_paths import get_paths
from utils.fminsearchcon import fminsearchcon
from ppe_optimization import optimization_ppe


def ppe_learning_fast(config_file='config.json', catalog_start_year=None, learn_start_year=None,
                         learn_end_year=None, m0=None, mT=None, fit_mode='joint', spatial_samples=50,
                         use_fast_mode=True, ppe_ref_mag='mT'):
    """
    Learn PPE model parameters using Maximum Likelihood Estimation.

    Args:
        config_file: Configuration JSON file path
        catalog_start_year: Catalog start year (optional, overrides config)
        learn_start_year: Learning period start year (optional, overrides config)
        learn_end_year: Learning period end year (optional, overrides config)
        m0: Completeness magnitude (optional, overrides config)
        mT: Target magnitude threshold (optional, overrides config)
        fit_mode: 'joint' (optimize a,d,s) or 'decoupled_gr' (fix a=1)
        spatial_samples: Grid resolution for integration (default: 50)
        use_fast_mode: Use fast trapezoidal integration (default: True)
        ppe_ref_mag: Magnitude reference: 'mT' or 'm0' (default: 'mT')

    Returns:
        dict: Fitted parameters containing {'a': float, 'd': float, 's': float, 'ln_L': float}
    """

    # ===== Model Configuration Options =====
    profile_opts = {
        'kernelMagFilter': ppe_ref_mag,     # Kernel magnitude filter criterion: 'mT' or 'm0'
        'integralLower': ppe_ref_mag,       # Integration lower limit: 'mT' or 'm0'
        'magDistReference': ppe_ref_mag,    # Magnitude distribution reference point: 'mT' (paper version) or 'm0' (old version)
        'mu': 7.5,                          # Magnitude upper limit (for G-R relation normalization)
        'exact_boundary': True,             # Use exact boundary calculation (vs approximation)
        'verbose': True                     # Display verbose output
    }

    # ===== Load Configuration and Data =====
    cfg = DataLoader.load_config(config_file)
    params = DataLoader.load_model_params(config_file)

    # Set time ranges (use config file if not specified)
    if catalog_start_year is None:
        catalog_start_year = cfg['catalogStartYear']
    if learn_start_year is None:
        learn_start_year = cfg['learnStartYear']
    if learn_end_year is None:
        learn_end_year = cfg['learnEndYear']

    # Check time logic validity
    # Requirement: catalog_start < learn_start < learn_end
    # Reason: Need historical earthquake data before learn_start to build the model
    if learn_start_year <= catalog_start_year:
        raise ValueError('Learning start year must be greater than catalog start year')
    if learn_end_year <= learn_start_year:
        raise ValueError('Learning end year must be greater than learning start year')

    # Set magnitude parameters
    if m0 is None:
        m0 = params['m0']  # Completeness magnitude
    if mT is None:
        mT = params['mT']  # Target magnitude threshold
    if m0 < 0:
        raise ValueError('Completeness magnitude (m0) must be non-negative')

    # Load earthquake catalog
    # HORUS: Main earthquake catalog (contains time, location, magnitude, etc.)
    # CELLE: Grid cells of the study region (defines spatial boundaries)
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
    except Exception as e:
        # Backward compatibility: If region config cannot be loaded, no spatial filtering applied
        print(f'Region configuration not loaded (no spatial filtering): {e}')
        region_manager = None

    # ===== Data Preprocessing =====
    # Determine magnitude filtering threshold for seismic kernels
    # kernelMagFilter='mT': Only historical earthquakes with M≥mT can form kernels
    # kernelMagFilter='m0': All earthquakes with M≥m0 can form kernels
    filter_threshold = mT
    if profile_opts.get('kernelMagFilter', 'mT').lower() == 'm0':
        filter_threshold = m0

    print(f'Debug: kernelMagFilter={profile_opts.get("kernelMagFilter", "mT")}, '
          f'filter_threshold={filter_threshold:.2f}, m0={m0:.2f}, mT={mT:.2f}')

    # Preprocess earthquake catalog: filter by time range and magnitude
    # T1: Learning period start time (decimal year)
    # T2: Learning period end time (decimal year)
    HORUS, T1, T2 = CatalogProcessor.preprocess_catalog(
        HORUS, catalog_start_year, learn_start_year, learn_end_year,
        completeness_threshold=m0, filter_target_mag=True,
        target_magnitude=filter_threshold, verbose=True
    )

    # ===== Create Two Earthquake Catalogs =====
    # Use region-aware catalog creation method
    # - Without region filtering (region_manager=None): No spatial filtering
    # - With region filtering (region_manager!=None): Use spatial region filtering
    #   * CatI: Historical source events within neighborhood region N (paper's i) - for kernel contributions
    #   * CatJ: Target events within testing region R (paper's j) - for likelihood sum

    # First filter by magnitude threshold for historical source events
    CatI_all = HORUS[HORUS[:, 9] >= filter_threshold]

    # Apply spatial filtering (if region_manager exists)
    if region_manager is not None:
        # With region filtering: Filter by neighborhood region
        CatI_all = CatalogProcessor.filter_by_region(
            CatI_all, region_manager, region_type='neighborhood'
        )

    # CatI (Historical source event catalog - paper's i): All historical earthquakes with M≥filter_threshold
    #   - Used to calculate "seismic kernel" contributions
    #   - Includes earthquakes before and during the learning period
    #   - From neighborhood region N
    mi, ti, yi, xi = CatI_all[:, 9], CatI_all[:, 10], CatI_all[:, 6], CatI_all[:, 7]
    # mi: magnitude, ti: time (decimal year), yi: latitude, xi: longitude

    # CatJ (Target event catalog - paper's j): Earthquakes with M≥mT during the learning period
    #   - These are the actual observations used to "validate" the model
    #   - Only includes earthquakes within the learning period (learn_start ~ learn_end)
    #   - From testing region R
    CatJ = HORUS[HORUS[:, 0] >= learn_start_year]
    CatJ = CatJ[CatJ[:, 9] >= filter_threshold]

    # Apply spatial filtering (if region_manager exists)
    if region_manager is not None:
        # With region filtering: Filter by testing region (forecast region)
        CatJ = CatalogProcessor.filter_by_region(
            CatJ, region_manager, region_type='testing'
        )

    mj, tj, yj, xj = CatJ[:, 9], CatJ[:, 10], CatJ[:, 6], CatJ[:, 7]

    print(f'PPE historical source events (CatI, paper\'s i): {len(mi)}, target events (CatJ, paper\'s j): {len(mj)}')

    # ===== Prepare Spatial Grid =====
    # Convert CELLE grid cells to polygon vertices
    # Each grid cell is a rectangle defined by 4 vertices
    Xpol = np.column_stack([CELLE[:, 0], CELLE[:, 0], CELLE[:, 1], CELLE[:, 1]])
    Ypol = np.column_stack([CELLE[:, 2], CELLE[:, 3], CELLE[:, 3], CELLE[:, 2]])
    # Format: [bottom-left, top-left, top-right, bottom-right]

    # ===== Load Fixed Parameters =====
    # B: b-value of Gutenberg-Richter relation (converted to natural logarithm)
    #    Commonly used in seismology: b≈1.0, i.e., log10(N) = a - b*M
    B = params['B'] * np.log(10)

    # delay: Time delay parameter (unit: years)
    #    Physical meaning: How long after an earthquake occurs before it starts producing "seismic kernel" effects
    #    Usually set to a small value (e.g., 0.01 years)
    delay = params['delay']

    print(f'\nStarting PPE parameter optimization (grid resolution={spatial_samples}x{spatial_samples})...')

    # Warm up compiler (first call requires compilation)
    _ = optimization_ppe(
        CELLE, 0.005, 10.0, 0.1, xj, yj, mj, tj, xi, yi, mi, ti, mT,
        Xpol, Ypol, None, B, delay, m0, fit_mode, profile_opts,
        T1=T1, T2=T2, spatial_samples=spatial_samples,
        region_manager=region_manager, use_fast_mode=use_fast_mode
    )
    print('Starting parameter optimization...\n')

    # ===== Parameter Optimization =====
    # Use Maximum Likelihood Estimation (MLE) to find optimal parameters

    if fit_mode == 'decoupled_gr':
        # ===== Mode 1: decoupled_gr =====
        # Assume a=1 (fixed), optimize only d and s
        # Purpose: Simplify the problem, suitable for initial exploration

        # Initial guess [d, s]
        x0 = np.array([10.0, 0.1])
        # d=10km (typical earthquake clustering scale)
        # s=0.1 (background seismicity rate)

        # Parameter bounds
        lb = np.array([0.1, 0.0])      # Lower bounds: d≥0.1km, s≥0
        ub = np.array([np.inf, 1.0])   # Upper bounds: d unlimited, s≤1

        def fun(x):
            # Calculate negative log-likelihood function (smaller is better)
            val = optimization_ppe(
                CELLE, 1.0, x[0], x[1], xj, yj, mj, tj, xi, yi, mi, ti, mT,
                Xpol, Ypol, None, B, delay, m0, fit_mode, profile_opts,
                T1=T1, T2=T2, spatial_samples=spatial_samples,
                region_manager=region_manager, use_fast_mode=use_fast_mode
            )
            return val

        # Execute constrained optimization
        final_params, fval, exitflag, output = fminsearchcon(
            fun, x0, lb=lb, ub=ub,
            options={'maxiter': 5500, 'xtol': 1e-8, 'ftol': 1e-8, 'disp': True}
        )
        final_params = np.array([np.nan, final_params[0], final_params[1]])
        # Format: [a (to be calculated), d, s]

    else:
        # ===== Mode 2: joint (recommended) =====
        # Optimize a, d, s simultaneously
        # Advantage: More flexible, can find global optimal solution

        # Initial guess [a, d, s]
        x0 = np.array([0.005, 10.0, 0.1])
        # a=0.005 (start with small value to avoid overfitting)
        # d=10km, s=0.1 (same as above)

        # Parameter bounds
        lb = np.array([0.0, 0.1, 1e-15])      # Lower bounds (s changed to 1e-15 to allow smaller values)
        ub = np.array([2000, 2000, 1.0])      # Upper bounds
        # a upper bound 2000: Prevent numerical overflow
        # d upper bound 2000km: Exceeds Taiwan scale
        # s lower bound 1e-15: Paper's s is approximately 9e-13

        def fun(x):
            # Calculate negative log-likelihood function
            val = optimization_ppe(
                CELLE, x[0], x[1], x[2], xj, yj, mj, tj, xi, yi, mi, ti, mT,
                Xpol, Ypol, None, B, delay, m0, fit_mode, profile_opts,
                T1=T1, T2=T2, spatial_samples=spatial_samples,
                region_manager=region_manager, use_fast_mode=use_fast_mode
            )
            return val

        # Execute constrained optimization
        final_params, fval, exitflag, output = fminsearchcon(
            fun, x0, lb=lb, ub=ub,
            options={'maxiter': 5500, 'xtol': 1e-8, 'ftol': 1e-8, 'disp': True}
        )

    # ===== Calculate Final a Value =====
    # If using decoupled_gr mode, need to back-calculate a from d and s
    if fit_mode == 'decoupled_gr':
        from ppe_optimization import J_of_d_closed, single_J_i

        prof_threshold = mT
        weight_base_prof = mT
        if profile_opts.get('kernelMagFilter', 'mT').lower() == 'm0':
            prof_threshold = m0
            weight_base_prof = m0

        use_idx = (tj < np.max(ti) - delay) & (mj >= prof_threshold)
        xjN, yjN, mjN = xj[use_idx], yj[use_idx], mj[use_idx]

        AR = np.sum((Xpol[:, 2] - Xpol[:, 0]) * (Ypol[:, 2] - Ypol[:, 0]))

        if profile_opts.get('exact_boundary', True):
            sum_wJ = sum(max(0, mjN[k] - weight_base_prof) * single_J_i(final_params[1], xjN[k], yjN[k], Xpol, Ypol)
                         for k in range(len(mjN)))
            sum_wJ = max(sum_wJ, np.finfo(float).eps)
        else:
            Jd = J_of_d_closed(final_params[1], xjN, yjN, Xpol, Ypol)
            wbar = np.mean(mjN - weight_base_prof) if len(mjN) > 0 else np.finfo(float).eps
            wbar = max(wbar, np.finfo(float).eps)
            sum_wJ = wbar * Jd

        m_lower = mT
        if profile_opts.get('integralLower', 'mT').lower() == 'm0':
            m_lower = m0
        C_GR = 1.0 / (np.exp(-B * (m_lower - m0)) - np.exp(-B * (7.5 - m0)))
        a_star = (len(mjN) * (C_GR - final_params[2] * AR)) / sum_wJ if sum_wJ > 0 else 0.0
        a_star = max(0, a_star) if np.isfinite(a_star) else 0.0
    else:
        # joint mode: directly use the optimized a value
        a_star = final_params[0]

    # ===== Save Results =====
    fitted_par_ppe = {
        'a': a_star,              # Seismic kernel intensity
        'd': final_params[1],     # Spatial decay distance [km]
        's': final_params[2],     # Background seismicity rate
        'ln_likelihood': -fval    # Log-likelihood value (larger is better)
    }

    # Get output path and save as CSV
    ppe_param_file = get_paths(cfg, learn_start_year, learn_end_year)['ppeParam']
    os.makedirs(os.path.dirname(ppe_param_file), exist_ok=True)
    pd.DataFrame([fitted_par_ppe]).to_csv(ppe_param_file, index=False)

    print(f'\nSaved: {ppe_param_file}')
    print(f'   a={fitted_par_ppe["a"]:.6f}, d={fitted_par_ppe["d"]:.6f}, '
          f's={fitted_par_ppe["s"]:.6f}, ln_L={fitted_par_ppe["ln_likelihood"]:.2f}')

    return fitted_par_ppe


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PPE Model Parameter Learning')
    parser.add_argument('--config', default='../config.json',
                        help='Configuration file path')
    parser.add_argument('--fit-mode', default='joint', choices=['joint', 'decoupled_gr'],
                        help='Fitting mode: joint (optimize a,d,s simultaneously) or decoupled_gr (fix a=1)')
    parser.add_argument('--spatial-samples', type=int, default=50,
                        help='Number of spatial integration sampling points (default 50, recommended 20-50)')
    parser.add_argument('--accurate', action='store_true',
                        help='Use accurate mode (dblquad adaptive integration, slower but more precise)')
    parser.add_argument('--ppe-ref-mag', choices=['m0', 'mT'], default='mT',
                        help='PPE reference magnitude: m0 or mT (default: mT, paper version)')
    args = parser.parse_args()

    # If using accurate mode, spatial_samples will be ignored
    if args.accurate:
        print("WARNING: Using accurate mode (dblquad), slower but higher precision", flush=True)
        use_fast_mode = False
        spatial_res = None
    else:
        print(f"Using fast mode (spatial_samples={args.spatial_samples})", flush=True)
        use_fast_mode = True
        spatial_res = args.spatial_samples

    print(f"Using PPE reference magnitude: {args.ppe_ref_mag}", flush=True)

    ppe_learning_fast(args.config, fit_mode=args.fit_mode, spatial_samples=spatial_res,
                        use_fast_mode=use_fast_mode, ppe_ref_mag=args.ppe_ref_mag)
