#!/usr/bin/env python3
"""
Aftershock Model Parameter Estimation

Estimate aftershock model parameters (ν, κ) to distinguish independent
events from aftershocks using an ETAS-like model.

Model: λ'(t,m,x,y) = ν·λ₀ + κ·Σλᵢ'

Independence weights wᵢ = ν·λ₀ / λ' are calculated for use in EEPAS learning.
"""

import numpy as np
import argparse
import os
import sys
from scipy.optimize import minimize
from utils.fminsearchcon import fminsearchcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.catalog_processor import CatalogProcessor
from utils.get_paths import get_paths
from neg_log_like_aftershock import neg_log_like_aftershock


def fit_aftershock_params_fast(config_file='config.json', ppe_ref_mag=None, target_mag=None,
                               integration_mode='fast', spatial_samples=50):
    """
    Main function for aftershock parameter estimation.

    Workflow:

        1. Load parameters a, d, s learned from Step 1 (PPE)
        2. Prepare earthquake catalogs (precursors, targets, PPE sources)
        3. Optimize v, k parameters using maximum likelihood estimation (MLE)
        4. Save results for use in Step 3 (EEPAS)

    Args:
        config_file: Path to configuration file
        ppe_ref_mag: PPE reference magnitude, 'm0' or 'mT' (default: 'mT')
        integration_mode: Integration mode, 'fast' (trapezoidal) or 'accurate' (dblquad)
        spatial_samples: Grid resolution for fast mode
        target_mag: Target event magnitude threshold, 'm0' or 'mT' (default: 'm0'), controls the lower bound of integration and magnitude range of summed events

    Returns:
        dict: Dictionary containing optimized parameters {v, k, nll, success, ...}
    """

    # ===== Load configuration and PPE parameters =====
    cfg = DataLoader.load_config(config_file)
    params = DataLoader.load_model_params(config_file)

    # Determine PPE reference magnitude
    if ppe_ref_mag is None:
        ppe_ref_mag = 'mT'  # Default to mT

    if ppe_ref_mag == 'm0':
        ppe_ref_mag_value = params['m0']
        print(f'Using PPE reference magnitude: m0 = {ppe_ref_mag_value}', flush=True)
    elif ppe_ref_mag == 'mT':
        ppe_ref_mag_value = params['mT']
        print(f'Using PPE reference magnitude: mT = {ppe_ref_mag_value}', flush=True)
    else:
        raise ValueError(f'Invalid ppe_ref_mag: {ppe_ref_mag}, must be "m0" or "mT"')

    # Determine target event magnitude threshold (lower bound for integration and summation)
    if target_mag is None:
        target_mag = 'mT'  # Default to mT

    if target_mag == 'm0':
        target_mag_value = params['m0']
        print(f'Using target event magnitude threshold: m0 = {target_mag_value}', flush=True)
    elif target_mag == 'mT':
        target_mag_value = params['mT']
        print(f'Using target event magnitude threshold: mT = {target_mag_value}', flush=True)
    else:
        raise ValueError(f'Invalid target_mag: {target_mag}, must be "m0" or "mT"')

    # Get PPE parameter file path
    paths = get_paths(cfg, cfg['learnStartYear'], cfg['learnEndYear'],
                      cfg['forecastStartYear'], cfg['forecastEndYear'], config_file=config_file)
    ppe_param_file = paths['ppeParam']

    # Check if PPE parameters exist (depends on results from Step 1)
    if not os.path.exists(ppe_param_file):
        raise FileNotFoundError(f'Cannot find fitted PPE parameter file: {ppe_param_file} (please complete PPE fitting first)')

    # Load PPE parameters a, d, s
    # These parameters are used to calculate spatial earthquake kernels, the basis for aftershock de-weighting
    ppe_params = np.genfromtxt(ppe_param_file, delimiter=',', names=True)
    a, d, s = ppe_params['a'], ppe_params['d'], ppe_params['s']
    print(f'Loaded PPE parameters: a={a:.6g}, d={d:.6g}, s={s:.6g}', flush=True)

    # ===== Load earthquake catalogs =====
    HORUS, _, CELLE = DataLoader.load_catalogs(config_file)

    # Load spatial region configuration (optional for spatial filtering)
    try:
        regions = DataLoader.load_spatial_regions(config_file)
        # Create RegionManager
        from utils.region_manager import RegionManager
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
        # Backward compatibility: if unable to load region configuration, no spatial filtering applied
        print(f'Region configuration not loaded (no spatial filtering): {e}')
        region_manager = None

    # Preprocessing: filter by time range and magnitude
    HORUS_proc, _, _ = CatalogProcessor.preprocess_catalog(
        HORUS, cfg['catalogStartYear'], cfg['learnStartYear'], cfg['learnEndYear'],
        completeness_threshold=params['m0'], filter_target_mag=False, verbose=True
    )

    # Convert time to relative days (from catalogStartYear)
    T1 = (cfg['learnStartYear'] - cfg['catalogStartYear']) * 365.2425
    T2 = (cfg['learnEndYear'] - cfg['catalogStartYear']) * 365.2425

    # ===== Build three earthquake catalogs (with spatial region filtering support) =====
    # Spatial filtering behavior:
    #   - Without region filtering (region_manager=None):
    #     All catalogs use the same spatial extent (entire study region)
    #   - With region filtering (region_manager!=None):
    #     * CatPrecursors, CatI: from neighborhood region (to avoid boundary effects)
    #     * CatTargets: from testing region R (the region we care about predicting)

    # 1. CatPrecursors: All earthquakes that may produce aftershocks (M≥m0, t<T2)
    #    Purpose: Calculate aftershock density function λᵢ'
    #    Spatial extent: neighborhood region (boundary compensation)
    #    Note: Always use m0, because EEPAS needs to classify all M≥m0 earthquakes
    CatPrecursors_all = HORUS_proc[(HORUS_proc[:, 10] < T2) & (HORUS_proc[:, 9] >= params['m0'])]

    if region_manager is not None:
        # With region filtering: filter to neighborhood region
        CatPrecursors = CatalogProcessor.filter_by_region(
            CatPrecursors_all, region_manager, region_type='neighborhood'
        )
        print(f'  Precursors spatial filtering: {len(CatPrecursors_all)} → {len(CatPrecursors)} (neighborhood region)')
    else:
        # Without region filtering: use all events
        CatPrecursors = CatPrecursors_all

    # 2. CatI: Earthquakes used by PPE model (M≥ppe_ref_mag_value, t<T2)
    #    Purpose: Calculate spatial kernel h₀(x,y) for background rate λ₀
    #    Spatial extent: neighborhood region (boundary compensation)
    #    Note:
    #      - If ppe_ref_mag='mT': use M≥mT earthquakes (PPE parameters fitted with mT)
    #      - If ppe_ref_mag='m0': use M≥m0 earthquakes (PPE parameters fitted with m0)
    CatI_all = HORUS_proc[(HORUS_proc[:, 10] < T2) & (HORUS_proc[:, 9] >= ppe_ref_mag_value)]

    if region_manager is not None:
        # With region filtering: filter to neighborhood region
        CatI = CatalogProcessor.filter_by_region(
            CatI_all, region_manager, region_type='neighborhood'
        )
        print(f'  PPE sources spatial filtering (M≥{ppe_ref_mag_value}): {len(CatI_all)} → {len(CatI)} (neighborhood region)', flush=True)
    else:
        # Without region filtering: use all events
        CatI = CatI_all

    # 3. CatTargets: Target earthquakes during learning period (M≥target_mag, T1≤t<T2)
    #    Purpose: These are the "observed data" we use to estimate parameters
    #    Spatial extent: testing region R (the region we care about predicting)
    #    Note: target_mag controls the summation range of Σ log λ' and the integration lower bound
    #          However, the aftershock term κΣλᵢ' inside λ' still sums over all M≥m0 precursors
    CatTargets_all = HORUS_proc[(HORUS_proc[:, 10] >= T1) & (HORUS_proc[:, 10] < T2) &
                                (HORUS_proc[:, 9] >= target_mag_value)]

    if region_manager is not None:
        # With region filtering: filter to testing region R
        CatTargets = CatalogProcessor.filter_by_region(
            CatTargets_all, region_manager, region_type='testing'
        )
        print(f'  Target events spatial filtering: {len(CatTargets_all)} → {len(CatTargets)} (testing region R)')
    else:
        # Without region filtering: use all events
        CatTargets = CatTargets_all

    print(f'\nAftershock model catalog statistics:')
    print(f'  Source events (Precursors, M≥{params["m0"]:.1f}): {len(CatPrecursors)}')
    print(f'  PPE sources (CatI, M≥{ppe_ref_mag_value:.1f}): {len(CatI)}')
    print(f'  Target events (Targets, [T1,T2), M≥{target_mag_value:.1f}): {len(CatTargets)}')
    print(f'  Integration lower bound (target_mag): {target_mag_value:.1f}')

    if len(CatTargets) == 0:
        raise ValueError('Target event set is empty (check learnStartYear / learnEndYear or m0 settings)')

    # ===== Set optimization initial values and bounds =====
    from scipy.optimize import Bounds
    x0 = np.array([0.5, 0.1])  # Initial guess: v=0.5 (50% non-aftershocks), k=0.1
    bounds = Bounds([0.0, 0.0], [np.inf, np.inf])  # v, k must be ≥0

    # ===== Define optimization objective function =====
    # Warm up compiler (first call will compile)
    print("Preparing aftershock model optimization...")
    _ = neg_log_like_aftershock(x0[0], x0[1], CatTargets, CatPrecursors, CatI, a, d, s, T1, T2, params, CELLE,
                                region_manager=region_manager, ppe_ref_mag=ppe_ref_mag_value, target_mag=target_mag_value,
                                integration_mode=integration_mode, spatial_samples=spatial_samples)

    iteration_count = [0]
    def objective(x):
        """
        Objective function: Calculate negative log-likelihood of aftershock model.

        Args:
            x[0] = v (ν): Independent event proportion
            x[1] = k (κ): Aftershock normalization constant

        Returns:
            Negative log-likelihood (smaller is better)
        """
        nll = neg_log_like_aftershock(
            x[0], x[1], CatTargets, CatPrecursors, CatI,
            a, d, s, T1, T2, params, CELLE, region_manager=region_manager, ppe_ref_mag=ppe_ref_mag_value, target_mag=target_mag_value,
            integration_mode=integration_mode, spatial_samples=spatial_samples
        )
        iteration_count[0] += 1
        if iteration_count[0] % 10 == 0:
            print(f'Iteration {iteration_count[0]:4d}: v = {x[0]:.6f}, k = {x[1]:.6f}, NLL = {nll:.3f}')
        return nll

    # ===== Execute maximum likelihood estimation =====
    print('Starting aftershock model parameter optimization...')

    lb = np.array([0.0, 0.0])  # Lower bounds for v, k
    ub = np.array([1, 2000])  # Upper bounds for v, k

    options = {
        'maxiter': 100000,
        'xtol': 1e-8,
        'ftol': 1e-8,
        'disp': True
    }

    x_optimal, fval, exitflag, output = fminsearchcon(
        objective, x0, lb=lb, ub=ub, options=options
    )

    v_hat, k_hat = x_optimal
    success = (exitflag == 0)

    print(f'Optimization completed: v = {v_hat:.6f}, k = {k_hat:.6f}, NLL = {fval:.3f}, success = {success}')

    # ===== Save results =====
    # These parameters will be used in the next step to calculate weights wᵢ
    aftershock_param_pattern = cfg['outputFiles']['AftershockParamPattern']
    aftershock_param_file = os.path.join(
        cfg['resultsDir'],
        aftershock_param_pattern % (cfg['learnStartYear'], cfg['learnEndYear'])
    )

    os.makedirs(os.path.dirname(aftershock_param_file), exist_ok=True)

    # Save in CSV format
    with open(aftershock_param_file, 'w') as f:
        f.write('v,k,ln_likelihood\n')
        f.write(f'{v_hat},{k_hat},{-fval}\n')  # Note: save positive log-likelihood

    print(f'Aftershock parameters saved to: {aftershock_param_file}')
    print(f'Interpretation: v={v_hat:.3f} means approximately {v_hat*100:.1f}% of earthquakes are not aftershocks')

    return {
        'v': v_hat,           # Independent event proportion (ν)
        'k': k_hat,           # Aftershock normalization constant (κ)
        'nll': fval,          # Negative log-likelihood
        'success': success,   # Whether optimization succeeded
        'x0': x0,             # Initial values
        'T1': T1, 'T2': T2,   # Time range
        'numTargets': len(CatTargets),  # Number of target earthquakes
        'exitflag': exitflag,
        'output': output
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='EEPAS Model Step 2: Estimate aftershock model parameters for weight calculation'
    )
    parser.add_argument('--config', default='../config.json',
                        help='Path to configuration file')
    parser.add_argument('--ppe-ref-mag', choices=['m0', 'mT'], default='mT',
                        help='PPE reference magnitude: m0 (completeness magnitude) or mT (target magnitude), default: mT')
    parser.add_argument('--target-mag', choices=['m0', 'mT'], default='mT',
                        help='Target event magnitude threshold: m0 or mT, controls integration lower bound and summation event range, default: mT (paper version)')
    parser.add_argument('--accurate', action='store_true',
                        help='Use accurate mode (dblquad adaptive integration, slow but very high precision)')
    parser.add_argument('--spatial-samples', type=int, default=50,
                        help='Grid resolution for fast mode (default: 50)')

    args = parser.parse_args()

    # Determine integration mode
    if args.accurate:
        integration_mode = 'accurate'
        print('Warning: Using accurate mode (dblquad), will be slower but higher precision', flush=True)
    else:
        integration_mode = 'fast'
        print(f'Using fast mode (trapezoidal method, spatial_samples={args.spatial_samples})', flush=True)

    result = fit_aftershock_params_fast(
        args.config,
        ppe_ref_mag=args.ppe_ref_mag,
        target_mag=args.target_mag,
        integration_mode=integration_mode,
        spatial_samples=args.spatial_samples
    )

    print('\n===== Aftershock Model Parameter Estimation Results =====')
    print(f'v (independent event proportion) = {result["v"]:.10f} ({result["v"]*100:.2f}%)')
    print(f'k (aftershock constant)          = {result["k"]:.10f}')
    print(f'NLL                              = {result["nll"]:.10f}')
    print(f'Optimization success             = {result["success"]}')

