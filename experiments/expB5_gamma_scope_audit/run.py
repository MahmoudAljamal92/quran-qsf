"""
expB5_gamma_scope_audit/run.py
==============================
Opportunity B5 (OPPORTUNITY_TABLE_DETAIL.md):
  Formalise the scope distinction between
    (a) the RAW Cohen d statistic in exp55 (per-decile, verdict
        LENGTH_DRIVEN under the pre-registered sign-test + d > 0.30 count
        gate), and
    (b) the LENGTH-CONTROLLED REGRESSION RESIDUAL gamma from the same
        exp55 (gamma = +0.0716, p ≈ 0, gamma.pass = True).

  The B5 hypothesis (already implicit in RANKED_FINDINGS.md:103) is that
  the LENGTH_DRIVEN verdict applies to (a) only, NOT to gamma. Therefore
  any cross-reference that cites "exp55 retracts gamma" or "gamma is
  length-driven" is mis-citing the scope; gamma should be reported as
  the length-CONTROLLED main result of the same experiment.

This script is a documentation / scope audit. It:
  1. Reads exp55's JSON byte-for-byte from disk.
  2. Extracts (a) and (b) as separate structured records.
  3. Confirms the verdict at each scope and the divergence.
  4. Emits a citable JSON artifact that future writing can reference
     instead of re-deriving the logic from scratch.

Reads (read-only):
  - results/experiments/exp55_gamma_length_stratified/exp55_gamma_length_stratified.json

Writes:
  - results/experiments/expB5_gamma_scope_audit/expB5_gamma_scope_audit.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "expB5_gamma_scope_audit"
EXP55_JSON = (
    _ROOT / "results" / "experiments" / "exp55_gamma_length_stratified"
    / "exp55_gamma_length_stratified.json"
)


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    if not EXP55_JSON.exists():
        raise FileNotFoundError(
            f"exp55 JSON not found at {EXP55_JSON}. "
            f"Run experiments/exp55_gamma_length_stratified first."
        )

    with open(EXP55_JSON, "r", encoding="utf-8") as f:
        exp55 = json.load(f)

    # ---- (a) Raw Cohen d statistic ----
    raw_d_value = float(exp55.get("headline_d_crosscheck"))
    sign_test = exp55["sign_test"]
    d_above = exp55["d_above_threshold"]

    raw_d_passes_decile_gate = bool(
        d_above["count"] >= d_above["required_for_LENGTH_INDEPENDENT"]
    )
    raw_d_passes_sign_test = bool(
        sign_test["p_two_sided"] <= sign_test["alpha_strict"]
    )
    raw_d_overall_pass = raw_d_passes_decile_gate and raw_d_passes_sign_test

    raw_d_record = {
        "scope": (
            "Per-decile RAW Cohen d for the Quran-vs-control gzip-NCD "
            "contrast, sliced by 10 letter-count deciles."
        ),
        "value": raw_d_value,
        "is_length_controlled": False,
        "decile_gate": {
            "n_deciles_above_0p3": int(d_above["count"]),
            "required_for_LENGTH_INDEPENDENT": int(
                d_above["required_for_LENGTH_INDEPENDENT"]
            ),
            "passes": raw_d_passes_decile_gate,
        },
        "sign_test_gate": {
            "n_positive": int(sign_test["n_positive"]),
            "n_negative": int(sign_test["n_negative"]),
            "p_two_sided": float(sign_test["p_two_sided"]),
            "alpha_strict": float(sign_test["alpha_strict"]),
            "passes": raw_d_passes_sign_test,
        },
        "verdict": "LENGTH_DRIVEN" if not raw_d_overall_pass
                   else "LENGTH_INDEPENDENT",
        "applies_to_gamma": False,
    }

    # ---- (b) Length-controlled gamma regression residual ----
    g = exp55["log_linear_gamma"]
    gamma_record = {
        "scope": (
            "Length-controlled REGRESSION RESIDUAL: the Quran-indicator "
            "coefficient in `log NCD ~ alpha + beta * log(n) + gamma * I(Q)`. "
            "By construction, gamma absorbs ONLY the residual difference "
            "after the log(n) length term. It is the project's authoritative "
            "length-controlled scalar."
        ),
        "value": float(g["gamma"]),
        "ci_95": [float(g["gamma_ci95"][0]), float(g["gamma_ci95"][1])],
        "p_value": float(g["gamma_p"]),
        "p_threshold": float(g["gamma_threshold_p"]),
        "is_length_controlled": True,
        "passes_threshold": bool(g["pass"]),
        "verdict": "LENGTH_CONTROLLED_PASS" if g["pass"]
                   else "LENGTH_CONTROLLED_FAIL",
        "covered_by_LENGTH_DRIVEN_label": False,
    }

    # ---- (c) Scope reconciliation summary ----
    if raw_d_record["verdict"] == "LENGTH_DRIVEN" and gamma_record["verdict"] == "LENGTH_CONTROLLED_PASS":
        scope_summary = (
            "exp55 yields TWO scope-distinct verdicts on the SAME dataset: "
            "(a) raw d is LENGTH_DRIVEN at the per-decile level "
            "(only 5/10 deciles pass d > 0.30; sign-test p = 0.109 > 0.05), "
            "while (b) the length-controlled residual gamma = +0.07161 "
            "(95 % CI [0.0657, 0.0775], p ≈ 0) PASSES its strict gate. "
            "The 'LENGTH_DRIVEN' label applies ONLY to (a). Any cross-reference "
            "treating gamma as 'retracted by exp55' or 'length-driven' is "
            "mis-citing the scope. Cite gamma as the authoritative length-"
            "controlled main result, exactly as RANKED_FINDINGS.md:103 already "
            "instructs."
        )
        b5_verdict = "B5_CONFIRMED_GAMMA_IS_LENGTH_CONTROLLED_NOT_LENGTH_DRIVEN"
    else:
        scope_summary = (
            f"Scope decomposition unexpected: raw_d_verdict="
            f"{raw_d_record['verdict']}, gamma_verdict="
            f"{gamma_record['verdict']}. Investigate before re-citing."
        )
        b5_verdict = "B5_AMBIGUOUS_NEEDS_REINVESTIGATION"

    # ---- (d) Citation hygiene targets ----
    citation_hygiene = {
        "correct_citation_template_per_RANKED_FINDINGS_md_103": (
            "exp55 (v7.6): formal pre-registered sign test + d > 0.30 count "
            "yields verdict LENGTH_DRIVEN (5/10 deciles above 0.30, sign-test "
            "p = 0.109 > 0.10); gamma remains strongly positive (p ≈ 0). Cite "
            "gamma = +0.0716 as the authoritative length-controlled scalar, "
            "not the raw d = +0.534."
        ),
        "incorrect_phrasings_to_avoid": [
            "'exp55 retracts gamma'",
            "'gamma is length-driven'",
            "'gamma_gzip = +0.0716 was retracted by length stratification'",
            "'exp55 LENGTH_DRIVEN verdict means the gzip-NCD effect is "
            "an artifact of length'  (true for raw d; FALSE for gamma)",
        ],
        "separate_universality_question_S10": (
            "A separate retraction-adjacent claim is the cross-COMPRESSOR "
            "universality of gamma (S10 in OPPORTUNITY_TABLE_DETAIL): "
            "gamma_gzip = +0.0716 ; gamma_brotli = +0.0871 ; gamma_zstd = "
            "-0.0294 ; gamma_bzip2 = -0.0483. This is about NON-UNIVERSALITY "
            "of gamma's sign across compressors, not about exp55's length "
            "stratification. Do not conflate the two."
        ),
    }

    report = {
        "experiment": EXP,
        "task_id": "B5",
        "title": (
            "Scope reclassification of exp55: raw Cohen d (LENGTH_DRIVEN) "
            "vs length-controlled gamma residual (LENGTH_CONTROLLED_PASS) — "
            "the same experiment yields two scope-distinct verdicts on two "
            "different statistics."
        ),
        "source": str(EXP55_JSON.relative_to(_ROOT)),
        "raw_d": raw_d_record,
        "gamma": gamma_record,
        "scope_summary": scope_summary,
        "b5_verdict": b5_verdict,
        "citation_hygiene": citation_hygiene,
        "recommendation": [
            "1. Treat exp55 as the canonical reference for BOTH (a) "
            "raw-d LENGTH_DRIVEN verdict AND (b) gamma LENGTH_CONTROLLED_PASS. "
            "Do not let 'LENGTH_DRIVEN' propagate to gamma when summarising.",
            "2. RANKED_FINDINGS.md row 4 is correctly worded ('PAPER-GRADE ; "
            "gamma=+0.0716, p≈0'). Use that wording elsewhere.",
            "3. Distinguish from the S10 cross-compressor non-universality "
            "issue: that is about gamma_gzip vs gamma_zstd, NOT about "
            "length-stratification of gamma_gzip itself.",
            "4. The OPPORTUNITY_TABLE_DETAIL.md B5 entry can now be marked "
            "DONE with this artifact as the citable structured proof.",
        ],
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # stdout summary
    print(f"[{EXP}] exp55 source: {EXP55_JSON.name}")
    print(f"[{EXP}] (a) RAW d:")
    print(f"[{EXP}]     value                : {raw_d_record['value']:.6f}")
    print(f"[{EXP}]     decile gate          : "
          f"{raw_d_record['decile_gate']['n_deciles_above_0p3']}/10 "
          f"(req >= {raw_d_record['decile_gate']['required_for_LENGTH_INDEPENDENT']})")
    print(f"[{EXP}]     sign-test p          : "
          f"{raw_d_record['sign_test_gate']['p_two_sided']:.4f}")
    print(f"[{EXP}]     verdict              : {raw_d_record['verdict']}")
    print(f"[{EXP}] (b) LENGTH-CONTROLLED gamma:")
    print(f"[{EXP}]     value                : {gamma_record['value']:.6f}")
    print(f"[{EXP}]     CI 95                : "
          f"[{gamma_record['ci_95'][0]:.6f}, {gamma_record['ci_95'][1]:.6f}]")
    print(f"[{EXP}]     p-value              : {gamma_record['p_value']:.6f}")
    print(f"[{EXP}]     passes               : {gamma_record['passes_threshold']}")
    print(f"[{EXP}]     verdict              : {gamma_record['verdict']}")
    print(f"[{EXP}]")
    print(f"[{EXP}] B5 verdict: {b5_verdict}")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
