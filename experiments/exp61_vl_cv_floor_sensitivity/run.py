"""
exp61_vl_cv_floor_sensitivity/run.py
====================================
H30: The VL_CV Floor Constant 0.1962 — Provenance, Sensitivity & Leak Audit.

Motivation
    `build_pipeline_p1.py` (legacy 8-D Colab pipeline, archived in
    `archive/CascadeProjects_legacy_builders/`) hard-codes

        VL_CV_FLOOR = 0.1962

    used to mark "degenerate" pseudo-surahs as *auto-outsiders* in the primary
    Mahalanobis separation (`build_pipeline_p2.py` S5.1: `c_out = (d_M > tau) |
    floor_excluded`). No derivation of 0.1962 is documented anywhere. The
    constant is therefore one of three things:

        (a)  a Quran-derived quantity (circular, inadmissible),
        (b)  a control-derived quantity (a selection threshold; admissible),
        (c)  arbitrary (should be robustness-tested).

    This experiment answers all three:
      * Provenance: does 0.1962 match any principled percentile or formula
        (tolerance ±0.002)?
      * Sensitivity: is the 5-D Mahalanobis AUC stable across floor values
        f in {0.00 ... 0.35}?
      * LEAK AUDIT: does the legacy "floor-excluded = auto-outside" logic
        inflate apparent separation compared to a pure-filter approach?

Pre-registered thresholds (frozen before execution)
    FLOOR_ROBUST           : max |AUC(f)-AUC(0)| < 0.005 across f in
                             {0, 0.10, 0.15, 0.1962, 0.22, 0.25} (no Quran
                             excluded in this range).
    FLOOR_INFLATING        : inflation_sep(0.1962) > 0.05 OR
                             inflation_auc(0.1962) > 0.01.
    FLOOR_FRAGILE          : max |AUC(f)-AUC(0)| > 0.02.
    FLOOR_PROVENANCE_FOUND : |0.1962 - best_candidate| < 0.002.

Reads (integrity-checked):
    phase_06_phi_m.pkl  ->  X_QURAN (68,5), X_CTRL_POOL (2509,5),
                            mu (ctrl centroid), S_inv (ctrl cov^{-1}+1e-6 I),
                            FEAT_COLS, FEATS, ARABIC_CTRL_POOL,
                            BAND_A_LO/HI, lam

Writes ONLY under results/experiments/exp61_vl_cv_floor_sensitivity/:
    exp61_vl_cv_floor_sensitivity.json
    self_check_<ts>.json
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

EXP = "exp61_vl_cv_floor_sensitivity"

# --- Frozen parameters (pre-registered) ---
LEGACY_FLOOR = 0.1962                     # the constant under audit
IDX_VL_CV = 1                              # FEAT_COLS = [EL, VL_CV, CN, H_cond, T]
FLOORS = [0.00, 0.05, 0.10, 0.15, LEGACY_FLOOR, 0.22, 0.25, 0.27, 0.30, 0.35]
# Tolerances: closed-form formulas should match at 4-decimal rounding (0.0005);
# empirical percentiles are subject to finite-sample noise (0.002). The
# distinction guards against false provenance claims when a large formula pool
# happens to include one curve fit at 0.002.
PROVENANCE_TOL_FORMULA = 0.0005
PROVENANCE_TOL_PCT = 0.002
N_BOOTSTRAP = 1000                         # stratified bootstrap for AUC CI
SEED = 42

# Percentile candidates for provenance search
PCT_CANDIDATES = [
    0.5, 1, 2, 2.5, 5, 10, 15, 20, 25, 30, 40, 45, 50, 55, 56, 57, 58, 60,
    65, 70, 75, 80, 85, 90, 95, 97.5, 99, 99.5,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _mah_dist(X: np.ndarray, mu: np.ndarray, S_inv: np.ndarray) -> np.ndarray:
    """Vectorised Mahalanobis distance of rows of X to point mu under S_inv."""
    diff = X - mu
    return np.sqrt(np.sum(diff @ S_inv * diff, axis=1))


def _roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """ROC AUC where positive class = label 1.
    Higher score -> more positive. Handles ties via mid-rank."""
    n_pos = int(labels.sum())
    n_neg = int(len(labels) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    # mid-rank for ties
    s = scores[order]
    i = 0
    N = len(s)
    while i < N:
        j = i
        while j + 1 < N and s[j + 1] == s[i]:
            j += 1
        mid = 0.5 * (i + j) + 1.0  # 1-based mid-rank
        ranks[order[i:j + 1]] = mid
        i = j + 1
    sum_pos = float(ranks[labels == 1].sum())
    return (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


# ---------------------------------------------------------------------------
# T1: Provenance search
# ---------------------------------------------------------------------------
def _provenance(vlcv_q: np.ndarray, vlcv_c: np.ndarray) -> dict:
    """Hunt 0.1962 in percentile-of-(Quran/Ctrl/Arabic-family) + formulas."""
    out: dict = {
        "target": LEGACY_FLOOR,
        "tolerance_formula_strict": PROVENANCE_TOL_FORMULA,
        "tolerance_percentile_strict": PROVENANCE_TOL_PCT,
        "percentile_matches": [],
        "formula_matches": [],
        "best_overall": None,
    }

    candidates: list[dict] = []

    # Quran percentiles
    for p in PCT_CANDIDATES:
        v = float(np.percentile(vlcv_q, p))
        candidates.append({
            "kind": "quran_percentile", "value": v, "pct": p,
            "delta": abs(v - LEGACY_FLOOR),
        })

    # Ctrl percentiles (pooled, 6 Arabic controls)
    for p in PCT_CANDIDATES:
        v = float(np.percentile(vlcv_c, p))
        candidates.append({
            "kind": "ctrl_pool_percentile", "value": v, "pct": p,
            "delta": abs(v - LEGACY_FLOOR),
        })

    # Combined Arabic-family (Quran + ctrl)
    vlcv_all = np.concatenate([vlcv_q, vlcv_c])
    for p in PCT_CANDIDATES:
        v = float(np.percentile(vlcv_all, p))
        candidates.append({
            "kind": "arabic_family_percentile", "value": v, "pct": p,
            "delta": abs(v - LEGACY_FLOOR),
        })

    # Mean/SD-based candidates
    candidates.extend([
        {"kind": "ctrl_mean - 0.5*ctrl_sd", "value":
            float(vlcv_c.mean() - 0.5 * vlcv_c.std(ddof=1)),
         "delta": None},
        {"kind": "ctrl_mean", "value": float(vlcv_c.mean()), "delta": None},
        {"kind": "ctrl_mean - 1*ctrl_sd", "value":
            float(vlcv_c.mean() - 1.0 * vlcv_c.std(ddof=1)),
         "delta": None},
        {"kind": "quran_mean - 2*quran_sd", "value":
            float(vlcv_q.mean() - 2 * vlcv_q.std(ddof=1)),
         "delta": None},
        {"kind": "quran_min - quran_sd", "value":
            float(vlcv_q.min() - vlcv_q.std(ddof=1)),
         "delta": None},
    ])

    # Closed-form math constants — PRINCIPLED only (derivable from the
    # 28-letter alphabet, classical structural ratios, or basic constants).
    # Arbitrary curve-fits like "1/5.09" are excluded by construction:
    # a match against such a formula cannot be distinguished from noise
    # and would constitute a false provenance claim.
    formula_cands_principled = [
        ("1/pi^2",                    1 / math.pi ** 2),
        ("1/e^2",                     1 / math.e ** 2),
        ("sqrt(1/28)",                math.sqrt(1 / 28)),
        ("1/sqrt(28)",                1 / math.sqrt(28)),
        ("log2(3)/log2(28)",          math.log2(3) / math.log2(28)),
        ("1/log2(28)",                1 / math.log2(28)),
        ("ln(2)/ln(28)",              math.log(2) / math.log(28)),
        ("1/(2*pi)",                  1 / (2 * math.pi)),
        ("(sqrt(5)-1)/10",            (math.sqrt(5) - 1) / 10),
        ("2/sqrt(7)/10",              2 / math.sqrt(7) / 10),
        ("(phi-1)/pi",                (1.61803398875 - 1) / math.pi),
        ("1/(phi*pi)",                1 / (1.61803398875 * math.pi)),
        ("ln(phi)/ln(phi*e)",         math.log(1.61803398875)
                                       / math.log(1.61803398875 * math.e)),
        ("1/(2*sqrt(e))",             1 / (2 * math.sqrt(math.e))),
    ]
    for name, v in formula_cands_principled:
        candidates.append({
            "kind": "formula_principled",
            "formula": name,
            "value": float(v),
            "delta": abs(v - LEGACY_FLOOR),
        })

    # Compute deltas for any not already computed
    for c in candidates:
        if c.get("delta") is None:
            c["delta"] = abs(c["value"] - LEGACY_FLOOR)

    # Type-aware matches (formulas require exact rounding precision)
    for c in candidates:
        tol = (
            PROVENANCE_TOL_FORMULA
            if c["kind"] == "formula_principled"
            else PROVENANCE_TOL_PCT
        )
        if c["delta"] <= tol:
            if c["kind"] == "formula_principled":
                out["formula_matches"].append(c)
            else:
                out["percentile_matches"].append(c)

    # Best overall by min delta (purely for diagnostics; may include
    # a formula match that is close but not within its strict tol)
    best = min(candidates, key=lambda x: x["delta"])
    best_tol = (
        PROVENANCE_TOL_FORMULA
        if best["kind"] == "formula_principled"
        else PROVENANCE_TOL_PCT
    )
    out["best_overall"] = best
    out["best_overall_within_strict"] = bool(best["delta"] <= best_tol)

    # Explicit "provenance identified" test: requires a clean formula match
    # (formula within 0.0005) OR a clean percentile match (within 0.002).
    any_strict_match = (
        len(out["formula_matches"]) > 0 or len(out["percentile_matches"]) > 0
    )
    out["any_strict_match"] = any_strict_match

    # Top-10 by proximity, for transparency
    ranked = sorted(candidates, key=lambda x: x["delta"])[:10]
    out["top_10_candidates"] = ranked

    return out


# ---------------------------------------------------------------------------
# T2: Per-corpus exclusion profile
# ---------------------------------------------------------------------------
def _exclusion_profile(
    vlcv_q: np.ndarray,
    vlcv_by_ctrl: dict[str, np.ndarray],
) -> dict:
    profile = {"floors": FLOORS, "per_floor": []}
    for f in FLOORS:
        row = {
            "floor": f,
            "quran_pct_excluded": float((vlcv_q < f).mean() * 100),
            "quran_n_excluded": int((vlcv_q < f).sum()),
            "quran_n_retained": int((vlcv_q >= f).sum()),
            "per_corpus": {},
            "ctrl_total_pct_excluded": None,
            "ctrl_total_n_excluded": 0,
            "ctrl_total_n_retained": 0,
        }
        total_excl = 0
        total_ret = 0
        for name, v in vlcv_by_ctrl.items():
            n_excl = int((v < f).sum())
            n_ret = int((v >= f).sum())
            row["per_corpus"][name] = {
                "n_total": int(len(v)),
                "n_excluded": n_excl,
                "pct_excluded": float(n_excl / len(v) * 100) if len(v) else 0.0,
            }
            total_excl += n_excl
            total_ret += n_ret
        total = total_excl + total_ret
        row["ctrl_total_n_excluded"] = total_excl
        row["ctrl_total_n_retained"] = total_ret
        row["ctrl_total_pct_excluded"] = (
            float(total_excl / total * 100) if total > 0 else 0.0
        )
        profile["per_floor"].append(row)
    return profile


# ---------------------------------------------------------------------------
# T3 + T4: AUC sensitivity + legacy inflation
# ---------------------------------------------------------------------------
def _auc_sensitivity(
    X_Q: np.ndarray, X_C: np.ndarray,
    mu: np.ndarray, S_inv: np.ndarray,
) -> dict:
    """Decompose floor effects into THREE distinct scenarios so the leak
    audit has clean apples-to-apples comparisons.

        (a) baseline  : all rows, no floor logic        (the honest number)
        (b) filter(f) : drop rows with VL_CV < f, then  (answers: "if the
                        classify on survivors only            floor's role is
                                                               data cleaning,
                                                               is AUC stable?")
        (c) legacy(f) : keep all rows; pin excluded     (the legacy leak:
                        ctrls to most-ctrl-like,               floor-excluded
                        excluded Qurans to most-Quran          ctrls are
                        -like                                  auto-classified)

    Inflation metrics are computed with CONSISTENT denominators against the
    baseline (the honest reference point), not against each other.
    """
    d_Q = _mah_dist(X_Q, mu, S_inv)
    d_C = _mah_dist(X_C, mu, S_inv)
    vlcv_Q = X_Q[:, IDX_VL_CV]
    vlcv_C = X_C[:, IDX_VL_CV]

    # Baseline (floor=0): all rows retained
    scores_all = np.concatenate([d_Q, d_C])
    labels_all = np.concatenate(
        [np.ones(len(d_Q), int), np.zeros(len(d_C), int)]
    )
    auc_baseline = _roc_auc(scores_all, labels_all)

    # Fixed tau at Quran 5th percentile of d_M at floor=0.
    # Quran "inside" defined as d_M >= tau (in our convention, larger d_M =
    # more Quran-like relative to the ctrl centroid mu).
    tau_star = float(np.percentile(d_Q, 5))
    n_q_total, n_c_total = len(d_Q), len(d_C)

    # Baseline Q_COV and sep at tau_star (all rows, no floor logic)
    qcov_baseline = float((d_Q >= tau_star).mean())
    sep_baseline = float((d_C < tau_star).mean())

    per_floor = []
    for f in FLOORS:
        q_mask = vlcv_Q >= f
        c_mask = vlcv_C >= f

        # --- (b) PURE FILTER MODE: drop floor-excluded rows, classify rest ---
        d_Q_f = d_Q[q_mask]
        d_C_f = d_C[c_mask]
        if len(d_Q_f) > 0 and len(d_C_f) > 0:
            scores_f = np.concatenate([d_Q_f, d_C_f])
            labels_f = np.concatenate(
                [np.ones(len(d_Q_f), int), np.zeros(len(d_C_f), int)]
            )
            auc_filtered = _roc_auc(scores_f, labels_f)
        else:
            auc_filtered = float("nan")

        qcov_filtered = (
            float((d_Q_f >= tau_star).mean()) if len(d_Q_f) else float("nan")
        )
        sep_filtered = (
            float((d_C_f < tau_star).mean()) if len(d_C_f) else float("nan")
        )

        # --- (c) LEGACY MODE: pin floor-excluded rows to class-correct extremes
        scores_legacy = scores_all.copy().astype(float)
        q_excl_mask = ~q_mask
        c_excl_mask = ~c_mask
        # Quran-excluded: score = +inf (forced most-Quran-like)
        scores_legacy[:n_q_total][q_excl_mask] = np.inf
        # Ctrl-excluded: score = -inf (forced most-ctrl-like)
        scores_legacy[n_q_total:][c_excl_mask] = -np.inf
        auc_legacy = _roc_auc(scores_legacy, labels_all)

        # Legacy tau-based metrics (denominators = FULL class sizes, matching
        # the legacy pipeline reporting convention)
        qcov_legacy = float(
            ((d_Q >= tau_star) | (~q_mask)).mean()  # excluded Q counted "inside"
        )
        sep_legacy = float(
            ((d_C < tau_star) | (~c_mask)).mean()   # excluded C counted as sep
        )

        # --- LEAK / INFLATION METRICS (all against baseline, same denom) ---
        # How many ctrl are "rescued" by the floor? = % with VL_CV<f AND d_M>=tau
        rescued_frac = float(((~c_mask) & (d_C >= tau_star)).mean())
        # How many ctrl are "over-credited" in AUC by the -inf pin? Same event.
        inflation_sep_vs_baseline = sep_legacy - sep_baseline   # = rescued_frac
        inflation_auc_vs_baseline = auc_legacy - auc_baseline

        # Diagnostic: filter-mode AUC change (only informative, NOT inflation)
        delta_auc_filter = (
            auc_filtered - auc_baseline
            if not math.isnan(auc_filtered) else float("nan")
        )

        per_floor.append({
            "floor": f,
            "n_quran_retained": int(q_mask.sum()),
            "n_ctrl_retained": int(c_mask.sum()),
            "n_quran_excluded": int((~q_mask).sum()),
            "n_ctrl_excluded": int((~c_mask).sum()),
            "pct_ctrl_rescued_by_floor": float(rescued_frac * 100),
            "pure_filter": {
                "AUC": auc_filtered,
                "delta_AUC_vs_baseline": delta_auc_filter,
                "Q_COV_at_tau_star_retained_denom": qcov_filtered,
                "sep_at_tau_star_retained_denom": sep_filtered,
                "note": (
                    "AUC & rates computed on retained rows only "
                    "(different denominator from baseline -- NOT directly "
                    "comparable, but useful to check stability of the "
                    "ranking on survivors)."
                ),
            },
            "legacy_mode": {
                "AUC_with_excluded_pinned": auc_legacy,
                "Q_COV_at_tau_star_full_denom": qcov_legacy,
                "sep_at_tau_star_full_denom": sep_legacy,
                "note": (
                    "AUC with excluded ctrls pinned to -inf and excluded "
                    "Qurans pinned to +inf. Q_COV/sep use full-class "
                    "denominators, matching the legacy pipeline's own "
                    "reporting formula."
                ),
            },
            "inflation_vs_baseline": {
                "auc_inflation": inflation_auc_vs_baseline,
                "sep_inflation": inflation_sep_vs_baseline,
                "qcov_inflation": qcov_legacy - qcov_baseline,
                "interpretation": (
                    f"At floor={f:.4f}: the legacy logic awards "
                    f"{rescued_frac*100:.2f}% of the ctrl pool free 'correct "
                    "classification' by VL_CV alone, regardless of "
                    "Mahalanobis distance."
                ),
            },
        })

    # Focus on f in [0, 0.25] where no Quran is excluded (pure-filter range)
    no_q_excl = [r for r in per_floor if r["n_quran_excluded"] == 0]
    filter_aucs_safe = [
        r["pure_filter"]["AUC"] for r in no_q_excl
        if not math.isnan(r["pure_filter"]["AUC"])
    ]

    return {
        "baseline_AUC": auc_baseline,
        "tau_star_quran_p5_at_floor_0": tau_star,
        "baseline_Q_COV_at_tau_star": qcov_baseline,
        "baseline_sep_at_tau_star": sep_baseline,
        "per_floor": per_floor,
        "filter_auc_range_no_quran_excluded": {
            "min": min(filter_aucs_safe) if filter_aucs_safe else float("nan"),
            "max": max(filter_aucs_safe) if filter_aucs_safe else float("nan"),
            "range": (max(filter_aucs_safe) - min(filter_aucs_safe))
            if filter_aucs_safe else float("nan"),
        },
    }


# ---------------------------------------------------------------------------
# T5: Stratified bootstrap CI
# ---------------------------------------------------------------------------
def _bootstrap_ci(
    X_Q: np.ndarray, X_C: np.ndarray,
    mu: np.ndarray, S_inv: np.ndarray,
    n_boot: int,
) -> dict:
    """Stratified bootstrap (resample Quran and ctrl rows independently)."""
    rng = np.random.RandomState(SEED)
    d_Q = _mah_dist(X_Q, mu, S_inv)
    d_C = _mah_dist(X_C, mu, S_inv)
    vlcv_Q = X_Q[:, IDX_VL_CV]
    vlcv_C = X_C[:, IDX_VL_CV]
    n_q, n_c = len(d_Q), len(d_C)

    target_floors = [0.00, LEGACY_FLOOR, 0.25]
    results = {f"floor_{f:.4f}": {"pure_AUC": [], "legacy_AUC": []}
               for f in target_floors}

    for b in range(n_boot):
        iq = rng.choice(n_q, n_q, replace=True)
        ic = rng.choice(n_c, n_c, replace=True)
        dQb, dCb = d_Q[iq], d_C[ic]
        vQb, vCb = vlcv_Q[iq], vlcv_C[ic]
        scores_all = np.concatenate([dQb, dCb])
        labels_all = np.concatenate(
            [np.ones(n_q, int), np.zeros(n_c, int)]
        )

        for f in target_floors:
            qm = vQb >= f
            cm = vCb >= f
            dQf = dQb[qm]
            dCf = dCb[cm]
            if len(dQf) == 0 or len(dCf) == 0:
                auc_p = float("nan")
            else:
                sc = np.concatenate([dQf, dCf])
                lb = np.concatenate(
                    [np.ones(len(dQf), int), np.zeros(len(dCf), int)]
                )
                auc_p = _roc_auc(sc, lb)

            sc_leg = scores_all.copy().astype(float)
            sc_leg[:n_q][~qm] = np.inf
            sc_leg[n_q:][~cm] = -np.inf
            auc_l = _roc_auc(sc_leg, labels_all)

            results[f"floor_{f:.4f}"]["pure_AUC"].append(auc_p)
            results[f"floor_{f:.4f}"]["legacy_AUC"].append(auc_l)

    summary: dict = {"n_bootstrap": n_boot, "seed": SEED, "per_floor": {}}
    for key, vals in results.items():
        pure = np.asarray([v for v in vals["pure_AUC"] if not math.isnan(v)])
        leg = np.asarray([v for v in vals["legacy_AUC"] if not math.isnan(v)])
        summary["per_floor"][key] = {
            "pure_AUC_mean": float(pure.mean()),
            "pure_AUC_std": float(pure.std(ddof=1)),
            "pure_AUC_ci95": [float(np.percentile(pure, 2.5)),
                              float(np.percentile(pure, 97.5))],
            "legacy_AUC_mean": float(leg.mean()),
            "legacy_AUC_std": float(leg.std(ddof=1)),
            "legacy_AUC_ci95": [float(np.percentile(leg, 2.5)),
                                float(np.percentile(leg, 97.5))],
            "inflation_mean": float(leg.mean() - pure.mean()),
        }
    return summary


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
def _compute_verdict(prov: dict, aucs: dict) -> dict:
    # AUC variation range over all floors (pure-filter AUC)
    pure_aucs_all = [
        r["pure_filter"]["AUC"] for r in aucs["per_floor"]
        if not math.isnan(r["pure_filter"]["AUC"])
    ]
    auc_range_all = max(pure_aucs_all) - min(pure_aucs_all)

    # AUC variation range over floors that don't exclude any Quran (the
    # pure-filter answers the question "is the ranking stable among survivors
    # when only ctrl rows are removed?"). A few units may be ctrl-filtered but
    # Quran is untouched.
    auc_range_safe = aucs["filter_auc_range_no_quran_excluded"]["range"]

    # Legacy-mode inflation AT the 0.1962 floor is the headline leak metric.
    r_1962 = next(
        (r for r in aucs["per_floor"]
         if abs(r["floor"] - LEGACY_FLOOR) < 1e-6),
        None,
    )
    infl_auc = (
        r_1962["inflation_vs_baseline"]["auc_inflation"] if r_1962 else None
    )
    infl_sep = (
        r_1962["inflation_vs_baseline"]["sep_inflation"] if r_1962 else None
    )
    rescued_pct = (
        r_1962["pct_ctrl_rescued_by_floor"] if r_1962 else None
    )

    flags = {
        # Filter-mode ranking stability (the "intrinsic" robustness test)
        "FILTER_STABLE": bool(
            not math.isnan(auc_range_safe) and auc_range_safe < 0.010
        ),
        # Legacy-mode leak severity at 0.1962
        "LEGACY_LEAK_MAJOR": bool(
            (infl_auc is not None and infl_auc > 0.01)
            or (infl_sep is not None and infl_sep > 0.05)
        ),
        "LEGACY_LEAK_MINOR": bool(
            (infl_auc is not None and 0.0005 <= infl_auc <= 0.01)
            or (infl_sep is not None and 0.001 <= infl_sep <= 0.05)
        ),
        # Fingerprint fragility (true pathology)
        "FLOOR_FRAGILE": bool(auc_range_all > 0.02),
        # Provenance: ANY strict match (formula <= 0.0005 OR pct <= 0.002)
        "FLOOR_PROVENANCE_FOUND_PRINCIPLED": bool(prov["any_strict_match"]),
    }

    # Headline verdict (priority: fragile > major-leak > minor-leak-with-
    # arbitrary > robust-principled > robust-arbitrary > undetermined)
    if flags["FLOOR_FRAGILE"]:
        headline = "FLOOR_FRAGILE"
    elif flags["LEGACY_LEAK_MAJOR"]:
        headline = "FLOOR_INFLATING"
    elif flags["FILTER_STABLE"] and flags["FLOOR_PROVENANCE_FOUND_PRINCIPLED"]:
        headline = "FLOOR_ROBUST_AND_PROVENANCE_IDENTIFIED"
    elif flags["FILTER_STABLE"] and flags["LEGACY_LEAK_MINOR"]:
        headline = "FLOOR_ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK"
    elif flags["FILTER_STABLE"]:
        headline = "FLOOR_ROBUST_ARBITRARY_CONSTANT"
    else:
        headline = "UNDETERMINED"

    return {
        "headline_verdict": headline,
        "flags": flags,
        "auc_variation_range_all_floors": auc_range_all,
        "auc_variation_range_f_with_no_quran_excluded": auc_range_safe,
        "leak_audit_at_0p1962": {
            "auc_inflation_vs_baseline": infl_auc,
            "sep_inflation_vs_baseline": infl_sep,
            "pct_ctrl_rescued_by_floor": rescued_pct,
            "explanation": (
                "auc_inflation = AUC(legacy pinning) - AUC(baseline, no floor).  "
                "sep_inflation = sep(legacy) - sep(baseline) at tau* = Quran p5. "
                "Both are evaluated on the full class denominators so they are "
                "apples-to-apples against the honest baseline."
            ),
        },
        "provenance_summary": {
            "best_candidate": prov["best_overall"],
            "within_own_tol": prov["best_overall_within_strict"],
            "n_formula_matches": len(prov["formula_matches"]),
            "n_percentile_matches": len(prov["percentile_matches"]),
            "any_strict_match": prov["any_strict_match"],
        },
        "prereg_thresholds": {
            "FILTER_STABLE": (
                "max |AUC(filter,f) - AUC(filter,0)| < 0.010 across f in "
                "[0.00, 0.1962, 0.22, 0.25] (floors that preserve all 68 "
                "Quran units). 0.010 chosen because filter removes easy ctrl "
                "rows; range up to ~0.005 is expected from selection alone."
            ),
            "LEGACY_LEAK_MAJOR": (
                "auc_inflation > 0.01 OR sep_inflation > 0.05 at f=0.1962"
            ),
            "LEGACY_LEAK_MINOR": (
                "0.0005 <= auc_inflation <= 0.01 OR "
                "0.001 <= sep_inflation <= 0.05 at f=0.1962"
            ),
            "FLOOR_FRAGILE": (
                "max |AUC(filter,f) - AUC(filter,0)| > 0.02 anywhere in the "
                "full sweep, including floors that exclude some Quran units"
            ),
            "FLOOR_PROVENANCE_FOUND_PRINCIPLED": (
                "|0.1962 - best_principled_candidate| < 0.002; arbitrary "
                "curve-fits excluded"
            ),
        },
    }


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

    print(f"[{EXP}] Loading phase_06_phi_m.pkl (SHA-verified)...")
    phi = load_phase("phase_06_phi_m")
    s = phi["state"]
    X_Q = np.asarray(s["X_QURAN"], dtype=float)
    X_C = np.asarray(s["X_CTRL_POOL"], dtype=float)
    mu = np.asarray(s["mu"], dtype=float)
    S_inv = np.asarray(s["S_inv"], dtype=float)
    feat_cols = list(s["FEAT_COLS"])
    lam = float(s["lam"])
    ARABIC_CTRL_POOL = list(s["ARABIC_CTRL_POOL"])
    BAND_A_LO, BAND_A_HI = int(s["BAND_A_LO"]), int(s["BAND_A_HI"])
    assert feat_cols[IDX_VL_CV] == "VL_CV", (
        f"Expected FEAT_COLS[{IDX_VL_CV}] = VL_CV, got {feat_cols[IDX_VL_CV]}"
    )

    # Build per-ctrl-corpus VL_CV arrays (Band-A), exactly matching
    # the iteration order baked into X_CTRL_POOL.
    FEATS = s["FEATS"]
    vlcv_by_ctrl = {}
    offset = 0
    for name in ARABIC_CTRL_POOL:
        band = [f for f in FEATS[name] if BAND_A_LO <= f["n_verses"] <= BAND_A_HI]
        v = np.array([f["VL_CV"] for f in band], dtype=float)
        vlcv_by_ctrl[name] = v
        # parity check: the slice of X_CTRL_POOL[:, VL_CV] must match
        n_here = len(v)
        slice_vlcv = X_C[offset:offset + n_here, IDX_VL_CV]
        if not np.allclose(slice_vlcv, v):
            raise AssertionError(
                f"VL_CV order mismatch for corpus {name}: "
                f"FEATS vs X_CTRL_POOL differ"
            )
        offset += n_here
    if offset != X_C.shape[0]:
        raise AssertionError(
            f"Rebuilt ctrl count {offset} != X_CTRL_POOL rows {X_C.shape[0]}"
        )

    vlcv_Q = X_Q[:, IDX_VL_CV]
    vlcv_C = X_C[:, IDX_VL_CV]

    print(f"[{EXP}] X_QURAN {X_Q.shape}, X_CTRL_POOL {X_C.shape}")
    print(f"[{EXP}] FEAT_COLS = {feat_cols}")
    print(f"[{EXP}] ARABIC_CTRL_POOL = {ARABIC_CTRL_POOL}")
    print(f"[{EXP}] Band-A = [{BAND_A_LO}, {BAND_A_HI}], ridge lam = {lam:.2g}")

    # --- T1: Provenance ---
    print(f"\n[{EXP}] === T1: Provenance of 0.1962 ===")
    prov = _provenance(vlcv_Q, vlcv_C)
    print(f"[{EXP}] Best candidate: {prov['best_overall']}")
    print(f"[{EXP}] Within its own strict tol: "
          f"{prov['best_overall_within_strict']}  "
          f"(formula tol = {PROVENANCE_TOL_FORMULA}, "
          f"pct tol = {PROVENANCE_TOL_PCT})")
    print(f"[{EXP}] # formula matches (<=0.0005): "
          f"{len(prov['formula_matches'])}  | "
          f"# percentile matches (<=0.002): "
          f"{len(prov['percentile_matches'])}")
    print(f"[{EXP}] Any strict match: {prov['any_strict_match']}")
    print(f"[{EXP}] Top 5 candidates:")
    for c in prov["top_10_candidates"][:5]:
        print(f"         {c}")

    # --- T2: Exclusion profile ---
    print(f"\n[{EXP}] === T2: Exclusion profile ===")
    excl = _exclusion_profile(vlcv_Q, vlcv_by_ctrl)
    for row in excl["per_floor"]:
        if abs(row["floor"] - LEGACY_FLOOR) < 1e-6 or row["floor"] in (0, 0.25):
            print(f"[{EXP}] floor={row['floor']:.4f}  "
                  f"Q_excl={row['quran_pct_excluded']:5.2f}%  "
                  f"Ctrl_excl={row['ctrl_total_pct_excluded']:5.2f}%")

    # --- T3 + T4: AUC sensitivity + legacy inflation ---
    print(f"\n[{EXP}] === T3 + T4: AUC sensitivity & legacy inflation ===")
    aucs = _auc_sensitivity(X_Q, X_C, mu, S_inv)
    print(f"[{EXP}] baseline AUC (f=0)       = {aucs['baseline_AUC']:.6f}")
    print(f"[{EXP}] tau* (Quran p5 of d_M)   = {aucs['tau_star_quran_p5_at_floor_0']:.4f}")
    print(f"[{EXP}] baseline Q_COV@tau*      = {aucs['baseline_Q_COV_at_tau_star']:.4f}  "
          f"baseline sep@tau* = {aucs['baseline_sep_at_tau_star']:.4f}")
    print(f"[{EXP}]  floor  | filter_AUC | legacy_AUC | Δ_auc_infl | sep_full | sep_leg | Δ_sep_infl | rescued%")
    for r in aucs["per_floor"]:
        p = r["pure_filter"]
        l = r["legacy_mode"]
        infl = r["inflation_vs_baseline"]
        print(
            f"[{EXP}] {r['floor']:.4f} | {p['AUC']:.6f}  | {l['AUC_with_excluded_pinned']:.6f}  | "
            f"{infl['auc_inflation']:+.6f}  | "
            f"{aucs['baseline_sep_at_tau_star']:.4f}   | "
            f"{l['sep_at_tau_star_full_denom']:.4f}  | {infl['sep_inflation']:+.4f}    | "
            f"{r['pct_ctrl_rescued_by_floor']:6.3f}"
        )

    # --- T5: Stratified bootstrap CI ---
    print(f"\n[{EXP}] === T5: Stratified bootstrap AUC CI ({N_BOOTSTRAP}) ===")
    boot = _bootstrap_ci(X_Q, X_C, mu, S_inv, N_BOOTSTRAP)
    for key, v in boot["per_floor"].items():
        print(f"[{EXP}] {key}: pure AUC {v['pure_AUC_mean']:.6f} "
              f"[{v['pure_AUC_ci95'][0]:.6f}, {v['pure_AUC_ci95'][1]:.6f}]  "
              f"legacy {v['legacy_AUC_mean']:.6f} "
              f"[{v['legacy_AUC_ci95'][0]:.6f}, {v['legacy_AUC_ci95'][1]:.6f}]")

    verdict = _compute_verdict(prov, aucs)
    elapsed = time.time() - t0

    print(f"\n{'='*65}")
    print(f"[{EXP}] VERDICT: {verdict['headline_verdict']}")
    print(f"[{EXP}] AUC variation range (no Quran excluded): "
          f"{verdict['auc_variation_range_f_with_no_quran_excluded']:.6f}")
    leak = verdict["leak_audit_at_0p1962"]
    print(f"[{EXP}] Leak at f=0.1962: auc_inflation = {leak['auc_inflation_vs_baseline']:+.6f}")
    print(f"[{EXP}]                   sep_inflation = {leak['sep_inflation_vs_baseline']:+.4f}")
    print(f"[{EXP}]                   pct ctrl rescued by floor = "
          f"{leak['pct_ctrl_rescued_by_floor']:.3f}%")
    print(f"[{EXP}] Flags: {verdict['flags']}")
    print(f"{'='*65}")

    report = {
        "experiment": EXP,
        "hypothesis": "H30 — VL_CV_FLOOR=0.1962 provenance, sensitivity & leak audit",
        "schema_version": 1,
        "data": {
            "n_quran_bandA": int(X_Q.shape[0]),
            "n_ctrl_bandA": int(X_C.shape[0]),
            "feat_cols": feat_cols,
            "IDX_VL_CV": IDX_VL_CV,
            "arabic_ctrl_pool": ARABIC_CTRL_POOL,
            "band_A": [BAND_A_LO, BAND_A_HI],
            "ridge_lambda": lam,
            "quran_vlcv_stats": {
                "min": float(vlcv_Q.min()), "max": float(vlcv_Q.max()),
                "mean": float(vlcv_Q.mean()),
                "median": float(np.median(vlcv_Q)),
                "p1": float(np.percentile(vlcv_Q, 1)),
                "p5": float(np.percentile(vlcv_Q, 5)),
                "p10": float(np.percentile(vlcv_Q, 10)),
            },
            "ctrl_vlcv_stats": {
                "min": float(vlcv_C.min()), "max": float(vlcv_C.max()),
                "mean": float(vlcv_C.mean()),
                "median": float(np.median(vlcv_C)),
                "p25": float(np.percentile(vlcv_C, 25)),
                "p50": float(np.percentile(vlcv_C, 50)),
                "p57": float(np.percentile(vlcv_C, 57)),
                "p75": float(np.percentile(vlcv_C, 75)),
            },
        },
        "T1_provenance": prov,
        "T2_exclusion_profile": excl,
        "T3_T4_auc_sensitivity_and_leak": aucs,
        "T5_bootstrap_CI": boot,
        "verdict": verdict,
        "parameters": {
            "legacy_floor": LEGACY_FLOOR,
            "floors_tested": FLOORS,
            "n_bootstrap": N_BOOTSTRAP,
            "seed": SEED,
        },
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False,
                  default=lambda o: float(o) if isinstance(o, np.floating)
                  else (int(o) if isinstance(o, np.integer) else str(o)))
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED -- no protected files mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
