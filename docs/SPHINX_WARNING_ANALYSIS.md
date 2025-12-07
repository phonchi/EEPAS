# Sphinx 建構警告分析報告

**日期**: 2025-11-25
**建構狀態**: ✅ 成功（21 個警告）

---

## 📊 警告分類統計

| 類別 | 數量 | 嚴重性 | 可修復 |
|------|------|--------|--------|
| **Autodoc 匯入失敗** | 5 | 低 | ❌ 否 |
| **Notebook 標題層級跳躍** | 5 | 低 | ✅ 是 |
| **Lexing 錯誤 (Colab 指令)** | 10 | 低 | ✅ 是 |
| **未知 MIME 類型** | 1 | 低 | ❌ 否 |
| **總計** | **21** | **低** | **15 可修** |

---

## 🔍 詳細警告分析

### 1. Autodoc 匯入失敗 (5 個警告) - ❌ 不需修復

**警告內容**:
```
WARNING: autodoc: failed to import function 'optimize_psi_working.optimize_psi' from module 'analysis'
No module named 'decimal_time'

WARNING: autodoc: failed to import function 'dataset.extract_period_forecast' from module 'analysis'
No module named 'csep'
```

**原因**:
- `decimal_time` 和 `csep` 是可選的外部依賴
- 這些模組用於進階分析和 PyCSEP 評估
- 不影響核心文檔生成

**影響**: 無 - 這些函數的 API 文檔不會顯示，但不影響主要文檔

**建議**: 不需修復（可選依賴）

---

### 2. Notebook 標題層級跳躍 (5 個警告) - ✅ 需要修復

**警告內容**:
```
WARNING: Non-consecutive header level increase; H2 to H4 [myst.header]
earth_viz_Italy_clean.ipynb.rst:470002
earth_viz_Italy_clean.ipynb.rst:490002
earth_viz_Italy_clean.ipynb.rst:520002
earth_viz_Italy_clean.ipynb.rst:550002
earth_viz_Italy_clean.ipynb.rst:570002
```

**原因**:
- Markdown 標題從 H2 (##) 直接跳到 H4 (####)
- 違反 reStructuredText 的層級規範
- 應該依序使用 H1 → H2 → H3 → H4

**位置**: `earth_viz_Italy_clean.ipynb` 的介紹部分

**影響**: 輕微 - 文檔結構不完美，但可讀

**建議**: ✅ **需要修復** - 調整標題層級

---

### 3. Lexing 錯誤：Colab 指令 (10 個警告) - ✅ 可修復

**警告內容**:
```
WARNING: Lexing literal_block '!pip install pycsep -qq' as "python" resulted in an error at token: '!'
WARNING: Lexing literal_block '!cp /content/drive/...' as "python" resulted in an error at token: '!'
```

**原因**:
- Jupyter Notebook 中的 shell 指令（`!` 開頭）
- Sphinx 試圖將其解析為 Python 程式碼
- `!` 不是有效的 Python token

**位置**: 所有 3 個 notebooks 的檔案複製和套件安裝儲存格

**影響**: 輕微 - 語法高亮不正確，但內容顯示正常

**建議**: ✅ **可修復** - 將這些儲存格標記為 bash/shell 語言

---

### 4. 未知 MIME 類型 (1 個警告) - ❌ 不需修復

**警告內容**:
```
WARNING: skipping unknown output mime type: application/vnd.google.colaboratory.intrinsic+json
Examine_Psi_Italy_clean.ipynb:130002
```

**原因**:
- Google Colab 特定的輸出格式
- Sphinx 無法解析此 MIME 類型

**影響**: 無 - 該輸出在文檔中被跳過，不影響其他內容

**建議**: 不需修復（Colab 特定格式）

---

## 🛠️ 修復計劃

### 優先級 1: 修復標題層級跳躍 (5 個)

**檔案**: `earth_viz_Italy_clean.ipynb`
**問題位置**: 介紹章節中的 H4 標題

**修復方法**:
檢查標題結構，確保:
- H1 (#) → H2 (##) → H3 (###) → H4 (####)
- 不跳過任何層級

**預估影響**: 會改善文檔結構和導覽

---

### 優先級 2: 修復 Lexing 錯誤 (10 個)

**檔案**:
- `Estimate_mc_b_Italy_clean.ipynb` (3 個)
- `Examine_Psi_Italy_clean.ipynb` (3 個)
- `earth_viz_Italy_clean.ipynb` (4 個)

**修復方法**:
在 notebook metadata 中為 shell 指令儲存格添加語言標記:
```json
{
  "cell_type": "code",
  "metadata": {
    "language": "bash"
  }
}
```

或者在 Sphinx conf.py 中抑制這些警告

**預估影響**: 改善語法高亮顯示

---

### 優先級 3: 不需修復 (6 個)

**Autodoc 匯入失敗** (5 個):
- 可選依賴缺失
- 不影響文檔生成
- 建議保持現狀

**未知 MIME 類型** (1 個):
- Colab 特定格式
- 無法在 Sphinx 中渲染
- 建議保持現狀

---

## 📋 修復執行摘要

### 需要修復的警告: 15 個
- ✅ 標題層級跳躍: 5 個
- ✅ Lexing 錯誤: 10 個

### 不需修復的警告: 6 個
- ❌ Autodoc 匯入失敗: 5 個
- ❌ 未知 MIME 類型: 1 個

---

## 🎯 建議的修復順序

1. **立即修復**: 標題層級跳躍（影響文檔結構）
2. **次要修復**: Lexing 錯誤（改善視覺呈現）
3. **不修復**: Autodoc 和 MIME 類型警告（無實際影響）

---

## ✅ 修復後預期結果

修復後預期警告數量:
- **當前**: 21 個警告
- **修復標題後**: 16 個警告
- **修復 Lexing 後**: 6 個警告
- **最終保留**: 6 個警告（不可避免）

**最佳情況**: 從 21 個減少到 6 個警告（減少 71%）

---

**報告生成時間**: 2025-11-25
**建議執行時間**: 15-20 分鐘
**風險評估**: 低（僅修改 notebook metadata）
