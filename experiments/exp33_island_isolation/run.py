"""
exp33_island_isolation/run.py
==============================
Topological extension of the corpus-level Phi_M claim (PAPER.md
Section 4.1). The locked headline (Hotelling T^2 = 3557, AUC = 0.998)
is an *aggregated* separation statistic. This experiment asks a
*density-based* / *topological* question:

  In the 5-D stylometric space under the locked Mahalanobis metric,
  do the Quran points form a discrete ISLAND, separated by a
  positive gap from every control point?

Let
    NND_within_Q[i]  = min_{j != i}  ||x_Q[i] - x_Q[j]||_M   for Q_i in Q
    NND_cross_QC[i]  = min_{c in C}  ||x_Q[i] - x_C[c]||_M   for Q_i in Q
    NND_within_C[j]  = min_{k != j}  ||x_C[j] - x_C[k]||_M   for C_j in C

Define the island gap as
    gap = min_i NND_cross_QC[i] - max_i NND_within_Q[i]

A positive gap means that EVERY Quran point is closer to another
Quran point than to ANY control point (single-linkage-island test).

We also report:
  * ratio  rho = mean(NND_within_Q) / mean(NND_cross_QC)
           (< 1 => Quran clusters tighter to itself than to ctrl)
  * permutation p-value on the gap under 10 000 label shuffles.
  * Silhouette score of the binary Q/C labelling in the Mahalanobis
    metric (standard ML clustering quality).
  * nearest-Quran / nearest-ctrl identities for each Quran point
    (diagnostic for which ctrl corpora are closest).

Reads (verified): phase_06_phi_m.pkl via experiments._lib.load_phase.
Writes only under results/experiments/exp33_island_isolation/.
No locked artefact is touched.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)

from src import features as ft  # noqa: E402

EXP = "exp33_island_isolation"
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
N_PERMUTATIONS = 10_000

ARABIC_CTRL_NAMES = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _band_a_units(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _features_stack(units) -> tuple[np.ndarray, list[str], list[str]]:
    out, labels, source = [], [], []
    for u in units:
        try:
            out.append(ft.features_5d(u.verses))
            labels.append(str(getattr(u, "label", "?")))
            source.append(str(getattr(u, "source", "?")))
        except Exception:
            continue
    return np.asarray(out, dtype=float), labels, source


def _pairwise_mahalanobis(X: np.ndarray, Sinv: np.ndarray) -> np.ndarray:
    diff = X[:, None, :] - X[None, :, :]
    d2 = np.einsum("ijk,kl,ijl->ij", diff, Sinv, diff)
    return np.sqrt(np.clip(d2, 0.0, None))


def _nn_distances(D_within: np.ndarray, D_cross: np.ndarray | None) -> tuple:
    """For a given block, return (within_NND, cross_NND). D_within
    is the square matrix with np.inf on diagonal. D_cross is
    rectangular (rows = self block, cols = other block); if None,
    cross_NND is None."""
    np.fill_diagonal(D_within, np.inf)
    within = D_within.min(axis=1)
    cross = D_cross.min(axis=1) if D_cross is not None else None
    return within, cross


def _silhouette(D_full: np.ndarray, labels: np.ndarray) -> float:
    """Binary-label silhouette in the supplied distance matrix.

    s_i = (b_i - a_i) / max(a_i, b_i), where
      a_i = mean dist to same-label points (excluding self)
      b_i = mean dist to other-label points
    Returns mean over all i.
    """
    n = len(labels)
    s = np.zeros(n, dtype=float)
    for i in range(n):
        same = np.where(labels == labels[i])[0]
        other = np.where(labels != labels[i])[0]
        same = same[same != i]
        if len(same) == 0 or len(other) == 0:
            s[i] = 0.0
            continue
        a = D_full[i, same].mean()
        b = D_full[i, other].mean()
        denom = max(a, b)
        s[i] = (b - a) / denom if denom > 0 else 0.0
    return float(s.mean())


def _summarise(values) -> dict:
    if len(values) == 0:
        return {"n": 0}
    a = np.asarray(values, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "sd": float(a.std(ddof=1)) if a.size > 1 else 0.0,
        "min": float(a.min()), "max": float(a.max()),
        "q05": float(np.quantile(a, 0.05)),
        "q25": float(np.quantile(a, 0.25)),
        "q75": float(np.quantile(a, 0.75)),
        "q95": float(np.quantile(a, 0.95)),
    }


def main() -> int:
    t0 = time.time()
    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading phase_06_phi_m state (read-only)...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    S_inv = np.asarray(state["S_inv"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    X_Q, lab_Q, src_Q = _features_stack(_band_a_units(CORPORA.get("quran", [])))

    X_C_parts: list[np.ndarray] = []
    lab_C: list[str] = []
    src_C: list[str] = []
    for name in ARABIC_CTRL_NAMES:
        units = _band_a_units(CORPORA.get(name, []))
        X_part, lab_part, _ = _features_stack(units)
        if X_part.size == 0:
            continue
        X_C_parts.append(X_part)
        lab_C.extend(lab_part)
        src_C.extend([name] * len(lab_part))
    X_C = np.vstack(X_C_parts)
    nQ, nC = X_Q.shape[0], X_C.shape[0]
    print(f"[{EXP}] nQ = {nQ}  nC = {nC}  feat dim = {X_Q.shape[1]}")

    # ---- Pairwise Mahalanobis distance matrices ---------------------------
    print(f"[{EXP}] computing pairwise Mahalanobis distance matrices...")
    X_full = np.vstack([X_Q, X_C])
    D_full = _pairwise_mahalanobis(X_full, S_inv)
    D_QQ = D_full[:nQ, :nQ].copy()
    D_CC = D_full[nQ:, nQ:].copy()
    D_QC = D_full[:nQ, nQ:].copy()
    D_CQ = D_full[nQ:, :nQ].copy()

    # ---- NND distances ----------------------------------------------------
    nnd_within_Q, nnd_cross_Q_to_C = _nn_distances(D_QQ, D_QC)
    nnd_within_C, nnd_cross_C_to_Q = _nn_distances(D_CC, D_CQ)

    # Island gap (single-linkage sense)
    gap = float(nnd_cross_Q_to_C.min() - nnd_within_Q.max())
    is_island = gap > 0

    # Mean NND ratio
    nnr_Q = float(nnd_within_Q.mean() / nnd_cross_Q_to_C.mean())
    nnr_C = float(nnd_within_C.mean() / nnd_cross_C_to_Q.mean())

    # ---- Silhouette -------------------------------------------------------
    labels = np.array([1] * nQ + [0] * nC)
    sil = _silhouette(D_full, labels)

    # ---- Permutation null on the gap --------------------------------------
    print(f"[{EXP}] permutation null on island gap (B = {N_PERMUTATIONS})...")
    rng = np.random.default_rng(SEED)
    n = nQ + nC
    null_gaps: list[float] = []
    null_max_within_Q: list[float] = []
    null_min_cross_Q_to_C: list[float] = []
    for b in range(N_PERMUTATIONS):
        perm = rng.permutation(n)
        q_idx = perm[:nQ]
        c_idx = perm[nQ:]
        D_QQ_p = D_full[np.ix_(q_idx, q_idx)].copy()
        D_QC_p = D_full[np.ix_(q_idx, c_idx)].copy()
        within_p, cross_p = _nn_distances(D_QQ_p, D_QC_p)
        null_gaps.append(float(cross_p.min() - within_p.max()))
        null_max_within_Q.append(float(within_p.max()))
        null_min_cross_Q_to_C.append(float(cross_p.min()))
    null_gaps_arr = np.asarray(null_gaps, dtype=float)
    p_gap = float((null_gaps_arr >= gap).sum() / N_PERMUTATIONS)

    # ---- Diagnostic: nearest-ctrl-corpus for each Quran surah ------------
    nearest_c_idx = D_QC.argmin(axis=1)
    ctrl_corpus_counts: dict[str, int] = {}
    for j in nearest_c_idx:
        ctrl_corpus_counts[src_C[j]] = ctrl_corpus_counts.get(src_C[j], 0) + 1

    # Top hostile Quran surahs (smallest margin to nearest ctrl)
    margin = nnd_cross_Q_to_C - nnd_within_Q
    ord_m = np.argsort(margin)  # smallest margin first
    hostile_top10 = [
        {
            "label": lab_Q[int(i)],
            "nnd_within_Q": round(float(nnd_within_Q[int(i)]), 4),
            "nnd_cross_Q_to_C": round(float(nnd_cross_Q_to_C[int(i)]), 4),
            "margin": round(float(margin[int(i)]), 4),
            "nearest_ctrl_label": lab_C[int(nearest_c_idx[int(i)])],
            "nearest_ctrl_corpus": src_C[int(nearest_c_idx[int(i)])],
        }
        for i in ord_m[:10]
    ]

    # ---- Assemble + save --------------------------------------------------
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "In the 5-D stylometric space under the locked Mahalanobis "
            "metric, do the Quran points form a topologically discrete "
            "ISLAND separated by a positive gap from all control "
            "points?"
        ),
        "config": {
            "seed": SEED,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "n_permutations": N_PERMUTATIONS,
            "arabic_ctrl_corpora": ARABIC_CTRL_NAMES,
        },
        "n_quran_band_a": nQ,
        "n_ctrl_band_a": nC,
        "feat_cols": feat_cols,
        "nnd_within_Q_summary": _summarise(nnd_within_Q),
        "nnd_cross_Q_to_C_summary": _summarise(nnd_cross_Q_to_C),
        "nnd_within_C_summary": _summarise(nnd_within_C),
        "max_within_Q": float(nnd_within_Q.max()),
        "min_cross_Q_to_C": float(nnd_cross_Q_to_C.min()),
        "island_gap_M_units": gap,
        "is_island_single_linkage": bool(is_island),
        "nnr_Q_ratio_withinQ_over_crossQC": nnr_Q,
        "nnr_C_ratio_withinC_over_crossCQ": nnr_C,
        "silhouette_binary_Q_vs_C_mahalanobis": sil,
        "permutation_test_gap": {
            "observed_gap": gap,
            "null_summary": _summarise(null_gaps),
            "p_value_one_sided_greater": p_gap,
        },
        "nearest_ctrl_corpus_histogram": ctrl_corpus_counts,
        "hostile_top10_smallest_margin": hostile_top10,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    outfile = out_dir / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console summary --------------------------------------------------
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] ======================= island analysis =======================")
    print(f"   nQ = {nQ}   nC = {nC}")
    print(f"   max(NND_within_Q)       = {nnd_within_Q.max():.4f}   (tightest within-Q)")
    print(f"   min(NND_cross_Q_to_C)   = {nnd_cross_Q_to_C.min():.4f}   "
          f"(closest Q->C)")
    print(f"   island gap              = {gap:.4f}   "
          f"({'ISLAND' if is_island else 'continuum'})")
    print(f"   NNR (within_Q / cross_QC) = {nnr_Q:.4f}   "
          f"(< 1 means Q clusters tighter to self)")
    print(f"   Silhouette (Q vs C, Mahal.) = {sil:+.4f}")
    print(f"   permutation p(gap >= observed) = {p_gap:.6f}   "
          f"(B = {N_PERMUTATIONS})")
    print(f"[{EXP}] Top 5 hostile Quran surahs (smallest margin):")
    for h in hostile_top10[:5]:
        print(f"   {h['label']:10s}  margin = {h['margin']:+.4f}   "
              f"nearest ctrl = {h['nearest_ctrl_corpus']:15s}  "
              f"({h['nearest_ctrl_label']})")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
