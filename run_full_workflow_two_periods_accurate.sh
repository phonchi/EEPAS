#!/bin/bash
#
# EEPAS 完整流程：兩個時期的預測 (1990-2012 和 2012-2022)
# 使用 useCausalEW=0 和 useCausalEW=1 兩種模式
# ⚡ ACCURATE 模式 - 使用精確數值積分
#

set -e  # 遇到錯誤立即退出

echo "========================================"
echo "EEPAS 雙時期預測流程 (ACCURATE 模式)"
echo "========================================"
echo ""
echo "學習期間: 1990-2012"
echo "預測期間: 2012-2022 (out-of-sample)"
echo "測試模式: useCausalEW=0 和 useCausalEW=1"
echo "積分模式: ACCURATE (dblquad精確積分)"
echo ""

# ===========================================
# Part 1: useCausalEW=0 完整流程 (ACCURATE)
# ===========================================

echo "========================================"
echo "Part 1: useCausalEW=0 (Fixed EW) - ACCURATE"
echo "========================================"

CONFIG_EW0="config_italy_causal_ew0_accurate.json"
RESULTS_EW0="results_italy_causal_ew0_accurate"

# 清理舊結果
if [ -d "$RESULTS_EW0" ]; then
    echo "清理舊結果目錄: $RESULTS_EW0"
    rm -rf "$RESULTS_EW0"
fi
mkdir -p "$RESULTS_EW0"

echo ""
echo "--- Step 1/5: PPE Learning (ACCURATE) ---"
python3 ppe_learning.py --config "$CONFIG_EW0" --accurate

echo ""
echo "--- Step 2/5: Aftershock Parameters Fitting (ACCURATE) ---"
python3 fit_aftershock_params.py --config "$CONFIG_EW0" --accurate

echo ""
echo "--- Step 3/5: EEPAS Learning (ACCURATE) ---"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_EW0" --three-stage --no-boundary-adjustment --accurate

echo ""
echo "--- Step 4/5: PPE Forecast (ACCURATE) ---"
python3 ppe_make_forecast.py --config "$CONFIG_EW0" --accurate

echo ""
echo "--- Step 5/5: EEPAS Forecast (ACCURATE) ---"
python3 eepas_make_forecast.py --config "$CONFIG_EW0" --accurate

echo ""
echo "✅ useCausalEW=0 ACCURATE 流程完成"
echo ""

# ===========================================
# Part 2: useCausalEW=1 完整流程 (ACCURATE)
# ===========================================

echo "========================================"
echo "Part 2: useCausalEW=1 (Dynamic EW) - ACCURATE"
echo "========================================"

CONFIG_EW1="config_italy_causal_ew1_accurate.json"
RESULTS_EW1="results_italy_causal_ew1_accurate"

# 清理舊結果
if [ -d "$RESULTS_EW1" ]; then
    echo "清理舊結果目錄: $RESULTS_EW1"
    rm -rf "$RESULTS_EW1"
fi
mkdir -p "$RESULTS_EW1"

echo ""
echo "--- Step 1/5: PPE Learning (ACCURATE) ---"
python3 ppe_learning.py --config "$CONFIG_EW1" --accurate

echo ""
echo "--- Step 2/5: Aftershock Parameters Fitting (ACCURATE) ---"
python3 fit_aftershock_params.py --config "$CONFIG_EW1" --accurate

echo ""
echo "--- Step 3/5: EEPAS Learning (ACCURATE) ---"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_EW1" --three-stage --no-boundary-adjustment --accurate

echo ""
echo "--- Step 4/5: PPE Forecast (ACCURATE) ---"
python3 ppe_make_forecast.py --config "$CONFIG_EW1" --accurate

echo ""
echo "--- Step 5/5: EEPAS Forecast (ACCURATE) ---"
python3 eepas_make_forecast.py --config "$CONFIG_EW1" --accurate

echo ""
echo "✅ useCausalEW=1 ACCURATE 流程完成"
echo ""

# ===========================================
# Part 3: Lambda 分析
# ===========================================

echo "========================================"
echo "Part 3: Lambda 值分析 (ACCURATE)"
echo "========================================"

python3 -c "
import scipy.io as sio
import numpy as np
import os

print('\\n======== ACCURATE 模式 Lambda 總和分析 ========\\n')

# EW0 分析
results_ew0 = 'results_italy_causal_ew0_accurate'
if os.path.exists(f'{results_ew0}/PREVISIONI_3m_PPE_2012_2022.mat'):
    mat_ppe = sio.loadmat(f'{results_ew0}/PREVISIONI_3m_PPE_2012_2022.mat')
    ppe_forecast = mat_ppe['PREVISIONI_3m']
    ppe_lambda = np.sum(ppe_forecast[:, 1:])

    mat_eepas = sio.loadmat(f'{results_ew0}/PREVISIONI_3m_EEPAS_2012_2022.mat')
    eepas_forecast = mat_eepas['PREVISIONI_3m_less']
    eepas_lambda = np.sum(eepas_forecast[:, 1:])

    print('=== useCausalEW=0 (Fixed EW) ===')
    print(f'PPE Lambda 總和:    {ppe_lambda:.6f}')
    print(f'EEPAS Lambda 總和:  {eepas_lambda:.6f}')
    print(f'目標事件數量:       27')
    print()

# EW1 分析
results_ew1 = 'results_italy_causal_ew1_accurate'
if os.path.exists(f'{results_ew1}/PREVISIONI_3m_PPE_2012_2022.mat'):
    mat_ppe = sio.loadmat(f'{results_ew1}/PREVISIONI_3m_PPE_2012_2022.mat')
    ppe_forecast = mat_ppe['PREVISIONI_3m']
    ppe_lambda = np.sum(ppe_forecast[:, 1:])

    mat_eepas = sio.loadmat(f'{results_ew1}/PREVISIONI_3m_EEPAS_2012_2022.mat')
    eepas_forecast = mat_eepas['PREVISIONI_3m_less']
    eepas_lambda = np.sum(eepas_forecast[:, 1:])

    print('=== useCausalEW=1 (Dynamic EW) ===')
    print(f'PPE Lambda 總和:    {ppe_lambda:.6f}')
    print(f'EEPAS Lambda 總和:  {eepas_lambda:.6f}')
    print(f'目標事件數量:       27')
    print()
"

echo ""
echo "========================================"
echo "✅ 所有 ACCURATE 流程完成！"
echo "========================================"
echo ""
echo "結果目錄:"
echo "  - $RESULTS_EW0"
echo "  - $RESULTS_EW1"
echo ""
