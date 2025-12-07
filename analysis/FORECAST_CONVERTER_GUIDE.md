# EEPAS Forecast Converter - User Guide

**Version**: 1.0.0
**Date**: 2025-11-26
**Author**: EEPAS Team

---

## 📚 Overview

The `EEPASForecastConverter` class provides a complete solution for converting EEPAS/PPE forecast files (MATLAB `.mat` format) to PyCSEP-compatible gridded forecast format.

### Key Features

- ✅ **Automatic format detection** - Detects MATLAB variable names automatically
- ✅ **Coordinate transformation** - Converts RDN2008 (EPSG:7794) → WGS84 (EPSG:4326)
- ✅ **Spatial downsampling** - Divides coarse grids into 0.1° × 0.1° sub-grids
- ✅ **Period handling** - Supports 3-month, 1-year, or custom periods
- ✅ **PyCSEP integration** - Direct conversion to `GriddedForecast` objects
- ✅ **Batch processing** - Convert all periods and sum rates

---

## 🚀 Quick Start

### Basic Usage

```python
from analysis.forecast_converter import EEPASForecastConverter

# Initialize converter
converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_EEPAS_2012_2022.mat',
    grid_file='CELLE_ter.mat'
)

# Convert single period
converter.convert_period(
    period=1,
    output_file='forecast_period_1.dat'
)

# Convert all periods (sum rates)
converter.convert_all_periods(
    output_file='forecast_all_periods.dat'
)
```

### One-Line Conversion

```python
from analysis.forecast_converter import convert_eepas_forecast

# Convert specific period
convert_eepas_forecast(
    'PREVISIONI_3m_EEPAS_2012_2022.mat',
    'CELLE_ter.mat',
    'forecast_period_1.dat',
    period=1
)

# Convert all periods
convert_eepas_forecast(
    'PREVISIONI_3m_EEPAS_2012_2022.mat',
    'CELLE_ter.mat',
    'forecast_all_periods.dat'
)
```

---

## 📖 Detailed Usage

### 1. Initialization Parameters

```python
converter = EEPASForecastConverter(
    forecast_file='path/to/forecast.mat',      # EEPAS/PPE forecast file
    grid_file='path/to/CELLE_ter.mat',         # Grid definition file
    num_regions=177,                            # Number of spatial grids (Italy: 177)
    num_magnitude_steps=25,                     # Number of magnitude bins
    magnitude_min=5.0,                          # Minimum magnitude
    magnitude_step=0.1,                         # Magnitude bin width
    depth_min=0.0,                              # Minimum depth (km)
    depth_max=30.0,                             # Maximum depth (km)
    coordinate_transform=True,                  # Enable coordinate transformation
    source_crs='EPSG:7794',                     # Source CRS (RDN2008 for Italy)
    target_crs='EPSG:4326',                     # Target CRS (WGS84)
    verbose=True                                # Print progress messages
)
```

### 2. Convert Single Period

```python
# Convert period 1 (e.g., 2012 Q1)
period_data = converter.convert_period(
    period=1,
    start_year=2012,                    # Optional: for date calculation
    output_file='forecast_p1.dat',      # Optional: save to file
    perform_downsampling=True,          # Enable spatial downsampling
    grid_resolution=0.1                 # Sub-grid resolution (degrees)
)

print(f"Total grid points: {len(period_data)}")
print(f"Total rate: {period_data['RATE'].sum():.6f}")
```

### 3. Convert All Periods

```python
# Convert and sum all periods (e.g., 2012-2022)
all_data = converter.convert_all_periods(
    start_period=1,                     # Start from period 1
    end_period=None,                    # None = all periods
    output_file='forecast_all.dat',
    perform_downsampling=True
)

print(f"Total periods: {converter.num_periods}")
print(f"Total cumulative rate: {all_data['RATE'].sum():.6f}")
```

### 4. PyCSEP Integration

```python
# Convert to PyCSEP GriddedForecast object
from datetime import datetime

period_data = converter.convert_period(period=1)

# Calculate time range
start_date, end_date = converter.calculate_period_dates(
    period=1,
    start_year=2012,
    period_length_months=3  # 3-month periods
)

# Create PyCSEP forecast
forecast = converter.to_pycsep_forecast(
    data=period_data,
    start_date=start_date,
    end_date=end_date,
    name='EEPAS_2012_Q1'
)

print(f"Forecast name: {forecast.name}")
print(f"Time range: {forecast.start_time} - {forecast.end_time}")
print(f"Expected events: {forecast.event_count:.2f}")
```

### 5. Time Period Calculation

```python
# 3-month periods
for period in range(1, 5):
    start, end = converter.calculate_period_dates(
        period=period,
        start_year=2012,
        period_length_months=3
    )
    print(f"Period {period}: {start.date()} - {end.date()}")

# Output:
# Period 1: 2012-01-01 - 2012-04-01
# Period 2: 2012-04-01 - 2012-07-01
# Period 3: 2012-07-01 - 2012-10-01
# Period 4: 2012-10-01 - 2013-01-01

# 1-year periods
for period in range(1, 4):
    start, end = converter.calculate_period_dates(
        period=period,
        start_year=2012,
        period_length_months=12
    )
    print(f"Year {period}: {start.date()} - {end.date()}")
```

---

## 🔧 Advanced Usage

### Custom Grid Resolution

```python
# Use 0.05° × 0.05° sub-grids instead of 0.1°
converter.convert_period(
    period=1,
    output_file='forecast_fine.dat',
    perform_downsampling=True,
    grid_resolution=0.05  # Finer resolution
)
```

### Disable Coordinate Transformation

```python
# If grid file already contains lat/lon coordinates
converter = EEPASForecastConverter(
    forecast_file='forecast.mat',
    grid_file='grid_latlon.mat',
    coordinate_transform=False  # Skip transformation
)
```

### Process Subset of Periods

```python
# Only process periods 1-10
converter.convert_all_periods(
    start_period=1,
    end_period=10,
    output_file='forecast_p1_10.dat'
)
```

### Export Without Downsampling

```python
# Keep original coarse grid
converter.convert_period(
    period=1,
    output_file='forecast_coarse.dat',
    perform_downsampling=False  # No spatial downsampling
)
```

---

## 📊 Output Format

### PyCSEP ASCII Format

The output file follows PyCSEP's standard format:

```
LON_0   LON_1   LAT_0   LAT_1   Z_0   Z_1   MAG_0   MAG_1   RATE   FLAG
```

Example:
```
6.5	6.6	45.0	45.1	0.0	30.0	5.0	5.1	1.0000e-05	1
6.5	6.6	45.0	45.1	0.0	30.0	5.1	5.2	9.0000e-06	1
6.5	6.6	45.0	45.1	0.0	30.0	5.2	5.3	8.0000e-06	1
```

### Column Descriptions

| Column | Description | Unit |
|--------|-------------|------|
| LON_0 | Minimum longitude | degrees |
| LON_1 | Maximum longitude | degrees |
| LAT_0 | Minimum latitude | degrees |
| LAT_1 | Maximum latitude | degrees |
| Z_0 | Minimum depth | km |
| Z_1 | Maximum depth | km |
| MAG_0 | Minimum magnitude | Mw |
| MAG_1 | Maximum magnitude | Mw |
| RATE | Expected number of events | count |
| FLAG | Status flag (1 = active) | - |

---

## 🔍 Common Use Cases

### Case 1: Prepare Forecasts for PyCSEP Evaluation

```python
from analysis.forecast_converter import EEPASForecastConverter
import csep
from csep.utils import time_utils

# 1. Convert EEPAS forecast
eepas_converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_EEPAS_2012_2022.mat',
    grid_file='CELLE_ter.mat'
)
eepas_converter.convert_all_periods(
    output_file='eepas_forecast.dat'
)

# 2. Convert PPE forecast (baseline)
ppe_converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_PPE_2012_2022.mat',
    grid_file='CELLE_ter.mat'
)
ppe_converter.convert_all_periods(
    output_file='ppe_forecast.dat'
)

# 3. Load as PyCSEP forecasts
start_date = time_utils.strptime_to_utc_datetime('2012-01-01 00:00:00.0')
end_date = time_utils.strptime_to_utc_datetime('2022-12-31 23:59:59.0')

eepas_fc = csep.load_gridded_forecast(
    'eepas_forecast.dat',
    start_date=start_date,
    end_date=end_date,
    name='EEPAS'
)

ppe_fc = csep.load_gridded_forecast(
    'ppe_forecast.dat',
    start_date=start_date,
    end_date=end_date,
    name='PPE'
)

print(f"EEPAS expected events: {eepas_fc.event_count:.2f}")
print(f"PPE expected events: {ppe_fc.event_count:.2f}")
```

### Case 2: Quarterly Forecast Visualization

```python
import matplotlib.pyplot as plt

converter = EEPASForecastConverter(
    forecast_file='PREVISIONI_3m_EEPAS_2012_2022.mat',
    grid_file='CELLE_ter.mat'
)

# Generate forecasts for first 4 quarters of 2012
for quarter in range(1, 5):
    # Convert period
    data = converter.convert_period(
        period=quarter,
        output_file=f'forecast_2012_Q{quarter}.dat'
    )

    # Calculate dates
    start, end = converter.calculate_period_dates(quarter, 2012, 3)

    # Convert to PyCSEP
    forecast = converter.to_pycsep_forecast(
        data=data,
        start_date=start,
        end_date=end,
        name=f'EEPAS_2012_Q{quarter}'
    )

    # Plot (requires cartopy)
    ax = forecast.plot(
        extent=[6, 19, 35, 48],  # Italy extent
        plot_args={'title': f'EEPAS Forecast: 2012 Q{quarter}'}
    )
    plt.savefig(f'forecast_2012_Q{quarter}.png', dpi=300)
    plt.close()
```

### Case 3: Compare EEPAS vs PPE

```python
# Convert both forecasts
eepas = EEPASForecastConverter(
    'PREVISIONI_3m_EEPAS_2012_2022.mat',
    'CELLE_ter.mat'
).convert_all_periods()

ppe = EEPASForecastConverter(
    'PREVISIONI_3m_PPE_2012_2022.mat',
    'CELLE_ter.mat'
).convert_all_periods()

# Compare total rates
print(f"EEPAS total rate: {eepas['RATE'].sum():.6f}")
print(f"PPE total rate: {ppe['RATE'].sum():.6f}")

# Spatial comparison
import numpy as np

# Merge on spatial-magnitude bins
merged = eepas.merge(
    ppe,
    on=['LON_0', 'LAT_0', 'MAG_0'],
    suffixes=('_eepas', '_ppe')
)

# Calculate rate ratio
merged['rate_ratio'] = merged['RATE_eepas'] / merged['RATE_ppe']

print(f"Mean rate ratio: {merged['rate_ratio'].mean():.3f}")
print(f"Median rate ratio: {merged['rate_ratio'].median():.3f}")
```

---

## ⚠️ Important Notes

### 1. Time Period Handling

EEPAS forecasts are typically for **3-month periods**:
- Period 1 = 2012 Q1 (Jan-Mar)
- Period 2 = 2012 Q2 (Apr-Jun)
- Period 3 = 2012 Q3 (Jul-Sep)
- Period 4 = 2012 Q4 (Oct-Dec)
- Period 5 = 2013 Q1, etc.

For **annual forecasts**, set `period_length_months=12`.

### 2. Coordinate Systems

**Italy forecasts** use:
- Source: RDN2008 (EPSG:7794) - Italian national projection
- Target: WGS84 (EPSG:4326) - Standard lat/lon

**Taiwan forecasts** may already be in lat/lon, so use `coordinate_transform=False`.

### 3. Spatial Downsampling

The downsampling algorithm:
1. Divides each coarse grid into 0.1° × 0.1° candidate sub-grids
2. Checks if sub-grid centroid falls within coarse grid bounds
3. Evenly distributes the coarse grid's RATE among valid sub-grids

This ensures:
- Conservation of total rate
- Proper handling of irregular grid boundaries
- PyCSEP compatibility (0.1° resolution)

### 4. Memory Usage

Processing all periods for large forecasts may use significant memory:
- **Single period**: ~100 MB
- **All periods** (40 periods): ~4 GB

For limited memory, process periods individually.

---

## 🐛 Troubleshooting

### Problem: "No module named 'pyproj'"

**Solution**: Install pyproj
```bash
pip install pyproj
```

### Problem: "No module named 'csep'"

**Solution**: Install PyCSEP
```bash
pip install pycsep
```

### Problem: Coordinate transformation fails

**Solution**: Check CRS codes
```python
# For Taiwan (if already in lat/lon)
converter = EEPASForecastConverter(
    ...,
    coordinate_transform=False
)

# For Italy with different projection
converter = EEPASForecastConverter(
    ...,
    source_crs='EPSG:XXXX',  # Check your projection
    target_crs='EPSG:4326'
)
```

### Problem: Wrong number of periods detected

**Solution**: Check MATLAB file structure
```python
import scipy.io as sio
mat = sio.loadmat('forecast.mat')
print(mat.keys())  # Check variable names
print(mat['PREVISIONI_3m'].shape)  # Should be (periods × mag_bins, regions + 1)
```

### Problem: Output file is too large

**Solution**: Disable downsampling for testing
```python
converter.convert_period(
    period=1,
    perform_downsampling=False  # Keep coarse grid
)
```

---

## 📚 API Reference

### Class: `EEPASForecastConverter`

#### Methods

| Method | Description |
|--------|-------------|
| `extract_period(period_idx)` | Extract specific period data |
| `spatial_downsampling(data, grid_resolution=0.1)` | Downsample to fine grid |
| `aggregate_overlaps(data)` | Aggregate duplicate grid points |
| `convert_period(...)` | Convert single period to PyCSEP |
| `convert_all_periods(...)` | Convert and sum all periods |
| `export_csep_format(data, output_file)` | Export to ASCII file |
| `to_pycsep_forecast(...)` | Create GriddedForecast object |
| `calculate_period_dates(...)` | Calculate period time range |

#### Properties

| Property | Description |
|----------|-------------|
| `forecast_data` | Loaded forecast matrix |
| `cell_bounds` | Grid boundaries DataFrame |
| `magnitude_bins` | List of (mag_min, mag_max) tuples |
| `num_periods` | Number of time periods |
| `num_regions` | Number of spatial regions |

### Function: `convert_eepas_forecast`

Convenience function for quick conversion.

```python
convert_eepas_forecast(
    forecast_file,      # Path to forecast .mat file
    grid_file,          # Path to grid .mat file
    output_file,        # Output PyCSEP file
    period=None,        # Period number (None = all)
    **kwargs            # Additional parameters
)
```

---

## 📖 References

- **PyCSEP Documentation**: https://docs.cseptesting.org/
- **PyProj Documentation**: https://pyproj4.github.io/pyproj/
- **EEPAS Paper**: Biondini et al. (2023) GJI

---

**Author**: EEPAS Development Team
**Last Updated**: 2025-11-26
**Version**: 1.0.0
