#!/usr/bin/env python3
"""
EEPAS Likelihood Calculation

Calculate negative log-likelihood for EEPAS model parameter optimization.

Combines PPE background rate with precursory signals from weighted earthquakes.
"""

import numpy as np
from scipy.special import erf
from scipy.integrate import quad, quad_vec
from numba import jit, prange
import warnings


@jit(nopython=True, fastmath=True)
def safe_exp(x):
    """
    Safe exponential function (prevents numerical overflow).

    Rationale: exp(x) overflows for x>709, underflows to 0 for x<-745
    Solution: Clamp exponent to [-700, 700] range
    """
    if x < -700:
        return np.exp(-700)
    elif x > 700:
        return np.exp(700)
    else:
        return np.exp(x)


@jit(nopython=True, fastmath=True)
def safe_log10(x):
    """
    Safe logarithm function (prevents non-positive input).

    Rationale: log(x) is undefined for x≤0
    Solution: Return log of tiny value for non-positive input (treating x as tiny positive)
    """
    if x <= 0:
        return np.log10(1e-300)
    else:
        return np.log10(x)


# ===== Shared function moved to unified module =====
# fast_magnitude_integral moved to utils/numerical_integration.py
# Import shared function to avoid code duplication
from utils.numerical_integration import fast_magnitude_integral


@jit(nopython=True, parallel=True, fastmath=True)
def compute_eepas_contributions_inner(
    mi_val, xi_val, ti_val, yi_val,
    te, xe, ye, me, W, mag_denoms,
    am, bm, Sm, at, bt, St, ba, Sa, u, B, EW, delay
):
    """
    Compute EEPAS foreshock contribution for a single target earthquake: Σ wₑ·ηₑ·λₑ(tᵢ,mᵢ,xᵢ,yᵢ)/Δ(mᵢ).

    Seismological significance:
        For target earthquake i, compute the summed contribution from all potential foreshocks e.
        Each foreshock contribution consists of four components:
        1. Magnitude distribution gₑ(mᵢ): Prediction relation from foreshock magnitude mₑ to mainshock magnitude mᵢ
        2. Temporal distribution fₑ(tᵢ): Delay distribution from foreshock time tₑ to mainshock time tᵢ
        3. Spatial distribution hₑ(xᵢ,yᵢ): Distance decay from foreshock location (xₑ,yₑ) to mainshock location (xᵢ,yᵢ)
        4. Weighting factors: wₑ (aftershock de-weighting) × ηₑ (magnitude normalization)

    Args:
        mi_val, xi_val, ti_val, yi_val: Magnitude, location, time of target earthquake i
        te, xe, ye, me: Time, location, magnitude arrays of all EEPAS foreshocks
        W: Aftershock de-weighting array wₑ (reduces aftershock foreshock status)
        mag_denoms: Pre-computed magnitude denominators Δ(mᵢ) (compensates for missing small earthquakes)
        am, bm, Sm: Magnitude distribution parameters (gₑ ~ N(am+bm·mₑ, Sm²))
        at, bt, St: Temporal distribution parameters (log₁₀(t-tₑ) ~ N(at+bt·mₑ, St²))
        ba, Sa: Spatial distribution parameters (σ_spatial = Sa × 10^(ba·mₑ/2))
        u: Failure-to-predict rate
        B: Gutenberg-Richter b-value
        EW: Mean weight E[wₑ]
        delay: Delay time (days)

    Returns:
        Total EEPAS contribution for this target earthquake (weighted superposition of all foreshocks)
    """
    n_events = len(te)
    total_contribution = 0.0

    # ===== Parallel loop over all EEPAS foreshocks =====
    # Numba prange implements multi-core parallelism (equivalent to MATLAB's parfor)
    for e in prange(n_events):
        # Time filtering already done externally (te[e] < ti_val - delay)
        time_diff = ti_val - te[e]  # Time interval from foreshock to mainshock (days)

        # ===== Magnitude term gₑ(mᵢ) =====
        # Gaussian distribution: N(am + bm·mₑ, Sm²)
        # Seismological meaning: Prediction relation from foreshock magnitude mₑ to mainshock magnitude mᵢ
        mag_diff = mi_val - am - bm * me[e]
        mag_numerator = (1.0 / (Sm * np.sqrt(2.0 * np.pi))) * \
                       safe_exp(-0.5 * (mag_diff / Sm)**2)

        # ===== Temporal term fₑ(tᵢ) =====
        # Log-normal distribution: log₁₀(t-tₑ) ~ N(at + bt·mₑ, St²)
        # Seismological meaning: How long after foreshock occurrence will mainshock be triggered
        log_time_diff = safe_log10(time_diff)
        time_exponent = -0.5 * ((log_time_diff - at - bt * me[e]) / St)**2
        temporal = (1.0 / (time_diff * np.log(10.0) * St * np.sqrt(2.0 * np.pi))) * \
                  safe_exp(time_exponent)

        # ===== Spatial term hₑ(xᵢ,yᵢ) =====
        # 2D Gaussian distribution with magnitude-dependent standard deviation: σ = Sa × 10^(ba·mₑ/2)
        # Seismological meaning: How far from the foreshock will the mainshock occur
        dx = xi_val - xe[e]
        dy = yi_val - ye[e]
        r2 = dx * dx + dy * dy  # Distance squared

        spatial_factor = 10.0**(ba * me[e])  # Magnitude-dependent spatial diffusion
        spatial_denom = 2.0 * np.pi * Sa * Sa * spatial_factor
        spatial_exponent = -r2 / (2.0 * Sa * Sa * spatial_factor)
        spatial = (1.0 / spatial_denom) * safe_exp(spatial_exponent)

        # ===== EEPAS normalization factor ηₑ =====
        # Formula: ηₑ = [bm·(1-u)/E(w)] × exp(-B[am+(bm-1)mₑ+Bσ²ₘ/2])
        # Seismological meaning: Ensures total integral of foreshock contributions = (1-u)
        rate_exponent = -B * (am + (bm - 1.0) * me[e] + (B * Sm * Sm) / 2.0)
        rate = ((bm * (1.0 - u)) / EW) * safe_exp(rate_exponent)

        # ===== Weighted accumulation =====
        # λₑ = ηₑ × gₑ × fₑ × hₑ × wₑ / Δ(mᵢ)
        # (Division by Δ(mᵢ) performed externally)
        total_contribution += rate * mag_numerator * temporal * spatial * W[e]

    return total_contribution


@jit(nopython=True, parallel=True, fastmath=True)
def compute_ppe_contributions_inner(
    mi_val, xi_val, ti_val, yi_val,
    xj, yj, mj, tj,
    a, d, s, B, m0, mT, delay, ppe_ref_mag
):
    """
    Compute PPE background rate contribution for a single target earthquake: λ₀(tᵢ,mᵢ,xᵢ,yᵢ).

    Seismological significance:
        PPE (Proximity to Past Earthquakes) model assumes future earthquakes tend to
        occur near past earthquakes. λ₀ is background rate based on spatial distribution of historical seismicity.

    Mathematical form:
        λ₀(t,m,x,y) = f₀(t) × g₀(m) × h₀(x,y)
        Where:
        - f₀(t) = 1/t: Temporal decay (Omori-type)
        - g₀(m) = β·exp[-β(m-m₀)]: Gutenberg-Richter magnitude distribution
        - h₀(x,y) = Σⱼ [a·(mⱼ-mT)/(π(d²+r²)) + s]: Superposition of spatial kernels

    Args:
        mi_val, xi_val, ti_val, yi_val: Magnitude, location, time of target earthquake
        xj, yj, mj, tj: Historical earthquake data (M≥mT, used for PPE background)
        a: Spatial kernel intensity coefficient
        d: Spatial kernel characteristic distance (km)
        s: Uniform background rate
        B: Gutenberg-Richter b-value (natural log base)
        m0: Completeness magnitude
        mT: Target magnitude threshold
    """
    n_ppe = len(tj)
    total_contribution = 0.0

    # ===== Compute spatial kernel h₀(xᵢ,yᵢ) =====
    # Superposition of Cauchy kernels over all historical earthquakes (M≥mT)
    for j in prange(n_ppe):
        # Compute spatial distance between target earthquake and historical earthquake j
        dx = xj[j] - xi_val
        dy = yj[j] - yi_val
        r2 = dx * dx + dy * dy

        # Cauchy kernel: Larger magnitude and closer distance contribute more
        # Formula: (mⱼ-ppe_ref_mag) / [π(d²+r²)]
        spatial = (mj[j] - ppe_ref_mag) / (np.pi * (d * d + r2))

        # Add uniform background rate s (represents randomly occurring earthquakes)
        intensity = a * spatial + s

        total_contribution += intensity

    # ===== Compute temporal and magnitude terms f₀(t) × g₀(m) =====
    # f₀(t) = 1/t: Temporal decay
    # g₀(m) = β·exp[-β(m-ppe_ref_mag)]: Magnitude distribution
    fg = (1.0 / ti_val) * B * safe_exp(-B * (mi_val - ppe_ref_mag))

    # Return complete PPE background rate λ₀ = f₀ × g₀ × h₀
    return fg * total_contribution


def eepas_likelihood(am, bm, Sm, at, bt, St, ba, Sa, u,
                     mj, xj, tj, yj, xi, yi, mi, ti,
                     me, xe, te, ye, W, EW, B, T1, T2, m0,
                     CELLE, params, region_manager=None,
                     use_fast_mode=False, magnitude_samples=20):
    """
    EEPAS model negative log-likelihood function (Stage 3 objective function).

    Seismological significance:
        Evaluates how well the 8 EEPAS parameters fit the earthquake catalog.
        Good parameters should assign high occurrence rates (large log λ) to earthquakes that actually occurred,
        while matching the total predicted earthquake count with the actual count (normalization constraint).

    Mathematical form:
        NLL = -[Σ_{j:(xj,yj)∈R} log λ(tj,mj,xj,yj) - ∫∫∫∫_R λ(t,m,x,y) dt dm dx dy]
        Where λ = μ·λ₀ + Σ wₑ·ηₑ·λₑ/Δ(m)

    Args:
        am, bm, Sm: Magnitude distribution parameters
        at, bt, St: Temporal distribution parameters
        ba, Sa: Spatial distribution parameters
        u: Failure-to-predict rate ∈ [0,1]
        mj, xj, tj, yj: Target earthquakes (M≥mT, in testing region R during learning period) - paper's j
        xi, yi, mi, ti: Historical source earthquakes for PPE background (M≥mT, from neighborhood region N) - paper's i
        me, xe, te, ye: EEPAS foreshocks (M≥m₀, from neighborhood region)
        W: Aftershock de-weighting array
        EW: Mean weight
        B: Gutenberg-Richter b-value
        T1, T2: Learning time window
        m0: Completeness magnitude
        CELLE: Spatial grid (testing region R)
        params: Other model parameters (PPE parameters, delay, etc.)
        region_manager: RegionManager instance (optional)
            - None: No spatial filtering (backward compatible)
            - RegionManager: Filter target earthquakes to testing region R
        use_fast_mode: Whether to use fast mode (default False)
            - True: Use Numba JIT accelerated midpoint rectangle method (fast)
            - False: Use exact quad_vec integration (slow but precise)
        magnitude_samples: Number of sampling points in fast mode (default 20, increase for higher accuracy)

    Returns:
        Negative log-likelihood value (smaller is better)

    Implementation features:
        - Numba JIT parallelization (equivalent to MATLAB's parfor)
        - Fully exact computation, numerically consistent with MATLAB
        - Pre-computed shared values reduce redundant calculations
        - Optional fast mode: Uses midpoint rectangle method instead of quad_vec (5-10x speedup)
    """

    # ===== Extract PPE parameters (results from Stage 1 learning) =====
    a = params['a']    # Spatial kernel intensity coefficient
    d = params['d']    # Spatial kernel characteristic distance (km)
    s = params['s']    # Uniform background rate
    delay = params['delay']  # Delay days after earthquake (avoids aftershock interference)
    mT = params['mT']  # Target magnitude threshold
    mu = params.get('mu', 7.5)  # Maximum mainshock magnitude (upper bound for magnitude integral)
    ppe_ref_mag = params.get('ppe_ref_mag_value', mT)  # PPE reference magnitude (default uses mT)

    # ===== Spatial region filtering: Filter target earthquakes to testing region R =====
    # Seismological meaning: According to the paper Equation 1, likelihood sum should only include events with (xj,yj)∈R
    # Without region filtering (region_manager=None): No filtering, maintains backward compatibility
    # With region filtering (region_manager provided): Only compute events within testing region R
    if region_manager is not None:
        # Use RegionManager to determine which target earthquakes are within testing region
        target_mask = region_manager.is_in_testing_region(xj, yj)
        xj_filtered = xj[target_mask]
        yj_filtered = yj[target_mask]
        mj_filtered = mj[target_mask]
        tj_filtered = tj[target_mask]

        # Hide detailed spatial filtering output to improve log readability
        # if len(mj) > 0:
        #     print(f'Spatial filtering: {len(mj)} → {len(mj_filtered)} events (testing region R)')
    else:
        # Without region filtering: Use all target earthquakes
        xj_filtered = xj
        yj_filtered = yj
        mj_filtered = mj
        tj_filtered = tj

    # ===== Part 1: Compute event term Σ_{j:(xj,yj)∈R} log λ(tj,mj,xj,yj) =====
    # Seismological meaning: Compute the "total occurrence rate" for each target earthquake at its occurrence time
    # Higher occurrence rate indicates better model prediction, contributing larger log λ

    # ===== Pre-compute magnitude denominators Δ(mj) =====
    # Seismological meaning: Compensate for small earthquakes missing due to completeness threshold m₀
    # Formula: Δ(m) = P(M≥m₀|Mmain=m) = Φ((m-am-bm·m₀-Sm²·β)/(√2·Sm))
    # Φ: Standard normal cumulative distribution function (computed using erf)
    denom_args = (mj_filtered - am - bm * m0 - Sm**2 * B) / (np.sqrt(2) * Sm)
    mag_denoms = 0.5 * (erf(denom_args) + 1)
    mag_denoms = np.maximum(mag_denoms, 1e-100)  # Prevent division by zero

    # Initialize contribution arrays
    eepas_contribs = np.zeros(len(mj_filtered))  # EEPAS foreshock contributions
    ppe_contribs = np.zeros(len(mj_filtered))    # PPE background contributions

    # ===== Check if using dynamic E(w) =====
    # Seismological meaning: Dynamic E(w) ensures G-R law is satisfied at each time
    use_causal_ew = params.get('useCausalEW', 0) == 1

    # ===== Compute total occurrence rate for each target earthquake =====
    for j in range(len(mj_filtered)):
        # Temporal filtering: Only consider events occurring at least delay days before target earthquake
        # Seismological meaning: delay period has high aftershock activity, excluded to avoid interference
        eventsBefore_eepas = te < tj_filtered[j] - delay  # EEPAS foreshock filtering
        ppeEventsBefore = ti < tj_filtered[j] - delay     # PPE background filtering (from historical source events)

        # ===== Compute E(w) =====
        # Dynamic mode (useCausalEW=1): Use only events before target earthquake to compute E(w)
        # Fixed mode (useCausalEW=0): Use global EW
        if use_causal_ew and np.any(eventsBefore_eepas):
            EW_j = np.mean(W[eventsBefore_eepas])
        else:
            EW_j = EW

        # ===== Compute EEPAS foreshock contribution Σ wₑ·ηₑ·λₑ/Δ(mj) =====
        if np.any(eventsBefore_eepas):
            eepas_contribs[j] = compute_eepas_contributions_inner(
                mj_filtered[j], xj_filtered[j], tj_filtered[j], yj_filtered[j],
                te[eventsBefore_eepas], xe[eventsBefore_eepas],
                ye[eventsBefore_eepas], me[eventsBefore_eepas],
                W[eventsBefore_eepas], mag_denoms,
                am, bm, Sm, at, bt, St, ba, Sa, u, B, EW_j, delay
            )

        # ===== Compute PPE background contribution λ₀(tj,mj,xj,yj) =====
        if np.any(ppeEventsBefore):
            ppe_contribs[j] = compute_ppe_contributions_inner(
                mj_filtered[j], xj_filtered[j], tj_filtered[j], yj_filtered[j],
                xi[ppeEventsBefore], yi[ppeEventsBefore],
                mi[ppeEventsBefore], ti[ppeEventsBefore],
                a, d, s, B, m0, mT, delay, ppe_ref_mag
            )

    # ===== Apply magnitude denominator correction =====
    # Foreshock contributions need to be divided by Δ(mj) to compensate for missing small foreshocks
    eepas_contribs = eepas_contribs / mag_denoms

    # ===== EEPAS mixture model: λ = (1-u)·foreshock + u·background =====
    # Seismological meaning:
    # - (1-u) portion: Earthquakes with detectable foreshocks
    # - u portion: Earthquakes without detectable foreshocks (only PPE background)
    total_intensities = eepas_contribs + u * ppe_contribs
    total_intensities = np.maximum(total_intensities, 1e-20)  # Prevent log(0)

    # Compute event term sum: Σ log λ(tj,mj,xj,yj)
    logLikelihoodSum = np.sum(np.log(total_intensities))

    E = len(mj_filtered)  # Total number of target earthquakes (within testing region R)

    # ===== Part 2: Compute normalization term ∫∫∫∫ λ(t,m,x,y) dt dm dx dy =====
    # Seismological meaning: Compute the "total earthquake count" predicted by model over entire space-time-magnitude range
    # Good model should have "predicted count" ≈ "actual observed count" (E earthquakes)

    # ===== PPE normalization integral: ∫∫∫∫ μ·λ₀(t,m,x,y) dt dm dx dy =====
    # Seismological meaning: Total earthquake count predicted by PPE background model during learning period
    if '_ppe_integral_cached' in params:
        # Use cached result (can reuse when PPE parameters are fixed)
        integral_PPE = params['_ppe_integral_cached']
    else:
        # First computation of PPE normalization integral (using Numba accelerated version)
        from ppe_optimization import calculate_ppe_normalization
        Xpol = np.column_stack([CELLE[:, 0], CELLE[:, 0], CELLE[:, 1], CELLE[:, 1]])
        Ypol = np.column_stack([CELLE[:, 2], CELLE[:, 3], CELLE[:, 3], CELLE[:, 2]])
        # Set profile_opts based on ppe_ref_mag
        ppe_ref_str = 'm0' if ppe_ref_mag == m0 else 'mT'
        profile_opts = {'mu': mu, 'kernelMagFilter': ppe_ref_str, 'integralLower': ppe_ref_str, 'magDistReference': ppe_ref_str}
        integral_PPE, _, _, _ = calculate_ppe_normalization(
            a, d, s, B, xi, yi, mi, ti, Xpol, Ypol, CELLE, delay, m0, mT,
            profile_opts, tj, T1, T2, spatial_samples=40
        )

    # ===== EEPAS normalization integral: ∫∫∫∫ Σ wₑ·ηₑ·λₑ(t,m,x,y)/Δ(m) dt dm dx dy =====
    # Seismological meaning: Total contribution from all foreshocks integrated over entire space-time-magnitude range
    # Formula: Σₑ wₑ·ηₑ · [∫gₑ(m)/Δ(m)dm] · [∫fₑ(t)dt] · [∫∫hₑ(x,y)dxdy]
    L = len(me)  # Total number of foreshocks
    qq = np.zeros((L, 6))  # Store integral components: [ηₑ, mag integral, time integral, spatial integral, wₑ, reserved]
    qq[:, 4] = W  # Aftershock de-weighting

    # ===== Compute EEPAS normalization factor ηₑ =====
    # Formula: ηₑ = [bm·(1-u)/E(W)] × exp[-β(am+(bm-1)mₑ+βSm²/2)]
    # Seismological meaning: Ensures total integral of foreshock contributions = (1-u) (fraction of earthquakes with foreshock signals)
    qq[:, 0] = ((bm * (1 - u)) / EW) * np.exp(-B * (am + (bm - 1) * me + (B * Sm**2) / 2))

    # ===== Magnitude integral: ∫ₘₜᵐᵘ gₑ(m)/Δ(m) dm =====
    # Seismological meaning: Prediction contribution from foreshock magnitude mₑ to mainshock magnitude m, integrated over [mT, mu]
    # gₑ(m) = N(am+bm·mₑ, Sm²): Linear relationship between foreshock and mainshock magnitude
    # Δ(m): Compensates for missing earthquakes below m₀

    if use_fast_mode:
        # Fast mode: Use Numba JIT accelerated midpoint rectangle method
        mag_integrals = fast_magnitude_integral(mT, mu, me, am, bm, Sm, m0, B, magnitude_samples)
    else:
        # Exact mode: Use scipy.quad_vec numerical integration
        def mag_integrand_vec(m):
            """
            Magnitude integral integrand (vectorized computation).
            Simultaneously computes contribution from all foreshocks to mainshock magnitude m
            """
            # Numerator: Gaussian distribution N(am+bm·mₑ, Sm²)
            numerator = (1 / (Sm * np.sqrt(2*np.pi))) * np.exp(-0.5 * ((m - am - bm * me) / Sm)**2)
            # Denominator: Δ(m) = P(M≥m₀|Mmain=m)
            denom_arg = (m - am - bm * m0 - Sm**2 * B) / (np.sqrt(2) * Sm)
            denom = 0.5 * (erf(denom_arg) + 1)
            return numerator / np.maximum(denom, 1e-100)

        # Use scipy.integrate.quad_vec to compute magnitude integral for all foreshocks simultaneously
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mag_integrals, _ = quad_vec(mag_integrand_vec, mT, mu, epsabs=1e-10, epsrel=1e-6)

    qq[:, 1] = mag_integrals

    # ===== Spatial integral: ∫∫ hₑ(x,y) dx dy =====
    # Seismological meaning: Contribution from foreshock location (xₑ,yₑ) to mainshock spatial distribution
    # hₑ(x,y) ~ N(xₑ,yₑ, Sa²·10^(ba·mₑ)): Larger magnitude, wider influence range
    # Integration domain: Entire study region (divided into grid cells)
    factor = 10**(-ba * me / 2)  # Reciprocal factor of spatial standard deviation, shape: (L,)

    # Use broadcasting to compute contributions from all foreshocks to all grid cells
    factor_expanded = factor[:, np.newaxis]  # (L, 1)
    xe_exp = xe[:, np.newaxis]  # (L, 1)
    ye_exp = ye[:, np.newaxis]  # (L, 1)

    # Compute 2D Gaussian integral over each grid cell [xmin,xmax]×[ymin,ymax]
    # Use analytical solution with erf: ∫∫ N(μ,σ²) = [Φ(x₂)-Φ(x₁)]×[Φ(y₂)-Φ(y₁)]
    term1 = erf(factor_expanded * (CELLE[:, 0] - xe_exp) / (np.sqrt(2) * Sa))  # (L, 24)
    term2 = erf(factor_expanded * (CELLE[:, 1] - xe_exp) / (np.sqrt(2) * Sa))  # (L, 24)
    term3 = erf(factor_expanded * (CELLE[:, 2] - ye_exp) / (np.sqrt(2) * Sa))  # (L, 24)
    term4 = erf(factor_expanded * (CELLE[:, 3] - ye_exp) / (np.sqrt(2) * Sa))  # (L, 24)

    # Compute sum of contributions over all grid cells
    region_contributions = (term1 * term3 - term1 * term4 - term2 * term3 + term2 * term4) / 4.0
    F = np.sum(region_contributions, axis=1)  # Sum over all grids, shape: (L,)
    qq[:, 3] = F

    # ===== Temporal integral: ∫ₜ₁ᵗ² fₑ(t) dt =====
    # Seismological meaning: Temporal distribution of mainshock triggering after foreshock occurrence, during learning period [T1,T2]
    # fₑ(t) ~ LogNormal(at+bt·mₑ, St²): Larger magnitude, longer precursory time
    time_integrals = np.zeros(L)
    valid_mask = te < T2  # Only consider foreshocks occurring before end of learning period

    if np.any(valid_mask):
        te_valid = te[valid_mask]
        me_valid = me[valid_mask]

        # Lower integration bound: max(T1, tₑ+delay) (learning start or delay days after foreshock)
        t_lower = np.maximum(T1, te_valid + delay)
        valid_time_mask = t_lower < T2  # Ensure integration interval is valid

        if np.any(valid_time_mask):
            te_v = te_valid[valid_time_mask]
            me_v = me_valid[valid_time_mask]
            t_lower_v = t_lower[valid_time_mask]

            # Use analytical solution with erf to compute log-normal distribution integral
            # ∫ LogNormal(μ,σ²) dt = Φ((log₁₀(t)-μ)/σ)
            time_int_v = 0.5 * (
                erf((np.log10(T2 - te_v) - at - bt * me_v) / (np.sqrt(2) * St)) -
                erf((np.log10(t_lower_v - te_v) - at - bt * me_v) / (np.sqrt(2) * St))
            )

            # Fill results into corresponding positions
            valid_indices = np.where(valid_mask)[0]
            valid_time_indices = valid_indices[valid_time_mask]
            time_integrals[valid_time_indices] = time_int_v

    qq[:, 2] = time_integrals

    # ===== Compute EEPAS total integral =====
    # Complete contribution from each foreshock = ηₑ × mag integral × time integral × spatial integral × wₑ
    qq[:, 5] = qq[:, 0] * qq[:, 1] * qq[:, 2] * qq[:, 3] * qq[:, 4]
    EEP = np.sum(qq[:, 5])  # Total contribution from all foreshocks

    # ===== Mixture model total normalization integral =====
    # λ total integral = u·(PPE background integral) + (EEPAS foreshock integral)
    # Seismological meaning: Total earthquake count predicted by model during learning period
    total_integral = u * integral_PPE + EEP

    # ===== Compute negative log-likelihood (NLL) =====
    # NLL = -[Σ log λ(tᵢ,mᵢ,xᵢ,yᵢ) - ∫λ dt dm dx dy]
    #     = -[event term - normalization term]
    # Seismological meaning:
    # - Large event term: Model successfully predicts actual earthquakes
    # - Large normalization term: Model predicts too many earthquakes
    # - Smaller NLL is better: Accurate prediction without over-prediction
    fd = -(logLikelihoodSum - total_integral)

    return fd, E, EEP, u


