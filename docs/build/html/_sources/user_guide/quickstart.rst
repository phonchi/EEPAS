Quick Start Guide
=================

This guide will help you get started with EEPAS earthquake forecasting using the Italy dataset as a tutorial example.

Prerequisites
-------------

- Python 3.8 or higher
- 8GB RAM (16GB recommended)
- Linux, macOS, or Windows with WSL

Installation
------------

1. **Install Dependencies**

   .. code-block:: bash

      pip install numpy scipy numba pandas h5py matplotlib

2. **Verify Installation**

   .. code-block:: bash

      python3 -c "import numpy, scipy, numba, pandas, h5py; print('✅ All dependencies installed')"

3. **Navigate to Project Directory**

   .. code-block:: bash

      cd /path/to/EEPAS/src/python_src

Tutorial Example: Italy Workflow (5 Steps)
-------------------------------------------

This tutorial demonstrates the complete EEPAS workflow using the Italy earthquake catalog as an example. The same workflow can be adapted to any seismic region by preparing appropriate configuration files and data.

**Step 1: PPE Learning**

Learn background seismicity parameters using the Italy configuration:

.. code-block:: bash

   python3 ppe_learning.py --config config_italy_causal_ew0_rerun.json

**Output**: ``results_italy/Fitted_par_PPE_1990_2012.csv``

- ``a``: Background seismicity rate
- ``d``: Spatial decay parameter (km)
- ``s``: Uniform background rate

.. note::
   For your own region, create a custom config file following the same structure as ``config_italy_causal_ew0_rerun.json``

**Step 2: Aftershock Parameters**

Calibrate short-term exclusion parameters with mT magnitude anchoring:

.. code-block:: bash

   python3 fit_aftershock_params.py --config config_italy_causal_ew0_rerun.json --ppe-ref-mag mT --target-mag mT

**Output**: ``results_italy/Fitted_par_aftershock_1990_2012.csv``

- ``v``: Independent event proportion
- ``k``: Aftershock normalization constant

.. tip::
   The ``--ppe-ref-mag mT`` option anchors the magnitude distribution at the target magnitude, improving model stability.

**Step 3: EEPAS Learning**

Learn EEPAS model parameters with automatic boundary adjustment and three-stage optimization:

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py \
       --config config_italy_causal_ew0_rerun.json \
       --three-stage \
       --ppe-ref-mag mT \
       --max-rounds 1

**Output**: ``results_italy/Fitted_par_EEPAS_1990_2012.csv``

- 9 parameters: ``am, bm, Sm, at, bt, St, ba, Sa, u``
- Three-stage optimization improves convergence
- Automatic boundary adjustment ensures parameter validity

.. note::
   The ``--three-stage`` option uses a sequential optimization strategy that first optimizes subsets of parameters before joint optimization, leading to better convergence.

**Step 4: PPE Forecast**

Generate PPE background seismicity forecast:

.. code-block:: bash

   python3 ppe_make_forecast.py --config config_italy_causal_ew0_rerun.json --ppe-ref-mag mT

**Output**: ``results_italy/PREVISIONI_3m_PPE_2012_2022.mat``

**Step 5: EEPAS Forecast**

Generate complete EEPAS forecast:

.. code-block:: bash

   python3 eepas_make_forecast.py --config config_italy_causal_ew0_rerun.json --ppe-ref-mag mT

**Output**: ``results_italy/PREVISIONI_3m_EEPAS_2012_2022.mat``

.. note::

   Fast mode (trapezoidal integration) is used by default. Use ``--accurate`` for verification only (significantly slower with < 0.004% difference).

See :doc:`workflows` for applying EEPAS to your own region and :doc:`configuration` for detailed configuration guide.

Verifying Results
-----------------

**Check PPE Results**:

.. code-block:: bash

   cat results_italy_causal_ew0/Fitted_par_PPE_1990_2012.csv

Expected output:

.. code-block:: text

   a,d,s,ln_likelihood
   0.616,29.64,1e-15,-514.10

**Check EEPAS Results**:

.. code-block:: bash

   cat results_italy_causal_ew0/Fitted_par_EEPAS_1990_2012.csv

Expected output:

.. code-block:: text

   am,bm,Sm,at,bt,St,ba,Sa,u,ln_likelihood
   1.234,1.000,0.242,2.588,0.349,0.150,0.504,1.000,0.167,-495.39

**Validate Forecast Lambda Sum**:

.. code-block:: bash

   python3 analysis/analyze_forecast_lambda.py

This verifies that the forecast rate density integrates to approximately the observed event count.

Next Steps
----------

- **Detailed Workflows**: See :doc:`workflows` for advanced usage
- **Configuration Guide**: See :doc:`configuration` for all configuration options
- **Results Interpretation**: See :doc:`results` for understanding output files
- **API Reference**: See :doc:`../api_reference/index` for programmatic usage

Performance Tips
----------------

- Fast mode is used by default for forecasting (significantly faster)
- Use ``--max-rounds 3`` for EEPAS learning
- See :doc:`workflows` for advanced optimization options

Resources
---------

- **Full Documentation**: :doc:`../index`
- **Configuration Reference**: :doc:`configuration`
- **API Documentation**: :doc:`../api_reference/index`
- **Changelog**: :doc:`../development/changelog`
