#!/usr/bin/env python3
"""測試新策略配置的完整性"""

import json
import numpy as np
from utils.optimization_strategies import load_optimization_config

def test_config(config_path):
    """測試配置檔案的完整性"""
    print(f"\n{'='*80}")
    print(f"測試配置: {config_path}")
    print('='*80)

    # 載入配置
    with open(config_path) as f:
        config = json.load(f)

    opt_config = load_optimization_config(config)

    print(f"策略: {opt_config.get('description', 'N/A')}")
    print(f"階段數: {len(opt_config['stages'])}")
    print()

    # 驗證每個階段
    all_ok = True
    for i, stage in enumerate(opt_config['stages'], 1):
        print(f"--- 階段 {i}: {stage['name']} ---")

        optimize_params = stage['optimize']
        fix_params = stage.get('fix', {})
        bounds_dict = stage.get('bounds', {})
        initial_dict = stage.get('initial', {})

        print(f"✓ 優化參數 ({len(optimize_params)}): {optimize_params}")
        print(f"✓ 固定參數 ({len(fix_params)}): {list(fix_params.keys())}")

        # 檢查邊界
        missing_bounds = []
        for p in optimize_params:
            if p not in bounds_dict:
                missing_bounds.append(p)

        if missing_bounds:
            print(f"✗ 缺少邊界的參數: {missing_bounds}")
            all_ok = False
        else:
            print(f"✓ 所有優化參數都有邊界")

        # 檢查初始值（第一階段必須有）
        if i == 1:
            if not initial_dict:
                print(f"✗ 第一階段缺少初始值！")
                all_ok = False
            else:
                missing_initial = []
                for p in optimize_params:
                    if p not in initial_dict:
                        missing_initial.append(p)

                if missing_initial:
                    print(f"✗ 缺少初始值的參數: {missing_initial}")
                    all_ok = False
                else:
                    print(f"✓ 所有優化參數都有初始值")
                    for p in optimize_params:
                        print(f"    {p} = {initial_dict[p]} (邊界: {bounds_dict.get(p, 'N/A')})")

        # 顯示固定值
        if fix_params:
            print(f"  固定值:")
            for k, v in fix_params.items():
                print(f"    {k} = {v}")

        print()

    if all_ok:
        print("✅ 配置檢查通過！")
    else:
        print("❌ 配置有問題！")

    return all_ok

if __name__ == '__main__':
    configs = [
        'config_italy_causal_ew0_new.json',
        'config_italy_causal_ew1_new.json',
        'config_italy_causal_ew0_accurate_new.json'
    ]

    all_passed = True
    for cfg in configs:
        try:
            passed = test_config(cfg)
            all_passed = all_passed and passed
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            all_passed = False

    print(f"\n{'='*80}")
    if all_passed:
        print("✅ 所有配置都通過檢查！")
    else:
        print("❌ 有配置檢查失敗！")
    print('='*80)
