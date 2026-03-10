<div align="center">
  <img src="logos/logo.png" alt="PyEEPAS Logo" width="200"/>
  <h1>PyEEPAS</h1>
  <p><em>Bridging the Medium-Term Gap in Open-Source Statistical Earthquake Forecasting</em></p>

  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Version](https://img.shields.io/badge/version-0.5.0-blue.svg)](CHANGELOG_EN.md)
</div>

<br/>

**PyEEPAS** is the first open-source Python implementation of the EEPAS (Every Earthquake a Precursor According to Scale) model, built on a complete mathematical derivation of the likelihood function. It fills the medium-term gap in the open-source earthquake forecasting ecosystem — short-term forecasting has ETAS/STEP, long-term has OpenQuake, and now medium-term has PyEEPAS.

## ✨ Key Features

- 🎯 **Complete EEPAS Implementation** - PPE background model + EEPAS medium-term precursory component
- 🌍 **Universal Application** - Apply to any seismic region worldwide
- 🚀 **Automated Workflow** - End-to-end pipeline from raw catalog to forecast evaluation
- ⚡ **High Performance** - Numba JIT acceleration, 4x faster forecasting
- 🔬 **Scientifically Validated** - Reproduces published results + better automated pipeline
- 📊 **PyCSEP Integration** - Standardized forecast evaluation and comparison

## 🎯 Latest Update (v0.5.0)

### Major Improvements

**1. Documentation and Usability**
- ✅ Complete Sphinx documentation with interactive notebooks
- ✅ Archive functionality for reproducible research
- ✅ Single-stage boundary adjustment fix
- ✅ Hard parameter caps to prevent unreasonable optimization

**2. Dual Validation Approach**
- **Reproduce Published Results** (`config_italy_reproduce.json`)
  - Validates framework can replicate Biondini et al. (2023) within 1 hour
  - Uses literature-reported initial parameters

- **End-to-End Automated Pipeline** (`config_italy_endtoend.json`)
  - Automated parameter estimation using rectangular algorithm
  - Achieves better log-likelihood (-484.23) than manual initialization
  - Passes all PyCSEP consistency tests

**3. Interactive Examples**
- Automated Ψ phenomenon detection (Notebook 1)
- PyCSEP forecast evaluation - Reproduce paper (Notebook 2)
- PyCSEP forecast evaluation - End-to-end pipeline (Notebook 3)
- Catalog preprocessing with SeismoStats (Notebook 4)

See [CHANGELOG_EN.md](CHANGELOG_EN.md) for complete version history.

## 📚 Documentation

**Full documentation available at:** `docs/build/html/index.html`

### Quick Links
- **Installation Guide** - `docs/source/user_guide/installation.rst`
- **Quick Start** - `docs/source/user_guide/quickstart.rst`
- **Complete Workflows** - `docs/source/user_guide/workflows.rst`
- **Configuration Reference** - `docs/source/user_guide/configuration.rst`
- **API Documentation** - `docs/source/api_reference/index.rst`
- **Interactive Examples** - `docs/source/examples/index.rst`

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/phonchi/EEPAS.git
cd EEPAS

# Install dependencies
pip install -r requirements.txt
```

### Italy Region - 5-Step Workflow (Reproduce Published Results)

```bash
# Step 1: PPE Learning
python3 ppe_learning.py --config config_italy_reproduce.json

# Step 2: Aftershock Parameters
python3 fit_aftershock_params.py \
    --config config_italy_reproduce.json \
    --ppe-ref-mag mT \
    --target-mag mT

# Step 3: EEPAS Learning (three-stage optimization)
python3 eepas_learning_auto_boundary.py \
    --config config_italy_reproduce.json \
    --three-stage \
    --ppe-ref-mag mT \
    --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py \
    --config config_italy_reproduce.json \
    --ppe-ref-mag mT

# Step 5: EEPAS Forecast
python3 eepas_make_forecast.py \
    --config config_italy_reproduce.json \
    --ppe-ref-mag mT

# Step 6: Archive Results (Optional)
python3 archive_results.py \
    --config config_italy_reproduce.json \
    --results-dir results_italy_reproduce/ \
    --workflow "EEPAS 5-step workflow" \
    --logs *.log \
    --ppe-ref-mag mT \
    --target-mag mT

# Step 7: Verify Forecasts (PyCSEP Statistical Tests)
python3 analysis/verify_forecasts.py \
    --catalog observation_catalog.mat \
    config_italy_reproduce.json

```

### Italy Region - End-to-End Automated Pipeline

```bash
CONFIG=config_italy_endtoend.json

# Step 1-5 (same structure, key difference: --target-mag m0)
python3 ppe_learning.py --config $CONFIG --ppe-ref-mag mT
python3 fit_aftershock_params.py --config $CONFIG --ppe-ref-mag mT --target-mag m0
python3 eepas_learning_auto_boundary.py --config $CONFIG --three-stage --ppe-ref-mag mT
python3 ppe_make_forecast.py --config $CONFIG --ppe-ref-mag mT
python3 eepas_make_forecast.py --config $CONFIG --ppe-ref-mag mT

# Step 7: Verify Forecasts
python3 analysis/verify_forecasts.py \
    --catalog analysis/HORUS_Italy_filtered.mat \
    --source-crs EPSG:7794 \
    $CONFIG
```

**Expected Runtime:** ~1 hour on 8-core laptop

See `docs/source/user_guide/workflows.rst` for complete workflow details.

## 📁 Directory Structure

```
EEPAS/
├── ppe_learning.py              # Step 1: PPE parameter learning
├── fit_aftershock_params.py     # Step 2: Aftershock parameters
├── eepas_learning_auto_boundary.py  # Step 3: EEPAS parameter learning
├── ppe_make_forecast.py         # Step 4: PPE forecast
├── eepas_make_forecast.py       # Step 5: EEPAS forecast
├── archive_results.py           # Archive workflow results
├── utils/                       # Core utilities
│   ├── data_loader.py          # Configuration and data loading
│   ├── numerical_integration.py # Numerical integration (FAST/ACCURATE)
│   ├── catalog_processor.py    # Catalog filtering
│   └── region_manager.py       # Region management
├── analysis/                    # Analysis and validation tools
│   ├── EEPAS_Forecast_Evaluation_New.ipynb  # Reproduce paper results
│   ├── EEPAS_Forecast_Evaluation_End_to_End.ipynb  # End-to-end pipeline
│   ├── Examine_Psi_Italy_clean.ipynb  # Ψ phenomenon detection
│   └── Estimate_mc_b_Italy_clean.ipynb  # b-value estimation
├── data/                        # Earthquake catalogs and regions
├── docs/                        # Sphinx documentation
└── config*.json                 # Configuration files
```

## 🔧 Configuration Files

- `config_italy_reproduce.json` - **Reproduce published results** (recommended for standard workflow)
  - Uses literature-reported parameters from Biondini et al. (2023)
  - Validates framework can replicate published results
  - Standard 5-step workflow example

- `config_italy_endtoend.json` - **End-to-end automated pipeline** (advanced)
  - Automated parameter initialization using rectangular algorithm
  - mT = 5.0, m0 = 2.95
  - Better log-likelihood results (-484.23)

See `docs/source/user_guide/configuration.rst` for creating custom configurations.

## 📊 Validation Results

### Reproduce Published Results (Biondini et al. 2023)
- Configuration: `config_italy_reproduce.json`
- Learning: 1990-2012, Forecast: 2012-2022
- Runtime: < 1 hour
- ✅ Successfully replicates published parameters

### End-to-End Automated Pipeline
- Configuration: `config_italy_endtoend.json`
- **Automated** parameter estimation (no manual Ψ identification needed)
- Log-likelihood: **-484.23** (better than manual initialization)
- ✅ Passes all PyCSEP consistency tests (L-test, N-test, S-test, M-test)

## 🧪 Analysis Tools

### Interactive Notebooks
1. **Automated Ψ Detection** - `analysis/Examine_Psi_Italy_clean.ipynb`
2. **Forecast Evaluation (Reproduce Paper)** - `analysis/EEPAS_Forecast_Evaluation_New.ipynb`
3. **Forecast Evaluation (End-to-End)** - `analysis/EEPAS_Forecast_Evaluation_End_to_End.ipynb`
4. **Catalog Preprocessing** - `analysis/Estimate_mc_b_Italy_clean.ipynb`

### Validation Scripts
```bash
# Validate forecast Lambda sums
python3 analysis/analyze_forecast_lambda.py
```

## ⚙️ Advanced Options

### EEPAS Learning Options

```bash
# Three-stage optimization (recommended)
python3 eepas_learning_auto_boundary.py --config $CONFIG --three-stage --ppe-ref-mag mT --max-rounds 1

# Custom boundary rounds
python3 eepas_learning_auto_boundary.py --config $CONFIG --ppe-ref-mag mT --max-rounds 5
```

### Integration Mode

- **Fast Mode** (default): Trapezoidal rule, 1.75x faster, <0.2% difference
- **Accurate Mode** (`--accurate`): scipy.dblquad, for final paper validation

### Magnitude Reference

| Option | Description | Use Case |
|--------|-------------|----------|
| `--ppe-ref-mag mT` | Anchor to target magnitude | Recommended |
| `--ppe-ref-mag m0` | Anchor to completeness magnitude | Legacy mode |

## 📦 Output Files

### Learning Phase

| File | Description |
|------|-------------|
| `Fitted_par_PPE_YYYY_YYYY.csv` | PPE parameters (a, d, s) |
| `Fitted_par_aftershock_YYYY_YYYY.csv` | Aftershock parameters (ν, κ) |
| `Fitted_par_EEPAS_YYYY_YYYY.csv` | EEPAS parameters (8 params) |

### Forecast Phase

| File | Description |
|------|-------------|
| `PREVISIONI_3m_PPE_YYYY_YYYY.mat` | PPE forecast rates |
| `PREVISIONI_3m_EEPAS_YYYY_YYYY.mat` | EEPAS forecast rates |

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Parameters hitting boundaries | Increase `--max-rounds` (default: 3, try 5) |
| Optimization not converging | Use `--three-stage` for complex parameter spaces |
| Memory errors | Reduce catalog size or use fast mode |
| Integration warnings | Usually valid if <1% of integrations fail |

## 🌍 Adapting to Your Region

Required data files (all `.mat` format):
1. **Earthquake Catalog** — Year, Month, Day, Hour, Minute, Second, Lat, Lon, Depth, Magnitude
2. **Testing Region** — Grid cells: lon_min, lon_max, lat_min, lat_max
3. **Neighborhood Region** — Must strictly contain testing region

Copy `config_italy_reproduce.json`, modify parameters, and run the 5-step workflow.
See `docs/source/user_guide/workflows.rst` for detailed guide.

## ⚡ Performance Tips

- **Fast Mode** for daily research (1.75x speedup, <0.2% difference)
- **Accurate Mode** for final paper validation only
- **Three-stage** for large regions (>50 cells); single-stage for smaller
- First run slower due to Numba JIT compilation warmup

## 🔬 Scientific Background

EEPAS is grounded in the **Ψ phenomenon** - empirical observation that most large earthquakes are preceded by increased seismicity. The model combines:

- **PPE (Proximity to Past Earthquakes)** - Baseline intensity in the absence of medium-term precursory build-up
- **EEPAS precursory component** - Medium-term precursory scaling based on magnitude, time, and spatial relationships

**Mathematical Framework:**
```
λ(t,m,x,y) = μ·λ₀ + (1-μ)·Σᵢ ηᵢ·λᵢ
```

Where:
- μ: Failure-to-predict rate
- λ₀: PPE baseline rate
- λᵢ: Contribution from precursor event i

See `docs/source/technical/mathematical_foundation.rst` for detailed derivations.

## 🤝 Integration with Seismological Tools

- **PyCSEP** - Forecast evaluation (consistency tests, scoring rules)
- **SeismoStats** - b-value estimation, catalog preprocessing
- **Rectangular Algorithm** - Automated Ψ phenomenon detection

## 📦 Software Availability

PyEEPAS is released under the MIT License. Source code, documentation, and
example configurations are available at https://github.com/phonchi/EEPAS.
The package requires Python 3.8+ with NumPy, SciPy, Numba, and joblib.

## 📄 Citation

If you use PyEEPAS in your research, please cite:

```bibtex
@article{pyeepas2026,
  title={PyEEPAS: Bridging the Medium-Term Gap in Open-Source Statistical Earthquake Forecasting},
  author={Chung, Szu-Chi and Cho, Chien-Hong and Wen, Strong},
  journal={xxx},
  year={2026}
}
```

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Based on the original EEPAS model by Rhoades and colleagues
- Italy earthquake data from CPTI15 and HORUS catalogs
- Integration with PyCSEP framework (Savran et al., 2022)
- SeismoStats package (Mirwald et al., 2025)

## 📞 Support

- **Documentation:** `docs/build/html/index.html`
- **Issues:** [GitHub Issues](https://github.com/phonchi/EEPAS/issues)
- **Changelog:** [CHANGELOG_EN.md](CHANGELOG_EN.md)

---

**Version:** 0.5.0 | **Last Updated:** 2026-02-27




