"""
Auto Boundary Adjustment Module - Auxiliary Tool for EEPAS Optimization

== Background ==
In constrained optimization, if the true optimal solution lies outside the bounds,
the optimizer can only stop at the boundary.
Example: St's true optimal value is 0.0005, but lower bound is set to 0.001,
then optimizer can only reach 0.001.

== Solution ==
This module provides two core functions:
1. check_boundary_hits(): Detect if parameters hit boundaries
2. suggest_boundary_adjustment(): Suggest new boundary values

== Physical Constraints Priority ==
When relaxing boundaries, strictly adhere to EEPAS model's physical constraints:
  - u ∈ [0,1]: Must be a ratio, cannot exceed 1
  - bm,bt,ba,Sm,St,Sa > 0: Must be positive, minimum lower bound 1e-6
  - am,at: Can be negative, no special restrictions

== Decision Logic ==
- Relative tolerance: parameter distance to boundary < 1% (regular parameters)
- Absolute tolerance: distance < 0.1*bound (small-value parameters like St,Sa)
- Stop suggestion: When lower bound ≤ 1e-5, no further relaxation (numerical limit reached)

Author: EEPAS Team
Date: 2025-01
"""

import numpy as np
from typing import Dict, Tuple, List
import json


def check_boundary_hits(
    params: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    param_names: List[str],
    tolerance: float = 0.01
) -> Dict[str, str]:
    """
    Check which parameters hit boundaries

    Args:
        params: Optimized parameter values
        lower_bounds: Lower bounds
        upper_bounds: Upper bounds
        param_names: Parameter name list
        tolerance: Relative tolerance for hit detection (default 1%)

    Returns:
        dict: Dictionary {param_name: 'lower'/'upper'}, recording boundary-hitting parameters

    Note:
        When parameter values are too close to boundaries, it may indicate
        that the true optimal solution lies outside the bounds.
        This function identifies these parameters for subsequent boundary adjustment.
    """
    # Must-be-positive parameters (physical constraints)
    # Sm,St,Sa: Variance parameters, must be >0 for statistical meaning
    # bm,bt,ba: Slope parameters, must be >0 to match seismological observation of magnitude correlation
    positive_params = ['Sm', 'St', 'Sa', 'bm', 'bt', 'ba']

    hits = {}

    for i, (p, lb, ub, name) in enumerate(zip(params, lower_bounds, upper_bounds, param_names)):
        # ===== Physical limit check =====
        # If positive parameter's lower bound is already <=1e-5, consider it loose enough, no further relaxation
        # Reason: 1e-5 is a reasonable numerical precision limit, further relaxation may cause instability
        if name in positive_params and lb <= 1e-5:
            continue

        # If u's upper bound is already >=1.0, no further relaxation
        # Reason: u represents failure-to-predict rate, must be ∈ [0,1], this is a physical constraint
        if name == 'u' and ub >= 1.0:
            continue

        # ===== Boundary distance calculation =====
        range_size = ub - lb

        # For variance parameters (Sm,St,Sa) when lower bound is small, use absolute tolerance
        # Reason: When boundary range is small (e.g. [0.001, 0.01]), relative tolerance fails
        if name in positive_params and lb < 0.01:
            # Absolute tolerance strategy: distance < max(10% of lower bound, 1e-6) considered as hit
            abs_tolerance = max(lb * 0.1, 1e-6)
            dist_to_lower = abs(p - lb)
            if dist_to_lower < abs_tolerance:
                hits[name] = 'lower'
                print(f'   ⚠️  {name}={p:.6e} close to lower bound {lb:.6e} (abs distance={dist_to_lower:.6e})')
                continue

        # ===== Regular relative tolerance check =====
        # Calculate relative distance from parameter value to boundary (as proportion of boundary range)
        dist_to_lower = abs(p - lb) / range_size if range_size > 0 else abs(p - lb)
        dist_to_upper = abs(p - ub) / range_size if range_size > 0 else abs(p - ub)

        # Decision criterion: distance ratio < tolerance (default 1%) considered as hitting boundary
        if dist_to_lower < tolerance:
            hits[name] = 'lower'
            print(f'   ⚠️  {name}={p:.6f} close to lower bound {lb:.6f} (distance ratio={dist_to_lower:.4f})')
        elif dist_to_upper < tolerance:
            hits[name] = 'upper'
            print(f'   ⚠️  {name}={p:.6f} close to upper bound {ub:.6f} (distance ratio={dist_to_upper:.4f})')

    return hits


def suggest_boundary_adjustment(
    param_name: str,
    current_value: float,
    current_bound: float,
    boundary_type: str,
    expansion_factor: float = 2.0
) -> float:
    """
    Suggest new boundary value

    Seismological physical constraints (from EEPAS model definition):
    - u ∈ [0, 1]: failure-to-predict rate, must be a ratio
    - bm, bt, ba > 0: Slopes of magnitude-time-space relationships, must be positive
      (From seismological observation: larger foreshocks correspond to larger mainshocks, requiring positive slopes)
    - Sm, St, Sa > 0: Standard deviations of time/magnitude/space distributions, must be positive
    - am, at can be negative: Intercept terms, physically can be negative

    Hard caps (based on main_gji.tex and empirical results):
    - am ≤ 4.5: Italy observed 3.5, add safety margin
    - at ≤ 3.0: Paper search range upper bound
    - ba ≤ 6.0: Italy observed 5.6, add safety margin
    - bt ≤ 2.0: Reasonable range based on Taiwan/Italy experiments
    - Sm ≤ 2.0: Prevents unreasonable variance
    - St ≤ 1.0: Prevents unreasonable variance
    - Sa ≤ 2.0: Prevents unreasonable spatial spread
    - u ≤ 0.75: Maximum failure rate

    Args:
        param_name: Parameter name
        current_value: Current parameter value
        current_bound: Current boundary value
        boundary_type: 'lower' or 'upper'
        expansion_factor: Expansion multiplier (default 2x)

    Returns:
        Suggested new boundary value (respecting physical constraints and hard caps)
    """
    # Hard caps based on main_gji.tex (prevents physically unreasonable expansions)
    HARD_CAPS = {
        'am': 4.5,   # Italy: 3.5, California: 1.2, add safety margin
        'at': 3.0,   # Paper search range: 1.0-3.0
        'ba': 6.0,   # Italy: 5.6, add safety margin
        'bt': 2.0,   # Reasonable based on empirical data
        'Sm': 2.0,   # Prevents unreasonable variance
        'St': 1.0,   # Prevents unreasonable variance
        'Sa': 2.0,   # Prevents unreasonable spatial spread
        'u': 0.75,   # Maximum failure rate
    }

    # Classify parameters according to seismological physical meaning
    positive_params = ['Sm', 'St', 'Sa', 'bm', 'bt', 'ba']  # Must be positive
    can_be_negative = ['am', 'at']  # Can be negative (intercept terms)

    if boundary_type == 'lower':
        # ===== Handle lower bound relaxation =====
        if param_name in positive_params:
            # Variance and slope parameters: lower bound minimum to 1e-6 (numerical precision limit)
            new_bound = max(current_bound / expansion_factor, 1e-6)
        elif param_name == 'u':
            # u: failure-to-predict rate lower bound cannot be less than 0 (physical constraint)
            new_bound = max(current_bound / expansion_factor, 0.0)
        elif param_name in can_be_negative:
            # am, at intercept terms: can be relaxed to negative values
            if current_bound > 0:
                # Current lower bound is positive, normally reduce
                new_bound = current_bound / expansion_factor
            elif current_bound == 0:
                # Current lower bound is 0, relax towards negative direction based on current value
                new_bound = -abs(current_value) * expansion_factor
            else:
                # Current lower bound is already negative, continue expanding negative range
                new_bound = current_bound * expansion_factor
        else:
            # Unknown parameter, conservative handling (don't allow negative)
            new_bound = max(current_bound / expansion_factor, 0.0)
    else:  # upper
        # ===== Handle upper bound relaxation =====
        if param_name == 'u':
            # u's upper bound cannot exceed 1 (physical constraint: must be a ratio)
            new_bound = min(current_bound * expansion_factor, 1.0)
        elif current_bound > 0:
            # Regular case: expand upper bound
            new_bound = current_bound * expansion_factor
        else:
            # Negative upper bound (rare), take value closer to 0
            new_bound = current_bound / expansion_factor

        # ===== Apply hard cap for upper bounds =====
        if param_name in HARD_CAPS:
            hard_cap = HARD_CAPS[param_name]
            if new_bound > hard_cap:
                print(f'      🛑 Hard cap applied: {param_name} upper bound limited to {hard_cap} (suggested {new_bound:.2f})')
                new_bound = hard_cap

    return new_bound


def auto_adjust_boundaries(
    config_path: str,
    stage: str,
    final_params: Dict[str, float],
    max_iterations: int = 3,
    tolerance: float = 0.01,
    expansion_factor: float = 2.0
) -> Tuple[bool, Dict]:
    """
    Auto-adjust boundaries in configuration file

    Workflow:
        1. Read current configuration and optimization results
        2. Check which parameters hit boundaries (may have limited optimal solution)
        3. Suggest new boundary values (respecting physical constraints)
        4. Update boundary settings in configuration file

    Args:
        config_path: Configuration file path
        stage: 'stage2' (aftershock params) or 'stage3' (EEPAS params)
        final_params: Final optimization parameter dictionary {param_name: value}
        max_iterations: Maximum adjustment iterations (unused, reserved for future extension)
        tolerance: Boundary hit tolerance (default 1%)
        expansion_factor: Boundary expansion multiplier (default 2x)

    Returns:
        (whether re-optimization is needed, updated config dictionary)
    """
    # ===== Load configuration =====
    with open(config_path, 'r') as f:
        config = json.load(f)

    stage_config = config['optimization'][stage]
    param_names = stage_config['parameters']
    lower_bounds = np.array(stage_config['lowerBounds'])
    upper_bounds = np.array(stage_config['upperBounds'])

    # ===== Extract optimization results =====
    # Arrange parameter values in the order defined in config file
    params = np.array([final_params[name] for name in param_names])

    # ===== Check boundary hits =====
    print(f'\n🔍 Checking if {stage} parameters hit boundaries...')
    hits = check_boundary_hits(params, lower_bounds, upper_bounds, param_names, tolerance)

    if not hits:
        print('   ✅ All parameters within bounds, no adjustment needed')
        return False, config

    # ===== Suggest boundary adjustments =====
    print(f'\n💡 Suggesting boundary adjustments (expansion factor = {expansion_factor}x):')
    adjustments = {}

    for param_name, bound_type in hits.items():
        idx = param_names.index(param_name)
        current_value = params[idx]

        if bound_type == 'lower':
            # Lower bound hit: need to relax lower bound (reduce lower bound value)
            current_bound = lower_bounds[idx]
            new_bound = suggest_boundary_adjustment(
                param_name, current_value, current_bound, 'lower', expansion_factor
            )
            adjustments[f'{param_name}_lower'] = new_bound
            print(f'   {param_name} lower bound: {current_bound:.6f} → {new_bound:.6f}')
        else:  # upper
            # Upper bound hit: need to relax upper bound (increase upper bound value)
            current_bound = upper_bounds[idx]
            new_bound = suggest_boundary_adjustment(
                param_name, current_value, current_bound, 'upper', expansion_factor
            )
            adjustments[f'{param_name}_upper'] = new_bound
            print(f'   {param_name} upper bound: {current_bound:.6f} → {new_bound:.6f}')

    # ===== Update configuration file =====
    # Write suggested new boundaries back to config dictionary
    for param_name, bound_type in hits.items():
        idx = param_names.index(param_name)
        if bound_type == 'lower':
            stage_config['lowerBounds'][idx] = adjustments[f'{param_name}_lower']
        else:
            stage_config['upperBounds'][idx] = adjustments[f'{param_name}_upper']

    return True, config


def save_adjusted_config(config: Dict, original_path: str, backup: bool = True):
    """
    Save adjusted configuration file

    Safety mechanism:
        - By default, backup original configuration as .bak file
        - Avoid accidentally overwriting manually adjusted configurations

    Args:
        config: Adjusted configuration dictionary
        original_path: Original configuration file path
        backup: Whether to backup original file (default True)
    """
    if backup:
        import shutil
        backup_path = original_path + '.bak'
        shutil.copy(original_path, backup_path)
        print(f'   💾 Original config backed up to: {backup_path}')

    # Write updated configuration back to JSON file
    with open(original_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'   ✅ Configuration file updated: {original_path}')


def monitor_and_adjust_optimization(
    config_path: str,
    optimize_func,
    max_adjustment_rounds: int = 3,
    tolerance: float = 0.01,
    expansion_factor: float = 2.0
):
    """
    Monitor optimization process and auto-adjust boundaries (high-level wrapper function)

    Workflow:
        1. Execute one complete optimization round (PPE → aftershock → EEPAS)
        2. Check if any parameters hit boundaries
        3. If yes, automatically relax boundaries and re-optimize
        4. Repeat until no boundary issues or maximum rounds reached

    Use case:
        This function is the core logic of eepas_learning_auto_boundary.py,
        providing fully automated boundary adjustment and re-optimization workflow.

    Args:
        config_path: Configuration file path
        optimize_func: Optimization function (accepts config_path, returns result dictionary)
            Return dictionary must contain 'stage3_params' and 'final_nll' keys
        max_adjustment_rounds: Maximum boundary adjustment rounds (default 3)
        tolerance: Boundary hit tolerance (default 1%)
        expansion_factor: Boundary expansion multiplier (default 2x)

    Returns:
        Final optimization result dictionary
    """
    print('='*80)
    print('🤖 Auto Boundary Adjustment Optimization')
    print('='*80)

    for round_num in range(1, max_adjustment_rounds + 1):
        print(f'\n📍 Optimization Round {round_num}')
        print('-'*80)

        # ===== Execute complete 3-stage optimization =====
        result = optimize_func(config_path)

        # ===== Check and adjust boundaries =====
        need_adjust = False

        # Check Stage3 (EEPAS parameters) - most important
        if 'stage3_params' in result:
            need_adjust_s3, new_config = auto_adjust_boundaries(
                config_path, 'stage3', result['stage3_params'],
                max_adjustment_rounds, tolerance, expansion_factor
            )

            if need_adjust_s3:
                need_adjust = True
                save_adjusted_config(new_config, config_path)

        # ===== Determine if further adjustment is needed =====
        if not need_adjust:
            # All parameters within bounds, optimization successfully completed
            print(f'\n✅ Optimization completed! No further boundary adjustment needed')
            print(f'   Final NLL = {result.get("final_nll", "N/A")}')
            break

        if round_num == max_adjustment_rounds:
            # Maximum rounds reached, stop adjustment
            print(f'\n⚠️  Maximum adjustment rounds ({max_adjustment_rounds}) reached, stopping')
            print(f'   Current NLL = {result.get("final_nll", "N/A")}')
            print('   Suggestion: Check if parameters still hit boundaries, may need manual adjustment')
        else:
            # Still have room for adjustment, prepare next optimization round
            print(f'\n🔄 Boundary issues detected, preparing Round {round_num + 1} optimization...')

    return result


def auto_adjust_custom_stages_boundaries(
    config_path: str,
    final_params: Dict[str, float],
    tolerance: float = 0.01,
    expansion_factor: float = 2.0
) -> Tuple[bool, Dict, str]:
    """
    Auto-adjust boundaries in Custom Stages format configuration file

    Differences from auto_adjust_boundaries:
    - Handles stages array format instead of stage1/stage2/stage3
    - Checks all parameter boundaries in all stages
    - Creates new adjusted config file (preserves original file)

    Args:
        config_path: Configuration file path
        final_params: Final optimization parameter dictionary {param_name: value}
        tolerance: Boundary hit tolerance (default 1%)
        expansion_factor: Boundary expansion multiplier (default 2x)

    Returns:
        (whether re-optimization is needed, updated config dictionary, new config file path)
    """
    import os
    import re

    # ===== Load configuration =====
    with open(config_path, 'r') as f:
        config = json.load(f)

    if 'stages' not in config['optimization']:
        raise ValueError(f'Config file {config_path} does not contain stages format!')

    stages = config['optimization']['stages']

    # ===== Check boundary hits in all stages =====
    print(f'\n🔍 Checking if Custom Stages parameters hit boundaries...')

    needs_adjustment = False
    boundary_touched_info = []

    for stage_idx, stage_config in enumerate(stages, start=1):
        stage_name = stage_config.get('name', f'Stage {stage_idx}')
        param_names = stage_config['parameters']
        lower_bounds = np.array(stage_config['lowerBounds'])
        upper_bounds = np.array(stage_config['upperBounds'])

        # Extract parameter values optimized in current stage
        params = np.array([final_params[name] for name in param_names])

        # Check boundary hits
        hits = check_boundary_hits(params, lower_bounds, upper_bounds, param_names, tolerance)

        if hits:
            needs_adjustment = True
            print(f'\n   ⚠️  {stage_name} boundary hits detected:')

            # Suggest boundary adjustments
            for param_name, bound_type in hits.items():
                idx = param_names.index(param_name)
                current_value = params[idx]

                if bound_type == 'lower':
                    current_bound = lower_bounds[idx]
                    new_bound = suggest_boundary_adjustment(
                        param_name, current_value, current_bound, 'lower', expansion_factor
                    )
                    # Update configuration
                    stage_config['lowerBounds'][idx] = new_bound
                    print(f'      {param_name} lower bound: {current_bound:.6f} → {new_bound:.6f}')
                    boundary_touched_info.append(f'{stage_name}:{param_name}_lower')
                else:  # upper
                    current_bound = upper_bounds[idx]
                    new_bound = suggest_boundary_adjustment(
                        param_name, current_value, current_bound, 'upper', expansion_factor
                    )
                    # Update configuration
                    stage_config['upperBounds'][idx] = new_bound
                    print(f'      {param_name} upper bound: {current_bound:.6f} → {new_bound:.6f}')
                    boundary_touched_info.append(f'{stage_name}:{param_name}_upper')

    if not needs_adjustment:
        print('   ✅ All parameters within bounds, no adjustment needed')
        return False, config, config_path

    # ===== Create new adjusted config file =====
    # Parse original filename, generate new filename
    config_dir = os.path.dirname(config_path)
    config_basename = os.path.basename(config_path)
    config_name, config_ext = os.path.splitext(config_basename)

    # If already contains _autoadjusted_roundN, extract round number and increment
    round_match = re.search(r'_autoadjusted_round(\d+)$', config_name)
    if round_match:
        current_round = int(round_match.group(1))
        next_round = current_round + 1
        new_config_name = re.sub(r'_autoadjusted_round\d+$', f'_autoadjusted_round{next_round}', config_name)
    else:
        # First adjustment
        new_config_name = f'{config_name}_autoadjusted_round1'

    new_config_path = os.path.join(config_dir, f'{new_config_name}{config_ext}')

    # Save new config file
    with open(new_config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'\n✅ Created new config file: {new_config_path}')
    print(f'   📌 Original config file preserved: {config_path}')
    print(f'   🔄 Recommend re-running optimization with new config file')

    return True, config, new_config_path


if __name__ == '__main__':
    # Example usage
    print(__doc__)

    # Test boundary checking
    params = np.array([0.545, 0.886, 0.008, 1.922, 0.448])
    lower = np.array([0.001, 0.05, 0.001, 0.05, 0.0])
    upper = np.array([2.0, 2.0, 2.0, 3.0, 0.75])
    names = ['Sm', 'bt', 'St', 'ba', 'u']

    print('\nExample: Check boundary hits')
    hits = check_boundary_hits(params, lower, upper, names, tolerance=0.02)

    if hits:
        print('\nExample: Suggest boundary adjustments')
        for name, bound_type in hits.items():
            idx = names.index(name)
            if bound_type == 'lower':
                new = suggest_boundary_adjustment(name, params[idx], lower[idx], 'lower')
                print(f'{name} lower bound: {lower[idx]} → {new}')
            else:
                new = suggest_boundary_adjustment(name, params[idx], upper[idx], 'upper')
                print(f'{name} upper bound: {upper[idx]} → {new}')
