# 三階段優化配置重新設計方案

## 📋 目前的問題

### 現有設計的限制

目前的三階段優化配置**硬編碼了每階段優化的參數**：

```json
{
  "optimization": {
    "stage1": {
      "parameters": ["am", "at", "Sa", "u"],  // 固定的！
      "fixedValues": {"bm": 1.0, "Sm": 0.32, ...}
    },
    "stage2": {
      "parameters": ["Sm", "bt", "St", "ba", "u"],  // 固定的！
      "fixedValues": {"bm": 1.0, "am": "from_stage1", ...}
    },
    "stage3": {
      "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],  // 固定的！
      "fixedValues": {"bm": 1.0}
    }
  }
}
```

**問題**：
1. ❌ 使用者無法自由選擇每階段優化的參數
2. ❌ 無法輕鬆實驗不同的優化策略
3. ❌ 參數依賴關係不明確（如 "from_stage1"）
4. ❌ 難以新增或移除參數

---

## 🎯 改進方案

### 設計目標

1. ✅ **彈性選擇**：使用者可自由配置每階段優化的參數
2. ✅ **清晰依賴**：明確參數間的依賴關係
3. ✅ **預設推薦**：提供論文建議的預設配置
4. ✅ **向後相容**：舊配置檔案仍可正常運作
5. ✅ **易於擴展**：方便新增新參數或新策略

---

## 📐 新的配置格式

### 方案 A：顯式參數列表（推薦）

**優點**：直觀、清晰、易於理解

```json
{
  "optimization": {
    "mode": "three-stage",  // 或 "single-stage", "custom"

    "stage1": {
      "description": "Optimize mean scaling parameters (am, at, Sa) and u",
      "optimize": ["am", "at", "Sa", "u"],  // 要優化的參數
      "fix": {                              // 固定的參數
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

    "stage2": {
      "description": "Optimize uncertainty parameters (Sm, St) and slope parameters (bt, ba)",
      "optimize": ["Sm", "bt", "St", "ba", "u"],
      "fix": {
        "bm": 1.0
      },
      "inherit": ["am", "at", "Sa"],  // 從 Stage 1 繼承
      "bounds": {
        "Sm": [0.2, 0.65],
        "bt": [0.3, 0.65],
        "St": [0.15, 0.6],
        "ba": [0.2, 0.6],
        "u": [0.0, 1.0]
      }
    },

    "stage3": {
      "description": "Joint optimization of all parameters",
      "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "fix": {
        "bm": 1.0
      },
      "inherit": [],  // 從 Stage 2 繼承所有參數作為初始值
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
  }
}
```

---

### 方案 B：參數角色定義（進階）

**優點**：更明確的參數分類和依賴關係

```json
{
  "parameters": {
    "all": ["am", "bm", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
    "categories": {
      "magnitude_scaling": ["am", "bm", "Sm"],
      "time_scaling": ["at", "bt", "St"],
      "spatial_scaling": ["ba", "Sa"],
      "mixing": ["u"]
    }
  },

  "optimization": {
    "mode": "three-stage",

    "stage1": {
      "description": "Optimize mean scaling + mixing",
      "optimize": {
        "magnitude_scaling": ["am"],          // 震級：只優化 am
        "time_scaling": ["at"],                // 時間：只優化 at
        "spatial_scaling": ["Sa"],             // 空間：只優化 Sa
        "mixing": ["u"]                        // 混合：優化 u
      },
      "fix": {
        "bm": {"value": 1.0, "reason": "Physical constraint (Bath's law)"},
        "Sm": {"value": 0.32, "reason": "Defer to Stage 2"},
        "bt": {"value": 0.4, "reason": "Defer to Stage 2"},
        "St": {"value": 0.23, "reason": "Defer to Stage 2"},
        "ba": {"value": 0.35, "reason": "Defer to Stage 2"}
      },
      "bounds": {
        "am": [1.0, 2.0],
        "at": [1.0, 3.0],
        "Sa": [1.0, 30.0],
        "u": [0.0, 1.0]
      }
    },

    "stage2": {
      "description": "Optimize uncertainty + slope parameters",
      "optimize": {
        "magnitude_scaling": ["Sm"],
        "time_scaling": ["bt", "St"],
        "spatial_scaling": ["ba"],
        "mixing": ["u"]
      },
      "fix": {
        "bm": 1.0
      },
      "inherit_from": "stage1",  // 繼承 am, at, Sa
      "bounds": {
        "Sm": [0.2, 0.65],
        "bt": [0.3, 0.65],
        "St": [0.15, 0.6],
        "ba": [0.2, 0.6],
        "u": [0.0, 1.0]
      }
    },

    "stage3": {
      "description": "Joint optimization (all except bm)",
      "optimize": {
        "magnitude_scaling": ["am", "Sm"],
        "time_scaling": ["at", "bt", "St"],
        "spatial_scaling": ["ba", "Sa"],
        "mixing": ["u"]
      },
      "fix": {
        "bm": 1.0
      },
      "inherit_from": "stage2",
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
  }
}
```

---

### 方案 C：策略模板（最彈性）

**優點**：可預先定義多種優化策略，使用者選擇

```json
{
  "optimization": {
    "strategy": "biondini2023",  // 使用預定義策略
    // 或 "custom" 使用自訂配置

    "strategies": {
      "biondini2023": {
        "description": "Three-stage optimization from Biondini et al. (2023)",
        "stages": [
          {
            "name": "stage1",
            "optimize": ["am", "at", "Sa", "u"],
            "fix": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35}
          },
          {
            "name": "stage2",
            "optimize": ["Sm", "bt", "St", "ba", "u"],
            "fix": {"bm": 1.0},
            "inherit": ["am", "at", "Sa"]
          },
          {
            "name": "stage3",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "fix": {"bm": 1.0},
            "inherit": ["all_from_stage2"]
          }
        ]
      },

      "magnitude_first": {
        "description": "Optimize magnitude parameters first, then time, then spatial",
        "stages": [
          {
            "name": "magnitude",
            "optimize": ["am", "Sm"],
            "fix": {"bm": 1.0, "at": 2.0, "bt": 0.4, "St": 0.23, "ba": 0.35, "Sa": 10.0, "u": 0.5}
          },
          {
            "name": "time",
            "optimize": ["at", "bt", "St"],
            "inherit": ["am", "Sm"]
          },
          {
            "name": "spatial_and_mixing",
            "optimize": ["ba", "Sa", "u"],
            "inherit": ["am", "Sm", "at", "bt", "St"]
          },
          {
            "name": "joint",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "fix": {"bm": 1.0}
          }
        ]
      },

      "single_stage": {
        "description": "Optimize all parameters at once",
        "stages": [
          {
            "name": "full",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "fix": {"bm": 1.0}
          }
        ]
      }
    },

    "custom": {
      "description": "User-defined custom optimization strategy",
      "stages": [
        // 使用者可以自由定義任意數量的階段
      ]
    },

    "bounds": {
      "am": [1.0, 2.0],
      "bm": [1.0, 1.0],  // 固定
      "Sm": [0.2, 0.65],
      "at": [1.0, 3.0],
      "bt": [0.3, 0.65],
      "St": [0.15, 0.6],
      "ba": [0.2, 0.6],
      "Sa": [1.0, 30.0],
      "u": [0.0, 1.0]
    }
  }
}
```

---

## 💡 使用範例

### 範例 1：使用預設策略（最簡單）

```json
{
  "optimization": {
    "strategy": "biondini2023"
  }
}
```

程式碼自動載入 Biondini et al. (2023) 的三階段優化配置。

---

### 範例 2：自訂每階段參數（彈性）

```json
{
  "optimization": {
    "mode": "three-stage",
    "stage1": {
      "optimize": ["am", "at", "u"],  // 只優化這三個
      "fix": {
        "bm": 1.0,
        "Sm": 0.3,
        "bt": 0.4,
        "St": 0.2,
        "ba": 0.35,
        "Sa": 10.0
      }
    },
    "stage2": {
      "optimize": ["Sm", "St", "Sa", "u"],  // 加入不確定性參數
      "inherit": ["am", "at"]  // 從 Stage 1 繼承
    },
    "stage3": {
      "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
      "fix": {"bm": 1.0}
    }
  }
}
```

---

### 範例 3：實驗新的優化順序

```json
{
  "optimization": {
    "mode": "custom",
    "stages": [
      {
        "name": "spatial_first",
        "optimize": ["ba", "Sa"],
        "fix": {
          "am": 1.5, "bm": 1.0, "Sm": 0.32,
          "at": 2.0, "bt": 0.4, "St": 0.23,
          "u": 0.5
        }
      },
      {
        "name": "time_second",
        "optimize": ["at", "bt", "St"],
        "inherit": ["ba", "Sa"]
      },
      {
        "name": "magnitude_third",
        "optimize": ["am", "Sm"],
        "inherit": ["ba", "Sa", "at", "bt", "St"]
      },
      {
        "name": "final_joint",
        "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
        "fix": {"bm": 1.0}
      }
    ]
  }
}
```

---

## 🔧 實作考量

### 1. 向後相容性

**舊格式** (現有):
```json
{
  "stage1": {
    "parameters": ["am", "at", "Sa", "u"],
    "lowerBounds": [1.0, 1.0, 1.0, 0.0],
    "upperBounds": [2.0, 3.0, 30.0, 1.0],
    "fixedValues": {"bm": 1.0, ...}
  }
}
```

**新格式** (建議):
```json
{
  "stage1": {
    "optimize": ["am", "at", "Sa", "u"],
    "fix": {"bm": 1.0, ...},
    "bounds": {
      "am": [1.0, 2.0],
      "at": [1.0, 3.0],
      "Sa": [1.0, 30.0],
      "u": [0.0, 1.0]
    }
  }
}
```

**相容處理**:
```python
def load_stage_config(stage_config):
    # 檢測格式
    if "parameters" in stage_config:
        # 舊格式：自動轉換
        return convert_old_format(stage_config)
    elif "optimize" in stage_config:
        # 新格式：直接使用
        return stage_config
    else:
        raise ValueError("Unknown stage configuration format")
```

---

### 2. 參數驗證

```python
def validate_stage_config(stage_config, all_params):
    """驗證階段配置的正確性"""
    optimize = stage_config.get('optimize', [])
    fix = stage_config.get('fix', {})
    inherit = stage_config.get('inherit', [])

    # 檢查所有參數都被處理
    defined = set(optimize) | set(fix.keys()) | set(inherit)
    missing = set(all_params) - defined

    if missing:
        raise ValueError(f"Parameters not defined: {missing}")

    # 檢查沒有重複
    if len(defined) != len(optimize) + len(fix) + len(inherit):
        raise ValueError("Duplicate parameter definitions")

    # 檢查 bounds 完整性
    bounds = stage_config.get('bounds', {})
    for param in optimize:
        if param not in bounds:
            raise ValueError(f"Missing bounds for optimized parameter: {param}")

    return True
```

---

### 3. 繼承機制

```python
def inherit_parameters(stage_config, previous_results):
    """從前一階段繼承參數值"""
    inherit = stage_config.get('inherit', [])
    initial_values = {}

    for param in inherit:
        if param in previous_results:
            initial_values[param] = previous_results[param]
        else:
            raise ValueError(f"Cannot inherit {param}: not in previous results")

    return initial_values
```

---

## 📊 推薦方案比較

| 特性 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **彈性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **可讀性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **維護性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **學習曲線** | 簡單 | 中等 | 簡單 |
| **擴展性** | 好 | 好 | 極好 |

---

## 🎯 我的推薦

### 最佳方案：**方案 C（策略模板）**

**理由**：
1. ✅ **簡單使用**：預設策略一行搞定 `"strategy": "biondini2023"`
2. ✅ **完全彈性**：可自訂任意階段和參數
3. ✅ **清晰文檔**：每個策略有描述，容易理解
4. ✅ **易於維護**：新增策略只需加入 `strategies` 字典
5. ✅ **向後相容**：可保留 `biondini2023` 作為預設
6. ✅ **方便實驗**：研究人員可快速測試不同策略

### 實作優先順序

**Phase 1** (立即實作):
- 方案 C 的基本框架
- `biondini2023` 預設策略（對應現有三階段）
- `single_stage` 策略
- 向後相容處理

**Phase 2** (後續加強):
- 更多預定義策略（`magnitude_first`, `conservative`, etc.）
- 策略驗證和錯誤訊息優化
- 策略模板文檔

**Phase 3** (進階功能):
- 自動策略推薦（根據資料特性）
- 策略效能比較工具
- 視覺化優化過程

---

## 📝 配置檔案範例（完整）

```json
{
  "optimization": {
    "strategy": "biondini2023",

    "strategies": {
      "biondini2023": {
        "description": "標準三階段優化（Biondini et al., 2023）",
        "citation": "Biondini, D., Console, R., & Murru, M. (2023). Geophys. J. Int.",
        "stages": [
          {
            "name": "stage1_mean_scaling",
            "description": "優化平均尺度參數",
            "optimize": ["am", "at", "Sa", "u"],
            "fix": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35}
          },
          {
            "name": "stage2_uncertainty",
            "description": "優化不確定性和斜率參數",
            "optimize": ["Sm", "bt", "St", "ba", "u"],
            "fix": {"bm": 1.0},
            "inherit": ["am", "at", "Sa"]
          },
          {
            "name": "stage3_joint",
            "description": "聯合優化所有參數",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "fix": {"bm": 1.0},
            "inherit": "all"
          }
        ]
      }
    },

    "bounds": {
      "am": [1.0, 2.0],
      "bm": [1.0, 1.0],
      "Sm": [0.2, 0.65],
      "at": [1.0, 3.0],
      "bt": [0.3, 0.65],
      "St": [0.15, 0.6],
      "ba": [0.2, 0.6],
      "Sa": [1.0, 30.0],
      "u": [0.0, 1.0]
    }
  }
}
```

---

**結論**：方案 C 提供了最佳的平衡，既簡單（預設策略）又強大（完全自訂），適合不同層級的使用者！
