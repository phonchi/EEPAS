#!/bin/bash
# 測試 --no-multistart 模式是否能得到一致結果

set -e  # 遇到錯誤立即停止

echo "════════════════════════════════════════════════════════════════════════════════"
echo "測試 --no-multistart 模式"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  重要: 將測試三個配置是否在 --no-multistart 模式下仍能得到一致結果"
echo "   預計執行時間: 8-10 小時"
echo ""

cd /home/math/EEPAS_Taiwan-main/src/python_src

# ================================================================================
# Phase 1: config_italy_causal_ew0_new.json (快速模式, NO MULTISTART)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 1: config_italy_causal_ew0_new.json (快速模式, NO MULTISTART)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 + NO MULTISTART"
echo "🎯 策略: biondini2023"
echo "📁 結果目錄: results_italy_causal_ew0_new_no_multistart"
echo ""

# 修改配置的結果目錄
cp "$CONFIG" "${CONFIG%.json}_no_multistart.json"
sed -i 's/"results_italy_causal_ew0_new"/"results_italy_causal_ew0_new_no_multistart"/' "${CONFIG%.json}_no_multistart.json"

CONFIG_NO_MS="${CONFIG%.json}_no_multistart.json"

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG_NO_MS"
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning (NO MULTISTART)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化, NO MULTISTART)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_NO_MS" --three-stage --no-multistart --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 1 完成"

# ================================================================================
# Phase 2: config_italy_causal_ew1_new.json (快速模式, NO MULTISTART)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 2: config_italy_causal_ew1_new.json (快速模式, NO MULTISTART)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew1_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 + NO MULTISTART + 加權 ew1"
echo "🎯 策略: biondini2023"
echo "📁 結果目錄: results_italy_causal_ew1_new_no_multistart"
echo ""

# 修改配置的結果目錄
cp "$CONFIG" "${CONFIG%.json}_no_multistart.json"
sed -i 's/"results_italy_causal_ew1_new"/"results_italy_causal_ew1_new_no_multistart"/' "${CONFIG%.json}_no_multistart.json"

CONFIG_NO_MS="${CONFIG%.json}_no_multistart.json"

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG_NO_MS"
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning (NO MULTISTART)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化, NO MULTISTART)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_NO_MS" --three-stage --no-multistart --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG_NO_MS" --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 2 完成"

# ================================================================================
# Phase 3: config_italy_causal_ew0_accurate_new.json (精確模式, NO MULTISTART)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 3: config_italy_causal_ew0_accurate_new.json (精確模式, NO MULTISTART)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0_accurate_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 精確 + NO MULTISTART"
echo "🎯 策略: biondini2023"
echo "📁 結果目錄: results_italy_causal_ew0_accurate_new_no_multistart"
echo "⚠️  警告: 此階段需要 6-8 小時"
echo ""

# 修改配置的結果目錄
cp "$CONFIG" "${CONFIG%.json}_no_multistart.json"
sed -i 's/"results_italy_causal_ew0_accurate_new"/"results_italy_causal_ew0_accurate_new_no_multistart"/' "${CONFIG%.json}_no_multistart.json"

CONFIG_NO_MS="${CONFIG%.json}_no_multistart.json"

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG_NO_MS" --accurate
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG_NO_MS" --accurate --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning (NO MULTISTART)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化, 精確模式, NO MULTISTART)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_NO_MS" --three-stage --no-multistart --accurate --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG_NO_MS" --accurate --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG_NO_MS" --accurate --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 3 完成"

# ================================================================================
# 結果比較
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "結果比較: NO MULTISTART vs REFERENCE"
echo "════════════════════════════════════════════════════════════════════════════════"

python3 << 'PYEOF'
import pandas as pd
import numpy as np
import scipy.io as sio

def compare(new_dir, ref_dir, name):
    print(f"\n{'='*80}")
    print(f"{name}")
    print(f"{'='*80}")

    # PPE
    try:
        new_ppe = pd.read_csv(f"{new_dir}/Fitted_par_PPE_1990_2012.csv")
        ref_ppe = pd.read_csv(f"{ref_dir}/Fitted_par_PPE_1990_2012.csv")
        print("\n📊 PPE Parameters:")
        print(f"{'參數':<15} {'NO MULTISTART':>18} {'REFERENCE':>18} {'差異':>18} {'相對差異%':>12}")
        print("-" * 80)
        for col in ['a', 'd', 's', 'ln_likelihood']:
            n, r = new_ppe[col].values[0], ref_ppe[col].values[0]
            diff = n - r
            rel_diff = abs(diff / r * 100) if r != 0 else 0
            status = "✅" if rel_diff < 0.01 else "⚠️" if rel_diff < 1.0 else "❌"
            print(f"{status} {col:<13} {n:18.10f} {r:18.10f} {diff:+18.10f} {rel_diff:11.6f}")
    except Exception as e:
        print(f"❌ PPE 比較失敗: {e}")

    # EEPAS
    try:
        new_eepas = pd.read_csv(f"{new_dir}/Fitted_par_EEPAS_1990_2012.csv")
        ref_eepas = pd.read_csv(f"{ref_dir}/Fitted_par_EEPAS_1990_2012.csv")
        print("\n📊 EEPAS Parameters:")
        print(f"{'參數':<15} {'NO MULTISTART':>18} {'REFERENCE':>18} {'差異':>18} {'相對差異%':>12}")
        print("-" * 80)
        for col in ['am', 'bm', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u', 'ln_likelihood']:
            n, r = new_eepas[col].values[0], ref_eepas[col].values[0]
            diff = n - r
            rel_diff = abs(diff / r * 100) if r != 0 else 0
            status = "✅" if rel_diff < 0.01 else "⚠️" if rel_diff < 1.0 else "❌"
            print(f"{status} {col:<13} {n:18.10f} {r:18.10f} {diff:+18.10f} {rel_diff:11.6f}")
    except Exception as e:
        print(f"❌ EEPAS 比較失敗: {e}")

    # Forecast
    try:
        new_ppe_mat = sio.loadmat(f"{new_dir}/PREVISIONI_3m_PPE_2012_2022.mat")
        ref_ppe_mat = sio.loadmat(f"{ref_dir}/PREVISIONI_3m_PPE_2012_2022.mat")
        new_ppe_lambda = np.sum(new_ppe_mat['PREVISIONI_3m'][:, 1:])
        ref_ppe_lambda = np.sum(ref_ppe_mat['PREVISIONI_3m'][:, 1:])

        new_eepas_mat = sio.loadmat(f"{new_dir}/PREVISIONI_3m_EEPAS_2012_2022.mat")
        ref_eepas_mat = sio.loadmat(f"{ref_dir}/PREVISIONI_3m_EEPAS_2012_2022.mat")
        new_eepas_lambda = np.sum(new_eepas_mat['PREVISIONI_3m_less'][:, 1:])
        ref_eepas_lambda = np.sum(ref_eepas_mat['PREVISIONI_3m_less'][:, 1:])

        print("\n📊 Forecast Lambda 總和:")
        print("-" * 80)
        ppe_diff = new_ppe_lambda - ref_ppe_lambda
        ppe_rel = abs(ppe_diff / ref_ppe_lambda * 100) if ref_ppe_lambda != 0 else 0
        eepas_diff = new_eepas_lambda - ref_eepas_lambda
        eepas_rel = abs(eepas_diff / ref_eepas_lambda * 100) if ref_eepas_lambda != 0 else 0

        ppe_status = "✅" if ppe_rel < 0.01 else "⚠️" if ppe_rel < 1.0 else "❌"
        eepas_status = "✅" if eepas_rel < 0.01 else "⚠️" if eepas_rel < 1.0 else "❌"

        print(f"{ppe_status} PPE:   新={new_ppe_lambda:12.6f}, 參考={ref_ppe_lambda:12.6f}, 差={ppe_diff:+12.6f} ({ppe_rel:8.4f}%)")
        print(f"{eepas_status} EEPAS: 新={new_eepas_lambda:12.6f}, 參考={ref_eepas_lambda:12.6f}, 差={eepas_diff:+12.6f} ({eepas_rel:8.4f}%)")
    except Exception as e:
        print(f"❌ Forecast 比較失敗: {e}")

print("\n" + "="*80)
print("NO MULTISTART 模式 vs REFERENCE 比較")
print("="*80)

compare("results_italy_causal_ew0_new_no_multistart", "results_italy_causal_ew0_reference", "Phase 1: EW0 (快速)")
compare("results_italy_causal_ew1_new_no_multistart", "results_italy_causal_ew1_reference", "Phase 2: EW1 (快速)")
compare("results_italy_causal_ew0_accurate_new_no_multistart", "results_italy_causal_ew0_accurate_reference", "Phase 3: EW0 (精確)")

print("\n" + "="*80)
print("✅ NO MULTISTART 測試完成！")
print("="*80)
PYEOF

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "測試完成！"
echo "════════════════════════════════════════════════════════════════════════════════"
