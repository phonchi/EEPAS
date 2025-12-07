#!/usr/bin/env python3
"""
EEPAS地震權重計算 - 餘震去權重核心模組

== 地震學背景 ==
在EEPAS模型中，每個地震都被視為潛在的「前震」。
但地震目錄中包含大量餘震，它們不是真正的前兆信號。

本模組計算每個地震的「獨立性權重」wᵢ：
  - wᵢ ≈ 1: 地震很可能是獨立事件（非餘震）→ 應被視為前震
  - wᵢ ≈ 0: 地震很可能是餘震 → 應降低其前震地位

== 權重公式 ==
  wᵢ = ν·λ₀(tᵢ,mᵢ,xᵢ,yᵢ) / λ'(tᵢ,mᵢ,xᵢ,yᵢ)

其中：
  - λ₀: PPE背景率（第一步學習的）
  - λ': 餘震模型預測的總率（背景 + 所有前面地震的餘震貢獻）
  - ν: 非餘震比例（第二步學習的）

== 使用場景 ==
權重 wᵢ 在EEPAS第三步優化中使用：
  - 加權對數概似函數
  - 降低餘震對前震信號的污染
  - 提高模型對真正前兆的敏感度
"""

import numpy as np
import os
import sys
from numba import njit, prange

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.data_loader import DataLoader


def calculate_earthquake_weights(CatE, CatI, params, weight_flag, delay, config_file='config.json', ppe_ref_mag=None):
    """
    計算每個地震的獨立性權重 wᵢ

    參數說明:
        CatE: EEPAS完整目錄（M≥m0的所有地震）
              每一列是一個地震事件，包含時間、位置、震級等
        CatI: PPE背景目錄（M≥mT的歷史地震，來自 neighborhood region N）- 論文中的 i
              用於計算PPE背景率 λ₀
        params: 模型參數字典，包含：
              - B: b-value（Gutenberg-Richter關係）
              - delta: Bath's law 參數（餘震震級上限）
              - mT, m0, mu: 震級閾值
              - a, d, s: PPE參數（第一步學習的）
        weight_flag: 權重模式
              0 = 均勻權重（wᵢ=1，不考慮餘震）
              1 = 計算權重（使用餘震模型）
        delay: 延遲天數（地震發生後多久才開始計入）
        config_file: 配置文件路徑

    返回:
        W: 權重向量（長度=len(CatE)）
           每個元素 wᵢ ∈ [0,1] 表示第i個地震的獨立性
        EW: 期望權重（所有權重的平均值）
        CatE_updated: 清理NaN後的目錄矩陣
    """

    # ===== 提取地震屬性 =====
    # CatE: 待計算權重的地震目錄
    me = CatE[:, 9]   # 震級
    te = CatE[:, 10]  # 時間（天）
    ye = CatE[:, 6]   # 緯度
    xe = CatE[:, 7]   # 經度

    # CatI: PPE背景目錄（歷史源事件，論文中的 i，用於計算 λ₀）
    mi = CatI[:, 9]
    ti = CatI[:, 10]
    yi = CatI[:, 6]
    xi = CatI[:, 7]

    # b-value（轉換為自然對數）
    B = params['B'] * np.log(10)

    # PPE參考震級：默認使用mT，但可以指定為m0
    if ppe_ref_mag is None:
        ppe_ref_mag_value = params['mT']
    elif ppe_ref_mag == 'm0':
        ppe_ref_mag_value = params['m0']
        print(f'Using PPE reference magnitude: m0 = {ppe_ref_mag_value}')
    elif ppe_ref_mag == 'mT':
        ppe_ref_mag_value = params['mT']
        print(f'Using PPE reference magnitude: mT = {ppe_ref_mag_value}')
    else:
        ppe_ref_mag_value = ppe_ref_mag  # 直接使用數值

    # ===== 權重計算模式 =====
    if weight_flag == 0:
        # 模式0：均勻權重（不考慮餘震）
        # 所有地震都被平等對待，wᵢ = 1
        W = np.ones(len(CatE))
    else:
        # 模式1：計算餘震去權重
        Del = params['delta']  # Bath's law 參數

        # 載入第二步學習的餘震參數 (ν, κ)
        cfg = DataLoader.load_config(config_file)
        aftershock_param_pattern = cfg['outputFiles']['AftershockParamPattern']
        results_dir = cfg['resultsDir']
        if not os.path.isabs(results_dir):
            results_dir = os.path.abspath(results_dir)
        aftershock_param_file = os.path.join(
            results_dir,
            aftershock_param_pattern % (cfg['learnStartYear'], cfg['learnEndYear'])
        )

        if not os.path.exists(aftershock_param_file):
            raise FileNotFoundError(
                f'找不到 aftershock 參數檔案: {aftershock_param_file}\n'
                f'請先執行 fit_aftershock_params 來產生此檔案'
            )

        aftershock_params = np.genfromtxt(aftershock_param_file, delimiter=',', names=True)
        v = aftershock_params['v']
        k = aftershock_params['k']
        print(f'Loaded v, k parameters from file: v={v:.6f}, k={k:.6f} (file: {aftershock_param_file})')

        print(f'⚖️  Calculating earthquake weights ({len(CatE)} events)...')

        # 使用 Numba 加速的權重計算
        @njit(parallel=True, fastmath=True)
        def compute_weights_numba(me, te, ye, xe, mi, ti, yi, xi, B, delay, Del,
                                  a, d, s, m0, ppe_ref_mag_value, p, c, sigmaU):
            n = len(me)
            WPPE = np.zeros(n)
            WFORE = np.zeros(n)

            for e in prange(n):
                # 計算PPE權重
                ppe_sum = 0.0
                for i in range(len(mi)):
                    if ti[i] < te[e] - delay:
                        r_sq = (yi[i] - ye[e])**2 + (xi[i] - xe[e])**2
                        ppe_sum += a * (mi[i] - ppe_ref_mag_value) * (1.0/np.pi) / (d**2 + r_sq) + s

                WPPE[e] = (B / te[e]) * np.exp(-B * (me[e] - ppe_ref_mag_value)) * ppe_sum

                # 計算前震權重
                fore_sum = 0.0
                for j in range(e):
                    if me[j] - Del - me[e] > 0:
                        time_decay = (p - 1) / (te[e] - te[j] + c)**p
                        mag_dist = B * np.exp(-B * (me[e] - me[j]))
                        r_sq = (xe[e] - xe[j])**2 + (ye[e] - ye[j])**2
                        space_dist = (1.0 / (2.0 * np.pi * sigmaU**2 * 10**me[j])) * \
                                    np.exp(-r_sq / (2.0 * sigmaU**2 * 10**me[j]))
                        fore_sum += time_decay * mag_dist * space_dist

                WFORE[e] = fore_sum

            return WPPE, WFORE

        WPPE, WFORE = compute_weights_numba(
            me, te, ye, xe, mi, ti, yi, xi, B, delay, Del,
            params['a'], params['d'], params['s'], params['m0'], ppe_ref_mag_value,
            params['p'], params['c'], params['sigmaU']
        )

        print('✅ Weight calculation completed')
        W = (v * WPPE) / (v * WPPE + k * WFORE)

        # Handle NaN values
        ww = np.isnan(W)
        if np.any(ww):
            print(f'Warning: Detected {np.sum(ww)} NaN values, removing these entries')
            W = W[~ww]
            CatE = CatE[~ww]

    # 計算平均權重
    EW = np.mean(W)

    return W, EW, CatE
