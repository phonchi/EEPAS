# Analysis Tools Directory

本資料夾包含 EEPAS Taiwan 項目的分析工具，用於地震數據分析、權重計算和區域處理。

## 📂 工具列表

### 1. 地震分布分析 (distribution_analysis.py)

**功能**：分析地震在6區域和24區域的分布差異

**使用方式**：
```bash
python3 distribution_analysis.py
```

**輸出**：
- `../analysis_outputs/distribution_comparison.txt` - 文字報告
- `../analysis_plots/earthquake_distribution_*.png` - 視覺化圖表
- `../analysis_data/region_*.json` - 詳細數據

**主要分析內容**：
- 6區域 vs 24區域地震數量比較
- 時間分布 (learning vs forecast period)
- 震級分布 (m0=2.35 vs m0=2.05)
- 統計顯著性檢驗

**執行時間**：~5秒

---

### 2. 權重分析 (weight_analysis.py)

**功能**：計算並比較四種配置的地震權重

**使用方式**：
```bash
python3 weight_analysis.py
```

**輸出**：
- `../docs/weight_analysis_report.txt` - 權重統計報告
- `../analysis_plots/weight_comparison_*.png` - 權重分布圖

**分析配置**：
1. 標準配置 (m0=2.35)
2. 去叢集配置 (m0=2.05)
3. 包含921配置 (m0=2.35)
4. m0=2.05 變體

**執行時間**：~8秒

---

### 3. 區域細分工具 (region_subdivision.py)

**功能**：將6個大區域細分為24個小區域

**使用方式**：
```bash
python3 region_subdivision.py
```

**輸出**：
- `../data/celle24_from_celle6.txt` - 24區域邊界數據
- 驗證報告

**驗證項目**：
- 邊界連續性檢查
- 區域面積計算
- 座標轉換正確性 (< 0.01m 誤差)

**執行時間**：~3秒

---

### 4. 執行腳本

#### run_distribution_analysis.py
```bash
python3 run_distribution_analysis.py
```
完整的分布分析流程，包含數據載入、分析和視覺化。

#### run_weight_analysis.py
```bash
python3 run_weight_analysis.py
```
完整的權重分析流程，包含四種配置的權重計算和比較。

---

## 🔧 依賴項

所有工具需要以下 Python 套件：
```bash
pip install numpy scipy pandas matplotlib pyproj
```

## 📊 輸出目錄

### analysis_data/
儲存中間數據和詳細結果（JSON, CSV格式）

### analysis_outputs/
儲存文字報告和摘要

### analysis_plots/
儲存所有視覺化圖表（PNG格式）

## 📖 詳細文檔

每個工具的詳細使用說明請參考：
- `../docs/README_DISTRIBUTION_ANALYSIS.md`
- `../docs/README_WEIGHT_ANALYSIS.md`
- `../docs/REGION_SUBDIVISION_VERIFICATION.md`

## 💡 常見用途

### 驗證數據質量
```bash
# 檢查地震分布是否合理
python3 distribution_analysis.py
```

### 比較配置效果
```bash
# 比較四種配置的權重差異
python3 weight_analysis.py
```

### 準備新數據
```bash
# 生成24區域邊界文件
python3 region_subdivision.py
```

## 🔍 故障排除

### 找不到數據文件
確保從 `python_src` 目錄執行：
```bash
cd /path/to/EEPAS_Taiwan-main/src/python_src/analysis
python3 distribution_analysis.py
```

### 座標轉換錯誤
檢查 pyproj 版本：
```bash
pip install --upgrade pyproj
```

---

**最後更新**：2025-10-19
