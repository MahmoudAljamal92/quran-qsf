"""experiments/exp151_QFootprint_Quran_Internal/run.py — Quran-internal joint extremum.

Treats each of the 114 sūrahs as a unit and computes the joint Hotelling T² /
sign-free Stouffer Z per sūrah. Identifies the joint-extremum sūrahs and
cross-tabulates with Nöldeke-Schwally chronology.

PREREG: experiments/exp151_QFootprint_Quran_Internal/PREREG.md
Output: results/experiments/exp151_QFootprint_Quran_Internal/exp151_QFootprint_Quran_Internal.json
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

EXP_NAME = "exp151_QFootprint_Quran_Internal"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

ALPHABET_SIZE_AR = 28

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

N_BOOTSTRAP = 1000
RIDGE = 1e-3
SEED = 42

# Locked Nöldeke-Schwally chronology (copied from scripts/compute_pareto_and_chrono.py)
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


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def compute_surah_features(surah_unit, normaliser, A_T):
    """Compute the 8-axis raw feature vector for ONE sūrah."""
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
    bg = [pooled_skel[i:i+2] for i in range(len(pooled_skel) - 1) if not pooled_skel[i:i+2].isspace()]
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
    """Compute Hotelling T² (Mahalanobis from centroid) per row of standardized matrix."""
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

    # Load Quran
    from scripts._phi_universal_xtrad_sizing import _load_quran, NORMALISERS
    quran_units = _load_quran()
    print(f"# Loaded {len(quran_units)} Quran sūrahs", flush=True)
    norm_fn = NORMALISERS["arabic"]

    # ---- Sub-task A: per-sūrah feature extraction
    print("# Sub-task A: per-sūrah 8-axis feature extraction...", flush=True)
    sids = []
    M_raw_rows = []
    for u in quran_units:
        sid = int(u["label"].split(":")[1])
        feats = compute_surah_features(u, norm_fn, ALPHABET_SIZE_AR)
        if feats is None:
            print(f"# WARN: sūrah {sid} has no extractable features, skipping", flush=True)
            continue
        sids.append(sid)
        M_raw_rows.append([feats[a] for a in AXES])
    M_raw = np.array(M_raw_rows, dtype=float)
    n_surahs = M_raw.shape[0]
    print(f"# Feature matrix: {n_surahs} sūrahs × {M_raw.shape[1]} axes", flush=True)

    sub_A = {
        "n_surahs": n_surahs,
        "axes": AXES,
        "per_axis_stats": {
            ax: {
                "median": float(np.median(M_raw[:, j])),
                "p5": float(np.percentile(M_raw[:, j], 5)),
                "p95": float(np.percentile(M_raw[:, j], 95)),
                "mean": float(M_raw[:, j].mean()),
                "std": float(M_raw[:, j].std(ddof=1)),
                "cv": float(M_raw[:, j].std(ddof=1) / M_raw[:, j].mean())
                      if M_raw[:, j].mean() != 0 else float("nan"),
            }
            for j, ax in enumerate(AXES)
        },
    }
    for ax in AXES:
        s = sub_A["per_axis_stats"][ax]
        print(f"#   {ax.ljust(26)} median={s['median']:8.4f}  mean={s['mean']:8.4f}  "
              f"std={s['std']:8.4f}  CV={s['cv']:6.3f}", flush=True)

    # ---- Sub-task B: Hotelling T² per sūrah (114-sūrah centroid + cov)
    print("# Sub-task B: Hotelling T² per sūrah...", flush=True)
    mu_axis = M_raw.mean(axis=0)
    sd_axis = M_raw.std(axis=0, ddof=1)
    sd_axis = np.where(sd_axis > 1e-12, sd_axis, 1.0)
    M_z = (M_raw - mu_axis) / sd_axis
    T2 = compute_T2_per_row(M_z)
    order = np.argsort(-T2)
    top10_T2 = []
    for rank, i in enumerate(order[:10], start=1):
        sid = sids[i]
        top10_T2.append({
            "rank": rank,
            "surah_id": sid,
            "T2": float(T2[i]),
            "n_verses": int(M_raw[i, AXES.index("n_verses_surah")]),
            "period": PERIOD_OF.get(sid, "?"),
            "chrono_rank": CHRONO_RANK.get(sid, -1),
        })
        print(f"#   T² rank {rank}: Q:{sid:03d}  T²={T2[i]:8.3f}  "
              f"n_verses={int(M_raw[i, AXES.index('n_verses_surah')])}  "
              f"period={PERIOD_OF.get(sid, '?')}  chrono={CHRONO_RANK.get(sid, -1)}",
              flush=True)
    top1_T2 = top10_T2[0]["T2"]
    top2_T2 = top10_T2[1]["T2"]
    top1_top2_ratio = top1_T2 / max(top2_T2, 1e-12)

    # ---- Sub-task C: sign-free joint Stouffer (Σ z²)^0.5
    joint_Z_signfree = np.sqrt((M_z ** 2).sum(axis=1))
    order_Z = np.argsort(-joint_Z_signfree)
    top10_signfree = []
    for rank, i in enumerate(order_Z[:10], start=1):
        sid = sids[i]
        top10_signfree.append({
            "rank": rank,
            "surah_id": sid,
            "joint_Z_signfree": float(joint_Z_signfree[i]),
            "period": PERIOD_OF.get(sid, "?"),
            "chrono_rank": CHRONO_RANK.get(sid, -1),
        })

    # ---- Sub-task D: chronological cross-tabulation of top-10
    period_counts_top10 = Counter(item["period"] for item in top10_T2)
    print(f"# Sub-task D: top-10 by T² period distribution: {dict(period_counts_top10)}",
          flush=True)
    top3_periods = list(set(item["period"] for item in top10_T2[:3]))
    period_diversity_top3 = len(top3_periods)

    # ---- Sub-task E: bootstrap stability of top-1 sūrah
    print(f"# Sub-task E: bootstrap stability (N={N_BOOTSTRAP})...", flush=True)
    rng = np.random.default_rng(SEED)
    top1_sid_actual = sids[order[0]]
    boot_top1_match = 0
    boot_top3_overlap = 0
    actual_top3_sids = {item["surah_id"] for item in top10_T2[:3]}
    for b in range(N_BOOTSTRAP):
        idx = rng.integers(0, n_surahs, size=n_surahs)
        M_z_boot = M_z[idx]
        T2_boot = compute_T2_per_row(M_z_boot)
        boot_top_idx = int(np.argmax(T2_boot))
        boot_top_sid = sids[idx[boot_top_idx]]
        if boot_top_sid == top1_sid_actual:
            boot_top1_match += 1
        # Top-3 in bootstrap
        boot_top3_local = np.argsort(-T2_boot)[:3]
        boot_top3_sids = {sids[idx[k]] for k in boot_top3_local}
        if boot_top3_sids & actual_top3_sids:
            boot_top3_overlap += 1
        if (b + 1) % 200 == 0:
            print(f"#     iter {b + 1:4,}/{N_BOOTSTRAP:,} ...", flush=True)

    boot_top1_freq = boot_top1_match / N_BOOTSTRAP
    boot_top3_overlap_freq = boot_top3_overlap / N_BOOTSTRAP
    print(f"#   Bootstrap rank-1 freq: {boot_top1_freq:.4f}  "
          f"(point-estimate top-1 = Q:{top1_sid_actual:03d})", flush=True)

    # ---- Find highest-CV axis
    cv_per_axis = {ax: sub_A["per_axis_stats"][ax]["cv"] for ax in AXES}
    highest_cv_axis = max(cv_per_axis, key=lambda a: abs(cv_per_axis[a]) if not math.isnan(cv_per_axis[a]) else 0)

    # ---- Length classification of top-1
    top1_n_verses = int(M_raw[order[0], AXES.index("n_verses_surah")])
    if top1_n_verses <= 30:
        top1_length_class = "short"
    elif top1_n_verses <= 100:
        top1_length_class = "medium"
    else:
        top1_length_class = "long"

    # ---- Acceptance
    A1 = top1_top2_ratio >= 1.5
    A2 = period_diversity_top3 >= 2
    A3 = boot_top1_freq >= 0.80
    n_pass = sum([A1, A2, A3])
    if n_pass == 3:
        verdict = "PASS_quran_internal_extremum_identified"
        verdict_reason = (f"Top-1 sūrah Q:{top1_sid_actual:03d} ({top1_length_class}, "
                          f"{PERIOD_OF.get(top1_sid_actual, '?')}); ratio={top1_top2_ratio:.2f}; "
                          f"top-3 spans {period_diversity_top3} periods; "
                          f"boot rank-1 freq={boot_top1_freq:.2f}")
    elif n_pass == 2:
        verdict = "PARTIAL_quran_internal_directional"
        verdict_reason = f"{n_pass}/3 PASS"
    else:
        verdict = "FAIL_quran_internal_indeterminate"
        verdict_reason = f"Only {n_pass}/3 PASS"

    # Audit
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    matrix_hash = hashlib.sha256(M_raw.tobytes()).hexdigest()
    # Check H_EL median matches F79's locked Quran value (3.838834 bits = log2(28) - 0.96915)
    quran_HEL_median = float(np.median(M_raw[:, AXES.index("H_EL_surah")]))
    F79_implied_HEL = math.log2(28) - 3.838834  # = 0.969 bits
    audit_report = {
        "feature_matrix_sha256": matrix_hash,
        "n_surahs_processed": n_surahs,
        "F79_match_check": {
            "median_H_EL_surah_now": quran_HEL_median,
            "F79_implied_H_EL_median": F79_implied_HEL,
            "diff": quran_HEL_median - F79_implied_HEL,
            "match_within_001": abs(quran_HEL_median - F79_implied_HEL) < 0.01,
        },
        "highest_CV_axis": highest_cv_axis,
        "highest_CV_value": cv_per_axis[highest_cv_axis],
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H95_Quran_Internal",
        "hypothesis": ("The Quran's joint Q-Footprint at the sūrah-pool resolution "
                       "(114 sūrahs as units) exhibits a clear top-1 sūrah by joint "
                       "Hotelling T² with gap ≥ 1.5× to top-2, top-3 sūrahs span "
                       "≥ 2 chronological periods, and bootstrap rank-1 freq ≥ 80%."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "AXES": AXES, "N_BOOTSTRAP": N_BOOTSTRAP,
            "RIDGE": RIDGE, "SEED": SEED,
            "ALPHABET_SIZE_AR": ALPHABET_SIZE_AR,
        },
        "results": {
            "sub_A_per_surah_stats": sub_A,
            "sub_B_top10_T2": top10_T2,
            "sub_C_top10_signfree": top10_signfree,
            "sub_D_chronological_distribution": {
                "top10_period_counts": dict(period_counts_top10),
                "top3_unique_periods": top3_periods,
                "period_diversity_top3": period_diversity_top3,
            },
            "sub_E_bootstrap": {
                "top1_surah_id_actual": top1_sid_actual,
                "top1_period": PERIOD_OF.get(top1_sid_actual, "?"),
                "top1_n_verses": top1_n_verses,
                "top1_length_class": top1_length_class,
                "top1_top2_ratio": top1_top2_ratio,
                "boot_top1_match_freq": boot_top1_freq,
                "boot_top3_overlap_freq": boot_top3_overlap_freq,
            },
            "criteria_pass": {
                "A1_top1_gap_geq_1p5x_top2": A1,
                "A2_top3_spans_2plus_periods": A2,
                "A3_boot_top1_freq_geq_80pct": A3,
                "n_pass_of_3": n_pass,
            },
            "descriptive_A4_highest_cv_axis": highest_cv_axis,
            "descriptive_A5_top1_length_class": top1_length_class,
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
    print(f"=== Quran-internal joint extremum (top-5 by T²) ===")
    for item in top10_T2[:5]:
        print(f"  rank {item['rank']}  Q:{item['surah_id']:03d}  T² = {item['T2']:7.2f}  "
              f"n_verses = {item['n_verses']:4d}  period = {item['period']}  "
              f"chrono = {item['chrono_rank']}")


if __name__ == "__main__":
    main()
