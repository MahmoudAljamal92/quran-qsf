"""exp179 — F89 = F85 scaled to 10,000,000 permutations (theorem-grade escalation).

Same joint-extremality test as Avenue D (exp176), but with B = 10M instead of 100k.
Target: empirical joint p ≤ 10^-7 (from 10^-5).

Vectorised permutation generation via argsort(random_matrix) — this is ~50x
faster than a Python loop over rng.permutation and avoids GIL overhead.
"""
from __future__ import annotations
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp179_F85_escalation_10M"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
CLASSICAL_PAIR_INDICES = [1, 7, 54, 66, 72, 74, 76, 80, 82, 86, 90, 92,
                          98, 102, 104, 110, 112]

SEED = 20260502
B_TOTAL = 10_000_000
BLOCK = 20_000


def load_surahs():
    s = {i: [] for i in range(1, 115)}
    for line in DATA.read_text(encoding="utf-8").splitlines():
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        k = int(x[0])
        if 1 <= k <= 114:
            s[k].append(x[2].strip())
    return s


def main():
    print("=" * 72)
    print("exp179 — F89 = F85 extremality scaled to B = 10,000,000")
    print("=" * 72)
    t_start = time.time()

    surahs = load_surahs()
    F1 = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        all_text = "".join("".join(c for c in v if c in ARABIC_LETTERS_SET)
                           for v in surahs[i])
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

    # Mushaf stats
    consec = np.linalg.norm(np.diff(F1_det, axis=0), axis=1)
    L_mushaf = float(consec.sum())
    mean_cl_m = float(consec[CLASSICAL_PAIR_INDICES].mean())
    nonclass_idx = np.array([i for i in range(113) if i not in CLASSICAL_PAIR_INDICES])
    mean_nc_m = float(consec[nonclass_idx].mean())
    diff_m = mean_cl_m - mean_nc_m
    print(f"\n# Mushaf stats (locked from F81 data):")
    print(f"  L              = {L_mushaf:.6f}")
    print(f"  mean_classical = {mean_cl_m:.6f}")
    print(f"  mean_non_class = {mean_nc_m:.6f}")
    print(f"  diff           = {diff_m:+.6f}")

    rng = np.random.default_rng(SEED)
    classical_idx = np.array(CLASSICAL_PAIR_INDICES)

    n_beat_L = 0
    n_beat_diff = 0
    n_beat_both = 0

    # Streaming quantile tracker: sample every 100th permutation for quantile estimation
    sample_L = []
    sample_diff = []

    print(f"\n# Running vectorised permutation sweep, B = {B_TOTAL:,} ...")
    t0 = time.time()
    for start in range(0, B_TOTAL, BLOCK):
        size = min(BLOCK, B_TOTAL - start)
        # Vectorised permutation generation
        perms = np.argsort(rng.random((size, 114), dtype=np.float32), axis=1).astype(np.int32)
        a = perms[:, :-1]
        b_ = perms[:, 1:]
        consec_perm = D[a, b_]  # (size, 113)
        L_p = consec_perm.sum(axis=1)
        mean_cl_p = consec_perm[:, classical_idx].mean(axis=1)
        mean_nc_p = consec_perm[:, nonclass_idx].mean(axis=1)
        diff_p = mean_cl_p - mean_nc_p

        n_beat_L += int(np.sum(L_p <= L_mushaf))
        n_beat_diff += int(np.sum(diff_p >= diff_m))
        n_beat_both += int(np.sum((L_p <= L_mushaf) & (diff_p >= diff_m)))

        # sparse sampling for quantiles
        sample_L.append(L_p[::100].copy())
        sample_diff.append(diff_p[::100].copy())

        if (start + BLOCK) % 500_000 == 0:
            elapsed = time.time() - t0
            rate = (start + BLOCK) / elapsed
            eta = (B_TOTAL - start - BLOCK) / rate
            print(f"  {start + BLOCK:>10,}/{B_TOTAL:,}  "
                  f"beats_L={n_beat_L}  beats_diff={n_beat_diff}  "
                  f"beats_both={n_beat_both}  "
                  f"rate={rate/1000:.1f}k/s  ETA={eta:.0f}s")

    elapsed = time.time() - t0
    print(f"\n  ... done in {elapsed:.1f} s ({B_TOTAL/elapsed/1000:.1f}k perms/s)")

    sample_L = np.concatenate(sample_L)
    sample_diff = np.concatenate(sample_diff)

    L_mean = float(sample_L.mean())
    L_std = float(sample_L.std())
    diff_mean = float(sample_diff.mean())
    diff_std = float(sample_diff.std())
    z_L = (L_mushaf - L_mean) / L_std
    z_diff = (diff_m - diff_mean) / diff_std

    print(f"\n=== Joint extremality results (B = {B_TOTAL:,}) ===")
    print(f"  L   null mean ± std (sample): {L_mean:.4f} ± {L_std:.4f}")
    print(f"  diff null mean ± std (sample): {diff_mean:+.5f} ± {diff_std:.4f}")
    print(f"  z_L    = {z_L:+.3f}")
    print(f"  z_diff = {z_diff:+.3f}")
    print()
    print(f"  Beats on F81 (L ≤ Mushaf):                    {n_beat_L:>10,} / {B_TOTAL:,}  (p = {(n_beat_L+1)/(B_TOTAL+1):.5g})")
    print(f"  Beats on F82 (diff ≥ Mushaf):                 {n_beat_diff:>10,} / {B_TOTAL:,}  (p = {(n_beat_diff+1)/(B_TOTAL+1):.5g})")
    print(f"  Beats on BOTH simultaneously:                 {n_beat_both:>10,} / {B_TOTAL:,}  (p = {(n_beat_both+1)/(B_TOTAL+1):.5g})")
    print()
    expected_joint_indep = (n_beat_L / B_TOTAL) * (n_beat_diff / B_TOTAL) * B_TOTAL
    print(f"  Expected joint count under independence: {expected_joint_indep:.4f}")

    if n_beat_both == 0:
        print(f"\n  >>> EMPIRICAL JOINT EXTREMUM: 0 of {B_TOTAL:,} permutations match Mushaf jointly <<<")
        print(f"  >>> Empirical p ≤ 1/{B_TOTAL:,} = {1/B_TOTAL:.2e} <<<")

    # Receipt
    out = dict(
        experiment="exp179_F85_escalation_10M",
        finding_id="F89",
        seed=SEED,
        B=B_TOTAL,
        L_mushaf=L_mushaf,
        diff_mushaf=diff_m,
        L_null_mean_sample=L_mean,
        L_null_std_sample=L_std,
        diff_null_mean_sample=diff_mean,
        diff_null_std_sample=diff_std,
        z_L=float(z_L),
        z_diff=float(z_diff),
        n_beat_L=int(n_beat_L),
        n_beat_diff=int(n_beat_diff),
        n_beat_both=int(n_beat_both),
        p_L=(n_beat_L + 1) / (B_TOTAL + 1),
        p_diff=(n_beat_diff + 1) / (B_TOTAL + 1),
        p_joint=(n_beat_both + 1) / (B_TOTAL + 1),
        expected_joint_under_independence=float(expected_joint_indep),
        wall_time_s=time.time() - t_start,
        comparison_to_F85_at_100k=dict(
            F85_B=100_000,
            F85_n_beat_both=0,
            F85_p_joint="≤ 1e-5",
            F89_B=B_TOTAL,
            F89_p_joint=f"≤ {1/B_TOTAL:.2e}" if n_beat_both == 0 else f"≈ {(n_beat_both+1)/(B_TOTAL+1):.2e}",
            escalation_gain=f"{B_TOTAL / 100_000:.0f}x more permutations",
        ),
    )
    out_path = OUT_DIR / "exp179_F85_escalation_10M.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
