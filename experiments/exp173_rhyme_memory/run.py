"""exp173_rhyme_memory — higher-order Markov memory analysis of the
verse-end rhyme sequence.

Operating principle: Quran is the reference. No external corpora.
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
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

# Rhyme classes (identical to exp172)
LONG_VOWEL = set("\u0627\u0648\u064A\u0649\u0671\u0622")
NASAL = set("\u0645\u0646")
LIQUID = set("\u0644\u0631")
CORONAL = set("\u062A\u062B\u062F\u0630\u0632\u0633\u0634\u0635\u0636\u0637\u0638")
LABIAL = set("\u0628\u0641")
DORSAL = set("\u062C\u0643\u0642\u062E\u063A")
GUTTURAL = set("\u062D\u0639\u0647\u0621\u0623\u0625\u0624\u0626")
TAA_MARBUTA = "\u0629"
DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F),
               (0x064B, 0x065F), (0x0670, 0x0670)]
DROP_SINGLES = {0x00A0, 0x0640, 0x0651, 0x0652}


def is_dropped(ch):
    cp = ord(ch)
    if cp < 128: return True
    if cp in DROP_SINGLES: return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi: return True
    return False


def rhyme_class(letter):
    if letter in LONG_VOWEL: return 0
    if letter in NASAL: return 1
    if letter in LIQUID: return 2
    if letter in CORONAL or letter == TAA_MARBUTA: return 3
    if letter in LABIAL: return 4
    if letter in DORSAL: return 5
    if letter in GUTTURAL: return 6
    return None


def last_letter(text):
    for ch in reversed(text):
        if ch in (" ", "\n", "\t", "\r"): continue
        if is_dropped(ch): continue
        cp = ord(ch)
        if 0x0621 <= cp <= 0x064A or ch in ("\u0671", "\u0649"):
            return ch
    return None


# Entropy estimators ───────────────────────────────────────────────
K = 7


def block_entropy(seq: np.ndarray, block: int, k: int = K) -> float:
    """Shannon entropy in bits of block-length `block` n-grams, MLE plug-in."""
    if block <= 0 or block > len(seq):
        return float("nan")
    if block == 1:
        c = np.bincount(seq, minlength=k).astype(float)
        p = c / c.sum(); p = p[p > 0]
        return float(-(p * np.log2(p)).sum())
    # sliding (block)-grams
    counts = Counter()
    for i in range(len(seq) - block + 1):
        t = tuple(int(x) for x in seq[i:i + block])
        counts[t] += 1
    total = sum(counts.values())
    p = np.array(list(counts.values()), dtype=float) / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def conditional_entropy(seq: np.ndarray, order: int, k: int = K) -> float:
    """H(X_t | X_{t-order}...X_{t-1}) = H(block=order+1) - H(block=order)."""
    if order == 0:
        return block_entropy(seq, 1, k)
    return block_entropy(seq, order + 1, k) - block_entropy(seq, order, k)


def main():
    out_dir = ROOT / "results" / "experiments" / "exp173_rhyme_memory"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp173] Loading verse rhymes ...", flush=True)
    raw = QURAN_VOCAL.read_text(encoding="utf-8")
    R_list = []
    surahs = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        si = int(parts[0])
        if not (1 <= si <= 114): continue
        letter = last_letter(parts[2])
        if letter is None: continue
        cls = rhyme_class(letter)
        if cls is None: continue
        R_list.append(cls); surahs.append(si)
    R = np.asarray(R_list, dtype=np.int8)
    surahs = np.asarray(surahs, dtype=int)
    N = len(R)
    print(f"[exp173] N = {N} verses", flush=True)

    # Observed entropies
    print("\n[exp173] === observed block & conditional entropies ===", flush=True)
    H0 = block_entropy(R, 1)
    H1 = conditional_entropy(R, 1)
    H2 = conditional_entropy(R, 2)
    H3 = conditional_entropy(R, 3)
    dH1 = H0 - H1
    dH2 = H1 - H2
    dH3 = H2 - H3
    print(f"  H_0  = {H0:.4f} bits", flush=True)
    print(f"  H_1  = {H1:.4f} bits   ΔH(1) = H_0−H_1 = {dH1:.4f}", flush=True)
    print(f"  H_2  = {H2:.4f} bits   ΔH(2) = H_1−H_2 = {dH2:.4f}", flush=True)
    print(f"  H_3  = {H3:.4f} bits   ΔH(3) = H_2−H_3 = {dH3:.4f}", flush=True)
    print(f"  total compressibility  H_0 − H_3 = {H0 - H3:.4f} bits  ({(H0-H3)/H0*100:.1f}% of H_0)", flush=True)

    # Surah modal rhyme sequence
    from collections import Counter as _C
    modal = []
    for s in range(1, 115):
        mask = surahs == s
        if mask.sum() == 0: continue
        c = _C(R[mask].tolist())
        modal.append(c.most_common(1)[0][0])
    M = np.asarray(modal, dtype=np.int8)
    print(f"\n[exp173] surah modal-rhyme sequence (114 surahs):", flush=True)
    print(f"  counts: {np.bincount(M, minlength=K).tolist()}", flush=True)

    def lag1(s):
        if len(s) < 10: return float("nan")
        # for categorical: fraction of adjacent pairs that match (shifted form)
        # Use classical autocorr on integer representation:
        s = s.astype(float); s0 = s - s.mean()
        v = (s0 * s0).sum()
        if v == 0: return float("nan")
        return float((s0[:-1] * s0[1:]).sum() / v)

    modal_lag1_obs = lag1(M)
    print(f"  lag-1 autocorr of M = {modal_lag1_obs:+.4f}", flush=True)

    # Shuffle null
    print("\n[exp173] === shuffle null (n=2000) ===", flush=True)
    rng = np.random.default_rng(20260501)
    N_PERM = 2000
    dH1_n = np.empty(N_PERM); dH2_n = np.empty(N_PERM); dH3_n = np.empty(N_PERM)
    totalc_n = np.empty(N_PERM); modal_n = np.empty(N_PERM)
    Rc = R.copy(); Mc = M.copy()
    t0 = time.time()
    for i in range(N_PERM):
        rng.shuffle(Rc)
        h0 = H0  # same (multiset preserved)
        h1 = conditional_entropy(Rc, 1)
        h2 = conditional_entropy(Rc, 2)
        h3 = conditional_entropy(Rc, 3)
        dH1_n[i] = h0 - h1
        dH2_n[i] = h1 - h2
        dH3_n[i] = h2 - h3
        totalc_n[i] = h0 - h3
        rng.shuffle(Mc)
        modal_n[i] = lag1(Mc)
        if (i + 1) % 200 == 0:
            print(f"    [shuffle] {i+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    p_dH1 = float((1 + (dH1_n >= dH1).sum()) / (1 + N_PERM))
    p_dH2 = float((1 + (dH2_n >= dH2).sum()) / (1 + N_PERM))
    p_dH3 = float((1 + (dH3_n >= dH3).sum()) / (1 + N_PERM))
    p_total = float((1 + (totalc_n >= (H0 - H3)).sum()) / (1 + N_PERM))
    p_modal = float((1 + (modal_n >= modal_lag1_obs).sum()) / (1 + N_PERM))

    def z(obs, null):
        sd = null.std()
        return (obs - null.mean()) / sd if sd > 0 else float("nan")

    print("\n[exp173] ── null summary ──", flush=True)
    print(f"  T1 ΔH(1)      obs={dH1:.4f}  null={dH1_n.mean():.4f}±{dH1_n.std():.4f}  z={z(dH1, dH1_n):+.2f}  p={p_dH1:.4g}", flush=True)
    print(f"  T2 ΔH(2)      obs={dH2:.4f}  null={dH2_n.mean():.4f}±{dH2_n.std():.4f}  z={z(dH2, dH2_n):+.2f}  p={p_dH2:.4g}", flush=True)
    print(f"  T3 ΔH(3)      obs={dH3:.4f}  null={dH3_n.mean():.4f}±{dH3_n.std():.4f}  z={z(dH3, dH3_n):+.2f}  p={p_dH3:.4g}", flush=True)
    print(f"  T4 total comp obs={H0-H3:.4f}  null={totalc_n.mean():.4f}±{totalc_n.std():.4f}  z={z(H0-H3, totalc_n):+.2f}  p={p_total:.4g}", flush=True)
    print(f"  T5 modal ρ    obs={modal_lag1_obs:+.4f}  null={modal_n.mean():+.4f}±{modal_n.std():.4f}  z={z(modal_lag1_obs, modal_n):+.2f}  p={p_modal:.4g}", flush=True)

    alpha = 0.01
    pT1 = p_dH1 < alpha; pT2 = p_dH2 < alpha; pT3 = p_dH3 < alpha
    pT4 = p_total < alpha; pT5 = p_modal < alpha
    n_pass = sum([pT1, pT2, pT3, pT4, pT5])

    if pT2 and pT3:
        verdict = "PASS_HIGHER_ORDER_RHYME_MEMORY"
    elif pT5 and not (pT2 and pT3):
        verdict = "PASS_SURAH_CYCLE"
    elif pT1 and not (pT2 or pT3):
        verdict = "PASS_SAJ_MARKOV1_ONLY"
    elif n_pass >= 1:
        verdict = f"PASS_PARTIAL_{n_pass}of5"
    else:
        verdict = "FAIL"

    print(f"\n[exp173] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp173] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp173] ║ ΔH(1)={dH1:.3f}  ΔH(2)={dH2:.3f}  ΔH(3)={dH3:.3f}  total={H0-H3:.3f} bits", flush=True)
    print(f"[exp173] ║ modal-surah ρ={modal_lag1_obs:+.3f}  n_pass={n_pass}/5", flush=True)
    print(f"[exp173] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp173_rhyme_memory",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": {"N_verses": int(N), "H0": H0},
        "observed": {"H_1": H1, "H_2": H2, "H_3": H3,
                     "dH1": dH1, "dH2": dH2, "dH3": dH3,
                     "total_compressibility_bits": H0 - H3,
                     "modal_lag1": modal_lag1_obs},
        "shuffle": {
            "n_perm": N_PERM, "alpha_per_test": alpha,
            "T1_dH1": {"p": p_dH1, "pass": bool(pT1), "null_mean": float(dH1_n.mean()), "null_std": float(dH1_n.std())},
            "T2_dH2": {"p": p_dH2, "pass": bool(pT2), "null_mean": float(dH2_n.mean()), "null_std": float(dH2_n.std())},
            "T3_dH3": {"p": p_dH3, "pass": bool(pT3), "null_mean": float(dH3_n.mean()), "null_std": float(dH3_n.std())},
            "T4_total": {"p": p_total, "pass": bool(pT4), "null_mean": float(totalc_n.mean()), "null_std": float(totalc_n.std())},
            "T5_modal": {"p": p_modal, "pass": bool(pT5), "null_mean": float(modal_n.mean()), "null_std": float(modal_n.std())},
        },
        "n_pass": int(n_pass),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 5, figsize=(20, 4))
        for ax, (label, obs, null) in zip(axes, [
            ("ΔH(1)", dH1, dH1_n), ("ΔH(2)", dH2, dH2_n), ("ΔH(3)", dH3, dH3_n),
            ("H_0-H_3", H0 - H3, totalc_n), ("modal ρ", modal_lag1_obs, modal_n)
        ]):
            ax.hist(null, bins=30, color="#888", alpha=0.7, density=True, label="null")
            ax.axvline(obs, color="r", linewidth=2, label=f"obs {obs:.3f}")
            ax.set_title(label); ax.legend(fontsize=8)
        fig.suptitle(f"exp173 rhyme memory — verdict {verdict}")
        fig.tight_layout(); fig.savefig(out_dir / "fig_nulls.png", dpi=120); plt.close(fig)
        print(f"[exp173] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp173] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
