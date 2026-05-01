"""
exp92_genai_adversarial_forge/run.py
=====================================
SCAFFOLD — EXECUTION DEFERRED (requires LLM API credentials).

Pre-registered in PREREG.md. This stub documents the frozen attack
protocol and emits a placeholder receipt. Actual execution requires:

    pip install openai anthropic google-generativeai
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...
    export GOOGLE_API_KEY=...

Then replace the `_call_llm()` stub with real API calls and run.

Reads (integrity-checked):
    phase_06_phi_m.pkl -> reference centroid for prompt-coaching

Writes ONLY under results/experiments/exp92_genai_adversarial_forge/
"""
from __future__ import annotations

import json
import sys
import time
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

EXP = "exp92_genai_adversarial_forge"

# Pre-registered constants (from PREREG.md; DO NOT MODIFY)
W_T = 0.5329
W_EL = 4.1790
B_CONST = -1.5221
ATTACK_BUDGET_PER_MODEL = 10_000
NEAR_MISS_MARGIN = 0.10
OOV_CUTOFF = 0.95
PROMPT_VARIANTS = ["V1_direct", "V2_informed", "V3_coached", "V4_iterative"]
MODELS_TARGET = [
    "gpt-4o",
    "claude-3.5-sonnet",
    "claude-3-opus",
    "gemini-1.5-pro",
    "llama-3.1-405b-instruct",
]


def _call_llm(model: str, prompt: str) -> str:
    """STUB — replace with real API call.

    When implemented, must:
    1. Call the named model with the given prompt.
    2. Return the generated Arabic text as a single string (verses separated by newlines).
    3. Raise on API error so the outer loop can retry.
    """
    raise NotImplementedError(
        f"exp92 is scaffold-only; LLM API credentials not present. "
        f"Implement _call_llm() and re-run to execute. model={model}"
    )


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] SCAFFOLD MODE — no LLM execution. See PREREG.md for frozen spec.")
    print(f"[{EXP}] Target equation: L = {W_T}*T + {W_EL}*EL + {B_CONST}")
    print(f"[{EXP}] Attack budget: {ATTACK_BUDGET_PER_MODEL} per (model, variant) × "
          f"{len(MODELS_TARGET)} models × {len(PROMPT_VARIANTS)} variants = "
          f"{ATTACK_BUDGET_PER_MODEL * len(MODELS_TARGET) * len(PROMPT_VARIANTS):,} total attempts")
    print(f"[{EXP}] Models: {MODELS_TARGET}")
    print(f"[{EXP}] Prompt variants: {PROMPT_VARIANTS}")
    print(f"[{EXP}] Pre-registered verdicts: PASS_any_forge / PASS_near_miss / "
          f"FAIL_no_forge / INCONCLUSIVE_attack_weak")

    elapsed = time.time() - t0

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "mode": "SCAFFOLD_ONLY",
        "execution_deferred_reason": (
            "LLM API credentials not available in this session. "
            "Pre-registered spec frozen in PREREG.md; execution requires replacing "
            "_call_llm() with real API calls and supplying credentials."
        ),
        "prereg_document": "experiments/exp92_genai_adversarial_forge/PREREG.md",
        "prereg_constants": {
            "w_T": W_T,
            "w_EL": W_EL,
            "b": B_CONST,
            "attack_budget_per_model": ATTACK_BUDGET_PER_MODEL,
            "near_miss_margin": NEAR_MISS_MARGIN,
            "oov_cutoff": OOV_CUTOFF,
            "prompt_variants": PROMPT_VARIANTS,
            "models_target": MODELS_TARGET,
        },
        "total_attempts_budget": (
            ATTACK_BUDGET_PER_MODEL * len(MODELS_TARGET) * len(PROMPT_VARIANTS)
        ),
        "verdict": "NOT_EXECUTED",
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[{EXP}] Wrote scaffold receipt: {outfile}")
    print(f"[{EXP}] To execute: implement _call_llm() with real API clients and rerun.")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED (scaffold mode).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
