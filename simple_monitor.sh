#!/bin/bash
# 簡單的持續監控腳本

LOG_FILE="verification_run_20251129_000904.log"

echo "開始監控驗證進度..."
echo "日誌: $LOG_FILE"
echo ""

while true; do
    clear
    echo "═══════════════════════════════════════════════════════════════"
    echo "監控時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # 檢查驗證腳本是否運行
    if ps aux | grep -q "[r]un_new_strategy_verification.sh"; then
        echo "✅ 驗證腳本運行中"

        # 顯示當前 Python 任務
        TASK=$(ps aux | grep "python3.*\(ppe_learning\|fit_aftershock\|eepas_learning\|ppe_make_forecast\|eepas_make_forecast\)" | grep -v grep | head -1 | awk '{print $11, $12, $13, $14, $15}')
        if [ -n "$TASK" ]; then
            echo "🔄 當前任務: $TASK"
        fi

        echo ""
        echo "───────────────────────────────────────────────────────────────"
        echo "最新日誌 (最後 25 行):"
        echo "───────────────────────────────────────────────────────────────"
        tail -25 "$LOG_FILE"

        echo ""
        echo "───────────────────────────────────────────────────────────────"
        echo "下次更新: $(date -d '+5 minutes' '+%H:%M:%S')"
        echo "按 Ctrl+C 停止監控"
        echo "═══════════════════════════════════════════════════════════════"

        sleep 300

    else
        echo "⚠️  驗證腳本已停止"
        echo ""

        # 檢查是否完成
        if tail -30 "$LOG_FILE" | grep -q "驗證完成"; then
            echo "✅ 驗證已完成！準備進行比較..."
            echo ""

            # 立即進行比較
            if [ -d "results_italy_causal_ew0_new" ]; then
                echo "開始比較 Phase 1 (EW0)..."
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
        for col in ['a', 'd', 's', 'ln_likelihood']:
            n, r = new_ppe[col].values[0], ref_ppe[col].values[0]
            print(f"  {col}: 新={n:.10f}, 參考={r:.10f}, 差={n-r:+.10f}")
    except Exception as e:
        print(f"PPE 比較失敗: {e}")

    # EEPAS
    try:
        new_eepas = pd.read_csv(f"{new_dir}/Fitted_par_EEPAS_1990_2012.csv")
        ref_eepas = pd.read_csv(f"{ref_dir}/Fitted_par_EEPAS_1990_2012.csv")
        print("\n📊 EEPAS Parameters:")
        for col in ['am', 'bm', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u', 'ln_likelihood']:
            n, r = new_eepas[col].values[0], ref_eepas[col].values[0]
            print(f"  {col}: 新={n:.10f}, 參考={r:.10f}, 差={n-r:+.10f}")
    except Exception as e:
        print(f"EEPAS 比較失敗: {e}")

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

        print("\n📊 Forecast Lambda:")
        print(f"  PPE:   新={new_ppe_lambda:.6f}, 參考={ref_ppe_lambda:.6f}, 差={new_ppe_lambda-ref_ppe_lambda:+.6f}")
        print(f"  EEPAS: 新={new_eepas_lambda:.6f}, 參考={ref_eepas_lambda:.6f}, 差={new_eepas_lambda-ref_eepas_lambda:+.6f}")
    except Exception as e:
        print(f"Forecast 比較失敗: {e}")

compare("results_italy_causal_ew0_new", "results_italy_causal_ew0_reference", "Phase 1: EW0")
if __import__('os').path.exists("results_italy_causal_ew1_new"):
    compare("results_italy_causal_ew1_new", "results_italy_causal_ew1_reference", "Phase 2: EW1")
if __import__('os').path.exists("results_italy_causal_ew0_accurate_new"):
    compare("results_italy_causal_ew0_accurate_new", "results_italy_causal_ew0_accurate_reference", "Phase 3: EW0 Accurate")
PYEOF
            fi

            echo ""
            echo "✅ 比較完成！"
        else
            echo "❌ 驗證可能出錯，查看日誌最後 50 行:"
            tail -50 "$LOG_FILE"
        fi

        break
    fi
done
