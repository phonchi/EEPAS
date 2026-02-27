#!/usr/bin/env python3
"""
EEPAS Parameter Learning with Automatic Boundary Adjustment.

Learn EEPAS model parameters with automatic boundary adjustment to avoid
local optima caused by parameters hitting bounds during optimization.

Defaults: Three-stage + Multistart (3 starts) + fminsearchcon optimizer

Optimization Modes (in priority order):
    1. Custom Stages (if customStages enabled in config)
    2. Single-Stage (if --single-stage specified)
    3. Three-Stage (default, or if --three-stage specified)

Examples:
    Default (three-stage)::

        python3 eepas_learning_auto_boundary.py --config config.json

    Single-stage optimization::

        python3 eepas_learning_auto_boundary.py --config config.json --single-stage

    Custom stages (enable in config)::

        # Set "customStages": {"enable": true, "stages": [...]} in config.json
        python3 eepas_learning_auto_boundary.py --config config_custom.json
"""

import argparse
import json
import sys
from pathlib import Path

from eepas_learning import eepas_learning
from utils.auto_boundary_adjustment import check_boundary_hits, suggest_boundary_adjustment, save_adjusted_config
import numpy as np


def parse_result_csv(csv_path: str):
    """
    Parse EEPAS result CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        dict: Dictionary containing 9 EEPAS parameters (am, bm, Sm, at, bt, St, ba, Sa, u) and ln_likelihood
    """
    import pandas as pd
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        return None
    return df.iloc[0].to_dict()


def eepas_with_auto_boundary(
    config_path: str,
    m0: float = None,
    max_adjustment_rounds: int = 3,
    disable_boundary_adjustment: bool = False,
    tolerance: float = 0.01,
    expansion_factor: float = 2.0,
    nll_convergence_threshold: float = 0.1,
    single_stage: bool = True,
    multi_start: bool = True,
    n_starts: int = 3,
    use_basinhopping: bool = False,
    basinhopping_niter: int = 20,
    optimizer: str = 'fminsearchcon',
    ppe_ref_mag: str = None,
    use_fast_mode: bool = False,
    magnitude_samples: int = 50,
    lead_time_days: float = None
):
    """
    EEPAS parameter learning with automatic boundary adjustment.

    Workflow:

        1. Execute EEPAS optimization with current boundaries (three-stage or single-stage)
        2. Check if any result parameters hit boundaries
        3. If hit, relax boundaries and save new configuration
        4. Check if NLL has converged
        5. Repeat until convergence or maximum rounds reached

    Args:
        config_path: Configuration file path
        m0: Completeness magnitude (if not specified, uses value from config file)
        max_adjustment_rounds: Maximum boundary adjustment rounds (default: 3), usually converges in 2-3 rounds
        tolerance: Boundary hit detection tolerance (default: 0.01 = 1%), parameter distance to boundary < 1% is considered hitting
        expansion_factor: Boundary expansion factor (default: 2.0), lower bound: new = old / 2.0, upper bound: new = old * 2.0
        nll_convergence_threshold: NLL convergence threshold (default: 0.1), two consecutive rounds with improvement < 0.1 → automatic stop
        single_stage: Whether to use single-stage full parameter optimization (default: True, uses single-stage)
        multi_start: Whether to use multi-start optimization (default: True)
        n_starts: Number of multi-start points (default: 3)
        use_basinhopping: Whether to use basinhopping global optimization (default: False)
        basinhopping_niter: Number of basinhopping iterations (default: 20)
        optimizer: Optimizer to use: 'fminsearchcon', 'SLSQP', 'L-BFGS-B' (default: 'fminsearchcon')
        ppe_ref_mag: PPE reference magnitude: 'mT' or 'm0' (default: None, uses config)
        use_fast_mode: Whether to use fast magnitude integration (default: False)
        magnitude_samples: Number of magnitude samples for fast mode (default: 50)
        lead_time_days: Fixed lead time L in days for FLEEPAS (default: None)
            - None: Read from config's timeComp.lead_time_days, or use all historical precursors if not set
            - float: Only use earthquakes within [t-L, t-delay] as precursors (FLEEPAS mode)

    Returns:
        dict: Final parameter dictionary containing optimized EEPAS parameters
    """
    print('='*80)
    if single_stage:
        print('EEPAS Parameter Learning - Single-Stage Full Optimization + Automatic Boundary Adjustment')
    else:
        print('EEPAS Parameter Learning - Three-Stage Optimization + Automatic Boundary Adjustment')
    print('='*80)
    print(f'Configuration: {config_path}')
    print(f'Optimization mode: {"Single-stage full parameter optimization" if single_stage else "Three-stage optimization"}')
    print(f'Maximum adjustment rounds: {max_adjustment_rounds}')
    print(f'Boundary tolerance: {tolerance} (parameter distance to boundary <{tolerance*100:.1f}% is considered hitting)')
    print(f'Expansion factor: {expansion_factor}x')
    print(f'NLL convergence threshold: {nll_convergence_threshold}')
    print('='*80)

    # ===== Load initial configuration =====
    original_config_path = config_path  # save original config path
    current_config_path = config_path   # current config path in use

    with open(current_config_path, 'r') as f:
        config = json.load(f)

    results_dir = config.get('resultsDir', 'results_decluster')
    learn_start = config['learnStartYear']
    learn_end = config['learnEndYear']

    # Construct EEPAS result file path
    base_dir = Path(results_dir)
    if not base_dir.is_absolute():
        base_dir = Path(current_config_path).parent / base_dir
    eepas_result_path = base_dir / f'Fitted_par_EEPAS_{learn_start}_{learn_end}.csv'

    # Record NLL from each round to determine convergence
    nll_history = []

    # ===== Start iterative optimization =====
    for round_num in range(1, max_adjustment_rounds + 1):
        print(f'\n{"="*80}')
        print(f'Round {round_num} Optimization')
        print(f'{"="*80}')
        print(f'Using configuration: {current_config_path}')
        print(f'{"="*80}')

        # Reload current config (might be newly adjusted)
        with open(current_config_path, 'r') as f:
            config = json.load(f)

        # Execute EEPAS optimization (call eepas_learning)
        try:
            eepas_learning(current_config_path, m0=m0,
                         multi_start=multi_start, n_starts=n_starts,
                         single_stage=single_stage,
                         use_basinhopping=use_basinhopping,
                         basinhopping_niter=basinhopping_niter,
                         optimizer=optimizer,
                         ppe_ref_mag=ppe_ref_mag,
                         use_fast_mode=use_fast_mode,
                         magnitude_samples=magnitude_samples,
                         lead_time_days=lead_time_days)
        except Exception as e:
            print(f'❌ Optimization failed: {e}')
            return None

        # Check if result file was generated
        if not eepas_result_path.exists():
            print(f'❌ Result file not found: {eepas_result_path}')
            return None

        # Parse optimization results (CSV file)
        result_params = parse_result_csv(str(eepas_result_path))
        if result_params is None:
            print('❌ Failed to parse result file')
            return None

        final_nll = result_params.get('ln_likelihood', None)
        print(f'\n✅ This round optimization complete')
        print(f'   Final NLL = {final_nll:.6f}')

        # ===== Check NLL convergence =====
        nll_history.append(final_nll)

        # If we have results from two or more rounds, check if NLL improvement is below threshold
        if len(nll_history) > 1:
            nll_improvement = abs(nll_history[-2] - nll_history[-1])
            print(f'   NLL improvement: {nll_improvement:.6f}')

            # NLL convergence criterion: two consecutive rounds with improvement < 0.1
            if nll_improvement < nll_convergence_threshold:
                print(f'\n{"="*80}')
                print(f'✅ NLL has converged! Improvement ({nll_improvement:.6f}) < threshold ({nll_convergence_threshold})')
                print(f'   Round {len(nll_history)-1}: NLL = {nll_history[-2]:.6f}')
                print(f'   Round {len(nll_history)}: NLL = {nll_history[-1]:.6f}')
                print(f'   Stopping further adjustments.')
                print('='*80)
                return result_params

        # ===== If boundary adjustment is disabled, return result directly =====
        if disable_boundary_adjustment:
            print('\n' + '='*80)
            print('✅ Optimization complete (boundary adjustment disabled)')
            print(f'   Final NLL = {final_nll:.6f}')
            print('='*80)
            return result_params

        # ===== Check boundary hits =====
        # Load boundary settings (Stage3 for three-stage, Stage1 for single-stage)
        if 'stage3' in config['optimization']:
            # Three-stage mode: use stage3 boundaries
            boundary_config = config['optimization']['stage3']
        else:
            # Single-stage mode: use stage1 boundaries
            boundary_config = config['optimization']['stage1']

        param_names = boundary_config['parameters']
        lower_bounds = np.array(boundary_config['lowerBounds'])
        upper_bounds = np.array(boundary_config['upperBounds'])

        # Extract 8 EEPAS parameter values from results
        params_values = []
        for name in param_names:
            if name in result_params:
                params_values.append(result_params[name])
            else:
                print(f'⚠️  Warning: Parameter {name} not found in results')
                params_values.append(0.0)

        params = np.array(params_values)

        # Check if parameters hit boundaries (using configured tolerance)
        print(f'\nChecking if Stage3 parameters hit boundaries...')
        hits = check_boundary_hits(params, lower_bounds, upper_bounds, param_names, tolerance)

        # If no parameters hit boundaries → optimization successfully completed
        if not hits:
            print('\n' + '='*80)
            print('✅ Optimization successfully completed! No parameters hit boundaries')
            print(f'   Final NLL = {final_nll:.6f}')
            print('='*80)
            return result_params

        # Suggest and apply adjustments (using unified adjustment logic, respecting physical constraints)
        print(f'\n💡 Suggesting boundary adjustments (expansion factor = {expansion_factor}x):')
        adjusted = False

        for param_name, bound_type in hits.items():
            idx = param_names.index(param_name)
            current_value = params[idx]

            if bound_type == 'lower':
                old_bound = lower_bounds[idx]
                # Use unified boundary adjustment function (respecting physical constraints)
                new_bound = suggest_boundary_adjustment(
                    param_name, current_value, old_bound, 'lower', expansion_factor
                )
                boundary_config['lowerBounds'][idx] = new_bound
                print(f'   {param_name} lower bound: {old_bound:.6f} → {new_bound:.6f}')
                adjusted = True

            else:  # upper
                old_bound = upper_bounds[idx]
                # Use unified boundary adjustment function (respecting physical constraints)
                new_bound = suggest_boundary_adjustment(
                    param_name, current_value, old_bound, 'upper', expansion_factor
                )
                boundary_config['upperBounds'][idx] = new_bound
                print(f'   {param_name} upper bound: {old_bound:.6f} → {new_bound:.6f}')
                adjusted = True

        if adjusted:
            # Create new configuration file (do not overwrite original)
            import shutil

            # Generate new config file name
            original_path = Path(original_config_path)
            stem = original_path.stem  # filename without extension
            suffix = original_path.suffix  # file extension
            new_config_name = f'{stem}_autoadjusted_round{round_num}{suffix}'
            new_config_path = original_path.parent / new_config_name

            # Save adjusted config to new file
            with open(new_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f'   ✅ Created new config file: {new_config_path}')
            print(f'   📌 Original config file remains unchanged: {original_config_path}')

            # Update current config path (next round will use the new config)
            current_config_path = str(new_config_path)

        if round_num == max_adjustment_rounds:
            print(f'\n{"="*80}')
            print(f'⚠️  Maximum adjustment rounds ({max_adjustment_rounds}) reached, stopping')
            print(f'   Current NLL = {final_nll:.6f}')
            print('   Recommendation: Check if parameters still hit boundaries, may need manual further adjustment')
            print('='*80)
        else:
            print(f'\n🔄 Boundary issue detected, preparing Round {round_num + 1} optimization...')
            import time
            time.sleep(2)  # Give user 2 seconds to view information, but no interaction needed

    return result_params


def main():
    parser = argparse.ArgumentParser(
        description='EEPAS Parameter Learning - Automatic Boundary Adjustment Version'
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Configuration file path (JSON format)'
    )
    parser.add_argument(
        '--m0',
        type=float,
        default=None,
        help='Completeness magnitude (optional, overrides value in config file)'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=3,
        help='Maximum boundary adjustment rounds (default: 3)'
    )
    parser.add_argument(
        '--no-boundary-adjustment',
        action='store_true',
        help='Disable automatic boundary adjustment, use fixed boundaries from config'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=0.01,
        help='Boundary hit tolerance, relative proportion (default: 0.01 = 1%%)'
    )
    parser.add_argument(
        '--expansion',
        type=float,
        default=2.0,
        help='Boundary expansion factor (default: 2.0)'
    )
    parser.add_argument(
        '--nll-threshold',
        type=float,
        default=0.1,
        help='NLL convergence threshold (default: 0.1)'
    )
    parser.add_argument(
        '--single-stage',
        action='store_true',
        help='Use single-stage full parameter optimization (8 parameters jointly)'
    )
    parser.add_argument(
        '--three-stage',
        action='store_true',
        help='Use three-stage optimization (stage 1: am,at,Sa,u → stage 2: Sm,bt,St,ba,u → stage 3: all)'
    )
    parser.add_argument(
        '--no-multistart',
        action='store_true',
        help='Disable multi-start search (default: enabled with 3 starting points)'
    )
    parser.add_argument(
        '--n-starts',
        type=int,
        default=3,
        help='Number of multi-start points (default: 3)'
    )
    parser.add_argument(
        '--basinhopping',
        action='store_true',
        help='Use Basin-Hopping global optimization (escape local optima)'
    )
    parser.add_argument(
        '--basinhopping-niter',
        type=int,
        default=20,
        help='Basin-hopping iteration count (default: 20)'
    )
    parser.add_argument(
        '--optimizer',
        type=str,
        default='fminsearchcon',
        choices=['fminsearchcon', 'L-BFGS-B', 'TNC', 'SLSQP', 'Powell'],
        help='Optimizer selection (default: fminsearchcon)'
    )
    parser.add_argument(
        '--ppe-ref-mag',
        type=str,
        choices=['m0', 'mT'],
        default='mT',
        help='PPE reference magnitude: m0 or mT (default: mT, paper version)'
    )
    parser.add_argument(
        '--accurate',
        action='store_true',
        help='Use accurate mode (quad_vec integration, slower but more precise)'
    )
    parser.add_argument(
        '--magnitude-samples',
        type=int,
        default=50,
        help='Number of sampling points for fast mode (default: 50)'
    )
    parser.add_argument(
        '--lead-time-days',
        type=float,
        default=None,
        help='Fixed lead time L in days for FLEEPAS mode (default: None, read from config)'
    )

    args = parser.parse_args()

    # Check for conflicting arguments
    if args.single_stage and args.three_stage:
        print('❌ Error: Cannot specify both --single-stage and --three-stage')
        sys.exit(1)

    # Determine optimization mode
    # Priority:
    # 1. If config has customStages enabled → use custom stages
    # 2. If --single-stage or --three-stage specified → use explicit mode
    # 3. Auto-detect from stage1 configuration:
    #    - If stage1 has all 8 parameters → single-stage
    #    - Otherwise → three-stage

    from utils.data_loader import DataLoader
    custom_config = DataLoader.load_custom_stages(args.config)

    if custom_config is not None:
        # Custom stages enabled in config
        optimization_mode = 'custom'
        single_stage_flag = False  # Not used for custom stages
        print(f'🎯 Optimization mode: Custom Stages ({len(custom_config["stages"])} stages)', flush=True)
    elif args.single_stage:
        # User explicitly requested single-stage
        optimization_mode = 'single'
        single_stage_flag = True
        print('🎯 Optimization mode: Single-Stage (8 parameters jointly)', flush=True)
    elif args.three_stage:
        # User explicitly requested three-stage
        optimization_mode = 'three'
        single_stage_flag = False
        print('🎯 Optimization mode: Three-Stage (am,at,Sa,u → Sm,bt,St,ba,u → all)', flush=True)
    else:
        # Auto-detect from stage1 configuration
        stage1_config_type = DataLoader.detect_stage1_config_type(args.config)

        if stage1_config_type == 'single':
            optimization_mode = 'single'
            single_stage_flag = True
            print('🎯 Optimization mode: Single-Stage (auto-detected from stage1 config)', flush=True)
            print('   stage1 contains all 8 parameters → using single-stage optimization', flush=True)
        else:
            optimization_mode = 'three'
            single_stage_flag = False
            print('🎯 Optimization mode: Three-Stage (auto-detected from stage1 config)', flush=True)
            print('   stage1 contains partial parameters → using three-stage optimization', flush=True)

    # Determine which mode to use
    use_fast_mode = not args.accurate
    if args.accurate:
        print('⚠️  Using accurate mode (quad_vec), slower but higher precision', flush=True)
    else:
        print(f'✅ Using fast mode (magnitude_samples={args.magnitude_samples})', flush=True)

    print(f'Using PPE reference magnitude: {args.ppe_ref_mag}', flush=True)

    result = eepas_with_auto_boundary(
        config_path=args.config,
        m0=args.m0,
        max_adjustment_rounds=1 if args.no_boundary_adjustment else args.max_rounds,
        disable_boundary_adjustment=args.no_boundary_adjustment,
        tolerance=args.tolerance,
        expansion_factor=args.expansion,
        nll_convergence_threshold=args.nll_threshold,
        single_stage=single_stage_flag,
        multi_start=not args.no_multistart,  # Default enable multistart, unless --no-multistart specified
        n_starts=args.n_starts,
        use_basinhopping=args.basinhopping,
        basinhopping_niter=args.basinhopping_niter,
        optimizer=args.optimizer,
        ppe_ref_mag=args.ppe_ref_mag,
        use_fast_mode=use_fast_mode,
        magnitude_samples=args.magnitude_samples,
        lead_time_days=args.lead_time_days
    )

    if result is not None:
        print('\nFinal Results Summary:')
        for key, value in result.items():
            if key != 'ln_likelihood':
                print(f'  {key} = {value:.6f}')
        print(f'  NLL = {result["ln_likelihood"]:.6f}')

        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()