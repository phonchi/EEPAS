from __future__ import annotations
import numpy as np
import math, os, argparse, scipy.io
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from decimal_time import decimal_time_precise   # Convert datetime to decimal year

# -----------------------------------------------------------------------------
#  Catalog loader
# -----------------------------------------------------------------------------
def _load_catalog(path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load earthquake catalog from .mat or text file.

    .mat file format: HORUS variable with columns:
        [yyyy, MM, dd, hh, mi, ss, lat, lon, depth, mag]

    Text file format (10 columns):
        yyyy mm dd hh mi ss lat lon depth mag

    Args:
        path: Path to catalog file (.mat or text) (str)

    Returns:
    tuple
        (time, lat, lon, depth, mag) arrays where time is in decimal years
    """
    if path.endswith(".mat"):
        m = scipy.io.loadmat(path)
        arr = m['HORUS']
        yyyy, MM, dd, hh, mi, ss_ = arr[:,0], arr[:,1], arr[:,2], arr[:,3], arr[:,4], arr[:,5]
        lat, lon, depth, mag = arr[:,6], arr[:,7], arr[:,8], arr[:,9]
        time = np.array([
            decimal_time_precise(int(y), int(M), int(d), int(h), int(mi_), s)
            for y, M, d, h, mi_, s in zip(yyyy, MM, dd, hh, mi, ss_)
        ])
        return time, lat, lon, depth, mag

    arr = np.loadtxt(path)
    yyyy, MM, dd, hh, mi, ss_ = arr[:,0], arr[:,1], arr[:,2], arr[:,3], arr[:,4], arr[:,5]
    lat, lon, depth, mag = arr[:,6], arr[:,7], arr[:,8], arr[:,9]
    time = np.array([
        decimal_time_precise(int(y), int(M), int(d), int(h), int(mi_), s)
        for y, M, d, h, mi_, s in zip(yyyy, MM, dd, hh, mi, ss_)
    ])
    return time, lat, lon, depth, mag


# -----------------------------------------------------------------------------
#  Helper – Cumulative Magnitude Anomaly C(t) for Ψ Detection
# -----------------------------------------------------------------------------
def _cum_mag(time: np.ndarray, mag: np.ndarray, mc: float,
             tmin: float, tmax: float):
    """
    Construct cumulative magnitude anomaly C(t) to identify Ψ onset time.

    Based on Christophersen et al. (2024, SRL 95(6):3464-3481) Equations (1) and (2):
        C(t) = Σ[Mᵢ − (mc − 0.1)] − k·Δt

    where:
        - Mᵢ: magnitude of earthquake i
        - mc: completeness magnitude
        - k: detrending slope to remove background trend
        - Δt = t - tmin

    The minimum of the detrended C(t) identifies Tₘᵢₙ (onset time).

    Algorithm:
        1. Compute cumulative sum Σ[Mᵢ − (mc − 0.1)]
        2. Create step function representation (duplicating points for vertical jumps)
        3. Detrend: C'(t) = C(t) − k·(t − tmin)
        4. Find Tₘᵢₙ = argmin(C'(t))

    Args:
        time: Event times (decimal years) (np.ndarray)
        mag: Event magnitudes (np.ndarray)
        mc: Completeness magnitude threshold (float)
    tmin : float
        Search start time
    tmax : float
        Search end time (mainshock time)

    Returns:
    tuple
        (cum_aug, norm, t_onset) where:
        - cum_aug: cumulative sum at each time point
        - norm: detrended C(t)
        - t_onset: identified onset time (Tₘᵢₙ)

    Notes:
    The arrays time_aug and cum_aug must be aligned and unsorted to correctly
    compute the detrending at corresponding time points.
    """
    # Sort by time (safety check)
    idx = np.argsort(time)
    t = time[idx]
    dm = mag[idx] - (mc - 0.1)

    # Cumulative sum (height after each event)
    c = np.cumsum(dm)

    # Create step function representation with doubled time points
    # Structure: (tmin, 0), each event (t_i, c_{i-1}) -> (t_i, c_i), (tmax, c_last)
    # This ensures time_aug and cum_aug are properly aligned for pairwise operations
    time_aug = np.empty(2*len(t) + 2, dtype=float)
    cum_aug  = np.empty(2*len(t) + 2, dtype=float)

    time_aug[0] = tmin
    cum_aug[0]  = 0.0

    # Fill event-by-event: first "before jump" height, then "after jump" height
    # For event i (0-based), "before jump" height is c[i-1] (0 when i==0)
    for i in range(len(t)):
        j = 2*i + 1
        cum_before = 0.0 if i == 0 else c[i-1]
        time_aug[j]   = t[i]
        cum_aug[j]    = cum_before      # End of horizontal segment
        time_aug[j+1] = t[i]
        cum_aug[j+1]  = c[i]            # After vertical jump

    time_aug[-1] = tmax
    cum_aug[-1]  = c[-1] if len(c)>0 else 0.0

    # Detrend: remove linear background trend
    total = cum_aug[-1] - cum_aug[0]   # == Σdm (total magnitude anomaly)
    duration = (tmax - tmin) if (tmax > tmin) else 1.0
    k = total / duration  # Detrending slope
    norm = cum_aug - (time_aug - tmin) * k  # C'(t) = C(t) - k·Δt

    # Find onset time: argmin(C'(t))
    i0 = int(np.argmin(norm))
    t_onset = float(time_aug[i0])

    return cum_aug, norm, t_onset


def optimize_psi(
    main_time: float, tprior: float, tpost: float,
    loc: Tuple[float,float], radius: float,
    depth_range: Tuple[float,float],
    catalog: Tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray],
    heading: str, cutoff: float, mm: float,
    eq_name: Optional[str] = None,
    # Configurable parameters with paper defaults
    tp_ratio_min: float = 0.4,    # Minimum TP/T ratio (paper default 0.4)
    tp_ratio_max: float = 0.6,    # Maximum TP/T ratio (paper default 0.6)
    mp_minus_m_min: float = 0.4,  # Minimum MP-M- difference (paper default 0.4)
    mm_minus_mp_min: float = 0.4, # Minimum Mm-MP difference (paper default 0.4)
    r_min: float = 3.0,           # Minimum slope ratio r (paper default 3.0)
    min_group_size: int = 2,      # Minimum group size for fixed-effects slope
    mc_increment: float = 0.1,    # Increment for mc threshold (default 0.1)
    width_shrink_factor: float = 0.95, # Rectangle shrink factor (default 0.95)
    max_r_iterations: int = 81,   # Maximum R-loop iterations (default 81)
    max_t_iterations: int = 241,  # Maximum T-loop iterations (default 241)
    t_shrink_factor: float = 0.95, # T shrink factor (default 0.95)
):
    """
    Detect Ψ phenomenon using the rectangular algorithm from Christophersen et al. (2024).

    This implements the outer T-loop (Algorithm Step 1 in the paper Figure 2).
    For each lead-up time T, it calls trimcycle_early() to perform the inner R-loop
    and rectangle shrinking procedure.

    Algorithm Overview (from Christophersen et al. 2024, SRL 95(6):3464-3481):
        - Grid search over T (lead-up time) and R (spatial radius)
        - For each (T,R) combination, identify events and compute C(t) curve
        - Shrink rectangle and increase mc until valid Ψ is found
        - Apply selection criteria: r≥3, MP-M-≥0.4, Mm-MP≥0.4, Tmin in central 20%

    Args:
        main_time: Mainshock occurrence time (decimal years) (float)
        tprior: Initial backwards search time (years) (float)
        tpost: Forwards search time (years, typically 0) (float)
    loc : tuple
        Center location (lon, lat)
    radius : float
        Initial search radius (km)
    depth_range : tuple
        Depth range (min_depth, max_depth) in km
    catalog : tuple
        Earthquake catalog (time, lat, lon, depth, mag)
    heading : str
        Output file prefix
    cutoff : float
        Minimum magnitude threshold
    mm : float
        Mainshock magnitude
    eq_name : str, optional
        Mainshock identifier name

    Selection Criteria Parameters
    ------------------------------
    tp_ratio_min : float
        Minimum TP/T ratio (ensures Tmin in central time window, default 0.4)
    tp_ratio_max : float
        Maximum TP/T ratio (ensures Tmin in central time window, default 0.6)
    mp_minus_m_min : float
        Minimum MP - M- magnitude increase (default 0.4)
    mm_minus_mp_min : float
        Minimum Mm - MP magnitude difference (default 0.4)
    r_min : float
        Minimum slope ratio r = (rate after Tmin)/(rate before Tmin) (default 3.0)

    Algorithm Control Parameters
    -----------------------------
    min_group_size : int
        Minimum group size for fixed-effects regression (default 2)
    mc_increment : float
        Increment for completeness magnitude mc (default 0.1)
    width_shrink_factor : float
        Rectangle shrink factor per iteration (default 0.95)
    max_r_iterations : int
        Maximum iterations for R-loop (default 81)
    max_t_iterations : int
        Maximum iterations for T-loop (default 241)
    t_shrink_factor : float
        T shrink factor per iteration (default 0.95)

    Output
    ------
    Results are appended to <heading>.ou4a file with 14 columns:
        eq_name, Mm, MP, M-, r, tmin, Tmin, tmax, TP, AP,
        rn_max, rn_min, re_max, re_min

    Notes:
    This function implements the T-loop from Christophersen et al. (2024) Figure 2 Step 1.
    For each T value, it calls trimcycle_early() which implements Steps 2-9.

    References:
    Christophersen, A., Rhoades, D. A., & Hainzl, S. (2024).
    Algorithmic Identification of the Precursory Scale Increase Phenomenon
    in Earthquake Catalogs. Seismological Research Letters, 95(6), 3464-3481.
    """
    time, lat, lon, depth, mag = catalog
    clon, clat = loc

    # ---- Spatial mask: select events within rectangular region ----
    # Note: Using km units directly (not degree-based conversion)
    lat0, lat1 = clat - radius, clat + radius
    lon0, lon1 = clon - radius, clon + radius

    # Apply rectangular lat/lon mask and depth range mask
    mask_xy = (lat >= lat0) & (lat <= lat1) & (lon >= lon0) & (lon <= lon1)
    mask = mask_xy & (depth >= depth_range[0]) & (depth <= depth_range[1])

    # Extract events within spatial region
    time_s, lat_s, lon_s, mag_s = time[mask], lat[mask], lon[mask], mag[mask]

    # Compute relative distances (north and east components in km)
    nd = lat_s - clat  # North distance (km)
    ed = lon_s - clon  # East distance (km)

    # Set base completeness magnitude (max of cutoff or Mm - 2.5)
    mc_base = max(cutoff, mm - 2.5)

    # ---- T loop: Algorithm Step 1 (Christophersen et al. 2024 Figure 2) ----
    # Iteratively shrink lead-up time T and search for Ψ
    t_prior = tprior
    for _ in range(max_t_iterations):  # T shrink loop: ΔT × t_shrink_factor
        tmin = main_time - t_prior
        sel  = (time_s >= tmin) & (time_s < main_time)

        # Require at least 10 events for C(t) computation
        if np.sum(sel) >= 10:
            trimcycle_early(
                mag_s[sel], time_s[sel], nd[sel], ed[sel],
                tmin, main_time, mm, mc_base,
                heading=heading, eq_name=eq_name,
                tp_ratio_min=tp_ratio_min, tp_ratio_max=tp_ratio_max,
                mp_minus_m_min=mp_minus_m_min, mm_minus_mp_min=mm_minus_mp_min,
                r_min=r_min, mc_increment=mc_increment,
                width_shrink_factor=width_shrink_factor,
                max_r_iterations=max_r_iterations
            )

        # Shrink T for next iteration
        t_prior *= t_shrink_factor

def trimcycle_early(
    magnitude: np.ndarray, time: np.ndarray,
    ndist: np.ndarray, edist: np.ndarray,
    tmin: float, tmax: float, mm: float, mc_base: float,
    heading: str, eq_name: Optional[str] = None,
    # Configurable parameters with paper defaults
    tp_ratio_min: float = 0.4,    # Minimum TP/T ratio (paper default 0.4)
    tp_ratio_max: float = 0.6,    # Maximum TP/T ratio (paper default 0.6)
    mp_minus_m_min: float = 0.4,  # Minimum MP-M- difference (paper default 0.4)
    mm_minus_mp_min: float = 0.4, # Minimum Mm-MP difference (paper default 0.4)
    r_min: float = 3.0,           # Minimum slope ratio r (paper default 3.0)
    mc_increment: float = 0.1,    # Increment for mc threshold (default 0.1)
    width_shrink_factor: float = 0.95, # Rectangle shrink factor (default 0.95)
    max_r_iterations: int = 81,   # Maximum R-loop iterations (default 81)
):
    """
    Core rectangular algorithm implementing R-loop and rectangle shrinking (Christophersen et al. 2024 Steps 2-9).

    This function performs the inner loop of the Ψ detection algorithm:
        - Step 2: Select events in rectangle (R × R)
        - Step 3-4: Check M1 ≤ Mm-0.5 and NS ≥ 10
        - Step 5-6: Compute C(t), find Tmin, identify precursor events
        - Step 7: Shrink rectangle to fit precursor events
        - Step 8: Increase mc and check selection criteria
        - Step 9: Shrink R and repeat

    Algorithm Flow (from Christophersen et al. 2024, SRL 95(6):3464-3481 Figure 2):
        FOR each R value (shrinking by width_shrink_factor):
            SELECT events in rectangle
            IF M1 > Mm-0.5:
                Shrink rectangle AND increase mc
                CONTINUE
            COMPUTE C(t) curve → find Tmin
            IDENTIFY precursor events (t ≥ Tmin)
            SHRINK rectangle to fit precursors
            INCREASE mc until valid Ψ found
            CHECK selection criteria:
                - r ≥ r_min (rate increase)
                - MP - M- ≥ mp_minus_m_min (magnitude increase)
                - Mm - MP ≥ mm_minus_mp_min (mainshock larger)
                - Tmin in central 20% of time window
            IF criteria met:
                SAVE Ψ identification
        END FOR

    Args:
        magnitude: Event magnitudes (np.ndarray)
        time: Event times (decimal years) (np.ndarray)
        ndist: North distances from mainshock (km) (np.ndarray)
    edist : np.ndarray
        East distances from mainshock (km)
    tmin : float
        Search window start time
    tmax : float
        Search window end time (mainshock time)
    mm : float
        Mainshock magnitude
    mc_base : float
        Base completeness magnitude threshold
    heading : str
        Output file prefix
    eq_name : str, optional
        Mainshock identifier name

    Selection Criteria Parameters
    ------------------------------
    tp_ratio_min : float
        Minimum TP/T ratio (ensures Tmin in central 20%, default 0.4)
    tp_ratio_max : float
        Maximum TP/T ratio (ensures Tmin in central 20%, default 0.6)
    mp_minus_m_min : float
        Minimum MP - M- magnitude increase (default 0.4)
    mm_minus_mp_min : float
        Minimum Mm - MP magnitude difference (default 0.4)
    r_min : float
        Minimum slope ratio r (default 3.0)

    Algorithm Control Parameters
    -----------------------------
    mc_increment : float
        Increment for mc threshold (default 0.1)
    width_shrink_factor : float
        Rectangle shrink factor per iteration (default 0.95)
    max_r_iterations : int
        Maximum iterations for R-loop (default 81)

    Output
    ------
    Valid Ψ identifications are appended to <heading>.ou4a file.
    Each line contains 14 columns: eq_name, Mm, MP, M-, r, tmin, Tmin, tmax,
    TP, AP, rn_max, rn_min, re_max, re_min

    Notes:
    This implements the core rectangular algorithm from Christophersen et al. (2024) Steps 2-9.
    It is called by optimize_psi() for each T value in the T-loop.
    """
    Δkm = 0.5  # Small buffer for rectangle expansion
    if magnitude.size == 0:
        return

    # Initialize with maximum extent of events
    r0 = max(float(np.max(np.abs(ndist))), float(np.max(np.abs(edist)))) + Δkm
    mc_cur = float(mc_base)
    best: Optional[Dict[str, Any]] = None
    optratio = 1.0

    # Start from full initial radius
    r_current = r0

    # ---- R-loop: Algorithm Step 9 (Christophersen et al. 2024) ----
    # Shrink R iteratively by width_shrink_factor
    for p in range(max_r_iterations):
        # Step 2: Select events in current rectangle (R × R)
        rn_min = -r_current
        rn_max =  r_current
        re_min = -r_current
        re_max =  r_current

        # Continue searching until valid Ψ found or proven impossible
        search_continue = True
        while search_continue:
            # Select events in current rectangle with current mc
            sel = (
                (ndist >= rn_min) & (ndist <= rn_max) &
                (edist >= re_min) & (edist <= re_max) &
                (magnitude >= mc_cur)
            )
            n_sel = int(np.sum(sel))

            # Step 4: Check NS ≥ 10? (minimum events for C(t) computation)
            if n_sel < 10:
                search_continue = False
                continue

            # Step 3: Check M1 ≤ Mm-0.5? (largest event in selection)
            m1 = float(np.max(magnitude[sel]))

            if m1 > (mm - 0.5):
                # Right branch of flowchart: M1 > Mm-0.5
                # Check N2 ≥ 3?
                if n_sel < 3:
                    search_continue = False
                    continue

                # Shrink rectangle AND increase mc (flowchart right path)
                # Shrink R
                width_ns = rn_max - rn_min
                width_ew = re_max - re_min
                center_ns = (rn_max + rn_min) / 2
                center_ew = (re_max + re_min) / 2

                width_ns *= width_shrink_factor
                width_ew *= width_shrink_factor

                rn_min = center_ns - width_ns / 2
                rn_max = center_ns + width_ns / 2
                re_min = center_ew - width_ew / 2
                re_max = center_ew + width_ew / 2

                # Increase mc
                mc_cur = round(mc_cur + mc_increment, 10)
                continue
            
            # Left branch of flowchart: M1 ≤ Mm-0.5
            # Step 5: Compute C(t) curve and find Tmin (onset time)
            cum_aug, norm_aug, t_onset = _cum_mag(
                time[sel], magnitude[sel], mc_cur, tmin, tmax
            )

            # Step 6: Identify precursor events (t ≥ Tmin)
            prec_sel = sel & (time >= t_onset)
            n_prec = int(np.sum(prec_sel))

            # Check if sufficient precursor events (≥3)
            if n_prec < 3:
                search_continue = False
                continue

            # Step 7: Shrink rectangle to fit precursor events
            max_ns_dist = float(np.max(np.abs(ndist[prec_sel]))) if n_prec > 0 else 0
            max_ew_dist = float(np.max(np.abs(edist[prec_sel]))) if n_prec > 0 else 0

            # Shrink using max(Rmax/2, Δ + max_distance)
            half_width_ns = (rn_max - rn_min) / 2  # Current half-width
            half_width_ew = (re_max - re_min) / 2

            new_half_ns = max(half_width_ns / 2, Δkm + max_ns_dist)
            new_half_ew = max(half_width_ew / 2, Δkm + max_ew_dist)

            # Update rectangle bounds (centered at mainshock)
            rn_min2, rn_max2 = -new_half_ns, new_half_ns
            re_min2, re_max2 = -new_half_ew, new_half_ew

            # Select events in shrunk rectangle
            sel_shrink = (
                (ndist >= rn_min2) & (ndist <= rn_max2) &
                (edist >= re_min2) & (edist <= re_max2) &
                (magnitude >= mc_cur)
            )

            if np.sum(sel_shrink) < 10:
                search_continue = False
                continue

            # Step 8: Increase mc to find valid Ψ identification
            mc_found = False
            current_mc = mc_cur
            best_result = None
            
            while True:
                # Compute results for current mc value
                curr_sel = (
                    (ndist >= rn_min2) & (ndist <= rn_max2) &
                    (edist >= re_min2) & (edist <= re_max2) &
                    (magnitude >= current_mc)
                )

                if np.sum(curr_sel) < 10:
                    break

                # Call parameters_select to check selection criteria
                curr_res = parameters_select(
                    magnitude[curr_sel], time[curr_sel],
                    ndist[curr_sel], edist[curr_sel],
                    tmin, tmax, mm, optratio,
                    rn_min2, rn_max2, re_min2, re_max2, current_mc,
                    tp_ratio_min=tp_ratio_min, tp_ratio_max=tp_ratio_max,
                    mp_minus_m_min=mp_minus_m_min, mm_minus_mp_min=mm_minus_mp_min,
                    r_min=r_min
                )

                if curr_res is None:
                    break

                curr_t_onset = float(curr_res["time_onset"])
                curr_prior = int(np.sum(curr_sel & (time < curr_t_onset)))

                # Check prior event count (≥3)
                if curr_prior < 3:
                    break

                # Current mc value is valid, save result
                mc_found = True
                best_result = curr_res

                # Try next mc value
                next_mc = round(current_mc + mc_increment, 10)
                current_mc = next_mc

            # If valid mc value found
            if mc_found and best_result is not None:
                # Check final selection criteria:
                # 1. Tmin in central 20% (TP/T ∈ [0.4, 0.6])
                # 2. MP - M- ≥ 0.4 (magnitude increase)
                # 3. Mm - MP ≥ 0.4 (mainshock larger than precursor)
                # 4. r ≥ 3 (rate increase)

                tp_ratio = (best_result["tp"] / (tmax - tmin))
                if not (tp_ratio_min <= tp_ratio <= tp_ratio_max):
                    search_continue = False
                    continue

                if ((mm - best_result["mp"]) < mm_minus_mp_min or
                    (best_result["mp"] - best_result["mminus"]) < mp_minus_m_min or
                    best_result["sloperatio"] < r_min):
                    search_continue = False
                    continue

                # Save valid Ψ identification
                final = dict(best_result)
                final["ap"] = (rn_max2 - rn_min2) * (re_max2 - re_min2)  # km²
                final["rn_max"] = rn_max2
                final["rn_min"] = rn_min2
                final["re_max"] = re_max2
                final["re_min"] = re_min2
                final["mc"] = current_mc

                # Keep identification with largest sloperatio
                if (best is None) or (final["sloperatio"] > best["sloperatio"]):
                    best = final
                    optratio = max(optratio, final["sloperatio"])

                search_continue = False
            else:
                search_continue = False

        # Step 9: Shrink R and reset mc for next iteration
        r_current *= width_shrink_factor
        mc_cur = float(mc_base)  # Reset mc to base value

    # ---- Output results ----
    # Write valid Ψ identification to .ou4a file
    if best is not None:
        ident = eq_name if eq_name is not None else heading
        row = [
            ident, round(mm, 4),
            round(best["mp"], 4), round(best["mminus"], 4),
            round(best["sloperatio"], 4),
            round(tmin, 4), round(best["time_onset"], 4), round(tmax, 4),
            round(best["tp"], 4), round(best["ap"], 4),
            round(best["rn_max"], 2), round(best["rn_min"], 2),
            round(best["re_max"], 2), round(best["re_min"], 2),
        ]
        with open(f"{heading}.ou4a", "a", encoding="utf-8") as f:
            f.write(" ".join(map(str, row)) + "\n")

def parameters_select(
    magnitude: np.ndarray, time: np.ndarray,
    ndist: np.ndarray, edist: np.ndarray,
    tmin: float, tmax: float, mm: float,
    optratio_prev: float,
    rn_min: float, rn_max: float, re_min: float, re_max: float,
    mc_threshold: Optional[float] = None,
    # Configurable parameters with paper defaults
    tp_ratio_min: float = 0.4,    # Minimum TP/T ratio (paper default 0.4)
    tp_ratio_max: float = 0.6,    # Maximum TP/T ratio (paper default 0.6)
    mp_minus_m_min: float = 0.4,  # Minimum MP-M- difference (paper default 0.4)
    mm_minus_mp_min: float = 0.4, # Minimum Mm-MP difference (paper default 0.4)
    r_min: float = 3.0,           # Minimum slope ratio r (paper default 3.0)
) -> Optional[Dict[str, Any]]:
    """
    Check Ψ selection criteria (Christophersen et al. 2024 Step 6).

    Applies the four selection criteria from Christophersen et al. (2024, SRL 95(6):3464-3481):
        1. Tmin in central 20% of time window (TP/T ∈ [0.4, 0.6])
        2. MP - M- ≥ 0.4 (magnitude increase before precursor)
        3. Mm - MP ≥ 0.4 (mainshock larger than precursor)
        4. r ≥ 3 (rate increase ratio)

    Args:
        magnitude: Event magnitudes (np.ndarray)
        time: Event times (decimal years) (np.ndarray)
        ndist: North distances from mainshock (km) (np.ndarray)
    edist : np.ndarray
        East distances from mainshock (km)
    tmin : float
        Search window start time
    tmax : float
        Search window end time (mainshock time)
    mm : float
        Mainshock magnitude
    optratio_prev : float
        Previous best slope ratio
    rn_min, rn_max : float
        Rectangle bounds in north direction (km)
    re_min, re_max : float
        Rectangle bounds in east direction (km)
    mc_threshold : float, optional
        Completeness magnitude threshold

    Selection Criteria Parameters
    ------------------------------
    tp_ratio_min : float
        Minimum TP/T ratio (default 0.4)
    tp_ratio_max : float
        Maximum TP/T ratio (default 0.6)
    mp_minus_m_min : float
        Minimum MP - M- difference (default 0.4)
    mm_minus_mp_min : float
        Minimum Mm - MP difference (default 0.4)
    r_min : float
        Minimum slope ratio r (default 3.0)

    Returns:
    dict or None
        Dictionary with Ψ parameters if criteria met, None otherwise.
        Keys: mp, mminus, sloperatio, time_onset, tp, ap, optratio

    Notes:
    This function implements the selection criteria check (Step 6) from Christophersen et al. (2024).
    It uses _cum_mag() to compute the C(t) curve and find Tmin.

    MP is computed as the mean of the 3 largest precursor magnitudes.
    M- is computed as the mean of the 3 largest prior magnitudes (before Tmin).
    AP is computed from the rectangle bounds provided by the caller.
    """
    if magnitude.size < 10 or (tmax - tmin) <= 0:
        return None
    mc = float(mc_threshold) if mc_threshold is not None else float(np.min(magnitude))

    # ---- Compute C(t) curve and find Tmin (onset time) ----
    cum_aug, norm_aug, t_onset = _cum_mag(time, magnitude, mc, tmin, tmax)
    idx_onset = int(np.argmin(norm_aug))

    # Check Tmin is within time window
    if not (tmin < t_onset < tmax):
        return None

    # ---- Calculate slope ratio r = (rate after Tmin) / (rate before Tmin) ----
    slope1 = cum_aug[idx_onset] / (t_onset - tmin)  # Rate before Tmin
    slope2 = (cum_aug[-1] - cum_aug[idx_onset]) / (tmax - t_onset)  # Rate after Tmin

    if slope1 <= 0:
        return None

    r = slope2 / slope1  # Slope ratio (rate increase)

    # ---- Identify precursor and prior events ----
    prec_idx = time >= t_onset  # Precursor events (after Tmin)
    if np.sum(prec_idx) < 3:
        return None

    prior_idx = ~prec_idx  # Prior events (before Tmin)

    # ---- Compute MP and M- (mean of 3 largest) ----
    mp = float(np.mean(np.sort(magnitude[prec_idx])[-3:]))  # Mean of 3 largest precursors

    if np.sum(prior_idx) == 0:
        mminus = float(mc)  # No prior events: use mc
    else:
        # Mean of up to 3 largest prior events
        mminus = float(np.mean(np.sort(magnitude[prior_idx])[-min(3, np.sum(prior_idx)):]))

    # ---- Apply selection criteria (Christophersen et al. 2024 Step 6) ----
    tp = tmax - t_onset  # Precursor time (lead time)
    tp_ratio = tp / (tmax - tmin)

    # Criterion 1: Tmin in central 20% of time window
    if not (tp_ratio_min <= tp_ratio <= tp_ratio_max):
        return None

    # Criteria 2-4: Magnitude differences and rate increase
    if (mm - mp) < mm_minus_mp_min or (mp - mminus) < mp_minus_m_min or r < r_min:
        return None

    # ---- Compute precursor area from rectangle bounds ----
    ap = (rn_max - rn_min) * (re_max - re_min)  # km²

    return {
        "mp": mp,                       # Precursor magnitude
        "mminus": mminus,               # Prior magnitude level
        "sloperatio": r,                # Rate increase ratio
        "time_onset": t_onset,          # Onset time (Tmin)
        "tp": tp,                       # Precursor time (lead time)
        "ap": ap,                       # Precursor area
        "optratio": max(r, optratio_prev),  # Maximum slope ratio seen
    }

