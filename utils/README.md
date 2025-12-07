# Utilities Directory

本資料夾包含 EEPAS Taiwan 項目的核心工具函數和輔助程式。

## 📂 文件列表

### 核心工具

#### 1. auto_boundary_adjustment.py
**功能**：自動邊界調整核心邏輯

**主要函數**：
- `check_boundary_touching()` - 檢測參數是否觸碰邊界
- `adjust_bounds()` - 根據觸碰情況調整邊界
- `backup_config()` - 備份配置文件

**使用場景**：
- 被 `eepas_learning_auto_boundary.py` 調用
- 自動放寬優化邊界以避免邊界約束

**關鍵參數**：
- `tolerance`: 邊界觸碰容差 (預設 0.01)
- `expansion_factor`: 邊界擴展倍數 (預設 2.0)

---

#### 2. fminsearchcon.py
**功能**：帶約束的 Nelder-Mead 單純形優化器

**主要函數**：
- `fminsearchcon(fun, x0, lb, ub, **options)` - 主優化函數

**特點**：
- MATLAB fminsearchcon 的 Python 實現
- 支持上下界約束
- 收斂標準：ftol (絕對容差)

**參數**：
```python
fminsearchcon(
    fun,           # 目標函數
    x0,            # 初始點
    lb, ub,        # 下界、上界
    maxiter=500,   # 最大迭代次數
    ftol=1e-4,     # 函數容差
    xtol=1e-4      # 參數容差
)
```

---

#### 3. data_loader.py
**功能**：地震目錄數據載入

**主要函數**：
- `load_earthquake_catalog()` - 載入 HORUS 和 CPTI 目錄
- `filter_by_completeness()` - 根據完整度震級過濾

**支持格式**：
- HORUS 格式 (台灣地震目錄)
- CPTI 格式 (義大利地震目錄)

---

#### 4. catalog_processor.py
**功能**：地震目錄處理和轉換

**主要函數**：
- `process_catalog()` - 目錄預處理
- `compute_distances()` - 計算震源距
- `decluster_catalog()` - 去叢集處理

---

#### 5. get_paths.py
**功能**：路徑解析和檔案位置管理

**主要函數**：
- `resolve_paths()` - 解析配置文件中的相對路徑
- `get_data_path()` - 獲取數據文件路徑
- `get_results_path()` - 獲取結果輸出路徑

**特點**：
- 支持相對和絕對路徑
- 跨平台兼容 (Linux/Mac/Windows)
- 自動從 `python_src/` 或項目根目錄執行

---

### 分析工具

#### 6. compare_results.py
**功能**：比較 MATLAB 和 Python 結果

**使用方式**：
```bash
python3 utils/compare_results.py \
    --matlab ../results/Fitted_par_EEPAS_2002_2016.csv \
    --python results/Fitted_par_EEPAS_2002_2016.csv
```

**輸出**：
- 參數差異報告
- 相對誤差統計
- 通過/失敗判定 (< 1% 誤差為通過)

---

#### 7. analyze_auto_boundary_result.py
**功能**：分析自動邊界調整結果

**使用方式**：
```bash
python3 utils/analyze_auto_boundary_result.py test_log.log
```

**輸出**：
- 每輪邊界變化
- NLL 改善曲線
- 收斂診斷

---

#### 8. convert_to_twd97.py
**功能**：座標系統轉換工具

**使用方式**：
```bash
python3 utils/convert_to_twd97.py
```

**功能**：
- WGS84 (經緯度) ↔ TWD97 (台灣大地座標系)
- 精度：< 0.01m 誤差
- 支持批量轉換

---

## 🔧 開發指南

### 導入工具函數

從項目根目錄：
```python
from utils.data_loader import load_earthquake_catalog
from utils.fminsearchcon import fminsearchcon
from utils.get_paths import resolve_paths
```

### 添加新工具

1. 在 `utils/` 創建新的 `.py` 文件
2. 在 `__init__.py` 中添加導入
3. 更新本 README

---

## 📊 依賴項

```bash
pip install numpy scipy pandas pyproj
```

---

## 🔍 故障排除

### ImportError: No module named 'utils'
確保從正確目錄執行：
```bash
cd /path/to/EEPAS_Taiwan-main/src/python_src
python3 your_script.py
```

### 路徑解析錯誤
使用 `get_paths.py` 中的函數而非硬編碼路徑：
```python
from utils.get_paths import get_data_path
data_file = get_data_path("horus_catalog.txt")
```

---

## 📝 核心函數索引

| 功能 | 文件 | 函數 |
|------|------|------|
| 優化器 | fminsearchcon.py | `fminsearchcon()` |
| 邊界調整 | auto_boundary_adjustment.py | `check_boundary_touching()` |
| 數據載入 | data_loader.py | `load_earthquake_catalog()` |
| 路徑解析 | get_paths.py | `resolve_paths()` |
| 結果比較 | compare_results.py | `compare_results()` |
| 座標轉換 | convert_to_twd97.py | `wgs84_to_twd97()` |

---

**最後更新**：2025-10-19
**維護者**：EEPAS Taiwan Team
