"""exp171_surah_constants — per-surah replication of the locked
v2 constants identified in exp167–exp169. Tests structural invariance,
outlier counts, length robustness, and positional drift.

Operating principle: Quran is the reference. No external corpora.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import welch
from scipy.stats import linregress, spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

# ── Inline the converters from exp170 ──
DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F)]
DROP_SINGLES = {0x00A0, 0x0640}


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


TAJWEED_V2 = {"\u064E": 1, "\u0650": 1, "\u064F": 1, "\u064B": 2, "\u064C": 2, "\u064D": 2,
              "\u0651": 1, "\u0653": 2, "\u0652": 1, "\u0670": 2, "\u0655": 1, "\u0656": 2,
              "\u0657": 1, "\u065E": 1}
ARABIC_CONS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويءأإآؤئةى\u0671")
HAMZA_LETTERS = set("\u0621\u0623\u0624\u0625\u0626")
MADD_LETTERS = set("\u0627\u0648\u064A\u0671")
NUN_MEEM = set("\u0646\u0645")
SHADDA = "\u0651"; SUKUN = "\u0652"; MADDAH = "\u0653"


def _word_dur_v2(word):
    base = 0
    for ch in word:
        if ch in ARABIC_CONS:
            base += 1
        elif ch in TAJWEED_V2:
            base += TAJWEED_V2[ch]
    if base <= 0:
        return 0
    has_hamza = any(c in HAMZA_LETTERS for c in word)
    has_madd_ctx = False
    if has_hamza:
        for i in range(1, len(word)):
            if word[i] in MADD_LETTERS and word[i - 1] in (SUKUN, MADDAH, "\u064E"):
                has_madd_ctx = True; break
    if has_madd_ctx:
        base += 3
    g = 0
    for i in range(len(word) - 1):
        if word[i] == SHADDA and word[i + 1] in NUN_MEEM:
            g += 1
        elif word[i + 1] == SHADDA and word[i] in NUN_MEEM:
            g += 1
    return max(1, base + g)


def _clean(text):
    out = []
    for ch in text:
        if ch in (" ", "\n", "\t", "\r"):
            out.append(" ")
        elif is_dropped(ch):
            continue
        else:
            out.append(ch)
    return "".join(out)


def duration_seq(text):
    cleaned = _clean(text)
    return np.asarray([d for w in cleaned.split() if (d := _word_dur_v2(w)) > 0], dtype=float)


VOWEL_DIAS = {"\u064E": (4,), "\u0650": (4,), "\u064F": (4,),
              "\u064B": (4, 2), "\u064C": (4, 2), "\u064D": (4, 2),
              "\u0670": (4,), "\u0653": (4,), "\u0655": (4,),
              "\u0656": (4,), "\u0657": (4,), "\u065E": (4,)}
GLIDE_LIQ = set("\u0648\u064A\u0644\u0631")
NASAL_L = set("\u0645\u0646")
ALEF = set("\u0627\u0671")


def _sonority(ch):
    if ch in ALEF: return 4
    if ch in GLIDE_LIQ: return 3
    if ch in NASAL_L: return 2
    cp = ord(ch)
    if 0x0621 <= cp <= 0x064A or ch == "\u0671": return 1
    return None


def sonority_seq(text):
    out = []; last = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r") or is_dropped(ch) or ch == SUKUN:
            continue
        if ch == SHADDA:
            if last is not None: out.append(last)
            continue
        if ch in VOWEL_DIAS:
            for v in VOWEL_DIAS[ch]: out.append(v)
            continue
        cls = _sonority(ch)
        if cls is None: continue
        out.append(cls)
        if cls != 4: last = cls
    return np.asarray(out, dtype=float)


# phoneme 8-class (exp169)
SHORT_V = {"\u064E": 0, "\u0650": 0, "\u064F": 0}
TANWEEN = {"\u064B": 1, "\u064C": 1, "\u064D": 1}
MADD_DIA = {"\u0653": 2, "\u0670": 2, "\u0656": 2, "\u0655": 2, "\u0657": 2, "\u065E": 2}
NASAL_SET = set("\u0645\u0646")
LIQ_SET = set("\u0644\u0631")
GLIDE_SET = set("\u0648\u064A")
EMP_SET = set("\u0635\u0636\u0637\u0638\u0642\u0639\u062D\u062E\u063A\u0621\u0623\u0625\u0622\u0624\u0626\u0647")
OBS_SET = set("\u0628\u062A\u062B\u062C\u062F\u0630\u0632\u0633\u0634\u0641\u0643\u0629\u0649")


def _class(ch):
    if ch in SHORT_V: return 0
    if ch in TANWEEN: return 1
    if ch in MADD_DIA or ch in ALEF: return 2
    if ch in NASAL_SET: return 3
    if ch in LIQ_SET: return 4
    if ch in GLIDE_SET: return 5
    if ch in EMP_SET: return 6
    if ch in OBS_SET: return 7
    return None


def class_seq(text):
    out = []; last = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r") or is_dropped(ch) or ch == SUKUN:
            continue
        if ch == SHADDA:
            if last is not None: out.append(last)
            continue
        cls = _class(ch)
        if cls is None: continue
        out.append(cls)
        last = cls
    return np.asarray(out, dtype=np.int8)


# ────────────────────────────────────────────────────────────────
# Per-surah statistics
# ────────────────────────────────────────────────────────────────
K = 8


def beta_of(seq, nperseg=None):
    if len(seq) < 256:
        return float("nan")
    nps = nperseg or min(2048, len(seq) // 2)
    nps = max(256, nps)
    try:
        freqs, psd = welch(seq, fs=1.0, nperseg=nps, noverlap=nps // 2, window="hann")
    except Exception:
        return float("nan")
    freqs, psd = freqs[1:], psd[1:]
    mask = (freqs >= 1e-3) & (freqs <= 1e-1)
    if mask.sum() < 5:
        return float("nan")
    slope, *_ = linregress(np.log10(freqs[mask]), np.log10(psd[mask] + 1e-30))
    return float(-slope)


def lag1_autocorr(s):
    if len(s) < 10:
        return float("nan")
    s0 = s - s.mean()
    v = (s0 * s0).sum()
    if v == 0: return float("nan")
    return float((s0[:-1] * s0[1:]).sum() / v)


def alt_rate(s):
    if len(s) < 2: return float("nan")
    return float((s[1:] != s[:-1]).mean())


def mutual_info_class(seq, k=K, alpha=1.0):
    if len(seq) < 20:
        return float("nan")
    counts = np.full((k, k), alpha, dtype=float)
    np.add.at(counts, (seq[:-1], seq[1:]), 1.0)
    P = counts / counts.sum(axis=1, keepdims=True)
    # stationary
    w, V = np.linalg.eig(P.T)
    i = int(np.argmin(np.abs(w - 1)))
    pi = np.real(V[:, i]); pi = np.abs(pi); pi = pi / pi.sum()
    # H_0
    sc = np.bincount(seq, minlength=k).astype(float)
    p = sc / sc.sum(); p = p[p > 0]
    H0 = float(-(p * np.log2(p)).sum())
    # H_1
    H1 = 0.0
    for ii in range(k):
        row = P[ii]; m = row > 0
        H1 -= pi[ii] * (row[m] * np.log2(row[m])).sum()
    return float(H0 - float(H1))


# ────────────────────────────────────────────────────────────────
def main():
    out_dir = ROOT / "results" / "experiments" / "exp171_surah_constants"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp171] Loading & splitting by surah ...", flush=True)
    raw = QURAN_VOCAL.read_text(encoding="utf-8")
    surah_text = {i: [] for i in range(1, 115)}
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        si = int(parts[0])
        if 1 <= si <= 114:
            surah_text[si].append(parts[2])
    surah_text = {i: "\n".join(v) for i, v in surah_text.items()}
    N_surahs = sum(1 for v in surah_text.values() if v)
    print(f"[exp171] got {N_surahs} surahs with text", flush=True)

    # compute constants per surah
    rows = []
    for i in range(1, 115):
        t = surah_text[i]
        D = duration_seq(t)
        S = sonority_seq(t)
        C = class_seq(t)
        beta = beta_of(D)
        rho = lag1_autocorr(S)
        alt = alt_rate(S)
        I = mutual_info_class(C)
        rows.append({
            "surah": i, "N_words": int(len(D)), "N_chars_S": int(len(S)), "N_chars_C": int(len(C)),
            "beta": beta, "rho_lag1": rho, "alt_rate": alt, "I": I,
        })
    for r in rows[:5] + [rows[56]] + rows[-3:]:
        print(f"  surah {r['surah']:3d}  W={r['N_words']:>5}  β={r['beta'] if np.isnan(r['beta']) else round(r['beta'],3)!s:>8}  ρ={r['rho_lag1']:+.4f}  alt={r['alt_rate']:.4f}  I={r['I']:.4f}", flush=True)

    # statistics
    def col(k):
        return np.array([r[k] for r in rows], dtype=float)

    metrics = ["beta", "rho_lag1", "alt_rate", "I"]
    stats = {}
    for m in metrics:
        v = col(m)
        valid = v[np.isfinite(v)]
        stats[m] = {
            "mean": float(valid.mean()),
            "std": float(valid.std()),
            "cv": float(valid.std() / abs(valid.mean())) if valid.mean() != 0 else float("inf"),
            "n_valid": int(len(valid)),
        }
    print("\n[exp171] === per-surah constant distributions ===", flush=True)
    for m in metrics:
        s = stats[m]
        print(f"  {m:10s}: n={s['n_valid']}  mean={s['mean']:+.4f}  std={s['std']:.4f}  CV={s['cv']:.4f}", flush=True)

    # H1 invariance
    cv_pass_count = sum(1 for m in metrics if stats[m]["cv"] < 0.10)
    H1_pass = cv_pass_count >= 2
    print(f"\n[exp171] H1 invariance (≥ 2 of 4 with CV < 0.10): {cv_pass_count}/4  pass={H1_pass}", flush=True)

    # z-scores and H2 multi-constant outliers
    z_grid = np.full((len(rows), len(metrics)), np.nan)
    for j, m in enumerate(metrics):
        v = col(m); mu = stats[m]["mean"]; sd = stats[m]["std"]
        if sd > 0:
            z_grid[:, j] = (v - mu) / sd
    big = np.abs(z_grid) > 3
    big_per_surah = big.sum(axis=1)
    multi_outliers = int((big_per_surah >= 2).sum())
    H2_pass = multi_outliers < 5
    print(f"[exp171] H2 multi-constant outliers (|z|>3 on ≥2 metrics): {multi_outliers} surahs  pass(<5)={H2_pass}", flush=True)
    if multi_outliers > 0:
        ix = np.where(big_per_surah >= 2)[0]
        print("    outlier surahs:", [(int(rows[i]["surah"]), rows[i]["N_words"], [f"{metrics[j]}:{z_grid[i,j]:+.2f}" for j in range(len(metrics)) if big[i, j]]) for i in ix], flush=True)

    # H3 length robustness
    Nw = col("N_words")
    logW = np.log10(Nw + 1)
    H3_pass = True
    length_rhos = {}
    for m in metrics:
        v = col(m); mask = np.isfinite(v)
        rho, _ = spearmanr(logW[mask], v[mask])
        length_rhos[m] = float(rho)
        if abs(rho) >= 0.30:
            H3_pass = False
    print(f"\n[exp171] H3 length robustness (Spearman ρ with log-W, threshold 0.30):", flush=True)
    for m in metrics:
        r = length_rhos[m]
        print(f"    {m:10s}:  ρ={r:+.4f}   {'OK' if abs(r) < 0.30 else 'FAIL'}", flush=True)
    print(f"    overall pass: {H3_pass}", flush=True)

    # H4 positional drift
    idx = np.arange(1, 115)
    H4_pass = True
    idx_rhos = {}
    for m in metrics:
        v = col(m); mask = np.isfinite(v)
        rho, _ = spearmanr(idx[mask], v[mask])
        idx_rhos[m] = float(rho)
        if abs(rho) >= 0.30:
            H4_pass = False
    print(f"\n[exp171] H4 positional drift (Spearman ρ with surah index, threshold 0.30):", flush=True)
    for m in metrics:
        r = idx_rhos[m]
        print(f"    {m:10s}:  ρ={r:+.4f}   {'OK' if abs(r) < 0.30 else 'FAIL'}", flush=True)
    print(f"    overall pass: {H4_pass}", flush=True)

    # Verdict
    n_pass = sum([H1_pass, H2_pass, H3_pass, H4_pass])
    if n_pass == 4:
        verdict = "PASS_SURAH_CONSTANTS_INVARIANT"
    elif n_pass >= 2:
        verdict = f"PASS_PARTIAL_{n_pass}of4"
    else:
        verdict = "FAIL"

    print(f"\n[exp171] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp171] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp171] ║ H1 invariance: {H1_pass}   H2 outliers: {H2_pass}", flush=True)
    print(f"[exp171] ║ H3 length:     {H3_pass}   H4 position: {H4_pass}", flush=True)
    print(f"[exp171] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp171_surah_constants",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "metrics": metrics,
        "per_surah": rows,
        "distributions": stats,
        "tests": {
            "H1_invariance": {"cv_pass_count": cv_pass_count, "pass": bool(H1_pass)},
            "H2_outliers":   {"multi_outlier_surahs": multi_outliers, "pass": bool(H2_pass)},
            "H3_length":     {"rhos": length_rhos, "pass": bool(H3_pass)},
            "H4_position":   {"rhos": idx_rhos, "pass": bool(H4_pass)},
        },
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        for ax, m in zip(axes.flat, metrics):
            v = col(m); mask = np.isfinite(v)
            ax.plot(idx[mask], v[mask], "o", color="#1565c0", markersize=3)
            ax.axhline(stats[m]["mean"], color="r", linestyle="--", label=f"mean={stats[m]['mean']:+.3f}  CV={stats[m]['cv']:.3f}")
            ax.set_xlabel("surah index")
            ax.set_ylabel(m)
            ax.set_title(m)
            ax.legend(); ax.grid(True, alpha=0.3)
        fig.suptitle(f"exp171 per-surah constants — verdict {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_surah_scatter.png", dpi=120)
        plt.close(fig)

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        for ax, m in zip(axes.flat, metrics):
            v = col(m); mask = np.isfinite(v)
            ax.scatter(logW[mask], v[mask], color="#1565c0", s=12, alpha=0.7)
            ax.axhline(stats[m]["mean"], color="r", linestyle="--")
            r = length_rhos[m]
            ax.set_xlabel("log10(N_words_surah)")
            ax.set_ylabel(m)
            ax.set_title(f"{m}  (Spearman ρ with log-W: {r:+.3f})")
            ax.grid(True, alpha=0.3)
        fig.suptitle(f"exp171 length-robustness scatter — verdict {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_length_robustness.png", dpi=120)
        plt.close(fig)
        print(f"[exp171] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp171] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
