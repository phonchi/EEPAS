#!/usr/bin/env python3
"""
EEPAS Forecast Converter 測試腳本

測試 forecast_converter.py 的所有功能

Author: EEPAS Team
Date: 2025-11-26
"""

import sys
import os
import numpy as np
from datetime import datetime

# 確保能導入模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.forecast_converter import EEPASForecastConverter, convert_eepas_forecast


def test_basic_conversion():
    """測試 1: 基本轉換功能"""
    print("=" * 70)
    print("測試 1: 基本轉換功能")
    print("=" * 70)

    # 使用義大利數據
    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file):
        print(f"⚠️  找不到預測檔案: {forecast_file}")
        print("   請確認檔案路徑正確")
        return False

    if not os.path.exists(grid_file):
        print(f"⚠️  找不到網格檔案: {grid_file}")
        print("   請確認檔案路徑正確")
        return False

    try:
        # 建立轉換器
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            num_regions=177,
            num_magnitude_steps=25,
            verbose=True
        )

        print(f"\n✅ 轉換器初始化成功！")
        print(f"   偵測到 {converter.num_periods} 個時間週期")
        print(f"   網格數量: {len(converter.cell_bounds)}")
        print(f"   震級範圍: M{converter.magnitude_min} - M{converter.magnitude_bins[-1][1]}")

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_period():
    """測試 2: 單一週期轉換"""
    print("\n" + "=" * 70)
    print("測試 2: 單一週期轉換")
    print("=" * 70)

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            verbose=True
        )

        # 轉換第 1 個週期
        output_file = 'test_output/forecast_period_1.dat'
        os.makedirs('test_output', exist_ok=True)

        period_data = converter.convert_period(
            period=1,
            output_file=output_file,
            perform_downsampling=True
        )

        print(f"\n✅ 單一週期轉換成功！")
        print(f"   輸出檔案: {output_file}")
        print(f"   網格點數: {len(period_data)}")
        print(f"   總預測率: {period_data['RATE'].sum():.6f}")

        # 驗證檔案內容
        print(f"\n   前 5 行數據預覽:")
        print(period_data.head())

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_periods():
    """測試 3: 所有週期累加轉換"""
    print("\n" + "=" * 70)
    print("測試 3: 所有週期累加轉換")
    print("=" * 70)

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            verbose=True
        )

        # 轉換所有週期
        output_file = 'test_output/forecast_all_periods.dat'
        os.makedirs('test_output', exist_ok=True)

        all_data = converter.convert_all_periods(
            output_file=output_file,
            perform_downsampling=True
        )

        print(f"\n✅ 所有週期轉換成功！")
        print(f"   輸出檔案: {output_file}")
        print(f"   網格點數: {len(all_data)}")
        print(f"   總預測率: {all_data['RATE'].sum():.6f}")

        # 驗證數據統計
        print(f"\n   數據統計:")
        print(f"   經度範圍: {all_data['LON_0'].min():.2f} - {all_data['LON_1'].max():.2f}")
        print(f"   緯度範圍: {all_data['LAT_0'].min():.2f} - {all_data['LAT_1'].max():.2f}")
        print(f"   震級範圍: M{all_data['MAG_0'].min():.1f} - M{all_data['MAG_1'].max():.1f}")

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ppe_conversion():
    """測試 4: PPE 預測轉換"""
    print("\n" + "=" * 70)
    print("測試 4: PPE 預測轉換")
    print("=" * 70)

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_PPE_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            verbose=True
        )

        # 轉換所有週期
        output_file = 'test_output/forecast_ppe_all_periods.dat'

        ppe_data = converter.convert_all_periods(
            output_file=output_file,
            perform_downsampling=True
        )

        print(f"\n✅ PPE 轉換成功！")
        print(f"   網格點數: {len(ppe_data)}")
        print(f"   總預測率: {ppe_data['RATE'].sum():.6f}")

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_period_dates():
    """測試 5: 時間週期計算"""
    print("\n" + "=" * 70)
    print("測試 5: 時間週期計算")
    print("=" * 70)

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            verbose=False
        )

        print("\n   3個月週期:")
        for period in [1, 2, 3, 4]:
            start, end = converter.calculate_period_dates(period, 2012, 3)
            print(f"   週期 {period}: {start.strftime('%Y-%m-%d')} - {end.strftime('%Y-%m-%d')}")

        print("\n   1年週期:")
        for period in [1, 2, 3]:
            start, end = converter.calculate_period_dates(period, 2012, 12)
            print(f"   週期 {period}: {start.strftime('%Y-%m-%d')} - {end.strftime('%Y-%m-%d')}")

        print(f"\n✅ 時間週期計算正確！")
        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pycsep_integration():
    """測試 6: PyCSEP 整合"""
    print("\n" + "=" * 70)
    print("測試 6: PyCSEP 整合")
    print("=" * 70)

    try:
        import csep
        from csep.utils import time_utils
    except ImportError:
        print("⚠️  pycsep 未安裝，跳過測試")
        print("   安裝指令: pip install pycsep")
        return False

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        converter = EEPASForecastConverter(
            forecast_file=forecast_file,
            grid_file=grid_file,
            verbose=True
        )

        # 轉換第 1 個週期
        period_data = converter.convert_period(period=1, perform_downsampling=True)

        # 計算時間範圍
        start_date, end_date = converter.calculate_period_dates(1, 2012, 3)

        # 轉換為 PyCSEP forecast 物件
        forecast = converter.to_pycsep_forecast(
            data=period_data,
            start_date=start_date,
            end_date=end_date,
            name='EEPAS_2012_Q1'
        )

        print(f"\n✅ PyCSEP 整合成功！")
        print(f"   Forecast 名稱: {forecast.name}")
        print(f"   時間範圍: {forecast.start_time} - {forecast.end_time}")
        print(f"   最小震級: {forecast.min_magnitude}")
        print(f"   預測事件數: {forecast.event_count:.2f}")

        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convenience_function():
    """測試 7: 便利函數"""
    print("\n" + "=" * 70)
    print("測試 7: 便利函數")
    print("=" * 70)

    forecast_file = 'results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat'
    grid_file = 'data/CELLE_ter.mat'

    if not os.path.exists(forecast_file) or not os.path.exists(grid_file):
        print("⚠️  跳過測試（檔案不存在）")
        return False

    try:
        output_file = 'test_output/forecast_convenience.dat'
        os.makedirs('test_output', exist_ok=True)

        # 使用便利函數轉換
        convert_eepas_forecast(
            forecast_file=forecast_file,
            grid_file=grid_file,
            output_file=output_file,
            period=1,
            verbose=False
        )

        # 驗證檔案存在
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"\n✅ 便利函數測試成功！")
            print(f"   輸出檔案: {output_file}")
            print(f"   檔案大小: {file_size:,} bytes")
            return True
        else:
            print(f"\n❌ 輸出檔案未建立")
            return False

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n" + "=" * 70)
    print("🧪 EEPAS Forecast Converter 完整測試")
    print("=" * 70)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 執行測試
    results['基本轉換'] = test_basic_conversion()
    results['單一週期'] = test_single_period()
    results['所有週期'] = test_all_periods()
    results['PPE轉換'] = test_ppe_conversion()
    results['時間計算'] = test_period_dates()
    results['PyCSEP整合'] = test_pycsep_integration()
    results['便利函數'] = test_convenience_function()

    # 總結報告
    print("\n" + "=" * 70)
    print("📊 測試總結")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n總測試項目: {total}")
    print(f"通過項目: {passed}")
    print(f"成功率: {passed/total*100:.1f}%")

    print("\n詳細結果:")
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗/跳過"
        print(f"  {test_name:15s}: {status}")

    if passed == total:
        print("\n🎉 所有測試全部通過！")
        return 0
    else:
        print(f"\n⚠️  部分測試失敗或跳過")
        return 1


if __name__ == '__main__':
    sys.exit(main())
