"""exp176 Avenue D — Joint extremality (theorem-grade attempt).

Define a joint score
    J(perm) := −z_F81(perm) + λ * z_F82_diff(perm)
where:
    z_F81 = (L(perm) - μ_perm) / σ_perm                      (more negative = more coherent)
    z_F82_diff = mean(d at classical-pair positions)
                 − mean(d at non-classical-pair positions)   (positive = contrast at pairs)

Hypothesis (Mushaf-extremality): of 100,000 random permutations of the
114 surahs, NONE simultaneously achieve  z_F81 ≤ −5  AND  z_F82_diff ≥ +0.022.
If 0 permutations beat Mushaf jointly, this is empirical extremality
at empirical p ≤ 1/100,000.

Note: under random permutation, the *positions* (classical-pair slots)
in the permuted sequence carry random surah identities. So the test is:
treating the 17 classical positions as a fixed slot set in Mushaf-order,
permute the 114 surahs and recompute both stats with the permuted
content placed at those slots.

This is the cleanest form of extremality test: holding the question
'are you simultaneously low-distance overall AND high-distance at
the maqrūnāt slots' constant, what fraction of orderings beat Mushaf?
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
# pair index i = (surah_{i+1}, surah_{i+2}); i.e., 0-indexed adjacency

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

    # Mushaf statistics
    consec = np.linalg.norm(np.diff(F1_det, axis=0), axis=1)
    L_mushaf = float(consec.sum())
    mean_classical_mushaf = float(consec[CLASSICAL_PAIR_INDICES].mean())
    nonclass_idx = [i for i in range(113) if i not in CLASSICAL_PAIR_INDICES]
    mean_nonclass_mushaf = float(consec[nonclass_idx].mean())
    diff_mushaf = mean_classical_mushaf - mean_nonclass_mushaf
    print(f"# Mushaf:")
    print(f"  L = {L_mushaf:.4f}")
    print(f"  classical-mean d = {mean_classical_mushaf:.4f}")
    print(f"  non-classical-mean d = {mean_nonclass_mushaf:.4f}")
    print(f"  diff = {diff_mushaf:+.4f}")
    print()

    # ----- Joint-extremality null: B = 100,000 permutations ----
    B = 100_000
    rng = np.random.default_rng(20260501)
    print(f"# Running joint-extremality test, B = {B} random permutations of 114 surahs...")
    t0 = time.time()

    # Precompute pairwise distance matrix
    D = np.linalg.norm(F1_det[:, None, :] - F1_det[None, :, :], axis=-1)

    # Vectorise: for each permutation, compute consec distances and the two
    # subset means + total L.
    n_beat_L = 0
    n_beat_diff = 0
    n_beat_both = 0
    L_nulls = np.empty(B)
    diff_nulls = np.empty(B)

    classical_idx = np.array(CLASSICAL_PAIR_INDICES)
    nonclass_arr = np.array(nonclass_idx)

    block = 5000
    for start in range(0, B, block):
        end = min(start + block, B)
        size = end - start
        # Generate `size` random permutations of 114
        perms = np.array([rng.permutation(114) for _ in range(size)], dtype=np.int32)
        # Adjacent pair indices: perms[:, :-1], perms[:, 1:]
        a = perms[:, :-1]
        b_ = perms[:, 1:]
        consec_perm = D[a, b_]  # shape (size, 113)
        L_p = consec_perm.sum(axis=1)
        mean_class_p = consec_perm[:, classical_idx].mean(axis=1)
        mean_nonclass_p = consec_perm[:, nonclass_arr].mean(axis=1)
        diff_p = mean_class_p - mean_nonclass_p

        L_nulls[start:end] = L_p
        diff_nulls[start:end] = diff_p

        n_beat_L += int(np.sum(L_p <= L_mushaf))
        n_beat_diff += int(np.sum(diff_p >= diff_mushaf))
        n_beat_both += int(np.sum((L_p <= L_mushaf) & (diff_p >= diff_mushaf)))

    elapsed = time.time() - t0
    print(f"  ... done in {elapsed:.1f} s\n")

    # Results
    print("=== Joint-extremality results (B = 100,000) ===")
    z_L = (L_mushaf - L_nulls.mean()) / L_nulls.std()
    z_diff = (diff_mushaf - diff_nulls.mean()) / diff_nulls.std()
    print(f"  L_mushaf = {L_mushaf:.4f}, null = {L_nulls.mean():.4f} ± {L_nulls.std():.4f}, z = {z_L:+.3f}")
    print(f"  diff_mushaf = {diff_mushaf:+.4f}, null = {diff_nulls.mean():+.5f} ± {diff_nulls.std():.4f}, z = {z_diff:+.3f}")
    print()
    print(f"  Beats on F81 (L ≤ Mushaf):                    {n_beat_L:>7d} / {B}  (p = {(n_beat_L+1)/(B+1):.5g})")
    print(f"  Beats on F82 (diff ≥ Mushaf):                 {n_beat_diff:>7d} / {B}  (p = {(n_beat_diff+1)/(B+1):.5g})")
    print(f"  Beats on BOTH simultaneously:                 {n_beat_both:>7d} / {B}  (p = {(n_beat_both+1)/(B+1):.5g})")
    print()
    if n_beat_both == 0:
        print(f"  >>> EMPIRICAL JOINT EXTREMUM: 0 of {B} permutations simultaneously match or exceed Mushaf <<<")
    else:
        print(f"  >>> {n_beat_both} permutations match Mushaf jointly; not unique extremum at this B <<<")

    # Independence test: under pure independence between F81 and F82 channels,
    # E[joint] = (n_beat_L / B) * (n_beat_diff / B) * B
    expected_joint_indep = (n_beat_L / B) * (n_beat_diff / B) * B
    print(f"  Expected joint count under independence: {expected_joint_indep:.4f}")
    if n_beat_both == 0 and expected_joint_indep < 1:
        print(f"  Independence-consistent: joint events are simply too rare under both individual rates")
    elif n_beat_both > 0 and abs(n_beat_both - expected_joint_indep) < 5 * np.sqrt(expected_joint_indep + 1):
        print(f"  Joint count consistent with INDEPENDENT-channel null at ±5σ Poisson")
    print()

    # Save quantile structure
    print("# F81 / F82 joint distribution structure (top quantiles of perm distribution):")
    L_q = np.quantile(L_nulls, [0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999])
    diff_q = np.quantile(diff_nulls, [0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999])
    print(f"  L quantiles (0.1%, 1%, 5%, 50%, 95%, 99%, 99.9%):    {[f'{x:.4f}' for x in L_q]}")
    print(f"  diff quantiles (0.1%, 1%, 5%, 50%, 95%, 99%, 99.9%):  {[f'{x:+.4f}' for x in diff_q]}")
    print(f"  Mushaf L = {L_mushaf:.4f} → quantile pos = {(L_nulls <= L_mushaf).sum()/B*100:.4f} %")
    print(f"  Mushaf diff = {diff_mushaf:+.4f} → quantile pos = {(diff_nulls <= diff_mushaf).sum()/B*100:.4f} %")

    out = dict(
        B=B,
        L_mushaf=L_mushaf,
        diff_mushaf=diff_mushaf,
        z_L=float(z_L),
        z_diff=float(z_diff),
        n_beat_L=n_beat_L,
        n_beat_diff=n_beat_diff,
        n_beat_both=n_beat_both,
        p_joint_empirical=float((n_beat_both + 1) / (B + 1)),
        expected_joint_under_independence=float(expected_joint_indep),
        L_null_mean=float(L_nulls.mean()),
        L_null_std=float(L_nulls.std()),
        diff_null_mean=float(diff_nulls.mean()),
        diff_null_std=float(diff_nulls.std()),
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\avenue_D_extremality.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
