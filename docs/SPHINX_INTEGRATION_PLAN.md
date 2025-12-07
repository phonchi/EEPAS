# Sphinx 文檔整合計劃

**日期**: 2025-11-24
**目標**: 將 analysis 模組 API 和三個示例 notebook 整合到 Sphinx 文檔

---

## 📋 當前狀態

### 現有文檔結構
```
docs/source/
├── index.rst
├── conf.py
├── api_reference/
│   ├── index.rst
│   ├── core.rst
│   └── utils.rst
├── user_guide/
│   ├── installation.rst
│   ├── quickstart.rst
│   ├── configuration.rst
│   ├── workflows.rst
│   └── results.rst
├── technical/
│   ├── mathematical_foundation.rst
│   ├── numerical_integration.rst
│   └── optimization.rst
└── development/
    └── changelog.rst
```

### 三個 Notebook 檔案
1. **Estimate_mc_b_Italy_clean.ipynb** (339 KB)
   - 用途: 估算完整度震級 (mc) 和 b 值
   - 內容: 使用 SeismoStats 套件估算參數
   - Code cells: 19, Markdown cells: 1

2. **Examine_Psi_Italy_clean.ipynb** (1.2 MB)
   - 用途: 檢查 Ψ 現象識別結果
   - 內容: 分析和視覺化 Ψ 現象
   - Code cells: 18, Markdown cells: 6

3. **earth_viz_Italy_clean.ipynb** (1.8 MB)
   - 用途: 地震視覺化和結果展示
   - 內容: 使用 pyCSEP 視覺化預測結果
   - Code cells: 52, Markdown cells: 21

---

## 🎯 整合目標

### 1. API 文檔整合
- ✅ 創建 `api_reference/analysis.rst` 包含所有 analysis 模組
- ✅ 自動生成 API 文檔從 docstrings
- ✅ 組織結構: Ψ Detection → Deduplication → Scaling Relations → Utilities

### 2. Notebook 範例整合
- ✅ 安裝 nbsphinx 擴展
- ✅ 創建 `examples/` 目錄結構
- ✅ 轉換 notebooks 為 Sphinx 相容格式
- ✅ 新增範例索引頁面

---

## 📐 實施計劃

### Phase 1: 安裝依賴 ✅

```bash
pip install nbsphinx pandoc ipykernel
```

### Phase 2: 更新 conf.py ✅

新增擴展：
```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'nbsphinx',  # ← 新增
]

# nbsphinx 配置
nbsphinx_execute = 'never'  # 不執行 notebook (已有輸出)
nbsphinx_allow_errors = True
nbsphinx_kernel_name = 'python3'
```

### Phase 3: 創建 API 文檔 ✅

**檔案**: `docs/source/api_reference/analysis.rst`

```rst
Analysis Modules
================

The analysis module provides tools for Ψ phenomenon detection, deduplication,
and scaling relation analysis.

.. contents:: Table of Contents
   :local:
   :depth: 2

Ψ Phenomenon Detection
----------------------

Core algorithm for detecting precursory scale increase (Ψ) phenomenon using the
rectangular algorithm from Christophersen et al. (2024).

.. automodule:: analysis.optimize_psi_working
   :members:
   :undoc-members:
   :show-inheritance:

Main Functions
^^^^^^^^^^^^^^

.. autofunction:: analysis.optimize_psi_working.optimize_psi

.. autofunction:: analysis.optimize_psi_working.trimcycle_early

.. autofunction:: analysis.optimize_psi_working.parameters_select

Helper Functions
^^^^^^^^^^^^^^^^

.. autofunction:: analysis.optimize_psi_working._cum_mag

.. autofunction:: analysis.optimize_psi_working._load_catalog

Deduplication (Step 9)
----------------------

Two-stage deduplication procedure to remove duplicate Ψ identifications.

.. automodule:: analysis.optimize_psi_results
   :members:
   :undoc-members:

Main Function
^^^^^^^^^^^^^

.. autofunction:: analysis.optimize_psi_results.optimize_psi_results

Helper Functions
^^^^^^^^^^^^^^^^

.. autofunction:: analysis.optimize_psi_results._run_once_round

.. autofunction:: analysis.optimize_psi_results._run_once_tolerance

Scaling Relations Analysis
--------------------------

Analyze scaling relations using fixed-effects regression to estimate initial
parameter values for the EEPAS model.

.. automodule:: analysis.plot_relations
   :members:
   :undoc-members:

Main Function
^^^^^^^^^^^^^

.. autofunction:: analysis.plot_relations.analyze_scaling_relations

Helper Functions
^^^^^^^^^^^^^^^^

.. autofunction:: analysis.plot_relations._fixed_effects_slope_safe

.. autofunction:: analysis.plot_relations.prediction_interval

Utility Modules
---------------

Dataset Extraction
^^^^^^^^^^^^^^^^^^

.. automodule:: analysis.dataset
   :members:
   :undoc-members:

Time Conversion
^^^^^^^^^^^^^^^

.. automodule:: analysis.decimal_time
   :members:
   :undoc-members:

Event Selection
^^^^^^^^^^^^^^^

.. automodule:: analysis.select_m5plus
   :members:
   :undoc-members:
```

### Phase 4: 創建 Examples 結構 ✅

**目錄結構**:
```
docs/source/examples/
├── index.rst
├── preprocessing/
│   ├── estimate_mc_b.ipynb (符號連結)
│   └── index.rst
├── analysis/
│   ├── examine_psi.ipynb (符號連結)
│   └── index.rst
└── visualization/
    ├── earthquake_viz.ipynb (符號連結)
    └── index.rst
```

**檔案**: `docs/source/examples/index.rst`

```rst
Examples and Tutorials
======================

This section provides practical examples demonstrating how to use the EEPAS
package for earthquake forecasting analysis.

.. note::
   These examples use the Italy region (HORUS catalog) for demonstration.
   The same workflows can be applied to other regions with appropriate
   catalog data.

Example Categories
------------------

.. toctree::
   :maxdepth: 2

   preprocessing/index
   analysis/index
   visualization/index

Quick Links
-----------

**Preprocessing Examples**
   Learn how to prepare earthquake catalogs and estimate key parameters.

**Analysis Examples**
   Explore Ψ phenomenon detection and scaling relations analysis.

**Visualization Examples**
   Create publication-quality maps and plots for forecast evaluation.

Data Requirements
-----------------

The examples use the following datasets:

- **HORUS Catalog**: Homogenized instrumental seismic catalog for Italy (1960-present)
- **CPTI15**: Italian Parametric Earthquake Catalog
- **Region Files**: Testing region (177 cells) and neighborhood region (polygon)

See :doc:`/user_guide/installation` for data download instructions.
```

### Phase 5: 創建各分類索引 ✅

**檔案**: `docs/source/examples/preprocessing/index.rst`

```rst
Preprocessing Examples
======================

Examples for data preparation and parameter estimation.

Estimating mc and b-value
--------------------------

This notebook demonstrates how to:

- Load earthquake catalogs (MAT format or CSV)
- Apply quality filters (depth, magnitude, time range)
- Estimate completeness magnitude (mc) using multiple methods
- Calculate b-value using various estimators (Utsu, b-positive, b-more-positive)
- Use the SeismoStats package for robust parameter estimation

.. toctree::
   :maxdepth: 1

   Estimate_mc_b_Italy_clean

Key Techniques
^^^^^^^^^^^^^^

- **mc Estimation Methods**:

  - Maximum Curvature (MAXC)
  - b-value Stability
  - Kolmogorov-Smirnov Test

- **b-value Estimators**:

  - Utsu (1965): Maximum likelihood
  - b-positive: Corrected for positive bias
  - b-more-positive: Enhanced correction for small samples

Prerequisites
^^^^^^^^^^^^^

.. code-block:: bash

   pip install pycsep seismostats
```

**檔案**: `docs/source/examples/analysis/index.rst`

```rst
Analysis Examples
=================

Examples for Ψ phenomenon detection and scaling relations analysis.

Examining Ψ Identifications
----------------------------

This notebook demonstrates how to:

- Run the rectangular algorithm to detect Ψ phenomena
- Apply Step 9 deduplication (two-stage filtering)
- Analyze scaling relations using fixed-effects regression
- Generate initial parameter estimates for EEPAS model
- Visualize Ψ identifications on maps

.. toctree::
   :maxdepth: 1

   Examine_Psi_Italy_clean

Key Concepts
^^^^^^^^^^^^

**Ψ Phenomenon**
   Precursory scale increase before major earthquakes, characterized by:

   - Increased seismicity rate
   - Magnitude increase (MP)
   - Spatial clustering (AP)
   - Lead time (TP)

**Rectangular Algorithm**
   Automated detection procedure (Christophersen et al., 2024):

   - Step 1: T-loop (shrink lead-up time)
   - Steps 2-9: R-loop (shrink radius, increase mc)
   - Selection criteria: r≥3, MP-M-≥0.4, Mm-MP≥0.4

**Deduplication (Step 9)**
   Two-stage filtering:

   - Step 9.1: For same (eq_name, tmin, tp, mp) → keep max sloperatio
   - Step 9.2: For same (eq_name, tp, r) → keep min ap

Related API
^^^^^^^^^^^

- :py:func:`analysis.optimize_psi_working.optimize_psi`
- :py:func:`analysis.optimize_psi_results.optimize_psi_results`
- :py:func:`analysis.plot_relations.analyze_scaling_relations`
```

**檔案**: `docs/source/examples/visualization/index.rst`

```rst
Visualization Examples
======================

Examples for creating maps, plots, and forecast visualizations.

Earthquake Visualization and Forecast Evaluation
-------------------------------------------------

This notebook demonstrates how to:

- Create spatial distribution maps of earthquakes
- Plot cumulative number vs time
- Generate magnitude-frequency distributions
- Visualize forecast grids using pyCSEP
- Apply CSEP consistency tests (N-test, S-test, M-test)
- Compare PPE and EEPAS model performance

.. toctree::
   :maxdepth: 1

   earth_viz_Italy_clean

Visualization Types
^^^^^^^^^^^^^^^^^^^

**Spatial Maps**
   - Epicenter locations with magnitude scaling
   - Testing region boundaries
   - Forecast rate heatmaps
   - Cartopy integration for professional maps

**Temporal Plots**
   - Cumulative number of earthquakes over time
   - Rate density evolution
   - Forecast vs observation comparison

**Statistical Plots**
   - Magnitude-frequency distributions (Gutenberg-Richter)
   - Quantile-quantile plots for consistency tests
   - Receiver Operating Characteristic (ROC) curves

**Forecast Evaluation**
   - CSEP consistency tests visualization
   - Model comparison diagrams
   - Skill score plots

pyCSEP Integration
^^^^^^^^^^^^^^^^^^

This notebook uses the pyCSEP framework for:

- Reading forecast files in CSEP format
- Applying statistical tests
- Generating publication-quality figures

See the `pyCSEP documentation <https://docs.cseptesting.org/>`_ for details.
```

### Phase 6: 更新主索引 ✅

**更新**: `docs/source/index.rst`

在 toctree 中新增：
```rst
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_guide/installation
   user_guide/quickstart
   user_guide/configuration
   user_guide/workflows
   user_guide/results
   api_reference/index
   examples/index        # ← 新增
   technical/mathematical_foundation
   technical/numerical_integration
   technical/optimization
   development/changelog
```

**更新**: `docs/source/api_reference/index.rst`

```rst
API Reference
=============

Complete API documentation for all EEPAS modules.

.. toctree::
   :maxdepth: 2

   core
   utils
   analysis  # ← 新增
```

### Phase 7: 創建符號連結 ✅

```bash
cd docs/source/examples/preprocessing/
ln -s ../../../../analysis/Estimate_mc_b_Italy_clean.ipynb .

cd ../analysis/
ln -s ../../../../analysis/Examine_Psi_Italy_clean.ipynb .

cd ../visualization/
ln -s ../../../../analysis/earth_viz_Italy_clean.ipynb .
```

### Phase 8: 測試構建 ✅

```bash
cd docs
make clean
make html

# 檢查警告
make html 2>&1 | grep -i warning

# 檢查生成的 HTML
firefox build/html/index.html
```

---

## 📝 額外改進（可選）

### 清理 Notebooks
- 移除 Google Colab 特定單元格 (drive.mount, !cp)
- 新增 Markdown 描述單元格
- 確保輸出已保存（圖表、結果）

### 新增 Cross-References
在文檔中新增交叉引用：
```rst
See :doc:`/examples/analysis/Examine_Psi_Italy_clean` for a complete example.
See :py:func:`analysis.optimize_psi_working.optimize_psi` for API details.
```

### 新增下載連結
提供 notebook 下載連結：
```rst
:download:`Download this notebook </examples/analysis/Examine_Psi_Italy_clean.ipynb>`
```

---

## ✅ 驗證清單

- [ ] conf.py 更新完成
- [ ] api_reference/analysis.rst 創建完成
- [ ] examples/ 目錄結構創建完成
- [ ] 所有 index.rst 文件創建完成
- [ ] 符號連結創建完成
- [ ] Sphinx 構建成功（無錯誤）
- [ ] API 文檔正確顯示
- [ ] Notebooks 正確渲染
- [ ] 交叉引用正常工作
- [ ] HTML 輸出檢查完成

---

## 📚 參考資料

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [nbsphinx](https://nbsphinx.readthedocs.io/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/)
- [PyCSEP Documentation](https://docs.cseptesting.org/)
- [SeismoStats Documentation](https://seismostats.readthedocs.io/)

---

**計劃狀態**: 準備執行
**預計時間**: 30-45 分鐘
**優先級**: 高（完成文檔整合）
