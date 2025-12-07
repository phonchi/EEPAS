Analysis Modules
================

Tools for :math:`\Psi` phenomenon detection, deduplication, and scaling relations analysis.

:math:`\Psi` Phenomenon Detection
----------------------

Detect precursory scale increase using the rectangular algorithm (Christophersen et al., 2024).

.. autofunction:: analysis.optimize_psi_working.optimize_psi

.. autofunction:: analysis.optimize_psi_working.trimcycle_early

.. autofunction:: analysis.optimize_psi_working.parameters_select

----

Deduplication
-------------

Two-stage deduplication to remove duplicate :math:`\Psi` identifications.

.. autofunction:: analysis.optimize_psi_results.optimize_psi_results

----

Scaling Relations
-----------------

Fixed-effects regression for initial parameter estimation.

.. autofunction:: analysis.plot_relations.analyze_scaling_relations

.. autofunction:: analysis.plot_relations._fixed_effects_slope_safe

----

Utility Functions
-----------------

Dataset Extraction
^^^^^^^^^^^^^^^^^^

.. autofunction:: analysis.dataset.extract_period_forecast

.. autofunction:: analysis.dataset.create_subgrids_spatial

Time Conversion
^^^^^^^^^^^^^^^

.. autofunction:: analysis.decimal_time.decimal_time_precise

.. autofunction:: analysis.decimal_time.ymd_time_precise

Event Selection
^^^^^^^^^^^^^^^

.. autofunction:: analysis.select_m5plus.select_events_with_options

Forecast Validation
^^^^^^^^^^^^^^^^^^^

.. autofunction:: analysis.analyze_forecast_lambda.analyze_forecast_results

Forecast Format Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Convert EEPAS/PPE forecast matrices to PyCSEP-compatible format.

.. autoclass:: analysis.forecast_converter.EEPASForecastConverter
   :members:
   :undoc-members:

.. autofunction:: analysis.forecast_converter.convert_eepas_forecast

PyCSEP Compatibility
^^^^^^^^^^^^^^^^^^^^

Patch pycsep for Shapely 2.x compatibility.

.. autofunction:: analysis.patch_pycsep.patch_csep_regions

----

References
----------

Christophersen, A., Rhoades, D. A., & Hainzl, S. (2024).
*Algorithmic Identification of the Precursory Scale Increase Phenomenon
in Earthquake Catalogs.* Seismological Research Letters, 95(6), 3464-3481.

----

See Also
--------

- :doc:`core` - Core EEPAS modules
- :doc:`../examples/index` - Analysis workflow examples
