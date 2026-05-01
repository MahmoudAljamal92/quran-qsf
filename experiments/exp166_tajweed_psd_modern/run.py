"""exp166_tajweed_psd_modern — frozen-PREREG modernisation of the
STF_v7 TAJWEED_PSD prototype.

Operating principle: the Quran is the reference. We measure β intrinsically
on the Quran's deterministic word-level tajweed-duration sequence; controls
appear only to calibrate the metric, not as the headline.

See PREREG.md (frozen_at 2026-05-01).
"""
from __future__ import annotations
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import welch
from scipy.stats import linregress

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ────────────────────────────────────────────────────────────────────
# Frozen tajweed model (Hafs 'an 'Asim, v1, per-character)
# ────────────────────────────────────────────────────────────────────
TAJWEED_WEIGHTS: dict[str, int] = {
    "\u064E": 1,  # fatha
    "\u0650": 1,  # kasra
    "\u064F": 1,  # damma
    "\u064B": 2,  # fathatan
    "\u064C": 2,  # dammatan
    "\u064D": 2,  # kasratan
    "\u0651": 1,  # shadda
    "\u0653": 2,  # maddah
    "\u0652": 1,  # sukun
    "\u0670": 2,  # superscript alef
}
ARABIC_CONSONANTS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويءأإآؤئةى")


def word_tajweed_duration(word: str) -> int:
    d = 0
    for ch in word:
        if ch in ARABIC_CONSONANTS:
            d += 1
        elif ch in TAJWEED_WEIGHTS:
            d += TAJWEED_WEIGHTS[ch]
    return max(d, 1)


# ────────────────────────────────────────────────────────────────────
# Loader
# ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
RIWAYAT_DIR = ROOT / "data" / "corpora" / "ar" / "riwayat"


def load_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def text_to_duration_seq(text: str) -> np.ndarray:
    out: list[int] = []
    for line in text.splitlines():
        # strip surah|verse| prefix if present
        if "|" in line:
            parts = line.split("|", 2)
            line = parts[-1] if len(parts) == 3 else line
        for word in line.split():
            d = word_tajweed_duration(word)
            if d > 0:
                out.append(d)
    return np.asarray(out, dtype=float)


# ────────────────────────────────────────────────────────────────────
# β estimator
# ────────────────────────────────────────────────────────────────────
INERTIAL_BAND = (1e-3, 1e-1)


def estimate_beta(
    seq: np.ndarray, nperseg: int = 2048, noverlap: int = 1024
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Return (beta, R2, freqs, psd) with β fit over INERTIAL_BAND."""
    if len(seq) < nperseg:
        nperseg = max(256, len(seq) // 4)
        noverlap = nperseg // 2
    freqs, psd = welch(seq, fs=1.0, nperseg=nperseg, noverlap=noverlap, window="hann")
    freqs = freqs[1:]
    psd = psd[1:]
    mask = (freqs >= INERTIAL_BAND[0]) & (freqs <= INERTIAL_BAND[1])
    if mask.sum() < 5:
        return float("nan"), float("nan"), freqs, psd
    log_f = np.log10(freqs[mask])
    log_p = np.log10(psd[mask] + 1e-30)
    slope, _, r, _, _ = linregress(log_f, log_p)
    return float(-slope), float(r ** 2), freqs, psd


def block_bootstrap_beta(
    seq: np.ndarray, n_boot: int = 1000, block_size: int = 700, seed: int = 20260501
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    W = len(seq)
    n_blocks = W // block_size
    betas = []
    for _ in range(n_boot):
        starts = rng.integers(0, W - block_size, size=n_blocks)
        sample = np.concatenate([seq[s : s + block_size] for s in starts])
        b, _, _, _ = estimate_beta(sample)
        if np.isfinite(b):
            betas.append(b)
    betas = np.asarray(betas)
    return float(np.percentile(betas, 2.5)), float(np.percentile(betas, 97.5))


def shuffle_null_betas(
    seq: np.ndarray, n_perm: int = 5000, seed: int = 20260502
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    seq_c = seq.copy()
    out = np.empty(n_perm, dtype=float)
    t0 = time.time()
    for i in range(n_perm):
        rng.shuffle(seq_c)
        b, _, _, _ = estimate_beta(seq_c)
        out[i] = b
        if (i + 1) % 1000 == 0:
            print(f"    [shuffle] perm {i+1}/{n_perm}  elapsed {time.time()-t0:.1f}s", flush=True)
    return out


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
def main():
    out_dir = ROOT / "results" / "experiments" / "exp166_tajweed_psd_modern"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp166] Loading vocalised Quran ...", flush=True)
    quran_txt = load_text(QURAN_VOCAL)
    D = text_to_duration_seq(quran_txt)
    W = len(D)
    print(f"[exp166] Quran word-duration sequence length: W={W}", flush=True)
    print(f"[exp166] mean={D.mean():.3f}  std={D.std():.3f}  min={D.min():.0f} max={D.max():.0f}", flush=True)

    # Audit
    audit = {
        "audit_W_geq_70000": bool(W >= 70_000),
        "audit_W": int(W),
        "audit_mean_duration": float(D.mean()),
        "audit_std_duration": float(D.std()),
    }
    print(f"[exp166] audit: {audit}", flush=True)

    # T1: primary β
    print("\n[exp166] === T1: primary β (nperseg=2048) ===", flush=True)
    beta_obs, r2_obs, freqs, psd = estimate_beta(D, nperseg=2048, noverlap=1024)
    print(f"  β = {beta_obs:.4f}   R² = {r2_obs:.4f}", flush=True)

    # block bootstrap CI
    print("[exp166] block-bootstrap 95% CI (n_boot=1000, block=700) ...", flush=True)
    t0 = time.time()
    ci_lo, ci_hi = block_bootstrap_beta(D)
    print(f"  95% CI = [{ci_lo:.4f}, {ci_hi:.4f}]   elapsed {time.time()-t0:.1f}s", flush=True)

    # T2: shuffle null
    print("\n[exp166] === T2: shuffle null (n_perm=5000) ===", flush=True)
    null_betas = shuffle_null_betas(D, n_perm=5000)
    p_shuffle = float((1 + (null_betas >= beta_obs).sum()) / (1 + len(null_betas)))
    null_mean, null_std = float(null_betas.mean()), float(null_betas.std())
    print(f"  null β: mean={null_mean:.4f}  std={null_std:.4f}", flush=True)
    print(f"  p_shuffle = {p_shuffle:.6f}   (Bonferroni α/4 = 0.0125)", flush=True)

    # T3: window robustness
    print("\n[exp166] === T3: window robustness ===", flush=True)
    window_betas = {}
    for nps in (1024, 2048, 4096):
        b, r2, _, _ = estimate_beta(D, nperseg=nps, noverlap=nps // 2)
        window_betas[nps] = (b, r2)
        print(f"  nperseg={nps}: β={b:.4f}  R²={r2:.4f}", flush=True)
    window_max_dev = max(abs(b - beta_obs) for (b, _) in window_betas.values())
    window_pass = bool(window_max_dev < 0.10)
    print(f"  max |Δβ| from 2048-baseline = {window_max_dev:.4f}   pass(<0.10)={window_pass}", flush=True)

    # T4: riwayat invariance
    print("\n[exp166] === T4: riwayat invariance ===", flush=True)
    riwayat_betas = {"hafs": beta_obs}
    for name in ("warsh", "qalun", "duri", "shuba", "sousi"):
        path = RIWAYAT_DIR / f"{name}.txt"
        if not path.exists():
            print(f"  [WARN] missing {path}", flush=True)
            continue
        Dr = text_to_duration_seq(load_text(path))
        br, _, _, _ = estimate_beta(Dr)
        riwayat_betas[name] = float(br)
        print(f"  {name:>6}:  W={len(Dr):>7}   β={br:.4f}", flush=True)
    rb_arr = np.array(list(riwayat_betas.values()))
    cv_beta = float(rb_arr.std() / abs(rb_arr.mean()))
    print(f"  CV_β across 6 readings = {cv_beta:.4f}   pass(<0.05)={cv_beta < 0.05}", flush=True)

    # ─────────────────────────────────────────────────────────────────
    # Verdict
    # ─────────────────────────────────────────────────────────────────
    pink_band = (0.8 <= beta_obs <= 1.2)
    sig_shuffle = p_shuffle < 0.0125
    riwayat_invariant = cv_beta < 0.05

    if not window_pass or not riwayat_invariant:
        verdict = "AMBIGUOUS"
    elif not sig_shuffle:
        verdict = "FAIL_NO_INTRINSIC_STRUCTURE"
    elif pink_band:
        verdict = "PASS_PINK_NOISE_QURAN_REFERENCE"
    else:
        verdict = "PASS_STRUCTURED_BUT_NOT_PINK"

    print(f"\n[exp166] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp166] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp166] ║ Quran rhythm constant β = {beta_obs:.4f}", flush=True)
    print(f"[exp166] ║   95% CI [{ci_lo:.4f}, {ci_hi:.4f}]", flush=True)
    print(f"[exp166] ║   shuffle null p = {p_shuffle:.6f}", flush=True)
    print(f"[exp166] ║   CV across 6 riwayat = {cv_beta:.4f}", flush=True)
    print(f"[exp166] ╚══════════════════════════════════════════════", flush=True)

    # ─────────────────────────────────────────────────────────────────
    # Receipt
    # ─────────────────────────────────────────────────────────────────
    receipt = {
        "experiment": "exp166_tajweed_psd_modern",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": audit,
        "T1_primary": {
            "beta_obs": float(beta_obs),
            "R2": float(r2_obs),
            "ci_95": [ci_lo, ci_hi],
            "nperseg": 2048,
            "noverlap": 1024,
            "inertial_band": list(INERTIAL_BAND),
        },
        "T2_shuffle_null": {
            "n_perm": 5000,
            "null_mean_beta": null_mean,
            "null_std_beta": null_std,
            "p_shuffle": p_shuffle,
            "alpha_bonferroni": 0.0125,
        },
        "T3_window_robustness": {
            f"nperseg_{k}": {"beta": v[0], "R2": v[1]}
            for k, v in window_betas.items()
        },
        "T3_max_deviation": float(window_max_dev),
        "T3_pass": window_pass,
        "T4_riwayat_betas": riwayat_betas,
        "T4_cv_beta": cv_beta,
        "T4_pass": riwayat_invariant,
        "interpretation": {
            "pink_noise_band": [0.8, 1.2],
            "in_pink_band": bool(pink_band),
            "shuffle_significant": bool(sig_shuffle),
            "operating_principle": "Quran-as-reference: β_obs is the locked Quran rhythm constant.",
        },
    }
    receipt_path = out_dir / "receipt.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    print(f"[exp166] receipt → {receipt_path}", flush=True)

    # ─────────────────────────────────────────────────────────────────
    # Figures
    # ─────────────────────────────────────────────────────────────────
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # PSD plot
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.loglog(freqs, psd, color="#1565c0", linewidth=0.7, alpha=0.7, label="Quran (Hafs)")
        mask = (freqs >= INERTIAL_BAND[0]) & (freqs <= INERTIAL_BAND[1])
        log_f = np.log10(freqs[mask])
        log_p = np.log10(psd[mask] + 1e-30)
        slope, intercept, *_ = linregress(log_f, log_p)
        fit_line = 10 ** (intercept + slope * log_f)
        ax.loglog(freqs[mask], fit_line, "r--", linewidth=2, label=f"fit β = {beta_obs:.3f}")
        ax.axvspan(*INERTIAL_BAND, alpha=0.1, color="grey", label="inertial band")
        ax.set_xlabel("frequency (cycles per word)")
        ax.set_ylabel("PSD")
        ax.set_title(f"exp166: Quran tajweed-duration PSD\nβ={beta_obs:.4f}  CI=[{ci_lo:.4f},{ci_hi:.4f}]  p_shuffle={p_shuffle:.4g}")
        ax.legend()
        ax.grid(True, alpha=0.3, which="both")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_psd.png", dpi=120)
        plt.close(fig)

        # Riwayat plot
        fig, ax = plt.subplots(figsize=(8, 5))
        names = list(riwayat_betas.keys())
        vals = [riwayat_betas[n] for n in names]
        ax.bar(names, vals, color=["#1565c0"] + ["#888"] * (len(names) - 1))
        ax.axhline(np.mean(vals), color="r", linestyle="--", label=f"mean={np.mean(vals):.4f}")
        ax.axhspan(0.8, 1.2, alpha=0.1, color="green", label="pink band [0.8,1.2]")
        ax.set_ylabel("β")
        ax.set_title(f"exp166: β across 6 readings  CV={cv_beta:.4f}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "fig_riwayat.png", dpi=120)
        plt.close(fig)

        # Shuffle null
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(null_betas, bins=50, color="#888", alpha=0.7, density=True, label=f"null (mean={null_mean:.3f})")
        ax.axvline(beta_obs, color="r", linewidth=2, label=f"observed β={beta_obs:.4f}")
        ax.set_xlabel("β")
        ax.set_ylabel("density")
        ax.set_title(f"exp166: shuffle null  (n=5000, p={p_shuffle:.4g})")
        ax.legend()
        fig.tight_layout()
        fig.savefig(out_dir / "fig_shuffle_null.png", dpi=120)
        plt.close(fig)

        print(f"[exp166] figures saved to {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp166] figure rendering skipped: {e}", flush=True)

    return receipt


if __name__ == "__main__":
    main()
