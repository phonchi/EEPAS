#!/bin/bash
# 新策略系統驗證腳本
# 使用新格式配置執行完整流程，並與舊格式結果比較

set -e  # 遇到錯誤立即停止

echo "════════════════════════════════════════════════════════════════════════════════"
echo "EEPAS 新策略系統驗證 - 自動執行腳本"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  重要提示:"
echo "   - 預計總執行時間: 10-12 小時"
echo "   - 將使用新格式配置（biondini2023 策略）"
echo "   - 不要中斷執行"
echo "   - 建議在 tmux/screen 中執行"
echo ""
echo "✅ 自動執行模式，跳過確認"
echo ""

cd /home/math/EEPAS_Taiwan-main/src/python_src

# ================================================================================
# Phase 1: config_italy_causal_ew0_new.json (快速模式, 新策略)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 1: config_italy_causal_ew0_new.json (快速模式, 新策略)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 (--fast)"
echo "🎯 策略: biondini2023"
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
echo "Step 3/5: EEPAS Learning (三階段優化, 新策略系統)"
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
echo "✅ Phase 1 完成: config_italy_causal_ew0_new.json"

# ================================================================================
# Phase 2: config_italy_causal_ew1_new.json (快速模式, 新策略)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 2: config_italy_causal_ew1_new.json (快速模式, 新策略, 加權 ew1)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew1_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 快速 (--fast) + 加權 ew1"
echo "🎯 策略: biondini2023"
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
echo "Step 3/5: EEPAS Learning (三階段優化, 新策略系統)"
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
echo "✅ Phase 2 完成: config_italy_causal_ew1_new.json"

# ================================================================================
# Phase 3: config_italy_causal_ew0_accurate_new.json (精確模式, 新策略)
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 3: config_italy_causal_ew0_accurate_new.json (精確模式, 新策略)"
echo "════════════════════════════════════════════════════════════════════════════════"

CONFIG="config_italy_causal_ew0_accurate_new.json"
echo ""
echo "🔧 配置: $CONFIG"
echo "📊 模式: 精確 (--accurate)"
echo "🎯 策略: biondini2023"
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
echo "Step 3/5: EEPAS Learning (三階段優化, 精確模式, 新策略系統)"
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
echo "✅ Phase 3 完成: config_italy_causal_ew0_accurate_new.json"

# ================================================================================
# Phase 4: 結果比較
# ================================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Phase 4: 結果比較與驗證"
echo "════════════════════════════════════════════════════════════════════════════════"

python3 compare_new_vs_old_results.py

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "驗證完成！"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📄 詳細報告: NEW_STRATEGY_VERIFICATION_RESULTS.md"
echo ""
