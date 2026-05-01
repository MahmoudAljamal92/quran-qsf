"""exp168_sonority_sequencing — frozen-PREREG sonority profile of the
recited Quran. Tests four intrinsic statistics vs random-shuffle null.

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
from scipy.stats import linregress

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ────────────────────────────────────────────────────────────────────
# Frozen sonority table (4-class)
# ────────────────────────────────────────────────────────────────────
# Vowel diacritics (sonority 4)
VOWEL_DIACRITICS = {
    "\u064E": (4,),         # fatha
    "\u0650": (4,),         # kasra
    "\u064F": (4,),         # damma
    "\u064B": (4, 2),       # fathatan = vowel + nasal
    "\u064C": (4, 2),       # dammatan
    "\u064D": (4, 2),       # kasratan
    "\u0670": (4,),         # superscript alef
    "\u0653": (4,),         # maddah
    "\u0655": (4,),         # hamza-below
    "\u0656": (4,),         # subscript alef
    "\u0657": (4,),         # inverted damma
    "\u065E": (4,),         # fatha + 2 dots
}
SHADDA = "\u0651"  # doubles previous consonant
SUKUN = "\u0652"   # dropped

GLIDE_LIQUID = set("\u0648\u064A\u0644\u0631")  # و ي ل ر
NASAL = set("\u0645\u0646")                      # م ن
ALEF = set("\u0627\u0671")                       # ا and alef-wasla treated as vowel
ARABIC_LETTER_RANGE = (0x0621, 0x064A)
EXTRA_LETTERS = set("\u0671")  # alef wasla


def char_class(ch: str) -> int | None:
    """Return sonority class of a base char, or None if not a base letter."""
    if ch in ALEF:
        return 4  # treat alef as vowel
    if ch in GLIDE_LIQUID:
        return 3
    if ch in NASAL:
        return 2
    cp = ord(ch)
    if (ARABIC_LETTER_RANGE[0] <= cp <= ARABIC_LETTER_RANGE[1]) or ch in EXTRA_LETTERS:
        return 1  # obstruent (default)
    return None


# Strip rules (identical to exp167)
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


def text_to_sonority_seq(text: str) -> np.ndarray:
    """Walk cleaned text and emit sonority values. Skip sukun. Shadda
    doubles the previous emitted class. Diacritics expand per VOWEL_DIACRITICS.
    """
    out: list[int] = []
    last_consonant_class: int | None = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r"):
            continue
        if is_dropped(ch):
            continue
        if ch == SUKUN:
            continue
        if ch == SHADDA:
            if last_consonant_class is not None:
                out.append(last_consonant_class)
            continue
        if ch in VOWEL_DIACRITICS:
            for v in VOWEL_DIACRITICS[ch]:
                out.append(v)
            continue
        cls = char_class(ch)
        if cls is None:
            continue
        out.append(cls)
        if cls != 4:
            last_consonant_class = cls
    return np.asarray(out, dtype=float)


# ────────────────────────────────────────────────────────────────────
# Statistics
# ────────────────────────────────────────────────────────────────────
INERTIAL_BAND = (1e-3, 1e-1)


def lag1_autocorr(s: np.ndarray) -> float:
    s0 = s - s.mean()
    return float(np.dot(s0[:-1], s0[1:]) / np.dot(s0, s0))


def estimate_beta(s: np.ndarray, nperseg=4096, noverlap=2048):
    if len(s) < nperseg:
        nperseg = max(512, len(s) // 4)
        noverlap = nperseg // 2
    freqs, psd = welch(s, fs=1.0, nperseg=nperseg, noverlap=noverlap, window="hann")
    freqs = freqs[1:]; psd = psd[1:]
    mask = (freqs >= INERTIAL_BAND[0]) & (freqs <= INERTIAL_BAND[1])
    if mask.sum() < 5:
        return float("nan"), freqs, psd
    log_f, log_p = np.log10(freqs[mask]), np.log10(psd[mask] + 1e-30)
    slope, *_ = linregress(log_f, log_p)
    return float(-slope), freqs, psd


def peak_freq_ratio(s: np.ndarray, nperseg=4096) -> float:
    """Fraction of total PSD power concentrated at the dominant peak's
    ±1-bin neighbourhood."""
    freqs, psd = welch(s, fs=1.0, nperseg=nperseg, noverlap=nperseg // 2, window="hann")
    freqs = freqs[1:]; psd = psd[1:]
    if len(psd) == 0:
        return float("nan")
    i = int(np.argmax(psd))
    lo = max(0, i - 1); hi = min(len(psd), i + 2)
    return float(psd[lo:hi].sum() / psd.sum())


def alt_rate(s: np.ndarray) -> float:
    """Fraction of adjacent positions where sonority class differs."""
    return float((s[1:] != s[:-1]).mean())


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"


def main():
    out_dir = ROOT / "results" / "experiments" / "exp168_sonority_sequencing"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp168] Loading vocalised Quran ...", flush=True)
    text = QURAN_VOCAL.read_text(encoding="utf-8")
    S = text_to_sonority_seq(text)
    N = len(S)
    print(f"[exp168] sonority sequence length N = {N}", flush=True)
    counts = {c: int((S == c).sum()) for c in (1, 2, 3, 4)}
    print(f"[exp168] class counts: {counts}", flush=True)

    print("\n[exp168] === T1 lag-1 autocorrelation ===", flush=True)
    rho_obs = lag1_autocorr(S)
    print(f"  ρ_lag1 = {rho_obs:+.6f}", flush=True)

    print("[exp168] === T2 PSD β ===", flush=True)
    beta_obs, freqs_obs, psd_obs = estimate_beta(S, 4096, 2048)
    print(f"  β = {beta_obs:.4f}", flush=True)

    print("[exp168] === T3 peak-frequency power ratio ===", flush=True)
    pkr_obs = peak_freq_ratio(S, 4096)
    print(f"  peak-bin power ratio = {pkr_obs:.6f}", flush=True)

    print("[exp168] === T4 alternation rate ===", flush=True)
    alt_obs = alt_rate(S)
    print(f"  alt rate = {alt_obs:.6f}", flush=True)

    print("\n[exp168] === shuffle null (n=2000) ===", flush=True)
    rng = np.random.default_rng(20260501)
    rho_null = np.empty(2000); beta_null = np.empty(2000)
    pkr_null = np.empty(2000); alt_null = np.empty(2000)
    Sc = S.copy()
    t0 = time.time()
    for i in range(2000):
        rng.shuffle(Sc)
        rho_null[i] = lag1_autocorr(Sc)
        b, _, _ = estimate_beta(Sc, 4096, 2048)
        beta_null[i] = b
        pkr_null[i] = peak_freq_ratio(Sc, 4096)
        alt_null[i] = alt_rate(Sc)
        if (i + 1) % 200 == 0:
            print(f"    [shuffle] {i+1}/2000  elapsed {time.time()-t0:.1f}s", flush=True)

    # p-values
    # T1: lag-1 autocorr — natural-language prediction is NEGATIVE → one-sided lower
    p_rho = float((1 + (rho_null <= rho_obs).sum()) / (1 + len(rho_null)))
    # T2: β — sonority-rise-fall expects DIFFERENT (typically MORE NEGATIVE than 0); test absolute deviation
    p_beta = float((1 + (np.abs(beta_null) >= abs(beta_obs)).sum()) / (1 + len(beta_null)))
    # T3: peak-bin power — expect HIGHER than null
    p_pkr = float((1 + (pkr_null >= pkr_obs).sum()) / (1 + len(pkr_null)))
    # T4: alt rate — expect HIGHER than null
    p_alt = float((1 + (alt_null >= alt_obs).sum()) / (1 + len(alt_null)))

    z_rho = (rho_obs - rho_null.mean()) / (rho_null.std() + 1e-30)
    z_beta = (beta_obs - beta_null.mean()) / (beta_null.std() + 1e-30)
    z_pkr = (pkr_obs - pkr_null.mean()) / (pkr_null.std() + 1e-30)
    z_alt = (alt_obs - alt_null.mean()) / (alt_null.std() + 1e-30)

    print(f"\n[exp168] ── shuffle null summary ──", flush=True)
    print(f"  T1 ρ_lag1: obs={rho_obs:+.4f}  null=({rho_null.mean():+.4f}±{rho_null.std():.4f})  z={z_rho:+.2f}  p={p_rho:.4g}", flush=True)
    print(f"  T2 β     : obs={beta_obs:+.4f}  null=({beta_null.mean():+.4f}±{beta_null.std():.4f})  z={z_beta:+.2f}  p={p_beta:.4g}", flush=True)
    print(f"  T3 peak  : obs={pkr_obs:.4f}   null=({pkr_null.mean():.4f}±{pkr_null.std():.4f})  z={z_pkr:+.2f}  p={p_pkr:.4g}", flush=True)
    print(f"  T4 alt   : obs={alt_obs:.4f}   null=({alt_null.mean():.4f}±{alt_null.std():.4f})  z={z_alt:+.2f}  p={p_alt:.4g}", flush=True)

    alpha = 0.0125
    pass_rho = p_rho < alpha
    pass_beta = p_beta < alpha
    pass_pkr = p_pkr < alpha
    pass_alt = p_alt < alpha

    n_pass = sum([pass_rho, pass_beta, pass_pkr, pass_alt])
    if n_pass >= 3 and pass_rho:
        verdict = "PASS_SONORITY_PRINCIPLE_QURAN_REFERENCE"
    elif n_pass >= 1:
        verdict = f"PASS_PARTIAL_{n_pass}of4"
    else:
        verdict = "FAIL"

    print(f"\n[exp168] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp168] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp168] ║ T1 ρ_lag1 = {rho_obs:+.4f}  T2 β = {beta_obs:+.4f}", flush=True)
    print(f"[exp168] ║ T3 peak ratio = {pkr_obs:.4f}  T4 alt rate = {alt_obs:.4f}", flush=True)
    print(f"[exp168] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp168_sonority_sequencing",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": {"N": int(N), "class_counts": counts},
        "alpha_per_test": alpha,
        "T1_lag1_autocorr": {"obs": float(rho_obs), "null_mean": float(rho_null.mean()), "null_std": float(rho_null.std()), "z": float(z_rho), "p": float(p_rho), "pass": bool(pass_rho)},
        "T2_psd_beta": {"obs": float(beta_obs), "null_mean": float(beta_null.mean()), "null_std": float(beta_null.std()), "z": float(z_beta), "p": float(p_beta), "pass": bool(pass_beta)},
        "T3_peak_power_ratio": {"obs": float(pkr_obs), "null_mean": float(pkr_null.mean()), "null_std": float(pkr_null.std()), "z": float(z_pkr), "p": float(p_pkr), "pass": bool(pass_pkr)},
        "T4_alternation_rate": {"obs": float(alt_obs), "null_mean": float(alt_null.mean()), "null_std": float(alt_null.std()), "z": float(z_alt), "p": float(p_alt), "pass": bool(pass_alt)},
        "n_pass": int(n_pass),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[exp168] receipt → {out_dir / 'receipt.json'}", flush=True)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        for ax, (label, obs, null) in zip(
            axes.flat,
            [("ρ_lag1", rho_obs, rho_null), ("β", beta_obs, beta_null),
             ("peak ratio", pkr_obs, pkr_null), ("alt rate", alt_obs, alt_null)],
        ):
            ax.hist(null, bins=40, color="#888", alpha=0.7, density=True, label="null")
            ax.axvline(obs, color="r", linewidth=2, label=f"obs {obs:.4f}")
            ax.set_title(label); ax.legend()
        fig.suptitle(f"exp168 sonority — verdict {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_nulls.png", dpi=120); plt.close(fig)

        # PSD plot
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.loglog(freqs_obs, psd_obs, color="#1565c0", linewidth=0.8, alpha=0.8, label=f"Quran sonority (β={beta_obs:.3f})")
        ax.set_xlabel("frequency (cycles/character)")
        ax.set_ylabel("PSD"); ax.set_title("exp168 sonority PSD")
        ax.legend(); ax.grid(True, alpha=0.3, which="both")
        fig.tight_layout(); fig.savefig(out_dir / "fig_psd.png", dpi=120); plt.close(fig)
        print(f"[exp168] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp168] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
