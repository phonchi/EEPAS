<div align="center">
  <img src="logos/logo.png" alt="EEPAS Logo" width="200"/>
  <h1>EEPAS - Python Implementation</h1>

  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

<br/>

Python implementation of the **EEPAS** (Every Earthquake a Precursor According to Scale) earthquake forecasting model for Italy seismic hazard assessment.

## ✨ Features

- 🎯 **Complete Implementation** - Includes PPE, EEPAS, and aftershock parameter learning
- 🌍 **Italy Application** - Optimized for Italy seismicity with proper Testing/Neighborhood region handling
- 🚀 **Automatic Optimization** - Automatic boundary adjustment ensuring convergence
- 📊 **Multiple Configurations** - Standard mode and three-stage optimization
- ⚡ **High Performance** - Numba JIT acceleration, PPE forecasting 60-70x faster with <0.03% accuracy loss
- 🧪 **Fully Validated** - Complete consistency with mathematical definitions and empirical validation

## 📊 Latest Achievements (v1.3.0)

### 🔬 Numerical Integration Refactoring and Validation

**Core Achievement: Unified numerical integration interface with verified correctness**

This version completes the refactoring of numerical integration methods, unifying the integration calling interface across all modules, and validating the implementation correctness through comprehensive FAST vs ACCURATE mode comparison.

**Refactoring Contents**:
- Unified numerical integration interface (`utils/numerical_integration.py`)
- ACCURATE mode: scipy.dblquad double integration (highest precision)
- FAST mode: Trapezoidal rule integration (default, high performance)
- All modules support `--accurate` / `--fast` parameter switching

**Validation Results** (`ACCURATE_VS_FAST_COMPARISON_REPORT.md`):
- **Testing Period**: Learning 1990-2012, Forecast 2012-2022
- **Test Configurations**: useCausalEW=0 (Fixed EW) and useCausalEW=1 (Dynamic EW)
- **Parameter Consistency**:
  - PPE parameter difference < 0.001%
  - EEPAS parameter difference < 0.16%
  - Forecast Lambda difference < 0.004%
- **Lambda Integration Validation**:
  - Learning: Λ_PPE ≈ 27.00 (target event count) ✓
  - Forecast: PPE ~14 + EEPAS ~16 = ~30 (close to 27) ✓
- **Performance Improvement**: FAST mode overall **1.75x faster** (Forecast **4x faster**)

**Conclusion**: ✅ Refactoring successful, trapezoidal rule highly consistent with dblquad (< 0.2% difference), FAST mode safe for daily research use

### 🌍 Italy Region Validation

**Mathematical Formula Consistency**: All formulas fully consistent with the paper (ggad123.pdf) ✓

**Typical Parameters** (1990-2012, validated with both integration modes):
- PPE: a=0.616, d=29.64, s≈0
- Aftershock: v=0.577 (57.7% non-aftershocks), k=0.205
- EEPAS: am=1.23, bm=1.00, Sm=0.24, at=2.59, bt=0.35, St=0.15, ba=0.50, Sa=1.00, u=0.17
- NLL ≈ -495 to -496

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Usage Guide](#usage-guide)
- [Analysis Tools](#analysis-tools)
- [Configuration](#configuration)
- [Development](#development)
- [Documentation](#documentation)
- [Citation](#citation)

## 🚀 Installation

### System Requirements

- Python 3.8 or higher
- 8GB+ RAM (recommended)
- Linux / macOS / Windows

### Dependency Installation

```bash
# Clone repository
git clone https://github.com/your-org/EEPAS.git
cd EEPAS/src/python_src

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
python3 -c "import numpy, scipy, numba, pandas; print('✓ All dependencies installed')"
```

## ⚡ Quick Start

### Italy Mode - Complete Forecasting Workflow

```bash
# 1. PPE parameter learning
python3 ppe_learning.py --config config_italy_causal_ew0.json

# 2. Aftershock parameter learning
python3 fit_aftershock_params.py --config config_italy_causal_ew0.json --ppe-ref-mag mT --target-mag mT

# 3. EEPAS parameter learning (automatic boundary adjustment + three-stage optimization)
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json --three-stage --ppe-ref-mag mT --max-rounds 1

# 4. PPE forecast (fast mode recommended)
python3 ppe_make_forecast.py --config config_italy_causal_ew0.json --fast --ppe-ref-mag mT

# 5. EEPAS forecast (fast mode recommended)
python3 eepas_make_forecast.py --config config_italy_causal_ew0.json --fast --ppe-ref-mag mT

# Causality weight test configurations
# EW0: Fixed EW
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew0.json --three-stage --no-boundary-adjustment --fast

# EW1: Dynamic EW
python3 eepas_learning_auto_boundary.py --config config_italy_causal_ew1.json --three-stage --no-boundary-adjustment --fast
```

## 📁 Directory Structure

```
python_src/
├── README.md                          # This file
├── USAGE.md                           # Detailed usage guide
├── requirements.txt                   # Python dependencies
│
├── Configuration Files/
│   ├── config.json                          # Taiwan standard configuration
│   ├── config_decluster.json                # Taiwan declustered configuration
│   ├── config_include921.json               # Taiwan include921 configuration
│   ├── config_m205.json                     # Taiwan m0=2.05 configuration
│   ├── config_italy.json                    # Italy standard configuration
│   ├── config_italy_3stage.json             # Italy three-stage optimization
│   ├── config_italy_causal_ew0.json         # Numerical integration validation: EW0
│   ├── config_italy_causal_ew0_accurate.json # Numerical integration validation: EW0 accurate mode
│   ├── config_italy_causal_ew1.json         # Numerical integration validation: EW1
│   └── config_italy_causal_ew1_accurate.json # Numerical integration validation: EW1 accurate mode
│
├── Core Programs/
│   ├── ppe_learning.py                      # PPE parameter learning
│   ├── fit_aftershock_params.py             # Aftershock parameter learning
│   ├── eepas_learning.py                    # EEPAS basic learning
│   ├── eepas_learning_auto_boundary.py      # EEPAS auto boundary adjustment (recommended)
│   ├── ppe_make_forecast.py                 # PPE forecasting
│   ├── eepas_make_forecast.py               # EEPAS forecasting
│   ├── optimize_eepas_parameters.py         # EEPAS optimizer
│   ├── eepas_likelihood.py                  # EEPAS likelihood function
│   ├── ppe_optimization.py                  # PPE optimization
│   ├── neg_log_like_aftershock.py           # Aftershock likelihood function
│   └── calculate_earthquake_weights.py      # Earthquake weight calculation
│
├── utils/                             # Utility modules
│   ├── data_loader.py                       # Data loading (supports region configuration)
│   ├── catalog_processor.py                 # Catalog processing (supports region filtering)
│   ├── region_manager.py                    # Region management (Testing/Neighborhood)
│   ├── auto_boundary_adjustment.py          # Boundary adjustment logic
│   ├── get_paths.py                         # Path handling
│   └── fminsearchcon.py                     # Optimization tools
│
├── data/                              # Earthquake data
│   ├── Taiwan/                              # Taiwan data
│   │   ├── CELLE_ter_TW_twd97_24regions_correct.mat
│   │   └── GDMScatalog_A_filtered_twd97.mat
│   └── Italy/                               # Italy data
│       ├── CELLE_ter.mat                    # Testing region (177 grid cells)
│       ├── HORUS_Italy_RDN2008_polygon_filtered.mat  # Neighborhood region
│       └── CPTI15.mat                       # Italian catalog
│
├── docs/                              # Documentation and reports
│   ├── README.md                            # Subdirectory overview
│   └── ...
│
├── results/                           # Taiwan standard results
├── results_decluster/                 # Taiwan declustered results
├── results_include921/                # Taiwan include921 results
├── results_m205_python/               # Taiwan m0=2.05 results
├── results_italy/                     # Italy standard results
├── results_italy_3stage/              # Italy three-stage results
├── results_italy_causal_ew0/          # Italy EW0 results
├── results_italy_causal_ew0_accurate/ # Italy EW0 accurate mode results
├── results_italy_causal_ew1/          # Italy EW1 results
└── archive_test_files/                # Historical test files (archived)
```

## 📖 Usage Guide

### Core Workflow

#### 1. PPE Parameter Learning

```bash
python3 ppe_learning.py --config config.json
```

**Output**: `results/Fitted_par_PPE_2002_2016.csv`

#### 2. Aftershock Parameter Learning

```bash
python3 fit_aftershock_params.py --config config.json
```

**Output**: `results/Fitted_par_aftershock_2002_2016.csv`

#### 3. EEPAS Parameter Learning

Using automatic boundary adjustment (**Recommended**):

```bash
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --max-rounds 3 \
    --tolerance 0.01 \
    --expansion 2.0 \
    --nll-threshold 0.1
```

**Output**: `results/Fitted_par_EEPAS_2002_2016.csv`

**Parameter Description**:
- `--max-rounds`: Maximum boundary adjustment rounds (default 3)
- `--tolerance`: Boundary touching tolerance (default 0.01 = 1%)
- `--expansion`: Boundary expansion factor (default 2.0)
- `--nll-threshold`: NLL convergence threshold (default 0.1)
- `--optimizer`: Optimizer selection (fminsearchcon, L-BFGS-B, TNC, SLSQP, Powell, default fminsearchcon)
- `--no-multistart`: Disable multi-start (default enabled with 3 starting points)
- `--n-starts`: Number of multi-start points (default 3)
- `--basinhopping`: Use Basin-Hopping global optimization
- `--basinhopping-niter`: Basin-Hopping iteration count (default 20)

**Optimizer Selection Recommendations** (see [OPTIMIZER_COMPARISON_REPORT.md](OPTIMIZER_COMPARISON_REPORT.md)):
- **Recommended**: `fminsearchcon` (most robust, finds high-quality solutions for all configurations)
- **Fast**: `L-BFGS-B` + `--n-starts 3` (fast but 50% chance of local optima)
- **Balanced**: Run both in parallel, take better result

**Examples**:
```bash
# Using L-BFGS-B + Multistart (3 starting points)
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --optimizer L-BFGS-B \
    --n-starts 3

# Using fminsearchcon (single point, most robust)
python3 eepas_learning_auto_boundary.py \
    --config config.json \
    --optimizer fminsearchcon \
    --no-multistart
```

#### 4-5. Forecasting

```bash
# PPE forecast
python3 ppe_make_forecast.py --config config.json

# EEPAS forecast
python3 eepas_make_forecast.py --config config.json
```

**Output**: `results/PREVISIONI_3m_*_2016_2024_24.mat`

## 🔬 Analysis Tools

### Earthquake Distribution Analysis

Analyze spatial distribution of Taiwan earthquakes in 6 and 24 regions:

```bash
python3 analysis/run_distribution_analysis.py config.json
```

**Output**:
- Console: Statistical summary (valid earthquake count, regional activity, temporal segments)
- `.mat` files: Complete analysis results

See: `docs/README_DISTRIBUTION_ANALYSIS.md`

### Weight Analysis

Compare earthquake weight distributions across 4 configurations:

```bash
python3 analysis/run_weight_analysis.py
```

**Analysis**:
- 4 configurations (standard, declustered, include921, m0=2.05)
- Annual and monthly weight distributions
- Statistical features (mean, standard deviation, coefficient of variation)
- Cross-configuration comparison

See: `docs/README_WEIGHT_ANALYSIS.md`

### Region Subdivision

Subdivide 6 regions into 24 regions:

```bash
python3 analysis/region_subdivision.py \
    data/CELLE_ter_TW.mat \
    output_24regions.mat \
    --lon-subdivisions 2 \
    --lat-subdivisions 2
```

**Workflow**:
1. Subdivide in WGS84 lat/lon (uniform angular intervals)
2. Convert to TWD97 using `convert_to_twd97.py`
3. Validate conversion precision

See: `docs/REGION_SUBDIVISION_VERIFICATION.md`

### Coordinate Conversion

WGS84 (lat/lon) → TWD97 TM2 zone 121 (projected coordinates):

```bash
python3 utils/convert_to_twd97.py \
    --horus-in data/GDMScatalog_A_filtered.mat \
    --celle-in data/CELLE_ter_TW.mat \
    --horus-out output_catalog_twd97.mat \
    --celle-out output_celle_twd97.mat
```

**Support**:
- HORUS earthquake catalog conversion
- CELLE region definition conversion
- EPSG:3826 projection (TWD97 TM2 zone 121)
- Meters → kilometers unit conversion

## ⚙️ Configuration

### Italy Configurations

| Config File | Description | Learning Period | Forecast Period | useCausalEW | Results Directory |
|------------|-------------|-----------------|-----------------|-------------|-------------------|
| `config_italy.json` | Standard configuration | 1990-2012 | 2012-2022 | 0 | results_italy/ |
| `config_italy_3stage.json` | Three-stage optimization | 1990-2012 | 2012-2022 | 0 | results_italy_3stage/ |
| `config_italy_causal_ew0.json` | EW0 test | 1990-2012 | 2012-2022 | 0 | results_italy_causal_ew0/ |
| `config_italy_causal_ew0_accurate.json` | EW0 accurate mode | 1990-2012 | 2012-2022 | 0 | results_italy_causal_ew0_accurate/ |
| `config_italy_causal_ew1.json` | EW1 test | 1990-2012 | 2012-2022 | 1 | results_italy_causal_ew1/ |

**Region Handling**:
- Testing Region: 177 grid cells (30√2 km)
- Neighborhood Region: CPTI15 polygon (includes offshore areas, avoids edge effects)

**Causality Settings** (for numerical integration validation tests):
- useCausalEW=0: Fixed EW
- useCausalEW=1: Dynamic EW (dynamic causal weighting)

### Configuration File Structure

```json
{
  "dataDir": "data",
  "resultsDir": "results_italy_causal_ew0",
  "catalogStartYear": 1985,
  "learnStartYear": 1990,
  "learnEndYear": 2012,
  "forecastStartYear": 2012,
  "forecastEndYear": 2022,
  "inputFiles": {
    "catalogFile": "HORUS_Italy_RDN2008_polygon_filtered.mat",
    "neighborhoodRegionFile": "CPTI15.mat",
    "testingRegionFile": "CELLE_ter.mat"
  },
  "modelParams": {
    "m0": 3.0,
    "mT": 5.0,
    "B": 0.96,
    ...
  }
}
```

## 🧪 Testing and Validation

### Italy Mode - Region Implementation Validation

Fully compliant with mathematical definitions in ggad123.pdf Equation 1:

- ✅ **Source Events**: From Neighborhood Region (avoids edge effects)
- ✅ **Target Event Summation**: Restricted to Testing Region R
- ✅ **Integration Range**: Integrated over Testing Region R (177 grid cells)

### Performance Validation

**PPE Forecast Integration Method Comparison**:
- Accurate (scipy.integrate.quad_vec): Slow but precise
- Fast (Numba JIT midpoint): **60-70x faster**, accuracy loss **<0.03%**

**EEPAS Forecast Optimization**:
- Initial version: 277 seconds
- Optimized: **56 seconds** (5x speedup)

## 🛠️ Development

### Coding Standards

- Python 3.8+ syntax
- Type hints
- Docstring documentation
- PEP 8 code style

### Performance Optimization

- Numba JIT compilation of core functions
- Vectorized computation
- Sparse matrix operations

### Contributing Guidelines

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Submit Pull Request

## 📚 Documentation

### Main Documentation
- **README.md** (this file) - Project overview and quick start
- **USAGE.md** - Detailed usage guide
- **docs/README.md** - Subdirectory documentation overview

### Analysis Reports
- **docs/README_DISTRIBUTION_ANALYSIS.md** - Earthquake distribution analysis documentation
- **docs/README_WEIGHT_ANALYSIS.md** - Earthquake weight analysis documentation
- **docs/REGION_SUBDIVISION_VERIFICATION.md** - Region subdivision validation report

### Test Data
Test files and intermediate results moved to `archive_test_files/` directory

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original MATLAB version developers
- Central Weather Bureau Seismological Center, Taiwan (data provision)
- GDMS earthquake catalog maintenance team
- CPTI15 Italian earthquake catalog maintenance team

## 📖 Citation

If you use this project in your research, please cite:

```bibtex
@software{eepas_taiwan_italy_python,
  title = {EEPAS Taiwan & Italy - Python Implementation},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/your-org/EEPAS_Taiwan}
}
```

## 🔗 Related Resources

- [EEPAS Original Paper (ggad123.pdf)](ggad123.pdf)
- [Taiwan Earthquake Catalog](https://gdms.cwb.gov.tw/)
- [TWD97 Coordinate System](https://en.wikipedia.org/wiki/TWD97)

---

**Version**: 1.3.0
**Python**: 3.8+
**Last Updated**: 2025-11-06

### 📝 Latest Updates (v1.3.0)
- 🔬 **Numerical Integration Refactoring**: Unified integration interface, supports ACCURATE/FAST mode switching
- ✅ **Validation Complete**: FAST vs ACCURATE parameter difference < 0.2%, refactoring correctness confirmed
- ⚡ **Performance Improvement**: FAST mode 1.75x faster, Forecast stage 4x faster
- 📊 **Lambda Validation**: Learning and Forecast stage integration validation passed
- 🚀 **Automated Workflow**: Complete workflow scripts for dual causality settings
