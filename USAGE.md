# EEPAS Taiwan & Italy - 詳細使用指南

## 目錄

1. [安裝與環境](#安裝與環境)
2. [完整工作流程](#完整工作流程)
3. [核心程式詳解](#核心程式詳解)
4. [配置文件說明](#配置文件說明)
5. [自動邊界調整](#自動邊界調整)
6. [結果解讀](#結果解讀)
7. [論文驗證工作流程](#論文驗證工作流程)
8. [故障排除](#故障排除)
9. [高級用法](#高級用法)

---

## 安裝與環境

### 系統需求

- Python 3.8+
- 8GB+ RAM (推薦16GB)
- Linux/Mac/Windows (WSL)

### 安裝依賴

```bash
pip install numpy scipy numba pandas h5py
```

### 驗證安裝

```bash
python3 -c "import numpy, scipy, numba, pandas, h5py; print('✅ All dependencies installed')"
```

---

## 完整工作流程

### 標準5步驟流程

```bash
cd /home/math/EEPAS_Taiwan-main/src/python_src

# 步驟1: PPE學習
python3 ppe_learning.py --config ../config.json

# 步驟2: 餘震學習
python3 fit_aftershock_params.py --config ../config.json

# 步驟3: EEPAS學習（自動邊界調整）
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1

# 步驟4: PPE預測
python3 ppe_make_forecast.py --config ../config.json

# 步驟5: EEPAS預測
python3 eepas_make_forecast.py --config ../config.json
```

### 批次處理多個配置

```bash
#!/bin/bash
for config in config.json config_include921.json config_m205.json config_decluster.json; do
    echo "處理 $config..."

    python3 ppe_learning.py --config ../$config
    python3 fit_aftershock_params.py --config ../$config
    python3 eepas_learning_auto_boundary.py --config ../$config
    python3 ppe_make_forecast.py --config ../$config
    python3 eepas_make_forecast.py --config ../$config

    echo "完成 $config"
done
```

---

## 核心程式詳解

### 1. PPE學習 (ppe_learning.py)

**功能**: 學習Proximity to Past Earthquakes背景地震率參數

**使用方式**:
```bash
python3 ppe_learning.py \
    --config ../config.json \
    --fit-mode joint \
    --grid-res 40
```

**參數說明**:
- `--config`: 配置文件路徑
- `--fit-mode`: 優化模式
  - `joint`: 聯合優化a, d, s（推薦）
  - `decoupled_gr`: 分離優化，使用G-R關係固定a
- `--grid-res`: 網格解析度（20-50，預設40）

**輸出**:
- `results_*/Fitted_par_PPE_*.csv`
- 包含參數：a (地震率), d (空間衰減), s (震級衰減), ln_likelihood

**執行時間**: ~4秒 (m0=2.35)

---

### 2. 餘震學習 (fit_aftershock_params.py)

**功能**: 擬合餘震觸發參數v, k

**使用方式**:
```bash
python3 fit_aftershock_params.py --config ../config.json
```

**依賴**: 需要先完成PPE學習

**輸出**:
- `results_*/Fitted_par_aftershock_*.csv`
- 包含參數：v (觸發強度), k (PPE與餘震比例), ln_likelihood

**執行時間**: ~3秒

---

### 3. EEPAS學習 - 基本版 (eepas_learning.py)

**功能**: 基本的EEPAS參數學習（無自動邊界調整）

**使用方式**:
```bash
python3 eepas_learning.py --config ../config.json --m0 2.35
```

**參數**:
- `--config`: 配置文件
- `--m0`: 完整度震級（可選，覆蓋配置文件）
- `--optimizer`: 優化器選擇（fminsearchcon, L-BFGS-B, TNC, SLSQP, Powell，預設 fminsearchcon）
- `--no-multistart`: 禁用多起始點（預設啟用 3 個起始點）
- `--n-starts`: 多起始點數量（預設 3）
- `--basinhopping`: 使用 Basin-Hopping 全局優化
- `--basinhopping-niter`: Basin-Hopping 迭代次數（預設 20）

**三階段優化**:
1. Stage 1: 優化 am, at, Sa, u
2. Stage 2: 優化 Sm, bt, St, ba, u
3. Stage 3: 聯合優化全部8個參數

**優化器選擇建議**:
- **推薦**: `fminsearchcon` (最穩健，所有配置都能找到高質量解)
- **快速**: `L-BFGS-B` + `--n-starts 3` (速度快但有 50% 機率陷入局部最優)
- **平衡**: 並行運行兩者，取較好結果

**範例**:
```bash
# 使用預設 fminsearchcon
python3 eepas_learning.py --config ../config.json

# 使用 L-BFGS-B + multistart (3個起始點)
python3 eepas_learning.py --config ../config.json --optimizer L-BFGS-B --n-starts 3

# 使用 SLSQP 單起始點
python3 eepas_learning.py --config ../config.json --optimizer SLSQP --no-multistart
```

**輸出**:
- `results_*/Fitted_par_EEPAS_*.csv`
- 包含9個欄位：am, bm, Sm, at, bt, St, ba, Sa, u, ln_likelihood

**執行時間**:
- fminsearchcon: ~230秒
- L-BFGS-B: ~30秒 (單次)
- Multistart (3次): ~90秒

---

### 4. EEPAS學習 - 自動邊界調整版 (eepas_learning_auto_boundary.py) ⭐推薦

**功能**: 自動檢測並調整邊界，直到優化收斂

**使用方式**:
```bash
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1
```

**參數詳解**:

| 參數 | 預設值 | 範圍 | 說明 |
|------|--------|------|------|
| `--max-rounds` | 3 | 1-5 | 最大邊界調整輪數 |
| `--tolerance` | 0.01 | 0.001-0.1 | 邊界觸碰容差（相對比例） |
| `--expansion` | 2.0 | 1.5-3.0 | 邊界擴展倍數 |
| `--nll-threshold` | 0.1 | 0.01-1.0 | NLL收斂閾值 |

**工作流程**:
1. 使用當前邊界執行EEPAS學習
2. 檢查參數是否觸碰邊界
3. 如果觸碰，自動放寬邊界並備份配置
4. 重複直到：
   - NLL收斂（連續兩輪改善 < threshold）
   - 無參數觸碰邊界
   - 達到最大輪數

**停止條件**:
- ✅ **NLL收斂**: 最常見，表示已找到最優解
- ✅ **無邊界問題**: 第1輪即無觸碰
- ⚠️ **最大輪數**: 可能需要檢查參數

**輸出**:
- 與基本版相同，但會生成配置備份文件：
  - `config.json.round1.bak`
  - `config.json.round2.bak`
  - ...

**執行時間**: ~10-20分鐘（2-3輪）

---

### 5. PPE預測 (ppe_make_forecast.py)

**功能**: 生成PPE背景地震率預測

**使用方式**:
```bash
python3 ppe_make_forecast.py --config ../config.json
```

**依賴**: 需要PPE學習結果

**輸出**:
- `results_*/PREVISIONI_3m_PPE_*.mat`
- MATLAB格式，包含各預測窗口的地震率

**執行時間**: ~3分鐘

---

### 6. EEPAS預測 (eepas_make_forecast.py)

**功能**: 生成EEPAS完整模型預測

**使用方式**:
```bash
python3 eepas_make_forecast.py --config ../config.json
```

**依賴**: 需要PPE、餘震、EEPAS全部學習結果

**輸出**:
- `results_*/PREVISIONI_3m_EEPAS_*.mat`
- 混合EEPAS和PPE預測結果

**執行時間**: ~4分鐘

---

## 配置文件說明

### 配置結構

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
    "catalogFile": "...",            // 地震目錄檔案 (HORUS格式)
    "neighborhoodRegionFile": "...", // 鄰域區域檔案 (CPTI15 polygon)
    "testingRegionFile": "..."       // 測試區域檔案 (CELLE網格)
  },

  "optimization": {
    "stage1": {...},
    "stage2": {...},
    "stage3": {...}
  },

  "modelParams": {
    "m0": 2.35,
    "mT": 5.0,
    "B": 0.942,
    ...
  }
}
```

### 關鍵參數

#### 時間範圍
- `catalogStartYear`: 地震目錄起始年份
- `learnStartYear/learnEndYear`: 學習期間
- `forecastStartYear/forecastEndYear`: 預測期間

#### 模型參數
- `m0`: 完整度震級（影響數據量）
- `mT`: 觸發門檻震級
- `B`: G-R關係參數
- `delay`: 前瞻性延遲天數

#### 優化參數 (Stage 3為例)
```json
"stage3": {
  "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
  "lowerBounds": [0.5, 0.05, -0.5, 0.05, 0.05, 0.05, 0.01, 0.0],
  "upperBounds": [4.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0, 0.75],
  "fixedValues": {"bm": 0.86}
}
```

### 邊界設定建議

**正常範圍**（推薦）:
```json
"lowerBounds": [0.5, 0.05, -0.5, 0.05, 0.05, 0.05, 0.01, 0.0]
"upperBounds": [4.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0, 0.75]
```

**寬鬆範圍**（自動邊界調整不常用）:
```json
"lowerBounds": [0.5, 0.001, -2.0, 0.001, 0.001, 0.001, 0.0001, 0.0]
"upperBounds": [4.0, 2.0, 3.0, 2.0, 2.0, 3.0, 2.0, 0.75]
```

---

## 自動邊界調整

### 觸發機制

程式檢查參數是否接近邊界：

**相對容差**（常規參數）:
```python
distance_ratio = |param_value - bound| / (upper_bound - lower_bound)
if distance_ratio < tolerance:  # 預設0.01 (1%)
    觸發調整
```

**絕對容差**（小值參數，如Sa, St）:
```python
if lower_bound < 0.01:
    absolute_distance = |param_value - bound|
    if absolute_distance < max(bound * 0.1, 1e-6):
        觸發調整
```

### 調整規則

**下界放寬**:
```python
new_lower = current_lower / expansion_factor

# 物理約束
if 參數為正值型 (b, s):
    new_lower = max(new_lower, 1e-6)
elif 參數為u:
    new_lower = max(new_lower, 0.0)
# a參數可為負
```

**上界放寬**:
```python
new_upper = current_upper * expansion_factor

# 物理約束
if 參數為u:
    new_upper = min(new_upper, 1.0)
```

### 停止條件

**1. NLL收斂**（最理想）:
```
第1輪: NLL = -344.831
第2輪: NLL = -344.735
改善 = 0.096 < 0.1 → 停止
```

**2. 無邊界問題**:
```
第1輪: 所有參數距離邊界 > 1%
→ 直接停止，無需調整
```

**3. 最大輪數**:
```
已達3輪，即使仍觸碰邊界
→ 強制停止，建議人工檢查
```

### 輸出解讀

```
================================================================================
📍 第 1 輪優化
================================================================================
✅ 本輪優化完成
   最終 NLL = -344.830686

🔍 檢查 Stage3 參數是否觸碰邊界...
   ⚠️  Sa=0.001000 接近下界 0.001000 (絕對距離=0.000000e+00)

💡 建議調整以下邊界 (擴展倍數=2.0x)：
   Sa 下界: 0.001000 → 0.000500
   💾 已備份配置到: ../config.json.round1.bak
   ✅ 已更新配置文件: ../config.json

🔄 檢測到邊界問題，準備第 2 輪優化...

================================================================================
📍 第 2 輪優化
================================================================================
✅ 本輪優化完成
   最終 NLL = -344.735410
   NLL改善: 0.095276

================================================================================
✅ NLL已收斂！改善量(0.095276) < 閾值(0.1)
   第1輪: NLL = -344.830686
   第2輪: NLL = -344.735410
   停止進一步調整。
================================================================================
```

---

## 結果解讀

### PPE結果

```csv
a,d,s,ln_likelihood
295.304401,18.433704,0.003417,-358.80
```

- `a`: 背景地震率（事件/年）
- `d`: 空間衰減參數（km）
- `s`: 震級衰減參數
- `ln_likelihood`: 對數似然

### 餘震結果

```csv
v,k,ln_likelihood
1.124883,0.073194,-143212.346
```

- `v`: 餘震觸發強度
- `k`: PPE與餘震比例參數

### EEPAS結果

```csv
am,bm,Sm,at,bt,St,ba,Sa,u,ln_likelihood
1.427,0.88,0.545,0.140,0.886,0.008,1.922,0.001,0.448,-292.153
```

**參數意義**:
- `am, at, ba`: 震級-頻率關係（a參數）
- `bm, bt`: G-R關係斜率（固定）
- `Sm, St, Sa`: 不確定性（標準差）
- `u`: EEPAS與PPE混合比例

**物理約束檢查**:
- ✅ `bm, bt, ba, Sm, St, Sa > 0`
- ✅ `u ∈ [0, 1]`
- ✅ `am, at` 可為負

---

## 論文驗證工作流程

### 義大利模式 - 論文完全一致配置

此工作流程使用 `config_italy_paper_1round_full.json`，完全匹配 ggad123.pdf 論文方法：

**關鍵設置**:
- 學習期：1990-2012
- 預測期：2012-2022
- mT = 5.0（目標震級閾值）
- 使用 mT 作為 ppe_ref_mag 和 target_mag
- 單輪優化（`--max-rounds 1`）
- 三階段參數優化

**完整流程**:

```bash
# Step 1: PPE Learning (使用 mT anchor)
python3 ppe_learning.py --config config_italy_paper_1round_full.json

# Step 2: Aftershock Parameters (兩個 mag 參數都用 mT)
python3 fit_aftershock_params.py --config config_italy_paper_1round_full.json --ppe-ref-mag mT --target-mag mT

# Step 3: EEPAS Learning (三階段 + 單輪優化)
python3 eepas_learning_auto_boundary.py --config config_italy_paper_1round_full.json --three-stage --ppe-ref-mag mT --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py --config config_italy_paper_1round_full.json --ppe-ref-mag mT

# Step 5: EEPAS Forecast (快速模式)
python3 eepas_make_forecast.py --config config_italy_paper_1round_full.json --fast --ppe-ref-mag mT
```

**驗證結果** (in `results_italy_paper_1round_full/`):

| 模組 | 參數 | 值 |
|------|------|-----|
| PPE | a | 0.616 |
| | d | 29.64 km |
| | s | ≈ 0 |
| Aftershock | v | 0.577 |
| | k | 0.205 |
| EEPAS | am | 1.234 |
| | Sm | 0.242 |
| | at | 2.589 |
| | bt | 0.349 |
| | St | 0.150 |
| | ba | 0.504 |
| | Sa | 1.000 |
| | u | 0.167 |
| | NLL | -495.41 |

**論文一致性驗證**:
- ✅ PPE 空間核函數：h₀(x,y) = Σ[a·(mₖ-mT)/(π(d²+r²)) + s]
- ✅ PPE 震級分布：g₀(m) = β·exp(-β(m-mT))
- ✅ EEPAS 空間分布：2D 高斯（使用 erf 函數積分）
- ✅ EEPAS 震級分布：截斷高斯（考慮 m0 截斷效應）
- ✅ EEPAS 時間分布：對數正態分布

---

## 故障排除

### 問題1: 找不到PPE/餘震結果

**錯誤訊息**:
```
FileNotFoundError: results/Fitted_par_PPE_2002_2016.csv
```

**原因**: 未執行前置步驟

**解決**:
```bash
# 確保依序執行
python3 ppe_learning.py --config ../config.json
python3 fit_aftershock_params.py --config ../config.json
python3 eepas_learning_auto_boundary.py --config ../config.json
```

---

### 問題2: NLL卡在較差值

**症狀**: EEPAS NLL = -299，預期 -292

**可能原因**:
1. 邊界過緊
2. 初始值不佳
3. 優化未收斂

**解決**:
```bash
# 使用自動邊界調整
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 5 \
    --tolerance 0.01
```

---

### 問題3: 路徑錯誤

**錯誤**:
```
找不到 results/xxx.csv
```

**原因**: 未從正確目錄執行

**解決**:
```bash
# 必須從python_src執行
cd /home/math/EEPAS_Taiwan-main/src/python_src
python3 xxx.py --config ../config.json
```

---

### 問題4: Numba編譯失敗

**錯誤**:
```
numba.core.errors.TypingError: ...
```

**解決**:
```bash
# 更新numba
pip install --upgrade numba

# 清除numba緩存
rm -rf ~/.numba_cache
```

---

## 高級用法

### 自定義m0

```bash
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --m0 2.05
# 會覆蓋配置文件中的m0值
```

### 調整收斂靈敏度

```bash
# 更嚴格（更早停止）
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --nll-threshold 0.05

# 更寬鬆（可能多跑幾輪）
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --nll-threshold 0.2
```

### 比較結果

```bash
python3 utils/compare_results.py \
    --matlab ../results_matlab/Fitted_par_EEPAS_2002_2016.csv \
    --python results_decluster_python/Fitted_par_EEPAS_2002_2016.csv
```

### 分析邊界調整歷史

```bash
python3 utils/analyze_auto_boundary_result.py test_log.log
```

---

## 參考文獻

詳見項目其他文檔：

- `README.md`: 快速開始

---

**最後更新**: 2025-10-30

---

## 優化器比較研究

詳見 `OPTIMIZER_COMPARISON_REPORT.md` 以了解各優化器的性能比較和使用建議。

### 主要發現

- ✅ **fminsearchcon (Nelder-Mead) 最穩健**（在所有配置上都能找到高質量解）
- ⚡ **梯度法速度快但不穩定**（50% 成功率，容易陷入局部最優）
- ❌ **Basin-Hopping 和大量 Multistart (>10) 對此問題無效**
- 💡 **推薦策略**：並行運行 fminsearchcon 和 L-BFGS-B + Multistart，取較好者
