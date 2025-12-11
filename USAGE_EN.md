# EEPAS - Usage Guide

**Version:** 0.4.0
**For complete documentation, see:** `docs/build/html/index.html`

## Quick Links

- [Installation](#installation)
- [Basic Workflow](#basic-workflow)
- [Configuration](#configuration)
- [Advanced Options](#advanced-options)
- [Result Archiving](#result-archiving)

---

## Installation

### Prerequisites
- Python 3.8+
- 8GB+ RAM (16GB recommended for Italy mode)

### Install Dependencies

```bash
cd EEPAS/src/python_src
pip install -r requirements.txt
```

### Verify Installation

```bash
python3 -c "import numpy, scipy, numba, pandas, h5py; print('✅ All dependencies installed')"
```

---

## Basic Workflow

### 5-Step EEPAS Workflow

**Configuration Files:**
- **`config_italy_target_m0.json`** - End-to-end automated pipeline (recommended)
- **`config_italy_causal_ew0_rerun.json`** - Reproduce published results

```bash
# Set configuration file
CONFIG=config_italy_target_m0.json

# Step 1: PPE Learning
python3 ppe_learning.py --config $CONFIG

# Step 2: Aftershock Parameters
python3 fit_aftershock_params.py \
    --config $CONFIG \
    --ppe-ref-mag mT \
    --target-mag mT

# Step 3: EEPAS Learning (three-stage optimization)
python3 eepas_learning_auto_boundary.py \
    --config $CONFIG \
    --three-stage \
    --ppe-ref-mag mT \
    --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py \
    --config $CONFIG \
    --ppe-ref-mag mT

# Step 5: EEPAS Forecast
python3 eepas_make_forecast.py \
    --config $CONFIG \
    --ppe-ref-mag mT

# Step 6: Archive Results (optional)
python3 archive_results.py \
    --config $CONFIG \
    --results-dir results_italy_target_m0/ \
    --workflow "EEPAS 5-step workflow" \
    --logs *.log \
    --ppe-ref-mag mT \
    --target-mag mT
```

**Expected Runtime:** ~1 hour on 8-core laptop

---

## Configuration

### Basic Configuration Structure

```json
{
  "dataDir": "data",
  "resultsDir": "results_yourregion",
  "catalogStartYear": 1960,
  "learnStartYear": 1990,
  "learnEndYear": 2012,
  "forecastStartYear": 2012,
  "forecastEndYear": 2022,
  "inputFiles": {
    "catalogFile": "catalog.mat",
    "neighborhoodRegionFile": "neighborhood.mat",
    "testingRegionFile": "testing.mat"
  },
  "modelParams": {
    "m0": 2.95,
    "mT": 4.95,
    "B": 1.036
  },
  "optimization": {
    "stage1": { ... },
    "stage2": { ... },
    "stage3": { ... }
  }
}
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `m0` | Completeness magnitude | 2.95 |
| `mT` | Target magnitude threshold | 4.95 |
| `B` | b-value × ln(10) | 1.036 |

**Complete configuration guide:** `docs/source/user_guide/configuration.rst`

---

## Advanced Options

### EEPAS Learning Options

```bash
# Three-stage optimization (recommended)
python3 eepas_learning_auto_boundary.py \
    --config $CONFIG \
    --three-stage \
    --ppe-ref-mag mT \
    --max-rounds 1

# Single-stage with custom boundary rounds
python3 eepas_learning_auto_boundary.py \
    --config $CONFIG \
    --ppe-ref-mag mT \
    --max-rounds 5

# Disable multi-start search
python3 eepas_learning_auto_boundary.py \
    --config $CONFIG \
    --no-multistart
```

### Integration Mode Selection

**Fast Mode (Default):**
```bash
python3 ppe_learning.py --config $CONFIG
python3 eepas_make_forecast.py --config $CONFIG --fast
```
- Uses trapezoidal rule integration
- 1.75x faster overall
- < 0.2% parameter difference

**Accurate Mode (Final Verification):**
```bash
python3 ppe_learning.py --config $CONFIG --accurate
python3 eepas_make_forecast.py --config $CONFIG --accurate
```
- Uses scipy.dblquad integration
- Highest precision
- Recommended for final paper validation

### Magnitude Reference Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `--ppe-ref-mag mT` | Anchor to target magnitude | Paper validation (recommended) |
| `--ppe-ref-mag m0` | Anchor to completeness magnitude | Legacy mode |

---

## Result Archiving

Archive workflow results for reproducibility:

```bash
python3 archive_results.py \
    --config config_italy_target_m0.json \
    --results-dir results_italy_target_m0/ \
    --workflow "EEPAS 5-step workflow" \
    --logs step1_ppe.log step2_aftershock.log step3_eepas.log \
    --ppe-ref-mag mT \
    --target-mag mT
```

**Archived Files:**
- `config_used.json` - Configuration snapshot
- `execution_info.txt` - Execution metadata
- `execution.log` - Combined logs
- `README_REPRODUCE.md` - Reproduction guide

---

## Output Files

### Learning Phase

| File | Description |
|------|-------------|
| `Fitted_par_PPE_YYYY_YYYY.csv` | PPE parameters (a, d, s) |
| `Fitted_par_aftershock_YYYY_YYYY.csv` | Aftershock parameters (ν, κ) |
| `Fitted_par_EEPAS_YYYY_YYYY.csv` | EEPAS parameters (8 parameters) |

### Forecast Phase

| File | Description |
|------|-------------|
| `PREVISIONI_3m_PPE_YYYY_YYYY.mat` | PPE forecast rates |
| `PREVISIONI_3m_EEPAS_YYYY_YYYY.mat` | EEPAS forecast rates |

---

## Validation and Evaluation

### Lambda Sum Validation

```bash
python3 analysis/analyze_forecast_lambda.py
```

**Expected Results:**
- Learning: Λ_PPE ≈ N (target event count)
- Forecast: PPE + EEPAS ≈ observed events

### PyCSEP Evaluation

See interactive notebooks:
- `analysis/EEPAS_Forecast_Evaluation_New.ipynb` (Reproduce paper)
- `analysis/EEPAS_Forecast_Evaluation_End_to_End.ipynb` (Automated pipeline)

---

## Troubleshooting

### Common Issues

**1. Parameters hitting boundaries**
- Increase `--max-rounds` (default: 3, try 5)
- Check initial values in configuration

**2. Optimization not converging**
- Use `--three-stage` for complex parameter spaces
- Try `--no-multistart` for simpler problems

**3. Memory errors**
- Reduce catalog size or time period
- Use fast mode instead of accurate mode

**4. Integration warnings**
- Expected in some cases
- Results usually still valid if < 1% of integrations fail

### Getting Help

- **Full Documentation:** `docs/build/html/index.html`
- **API Reference:** `docs/source/api_reference/index.rst`
- **Workflow Guide:** `docs/source/user_guide/workflows.rst`
- **GitHub Issues:** https://github.com/phonchi/EEPAS/issues

---

## Adapting to Your Region

### Required Data Files

1. **Earthquake Catalog** (`.mat` format)
   - Columns: Year, Month, Day, Hour, Minute, Second, Lat, Lon, Depth, Magnitude

2. **Testing Region** (`.mat` format)
   - Grid cells: lon_min, lon_max, lat_min, lat_max

3. **Neighborhood Region** (`.mat` format)
   - Grid or polygon format
   - Must strictly contain testing region

### Workflow Steps

1. Prepare data files in `.mat` format
2. Create configuration file (copy `config_italy_target_m0.json`)
3. Estimate b-value using SeismoStats
4. Run 5-step workflow
5. Evaluate results with PyCSEP

**Complete guide:** `docs/source/user_guide/workflows.rst` (Section: "Applying to Your Region")

---

## Performance Tips

- **Fast Mode** recommended for daily research (1.75x speedup, <0.2% difference)
- **Accurate Mode** for final paper validation
- **Three-stage optimization** for Italy-sized regions (177 cells)
- **Single-stage** sufficient for smaller regions (< 50 cells)
- **JIT compilation** warmup: first run slower, subsequent runs faster

---

## Version History

See [CHANGELOG_EN.md](CHANGELOG_EN.md) for detailed version history.

**Current Version:** 0.4.0 (2025-12-11)

---

## Additional Resources

- **Mathematical Foundation:** `docs/source/technical/mathematical_foundation.rst`
- **Numerical Integration:** `docs/source/technical/numerical_integration.rst`
- **Optimization Details:** `docs/source/technical/optimization.rst`
- **Interactive Examples:** `docs/source/examples/index.rst`

---

**For complete, up-to-date documentation, always refer to:** `docs/build/html/index.html`
