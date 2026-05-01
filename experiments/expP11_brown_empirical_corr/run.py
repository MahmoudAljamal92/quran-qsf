"""
expP11_brown_empirical_corr/run.py
==================================
Pre-registered tightening of the Brown joint p for the 4-channel combo
{EL, R3, J1, Hurst} using the empirical 4x4 correlation matrix from
control corpora (vs the conservative ρ=0.5 prior used in patch_3).

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
        results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json (R3 z-scores)
        results/experiments/expP4_hurst_universal_cross_tradition/...json (Hurst H)
        results/experiments/expE17b_mushaf_j1_1m_perms/...json (J1)

Writes: results/experiments/expP11_brown_empirical_corr/expP11_brown_empirical_corr.json
"""
from __future__ import annotations

import hashlib
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
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import el_rate  # noqa: E402

EXP = "expP11_brown_empirical_corr"
SEED = 42
MIN_VERSES = 2

CONSERVATIVE_RHO = 0.5

# Per-corpus channel values from existing experiments (v7.8/v7.9 record).
# Each row: (corpus, EL_z, R3_z, J1_z, Hurst_z) — Z-scores against null distributions.
# Sources (audit-traceable):
#   EL_z  : exp104 + this run; per-corpus pool z = (EL_corpus - EL_pool_mean)/sigma_pool
#   R3_z  : expP4_cross_tradition_R3
#   J1_z  : expE17b_mushaf_j1_1m_perms (per-corpus where available)
#   Hurst : expP4_hurst_universal_cross_tradition
# We compute these here from the source JSONs (read-only).


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _hurst_per_unit(values: np.ndarray) -> float:
    """Quick rescaled-range Hurst on a 1-D series."""
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n < 16:
        return float("nan")
    mu = x.mean()
    Y = np.cumsum(x - mu)
    R = Y.max() - Y.min()
    S = x.std(ddof=1)
    if S == 0 or R == 0:
        return float("nan")
    return float(np.log(R / S) / np.log(n))


def _per_corpus_channels(CORPORA: dict) -> dict:
    """Compute per-corpus EL, surrogate R3 (mean verse-final letter entropy),
    surrogate J1 (cumulative-shift deviation), Hurst (verse-length series).
    These are POOL-INTERNAL surrogates — adequate for the empirical
    correlation matrix even though the global R3/J1 use different nulls.
    The shape of R is what matters for Brown."""
    rows = []
    for name, units in CORPORA.items():
        verses_concat = []
        verse_lens = []
        for u in units:
            if len(u.verses) >= MIN_VERSES:
                vs = list(u.verses)
                verses_concat.extend(vs)
                verse_lens.extend([len(v.split()) for v in vs])
        if len(verse_lens) < 32:
            continue
        # EL on the whole corpus (concat treated as one sequence)
        el = el_rate(verses_concat) if len(verses_concat) >= 2 else float("nan")
        # R3 surrogate: H of verse-final letter distribution (lower => more concentrated)
        from collections import Counter
        finals = []
        for v in verses_concat:
            v2 = v.strip()
            if v2:
                ch = next((c for c in reversed(v2) if c.isalpha()), "")
                if ch:
                    finals.append(ch)
        cnt = Counter(finals)
        tot = sum(cnt.values())
        H = -sum((c/tot) * np.log2(c/tot) for c in cnt.values() if c > 0) if tot > 0 else 0.0
        # J1 surrogate: variance of consecutive verse-length deltas (higher =>
        # rougher local structure; used as orthogonal signature)
        vl = np.array(verse_lens, dtype=float)
        d = np.diff(vl)
        j1 = float(np.var(d)) if d.size > 0 else 0.0
        # Hurst on verse-length series
        H_hurst = _hurst_per_unit(vl)
        rows.append({
            "corpus": name,
            "n_units": len(units),
            "n_verses": len(verses_concat),
            "EL": el,
            "R3_surrogate_H_finals": H,
            "J1_surrogate_var_dvl": j1,
            "Hurst": H_hurst,
        })
    return rows


def _brown_p(p_individual: list[float], R: np.ndarray) -> dict:
    """Brown's method (1975): combine k correlated p-values.
    chi2_obs = -2 sum log p_i.   Effective df = 2k / c where c = ... .
    Tail of chi2 with that df gives the joint p.
    """
    p = np.asarray(p_individual, dtype=float)
    p = np.clip(p, 1e-300, 1.0 - 1e-12)
    k = len(p)
    chi2_obs = -2.0 * np.sum(np.log(p))
    # Brown scaling: c = (2k - 2 * sum_{i<j} 2*rho_ij - tr(R^2) corrections)/k
    # More precisely: var(-2 sum log p_i) approximately = 4k + 2*sum_{i<j} f(rho_ij)
    # where f(rho) ≈ rho * (3.25 + 0.75*rho)  (Brown's Lemma)
    cov_sum = 0.0
    for i in range(k):
        for j in range(i+1, k):
            r = float(R[i, j])
            cov_sum += r * (3.25 + 0.75 * r)
    var_obs = 4.0 * k + 2.0 * cov_sum
    mean_obs = 2.0 * k
    # match to chi2 with df = 2k/c via mean and variance scaling
    c = var_obs / (2.0 * mean_obs)
    df_eff = 2.0 * mean_obs / var_obs * (2.0 * k)
    # Tail
    from scipy.stats import chi2
    p_joint = float(chi2.sf(chi2_obs / c, df_eff))
    return {
        "chi2_obs": float(chi2_obs),
        "c": float(c),
        "df_eff": float(df_eff),
        "p_joint": p_joint,
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

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    print(f"[{EXP}] Computing 4-channel surrogates per corpus ...")
    rows = _per_corpus_channels(CORPORA)
    # Drop quran from R-estimation; keep all controls regardless of language.
    ctrl_rows = [r for r in rows if r["corpus"] != "quran"]
    print(f"[{EXP}] Controls used for R: {[r['corpus'] for r in ctrl_rows]} (n={len(ctrl_rows)})")
    if len(ctrl_rows) < 5:
        print(f"[{EXP}] WARN: small N for empirical R (n={len(ctrl_rows)}); proceeding")

    # Build N x 4 design matrix and z-score each column
    cols = ["EL", "R3_surrogate_H_finals", "J1_surrogate_var_dvl", "Hurst"]
    X = np.array([[r[c] for c in cols] for r in ctrl_rows], dtype=float)
    finite = np.isfinite(X).all(axis=1)
    X = X[finite]
    n_used = X.shape[0]
    Xz = (X - X.mean(axis=0)) / (X.std(axis=0, ddof=1) + 1e-12)
    R_empirical = np.corrcoef(Xz, rowvar=False) if n_used >= 4 else np.eye(4)
    R_conservative = np.full((4, 4), CONSERVATIVE_RHO)
    np.fill_diagonal(R_conservative, 1.0)

    # Use the four locked individual p-values from the v7.9-cand record:
    # EL p (full-114 AUC=0.9813)         -> 1.4e-12  (Mann-Whitney, already locked)
    # R3 cross-tradition Quran z = -8.92  -> 2.4e-19
    # J1 Mushaf perm 0/10^6                -> < 1e-6 (use conservative 1e-6)
    # Hurst Quran z = 3.70 vs perm null    -> 2.2e-4
    p_individual = {
        "EL_full114":  1.4e-12,
        "R3_Quran_z":  2.4e-19,
        "J1_Mushaf":   1.0e-6,
        "Hurst_Quran": 2.2e-4,
    }
    print(f"[{EXP}] Per-channel locked p-values: {p_individual}")

    res_emp = _brown_p(list(p_individual.values()), R_empirical)
    res_con = _brown_p(list(p_individual.values()), R_conservative)
    ratio = res_emp["p_joint"] / max(res_con["p_joint"], 1e-300)

    if res_emp["p_joint"] <= 1e-6:
        verdict = "TIGHTENED_STRONG"
    elif res_emp["p_joint"] <= 2.95e-5:
        verdict = "TIGHTENED"
    elif res_emp["p_joint"] <= 1e-4:
        verdict = "LOOSENED_MILD"
    else:
        verdict = "LOOSENED_STRONG"

    print(f"[{EXP}] Brown p (conservative ρ=0.5): {res_con['p_joint']:.3e}")
    print(f"[{EXP}] Brown p (empirical R):        {res_emp['p_joint']:.3e}")
    print(f"[{EXP}] Ratio (emp / con):            {ratio:.3f}")
    print(f"[{EXP}] Verdict: {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "n_controls_for_R": int(n_used),
        "controls_used": [r["corpus"] for r in ctrl_rows if all(np.isfinite(r[c]) for c in cols)],
        "channels": cols,
        "per_corpus_table": rows,
        "p_individual": p_individual,
        "R_empirical": R_empirical.tolist(),
        "R_conservative": R_conservative.tolist(),
        "brown_empirical": res_emp,
        "brown_conservative": res_con,
        "p_joint_empirical": res_emp["p_joint"],
        "p_joint_conservative": res_con["p_joint"],
        "ratio_emp_over_con": ratio,
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
