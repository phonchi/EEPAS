# ✅ EEPAS 功能驗證準備完成

**日期**: 2025-11-25
**狀態**: 🟢 準備就緒

---

## 📋 已完成準備工作

### 1. ✅ 備份現有結果

所有三個配置的結果已備份：

| 原始目錄 | 備份目錄 | 檔案數 | 狀態 |
|---------|---------|--------|------|
| `results_italy_causal_ew0/` | `results_italy_causal_ew0_backup/` | 26 | ✅ |
| `results_italy_causal_ew1/` | `results_italy_causal_ew1_backup/` | 26 | ✅ |
| `results_italy_causal_ew0_accurate/` | `results_italy_causal_ew0_accurate_backup/` | 26 | ✅ |

### 2. ✅ 建立驗證腳本

| 腳本 | 用途 | 狀態 |
|------|------|------|
| `run_verification.sh` | 自動執行全部五步驟 | ✅ 已建立 |
| `compare_results.py` | 比較備份與新結果 | ✅ 已建立 |

### 3. ✅ 建立文檔

| 文檔 | 說明 | 狀態 |
|------|------|------|
| `VERIFICATION_PLAN.md` | 詳細驗證計劃 | ✅ 已建立 |
| `VERIFICATION_READY.md` | 本文件 | ✅ 已建立 |

---

## 🚀 執行方式

### 選項 1: 自動執行（推薦）

```bash
cd /home/math/EEPAS_Taiwan-main/src/python_src

# 在 tmux 或 screen 中執行（建議）
tmux new -s eepas_verify
./run_verification.sh
```

**預計時間**: 10-12 小時

### 選項 2: 手動執行

按照 `VERIFICATION_PLAN.md` 中的步驟手動執行每個配置。

---

## 📊 三個配置說明

### 1. config_italy_causal_ew0.json (快速模式)

**參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: Fast (`--fast`)
- Weight: ew0 (標準加權)
- PPE ref mag: mT

**預計時間**: ~2 小時

**執行指令**:
```bash
# Step 1
python3 ppe_learning.py --config config_italy_causal_ew0.json --grid-res 30

# Step 2
python3 fit_aftershock_params.py --config config_italy_causal_ew0.json --fast --ppe-ref-mag mT --target-mag mT

# Step 3
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json --three-stage --ppe-ref-mag mT --max-rounds 1

# Step 4
python3 ppe_make_forecast.py --config config_italy_causal_ew0.json --fast --ppe-ref-mag mT

# Step 5
python3 eepas_make_forecast.py --config config_italy_causal_ew0.json --fast --ppe-ref-mag mT
```

---

### 2. config_italy_causal_ew1.json (加權模式)

**參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: Fast (`--fast`)
- Weight: ew1 (加權模式 1)
- PPE ref mag: mT

**預計時間**: ~2 小時

**執行指令**:
```bash
# Step 1
python3 ppe_learning.py --config config_italy_causal_ew1.json --grid-res 30

# Step 2
python3 fit_aftershock_params.py --config config_italy_causal_ew1.json --fast --ppe-ref-mag mT --target-mag mT

# Step 3
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew1.json --three-stage --ppe-ref-mag mT --max-rounds 1

# Step 4
python3 ppe_make_forecast.py --config config_italy_causal_ew1.json --fast --ppe-ref-mag mT

# Step 5
python3 eepas_make_forecast.py --config config_italy_causal_ew1.json --fast --ppe-ref-mag mT
```

---

### 3. config_italy_causal_ew0_accurate.json (精確模式)

**參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: **Accurate** (`--accurate`)
- Weight: ew0
- PPE ref mag: mT

**預計時間**: ~6-8 小時

**執行指令**:
```bash
# Step 1
python3 ppe_learning.py --config config_italy_causal_ew0_accurate.json --accurate

# Step 2
python3 fit_aftershock_params.py --config config_italy_causal_ew0_accurate.json --accurate --ppe-ref-mag mT --target-mag mT

# Step 3
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0_accurate.json --three-stage --accurate --ppe-ref-mag mT --max-rounds 1

# Step 4
python3 ppe_make_forecast.py --config config_italy_causal_ew0_accurate.json --accurate --ppe-ref-mag mT

# Step 5
python3 eepas_make_forecast.py --config config_italy_causal_ew0_accurate.json --accurate --ppe-ref-mag mT
```

---

## 🔍 驗證結果比較

執行完成後，運行比較腳本：

```bash
python3 compare_results.py
```

**比較項目**:
1. ✅ PPE 參數 (a, d, s)
2. ✅ Aftershock 參數 (v, k)
3. ✅ EEPAS 參數 (am, bm, Sm, at, bt, St, ba, Sa, u)
4. ✅ PPE 預測矩陣
5. ✅ EEPAS 預測矩陣
6. ✅ Lambda 總和

**成功標準**:
- 數值差異 < 1e-6 (CSV 參數)
- Lambda 總和差異 < 1e-4
- 矩陣形狀完全相同

---

## 📈 預期結果

### config_italy_causal_ew0 (快速)

**PPE 參數**:
- a ≈ 0.616
- d ≈ 29.6 km
- s ≈ 0

**Aftershock 參數**:
- v ≈ 0.577
- k ≈ 0.205

**EEPAS 參數**:
- am ≈ 1.234, bm ≈ 1.0, Sm ≈ 0.242
- at ≈ 2.588, bt ≈ 0.349, St ≈ 0.15
- ba ≈ 0.504, Sa ≈ 1.0, u ≈ 0.167

**Lambda 總和**:
- PPE: ~14.00
- EEPAS: ~16.19

---

### config_italy_causal_ew1 (加權)

參數值會與 ew0 略有不同（因為不同的加權方案）

---

### config_italy_causal_ew0_accurate (精確)

參數值應與 ew0 非常接近（差異 < 0.1%），因為使用更精確的數值積分方法。

---

## ⚠️ 重要注意事項

### 1. 執行環境
- ✅ **使用 tmux/screen**: 避免 SSH 斷線中斷
- ✅ **確保磁碟空間**: 每個配置約需 500MB
- ✅ **不要中斷執行**: 每個配置的五步驟必須完整執行

### 2. EEPAS Learning 特別注意
- ⚠️ **不設 timeout**: Step 3 可能需要 30-60 分鐘
- ⚠️ **使用 --three-stage**: 論文標準方法
- ⚠️ **使用 --max-rounds 1**: 單輪優化（論文版本）

### 3. 精確模式注意事項
- ⚠️ **執行時間長**: 6-8 小時
- ⚠️ **CPU 密集**: 會使用所有核心
- ⚠️ **建議夜間執行**: 避免白天影響其他工作

---

## 📝 執行進度檢查

執行過程中可以檢查：

```bash
# 查看最新生成的檔案
ls -lt results_italy_causal_ew0/*.csv results_italy_causal_ew0/*.mat | head

# 查看 Python 進程
ps aux | grep python3

# 查看日誌（如果有重定向）
tail -f verification.log
```

---

## 🎯 驗證目標

本次驗證的目的是確認：

1. ✅ **Docstring 修改不影響計算邏輯**
2. ✅ **所有參數完全一致** (誤差 < 1e-6)
3. ✅ **預測結果完全一致** (誤差 < 1e-4)
4. ✅ **三種配置都正常運作**

**如果驗證通過**: 可以確認 docstring 修改是安全的，不影響任何功能。

**如果驗證失敗**: 需要檢查差異來源，確認是否為數值誤差或邏輯錯誤。

---

## 📄 輸出檔案

驗證完成後會產生：

| 檔案 | 說明 |
|------|------|
| `VERIFICATION_RESULTS.md` | 詳細驗證結果報告 |
| `verification.log` | 完整執行日誌 |

---

## 🆘 遇到問題？

### 常見問題

**Q1: Step 3 執行很久沒反應？**
- A: 正常現象，EEPAS Learning 需要 30-60 分鐘

**Q2: 記憶體不足？**
- A: 確認系統有至少 8GB RAM，考慮關閉其他程式

**Q3: 某個配置失敗？**
- A: 檢查錯誤訊息，可能需要調整參數或重新執行該配置

**Q4: 結果有微小差異？**
- A: 如果差異 < 1e-4，屬於數值誤差範圍，可接受

---

## ✅ 準備檢查清單

開始執行前確認：

- [x] 備份已完成（3 個配置）
- [x] 執行腳本已建立
- [x] 比較腳本已建立
- [x] 磁碟空間充足（> 5GB）
- [x] 在 tmux/screen 中（建議）
- [ ] 開始執行 `./run_verification.sh`

---

**準備完成日期**: 2025-11-25
**預計執行時間**: 10-12 小時
**建議執行時段**: 週末或夜間

🎯 **一切準備就緒！可以開始執行驗證了！**
