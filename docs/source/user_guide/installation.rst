Installation Guide
==================

System Requirements
-------------------

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 8GB RAM (16GB+ recommended for large datasets)
- **Disk Space**: ~500MB for dependencies + data storage

Quick Installation
------------------

.. code-block:: bash

   # Clone repository
   git clone https://github.com/your-repo/EEPAS.git
   cd EEPAS/src/EEPAS

   # Install core dependencies (required)
   pip install numpy scipy pandas h5py numba joblib

   # Install optional dependencies (recommended)
   pip install pyproj jupyter matplotlib cartopy

   # Verify installation
   python3 -c "import numpy, scipy, numba, joblib; print('✓ Core installation successful')"

Dependencies Overview
---------------------

EEPAS dependencies are categorized by usage:

.. list-table::
   :header-rows: 1
   :widths: 20 30 15 35

   * - Category
     - Package
     - Status
     - Purpose
   * - **Core**
     - numpy, scipy, pandas
     - Required
     - Scientific computing
   * - **Core**
     - h5py
     - Required
     - MATLAB file I/O
   * - **Core**
     - numba
     - Required
     - JIT acceleration
   * - **Core**
     - joblib
     - Required
     - Parallel computing
   * - **Geospatial**
     - pyproj
     - Optional
     - Coordinate transformation (Italy)
   * - **Analysis**
     - jupyter, matplotlib
     - Optional
     - Interactive notebooks
   * - **Analysis**
     - SeismoStats
     - Optional
     - b-value estimation
   * - **Analysis**
     - pycsep
     - Optional
     - Forecast evaluation
   * - **Analysis**
     - cartopy
     - Optional
     - Map visualization
   * - **Documentation**
     - sphinx, sphinx_book_theme
     - Optional
     - Build docs

Core Dependencies (Required)
-----------------------------

These packages are **essential** for running EEPAS:

Scientific Computing Stack
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   numpy>=1.21.0          # Array operations, linear algebra
   scipy>=1.7.0           # Optimization (minimize, dblquad)
   pandas>=1.3.0          # DataFrame operations, CSV I/O
   h5py>=3.0.0            # MATLAB .mat file support

**Used in**: All scripts (``ppe_learning.py``, ``eepas_learning.py``, ``*_forecast.py``)

**Installation**:

.. code-block:: bash

   pip install "numpy>=1.21" "scipy>=1.7" "pandas>=1.3" "h5py>=3.0"

Performance Libraries
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   numba>=0.54.0          # JIT compilation for likelihood functions
   joblib>=1.0.0          # Parallel processing for optimization

**Used in**:
- ``numba``: :func:`eepas_likelihood`, :func:`neg_log_like_aftershock`, :func:`utils.numerical_integration`
- ``joblib``: :func:`optimize_eepas_parameters` (multi-start search)

**Installation**:

.. code-block:: bash

   pip install "numba>=0.54" "joblib>=1.0"

**Performance Impact**:
- ``numba`` provides **10-100x** speedup for likelihood calculations
- ``joblib`` enables parallel optimization (3x faster for multi-start)

Optional Dependencies
---------------------

Geospatial Tools
^^^^^^^^^^^^^^^^

.. code-block:: text

   pyproj>=3.0.0          # Coordinate system transformations

**Used in**: :mod:`utils.coordinate_transform` (coordinate system transformations)

**When needed**: For converting seismic data between coordinate systems (WGS84 → RDN2008, TWD97, etc.)

**Installation**:

.. code-block:: bash

   pip install pyproj

Analysis & Visualization (Notebooks)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Required for running Jupyter notebooks in ``analysis/``:

.. code-block:: text

   jupyter>=1.0.0         # Interactive notebook environment
   matplotlib>=3.5.0      # Plotting and visualization
   SeismoStats>=0.5.0     # b-value estimation (Utsu, B-positive)
   pycsep>=0.6.0          # Forecast evaluation (N-test, M-test)
   cartopy>=0.20.0        # Geospatial plotting
   tqdm>=4.60.0           # Progress bars
   decimal-time           # Datetime to decimal year conversion

**Used in**:
- ``Estimate_mc_b_Italy_clean.ipynb``: b-value analysis (SeismoStats)
- ``Examine_Psi_Italy_clean.ipynb``: Parameter optimization visualization
- ``earth_viz_Italy_clean.ipynb``: Map plotting (cartopy), forecast evaluation (pycsep)

**Installation**:

.. code-block:: bash

   # Visualization basics
   pip install jupyter matplotlib tqdm

   # Seismology-specific (may require additional steps)
   pip install SeismoStats pycsep cartopy decimal-time

.. note::
   **Cartopy Installation**: May require system libraries (GEOS, PROJ). See
   `Cartopy installation guide <https://scitools.org.uk/cartopy/docs/latest/installing.html>`_.

Documentation Building
^^^^^^^^^^^^^^^^^^^^^^

Required only for building Sphinx documentation:

.. code-block:: text

   sphinx>=4.0.0          # Documentation generator
   sphinx_book_theme      # Theme for HTML docs
   myst-parser            # Markdown support in Sphinx

**Installation**:

.. code-block:: bash

   cd docs
   pip install -r requirements.txt
   make html

Complete Installation Scenarios
--------------------------------

Minimal (Core Functionality Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For running EEPAS learning and forecasting only:

.. code-block:: bash

   pip install numpy scipy pandas h5py numba joblib

**Use case**: Headless servers, production environments

Italy Dataset (Minimal + Geospatial)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install numpy scipy pandas h5py numba joblib pyproj

**Use case**: Working with CPTI/HORUS Italian catalogs

Full Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For development, analysis, and documentation:

.. code-block:: bash

   # Core dependencies
   pip install numpy scipy pandas h5py numba joblib pyproj

   # Analysis tools
   pip install jupyter matplotlib SeismoStats pycsep cartopy tqdm decimal-time

   # Documentation
   cd docs && pip install -r requirements.txt

Verification
------------

Test Core Installation
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   python3 << 'EOF'
   import numpy as np
   import scipy
   import pandas as pd
   import h5py
   import numba
   import joblib
   print("✓ All core dependencies installed successfully")
   print(f"  NumPy: {np.__version__}")
   print(f"  SciPy: {scipy.__version__}")
   print(f"  Pandas: {pd.__version__}")
   print(f"  Numba: {numba.__version__}")
   EOF

Test EEPAS Functionality
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Test data loading
   python3 -c "from utils.data_loader import DataLoader; print('✓ Data loader OK')"

   # Test JIT compilation
   python3 -c "from eepas_likelihood import eepas_likelihood; print('✓ Numba JIT OK')"

   # Test basic workflow
   python3 ppe_learning.py --config config.json --help

Test Optional Tools
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Test pyproj (geospatial)
   python3 -c "import pyproj; print('✓ PyProj available')" || echo "✗ PyProj not installed"

   # Test SeismoStats (b-value)
   python3 -c "import SeismoStats; print('✓ SeismoStats available')" || echo "✗ SeismoStats not installed"

   # Test pycsep (evaluation)
   python3 -c "import csep; print('✓ PyCSEP available')" || echo "✗ PyCSEP not installed"

Troubleshooting
---------------

Numba Installation Issues
^^^^^^^^^^^^^^^^^^^^^^^^^^

If Numba fails to install:

.. code-block:: bash

   # Try installing llvmlite first
   pip install llvmlite
   pip install numba

Cartopy Installation Issues
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cartopy requires GEOS and PROJ system libraries:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install libgeos-dev libproj-dev
   pip install cartopy

   # macOS (Homebrew)
   brew install geos proj
   pip install cartopy

   # Conda (recommended for Cartopy)
   conda install -c conda-forge cartopy

PyCSEP Installation
^^^^^^^^^^^^^^^^^^^

PyCSEP may have specific version requirements:

.. code-block:: bash

   pip install pycsep>=0.6.0

   # If issues persist, check compatibility:
   # https://github.com/SCECcode/pycsep

Import Errors
^^^^^^^^^^^^^

If you encounter ``ModuleNotFoundError``:

1. Verify Python version: ``python3 --version`` (must be ≥3.8)
2. Check installation: ``pip list | grep <package>``
3. Ensure correct Python environment (venv/conda)

See Also
--------

- :doc:`quickstart` - Quick start guide
- :doc:`workflows` - Complete workflow examples
- :doc:`configuration` - Configuration file format
