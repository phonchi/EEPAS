Optimization Strategies
=======================

This document describes the optimization algorithms and strategies used in PyEEPAS parameter learning.

Overview
--------

EEPAS parameter learning involves finding parameters that minimize the negative log-likelihood (NLL):

.. math::

   \theta^* = \arg\min_{\theta} \text{NLL}(\theta | \text{data})

This is a challenging non-convex optimization problem with:

- **8 parameters** to optimize (EEPAS)
- **Strong parameter correlations**
- **Bounded constraints** (all parameters must be positive)
- **Computational cost** (varies by dataset size and configuration)

Optimization Modes
^^^^^^^^^^^^^^^^^^

PyEEPAS supports three optimization modes that can be auto-detected or explicitly specified:

1. **Single-Stage Optimization**: Optimize all 8 parameters simultaneously (define 8 parameters in stage1)
2. **Three-Stage Optimization**: Sequential optimization of parameter groups (define stage1/stage2/stage3)
3. **Custom Stages Optimization**: Define your own stages with full control (enableCustomStages=true)

**Mode Auto-Detection**:

- If ``enableCustomStages=true`` in config → Custom Stages mode
- If ``stage1`` has 8 parameters → Single-Stage mode
- If ``stage1`` has <8 parameters → Three-Stage mode
- Can override with ``--single-stage`` or ``--three-stage`` flags

Additional Features
^^^^^^^^^^^^^^^^^^^

1. **Multi-Start Optimization**: Multiple random starting points (enabled by default for Single/Three-Stage)
2. **Auto Boundary Adjustment**: Automatic detection and correction of boundary issues (all modes)

Optimization Algorithms
-----------------------

PyEEPAS supports three optimization algorithms:

fminsearchcon (Nelder-Mead with Constraints) - Default
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Algorithm**: Constrained Nelder-Mead simplex method

**Advantages**:
   - Derivative-free (robust to non-smooth functions)
   - Good for difficult landscapes
   - Handles constraints via transformation
   - More robust than gradient-based methods

**Disadvantages**:
   - Slower convergence
   - Higher computational cost

**Usage**:

.. code-block:: bash

   # Default optimizer (fminsearchcon)
   python3 eepas_learning_auto_boundary.py --config config.json

   # Explicit specification
   python3 eepas_learning_auto_boundary.py --config config.json --optimizer fminsearchcon

**Recommended For**: Standard use (default), debugging convergence issues

SLSQP (Sequential Least Squares Programming)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Algorithm**: Sequential quadratic programming with gradient approximation

**Advantages**:
   - Fast convergence for smooth problems
   - Handles bound constraints natively
   - Good for high-dimensional problems (8+ parameters)

**Disadvantages**:
   - May get stuck in local minima
   - Requires good initial guess

**Usage**:

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py --config config.json --optimizer SLSQP

**Recommended For**: Fast exploratory runs, smooth objective functions

L-BFGS-B (Limited-memory BFGS with Bounds)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Algorithm**: Quasi-Newton method with limited memory

**Advantages**:
   - Very efficient for large-scale problems
   - Good convergence properties
   - Low memory usage

**Disadvantages**:
   - Sensitive to initial guess
   - May struggle with highly correlated parameters

**Usage**:

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py --config config.json --optimizer L-BFGS-B

**Recommended For**: Quick exploratory runs

Single-Stage Optimization
--------------------------

**Strategy**: Optimize all 8 EEPAS parameters simultaneously in one step

.. math::

   \min_{\theta} \text{NLL}(a_m, S_m, a_t, b_t, S_t, b_a, S_a, u)

**Advantages**:
   - Simpler conceptually
   - No parameter fixing decisions needed
   - One optimization run
   - Multi-start enabled by default for robustness

**Disadvantages**:
   - May struggle with parameter correlations
   - More sensitive to initial guess
   - Higher risk of local minima (mitigated by multi-start)

Configuration
^^^^^^^^^^^^^

**New Format** (Recommended):

Define all 8 parameters directly in ``stage1`` - this is automatically detected as single-stage:

.. code-block:: json

   "optimization": {
     "stage1": {
       "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
       "initialValues": [1.5, 0.32, 1.5, 0.4, 0.23, 0.35, 2.0, 0.2],
       "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.15, 0.2, 1.0, 0.0],
       "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
       "fixedValues": {"bm": 1.0}
     }
   }

**Old Format** (Still Supported):

.. code-block:: json

   "optimization": {
     "stage3": {
       "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
       "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.075, 0.2, 0.5, 0.0],
       "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
       "fixedValues": {"bm": 1.0}
     }
   }

Usage
^^^^^

.. code-block:: bash

   # Auto-detected single-stage (when stage1 has 8 parameters)
   python3 eepas_learning_auto_boundary.py --config config.json

   # Explicit single-stage (forces single-stage even with three-stage config)
   python3 eepas_learning_auto_boundary.py --config config.json --single-stage

   # Disable multi-start (faster but less robust)
   python3 eepas_learning_auto_boundary.py --config config.json --no-multistart

Output Example
^^^^^^^^^^^^^^

Single-stage optimization outputs iteration-by-iteration progress similar to Stage 3:

.. code-block:: text

   🔄 Optimizing all 8 parameters jointly
      Initial values: am=1.50, Sm=0.32, at=1.50, bt=0.40, St=0.23, ba=0.35, Sa=2.00, u=0.20
      Starting optimization...
      Iteration   10: NLL = 505.234...
      Iteration   20: NLL = 498.567...
      ...
      Iteration  150: NLL = 495.395...

      ✅ Optimization completed
      Final NLL: 495.394994

.. note::
   Actual output format and NLL values depend on your dataset and optimizer settings.

Three-Stage Optimization
-------------------------

**Strategy**: Sequentially optimize parameter groups to reduce correlation issues

**Motivation**:
   - Some parameters are highly correlated (e.g., am and Sm)
   - Optimizing correlated groups separately improves convergence
   - Matches the methodology in Biondini et al. (2023) paper

Stage Sequence
^^^^^^^^^^^^^^

**Stage 1**: Primary Parameters
   Optimize: ``am``, ``at``, ``Sa``, ``u``

   Fix: ``bm``, ``Sm``, ``bt``, ``St``, ``ba``

   **Purpose**: Establish magnitude and time scaling, initial mixing ratio

**Stage 2**: Optimize Sm, bt, St, ba, u
   Optimize: ``Sm``, ``bt``, ``St``, ``ba``, ``u``

   Fix: ``bm``, ``am`` (from Stage 1), ``at`` (from Stage 1), ``Sa`` (from Stage 1)

   **Purpose**: Refine variance and slope parameters, re-optimize mixing ratio

**Stage 3**: Joint Optimization
   Optimize: All 8 parameters simultaneously

   Fix: Only ``bm``

   Initial values: Results from Stages 1-2

   **Purpose**: Fine-tune all parameters jointly for best global fit

Mathematical Formulation
^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

   \text{Stage 1:} \quad \min_{a_m, a_t, S_a, u} \text{NLL}(\theta_1 | \theta_{\text{fixed}}^{(1)})

   \text{Stage 2:} \quad \min_{S_m, b_t, S_t, b_a, u} \text{NLL}(\theta_2 | \theta_{\text{fixed}}^{(2)})

   \text{Stage 3:} \quad \min_{\theta_{\text{all}}} \text{NLL}(\theta | b_m = \text{const})

Configuration
^^^^^^^^^^^^^

Three-stage uses all three optimization sections:

.. code-block:: json

   "optimization": {
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
     },
     "stage2": {
       "parameters": ["Sm", "bt", "St", "ba", "u"],
       "initialValues": [0.32, 0.4, 0.23, 0.35, "u_from_stage1"],
       "lowerBounds": [0.2, 0.3, 0.15, 0.2, 0.0],
       "upperBounds": [0.65, 0.65, 0.6, 0.6, 1.0]
     },
     "stage3": {
       "parameters": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
       "lowerBounds": [1.0, 0.2, 1.0, 0.3, 0.075, 0.2, 0.5, 0.0],
       "upperBounds": [2.0, 0.65, 3.0, 0.65, 0.6, 0.6, 30.0, 1.0],
       "fixedValues": {"bm": 1.0}
     }
   }

Usage
^^^^^

.. code-block:: bash

   # Auto-detected three-stage (when stage1 has fewer than 8 parameters)
   python3 eepas_learning_auto_boundary.py --config config.json

   # Explicit three-stage
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage

   # Disable multi-start (not recommended for three-stage)
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage --no-multistart

Output Example
^^^^^^^^^^^^^^

The following shows the typical three-stage optimization output structure (values are illustrative):

.. code-block:: text

   🔄 Stage 1: Optimize am, at, Sa, u
      Fixed parameters: bm=1.00, Sm=0.32, bt=0.40, St=0.23, ba=0.35
      Initial values: am=1.50, at=1.50, Sa=2.00, u=0.20
      Starting optimization...
      Iteration    1: NLL = 512.478407, am=1.5000, at=1.5000, Sa=2.0000, u=0.200000
      Iteration   10: NLL = 500.347721, am=1.5734, at=2.0433, Sa=1.7267, u=0.210678
      ...
      Iteration  320: NLL = 496.456507, am=1.1310, at=2.3899, Sa=1.8725, u=0.172587

      ✅ Stage 1 completed
      Best values: am=1.131021, at=2.389865, Sa=1.872489, u=0.172587
      Stage NLL: 496.456507

   🔄 Stage 2: Optimize Sm, bt, St, ba, u
      🎯 Using multi-start search (3 starting points) + Stage 3 quick evaluation
      Starting point 1/3: Sm=0.32, bt=0.40, St=0.23, ba=0.35, u=0.17
      → Stage 2 NLL=495.805945, Sm=0.309
      → Stage 3 quick evaluation NLL=495.406852
      ...
      ✅ Stage 2 completed
      Best values: Sm=0.309224, bt=0.398886, St=0.150000, ba=0.360706, u=0.185882
      Stage objective value: 495.805945

   🔄 Stage 3: Joint optimization of all parameters
      Initial values: [1.13, 0.31, 2.39, 0.40, 0.15, 0.36, 1.87, 0.19]
      Starting optimization...
      Iteration   10: NLL = 500.314676
      Iteration   20: NLL = 497.985286
      ...
      Iteration  180: NLL = 495.397577

      ✅ Stage 3 completed
      Final NLL: 495.394994

.. note::
   Parameter values shown are illustrative examples. Actual values depend on your dataset.

**Performance Comparison**:

Three-stage optimization provides better convergence than single-stage.

Auto Boundary Adjustment
-------------------------

**Problem**: Parameters may converge to constraint boundaries, indicating:

1. Bounds are too restrictive (need expansion)
2. True optimum is at boundary (need tighter bounds)
3. Optimization got stuck (need different initial guess)

**Solution**: Automatically detect boundary touching and adjust bounds iteratively

Algorithm
^^^^^^^^^

.. code-block:: text

   For round = 1 to max_rounds:
       1. Run complete optimization (PPE → Aftershock → EEPAS)
       2. Check if Stage 3 parameters touch boundaries (within tolerance)
       3. If boundary touched:
          - If at lower bound: new_lower = current_lower / expansion_factor
          - If at upper bound: new_upper = current_upper × expansion_factor
          - Save adjusted config (with .bak backup)
          - Re-run entire optimization with new bounds
       4. If no boundaries touched OR round == max_rounds: Done ✓

Configuration
^^^^^^^^^^^^^

.. code-block:: bash

   python3 eepas_learning_auto_boundary.py \
       --config config.json \
       --max-rounds 3 \
       --tolerance 0.01 \
       --expansion 2.0

**Parameters**:

- ``--max-rounds N``: Maximum boundary adjustment iterations (default: 3)
- ``--tolerance TOL``: Boundary touching threshold (default: 0.01, i.e., 1%)
- ``--expansion FACTOR``: Boundary expansion factor (default: 2.0)

  - Lower bound adjustment: ``new_lower = current_lower / FACTOR``
  - Upper bound adjustment: ``new_upper = current_upper × FACTOR``
  - Example with default (2.0): lower 0.15 → 0.075, upper 30.0 → 60.0

**Boundary Detection**:

A parameter is considered "touching" if:

.. math::

   \frac{|\theta - \text{bound}|}{\text{bound}} < \text{tolerance}

Example: With tolerance=0.01, parameter St=0.150000 touches lower bound=0.15 because:

.. math::

   \frac{|0.150000 - 0.15|}{0.15} = 0.0000 < 0.01

Output Example
^^^^^^^^^^^^^^

.. code-block:: text

   ================================================================================
   Round 1 Optimization
   ================================================================================
   Using PPE reference magnitude: mT = 5.0
   ================================================================================
   EEPAS Model Parameter Learning - Numba Accelerated Version
   ================================================================================
   Config file: config_italy_causal_ew0_accurate.json
   Learning period: 1990 - 2012
   Completeness magnitude: m0=2.45

   ... [optimization process] ...

   ✅ This round optimization complete
      Final NLL = -495.406852

   Checking if Stage3 parameters hit boundaries...
      ⚠️  St=0.150000 near lower bound 0.150000 (distance ratio=0.0000)
      ⚠️  Sa=1.000000 near lower bound 1.000000 (distance ratio=0.0000)

   💡 Suggesting boundary adjustments (expansion factor = 2.0x):
      St lower bound: 0.150000 → 0.075000
      Sa lower bound: 1.000000 → 0.500000
      💾 Configuration backed up to: config_italy_causal_ew0_accurate.json.round1.bak
      ✅ Configuration file updated: config_italy_causal_ew0_accurate.json

   ================================================================================
   ⚠️  Maximum adjustment rounds (1) reached, stopping
      Current NLL = -495.406852
      Recommendation: Check if parameters still hit boundaries, may need manual further adjustment
   ================================================================================

Custom Stages Optimization
---------------------------

**Strategy**: Define your own custom optimization stages with full control over parameters, bounds, and progression

**When to Use**:

- You need more than 3 stages for better convergence
- Your dataset has specific characteristics requiring custom parameter grouping
- You want to implement advanced strategies like magnitude-first or conservative optimization
- You're researching different optimization approaches

Configuration
^^^^^^^^^^^^^

Enable custom stages in your config file:

.. code-block:: json

   "optimization": {
     "enableCustomStages": true,
     "customStages": [
       {
         "name": "magnitude",
         "optimize": ["am", "Sm"],
         "fix": {
           "bm": 1.0,
           "at": 2.0, "bt": 0.4, "St": 0.23,
           "ba": 0.35, "Sa": 10.0,
           "u": 0.5
         },
         "bounds": {
           "am": [1.0, 2.0],
           "Sm": [0.2, 0.65]
         }
       },
       {
         "name": "time",
         "optimize": ["at", "bt", "St"],
         "inherit": ["am", "Sm"],
         "fix": {
           "bm": 1.0,
           "ba": 0.35, "Sa": 10.0,
           "u": 0.5
         },
         "bounds": {
           "at": [1.0, 3.0],
           "bt": [0.3, 0.65],
           "St": [0.15, 0.6]
         }
       },
       {
         "name": "spatial_mixing",
         "optimize": ["ba", "Sa", "u"],
         "inherit": ["am", "Sm", "at", "bt", "St"],
         "fix": {"bm": 1.0},
         "bounds": {
           "ba": [0.2, 0.6],
           "Sa": [0.5, 30.0],
           "u": [0.0, 1.0]
         }
       },
       {
         "name": "joint",
         "optimize": ["am", "Sm", "at", "bt", "St", "ba", "Sa", "u"],
         "inherit": "all",
         "fix": {"bm": 1.0},
         "bounds": {
           "am": [1.0, 2.0],
           "Sm": [0.2, 0.65],
           "at": [1.0, 3.0],
           "bt": [0.3, 0.65],
           "St": [0.15, 0.6],
           "ba": [0.2, 0.6],
           "Sa": [0.5, 30.0],
           "u": [0.0, 1.0]
         }
       }
     ]
   }

**Key Features**:

- ``optimize``: List of parameters to optimize in this stage
- ``inherit``: Parameters to inherit from previous stages (or "all")
- ``fix``: Parameters to fix at specified values
- ``bounds``: Custom bounds for each optimized parameter (optional)

Usage
^^^^^

.. code-block:: bash

   # Custom stages are auto-detected when enableCustomStages=true
   python3 eepas_learning_auto_boundary.py --config config_custom.json

**Important Notes**:

- Multi-start is **NOT supported** for custom stages
- Each stage runs once with the specified initial values
- Ensure parameter progression makes physical sense
- Test convergence carefully

Pre-defined Strategy Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Magnitude-First Strategy** (4 stages):

1. Magnitude parameters only (am, Sm)
2. Time parameters only (at, bt, St)
3. Spatial + mixing (ba, Sa, u)
4. Joint optimization

**Conservative Strategy** (5-6 stages):

1. Core scaling (am, at, Sa)
2. Magnitude uncertainty (Sm)
3. Time uncertainty (St)
4. Slopes (bt, ba)
5. Mixing (u)
6. Final joint tuning

Multi-Start Optimization
-------------------------

**Problem**: Non-convex objective may have multiple local minima

**Solution**: Run optimization from multiple random initial guesses and select best result

Algorithm
^^^^^^^^^

.. code-block:: python

   best_nll = +inf
   best_params = None

   for trial in range(n_multistart):
       # Generate random initial guess within bounds
       x0 = random_uniform(lower_bounds, upper_bounds)

       # Run optimization
       result = optimize(objective, x0, bounds)

       # Track best result
       if result.fun < best_nll:
           best_nll = result.fun
           best_params = result.x

   return best_params

Configuration
^^^^^^^^^^^^^

Multi-start is **enabled by default** in three-stage optimization.

**Parameters**:

- ``--no-multistart``: Disable multi-start (default: enabled)
- ``--n-starts N``: Number of starting points (default: 3, includes 1 config initial + (N-1) random perturbations)

.. code-block:: bash

   # Use default: 3 starting points (1 config initial + 2 random)
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage

   # Disable multi-start (single optimization run using config initial values)
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage --no-multistart

   # Custom number of starts (e.g., 1 config initial + 4 random)
   python3 eepas_learning_auto_boundary.py --config config.json --three-stage --n-starts 5

Output Example
^^^^^^^^^^^^^^

The following shows the typical multi-start optimization output structure:

.. code-block:: text

   🔄 Stage 2: Optimize Sm, bt, St, ba, u
      🎯 Using multi-start search (3 starting points) + Stage 3 quick evaluation
      Starting point 1/3: Sm=0.32, bt=0.40, St=0.23, ba=0.35, u=0.17
      → Stage 2 NLL=495.805945, Sm=0.309
      → Stage 3 quick evaluation NLL=495.406852
      Starting point 2/3: Sm=0.28, bt=0.58, St=0.28, ba=0.38, u=0.19
      → Stage 2 NLL=495.805945, Sm=0.309
      → Stage 3 quick evaluation NLL=495.406852
      Starting point 3/3: Sm=0.39, bt=0.30, St=0.34, ba=0.47, u=0.22
      → Stage 2 NLL=495.805945, Sm=0.309
      → Stage 3 quick evaluation NLL=495.406852
      ✨ Selected starting point 1: Stage 2 NLL=495.805945, Stage 3 evaluation NLL=495.406852
      ✅ Stage 2 completed
      Best values: Sm=0.309224, bt=0.398886, St=0.150000, ba=0.360706, u=0.185882
      Stage objective value: 495.805945

.. note::
   Multi-start optimization runs multiple trials and selects the best result.

Optimization Mode Comparison
-----------------------------

The following table compares the three optimization modes:

.. list-table:: Optimization Mode Comparison
   :header-rows: 1
   :widths: 20 25 25 30

   * - Feature
     - Single-Stage
     - Three-Stage
     - Custom Stages
   * - **Configuration**
     - Simple (stage1 only)
     - Medium (stage1/2/3)
     - Complex (custom stages)
   * - **Multi-Start**
     - ✅ Enabled by default
     - ✅ Enabled by default
     - ❌ Not supported
   * - **Convergence**
     - Medium
     - High
     - Depends on design
   * - **Speed**
     - Fast
     - Slower
     - Depends on # stages
   * - **Auto-Detection**
     - ✅ Yes (8 params in stage1)
     - ✅ Yes (<8 params in stage1)
     - ✅ Yes (enableCustomStages=true)
   * - **Recommended For**
     - Quick tests, large datasets
     - Standard use, robust results
     - Research, special datasets

Quick Start Guide
-----------------

**For most users** (recommended):

1. Use **Three-Stage** with default settings:

   .. code-block:: bash

      python3 eepas_learning_auto_boundary.py --config config.json --three-stage

2. If you have a good initial guess or very large dataset:

   .. code-block:: bash

      python3 eepas_learning_auto_boundary.py --config config_single.json

3. If you need custom parameter grouping:

   Create config with ``enableCustomStages: true`` and define custom stages.

Understanding NLL Values
-------------------------

**Higher NLL (less negative) is better.**

NLL magnitude depends on the number of events in the learning period.


See Also
--------

- :doc:`../api_reference/core` - API documentation for optimization modules
- :doc:`../user_guide/workflows` - Complete workflow examples with optimization
- :doc:`numerical_integration` - Integration methods used in likelihood calculation
- :doc:`../user_guide/configuration` - Configuration file optimization section
