"""
exp66_extended_mahalanobis/run.py
==================================
H28: 10-Feature Extended Mahalanobis — Do phi_structural and TE_net
Improve Quran vs Control Separation?

Adapted to our 5-D pipeline: tests 5-D → 7-D extension by adding
phi_structural (0.5*H_dfa_jm + 0.5*K2) and TE_net (transfer entropy
net) from v27_helpers.

Protocol (frozen before execution)
    T1. Compute 5-D features + phi_structural + TE_net for all units.
    T2. Baseline: 5-D Mahalanobis separation (Quran-centroid ellipsoid,
        TAU at 80% Quran coverage).
    T3. Extended: 7-D Mahalanobis separation (same protocol).
    T4. Δsep = sep_7D − sep_5D.
    T5. Per-feature ablation: 6-D with just phi_structural, 6-D with
        just TE_net.
    T6. VIF for the 7 features (collinearity check).
    T7. Permutation test (1000x): shuffle Quran/ctrl labels, recompute
        Δsep. p = frac(null Δsep >= observed).

Pre-registered acceptance (mirroring exp49 gate)
    PROMOTED:    Δsep >= 0.01 AND per-feature Δsep >= 0 AND perm p <= 0.01
    MARGINAL:    Δsep >= 0.01 OR (perm p <= 0.05)
    REDUNDANT:   Δsep < 0.01 AND perm p > 0.05

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA, FEAT_COLS, mu, S_inv

Writes ONLY under results/experiments/exp66_extended_mahalanobis/:
    exp66_extended_mahalanobis.json
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

_V27_DIR = _ROOT / "archive" / "helpers"
if str(_V27_DIR) not in sys.path:
    sys.path.insert(0, str(_V27_DIR))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import features as ft  # noqa: E402
import v27_helpers as v27  # noqa: E402

EXP = "exp66_extended_mahalanobis"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

OWN_COV_TARGET = 0.80     # 80% Quran coverage for TAU
N_PERM = 1000              # Permutation test iterations
SEED = 42


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------
def _compute_7d(units: list, corpus_name: str) -> list[dict]:
    """Compute 5-D + phi_structural + TE_net for each unit."""
    rows = []
    for u in units:
        if len(u.verses) < 3:
            continue
        try:
            f5 = ft.features_5d(u.verses)
            if np.any(np.isnan(f5)) or np.any(np.isinf(f5)):
                continue
        except Exception:
            continue

        bare_text = " ".join(u.verses)
        try:
            phi_s, _, _ = v27.phi_sukun_components(bare_text, None, u.verses)
        except Exception:
            phi_s = float("nan")
        if phi_s is None or not math.isfinite(phi_s):
            phi_s = float("nan")

        try:
            te = v27.compute_te_net(u.verses)
        except Exception:
            te = float("nan")
        if te is None or not math.isfinite(te):
            te = float("nan")

        rows.append({
            "label": u.label,
            "corpus": corpus_name,
            "f5": f5,
            "phi_structural": phi_s,
            "te_net": te,
        })
    return rows


def _sort_quran(units: list) -> list:
    def _n(u):
        if ":" in u.label:
            try: return int(u.label.split(":")[1])
            except ValueError: return 9999
        return 9999
    return sorted(units, key=_n)


# ---------------------------------------------------------------------------
# Mahalanobis separation engine
# ---------------------------------------------------------------------------
def _mahalanobis_separation(X_quran: np.ndarray, X_ctrl: np.ndarray,
                            cov_target: float = OWN_COV_TARGET
                            ) -> dict:
    """Compute Quran-centroid ellipsoid separation.

    1. Standardise using Quran mean/std.
    2. Compute Quran centroid + covariance.
    3. Mahalanobis distances from Quran centroid for everyone.
    4. TAU at cov_target coverage.
    5. Separation = fraction of controls outside TAU.
    """
    n_q, d = X_quran.shape
    n_c = X_ctrl.shape[0]

    # Standardise on Quran
    mu = X_quran.mean(axis=0)
    sigma = X_quran.std(axis=0, ddof=1)
    sigma = np.where(sigma < 1e-12, 1.0, sigma)
    Xq_s = (X_quran - mu) / sigma
    Xc_s = (X_ctrl - mu) / sigma

    # Quran covariance + inverse
    cov_q = np.cov(Xq_s, rowvar=False)
    try:
        cov_inv = np.linalg.inv(cov_q)
    except np.linalg.LinAlgError:
        cov_inv = np.linalg.pinv(cov_q)

    # Quran centroid (should be ~0 after standardisation)
    mu_q = Xq_s.mean(axis=0)

    # Distances
    def _dist(X, mu_ref, Sinv):
        d = X - mu_ref
        return np.sqrt(np.einsum("ij,jk,ik->i", d, Sinv, d))

    d_q = _dist(Xq_s, mu_q, cov_inv)
    d_c = _dist(Xc_s, mu_q, cov_inv)

    # TAU at coverage target
    tau_pct = cov_target * 100
    tau = float(np.percentile(d_q, tau_pct))

    q_inside = float(np.mean(d_q <= tau))
    c_outside = float(np.mean(d_c > tau))

    return {
        "d": d,
        "n_quran": n_q,
        "n_ctrl": n_c,
        "tau": tau,
        "q_coverage": round(q_inside, 4),
        "ctrl_separation": round(c_outside, 4),
        "q_dist_mean": float(d_q.mean()),
        "c_dist_mean": float(d_c.mean()),
    }


# ---------------------------------------------------------------------------
# VIF
# ---------------------------------------------------------------------------
def _vif(X: np.ndarray, feat_names: list[str]) -> dict:
    """Variance Inflation Factor for each feature."""
    from numpy.linalg import lstsq
    n, d = X.shape
    vifs = {}
    for j in range(d):
        y = X[:, j]
        others = np.delete(X, j, axis=1)
        others_with_intercept = np.column_stack([np.ones(n), others])
        beta, _, _, _ = lstsq(others_with_intercept, y, rcond=None)
        y_hat = others_with_intercept @ beta
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
        vif_val = 1.0 / (1.0 - r2) if r2 < 1.0 - 1e-12 else float("inf")
        vifs[feat_names[j]] = round(vif_val, 3)
    return vifs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
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
    CORPORA = state["CORPORA"]
    feat_cols_5d = list(state["FEAT_COLS"])
    print(f"[{EXP}] 5-D FEAT_COLS={feat_cols_5d}")

    # --- Compute 7-D features ---
    print(f"\n[{EXP}] Computing 7-D features (5-D + phi_structural + TE_net)...")
    quran_units = _sort_quran(CORPORA["quran"])
    q_rows = _compute_7d(quran_units, "quran")
    c_rows = []
    for cname in ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        cr = _compute_7d(units, cname)
        c_rows.extend(cr)
        print(f"[{EXP}] {cname:20s}: {len(cr):5d} units")

    n_q = len(q_rows)
    n_c = len(c_rows)
    print(f"[{EXP}] Quran: {n_q}, Controls: {n_c}")

    # Build arrays
    X5_q = np.array([r["f5"] for r in q_rows])
    X5_c = np.array([r["f5"] for r in c_rows])

    phi_s_q = np.array([r["phi_structural"] for r in q_rows])
    phi_s_c = np.array([r["phi_structural"] for r in c_rows])
    te_q = np.array([r["te_net"] for r in q_rows])
    te_c = np.array([r["te_net"] for r in c_rows])

    # NaN imputation with Quran median
    def _impute(q_arr, c_arr, name):
        q_valid = q_arr[np.isfinite(q_arr)]
        med = float(np.median(q_valid)) if len(q_valid) > 0 else 0.0
        n_q_nan = int(np.sum(~np.isfinite(q_arr)))
        n_c_nan = int(np.sum(~np.isfinite(c_arr)))
        q_out = np.where(np.isfinite(q_arr), q_arr, med)
        c_out = np.where(np.isfinite(c_arr), c_arr, med)
        print(f"[{EXP}] {name}: Q NaN={n_q_nan}, C NaN={n_c_nan}, "
              f"imputed with median={med:.4f}")
        return q_out, c_out, med, n_q_nan, n_c_nan

    phi_s_q_imp, phi_s_c_imp, phi_s_med, phi_s_qnan, phi_s_cnan = \
        _impute(phi_s_q, phi_s_c, "phi_structural")
    te_q_imp, te_c_imp, te_med, te_qnan, te_cnan = \
        _impute(te_q, te_c, "TE_net")

    # Assemble extended matrices
    X7_q = np.column_stack([X5_q, phi_s_q_imp.reshape(-1, 1),
                            te_q_imp.reshape(-1, 1)])
    X7_c = np.column_stack([X5_c, phi_s_c_imp.reshape(-1, 1),
                            te_c_imp.reshape(-1, 1)])
    feat_cols_7d = feat_cols_5d + ["phi_structural", "TE_net"]

    # 6-D variants (ablation)
    X6phi_q = np.column_stack([X5_q, phi_s_q_imp.reshape(-1, 1)])
    X6phi_c = np.column_stack([X5_c, phi_s_c_imp.reshape(-1, 1)])
    X6te_q = np.column_stack([X5_q, te_q_imp.reshape(-1, 1)])
    X6te_c = np.column_stack([X5_c, te_c_imp.reshape(-1, 1)])

    # --- T2: Baseline 5-D ---
    print(f"\n[{EXP}] === T2: Baseline 5-D Mahalanobis ===")
    res_5d = _mahalanobis_separation(X5_q, X5_c)
    sep_5d = res_5d["ctrl_separation"]
    print(f"[{EXP}] 5-D: coverage={res_5d['q_coverage']:.2%}, "
          f"separation={sep_5d:.2%}, tau={res_5d['tau']:.4f}")

    # --- T3: Extended 7-D ---
    print(f"\n[{EXP}] === T3: Extended 7-D Mahalanobis ===")
    res_7d = _mahalanobis_separation(X7_q, X7_c)
    sep_7d = res_7d["ctrl_separation"]
    print(f"[{EXP}] 7-D: coverage={res_7d['q_coverage']:.2%}, "
          f"separation={sep_7d:.2%}, tau={res_7d['tau']:.4f}")

    # --- T4: Δsep ---
    delta_sep = sep_7d - sep_5d
    print(f"\n[{EXP}] Δsep (7D - 5D) = {delta_sep:+.4f} ({delta_sep*100:+.2f} pp)")

    # --- T5: Per-feature ablation ---
    print(f"\n[{EXP}] === T5: Per-feature ablation ===")
    res_6phi = _mahalanobis_separation(X6phi_q, X6phi_c)
    res_6te = _mahalanobis_separation(X6te_q, X6te_c)
    delta_phi = res_6phi["ctrl_separation"] - sep_5d
    delta_te = res_6te["ctrl_separation"] - sep_5d
    print(f"[{EXP}] +phi_structural only (6-D): sep={res_6phi['ctrl_separation']:.2%}, "
          f"Δ={delta_phi:+.4f}")
    print(f"[{EXP}] +TE_net only (6-D):         sep={res_6te['ctrl_separation']:.2%}, "
          f"Δ={delta_te:+.4f}")

    # --- T6: VIF ---
    print(f"\n[{EXP}] === T6: VIF (collinearity) ===")
    X_all_7d = np.vstack([X7_q, X7_c])
    vifs = _vif(X_all_7d, feat_cols_7d)
    for fn, v in vifs.items():
        flag = " *** REDUNDANT" if v > 10 else ""
        print(f"  {fn:16s}: VIF = {v:.2f}{flag}")

    # --- T7: Permutation test ---
    print(f"\n[{EXP}] === T7: Permutation test ({N_PERM}x) ===")
    rng = np.random.RandomState(SEED)
    X_all_5 = np.vstack([X5_q, X5_c])
    X_all_7 = np.vstack([X7_q, X7_c])
    n_total = n_q + n_c
    null_deltas = np.empty(N_PERM)

    for b in range(N_PERM):
        perm = rng.permutation(n_total)
        pq = perm[:n_q]
        pc = perm[n_q:]
        s5 = _mahalanobis_separation(X_all_5[pq], X_all_5[pc])
        s7 = _mahalanobis_separation(X_all_7[pq], X_all_7[pc])
        null_deltas[b] = s7["ctrl_separation"] - s5["ctrl_separation"]

    p_perm = float(np.mean(null_deltas >= delta_sep))
    print(f"[{EXP}] Observed Δsep = {delta_sep:+.4f}")
    print(f"[{EXP}] Null Δsep: mean={null_deltas.mean():+.4f}, "
          f"std={null_deltas.std():.4f}")
    print(f"[{EXP}] p(perm) = {p_perm:.4f}")

    # --- Verdict ---
    per_feat_pass = (delta_phi >= 0) and (delta_te >= 0)
    any_vif_high = any(v > 10 for v in vifs.values())

    if delta_sep >= 0.01 and per_feat_pass and p_perm <= 0.01:
        verdict = "PROMOTED"
    elif delta_sep >= 0.01 or p_perm <= 0.05:
        verdict = "MARGINAL"
    else:
        verdict = "REDUNDANT"

    # Falsifier
    falsifier = "PASS"
    falsifier_reasons = []
    if delta_sep <= 0:
        falsifier = "FAIL"
        falsifier_reasons.append(f"Δsep={delta_sep:+.4f} ≤ 0")
    if any_vif_high:
        falsifier = "FAIL"
        new_vif = {k: v for k, v in vifs.items()
                   if k in ("phi_structural", "TE_net") and v > 10}
        if new_vif:
            falsifier_reasons.append(f"VIF > 10: {new_vif}")

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Δsep = {delta_sep:+.4f} (threshold ≥ 0.01)")
    print(f"  per-feat Δ: phi_structural={delta_phi:+.4f}, TE_net={delta_te:+.4f}")
    print(f"  p(perm) = {p_perm:.4f} (threshold ≤ 0.01)")
    print(f"  Falsifier: {falsifier}")
    if falsifier_reasons:
        for r in falsifier_reasons:
            print(f"    {r}")
    print(f"{'=' * 60}")

    # --- Per-corpus breakdown ---
    print(f"\n[{EXP}] Per-corpus separation (5-D → 7-D):")
    all_labels_c = [r["corpus"] for r in c_rows]
    for cname in ARABIC_CTRL:
        c_mask = np.array([l == cname for l in all_labels_c])
        if c_mask.sum() == 0:
            continue
        # Can't easily compute per-corpus separation without re-fitting.
        # Report per-corpus mean distances instead.
        print(f"  {cname:20s}: n={int(c_mask.sum())}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H28 — Do phi_structural and TE_net improve 5-D → 7-D "
                      "Mahalanobis separation?",
        "schema_version": 1,
        "data": {
            "n_quran": n_q,
            "n_ctrl": n_c,
            "feat_cols_5d": feat_cols_5d,
            "feat_cols_7d": feat_cols_7d,
            "imputation": {
                "phi_structural": {"median": phi_s_med, "q_nan": phi_s_qnan,
                                   "c_nan": phi_s_cnan},
                "TE_net": {"median": te_med, "q_nan": te_qnan,
                           "c_nan": te_cnan},
            },
        },
        "T2_baseline_5d": res_5d,
        "T3_extended_7d": res_7d,
        "T4_delta_sep": round(delta_sep, 6),
        "T5_ablation": {
            "phi_structural_only_6d": {
                "separation": res_6phi["ctrl_separation"],
                "delta_vs_5d": round(delta_phi, 6),
            },
            "TE_net_only_6d": {
                "separation": res_6te["ctrl_separation"],
                "delta_vs_5d": round(delta_te, 6),
            },
        },
        "T6_vif": vifs,
        "T7_permutation": {
            "observed_delta_sep": round(delta_sep, 6),
            "null_mean": round(float(null_deltas.mean()), 6),
            "null_std": round(float(null_deltas.std()), 6),
            "p_value": round(p_perm, 4),
            "n_permutations": N_PERM,
        },
        "verdict": {
            "verdict": verdict,
            "delta_sep": round(delta_sep, 4),
            "delta_phi": round(delta_phi, 4),
            "delta_te": round(delta_te, 4),
            "p_perm": round(p_perm, 4),
            "falsifier": falsifier,
            "falsifier_reasons": falsifier_reasons,
            "prereg_thresholds": {
                "PROMOTED": "Δsep ≥ 0.01 AND per-feat Δ ≥ 0 AND p ≤ 0.01",
                "MARGINAL": "Δsep ≥ 0.01 OR p ≤ 0.05",
                "REDUNDANT": "Δsep < 0.01 AND p > 0.05",
            },
        },
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
