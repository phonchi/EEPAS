.. PyEEPAS documentation master file

PyEEPAS — Bridging the Medium-Term Gap in Open-Source Statistical Earthquake Forecasting
=========================================================================================

**Version:** 0.5.0

**PyEEPAS** is the first open-source Python implementation of the EEPAS (Every Earthquake a Precursor According to Scale) model, built on a rigorous mathematical derivation of the likelihood function. It fills the medium-term gap in the open-source earthquake forecasting ecosystem — short-term has ETAS/STEP, long-term has OpenQuake, and now medium-term has PyEEPAS. The package provides a complete, reproducible framework demonstrated using the Italy earthquake catalog as a comprehensive example.

.. image:: https://img.shields.io/badge/version-0.5.0-blue.svg
   :alt: Version
   :target: https://github.com/phonchi/EEPAS

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :alt: Python Version
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :alt: License
   :target: https://opensource.org/licenses/MIT

Key Features
------------

🌍 **Universal Application**
   - Applicable to any seismic region worldwide
   - Tutorial examples using Italy earthquake data
   - Flexible configuration for different catalogs and spatial grids

🎯 **Complete EEPAS Implementation**
   - PPE Model: Baseline intensity in the absence of medium-term precursory build-up
   - EEPAS Precursory Component: Medium-term precursory scaling (magnitude, time, spatial)
   - Aftershock Parameters: Calibration for excluding short-term clustering effects

⚡ **Performance Optimized**
   - FAST mode: Trapezoidal rule integration (default, 1.75x faster)
   - ACCURATE mode: scipy.dblquad integration (< 0.2% difference)
   - Numba JIT compilation for critical paths

🔬 **Scientifically Validated**
   - Validated against Biondini et al. (2023) paper methodology
   - Comprehensive numerical integration verification (v0.3.0)

🚀 **Production Ready**
   - Automatic boundary adjustment for parameter optimization
   - Automated workflows for batch processing
   - Extensive documentation and examples

Latest Updates (v0.5.0)
-----------------------

**Documentation and Dual Validation Approach**

This release focuses on comprehensive documentation and validation:

- **Complete Sphinx Documentation**: User guide, API reference, technical docs, interactive examples
- **Dual Validation**: Reproduce published results + end-to-end automated pipeline
- **Archive Functionality**: Save workflow results for reproducibility
- **Bug Fixes**: Single-stage boundary adjustment, parameter hard caps

Previous Updates (v0.3.0)
--------------------------

**Numerical Integration Refactoring and Validation**

- **Unified Interface**: All numerical integration now uses ``utils/numerical_integration.py``
- **Dual Modes**: ACCURATE (scipy.dblquad) and FAST (trapezoidal rule)
- **Validation Results**: All parameter differences < 0.2% between modes
- **Performance**: FAST mode provides significant speedup, especially for forecasting

Quick Links
-----------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/quickstart
   user_guide/installation
   user_guide/workflows
   user_guide/configuration
   user_guide/results

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api_reference/index

.. toctree::
   :maxdepth: 2
   :caption: Examples and Tutorials

   examples/index

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   technical/mathematical_foundation
   technical/numerical_integration
   technical/optimization

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/changelog

Getting Started
---------------

For a quick introduction, see the :doc:`user_guide/quickstart` guide.

For detailed installation instructions, see :doc:`user_guide/installation`.

For complete workflow examples, see :doc:`user_guide/workflows`.

Scientific Background
---------------------

EEPAS is grounded in the **:math:`\Psi` phenomenon** - the empirical observation that most large earthquakes are preceded by increased seismicity in their source region. This precursory activity exhibits systematic scaling relationships:

.. math::

   \log_{10} T_p &= a_T + b_T M_p \\
   \log_{10} A_p &= b_A M_p \\
   M_m &= a_M + b_M M_p

where:
   - **T_p**: Precursor time (lead time to mainshock)
   - **A_p**: Precursor area (spatial extent)
   - **M_m**: Mainshock magnitude
   - **M_p**: Precursor magnitude

The EEPAS model treats **every earthquake as a potential precursor**, with contribution determined by these scaling relations.

Mathematical Framework
^^^^^^^^^^^^^^^^^^^^^^

The complete rate density combines two components:

.. math::

   \lambda(t,m,x,y) = \mu \lambda_0 + (1-\mu) \sum_i \eta(m_i) \frac{\lambda_i}{\Delta(m)}

where:
   - **μ**: Failure-to-predict rate (background proportion)
   - **λ₀**: PPE baseline (proximity to past earthquakes)
   - **λᵢ**: Precursor contribution from event i
   - **η(m)**: Magnitude-dependent scaling
   - **Δ(m)**: Catalog incompleteness correction

Each precursor contribution decomposes into:

.. math::

   \lambda_i(t,m,x,y) = w_i \cdot f_i(t) \cdot g_i(m) \cdot h_i(x,y)

with:
   - **f(t)**: Lognormal time distribution
   - **g(m)**: Gaussian magnitude distribution
   - **h(x,y)**: Bivariate Gaussian spatial distribution

For mathematical details and derivations, see :doc:`technical/mathematical_foundation`.

Example Application: Italy Dataset
-----------------------------------

This documentation demonstrates EEPAS using the Italy earthquake catalog:

**Spatial Configuration**
   - Testing Region: 177 grid cells covering Italy
   - Neighborhood Region: CPTI15 polygon (avoids boundary effects)
   - Demonstrates best practices for regional applications

**Temporal Configuration**
   - Learning Period: 1990-2011 (22 years)
   - Forecast Period: 2012-2021 (10 years)

**Model Parameters**
   - Catalog: CPTI15 (Parametric Catalog of Italian Earthquakes)
   - Completeness magnitude: m₀ = 2.45
   - Target magnitude: mT = 5.0

**Adapting to Other Regions**

To apply EEPAS to a different seismic region, you will need:
   1. Earthquake catalog in MATLAB .mat format (lon, lat, mag, time)
   2. Spatial grid definition for your testing region
   3. Neighborhood region definition (grid or polygon)
   4. Configuration file with appropriate time ranges and model parameters

See :doc:`user_guide/configuration` for detailed guidance on creating custom configurations.

Citation
--------

If you use PyEEPAS in your research, please cite:

.. code-block:: bibtex

   @article{pyeepas2026,
     title={PyEEPAS: Bridging the Medium-Term Gap in Open-Source Statistical Earthquake Forecasting},
     author={Chung, Szu-Chi and Cho, Chien-Hong and Wen, Strong},
     journal={Computers \& Geosciences},
     year={2026}
   }

Software Availability
---------------------

PyEEPAS is released under the MIT License. Source code, documentation, and
example configurations are available at https://github.com/phonchi/EEPAS.
The package requires Python 3.8+ with NumPy, SciPy, Numba, and joblib.

Support and Contributing
------------------------

- **Issues**: Report bugs at `GitHub Issues <https://github.com/phonchi/EEPAS/issues>`_
- **Discussions**: Ask questions at `GitHub Discussions <https://github.com/phonchi/EEPAS/discussions>`_
- **Contributing**: Contact the development team for contribution guidelines

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
