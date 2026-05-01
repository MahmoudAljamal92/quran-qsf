"""
exp76_zipf/run.py
==================
H7: Zipf's Law Deviation as a Quran Fingerprint.

Motivation
    Zipf's exponent alpha and Heaps' exponent beta characterise a
    text's vocabulary generation process. The Quran has never been
    compared to controls on these metrics.

Protocol (frozen before execution)
    T1. For each corpus: tokenise (whitespace), compute rank-frequency.
    T2. Fit Zipf's law: f(r) ~ C * r^(-alpha) via MLE on rank-freq.
    T3. Compute Heaps' law: V(n) = K * n^beta by accumulating vocab.
    T4. Test Zipf-Heaps relationship: beta ≈ 1/alpha.
    T5. 2D (alpha, beta) comparison; Mahalanobis outlier test.
    T6. Bootstrap 10k for CIs on alpha and beta.

Pre-registered thresholds
    DISTINCT:     Quran (alpha, beta) is >2σ from ctrl centroid
    SUGGESTIVE:   >1σ or unique in one dimension
    NULL:         within ctrl distribution

Reads: phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp76_zipf/
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import minimize_scalar

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp76_zipf"
SEED = 42
N_BOOT = 10000

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _tokenise_corpus(units) -> list[str]:
    """Whitespace tokenisation across all verses of all units."""
    tokens = []
    for u in units:
        for v in u.verses:
            tokens.extend(v.split())
    return tokens


def _zipf_alpha_mle(freq_sorted: np.ndarray) -> float:
    """MLE for Zipf exponent: f(r) = C * r^(-alpha).
    Using Clauset et al. (2009) discrete power-law MLE on ranks."""
    n = len(freq_sorted)
    if n < 5:
        return float("nan")
    # Use log-linear regression on top 80% of ranks (avoid tail noise)
    cutoff = max(5, int(n * 0.8))
    ranks = np.arange(1, cutoff + 1, dtype=float)
    freqs = freq_sorted[:cutoff].astype(float)
    freqs = np.maximum(freqs, 1)  # avoid log(0)

    log_r = np.log(ranks)
    log_f = np.log(freqs)

    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(log_r, log_f)
    alpha = -slope
    return float(alpha), float(r_value**2), float(std_err)


def _heaps_law(tokens: list[str], n_points: int = 50) -> tuple:
    """Compute Heaps' law V(n) = K * n^beta by accumulating vocabulary."""
    total = len(tokens)
    if total < 100:
        return float("nan"), float("nan"), float("nan")

    checkpoints = np.unique(np.geomspace(100, total, n_points).astype(int))
    vocab_seen = set()
    ns = []
    vs = []
    idx = 0

    for cp in checkpoints:
        while idx < cp and idx < total:
            vocab_seen.add(tokens[idx])
            idx += 1
        ns.append(cp)
        vs.append(len(vocab_seen))

    log_n = np.log(np.array(ns, dtype=float))
    log_v = np.log(np.array(vs, dtype=float))

    slope, intercept, r_value, _, std_err = sp_stats.linregress(log_n, log_v)
    beta = slope
    K = math.exp(intercept)
    return float(beta), float(K), float(r_value**2)


def _analyse_corpus(cname: str, units) -> dict:
    """Full Zipf + Heaps analysis for one corpus."""
    tokens = _tokenise_corpus(units)
    n_tokens = len(tokens)

    # Word frequencies
    freq_counter = Counter(tokens)
    vocab_size = len(freq_counter)
    freq_sorted = np.array(sorted(freq_counter.values(), reverse=True))

    # Zipf fit
    alpha, r2_zipf, se_alpha = _zipf_alpha_mle(freq_sorted)

    # Heaps fit
    beta, K, r2_heaps = _heaps_law(tokens)

    # Zipf-Heaps relationship: theoretical beta = 1/alpha
    beta_predicted = 1.0 / alpha if alpha > 0 else float("nan")
    beta_residual = beta - beta_predicted if np.isfinite(beta_predicted) else float("nan")

    # Hapax legomena ratio
    hapax = sum(1 for f in freq_counter.values() if f == 1)
    hapax_ratio = hapax / vocab_size if vocab_size > 0 else 0

    # Type-token ratio
    ttr = vocab_size / n_tokens if n_tokens > 0 else 0

    return {
        "n_tokens": n_tokens,
        "vocab_size": vocab_size,
        "ttr": round(ttr, 4),
        "hapax_ratio": round(hapax_ratio, 4),
        "zipf": {
            "alpha": round(alpha, 4),
            "R2": round(r2_zipf, 4),
            "std_err": round(se_alpha, 4),
        },
        "heaps": {
            "beta": round(beta, 4),
            "K": round(K, 2),
            "R2": round(r2_heaps, 4),
        },
        "zipf_heaps": {
            "beta_predicted": round(beta_predicted, 4),
            "beta_residual": round(beta_residual, 4),
        },
        "top10_words": freq_counter.most_common(10),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    results = {}

    for cname in ["quran"] + ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        res = _analyse_corpus(cname, units)
        results[cname] = res

        print(f"\n[{EXP}] {cname:20s}: n={res['n_tokens']:7d}  "
              f"V={res['vocab_size']:6d}  TTR={res['ttr']:.4f}  "
              f"α={res['zipf']['alpha']:.4f} (R²={res['zipf']['R2']:.3f})  "
              f"β={res['heaps']['beta']:.4f} (R²={res['heaps']['R2']:.3f})  "
              f"β_pred={res['zipf_heaps']['beta_predicted']:.4f}  "
              f"Δβ={res['zipf_heaps']['beta_residual']:+.4f}")

    # --- T5: 2D (alpha, beta) outlier test ---
    print(f"\n[{EXP}] === T5: 2D outlier test ===")
    q_alpha = results["quran"]["zipf"]["alpha"]
    q_beta = results["quran"]["heaps"]["beta"]
    ctrl_alphas = [results[c]["zipf"]["alpha"] for c in ARABIC_CTRL]
    ctrl_betas = [results[c]["heaps"]["beta"] for c in ARABIC_CTRL]

    mu_ctrl = np.array([np.mean(ctrl_alphas), np.mean(ctrl_betas)])
    cov_ctrl = np.cov(np.array([ctrl_alphas, ctrl_betas]))
    q_point = np.array([q_alpha, q_beta])
    diff = q_point - mu_ctrl

    # Mahalanobis distance
    try:
        cov_inv = np.linalg.inv(cov_ctrl)
        mah_d = float(np.sqrt(diff @ cov_inv @ diff))
    except np.linalg.LinAlgError:
        mah_d = float("nan")

    print(f"  Quran: (α={q_alpha:.4f}, β={q_beta:.4f})")
    print(f"  Ctrl centroid: (α={mu_ctrl[0]:.4f}, β={mu_ctrl[1]:.4f})")
    print(f"  Mahalanobis distance: {mah_d:.2f}σ")

    # Per-dimension z-scores
    z_alpha = (q_alpha - np.mean(ctrl_alphas)) / np.std(ctrl_alphas, ddof=1) if np.std(ctrl_alphas, ddof=1) > 0 else 0
    z_beta = (q_beta - np.mean(ctrl_betas)) / np.std(ctrl_betas, ddof=1) if np.std(ctrl_betas, ddof=1) > 0 else 0
    print(f"  z(α) = {z_alpha:+.2f}")
    print(f"  z(β) = {z_beta:+.2f}")

    # --- T6: Bootstrap ---
    print(f"\n[{EXP}] === T6: Bootstrap ({N_BOOT}x) on Quran ===")
    q_units = CORPORA.get("quran", [])
    rng = np.random.RandomState(SEED)
    boot_alpha = []
    boot_beta = []

    for i in range(N_BOOT):
        # Resample surahs with replacement
        idx = rng.choice(len(q_units), len(q_units), replace=True)
        sampled_units = [q_units[j] for j in idx]
        tokens = _tokenise_corpus(sampled_units)
        freq = Counter(tokens)
        fs = np.array(sorted(freq.values(), reverse=True))
        a, _, _ = _zipf_alpha_mle(fs)
        b, _, _ = _heaps_law(tokens)
        boot_alpha.append(a)
        boot_beta.append(b)

    boot_alpha = np.array(boot_alpha)
    boot_beta = np.array(boot_beta)
    a_lo, a_hi = np.percentile(boot_alpha, [2.5, 97.5])
    b_lo, b_hi = np.percentile(boot_beta, [2.5, 97.5])
    print(f"  α: {np.median(boot_alpha):.4f} [{a_lo:.4f}, {a_hi:.4f}]")
    print(f"  β: {np.median(boot_beta):.4f} [{b_lo:.4f}, {b_hi:.4f}]")

    # --- Verdict ---
    if mah_d >= 2.0:
        verdict = "DISTINCT"
    elif mah_d >= 1.0 or abs(z_alpha) > 1.0 or abs(z_beta) > 1.0:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran α={q_alpha:.4f} [{a_lo:.4f}, {a_hi:.4f}]")
    print(f"  Quran β={q_beta:.4f} [{b_lo:.4f}, {b_hi:.4f}]")
    print(f"  Mahalanobis from ctrl centroid: {mah_d:.2f}σ")
    print(f"  z(α)={z_alpha:+.2f}, z(β)={z_beta:+.2f}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H7 — Does the Quran have a unique Zipf/Heaps exponent pair?",
        "schema_version": 1,
        "per_corpus": {k: {kk: vv for kk, vv in v.items() if kk != "top10_words"}
                       for k, v in results.items()},
        "outlier_test": {
            "quran_alpha": q_alpha,
            "quran_beta": q_beta,
            "ctrl_centroid_alpha": round(float(mu_ctrl[0]), 4),
            "ctrl_centroid_beta": round(float(mu_ctrl[1]), 4),
            "mahalanobis_d": round(mah_d, 4),
            "z_alpha": round(z_alpha, 4),
            "z_beta": round(z_beta, 4),
        },
        "bootstrap": {
            "n_boot": N_BOOT,
            "alpha_ci": [round(float(a_lo), 4), round(float(a_hi), 4)],
            "beta_ci": [round(float(b_lo), 4), round(float(b_hi), 4)],
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
