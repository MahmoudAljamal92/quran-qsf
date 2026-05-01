"""
exp02_mi_criticality/run.py
===========================
Long-range mutual-information decay: a criticality / scaling test
(Lin & Tegmark 2017, "Critical Behavior in Physics and Probabilistic
Formal Languages", Entropy 19, 299).

For a tokenised sequence X_1, X_2, ..., X_N, define the τ-lagged MI:

    I(τ) = H(X_t) + H(X_{t+τ}) - H(X_t, X_{t+τ})
         = H(X) + H(X) - H(X, X_τ)            (stationarity)

Empirical behaviour:
  - Random / Markov chain:           I(τ) ~ exp(−τ/ξ)   (finite-range, ξ).
  - Critical (Ising, natural lang):  I(τ) ~ A · τ^(−α)  (power law).

Lin & Tegmark argued that natural language fits power-law better than
exponential, indicating near-critical statistics. Here we ask a sharper
question: **among band-matched Arabic corpora, does the Quran's I(τ)
decay differ systematically from controls?**

Protocol
--------
For each Arabic corpus (excluding quarantined hadith):
  1. Flatten all units into one character sequence (diacritics stripped,
     only 28-letter alphabet kept).
  2. Truncate all corpora to the same length L_trunc = min length across
     corpora (fair comparison — the longer corpora are not advantaged).
  3. For τ ∈ {1, 2, 4, 8, 16, 32, 64, 128, 256}, compute plug-in MI with
     Miller-Madow correction on the 2-D (X, X_τ) histogram.
  4. Fit BOTH decay models in least-squares on log-transformed I(τ):
        power-law:    log I  =  log A − α · log τ
        exponential:  log I  =  log B − τ / ξ
  5. Report R² for each, α, ξ, and the AIC-based winning model per corpus.

Reads (read-only):
  - phase_06_phi_m.pkl   (CORPORA — canonical tokenised units)

Writes ONLY under results/experiments/exp02_mi_criticality/:
  - exp02_mi_criticality.json
  - fig_mi_decay_loglog.png
  - fig_mi_decay_semilog.png
  - fig_model_comparison_aic.png
  - self_check_<ts>.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src import features as ft  # noqa: E402

EXP = "exp02_mi_criticality"

# Arabic 28-letter alphabet we keep. Other characters drop.
ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي") + ["ء", "ى"]
LETTER2IDX = {c: i for i, c in enumerate(ARABIC_28)}
N_ALPHA = len(ARABIC_28)

# Τ-grid: log-spaced up to 256.
TAU_GRID = [1, 2, 4, 8, 16, 32, 64, 128, 256]

# Arabic corpora to include (exclude quarantined hadith).
CORPORA_LIST = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _encode(text: str) -> np.ndarray:
    """Strip diacritics, drop non-Arabic letters, map to 0..27."""
    s = ft._strip_d(text)
    out = np.empty(len(s), dtype=np.int16)
    k = 0
    for ch in s:
        if ch in LETTER2IDX:
            out[k] = LETTER2IDX[ch]
            k += 1
    return out[:k]


def _mi_lag(seq: np.ndarray, tau: int, n_alpha: int) -> float:
    """Plug-in MI with Miller-Madow bias correction on the 2-D (X, X_τ)
    histogram."""
    x = seq[:-tau]
    y = seq[tau:]
    n = len(x)
    if n < 50:
        return 0.0
    # 2-D joint histogram
    joint = np.zeros((n_alpha, n_alpha), dtype=np.int64)
    np.add.at(joint, (x, y), 1)
    px = joint.sum(axis=1) / n
    py = joint.sum(axis=0) / n
    pxy = joint / n

    def H(p: np.ndarray) -> float:
        p = p[p > 0]
        return float(-(p * np.log2(p)).sum())

    Hx = H(px)
    Hy = H(py)
    Hxy = H(pxy.ravel())
    I = Hx + Hy - Hxy
    # Miller-Madow correction (subtracts positive bias term)
    k_x = int((px > 0).sum())
    k_y = int((py > 0).sum())
    k_xy = int((pxy > 0).sum())
    bias_corr = (k_xy - k_x - k_y + 1) / (2 * n * math.log(2))
    I_corr = I - bias_corr
    # Can't be negative after correction — clip to 0
    return max(I_corr, 0.0)


def _fit_power_law(tau: np.ndarray, I: np.ndarray) -> dict:
    """log I = log A − α log τ, weighted least squares in log-log space."""
    mask = I > 0
    if mask.sum() < 3:
        return {"alpha": None, "A": None, "R2": None, "residual_rms": None}
    x = np.log(tau[mask])
    y = np.log(I[mask])
    # ordinary least squares
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    return {
        "alpha": float(-slope),
        "A": float(math.exp(intercept)),
        "R2": R2,
        "residual_rms": float(math.sqrt(ss_res / mask.sum())),
        "n_points": int(mask.sum()),
    }


def _fit_exponential(tau: np.ndarray, I: np.ndarray) -> dict:
    """log I = log B − τ/ξ, OLS in semi-log space."""
    mask = I > 0
    if mask.sum() < 3:
        return {"xi": None, "B": None, "R2": None, "residual_rms": None}
    x = tau[mask].astype(float)
    y = np.log(I[mask])
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    xi = -1.0 / slope if slope < 0 else None
    return {
        "xi": float(xi) if xi is not None else None,
        "B": float(math.exp(intercept)),
        "R2": R2,
        "residual_rms": float(math.sqrt(ss_res / mask.sum())),
        "n_points": int(mask.sum()),
    }


def _aic(n: int, rss: float, k: int) -> float:
    """AIC for least-squares regression."""
    if rss <= 0 or n <= 0:
        return float("inf")
    return n * math.log(rss / n) + 2 * k


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Encode each corpus
    enc = {}
    for c in CORPORA_LIST:
        if c not in CORPORA:
            continue
        big = "".join(" ".join(u.verses) for u in CORPORA[c])
        enc[c] = _encode(big)
        print(f"[{EXP}] {c:18s}  n_letters = {len(enc[c])}")

    # Fair-length truncation
    L_trunc = min(len(v) for v in enc.values())
    print(f"[{EXP}] L_trunc (equal for all corpora) = {L_trunc}")
    enc = {c: v[:L_trunc] for c, v in enc.items()}

    # Compute I(τ)
    I_table = {c: [] for c in enc}
    for c, seq in enc.items():
        for tau in TAU_GRID:
            if tau >= len(seq):
                I_table[c].append(0.0)
            else:
                I_table[c].append(_mi_lag(seq, tau, N_ALPHA))

    # Fit both models, per corpus
    fits = {}
    tau_arr = np.array(TAU_GRID, dtype=float)
    for c, I_list in I_table.items():
        I_arr = np.array(I_list, dtype=float)
        pl = _fit_power_law(tau_arr, I_arr)
        ex = _fit_exponential(tau_arr, I_arr)
        n = int((I_arr > 0).sum())
        k = 2
        rss_pl = (pl["residual_rms"] ** 2) * n if pl["residual_rms"] is not None else float("inf")
        rss_ex = (ex["residual_rms"] ** 2) * n if ex["residual_rms"] is not None else float("inf")
        aic_pl = _aic(n, rss_pl, k) if rss_pl != float("inf") else float("inf")
        aic_ex = _aic(n, rss_ex, k) if rss_ex != float("inf") else float("inf")
        delta_aic = aic_ex - aic_pl  # + means power-law wins
        winner = "power_law" if delta_aic > 0 else "exponential"
        fits[c] = {
            "I_of_tau": [float(x) for x in I_arr],
            "tau_grid": TAU_GRID,
            "power_law": pl,
            "exponential": ex,
            "AIC_power_law": aic_pl,
            "AIC_exponential": aic_ex,
            "delta_AIC_exp_minus_pl": delta_aic,
            "winner": winner,
        }

    # ---------- Plots ----------
    # log-log I vs τ
    fig, ax = plt.subplots(figsize=(7, 5))
    colours = plt.get_cmap("tab10")
    for i, (c, d) in enumerate(fits.items()):
        I_arr = np.array(d["I_of_tau"])
        ax.plot(TAU_GRID, np.where(I_arr > 0, I_arr, np.nan), "o-",
                color=colours(i), label=f"{c} α={d['power_law']['alpha']}" if d['power_law']['alpha'] else c,
                alpha=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("lag τ (characters)")
    ax.set_ylabel("I(X_t; X_{t+τ}) [bits]")
    ax.set_title("Lagged MI decay — log-log (straight = power law)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "fig_mi_decay_loglog.png", dpi=130)
    plt.close(fig)

    # semi-log (ln I vs τ) — straight line = exponential
    fig, ax = plt.subplots(figsize=(7, 5))
    for i, (c, d) in enumerate(fits.items()):
        I_arr = np.array(d["I_of_tau"])
        xi = d["exponential"]["xi"]
        lbl = f"{c}  ξ={xi:.1f}" if xi else c
        ax.plot(TAU_GRID, np.where(I_arr > 0, I_arr, np.nan), "o-",
                color=colours(i), label=lbl, alpha=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("lag τ (characters)")
    ax.set_ylabel("I(X_t; X_{t+τ}) [bits]")
    ax.set_title("Lagged MI decay — semi-log (straight = exponential)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "fig_mi_decay_semilog.png", dpi=130)
    plt.close(fig)

    # AIC model comparison bar plot
    fig, ax = plt.subplots(figsize=(7, 4))
    xs = list(fits.keys())
    dAIC = [fits[c]["delta_AIC_exp_minus_pl"] for c in xs]
    colors = ["#2ca02c" if d > 0 else "#d62728" for d in dAIC]
    ax.bar(range(len(xs)), dAIC, color=colors)
    for i, d in enumerate(dAIC):
        ax.text(i, d + (1 if d >= 0 else -1) * 0.5,
                f"{d:+.1f}", ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("ΔAIC = AIC_exp − AIC_pl\n(positive = power-law wins)")
    ax.set_title("Criticality model comparison per corpus")
    fig.tight_layout()
    fig.savefig(out / "fig_model_comparison_aic.png", dpi=130)
    plt.close(fig)

    # ---------- JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            "Lagged MI decay (Lin & Tegmark 2017). Tests power-law vs "
            "exponential fit of I(τ) per Arabic corpus. All corpora "
            "truncated to equal length for fairness."
        ),
        "protocol": {
            "alphabet_size": N_ALPHA,
            "tau_grid": TAU_GRID,
            "L_trunc": int(L_trunc),
            "estimator": "plug-in MI with Miller-Madow bias correction",
            "corpora_included": list(enc.keys()),
            "corpora_excluded": ["hadith_bukhari (quarantined)",
                                 "iliad_greek (different alphabet)"],
        },
        "fits": fits,
    }
    with open(out / "exp02_mi_criticality.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print(f"\n[{EXP}] === Fit summary ===")
    header = f"  {'corpus':<18s} {'α (pl)':>8s} {'R²_pl':>7s} {'ξ (exp)':>10s} {'R²_exp':>8s} {'ΔAIC':>8s} {'winner':>12s}"
    print(header)
    for c, d in fits.items():
        pl = d["power_law"]
        ex = d["exponential"]
        print(f"  {c:<18s} "
              f"{pl['alpha']:>8.3f} " if pl['alpha'] else f"  {c:<18s} {'--':>8s} "
              + f"{pl['R2']:>7.3f} " if pl['R2'] is not None else f"{'--':>7s} "
              + f"{ex['xi']:>10.2f} " if ex['xi'] else f"{'--':>10s} "
              + f"{ex['R2']:>8.3f} " if ex['R2'] is not None else f"{'--':>8s} "
              + f"{d['delta_AIC_exp_minus_pl']:>+8.2f} {d['winner']:>12s}")
    # The f-string chain above is awkward; re-do simply:
    print("")
    for c, d in fits.items():
        pl = d["power_law"]; ex = d["exponential"]
        alpha = pl["alpha"]; Rpl = pl["R2"]
        xi = ex["xi"]; Rex = ex["R2"]
        alpha_s = f"{alpha:.3f}" if alpha is not None else "  --"
        Rpl_s = f"{Rpl:.3f}" if Rpl is not None else " --"
        xi_s = f"{xi:.2f}" if xi is not None else "  --"
        Rex_s = f"{Rex:.3f}" if Rex is not None else " --"
        print(f"  {c:<18s}  α={alpha_s}  R²_pl={Rpl_s}  "
              f"ξ={xi_s}  R²_exp={Rex_s}  ΔAIC={d['delta_AIC_exp_minus_pl']:+7.2f}  "
              f"winner={d['winner']}")

    print(f"[{EXP}] wrote: {out}")
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
