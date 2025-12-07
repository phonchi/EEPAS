# Sphinx 文檔冗餘清理報告

## 日期
2025-11-24

## 問題描述

### 原始問題
Sphinx 編譯的 API 文檔存在嚴重的**冗餘和重複**問題：

1. **Parameters 段落出現 2-3 次**（autodoc 自動生成 + 手動 RST 重複描述）
2. **Returns 段落出現 2-3 次**
3. **Examples 段落重複**
4. **Command-Line Interface 重複**

### 具體案例

以 `eepas_with_auto_boundary` 函數為例，原始文檔包含：

```rst
.. automodule:: eepas_learning_auto_boundary
   :members:
   :undoc-members:
   :show-inheritance:

Main Function
^^^^^^^^^^^^^

.. autofunction:: eepas_learning_auto_boundary.eepas_with_auto_boundary
   :no-index:

Parameters
~~~~~~~~~~

:param str config_file: Configuration file path
:param bool use_three_stage: Use 3-stage optimization strategy
...

Returns
~~~~~~~

:returns: Dictionary with 8 EEPAS parameters
:rtype: dict

Dictionary keys:
...

Example
~~~~~~~

.. code-block:: python

   params = eepas_with_auto_boundary(...)
   ...

Command-Line Interface
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py --config config.json
   ...

Three-Stage Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~
...
```

**問題**：
- `automodule` 已經從 docstring 生成了完整文檔
- 下面又手動重複了一次 Parameters, Returns, Example, CLI
- 導致 HTML 中相同內容重複 2 次

## 解決方案

### 核心原則

**只使用 `automodule` 自動生成文檔，移除所有手動重複的內容**

### 修改前後對比

#### core.rst

**修改前**：430 行（大量冗餘）

```rst
PPE Learning
------------

.. automodule:: ppe_learning
   :members:
   :undoc-members:
   :show-inheritance:

Main Function
^^^^^^^^^^^^^

.. autofunction:: ppe_learning.ppe_learning_tw_fast
   :no-index:

Parameters
~~~~~~~~~~

:param str config_file: Path to configuration JSON file (default: 'config.json')
:param int catalog_start_year: Catalog start year (overrides config if specified)
...
(重複 100+ 行)

Aftershock Parameter Fitting
-----------------------------

.. automodule:: fit_aftershock_params
   :members:
   :undoc-members:
   :show-inheritance:

Main Function
^^^^^^^^^^^^^

.. autofunction:: fit_aftershock_params.fit_aftershock_params_fast
   :no-index:

Parameters
~~~~~~~~~~
...
(重複 100+ 行)

... (重複 5 個模組)
```

**修改後**：63 行（**減少 85%**）

```rst
Core Modules
============

This page documents the main EEPAS workflow modules.

PPE Learning
------------

.. automodule:: ppe_learning
   :members:
   :undoc-members:
   :show-inheritance:

----

Aftershock Parameter Fitting
-----------------------------

.. automodule:: fit_aftershock_params
   :members:
   :undoc-members:
   :show-inheritance:

----

EEPAS Learning
--------------

.. automodule:: eepas_learning_auto_boundary
   :members:
   :undoc-members:
   :show-inheritance:

----

PPE Forecast
------------

.. automodule:: ppe_make_forecast
   :members:
   :undoc-members:
   :show-inheritance:

----

EEPAS Forecast
--------------

.. automodule:: eepas_make_forecast
   :members:
   :undoc-members:
   :show-inheritance:

----

See Also
--------

- :doc:`utils` - Utility modules used by core functions
- :doc:`../user_guide/workflows` - Complete workflow examples
- :doc:`../technical/optimization` - Optimization algorithm details
- :doc:`../technical/numerical_integration` - Integration method details
```

#### utils.rst

**修改前**：509 行（詳細的手動文檔）

```rst
Utility Modules
===============

Data Loader
-----------

The ``DataLoader`` class provides static methods for loading configuration files, earthquake catalogs, and spatial regions.

Configuration Loading
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: utils.data_loader.DataLoader
   :noindex:

.. automethod:: utils.data_loader.DataLoader.load_config

Load configuration from JSON file with automatic default value filling.

:param str config_file: Path to configuration JSON file (default: 'config.json')
:returns: Configuration dictionary
:rtype: dict
:raises FileNotFoundError: If config file doesn't exist

**Backward Compatibility**:
   Automatically converts old field names to new names:

   - ``horusFile`` → ``catalogFile``
   - ``cptiFile`` → ``neighborhoodRegionFile``
   - ``celleFile`` → ``testingRegionFile``

Example:

.. code-block:: python

   from utils.data_loader import DataLoader

   # Load configuration
   cfg = DataLoader.load_config('config.json')

   # Access fields
   print(f"Results directory: {cfg['resultsDir']}")
   print(f"Learning period: {cfg['learnStartYear']}-{cfg['learnEndYear']}")
   print(f"Completeness magnitude: {cfg['modelParams']['m0']}")

... (手動重複 400+ 行)
```

**修改後**：72 行（**減少 86%**）

```rst
Utility Modules
===============

This page documents utility modules that provide data loading, processing, and numerical integration functions.

Data Loader
-----------

.. automodule:: utils.data_loader
   :members:
   :undoc-members:
   :show-inheritance:

----

Catalog Processor
-----------------

.. automodule:: utils.catalog_processor
   :members:
   :undoc-members:
   :show-inheritance:

----

Region Manager
--------------

.. automodule:: utils.region_manager
   :members:
   :undoc-members:
   :show-inheritance:

----

Numerical Integration
---------------------

.. automodule:: utils.numerical_integration
   :members:
   :undoc-members:
   :show-inheritance:

----

Path Management
---------------

.. automodule:: utils.get_paths
   :members:
   :undoc-members:
   :show-inheritance:

----

Optimization Helpers
--------------------

.. automodule:: utils.fminsearchcon
   :members:
   :undoc-members:
   :show-inheritance:

----

See Also
--------

- :doc:`core` - Core modules that use these utilities
- :doc:`../technical/numerical_integration` - Detailed integration theory
- :doc:`../user_guide/configuration` - Configuration file reference
```

#### analysis.rst

**修改前**：61 行（相對簡潔）
**修改後**：77 行（**微調**，增加 See Also 和 References）

## 成果統計

### 檔案大小變化

| 檔案 | 修改前 (行數) | 修改後 (行數) | 減少比例 |
|------|--------------|--------------|----------|
| `docs/source/api_reference/core.rst` | 430 | 63 | **85%** |
| `docs/source/api_reference/utils.rst` | 509 | 72 | **86%** |
| `docs/source/api_reference/analysis.rst` | 61 | 77 | +26% (增加 See Also) |
| **總計** | **1000** | **212** | **79%** |

### 編譯結果

```bash
$ make -C docs html
...
build succeeded, 71 warnings.

The HTML pages are in build/html.
```

**警告數量**：71 (主要來自 notebook 標題問題，與此次清理無關)

### 生成的 HTML 大小

```bash
$ wc -l docs/build/html/api_reference/*.html
   945 docs/build/html/api_reference/core.html
  1492 docs/build/html/api_reference/utils.html
   833 docs/build/html/api_reference/analysis.html
  3270 total
```

## 文檔品質改善

### 修改前的問題

1. ❌ **冗餘嚴重**：相同內容重複 2-3 次
2. ❌ **維護困難**：修改一個參數需要同時更新 docstring 和 RST
3. ❌ **不一致風險**：手動 RST 和 docstring 可能出現不同步
4. ❌ **閱讀體驗差**：用戶需要跳過重複內容

### 修改後的優勢

1. ✅ **單一來源**：所有文檔來自 docstring（Single Source of Truth）
2. ✅ **易於維護**：只需維護 Python 代碼中的 docstring
3. ✅ **一致性保證**：autodoc 確保文檔與代碼同步
4. ✅ **閱讀流暢**：沒有重複，每個參數只出現一次
5. ✅ **符合最佳實踐**：遵循 Sphinx/autodoc 官方推薦用法

## Sphinx 配置說明

### conf.py 關鍵設定

```python
# Napoleon extension: 支援 Google/NumPy style docstrings
extensions = [
    'sphinx.ext.autodoc',        # 自動從 docstring 生成文檔
    'sphinx.ext.napoleon',       # 支援 Google/NumPy 風格
    'sphinx.ext.viewcode',       # 連結到源碼
    'sphinx.ext.mathjax',        # 數學公式渲染
]

# Napoleon 設定
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc 設定
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
```

### RST 文件最佳實踐

**✅ 推薦用法（單一來源）**：

```rst
Module Name
-----------

.. automodule:: module_name
   :members:
   :undoc-members:
   :show-inheritance:
```

**❌ 避免用法（冗餘）**：

```rst
Module Name
-----------

.. automodule:: module_name
   :members:
   :undoc-members:
   :show-inheritance:

Main Function
^^^^^^^^^^^^^

.. autofunction:: module_name.func
   :no-index:

Parameters
~~~~~~~~~~

:param str arg1: Description
:param int arg2: Description

Returns
~~~~~~~

:returns: Description
:rtype: type

Example
~~~~~~~

.. code-block:: python

   func(arg1='value', arg2=42)
```

## 相關檔案

### 修改的檔案

- `docs/source/api_reference/core.rst` (430 → 63 行)
- `docs/source/api_reference/utils.rst` (509 → 72 行)
- `docs/source/api_reference/analysis.rst` (61 → 77 行)

### 未修改的檔案

- `docs/source/conf.py` (配置正確，無需修改)
- `docs/source/index.rst` (主頁，無需修改)
- `docs/source/user_guide/*.rst` (用戶指南，非 API 文檔)
- `docs/source/technical/*.rst` (技術文檔，非 API 文檔)
- `docs/source/examples/*.rst` (範例文檔，非 API 文檔)

## 驗證結果

### HTML 文檔檢查

```bash
# 檢查編譯後的 HTML 是否正常
$ grep -c "Parameters" docs/build/html/api_reference/core.html
31  # 只在 autodoc 生成的部分出現（無重複）

# 檢查函數簽名是否完整
$ grep -c "eepas_with_auto_boundary" docs/build/html/api_reference/core.html
1  # 只出現一次（正確）
```

### 瀏覽器測試

打開 `docs/build/html/index.html` 驗證：

1. ✅ API Reference 頁面正常顯示
2. ✅ 每個函數只有一個 Parameters 段落
3. ✅ 每個函數只有一個 Returns 段落
4. ✅ 每個函數只有一個 Examples 段落
5. ✅ 源碼連結（[source]）正常工作
6. ✅ 導航和搜索功能正常

## 後續建議

### 短期（已完成）

- [x] 移除 API Reference 的所有冗餘內容
- [x] 驗證編譯結果正確
- [x] 確認 HTML 文檔無重複

### 長期維護

1. **只維護 docstring**：所有 API 文檔應在 Python 代碼中的 docstring 維護
2. **RST 保持簡潔**：只包含 `automodule` 指令和簡短說明
3. **定期檢查一致性**：確保 docstring 風格統一（Google/NumPy style）
4. **使用 type hints**：Python 代碼中使用 type hints，autodoc 會自動提取

### Docstring 品質標準

所有 Python 函數應遵循以下 docstring 格式：

```python
def function_name(arg1: str, arg2: int = 10) -> dict:
    """
    簡短描述（一行）。

    詳細描述（可選，多行）。
    可以包含數學公式、列表等。

    Args:
        arg1: 參數 1 的描述
        arg2: 參數 2 的描述（預設：10）

    Returns:
        返回值的描述。
        可以多行說明結構。

    Raises:
        ValueError: 何時拋出此錯誤
        FileNotFoundError: 何時拋出此錯誤

    Examples:
        >>> result = function_name('test', 20)
        >>> print(result)
        {'key': 'value'}

    Notes:
        額外的重要說明。

    See Also:
        other_function: 相關函數
        SomeClass: 相關類
    """
    pass
```

## 總結

本次清理完成了以下目標：

1. **移除 79% 的冗餘代碼**（1000 行 → 212 行）
2. **確保單一來源原則**：所有文檔來自 docstring
3. **改善維護性**：只需維護一處（docstring）
4. **提升用戶體驗**：每個參數只出現一次，無重複干擾
5. **符合最佳實踐**：遵循 Sphinx/autodoc 官方推薦

**結論**：文檔冗餘問題已完全解決，現在的文檔結構簡潔、易維護且符合業界標準。

---

**作者**：Claude Code
**日期**：2025-11-24
**版本**：v1.3.0
