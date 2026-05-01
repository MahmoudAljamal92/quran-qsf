"""exp176 Avenue E — Closed-form ceiling and derivational structure.

Question: how close does Mushaf get to the THEORETICAL MAXIMUM of the
joint F81+F82 metric, given the fixed 114-surah feature multiset?

Three derivations:

(D1) F81 lower bound (combinatorial):
     L_min over all 114! orderings ≥ minimum-weight Hamiltonian path
     on the 114-vertex pairwise-distance complete graph. Held-Karp is
     O(2^N * N^2) = infeasible for N=114, but a tight LP relaxation
     and a 2-opt approximation give us the practical lower bound.

(D2) F82 upper bound (combinatorial):
     For a fixed total of 113 adjacencies and a fixed 17-pair classical
     subset, the maximum possible (mean_class − mean_nonclass) is
     bounded by the gap between the 17 largest possible inter-surah
     distances and the 96 smallest. We can compute this analytically.

(D3) Joint ceiling:
     Even tighter — the tour structure constrains adjacencies to be
     a Hamiltonian path. The 17 classical-pair POSITIONS are fixed
     by Mushaf order; we can permute the 114 surah identities only.
     Compute the maximum classical-pair-contrast achievable subject
     to fixing the tour positions of classical pairs.

Honest scientific question: how close does Mushaf get to (D1) and (D2)?
If Mushaf achieves > 90 % of the achievable F82 contrast under the
"non-pair-positions stay below median" constraint, that's strong
derivational evidence the editor was OPTIMIZING this dual rule.
"""
from __future__ import annotations
import io
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
CLASSICAL_PAIR_INDICES = [1, 7, 54, 66, 72, 74, 76, 80, 82, 86, 90, 92,
                          98, 102, 104, 110, 112]


def load_surahs():
    p = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    s = {i: [] for i in range(1, 115)}
    for line in p.read_text(encoding="utf-8").splitlines():
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        k = int(x[0])
        if 1 <= k <= 114:
            s[k].append(x[2].strip())
    return s


def main():
    surahs = load_surahs()
    F1 = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        all_text = "".join("".join(c for c in v if c in ARABIC_LETTERS_SET) for v in surahs[i])
        n = len(all_text)
        Nlet[i - 1] = n
        if n > 0:
            counts = Counter(all_text)
            F1[i - 1] = np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS])
    logN = np.log(Nlet)
    md = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    F1_det = np.zeros_like(F1)
    for k in range(28):
        b = np.linalg.lstsq(X, F1[:, k], rcond=None)[0]
        F1_det[:, k] = F1[:, k] - X @ b

    D = np.linalg.norm(F1_det[:, None, :] - F1_det[None, :, :], axis=-1)
    consec = np.linalg.norm(np.diff(F1_det, axis=0), axis=1)

    L_mushaf = float(consec.sum())
    classical_mean = float(consec[CLASSICAL_PAIR_INDICES].mean())
    nonclass_idx = [i for i in range(113) if i not in CLASSICAL_PAIR_INDICES]
    nonclass_mean = float(consec[nonclass_idx].mean())
    diff_mushaf = classical_mean - nonclass_mean

    print("=== AVENUE E: Closed-form ceiling derivation ===\n")
    print(f"# Mushaf observed:")
    print(f"  L_F81 = {L_mushaf:.4f}")
    print(f"  classical mean d = {classical_mean:.4f}")
    print(f"  non-classical mean d = {nonclass_mean:.4f}")
    print(f"  diff = {diff_mushaf:+.4f}")
    print()

    # ---------- D1: F81 ceiling = minimum Hamiltonian path length ----------
    print("# (D1) F81 lower bound — minimum Hamiltonian path:")
    # Multi-start 2-opt optimization (many restarts for tightness)
    iu = np.triu_indices(114, k=1)
    all_pw = D[iu]
    # Combinatorial lower bound: sum of 113 smallest pairwise distances
    # in any Hamiltonian path is bounded below by the sum of 113 smallest
    # weights ASSIGNED TO A SPANNING PATH, but min spanning tree = 113 edges
    # gives a clean lower bound.
    # Compute MST via Prim's algorithm
    n = 114
    in_tree = np.zeros(n, dtype=bool)
    in_tree[0] = True
    min_d = D[0].copy()
    min_d[0] = np.inf
    mst_total = 0.0
    mst_edges = []
    for _ in range(n - 1):
        v = int(np.argmin(min_d))
        mst_total += float(min_d[v])
        in_tree[v] = True
        mst_edges.append((v, float(min_d[v])))
        for u in range(n):
            if not in_tree[u] and D[v, u] < min_d[u]:
                min_d[u] = D[v, u]
        min_d[in_tree] = np.inf
    mst_lower_bound = mst_total
    print(f"  MST lower bound (Hamiltonian path ≥ MST): {mst_lower_bound:.4f}")

    # Practical upper bound on optimum: best of many 2-opt restarts
    best_L = np.inf
    rng = np.random.default_rng(42)
    print(f"  Running 50-restart 2-opt for tighter F81 ceiling...")
    t0 = time.time()
    for r in range(50):
        if r < 30:
            # Greedy NN starting from each surah
            start = r % n
            visited = [start]
            used = {start}
            cur = start
            while len(visited) < n:
                cands = [(D[cur, j], j) for j in range(n) if j not in used]
                _, j = min(cands)
                visited.append(j)
                used.add(j)
                cur = j
            t = np.array(visited)
        else:
            t = rng.permutation(n)
        # 2-opt
        tour = t.copy()
        improved = True
        while improved:
            improved = False
            for i in range(n - 2):
                for j in range(i + 2, n):
                    a_, b_ = tour[i], tour[i + 1]
                    c_ = tour[j]
                    d_ = tour[j + 1] if j + 1 < n else None
                    if d_ is None:
                        delta = D[a_, c_] - D[a_, b_]
                    else:
                        delta = D[a_, c_] + D[b_, d_] - D[a_, b_] - D[c_, d_]
                    if delta < -1e-12:
                        if d_ is None:
                            tour = np.concatenate([tour[:i + 1], tour[j:i:-1]])
                        else:
                            tour = np.concatenate([tour[:i + 1], tour[j:i:-1], tour[j + 1:]])
                        improved = True
                        break
                if improved:
                    break
        L = float(np.sum(D[tour[:-1], tour[1:]]))
        if L < best_L:
            best_L = L
    elapsed = time.time() - t0
    print(f"  Best 2-opt path L = {best_L:.4f}  ({elapsed:.1f} s, 50 restarts)")
    print(f"  F81 ceiling band: [{mst_lower_bound:.4f}, {best_L:.4f}]")
    print(f"  Mushaf L = {L_mushaf:.4f}")
    print(f"  Mushaf efficiency vs MST lower bound: {mst_lower_bound / L_mushaf * 100:.1f} %")
    print(f"  Mushaf efficiency vs 2-opt minimum: {best_L / L_mushaf * 100:.1f} %")
    print(f"  Mushaf above 2-opt minimum by: {(L_mushaf / best_L - 1) * 100:.1f} %")
    print()

    # ---------- D2: F82 ceiling — maximum diff-of-means ----------
    print("# (D2) F82 ceiling — maximum classical/non-classical contrast:")
    # The 113 adjacent distances in any tour are a subset of size 113 of
    # the 6,441 inter-surah distances, constrained to form a Hamiltonian path.
    # The MAX |mean_class − mean_nonclass| over tour space is hard to compute
    # exactly. But we can compute the *unconstrained* upper bound:
    # if we could freely choose which 17 of the 113 chosen pairs are
    # classical, the maximum diff = (mean of top-17 distances) − (mean of bottom-96).
    # This gives the absolute information-theoretic ceiling.
    # Mushaf's tour adjacency-distances:
    sorted_consec = np.sort(consec)
    max_class_mean_in_tour = sorted_consec[-17:].mean()
    min_nonclass_mean_in_tour = sorted_consec[:96].mean()
    ceiling_within_tour = max_class_mean_in_tour - min_nonclass_mean_in_tour
    print(f"  Within Mushaf-tour 113 distances:")
    print(f"    Max attainable diff (top-17 mean − bottom-96 mean): {ceiling_within_tour:.4f}")
    print(f"    Mushaf observed diff: {diff_mushaf:+.4f}")
    print(f"    Ratio Mushaf/ceiling: {diff_mushaf / ceiling_within_tour:.3f}")
    print()
    # Across all 6441 inter-surah pairs
    sorted_all = np.sort(all_pw)
    max_class_mean_all = sorted_all[-17:].mean()
    min_nonclass_mean_all = sorted_all[:96].mean()
    ceiling_all = max_class_mean_all - min_nonclass_mean_all
    print(f"  Across all 6,441 inter-surah pairs (theoretical maximum, no Hamiltonian constraint):")
    print(f"    Max attainable diff: {ceiling_all:.4f}")
    print(f"    Mushaf observed: {diff_mushaf:+.4f}")
    print(f"    Ratio Mushaf/ceiling: {diff_mushaf / ceiling_all:.3f}")
    print()

    # ---------- D3: Joint ceiling under tour constraint ----------
    print("# (D3) Joint ceiling — best simultaneous F81/F82 within tour space:")
    # Pareto front exploration: random 100,000 tours and find the Pareto front
    print(f"  Sampling 100,000 random tours to find Pareto front...")
    t0 = time.time()
    pareto_pts = []
    rng = np.random.default_rng(20260501)
    B = 100_000
    block = 5000
    L_grid = []
    diff_grid = []
    for start in range(0, B, block):
        end = min(start + block, B)
        size = end - start
        perms = np.array([rng.permutation(114) for _ in range(size)], dtype=np.int32)
        a = perms[:, :-1]
        b_ = perms[:, 1:]
        consec_perm = D[a, b_]
        L_p = consec_perm.sum(axis=1)
        cls = consec_perm[:, CLASSICAL_PAIR_INDICES].mean(axis=1)
        nc = np.delete(consec_perm, CLASSICAL_PAIR_INDICES, axis=1).mean(axis=1)
        diff_p = cls - nc
        L_grid.append(L_p)
        diff_grid.append(diff_p)
    L_grid = np.concatenate(L_grid)
    diff_grid = np.concatenate(diff_grid)
    print(f"  ... done in {time.time()-t0:.1f} s")
    print()

    # Pareto: minimize L AND maximize diff
    # Find the Pareto front (non-dominated points)
    # Add Mushaf point
    L_all = np.concatenate([L_grid, [L_mushaf]])
    diff_all = np.concatenate([diff_grid, [diff_mushaf]])
    # Sort by L ascending; sweep
    order = np.argsort(L_all)
    pareto_mask = np.zeros(len(L_all), dtype=bool)
    best_diff_so_far = -np.inf
    pareto_idx = []
    for k in order:
        if diff_all[k] > best_diff_so_far:
            pareto_mask[k] = True
            best_diff_so_far = diff_all[k]
            pareto_idx.append(k)
    n_pareto = pareto_mask.sum()
    is_mushaf_pareto = pareto_mask[-1]
    print(f"  Pareto front size (lower L AND higher diff is better): {n_pareto}")
    print(f"  Is Mushaf on the Pareto front? {is_mushaf_pareto}")
    if is_mushaf_pareto:
        # find rank in pareto front
        pareto_L = L_all[pareto_mask]
        pareto_diff = diff_all[pareto_mask]
        # Mushaf is the lowest L on pareto?
        rank_L = int((pareto_L < L_mushaf).sum())
        rank_diff = int((pareto_diff > diff_mushaf).sum())
        print(f"  Mushaf rank on Pareto front by L (lower better): {rank_L} of {n_pareto}")
        print(f"  Mushaf rank on Pareto front by diff (higher better): {rank_diff} of {n_pareto}")
        if rank_L == 0:
            print(f"  >>> Mushaf has the LOWEST L on the entire Pareto front <<<")
        if rank_diff == 0:
            print(f"  >>> Mushaf has the HIGHEST diff on the entire Pareto front <<<")
    print()
    # How many random tours STRICTLY DOMINATE Mushaf?
    dom_mask = (L_grid < L_mushaf) & (diff_grid > diff_mushaf)
    n_dom = int(dom_mask.sum())
    print(f"  Random tours that strictly dominate Mushaf (lower L AND higher diff): {n_dom} / {B}")
    print(f"  Mushaf empirical Pareto-extremum p ≤ {(n_dom + 1) / (B + 1):.5g}")

    out = dict(
        L_mushaf=L_mushaf,
        diff_mushaf=diff_mushaf,
        D1_MST_lower_bound=float(mst_lower_bound),
        D1_2opt_upper_bound=float(best_L),
        D1_efficiency_vs_2opt_pct=float(best_L / L_mushaf * 100),
        D1_above_2opt_pct=float((L_mushaf / best_L - 1) * 100),
        D2_ceiling_within_tour_distances=float(ceiling_within_tour),
        D2_ceiling_across_all_pairs=float(ceiling_all),
        D2_mushaf_to_within_tour_ratio=float(diff_mushaf / ceiling_within_tour),
        D2_mushaf_to_global_ratio=float(diff_mushaf / ceiling_all),
        D3_pareto_front_size=int(n_pareto),
        D3_is_mushaf_on_pareto=bool(is_mushaf_pareto),
        D3_n_strictly_dominate=int(n_dom),
        D3_p_empirical_pareto=float((n_dom + 1) / (B + 1)),
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\avenue_E_ceiling.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
