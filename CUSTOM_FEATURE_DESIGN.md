# Custom 優化階段功能設計

## 目標
新增支援任意階段數的 custom 優化功能，同時**完全保留**現有的三階段 + multistart 功能。

## 參數順序修正
**問題**：optimize_eepas_parameters 的參數順序與 eepas_likelihood 不一致

**修正**：
- 原始：`mi, xi, ti, yi, xj, yj, mj, tj`
- 修正後：`mj, xj, tj, yj, xi, yi, mi, ti`
- 原因：與 eepas_likelihood 一致，xj=testing region, xi=neighborhood region

## 支援的兩種 JSON 格式

### 格式 1：舊格式（完全保留，使用現有代碼）
```json
{
  "optimization": {
    "stage1": { ... },
    "stage2": { ... },
    "stage3": { ... }
  }
}
```
→ **使用第 400-692 行的現有三階段 + multistart 代碼**

### 格式 2：新格式（新功能）
```json
{
  "optimization": {
    "stages": [
      {
        "name": "Stage 1",
        "parameters": ["am", "at", "Sa", "u"],
        "initialValues": [1.5, 1.5, 2.0, 0.2],
        "lowerBounds": [1.0, 1.0, 1.0, 0.0],
        "upperBounds": [2.0, 3.0, 30.0, 1.0],
        "fixedValues": {"bm": 1.0, "Sm": 0.32, "bt": 0.4, "St": 0.23, "ba": 0.35}
      },
      {
        "name": "Stage 2",
        "parameters": ["Sm", "bt", "St", "ba", "u"],
        "initialValues": ["Sm_default", 0.4, 0.23, 0.35, "u_from_stage_1"],
        "lowerBounds": [0.1, 0.1, 0.1, 0.1, 0.0],
        "upperBounds": [5.0, 3.0, 5.0, 2.0, 1.0],
        "fixedValues": {"bm": 1.0, "am": "am_from_stage_1", "at": "at_from_stage_1", "Sa": "Sa_from_stage_1"}
      }
    ]
  }
}
```
→ **使用新的 custom 處理邏輯**

## 實作策略

### 1. 函數簽名修正（第 38 行）
```python
# 修正前
def optimize_eepas_parameters(mi, xi, ti, yi, xj, yj, mj, tj, ...)

# 修正後
def optimize_eepas_parameters(mj, xj, tj, yj, xi, yi, mi, ti, ...)
```

### 2. 在函數開頭新增格式檢測（約第 100 行之前）
```python
# 載入優化配置
opt_config = cfg['optimization']

# 檢測格式
if 'stages' in opt_config:
    # 使用新的 custom 模式
    return _optimize_custom_stages(mj, xj, tj, yj, xi, yi, mi, ti, ...)
elif 'stage1' in opt_config:
    # 使用現有的三階段代碼（第 400-692 行，完全不修改）
    # 繼續執行現有邏輯...
    pass
```

### 3. 新增 _optimize_custom_stages 函數（在現有代碼之前插入）
- 支援任意階段數（1, 2, 3, 4, ...）
- 支援參數引用（如 `"u_from_stage_1"`）
- 支援 auto-boundary 調整
- 印出每階段的 NLL 和所有參數值

### 4. 現有三階段代碼（第 400-692 行）
**完全不修改！** 保留所有功能：
- multistart with Stage 3 quick evaluation
- 三階段優化邏輯
- 所有現有的輸出和日誌

## 關鍵點
1. ✅ **不刪除任何現有代碼**
2. ✅ **新功能完全獨立**
3. ✅ **向後相容 100%**
4. ✅ **參數順序統一**
5. ✅ **Auto-boundary 支援兩種模式**

## 需要修改的位置
1. 第 38 行：函數簽名（參數順序）
2. 約第 100 行前：新增格式檢測邏輯
3. 約第 150-390 行：新增 _optimize_custom_stages 函數
4. 第 400-692 行：**完全不動！**
5. eepas_learning.py：調用處的參數順序需要對應修正

## 測試計劃
1. 測試舊格式（stage1/stage2/stage3）→ 確保功能完全不變
2. 測試新格式（stages array）→ 確保 custom 功能正常
3. 測試 auto-boundary 在兩種模式下都正常運作
