# CatalogProcessor 多格式支援擴展計劃

**日期**: 2025-11-26
**目的**: 擴展 `utils.catalog_processor.CatalogProcessor` 支援多種常見地震目錄格式

---

## 📋 目標格式

### 1. ZMAP 格式
- **來源**: [ObsPy ZMAP Documentation](https://docs.obspy.org/packages/obspy.io.zmap.html)
- **欄位定義** (10 columns):
  1. Longitude (經度)
  2. Latitude (緯度)
  3. Decimal year (十進位年份)
  4. Month (月)
  5. Day (日)
  6. Magnitude (震級)
  7. Depth (深度，km)
  8. Hour (時)
  9. Minute (分)
  10. Second (秒)
- **格式**: Tab-separated 或 space-separated text file
- **變體**: 可能有 13 columns（額外 3 個欄位通常是誤差資訊）

### 2. OpenQuake 格式
- **來源**: [SeismoStats OpenQuake](https://seismostats.readthedocs.io/v1.0.0/user/catalogs.html)
- **欄位定義**:
  - eventID (可選)
  - longitude, latitude, depth
  - year, month, day, hour, minute, second
  - magnitude
- **格式**: Python 物件（需要 `openquake` 套件）或 CSV/DataFrame
- **轉換**: 需要實作 `from_openquake()` 轉換方法

### 3. CSEP ASCII 格式
- **來源**: [PyCSEP Catalogs](https://docs.cseptesting.org/concepts/catalogs.html)
- **欄位定義**:
  - longitude, latitude, magnitude, origin_time (ISO format), depth
- **格式**: Space-separated text file with header

### 4. Pandas DataFrame
- **來源**: 通用 Python 資料格式
- **必需欄位**:
  - longitude (或 lon)
  - latitude (或 lat)
  - magnitude (或 mag)
  - time (datetime 或 decimal year)
  - depth (可選，預設 10 km)
- **支援格式**: CSV, Excel, JSON, Parquet 等

### 5. 當前 HORUS 格式 (保持向後相容)
- **欄位定義** (10 columns):
  1. Year
  2. Month
  3. Day
  4. Hour
  5. Minute
  6. Second
  7. Latitude
  8. Longitude
  9. Depth
  10. Magnitude
  11. (可選) Decimal year / relative time

---

## 🏗️ 架構設計

### 設計原則

1. **統一內部格式**: 所有外部格式轉換為標準 HORUS 格式（10-11 columns）
2. **向後相容**: 保持現有程式碼完全不變
3. **模組化設計**: 每種格式有獨立的讀取和轉換函數
4. **自動偵測**: 根據檔案內容自動判斷格式
5. **錯誤處理**: 清晰的錯誤訊息和資料驗證

### 核心架構

```python
class CatalogProcessor:
    # ========== 現有方法 (不變) ==========
    @staticmethod
    def preprocess_catalog(...)  # 保持不變

    @staticmethod
    def create_catalogs(...)  # 保持不變

    # ... 其他現有方法 ...

    # ========== 新增：格式讀取器 ==========
    @staticmethod
    def load_catalog(file_path, format='auto', **kwargs):
        """
        統一的目錄載入介面，支援多種格式

        Args:
            file_path: 檔案路徑或 DataFrame
            format: 'auto', 'horus', 'zmap', 'csep', 'openquake', 'dataframe'
            **kwargs: 格式特定參數

        Returns:
            numpy.ndarray: HORUS 格式的目錄 (10-11 columns)
        """

    # ========== 新增：格式轉換器 ==========
    @staticmethod
    def from_zmap(file_path):
        """讀取 ZMAP 格式並轉換為 HORUS 格式"""

    @staticmethod
    def from_csep(file_path):
        """讀取 CSEP ASCII 格式並轉換為 HORUS 格式"""

    @staticmethod
    def from_openquake(catalog_obj):
        """從 OpenQuake Catalogue 物件轉換為 HORUS 格式"""

    @staticmethod
    def from_dataframe(df, column_mapping=None):
        """從 Pandas DataFrame 轉換為 HORUS 格式"""

    @staticmethod
    def from_horus_mat(file_path):
        """讀取 MATLAB .mat 格式 (現有邏輯抽取)"""

    # ========== 新增：格式偵測器 ==========
    @staticmethod
    def detect_format(file_path):
        """自動偵測檔案格式"""

    # ========== 新增：格式驗證器 ==========
    @staticmethod
    def validate_catalog(catalog):
        """驗證目錄資料的完整性和正確性"""
```

---

## 📝 詳細實作計劃

### Phase 1: 核心架構 (優先)

#### 1.1 統一載入介面

```python
@staticmethod
def load_catalog(file_path, format='auto', **kwargs):
    """
    統一的目錄載入介面

    Args:
        file_path: str or pd.DataFrame
        format: 'auto', 'horus', 'zmap', 'csep', 'openquake', 'dataframe'
        **kwargs:
            - column_mapping (for dataframe)
            - header_lines (for text files)
            - delimiter (for text files)

    Returns:
        np.ndarray: HORUS format catalog (10 columns minimum)

    Examples:
        >>> # 自動偵測
        >>> cat = CatalogProcessor.load_catalog('catalog.txt')

        >>> # 明確指定格式
        >>> cat = CatalogProcessor.load_catalog('data.zmap', format='zmap')

        >>> # 從 DataFrame
        >>> cat = CatalogProcessor.load_catalog(df, format='dataframe',
        ...     column_mapping={'lon': 'longitude', 'lat': 'latitude'})
    """

    # 處理 DataFrame 輸入
    if isinstance(file_path, pd.DataFrame):
        return CatalogProcessor.from_dataframe(file_path, **kwargs)

    # 自動偵測格式
    if format == 'auto':
        format = CatalogProcessor.detect_format(file_path)
        print(f"Auto-detected format: {format}")

    # 根據格式調用對應的轉換器
    if format == 'horus':
        return CatalogProcessor.from_horus_mat(file_path)
    elif format == 'zmap':
        return CatalogProcessor.from_zmap(file_path)
    elif format == 'csep':
        return CatalogProcessor.from_csep(file_path)
    elif format == 'openquake':
        return CatalogProcessor.from_openquake(file_path)
    else:
        raise ValueError(f"Unsupported format: {format}")
```

#### 1.2 格式自動偵測

```python
@staticmethod
def detect_format(file_path):
    """
    自動偵測檔案格式

    偵測邏輯:
    1. 檔案副檔名: .mat → horus, .zmap → zmap
    2. 檔案內容分析:
       - 讀取前 5 行
       - 檢查欄位數量
       - 檢查第一個欄位範圍 (經度 vs 年份)

    Returns:
        str: 'horus', 'zmap', 'csep', 'unknown'
    """
    ext = os.path.splitext(file_path)[1].lower()

    # 根據副檔名
    if ext == '.mat':
        return 'horus'
    elif ext == '.zmap':
        return 'zmap'

    # 讀取文字檔案分析
    try:
        with open(file_path, 'r') as f:
            # 跳過可能的 header
            lines = []
            for _ in range(10):
                line = f.readline().strip()
                if line and not line.startswith('#'):
                    lines.append(line)
                if len(lines) >= 5:
                    break

        if not lines:
            return 'unknown'

        # 分析第一行
        first_line = lines[0]
        parts = first_line.split()

        if len(parts) < 6:
            return 'unknown'

        # 嘗試解析第一個數字
        first_val = float(parts[0])

        # ZMAP: 第一欄是經度 (-180 ~ 180)
        if -180 <= first_val <= 180 and len(parts) >= 10:
            # 檢查第三欄是否為年份 (>1900)
            third_val = float(parts[2])
            if third_val > 1900:
                return 'zmap'

        # HORUS: 第一欄是年份 (>1900)
        if first_val > 1900 and len(parts) >= 10:
            return 'horus'

        # CSEP: 檢查是否有 ISO 時間格式
        if any('T' in part and '-' in part for part in parts):
            return 'csep'

        return 'unknown'

    except Exception as e:
        print(f"Warning: Format detection failed: {e}")
        return 'unknown'
```

---

### Phase 2: 格式轉換器實作

#### 2.1 ZMAP 格式轉換

```python
@staticmethod
def from_zmap(file_path, delimiter=None):
    """
    讀取 ZMAP 格式並轉換為 HORUS 格式

    ZMAP format (10 columns):
    lon, lat, year, month, day, mag, depth, hour, minute, second

    HORUS format (10 columns):
    year, month, day, hour, minute, second, lat, lon, depth, mag

    Args:
        file_path: ZMAP 檔案路徑
        delimiter: 分隔符號 (None=自動偵測, ' ', '\t', ',')

    Returns:
        np.ndarray: HORUS format catalog
    """
    # 讀取資料（跳過可能的 header）
    try:
        # 先嘗試讀取第一行判斷格式
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('#'):
                skiprows = 1
            else:
                skiprows = 0

        # 自動偵測分隔符
        if delimiter is None:
            if '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = None  # numpy 預設處理空白

        # 讀取資料
        data = np.loadtxt(file_path, delimiter=delimiter, skiprows=skiprows)

        if data.ndim == 1:
            data = data.reshape(1, -1)

        # 檢查欄位數量
        if data.shape[1] < 10:
            raise ValueError(f"ZMAP file must have at least 10 columns, got {data.shape[1]}")

        # 只取前 10 欄
        data = data[:, :10]

        # ZMAP: lon, lat, year, month, day, mag, depth, hour, minute, second
        # HORUS: year, month, day, hour, minute, second, lat, lon, depth, mag

        lon = data[:, 0]
        lat = data[:, 1]
        year = data[:, 2]
        month = data[:, 3]
        day = data[:, 4]
        mag = data[:, 5]
        depth = data[:, 6]
        hour = data[:, 7]
        minute = data[:, 8]
        second = data[:, 9]

        # 重新排列為 HORUS 格式
        horus = np.column_stack([
            year, month, day, hour, minute, second,  # Time (cols 0-5)
            lat, lon, depth, mag  # Space & magnitude (cols 6-9)
        ])

        print(f"✅ Loaded ZMAP catalog: {horus.shape[0]} events")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read ZMAP file {file_path}: {e}")
```

#### 2.2 CSEP ASCII 格式轉換

```python
@staticmethod
def from_csep(file_path):
    """
    讀取 CSEP ASCII 格式並轉換為 HORUS 格式

    CSEP format:
    lon lat mag origin_time depth

    origin_time: ISO format (YYYY-MM-DDTHH:MM:SS.fff)

    Args:
        file_path: CSEP 檔案路徑

    Returns:
        np.ndarray: HORUS format catalog
    """
    from datetime import datetime

    events = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                lon = float(parts[0])
                lat = float(parts[1])
                mag = float(parts[2])
                time_str = parts[3]
                depth = float(parts[4]) if len(parts) > 4 else 10.0

                # 解析 ISO 時間
                # 格式: YYYY-MM-DDTHH:MM:SS 或 YYYY-MM-DDTHH:MM:SS.fff
                dt = datetime.fromisoformat(time_str.replace('Z', ''))

                # 轉換為 HORUS 格式
                events.append([
                    dt.year, dt.month, dt.day,
                    dt.hour, dt.minute, dt.second + dt.microsecond / 1e6,
                    lat, lon, depth, mag
                ])

            except Exception as e:
                print(f"Warning: Failed to parse line: {line} ({e})")
                continue

    if not events:
        raise ValueError(f"No valid events found in CSEP file: {file_path}")

    horus = np.array(events)
    print(f"✅ Loaded CSEP catalog: {horus.shape[0]} events")
    return horus
```

#### 2.3 DataFrame 格式轉換

```python
@staticmethod
def from_dataframe(df, column_mapping=None):
    """
    從 Pandas DataFrame 轉換為 HORUS 格式

    Args:
        df: Pandas DataFrame
        column_mapping: dict, 欄位對應關係
            例: {'lon': 'longitude', 'lat': 'latitude', 'mag': 'magnitude'}

    Required columns (after mapping):
        - longitude (or lon)
        - latitude (or lat)
        - magnitude (or mag)
        - time: datetime object, decimal year, or (year, month, day, ...)
        - depth (optional, default 10 km)

    Returns:
        np.ndarray: HORUS format catalog
    """
    import pandas as pd

    df = df.copy()

    # 應用欄位對應
    if column_mapping:
        df = df.rename(columns=column_mapping)

    # 標準化欄位名稱
    if 'lon' in df.columns and 'longitude' not in df.columns:
        df['longitude'] = df['lon']
    if 'lat' in df.columns and 'latitude' not in df.columns:
        df['latitude'] = df['lat']
    if 'mag' in df.columns and 'magnitude' not in df.columns:
        df['magnitude'] = df['mag']

    # 檢查必需欄位
    required = ['longitude', 'latitude', 'magnitude']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # 處理時間欄位
    if 'time' in df.columns:
        # 如果是 datetime 物件
        if pd.api.types.is_datetime64_any_dtype(df['time']):
            dt = pd.to_datetime(df['time'])
            year = dt.dt.year
            month = dt.dt.month
            day = dt.dt.day
            hour = dt.dt.hour
            minute = dt.dt.minute
            second = dt.dt.second + dt.dt.microsecond / 1e6
        # 如果是 decimal year
        elif pd.api.types.is_numeric_dtype(df['time']):
            # 需要轉換 decimal year → calendar date
            year, month, day, hour, minute, second = \
                CatalogProcessor._decimal_year_to_calendar(df['time'].values)
        else:
            raise ValueError("Unsupported time format in DataFrame")

    # 或者分別提供年月日
    elif all(col in df.columns for col in ['year', 'month', 'day']):
        year = df['year']
        month = df['month']
        day = df['day']
        hour = df.get('hour', 0)
        minute = df.get('minute', 0)
        second = df.get('second', 0.0)
    else:
        raise ValueError("DataFrame must have 'time' column or (year, month, day) columns")

    # 處理深度
    depth = df['depth'] if 'depth' in df.columns else 10.0

    # 組合成 HORUS 格式
    horus = np.column_stack([
        year, month, day, hour, minute, second,
        df['latitude'], df['longitude'], depth, df['magnitude']
    ])

    print(f"✅ Converted DataFrame to HORUS: {horus.shape[0]} events")
    return horus

@staticmethod
def _decimal_year_to_calendar(decimal_years):
    """
    將 decimal year 轉換為日曆日期

    Args:
        decimal_years: np.array of decimal years

    Returns:
        tuple: (year, month, day, hour, minute, second)
    """
    from datetime import datetime, timedelta

    n = len(decimal_years)
    year = np.zeros(n, dtype=int)
    month = np.zeros(n, dtype=int)
    day = np.zeros(n, dtype=int)
    hour = np.zeros(n, dtype=int)
    minute = np.zeros(n, dtype=int)
    second = np.zeros(n, dtype=float)

    for i, dy in enumerate(decimal_years):
        y = int(dy)
        fraction = dy - y

        start_of_year = datetime(y, 1, 1)
        days_in_year = (datetime(y + 1, 1, 1) - start_of_year).days

        day_of_year = fraction * days_in_year
        dt = start_of_year + timedelta(days=day_of_year)

        year[i] = dt.year
        month[i] = dt.month
        day[i] = dt.day
        hour[i] = dt.hour
        minute[i] = dt.minute
        second[i] = dt.second + dt.microsecond / 1e6

    return year, month, day, hour, minute, second
```

#### 2.4 OpenQuake 格式轉換

```python
@staticmethod
def from_openquake(catalog_obj):
    """
    從 OpenQuake Catalogue 物件轉換為 HORUS 格式

    Args:
        catalog_obj: OpenQuake Catalogue object

    Returns:
        np.ndarray: HORUS format catalog

    Requires:
        openquake.hmtk package installed
    """
    try:
        # 提取所需欄位
        events = []

        for event in catalog_obj.data:
            year = event.year
            month = event.month
            day = event.day
            hour = event.hour
            minute = event.minute
            second = event.second
            lat = event.latitude
            lon = event.longitude
            depth = event.depth
            mag = event.magnitude

            events.append([
                year, month, day, hour, minute, second,
                lat, lon, depth, mag
            ])

        horus = np.array(events)
        print(f"✅ Converted OpenQuake catalog: {horus.shape[0]} events")
        return horus

    except ImportError:
        raise ImportError(
            "OpenQuake format requires 'openquake.hmtk' package. "
            "Install with: pip install openquake.engine"
        )
    except Exception as e:
        raise ValueError(f"Failed to convert OpenQuake catalog: {e}")
```

---

### Phase 3: 整合到現有系統

#### 3.1 修改 `data_loader.py`

在 `DataLoader.load_catalogs()` 中整合新的載入器：

```python
@staticmethod
def load_catalogs(input_arg):
    """
    載入地震目錄和區域檔案（支援多種格式）

    Args:
        input_arg: 配置檔案路徑 (.json)

    Returns:
        tuple: (catalog, neighborhood_region, testing_region)
    """
    if input_arg.endswith('.json'):
        cfg = DataLoader.load_config(input_arg)
        data_path = cfg['dataDir']

        # 解析路徑
        if not os.path.isabs(data_path):
            config_dir = os.path.dirname(os.path.abspath(input_arg))
            data_path = os.path.join(config_dir, data_path)

        catalog_file = os.path.join(data_path, cfg['inputFiles']['catalogFile'])

        # 檢查檔案是否存在
        if not os.path.isfile(catalog_file):
            raise FileNotFoundError(f'Catalog file not found: {catalog_file}')

        # ===== 新增：使用 CatalogProcessor 載入 =====
        from utils.catalog_processor import CatalogProcessor

        # 自動偵測格式並載入
        HORUS = CatalogProcessor.load_catalog(catalog_file, format='auto')

        # 載入區域檔案（保持不變）
        neighborhood_file = os.path.join(data_path, cfg['inputFiles']['neighborhoodRegionFile'])
        testing_file = os.path.join(data_path, cfg['inputFiles']['testingRegionFile'])

        # ... (區域載入邏輯不變) ...

        return HORUS, CPTI11, CELLE
```

#### 3.2 新增配置選項

在配置檔案中新增格式指定選項：

```json
{
  "inputFiles": {
    "catalogFile": "catalog.zmap",
    "catalogFormat": "zmap",  // 新增：可選，預設 auto
    "neighborhoodRegionFile": "CPTI15.mat",
    "testingRegionFile": "CELLE_ter.mat"
  }
}
```

---

## 📊 測試計劃

### 單元測試

```python
# tests/test_catalog_formats.py

def test_zmap_format():
    """測試 ZMAP 格式轉換"""
    cat = CatalogProcessor.from_zmap('test_data/catalog.zmap')
    assert cat.shape[1] == 10
    assert cat[:, 0].min() > 1900  # Year column

def test_csep_format():
    """測試 CSEP 格式轉換"""
    cat = CatalogProcessor.from_csep('test_data/catalog.csep')
    assert cat.shape[1] == 10

def test_dataframe_format():
    """測試 DataFrame 轉換"""
    df = pd.DataFrame({
        'longitude': [121.5, 122.0],
        'latitude': [24.0, 24.5],
        'magnitude': [5.0, 5.5],
        'time': pd.to_datetime(['2020-01-01', '2020-01-02'])
    })
    cat = CatalogProcessor.from_dataframe(df)
    assert cat.shape == (2, 10)

def test_format_detection():
    """測試格式自動偵測"""
    fmt = CatalogProcessor.detect_format('test.zmap')
    assert fmt == 'zmap'

    fmt = CatalogProcessor.detect_format('test.mat')
    assert fmt == 'horus'
```

### 整合測試

```python
def test_full_pipeline():
    """測試完整流程：載入 → 前處理 → 子目錄"""
    # 載入 ZMAP 格式
    cat = CatalogProcessor.load_catalog('italy.zmap')

    # 前處理
    processed, T1, T2 = CatalogProcessor.preprocess_catalog(
        cat, 1960, 1990, 2012
    )

    # 建立子目錄
    params = {'mT': 5.0}
    CatE, CatJ, CatI = CatalogProcessor.create_catalogs(
        processed, params, 1990, 2012, 1960
    )

    assert CatI.shape[0] > 0
```

---

## 📦 依賴套件

### 必需
- `numpy` (已有)
- `pandas` (新增) - DataFrame 支援

### 可選
- `openquake.engine` - OpenQuake 格式支援
- `obspy` - 額外的地震學格式支援

### 安裝指令

```bash
# 基本支援 (ZMAP, CSEP, DataFrame)
pip install pandas

# OpenQuake 支援 (可選)
pip install openquake.engine
```

---

## 🔄 向後相容性

### 保證事項

1. **現有程式碼完全不變**: 所有現有的 `preprocess_catalog()`, `create_catalogs()` 等方法保持不變
2. **MATLAB .mat 格式持續支援**: 透過 `format='horus'` 或自動偵測
3. **現有配置檔案持續運作**: 不需要修改任何現有配置

### 升級路徑

```python
# 舊方式 (仍然支援)
mat_data = sio.loadmat('catalog.mat')
HORUS = mat_data['HORUS']

# 新方式 (推薦)
HORUS = CatalogProcessor.load_catalog('catalog.mat')

# 或使用其他格式
HORUS = CatalogProcessor.load_catalog('catalog.zmap')
```

---

## 📚 文檔更新

### 需要更新的檔案

1. **`docs/source/user_guide/configuration.rst`**
   - 新增 `catalogFormat` 欄位說明
   - 新增支援格式列表

2. **`docs/source/api_reference/utils.rst`**
   - 新增 `CatalogProcessor.load_catalog()` API 文檔
   - 新增格式轉換器文檔

3. **`README.md`**
   - 新增支援格式列表
   - 新增使用範例

4. **新增 `docs/source/user_guide/catalog_formats.rst`**
   - 詳細說明各種格式
   - 提供轉換範例

---

## ⏱️ 實作時程

### Week 1: 核心架構
- [ ] 實作 `load_catalog()` 統一介面
- [ ] 實作 `detect_format()` 自動偵測
- [ ] 實作 `validate_catalog()` 驗證器

### Week 2: 格式轉換器
- [ ] 實作 `from_zmap()`
- [ ] 實作 `from_csep()`
- [ ] 實作 `from_dataframe()`

### Week 3: 整合與測試
- [ ] 整合到 `data_loader.py`
- [ ] 撰寫單元測試
- [ ] 撰寫整合測試

### Week 4: 文檔與範例
- [ ] 更新 API 文檔
- [ ] 撰寫使用手冊
- [ ] 建立範例 notebooks

---

## ✅ 驗收標準

1. **功能完整性**:
   - ✅ 支援 ZMAP, CSEP, DataFrame 三種基本格式
   - ✅ 自動格式偵測正確率 > 95%
   - ✅ 所有轉換器產生正確的 HORUS 格式

2. **向後相容性**:
   - ✅ 現有程式碼無需修改即可運行
   - ✅ 現有配置檔案持續有效
   - ✅ MATLAB .mat 格式正常載入

3. **程式碼品質**:
   - ✅ 單元測試覆蓋率 > 90%
   - ✅ 所有 docstrings 完整
   - ✅ 錯誤處理完善

4. **文檔完整性**:
   - ✅ API 文檔完整
   - ✅ 使用範例清晰
   - ✅ 格式說明詳細

---

## 🎯 後續擴展

### 可能的未來功能

1. **更多格式支援**:
   - QuakeML
   - ISF (International Seismological Format)
   - NDK (GCMT format)

2. **格式轉換器**:
   - `to_zmap()` - 匯出為 ZMAP
   - `to_csep()` - 匯出為 CSEP
   - `to_dataframe()` - 匯出為 DataFrame

3. **進階功能**:
   - 目錄合併
   - 重複事件檢測
   - 資料品質報告

---

**計劃制定完成日期**: 2025-11-26
**預計開始日期**: 待確認
**預計完成日期**: 4 週後

## 參考資料

- [ObsPy ZMAP Documentation](https://docs.obspy.org/packages/obspy.io.zmap.html)
- [PyCSEP Catalog Formats](https://docs.cseptesting.org/concepts/catalogs.html)
- [SeismoStats Catalog Handling](https://seismostats.readthedocs.io/v1.0.0/user/catalogs.html)
