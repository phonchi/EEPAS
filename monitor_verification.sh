#!/bin/bash
# 持續監控驗證進度

LOG_FILE="verification_run_20251129_000904.log"
CHECK_INTERVAL=300  # 每 5 分鐘檢查一次

echo "開始監控驗證進度..."
echo "日誌檔案: $LOG_FILE"
echo "檢查間隔: ${CHECK_INTERVAL} 秒"
echo ""

while true; do
    clear
    echo "═══════════════════════════════════════════════════════════════"
    echo "EEPAS 驗證進度監控 - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    # 檢查進程狀態
    if ps aux | grep -q "[r]un_new_strategy_verification.sh"; then
        echo "✅ 驗證腳本運行中"
        
        # 顯示當前執行的 Python 進程
        CURRENT_TASK=$(ps aux | grep "python3.*\(ppe_learning\|fit_aftershock\|eepas_learning\|ppe_make_forecast\|eepas_make_forecast\)" | grep -v grep | head -1 | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        
        if [ -n "$CURRENT_TASK" ]; then
            echo "🔄 當前任務: $CURRENT_TASK"
        fi
        
        echo ""
        echo "───────────────────────────────────────────────────────────────"
        echo "最新日誌 (最後 30 行):"
        echo "───────────────────────────────────────────────────────────────"
        tail -30 "$LOG_FILE"
        
    else
        echo "⚠️  驗證腳本已停止或完成"
        
        # 檢查是否成功完成
        if tail -20 "$LOG_FILE" | grep -q "驗證完成"; then
            echo "✅ 驗證已成功完成！"
            echo ""
            echo "最後 50 行日誌:"
            echo "───────────────────────────────────────────────────────────────"
            tail -50 "$LOG_FILE"
            break
        else
            echo "❌ 可能發生錯誤，請檢查日誌"
            echo ""
            echo "最後 50 行日誌:"
            echo "───────────────────────────────────────────────────────────────"
            tail -50 "$LOG_FILE"
            break
        fi
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "下次更新: $(date -d "+${CHECK_INTERVAL} seconds" '+%H:%M:%S')"
    echo "按 Ctrl+C 停止監控"
    echo "═══════════════════════════════════════════════════════════════"
    
    sleep $CHECK_INTERVAL
done
