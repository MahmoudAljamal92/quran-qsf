"""experiments/exp143_QFootprint_Sharpshooter_Audit/run.py.

Three-part sharpshooter audit of exp138's Q-Footprint joint Z = 12.149σ:
(A) leave-one-axis-out, (B) random K=8 from 20-axis pool null, (C) inverse test.

PREREG: experiments/exp143_QFootprint_Sharpshooter_Audit/PREREG.md
Output: results/experiments/exp143_QFootprint_Sharpshooter_Audit/exp143_QFootprint_Sharpshooter_Audit.json
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EXP_NAME = "exp143_QFootprint_Sharpshooter_Audit"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

EXPECTED_CORPORA = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi", "hindawi",
    "ksucca", "arabic_bible", "hebrew_tanakh", "greek_nt", "pali",
    "avestan_yasna", "rigveda",
]
ALPHABET_SIZES = {
    "quran": 28, "poetry_jahili": 28, "poetry_islami": 28, "poetry_abbasi": 28,
    "hindawi": 28, "ksucca": 28, "arabic_bible": 28, "hebrew_tanakh": 22,
    "greek_nt": 24, "pali": 31, "avestan_yasna": 26, "rigveda": 47,
}

# 20-axis pool (declared in PREREG)
AXIS_POOL = [
    ("HEL_pool",            -1),
    ("pmax_pool",           +1),
    ("bigram_distinct_pool", -1),
    ("gzip_eff_pool",       -1),
    ("Delta_pool",          +1),
    ("HEL_unit_p10",        -1),
    ("HEL_unit_p25",        -1),
    ("HEL_unit_median",     -1),
    ("HEL_unit_p75",        -1),
    ("HEL_unit_mean",       -1),
    ("pmax_unit_p25",       +1),
    ("pmax_unit_median",    +1),
    ("pmax_unit_p75",       +1),
    ("pmax_unit_mean",      +1),
    ("VL_CV_unit_p25",      +1),
    ("VL_CV_unit_median",   +1),
    ("VL_CV_unit_p75",      +1),
    ("Delta_unit_p25",      +1),
    ("Delta_unit_median",   +1),
    ("Delta_unit_p10",      +1),
]
ORIGINAL_8_AXES = [
    "HEL_pool", "pmax_pool",
    "HEL_unit_median", "HEL_unit_p25",
    "VL_CV_unit_median",
    "bigram_distinct_pool", "gzip_eff_pool",
    "Delta_unit_median",
]

N_RANDOM_SUBSETS = 10_000
RIDGE = 1e-3
SEED = 42
QURAN_ACTUAL_Z = 12.149  # from exp138 receipt — locked headline scalar


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def per_unit_finals_skel_lengths(unit_list, normaliser):
    """Return (finals_per_unit, skeletons_per_unit, verse_word_counts_per_unit)."""
    finals_pu, skel_pu, wc_pu = [], [], []
    for u in unit_list:
        finals, sk, wc = [], [], []
        for v in u["verses"]:
            norm = normaliser(v)
            if norm:
                finals.append(norm[-1])
                sk.append(norm)
                wc.append(len(v.split()))
        if finals:
            finals_pu.append(finals)
            skel_pu.append(" ".join(sk))
            wc_pu.append(wc)
    return finals_pu, skel_pu, wc_pu


def compute_corpus_20_axes(unit_list, normaliser, A_T):
    """Compute the 20-axis raw feature vector for one corpus."""
    finals_pu, skel_pu, wc_pu = per_unit_finals_skel_lengths(unit_list, normaliser)

    # --- Pooled
    all_finals = [f for uf in finals_pu for f in uf]
    fc = Counter(all_finals)
    total = sum(fc.values())
    p_pool = np.array([fc[k] / total for k in sorted(fc)], dtype=float)
    HEL_pool = shannon_entropy(p_pool)
    pmax_pool = float(p_pool.max())
    Delta_pool = math.log2(A_T) - HEL_pool
    pooled_skel = " ".join(skel_pu)
    bg = [pooled_skel[i:i+2] for i in range(len(pooled_skel) - 1) if not pooled_skel[i:i+2].isspace()]
    bigram_distinct_pool = (len(set(bg)) / len(bg)) if bg else 0.0
    pooled_bytes = pooled_skel.encode("utf-8")
    gz = gzip.compress(pooled_bytes, compresslevel=9)
    gzip_eff_pool = len(gz) / max(len(pooled_bytes), 1)

    # --- Per-unit H_EL
    pu_H = []
    for uf in finals_pu:
        c = Counter(uf)
        t = sum(c.values())
        p = np.array([c[k] / t for k in sorted(c)], dtype=float)
        pu_H.append(shannon_entropy(p))
    pu_H = np.array(pu_H, dtype=float)

    # --- Per-unit p_max
    pu_pmax = []
    for uf in finals_pu:
        c = Counter(uf)
        t = sum(c.values())
        pu_pmax.append(max(c.values()) / t)
    pu_pmax = np.array(pu_pmax, dtype=float)

    # --- Per-unit VL_CV (in WORDS)
    pu_vlcv = []
    for wc in wc_pu:
        if len(wc) >= 2:
            arr = np.array(wc, dtype=float)
            mu = float(arr.mean())
            if mu > 0:
                pu_vlcv.append(float(arr.std(ddof=1) / mu))
    pu_vlcv = np.array(pu_vlcv, dtype=float) if pu_vlcv else np.zeros(1)

    log_A = math.log2(A_T)
    return {
        "HEL_pool": HEL_pool,
        "pmax_pool": pmax_pool,
        "bigram_distinct_pool": bigram_distinct_pool,
        "gzip_eff_pool": gzip_eff_pool,
        "Delta_pool": Delta_pool,
        "HEL_unit_p10": float(np.percentile(pu_H, 10)),
        "HEL_unit_p25": float(np.percentile(pu_H, 25)),
        "HEL_unit_median": float(np.percentile(pu_H, 50)),
        "HEL_unit_p75": float(np.percentile(pu_H, 75)),
        "HEL_unit_mean": float(pu_H.mean()),
        "pmax_unit_p25": float(np.percentile(pu_pmax, 25)),
        "pmax_unit_median": float(np.percentile(pu_pmax, 50)),
        "pmax_unit_p75": float(np.percentile(pu_pmax, 75)),
        "pmax_unit_mean": float(pu_pmax.mean()),
        "VL_CV_unit_p25": float(np.percentile(pu_vlcv, 25)),
        "VL_CV_unit_median": float(np.percentile(pu_vlcv, 50)),
        "VL_CV_unit_p75": float(np.percentile(pu_vlcv, 75)),
        "Delta_unit_p25": log_A - float(np.percentile(pu_H, 25)),
        "Delta_unit_median": log_A - float(np.percentile(pu_H, 50)),
        "Delta_unit_p10": log_A - float(np.percentile(pu_H, 10)),
        "_n_units": len(finals_pu),
    }


def stouffer_z_brown(z_subset_row, R_subset):
    """Stouffer Z with Brown effective K from a correlation matrix R_subset."""
    K = len(z_subset_row)
    sumR = float(R_subset.sum())
    # F1 fix 2026-04-29: Brown-Stouffer divisor is sqrt(sumR), not
    # sqrt(K^2/sumR). K_eff = K^2/sumR is Cheverud-Li-Ji M_eff (Bonferroni
    # alpha adjustment), retained for receipt diagnostics.
    K_eff = (K * K) / max(sumR, 1e-12)
    return float(z_subset_row.sum() / math.sqrt(max(sumR, 1e-12))), K_eff


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)

    # ---- Load corpora using exp138's loader
    from experiments.exp138_Quran_Footprint_Joint_Z.run import load_corpora_normalisers
    corpora, norm_lookup = load_corpora_normalisers()

    # ---- Compute 20-axis raw matrix M (12 × 20)
    print("# Computing 20-axis raw feature matrix per corpus...", flush=True)
    raw = {}
    for c in EXPECTED_CORPORA:
        units = corpora[c]
        norm_name = units[0]["normaliser"]
        norm_fn = norm_lookup[norm_name]
        raw[c] = compute_corpus_20_axes(units, norm_fn, ALPHABET_SIZES[c])

    axis_names = [a for a, _ in AXIS_POOL]
    quran_signs = {a: s for a, s in AXIS_POOL}
    M_raw = np.zeros((12, 20))
    for i, c in enumerate(EXPECTED_CORPORA):
        for j, a in enumerate(axis_names):
            M_raw[i, j] = raw[c][a]
    quran_idx = EXPECTED_CORPORA.index("quran")

    # ---- Build z-matrix using non-Quran rows as cluster (Quran-favorable signs)
    non_q_idx = [i for i in range(12) if i != quran_idx]
    M_z_q = np.zeros_like(M_raw)
    for j, a in enumerate(axis_names):
        col = M_raw[non_q_idx, j]
        mu, sd = float(col.mean()), float(col.std(ddof=1))
        sd = sd if sd > 1e-12 else 1.0
        M_z_q[:, j] = quran_signs[a] * (M_raw[:, j] - mu) / sd
    R_q = np.corrcoef(M_z_q[non_q_idx, :], rowvar=False)

    # ============================================================
    # Sub-task A — Leave-one-axis-out (LOAO) on the original 8
    # ============================================================
    print("# Sub-task A: leave-one-axis-out on the original 8 axes...", flush=True)
    orig_8_idx = [axis_names.index(a) for a in ORIGINAL_8_AXES]
    M_z_orig8 = M_z_q[:, orig_8_idx]
    R_orig8 = R_q[np.ix_(orig_8_idx, orig_8_idx)]
    # Full Z for sanity check (should match exp138's 12.149)
    Z_full, K_eff_full = stouffer_z_brown(M_z_orig8[quran_idx, :], R_orig8)
    print(f"#   Full 8-axis Quran Z_brown (sanity): {Z_full:.4f} "
          f"(exp138 was 12.149, K_eff_full={K_eff_full:.3f})", flush=True)

    loao_results = {}
    for k, ax_name in enumerate(ORIGINAL_8_AXES):
        keep = [i for i in range(8) if i != k]
        z_row = M_z_orig8[quran_idx, keep]
        R_sub = R_orig8[np.ix_(keep, keep)]
        z_brown_loao, k_eff_loao = stouffer_z_brown(z_row, R_sub)
        # Compute rank of Quran in this LOAO subset
        z_loao_all = []
        for c_idx in range(12):
            zc = M_z_orig8[c_idx, keep]
            zb, _ = stouffer_z_brown(zc, R_sub)
            z_loao_all.append(zb)
        rank_q = int(np.argsort(-np.array(z_loao_all)).tolist().index(quran_idx)) + 1
        loao_results[ax_name] = {
            "Z_brown_drop_this_axis": z_brown_loao,
            "K_eff": k_eff_loao,
            "quran_rank_of_12": rank_q,
            "drop_from_full": Z_full - z_brown_loao,
        }
        print(f"#   drop {ax_name.ljust(22)} → Z={z_brown_loao:6.3f}  "
              f"rank={rank_q}  drop={Z_full - z_brown_loao:+.3f}", flush=True)

    loao_Zs = np.array([loao_results[a]["Z_brown_drop_this_axis"] for a in ORIGINAL_8_AXES])
    loao_min = float(loao_Zs.min())
    loao_n_geq_8 = int((loao_Zs >= 8.0).sum())
    dominant_axis = max(loao_results, key=lambda a: loao_results[a]["drop_from_full"])

    # ============================================================
    # Sub-task B — Random K=8 from 20-axis pool null
    # ============================================================
    print(f"# Sub-task B: random K=8 from 20-pool null (N={N_RANDOM_SUBSETS:,})...", flush=True)
    rng = np.random.default_rng(SEED)
    quran_Zs_random = np.zeros(N_RANDOM_SUBSETS)
    quran_rank1_count = 0
    z_q = M_z_q[quran_idx, :]
    for it in range(N_RANDOM_SUBSETS):
        idx = rng.choice(20, size=8, replace=False)
        z_row = z_q[idx]
        R_sub = R_q[np.ix_(idx, idx)]
        z_brown, _ = stouffer_z_brown(z_row, R_sub)
        quran_Zs_random[it] = z_brown
        # Compute rank of Quran in this random subset
        z_all = []
        for c_idx in range(12):
            zc = M_z_q[c_idx, idx]
            zb, _ = stouffer_z_brown(zc, R_sub)
            z_all.append(zb)
        if int(np.argmax(z_all)) == quran_idx:
            quran_rank1_count += 1
        if (it + 1) % 2000 == 0:
            print(f"#     iter {it + 1:6,}/{N_RANDOM_SUBSETS:,} ...", flush=True)

    frac_q_geq_actual = float((quran_Zs_random >= QURAN_ACTUAL_Z).mean())
    quran_rank1_freq = quran_rank1_count / N_RANDOM_SUBSETS
    print(f"#   Random K=8: Quran median Z = {np.median(quran_Zs_random):.3f}, "
          f"max = {quran_Zs_random.max():.3f}, p99 = {np.percentile(quran_Zs_random, 99):.3f}",
          flush=True)
    print(f"#   Fraction with Z ≥ {QURAN_ACTUAL_Z}: {frac_q_geq_actual:.4f}", flush=True)
    print(f"#   Quran rank-1 frequency: {quran_rank1_freq:.4f}", flush=True)

    # ============================================================
    # Sub-task C — Inverse test (per-corpus best K=8)
    # ============================================================
    print("# Sub-task C: inverse test — each corpus's best K=8 from 20 pool...", flush=True)
    # For each corpus c, build c-centered z-matrix using non-c rows as cluster,
    # take |z_c| absolute values (sign-free; corpus can be extreme either way),
    # sort by |z_c|, take top-8, compute joint |Z|.
    inverse_results = {}
    for ci, c in enumerate(EXPECTED_CORPORA):
        non_c_idx = [i for i in range(12) if i != ci]
        M_z_c = np.zeros_like(M_raw)
        for j, a in enumerate(axis_names):
            col = M_raw[non_c_idx, j]
            mu, sd = float(col.mean()), float(col.std(ddof=1))
            sd = sd if sd > 1e-12 else 1.0
            M_z_c[:, j] = (M_raw[:, j] - mu) / sd
        abs_z_c = np.abs(M_z_c[ci, :])
        top8_idx = np.argsort(-abs_z_c)[:8]
        # Sign-aligned for c-extreme: use sign of M_z_c[ci, j]
        signs = np.sign(M_z_c[ci, top8_idx])
        z_row = signs * M_z_c[ci, top8_idx]  # = abs_z_c[top8_idx]
        # Brown adjustment using non-c correlation
        R_c = np.corrcoef(M_z_c[non_c_idx, :], rowvar=False)
        R_sub = R_c[np.ix_(top8_idx, top8_idx)]
        # Apply same signs to correlation matrix
        D = np.diag(signs)
        R_sub_signed = D @ R_sub @ D
        z_brown_c, k_eff_c = stouffer_z_brown(z_row, R_sub_signed)
        inverse_results[c] = {
            "best_8_axes": [axis_names[j] for j in top8_idx],
            "best_signs": [int(s) for s in signs],
            "best_joint_Z_brown": z_brown_c,
            "K_eff": k_eff_c,
        }

    sorted_inverse = sorted(inverse_results.items(), key=lambda kv: -kv[1]["best_joint_Z_brown"])
    quran_inverse_Z = inverse_results["quran"]["best_joint_Z_brown"]
    max_non_quran_inverse_Z = max(
        inverse_results[c]["best_joint_Z_brown"]
        for c in EXPECTED_CORPORA if c != "quran"
    )
    runner_up_corpus = max(
        (c for c in EXPECTED_CORPORA if c != "quran"),
        key=lambda c: inverse_results[c]["best_joint_Z_brown"],
    )
    print(f"#   Quran's best-8 joint Z: {quran_inverse_Z:.3f}", flush=True)
    print(f"#   Max non-Quran best-8 joint Z: {max_non_quran_inverse_Z:.3f} ({runner_up_corpus})",
          flush=True)
    print("#   TOP-3 by inverse-test best joint Z:", flush=True)
    for c, info in sorted_inverse[:3]:
        print(f"#     {c.ljust(18)} Z = {info['best_joint_Z_brown']:+6.3f}  "
              f"axes={info['best_8_axes'][:3]}...", flush=True)

    # ============================================================
    # Acceptance
    # ============================================================
    A1 = (loao_n_geq_8 >= 7) and (loao_min >= 6.0)
    A2 = frac_q_geq_actual < 0.01
    A3 = max_non_quran_inverse_Z < QURAN_ACTUAL_Z
    A4 = quran_rank1_freq >= 0.99
    # A5: dominant axis is in per-unit H_EL family
    per_unit_HEL_axes = {"HEL_unit_p25", "HEL_unit_median", "Delta_unit_median"}
    A5 = dominant_axis in per_unit_HEL_axes

    n_pass = sum([A1, A2, A3])
    if A1 and A2 and A3:
        verdict = "PASS_no_sharpshooter"
        verdict_reason = (f"All 3 PASS: LOAO {loao_n_geq_8}/8 ≥ 8 (min {loao_min:.2f}); "
                          f"random-K=8 frac {frac_q_geq_actual:.4f} < 0.01; "
                          f"inverse max non-Q {max_non_quran_inverse_Z:.2f} < {QURAN_ACTUAL_Z}")
    elif n_pass == 2:
        verdict = "PARTIAL_low_sharpshooter_risk"
        verdict_reason = f"{n_pass}/3 PASS"
    else:
        verdict = "FAIL_sharpshooter_risk_present"
        verdict_reason = f"Only {n_pass}/3 PASS"

    # Audit
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    matrix_hash = hashlib.sha256(M_raw.tobytes()).hexdigest()
    audit_report = {
        "feature_matrix_20axis_sha256": matrix_hash,
        "n_units_per_corpus": {c: raw[c]["_n_units"] for c in EXPECTED_CORPORA},
        "Z_full_sanity_check_vs_exp138": Z_full,
        "Z_full_diff_from_exp138_locked": Z_full - QURAN_ACTUAL_Z,
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H93_Sharpshooter_Audit",
        "hypothesis": ("The Q-Footprint joint Z = 12.149σ (exp138/FN20) survives three "
                       "sharpshooter tests: LOAO (≥7/8 axes ≥ 8.0, min ≥ 6.0); "
                       "random K=8 from 20-pool (frac ≥ 12.149 < 0.01); "
                       "inverse (max non-Quran best-8 < 12.149)."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "AXIS_POOL_size": 20,
            "ORIGINAL_8_AXES": ORIGINAL_8_AXES,
            "N_RANDOM_SUBSETS": N_RANDOM_SUBSETS,
            "RIDGE": RIDGE, "SEED": SEED,
            "QURAN_ACTUAL_Z_LOCKED": QURAN_ACTUAL_Z,
        },
        "results": {
            "raw_feature_matrix": {c: {a: raw[c][a] for a in axis_names} for c in EXPECTED_CORPORA},
            "sub_A_LOAO": {
                "Z_full_sanity": Z_full,
                "K_eff_full": K_eff_full,
                "per_axis_drop": loao_results,
                "min_LOAO_Z_brown": loao_min,
                "n_LOAO_Z_brown_geq_8": loao_n_geq_8,
                "dominant_axis": dominant_axis,
                "dominant_axis_drop": loao_results[dominant_axis]["drop_from_full"],
            },
            "sub_B_random_K8_null": {
                "N": N_RANDOM_SUBSETS,
                "quran_Z_distribution": {
                    "min": float(quran_Zs_random.min()),
                    "p25": float(np.percentile(quran_Zs_random, 25)),
                    "median": float(np.median(quran_Zs_random)),
                    "p75": float(np.percentile(quran_Zs_random, 75)),
                    "p95": float(np.percentile(quran_Zs_random, 95)),
                    "p99": float(np.percentile(quran_Zs_random, 99)),
                    "max": float(quran_Zs_random.max()),
                    "mean": float(quran_Zs_random.mean()),
                    "std": float(quran_Zs_random.std(ddof=1)),
                },
                "fraction_quran_Z_geq_actual_12p149": frac_q_geq_actual,
                "quran_rank1_frequency": quran_rank1_freq,
            },
            "sub_C_inverse_test": {
                "per_corpus_best_8": inverse_results,
                "quran_inverse_Z": quran_inverse_Z,
                "max_non_quran_inverse_Z": max_non_quran_inverse_Z,
                "runner_up_corpus": runner_up_corpus,
                "gap_quran_minus_max_non_quran": quran_inverse_Z - max_non_quran_inverse_Z,
            },
            "criteria_pass": {
                "A1_LOAO_robust": A1,
                "A2_random_K8_frac_lt_001": A2,
                "A3_inverse_quran_dominates": A3,
                "A4_random_K8_quran_rank1_geq_99pct": A4,
                "A5_dominant_axis_per_unit_HEL": A5,
                "n_pass_of_3_core": n_pass,
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


if __name__ == "__main__":
    main()
