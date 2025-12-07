# EEPAS 優化策略使用指南

## 📚 概述

EEPAS v0.4.0 引入了靈活的優化策略系統，允許使用者：
- 使用預定義策略（`biondini2023`, `magnitude_first`, `conservative`, `single_stage`）
- 自訂優化策略（自由選擇每階段優化的參數）
- **完全向後相容**舊的配置格式

## 🚀 快速開始

### 使用預定義策略

只需在配置檔案中指定策略名稱：

```json
{
  "optimization": {
    "strategy": "biondini2023"
  }
}
```

### 使用自訂策略

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "我的自訂策略",
      "stages": [
        {
          "name": "stage1",
          "optimize": ["am", "at", "Sa", "u"],
          "fix": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35},
          "bounds": {
            "am": [1.0, 2.0],
            "at": [1.0, 3.0],
            "Sa": [1.0, 30.0],
            "u": [0.0, 1.0]
          }
        },
        {
          "name": "stage2",
          "optimize": ["Sm", "bt", "St", "ba", "u"],
          "fix": {"bm": 1.0},
          "inherit": ["am", "at", "Sa"],
          "bounds": {
            "Sm": [0.2, 0.65],
            "bt": [0.3, 0.65],
            "St": [0.15, 0.6],
            "ba": [0.2, 0.6],
            "u": [0.0, 1.0]
          }
        }
      ]
    }
  }
}
```

## 📋 預定義策略

### 1. `biondini2023` - 標準三階段優化（預設，推薦）

**來源**: Biondini et al. (2023) 論文

**策略**:
- **Stage 1**: 優化平均尺度參數 `[am, at, Sa, u]`
  - 固定不確定性參數 (Sm, St) 和斜率參數 (bt, ba)
- **Stage 2**: 優化不確定性和斜率 `[Sm, bt, St, ba, u]`
  - 繼承 Stage 1 的結果 (am, at, Sa)
- **Stage 3**: 聯合優化所有參數 `[am, Sm, at, bt, St, ba, Sa, u]`

**適用場景**:
- ✅ 標準應用（推薦）
- ✅ 有充足數據
- ✅ 想要穩健收斂

**使用範例**:
```json
{
  "optimization": {
    "strategy": "biondini2023"
  }
}
```

---

### 2. `magnitude_first` - 震級優先策略

**策略**:
- **Stage 1**: 只優化震級參數 `[am, Sm]`
- **Stage 2**: 只優化時間參數 `[at, bt, St]`
- **Stage 3**: 只優化空間和混合 `[ba, Sa, u]`
- **Stage 4**: 聯合優化所有參數

**理由**:
- 震級關係最穩定（Bath's law, GR law）
- 減少每階段的參數空間
- 物理意義分離清晰

**適用場景**:
- ✅ 數據量較小
- ✅ 震級分布清晰
- ✅ 想要更穩健的收斂
- ✅ 調試階段

**使用範例**:
```json
{
  "optimization": {
    "strategy": "magnitude_first"
  }
}
```

---

### 3. `conservative` - 保守策略

**策略**:
- **Stage 1**: 只優化最穩定的參數 `[am, at, Sa]`
- **Stage 2**: 加入震級不確定性 `[Sm]`
- **Stage 3**: 加入時間不確定性 `[St]`
- **Stage 4**: 加入斜率參數 `[bt, ba]`
- **Stage 5**: 優化混合參數 `[u]`
- **Stage 6**: 聯合微調（可選）

**理由**:
- 最小風險
- 逐步引入複雜性
- 保守的 u 值（防止過擬合）

**適用場景**:
- ✅ **數據量很小**（< 50 個 M≥5）
- ✅ **數據質量不佳**
- ✅ **探索新區域**（沒有先驗知識）
- ✅ **模型驗證階段**

**使用範例**:
```json
{
  "optimization": {
    "strategy": "conservative"
  }
}
```

---

### 4. `single_stage` - 單階段優化

**策略**:
- **Stage 1**: 直接優化所有參數 `[am, Sm, at, bt, St, ba, Sa, u]`

**理由**: 最簡單，但容易陷入局部最優

**適用場景**:
- ✅ 有很好的初始值
- ✅ 數據量很大（> 200 個 M≥5）
- ✅ 快速測試
- ⚠️ **不推薦用於正式分析**

**使用範例**:
```json
{
  "optimization": {
    "strategy": "single_stage"
  }
}
```

---

## 🎯 策略選擇指南

### 決策樹

```
數據量有多少？
├─ < 50 個 M≥5 事件
│  └─ 使用 conservative（最穩健）
│
├─ 50-150 個 M≥5 事件
│  ├─ 數據質量好？
│  │  ├─ 是 → biondini2023（標準）
│  │  └─ 否 → magnitude_first（較穩健）
│  └─ 特殊空間分布？
│     └─ 是 → 考慮自訂策略
│
└─ > 150 個 M≥5 事件
   ├─ 有很好的初始值？
   │  └─ 是 → single_stage（最快）
   └─ 否 → biondini2023（標準）
```

### 策略比較表

| 策略 | 階段數 | 穩健性 | 速度 | 適用數據量 | 複雜度 |
|------|--------|--------|------|------------|--------|
| `biondini2023` | 3 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 中-大 | 中 |
| `magnitude_first` | 4 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 小-中 | 中 |
| `conservative` | 5-6 | ⭐⭐⭐⭐⭐ | ⭐ | 小 | 高 |
| `single_stage` | 1 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 大 | 低 |

---

## 🛠️ 自訂策略

### 基本結構

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "策略描述（可選）",
      "citation": "引用來源（可選）",
      "stages": [
        {
          "name": "階段名稱",
          "description": "階段描述（可選）",
          "optimize": ["要優化的參數列表"],
          "fix": {"固定參數": 值},
          "inherit": ["從前階段繼承的參數"] | "all",
          "bounds": {
            "參數名": [下界, 上界]
          }
        }
      ]
    }
  }
}
```

### 欄位說明

#### `optimize` (必填)
要在此階段優化的參數列表。

**可用參數**: `am`, `bm`, `Sm`, `at`, `bt`, `St`, `ba`, `Sa`, `u`

**注意**: `bm` 通常固定為 1.0

#### `fix` (可選)
固定參數及其值。

**範例**:
```json
"fix": {
  "bm": 1.0,
  "Sm": 0.32,
  "bt": 0.4
}
```

#### `inherit` (可選)
從前階段繼承參數的方式：
- `["param1", "param2", ...]`: 繼承指定參數
- `"all"`: 繼承所有前階段參數（除了 `fix` 中的）

**範例**:
```json
// 繼承指定參數
"inherit": ["am", "at", "Sa"]

// 繼承所有
"inherit": "all"
```

#### `bounds` (必填)
參數的邊界約束。

**範例**:
```json
"bounds": {
  "am": [1.0, 2.0],
  "Sm": [0.2, 0.65],
  "at": [1.0, 3.0]
}
```

### 自訂策略範例

#### 範例 1: 簡單兩階段策略

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "簡單兩階段：主要參數 → 聯合優化",
      "stages": [
        {
          "name": "main",
          "optimize": ["am", "at", "Sa", "u"],
          "fix": {
            "bm": 1.0,
            "Sm": 0.32,
            "bt": 0.4,
            "St": 0.23,
            "ba": 0.35
          },
          "bounds": {
            "am": [1.0, 2.0],
            "at": [1.0, 3.0],
            "Sa": [1.0, 30.0],
            "u": [0.0, 1.0]
          }
        },
        {
          "name": "joint",
          "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
          "fix": {"bm": 1.0},
          "inherit": "all",
          "bounds": {
            "am": [1.0, 2.0],
            "Sm": [0.2, 0.65],
            "at": [1.0, 3.0],
            "bt": [0.3, 0.65],
            "St": [0.15, 0.6],
            "ba": [0.2, 0.6],
            "Sa": [1.0, 30.0],
            "u": [0.0, 1.0]
          }
        }
      ]
    }
  }
}
```

#### 範例 2: 不確定性優先策略

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "不確定性優先（適合高度不確定的目錄）",
      "stages": [
        {
          "name": "uncertainty",
          "optimize": ["Sm", "St"],
          "fix": {
            "bm": 1.0,
            "am": 1.5,
            "at": 2.0,
            "bt": 0.4,
            "ba": 0.35,
            "Sa": 10.0,
            "u": 0.5
          },
          "bounds": {
            "Sm": [0.2, 0.65],
            "St": [0.15, 0.6]
          }
        },
        {
          "name": "mean_params",
          "optimize": ["am", "at", "Sa"],
          "fix": {"bm": 1.0, "bt": 0.4, "ba": 0.35, "u": 0.5},
          "inherit": ["Sm", "St"],
          "bounds": {
            "am": [1.0, 2.0],
            "at": [1.0, 3.0],
            "Sa": [1.0, 30.0]
          }
        },
        {
          "name": "slopes_mixing",
          "optimize": ["bt", "ba", "u"],
          "fix": {"bm": 1.0},
          "inherit": ["Sm", "St", "am", "at", "Sa"],
          "bounds": {
            "bt": [0.3, 0.65],
            "ba": [0.2, 0.6],
            "u": [0.0, 1.0]
          }
        },
        {
          "name": "joint",
          "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
          "fix": {"bm": 1.0},
          "inherit": "all",
          "bounds": {
            "am": [1.0, 2.0],
            "Sm": [0.2, 0.65],
            "at": [1.0, 3.0],
            "bt": [0.3, 0.65],
            "St": [0.15, 0.6],
            "ba": [0.2, 0.6],
            "Sa": [1.0, 30.0],
            "u": [0.0, 1.0]
          }
        }
      ]
    }
  }
}
```

---

## 🔄 向後相容性

**重要**: 舊的配置格式完全支援，無需修改！

舊格式（自動轉換）:
```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am", "at", "Sa", "u"],
      "initialValues": [1.5, 1.5, 2.0, 0.2],
      "lowerBounds": [1.0, 1.0, 1.0, 0.0],
      "upperBounds": [2.0, 3.0, 30.0, 1.0],
      "fixedValues": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35}
    },
    "stage2": {...},
    "stage3": {...}
  }
}
```

新格式會自動轉換為：
```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "從舊格式轉換（向後相容）",
      "stages": [
        {
          "name": "stage1",
          "optimize": ["am", "at", "Sa", "u"],
          "fix": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35},
          "bounds": {...}
        },
        ...
      ]
    }
  }
}
```

---

## 📚 執行範例

### 使用預定義策略

```bash
# 使用標準 biondini2023 策略
python3 eepas_learning_auto_boundary.py \
  --config config_italy_biondini2023.json \
  --three-stage

# 使用 magnitude_first 策略（更穩健）
python3 eepas_learning_auto_boundary.py \
  --config config_italy_magnitude_first.json \
  --three-stage

# 使用 conservative 策略（小數據集）
python3 eepas_learning_auto_boundary.py \
  --config config_italy_conservative.json \
  --three-stage
```

### 使用自訂策略

```bash
python3 eepas_learning_auto_boundary.py \
  --config config_italy_custom_strategy.json \
  --three-stage
```

### 使用舊格式配置（向後相容）

```bash
# 舊配置檔案仍然可以正常使用
python3 eepas_learning_auto_boundary.py \
  --config config_italy_causal_ew0.json \
  --three-stage
```

---

## 🔍 查看可用策略

在 Python 中查看所有預定義策略：

```python
from utils.optimization_strategies import list_available_strategies, print_strategy_info

# 列出所有可用策略
list_available_strategies()

# 查看特定策略詳情
print_strategy_info('biondini2023')
print_strategy_info('magnitude_first')
```

---

## 💡 最佳實踐

1. **首選預定義策略**: 除非有特殊需求，優先使用 `biondini2023`
2. **小數據集用 conservative**: 數據量 < 50 個 M≥5 時，使用 `conservative`
3. **調試用 magnitude_first**: 逐維度檢查，容易診斷問題
4. **測試自訂策略**: 新策略先在小數據集上測試
5. **記錄策略選擇**: 在 description 中記錄選擇此策略的原因

---

## 📞 常見問題

### Q: 如何選擇策略？
A: 參考上面的「策略選擇指南」，主要考慮數據量和數據質量。

### Q: 可以修改預定義策略嗎？
A: 不能直接修改，但可以複製到 `custom` 中進行修改。

### Q: 舊配置需要更新嗎？
A: 不需要！完全向後相容，舊配置會自動轉換。

### Q: 如何驗證策略配置？
A: 使用 `validate_stage_config()` 函數會自動驗證。

### Q: 階段數量有限制嗎？
A: 沒有限制，但建議不超過 6 個階段（性能考量）。

---

**最後更新**: 2025-11-28
**版本**: 0.4.0
**維護者**: EEPAS Development Team
