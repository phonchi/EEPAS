#!/bin/bash
#
# EEPAS 完整流程：兩個時期的預測 (1990-2012 和 2012-2022)
# 使用 useCausalEW=0 和 useCausalEW=1 兩種模式
#

set -e  # 遇到錯誤立即退出

echo "========================================"
echo "EEPAS 雙時期預測流程"
echo "========================================"
echo ""
echo "學習期間: 1990-2012"
echo "預測期間1: 1990-2012 (in-sample)"
echo "預測期間2: 2012-2022 (out-of-sample)"
echo "測試模式: useCausalEW=0 和 useCausalEW=1"
echo ""

# ===========================================
# Part 1: useCausalEW=0 完整流程
# ===========================================

echo "========================================"
echo "Part 1: useCausalEW=0 (Fixed EW)"
echo "========================================"

CONFIG_EW0="config_italy_causal_ew0.json"
RESULTS_EW0="results_italy_causal_ew0"

# 清理舊結果
if [ -d "$RESULTS_EW0" ]; then
    echo "清理舊結果目錄: $RESULTS_EW0"
    rm -rf "$RESULTS_EW0"
fi
mkdir -p "$RESULTS_EW0"

echo ""
echo "--- Step 1/5: PPE Learning ---"
python3 ppe_learning.py --config "$CONFIG_EW0"

echo ""
echo "--- Step 2/5: Aftershock Parameters Fitting ---"
python3 fit_aftershock_params.py --config "$CONFIG_EW0"

echo ""
echo "--- Step 3/5: EEPAS Learning ---"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_EW0" --three-stage --no-boundary-adjustment

echo ""
echo "--- Step 4/5: PPE Forecast (2012-2022) ---"
python3 ppe_make_forecast.py --config "$CONFIG_EW0"

echo ""
echo "--- Step 5/5: EEPAS Forecast (2012-2022) ---"
python3 eepas_make_forecast.py --config "$CONFIG_EW0"

echo ""
echo "✅ useCausalEW=0 流程完成"
echo ""

# ===========================================
# Part 2: useCausalEW=1 完整流程
# ===========================================

echo "========================================"
echo "Part 2: useCausalEW=1 (Dynamic EW)"
echo "========================================"

CONFIG_EW1="config_italy_causal_ew1.json"
RESULTS_EW1="results_italy_causal_ew1"

# 清理舊結果
if [ -d "$RESULTS_EW1" ]; then
    echo "清理舊結果目錄: $RESULTS_EW1"
    rm -rf "$RESULTS_EW1"
fi
mkdir -p "$RESULTS_EW1"

echo ""
echo "--- Step 1/5: PPE Learning ---"
python3 ppe_learning.py --config "$CONFIG_EW1"

echo ""
echo "--- Step 2/5: Aftershock Parameters Fitting ---"
python3 fit_aftershock_params.py --config "$CONFIG_EW1"

echo ""
echo "--- Step 3/5: EEPAS Learning ---"
python3 eepas_learning_auto_boundary.py --config "$CONFIG_EW1" --three-stage --no-boundary-adjustment

echo ""
echo "--- Step 4/5: PPE Forecast (2012-2022) ---"
python3 ppe_make_forecast.py --config "$CONFIG_EW1"

echo ""
echo "--- Step 5/5: EEPAS Forecast (2012-2022) ---"
python3 eepas_make_forecast.py --config "$CONFIG_EW1"

echo ""
echo "✅ useCausalEW=1 流程完成"
echo ""

# ===========================================
# Part 3: Lambda 分析
# ===========================================

echo "========================================"
echo "Part 3: Lambda 值分析"
echo "========================================"

python3 analysis/analyze_forecast_lambda.py

echo ""
echo "========================================"
echo "✅ 所有流程完成！"
echo "========================================"
echo ""
echo "結果目錄:"
echo "  - $RESULTS_EW0"
echo "  - $RESULTS_EW1"
echo ""
echo "請查看 lambda_comparison_corrected.log 獲取詳細分析結果"
