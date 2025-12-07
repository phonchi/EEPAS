# EEPAS 功能驗證計劃

**目的**: 驗證 docstring 修改後，EEPAS 五步驟流程的功能完全不變
**日期**: 2025-11-25
**驗證配置**: 3 個配置檔案

---

## 📋 驗證配置檔案

| 配置檔案 | 模式 | 說明 |
|---------|------|------|
| `config_italy_causal_ew0.json` | 快速模式 (ew0) | 標準快速預測 |
| `config_italy_causal_ew1.json` | 快速模式 (ew1) | 加權模式 1 |
| `config_italy_causal_ew0_accurate.json` | 精確模式 | 高精度數值積分 |

---

## 🎯 五步驟流程

### Step 1: PPE Learning
學習 PPE 模型參數 (a, d, s)

### Step 2: Aftershock Parameters Fitting
擬合餘震去叢集參數 (ν, κ)

### Step 3: EEPAS Learning
學習 EEPAS 完整參數 (am, bm, Sm, at, bt, St, ba, Sa, u)

### Step 4: PPE Forecast
生成 PPE 基準預測

### Step 5: EEPAS Forecast
生成 EEPAS 最終預測

---

## 📂 結果目錄結構

### 現有結果目錄（需要備份）

```
results_italy_causal_ew0/          # 標準快速模式
├── Fitted_par_PPE_1990_2012.csv
├── Fitted_par_aftershock_1990_2012.csv
├── Fitted_par_EEPAS_1990_2012.csv
├── PREVISIONI_3m_PPE_2012_2022.mat
└── PREVISIONI_3m_EEPAS_2012_2022.mat

results_italy_causal_ew1/          # 加權模式 1
├── Fitted_par_PPE_1990_2012.csv
├── Fitted_par_aftershock_1990_2012.csv
├── Fitted_par_EEPAS_1990_2012.csv
├── PREVISIONI_3m_PPE_2012_2022.mat
└── PREVISIONI_3m_EEPAS_2012_2022.mat

results_italy_causal_ew0_accurate/ # 精確模式
├── Fitted_par_PPE_1990_2012.csv
├── Fitted_par_aftershock_1990_2012.csv
├── Fitted_par_EEPAS_1990_2012.csv
├── PREVISIONI_3m_PPE_2012_2022.mat
└── PREVISIONI_3m_EEPAS_2012_2022.mat
```

### 備份目錄（驗證前建立）

```
results_italy_causal_ew0_backup/
results_italy_causal_ew1_backup/
results_italy_causal_ew0_accurate_backup/
```

### 新結果目錄（驗證後產生）

```
results_italy_causal_ew0/          # 重新執行後的結果
results_italy_causal_ew1/
results_italy_causal_ew0_accurate/
```

---

## 🔄 執行流程

### Phase 1: 備份現有結果 ✅

```bash
# 備份三個配置的現有結果
cp -r results_italy_causal_ew0 results_italy_causal_ew0_backup
cp -r results_italy_causal_ew1 results_italy_causal_ew1_backup
cp -r results_italy_causal_ew0_accurate results_italy_causal_ew0_accurate_backup

# 驗證備份完成
ls -lh results_italy_causal_ew0_backup/
ls -lh results_italy_causal_ew1_backup/
ls -lh results_italy_causal_ew0_accurate_backup/
```

---

### Phase 2: 重新執行 config_italy_causal_ew0.json (快速模式) ⏳

**配置參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: Fast (--fast)
- Weight: ew0
- PPE ref mag: mT

#### Step 1: PPE Learning
```bash
python3 ppe_learning.py \
  --config config_italy_causal_ew0.json \
  --grid-res 30
```

**預期輸出**: `results_italy_causal_ew0/Fitted_par_PPE_1990_2012.csv`

**預期參數** (從 backup 比較):
- a ≈ 0.616
- d ≈ 29.6 km
- s ≈ 0

---

#### Step 2: Aftershock Fitting
```bash
python3 fit_aftershock_params.py \
  --config config_italy_causal_ew0.json \
  --fast \
  --ppe-ref-mag mT \
  --target-mag mT
```

**預期輸出**: `results_italy_causal_ew0/Fitted_par_aftershock_1990_2012.csv`

**預期參數**:
- v ≈ 0.577
- k ≈ 0.205

---

#### Step 3: EEPAS Learning
```bash
python3 eepas_learning_auto_boundary.py \
  --config config_italy_causal_ew0.json \
  --three-stage \
  --ppe-ref-mag mT \
  --max-rounds 1
```

**預期輸出**: `results_italy_causal_ew0/Fitted_par_EEPAS_1990_2012.csv`

**預期參數**:
- am ≈ 1.234
- bm ≈ 1.0
- Sm ≈ 0.242
- at ≈ 2.588
- bt ≈ 0.349
- St ≈ 0.15
- ba ≈ 0.504
- Sa ≈ 1.0
- u ≈ 0.167

---

#### Step 4: PPE Forecast
```bash
python3 ppe_make_forecast.py \
  --config config_italy_causal_ew0.json \
  --fast \
  --ppe-ref-mag mT
```

**預期輸出**: `results_italy_causal_ew0/PREVISIONI_3m_PPE_2012_2022.mat`

**驗證指標**:
- Lambda 總和 ≈ 14.00

---

#### Step 5: EEPAS Forecast
```bash
python3 eepas_make_forecast.py \
  --config config_italy_causal_ew0.json \
  --fast \
  --ppe-ref-mag mT
```

**預期輸出**: `results_italy_causal_ew0/PREVISIONI_3m_EEPAS_2012_2022.mat`

**驗證指標**:
- Lambda 總和 ≈ 16.19

---

### Phase 3: 重新執行 config_italy_causal_ew1.json (加權模式) ⏳

**配置參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: Fast (--fast)
- Weight: ew1
- PPE ref mag: mT

#### 執行指令
```bash
# Step 1: PPE Learning
python3 ppe_learning.py \
  --config config_italy_causal_ew1.json \
  --grid-res 30

# Step 2: Aftershock Fitting
python3 fit_aftershock_params.py \
  --config config_italy_causal_ew1.json \
  --fast \
  --ppe-ref-mag mT \
  --target-mag mT

# Step 3: EEPAS Learning
python3 eepas_learning_auto_boundary.py \
  --config config_italy_causal_ew1.json \
  --three-stage \
  --ppe-ref-mag mT \
  --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py \
  --config config_italy_causal_ew1.json \
  --fast \
  --ppe-ref-mag mT

# Step 5: EEPAS Forecast
python3 eepas_make_forecast.py \
  --config config_italy_causal_ew1.json \
  --fast \
  --ppe-ref-mag mT
```

---

### Phase 4: 重新執行 config_italy_causal_ew0_accurate.json (精確模式) ⏳

**配置參數**:
- Learning: 1990-2012
- Forecast: 2012-2022
- Mode: **Accurate** (--accurate)
- Weight: ew0
- PPE ref mag: mT

#### 執行指令
```bash
# Step 1: PPE Learning (精確模式)
python3 ppe_learning.py \
  --config config_italy_causal_ew0_accurate.json \
  --accurate

# Step 2: Aftershock Fitting (精確模式)
python3 fit_aftershock_params.py \
  --config config_italy_causal_ew0_accurate.json \
  --accurate \
  --ppe-ref-mag mT \
  --target-mag mT

# Step 3: EEPAS Learning (精確模式)
python3 eepas_learning_auto_boundary.py \
  --config config_italy_causal_ew0_accurate.json \
  --three-stage \
  --accurate \
  --ppe-ref-mag mT \
  --max-rounds 1

# Step 4: PPE Forecast (精確模式)
python3 ppe_make_forecast.py \
  --config config_italy_causal_ew0_accurate.json \
  --accurate \
  --ppe-ref-mag mT

# Step 5: EEPAS Forecast (精確模式)
python3 eepas_make_forecast.py \
  --config config_italy_causal_ew0_accurate.json \
  --accurate \
  --ppe-ref-mag mT
```

---

## 🔍 Phase 5: 結果比較與驗證

### 比較腳本

建立 Python 腳本比較備份與新結果：

```python
# compare_results.py
import numpy as np
import pandas as pd
import scipy.io as sio
import os

def compare_csv(backup_file, new_file, tolerance=1e-6):
    """比較 CSV 參數檔案"""
    backup = pd.read_csv(backup_file)
    new = pd.read_csv(new_file)

    print(f"\n比較: {os.path.basename(backup_file)}")
    print("=" * 60)

    all_match = True
    for col in backup.columns:
        backup_val = backup[col].values[0]
        new_val = new[col].values[0]
        diff = abs(backup_val - new_val)
        rel_diff = diff / abs(backup_val) if backup_val != 0 else diff

        match = diff < tolerance or rel_diff < tolerance
        status = "✅" if match else "❌"

        print(f"{status} {col:15s}: {backup_val:12.8f} → {new_val:12.8f} (diff: {diff:.2e})")

        if not match:
            all_match = False

    return all_match

def compare_mat(backup_file, new_file, tolerance=1e-6):
    """比較 MATLAB 預測檔案"""
    backup = sio.loadmat(backup_file)
    new = sio.loadmat(new_file)

    print(f"\n比較: {os.path.basename(backup_file)}")
    print("=" * 60)

    # 找到預測矩陣的 key
    keys = [k for k in backup.keys() if not k.startswith('__')]

    all_match = True
    for key in keys:
        backup_data = backup[key]
        new_data = new[key]

        # 比較形狀
        if backup_data.shape != new_data.shape:
            print(f"❌ {key} 形狀不匹配: {backup_data.shape} vs {new_data.shape}")
            all_match = False
            continue

        # 比較數值
        diff = np.abs(backup_data - new_data)
        max_diff = np.max(diff)
        rel_diff = np.max(diff / (np.abs(backup_data) + 1e-10))

        match = max_diff < tolerance or rel_diff < tolerance
        status = "✅" if match else "❌"

        # 計算 Lambda 總和
        backup_sum = np.sum(backup_data[:, 1:])  # 排除第一列索引
        new_sum = np.sum(new_data[:, 1:])

        print(f"{status} {key}")
        print(f"   形狀: {backup_data.shape}")
        print(f"   最大差異: {max_diff:.2e}")
        print(f"   相對差異: {rel_diff:.2e}")
        print(f"   Lambda 總和: {backup_sum:.6f} → {new_sum:.6f}")

        if not match:
            all_match = False

    return all_match

def verify_config(config_name):
    """驗證單一配置的所有結果"""
    backup_dir = f"{config_name}_backup"
    new_dir = config_name

    print("\n" + "=" * 80)
    print(f"驗證配置: {config_name}")
    print("=" * 80)

    files = [
        "Fitted_par_PPE_1990_2012.csv",
        "Fitted_par_aftershock_1990_2012.csv",
        "Fitted_par_EEPAS_1990_2012.csv",
    ]

    mat_files = [
        "PREVISIONI_3m_PPE_2012_2022.mat",
        "PREVISIONI_3m_EEPAS_2012_2022.mat",
    ]

    all_pass = True

    # 比較 CSV 檔案
    for file in files:
        backup_path = os.path.join(backup_dir, file)
        new_path = os.path.join(new_dir, file)

        if not os.path.exists(backup_path) or not os.path.exists(new_path):
            print(f"⚠️  檔案不存在: {file}")
            continue

        if not compare_csv(backup_path, new_path):
            all_pass = False

    # 比較 MAT 檔案
    for file in mat_files:
        backup_path = os.path.join(backup_dir, file)
        new_path = os.path.join(new_dir, file)

        if not os.path.exists(backup_path) or not os.path.exists(new_path):
            print(f"⚠️  檔案不存在: {file}")
            continue

        if not compare_mat(backup_path, new_path):
            all_pass = False

    return all_pass

# 主程式
if __name__ == "__main__":
    configs = [
        "results_italy_causal_ew0",
        "results_italy_causal_ew1",
        "results_italy_causal_ew0_accurate",
    ]

    results = {}
    for config in configs:
        results[config] = verify_config(config)

    # 總結
    print("\n" + "=" * 80)
    print("驗證總結")
    print("=" * 80)

    for config, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {config}")

    # 總體結果
    if all(results.values()):
        print("\n🎉 所有配置驗證通過！功能完全一致！")
        exit(0)
    else:
        print("\n⚠️  部分配置驗證失敗，請檢查差異。")
        exit(1)
```

### 執行比較
```bash
python3 compare_results.py
```

---

## 📊 預期驗證結果

### 成功標準

所有參數和預測結果應滿足：

| 項目 | 容許差異 | 說明 |
|------|---------|------|
| **PPE 參數** (a, d, s) | < 1e-6 | 數值積分穩定 |
| **Aftershock 參數** (v, k) | < 1e-6 | MLE 優化穩定 |
| **EEPAS 參數** (9 個) | < 1e-6 | 三階段優化穩定 |
| **預測矩陣形狀** | 完全相同 | 時間窗×震級bins×網格 |
| **Lambda 總和** | < 1e-4 | 預測率總和穩定 |

### 預期時間

| 配置 | 模式 | 預估時間 |
|------|------|---------|
| config_italy_causal_ew0 | 快速 | ~2 小時 |
| config_italy_causal_ew1 | 快速 | ~2 小時 |
| config_italy_causal_ew0_accurate | 精確 | ~6-8 小時 |
| **總計** | - | **10-12 小時** |

---

## ⚠️ 重要注意事項

### 1. 執行順序
- ✅ **必須先備份**再執行
- ✅ **按順序執行**五個步驟（不能跳過）
- ✅ **等待完成**再執行下一步

### 2. 錯誤處理
如果某步驟失敗：
1. 檢查錯誤訊息
2. 確認配置檔案正確
3. 檢查結果目錄權限
4. 重新執行該步驟

### 3. EEPAS Learning 注意事項
- ⚠️ **不要設置 timeout**（可能需要 30-60 分鐘）
- ⚠️ **使用 --three-stage** （論文標準方法）
- ⚠️ **使用 --max-rounds 1**（論文單輪優化）

### 4. 精確模式特別注意
- config_italy_causal_ew0_accurate 使用 `--accurate` 標記
- 執行時間會長很多（~6-8 小時）
- 建議晚上或週末執行

---

## 📝 執行檢查清單

### 準備階段
- [ ] 確認工作目錄: `/home/math/EEPAS_Taiwan-main/src/python_src`
- [ ] 確認三個配置檔案存在
- [ ] 確認三個結果目錄存在

### 備份階段
- [ ] 備份 results_italy_causal_ew0
- [ ] 備份 results_italy_causal_ew1
- [ ] 備份 results_italy_causal_ew0_accurate
- [ ] 驗證備份完整性

### 執行階段 - ew0 (快速)
- [ ] Step 1: PPE Learning
- [ ] Step 2: Aftershock Fitting
- [ ] Step 3: EEPAS Learning
- [ ] Step 4: PPE Forecast
- [ ] Step 5: EEPAS Forecast

### 執行階段 - ew1 (快速)
- [ ] Step 1: PPE Learning
- [ ] Step 2: Aftershock Fitting
- [ ] Step 3: EEPAS Learning
- [ ] Step 4: PPE Forecast
- [ ] Step 5: EEPAS Forecast

### 執行階段 - ew0_accurate (精確)
- [ ] Step 1: PPE Learning (--accurate)
- [ ] Step 2: Aftershock Fitting (--accurate)
- [ ] Step 3: EEPAS Learning (--accurate)
- [ ] Step 4: PPE Forecast (--accurate)
- [ ] Step 5: EEPAS Forecast (--accurate)

### 驗證階段
- [ ] 建立比較腳本 compare_results.py
- [ ] 執行結果比較
- [ ] 檢查所有參數差異
- [ ] 檢查 Lambda 總和
- [ ] 生成驗證報告

---

## 🎯 驗證成功標準

驗證通過的條件：

1. ✅ **所有 CSV 參數檔案**數值差異 < 1e-6
2. ✅ **所有 MAT 預測檔案**形狀完全相同
3. ✅ **所有 Lambda 總和**差異 < 1e-4
4. ✅ **三個配置全部通過**驗證

**結論**: Docstring 修改**不影響任何計算邏輯**，功能完全保持一致！

---

## 📄 輸出報告

驗證完成後將生成：

1. **VERIFICATION_RESULTS.md** - 詳細驗證結果
2. **parameter_comparison.csv** - 參數對比表
3. **lambda_comparison.csv** - Lambda 總和對比
4. **verification_log.txt** - 完整執行日誌

---

**計劃建立日期**: 2025-11-25
**預計執行時間**: 10-12 小時
**風險評估**: 低（僅驗證，不修改邏輯）
**建議執行時段**: 週末或夜間
