# Claude Code 開發注意事項

本文件記錄 EEPAS 項目的重要開發注意事項和規範，供 Claude Code 參考。

## 🌐 語言規範

**⚠️ 重要：請永遠使用繁體中文與用戶溝通！**

- 所有回覆、說明、註解都使用繁體中文
- 變數名稱、函數名稱可以使用英文
- 文檔、commit message 使用繁體中文

## 🚨 重要規則

### ⚠️ 修改核心程式碼前必須確認
- **修改任何 .py 檔案之前，必須先和用戶確認**
- **❌ 絕對不要在重構時隨意修改函數的預設值**
- **❌ 絕對不要自作聰明修改任何預設值或參數**
- 不要自作主張修復看起來像 "錯誤" 的程式碼，它們可能是預期的行為
- 如果發現程式碼問題，先詢問用戶是否需要修改
- EEPAS Learning 使用 `eepas_learning_auto_boundary.py` 的 **auto_boundary 功能**

### 🔴 重構時的關鍵原則
- **保持所有函數的預設值不變**（除非用戶明確要求修改）
- **保持所有參數的預設行為不變**
- **只重構結構，不改變行為**
- 範例：`multi_start=True` 必須保持為 `True`，不能改成 `False`

### 🚫 絕對禁止的破壞性指令

**❌ 永遠不要使用這些會影響大量檔案的指令：**

1. **批量 sed 替換所有 Python 檔案**
   ```bash
   # ❌ 極度危險！會破壞函數名稱、import 語句
   find . -name "*.py" -type f -exec sed -i 's/old/new/g' {} \;
   ```
   - 問題：會錯誤替換函數名稱、變數名稱、import 語句
   - 後果：破壞程式邏輯，導致執行錯誤
   - **正確做法**：逐一檢查需要修改的檔案，使用 Edit 工具精確修改

2. **批量 git restore**
   ```bash
   # ❌ 危險！會覆蓋所有未提交的修改
   git restore '*.py'
   git restore .
   ```
   - 問題：會恢復所有 Python 檔案，包括正確的修改
   - 後果：丟失用戶的工作成果
   - **正確做法**：只 restore 確定需要恢復的單一檔案
     ```bash
     git restore utils/catalog_processor.py
     ```

3. **文字替換的正確原則**
   - ✅ **只修改文檔和註解中的術語大小寫**（如 seismostats → SeismoStats）
   - ❌ **絕不修改程式碼中的函數名稱、變數名稱、import 語句**
   - ✅ **使用 Edit 工具逐一修改**，確保只改 docstring 描述
   - ❌ **絕不使用 find + sed 批量替換程式碼**

4. **修改前必須確認的清單**
   - [ ] 這個修改只影響註解/文檔嗎？
   - [ ] 這會改到函數名稱或 import 語句嗎？
   - [ ] 我可以用 Edit 工具精確修改嗎？
   - [ ] 我是否檢查了所有受影響的檔案？
   - [ ] 修改後是否會破壞現有功能？

### 🔍 安全的修改流程

**當需要修改多個檔案中的相同內容時：**

1. **先搜尋確認範圍**
   ```bash
   grep -rn "要修改的內容" --include="*.py"
   ```

2. **分析每個結果**
   - 是否在註解/docstring 中？（可以改）
   - 是否在函數名稱中？（不能改）
   - 是否在 import 語句中？（不能改）
   - 是否在變數名稱中？（不能改）

3. **使用 Edit 工具逐一修改**
   - 只修改確定安全的部分
   - 每次修改提供充足的上下文
   - 修改後驗證語法正確性

4. **修改後必須驗證**
   ```bash
   # 驗證 Python 語法
   python3 -c "import module_name"

   # 檢查函數是否存在
   python3 -c "from utils.catalog_processor import CatalogProcessor; print(hasattr(CatalogProcessor, 'function_name'))"
   ```

### 🔴 驗證與比較時的重要原則

**❌ 絕對禁止覆蓋現有結果目錄進行比較**

當需要驗證重構或比較結果時：

1. **使用不同的結果目錄**
   ```bash
   # ❌ 錯誤：直接覆蓋原結果
   python3 ppe_learning.py --config config.json  # 會寫入 results/

   # ✅ 正確：使用新的結果目錄
   # 修改 config 的 resultsDir 為 "results_refactor_test"
   python3 ppe_learning.py --config config_refactor.json
   ```

2. **建立專用測試配置檔案**
   - 複製現有配置檔案（如 `config_italy.json`）
   - 重新命名為測試用（如 `config_italy_refactor_test.json`）
   - **修改 `resultsDir` 欄位**指向新目錄（如 `results_italy_refactor_test`）
   - 其他參數保持完全一致

3. **比較結果的正確流程**
   ```bash
   # Step 1: 確認原結果目錄存在且不被修改
   ls -lh results_italy/

   # Step 2: 使用新配置執行測試
   python3 ppe_learning.py --config config_italy_refactor_test.json

   # Step 3: 比較兩個目錄的結果
   diff results_italy/Fitted_par_PPE_1990_2012.csv \
        results_italy_refactor_test/Fitted_par_PPE_1990_2012.csv

   # Step 4: 使用 Python 比較 .mat 檔案
   python3 compare_results.py results_italy/ results_italy_refactor_test/
   ```

4. **重要的結果目錄命名規則**
   - 原始結果：`results_*` (保持不變)
   - 重構測試：`results_*_refactor_test`
   - 精確模式測試：`results_*_accurate`
   - 快速模式測試：`results_*_fast`
   - 臨時測試：`results_*_temp` (可刪除)

5. **如果不小心覆蓋了結果**
   - 立即停止所有運行中的任務
   - 檢查 git 狀態：`git status`
   - 如果結果在 git 中：`git restore <file>`
   - 如果不在 git 中：查看日誌檔案 (*.log) 中的數值
   - 必要時重新執行原始配置生成結果

6. **記錄比較結果**
   - 將比較結果寫入 markdown 報告
   - 記錄關鍵參數的相對差異
   - 保留兩個版本的完整日誌檔案

### 檔案管理

#### ❌ 絕對禁止刪除的檔案類型
- **所有 config*.json 檔案** - 包括測試用的配置檔案（如 config_italy_new.json）
- **主要結果目錄** - results/, results_decluster/, results_include921/, results_m205_python/, results_italy/, results_italy_3stage/
- **核心程式碼** - 10 個主要 .py 檔案
- **主要文檔** - README.md, CHANGELOG.md, USAGE.md
- **數據檔案** - data/ 目錄下的所有 .mat 檔案

#### ⚠️ 需要確認才能刪除
- 測試腳本 (test_*.py)
- 日誌檔案 (.log, .bak)
- 備份檔案 (*_backup.py, *_original.py)
- 臨時配置 (*_temp.json)

#### ✅ 可以安全刪除
- Zone.Identifier 檔案
- __pycache__/ 目錄
- .pyc 檔案

### Git 操作

#### Commit 前檢查清單
1. ✅ 確認沒有誤刪用戶的測試配置檔案
2. ✅ 移除不需要提交的臨時檔案（Zone.Identifier 等）
3. ✅ 檢查是否有未歸檔的測試日誌
4. ✅ 驗證程式碼更新後仍可正常運作

#### Commit 訊息格式
```
簡短描述（中文，50字內）

## 變更摘要
（詳細說明）

### 類別
- 具體變更項目

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 📐 架構與設計原則

### 區域定義（根據 ggad123.pdf）

#### Testing Region (R)
- **用途**: 目標事件求和範圍、積分範圍
- **配置欄位**: `testingRegionFile`
- **檔案格式**: CELLE grid（網格）
- **數學定義**: NLL = -[Σ_{i:(xi,yi)∈R} log λ(...) - ∫∫∫∫_R λ(...) dt dm dx dy]

#### Neighborhood Region
- **用途**: 源事件來源區域（避免邊界效應）
- **配置欄位**: `neighborhoodRegionFile`
- **檔案格式**:
  - Taiwan: CELLE grid（與 Testing Region 相同）
  - Italy: CPTI15 polygon（包含 Testing Region 及周邊區域）

### 配置欄位命名規範

#### 當前命名（v1.2.0+）
```json
"inputFiles": {
  "catalogFile": "地震目錄檔案.mat",
  "neighborhoodRegionFile": "Neighborhood Region 檔案.mat",
  "testingRegionFile": "Testing Region 檔案.mat"
}
```

#### 舊命名（向後相容）
- `horusFile` → 自動轉換為 `catalogFile`
- `cptiFile` → 自動轉換為 `neighborhoodRegionFile`
- `celleFile` → 自動轉換為 `testingRegionFile`

### 模式差異

#### Taiwan 模式
- Testing Region = Neighborhood Region (相同檔案)
- 兩者都是 grid 格式
- 24 個網格區域

#### Italy 模式
- Testing Region ⊂ Neighborhood Region
- Testing Region: 177 個網格 (CELLE_ter.mat)
- Neighborhood Region: Polygon (CPTI15.mat)
- 需要考慮邊界效應

## 🔧 開發工作流程

### 正確的執行指令（重要！）

#### EEPAS 完整五步流程

**🚨 重要提醒：所有步驟都要啟用快速模式！**

##### 標準流程（快速模式 - 日常使用）
```bash
# Step 1: PPE Learning（快速模式：網格積分）
python3 ppe_learning.py --config config.json --grid-res 30

# Step 2: Aftershock Parameters Fitting（快速模式：梯形法）
python3 fit_aftershock_params.py --config config.json --fast --ppe-ref-mag mT --target-mag mT

# Step 3: EEPAS Learning（快速模式 + 三階段優化）
python3 eepas_learning_auto_boundary.py --config config.json --three-stage --fast --ppe-ref-mag mT --max-rounds 1

# Step 4: PPE Forecast（快速模式）
python3 ppe_make_forecast.py --config config.json --fast --ppe-ref-mag mT

# Step 5: EEPAS Forecast（快速模式）
python3 eepas_make_forecast.py --config config.json --fast --ppe-ref-mag mT
```

##### 精確模式（僅用於最終驗證）
```bash
# Step 1: PPE Learning（精確模式：dblquad積分）
python3 ppe_learning.py --config config.json --accurate

# Step 2: Aftershock Parameters Fitting（精確模式）
python3 fit_aftershock_params.py --config config.json --accurate --ppe-ref-mag mT --target-mag mT

# Step 3: EEPAS Learning（精確模式 + 三階段）
python3 eepas_learning_auto_boundary.py --config config.json --three-stage --accurate-ppe --ppe-ref-mag mT --max-rounds 1

# Step 4: PPE Forecast（精確模式）
python3 ppe_make_forecast.py --config config.json --accurate --ppe-ref-mag mT

# Step 5: EEPAS Forecast（精確模式）
python3 eepas_make_forecast.py --config config.json --accurate --ppe-ref-mag mT
```

#### ⚡ 快速模式（--fast）使用指南

**重要：快速模式在不同階段的效能表現差異很大！**

| 階段 | 快速模式效能 | 建議 |
|------|------------|------|
| **Learning** | ❌ 慢 3x（JIT 編譯成本無法攤銷） | **不要使用 --fast** |
| **Forecast** | ✅ 快 4.7x（2,200 次調用攤銷成本） | **強烈建議使用 --fast** |

**使用範例：**
```bash
# Learning: 不要使用 --fast（反而更慢）
python3 eepas_learning_auto_boundary.py --config config.json --three-stage

# Forecast: 強烈建議使用 --fast（快 4.7 倍）
python3 eepas_make_forecast.py --config config.json --fast
```

**詳細說明請參考：** `FAST_MODE_GUIDE.md`

#### ⚠️ 重要說明 - EEPAS Learning 的三個選項

EEPAS 參數學習有三個不同的程式可以使用：

1. **`eepas_learning_auto_boundary.py`** ✅ **強烈推薦**
   - 自動邊界調整包裝器
   - 預設：單階段 + Multistart + SLSQP 優化器
   - 自動檢測參數觸碰邊界並調整
   - 最穩健，最容易收斂
   ```bash
   # 預設配置（推薦）
   python3 eepas_learning_auto_boundary.py --config config.json

   # 三階段優化
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage
   ```

2. **`optimize_eepas_parameters.py`** ⚙️ **進階使用**
   - 三階段優化核心模組
   - 提供更多底層控制選項
   - 需要手動處理邊界問題
   ```bash
   python3 optimize_eepas_parameters.py --config config.json
   ```

3. **`eepas_learning.py`** ⚠️ **不推薦**
   - 基本學習版本
   - 缺少自動邊界調整
   - 可能無法正常執行（有 bug）
   - **不要使用這個！**

#### 📝 參數選項說明

`eepas_learning_auto_boundary.py` 支援的參數：
- `--config` : 配置檔案路徑
- `--three-stage` : 使用三階段優化（預設：單階段）
- `--no-multistart` : 禁用多起始點搜索
- `--optimizer` : 指定優化器（SLSQP, L-BFGS-B, fminsearchcon）
- `--m0` : 完整度震級（加速用）
- `--max-rounds` : 邊界調整最大輪數（預設：3，建議遇到邊界問題時設為 5）

**🔴 重要：自動邊界調整不會修改原始 config 檔案**

從 v0.4.0 開始，自動邊界調整會：
1. **第一輪**：使用原始 config 檔案（如 `config_italy.json`）
2. **如需調整**：創建新的 config 檔案（如 `config_italy_autoadjusted_round1.json`）
3. **後續輪次**：使用新的 config 檔案
4. **原始 config 保持不變**：可以重複執行實驗

**範例**：
```bash
# 原始 config: config_italy.json
python3 eepas_learning_auto_boundary.py --config config_italy.json --three-stage --max-rounds 3

# 如果 Round 1 觸碰邊界：
#   → 創建 config_italy_autoadjusted_round1.json（調整後的邊界）
#   → Round 2 使用 config_italy_autoadjusted_round1.json
#   → 如再次觸碰邊界，創建 config_italy_autoadjusted_round2.json
#   → 原始 config_italy.json 保持不變！
```

**優點**：
- ✅ 原始 config 不會被修改
- ✅ 可以隨時重新執行實驗
- ✅ 調整歷史完整記錄（每個 round 都有獨立的 config）
- ✅ 方便比較不同 round 的邊界設定

#### ⏱️ 執行時間預估

- **PPE Learning**: ~10-30 秒
- **Aftershock Fitting**: ~30-60 秒
- **EEPAS Learning**:
  - 單階段：10-30 分鐘
  - 三階段：30-60 分鐘（義大利模式可能更久）
  - ⚠️ **重要**：執行 EEPAS Learning 時**不要設置 timeout**！
- **PPE Forecast**: ~5-15 分鐘
- **EEPAS Forecast (--fast)**: ~1-5 分鐘

### 1. 配置檔案變更
```bash
# 更新配置後務必測試
python3 -c "
from utils.data_loader import DataLoader
cfg = DataLoader.load_config('config.json')
print('Config loaded successfully')
"
```

### 2. 程式碼修改
- ⛔ **不要修改核心 .py 檔案**
- 確保向後相容性
- 更新相關文檔和註解

### 3. 提交前驗證
```bash
# 檢查未追蹤檔案
git status

# 測試 Taiwan 模式
python3 -c "from utils.data_loader import DataLoader; DataLoader.load_catalogs('config.json')"

# 測試 Italy 模式
python3 -c "from utils.data_loader import DataLoader; DataLoader.load_catalogs('config_italy.json')"
```

## 📂 目錄結構規範

### 主要結果（絕不刪除）
```
results/                  # Taiwan 標準
results_decluster/        # Taiwan 去叢集
results_include921/       # Taiwan 包含921
results_m205_python/      # Taiwan m0=2.05
results_italy/            # Italy 標準
results_italy_3stage/     # Italy 三階段
```

### 測試與開發（可歸檔）
```
archive_test_files/
├── test_scripts/         # 測試腳本
├── configs/              # 測試配置
├── logs/                 # 測試日誌
└── comparison_results/   # 對比結果
```

## 📝 文檔維護

### 需要同步更新的文檔
1. **README.md** - 主要文檔
2. **CHANGELOG.md** - 版本記錄
3. **USAGE.md** - 使用指南
4. **docs/README.md** - 子目錄說明

### 文檔更新時機
- 新增功能時
- 配置格式變更時
- API 介面修改時
- 重大 bug 修復時

## 🐛 常見錯誤與解決

### 1. 配置檔案載入失敗
**症狀**: FileNotFoundError for config file
**檢查**:
- 檔案路徑是否正確
- 檔案是否被誤刪
- 欄位名稱是否正確（新舊命名）

### 2. 數據檔案載入失敗
**症狀**: FileNotFoundError for .mat file
**檢查**:
- data/ 目錄是否完整
- 配置中的檔案名稱是否正確
- Testing/Neighborhood Region 檔案是否存在

### 3. 區域類型識別錯誤
**症狀**: 義大利模式被識別為台灣模式
**檢查**:
- neighborhoodRegionFile 是否指向正確檔案
- 檔案內容格式是否正確（grid vs polygon）

## 🔄 版本歷史

### v1.2.0 (2025-10-26)
- ✅ 義大利模式完整支持
- ✅ 配置欄位重新命名（更具描述性）
- ✅ 代碼整理（測試檔案歸檔）
- ✅ 文檔更新

### v1.1.0 (2025-10-19)
- ✅ 優化器擴展支持
- ✅ 性能優化（Numba JIT）

### v1.0.0 (2025-10-15)
- ✅ 初始 Python 版本發布
- ✅ 與 MATLAB 版本 100% 一致

## 📞 問題排查

遇到問題時：
1. 檢查此文件的相關規範
2. 查看 docs/ 目錄的詳細文檔
3. 檢查 git log 了解最近變更
4. 參考 CHANGELOG.md 版本歷史

---

**最後更新**: 2025-10-30
**維護者**: EEPAS Development Team
**重要提醒**: 此文件包含關鍵開發規範，請 Claude Code 在執行任何操作前參考！

## 🎯 v1.2.0 論文驗證完成

### 驗證成果
- ✅ PPE 和 EEPAS 預測公式與 ggad123.pdf 完全一致
- ✅ mT anchor 支持（`--ppe-ref-mag mT --target-mag mT`）
- ✅ 單輪優化模式（`--max-rounds 1`）匹配論文方法
- ✅ 完整驗證結果在 `results_italy_paper_1round_full/`

### 關鍵配置
- 配置文件：`config_italy_paper_1round_full.json`
- 學習期：1990-2012
- 預測期：2012-2022
- mT = 5.0（目標震級閾值）

## 🔍 重構驗證與 Lambda 總和檢查

### 重構驗證原則

**重要**：當進行數值積分重構或其他核心算法修改時，必須驗證結果的正確性。

#### 1. Learning 階段的 Lambda 積分驗證

在 EEPAS Learning 過程中，會計算 PPE 正規化積分 Λ_PPE：

```python
# 在 optimize_eepas_parameters.py 中
integral_PPE = calculate_ppe_normalization(...)  # PPE 正規化積分
```

**理論驗證**：
- **Λ_PPE ≈ N**（目標事件數量）
- 對於義大利模式：N = 27（學習期間 1990-2012 的 M≥5.0 事件）
- 快速模式：Λ_PPE = 27.000197 ✅
- 精確模式：Λ_PPE = 26.999756 ✅

這驗證了 PPE 空間積分的正確性（無論是快速的梯形法還是精確的 dblquad）。

#### 2. Forecast 階段的 Lambda 總和驗證

**⚠️ 關鍵注意事項**：
- Forecast 結果矩陣的**第一列是索引**，需要排除！
- 只計算第 2 列到最後一列（實際的網格預測值）

**驗證方法**：

```python
import scipy.io as sio
import numpy as np

# 讀取 Forecast 結果
mat_ppe = sio.loadmat('results_*/PREVISIONI_3m_PPE_*.mat')
ppe_forecast = mat_ppe['PREVISIONI_3m']

# ⚠️ 排除第一列索引
ppe_lambda = np.sum(ppe_forecast[:, 1:])

mat_eepas = sio.loadmat('results_*/PREVISIONI_3m_EEPAS_*.mat')
eepas_forecast = mat_eepas['PREVISIONI_3m_less']
eepas_lambda = np.sum(eepas_forecast[:, 1:])

print(f'PPE Lambda 總和: {ppe_lambda:.6f}')
print(f'EEPAS Lambda 總和: {eepas_lambda:.6f}')
```

**快速模式驗證結果**（義大利，1990-2012）：
- PPE Lambda 總和：26.93
- EEPAS Lambda 總和：28.21
- 目標事件數量：27
- **結論**：✅ 兩者都接近 27，驗證通過！

**意義**：
- 這驗證了 Forecast 階段的數值積分正確
- PPE 和 EEPAS 的預測率總和應該接近實際觀測到的事件數量
- 這是 Poisson 點過程模型的基本性質

#### 3. 驗證工具

使用 `analysis/` 目錄下的腳本進行驗證：

```bash
# 進入工作目錄
cd /home/math/EEPAS_Taiwan-main/src/python_src

# 驗證 Forecast Lambda 總和
python3 analysis/analyze_forecast_lambda.py

# 驗證 Learning 階段的積分（從日誌提取）
python3 analysis/calculate_lambda_sum.py
```

這些工具會：
- 自動排除索引列
- 比較 PPE 和 EEPAS 的結果
- 驗證是否接近理論值
- 報告相對差異百分比
