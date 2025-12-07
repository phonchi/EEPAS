# EEPAS 優化配置指南

## 概述

EEPAS 支援自由配置多階段優化流程，使用者可以在 JSON 配置檔案中完全控制：
- 階段數量（1-10 個階段）
- 每階段優化哪些參數
- 每階段固定哪些參數
- 初始值和邊界

## 基本配置格式

```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am", "at", "Sa", "u"],
      "initialValues": [1.5, 1.5, 2.0, 0.2],
      "lowerBounds": [1.0, 1.0, 1.0, 0.0],
      "upperBounds": [2.0, 3.0, 30.0, 1.0],
      "fixedValues": {
        "bm": 1.0,
        "Sm": 0.32,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35
      }
    },
    "stage2": {...},
    "stage3": {...}
  }
}
```

## 參數說明

### 每個階段必須包含：

- **parameters**: 本階段要優化的參數列表（陣列）
- **initialValues**: 對應參數的初始值（陣列，順序與 parameters 相同）
- **lowerBounds**: 對應參數的下界（陣列）
- **upperBounds**: 對應參數的上界（陣列）
- **fixedValues**: 固定參數及其值（字典）

### 可用參數：

- `am`: 震級均值尺度參數
- `bm`: 震級斜率（通常固定為 1.0）
- `Sm`: 震級標準差
- `at`: 時間均值尺度參數
- `bt`: 時間斜率
- `St`: 時間標準差
- `ba`: 空間斜率
- `Sa`: 空間標準差
- `u`: 混合參數

### 標準邊界範圍（供參考）：

```python
'am': [1.0, 2.0]
'bm': [0.8, 1.2]  # 通常固定為 1.0
'Sm': [0.2, 0.65]
'at': [1.0, 3.0]
'bt': [0.3, 0.65]
'St': [0.15, 0.6]
'ba': [0.2, 0.6]
'Sa': [1.0, 30.0]
'u': [0.0, 1.0]
```

## 範例 1: 標準三階段優化（Biondini et al., 2023）

```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am", "at", "Sa", "u"],
      "initialValues": [1.5, 1.5, 2.0, 0.2],
      "lowerBounds": [1.0, 1.0, 1.0, 0.0],
      "upperBounds": [2.0, 3.0, 30.0, 1.0],
      "fixedValues": {
        "bm": 1.0,
        "Sm": 0.32,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35
      }
    },
    "stage2": {
      "parameters": ["Sm", "bt", "St", "ba", "u"],
      "initialValues": [0.32, 0.4, 0.23, 0.35, 0.2],
      "lowerBounds": [0.2, 0.3, 0.15, 0.2, 0.0],
      "upperBounds": [0.65, 0.65, 0.6, 0.6, 1.0],
      "fixedValues": {
        "bm": 1.0
      }
    },
    "stage3": {
      "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
      "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
      "fixedValues": {
        "bm": 1.0
      }
    }
  }
}
```

**說明**：
- Stage 1: 優化均值參數（am, at）、空間參數（Sa）和混合參數（u）
- Stage 2: 優化不確定性和斜率參數，繼承 Stage 1 的結果
- Stage 3: 聯合優化所有參數，從 Stage 2 的結果開始

## 範例 2: 兩階段優化

```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am", "Sm", "Sa"],
      "initialValues": [1.5, 0.3, 5.0],
      "lowerBounds": [1.0, 0.2, 1.0],
      "upperBounds": [2.0, 0.65, 30.0],
      "fixedValues": {
        "bm": 1.0,
        "at": 2.0,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35,
        "u": 0.5
      }
    },
    "stage2": {
      "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
      "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
      "fixedValues": {
        "bm": 1.0
      }
    }
  }
}
```

## 範例 3: 四階段精細優化

```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am"],
      "initialValues": [1.5],
      "lowerBounds": [1.0],
      "upperBounds": [2.0],
      "fixedValues": {
        "bm": 1.0,
        "Sm": 0.32,
        "at": 1.5,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35,
        "Sa": 10.0,
        "u": 0.2
      }
    },
    "stage2": {
      "parameters": ["at"],
      "initialValues": [1.5],
      "lowerBounds": [1.0],
      "upperBounds": [3.0],
      "fixedValues": {
        "bm": 1.0,
        "Sm": 0.32,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35,
        "Sa": 10.0,
        "u": 0.2
      }
    },
    "stage3": {
      "parameters": ["Sa", "u"],
      "initialValues": [10.0, 0.2],
      "lowerBounds": [1.0, 0.0],
      "upperBounds": [30.0, 1.0],
      "fixedValues": {
        "bm": 1.0,
        "Sm": 0.32,
        "bt": 0.4,
        "St": 0.23,
        "ba": 0.35
      }
    },
    "stage4": {
      "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
      "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
      "fixedValues": {
        "bm": 1.0
      }
    }
  }
}
```

## 參數繼承

程式會自動從前階段繼承優化結果：
- Stage 2 自動繼承 Stage 1 的優化結果
- Stage 3 自動繼承 Stage 2 的優化結果
- 以此類推

**注意**：如果某參數在前階段已優化，但本階段不在 `parameters` 和 `fixedValues` 中，它會自動繼承前階段的值。

## Auto-Boundary 支持

使用 `eepas_learning_auto_boundary.py` 時，如果參數觸碰邊界，程式會：
1. 自動調整該參數的邊界
2. 將新邊界寫回 JSON 檔案（生成 `*_autoadjusted_roundN.json`）
3. 使用新邊界重新優化

**這就是為什麼所有配置都必須在 JSON 裡！**

## 使用範例

### 三階段優化（推薦）

```bash
python3 eepas_learning_auto_boundary.py --config config.json --three-stage
```

### 單階段優化（快速測試）

設定 stage1 包含所有參數，然後：
```bash
python3 eepas_learning_auto_boundary.py --config config_single.json
```

## 驗證配置

使用以下指令驗證配置是否正確：

```bash
python3 -c "
import json

with open('your_config.json') as f:
    config = json.load(f)

opt = config.get('optimization', {})
n = 1
while f'stage{n}' in opt:
    stage = opt[f'stage{n}']
    params = stage.get('parameters', [])
    print(f'Stage {n}: 優化 {len(params)} 個參數: {params}')
    n += 1

print(f'\\n總共 {n-1} 個階段')
"
```

## 常見問題

### Q: initialValues 的順序重要嗎？
A: **非常重要！**必須與 `parameters` 陣列的順序完全對應。

### Q: 可以定義幾個階段？
A: 理論上任意多個（stage1, stage2, ..., stage10 等），但通常 3 個階段已足夠。

### Q: 如果不提供 initialValues 會怎樣？
A: 程式會使用邊界的中點作為初始值。

### Q: fixedValues 可以省略嗎？
A: 可以。如果某參數既不在 `parameters` 也不在 `fixedValues` 中，它會從前階段繼承（如果有的話）。

---

**最後更新**: 2025-11-28
**維護者**: EEPAS Development Team
