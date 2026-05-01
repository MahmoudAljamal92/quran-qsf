"""experiments/exp138_Quran_Footprint_Joint_Z/run.py — The Quran Footprint pinnacle.

Computes a single joint statistic (Stouffer Z + Hotelling T²) over K=8 pre-registered
universal-feature axes across the 12-corpus pool and runs a column-shuffle permutation
null. Closes the V3.15.1 sprint with a decisive Quran-alone joint extremum.

PREREG: experiments/exp138_Quran_Footprint_Joint_Z/PREREG.md
Output: results/experiments/exp138_Quran_Footprint_Joint_Z/exp138_Quran_Footprint_Joint_Z.json
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EXP_NAME = "exp138_Quran_Footprint_Joint_Z"
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

# Pre-registered K=8 axes
AXES = [
    "z_HEL_pool",
    "z_pmax_pool",
    "z_HEL_unit_median",
    "z_HEL_unit_p25",
    "z_VL_CV_median",
    "z_bigram_distinct_pool",
    "z_gzip_eff_pool",
    "z_Delta_max_unit",
]
# Quran-extreme direction: +1 means HIGHER value is more Quran-like, -1 means LOWER
SIGN_QURAN_EXTREME = {
    "z_HEL_pool": -1,         # lower H_EL → more Quran-like
    "z_pmax_pool": +1,        # higher p_max → more Quran-like
    "z_HEL_unit_median": -1,  # lower median H_EL → more Quran-like
    "z_HEL_unit_p25": -1,     # lower p25 H_EL → more Quran-like
    "z_VL_CV_median": +1,     # higher VL_CV → more Quran-like
    "z_bigram_distinct_pool": -1,  # lower distinct ratio → more Quran-like
    "z_gzip_eff_pool": -1,    # lower gzip → more Quran-like
    "z_Delta_max_unit": +1,   # higher Δ_max → more Quran-like
}

N_PERM = 10_000
RIDGE = 1e-3
SEED = 42


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def per_unit_finals(unit_list, normaliser):
    out = []
    for u in unit_list:
        finals = []
        for v in u["verses"]:
            norm = normaliser(v)
            if norm:
                finals.append(norm[-1])
        if finals:
            out.append(finals)
    return out


def per_unit_skeletons(unit_list, normaliser):
    """Return per-unit space-joined normalised verse skeletons."""
    out = []
    for u in unit_list:
        sk = []
        for v in u["verses"]:
            norm = normaliser(v)
            if norm:
                sk.append(norm)
        out.append(" ".join(sk))
    return out


def per_unit_verse_lengths(unit_list, normaliser):
    out = []
    for u in unit_list:
        L = []
        for v in u["verses"]:
            norm = normaliser(v)
            if norm:
                L.append(len(norm))
        out.append(L)
    return out


def compute_corpus_features(unit_list, normaliser, A_T):
    """Compute the 8 axes' raw values for one corpus."""
    finals_per_unit = per_unit_finals(unit_list, normaliser)
    skeletons_per_unit = per_unit_skeletons(unit_list, normaliser)
    verse_lens_per_unit = per_unit_verse_lengths(unit_list, normaliser)

    # Pooled finals
    all_finals = [f for uf in finals_per_unit for f in uf]
    finals_counter = Counter(all_finals)
    total = sum(finals_counter.values())
    p_pool = np.array([finals_counter[k] / total for k in sorted(finals_counter)], dtype=float)
    H_pool = shannon_entropy(p_pool)
    p_max_pool = float(p_pool.max())

    # Per-unit H_EL
    per_unit_H = []
    for uf in finals_per_unit:
        c = Counter(uf)
        t = sum(c.values())
        p = np.array([c[k] / t for k in sorted(c)], dtype=float)
        per_unit_H.append(shannon_entropy(p))
    per_unit_H = np.array(per_unit_H)
    HEL_unit_median = float(np.median(per_unit_H))
    HEL_unit_p25 = float(np.percentile(per_unit_H, 25))

    # Per-unit verse length CV (std/mean), then median
    cvs = []
    for L in verse_lens_per_unit:
        if len(L) >= 2:
            mu, sd = float(np.mean(L)), float(np.std(L, ddof=0))
            if mu > 0:
                cvs.append(sd / mu)
    VL_CV_median = float(np.median(cvs)) if cvs else 0.0

    # Pooled bigram distinct ratio + gzip efficiency on full pooled skeleton
    pooled_skel = " ".join(skeletons_per_unit)
    bigrams = [pooled_skel[i:i + 2] for i in range(len(pooled_skel) - 1) if not pooled_skel[i:i + 2].isspace()]
    distinct = len(set(bigrams))
    total_b = len(bigrams)
    bigram_distinct_ratio = (distinct / total_b) if total_b > 0 else 0.0

    pooled_bytes = pooled_skel.encode("utf-8")
    gz = gzip.compress(pooled_bytes, compresslevel=9)
    gzip_eff = len(gz) / max(len(pooled_bytes), 1)

    Delta_max_unit = math.log2(A_T) - HEL_unit_median

    return {
        "z_HEL_pool": H_pool,
        "z_pmax_pool": p_max_pool,
        "z_HEL_unit_median": HEL_unit_median,
        "z_HEL_unit_p25": HEL_unit_p25,
        "z_VL_CV_median": VL_CV_median,
        "z_bigram_distinct_pool": bigram_distinct_ratio,
        "z_gzip_eff_pool": gzip_eff,
        "z_Delta_max_unit": Delta_max_unit,
        "_n_units": len(finals_per_unit),
        "_alphabet_size": A_T,
    }


def load_corpora_normalisers():
    from scripts._phi_universal_xtrad_sizing import (
        _load_quran, _load_arabic_peers, _load_hebrew_tanakh,
        _load_greek_nt, _load_pali, _load_avestan, NORMALISERS,
    )
    from scripts._rigveda_loader_v2 import load_rigveda, _normalise_sanskrit

    print("# Loading 12 corpora...", flush=True)
    t = time.time()
    corpora = {}
    corpora["quran"] = _load_quran()
    arabic_peers = _load_arabic_peers()
    for name, units in arabic_peers.items():
        corpora[name] = units
    corpora["hebrew_tanakh"] = _load_hebrew_tanakh()
    corpora["greek_nt"] = _load_greek_nt()
    corpora["pali"] = _load_pali()
    corpora["avestan_yasna"] = _load_avestan()
    corpora["rigveda"] = load_rigveda()
    print(f"# Loaded in {time.time() - t:.1f}s", flush=True)

    norm_lookup = dict(NORMALISERS)
    norm_lookup["sanskrit"] = _normalise_sanskrit
    return corpora, norm_lookup


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)

    # ---- Load
    corpora, norm_lookup = load_corpora_normalisers()
    print("# Computing 8-axis raw feature matrix per corpus...", flush=True)
    raw = {}
    for c in EXPECTED_CORPORA:
        units = corpora[c]
        norm_name = units[0]["normaliser"]
        norm_fn = norm_lookup[norm_name]
        A_T = ALPHABET_SIZES[c]
        raw[c] = compute_corpus_features(units, norm_fn, A_T)
        v = raw[c]
        print(f"#   {c.ljust(18)} HEL_pool={v['z_HEL_pool']:.4f} pmax={v['z_pmax_pool']:.4f} "
              f"HEL_unit_med={v['z_HEL_unit_median']:.4f} Δ_max={v['z_Delta_max_unit']:.4f}",
              flush=True)

    # ---- Build 12 × 8 feature matrix M_raw
    M_raw = np.zeros((12, 8))
    for i, c in enumerate(EXPECTED_CORPORA):
        for j, ax in enumerate(AXES):
            M_raw[i, j] = raw[c][ax]

    # ---- Z-score per axis using NON-QURAN cluster (Quran row excluded from mean/std)
    quran_idx = EXPECTED_CORPORA.index("quran")
    non_q_idx = [i for i in range(12) if i != quran_idx]
    M_z = np.zeros_like(M_raw)
    axis_stats = {}
    for j, ax in enumerate(AXES):
        col_non_q = M_raw[non_q_idx, j]
        mu = float(col_non_q.mean())
        sd = float(col_non_q.std(ddof=1))
        sd = sd if sd > 1e-12 else 1.0
        s = SIGN_QURAN_EXTREME[ax]
        M_z[:, j] = s * (M_raw[:, j] - mu) / sd
        axis_stats[ax] = {"mu_non_quran": mu, "sd_non_quran": sd, "sign_quran_extreme": s}

    # ---- Sub-task C: Stouffer Z with Brown-Westhavik effective K
    print("# Sub-task C: Stouffer Z (raw and Brown-adjusted)...", flush=True)
    Z_sums = M_z.sum(axis=1)
    K = M_z.shape[1]
    Z_raw = Z_sums / math.sqrt(K)

    # Correlation of axes from non-Quran rows (no Quran leakage)
    R = np.corrcoef(M_z[non_q_idx, :], rowvar=False)
    sum_R = float(R.sum())
    # Cheverud-Li-Ji M_eff (kept for receipt diagnostics; NOT the Brown
    # divisor; F1 fix 2026-04-29: Brown-Stouffer combined Z under correlated
    # axes is sum_z / sqrt(Var(sum_z)) = sum_z / sqrt(sum_R), since each
    # z_i has Var=1 and pairwise covariances given by R.)
    K_eff = (K * K) / max(sum_R, 1e-12)
    Z_brown = Z_sums / math.sqrt(max(sum_R, 1e-12))

    rank_Z_raw_quran = int(np.argsort(-Z_raw).tolist().index(quran_idx)) + 1
    rank_Z_brown_quran = int(np.argsort(-Z_brown).tolist().index(quran_idx)) + 1

    # Sort and report
    Z_raw_sorted = sorted(zip(EXPECTED_CORPORA, Z_raw), key=lambda kv: -kv[1])
    Z_brown_sorted = sorted(zip(EXPECTED_CORPORA, Z_brown), key=lambda kv: -kv[1])
    quran_Z_raw = float(Z_raw[quran_idx])
    quran_Z_brown = float(Z_brown[quran_idx])
    rank2_Z_brown = float(Z_brown_sorted[1][1])
    rank2_name_brown = Z_brown_sorted[1][0]
    gap_Z_brown = quran_Z_brown - rank2_Z_brown

    print(f"#   K = {K},  K_eff (Brown) = {K_eff:.3f}", flush=True)
    print(f"#   Quran Z_raw = {quran_Z_raw:.3f}  rank = {rank_Z_raw_quran}/12", flush=True)
    print(f"#   Quran Z_brown = {quran_Z_brown:.3f}  rank = {rank_Z_brown_quran}/12  "
          f"gap to {rank2_name_brown} = {gap_Z_brown:.3f}", flush=True)

    # ---- Sub-task D: Hotelling T² in 8-D z-space
    print("# Sub-task D: Hotelling T² in 8-D z-space...", flush=True)
    mu_z = M_z[non_q_idx, :].mean(axis=0)
    Sigma = np.cov(M_z[non_q_idx, :], rowvar=False, ddof=1) + RIDGE * np.eye(K)
    Sigma_inv = np.linalg.pinv(Sigma)
    T2 = np.zeros(12)
    for i in range(12):
        d = M_z[i, :] - mu_z
        T2[i] = float(d @ Sigma_inv @ d)
    rank_T2_quran = int(np.argsort(-T2).tolist().index(quran_idx)) + 1
    quran_T2 = float(T2[quran_idx])
    T2_sorted = sorted(zip(EXPECTED_CORPORA, T2), key=lambda kv: -kv[1])
    rank2_T2 = float(T2_sorted[1][1])
    rank2_T2_name = T2_sorted[1][0]
    gap_T2 = quran_T2 - rank2_T2
    print(f"#   Quran T² = {quran_T2:.2f}  rank = {rank_T2_quran}/12  "
          f"gap to {rank2_T2_name} = {gap_T2:.2f}", flush=True)

    # ---- Sub-task E: Column-shuffle permutation null
    print(f"# Sub-task E: Column-shuffle permutation null (N={N_PERM:,})...", flush=True)
    rng = np.random.default_rng(SEED)
    perm_max_Z_brown = np.zeros(N_PERM)
    perm_max_T2 = np.zeros(N_PERM)
    perm_quran_rank1_Z = 0
    perm_quran_rank1_T2 = 0
    for it in range(N_PERM):
        # Column-shuffle: independently permute each column of M_z
        M_perm = M_z.copy()
        for j in range(K):
            M_perm[:, j] = rng.permutation(M_perm[:, j])
        Z_p = M_perm.sum(axis=1) / math.sqrt(max(sum_R, 1e-12))  # F1 fix: use sqrt(sum_R), same as actual
        T2_p = np.array([
            (M_perm[i] - mu_z) @ Sigma_inv @ (M_perm[i] - mu_z)
            for i in range(12)
        ])
        perm_max_Z_brown[it] = float(Z_p.max())
        perm_max_T2[it] = float(T2_p.max())
        if int(np.argmax(Z_p)) == quran_idx:
            perm_quran_rank1_Z += 1
        if int(np.argmax(T2_p)) == quran_idx:
            perm_quran_rank1_T2 += 1
        if (it + 1) % 2000 == 0:
            print(f"#     iter {it + 1:6,}/{N_PERM:,} ...", flush=True)

    p_Z = float((perm_max_Z_brown >= quran_Z_brown).mean())
    p_T2 = float((perm_max_T2 >= quran_T2).mean())
    print(f"#   Column-shuffle null: p_Z = {p_Z:.5f}, p_T² = {p_T2:.5f}", flush=True)
    print(f"#   Quran rank-1 in column-shuffled max Z: {perm_quran_rank1_Z / N_PERM:.4f}",
          flush=True)

    # ---- Sub-task F: per-axis decomposition
    sub_F = {}
    for j, ax in enumerate(AXES):
        col_z = M_z[:, j]
        rank_q = int(np.argsort(-col_z).tolist().index(quran_idx)) + 1
        sub_F[ax] = {
            "quran_z": float(col_z[quran_idx]),
            "quran_rank_of_12": rank_q,
            "non_quran_max_z": float(col_z[non_q_idx].max()),
        }

    # Acceptance criteria
    A1 = quran_Z_brown >= 8.0
    A2 = rank_Z_brown_quran == 1
    A3 = gap_Z_brown >= 4.0
    A4 = rank_T2_quran == 1
    A5 = p_Z < 0.001
    A6 = p_T2 < 0.001
    n_pass = sum([A1, A2, A3, A4, A5, A6])
    if n_pass == 6:
        verdict = "PASS_q_footprint_pinnacle"
        verdict_reason = (f"All 6 criteria PASS: Z_brown={quran_Z_brown:.3f}≥8, "
                          f"rank=1, gap={gap_Z_brown:.3f}≥4, T²-rank=1, p_Z={p_Z:.5f}, "
                          f"p_T²={p_T2:.5f}")
    elif n_pass >= 4:
        verdict = "PARTIAL_q_footprint_directional"
        verdict_reason = f"{n_pass}/6 criteria PASS; joint Quran-extremum directional but not full pinnacle"
    else:
        verdict = "FAIL_q_footprint_no_joint_pinnacle"
        verdict_reason = f"Only {n_pass}/6 criteria PASS"

    # Audit
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    matrix_hash = hashlib.sha256(M_raw.tobytes()).hexdigest()
    z_matrix_hash = hashlib.sha256(M_z.tobytes()).hexdigest()
    audit_report = {
        "feature_matrix_sha256": matrix_hash,
        "z_matrix_sha256": z_matrix_hash,
        "alphabet_sizes": ALPHABET_SIZES,
        "n_units_per_corpus": {c: raw[c]["_n_units"] for c in EXPECTED_CORPORA},
        "axis_correlation_R_first_2_rows": R[:2, :].tolist(),
        "axis_correlation_sum": sum_R,
        "K_eff_brown": K_eff,
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H91_Q_Footprint_Joint_Z",
        "hypothesis": ("Across K=8 independent universal-feature axes, the Quran's joint "
                       "Stouffer Z (Brown-adjusted) exceeds 8.0, is rank-1 of 12 with gap "
                       "≥ 4.0 to runner-up, and column-shuffle null gives p < 0.001."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "K_axes": K, "N_PERM": N_PERM, "RIDGE": RIDGE, "SEED": SEED,
            "axes": AXES, "sign_quran_extreme": SIGN_QURAN_EXTREME,
        },
        "results": {
            "raw_feature_matrix": {
                c: {ax: raw[c][ax] for ax in AXES} for c in EXPECTED_CORPORA
            },
            "z_matrix": {
                c: {AXES[j]: float(M_z[i, j]) for j in range(K)}
                for i, c in enumerate(EXPECTED_CORPORA)
            },
            "axis_stats": axis_stats,
            "sub_C_stouffer_Z": {
                "K": K, "K_eff_brown": K_eff,
                "axis_correlation_sum": sum_R,
                "Z_raw_per_corpus_sorted_desc":
                    [{"corpus": c, "Z": float(z)} for c, z in Z_raw_sorted],
                "Z_brown_per_corpus_sorted_desc":
                    [{"corpus": c, "Z": float(z)} for c, z in Z_brown_sorted],
                "quran_Z_raw": quran_Z_raw,
                "quran_Z_brown": quran_Z_brown,
                "quran_rank_Z_raw_of_12": rank_Z_raw_quran,
                "quran_rank_Z_brown_of_12": rank_Z_brown_quran,
                "rank_2_corpus": rank2_name_brown,
                "rank_2_Z_brown": rank2_Z_brown,
                "gap_Z_brown_quran_to_rank2": gap_Z_brown,
            },
            "sub_D_hotelling": {
                "T2_per_corpus_sorted_desc":
                    [{"corpus": c, "T2": float(t)} for c, t in T2_sorted],
                "quran_T2": quran_T2,
                "quran_rank_T2_of_12": rank_T2_quran,
                "rank_2_corpus": rank2_T2_name,
                "rank_2_T2": rank2_T2,
                "gap_T2_quran_to_rank2": gap_T2,
            },
            "sub_E_permutation_null": {
                "N_PERM": N_PERM,
                "p_Z": p_Z, "p_T2": p_T2,
                "perm_max_Z_brown_p95": float(np.percentile(perm_max_Z_brown, 95)),
                "perm_max_Z_brown_p99": float(np.percentile(perm_max_Z_brown, 99)),
                "perm_max_T2_p95": float(np.percentile(perm_max_T2, 95)),
                "perm_max_T2_p99": float(np.percentile(perm_max_T2, 99)),
                "quran_rank1_freq_Z": perm_quran_rank1_Z / N_PERM,
                "quran_rank1_freq_T2": perm_quran_rank1_T2 / N_PERM,
            },
            "sub_F_per_axis": sub_F,
            "criteria_pass": {
                "A1_Z_brown_geq_8": A1, "A2_Z_brown_rank1": A2,
                "A3_gap_geq_4": A3, "A4_T2_rank1": A4,
                "A5_p_Z_lt_001": A5, "A6_p_T2_lt_001": A6,
                "n_pass_of_6": n_pass,
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
    print("=== TOP-3 by joint Z (Brown-adjusted) ===")
    for c, z in Z_brown_sorted[:3]:
        print(f"  {c.ljust(18)} Z = {z:+.3f}")
    print("=== TOP-3 by Hotelling T² ===")
    for c, t in T2_sorted[:3]:
        print(f"  {c.ljust(18)} T² = {t:.2f}")


if __name__ == "__main__":
    main()
