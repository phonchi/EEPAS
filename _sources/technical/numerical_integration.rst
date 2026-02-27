Numerical Integration
=====================

This document explains the numerical integration methods used in EEPAS and provides technical details on the fast vs accurate modes.

Overview
--------

EEPAS requires numerical integration at multiple stages:

1. **PPE Learning**: Spatial integration over testing region (baseline intensity)
2. **Aftershock Fitting**: Spatial integration for normalization (short-term exclusion calibration)
3. **EEPAS Learning**: Magnitude integration for precursory scaling kernels
4. **Forecasting**: Spatiotemporal integration for rate calculation (medium-term predictions)

Two integration modes are available:

- **FAST Mode**: Trapezoidal rule / midpoint rule (default, recommended)
- **ACCURATE Mode**: scipy.dblquad / scipy.quad_vec (for verification only)

Integration Methods
-------------------

PPE Spatial Integration
^^^^^^^^^^^^^^^^^^^^^^^^

**Mathematical Problem**

Calculate the spatial background rate:

.. math::

   \Lambda_{\text{PPE}} = \int \int_R \lambda_0(x,y) \, dx \, dy

where:

.. math::

   h_0(x,y) = \sum_{i: t_i < t - \text{delay}, m_i \geq m_T} \left[ \frac{a(m_i - m_T)}{\pi(d^2 + r_i^2)} + s \right]

- :math:`R`: Testing region (spatial domain)
- :math:`s`: Uniform background rate
- :math:`a`: Normalization factor
- :math:`d`: Smoothing parameter (characteristic distance)
- :math:`m_T`: Target magnitude threshold
- :math:`r_i^2 = (x-x_i)^2 + (y-y_i)^2`: Squared distance to event i

**Fast Mode: Grid-Based Trapezoidal Rule**

1. Create spatial grid over region R
2. Evaluate :math:`\lambda_0(x,y)` at grid points using ``fast_kernel_sum_2d``
3. Apply 2D trapezoidal rule

.. code-block:: python

   from utils.numerical_integration import fast_kernel_sum_2d, trapezoidal_2d
   import numpy as np

   # Step 1: Create grid (50x50)
   x = np.linspace(x_min, x_max, 50)
   y = np.linspace(y_min, y_max, 50)
   x_grid, y_grid = np.meshgrid(x, y)

   # Step 2: Calculate kernel sum (Numba parallelized)
   kernel_values = fast_kernel_sum_2d(x_grid, y_grid, d, xj, yj, weights)
   lambda_grid = s + kernel_values

   # Step 3: Integrate using trapezoidal rule
   integral_PPE = trapezoidal_2d(lambda_grid, x_grid, y_grid)

**Optimizations**:

- ``fast_kernel_sum_2d`` uses Numba JIT compilation with ``parallel=True``
- Multi-core parallelization across grid points
- ``fastmath=True`` for aggressive floating-point optimization


**Accurate Mode: scipy.dblquad**

.. code-block:: python

   from scipy.integrate import dblquad

   def integrand(y, x):
       val = 0.0
       for weight, xj, yj in event_data:
           denom = d**2 + (x - xj)**2 + (y - yj)**2
           val += a_coeff * weight / (np.pi * denom)
       val += s * s_coeff
       return val

   integral_PPE, error = dblquad(
       integrand,
       x_min, x_max,
       y_min, y_max,
       epsabs=1e-6,
       epsrel=1e-3
   )

EEPAS Magnitude Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Mathematical Problem**

Calculate magnitude-integrated triggering rate for normalization:

.. math::

   I_m = \int_{m_T}^{m_u} \frac{\eta(m_i) w_i}{\Delta(m)} g_i(m) \, dm

where:
   - :math:`g_i(m)`: Gaussian magnitude distribution :math:`\mathcal{N}(a_M + b_M m_i, \sigma_M^2)`
   - :math:`\Delta(m)`: Incompleteness correction factor
   - :math:`\eta(m_i)`: Magnitude-dependent scaling function
   - :math:`w_i`: Aftershock de-weighting factor

**Fast Mode: Midpoint Rule**

.. code-block:: python

   from utils.numerical_integration import fast_magnitude_integral

   # Midpoint rule with 20 points (Numba JIT)
   integral_mag = fast_magnitude_integral(
       m1=m_lower,
       m2=m_upper,
       mee=precursor_mags,
       am=am, bm=bm, Sm=Sm,
       m0=m0, B=B,
       magnitude_samples=20
   )

**Accurate Mode: scipy.quad_vec**

.. code-block:: python

   from utils.numerical_integration import magnitude_integral_accurate

   integral_mag, error = magnitude_integral_accurate(
       m1=m_lower,
       m2=m_upper,
       mee=precursor_mags,
       am=am, bm=bm, Sm=Sm,
       m0=m0, B=B
   )

Integration in Different Modules
---------------------------------

PPE Learning (ppe_learning.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Default**: ``--spatial-samples 50``

.. code-block:: bash

   # Fast mode (default: spatial grid 50×50)
   python3 ppe_learning.py --config config.json

   # Accurate mode (scipy.dblquad)
   python3 ppe_learning.py --config config.json --accurate

   # Custom grid resolution
   python3 ppe_learning.py --config config.json --spatial-samples 100

Aftershock Fitting (fit_aftershock_params.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Default**: ``--spatial-samples 50``

.. code-block:: bash

   # Fast mode (default: spatial grid 50×50)
   python3 fit_aftershock_params.py --config config.json

   # Accurate mode (scipy.dblquad)
   python3 fit_aftershock_params.py --config config.json --accurate

   # Custom grid resolution
   python3 fit_aftershock_params.py --config config.json --spatial-samples 100

EEPAS Learning (eepas_learning_auto_boundary.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Default**: ``--magnitude-samples 50``

.. code-block:: bash

   # Fast mode (default: 50 magnitude samples)
   python3 eepas_learning_auto_boundary.py --config config.json

   # Accurate mode (scipy.quad_vec)
   python3 eepas_learning_auto_boundary.py --config config.json --accurate

   # Custom number of samples
   python3 eepas_learning_auto_boundary.py --config config.json --magnitude-samples 100

PPE Forecast (ppe_make_forecast.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Default**: ``--spatial-samples 50``

.. code-block:: bash

   # Fast mode (default: spatial grid 50×50)
   python3 ppe_make_forecast.py --config config.json

   # Accurate mode (scipy.dblquad)
   python3 ppe_make_forecast.py --config config.json --accurate

   # Custom grid resolution
   python3 ppe_make_forecast.py --config config.json --spatial-samples 100

EEPAS Forecast (eepas_make_forecast.py)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Default**: ``--magnitude-samples 50``

.. code-block:: bash

   # Fast mode (default: 50 magnitude samples)
   python3 eepas_make_forecast.py --config config.json

   # Accurate mode (scipy.quad_vec)
   python3 eepas_make_forecast.py --config config.json --accurate

   # Custom number of samples
   python3 eepas_make_forecast.py --config config.json --magnitude-samples 100

Validation and Verification
----------------------------

Lambda Sum Validation
^^^^^^^^^^^^^^^^^^^^^

**Theory**: For a Poisson point process, the integral of the rate function equals the expected number of events:

.. math::

   \mathbb{E}[N] = \Lambda = \int \int \int \int \lambda(t,x,y,m) \, dt \, dx \, dy \, dm

**Validation Method**: Compare Lambda sum to observed event count

.. code-block:: python

   import scipy.io as sio
   import numpy as np

   # Load forecast (adjust path to your results directory)
   mat = sio.loadmat('results_italy_causal_ew0_rerun/PREVISIONI_3m_PPE_2012_2022.mat')
   forecast = mat['PREVISIONI_3m']

   # Calculate Lambda (EXCLUDE index column!)
   lambda_sum = np.sum(forecast[:, 1:])

   # Compare to observed events
   print(f'Lambda sum: {lambda_sum:.2f}')
   print(f'Observed events: {N_observed}')
   print(f'Ratio: {lambda_sum/N_observed:.2f}')

**Expected Result**: :math:`\Lambda / N \approx 1.0 \pm 0.2`

**Italy Example** (1990-2012 learning, 2012-2022 forecast):

.. code-block:: text

   PPE Lambda:     26.93
   EEPAS Lambda:   28.21
   Observed:       27

   PPE ratio:      0.997  ✅
   EEPAS ratio:    1.044  ✅

**Interpretation**:
   - < 0.8: Model under-forecasting (possible issues)
   - 0.8-1.2: Good calibration ✅
   - > 1.2: Model over-forecasting (possible issues)

Comparing Fast vs Accurate
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Tool**: ``analysis/analyze_forecast_lambda.py``

.. code-block:: bash

   # Run analysis
   python3 analysis/analyze_forecast_lambda.py

**Example Results** (Italy dataset, 1990-2012 learning period):

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20

   * - Parameter
     - Fast
     - Accurate
     - Rel. Diff
   * - a
     - 0.6161
     - 0.6161
     - < 0.001%
   * - d
     - 29.639
     - 29.639
     - < 0.001%
   * - s
     - 0.0
     - 0.0
     - N/A

**Tolerance**: Relative difference < 0.5% indicates excellent agreement between modes.

.. note::
   Values shown are from actual Italy dataset results (config_italy_causal_ew0).
   Your results may differ depending on your dataset and configuration.

Technical Implementation Details
---------------------------------

Numba JIT Compilation
^^^^^^^^^^^^^^^^^^^^^^

All fast integration functions use Numba's ``@jit`` decorator:

.. code-block:: python

   from numba import jit, prange
   import numpy as np

   @jit(nopython=True, parallel=True, fastmath=True, cache=True)
   def fast_kernel_sum_2d(x_grid, y_grid, d, xj, yj, weights):
       """Numba-accelerated kernel summation"""
       nx, ny = x_grid.shape
       result = np.zeros((nx, ny))

       for i in prange(nx):  # Parallel loop
           for j in range(ny):
               val = 0.0
               for k in range(len(xj)):
                   dx = x_grid[i, j] - xj[k]
                   dy = y_grid[i, j] - yj[k]
                   val += weights[k] / (np.pi * (d**2 + dx**2 + dy**2))
               result[i, j] = val

       return result

**Flags**:
   - ``nopython=True``: Pure machine code (no Python overhead)
   - ``parallel=True``: Multi-core parallelization
   - ``fastmath=True``: Aggressive floating-point optimizations
   - ``cache=True``: Cache compiled code between runs

Trapezoidal Rule Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   @jit(nopython=True, parallel=True, fastmath=True, cache=True)
   def trapezoidal_2d(f_values, dx, dy):
       """2D trapezoidal integration"""
       nx, ny = f_values.shape
       integral = 0.0

       # Sum over cells
       for i in prange(nx - 1):
           for j in range(ny - 1):
               # Trapezoidal rule: average of four vertices
               integral += 0.25 * (
                   f_values[i, j] +
                   f_values[i+1, j] +
                   f_values[i, j+1] +
                   f_values[i+1, j+1]
               )

       return integral * dx * dy

See Also
--------

- :doc:`../api_reference/utils` - API documentation for integration functions
- :doc:`../user_guide/workflows` - How to use different integration modes
- :doc:`optimization` - Optimization algorithms and strategies
