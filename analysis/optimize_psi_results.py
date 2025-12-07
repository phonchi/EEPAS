# -*- coding: utf-8 -*-
"""
PSI Step 9 Optimization (Deduplication) - Robust Implementation

Supports two methods for identifying "identical" Ψ identifications:
  (1) round mode: Group by rounding to decimal places
  (2) tolerance mode: Group by binning with tolerance (±t_tol, ±mp_tol, ±r_tol)  ← RECOMMENDED

Features:
  - Fixed 14-column output format matching paper specification
  - Detailed reporting of 9.1/9.2 counts before/after
  - Per-mainshock identification counts

Usage Example (tolerance mode, RECOMMENDED):
    python optimize_psi_results.py \
        --input testopt.ou4a --output optimized_psi.ou4 \
        --mode tolerance --t-tol 0.03 --mp-tol 0.05 --r-tol 0.25

Usage Example (round mode, more conservative):
    python optimize_psi_results.py \
        --input testopt.ou4a --output optimized_psi.ou4 \
        --mode round --t-decimals 2 --mp-decimals 1 --r-decimals 0

Algorithm Steps (from Christophersen et al. 2024, SRL 95(6):3464-3481 Section 2.3):
    Step 9.1: For identical (eq_name, tmin, tp, mp) → keep max sloperatio (ties: min ap)
    Step 9.2: For identical (eq_name, tp, r) → keep min ap
"""

import argparse
from collections import OrderedDict
from typing import Tuple

import numpy as np
import pandas as pd

# === Paper-specified 14 columns (fixed output order) ===
CANONICAL_14 = [
    "eq_name", "mm", "mp", "mminus", "sloperatio",
    "tmin", "time_onset", "tmax", "tp", "ap",
    "rn_max", "rn_min", "re_max", "re_min",
]


# -------------------------------
# File reading and column normalization
# -------------------------------
def _read_ou4a_like(input_file: str) -> pd.DataFrame:
    """
    Read first 14 columns from .ou4a file and assign CANONICAL_14 column names.

    Does not rely on file's built-in column names to avoid misalignment from
    debug columns or inconsistent naming.

    Args:
        input_file: Path to .ou4a file (str)

    Returns:
    pd.DataFrame
        DataFrame with 14 standardized columns and proper types

    Raises:
    ValueError
        If file has fewer than 14 columns
    """
    raw = pd.read_csv(input_file, sep=r"\s+", header=None, dtype=str)
    if raw.shape[1] < 14:
        raise ValueError(f"{input_file} has {raw.shape[1]} columns < 14, incorrect format.")

    df = raw.iloc[:, :14].copy()
    df.columns = CANONICAL_14

    # Type conversion (eq_name remains string)
    for c in CANONICAL_14[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["eq_name"] = df["eq_name"].astype(str).str.strip()
    return df


def _ensure_canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame contains only CANONICAL_14 columns in fixed order.

    Supports legacy column name 'time_mina' -> 'time_onset' for compatibility.

    Args:
        df: Input DataFrame (pd.DataFrame)

    Returns:
    pd.DataFrame
        DataFrame with standardized column order

    Raises:
    ValueError
        If required columns are missing
    """
    cols = list(df.columns)
    if "time_onset" not in cols and "time_mina" in cols:
        df = df.rename(columns={"time_mina": "time_onset"})
    missing = [c for c in CANONICAL_14 if c not in df.columns]
    if missing:
        raise ValueError(f"Step 9 missing required columns: {missing}")
    return df.reindex(columns=CANONICAL_14).copy()


# -------------------------------
# Step 9.1/9.2: Two grouping implementations
# -------------------------------
def _run_once_round(df_in: pd.DataFrame,
                    t_decimals: int, mp_decimals: int, r_decimals: int) -> Tuple[pd.DataFrame, int, int]:
    """
    Round mode: discretize keys by rounding to decimal places, then apply Steps 9.1/9.2.

    Args:
        df_in: Input Ψ identifications (pd.DataFrame)
        t_decimals: Decimal places for time rounding (int)
        mp_decimals: Decimal places for magnitude rounding (int)
    r_decimals : int
        Decimal places for slope ratio rounding

    Returns:
    tuple
        (df_after_9.2, count_after_9.1, count_after_9.2)
    """
    df1 = df_in.copy()
    # Quantize by rounding
    df1["tmin_q"] = np.round(df1["tmin"].astype(float), t_decimals)
    df1["tp_q"]   = np.round(df1["tp"].astype(float),   t_decimals)
    df1["mp_q"]   = np.round(df1["mp"].astype(float),   mp_decimals)
    df1["r_q"]    = np.round(df1["sloperatio"].astype(float), r_decimals)

    # Step 9.1: For same (eq_name, tmin_q, tp_q, mp_q) → max sloperatio; ties: min ap
    g91 = ["eq_name", "tmin_q", "tp_q", "mp_q"]
    df_91 = (
        df1.sort_values(by=["sloperatio", "ap"], ascending=[False, True])
           .groupby(g91, as_index=False, sort=False)
           .head(1)
    )
    n91 = len(df_91)

    # Step 9.2: For same (eq_name, tp_q, r_q) → min ap
    g92 = ["eq_name", "tp_q", "r_q"]
    df_92 = (
        df_91.sort_values(by=["ap"], ascending=True)
             .groupby(g92, as_index=False, sort=False)
             .head(1)
    )
    n92 = len(df_92)

    # Remove auxiliary columns
    df_92 = df_92.drop(columns=["tmin_q", "tp_q", "mp_q", "r_q"], errors="ignore")
    return df_92, n91, n92


def _bin_with_tolerance(x: np.ndarray, tol: float) -> np.ndarray:
    """
    Bin values with tolerance: discretize using bin width tol.

    Equivalent to round(x/tol) * tol, but uses floor((x/tol)+0.5)*tol
    to avoid system-dependent rounding at 0.5 boundaries.

    Args:
        x: Input values (np.ndarray)
        tol: Tolerance (bin width) (float)

    Returns:
    np.ndarray
        Binned values
    """
    x = np.asarray(x, float)
    return np.floor((x / tol) + 0.5) * tol


def _run_once_tolerance(df_in: pd.DataFrame,
                        t_tol: float, mp_tol: float, r_tol: float) -> Tuple[pd.DataFrame, int, int]:
    """
    Tolerance mode: discretize keys by binning with tolerance, then apply Steps 9.1/9.2.

    Args:
        df_in: Input Ψ identifications (pd.DataFrame)
        t_tol: Time tolerance (years) (float)
        mp_tol: Magnitude tolerance (float)
    r_tol : float
        Slope ratio tolerance

    Returns:
    tuple
        (df_after_9.2, count_after_9.1, count_after_9.2)
    """
    df1 = df_in.copy()
    df1["tmin_b"] = _bin_with_tolerance(df1["tmin"].values, t_tol)
    df1["tp_b"]   = _bin_with_tolerance(df1["tp"].values,   t_tol)
    df1["mp_b"]   = _bin_with_tolerance(df1["mp"].values,   mp_tol)
    df1["r_b"]    = _bin_with_tolerance(df1["sloperatio"].values, r_tol)

    # Step 9.1: For same (eq_name, tmin_b, tp_b, mp_b) → max sloperatio; ties: min ap
    g91 = ["eq_name", "tmin_b", "tp_b", "mp_b"]
    df_91 = (
        df1.sort_values(by=["sloperatio", "ap"], ascending=[False, True])
           .groupby(g91, as_index=False, sort=False)
           .head(1)
    )
    n91 = len(df_91)

    # Step 9.2: For same (eq_name, tp_b, r_b) → min ap
    g92 = ["eq_name", "tp_b", "r_b"]
    df_92 = (
        df_91.sort_values(by=["ap"], ascending=True)
             .groupby(g92, as_index=False, sort=False)
             .head(1)
    )
    n92 = len(df_92)

    # Remove auxiliary columns
    df_92 = df_92.drop(columns=["tmin_b", "tp_b", "mp_b", "r_b"], errors="ignore")
    return df_92, n91, n92


# -------------------------------
# Main function
# -------------------------------
def optimize_psi_results(
    input_file: str = "psi.ou4a",
    output_file: str = "optimized_psi.ou4",
    # Round mode parameters
    t_decimals: int = 3, mp_decimals: int = 1, r_decimals: int = 1,
    # Auto-relax precision (only for round mode; tolerance mode usually doesn't need this)
    auto_relax: bool = True,
    verbose: bool = True,
    # Mode selection
    mode: str = "round",   # "round" or "tolerance"
    # Tolerance mode parameters (years, magnitude, slope ratio)
    t_tol: float = 0.03,   # ≈ 11 days
    mp_tol: float = 0.05,
    r_tol: float = 0.25,
):
    """
    Apply Step 9 two-stage deduplication to Ψ identification results.

    This implements the deduplication procedure from Christophersen et al. (2024, SRL 95(6):3464-3481):
        Step 9.1: For same (eq_name, tmin, tp, mp) → keep max sloperatio (ties: min ap)
        Step 9.2: For same (eq_name, tp, r) → keep min ap

    Two discretization modes:
        - mode="round": Discretize by rounding to decimal places (simple, controllable)
        - mode="tolerance": Discretize by binning with tolerance (RECOMMENDED, closer to physical resolution)

    Output format: Fixed 14 columns in CANONICAL_14 order.

    Args:
        input_file: Input .ou4a file with raw Ψ identifications
        output_file: Output .ou4 file with deduplicated results
        t_decimals: Decimal places for time (round mode)
        mp_decimals: Decimal places for magnitude (round mode)
        r_decimals: Decimal places for slope ratio (round mode)
        auto_relax: Automatically relax precision if no reduction (round mode only)
        verbose: Print detailed progress information
        mode: "round" or "tolerance"
        t_tol: Time tolerance in years (tolerance mode, default 0.03 ≈ 11 days)
        mp_tol: Magnitude tolerance (tolerance mode)
        r_tol: Slope ratio tolerance (tolerance mode)

    Returns:
        Tuple (n_initial, n_after_9.1, n_after_9.2) - counts at each stage
    """
    df = _read_ou4a_like(input_file)
    n0 = len(df)

    if verbose:
        print("=== PSI Result Optimization (Step 9) ===")
        print("Following the exact algorithm from the paper")
        print(f"Read {n0} raw Ψ identification records")
        print(f"Mode: {mode}")

    # ---- Execute Steps 9.1/9.2 ----
    if mode.lower() == "tolerance":
        df2, n91, n92 = _run_once_tolerance(df, t_tol=t_tol, mp_tol=mp_tol, r_tol=r_tol)
    else:
        df2, n91, n92 = _run_once_round(df, t_decimals, mp_decimals, r_decimals)

        # Auto-relax precision for round mode (fault tolerance)
        if auto_relax and n91 == n0 and n92 == n91:
            if verbose:
                print("\n⚠️  No reduction in both steps, enabling auto-relax precision retry...")
            tried = OrderedDict()
            for (td, md, rd) in [(2, mp_decimals, r_decimals),
                                 (2, 0, r_decimals),
                                 (2, 0, 0)]:
                key = (td, md, rd)
                if key in tried:
                    continue
                tried[key] = True
                df_try, n91_try, n92_try = _run_once_round(df, td, md, rd)
                if verbose:
                    print(f"  → Precision (t={td}, mp={md}, r={rd}): after 9.1={n91_try}, after 9.2={n92_try}")
                if (n91_try < n0) or (n92_try < n91_try):
                    df2, n91, n92 = df_try, n91_try, n92_try
                    t_decimals, mp_decimals, r_decimals = td, md, rd
                    break

    if verbose:
        print("\nStep 9.1: For identical tmin, tp, mp → keep max sloperatio...")
        print(f"  After first filter: {n91} records")
        print("\nStep 9.2: For identical tp, sloperatio → keep min ap...")
        print(f"  After second filter: {n92} records")

    # ---- Fixed 14-column output ----
    df2 = _ensure_canonical_columns(df2)
    df2["eq_name"] = df2["eq_name"].astype(str).str.strip()

    df2.to_csv(output_file, sep=" ", header=False, index=False, float_format="%.4f")

    if verbose:
        print(f"\nAfter optimization: {df2['eq_name'].nunique()} earthquakes have Ψ identifications")
        print("Number of Ψ identifications per earthquake (top 10):")
        print(df2["eq_name"].value_counts().head(10))
        print(f"\nSaved to {output_file} (fixed 14 columns)")

    return n0, n91, n92