"""exp176 Avenue C — Multi-scale invariance.

Tests whether the project's existing universal regularities hold at
multiple scales WITHIN the Quran:

(1) F75 universal:  H_EL + log₂(p_max · A) ≈ 5.75 bits
    Cross-corpus CV = 1.94 %.
    Test: does this also hold for individual surahs of the Quran?

(2) F76 categorical:  H_EL < 1 bit
    Test: does this also hold per-surah?

(3) F67 C_Ω = 1 - H_EL/log₂(A) ≈ 0.7985
    Test: does this also hold per-surah / per-juzʾ?

(4) F81/F82 dual-mode signature
    Test: does the same dual-mode appear at the within-block level?

Universal-grade requires the F75 quantity to be constant across BOTH
cross-tradition corpora (already proven at 1.94% CV) AND across
individual surahs (target: CV < 10%, ideally < 5%).
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
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
A = 28  # Arabic alphabet size used uniformly in F75


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


def verse_final_letter(verse):
    rev = [c for c in reversed(verse) if c in ARABIC_LETTERS_SET]
    return rev[0] if rev else None


def shannon_H(p, base=2):
    p = np.asarray(p, float)
    p = p[p > 0]
    return float(-np.sum(p * np.log(p) / np.log(base)))


def main():
    surahs = load_surahs()
    n_surah_total = len(surahs)
    print(f"# Avenue C: multi-scale invariance test")
    print(f"# Quran: {n_surah_total} surahs total\n")

    # ---- Test (1)+(2)+(3): per-surah end-letter distribution stats ----
    rows = []
    skipped = []
    for i in range(1, 115):
        finals = [verse_final_letter(v) for v in surahs[i]]
        finals = [f for f in finals if f is not None]
        n_v = len(finals)
        if n_v < 5:
            skipped.append((i, n_v))
            continue
        counts = Counter(finals)
        probs = np.array([counts.get(c, 0) / n_v for c in ARABIC_LETTERS])
        H_EL = shannon_H(probs, base=2)
        p_max = float(probs.max())
        if p_max <= 0:
            continue
        F75 = H_EL + np.log2(p_max * A)
        F67_COmega = 1.0 - H_EL / np.log2(A)
        rows.append((i, n_v, H_EL, p_max, F75, F67_COmega))

    arr = np.array([(r[2], r[3], r[4], r[5]) for r in rows])
    H_EL_vals = arr[:, 0]
    p_max_vals = arr[:, 1]
    F75_vals = arr[:, 2]
    F67_vals = arr[:, 3]
    n_used = len(rows)
    print(f"# Per-surah analysis: {n_used} surahs used "
          f"({len(skipped)} skipped: surah_id, n_verses)")
    if skipped:
        print(f"#  skipped: {skipped[:10]}{'...' if len(skipped)>10 else ''}")
    print()

    # F75 invariance
    print("(1) F75 quantity  H_EL + log₂(p_max · A)")
    print(f"    Per-surah mean = {F75_vals.mean():.4f}")
    print(f"    Per-surah std  = {F75_vals.std():.4f}")
    print(f"    Per-surah CV   = {F75_vals.std() / F75_vals.mean() * 100:.2f} %")
    print(f"    Cross-tradition reference (F75): mean = 5.75 bits, CV = 1.94 %")
    print(f"    Range: [{F75_vals.min():.3f}, {F75_vals.max():.3f}]")
    # Tier criterion: per-surah mean within ±0.5 of cross-tradition 5.75; CV < 10%
    f75_mean_ok = abs(F75_vals.mean() - 5.75) < 0.5
    f75_cv_ok = F75_vals.std() / F75_vals.mean() * 100 < 10.0
    print(f"    [tier check] mean within ±0.5 of 5.75: {f75_mean_ok}")
    print(f"    [tier check] CV < 10%: {f75_cv_ok}")
    print()

    # F76 categorical: H_EL < 1 bit per-surah?
    print("(2) F76 categorical: H_EL < 1 bit")
    n_below = int(np.sum(H_EL_vals < 1.0))
    print(f"    Surahs with H_EL < 1: {n_below} / {n_used} = {n_below/n_used*100:.1f} %")
    print(f"    H_EL mean = {H_EL_vals.mean():.4f}, std = {H_EL_vals.std():.4f}")
    print(f"    Per-surah H_EL range: [{H_EL_vals.min():.3f}, {H_EL_vals.max():.3f}]")
    print()

    # F67 C_Ω
    print("(3) F67 C_Ω = 1 - H_EL/log₂(28)")
    print(f"    Per-surah mean = {F67_vals.mean():.4f}")
    print(f"    Per-surah std  = {F67_vals.std():.4f}")
    print(f"    Per-surah CV   = {F67_vals.std() / F67_vals.mean() * 100:.2f} %")
    print(f"    Full-Quran reference (F67): C_Ω = 0.7985")
    print(f"    Cross-tradition rank-2 (Rigveda): C_Ω = 0.5881")
    n_above_runner_up = int(np.sum(F67_vals > 0.5881))
    print(f"    Per-surah C_Ω > 0.5881 (above cross-tradition rank-2): {n_above_runner_up}/{n_used} = {n_above_runner_up/n_used*100:.1f} %")
    print()

    # ---- F75 sub-segments: juzʾ-level approximation by 30 contiguous chunks ----
    # The Quran has 30 juzʾ; we approximate by partitioning the 114 surahs
    # by cumulative-letter-count into 30 ~equal letter-count segments.
    print("# Juzʾ-scale (30 ≈-equal segments by letter count):")
    # Compute total Arabic-letter count per surah
    sl = np.zeros(114, dtype=int)
    for i in range(1, 115):
        for v in surahs[i]:
            sl[i - 1] += sum(1 for c in v if c in ARABIC_LETTERS_SET)
    total = sl.sum()
    target = total / 30.0
    bounds = [0]
    cum = 0
    for i in range(114):
        cum += sl[i]
        if cum >= target * (len(bounds)) and len(bounds) < 30:
            bounds.append(i + 1)
    bounds.append(114)
    # 30 segments from `bounds[k]` to `bounds[k+1]` (surah indices 0..113)
    # Compute F75 per segment
    seg_F75 = []
    seg_H = []
    seg_C = []
    for s_start, s_end in zip(bounds[:-1], bounds[1:]):
        finals = []
        for k in range(s_start, s_end):
            finals.extend(verse_final_letter(v) for v in surahs[k + 1])
        finals = [f for f in finals if f is not None]
        if len(finals) < 5:
            continue
        counts = Counter(finals)
        probs = np.array([counts.get(c, 0) / len(finals) for c in ARABIC_LETTERS])
        H = shannon_H(probs)
        pm = probs.max()
        if pm <= 0:
            continue
        seg_F75.append(H + np.log2(pm * A))
        seg_H.append(H)
        seg_C.append(1 - H / np.log2(A))
    seg_F75 = np.array(seg_F75)
    seg_H = np.array(seg_H)
    seg_C = np.array(seg_C)
    print(f"  Number of valid juzʾ-scale segments: {len(seg_F75)}")
    print(f"  F75 segments: mean = {seg_F75.mean():.4f}, std = {seg_F75.std():.4f}, "
          f"CV = {seg_F75.std()/seg_F75.mean()*100:.2f} %")
    print(f"  H_EL segments: mean = {seg_H.mean():.4f}, std = {seg_H.std():.4f}")
    print(f"  C_Ω segments: mean = {seg_C.mean():.4f}, std = {seg_C.std():.4f}")
    print()

    # ---- (4) Cross-scale comparison summary ----
    print("=== Multi-scale F75 invariance summary ===")
    print(f"  Scale 1 (cross-tradition, 11 corpora): mean = 5.75, CV = 1.94 % [F75 locked]")
    print(f"  Scale 2 (cross-tradition, 12 corpora w/ Rigveda): see F75 row")
    print(f"  Scale 3 (Quran 30 juzʾ-segments):    mean = {seg_F75.mean():.4f}, CV = {seg_F75.std()/seg_F75.mean()*100:.2f} %")
    print(f"  Scale 4 (Quran 114 surahs, ≥5 v):    mean = {F75_vals.mean():.4f}, CV = {F75_vals.std()/F75_vals.mean()*100:.2f} %")
    print()
    # Tier verdict
    universal_grade = (f75_mean_ok and (F75_vals.std() / F75_vals.mean() * 100 < 5))
    if universal_grade:
        print("  >>> UNIVERSAL_GRADE_F75: per-surah within ±0.5 of cross-tradition mean AND CV < 5% <<<")
    elif f75_cv_ok:
        print("  >>> SCALE_INVARIANT_F75: per-surah within reasonable bounds (CV < 10%) <<<")
    else:
        print("  >>> NOT scale-invariant — per-surah CV exceeds 10% <<<")
    print()

    # ---- F82 dual-mode at additional scales ----
    # Test: do the four classical macro-blocks (ṭiwāl/miʾīn/mathānī/mufaṣṣal)
    # themselves show coherence-vs-contrast? Compute the inter-block
    # distance (block centroid to block centroid) and the within-block
    # spread, see if they are anti-correlated.
    print("# F81/F82 multi-scale: block-centroid vs within-block spread analysis")
    blocks = {
        "tiwāl": list(range(2, 10)),
        "miʾīn": list(range(10, 36)),
        "mathānī": list(range(36, 50)),
        "mufaṣṣal": list(range(50, 115)),
    }
    # Compute F1 letter freq per surah and detrend
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
    MEDINAN = {2,3,4,5,8,9,22,24,33,47,48,49,55,57,58,59,60,61,62,63,64,65,66,76,98,99,110}
    md = np.array([1 if (i+1) in MEDINAN else 0 for i in range(114)])
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    F1_det = np.zeros_like(F1)
    for k in range(28):
        b = np.linalg.lstsq(X, F1[:, k], rcond=None)[0]
        F1_det[:, k] = F1[:, k] - X @ b

    centroids = {}
    spreads = {}
    for bname, sl in blocks.items():
        idx = np.array([s - 1 for s in sl])
        centroids[bname] = F1_det[idx].mean(axis=0)
        spreads[bname] = float(np.linalg.norm(F1_det[idx] - centroids[bname], axis=1).mean())
    bnames = list(blocks.keys())
    print(f"  Block centroid distances:")
    for i, b1 in enumerate(bnames):
        for b2 in bnames[i+1:]:
            d = float(np.linalg.norm(centroids[b1] - centroids[b2]))
            print(f"    d({b1},{b2}) = {d:.4f}")
    print(f"  Within-block mean radius (spread):")
    for b in bnames:
        print(f"    {b}: {spreads[b]:.4f}")

    out = dict(
        n_surah_used=n_used,
        F75_per_surah=dict(mean=float(F75_vals.mean()),
                            std=float(F75_vals.std()),
                            cv_pct=float(F75_vals.std() / F75_vals.mean() * 100),
                            min=float(F75_vals.min()),
                            max=float(F75_vals.max())),
        F75_per_juz=dict(mean=float(seg_F75.mean()),
                          std=float(seg_F75.std()),
                          cv_pct=float(seg_F75.std() / seg_F75.mean() * 100),
                          n_segments=len(seg_F75)),
        H_EL_per_surah=dict(mean=float(H_EL_vals.mean()),
                             below_1bit_count=n_below,
                             total=n_used),
        F67_per_surah=dict(mean=float(F67_vals.mean()),
                            std=float(F67_vals.std()),
                            cv_pct=float(F67_vals.std() / F67_vals.mean() * 100),
                            above_runner_up_count=n_above_runner_up,
                            total=n_used),
        block_centroids={k: v.tolist() for k, v in centroids.items()},
        block_spreads=spreads,
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\avenue_C_multiscale.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
