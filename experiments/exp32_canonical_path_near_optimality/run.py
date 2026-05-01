"""
exp32_canonical_path_near_optimality/run.py
===========================================
Combinatorial extension of T8 (locked scalar
`path_length_canonical_5D` -> rank among 1M random permutations):
is the canonical surah ordering NEAR-OPTIMAL under combinatorial
search, or merely statistically rare?

Protocol
--------
1. Load all 114 Quran surahs in canonical order. Compute 5-D features.
2. `L_canonical` = sum over i of ||f_i - f_{i+1}||_M  in Mahalanobis
   metric using the locked `S_inv` from phase_06.
3. Baselines:
   a. Nearest-neighbour greedy from each of the 114 starting surahs.
      Take the minimum over all 114 starts  -> `L_NN_min`.
   b. 2-opt local descent:
        * from canonical ordering                  -> `L_2opt_canonical`
        * from 200 random permutations             -> distribution of
                                                      local minima;
                                                      take the min
                                                      -> `L_2opt_random_min`
   c. Simulated annealing: 50k iterations from the 2-opt-canonical seed,
      geometric cooling 1.0 -> 0.01, swap moves. Take best
      -> `L_SA`.
4. Report:
     * `ratio_canonical_to_2opt_canonical` = L_canonical / L_2opt_canonical
     * `ratio_canonical_to_2opt_random_min` = L_canonical / L_2opt_random_min
     * `ratio_canonical_to_SA` = L_canonical / L_SA  (global lower bound)
     * `rank_of_canonical_among_random_2opt_minima` in [1, 201]
     * distribution of 2-opt random minima (summary stats)
5. Additionally report uniform-random-permutation baseline (1k samples)
   to compare against T8's rank-based claim.

Reads (verified): phase_06_phi_m.pkl
Writes only under results/experiments/exp32_canonical_path_near_optimality/.
No locked artefact is touched.
"""
from __future__ import annotations

import json
import math
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

EXP = "exp32_canonical_path_near_optimality"
SEED = 42
N_RANDOM_2OPT_STARTS = 200
SA_ITER = 50_000
SA_T_START = 1.0
SA_T_END = 0.01
N_UNIFORM_RANDOM = 1000


def _compute_pairwise_M(X: np.ndarray, Sinv: np.ndarray) -> np.ndarray:
    """Full 114x114 Mahalanobis distance matrix."""
    diff = X[:, None, :] - X[None, :, :]
    # d^2 = (x-y) S_inv (x-y), use einsum
    d2 = np.einsum("ijk,kl,ijl->ij", diff, Sinv, diff)
    d2 = np.clip(d2, 0.0, None)
    return np.sqrt(d2)


def _path_length(order: list[int], D: np.ndarray) -> float:
    return float(sum(D[order[i], order[i + 1]] for i in range(len(order) - 1)))


def _nn_greedy(start: int, D: np.ndarray) -> list[int]:
    n = D.shape[0]
    unvisited = set(range(n)) - {start}
    order = [start]
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: D[cur, j])
        order.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    return order


def _two_opt(order: list[int], D: np.ndarray, max_passes: int = 50) -> list[int]:
    """Standard 2-opt local descent on an open Hamiltonian path.
    Iterates until no improving edge swap exists or max_passes reached.
    """
    n = len(order)
    path = list(order)
    for _pass in range(max_passes):
        improved = False
        # For an open path, swapping edges (i,i+1) and (j,j+1) means
        # reversing path[i+1:j+1]. Valid for 0 <= i < j-1 <= n-2.
        for i in range(n - 2):
            a = path[i]
            b = path[i + 1]
            D_ab = D[a, b]
            for j in range(i + 2, n - 1):
                c = path[j]
                d = path[j + 1]
                delta = (D[a, c] + D[b, d]) - (D_ab + D[c, d])
                if delta < -1e-12:
                    path[i + 1:j + 1] = path[i + 1:j + 1][::-1]
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return path


def _sa(
    order0: list[int], D: np.ndarray,
    n_iter: int, T0: float, T1: float, rng: random.Random,
) -> tuple[list[int], float]:
    n = len(order0)
    cur = list(order0)
    cur_L = _path_length(cur, D)
    best = list(cur)
    best_L = cur_L
    # geometric cooling
    alpha = (T1 / T0) ** (1.0 / max(n_iter - 1, 1))
    T = T0
    for _it in range(n_iter):
        # 2-opt swap move: pick i < j and reverse slice
        i = rng.randrange(0, n - 2)
        j = rng.randrange(i + 2, n)
        a = cur[i]
        b = cur[i + 1]
        c = cur[j]
        d = cur[j + 1] if (j + 1) < n else None
        if d is None:
            # edge (j, j+1) does not exist (j is terminal);
            # fall back to single adjacent swap
            delta = 0.0
            # approximate: accept only if i+1 < j trivially equal
            new = list(cur)
            new[i + 1:j + 1] = new[i + 1:j + 1][::-1]
            new_L = _path_length(new, D)
            delta = new_L - cur_L
        else:
            delta = (D[a, c] + D[b, d]) - (D[a, b] + D[c, d])
        if delta < 0 or rng.random() < math.exp(-delta / max(T, 1e-12)):
            cur[i + 1:j + 1] = cur[i + 1:j + 1][::-1]
            cur_L = cur_L + delta
            if cur_L < best_L:
                best_L = cur_L
                best = list(cur)
        T = T * alpha
    return best, best_L


def _summarise(values) -> dict:
    if not values:
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


def _surah_num(label: str) -> int | None:
    try:
        return int(str(label).split(":")[1])
    except Exception:
        return None


def main() -> int:
    t0 = time.time()
    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading phase_06_phi_m state (read-only)...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    S_inv = np.asarray(state["S_inv"], dtype=float)

    # Collect ALL 114 Quran surahs in canonical order
    q_units = CORPORA.get("quran", [])
    # Sort by surah number for canonical order
    q_sorted = sorted(
        q_units, key=lambda u: _surah_num(str(getattr(u, "label", ""))) or 0
    )
    X = []
    labels = []
    for u in q_sorted:
        try:
            X.append(ft.features_5d(u.verses))
            labels.append(str(getattr(u, "label", "?")))
        except Exception as e:
            print(f"[{EXP}] feature fail for {getattr(u,'label','?')}: {e}")
    X = np.asarray(X, dtype=float)
    N = X.shape[0]
    print(f"[{EXP}] full Quran corpus: N = {N} surahs, feat dim = {X.shape[1]}")
    if N < 50:
        raise RuntimeError(f"Too few Quran surahs ({N})")

    # Compute pairwise Mahalanobis distance matrix (one-shot)
    print(f"[{EXP}] computing {N}x{N} Mahalanobis distance matrix...")
    D = _compute_pairwise_M(X, S_inv)

    # Canonical path is just [0, 1, 2, ..., N-1]
    canonical_order = list(range(N))
    L_canonical = _path_length(canonical_order, D)
    print(f"[{EXP}] L_canonical = {L_canonical:.3f}")

    # ---- NN-greedy from each start ----------------------------------------
    print(f"[{EXP}] nearest-neighbour greedy from each of {N} starts...")
    nn_L = []
    nn_best_order = None
    nn_best_L = math.inf
    for s in range(N):
        o = _nn_greedy(s, D)
        L = _path_length(o, D)
        nn_L.append(L)
        if L < nn_best_L:
            nn_best_L, nn_best_order = L, o
    print(f"[{EXP}]   NN min = {nn_best_L:.3f}   median = {np.median(nn_L):.3f}")

    # ---- 2-opt from canonical ---------------------------------------------
    print(f"[{EXP}] 2-opt descent from canonical...")
    t = time.time()
    o_2opt_canon = _two_opt(canonical_order, D)
    L_2opt_canon = _path_length(o_2opt_canon, D)
    print(f"[{EXP}]   L_2opt_canonical = {L_2opt_canon:.3f}  "
          f"({time.time() - t:.1f}s)")

    # ---- 2-opt from random starts -----------------------------------------
    print(f"[{EXP}] 2-opt descent from {N_RANDOM_2OPT_STARTS} random starts...")
    rng = random.Random(SEED)
    random_2opt_Ls: list[float] = []
    random_2opt_best_L = math.inf
    random_2opt_best_order = None
    for b in range(N_RANDOM_2OPT_STARTS):
        seed_order = list(range(N))
        rng.shuffle(seed_order)
        o_b = _two_opt(seed_order, D)
        L_b = _path_length(o_b, D)
        random_2opt_Ls.append(L_b)
        if L_b < random_2opt_best_L:
            random_2opt_best_L = L_b
            random_2opt_best_order = o_b
        if (b + 1) % 50 == 0:
            print(f"[{EXP}]   2-opt random [{b+1}/{N_RANDOM_2OPT_STARTS}]  "
                  f"min so far = {random_2opt_best_L:.3f}  "
                  f"({time.time() - t0:.0f}s)")
    print(f"[{EXP}]   L_2opt_random_min = {random_2opt_best_L:.3f}   "
          f"median = {np.median(random_2opt_Ls):.3f}")

    # ---- SA polish --------------------------------------------------------
    print(f"[{EXP}] simulated annealing polish ({SA_ITER} iter)...")
    # Start SA from the best 2-opt seed found so far
    if random_2opt_best_L < L_2opt_canon:
        sa_seed = list(random_2opt_best_order)
    else:
        sa_seed = list(o_2opt_canon)
    sa_best, sa_best_L = _sa(sa_seed, D, SA_ITER, SA_T_START, SA_T_END, rng)
    # One final 2-opt clean-up on SA output
    sa_best = _two_opt(sa_best, D)
    sa_best_L = _path_length(sa_best, D)
    L_best_known = min(sa_best_L, random_2opt_best_L, L_2opt_canon, nn_best_L)
    print(f"[{EXP}]   L_SA = {sa_best_L:.3f}   L_best_known = {L_best_known:.3f}")

    # ---- Ranks ------------------------------------------------------------
    # Rank of canonical among the random-2-opt local minima distribution
    all_2opt = sorted(random_2opt_Ls + [L_2opt_canon])
    rank_canonical_in_2opt = int(
        sum(1 for v in random_2opt_Ls if v <= L_canonical)
    )  # how many random 2-opt local minima are shorter than canonical

    # Uniform-random-permutation baseline (for comparison with T8)
    print(f"[{EXP}] computing {N_UNIFORM_RANDOM} uniform-random-permutation "
          f"baselines...")
    rnd_Ls: list[float] = []
    for _ in range(N_UNIFORM_RANDOM):
        o = list(range(N))
        rng.shuffle(o)
        rnd_Ls.append(_path_length(o, D))
    n_better_than_canonical = sum(1 for L in rnd_Ls if L <= L_canonical)

    # ---- Assemble + save --------------------------------------------------
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "Is the canonical surah ordering near-optimal under "
            "combinatorial search (NN-greedy + 2-opt + SA), not just "
            "statistically rare under uniform random permutations?"
        ),
        "config": {
            "seed": SEED,
            "n_random_2opt_starts": N_RANDOM_2OPT_STARTS,
            "sa_iter": SA_ITER,
            "sa_t_start": SA_T_START,
            "sa_t_end": SA_T_END,
            "n_uniform_random": N_UNIFORM_RANDOM,
        },
        "n_surahs": N,
        "canonical_order_labels": labels,
        "L_canonical": L_canonical,
        "L_NN_min_across_114_starts": nn_best_L,
        "L_NN_summary": _summarise(nn_L),
        "L_2opt_canonical": L_2opt_canon,
        "L_2opt_random_min": random_2opt_best_L,
        "L_2opt_random_summary": _summarise(random_2opt_Ls),
        "L_SA_final": sa_best_L,
        "L_best_known_lower_bound": L_best_known,
        "ratio_canonical_to_2opt_canonical": L_canonical / L_2opt_canon,
        "ratio_canonical_to_2opt_random_min": L_canonical / random_2opt_best_L,
        "ratio_canonical_to_SA": L_canonical / sa_best_L,
        "ratio_canonical_to_best_known": L_canonical / L_best_known,
        "rank_of_canonical_among_200_random_2opt_minima": rank_canonical_in_2opt,
        "uniform_random_baseline": {
            "n": N_UNIFORM_RANDOM,
            "summary": _summarise(rnd_Ls),
            "n_uniformly_shorter_than_canonical": n_better_than_canonical,
            "one_sided_p_value_canonical_shorter_than_random": (
                n_better_than_canonical / N_UNIFORM_RANDOM
            ),
        },
        "runtime_seconds": round(time.time() - t0, 1),
    }
    outfile = out_dir / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console summary --------------------------------------------------
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] ======================= path-length summary =======================")
    print(f"   L_canonical                 = {L_canonical:.3f}")
    print(f"   L_NN_min (114 starts)       = {nn_best_L:.3f}  "
          f"ratio canon/NN_min = {L_canonical / nn_best_L:.4f}")
    print(f"   L_2opt_canonical            = {L_2opt_canon:.3f}  "
          f"ratio canon/2opt_canon = {L_canonical / L_2opt_canon:.4f}")
    print(f"   L_2opt_random_min (200)     = {random_2opt_best_L:.3f}  "
          f"ratio canon/2opt_rand_min = {L_canonical / random_2opt_best_L:.4f}")
    print(f"   L_SA (50k iter)             = {sa_best_L:.3f}  "
          f"ratio canon/SA = {L_canonical / sa_best_L:.4f}")
    print(f"   L_best_known (lower bound)  = {L_best_known:.3f}  "
          f"ratio canon/best = {L_canonical / L_best_known:.4f}")
    print(f"[{EXP}] uniform-random baseline N={N_UNIFORM_RANDOM}: "
          f"{n_better_than_canonical} of {N_UNIFORM_RANDOM} shorter than canonical  "
          f"(one-sided p = {n_better_than_canonical / N_UNIFORM_RANDOM:.4f})")
    print(f"[{EXP}] rank of canonical among 200 random 2-opt local minima: "
          f"{rank_canonical_in_2opt}/200  "
          f"({'top' if rank_canonical_in_2opt == 0 else f'{rank_canonical_in_2opt} local minima shorter'})")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
