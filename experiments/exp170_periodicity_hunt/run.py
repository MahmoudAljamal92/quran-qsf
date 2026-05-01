"""exp170_periodicity_hunt — frozen-PREREG periodicity scan over
3 intrinsic Quran sequences × 11 culturally-loaded lags.

Operating principle: Quran is the reference. No external corpus comparison.
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import welch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

# ── Inlined text converters (avoid stdout-wrap collision on import) ──
DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F)]
DROP_SINGLES = {0x00A0, 0x0640}


def is_dropped(ch: str) -> bool:
    cp = ord(ch)
    if cp < 128:
        return True
    if cp in DROP_SINGLES:
        return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi:
            return True
    return False


# v2 tajweed (exp167)
TAJWEED_V2 = {"\u064E": 1, "\u0650": 1, "\u064F": 1, "\u064B": 2, "\u064C": 2, "\u064D": 2,
              "\u0651": 1, "\u0653": 2, "\u0652": 1, "\u0670": 2, "\u0655": 1, "\u0656": 2,
              "\u0657": 1, "\u065E": 1}
ARABIC_CONS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويءأإآؤئةى\u0671")
HAMZA_LETTERS = set("\u0621\u0623\u0624\u0625\u0626")
MADD_LETTERS = set("\u0627\u0648\u064A\u0671")
NUN_MEEM = set("\u0646\u0645")
SHADDA = "\u0651"; SUKUN = "\u0652"; MADDAH = "\u0653"


def _clean_v167(text):
    out = []
    for ch in text:
        if ch in (" ", "\n", "\t", "\r"):
            out.append(" ")
        elif is_dropped(ch):
            continue
        else:
            out.append(ch)
    return "".join(out)


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
            if word[i] in MADD_LETTERS:
                if word[i - 1] in (SUKUN, MADDAH, "\u064E"):
                    has_madd_ctx = True; break
    if has_madd_ctx:
        base += 3
    g = 0
    for i in range(len(word) - 1):
        if word[i] == SHADDA and word[i + 1] in NUN_MEEM:
            g += 1
        elif word[i + 1] == SHADDA and word[i] in NUN_MEEM:
            g += 1
    base += g
    return max(1, base)


def text_to_duration_seq_v2(text):
    cleaned = _clean_v167(text)
    out = []
    for w in cleaned.split():
        d = _word_dur_v2(w)
        if d > 0:
            out.append(d)
    return np.asarray(out, dtype=float)


# Sonority (exp168)
VOWEL_DIACRITICS = {"\u064E": (4,), "\u0650": (4,), "\u064F": (4,),
                    "\u064B": (4, 2), "\u064C": (4, 2), "\u064D": (4, 2),
                    "\u0670": (4,), "\u0653": (4,), "\u0655": (4,),
                    "\u0656": (4,), "\u0657": (4,), "\u065E": (4,)}
GLIDE_LIQUID = set("\u0648\u064A\u0644\u0631")
NASAL = set("\u0645\u0646")
ALEF = set("\u0627\u0671")
EXTRA = set("\u0671")


def _sonority_class(ch):
    if ch in ALEF:
        return 4
    if ch in GLIDE_LIQUID:
        return 3
    if ch in NASAL:
        return 2
    cp = ord(ch)
    if 0x0621 <= cp <= 0x064A or ch in EXTRA:
        return 1
    return None


def text_to_sonority_seq(text):
    out = []; last_c = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r") or is_dropped(ch) or ch == SUKUN:
            continue
        if ch == SHADDA:
            if last_c is not None:
                out.append(last_c)
            continue
        if ch in VOWEL_DIACRITICS:
            for v in VOWEL_DIACRITICS[ch]:
                out.append(v)
            continue
        cls = _sonority_class(ch)
        if cls is None:
            continue
        out.append(cls)
        if cls != 4:
            last_c = cls
    return np.asarray(out, dtype=float)


# Phoneme classes (exp169)
SHORT_V = {"\u064E": 0, "\u0650": 0, "\u064F": 0}
TANWEEN = {"\u064B": 1, "\u064C": 1, "\u064D": 1}
MADD_DIA = {"\u0653": 2, "\u0670": 2, "\u0656": 2, "\u0655": 2, "\u0657": 2, "\u065E": 2}
MADD_LET = set("\u0627\u0671")
NASAL_LET = set("\u0645\u0646")
LIQ_LET = set("\u0644\u0631")
GLIDE_LET = set("\u0648\u064A")
EMP_LET = set("\u0635\u0636\u0637\u0638\u0642\u0639\u062D\u062E\u063A\u0621\u0623\u0625\u0622\u0624\u0626\u0647")
OBS_LET = set("\u0628\u062A\u062B\u062C\u062F\u0630\u0632\u0633\u0634\u0641\u0643\u0629\u0649")


def _class_of(ch):
    if ch in SHORT_V:
        return 0
    if ch in TANWEEN:
        return 1
    if ch in MADD_DIA or ch in MADD_LET:
        return 2
    if ch in NASAL_LET:
        return 3
    if ch in LIQ_LET:
        return 4
    if ch in GLIDE_LET:
        return 5
    if ch in EMP_LET:
        return 6
    if ch in OBS_LET:
        return 7
    return None


def text_to_class_seq(text):
    out = []; last_c = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r") or is_dropped(ch) or ch == SUKUN:
            continue
        if ch == SHADDA:
            if last_c is not None:
                out.append(last_c)
            continue
        cls = _class_of(ch)
        if cls is None:
            continue
        out.append(cls)
        last_c = cls
    return np.asarray(out, dtype=np.int8)

LAGS = [7, 11, 14, 19, 28, 29, 30, 50, 60, 100, 114]
N_PERM = 2000


def lag_autocorr(seq: np.ndarray, lag: int) -> float:
    if lag <= 0 or lag >= len(seq):
        return float("nan")
    s0 = seq - seq.mean()
    var = (s0 * s0).sum()
    if var == 0:
        return float("nan")
    return float((s0[:-lag] * s0[lag:]).sum() / var)


def lag_autocorrs(seq: np.ndarray, lags: list) -> np.ndarray:
    """Vectorised: return autocorrelation at all lags in one pass."""
    s0 = seq - seq.mean()
    var = (s0 * s0).sum()
    if var == 0:
        return np.full(len(lags), np.nan)
    out = np.empty(len(lags))
    for i, L in enumerate(lags):
        out[i] = (s0[:-L] * s0[L:]).sum() / var if 0 < L < len(seq) else np.nan
    return out


def spectral_power_ratio(seq: np.ndarray, period: int, nperseg: int = 4096) -> float:
    """PSD power at f = 1/period divided by median PSD power. (Welch, slow — only used for observed values.)"""
    if period <= 1 or period >= len(seq) // 2:
        return float("nan")
    freqs, psd = welch(seq, fs=1.0, nperseg=min(nperseg, len(seq) // 2), window="hann")
    f_target = 1.0 / period
    i = int(np.argmin(np.abs(freqs - f_target)))
    return float(psd[i] / np.median(psd))


def fft_power_at_lags(seq: np.ndarray, lags: list) -> np.ndarray:
    """Fast: single rfft, return power at each f = 1/L, divided by median rfft power."""
    s0 = seq - seq.mean()
    P = np.abs(np.fft.rfft(s0)) ** 2
    N = len(seq)
    med = np.median(P[1:])  # drop DC
    out = np.empty(len(lags))
    for i, L in enumerate(lags):
        k = int(round(N / L))
        if 1 <= k < len(P):
            out[i] = P[k] / med
        else:
            out[i] = np.nan
    return out


def main():
    out_dir = ROOT / "results" / "experiments" / "exp170_periodicity_hunt"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp170] Loading Quran sequences ...", flush=True)
    text = QURAN_VOCAL.read_text(encoding="utf-8")

    D = text_to_duration_seq_v2(text)            # word-level
    S = text_to_sonority_seq(text)               # char-level sonority
    C = text_to_class_seq(text).astype(float)    # char-level class
    print(f"  D (word-duration) length     = {len(D)}", flush=True)
    print(f"  S (sonority) length          = {len(S)}", flush=True)
    print(f"  C (phoneme-class) length     = {len(C)}", flush=True)

    sequences = {"D": D, "S": S, "C": C}

    # Observed values (using raw-FFT power ratio so it matches the null metric)
    print("\n[exp170] === observed lag-autocorr & FFT power ratios ===", flush=True)
    obs = {}
    for name, seq in sequences.items():
        rhos = lag_autocorrs(seq, LAGS)
        Rs = fft_power_at_lags(seq, LAGS)
        obs[name] = {"rho": {L: float(rhos[i]) for i, L in enumerate(LAGS)},
                     "R":   {L: float(Rs[i])   for i, L in enumerate(LAGS)}}
        print(f"  {name}:  rho = {{{', '.join(f'{L}:{rhos[i]:+.4f}' for i, L in enumerate(LAGS))}}}", flush=True)
        print(f"         R   = {{{', '.join(f'{L}:{Rs[i]:.3f}' for i, L in enumerate(LAGS))}}}", flush=True)

    # Shuffle null (fast: rfft + vector autocorr per shuffle)
    print(f"\n[exp170] === shuffle null  (n_perm={N_PERM}) ===", flush=True)
    rng = np.random.default_rng(20260501)
    rho_null = {n: {L: np.empty(N_PERM) for L in LAGS} for n in sequences}
    R_null = {n: {L: np.empty(N_PERM) for L in LAGS} for n in sequences}
    t0 = time.time()
    seqs_c = {n: s.copy() for n, s in sequences.items()}
    for k in range(N_PERM):
        for n, sc in seqs_c.items():
            rng.shuffle(sc)
            rhos = lag_autocorrs(sc, LAGS)
            Rs = fft_power_at_lags(sc, LAGS)
            for i, L in enumerate(LAGS):
                rho_null[n][L][k] = rhos[i]
                R_null[n][L][k] = Rs[i]
        if (k + 1) % 200 == 0:
            print(f"    [shuffle] {k+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    # p-values, BHL
    print(f"\n[exp170] === p-values (Bonferroni-Holm at family α = 0.05) ===", flush=True)
    cells = []
    for n, seq in sequences.items():
        for L in LAGS:
            rho_o = obs[n]["rho"][L]
            R_o = obs[n]["R"][L]
            null_r = rho_null[n][L]
            null_R = R_null[n][L]
            p_rho = float((1 + (np.abs(null_r) >= abs(rho_o)).sum()) / (1 + len(null_r)))
            p_R = float((1 + (null_R >= R_o).sum()) / (1 + len(null_R)))
            cells.append({
                "seq": n, "lag": L,
                "rho_obs": rho_o, "p_rho": p_rho,
                "R_obs": R_o, "p_R": p_R,
                "z_rho": (rho_o - null_r.mean()) / (null_r.std() + 1e-30),
                "z_R": (R_o - null_R.mean()) / (null_R.std() + 1e-30),
            })

    # Bonferroni-Holm on the full 33-cell × 2-stat = 66 p-values
    all_p = [(c["p_rho"], c["seq"], c["lag"], "rho", c) for c in cells] + \
            [(c["p_R"], c["seq"], c["lag"], "R", c) for c in cells]
    all_p.sort(key=lambda t: t[0])
    M = len(all_p)
    bhl = []
    alpha = 0.05
    for i, (p, seq, L, kind, ref) in enumerate(all_p):
        thresh = alpha / (M - i)
        passes = p < thresh
        bhl.append({"rank": i + 1, "p": p, "seq": seq, "lag": L, "stat": kind, "thresh": thresh, "pass": bool(passes)})
        if not passes:
            # Holm: after first failure, all higher fail
            for j in range(i + 1, M):
                p_j, seq_j, L_j, kind_j, ref_j = all_p[j]
                bhl.append({"rank": j + 1, "p": p_j, "seq": seq_j, "lag": L_j, "stat": kind_j, "thresh": alpha / (M - j), "pass": False})
            break

    bhl_pass_cells = [b for b in bhl if b["pass"]]
    print(f"  total p-values: {M}; BHL surviving: {len(bhl_pass_cells)}", flush=True)
    if bhl_pass_cells:
        print(f"\n  surviving cells (sorted by p):", flush=True)
        for b in bhl_pass_cells[:20]:
            c = next(c for c in cells if c["seq"] == b["seq"] and c["lag"] == b["lag"])
            stat_val = c["rho_obs"] if b["stat"] == "rho" else c["R_obs"]
            z_val = c["z_rho"] if b["stat"] == "rho" else c["z_R"]
            print(f"    seq={b['seq']:1s}  lag={b['lag']:3d}  stat={b['stat']:3s}  obs={stat_val:+.4f}  z={z_val:+.2f}  p={b['p']:.4g}", flush=True)

    # Cross-sequence corroboration
    survivors_by_lag: dict[int, set[str]] = {}
    for b in bhl_pass_cells:
        survivors_by_lag.setdefault(b["lag"], set()).add(b["seq"])
    cross_corroborated = {L: seqs for L, seqs in survivors_by_lag.items() if len(seqs) >= 2}

    print(f"\n[exp170] cross-sequence corroborated lags (≥ 2 of 3 sequences):", flush=True)
    if cross_corroborated:
        for L, seqs in sorted(cross_corroborated.items()):
            print(f"    lag={L}: surviving in sequences {sorted(seqs)}", flush=True)
        verdict = "PASS_PERIODIC_QURAN_REFERENCE"
    elif bhl_pass_cells:
        verdict = "PASS_SINGLE_SEQUENCE"
    else:
        verdict = "FAIL"

    print(f"\n[exp170] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp170] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp170] ║ BHL-surviving cells: {len(bhl_pass_cells)} / {M}", flush=True)
    print(f"[exp170] ║ cross-corroborated lags: {sorted(cross_corroborated.keys()) if cross_corroborated else 'none'}", flush=True)
    print(f"[exp170] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp170_periodicity_hunt",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "lags": LAGS,
        "audit": {
            "len_D": int(len(D)), "len_S": int(len(S)), "len_C": int(len(C)),
            "n_perm": N_PERM, "family_alpha": alpha, "bonferroni_M": M,
        },
        "observed": {
            n: {"rho": {str(L): obs[n]["rho"][L] for L in LAGS},
                "R": {str(L): obs[n]["R"][L] for L in LAGS}}
            for n in sequences
        },
        "cells": cells,
        "bhl_surviving": bhl_pass_cells,
        "cross_corroborated_lags": {str(L): sorted(s) for L, s in cross_corroborated.items()},
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

    # Plot autocorrelation function up to lag 200
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
        max_lag = 200
        for ax, (name, seq) in zip(axes, sequences.items()):
            acf = np.array([lag_autocorr(seq, L) for L in range(1, max_lag + 1)])
            ax.plot(range(1, max_lag + 1), acf, color="#1565c0", linewidth=0.8)
            ax.axhline(0, color="k", linewidth=0.5, alpha=0.5)
            for L in LAGS:
                if L <= max_lag:
                    ax.axvline(L, color="r", linestyle=":", alpha=0.4)
            ax.set_ylabel(f"ρ({name}, L)")
            ax.set_title(f"sequence {name}: autocorrelation up to lag {max_lag}")
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel("lag")
        fig.suptitle(f"exp170 — verdict {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_acf.png", dpi=120)
        plt.close(fig)
        print(f"[exp170] figure → {out_dir / 'fig_acf.png'}", flush=True)
    except Exception as e:
        print(f"[exp170] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
