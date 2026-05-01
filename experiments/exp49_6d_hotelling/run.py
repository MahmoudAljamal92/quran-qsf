"""
exp49_6d_hotelling/run.py
=========================
Pre-registered 6-D Hotelling T^2 gate for exp48 verse-graph promotion.

Motivation
    exp48 reported n_communities as the strongest surviving graph
    metric (d = +0.937, p = 1.2e-12, Quran rank 1/6). The
    pre-registered promotion rule in exp48/notes.md states:

        Add the strongest metric to the 5-D Phi_M feature vector on
        Band-A matched data and compute the 6-D Hotelling T^2 with
        the same Sigma-regularisation (1e-6 * I).

        Promote to 6th channel iff  T^2_6D >= 5-D T^2 * 6/5 = 4269.
        Otherwise label SIGNIFICANT BUT REDUNDANT.

    The 5-D T^2 baseline is 3557.34 (phase_06_phi_m, exp01_ftail).
    The gate threshold is 3557.34 * 6/5 = 4268.8. This script computes
    the 6-D T^2 and emits the pre-registered verdict.

Protocol (frozen before computation)
    1. Load X_QURAN (68 x 5) and X_CTRL_POOL (2509 x 5) from the SHA-
       pinned phase_06_phi_m checkpoint.
    2. For every Band-A Quran unit (15 <= n_verses <= 100), compute
       n_communities on the same verse-transition graph used in exp48
       (same _el_match + _length_ratio edge weights, same
       greedy_modularity_communities). Append as a 6th column in the
       same order as _X_for() so the rows stay aligned.
    3. Same for every Band-A unit in the Arabic control pool in the
       canonical ARABIC_CTRL_POOL iteration order.
    4. Two-sample Hotelling T^2 with pooled covariance + ridge 1e-6*I.
    5. Emit verdict {PROMOTE_6TH_CHANNEL | SIGNIFICANT_BUT_REDUNDANT}.

Reads (integrity-checked)
    phase_06_phi_m.pkl  ->  state (X_QURAN, X_CTRL_POOL, FEATS,
                            CORPORA, ARABIC_CTRL_POOL, BAND_A bounds)

Writes ONLY under results/experiments/exp49_6d_hotelling/

Runtime ~2-5 min (only one graph metric, so ~6x faster than exp48).
"""
from __future__ import annotations

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
from experiments.exp48_verse_graph_topology.run import (  # noqa: E402
    _el_match,
    _length_ratio,
    MIN_VERSES,
)

try:
    import networkx as nx  # noqa: E402
    _HAS_NX = True
except ImportError:
    _HAS_NX = False


EXP = "exp49_6d_hotelling"

# Pre-registered gate parameters (frozen before any run).
FIVE_D_T2_BASELINE = 3557.339454504635     # exp01_ftail / phase_07 locked
GATE_RATIO = 6.0 / 5.0                     # dimension-penalty factor
GATE_THRESHOLD = FIVE_D_T2_BASELINE * GATE_RATIO   # = 4268.8...
RIDGE_LAMBDA = 1e-6
EXTRA_METRIC_NAME = "n_communities"        # strongest exp48 metric, d=+0.937


# --------------------------------------------------------------------------- #
# Graph metric (modularity-community branch of exp48._unit_metrics)            #
# --------------------------------------------------------------------------- #
def _n_communities(verses: list[str]) -> float:
    """Return greedy_modularity_communities count on exp48's verse graph.
    Returns NaN if too few verses or networkx unavailable; returns 1.0 on
    graph-construction failure (matches exp48's own fallback)."""
    n = len(verses)
    if n < MIN_VERSES or not _HAS_NX:
        return float("nan")
    G = nx.DiGraph()
    for i in range(n):
        G.add_node(i)
    for i in range(n - 1):
        w = 0.5 * _el_match(verses[i], verses[i + 1]) \
            + 0.5 * _length_ratio(verses[i], verses[i + 1])
        G.add_edge(i, i + 1, weight=w)
        G.add_edge(i + 1, i, weight=w)
    Gu = G.to_undirected()
    try:
        communities = list(nx.community.greedy_modularity_communities(Gu))
        return float(len(communities))
    except Exception:
        return 1.0


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
# Hotelling T^2 (byte-exact copy of exp26._hotelling_t2 / _build.py Cell 29)   #
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

    Iteration order exactly matches _build.py::_X_for (i.e. the order
    records appear in FEATS[name] after the Band-A filter). For each
    record, the matching Unit is located in CORPORA[name] by .label
    and n_communities is computed on its verses.
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
        v = _n_communities(_unit_verses(u))
        if not np.isfinite(v):
            X[i, -1] = float("nan")
            n_nan += 1
        else:
            X[i, -1] = v
    return X, labels, n_nan


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not _HAS_NX:
        raise RuntimeError(
            "networkx is required for exp49. Install: pip install networkx>=3.0"
        )

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
    print(f"[{EXP}] ctrl_pool (canonical _X_for iteration order): {ctrl_pool}")

    # --- Build 6-D matrices in the canonical iteration order ---
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

    # Drop any rows with NaN in the 6th column (rare; logged in the report).
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

    # --- Pre-registered verdict ---
    if T2_6D >= GATE_THRESHOLD:
        verdict = "PROMOTE_6TH_CHANNEL"
    else:
        verdict = "SIGNIFICANT_BUT_REDUNDANT"
    gate_ratio_obs = T2_6D / max(FIVE_D_T2_BASELINE, 1e-12)
    delta_T2 = T2_6D - T2_5D
    per_dim_T2_5D = T2_5D / 5.0
    per_dim_T2_6D = T2_6D / 6.0
    per_dim_gain = per_dim_T2_6D / max(per_dim_T2_5D, 1e-12)
    mean_nc_q = float(XQ6c[:, -1].mean())
    mean_nc_c = float(XC6c[:, -1].mean())

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg": {
            "extra_metric": EXTRA_METRIC_NAME,
            "ridge_lambda": RIDGE_LAMBDA,
            "gate_formula": "T2_6D >= 5D_T2 * 6/5",
            "gate_threshold": GATE_THRESHOLD,
            "five_d_T2_baseline": FIVE_D_T2_BASELINE,
            "band_A": [band_lo, band_hi],
            "control_pool": ctrl_pool,
            "source_notes": "experiments/exp48_verse_graph_topology/notes.md",
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
            "note": (
                "First 5 columns of the 6-D matrices are byte-identical to "
                "phase_06_phi_m.X_QURAN / X_CTRL_POOL. Asserted at build "
                "time; a drift raises AssertionError."
            ),
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
        "gate_verdict": {
            "verdict": verdict,
            "gate_threshold": GATE_THRESHOLD,
            "observed_T2_6D": T2_6D,
            "observed_gate_ratio_6D_over_5D": gate_ratio_obs,
            "marginal_delta_T2_6D_minus_5D": delta_T2,
            "per_dim_T2_5D": per_dim_T2_5D,
            "per_dim_T2_6D": per_dim_T2_6D,
            "per_dim_gain_ratio": per_dim_gain,
            "interpretation": (
                "PROMOTE_6TH_CHANNEL = the n_communities column provides "
                "enough NEW multivariate separation to overcome the 6/5 "
                "dimension penalty; it is non-redundant with the 5-D Phi_M "
                "and graduates to a full 6th channel. "
                "SIGNIFICANT_BUT_REDUNDANT = signal is real (exp48 d=+0.937) "
                "but duplicates information already present in "
                "(EL, VL_CV, CN, H_cond, T); stays in the supplementary ledger."
            ),
        },
        "n_communities_means_bandA": {
            "quran": mean_nc_q,
            "ctrl_pool": mean_nc_c,
            "note": (
                "Means over rows that entered the 6-D T^2. exp48's "
                "corpus_means use ALL units with >=5 verses (not just "
                "Band-A), so the numbers are not one-to-one comparable."
            ),
        },
        "centroids": {
            "mu_QURAN_bandA_6D": XQ6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_bandA_6D": XC6c.mean(axis=0).tolist(),
            "mu_CTRL_POOL_5D_locked": mu_ctrl.tolist(),
            "feature_cols_6D": feat_cols + [EXTRA_METRIC_NAME],
        },
        "reference": {
            "prereg_doc": "experiments/exp48_verse_graph_topology/notes.md",
            "input_checkpoint": "phase_06_phi_m.pkl",
            "depends_on_exp48_verdict": "PROMOTE",
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
    print(f"[{EXP}] 6-D F   = {F_6D:10.4f}   df=({df1_6D},{df2_6D})  "
          f"p = {p6['p_F_tail']:.3e}")
    print(f"[{EXP}] delta_T2 = {delta_T2:+.4f}   "
          f"per-dim gain ratio = {per_dim_gain:.4f}")
    print(f"[{EXP}] n_communities mean  Quran={mean_nc_q:.3f}  "
          f"ctrl_pool={mean_nc_c:.3f}")
    print(f"[{EXP}] VERDICT: {verdict}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
