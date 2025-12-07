# Documentation Directory

本資料夾包含 EEPAS Taiwan 項目的詳細文檔和分析報告。

## 📂 文檔列表

### 義大利模式實現（v1.2.0）

- **IMPLEMENTATION_STATUS.md** - 完整實現狀態總結
  - 所有模組（PPE/EEPAS Learning/Forecast + Aftershock）義大利模式支持
  - 測試覆蓋率 24/24 (100%)
  - 向後相容台灣模式

- **AFTERSHOCK_REGIONS_IMPLEMENTATION.md** - Aftershock Fitting 空間區域實現
  - `fit_aftershock_params.py` 修改細節
  - `neg_log_like_aftershock.py` 修改細節
  - 測試驗證結果

### 配置與映射

- **CONFIG_MAPPING.md** - 四種配置對應關係說明
  - 標準配置 (m0=2.35)
  - 去叢集配置 (m0=2.05)
  - 包含921地震配置 (m0=2.35)
  - m0=2.05 變體配置

### 分析報告

- **earthquake_distribution_analysis_report.md** - 地震分布分析報告
  - 6區域 vs 24區域地震分布比較
  - 統計分析與視覺化結果

- **README_DISTRIBUTION_ANALYSIS.md** - 地震分布分析工具說明
  - `distribution_analysis.py` 使用指南
  - 輸出格式與解讀

- **README_WEIGHT_ANALYSIS.md** - 權重分析工具說明
  - `weight_analysis.py` 使用指南
  - 四種配置的權重比較

- **REGION_SUBDIVISION_VERIFICATION.md** - 區域細分驗證報告
  - 6→24 區域細分正確性驗證
  - 數值驗證與結果

### 遷移記錄

- **ANALYSIS_MIGRATION_COMPLETE.md** - 分析工具 MATLAB→Python 遷移完成報告
  - 遷移項目清單
  - 驗證結果
  - 功能對照表

## 🎯 主要用途

### 1. 配置選擇參考
查閱 `CONFIG_MAPPING.md` 了解不同配置的特點和適用場景。

### 2. 分析工具使用
- 地震分布分析：`README_DISTRIBUTION_ANALYSIS.md`
- 權重分析：`README_WEIGHT_ANALYSIS.md`
- 區域細分：`REGION_SUBDIVISION_VERIFICATION.md`

### 3. 研究參考
所有分析報告提供了詳細的數據、圖表和統計結果，可作為研究和論文撰寫的參考。

## 📊 相關工具

所有分析工具位於 `../analysis/` 資料夾：

```bash
cd ../analysis/
python3 distribution_analysis.py  # 地震分布分析
python3 weight_analysis.py        # 權重分析
python3 region_subdivision.py     # 區域細分工具
```

## 🌍 義大利數據支持

系統現已完全支持義大利地震數據：
- Testing Region R (177 grid cells, 30√2 km)
- Neighborhood Region (polygon, larger area)
- 所有模組支持空間區域篩選
- 完全向後相容台灣模式

詳見 `IMPLEMENTATION_STATUS.md`

## 📝 文檔維護

- 最後更新：2025-01-24
- 維護者：EEPAS Taiwan Team
- 如有問題或建議，請參考主 README.md
