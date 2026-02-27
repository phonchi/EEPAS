API Reference
=============

This section provides detailed API documentation for all EEPAS modules.

Module Organization
-------------------

EEPAS is organized into several functional groups:

**Core Modules** - Main workflow scripts
   The five main scripts that implement the EEPAS workflow:

   - :doc:`core` - PPE Learning, EEPAS Learning, Aftershock Fitting, Forecast Generation

**Utility Modules** - Support functions
   Helper modules for data loading, processing, and numerical operations:

   - :doc:`utils` - Data Loader, Catalog Processor, Region Manager, Numerical Integration

**Analysis Modules** - :math:`\Psi` phenomenon detection and scaling relations
   Tools for precursory scale increase analysis and parameter estimation:

   - :doc:`analysis` - :math:`\Psi` Detection, Deduplication, Scaling Relations, Dataset Tools

**Optimization Modules** - Parameter learning engines
   Internal optimization logic (called by core modules):

   - PPE Optimization
   - EEPAS Likelihood Calculation
   - Negative Log-Likelihood Functions

Quick Reference
---------------

.. list-table:: Core Functions by Task
   :widths: 30 35 35
   :header-rows: 1

   * - Task
     - Function
     - Module
   * - Learn PPE parameters
     - ``ppe_learning_tw_fast()``
     - :py:mod:`ppe_learning`
   * - Fit aftershock parameters
     - ``fit_aftershock_params_fast()``
     - :py:mod:`fit_aftershock_params`
   * - Learn EEPAS parameters
     - ``eepas_with_auto_boundary()``
     - :py:mod:`eepas_learning_auto_boundary`
   * - Generate PPE forecast
     - ``ppe_make_forecast()``
     - :py:mod:`ppe_make_forecast`
   * - Generate EEPAS forecast
     - ``eepas_make_forecast()``
     - :py:mod:`eepas_make_forecast`
   * - Load configuration
     - ``DataLoader.load_config()``
     - :py:mod:`utils.data_loader`
   * - Load catalog
     - ``DataLoader.load_catalogs()``
     - :py:mod:`utils.data_loader`
   * - Filter catalog
     - ``CatalogProcessor.filter_catalog()``
     - :py:mod:`utils.catalog_processor`

Common Usage Patterns
----------------------

Usage Examples
^^^^^^^^^^^^^^

.. code-block:: python

   from utils.data_loader import DataLoader
   from utils.catalog_processor import CatalogProcessor

   # Load configuration and data
   cfg = DataLoader.load_config('config_italy_reproduce.json')
   catalog = DataLoader.load_catalogs('config_italy_reproduce.json')

   # Filter catalog
   filtered = CatalogProcessor.filter_catalog(
       catalog, min_mag=2.45, start_year=1990, end_year=2012
   )

Detailed API Documentation
---------------------------

.. toctree::
   :maxdepth: 2

   core
   utils
   analysis

Module Index
------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
