#!/usr/bin/env python3
"""
Custom Optimization Stages Test Script

Tests three different optimization modes:
1. Custom 2-stage optimization (Magnitude-First strategy)
2. Custom 4-stage optimization (M-T-S-Joint strategy)
3. Standard three-stage optimization (backward compatibility)

Usage:
    python3 test_custom_stages.py [--mode MODE] [--skip-ppe]

Options:
    --mode MODE       Test mode: '2stage', '4stage', 'threestage', or 'all' (default: all)
    --skip-ppe        Skip PPE learning (use existing PPE parameters)
    --max-rounds N    Maximum boundary adjustment rounds (default: 1)
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run shell command and handle errors"""
    print(f'\n{"="*80}')
    print(f'🚀 {description}')
    print(f'{"="*80}')
    print(f'Command: {" ".join(cmd)}')
    print(f'{"="*80}\n')

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f'\n❌ {description} failed with exit code {result.returncode}')
        sys.exit(1)

    print(f'\n✅ {description} completed successfully\n')
    return result.returncode

def test_2stage(skip_ppe=False, max_rounds=1):
    """Test 2-stage custom optimization"""
    config = 'config_test_custom_2stage.json'

    # Step 1: PPE Learning
    if not skip_ppe:
        run_command(
            ['python3', 'ppe_learning.py', '--config', config],
            'Test 1.1: PPE Learning (2-stage)'
        )

    # Step 2: EEPAS Learning with custom 2-stage
    run_command(
        ['python3', 'eepas_learning_auto_boundary.py',
         '--config', config,
         '--optimizer', 'SLSQP',
         '--max-rounds', str(max_rounds)],
        'Test 1.2: EEPAS Learning (Custom 2-Stage)'
    )

    print('\n' + '='*80)
    print('✅ 2-Stage Custom Optimization Test PASSED')
    print('='*80)

def test_4stage(skip_ppe=False, max_rounds=1):
    """Test 4-stage custom optimization"""
    config = 'config_test_custom_4stage.json'

    # Step 1: PPE Learning
    if not skip_ppe:
        run_command(
            ['python3', 'ppe_learning.py', '--config', config],
            'Test 2.1: PPE Learning (4-stage)'
        )

    # Step 2: EEPAS Learning with custom 4-stage
    run_command(
        ['python3', 'eepas_learning_auto_boundary.py',
         '--config', config,
         '--optimizer', 'SLSQP',
         '--max-rounds', str(max_rounds)],
        'Test 2.2: EEPAS Learning (Custom 4-Stage)'
    )

    print('\n' + '='*80)
    print('✅ 4-Stage Custom Optimization Test PASSED')
    print('='*80)

def test_threestage(skip_ppe=False, max_rounds=1):
    """Test standard three-stage optimization (backward compatibility)"""
    config = 'config_test_standard_threestage.json'

    # Step 1: PPE Learning
    if not skip_ppe:
        run_command(
            ['python3', 'ppe_learning.py', '--config', config],
            'Test 3.1: PPE Learning (standard three-stage)'
        )

    # Step 2: EEPAS Learning with standard three-stage
    run_command(
        ['python3', 'eepas_learning_auto_boundary.py',
         '--config', config,
         '--three-stage',
         '--optimizer', 'SLSQP',
         '--max-rounds', str(max_rounds)],
        'Test 3.2: EEPAS Learning (Standard Three-Stage)'
    )

    print('\n' + '='*80)
    print('✅ Standard Three-Stage Test PASSED (Backward Compatibility OK)')
    print('='*80)

def main():
    parser = argparse.ArgumentParser(description='Test custom optimization stages')
    parser.add_argument('--mode', choices=['2stage', '4stage', 'threestage', 'all'],
                       default='all', help='Test mode (default: all)')
    parser.add_argument('--skip-ppe', action='store_true',
                       help='Skip PPE learning (use existing parameters)')
    parser.add_argument('--max-rounds', type=int, default=1,
                       help='Maximum boundary adjustment rounds (default: 1)')

    args = parser.parse_args()

    print('\n' + '='*80)
    print('EEPAS Custom Optimization Stages Test Suite')
    print('='*80)
    print(f'Test mode: {args.mode}')
    print(f'Skip PPE: {args.skip_ppe}')
    print(f'Max boundary adjustment rounds: {args.max_rounds}')
    print('='*80)

    # Run tests based on mode
    if args.mode in ['2stage', 'all']:
        test_2stage(skip_ppe=args.skip_ppe, max_rounds=args.max_rounds)

    if args.mode in ['4stage', 'all']:
        test_4stage(skip_ppe=args.skip_ppe, max_rounds=args.max_rounds)

    if args.mode in ['threestage', 'all']:
        test_threestage(skip_ppe=args.skip_ppe, max_rounds=args.max_rounds)

    # Final summary
    print('\n' + '='*80)
    print('🎉 ALL TESTS PASSED!')
    print('='*80)
    print('\nTest Results Summary:')

    if args.mode in ['2stage', 'all']:
        result_file = 'results_test_custom_2stage/Fitted_par_EEPAS_1990_2012.csv'
        if Path(result_file).exists():
            print(f'✅ 2-stage results: {result_file}')
        else:
            print(f'⚠️  2-stage results not found: {result_file}')

    if args.mode in ['4stage', 'all']:
        result_file = 'results_test_custom_4stage/Fitted_par_EEPAS_1990_2012.csv'
        if Path(result_file).exists():
            print(f'✅ 4-stage results: {result_file}')
        else:
            print(f'⚠️  4-stage results not found: {result_file}')

    if args.mode in ['threestage', 'all']:
        result_file = 'results_test_standard_threestage/Fitted_par_EEPAS_1990_2012.csv'
        if Path(result_file).exists():
            print(f'✅ Three-stage results: {result_file}')
        else:
            print(f'⚠️  Three-stage results not found: {result_file}')

    print('\n' + '='*80)
    print('Test suite completed successfully!')
    print('='*80)

if __name__ == '__main__':
    main()
