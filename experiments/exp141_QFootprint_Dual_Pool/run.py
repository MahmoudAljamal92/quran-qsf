"""experiments/exp141_QFootprint_Dual_Pool/run.py — split exp138 by pool.

Pool A (Arabic-only, n=7), Pool B (non-Arabic, n=6), Pool C (combined, n=12).
For each pool, recompute Quran joint Stouffer Z (Brown-adjusted), Hotelling T²,
and column-shuffle null. Report bilateral (Z_A, Z_B, Z_C) tuple.

PREREG: experiments/exp141_QFootprint_Dual_Pool/PREREG.md
Output: results/experiments/exp141_QFootprint_Dual_Pool/exp141_QFootprint_Dual_Pool.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EXP_NAME = "exp141_QFootprint_Dual_Pool"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

POOL_A = ["quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
          "hindawi", "ksucca", "arabic_bible"]
POOL_B = ["quran", "hebrew_tanakh", "greek_nt", "pali", "avestan_yasna", "rigveda"]
POOL_C = ["quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
          "hindawi", "ksucca", "arabic_bible", "hebrew_tanakh", "greek_nt",
          "pali", "avestan_yasna", "rigveda"]
ALPHABET_SIZES = {
    "quran": 28, "poetry_jahili": 28, "poetry_islami": 28, "poetry_abbasi": 28,
    "hindawi": 28, "ksucca": 28, "arabic_bible": 28, "hebrew_tanakh": 22,
    "greek_nt": 24, "pali": 31, "avestan_yasna": 26, "rigveda": 47,
}

# Same 8 axes as exp138
AXES = [
    "z_HEL_pool", "z_pmax_pool",
    "z_HEL_unit_median", "z_HEL_unit_p25",
    "z_VL_CV_median", "z_bigram_distinct_pool",
    "z_gzip_eff_pool", "z_Delta_max_unit",
]
SIGN_QURAN_EXTREME = {
    "z_HEL_pool": -1, "z_pmax_pool": +1,
    "z_HEL_unit_median": -1, "z_HEL_unit_p25": -1,
    "z_VL_CV_median": +1, "z_bigram_distinct_pool": -1,
    "z_gzip_eff_pool": -1, "z_Delta_max_unit": +1,
}

N_PERM = 10_000
RIDGE = 1e-3
SEED = 42


def stouffer_z_brown(z_subset_row, R_subset):
    K = len(z_subset_row)
    sumR = float(R_subset.sum())
    # F1 fix 2026-04-29: Brown-Stouffer combined Z under correlated axes is
    # sum_z / sqrt(Var(sum_z)) = sum_z / sqrt(sumR), since each z_i has Var=1
    # and pairwise covariances given by R. K_eff = K^2/sumR is Cheverud-Li-Ji
    # M_eff (for Bonferroni alpha adjustment), kept for receipt diagnostics.
    K_eff = (K * K) / max(sumR, 1e-12)
    return float(z_subset_row.sum() / math.sqrt(max(sumR, 1e-12))), K_eff


def analyze_pool(pool_name, corpus_list, raw_data):
    """Run full Q-Footprint analysis on a pool."""
    print(f"# === Pool {pool_name}: {len(corpus_list)} corpora ===", flush=True)
    n = len(corpus_list)
    M_raw = np.zeros((n, 8))
    for i, c in enumerate(corpus_list):
        for j, ax in enumerate(AXES):
            M_raw[i, j] = raw_data[c][ax]
    quran_idx = corpus_list.index("quran")
    non_q_idx = [i for i in range(n) if i != quran_idx]

    # Z-score per axis using non-Quran rows IN THIS POOL
    M_z = np.zeros_like(M_raw)
    for j, ax in enumerate(AXES):
        col = M_raw[non_q_idx, j]
        mu, sd = float(col.mean()), float(col.std(ddof=1)) if len(col) > 1 else 1.0
        sd = sd if sd > 1e-12 else 1.0
        s = SIGN_QURAN_EXTREME[ax]
        M_z[:, j] = s * (M_raw[:, j] - mu) / sd

    # Stouffer Z (Brown-adjusted)
    if len(non_q_idx) >= 2:
        R = np.corrcoef(M_z[non_q_idx, :], rowvar=False)
    else:
        R = np.eye(8)
    Z_brown_per_corpus = np.array([stouffer_z_brown(M_z[i, :], R)[0] for i in range(n)])
    K_eff = (8 * 8) / max(float(R.sum()), 1e-12)
    quran_Z_brown = float(Z_brown_per_corpus[quran_idx])
    Z_sorted = sorted(zip(corpus_list, Z_brown_per_corpus), key=lambda kv: -kv[1])
    rank_quran_Z = [c for c, _ in Z_sorted].index("quran") + 1
    rank_2_corpus = Z_sorted[1][0] if len(Z_sorted) > 1 else None
    rank_2_Z = float(Z_sorted[1][1]) if len(Z_sorted) > 1 else 0.0
    gap_Z = quran_Z_brown - rank_2_Z

    # Hotelling T²
    mu_z = M_z[non_q_idx, :].mean(axis=0)
    if len(non_q_idx) >= 2:
        Sigma = np.cov(M_z[non_q_idx, :], rowvar=False, ddof=1) + RIDGE * np.eye(8)
    else:
        Sigma = RIDGE * np.eye(8)
    Sigma_inv = np.linalg.pinv(Sigma)
    T2_per_corpus = np.array([
        float((M_z[i] - mu_z) @ Sigma_inv @ (M_z[i] - mu_z)) for i in range(n)
    ])
    quran_T2 = float(T2_per_corpus[quran_idx])
    T2_sorted = sorted(zip(corpus_list, T2_per_corpus), key=lambda kv: -kv[1])
    rank_quran_T2 = [c for c, _ in T2_sorted].index("quran") + 1
    rank_2_T2 = float(T2_sorted[1][1]) if len(T2_sorted) > 1 else 0.0
    gap_T2 = quran_T2 - rank_2_T2

    # Column-shuffle null
    rng = np.random.default_rng(SEED)
    perm_max_Z = np.zeros(N_PERM)
    perm_q_rank1 = 0
    for it in range(N_PERM):
        M_perm = M_z.copy()
        for j in range(8):
            M_perm[:, j] = rng.permutation(M_perm[:, j])
        Z_p = np.array([stouffer_z_brown(M_perm[i, :], R)[0] for i in range(n)])
        perm_max_Z[it] = float(Z_p.max())
        if int(np.argmax(Z_p)) == quran_idx:
            perm_q_rank1 += 1
    p_Z = float((perm_max_Z >= quran_Z_brown).mean())

    print(f"#   Quran Z_brown = {quran_Z_brown:.3f}  rank = {rank_quran_Z}/{n}  "
          f"gap to {rank_2_corpus} = {gap_Z:.3f}", flush=True)
    print(f"#   Quran T² = {quran_T2:.2f}  rank = {rank_quran_T2}/{n}  gap = {gap_T2:.2f}",
          flush=True)
    print(f"#   Column-shuffle p_Z = {p_Z:.5f},  K_eff = {K_eff:.3f}", flush=True)

    return {
        "n_corpora": n,
        "K_eff_brown": K_eff,
        "Z_brown_sorted": [{"corpus": c, "Z": float(z)} for c, z in Z_sorted],
        "T2_sorted": [{"corpus": c, "T2": float(t)} for c, t in T2_sorted],
        "quran_Z_brown": quran_Z_brown,
        "quran_rank_Z_of_n": rank_quran_Z,
        "rank_2_corpus_Z": rank_2_corpus,
        "rank_2_Z": rank_2_Z,
        "gap_Z_quran_to_rank2": gap_Z,
        "quran_T2": quran_T2,
        "quran_rank_T2_of_n": rank_quran_T2,
        "gap_T2_quran_to_rank2": gap_T2,
        "p_Z_column_shuffle": p_Z,
        "quran_rank1_freq_perm": perm_q_rank1 / N_PERM,
        "M_z_sha256": hashlib.sha256(M_z.tobytes()).hexdigest(),
        "z_per_axis_quran": {ax: float(M_z[quran_idx, j]) for j, ax in enumerate(AXES)},
    }


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)

    # Load 12 corpora and compute raw 8-axis values per corpus (reuse exp138)
    from experiments.exp138_Quran_Footprint_Joint_Z.run import (
        load_corpora_normalisers, compute_corpus_features,
    )

    corpora, norm_lookup = load_corpora_normalisers()
    print("# Computing 8-axis raw feature matrix per corpus (= exp138 axes)...", flush=True)
    raw = {}
    for c in POOL_C:
        units = corpora[c]
        norm_name = units[0]["normaliser"]
        norm_fn = norm_lookup[norm_name]
        raw[c] = compute_corpus_features(units, norm_fn, ALPHABET_SIZES[c])

    pool_results = {
        "A_Arabic_only": analyze_pool("A_Arabic_only", POOL_A, raw),
        "B_non_Arabic": analyze_pool("B_non_Arabic", POOL_B, raw),
        "C_combined_12": analyze_pool("C_combined_12", POOL_C, raw),
    }

    Z_A = pool_results["A_Arabic_only"]["quran_Z_brown"]
    Z_B = pool_results["B_non_Arabic"]["quran_Z_brown"]
    Z_C = pool_results["C_combined_12"]["quran_Z_brown"]
    rank_A = pool_results["A_Arabic_only"]["quran_rank_Z_of_n"]
    rank_B = pool_results["B_non_Arabic"]["quran_rank_Z_of_n"]
    rank_C = pool_results["C_combined_12"]["quran_rank_Z_of_n"]
    p_A = pool_results["A_Arabic_only"]["p_Z_column_shuffle"]
    p_B = pool_results["B_non_Arabic"]["p_Z_column_shuffle"]
    p_C = pool_results["C_combined_12"]["p_Z_column_shuffle"]

    Z_min = min(Z_A, Z_B, Z_C)

    # Acceptance
    A1 = (rank_A == 1) and (Z_A >= 10.0)
    A2 = (rank_B == 1) and (Z_B >= 5.0)
    A3 = (rank_C == 1) and (Z_C >= 8.0)
    A4 = Z_min >= 5.0
    A5 = (p_A < 0.001) and (p_B < 0.001) and (p_C < 0.001)
    n_pass = sum([A1, A2, A3, A4, A5])

    if n_pass == 5:
        verdict = "PASS_dual_pool_quran_alone_in_both"
        verdict_reason = (f"All 5 PASS: Z_A={Z_A:.2f} (rank1, p={p_A:.4f}), "
                          f"Z_B={Z_B:.2f} (rank1, p={p_B:.4f}), Z_C={Z_C:.2f} (rank1, p={p_C:.4f})")
    elif n_pass >= 3:
        verdict = "PARTIAL_dual_pool_directional"
        verdict_reason = f"{n_pass}/5 PASS"
    else:
        verdict = "FAIL_dual_pool_inhomogeneous"
        verdict_reason = f"Only {n_pass}/5 PASS"

    # Audit
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    audit_report = {
        "exp138_reproduction_check": {
            "exp138_locked_Z_brown": 12.149,
            "Pool_C_Z_brown_now": Z_C,
            "diff": Z_C - 12.149,
            "match_within_005": abs(Z_C - 12.149) < 0.05,
        },
        "n_corpora_per_pool": {"A": 7, "B": 6, "C": 12},
        "Z_min_across_pools": Z_min,
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H94_Dual_Pool",
        "hypothesis": ("Quran joint Stouffer Z is rank-1 in BOTH Arabic-only (n=7) and "
                       "non-Arabic-only (n=6) pools, with Z_A ≥ 10, Z_B ≥ 5, "
                       "and column-shuffle null p < 0.001 in each pool."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "POOL_A": POOL_A, "POOL_B": POOL_B, "POOL_C": POOL_C,
            "AXES": AXES, "N_PERM": N_PERM, "RIDGE": RIDGE, "SEED": SEED,
        },
        "results": {
            "summary_table": {
                "Pool_A_Arabic": {"n": 7, "quran_Z": Z_A, "quran_rank": rank_A,
                                  "p_col_shuffle": p_A},
                "Pool_B_non_Arabic": {"n": 6, "quran_Z": Z_B, "quran_rank": rank_B,
                                      "p_col_shuffle": p_B},
                "Pool_C_combined": {"n": 12, "quran_Z": Z_C, "quran_rank": rank_C,
                                    "p_col_shuffle": p_C},
                "Z_min_across_pools": Z_min,
            },
            "per_pool": pool_results,
            "criteria_pass": {
                "A1_Pool_A_Z_geq_10_rank1": A1,
                "A2_Pool_B_Z_geq_5_rank1": A2,
                "A3_Pool_C_Z_geq_8_rank1": A3,
                "A4_bilateral_Z_min_geq_5": A4,
                "A5_all_pools_p_lt_001": A5,
                "n_pass_of_5": n_pass,
            },
        },
        "audit_report": audit_report,
        "wall_time_s": float(time.time() - t0),
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"# Receipt written to {OUT_PATH}", flush=True)
    print(f"# Wall time: {receipt['wall_time_s']:.1f}s", flush=True)
    print(f"# Verdict: {verdict}", flush=True)
    print(f"# Reason : {verdict_reason}", flush=True)
    print()
    print(f"=== Bilateral Q-Footprint summary ===")
    print(f"  Pool A (Arabic-only,    n=7):  Z = {Z_A:+7.3f}  rank {rank_A}/7  p={p_A:.4f}")
    print(f"  Pool B (non-Arabic,     n=6):  Z = {Z_B:+7.3f}  rank {rank_B}/6  p={p_B:.4f}")
    print(f"  Pool C (combined,      n=12):  Z = {Z_C:+7.3f}  rank {rank_C}/12  p={p_C:.4f}")
    print(f"  Z_min across all pools     :   {Z_min:+7.3f}  (= conservative claim)")


if __name__ == "__main__":
    main()
