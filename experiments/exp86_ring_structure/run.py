"""
exp86_ring_structure/run.py
============================
H20: Ring Structure / Chiasm — Quantitative Validation.

Motivation
    Ring composition (A-B-C-B'-A') is the most widely documented
    large-scale literary structure in the Quran per classical scholarship.
    Never quantitatively tested.

Ring score definition
    For a unit of n verses with per-verse feature vectors f_i:
      palindromic_sim = mean cos(f_i, f_{n-1-i}) for i in 0..n//2-1
      random_sim = mean cos(f_i, f_j) for random i!=j pairs
      ring_score = palindromic_sim - random_sim

    ring_score > 0 means mirrored pairs are more similar than random.

Protocol (frozen before execution)
    T1. Per-verse features: character 3-gram TF-IDF vectors (richer than 5D).
    T2. Per unit: compute ring_score.
    T3. Permutation null: shuffle verse order 1000 times, recompute.
    T4. Compare Quran ring_score distribution to controls.
    T5. Individual surah ranking; check Surah 5, 12.

Pre-registered thresholds
    CONFIRMED:    mean Quran R > 0, MW p < 1e-5, d >= 0.5
    SUGGESTIVE:   R > 0 with p < 0.05
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats
from scipy.spatial.distance import cosine as cosine_dist

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

EXP = "exp86_ring_structure"
SEED = 42
N_PERM = 1000
MIN_VERSES = 7
N_RANDOM_PAIRS = 200

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _verses_to_matrix(verses: list[str], n_gram: int = 3) -> np.ndarray:
    """Convert verses to a TF matrix using char n-grams. Returns (n_verses, n_features)."""
    # Collect all n-grams
    all_ngrams: dict[str, int] = {}
    verse_counters = []
    for v in verses:
        t = _strip_d(v)
        c: dict[str, int] = {}
        for i in range(len(t) - n_gram + 1):
            ng = t[i:i + n_gram]
            c[ng] = c.get(ng, 0) + 1
            if ng not in all_ngrams:
                all_ngrams[ng] = len(all_ngrams)
        verse_counters.append(c)

    n_feat = len(all_ngrams)
    if n_feat == 0:
        return np.zeros((len(verses), 1))

    mat = np.zeros((len(verses), n_feat), dtype=np.float32)
    for i, c in enumerate(verse_counters):
        for ng, cnt in c.items():
            mat[i, all_ngrams[ng]] = cnt

    # L2 normalise rows for cosine = dot product
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat /= norms
    return mat


def _pal_mean_fast(sim_matrix: np.ndarray) -> float:
    """Palindromic mean from precomputed similarity matrix."""
    n = sim_matrix.shape[0]
    half = n // 2
    if half == 0:
        return 0.0
    return float(np.mean([sim_matrix[i, n - 1 - i] for i in range(half)]))


def _ring_score_from_sim(sim_matrix: np.ndarray, global_mean: float) -> tuple[float, float, float]:
    """Ring score from precomputed similarity matrix."""
    n = sim_matrix.shape[0]
    if n < MIN_VERSES:
        return float("nan"), float("nan"), float("nan")
    pal = _pal_mean_fast(sim_matrix)
    return pal, global_mean, float(pal - global_mean)


def _analyse_corpus(units, rng: np.random.RandomState) -> dict:
    """Compute ring scores and permutation p-values for all units."""
    scores = []
    p_values = []
    unit_details = []

    for u in units:
        if len(u.verses) < MIN_VERSES:
            continue

        mat = _verses_to_matrix(u.verses)
        n = mat.shape[0]

        # Precompute full cosine similarity matrix (n x n)
        sim = mat @ mat.T  # cosine since rows are L2-normalised

        # Global mean similarity (off-diagonal)
        mask = ~np.eye(n, dtype=bool)
        global_mean = float(sim[mask].mean())

        pal, rand, rs = _ring_score_from_sim(sim, global_mean)

        if np.isnan(rs):
            continue

        # Permutation test: shuffle indices, read palindromic pairs from sim
        n_geq = 0
        half = n // 2
        for _ in range(N_PERM):
            perm = rng.permutation(n)
            pal_perm = np.mean([sim[perm[i], perm[n - 1 - i]] for i in range(half)])
            rs_perm = float(pal_perm) - global_mean
            if rs_perm >= rs:
                n_geq += 1
        p = (n_geq + 1) / (N_PERM + 1)

        scores.append(rs)
        p_values.append(p)
        unit_details.append({
            "label": u.label,
            "n_verses": len(u.verses),
            "palindromic_sim": round(pal, 6),
            "random_sim": round(rand, 6),
            "ring_score": round(rs, 6),
            "p_perm": round(p, 4),
        })

    return {
        "n_units": len(scores),
        "scores": scores,
        "p_values": p_values,
        "details": unit_details,
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

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        rng = np.random.RandomState(SEED)
        t_start = time.time()

        r = _analyse_corpus(units, rng)
        dt = time.time() - t_start

        arr = np.array(r["scores"])
        mean_rs = float(arr.mean()) if len(arr) > 0 else float("nan")
        std_rs = float(arr.std(ddof=1)) if len(arr) > 1 else 0
        n_sig = sum(1 for p in r["p_values"] if p < 0.05)

        results[cname] = {
            "n_units": r["n_units"],
            "ring_score_mean": round(mean_rs, 6),
            "ring_score_std": round(std_rs, 6),
            "n_significant_005": n_sig,
            "frac_significant": round(n_sig / r["n_units"], 4) if r["n_units"] > 0 else 0,
            "_scores": r["scores"],
            "_details": r["details"],
        }

        print(f"[{EXP}] {cname:20s}: n={r['n_units']:4d}  "
              f"R̄={mean_rs:+.6f}±{std_rs:.6f}  "
              f"sig={n_sig}/{r['n_units']}  ({dt:.1f}s)")

    # --- T4: Quran vs controls ---
    print(f"\n[{EXP}] === T4: Quran vs controls ===")
    q_scores = results["quran"]["_scores"]

    ctrl_scores_all = []
    for cname in ARABIC_CTRL:
        c_scores = results[cname]["_scores"]
        ctrl_scores_all.extend(c_scores)
        if len(c_scores) >= 3 and len(q_scores) >= 3:
            d = ((np.mean(q_scores) - np.mean(c_scores)) /
                 np.sqrt((np.var(q_scores, ddof=1) + np.var(c_scores, ddof=1)) / 2))
            _, p = sp_stats.mannwhitneyu(q_scores, c_scores, alternative='greater')
            print(f"  Quran vs {cname:20s}: d={d:+.3f}  MW p_greater={p:.4e}")

    # Pooled
    if len(ctrl_scores_all) >= 3 and len(q_scores) >= 3:
        d_all = ((np.mean(q_scores) - np.mean(ctrl_scores_all)) /
                 np.sqrt((np.var(q_scores, ddof=1) + np.var(ctrl_scores_all, ddof=1)) / 2))
        _, p_all = sp_stats.mannwhitneyu(q_scores, ctrl_scores_all, alternative='greater')
    else:
        d_all = float("nan")
        p_all = float("nan")

    print(f"\n  Quran vs pooled ctrl: d={d_all:+.4f}, MW p_greater={p_all:.4e}")
    print(f"  Quran mean R = {np.mean(q_scores):+.6f}")
    print(f"  Ctrl mean R  = {np.mean(ctrl_scores_all):+.6f}")

    # --- T5: Famous surahs ---
    print(f"\n[{EXP}] === T5: Individual surah ranking ===")
    q_details = results["quran"]["_details"]
    q_sorted = sorted(q_details, key=lambda x: x["ring_score"], reverse=True)

    print(f"  Top 10 surahs by ring score:")
    for i, d in enumerate(q_sorted[:10], 1):
        sig = "*" if d["p_perm"] < 0.05 else ""
        print(f"    {i:2d}. {d['label']:30s} R={d['ring_score']:+.6f}  "
              f"p={d['p_perm']:.4f} {sig}")

    # Check Surah 5 and 12
    print(f"\n  Famous test cases:")
    for d in q_details:
        if "Ma'ida" in d["label"] or "maid" in d["label"].lower() or d["label"].startswith("5"):
            print(f"    Surah 5 (Al-Ma'ida): R={d['ring_score']:+.6f}, p={d['p_perm']:.4f}")
        if "Yusuf" in d["label"] or "yusuf" in d["label"].lower() or d["label"].startswith("12"):
            print(f"    Surah 12 (Yusuf):    R={d['ring_score']:+.6f}, p={d['p_perm']:.4f}")

    # --- Verdict ---
    q_mean_positive = np.mean(q_scores) > 0
    if q_mean_positive and p_all < 1e-5 and d_all >= 0.5:
        verdict = "CONFIRMED"
    elif q_mean_positive and p_all < 0.05:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran mean R = {np.mean(q_scores):+.6f}")
    print(f"  d(R) vs ctrl = {d_all:+.4f}, p_greater = {p_all:.4e}")
    print(f"  Quran sig units: {results['quran']['n_significant_005']}/{results['quran']['n_units']}")
    print(f"{'=' * 60}")

    # Clean report
    report_results = {}
    for k, v in results.items():
        report_results[k] = {kk: vv for kk, vv in v.items()
                             if not kk.startswith("_")}
        # Add top-10 details for Quran
        if k == "quran":
            report_results[k]["top10_surahs"] = q_sorted[:10]

    report = {
        "experiment": EXP,
        "hypothesis": "H20 — Does the Quran exhibit statistically significant ring composition?",
        "schema_version": 1,
        "method": "char-3gram cosine, palindromic vs random within-unit similarity",
        "n_perm": N_PERM,
        "per_corpus": report_results,
        "quran_vs_ctrl": {
            "d_ring_score": round(float(d_all), 4),
            "p_greater": float(p_all),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
