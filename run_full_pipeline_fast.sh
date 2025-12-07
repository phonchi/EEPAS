#!/bin/bash
# 完整五步驟流程 - 快速模式
# 配置文件：config_italy_refactor_test.json

set -e  # 遇到錯誤立即停止

CONFIG="config_italy_refactor_test.json"
LOG_PREFIX="refactor_test_fast"

echo "================================================================================"
echo "開始執行完整 EEPAS 五步驟流程（快速模式）"
echo "配置文件: $CONFIG"
echo "================================================================================"

# Step 1: PPE Learning
echo ""
echo ">>> Step 1/5: PPE Learning (快速模式, 30x30網格)"
python3 ppe_learning.py --config $CONFIG --grid-res 30 2>&1 | tee ${LOG_PREFIX}_step1_ppe.log
if [ $? -eq 0 ]; then
    echo "✅ Step 1 完成"
else
    echo "❌ Step 1 失敗"
    exit 1
fi

# Step 2: Aftershock Parameters Fitting
echo ""
echo ">>> Step 2/5: Aftershock Parameters Fitting (快速模式, 50x50網格)"
python3 fit_aftershock_params.py --config $CONFIG --ppe-ref-mag mT --target-mag mT --fast 2>&1 | tee ${LOG_PREFIX}_step2_aftershock.log
if [ $? -eq 0 ]; then
    echo "✅ Step 2 完成"
else
    echo "❌ Step 2 失敗"
    exit 1
fi

# Step 3: EEPAS Learning
echo ""
echo ">>> Step 3/5: EEPAS Learning (三階段 + 單輪優化)"
python3 eepas_learning_auto_boundary.py --config $CONFIG --three-stage --ppe-ref-mag mT --max-rounds 1 2>&1 | tee ${LOG_PREFIX}_step3_eepas.log
if [ $? -eq 0 ]; then
    echo "✅ Step 3 完成"
else
    echo "❌ Step 3 失敗"
    exit 1
fi

# Step 4: PPE Forecast
echo ""
echo ">>> Step 4/5: PPE Forecast (快速模式)"
python3 ppe_make_forecast.py --config $CONFIG --ppe-ref-mag mT 2>&1 | tee ${LOG_PREFIX}_step4_ppe_forecast.log
if [ $? -eq 0 ]; then
    echo "✅ Step 4 完成"
else
    echo "❌ Step 4 失敗"
    exit 1
fi

# Step 5: EEPAS Forecast
echo ""
echo ">>> Step 5/5: EEPAS Forecast (快速模式)"
python3 eepas_make_forecast.py --config $CONFIG --fast --ppe-ref-mag mT 2>&1 | tee ${LOG_PREFIX}_step5_eepas_forecast.log
if [ $? -eq 0 ]; then
    echo "✅ Step 5 完成"
else
    echo "❌ Step 5 失敗"
    exit 1
fi

echo ""
echo "================================================================================"
echo "✅ 完整五步驟流程執行完成！"
echo "================================================================================"
echo ""
echo "結果保存在: results_italy_test_dynamic_ew/"
echo ""
echo "查看結果："
echo "  PPE 參數:        cat results_italy_test_dynamic_ew/Fitted_par_PPE_1990_2012.csv"
echo "  Aftershock 參數: cat results_italy_test_dynamic_ew/Fitted_par_aftershock_1990_2012.csv"
echo "  EEPAS 參數:      cat results_italy_test_dynamic_ew/Fitted_par_EEPAS_1990_2012.csv"
