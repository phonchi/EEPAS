# Utilities Directory

Core utility modules for the EEPAS earthquake forecasting system.

## Core Modules

### Configuration and Data Loading

- **data_loader.py** - Load configuration files and earthquake catalogs
- **catalog_processor.py** - Process and filter earthquake catalogs
- **region_manager.py** - Manage spatial regions (testing and neighborhood)
- **get_paths.py** - Resolve file paths from configuration

### Numerical Methods

- **numerical_integration.py** - Fast and accurate numerical integration
- **fminsearchcon.py** - Constrained Nelder-Mead optimizer

### Coordinate Systems

- **coordinate_transform.py** - WGS84 ↔ projected coordinates (RDN2008, TWD97)

### Optimization Support

- **auto_boundary_adjustment.py** - Automatic parameter boundary adjustment
- **result_archiver.py** - Archive workflow results for reproducibility
- **time_compensation.py** - Forecast time compensation
- **catalog_processor_extensions.py** - Extended catalog processing
- **analyze_auto_boundary_result.py** - Auto-boundary result analysis

## Usage

```python
from utils.data_loader import DataLoader
from utils.numerical_integration import fast_kernel_sum_2d

# Load configuration
cfg = DataLoader.load_config('config.json')

# Load earthquake catalog
catalog = DataLoader.load_catalogs('config.json')
```

## Documentation

For detailed API documentation, see:
- `docs/build/html/api_reference/utils.html`
- `docs/source/api_reference/utils.rst`

---

**Version:** 0.5.0
**Last Updated:** 2026-02-27
