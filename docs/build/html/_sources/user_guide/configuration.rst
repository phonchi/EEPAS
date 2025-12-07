Configuration Reference
=======================

This guide provides a complete reference for all configuration file fields in EEPAS.

Configuration File Structure
-----------------------------

EEPAS uses JSON configuration files to control all aspects of the forecasting workflow. A configuration file consists of several main sections:

.. code-block:: text

   {
     "dataDir": "data",
     "resultsDir": "results_italy",
     "catalogStartYear": 1960,
     "learnStartYear": 1990,
     "learnEndYear": 2012,
     "forecastStartYear": 2012,
     "forecastEndYear": 2022,
     "inputFiles": { ... },
     "outputFiles": { ... },
     "optimization": { ... },
     "modelParams": { ... }
   }

Directory and File Paths
-------------------------

Base Directories
^^^^^^^^^^^^^^^^

.. py:data:: dataDir
   :type: string
   :value: "data"

   Directory containing input data files (earthquake catalogs, region definitions).

   **Example**: ``"data"`` (relative path from working directory)

.. py:data:: resultsDir
   :type: string
   :value: "results"

   Directory where output files (fitted parameters, forecasts) will be saved.

   **Important**: Use different result directories for different configurations to avoid overwriting results.

   **Examples**:
      - ``"results"`` - Standard results
      - ``"results_italy"`` - Italy configuration
      - ``"results_refactor_test"`` - Testing new code

Time Range Configuration
-------------------------

.. py:data:: catalogStartYear
   :type: integer

   Starting year of the earthquake catalog. Events before this year are excluded.

   **Seismological Meaning**: Year when magnitude completeness is guaranteed (when seismic networks became reliable).

   **Example**:
      - Italy: ``1960`` (CPTI15 catalog completeness)

.. py:data:: learnStartYear
   :type: integer

   Starting year of the learning period.

   **Seismological Meaning**: Beginning of the training period for model parameter estimation.

   **Constraints**: ``learnStartYear >= catalogStartYear`` (need historical data before learning period)

   **Example**:
      - Italy: ``1990`` (30 years of history from 1960)

.. py:data:: learnEndYear
   :type: integer

   Ending year of the learning period (data included up to December 31 of the previous year).

   **Seismological Meaning**: End of training period. The learning period includes data up to the last day of (learnEndYear - 1). For example, learnEndYear: 2012 means data up to 2011/12/31, and the forecast starts from 2012/01/01.

   **Example**:
      - Italy: ``2012`` (learning period: 1990-2011, 22 years of data)

.. py:data:: forecastStartYear
   :type: integer

   Starting year of the forecast period.

   **Standard Practice**: ``forecastStartYear == learnEndYear`` (forecast begins immediately after learning period)

.. py:data:: forecastEndYear
   :type: integer

   Ending year of the forecast period.

   **Example**:
      - Italy: ``2022`` (10-year forecast horizon)

Input Files
-----------

The ``inputFiles`` section specifies the earthquake catalog and spatial region files.

.. py:data:: inputFiles.catalogFile
   :type: string

   Earthquake catalog file (MATLAB .mat format).

   **File Format**:

   MATLAB .mat file containing a matrix variable (N_events × 10):

   .. code-block:: text

      Column 1-6:  Date/time (Year, Month, Day, Hour, Minute, Second)
      Column 7:    Latitude (degrees N)
      Column 8:    Longitude (degrees E)
      Column 9:    Depth (km)
      Column 10:   Magnitude

   **Variable Name**: Flexible (e.g., ``HORUS``, ``catalog``, ``GDMScatalog``)

   **Tutorial Example** (Italy):
      - File: ``HORUS_Italy_RDN2008_polygon_filtered.mat``
      - Variable: ``HORUS`` (438,192 × 10 matrix)
      - Optional: ``column_names`` array

   **Your Region**: Create .mat file with same column structure, any variable name

   **Old Name**: ``horusFile`` (deprecated, still supported)

.. py:data:: inputFiles.neighborhoodRegionFile
   :type: string

   Neighborhood region definition - source events come from this region (larger area to avoid edge effects).

   **File Format**:

   **Option 1: Grid format** (same as testing region, N_cells × 10 matrix)

   **Option 2: Polygon format** (N_vertices × 2 or N_vertices × 4 matrix)

   .. code-block:: text

      Column 1-2: (lon, lat) coordinates of polygon vertices
      Column 3-4: (optional) projected coordinates

   **Important**: Vertices must be in **clockwise order** with no repetitions.

   **Tutorial Example** (Italy):
      - File: ``CPTI15.mat``
      - Variable: ``cpti15`` (15 × 4 matrix, polygon)
      - Covers Italy and surroundings (larger than testing region)

   **Simple Alternative**: Use same file as testingRegionFile (grid)

   **Old Name**: ``cptiFile`` (deprecated)

.. py:data:: inputFiles.testingRegionFile
   :type: string

   Testing region definition - spatial extent for likelihood calculation and forecasting (integration domain).

   **File Format**:

   MATLAB .mat file containing grid matrix (N_cells × 10):

   .. code-block:: text

      Column 1-4:  Grid bounds (lon_min, lon_max, lat_min, lat_max)
      Column 5-8:  Reserved/unused
      Column 9:    Cell identifier (integer)
      Column 10:   Reserved

   **Only columns 1-4 are used** for defining rectangular grid cells.

   **Variable Name**: Flexible (e.g., ``CELLESD``, ``CELLE_ter_TW``)

   **Tutorial Example** (Italy):
      - File: ``CELLE_ter.mat``
      - Variable: ``CELLESD`` (177 × 10 matrix)
      - 177 grid cells covering Italy land area

   **Relationship**: Testing Region should be ⊆ Neighborhood Region (to avoid boundary effects)

   **Old Name**: ``celleFile`` (deprecated)

Output Files
------------

The ``outputFiles`` section specifies filename patterns for results. Use ``%d_%d`` placeholders for year ranges.

.. py:data:: outputFiles.PPEParamPattern
   :type: string
   :value: "Fitted_par_PPE_%d_%d.csv"

   Output filename pattern for PPE parameters (a, d, s).

   **Generated File Example**: ``Fitted_par_PPE_1990_2012.csv``

   **File Content**:
      .. code-block:: text

         a,d,s,ln_likelihood
         0.616,29.64,0.0,-514.10

.. py:data:: outputFiles.AftershockParamPattern
   :type: string
   :value: "Fitted_par_aftershock_%d_%d.csv"

   Output filename pattern for aftershock parameters (v, k).

   **Generated File Example**: ``Fitted_par_aftershock_1990_2012.csv``

   **File Content**:
      .. code-block:: text

         v,k,ln_likelihood
         0.577,0.205,-429.26

.. py:data:: outputFiles.EEPASParamPattern
   :type: string
   :value: "Fitted_par_EEPAS_%d_%d.csv"

   Output filename pattern for EEPAS parameters (am, Sm, at, bt, St, ba, Sa, u).

   **Generated File Example**: ``Fitted_par_EEPAS_1990_2012.csv``

.. py:data:: outputFiles.PPEForecastPattern
   :type: string

   Output filename pattern for PPE forecast files (.mat format).

   **Example**:
      - Italy: ``"PREVISIONI_3m_PPE_%d_%d.mat"`` (177 cells)

.. py:data:: outputFiles.EEPASForecastPattern
   :type: string

   Output filename pattern for EEPAS forecast files (.mat format).

   **Example**:
      - Italy: ``"PREVISIONI_3m_EEPAS_%d_%d.mat"``

Optimization Configuration
---------------------------

The ``optimization`` section defines the three-stage optimization strategy for EEPAS parameter learning.

Stage 1: Primary Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "stage1": {
     "parameters": ["am", "at", "Sa", "u"],
     "initialValues": [1.5, 1.5, 2.0, 0.2],
     "lowerBounds": [1.0, 1.0, 1.0, 0.0],
     "upperBounds": [2.0, 3.0, 30.0, 1.0],
     "fixedValues": {
       "bm": 1.0,
       "Sm": 0.32,
       "bt": 0.4,
       "St": 0.23,
       "ba": 0.35
     }
   }

**Parameters Optimized**:
   - ``am``: Magnitude intercept
   - ``at``: Time intercept
   - ``Sa``: Spatial uncertainty parameter
   - ``u``: EEPAS/PPE mixing ratio

**Fixed Parameters**: ``bm = 1.0``, ``Sm``, ``bt``, ``St``, ``ba``

Stage 2: Optimize Sm, bt, St, ba, u
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "stage2": {
     "parameters": ["Sm", "bt", "St", "ba", "u"],
     "initialValues": [0.32, 0.4, 0.23, 0.35, "u_from_stage1"],
     "lowerBounds": [0.2, 0.3, 0.15, 0.2, 0.0],
     "upperBounds": [0.65, 0.65, 0.6, 0.6, 1.0]
   }

**Parameters Optimized**:
   - ``Sm``: Magnitude uncertainty (standard deviation)
   - ``bt``: Time scaling exponent
   - ``St``: Time uncertainty (standard deviation)
   - ``ba``: Spatial scaling exponent
   - ``u``: EEPAS/PPE mixing ratio

**Fixed Parameters**: ``am``, ``at``, ``Sa`` from Stage 1, and ``bm = 1.0``

**Purpose**: Optimize uncertainty parameters using Stage 1 results as initial values.

Stage 3: Joint Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   "stage3": {
     "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
     "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.075, 0.2, 0.5, 0.0],
     "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
     "fixedValues": {"bm": 1.0}
   }

**Parameters Optimized**: All 8 parameters jointly.

**Fixed Parameter**: Only ``bm`` (magnitude exponent) remains fixed.

**Purpose**: Final joint optimization using Stage 1 and Stage 2 results as initial values.

Model Parameters
----------------

The ``modelParams`` section contains physical model constants and configuration flags.

Physical Constants
^^^^^^^^^^^^^^^^^^

.. py:data:: modelParams.delay
   :type: integer
   :value: 50

   Time delay (days) to exclude high aftershock activity period before each target event.

   **Usage**: Only events occurring ≥ delay days before target event are considered as potential precursors/sources.

   **Seismological Meaning**: Excludes immediate aftershock period to avoid interference.

   **Standard Value**: 50 days

.. py:data:: modelParams.B
   :type: float
   :value: 1.084

   Magnitude scaling parameter β = b_GR × ln(10), where b_GR is the Gutenberg-Richter b-value.

   **Formula**: B = b_GR × 2.302585

.. py:data:: modelParams.m0
   :type: float
   :value: 2.45

   Completeness magnitude - minimum magnitude guaranteed to be detected.

.. py:data:: modelParams.mT
   :type: float
   :value: 5.0

   Target magnitude threshold - minimum magnitude to forecast.

   **Requirement**: mT > m0

Aftershock Model Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:data:: modelParams.delta
   :type: float
   :value: 0.7

   Bath's law offset - minimum magnitude difference between mainshock and aftershock.

   **Condition**: Aftershock magnitude m_aftershock ≤ m_mainshock - δ

   **Standard Value**: δ = 0.7

.. py:data:: modelParams.p
   :type: float
   :value: 1.2

   Omori law exponent - controls temporal decay rate of aftershocks.

   **Formula**: f'(t) ∝ (Δt + c)^(-p), where Δt = time since mainshock

   **Standard Value**: p = 1.2

.. py:data:: modelParams.c
   :type: float
   :value: 0.03

   Omori law offset parameter (days) - prevents singularity at Δt=0.

   **Standard Value**: c = 0.03 days

.. py:data:: modelParams.sigmaU
   :type: float
   :value: 0.006

   Utsu spatial relationship parameter for aftershock distribution.

   **Formula**: σ = sigmaU × √(10^m_mainshock), where σ is spatial standard deviation

   **Standard Value**: 0.006

Configuration Flags
^^^^^^^^^^^^^^^^^^^

.. py:data:: modelParams.weightFlag
   :type: integer
   :value: 0 or 1

   Earthquake weighting scheme.

   **Values**:
      - ``0``: Equal weights (all earthquakes weighted equally)
      - ``1``: Causal weighting (time-dependent weights)

   **Standard**: Use ``1`` for causal EEPAS.

.. py:data:: modelParams.useCausalEW
   :type: integer
   :value: 0 or 1

   Controls how E(w) (expected aftershock weight) is calculated during EEPAS learning.

   **Values**:
      - ``0``: Use global E(w) computed from all events in learning period
      - ``1``: For each target event, compute E(w) using only events before that event (causal)

   **Default**: ``0`` (standard approach)

.. py:data:: modelParams.useRollingUpdate
   :type: boolean
   :value: true or false

   Controls how historical data is updated during PPE forecasting.

   **Values**:
      - ``true``: Each forecast window uses all earthquakes up to that time (rolling update)
      - ``false``: All forecast windows use fixed historical data from forecast start (static snapshot)

   **Default**: ``true``

Forecast Parameters
^^^^^^^^^^^^^^^^^^^

.. py:data:: modelParams.forecastPeriodDays
   :type: float
   :value: 91.31

   Length of each forecast time window (days).

   **Standard Value**: 91.31 days ≈ 3 months (quarterly forecasts)

Configuration Examples
-----------------------

Tutorial Configuration (Italy)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../../config_italy.json
   :language: json
   :caption: config_italy.json (Tutorial Example)

This configuration demonstrates best practices and can serve as a template for your own region.

Creating Variations
^^^^^^^^^^^^^^^^^^^

**Different Completeness Magnitude**:

.. code-block:: json

   {
     "resultsDir": "results_yourregion_m30",
     "modelParams": {
       "m0": 3.0
     }
   }

**Different Time Periods**:

.. code-block:: json

   {
     "resultsDir": "results_yourregion_2000_2015",
     "learnStartYear": 2000,
     "learnEndYear": 2015,
     "forecastStartYear": 2015,
     "forecastEndYear": 2025
   }

**Different Catalog**:

.. code-block:: json

   {
     "resultsDir": "results_yourregion_declustered",
     "inputFiles": {
       "catalogFile": "your_catalog_declustered.mat"
     }
   }

Creating Custom Configurations
-------------------------------

Step 1: Copy Tutorial Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Copy Italy tutorial configuration as template
   cp config_italy.json config_yourregion.json

Step 2: Modify Key Fields
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "resultsDir": "results_yourregion",
     "catalogStartYear": 1990,
     "learnStartYear": 2000,
     "learnEndYear": 2015,
     "forecastStartYear": 2015,
     "forecastEndYear": 2025,
     "inputFiles": {
       "catalogFile": "your_catalog.mat",
       "neighborhoodRegionFile": "your_region.mat",
       "testingRegionFile": "your_region.mat"
     },
     "modelParams": {
       "m0": 2.5,
       "mT": 5.0,
       "B": 1.036
     }
   }

Step 3: Validate Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   python3 -c "
   from utils.data_loader import DataLoader
   cfg = DataLoader.load_config('config_yourregion.json')
   print('Configuration valid!')
   print(f'Learning period: {cfg[\"learnStartYear\"]}-{cfg[\"learnEndYear\"]}')
   print(f'Results directory: {cfg[\"resultsDir\"]}')
   print(f'Completeness magnitude: {cfg[\"modelParams\"][\"m0\"]}')
   "

Best Practices
--------------

Result Directory Management
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Rule**: Always use unique result directories for different experiments.

.. code-block:: json

   // Good - Clear naming
   "resultsDir": "results_yourregion_2000_2015"
   "resultsDir": "results_italy_1990_2012"
   "resultsDir": "results_test_m30"

   // Bad - Overwriting risk
   "resultsDir": "results"  // Multiple configs using same directory!

Time Range Selection
^^^^^^^^^^^^^^^^^^^^

**Guidelines**:

1. **Catalog Start**: Choose year when magnitude completeness begins
2. **Learning Period**: Need sufficient events for parameter estimation (recommended: ≥10 years)
3. **Forecast Period**: Choose based on your validation needs

.. code-block:: json

   {
     "catalogStartYear": 1960,    // Completeness guaranteed
     "learnStartYear": 1990,       // 30 years of history available
     "learnEndYear": 2012,         // 22 years of learning data
     "forecastStartYear": 2012,    // Immediate forecast after learning
     "forecastEndYear": 2022       // 10 years forecast horizon
   }

**Warning**: If parameters consistently hit bounds during optimization, use ``--max-rounds 5`` to allow automatic boundary adjustment.

See Also
--------

- :doc:`workflows` - How to use configurations in complete workflows
- :doc:`results` - Interpreting output files
- :doc:`../api_reference/utils` - DataLoader API documentation
