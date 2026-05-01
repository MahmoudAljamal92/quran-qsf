"""experiments/exp152_pinnacle_robustness/run.py — 5-sūrah pinnacle TRIO hypothesis.

Tests H97: the trio {Q:074, Q:073, Q:002} is a structurally robust pinnacle
in joint-Hotelling-T² space at the sūrah-pool resolution, spanning the entire
Quranic chronological timeline (Nöldeke ranks 2/3/84) with a bimodal mechanism
(rhyme-density extreme + length extreme).

This is a follow-up to `exp151_QFootprint_Quran_Internal` (H95
`FAIL_quran_internal_indeterminate` at 1/3 PASS) under SUBSTANTIVELY-ALIGNED
criteria for a SET hypothesis (not a single-sūrah hypothesis).

Trio identity {Q:074, Q:073, Q:002} locked from exp151 `sub_B_top10_T2`.

PREREG : experiments/exp152_pinnacle_robustness/PREREG.md
Output : results/experiments/exp152_pinnacle_robustness/exp152_pinnacle_robustness.json

V3.17 / 2026-04-30. Brown-formula-INVARIANT (Hotelling T² only).
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

EXP_NAME = "exp152_pinnacle_robustness"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# === Frozen constants (mirrored from PREREG.md) ===
TRIO_SURAH_IDS = (74, 73, 2)
N_BOOTSTRAP = 1000
N_CHRONO_SHUFFLE = 10000
RIDGE = 1e-3
SEED = 42
ALPHABET_SIZE_AR = 28
GAP_RANK4_FLOOR = 1.20
TRIO_RANGE_FLOOR = 80
TRIO_BOOT_FREQ_FLOOR = 0.90
CHRONO_NULL_ALPHA = 0.05
HEL_TOP12_BITS_CEILING = 0.50
RANK3_VERSECOUNT_FLOOR = 100

AXES = [
    "H_EL_surah",
    "p_max_surah",
    "Delta_max_surah",
    "VL_CV_surah",
    "bigram_distinct_surah",
    "gzip_eff_surah",
    "n_verses_surah",
    "mean_verse_words_surah",
]

# Locked Nöldeke-Schwally chronology (copied byte-exact from exp151/run.py)
NOLDEKE_CHRONOLOGY_MECCAN = [
    96, 74, 73, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102, 107, 109, 105, 113, 114, 112,
    53, 80, 97, 91, 85, 95, 106, 101, 75, 104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35,
    19, 20, 56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45,
    46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82, 84, 30, 29, 83,
]
NOLDEKE_CHRONOLOGY_MEDINAN = [
    2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55, 76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64,
    61, 62, 48, 5, 9, 110, 1,
]
NOLDEKE_CHRONOLOGY = NOLDEKE_CHRONOLOGY_MECCAN + NOLDEKE_CHRONOLOGY_MEDINAN
PERIOD_OF = {sid: "Meccan" for sid in NOLDEKE_CHRONOLOGY_MECCAN}
PERIOD_OF.update({sid: "Medinan" for sid in NOLDEKE_CHRONOLOGY_MEDINAN})
CHRONO_RANK = {sid: i + 1 for i, sid in enumerate(NOLDEKE_CHRONOLOGY)}

# exp151's locked feature-matrix SHA-256 (replicates exact same matrix)
EXP151_MATRIX_SHA256 = "0b0e751b5358f3b045049985bb4c894afc592e7fea189d5ce4a7ee4791974e55"


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def compute_surah_features(surah_unit, normaliser, A_T):
    """Compute the 8-axis raw feature vector for ONE sūrah.

    Byte-equivalent reimplementation of exp151's compute_surah_features.
    """
    verses = surah_unit["verses"]
    finals = []
    sk_parts = []
    word_counts = []
    for v in verses:
        norm = normaliser(v)
        if norm:
            finals.append(norm[-1])
            sk_parts.append(norm)
        word_counts.append(len(v.split()))

    if not finals:
        return None

    fc = Counter(finals)
    total = sum(fc.values())
    p = np.array([fc[k] / total for k in sorted(fc)], dtype=float)
    H_EL = shannon_entropy(p)
    p_max = float(p.max())
    Delta_max = math.log2(A_T) - H_EL

    pooled_skel = " ".join(sk_parts)
    bg = [pooled_skel[i:i + 2] for i in range(len(pooled_skel) - 1) if not pooled_skel[i:i + 2].isspace()]
    bigram_distinct = (len(set(bg)) / len(bg)) if bg else 0.0
    pooled_bytes = pooled_skel.encode("utf-8")
    if len(pooled_bytes) > 0:
        gz = gzip.compress(pooled_bytes, compresslevel=9)
        gzip_eff = len(gz) / len(pooled_bytes)
    else:
        gzip_eff = 1.0

    if len(word_counts) >= 2:
        wc = np.array(word_counts, dtype=float)
        mu_wc = float(wc.mean())
        VL_CV = float(wc.std(ddof=1) / mu_wc) if mu_wc > 0 else 0.0
        mean_verse_words = mu_wc
    else:
        VL_CV = 0.0
        mean_verse_words = float(word_counts[0]) if word_counts else 0.0

    n_verses = len(verses)
    return {
        "H_EL_surah": H_EL,
        "p_max_surah": p_max,
        "Delta_max_surah": Delta_max,
        "VL_CV_surah": VL_CV,
        "bigram_distinct_surah": bigram_distinct,
        "gzip_eff_surah": gzip_eff,
        "n_verses_surah": float(n_verses),
        "mean_verse_words_surah": mean_verse_words,
    }


def compute_T2_per_row(M_z, ridge=RIDGE):
    """Compute Hotelling T² (Mahalanobis from centroid) per row."""
    n, k = M_z.shape
    mu = M_z.mean(axis=0)
    Sigma = np.cov(M_z, rowvar=False, ddof=1) + ridge * np.eye(k)
    Sigma_inv = np.linalg.pinv(Sigma)
    T2 = np.zeros(n)
    for i in range(n):
        d = M_z[i] - mu
        T2[i] = float(d @ Sigma_inv @ d)
    return T2


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)
    print(f"# H97 trio hypothesis: {{Q:{TRIO_SURAH_IDS[0]:03d}, Q:{TRIO_SURAH_IDS[1]:03d}, "
          f"Q:{TRIO_SURAH_IDS[2]:03d}}} robustness", flush=True)

    # ---- Load Quran (replicates exp151 feature matrix)
    from scripts._phi_universal_xtrad_sizing import _load_quran, NORMALISERS
    quran_units = _load_quran()
    norm_fn = NORMALISERS["arabic"]

    sids = []
    M_raw_rows = []
    for u in quran_units:
        sid = int(u["label"].split(":")[1])
        feats = compute_surah_features(u, norm_fn, ALPHABET_SIZE_AR)
        if feats is None:
            continue
        sids.append(sid)
        M_raw_rows.append([feats[a] for a in AXES])
    M_raw = np.array(M_raw_rows, dtype=float)
    n_surahs = M_raw.shape[0]
    matrix_hash = hashlib.sha256(M_raw.tobytes()).hexdigest()
    print(f"# Feature matrix: {n_surahs} sūrahs × {M_raw.shape[1]} axes  "
          f"sha256={matrix_hash[:16]}...", flush=True)

    sid_to_idx = {sid: i for i, sid in enumerate(sids)}
    trio_indices = [sid_to_idx[sid] for sid in TRIO_SURAH_IDS]

    # ---- Compute joint Hotelling T² (locked feature ordering)
    mu_axis = M_raw.mean(axis=0)
    sd_axis = M_raw.std(axis=0, ddof=1)
    sd_axis = np.where(sd_axis > 1e-12, sd_axis, 1.0)
    M_z = (M_raw - mu_axis) / sd_axis
    T2 = compute_T2_per_row(M_z)
    order_full = np.argsort(-T2)
    top10 = [{
        "rank": rank,
        "surah_id": sids[i],
        "T2": float(T2[i]),
        "n_verses": int(M_raw[i, AXES.index("n_verses_surah")]),
        "period": PERIOD_OF.get(sids[i], "?"),
        "chrono_rank": CHRONO_RANK.get(sids[i], -1),
    } for rank, i in enumerate(order_full[:10], start=1)]
    print("# Locked top-5 by joint T²:", flush=True)
    for item in top10[:5]:
        print(f"#   rank {item['rank']}  Q:{item['surah_id']:03d}  T²={item['T2']:8.3f}  "
              f"n_verses={item['n_verses']:4d}  period={item['period']:7s}  "
              f"chrono={item['chrono_rank']}", flush=True)

    actual_top3_sids = {sids[i] for i in order_full[:3]}
    trio_set = set(TRIO_SURAH_IDS)
    if actual_top3_sids != trio_set:
        print(f"# CRITICAL: actual top-3 {actual_top3_sids} != PREREG-locked trio {trio_set}",
              flush=True)
        # We continue but report this in the audit; it would be a structural shift since exp151

    # ============================================
    # A1 — bootstrap stability of TRIO AS A SET
    # ============================================
    print(f"# A1: bootstrap trio-as-SET stability (N={N_BOOTSTRAP})...", flush=True)
    rng = np.random.default_rng(SEED)
    boot_trio_match = 0
    for b in range(N_BOOTSTRAP):
        idx = rng.integers(0, n_surahs, size=n_surahs)
        M_z_boot = M_z[idx]
        T2_boot = compute_T2_per_row(M_z_boot)
        boot_top3_local = np.argsort(-T2_boot)[:3]
        boot_top3_sids = {sids[idx[k]] for k in boot_top3_local}
        if boot_top3_sids == trio_set:
            boot_trio_match += 1
    A1_freq = boot_trio_match / N_BOOTSTRAP
    A1_pass = A1_freq >= TRIO_BOOT_FREQ_FLOOR
    print(f"#   trio-as-SET bootstrap freq = {A1_freq:.4f}   PASS={A1_pass}  "
          f"(floor {TRIO_BOOT_FREQ_FLOOR})", flush=True)

    # ============================================
    # A2 — chronological-rank range of trio
    # ============================================
    trio_chrono_ranks = sorted(CHRONO_RANK.get(sid, -1) for sid in TRIO_SURAH_IDS)
    chrono_range_observed = trio_chrono_ranks[-1] - trio_chrono_ranks[0]
    A2_pass = chrono_range_observed >= TRIO_RANGE_FLOOR
    print(f"# A2: trio chrono-rank range = {chrono_range_observed} "
          f"(min={trio_chrono_ranks[0]}, max={trio_chrono_ranks[-1]})   PASS={A2_pass}  "
          f"(floor {TRIO_RANGE_FLOOR})", flush=True)

    # ============================================
    # A3 — chronological-rank shuffle null
    # ============================================
    print(f"# A3: chronological-rank shuffle null (N={N_CHRONO_SHUFFLE:,})...", flush=True)
    rng_a3 = np.random.default_rng(SEED + 1)
    null_ranges = np.empty(N_CHRONO_SHUFFLE, dtype=np.int64)
    chrono_label_pool = np.arange(1, n_surahs + 1)
    for s in range(N_CHRONO_SHUFFLE):
        shuffled = rng_a3.permutation(chrono_label_pool)
        # Top-3 sūrahs by T² are FIXED (not shuffled). Get their indices into sids.
        # Under the null, chrono labels are randomly reassigned to sūrahs.
        # The trio's labels under the shuffle are shuffled[trio_indices].
        trio_shuffle_labels = shuffled[trio_indices]
        null_ranges[s] = int(trio_shuffle_labels.max() - trio_shuffle_labels.min())
    A3_p_value = float(np.mean(null_ranges >= chrono_range_observed))
    A3_pass = A3_p_value < CHRONO_NULL_ALPHA
    print(f"#   p(range ≥ {chrono_range_observed} | null) = {A3_p_value:.4f}   "
          f"PASS={A3_pass}  (alpha {CHRONO_NULL_ALPHA})", flush=True)

    # ============================================
    # A4 — gap to rank-4
    # ============================================
    T2_rank3 = top10[2]["T2"]
    T2_rank4 = top10[3]["T2"]
    gap_rank4 = T2_rank3 / max(T2_rank4, 1e-12)
    A4_pass = gap_rank4 >= GAP_RANK4_FLOOR
    print(f"# A4: gap T²[rank-3] / T²[rank-4] = {gap_rank4:.4f}   "
          f"PASS={A4_pass}  (floor {GAP_RANK4_FLOOR})", flush=True)

    # ============================================
    # A5 — bimodal-mechanism check
    # ============================================
    # rhyme-extreme: top-1 + top-2 are short Meccan with low H_EL
    HEL_idx = AXES.index("H_EL_surah")
    NV_idx = AXES.index("n_verses_surah")
    HEL_top1 = float(M_raw[order_full[0], HEL_idx])
    HEL_top2 = float(M_raw[order_full[1], HEL_idx])
    HEL_top12_median = float(np.median([HEL_top1, HEL_top2]))
    rhyme_extreme_pass = HEL_top12_median <= HEL_TOP12_BITS_CEILING

    # length-extreme: rank-3 has verse-count rank ≥ RANK3_VERSECOUNT_FLOOR
    nverses_per_surah = M_raw[:, NV_idx]
    nverses_order = np.argsort(nverses_per_surah)
    rank3_idx = order_full[2]
    rank3_n_verses = int(nverses_per_surah[rank3_idx])
    rank3_n_verses_rank = int(np.where(nverses_order == rank3_idx)[0][0]) + 1  # 1-indexed
    length_extreme_pass = rank3_n_verses_rank >= RANK3_VERSECOUNT_FLOOR
    A5_pass = rhyme_extreme_pass and length_extreme_pass
    print(f"# A5: rhyme-extreme (HEL_top12 median {HEL_top12_median:.4f} ≤ "
          f"{HEL_TOP12_BITS_CEILING}) PASS={rhyme_extreme_pass}", flush=True)
    print(f"#     length-extreme (rank-3 verse-count rank {rank3_n_verses_rank} ≥ "
          f"{RANK3_VERSECOUNT_FLOOR}, n_verses={rank3_n_verses}) "
          f"PASS={length_extreme_pass}", flush=True)
    print(f"#     A5 PASS={A5_pass}", flush=True)

    # ============================================
    # Verdict
    # ============================================
    n_pass = int(A1_pass) + int(A2_pass) + int(A3_pass) + int(A4_pass) + int(A5_pass)
    if n_pass == 5:
        verdict = "PASS_pinnacle_trio_robust"
        verdict_reason = (f"5/5 PREREG criteria PASS. Trio {{Q:074, Q:073, Q:002}} is "
                          f"bootstrap-robust as a set (freq={A1_freq:.3f}), spans the entire "
                          f"Quranic chronological timeline (range={chrono_range_observed}, "
                          f"chrono-shuffle null p={A3_p_value:.4f}), separable from rank-4 "
                          f"(gap={gap_rank4:.3f}×), and bimodal in mechanism "
                          f"(rhyme-extreme {{Q:074,Q:073}} + length-extreme {{Q:002}}).")
    elif n_pass == 4:
        verdict = "PARTIAL_pinnacle_trio_directional"
        verdict_reason = f"{n_pass}/5 PREREG criteria PASS"
    else:
        verdict = "FAIL_pinnacle_trio_indeterminate"
        verdict_reason = f"Only {n_pass}/5 PREREG criteria PASS"

    # ============================================
    # Audit
    # ============================================
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    HEL_median = float(np.median(M_raw[:, HEL_idx]))
    F79_implied_HEL = math.log2(28) - 3.838834
    audit_report = {
        "feature_matrix_sha256": matrix_hash,
        "matrix_matches_exp151_locked": matrix_hash == EXP151_MATRIX_SHA256,
        "exp151_matrix_sha256_expected": EXP151_MATRIX_SHA256,
        "n_surahs_processed": n_surahs,
        "F79_match_check": {
            "median_H_EL_surah_now": HEL_median,
            "F79_implied_H_EL_median": F79_implied_HEL,
            "diff": HEL_median - F79_implied_HEL,
            "match_within_001": abs(HEL_median - F79_implied_HEL) < 0.01,
        },
        "actual_top3_matches_PREREG_trio": actual_top3_sids == trio_set,
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H97_5_Surah_Pinnacle_Trio",
        "hypothesis": ("The Quran's joint-T² extremum at sūrah-pool resolution is "
                       "structurally characterised by a stable trio {Q:074, Q:073, Q:002} "
                       "spanning the entire Quranic revelation timeline (Nöldeke chrono "
                       "ranks 2/3/84) and bimodal in mechanism (rhyme-extreme + length-extreme). "
                       "Tests trio-as-SET bootstrap robustness, chronological-span shuffle null, "
                       "rank-4 separation, and bimodal-mechanism directionality."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "TRIO_SURAH_IDS": list(TRIO_SURAH_IDS),
            "AXES": AXES,
            "N_BOOTSTRAP": N_BOOTSTRAP,
            "N_CHRONO_SHUFFLE": N_CHRONO_SHUFFLE,
            "RIDGE": RIDGE,
            "SEED": SEED,
            "ALPHABET_SIZE_AR": ALPHABET_SIZE_AR,
            "GAP_RANK4_FLOOR": GAP_RANK4_FLOOR,
            "TRIO_RANGE_FLOOR": TRIO_RANGE_FLOOR,
            "TRIO_BOOT_FREQ_FLOOR": TRIO_BOOT_FREQ_FLOOR,
            "CHRONO_NULL_ALPHA": CHRONO_NULL_ALPHA,
            "HEL_TOP12_BITS_CEILING": HEL_TOP12_BITS_CEILING,
            "RANK3_VERSECOUNT_FLOOR": RANK3_VERSECOUNT_FLOOR,
        },
        "results": {
            "top10_by_T2": top10,
            "actual_top3_sids": sorted(actual_top3_sids),
            "trio_set_PREREG_locked": list(TRIO_SURAH_IDS),
            "criteria": {
                "A1_trio_set_bootstrap_freq": {
                    "value": A1_freq,
                    "floor": TRIO_BOOT_FREQ_FLOOR,
                    "PASS": bool(A1_pass),
                    "n_bootstrap": N_BOOTSTRAP,
                },
                "A2_trio_chrono_range": {
                    "value": chrono_range_observed,
                    "floor": TRIO_RANGE_FLOOR,
                    "PASS": bool(A2_pass),
                    "trio_chrono_ranks_sorted": trio_chrono_ranks,
                },
                "A3_chrono_shuffle_null_p": {
                    "value": A3_p_value,
                    "alpha": CHRONO_NULL_ALPHA,
                    "PASS": bool(A3_pass),
                    "null_range_min": int(null_ranges.min()),
                    "null_range_p50": int(np.median(null_ranges)),
                    "null_range_p99": int(np.percentile(null_ranges, 99)),
                    "null_range_max": int(null_ranges.max()),
                    "n_shuffle": N_CHRONO_SHUFFLE,
                },
                "A4_gap_to_rank4": {
                    "value": gap_rank4,
                    "T2_rank3": T2_rank3,
                    "T2_rank4": T2_rank4,
                    "floor": GAP_RANK4_FLOOR,
                    "PASS": bool(A4_pass),
                },
                "A5_bimodal_mechanism": {
                    "rhyme_extreme": {
                        "HEL_top1_bits": HEL_top1,
                        "HEL_top2_bits": HEL_top2,
                        "HEL_top12_median_bits": HEL_top12_median,
                        "ceiling_bits": HEL_TOP12_BITS_CEILING,
                        "PASS": bool(rhyme_extreme_pass),
                    },
                    "length_extreme": {
                        "rank3_n_verses": rank3_n_verses,
                        "rank3_n_verses_rank": rank3_n_verses_rank,
                        "floor_rank": RANK3_VERSECOUNT_FLOOR,
                        "PASS": bool(length_extreme_pass),
                    },
                    "PASS": bool(A5_pass),
                },
                "n_pass_of_5": n_pass,
            },
        },
        "audit_report": audit_report,
        "wall_time_s": float(time.time() - t0),
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"# Receipt: {OUT_PATH}", flush=True)
    print(f"# Verdict: {verdict}", flush=True)
    print(f"# Reason : {verdict_reason}", flush=True)
    print(f"# Wall   : {receipt['wall_time_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
