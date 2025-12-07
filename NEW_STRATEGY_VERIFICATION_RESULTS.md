# EEPAS 新策略系統驗證結果

## 比較項目

比較舊格式（stage1/2/3）與新格式（biondini2023 策略）的結果：

1. PPE 參數 (CSV)
2. Aftershock 參數 (CSV)
3. EEPAS 參數 (CSV)
4. PPE Forecast Matrix (.mat)
5. EEPAS Forecast Matrix (.mat)

## 總結

| 配置 | PPE參數 | Aftershock參數 | EEPAS參數 | PPE Forecast | EEPAS Forecast | 最大參數差異 |
|------|---------|---------------|-----------|-------------|---------------|-------------|
| ew0 (快速模式)           | ✅ | ✅ | ✅ | ✅ | ⚠️ | 0.000002% |
| ew1 (快速模式, 加權)       | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | 0.000015% |
| ew0 accurate (精確模式)  | ✅ | ✅ | ✅ | ✅ | ⚠️ | 0.000020% |

## 結論

⚠️  部分結果有差異，建議進一步檢查。
