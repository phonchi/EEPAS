# Analysis Tools Directory

Analysis tools and interactive notebooks for EEPAS earthquake forecasting.

## 📓 Interactive Notebooks

**Main Analysis Notebooks:**
- **Examine_Psi_Italy_clean.ipynb** - Automated Ψ phenomenon detection
- **EEPAS_Forecast_Evaluation_New.ipynb** - PyCSEP evaluation (reproduce published results)
- **EEPAS_Forecast_Evaluation_End_to_End.ipynb** - PyCSEP evaluation (end-to-end pipeline)
- **Estimate_mc_b_Italy_clean.ipynb** - Catalog preprocessing with SeismoStats

## 🔧 Analysis Scripts

**Core Tools:**
- **analyze_forecast_lambda.py** - Verify forecast Lambda sums
- **forecast_converter.py** - Convert forecasts to PyCSEP format
- **dataset.py** - Data extraction utilities
- **decimal_time.py** - Time format conversion
- **optimize_psi_working.py** - Ψ phenomenon detection
- **plot_relations.py** - Scaling relationship visualization
- **verify_forecasts.py** - PyCSEP forecast verification
- **patch_pycsep.py** - PyCSEP compatibility patches
- **select_m5plus.py** - Select M5+ events from catalog
- **optimize_psi_results.py** - Ψ optimization result analysis

## 📖 Documentation

For detailed usage, see:
- Sphinx documentation: `docs/build/html/index.html`
- Interactive examples: `docs/source/examples/index.rst`

---

**Version:** 0.4.0 | **Last Updated:** 2026-02-27
