# Utilities Directory

This directory contains core utility functions and helper programs for the EEPAS project.

## 📂 File List

### Core Utilities

#### 1. auto_boundary_adjustment.py
**Purpose**: Core logic for automatic boundary adjustment

**Main Functions**:
- `check_boundary_touching()` - Detect if parameters touch boundaries
- `adjust_bounds()` - Adjust boundaries based on touching conditions
- `backup_config()` - Backup configuration files

**Use Cases**:
- Called by `eepas_learning_auto_boundary.py`
- Automatically relax optimization boundaries to avoid constraints

**Key Parameters**:
- `tolerance`: Boundary touching tolerance (default 0.01)
- `expansion_factor`: Boundary expansion multiplier (default 2.0)

---

#### 2. fminsearchcon.py
**Purpose**: Constrained Nelder-Mead simplex optimizer

**Main Function**:
- `fminsearchcon(fun, x0, lb, ub, **options)` - Main optimization function

**Features**:
- Python implementation of MATLAB's fminsearchcon
- Supports upper and lower bound constraints
- Convergence criteria: ftol (absolute tolerance)

**Parameters**:
```python
fminsearchcon(
    fun,           # Objective function
    x0,            # Initial point
    lb, ub,        # Lower and upper bounds
    maxiter=500,   # Maximum iterations
    ftol=1e-4,     # Function tolerance
    xtol=1e-4      # Parameter tolerance
)
```

---

#### 3. data_loader.py
**Purpose**: Earthquake catalog data loading

**Main Functions**:
- `load_earthquake_catalog()` - Load HORUS and CPTI catalogs
- `filter_by_completeness()` - Filter by completeness magnitude

**Supported Formats**:
- HORUS format (Italy earthquake catalog)
- CPTI format (Italy parametric catalog)

---

#### 4. catalog_processor.py
**Purpose**: Earthquake catalog processing and transformation

**Main Functions**:
- `process_catalog()` - Catalog preprocessing
- `compute_distances()` - Calculate hypocentral distances
- `decluster_catalog()` - Declustering processing

---

#### 5. get_paths.py
**Purpose**: Path resolution and file location management

**Main Functions**:
- `resolve_paths()` - Resolve relative paths in configuration files
- `get_data_path()` - Get data file paths
- `get_results_path()` - Get result output paths

**Features**:
- Supports relative and absolute paths
- Cross-platform compatible (Linux/Mac/Windows)
- Automatically executes from `python_src/` or project root

---

#### 6. region_manager.py
**Purpose**: Region management for spatial filtering

**Main Functions**:
- `load_region()` - Load testing and neighborhood regions
- `filter_events_in_region()` - Filter events within region boundaries

---

#### 7. coordinate_transform.py
**Purpose**: Coordinate system transformations

**Main Functions**:
- `wgs84_to_rdn2008()` - WGS84 to RDN2008 (Italy) transformation

---

#### 8. numerical_integration.py
**Purpose**: Numerical integration utilities with fast/accurate modes

**Main Functions**:
- `integrate_spatial_ppe()` - PPE spatial integration (grid or dblquad)
- `integrate_spatial_lambda()` - Lambda spatial integration (trapezoid or dblquad)

**Modes**:
- Fast mode: Grid-based integration (30x30 points)
- Accurate mode: dblquad adaptive integration

---

## 🔧 Development Guide

### Import Utility Functions

From project root:
```python
from utils.data_loader import load_earthquake_catalog
from utils.fminsearchcon import fminsearchcon
from utils.get_paths import resolve_paths
```

### Adding New Utilities

1. Create new `.py` file in `utils/`
2. Add import in `__init__.py`
3. Update this README

---

## 📊 Dependencies

```bash
pip install numpy scipy pandas pyproj
```

---

## 🔍 Troubleshooting

### ImportError: No module named 'utils'
Ensure execution from correct directory:
```bash
cd /path/to/EEPAS_Taiwan-main/src/python_src
python3 your_script.py
```

### Path Resolution Errors
Use functions from `get_paths.py` instead of hardcoded paths:
```python
from utils.get_paths import get_data_path
data_file = get_data_path("horus_catalog.txt")
```

---

## 📝 Core Function Index

| Function | File | Method |
|----------|------|--------|
| Optimizer | fminsearchcon.py | `fminsearchcon()` |
| Boundary Adjustment | auto_boundary_adjustment.py | `check_boundary_touching()` |
| Data Loading | data_loader.py | `load_earthquake_catalog()` |
| Path Resolution | get_paths.py | `resolve_paths()` |
| Coordinate Transform | coordinate_transform.py | `wgs84_to_rdn2008()` |
| Numerical Integration | numerical_integration.py | `integrate_spatial_ppe()` |

---

**Last Updated**: 2025-12-07
**Maintainer**: EEPAS Development Team
