<div align="center">
  <img src="logos/logo.png" alt="EEPAS Logo" width="200"/>
  <h1>EEPAS - Python Implementation</h1>

  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](CHANGELOG_EN.md)
</div>

<br/>

**EEPAS** (Every Earthquake a Precursor According to Scale) is a state-of-the-art medium- to long-term earthquake forecasting model. This is the first fully documented, high-performance open-source Python implementation.

## ✨ Key Features

- 🎯 **Complete EEPAS Implementation** - PPE background model + EEPAS short-term triggering
- 🌍 **Universal Application** - Apply to any seismic region worldwide
- 🚀 **Automated Workflow** - End-to-end pipeline from raw catalog to forecast evaluation
- ⚡ **High Performance** - Numba JIT acceleration, 4x faster forecasting
- 🔬 **Scientifically Validated** - Reproduces published results + better automated pipeline
- 📊 **PyCSEP Integration** - Standardized forecast evaluation and comparison

## 🎯 Latest Update (v0.4.0)

### Major Improvements

**1. Documentation and Usability**
- ✅ Complete Sphinx documentation with interactive notebooks
- ✅ Archive functionality for reproducible research
- ✅ Single-stage boundary adjustment fix
- ✅ Hard parameter caps to prevent unreasonable optimization

**2. Dual Validation Approach**
- **Reproduce Published Results** (`config_italy_causal_ew0_rerun.json`)
  - Validates framework can replicate Biondini et al. (2023) within 1 hour
  - Uses literature-reported initial parameters

- **End-to-End Automated Pipeline** (`config_italy_target_m0.json`)
  - Automated parameter estimation using rectangular algorithm
  - Achieves better log-likelihood (-483) than manual initialization
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
cd EEPAS/src/python_src

# Install dependencies
pip install -r requirements.txt
```

### Italy Region - 5-Step Workflow (Reproduce Published Results)

```bash
# Step 1: PPE Learning
python3 ppe_learning.py --config config_italy_causal_ew0_rerun.json

# Step 2: Aftershock Parameters
python3 fit_aftershock_params.py \
    --config config_italy_causal_ew0_rerun.json \
    --ppe-ref-mag mT \
    --target-mag mT

# Step 3: EEPAS Learning (three-stage optimization)
python3 eepas_learning_auto_boundary.py \
    --config config_italy_causal_ew0_rerun.json \
    --three-stage \
    --ppe-ref-mag mT \
    --max-rounds 1

# Step 4: PPE Forecast
python3 ppe_make_forecast.py \
    --config config_italy_causal_ew0_rerun.json \
    --ppe-ref-mag mT

# Step 5: EEPAS Forecast
python3 eepas_make_forecast.py \
    --config config_italy_causal_ew0_rerun.json \
    --ppe-ref-mag mT

# Step 6: Archive Results (Optional)
python3 archive_results.py \
    --config config_italy_causal_ew0_rerun.json \
    --results-dir results_italy_causal_ew0_rerun/ \
    --workflow "EEPAS 5-step workflow" \
    --logs *.log \
    --ppe-ref-mag mT \
    --target-mag mT
```

**Expected Runtime:** ~1 hour on 8-core laptop

See `docs/source/user_guide/workflows.rst` for complete workflow details.

## 📁 Directory Structure

```
python_src/
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

- `config_italy_causal_ew0_rerun.json` - **Reproduce published results** (recommended for standard workflow)
  - Uses literature-reported parameters from Biondini et al. (2023)
  - Validates framework can replicate published results
  - Standard 5-step workflow example

- `config_italy_target_m0.json` - **End-to-end automated pipeline** (advanced)
  - Automated parameter initialization using rectangular algorithm
  - mT = 4.95, m0 = 2.95
  - Better log-likelihood results (-483)

See `docs/source/user_guide/configuration.rst` for creating custom configurations.

## 📊 Validation Results

### Reproduce Published Results (Biondini et al. 2023)
- Configuration: `config_italy_causal_ew0_rerun.json`
- Learning: 1990-2012, Forecast: 2012-2022
- Runtime: < 1 hour
- ✅ Successfully replicates published parameters

### End-to-End Automated Pipeline
- Configuration: `config_italy_target_m0.json`
- **Automated** parameter estimation (no manual Ψ identification needed)
- Log-likelihood: **-483** (better than manual initialization)
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

## 🔬 Scientific Background

EEPAS is grounded in the **Ψ phenomenon** - empirical observation that most large earthquakes are preceded by increased seismicity. The model combines:

- **PPE (Proximity to Past Earthquakes)** - Background seismicity model
- **EEPAS** - Short-term earthquake triggering based on scaling relations

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

## 📄 Citation

If you use EEPAS in your research, please cite:

```bibtex
@article{eepas2024,
  title={EEPAS: Every Earthquake a Precursor According to Scale},
  author={Author Names},
  journal={Journal Name},
  year={2024}
}
```

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Based on the original EEPAS model by Rhoades, Christophersen, and colleagues
- Italy earthquake data from CPTI15 and HORUS catalogs
- Integration with PyCSEP framework (Savran et al., 2022)
- SeismoStats package (Mirwald et al., 2025)

## 📞 Support

- **Documentation:** `docs/build/html/index.html`
- **Issues:** [GitHub Issues](https://github.com/phonchi/EEPAS/issues)
- **Changelog:** [CHANGELOG_EN.md](CHANGELOG_EN.md)

---

**Version:** 0.4.0 | **Last Updated:** 2025-12-11
