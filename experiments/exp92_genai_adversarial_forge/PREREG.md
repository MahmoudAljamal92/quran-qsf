# exp92_genai_adversarial_forge — PRE-REGISTRATION

**Timestamp**: 2026-04-21 (late evening, v7.7)
**Status**: Frozen BEFORE any run. **Scaffold-only in this session** — PREREG + `run.py` stub committed; execution requires LLM API credentials and is explicitly deferred. The frozen spec below is the audit trail for whoever runs it.

---

## 1. Motivation

External review critique: *"Maybe 7th-century humans couldn't produce the fingerprint, but what if we deliberately try to engineer a text today using supercomputers? Is the fingerprint actually a computational singularity, or just a historical one?"*

This is a **computational-lower-bound challenge** for LC3-70-U. The existing corpus tests all 2 509 known Arabic texts and shows only 7 cross the boundary (all `arabic_bible`). But known Arabic texts do not include *adversarial engineered forgeries*. If an LLM armed with the target equation can generate text that crosses `L > 0`, the fingerprint is "human-natural-distribution unique" but not "computationally unforgeable." If 10 000 LLM attempts all fail to cross, it is a published computational lower bound.

## 2. Hypothesis

**H-GENAI-FORGE** — State-of-the-art LLMs (GPT-4o, Claude 3.5/4 Sonnet/Opus, Gemini 1.5 Pro, or whatever is frontier at run time), given the explicit target equation and informed feedback about the Quran's (T, EL) centroid, cannot generate Arabic text with (T_forge, EL_forge) satisfying `L(x) = 0.5329·T + 4.1790·EL − 1.5221 > 0` in ≥ 1 of N_attempts = 10 000 parallel generations.

## 3. Attack specification (frozen)

- **Target coordinate**: `T ≥ 0` AND `EL ≥ 0.3642` (the EL = 0.3642 boundary at T = 0; any point with both simultaneous conditions clears `L > 0` by the linear equation).
- **Unit size**: each forgery is a single "surah-like" text of 15–100 verses (matching Band-A).
- **Arabic constraint**: outputs must parse as valid Arabic under `camel_tools` tokenisation at ≥ 95 % non-OOV rate (blocks non-Arabic gibberish).
- **Attack budget**: 10 000 independent generations per model; up to 5 frontier models tested in parallel (GPT-4o, Claude 3.5 Sonnet, Claude 3 Opus, Gemini 1.5 Pro, Llama-3.1-405B-instruct or current-frontier equivalents).
- **Prompt strategy**: four variants per model to avoid single-prompt artefacts:
  - V1 direct: "Generate Arabic verses with EL ≥ 0.36 (most verses ending in the same letter) across 15–100 verses."
  - V2 informed: as V1 plus the explicit equation `L = 0.5329·T + 4.1790·EL − 1.5221`.
  - V3 coached: V2 + worked example (one Quran surah's T, EL coordinates, not content).
  - V4 unbounded: V3 + "you may iterate; feedback will be provided each round" (iterative refinement).

## 4. Pre-registered verdict ladder

1. **PASS_any_forge** — at least one attempt across all models and prompts produces Arabic text (at ≥ 95 % CamelTools validity) with `L > 0`. **The fingerprint is computationally forgeable.** LC3-70-U downgraded to a "natural-distribution outlier" claim; no computational-lower-bound claim.
2. **PASS_near_miss** — no attempt crosses `L > 0`, but ≥ 1 attempt reaches `L > −0.10` (within ~20 % of the margin). Fingerprint survives but tightly.
3. **FAIL_no_forge** — all 10 000+ attempts across all models yield `L ≤ −0.10`; no crossing, no near-miss at the margin boundary. **The fingerprint is a computational lower bound under the tested models' capabilities.** LC3-70-U gains the computational-unforgeability claim.
4. **INCONCLUSIVE_attack_weak** — modal Cohen d of forgery attempts vs controls ≤ 0.3 (forgeries are indistinguishable from controls). The attack did not converge on the target; cannot conclude about forgeability.

## 5. Methodology (frozen)

- **Execution environment**: any Python 3.10+ with sklearn; LLM API clients for the listed providers.
- **Per-attempt pipeline**:
  1. Invoke LLM with prompt variant V_k.
  2. Extract Arabic text; validate with `camel_tools` tokeniser (≥ 95 % non-OOV).
  3. Compute `(T, EL)` via `src.features.el_rate` and `src.features.t_tension` (same code path as phase_06).
  4. Score `L = 0.5329·T + 4.1790·EL − 1.5221`.
  5. Log attempt record with prompt variant, model, seed, (T, EL, L), raw text SHA.
- **Attack budget**: 10 000 / model / prompt-variant × 4 variants × 5 models = 200 000 total attempts. At ~$0.002 per attempt this is ~$400 in API costs — reasonable for a paper-grade result.
- **Adversarial fairness**: each model is given the same prompt family; no post-hoc prompt engineering on failed attempts. Iterative V4 is allowed up to 10 refinement rounds per attempt before logging.

## 6. Stakes

- **PASS_any_forge** → LC3-70-U is downgraded to "distinguishes Quran from all known natural Arabic texts" (still a legitimate stylometric claim). The "7th-century computational singularity" angle is lost. **Publication value: still moderate, but no PNAS-grade uniqueness.**
- **FAIL_no_forge** → LC3-70-U gains a "computational lower bound" appendix. Combined with the 2 509-text natural-distribution result, this approaches PNAS significance. **Publication value: high.** Framing: *"the Quranic (T, EL) fingerprint is not reproducible by state-of-the-art LLMs at 200 000 adversarial attempts, establishing a computational lower bound on its construction-complexity."*
- **INCONCLUSIVE** → iterate; use better-coached prompts or fine-tuned models.

## 7. What this experiment does NOT claim

- It does NOT claim divine or supernatural origin.
- It does NOT claim pre-modern humans could not have built it — only that 2026-era frontier LLMs explicitly informed of the target cannot.
- It does NOT claim the fingerprint is information-theoretically unforgeable (a formal proof would require Kolmogorov-complexity arguments).

## 8. Why scaffold-only in this session

LLM API calls require credentials and billed runtime. The session environment does not carry those credentials. The PREREG + `run.py` stub are committed here so that:

- Whoever runs it (user or a later automated session) executes the frozen spec verbatim.
- The result is audit-traceable even if execution happens weeks or months later.
- The commitment is fully public before any execution, blocking cherry-picking the attack parameters post hoc.

## 9. No re-tuning

Attack budget 10 000 / model, 5 models, 4 prompt variants, margin threshold 0.10, CamelTools OOV cut 95 %. Any deviation requires a new experiment number.

---

*Pre-registration committed 2026-04-21 post-exp91. No execution performed in this session.*
