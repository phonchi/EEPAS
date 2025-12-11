Mathematical Foundation
=======================

This section provides the mathematical foundations of the EEPAS and PPE models, extracted from the theoretical framework presented in the research paper.

Overview
--------

The EEPAS (Every Earthquake a Precursor According to Scale) model combines:

1. **PPE Model**: Proximity to Past Earthquakes - baseline seismicity
2. **EEPAS Component**: Precursor-driven rate enhancement
3. **Mixing Parameter**: μ (failure-to-predict rate)

The Total Rate Density
----------------------

Mathematical Formulation
^^^^^^^^^^^^^^^^^^^^^^^^

The complete EEPAS+PPE rate density is:

.. math::

   \lambda(t,m,x,y) = \mu \lambda_0(t,m,x,y) + \sum_{t_i \geq t_0;\, m_i \geq m_0}^{t - \mathrm{delay}} \eta(m_i) \frac{\lambda_i(t,m,x,y)}{\Delta(m)}

where:

- **μ**: Failure-to-predict rate (proportion without detectable medium-term precursors)
- **1-μ**: Precursor-driven rate (proportion with medium-term precursory scaling)
- **λ₀**: PPE baseline intensity (in the absence of medium-term precursory build-up)
- **λᵢ**: Medium-term precursory contribution from event i
- **η(m)**: Magnitude-dependent scaling function
- **Δ(m)**: Incompleteness correction factor

Component Functions
^^^^^^^^^^^^^^^^^^^

Each precursor contribution λᵢ(t,m,x,y) decomposes into three independent components:

.. math::

   \lambda_i(t,m,x,y) = w_i f_i(t) g_i(m) h_i(x,y)

**Time Component** f(t): Lognormal distribution

.. math::

   f_i(t) = \frac{1}{(t-t_i)\ln 10\, \sigma_T \sqrt{2\pi}}
   \exp\left[-\frac{(\log_{10}(t-t_i) - a_T - b_T m_i)^2}{2\sigma_T^2}\right]

**Magnitude Component** g(m): Gaussian distribution

.. math::

   g_i(m) = \frac{1}{\sigma_M \sqrt{2\pi}}
   \exp\left[-\frac{(m - a_M - b_M m_i)^2}{2\sigma_M^2}\right]

**Spatial Component** h(x,y): Bivariate Gaussian

.. math::

   h_i(x,y) = \frac{1}{2\pi \sigma_A^2 10^{b_A m_i}}
   \exp\left[-\frac{(x-x_i)^2 + (y-y_i)^2}{2\sigma_A^2 10^{b_A m_i}}\right]

PPE Model
---------

The PPE baseline rate density represents seismicity without medium-term precursory effects:

.. math::

   \lambda_0(t,m,x,y) = f_0(t) g_0(m) h_0(x,y)

**Time**: Proportional to catalog duration

.. math::

   f_0(t) = \frac{1}{t - t_0}

**Magnitude**: Gutenberg-Richter law

.. math::

   g_0(m) = \beta \exp[-\beta(m - m_T)]

where β = b_GR ln(10), with b_GR being the Gutenberg-Richter b-value.

**Space**: Sum of spatial kernels from past events

.. math::

   h_0(x,y) = \sum_{t_i < t;\, m_i \geq m_T} \left[a(m_i - m_T) \frac{1}{\pi(d^2 + r_i^2)} + s\right]

where rᵢ² = (x-xᵢ)² + (y-yᵢ)² is the squared distance to event i.

Parameters:
   - **a**: Intensity parameter (background rate amplitude)
   - **d**: Characteristic distance (spatial decay, km)
   - **s**: Uniform background rate

Correction Factors
------------------

Incompleteness Correction Δ(m)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since earthquakes below m₀ are excluded from the catalog, their contribution must be accounted for:

.. math::

   \Delta(m) = \Phi\left(\frac{m - a_M - b_M m_0 - \sigma_M^2 \beta}{\sigma_M}\right)

where Φ(x) is the standard normal cumulative distribution function (CDF).

**Physical Meaning**: Δ(m) represents the fraction of triggered events above m₀ that would be observed given the catalog's completeness threshold.

Magnitude Scaling Function η(m)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The function η(m) scales precursor productivity to preserve the Gutenberg-Richter magnitude distribution:

.. math::

   \eta(m) = \frac{(1 - \mu) b_M}{E(w)} \exp\left\{-\beta \left[a_M + (b_M - 1)m + \frac{\sigma_M^2 \beta}{2}\right]\right\}

where:
   - **E(w)**: Expected value (mean) of weights wᵢ
   - **β**: Magnitude scaling constant (b_GR ln 10)

**Purpose**: Ensures that the integrated contribution from precursors averages to (1-μ), maintaining the overall Gutenberg-Richter distribution.

Log-Likelihood Function
-----------------------

Parameter Estimation
^^^^^^^^^^^^^^^^^^^^

Parameters are estimated by maximizing the log-likelihood for an inhomogeneous Poisson point process:

.. math::

   \ln\mathcal{L}(\lambda) = \sum_{j} \ln\lambda(t_j, m_j, x_j, y_j)
   - \int_{t_s}^{t_e} \int_{m_T}^{m_u} \iint_R \lambda(t,m,x,y)\, dA\, dm\, dt

where:
   - **First term**: Sum over observed target events (j) in [t_s, t_e) with m ≥ m_T
   - **Second term**: Expected number of events (normalization integral)
   - **R**: Testing region (spatial domain)

Key Property
^^^^^^^^^^^^

Under maximum likelihood estimation, the normalization integral equals the observed event count:

.. math::

   \int_{t_s}^{t_e} \int_{m_T}^{m_u} \iint_R \lambda(t,m,x,y)\, dA\, dm\, dt \approx N_{\text{observed}}

This is a fundamental consistency check for model calibration.

Analytical Integration
----------------------

Many integrals in EEPAS have closed-form solutions using the error function:

.. math::

   \mathrm{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2} dt

Time Integral (Lognormal)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

   \int_{t_s}^{t_e} f_i(t)\, dt = \frac{1}{2}\left[
   \mathrm{erf}\left(\frac{\log_{10}(t_e - t_i) - \mu_i}{\sqrt{2}\sigma_T}\right)
   - \mathrm{erf}\left(\frac{\log_{10}(t_s - t_i) - \mu_i}{\sqrt{2}\sigma_T}\right)
   \right]

where μᵢ = a_T + b_T mᵢ.

Spatial Integral (Gaussian)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a rectangular cell [X₁, X₂] × [Y₁, Y₂]:

.. math::

   \iint_{[X_1,X_2] \times [Y_1,Y_2]} h_i(x,y)\, dA = \frac{1}{4}
   \left[\mathrm{erf}\left(\frac{X_2-x_i}{\sqrt{2}\sigma_i}\right)
   - \mathrm{erf}\left(\frac{X_1-x_i}{\sqrt{2}\sigma_i}\right)\right]
   \times
   \left[\mathrm{erf}\left(\frac{Y_2-y_i}{\sqrt{2}\sigma_i}\right)
   - \mathrm{erf}\left(\frac{Y_1-y_i}{\sqrt{2}\sigma_i}\right)\right]

where σᵢ = σ_A · 10^(b_A mᵢ/2).

**Performance Benefit**: Using erf (implemented with fast polynomial approximations) instead of numerical quadrature provides ~10x speedup with no loss of accuracy.

Model Parameters
----------------

PPE Parameters (3)
^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Meaning
   * - a
     - Background intensity (region-dependent)
   * - d
     - Spatial decay distance (km)
   * - s
     - Uniform background rate (often ≈0)

EEPAS Parameters (8+1)
^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Meaning
   * - a_M
     - Magnitude scaling intercept
   * - b_M
     - Magnitude scaling slope (often fixed at 1.0)
   * - σ_M
     - Magnitude uncertainty
   * - a_T
     - Time scaling intercept
   * - b_T
     - Time scaling slope
   * - σ_T
     - Time uncertainty
   * - b_A
     - Spatial scaling exponent
   * - σ_A
     - Spatial uncertainty
   * - μ (u)
     - Failure-to-predict rate (0.0-1.0)

Aftershock Parameters (2)
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Meaning
   * - ν (v)
     - Independent event proportion (not aftershocks)
   * - κ (k)
     - Aftershock normalization constant

Physical Interpretation
-----------------------

Scaling Relations (:math:`\Psi` Phenomenon)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The EEPAS model is based on empirical scaling relations:

**Magnitude Scaling**:

.. math::

   M_m = a_M + b_M M_p

Larger precursors predict larger mainshocks.

**Time Scaling**:

.. math::

   \log_{10} T_p = a_T + b_T M_p

Larger precursors have longer lead times.

**Spatial Scaling**:

.. math::

   \log_{10} A_p = b_A M_p

Larger precursors affect wider areas.

Failure-to-Predict Rate
^^^^^^^^^^^^^^^^^^^^^^^^

The parameter μ represents the proportion of earthquakes occurring without identifiable precursors:

- **μ = 0**: All events have precursors (pure EEPAS)
- **μ = 0.5**: Half background, half precursor-driven
- **μ = 1**: No precursors (pure PPE)

**Italy Example** (μ = 0.167):
   - 16.7% of events are "background" (no detectable precursor)
   - 83.3% of events are precursor-driven (EEPAS component)

Computational Complexity
------------------------

The computational cost of EEPAS is dominated by the normalization integral:

.. math::

   \text{Cost} \sim \mathcal{O}(N_{\text{cells}} \times N_{\text{events}} \times N_{\text{time windows}})

**Italy Example** (177 cells, ~27,000 events, 40 time windows):
   - Evaluations per forecast: ~177 × 27,000 × 40 ≈ 191 million
   - With analytical integrals + Numba JIT: significantly faster
   - Without optimization: ~hours

See Also
--------

- :doc:`optimization` - Parameter estimation strategies
- :doc:`numerical_integration` - Integration methods and performance
- :doc:`../api_reference/core` - API documentation for core modules
