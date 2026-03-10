#!/usr/bin/env python3
"""
Automatic boundary adjustment result analysis tool.

== Purpose ==
Analyze execution logs from eepas_learning_auto_boundary.py,
providing a visual summary of the boundary adjustment process.

== Analysis Contents ==
1. Round statistics: total number of optimization rounds executed
2. NLL tracking: negative log-likelihood value for each round
3. Boundary adjustment records: which parameters hit boundaries and how they were adjusted
4. Convergence assessment: whether the expected level was reached

== Usage ==
python analyze_auto_boundary_result.py <log_file>

Example:
python analyze_auto_boundary_result.py test_auto_boundary.log
"""

import re
import sys

def parse_log(log_file):
    """
    Parse the automatic boundary adjustment log file.

    Extracts from the eepas_learning_auto_boundary.py output log:
    - Round number
    - Final NLL value for each round
    - Boundary adjustment records (parameter name, upper/lower bound, before/after values)

    Returns:
        List of rounds, each containing {round, nll, adjustments}.
    """
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # ===== Define regex patterns =====
    rounds = []
    round_pattern = r'第\s*(\d+)\s*輪優化'  # Matches "第 1 輪優化"
    nll_pattern = r'最終 NLL = ([-\d.]+)'   # Matches "最終 NLL = -292.123"
    bound_pattern = r'(\w+) (下界|上界): ([\d.e+-]+) → ([\d.e+-]+)'  # Matches "St 下界: 0.001 → 0.0005"

    # ===== Parse round by round =====
    for match in re.finditer(round_pattern, content):
        round_num = int(match.group(1))
        start_pos = match.start()

        # Determine the content range for the current round (until next round or end of file)
        next_match = re.search(round_pattern, content[start_pos+10:])
        end_pos = start_pos + next_match.start() + 10 if next_match else len(content)

        round_content = content[start_pos:end_pos]

        # Extract NLL value
        nll_match = re.search(nll_pattern, round_content)
        nll = float(nll_match.group(1)) if nll_match else None

        # Extract boundary adjustment records
        adjustments = []
        for adj_match in re.finditer(bound_pattern, round_content):
            adjustments.append({
                'param': adj_match.group(1),    # Parameter name (e.g., St)
                'type': adj_match.group(2),      # Upper or lower bound
                'old': float(adj_match.group(3)), # Value before adjustment
                'new': float(adj_match.group(4))  # Value after adjustment
            })

        rounds.append({
            'round': round_num,
            'nll': nll,
            'adjustments': adjustments
        })

    return rounds

def analyze_results(log_file):
    """
    Analyze the automatic boundary adjustment execution results.

    Output:
    1. Per-round display of NLL and boundary adjustment details
    2. Comparison with MATLAB version (target NLL ~ -292)
    3. Boundary adjustment statistics (total count, per-parameter count)
    """
    print('='*80)
    print('Automatic Boundary Adjustment Test Result Analysis')
    print('='*80)

    # ===== Parse log =====
    try:
        rounds = parse_log(log_file)
    except Exception as e:
        print(f'Failed to parse log: {e}')
        return

    if not rounds:
        print('Warning: No complete round information found')
        return

    print(f'\nCompleted {len(rounds)} optimization rounds\n')

    # ===== Display results per round =====
    for r in rounds:
        print(f'Round {r["round"]}:')
        if r['nll']:
            print(f'  Final NLL: {r["nll"]:.6f}')

        if r['adjustments']:
            print(f'  Boundary adjustments:')
            for adj in r['adjustments']:
                print(f'    {adj["param"]} {adj["type"]}: {adj["old"]:.6e} -> {adj["new"]:.6e}')
        else:
            print(f'  No boundary issues (all parameters far from boundaries)')
        print()

    # ===== Compare with MATLAB version =====
    # Original MATLAB version NLL under decluster configuration ~ -292.246
    if rounds:
        final_nll = rounds[-1]['nll']
        matlab_nll = -292.246  # MATLAB baseline value
        if final_nll and final_nll < -292:
            diff = abs(final_nll - matlab_nll)
            print(f'Successfully reached MATLAB level!')
            print(f'   MATLAB: {matlab_nll:.6f}')
            print(f'   Python: {final_nll:.6f}')
            print(f'   Diff:   {diff:.6f} ({diff/abs(matlab_nll)*100:.4f}%)')
        elif final_nll:
            print(f'Warning: NLL={final_nll:.6f}, did not reach target of -292')
            print(f'   Suggestion: Check if more adjustment rounds or manual boundary tuning is needed')

    # ===== Boundary adjustment statistics =====
    total_adj = sum(len(r['adjustments']) for r in rounds)
    print(f'\nBoundary adjustment statistics:')
    print(f'  Total adjustments: {total_adj}')

    # Count adjustments per parameter
    param_adj = {}
    for r in rounds:
        for adj in r['adjustments']:
            key = f"{adj['param']} {adj['type']}"
            param_adj[key] = param_adj.get(key, 0) + 1

    if param_adj:
        print(f'  Adjustments per parameter:')
        for key, count in sorted(param_adj.items()):
            print(f'    {key}: {count} times')
    else:
        print(f'  Initial boundary settings are reasonable, no adjustments needed')

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'test_auto_full_v2.log'
    analyze_results(log_file)
