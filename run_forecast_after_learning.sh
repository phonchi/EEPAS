#!/bin/bash
# 等待 EEPAS learning 完成後自動執行 forecast

CONFIG="config_italy_test_dynamic_ew.json"
RESULTS_DIR="results_italy_test_dynamic_ew"

echo "=========================================="
echo "等待 EEPAS learning 完成..."
echo "=========================================="

# 等待 EEPAS 參數檔案生成
while [ ! -f "$RESULTS_DIR/Fitted_par_EEPAS_1990_2012.csv" ]; do
    sleep 30
    echo "等待中..."
done

echo ""
echo "=========================================="
echo "✅ EEPAS learning 完成！"
echo "=========================================="

# 顯示學習到的參數
echo ""
echo "學習到的 EEPAS 參數："
cat "$RESULTS_DIR/Fitted_par_EEPAS_1990_2012.csv"

echo ""
echo "=========================================="
echo "開始執行 PPE forecast..."
echo "=========================================="
python3 ppe_make_forecast.py --config $CONFIG --ppe-ref-mag mT

echo ""
echo "=========================================="
echo "開始執行 EEPAS forecast..."
echo "=========================================="
python3 eepas_make_forecast.py --config $CONFIG --fast --ppe-ref-mag mT

echo ""
echo "=========================================="
echo "✅ Forecast 完成！"
echo "=========================================="

# 比較結果
echo ""
echo "比較預測結果..."
python3 << 'EOF'
import numpy as np
import scipy.io as sio

print("\n" + "="*80)
print("預測結果比較（動態 EW）")
print("="*80)

# 讀取 PPE forecast
ppe_file = 'results_italy_test_dynamic_ew/PREVISIONI_3m_PPE_1990_2012.mat'
eepas_file = 'results_italy_test_dynamic_ew/PREVISIONI_3m_EEPAS_1990_2012.mat'

try:
    ppe_data = sio.loadmat(ppe_file)
    eepas_data = sio.loadmat(eepas_file)

    ppe_forecast = ppe_data['PREVISIONI_3m']
    eepas_forecast = eepas_data['PREVISIONI_3m_less']

    # 排除第0列（標記列），只取第1到177列
    ppe_sum = np.sum(ppe_forecast[:, 1:178])
    eepas_sum = np.sum(eepas_forecast[:, 1:178])

    print(f"\nPPE 預測總數:   {ppe_sum:.2f}")
    print(f"EEPAS 預測總數: {eepas_sum:.2f}")
    print(f"EEPAS/PPE 比例: {eepas_sum/ppe_sum:.4f}")

    print("\n與基準比較（固定 EW）:")
    print(f"基準 PPE:       26.93")
    print(f"基準 EEPAS:     28.36")
    print(f"基準 EEPAS/PPE: 1.0531")

    print("\n與論文比較（Table 5）:")
    print(f"論文 PPE:       27.00")
    print(f"論文 EEPAS:     27.73")
    print(f"論文 EEPAS/PPE: 1.0270")

    print("\n觀測值:         27")

except Exception as e:
    print(f"錯誤: {e}")

print("="*80)
EOF

echo ""
echo "完成！"
