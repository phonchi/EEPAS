# 核心模組完整依賴分析

**目的**：確保 GitHub 上傳包含所有必要的依賴檔案

---

## 📊 依賴樹狀圖

### 1️⃣ ppe_learning.py (Sphinx 直接引用)
```
ppe_learning.py
├── utils/data_loader.py ✓
├── utils/catalog_processor.py ✓
├── utils/region_manager.py ✓
├── utils/get_paths.py ✓
├── utils/fminsearchcon.py ✓
└── ppe_optimization.py ✓ (必須上傳)
    └── utils/numerical_integration.py ✓
```

### 2️⃣ fit_aftershock_params.py (Sphinx 直接引用)
```
fit_aftershock_params.py
├── utils/fminsearchcon.py ✓
├── utils/data_loader.py ✓
├── utils/catalog_processor.py ✓
├── utils/get_paths.py ✓
└── neg_log_like_aftershock.py ✓ (必須上傳)
    └── utils/numerical_integration.py ✓
```

### 3️⃣ eepas_learning_auto_boundary.py (Sphinx 直接引用)
```
eepas_learning_auto_boundary.py
├── eepas_learning.py ✓ (必須上傳)
│   ├── utils/data_loader.py ✓
│   ├── utils/catalog_processor.py ✓
│   ├── utils/region_manager.py ✓
│   ├── utils/get_paths.py ✓
│   ├── eepas_likelihood.py ✓ (必須上傳)
│   │   └── utils/numerical_integration.py ✓
│   ├── calculate_earthquake_weights.py ✓ (必須上傳)
│   │   └── utils/data_loader.py ✓
│   └── optimize_eepas_parameters.py ✓ (必須上傳)
│       ├── eepas_likelihood.py ✓
│       ├── utils/data_loader.py ✓
│       └── utils/fminsearchcon.py ✓
└── utils/auto_boundary_adjustment.py ✓ (必須上傳)
```

### 4️⃣ ppe_make_forecast.py (Sphinx 直接引用)
```
ppe_make_forecast.py
├── utils/data_loader.py ✓
├── utils/catalog_processor.py ✓
├── utils/region_manager.py ✓
├── utils/get_paths.py ✓
└── utils/numerical_integration.py ✓
```

### 5️⃣ eepas_make_forecast.py (Sphinx 直接引用)
```
eepas_make_forecast.py
├── utils/data_loader.py ✓
├── utils/catalog_processor.py ✓
├── utils/region_manager.py ✓
├── utils/get_paths.py ✓
├── calculate_earthquake_weights.py ✓ (必須上傳)
│   └── utils/data_loader.py ✓
└── utils/numerical_integration.py ✓
```

---

## ✅ 必須上傳的核心模組清單

### 📁 主程式目錄（12 個 .py 檔案）

| # | 檔案 | 類型 | 原因 |
|---|------|------|------|
| 1 | `ppe_learning.py` | 主程式 | Sphinx 直接引用 |
| 2 | `fit_aftershock_params.py` | 主程式 | Sphinx 直接引用 |
| 3 | `eepas_learning_auto_boundary.py` | 主程式 | Sphinx 直接引用 |
| 4 | `ppe_make_forecast.py` | 主程式 | Sphinx 直接引用 |
| 5 | `eepas_make_forecast.py` | 主程式 | Sphinx 直接引用 |
| 6 | `eepas_learning.py` | 依賴 | 被 `eepas_learning_auto_boundary.py` 引用 |
| 7 | `eepas_likelihood.py` | 依賴 | 被 `eepas_learning.py` 引用 |
| 8 | `optimize_eepas_parameters.py` | 依賴 | 被 `eepas_learning.py` 引用 |
| 9 | `ppe_optimization.py` | 依賴 | 被 `ppe_learning.py` 引用 |
| 10 | `neg_log_like_aftershock.py` | 依賴 | 被 `fit_aftershock_params.py` 引用 |
| 11 | `calculate_earthquake_weights.py` | 依賴 | 被 `eepas_learning.py`, `eepas_make_forecast.py` 引用 |
| 12 | `setup.py` | 安裝 | Python package 安裝腳本 |

### 📁 utils/ 模組（10 個）

| # | 檔案 | 引用次數 | 原因 |
|---|------|----------|------|
| 1 | `utils/__init__.py` | - | Package 初始化 |
| 2 | `utils/data_loader.py` | 所有 | 被所有核心模組引用 |
| 3 | `utils/catalog_processor.py` | 所有 | 被所有核心模組引用 |
| 4 | `utils/region_manager.py` | 大部分 | 被大部分核心模組引用 |
| 5 | `utils/get_paths.py` | 大部分 | 被大部分核心模組引用 |
| 6 | `utils/fminsearchcon.py` | 多個 | 優化器，被多個模組引用 |
| 7 | `utils/coordinate_transform.py` | Sphinx | Sphinx API 文檔引用 |
| 8 | `utils/auto_boundary_adjustment.py` | 1 | 被 `eepas_learning_auto_boundary.py` 引用 |
| 9 | `utils/numerical_integration.py` | 多個 | 被多個模組引用（核心數值計算） |
| 10 | `utils/catalog_processor_extensions.py` | 可選 | 擴展功能（建議保留） |

### 📁 analysis/ 模組（9 個，Sphinx 引用）

| # | 檔案 | 說明 |
|---|------|------|
| 1 | `analysis/__init__.py` | Package 初始化 |
| 2 | `analysis/optimize_psi_working.py` | Ψ 現象檢測 |
| 3 | `analysis/optimize_psi_results.py` | Ψ 去重 |
| 4 | `analysis/plot_relations.py` | 標度關係分析 |
| 5 | `analysis/dataset.py` | 數據集提取 |
| 6 | `analysis/decimal_time.py` | 時間轉換 |
| 7 | `analysis/select_m5plus.py` | 事件篩選 |
| 8 | `analysis/analyze_forecast_lambda.py` | 預測驗證 |
| 9 | `analysis/forecast_converter.py` | PyCSEP 格式轉換 |
| 10 | `analysis/patch_pycsep.py` | pycsep 補丁 |

---

## ❌ 不上傳的檔案（已在 .gitignore 中排除）

### 測試/開發用工具腳本
```
add_bounds_to_strategies.py
auto_monitor_and_compare.py
batch_fix_docstrings.py
cleanup_docstrings.py
compare_forecast_matrices.py
compare_new_vs_old_results.py
compare_results.py
start_new_strategy_verification.py
```

### 測試/開發用分析腳本
```
analysis/run_distribution_analysis.py
analysis/run_weight_analysis.py
analysis/region_subdivision.py
analysis/distribution_analysis.py
analysis/weight_analysis.py
```

**原因**：這些是開發測試用途，不被 Sphinx 文檔引用，不影響核心功能。

---

## 🔍 驗證方法

### 檢查所有依賴是否完整

```bash
# 1. 檢查主程式模組
for file in ppe_learning.py fit_aftershock_params.py \
            eepas_learning_auto_boundary.py ppe_make_forecast.py \
            eepas_make_forecast.py; do
    echo "=== $file ==="
    grep "^from \|^import " $file | grep -v "typing\|sys\|os\|numpy\|scipy\|pandas"
done

# 2. 檢查間接依賴
for file in eepas_learning.py eepas_likelihood.py \
            optimize_eepas_parameters.py ppe_optimization.py \
            neg_log_like_aftershock.py calculate_earthquake_weights.py; do
    echo "=== $file ==="
    grep "^from \|^import " $file | grep -v "typing\|sys\|os\|numpy\|scipy\|pandas"
done

# 3. 確認檔案存在
ls -1 ppe_learning.py fit_aftershock_params.py \
      eepas_learning_auto_boundary.py ppe_make_forecast.py \
      eepas_make_forecast.py eepas_learning.py \
      eepas_likelihood.py optimize_eepas_parameters.py \
      ppe_optimization.py neg_log_like_aftershock.py \
      calculate_earthquake_weights.py setup.py

ls -1 utils/data_loader.py utils/catalog_processor.py \
      utils/region_manager.py utils/get_paths.py \
      utils/fminsearchcon.py utils/coordinate_transform.py \
      utils/auto_boundary_adjustment.py utils/numerical_integration.py
```

### 檢查是否被 .gitignore 錯誤排除

```bash
# 確認核心檔案不在 .gitignore 中
git check-ignore -v eepas_learning.py eepas_likelihood.py \
                    optimize_eepas_parameters.py ppe_optimization.py \
                    neg_log_like_aftershock.py calculate_earthquake_weights.py

# 如果有輸出，表示被排除了（需要修正）
# 無輸出表示正常
```

---

## 📦 完整上傳清單總結

**Python 模組總計**：
- 主程式：12 個
- utils/：10 個
- analysis/：10 個（9 個 .py + 1 個 __init__.py）
- **總計**：32 個 Python 檔案

**其他必要檔案**：
- Jupyter Notebooks：4 個
- 配置檔案：6 個
- Sphinx 文檔：完整
- 數據檔案：15 個 .mat
- 文檔：README, USAGE, LICENSE 等

**總上傳大小**：~170 MB

---

## ✅ 檢查清單

- [x] 所有 Sphinx 直接引用的 5 個主程式
- [x] 所有間接依賴的 6 個核心模組
- [x] 所有 utils/ 工具模組（10 個）
- [x] 所有 analysis/ 分析模組（9 個）
- [x] setup.py 安裝腳本
- [x] .gitignore 已更新（不會排除核心檔案）
- [x] 依賴關係已完整分析

---

**版本**：v1.3.0
**日期**：2025-12-07
**狀態**：✅ 已驗證完整
