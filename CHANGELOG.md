# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-11-06

### Added
- 🔬 **數值積分重構與驗證（本版本核心）**：
  - 統一數值積分介面：`utils/numerical_integration.py`
  - 實現 ACCURATE 模式（scipy.dblquad 雙重積分）
  - 實現 FAST 模式（梯形法積分，預設）
  - 所有模組支持 `--accurate` 和 `--fast` 參數切換
  - 完整的 ACCURATE vs FAST 比較報告（`ACCURATE_VS_FAST_COMPARISON_REPORT.md`）
- ✅ **數值積分驗證結果**：
  - 兩種因果性設定測試：useCausalEW=0 (Fixed EW) 和 useCausalEW=1 (Dynamic EW)
  - **所有參數相對差異 < 0.2%**，驗證梯形法精度充分
  - PPE 參數差異 < 0.001%
  - EEPAS 參數差異 < 0.16%
  - Forecast Lambda 差異 < 0.004%
- ⚡ **性能基準測試**：
  - FAST 模式整體快 **1.75 倍**（Forecast 階段快 **4 倍**）
  - **推薦策略**：日常研究使用 FAST 模式，最終論文驗證使用 ACCURATE 模式
- 📊 **Lambda 積分驗證工具**：
  - Learning 階段 Λ_PPE 驗證：應接近目標事件數量 N
  - Forecast 階段 Lambda 總和驗證工具（`analysis/analyze_forecast_lambda.py`）
  - 修正索引列處理問題，正確計算預測率總和
  - **驗證結果**：
    - Learning: Λ_PPE ≈ 27.00（目標 27 個事件）✓
    - Forecast: PPE ~14 + EEPAS ~16 = ~30（接近觀測值 27）✓
- 🚀 **自動化工作流程腳本**：
  - `run_full_workflow_two_periods.sh` - FAST 模式雙因果性設定完整流程
  - `run_full_workflow_two_periods_accurate.sh` - ACCURATE 模式雙因果性設定完整流程
  - `run_causal_ew_comparison.sh` - 因果性權重比較腳本
  - 支持 `--no-boundary-adjustment` 參數

### Changed
- 📚 **核心模組更新**：
  - `ppe_optimization.py` - 支持 ACCURATE/FAST 模式切換
  - `eepas_likelihood.py` - 統一使用 numerical_integration 模組
  - `ppe_make_forecast.py` - 支持 `--accurate` 參數
  - `eepas_make_forecast.py` - 支持 `--accurate` 參數
  - `fit_aftershock_params.py` - 支持 `--accurate` 參數
  - 所有數值積分呼叫統一介面
- 📖 **文檔更新**：
  - README.md 更新至 v1.3.0，強調數值積分驗證成果
  - CHANGELOG.md 詳細記錄重構過程和驗證結果
  - CLAUDE.md 新增 ACCURATE vs FAST 模式使用指南
  - CLAUDE.md 新增 Lambda 總和驗證方法說明
  - 配置列表更新（EW0/EW1 測試配置）

### Fixed
- 🐛 修正 Forecast Lambda 計算時未排除索引列的問題
- 🔧 統一數值積分呼叫方式，消除重複代碼
- 🔧 改善 EEPAS Learning 邊界調整策略

### Validated
- ✅ **數值積分重構驗證成功**：
  - 梯形法（FAST）與 dblquad（ACCURATE）結果高度一致
  - 所有測試配置的參數差異 < 0.2%
  - Lambda 積分驗證通過（Learning 和 Forecast 階段）
  - **結論**：重構後的數值積分實現正確，FAST 模式可安全用於日常研究

### Performance
- ⚡ FAST 模式相較 ACCURATE 模式：
  - PPE Learning: ~1.3x 加速
  - Aftershock Fitting: ~1.5x 加速
  - EEPAS Learning: ~1.3x 加速
  - PPE Forecast: ~4.0x 加速
  - EEPAS Forecast: ~4.0x 加速
  - **整體**: ~1.75x 加速

---

## [0.2.0] - 2025-10-30

### Added
- 🌍 **義大利模式完整支持與論文驗證**：
  - Testing Region 與 Neighborhood Region 區域管理
  - 所有模組支持義大利地震數據（PPE/EEPAS Learning/Forecast + Aftershock）
  - 符合 ggad123.pdf Equation 1 數學定義
  - ✅ **論文一致性驗證完成**：
    - PPE 和 EEPAS 預測公式與論文完全一致
    - mT anchor 支持（`--ppe-ref-mag mT --target-mag mT`）
    - 單輪優化模式（`--max-rounds 1`）匹配論文方法
    - 完整驗證結果在 `results_italy_paper_1round_full/`（已歸檔）
- ⚡ **性能優化**：
  - PPE Forecast 快速模式（Numba JIT）：快 60-70 倍，精度損失 <0.03%
  - EEPAS Forecast 優化：從 277 秒優化至 56 秒（5x 加速）
- 🧪 **完整驗證**：
  - 區域實現完全正確（源事件、目標事件、積分範圍）
  - 台灣模式向後相容 100%
  - 義大利模式參數結果與論文一致（1990-2012 學習期，2012-2022 預測期）

### Changed
- 📚 **文檔更新**：
  - README.md 新增論文驗證工作流程和最新成果
  - 新增義大利快速開始指南
  - 更新目錄結構說明

### Fixed
- 🐛 區域篩選邏輯完善（Testing vs Neighborhood）
- 🔧 義大利數據載入與處理

### Validated
- ✅ PPE 學習：a=0.616, d=29.64, s≈0（mT=5.0 anchor）
- ✅ Aftershock 參數：v=0.577, k=0.205
- ✅ EEPAS 參數：NLL=-495.41（8 個參數單輪優化）
- ✅ 數學公式驗證：PPE 和 EEPAS 預測邏輯與 ggad123.pdf 完全一致

---

## [0.1.0] - 2025-10-19

### Added
- 🔬 **優化器支援擴展**：
  - 新增 L-BFGS-B, TNC, SLSQP, Powell 優化器
  - Basin-Hopping 全局優化策略
  - Multistart 多起始點策略（可自訂起始點數量）
- 📊 **優化器比較研究**：
  - 完整的優化器比較報告 (OPTIMIZER_COMPARISON_REPORT.md)
  - 5 種優化器在 4 個配置上的系統性比較
  - 測試 Multistart (3/10 個起始點), Basin-Hopping, Hybrid 策略
- 🎯 **單階段優化模式**：
  - `--no-multistart` 參數支援單起始點優化
  - `--optimizer` 參數可選擇優化器
  - `--n-starts` 參數可自訂 multistart 起始點數量
  - `--basinhopping` 和 `--basinhopping-niter` 參數

### Changed
- ⚡ **收斂標準優化**：
  - 調整不同優化器的收斂容差以確保公平比較
  - scipy 梯度優化器使用相對 ftol，fmin 使用絕對 ftol
  - L-BFGS-B: ftol=1e-9, gtol=1e-7
  - SLSQP: ftol=1e-12
  - TNC: ftol=1e-9, gtol=1e-3

### Fixed
- 🐛 修正優化器收斂判據不一致的問題
- 🔧 改善邊界調整邏輯

### Research Findings
- ✅ **fminsearchcon (Nelder-Mead) 最穩健**（在所有配置上都能找到高質量解）
- ⚡ **梯度法速度快但不穩定**（50% 成功率，容易陷入局部最優）
- ❌ **Basin-Hopping 和大量 Multistart (>10) 對此問題無效**
- 💡 **推薦策略**：並行運行 fminsearchcon 和 L-BFGS-B + Multistart，取較好者

### Archived
- 📦 所有優化器測試資料移至 `archive/optimizer_tests_2025_10_19/`

---

## [0.0.1] - 2025-10-15

### Added
- 🎉 Initial release of Python implementation
- ✨ Complete EEPAS model implementation (PPE, EEPAS, Aftershock learning)
- 🚀 Automatic boundary adjustment for EEPAS learning
- 📊 Analysis tools:
  - Earthquake distribution analysis (6 vs 24 regions)
  - Weight analysis across 4 configurations
  - Region subdivision tool (6 → 24 regions)
- 🔧 Coordinate conversion tool (WGS84 ↔ TWD97)
- 📈 4 pre-configured setups:
  - Standard (m0=2.35)
  - Declustered (m0=2.05)
  - Include 921 earthquake (m0=2.35)
  - m0=2.05 variant
- 📚 Comprehensive documentation:
  - README.md with quick start guide
  - USAGE.md with detailed instructions
  - Analysis documentation in docs/
- 🧪 Full validation against MATLAB version (100% match)
- 🎯 Standalone python_src directory (no external dependencies)
- ⚡ Performance optimization with Numba JIT

### Changed
- Migrated all MATLAB analysis scripts to Python
- Refactored code structure for better organization
- Updated directory layout for professional project structure

### Fixed
- Boundary touching issues in EEPAS optimization
- Coordinate conversion precision (< 0.01m error)
- Path handling for cross-platform compatibility

### Technical
- Python 3.8+ support
- Dependencies: numpy, scipy, numba, pandas, h5py, matplotlib, pyproj
- MIT License
- Git-friendly structure with .gitignore

---

## [Unreleased]

### Planned Features
- GUI interface for parameter tuning
- Real-time earthquake monitoring integration
- Web API for forecast delivery
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Performance benchmarks
- Additional coordinate systems support

---

**Legend**:
- 🎉 Major milestone
- ✨ New feature
- 🚀 Enhancement
- 📊 Analysis/Tool
- 🔧 Utility
- 📚 Documentation
- 🧪 Testing
- 🐛 Bug fix
- ⚡ Performance
- 🔒 Security
