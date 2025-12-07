# Data Directory

**Version 0.1**

This directory contains earthquake catalogs, spatial grid definitions, and supporting datasets used by the code.
## Earthquake Catalogs

### Primary Catalog
Download here https://drive.google.com/drive/folders/170WNb8M8PQJDX1B2JSQYfqj4ad80TC0U?usp=sharing

## Spatial Grid Definitions

### `CELLE_ter.mat` - Forecast Grid System
- **Purpose**: Defines spatial cells for earthquake rate forecasting
- **Resolution**: Variable resolution optimized for Taiwan's seismic zones
- **Coordinate Reference**: WGS84 with bounds in decimal degrees
- **Cell Count**: 177 primary regions subdivided into fine-scale forecast cells

### `CPTI11.mat` - Reference Spatial Framework
- **Source**: **NOT USED**. Italian Parametric Earthquake Catalog (CPTI11) spatial framework

## Data Processing Notes

### Coordinate Systems
- **Input Data**: WGS84 geographic coordinates (degrees)
- **Processing**: RDN2008 projected coordinates (meters)
- **Conversion**: Use `src/utils/coordinate_transform.py` for accurate transformations

For detailed column specifications and usage examples, see the main README.md file in the repository root.

## File Format Specifications

### Input Data Formats


**`HORUS.mat` (MATLAB format):**
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
| 10 | Local magnitude | ML |

**`CELLE_ter.mat` (Spatial grid definition):**
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
Row Block 1 (Period 1):  [Period_ID, Rate_Region1, Rate_Region2, ..., Rate_Region6] for M5.0-5.1
Row Block 1 (Period 1):  [Period_ID, Rate_Region1, Rate_Region2, ..., Rate_Region6] for M5.1-5.2
...
Row Block 1 (Period 1):  [Period_ID, Rate_Region1, Rate_Region2, ..., Rate_Region6] for M7.4-7.5

Row Block 2 (Period 2):  [Same structure for next 3-month period]
...
```

For detailed analysis workflows and visualization examples, see the main repository README.md and the analysis notebook.

### Detailed Matrix Specifications

**EEPAS Forecast Files** (`PREVISIONI_3m_EEPAS_*.mat`):
- **Variable Name**: `PREVISIONI_3m_less` 
- **Matrix Dimensions**: N×7 where N = number_of_periods × 25
- **Row Structure**: Groups of 25 rows per forecast period
- **Magnitude Resolution**: 25 bins from M5.0-M7.5 (0.1 magnitude increments)
- **Spatial Resolution**: 6 primary Taiwan seismic regions
- **Column Structure**: 
  - Column 1: Period identifier (integer)
  - Columns 2-7: Earthquake rates per region per magnitude bin (decimal)

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
# 義大利（預設 RDN2008）
python src/utils/coordinate_transform.py \
  --horus-in data/HORUS_Italy.mat \
  --celle-in data/CELLE_ter.mat \
  --horus-out data/HORUS_Italy_RDN2008.mat \
  --celle-out data/CELLE_ter_RDN2008.mat

# 台灣（TWD97）
python src/utils/coordinate_transform.py \
  --horus-in data/HORUS_TW_A.mat \
  --celle-in data/CELLE_ter_TW.mat \
  --horus-out data/HORUS_TW_A_twd97.mat \
  --celle-out data/CELLE_ter_TW_twd97.mat \
  --target-crs twd97 \
  --region Taiwan
```

The output includes original coordinates plus transformed eastings/northings in kilometers.

