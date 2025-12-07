# 自定義優化階段系統設計文檔

## 📋 需求分析

### 使用者需求
1. ✅ **自定義階段數量** - 不限於 1 或 3 階段，可以是 2、4、5 等任意階段
2. ✅ **每階段參數控制** - 靈活指定每階段要優化哪些參數、固定哪些參數
3. ✅ **參數初始值設定** - 每階段可設定不同的初始值
4. ✅ **參數邊界設定** - 每階段可設定不同的上下界
5. ⚠️ **不支援 multistart** - 自定義模式下不支援，但保留 single/three-stage 的 multistart 功能

### 向後相容需求
1. ✅ **保留 single-stage 模式** - 完整保留現有功能，包括 multistart
2. ✅ **保留 three-stage 模式** - 完整保留現有功能，包括 multistart
3. ✅ **配置檔案相容** - 現有 config*.json 檔案無需修改即可正常運作

---

## 🏗️ 系統架構設計

### 1. 配置檔案格式

#### 方案 A：新增 `customStages` 欄位（推薦）

**優點**：
- ✅ 完全向後相容（舊配置檔案不受影響）
- ✅ 職責分離清楚（標準模式 vs 自定義模式）
- ✅ 易於驗證和理解

**範例配置**：

```json
{
  "optimization": {
    "stage1": {...},  // 保留給 three-stage 使用
    "stage2": {...},
    "stage3": {...},

    "customStages": {
      "enable": true,
      "stages": [
        {
          "name": "Magnitude First",
          "parameters": ["am", "bm", "Sm"],
          "initialValues": [1.5, 0.86, 0.3],
          "lowerBounds": [1.0, 0.7, 0.2],
          "upperBounds": [2.0, 1.0, 0.5],
          "fixedValues": {
            "at": 2.0,
            "bt": 0.3,
            "St": 0.15,
            "ba": 0.3,
            "Sa": 2.0,
            "u": 0.2
          }
        },
        {
          "name": "Temporal Scaling",
          "parameters": ["at", "bt", "St"],
          "initialValues": ["am_from_stage_1", 0.4, 0.2],
          "lowerBounds": [1.0, 0.3, 0.15],
          "upperBounds": [3.0, 0.6, 0.5],
          "fixedValues": {
            "am": "from_stage_1",
            "bm": "from_stage_1",
            "Sm": "from_stage_1",
            "ba": 0.3,
            "Sa": 2.0,
            "u": 0.2
          }
        },
        {
          "name": "Spatial and Mu",
          "parameters": ["ba", "Sa", "u"],
          "initialValues": [0.35, "Sa_from_stage_1", 0.2],
          "lowerBounds": [0.2, 1.0, 0.0],
          "upperBounds": [0.6, 30.0, 1.0],
          "fixedValues": {
            "am": "from_stage_2",
            "bm": "from_stage_1",
            "Sm": "from_stage_1",
            "at": "from_stage_2",
            "bt": "from_stage_2",
            "St": "from_stage_2"
          }
        },
        {
          "name": "Joint Refinement",
          "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
          "initialValues": "from_previous_stages",
          "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
          "upperBounds": [2.0, 0.5, 3.0, 0.6, 0.5, 0.6, 30.0, 1.0],
          "fixedValues": {
            "bm": "from_stage_1"
          }
        }
      ]
    }
  }
}
```

### 2. 參數繼承機制

**核心原則**：每個階段都會**自動繼承**前一階段優化的所有參數值

#### 現有 Three-Stage 行為（我們要保持一致）：

```python
# Stage 1: 優化 [am, at, Sa, u]
# 固定：bm=1, Sm=0.2, bt=0.3, St=0.15, ba=0.3
result_stage1 = {am: 1.23, at: 2.59, Sa: 1.00, u: 0.17}

# Stage 2: 優化 [Sm, bt, St, ba, u]
# 固定：am=1.23 (來自Stage1), at=2.59 (來自Stage1), Sa=1.00 (來自Stage1), bm=1
# → Stage 2 自動使用 Stage 1 的結果作為固定值
result_stage2 = {Sm: 0.24, bt: 0.35, St: 0.15, ba: 0.50, u: 0.17}

# Stage 3: 優化全部 8 個參數
# 初始值：使用 Stage1 和 Stage2 的結果
x0_stage3 = [am=1.23, Sm=0.24, at=2.59, bt=0.35, St=0.15, ba=0.50, Sa=1.00, u=0.17]
```

#### 自定義階段的行為（與上述一致）：

**配置語法**：
- **不需要**指定 `"from_stage_X"`，參數會**自動繼承**！
- `fixedValues` 只需要指定**當前階段不優化**的參數
- `initialValues` 可以用數值（覆蓋繼承值）或省略（使用繼承值）

**範例配置**：

```json
{
  "stages": [
    {
      "name": "Stage 1: Magnitude",
      "parameters": ["am", "bm", "Sm"],
      "initialValues": [1.5, 0.86, 0.3],  // 第一階段必須提供初始值
      "fixedValues": {
        "at": 2.0, "bt": 0.3, "St": 0.15,  // 這階段不優化的參數
        "ba": 0.3, "Sa": 2.0, "u": 0.2
      }
    },
    {
      "name": "Stage 2: Temporal",
      "parameters": ["at", "bt", "St"],
      "initialValues": null,  // null 表示使用 Stage 1 的結果
      "fixedValues": {
        // am, bm, Sm 自動使用 Stage 1 的優化結果（不需要寫！）
        "ba": 0.3, "Sa": 2.0, "u": 0.2  // 這階段不優化的參數
      }
    },
    {
      "name": "Stage 3: Joint",
      "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "initialValues": null,  // 使用前階段的所有結果作為初始值
      "fixedValues": {
        "bm": 0.86  // bm 始終固定
      }
    }
  ]
}
```

### 3. 程式執行模式

#### 模式判斷邏輯

```python
def determine_optimization_mode(config, args):
    """
    決定優化模式

    優先順序：
    1. 檢查 config 是否有 customStages.enable = true
    2. 檢查命令列參數 --three-stage
    3. 預設使用 single-stage
    """
    if config.get('optimization', {}).get('customStages', {}).get('enable', False):
        return 'custom'
    elif args.three_stage:
        return 'three_stage'
    else:
        return 'single_stage'
```

#### 命令列參數設計

```bash
# 自動模式（根據 config 判斷）
python3 eepas_learning_auto_boundary.py --config config.json

# 強制使用 single-stage（忽略 customStages）
python3 eepas_learning_auto_boundary.py --config config.json --force-single-stage

# 強制使用 three-stage（忽略 customStages）
python3 eepas_learning_auto_boundary.py --config config.json --three-stage

# 自定義模式（必須在 config 中啟用）
python3 eepas_learning_auto_boundary.py --config config_custom.json
```

---

## 🔧 實作計劃

### Phase 1: 核心功能實作

#### 1.1 新增配置解析函數

檔案：`utils/data_loader.py`

```python
def load_custom_stages(config_file):
    """
    載入自定義階段配置

    Returns:
        list: 階段定義列表，每個元素包含：
            - name: str
            - parameters: list[str]
            - initialValues: list or str
            - lowerBounds: list[float]
            - upperBounds: list[float]
            - fixedValues: dict
    """
    pass

def validate_custom_stages(stages):
    """
    驗證自定義階段配置的正確性

    檢查：
    1. 參數名稱是否合法（必須是 9 個 EEPAS 參數之一）
    2. 邊界數量是否與參數數量一致
    3. 初始值數量是否與參數數量一致
    4. 固定參數 + 優化參數 = 9 個
    5. from_stage_X 引用是否有效
    """
    pass
```

#### 1.2 新增自定義優化引擎

檔案：`optimize_eepas_parameters.py`

```python
def optimize_custom_stages(
    mj, xj, tj, yj, xi, yi, mi, ti,
    me, xe, te, ye, W, EW, B, T1, T2, m0,
    CELLE, params, config_file='config.json',
    optimizer='SLSQP',
    region_manager=None, use_fast_mode=False, magnitude_samples=20
):
    """
    自定義階段優化

    特性：
    - 支援任意階段數量
    - 每階段可自定義參數
    - 不支援 multistart（避免複雜度）
    - 使用單一優化器（預設 SLSQP）
    """
    pass
```

### Phase 2: 自動邊界調整整合

檔案：`eepas_learning_auto_boundary.py`

```python
def eepas_with_auto_boundary(..., use_custom_stages=False):
    """
    擴展現有函數支援自定義模式

    新增參數：
    - use_custom_stages: bool - 是否使用自定義階段（從 config 讀取）
    """
    pass
```

### Phase 3: 測試與驗證

#### 3.1 向後相容測試

```bash
# 測試 single-stage 保持不變
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json

# 測試 three-stage 保持不變
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json --three-stage
```

#### 3.2 新功能測試

```bash
# 測試 2 階段優化
python3 eepas_learning_auto_boundary.py --config config_custom_2stage.json

# 測試 4 階段優化
python3 eepas_learning_auto_boundary.py --config config_custom_4stage.json

# 測試 Magnitude-First 策略
python3 eepas_learning_auto_boundary.py --config config_magnitude_first.json
```

---

## 📊 測試案例設計

### 測試案例 1：兩階段優化（Magnitude First）

**策略**：先優化震級相關參數，再聯合優化

```json
{
  "customStages": {
    "enable": true,
    "stages": [
      {
        "name": "Stage 1: Magnitude Scaling",
        "parameters": ["am", "bm", "Sm"],
        "initialValues": [1.5, 0.86, 0.3],
        "lowerBounds": [1.0, 0.7, 0.2],
        "upperBounds": [2.0, 1.0, 0.5],
        "fixedValues": {
          "at": 2.0, "bt": 0.3, "St": 0.15,
          "ba": 0.3, "Sa": 2.0, "u": 0.2
        }
      },
      {
        "name": "Stage 2: Joint Optimization",
        "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
        "initialValues": null,  // 使用 Stage 1 的結果
        "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
        "upperBounds": [2.0, 0.5, 3.0, 0.6, 0.5, 0.6, 30.0, 1.0],
        "fixedValues": {
          "bm": 0.86  // bm 保持固定（也可以從 Stage 1 繼承）
        }
      }
    ]
  }
}
```

### 測試案例 2：四階段優化（M-T-S-Joint）

**策略**：依序優化震級、時間、空間，最後聯合調整

```json
{
  "customStages": {
    "enable": true,
    "stages": [
      {
        "name": "Stage 1: Magnitude",
        "parameters": ["am", "Sm"],
        "initialValues": [1.5, 0.3],
        "lowerBounds": [1.0, 0.2],
        "upperBounds": [2.0, 0.5],
        "fixedValues": {
          "bm": 0.86, "at": 2.0, "bt": 0.3, "St": 0.15,
          "ba": 0.3, "Sa": 2.0, "u": 0.2
        }
      },
      {
        "name": "Stage 2: Temporal",
        "parameters": ["at", "bt", "St"],
        "initialValues": null,  // 繼承 Stage 1
        "lowerBounds": [1.0, 0.3, 0.15],
        "upperBounds": [3.0, 0.6, 0.5],
        "fixedValues": {
          // am, Sm, bm 自動繼承 Stage 1
          "ba": 0.3, "Sa": 2.0, "u": 0.2
        }
      },
      {
        "name": "Stage 3: Spatial",
        "parameters": ["ba", "Sa"],
        "initialValues": null,
        "lowerBounds": [0.2, 1.0],
        "upperBounds": [0.6, 30.0],
        "fixedValues": {
          // am, Sm, at, bt, St, bm 自動繼承前階段
          "u": 0.2
        }
      },
      {
        "name": "Stage 4: Joint Refinement",
        "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
        "initialValues": null,  // 使用前三階段的所有結果
        "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
        "upperBounds": [2.0, 0.5, 3.0, 0.6, 0.5, 0.6, 30.0, 1.0],
        "fixedValues": {"bm": 0.86}
      }
    ]
  }
}
```

### 測試案例 3：五階段超細緻優化

**策略**：逐一優化每個參數組，最後聯合調整

```json
{
  "customStages": {
    "enable": true,
    "stages": [
      {
        "name": "Stage 1: Magnitude Intercept",
        "parameters": ["am"],
        "initialValues": [1.5],
        "lowerBounds": [1.0],
        "upperBounds": [2.0],
        "fixedValues": {
          "bm": 0.86, "Sm": 0.3, "at": 2.0, "bt": 0.3,
          "St": 0.15, "ba": 0.3, "Sa": 2.0, "u": 0.2
        }
      },
      {
        "name": "Stage 2: Temporal Parameters",
        "parameters": ["at", "bt"],
        "initialValues": null,
        "lowerBounds": [1.0, 0.3],
        "upperBounds": [3.0, 0.6],
        "fixedValues": {
          "Sm": 0.3, "St": 0.15, "ba": 0.3, "Sa": 2.0, "u": 0.2
        }
      },
      {
        "name": "Stage 3: Variances",
        "parameters": ["Sm", "St"],
        "initialValues": null,
        "lowerBounds": [0.2, 0.15],
        "upperBounds": [0.5, 0.5],
        "fixedValues": {"ba": 0.3, "Sa": 2.0, "u": 0.2}
      },
      {
        "name": "Stage 4: Spatial and Mu",
        "parameters": ["ba", "Sa", "u"],
        "initialValues": null,
        "lowerBounds": [0.2, 1.0, 0.0],
        "upperBounds": [0.6, 30.0, 1.0],
        "fixedValues": {}  // 所有其他參數都已優化
      },
      {
        "name": "Stage 5: Joint Refinement",
        "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
        "initialValues": null,
        "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
        "upperBounds": [2.0, 0.5, 3.0, 0.6, 0.5, 0.6, 30.0, 1.0],
        "fixedValues": {"bm": 0.86}
      }
    ]
  }
}
```

---

## ⚠️ 重要限制與注意事項

### 1. Multistart 支援策略

- ✅ **Single-stage** 保持完整 multistart 支援
- ✅ **Three-stage** 保持完整 multistart 支援
- ❌ **Custom stages** 不支援 multistart（避免過度複雜）

理由：
- 自定義階段已經很靈活，再加 multistart 會讓配置過於複雜
- 使用者可以透過調整階段設計來達到類似效果
- 保持程式碼可維護性

### 2. 優化器選擇

自定義模式只支援單一優化器（從命令列或 config 指定），推薦：
- `SLSQP` (預設) - 穩定且快速
- `L-BFGS-B` - 適合高維問題
- `fminsearchcon` - 向後相容

### 3. 自動邊界調整

**現有行為**（我們要保持一致）：
- 執行完**所有階段**後，檢查最終結果是否觸碰邊界
- 如果觸碰，放寬邊界並重新執行**整個優化流程**（從第一階段開始）
- 迭代直到不觸碰邊界或達到最大輪數

**自定義模式的行為**（與上述一致）：
- ✅ 支援自動邊界調整
- ✅ 所有自定義階段執行完畢後，才檢查邊界
- ✅ 如需調整，放寬邊界並重新執行所有自定義階段
- ✅ 調整後的配置另存新檔（如 `config_custom_autoadjusted_round1.json`）

**範例流程**：
```
Round 1:
  → Stage 1 優化
  → Stage 2 優化
  → Stage 3 優化
  → 檢查最終結果：ba=0.599 觸碰上界 0.6
  → 放寬 ba 上界：0.6 → 1.2
  → 儲存為 config_custom_autoadjusted_round1.json

Round 2:
  → Stage 1 優化（使用新邊界）
  → Stage 2 優化（使用新邊界）
  → Stage 3 優化（使用新邊界）
  → 檢查最終結果：ba=0.701，不觸碰
  → 完成！
```

---

## 🔍 Git 保護策略

### 提交前檢查清單

1. ✅ 備份關鍵檔案
   ```bash
   cp optimize_eepas_parameters.py optimize_eepas_parameters.py.backup
   cp eepas_learning_auto_boundary.py eepas_learning_auto_boundary.py.backup
   cp utils/data_loader.py utils/data_loader.py.backup
   ```

2. ✅ 建立功能分支
   ```bash
   git checkout -b feature/custom-optimization-stages
   ```

3. ✅ 分階段提交
   - Commit 1: 新增配置解析函數
   - Commit 2: 新增自定義優化引擎
   - Commit 3: 整合自動邊界調整
   - Commit 4: 新增測試案例

4. ✅ 每次提交前測試向後相容
   ```bash
   # 測試腳本
   python3 test_backward_compatibility.py
   ```

---

## 📝 開發檢查清單

- [ ] 設計完成並確認
- [ ] 建立 Git 分支
- [ ] 實作配置解析函數
- [ ] 實作自定義優化引擎
- [ ] 整合到 auto_boundary
- [ ] 建立測試配置檔案
- [ ] 向後相容測試
- [ ] 新功能測試
- [ ] 文檔更新
- [ ] 最終驗證

---

## 📚 相關檔案

### 需要修改的檔案
1. `optimize_eepas_parameters.py` - 新增 `optimize_custom_stages()` 函數
2. `eepas_learning_auto_boundary.py` - 新增模式判斷邏輯
3. `utils/data_loader.py` - 新增配置解析函數
4. `CLAUDE.md` - 更新使用說明

### 需要建立的測試檔案
1. `config_custom_2stage.json` - 兩階段測試
2. `config_custom_4stage.json` - 四階段測試
3. `test_custom_stages.py` - 自動化測試腳本
4. `test_backward_compatibility.py` - 向後相容測試

---

**設計完成日期**: 2025-11-30
**設計者**: Claude Code
**版本**: v1.0
