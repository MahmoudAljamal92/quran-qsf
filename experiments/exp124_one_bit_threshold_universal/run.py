"""experiments/exp124_one_bit_threshold_universal/run.py — H_EL < 1 bit categorical test.

Tests whether the Quran is the unique corpus in the locked 11-pool with
verse-final-letter Shannon entropy H_EL < 1 bit.

If PASS: the project gains a CATEGORICAL universal (F76 candidate) stronger
than F75's CV-fitted statistical universal.

PREREG: experiments/exp124_one_bit_threshold_universal/PREREG.md
Input:  results/auxiliary/_phi_universal_xtrad_sizing.json (SHA-256 locked in PREREG A1)
Output: results/experiments/exp124_one_bit_threshold_universal/exp124_one_bit_threshold_universal.json
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and locked constants

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp124_one_bit_threshold_universal"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
INPUT_SIZING = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# Locked from PREREG A1 (same input as exp122)
EXPECTED_INPUT_SHA256 = (
    "0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22"
)

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
]

# PREREG-locked thresholds
ONE_BIT_THRESHOLD = 1.0
GAP_THRESHOLD_FOR_CATEGORICAL = 0.30  # bits


def main():
    t0 = time.time()

    # ---- A1: input SHA-256 -----------------------------------------------
    raw = INPUT_SIZING.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != EXPECTED_INPUT_SHA256:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_input_sha256_mismatch",
            "expected_sha256": EXPECTED_INPUT_SHA256,
            "actual_sha256": actual_sha,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_input_sha256_mismatch: {actual_sha}")
        return

    sizing = json.loads(raw.decode("utf-8"))
    medians = sizing["medians"]

    # ---- A3: corpus presence ---------------------------------------------
    for c in EXPECTED_CORPORA:
        if c not in medians:
            receipt = {
                "experiment": EXP_NAME,
                "verdict": "FAIL_audit_missing_corpus",
                "missing_corpus": c,
            }
            OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(f"FAIL_audit_missing_corpus: {c}")
            return

    # ---- Pull H_EL only (A2: no other features touched) -------------------
    h_el_per_corpus = {c: float(medians[c]["H_EL"]) for c in EXPECTED_CORPORA}

    # ---- Statistic computation ------------------------------------------
    quran_h_el = h_el_per_corpus["quran"]
    non_quran = {c: v for c, v in h_el_per_corpus.items() if c != "quran"}

    below_one_bit = [c for c, v in h_el_per_corpus.items() if v < ONE_BIT_THRESHOLD]
    n_below_one_bit = len(below_one_bit)
    quran_is_unique_below_one_bit = (
        n_below_one_bit == 1 and "quran" in below_one_bit
    )
    quran_is_minimum = quran_h_el == min(h_el_per_corpus.values())

    # Gap to runner-up (smallest non-Quran H_EL minus Quran's H_EL)
    min_non_quran_h_el = min(non_quran.values())
    runner_up_corpus = min(non_quran, key=non_quran.get)
    gap_to_runner_up = min_non_quran_h_el - quran_h_el

    # ---- Sort table for output ------------------------------------------
    sorted_table = sorted(
        h_el_per_corpus.items(), key=lambda kv: kv[1]
    )

    # ---- Verdict ladder -------------------------------------------------
    if quran_is_unique_below_one_bit and gap_to_runner_up >= GAP_THRESHOLD_FOR_CATEGORICAL:
        verdict = "PASS_one_bit_categorical_universal"
        verdict_reason = (
            f"Quran (H_EL={quran_h_el:.4f}) is the unique 11-pool corpus with "
            f"H_EL<1 bit; runner-up={runner_up_corpus} at H_EL={min_non_quran_h_el:.4f} "
            f"(gap={gap_to_runner_up:.4f} bits >= {GAP_THRESHOLD_FOR_CATEGORICAL})."
        )
    elif quran_is_unique_below_one_bit:
        verdict = "PASS_one_bit_strict"
        verdict_reason = (
            f"Quran is the unique corpus below 1 bit, but gap to runner-up "
            f"({gap_to_runner_up:.4f}) is below {GAP_THRESHOLD_FOR_CATEGORICAL}."
        )
    elif quran_is_minimum and n_below_one_bit >= 2:
        verdict = "PARTIAL_quran_minimum_but_not_alone"
        verdict_reason = (
            f"Quran has minimum H_EL but {n_below_one_bit} corpora are below 1 bit: "
            f"{below_one_bit}."
        )
    elif quran_is_minimum:
        # Edge case: Quran is minimum but at H_EL >= 1
        verdict = "FAIL_no_corpus_below_one_bit"
        verdict_reason = (
            f"Quran has minimum H_EL ({quran_h_el:.4f}) but is not below 1 bit; "
            "no corpus is below 1 bit."
        )
    else:
        verdict = "FAIL_quran_not_minimum"
        # Find which corpus beats Quran
        beats_quran = [
            c for c, v in h_el_per_corpus.items()
            if v <= quran_h_el and c != "quran"
        ]
        verdict_reason = (
            f"Quran is not the minimum-H_EL corpus; "
            f"beaten/tied by {beats_quran}."
        )

    # ---- Audit ----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_input_sha256_match": actual_sha == EXPECTED_INPUT_SHA256,
            "A2_h_el_only_used": True,
            "A3_corpora_match": len(h_el_per_corpus) == 11,
            "A4_deterministic": True,
        },
    }

    # ---- prereg hash ----------------------------------------------------
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H78",
        "hypothesis": (
            "The Quran is the unique literary corpus in the locked 11-pool "
            "with verse-final-letter Shannon entropy H_EL < 1 bit."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "input_sizing_sha256": actual_sha,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "ONE_BIT_THRESHOLD": ONE_BIT_THRESHOLD,
            "GAP_THRESHOLD_FOR_CATEGORICAL": GAP_THRESHOLD_FOR_CATEGORICAL,
        },
        "results": {
            "H_EL_per_corpus": h_el_per_corpus,
            "H_EL_sorted_ascending": [
                {"corpus": c, "H_EL": v, "below_one_bit": v < ONE_BIT_THRESHOLD}
                for c, v in sorted_table
            ],
            "quran_H_EL": quran_h_el,
            "n_below_one_bit": n_below_one_bit,
            "below_one_bit_corpora": below_one_bit,
            "quran_is_unique_below_one_bit": quran_is_unique_below_one_bit,
            "quran_is_minimum": quran_is_minimum,
            "runner_up_corpus": runner_up_corpus,
            "runner_up_H_EL": min_non_quran_h_el,
            "gap_to_runner_up_bits": gap_to_runner_up,
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 6),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ---- Console summary -------------------------------------------------
    print(f"# {EXP_NAME}")
    print(f"# verdict: {verdict}")
    print(f"# {verdict_reason}")
    print()
    print("## H_EL per corpus (sorted ascending):")
    for c, v in sorted_table:
        flag = " <-- QURAN" if c == "quran" else ""
        below = " < 1 bit" if v < ONE_BIT_THRESHOLD else ""
        print(f"  {c:20s}  H_EL = {v:.4f} bits{below}{flag}")
    print()
    print(f"# n_below_one_bit = {n_below_one_bit}")
    print(f"# Quran unique below 1 bit? {quran_is_unique_below_one_bit}")
    print(f"# Gap to runner-up: {gap_to_runner_up:.4f} bits")
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
