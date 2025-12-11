#!/usr/bin/env python3
"""
EEPAS Earthquake Weight Calculation - Aftershock Deweighting Core Module

== Seismological Background ==
In the EEPAS model, every earthquake is viewed as a potential "precursor".
However, earthquake catalogs contain many aftershocks, which are not true precursory signals.

This module calculates the "independence weight" wᵢ for each earthquake:
  - wᵢ ≈ 1: earthquake is likely an independent event (not an aftershock) → should be treated as precursor
  - wᵢ ≈ 0: earthquake is likely an aftershock → should reduce its precursor status

== Weight Formula ==
  wᵢ = ν·λ₀(tᵢ,mᵢ,xᵢ,yᵢ) / λ'(tᵢ,mᵢ,xᵢ,yᵢ)

Where:
  - λ₀: PPE baseline rate (learned in Step 1)
  - λ': Total rate predicted by aftershock model (baseline + aftershock contributions from all previous events)
  - ν: Non-aftershock proportion (learned in Step 2)

== Usage ==
Weights wᵢ are used in EEPAS Step 3 optimization:
  - Weighted log-likelihood function
  - Reduce contamination of precursory signals by aftershocks
  - Improve model sensitivity to true precursors
"""

import numpy as np
import os
import sys
from numba import njit, prange

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.data_loader import DataLoader


def calculate_earthquake_weights(CatE, CatI, params, weight_flag, delay, config_file='config.json', ppe_ref_mag=None):
    """
    Calculate independence weight wᵢ for each earthquake

    Parameters
    ----------
    CatE : ndarray
        EEPAS complete catalog (all earthquakes with M≥m0)
        Each row is an earthquake event with time, location, magnitude, etc.
    CatI : ndarray
        PPE background catalog (historical earthquakes with M≥mT from neighborhood region N) - 'i' in paper
        Used to calculate PPE baseline rate λ₀
    params : dict
        Model parameter dictionary containing:
        - B: b-value (Gutenberg-Richter relation)
        - delta: Bath's law parameter (aftershock magnitude upper bound)
        - mT, m0, mu: magnitude thresholds
        - a, d, s: PPE parameters (learned in Step 1)
    weight_flag : int
        Weight mode
        0 = uniform weights (wᵢ=1, ignore aftershocks)
        1 = calculate weights (using aftershock model)
    delay : float
        Delay period in days (how long after earthquake occurrence to start counting)
    config_file : str
        Configuration file path
    ppe_ref_mag : str or float, optional
        PPE reference magnitude ('m0', 'mT', or numeric value)

    Returns
    -------
    W : ndarray
        Weight vector (length=len(CatE))
        Each element wᵢ ∈ [0,1] represents independence of i-th earthquake
    EW : float
        Expected weight (average of all weights)
    CatE_updated : ndarray
        Catalog matrix after removing NaN values
    """

    # ===== Extract earthquake attributes =====
    # CatE: catalog for weight calculation
    me = CatE[:, 9]   # magnitude
    te = CatE[:, 10]  # time (days)
    ye = CatE[:, 6]   # latitude
    xe = CatE[:, 7]   # longitude

    # CatI: PPE background catalog (historical source events, 'i' in paper, for calculating λ₀)
    mi = CatI[:, 9]
    ti = CatI[:, 10]
    yi = CatI[:, 6]
    xi = CatI[:, 7]

    # b-value (convert to natural logarithm)
    B = params['B'] * np.log(10)

    # PPE reference magnitude: default uses mT, but can be specified as m0
    if ppe_ref_mag is None:
        ppe_ref_mag_value = params['mT']
    elif ppe_ref_mag == 'm0':
        ppe_ref_mag_value = params['m0']
        print(f'Using PPE reference magnitude: m0 = {ppe_ref_mag_value}')
    elif ppe_ref_mag == 'mT':
        ppe_ref_mag_value = params['mT']
        print(f'Using PPE reference magnitude: mT = {ppe_ref_mag_value}')
    else:
        ppe_ref_mag_value = ppe_ref_mag  # use numeric value directly

    # ===== Weight calculation mode =====
    if weight_flag == 0:
        # Mode 0: Uniform weights (ignore aftershocks)
        # All earthquakes are treated equally, wᵢ = 1
        W = np.ones(len(CatE))
    else:
        # Mode 1: Calculate aftershock deweighting
        Del = params['delta']  # Bath's law parameter

        # Load aftershock parameters (ν, κ) learned in Step 2
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
                f'Cannot find aftershock parameter file: {aftershock_param_file}\n'
                f'Please run fit_aftershock_params first to generate this file'
            )

        aftershock_params = np.genfromtxt(aftershock_param_file, delimiter=',', names=True)
        v = aftershock_params['v']
        k = aftershock_params['k']
        print(f'Loaded v, k parameters from file: v={v:.6f}, k={k:.6f} (file: {aftershock_param_file})')

        print(f'⚖️  Calculating earthquake weights ({len(CatE)} events)...')

        # Use Numba-accelerated weight calculation
        @njit(parallel=True, fastmath=True)
        def compute_weights_numba(me, te, ye, xe, mi, ti, yi, xi, B, delay, Del,
                                  a, d, s, m0, ppe_ref_mag_value, p, c, sigmaU):
            n = len(me)
            WPPE = np.zeros(n)
            WFORE = np.zeros(n)

            for e in prange(n):
                # Calculate PPE weight
                ppe_sum = 0.0
                for i in range(len(mi)):
                    if ti[i] < te[e] - delay:
                        r_sq = (yi[i] - ye[e])**2 + (xi[i] - xe[e])**2
                        ppe_sum += a * (mi[i] - ppe_ref_mag_value) * (1.0/np.pi) / (d**2 + r_sq) + s

                WPPE[e] = (B / te[e]) * np.exp(-B * (me[e] - ppe_ref_mag_value)) * ppe_sum

                # Calculate foreshock weight
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

    # Calculate average weight
    EW = np.mean(W)

    return W, EW, CatE
