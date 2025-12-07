#!/bin/bash
# EEPAS 功能驗證自動執行腳本
# 重新執行三個配置的完整五步驟流程

set -e  # 遇到錯誤立即停止

echo "════════════════════════════════════════════════════════════════════════════════"
echo "EEPAS 功能驗證 - 自動執行腳本"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  重要提示:"
echo "   - 預計總執行時間: 10-12 小時"
echo "   - 不要中斷執行"
echo "   - 建議在 tmux/screen 中執行"
echo ""
echo "按 Enter 繼續，或 Ctrl+C 取消..."
read

cd /home/math/EEPAS_Taiwan-main/src/python_src

# ================================================================================
# Phase 1: config_italy_causal_ew0.json (快速模式)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 1: config_italy_causal_ew0.json (快速模式)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 (--fast)"
echo ""

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG" 
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG" --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG" --three-stage --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG" --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG" --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 1 完成: config_italy_causal_ew0.json"

# ================================================================================
# Phase 2: config_italy_causal_ew1.json (快速模式)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 2: config_italy_causal_ew1.json (快速模式, 加權 ew1)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew1.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 (--fast) + 加權 ew1"
echo ""

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG" 
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG" --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG" --three-stage --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG" --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG" --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 2 完成: config_italy_causal_ew1.json"

# ================================================================================
# Phase 3: config_italy_causal_ew0_accurate.json (精確模式)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 3: config_italy_causal_ew0_accurate.json (精確模式)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0_accurate.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 精確 (--accurate)"
echo "⚠️  警告: 此階段需要 6-8 小時"
echo ""

# Step 1: PPE Learning
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/5: PPE Learning (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_learning.py --config "$CONFIG" --accurate
echo "✅ Step 1 完成"

# Step 2: Aftershock Fitting
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/5: Aftershock Parameters Fitting (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 fit_aftershock_params.py --config "$CONFIG" --accurate --ppe-ref-mag mT --target-mag mT
echo "✅ Step 2 完成"

# Step 3: EEPAS Learning
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/5: EEPAS Learning (三階段優化, 精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_learning_auto_boundary.py --config "$CONFIG" --three-stage --accurate --ppe-ref-mag mT --max-rounds 1
echo "✅ Step 3 完成"

# Step 4: PPE Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4/5: PPE Forecast (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 ppe_make_forecast.py --config "$CONFIG" --accurate --ppe-ref-mag mT
echo "✅ Step 4 完成"

# Step 5: EEPAS Forecast
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5/5: EEPAS Forecast (精確模式)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 eepas_make_forecast.py --config "$CONFIG" --accurate --ppe-ref-mag mT
echo "✅ Step 5 完成"

echo ""
echo "✅ Phase 3 完成: config_italy_causal_ew0_accurate.json"

# ================================================================================
# Phase 4: 結果比較
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 4: 結果比較與驗證"
echo "════════════════════════════════════════════════════════════════════════════════"

python3 compare_results.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "驗證完成！"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📄 詳細報告: VERIFICATION_RESULTS.md"
echo "📋 執行計劃: VERIFICATION_PLAN.md"
echo ""
