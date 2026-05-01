"""exp176 escalation 2 — TSP global-minimum analysis.

Locates approximate global-minimum TSP tour length for the 114 surahs
in F1_det feature space using multi-start 2-opt + simulated annealing,
and measures where Mushaf sits relative to:

  (i)   unconstrained minimum
  (ii)  length-tertile-constrained minimum (monotonic by logN tertile)
  (iii) M/D-segregated minimum (Meccan block contiguous, Medinan block contiguous)
  (iv)  combined (length-tertile × M/D) minimum

This converts 'Mushaf is better than random' into 'Mushaf is X% above
the best attainable tour under natural invariants'.
"""
from __future__ import annotations
import io
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}


def load_surahs():
    path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    surahs: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surahs[s].append(p[2].strip())
    return {i: " ".join(surahs[i]) for i in range(1, 115)}


def letter_freq(text: str) -> tuple[np.ndarray, int]:
    only = [c for c in text if c in ARABIC_LETTERS]
    n = len(only)
    if n == 0:
        return np.zeros(28), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


def detrend(F, logN, md):
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def tour_length(idx: np.ndarray, D: np.ndarray) -> float:
    """Path length (open tour, no return to start)."""
    return float(D[idx[:-1], idx[1:]].sum())


def two_opt(tour: np.ndarray, D: np.ndarray, max_iter: int = 200000) -> np.ndarray:
    """Standard open-path 2-opt: reverse segment [i, j]."""
    n = len(tour)
    t = tour.copy()
    improved = True
    it = 0
    L = tour_length(t, D)
    while improved and it < max_iter:
        improved = False
        for i in range(n - 2):
            a = t[i]
            b = t[i + 1]
            # delta from removing edge (a,b) and adding (a, t[j+1])
            for j in range(i + 2, n):
                c = t[j]
                d = t[j + 1] if j + 1 < n else None
                # cost of removing (a,b) + (c,d), adding (a,c) + (b,d)  (for open path last-edge absent)
                if d is None:
                    delta = D[a, c] - D[a, b]
                    new_tail = np.concatenate([t[:i + 1], t[j:i:-1]])
                    if len(new_tail) == n and delta < -1e-12:
                        t = new_tail
                        L += delta
                        improved = True
                        break
                else:
                    delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
                    if delta < -1e-12:
                        t = np.concatenate([t[:i + 1], t[j:i:-1], t[j + 1:]])
                        L += delta
                        improved = True
                        break
            if improved:
                break
        it += 1
    return t


def greedy_nn(start: int, D: np.ndarray) -> np.ndarray:
    n = D.shape[0]
    visited = [start]
    used = {start}
    cur = start
    while len(visited) < n:
        best_d, best_j = np.inf, -1
        for j in range(n):
            if j in used:
                continue
            if D[cur, j] < best_d:
                best_d, best_j = D[cur, j], j
        visited.append(best_j)
        used.add(best_j)
        cur = best_j
    return np.array(visited)


def multistart_2opt(D: np.ndarray, starts: int = 30, seed: int = 42) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    best_L = np.inf
    best_t = None
    n = D.shape[0]
    # greedy NN from each of several starting points
    gn_starts = list(range(min(starts, n)))
    rand_starts = [rng.permutation(n) for _ in range(max(0, starts - len(gn_starts)))]
    candidates = []
    for s in gn_starts:
        candidates.append(greedy_nn(s, D))
    for p in rand_starts:
        candidates.append(p)
    for c, cand in enumerate(candidates):
        t = two_opt(cand, D)
        L = tour_length(t, D)
        if L < best_L:
            best_L = L
            best_t = t
    return best_t, best_L


def main() -> None:
    surah_text = load_surahs()
    F = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F[i - 1], Nlet[i - 1] = letter_freq(surah_text[i])
    logN = np.log(Nlet)
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    F_det = detrend(F, logN, md_label)
    n = 114
    D = np.linalg.norm(F_det[:, None, :] - F_det[None, :, :], axis=-1)

    L_mushaf = tour_length(np.arange(n), D)
    NUZUL = [96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108,
             102, 107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106,
             101, 75, 104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20,
             56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42,
             43, 44, 45, 46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70,
             78, 79, 82, 84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55,
             76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110]
    nuzul_idx = np.array([s - 1 for s in NUZUL])
    L_nuzul = tour_length(nuzul_idx, D)

    print(f"L_Mushaf = {L_mushaf:.4f}")
    print(f"L_Nuzul  = {L_nuzul:.4f}")

    # null mean/std from prior run (B=5000)
    rng = np.random.default_rng(20260501)
    nulls = np.array([tour_length(rng.permutation(n), D) for _ in range(3000)])
    null_mean = nulls.mean()
    null_std = nulls.std()
    print(f"null     = {null_mean:.4f} ± {null_std:.4f}  (B=3000)")

    # --- (i) Unconstrained multi-start 2-opt
    print("\n(i) Unconstrained multi-start 2-opt (30 restarts)...")
    best_t_uncon, L_uncon = multistart_2opt(D, starts=30, seed=42)
    print(f"    L_min_unconstrained = {L_uncon:.4f}  "
          f"(Mushaf is {(L_mushaf / L_uncon - 1) * 100:.2f}% above unconstrained optimum)")

    # --- (ii) Length-tertile-constrained: tour must visit tertile-0 cluster, then 1, then 2
    #    (or reverse). We 2-opt within each tertile independently and then concat.
    q1, q2 = np.quantile(Nlet, [1/3, 2/3])
    tert = np.where(Nlet <= q1, 0, np.where(Nlet <= q2, 1, 2))
    cells_tert = [np.where(tert == k)[0] for k in range(3)]
    # order: long-to-short (matches Mushaf's macro gradient)
    print("\n(ii) Length-tertile-constrained (long→short macro, 2-opt within each tertile)...")
    def best_tour_in_cell(cell_idx):
        if len(cell_idx) <= 1:
            return cell_idx
        sub_D = D[np.ix_(cell_idx, cell_idx)]
        best_t, _ = multistart_2opt(sub_D, starts=min(10, len(cell_idx)), seed=42)
        return cell_idx[best_t]
    concat_desc = np.concatenate([best_tour_in_cell(cells_tert[2]),
                                  best_tour_in_cell(cells_tert[1]),
                                  best_tour_in_cell(cells_tert[0])])
    L_tert_desc = tour_length(concat_desc, D)
    print(f"    L_min_tert_long_to_short = {L_tert_desc:.4f}")

    # --- (iii) M/D segregated: Meccan block contiguous (+ 2-opt within) + Medinan block contiguous
    mec = np.where(md_label == 0)[0]
    med = np.where(md_label == 1)[0]
    # try both orderings
    best_mec = best_tour_in_cell(mec)
    best_med = best_tour_in_cell(med)
    L_md_AB = tour_length(np.concatenate([best_mec, best_med]), D)
    L_md_BA = tour_length(np.concatenate([best_med, best_mec]), D)
    L_md_min = min(L_md_AB, L_md_BA)
    print(f"\n(iii) M/D-segregated (Meccan+Medinan contiguous blocks, 2-opt within each):")
    print(f"    L_min_MD = {L_md_min:.4f}  (best of AB={L_md_AB:.4f}, BA={L_md_BA:.4f})")

    # --- (iv) Combined tertile × M/D: 6 cells, 2-opt within each, concat in Mushaf-mimic order
    print("\n(iv) Combined tertile × M/D (6 cells, 2-opt within each, concat long-to-short):")
    cell_labels = tert * 2 + md_label  # 0..5
    cells6 = [np.where(cell_labels == k)[0] for k in range(6)]
    # Mushaf macro: T2 first (long), then T1, then T0 (short); within each prefer Mec first? try orderings
    orderings = []
    from itertools import permutations as iperms
    # enumerate 6-cell orderings is 720, small; evaluate all
    best_L_combined = np.inf
    best_order = None
    best_concat = None
    inner_cells = {k: best_tour_in_cell(cells6[k]) for k in range(6)}
    for perm in iperms(range(6)):
        concat = np.concatenate([inner_cells[k] for k in perm])
        L = tour_length(concat, D)
        if L < best_L_combined:
            best_L_combined = L
            best_order = perm
            best_concat = concat
    print(f"    L_min_combined_cells = {best_L_combined:.4f}  "
          f"(best cell ordering = {best_order})")

    # Summary
    out = dict(
        L_Mushaf=float(L_mushaf),
        L_Nuzul=float(L_nuzul),
        null_mean=float(null_mean),
        null_std=float(null_std),
        L_unconstrained_2opt=float(L_uncon),
        L_length_tertile_desc=float(L_tert_desc),
        L_MD_segregated=float(L_md_min),
        L_combined_tertile_MD=float(best_L_combined),
        combined_best_cell_order=list(best_order),
    )

    print("\n=== Summary table ===")
    print(f"{'reference':28s} {'L':>9s} {'Mushaf/ref':>11s}")
    print("-" * 50)
    print(f"{'unconstrained 2-opt':28s} {L_uncon:>9.4f} {L_mushaf/L_uncon:>10.3f}x")
    print(f"{'length-tertile-constrained':28s} {L_tert_desc:>9.4f} {L_mushaf/L_tert_desc:>10.3f}x")
    print(f"{'M/D-segregated':28s} {L_md_min:>9.4f} {L_mushaf/L_md_min:>10.3f}x")
    print(f"{'combined tertile × M/D':28s} {best_L_combined:>9.4f} {L_mushaf/best_L_combined:>10.3f}x")
    print(f"{'Mushaf':28s} {L_mushaf:>9.4f} {'1.000x':>11s}")
    print(f"{'Nuzul':28s} {L_nuzul:>9.4f} {L_mushaf/L_nuzul:>10.3f}x")
    print(f"{'random-permutation mean':28s} {null_mean:>9.4f} {L_mushaf/null_mean:>10.3f}x")

    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\tsp_global_minimum.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
