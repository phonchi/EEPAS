#!/bin/bash

# EEPAS Causality Comparison Test
# 比較 useCausalEW=0 和 useCausalEW=1 兩種模式的結果

set -e  # Exit on error

echo "========================================"
echo "EEPAS Causality Comparison Test"
echo "========================================"
echo ""

# Configuration
CONFIG_EW0="config_italy_causal_ew0.json"
CONFIG_EW1="config_italy_causal_ew1.json"
LOG_DIR="logs_causal_comparison"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to run complete workflow
run_workflow() {
    local config=$1
    local label=$2
    local log_prefix="${LOG_DIR}/${label}"

    echo "----------------------------------------"
    echo "Running workflow for $label"
    echo "Config: $config"
    echo "----------------------------------------"
    echo ""

    # Step 1: PPE Learning (fast mode)
    echo "Step 1/5: PPE Learning (fast mode)..."
    python3 ppe_learning.py --config "$config" --grid-res 30 2>&1 | tee "${log_prefix}_step1_ppe.log"
    echo "✓ PPE Learning completed"
    echo ""

    # Step 2: Aftershock Parameters Fitting (fast mode)
    echo "Step 2/5: Aftershock Parameters Fitting (fast mode)..."
    python3 fit_aftershock_params.py --config "$config" --fast --ppe-ref-mag mT --target-mag mT 2>&1 | tee "${log_prefix}_step2_aftershock.log"
    echo "✓ Aftershock fitting completed"
    echo ""

    # Step 3: EEPAS Learning (fast mode, three-stage)
    echo "Step 3/5: EEPAS Learning (fast mode, three-stage)..."
    python3 eepas_learning_auto_boundary.py --config "$config" --three-stage --fast --ppe-ref-mag mT --max-rounds 1 2>&1 | tee "${log_prefix}_step3_eepas.log"
    echo "✓ EEPAS Learning completed"
    echo ""

    # Step 4: PPE Forecast (fast mode)
    echo "Step 4/5: PPE Forecast (fast mode)..."
    python3 ppe_make_forecast.py --config "$config" --fast --ppe-ref-mag mT 2>&1 | tee "${log_prefix}_step4_ppe_forecast.log"
    echo "✓ PPE Forecast completed"
    echo ""

    # Step 5: EEPAS Forecast (fast mode)
    echo "Step 5/5: EEPAS Forecast (fast mode)..."
    python3 eepas_make_forecast.py --config "$config" --fast --ppe-ref-mag mT 2>&1 | tee "${log_prefix}_step5_eepas_forecast.log"
    echo "✓ EEPAS Forecast completed"
    echo ""

    echo "✓✓✓ Workflow for $label completed successfully ✓✓✓"
    echo ""
}

# Run workflow for useCausalEW=0
echo "========================================"
echo "Part 1: useCausalEW=0 (Fixed EW per period)"
echo "========================================"
echo ""
run_workflow "$CONFIG_EW0" "ew0"

# Run workflow for useCausalEW=1
echo "========================================"
echo "Part 2: useCausalEW=1 (Dynamic EW)"
echo "========================================"
echo ""
run_workflow "$CONFIG_EW1" "ew1"

# Summary
echo "========================================"
echo "✓ All workflows completed successfully!"
echo "========================================"
echo ""
echo "Results:"
echo "  - useCausalEW=0: results_italy_causal_ew0/"
echo "  - useCausalEW=1: results_italy_causal_ew1/"
echo ""
echo "Logs:"
echo "  - All logs saved in: ${LOG_DIR}/"
echo ""
echo "Next steps:"
echo "  1. Compare learned parameters (CSV files)"
echo "  2. Compare forecast outputs (.mat files)"
echo "  3. Analyze EW differences"
echo ""
