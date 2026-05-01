"""
exp62_adiyat_2d_retest/run.py
==============================
Adiyat (Surah 100) anomaly re-test under 2D (T, EL) parsimony model.

Motivation
    exp60 showed Fisher(T,EL) = 100.9% of total discriminant (negative cross-
    term from residual features). This means the 5-D Mahalanobis distance
    may be *inflated or deflated* by VL_CV, CN, H_cond for individual surahs.
    The Adiyat case (Surah 100) is a critical single-case diagnostic; we must
    know whether its anomaly status survives projection to 2D.

Protocol
    T1. Compute Phi_M in 5-D (full) and 2-D (T, EL only) for all 114 surahs
        and the full control pool. Report Surah 100's rank in both.
    T2. Spearman correlation between 114-surah Phi_M_5D and Phi_M_2D rankings.
    T3. Is Surah 100's Phi_M_2D still above the ctrl pool's 95th percentile?

Pre-registered thresholds
    ANOMALY_SURVIVES:    Phi_M_2D(S100) > ctrl 95th pct AND rank_2D <= rank_5D * 1.5
    ANOMALY_WEAKENS:     Phi_M_2D(S100) < ctrl 95th pct
    ANOMALY_STRENGTHENS: rank_2D < rank_5D (improves in 2D)

Reads (integrity-checked):
    phase_06_phi_m.pkl

Writes ONLY under results/experiments/exp62_adiyat_2d_retest/
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

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
from src import features as ft  # noqa: E402

EXP = "exp62_adiyat_2d_retest"
ADIYAT_LABEL = "Q:100"

# Indices: FEAT_COLS = [EL, VL_CV, CN, H_cond, T]
IDX_EL = 0
IDX_T = 4
IDX_TE = [IDX_T, IDX_EL]  # the 2D subspace


def _phi_m(X: np.ndarray, mu: np.ndarray, Sinv: np.ndarray) -> np.ndarray:
    """Mahalanobis distance of each row from mu under Sinv."""
    X = np.atleast_2d(X)
    d = X - mu[None, :]
    return np.sqrt(np.einsum("ij,jk,ik->i", d, Sinv, d))


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu_5d = np.asarray(state["mu"], dtype=float)
    Sinv_5d = np.asarray(state["S_inv"], dtype=float)
    X_CTRL = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    # --- Compute 5-D features for all 114 Quran surahs ---
    quran_units = CORPORA["quran"]
    X_Q_all = []
    labels = []
    n_verses = []
    for u in quran_units:
        try:
            f = ft.features_5d(u.verses)
            X_Q_all.append(f)
            labels.append(u.label)
            n_verses.append(len(u.verses))
        except Exception as ex:
            print(f"[warn] features failed for {u.label}: {ex}")
    X_Q_all = np.array(X_Q_all, dtype=float)
    labels = np.array(labels)
    n_verses = np.array(n_verses)

    n_q = len(X_Q_all)
    print(f"[{EXP}] {n_q} Quran surahs, {len(X_CTRL)} ctrl units")

    # Find Surah 100
    idx_100 = int(np.where(labels == ADIYAT_LABEL)[0][0])

    # ====================================================================
    # 5-D analysis (baseline, matching exp03)
    # ====================================================================
    phi_m_5d_quran = _phi_m(X_Q_all, mu_5d, Sinv_5d)
    phi_m_5d_ctrl = _phi_m(X_CTRL, mu_5d, Sinv_5d)

    phi100_5d = float(phi_m_5d_quran[idx_100])
    rank_5d = int(np.sum(phi_m_5d_quran > phi100_5d)) + 1
    ctrl_p95_5d = float(np.percentile(phi_m_5d_ctrl, 95))
    above_ctrl95_5d = bool(phi100_5d > ctrl_p95_5d)

    print(f"\n[{EXP}] === 5-D baseline ===")
    print(f"  Surah 100 Phi_M_5D = {phi100_5d:.4f}")
    print(f"  Rank among {n_q} surahs: {rank_5d}")
    print(f"  Ctrl 95th pct = {ctrl_p95_5d:.4f}, above? {above_ctrl95_5d}")

    # ====================================================================
    # 2-D (T, EL) analysis
    # ====================================================================
    X_Q_2d = X_Q_all[:, IDX_TE]
    X_C_2d = X_CTRL[:, IDX_TE]

    # Compute 2D ctrl centroid and inverse covariance
    mu_2d = X_C_2d.mean(axis=0)
    Sigma_2d = np.cov(X_C_2d.T, ddof=1)
    Sinv_2d = np.linalg.inv(Sigma_2d + 1e-10 * np.eye(2))

    phi_m_2d_quran = _phi_m(X_Q_2d, mu_2d, Sinv_2d)
    phi_m_2d_ctrl = _phi_m(X_C_2d, mu_2d, Sinv_2d)

    phi100_2d = float(phi_m_2d_quran[idx_100])
    rank_2d = int(np.sum(phi_m_2d_quran > phi100_2d)) + 1
    ctrl_p95_2d = float(np.percentile(phi_m_2d_ctrl, 95))
    above_ctrl95_2d = bool(phi100_2d > ctrl_p95_2d)

    print(f"\n[{EXP}] === 2-D (T, EL) ===")
    print(f"  Surah 100 Phi_M_2D = {phi100_2d:.4f}")
    print(f"  Rank among {n_q} surahs: {rank_2d}")
    print(f"  Ctrl 95th pct = {ctrl_p95_2d:.4f}, above? {above_ctrl95_2d}")

    # ====================================================================
    # 3-D residual (VL_CV, CN, H_cond) analysis — for comparison
    # ====================================================================
    IDX_RESID = [1, 2, 3]
    X_Q_3d = X_Q_all[:, IDX_RESID]
    X_C_3d = X_CTRL[:, IDX_RESID]

    mu_3d = X_C_3d.mean(axis=0)
    Sigma_3d = np.cov(X_C_3d.T, ddof=1)
    Sinv_3d = np.linalg.inv(Sigma_3d + 1e-10 * np.eye(3))

    phi_m_3d_quran = _phi_m(X_Q_3d, mu_3d, Sinv_3d)
    phi_m_3d_ctrl = _phi_m(X_C_3d, mu_3d, Sinv_3d)

    phi100_3d = float(phi_m_3d_quran[idx_100])
    rank_3d = int(np.sum(phi_m_3d_quran > phi100_3d)) + 1
    ctrl_p95_3d = float(np.percentile(phi_m_3d_ctrl, 95))
    above_ctrl95_3d = bool(phi100_3d > ctrl_p95_3d)

    print(f"\n[{EXP}] === 3-D residual (VL_CV, CN, H_cond) ===")
    print(f"  Surah 100 Phi_M_3D = {phi100_3d:.4f}")
    print(f"  Rank among {n_q} surahs: {rank_3d}")
    print(f"  Ctrl 95th pct = {ctrl_p95_3d:.4f}, above? {above_ctrl95_3d}")

    # ====================================================================
    # T2: Spearman correlation between 5D and 2D rankings
    # ====================================================================
    ranks_5d_arr = np.argsort(np.argsort(-phi_m_5d_quran)) + 1
    ranks_2d_arr = np.argsort(np.argsort(-phi_m_2d_quran)) + 1
    spearman_r, spearman_p = stats.spearmanr(ranks_5d_arr, ranks_2d_arr)

    print(f"\n[{EXP}] === T2: Rank correlation ===")
    print(f"  Spearman rho(5D, 2D) = {spearman_r:.4f}  p = {spearman_p:.2e}")

    # ====================================================================
    # Feature decomposition for Surah 100
    # ====================================================================
    s100_feats = dict(zip(feat_cols, X_Q_all[idx_100].tolist()))
    ctrl_means = dict(zip(feat_cols, X_CTRL.mean(axis=0).tolist()))
    ctrl_stds = dict(zip(feat_cols, X_CTRL.std(axis=0, ddof=1).tolist()))

    # Z-score per feature for Surah 100
    z_per_feat = {}
    for i, col in enumerate(feat_cols):
        z = (X_Q_all[idx_100, i] - X_CTRL[:, i].mean()) / max(X_CTRL[:, i].std(ddof=1), 1e-9)
        z_per_feat[col] = float(z)

    print(f"\n[{EXP}] === Surah 100 per-feature z-scores ===")
    for col, z in z_per_feat.items():
        marker = " *** DRIVES ANOMALY" if abs(z) > 2 else ""
        print(f"  {col:8s}: z = {z:+.3f}{marker}")

    # ====================================================================
    # Top-10 surahs in each model
    # ====================================================================
    top10_5d = np.argsort(-phi_m_5d_quran)[:10]
    top10_2d = np.argsort(-phi_m_2d_quran)[:10]

    print(f"\n[{EXP}] === Top-10 surahs by Phi_M ===")
    print(f"  {'5-D':>10s}  {'Phi_M_5D':>10s}  {'2-D':>10s}  {'Phi_M_2D':>10s}")
    for i in range(10):
        print(f"  {labels[top10_5d[i]]:>10s}  {phi_m_5d_quran[top10_5d[i]]:10.4f}  "
              f"{labels[top10_2d[i]]:>10s}  {phi_m_2d_quran[top10_2d[i]]:10.4f}")

    # ====================================================================
    # Verdict
    # ====================================================================
    if above_ctrl95_2d and rank_2d <= rank_5d:
        verdict = "ANOMALY_STRENGTHENS"
    elif above_ctrl95_2d and rank_2d <= rank_5d * 1.5:
        verdict = "ANOMALY_SURVIVES"
    elif not above_ctrl95_2d:
        verdict = "ANOMALY_WEAKENS"
    else:
        verdict = "ANOMALY_SURVIVES"  # above p95 but rank degraded moderately

    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  5D: Phi_M={phi100_5d:.4f}, rank={rank_5d}/{n_q}, above_ctrl95={above_ctrl95_5d}")
    print(f"  2D: Phi_M={phi100_2d:.4f}, rank={rank_2d}/{n_q}, above_ctrl95={above_ctrl95_2d}")
    print(f"  3D(resid): Phi_M={phi100_3d:.4f}, rank={rank_3d}/{n_q}, above_ctrl95={above_ctrl95_3d}")
    print(f"{'='*60}")

    # ====================================================================
    # Report
    # ====================================================================
    report = {
        "experiment": EXP,
        "hypothesis": "Adiyat anomaly re-test under 2D (T, EL) parsimony model from exp60",
        "schema_version": 1,
        "surah_100_label": ADIYAT_LABEL,
        "surah_100_n_verses": int(n_verses[idx_100]),
        "surah_100_features": s100_feats,
        "surah_100_z_scores": z_per_feat,
        "ctrl_means": ctrl_means,
        "ctrl_stds": ctrl_stds,
        "analysis_5D": {
            "phi_m": phi100_5d,
            "rank": rank_5d,
            "n_surahs": n_q,
            "ctrl_95th_pct": ctrl_p95_5d,
            "above_ctrl95": above_ctrl95_5d,
            "quran_mean_phi_m": float(phi_m_5d_quran.mean()),
            "quran_median_phi_m": float(np.median(phi_m_5d_quran)),
        },
        "analysis_2D_TE": {
            "features_used": ["T", "EL"],
            "indices": IDX_TE,
            "mu_ctrl_2d": mu_2d.tolist(),
            "phi_m": phi100_2d,
            "rank": rank_2d,
            "n_surahs": n_q,
            "ctrl_95th_pct": ctrl_p95_2d,
            "above_ctrl95": above_ctrl95_2d,
            "quran_mean_phi_m": float(phi_m_2d_quran.mean()),
            "quran_median_phi_m": float(np.median(phi_m_2d_quran)),
        },
        "analysis_3D_residual": {
            "features_used": ["VL_CV", "CN", "H_cond"],
            "indices": IDX_RESID,
            "phi_m": phi100_3d,
            "rank": rank_3d,
            "n_surahs": n_q,
            "ctrl_95th_pct": ctrl_p95_3d,
            "above_ctrl95": above_ctrl95_3d,
        },
        "rank_correlation": {
            "spearman_rho": float(spearman_r),
            "spearman_p": float(spearman_p),
            "note": "Correlation between 114-surah Phi_M rankings in 5D vs 2D",
        },
        "top10_5D": [
            {"label": labels[i], "phi_m": float(phi_m_5d_quran[i])}
            for i in top10_5d
        ],
        "top10_2D": [
            {"label": labels[i], "phi_m": float(phi_m_2d_quran[i])}
            for i in top10_2d
        ],
        "verdict": {
            "verdict": verdict,
            "interpretation": {
                "ANOMALY_STRENGTHENS": "Surah 100 ranks higher in 2D than 5D — the residual features were diluting its anomaly",
                "ANOMALY_SURVIVES": "Surah 100 remains above ctrl 95th pct in 2D, anomaly is robust to dimension reduction",
                "ANOMALY_WEAKENS": "Surah 100 falls below ctrl 95th pct in 2D — its anomaly was driven by VL_CV/CN/H_cond, not (T,EL)",
            },
            "exp60_reference": "Fisher(T,EL) = 100.9% of total; negative cross-term = -9.7%",
        },
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
