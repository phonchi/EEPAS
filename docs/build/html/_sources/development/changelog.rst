Changelog
=========

All notable changes to this project are documented here.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Version 0.5.0 (2026-02-27)
--------------------------

PyEEPAS Branding and Documentation Overhaul

Added
^^^^^

**Formal Citation**

- Paper submitted to *Computers & Geosciences*: "PyEEPAS: Bridging the Medium-Term Gap in Open-Source Statistical Earthquake Forecasting"
- Authors: Szu-Chi Chung, Chien-Hong Cho, Strong Wen

Changed
^^^^^^^

**Branding**

- Project renamed from EEPAS to **PyEEPAS** throughout documentation
- Version bumped from 0.4.0 to 0.5.0

**Configuration Renaming**

- ``config_italy_causal_ew0_rerun.json`` → ``config_italy_reproduce.json``
- ``config_italy_target_m0.json`` → ``config_italy_endtoend.json``

**Function Renaming** (remove region-specific suffixes)

- ``ppe_learning_tw_fast()`` → ``ppe_learning_fast()``
- ``optimization_ppe_taiwan()`` → ``optimization_ppe()``

**Documentation Consolidation**

- USAGE_EN.md merged into README.md and deleted
- ``analysis/step7_verify_forecasts.py`` → ``analysis/verify_forecasts.py``

----

Version 0.4.0 (2025-12-11)
--------------------------

Documentation and Dual Validation Approach

Added
^^^^^

**Complete Sphinx Documentation**

- Comprehensive user guide (installation, quickstart, workflows, configuration, results)
- API reference documentation for all modules
- Technical documentation (mathematical foundation, numerical integration, optimization)
- Interactive examples (4 Jupyter notebooks)

**Interactive Example Notebooks**

- Automated Ψ phenomenon detection (``Examine_Psi_Italy_clean.ipynb``)
- PyCSEP evaluation - Reproduce paper results (``EEPAS_Forecast_Evaluation_New.ipynb``)
- PyCSEP evaluation - End-to-end pipeline (``EEPAS_Forecast_Evaluation_End_to_End.ipynb``)
- Catalog preprocessing with SeismoStats (``Estimate_mc_b_Italy_clean.ipynb``)

**Archive Functionality**

- ``archive_results.py`` - Archive workflow results for reproducibility
- Saves configuration snapshot, execution metadata, combined logs, and reproduction guide
- Integrated into workflow documentation

**Dual Validation Approach**

- **Reproduce Published Results**: ``config_italy_reproduce.json`` (originally named ``config_italy_causal_ew0_rerun.json``)
- **End-to-End Automated Pipeline**: ``config_italy_endtoend.json`` (originally named ``config_italy_target_m0.json``)

Changed
^^^^^^^

**Documentation Overhaul**

- README.md simplified (428 → 243 lines) and updated to v0.4.0
- USAGE_EN.md simplified (689 → 329 lines) focusing on essential workflows
- All documentation now references comprehensive Sphinx docs
- Version numbering adjusted (v1.x.0 → v0.x.0)

Fixed
^^^^^

**Single-Stage Mode Boundary Adjustment**

- Previously only worked with three-stage optimization (stage3)
- Now automatically detects single-stage mode and uses stage1 boundaries

**Parameter Hard Caps**

- Prevents unreasonable parameter expansion during boundary adjustment
- Caps: am≤4.5, at≤3.0, ba≤6.0, bt≤2.0, Sm/St/Sa≤2.0/1.0/2.0, u≤0.75

Validated
^^^^^^^^^

- **Reproduce Published Results**: Successfully replicates Biondini et al. (2023) within 1 hour
- **End-to-End Pipeline**: Achieves log-likelihood -483 (better than manual initialization)
- **PyCSEP Integration**: Passes all consistency tests (L-test, N-test, S-test, M-test)

----

Version 0.3.0 (2025-11-06)
--------------------------

Numerical Integration Refactoring and Validation

Added
^^^^^

**Numerical Integration Refactoring (Core Feature)**

- Unified numerical integration interface: ``utils/numerical_integration.py``
- Implemented ACCURATE mode (scipy.dblquad double integration)
- Implemented FAST mode (trapezoidal rule integration, default)
- All modules support ``--accurate`` parameter (fast mode is default)
- Complete ACCURATE vs FAST comparison report

**Numerical Integration Validation Results**

- Two causality settings tested: useCausalEW=0 (Fixed EW) and useCausalEW=1 (Dynamic EW)
- **All parameter relative differences < 0.2%**, validating sufficient trapezoidal rule precision
- PPE parameter difference < 0.001%
- EEPAS parameter difference < 0.16%
- Forecast Lambda difference < 0.004%

**Performance Benchmarking**

- FAST mode provides **significant speedup** (especially for forecast stage)
- **Recommended strategy**: Use FAST mode for daily research, ACCURATE mode for final paper validation

**Lambda Integration Validation Tools**

- Learning stage Λ_PPE validation: should approximate target event count N
- Forecast stage Lambda sum validation tool (``analysis/analyze_forecast_lambda.py``)
- Fixed index column handling issue, correctly calculates prediction rate sum
- **Validation results**:

  - Learning: Λ_PPE ≈ 27.00 (target 27 events) ✓
  - Forecast: PPE ~14 + EEPAS ~16 = ~30 (close to observed 27) ✓

**Automated Workflow Scripts**

- ``run_full_workflow_two_periods.sh`` - FAST mode dual causality setting complete workflow
- ``run_full_workflow_two_periods_accurate.sh`` - ACCURATE mode dual causality setting complete workflow
- ``run_causal_ew_comparison.sh`` - Causality weight comparison script
- Support for ``--no-boundary-adjustment`` parameter

Changed
^^^^^^^

**Core Module Updates**

- ``ppe_optimization.py`` - Support for ACCURATE/FAST mode switching
- ``eepas_likelihood.py`` - Unified use of numerical_integration module
- ``ppe_make_forecast.py`` - Support for ``--accurate`` parameter
- ``eepas_make_forecast.py`` - Support for ``--accurate`` parameter
- ``fit_aftershock_params.py`` - Support for ``--accurate`` parameter
- All numerical integration calls unified interface

**Documentation Updates**

- README.md updated to v0.3.0, emphasizing numerical integration validation achievements
- CHANGELOG.md detailed recording of refactoring process and validation results
- Configuration list updated (EW0/EW1 test configurations)

Fixed
^^^^^

- Fixed issue of not excluding index column when calculating Forecast Lambda
- Unified numerical integration calling method, eliminated duplicate code
- Improved EEPAS Learning boundary adjustment strategy

Validated
^^^^^^^^^

**Numerical Integration Refactoring Successfully Validated**

- Trapezoidal rule (FAST) and dblquad (ACCURATE) results highly consistent
- Parameter differences < 0.2% for all test configurations
- Lambda integration validation passed (Learning and Forecast stages)
- **Conclusion**: Refactored numerical integration implementation is correct, FAST mode can be safely used for daily research

Performance
^^^^^^^^^^^

FAST mode compared to ACCURATE mode:

- PPE Learning: ~1.3x speedup
- Aftershock Fitting: ~1.5x speedup
- EEPAS Learning: ~1.3x speedup
- PPE Forecast: ~4.0x speedup
- EEPAS Forecast: ~4.0x speedup
- **Overall**: ~1.75x speedup

----

Version 0.2.0 (2025-10-30)
--------------------------

Italy Mode Support and Paper Validation

Added
^^^^^

**Complete Italy Mode Support and Paper Validation**

- Testing Region and Neighborhood Region area management
- All modules support Italy earthquake data (PPE/EEPAS Learning/Forecast + Aftershock)
- Compliant with Biondini et al. (2023) Equation 1 mathematical definition
- **Paper Consistency Validation Completed**:

  - PPE and EEPAS forecast formulas fully consistent with paper
  - mT anchor support (``--ppe-ref-mag mT --target-mag mT``)
  - Single-round optimization mode (``--max-rounds 1``) matches paper methodology
  - Complete validation results in ``results_italy_paper_1round_full/`` (archived)

**Performance Optimization**

- PPE Forecast fast mode (Numba JIT): significantly faster with Numba acceleration, precision loss <0.03%
- EEPAS Forecast optimization: significant performance improvement with fast mode

**Complete Validation**

- Region implementation fully correct (source events, target events, integration range)
- Backward compatible with existing configurations
- Parameter results consistent with paper (1990-2012 learning period, 2012-2022 forecast period)

Changed
^^^^^^^

**Documentation Updates**

- README.md added paper validation workflow and latest achievements
- Added Italy quick start guide
- Updated directory structure description

Fixed
^^^^^

- Improved region filtering logic (Testing vs Neighborhood)
- Italy data loading and processing

Validated
^^^^^^^^^

- PPE Learning: a=0.616, d=29.64, s≈0 (mT=5.0 anchor)
- Aftershock parameters: v=0.577, k=0.205
- EEPAS parameters: NLL=-495.41 (8 parameters single-round optimization)
- Mathematical formula validation: PPE and EEPAS forecast logic fully consistent with Biondini et al. (2023)

----

Version 0.1.0 (2025-10-19)
--------------------------

Optimizer Support Expansion

Added
^^^^^

**Optimizer Support Expansion**

- Added L-BFGS-B, TNC, SLSQP, Powell optimizers
- Basin-Hopping global optimization strategy
- Multistart multiple starting point strategy (customizable number of starting points)

**Optimizer Comparison Study**

- Complete optimizer comparison report (OPTIMIZER_COMPARISON_REPORT.md)
- Systematic comparison of 5 optimizers across 4 configurations
- Tested Multistart (3/10 starting points), Basin-Hopping, Hybrid strategies

**Single-Stage Optimization Mode**

- ``--no-multistart`` parameter support for single starting point optimization
- ``--optimizer`` parameter for optimizer selection
- ``--n-starts`` parameter for customizable multistart starting points
- ``--basinhopping`` and ``--basinhopping-niter`` parameters

Changed
^^^^^^^

**Convergence Criteria Optimization**

- Adjusted convergence tolerances for different optimizers to ensure fair comparison
- scipy gradient optimizers use relative ftol, fmin uses absolute ftol
- L-BFGS-B: ftol=1e-9, gtol=1e-7
- SLSQP: ftol=1e-12
- TNC: ftol=1e-9, gtol=1e-3

Fixed
^^^^^

- Fixed optimizer convergence criteria inconsistency issue
- Improved boundary adjustment logic

Research Findings
^^^^^^^^^^^^^^^^^

- **fminsearchcon (Nelder-Mead) most robust** (finds high-quality solutions on all configurations)
- **Gradient methods fast but unstable** (50% success rate, prone to local optima)
- **Basin-Hopping and large Multistart (>10) ineffective for this problem**
- **Recommended strategy**: Run fminsearchcon and L-BFGS-B + Multistart in parallel, select better result

Archived
^^^^^^^^

- All optimizer test data moved to ``archive/optimizer_tests_2025_10_19/``

----

Version 0.0.0 (2025-10-15)
--------------------------

Initial Python Release

Added
^^^^^

**Initial Features**

- Complete EEPAS model implementation (PPE, EEPAS, Aftershock learning)
- Automatic boundary adjustment for EEPAS learning
- Analysis tools:

  - Earthquake distribution analysis (6 vs 24 regions)
  - Weight analysis across 4 configurations
  - Region subdivision tool (6 → 24 regions)

- Coordinate conversion tool (WGS84 ↔ TWD97)
- 4 pre-configured setups:

  - Standard (m0=2.35)
  - Declustered (m0=2.05)
  - Include 921 earthquake (m0=2.35)
  - m0=2.05 variant

**Documentation**

- README.md with quick start guide
- USAGE.md with detailed instructions
- Analysis documentation in docs/

**Validation**

- Full validation against MATLAB version (100% match)
- Standalone python_src directory (no external dependencies)

**Performance**

- Performance optimization with Numba JIT

Changed
^^^^^^^

- Migrated all MATLAB analysis scripts to Python
- Refactored code structure for better organization
- Updated directory layout for professional project structure

Fixed
^^^^^

- Boundary touching issues in EEPAS optimization
- Coordinate conversion precision (< 0.01m error)
- Path handling for cross-platform compatibility

Technical Details
^^^^^^^^^^^^^^^^^

- Python 3.8+ support
- Dependencies: numpy, scipy, numba, pandas, h5py, matplotlib, pyproj
- MIT License
- Git-friendly structure with .gitignore

Contributing
------------

For guidelines on how to contribute to this project, please contact the development team.

For detailed information about each version, see the full CHANGELOG in the repository.

