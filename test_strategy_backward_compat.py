#!/usr/bin/env python3
"""
測試優化策略系統的向後相容性

驗證：
1. 舊格式配置能正確載入
2. 舊格式能正確轉換為新格式
3. 新格式配置能正確載入
4. 預定義策略能正確載入
5. 自訂策略能正確載入
"""

import json
from utils.optimization_strategies import (
    load_optimization_config,
    validate_stage_config,
    print_strategy_info,
    list_available_strategies
)

def test_old_format():
    """測試舊格式配置載入"""
    print("=" * 80)
    print("測試 1: 舊格式配置（向後相容）")
    print("=" * 80)

    # 載入舊格式配置
    with open('config_italy_causal_ew0.json', 'r') as f:
        old_config = json.load(f)

    # 載入並轉換
    opt_config = load_optimization_config(old_config)

    print(f"✓ 成功載入舊格式配置")
    print(f"✓ 轉換後階段數: {len(opt_config['stages'])}")
    print(f"✓ 描述: {opt_config.get('description', 'N/A')}")

    # 驗證每個階段
    for i, stage in enumerate(opt_config['stages'], 1):
        print(f"\n  階段 {i}: {stage.get('name', 'unknown')}")
        print(f"    優化參數: {stage['optimize']}")
        print(f"    固定參數: {list(stage.get('fix', {}).keys())}")

        # 驗證配置
        try:
            validate_stage_config(stage)
            print(f"    ✓ 配置驗證通過")
        except ValueError as e:
            print(f"    ✗ 配置驗證失敗: {e}")
            return False

    print("\n✅ 測試 1 通過\n")
    return True


def test_predefined_strategies():
    """測試預定義策略"""
    print("=" * 80)
    print("測試 2: 預定義策略")
    print("=" * 80)

    strategies = ['biondini2023', 'magnitude_first', 'conservative', 'single_stage']

    for strategy_name in strategies:
        print(f"\n測試策略: {strategy_name}")

        # 創建測試配置
        test_config = {
            'optimization': {
                'strategy': strategy_name
            }
        }

        # 載入策略
        opt_config = load_optimization_config(test_config)

        print(f"  ✓ 成功載入 {strategy_name}")
        print(f"  ✓ 階段數: {len(opt_config['stages'])}")
        print(f"  ✓ 描述: {opt_config.get('description', 'N/A')}")

        # 驗證每個階段
        for stage in opt_config['stages']:
            try:
                validate_stage_config(stage)
            except ValueError as e:
                print(f"  ✗ 階段 {stage.get('name')} 驗證失敗: {e}")
                return False

        print(f"  ✓ 所有階段驗證通過")

    print("\n✅ 測試 2 通過\n")
    return True


def test_new_format_configs():
    """測試新格式配置檔案"""
    print("=" * 80)
    print("測試 3: 新格式配置檔案")
    print("=" * 80)

    config_files = [
        'config_italy_biondini2023.json',
        'config_italy_magnitude_first.json',
        'config_italy_custom_strategy.json'
    ]

    for config_file in config_files:
        print(f"\n測試配置: {config_file}")

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            opt_config = load_optimization_config(config)

            print(f"  ✓ 成功載入")
            print(f"  ✓ 階段數: {len(opt_config['stages'])}")
            print(f"  ✓ 描述: {opt_config.get('description', 'N/A')}")

            # 驗證階段
            for stage in opt_config['stages']:
                validate_stage_config(stage)

            print(f"  ✓ 所有階段驗證通過")

        except FileNotFoundError:
            print(f"  ⚠️  配置檔案不存在，跳過")
        except Exception as e:
            print(f"  ✗ 測試失敗: {e}")
            return False

    print("\n✅ 測試 3 通過\n")
    return True


def test_stage_inheritance():
    """測試階段繼承邏輯"""
    print("=" * 80)
    print("測試 4: 階段繼承邏輯")
    print("=" * 80)

    # 測試配置：確保繼承邏輯正確
    test_config = {
        'optimization': {
            'strategy': 'custom',
            'custom': {
                'stages': [
                    {
                        'name': 'stage1',
                        'optimize': ['am', 'at'],
                        'fix': {'bm': 1.0, 'Sm': 0.3},
                        'bounds': {'am': [1.0, 2.0], 'at': [1.0, 3.0]}
                    },
                    {
                        'name': 'stage2',
                        'optimize': ['Sm', 'u'],
                        'fix': {'bm': 1.0},
                        'inherit': ['am', 'at'],
                        'bounds': {'Sm': [0.2, 0.6], 'u': [0.0, 1.0]}
                    },
                    {
                        'name': 'stage3',
                        'optimize': ['am', 'Sm', 'at', 'u'],
                        'fix': {'bm': 1.0},
                        'inherit': 'all',
                        'bounds': {
                            'am': [1.0, 2.0],
                            'Sm': [0.2, 0.6],
                            'at': [1.0, 3.0],
                            'u': [0.0, 1.0]
                        }
                    }
                ]
            }
        }
    }

    opt_config = load_optimization_config(test_config)

    print("✓ 載入自訂策略")

    # 驗證階段配置
    for i, stage in enumerate(opt_config['stages'], 1):
        print(f"\n  階段 {i}: {stage['name']}")
        print(f"    優化: {stage['optimize']}")
        print(f"    固定: {list(stage.get('fix', {}).keys())}")
        print(f"    繼承: {stage.get('inherit', '無')}")

        try:
            validate_stage_config(stage)
            print(f"    ✓ 驗證通過")
        except ValueError as e:
            print(f"    ✗ 驗證失敗: {e}")
            return False

    print("\n✅ 測試 4 通過\n")
    return True


def test_parameter_conflicts():
    """測試參數衝突檢測"""
    print("=" * 80)
    print("測試 5: 參數衝突檢測")
    print("=" * 80)

    # 測試衝突配置：參數同時在 optimize 和 fix 中
    conflict_stage = {
        'name': 'conflict_test',
        'optimize': ['am', 'at', 'u'],
        'fix': {'bm': 1.0, 'am': 1.5},  # am 衝突！
        'bounds': {'am': [1.0, 2.0], 'at': [1.0, 3.0], 'u': [0.0, 1.0]}
    }

    try:
        validate_stage_config(conflict_stage)
        print("✗ 測試失敗：應該檢測到參數衝突")
        return False
    except ValueError as e:
        print(f"✓ 成功檢測到參數衝突: {e}")

    print("\n✅ 測試 5 通過\n")
    return True


def main():
    print("\n" + "=" * 80)
    print("EEPAS 優化策略系統 - 向後相容性測試")
    print("=" * 80 + "\n")

    # 先列出所有可用策略
    print("可用的預定義策略：\n")
    list_available_strategies()

    # 執行測試
    tests = [
        ("舊格式配置", test_old_format),
        ("預定義策略", test_predefined_strategies),
        ("新格式配置", test_new_format_configs),
        ("階段繼承", test_stage_inheritance),
        ("參數衝突", test_parameter_conflicts)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試出錯: {e}")
            results.append((test_name, False))

    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 80)
    print(f"總計: {passed}/{total} 測試通過")
    print("=" * 80 + "\n")

    return passed == total


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
