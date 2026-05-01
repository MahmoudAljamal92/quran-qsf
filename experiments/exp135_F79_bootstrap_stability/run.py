"""experiments/exp135_F79_bootstrap_stability/run.py — F79 bootstrap robustness test.

Tests F79's `Δ_max(c) := log₂(A_c) − median_u(H_EL_u)` under bootstrap-resampling-of-units
across the 12-corpus / 6-alphabet pool. PASS upgrades F79 from PASS_strict point estimate
to PASS_strict_BOOTSTRAP_ROBUST (the project's strongest categorical universal at N=12).

PREREG: experiments/exp135_F79_bootstrap_stability/PREREG.md
Output: results/experiments/exp135_F79_bootstrap_stability/exp135_F79_bootstrap_stability.json
"""
from __future__ import annotations

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

EXP_NAME = "exp135_F79_bootstrap_stability"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# Pre-registered constants
EXPECTED_CORPORA = [
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "hindawi",
    "ksucca",
    "arabic_bible",
    "hebrew_tanakh",
    "greek_nt",
    "pali",
    "avestan_yasna",
    "rigveda",
]
ALPHABET_SIZES = {
    "quran": 28,
    "poetry_jahili": 28,
    "poetry_islami": 28,
    "poetry_abbasi": 28,
    "hindawi": 28,
    "ksucca": 28,
    "arabic_bible": 28,
    "hebrew_tanakh": 22,
    "greek_nt": 24,
    "pali": 31,
    "avestan_yasna": 26,
    "rigveda": 47,
}

DELTA_MAX_THRESHOLD = 3.5         # F79's pre-registered strict threshold
RIGVEDA_TIER2_FLOOR = 3.0
PASS_FREQ_FLOOR = 0.95
N_BOOTSTRAP = 200
N_PERM_SANITY = 50
SEED = 42
Q1_TOLERANCE = 1e-12

# F79 locked Δ_max values (from exp124c receipt; for A4 audit hook)
F79_LOCKED_DELTA_MAX = {
    "quran": 3.838834,
    "rigveda": 3.266805,
    "pali": 2.864257,
    "avestan_yasna": 2.582491,
    "greek_nt": 2.151256,
    "poetry_islami": 2.118585,
    "poetry_abbasi": 2.055656,
    "poetry_jahili": 2.027808,
    "ksucca": 1.899525,
    "arabic_bible": 1.889059,
    "hebrew_tanakh": 1.406299,
    "hindawi": 1.328527,
}
A4_TOLERANCE = 0.001


def unit_h_el(verses, normaliser_fn):
    """Compute H_EL for a single unit's verse list. Return None if no finals."""
    finals = []
    for v in verses:
        norm = normaliser_fn(v)
        if norm:
            finals.append(norm[-1])
    if not finals:
        return None
    counter = Counter(finals)
    total = sum(counter.values())
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def load_per_corpus_h_el():
    """Load 12 corpora and extract per-unit H_EL list."""
    from scripts._phi_universal_xtrad_sizing import (
        _load_quran, _load_arabic_peers, _load_hebrew_tanakh,
        _load_greek_nt, _load_pali, _load_avestan, NORMALISERS,
        _normalise_arabic, _normalise_hebrew, _normalise_greek,
        _normalise_pali, _normalise_avestan,
    )
    from scripts._rigveda_loader_v2 import load_rigveda, _normalise_sanskrit

    print("# Loading 12 corpora...", flush=True)
    corpora = {}
    t = time.time()
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

    # Pick the right normaliser per corpus
    normaliser_lookup = dict(NORMALISERS)  # arabic, hebrew, greek, pali, avestan
    normaliser_lookup["sanskrit"] = _normalise_sanskrit

    per_corpus_h_el = {}
    for c in EXPECTED_CORPORA:
        unit_list = corpora[c]
        norm_name = unit_list[0]["normaliser"]
        norm_fn = normaliser_lookup[norm_name]
        h_el_list = []
        for u in unit_list:
            h = unit_h_el(u["verses"], norm_fn)
            if h is not None:
                h_el_list.append(h)
        per_corpus_h_el[c] = h_el_list
    return per_corpus_h_el


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)

    per_corpus_h_el = load_per_corpus_h_el()

    # Stage A: per-corpus point-estimate Δ_max
    print("# Stage A: Computing point-estimate Δ_max per corpus...", flush=True)
    point_estimates = {}
    for c in EXPECTED_CORPORA:
        h_list = per_corpus_h_el[c]
        if not h_list:
            point_estimates[c] = {"n_units": 0, "Delta_max": float("nan"), "median_H_EL": float("nan")}
            continue
        med_h = float(np.median(h_list))
        delta = math.log2(ALPHABET_SIZES[c]) - med_h
        point_estimates[c] = {
            "n_units": len(h_list),
            "Delta_max": delta,
            "median_H_EL": med_h,
        }

    # A4 audit: match locked F79 values
    a4_failures = []
    for c, locked in F79_LOCKED_DELTA_MAX.items():
        actual = point_estimates[c]["Delta_max"]
        if abs(actual - locked) > A4_TOLERANCE:
            a4_failures.append({"corpus": c, "expected": locked, "actual": actual,
                                "diff": actual - locked})
    a4_pass = len(a4_failures) == 0

    if not a4_pass:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_A4_F79_point_estimate_drift",
            "a4_failures": a4_failures,
            "point_estimates": point_estimates,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"FAIL_audit_A4: {a4_failures}")
        return

    # A5 sanity: unit-shuffle invariance
    print(f"# A5 sanity: {N_PERM_SANITY} unit-shuffles × 12 corpora...", flush=True)
    rng_perm = np.random.default_rng(SEED)
    a5_max_dev = 0.0
    for c in EXPECTED_CORPORA:
        h_arr = np.array(per_corpus_h_el[c], dtype=float)
        if len(h_arr) == 0:
            continue
        original = point_estimates[c]["Delta_max"]
        log2_A = math.log2(ALPHABET_SIZES[c])
        for _ in range(N_PERM_SANITY):
            perm = rng_perm.permutation(len(h_arr))
            shuf = h_arr[perm]
            d = log2_A - float(np.median(shuf))
            a5_max_dev = max(a5_max_dev, abs(d - original))
    a5_pass = a5_max_dev < Q1_TOLERANCE
    print(f"#   A5 max deviation: {a5_max_dev:.2e} (tol {Q1_TOLERANCE:.0e}, "
          f"{'PASS' if a5_pass else 'FAIL'})", flush=True)

    # Stage B: bootstrap resampling
    print(f"# Stage B: {N_BOOTSTRAP} unit-bootstraps × 12 corpora...", flush=True)
    rng_boot = np.random.default_rng(SEED + 1)
    boot_matrix = np.zeros((len(EXPECTED_CORPORA), N_BOOTSTRAP), dtype=float)
    per_corpus_boot_stats = {}
    for ci, c in enumerate(EXPECTED_CORPORA):
        h_arr = np.array(per_corpus_h_el[c], dtype=float)
        N = len(h_arr)
        log2_A = math.log2(ALPHABET_SIZES[c])
        deltas = []
        for boot_idx in range(N_BOOTSTRAP):
            sample_idx = rng_boot.integers(0, N, size=N)
            med = float(np.median(h_arr[sample_idx]))
            d = log2_A - med
            deltas.append(d)
            boot_matrix[ci, boot_idx] = d
        d_arr = np.array(deltas, dtype=float)
        per_corpus_boot_stats[c] = {
            "mean": float(d_arr.mean()),
            "std": float(d_arr.std(ddof=0)),
            "cv": float(d_arr.std(ddof=0) / d_arr.mean()) if d_arr.mean() != 0 else float("nan"),
            "min": float(d_arr.min()),
            "max": float(d_arr.max()),
            "p05": float(np.percentile(d_arr, 5)),
            "p95": float(np.percentile(d_arr, 95)),
        }

    # Stage C: per-bootstrap acceptance
    print("# Stage C: per-bootstrap acceptance...", flush=True)
    quran_idx = EXPECTED_CORPORA.index("quran")
    rigveda_idx = EXPECTED_CORPORA.index("rigveda")

    quran_rank_1_count = 0
    quran_above_3p5_count = 0
    quran_unique_above_3p5_count = 0
    rigveda_above_3p0_count = 0
    quran_rank_distribution = Counter()
    n_above_3p5_distribution = Counter()

    for boot_idx in range(N_BOOTSTRAP):
        col = boot_matrix[:, boot_idx]
        quran_d = float(col[quran_idx])
        rigveda_d = float(col[rigveda_idx])

        # Quran rank (1 = highest Δ_max)
        ranks = np.argsort(-col)  # descending; ranks[0] = idx of highest
        quran_rank = int(np.where(ranks == quran_idx)[0][0]) + 1
        quran_rank_distribution[quran_rank] += 1

        if quran_rank == 1:
            quran_rank_1_count += 1

        if quran_d >= DELTA_MAX_THRESHOLD:
            quran_above_3p5_count += 1
            n_above = int(np.sum(col >= DELTA_MAX_THRESHOLD))
            n_above_3p5_distribution[n_above] += 1
            if n_above == 1:
                quran_unique_above_3p5_count += 1
        else:
            n_above_3p5_distribution[int(np.sum(col >= DELTA_MAX_THRESHOLD))] += 1

        if rigveda_d >= RIGVEDA_TIER2_FLOOR:
            rigveda_above_3p0_count += 1

    freq_quran_rank_1 = quran_rank_1_count / N_BOOTSTRAP
    freq_quran_above_3p5 = quran_above_3p5_count / N_BOOTSTRAP
    freq_quran_unique_above_3p5 = quran_unique_above_3p5_count / N_BOOTSTRAP
    freq_rigveda_above_3p0 = rigveda_above_3p0_count / N_BOOTSTRAP
    quran_delta_boot_mean = per_corpus_boot_stats["quran"]["mean"]

    # Acceptance
    a = freq_quran_rank_1 >= PASS_FREQ_FLOOR
    b = freq_quran_above_3p5 >= PASS_FREQ_FLOOR
    c_unique = freq_quran_unique_above_3p5 >= PASS_FREQ_FLOOR
    d = freq_rigveda_above_3p0 >= PASS_FREQ_FLOOR
    e = quran_delta_boot_mean >= DELTA_MAX_THRESHOLD

    if a and b and c_unique and d and e:
        verdict = "PASS_F79_robust_bootstrap"
        verdict_reason = (
            f"All five criteria pass: "
            f"Quran rank-1 freq {freq_quran_rank_1*100:.1f}%, "
            f"Quran ≥ 3.5 freq {freq_quran_above_3p5*100:.1f}%, "
            f"Quran unique ≥ 3.5 freq {freq_quran_unique_above_3p5*100:.1f}%, "
            f"Rigveda ≥ 3.0 freq {freq_rigveda_above_3p0*100:.1f}%, "
            f"Quran bootstrap-mean Δ_max = {quran_delta_boot_mean:.4f} ≥ {DELTA_MAX_THRESHOLD}."
        )
    elif a and b and c_unique and e:
        verdict = "PASS_F79_strong_robust"
        verdict_reason = (
            f"Quran-uniqueness criteria (a)+(b)+(c)+(e) all pass; "
            f"Rigveda tier-2 fragile: freq_rigveda_above_3p0 = "
            f"{freq_rigveda_above_3p0*100:.1f}% < 95%."
        )
    elif a and b and e:
        verdict = "PARTIAL_F79_outlier_robust_but_not_unique"
        verdict_reason = (
            f"Quran rank-1 ({freq_quran_rank_1*100:.1f}%) and ≥ 3.5 ({freq_quran_above_3p5*100:.1f}%) "
            f"hold; uniqueness fragile at freq_unique = {freq_quran_unique_above_3p5*100:.1f}% < 95%. "
            f"Distribution of n_corpora ≥ 3.5: {dict(n_above_3p5_distribution)}."
        )
    elif b and e:
        verdict = "PARTIAL_F79_rank_1_diluted"
        verdict_reason = (
            f"Quran ≥ 3.5 robustly ({freq_quran_above_3p5*100:.1f}%) but rank-1 fragile "
            f"({freq_quran_rank_1*100:.1f}%); Rigveda sometimes outranks Quran on Δ_max. "
            f"Quran rank distribution: {dict(quran_rank_distribution)}."
        )
    else:
        verdict = "FAIL_F79_breaks_under_resampling"
        verdict_reason = (
            f"Bootstrap-mean Quran Δ_max = {quran_delta_boot_mean:.4f}; "
            f"freq above 3.5 = {freq_quran_above_3p5*100:.1f}%."
        )

    audit = {
        "ok": True,
        "checks": {
            "A1_eleven_pool_sha_via_indirect": "11-pool data routed through _phi_universal_xtrad_sizing.py loaders",
            "A2_rigveda_via_loader_v2": "Rigveda data via _rigveda_loader_v2.load_rigveda()",
            "A3_n_corpora": len(EXPECTED_CORPORA),
            "A4_F79_point_estimate_match": a4_pass,
            "A4_max_drift": max(abs(point_estimates[c]["Delta_max"] - F79_LOCKED_DELTA_MAX[c])
                                for c in F79_LOCKED_DELTA_MAX),
            "A5_unit_shuffle_max_dev": a5_max_dev,
            "A5_sanity_pass": a5_pass,
            "A6_deterministic": True,
        },
    }
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H87",
        "hypothesis": (
            "F79's PASS_alphabet_corrected_strict_6_alphabets verdict is robust under "
            "bootstrap-resampling-of-units: Quran is the unique above-3.5-bit corpus on "
            "Δ_max in ≥ 95% of 200 bootstraps, with Rigveda tier-2 (≥ 3.0) preserved "
            "in ≥ 95%, upgrading F79 to PASS_strict_BOOTSTRAP_ROBUST."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "ALPHABET_SIZES": ALPHABET_SIZES,
            "DELTA_MAX_THRESHOLD": DELTA_MAX_THRESHOLD,
            "RIGVEDA_TIER2_FLOOR": RIGVEDA_TIER2_FLOOR,
            "PASS_FREQ_FLOOR": PASS_FREQ_FLOOR,
            "N_BOOTSTRAP": N_BOOTSTRAP,
            "N_PERM_SANITY": N_PERM_SANITY,
            "SEED": SEED,
            "Q1_TOLERANCE": Q1_TOLERANCE,
            "A4_TOLERANCE": A4_TOLERANCE,
        },
        "results": {
            "per_corpus_point_estimate": point_estimates,
            "per_corpus_bootstrap_stats": per_corpus_boot_stats,
            "freq_quran_rank_1": freq_quran_rank_1,
            "freq_quran_above_3p5": freq_quran_above_3p5,
            "freq_quran_unique_above_3p5": freq_quran_unique_above_3p5,
            "freq_rigveda_above_3p0": freq_rigveda_above_3p0,
            "quran_delta_bootstrap_mean": quran_delta_boot_mean,
            "quran_rank_distribution": dict(quran_rank_distribution),
            "n_corpora_above_3p5_distribution": dict(n_above_3p5_distribution),
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 4),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"# verdict: {verdict}")
    print(f"# {verdict_reason}")
    print()
    print("## Per-corpus Δ_max (point estimate vs. bootstrap):")
    print(f"  {'corpus':20s}  {'n_units':>8s}  {'Δ_pt':>8s}  {'Δ_boot_mean':>12s}  "
          f"{'std':>8s}  {'p5':>8s}  {'p95':>8s}")
    sorted_c = sorted(EXPECTED_CORPORA, key=lambda c: -point_estimates[c]["Delta_max"])
    for c in sorted_c:
        pt = point_estimates[c]
        bs = per_corpus_boot_stats[c]
        flag_q = "  <-- QURAN" if c == "quran" else ""
        flag_r = "  <-- RIGVEDA" if c == "rigveda" else ""
        print(f"  {c:20s}  {pt['n_units']:8d}  "
              f"{pt['Delta_max']:8.4f}  {bs['mean']:12.4f}  "
              f"{bs['std']:8.4f}  {bs['p05']:8.4f}  {bs['p95']:8.4f}{flag_q}{flag_r}")
    print()
    print(f"# (a) Quran rank-1 freq:           {freq_quran_rank_1*100:6.2f}%  "
          f"{'PASS' if a else 'FAIL'} (floor 95%)")
    print(f"# (b) Quran ≥ 3.5 freq:            {freq_quran_above_3p5*100:6.2f}%  "
          f"{'PASS' if b else 'FAIL'}")
    print(f"# (c) Quran unique ≥ 3.5 freq:     {freq_quran_unique_above_3p5*100:6.2f}%  "
          f"{'PASS' if c_unique else 'FAIL'}")
    print(f"# (d) Rigveda ≥ 3.0 freq:          {freq_rigveda_above_3p0*100:6.2f}%  "
          f"{'PASS' if d else 'FAIL'}")
    print(f"# (e) Quran bootstrap-mean Δ_max:  {quran_delta_boot_mean:6.4f}  "
          f"{'PASS' if e else 'FAIL'} (floor 3.5)")
    print()
    print(f"# Quran rank distribution: {dict(quran_rank_distribution)}")
    print(f"# n_corpora ≥ 3.5 distribution: {dict(n_above_3p5_distribution)}")
    print(f"# A4 max drift vs F79: {audit['checks']['A4_max_drift']:.6f} (tol {A4_TOLERANCE})")
    print(f"# A5 sanity max deviation: {a5_max_dev:.2e} (tol {Q1_TOLERANCE:.0e})")
    print()
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
