# Custom 策略使用指南

## 概述

EEPAS 提供三種使用方式：

1. **舊格式（完全自定義）**: 直接在 JSON 中定義 stage1/stage2/stage3
2. **預定義策略**: 使用 `biondini2023` 或 `single_stage`
3. **Custom 策略**: 使用 `strategy: "custom"` 並自定義所有細節

## 預定義策略

### biondini2023
標準三階段優化（Biondini et al., 2023）

```json
{
  "optimization": {
    "strategy": "biondini2023"
  }
}
```

### single_stage
單階段優化（適合大數據集或良好初值）

```json
{
  "optimization": {
    "strategy": "single_stage"
  }
}
```

## Custom 策略

使用 custom 策略可以完全自定義：
- 階段數量（1-10個階段）
- 每階段優化哪些參數
- 每階段固定哪些參數
- 初始值
- 邊界

### 範例 1: 兩階段自定義

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "自定義兩階段優化",
      "stages": [
        {
          "name": "stage1_magnitude",
          "description": "先優化震級相關參數",
          "optimize": ["am", "Sm", "Sa"],
          "fix": {
            "bm": 1.0,
            "at": 2.0,
            "bt": 0.4,
            "St": 0.23,
            "ba": 0.35,
            "u": 0.5
          },
          "initial": {
            "am": 1.5,
            "Sm": 0.3,
            "Sa": 5.0
          },
          "bounds": {
            "am": [1.0, 2.0],
            "Sm": [0.2, 0.65],
            "Sa": [1.0, 30.0]
          }
        },
        {
          "name": "stage2_all",
          "description": "聯合優化所有參數",
          "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
          "fix": {
            "bm": 1.0
          },
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

### 範例 2: 四階段精細優化

```json
{
  "optimization": {
    "strategy": "custom",
    "custom": {
      "description": "四階段精細優化",
      "stages": [
        {
          "name": "magnitude_mean",
          "optimize": ["am"],
          "fix": {
            "bm": 1.0,
            "Sm": 0.32,
            "at": 1.5,
            "bt": 0.4,
            "St": 0.23,
            "ba": 0.35,
            "Sa": 10.0,
            "u": 0.2
          },
          "initial": {"am": 1.5},
          "bounds": {"am": [1.0, 2.0]}
        },
        {
          "name": "time_mean",
          "optimize": ["at"],
          "fix": {
            "bm": 1.0,
            "Sm": 0.32,
            "bt": 0.4,
            "St": 0.23,
            "ba": 0.35,
            "Sa": 10.0,
            "u": 0.2
          },
          "inherit": ["am"],
          "initial": {"at": 1.5},
          "bounds": {"at": [1.0, 3.0]}
        },
        {
          "name": "spatial_mixing",
          "optimize": ["Sa", "u"],
          "fix": {
            "bm": 1.0,
            "Sm": 0.32,
            "bt": 0.4,
            "St": 0.23,
            "ba": 0.35
          },
          "inherit": ["am", "at"],
          "initial": {"Sa": 10.0, "u": 0.2},
          "bounds": {
            "Sa": [1.0, 30.0],
            "u": [0.0, 1.0]
          }
        },
        {
          "name": "final_joint",
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

## 參數說明

### 每個階段可設定：

- **name**: 階段名稱（字串）
- **description**: 階段描述（可選）
- **optimize**: 要優化的參數列表
- **fix**: 固定參數及其值（字典）
- **inherit**: 從前階段繼承哪些參數
  - `"all"`: 繼承所有前階段參數
  - `["am", "at"]`: 只繼承指定參數
- **initial**: 初始值（字典，第一階段必須提供）
- **bounds**: 邊界（字典，所有優化參數都需要）

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

## 使用建議

1. **初學者**: 使用 `biondini2023` 策略
2. **快速測試**: 使用 `single_stage` 策略
3. **研究需求**: 使用 `custom` 策略自定義優化流程
4. **最大控制**: 使用舊格式（stage1/stage2/stage3 直接定義）

## 驗證配置

使用以下指令驗證配置是否正確：

```bash
python3 -c "
from utils.optimization_strategies import load_optimization_config
import json

with open('your_config.json') as f:
    config = json.load(f)

opt_config = load_optimization_config(config)
print('✅ 配置載入成功')
print(f'階段數: {len(opt_config[\"stages\"])}')
for i, stage in enumerate(opt_config['stages'], 1):
    print(f'  階段 {i}: {stage[\"name\"]} - 優化 {len(stage[\"optimize\"])} 個參數')
"
```
