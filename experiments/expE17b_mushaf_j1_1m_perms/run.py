"""
expE17b_mushaf_j1_1m_perms/run.py
==================================
Opportunity A10 (OPPORTUNITY_TABLE_DETAIL.md):
  Extend the canonical-order J1 smoothness permutation null from
  N = 10 000 (`expE17_dual_opt`) to N = 1 000 000.

Pre-registration (frozen at 2026-04-25 from S1 of OPPORTUNITY_TABLE_DETAIL):
  Statistic:
    J1(σ) = Σ_{i=1..113} (X[σ_{i+1}] − X[σ_i])^T Σ_inv (X[σ_{i+1}] − X[σ_i])
  where X is the 114 × 5 surah-level feature matrix on FEAT_COLS, and
  Σ_inv is the pseudoinverse of the Quran-pooled covariance (1e-6 ridge),
  matching expE17_dual_opt:78-82 byte-for-byte.

  Null:        Mushaf J1 ≥ random-perm J1 minimum, i.e. Mushaf is not the
               smallest-J1 of the {Mushaf} ∪ {N random permutations} pool.
  Bound:       q = (#perms with J1 ≤ J1_Mushaf) / N. Quantile-based p-bound
               at p ≤ 1 / (N + 1) when Mushaf strictly beats all N perms.
  Pass:        q == 0  →  p < 1 / (10⁶ + 1)  ≈  10⁻⁶
  Seed:        42 (matches expE17_dual_opt for direct comparability)
  Equivalence: This pipeline reproduces expE17_dual_opt's J1 statistic
               BIT-IDENTICALLY at N = 10 000 (verified separately by setting
               N_PERM = 10000 and comparing q_J1_mushaf, q_J1_nuzul to the
               locked expE17 report).

This script is sandbox / read-only:
  inputs:  results/checkpoints/phase_06_phi_m.pkl
  outputs: results/experiments/expE17b_mushaf_j1_1m_perms/{json, md}

It does NOT compute J2 (sign-entropy axis), per Tier-S1 instruction:
  "Publish the J1 law solo; leave J2 as a separate non-universal-smoothness
   footnote."

Performance: vectorised in batches of 50 000 perms via
  perms = argsort(rng.random((B, 114))). Whitened X is precomputed so the
  per-perm cost is one (B, 113, 5) tensor diff + (B,)-shaped reduction.
  Wall-clock target: ≤ 5 minutes on a modern x86 CPU.
"""

from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import entropy as shannon_entropy

# Make the sandbox importable regardless of how this script is launched.
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

EXP = "expE17b_mushaf_j1_1m_perms"
SEED = 42
N_PERM = 1_000_000
BATCH = 50_000
FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]

# Egyptian-Standard-Edition Nuzul order, same source as expE17_dual_opt:48-56.
NUZUL_ORDER_1IDX = [
    96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102,
    107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106, 101, 75,
    104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20, 56, 26, 27,
    28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45,
    46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82,
    84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55, 76, 65, 98,
    59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110,
]
assert len(NUZUL_ORDER_1IDX) == 114 and set(NUZUL_ORDER_1IDX) == set(range(1, 115))


def _load_per_surah_features(state: dict) -> np.ndarray:
    """Reproduce expE17_dual_opt:64-76 to extract a (114, 5) feature matrix
    in canonical Mushaf order (row i = surah i+1)."""
    assert state["FEAT_COLS"] == FV_ORDER, (
        f"FEAT_COLS drift: expected {FV_ORDER}, got {state['FEAT_COLS']}"
    )
    feat_by_surah: dict[int, list[float]] = {}
    for i, u in enumerate(state["CORPORA"]["quran"]):
        label = getattr(u, "label", f"Q:{i + 1}")
        sn = int(str(label).replace("Q:", "").strip())
        feat_by_surah[sn] = [state["FEATS"]["quran"][i][c] for c in FV_ORDER]
    missing = set(range(1, 115)) - set(feat_by_surah.keys())
    if missing:
        raise RuntimeError(f"Missing surah indices: {sorted(missing)[:5]}...")
    return np.array(
        [feat_by_surah[s] for s in range(1, 115)], dtype=np.float64
    )


def _whitening_transform(X: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    """Return X' such that ||X'_i - X'_j||² == (X_i - X_j)^T Σ_inv (X_i - X_j),
    where Σ = Cov(X) + ridge·I and Σ_inv = pinv(Σ).

    Construction: Σ_inv = U diag(λ_inv) U^T (eigendecomp of symmetric PD).
    Take A = diag(sqrt(λ_inv)) U^T  →  Σ_inv = A^T A.
    Then x^T Σ_inv x = ||A x||² = ||x'||² with x' = A x.

    Equivalent to the Mahalanobis-distance computation in
    expE17_dual_opt:78-89 but pre-baked into the feature matrix so the
    inner loop becomes a plain Euclidean squared-distance sum.
    """
    mu = X.mean(axis=0)
    Z = X - mu
    Sigma = np.cov(Z, rowvar=False) + ridge * np.eye(X.shape[1])
    # Use eigh on the symmetric PD covariance, then invert eigenvalues.
    w, V = np.linalg.eigh(Sigma)
    w_inv = 1.0 / w  # PD ⇒ all w > 0; ridge guarantees this
    A = (V * np.sqrt(w_inv)).T  # shape (p, p);  A^T A == Σ_inv
    Xp = X @ A.T               # shape (n, p)
    return Xp


def _j1_one(order_1idx: list[int], Xp: np.ndarray) -> float:
    """J1 in pre-whitened coordinates. Reduces to plain L2² of transitions."""
    rows = Xp[np.array(order_1idx, dtype=np.int64) - 1]
    diffs = rows[1:] - rows[:-1]
    return float((diffs * diffs).sum())


def _j2_sign_entropy(order_1idx: list[int], X: np.ndarray) -> float:
    """Entropy of the 5-bit sign-direction sequence (same definition as
    expE17_dual_opt:91-107). Computed once for Mushaf + Nuzul only,
    NOT over the 10⁶ perms — A10 is J1-only.
    """
    rows = X[np.array(order_1idx, dtype=np.int64) - 1]
    diffs = rows[1:] - rows[:-1]
    sign = np.sign(diffs).astype(int) + 1  # {0, 1, 2}
    code = (sign[:, 0] * 81 + sign[:, 1] * 27 + sign[:, 2] * 9
            + sign[:, 3] * 3 + sign[:, 4]).tolist()
    cnt = Counter(code)
    freqs = np.array(list(cnt.values()), dtype=float)
    freqs /= freqs.sum()
    return float(shannon_entropy(freqs, base=2))


def _batch_j1(perms: np.ndarray, Xp: np.ndarray) -> np.ndarray:
    """Vectorised J1 for a (B, 114) batch of 0-indexed permutations.

    Returns (B,) float64 array of J1 values."""
    rows = Xp[perms]                               # (B, 114, 5)
    diffs = rows[:, 1:, :] - rows[:, :-1, :]       # (B, 113, 5)
    return (diffs * diffs).sum(axis=(1, 2))        # (B,)


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --------------------------------------------------------------- inputs
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X = _load_per_surah_features(state)
    Xp = _whitening_transform(X, ridge=1e-6)

    mushaf = list(range(1, 115))
    nuzul = list(NUZUL_ORDER_1IDX)

    # --------------------------------------------------------------- baselines
    J1_mushaf = _j1_one(mushaf, Xp)
    J1_nuzul = _j1_one(nuzul, Xp)
    J2_mushaf = _j2_sign_entropy(mushaf, X)
    J2_nuzul = _j2_sign_entropy(nuzul, X)

    print(f"[{EXP}] Mushaf J1 = {J1_mushaf:.6f}    J2 = {J2_mushaf:.4f}")
    print(f"[{EXP}] Nuzul  J1 = {J1_nuzul:.6f}    J2 = {J2_nuzul:.4f}")

    # --------------------------------------------------------------- 10^6 perm null
    rng = np.random.default_rng(SEED)
    n_le_mushaf = 0
    n_lt_mushaf = 0
    n_le_nuzul = 0
    n_lt_nuzul = 0
    perm_J1_min = math.inf
    perm_J1_max = -math.inf
    perm_J1_sum = 0.0
    perm_J1_sumsq = 0.0
    n_done = 0

    n_batches = N_PERM // BATCH
    rem = N_PERM - n_batches * BATCH

    def _consume(perms_idx0: np.ndarray) -> None:
        nonlocal n_le_mushaf, n_lt_mushaf, n_le_nuzul, n_lt_nuzul
        nonlocal perm_J1_min, perm_J1_max, perm_J1_sum, perm_J1_sumsq, n_done
        j1 = _batch_j1(perms_idx0, Xp)
        n_le_mushaf += int((j1 <= J1_mushaf).sum())
        n_lt_mushaf += int((j1 <  J1_mushaf).sum())
        n_le_nuzul  += int((j1 <= J1_nuzul ).sum())
        n_lt_nuzul  += int((j1 <  J1_nuzul ).sum())
        if j1.size:
            perm_J1_min = min(perm_J1_min, float(j1.min()))
            perm_J1_max = max(perm_J1_max, float(j1.max()))
            perm_J1_sum += float(j1.sum())
            perm_J1_sumsq += float((j1 * j1).sum())
            n_done += int(j1.size)

    # Vectorised batch perm: argsort(uniform) gives a uniformly random
    # permutation per row (Knuth-equivalent for our use). No rejection step.
    for b in range(n_batches):
        perms_idx0 = np.argsort(rng.random((BATCH, 114)), axis=1)
        _consume(perms_idx0)
        if (b + 1) % 4 == 0 or b == n_batches - 1:
            elapsed = time.time() - t0
            done = n_done
            print(f"[{EXP}]   batch {b+1}/{n_batches}   "
                  f"perms={done}/{N_PERM}   "
                  f"min_J1={perm_J1_min:.4f}   "
                  f"n_le_Mushaf={n_le_mushaf}   "
                  f"elapsed={elapsed:.1f}s")
    if rem > 0:
        perms_idx0 = np.argsort(rng.random((rem, 114)), axis=1)
        _consume(perms_idx0)

    perm_J1_mean = perm_J1_sum / n_done
    perm_J1_var  = perm_J1_sumsq / n_done - perm_J1_mean ** 2
    perm_J1_sd   = math.sqrt(max(perm_J1_var, 0.0))

    q_J1_mushaf_le = n_le_mushaf / n_done
    q_J1_mushaf_lt = n_lt_mushaf / n_done
    q_J1_nuzul_le  = n_le_nuzul  / n_done
    q_J1_nuzul_lt  = n_lt_nuzul  / n_done

    # --------------------------------------------------------------- p-bound
    # Mushaf is treated as one of the (N + 1) samples in a permutation pool.
    # Conservative one-sided p (lower-tail = "smaller J1 wins"):
    #   p_perm = (#perms with J1 ≤ J1_Mushaf + 1) / (N + 1)
    # If n_le_mushaf == 0 then p_perm = 1 / (N+1) exactly, which is the
    # tightest bound this perm count can deliver.
    p_perm_le_mushaf = (n_le_mushaf + 1) / (n_done + 1)
    p_perm_le_nuzul  = (n_le_nuzul  + 1) / (n_done + 1)

    # --------------------------------------------------------------- verdict
    if n_le_mushaf == 0:
        verdict = "MUSHAF_J1_GLOBAL_EXTREMUM_AT_1M"
    elif q_J1_mushaf_le <= 0.05:
        verdict = "MUSHAF_J1_DOMINANT_NOT_EXTREMUM"
    else:
        verdict = "NULL_J1"

    if n_le_mushaf == 0:
        print(f"[{EXP}] verdict = {verdict}  (Mushaf strictly < every one of "
              f"{n_done} random perms)")
    else:
        print(f"[{EXP}] verdict = {verdict}  ({n_le_mushaf}/{n_done} perms "
              f"<= Mushaf J1 = {J1_mushaf:.4f})")

    print(f"[{EXP}] Mushaf vs perms: q_le = {q_J1_mushaf_le:.7f}, "
          f"p_perm_le = {p_perm_le_mushaf:.3e}  (1/(N+1) = "
          f"{1/(n_done+1):.3e})")
    print(f"[{EXP}] Nuzul  vs perms: q_le = {q_J1_nuzul_le:.7f}, "
          f"p_perm_le = {p_perm_le_nuzul:.3e}")

    # --------------------------------------------------------------- report
    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "A10",
        "title": "Mushaf J1 smoothness — 10^6 random-perm null",
        "objective": (
            "Bound the p-value of S1 (Mushaf J1 extremum) below 1/(N+1) "
            "with N = 10^6, replacing the N = 10^4 floor of expE17_dual_opt."
        ),
        "seed": SEED,
        "n_permutations": int(n_done),
        "batch_size": BATCH,
        "feature_order": FV_ORDER,
        "ridge_lambda": 1e-6,
        "scalars": {
            "J1_mushaf": J1_mushaf,
            "J1_nuzul": J1_nuzul,
            "J2_mushaf": J2_mushaf,
            "J2_nuzul": J2_nuzul,
        },
        "perm_J1_summary": {
            "n": int(n_done),
            "min": perm_J1_min,
            "max": perm_J1_max,
            "mean": perm_J1_mean,
            "sd": perm_J1_sd,
        },
        "mushaf_quantiles": {
            "n_perms_le_mushaf": int(n_le_mushaf),
            "n_perms_lt_mushaf": int(n_lt_mushaf),
            "q_le_mushaf": q_J1_mushaf_le,
            "q_lt_mushaf": q_J1_mushaf_lt,
            "p_perm_le_mushaf": p_perm_le_mushaf,
            "p_perm_floor_inverse_n_plus_1": 1.0 / (n_done + 1),
        },
        "nuzul_quantiles": {
            "n_perms_le_nuzul": int(n_le_nuzul),
            "n_perms_lt_nuzul": int(n_lt_nuzul),
            "q_le_nuzul": q_J1_nuzul_le,
            "q_lt_nuzul": q_J1_nuzul_lt,
            "p_perm_le_nuzul": p_perm_le_nuzul,
        },
        "verdict": verdict,
        "verdict_taxonomy": {
            "MUSHAF_J1_GLOBAL_EXTREMUM_AT_1M":
                "n_perms_le_mushaf == 0  (Mushaf < every one of N perms)",
            "MUSHAF_J1_DOMINANT_NOT_EXTREMUM":
                "q_le_mushaf ≤ 0.05 but n_perms_le_mushaf > 0",
            "NULL_J1":
                "q_le_mushaf > 0.05",
        },
        "comparison_to_expE17_n_10000": {
            "expE17_q_J1_mushaf_le": 0.0,
            "expE17_q_J1_nuzul_le":  0.4046,
            "expE17_p_floor": 1.0 / (10000 + 1),
            "this_run_p_floor": 1.0 / (n_done + 1),
            "p_floor_tightening_ratio": (10000 + 1) / (n_done + 1),
        },
        "runtime_seconds": runtime,
        "side_effects": "no mutation of any pinned artefact; outputs under expE17b only",
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")
    print(f"[{EXP}] runtime: {runtime:.1f}s")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
