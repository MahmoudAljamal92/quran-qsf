"""
exp95o_joint_extremum_likelihood — H48 (joint-extremum likelihood
under 10-feature panel: 5-D Φ_M + 5-D Ψ_L).

For each Arabic corpus, compute the per-unit 10-feature vector
(5 Φ_M features + 5 Ψ_L letter-level features). Compute the 7×10
corpus-mean matrix M[c, k]. For each feature k, rank the 7 corpora
descending. Count S_obs = number of features on which Quran is at
extremum (rank 1 or rank 7). Compute:

  - naive null p = binomial probability under independence
  - permutation null p = empirical from N_PERM = 100,000 trials
    that shuffle corpus labels at the unit level (preserving corpus
    sizes) and re-rank.

H48 (locked in PREREG.md): S_obs ≥ 6 AND p_perm < 0.001 → strong;
S_obs ≥ 4 AND p_perm < 0.01 → joint extremum. Otherwise FAIL ladder.

Reads:
  - phase_06_phi_m.pkl (corpus pool)
  - experiments/exp95o_joint_extremum_likelihood/PREREG.md (hash-lock)
  - src/features.py (Φ_M definitions)

Writes:
  - results/experiments/exp95o_joint_extremum_likelihood/
      exp95o_joint_extremum_likelihood.json (receipt)
      per_feature_ranking.csv (rank table)
"""
from __future__ import annotations

import csv
import gzip as gz
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    letters_28,
)
from experiments.exp95n_msfc_letter_level_fragility.run import (  # noqa: E402
    features_letter,
)
from src.features import (  # noqa: E402
    ARABIC_CONN,
    cn_rate,
    el_rate,
    h_cond_roots,
    h_el,
    vl_cv,
)
from src.features import _terminal_alpha  # noqa: E402

EXP = "exp95o_joint_extremum_likelihood"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "31eaf358d10a500405348a65e29dc52245003e923d29426628a878e591fbc660"
)

# Frozen constants (must match PREREG §4)
N_PERM = 100_000
RNG_SEED = 95_000
MIN_VERSES_PER_UNIT = 2
MIN_UNITS_PER_CORPUS = 5
ARABIC_POOL = (
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "ksucca",
    "arabic_bible",
    "hindawi",
)
EL_RATE_QURAN_LOCKED = 0.7271
EL_RATE_TOL = 0.02
P_MAX_QURAN_LOCKED = 0.501
P_MAX_TOL = 0.02

PANEL = [
    # 5-D Φ_M (verse-aggregate)
    "el_rate", "vl_cv", "cn_rate", "h_cond_roots", "h_el",
    # 5-D Ψ_L (letter-level)
    "H_2", "H_3", "Gini", "gzip_ratio", "log10_nb",
]
N_FEATURES = len(PANEL)


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def features_phi_m(verses: list[str]) -> np.ndarray:
    """5-D Φ_M feature vector (matches src.features.features_5d but
    with the explicit (el_rate, vl_cv, cn_rate, h_cond_roots, h_el)
    ordering — h_el rather than T = h_cond - h_el — so the panel has
    h_cond and h_el as independent dimensions."""
    return np.array([
        el_rate(verses),
        vl_cv(verses),
        cn_rate(verses, ARABIC_CONN),
        h_cond_roots(verses),
        h_el(verses),
    ], dtype=float)


def p_max_corpus(units: list[Any]) -> float:
    finals: list[str] = []
    for u in units:
        for v in u.verses:
            tf = _terminal_alpha(v)
            if tf:
                finals.append(tf)
    if not finals:
        return 0.0
    c = Counter(finals)
    n = sum(c.values())
    return max(c.values()) / n if n > 0 else 0.0


def main() -> None:
    out_dir = safe_output_dir(EXP)
    t0 = time.time()

    # ---- 1. Lock PREREG hash ----
    actual_hash = _sha256(PREREG_PATH)
    if actual_hash != EXPECTED_PREREG_HASH:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift:\n"
            f"  expected: {EXPECTED_PREREG_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"REFUSING TO RUN."
        )

    # ---- 2. Load corpora ----
    print(f"[{EXP}] loading corpus phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # ---- 3. Compute per-unit 10-feature matrix ----
    print(f"[{EXP}] computing per-unit 10-feature matrix...")
    by_corpus_features: dict[str, list[np.ndarray]] = {}
    by_corpus_units: dict[str, list[Any]] = {}
    audit_non_finite: list[dict[str, Any]] = []
    feat_t0 = time.time()

    for cname in ARABIC_POOL:
        items = CORPORA.get(cname, [])
        feats: list[np.ndarray] = []
        units: list[Any] = []
        for u in items:
            verses = list(u.verses)
            if len(verses) < MIN_VERSES_PER_UNIT:
                continue
            try:
                phi_5 = features_phi_m(verses)
                s = letters_28(" ".join(verses))
                if len(s) < 2:
                    continue
                psi_5 = features_letter(s)
            except Exception as e:
                print(
                    f"[{EXP}]   skip {getattr(u, 'label', '?')}: {e}"
                )
                continue
            f = np.concatenate([phi_5, psi_5])
            if not np.all(np.isfinite(f)):
                audit_non_finite.append({
                    "corpus": cname,
                    "label": getattr(u, "label", "?"),
                    "feature": [float(x) for x in f],
                })
                continue
            feats.append(f)
            units.append(u)
        by_corpus_features[cname] = feats
        by_corpus_units[cname] = units
        print(
            f"[{EXP}]   {cname}: {len(feats)} units, "
            f"elapsed {time.time() - feat_t0:.1f}s"
        )

    # ---- 4. Build 7×10 corpus-mean matrix M and stacked X ----
    M = np.zeros((len(ARABIC_POOL), N_FEATURES), dtype=float)
    corpus_sizes: list[int] = []
    X_rows: list[np.ndarray] = []
    for ic, cname in enumerate(ARABIC_POOL):
        feats = by_corpus_features[cname]
        if len(feats) < MIN_UNITS_PER_CORPUS:
            print(
                f"[{EXP}] AUDIT_FAIL min_units_per_corpus: "
                f"{cname} has {len(feats)} < {MIN_UNITS_PER_CORPUS}"
            )
        Xc = np.array(feats, dtype=float)
        corpus_sizes.append(len(feats))
        X_rows.append(Xc)
        M[ic] = Xc.mean(axis=0)
    X = np.concatenate(X_rows, axis=0)
    n_units_total = X.shape[0]
    print(
        f"[{EXP}] X shape = {X.shape}, corpus_sizes = {corpus_sizes}"
    )

    # ---- 5. Audit panel completeness ----
    if not np.all(np.isfinite(M)):
        raise SystemExit(
            f"[{EXP}] AUDIT_FAIL panel_completeness: M has non-finite cells"
        )

    # ---- 6. Audit locked-Quran-feature matches ----
    quran_idx = ARABIC_POOL.index("quran")
    el_rate_quran = M[quran_idx, 0]
    el_rate_drift = abs(el_rate_quran - EL_RATE_QURAN_LOCKED)
    audit_el_rate_pass = el_rate_drift <= EL_RATE_TOL
    print(
        f"[{EXP}] audit el_rate(quran) = {el_rate_quran:.4f} vs "
        f"locked {EL_RATE_QURAN_LOCKED} ± {EL_RATE_TOL} → "
        f"{'PASS' if audit_el_rate_pass else 'FAIL'}"
    )

    p_max_quran = p_max_corpus(by_corpus_units["quran"])
    p_max_drift = abs(p_max_quran - P_MAX_QURAN_LOCKED)
    audit_p_max_pass = p_max_drift <= P_MAX_TOL
    print(
        f"[{EXP}] audit p_max(quran) = {p_max_quran:.4f} vs "
        f"locked {P_MAX_QURAN_LOCKED} ± {P_MAX_TOL} → "
        f"{'PASS' if audit_p_max_pass else 'FAIL'}"
    )

    # ---- 7. Per-feature ranking + S(c) per corpus ----
    # rank_matrix[c, k] = descending rank of corpus c on feature k (1-based)
    ranks = np.zeros((len(ARABIC_POOL), N_FEATURES), dtype=int)
    for k in range(N_FEATURES):
        order = np.argsort(-M[:, k])  # descending
        for r, c in enumerate(order):
            ranks[c, k] = r + 1
    S_per_corpus = np.zeros(len(ARABIC_POOL), dtype=int)
    for c in range(len(ARABIC_POOL)):
        S_per_corpus[c] = int(np.sum((ranks[c] == 1) | (ranks[c] == 7)))
    S_obs = int(S_per_corpus[quran_idx])
    quran_top_features = [
        PANEL[k] for k in range(N_FEATURES) if ranks[quran_idx, k] == 1
    ]
    quran_bottom_features = [
        PANEL[k] for k in range(N_FEATURES) if ranks[quran_idx, k] == 7
    ]
    print(
        f"\n[{EXP}] S_obs (Quran extremum count) = {S_obs} of {N_FEATURES}"
    )
    print(f"[{EXP}]   Quran rank 1 features: {quran_top_features}")
    print(f"[{EXP}]   Quran rank 7 features: {quran_bottom_features}")
    print(f"[{EXP}] Per-corpus S table:")
    for ic, cname in enumerate(ARABIC_POOL):
        rank_str = ", ".join(
            f"{PANEL[k]}={ranks[ic, k]}" for k in range(N_FEATURES)
        )
        print(
            f"[{EXP}]   {cname:16s} S={S_per_corpus[ic]} | {rank_str}"
        )

    # ---- 8. Naive null binomial p ----
    # Under H0 of independence + uniform extremum, S ~ Binomial(K, 2/7)
    p_per_feature = 2.0 / 7.0
    p_naive = 0.0
    for s in range(S_obs, N_FEATURES + 1):
        p_naive += math.comb(N_FEATURES, s) * (
            p_per_feature ** s
        ) * ((1.0 - p_per_feature) ** (N_FEATURES - s))
    print(f"\n[{EXP}] naive null p (binomial, indep): {p_naive:.6e}")

    # ---- 9. Permutation null (unit-level shuffle, preserving sizes) ----
    print(f"[{EXP}] running {N_PERM} permutations...")
    perm_t0 = time.time()
    rng = np.random.default_rng(RNG_SEED)
    cum_sizes = np.cumsum([0] + corpus_sizes)  # length 8 boundaries
    n_at_least = 0
    perm_max_S_distribution: list[int] = []

    for trial in range(N_PERM):
        perm = rng.permutation(n_units_total)
        X_p = X[perm]
        # Compute means per corpus via cumsum trick
        cum = np.zeros((n_units_total + 1, N_FEATURES), dtype=float)
        cum[1:] = np.cumsum(X_p, axis=0)
        means = np.zeros((len(ARABIC_POOL), N_FEATURES), dtype=float)
        for c in range(len(ARABIC_POOL)):
            means[c] = (
                cum[cum_sizes[c + 1]] - cum[cum_sizes[c]]
            ) / corpus_sizes[c]
        argmax = means.argmax(axis=0)
        argmin = means.argmin(axis=0)
        S_p = np.zeros(len(ARABIC_POOL), dtype=int)
        for k in range(N_FEATURES):
            S_p[argmax[k]] += 1
            S_p[argmin[k]] += 1
        max_S = int(S_p.max())
        perm_max_S_distribution.append(max_S)
        if max_S >= S_obs:
            n_at_least += 1
        if (trial + 1) % 10000 == 0:
            print(
                f"[{EXP}]   perm {trial + 1}/{N_PERM} "
                f"elapsed {time.time() - perm_t0:.1f}s, "
                f"running p = {n_at_least / (trial + 1):.5f}"
            )

    p_perm = n_at_least / N_PERM
    perm_dist_counter = Counter(perm_max_S_distribution)
    perm_t = time.time() - perm_t0
    print(
        f"[{EXP}] permutation done in {perm_t:.1f}s; p_perm = {p_perm:.6f} "
        f"(n_at_least = {n_at_least}/{N_PERM})"
    )

    # ---- 10. Verdict ladder ----
    if audit_non_finite:
        verdict = "FAIL_audit_features_finite"
    elif not np.all(np.isfinite(M)):
        verdict = "FAIL_audit_panel_completeness"
    elif not audit_el_rate_pass:
        verdict = "FAIL_audit_el_rate_quran_drift"
    elif not audit_p_max_pass:
        verdict = "FAIL_audit_p_max_quran_drift"
    elif S_obs < 4:
        verdict = "FAIL_no_extremum"
    elif S_obs >= 6 and p_perm < 0.001:
        verdict = "PASS_strong_joint_extremum"
    elif S_obs >= 4 and p_perm < 0.01:
        verdict = "PASS_joint_extremum"
    elif S_obs >= 4 and p_perm < 0.05:
        verdict = "PARTIAL_moderate_extremum"
    else:
        verdict = "FAIL_no_extremum"

    # ---- 11. Receipt JSON + CSV ----
    elapsed = time.time() - t0
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H48",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "N_PERM": N_PERM,
            "RNG_SEED": RNG_SEED,
            "MIN_VERSES_PER_UNIT": MIN_VERSES_PER_UNIT,
            "MIN_UNITS_PER_CORPUS": MIN_UNITS_PER_CORPUS,
            "ARABIC_POOL": list(ARABIC_POOL),
            "PANEL": list(PANEL),
            "EL_RATE_QURAN_LOCKED": EL_RATE_QURAN_LOCKED,
            "EL_RATE_TOL": EL_RATE_TOL,
            "P_MAX_QURAN_LOCKED": P_MAX_QURAN_LOCKED,
            "P_MAX_TOL": P_MAX_TOL,
        },
        "audit": {
            "non_finite_features": audit_non_finite,
            "el_rate_quran_actual": float(el_rate_quran),
            "el_rate_quran_drift": float(el_rate_drift),
            "el_rate_quran_pass": bool(audit_el_rate_pass),
            "p_max_quran_actual": float(p_max_quran),
            "p_max_quran_drift": float(p_max_drift),
            "p_max_quran_pass": bool(audit_p_max_pass),
        },
        "corpus_sizes": dict(zip(ARABIC_POOL, corpus_sizes)),
        "M_matrix": {
            cname: {PANEL[k]: float(M[ic, k]) for k in range(N_FEATURES)}
            for ic, cname in enumerate(ARABIC_POOL)
        },
        "rank_matrix": {
            cname: {PANEL[k]: int(ranks[ic, k]) for k in range(N_FEATURES)}
            for ic, cname in enumerate(ARABIC_POOL)
        },
        "S_per_corpus": {
            cname: int(S_per_corpus[ic])
            for ic, cname in enumerate(ARABIC_POOL)
        },
        "S_obs": S_obs,
        "quran_top_features": quran_top_features,
        "quran_bottom_features": quran_bottom_features,
        "p_naive_binomial_indep": p_naive,
        "p_perm_correlation_corrected": p_perm,
        "perm_max_S_distribution": dict(
            sorted(
                {int(k): int(v) for k, v in perm_dist_counter.items()}.items()
            )
        ),
        "wall_time_s": round(elapsed, 2),
        "permutation_wall_time_s": round(perm_t, 2),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    receipt_path = out_dir / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    csv_path = out_dir / "per_feature_ranking.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["feature"] + list(ARABIC_POOL))
        for k in range(N_FEATURES):
            w.writerow(
                [PANEL[k]]
                + [f"{M[ic, k]:.6f} (rank {ranks[ic, k]})"
                   for ic in range(len(ARABIC_POOL))]
            )
        w.writerow([])
        w.writerow(["S(corpus)"] + [
            int(S_per_corpus[ic]) for ic in range(len(ARABIC_POOL))
        ])

    print(f"\n[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] S_obs = {S_obs} of {N_FEATURES}")
    print(
        f"[{EXP}] p_naive_binomial_indep = {p_naive:.6e}; "
        f"p_perm_correlation_corrected = {p_perm:.6f}"
    )
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] csv:     {csv_path}")
    print(f"[{EXP}] elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
