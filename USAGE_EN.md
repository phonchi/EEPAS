# EEPAS - Detailed Usage Guide

## Table of Contents

1. [Installation and Environment](#installation-and-environment)
2. [Complete Workflow](#complete-workflow)
3. [Core Module Details](#core-module-details)
4. [Configuration File Guide](#configuration-file-guide)
5. [Automatic Boundary Adjustment](#automatic-boundary-adjustment)
6. [Interpreting Results](#interpreting-results)
7. [Paper Validation Workflow](#paper-validation-workflow)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## Installation and Environment

### System Requirements

- Python 3.8+
- 8GB+ RAM (16GB recommended)
- Linux/Mac/Windows (WSL)

### Install Dependencies

```bash
pip install numpy scipy numba pandas h5py
```

### Verify Installation

```bash
python3 -c "import numpy, scipy, numba, pandas, h5py; print('✅ All dependencies installed')"
```

---

## Complete Workflow

### Standard 5-Step Workflow

```bash
cd /path/to/EEPAS/src/python_src

# Step 1: PPE Learning
python3 ppe_learning.py --config config_italy_causal_ew0.json

# Step 2: Aftershock Learning
python3 fit_aftershock_params.py --config ../config.json

# Step 3: EEPAS Learning (Automatic Boundary Adjustment)
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py --config ../config.json

# Step 5: EEPAS Forecast
python3 eepas_make_forecast.py --config ../config.json
```

### Batch Processing Multiple Configurations

```bash
#!/bin/bash
for config in config.json config_include921.json config_m205.json config_decluster.json; do
    echo "Processing $config..."

    python3 ppe_learning.py --config ../$config
    python3 fit_aftershock_params.py --config ../$config
    python3 eepas_learning_auto_boundary.py --config ../$config
    python3 ppe_make_forecast.py --config ../$config
    python3 eepas_make_forecast.py --config ../$config

    echo "Completed $config"
done
```

---

## Core Module Details

### 1. PPE Learning (ppe_learning.py)

**Function**: Learn Proximity to Past Earthquakes background seismicity rate parameters

**Usage**:
```bash
python3 ppe_learning.py \
    --config ../config.json \
    --fit-mode joint \
    --grid-res 40
```

**Parameter Description**:
- `--config`: Configuration file path
- `--fit-mode`: Optimization mode
  - `joint`: Joint optimization of a, d, s (recommended)
  - `decoupled_gr`: Decoupled optimization, using Gutenberg-Richter relation to fix a
- `--grid-res`: Grid resolution (20-50, default 40)

**Output**:
- `results_*/Fitted_par_PPE_*.csv`
- Contains parameters: a (seismicity rate), d (spatial decay), s (magnitude decay), ln_likelihood

**Execution Time**: ~4 seconds (m0=2.35)

---

### 2. Aftershock Learning (fit_aftershock_params.py)

**Function**: Fit aftershock triggering parameters v, k

**Usage**:
```bash
python3 fit_aftershock_params.py --config ../config.json
```

**Dependencies**: Requires completed PPE learning

**Output**:
- `results_*/Fitted_par_aftershock_*.csv`
- Contains parameters: v (triggering intensity), k (PPE-to-aftershock ratio), ln_likelihood

**Execution Time**: ~3 seconds

---

### 3. EEPAS Learning - Basic Version (eepas_learning.py)

**Function**: Basic EEPAS parameter learning (without automatic boundary adjustment)

**Usage**:
```bash
python3 eepas_learning.py --config ../config.json --m0 2.35
```

**Parameters**:
- `--config`: Configuration file
- `--m0`: Completeness magnitude (optional, overrides config file)
- `--optimizer`: Optimizer selection (fminsearchcon, L-BFGS-B, TNC, SLSQP, Powell, default fminsearchcon)
- `--no-multistart`: Disable multistart (default enabled with 3 starting points)
- `--n-starts`: Number of multistart points (default 3)
- `--basinhopping`: Use Basin-Hopping global optimization
- `--basinhopping-niter`: Basin-Hopping iteration count (default 20)

**Three-Stage Optimization**:
1. Stage 1: Optimize am, at, Sa, u
2. Stage 2: Optimize Sm, bt, St, ba, u
3. Stage 3: Joint optimization of all 8 parameters

**Optimizer Selection Recommendations**:
- **Recommended**: `fminsearchcon` (most robust, finds high-quality solutions for all configurations)
- **Fast**: `L-BFGS-B` + `--n-starts 3` (fast but 50% chance of local optima)
- **Balanced**: Run both in parallel, select better result

**Examples**:
```bash
# Use default fminsearchcon
python3 eepas_learning.py --config ../config.json

# Use L-BFGS-B + multistart (3 starting points)
python3 eepas_learning.py --config ../config.json --optimizer L-BFGS-B --n-starts 3

# Use SLSQP single start
python3 eepas_learning.py --config ../config.json --optimizer SLSQP --no-multistart
```

**Output**:
- `results_*/Fitted_par_EEPAS_*.csv`
- Contains 9 columns: am, bm, Sm, at, bt, St, ba, Sa, u, ln_likelihood

**Execution Time**:
- fminsearchcon: ~230 seconds
- L-BFGS-B: ~30 seconds (single run)
- Multistart (3 runs): ~90 seconds

---

### 4. EEPAS Learning - Automatic Boundary Adjustment (eepas_learning_auto_boundary.py) ⭐Recommended

**Function**: Automatically detect and adjust boundaries until optimization converges

**Usage**:
```bash
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1
```

**Parameter Details**:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `--max-rounds` | 3 | 1-5 | Maximum boundary adjustment rounds |
| `--tolerance` | 0.01 | 0.001-0.1 | Boundary contact tolerance (relative ratio) |
| `--expansion` | 2.0 | 1.5-3.0 | Boundary expansion multiplier |
| `--nll-threshold` | 0.1 | 0.01-1.0 | NLL convergence threshold |

**Workflow**:
1. Execute EEPAS learning with current boundaries
2. Check if parameters touch boundaries
3. If touching, automatically expand boundaries and backup configuration
4. Repeat until:
   - NLL converges (consecutive improvement < threshold)
   - No parameters touch boundaries
   - Maximum rounds reached

**Stopping Conditions**:
- ✅ **NLL Convergence**: Most common, indicates optimal solution found
- ✅ **No Boundary Issues**: No contact in round 1
- ⚠️ **Maximum Rounds**: May need to check parameters

**Output**:
- Same as basic version, but generates configuration backup files:
  - `config.json.round1.bak`
  - `config.json.round2.bak`
  - ...

**Execution Time**: ~10-20 minutes (2-3 rounds)

---

### 5. PPE Forecast (ppe_make_forecast.py)

**Function**: Generate PPE background seismicity rate forecast

**Usage**:
```bash
python3 ppe_make_forecast.py --config ../config.json
```

**Dependencies**: Requires PPE learning results

**Output**:
- `results_*/PREVISIONI_3m_PPE_*.mat`
- MATLAB format, contains seismicity rates for each forecast window

**Execution Time**: ~3 minutes

---

### 6. EEPAS Forecast (eepas_make_forecast.py)

**Function**: Generate complete EEPAS model forecast

**Usage**:
```bash
python3 eepas_make_forecast.py --config ../config.json
```

**Dependencies**: Requires all PPE, aftershock, and EEPAS learning results

**Output**:
- `results_*/PREVISIONI_3m_EEPAS_*.mat`
- Mixed EEPAS and PPE forecast results

**Execution Time**: ~4 minutes

---

## Configuration File Guide

### Configuration Structure

```json
{
  "dataDir": "data",
  "resultsDir": "results",
  "catalogStartYear": 1991,
  "learnStartYear": 2002,
  "learnEndYear": 2016,
  "forecastStartYear": 2016,
  "forecastEndYear": 2024,

  "inputFiles": {
    "catalogFile": "...",            // Earthquake catalog file (HORUS format)
    "neighborhoodRegionFile": "...", // Neighborhood region file (CPTI15 polygon)
    "testingRegionFile": "..."       // Testing region file (CELLE grid)
  },

  "optimization": {
    "stage1": {...},
    "stage2": {...},
    "stage3": {...}
  },

  "modelParams": {
    "m0": 2.35,
    "mT": 5.0,
    "B": 0.942,
    ...
  }
}
```

### Key Parameters

#### Time Ranges
- `catalogStartYear`: Earthquake catalog start year
- `learnStartYear/learnEndYear`: Learning period
- `forecastStartYear/forecastEndYear`: Forecast period

#### Model Parameters
- `m0`: Completeness magnitude (affects data volume)
- `mT`: Triggering threshold magnitude
- `B`: Gutenberg-Richter relation parameter
- `delay`: Prospective delay days

#### Optimization Parameters (Stage 3 Example)
```json
"stage3": {
  "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
  "lowerBounds": [0.5, 0.05, -0.5, 0.05, 0.05, 0.05, 0.01, 0.0],
  "upperBounds": [4.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0, 0.75],
  "fixedValues": {"bm": 0.86}
}
```

### Boundary Setting Recommendations

**Normal Range** (recommended):
```json
"lowerBounds": [0.5, 0.05, -0.5, 0.05, 0.05, 0.05, 0.01, 0.0]
"upperBounds": [4.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0, 0.75]
```

**Relaxed Range** (rarely used with automatic boundary adjustment):
```json
"lowerBounds": [0.5, 0.001, -2.0, 0.001, 0.001, 0.001, 0.0001, 0.0]
"upperBounds": [4.0, 2.0, 3.0, 2.0, 2.0, 3.0, 2.0, 0.75]
```

---

## Automatic Boundary Adjustment

### Triggering Mechanism

The program checks if parameters are close to boundaries:

**Relative Tolerance** (regular parameters):
```python
distance_ratio = |param_value - bound| / (upper_bound - lower_bound)
if distance_ratio < tolerance:  # Default 0.01 (1%)
    trigger adjustment
```

**Absolute Tolerance** (small-value parameters, such as Sa, St):
```python
if lower_bound < 0.01:
    absolute_distance = |param_value - bound|
    if absolute_distance < max(bound * 0.1, 1e-6):
        trigger adjustment
```

### Adjustment Rules

**Lower Bound Relaxation**:
```python
new_lower = current_lower / expansion_factor

# Physical constraints
if parameter is positive-type (b, s):
    new_lower = max(new_lower, 1e-6)
elif parameter is u:
    new_lower = max(new_lower, 0.0)
# a parameter can be negative
```

**Upper Bound Relaxation**:
```python
new_upper = current_upper * expansion_factor

# Physical constraints
if parameter is u:
    new_upper = min(new_upper, 1.0)
```

### Stopping Conditions

**1. NLL Convergence** (most ideal):
```
Round 1: NLL = -344.831
Round 2: NLL = -344.735
Improvement = 0.096 < 0.1 → Stop
```

**2. No Boundary Issues**:
```
Round 1: All parameters distance from boundary > 1%
→ Stop immediately, no adjustment needed
```

**3. Maximum Rounds**:
```
Reached 3 rounds, even if still touching boundaries
→ Force stop, manual inspection recommended
```

### Output Interpretation

```
================================================================================
📍 Round 1 Optimization
================================================================================
✅ This round optimization completed
   Final NLL = -344.830686

🔍 Checking if Stage3 parameters touch boundaries...
   ⚠️  Sa=0.001000 near lower bound 0.001000 (absolute distance=0.000000e+00)

💡 Recommend adjusting the following boundaries (expansion factor=2.0x):
   Sa lower bound: 0.001000 → 0.000500
   💾 Configuration backed up to: ../config.json.round1.bak
   ✅ Configuration file updated: ../config.json

🔄 Boundary issue detected, preparing for Round 2 optimization...

================================================================================
📍 Round 2 Optimization
================================================================================
✅ This round optimization completed
   Final NLL = -344.735410
   NLL improvement: 0.095276

================================================================================
✅ NLL has converged! Improvement (0.095276) < threshold (0.1)
   Round 1: NLL = -344.830686
   Round 2: NLL = -344.735410
   Stopping further adjustments.
================================================================================
```

---

## Interpreting Results

### PPE Results

```csv
a,d,s,ln_likelihood
295.304401,18.433704,0.003417,-358.80
```

- `a`: Background seismicity rate (events/year)
- `d`: Spatial decay parameter (km)
- `s`: Magnitude decay parameter
- `ln_likelihood`: Log-likelihood

### Aftershock Results

```csv
v,k,ln_likelihood
1.124883,0.073194,-143212.346
```

- `v`: Aftershock triggering intensity
- `k`: PPE-to-aftershock ratio parameter

### EEPAS Results

```csv
am,bm,Sm,at,bt,St,ba,Sa,u,ln_likelihood
1.427,0.88,0.545,0.140,0.886,0.008,1.922,0.001,0.448,-292.153
```

**Parameter Meanings**:
- `am, at, ba`: Magnitude-frequency relation (a parameter)
- `bm, bt`: Gutenberg-Richter relation slope (fixed)
- `Sm, St, Sa`: Uncertainty (standard deviation)
- `u`: EEPAS-PPE mixing ratio

**Physical Constraint Checks**:
- ✅ `bm, bt, ba, Sm, St, Sa > 0`
- ✅ `u ∈ [0, 1]`
- ✅ `am, at` can be negative

---

## Paper Validation Workflow

### Italy Mode - Full Paper-Consistent Configuration

This workflow uses `config_italy_paper_1round_full.json`, fully matching the ggad123.pdf paper methodology:

**Key Settings**:
- Learning period: 1990-2012
- Forecast period: 2012-2022
- mT = 5.0 (target magnitude threshold)
- Use mT as ppe_ref_mag and target_mag
- Single-round optimization (`--max-rounds 1`)
- Three-stage parameter optimization

**Complete Workflow**:

```bash
# Step 1: PPE Learning (using mT anchor)
python3 ppe_learning.py --config config_italy_paper_1round_full.json

# Step 2: Aftershock Parameters (both mag parameters use mT)
python3 fit_aftershock_params.py --config config_italy_paper_1round_full.json --ppe-ref-mag mT --target-mag mT

# Step 3: EEPAS Learning (three-stage + single-round optimization)
python3 eepas_learning_auto_boundary.py --config config_italy_paper_1round_full.json --three-stage --ppe-ref-mag mT --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py --config config_italy_paper_1round_full.json --ppe-ref-mag mT

# Step 5: EEPAS Forecast (fast mode)
python3 eepas_make_forecast.py --config config_italy_paper_1round_full.json --fast --ppe-ref-mag mT
```

**Validation Results** (in `results_italy_paper_1round_full/`):

| Module | Parameter | Value |
|--------|-----------|-------|
| PPE | a | 0.616 |
| | d | 29.64 km |
| | s | ≈ 0 |
| Aftershock | v | 0.577 |
| | k | 0.205 |
| EEPAS | am | 1.234 |
| | Sm | 0.242 |
| | at | 2.589 |
| | bt | 0.349 |
| | St | 0.150 |
| | ba | 0.504 |
| | Sa | 1.000 |
| | u | 0.167 |
| | NLL | -495.41 |

**Paper Consistency Verification**:
- ✅ PPE spatial kernel function: h₀(x,y) = Σ[a·(mₖ-mT)/(π(d²+r²)) + s]
- ✅ PPE magnitude distribution: g₀(m) = β·exp(-β(m-mT))
- ✅ EEPAS spatial distribution: 2D Gaussian (using erf function integration)
- ✅ EEPAS magnitude distribution: Truncated Gaussian (considering m0 truncation effect)
- ✅ EEPAS temporal distribution: Log-normal distribution

---

## Troubleshooting

### Issue 1: PPE/Aftershock Results Not Found

**Error Message**:
```
FileNotFoundError: results/Fitted_par_PPE_2002_2016.csv
```

**Cause**: Prerequisite steps not executed

**Solution**:
```bash
# Ensure sequential execution
python3 ppe_learning.py --config ../config.json
python3 fit_aftershock_params.py --config ../config.json
python3 eepas_learning_auto_boundary.py --config ../config.json
```

---

### Issue 2: NLL Stuck at Suboptimal Value

**Symptom**: EEPAS NLL = -299, expected -292

**Possible Causes**:
1. Boundaries too tight
2. Poor initial values
3. Optimization not converged

**Solution**:
```bash
# Use automatic boundary adjustment
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --max-rounds 5 \
    --tolerance 0.01
```

---

### Issue 3: Path Error

**Error**:
```
Cannot find results/xxx.csv
```

**Cause**: Not executing from correct directory

**Solution**:
```bash
# Must execute from python_src
cd /path/to/EEPAS/src/python_src
python3 xxx.py --config config_italy_causal_ew0.json
```

---

### Issue 4: Numba Compilation Failure

**Error**:
```
numba.core.errors.TypingError: ...
```

**Solution**:
```bash
# Update numba
pip install --upgrade numba

# Clear numba cache
rm -rf ~/.numba_cache
```

---

## Advanced Usage

### Custom m0

```bash
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --m0 2.05
# Overrides m0 value in configuration file
```

### Adjust Convergence Sensitivity

```bash
# Stricter (stops earlier)
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --nll-threshold 0.05

# More relaxed (may run more rounds)
python3 eepas_learning_auto_boundary.py \
    --config ../config.json \
    --nll-threshold 0.2
```

### Compare Results

```bash
python3 utils/compare_results.py \
    --matlab ../results_matlab/Fitted_par_EEPAS_2002_2016.csv \
    --python results_decluster_python/Fitted_par_EEPAS_2002_2016.csv
```

### Analyze Boundary Adjustment History

```bash
python3 utils/analyze_auto_boundary_result.py test_log.log
```

---

## References

See other project documentation:

- `README.md`: Quick Start

---

**Last Updated**: 2025-10-30

---

## Optimizer Comparison Study

See `OPTIMIZER_COMPARISON_REPORT.md` for performance comparison and usage recommendations for various optimizers.

### Key Findings

- ✅ **fminsearchcon (Nelder-Mead) most robust** (finds high-quality solutions across all configurations)
- ⚡ **Gradient methods fast but unstable** (50% success rate, prone to local optima)
- ❌ **Basin-Hopping and extensive Multistart (>10) ineffective for this problem**
- 💡 **Recommended strategy**: Run fminsearchcon and L-BFGS-B + Multistart in parallel, select better result
