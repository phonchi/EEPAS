# Data Directory

**Version 0.2**

This directory contains earthquake catalogs, spatial grid definitions, and supporting datasets used by the EEPAS project.

## Earthquake Catalogs

### Primary Catalog
Download from: https://drive.google.com/drive/folders/170WNb8M8PQJDX1B2JSQYfqj4ad80TC0U?usp=sharing

### Italy Catalog
- **File**: `HORUS_Italy_RDN2008_polygon_filtered.mat`
- **Format**: HORUS format with RDN2008 coordinates
- **Coverage**: Italy seismic events (1990-2022)
- **Coordinate System**: RDN2008 (EPSG:6875)

### Taiwan Catalog
- **File**: `GDMScatalog_A_filtered_twd97.mat`
- **Format**: GDMS format with TWD97 coordinates
- **Coverage**: Taiwan seismic events
- **Coordinate System**: TWD97 (EPSG:3826)

## Spatial Grid Definitions

### Italy Testing Region
- **File**: `CELLE_ter.mat`
- **Purpose**: Defines spatial cells for earthquake rate forecasting
- **Resolution**: 177 grid cells covering Italy
- **Coordinate Reference**: WGS84 with bounds in decimal degrees

### Italy Neighborhood Region
- **File**: `CPTI15.mat`
- **Purpose**: Polygon boundary for source event region
- **Source**: Italian Parametric Earthquake Catalog (CPTI15) spatial framework
- **Usage**: Avoids boundary effects by including events outside testing region

### Taiwan Testing Region
- **File**: `CELLE_ter_TW_twd97_24regions_correct.mat`
- **Purpose**: 24-region grid system for Taiwan
- **Resolution**: 24 grid cells
- **Coordinate Reference**: TWD97 projected coordinates

## Data Processing Notes

### Coordinate Systems
- **Input Data**: WGS84 geographic coordinates (degrees)
- **Processing**:
  - Italy: RDN2008 projected coordinates (meters)
  - Taiwan: TWD97 projected coordinates (meters)
- **Conversion**: Use `utils/coordinate_transform.py` for accurate transformations

## File Format Specifications

### Earthquake Catalog Format

**HORUS/GDMS Catalog (.mat format):**
| Column | Description | Units |
|--------|-------------|-------|
| 1 | Year | YYYY |
| 2 | Month | 1-12 |
| 3 | Day | 1-31 |
| 4 | Hour | 0-23 (UTC) |
| 5 | Minute | 0-59 |
| 6 | Second | 0-59 |
| 7 | Latitude | °N |
| 8 | Longitude | °E |
| 9 | Depth | km |
| 10 | Magnitude | ML or Mw |

**Spatial Grid Definition (.mat format):**
| Column | Description | Units |
|--------|-------------|-------|
| 1 | Minimum longitude | °E |
| 2 | Maximum longitude | °E |
| 3 | Minimum latitude | °N |
| 4 | Maximum latitude | °N |
| 5-8 | Reserved (unused) | - |
| 9 | Cell identifier | integer |
| 10 | Reserved | - |

### Forecast Matrix Organization

Each forecast file contains earthquake rate predictions organized as:

```
Row Block 1 (Period 1):  [Period_ID, Rate_Cell1, Rate_Cell2, ..., Rate_CellN] for M5.0-5.1
Row Block 1 (Period 1):  [Period_ID, Rate_Cell1, Rate_Cell2, ..., Rate_CellN] for M5.1-5.2
...
Row Block 1 (Period 1):  [Period_ID, Rate_Cell1, Rate_Cell2, ..., Rate_CellN] for M7.4-7.5

Row Block 2 (Period 2):  [Same structure for next 3-month period]
...
```

### Detailed Matrix Specifications

**EEPAS Forecast Files** (`PREVISIONI_3m_EEPAS_*.mat`):
- **Variable Name**: `PREVISIONI_3m_less`
- **Matrix Dimensions**: N×(1+n_cells) where N = number_of_periods × 25
- **Row Structure**: Groups of 25 rows per forecast period
- **Magnitude Resolution**: 25 bins from M5.0-M7.5 (0.1 magnitude increments)
- **Spatial Resolution**: n_cells (177 for Italy, 24 for Taiwan)
- **Column Structure**:
  - Column 1: Period identifier (integer)
  - Columns 2 to (1+n_cells): Earthquake rates per cell per magnitude bin

**PPE Forecast Files** (`PREVISIONI_3m_PPE_*.mat`):
- **Variable Name**: `PREVISIONI_3m`
- **Structure**: Same format as EEPAS forecasts for direct comparison
- **Content**: Earthquake rates based on proximity to past earthquakes

### Parameter File Structure

**EEPAS Parameter Files** (`Fitted_par_EEPAS_*.csv`):
Contains optimized parameters including:
- Temporal decay parameters (at, bt, St)
- Spatial scaling factors (ba, Sa)
- Magnitude scaling constants (am, bm, Sm)
- Mixing weight parameter (u)
- Optimization metadata and convergence statistics

**PPE Parameter Files** (`Fitted_par_PPE_*.csv`):
Contains fitted parameters specific to the PPE model:
- Distance decay parameters (a, d)
- Temporal weighting factors (s)
- Regional scaling adjustments

**Aftershock Parameter Files** (`Fitted_par_aftershock_*.csv`):
Contains the aftershock model parameters:
- v: Weight parameter for PPE component
- k: Weight parameter for foreshock component
- Likelihood value and optimization metadata

## Coordinate System Conversion

Convert between coordinate systems using:

```bash
# Italy (RDN2008 default)
python3 utils/coordinate_transform.py \
  --horus-in data/HORUS_Italy.mat \
  --celle-in data/CELLE_ter.mat \
  --horus-out data/HORUS_Italy_RDN2008.mat \
  --celle-out data/CELLE_ter_RDN2008.mat

# Taiwan (TWD97)
python3 utils/coordinate_transform.py \
  --horus-in data/HORUS_TW_A.mat \
  --celle-in data/CELLE_ter_TW.mat \
  --horus-out data/HORUS_TW_A_twd97.mat \
  --celle-out data/CELLE_ter_TW_twd97.mat \
  --target-crs twd97 \
  --region Taiwan
```

The output includes original coordinates plus transformed eastings/northings in kilometers.

---

**Last Updated**: 2025-12-07
**Maintainer**: EEPAS Development Team
