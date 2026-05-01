"""
expB12_f6_6d_gate/run.py
========================
Opportunity B12 (OPPORTUNITY_TABLE_DETAIL.md):
  Test whether F6 (adjacent-verse length-coherence) qualifies as the 6th
  Phi_M channel under the same pre-registered Hotelling-T^2 gate that
  exp53_ar1_6d_gate applied to the AR(1) candidate.

Construction
    Clone of `experiments/exp53_ar1_6d_gate/run.py` with one substitution:
      - exp53: 6th feature = phi_1 from OLS AR(1) fit on per-verse word
               counts.
      - this : 6th feature = lag-1 Spearman rho on per-verse word counts
               (F6, exactly as defined in `exp24_F6_autocorr.run._spearman_lag`).

    All other parameters frozen identical to exp53 (5-D baseline, ridge,
    gate ratio 6/5, permutation_n = 10 000, seed = 42).

Pre-registered decision rule (verbatim from exp53):
    PROMOTE_6TH_CHANNEL        : T2_6D >= gate AND perm_p <= 0.01 AND
                                  per_dim_gain >= 1.0
    GATE_PASS_UNCERTAIN        : T2_6D >= gate AND perm_p > 0.01
    SIGNIFICANT_BUT_REDUNDANT  : T2_6D >= T2_5D AND perm_p <= 0.05 AND
                                  gate FAILED
    REJECT_6TH_CHANNEL         : otherwise

Reads (integrity-checked via _lib.load_phase):
    phase_06_phi_m.pkl  ->  X_QURAN, X_CTRL_POOL, CORPORA, FEATS,
                            ARABIC_CTRL_POOL, BAND_A bounds

Imports (read-only, byte-equivalent helpers from sister experiments):
    experiments.exp53_ar1_6d_gate.run._hotelling_t2  (Hotelling T^2)
    experiments.exp53_ar1_6d_gate.run._f_tail_p      (analytic F-tail)
    experiments.exp53_ar1_6d_gate.run._perm_test_t2  (permutation null)
    experiments.exp53_ar1_6d_gate.run._unit_verses
    experiments.exp44_F6_spectrum.run._verse_lengths

Writes ONLY under results/experiments/expB12_f6_6d_gate/:
    expB12_f6_6d_gate.json
    f6_distribution.png  (if matplotlib available)
"""

from __future__ import annotations

import json
import math
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
# Reuse exp53's verified Hotelling + perm helpers byte-for-byte. This is the
# single-source-of-truth pattern: any future fix in exp53 propagates here.
from experiments.exp53_ar1_6d_gate.run import (  # noqa: E402
    FIVE_D_T2_BASELINE,
    GATE_THRESHOLD,
    RIDGE_LAMBDA,
    PERMUTATION_N,
    PERMUTATION_SEED,
    _hotelling_t2,
    _f_tail_p,
    _perm_test_t2,
    _unit_verses,
)
from experiments.exp44_F6_spectrum.run import _verse_lengths  # noqa: E402

EXP = "expB12_f6_6d_gate"
EXTRA_METRIC_NAME = "f6_lag1_spearman_vlen"


def _f6_lag1_spearman(verses: list[str]) -> float:
    """Lag-1 Spearman correlation of per-verse word counts within a surah.

    Mirror of `experiments.exp24_F6_autocorr.run._spearman_lag(lens, k=1)`.
    Returns NaN if the series is too short (<3 verses) or constant.
    """
    if not verses:
        return float("nan")
    lens = _verse_lengths(verses)
    if len(lens) < 3:
        return float("nan")
    a = lens[:-1]
    b = lens[1:]
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    rho, _ = stats.spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else float("nan")


def _build_6d_rows(
    corpus_name: str,
    corpora: dict,
    feats: dict,
    band_lo: int,
    band_hi: int,
    feat_cols: list[str],
) -> tuple[np.ndarray, list[str], int]:
    """Return (X_6D, labels, n_nan) for one corpus, Band-A filtered.

    Iteration order matches exp53._build_6d_rows: records in FEATS[name]
    after the Band-A filter, paired by .label with the matching Unit in
    CORPORA[name] for the F6 computation.
    """
    units = corpora.get(corpus_name, []) or []
    by_label: dict[str, object] = {}
    for i, u in enumerate(units):
        lab = getattr(u, "label", f"_idx_{i}")
        by_label[lab] = u

    recs = [r for r in feats.get(corpus_name, []) or []
            if band_lo <= r["n_verses"] <= band_hi]

    X = np.zeros((len(recs), len(feat_cols) + 1), dtype=float)
    labels: list[str] = []
    n_nan = 0
    for i, r in enumerate(recs):
        X[i, :-1] = [r[c] for c in feat_cols]
        label = r.get("label", "")
        labels.append(label)
        u = by_label.get(label)
        if u is None:
            X[i, -1] = float("nan")
            n_nan += 1
            continue
        v = _f6_lag1_spearman(_unit_verses(u))
        if not np.isfinite(v):
            X[i, -1] = float("nan")
            n_nan += 1
        else:
            X[i, -1] = v
    return X, labels, n_nan


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load SHA-pinned state ---
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q_5D = np.asarray(state["X_QURAN"], dtype=float)
    X_C_5D = np.asarray(state["X_CTRL_POOL"], dtype=float)
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    corpora = state["CORPORA"]
    feats = state["FEATS"]

    print(f"[{EXP}] loaded  X_QURAN {X_Q_5D.shape}  X_CTRL_POOL {X_C_5D.shape}")
    print(f"[{EXP}] ctrl_pool: {ctrl_pool}")
    print(f"[{EXP}] band_A: [{band_lo}, {band_hi}]  feat_cols: {feat_cols}")

    # --- Build 6-D matrices ---
    XQ6, q_labels, q_nan = _build_6d_rows(
        "quran", corpora, feats, band_lo, band_hi, feat_cols)
    assert np.allclose(XQ6[:, :-1], X_Q_5D), (
        "Row-alignment check FAILED: 6-D Quran 5-D columns differ from "
        "phase_06 X_QURAN. Feature iteration order has drifted."
    )
    print(f"[{EXP}] XQ6 {XQ6.shape}  n_nan_6th={q_nan}")

    ctrl_parts: list[np.ndarray] = []
    ctrl_n_nan: dict[str, int] = {}
    for name in ctrl_pool:
        Xc, _labs, n_nan = _build_6d_rows(
            name, corpora, feats, band_lo, band_hi, feat_cols)
        if len(Xc) == 0:
            continue
        ctrl_parts.append(Xc)
        ctrl_n_nan[name] = n_nan
        print(f"[{EXP}]   {name:20s} {Xc.shape}  n_nan={n_nan}")
    XC6 = np.vstack(ctrl_parts)
    assert np.allclose(XC6[:, :-1], X_C_5D), (
        "Row-alignment check FAILED: 6-D CTRL_POOL 5-D columns differ from "
        "phase_06 X_CTRL_POOL."
    )
    print(f"[{EXP}] XC6 {XC6.shape}  total_n_nan={sum(ctrl_n_nan.values())}")

    q_mask = np.isfinite(XQ6[:, -1])
    c_mask = np.isfinite(XC6[:, -1])
    XQ6c = XQ6[q_mask]
    XC6c = XC6[c_mask]
    n_dropped_q = int((~q_mask).sum())
    n_dropped_c = int((~c_mask).sum())

    # --- 5-D baseline sanity re-check ---
    T2_5D, F_5D, df1_5D, df2_5D = _hotelling_t2(X_Q_5D, X_C_5D)
    p5 = _f_tail_p(F_5D, df1_5D, df2_5D)
    print(f"[{EXP}] 5-D  T^2={T2_5D:.4f}  F={F_5D:.4f}  "
          f"df=({df1_5D},{df2_5D})   locked={FIVE_D_T2_BASELINE:.4f}")

    # --- 6-D Hotelling T^2 ---
    T2_6D, F_6D, df1_6D, df2_6D = _hotelling_t2(XQ6c, XC6c)
    p6 = _f_tail_p(F_6D, df1_6D, df2_6D)
    print(f"[{EXP}] 6-D  T^2={T2_6D:.4f}  F={F_6D:.4f}  df=({df1_6D},{df2_6D})")

    # --- AUDIT: fair head-to-head 5-D vs 6-D on the SAME (F6-defined) subset ---
    # F6 is structurally undefined for constant verse-length series (poetry has
    # ~fixed meter). The 6-D matrix above drops every poetry-NaN row; the 5-D
    # baseline above used the full ctrl pool. To attribute T^2 changes to "F6
    # adds info" vs "different dataset", we recompute the 5-D T^2 on the SAME
    # subset that survives the 6-D NaN drop.
    XQ5_subset = XQ6c[:, :-1]
    XC5_subset = XC6c[:, :-1]
    T2_5D_sub, F_5D_sub, df1_5D_sub, df2_5D_sub = _hotelling_t2(
        XQ5_subset, XC5_subset)
    print(f"[{EXP}] 5-D on F6-defined subset (n_q={len(XQ5_subset)}, "
          f"n_c={len(XC5_subset)}):  T^2={T2_5D_sub:.4f}  F={F_5D_sub:.4f}")
    delta_subset = T2_6D - T2_5D_sub
    per_dim_5D_sub = T2_5D_sub / 5.0
    per_dim_gain_subset = (T2_6D / 6.0) / max(per_dim_5D_sub, 1e-12)
    print(f"[{EXP}] FAIR HEAD-TO-HEAD on subset:  "
          f"5-D T^2={T2_5D_sub:.4f}  6-D T^2={T2_6D:.4f}  "
          f"delta=+{delta_subset:.4f}  "
          f"per-dim gain ratio = {per_dim_gain_subset:.4f}")

    # --- Cohen's d on the 6th feature alone (diagnostic) ---
    f6_q = XQ6c[:, -1]
    f6_c = XC6c[:, -1]
    pool_sd = math.sqrt(
        ((len(f6_q) - 1) * f6_q.var(ddof=1)
         + (len(f6_c) - 1) * f6_c.var(ddof=1))
        / max(1, (len(f6_q) + len(f6_c) - 2))
    )
    cohen_d_f6 = (
        (f6_q.mean() - f6_c.mean()) / pool_sd if pool_sd > 1e-12
        else float("nan")
    )
    try:
        mw_p = float(stats.mannwhitneyu(
            f6_q, f6_c, alternative="greater").pvalue)
    except ValueError:
        mw_p = float("nan")

    # --- Permutation test on 6-D T^2 (primary significance test) ---
    print(f"[{EXP}] running permutation test, n_perm={PERMUTATION_N}...")
    t_perm = time.time()
    perm = _perm_test_t2(XQ6c, XC6c, n_perm=PERMUTATION_N, seed=PERMUTATION_SEED)
    print(f"[{EXP}] permutation done in {time.time()-t_perm:.1f}s  "
          f"p={perm['p_value']:.4g}  null_mean={perm['null_mean_T2']:.2f}")

    # --- Pre-registered verdict (exp53 decision rule, byte-for-byte) ---
    gate_ratio_obs = T2_6D / max(FIVE_D_T2_BASELINE, 1e-12)
    delta_T2 = T2_6D - T2_5D
    per_dim_T2_5D = T2_5D / 5.0
    per_dim_T2_6D = T2_6D / 6.0
    per_dim_gain = per_dim_T2_6D / max(per_dim_T2_5D, 1e-12)

    perm_p = perm["p_value"]
    if T2_6D >= GATE_THRESHOLD and perm_p <= 0.01 and per_dim_gain >= 1.0:
        verdict = "PROMOTE_6TH_CHANNEL"
    elif T2_6D >= GATE_THRESHOLD and perm_p > 0.01:
        verdict = "GATE_PASS_UNCERTAIN"
    elif T2_6D >= T2_5D and perm_p <= 0.05:
        verdict = "SIGNIFICANT_BUT_REDUNDANT"
    else:
        verdict = "REJECT_6TH_CHANNEL"

    # --- Optional PNG ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(f6_c, bins=40, alpha=0.5,
                label=f"Arabic control (n={len(f6_c)})",
                color="gray", density=True)
        ax.hist(f6_q, bins=20, alpha=0.7,
                label=f"Quran (n={len(f6_q)})",
                color="steelblue", density=True)
        ax.axvline(f6_q.mean(), color="steelblue", linestyle="--", linewidth=1.5,
                   label=f"Quran mean = {f6_q.mean():.3f}")
        ax.axvline(f6_c.mean(), color="gray", linestyle="--", linewidth=1.5,
                   label=f"Control mean = {f6_c.mean():.3f}")
        ax.set_xlabel("F6 = Spearman lag-1(verse-length series)")
        ax.set_ylabel("Density")
        ax.set_title(
            f"expB12 F6 distribution — Cohen d = {cohen_d_f6:+.3f}, "
            f"6-D verdict = {verdict}"
        )
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        fig.savefig(out / "f6_distribution.png", dpi=150)
        plt.close(fig)
    except ImportError:
        pass

    # --- Report ---
    report = {
        "experiment": EXP,
        "task_id": "B12",
        "schema_version": 1,
        "title": (
            "F6 length-coherence (lag-1 Spearman of verse-length series) as "
            "candidate 6th Phi_M channel under exp53's pre-registered gate."
        ),
        "prereg": {
            "extra_metric": EXTRA_METRIC_NAME,
            "ridge_lambda": RIDGE_LAMBDA,
            "gate_formula": "T2_6D >= 5D_T2 * 6/5",
            "gate_threshold": GATE_THRESHOLD,
            "five_d_T2_baseline": FIVE_D_T2_BASELINE,
            "band_A": [band_lo, band_hi],
            "control_pool": ctrl_pool,
            "permutation_n": PERMUTATION_N,
            "permutation_seed": PERMUTATION_SEED,
            "decision_rule": {
                "PROMOTE_6TH_CHANNEL":
                    "T2_6D >= gate AND perm_p <= 0.01 AND per_dim_gain >= 1.0",
                "GATE_PASS_UNCERTAIN":
                    "T2_6D >= gate AND perm_p > 0.01",
                "SIGNIFICANT_BUT_REDUNDANT":
                    "T2_6D >= T2_5D AND perm_p <= 0.05 AND gate FAILED",
                "REJECT_6TH_CHANNEL":
                    "otherwise",
            },
            "source_exp": "exp24_F6_autocorr (lag-1 Spearman, locked d ~ 0.877)",
            "template_exp": "exp53_ar1_6d_gate (byte-for-byte gate clone)",
        },
        "row_counts": {
            "n_quran_bandA": int(XQ6.shape[0]),
            "n_ctrl_bandA": int(XC6.shape[0]),
            "n_quran_dropped_nan_6th": n_dropped_q,
            "n_ctrl_dropped_nan_6th": n_dropped_c,
            "ctrl_per_corpus_nan": ctrl_n_nan,
        },
        "row_alignment_check": {
            "quran_5d_matches_phase06": True,
            "ctrl_5d_matches_phase06": True,
        },
        "five_d_sanity": {
            "T2": T2_5D,
            "F": F_5D,
            "df1": df1_5D,
            "df2": df2_5D,
            **p5,
            "locked_T2": FIVE_D_T2_BASELINE,
            "abs_delta_vs_locked": abs(T2_5D - FIVE_D_T2_BASELINE),
        },
        "six_d_hotelling": {
            "T2": T2_6D,
            "F": F_6D,
            "df1": df1_6D,
            "df2": df2_6D,
            **p6,
            "n_quran": int(XQ6c.shape[0]),
            "n_ctrl": int(XC6c.shape[0]),
            "p_dim": int(XQ6c.shape[1]),
        },
        "permutation_test": perm,
        "f6_diagnostic": {
            "quran_mean": float(f6_q.mean()),
            "quran_median": float(np.median(f6_q)),
            "quran_std": float(f6_q.std(ddof=1)),
            "ctrl_mean": float(f6_c.mean()),
            "ctrl_median": float(np.median(f6_c)),
            "ctrl_std": float(f6_c.std(ddof=1)),
            "cohen_d": float(cohen_d_f6),
            "mw_p_greater": float(mw_p),
            "n_quran": int(len(f6_q)),
            "n_ctrl": int(len(f6_c)),
        },
        "gate_verdict": {
            "verdict": verdict,
            "gate_threshold": GATE_THRESHOLD,
            "observed_T2_6D": T2_6D,
            "observed_gate_ratio_6D_over_5D": gate_ratio_obs,
            "marginal_delta_T2_6D_minus_5D": delta_T2,
            "per_dim_T2_5D": per_dim_T2_5D,
            "per_dim_T2_6D": per_dim_T2_6D,
            "per_dim_gain_ratio": per_dim_gain,
            "permutation_p_value": perm_p,
        },
        "subset_fair_head_to_head": {
            "comment": (
                "F6 is structurally undefined on constant verse-length series "
                "(classical Arabic poetry has ~fixed meter). The 6-D matrix "
                "drops every poetry NaN row, so the gate above compares "
                "5-D-on-FULL-pool vs 6-D-on-NON-POETRY-pool. This entry "
                "recomputes the 5-D T^2 on the SAME (F6-defined) subset, "
                "which is the fair head-to-head: does F6 add information "
                "CONDITIONAL on the 5 baseline channels for the units where "
                "F6 is defined?"
            ),
            "n_quran_subset": int(XQ5_subset.shape[0]),
            "n_ctrl_subset": int(XC5_subset.shape[0]),
            "T2_5D_subset": T2_5D_sub,
            "T2_6D_subset": T2_6D,
            "delta_T2_6D_minus_5D_subset": delta_subset,
            "per_dim_T2_5D_subset": per_dim_5D_sub,
            "per_dim_T2_6D_subset": T2_6D / 6.0,
            "per_dim_gain_ratio_subset": per_dim_gain_subset,
            "interpretation": (
                "If per_dim_gain_ratio_subset >= 1.0 then F6 adds information "
                "conditional on the 5 baseline channels for non-poetry "
                "controls. If < 1.0, F6 is redundant with the 5 channels on "
                "this subset. Either way, F6 cannot be promoted as a UNIVERSAL "
                "6th channel because it is undefined on poetry; only as a "
                "non-poetry-restricted channel."
            ),
        },
        "centroids": {
            "mu_QURAN_bandA_6D": XQ6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_bandA_6D": XC6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_5D_locked": mu_ctrl.tolist(),
            "feature_cols_6D": feat_cols + [EXTRA_METRIC_NAME],
        },
        "reference": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "source_experiment": "exp24_F6_autocorr",
            "template_experiment": "exp53_ar1_6d_gate",
        },
        "runtime_seconds": round(time.time() - t0, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console summary ---
    print(f"\n[{EXP}] DONE in {report['runtime_seconds']:.1f}s")
    print(f"[{EXP}] 5-D T^2 = {T2_5D:10.4f}   (locked {FIVE_D_T2_BASELINE:.4f})")
    print(f"[{EXP}] 6-D T^2 = {T2_6D:10.4f}   gate = {GATE_THRESHOLD:.4f}")
    print(f"[{EXP}] perm p  = {perm_p:.4g}  (n_perm={PERMUTATION_N})")
    print(f"[{EXP}] delta_T2 = {delta_T2:+.4f}   "
          f"per-dim gain ratio = {per_dim_gain:.4f}")
    print(f"[{EXP}] F6 Cohen d = {cohen_d_f6:+.3f}   "
          f"Quran mean={f6_q.mean():+.3f}   ctrl mean={f6_c.mean():+.3f}")
    print(f"[{EXP}] VERDICT: {verdict}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
