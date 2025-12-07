# EEPAS 地震目錄多格式支援使用指南

**版本**: v1.3.0
**日期**: 2025-11-26
**作者**: EEPAS Team

## 📚 概述

EEPAS 現已支援多種地震目錄格式的讀取和轉換，包括：

### 支援的格式

1. **文本格式** (File-based)
   - ✅ **HORUS** - EEPAS 內部標準格式
   - ✅ **ZMAP** - ObsPy 標準格式
   - ✅ **CSEP** - PyCSEP ASCII 格式
   - ✅ **QuakeML** - 需要 ObsPy

2. **Python 物件格式** (Object-based)
   - ✅ **seismostats.Catalog** - SeismoStats 套件
   - ✅ **pycsep.CSEPCatalog** - PyCSEP 套件
   - ✅ **pandas.DataFrame** - 通用數據框架

---

## 🚀 快速開始

### 安裝可選依賴套件

```bash
# SeismoStats (地震統計分析)
pip install seismostats

# PyCSEP (地震預測測試)
pip install pycsep

# ObsPy (QuakeML 支援)
pip install obspy
```

### 基本使用

```python
from utils.catalog_processor import CatalogProcessor

# 自動偵測格式並載入
catalog = CatalogProcessor.load_catalog('earthquakes.zmap')

# 明確指定格式
catalog = CatalogProcessor.load_catalog('data.txt', format='horus')
```

---

## 📖 格式詳細說明

### 1. HORUS 格式

**EEPAS 內部標準格式**

#### 欄位定義（10 欄）

```
[year, month, day, hour, minute, second, latitude, longitude, depth, magnitude]
```

#### 範例數據

```
2020  1  15  10  30  25.5  42.8  13.2  15.0  5.2
2020  3  22  14  45  10.2  43.1  13.5  10.0  4.8
2020  5  10   8  15  35.8  42.5  13.0  20.0  5.5
```

#### 使用方式

```python
# 從 MATLAB .mat 檔案載入 (標準方式)
import scipy.io as sio
mat_data = sio.loadmat('HORUS_Italy.mat')
catalog = mat_data['HORUS']

# 從文本檔案載入
catalog = CatalogProcessor.from_horus_text('catalog.txt')

# 儲存為文本
import numpy as np
np.savetxt('output.txt', catalog, fmt='%.6f')
```

---

### 2. ZMAP 格式

**ObsPy 標準格式**

#### 欄位定義（10 欄）

```
[lon, lat, year, month, day, mag, depth, hour, minute, second]
```

#### 範例數據

```
13.2000	42.8000	2020	1	15	5.20	15.00	10	30	25.50
13.5000	43.1000	2020	3	22	4.80	10.00	14	45	10.20
13.0000	42.5000	2020	5	10	5.50	20.00	8	15	35.80
```

#### 使用方式

```python
# 讀取 ZMAP 格式
catalog = CatalogProcessor.from_zmap('catalog.zmap')

# 轉換 HORUS → ZMAP (手動匯出)
with open('output.zmap', 'w') as f:
    for event in horus_catalog:
        year, month, day, hour, minute, second, lat, lon, depth, mag = event
        f.write(f"{lon:.4f}\t{lat:.4f}\t{int(year)}\t{int(month)}\t{int(day)}\t"
               f"{mag:.2f}\t{depth:.2f}\t{int(hour)}\t{int(minute)}\t{second:.2f}\n")
```

---

### 3. CSEP 格式

**PyCSEP ASCII 標準格式**

#### 格式說明

```
lon lat mag origin_time depth
```

其中 `origin_time` 為 ISO 8601 格式：`YYYY-MM-DDTHH:MM:SS.fffZ`

#### 範例數據

```
# CSEP Catalog Format
# lon, lat, mag, origin_time, depth
13.2000 42.8000 5.20 2020-01-15T10:30:25Z 15.00
13.5000 43.1000 4.80 2020-03-22T14:45:10Z 10.00
13.0000 42.5000 5.50 2020-05-10T08:15:35Z 20.00
```

#### 使用方式

```python
# 讀取 CSEP 格式
catalog = CatalogProcessor.from_csep('catalog.csep')

# 轉換 HORUS → CSEP (手動匯出)
from datetime import datetime
with open('output.csep', 'w') as f:
    f.write("# lon, lat, mag, origin_time, depth\n")
    for event in horus_catalog:
        year, month, day, hour, minute, second, lat, lon, depth, mag = event
        dt = datetime(int(year), int(month), int(day),
                     int(hour), int(minute), int(second))
        time_str = dt.isoformat() + "Z"
        f.write(f"{lon:.4f} {lat:.4f} {mag:.2f} {time_str} {depth:.2f}\n")
```

---

### 4. QuakeML 格式

**國際標準 XML 格式**

需要安裝 ObsPy：`pip install obspy`

#### 使用方式

```python
# 讀取 QuakeML
catalog = CatalogProcessor.from_quakeml('earthquakes.xml')

# 轉換 QuakeML → HORUS
from obspy import read_events
events = read_events('earthquakes.xml')
catalog = CatalogProcessor.from_quakeml('earthquakes.xml')
```

---

## 🔄 雙向轉換

### seismostats Catalog

**SeismoStats 套件整合**

#### HORUS → seismostats

```python
# 轉換到 seismostats Catalog
ss_catalog = CatalogProcessor.to_seismostats(
    horus_catalog,
    mc=2.5,          # 完整度震級
    delta_m=0.1,     # 震級精度
    b_value=1.0,     # Gutenberg-Richter b 值（可選）
    a_value=5.0      # Gutenberg-Richter a 值（可選）
)

# seismostats.Catalog 繼承自 pandas.DataFrame
print(f"事件數: {len(ss_catalog)}")
print(f"完整度震級: {ss_catalog.mc}")
print(ss_catalog.head())

# 使用 seismostats 的分析功能
from seismostats.analysis import estimate_b
b_value, std_b = ss_catalog.estimate_b(mc=2.5, delta_m=0.1)
print(f"估計的 b 值: {b_value:.3f} ± {std_b:.3f}")
```

#### seismostats → HORUS

```python
# 從 seismostats Catalog 轉回 HORUS
horus_catalog = CatalogProcessor.from_seismostats(ss_catalog)

# 驗證數據保真度
diff = np.abs(original_horus - horus_catalog).max()
print(f"往返轉換差異: {diff:.6f}")
```

---

### pyCSEP CSEPCatalog

**PyCSEP 套件整合**

#### HORUS → pyCSEP

```python
# 轉換到 pyCSEP CSEPCatalog
csep_catalog = CatalogProcessor.to_pycsep(
    horus_catalog,
    name='Italy_2020_M5+',  # 目錄名稱
    region=None              # 可選：空間區域定義
)

# 使用 pyCSEP 功能
print(f"目錄名稱: {csep_catalog.name}")
print(f"事件數: {csep_catalog.get_number_of_events()}")

# 篩選事件
filtered = csep_catalog.filter(f'magnitude >= 5.0')
print(f"M≥5.0 事件: {filtered.get_number_of_events()}")
```

#### pyCSEP → HORUS

```python
# 從 pyCSEP CSEPCatalog 轉回 HORUS
horus_catalog = CatalogProcessor.from_pycsep(csep_catalog)
```

---

### pandas DataFrame

**通用數據框架整合**

#### HORUS → DataFrame

```python
import pandas as pd

# 手動建立 DataFrame
df = pd.DataFrame(horus_catalog, columns=[
    'year', 'month', 'day', 'hour', 'minute', 'second',
    'latitude', 'longitude', 'depth', 'magnitude'
])

# 建立時間欄位
df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
```

#### DataFrame → HORUS

```python
# 從 DataFrame 轉換
catalog = CatalogProcessor.from_dataframe(
    df,
    column_mapping={'lon': 'longitude', 'lat': 'latitude'}  # 可選：欄位映射
)
```

---

## 🔗 完整轉換鏈範例

### 範例 1: HORUS → seismostats → pyCSEP → HORUS

```python
from utils.catalog_processor import CatalogProcessor
import numpy as np

# 載入原始 HORUS 目錄
import scipy.io as sio
mat_data = sio.loadmat('data/HORUS_Italy.mat')
original = mat_data['HORUS']

print(f"原始目錄: {original.shape[0]} 事件")

# Step 1: HORUS → seismostats
ss_catalog = CatalogProcessor.to_seismostats(original, mc=2.5, delta_m=0.1)
print(f"seismostats Catalog: {len(ss_catalog)} 事件")

# Step 2: seismostats → HORUS
horus_mid = CatalogProcessor.from_seismostats(ss_catalog)
print(f"中間 HORUS: {horus_mid.shape[0]} 事件")

# Step 3: HORUS → pyCSEP
csep_catalog = CatalogProcessor.to_pycsep(horus_mid, name='Italy_Chain')
print(f"pyCSEP Catalog: {csep_catalog.get_number_of_events()} 事件")

# Step 4: pyCSEP → HORUS
horus_final = CatalogProcessor.from_pycsep(csep_catalog)
print(f"最終 HORUS: {horus_final.shape[0]} 事件")

# 驗證數據保真度
diff = np.abs(original - horus_final).max()
print(f"\n完整鏈差異: {diff:.6f}")
if diff < 0.01:
    print("✅ 轉換鏈測試通過！數據保真度良好")
```

### 範例 2: 多格式匯出

```python
# 載入 EEPAS 目錄
original = load_eepas_catalog()

# 匯出為不同格式
# 1. ZMAP 格式
export_to_zmap(original, 'italy_catalog.zmap')

# 2. CSEP 格式
export_to_csep(original, 'italy_catalog.csep')

# 3. seismostats Catalog (可用於進一步分析)
ss_catalog = CatalogProcessor.to_seismostats(original, mc=2.5)
ss_catalog.to_csv('italy_catalog.csv')  # seismostats 支援 CSV 匯出

# 4. pyCSEP Catalog (可用於預測測試)
csep_catalog = CatalogProcessor.to_pycsep(original, name='Italy_EEPAS')
```

---

## 🧪 測試與驗證

### 執行完整測試

```bash
# 測試所有格式轉換
python3 test_multiformat_conversion.py

# 測試實際數據轉換
python3 test_real_data_conversion.py
```

### 預期結果

```
======================================================================
📊 測試總結
======================================================================

總測試項目: 5
通過項目: 5
成功率: 100.0%

詳細結果:
  basic_formats       : ✅ 通過
  seismostats         : ✅ 通過
  pycsep              : ✅ 通過
  conversion_chain    : ✅ 通過
  auto_detection      : ✅ 通過

🎉 所有測試全部通過！
```

---

## 📊 格式比較表

| 格式 | 用途 | 優點 | 缺點 | 推薦場景 |
|------|------|------|------|----------|
| **HORUS** | EEPAS 內部 | 簡單、高效 | 需轉換才能用於其他工具 | EEPAS 主要流程 |
| **ZMAP** | ObsPy 通用 | 廣泛支援 | 欄位順序不直觀 | 與 ObsPy 整合 |
| **CSEP** | PyCSEP 標準 | 可讀性強、標準時間格式 | 檔案較大 | 預測測試、交換 |
| **QuakeML** | 國際標準 | 包含完整元數據 | XML 冗長 | 國際數據交換 |
| **seismostats** | 統計分析 | 內建統計功能 | 需額外套件 | b 值估計、統計分析 |
| **pyCSEP** | 預測測試 | 完整測試框架 | 需額外套件 | 地震預測評估 |

---

## 🔧 進階使用

### 自動格式偵測

```python
# CatalogProcessor 會自動偵測檔案格式
catalog = CatalogProcessor.load_catalog('unknown_format.txt', format='auto')

# 手動偵測
detected_format = CatalogProcessor.detect_format('mystery_file.dat')
print(f"偵測到的格式: {detected_format}")
```

### 自訂欄位映射

```python
# 從 DataFrame 載入，自訂欄位名稱
import pandas as pd
df = pd.read_csv('custom_catalog.csv')

catalog = CatalogProcessor.from_dataframe(
    df,
    column_mapping={
        'lon': 'longitude',
        'lat': 'latitude',
        'mag': 'magnitude',
        'datetime': 'time'
    }
)
```

### 批次轉換

```python
import glob

# 批次轉換所有 ZMAP 檔案
for zmap_file in glob.glob('data/*.zmap'):
    catalog = CatalogProcessor.from_zmap(zmap_file)

    # 轉換為 CSEP
    output_file = zmap_file.replace('.zmap', '.csep')
    export_to_csep(catalog, output_file)

    print(f"✅ 轉換完成: {zmap_file} → {output_file}")
```

---

## 📚 參考文獻

### 相關套件文件

- **SeismoStats**: https://seismostats.readthedocs.io/
- **PyCSEP**: https://docs.cseptesting.org/
- **ObsPy**: https://docs.obspy.org/

### EEPAS 相關文件

- `CLAUDE.md` - 開發注意事項
- `USAGE.md` - EEPAS 使用指南
- `README.md` - 專案總覽

---

## ❓ 常見問題

### Q1: 轉換過程會損失精度嗎？

往返轉換的最大誤差通常 < 0.001，主要來自：
- 時間精度（秒數的浮點數處理）
- Unix timestamp 轉換（pyCSEP）

對於地震學應用，這些誤差完全可以忽略。

### Q2: 需要安裝所有可選套件嗎？

**不需要**。只安裝你需要的功能：
- 只用 EEPAS：不需要額外套件
- 需要統計分析：安裝 `seismostats`
- 需要預測測試：安裝 `pycsep`
- 需要 QuakeML：安裝 `obspy`

### Q3: 如何處理大型目錄檔案？

```python
# 分批處理
chunk_size = 10000
for i in range(0, len(large_catalog), chunk_size):
    chunk = large_catalog[i:i+chunk_size]
    process_chunk(chunk)
```

### Q4: 支援其他格式嗎？

目前支援的格式已涵蓋主流需求。如需新格式，請：
1. 在 `catalog_processor_extensions.py` 中新增轉換函數
2. 在 `CatalogProcessor` 中新增對應方法
3. 更新測試腳本

---

**維護者**: EEPAS Development Team
**最後更新**: 2025-11-26
**版本**: v1.3.0
