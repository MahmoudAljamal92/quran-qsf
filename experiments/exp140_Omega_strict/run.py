"""experiments/exp140_Omega_strict/run.py — Percentile-aggregation sweep on per-unit Ω.

Tests whether a stricter aggregation than the median widens the Quran-Rigveda
gap on Ω_unit beyond F79's 0.572 bits.

PREREG: experiments/exp140_Omega_strict/PREREG.md
Output: results/experiments/exp140_Omega_strict/exp140_Omega_strict.json
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

EXP_NAME = "exp140_Omega_strict"
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

# Aggregation labels and their numpy implementations
AGGREGATIONS = [
    ("min", lambda x: float(np.min(x))),
    ("p5", lambda x: float(np.percentile(x, 5))),
    ("p10", lambda x: float(np.percentile(x, 10))),
    ("p25", lambda x: float(np.percentile(x, 25))),
    ("p50_median", lambda x: float(np.percentile(x, 50))),
    ("p75", lambda x: float(np.percentile(x, 75))),
    ("mean", lambda x: float(np.mean(x))),
    ("max", lambda x: float(np.max(x))),
]
LOWER_HALF = {"min", "p5", "p10", "p25"}

N_BOOTSTRAP = 1000
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


def per_unit_omegas(unit_finals_list, A_T):
    """Return numpy array of per-unit Ω_u = log₂(A) − H_EL_u."""
    log_A = math.log2(A_T)
    omegas = []
    for finals in unit_finals_list:
        c = Counter(finals)
        total = sum(c.values())
        p = np.array([c[k] / total for k in sorted(c)], dtype=float)
        omegas.append(log_A - shannon_entropy(p))
    return np.array(omegas, dtype=float)


def load_per_unit_finals():
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
        out[c] = per_unit_finals(unit_list, norm_fn)
    return out


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)
    per_unit = load_per_unit_finals()

    # ---- Sub-task A: per-corpus per-unit Ω distribution
    print("# Sub-task A: per-unit Ω distribution per corpus...", flush=True)
    omegas_per_corpus = {}
    sub_A = {}
    for c in EXPECTED_CORPORA:
        A_T = ALPHABET_SIZES[c]
        omegas = per_unit_omegas(per_unit[c], A_T)
        omegas_per_corpus[c] = omegas
        sub_A[c] = {
            "n_units": int(len(omegas)),
            "alphabet_size": A_T,
            "min": float(omegas.min()),
            "p5": float(np.percentile(omegas, 5)),
            "p10": float(np.percentile(omegas, 10)),
            "p25": float(np.percentile(omegas, 25)),
            "p50_median": float(np.percentile(omegas, 50)),
            "p75": float(np.percentile(omegas, 75)),
            "mean": float(omegas.mean()),
            "max": float(omegas.max()),
            "std": float(omegas.std(ddof=1)),
            "cv": float(omegas.std(ddof=1) / max(omegas.mean(), 1e-9)),
        }
    for c in EXPECTED_CORPORA:
        s = sub_A[c]
        print(f"#   {c.ljust(18)} n={s['n_units']:5d} min={s['min']:6.3f} "
              f"p5={s['p5']:6.3f} p25={s['p25']:6.3f} p50={s['p50_median']:6.3f} "
              f"mean={s['mean']:6.3f} max={s['max']:6.3f} CV={s['cv']:.3f}", flush=True)

    # ---- Sub-task B: aggregation sweep
    print("# Sub-task B: aggregation sweep...", flush=True)
    sub_B = {}
    for ag_name, ag_fn in AGGREGATIONS:
        per_corpus = {c: ag_fn(omegas_per_corpus[c]) for c in EXPECTED_CORPORA}
        sorted_desc = sorted(per_corpus.items(), key=lambda kv: -kv[1])
        rank1, rank2 = sorted_desc[0], sorted_desc[1]
        gap = rank1[1] - rank2[1]
        quran_rank = [c for c, _ in sorted_desc].index("quran") + 1
        sub_B[ag_name] = {
            "per_corpus_sorted_desc":
                [{"corpus": c, "omega_a": float(v)} for c, v in sorted_desc],
            "rank_1_corpus": rank1[0],
            "rank_1_value": float(rank1[1]),
            "rank_2_corpus": rank2[0],
            "rank_2_value": float(rank2[1]),
            "gap_rank1_to_rank2": float(gap),
            "quran_rank_of_12": quran_rank,
            "quran_value": float(per_corpus["quran"]),
        }
        print(f"#   ag={ag_name.ljust(11)} rank1={rank1[0].ljust(10)} ({rank1[1]:.4f})  "
              f"rank2={rank2[0].ljust(10)} ({rank2[1]:.4f})  gap={gap:.4f}  "
              f"quran_rank={quran_rank}/12", flush=True)

    # ---- Sub-task C: Quran-vs-Rigveda contrast
    print("# Sub-task C: Quran-vs-Rigveda gap per aggregation...", flush=True)
    sub_C = {}
    best_gap = -1e9
    best_ag = None
    for ag_name, ag_fn in AGGREGATIONS:
        q = ag_fn(omegas_per_corpus["quran"])
        r = ag_fn(omegas_per_corpus["rigveda"])
        sub_C[ag_name] = {"quran_value": float(q), "rigveda_value": float(r),
                          "gap_q_minus_r": float(q - r)}
        if (q - r) > best_gap and sub_B[ag_name]["quran_rank_of_12"] == 1:
            best_gap = q - r
            best_ag = ag_name
    print(f"#   Best aggregation by Quran-vs-Rigveda gap (with Quran rank-1): "
          f"{best_ag} (gap = {best_gap:.4f} bits)", flush=True)

    # ---- Sub-task D: bootstrap stability of best_ag
    print(f"# Sub-task D: bootstrap stability of {best_ag} (N={N_BOOTSTRAP})...", flush=True)
    rng = np.random.default_rng(SEED)
    boot_quran_rank1 = 0
    boot_q_minus_r_gaps = np.zeros(N_BOOTSTRAP)
    if best_ag is None:
        best_ag = "p50_median"  # fallback
    best_ag_fn = dict(AGGREGATIONS)[best_ag]
    for b in range(N_BOOTSTRAP):
        per_corpus = {}
        for c in EXPECTED_CORPORA:
            arr = omegas_per_corpus[c]
            n = len(arr)
            idx = rng.integers(0, n, size=n)
            per_corpus[c] = best_ag_fn(arr[idx])
        sorted_desc = sorted(per_corpus.items(), key=lambda kv: -kv[1])
        if sorted_desc[0][0] == "quran":
            boot_quran_rank1 += 1
        boot_q_minus_r_gaps[b] = per_corpus["quran"] - per_corpus["rigveda"]
        if (b + 1) % 200 == 0:
            print(f"#     iter {b + 1:4,}/{N_BOOTSTRAP:,} ...", flush=True)
    boot_rank1_freq = boot_quran_rank1 / N_BOOTSTRAP
    sub_D = {
        "best_aggregation": best_ag,
        "boot_quran_rank1_freq": float(boot_rank1_freq),
        "boot_q_minus_r_mean": float(boot_q_minus_r_gaps.mean()),
        "boot_q_minus_r_p5": float(np.percentile(boot_q_minus_r_gaps, 5)),
        "boot_q_minus_r_p95": float(np.percentile(boot_q_minus_r_gaps, 95)),
        "n_bootstrap": N_BOOTSTRAP,
    }
    print(f"#   {best_ag} bootstrap rank-1 freq: {boot_rank1_freq:.4f}  "
          f"q-r gap: 95% CI [{sub_D['boot_q_minus_r_p5']:.4f}, "
          f"{sub_D['boot_q_minus_r_p95']:.4f}]", flush=True)

    # ---- Sub-task E: CV(Ω_u) test
    quran_cv = sub_A["quran"]["cv"]
    rigveda_cv = sub_A["rigveda"]["cv"]
    cv_ratio = quran_cv / rigveda_cv if rigveda_cv > 0 else float("inf")
    print(f"#   CV(Ω_u): Quran = {quran_cv:.4f}, Rigveda = {rigveda_cv:.4f}, "
          f"ratio = {cv_ratio:.4f}", flush=True)

    # ---- Acceptance criteria
    # A1: at least one ag yields Quran rank-1 with gap >= 1.0
    A1 = any(sub_B[ag]["quran_rank_of_12"] == 1
             and sub_B[ag]["gap_rank1_to_rank2"] >= 1.0
             for ag, _ in AGGREGATIONS)
    # A2: at best_ag, q-r gap >= 1.0
    A2 = best_ag is not None and best_gap >= 1.0
    # A3: best_ag in lower half {min, p5, p10, p25}
    A3 = best_ag in LOWER_HALF
    # A4: bootstrap rank-1 freq >= 0.95
    A4 = boot_rank1_freq >= 0.95
    # A5: Quran CV < 0.5 × Rigveda CV
    A5 = cv_ratio < 0.5
    n_pass = sum([A1, A2, A3, A4, A5])
    if n_pass == 5:
        verdict = "PASS_omega_strict_widens_gap"
        verdict_reason = (f"All 5 PASS: best_ag={best_ag}, gap={best_gap:.4f}, "
                          f"boot_freq={boot_rank1_freq:.4f}, cv_ratio={cv_ratio:.4f}")
    elif n_pass >= 3:
        verdict = "PARTIAL_omega_strict_directional"
        verdict_reason = f"{n_pass}/5 PASS"
    else:
        verdict = "FAIL_omega_strict_no_widening"
        verdict_reason = f"Only {n_pass}/5 PASS — Quran/Rigveda truly indistinguishable on per-unit Ω"

    # Audit
    prereg_text = PREREG.read_text(encoding="utf-8")
    prereg_hash = hashlib.sha256(prereg_text.encode("utf-8")).hexdigest()
    omegas_concat_bytes = b"".join(
        omegas_per_corpus[c].astype(np.float64).tobytes() for c in EXPECTED_CORPORA
    )
    omegas_hash = hashlib.sha256(omegas_concat_bytes).hexdigest()
    audit_report = {
        "per_unit_omegas_sha256": omegas_hash,
        "n_units_per_corpus": {c: int(len(omegas_per_corpus[c])) for c in EXPECTED_CORPORA},
        "F79_median_match": {
            "quran": sub_A["quran"]["p50_median"],
            "rigveda": sub_A["rigveda"]["p50_median"],
            "F79_locked_quran": 3.838834,
            "F79_locked_rigveda": 3.266805,
            "match_quran": abs(sub_A["quran"]["p50_median"] - 3.838834) < 0.001,
            "match_rigveda": abs(sub_A["rigveda"]["p50_median"] - 3.266805) < 0.001,
        },
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H92_Omega_strict",
        "hypothesis": ("There exists an aggregation a in {min,p5,p10,p25,p50,p75,mean,max} "
                       "of per-unit Ω such that Quran rank-1 with gap ≥ 1.0 bits, "
                       "and the optimal aggregation is in the lower half (p ≤ 25)."),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "AGGREGATIONS": [a for a, _ in AGGREGATIONS],
            "N_BOOTSTRAP": N_BOOTSTRAP, "SEED": SEED,
        },
        "results": {
            "sub_A_per_unit_distribution": sub_A,
            "sub_B_aggregation_sweep": sub_B,
            "sub_C_quran_vs_rigveda_gap": {
                "per_aggregation": sub_C,
                "best_aggregation": best_ag,
                "best_gap_quran_minus_rigveda": float(best_gap),
            },
            "sub_D_bootstrap": sub_D,
            "sub_E_cv_test": {
                "quran_cv": float(quran_cv),
                "rigveda_cv": float(rigveda_cv),
                "ratio_q_over_r": float(cv_ratio),
            },
            "criteria_pass": {
                "A1_some_ag_quran_rank1_gap_geq_1bit": A1,
                "A2_best_ag_gap_geq_1bit": A2,
                "A3_best_ag_in_lower_half": A3,
                "A4_bootstrap_rank1_geq_95pct": A4,
                "A5_quran_cv_lt_half_rigveda_cv": A5,
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


if __name__ == "__main__":
    main()
