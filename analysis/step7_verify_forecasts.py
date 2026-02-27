#!/usr/bin/env python3
"""
EEPAS Workflow Step 7: Forecast Verification
=============================================

Performs PyCSEP statistical verification for EEPAS experiments.
Verifies experiments specified by config files against observed earthquakes.

This is Step 7 in the standard EEPAS workflow:
  Steps 1-5: EEPAS learning and forecasting
  Step 6:    Archive results
  Step 7:    Verify forecasts (this script)
  Step 8:    Assess probability risk

Usage:
    python step7_verify_forecasts.py [--catalog CATALOG_FILE] [--mag-buffer MAG_BUFFER] config1.json config2.json ...

    --catalog: Observation catalog file (default: HORUS_Italy_RDN2008_polygon_filtered.mat)
    --mag-buffer: Magnitude buffer below mT for filtering (default: 0.05)

Each experiment's results are saved to its own results directory.

Key Improvements:
- Reads forecast time range from config (forecastStartYear, forecastEndYear)
- Reads target magnitude (mT) from config
- Automatically determines num_regions from grid file
- No hard-coded constants
"""

import sys
import os
import json
import argparse
import numpy as np
import pandas as pd
import scipy.io
import scipy.stats
from datetime import datetime, timezone

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import csep
from csep.utils import time_utils
from csep.core import poisson_evaluations as poisson
from csep.core import binomial_evaluations as binomial
from csep.utils.stats import get_Kagan_I1_score
from csep.core.binomial_evaluations import binary_joint_log_likelihood_ndarray as jolib
from csep.core.poisson_evaluations import poisson_joint_log_likelihood_ndarray as jolip

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from forecast_converter import EEPASForecastConverter

print("=" * 80)
print("EEPAS Workflow Step 7: Forecast Verification")
print("=" * 80)

# ============================================================================
# Parse Arguments
# ============================================================================

parser = argparse.ArgumentParser(description='Verify EEPAS experiments')
parser.add_argument('--catalog', type=str, default='HORUS_Italy_RDN2008_polygon_filtered.mat',
                    help='Observation catalog file (default: HORUS_Italy_RDN2008_polygon_filtered.mat)')
parser.add_argument('--mag-buffer', type=float, default=0.05,
                    help='Magnitude buffer below mT for filtering (default: 0.05)')
parser.add_argument('--source-crs', type=str, default='EPSG:7794',
                    help='Source CRS for coordinate transform (default: EPSG:7794 for Italy RDN2008, use EPSG:3826 for Taiwan TWD97)')
parser.add_argument('configs', nargs='*', help='Configuration files')

args = parser.parse_args()

# Get catalog file and magnitude buffer
CATALOG_FILE = args.catalog
MAG_BUFFER = args.mag_buffer

# Get config files
if len(args.configs) == 0:
    print("\nUsage: python step7_verify_forecasts.py [--catalog CATALOG] [--mag-buffer MAG_BUFFER] config1.json config2.json ...")
    print("\nError: At least one config file must be specified.")
    sys.exit(1)
else:
    config_files = args.configs

print(f"\n📋 Config files to process: {len(config_files)}")
for cf in config_files:
    print(f"   - {cf}")
print(f"📊 Magnitude buffer: {MAG_BUFFER} (events filtered at mT - {MAG_BUFFER})")

# ============================================================================
# Helper Functions
# ============================================================================

def _brier_score_ndarray(forecast, observations):
    """Calculate Brier score"""
    prob_success = 1 - scipy.stats.poisson.cdf(0, forecast)
    brier_cell = np.square(prob_success.ravel() - (observations.ravel() > 0))
    brier = -2 * brier_cell.sum()
    for n_dim in observations.shape:
        brier /= n_dim
    return brier

def pass_fail(quantile, test_type='one-sided-lower'):
    """Determine if test passes"""
    if test_type == 'one-sided-lower':
        return 'Pass' if quantile >= 0.025 else 'Fail'
    elif test_type == 'N-test':
        q1, q2 = quantile
        return 'Pass' if 0.025 <= q1 <= 0.975 and 0.025 <= q2 <= 0.975 else 'Fail'
    return 'Unknown'

def load_horus_catalog(filename, **kwargs):
    """Load HORUS-format catalog in PyCSEP format"""
    mat_data = scipy.io.loadmat(filename)
    horus_data = mat_data['HORUS']
    eventlist = []
    for i, event in enumerate(horus_data):
        try:
            year, month, day = int(event[0]), int(event[1]), int(event[2])
            hour, minute = int(event[3]), int(event[4])
            second_float = float(event[5])
            second = int(second_float)
            microsecond = int((second_float - second) * 1000000)
            latitude, longitude = float(event[6]), float(event[7])
            depth, magnitude = float(event[8]), round(float(event[9]), 1)
            dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
            origin_time = time_utils.datetime_to_utc_epoch(dt)
            event_id = f'HORUS-{i+1:06d}'
            eventlist.append((event_id, origin_time, latitude, longitude, depth, magnitude))
        except:
            continue
    if kwargs.get('return_catalog_id', False):
        return eventlist, 'EEPAS_Catalog'
    return eventlist

# ============================================================================
# Load Common Parameters from First Config
# ============================================================================

print("\n" + "=" * 80)
print("Loading Common Parameters from Config")
print("=" * 80)

# Load first config to get common parameters
with open(config_files[0], 'r') as f:
    first_config = json.load(f)

# Extract time range from config
forecast_start_year = first_config['forecastStartYear']
forecast_end_year = first_config['forecastEndYear']

# Extract target magnitude
mT = first_config['modelParams']['mT']
mag_filter_threshold = mT - MAG_BUFFER

# IMPORTANT: forecastEndYear means forecast up to (forecastEndYear - 1) Dec 31
# Example: forecastEndYear=2026 means forecast period ends on 2025-12-31
start_date_str = f'{forecast_start_year}-01-01 00:00:00.0'
end_date_str = f'{forecast_end_year - 1}-12-31 23:59:59.999'

start_date = time_utils.strptime_to_utc_datetime(start_date_str)
end_date = time_utils.strptime_to_utc_datetime(end_date_str)

print(f"📅 Forecast period: {forecast_start_year}-01-01 to {forecast_end_year - 1}-12-31")
print(f"🎯 Target magnitude (mT): {mT}")
print(f"📊 Magnitude filter: M ≥ {mag_filter_threshold:.2f} (mT - {MAG_BUFFER})")

# ============================================================================
# NOTE: Catalog will be loaded per-config inside the loop
# to ensure each experiment uses its own time range
# ============================================================================

catalog_path = f'../data/{CATALOG_FILE}'
print(f"📂 Observation catalog: {CATALOG_FILE}")

# ============================================================================
# Process Each Config/Experiment
# ============================================================================

all_results = {}

for config_file in config_files:
    print(f"\n{'=' * 80}")
    print(f"Processing config: {config_file}")
    print('=' * 80)

    # Load config
    if not os.path.exists(config_file):
        print(f"⚠️  Config file not found: {config_file}, skipping...")
        continue

    with open(config_file, 'r') as f:
        config = json.load(f)

    results_dir = config['resultsDir']
    exp_name = os.path.basename(results_dir)

    print(f"📂 Results directory: {results_dir}")

    # Get parameters from config
    config_forecast_start = config['forecastStartYear']
    config_forecast_end = config['forecastEndYear']
    config_mT = config['modelParams']['mT']
    config_mag_filter = config_mT - MAG_BUFFER

    print(f"📅 Config forecast: {config_forecast_start}-01-01 to {config_forecast_end - 1}-12-31")

    # Load catalog for THIS config's time range
    print(f"\n⏳ Loading observation catalog for {config_forecast_start}-{config_forecast_end - 1}...")
    catalog = csep.load_catalog(catalog_path, loader=load_horus_catalog)

    # Filter by magnitude (using this config's mT)
    catalog = catalog.filter(f'magnitude >= {config_mag_filter}')

    # Filter by depth
    catalog = catalog.filter('depth <= 40')

    # Filter by THIS config's time range
    config_start_date_str = f'{config_forecast_start}-01-01 00:00:00.0'
    config_end_date_str = f'{config_forecast_end - 1}-12-31 23:59:59.999'
    config_start_date = time_utils.strptime_to_utc_datetime(config_start_date_str)
    config_end_date = time_utils.strptime_to_utc_datetime(config_end_date_str)
    config_start_epoch = time_utils.datetime_to_utc_epoch(config_start_date)
    config_end_epoch = time_utils.datetime_to_utc_epoch(config_end_date)
    catalog = catalog.filter([f'origin_time >= {config_start_epoch}', f'origin_time < {config_end_epoch}'])

    print(f"✅ Loaded {catalog.event_count} events")
    print(f"   Magnitude: M ≥ {config_mag_filter:.2f}")
    print(f"   Depth: ≤ 40 km")
    print(f"   Time: {config_forecast_start}-01-01 to {config_forecast_end - 1}-12-31")

    # Check files exist
    eepas_file = f'../{results_dir}/PREVISIONI_3m_EEPAS_{config_forecast_start}_{config_forecast_end}.mat'
    ppe_file = f'../{results_dir}/PREVISIONI_3m_PPE_{config_forecast_start}_{config_forecast_end}.mat'
    grid_file = f"../data/{config['inputFiles']['testingRegionFile']}"

    if not os.path.exists(f'../{results_dir}'):
        print(f"⚠️  Results directory not found, skipping...")
        continue
    if not os.path.exists(eepas_file):
        print(f"⚠️  EEPAS forecast not found, skipping...")
        continue
    if not os.path.exists(ppe_file):
        print(f"⚠️  PPE forecast not found, skipping...")
        continue

    # Auto-detect num_regions from grid file
    print(f"\n⏳ Reading grid file to determine num_regions...")
    grid_data = scipy.io.loadmat(grid_file)
    # Try common variable names
    if 'CELLESD' in grid_data:
        grid_array = grid_data['CELLESD']
    elif 'CELLE' in grid_data:
        grid_array = grid_data['CELLE']
    elif 'CELLE_ter_TW' in grid_data:
        grid_array = grid_data['CELLE_ter_TW']
    else:
        # Find the first numeric array with appropriate dimensions
        for key in grid_data.keys():
            if not key.startswith('__') and isinstance(grid_data[key], np.ndarray):
                if grid_data[key].ndim == 2 and grid_data[key].shape[1] >= 4:
                    grid_array = grid_data[key]
                    break
        else:
            print(f"⚠️  Could not find grid data in {grid_file}, skipping...")
            continue

    num_regions = grid_array.shape[0]
    print(f"   ✅ Detected {num_regions} regions from grid file")

    # Magnitude binning parameters
    # Note: These are typically fixed in EEPAS forecast generation
    # mT is the minimum target magnitude, bins typically cover mT to mT+2.4 in 0.1 steps
    num_magnitude_steps = 25  # Standard: 25 bins covering 2.5 magnitude units
    magnitude_min = config_mT
    magnitude_step = 0.1  # Standard bin width

    # Load EEPAS forecast
    print(f"\n⏳ Loading EEPAS forecast...")
    eepas_conv = EEPASForecastConverter(
        forecast_file=eepas_file,
        grid_file=grid_file,
        num_regions=num_regions,
        num_magnitude_steps=num_magnitude_steps,
        magnitude_min=magnitude_min,
        magnitude_step=magnitude_step,
        coordinate_transform=True,
        source_crs=args.source_crs, target_crs='EPSG:4326',
        verbose=False
    )

    eepas_data = eepas_conv.convert_all_periods(
        output_file=f'temp_{exp_name}_eepas.dat',
        perform_downsampling=True, grid_resolution=0.1
    )

    eepas_forecast = eepas_conv.to_pycsep_forecast(
        data=eepas_data, start_date=start_date, end_date=end_date,
        name=f'EEPAS_{exp_name}'
    )

    # Load PPE forecast
    print(f"⏳ Loading PPE forecast...")
    ppe_conv = EEPASForecastConverter(
        forecast_file=ppe_file,
        grid_file=grid_file,
        num_regions=num_regions,
        num_magnitude_steps=num_magnitude_steps,
        magnitude_min=magnitude_min,
        magnitude_step=magnitude_step,
        coordinate_transform=True,
        source_crs=args.source_crs, target_crs='EPSG:4326',
        verbose=False
    )

    ppe_data = ppe_conv.convert_all_periods(
        output_file=f'temp_{exp_name}_ppe.dat',
        perform_downsampling=True, grid_resolution=0.1
    )

    ppe_forecast = ppe_conv.to_pycsep_forecast(
        data=ppe_data, start_date=start_date, end_date=end_date,
        name=f'PPE_{exp_name}'
    )

    # Filter catalog
    cat = catalog.filter_spatial(eepas_forecast.region)

    print(f"\n📊 Forecast Summary:")
    print(f"   EEPAS expected: {eepas_forecast.event_count:.2f}")
    print(f"   PPE expected:   {ppe_forecast.event_count:.2f}")
    print(f"   Observed:       {cat.event_count}")

    # Run tests
    seed = 123456
    nsim = 10000

    print(f"\n⏳ Running PyCSEP tests (nsim={nsim})...")

    # EEPAS tests
    eepas_poisson = {
        'L': poisson.likelihood_test(eepas_forecast, cat, seed=seed, num_simulations=nsim),
        'CL': poisson.conditional_likelihood_test(eepas_forecast, cat, seed=seed, num_simulations=nsim),
        'N': poisson.number_test(eepas_forecast, cat),
        'S': poisson.spatial_test(eepas_forecast, cat, seed=seed, num_simulations=nsim),
        'M': poisson.magnitude_test(eepas_forecast, cat, seed=seed, num_simulations=nsim)
    }

    eepas_binomial = {
        'CL': binomial.binary_conditional_likelihood_test(eepas_forecast, cat, seed=seed, num_simulations=nsim),
        'S': binomial.binary_spatial_test(eepas_forecast, cat, seed=seed, num_simulations=nsim)
    }

    # PPE tests
    ppe_poisson = {
        'L': poisson.likelihood_test(ppe_forecast, cat, seed=seed, num_simulations=nsim),
        'CL': poisson.conditional_likelihood_test(ppe_forecast, cat, seed=seed, num_simulations=nsim),
        'N': poisson.number_test(ppe_forecast, cat),
        'S': poisson.spatial_test(ppe_forecast, cat, seed=seed, num_simulations=nsim),
        'M': poisson.magnitude_test(ppe_forecast, cat, seed=seed, num_simulations=nsim)
    }

    ppe_binomial = {
        'CL': binomial.binary_conditional_likelihood_test(ppe_forecast, cat, seed=seed, num_simulations=nsim),
        'S': binomial.binary_spatial_test(ppe_forecast, cat, seed=seed, num_simulations=nsim)
    }

    # Calculate comparison metrics
    print(f"⏳ Calculating comparison metrics...")

    target_idx_eepas = np.nonzero(cat.spatial_counts().ravel())
    target_rates_eepas = np.log(eepas_forecast.spatial_counts().ravel()[target_idx_eepas])
    eepas_llp = jolip(target_rates_eepas, cat.event_count, eepas_forecast.event_count)

    target_idx_ppe = np.nonzero(cat.spatial_counts().ravel())
    target_rates_ppe = np.log(ppe_forecast.spatial_counts().ravel()[target_idx_ppe])
    ppe_llp = jolip(target_rates_ppe, cat.event_count, ppe_forecast.event_count)

    eepas_llb = jolib(eepas_forecast.spatial_counts(), cat.spatial_counts())
    ppe_llb = jolib(ppe_forecast.spatial_counts(), cat.spatial_counts())

    eepas_kagan = get_Kagan_I1_score(eepas_forecast, cat)
    ppe_kagan = get_Kagan_I1_score(ppe_forecast, cat)

    eepas_brier = _brier_score_ndarray(eepas_forecast.spatial_counts(), cat.spatial_counts())
    ppe_brier = _brier_score_ndarray(ppe_forecast.spatial_counts(), cat.spatial_counts())

    # Store results
    all_results[exp_name] = {
        'config_file': config_file,
        'results_dir': results_dir,
        'catalog': cat,
        'eepas_forecast': eepas_forecast,
        'ppe_forecast': ppe_forecast,
        'eepas_poisson': eepas_poisson,
        'ppe_poisson': ppe_poisson,
        'eepas_binomial': eepas_binomial,
        'ppe_binomial': ppe_binomial,
        'eepas_llp': eepas_llp,
        'ppe_llp': ppe_llp,
        'eepas_llb': eepas_llb,
        'ppe_llb': ppe_llb,
        'eepas_kagan': eepas_kagan,
        'ppe_kagan': ppe_kagan,
        'eepas_brier': eepas_brier,
        'ppe_brier': ppe_brier
    }

    # ========================================================================
    # Save results to this experiment's directory
    # ========================================================================

    output_dir = f'../{results_dir}'

    # Print results
    print(f"\n{'=' * 60}")
    print(f"RESULTS FOR: {exp_name}")
    print('=' * 60)

    # EEPAS Poisson
    print(f"\n--- EEPAS Poisson Tests ---")
    test_data = []
    for test_name, test_result in eepas_poisson.items():
        if test_name == 'N':
            q = test_result.quantile
            status = pass_fail(q, 'N-test')
            print(f"{test_name}-test: δ₁={q[0]:.4f}, δ₂={q[1]:.4f} [{status}]")
        else:
            q = test_result.quantile
            status = pass_fail(q)
            print(f"{test_name}-test: δ={q:.4f} [{status}]")
        test_data.append(['EEPAS', 'Poisson', test_name, status])

    # EEPAS Binomial
    print(f"\n--- EEPAS Binomial Tests ---")
    for test_name, test_result in eepas_binomial.items():
        q = test_result.quantile
        status = pass_fail(q)
        print(f"{test_name}-test: δ={q:.4f} [{status}]")
        test_data.append(['EEPAS', 'Binomial', test_name, status])

    # PPE Poisson
    print(f"\n--- PPE Poisson Tests ---")
    for test_name, test_result in ppe_poisson.items():
        if test_name == 'N':
            q = test_result.quantile
            status = pass_fail(q, 'N-test')
            print(f"{test_name}-test: δ₁={q[0]:.4f}, δ₂={q[1]:.4f} [{status}]")
        else:
            q = test_result.quantile
            status = pass_fail(q)
            print(f"{test_name}-test: δ={q:.4f} [{status}]")
        test_data.append(['PPE', 'Poisson', test_name, status])

    # PPE Binomial
    print(f"\n--- PPE Binomial Tests ---")
    for test_name, test_result in ppe_binomial.items():
        q = test_result.quantile
        status = pass_fail(q)
        print(f"{test_name}-test: δ={q:.4f} [{status}]")
        test_data.append(['PPE', 'Binomial', test_name, status])

    # Comparison metrics
    print(f"\n--- Comparison Metrics ---")
    print(f"{'Metric':<30} {'EEPAS':>12} {'PPE':>12} {'Winner':>10}")
    print("-" * 65)
    print(f"{'Poisson log-likelihood':<30} {eepas_llp:>12.6f} {ppe_llp:>12.6f} {'EEPAS' if eepas_llp > ppe_llp else 'PPE':>10}")
    print(f"{'Binary log-likelihood':<30} {eepas_llb:>12.6f} {ppe_llb:>12.6f} {'EEPAS' if eepas_llb > ppe_llb else 'PPE':>10}")
    print(f"{'Kagan I₁ score':<30} {eepas_kagan[0]:>12.6f} {ppe_kagan[0]:>12.6f} {'EEPAS' if eepas_kagan[0] > ppe_kagan[0] else 'PPE':>10}")
    print(f"{'Brier score':<30} {eepas_brier:>12.6f} {ppe_brier:>12.6f} {'EEPAS' if eepas_brier > ppe_brier else 'PPE':>10}")

    # Save CSV
    df = pd.DataFrame(test_data, columns=['Model', 'Test_Type', 'Test', 'Status'])
    csv_file = f'{output_dir}/PYCSEP_TEST_RESULTS.csv'
    df.to_csv(csv_file, index=False)
    print(f"\n✅ Saved: {csv_file}")

    # Save detailed report
    report_file = f'{output_dir}/VERIFICATION_REPORT.md'
    with open(report_file, 'w') as f:
        f.write(f"# Verification Report: {exp_name}\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Config**: `{config_file}`\n\n")
        f.write(f"**Results Directory**: `{results_dir}`\n\n")

        f.write(f"## Configuration Summary\n\n")
        f.write(f"- **Forecast Period**: {config_forecast_start}-01-01 to {config_forecast_end - 1}-12-31\n")
        f.write(f"- **Target Magnitude (mT)**: {config_mT}\n")
        f.write(f"- **Magnitude Filter**: M ≥ {mag_filter_threshold:.2f} (mT - {MAG_BUFFER})\n")
        f.write(f"- **Number of Regions**: {num_regions}\n")
        f.write(f"- **Magnitude Bins**: {num_magnitude_steps} bins ({magnitude_min:.1f} to {magnitude_min + (num_magnitude_steps - 1) * magnitude_step:.1f}, step {magnitude_step})\n\n")

        f.write(f"## Forecast Summary\n\n")
        f.write(f"- Observed events: {cat.event_count}\n")
        f.write(f"- EEPAS expected: {eepas_forecast.event_count:.2f}\n")
        f.write(f"- PPE expected: {ppe_forecast.event_count:.2f}\n\n")

        f.write(f"## Comparison Metrics\n\n")
        f.write(f"| Metric | EEPAS | PPE | Winner |\n")
        f.write(f"|--------|-------|-----|--------|\n")
        f.write(f"| Poisson LL | {eepas_llp:.2f} | {ppe_llp:.2f} | {'EEPAS' if eepas_llp > ppe_llp else 'PPE'} |\n")
        f.write(f"| Binary LL | {eepas_llb:.2f} | {ppe_llb:.2f} | {'EEPAS' if eepas_llb > ppe_llb else 'PPE'} |\n")
        f.write(f"| Kagan I₁ | {eepas_kagan[0]:.4f} | {ppe_kagan[0]:.4f} | {'EEPAS' if eepas_kagan[0] > ppe_kagan[0] else 'PPE'} |\n")
        f.write(f"| Brier | {eepas_brier:.4f} | {ppe_brier:.4f} | {'EEPAS' if eepas_brier > ppe_brier else 'PPE'} |\n\n")

        f.write(f"## Test Results\n\n")
        for model in ['EEPAS', 'PPE']:
            model_data = df[df['Model'] == model]
            poisson_data = model_data[model_data['Test_Type'] == 'Poisson']
            binomial_data = model_data[model_data['Test_Type'] == 'Binomial']
            poisson_pass = (poisson_data['Status'] == 'Pass').sum()
            binomial_pass = (binomial_data['Status'] == 'Pass').sum()
            total_pass = poisson_pass + binomial_pass
            f.write(f"### {model}\n\n")
            f.write(f"- Poisson: {poisson_pass}/5\n")
            f.write(f"- Binomial: {binomial_pass}/2\n")
            f.write(f"- **Total: {total_pass}/7 ({100*total_pass/7:.1f}%)**\n\n")

    print(f"✅ Saved: {report_file}")

print("\n" + "=" * 80)
print("✅ All Verifications Complete!")
print("=" * 80)
print(f"\nProcessed {len(all_results)} experiment(s)")
for exp_name, res in all_results.items():
    print(f"\n{exp_name}:")
    print(f"  - {res['results_dir']}/PYCSEP_TEST_RESULTS.csv")
    print(f"  - {res['results_dir']}/VERIFICATION_REPORT.md")

# Clean up temp files
import glob
for f in glob.glob('temp_*.dat'):
    try:
        os.remove(f)
    except:
        pass
