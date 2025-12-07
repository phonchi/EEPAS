#!/usr/bin/env python3
"""完整流程測試：模擬 optimize_eepas_parameters.py 的執行"""

import json
import numpy as np
from utils.optimization_strategies import load_optimization_config

def test_stage_initialization(config_path):
    """測試每個階段的初始化"""
    print(f"\n{'='*80}")
    print(f"測試配置: {config_path}")
    print('='*80)

    with open(config_path) as f:
        config = json.load(f)

    opt_config = load_optimization_config(config)

    prev_results = None  # 第一階段無繼承

    for stage_idx, stage_config in enumerate(opt_config['stages'], 1):
        stage_name = stage_config.get('name', f'stage{stage_idx}')
        optimize_params = stage_config['optimize']
        fix_params = stage_config.get('fix', {})
        inherit_params = stage_config.get('inherit', [])
        bounds_dict = stage_config.get('bounds', {})

        print(f"\n{'='*80}")
        print(f"階段 {stage_idx}: {stage_name}")
        print('='*80)

        # 模擬 optimize_eepas_parameters.py 的初始值設定邏輯
        x0 = []
        lb_list = []
        ub_list = []

        for pname in optimize_params:
            # 初始值優先順序
            if prev_results and pname in prev_results:
                init_val = prev_results[pname]
                print(f"  {pname}: {init_val:.4f} (繼承自前階段)")
            elif 'initial' in stage_config and pname in stage_config['initial']:
                init_val = stage_config['initial'][pname]
                print(f"  {pname}: {init_val:.4f} (新格式 initial)")
            elif 'initialValues' in stage_config and pname in stage_config.get('parameters', []):
                idx = stage_config['parameters'].index(pname)
                init_val = stage_config['initialValues'][idx]
                print(f"  {pname}: {init_val:.4f} (舊格式 initialValues)")
            else:
                if pname in bounds_dict:
                    init_val = np.mean(bounds_dict[pname])
                    print(f"  {pname}: {init_val:.4f} (邊界中點)")
                else:
                    init_val = 0.5
                    print(f"  {pname}: {init_val:.4f} (預設值)")

            x0.append(init_val)

            # 邊界
            if pname in bounds_dict:
                lb_list.append(bounds_dict[pname][0])
                ub_list.append(bounds_dict[pname][1])
            else:
                lb_list.append(0.0)
                ub_list.append(10.0)
                print(f"  ⚠️  {pname} 缺少邊界")

        x0 = np.array(x0)
        lb_array = np.array(lb_list)
        ub_array = np.array(ub_list)

        print(f"\n固定參數:")
        for k, v in fix_params.items():
            print(f"  {k} = {v}")

        print(f"\n初始值向量: {x0}")
        print(f"下界向量: {lb_array}")
        print(f"上界向量: {ub_array}")

        # 檢查初始值是否在邊界內
        violations = []
        for i, pname in enumerate(optimize_params):
            if x0[i] < lb_array[i] or x0[i] > ub_array[i]:
                violations.append(f"{pname}={x0[i]:.4f} 不在 [{lb_array[i]}, {ub_array[i]}] 範圍內")

        if violations:
            print(f"\n❌ 初始值違反邊界:")
            for v in violations:
                print(f"  {v}")
            return False
        else:
            print(f"\n✅ 所有初始值都在邊界內")

        # 模擬階段結果（用於下一階段繼承）
        # 假設優化後的結果接近初始值（簡化）
        result = dict(fix_params)
        for i, pname in enumerate(optimize_params):
            result[pname] = x0[i] * 1.1  # 模擬優化後的值

        # 繼承邏輯
        if inherit_params:
            if inherit_params == 'all':
                prev_results = result.copy()
            elif isinstance(inherit_params, list):
                if prev_results is None:
                    prev_results = {}
                for key in inherit_params:
                    if key in result:
                        prev_results[key] = result[key]
        else:
            prev_results = result.copy()

    return True

if __name__ == '__main__':
    configs = [
        'config_italy_causal_ew0_new.json',
        'config_italy_causal_ew1_new.json',
        'config_italy_causal_ew0_accurate_new.json'
    ]

    all_passed = True
    for cfg in configs:
        try:
            passed = test_stage_initialization(cfg)
            all_passed = all_passed and passed
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print(f"\n{'='*80}")
    if all_passed:
        print("✅ 所有測試通過！")
    else:
        print("❌ 有測試失敗！")
    print('='*80)
