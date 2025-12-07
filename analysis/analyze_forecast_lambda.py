#!/usr/bin/env python3
"""
Analyze Lambda sum of PPE and EEPAS Forecast results

Based on previous discussions, the forecast matrix format:
- Shape: (n_windows × n_mag_bins, n_cells + 1)
- Each element represents the predicted seismicity rate for that spatio-temporal-magnitude bin
- Need to sum all elements to obtain the total predicted earthquake count
"""

import scipy.io as sio
import numpy as np
import json

def analyze_forecast_results(results_dir, config_file):
    """
    Analyze PPE and EEPAS forecast Lambda sum for validation.

    This function validates forecast results by checking if the integrated rate
    density (Lambda sum) is consistent with the observed event count. For a
    properly calibrated forecast, the Lambda sum should be close to the number
    of observed events in the forecast period.

    Args:
        results_dir: Path to results directory containing forecast .mat files
        config_file: Path to configuration JSON file

    Returns:
        dict: Dictionary containing 'ppe_lambda_sum' and 'eepas_lambda_sum'

    Notes:

        - Forecast matrix format: (n_windows × n_mag_bins, n_cells + 1)
        - First column contains time_s index and should be excluded from Lambda sum
        - Lambda sum = Σ forecast[:, 1:]  (exclude index column)
        - Expected: Lambda sum ≈ observed event count (within ±20%)
    """
    print(f"\n{'='*70}")
    print(f"Analyzing Forecast results: {results_dir}")
    print(f"{'='*70}")

    # Load configuration
    with open(config_file, 'r') as f:
        config = json.load(f)

    learn_start = config['learnStartYear']
    learn_end = config['learnEndYear']
    forecast_start = config['forecastStartYear']
    forecast_end = config['forecastEndYear']

    print(f"\nConfiguration:")
    print(f"  Learning period: {learn_start} - {learn_end}")
    print(f"  Forecast period: {forecast_start} - {forecast_end}")

    # Load PPE Forecast
    try:
        ppe_file = f"{results_dir}/PREVISIONI_3m_PPE_{forecast_start}_{forecast_end}.mat"
        mat_ppe = sio.loadmat(ppe_file)
        ppe_forecast = mat_ppe['PREVISIONI_3m']

        print(f"\n[PPE Forecast]")
        print(f"  File: {ppe_file}")
        print(f"  Matrix shape: {ppe_forecast.shape}")
        print(f"  Matrix element sum: {np.sum(ppe_forecast):.6f}")

        # Analyze matrix structure
        n_rows, n_cols = ppe_forecast.shape
        print(f"\n  Matrix structure analysis:")
        print(f"    Rows (time windows × magnitude bins): {n_rows}")
        print(f"    Columns (grid cells + 1): {n_cols}")

        # Calculate column sums
        col_sums = np.sum(ppe_forecast, axis=0)
        print(f"    First column sum (time_s index): {col_sums[0]:.6f}")
        print(f"    Remaining {n_cols-1} columns sum (actual grid data): {np.sum(col_sums[1:]):.6f}")

        # Lambda sum: exclude first column (time_s index)
        ppe_lambda_sum = np.sum(ppe_forecast[:, 1:])

    except Exception as e:
        print(f"\nError: Cannot read PPE Forecast - {e}")
        ppe_lambda_sum = None

    # Load EEPAS Forecast
    try:
        eepas_file = f"{results_dir}/PREVISIONI_3m_EEPAS_{forecast_start}_{forecast_end}.mat"
        mat_eepas = sio.loadmat(eepas_file)
        eepas_forecast = mat_eepas['PREVISIONI_3m_less']

        print(f"\n[EEPAS Forecast]")
        print(f"  File: {eepas_file}")
        print(f"  Matrix shape: {eepas_forecast.shape}")
        print(f"  Matrix element sum: {np.sum(eepas_forecast):.6f}")

        # Analyze matrix structure
        n_rows, n_cols = eepas_forecast.shape
        print(f"\n  Matrix structure analysis:")
        print(f"    Rows (time windows × magnitude bins): {n_rows}")
        print(f"    Columns (grid cells + 1): {n_cols}")

        # Calculate column sums
        col_sums = np.sum(eepas_forecast, axis=0)
        print(f"    First column sum (time_s index): {col_sums[0]:.6f}")
        print(f"    Remaining {n_cols-1} columns sum (actual grid data): {np.sum(col_sums[1:]):.6f}")

        # Lambda sum: exclude first column (time_s index)
        eepas_lambda_sum = np.sum(eepas_forecast[:, 1:])

    except Exception as e:
        print(f"\nError: Cannot read EEPAS Forecast - {e}")
        eepas_lambda_sum = None

    # Summary
    print(f"\n{'='*70}")
    print(f"Lambda Sum Summary")
    print(f"{'='*70}")

    if ppe_lambda_sum is not None:
        print(f"\nPPE Lambda sum:   {ppe_lambda_sum:.6f}")

    if eepas_lambda_sum is not None:
        print(f"EEPAS Lambda sum: {eepas_lambda_sum:.6f}")

    if ppe_lambda_sum is not None and eepas_lambda_sum is not None:
        diff = abs(eepas_lambda_sum - ppe_lambda_sum)
        rel_diff = diff / ppe_lambda_sum * 100
        print(f"\nDifference: {diff:.6f} ({rel_diff:.4f}%)")

        # Check if close to target event count
        # Note: This sum represents the entire forecast period
        # If the forecast period is T years and predicts N events per year, the sum should be close to N*T
        # Or if forecasting the learning period, should be close to the learning period event count

        print(f"\n⚠️  Note: These values represent the sum of the entire forecast matrix")
        print(f"   To verify if close to actual event count, need to:")
        print(f"   1. Confirm forecast period and target event count")
        print(f"   2. Consider spatio-temporal-magnitude resolution of the matrix")
        print(f"   3. May need to sum over specific time windows or magnitude ranges")

    return {
        'ppe_lambda_sum': ppe_lambda_sum,
        'eepas_lambda_sum': eepas_lambda_sum
    }

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("PPE and EEPAS Forecast Lambda Sum Analysis")
    print("="*70)

    # Default: analyze causal EW results
    print("\n\n" + "="*70)
    print("[useCausalEW=0 Results]")
    print("="*70)
    results_ew0 = analyze_forecast_results(
        "results_italy_causal_ew0",
        "config_italy_causal_ew0.json"
    )

    print("\n\n" + "="*70)
    print("[useCausalEW=1 Results]")
    print("="*70)
    results_ew1 = analyze_forecast_results(
        "results_italy_causal_ew1",
        "config_italy_causal_ew1.json"
    )

    # Compare two modes
    if results_ew0['ppe_lambda_sum'] and results_ew1['ppe_lambda_sum']:
        print("\n\n" + "="*70)
        print("[useCausalEW=0 vs useCausalEW=1]")
        print("="*70)

        print(f"\nPPE Lambda sum:")
        print(f"  useCausalEW=0: {results_ew0['ppe_lambda_sum']:.6f}")
        print(f"  useCausalEW=1: {results_ew1['ppe_lambda_sum']:.6f}")
        diff = abs(results_ew0['ppe_lambda_sum'] - results_ew1['ppe_lambda_sum'])
        rel_diff = diff / results_ew0['ppe_lambda_sum'] * 100
        print(f"  Absolute difference: {diff:.6f}")
        print(f"  Relative difference: {rel_diff:.4f}%")

        print(f"\nEEPAS Lambda sum:")
        print(f"  useCausalEW=0: {results_ew0['eepas_lambda_sum']:.6f}")
        print(f"  useCausalEW=1: {results_ew1['eepas_lambda_sum']:.6f}")
        diff = abs(results_ew0['eepas_lambda_sum'] - results_ew1['eepas_lambda_sum'])
        rel_diff = diff / results_ew0['eepas_lambda_sum'] * 100
        print(f"  Absolute difference: {diff:.6f}")
        print(f"  Relative difference: {rel_diff:.4f}%")

        # Explain forecast period
        print("\n\n" + "="*70)
        print("[Forecast Results Explanation]")
        print("="*70)
        print(f"\nNote: Learning period is 1990-2012 (22 years), forecast period is 2012-2022 (10 years)")
        print(f"      Lambda sum represents expected earthquake count for forecast period (2012-2022)")

        print(f"\nPPE Lambda sum:")
        print(f"  useCausalEW=0: {results_ew0['ppe_lambda_sum']:.2f}")
        print(f"  useCausalEW=1: {results_ew1['ppe_lambda_sum']:.2f}")

        print(f"\nEEPAS Lambda sum:")
        print(f"  useCausalEW=0: {results_ew0['eepas_lambda_sum']:.2f}")
        print(f"  useCausalEW=1: {results_ew1['eepas_lambda_sum']:.2f}")
