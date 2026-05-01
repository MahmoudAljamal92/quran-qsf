"""
exp53_ar1_6d_gate/run.py
========================
Pre-registered 6-D Hotelling T^2 gate with AR(1) phi_1 on verse-length
as the 6th candidate channel.

Construction
    Clones exp49_6d_hotelling verbatim. Only the 6th feature is swapped:
      - exp49: n_communities (greedy-modularity count on verse-transition graph).
      - exp53: phi_1 from OLS AR(1) fit on the mean-centred per-verse
               word-count sequence (same fit as exp44_F6_spectrum._ar_fit).

Pre-registration
    experiments/exp53_ar1_6d_gate/PREREG.md
    Frozen before execution. Thresholds, falsifier, and inputs listed there
    and implemented below verbatim.

Reads (integrity-checked via _lib.load_phase):
    phase_06_phi_m.pkl -> state (X_QURAN, X_CTRL_POOL, CORPORA, FEATS,
                                 ARABIC_CTRL_POOL, BAND_A bounds)

Imports (from the experiments tree; never modified by this script):
    experiments.exp44_F6_spectrum.run._ar_fit

Writes ONLY under results/experiments/exp53_ar1_6d_gate/:
    exp53_ar1_6d_gate.json
    phi1_distribution.png
    self_check_<ts>.json

Runtime: ~3-8 min (AR(1) OLS is O(n_verses) per unit; permutation test
         is 10 000 shuffles).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

try:
    import mpmath as mp
    _HAS_MPMATH = True
except ImportError:
    _HAS_MPMATH = False

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
# Re-use exp44's AR(1) fitter verbatim to guarantee method equivalence.
from experiments.exp44_F6_spectrum.run import _ar_fit, _verse_lengths  # noqa: E402


EXP = "exp53_ar1_6d_gate"

# Pre-registered gate parameters (frozen before any run).
FIVE_D_T2_BASELINE = 3557.339454504635     # phase_07 locked, matches exp49
GATE_RATIO = 6.0 / 5.0                     # dimension-penalty factor
GATE_THRESHOLD = FIVE_D_T2_BASELINE * GATE_RATIO   # = 4268.8...
RIDGE_LAMBDA = 1e-6
EXTRA_METRIC_NAME = "phi1_ar1_vlen"
PERMUTATION_N = 10_000
PERMUTATION_SEED = 42


# --------------------------------------------------------------------------- #
# 6th feature: AR(1) phi_1 on verse-length series                              #
# --------------------------------------------------------------------------- #
def _phi1_ar1_vlen(verses: list[str]) -> float:
    """Return AR(1) phi_1 OLS coefficient on per-verse word-count sequence.

    Returns NaN if the series is too short (<= 3 verses) or the fit fails.
    Uses exp44's _ar_fit with p=1 to guarantee method equivalence.
    """
    if not verses:
        return float("nan")
    lens = _verse_lengths(verses)
    if len(lens) < 4:
        return float("nan")
    coefs = _ar_fit(lens, p=1)
    if not np.isfinite(coefs[0]):
        return float("nan")
    return float(coefs[0])


def _unit_verses(u) -> list[str]:
    vs = getattr(u, "verses", None)
    if vs is None:
        return []
    if isinstance(vs, (list, tuple)):
        return [str(v) for v in vs]
    if isinstance(vs, str):
        return vs.splitlines()
    try:
        return [str(v) for v in vs]
    except Exception:
        return []


# --------------------------------------------------------------------------- #
# Hotelling T^2 (byte-exact copy of exp49._hotelling_t2)                       #
# --------------------------------------------------------------------------- #
def _hotelling_t2(XA: np.ndarray, XB: np.ndarray,
                  ridge: float = RIDGE_LAMBDA) -> tuple[float, float, int, int]:
    nA, p = XA.shape
    nB = XB.shape[0]
    mA, mB = XA.mean(0), XB.mean(0)
    SA = np.cov(XA.T, ddof=1)
    SB = np.cov(XB.T, ddof=1)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / max(1, (nA + nB - 2))
    Spi = np.linalg.inv(Sp + ridge * np.eye(p))
    diff = mA - mB
    T2 = float((nA * nB / (nA + nB)) * diff @ Spi @ diff)
    df1, df2 = p, nA + nB - p - 1
    F = ((nA + nB - p - 1) / ((nA + nB - 2) * p)) * T2
    return T2, float(F), int(df1), int(df2)


def _f_tail_p(F: float, df1: int, df2: int) -> dict:
    p_val = float(stats.f.sf(F, df1, df2))
    scipy_log10 = float(stats.f.logsf(F, df1, df2) / math.log(10))
    hp_log10 = None
    hp_dps = None
    if _HAS_MPMATH and (not math.isfinite(scipy_log10) or p_val == 0.0):
        hp_dps = 80
        mp.mp.dps = hp_dps
        F_mp = mp.mpf(F)
        df1_mp = mp.mpf(df1)
        df2_mp = mp.mpf(df2)
        x = df2_mp / (df2_mp + df1_mp * F_mp)
        sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
        hp_log10 = float(mp.log10(sf))
    return {
        "p_F_tail": p_val,
        "scipy_log10_p_F_tail": scipy_log10,
        "highprec_log10_p_F_tail": hp_log10,
        "highprec_dps": hp_dps,
    }


# --------------------------------------------------------------------------- #
# Permutation test on 6-D T^2                                                  #
# --------------------------------------------------------------------------- #
def _perm_test_t2(XA: np.ndarray, XB: np.ndarray, n_perm: int = PERMUTATION_N,
                  seed: int = PERMUTATION_SEED) -> dict:
    """Two-sample permutation test on Hotelling T^2 (label shuffling).

    Returns {p_value, obs_T2, n_perm_ge_obs, null_mean, null_std}.
    """
    obs_T2, *_ = _hotelling_t2(XA, XB)
    nA = XA.shape[0]
    X = np.vstack([XA, XB])
    rng = np.random.default_rng(seed)
    idx = np.arange(X.shape[0])

    null_T2 = np.empty(n_perm, dtype=float)
    n_ge = 0
    for i in range(n_perm):
        rng.shuffle(idx)
        XA_s = X[idx[:nA]]
        XB_s = X[idx[nA:]]
        t2, *_ = _hotelling_t2(XA_s, XB_s)
        null_T2[i] = t2
        if t2 >= obs_T2:
            n_ge += 1

    # One-sided p-value with (1+n_ge)/(1+n_perm) Laplace smoothing
    p_val = (1 + n_ge) / (1 + n_perm)
    return {
        "p_value": float(p_val),
        "observed_T2": float(obs_T2),
        "n_perm": int(n_perm),
        "n_perm_ge_observed": int(n_ge),
        "null_mean_T2": float(null_T2.mean()),
        "null_std_T2": float(null_T2.std(ddof=1)),
        "null_p95_T2": float(np.percentile(null_T2, 95)),
        "null_p99_T2": float(np.percentile(null_T2, 99)),
    }


# --------------------------------------------------------------------------- #
# 6-D feature matrix builder (row-aligned with X_QURAN / X_CTRL_POOL)          #
# --------------------------------------------------------------------------- #
def _build_6d_rows(
    corpus_name: str,
    corpora: dict,
    feats: dict,
    band_lo: int,
    band_hi: int,
    feat_cols: list[str],
) -> tuple[np.ndarray, list[str], int]:
    """Return (X_6D, labels, n_nan) for one corpus, Band-A filtered.

    Iteration order exactly matches exp49's _build_6d_rows (i.e. records
    in FEATS[name] after the Band-A filter). For each record, the
    matching Unit is located in CORPORA[name] by .label and
    phi_1 AR(1) is computed on its verse-length series.
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
        v = _phi1_ar1_vlen(_unit_verses(u))
        if not np.isfinite(v):
            X[i, -1] = float("nan")
            n_nan += 1
        else:
            X[i, -1] = v
    return X, labels, n_nan


# --------------------------------------------------------------------------- #
# Pre-reg hash                                                                 #
# --------------------------------------------------------------------------- #
def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
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
    if abs(T2_5D - FIVE_D_T2_BASELINE) > 1e-9:
        print(f"[{EXP}] WARNING: 5-D baseline T^2 differs from locked value "
              f"by {abs(T2_5D - FIVE_D_T2_BASELINE):.3e}")

    # --- 6-D Hotelling T^2 ---
    T2_6D, F_6D, df1_6D, df2_6D = _hotelling_t2(XQ6c, XC6c)
    p6 = _f_tail_p(F_6D, df1_6D, df2_6D)
    print(f"[{EXP}] 6-D  T^2={T2_6D:.4f}  F={F_6D:.4f}  df=({df1_6D},{df2_6D})")

    # --- Cohen's d on the 6th feature alone (diagnostic) ---
    phi1_q = XQ6c[:, -1]
    phi1_c = XC6c[:, -1]
    pool_sd = math.sqrt(
        ((len(phi1_q) - 1) * phi1_q.var(ddof=1)
         + (len(phi1_c) - 1) * phi1_c.var(ddof=1))
        / max(1, (len(phi1_q) + len(phi1_c) - 2))
    )
    cohen_d_phi1 = (
        (phi1_q.mean() - phi1_c.mean()) / pool_sd if pool_sd > 1e-12
        else float("nan")
    )
    try:
        mw_p = float(stats.mannwhitneyu(
            phi1_q, phi1_c, alternative="greater").pvalue)
    except ValueError:
        mw_p = float("nan")

    # --- Permutation test on 6-D T^2 (primary significance test) ---
    print(f"[{EXP}] running permutation test, n_perm={PERMUTATION_N}...")
    t_perm = time.time()
    perm = _perm_test_t2(XQ6c, XC6c, n_perm=PERMUTATION_N, seed=PERMUTATION_SEED)
    print(f"[{EXP}] permutation done in {time.time()-t_perm:.1f}s  "
          f"p={perm['p_value']:.4g}  null_mean={perm['null_mean_T2']:.2f}")

    # --- Pre-registered verdict ---
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
        ax.hist(phi1_c, bins=40, alpha=0.5, label=f"Arabic control (n={len(phi1_c)})",
                color="gray", density=True)
        ax.hist(phi1_q, bins=20, alpha=0.7, label=f"Quran (n={len(phi1_q)})",
                color="steelblue", density=True)
        ax.axvline(phi1_q.mean(), color="steelblue", linestyle="--", linewidth=1.5,
                   label=f"Quran mean = {phi1_q.mean():.3f}")
        ax.axvline(phi1_c.mean(), color="gray", linestyle="--", linewidth=1.5,
                   label=f"Control mean = {phi1_c.mean():.3f}")
        ax.set_xlabel("phi_1 (AR(1) coefficient on verse-length series)")
        ax.set_ylabel("Density")
        ax.set_title(
            f"exp53 AR(1) phi_1 distribution — Cohen's d = {cohen_d_phi1:+.3f}, "
            f"6-D verdict = {verdict}"
        )
        ax.legend(loc="upper right", fontsize=9)
        plt.tight_layout()
        fig.savefig(out / "phi1_distribution.png", dpi=150)
        plt.close(fig)
    except ImportError:
        pass

    # --- Report ---
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_hash": _prereg_hash(),
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
                "PROMOTE_6TH_CHANNEL": "T2_6D >= gate AND perm_p <= 0.01 AND per_dim_gain >= 1.0",
                "GATE_PASS_UNCERTAIN": "T2_6D >= gate AND perm_p > 0.01",
                "SIGNIFICANT_BUT_REDUNDANT": "T2_6D >= T2_5D AND perm_p <= 0.05 AND gate FAILED",
                "REJECT_6TH_CHANNEL": "otherwise",
            },
            "source_exp": "exp44_F6_spectrum (AR(1) lag-1 Cohen's d = +0.79)",
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
        "phi1_ar1_diagnostic": {
            "quran_mean": float(phi1_q.mean()),
            "quran_median": float(np.median(phi1_q)),
            "quran_std": float(phi1_q.std(ddof=1)),
            "ctrl_mean": float(phi1_c.mean()),
            "ctrl_median": float(np.median(phi1_c)),
            "ctrl_std": float(phi1_c.std(ddof=1)),
            "cohen_d": float(cohen_d_phi1),
            "mw_p_greater": float(mw_p),
            "n_quran": int(len(phi1_q)),
            "n_ctrl": int(len(phi1_c)),
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
        "centroids": {
            "mu_QURAN_bandA_6D": XQ6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_bandA_6D": XC6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_5D_locked": mu_ctrl.tolist(),
            "feature_cols_6D": feat_cols + [EXTRA_METRIC_NAME],
        },
        "reference": {
            "prereg_doc": "experiments/exp53_ar1_6d_gate/PREREG.md",
            "input_checkpoint": "phase_06_phi_m.pkl",
            "source_experiment": "exp44_F6_spectrum",
            "template_experiment": "exp49_6d_hotelling",
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
    print(f"[{EXP}] phi_1 Cohen's d = {cohen_d_phi1:+.3f}  "
          f"Quran mean={phi1_q.mean():.3f}  ctrl mean={phi1_c.mean():.3f}")
    print(f"[{EXP}] VERDICT: {verdict}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
