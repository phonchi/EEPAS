# convert_to_rdn2008.py 翻譯與文檔更新摘要

## 完成事項

### 1. ✅ 程式碼翻譯為英文

**翻譯範圍：**
- 模組 docstring（檔案頂部說明）
- 所有函數 docstring
- 所有註解
- 所有 print 訊息
- 命令列說明文字

**保持一致的命名：**
- `convert_coordinates()`: 轉換 HORUS 目錄座標
- `convert_celle_coordinates()`: 轉換 CELLE 網格邊界
- `main()`: 主要轉換流程

### 2. ✅ 添加 Google-style Docstring

所有函數都添加了完整的 Google-style docstring，包含：

**convert_coordinates()**
```python
"""
Convert geographic coordinates to RDN2008 projected coordinates.

Args:
    array (np.ndarray): Array containing geographic coordinate data.
    lon_idx (int): Column index for longitude values.
    lat_idx (int): Column index for latitude values.
    transformer (pyproj.Transformer): Coordinate transformation object.
    meters_per_km (float, optional): Meters to kilometers conversion factor.
        Defaults to 1000.0.

Returns:
    np.ndarray: Transformed array with projected coordinates in kilometers.

Warns:
    UserWarning: If coordinates are outside valid range for Italy region.

Examples:
    >>> transformer = Transformer.from_crs('epsg:4326', 'epsg:7794', always_xy=True)
    >>> horus_rdn = convert_coordinates(horus_data, 7, 6, transformer)
"""
```

**convert_celle_coordinates()**
- 完整的參數說明
- 返回值描述
- Notes 說明 CELLE 格式規範
- 使用範例

**main()**
- 詳細的參數說明
- 可能拋出的異常
- 重要注意事項（欄位索引、變數名稱、座標系統）
- 完整的使用範例

### 3. ✅ 加入 Sphinx 文檔

#### 更新 `api_reference/utils.rst`

添加新章節：

```rst
Coordinate Transformation
-------------------------

.. automodule:: utils.convert_to_rdn2008
   :members:
   :undoc-members:
   :show-inheritance:

This module provides coordinate system conversion utilities for transforming Italian
seismic data from WGS84 geographic coordinates to RDN2008 projected coordinates.

**Key Functions:**

- convert_coordinates(): Transform HORUS catalog coordinates
- convert_celle_coordinates(): Transform CELLE grid boundaries
- main(): Main conversion routine for both files

**Coordinate Systems:**

- Source: EPSG:4326 (WGS84 geographic coordinates)
- Target: EPSG:7794 (RDN2008 / Italy zone projected coordinates)
- Units: Output coordinates in kilometers

**Usage Example:**

.. code-block:: bash

   # Convert HORUS and CELLE files to RDN2008
   python -m utils.convert_to_rdn2008 \
       --horus-in data/HORUS_Italy.mat \
       --celle-in data/CELLE_Italy.mat \
       --horus-out data/HORUS_Italy_RDN2008.mat \
       --celle-out data/CELLE_Italy_RDN2008.mat
```

#### 更新 `user_guide/installation.rst`

添加可選依賴章節：

```rst
Geospatial Libraries (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Required for coordinate transformation utilities (Italy dataset):

.. code-block:: text

   pyproj>=3.0.0        # Coordinate system transformations

**Usage:** The :mod:`utils.convert_to_rdn2008` module requires ``pyproj`` to convert
Italian HORUS/CELLE data from WGS84 to RDN2008 projected coordinates.

To install:

.. code-block:: bash

   pip install pyproj
```

## 文檔生成驗證

### ✅ Sphinx 編譯成功
```
build succeeded, 25 warnings.
```

### ✅ 模組正確加入目錄
生成的 HTML 包含：
- Coordinate Transformation 章節
- 三個函數的完整文檔
- 函數簽名和參數說明
- 使用範例

### ✅ HTML 輸出檢查
```html
<h2>Coordinate Transformation</h2>
<p>Coordinate System Converter for Italian Seismic Data</p>

<dt id="utils.convert_to_rdn2008.convert_coordinates">
<span class="sig-name descname">convert_coordinates</span>
(array, lon_idx, lat_idx, transformer, meters_per_km=1000.0)
</dt>
```

## 檔案變更清單

### 程式碼檔案
- `utils/convert_to_rdn2008.py`: 完整翻譯為英文，添加 Google-style docstring

### 文檔檔案
- `docs/source/api_reference/utils.rst`: 新增 Coordinate Transformation 章節
- `docs/source/user_guide/installation.rst`: 新增 pyproj 可選依賴說明

## 技術細節

### 座標轉換規格
- **輸入**: WGS84 經緯度 (EPSG:4326)
  - HORUS: 第7欄 (索引6) = 緯度，第8欄 (索引7) = 經度
  - CELLE: [lon_min, lon_max, lat_min, lat_max]

- **輸出**: RDN2008 投影座標 (EPSG:7794)
  - 單位：公里
  - 東向 (Easting): x 座標
  - 北向 (Northing): y 座標

### 使用的函式庫
- `scipy.io`: 讀寫 MATLAB .mat 檔案
- `pyproj`: 座標系統轉換
- `numpy`: 數值運算
- `argparse`: 命令列介面

### 驗證機制
- 座標範圍檢查（義大利地區：35-48°N, 6-20°E）
- 無效座標警告
- 轉換前後座標範圍顯示

## 總結

✅ **程式碼翻譯**: 完整英文化
✅ **Docstring**: 符合 Google-style 標準
✅ **文檔整合**: 成功加入 Sphinx API 文檔
✅ **依賴說明**: 添加 pyproj 安裝指南
✅ **編譯驗證**: 無新增錯誤，25 warnings（與之前一致）

**編譯狀態**: `build succeeded, 25 warnings.`
**新增模組**: `utils.convert_to_rdn2008`
**文檔位置**: `api_reference/utils.html#coordinate-transformation`
