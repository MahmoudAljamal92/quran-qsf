"""
exp64_unified_law_ensemble/run.py
==================================
H29: Multi-Variant Unified Law Ensemble (A1/A2/A3/A4) — Best of 5 Gate
Designs for Quran vs Control Separation.

Motivation
    build_pipeline_p3.py S9.2b implements four distinct unified-law gate
    designs operating in 2D (macro_z, micro_z) space. Each gate captures a
    different aspect of the Quran's structural uniqueness. Running all gates
    and reporting **consensus exclusion** per control corpus gives a robust,
    ensemble-level unified law that no single-gate reviewer critique can
    invalidate.

    We adapt the legacy 8-feature pipeline concept to our audited 5-D
    feature space:
      * macro_z = z-scored Phi_M (5-D Mahalanobis distance from ctrl
        centroid, higher = more Quran-like)
      * micro_z = z-scored phi_structural (0.5*H_dfa_jm + 0.5*K2 from
        v27_helpers, symmetric sub-score computable from bare text)

Protocol (frozen before execution)
    T1. Compute macro_z for ALL units (5-D Phi_M, z-scored by Quran).
    T2. Compute phi_structural for all units (from v27_helpers archive).
    T3. Build micro_z from phi_structural (z-scored by Quran).
    T4. Run 5 gate tests:
        A1: Linear sum  I_total = macro_z + micro_z >= Quran q5
        A2: Two-gate OR  macro_pass OR (macro_fail AND micro_rescue)
        A3-SVM: 2D One-Class SVM(nu=0.10) in (macro_z, micro_z)
        A3-KDE: 2D KDE density gate (5th percentile threshold)
        A4: Product  macro_z * micro_z >= Quran q5 of products
    T5. Per-corpus exclusion matrix (5 gates x N_corpora).
    T6. Consensus: count gates excluding >= 70% per control corpus.

Pre-registered thresholds
    STRONG:   consensus >= 3 of 5 gates for ALL controls
    MODERATE: consensus >= 2 of 5 for ALL controls
    WEAK:     consensus <= 1 for any control

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA, FEAT_COLS, mu, S_inv, lam

Writes ONLY under results/experiments/exp64_unified_law_ensemble/:
    exp64_unified_law_ensemble.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import gaussian_kde

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Import v27_helpers from archive for phi_structural computation
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

# Import v27_helpers functions we need
import v27_helpers as v27  # noqa: E402

EXP = "exp64_unified_law_ensemble"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

NU_SVM = 0.10            # One-Class SVM nu parameter (matches legacy S9.2b)
Q_FLOOR_PCT = 5           # 5th percentile for Quran floor thresholds
EXCLUSION_THRESHOLD = 0.70  # 70% exclusion = gate "excludes" that corpus
SEED = 42


# ---------------------------------------------------------------------------
# Mahalanobis helper
# ---------------------------------------------------------------------------
def _phi_m(X: np.ndarray, mu: np.ndarray, Sinv: np.ndarray) -> np.ndarray:
    X = np.atleast_2d(X)
    d = X - mu[None, :]
    return np.sqrt(np.einsum("ij,jk,ik->i", d, Sinv, d))


# ---------------------------------------------------------------------------
# Feature + micro computation for all units
# ---------------------------------------------------------------------------
def _compute_all_features(units: list, mu: np.ndarray, Sinv: np.ndarray,
                          corpus_name: str) -> list[dict]:
    """Compute 5-D features, Phi_M, phi_structural for each unit.
    Returns list of dicts with keys: label, n_verses, feats_5d, phi_m,
    phi_structural, te_net."""
    rows = []
    for u in units:
        if len(u.verses) < 3:
            continue
        try:
            f = ft.features_5d(u.verses)
            if np.any(np.isnan(f)) or np.any(np.isinf(f)):
                continue
        except Exception:
            continue

        phi_m_val = float(_phi_m(f.reshape(1, -1), mu, Sinv)[0])

        # phi_structural from v27_helpers (symmetric sub-score)
        bare_text = " ".join(u.verses)
        try:
            phi_s, _, _ = v27.phi_sukun_components(bare_text, None, u.verses)
        except Exception:
            phi_s = float("nan")
        if phi_s is None or not math.isfinite(phi_s):
            phi_s = float("nan")

        rows.append({
            "label": u.label,
            "corpus": corpus_name,
            "n_verses": len(u.verses),
            "feats_5d": f,
            "phi_m": phi_m_val,
            "phi_structural": phi_s,
        })
    return rows


def _sort_quran_units(units: list) -> list:
    def _num(u):
        if ":" in u.label:
            try:
                return int(u.label.split(":")[1])
            except ValueError:
                return 9999
        return 9999
    return sorted(units, key=_num)


# ---------------------------------------------------------------------------
# Gate implementations
# ---------------------------------------------------------------------------
def _gate_a1(macro_z: np.ndarray, micro_z: np.ndarray,
             q_mask: np.ndarray) -> np.ndarray:
    """A1: Linear sum I_total = macro_z + micro_z >= Quran q5."""
    i_total = macro_z + micro_z
    q_vals = i_total[q_mask & np.isfinite(i_total)]
    threshold = float(np.percentile(q_vals, Q_FLOOR_PCT))
    return (i_total >= threshold) & np.isfinite(i_total), threshold


def _gate_a2(macro_z: np.ndarray, micro_z: np.ndarray,
             q_mask: np.ndarray) -> np.ndarray:
    """A2: Two-gate OR — macro pass OR (macro fail AND micro rescue).
    macro_floor = Quran q5 of macro_z
    rescue_threshold = median micro_z of Quran macro-failures."""
    valid = np.isfinite(macro_z) & np.isfinite(micro_z)
    q_valid = q_mask & valid

    q_macro = macro_z[q_valid]
    macro_floor = float(np.percentile(q_macro, Q_FLOOR_PCT))

    # Rescue threshold from Quran macro-failures
    q_micro = micro_z[q_valid]
    q_macro_fail = q_macro < macro_floor
    if q_macro_fail.sum() >= 2:
        rescue_threshold = float(np.median(q_micro[q_macro_fail]))
    else:
        q_micro_all = micro_z[q_valid]
        rescue_threshold = float(np.percentile(q_micro_all, Q_FLOOR_PCT))

    macro_pass = macro_z >= macro_floor
    rescue = (~macro_pass) & (micro_z >= rescue_threshold)
    result = (macro_pass | rescue) & valid
    return result, {"macro_floor": macro_floor, "rescue_threshold": rescue_threshold}


def _gate_a3_svm(macro_z: np.ndarray, micro_z: np.ndarray,
                 q_mask: np.ndarray) -> np.ndarray:
    """A3-SVM: 2D One-Class SVM in (macro_z, micro_z) space."""
    try:
        from sklearn.svm import OneClassSVM
    except ImportError:
        # Return all-True if sklearn not available
        return np.ones(len(macro_z), dtype=bool), {"error": "sklearn not installed"}

    valid = np.isfinite(macro_z) & np.isfinite(micro_z)
    q_valid = q_mask & valid

    X_q = np.column_stack([macro_z[q_valid], micro_z[q_valid]])
    ocsvm = OneClassSVM(kernel="rbf", nu=NU_SVM, gamma="scale")
    ocsvm.fit(X_q)

    X_all = np.column_stack([macro_z, micro_z])
    pred = np.full(len(macro_z), -1)
    pred[valid] = ocsvm.predict(X_all[valid])
    return (pred == 1), {}


def _gate_a3_kde(macro_z: np.ndarray, micro_z: np.ndarray,
                 q_mask: np.ndarray) -> np.ndarray:
    """A3-KDE: 2D KDE density gate (5th percentile of Quran density)."""
    valid = np.isfinite(macro_z) & np.isfinite(micro_z)
    q_valid = q_mask & valid

    X_q = np.column_stack([macro_z[q_valid], micro_z[q_valid]])
    kde = gaussian_kde(X_q.T)
    q_dens = kde(X_q.T)
    threshold = float(np.percentile(q_dens, Q_FLOOR_PCT))

    X_all = np.column_stack([macro_z, micro_z])
    result = np.zeros(len(macro_z), dtype=bool)
    dens_all = np.zeros(len(macro_z))
    dens_all[valid] = kde(X_all[valid].T)
    result[valid] = dens_all[valid] >= threshold
    return result, {"kde_threshold": threshold}


def _gate_a4(macro_z: np.ndarray, micro_z: np.ndarray,
             q_mask: np.ndarray) -> np.ndarray:
    """A4: Product threshold  macro_z * micro_z >= Quran q5."""
    valid = np.isfinite(macro_z) & np.isfinite(micro_z)
    q_valid = q_mask & valid

    q_prods = macro_z[q_valid] * micro_z[q_valid]
    threshold = float(np.percentile(q_prods, Q_FLOOR_PCT))

    prods = macro_z * micro_z
    result = (prods >= threshold) & valid
    return result, {"product_threshold": threshold}


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

    # --- Load ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    Sinv_ctrl = np.asarray(state["S_inv"], dtype=float)
    lam = float(state["lam"])
    print(f"[{EXP}] FEAT_COLS={feat_cols}, TAU(lam)={lam:.4f}")

    # --- Compute features + micro for all corpora ---
    print(f"\n[{EXP}] Computing 5-D + micro features for all units...")
    quran_units = _sort_quran_units(CORPORA["quran"])
    all_rows = _compute_all_features(quran_units, mu_ctrl, Sinv_ctrl, "quran")
    n_q = len(all_rows)
    print(f"[{EXP}] Quran: {n_q} surahs with valid features")

    for cname in ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        c_rows = _compute_all_features(units, mu_ctrl, Sinv_ctrl, cname)
        all_rows.extend(c_rows)
        print(f"[{EXP}] {cname:20s}: {len(c_rows):5d} units")

    n_total = len(all_rows)
    print(f"[{EXP}] Total: {n_total} units")

    # --- Build arrays ---
    phi_m_arr = np.array([r["phi_m"] for r in all_rows])
    phi_s_arr = np.array([r["phi_structural"] for r in all_rows])
    corpus_arr = np.array([r["corpus"] for r in all_rows])
    q_mask = corpus_arr == "quran"

    # --- macro_z: z-scored Phi_M relative to Quran ---
    q_phi_m = phi_m_arr[q_mask]
    macro_mu = float(q_phi_m.mean())
    macro_std = float(q_phi_m.std(ddof=1))
    if macro_std < 1e-9:
        macro_std = 1.0
    macro_z = (phi_m_arr - macro_mu) / macro_std

    print(f"\n[{EXP}] macro_z (5-D Phi_M z-scored):")
    print(f"  Quran: mean={macro_z[q_mask].mean():+.3f} "
          f"std={macro_z[q_mask].std():.3f}")
    print(f"  Controls: mean={macro_z[~q_mask].mean():+.3f} "
          f"std={macro_z[~q_mask].std():.3f}")

    # --- micro_z: z-scored phi_structural relative to Quran ---
    q_phi_s = phi_s_arr[q_mask]
    q_phi_s_valid = q_phi_s[np.isfinite(q_phi_s)]
    n_micro_valid = len(q_phi_s_valid)
    print(f"\n[{EXP}] phi_structural: {n_micro_valid}/{n_q} Quran surahs valid")

    if n_micro_valid < 10:
        print(f"[{EXP}] ERROR: too few valid phi_structural values. Aborting.")
        return 1

    micro_mu = float(q_phi_s_valid.mean())
    micro_std = float(q_phi_s_valid.std(ddof=1))
    if micro_std < 1e-9:
        micro_std = 1.0
    micro_z = (phi_s_arr - micro_mu) / micro_std

    print(f"[{EXP}] micro_z (phi_structural z-scored):")
    print(f"  Quran: mean={micro_z[q_mask & np.isfinite(micro_z)].mean():+.3f} "
          f"std={micro_z[q_mask & np.isfinite(micro_z)].std():.3f}")
    ctrl_micro_valid = micro_z[~q_mask & np.isfinite(micro_z)]
    if len(ctrl_micro_valid) > 0:
        print(f"  Controls: mean={ctrl_micro_valid.mean():+.3f} "
              f"std={ctrl_micro_valid.std():.3f}")

    # --- Run gates ---
    print(f"\n[{EXP}] === Running 5 gate tests ===")

    gates = {}

    # A1
    a1_pass, a1_thresh = _gate_a1(macro_z, micro_z, q_mask)
    gates["A1_linear"] = a1_pass
    print(f"  A1 threshold (I_total q{Q_FLOOR_PCT}): {a1_thresh:+.4f}")

    # A2
    a2_pass, a2_info = _gate_a2(macro_z, micro_z, q_mask)
    gates["A2_twogatOR"] = a2_pass
    print(f"  A2 macro_floor: {a2_info['macro_floor']:+.4f}, "
          f"rescue: {a2_info['rescue_threshold']:+.4f}")

    # A3-SVM
    a3s_pass, a3s_info = _gate_a3_svm(macro_z, micro_z, q_mask)
    gates["A3_SVM"] = a3s_pass
    if "error" in a3s_info:
        print(f"  A3-SVM: {a3s_info['error']}")
    else:
        print(f"  A3-SVM fitted (nu={NU_SVM})")

    # A3-KDE
    a3k_pass, a3k_info = _gate_a3_kde(macro_z, micro_z, q_mask)
    gates["A3_KDE"] = a3k_pass
    print(f"  A3-KDE threshold: {a3k_info.get('kde_threshold', 'N/A')}")

    # A4
    a4_pass, a4_info = _gate_a4(macro_z, micro_z, q_mask)
    gates["A4_product"] = a4_pass
    print(f"  A4 product threshold: {a4_info['product_threshold']:+.4f}")

    # --- Per-corpus exclusion matrix ---
    print(f"\n[{EXP}] === Per-Corpus Exclusion Matrix ===")
    gate_names = list(gates.keys())
    corpus_names = ["quran"] + ARABIC_CTRL

    # Header
    hdr = f"{'Corpus':20s}"
    for gn in gate_names:
        hdr += f"  {gn:>12s}"
    hdr += f"  {'consensus':>10s}"
    print(hdr)
    print("-" * len(hdr))

    exclusion_matrix = {}
    consensus_results = {}
    for cname in corpus_names:
        c_mask = corpus_arr == cname
        n_c = int(c_mask.sum())
        if n_c == 0:
            continue

        row = {}
        for gn in gate_names:
            n_pass = int(gates[gn][c_mask].sum())
            n_excluded = n_c - n_pass
            excl_pct = 100.0 * n_excluded / n_c
            row[gn] = {
                "n_pass": n_pass,
                "n_excluded": n_excluded,
                "n_total": n_c,
                "exclusion_pct": round(excl_pct, 1),
            }

        # Consensus = count of gates that exclude >= EXCLUSION_THRESHOLD
        consensus = sum(
            1 for gn in gate_names
            if row[gn]["exclusion_pct"] >= EXCLUSION_THRESHOLD * 100
        )

        exclusion_matrix[cname] = row
        consensus_results[cname] = consensus

        line = f"{cname:20s}"
        for gn in gate_names:
            ep = row[gn]["exclusion_pct"]
            marker = "*" if ep >= EXCLUSION_THRESHOLD * 100 else " "
            line += f"  {ep:11.1f}{marker}"
        line += f"  {consensus:10d}/5"
        is_q = " ***" if cname == "quran" else ""
        print(f"{line}{is_q}")

    # --- Quran coverage (how many Quran surahs PASS each gate) ---
    print(f"\n[{EXP}] Quran coverage per gate:")
    quran_coverage = {}
    for gn in gate_names:
        n_pass = int(gates[gn][q_mask].sum())
        pct = 100.0 * n_pass / n_q
        quran_coverage[gn] = {"n_pass": n_pass, "n_total": n_q, "pct": round(pct, 1)}
        print(f"  {gn:12s}: {n_pass}/{n_q} ({pct:.1f}%)")

    # --- Verdict ---
    ctrl_only = {k: v for k, v in consensus_results.items() if k != "quran"}
    min_consensus = min(ctrl_only.values()) if ctrl_only else 0
    mean_consensus = float(np.mean(list(ctrl_only.values()))) if ctrl_only else 0.0

    if min_consensus >= 3:
        verdict = "STRONG"
    elif min_consensus >= 2:
        verdict = "MODERATE"
    else:
        verdict = "WEAK"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Min consensus across controls: {min_consensus}/5")
    print(f"  Mean consensus: {mean_consensus:.1f}/5")
    for cname, cons in sorted(ctrl_only.items(), key=lambda x: x[1]):
        print(f"    {cname:20s}: {cons}/5")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H29 — Multi-variant unified law ensemble: do 5 independent "
                      "gate designs consistently exclude control corpora?",
        "schema_version": 1,
        "data": {
            "n_quran": n_q,
            "n_total": n_total,
            "n_micro_valid_quran": n_micro_valid,
            "feat_cols": feat_cols,
            "tau_lam": lam,
            "macro_z_ref": {"mu": macro_mu, "std": macro_std},
            "micro_z_ref": {"mu": micro_mu, "std": micro_std},
        },
        "gate_parameters": {
            "A1_linear": {"threshold": a1_thresh},
            "A2_twogatOR": a2_info,
            "A3_SVM": {"nu": NU_SVM, "kernel": "rbf", "gamma": "scale"},
            "A3_KDE": a3k_info,
            "A4_product": a4_info,
            "q_floor_percentile": Q_FLOOR_PCT,
            "exclusion_threshold": EXCLUSION_THRESHOLD,
        },
        "exclusion_matrix": exclusion_matrix,
        "quran_coverage": quran_coverage,
        "consensus": consensus_results,
        "verdict": {
            "verdict": verdict,
            "min_consensus": min_consensus,
            "mean_consensus": round(mean_consensus, 2),
            "prereg_thresholds": {
                "STRONG": "consensus >= 3 of 5 for ALL controls",
                "MODERATE": "consensus >= 2 of 5 for ALL controls",
                "WEAK": "consensus <= 1 for any control",
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
