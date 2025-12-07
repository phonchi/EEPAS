# Analysis Tools Directory

This directory contains analysis tools for the EEPAS project, including earthquake data analysis, Ψ parameter optimization, and forecast evaluation.

## 📂 Tool List

### 1. Ψ Parameter Optimization

#### optimize_psi_working.py
**Purpose**: Detect Ψ phenomenon (precursor-triggered events) in earthquake catalogs

**Usage**:
```bash
python3 optimize_psi_working.py --config config.json
```

**Output**:
- Candidate Ψ events with their parameters
- Spatial and temporal relationships
- Magnitude scaling relationships

**Execution Time**: ~10-30 minutes (depends on catalog size)

---

#### optimize_psi_results.py
**Purpose**: Deduplicate and filter Ψ parameter results

**Usage**:
```bash
python3 optimize_psi_results.py
```

**Output**:
- Deduplicated Ψ events
- Statistical summaries
- Quality metrics

---

### 2. Scaling Relationship Analysis

#### plot_relations.py
**Purpose**: Analyze and visualize magnitude, time, and space scaling relationships

**Usage**:
```bash
python3 plot_relations.py
```

**Output**:
- Magnitude relation plots (M_mainshock vs M_precursor)
- Time relation plots (log₁₀(T_precursor) vs M_precursor)
- Spatial relation plots (σ² vs magnitude)

**Analyses**:
- Linear regression with confidence intervals
- Parameter estimation (am, bm, at, bt, σ_A, b_A)
- Residual diagnostics

---

### 3. Data Processing

#### dataset.py
**Purpose**: Extract and process earthquake datasets for analysis

**Main Functions**:
- `extract_precursor_mainshock_pairs()` - Extract Ψ event pairs
- `filter_by_magnitude()` - Filter events by magnitude threshold
- `compute_statistics()` - Compute statistical summaries

---

#### decimal_time.py
**Purpose**: Convert between datetime and decimal year formats

**Main Functions**:
- `datetime_to_decimal()` - Convert datetime to decimal year
- `decimal_to_datetime()` - Convert decimal year to datetime

---

#### select_m5plus.py
**Purpose**: Select and filter M≥5.0 events from catalogs

**Usage**:
```bash
python3 select_m5plus.py --catalog data/HORUS_Italy_RDN2008_polygon_filtered.mat
```

---

### 4. Forecast Evaluation

#### analyze_forecast_lambda.py
**Purpose**: Verify forecast Lambda sums and spatial integration

**Usage**:
```bash
python3 analyze_forecast_lambda.py --results-dir results_italy_causal_ew0
```

**Output**:
- PPE Lambda sum verification
- EEPAS Lambda sum verification
- Comparison with target event count

**Verification**:
- Λ_PPE ≈ N (target event count)
- Λ_EEPAS ≈ N
- Relative difference < 5%

---

#### forecast_converter.py
**Purpose**: Convert EEPAS forecasts to PyCSEP format

**Usage**:
```bash
python3 forecast_converter.py \
    --input results/PREVISIONI_3m_EEPAS_2012_2022.mat \
    --output forecasts/eepas_forecast.csv \
    --format pycsep
```

**Supported Formats**:
- PyCSEP (for CSEP testing)
- CSV (tabular format)
- JSON (metadata included)

---

#### patch_pycsep.py
**Purpose**: Compatibility patches for pycsep library integration

**Functions**:
- Fix spatial cell indexing
- Adjust magnitude bin handling
- Ensure CSEP compliance

---

## 🔧 Dependencies

All tools require the following Python packages:
```bash
pip install numpy scipy pandas matplotlib pyproj
```

For forecast evaluation:
```bash
pip install pycsep
```

## 📊 Output Directories

### analysis_data/
Stores intermediate data and detailed results (JSON, CSV format)

### analysis_outputs/
Stores text reports and summaries

### analysis_plots/
Stores all visualization plots (PNG format)

## 📖 Detailed Documentation

For detailed usage of each tool, refer to:
- Sphinx documentation: `docs/build/html/index.html`
- API reference: `docs/build/html/api_reference/analysis.html`

## 💡 Common Use Cases

### Verify Forecast Results
```bash
# Check Lambda sum consistency
python3 analyze_forecast_lambda.py --results-dir results_italy_causal_ew0
```

### Analyze Scaling Relations
```bash
# Generate scaling relationship plots
python3 plot_relations.py
```

### Convert to CSEP Format
```bash
# Convert forecast for CSEP evaluation
python3 forecast_converter.py --input results/PREVISIONI_3m_EEPAS_2012_2022.mat --format pycsep
```

## 🔍 Troubleshooting

### Data File Not Found
Ensure execution from correct directory:
```bash
cd /path/to/EEPAS/src/python_src
python3 analysis/analyze_forecast_lambda.py
```

### PyCSEP Import Error
Install pycsep:
```bash
pip install pycsep
```

---

**Last Updated**: 2025-12-07
**Maintainer**: EEPAS Development Team
