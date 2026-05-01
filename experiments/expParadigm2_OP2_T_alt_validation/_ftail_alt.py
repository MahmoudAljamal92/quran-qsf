"""
_ftail_alt.py — Quick mpmath F-tail re-derivation for the T_alt 5-D
Hotelling T². Sandboxed inside the T_alt validation experiment dir.

Reads:
  results/experiments/expParadigm2_OP2_T_alt_validation/expParadigm2_OP2_T_alt_validation.json
  results/experiments/exp01_ftail/exp01_ftail.json

Writes:
  results/experiments/expParadigm2_OP2_T_alt_validation/ftail_alt.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import mpmath as mp

_ROOT = Path(__file__).resolve().parent.parent.parent
_ALT = (_ROOT / "results" / "experiments"
        / "expParadigm2_OP2_T_alt_validation"
        / "expParadigm2_OP2_T_alt_validation.json")
_CANON = (_ROOT / "results" / "experiments" / "exp01_ftail" / "exp01_ftail.json")
_OUT = (_ROOT / "results" / "experiments"
        / "expParadigm2_OP2_T_alt_validation" / "ftail_alt.json")


def _hp_logsf(F: float, df1: int, df2: int, dps: int = 80) -> float:
    mp.mp.dps = dps
    F_mp = mp.mpf(F)
    df1_mp = mp.mpf(df1)
    df2_mp = mp.mpf(df2)
    x = df2_mp / (df2_mp + df1_mp * F_mp)
    sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
    return float(mp.log10(sf))


def main() -> int:
    d_alt = json.loads(_ALT.read_text(encoding="utf-8"))
    d_canon = json.loads(_CANON.read_text(encoding="utf-8"))

    print("=== Locked canonical (5-D, T) ===")
    ts = d_canon["two_sample_hotelling_T2_pooled_cov"]
    canon_T2 = float(ts["T2"])
    canon_F  = float(ts["F"])
    canon_df1 = int(ts["df1"])
    canon_df2 = int(ts["df2"])
    canon_log10_p = float(ts["highprec_log10_p_F_tail"])
    print(f"  T2          = {canon_T2:.4f}")
    print(f"  F           = {canon_F:.4f}  df=({canon_df1}, {canon_df2})")
    print(f"  log10 p     = {canon_log10_p:.4f}  (mpmath 80-dps)")

    print()
    print("=== Re-derived alternate (5-D, T_alt) ===")
    ta = d_alt["hotelling_T2_alt"]
    alt_T2 = float(ta["T2"])
    alt_F  = float(ta["F"])
    alt_df1 = int(ta["df1"])
    alt_df2 = int(ta["df2"])
    print(f"  T2          = {alt_T2:.4f}")
    print(f"  F           = {alt_F:.4f}  df=({alt_df1}, {alt_df2})")

    alt_log10_p = _hp_logsf(alt_F, alt_df1, alt_df2, dps=80)
    print(f"  log10 p     = {alt_log10_p:.4f}  (mpmath 80-dps)")

    print()
    print("=== Comparison ===")
    delta = alt_log10_p - canon_log10_p
    # σ-equivalent for a one-sided p-value: solve for z with sf(z) = p,
    # giving z² = -2 ln(p) (chi² df=1 tail asymptotic). Use natural log.
    sigma_canon = math.sqrt(-2.0 * canon_log10_p * math.log(10))
    sigma_alt   = math.sqrt(-2.0 * alt_log10_p   * math.log(10))
    print(f"  canon  log10 p = {canon_log10_p:+.4f}  (~ {sigma_canon:.2f}-sigma)")
    print(f"  alt    log10 p = {alt_log10_p:+.4f}  (~ {sigma_alt:.2f}-sigma)")
    print(f"  delta log10 p  = {delta:+.4f}  (alt - canon)")
    print(f"  sigma gain     = {sigma_alt - sigma_canon:+.4f}-sigma")

    out = {
        "experiment": "expParadigm2_OP2_T_alt_validation::ftail_alt",
        "canonical": {
            "T2": canon_T2, "F": canon_F,
            "df1": canon_df1, "df2": canon_df2,
            "highprec_log10_p_F_tail": canon_log10_p,
            "sigma_equivalent": sigma_canon,
        },
        "alt_T_alt": {
            "T2": alt_T2, "F": alt_F,
            "df1": alt_df1, "df2": alt_df2,
            "highprec_log10_p_F_tail": alt_log10_p,
            "highprec_dps": 80,
            "sigma_equivalent": sigma_alt,
        },
        "comparison": {
            "delta_log10_p_alt_minus_canon": delta,
            "delta_sigma_alt_minus_canon": sigma_alt - sigma_canon,
            "T2_ratio_alt_over_canon": alt_T2 / canon_T2,
        },
        "interpretation": (
            "Hotelling T-squared under T_alt produces a deeper F-tail "
            "log10 p-value than the canonical T. The sigma gain is the "
            "increase in the chi-squared-df1 tail equivalent when the "
            "F-tail probability is mapped to a one-tailed normal sigma."
        ),
    }
    _OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    print(f"\nwrote: {_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
