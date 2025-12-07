"""
PPE Parameter Optimization Engine

Optimize PPE model parameters (a, d, s) using Maximum Likelihood Estimation.

Model: λ₀(x,y) = Σⱼ [a·(mⱼ-mT)/(π(d²+r²)) + s]

Called by ppe_learning.py to find optimal spatial clustering parameters.
"""

import numpy as np
from numba import jit, prange
from scipy.integrate import dblquad


# ===== Shared functions moved to unified module =====
# fast_kernel_sum_2d and trapezoidal_2d moved to utils/numerical_integration.py
# Import shared functions to avoid code duplication
from utils.numerical_integration import fast_kernel_sum_2d, trapezoidal_2d


@jit(nopython=True, fastmath=True)
def fast_kernel_single(x, y, d, xj, yj, weights):
    """
    Computes PPE spatial kernel superposition at a single point.

    Seismological meaning:
        Same as fast_kernel_sum_2d, but only computes the value at a single coordinate point (x,y).
        Used as the integrand function during numerical integration.

    Args:
        x, y: Single coordinate point
        d: Characteristic distance (km)
        xj, yj: Historical earthquake location arrays
        weights: Magnitude weight array

    Returns:
        Kernel function superposition value at that point
    """
    val = 0.0
    for k in range(len(xj)):
        dx = x - xj[k]
        dy = y - yj[k]
        # Cauchy kernel superposition
        val += weights[k] / (np.pi * (d**2 + dx**2 + dy**2))
    return val


# trapezoidal_2d moved to utils/numerical_integration.py (see import above)


def calculate_ppe_normalization(a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE,
                                delay, m0, mT, profile_opts, tj, T1, T2,
                                use_fast_mode=True, spatial_samples=50):
    """
    Computes PPE normalization integral: unified interface (supports fast/accurate modes).

    Args:
        use_fast_mode: True=trapezoidal rule (fast), False=dblquad (accurate)
        spatial_samples: Grid resolution for trapezoidal rule (effective when use_fast_mode=True)

    Returns:
        (normalization_sum, kernel_integral_total, kernel_deriv_total, s_area_total)
    """
    if use_fast_mode:
        return _calculate_ppe_normalization_fast(
            a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE,
            delay, m0, mT, profile_opts, tj, T1, T2, spatial_samples
        )
    else:
        return _calculate_ppe_normalization_accurate(
            a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE,
            delay, m0, mT, profile_opts, tj, T1, T2
        )


def _calculate_ppe_normalization_fast(a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE,
                                      delay, m0, mT, profile_opts, tj, T1, T2,
                                      spatial_samples=50):
    """
    Computes PPE normalization integral: ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy

    Seismological meaning:
        Computes the "total number of earthquakes" predicted by the PPE model during the learning
        period [T1,T2] over the entire study region. This value should approximate the actual
        number of observed earthquakes (a sign of good fit).

    Mathematical form:
        ∫ₜ₁ᵗ² ∫ₘₜᵐᵘ ∫∫ₐᵣₑₐ [f₀(t)×g₀(m)×h₀(x,y)] dx dy dm dt

    where:
        - f₀(t) = 1/t: Temporal integral = log(T2) - log(T1)
        - g₀(m) = β·exp[-β(m-m₀)]: Magnitude integral = exp[-β(mT-m₀)] - exp[-β(mu-m₀)]
        - h₀(x,y) = Σⱼ[a·(mⱼ-mT)/(π(d²+r²)) + s]: Spatial integral (numerical computation)

    Implementation strategy:
        1. Temporal and magnitude integrals: Analytical solution
        2. Spatial integral: Use fixed-grid trapezoidal integration (faster than scipy.dblquad)
        3. Consider delay: Earthquakes contribute only after 'delay' days

    Args:
        a, d, s: PPE parameters (to be estimated)
        B: Gutenberg-Richter b-value
        xi, yi, mi, ti: Historical earthquake data
        Xpol, Ypol: Grid cell boundaries
        CELLE: Grid cell definitions
        delay: Delay in days
        m0, mT: Completeness magnitude, target magnitude
        profile_opts: Integration options (magnitude range, etc.)
        T1, T2: Learning time window
        spatial_samples: Spatial integration grid resolution (default 50×50)

    Returns:
        PPE normalization integral value
    """
    # ===== Set integration range =====
    mu_upper = profile_opts.get('mu', 7.5)  # Upper bound for magnitude integral (maximum mainshock magnitude)
    m_lower = mT  # Lower bound for magnitude integral (default: target magnitude mT)
    if profile_opts.get('integralLower', 'mT').lower() == 'm0':
        m_lower = m0  # Optional: Start integration from completeness magnitude m₀

    # ===== Set magnitude distribution reference point =====
    # Determines reference point for magnitude distribution g₀(m) = β·exp[-β(m-mag_ref)]
    mag_ref = mT  # Default: mT (paper version)
    if profile_opts.get('magDistReference', 'mT').lower() == 'm0':
        mag_ref = m0  # Optional: m0 (legacy version)

    # ===== Compute magnitude integral (analytical solution) =====
    # ∫ₘₗᵐᵘ β·exp[-β(m-mag_ref)] dm = exp[-β(m_lower-mag_ref)] - exp[-β(mu-mag_ref)]
    mag_integral_part = np.exp(-B * (m_lower - mag_ref)) - np.exp(-B * (mu_upper - mag_ref))

    # ===== Set spatial kernel weight baseline =====
    # Seismological meaning: Determines which earthquakes contribute to spatial kernel and how weights are computed
    thrK = mT  # Spatial kernel magnitude threshold
    weight_base = mT  # Weight baseline (wⱼ = mⱼ - weight_base)
    if profile_opts.get('kernelMagFilter', 'mT').lower() == 'm0':
        thrK = m0
        weight_base = m0

    # ===== Filter events and compute temporal integral =====
    # Seismological meaning: Account for delay - earthquakes contribute only after 'delay' days
    # Sum_I: Earthquakes before T1-delay (contribute over entire [T1,T2] period)
    # Sum_II: Earthquakes in (T1-delay, T2-delay] (contribute over partial period)
    indices_in_Sum_I = np.where(ti <= T1 - delay)[0]
    indices_in_Sum_II = np.where((ti > T1 - delay) & (ti <= T2 - delay))[0]

    # Pre-compute coefficient for each event (temporal integral × magnitude integral × magnitude weight)
    event_xi = []
    event_yi = []
    event_weights = []
    t_sum = 0  # Used to compute total temporal integral for background term s

    # ===== Sum_I: Early earthquakes (full contribution) =====
    for ii in indices_in_Sum_I:
        if mi[ii] < thrK:  # Filter earthquakes below threshold
            continue
        # Temporal integral: ∫ₜ₁ᵗ² 1/t dt = log(T2) - log(T1)
        t_int = np.log(T2) - np.log(T1)
        t_sum += t_int
        # Full coefficient = temporal integral × magnitude integral × a·(mᵢ-mT)
        coeff = t_int * mag_integral_part * (mi[ii] - weight_base)
        event_xi.append(xi[ii])
        event_yi.append(yi[ii])
        event_weights.append(coeff)

    # ===== Sum_II: Mid-period earthquakes (partial contribution) =====
    for ii in indices_in_Sum_II:
        if mi[ii] < thrK:
            continue
        # Temporal integral: ∫ₜᵢ₊ₐₑₗₐᵧᵗ² 1/t dt = log(T2) - log(tᵢ+delay)
        t_int = np.log(T2) - np.log(ti[ii] + delay)
        t_sum += t_int
        coeff = t_int * mag_integral_part * (mi[ii] - weight_base)
        event_xi.append(xi[ii])
        event_yi.append(yi[ii])
        event_weights.append(coeff)

    event_xi = np.array(event_xi)
    event_yi = np.array(event_yi)
    event_weights = np.array(event_weights)

    # Coefficient for background term s (magnitude integral × total temporal integral)
    s_base_coeff = mag_integral_part * t_sum

    # ===== Compute spatial integral: ∫∫ h₀(x,y) dx dy =====
    # Seismological meaning: Compute total contribution of spatial kernel over entire study region
    # Method: Use trapezoidal integration for each grid cell
    normalization_sum = 0.0
    total_area = 0.0

    for cell_idx in range(len(CELLE)):
        # Get boundaries of current grid cell
        xa = Xpol[cell_idx, 0]  # x minimum value
        xb = Xpol[cell_idx, 2]  # x maximum value
        ya = Ypol[cell_idx, 0]  # y minimum value
        yb = Ypol[cell_idx, 2]  # y maximum value

        area_cell = (xb - xa) * (yb - ya)  # Grid cell area
        total_area += area_cell

        # Create regular grid within current grid cell (spatial_samples × spatial_samples)
        x_1d = np.linspace(xa, xb, spatial_samples)
        y_1d = np.linspace(ya, yb, spatial_samples)
        x_grid, y_grid = np.meshgrid(x_1d, y_1d)

        # ===== Compute Cauchy kernel superposition =====
        # Use Numba JIT parallelization to compute kernel function values at all grid points
        if len(event_xi) > 0:
            # h₀(x,y) = Σᵢ [a·(mᵢ-mT)/(π(d²+r²))]
            kernel_values = fast_kernel_sum_2d(x_grid, y_grid, d, event_xi, event_yi, event_weights)
        else:
            kernel_values = np.zeros_like(x_grid)

        # ===== Add uniform background term s =====
        # h₀(x,y) = a × Cauchy kernel superposition + s
        # Note: kernel_values already includes temporal and magnitude integral coefficients
        f_values = a * kernel_values + s * s_base_coeff

        # ===== Use trapezoidal integration to compute integral over current grid cell =====
        dx = (xb - xa) / (spatial_samples - 1)  # Grid spacing in x direction
        dy = (yb - ya) / (spatial_samples - 1)  # Grid spacing in y direction
        cell_integral = trapezoidal_2d(f_values, dx, dy)

        normalization_sum += cell_integral

    # Ensure normalization integral is positive
    normalization_sum = max(normalization_sum, 0.0)

    # Total contribution of background term s (for diagnostics)
    s_area_total = s_base_coeff * total_area

    # Gradient computation related (not implemented in this function, interface reserved)
    kernel_integral_total = 0.0
    kernel_deriv_total = 0.0

    return normalization_sum, kernel_integral_total, kernel_deriv_total, s_area_total


def optimization_ppe_taiwan(CELLE, a, d, s, xj, yj, mj, tj, xi, yi, mi, ti, mT,
                            Xpol, Ypol, F_func, B, delay, m0, fit_mode='joint',
                            profile_opts=None, T1=None, T2=None, return_gradient=False,
                            spatial_samples=40, region_manager=None,
                            use_fast_mode=True):
    """
    PPE model negative log-likelihood function (Stage 1 objective function).

    Seismological meaning:
        Evaluates the goodness of fit of PPE parameters (a, d, s) to the earthquake catalog.
        Good parameters should assign high occurrence rates to "earthquakes that actually occurred",
        while ensuring "total predicted earthquake count" matches "actual earthquake count".

    Mathematical form:
        NLL = -[Σ_{(xj,yj)∈R} log λ₀(tj,mj,xj,yj) - ∫∫∫∫_R λ₀(t,m,x,y) dt dm dx dy]

    Args:
        CELLE: Spatial grid definition
        a, d, s: PPE parameters (to be estimated)
            a: Spatial kernel intensity coefficient
            d: Characteristic distance (km)
            s: Uniform background rate
        xj, yj, mj, tj: Target earthquake locations, magnitudes, times (testing region R) - paper's j
        xi, yi, mi, ti: Historical earthquakes for PPE background calculation (neighborhood region N) - paper's i (M≥mT, from neighborhood region)
        mT: Target magnitude threshold
        Xpol, Ypol: Grid cell boundaries
        F_func: Spatial distribution function (unused in this function, interface reserved)
        B: Gutenberg-Richter b-value
        delay: Delay in days
        m0: Completeness magnitude
        fit_mode: Fitting mode (default 'joint')
        profile_opts: Integration options
        T1, T2: Learning time window
        return_gradient: Whether to return gradient (not implemented in this version)
        spatial_samples: Spatial integration grid resolution (default 40)
        region_manager: RegionManager instance (optional)
            - None: No spatial filtering (backward compatible)
            - RegionManager: Filter target earthquakes to testing region R

    Returns:
        NLL value (smaller is better)
    """
    profile_opts = profile_opts or {}
    mu = profile_opts.get('mu', 7.5)  # Maximum mainshock magnitude
    verbose = profile_opts.get('verbose', True)

    # Set magnitude distribution reference point
    mag_ref = mT  # Default: mT (paper version)
    if profile_opts.get('magDistReference', 'mT').lower() == 'm0':
        mag_ref = m0  # Optional: m0 (legacy version)

    # Set spatial kernel weight baseline
    weight_base_event = mT
    if profile_opts.get('kernelMagFilter', 'mT').lower() == 'm0':
        weight_base_event = m0

    # ===== Spatial region filtering: Filter target earthquakes to testing region R =====
    # Seismological meaning: According to the paper Equation 1, likelihood summation should only include events with (xj,yj)∈R
    # Without region filtering (region_manager=None): No filtering, maintain backward compatibility
    # With region filtering (region_manager provided): Only compute events within testing region R
    if region_manager is not None:
        # Use RegionManager to determine which target earthquakes are in testing region
        target_mask = region_manager.is_in_testing_region(xj, yj)
        xj_filtered = xj[target_mask]
        yj_filtered = yj[target_mask]
        mj_filtered = mj[target_mask]
        tj_filtered = tj[target_mask]

        # Hide detailed spatial filtering output to improve log readability
        # if verbose and len(mi) > 0:
        #     print(f'Spatial filtering: {len(mi)} → {len(mj_filtered)} events (testing region R)')
    else:
        # Without region filtering: Use all target earthquakes
        xj_filtered = xj
        yj_filtered = yj
        mj_filtered = mj
        tj_filtered = tj

    # ===== Part 1: Compute event term Σ_{(xj,yj)∈R} log λ₀(tj,mj,xj,yj) =====
    log_LL = 0.0

    for i in range(len(mj_filtered)):
        # Select historical earthquakes occurring more than 'delay' days before target earthquake i
        before_idx = ti < tj_filtered[i] - delay
        if not np.any(before_idx):
            continue

        # Compute temporal and magnitude term: f₀(t) × g₀(m) = (1/t) × β·exp[-β(m-mag_ref)]
        # mag_ref is set at beginning of function according to profile_opts['magDistReference']
        fg_i = (1 / tj_filtered[i]) * B * np.exp(-B * (mj_filtered[i] - mag_ref))

        # Compute spatial term: h₀(xᵢ,yᵢ) = Σⱼ [a·(mⱼ-mT)/(π(d²+rⱼ²)) + s]
        dx, dy = xi[before_idx] - xj_filtered[i], yi[before_idx] - yj_filtered[i]
        r2 = dx**2 + dy**2  # Distance squared
        inv_den = 1.0 / (d**2 + r2)  # Reciprocal of Cauchy kernel denominator
        weights = (mi[before_idx] - weight_base_event) / np.pi * inv_den  # Magnitude weight × Cauchy kernel

        # λ₀(tᵢ,mᵢ,xᵢ,yᵢ) = f₀(t) × g₀(m) × [a·Σwⱼ + s·N]
        # where N is the number of historical earthquakes
        event_sum = fg_i * (a * np.sum(weights) + np.sum(before_idx) * s)

        # Check numerical validity
        if event_sum <= 0:
            return np.inf  # Unreasonable parameter combination

        log_LL += np.log(event_sum)

    # ===== Part 2: Compute normalization term ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy =====
    # Seismological meaning: Total number of earthquakes predicted by PPE model during learning period
    # Use unified interface (supports fast/accurate modes)
    norm, _, _, _ = calculate_ppe_normalization(
        a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE, delay, m0, mT,
        profile_opts, tj, T1 or np.min(ti), T2 or np.max(ti),
        use_fast_mode=use_fast_mode, spatial_samples=spatial_samples
    )

    # Diagnostic output (optional)
    if verbose:
        # norm: Total number of earthquakes predicted by model
        # len(mj_filtered): Actual number of observed earthquakes (within testing region R)
        # Difference close to 0 indicates good model fit
        print(f'Mode: {fit_mode}, N = {len(mj_filtered)}, Λ(D) = {norm:.6f}, Difference = {norm - len(mj_filtered):.6f}')

    # ===== Compute negative log-likelihood (NLL) =====
    # NLL = -[Σ log λ₀ - ∫λ₀] = -[event term - normalization term]
    # Smaller is better: large event term (successful prediction) and moderate normalization term (no over-prediction)
    fd = -(log_LL - norm)
    return fd


def _calculate_ppe_normalization_accurate(a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE,
                                          delay, m0, mT, profile_opts, tj, T1, T2):
    """
    Computes PPE normalization integral: ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy (accurate version - dblquad)

    Seismological meaning:
        Same as fast version, but uses scipy.dblquad for adaptive double integration.
        Higher accuracy but slower speed (approximately 10-20x slower).

    Method:
        Uses ppe_spatial_integral_accurate from unified module for adaptive integration over each grid cell.
        Suitable for paper verification or scenarios requiring extremely high accuracy.

    Args: Same as _calculate_ppe_normalization_fast
    Returns: (normalization_sum, kernel_integral_total, kernel_deriv_total, s_area_total)
    """
    from utils.numerical_integration import ppe_spatial_integral_accurate

    mu_upper = profile_opts.get('mu', 7.5)
    m_lower = mT
    if profile_opts.get('integralLower', 'mT').lower() == 'm0':
        m_lower = m0

    mag_ref = mT
    if profile_opts.get('magDistReference', 'mT').lower() == 'm0':
        mag_ref = m0

    mag_integral_part = np.exp(-B * (m_lower - mag_ref)) - np.exp(-B * (mu_upper - mag_ref))

    thrK = mT
    weight_base = mT
    if profile_opts.get('kernelMagFilter', 'mT').lower() == 'm0':
        thrK = m0
        weight_base = m0

    indices_in_Sum_I = np.where(ti <= T1 - delay)[0]
    indices_in_Sum_II = np.where((ti > T1 - delay) & (ti <= T2 - delay))[0]

    # Pre-compute coefficients (weight does not include a, will be multiplied through a_coeff later)
    event_data = []
    t_sum = 0

    for ii in indices_in_Sum_I:
        if mi[ii] < thrK:
            continue
        t_int = np.log(T2) - np.log(T1)
        t_sum += t_int
        # weight = t_int * mag_integral * (mᵢ - weight_base), does not include a
        weight = t_int * mag_integral_part * (mi[ii] - weight_base)
        event_data.append((weight, xi[ii], yi[ii]))

    for ii in indices_in_Sum_II:
        if mi[ii] < thrK:
            continue
        t_int = np.log(T2) - np.log(ti[ii] + delay)
        t_sum += t_int
        weight = t_int * mag_integral_part * (mi[ii] - weight_base)
        event_data.append((weight, xi[ii], yi[ii]))

    s_coeff = mag_integral_part * t_sum

    # Compute spatial integral (using unified module)
    normalization_sum = 0.0
    total_area = 0.0

    for cell_idx in range(len(CELLE)):
        xa = Xpol[cell_idx, 0]
        xb = Xpol[cell_idx, 2]
        ya = Ypol[cell_idx, 0]
        yb = Ypol[cell_idx, 2]

        area_cell = (xb - xa) * (yb - ya)
        total_area += area_cell

        # Use accurate integration function from unified module
        cell_integral = ppe_spatial_integral_accurate(
            (xa, xb), (ya, yb),
            event_data, d, s, s_coeff,
            a_coeff=a  # PPE Learning: need to multiply by a
        )

        normalization_sum += cell_integral

    normalization_sum = max(normalization_sum, 0.0)
    s_area_total = s_coeff * total_area

    # Accurate mode does not compute gradients
    kernel_integral_total = 0.0
    kernel_deriv_total = 0.0

    return normalization_sum, kernel_integral_total, kernel_deriv_total, s_area_total
