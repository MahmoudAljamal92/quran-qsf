"""
expA7_dna_reconstruction/run.py
================================
Opportunity A7 (OPPORTUNITY_TABLE_DETAIL.md):
  The "DNA of the Quran" claim implies that the canonical mushaf order is
  not arbitrary — that perturbations to it are DETECTABLE and (perhaps)
  CORRECTABLE from local structure alone, the way Reed-Solomon codes
  detect/correct bit errors from local parity.

  This experiment tests the IDENTIFICATION half of the claim at the
  surah-level: given the 114 Mushaf-ordered surahs with a random subset
  X% swapped to other positions, can a local-J1-anomaly score identify
  which surahs are out of place at precision/recall above the random
  baseline?

Method
------
For each perturbation rate p_corrupt ∈ {0.05, 0.10, 0.20, 0.30, 0.50}:
  For each trial in 1..N_TRIALS (default 100):
    1. Sample a random subset S of |p_corrupt × 114| surah indices.
    2. Permute S's positions among themselves (random within-S shuffle).
       Result: a perturbed mushaf sequence where exactly |S| surahs are
       at the wrong index (each is at another surah's correct slot).
    3. For each position i in the perturbed sequence, compute
       anomaly_i = ||X'[i] - X'[i-1]||² + ||X'[i+1] - X'[i]||²
       in pre-whitened coordinates (so distances are Mahalanobis).
       Boundary positions only have one transition; we use the single
       transition for i=0 and i=N-1.
    4. Rank surah indices by anomaly_i descending; predict the top |S|
       as "misplaced".
    5. Compute precision = |pred ∩ S| / |pred| ; recall = |pred ∩ S| / |S|.
       (precision == recall == F1 here because |pred| == |S|.)
  Aggregate: mean precision, mean F1, sd, distribution.

Random baseline:
  Random selection of |S| surahs gives expected precision = |S|/N where
  N = 114, but here |S|/N == p_corrupt by construction, so the random
  baseline F1 for any p_corrupt is **p_corrupt itself**. PASS if mean
  F1 > 2 × random baseline at every p_corrupt tested.

Pre-registration
----------------
  POSITIVE_RECONSTRUCTION_DETECTABLE if mean F1 > 2 × p_corrupt at every
                                      p_corrupt in {0.05, 0.10, 0.20}.
  PARTIAL_DETECTABLE                  if F1 > 2 × p_corrupt at some but
                                      not all p_corrupt.
  NEGATIVE_DNA_METAPHOR_ONLY         otherwise.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl  (CORPORA.quran for canonical
                                              order; FEATS.quran for the
                                              5-D feature scalars per surah)

Writes:
  - results/experiments/expA7_dna_reconstruction/expA7_dna_reconstruction.json
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

EXP = "expA7_dna_reconstruction"
SEED = 42
N_TRIALS = 100
PERTURB_RATES = [0.05, 0.10, 0.20, 0.30, 0.50]
RIDGE_LAMBDA = 1e-6
FEAT_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]


def _per_surah_features(state: dict) -> np.ndarray:
    """Return a (114, 5) feature matrix in canonical Mushaf order, indexed
    by 0..113 corresponding to surah 1..114."""
    feats = state["FEATS"].get("quran", [])
    by_label: dict[int, list[float]] = {}
    for r in feats:
        label = str(r.get("label", "")).replace("Q:", "").strip()
        try:
            sn = int(label)
        except ValueError:
            continue
        by_label[sn] = [r[c] for c in FEAT_NAMES]
    if set(by_label.keys()) != set(range(1, 115)):
        missing = set(range(1, 115)) - set(by_label.keys())
        raise RuntimeError(
            f"Missing surah indices in FEATS['quran']: {sorted(missing)[:5]}..."
        )
    X = np.array([by_label[s] for s in range(1, 115)], dtype=float)
    if X.shape != (114, 5):
        raise RuntimeError(f"X shape {X.shape} != (114, 5)")
    return X


def _whitening_matrix(X: np.ndarray, ridge: float = RIDGE_LAMBDA) -> np.ndarray:
    """Return A such that A^T A = Sigma_inv, Sigma = Cov(X) + ridge·I.
    Then ||A x_i - A x_j||² == (x_i - x_j)^T Sigma_inv (x_i - x_j)."""
    mu = X.mean(axis=0)
    Sigma = np.cov(X - mu, rowvar=False) + ridge * np.eye(X.shape[1])
    w, V = np.linalg.eigh(Sigma)
    return (V * np.sqrt(1.0 / w)).T


def _local_anomaly_scores(Xp: np.ndarray) -> np.ndarray:
    """For an N×p matrix Xp in pre-whitened coords, return a length-N
    anomaly score per row = sum of squared transitions involving that row.

    For interior positions i: incoming + outgoing transition.
    For boundary positions i=0 and i=N-1: only one transition.
    """
    N = Xp.shape[0]
    diffs = Xp[1:] - Xp[:-1]                       # (N-1, p)
    sq = (diffs * diffs).sum(axis=1)               # (N-1,)  edge i = (i, i+1)
    a = np.zeros(N, dtype=float)
    a[0] = sq[0]
    a[N - 1] = sq[N - 2]
    if N > 2:
        a[1:N - 1] = sq[:-1] + sq[1:]
    return a


def _within_subset_permutation(
    rng: np.random.Generator, S: np.ndarray
) -> np.ndarray:
    """Return a permutation of indices in S, ensuring at least one
    derangement (no fixed points) when |S| ≥ 2 — so every selected surah
    actually moves."""
    if len(S) < 2:
        return S.copy()
    while True:
        perm = rng.permutation(S)
        if not np.any(perm == S):
            return perm


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feat_cols = list(state["FEAT_COLS"])
    if feat_cols != FEAT_NAMES:
        raise RuntimeError(f"FEAT_COLS drift: expected {FEAT_NAMES}, got {feat_cols}")

    X = _per_surah_features(state)
    A = _whitening_matrix(X)
    Xp = X @ A.T
    print(f"[{EXP}] X = {X.shape}   pre-whitened.")

    # Sanity check: J1 of canonical order on Xp
    j1_canonical = float(((Xp[1:] - Xp[:-1]) ** 2).sum())
    print(f"[{EXP}] canonical mushaf J1 (whitened) = {j1_canonical:.6f}")

    rng = np.random.default_rng(SEED)
    results = []
    N = X.shape[0]
    for p_corrupt in PERTURB_RATES:
        n_corrupt = max(2, int(round(p_corrupt * N)))
        precisions = []
        f1s = []
        j1_perturbed = []
        # Random-baseline F1 trace (predict random |S| at every trial)
        f1_baseline = []
        for trial in range(N_TRIALS):
            # 1. Sample subset S
            S = rng.choice(N, size=n_corrupt, replace=False)
            S_set = set(int(s) for s in S)
            # 2. Within-S derangement permutation
            S_perm = _within_subset_permutation(rng, S)
            order = np.arange(N)
            order[S] = S_perm  # surah originally at index S[k] now goes to index... wait
            # Build the perturbed surah-order vector:
            # `perturbed[i]` = the surah that ends up at position i in the perturbed sequence.
            # We swap positions: at each i in S, the "correct" surah is i (canonical order),
            # but after permutation we put surah S_perm[k] at position S[k].
            perturbed = np.arange(N)
            perturbed[S] = S_perm
            # `perturbed` is the new index-of-original-surah at each position.
            # Build the perturbed feature matrix:
            Xp_pert = Xp[perturbed]
            # 3. Anomaly scores
            anom = _local_anomaly_scores(Xp_pert)
            # 4. Predict: top n_corrupt indices by anomaly
            pred_idx = np.argsort(-anom)[:n_corrupt]
            pred_set = set(int(p) for p in pred_idx)
            # Ground truth: positions whose displayed surah is NOT the canonical
            # one. In our perturbation, S[k] holds S_perm[k] != S[k] (derangement),
            # so ground truth set = S itself (positions that are wrong).
            tp = len(pred_set & S_set)
            precision = tp / n_corrupt
            recall = tp / n_corrupt  # |gt| == n_corrupt by construction
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            precisions.append(precision)
            f1s.append(f1)
            # Random-baseline F1
            rand_pred = set(int(x) for x in rng.choice(N, size=n_corrupt, replace=False))
            tp_rand = len(rand_pred & S_set)
            f1_rand = tp_rand / n_corrupt  # == prec == recall here
            f1_baseline.append(f1_rand)
            # J1 of perturbed
            j1_perturbed.append(
                float(((Xp_pert[1:] - Xp_pert[:-1]) ** 2).sum())
            )
        precisions = np.asarray(precisions)
        f1s = np.asarray(f1s)
        f1_baseline = np.asarray(f1_baseline)
        j1_pert = np.asarray(j1_perturbed)
        results.append({
            "p_corrupt": p_corrupt,
            "n_corrupt_per_trial": int(n_corrupt),
            "n_trials": int(N_TRIALS),
            "f1_mean": float(f1s.mean()),
            "f1_sd":   float(f1s.std(ddof=1)),
            "f1_min":  float(f1s.min()),
            "f1_max":  float(f1s.max()),
            "f1_random_baseline_mean":     float(f1_baseline.mean()),
            "f1_random_baseline_expected": float(p_corrupt),
            "f1_lift_vs_random":           float(f1s.mean() / max(f1_baseline.mean(), 1e-9)),
            "f1_lift_vs_expected":         float(f1s.mean() / max(p_corrupt, 1e-9)),
            "perturbed_J1_mean": float(j1_pert.mean()),
            "perturbed_J1_min":  float(j1_pert.min()),
            "perturbed_J1_max":  float(j1_pert.max()),
            "canonical_J1":      j1_canonical,
            "perturbed_J1_above_canonical_frac":
                float((j1_pert > j1_canonical).mean()),
        })
        print(f"[{EXP}]   p={p_corrupt:.2f}  n={n_corrupt}  "
              f"F1_mean={f1s.mean():.4f}  baseline={f1_baseline.mean():.4f}  "
              f"lift={f1s.mean() / max(f1_baseline.mean(), 1e-9):.2f}x")

    # ---- Pre-registered verdict ----
    detect_targets = [r for r in results if r["p_corrupt"] in (0.05, 0.10, 0.20)]
    pass_per_target = [r["f1_mean"] > 2 * r["p_corrupt"] for r in detect_targets]
    if all(pass_per_target):
        verdict = "POSITIVE_RECONSTRUCTION_DETECTABLE"
    elif any(pass_per_target):
        verdict = "PARTIAL_DETECTABLE"
    else:
        verdict = "NEGATIVE_DNA_METAPHOR_ONLY"

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "A7",
        "title": (
            "DNA-of-the-Quran reconstruction test: can the canonical "
            "mushaf order's local 5-D feature smoothness IDENTIFY which "
            "surahs are out of place under random misplacement?"
        ),
        "method": (
            "For each perturbation rate p_corrupt ∈ {0.05, 0.10, 0.20, "
            "0.30, 0.50}, sample a random subset S of |p N| surah "
            "indices (N=114), apply a within-S derangement, recompute "
            "the per-position J1-anomaly score (sum of squared "
            "Mahalanobis transitions involving that position) on the "
            "perturbed sequence, predict the top |S| by anomaly score, "
            "and measure F1 against ground-truth S. Repeat 100 trials "
            "per rate."
        ),
        "n_surahs": int(N),
        "n_trials_per_rate": int(N_TRIALS),
        "perturb_rates": PERTURB_RATES,
        "seed": SEED,
        "ridge_lambda": RIDGE_LAMBDA,
        "feat_names": FEAT_NAMES,
        "canonical_J1_whitened": j1_canonical,
        "results_per_rate": results,
        "verdict": verdict,
        "interpretation": [
            "Random-baseline F1 at perturbation rate p_corrupt is "
            "exactly p_corrupt (random predict-|S|-of-N has expected "
            "F1 = |S|/N = p_corrupt). The 'lift_vs_expected' column "
            "shows the gain over random.",
            "If `verdict = POSITIVE_RECONSTRUCTION_DETECTABLE`, the "
            "5-D Mahalanobis transitions carry enough local information "
            "to flag perturbed positions at >2x random baseline at every "
            "tested rate up to 20 %. This is the strongest 'error-"
            "detecting code' claim the project can make at the surah "
            "scale.",
            "Note: This is the IDENTIFICATION half. The CORRECTION half "
            "(can we put the misplaced surahs back in their correct "
            "positions?) requires a permutation search over the |S|! "
            "candidate orderings, tractable only for small |S|. Deferred.",
        ],
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   {'rate':<8s} {'n_corr':>7s}  "
          f"{'F1_mean':>8s} {'baseline':>9s} {'lift':>5s}  "
          f"{'J1_pert/canon':>14s}")
    for r in results:
        print(f"[{EXP}]   {r['p_corrupt']:<8.2f} {r['n_corrupt_per_trial']:>7d}  "
              f"{r['f1_mean']:>8.4f} {r['f1_random_baseline_mean']:>9.4f} "
              f"{r['f1_lift_vs_random']:>5.2f}x  "
              f"{r['perturbed_J1_mean'] / max(r['canonical_J1'], 1e-9):>14.3f}")
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
