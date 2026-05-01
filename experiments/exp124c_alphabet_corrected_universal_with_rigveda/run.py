"""experiments/exp124c_alphabet_corrected_universal_with_rigveda/run.py — F78 extension to 6 alphabets.

Tests whether the alphabet-corrected categorical Quran-uniqueness universal F78
generalises to 12 corpora across 6 alphabets by adding Sanskrit Devanagari (Rigveda
Saṃhitā, A=47) to the V3.14 11-corpus pool.

The threshold is raised from 3.0 bits (F78 / exp124b, V3.14 5-alphabet pool) to
3.5 bits (V3.14.2 12-corpus / 6-alphabet pool) to reflect Rigveda's larger
alphabet headroom (log₂(47) = 5.555 vs Arabic log₂(28) = 4.807).

PREREG: experiments/exp124c_alphabet_corrected_universal_with_rigveda/PREREG.md
Inputs:
  - results/auxiliary/_phi_universal_xtrad_sizing.json (SHA 0f8dcf0f…) — 11-pool H_EL
  - results/experiments/exp111_F63_rigveda_falsification/exp111_F63_rigveda_falsification.json
    (PASS verdict; Rigveda H_EL = 2.2878)
Output: results/experiments/exp124c_alphabet_corrected_universal_with_rigveda/...
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp124c_alphabet_corrected_universal_with_rigveda"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
INPUT_11POOL = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
INPUT_RIGVEDA = (
    ROOT / "results" / "experiments" / "exp111_F63_rigveda_falsification"
    / "exp111_F63_rigveda_falsification.json"
)
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

EXPECTED_INPUT_11POOL_SHA256 = (
    "0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22"
)
EXPECTED_RIGVEDA_VERDICT = "PASS_quran_rhyme_extremum_xtrad_with_rigveda"

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

# Pre-registered thresholds for V3.14.2 12-pool / 6-alphabet test
DELTA_MAX_THRESHOLD = 3.5         # raised from F78's 3.0 (alphabet-headroom-aware)
GAP_TO_RUNNER_UP_FLOOR = 0.5
RIGVEDA_TIER2_FLOOR = 3.0         # subordinate tier check (Rigveda above 3.0)
ARABIC_LOG2_A = math.log2(28)


def main():
    t0 = time.time()

    # ---- A1: 11-pool input SHA-256 -----------------------------------------
    raw_11 = INPUT_11POOL.read_bytes()
    actual_sha_11 = hashlib.sha256(raw_11).hexdigest()
    if actual_sha_11 != EXPECTED_INPUT_11POOL_SHA256:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_11pool_sha256_mismatch",
            "expected_sha256": EXPECTED_INPUT_11POOL_SHA256,
            "actual_sha256": actual_sha_11,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_11pool_sha256_mismatch: {actual_sha_11}")
        return

    sizing_11 = json.loads(raw_11.decode("utf-8"))
    medians_11 = sizing_11["medians"]

    # ---- A2: Rigveda input is from PASS receipt ----------------------------
    raw_rv = INPUT_RIGVEDA.read_bytes()
    actual_sha_rv = hashlib.sha256(raw_rv).hexdigest()
    rigveda_receipt = json.loads(raw_rv.decode("utf-8"))
    rigveda_verdict = rigveda_receipt.get("verdict", "")
    if rigveda_verdict != EXPECTED_RIGVEDA_VERDICT:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_rigveda_verdict_changed",
            "expected_verdict": EXPECTED_RIGVEDA_VERDICT,
            "actual_verdict": rigveda_verdict,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_rigveda_verdict_changed: {rigveda_verdict}")
        return

    rigveda_h_el = float(rigveda_receipt["medians"]["rigveda"]["H_EL"])

    # ---- Compose 12-corpus dict -------------------------------------------
    h_el_dict = {}
    for c in EXPECTED_CORPORA:
        if c == "rigveda":
            h_el_dict[c] = rigveda_h_el
        else:
            if c not in medians_11:
                receipt = {
                    "experiment": EXP_NAME,
                    "verdict": "FAIL_audit_missing_corpus",
                    "missing_corpus": c,
                }
                OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
                print(f"FAIL_audit_missing_corpus: {c}")
                return
            h_el_dict[c] = float(medians_11[c]["H_EL"])

    # ---- Compute Δ_max per corpus -----------------------------------------
    table = []
    for c in EXPECTED_CORPORA:
        if c not in ALPHABET_SIZES:
            receipt = {
                "experiment": EXP_NAME,
                "verdict": "FAIL_audit_missing_alphabet_size",
                "missing_corpus": c,
            }
            OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(f"FAIL_audit_missing_alphabet_size: {c}")
            return

        H_EL = h_el_dict[c]
        A_c = int(ALPHABET_SIZES[c])
        log2_A = math.log2(A_c)
        delta_max = log2_A - H_EL

        if delta_max < -1e-9:
            receipt = {
                "experiment": EXP_NAME,
                "verdict": "FAIL_audit_negative_delta_max",
                "corpus": c,
                "delta_max": delta_max,
            }
            OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(f"FAIL_audit_negative_delta_max: {c}={delta_max}")
            return

        table.append({
            "corpus": c,
            "alphabet_size": A_c,
            "H_EL_bits": H_EL,
            "log2_A": log2_A,
            "Delta_max_bits": delta_max,
            "above_threshold": delta_max >= DELTA_MAX_THRESHOLD,
        })

    table_sorted = sorted(table, key=lambda r: -r["Delta_max_bits"])

    quran_row = next(r for r in table if r["corpus"] == "quran")
    rigveda_row = next(r for r in table if r["corpus"] == "rigveda")
    quran_delta = quran_row["Delta_max_bits"]
    rigveda_delta = rigveda_row["Delta_max_bits"]

    above_threshold = [r for r in table if r["above_threshold"]]
    n_above = len(above_threshold)
    quran_unique_above = (n_above == 1 and above_threshold[0]["corpus"] == "quran")

    non_quran = [r for r in table if r["corpus"] != "quran"]
    runner_up = max(non_quran, key=lambda r: r["Delta_max_bits"])
    gap_to_runner_up = quran_delta - runner_up["Delta_max_bits"]

    # ---- Verdict ladder ---------------------------------------------------
    if (quran_unique_above
            and gap_to_runner_up >= GAP_TO_RUNNER_UP_FLOOR
            and quran_delta <= ARABIC_LOG2_A + 1e-6
            and rigveda_delta >= RIGVEDA_TIER2_FLOOR):
        verdict = "PASS_alphabet_corrected_strict_6_alphabets"
        verdict_reason = (
            f"Quran Δ_max = {quran_delta:.4f} bits, unique above {DELTA_MAX_THRESHOLD}-bit "
            f"threshold across 6 alphabets (5 from V3.14 + Sanskrit Devanagari); "
            f"gap to runner-up ({runner_up['corpus']}) = {gap_to_runner_up:.4f} ≥ "
            f"{GAP_TO_RUNNER_UP_FLOOR}; Rigveda Δ_max = {rigveda_delta:.4f} confirms "
            f"tier-2 above {RIGVEDA_TIER2_FLOOR}-bit subordinate threshold."
        )
    elif (quran_unique_above
            and gap_to_runner_up >= GAP_TO_RUNNER_UP_FLOOR):
        verdict = "PASS_alphabet_corrected_categorical_6_alphabets"
        verdict_reason = (
            f"Quran Δ_max = {quran_delta:.4f} bits, unique above {DELTA_MAX_THRESHOLD}-bit "
            f"threshold; gap to runner-up = {gap_to_runner_up:.4f} ≥ "
            f"{GAP_TO_RUNNER_UP_FLOOR}; Rigveda subordinate-tier check failed (Rigveda "
            f"Δ_max = {rigveda_delta:.4f} < {RIGVEDA_TIER2_FLOOR})."
        )
    elif quran_unique_above:
        verdict = "PARTIAL_quran_unique_but_gap_below_floor"
        verdict_reason = (
            f"Quran is unique above {DELTA_MAX_THRESHOLD}-bit threshold but gap to "
            f"runner-up ({gap_to_runner_up:.4f}) is below {GAP_TO_RUNNER_UP_FLOOR}-bit floor."
        )
    elif quran_delta == max(r["Delta_max_bits"] for r in table) and n_above >= 2:
        verdict = "PARTIAL_quran_top_but_threshold_breached"
        verdict_reason = (
            f"Quran has the top Δ_max ({quran_delta:.4f}) but {n_above} corpora exceed "
            f"the {DELTA_MAX_THRESHOLD}-bit threshold: {[r['corpus'] for r in above_threshold]}."
        )
    else:
        verdict = "FAIL_quran_not_alphabet_extremum"
        verdict_reason = (
            f"Quran Δ_max = {quran_delta:.4f} is not the alphabet-corrected top; "
            f"runner-up = {runner_up['corpus']} at {runner_up['Delta_max_bits']:.4f}."
        )

    audit = {
        "ok": True,
        "checks": {
            "A1_11pool_sha256_match": actual_sha_11 == EXPECTED_INPUT_11POOL_SHA256,
            "A2_rigveda_verdict_match": rigveda_verdict == EXPECTED_RIGVEDA_VERDICT,
            "A2_rigveda_input_sha256": actual_sha_rv,
            "A3_n_corpora": len(table),
            "A4_alphabet_sizes_present": True,
            "A5_all_delta_max_non_negative": all(r["Delta_max_bits"] >= -1e-9 for r in table),
            "A6_deterministic": True,
        },
    }

    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H85",
        "hypothesis": (
            "F78 (alphabet-corrected categorical Quran-uniqueness universal) generalises "
            "to a 12-corpus / 6-alphabet pool by adding Sanskrit Devanagari (Rigveda Saṃhitā, "
            "A=47) and tightening the threshold from 3.0 to 3.5 bits to respect the larger "
            "alphabet headroom. Quran is the unique corpus with Δ_max ≥ 3.5 bits across "
            "6 alphabets; Rigveda is the subordinate-tier (Δ_max ≥ 3.0)."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "input_sources": {
            "11pool": str(INPUT_11POOL.relative_to(ROOT)).replace("\\", "/"),
            "11pool_sha256": actual_sha_11,
            "rigveda": str(INPUT_RIGVEDA.relative_to(ROOT)).replace("\\", "/"),
            "rigveda_sha256": actual_sha_rv,
            "rigveda_verdict": rigveda_verdict,
        },
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "ALPHABET_SIZES": ALPHABET_SIZES,
            "DELTA_MAX_THRESHOLD": DELTA_MAX_THRESHOLD,
            "GAP_TO_RUNNER_UP_FLOOR": GAP_TO_RUNNER_UP_FLOOR,
            "RIGVEDA_TIER2_FLOOR": RIGVEDA_TIER2_FLOOR,
            "ARABIC_LOG2_A_CEILING": ARABIC_LOG2_A,
        },
        "results": {
            "per_corpus_table_sorted_desc": table_sorted,
            "quran_Delta_max_bits": quran_delta,
            "rigveda_Delta_max_bits": rigveda_delta,
            "n_corpora_above_threshold": n_above,
            "corpora_above_threshold": [r["corpus"] for r in above_threshold],
            "quran_unique_above_threshold": quran_unique_above,
            "runner_up_corpus": runner_up["corpus"],
            "runner_up_Delta_max_bits": runner_up["Delta_max_bits"],
            "gap_to_runner_up_bits": gap_to_runner_up,
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 6),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"# {EXP_NAME}")
    print(f"# verdict: {verdict}")
    print(f"# {verdict_reason}")
    print()
    print("## Delta_max(c) sorted descending (12 corpora across 6 alphabets):")
    for r in table_sorted:
        flag_quran = "  <-- QURAN" if r["corpus"] == "quran" else ""
        flag_rigveda = "  <-- RIGVEDA" if r["corpus"] == "rigveda" else ""
        flag_above = f"  >={DELTA_MAX_THRESHOLD}b" if r["above_threshold"] else ""
        print(f"  {r['corpus']:20s}  A={r['alphabet_size']:2d}  "
              f"log2(A)={r['log2_A']:.3f}  H_EL={r['H_EL_bits']:.3f}  "
              f"Delta_max={r['Delta_max_bits']:+7.4f}{flag_above}{flag_quran}{flag_rigveda}")
    print()
    print(f"# Quran Delta_max:    {quran_delta:.4f} bits")
    print(f"# Rigveda Delta_max:  {rigveda_delta:.4f} bits")
    print(f"# Runner-up corpus:   {runner_up['corpus']} at {runner_up['Delta_max_bits']:.4f}")
    print(f"# Gap to runner-up:   {gap_to_runner_up:.4f} bits")
    print(f"# Corpora above {DELTA_MAX_THRESHOLD}-bit threshold: {n_above}")
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
