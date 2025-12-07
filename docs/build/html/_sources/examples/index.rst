Examples and Tutorials
======================

This section demonstrates EEPAS integration with the earthquake forecasting ecosystem through three interactive notebooks.

**Framework Integration**

EEPAS is designed to work seamlessly with established seismological tools:

- **pyCSEP** (Savran et al., 2022; Graham et al., 2024): Standardized forecast evaluation using consistency tests (L-test, N-test, S-test, M-test) and comparative scoring rules (log-likelihood, Brier, Kagan information scores).
- **SeismoStats** (Mirwald et al., 2025): Statistical seismology package providing robust b-value estimators (b-positive, Tinti, Kijko-Smit) and catalog preprocessing tools.
- **Rectangular Algorithm** (Christophersen et al., 2024): Automated :math:`\Psi` phenomenon detection that identifies precursor-mainshock pairs and derives initial EEPAS parameter estimates through fixed-effects regression.

The complete workflow from raw catalog preprocessing to rigorous forecast evaluation is demonstrated below.

Notebooks
---------

.. toctree::
   :maxdepth: 1
   :caption: Interactive Examples

   Examine_Psi_Italy_clean
   EEPAS_Forecast_Evaluation_New
   Estimate_mc_b_Italy_clean

Notebook 1: Automated :math:`\Psi` Phenomenon Detection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`Examine_Psi_Italy_clean`

**Purpose**: Demonstrate the rectangular algorithm for automated precursor identification.

**Integration Highlights**:

- **Automated :math:`\Psi` Detection**: The rectangular algorithm (Christophersen et al., 2024) systematically identifies all precursor-mainshock pairs within a specified search radius (e.g., 400 km).
- **Fixed-Effects Regression**: Addresses the space-time trade-off inherent in nested observations by properly distinguishing within-mainshock correlation from between-mainshock scaling relationships.
- **Initial Parameter Estimation**: Derives initial values for EEPAS parameters from empirical scaling relations:

  .. math::

     \log_{10} T_p &= a_T + b_T M_p \\
     \log_{10} A_p &= b_A M_p \\
     M_m &= a_M + b_M M_p

**Outputs**:

- Scatterplots with fitted scaling relations
- Initial parameter estimates

**Key Advantage**: Replaces manual :math:`\Psi` identification (a major barrier to EEPAS adoption) with a fully automated, reproducible procedure.

Notebook 2: Forecast Evaluation with pyCSEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`EEPAS_Forecast_Evaluation_New`

**Purpose**: Rigorous statistical evaluation of EEPAS and PPE forecasts using pyCSEP.

**Integration Highlights**:

- **Consistency Tests**:

  - **L-test**: Overall likelihood fit (observed earthquakes vs forecast)
  - **N-test**: Total event count (Poisson or Negative Binomial)
  - **S-test**: Spatial distribution consistency
  - **M-test**: Magnitude distribution consistency

- **Comparative Scoring**:

  - **Log-likelihood score**: Measures overall model fit
  - **Brier score**: Particularly suitable for rare events
  - **Kagan information score**: Quantifies spatial informativeness

- **pyCSEP-Compatible Output**: EEPAS generates gridded forecasts in the standard format required by pyCSEP, enabling seamless integration with the Collaboratory for the Study of Earthquake Predictability (CSEP) testing framework.

**Key Advantage**: End-to-end validation using established statistical benchmarks, ensuring reproducibility and comparability with other forecasting models.

Notebook 3: Catalog Preprocessing with SeismoStats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`Estimate_mc_b_Italy_clean`

**Purpose**: Estimate magnitude of completeness (:math:`m_c`) and b-value using SeismoStats.

**Integration Highlights**:

- **SeismoStats Package**: Provides multiple b-value estimators:

  - **b-positive** (Lippiello et al., 2024): Maximum likelihood with positive bias correction
  - **Tinti & Mulargia** (1987): Accounts for magnitude binning
  - **Kijko & Smit** (2012): Handles temporal variation in completeness

- **Magnitude of Completeness (:math:`m_c`) Estimation**:

  - Maximum curvature method
  - Goodness-of-fit test (GFT)
  - b-value stability analysis

- **Gutenberg-Richter Validation**:

  .. math::

     \log_{10} N(m) = a - b \cdot m

  where :math:`b \approx 1.0` for most regions.

**EEPAS Parameter Dependency**:

The estimated b-value feeds directly into EEPAS:

.. math::

   \beta = b \ln 10 \approx 2.303 b

This :math:`\beta` parameter appears in:

- Incompleteness correction: :math:`\Delta(m) = \Phi\left(\frac{m - a_M - b_M m_0 - \sigma_M^2 \beta}{\sigma_M}\right)`
- Normalization factor: :math:`\eta(m) \propto \exp\{-\beta[a_M + (b_M - 1)m + \sigma_M^2 \beta / 2]\}`

**Key Advantage**: Ensures EEPAS forecasts are based on statistically sound catalog preprocessing, avoiding biases from incorrect :math:`m_c` or :math:`b`-value estimates.

Complete Workflow Summary
--------------------------

The three notebooks demonstrate a complete earthquake forecasting pipeline:

1. **Preprocessing** (Notebook 3): Estimate :math:`m_c` and :math:`b` using **SeismoStats**
2. **Parameter Initialization** (Notebook 1): Automate :math:`\Psi` detection using **Rectangular Algorithm**
3. **Model Fitting**: Optimize EEPAS parameters via maximum likelihood (command-line tools)
4. **Forecast Generation**: Create gridded rate forecasts (command-line tools)
5. **Statistical Evaluation** (Notebook 2): Validate forecasts using **pyCSEP**

This end-to-end integration showcases EEPAS as a modern, reproducible framework for medium- to long-term earthquake forecasting, fully compatible with the established tools of statistical seismology.

**References**

- Christophersen, A., Rhoades, D. A., & Hainzl, S. (2024). Algorithmic Identification of the Precursory Scale Increase Phenomenon in Earthquake Catalogs. *Seismological Research Letters*, 95(6), 3464–3481.

- Glenn, W. B., et al. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3.

- Graham, K. M., Bayona, J. A., Khawaja, A. M., et al. (2024). New features in the pyCSEP toolkit for earthquake forecast development and evaluation. *Seismological Research Letters*, 95(6), 3449–3463.

- Kagan, Y. Y. (2009). Testing long-term earthquake forecasts: likelihood methods and error diagrams. *Geophysical Journal International*, 177(2), 532–542.

- Lippiello, E., & Petrillo, G. (2024). b-more-incomplete and b-more-positive: Insights on a robust estimator of magnitude distribution. *Journal of Geophysical Research: Solid Earth*, 129(2), e2023JB027849.

- Mirwald, A., Schmid, N., Han, M., Rohnacher, A., Mizrahi, L., Ritz, V. A., & Wiemer, S. (2025). SeismoStats: A Python Package for Statistical Seismology. GitHub repository. https://github.com/swiss-seismological-service/SeismoStats

- Savran, W. H., Bayona, J. A., Iturrieta, P., Asim, K. M., Bao, H., Bayliss, K., Herrmann, M., Schorlemmer, D., Maechling, P. J., & Werner, M. J. (2022). pyCSEP: A Python toolkit for earthquake forecast developers. *Seismological Society of America*, 93(5), 2858–2870.
