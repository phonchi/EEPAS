# EEPAS Forecast Converter 使用指南

**快速開始** | [完整文件](FORECAST_CONVERTER_GUIDE.md) | [驗證報告](FORECAST_CONVERTER_VERIFICATION.md)

---

## 🚀 30 秒快速開始

```python
from analysis.forecast_converter import EEPASForecastConverter

# 初始化
converter = EEPASForecastConverter(
    forecast_file='results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat',
    grid_file='data/CELLE_ter.mat'
)

# 轉換所有週期
converter.convert_all_periods(output_file='eepas_forecast.dat')
```

就這麼簡單！🎉

---

## 📚 這是什麼？

`EEPASForecastConverter` 是一個**統一的轉換類別**，用於：

1. ✅ 載入 EEPAS/PPE MATLAB 預測檔案
2. ✅ 轉換座標系統 (RDN2008 → WGS84)
3. ✅ 執行空間降採樣 (粗網格 → 0.1° 細網格)
4. ✅ 處理時間週期 (3 個月/1 年)
5. ✅ 匯出 PyCSEP 格式
6. ✅ 直接建立 PyCSEP GriddedForecast 物件

**取代**: `dataset.py` 的所有功能

---

## 🎯 為什麼使用它？

### 舊方法 (dataset.py)

```python
# 需要 50+ 行程式碼
mat_data = scipy.io.loadmat(celle_file)
cells_data_km = mat_data['CELLESD'][:, :4]
transformer = Transformer.from_crs("EPSG:7794", "EPSG:4326")
# ... 座標轉換 ...
# ... 載入預測 ...
# ... 建立震級區間 ...
# ... 迴圈處理 40 個週期 ...
# ... 降採樣 ...
# ... 合併和累加 ...
# ... 匯出 ...
```

### 新方法 (EEPASForecastConverter)

```python
# 只需要 3 行程式碼
converter = EEPASForecastConverter(forecast_file, grid_file)
converter.convert_all_periods(output_file='forecast.dat')
```

**程式碼減少 94%** ✨

---

## 📖 基本使用

### 1. 轉換單一週期

```python
from analysis.forecast_converter import EEPASForecastConverter

converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_EEPAS_2012_2022.mat',
    grid_file='CELLE_ter.mat'
)

# 轉換第 1 週期 (2012 Q1)
period_1 = converter.convert_period(
    period=1,
    output_file='forecast_2012_Q1.dat'
)

print(f"期間 1 預測率: {period_1['RATE'].sum():.4f}")
```

### 2. 轉換所有週期

```python
# 轉換並累加所有 40 個週期
all_periods = converter.convert_all_periods(
    output_file='forecast_all.dat'
)

print(f"總預測率: {all_periods['RATE'].sum():.2f}")
```

### 3. PyCSEP 整合

```python
from csep.utils import time_utils

# 定義時間範圍
start_date = time_utils.strptime_to_utc_datetime('2012-01-01 00:00:00.0')
end_date = time_utils.strptime_to_utc_datetime('2021-12-31 23:59:59.0')

# 直接建立 PyCSEP forecast 物件
forecast = converter.to_pycsep_forecast(
    data=all_periods,
    start_date=start_date,
    end_date=end_date,
    name='EEPAS_2012_2021'
)

# 使用 PyCSEP 測試
import csep
n_test = csep.poisson.number_test(forecast, catalog)
```

---

## 🔧 進階功能

### 自訂網格解析度

```python
# 使用 0.05° × 0.05° 細網格
converter.convert_all_periods(
    output_file='forecast_fine.dat',
    grid_resolution=0.05
)
```

### 處理特定週期範圍

```python
# 只處理前 10 個週期
converter.convert_all_periods(
    start_period=1,
    end_period=10,
    output_file='forecast_p1_10.dat'
)
```

### 時間週期計算

```python
# 計算各週期的時間範圍
for period in range(1, 5):
    start, end = converter.calculate_period_dates(
        period=period,
        start_year=2012,
        period_length_months=3  # 3 個月週期
    )
    print(f"週期 {period}: {start.date()} - {end.date()}")
```

輸出：
```
週期 1: 2012-01-01 - 2012-04-01
週期 2: 2012-04-01 - 2012-07-01
週期 3: 2012-07-01 - 2012-10-01
週期 4: 2012-10-01 - 2013-01-01
```

---

## 📊 實際案例

### 案例 1: EEPAS vs PPE 比較

```python
# 轉換 EEPAS
eepas = EEPASForecastConverter(
    'PREVISIONI_3m_EEPAS_2012_2022.mat',
    'CELLE_ter.mat'
)
eepas_data = eepas.convert_all_periods()

# 轉換 PPE
ppe = EEPASForecastConverter(
    'PREVISIONI_3m_PPE_2012_2022.mat',
    'CELLE_ter.mat'
)
ppe_data = ppe.convert_all_periods()

# 比較
print(f"EEPAS lambda: {eepas_data['RATE'].sum():.2f}")
print(f"PPE lambda: {ppe_data['RATE'].sum():.2f}")
print(f"EEPAS/PPE 比值: {eepas_data['RATE'].sum() / ppe_data['RATE'].sum():.4f}")
```

輸出：
```
EEPAS lambda: 16.27
PPE lambda: 14.00
EEPAS/PPE 比值: 1.1620
```

### 案例 2: 季度預測視覺化

```python
import matplotlib.pyplot as plt

# 生成 2012 年 4 個季度的預測
for quarter in range(1, 5):
    # 轉換
    data = converter.convert_period(
        period=quarter,
        output_file=f'forecast_2012_Q{quarter}.dat'
    )

    # 計算日期
    start, end = converter.calculate_period_dates(quarter, 2012, 3)

    # 建立 PyCSEP forecast
    forecast = converter.to_pycsep_forecast(
        data=data,
        start_date=start,
        end_date=end,
        name=f'EEPAS_2012_Q{quarter}'
    )

    # 繪圖
    ax = forecast.plot(
        extent=[6, 19, 35, 48],  # 義大利範圍
        plot_args={'title': f'EEPAS Forecast: 2012 Q{quarter}'}
    )
    plt.savefig(f'forecast_2012_Q{quarter}.png', dpi=300)
    plt.close()
```

---

## 📁 檔案說明

### 主要檔案

| 檔案 | 說明 |
|------|------|
| `forecast_converter.py` | 核心轉換類別 (663 行) |
| `FORECAST_CONVERTER_GUIDE.md` | 完整使用指南 (542 行) |
| `EEPAS_Forecast_Evaluation_New.ipynb` | PyCSEP 評估範例 notebook |
| `test_forecast_converter.py` | 自動化測試腳本 (390 行) |
| `FORECAST_CONVERTER_VERIFICATION.md` | 驗證報告 |

### 測試

```bash
# 執行完整測試
python3 test_forecast_converter.py
```

---

## 🎓 完整文件

- **[完整使用指南](FORECAST_CONVERTER_GUIDE.md)** - 542 行詳細文件
  - API 參考
  - 所有功能說明
  - 20+ 範例程式碼
  - 常見問題解答

- **[驗證報告](FORECAST_CONVERTER_VERIFICATION.md)** - 測試結果和效能對比
  - 6 個測試場景全部通過
  - 與 `dataset.py` 數值一致驗證
  - 效能指標

- **[Notebook 範例](EEPAS_Forecast_Evaluation_New.ipynb)** - 完整 PyCSEP 評估流程
  - 載入和轉換預測
  - PyCSEP 一致性測試
  - EEPAS vs PPE 比較

---

## ❓ 常見問題

### Q1: 這個 converter 可以處理 Taiwan 數據嗎？

**可以**！只需要設定 `coordinate_transform=False`（如果已經是經緯度）：

```python
converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_Taiwan.mat',
    grid_file='CELLE_Taiwan.mat',
    coordinate_transform=False  # Taiwan 資料已經是經緯度
)
```

### Q2: 轉換會損失精度嗎？

**不會**。測試顯示：
- Export/Reload 差異: 0.000000
- 與 `dataset.py` 結果完全一致

### Q3: 效能如何？

- 單一週期: ~0.5 秒
- 40 週期: ~30 秒
- 記憶體: ~500 MB

### Q4: 支援哪些時間週期？

- 3 個月週期 (預設)
- 1 年週期
- 自訂週期 (`period_length_months` 參數)

### Q5: 可以不進行空間降採樣嗎？

**可以**：

```python
converter.convert_period(
    period=1,
    perform_downsampling=False  # 保持原始粗網格
)
```

---

## 🔗 相關連結

- **PyCSEP 文件**: https://docs.cseptesting.org/
- **PyProj 文件**: https://pyproj4.github.io/pyproj/
- **EEPAS 論文**: Biondini et al. (2023) GJI

---

## 📞 支援

遇到問題？

1. 查看 [完整使用指南](FORECAST_CONVERTER_GUIDE.md)
2. 查看 [驗證報告](FORECAST_CONVERTER_VERIFICATION.md)
3. 執行測試: `python3 test_forecast_converter.py`
4. 檢查 [Notebook 範例](EEPAS_Forecast_Evaluation_New.ipynb)

---

**版本**: 1.0.0
**最後更新**: 2025-11-26
**狀態**: ✅ 生產就緒

**開始使用**: [完整使用指南](FORECAST_CONVERTER_GUIDE.md) 📖
