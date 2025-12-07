<div align="center">
  <img src="logos/logo.png" alt="EEPAS Logo" width="200"/>
  <h1>EEPAS Taiwan & Italy - Python Implementation</h1>

  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

<br/>

**EEPAS** (Every Earthquake a Precursor According to Scale) 地震預測模型的 Python 實現版本，支援台灣和義大利地區地震預測。

## ✨ 特性

- 🎯 **完整實現** - 包含 PPE、EEPAS 和餘震參數學習
- 🌍 **多區域支持** - 支援台灣和義大利模式，正確處理 Testing/Neighborhood 區域
- 🚀 **自動優化** - 自動邊界調整，確保收斂
- 📊 **多配置支持** - 台灣：標準、去叢集、包含921、m0=2.05；義大利：標準、三階段優化
- ⚡ **高性能** - 使用 Numba JIT 加速，PPE 預測快 60-70 倍，精度損失 <0.03%
- 🧪 **完全驗證** - 與論文 (ggad123.pdf) 數學定義完全一致，台灣模式向後相容

## 📊 最新成果 (v1.3.0)

### 🔬 數值積分重構與驗證

**核心成就：統一數值積分介面並驗證正確性**

本版本完成了數值積分方法的重構，統一了所有模組的積分呼叫介面，並通過 FAST vs ACCURATE 模式的全面比較驗證了實現的正確性。

**重構內容**：
- 統一數值積分介面（`utils/numerical_integration.py`）
- ACCURATE 模式：scipy.dblquad 雙重積分（最高精度）
- FAST 模式：梯形法積分（預設，高效能）
- 所有模組支持 `--accurate` / `--fast` 參數切換

**驗證結果** (`ACCURATE_VS_FAST_COMPARISON_REPORT.md`)：
- **測試期間**: 學習 1990-2012，預測 2012-2022
- **測試配置**: useCausalEW=0 (Fixed EW) 和 useCausalEW=1 (Dynamic EW)
- **參數一致性**:
  - PPE 參數差異 < 0.001%
  - EEPAS 參數差異 < 0.16%
  - Forecast Lambda 差異 < 0.004%
- **Lambda 積分驗證**:
  - Learning: Λ_PPE ≈ 27.00（目標事件數）✓
  - Forecast: PPE ~14 + EEPAS ~16 = ~30（接近 27）✓
- **性能提升**: FAST 模式整體快 **1.75 倍**（Forecast 快 **4 倍**）

**結論**: ✅ 重構成功，梯形法與 dblquad 結果高度一致（< 0.2% 差異），FAST 模式可安全用於日常研究

### 🌍 義大利地區驗證

**數學公式一致性**: 所有公式與論文 (ggad123.pdf) 完全一致 ✓

**典型參數** (1990-2012, 兩種積分模式驗證):
- PPE: a=0.616, d=29.64, s≈0
- Aftershock: v=0.577 (57.7% 非餘震), k=0.205
- EEPAS: am=1.23, bm=1.00, Sm=0.24, at=2.59, bt=0.35, St=0.15, ba=0.50, Sa=1.00, u=0.17
- NLL ≈ -495 to -496

## 📋 目錄

- [安裝](#安裝)
- [快速開始](#快速開始)
- [目錄結構](#目錄結構)
- [使用指南](#使用指南)
- [分析工具](#分析工具)
- [配置說明](#配置說明)
- [開發](#開發)
- [文檔](#文檔)
- [引用](#引用)

## 🚀 安裝

### 系統要求

- Python 3.8 或更高版本
- 8GB+ RAM (建議)
- Linux / macOS / Windows

### 依賴安裝

```bash
# 克隆倉庫
git clone https://github.com/your-org/EEPAS_Taiwan.git
cd EEPAS_Taiwan/src/python_src

# 安裝依賴
pip install -r requirements.txt
```

### 驗證安裝

```bash
python3 -c "import numpy, scipy, numba, pandas; print('✓ 所有依賴已安裝')"
```

## ⚡ 快速開始

### 台灣模式 - 完整預測流程

```bash
# 1. PPE 參數學習
python3 ppe_learning.py --config config.json

# 2. 餘震參數學習
python3 fit_aftershock_params.py --config config.json

# 3. EEPAS 參數學習（自動邊界調整）
python3 eepas_learning_auto_boundary.py --config config.json

# 4. PPE 預測（快速模式，預設啟用）
python3 ppe_make_forecast.py --config config.json

# 5. EEPAS 預測（快速模式，預設啟用）
python3 eepas_make_forecast.py --config config.json --fast
```

### 義大利模式 - 標準流程（推薦）

使用自動化腳本執行完整工作流程：

```bash
# FAST 模式 - 日常研究（快速，精度充分）
bash run_full_workflow_two_periods.sh

# ACCURATE 模式 - 最終驗證（慢，最高精度）
bash run_full_workflow_two_periods_accurate.sh
```

或手動執行單步流程：

```bash
# 義大利標準配置（自動處理 Testing/Neighborhood Region）
python3 ppe_learning.py --config config_italy.json --fast
python3 fit_aftershock_params.py --config config_italy.json --fast
python3 eepas_learning_auto_boundary.py --config config_italy.json --three-stage --fast
python3 ppe_make_forecast.py --config config_italy.json --fast
python3 eepas_make_forecast.py --config config_italy.json --fast

# 因果性權重測試配置
# EW0: Fixed EW (固定權重)
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json --three-stage --no-boundary-adjustment --fast

# EW1: Dynamic EW (動態權重)
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew1.json --three-stage --no-boundary-adjustment --fast
```

## 📁 目錄結構

```
python_src/
├── README.md                          # 本文件
├── USAGE.md                           # 詳細使用指南
├── requirements.txt                   # Python 依賴
│
├── 配置文件/
│   ├── config.json                          # 台灣標準配置
│   ├── config_decluster.json                # 台灣去叢集配置
│   ├── config_include921.json               # 台灣包含921配置
│   ├── config_m205.json                     # 台灣 m0=2.05 配置
│   ├── config_italy.json                    # 義大利標準配置
│   ├── config_italy_3stage.json             # 義大利三階段優化
│   ├── config_italy_causal_ew0.json         # 數值積分驗證: EW0
│   ├── config_italy_causal_ew0_accurate.json # 數值積分驗證: EW0 精確模式
│   ├── config_italy_causal_ew1.json         # 數值積分驗證: EW1
│   └── config_italy_causal_ew1_accurate.json # 數值積分驗證: EW1 精確模式
│
├── 核心程式/
│   ├── ppe_learning.py                      # PPE 參數學習
│   ├── fit_aftershock_params.py             # 餘震參數學習
│   ├── eepas_learning.py                    # EEPAS 基本學習
│   ├── eepas_learning_auto_boundary.py      # EEPAS 自動邊界調整（推薦）
│   ├── ppe_make_forecast.py                 # PPE 預測
│   ├── eepas_make_forecast.py               # EEPAS 預測
│   ├── optimize_eepas_parameters.py         # EEPAS 優化器
│   ├── eepas_likelihood.py                  # EEPAS 似然函數
│   ├── ppe_optimization.py                  # PPE 優化
│   ├── neg_log_like_aftershock.py           # 餘震似然函數
│   └── calculate_earthquake_weights.py      # 地震權重計算
│
├── utils/                             # 工具模組
│   ├── data_loader.py                       # 數據載入（支援區域配置）
│   ├── catalog_processor.py                 # 目錄處理（支援區域篩選）
│   ├── region_manager.py                    # 區域管理（Testing/Neighborhood）
│   ├── auto_boundary_adjustment.py          # 邊界調整邏輯
│   ├── get_paths.py                         # 路徑處理
│   └── fminsearchcon.py                     # 優化工具
│
├── data/                              # 地震數據
│   ├── Taiwan/                              # 台灣數據
│   │   ├── CELLE_ter_TW_twd97_24regions_correct.mat
│   │   └── GDMScatalog_A_filtered_twd97.mat
│   └── Italy/                               # 義大利數據
│       ├── CELLE_ter.mat                    # Testing region (177 grid cells)
│       ├── HORUS_Italy_RDN2008_polygon_filtered.mat  # Neighborhood region
│       └── CPTI15.mat                       # Italian catalog
│
├── docs/                              # 文檔和報告
│   ├── README.md                            # 子目錄總覽
│   └── ...
│
├── results/                           # 台灣標準結果
├── results_decluster/                 # 台灣去叢集結果
├── results_include921/                # 台灣包含921結果
├── results_m205_python/               # 台灣 m0=2.05 結果
├── results_italy/                     # 義大利標準結果
├── results_italy_3stage/              # 義大利三階段結果
├── results_italy_causal_ew0/          # 義大利 EW0 結果
├── results_italy_causal_ew0_accurate/ # 義大利 EW0 精確模式結果
├── results_italy_causal_ew1/          # 義大利 EW1 結果
└── archive_test_files/                # 歷史測試檔案（已歸檔）
```

## 📖 使用指南

### 核心流程

#### 1. PPE 參數學習

```bash
python3 ppe_learning.py --config config.json
```

**輸出**: `results/Fitted_par_PPE_2002_2016.csv`

#### 2. 餘震參數學習

```bash
python3 fit_aftershock_params.py --config config.json
```

**輸出**: `results/Fitted_par_aftershock_2002_2016.csv`

#### 3. EEPAS 參數學習

使用自動邊界調整（**推薦**）：

```bash
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1
```

**輸出**: `results/Fitted_par_EEPAS_2002_2016.csv`

**參數說明**:
- `--max-rounds`: 最大邊界調整輪數（預設 3）
- `--tolerance`: 邊界觸碰容差（預設 0.01 = 1%）
- `--expansion`: 邊界擴展倍數（預設 2.0）
- `--nll-threshold`: NLL 收斂閾值（預設 0.1）
- `--optimizer`: 優化器選擇（fminsearchcon, L-BFGS-B, TNC, SLSQP, Powell，預設 fminsearchcon）
- `--no-multistart`: 禁用多起始點（預設啟用 3 個起始點）
- `--n-starts`: 多起始點數量（預設 3）
- `--basinhopping`: 使用 Basin-Hopping 全局優化
- `--basinhopping-niter`: Basin-Hopping 迭代次數（預設 20）

**優化器選擇建議** (詳見 [OPTIMIZER_COMPARISON_REPORT.md](OPTIMIZER_COMPARISON_REPORT.md)):
- **推薦**: `fminsearchcon` (最穩健，所有配置都能找到高質量解)
- **快速**: `L-BFGS-B` + `--n-starts 3` (速度快但有 50% 機率陷入局部最優)
- **平衡**: 並行運行兩者，取較好結果

**示例**:
```bash
# 使用 L-BFGS-B + Multistart (3 個起始點)
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --optimizer L-BFGS-B \
    --n-starts 3

# 使用 fminsearchcon (單點，最穩健)
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --optimizer fminsearchcon \
    --no-multistart
```

#### 4-5. 預測

```bash
# PPE 預測
python3 ppe_make_forecast.py --config config.json

# EEPAS 預測
python3 eepas_make_forecast.py --config config.json
```

**輸出**: `results/PREVISIONI_3m_*_2016_2024_24.mat`

## 🔬 分析工具

### 地震分布分析

分析台灣地震在 6 區域和 24 區域的空間分布：

```bash
python3 analysis/run_distribution_analysis.py config.json
```

**輸出**:
- 控制台：統計摘要（有效地震數、區域活動性、時間分段）
- `.mat` 文件：完整分析結果

詳見：`docs/README_DISTRIBUTION_ANALYSIS.md`

### 權重分析

比較 4 種配置的地震權重分布：

```bash
python3 analysis/run_weight_analysis.py
```

**分析**:
- 4 種配置（標準、去叢集、包含921、m0=2.05）
- 年度和月度權重分布
- 統計特徵（均值、標準差、變異係數）
- 跨配置比較

詳見：`docs/README_WEIGHT_ANALYSIS.md`

### 區域細分

將 6 區域細分為 24 區域：

```bash
python3 analysis/region_subdivision.py \
    data/CELLE_ter_TW.mat \
    output_24regions.mat \
    --lon-subdivisions 2 \
    --lat-subdivisions 2
```

**流程**:
1. 在 WGS84 經緯度下細分（均勻角度間隔）
2. 使用 `convert_to_twd97.py` 轉換為 TWD97
3. 驗證轉換精度

詳見：`docs/REGION_SUBDIVISION_VERIFICATION.md`

### 座標轉換

WGS84（經緯度）→ TWD97 TM2 zone 121（投影座標）：

```bash
python3 utils/convert_to_twd97.py \
    --horus-in data/GDMScatalog_A_filtered.mat \
    --celle-in data/CELLE_ter_TW.mat \
    --horus-out output_catalog_twd97.mat \
    --celle-out output_celle_twd97.mat
```

**支持**:
- HORUS 地震目錄轉換
- CELLE 區域定義轉換
- EPSG:3826 投影（TWD97 TM2 zone 121）
- 公尺 → 公里單位轉換

## ⚙️ 配置說明

### 台灣配置

| 配置文件 | 說明 | m0 | 數據集 | 預期 NLL | Results 目錄 |
|----------|------|-----|--------|----------|-------------|
| `config.json` | 標準配置 | 2.35 | filtered | -344.83 | results/ |
| `config_decluster.json` | 去叢集配置 | 2.05 | declustered | -292.15 | results_decluster/ |
| `config_include921.json` | 包含 921 地震 | 2.35 | complete | -342.67 | results_include921/ |
| `config_m205.json` | m0=2.05 配置 | 2.05 | declustered | -296.72 | results_m205_python/ |

### 義大利配置

| 配置文件 | 說明 | 學習期 | 預測期 | useCausalEW | Results 目錄 |
|----------|------|--------|--------|-------------|-------------|
| `config_italy.json` | 標準配置 | 1990-2012 | 2012-2022 | 0 | results_italy/ |
| `config_italy_3stage.json` | 三階段優化 | 1990-2012 | 2012-2022 | 0 | results_italy_3stage/ |
| `config_italy_causal_ew0.json` | EW0 測試 | 1990-2012 | 2012-2022 | 0 | results_italy_causal_ew0/ |
| `config_italy_causal_ew0_accurate.json` | EW0 精確模式 | 1990-2012 | 2012-2022 | 0 | results_italy_causal_ew0_accurate/ |
| `config_italy_causal_ew1.json` | EW1 測試 | 1990-2012 | 2012-2022 | 1 | results_italy_causal_ew1/ |

**區域處理**：
- Testing Region: 177 個網格單元 (30√2 km)
- Neighborhood Region: CPTI15 多邊形（包含離岸區域，避免邊界效應）

**因果性設定**（用於數值積分驗證測試）：
- useCausalEW=0: Fixed EW（固定權重）
- useCausalEW=1: Dynamic EW（動態因果權重）

### 配置文件結構

```json
{
  "dataDir": "data",
  "resultsDir": "results",
  "catalogStartYear": 1991,
  "learnStartYear": 2002,
  "learnEndYear": 2016,
  "forecastStartYear": 2016,
  "forecastEndYear": 2024,
  "inputFiles": {
    "catalogFile": "GDMScatalog_A_filtered_twd97.mat",            // 地震目錄
    "neighborhoodRegionFile": "CPTI11.mat",                       // 鄰域區域（源事件）
    "testingRegionFile": "CELLE_ter_TW_twd97_24regions_correct.mat"  // 測試區域（目標事件）
  },
  "modelParams": {
    "m0": 2.35,
    "mT": 5.0,
    "B": 0.942069105,
    ...
  }
}
```

## 🧪 測試與驗證

### 台灣模式 - 與 MATLAB 版本比較

所有配置均已與 MATLAB 原版驗證，結果 100% 一致：

| 配置 | Python NLL | MATLAB NLL | 差異 |
|------|------------|------------|------|
| standard | -344.83 | -344.83 | 0.00 |
| decluster | -292.15 | -292.15 | 0.00 |
| include921 | -342.67 | -342.67 | 0.00 |
| m205 | -296.72 | -296.72 | 0.00 |

### 義大利模式 - 區域實現驗證

完全符合 ggad123.pdf Equation 1 的數學定義：

- ✅ **源事件**：來自 Neighborhood Region（避免邊界效應）
- ✅ **目標事件求和**：限制在 Testing Region R
- ✅ **積分範圍**：在 Testing Region R 上積分（CELLE grid）
- ✅ **台灣模式向後相容**：Testing Region = Neighborhood Region

### 性能驗證

**PPE Forecast 積分方法比較**：
- Accurate (scipy.integrate.quad_vec): 慢但精確
- Fast (Numba JIT midpoint): **快 60-70 倍**，精度損失 **<0.03%**

**EEPAS Forecast 優化**：
- 初始版本: 277 秒
- 優化後: **56 秒**（5x 加速）

## 🛠️ 開發

### 代碼規範

- Python 3.8+ 語法
- 類型提示（Type Hints）
- Docstring 文檔
- PEP 8 代碼風格

### 性能優化

- Numba JIT 編譯核心函數
- 向量化計算
- 稀疏矩陣運算

### 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 📚 文檔

### 主要文檔
- **README.md** (本文件) - 項目概覽與快速開始
- **USAGE.md** - 詳細使用指南
- **docs/README.md** - 子目錄文檔總覽

### 分析報告
- **docs/README_DISTRIBUTION_ANALYSIS.md** - 地震分布分析文檔
- **docs/README_WEIGHT_ANALYSIS.md** - 地震權重分析文檔
- **docs/REGION_SUBDIVISION_VERIFICATION.md** - 區域細分驗證報告

### 測試資料
測試檔案與中間結果已移至 `archive_test_files/` 目錄

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 致謝

- 原始 MATLAB 版本開發者
- 台灣中央氣象局地震測報中心（提供數據）
- GDMS 地震目錄維護團隊
- CPTI15 義大利地震目錄維護團隊

## 📖 引用

如果您在研究中使用此項目，請引用：

```bibtex
@software{eepas_taiwan_italy_python,
  title = {EEPAS Taiwan & Italy - Python Implementation},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/your-org/EEPAS_Taiwan}
}
```

## 🔗 相關資源

- [EEPAS 原論文 (ggad123.pdf)](ggad123.pdf)
- [台灣地震目錄](https://gdms.cwb.gov.tw/)
- [TWD97 座標系統](https://en.wikipedia.org/wiki/TWD97)

---

**版本**: 1.3.0
**Python**: 3.8+
**最後更新**: 2025-11-06

### 📝 最新更新 (v1.3.0)
- 🔬 **數值積分重構**：統一積分介面，支持 ACCURATE/FAST 模式切換
- ✅ **驗證完成**：FAST vs ACCURATE 參數差異 < 0.2%，重構正確性確認
- ⚡ **性能提升**：FAST 模式快 1.75 倍，Forecast 階段快 4 倍
- 📊 **Lambda 驗證**：Learning 和 Forecast 階段積分驗證通過
- 🚀 **自動化工作流程**：雙因果性設定完整流程腳本
