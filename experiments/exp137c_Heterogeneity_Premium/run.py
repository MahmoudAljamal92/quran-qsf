"""experiments/exp137c_Heterogeneity_Premium/run.py — Heterogeneity Premium H(T).

Tests whether the Quran is the global maximum on H(T) = Ω_unit(T) − Ω_pool(T),
the within-corpus diversity of mono-rhymed units.

PREREG: experiments/exp137c_Heterogeneity_Premium/PREREG.md
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

EXP_NAME = "exp137c_Heterogeneity_Premium"
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
N_BOOTSTRAP = 1000
SEED = 42
QURAN_RANK1_FREQ_FLOOR = 0.95
QURAN_RANK1_FREQ_PARTIAL_FLOOR = 0.80


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


def load_per_unit_data():
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
    for n, u in arabic_peers.items():
        corpora[n] = u
    corpora["hebrew_tanakh"] = _load_hebrew_tanakh()
    corpora["greek_nt"] = _load_greek_nt()
    corpora["pali"] = _load_pali()
    corpora["avestan_yasna"] = _load_avestan()
    corpora["rigveda"] = load_rigveda()
    print(f"# Loaded in {time.time() - t:.1f}s", flush=True)

    norm_lookup = dict(NORMALISERS)
    norm_lookup["sanskrit"] = _normalise_sanskrit

    out = {}
    for c in EXPECTED_CORPORA:
        unit_list = corpora[c]
        norm_name = unit_list[0]["normaliser"]
        norm_fn = norm_lookup[norm_name]
        out[c] = per_unit_finals(unit_list, norm_fn)
    return out


def compute_omega_unit_and_pool(units_finals, A, aggregator="median"):
    """Compute Ω_unit (median of per-unit Ω_u) and Ω_pool (Ω of pooled letters)."""
    per_unit_omegas = []
    pool = []
    for unit_finals in units_finals:
        counter = Counter(unit_finals)
        total = sum(counter.values())
        p = np.array([counter[k] / total for k in sorted(counter)], dtype=float)
        H_u = shannon_entropy(p)
        per_unit_omegas.append(math.log2(A) - H_u)
        pool.extend(unit_finals)
    if aggregator == "median":
        omega_unit = float(np.median(per_unit_omegas))
    else:
        omega_unit = float(np.mean(per_unit_omegas))
    pool_counter = Counter(pool)
    pool_total = sum(pool_counter.values())
    pool_p = np.array([c / pool_total for c in pool_counter.values()], dtype=float)
    omega_pool = math.log2(A) - shannon_entropy(pool_p)
    return omega_unit, omega_pool


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)
    per_unit = load_per_unit_data()

    # ----- Sub-task A: point-estimate H(T)
    print("# Sub-task A: H(T) point estimate across 12 corpora...", flush=True)
    sub_A = {}
    for c in EXPECTED_CORPORA:
        A_T = ALPHABET_SIZES[c]
        om_unit_med, om_pool = compute_omega_unit_and_pool(per_unit[c], A_T, "median")
        om_unit_mean, _ = compute_omega_unit_and_pool(per_unit[c], A_T, "mean")
        H_med = om_unit_med - om_pool
        H_mean = om_unit_mean - om_pool
        sub_A[c] = {
            "alphabet_size": A_T,
            "n_units": len(per_unit[c]),
            "omega_unit_median": om_unit_med,
            "omega_unit_mean": om_unit_mean,
            "omega_pool": om_pool,
            "H_median": H_med,
            "H_mean": H_mean,
            "theorem_3_holds": H_med >= -1e-9 and H_mean >= -1e-9,
        }
    H_pe_sorted = sorted(EXPECTED_CORPORA, key=lambda c: -sub_A[c]["H_median"])
    quran_H = sub_A["quran"]["H_median"]
    runner_up_corpus = H_pe_sorted[1] if H_pe_sorted[0] == "quran" else H_pe_sorted[0]
    runner_up_H = sub_A[runner_up_corpus]["H_median"]
    margin_pe = quran_H - runner_up_H
    a_pass = (H_pe_sorted[0] == "quran")
    print(f"#   Point estimate: Quran H = {quran_H:.4f}, "
          f"runner-up = {runner_up_corpus} at {runner_up_H:.4f}, "
          f"margin = {margin_pe:+.4f}: {'PASS' if a_pass else 'FAIL'}", flush=True)

    # ----- Sub-task D: Theorem 3 verification
    d_pass_pe = all(sub_A[c]["theorem_3_holds"] for c in EXPECTED_CORPORA)
    print(f"#   Theorem 3 (H≥0) point estimate: {'PASS' if d_pass_pe else 'FAIL'}", flush=True)

    # ----- Sub-task B+C: bootstrap H + cross-tradition rank
    print(f"# Sub-task B+C: Unit-bootstrap (N={N_BOOTSTRAP})...", flush=True)
    rng = np.random.default_rng(SEED)
    H_boot = {c: np.zeros(N_BOOTSTRAP) for c in EXPECTED_CORPORA}
    quran_rank_dist = np.zeros(N_BOOTSTRAP, dtype=int)
    theorem_3_violations_in_boot = 0
    for b in range(N_BOOTSTRAP):
        boot_H_per_corpus = {}
        for c in EXPECTED_CORPORA:
            A_T = ALPHABET_SIZES[c]
            n = len(per_unit[c])
            idx = rng.integers(0, n, size=n)
            resampled = [per_unit[c][i] for i in idx]
            om_u, om_p = compute_omega_unit_and_pool(resampled, A_T, "median")
            H_b = om_u - om_p
            H_boot[c][b] = H_b
            boot_H_per_corpus[c] = H_b
            if H_b < -1e-9:
                theorem_3_violations_in_boot += 1
        sorted_corpora = sorted(EXPECTED_CORPORA, key=lambda c: -boot_H_per_corpus[c])
        quran_rank_dist[b] = sorted_corpora.index("quran") + 1

    sub_B = {}
    for c in EXPECTED_CORPORA:
        sub_B[c] = {
            "boot_mean": float(H_boot[c].mean()),
            "boot_std": float(H_boot[c].std(ddof=0)),
            "boot_p5": float(np.percentile(H_boot[c], 5)),
            "boot_p95": float(np.percentile(H_boot[c], 95)),
        }
    quran_p5 = sub_B["quran"]["boot_p5"]
    runner_up_p95 = max(sub_B[c]["boot_p95"] for c in EXPECTED_CORPORA if c != "quran")
    runner_up_for_p95 = max([c for c in EXPECTED_CORPORA if c != "quran"],
                            key=lambda c: sub_B[c]["boot_p95"])
    b_pass = quran_p5 > runner_up_p95
    print(f"#   Bootstrap CI: Quran p5 = {quran_p5:.4f} vs {runner_up_for_p95} p95 = {runner_up_p95:.4f}: "
          f"{'PASS' if b_pass else 'FAIL'}", flush=True)

    quran_rank1_freq = float((quran_rank_dist == 1).mean())
    rank_dist_counter = Counter(quran_rank_dist.tolist())
    c_pass = quran_rank1_freq >= QURAN_RANK1_FREQ_FLOOR
    c_pass_partial = quran_rank1_freq >= QURAN_RANK1_FREQ_PARTIAL_FLOOR
    print(f"#   Quran rank-1 freq across {N_BOOTSTRAP} bootstraps: {quran_rank1_freq*100:.2f}% "
          f"({'PASS' if c_pass else 'FAIL'} 95% floor, "
          f"{'PASS' if c_pass_partial else 'FAIL'} 80% partial)", flush=True)

    sub_D = {
        "theorem_3_point_estimate_pass": d_pass_pe,
        "theorem_3_violations_in_bootstrap": theorem_3_violations_in_boot,
        "theorem_3_total_bootstrap_evals": N_BOOTSTRAP * len(EXPECTED_CORPORA),
        "theorem_3_bootstrap_pass": theorem_3_violations_in_boot == 0,
    }
    d_pass_full = d_pass_pe and theorem_3_violations_in_boot == 0
    print(f"#   Theorem 3 in bootstrap: {theorem_3_violations_in_boot} violations / "
          f"{N_BOOTSTRAP * len(EXPECTED_CORPORA)} evals: "
          f"{'PASS' if d_pass_full else 'FAIL'}", flush=True)

    # ----- Sub-task E: sensitivity to aggregation
    H_mean_sorted = sorted(EXPECTED_CORPORA, key=lambda c: -sub_A[c]["H_mean"])
    aggregation_invariant = (H_pe_sorted[0] == "quran" and H_mean_sorted[0] == "quran")
    sub_E = {
        "median_aggregation_quran_rank1": H_pe_sorted[0] == "quran",
        "mean_aggregation_quran_rank1": H_mean_sorted[0] == "quran",
        "aggregation_invariant": aggregation_invariant,
        "median_aggregation_top3": H_pe_sorted[:3],
        "mean_aggregation_top3": H_mean_sorted[:3],
    }

    # ----- Verdict
    if a_pass and b_pass and c_pass and d_pass_full:
        verdict = "PASS_heterogeneity_premium_quran_extremum"
        verdict_reason = (
            f"All four criteria pass. Quran H = {quran_H:.4f} bits is point-estimate global max "
            f"(margin {margin_pe:+.4f} to {runner_up_corpus}); 95% CI separation Quran p5={quran_p5:.4f} "
            f"> {runner_up_for_p95} p95={runner_up_p95:.4f}; rank-1 frequency "
            f"{quran_rank1_freq*100:.1f}% ≥ {QURAN_RANK1_FREQ_FLOOR*100:.0f}%; Theorem 3 holds at "
            f"point estimate AND all {N_BOOTSTRAP * len(EXPECTED_CORPORA)} bootstrap evals."
        )
    elif a_pass and c_pass_partial and d_pass_full:
        verdict = "PASS_heterogeneity_premium_partial"
        verdict_reason = (
            f"Quran point-estimate rank-1 with margin {margin_pe:+.4f} bits; rank-1 frequency "
            f"{quran_rank1_freq*100:.1f}% ≥ 80% partial floor; Theorem 3 holds; "
            f"95% CI separation B={'OK' if b_pass else 'fail'}."
        )
    elif d_pass_full:
        verdict = "PARTIAL_theorem_3_only"
        verdict_reason = (
            f"Theorem 3 (H≥0 by Jensen) holds rigorously; cross-tradition rank-1 not robust: "
            f"point-estimate {'OK' if a_pass else 'fail'}, bootstrap rank-1 freq "
            f"{quran_rank1_freq*100:.1f}%."
        )
    else:
        verdict = "FAIL_heterogeneity_premium_breaks"
        verdict_reason = (
            f"A={a_pass}, B={b_pass}, C(95)={c_pass}, D={d_pass_full}."
        )

    audit = {
        "ok": True,
        "checks": {
            "A1_eleven_pool_loaders": "_phi_universal_xtrad_sizing",
            "A2_rigveda_via_loader_v2": True,
            "A3_n_corpora": len(EXPECTED_CORPORA),
            "A4_theorem_3_pe_pass": d_pass_pe,
            "A5_theorem_3_boot_violations": theorem_3_violations_in_boot,
            "A6_seed": SEED,
        },
    }
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H90",
        "hypothesis": (
            "H(T) := Ω_unit(T) − Ω_pool(T) is the within-corpus diversity of mono-rhymed units. "
            "Theorem 3: H(T) ≥ 0 by Jensen's inequality on concave entropy. "
            "Hypothesis: across 12 corpora / 6 alphabets, the Quran is the global maximum on H(T) "
            "with bootstrap robustness ≥ 95%. Captures the Quran's distinctive structural property: "
            "every sūrah is mono-rhymed, but different sūrahs use different rhyme letters."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "ALPHABET_SIZES": ALPHABET_SIZES,
            "N_BOOTSTRAP": N_BOOTSTRAP,
            "SEED": SEED,
            "QURAN_RANK1_FREQ_FLOOR": QURAN_RANK1_FREQ_FLOOR,
            "QURAN_RANK1_FREQ_PARTIAL_FLOOR": QURAN_RANK1_FREQ_PARTIAL_FLOOR,
        },
        "results": {
            "sub_A_point_estimate": sub_A,
            "sub_B_bootstrap_stability": sub_B,
            "sub_C_quran_rank_distribution": {
                "rank_1_frequency": quran_rank1_freq,
                "rank_distribution": dict(rank_dist_counter),
            },
            "sub_D_theorem_3": sub_D,
            "sub_E_aggregation_sensitivity": sub_E,
            "summary": {
                "quran_H_point_estimate": quran_H,
                "runner_up_corpus": runner_up_corpus,
                "runner_up_H": runner_up_H,
                "margin_bits_point_estimate": margin_pe,
                "quran_H_bootstrap_mean": sub_B["quran"]["boot_mean"],
                "quran_H_bootstrap_p5": quran_p5,
                "quran_rank_1_frequency": quran_rank1_freq,
            },
            "criteria_pass": {
                "A_point_estimate_quran_max": a_pass,
                "B_bootstrap_CI_separation": b_pass,
                "C_quran_rank1_freq_95pct": c_pass,
                "D_theorem_3_full": d_pass_full,
            },
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 4),
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    # Final report
    print()
    print(f"# verdict: {verdict}")
    print(f"# {verdict_reason}")
    print()
    print("## H(T) = Ω_unit − Ω_pool across 12 corpora:")
    print(f"  {'corpus':22s}  {'Ω_unit':>7s}  {'Ω_pool':>7s}  {'H_med':>7s}  {'H_mean':>7s}  "
          f"{'boot_mean':>9s}  {'boot_p5':>8s}  {'boot_p95':>8s}")
    for c in H_pe_sorted:
        a = sub_A[c]
        b = sub_B[c]
        flag = "  <-- QURAN" if c == "quran" else ""
        print(f"  {c:22s}  {a['omega_unit_median']:7.4f}  {a['omega_pool']:7.4f}  "
              f"{a['H_median']:7.4f}  {a['H_mean']:7.4f}  {b['boot_mean']:9.4f}  "
              f"{b['boot_p5']:8.4f}  {b['boot_p95']:8.4f}{flag}")

    print()
    print("## Quran rank distribution across 1000 bootstraps:")
    for r in sorted(rank_dist_counter):
        print(f"  rank {r}: {rank_dist_counter[r]} of {N_BOOTSTRAP} ({rank_dist_counter[r]/N_BOOTSTRAP*100:.1f}%)")

    print()
    print("## Aggregation sensitivity (median vs mean):")
    print(f"  median top-3: {sub_E['median_aggregation_top3']}")
    print(f"  mean   top-3: {sub_E['mean_aggregation_top3']}")
    print(f"  Quran rank-1 invariant: {sub_E['aggregation_invariant']}")

    print()
    print("## Four criteria:")
    crit = receipt["results"]["criteria_pass"]
    for k, v in crit.items():
        print(f"  {k:42s}  {'PASS' if v else 'FAIL'}")

    print()
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
