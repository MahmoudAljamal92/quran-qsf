"""
expA6_structural_coherence_score/run.py
========================================
Opportunity A6 (OPPORTUNITY_TABLE_DETAIL.md):
  Implement the external reviewer's proposed Structural Coherence Score
        SCS(T) = I(position ; content) / H(content)
  as a single scalar per (corpus, feature) pair, and rank corpora by
  their average SCS.

Method:
  For each corpus and each of the 5 features f ∈ {EL, VL_CV, CN, H_cond, T}:
    1. Take the Band-A units in their CANONICAL order (= the order they
       appear in CORPORA[corpus]; for Quran this is mushaf order).
    2. Discretise the feature value f into Q quantile bins (default Q=3).
    3. Discretise the unit-position index 0..(n-1) into P bins (default P=3).
    4. Build the P×Q contingency table.
    5. I(P;Q) and H(Q) computed via empirical joint and marginal probs.
    6. SCS_f = I(P;Q) / H(Q).
  Per-corpus SCS = mean(SCS_f over the 5 features).

Outputs:
  - results/experiments/expA6_structural_coherence_score/expA6_structural_coherence_score.json

Pre-registration:
  - PASS if Quran's mean SCS is the strict maximum across the 7 corpora.
  - We also report the per-feature ranking and the maxbinning-Q sweep
    (Q ∈ {2, 3, 4, 5}) to expose any binning-fragility.

Reads:
  - results/checkpoints/phase_06_phi_m.pkl  (CORPORA, FEATS, Band-A bounds)
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
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

EXP = "expA6_structural_coherence_score"
FEAT_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]
QS = [2, 3, 4, 5]
PS = [2, 3, 4, 5]


def _quantile_bin(x: np.ndarray, k: int) -> np.ndarray:
    """Map x into k equal-frequency bins {0..k-1}. Ties broken by quantile
    (float positions). If x is too constant for k bins, falls back to
    fewer non-empty bins.
    """
    if len(x) < k:
        # Not enough samples; bin into len(x) tiers
        qs = np.argsort(np.argsort(x)).astype(int)
        return qs
    edges = np.quantile(x, np.linspace(0, 1, k + 1)[1:-1])
    return np.searchsorted(edges, x, side="right").astype(int)


def _mutual_information_bits(p_bins: np.ndarray, q_bins: np.ndarray) -> tuple[float, float, float, float]:
    """Return (I_naive, I_MillerMadow_corrected, H(P), H(Q)) all in bits.

    Miller-Madow correction (Miller 1955; Paninski 2003 form):
        MI_MM = MI_naive - (a + b - c - 1) / (2 N ln 2)
    where a = # non-zero joint cells, b = # non-zero P×Q product
    cells (= n_p_active * n_q_active under iid product), c = ... — for
    practical use we adopt the commonly cited Miller form:
        bias ≈ (n_p_active + n_q_active - n_joint_active - 1) / (2 N ln 2)
    The standard textbook bias of plug-in MI under independence is
    (n_p_active - 1)(n_q_active - 1) / (2 N), which exceeds the bias
    of the marginal entropies. We subtract it as a conservative
    finite-sample correction.
    """
    if len(p_bins) != len(q_bins) or len(p_bins) < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    n = len(p_bins)
    joint = Counter(zip(p_bins.tolist(), q_bins.tolist()))
    p_only = Counter(p_bins.tolist())
    q_only = Counter(q_bins.tolist())
    H_P = -sum((c / n) * math.log2(c / n) for c in p_only.values() if c > 0)
    H_Q = -sum((c / n) * math.log2(c / n) for c in q_only.values() if c > 0)
    I_naive = 0.0
    for (a, b), n_ab in joint.items():
        p_ab = n_ab / n
        p_a = p_only[a] / n
        p_b = q_only[b] / n
        if p_ab > 0 and p_a > 0 and p_b > 0:
            I_naive += p_ab * math.log2(p_ab / (p_a * p_b))
    # Miller-Madow finite-sample bias correction for plug-in MI under
    # the null of independence:
    #   bias = (a-1)(b-1) / (2 N ln 2)   bits
    a_active = sum(1 for c in p_only.values() if c > 0)
    b_active = sum(1 for c in q_only.values() if c > 0)
    bias_bits = ((a_active - 1) * (b_active - 1)) / (2 * n * math.log(2)) if n > 0 else 0.0
    I_corrected = I_naive - bias_bits
    return I_naive, I_corrected, H_P, H_Q


def _scs_per_feature(values: np.ndarray, P: int, Q: int) -> dict:
    """Compute SCS = I(position_bin ; feature_bin) / H(feature_bin)
    on a 1-D array of feature values in canonical position order. Reports
    both naive and Miller-Madow-corrected SCS."""
    n = len(values)
    if n < max(P, Q):
        return {"n": int(n), "I_PQ_bits_naive": float("nan"),
                "I_PQ_bits_MM": float("nan"),
                "H_Q_bits": float("nan"),
                "SCS_naive": float("nan"),
                "SCS_MM": float("nan")}
    pos = np.arange(n)
    p_bins = _quantile_bin(pos.astype(float), P)
    q_bins = _quantile_bin(values, Q)
    I_naive, I_mm, _H_P, H_Q = _mutual_information_bits(p_bins, q_bins)
    scs_naive = I_naive / H_Q if (H_Q and H_Q > 0) else float("nan")
    scs_mm    = I_mm    / H_Q if (H_Q and H_Q > 0) else float("nan")
    # Clamp negative MM-corrected SCS to 0 (MI is theoretically >= 0;
    # negative values are pure noise after subtracting bias).
    if math.isfinite(scs_mm):
        scs_mm = max(0.0, scs_mm)
    return {
        "n": int(n),
        "I_PQ_bits_naive": I_naive,
        "I_PQ_bits_MM":    I_mm,
        "H_Q_bits":        H_Q,
        "SCS_naive":       float(scs_naive),
        "SCS_MM":          float(scs_mm),
    }


def _band_a_feature_matrix(corpus_name: str, state: dict) -> np.ndarray | None:
    """Reproduce Band-A filtered feature extraction for one corpus.
    Returns (n_units, 5) np.ndarray ordered by the underlying CORPORA list,
    or None if the corpus is empty."""
    feats = state["FEATS"].get(corpus_name, [])
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))
    rows = [
        [r[c] for c in FEAT_NAMES]
        for r in feats
        if band_lo <= r["n_verses"] <= band_hi
    ]
    if not rows:
        return None
    return np.asarray(rows, dtype=float)


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])
    if feat_cols != FEAT_NAMES:
        raise RuntimeError(f"FEAT_COLS drift: expected {FEAT_NAMES}, got {feat_cols}")

    # All corpora that have Band-A units in the audited pipeline
    corpora_to_test = [
        "quran",
        "poetry_jahili", "poetry_islami", "poetry_abbasi",
        "ksucca", "arabic_bible", "hindawi",
    ]

    print(f"[{EXP}] testing corpora: {corpora_to_test}")
    print(f"[{EXP}] grid P × Q ∈ {PS} × {QS}")

    # ---- Per-corpus, per-(P, Q), per-feature SCS ----
    per_corpus = {}
    for c in corpora_to_test:
        X = _band_a_feature_matrix(c, state)
        if X is None or X.shape[0] < 5:
            per_corpus[c] = {"error": "too few Band-A units", "n": 0}
            continue
        n = X.shape[0]
        rec = {"n_band_a": int(n), "scs_grid": {}, "feature_means": {}}
        # Mean SCS per feature, default P=Q=3
        feat_scs_default = {}
        for j, f in enumerate(FEAT_NAMES):
            feat_scs_default[f] = _scs_per_feature(X[:, j], P=3, Q=3)
        rec["per_feature_default_P3_Q3"] = feat_scs_default
        rec["mean_SCS_naive_default_P3_Q3"] = float(np.nanmean([
            feat_scs_default[f]["SCS_naive"] for f in FEAT_NAMES
        ]))
        rec["mean_SCS_MM_default_P3_Q3"] = float(np.nanmean([
            feat_scs_default[f]["SCS_MM"] for f in FEAT_NAMES
        ]))
        # Sweep over P, Q for stability check
        for P in PS:
            for Q in QS:
                key = f"P{P}_Q{Q}"
                feat_scs = {
                    f: _scs_per_feature(X[:, j], P=P, Q=Q)
                    for j, f in enumerate(FEAT_NAMES)
                }
                mean_scs_naive = float(np.nanmean([feat_scs[f]["SCS_naive"] for f in FEAT_NAMES]))
                mean_scs_mm    = float(np.nanmean([feat_scs[f]["SCS_MM"]    for f in FEAT_NAMES]))
                rec["scs_grid"][key] = {
                    "per_feature_SCS_naive": {f: feat_scs[f]["SCS_naive"] for f in FEAT_NAMES},
                    "per_feature_SCS_MM":    {f: feat_scs[f]["SCS_MM"]    for f in FEAT_NAMES},
                    "mean_SCS_naive": mean_scs_naive,
                    "mean_SCS_MM":    mean_scs_mm,
                }
        per_corpus[c] = rec

    # ---- Ranking by mean SCS at default P=3, Q=3 (both naive and MM) ----
    def _ranking(score_key: str) -> list[tuple[str, float, int]]:
        return sorted(
            [(c, r.get(score_key, float("nan")), r.get("n_band_a", 0))
             for c, r in per_corpus.items() if "error" not in r],
            key=lambda x: -x[1] if not math.isnan(x[1]) else float("inf"),
        )
    ranked_naive = _ranking("mean_SCS_naive_default_P3_Q3")
    ranked_mm    = _ranking("mean_SCS_MM_default_P3_Q3")

    def _quran_rank(rank_list: list) -> int | None:
        return next(
            (i + 1 for i, (c, _s, _n) in enumerate(rank_list) if c == "quran"),
            None,
        )
    def _quran_strict_max(rank_list: list) -> bool:
        return bool(
            rank_list and rank_list[0][0] == "quran" and len(rank_list) > 1
            and rank_list[0][1] > rank_list[1][1]
        )

    quran_rank_naive = _quran_rank(ranked_naive)
    quran_rank_mm    = _quran_rank(ranked_mm)
    quran_strict_max_naive = _quran_strict_max(ranked_naive)
    quran_strict_max_mm    = _quran_strict_max(ranked_mm)

    # ---- Robustness: how often is Quran top across the 16 (P,Q) cells? ----
    def _cell_winners(score_key: str) -> list[dict]:
        out = []
        for P in PS:
            for Q in QS:
                key = f"P{P}_Q{Q}"
                cell_scores = []
                for c in corpora_to_test:
                    r = per_corpus.get(c, {})
                    if "error" in r: continue
                    v = r.get("scs_grid", {}).get(key, {}).get(score_key, float("nan"))
                    cell_scores.append((c, v))
                cell_scores.sort(key=lambda x: -x[1] if not math.isnan(x[1]) else float("inf"))
                out.append({
                    "P": P, "Q": Q,
                    "winner": cell_scores[0][0] if cell_scores else None,
                    "winner_SCS": cell_scores[0][1] if cell_scores else float("nan"),
                    "quran_SCS": next(
                        (v for c, v in cell_scores if c == "quran"), float("nan")
                    ),
                    "quran_rank": next(
                        (i + 1 for i, (c, _v) in enumerate(cell_scores) if c == "quran"),
                        None,
                    ),
                })
        return out
    cell_winners_naive = _cell_winners("mean_SCS_naive")
    cell_winners_mm    = _cell_winners("mean_SCS_MM")
    n_cells_total = len(cell_winners_naive)
    n_cells_quran_top_naive = sum(1 for w in cell_winners_naive if w["winner"] == "quran")
    n_cells_quran_top_mm    = sum(1 for w in cell_winners_mm    if w["winner"] == "quran")

    # Verdict prefers MM-corrected as the primary; reports both.
    if quran_strict_max_mm and n_cells_quran_top_mm == n_cells_total:
        verdict = "QURAN_SCS_MAXIMUM_ROBUST_MM"
    elif quran_rank_mm == 1:
        verdict = "QURAN_TOP_AT_DEFAULT_MM_PARTIAL_GRID"
    elif quran_strict_max_naive and n_cells_quran_top_naive == n_cells_total:
        verdict = "QURAN_SCS_MAXIMUM_ROBUST_NAIVE_ONLY"
    elif quran_rank_naive == 1 and quran_rank_mm and quran_rank_mm <= 2:
        verdict = "QURAN_TOP_NAIVE_NEAR_TOP_MM"
    elif quran_rank_mm and quran_rank_mm <= 2:
        verdict = "QURAN_TOP2_MM"
    else:
        verdict = "QURAN_NOT_TOP"

    report = {
        "experiment": EXP,
        "task_id": "A6",
        "title": (
            "Structural Coherence Score (SCS) = I(position; content) / "
            "H(content), per (corpus, feature). Reviewer's proposal "
            "(QSF_CRITICAL_REVIEW.md:110-134, 237-253) implemented over "
            "the 5 Phi_M features and the 7 audited Band-A corpora."
        ),
        "method": (
            "For each (corpus, feature): bin position into P equal-freq "
            "tiers and feature into Q equal-freq tiers; compute I and H "
            "via empirical joint/marginal counts; SCS = I/H. Default "
            "P=Q=3 (thirds); robustness sweep over (P, Q) ∈ {2,3,4,5}^2 "
            "(16 cells)."
        ),
        "corpora_tested": corpora_to_test,
        "per_corpus": per_corpus,
        "ranking_default_P3_Q3_naive": [
            {"corpus": c, "mean_SCS": s, "n_band_a": n} for c, s, n in ranked_naive
        ],
        "ranking_default_P3_Q3_MM": [
            {"corpus": c, "mean_SCS": s, "n_band_a": n} for c, s, n in ranked_mm
        ],
        "quran_rank_default_naive":     quran_rank_naive,
        "quran_rank_default_MM":        quran_rank_mm,
        "quran_strict_max_default_naive": quran_strict_max_naive,
        "quran_strict_max_default_MM":    quran_strict_max_mm,
        "robustness_grid_naive": cell_winners_naive,
        "robustness_grid_MM":    cell_winners_mm,
        "n_grid_cells_total":    n_cells_total,
        "n_grid_cells_quran_top_naive": n_cells_quran_top_naive,
        "n_grid_cells_quran_top_MM":    n_cells_quran_top_mm,
        "verdict": verdict,
        "interpretation": [
            "Higher SCS = the feature value is more predictable from the "
            "unit's position in the canonical order. For the Quran, this "
            "captures any Meccan->Medinan / length / topical gradient that "
            "the canonical mushaf ordering encodes.",
            "If `verdict = QURAN_SCS_MAXIMUM_ROBUST`, the Quran has the "
            "largest position-content mutual information / H(content) "
            "ratio across all 16 (P,Q) cells of the robustness grid AND "
            "strictly above the runner-up at the default (P=3, Q=3). This "
            "is the strongest form of the universal-one-number claim.",
            "If Quran is top only at default P=Q=3 but not on the full "
            "grid, report SCS as binning-fragile — still a published "
            "scalar but with caveats.",
        ],
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Stdout
    print()
    print(f"[{EXP}] -- ranking at default P=3, Q=3 (NAIVE plug-in MI) --")
    for i, (c, scs, n) in enumerate(ranked_naive, start=1):
        marker = " <- Quran" if c == "quran" else ""
        print(f"[{EXP}]   {i:2d}. {c:<20s}  mean_SCS_naive = {scs:.4f}   "
              f"n_band_a = {n}{marker}")
    print()
    print(f"[{EXP}] -- ranking at default P=3, Q=3 (MM-corrected MI) --")
    for i, (c, scs, n) in enumerate(ranked_mm, start=1):
        marker = " <- Quran" if c == "quran" else ""
        print(f"[{EXP}]   {i:2d}. {c:<20s}  mean_SCS_MM    = {scs:.4f}   "
              f"n_band_a = {n}{marker}")
    print()
    print(f"[{EXP}] Quran rank (naive)            : {quran_rank_naive}")
    print(f"[{EXP}] Quran rank (MM-corrected)     : {quran_rank_mm}")
    print(f"[{EXP}] Quran strict max @ naive      : {quran_strict_max_naive}")
    print(f"[{EXP}] Quran strict max @ MM         : {quran_strict_max_mm}")
    print(f"[{EXP}] Quran top in {n_cells_quran_top_naive}/{n_cells_total} cells (naive)")
    print(f"[{EXP}] Quran top in {n_cells_quran_top_mm}/{n_cells_total} cells (MM-corrected)")
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
