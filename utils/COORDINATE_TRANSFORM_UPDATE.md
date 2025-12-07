# 坐標轉換工具更新說明

## 變更摘要

**日期**: 2025-11-28
**版本**: v0.3.0 → v0.4.0

### 主要變更

1. **檔案改名**: `convert_to_rdn2008.py` → `coordinate_transform.py`
2. **功能擴展**: 支援多種坐標系統，不再僅限於 RDN2008
3. **向後相容**: 保留舊檔案，新舊檔案可並存使用

---

## 新功能

### 1. 支援多種坐標系統

#### 預設坐標系統

| 名稱 | EPSG 代碼 | 說明 | 適用區域 |
|------|-----------|------|----------|
| **rdn2008** | EPSG:7794 | RDN2008 Italy Zone | 義大利 (預設) |
| **twd97** | EPSG:3826 | TWD97 TM2 121°E | 台灣 |
| **自訂** | epsg:XXXX | 任何 pyproj 支援的 EPSG | 自訂區域 |

#### 坐標驗證邊界

- **RDN2008**: Lat 35-48°N, Lon 6-20°E
- **TWD97**: Lat 21-26°N, Lon 119-123°E
- **自訂**: Lat -90~90°N, Lon -180~180°E

### 2. 彈性輸入輸出

- 可以只轉換 HORUS（省略 CELLE 參數）
- 可以只轉換 CELLE（省略 HORUS 參數）
- 支援自訂區域名稱（`--region` 參數）

### 3. 更好的錯誤訊息

- 繁體中文輸出
- 詳細的坐標範圍驗證
- 超出邊界時顯示具體無效範圍

---

## 使用範例

### 範例 1: 義大利（預設）

```bash
# 與舊版 convert_to_rdn2008.py 完全相同
python3 utils/coordinate_transform.py \
    --horus-in data/HORUS_Italy.mat \
    --celle-in data/CELLE_ter.mat \
    --horus-out data/HORUS_Italy_RDN2008.mat \
    --celle-out data/CELLE_Italy_RDN2008.mat
```

**輸出**:
```
============================================================
坐標轉換工具
============================================================
目標坐標系統: RDN2008 Italy Zone (epsg:7794)
描述: Italy national projected coordinate system
區域: RDN2008 Italy Zone
============================================================

✓ 建立坐標轉換器: epsg:4326 -> epsg:7794
...
```

### 範例 2: 台灣

```bash
python3 utils/coordinate_transform.py \
    --horus-in data/HORUS_Taiwan.mat \
    --celle-in data/CELLE_Taiwan.mat \
    --horus-out data/HORUS_Taiwan_TWD97.mat \
    --celle-out data/CELLE_Taiwan_TWD97.mat \
    --target-crs twd97 \
    --region Taiwan
```

### 範例 3: 自訂 EPSG 代碼

```bash
# UTM Zone 33N (常用於歐洲)
python3 utils/coordinate_transform.py \
    --horus-in data/input.mat \
    --horus-out data/output_UTM33N.mat \
    --target-crs epsg:32633 \
    --region "Europe UTM 33N"
```

### 範例 4: 只轉換 HORUS

```bash
python3 utils/coordinate_transform.py \
    --horus-in data/HORUS.mat \
    --horus-out data/HORUS_transformed.mat \
    --target-crs twd97
```

---

## API 變更

### 新增函數

#### `get_crs_info(crs_key: str) -> dict`

取得坐標系統資訊。

```python
from utils.coordinate_transform import get_crs_info

# 預設坐標系統
info = get_crs_info('rdn2008')
# {'epsg': 'epsg:7794', 'name': 'RDN2008 Italy Zone', ...}

info = get_crs_info('twd97')
# {'epsg': 'epsg:3826', 'name': 'TWD97 TM2 121°E', ...}

# 自訂 EPSG
info = get_crs_info('epsg:32633')
# {'epsg': 'epsg:32633', 'name': 'Custom EPSG:32633', ...}
```

#### `validate_coordinates(lon, lat, bounds, region_name) -> Tuple[bool, int]`

驗證坐標是否在預期範圍內。

```python
from utils.coordinate_transform import validate_coordinates
import numpy as np

lon = np.array([12.5, 13.0, 14.5])
lat = np.array([41.9, 42.5, 43.0])
bounds = {'lat': (35, 48), 'lon': (6, 20)}

all_valid, invalid_count = validate_coordinates(lon, lat, bounds, "Italy")
# (True, 0)
```

### 函數簽名變更

#### `main()` 函數

**新增參數**:
- `target_crs: str = 'rdn2008'` - 目標坐標系統
- `region_name: Optional[str] = None` - 區域名稱

**參數改為可選**:
- `horus_infile: Optional[Path]` - 可以不提供
- `celle_infile: Optional[Path]` - 可以不提供
- `horus_outfile: Optional[Path]` - 可以不提供
- `celle_outfile: Optional[Path]` - 可以不提供

#### `convert_coordinates()` 函數

**新增參數**:
- `bounds: dict` - 坐標驗證邊界
- `region_name: str = "region"` - 區域名稱

#### `convert_celle_coordinates()` 函數

**新增參數**:
- `bounds: dict` - 坐標驗證邊界
- `region_name: str = "region"` - 區域名稱

---

## 遷移指南

### 舊檔案已移除

`convert_to_rdn2008.py` 已被 `coordinate_transform.py` 完全取代並移除。

**遷移步驟**:
1. 將所有 `convert_to_rdn2008.py` 改為 `coordinate_transform.py`
2. 義大利專案：不需要修改參數（預設即為 RDN2008）
3. 台灣專案：新增 `--target-crs twd97 --region Taiwan` 參數

### 完全相容的用法

```bash
# 舊版指令（已移除）
python3 utils/convert_to_rdn2008.py \
    --horus-in A.mat --celle-in B.mat \
    --horus-out C.mat --celle-out D.mat

# 新版指令（完全相同的輸出）
python3 utils/coordinate_transform.py \
    --horus-in A.mat --celle-in B.mat \
    --horus-out C.mat --celle-out D.mat
```

---

## 常見 EPSG 代碼參考

### 台灣常用坐標系統

| 名稱 | EPSG | 說明 |
|------|------|------|
| TWD97 TM2 121°E | 3826 | 台灣二度分帶 (121°E) |
| TWD97 TM2 119°E | 3825 | 台灣二度分帶 (119°E) |
| TWD67 TM Taiwan | 3828 | 台灣舊坐標系統 |

### 義大利常用坐標系統

| 名稱 | EPSG | 說明 |
|------|------|------|
| RDN2008 / Italy zone | 7794 | 義大利國家投影 (預設) |
| Monte Mario / Italy zone 1 | 3003 | 舊義大利坐標系統 zone 1 |
| Monte Mario / Italy zone 2 | 3004 | 舊義大利坐標系統 zone 2 |

### 全球通用 UTM 坐標系統

| 區域 | EPSG 範圍 | 說明 |
|------|-----------|------|
| UTM Northern Hemisphere | 32601-32660 | WGS84 / UTM zone 1N-60N |
| UTM Southern Hemisphere | 32701-32760 | WGS84 / UTM zone 1S-60S |

**範例**:
- 義大利 (東經 12°): UTM Zone 33N = EPSG:32633
- 台灣 (東經 121°): UTM Zone 51N = EPSG:32651

---

## 測試

### 單元測試

```python
from utils.coordinate_transform import get_crs_info, validate_coordinates
import numpy as np

# 測試 CRS 資訊
assert get_crs_info('rdn2008')['epsg'] == 'epsg:7794'
assert get_crs_info('twd97')['epsg'] == 'epsg:3826'
assert get_crs_info('epsg:32633')['epsg'] == 'epsg:32633'

# 測試坐標驗證
lon = np.array([12.0])
lat = np.array([42.0])
bounds = {'lat': (35, 48), 'lon': (6, 20)}
valid, count = validate_coordinates(lon, lat, bounds, "Italy")
assert valid == True
assert count == 0

print("✓ 所有測試通過")
```

### 整合測試

```bash
# 測試義大利轉換（需要實際資料檔案）
python3 utils/coordinate_transform.py \
    --horus-in data/HORUS_Italy.mat \
    --horus-out /tmp/test_output.mat \
    --target-crs rdn2008

# 測試台灣轉換（模擬）
python3 utils/coordinate_transform.py \
    --horus-in data/HORUS_Taiwan.mat \
    --horus-out /tmp/test_taiwan.mat \
    --target-crs twd97 \
    --region Taiwan
```

---

## 未來擴展

### 計畫中的功能

1. **反向轉換**: 投影坐標 → WGS84
2. **批次轉換**: 一次處理多個檔案
3. **坐標系統偵測**: 自動識別輸入坐標系統
4. **更多預設**: 增加日本、紐西蘭等地區預設

### 如何貢獻

如需新增其他區域的預設坐標系統，請編輯 `CRS_PRESETS` 字典：

```python
CRS_PRESETS = {
    'your_region': {
        'epsg': 'epsg:XXXX',
        'name': '坐標系統名稱',
        'bounds': {'lat': (min, max), 'lon': (min, max)},
        'description': '說明'
    }
}
```

---

## 相關文檔

- [pyproj 文檔](https://pyproj4.github.io/pyproj/)
- [EPSG 代碼查詢](https://epsg.io/)
- [台灣坐標系統說明](https://www.sunriver.com.tw/grid_tm2.htm)
- [義大利坐標系統說明](http://www.epsg.org/)

---

**維護者**: EEPAS Development Team
**最後更新**: 2025-11-28
