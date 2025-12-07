# EEPAS 權重分析模組使用說明

## 📋 概述

本模組將 MATLAB 版本的權重分析腳本移植到 Python，功能包括：

- 計算4種配置的EEPAS地震權重
- 生成詳細的統計分析報告
- 生成多種視覺化圖表

**移植自**:
- `analysis_plots/detail_analysis/WeightAnalyzer.m`
- `analysis_plots/detail_analysis/WeightVisualizer.m`
- `analysis_plots/detail_analysis/run_weight_analysis.m`
- `analysis_plots/detail_analysis/plot_detailed_time_series.m`
- `analysis_plots/detail_analysis/create_english_visualization.m`

## 🚀 快速開始

### 執行完整分析

```bash
cd /home/math/EEPAS_Taiwan-main/src/python_src
python3 run_weight_analysis.py
```

這將：
1. 分析4種配置 (standard, decluster, include921, decluster_include921)
2. 生成權重資料 CSV
3. 生成分析報告
4. 生成所有視覺化圖表

### 執行測試

```bash
# 測試單一配置的權重計算
python3 test_weight_analysis.py

# 測試圖表生成
python3 test_plot_generation.py
```

## 📁 檔案結構

### 核心模組

```
python_src/
├── weight_analysis.py          # 統一的分析與視覺化模組
│   ├── WeightAnalyzer          # 權重分析核心類別
│   ├── WeightVisualizer        # 視覺化繪圖類別
│   └── load_config_data()      # 載入配置與資料
│
├── run_weight_analysis.py      # 主執行腳本
├── test_weight_analysis.py     # 單一配置測試腳本
└── test_plot_generation.py     # 圖表生成測試腳本
```

### 輸出檔案

**權重資料** (CSV格式):
```
weights_standard.csv
weights_decluster.csv
weights_include921.csv
weights_decluster_include921.csv
```

**分析報告**:
```
weight_analysis_report.txt      # 綜合統計報告
```

**視覺化圖表** (`analysis_plots/` 目錄):
```
comprehensive_analysis.png      # 綜合分析圖 (6個子圖)
detailed_time_series.png        # 詳細時間序列圖 (6個子圖)
01_monthly_weight_changes.png   # 月度權重變化
02_annual_statistics.png        # 年度統計
03_921_earthquake_impact.png    # 921地震影響
04_weight_change_rate.png       # 權重變化率
05_weight_distribution_evolution.png  # 權重分布演化
06_configuration_comparison.png # 配置比較
```

## 📊 生成的圖表說明

### Comprehensive Analysis (綜合分析圖)

包含6個子圖：
1. **權重分布直方圖** - 比較4種配置的權重分布
2. **年度統計** - 年平均權重 ± 標準差
3. **921地震影響** - 1999年921地震前後2年的權重變化
4. **權重變化率** - 年度間權重變化率
5. **權重分布演化** - s1配置的權重隨時間演化熱圖
6. **配置比較** - 平行座標圖比較4種配置

### Detailed Time Series (詳細時間序列圖)

包含6個子圖：
1. **月度權重變化** - 每月平均權重趨勢
2. **年度平均±標準差** - 年度統計
3. **921地震前後對比** - 以季度解析度觀察921影響
4. **權重變化率** - 年度間變化率
5. **權重分布演化** - 2D直方圖熱圖
6. **配置統計比較** - 標準化統計指標比較

### Individual Plots (個別圖檔)

01-06號圖檔分別對應上述各項分析，方便單獨使用。

## 🎨 配置名稱映射

視覺化中使用簡化名稱：

| 配置檔案 | 顯示名稱 | 顏色 | 說明 |
|---------|---------|------|------|
| `config.json` | s1 | 紅色 | 標準配置 |
| `config_include921.json` | s2 | 綠色 | 包含921地震 |
| `config_decluster.json` | s3 | 藍色 | 去叢集化 |
| `config_decluster_include921.json` | s4 | 紫色 | 去叢集化+921 |

## 🔧 程式設計說明

### WeightAnalyzer 類別

主要方法：
- `load_config(config_name, config_path)` - 載入配置檔案
- `compute_and_store_weights(config_name, CatE, CatJ, params, config_file)` - 計算權重
- `analyze_all_configs()` - 綜合分析所有配置
- `export_weights(config_name, output_file)` - 匯出權重到CSV
- `generate_report(output_file)` - 生成分析報告

### WeightVisualizer 類別

主要方法：
- `plot_comprehensive_analysis(output_file)` - 生成綜合分析圖
- `plot_detailed_time_series(output_file)` - 生成詳細時間序列圖
- `save_individual_plots(output_dir)` - 保存個別圖檔

私有方法（各個子圖繪製函數）：
- `_plot_weight_distributions(ax)`
- `_plot_annual_statistics(ax)`
- `_plot_921_earthquake_impact(ax)`
- `_plot_weight_change_rate(ax)`
- `_plot_weight_distribution_evolution(ax)`
- `_plot_configuration_comparison(ax)`
- `_plot_monthly_weight_changes(ax)`

### 重要特性

1. **統一的顏色方案**: 所有圖表使用一致的s1-s4配色
2. **非交互式後端**: 自動使用Agg後端，適合無圖形環境
3. **模組化設計**: 功能集中在兩個類別中，易於維護
4. **容錯處理**: 包含異常處理和進度提示

## 📝 使用範例

### 範例1: 分析單一配置

```python
from weight_analysis import WeightAnalyzer, load_config_data

# 創建分析器
analyzer = WeightAnalyzer()

# 載入配置
analyzer.load_config('standard', '../config.json')

# 載入資料
CatE, CatJ, params = load_config_data('../config.json', 'standard')

# 計算權重
analyzer.compute_and_store_weights('standard', CatE, CatJ, params, '../config.json')

# 匯出權重
analyzer.export_weights('standard', 'weights_standard.csv')

# 查看統計
stats = analyzer.weight_storage['standard']['statistics']
print(f"平均權重: {stats['mean']:.6f}")
print(f"變異係數: {stats['cv']:.6f}")
```

### 範例2: 生成圖表

```python
from weight_analysis import WeightAnalyzer, WeightVisualizer

# 假設已經計算並儲存了權重
analyzer = WeightAnalyzer()
# ... (載入配置和計算權重)

# 創建視覺化器
visualizer = WeightVisualizer(analyzer)

# 生成綜合分析圖
visualizer.plot_comprehensive_analysis('comprehensive.png')

# 生成詳細時間序列圖
visualizer.plot_detailed_time_series('detailed_time_series.png')

# 保存個別圖檔
visualizer.save_individual_plots('plots_output')
```

### 範例3: 從CSV載入權重資料

```python
import pandas as pd
from weight_analysis import WeightAnalyzer, WeightVisualizer

analyzer = WeightAnalyzer()

# 從CSV載入
data = pd.read_csv('weights_standard.csv')

# 手動構建 weight_storage
weight_data = {
    'W': data['weight'].values,
    'EW': data['weight'].mean(),
    'CatE_updated': data[['year', 'month', 'day', 'hour', 'minute',
                          'sec', 'lat', 'lon', 'depth', 'mag', 'time']].values,
    'statistics': analyzer.compute_weight_statistics(data['weight'].values)
}

analyzer.weight_storage['standard'] = weight_data

# 然後可以使用視覺化功能
visualizer = WeightVisualizer(analyzer)
# ...
```

## ⚙️ 依賴項

- `numpy` - 數值計算
- `pandas` - 資料處理
- `matplotlib` - 繪圖
- `scipy` - 科學計算（載入MAT檔案）
- `numba` - JIT加速（權重計算）

## 🐛 常見問題

### Q1: 圖表無法生成，出現 Qt 錯誤

**解決方案**: 程式已自動設置使用 Agg 後端，不需要圖形環境。確保在導入 pyplot 前設置：
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```

### Q2: 找不到地震目錄檔案

**解決方案**: 確保執行目錄正確，資料檔案應在 `../data/` 目錄下。

### Q3: 權重計算出現 NaN

**原因**: 某些地震事件的權重計算可能產生 NaN（如分母為0）。

**處理**: 程式會自動移除 NaN 值並輸出警告訊息。

### Q4: 記憶體不足

**解決方案**:
- 一次只處理一個配置
- 使用測試腳本先測試
- 生成圖表後立即關閉 figure: `plt.close()`

## 📖 與MATLAB版本的對應關係

| MATLAB 檔案 | Python 模組/類別 | 功能 |
|------------|-----------------|------|
| `WeightAnalyzer.m` | `WeightAnalyzer` 類別 | 權重分析核心 |
| `WeightVisualizer.m` | `WeightVisualizer` 類別 | 視覺化繪圖 |
| `run_weight_analysis.m` | `run_weight_analysis.py` | 主執行腳本 |
| `analyze_config_weights.m` | `load_config_data()` 函數 | 載入配置資料 |
| `plot_detailed_time_series.m` | `plot_detailed_time_series()` | 時間序列圖 |
| `create_english_visualization.m` | `save_individual_plots()` | 個別圖檔 |

## 🔄 更新日誌

**2025-10-15**
- ✅ 完成 MATLAB 程式移植
- ✅ 統一分析與視覺化功能到單一模組
- ✅ 添加非交互式後端支援
- ✅ 通過單一配置測試
- ✅ 通過圖表生成測試

## 📧 技術支援

如有問題請參考：
- `claude.md` - EEPAS專案移植經驗總結
- `calculate_earthquake_weights.py` - 權重計算核心模組文檔

---

**注意**: 本模組為 EEPAS Taiwan 專案的一部分，專注於權重分析與視覺化功能。完整的EEPAS執行流程請參考主專案文檔。
