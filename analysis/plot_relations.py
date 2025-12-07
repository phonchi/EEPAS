# -*- coding: utf-8 -*-
"""
Ψ Phenomenon Scaling Relations Analysis

This module analyzes the scaling relations from Ψ identifications using
fixed-effects regression to remove within-mainshock AP-TP trade-offs.

Based on:
    - Christophersen et al. (2024, SRL 95(6):3464-3481) Section 2.4
    - The paper Section 5.2 (two-stage estimation)

Scaling Relations:
    1. log₁₀(AP) vs MP  (precursor area vs precursor magnitude)
    2. log₁₀(TP) vs MP  (precursor time vs precursor magnitude)
    3. Mm vs MP         (mainshock magnitude vs precursor magnitude)
"""
import numpy as np
import pandas as pd
import math

# Matplotlib: use basic interface only
import matplotlib.pyplot as plt

# Use scipy.stats.linregress if available; fallback to numpy version
try:
    from scipy import stats
except Exception:
    stats = None

# ---- Shared: Column names ----
CANONICAL_14 = [
    "eq_name","mm","mp","mminus","sloperatio",
    "tmin","time_onset","tmax","tp","ap",
    "rn_max","rn_min","re_max","re_min"
]

# ---- Utility: Check if string is numeric ----
def _isfloat(v):
    """Check if value can be converted to float."""
    try:
        float(v); return True
    except Exception:
        return False

# ---- File reading: Compatible with 14 or wider columns ----
def _read_psi_any_layout(psi_file: str) -> pd.DataFrame:
    """
    Read Ψ identification file with 14 or more columns.

    Compatible with 14-column (canonical) and wider .ou4 files.
    Only keeps first 14 columns, converts to standard names, filters out ap<=0 or tp<=0.

    Args:
        psi_file: Path to .ou4 file

    Returns:
        DataFrame with 14 standardized columns

    Raises:
        ValueError: If file has fewer than 14 columns
    """
    raw = pd.read_csv(psi_file, sep=r"\s+", header=None, dtype=str)
    ncol = raw.shape[1]
    if ncol < 14:
        raise ValueError(f"{psi_file} has {ncol} columns < 14, incorrect format.")

    # Assume first 14 columns are canonical
    df = raw.iloc[:, :14].copy()
    df.columns = CANONICAL_14

    # If eq_name is mostly numeric, find least numeric column for name
    sample = df["eq_name"].astype(str).head(100)
    num_ratio = sum(1 for v in sample if _isfloat(v)) / max(1, len(sample))
    if num_ratio > 0.95:
        best_j = 0; best_nonnum = -1
        for j in range(min(ncol, 20)):
            s = raw.iloc[:, j].astype(str).head(100)
            nonnum = sum(1 for v in s if not _isfloat(v))
            if nonnum > best_nonnum:
                best_nonnum = nonnum; best_j = j
        name_col = raw.iloc[:, best_j].astype(str)
        num_cols = raw.drop(raw.columns[best_j], axis=1).iloc[:, :13]
        num_cols.columns = [c for c in CANONICAL_14 if c != "eq_name"]
        df = pd.concat([name_col, num_cols], axis=1)
        df.columns = CANONICAL_14

    # Type conversion
    for c in CANONICAL_14[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Filter invalid rows
    df = df[(df["ap"] > 0) & (df["tp"] > 0)].copy()
    df["eq_name"] = df["eq_name"].astype(str).str.strip()
    return df

# ---- Fixed-effects (common slope) estimation; fallback to pooled OLS if denominator is 0 ----
def _fixed_effects_slope_safe(x, y, group, min_group_size=2):
    """
    Estimate common slope using fixed-effects regression (within-group demeaning).

    Removes within-mainshock trade-off by demeaning x and y within each mainshock,
    then computing pooled slope across all demeaned observations.

    Args:
        x: Independent variable (array-like)
        y: Dependent variable (array-like)
        group: Group identifiers (mainshock names, array-like)
        min_group_size: Minimum group size to include (default: 2)

    Returns:
        Common slope estimate (b_AT or b_TA). Falls back to pooled OLS if
        denominator is zero or no groups meet minimum size.
    """
    tmp = pd.DataFrame({'x': x, 'y': y, 'g': group})
    sz = tmp.groupby('g')['g'].transform('size')
    tmp = tmp[sz >= min_group_size].copy()
    if len(tmp) == 0:
        # Fallback to pooled OLS
        x_all = np.asarray(x, float); y_all = np.asarray(y, float)
        den = np.sum((x_all - x_all.mean())**2)
        return float(np.sum((x_all - x_all.mean())*(y_all - y_all.mean())) / den) if den>0 else np.nan

    x_dm = tmp['x'] - tmp.groupby('g')['x'].transform('mean')
    y_dm = tmp['y'] - tmp.groupby('g')['y'].transform('mean')
    den = float(np.sum(x_dm**2))
    if den <= 0:
        x_all = np.asarray(x, float); y_all = np.asarray(y, float)
        den2 = np.sum((x_all - x_all.mean())**2)
        return float(np.sum((x_all - x_all.mean())*(y_all - y_all.mean())) / den2) if den2>0 else np.nan
    num = float(np.sum(x_dm * y_dm))
    return num / den

# ---- Numpy version of linregress (if no SciPy) ----
def _linregress_np(x, y):
    """
    Simple linear regression using NumPy (fallback when SciPy unavailable).

    Args:
        x: Independent variable (array-like)
        y: Dependent variable (array-like)

    Returns:
        Result object with slope, intercept, rvalue attributes.
        Returns None if insufficient data.
    """
    x = np.asarray(x, float); y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]; y = y[mask]
    if len(x) < 2:
        return None
    xm = x.mean(); ym = y.mean()
    cov = np.sum((x - xm)*(y - ym))
    var = np.sum((x - xm)**2)
    if var <= 0:
        return None
    slope = cov / var
    intercept = ym - slope*xm
    r_num = cov
    r_den = np.sqrt(var*np.sum((y - ym)**2))
    r = r_num / r_den if r_den>0 else np.nan
    class Res: pass
    res = Res()
    res.slope = float(slope)
    res.intercept = float(intercept)
    res.rvalue = float(r)
    res.pvalue = np.nan
    res.stderr = np.nan
    return res

# ---- For plotting: 95% prediction interval (accurate version) ----
def prediction_interval(x_data, x_plot_range, slope, intercept, std_err):
    """
    Compute 95% prediction interval for linear regression.

    Args:
        x_data: Original x values used for fitting (array-like)
        x_plot_range: X coordinates for plotting (array-like)
        slope: Regression slope (float)
        intercept: Regression intercept (float)
        std_err: Standard error of residuals, sigma = sqrt(SSE/(n-2)) (float)

    Returns:
        Tuple (y_pred, y_low, y_high) - predicted values and 95% prediction
        interval bounds. Returns (y_pred, None, None) if insufficient data.
    """
    x_data = np.asarray(x_data, float)
    x_plot_range = np.asarray(x_plot_range, float)
    n = len(x_data)
    if n < 2:
        return None, None, None
    x_mean = np.mean(x_data)
    y_pred = intercept + slope * x_plot_range
    denom = np.sum((x_data - x_mean)**2)
    if denom <= 0:
        return y_pred, None, None
    se_pred = std_err * np.sqrt(1.0 + 1.0/n + ((x_plot_range - x_mean)**2)/denom)
    z = 1.96  # 95% confidence level
    return y_pred, y_pred - z*se_pred, y_pred + z*se_pred

# ---- Main function: File reading, fixed-effects projection, regression, plotting ----
def analyze_scaling_relations(psi_file="optimized_psi.ou4", output_prefix="scaling_final"):
    """
    Analyze Ψ phenomenon scaling relations using fixed-effects regression.

    This function implements the two-stage estimation procedure to estimate initial
    values for EEPAS model parameters. It removes the within-mainshock AP-TP trade-off
    using fixed-effects regression, then fits scaling relations.

    Args:
        psi_file: Input file with deduplicated Ψ identifications (.ou4 format)
        output_prefix: Prefix for output files (plots and CSV)

    Algorithm:
        1. Read all Ψ identifications from file
        2. Convert units (years → days, km²) and compute logarithms
        3. Estimate fixed-effects common slopes (b_AT, b_TA) to remove trade-off
        4. Project each mainshock's identifications to representative point
        5. Fit linear regressions on representative points:
           - log₁₀(AP) vs MP → b_A (spatial scaling), sigma_A
           - log₁₀(TP) vs MP → b_T, a_T (temporal scaling), sigma_T
           - Mm vs MP → b_M, a_M (magnitude scaling), sigma_M
        6. Generate plots with 95% prediction intervals

    Output Files:
        - {output_prefix}_projected_points.csv: Representative points per mainshock
        - {output_prefix}_mp_relations.png: Plots of AP and TP vs MP (semi-log)
        - {output_prefix}_mm_mp.png: Plot of Mm vs MP (linear scale)

    Returns:
        None (writes output files directly)

    Note:
        Estimated parameters (b_A, sigma_A, a_T, b_T, sigma_T, a_M, b_M, sigma_M)
        can be used as initial values for EEPAS learning.

    References:
        Christophersen et al. (2024). Algorithmic Identification of the Precursory
        Scale Increase Phenomenon in Earthquake Catalogs. SRL 95(6):3464-3481.
    """
    print("="*60)
    print("=== Ψ Scaling Relations Analysis (Projected Means + Plots) ===")

    # 1) Read file (all identifications)
    df = _read_psi_any_layout(psi_file)
    print(f"✅ Successfully read {len(df)} total Ψ identification records.")
    n_eq = df['eq_name'].nunique()
    print(f"ℹ️  Number of mainshocks (unique eq_name) = {n_eq}")
    print("ℹ️  Number of identifications per mainshock (top 10):")
    print(df['eq_name'].value_counts().head(10))

    # 2) Unit conversion and logarithms
    df['tp_days'] = df['tp'].astype(float) * 365.25
    df = df[(df['ap'] > 0) & (df['tp_days'] >= 1.0)].copy()
    if len(df) == 0:
        print("⚠️  All rows filtered out (ap<=0 or tp_days<1).")
        return

    df['log_ap_km2'] = np.log10(df['ap'].astype(float))
    df['log_tp']     = np.log10(df['tp_days'].astype(float))

    # 3) Fixed-effects common slope (remove trade-off)
    b_AT = _fixed_effects_slope_safe(df['log_tp'].values,
                                     df['log_ap_km2'].values,
                                     df['eq_name'].values,
                                     min_group_size=2)
    b_TA = _fixed_effects_slope_safe(df['log_ap_km2'].values,
                                     df['log_tp'].values,
                                     df['eq_name'].values,
                                     min_group_size=2)
    xbar = float(df['log_tp'].mean())
    ybar = float(df['log_ap_km2'].mean())

    # 4) Generate representative points per mainshock (projected means) using Eqs (13)(14)
    rows = []
    mm_first = df.groupby('eq_name', sort=False)['mm'].first()
    mp_mean  = df.groupby('eq_name', sort=False)['mp'].mean()
    for g, dfg in df.groupby('eq_name', sort=False):
        x_i = float(dfg['log_tp'].mean())
        y_i = float(dfg['log_ap_km2'].mean())
        a_i    = y_i - b_AT * x_i
        logA_p = a_i + b_AT * xbar   # Eq (13): projected mean of log10(A)
        a_i_p  = x_i - b_TA * y_i
        logT_p = a_i_p + b_TA * ybar # Eq (14): projected mean of log10(T)
        rows.append({
            'eq_name': g,
            'mm': float(mm_first.loc[g]),
            'mp': float(mp_mean.loc[g]),
            'log_ap_km2_proj': float(logA_p),
            'log_tp_proj': float(logT_p),
        })
    proj = pd.DataFrame(rows)
    print(f"✅ Generated {len(proj)} mainshock representative points with trade-off removed (should equal number of mainshocks).")
    proj.to_csv(f"{output_prefix}_projected_points.csv", index=False)

    # 5) Linear regression (using projected representative points)
    def _linreg(x, y):
        """Perform linear regression and compute residual standard error."""
        x = np.asarray(x, float); y = np.asarray(y, float)
        mask = np.isfinite(x) & np.isfinite(y)
        x = x[mask]; y = y[mask]
        if len(x) < 2:
            return None, None
        if stats is not None:
            res = stats.linregress(x, y)
            slope, intercept, r2, pval = res.slope, res.intercept, res.rvalue**2, getattr(res, "pvalue", np.nan)
        else:
            res = _linregress_np(x, y)
            slope, intercept, r2, pval = res.slope, res.intercept, res.rvalue**2, np.nan
        # Residual standard deviation (for prediction interval)
        yhat = intercept + slope * x
        sse = float(np.sum((y - yhat)**2))
        std_err = math.sqrt(sse / max(1, len(x) - 2))
        return (slope, intercept, r2, pval, std_err), mask

    # A: log10(A[km2]) vs MP
    regA, _ = _linreg(proj['mp'], proj['log_ap_km2_proj'])
    # T: log10(T[days]) vs MP
    regT, _ = _linreg(proj['mp'], proj['log_tp_proj'])
    # M: Mm vs MP
    regM, _ = _linreg(proj['mp'], proj['mm'])

    print("\n--- Initial Value Estimates for MLE ---")
    if regA:
        slope_A, intercept_A, r2_A, p_A, std_err_A = regA
        # Calculate sigma_A initial value using simplified estimation method
        c_for_sigma_A = 0.33
        a_A = intercept_A
        sigma_A_initial = c_for_sigma_A * (10**(a_A / 2.0))
        print(f"Relation 1 (Area): log10(A_P[km²]) = {intercept_A:.4f} + {slope_A:.4f}*M_P "
              f"(R² = {r2_A:.4f}, p-value = {p_A:.6f})")
        print(f"sigma_A initial value (from simplified estimation): {sigma_A_initial:.4f}")
        print(f"  (Formula: 0.33 * 10^(a_A / 2), where a_A = {a_A:.4f})")
    else:
        print("sigma_A initial value: Insufficient samples.")

    if regT:
        slope_T, intercept_T, r2_T, p_T, std_err_T = regT
        print(f"Relation 2 (Time): log10(T_P[days]) = {intercept_T:.4f} + {slope_T:.4f}*M_P "
              f"(R² = {r2_T:.4f}, p-value = {p_T:.6f})")
        print(f"sigma_T initial value (residual std from log(T_p) vs M_P): {std_err_T:.4f}")
    else:
        print("sigma_T initial value: Insufficient samples.")

    if regM:
        slope_M, intercept_M, r2_M, p_M, std_err_M = regM
        print(f"Relation 3 (Mag):  M_m = {intercept_M:.4f} + {slope_M:.4f}*M_P "
              f"(R² = {r2_M:.4f}, p-value = {p_M:.6f})")
        print(f"sigma_M initial value (residual std from M_m vs M_P): {std_err_M:.4f}")
    else:
        print("sigma_M initial value: Insufficient samples.")

    # 6) Prepare plotting data
    # All identifications: use original df
    data_all = pd.DataFrame({
        "mp": df["mp"].astype(float),
        "ap_1000km2": df["ap"].astype(float) / 1000.0,   # Convert to 10^3 km²
        "tp_days": df["tp_days"].astype(float),
        "mm": df["mm"].astype(float)
    })
    # Representative points per mainshock (after projection): convert from proj back to linear scale
    mean_data = pd.DataFrame({
        "eq_name": proj["eq_name"].values,
        "mp": proj["mp"].astype(float).values,
        "ap_1000km2": (10.0**proj["log_ap_km2_proj"].astype(float).values) / 1000.0,
        "tp_days": 10.0**proj["log_tp_proj"].astype(float).values,
        "mm": proj["mm"].astype(float).values
    })

    # 7) X range for prediction interval (based on MP range of representative points)
    if len(mean_data) >= 2:
        x_range_mp = np.linspace(mean_data['mp'].min() - 0.2,
                                 mean_data['mp'].max() + 0.2, 100)
    else:
        x_range_mp = np.linspace(df['mp'].min() - 0.2,
                                 df['mp'].max() + 0.2, 100)

    # 8) Plot (a), (b): semi-log y (fixed colors: gray=all, blue=representative, black=line)
    plt.figure(figsize=(15, 6))

    # (a) MP vs AP (10^3 km²) — log y-axis
    ax1 = plt.subplot(1, 2, 1)
    ax1.scatter(data_all['mp'], data_all['ap_1000km2'],
                alpha=0.15, s=10, color='tab:gray', label='All Identifications')
    ax1.scatter(mean_data['mp'], mean_data['ap_1000km2'],
                alpha=0.8, s=25, color='tab:blue', label='Mean per Mainshock')

    if regA:
        y_fit_A, lower_A, upper_A = prediction_interval(mean_data['mp'], x_range_mp,
                                                        slope_A, intercept_A, std_err_A)
        # Regression plotted on linear scale (original regression on log10(A[km²]))
        ax1.semilogy(x_range_mp, (10**y_fit_A)/1000.0,
                     color='k', linewidth=2,
                     label=f'$\\log_{{10}}A_P = {intercept_A:.2f} + {slope_A:.2f}M_P$')
        if lower_A is not None:
            ax1.semilogy(x_range_mp, (10**lower_A)/1000.0,
                         color='k', linestyle='--', linewidth=1.5, label='95% PI')
            ax1.semilogy(x_range_mp, (10**upper_A)/1000.0,
                         color='k', linestyle='--', linewidth=1.5)

    ax1.set_xlabel('$M_P$', fontsize=12)
    ax1.set_ylabel('$A_P$ (10³ km²)', fontsize=12)
    ax1.grid(True, which='both', ls='-', alpha=0.2)
    ax1.legend(loc='best', fontsize=10)
    ax1.set_title('(a) $A_P$ vs $M_P$', fontsize=14)

    # (b) MP vs TP (days) — log y-axis
    ax2 = plt.subplot(1, 2, 2)
    ax2.scatter(data_all['mp'], data_all['tp_days'],
                alpha=0.15, s=10, color='tab:gray', label='All Identifications')
    ax2.scatter(mean_data['mp'], mean_data['tp_days'],
                alpha=0.8, s=25, color='tab:blue', label='Mean per Mainshock')

    if regT:
        y_fit_T, lower_T, upper_T = prediction_interval(mean_data['mp'], x_range_mp,
                                                        slope_T, intercept_T, std_err_T)
        ax2.semilogy(x_range_mp, 10**y_fit_T,
                     color='k', linewidth=2,
                     label=f'$\\log_{{10}}T_P = {intercept_T:.2f} + {slope_T:.2f}M_P$')
        if lower_T is not None:
            ax2.semilogy(x_range_mp, 10**lower_T,
                         color='k', linestyle='--', linewidth=1.5, label='95% PI')
            ax2.semilogy(x_range_mp, 10**upper_T,
                         color='k', linestyle='--', linewidth=1.5)

    ax2.set_xlabel('$M_P$', fontsize=12)
    ax2.set_ylabel('$T_P$ (days)', fontsize=12)
    ax2.grid(True, which='both', ls='-', alpha=0.2)
    ax2.legend(loc='best', fontsize=10)
    ax2.set_title('(b) $T_P$ vs $M_P$', fontsize=14)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_mp_relations.png", dpi=300, bbox_inches='tight')
    print(f"\nSaved M_P relation plots to {output_prefix}_mp_relations.png")

    # 9) Plot (c): Mm vs MP (linear y)
    plt.figure(figsize=(7, 6))
    ax3 = plt.gca()
    ax3.scatter(data_all['mp'], data_all['mm'],
                alpha=0.15, s=10, color='tab:gray', label='All Identifications')
    ax3.scatter(mean_data['mp'], mean_data['mm'],
                alpha=0.8, s=25, color='tab:blue', label='Mean per Mainshock')

    if regM:
        # Extract regression parameters from regM tuple
        slope_M, intercept_M, _, _, std_err_M = regM
        y_fit_M, lower_M, upper_M = prediction_interval(mean_data['mp'], x_range_mp,
                                                        slope_M, intercept_M, std_err_M)
        ax3.plot(x_range_mp, y_fit_M,
                 color='k', linewidth=2,
                 label=f'$M_m = {intercept_M:.2f} + {slope_M:.2f}M_P$')
        if lower_M is not None:
            ax3.plot(x_range_mp, lower_M, color='k', linestyle='--', linewidth=1.5, label='95% PI')
            ax3.plot(x_range_mp, upper_M, color='k', linestyle='--', linewidth=1.5)

    ax3.set_xlabel('$M_P$', fontsize=12)
    ax3.set_ylabel('$M_m$', fontsize=12)
    ax3.grid(True, alpha=0.2)
    ax3.legend(loc='best', fontsize=10)
    ax3.set_title('(c) $M_m$ vs $M_P$', fontsize=14)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_mm_mp.png", dpi=300, bbox_inches='tight')
    print(f"Saved M_m vs M_P plot to {output_prefix}_mm_mp.png")
