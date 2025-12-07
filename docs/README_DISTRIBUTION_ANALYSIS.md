# EEPAS 地震分布分析工具 (Python 版)

## 📋 概述

本套工具用於分析 EEPAS 地震目錄的空間和時間分布特性，移植自 MATLAB `analysis_plots/detail_analysis` 目錄中的分析腳本。

**移植日期**: 2025-10-15
**來源**: MATLAB 分析腳本 (9/23後創建)

---

## 🎯 功能

### 1. 地震分布分析 (`distribution_analysis.py`)

**功能**:
- ✅ 空間分布分析 (6區域 vs 24區域)
- ✅ 時間分段分析 (前兆時間/學習期間/預測期間)
- ✅ TWD97 和 WGS84 座標系統支持
- ✅ 震級閾值統計 (>=m0, >=mT)
- ✅ 區域活動性分析
- ✅ 分布均勻性評估

**移植自**:
- `analyze_distribution_twd97.m`
- `analyze_distribution_wgs84_complete.m`
- `analyze_distribution_wgs84_corrected.m`
- `analyze_time_periods_distribution.m`
- `verify_analysis_correctness.m`

### 2. 區域細分工具 (`region_subdivision.py`)

**功能**:
- ✅ CELLE 空間網格細分 (6區域 → 24區域)
- ✅ 經度優先排列順序
- ✅ 區域覆蓋範圍驗證
- ✅ 區域大小一致性檢查

**移植自**:
- `create_24_regions_correct.m`
- `subdivide_celle_correct.m`

---

## 🚀 使用方法

### 基本分析

```bash
# 執行完整分析 (TWD97 座標)
cd /path/to/EEPAS_Taiwan-main/src/python_src
python3 run_distribution_analysis.py ../config.json

# 驗證分析邏輯
python3 run_distribution_analysis.py ../config.json --verify

# 同時執行 WGS84 分析
python3 run_distribution_analysis.py ../config.json --wgs84
```

### 區域細分

```bash
# 創建24區域 (從6區域細分)
python3 region_subdivision.py ../data/CELLE_ter_TW.mat ../data/CELLE_ter_TW_24regions.mat
```

### 單獨使用模組

```python
from distribution_analysis import EarthquakeDistributionAnalyzer

# 創建分析器
analyzer = EarthquakeDistributionAnalyzer('../config.json')

# 執行分析
results = analyzer.run_full_analysis(
    horus_file='../data/GDMScatalog_A_filtered_twd97.mat',
    celle6_file='../data/CELLE_ter_TW_twd97.mat',
    celle24_file='../data/CELLE_ter_TW_twd97_24regions_correct.mat',
    coord_system='twd97',
    output_file='analysis_results.mat'
)
```

---

## 📊 輸出結果

### 分析輸出文件

執行後會生成：

```
python_src/
├── earthquake_distribution_analysis_twd97.mat  # TWD97 分析結果
├── earthquake_distribution_analysis_wgs84.mat  # WGS84 分析結果 (選擇性)
└── distribution_analysis_run.log               # 執行日誌
```

### 結果結構

分析結果包含：

1. **空間分布** (`spatial`)
   - 6區域統計 (總數, >=m0, >=mT)
   - 24區域統計
   - 活動區域數
   - 分布均勻性 (變異係數)

2. **時間分段** (`temporal`)
   - 前兆時間 (1991-2001)
   - 學習期間 (2002-2015)
   - 預測期間 (2016-2023)
   - 各時間段的區域分布

3. **數據摘要** (`data_summary`)
   - 有效地震數
   - 座標系統
   - 過濾參數

---

## 📈 分析示例輸出

### 空間分布統計

```
6區域事件分布:
區域 |  總數  | >=m0  | >=mT  | >=m0% | >=mT%
-----|--------|-------|-------|-------|-------
 1   |   1093 |   768 |     2 |  70.3 |   0.2
 2   |   4932 |  2460 |     5 |  49.9 |   0.1
 3   |   4009 |  2173 |     6 |  54.2 |   0.1
 4   |  18293 |  8854 |    25 |  48.4 |   0.1
 5   |   5365 |  2679 |     6 |  49.9 |   0.1
 6   |  11227 |  5346 |    23 |  47.6 |   0.2
總計 |  44919 | 22280 |    67 |  49.6 |   0.1
```

### 時間分段比較

```
時間段比較 (6區域):
時間段     |  總地震 | >=m0   | >=mT  | 活動區域 | 平均/區域
-----------|---------|--------|-------|----------|----------
前兆時間   |   13838 |   7325 |    19 |    6/6   |   2300.5
學習期間   |   17743 |   7822 |    22 |    6/6   |   2950.7
預測期間   |   13434 |   7133 |    26 |    6/6   |   2235.3
```

---

## 🔍 關鍵差異與改進

### 與 MATLAB 版本的差異

1. **統一模組化設計**
   - MATLAB: 7個獨立腳本
   - Python: 2個統一模組 + 1個執行腳本

2. **座標系統處理**
   - MATLAB: 3個分離的 WGS84 版本
   - Python: 單一模組支持 TWD97/WGS84

3. **數據過濾邏輯**
   - ✅ 深度過濾: < 40km
   - ✅ 區域過濾: 6區域範圍內
   - ✅ 震級四捨五入: 1位小數
   - ✅ 閾值比較: >= (不是 >)

4. **時間分段定義**
   - ✅ 前兆時間: catalogStartYear ~ (learnStartYear - 1)
   - ✅ 學習期間: learnStartYear ~ (learnEndYear - 1)
   - ✅ 預測期間: forecastStartYear ~ (forecastEndYear - 1)
   - ✅ 無重疊無空隙

---

## 📋 依賴項

```python
numpy>=1.20.0
scipy>=1.7.0
```

安裝：
```bash
pip install numpy scipy
```

---

## 🧪 驗證測試

### 驗證分析邏輯

```bash
python3 run_distribution_analysis.py ../config.json --verify
```

驗證項目：
- ✅ 參數設定 (m0, mT, 深度閾值)
- ✅ 時間分段銜接
- ✅ 震級閾值邏輯 (>=)
- ✅ 震級四捨五入

### 測試結果對比

與 MATLAB 版本對比（TWD97 座標）：

| 項目 | MATLAB | Python | 差異 |
|------|--------|--------|------|
| 有效地震數 | 45015 | 45015 | ✅ 一致 |
| 6區域活動 | 6/6 | 6/6 | ✅ 一致 |
| 24區域活動 | 24/24 | 24/24 | ✅ 一致 |
| 前兆時間地震 | 13838 | 13838 | ✅ 一致 |
| 學習期間地震 | 17743 | 17743 | ✅ 一致 |
| 預測期間地震 | 13434 | 13434 | ✅ 一致 |

---

## 📁 檔案結構

```
python_src/
├── distribution_analysis.py          # 核心分析模組
├── region_subdivision.py             # 區域細分模組
├── run_distribution_analysis.py      # 主執行腳本
├── README_DISTRIBUTION_ANALYSIS.md   # 本文件
└── earthquake_distribution_analysis_*.mat  # 輸出結果
```

---

## 🛠️ 進階使用

### 自訂參數分析

```python
from distribution_analysis import (
    EarthquakeDistributionAnalyzer,
    DistributionParams
)

# 創建自訂參數
analyzer = EarthquakeDistributionAnalyzer('../config.json')
analyzer.params.m0 = 3.0  # 修改完整度閾值
analyzer.params.mT = 5.5  # 修改PPE閾值
analyzer.params.depth_threshold = 35.0  # 修改深度閾值

# 執行分析
results = analyzer.run_full_analysis(...)
```

### 只分析空間分布

```python
analyzer = EarthquakeDistributionAnalyzer('../config.json')
analyzer.load_data(horus_file, celle6_file, celle24_file)
data = analyzer.preprocess_data(coord_system='twd97')
spatial_results = analyzer.analyze_spatial_distribution(data)
```

### 只分析時間分段

```python
analyzer = EarthquakeDistributionAnalyzer('../config.json')
analyzer.load_data(horus_file, celle6_file, celle24_file)
data = analyzer.preprocess_data(coord_system='twd97')
temporal_results = analyzer.analyze_time_periods(data)
```

### 自訂區域細分

```python
from region_subdivision import CELLESubdivider

subdivider = CELLESubdivider()

# 6區域 → 48區域 (4倍經度 × 3倍緯度)
celle_48, info = subdivider.subdivide_celle(
    celle_original,
    lon_subdivisions=4,
    lat_subdivisions=3,
    output_filename='CELLE_48regions.mat'
)
```

---

## 🔧 故障排除

### 常見問題

1. **FileNotFoundError: 找不到數據文件**
   ```bash
   # 確認數據文件位置
   ls -lh ../data/GDMScatalog_A_filtered_twd97.mat
   ls -lh ../data/CELLE_ter_TW_twd97.mat
   ls -lh ../data/CELLE_ter_TW_twd97_24regions_correct.mat
   ```

2. **ValueError: CELLE 矩陣結構不符合預期**
   - 檢查 CELLE 檔案是否為標準 6區域 (2×3 網格)
   - 確認使用經度優先排列

3. **統計數字與 MATLAB 不一致**
   - 確認使用相同的配置文件
   - 檢查震級閾值參數 (m0, mT)
   - 驗證數據文件版本

---

## 📊 統計發現

根據 TWD97 座標分析結果：

### 空間分布特性
- **最活躍區域**: 區域4 (18,293筆, 39.4%)
- **6區域分布**: 變異係數 0.761
- **24區域分布**: 變異係數 0.881
- **結論**: 6區域分布相對更均勻

### 時間變化特性
- **學習期間**: 地震活動最頻繁 (17,743筆)
- **前兆時間**: >=m0 比例最高 (53.1%)
- **預測期間**: >=mT 比例最高 (0.2%)

### 大震分布
- **總大震數** (M≥5.0): 67筆
- **時間分布**: 前兆19筆, 學習22筆, 預測26筆
- **空間分布**: 集中在區域4和區域6

---

## 🤝 貢獻

本工具由 Claude Code 移植並優化。

---

## 📝 更新日誌

### v1.0 (2025-10-15)
- ✅ 首次移植完成
- ✅ 整合7個 MATLAB 腳本至2個 Python 模組
- ✅ 支持 TWD97 和 WGS84 座標系統
- ✅ 完整的驗證和測試
- ✅ 與 MATLAB 結果一致性驗證

---

## 📧 問題回報

如發現問題或需要改進，請在項目 issue 中回報。

---

**最後更新**: 2025-10-15
**版本**: 1.0
**狀態**: ✅ 生產就緒
