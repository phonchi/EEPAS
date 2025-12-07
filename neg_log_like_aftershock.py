#!/usr/bin/env python3
"""
Aftershock Model Negative Log-Likelihood

Calculate NLL for aftershock model parameter estimation (ν, κ).

Used in Step 2 to distinguish independent events from aftershocks.
"""

import numpy as np
from scipy.integrate import dblquad
from numba import jit, prange
from numpy.polynomial.legendre import leggauss
import math


@jit(nopython=True, parallel=True, fastmath=True)
def compute_event_terms_fast(t_targ, m_targ, x_targ, y_targ,
                             t_prec, m_prec, x_prec, y_prec,
                             t_j, m_j, x_j, y_j,
                             v, k, a, d, s, B, mT, m0, p_omori, c_omori, delta, sigmaU, delay, ppe_ref_mag):
    """
    Compute log-likelihood term for all target events: Σ log λ'(tᵢ,mᵢ,xᵢ,yᵢ)

    Seismological Significance:
        The "total occurrence rate" at the time of each target earthquake, comprising two sources:
        1. PPE background rate λ₀: from spatial proximity
        2. Aftershock triggering rate Σλᵢ': from aftershock triggering by previous earthquakes

    Args:
        t_targ, m_targ, x_targ, y_targ: Time, magnitude, location of target earthquakes
        t_prec, m_prec, x_prec, y_prec: Time, magnitude, location of potential precursors
        t_j, m_j, x_j, y_j: Historical earthquakes for PPE background calculation
        v, k: Aftershock model parameters (ν, κ)
        a, d, s: PPE parameters
        B: Gutenberg-Richter b-value (natural logarithm base)
        mT, m0: Magnitude thresholds
        p_omori, c_omori: Omori's law parameters
        delta: Bath's law parameter (magnitude difference between aftershocks and mainshock)
        sigmaU: Utsu spatial relationship parameter
        delay: Delay time (days)

    Returns:
        Σ log λ'(tᵢ,mᵢ,xᵢ,yᵢ)
    """
    num_targets = len(t_targ)
    log_lambda_values = np.zeros(num_targets)

    # ===== Parallel computation of log λ'(tᵢ,mᵢ,xᵢ,yᵢ) for each target event =====
    # Numba prange implements multi-core parallelization (equivalent to MATLAB's parfor)
    for i in prange(num_targets):
        ti = t_targ[i]
        mi = m_targ[i]
        xi = x_targ[i]
        yi = y_targ[i]

        # ===== Compute PPE background rate λ₀(tᵢ,mᵢ,xᵢ,yᵢ) =====
        # λ₀ = f₀(t) × g₀(m) × h₀(x,y)
        # h₀(x,y): PPE spatial function, superposition of Cauchy kernels from historical earthquakes
        h0_sum_part = 0.0
        for j in range(len(t_j)):
            if t_j[j] < ti - delay:  # Only consider earthquakes before the delay period
                dx = x_j[j] - xi
                dy = y_j[j] - yi
                inv_den = 1.0 / (d**2 + (dx**2 + dy**2))
                # Cauchy kernel + uniform background rate (using ppe_ref_mag as reference magnitude)
                h0_sum_part += a * (m_j[j] - ppe_ref_mag) * (1.0/np.pi) * inv_den + s

        # g₀(m): Gutenberg-Richter magnitude distribution (using ppe_ref_mag as reference magnitude)
        g0_part = B * np.exp(-B * (mi - ppe_ref_mag))
        # f₀(t): Time function 1/t
        f0_part = 1.0 / ti
        lambda0_at_i = f0_part * g0_part * h0_sum_part

        # ===== Compute aftershock triggering rate Σ λᵢ'(tᵢ,mᵢ,xᵢ,yᵢ) =====
        # Aftershock contribution from each past earthquake ℓ
        triggered_rate_at_i = 0.0
        for l in range(len(t_prec)):
            if t_prec[l] < ti:  # Only consider earthquakes occurring before the current event
                t_past = t_prec[l]
                m_past = m_prec[l]
                x_past = x_prec[l]
                y_past = y_prec[l]

                # f'(t): Omori's law (aftershock temporal decay)
                # Form: (p-1)/(t-t_ℓ+c)^p
                time_decay = (p_omori - 1) / (ti - t_past + c_omori)**p_omori

                # g'(m): Bath's law (aftershock magnitude distribution)
                # Heaviside function: aftershock magnitude must be smaller than mainshock
                if m_past - delta >= mi:
                    mag_dist = B * np.exp(-B * (mi - m_past))
                else:
                    mag_dist = 0.0  # Magnitude too large, does not satisfy Bath's law

                # h'(x,y): Utsu spatial relationship (aftershock spatial distribution)
                # 2D Gaussian distribution, variance related to mainshock magnitude
                sigma_val = sigmaU * np.sqrt(10**m_past)
                space_dist = (1.0/(2.0*np.pi*sigma_val**2)) * \
                            np.exp(-((xi-x_past)**2+(yi-y_past)**2)/(2.0*sigma_val**2))

                triggered_rate_at_i += time_decay * mag_dist * space_dist

        # ===== Total occurrence rate =====
        # λ'(tᵢ,mᵢ,xᵢ,yᵢ) = ν·λ₀ + κ·Σλᵢ'
        lam_i = v * lambda0_at_i + k * triggered_rate_at_i
        log_lambda_values[i] = np.log(lam_i)

    return np.sum(log_lambda_values)


@jit(nopython=True, fastmath=True)
def calculate_aftershock_spatial_integral_fast(xp, yp, mp, sigmaU, CELLE):
    """
    Compute aftershock spatial integral: ∫∫ h'(x,y|xₚ,yₚ,mₚ) dx dy

    Seismological Significance:
        Calculates the total probability of aftershocks generated from source (xₚ,yₚ)
        across the entire study region. Uses Utsu spatial relationship: aftershock
        spatial distribution is 2D Gaussian, with standard deviation related to
        mainshock magnitude: σ = sigmaU × √(10^mₚ)

    Mathematical Principle:
        Integral of 2D Gaussian distribution over rectangular region, using analytical
        solution with error function (erf):
        ∫∫ N(x,y|μₓ,μᵧ,σ²) dx dy = [Φ(x₂)-Φ(x₁)] × [Φ(y₂)-Φ(y₁)]
        where Φ is the cumulative distribution function of standard normal distribution

    Args:
        xp, yp: Mainshock location
        mp: Mainshock magnitude
        sigmaU: Utsu parameter (controls aftershock spatial diffusion)
        CELLE: Spatial grid matrix [x_left, x_right, y_bottom, y_top]

    Returns:
        Total probability of aftershocks in all grid cells (should be ≈1, but <1 due to finite study region)
    """
    sigma = sigmaU * np.sqrt(10**mp)  # Utsu relationship: σ proportional to 10^(M/2)
    spatial_integral = 0.0
    sqrt2_sigma = np.sqrt(2) * sigma

    for c in range(len(CELLE)):
        X1, X2 = CELLE[c, 0], CELLE[c, 1]
        Y1, Y2 = CELLE[c, 2], CELLE[c, 3]

        # Compute Gaussian integral using analytical solution with error function
        integral_x = 0.5 * (math.erf((X2 - xp)/sqrt2_sigma) - math.erf((X1 - xp)/sqrt2_sigma))
        integral_y = 0.5 * (math.erf((Y2 - yp)/sqrt2_sigma) - math.erf((Y1 - yp)/sqrt2_sigma))

        spatial_integral += integral_x * integral_y

    return spatial_integral


def neg_log_like_aftershock(v, k, CatTargets, CatPrecursors, CatI, a, d, s, T1, T2, params, CELLE, region_manager=None, integral_method='accurate', ppe_ref_mag=None, target_mag=None, integration_mode='fast', spatial_samples=50):
    """
    Compute negative log-likelihood for aftershock model (EEPAS Stage 2 objective function)

    Seismological Significance:
        Evaluates how well parameters (ν, κ) fit the earthquake catalog.
        Good parameters should give high probability (large log λ) to "earthquakes that actually occurred"
        while "total predicted earthquake count" matches "actual earthquake count" (integral term constraint).

    Mathematical Form:
        NLL(ν,κ) = -[Σ log λ'(tᵢ,mᵢ,xᵢ,yᵢ) - ∫∫∫∫ λ'(t,m,x,y) dt dm dx dy]
              = -[log-likelihood term - normalization term]

    Optimization Goal:
        minimize NLL(ν,κ) → find optimal aftershock classification parameters

    Spatial Region Handling:
        - Without region filtering (region_manager=None):
          All computations over entire study region
        - With region filtering (region_manager!=None):
          * Log-likelihood term: sum only over target events in testing region R
          * Integral term: integrate only over testing region R
          * Source events (CatPrecursors, CatI): from neighborhood region

    Args:
        v (ν): Proportion of non-aftershocks ∈ [0,1] (close to 1 means most events are independent)
        k (κ): Aftershock triggering intensity normalization constant (adjusts total aftershock contribution)
        CatTargets: Target event catalog (earthquakes during learning period, testing region R)
        CatPrecursors: Precursor source catalog (earthquakes that may trigger aftershocks, neighborhood region)
        CatI: Historical earthquakes for PPE background calculation (M≥mT, neighborhood region)
        a, d, s: PPE parameters (learned in Stage 1)
        T1, T2: Learning time window [T1, T2) (unit: days)
        params: Model parameter dictionary (b-value, Omori parameters, Utsu parameter, etc.)
        CELLE: Spatial grid matrix (testing region R)
        region_manager: RegionManager instance (optional, for spatial filtering)
        integral_method: Integration method
            'accurate': Full PPE integral calculation (slow but accurate)
            'approximate': Approximate PPE integral ≈ event count (fast but rough)
        integration_mode: PPE integration mode (when integral_method='accurate')
            'fast': Trapezoidal rule (fast)
            'accurate': dblquad adaptive integration (precise)
        spatial_samples: Grid resolution for fast mode (default 50)

    Returns:
        NLL value (smaller is better, negative value indicates higher likelihood)
    """

    # ===== Extract earthquake catalog fields =====
    # MATLAB indexing starts from 1, Python from 0, need -1 conversion
    t_targ = CatTargets[:, 10].copy()  # Time (days)
    m_targ = CatTargets[:, 9].copy()   # Magnitude
    x_targ = CatTargets[:, 7].copy()   # Longitude
    y_targ = CatTargets[:, 6].copy()   # Latitude

    t_prec = CatPrecursors[:, 10].copy()
    m_prec = CatPrecursors[:, 9].copy()
    x_prec = CatPrecursors[:, 7].copy()
    y_prec = CatPrecursors[:, 6].copy()

    t_j = CatI[:, 10].copy()
    m_j = CatI[:, 9].copy()
    x_j = CatI[:, 7].copy()
    y_j = CatI[:, 6].copy()

    # ===== Extract model parameters =====
    num_targets = len(CatTargets)
    B = params['B'] * np.log(10)  # Gutenberg-Richter b-value (convert to natural logarithm base)
    mT = params['mT']              # PPE magnitude threshold
    m0 = params['m0']              # Completeness magnitude
    p_omori = params['p']          # Omori's law exponent (typical value ≈ 1.1)
    c_omori = params['c']          # Omori's law time offset (avoid t=0 singularity)
    delta = params['delta']        # Bath's law: magnitude difference between aftershocks and mainshock (typical value ≈ 1.2)
    sigmaU = params['sigmaU']      # Utsu spatial relationship parameter
    delay = params['delay']        # Delay time (days)
    mu_upper = params.get('mu', 7.5)  # Upper magnitude limit

    # PPE reference magnitude: default uses mT, but can be specified as m0
    if ppe_ref_mag is None:
        ppe_ref_mag = mT

    # Target event magnitude threshold: default uses m0, but can be specified as mT
    # Controls integral lower bound and summation event range
    if target_mag is None:
        target_mag = m0

    # ===== Compute first term: log-likelihood term Σ_{(xi,yi)∈R} log λ'(tᵢ,mᵢ,xᵢ,yᵢ) =====
    # Note:
    #   - CatTargets has been filtered to testing region R in fit_aftershock_params.py
    #   - Therefore this summation is only over target events within testing region R
    # Use Numba parallelization for acceleration (equivalent to MATLAB's parfor)
    log_lambda_sum = compute_event_terms_fast(
        t_targ, m_targ, x_targ, y_targ,
        t_prec, m_prec, x_prec, y_prec,
        t_j, m_j, x_j, y_j,
        v, k, a, d, s, B, mT, m0, p_omori, c_omori, delta, sigmaU, delay, ppe_ref_mag
    )

    # ===== Compute second term: normalization integral ∫∫∫∫[R] λ'(t,m,x,y) dt dm dx dy =====
    # Note:
    #   - CELLE defines the grid of testing region R
    #   - Therefore spatial integration is only over testing region R
    #   - Source events (CatPrecursors, CatI) are from neighborhood region (avoid boundary effects)
    # Split into two parts: PPE background integral + aftershock triggering integral

    # 2a) PPE background integral: ν × ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy
    if integral_method == 'approximate':
        # Approximation: assume integral ≈ event count (fast but rough)
        integral_ppe_total = v * num_targets
    else:
        # Accurate method: full computation of time-space-magnitude integral
        if integration_mode == 'accurate':
            # Use dblquad adaptive integration (accurate but slow)
            integral_ppe = calculate_ppe_integral_term_mT_accurate(
                a, d, s, B, T1, T2, x_j, y_j, m_j, t_j, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag
            )
        else:
            # Use trapezoidal rule (fast, consistent with PPE/EEPAS Learning)
            integral_ppe = calculate_ppe_integral_term_mT_fast(
                a, d, s, B, T1, T2, x_j, y_j, m_j, t_j, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag,
                spatial_samples=spatial_samples
            )
        integral_ppe_total = v * integral_ppe

        # Old version (Gauss-Legendre) is retained in calculate_ppe_integral_term_mT function
        # For comparison testing, can temporarily switch back to old method:
        # integral_ppe = calculate_ppe_integral_term_mT(
        #     a, d, s, B, T1, T2, x_j, y_j, m_j, t_j, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag
        # )

    # 2b) Aftershock triggering integral: κ × Σ ∫∫∫∫ λᵢ'(t,m,x,y) dt dm dx dy
    integral_triggered = calculate_triggered_integral_fast(
        t_prec, m_prec, x_prec, y_prec, T1, T2,
        p_omori, c_omori, delta, target_mag, mu_upper, B, sigmaU, CELLE
    )

    integral_triggered_total = k * integral_triggered
    total_integral = integral_ppe_total + integral_triggered_total

    # ===== Compute negative log-likelihood =====
    # NLL = -(Σ log λ' - ∫ λ')
    # Minimizing NLL is equivalent to maximizing log-likelihood
    nll = -(log_lambda_sum - total_integral)

    return nll


def calculate_triggered_integral_fast(t_prec, m_prec, x_prec, y_prec, T1, T2,
                                      p_omori, c_omori, delta, target_mag, mu_upper, B, sigmaU, CELLE):
    """
    Compute normalization integral for aftershock triggering: Σ ∫∫∫∫ λᵢ'(t,m,x,y) dt dm dx dy

    Seismological Significance:
        Calculates the total "expected number" of aftershocks generated by all potential
        mainshocks in time-space-magnitude. Integral decomposes into: time integral (Omori's law)
        × magnitude integral (Bath's law) × spatial integral (Utsu relationship)

    Args:
        t_prec, m_prec, x_prec, y_prec: Time, magnitude, location of potential mainshocks
        T1, T2: Integral time range
        p_omori, c_omori: Omori's law parameters
        delta: Bath's law parameter
        target_mag, mu_upper: Magnitude integral range (target_mag is lower bound)
        B: Gutenberg-Richter b-value
        sigmaU: Utsu spatial parameter
        CELLE: Spatial grid

    Returns:
        Expected total number of all aftershocks (not multiplied by κ)
    """
    integral_triggered = 0.0

    # Filter out events with tp >= T2
    valid_mask = t_prec < T2
    t_prec_valid = t_prec[valid_mask]
    m_prec_valid = m_prec[valid_mask]
    x_prec_valid = x_prec[valid_mask]
    y_prec_valid = y_prec[valid_mask]

    for i in range(len(t_prec_valid)):
        tp, mp, xp, yp = t_prec_valid[i], m_prec_valid[i], x_prec_valid[i], y_prec_valid[i]

        # Omori time integral
        t_start = max(T1, tp)
        if t_start >= T2:
            int_f2 = 0.0
        else:
            int_f2 = -((T2 - tp + c_omori)**(-p_omori+1)) + ((t_start - tp + c_omori)**(-p_omori+1))

        if int_f2 == 0.0:
            continue

        # Bath magnitude integral
        m_up = mp - delta
        if m_up <= target_mag:
            int_g2 = 0.0
        else:
            m_int_up = min(m_up, mu_upper)
            int_g2 = -np.exp(-B*(m_int_up - mp)) + np.exp(-B*(target_mag - mp))

        if int_g2 == 0.0:
            continue

        # Utsu spatial integral (using Numba accelerated version)
        int_h2 = calculate_aftershock_spatial_integral_fast(xp, yp, mp, sigmaU, CELLE)

        integral_triggered += int_f2 * int_g2 * int_h2

    return integral_triggered


@jit(nopython=True, fastmath=True)
def cauchy_integral_gauss_numba(x0, y0, d, X1, X2, Y1, Y2, xi, wi):
    """
    Compute Cauchy kernel integral over rectangular region (Gauss-Legendre quadrature)

    Seismological Significance:
        Calculates the total contribution of PPE earthquake kernel from source (x0, y0)
        over a rectangular grid cell. Cauchy distribution reflects the spatial influence
        range of earthquakes, with parameter d controlling decay rate.

    Mathematical Form:
        ∫∫ (1/π) / (d² + (x-x0)² + (y-y0)²) dx dy

    Implementation Method:
        Gauss-Legendre quadrature (10×10 points), high precision and avoids scipy dependency

    Args:
        x0, y0: Source location
        d: PPE distance decay parameter
        X1, X2, Y1, Y2: Rectangular region boundaries
        xi, wi: Gauss-Legendre quadrature points and weights (pre-computed)

    Returns:
        Integral value (represents contribution of this source to this grid cell)
    """
    n = len(xi)

    # Linear transformation to [X1, X2] and [Y1, Y2]
    dx = (X2 - X1) / 2.0
    dy = (Y2 - Y1) / 2.0
    xc = (X2 + X1) / 2.0
    yc = (Y2 + Y1) / 2.0

    # Double summation
    result = 0.0
    for i in range(n):
        x = xc + dx * xi[i]
        for j in range(n):
            y = yc + dy * xi[j]
            f_val = (1.0/np.pi) / (d**2 + (x - x0)**2 + (y - y0)**2)
            result += wi[i] * wi[j] * f_val

    # Jacobian
    result *= dx * dy

    return result


# ===== Pre-compute Gauss-Legendre quadrature points and weights =====
# Global variable, computed once at program startup and reused
# 10-point quadrature → 10×10=100 sample points, balancing precision and speed
_GAUSS_XI, _GAUSS_WI = leggauss(10)


# ===== Duplicate code removed =====
# fast_kernel_sum_2d and trapezoidal_2d moved to utils/numerical_integration.py
# Import shared functions to avoid code duplication
from utils.numerical_integration import fast_kernel_sum_2d, trapezoidal_2d


def calculate_ppe_integral_term_mT(a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag):
    """
    Compute PPE background rate normalization integral: ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy

    Seismological Significance:
        Calculates the "expected total number of earthquakes" for PPE model over entire
        time-space-magnitude range. This is the normalization condition for probability
        density function, ensuring model predicts a reasonable total earthquake count.

    Integral Decomposition:
        - Time integral: Σ log(T2/max(T1, tⱼ+delay))
        - Magnitude integral: 1 - exp(-B(μ_upper - target_mag))
        - Spatial integral: Superposition of Cauchy kernels over all grid cells

    Args:
        a, d, s: PPE parameters
        B: Gutenberg-Richter b-value
        T1, T2: Time range
        xj, yj, mj, tj: Historical earthquakes (M≥mT)
        CELLE: Spatial grid
        mT: PPE magnitude threshold
        delay: Delay time
        target_mag, mu_upper: Magnitude integral range (target_mag is lower bound)

    Returns:
        Total integral of PPE background rate (expected earthquake count)
    """

    # Magnitude integral: use ppe_ref_mag as reference magnitude, target_mag as lower bound
    mag_int = - np.exp(-B * (mu_upper - ppe_ref_mag)) + np.exp(-B * (target_mag - ppe_ref_mag))

    area_total = np.sum((CELLE[:, 1] - CELLE[:, 0]) * (CELLE[:, 3] - CELLE[:, 2]))
    t_sum = 0
    kernel_sum = 0

    for i in range(len(mj)):
        lower_t = max(T1, tj[i] + delay)
        if lower_t >= T2:
            t_j_val = 0
        else:
            t_j_val = np.log(T2) - np.log(lower_t)

        t_sum += t_j_val

        if t_j_val == 0:
            continue

        # Spatial integral for κ (using Numba accelerated Gauss quadrature)
        spatial_int = 0
        for c in range(len(CELLE)):
            X1, X2 = CELLE[c, 0], CELLE[c, 1]
            Y1, Y2 = CELLE[c, 2], CELLE[c, 3]

            spatial_int += cauchy_integral_gauss_numba(
                xj[i], yj[i], d, X1, X2, Y1, Y2, _GAUSS_XI, _GAUSS_WI
            )

        # Spatial kernel also uses ppe_ref_mag as reference magnitude
        kernel_sum += a * (mj[i] - ppe_ref_mag) * t_j_val * spatial_int

    ppe_integral = mag_int * (kernel_sum + s * area_total * t_sum)
    return ppe_integral


def calculate_ppe_integral_term_mT_fast(a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag, spatial_samples=50):
    """
    Compute PPE background rate normalization integral: ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy (Trapezoidal version)

    Renamed from: calculate_ppe_integral_term_mT_trapezoidal

    Seismological Significance:
        Same as calculate_ppe_integral_term_mT, but uses trapezoidal rule instead of Gauss-Legendre integration.
        This uses the same integration method as PPE Learning and EEPAS Learning, ensuring consistency.

    Implementation Strategy:
        - First superpose Cauchy kernels from all earthquakes onto grid (vectorized)
        - Then perform trapezoidal integration once over entire grid
        - Instead of integrating each earthquake separately (current Gauss approach)

    Mathematical Equivalence:
        ∫∫ [Σⱼ wⱼ·κⱼ(x,y)] dx dy = Σⱼ wⱼ·[∫∫ κⱼ(x,y) dx dy]

    Performance Advantage:
        - Gauss method: 26,000 integration calls (one per earthquake)
        - Trapezoidal method: 177 integration calls (one per grid cell) + vectorized superposition

    Args:
        a, d, s: PPE parameters
        B: Gutenberg-Richter b-value
        T1, T2: Time range
        xj, yj, mj, tj: Historical earthquakes (M≥mT)
        CELLE: Spatial grid
        mT: PPE magnitude threshold
        delay: Delay time
        target_mag, mu_upper: Magnitude integral range
        ppe_ref_mag: PPE reference magnitude
        spatial_samples: Grid resolution (default 50)

    Returns:
        Total integral of PPE background rate (expected earthquake count)
    """
    # Magnitude integral (same as Gauss version)
    mag_int = - np.exp(-B * (mu_upper - ppe_ref_mag)) + np.exp(-B * (target_mag - ppe_ref_mag))

    area_total = np.sum((CELLE[:, 1] - CELLE[:, 0]) * (CELLE[:, 3] - CELLE[:, 2]))

    # ===== Collect event locations and weights =====
    event_xj = []
    event_yj = []
    event_weights = []
    t_sum = 0

    for i in range(len(mj)):
        lower_t = max(T1, tj[i] + delay)
        if lower_t >= T2:
            continue

        t_j_val = np.log(T2) - np.log(lower_t)
        t_sum += t_j_val

        # Collect event locations and weights (time integral × magnitude weight)
        event_xj.append(xj[i])
        event_yj.append(yj[i])
        event_weights.append(a * (mj[i] - ppe_ref_mag) * t_j_val)

    event_xj = np.array(event_xj)
    event_yj = np.array(event_yj)
    event_weights = np.array(event_weights)

    # ===== Spatial integral (trapezoidal rule) =====
    spatial_int = 0.0

    for c in range(len(CELLE)):
        X1, X2 = CELLE[c, 0], CELLE[c, 1]
        Y1, Y2 = CELLE[c, 2], CELLE[c, 3]

        # Generate grid
        x_1d = np.linspace(X1, X2, spatial_samples)
        y_1d = np.linspace(Y1, Y2, spatial_samples)
        x_grid, y_grid = np.meshgrid(x_1d, y_1d)

        # Vectorized computation of Cauchy kernel superposition at all grid points
        if len(event_xj) > 0:
            kernel_values = fast_kernel_sum_2d(
                x_grid, y_grid, d, event_xj, event_yj, event_weights
            )
        else:
            kernel_values = np.zeros_like(x_grid)

        # Trapezoidal integration
        dx = (X2 - X1) / (spatial_samples - 1)
        dy = (Y2 - Y1) / (spatial_samples - 1)
        spatial_int += trapezoidal_2d(kernel_values, dx, dy)

    # PPE total integral
    ppe_integral = mag_int * (spatial_int + s * area_total * t_sum)
    return ppe_integral



def calculate_ppe_integral_term_mT_accurate(a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag):
    """
    Compute PPE background rate normalization integral: ∫∫∫∫ λ₀(t,m,x,y) dt dm dx dy (Accurate version - dblquad)

    Seismological Significance:
        Same as fast version, but uses scipy.dblquad for adaptive double integration
        Higher precision but slower (approximately 10-20x)

    Method:
        Uses ppe_spatial_integral_accurate from unified module for adaptive integration
        over each grid cell. Suitable for paper validation or scenarios requiring
        extremely high precision.

    Args: Same as calculate_ppe_integral_term_mT_fast (except no spatial_samples)
    Returns: Total integral of PPE background rate (expected earthquake count)
    """
    from utils.numerical_integration import ppe_spatial_integral_accurate

    # Magnitude integral (same as fast version)
    mag_int = - np.exp(-B * (mu_upper - ppe_ref_mag)) + np.exp(-B * (target_mag - ppe_ref_mag))

    area_total = np.sum((CELLE[:, 1] - CELLE[:, 0]) * (CELLE[:, 3] - CELLE[:, 2]))

    # Collect event locations and weights (weight already includes a, so a_coeff=1 later)
    event_data = []
    t_sum = 0

    for i in range(len(mj)):
        lower_t = max(T1, tj[i] + delay)
        if lower_t >= T2:
            continue

        t_j_val = np.log(T2) - np.log(lower_t)
        t_sum += t_j_val

        # weight = a * (mⱼ - ppe_ref_mag) * t_j_val, already includes a
        weight = a * (mj[i] - ppe_ref_mag) * t_j_val
        event_data.append((weight, xj[i], yj[i]))

    s_coeff = mag_int * t_sum

    # Spatial integral (using unified module)
    spatial_int = 0.0

    for c in range(len(CELLE)):
        X1, X2 = CELLE[c, 0], CELLE[c, 1]
        Y1, Y2 = CELLE[c, 2], CELLE[c, 3]

        # Use accurate integration function from unified module
        cell_integral = ppe_spatial_integral_accurate(
            (X1, X2), (Y1, Y2),
            event_data, d, s, s_coeff,
            a_coeff=1.0  # Fit Aftershock: weight already includes a
        )

        spatial_int += cell_integral

    # PPE total integral
    ppe_integral = mag_int * spatial_int
    return ppe_integral


def calculate_ppe_integral_term_mT(a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag,
                                    use_fast_mode=True, spatial_samples=50):
    """
    Compute PPE background rate normalization integral: Unified interface (supports fast/accurate modes)

    Args:
        use_fast_mode: True=trapezoidal rule (fast), False=dblquad (accurate)
        spatial_samples: Grid resolution for trapezoidal method (effective when use_fast_mode=True)

    Returns:
        Total integral of PPE background rate (expected earthquake count)
    """
    if use_fast_mode:
        return calculate_ppe_integral_term_mT_fast(
            a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag,
            spatial_samples
        )
    else:
        return calculate_ppe_integral_term_mT_accurate(
            a, d, s, B, T1, T2, xj, yj, mj, tj, CELLE, mT, delay, target_mag, mu_upper, ppe_ref_mag
        )
