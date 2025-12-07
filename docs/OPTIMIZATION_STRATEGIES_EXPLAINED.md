# EEPAS 優化策略詳解

## 📚 預定義優化策略說明

### 1. `biondini2023` - 標準三階段（預設）

**來源**: Biondini et al. (2023) 論文的方法

**策略**:
```
Stage 1: 優化平均尺度參數 [am, at, Sa] + 混合參數 [u]
  → 固定不確定性參數 (Sm, St) 和斜率參數 (bt, ba)

Stage 2: 優化不確定性參數 [Sm, St] + 斜率參數 [bt, ba] + 混合參數 [u]
  → 繼承 Stage 1 的結果 (am, at, Sa)
  → 固定 bm = 1.0

Stage 3: 聯合優化所有參數 [am, Sm, at, bt, St, ba, Sa, u]
  → 繼承 Stage 2 的所有結果作為初始值
  → 固定 bm = 1.0
```

**理由**:
1. **Stage 1 先優化平均值**：確定震級、時間、空間的基本尺度關係
2. **Stage 2 加入不確定性**：在已知平均尺度的基礎上，優化分散度和斜率
3. **Stage 3 聯合調整**：微調所有參數以達到全局最優

**適用場景**:
- ✅ 標準應用（推薦）
- ✅ 有充足數據
- ✅ 想要穩健收斂

**配置範例**:
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
```
Stage 1: 只優化震級相關參數 [am, Sm]
  → 固定時間和空間參數於合理初值

Stage 2: 只優化時間相關參數 [at, bt, St]
  → 繼承 Stage 1 的震級參數
  → 固定空間參數

Stage 3: 只優化空間和混合參數 [ba, Sa, u]
  → 繼承 Stage 1, 2 的結果

Stage 4: 聯合優化所有參數
  → 微調全域最優解
```

**理由**:
1. **震級最穩定**：震級關係通常有最強的信號（Bath's law, GR law）
2. **減少參數空間**：每階段只優化 2-3 個參數，降低複雜度
3. **物理意義分離**：分別處理震級、時間、空間三個獨立維度

**適用場景**:
- ✅ 數據量較小
- ✅ 震級分布清晰（明顯的 GR 關係）
- ✅ 想要更穩健的收斂
- ✅ 調試階段（逐步檢查每個維度）

**配置範例**:
```json
{
  "optimization": {
    "strategy": "magnitude_first",
    "strategies": {
      "magnitude_first": {
        "description": "逐維度優化：震級 → 時間 → 空間 → 聯合",
        "stages": [
          {
            "name": "magnitude",
            "optimize": ["am", "Sm"],
            "fix": {
              "bm": 1.0,
              "at": 2.0, "bt": 0.4, "St": 0.23,
              "ba": 0.35, "Sa": 10.0,
              "u": 0.5
            }
          },
          {
            "name": "time",
            "optimize": ["at", "bt", "St"],
            "inherit": ["am", "Sm"],
            "fix": {
              "bm": 1.0,
              "ba": 0.35, "Sa": 10.0,
              "u": 0.5
            }
          },
          {
            "name": "spatial_mixing",
            "optimize": ["ba", "Sa", "u"],
            "inherit": ["am", "Sm", "at", "bt", "St"],
            "fix": {"bm": 1.0}
          },
          {
            "name": "joint",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "inherit": "all",
            "fix": {"bm": 1.0}
          }
        ]
      }
    }
  }
}
```

**優點**:
- ⭐ 收斂更穩健（每階段參數少）
- ⭐ 容易診斷問題（分維度檢查）
- ⭐ 適合小數據集

**缺點**:
- ⚠️ 階段較多（4 階段）
- ⚠️ 總時間可能較長

---

### 3. `conservative` - 保守策略

**策略**:
```
Stage 1: 只優化最穩定的參數 [am, at, Sa]
  → 固定所有不確定性參數於文獻值
  → 固定混合參數 u 於保守值 (0.3-0.5)

Stage 2: 加入不確定性參數 [Sm, St]
  → 保持斜率參數固定
  → 繼承 Stage 1 結果

Stage 3: 加入斜率參數 [bt, ba]
  → 繼承 Stage 1, 2 結果

Stage 4: 最後才優化混合參數 [u]
  → 在所有物理參數確定後調整

Stage 5: 聯合微調（可選）
  → 小幅調整所有參數
```

**理由**:
1. **最小風險**：優先優化最穩定、物理意義最明確的參數
2. **逐步引入複雜性**：慢慢加入不確定性和高階參數
3. **保守的 u 值**：避免過度依賴 EEPAS component（防止過擬合）

**適用場景**:
- ✅ **數據量很小**（< 50 個 M≥5 事件）
- ✅ **數據質量不佳**（不完整性嚴重）
- ✅ **探索新區域**（沒有先驗知識）
- ✅ **需要穩健預測**（不追求極致擬合）
- ✅ **模型驗證階段**（確保基本參數正確）

**配置範例**:
```json
{
  "optimization": {
    "strategy": "conservative",
    "strategies": {
      "conservative": {
        "description": "保守逐步優化策略（適合小數據集）",
        "stages": [
          {
            "name": "core_scaling",
            "optimize": ["am", "at", "Sa"],
            "fix": {
              "bm": 1.0,
              "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35,
              "u": 0.4
            }
          },
          {
            "name": "magnitude_uncertainty",
            "optimize": ["Sm"],
            "inherit": ["am", "at", "Sa"],
            "fix": {
              "bm": 1.0,
              "bt": 0.4, "St": 0.23, "ba": 0.35,
              "u": 0.4
            }
          },
          {
            "name": "time_uncertainty",
            "optimize": ["St"],
            "inherit": ["am", "Sm", "at", "Sa"],
            "fix": {
              "bm": 1.0,
              "bt": 0.4, "ba": 0.35,
              "u": 0.4
            }
          },
          {
            "name": "slopes",
            "optimize": ["bt", "ba"],
            "inherit": ["am", "Sm", "at", "St", "Sa"],
            "fix": {
              "bm": 1.0,
              "u": 0.4
            }
          },
          {
            "name": "mixing",
            "optimize": ["u"],
            "inherit": ["am", "Sm", "at", "bt", "St", "ba", "Sa"],
            "fix": {"bm": 1.0}
          },
          {
            "name": "final_tuning",
            "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
            "inherit": "all",
            "fix": {"bm": 1.0},
            "bounds_tightened": true  // 使用更嚴格的邊界（±10%）
          }
        ]
      }
    }
  }
}
```

**優點**:
- ⭐ 最穩健（適合困難情況）
- ⭐ 防止過擬合
- ⭐ 容易理解和診斷

**缺點**:
- ⚠️ 階段很多（5-6 階段）
- ⚠️ 總時間長
- ⚠️ 可能無法達到最佳擬合

---

## 🎯 其他可能的策略

### 4. `uncertainty_first` - 不確定性優先

**策略**:
```
Stage 1: 優化所有不確定性參數 [Sm, St]
Stage 2: 優化平均參數 [am, at, Sa]
Stage 3: 優化斜率和混合 [bt, ba, u]
Stage 4: 聯合優化
```

**理由**: 如果你的數據分散度很大，先確定不確定性可能更合理

**適用**: 高度不確定的目錄（如歷史地震目錄）

---

### 5. `spatial_first` - 空間優先

**策略**:
```
Stage 1: 優化空間參數 [ba, Sa]
Stage 2: 優化時間參數 [at, bt, St]
Stage 3: 優化震級參數 [am, Sm]
Stage 4: 優化混合參數 [u]
Stage 5: 聯合優化
```

**理由**: 如果你的區域空間分布有明顯特徵（如斷層系統）

**適用**: 強烈空間聚集的地震目錄

---

### 6. `single_stage` - 單階段（最快但最不穩健）

**策略**:
```
Stage 1: 直接優化所有參數 [am, Sm, at, bt, St, ba, Sa, u]
```

**理由**: 最簡單，但容易陷入局部最優

**適用**:
- ✅ 有很好的初始值
- ✅ 數據量很大（> 200 個 M≥5）
- ✅ 快速測試
- ⚠️ 不推薦用於正式分析

---

## 📊 策略比較表

| 策略 | 階段數 | 穩健性 | 速度 | 適用數據量 | 複雜度 |
|------|--------|--------|------|------------|--------|
| `biondini2023` | 3 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 中-大 | 中 |
| `magnitude_first` | 4 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 小-中 | 中 |
| `conservative` | 5-6 | ⭐⭐⭐⭐⭐ | ⭐ | 小 | 高 |
| `uncertainty_first` | 4 | ⭐⭐⭐ | ⭐⭐ | 中 | 中 |
| `spatial_first` | 5 | ⭐⭐⭐ | ⭐⭐ | 中 | 中 |
| `single_stage` | 1 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 大 | 低 |

---

## 🔬 策略選擇指南

### 決策樹

```
數據量有多少？
├─ < 50 個 M≥5 事件
│  └─ 使用 `conservative`（最穩健）
│
├─ 50-150 個 M≥5 事件
│  ├─ 數據質量好？
│  │  ├─ 是 → `biondini2023`（標準）
│  │  └─ 否 → `magnitude_first`（較穩健）
│  └─ 特殊空間分布？
│     └─ 是 → `spatial_first`
│
└─ > 150 個 M≥5 事件
   ├─ 有很好的初始值？
   │  └─ 是 → `single_stage`（最快）
   └─ 否 → `biondini2023`（標準）
```

### 義大利範例（1990-2012）

- **事件數**: 27 個 M≥5
- **推薦**: `biondini2023` 或 `magnitude_first`
- **不推薦**: `single_stage`（數據太少）

### 台灣範例（假設）

- **事件數**: ~100 個 M≥5（1990-2020）
- **推薦**: `biondini2023`
- **可選**: `magnitude_first`（如果收斂有問題）

---

## 💡 實作建議

### 1. 預設策略優先順序

```python
DEFAULT_STRATEGY_PRIORITY = [
    'biondini2023',      # 首選：論文方法
    'magnitude_first',   # 備選：更穩健
    'conservative',      # 保底：最穩健但慢
]
```

### 2. 自動策略推薦

```python
def recommend_strategy(n_events, data_quality='medium'):
    """根據數據特性推薦策略"""
    if n_events < 50:
        return 'conservative'
    elif n_events < 150:
        if data_quality == 'high':
            return 'biondini2023'
        else:
            return 'magnitude_first'
    else:
        return 'biondini2023'
```

### 3. 策略驗證

每個策略應該包含：
- 描述和引用
- 適用場景
- 預期執行時間
- 範例配置

---

## 📚 參考文獻

1. **Biondini et al. (2023)** - 三階段優化方法
   - Geophysical Journal International
   - 標準 `biondini2023` 策略來源

2. **優化理論**
   - Multi-start optimization
   - Parameter space partitioning
   - Constrained optimization

3. **EEPAS 物理模型**
   - 震級尺度: Bath's law, GR law
   - 時間尺度: 前震時間分布
   - 空間尺度: 空間衰減

---

**總結**: 不同的策略適合不同的數據和目標，預設使用 `biondini2023`，遇到收斂問題時嘗試 `magnitude_first` 或 `conservative`！
