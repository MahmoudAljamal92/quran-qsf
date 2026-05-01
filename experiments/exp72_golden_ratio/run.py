"""
exp72_golden_ratio/run.py
==========================
H1: Golden Ratio in the (T, EL) Sufficiency Plane.

Motivation
    T and EL yield AUC=0.9975 (exp70). Does the Quran centroid's
    angular position, eigenvalue ratio, or any derived quantity
    converge to a known mathematical constant (phi, e, pi, sqrt(2))?

Protocol (frozen before execution)
    T1. Compute Quran and Ctrl centroids in (T, EL) Band-A space.
    T2. Compute separation vector angle theta.
    T3. Compute 2x2 covariance eigenvalue ratio for Quran cluster.
    T4. Compute various derived ratios: EL_q/|T_q|, separation
        distance, margin from exp70, etc.
    T5. Compare each quantity to a library of known constants.
    T6. Bootstrap 10k for CIs on all ratios.
    T7. Apply look-elsewhere correction: with N quantities and M
        constants, the chance of a ≤2% match is 1-(1-0.02)^(N*M).

Pre-registered thresholds
    CONSTANT_FOUND:    a ratio's 95% CI contains a known constant
                       AND the CI width < 10% of the constant
    SUGGESTIVE:        CI contains a constant but width > 10%
    NULL:              no constant within any CI

Reads: phase_06_phi_m.pkl

Writes ONLY under results/experiments/exp72_golden_ratio/
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp72_golden_ratio"

SEED = 42
N_BOOT = 10000

# Library of known mathematical constants
CONSTANTS = {
    "phi": (1 + math.sqrt(5)) / 2,       # 1.6180
    "1/phi": 2 / (1 + math.sqrt(5)),      # 0.6180
    "sqrt(2)": math.sqrt(2),              # 1.4142
    "1/sqrt(2)": 1 / math.sqrt(2),        # 0.7071
    "e": math.e,                          # 2.7183
    "1/e": 1 / math.e,                    # 0.3679
    "pi": math.pi,                        # 3.1416
    "pi/2": math.pi / 2,                  # 1.5708
    "pi/4": math.pi / 4,                  # 0.7854
    "1/pi": 1 / math.pi,                  # 0.3183
    "2/pi": 2 / math.pi,                  # 0.6366
    "sqrt(3)": math.sqrt(3),              # 1.7321
    "ln(2)": math.log(2),                 # 0.6931
    "1/3": 1/3,                           # 0.3333
    "2/3": 2/3,                           # 0.6667
    "sqrt(5)": math.sqrt(5),              # 2.2361
    "euler_gamma": 0.5772156649,          # Euler-Mascheroni
}


def _closest_constant(value: float) -> tuple[str, float, float]:
    """Find closest known constant, return (name, const_value, pct_error)."""
    best = None
    for name, c in CONSTANTS.items():
        if c == 0:
            continue
        pct = abs(value - c) / abs(c) * 100
        if best is None or pct < best[2]:
            best = (name, c, pct)
    return best


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    t_idx = feat_cols.index("T")
    el_idx = feat_cols.index("EL")

    Q2 = X_Q[:, [t_idx, el_idx]]  # (n_q, 2): [T, EL]
    C2 = X_C[:, [t_idx, el_idx]]

    n_q = Q2.shape[0]
    n_c = C2.shape[0]
    print(f"[{EXP}] Quran={n_q}, Ctrl={n_c} (Band-A), features=[T, EL]")

    # --- T1: Centroids ---
    cq = Q2.mean(axis=0)   # [T_q, EL_q]
    cc = C2.mean(axis=0)   # [T_c, EL_c]
    print(f"\n[{EXP}] === T1: Centroids ===")
    print(f"  Quran: T={cq[0]:.4f}, EL={cq[1]:.4f}")
    print(f"  Ctrl:  T={cc[0]:.4f}, EL={cc[1]:.4f}")

    # --- T2: Separation vector angle ---
    sep = cq - cc
    theta = math.atan2(sep[1], sep[0])  # atan2(dEL, dT)
    theta_deg = math.degrees(theta)
    sep_dist = math.sqrt(sep[0]**2 + sep[1]**2)
    print(f"\n[{EXP}] === T2: Separation vector ===")
    print(f"  ΔT={sep[0]:.4f}, ΔEL={sep[1]:.4f}")
    print(f"  θ = {theta_deg:.2f}° ({theta:.4f} rad)")
    print(f"  Distance = {sep_dist:.4f}")

    # --- T3: Eigenvalue ratio ---
    cov_q = np.cov(Q2.T)
    eigvals = np.linalg.eigvalsh(cov_q)
    eigvals = np.sort(eigvals)[::-1]  # descending
    eig_ratio = eigvals[0] / eigvals[1] if eigvals[1] > 1e-12 else float("inf")
    print(f"\n[{EXP}] === T3: Quran cluster eigenvalues ===")
    print(f"  λ1={eigvals[0]:.6f}, λ2={eigvals[1]:.6f}")
    print(f"  λ1/λ2 = {eig_ratio:.4f}")

    # --- T4: Derived ratios ---
    ratios = {}
    ratios["EL_q/|T_q|"] = abs(cq[1] / cq[0]) if abs(cq[0]) > 1e-12 else float("inf")
    ratios["theta/pi"] = theta / math.pi
    ratios["theta_deg/90"] = theta_deg / 90
    ratios["sep_dist"] = sep_dist
    ratios["eig_ratio"] = eig_ratio
    ratios["dEL/dT"] = abs(sep[1] / sep[0]) if abs(sep[0]) > 1e-12 else float("inf")
    ratios["EL_q"] = cq[1]
    ratios["T_q"] = abs(cq[0])
    ratios["EL_q/EL_c"] = cq[1] / cc[1] if abs(cc[1]) > 1e-12 else float("inf")

    print(f"\n[{EXP}] === T4: Derived ratios ===")
    for name, val in ratios.items():
        closest = _closest_constant(val)
        print(f"  {name:20s} = {val:.6f}  "
              f"closest: {closest[0]}={closest[1]:.4f} ({closest[2]:.1f}% off)")

    # --- T6: Bootstrap ---
    print(f"\n[{EXP}] === T6: Bootstrap ({N_BOOT}x) ===")
    rng = np.random.RandomState(SEED)
    boot = {name: np.empty(N_BOOT) for name in ratios}

    for i in range(N_BOOT):
        idx_q = rng.choice(n_q, n_q, replace=True)
        idx_c = rng.choice(n_c, n_c, replace=True)
        Qb = Q2[idx_q]
        Cb = C2[idx_c]
        cqb = Qb.mean(axis=0)
        ccb = Cb.mean(axis=0)
        sepb = cqb - ccb

        boot["EL_q/|T_q|"][i] = abs(cqb[1] / cqb[0]) if abs(cqb[0]) > 1e-12 else float("nan")
        tb = math.atan2(sepb[1], sepb[0])
        boot["theta/pi"][i] = tb / math.pi
        boot["theta_deg/90"][i] = math.degrees(tb) / 90
        boot["sep_dist"][i] = math.sqrt(sepb[0]**2 + sepb[1]**2)
        boot["dEL/dT"][i] = abs(sepb[1] / sepb[0]) if abs(sepb[0]) > 1e-12 else float("nan")
        boot["EL_q"][i] = cqb[1]
        boot["T_q"][i] = abs(cqb[0])
        boot["EL_q/EL_c"][i] = cqb[1] / ccb[1] if abs(ccb[1]) > 1e-12 else float("nan")

        try:
            cov_b = np.cov(Qb.T)
            ev = np.linalg.eigvalsh(cov_b)
            ev = np.sort(ev)[::-1]
            boot["eig_ratio"][i] = ev[0] / ev[1] if ev[1] > 1e-12 else float("nan")
        except Exception:
            boot["eig_ratio"][i] = float("nan")

    ci_results = {}
    for name in ratios:
        v = boot[name][np.isfinite(boot[name])]
        if len(v) < 100:
            ci_results[name] = {"median": float("nan"), "ci_lo": float("nan"),
                                "ci_hi": float("nan"), "width_pct": float("nan")}
            continue
        lo, hi = np.percentile(v, [2.5, 97.5])
        med = np.median(v)
        width_pct = (hi - lo) / abs(med) * 100 if abs(med) > 1e-12 else float("inf")
        ci_results[name] = {
            "median": round(float(med), 6),
            "ci_lo": round(float(lo), 6),
            "ci_hi": round(float(hi), 6),
            "width_pct": round(float(width_pct), 1),
        }
        print(f"  {name:20s}: med={med:.4f}  95% CI=[{lo:.4f}, {hi:.4f}]  "
              f"width={width_pct:.1f}%")

    # --- T5+T7: Constant matching with look-elsewhere ---
    print(f"\n[{EXP}] === T5: Constant matching ===")
    matches = []
    for rname, ci in ci_results.items():
        if math.isnan(ci["ci_lo"]):
            continue
        for cname, cval in CONSTANTS.items():
            if ci["ci_lo"] <= cval <= ci["ci_hi"]:
                pct_err = abs(ratios[rname] - cval) / abs(cval) * 100
                narrow = ci["width_pct"] < 10
                verdict_m = "NARROW" if narrow else "WIDE"
                matches.append({
                    "ratio": rname,
                    "constant": cname,
                    "const_val": cval,
                    "ratio_val": round(ratios[rname], 6),
                    "pct_error": round(pct_err, 2),
                    "ci_width_pct": ci["width_pct"],
                    "narrow": narrow,
                })
                print(f"  MATCH: {rname} ≈ {cname} ({cval:.4f})  "
                      f"err={pct_err:.1f}%  CI_width={ci['width_pct']:.1f}%  "
                      f"→ {verdict_m}")

    n_ratios = len(ratios)
    n_consts = len(CONSTANTS)
    n_trials = n_ratios * n_consts
    p_any_match = 1 - (1 - 0.02)**n_trials  # prob of at least 1 spurious match at 2%
    print(f"\n  Look-elsewhere: {n_ratios} ratios × {n_consts} constants = "
          f"{n_trials} trials")
    print(f"  P(≥1 spurious 2%-match) = {p_any_match:.3f}")

    # --- Verdict ---
    narrow_matches = [m for m in matches if m["narrow"]]
    if narrow_matches:
        verdict = "SUGGESTIVE"  # Upgrade to CONSTANT_FOUND only if extraordinarily tight
        for m in narrow_matches:
            if m["pct_error"] < 1.0:
                verdict = "CONSTANT_FOUND"
                break
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Matches found: {len(matches)} ({len(narrow_matches)} narrow)")
    print(f"  Look-elsewhere P = {p_any_match:.3f}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H1 — Does the Quran's position in (T, EL) space "
                      "relate to a known mathematical constant?",
        "schema_version": 1,
        "centroids": {
            "quran": {"T": round(float(cq[0]), 6), "EL": round(float(cq[1]), 6)},
            "ctrl": {"T": round(float(cc[0]), 6), "EL": round(float(cc[1]), 6)},
        },
        "separation": {
            "dT": round(float(sep[0]), 6),
            "dEL": round(float(sep[1]), 6),
            "theta_deg": round(theta_deg, 4),
            "distance": round(sep_dist, 6),
        },
        "eigenvalues": {
            "lambda1": round(float(eigvals[0]), 6),
            "lambda2": round(float(eigvals[1]), 6),
            "ratio": round(eig_ratio, 6),
        },
        "ratios": {k: round(v, 6) for k, v in ratios.items()},
        "bootstrap": ci_results,
        "matches": matches,
        "look_elsewhere": {
            "n_trials": n_trials,
            "p_spurious": round(p_any_match, 4),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
