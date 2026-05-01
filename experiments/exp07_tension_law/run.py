"""
exp07_tension_law/run.py
========================
Tension-Asymmetry Law (Approach C) — direct test.

Claim under test (falsifiable, cross-corpus):

    P(T > 0 | corpus)  ≈  s · max(0, RD · EL − θ)

where
    RD = root_diversity = #unique verse-final roots / #verses
    EL = avg end-letter-repetition rate
    T  = H_cond(roots) − H(end-letter)   [paper §2.6]

Pre-registered hypothesis parameters (from the user's synthesis):
    θ_hat ≈ 0.17,   s_hat ≈ 60   (i.e. 0.60 per unit of (RD·EL − 0.17))

We compute (RD, EL, P(T>0)) freshly for all nine corpora using the
canonical src.features extractor, fit a linear model on the data, and
report:
  - slope s and intercept b (and threshold θ = −b/s)
  - R² of the fit
  - whether the relationship is strong (R² ≥ 0.80) — which the user
    flagged as the publishability bar
  - rank of Quran's residual (is the Quran inside the law's envelope,
    or is it an outlier even on this axis?)

Reads (read-only):
  - phase_06_phi_m.pkl    (CORPORA)
  - phase_07_core.pkl     (EL_by, pct_T_pos — for cross-check)

Writes ONLY under results/experiments/exp07_tension_law/:
  - exp07_tension_law.json
  - fig_tension_law.png
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
from src import roots as rc  # noqa: E402

EXP = "exp07_tension_law"

ARABIC_CORPORA = [
    "quran",
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
    # hadith quarantined per preregistration — still compute, flag
    "hadith_bukhari",
]

# Pre-registered hypothesis parameters (fixed before computing anything)
THETA_HAT = 0.17
S_HAT = 60.0


def _final_root(verse: str) -> str:
    v = ft._strip_d(verse).strip()
    toks = v.split()
    if not toks:
        return ""
    return rc.primary_root_normalized(toks[-1]) or "<unk>"


def _corpus_stats(units: list) -> dict:
    """Compute (EL_avg, RD, P_T_pos) aggregated over units in a corpus.

    EL_avg = mean EL over units with ≥ 2 verses
    RD = unique verse-final roots / total verses (corpus-wide)
    P_T_pos = fraction of units with T > 0 (among units for which T is
              computable, i.e. n_verses ≥ 2)
    """
    ELs = []
    Ts = []
    all_roots = []
    n_verses_total = 0
    n_units = 0
    for u in units:
        if len(u.verses) < 2:
            continue
        try:
            f = ft.features_5d(u.verses)
            if not np.all(np.isfinite(f)):
                continue
            ELs.append(float(f[0]))
            Ts.append(float(f[4]))
            for v in u.verses:
                r = _final_root(v)
                all_roots.append(r)
            n_verses_total += len(u.verses)
            n_units += 1
        except Exception:
            pass
    if n_units == 0:
        return {"EL": math.nan, "RD": math.nan, "P_T_pos": math.nan,
                "n_units": 0, "n_verses_total": 0, "T_mean": math.nan,
                "T_median": math.nan, "RD_EL": math.nan}
    EL = float(np.mean(ELs))
    # Root diversity = unique roots / total verses
    unique_roots = len(set(r for r in all_roots if r and r != "<unk>"))
    RD = unique_roots / n_verses_total if n_verses_total > 0 else 0.0
    P_T_pos = float(np.mean([1.0 if t > 0 else 0.0 for t in Ts]))
    T_mean = float(np.mean(Ts))
    T_median = float(np.median(Ts))
    return {
        "EL": EL, "RD": RD, "P_T_pos": P_T_pos,
        "n_units": n_units, "n_verses_total": n_verses_total,
        "T_mean": T_mean, "T_median": T_median,
        "RD_EL": RD * EL,
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Per-corpus aggregate stats
    stats_by = {}
    for c in ARABIC_CORPORA:
        if c not in CORPORA:
            continue
        stats_by[c] = _corpus_stats(CORPORA[c])
        s = stats_by[c]
        print(f"[{EXP}] {c:<18s}  EL={s['EL']:.3f}  RD={s['RD']:.3f}  "
              f"RD·EL={s['RD_EL']:.3f}  P(T>0)={s['P_T_pos']:.3f}  "
              f"n_units={s['n_units']:>4d}  n_verses={s['n_verses_total']:>6d}")

    # Fit linear law, with and without hadith (quarantined per preregistration)
    def _fit(keys):
        xs = np.array([stats_by[k]["RD_EL"] for k in keys])
        ys = np.array([stats_by[k]["P_T_pos"] for k in keys])
        valid = np.isfinite(xs) & np.isfinite(ys)
        xs, ys = xs[valid], ys[valid]
        if len(xs) < 3:
            return None
        slope, intercept = np.polyfit(xs, ys, 1)
        pred = slope * xs + intercept
        ss_res = float(((ys - pred) ** 2).sum())
        ss_tot = float(((ys - ys.mean()) ** 2).sum())
        R2 = 1 - ss_res / ss_tot if ss_tot > 0 else math.nan
        # Correlation coefficient
        r = float(np.corrcoef(xs, ys)[0, 1])
        # Residuals per corpus
        residuals = {k: float(stats_by[k]["P_T_pos"] - (slope * stats_by[k]["RD_EL"] + intercept))
                     for k in keys if np.isfinite(stats_by[k]["RD_EL"]) and np.isfinite(stats_by[k]["P_T_pos"])}
        return {
            "slope": float(slope),
            "intercept": float(intercept),
            "threshold_theta": float(-intercept / slope) if slope != 0 else None,
            "R2": float(R2),
            "pearson_r": r,
            "n_corpora": int(len(xs)),
            "keys_used": keys,
            "residuals": residuals,
        }

    keys_all = [k for k in ARABIC_CORPORA if k in stats_by]
    keys_no_hadith = [k for k in keys_all if k != "hadith_bukhari"]

    fit_all = _fit(keys_all)
    fit_no_hadith = _fit(keys_no_hadith)

    # Check how well the pre-registered hypothesis (s=60, θ=0.17) holds
    # i.e. residuals against P_pred = 60 * max(0, RD·EL − 0.17)
    preds_h = {}
    for k, s in stats_by.items():
        if np.isfinite(s["RD_EL"]):
            p_pred = S_HAT * max(0.0, s["RD_EL"] - THETA_HAT)
            preds_h[k] = {"P_pred_hypothesis": p_pred,
                          "P_obs": s["P_T_pos"],
                          "residual_hyp": s["P_T_pos"] - p_pred}

    # Verdict rubric
    verdict_R2 = fit_no_hadith["R2"] if fit_no_hadith else None
    if verdict_R2 is None:
        verdict = "insufficient_data"
    elif verdict_R2 >= 0.80:
        verdict = "LAW_SUPPORTED (R² ≥ 0.80 publishable bar met)"
    elif verdict_R2 >= 0.50:
        verdict = "LAW_SUGGESTIVE (R² in [0.5, 0.8); needs more corpora)"
    else:
        verdict = "LAW_FAILED (R² < 0.5 — relationship too weak to call a law)"

    # ---------- Plot ----------
    fig, ax = plt.subplots(figsize=(8, 6))
    xs_plot = np.linspace(0.0, 0.75, 100)

    # fitted line (excluding hadith)
    if fit_no_hadith is not None:
        ys_fit = fit_no_hadith["slope"] * xs_plot + fit_no_hadith["intercept"]
        ax.plot(xs_plot, ys_fit, color="crimson", lw=1.5,
                label=f"OLS fit (no hadith): P = {fit_no_hadith['slope']:.1f}·(RD·EL) + {fit_no_hadith['intercept']:+.3f}"
                      f"\n  R² = {fit_no_hadith['R2']:.3f}, θ = {fit_no_hadith['threshold_theta']:.3f}")

    # hypothesis line
    ys_h = np.array([S_HAT * max(0.0, x - THETA_HAT) for x in xs_plot])
    ax.plot(xs_plot, ys_h, color="blue", ls="--", lw=1.0,
            label=f"Hypothesis: P = {S_HAT:.0f}·max(0, RD·EL − {THETA_HAT})")

    # scatter
    for k, s in stats_by.items():
        if not np.isfinite(s["RD_EL"]):
            continue
        col = "crimson" if k == "quran" else ("grey" if k == "hadith_bukhari" else "#2b8cbe")
        mk = "*" if k == "quran" else ("x" if k == "hadith_bukhari" else "o")
        ms = 220 if k == "quran" else (90 if k == "hadith_bukhari" else 90)
        ax.scatter([s["RD_EL"]], [s["P_T_pos"]], color=col, marker=mk, s=ms,
                   edgecolor="black", linewidth=0.5, zorder=5)
        ax.annotate(k, (s["RD_EL"], s["P_T_pos"]), fontsize=8,
                    xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("RD · EL  (rhyme-diversity joint index)")
    ax.set_ylabel("P(T > 0 | unit)  (fraction of units with positive tension)")
    ax.set_title(f"Tension-Asymmetry Law (Approach C)\nVerdict: {verdict}")
    ax.set_xlim(0.0, 0.75)
    ax.set_ylim(-0.02, 0.6)
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "fig_tension_law.png", dpi=130)
    plt.close(fig)

    # ---------- JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            "Cross-corpus test of the Tension-Asymmetry Law: "
            "P(T>0) ≈ s·max(0, RD·EL − θ). Uses only data extractable "
            "from the locked CORPORA dump; nothing re-runs upstream."
        ),
        "post_hoc_baseline_hypothesis": {
            "s_hat": S_HAT, "theta_hat": THETA_HAT,
            "source": (
                "User synthesis summary, Approach C. IMPORTANT: these "
                "constants were proposed AFTER inspection of the locked "
                "per-corpus scalars and are therefore NOT pre-registered. "
                "The OLS fit reported below is the empirical test; the "
                "baseline values are shown only for reference."
            ),
        },
        "per_corpus_stats": stats_by,
        "hypothesis_check": preds_h,
        "linear_fit_all_corpora": fit_all,
        "linear_fit_excluding_hadith": fit_no_hadith,
        "verdict": verdict,
        "notes": [
            "RD is corpus-wide (unique verse-final roots / n_verses).",
            "EL is mean over units with ≥ 2 verses.",
            "P(T>0) is fraction of units with positive T (2-verse minimum).",
            "hadith_bukhari is quarantined per preregistration; fit also "
            "reported with it included for transparency.",
        ],
    }
    with open(out / "exp07_tension_law.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print(f"\n[{EXP}] === Linear fit (including hadith) ===")
    if fit_all:
        print(f"  slope={fit_all['slope']:.3f}  intercept={fit_all['intercept']:+.3f}  "
              f"θ={fit_all['threshold_theta']:.3f}  R²={fit_all['R2']:.3f}  "
              f"n_corpora={fit_all['n_corpora']}")
    print(f"[{EXP}] === Linear fit (no hadith) ===")
    if fit_no_hadith:
        print(f"  slope={fit_no_hadith['slope']:.3f}  "
              f"intercept={fit_no_hadith['intercept']:+.3f}  "
              f"θ={fit_no_hadith['threshold_theta']:.3f}  "
              f"R²={fit_no_hadith['R2']:.3f}  "
              f"n_corpora={fit_no_hadith['n_corpora']}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"[{EXP}] wrote: {out}")
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
