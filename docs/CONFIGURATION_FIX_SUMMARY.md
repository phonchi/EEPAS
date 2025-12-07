# Configuration.rst 文檔修正摘要

**日期**: 2025-11-26
**修正文件**: `docs/source/user_guide/configuration.rst`

---

## ✅ 已完成的修正

### 1. 修正 `learnEndYear` 語義不清 (Line 59-68)

**修正內容**:
- 明確標註此參數為 **exclusive**
- 新增說明：事件包含至前一年的 12 月 31 日
- 更新範例說明：`learnEndYear: 2012` 實際使用 1990-01-01 到 2011-12-31 的資料

**修正後**:
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

### 2. 修正 `useCausalEW` 和 `useRollingUpdate` 描述模糊 (Line 350-382)

**修正內容**:

#### `useCausalEW`:
- 明確說明作用階段：**learning 和 forecasting**
- 詳細解釋兩種模式：
  - `0`: Global E(w) - 使用整個學習期的全域平均權重
  - `1`: Causal E(w) - 僅使用目標地震之前的事件計算 E(w_i)
- 新增物理意義：確保每個時間步的 Gutenberg-Richter 定律成立
- 新增註記：雖然論文未明確提及，`useCausalEW=1` 更符合因果性原則

#### `useRollingUpdate`:
- 明確說明作用階段：**forecast phase only**
- 詳細說明兩種模式：
  - `true`: 每 3 個月更新預測，納入新觀測地震（論文標準方法）
  - `false`: 僅使用學習期地震生成預測（不推薦）
- 新增論文引用（引述 3-month rolling mechanism）

---

### 3. 刪除 `timeComp` 章節 (原 Line 375-387)

**修正內容**:
- **完全刪除** `timeComp` 參數說明
- 原因：此配置項在當前程式碼中**完全未使用**，保留會造成混淆

**刪除的內容**:
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

**注意**: 配置檔案 `config_italy_causal_ew0.json` 中仍保留此欄位（向後相容），但文檔不再說明。

---

### 4. 修正 `sigmaU` 描述完全錯誤 (Line 330-351)

**修正內容**:
- **完全重寫描述**
- 從錯誤的「mixing ratio u 的不確定性」改為正確的「Utsu 空間關係參數」
- 新增數學公式：σ_i = σ_U × 10^(m_i/2)
- 新增參數說明：
  - σ_i: 地震 i 觸發的餘震空間標準差
  - m_i: 觸發地震的震級
  - σ_U: 基礎空間縮放參數（本參數）
- 新增物理意義：控制餘震空間擴散如何隨主震震級縮放，較大主震產生更寬的餘震區

**修正後**:
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

   **Italy example**: ``0.006`` (calibrated for Italy from literature)
```

---

## 🔍 驗證結果

### Sphinx 編譯
```bash
cd docs
make clean && make html
```

**結果**: ✅ **成功編譯，無 warnings，無 errors**

### 數學公式渲染
檢查生成的 HTML 文件：
```bash
grep "sigma_i.*sigma_U" build/html/user_guide/configuration.html
```

**結果**: ✅ 公式正確渲染為 LaTeX 格式
```html
\[\sigma_i = \sigma_U \times 10^{m_i/2}\]
```

---

## 📊 修正統計

| 項目 | 數量 |
|------|------|
| 修正的參數描述 | 4 個 |
| 刪除的章節 | 1 個 |
| 新增的數學公式 | 1 個 |
| 總修改行數 | 約 80 行 |
| 編譯 warnings | 0 |
| 編譯 errors | 0 |

---

## 📝 未修正項目

根據 `CONFIG_DOCUMENTATION_FIX_PLAN.md` 問題 5：

### `bm` 參數值需要確認

**當前配置**: Stage 1, 2 中未優化，Stage 3 固定為 `bm = 1.0`

**論文中的兩種模式**:
- **模式 A (複現實驗)**: 固定 bm=1.0
- **模式 B (自動化優化)**: 優化得到 bm=0.764

**待確認**: 當前配置使用哪種模式？需要用戶確認後才能修正文檔中的 bm 描述。

---

## 🎯 修正影響

### 改善使用者體驗
1. **消除誤解**: `learnEndYear` 的 exclusive 行為現在明確說明
2. **增加透明度**: `useCausalEW` 和 `useRollingUpdate` 的物理意義清晰
3. **移除混淆**: 刪除未使用的 `timeComp` 參數
4. **修正錯誤**: `sigmaU` 描述現在與程式碼實現一致

### 技術文檔品質
1. **數學嚴謹性**: 新增 Utsu 空間關係公式
2. **可追溯性**: 引用論文來源（manuscript）
3. **一致性**: 文檔與程式碼實現完全一致

---

**修正完成時間**: 2025-11-26
**驗證狀態**: ✅ 全部通過
**文檔版本**: v1.2.1 (建議)
