#!/usr/bin/env python3
"""
自動邊界調整結果分析工具

== 用途 ==
分析eepas_learning_auto_boundary.py的執行日誌，
提供邊界調整過程的可視化總結。

== 分析內容 ==
1. 輪次統計：共執行幾輪優化
2. NLL追蹤：每輪的負對數概似值
3. 邊界調整記錄：哪些參數觸碰邊界，如何調整
4. 收斂判定：是否達到預期水平

== 使用方式 ==
python analyze_auto_boundary_result.py <log_file>

範例：
python analyze_auto_boundary_result.py test_auto_boundary.log

作者：Claude Code
日期：2025-01
"""

import re
import sys

def parse_log(log_file):
    """
    解析自動邊界調整的日誌文件

    從 eepas_learning_auto_boundary.py 的輸出日誌中提取：
    - 輪次編號
    - 每輪的最終 NLL 值
    - 邊界調整記錄（哪個參數、上界/下界、調整前後值）

    返回:
        輪次列表，每個元素包含 {round, nll, adjustments}
    """
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # ===== 定義正則表達式模式 =====
    rounds = []
    round_pattern = r'第\s*(\d+)\s*輪優化'  # 匹配 "第 1 輪優化"
    nll_pattern = r'最終 NLL = ([-\d.]+)'   # 匹配 "最終 NLL = -292.123"
    bound_pattern = r'(\w+) (下界|上界): ([\d.e+-]+) → ([\d.e+-]+)'  # 匹配 "St 下界: 0.001 → 0.0005"

    # ===== 逐輪次解析 =====
    for match in re.finditer(round_pattern, content):
        round_num = int(match.group(1))
        start_pos = match.start()

        # 確定當前輪次內容的範圍（直到下一輪或文件結束）
        next_match = re.search(round_pattern, content[start_pos+10:])
        end_pos = start_pos + next_match.start() + 10 if next_match else len(content)

        round_content = content[start_pos:end_pos]

        # 提取 NLL 值
        nll_match = re.search(nll_pattern, round_content)
        nll = float(nll_match.group(1)) if nll_match else None

        # 提取邊界調整記錄
        adjustments = []
        for adj_match in re.finditer(bound_pattern, round_content):
            adjustments.append({
                'param': adj_match.group(1),    # 參數名（如St）
                'type': adj_match.group(2),      # 上界或下界
                'old': float(adj_match.group(3)), # 調整前的值
                'new': float(adj_match.group(4))  # 調整後的值
            })

        rounds.append({
            'round': round_num,
            'nll': nll,
            'adjustments': adjustments
        })

    return rounds

def analyze_results(log_file):
    """
    分析自動邊界調整的執行結果

    輸出內容：
    1. 逐輪顯示 NLL 和邊界調整情況
    2. 與 MATLAB 版本比較（目標 NLL ≈ -292）
    3. 邊界調整統計（總次數、各參數調整次數）
    """
    print('='*80)
    print('自動邊界調整測試結果分析')
    print('='*80)

    # ===== 解析日誌 =====
    try:
        rounds = parse_log(log_file)
    except Exception as e:
        print(f'❌ 無法解析日誌: {e}')
        return

    if not rounds:
        print('⚠️  未找到完整的輪次信息')
        return

    print(f'\n共完成 {len(rounds)} 輪優化\n')

    # ===== 逐輪顯示結果 =====
    for r in rounds:
        print(f'第{r["round"]}輪:')
        if r['nll']:
            print(f'  最終 NLL: {r["nll"]:.6f}')

        if r['adjustments']:
            print(f'  邊界調整:')
            for adj in r['adjustments']:
                print(f'    {adj["param"]} {adj["type"]}: {adj["old"]:.6e} → {adj["new"]:.6e}')
        else:
            print(f'  ✅ 無邊界問題（所有參數遠離邊界）')
        print()

    # ===== 與 MATLAB 版本比較 =====
    # MATLAB 原始版本在 decluster 配置下的 NLL ≈ -292.246
    if rounds:
        final_nll = rounds[-1]['nll']
        matlab_nll = -292.246  # MATLAB 基準值
        if final_nll and final_nll < -292:
            diff = abs(final_nll - matlab_nll)
            print(f'✅ 成功達到 MATLAB 水平！')
            print(f'   MATLAB: {matlab_nll:.6f}')
            print(f'   Python: {final_nll:.6f}')
            print(f'   差異:   {diff:.6f} ({diff/abs(matlab_nll)*100:.4f}%)')
        elif final_nll:
            print(f'⚠️  NLL={final_nll:.6f}，未達到 -292 的目標')
            print(f'   建議：檢查是否需要更多調整輪次或手動調整邊界')

    # ===== 邊界調整統計 =====
    total_adj = sum(len(r['adjustments']) for r in rounds)
    print(f'\n邊界調整統計:')
    print(f'  總調整次數: {total_adj}')

    # 按參數統計調整次數
    param_adj = {}
    for r in rounds:
        for adj in r['adjustments']:
            key = f"{adj['param']} {adj['type']}"
            param_adj[key] = param_adj.get(key, 0) + 1

    if param_adj:
        print(f'  各參數調整次數:')
        for key, count in sorted(param_adj.items()):
            print(f'    {key}: {count}次')
    else:
        print(f'  ✅ 初始邊界設定合理，無需調整')

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'test_auto_full_v2.log'
    analyze_results(log_file)
