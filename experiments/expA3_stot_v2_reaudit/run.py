"""
expA3_stot_v2_reaudit/run.py
============================
Opportunity A3 = H23 (OPPORTUNITY_TABLE_DETAIL.md):
  Re-derive the STOT v2 (Structural Theorem of Oral Texts, version 2) 5
  conditions from `phase_06_phi_m.pkl` under the current audited pipeline
  (post-F-11 T-definition fix, post-hadith-quarantine, post-CamelTools
  root extraction). The pre-registered theorem is:

      "A text T satisfies STOT v2 iff it passes >= 4 of 5 conditions at
       BH-corrected p <= 0.01."

The 5 conditions (from `cross_language_stot_test_v2_fair.py:269-314`):
  C1 AntiMetric        : Cohen d(VL_CV, target vs ctrl) > 0.3 AND MW-p < 0.05
  C2 DualChannel       : Cohen d(EL,    target vs ctrl) > 0.3 AND MW-p < 0.05
  C3 RootDiversity     : Cohen d(H_cond,target vs ctrl) > 0.3 AND MW-p < 0.05
  C4 AntiRegularity    : Cohen d(T,     target vs ctrl) > 0.3 AND MW-p < 0.05
  C5 MinPathCost       : per-unit verse-shuffle null on EL; q_sig = fraction
                          of target units in top 5 % of their permutation
                          null; enrich = q_sig / ctrl_sig. PASS if q_sig >
                          0.3 AND enrich > 1.5.

Note on threshold conventions:
  - Code thresholds (this experiment, mirrors the legacy script byte-for-byte):
    C1-C4: d > 0.3, p < 0.05  ;  C5: q_sig > 0.3, enrich > 1.5.
  - Doc-narrative thresholds (HYPOTHESES_AND_TESTS.md:1207-1211 mention
    d > 0.50 for C2, d > 0.15 for C4, enrich > 2.0 for C5).
  Both are reported via the `pass_code_thresholds` and `pass_md_thresholds`
  fields per condition so future writing can use either.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl

Writes:
  - results/experiments/expA3_stot_v2_reaudit/expA3_stot_v2_reaudit.json
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
from src.features import el_rate  # noqa: E402

EXP = "expA3_stot_v2_reaudit"
SEED = 42
N_SHUFFLES = 200  # matches legacy default for C5 within-unit verse shuffle


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    s2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / max(
        1, len(a) + len(b) - 2
    )
    s = math.sqrt(s2)
    if s <= 1e-12:
        return float("nan")
    return float((a.mean() - b.mean()) / s)


def _mw_p_greater(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        return float(stats.mannwhitneyu(a, b, alternative="greater").pvalue)
    except ValueError:
        return float("nan")


def _c5_unit_significance(
    verses: list[str], rng: np.random.Generator, n_shuffles: int = N_SHUFFLES
) -> float:
    """Return percentile of obs el_rate within the verse-shuffle null.

    Lower percentile = higher el_rate vs shuffled order. The legacy code
    counts a "sig" hit when this percentile < 0.05 (top-5 % of nulls).
    """
    if len(verses) < 3:
        return float("nan")
    obs = el_rate(list(verses))
    nulls = np.empty(n_shuffles, dtype=float)
    arr = list(verses)
    for i in range(n_shuffles):
        rng.shuffle(arr)
        nulls[i] = el_rate(list(arr))
    return float((nulls >= obs).mean())


def _bh_fdr(pvals: list[float], alpha: float = 0.01) -> tuple[list[bool], list[float]]:
    """Benjamini-Hochberg FDR. Returns (rejected, q-values) aligned to input order."""
    pvals = list(pvals)
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    sorted_p = [pvals[i] for i in order]
    q = [0.0] * n
    # Compute q-values
    min_q = 1.0
    for k in range(n - 1, -1, -1):
        rank = k + 1
        adj = sorted_p[k] * n / rank
        if adj < min_q:
            min_q = adj
        q[order[k]] = min(min_q, 1.0)
    rejected = [qv <= alpha for qv in q]
    return rejected, q


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feat_cols = list(state["FEAT_COLS"])
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    corpora = state["CORPORA"]

    print(f"[{EXP}] feat_cols: {feat_cols}")
    print(f"[{EXP}] band_A: [{band_lo}, {band_hi}]")
    print(f"[{EXP}] X_QURAN {X_Q.shape}   X_CTRL_POOL {X_C.shape}")
    print(f"[{EXP}] ctrl_pool members: {ctrl_pool}")

    # Column indices
    idx = {c: feat_cols.index(c) for c in ("EL", "VL_CV", "CN", "H_cond", "T")}

    # ---- C1-C4: per-feature Cohen d + MW p (Quran higher) ----
    conditions = []

    def _record(label: str, feat: str, d_thresh_code: float, d_thresh_md: float,
                p_thresh: float = 0.05) -> dict:
        a = X_Q[:, idx[feat]]
        b = X_C[:, idx[feat]]
        d = _cohens_d(a, b)
        p = _mw_p_greater(a, b)
        rec = {
            "id": label,
            "feature": feat,
            "n_target": int(len(a)),
            "n_control": int(len(b)),
            "cohen_d_target_minus_control": d,
            "mannwhitney_p_one_sided_greater": p,
            "code_threshold_d": d_thresh_code,
            "code_threshold_p": p_thresh,
            "md_threshold_d": d_thresh_md,
            "pass_code_thresholds": bool(
                math.isfinite(d) and math.isfinite(p) and d > d_thresh_code and p < p_thresh
            ),
            "pass_md_thresholds": bool(
                math.isfinite(d) and math.isfinite(p) and d > d_thresh_md and p < p_thresh
            ),
        }
        return rec

    conditions.append(_record(
        "C1_AntiMetric", "VL_CV", d_thresh_code=0.3, d_thresh_md=0.30
    ))
    conditions.append(_record(
        "C2_DualChannel", "EL", d_thresh_code=0.3, d_thresh_md=0.50
    ))
    conditions.append(_record(
        "C3_RootDiversity", "H_cond", d_thresh_code=0.3, d_thresh_md=0.30
    ))
    conditions.append(_record(
        "C4_AntiRegularity", "T", d_thresh_code=0.3, d_thresh_md=0.15
    ))

    # ---- C5: MinPathCost via verse-shuffle el_rate null ----
    print(f"[{EXP}] computing C5 verse-shuffle null (N_SHUFFLES={N_SHUFFLES})...")
    rng = np.random.default_rng(SEED)

    def _band_a(units):
        return [u for u in units if band_lo <= len(u.verses) <= band_hi]

    quran_units = _band_a(corpora.get("quran", []))
    ctrl_units: list = []
    for name in ctrl_pool:
        ctrl_units.extend(_band_a(corpora.get(name, [])))

    print(f"[{EXP}]   target units (Quran Band-A) : {len(quran_units)}")
    print(f"[{EXP}]   ctrl   units (pool  Band-A) : {len(ctrl_units)}")

    q_pcts = np.array(
        [_c5_unit_significance(u.verses, rng) for u in quran_units]
    )
    c_pcts = np.array(
        [_c5_unit_significance(u.verses, rng) for u in ctrl_units]
    )
    q_pcts = q_pcts[~np.isnan(q_pcts)]
    c_pcts = c_pcts[~np.isnan(c_pcts)]

    q_sig = float((q_pcts < 0.05).mean()) if len(q_pcts) else 0.0
    c_sig = float((c_pcts < 0.05).mean()) if len(c_pcts) else 0.0
    enrich = q_sig / c_sig if c_sig > 0 else float("inf")

    c5 = {
        "id": "C5_MinPathCost",
        "feature": "EL via verse-shuffle null",
        "n_target": int(len(q_pcts)),
        "n_control": int(len(c_pcts)),
        "target_sig_rate": q_sig,
        "control_sig_rate": c_sig,
        "enrichment_ratio": enrich,
        "code_threshold_q_sig": 0.3,
        "code_threshold_enrich": 1.5,
        "md_threshold_enrich": 2.0,
        "pass_code_thresholds": bool(q_sig > 0.3 and enrich > 1.5),
        "pass_md_thresholds": bool(q_sig > 0.3 and enrich > 2.0),
    }
    conditions.append(c5)

    print(f"[{EXP}]   target_sig = {q_sig:.4f}   ctrl_sig = {c_sig:.4f}   "
          f"enrich = {enrich:.3f}")

    # ---- BH-FDR across the 4 d-test p-values (C1-C4) ----
    pvals = [c["mannwhitney_p_one_sided_greater"] for c in conditions[:4]]
    rejected_001, q_001 = _bh_fdr(pvals, alpha=0.01)
    rejected_005, q_005 = _bh_fdr(pvals, alpha=0.05)
    for i, c in enumerate(conditions[:4]):
        c["bh_q_value"] = q_001[i]
        c["bh_rejected_at_alpha_0p01"] = rejected_001[i]
        c["bh_rejected_at_alpha_0p05"] = rejected_005[i]

    # ---- Aggregate verdict ----
    n_pass_code = int(sum(c["pass_code_thresholds"] for c in conditions))
    n_pass_md   = int(sum(c["pass_md_thresholds"]   for c in conditions))
    n_pass_bh01 = int(sum(c.get("bh_rejected_at_alpha_0p01", False)
                          for c in conditions[:4])) + int(c5["pass_code_thresholds"])
    n_pass_bh05 = int(sum(c.get("bh_rejected_at_alpha_0p05", False)
                          for c in conditions[:4])) + int(c5["pass_code_thresholds"])

    def _verdict(n_pass: int) -> str:
        if n_pass >= 4:
            return "STOT_v2_SATISFIED"
        if n_pass >= 2:
            return "STOT_v2_PARTIAL"
        return "STOT_v2_NOT_SATISFIED"

    aggregate = {
        "n_passed_code_thresholds":     n_pass_code,
        "n_passed_md_thresholds":       n_pass_md,
        "n_passed_bh_corrected_p_0p01": n_pass_bh01,
        "n_passed_bh_corrected_p_0p05": n_pass_bh05,
        "verdict_code_thresholds":      _verdict(n_pass_code),
        "verdict_md_thresholds":        _verdict(n_pass_md),
        "verdict_bh_0p01":              _verdict(n_pass_bh01),
        "verdict_bh_0p05":              _verdict(n_pass_bh05),
    }

    # ---- Pre-reg gate test ----
    pre_reg_pass = aggregate["verdict_bh_0p01"] == "STOT_v2_SATISFIED"

    # ---- Independence diagnostic: pairwise abs-corr across the 4 d-features ----
    from itertools import combinations
    pair_corrs = {}
    for f1, f2 in combinations(["EL", "VL_CV", "H_cond", "T"], 2):
        a = np.concatenate([X_Q[:, idx[f1]], X_C[:, idx[f1]]])
        b = np.concatenate([X_Q[:, idx[f2]], X_C[:, idx[f2]]])
        rho, _ = stats.spearmanr(a, b)
        pair_corrs[f"{f1}_x_{f2}"] = float(rho) if math.isfinite(rho) else None
    max_abs_pair_corr = max(
        (abs(v) for v in pair_corrs.values() if v is not None), default=0.0
    )
    independence_diag = {
        "comment": (
            "Pairwise Spearman rho across the 4 features used in C1-C4. "
            "STOT v2 is most useful as a sufficiency theorem when the "
            "conditions are roughly independent (so passing >= 4/5 is "
            "non-trivial). Pre-reg note in HYPOTHESES_AND_TESTS.md:1220 "
            "asks for max |rho| < 0.3 across pairs."
        ),
        "pairs": pair_corrs,
        "max_abs_pair_corr": max_abs_pair_corr,
        "passes_independence_threshold_0p3": bool(max_abs_pair_corr < 0.3),
    }

    # ---- Report ----
    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "A3 (= H23)",
        "title": (
            "STOT v2 5-condition theorem re-derived from phase_06_phi_m "
            "under the audited pipeline (post-F11, post-hadith-quarantine, "
            "post-CamelTools)."
        ),
        "pre_reg": {
            "theorem": (
                "A text satisfies STOT v2 iff it passes >= 4 of 5 conditions "
                "at BH-corrected p <= 0.01."
            ),
            "n_shuffles_C5": N_SHUFFLES,
            "seed": SEED,
            "method_source": (
                "archive/2025-10_legacy_scripts/cross_language_stot_test_v2_fair.py:"
                "269-314 (re-derived; same Cohen d + Mann-Whitney + verse-shuffle "
                "null, but using audited X_QURAN / X_CTRL_POOL / Band-A from "
                "phase_06_phi_m instead of the legacy `target_df`/`control_df`)."
            ),
            "code_thresholds_C1_C4": {"d_min": 0.3, "p_max": 0.05},
            "code_thresholds_C5":    {"q_sig_min": 0.3, "enrich_min": 1.5},
            "md_thresholds_C1_C4": {
                "C1_d_min": 0.30, "C2_d_min": 0.50,
                "C3_d_min": 0.30, "C4_d_min": 0.15,
            },
            "md_thresholds_C5": {"q_sig_min": 0.3, "enrich_min": 2.0},
        },
        "conditions": conditions,
        "aggregate_verdict": aggregate,
        "pre_registered_gate_pass_bh_0p01_4_of_5": pre_reg_pass,
        "independence_diagnostic": independence_diag,
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Stdout ----
    print()
    print(f"[{EXP}] -- per-condition results --")
    for c in conditions:
        if c["id"] == "C5_MinPathCost":
            print(f"[{EXP}]  {c['id']:<22s}: q_sig={c['target_sig_rate']:.4f}   "
                  f"c_sig={c['control_sig_rate']:.4f}   "
                  f"enrich={c['enrichment_ratio']:.3f}   "
                  f"pass_code={c['pass_code_thresholds']}   "
                  f"pass_md={c['pass_md_thresholds']}")
        else:
            print(f"[{EXP}]  {c['id']:<22s}: feat={c['feature']:<7s} "
                  f"d={c['cohen_d_target_minus_control']:+.4f}  "
                  f"MW_p={c['mannwhitney_p_one_sided_greater']:.2e}  "
                  f"BH_q={c.get('bh_q_value', float('nan')):.2e}  "
                  f"pass_code={c['pass_code_thresholds']}   "
                  f"pass_md={c['pass_md_thresholds']}")
    print()
    print(f"[{EXP}] aggregate verdict:")
    for k, v in aggregate.items():
        print(f"[{EXP}]   {k:<35s} = {v}")
    print()
    print(f"[{EXP}] PRE-REG GATE (>= 4/5 BH @ alpha=0.01): "
          f"{'PASS' if pre_reg_pass else 'FAIL'}")
    print(f"[{EXP}] independence: max |pair-rho| = "
          f"{independence_diag['max_abs_pair_corr']:.3f}  "
          f"(< 0.3 threshold: {independence_diag['passes_independence_threshold_0p3']})")
    print(f"[{EXP}] runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
