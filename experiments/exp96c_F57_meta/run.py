"""
exp96c_F57_meta — Self-reference meta-finding for the Quran.

Purpose
-------
Measure the *self-describing accuracy* of the Quran: of the six
specific structural claims the Quran makes about itself (54:17,
2:23, 15:9, 11:1, 39:23, 41:42), how many are independently
confirmed under the project's pre-registered op-tests?

Compute the naive Binomial(6, 1/7) null tail for the observed pass
count, and stamp the verdict.

Inputs (chain-of-custody verified)
----------------------------------
- expE16_lc2_signature/expE16_report.json   (C1)
- exp95j_bigram_shift_universal.json        (C2)
- expP15_riwayat_invariance.json            (C3)
- exp97_multifractal_spectrum.json          (C5, PENDING)
- exp98_per_verse_mdl.json                  (C4, PENDING)
- exp99_adversarial_complexity.json         (C6, PENDING)

Output
------
- results/experiments/exp96c_F57_meta/exp96c_F57_meta.json

PREREG: experiments/exp96c_F57_meta/PREREG.md
PREREG hash: ba2b5af4a10f07b66446da29898224deb8b97ec0ce3ff42bfc169e8d0bd063a4
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RESULTS = ROOT / "results"
EXP_OUT = RESULTS / "experiments" / "exp96c_F57_meta"
EXP_OUT.mkdir(parents=True, exist_ok=True)

EXP = "exp96c_F57_meta"
PREREG_HASH_EXPECTED = "ba2b5af4a10f07b66446da29898224deb8b97ec0ce3ff42bfc169e8d0bd063a4"

# ---------------------------------------------------------------------------
# Frozen constants (must match PREREG.md §4)
# ---------------------------------------------------------------------------
N_CLAIMS         = 6
PASS_PROB_NULL   = 1.0 / 7.0
H51_PASS_FLOOR   = 4
H51_STRICT_FLOOR = 5
H51_EXTREMUM     = 6

EXP95J_HASH_EXPECTED = "a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd"
EXPP15_HASH_EXPECTED = "16f4f0ff0d9a3e6137628ab3801855a172eda02bac9cf351219d2dc03186da87"

# Pending exp IDs
EXP97_ID = "exp97_multifractal_spectrum"
EXP98_ID = "exp98_per_verse_mdl"
EXP99_ID = "exp99_adversarial_complexity"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def binom_tail_ge(n: int, p: float, s: int) -> float:
    """P(X >= s) for X ~ Binomial(n, p)."""
    if s <= 0:
        return 1.0
    if s > n:
        return 0.0
    total = 0.0
    for k in range(s, n + 1):
        total += math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))
    return total


# ---------------------------------------------------------------------------
# Per-claim verdict logic (strictly per-PREREG §2)
# ---------------------------------------------------------------------------
def evaluate_C1(rec: dict | None) -> dict:
    """C1: LC2 path-minimality. Pass = verdict in {WEAK_LC2, LC2_SIGNATURE}."""
    if rec is None:
        return {"claim": "C1_memory_optimised_54_17", "pass": None,
                "status": "PENDING", "reason": "expE16 receipt missing"}
    verdict = rec.get("verdict")
    passed = verdict in ("WEAK_LC2", "LC2_SIGNATURE")
    return {"claim": "C1_memory_optimised_54_17",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "verdict_observed": verdict,
            "n_lambda_at_5pct": rec.get("n_lambda_at_5pct"),
            "n_lambda_at_10pct": rec.get("n_lambda_at_10pct")}


def evaluate_C2(rec: dict | None) -> dict:
    """C2: Tahaddi via F55 universal symbolic detector. Pass = recall = 1.000
    AND FPR = 0.000."""
    if rec is None:
        return {"claim": "C2_tahaddi_2_23", "pass": None,
                "status": "PENDING", "reason": "exp95j receipt missing"}
    h_actual = rec.get("prereg_hash_actual")
    hash_match = (h_actual == EXP95J_HASH_EXPECTED)
    agg = rec.get("aggregate", {})
    recall = agg.get("recall")
    fpr    = agg.get("fpr")
    passed = (hash_match and recall == 1.0 and fpr == 0.0)
    return {"claim": "C2_tahaddi_2_23",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "recall": recall, "fpr": fpr,
            "n_pair_total": rec.get("n_pair_total"),
            "hash_match": hash_match}


def evaluate_C3(rec: dict | None) -> dict:
    """C3: 5-riwayat invariance. Pass = min AUC across riwayat >= 0.95."""
    if rec is None:
        return {"claim": "C3_preservation_15_9", "pass": None,
                "status": "PENDING", "reason": "expP15 receipt missing"}
    h_actual = rec.get("prereg_sha256")
    hash_match = (h_actual == EXPP15_HASH_EXPECTED)
    rows = rec.get("rows", {})
    aucs = {r: row.get("auc_el") for r, row in rows.items()
            if isinstance(row, dict)}
    auc_vals = [a for a in aucs.values() if isinstance(a, (int, float))]
    if not auc_vals:
        return {"claim": "C3_preservation_15_9", "pass": False,
                "status": "FAIL", "reason": "no AUC found",
                "hash_match": hash_match}
    auc_min = min(auc_vals)
    passed = (hash_match and auc_min >= 0.95)
    return {"claim": "C3_preservation_15_9",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "auc_min": auc_min,
            "auc_by_riwaya": aucs,
            "hash_match": hash_match}


def evaluate_C4(rec: dict | None) -> dict:
    """C4: Per-verse MDL. Pass = Quran rank 1 in median MDL/length."""
    if rec is None:
        return {"claim": "C4_precision_11_1", "pass": None,
                "status": "PENDING", "reason": f"{EXP98_ID} not yet run"}
    quran_rank = rec.get("quran_mdl_rank")
    n_corpora = rec.get("n_corpora", 7)
    passed = (quran_rank == 1)
    return {"claim": "C4_precision_11_1",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "quran_rank": quran_rank,
            "n_corpora": n_corpora}


def evaluate_C5(rec: dict | None) -> dict:
    """C5: Multifractal singularity spectrum width. Pass = Quran has
    rank 1 (smallest Δα = most monofractal)."""
    if rec is None:
        return {"claim": "C5_self_similar_39_23", "pass": None,
                "status": "PENDING", "reason": f"{EXP97_ID} not yet run"}
    quran_rank = rec.get("quran_delta_alpha_rank")
    n_corpora = rec.get("n_corpora", 7)
    passed = (quran_rank == 1)
    return {"claim": "C5_self_similar_39_23",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "quran_rank": quran_rank,
            "n_corpora": n_corpora}


def evaluate_C6(rec: dict | None) -> dict:
    """C6: Joint adversarial robustness. Pass = 0 of 10^6 forgeries pass
    Gate 1 ∧ F55 ∧ F56 simultaneously."""
    if rec is None:
        return {"claim": "C6_falsehood_41_42", "pass": None,
                "status": "PENDING", "reason": f"{EXP99_ID} not yet run"}
    n_forgeries = rec.get("n_forgeries")
    n_pass_joint = rec.get("n_joint_pass")
    passed = (n_pass_joint == 0)
    return {"claim": "C6_falsehood_41_42",
            "pass": bool(passed),
            "status": "CONFIRMED" if passed else "FAIL",
            "n_forgeries": n_forgeries,
            "n_pass_joint": n_pass_joint}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    t0 = time.time()
    prereg_hash_actual = sha256_of(HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash_actual}")

    audit_failures = []
    if prereg_hash_actual != PREREG_HASH_EXPECTED:
        audit_failures.append(
            f"PREREG drift: actual={prereg_hash_actual} expected={PREREG_HASH_EXPECTED}"
        )

    # Load all 6 receipts (None for pending)
    rec_e16 = load_json(RESULTS / "experiments" / "expE16_lc2_signature" / "expE16_report.json")
    rec_95j = load_json(RESULTS / "experiments" / "exp95j_bigram_shift_universal"
                                 / "exp95j_bigram_shift_universal.json")
    rec_p15 = load_json(RESULTS / "experiments" / "expP15_riwayat_invariance"
                                 / "expP15_riwayat_invariance.json")
    rec_98  = load_json(RESULTS / "experiments" / EXP98_ID / f"{EXP98_ID}.json")
    rec_97  = load_json(RESULTS / "experiments" / EXP97_ID / f"{EXP97_ID}.json")
    rec_99  = load_json(RESULTS / "experiments" / EXP99_ID / f"{EXP99_ID}.json")

    # Audit A1: 3 completed receipts present
    if rec_e16 is None: audit_failures.append("A1: expE16 missing")
    if rec_95j is None: audit_failures.append("A1: exp95j missing")
    if rec_p15 is None: audit_failures.append("A1: expP15 missing")

    # Per-claim evaluation
    c1 = evaluate_C1(rec_e16)
    c2 = evaluate_C2(rec_95j)
    c3 = evaluate_C3(rec_p15)
    c4 = evaluate_C4(rec_98)
    c5 = evaluate_C5(rec_97)
    c6 = evaluate_C6(rec_99)
    claims = [c1, c2, c3, c4, c5, c6]

    # Audit A2-A4: completed-claim sanity
    if rec_e16 is not None and not c1["pass"]:
        audit_failures.append(f"A2_C1: expE16 verdict {c1.get('verdict_observed')!r} not in WEAK/LC2_SIGNATURE")
    if rec_95j is not None and not c2["pass"]:
        audit_failures.append(f"A3_C2: exp95j recall/fpr/hash check failed: {c2}")
    if rec_p15 is not None and not c3["pass"]:
        audit_failures.append(f"A4_C3: expP15 min-AUC={c3.get('auc_min')} or hash failed")

    # Aggregate
    confirmed = [c for c in claims if c["pass"] is True]
    failed    = [c for c in claims if c["pass"] is False]
    pending   = [c for c in claims if c["pass"] is None]
    S_obs = len(confirmed)
    n_pending = len(pending)

    # Null-Binomial tail
    p_null_tail = binom_tail_ge(N_CLAIMS, PASS_PROB_NULL, S_obs)
    p_null_ge_4 = binom_tail_ge(N_CLAIMS, PASS_PROB_NULL, H51_PASS_FLOOR)
    p_null_ge_5 = binom_tail_ge(N_CLAIMS, PASS_PROB_NULL, H51_STRICT_FLOOR)
    p_null_eq_6 = binom_tail_ge(N_CLAIMS, PASS_PROB_NULL, H51_EXTREMUM)

    # Verdict ladder (PREREG §6)
    n_failed = len(failed)
    if audit_failures:
        verdict = "FAIL_audit_" + audit_failures[0].split(":", 1)[0].strip()
    elif n_pending > 0 and n_failed > 0:
        verdict = f"PARTIAL_pending_{n_pending}_with_{n_failed}_fail"
    elif n_pending > 0:
        verdict = f"PARTIAL_pending_{n_pending}"
    elif S_obs < H51_PASS_FLOOR:
        verdict = "FAIL_S_obs_below_floor"
    elif S_obs == H51_EXTREMUM:
        verdict = "PASS_F57_extremum"
    elif S_obs >= H51_STRICT_FLOOR:
        verdict = "PASS_F57_strict"
    else:
        verdict = "PASS_F57_meta_finding"

    # Console summary
    print()
    print(f"  per-claim status:")
    for c in claims:
        flag = "✓" if c["pass"] is True else ("✗" if c["pass"] is False else "·")
        print(f"    {flag}  {c['claim']:30s}  {c['status']}")
    print()
    print(f"  S_obs (confirmed)        = {S_obs} of {N_CLAIMS}")
    print(f"  pending (Phase 2)        = {n_pending}")
    print(f"  P_null(>= S_obs|Bin(6,1/7)) = {p_null_tail:.6f}")
    print(f"  P_null(>= 4)             = {p_null_ge_4:.6f}")
    print(f"  P_null(>= 5)             = {p_null_ge_5:.6f}")
    print(f"  P_null(= 6)              = {p_null_eq_6:.6f}")
    print(f"  verdict = {verdict}")

    receipt = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H51",
        "verdict": verdict,
        "prereg_hash_expected": PREREG_HASH_EXPECTED,
        "prereg_hash_actual": prereg_hash_actual,
        "frozen_constants": {
            "N_CLAIMS": N_CLAIMS,
            "PASS_PROB_NULL": PASS_PROB_NULL,
            "H51_PASS_FLOOR": H51_PASS_FLOOR,
            "H51_STRICT_FLOOR": H51_STRICT_FLOOR,
            "H51_EXTREMUM": H51_EXTREMUM,
        },
        "claims": claims,
        "S_obs": S_obs,
        "n_pending": n_pending,
        "n_confirmed": S_obs,
        "n_failed": len(failed),
        "P_null_ge_S_obs": p_null_tail,
        "P_null_ge_4": p_null_ge_4,
        "P_null_ge_5": p_null_ge_5,
        "P_null_eq_6": p_null_eq_6,
        "audit_failures": audit_failures,
        "wall_time_s": time.time() - t0,
    }
    out_path = EXP_OUT / f"{EXP}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    print(f"  receipt: {out_path}")

    return 0 if verdict.startswith("PASS_") else (1 if audit_failures else 2)


if __name__ == "__main__":
    sys.exit(main())
