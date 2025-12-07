# 參考版本（輩分）參數記錄

## EW0 快速模式 (config_italy_causal_ew0_reference)

### PPE Parameters
- a = 0.6160851463290484
- d = 29.63911393695742
- s = 1e-15
- ln_L = -514.1045952302474

### EEPAS Parameters
- am = 1.234371016377085795
- bm = 1.000000000000000000
- Sm = 0.241961655427662764
- at = 2.587598187154488638
- bt = 0.349374185549880034
- St = 0.150000000000017758
- ba = 0.503754126161064297
- Sa = 1.000000000000007994
- u = 0.167019921817607830
- ln_L = -495.3949938149671084

## 比較項目清單

待驗證完成後比較：

1. **PPE Parameters**
   - [ ] a, d, s 是否一致
   - [ ] ln_L 差異

2. **EEPAS Parameters**
   - [ ] 8 個參數 (am, bm, Sm, at, bt, St, ba, Sa) 是否一致
   - [ ] u 參數是否一致
   - [ ] ln_L 差異

3. **Forecasting Matrix**
   - [ ] PREVISIONI_3m_PPE Lambda 總和
   - [ ] PREVISIONI_3m_EEPAS Lambda 總和
   - [ ] 逐格差異分析

