"""experiments/exp137b_The_Quran_Constant_per_unit/run.py — Per-unit Ω_unit theorem promotion of F79.

Tests whether F79's per-unit-median Ω formulation satisfies the same Theorem 1
(KL identity per unit) and Theorem 2 (channel capacity per unit) verified at the
pooled level by exp137. Promotes F79 → F80 if all six sub-tasks pass.

PREREG: experiments/exp137b_The_Quran_Constant_per_unit/PREREG.md
Output: results/experiments/exp137b_The_Quran_Constant_per_unit/exp137b_The_Quran_Constant_per_unit.json
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

EXP_NAME = "exp137b_The_Quran_Constant_per_unit"
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
N_MC = 50_000
NOISE_RATES = [0.001, 0.01, 0.05, 0.10]
N_REPRESENTATIVE_UNITS = 5
MARGIN_THRESHOLDS = [2.5, 3.0, 3.3, 3.5, 3.8, 4.0]
SEED = 42
THEOREM_1_TOL = 1e-12
MC_REL_TOL = 0.01

# F79 locked Δ_max values (per-unit-median, from exp124c receipt)
F79_LOCKED_DELTA_MAX = {
    "quran": 3.838834, "rigveda": 3.266805, "pali": 2.864257,
    "avestan_yasna": 2.582491, "greek_nt": 2.151256, "poetry_islami": 2.118585,
    "poetry_abbasi": 2.055656, "poetry_jahili": 2.027808, "ksucca": 1.899525,
    "arabic_bible": 1.889059, "hebrew_tanakh": 1.406299, "hindawi": 1.328527,
}
F79_MATCH_TOL = 0.01


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def kl_to_uniform(p, A):
    p = np.asarray(p, dtype=float)
    nz = p > 0
    return float(np.sum(p[nz] * np.log2(p[nz] * A)))


def a_ary_bsc_entropy(eps, A):
    if eps == 0 or A <= 1:
        return 0.0
    if eps == 1:
        return math.log2(max(A - 1, 1))
    e_term = -eps * math.log2(eps / (A - 1))
    n_term = -(1 - eps) * math.log2(1 - eps)
    return e_term + n_term


def bsc_output_distribution(p, eps, A):
    p = np.asarray(p, dtype=float)
    return (1 - eps) * p + eps * (1 - p) / max(A - 1, 1)


def per_unit_finals(unit_list, normaliser):
    """Return list of per-unit verse-final-letter lists."""
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

    out = {}
    for c in EXPECTED_CORPORA:
        unit_list = corpora[c]
        norm_name = unit_list[0]["normaliser"]
        norm_fn = norm_lookup[norm_name]
        units_finals = per_unit_finals(unit_list, norm_fn)
        out[c] = units_finals
    return out


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)
    per_unit = load_per_unit_data()

    # ----- Sub-task A: per-unit Theorem 1 identity
    print("# Sub-task A: per-unit Theorem 1 identity verification...", flush=True)
    sub_A = {}
    a_pass = True
    max_diff_overall = 0.0
    for c in EXPECTED_CORPORA:
        A_T = ALPHABET_SIZES[c]
        diffs = []
        omegas_per_unit = []
        for unit_finals in per_unit[c]:
            counter = Counter(unit_finals)
            total = sum(counter.values())
            p = np.array([counter[k] / total for k in sorted(counter)], dtype=float)
            H_u = shannon_entropy(p)
            om_def = math.log2(A_T) - H_u
            om_kl = kl_to_uniform(p, A_T)
            diffs.append(abs(om_def - om_kl))
            omegas_per_unit.append(om_def)
        max_diff = max(diffs)
        max_diff_overall = max(max_diff_overall, max_diff)
        omega_median = float(np.median(omegas_per_unit))
        omega_mean = float(np.mean(omegas_per_unit))
        sub_A[c] = {
            "n_units": len(per_unit[c]),
            "alphabet_size": A_T,
            "omega_unit_median": omega_median,
            "omega_unit_mean": omega_mean,
            "max_per_unit_identity_diff": max_diff,
            "identity_holds": max_diff < THEOREM_1_TOL,
            "F79_locked_value": F79_LOCKED_DELTA_MAX[c],
            "F79_match_diff": abs(omega_median - F79_LOCKED_DELTA_MAX[c]),
            "F79_match_within_tol": abs(omega_median - F79_LOCKED_DELTA_MAX[c]) < F79_MATCH_TOL,
        }
        if max_diff >= THEOREM_1_TOL:
            a_pass = False
    f79_match = all(sub_A[c]["F79_match_within_tol"] for c in EXPECTED_CORPORA)
    print(f"#   Theorem 1' identity: {'PASS' if a_pass else 'FAIL'} "
          f"(max overall diff = {max_diff_overall:.2e})", flush=True)
    print(f"#   F79 receipt match: {'PASS' if f79_match else 'FAIL'} "
          f"(max diff = {max(sub_A[c]['F79_match_diff'] for c in EXPECTED_CORPORA):.4f})", flush=True)

    # ----- Sub-task B: unit bootstrap (resample units)
    print(f"# Sub-task B: Unit-bootstrap stability (N={N_BOOTSTRAP})...", flush=True)
    rng_b = np.random.default_rng(SEED)
    sub_B = {}
    for c in EXPECTED_CORPORA:
        A_T = ALPHABET_SIZES[c]
        per_unit_omegas = []
        for unit_finals in per_unit[c]:
            counter = Counter(unit_finals)
            total = sum(counter.values())
            p = np.array([counter[k] / total for k in sorted(counter)], dtype=float)
            per_unit_omegas.append(math.log2(A_T) - shannon_entropy(p))
        per_unit_omegas = np.array(per_unit_omegas)
        n = len(per_unit_omegas)
        boot_medians = np.zeros(N_BOOTSTRAP)
        for b in range(N_BOOTSTRAP):
            idx = rng_b.integers(0, n, size=n)
            boot_medians[b] = np.median(per_unit_omegas[idx])
        sub_B[c] = {
            "median_estimator_mean": float(boot_medians.mean()),
            "median_estimator_std": float(boot_medians.std(ddof=0)),
            "median_estimator_p5": float(np.percentile(boot_medians, 5)),
            "median_estimator_p95": float(np.percentile(boot_medians, 95)),
        }

    quran_p5 = sub_B["quran"]["median_estimator_p5"]
    runner_up = max([c for c in EXPECTED_CORPORA if c != "quran"],
                    key=lambda c: sub_B[c]["median_estimator_mean"])
    runner_up_p95 = sub_B[runner_up]["median_estimator_p95"]
    b_pass = quran_p5 > runner_up_p95
    print(f"#   Unit-bootstrap: Quran p5 = {quran_p5:.4f} vs {runner_up} p95 = {runner_up_p95:.4f}: "
          f"{'PASS' if b_pass else 'FAIL'}", flush=True)

    # ----- Sub-task C: per-unit dominant letter heterogeneity
    print("# Sub-task C: Per-unit dominant-letter heterogeneity...", flush=True)
    sub_C = {}
    for c in EXPECTED_CORPORA:
        dominant_letters = []
        for unit_finals in per_unit[c]:
            counter = Counter(unit_finals)
            dominant_letters.append(counter.most_common(1)[0][0])
        d_counter = Counter(dominant_letters)
        D = len(d_counter)
        total = sum(d_counter.values())
        H_dom = -sum((c2 / total) * math.log2(c2 / total) for c2 in d_counter.values())
        top1_dom_pct = d_counter.most_common(1)[0][1] / total * 100
        sub_C[c] = {
            "n_distinct_dominant_letters": D,
            "H_dominant_letter_distribution": H_dom,
            "top_1_dominant_letter": d_counter.most_common(1)[0][0],
            "top_1_dominant_letter_pct_of_units": top1_dom_pct,
            "n_units": len(dominant_letters),
        }
    quran_D = sub_C["quran"]["n_distinct_dominant_letters"]
    pali_D = sub_C["pali"]["n_distinct_dominant_letters"]
    c_pass = quran_D >= 5 and pali_D <= 3
    print(f"#   Quran D = {quran_D} (floor 5), Pali D = {pali_D} (ceil 3): "
          f"{'PASS' if c_pass else 'FAIL'}", flush=True)

    # ----- Sub-task D: per-unit channel-capacity MC (5 representative units per corpus)
    print(f"# Sub-task D: Per-unit channel-capacity MC ({N_REPRESENTATIVE_UNITS} units × 12 × 4)...",
          flush=True)
    rng_mc = np.random.default_rng(SEED + 1)
    sub_D = {}
    d_failures = []
    d_total_combos = 0
    for c in EXPECTED_CORPORA:
        A_T = ALPHABET_SIZES[c]
        n_units = len(per_unit[c])
        # Pick units with sufficient sample size for MC validity (≥30 verse-finals)
        candidates = [i for i, uf in enumerate(per_unit[c]) if len(uf) >= 30]
        if len(candidates) < N_REPRESENTATIVE_UNITS:
            sample_idx = candidates
        else:
            sample_idx = list(rng_mc.choice(candidates, size=N_REPRESENTATIVE_UNITS, replace=False))
        unit_results = []
        for u_idx in sample_idx:
            unit_finals = per_unit[c][u_idx]
            counter = Counter(unit_finals)
            total = sum(counter.values())
            letters_sorted = sorted(counter.keys())
            p_emp = np.array([counter[l] / total for l in letters_sorted], dtype=float)
            n_letters = len(letters_sorted)
            x_indices = rng_mc.choice(n_letters, size=N_MC, p=p_emp)
            per_eps = {}
            for eps in NOISE_RATES:
                d_total_combos += 1
                keep_mask = rng_mc.random(N_MC) >= eps
                y_indices = x_indices.copy()
                flip_pos = np.where(~keep_mask)[0]
                if len(flip_pos) > 0 and n_letters > 1:
                    repl = rng_mc.integers(0, n_letters, size=len(flip_pos))
                    coll = repl == x_indices[flip_pos]
                    while coll.any():
                        repl[coll] = rng_mc.integers(0, n_letters, size=int(coll.sum()))
                        coll = repl == x_indices[flip_pos]
                    y_indices[flip_pos] = repl
                joint = np.zeros((n_letters, n_letters), dtype=np.int64)
                for xi, yi in zip(x_indices, y_indices):
                    joint[xi, yi] += 1
                joint_p = joint / N_MC
                px = joint_p.sum(axis=1)
                py = joint_p.sum(axis=0)
                I_emp = shannon_entropy(px) + shannon_entropy(py) - shannon_entropy(joint_p.flatten())
                p_y_th = bsc_output_distribution(p_emp, eps, n_letters)
                I_th = shannon_entropy(p_y_th) - a_ary_bsc_entropy(eps, n_letters)
                rel_err = abs(I_emp - I_th) / max(I_th, 1e-9)
                per_eps[f"eps={eps}"] = {
                    "I_empirical": I_emp,
                    "I_theoretical": I_th,
                    "rel_error": rel_err,
                    "match_within_1pct": rel_err < MC_REL_TOL,
                }
                if rel_err >= MC_REL_TOL:
                    d_failures.append({"corpus": c, "unit_idx": int(u_idx), "eps": eps,
                                      "rel_err": rel_err})
            unit_results.append({
                "unit_index": int(u_idx),
                "n_verse_finals": total,
                "n_letters_support": n_letters,
                "omega_unit": math.log2(A_T) - shannon_entropy(p_emp),
                "per_noise_rate": per_eps,
            })
        sub_D[c] = unit_results
    d_pass = len(d_failures) == 0
    print(f"#   Per-unit MC: {len(d_failures)} of {d_total_combos} (unit, eps) combos failed: "
          f"{'PASS' if d_pass else 'FAIL'}", flush=True)

    # ----- Sub-task E: margin-tightness on Ω_unit
    print("# Sub-task E: Margin-tightness threshold sweep on Ω_unit...", flush=True)
    sub_E = {}
    for tau in MARGIN_THRESHOLDS:
        above = [c for c in EXPECTED_CORPORA if sub_A[c]["omega_unit_median"] >= tau]
        sub_E[f"tau={tau}"] = {
            "n_corpora_above": len(above),
            "corpora_above": above,
            "quran_unique": above == ["quran"],
        }
    unique_taus = [t for t in MARGIN_THRESHOLDS if sub_E[f"tau={t}"]["quran_unique"]]
    largest_unique = max(unique_taus) if unique_taus else None
    e_pass = largest_unique is not None and largest_unique >= 3.3
    print(f"#   Largest threshold Quran-unique: {largest_unique} bits "
          f"({'PASS' if e_pass else 'FAIL'} floor 3.3)", flush=True)

    # ----- Sub-task F: cross-tradition global max + margin
    quran_om = sub_A["quran"]["omega_unit_median"]
    others_sorted = sorted(
        [(c, sub_A[c]["omega_unit_median"]) for c in EXPECTED_CORPORA if c != "quran"],
        key=lambda kv: -kv[1],
    )
    runner_up_corpus, runner_up_om = others_sorted[0]
    margin = quran_om - runner_up_om
    is_global_max = quran_om > runner_up_om
    f_pass = is_global_max and margin >= 0.5
    print(f"#   Quran Ω_unit = {quran_om:.4f}; runner-up = {runner_up_corpus} at {runner_up_om:.4f}; "
          f"margin = {margin:.4f}: {'PASS' if f_pass else 'FAIL'}", flush=True)

    # ----- Verdict
    if a_pass and b_pass and c_pass and d_pass and e_pass and f_pass:
        verdict = "PASS_quran_constant_theorem"
        verdict_reason = (
            f"All six criteria pass. Per-unit Theorem 1 identity within {THEOREM_1_TOL:.0e}; "
            f"unit-bootstrap CI separation Quran p5 {quran_p5:.4f} > {runner_up} p95 {runner_up_p95:.4f}; "
            f"Quran D = {quran_D} distinct dominant letters across {sub_C['quran']['n_units']} sūrahs vs "
            f"Pali D = {pali_D} (Pali dominated by '{sub_C['pali']['top_1_dominant_letter']}' "
            f"in {sub_C['pali']['top_1_dominant_letter_pct_of_units']:.1f}% of suttas); "
            f"per-unit channel-capacity MC matches theory within 1%; "
            f"Quran uniquely above {largest_unique} bits with margin {margin:.4f} bits to {runner_up_corpus}."
        )
    elif a_pass and d_pass and f_pass:
        verdict = "PASS_quran_constant_theorem_partial"
        verdict_reason = (
            f"Theorems hold and Quran-rank-1 with margin {margin:.4f} bits; "
            f"B={'OK' if b_pass else 'fail'}, C={'OK' if c_pass else 'fail'}, "
            f"E={'OK' if e_pass else 'fail'}."
        )
    else:
        verdict = "FAIL_quran_constant_theorem"
        verdict_reason = (
            f"A={a_pass}, B={b_pass}, C={c_pass}, D={d_pass}, E={e_pass}, F={f_pass}."
        )

    audit = {
        "ok": True,
        "checks": {
            "A1_eleven_pool_loaders": "_phi_universal_xtrad_sizing",
            "A2_rigveda_via_loader_v2": True,
            "A3_n_corpora": len(EXPECTED_CORPORA),
            "A4_F79_match": f79_match,
            "A5_seed": SEED,
            "A6_per_unit_max_diff": max_diff_overall,
        },
    }
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H89",
        "hypothesis": (
            "Ω_unit(T) = log₂(A_T) − median_u(H_EL_u) is the project's information-theoretically "
            "rigorous Quran-distinctiveness constant: each per-unit Ω_u is a KL divergence "
            "(Theorem 1'); per-unit channel capacity gap → Ω_u at zero noise (Theorem 2'); "
            "median aggregation makes Quran the global maximum across 12 corpora at 3.84 bits "
            "with 0.57-bit margin (matching F79). Promotes F79 → F80 with theorem backing."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "ALPHABET_SIZES": ALPHABET_SIZES,
            "N_BOOTSTRAP": N_BOOTSTRAP,
            "N_MC": N_MC,
            "NOISE_RATES": NOISE_RATES,
            "N_REPRESENTATIVE_UNITS": N_REPRESENTATIVE_UNITS,
            "MARGIN_THRESHOLDS": MARGIN_THRESHOLDS,
            "SEED": SEED,
            "THEOREM_1_TOL": THEOREM_1_TOL,
            "MC_REL_TOL": MC_REL_TOL,
            "F79_MATCH_TOL": F79_MATCH_TOL,
        },
        "results": {
            "sub_A_per_unit_theorem_1": sub_A,
            "sub_B_unit_bootstrap": sub_B,
            "sub_C_dominant_letter_heterogeneity": sub_C,
            "sub_D_per_unit_channel_capacity_MC": sub_D,
            "sub_E_margin_tightness": sub_E,
            "sub_F_global_max": {
                "quran_omega_unit": quran_om,
                "runner_up_corpus": runner_up_corpus,
                "runner_up_omega_unit": runner_up_om,
                "margin_bits": margin,
                "is_global_max": is_global_max,
            },
            "criteria_pass": {
                "A_per_unit_theorem_1": a_pass,
                "B_unit_bootstrap_CI_separation": b_pass,
                "C_heterogeneity_contrast": c_pass,
                "D_per_unit_channel_capacity_MC": d_pass,
                "E_uniquely_above_3p3_bits": e_pass,
                "F_global_max_margin_0p5_bits": f_pass,
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
    print("## The Quran Constant (per-unit form Ω_unit) across 12 corpora:")
    print(f"  {'corpus':22s}  {'A':>3s}  {'n_units':>7s}  {'Ω_unit':>7s}  {'F79_locked':>10s}  "
          f"{'D':>3s}  {'top-1 dom %':>11s}")
    sorted_c = sorted(EXPECTED_CORPORA, key=lambda c: -sub_A[c]["omega_unit_median"])
    for c in sorted_c:
        a = sub_A[c]
        cc = sub_C[c]
        flag = "  <-- QURAN" if c == "quran" else ""
        print(f"  {c:22s}  {a['alphabet_size']:3d}  {a['n_units']:7d}  "
              f"{a['omega_unit_median']:7.4f}  {a['F79_locked_value']:10.4f}  "
              f"{cc['n_distinct_dominant_letters']:3d}  "
              f"{cc['top_1_dominant_letter_pct_of_units']:10.1f}%{flag}")

    print()
    print("## Six criteria:")
    crit = receipt["results"]["criteria_pass"]
    for k, v in crit.items():
        print(f"  {k:42s}  {'PASS' if v else 'FAIL'}")

    print()
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
