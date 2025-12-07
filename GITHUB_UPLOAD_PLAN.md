# GitHub 上傳計劃

## 📋 上傳檔案清單（基於 Sphinx 文檔引用）

本文檔列出所有需要上傳到 GitHub 的檔案，確保 Sphinx 文檔完整可用。

---

## ✅ 必須上傳的檔案

### 1. **核心 Python 模組**（Sphinx API 引用）

#### 主程式（根目錄 - 12 個）

**Sphinx 直接引用（5 個）**
```
✅ ppe_learning.py                      # PPE 參數學習
✅ fit_aftershock_params.py             # 餘震參數擬合
✅ eepas_learning_auto_boundary.py      # EEPAS 自動邊界學習
✅ ppe_make_forecast.py                 # PPE 預測生成
✅ eepas_make_forecast.py               # EEPAS 預測生成
```

**核心依賴（6 個，必須上傳）**
```
✅ eepas_learning.py                    # 被 eepas_learning_auto_boundary.py 引用
✅ eepas_likelihood.py                  # 被 eepas_learning.py 引用
✅ optimize_eepas_parameters.py         # 被 eepas_learning.py 引用
✅ ppe_optimization.py                  # 被 ppe_learning.py 引用
✅ neg_log_like_aftershock.py           # 被 fit_aftershock_params.py 引用
✅ calculate_earthquake_weights.py      # 被 eepas_learning.py, eepas_make_forecast.py 引用
```

**其他**
```
✅ setup.py                             # Python package 安裝腳本
```

#### 工具模組（utils/ - 10 個）
```
✅ utils/__init__.py                    # Package 初始化
✅ utils/data_loader.py                 # 數據載入器（被所有核心模組引用）
✅ utils/catalog_processor.py           # 目錄處理器（被所有核心模組引用）
✅ utils/region_manager.py              # 區域管理器（被大部分模組引用）
✅ utils/get_paths.py                   # 路徑處理（被大部分模組引用）
✅ utils/fminsearchcon.py               # 優化工具（被多個模組引用）
✅ utils/coordinate_transform.py        # 座標轉換（Sphinx 引用）
✅ utils/auto_boundary_adjustment.py    # 自動邊界調整（被 eepas_learning_auto_boundary.py 引用）
✅ utils/numerical_integration.py       # 數值積分（被多個模組引用）
✅ utils/catalog_processor_extensions.py # 擴展功能（建議保留）
```

#### 分析模組（analysis/ - 10 個，Sphinx 引用）
```
✅ analysis/__init__.py                 # Package 初始化
✅ analysis/optimize_psi_working.py     # Ψ 現象檢測
✅ analysis/optimize_psi_results.py     # Ψ 去重
✅ analysis/plot_relations.py           # 標度關係分析
✅ analysis/dataset.py                  # 數據集提取
✅ analysis/decimal_time.py             # 時間轉換
✅ analysis/select_m5plus.py            # 事件篩選
✅ analysis/analyze_forecast_lambda.py  # 預測驗證
✅ analysis/forecast_converter.py       # PyCSEP 格式轉換
✅ analysis/patch_pycsep.py             # pycsep 補丁
```

**注意**：上述列表已包含所有核心依賴。詳細依賴關係請參閱 `CORE_MODULES_DEPENDENCY.md`。

---

### 2. **Jupyter Notebooks**（Sphinx examples/ 引用）

```
✅ analysis/Estimate_mc_b_Italy_clean.ipynb     # b 值分析
✅ analysis/Examine_Psi_Italy_clean.ipynb       # Ψ 參數優化視覺化
✅ analysis/earth_viz_Italy_clean.ipynb         # 地圖繪製（缺失，需確認）
✅ analysis/EEPAS_Forecast_Evaluation_New.ipynb # 預測評估
```

**注意**：`earth_viz_Italy_clean.ipynb` 在 Sphinx 中有引用，但檔案可能不存在，需確認。

---

### 3. **配置檔案**

```
✅ config_italy.json                    # 義大利標準配置
✅ config_italy_3stage.json             # 義大利三階段優化
✅ config_italy_causal_ew0.json         # 義大利 EW0（主要結果）
✅ config_italy_causal_ew0_accurate.json # 義大利 EW0 精確模式
✅ config_italy_causal_ew1.json         # 義大利 EW1
✅ config.json                          # 台灣標準配置（參考）
```

---

### 4. **數據檔案**（data/）

```
✅ data/HORUS_Italy_RDN2008_polygon_filtered.mat  # 義大利地震目錄
✅ data/CPTI15.mat                                # 鄰域區域（多邊形）
✅ data/CELLE_ter.mat                             # 測試區域（177 網格）
✅ data/GDMScatalog_A_filtered_twd97.mat          # 台灣目錄（參考）
✅ data/CELLE_ter_TW_twd97_24regions_correct.mat  # 台灣網格（參考）
```

**大小估計**：約 10-50 MB（需檢查是否超過 GitHub 限制）

---

### 5. **Sphinx 文檔**

#### 原始碼（docs/source/）
```
✅ docs/source/conf.py                  # Sphinx 配置
✅ docs/source/index.rst                # 首頁
✅ docs/source/api_reference/index.rst  # API 索引
✅ docs/source/api_reference/core.rst   # 核心模組 API
✅ docs/source/api_reference/utils.rst  # 工具模組 API
✅ docs/source/api_reference/analysis.rst # 分析模組 API
✅ docs/source/user_guide/*.rst         # 用戶指南（所有檔案）
✅ docs/source/technical/*.rst          # 技術文檔（所有檔案）
✅ docs/source/examples/index.rst       # 範例索引
✅ docs/source/examples/*.ipynb         # Notebook 符號連結
✅ docs/source/_static/                 # 靜態資源
✅ docs/source/_templates/              # 模板
```

#### 編譯結果（docs/build/）
```
✅ docs/build/html/**/*                 # 完整 HTML 文檔（用於 GitHub Pages）
```

---

### 6. **文檔與說明**

```
✅ README.md                            # 專案主文檔
✅ USAGE.md                             # 詳細使用指南
✅ CHANGELOG.md                         # 版本變更記錄（如有）
✅ requirements.txt                     # Python 依賴
✅ setup.py                             # 安裝腳本
✅ LICENSE                              # MIT 授權（需創建）
✅ .gitignore                           # Git 忽略規則
✅ CLAUDE.md                            # Claude Code 開發注意事項
```

---

### 7. **結果目錄佔位**

```
✅ results_italy_causal_ew0/.gitkeep    # 主要結果目錄佔位
✅ results_italy_causal_ew0_accurate/.gitkeep # 精確模式結果目錄佔位
```

**說明**：結果檔案（.csv, .mat）過大，不上傳實際檔案，只保留目錄結構。

---

### 8. **其他必要檔案**

```
✅ logos/logo.png                       # 專案 Logo（README 引用）
✅ docs/README.md                       # 文檔目錄說明
✅ utils/README.md                      # 工具模組說明
✅ analysis/README.md                   # 分析模組說明
```

---

## ❌ 不上傳的檔案（已加入 .gitignore）

### 1. **Python 快取**
- `__pycache__/`（35 個目錄）
- `*.pyc`
- `*.pyo`

### 2. **結果檔案**（太大）
- `results/`（台灣標準結果）
- `results_italy/`（義大利標準結果）
- `results_*_BACKUP_*/`（所有備份目錄）
- `results_*_new/`（測試結果）
- `results_*_reference/`（參考結果）
- 所有 `*.csv` 和 `*.mat` 結果檔案

### 3. **測試與臨時檔案**
- `archive/`
- `.archive/`
- `archive_test_files/`
- `test_data/`
- `test_output/`
- `analysis_outputs/`
- `analysis_plots/`
- `analysis_data/`
- `*.log`, `*.bak`, `*.tmp`
- `*Zone.Identifier`
- `*_autoadjusted_round*.json`

### 4. **測試配置檔案**
- `config_test_*.json`
- `config_*_new.json`
- `config_*_old_format.json`
- `*.json.round*.bak`

### 5. **非 Sphinx 引用的工具腳本**
- `add_bounds_to_strategies.py`
- `auto_monitor_and_compare.py`
- `batch_fix_docstrings.py`
- `cleanup_docstrings.py`
- `compare_forecast_matrices.py`
- `compare_new_vs_old_results.py`
- `compare_results.py`
- `start_new_strategy_verification.py`
- `analysis/run_distribution_analysis.py`
- `analysis/run_weight_analysis.py`
- `analysis/region_subdivision.py`
- `analysis/distribution_analysis.py`
- `analysis/weight_analysis.py`

### 6. **非 Sphinx 開發文檔**
- `CUSTOM_STAGES_USAGE.md`
- `OPTIMIZATION_MODES_GUIDE.md`
- `STAGE1_SINGLE_STAGE_IMPLEMENTATION.md`
- `STAGE1_VERIFICATION_REPORT.md`
- `ACCURATE_VS_FAST_COMPARISON_REPORT.md`
- `NUMERICAL_INTEGRATION_USAGE.md`
- `INTERNATIONALIZATION_AND_SPHINX_PLAN.md`
- `USAGE_EN.md`
- `CHANGELOG_EN.md`
- 其他開發報告文檔

---

## 📊 上傳大小估計

| 類別 | 檔案數量 | 預估大小 |
|------|---------|---------|
| Python 原始碼 | ~30 | 500 KB |
| Jupyter Notebooks | 3-4 | 2 MB |
| 配置檔案 | 6 | 20 KB |
| 數據檔案 | 5 | **10-50 MB** ⚠️ |
| Sphinx 原始碼 | ~20 | 200 KB |
| Sphinx HTML | ~200 | **5-10 MB** |
| 文檔 | 5 | 100 KB |
| **總計** | ~300 | **20-70 MB** |

⚠️ **注意**：數據檔案可能超過 GitHub 建議大小（50 MB），需要檢查！

---

## 🚀 上傳步驟

### 步驟 1：清理快取
```bash
# 清理所有 Python 快取
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
```

### 步驟 2：檢查大檔案
```bash
# 檢查超過 50MB 的檔案
find . -type f -size +50M -exec ls -lh {} \;

# 檢查 .mat 檔案大小
find data -name "*.mat" -exec du -h {} \; | sort -rh
```

### 步驟 3：創建 LICENSE
```bash
# 創建 MIT License（範例）
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 EEPAS Development Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### 步驟 4：驗證 .gitignore
```bash
# 檢查將被上傳的檔案（前 50 個）
git status --short | head -50

# 檢查將被忽略的檔案（前 50 個）
git status --ignored --short | head -50
```

### 步驟 5：提交與推送
```bash
# 添加所有追蹤的檔案
git add .gitignore GITHUB_UPLOAD_PLAN.md
git add results_italy_causal_ew0/.gitkeep results_italy_causal_ew0_accurate/.gitkeep

# 提交
git commit -m "準備 GitHub 上傳：精簡專案檔案，保留 Sphinx 必要內容

- 更新 .gitignore，排除測試檔案、快取、結果檔案
- 保留 Sphinx 引用的所有 Python 模組和 Notebooks
- 上傳 Sphinx 編譯結果（docs/build/html）用於 GitHub Pages
- 創建結果目錄佔位檔案

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 推送到 GitHub
git push -u origin master
```

---

## 📝 後續工作

### GitHub Pages 設定
1. 進入 GitHub repo → Settings → Pages
2. Source: Deploy from a branch
3. Branch: `master` / 目錄: `/docs/build/html`
4. 文檔將發布在：`https://YOUR_USERNAME.github.io/EEPAS_Taiwan/`

### 大檔案處理（如需要）
如果數據檔案超過 100MB：
1. 使用 Git LFS
2. 或上傳到外部儲存（Zenodo, Google Drive）
3. 在 README 提供下載連結

---

**版本**：v1.3.0
**日期**：2025-12-07
**負責人**：Claude Code
