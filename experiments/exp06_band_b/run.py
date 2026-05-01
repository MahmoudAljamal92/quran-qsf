"""
exp06_band_b/run.py
===================
Short-surah Band B reference experiment.

The locked pipeline's Band A covers n_verses ∈ [15, 100]. Sūrahs with
fewer than 15 verses are *excluded*, which is why exp03 found Ādiyāt
(11 verses) marginal on the 7-metric blind test — the framework was
never designed for it.

This experiment builds a **second band** (Band B: n_verses ∈ [5, 14])
with its own matched control pool, estimates μ_B and Σ_B on controls
only (avoiding circularity), and recomputes Φ_M (Mahalanobis to μ_B
under Σ_B^-1) for every Band-B Quran surah.

Protocol (locked before looking at results):
  1. Band_B_LO = 5,  Band_B_HI = 14  (inclusive).
  2. Control pool = all units in {poetry_jahili, poetry_islami,
     poetry_abbasi, ksucca, arabic_bible, hindawi} whose n_verses falls
     in [5, 14]. Hadith quarantined per preregistration.
  3. μ_B, Σ_B computed from control pool only (never Quran).
  4. Hotelling T² two-sample test Quran-B vs Ctrl-B.
  5. Report Φ_M rank of each Band-B surah vs control distribution.
  6. Report how many Quran Band-B surahs sit above the control 95th pct.

Reads (read-only):
  - phase_06_phi_m.pkl (CORPORA)

Writes ONLY under results/experiments/exp06_band_b/:
  - exp06_band_b.json
  - fig_band_b_phi_m.png
  - fig_band_a_vs_b.png
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
from scipy import stats

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src import features as ft  # noqa: E402

EXP = "exp06_band_b"

BAND_B_LO = 5
BAND_B_HI = 14
RIDGE = 1e-6

CONTROL_CORPORA = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _extract_band_b(units, lo=BAND_B_LO, hi=BAND_B_HI):
    """Return (X, labels, n_verses) for units in the band and that succeed
    in feature extraction."""
    X = []
    labels = []
    nv = []
    for u in units:
        nvu = len(u.verses)
        if not (lo <= nvu <= hi):
            continue
        try:
            f = ft.features_5d(u.verses)
            if np.all(np.isfinite(f)):
                X.append(f)
                labels.append(u.label)
                nv.append(nvu)
        except Exception:
            pass
    return np.asarray(X), np.asarray(labels), np.asarray(nv)


def _pooled_cov(X1, X2, ridge=RIDGE):
    n1, n2 = len(X1), len(X2)
    S1 = np.cov(X1, rowvar=False, ddof=1)
    S2 = np.cov(X2, rowvar=False, ddof=1)
    S = ((n1 - 1) * S1 + (n2 - 1) * S2) / (n1 + n2 - 2)
    return S + ridge * np.eye(S.shape[0])


def _hotelling_two_sample(X1, X2):
    n1, n2 = len(X1), len(X2)
    p = X1.shape[1]
    diff = X1.mean(axis=0) - X2.mean(axis=0)
    S = _pooled_cov(X1, X2)
    S_inv = np.linalg.pinv(S)
    T2 = (n1 * n2) / (n1 + n2) * float(diff @ S_inv @ diff)
    df1, df2 = p, n1 + n2 - p - 1
    F = ((n1 + n2 - p - 1) / ((n1 + n2 - 2) * p)) * T2
    p_val = float(stats.f.sf(F, df1, df2))
    logp = float(stats.f.logsf(F, df1, df2) / math.log(10))
    d_mv = math.sqrt(float(diff @ S_inv @ diff))
    return {"T2": T2, "F": F, "df1": df1, "df2": df2,
            "p_F_tail": p_val, "log10_p_F_tail": logp,
            "multivariate_cohens_d": d_mv, "n1": n1, "n2": n2}


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    feat_cols = list(phi["state"]["FEAT_COLS"])

    # Band-B Quran
    X_Q_B, labels_Q_B, nv_Q_B = _extract_band_b(CORPORA["quran"])
    # Band-B controls
    X_C_B_parts = {}
    for c in CONTROL_CORPORA:
        X_c, lbl_c, nv_c = _extract_band_b(CORPORA.get(c, []))
        X_C_B_parts[c] = X_c
    X_C_B = np.concatenate([v for v in X_C_B_parts.values() if len(v) > 0], axis=0)

    print(f"[{EXP}] Band B n_verses range = [{BAND_B_LO}, {BAND_B_HI}]")
    print(f"[{EXP}] n_Quran_B = {len(X_Q_B)}   n_Ctrl_B = {len(X_C_B)}")
    for c, v in X_C_B_parts.items():
        print(f"           {c:<18s} n = {len(v)}")

    if len(X_Q_B) < 2 or len(X_C_B) < 2:
        raise RuntimeError("Insufficient Band-B data for statistical testing.")

    # Band-B control centroid + covariance (CONTROLS ONLY — not circular)
    mu_B = X_C_B.mean(axis=0)
    S_B = np.cov(X_C_B, rowvar=False, ddof=1) + RIDGE * np.eye(X_C_B.shape[1])
    S_B_inv = np.linalg.pinv(S_B)

    # Φ_M for every Quran Band-B surah
    diff_Q = X_Q_B - mu_B[None, :]
    phi_Q = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", diff_Q, S_B_inv, diff_Q), 0))
    diff_C = X_C_B - mu_B[None, :]
    phi_C = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", diff_C, S_B_inv, diff_C), 0))

    ctrl_95 = float(np.quantile(phi_C, 0.95))
    ctrl_max = float(phi_C.max())
    n_above_95 = int(np.sum(phi_Q > ctrl_95))

    # Hotelling two-sample T² Band B
    hot = _hotelling_two_sample(X_Q_B, X_C_B)

    # mpmath refinement of p-value
    try:
        import mpmath as mp
        mp.mp.dps = 80
        F_mp = mp.mpf(hot["F"])
        df1_mp = mp.mpf(hot["df1"])
        df2_mp = mp.mpf(hot["df2"])
        x = df2_mp / (df2_mp + df1_mp * F_mp)
        sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
        hot["highprec_log10_p_F_tail"] = float(mp.log10(sf))
    except Exception as ex:
        hot["highprec_log10_p_F_tail"] = None
        hot["highprec_error"] = str(ex)

    # Rank of sūra 100 in the Band B distribution
    idx_100 = int(np.where(labels_Q_B == "Q:100")[0][0]) if "Q:100" in labels_Q_B.tolist() else None
    if idx_100 is not None:
        phi_100_B = float(phi_Q[idx_100])
        rank_100_B = int(np.sum(phi_Q > phi_100_B)) + 1
        adiyat_block = {
            "label": "Q:100",
            "phi_m_band_B": phi_100_B,
            "rank_in_quran_band_B": rank_100_B,
            "total_band_B_surahs": int(len(phi_Q)),
            "above_ctrl_95pct": bool(phi_100_B > ctrl_95),
            "ctrl_95pct_phi": ctrl_95,
        }
    else:
        adiyat_block = None

    # Per-surah listing
    per_surah = [
        {"label": str(labels_Q_B[i]), "n_verses": int(nv_Q_B[i]),
         "phi_m_band_B": float(phi_Q[i]),
         "above_ctrl_95pct": bool(phi_Q[i] > ctrl_95)}
        for i in range(len(labels_Q_B))
    ]
    per_surah.sort(key=lambda r: -r["phi_m_band_B"])

    # ---------- Plots ----------
    # Band-B Φ_M histogram
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(phi_C, bins=60, alpha=0.6, color="#999",
            label=f"Controls B (n={len(phi_C)})")
    ax.hist(phi_Q, bins=20, alpha=0.75, color="#2b8cbe",
            label=f"Quran B (n={len(phi_Q)})")
    ax.axvline(ctrl_95, color="navy", ls="--", lw=0.8,
               label=f"Ctrl 95th pct = {ctrl_95:.2f}")
    if idx_100 is not None:
        ax.axvline(phi_Q[idx_100], color="crimson", lw=2,
                   label=f"Sūra 100 = {phi_Q[idx_100]:.2f}")
    ax.set_xlabel("Φ_M (Band B: Mahalanobis to Ctrl-B centroid under Σ_B)")
    ax.set_ylabel("count")
    ax.set_title(f"Band B (n_verses ∈ [{BAND_B_LO}, {BAND_B_HI}]) — "
                 f"{n_above_95}/{len(phi_Q)} Quran surahs above control 95th pct")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_band_b_phi_m.png", dpi=130)
    plt.close(fig)

    # Band A vs Band B comparison (requires Band A — reuse locked pipeline)
    # Grab Band A X_QURAN from state
    X_Q_A = phi["state"]["X_QURAN"]
    X_C_A = phi["state"]["X_CTRL_POOL"]
    mu_A = phi["state"]["mu"]
    S_inv_A = phi["state"]["S_inv"]
    diff_A = X_Q_A - mu_A[None, :]
    phi_A = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", diff_A, S_inv_A, diff_A), 0))
    phi_A_ctrl = np.sqrt(np.maximum(np.einsum(
        "ij,jk,ik->i",
        X_C_A - mu_A[None, :], S_inv_A, X_C_A - mu_A[None, :]), 0))

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bp = ax.boxplot([phi_A_ctrl, phi_A, phi_C, phi_Q],
                    labels=["Ctrl A", "Quran A", "Ctrl B", "Quran B"],
                    patch_artist=True)
    colors_box = ["#bbb", "#2b8cbe", "#bbb", "#8cb4e8"]
    for p, c in zip(bp["boxes"], colors_box):
        p.set_facecolor(c)
    ax.set_ylabel("Φ_M")
    ax.set_title("Band A vs Band B Φ_M distributions (locked-compatible)")
    fig.tight_layout()
    fig.savefig(out / "fig_band_a_vs_b.png", dpi=130)
    plt.close(fig)

    # ---------- JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            f"Short-surah Band B (n_verses ∈ [{BAND_B_LO}, {BAND_B_HI}]) "
            "reference. μ_B and Σ_B estimated from controls only. Tests "
            "whether the 5-D framework generalises to short surahs."
        ),
        "band": {"lo": BAND_B_LO, "hi": BAND_B_HI},
        "control_corpora": CONTROL_CORPORA,
        "sizes": {"n_quran_B": int(len(X_Q_B)), "n_ctrl_B": int(len(X_C_B))},
        "mu_B_ctrl": dict(zip(feat_cols, mu_B.tolist())),
        "hotelling_two_sample": hot,
        "phi_m_distribution": {
            "ctrl_mean": float(phi_C.mean()),
            "ctrl_median": float(np.median(phi_C)),
            "ctrl_95pct": ctrl_95,
            "ctrl_max": ctrl_max,
            "quran_mean": float(phi_Q.mean()),
            "quran_median": float(np.median(phi_Q)),
            "quran_max": float(phi_Q.max()),
            "quran_above_ctrl_95pct": n_above_95,
            "quran_total": int(len(phi_Q)),
            "fraction_above_95": n_above_95 / len(phi_Q),
        },
        "per_surah_ranked": per_surah,
        "adiyat_specific": adiyat_block,
    }
    with open(out / "exp06_band_b.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console
    print(f"\n[{EXP}] === Hotelling T² Band B ===")
    print(f"  T²  = {hot['T2']:.2f}   F = {hot['F']:.3f}  df=({hot['df1']},{hot['df2']})")
    print(f"  p   = {hot['p_F_tail']:.3e}  log10 p (scipy) = {hot['log10_p_F_tail']}")
    if hot.get("highprec_log10_p_F_tail") is not None:
        print(f"  log10 p (mpmath 80-digit) = {hot['highprec_log10_p_F_tail']:.2f}")
    print(f"  multivariate Cohen's d = {hot['multivariate_cohens_d']:.3f}")
    print(f"[{EXP}] === Φ_M distribution Band B ===")
    print(f"  Ctrl mean {phi_C.mean():.2f}  95th pct {ctrl_95:.2f}  max {ctrl_max:.2f}")
    print(f"  Quran mean {phi_Q.mean():.2f}  max {phi_Q.max():.2f}")
    print(f"  Quran above ctrl 95th pct: {n_above_95}/{len(phi_Q)} "
          f"({100*n_above_95/len(phi_Q):.1f}%)")
    if adiyat_block:
        print(f"[{EXP}] Sūra 100: Φ_M_B = {phi_100_B:.2f}  "
              f"rank {rank_100_B}/{len(phi_Q)}  "
              f"above_95_pct={adiyat_block['above_ctrl_95pct']}")
    print(f"[{EXP}] wrote: {out}")
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
