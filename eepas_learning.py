#!/usr/bin/env python3
"""
EEPAS Model Parameter Learning

Core implementation for EEPAS parameter optimization.

Workflow: Load catalog → Calculate weights → Optimize parameters → Save results

Note: Use eepas_learning_auto_boundary.py for automatic boundary adjustment.
"""

import numpy as np
import argparse
import os
import sys
from scipy.optimize import minimize, Bounds
from scipy.special import erf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.catalog_processor import CatalogProcessor
from utils.region_manager import RegionManager
from utils.get_paths import get_paths
from eepas_likelihood import eepas_likelihood
from calculate_earthquake_weights import calculate_earthquake_weights
from optimize_eepas_parameters import optimize_eepas_parameters, optimize_custom_stages


def eepas_learning(config_file='config.json',
                        catalog_start_year=None,
                        learn_start_year=None,
                        learn_end_year=None,
                        weight_flag=None,
                        m0=None,
                        delay=None,
                        multi_start=False,
                        n_starts=3,
                        single_stage=False,
                        use_basinhopping=False,
                        basinhopping_niter=20,
                        optimizer='fminsearchcon',
                        ppe_ref_mag=None,
                        use_fast_mode=False,
                        magnitude_samples=20):
    """
    EEPAS model parameter learning main function.

    Workflow:
        1. Load earthquake catalog and preprocess
        2. Calculate aftershock declustering weights W
        3. Call optimize_eepas_parameters to perform optimization (three-stage or single-stage)
        4. Save learning results to CSV

    Args:
        config_file: Configuration file path (contains PPE parameters, optimization settings, etc.)
        catalog_start_year: Catalog start year (default from config file)
        learn_start_year: Learning start year (default from config file)
        learn_end_year: Learning end year (default from config file)
        weight_flag: Weight calculation mode (default from config file)
        m0: Completeness magnitude (default from config file)
        delay: Delay in days (default from config file)
        multi_start: Whether to use multi-start search (default False)
        n_starts: Number of multi-start points (default 3)
        single_stage: Whether to use single-stage full parameter optimization (default False, use three-stage)

    Returns:
        result: Dictionary containing optimal EEPAS parameters and negative log-likelihood value
    """

    # Load configuration
    cfg = DataLoader.load_config(config_file)
    params = DataLoader.load_model_params(config_file)

    # Parameter override
    catalog_start_year = catalog_start_year or cfg['catalogStartYear']
    learn_start_year = learn_start_year or cfg['learnStartYear']
    learn_end_year = learn_end_year or cfg['learnEndYear']

    if m0 is not None:
        params['m0'] = m0
    if delay is not None:
        params['delay'] = delay
    if weight_flag is not None:
        params['weightFlag'] = weight_flag
    else:
        weight_flag = params.get('weightFlag', 1)

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
        params['ppe_ref_mag_value'] = ppe_ref_mag  # Use numeric value directly

    paths = get_paths(cfg, learn_start_year, learn_end_year,
                      cfg['forecastStartYear'], cfg['forecastEndYear'])

    print('='*80)
    print('EEPAS Model Parameter Learning - Numba Accelerated Version')
    print('='*80)
    print(f'Config file: {config_file}')
    print(f'Learning period: {learn_start_year} - {learn_end_year}')
    print(f'Completeness magnitude: m0={params["m0"]}')
    print('='*80)

    print('\nLoading earthquake catalog data...')
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
        # Backward compatibility: if unable to load region config, no spatial filtering applied
        print(f'Region configuration not loaded (no spatial filtering): {e}')
        region_manager = None

    # Preprocessing
    HORUS, T1, T2 = CatalogProcessor.preprocess_catalog(
        HORUS, catalog_start_year, learn_start_year, learn_end_year,
        completeness_threshold=params['m0'], verbose=True
    )

    # Create EEPAS-required catalogs (using region-aware method)
    print('Creating earthquake sub-catalogs...')
    CatE, CatI, CatJ = CatalogProcessor.create_catalogs_with_regions(
        HORUS, params, learn_start_year, learn_end_year, catalog_start_year,
        region_manager=region_manager
    )

    # Load PPE parameters
    print('\nLoading PPE parameters...')
    results_dir = cfg['resultsDir']
    if not os.path.isabs(results_dir):
        # Use current working directory, consistent with other modules
        results_dir = os.path.abspath(results_dir)
    ppe_param_pattern = cfg['outputFiles']['PPEParamPattern']
    ppe_param_file = os.path.join(
        results_dir,
        ppe_param_pattern % (learn_start_year, learn_end_year)
    )

    if not os.path.exists(ppe_param_file):
        raise FileNotFoundError(
            f'PPE parameter file not found: {ppe_param_file}\n'
            f'Please run ppe_learning_tw_fast.py first to generate this file'
        )

    ppe_params = np.genfromtxt(ppe_param_file, delimiter=',', names=True)
    params['a'] = ppe_params['a']
    params['d'] = ppe_params['d']
    params['s'] = ppe_params['s']
    print(f'PPE parameters: a={params["a"]:.6f}, d={params["d"]:.6f}, s={params["s"]:.6f}')

    # Calculate earthquake weights
    if weight_flag == 0:
        print('\nSkipping weight calculation (weight_flag=0), using W=1')
        W = np.ones(len(CatE))
        EW = 1.0
    else:
        print('\nCalculating earthquake weights...')
        W, EW, CatE = calculate_earthquake_weights(
            CatE, CatI, params, weight_flag, params['delay'], config_file, ppe_ref_mag
        )
        print(f'Weight calculation complete: EW = {EW:.6f}')

    # Extract data vectors
    me = CatE[:, 9]
    xe = CatE[:, 7]
    te = CatE[:, 10]
    ye = CatE[:, 6]

    # Historical source events (paper's i) - from neighborhood region
    mi = CatI[:, 9]
    xi = CatI[:, 7]
    ti = CatI[:, 10]
    yi = CatI[:, 6]

    # Target events (paper's j) - from testing region
    mj = CatJ[:, 9]
    xj = CatJ[:, 7]
    tj = CatJ[:, 10]
    yj = CatJ[:, 6]

    # Calculate basic parameters
    B = params['B'] * np.log(10)

    print(f'\nData statistics:')
    print(f'  EEPAS foreshocks: {len(me)}')
    print(f'  Historical source events (paper\'s i): {len(mi)}')
    print(f'  Target earthquakes (paper\'s j): {len(mj)}')
    print(f'  Grid cells: {len(CELLE)}')

    # Warm up Numba compilation
    print('\nWarming up Numba JIT compiler...')
    _ = eepas_likelihood(
        0.5, 1.0, 0.3, -1.0, 0.5, 0.5, 1.0, 10.0, 0.5,
        mj, xj, tj, yj, xi, yi, mi, ti,
        me, xe, te, ye, W, EW, B, T1, T2, params['m0'],
        CELLE, params
    )
    print('JIT compilation complete!')

    # Execute parameter optimization (custom stages, three-stage, or single-stage)
    # Check if custom stages are enabled
    custom_config = DataLoader.load_custom_stages(config_file)

    if custom_config is not None:
        # Use custom stages optimization
        print('\nStarting EEPAS parameter optimization (custom stages, Numba accelerated)...')
        print(f'Number of stages: {len(custom_config["stages"])}')
        print('='*80)
        result = optimize_custom_stages(
            mj, xj, tj, yj, xi, yi, mi, ti,
            me, xe, te, ye, W, EW, B, T1, T2, params['m0'],
            CELLE, params, config_file,
            optimizer=optimizer, region_manager=region_manager,
            use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples
        )
    else:
        # Use standard optimization (three-stage or single-stage)
        if single_stage:
            print('\nStarting EEPAS parameter optimization (single-stage full parameter optimization, Numba accelerated)...')
        else:
            print('\nStarting EEPAS parameter optimization (three-stage optimization, Numba accelerated)...')
        print('='*80)
        result = optimize_eepas_parameters(
            mj, xj, tj, yj, xi, yi, mi, ti,
            me, xe, te, ye, W, EW, B, T1, T2, params['m0'],
            CELLE, params, config_file,
            multi_start=multi_start, n_starts=n_starts, single_stage=single_stage,
            use_basinhopping=use_basinhopping, basinhopping_niter=basinhopping_niter,
            optimizer=optimizer, region_manager=region_manager,
            use_fast_mode=use_fast_mode, magnitude_samples=magnitude_samples
        )

    # Save results
    output_pattern = cfg['outputFiles']['EEPASParamPattern']
    output_file = os.path.join(
        results_dir,
        output_pattern % (learn_start_year, learn_end_year)
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write CSV
    header = 'am,bm,Sm,at,bt,St,ba,Sa,u,ln_likelihood'
    data = np.array([
        result['am'], result['bm'], result['Sm'],
        result['at'], result['bt'], result['St'],
        result['ba'], result['Sa'], result['u'],
        result['ln_likelihood']
    ])
    np.savetxt(output_file, data.reshape(1, -1), delimiter=',', header=header, comments='')

    print(f'\nEEPAS parameters saved to: {output_file}')
    print(f'ln_likelihood = {result["ln_likelihood"]:.6f}')
    print('\nUsing Numba acceleration, expected to be 10x faster than original version!')

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EEPAS Model Parameter Learning - Numba Accelerated')
    parser.add_argument('--config', default='../config_eepas_test.json')
    parser.add_argument('--m0', type=float, help='Completeness magnitude (4.0 recommended for acceleration)')
    parser.add_argument('--multi_start', action='store_true', help='Use multi-start search for improved robustness')
    parser.add_argument('--n_starts', type=int, default=3, help='Number of multi-start points (default 3)')
    parser.add_argument('--ppe-ref-mag', choices=['m0', 'mT'], default=None,
                        help='PPE reference magnitude: m0 or mT (default uses mT)')
    parser.add_argument('--fast', action='store_true',
                        help='Use fast mode (midpoint rectangle method instead of quad_vec)')
    parser.add_argument('--n-samples', type=int, default=20,
                        help='Number of sampling points for fast mode (default 20)')
    args = parser.parse_args()

    eepas_learning(args.config, m0=args.m0, multi_start=args.multi_start, n_starts=args.n_starts,
                   ppe_ref_mag=args.ppe_ref_mag, use_fast_mode=args.fast, magnitude_samples=args.n_samples)