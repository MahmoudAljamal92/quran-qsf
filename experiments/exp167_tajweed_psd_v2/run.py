"""exp167_tajweed_psd_v2 — frozen-PREREG v2 model.

Fixes v1 unicode-coverage gap and adds two highest-impact context rules
(madd-wajib, ghunnah). Pre-committed thresholds in PREREG.md.

Operating principle: Quran is the reference. Headline numbers intrinsic to
the Quran. No external corpus comparisons.
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
# v2 frozen tajweed model
# ────────────────────────────────────────────────────────────────────
TAJWEED_V2: dict[str, int] = {
    "\u064E": 1, "\u0650": 1, "\u064F": 1,            # short vowels
    "\u064B": 2, "\u064C": 2, "\u064D": 2,            # tanween
    "\u0651": 1,                                       # shadda
    "\u0653": 2,                                       # maddah
    "\u0652": 1,                                       # sukun
    "\u0670": 2,                                       # superscript alef
    "\u0655": 1,                                       # hamza-below  (NEW)
    "\u0656": 2,                                       # subscript alef (NEW)
    "\u0657": 1,                                       # inverted damma (NEW)
    "\u065E": 1,                                       # fatha + 2 dots (NEW)
}
ARABIC_CONSONANTS_V2 = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويءأإآؤئةى\u0671")  # +alef-wasla
HAMZA_LETTERS = set("\u0621\u0623\u0624\u0625\u0626")
MADD_LETTERS = set("\u0627\u0648\u064A\u0671")
NUN_MEEM = set("\u0646\u0645")
SHADDA = "\u0651"
SUKUN = "\u0652"
MADDAH = "\u0653"

# Strip set: ASCII (handled separately), Arabic-Indic digits, tatweel,
# pause/sajdah/marker codepoints, NBSP, ZW joiners.
DROP_RANGES = [
    (0x0660, 0x0669),  # Arabic-Indic digits
    (0x066B, 0x066C),  # decimal separators
    (0x06D6, 0x06ED),  # pause/sajdah/marker block
    (0x200C, 0x200F),  # zero-width joiners + RLM
]
DROP_SINGLES = {0x00A0, 0x0640}  # NBSP, tatweel


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


def clean_text(text: str) -> str:
    """Strip per pre-processing rules. Preserve whitespace."""
    out_chars = []
    for ch in text:
        if ch in (" ", "\n", "\t", "\r"):
            out_chars.append(" ")
        elif is_dropped(ch):
            continue
        else:
            out_chars.append(ch)
    return "".join(out_chars)


def word_duration_v2(word: str) -> int:
    base = 0
    for ch in word:
        if ch in ARABIC_CONSONANTS_V2:
            base += 1
        elif ch in TAJWEED_V2:
            base += TAJWEED_V2[ch]
    if base <= 0:
        return 0  # purely-stripped word; will be dropped from sequence

    # Madd-wajib context: word contains a madd-context long vowel
    # (alif/waw/yaa preceded by sukun or maddah) AND a hamza letter.
    has_hamza = any(c in HAMZA_LETTERS for c in word)
    has_madd_context = False
    if has_hamza:
        for i in range(1, len(word)):
            if word[i] in MADD_LETTERS:
                # look back for sukun or maddah on prior char
                prev = word[i - 1]
                if prev == SUKUN or prev == MADDAH:
                    has_madd_context = True
                    break
        # also alef alone after fatha is a madd context
        if not has_madd_context:
            for i in range(1, len(word)):
                if word[i] in MADD_LETTERS and word[i - 1] == "\u064E":
                    has_madd_context = True
                    break
    if has_madd_context:
        base += 3

    # Ghunnah upgrade: shadda adjacent to noon/meem.
    ghunnah_count = 0
    for i in range(len(word) - 1):
        if word[i] == SHADDA and word[i + 1] in NUN_MEEM:
            ghunnah_count += 1
        elif word[i + 1] == SHADDA and word[i] in NUN_MEEM:
            ghunnah_count += 1
    base += ghunnah_count

    return max(1, base)


def text_to_duration_seq_v2(text: str) -> np.ndarray:
    cleaned = clean_text(text)
    out: list[int] = []
    for word in cleaned.split():
        d = word_duration_v2(word)
        if d > 0:
            out.append(d)
    return np.asarray(out, dtype=float)


# ────────────────────────────────────────────────────────────────────
# β estimator (identical to exp166)
# ────────────────────────────────────────────────────────────────────
INERTIAL_BAND = (1e-3, 1e-1)


def estimate_beta(seq, nperseg=2048, noverlap=1024):
    if len(seq) < nperseg:
        nperseg = max(256, len(seq) // 4)
        noverlap = nperseg // 2
    freqs, psd = welch(seq, fs=1.0, nperseg=nperseg, noverlap=noverlap, window="hann")
    freqs = freqs[1:]; psd = psd[1:]
    mask = (freqs >= INERTIAL_BAND[0]) & (freqs <= INERTIAL_BAND[1])
    if mask.sum() < 5:
        return float("nan"), float("nan"), freqs, psd
    log_f = np.log10(freqs[mask])
    log_p = np.log10(psd[mask] + 1e-30)
    slope, _, r, _, _ = linregress(log_f, log_p)
    return float(-slope), float(r ** 2), freqs, psd


def block_bootstrap_beta(seq, n_boot=1000, block_size=700, seed=20260501):
    rng = np.random.default_rng(seed)
    W = len(seq)
    n_blocks = W // block_size
    betas = []
    for _ in range(n_boot):
        starts = rng.integers(0, W - block_size, size=n_blocks)
        sample = np.concatenate([seq[s:s + block_size] for s in starts])
        b, _, _, _ = estimate_beta(sample)
        if np.isfinite(b):
            betas.append(b)
    arr = np.asarray(betas)
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def shuffle_null_betas(seq, n_perm=5000, seed=20260502):
    rng = np.random.default_rng(seed)
    seq_c = seq.copy()
    out = np.empty(n_perm)
    t0 = time.time()
    for i in range(n_perm):
        rng.shuffle(seq_c)
        b, _, _, _ = estimate_beta(seq_c)
        out[i] = b
        if (i + 1) % 1000 == 0:
            print(f"    [shuffle] {i+1}/{n_perm}  elapsed {time.time()-t0:.1f}s", flush=True)
    return out


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
RIWAYAT_DIR = ROOT / "data" / "corpora" / "ar" / "riwayat"

# Pre-committed thresholds
BETA_V1 = 0.1583  # locked from exp166 receipt
TH_DRIFT = 0.5
TH_PINK = (0.8, 1.2)
TH_SHUFFLE = 0.0125
TH_WINDOW = 0.10
TH_RIWAYAT_CV = 0.05


def main():
    out_dir = ROOT / "results" / "experiments" / "exp167_tajweed_psd_v2"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp167] Loading vocalised Quran (Hafs) ...", flush=True)
    quran_txt = (QURAN_VOCAL).read_text(encoding="utf-8")
    D = text_to_duration_seq_v2(quran_txt)
    print(f"[exp167] v2 word sequence: W={len(D)}  mean={D.mean():.3f}  std={D.std():.3f}  range=[{D.min():.0f},{D.max():.0f}]", flush=True)

    # T1: primary β
    print("\n[exp167] === T1 primary β ===", flush=True)
    beta_obs, r2, freqs, psd = estimate_beta(D, 2048, 1024)
    print(f"  β_v2 = {beta_obs:.4f}   R² = {r2:.4f}", flush=True)

    drift = abs(beta_obs - BETA_V1)
    print(f"  drift |β_v2 - β_v1| = {drift:.4f}   pass(<{TH_DRIFT})={drift < TH_DRIFT}", flush=True)

    print("[exp167] block-bootstrap CI ...", flush=True)
    ci_lo, ci_hi = block_bootstrap_beta(D)
    print(f"  95% CI [{ci_lo:.4f}, {ci_hi:.4f}]", flush=True)

    # T2 shuffle null
    print("\n[exp167] === T2 shuffle null ===", flush=True)
    null_betas = shuffle_null_betas(D, 5000)
    p_shuf = float((1 + (null_betas >= beta_obs).sum()) / (1 + len(null_betas)))
    print(f"  null β: mean={null_betas.mean():.4f}  std={null_betas.std():.4f}", flush=True)
    print(f"  p_shuffle = {p_shuf:.6f}   pass(<{TH_SHUFFLE})={p_shuf < TH_SHUFFLE}", flush=True)

    # T3 windows
    print("\n[exp167] === T3 windows ===", flush=True)
    win_betas = {}
    for nps in (1024, 2048, 4096):
        b, rr, _, _ = estimate_beta(D, nperseg=nps, noverlap=nps // 2)
        win_betas[nps] = (b, rr)
        print(f"  nperseg={nps}: β={b:.4f}", flush=True)
    win_dev = max(abs(b - beta_obs) for b, _ in win_betas.values())
    win_pass = win_dev < TH_WINDOW
    print(f"  max|Δβ| = {win_dev:.4f}   pass={win_pass}", flush=True)

    # T4 riwayat
    print("\n[exp167] === T4 riwayat invariance ===", flush=True)
    riw = {"hafs": beta_obs}
    riw_W = {"hafs": int(len(D))}
    for name in ("warsh", "qalun", "duri", "shuba", "sousi"):
        path = RIWAYAT_DIR / f"{name}.txt"
        if not path.exists():
            print(f"  [WARN] missing {path}", flush=True); continue
        Dr = text_to_duration_seq_v2(path.read_text(encoding="utf-8"))
        br, _, _, _ = estimate_beta(Dr)
        riw[name] = float(br); riw_W[name] = int(len(Dr))
        print(f"  {name:>6}:  W={len(Dr):>7}   β={br:.4f}", flush=True)
    rb = np.array(list(riw.values()))
    cv = float(rb.std() / abs(rb.mean()))
    print(f"  CV(β) = {cv:.4f}   pass(<{TH_RIWAYAT_CV})={cv < TH_RIWAYAT_CV}", flush=True)

    # ── Verdict ──────────────────────────────────────────
    in_pink = TH_PINK[0] <= beta_obs <= TH_PINK[1]
    sig = p_shuf < TH_SHUFFLE
    riwayat_ok = cv < TH_RIWAYAT_CV
    drift_ok = drift < TH_DRIFT

    if not drift_ok:
        verdict = "AMBIGUOUS_DRIFT"
    elif not win_pass:
        verdict = "AMBIGUOUS_WINDOWS"
    elif not riwayat_ok:
        verdict = "AMBIGUOUS_RIWAYAT_DRIFT"
    elif not sig:
        verdict = "FAIL_NO_INTRINSIC_STRUCTURE"
    elif in_pink:
        verdict = "PASS_PINK_QURAN_REFERENCE"
    else:
        verdict = "PASS_STRUCTURED_QURAN_REFERENCE"

    print(f"\n[exp167] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp167] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp167] ║ β_v2 = {beta_obs:.4f}   95% CI [{ci_lo:.4f},{ci_hi:.4f}]", flush=True)
    print(f"[exp167] ║ drift|v2−v1| = {drift:.4f}   p_shuf = {p_shuf:.4g}", flush=True)
    print(f"[exp167] ║ window max|Δβ| = {win_dev:.4f}   riwayat CV = {cv:.4f}", flush=True)
    print(f"[exp167] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp167_tajweed_psd_v2",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": {
            "W_v2": int(len(D)),
            "mean_dur_v2": float(D.mean()),
            "std_dur_v2": float(D.std()),
            "max_dur_v2": float(D.max()),
        },
        "thresholds_pre_committed": {
            "drift_max": TH_DRIFT,
            "pink_band": list(TH_PINK),
            "shuffle_alpha": TH_SHUFFLE,
            "window_max_dev": TH_WINDOW,
            "riwayat_cv_max": TH_RIWAYAT_CV,
            "beta_v1_reference": BETA_V1,
        },
        "T1_primary": {
            "beta_v2": float(beta_obs),
            "R2": float(r2),
            "ci_95": [ci_lo, ci_hi],
            "drift_v2_v1": float(drift),
            "drift_pass": bool(drift_ok),
        },
        "T2_shuffle": {
            "n_perm": 5000,
            "null_mean": float(null_betas.mean()),
            "null_std": float(null_betas.std()),
            "p_shuffle": float(p_shuf),
            "pass": bool(sig),
        },
        "T3_windows": {f"nperseg_{k}": {"beta": v[0], "R2": v[1]} for k, v in win_betas.items()},
        "T3_max_dev": float(win_dev),
        "T3_pass": bool(win_pass),
        "T4_riwayat_betas": riw,
        "T4_riwayat_W": riw_W,
        "T4_cv": float(cv),
        "T4_pass": bool(riwayat_ok),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    # Figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.loglog(freqs, psd, color="#1565c0", linewidth=0.7, alpha=0.7, label="Quran v2 (Hafs)")
        m = (freqs >= INERTIAL_BAND[0]) & (freqs <= INERTIAL_BAND[1])
        log_f, log_p = np.log10(freqs[m]), np.log10(psd[m] + 1e-30)
        slope, intercept, *_ = linregress(log_f, log_p)
        fit = 10 ** (intercept + slope * log_f)
        ax.loglog(freqs[m], fit, "r--", linewidth=2, label=f"fit β={beta_obs:.3f}")
        ax.axvspan(*INERTIAL_BAND, alpha=0.1, color="grey")
        ax.set_xlabel("frequency (cycles per word)")
        ax.set_ylabel("PSD")
        ax.set_title(f"exp167 v2 PSD\nβ={beta_obs:.4f}  p_shuf={p_shuf:.4g}  CV_riw={cv:.4f}")
        ax.legend(); ax.grid(True, alpha=0.3, which="both")
        fig.tight_layout(); fig.savefig(out_dir / "fig_psd.png", dpi=120); plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 5))
        names = list(riw.keys()); vals = [riw[n] for n in names]
        ax.bar(names, vals, color=["#1565c0"] + ["#888"] * (len(names) - 1))
        ax.axhline(np.mean(vals), color="r", linestyle="--", label=f"mean={np.mean(vals):.4f}")
        ax.axhspan(*TH_PINK, alpha=0.1, color="green", label="pink [0.8,1.2]")
        ax.set_ylabel("β"); ax.set_title(f"exp167 v2 riwayat  CV={cv:.4f}")
        ax.legend(); fig.tight_layout(); fig.savefig(out_dir / "fig_riwayat.png", dpi=120); plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(null_betas, bins=50, color="#888", alpha=0.7, density=True, label=f"null mean={null_betas.mean():.3f}")
        ax.axvline(beta_obs, color="r", linewidth=2, label=f"obs β={beta_obs:.4f}")
        ax.set_xlabel("β"); ax.set_ylabel("density")
        ax.set_title(f"exp167 v2 shuffle null  p={p_shuf:.4g}")
        ax.legend(); fig.tight_layout(); fig.savefig(out_dir / "fig_shuffle.png", dpi=120); plt.close(fig)

        print(f"[exp167] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp167] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
