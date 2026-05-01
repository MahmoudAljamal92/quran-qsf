"""exp172_saj_rhyme — intrinsic test of verse-end rhyme (fasilah)
structure in the canonical Hafs Mushaf. 6,236 verses, 7-class rhyme
scheme, 5 statistics vs shuffle null.

Operating principle: Quran is the reference. No external corpora.
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

# Rhyme class scheme (7 classes) ────────────────────────────────────
LONG_VOWEL = set("\u0627\u0648\u064A\u0649\u0671\u0622")       # ا و ي ى ٱ آ
NASAL      = set("\u0645\u0646")                                 # م ن
LIQUID     = set("\u0644\u0631")                                 # ل ر
CORONAL    = set("\u062A\u062B\u062F\u0630\u0632\u0633\u0634\u0635\u0636\u0637\u0638")
LABIAL     = set("\u0628\u0641")                                 # ب ف
DORSAL     = set("\u062C\u0643\u0642\u062E\u063A")               # ج ك ق خ غ
GUTTURAL   = set("\u062D\u0639\u0647\u0621\u0623\u0625\u0624\u0626")  # ح ع ه ء أ إ ؤ ئ
TAA_MARBUTA = "\u0629"   # treat as coronal
ALEF_MAKSURA = "\u0649"  # treat as long-vowel


def rhyme_class(letter: str) -> int | None:
    if letter in LONG_VOWEL:
        return 0
    if letter in NASAL:
        return 1
    if letter in LIQUID:
        return 2
    if letter in CORONAL or letter == TAA_MARBUTA:
        return 3
    if letter in LABIAL:
        return 4
    if letter in DORSAL:
        return 5
    if letter in GUTTURAL:
        return 6
    return None


# Stripping: keep only base Arabic letters.
DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F),
               (0x064B, 0x065F), (0x0670, 0x0670)]  # also strip ALL diacritics for rhyme extraction
DROP_SINGLES = {0x00A0, 0x0640, 0x0651, 0x0652}


def is_dropped(ch):
    cp = ord(ch)
    if cp < 128:
        return True
    if cp in DROP_SINGLES:
        return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def last_letter(text: str) -> str | None:
    """Return the last Arabic letter (no diacritics, no pause marks)."""
    for ch in reversed(text):
        if ch in (" ", "\n", "\t", "\r"):
            continue
        if is_dropped(ch):
            continue
        cp = ord(ch)
        if 0x0621 <= cp <= 0x064A or ch in ("\u0671", "\u0649"):
            return ch
    return None


# ────────────────────────────────────────────────────────────────
# Statistics
# ────────────────────────────────────────────────────────────────
def rhyme_density(R):
    return float((R[1:] == R[:-1]).mean())


def run_lengths(R):
    runs = []
    cur_r = R[0]; cur_len = 1
    for r in R[1:]:
        if r == cur_r:
            cur_len += 1
        else:
            runs.append(cur_len); cur_r = r; cur_len = 1
    runs.append(cur_len)
    return np.asarray(runs)


def within_surah_purity(R, surah_of_verse):
    # For each surah, fraction of verses matching surah's modal rhyme
    import collections
    by_s = collections.defaultdict(list)
    for r, s in zip(R, surah_of_verse):
        by_s[s].append(r)
    purities = []
    for s, rs in by_s.items():
        vals, counts = np.unique(rs, return_counts=True)
        modal = vals[np.argmax(counts)]
        purities.append((np.array(rs) == modal).mean())
    return float(np.mean(purities))


def shannon_entropy(R, k=7):
    counts = np.bincount(R, minlength=k).astype(float)
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


# ────────────────────────────────────────────────────────────────
def main():
    out_dir = ROOT / "results" / "experiments" / "exp172_saj_rhyme"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp172] Loading Mushaf & extracting verse-end rhymes ...", flush=True)
    raw = QURAN_VOCAL.read_text(encoding="utf-8")
    rhymes = []
    surahs = []
    dropped = 0
    unclassified = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        si = int(parts[0])
        if not (1 <= si <= 114):
            continue
        letter = last_letter(parts[2])
        if letter is None:
            dropped += 1; continue
        cls = rhyme_class(letter)
        if cls is None:
            unclassified.append(letter)
            dropped += 1; continue
        rhymes.append(cls)
        surahs.append(si)

    R = np.asarray(rhymes, dtype=np.int8)
    surahs = np.asarray(surahs, dtype=int)
    N = len(R)
    print(f"[exp172] extracted {N} verse rhymes (dropped {dropped})", flush=True)
    if unclassified:
        uc = set(unclassified)
        print(f"[exp172] unclassified final letters (dropped): {[(c, hex(ord(c))) for c in uc][:10]}", flush=True)

    K = 7
    counts = np.bincount(R, minlength=K).tolist()
    print(f"[exp172] class counts (long-V, nasal, liquid, coronal, labial, dorsal, guttural): {counts}", flush=True)

    # Observed stats
    print("\n[exp172] === observed stats ===", flush=True)
    density_obs = rhyme_density(R)
    runs = run_lengths(R)
    mean_run_obs = float(runs.mean())
    max_run_obs = int(runs.max())
    purity_obs = within_surah_purity(R, surahs)
    H_obs = shannon_entropy(R, K)
    print(f"  T1 rhyme density             = {density_obs:.6f}", flush=True)
    print(f"  T2 mean run length           = {mean_run_obs:.4f}", flush=True)
    print(f"  T3 max run length            = {max_run_obs}", flush=True)
    print(f"  T4 within-surah purity       = {purity_obs:.6f}", flush=True)
    print(f"  T5 rhyme entropy             = {H_obs:.4f} bits  (max {np.log2(K):.4f})", flush=True)

    # Shuffle null
    print("\n[exp172] === shuffle null (n=5000) ===", flush=True)
    rng = np.random.default_rng(20260501)
    N_PERM = 5000
    d_null = np.empty(N_PERM); mr_null = np.empty(N_PERM); xr_null = np.empty(N_PERM, dtype=int)
    pur_null = np.empty(N_PERM); H_null = np.empty(N_PERM)
    Rc = R.copy()
    t0 = time.time()
    for i in range(N_PERM):
        rng.shuffle(Rc)
        d_null[i] = rhyme_density(Rc)
        rlen = run_lengths(Rc)
        mr_null[i] = rlen.mean(); xr_null[i] = rlen.max()
        pur_null[i] = within_surah_purity(Rc, surahs)
        H_null[i] = shannon_entropy(Rc, K)
        if (i + 1) % 500 == 0:
            print(f"    [shuffle] {i+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    p_d = float((1 + (d_null >= density_obs).sum()) / (1 + N_PERM))
    p_mr = float((1 + (mr_null >= mean_run_obs).sum()) / (1 + N_PERM))
    p_xr = float((1 + (xr_null >= max_run_obs).sum()) / (1 + N_PERM))
    p_pur = float((1 + (pur_null >= purity_obs).sum()) / (1 + N_PERM))
    # T5 two-tailed:
    H_dev_obs = abs(H_obs - H_null.mean())
    p_H = float((1 + (np.abs(H_null - H_null.mean()) >= H_dev_obs).sum()) / (1 + N_PERM))

    print(f"\n[exp172] ── null summary ──", flush=True)
    print(f"  T1 density :  obs={density_obs:.4f}  null={d_null.mean():.4f}±{d_null.std():.4f}  z={(density_obs-d_null.mean())/d_null.std():+.2f}  p={p_d:.4g}", flush=True)
    print(f"  T2 mean run:  obs={mean_run_obs:.4f}  null={mr_null.mean():.4f}±{mr_null.std():.4f}  z={(mean_run_obs-mr_null.mean())/mr_null.std():+.2f}  p={p_mr:.4g}", flush=True)
    print(f"  T3 max run :  obs={max_run_obs}      null={xr_null.mean():.2f}±{xr_null.std():.2f}  p={p_xr:.4g}", flush=True)
    print(f"  T4 purity  :  obs={purity_obs:.4f}  null={pur_null.mean():.4f}±{pur_null.std():.4f}  z={(purity_obs-pur_null.mean())/pur_null.std():+.2f}  p={p_pur:.4g}", flush=True)
    print(f"  T5 entropy :  obs={H_obs:.4f}    null={H_null.mean():.4f}±{H_null.std():.4f}  p={p_H:.4g}", flush=True)

    alpha = 0.01
    pass_d = p_d < alpha
    pass_mr = p_mr < alpha
    pass_xr = p_xr < alpha
    pass_pur = p_pur < alpha
    pass_H = p_H < alpha
    n_pass = sum([pass_d, pass_mr, pass_xr, pass_pur, pass_H])

    if n_pass >= 3 and pass_d:
        verdict = "PASS_SAJ_QURAN_REFERENCE"
    elif n_pass >= 1:
        verdict = f"PASS_PARTIAL_{n_pass}of5"
    else:
        verdict = "FAIL"

    print(f"\n[exp172] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp172] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp172] ║ T1 density={density_obs:.3f}  T2 mean-run={mean_run_obs:.2f}  T3 max-run={max_run_obs}", flush=True)
    print(f"[exp172] ║ T4 purity={purity_obs:.3f}  T5 H={H_obs:.3f}b  n_pass={n_pass}/5", flush=True)
    print(f"[exp172] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp172_saj_rhyme",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": {"N_verses_classified": int(N), "N_dropped": int(dropped), "class_counts": counts},
        "alpha_per_test": alpha,
        "observed": {
            "T1_density": density_obs, "T2_mean_run": mean_run_obs, "T3_max_run": max_run_obs,
            "T4_within_surah_purity": purity_obs, "T5_entropy_bits": H_obs,
        },
        "shuffle_null": {
            "n_perm": N_PERM,
            "T1": {"obs": density_obs, "null_mean": float(d_null.mean()), "null_std": float(d_null.std()), "p": p_d, "pass": bool(pass_d)},
            "T2": {"obs": mean_run_obs, "null_mean": float(mr_null.mean()), "null_std": float(mr_null.std()), "p": p_mr, "pass": bool(pass_mr)},
            "T3": {"obs": max_run_obs, "null_mean": float(xr_null.mean()), "null_std": float(xr_null.std()), "p": p_xr, "pass": bool(pass_xr)},
            "T4": {"obs": purity_obs, "null_mean": float(pur_null.mean()), "null_std": float(pur_null.std()), "p": p_pur, "pass": bool(pass_pur)},
            "T5": {"obs": H_obs, "null_mean": float(H_null.mean()), "null_std": float(H_null.std()), "p": p_H, "pass": bool(pass_H)},
        },
        "n_pass": int(n_pass),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        for ax, (label, obs, null) in zip(
            axes.flat,
            [("T1 density", density_obs, d_null), ("T2 mean run", mean_run_obs, mr_null),
             ("T3 max run", max_run_obs, xr_null), ("T4 purity", purity_obs, pur_null),
             ("T5 entropy", H_obs, H_null)]
        ):
            ax.hist(null, bins=40, color="#888", alpha=0.7, density=True, label="null")
            ax.axvline(obs, color="r", linewidth=2, label=f"obs {obs:.4f}")
            ax.set_title(label); ax.legend()
        axes.flat[-1].axis("off")
        fig.suptitle(f"exp172 saj' — verdict {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_nulls.png", dpi=120)
        plt.close(fig)

        # Run-length distribution
        fig, ax = plt.subplots(figsize=(9, 5))
        max_plot = min(max(runs), 80)
        ax.hist(runs, bins=np.arange(1, max_plot + 2) - 0.5, color="#1565c0", alpha=0.7, density=True, label="Quran observed")
        ax.hist(run_lengths(np.random.default_rng(42).permutation(R)), bins=np.arange(1, max_plot + 2) - 0.5,
                color="#888", alpha=0.5, density=True, label="one shuffle realisation")
        ax.set_xlabel("run length (consecutive same-rhyme verses)")
        ax.set_ylabel("density"); ax.set_yscale("log")
        ax.set_title(f"exp172: run-length distribution (max run = {max_run_obs})")
        ax.legend()
        fig.tight_layout(); fig.savefig(out_dir / "fig_run_lengths.png", dpi=120); plt.close(fig)

        # Rhyme sequence timeline
        fig, ax = plt.subplots(figsize=(14, 3))
        colors = ["#1976d2", "#d32f2f", "#388e3c", "#f57c00", "#7b1fa2", "#0097a7", "#5d4037"]
        for c in range(K):
            m = R == c
            ax.scatter(np.arange(N)[m], [c] * m.sum(), s=2, color=colors[c], alpha=0.7)
        ax.set_xlabel("verse index")
        ax.set_ylabel("rhyme class")
        ax.set_yticks(range(K))
        ax.set_yticklabels(["long-V", "nasal", "liquid", "coronal", "labial", "dorsal", "guttural"])
        ax.set_title("exp172: verse-end rhyme class across the Mushaf")
        fig.tight_layout(); fig.savefig(out_dir / "fig_rhyme_timeline.png", dpi=120); plt.close(fig)
        print(f"[exp172] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp172] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
