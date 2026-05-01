"""
exp65_dual_state_bic/run.py
============================
H27: Dual-State Law — Short (<=7 verses) vs Long (>7 verses) Surahs as
Distinct Ellipsoids.

Motivation
    build_pipeline_p2.py S5.2 fits separate Mahalanobis ellipsoids for
    short and long surahs, reporting +1.02 pp separation gain. This
    experiment formalises the bimodality test via Gaussian Mixture BIC.

Protocol (frozen before execution)
    T1. Compute 5-D features for all 114 Quran surahs.
    T2. Fit GMM(1) and GMM(2) on Quran 5-D features; compute
        ΔBIC = BIC(1) - BIC(2).  Positive = 2-component preferred.
    T3. Cross-corpus falsifier: same BIC test per control corpus.
        Controls (homogeneous DP-matched segments) should NOT show
        bimodality.
    T4. Report two-component centroids μ_short, μ_long and their
        Mahalanobis separation.
    T5. Threshold sensitivity: sweep cut at {5, 7, 9, 11} verses.
    T6. Identify which Quran surahs are assigned to each component by
        GMM(2) — cross-reference with verse count.

Pre-registered thresholds
    BIMODAL_STRONG:     Quran ΔBIC > 10 AND Quran ΔBIC > max(ctrl ΔBIC)
    BIMODAL_MODERATE:   Quran ΔBIC > 10
    NULL:               Quran ΔBIC <= 2

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA, FEAT_COLS, mu, S_inv

Writes ONLY under results/experiments/exp65_dual_state_bic/:
    exp65_dual_state_bic.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

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

EXP = "exp65_dual_state_bic"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

VERSE_THRESHOLDS = [5, 7, 9, 11]      # Sensitivity sweep
PRIMARY_THRESHOLD = 7                   # Legacy S5.2 cut
MIN_UNITS_FOR_GMM = 20                  # Skip corpora too small for GMM(2)
N_GMM_INIT = 10                         # Number of GMM initialisations
SEED = 42


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------
def _compute_features(units: list, corpus_name: str) -> tuple[np.ndarray, list[str], list[int]]:
    """Returns (X, labels, n_verses_list)."""
    X_list, labels, nv_list = [], [], []
    for u in units:
        if len(u.verses) < 3:
            continue
        try:
            f = ft.features_5d(u.verses)
            if np.any(np.isnan(f)) or np.any(np.isinf(f)):
                continue
            X_list.append(f)
            labels.append(u.label)
            nv_list.append(len(u.verses))
        except Exception:
            continue
    if not X_list:
        return np.empty((0, 5)), [], []
    return np.array(X_list, dtype=float), labels, nv_list


def _sort_quran_units(units: list) -> list:
    def _num(u):
        if ":" in u.label:
            try:
                return int(u.label.split(":")[1])
            except ValueError:
                return 9999
        return 9999
    return sorted(units, key=_num)


# ---------------------------------------------------------------------------
# GMM BIC helpers
# ---------------------------------------------------------------------------
def _gmm_bic_test(X: np.ndarray, n_init: int = N_GMM_INIT) -> dict:
    """Fit GMM(1) and GMM(2), return BIC comparison."""
    from sklearn.mixture import GaussianMixture

    n, d = X.shape
    gmm1 = GaussianMixture(n_components=1, covariance_type="full",
                            n_init=n_init, random_state=SEED)
    gmm1.fit(X)
    bic1 = gmm1.bic(X)

    gmm2 = GaussianMixture(n_components=2, covariance_type="full",
                            n_init=n_init, random_state=SEED)
    gmm2.fit(X)
    bic2 = gmm2.bic(X)

    delta_bic = bic1 - bic2   # positive = 2-component preferred
    labels_2 = gmm2.predict(X)

    return {
        "bic_1": float(bic1),
        "bic_2": float(bic2),
        "delta_bic": float(delta_bic),
        "n": n,
        "d": d,
        "gmm2_means": gmm2.means_.tolist(),
        "gmm2_weights": gmm2.weights_.tolist(),
        "gmm2_labels": labels_2.tolist(),
        "gmm2_converged": bool(gmm2.converged_),
    }


def _centroid_mahalanobis(mu0: np.ndarray, mu1: np.ndarray,
                          Sinv: np.ndarray) -> float:
    """Mahalanobis distance between two centroids."""
    d = mu0 - mu1
    return float(np.sqrt(d @ Sinv @ d))


def _centroid_euclidean(mu0: np.ndarray, mu1: np.ndarray) -> float:
    return float(np.linalg.norm(mu0 - mu1))


# ---------------------------------------------------------------------------
# Verse-count threshold sensitivity
# ---------------------------------------------------------------------------
def _threshold_analysis(X: np.ndarray, n_verses: list[int],
                        labels: list[str], feat_cols: list[str],
                        thresholds: list[int]) -> dict:
    """For each threshold, report short/long split and per-group stats."""
    nv = np.array(n_verses)
    results = {}
    for thr in thresholds:
        short_mask = nv <= thr
        long_mask = nv > thr
        n_short = int(short_mask.sum())
        n_long = int(long_mask.sum())

        entry = {
            "threshold": thr,
            "n_short": n_short,
            "n_long": n_long,
        }

        if n_short >= 5 and n_long >= 5:
            mu_short = X[short_mask].mean(axis=0)
            mu_long = X[long_mask].mean(axis=0)
            entry["mu_short"] = {feat_cols[i]: float(mu_short[i])
                                 for i in range(len(feat_cols))}
            entry["mu_long"] = {feat_cols[i]: float(mu_long[i])
                                for i in range(len(feat_cols))}
            entry["euclidean_dist"] = _centroid_euclidean(mu_short, mu_long)

            # Per-feature Cohen's d (short vs long)
            for i, fc in enumerate(feat_cols):
                sv = X[short_mask, i]
                lv = X[long_mask, i]
                ps = np.sqrt((sv.std(ddof=1)**2 + lv.std(ddof=1)**2) / 2)
                d = float((sv.mean() - lv.mean()) / ps) if ps > 1e-12 else 0.0
                entry[f"cohen_d_{fc}"] = round(d, 4)

        results[f"thr_{thr}"] = entry
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
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
    feat_cols = list(state["FEAT_COLS"])
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    Sinv_ctrl = np.asarray(state["S_inv"], dtype=float)
    print(f"[{EXP}] FEAT_COLS={feat_cols}")

    # --- Quran features ---
    quran_units = _sort_quran_units(CORPORA["quran"])
    X_q, q_labels, q_nv = _compute_features(quran_units, "quran")
    n_q = X_q.shape[0]
    print(f"[{EXP}] Quran: {n_q} surahs with valid features")

    # Short / long split at primary threshold
    q_nv_arr = np.array(q_nv)
    n_short = int((q_nv_arr <= PRIMARY_THRESHOLD).sum())
    n_long = int((q_nv_arr > PRIMARY_THRESHOLD).sum())
    print(f"[{EXP}] Short (≤{PRIMARY_THRESHOLD}v): {n_short}, Long (>{PRIMARY_THRESHOLD}v): {n_long}")

    # --- T2: GMM BIC test on Quran ---
    print(f"\n[{EXP}] === T2: GMM BIC test (1 vs 2 components) ===")
    q_bic = _gmm_bic_test(X_q)
    dbic_q = q_bic["delta_bic"]
    print(f"[{EXP}] Quran BIC(1)={q_bic['bic_1']:.2f}, BIC(2)={q_bic['bic_2']:.2f}")
    print(f"[{EXP}] ΔBIC = {dbic_q:.2f} ({'2-component preferred' if dbic_q > 0 else '1-component preferred'})")
    if dbic_q > 10:
        print(f"[{EXP}] ΔBIC > 10 → STRONG bimodality preference")
    elif dbic_q > 2:
        print(f"[{EXP}] ΔBIC in (2, 10] → moderate bimodality")
    else:
        print(f"[{EXP}] ΔBIC ≤ 2 → no preference for bimodality")

    # --- T4: Centroids ---
    mu0 = np.array(q_bic["gmm2_means"][0])
    mu1 = np.array(q_bic["gmm2_means"][1])
    w0 = q_bic["gmm2_weights"][0]
    w1 = q_bic["gmm2_weights"][1]
    mah_dist = _centroid_mahalanobis(mu0, mu1, Sinv_ctrl)
    euc_dist = _centroid_euclidean(mu0, mu1)
    print(f"\n[{EXP}] GMM(2) centroids:")
    print(f"  Component 0 (weight={w0:.3f}):")
    for i, fc in enumerate(feat_cols):
        print(f"    {fc:8s}: {mu0[i]:+.4f}")
    print(f"  Component 1 (weight={w1:.3f}):")
    for i, fc in enumerate(feat_cols):
        print(f"    {fc:8s}: {mu1[i]:+.4f}")
    print(f"  Mahalanobis dist between centroids: {mah_dist:.4f}")
    print(f"  Euclidean dist between centroids:   {euc_dist:.4f}")

    # Cross-reference GMM labels with verse counts
    gmm_labels = np.array(q_bic["gmm2_labels"])
    comp0_nv = q_nv_arr[gmm_labels == 0]
    comp1_nv = q_nv_arr[gmm_labels == 1]
    print(f"\n[{EXP}] GMM(2) component vs verse count:")
    print(f"  Comp 0: n={len(comp0_nv)}, median_nv={np.median(comp0_nv):.0f}, "
          f"mean_nv={comp0_nv.mean():.1f}")
    print(f"  Comp 1: n={len(comp1_nv)}, median_nv={np.median(comp1_nv):.0f}, "
          f"mean_nv={comp1_nv.mean():.1f}")

    # Agreement with threshold split
    short_mask = q_nv_arr <= PRIMARY_THRESHOLD
    # Which component is "short"? The one with lower median verse count.
    if np.median(comp0_nv) < np.median(comp1_nv):
        short_comp = 0
    else:
        short_comp = 1
    agreement = float(np.mean((gmm_labels == short_comp) == short_mask))
    print(f"  Agreement with ≤{PRIMARY_THRESHOLD}v split: {agreement*100:.1f}%")

    # --- T3: Control corpora BIC ---
    print(f"\n[{EXP}] === T3: Control corpora BIC ===")
    ctrl_bic_results = {}
    ctrl_dbics = []
    for cname in ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        X_c, c_labels, c_nv = _compute_features(units, cname)
        n_c = X_c.shape[0]
        if n_c < MIN_UNITS_FOR_GMM:
            print(f"[{EXP}] {cname:20s}: {n_c:4d} units — SKIPPED (< {MIN_UNITS_FOR_GMM})")
            ctrl_bic_results[cname] = {"n": n_c, "skipped": True}
            continue

        c_bic = _gmm_bic_test(X_c)
        dbic_c = c_bic["delta_bic"]
        ctrl_dbics.append(dbic_c)
        marker = " ≫ Quran" if dbic_c > dbic_q else ""
        print(f"[{EXP}] {cname:20s}: n={n_c:4d}  ΔBIC={dbic_c:+.2f}{marker}")
        ctrl_bic_results[cname] = {
            "n": n_c,
            "skipped": False,
            "bic_1": c_bic["bic_1"],
            "bic_2": c_bic["bic_2"],
            "delta_bic": dbic_c,
        }

    # --- T5: Threshold sensitivity ---
    print(f"\n[{EXP}] === T5: Verse-count threshold sensitivity ===")
    thr_results = _threshold_analysis(X_q, q_nv, q_labels, feat_cols, VERSE_THRESHOLDS)
    for thr in VERSE_THRESHOLDS:
        entry = thr_results[f"thr_{thr}"]
        marker = " ← PRIMARY" if thr == PRIMARY_THRESHOLD else ""
        print(f"  thr={thr}: short={entry['n_short']}, long={entry['n_long']}"
              f"  euclid={entry.get('euclidean_dist', 'N/A'):.4f}{marker}")
        if f"cohen_d_{feat_cols[0]}" in entry:
            ds = [f"{fc}={entry[f'cohen_d_{fc}']:+.2f}" for fc in feat_cols]
            print(f"    Cohen's d: {', '.join(ds)}")

    # --- Verdict ---
    max_ctrl_dbic = max(ctrl_dbics) if ctrl_dbics else 0.0

    if dbic_q > 10 and dbic_q > max_ctrl_dbic:
        verdict = "BIMODAL_STRONG"
    elif dbic_q > 10:
        verdict = "BIMODAL_MODERATE"
    elif dbic_q > 2:
        verdict = "BIMODAL_WEAK"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran ΔBIC = {dbic_q:.2f}")
    print(f"  Max control ΔBIC = {max_ctrl_dbic:.2f}")
    print(f"  Centroid Mahalanobis = {mah_dist:.4f}")
    print(f"  GMM↔threshold agreement = {agreement*100:.1f}%")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H27 — Dual-state law: are short (≤7v) and long (>7v) "
                      "Quran surahs distinct structural regimes (bimodal in 5-D)?",
        "schema_version": 1,
        "data": {
            "n_quran": n_q,
            "n_short": n_short,
            "n_long": n_long,
            "primary_threshold": PRIMARY_THRESHOLD,
            "feat_cols": feat_cols,
        },
        "T2_quran_bic": q_bic,
        "T3_control_bic": ctrl_bic_results,
        "T4_centroids": {
            "mu_comp0": mu0.tolist(),
            "mu_comp1": mu1.tolist(),
            "weights": [w0, w1],
            "mahalanobis_dist": mah_dist,
            "euclidean_dist": euc_dist,
            "short_comp": short_comp,
            "agreement_with_threshold": round(agreement, 4),
            "comp0_median_nv": float(np.median(comp0_nv)),
            "comp1_median_nv": float(np.median(comp1_nv)),
        },
        "T5_threshold_sensitivity": thr_results,
        "verdict": {
            "verdict": verdict,
            "quran_delta_bic": round(dbic_q, 2),
            "max_ctrl_delta_bic": round(max_ctrl_dbic, 2),
            "prereg_thresholds": {
                "BIMODAL_STRONG": "ΔBIC > 10 AND ΔBIC > max(ctrl ΔBIC)",
                "BIMODAL_MODERATE": "ΔBIC > 10",
                "BIMODAL_WEAK": "ΔBIC in (2, 10]",
                "NULL": "ΔBIC ≤ 2",
            },
        },
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
