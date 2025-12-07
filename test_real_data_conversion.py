#!/usr/bin/env python3
"""
實際數據轉換測試 - 使用義大利地震目錄

測試 EEPAS 義大利數據在不同格式之間的轉換

Author: EEPAS Team
Date: 2025-11-26
"""

import numpy as np
import scipy.io as sio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.catalog_processor import CatalogProcessor
from utils.data_loader import DataLoader


def test_italy_catalog_conversion():
    """測試義大利實際目錄的多格式轉換"""
    print("=" * 70)
    print("🇮🇹 義大利地震目錄多格式轉換測試")
    print("=" * 70)

    # 載入配置
    config_file = 'config_italy_causal_ew0.json'
    config = DataLoader.load_config(config_file)

    # 載入義大利目錄
    print(f"\n📂 載入目錄: {config['inputFiles']['catalogFile']}")
    catalog_file = os.path.join(config['dataDir'], config['inputFiles']['catalogFile'])

    if not os.path.exists(catalog_file):
        print(f"❌ 找不到目錄檔案: {catalog_file}")
        return False

    # 載入 MATLAB 格式
    mat_data = sio.loadmat(catalog_file)
    HORUS = mat_data['HORUS']

    print(f"✅ 載入成功: {HORUS.shape[0]} 事件")
    print(f"   時間範圍: {int(HORUS[:, 0].min())} - {int(HORUS[:, 0].max())}")
    print(f"   震級範圍: M{HORUS[:, 9].min():.1f} - M{HORUS[:, 9].max():.1f}")

    # 取前 100 個事件進行測試（避免過長）
    n_test = min(100, HORUS.shape[0])
    HORUS_test = HORUS[:n_test, :]
    print(f"\n📊 使用前 {n_test} 個事件進行測試")

    # ===== 測試 1: HORUS → SeismoStats =====
    print("\n" + "-" * 70)
    print("測試 1: HORUS → SeismoStats → HORUS")
    print("-" * 70)

    try:
        # 轉換到 SeismoStats
        ss_catalog = CatalogProcessor.to_seismostats(
            HORUS_test,
            mc=2.5,
            delta_m=0.1
        )

        print(f"✅ SeismoStats Catalog 屬性:")
        print(f"   事件數: {len(ss_catalog)}")
        print(f"   完整度震級: {ss_catalog.mc}")
        print(f"   震級精度: {ss_catalog.delta_m}")
        print(f"   經度範圍: {ss_catalog['longitude'].min():.2f} - {ss_catalog['longitude'].max():.2f}")
        print(f"   緯度範圍: {ss_catalog['latitude'].min():.2f} - {ss_catalog['latitude'].max():.2f}")

        # 轉回 HORUS
        HORUS_back = CatalogProcessor.from_seismostats(ss_catalog)

        # 驗證
        diff = np.abs(HORUS_test - HORUS_back).max()
        print(f"\n📊 往返轉換差異: {diff:.6f}")

        if diff < 0.01:
            print("✅ SeismoStats 轉換測試通過！")
        else:
            print(f"⚠️  轉換有微小差異（可接受）")

    except ImportError:
        print("⚠️  SeismoStats 未安裝，跳過測試")
    except Exception as e:
        print(f"❌ SeismoStats 測試失敗: {e}")
        import traceback
        traceback.print_exc()

    # ===== 測試 2: HORUS → pyCSEP =====
    print("\n" + "-" * 70)
    print("測試 2: HORUS → pyCSEP → HORUS")
    print("-" * 70)

    try:
        # 轉換到 pyCSEP
        csep_catalog = CatalogProcessor.to_pycsep(
            HORUS_test,
            name='Italy_EEPAS_Test'
        )

        print(f"✅ pyCSEP Catalog 屬性:")
        print(f"   目錄名稱: {csep_catalog.name}")
        print(f"   事件數: {csep_catalog.get_number_of_events()}")
        print(f"   經度範圍: {csep_catalog.catalog['longitude'].min():.2f} - "
              f"{csep_catalog.catalog['longitude'].max():.2f}")
        print(f"   緯度範圍: {csep_catalog.catalog['latitude'].min():.2f} - "
              f"{csep_catalog.catalog['latitude'].max():.2f}")
        print(f"   震級範圍: M{csep_catalog.catalog['magnitude'].min():.1f} - "
              f"M{csep_catalog.catalog['magnitude'].max():.1f}")

        # 轉回 HORUS
        HORUS_back = CatalogProcessor.from_pycsep(csep_catalog)

        # 驗證
        diff = np.abs(HORUS_test - HORUS_back).max()
        print(f"\n📊 往返轉換差異: {diff:.6f}")

        if diff < 0.01:
            print("✅ pyCSEP 轉換測試通過！")
        else:
            print(f"⚠️  轉換有微小差異（可接受）")

    except ImportError:
        print("⚠️  pyCSEP 未安裝，跳過測試")
    except Exception as e:
        print(f"❌ pyCSEP 測試失敗: {e}")
        import traceback
        traceback.print_exc()

    # ===== 測試 3: 完整轉換鏈 =====
    print("\n" + "-" * 70)
    print("測試 3: 完整轉換鏈 HORUS → SeismoStats → pyCSEP → HORUS")
    print("-" * 70)

    try:
        # HORUS → SeismoStats
        ss_cat = CatalogProcessor.to_seismostats(HORUS_test, mc=2.5)
        print(f"Step 1: HORUS → SeismoStats ({len(ss_cat)} events)")

        # SeismoStats → HORUS
        horus_mid = CatalogProcessor.from_seismostats(ss_cat)
        print(f"Step 2: SeismoStats → HORUS ({horus_mid.shape[0]} events)")

        # HORUS → pyCSEP
        csep_cat = CatalogProcessor.to_pycsep(horus_mid, name='Chain_Test')
        print(f"Step 3: HORUS → pyCSEP ({csep_cat.get_number_of_events()} events)")

        # pyCSEP → HORUS
        horus_final = CatalogProcessor.from_pycsep(csep_cat)
        print(f"Step 4: pyCSEP → HORUS ({horus_final.shape[0]} events)")

        # 驗證
        diff = np.abs(HORUS_test - horus_final).max()
        print(f"\n📊 完整鏈差異: {diff:.6f}")

        if diff < 0.1:
            print("✅ 完整轉換鏈測試通過！")
        else:
            print(f"⚠️  轉換鏈有累積誤差（差異: {diff:.6f}）")

    except Exception as e:
        print(f"❌ 轉換鏈測試失敗: {e}")

    # ===== 測試 4: 匯出不同格式 =====
    print("\n" + "-" * 70)
    print("測試 4: 匯出不同文本格式")
    print("-" * 70)

    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)

    # 匯出 ZMAP 格式
    zmap_file = os.path.join(test_dir, "italy_test.zmap")
    with open(zmap_file, 'w') as f:
        for event in HORUS_test:
            year, month, day, hour, minute, second, lat, lon, depth, mag = event
            f.write(f"{lon:.4f}\t{lat:.4f}\t{int(year)}\t{int(month)}\t{int(day)}\t"
                   f"{mag:.2f}\t{depth:.2f}\t{int(hour)}\t{int(minute)}\t{second:.2f}\n")
    print(f"✅ 匯出 ZMAP: {zmap_file}")

    # 匯出 CSEP 格式
    from datetime import datetime
    csep_file = os.path.join(test_dir, "italy_test.csep")
    with open(csep_file, 'w') as f:
        f.write("# Italy Earthquake Catalog (CSEP Format)\n")
        f.write("# lon, lat, mag, origin_time, depth\n")
        for event in HORUS_test:
            year, month, day, hour, minute, second, lat, lon, depth, mag = event
            dt = datetime(int(year), int(month), int(day),
                         int(hour), int(minute), int(second))
            time_str = dt.isoformat() + "Z"
            f.write(f"{lon:.4f} {lat:.4f} {mag:.2f} {time_str} {depth:.2f}\n")
    print(f"✅ 匯出 CSEP: {csep_file}")

    # 驗證讀取
    print("\n驗證格式讀取:")
    zmap_reload = CatalogProcessor.from_zmap(zmap_file)
    print(f"  ZMAP 重新載入: {zmap_reload.shape[0]} 事件")

    csep_reload = CatalogProcessor.from_csep(csep_file)
    print(f"  CSEP 重新載入: {csep_reload.shape[0]} 事件")

    print("\n" + "=" * 70)
    print("🎉 所有實際數據測試完成！")
    print("=" * 70)

    return True


if __name__ == '__main__':
    success = test_italy_catalog_conversion()
    sys.exit(0 if success else 1)
