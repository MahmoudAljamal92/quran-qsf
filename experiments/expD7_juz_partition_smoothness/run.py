"""
expD7_juz_partition_smoothness/run.py
=====================================
Opportunity D7 (OPPORTUNITY_TABLE_DETAIL.md):
  Apply the E17 J1 smoothness test at juzʾ granularity (30 partitions of
  the 6 236 verses) instead of surah granularity (114 partitions). Test
  whether the canonical juzʾ boundary placement minimises 5-D feature
  discontinuity more than random partitions of the same sizes.

  D8 (ḥizb 60, rubʿ 240, rukūʿ ~558) is deferred — same algorithm but
  needs the larger boundary lists.

Method (mirror of expE17b_mushaf_j1_1m_perms):
  1. Build 30 juzʾ Units, each containing the verses falling inside that
     juzʾ (boundaries hardcoded from the standard Tanzil partition).
  2. Compute the 5-D feature vector (EL, VL_CV, CN, H_cond, T) per juzʾ
     via src.features.features_5d.
  3. Compute J1 = sum_{i=1..29} (X[i+1] - X[i])^T Σ_inv (X[i+1] - X[i])
     where Σ = pooled covariance of the 30 juzʾ feature vectors + ridge.
  4. Generate N_PERM random 29-cut partitions of the 6 236-verse sequence
     producing 30 windows with the SAME size distribution as the canonical
     juzʾ (preserves the size-of-juz histogram so the test isolates
     BOUNDARY PLACEMENT, not size variance).
  5. Recompute J1 for each random partition. Compare canonical J1
     quantile vs random null.

Pre-registration:
  PASS if canonical-juz J1 quantile <= 0.05 against the size-preserving
  random-partition null. STRONG PASS if quantile == 0/N_PERM.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl  (CORPORA.quran)

Writes:
  - results/experiments/expD7_juz_partition_smoothness/expD7_juz_partition_smoothness.json
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
from src.features import features_5d, ARABIC_CONN  # noqa: E402

EXP = "expD7_juz_partition_smoothness"
SEED = 42
# Reduced from 10_000 to 1_000 because features_5d on ~200-verse juzʾ
# windows is ~10x slower per call than on small Band-A surahs (CamelTools
# root extraction scales linearly with verses). 1_000 perms still gives a
# (k+1)/(N+1) p-bound of ~ 1e-3, ample for the canonical-vs-random test.
N_PERM = 1_000
RIDGE_LAMBDA = 1e-6


# --- Tanzil canonical 30-juzʾ start verses (1-indexed surah:verse) -----
# Source: tanzil.net juz boundary list, also in standard Mushaf prints.
JUZ_STARTS_1IDX = [
    (1, 1),    (2, 142),  (2, 253),  (3, 93),   (4, 24),
    (4, 148),  (5, 82),   (6, 111),  (7, 88),   (8, 41),
    (9, 93),   (11, 6),   (12, 53),  (15, 1),   (17, 1),
    (18, 75),  (21, 1),   (23, 1),   (25, 21),  (27, 56),
    (29, 46),  (33, 31),  (36, 28),  (39, 32),  (41, 47),
    (46, 1),   (51, 31),  (58, 1),   (67, 1),   (78, 1),
]
assert len(JUZ_STARTS_1IDX) == 30


def _flat_verse_index(quran_units, sura_1idx: int, verse_1idx: int) -> int:
    """Return the 0-indexed flat verse index of (sura, verse) in the
    concatenated 6 236-verse Quran sequence (mushaf order)."""
    flat = 0
    for u in quran_units:
        # Unit.label = "Q:001" etc.
        sn = int(str(getattr(u, "label", "")).replace("Q:", "").strip())
        n = len(u.verses)
        if sn < sura_1idx:
            flat += n
        elif sn == sura_1idx:
            return flat + (verse_1idx - 1)
        else:
            raise IndexError(
                f"Looking for ({sura_1idx},{verse_1idx}) but already past "
                f"surah in iteration order. Mushaf order assumption broken."
            )
    raise IndexError(f"({sura_1idx},{verse_1idx}) not found in the corpus")


def _juz_size_distribution(starts_flat: list[int], total: int) -> list[int]:
    """Sizes of the 30 juzʾ in verses, given start indices (sorted)."""
    starts = sorted(starts_flat)
    ends = starts[1:] + [total]
    return [e - s for s, e in zip(starts, ends)]


def _whitening_transform(X: np.ndarray, ridge: float = RIDGE_LAMBDA) -> np.ndarray:
    """Return X' such that ||X'_i - X'_j||^2 == (X_i-X_j)^T Σ_inv (X_i-X_j)
    where Σ = Cov(X) + ridge*I and Σ_inv = pinv(Σ).
    """
    mu = X.mean(axis=0)
    Z = X - mu
    Sigma = np.cov(Z, rowvar=False) + ridge * np.eye(X.shape[1])
    w, V = np.linalg.eigh(Sigma)
    w_inv = 1.0 / w
    A = (V * np.sqrt(w_inv)).T  # A^T A == Σ_inv
    return X @ A.T


def _features_for_partition(
    flat_verses: list[str], starts: list[int]
) -> np.ndarray:
    """For a partition (sorted start indices into the flat verse list),
    compute the 5-D features per partition window. Returns (n_part, 5)."""
    n = len(flat_verses)
    starts_sorted = sorted(starts)
    ends = starts_sorted[1:] + [n]
    rows = []
    for s, e in zip(starts_sorted, ends):
        verses = flat_verses[s:e]
        if len(verses) < 2:
            return np.empty((0, 5))  # invalid; skip this partition
        try:
            v = features_5d(verses, ARABIC_CONN)
        except Exception:
            return np.empty((0, 5))
        if not np.all(np.isfinite(v)):
            return np.empty((0, 5))
        rows.append(v)
    return np.asarray(rows, dtype=float)


def _j1_smoothness(Xp: np.ndarray) -> float:
    """J1 in pre-whitened coords = sum of squared Euclidean transitions."""
    if Xp.shape[0] < 2:
        return float("nan")
    diffs = Xp[1:] - Xp[:-1]
    return float((diffs * diffs).sum())


def _random_partition_starts(
    sizes: list[int], total: int, rng: np.random.Generator
) -> list[int]:
    """Generate random 29 cut points yielding 30 windows of permuted SAME
    sizes as the canonical juzʾ. This preserves the exact size histogram
    so only the boundary PLACEMENT is being tested.

    A random size-permutation of `sizes` is laid down sequentially from
    flat verse 0, producing 30 contiguous windows. Returns their start
    positions.
    """
    perm = rng.permutation(len(sizes))
    starts = [0]
    cur = 0
    for k in perm[:-1]:
        cur += sizes[k]
        starts.append(cur)
    return starts


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass
    else:
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    quran_units = state["CORPORA"]["quran"]
    n_surah = len(quran_units)

    # Flat verse list in mushaf order
    flat_verses: list[str] = []
    for u in quran_units:
        flat_verses.extend(u.verses)
    n_total = len(flat_verses)
    print(f"[{EXP}] n_surah = {n_surah}   n_total_verses = {n_total}")

    # Map juzʾ starts to flat verse indices
    juz_flat_starts = [
        _flat_verse_index(quran_units, sn, vn) for sn, vn in JUZ_STARTS_1IDX
    ]
    juz_sizes = _juz_size_distribution(juz_flat_starts, n_total)
    print(f"[{EXP}] juzʾ size range: min={min(juz_sizes)}  "
          f"max={max(juz_sizes)}  mean={np.mean(juz_sizes):.1f}")

    # ---- Canonical-juzʾ feature matrix + J1 ----
    X_canonical = _features_for_partition(flat_verses, juz_flat_starts)
    if X_canonical.shape[0] != 30:
        raise RuntimeError(
            f"Canonical juzʾ feature extraction failed: got "
            f"{X_canonical.shape[0]} feature rows, expected 30."
        )
    # Precompute the whitening matrix A from the canonical Σ once. The
    # SAME A is reused on every random-perm partition so all J1 values
    # are computed in the same coordinate frame.
    mu = X_canonical.mean(axis=0)
    Sigma = np.cov(X_canonical - mu, rowvar=False) + RIDGE_LAMBDA * np.eye(5)
    w, V = np.linalg.eigh(Sigma)
    A = (V * np.sqrt(1.0 / w)).T  # A^T A == Σ_inv

    def _j1_via_A(X: np.ndarray) -> float:
        Xp = X @ A.T
        diffs = Xp[1:] - Xp[:-1]
        return float((diffs * diffs).sum())

    j1_canonical = _j1_via_A(X_canonical)
    print(f"[{EXP}] canonical-juzʾ feature matrix: {X_canonical.shape}")
    print(f"[{EXP}] canonical-juzʾ J1 smoothness:  {j1_canonical:.6f}")

    # ---- Random size-preserving null ----
    rng = np.random.default_rng(SEED)
    n_le_canonical = 0
    n_done = 0
    perm_J1_min = math.inf
    perm_J1_max = -math.inf
    perm_J1_sum = 0.0
    perm_J1_sumsq = 0.0
    n_invalid = 0

    print(f"[{EXP}] running {N_PERM} random size-preserving partitions...")
    for i in range(N_PERM):
        starts_rand = _random_partition_starts(juz_sizes, n_total, rng)
        X_rand = _features_for_partition(flat_verses, starts_rand)
        if X_rand.shape[0] != 30:
            n_invalid += 1
            continue
        j1_rand = _j1_via_A(X_rand)
        if not math.isfinite(j1_rand):
            n_invalid += 1
            continue
        if j1_rand <= j1_canonical:
            n_le_canonical += 1
        n_done += 1
        if j1_rand < perm_J1_min:
            perm_J1_min = j1_rand
        if j1_rand > perm_J1_max:
            perm_J1_max = j1_rand
        perm_J1_sum += j1_rand
        perm_J1_sumsq += j1_rand * j1_rand
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"[{EXP}]   perm {i+1}/{N_PERM}  n_done={n_done}  "
                  f"min_J1={perm_J1_min:.4f}  n_le_canonical={n_le_canonical}  "
                  f"elapsed={elapsed:.1f}s", flush=True)

    perm_J1_mean = perm_J1_sum / n_done if n_done else float("nan")
    perm_J1_var = (perm_J1_sumsq / n_done - perm_J1_mean ** 2) if n_done else float("nan")
    perm_J1_sd = math.sqrt(max(perm_J1_var, 0.0)) if n_done else float("nan")
    q_le_canonical = n_le_canonical / n_done if n_done else float("nan")
    p_perm = (n_le_canonical + 1) / (n_done + 1) if n_done else float("nan")

    if n_le_canonical == 0 and n_done > 0:
        verdict = "JUZ_J1_GLOBAL_EXTREMUM"
    elif q_le_canonical <= 0.05:
        verdict = "JUZ_J1_DOMINANT"
    elif q_le_canonical <= 0.50:
        verdict = "JUZ_J1_BETTER_THAN_AVERAGE"
    else:
        verdict = "NULL_J1_AT_JUZ_LEVEL"

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "D7",
        "title": (
            "Juzʾ partition J1 smoothness test: do the canonical 30-juzʾ "
            "boundaries minimise 5-D feature discontinuity more than "
            "random partitions of the same size distribution?"
        ),
        "method": (
            "Mirror of expE17b_mushaf_j1_1m_perms but at juzʾ granularity. "
            "Same J1 = sum of squared Mahalanobis transitions in pre-"
            "whitened coords; same ridge=1e-6; same `(k+1)/(N+1)` p-bound. "
            "Random null preserves the canonical juzʾ size histogram (30 "
            "contiguous windows in random size-permutation order) so the "
            "test isolates BOUNDARY PLACEMENT, not size variance."
        ),
        "n_perms": int(n_done),
        "n_invalid_perms": int(n_invalid),
        "seed": SEED,
        "ridge_lambda": RIDGE_LAMBDA,
        "canonical_juz_sizes": juz_sizes,
        "canonical_juz_J1": j1_canonical,
        "perm_J1_min": perm_J1_min,
        "perm_J1_max": perm_J1_max,
        "perm_J1_mean": perm_J1_mean,
        "perm_J1_sd": perm_J1_sd,
        "n_perms_le_canonical": int(n_le_canonical),
        "q_le_canonical": q_le_canonical,
        "p_perm_le_canonical": p_perm,
        "verdict": verdict,
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   canonical J1            = {j1_canonical:.6f}")
    print(f"[{EXP}]   random-perm null:")
    print(f"[{EXP}]     min  J1  = {perm_J1_min:.4f}")
    print(f"[{EXP}]     mean J1  = {perm_J1_mean:.4f}")
    print(f"[{EXP}]     sd   J1  = {perm_J1_sd:.4f}")
    print(f"[{EXP}]   n_perms_le_canonical    = {n_le_canonical} / {n_done}")
    print(f"[{EXP}]   q_le_canonical          = {q_le_canonical:.6f}")
    print(f"[{EXP}]   p_perm bound            = {p_perm:.3e}")
    print(f"[{EXP}]   verdict                 = {verdict}")
    print(f"[{EXP}]   runtime                 = {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
