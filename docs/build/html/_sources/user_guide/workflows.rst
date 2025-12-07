Complete Workflows
==================

This guide provides complete, step-by-step workflows for earthquake forecasting using EEPAS. The tutorial uses the Italy earthquake catalog as an example, but the same workflow can be applied to any seismic region.

Tutorial Example Workflow
--------------------------

Italy Earthquake Forecasting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tutorial demonstrates the complete EEPAS workflow using the Italy (CPTI15) earthquake catalog.

Overview
~~~~~~~~

This workflow demonstrates:
   - Magnitude anchoring with ``--ppe-ref-mag mT`` option
   - Three-stage optimization for complex parameter spaces
   - Handling larger spatial grids (177 cells)
   - Best practices for edge effect management (separate testing/neighborhood regions)

Step-by-Step Execution
~~~~~~~~~~~~~~~~~~~~~~~

**Step 1: PPE Learning**

.. code-block:: bash

   python3 ppe_learning.py --config config_italy.json

**Expected Output**:

.. code-block:: text

   Spatial region configuration:
     Testing Region: grid (177 cells)
     Neighborhood Region: polygon (CPTI15)
   PPE historical events (CatJ): 312, target events (CatI): 27

   ✅ Saved: results_italy/Fitted_par_PPE_1990_2012.csv
      a=0.616, d=29.64, s≈0

**Step 2: Aftershock Fitting**

.. code-block:: bash

   python3 fit_aftershock_params.py \
       --config config_italy.json \
       --ppe-ref-mag mT \
       --target-mag mT

**Expected Output**:

.. code-block:: text

   ✅ Saved: results_italy/Fitted_par_aftershock_1990_2012.csv
      v=0.577, k=0.205

**Step 3: EEPAS Learning**

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py \
       --config config_italy.json \
       --three-stage \
       --ppe-ref-mag mT \
       --max-rounds 1

**Expected Output**:

.. code-block:: text

   🔄 Stage 1: Optimize am, at, Sa, u
      Fixed parameters: bm=1.00, Sm=0.32, bt=0.40, St=0.23, ba=0.35
      ...
      ✅ Stage 1 completed

   🔄 Stage 2: Optimize Sm, bt, St, ba, u
      🎯 Using multi-start search (3 starting points) + Stage 3 quick evaluation
      ...
      ✅ Stage 2 completed

   🔄 Stage 3: Joint optimization of all parameters
      ...
      ✅ Stage 3 completed
      Final NLL: 495.394994

   ✅ Saved: results_italy_causal_ew0/Fitted_par_EEPAS_1990_2012.csv

**Step 4: PPE Forecast**

.. code-block:: bash

   python3 ppe_make_forecast.py \
       --config config_italy.json \
       --ppe-ref-mag mT

**Step 5: EEPAS Forecast**

.. code-block:: bash

   python3 eepas_make_forecast.py \
       --config config_italy.json \
       --ppe-ref-mag mT

Complete Italy Workflow Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Save as ``run_italy_workflow.sh``:

.. code-block:: bash

   #!/bin/bash
   # EEPAS Italy Workflow (Paper Validation)

   set -e

   echo "=== EEPAS Italy Workflow ==="
   echo "Configuration: config_italy.json"
   echo "Mode: Paper validation (mT anchor, 3-stage)"
   echo ""

   # Step 1: PPE Learning
   echo "Step 1/5: PPE Learning..."
   python3 ppe_learning.py --config config_italy.json

   # Step 2: Aftershock Parameters (mT anchor)
   echo "Step 2/5: Aftershock Parameters..."
   python3 fit_aftershock_params.py \
       --config config_italy.json \
       --ppe-ref-mag mT \
       --target-mag mT

   # Step 3: EEPAS Learning (3-stage, single round)
   echo "Step 3/5: EEPAS Learning (3-stage)..."
   python3 eepas_learning_auto_boundary.py \
       --config config_italy.json \
       --three-stage \
       --ppe-ref-mag mT \
       --max-rounds 1

   # Step 4: PPE Forecast
   echo "Step 4/5: PPE Forecast..."
   python3 ppe_make_forecast.py \
       --config config_italy.json \
       --ppe-ref-mag mT

   # Step 5: EEPAS Forecast (fast mode)
   echo "Step 5/5: EEPAS Forecast..."
   python3 eepas_make_forecast.py \
       --config config_italy.json \
       --ppe-ref-mag mT

   echo ""
   echo "=== Workflow Complete! ==="
   echo "Results saved in: results_italy/"
   ls -lh results_italy/

Applying to Your Region
------------------------

General Workflow Steps
^^^^^^^^^^^^^^^^^^^^^^

To apply EEPAS to your own seismic region, follow these steps:

**Prerequisites**

1. **Prepare Data Files**:

   - Earthquake catalog (.mat format):

     Variable name flexible (e.g., ``HORUS``, ``catalog``), matrix format (N_events × 10):

     .. code-block:: text

        Column 1-6:  Date/time (Year, Month, Day, Hour, Minute, Second)
        Column 7:    Latitude (degrees N)
        Column 8:    Longitude (degrees E)
        Column 9:    Depth (km)
        Column 10:   Magnitude

     See ``data/README.md`` for detailed format specification.

   - Testing region grid (.mat format):

     Variable name flexible (e.g., ``CELLESD``), matrix format (N_cells × 10):

     .. code-block:: text

        Column 1-4:  Grid bounds (lon_min, lon_max, lat_min, lat_max)
        Column 5-8:  Reserved/unused
        Column 9:    Cell identifier (integer)
        Column 10:   Reserved

     **Only columns 1-4 are used** for defining rectangular grid cells.

   - Neighborhood region (.mat format):

     **Grid format** (same as testing region): N_cells × 10 matrix

     **Polygon format**: N_vertices × 2 or N_vertices × 4 matrix

     .. code-block:: text

        Columns 1-2: (lon, lat) coordinates of polygon vertices
        Columns 3-4: (optional) projected coordinates

     **Important**: Polygon vertices must be in **clockwise order** with no repetitions. The neighborhood region must **strictly contain** the testing region to avoid boundary effects (truncation of precursor events outside R that may influence target events near the edge).

2. **Create Configuration File**:

   Copy ``config_italy.json`` and modify for your region:

   .. code-block:: text

      {
        "resultsDir": "results_yourregion",
        "catalogStartYear": YYYY,
        "learnStartYear": YYYY,
        "learnEndYear": YYYY,
        "forecastStartYear": YYYY,
        "forecastEndYear": YYYY,
        "inputFiles": {
          "catalogFile": "your_catalog.mat",
          "neighborhoodRegionFile": "your_neighborhood.mat",
          "testingRegionFile": "your_testing.mat"
        },
        "modelParams": {
          "m0": 2.5,
          "mT": 5.0,
          "B": 1.036
        }
      }

**Workflow Execution**

Run the same 5-step workflow with your configuration:

.. code-block:: bash

   # Step 1: PPE Learning
   python3 ppe_learning.py --config config_yourregion.json

   # Step 2: Aftershock Parameters
   python3 fit_aftershock_params.py \
       --config config_yourregion.json \
       --ppe-ref-mag mT \
       --target-mag mT

   # Step 3: EEPAS Learning (3-stage optimization)
   python3 eepas_learning_auto_boundary.py \
       --config config_yourregion.json \
       --three-stage \
       --ppe-ref-mag mT \
       --max-rounds 1

   # Step 4: PPE Forecast
   python3 ppe_make_forecast.py \
       --config config_yourregion.json \
       --ppe-ref-mag mT

   # Step 5: EEPAS Forecast
   python3 eepas_make_forecast.py \
       --config config_yourregion.json \
       --ppe-ref-mag mT

Batch Processing
^^^^^^^^^^^^^^^^

To process multiple configurations or scenarios:

.. code-block:: bash

   #!/bin/bash
   # Batch process multiple configurations

   CONFIGS=(
       "config_region1.json"
       "config_region2.json"
       "config_different_m0.json"
   )

   for config in "${CONFIGS[@]}"; do
       echo "========================================="
       echo "Processing: $config"
       echo "========================================="

       python3 ppe_learning.py --config "$config"
       python3 fit_aftershock_params.py --config "$config" --ppe-ref-mag mT --target-mag mT
       python3 eepas_learning_auto_boundary.py --config "$config" --three-stage --ppe-ref-mag mT --max-rounds 1
       python3 ppe_make_forecast.py --config "$config" --ppe-ref-mag mT
       python3 eepas_make_forecast.py --config "$config" --ppe-ref-mag mT

       echo "Completed: $config"
       echo ""
   done

   echo "All configurations processed!"

Advanced Workflows
------------------

Accurate Mode (Final Verification)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For publication or final verification, use accurate mode instead of fast mode:

.. code-block:: bash

   # PPE Learning (dblquad integration)
   python3 ppe_learning.py --config config.json --accurate

   # Aftershock Fitting (accurate mode)
   python3 fit_aftershock_params.py --config config.json --accurate

   # EEPAS Learning (accurate mode)
   python3 eepas_learning_auto_boundary.py --config config.json --accurate

   # PPE Forecast (accurate mode)
   python3 ppe_make_forecast.py --config config.json --accurate

   # EEPAS Forecast (accurate mode)
   python3 eepas_make_forecast.py --config config.json --accurate

.. warning::
   Accurate mode is **significantly slower** than fast mode, but provides < 0.2% difference in results.

Custom Magnitude Threshold
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Override completeness magnitude (m0):

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py \
       --config config.json \
       --m0 2.05

Custom Optimization Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adjust optimization behavior:

.. code-block:: bash

   # Increase maximum boundary adjustment rounds
   python3 eepas_learning_auto_boundary.py \
       --config config.json \
       --max-rounds 5 \
       --tolerance 0.01

   # Use specific optimizer
   python3 eepas_learning_auto_boundary.py \
       --config config.json \
       --no-multistart

Verification
------------

Verify Results
^^^^^^^^^^^^^^

After workflow completion, verify outputs exist:

.. code-block:: bash

   # Check all output files
   ls -lh results/Fitted_par_PPE_*.csv
   ls -lh results/Fitted_par_aftershock_*.csv
   ls -lh results/Fitted_par_EEPAS_*.csv
   ls -lh results/PREVISIONI_3m_PPE_*.mat
   ls -lh results/PREVISIONI_3m_EEPAS_*.mat

Check Parameter Values
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # PPE parameters
   cat results_yourregion/Fitted_par_PPE_*.csv

   # EEPAS parameters
   cat results_yourregion/Fitted_par_EEPAS_*.csv

Validate Forecast Lambda Sum
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the analysis tool to verify forecast correctness:

.. code-block:: bash

   python3 analysis/analyze_forecast_lambda.py

Next Steps
----------

- :doc:`configuration` - Customize configuration files
- :doc:`results` - Interpret forecast results
- :doc:`../api_reference/index` - API documentation

.. seealso::

   - :doc:`quickstart` - Quick introduction
   - :doc:`installation` - Installation guide
   - :doc:`../technical/numerical_integration` - Technical details
