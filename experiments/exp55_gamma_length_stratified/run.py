#!/usr/bin/env python
"""
exp55_gamma_length_stratified  –  Length-stratified gzip NCD analysis
=====================================================================

Tests hypothesis H3: the Band-A doc-scale gzip NCD Cohen's d = +0.534
(from exp41_gzip_formalised) is NOT length-driven — the Quran-vs-control
difference survives when surahs are matched by letter-count decile.

Applies a formal pre-registered decision rule to the existing
exp41 length_audit.json per-decile data and adds:
  1. Binomial sign test on decile Cohen's d > 0
  2. Count of deciles with d > 0.30
  3. Analytic 95% CI on per-decile Cohen's d (SE approximation)
  4. Cross-check of log-linear gamma (Quran indicator) > 0, p < 0.001

Pre-registered verdict table (frozen before computation):
  >= 7/10 deciles d>0.30 AND sign-test p<=0.05 AND gamma>0
      -> LENGTH_INDEPENDENT
  4-6 deciles d>0.30 AND sign-test p<=0.10
      -> PARTIALLY_LENGTH_DRIVEN
  <= 3 deciles d>0.30 OR sign-test p>0.10
      -> LENGTH_DRIVEN  (retract d=+0.534 as headline)

Falsifier: majority of deciles (>=6/10) with d<=0, sign-test n_positive<=4,
           sign-test p>0.10.

Inputs:
  results/experiments/exp41_gzip_formalised/length_audit.json
  results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json
Outputs:
  results/experiments/exp55_gamma_length_stratified/exp55_gamma_length_stratified.json
  results/experiments/exp55_gamma_length_stratified/decile_d_ci.png
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Bootstrap the project root so _lib imports work from any cwd.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_EXP_ROOT = _HERE.parent                     # experiments/
sys.path.insert(0, str(_EXP_ROOT))

import _lib  # noqa: E402  (experiments/_lib.py)

# ---------------------------------------------------------------------------
# Constants (pre-registered)
# ---------------------------------------------------------------------------
EXP_NAME = "exp55_gamma_length_stratified"
PREREG_PATH = _HERE / "PREREG.md"
HEADLINE_D_EXPECTED = 0.534       # approx doc-scale d from exp41

SIGN_TEST_ALPHA_STRICT = 0.05
SIGN_TEST_ALPHA_LOOSE = 0.10
D_THRESHOLD = 0.30
PROMOTE_COUNT = 7      # deciles with d > D_THRESHOLD for LENGTH_INDEPENDENT
PARTIAL_LO = 4
PARTIAL_HI = 6
GAMMA_P_THRESHOLD = 0.001


# ---------------------------------------------------------------------------
# Input file paths
# ---------------------------------------------------------------------------
_RESULTS = _lib._ROOT / "results"
_EXP41_DIR = _RESULTS / "experiments" / "exp41_gzip_formalised"
_LENGTH_AUDIT = _EXP41_DIR / "length_audit.json"
_EXP41_MAIN = _EXP41_DIR / "exp41_gzip_formalised.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _prereg_hash() -> str:
    """SHA-256 of the PREREG.md file."""
    h = hashlib.sha256()
    with open(PREREG_PATH, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _binomial_sign_test(n_positive: int, n_total: int, p0: float = 0.5) -> float:
    """
    Two-sided binomial test: probability of observing n_positive or more
    extreme under H0: P(d > 0) = p0.  Returns the two-sided p-value.

    Uses the exact CDF via math.comb (no scipy dependency).
    """
    # P(X >= n_positive) under Binom(n_total, p0)
    p_right = sum(
        math.comb(n_total, k) * (p0 ** k) * ((1 - p0) ** (n_total - k))
        for k in range(n_positive, n_total + 1)
    )
    # P(X <= n_total - n_positive)
    n_mirror = n_total - n_positive
    p_left = sum(
        math.comb(n_total, k) * (p0 ** k) * ((1 - p0) ** (n_total - k))
        for k in range(0, n_mirror + 1)
    )
    return min(2.0 * min(p_right, p_left), 1.0)


def _cohen_d_se(d: float, n1: int, n2: int) -> float:
    """
    Analytic standard error of Cohen's d (Hedges & Olkin approximation):
        SE(d) = sqrt( (n1+n2)/(n1*n2) + d^2 / (2*(n1+n2)) )
    """
    n = n1 + n2
    return math.sqrt(n / (n1 * n2) + (d ** 2) / (2 * n))


def _ci95(d: float, se: float) -> tuple[float, float]:
    """Symmetric 95% CI: d +/- 1.96*SE."""
    hw = 1.96 * se
    return (d - hw, d + hw)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def _plot_decile_ci(
    deciles: List[Dict[str, Any]],
    out_path: Path,
) -> None:
    """Bar chart of per-decile Cohen's d with 95% CI error bars."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[exp55] matplotlib not available, skipping plot.", file=sys.stderr)
        return

    labels = [f"D{dec['decile']}" for dec in deciles]
    ds = [dec["cohen_d"] for dec in deciles]
    ci_lo = [dec["ci95_lo"] for dec in deciles]
    ci_hi = [dec["ci95_hi"] for dec in deciles]
    err_lo = [d - lo for d, lo in zip(ds, ci_lo)]
    err_hi = [hi - d for d, hi in zip(ds, ci_hi)]

    colours = ["#2ca02c" if d > D_THRESHOLD else "#d62728" if d < 0 else "#ff7f0e"
               for d in ds]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(labels))
    ax.bar(x, ds, color=colours, edgecolor="black", linewidth=0.5, zorder=2)
    ax.errorbar(x, ds, yerr=[err_lo, err_hi], fmt="none", ecolor="black",
                capsize=4, zorder=3)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(D_THRESHOLD, color="grey", linestyle="--", linewidth=0.7,
               label=f"d = {D_THRESHOLD}")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Cohen's d (Quran vs Control NCD)")
    ax.set_xlabel("Letter-count decile")
    ax.set_title("exp55: Per-decile Cohen's d with 95% CI")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    print(f"[exp55] Plot saved -> {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ts_start = time.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[exp55] start  {ts_start}")
    prereg_sha = _prereg_hash()
    print(f"[exp55] PREREG SHA-256 = {prereg_sha}")

    # -- Sandbox self-check begin -------------------------------------------
    pre_snap = _lib.self_check_begin()

    # -- Load inputs --------------------------------------------------------
    if not _LENGTH_AUDIT.exists():
        print(f"[exp55] FATAL: missing {_LENGTH_AUDIT}", file=sys.stderr)
        return 1
    if not _EXP41_MAIN.exists():
        print(f"[exp55] FATAL: missing {_EXP41_MAIN}", file=sys.stderr)
        return 1

    with open(_LENGTH_AUDIT, "r", encoding="utf-8") as f:
        audit = json.load(f)
    with open(_EXP41_MAIN, "r", encoding="utf-8") as f:
        exp41 = json.load(f)

    deciles_raw: List[Dict[str, Any]] = audit["decile_stratified"]
    log_lin = audit["log_linear_regression"]

    # Cross-check headline d
    headline_d = exp41["doc_scale_summary"]["cohen_d"]
    print(f"[exp55] headline doc-scale d = {headline_d:.4f} "
          f"(expected ~{HEADLINE_D_EXPECTED})")

    # -- 1. Per-decile Cohen's d with analytic 95% CI ----------------------
    enriched_deciles: List[Dict[str, Any]] = []
    for dec in deciles_raw:
        d = dec["cohen_d"]
        n_q = dec["n_q"]
        n_ctrl = dec["n_ctrl"]
        se = _cohen_d_se(d, n_q, n_ctrl)
        lo, hi = _ci95(d, se)
        enriched_deciles.append({
            "decile": dec["decile"],
            "n_q": n_q,
            "n_ctrl": n_ctrl,
            "n_letters_lo": dec["n_letters_lo"],
            "n_letters_hi": dec["n_letters_hi"],
            "cohen_d": d,
            "se_d": round(se, 6),
            "ci95_lo": round(lo, 6),
            "ci95_hi": round(hi, 6),
        })

    # -- 2. Sign test -------------------------------------------------------
    n_total = len(enriched_deciles)
    n_positive = sum(1 for dec in enriched_deciles if dec["cohen_d"] > 0)
    n_negative = n_total - n_positive
    sign_p = _binomial_sign_test(n_positive, n_total, 0.5)
    print(f"[exp55] sign test: {n_positive}/{n_total} positive, p = {sign_p:.6f}")

    # -- 3. Count d > D_THRESHOLD -------------------------------------------
    n_above_threshold = sum(
        1 for dec in enriched_deciles if dec["cohen_d"] > D_THRESHOLD
    )
    print(f"[exp55] deciles with d > {D_THRESHOLD}: {n_above_threshold}/{n_total}")

    # -- 4. Log-linear gamma check ------------------------------------------
    gamma = log_lin["gamma_quran_effect"]
    gamma_p = log_lin["gamma_p_two_sided"]
    gamma_ci = log_lin["gamma_ci95"]
    gamma_ok = gamma > 0 and gamma_p < GAMMA_P_THRESHOLD
    print(f"[exp55] gamma = {gamma:.6f}, p = {gamma_p}, "
          f"CI95 = {gamma_ci}, pass = {gamma_ok}")

    # -- 5. Verdict ---------------------------------------------------------
    if (n_above_threshold >= PROMOTE_COUNT
            and sign_p <= SIGN_TEST_ALPHA_STRICT
            and gamma > 0):
        verdict = "LENGTH_INDEPENDENT"
    elif (PARTIAL_LO <= n_above_threshold <= PARTIAL_HI
          and sign_p <= SIGN_TEST_ALPHA_LOOSE):
        verdict = "PARTIALLY_LENGTH_DRIVEN"
    elif n_above_threshold <= 3 or sign_p > SIGN_TEST_ALPHA_LOOSE:
        verdict = "LENGTH_DRIVEN"
    else:
        # Fallback (shouldn't be reached with well-defined rules)
        verdict = "INDETERMINATE"
    print(f"[exp55] VERDICT: {verdict}")

    # -- Falsifier check ----------------------------------------------------
    falsified = (n_positive <= 4 and sign_p > SIGN_TEST_ALPHA_LOOSE)
    print(f"[exp55] falsifier triggered: {falsified}")

    # -- Build output -------------------------------------------------------
    ts_end = time.strftime("%Y-%m-%dT%H:%M:%S")

    report: Dict[str, Any] = {
        "experiment": EXP_NAME,
        "schema_version": 1,
        "ts_start": ts_start,
        "ts_end": ts_end,
        "prereg_sha256": prereg_sha,
        "inputs": {
            "length_audit": str(_LENGTH_AUDIT.relative_to(_lib._ROOT)),
            "exp41_main": str(_EXP41_MAIN.relative_to(_lib._ROOT)),
        },
        "headline_d_crosscheck": round(headline_d, 6),
        "sign_test": {
            "n_total": n_total,
            "n_positive": n_positive,
            "n_negative": n_negative,
            "p_two_sided": sign_p,
            "alpha_strict": SIGN_TEST_ALPHA_STRICT,
            "alpha_loose": SIGN_TEST_ALPHA_LOOSE,
        },
        "d_above_threshold": {
            "threshold": D_THRESHOLD,
            "count": n_above_threshold,
            "required_for_LENGTH_INDEPENDENT": PROMOTE_COUNT,
        },
        "log_linear_gamma": {
            "gamma": gamma,
            "gamma_p": gamma_p,
            "gamma_ci95": gamma_ci,
            "gamma_threshold_p": GAMMA_P_THRESHOLD,
            "pass": gamma_ok,
        },
        "per_decile": enriched_deciles,
        "verdict": verdict,
        "falsifier_triggered": falsified,
        "notes": (
            "Analytic SE(d) used for CI (Hedges & Olkin approximation) "
            "because raw per-unit NCD values are not stored in the summary JSON. "
            "Pre-registered decision rules applied verbatim."
        ),
    }

    # -- Write outputs ------------------------------------------------------
    out_dir = _lib.safe_output_dir(EXP_NAME)
    out_json = out_dir / f"{EXP_NAME}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[exp55] report -> {out_json}")

    # Plot
    plot_path = out_dir / "decile_d_ci.png"
    _plot_decile_ci(enriched_deciles, plot_path)

    # -- Sandbox self-check end ---------------------------------------------
    _lib.self_check_end(pre_snap, EXP_NAME)
    print(f"[exp55] self-check PASSED — no protected files mutated.")

    print(f"[exp55] done    {ts_end}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
