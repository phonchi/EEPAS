# 配置文檔修正計畫

**日期**: 2025-11-26
**目的**: 修正 configuration.rst 中不直覺和錯誤的參數描述

---

## 📋 需要修正的問題

### 問題 1: `learnEndYear` 語義不清

**當前描述** (`source/user_guide/configuration.rst:59-64`):
```rst
.. py:data:: learnEndYear
   :type: integer

   Ending year of the learning period.

   **Italy example**: ``2012``
```

**問題**:
- 使用者會誤以為 `learnEndYear: 2012` 包含 2012 年的數據
- 實際上只使用到 2011-12-31 的數據（2012 是 exclusive）

**修正方案**:
```rst
.. py:data:: learnEndYear
   :type: integer

   Ending year of the learning period (exclusive).

   Events are included up to December 31 of the **previous year**.
   For example, ``learnEndYear: 2012`` means learning data spans
   from ``learnStartYear`` to 2011-12-31.

   **Italy example**: ``2012`` (uses data 1990-01-01 to 2011-12-31)
```

---

### 問題 2: `useCausalEW` 和 `useRollingUpdate` 描述模糊

**當前描述** (`source/user_guide/configuration.rst:346-362`):
```rst
.. py:data:: modelParams.useCausalEW
   :type: integer
   :value: 0 or 1

   Enable causal earthquake weighting.

   - ``0``: Non-causal (use all events)
   - ``1``: Causal (only past events influence forecast)

   **Italy example**: 0

.. py:data:: modelParams.useRollingUpdate
   :type: boolean

   Enable rolling update of earthquake weights during forecast.

   **Italy example**: true
```

**問題**:
- 兩者的差別不清楚
- 沒有說明在哪個階段使用
- 物理意義不明確

**根據程式碼和論文的正確定義**:

1. **useCausalEW** (使用位置: `eepas_likelihood.py:319-334`)
   - 作用階段: **Learning 和 Forecast**
   - 控制 E(w) 的計算方式
   - 論文未明確提及，但符合因果性原則

2. **useRollingUpdate** (使用位置: `ppe_make_forecast.py:135`)
   - 作用階段: **Forecast only**
   - 控制是否滾動更新預測（納入新地震）
   - 論文明確描述（第 653 行："3-month rolling mechanism"）

**修正方案**:
```rst
.. py:data:: modelParams.useCausalEW
   :type: integer
   :value: 0 or 1

   Control how the expected earthquake weight E(w) is calculated during
   **learning and forecasting**.

   - ``0`` (Global E(w)): Use the global average weight from entire learning period
   - ``1`` (Causal E(w)): For each target earthquake i, compute E(w_i) using only
     events that occurred **before** it (enforces causality)

   **Physical meaning**: Ensures Gutenberg-Richter law is satisfied at each time step.

   **Italy example**: ``0`` (global average for computational efficiency)

   **Note**: While not explicitly mentioned in the paper, ``useCausalEW=1`` better
   aligns with the causality principle enforced by Heaviside step functions.

.. py:data:: modelParams.useRollingUpdate
   :type: boolean

   Enable rolling update mechanism during **forecast phase only**.

   - ``true``: Update forecasts every 3 months by including newly observed earthquakes
     (standard approach described in paper)
   - ``false``: Generate forecasts once using only learning period earthquakes
     (not recommended)

   **Paper reference**: "Forecast generation operates on a 3-month rolling mechanism,
   which balances parameter stability with the incorporation of new seismic data"
   (main_gji.tex, line 653).

   **Italy example**: ``true``
```

---

### 問題 3: `timeComp` 已廢棄但仍存在

**當前描述** (`source/user_guide/configuration.rst:375-387`):
```rst
.. py:data:: modelParams.timeComp
   :type: object

   Time compensation configuration for magnitude distribution.

   .. code-block:: json

      "timeComp": {
        "enable": true,
        "mode": "B",
        "omega": 0.0,
        "lead_time_days": 90
      }
```

**問題**:
- 此配置項在當前程式碼中**完全未使用**
- 保留在配置文件和文檔中會造成混淆

**修正方案**:
- **完全刪除此章節**
- 從範例配置文件中移除 `timeComp` 欄位

---

### 問題 4: `sigmaU` 描述完全錯誤 ❌

**當前描述** (`source/user_guide/configuration.rst:326-332`):
```rst
.. py:data:: modelParams.sigmaU
   :type: float
   :value: 0.006

   Uncertainty in mixing ratio u.

   **Italy example**: 0.006
```

**問題**:
- **嚴重錯誤**: `sigmaU` 不是 "mixing ratio u 的不確定性"
- 正確定義: **Utsu 餘震空間擴散參數**

**論文定義** (main_gji.tex:264, 300, 683):
- 數學公式: σ_i = σ_U × 10^(m_i/2)
- 物理意義: 控制餘震相對於主震的空間擴散範圍
- 義大利設定值: 0.006

**程式碼實現** (`neg_log_like_aftershock.py:138`):
```python
sigma = sigmaU * np.sqrt(10**mp)  # σ = σ_U × √(10^m)
```

**修正方案**:
```rst
.. py:data:: modelParams.sigmaU
   :type: float
   :value: 0.006

   Utsu spatial relationship parameter for aftershock spatial distribution.

   **Mathematical definition**:

   .. math::

      \sigma_i = \sigma_U \times 10^{m_i/2}

   where:

   - σ_i: spatial standard deviation for aftershocks triggered by earthquake i
   - m_i: magnitude of triggering earthquake
   - σ_U: base spatial scaling parameter (this parameter)

   **Physical meaning**: Controls how aftershock spatial spread scales with
   mainshock magnitude. Larger mainshocks produce wider aftershock zones.

   **Italy example**: ``0.006`` (from Biondini et al. 2023, calibrated for Italy)

   **Paper reference**: main_gji.tex, lines 264, 300, 683
```

---

## 🎯 修正範圍

### 需要修改的檔案

1. **`docs/source/user_guide/configuration.rst`**
   - 修正 4 個參數描述
   - 刪除 timeComp 章節

2. **範例配置檔案** (可選，取決於是否要移除 timeComp)
   - `config_italy_causal_ew0.json`
   - `config_italy_causal_ew1.json`
   - `config_italy_causal_ew0_accurate.json`

### 不需要修改的檔案

- **程式碼**: 所有 Python 檔案實現正確，無需修改
- **論文**: main_gji.tex 是參考文件

---

## ✅ 驗證步驟

修正後需要執行：

1. **Sphinx 編譯測試**:
   ```bash
   cd docs
   make clean && make html
   ```

2. **數學公式渲染檢查**:
   - 確認 `σ_i = σ_U × 10^{m_i/2}` 正確顯示

3. **交叉引用檢查**:
   - 確認所有參數引用仍然有效

---

## 📌 待確認問題

### 問題 5: `bm` 參數值

**當前配置值**: `bm = 1.0` (Stage 1, 2)，`bm = 1.0` (Stage 3 fixed)

**論文中的兩種模式**:
- **模式 A (複現實驗)**: 固定 bm=1.0
- **模式 B (自動化優化)**: 優化得到 bm=0.764

**問題**: 當前配置使用哪種模式？需要用戶確認。

**影響**:
- 如果目標是複現論文：保持 `bm=1.0`
- 如果目標是自動化改進：可考慮使用 `bm=0.764` 或讓它自由優化

**建議**: 等待用戶確認後再修正文檔中的 bm 描述。

---

**執行狀態**: 📝 計畫已撰寫，等待執行修正
**預計修改行數**: ~80 行
**預計耗時**: 15-20 分鐘
