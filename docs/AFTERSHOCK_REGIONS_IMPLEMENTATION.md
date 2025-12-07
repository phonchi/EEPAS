# Aftershock Fitting 空間區域處理實現

## 概述

本文檔說明 EEPAS 第二階段（Aftershock Model Fitting）中 testing region R 和 neighborhood region 的正確處理方式。

## 數學背景

根據 README.tex (Lines 191-226) 和 ggad123.pdf，aftershock model 的似然函數為：

```
ln L = Σ_{ti∈(T1,T2), mi≥m0, (xi,yi)∈R} log λ'(ti,mi,xi,yi)
       - ∫∫∫∫[R] λ'(t,m,x,y) dt dm dx dy
```

其中：
- **Σ 求和**：僅對 **testing region R** 內的目標事件
- **∫ 積分**：僅在 **testing region R** 上進行
- **Source events**：來自 **neighborhood region**（避免邊界效應）

Aftershock model:
```
λ'(t,m,x,y) = ν·λ₀(t,m,x,y) + κ·Σ λᵢ'(t,m,x,y)
```

其中：
- **ν (nu)**: 非餘震比例
- **κ (kappa)**: 餘震正規化常數
- **λ₀**: PPE 背景率
- **λᵢ'**: 餘震貢獻

## 實現詳情

### 1. 修改文件

#### `fit_aftershock_params.py`

**修改內容**：
- 載入 `RegionManager`（Lines 95-112）
- 對三個地震目錄進行空間篩選（Lines 124-181）：
  - **CatPrecursors** (M≥m0): 篩選至 **neighborhood region**
  - **CatJ** (M≥mT): 篩選至 **neighborhood region**
  - **CatTargets** (學習期, M≥m0): 篩選至 **testing region R**
- 傳遞 `region_manager` 至 likelihood 函數（Lines 194, 208）

**關鍵邏輯**：
```python
# 義大利模式
if region_manager is not None:
    # Source events: neighborhood region（邊界補償）
    CatPrecursors = CatalogProcessor.filter_by_region(
        CatPrecursors_all, region_manager, region_type='neighborhood'
    )
    CatJ = CatalogProcessor.filter_by_region(
        CatJ_all, region_manager, region_type='neighborhood'
    )

    # Target events: testing region R（我們關心的預測區域）
    CatTargets = CatalogProcessor.filter_by_region(
        CatTargets_all, region_manager, region_type='testing'
    )
else:
    # 台灣模式：不篩選（向後相容）
    CatPrecursors = CatPrecursors_all
    CatJ = CatJ_all
    CatTargets = CatTargets_all
```

#### `neg_log_like_aftershock.py`

**修改內容**：
- 添加 `region_manager` 參數（Line 174）
- 更新文檔字符串說明空間區域處理（Lines 190-196）
- 添加註釋說明對數似然項和積分項的空間範圍（Lines 246-263）

**關鍵說明**：
```python
# 對數似然項：Σ_{(xi,yi)∈R} log λ'(ti,mi,xi,yi)
# CatTargets 已在 fit_aftershock_params.py 中篩選至 testing region R
log_lambda_sum = compute_event_terms_fast(...)

# 正規化積分：∫∫∫∫[R] λ'(t,m,x,y) dt dm dx dy
# CELLE 定義了 testing region R 的網格
# Source events (CatPrecursors, CatJ) 來自 neighborhood region
integral_ppe = calculate_ppe_integral_term_mT(..., CELLE, ...)
integral_triggered = calculate_triggered_integral_fast(..., CELLE)
```

### 2. 空間區域對應關係

| 項目 | 台灣模式 | 義大利模式 | 說明 |
|------|---------|-----------|------|
| **CatTargets** | 全域 | Testing R | 目標事件（用於似然求和） |
| **CatPrecursors** | 全域 | Neighborhood | 餘震源事件（M≥m0） |
| **CatJ** | 全域 | Neighborhood | PPE源事件（M≥mT） |
| **積分區域 (CELLE)** | 全域 | Testing R | 空間積分範圍 |

### 3. 與其他模組的一致性

Aftershock fitting 的空間處理與其他模組完全一致：

| 模組 | Target Events | Source Events | 積分區域 | 狀態 |
|------|---------------|---------------|----------|------|
| **PPE Learning** | Testing R | Neighborhood | Testing R | ✅ |
| **EEPAS Learning** | Testing R | Neighborhood | Testing R | ✅ |
| **PPE Forecast** | - | Neighborhood | Testing R | ✅ |
| **EEPAS Forecast** | - | Neighborhood | Testing R | ✅ |
| **Aftershock Fitting** | Testing R | Neighborhood | Testing R | ✅ |

## 測試驗證

### 測試文件

`test_aftershock_regions.py` 包含三個測試：

1. **向後相容性測試**：驗證台灣模式（`region_manager=None`）正常工作
2. **義大利模式空間篩選測試**：驗證空間區域正確篩選
3. **積分區域驗證測試**：驗證 CELLE 定義 testing region R

### 測試結果

```
✓ 通過 - 向後相容性（台灣模式）
✓ 通過 - 義大利模式空間篩選
✓ 通過 - 積分區域驗證

總計: 3 通過, 0 失敗, 0 跳過
```

### 義大利模式測試輸出示例

```
空間區域配置:
  Testing Region: grid
  Neighborhood Region: polygon

1. CatPrecursors (M≥3.0):
   篩選前: 11325 事件
   篩選後: 11325 事件 (neighborhood region)

2. CatJ (M≥5.0):
   篩選前: 101 事件
   篩選後: 101 事件 (neighborhood region)

3. CatTargets (學習期, M≥3.0):
   篩選前: 6018 事件
   篩選後: 4538 事件 (testing region R)

✓ 空間篩選邏輯正確:
  - Source events 來自 neighborhood region
  - Target events 來自 testing region R
  - neighborhood region ⊃ testing region R ✓
```

## 物理意義

### 為什麼 Source Events 來自 Neighborhood Region？

根據 ggad123.pdf page 2：
> "To avoid edge effects in the fitting of model parameters, **the contribution of earthquakes in the neighbourhood of the region R must also be considered**"

- **邊界效應問題**：如果只使用 testing region R 內的地震，靠近邊界的目標事件會缺少來自外部的影響
- **解決方法**：使用更大的 neighborhood region 作為 source events，確保 testing region R 內的所有位置都能獲得完整的影響

### 為什麼 Target Events 和積分在 Testing Region R？

- **預測目標**：我們關心的是 testing region R 內的地震預測
- **似然函數定義**：對數似然項僅對我們關心預測的區域內的事件求和
- **正規化條件**：積分確保預測的總地震數與該區域內的實際地震數匹配

## 向後相容性

當 `region_manager=None` 時（台灣模式）：
- 所有空間篩選邏輯被跳過
- 行為與原始實現完全一致
- 不影響現有台灣數據的處理

## 總結

✅ **完成項目**：
1. ✅ `fit_aftershock_params.py` 支援空間區域篩選
2. ✅ `neg_log_like_aftershock.py` 添加 `region_manager` 參數
3. ✅ Source events 正確來自 neighborhood region
4. ✅ Target events 正確來自 testing region R
5. ✅ 積分正確在 testing region R 上進行
6. ✅ 完全向後相容台灣模式
7. ✅ 與其他模組（PPE/EEPAS Learning/Forecast）邏輯一致
8. ✅ 測試驗證通過

**系統現在可以正確處理義大利數據的 aftershock fitting！** 🎉
