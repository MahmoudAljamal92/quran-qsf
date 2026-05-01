# exp103_semantic_coherence_floor — Pre-registration (DESIGN-ONLY, NOT YET EXECUTED)

**Hypothesis ID**: H58
**Status**: pre-registered, **DESIGN-ONLY** as of 2026-04-28 evening (Asia/Riyadh). No run script has been executed; no receipt has been produced. This PREREG is hash-locked at the time of writing so that the substantive claim and decision rules cannot be edited after the data is touched.
**Patch context**: v7.9-cand patch H V3.1 — sister design to `exp102_imitation_battery` (structural fingerprint test) and the future Phase-5 clean-room LLM forgery test. **Not on the critical path for the current paper.**
**Supersedes**: nothing.

---

## 0. Why this exists (one paragraph)

The locked Φ_master scalar (`exp96a_phi_master`, F58 = 1,862.31 nats) measures **structural fingerprint** — letter distributions, rhyme rate, conditional entropy of verse-final roots, etc. It does **not** measure semantic coherence, theological consistency, or narrative truthfulness. If a hypothetical clean-room LLM trained only on pre-Islamic Arabic (the future Phase-5 test) produced text that matched Φ_master ≈ 1,862 nats but was semantically incoherent gibberish, the existing detector would call it a "match" while a human reader would not. **`exp103` adds a complementary semantic-coherence floor**: a single scalar `Ψ_coherence` that scores how well a text continues itself across long-range verse boundaries, against an LLM-as-judge measurement protocol that is fixed before any score is opened. The Quran's `Ψ_coherence` becomes a baseline against which forgery candidates (current Markov, future LLM clean-room, alleged human imitations) are compared.

---

## 1. Hypothesis (one paragraph)

**H58 (semantic-coherence floor)**: Under a fixed instruct-LLM-as-judge protocol, the Quran's mean per-verse `Ψ_coherence` score (defined below) is **strictly greater than** the mean `Ψ_coherence` of every text in `exp102`'s imitation battery (Furqan al-Haqq, Musaylimah fragments, Khalifa, Markov-3 baseline, plus any LLM-generated samples). Operationalised: paired Wilcoxon test on per-verse `Ψ_coherence` between Quran (114 surahs, 6,236 verses) and each imitation, **all paired tests must yield p < 0.01 with Quran > imitation**.

If H58 holds, no imitation in the battery achieves both fingerprint-match AND coherence-match simultaneously. If even one imitation does, that imitation is a substantively interesting candidate forgery and gets its own follow-on PREREG.

---

## 2. Locked decision rules

### 2.1 Definition of `Ψ_coherence`

For each verse `v_i` in a text:

1. Strip the verse to its first ~75% of tokens; call this the **prefix** `P_i`.
2. Provide an instruct-LLM (the **judge**) with the **prefix only** plus the *previous K verses* as context (K = 3, locked).
3. Ask the judge to predict the *most likely continuation* under a temperature = 0 deterministic decode.
4. Score the predicted continuation against the actual rest-of-verse `S_i` using **chrF** (character n-gram F-score) — a deterministic, language-agnostic similarity metric.
5. `Ψ_coherence(v_i) = chrF(predicted_continuation, S_i)` ∈ [0, 1].

The text-level scalar is `Ψ_coherence(text) = median over all v_i with at least 8 prefix tokens`.

**Why median, not mean**: mean is hijacked by short verses where chrF is high by luck; median is robust.

### 2.2 Locked judge

- **Model**: a **single, fixed** instruct-LLM whose name + version + revision hash are written into `frozen_constants` at PREREG-lock time and verified at run time.
- **Decoding**: temperature = 0, `top_p = 1.0`, `seed` (where supported by the API) = `42`.
- **Prompt template**: locked verbatim in §3 below; no edits after PREREG-hash.
- **Why fixed**: any change to the judge changes the score; switching judges mid-experiment is a protocol violation. A future PREREG (`exp103b_*`) may run the same protocol with a different judge to test judge-invariance.

### 2.3 Verdict ladder (strict order; first match wins)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_no_judge` | Judge LLM not configured / API unreachable | Configure judge, re-run |
| 2 | `BLOCKED_imitations_missing` | `exp102` has not produced a non-BLOCKED receipt | Acquire imitations and run `exp102` first |
| 3 | `FAIL_judge_drift` | Judge fingerprint (model + version + reported temperature) drifts from the locked constants | Lock judge, re-run |
| 4 | `FAIL_quran_not_above_imitation` | Any imitation has paired Wilcoxon p ≥ 0.01 OR Quran median ≤ imitation median | The semantic-floor claim fails for that imitation; document and open follow-on |
| 5 | `PARTIAL_quran_above_with_caveat` | All paired tests pass at p < 0.01 BUT Quran median lead is < 0.05 chrF on at least one | Borderline pass; report explicitly |
| 6 | **`PASS_quran_strict_above`** | All paired tests pass at p < 0.01 AND Quran median > imitation median + 0.05 chrF for every imitation | H58 confirmed |

### 2.4 Why this is not data-fishing

- **No model selection**: the judge is locked. A second-judge re-test is filed as `exp103b`, not as a re-roll.
- **No prompt selection**: the prompt template is locked. Variants are filed as separate experiments.
- **No metric selection**: chrF is locked. BLEU / ROUGE / cosine-similarity-of-embeddings variants are separate experiments.
- **No imitation cherry-picking**: every text on disk under `data/corpora/imitations/` is scored; reports cannot omit any.
- **All thresholds (p < 0.01, lead > 0.05) are fixed in this PREREG before any scoring is run.**

---

## 3. Frozen prompt template (verbatim; do not edit post-hoc)

```
SYSTEM: You are a careful continuation predictor. Given a text in classical
Arabic and the verse-prefix the user is reading, output the single most
likely continuation of the prefix. Do not paraphrase. Match the register
and meter of the surrounding verses. Output ONLY the continuation, with no
prefix, suffix, or commentary.

USER:
Previous verses (context, K=3):
{previous_3_verses}

Current verse, prefix only:
{prefix}

Continuation (one line, no prefix):
```

Any deviation from this template — even whitespace — invalidates the run.

---

## 4. Frozen constants

- `K = 3` (number of previous verses provided as context).
- `prefix_fraction = 0.75` (first 75 % of tokens of each verse become the prefix; remainder is the held-out continuation).
- `min_prefix_tokens = 8` (verses with fewer than 8 prefix tokens are excluded from the median).
- Judge: **TBD at lock time** — name + version + revision hash recorded in `frozen_constants.judge` of the receipt; the model identifier is written into PREREG_HASH-locked `JUDGE.json` next to the PREREG.
- `seed = 42`, `temperature = 0`, `top_p = 1.0`.
- chrF parameters: `n_char = 6`, `beta = 2`, **case-folded** comparison, **whitespace-normalised** to single space, **diacritics-stripped** for both predicted and actual (so the comparison is on rasm + case-folded ASCII transliteration; or, for Arabic, on diacritic-stripped consonant skeleton). The diacritics-stripped form is to prevent superficial differences in vocalisation from inflating the score.

---

## 5. Audit hooks

- **Judge fingerprint sentinel**: receipt's `frozen_constants.judge.fingerprint` must match the value declared in `experiments/exp103_semantic_coherence_floor/JUDGE.json` (a tiny side-file written at PREREG-lock time). Mismatch fires branch 3.
- **PREREG-hash sentinel**: SHA-256 of this PREREG.md must match `_PREREG_EXPECTED_HASH` in run.py (when run.py is written).
- **API-determinism sentinel**: same prefix, same context, same seed must produce same continuation across two consecutive calls; the receipt logs both, and any disagreement aborts.
- **`exp102` precondition sentinel**: receipt loads `results/experiments/exp102_imitation_battery/exp102_imitation_battery.json`; if its verdict starts with `BLOCKED_*`, branch 2 fires.
- **No-leak sentinel**: the prefix length must be strictly less than the full verse; the predicted continuation must not be allowed to access the held-out portion (verified by re-running with a perturbed prefix and confirming the prediction changes).

---

## 6. Honesty clauses

### 6.1 Cost disclosure

This experiment requires LLM API calls — typically `n_verses × n_imitations` continuation generations. Conservative estimate: 6,236 verses × ~5 imitations ≈ 30,000 calls. Cost-prudent runs subsample per-verse first; subsampling rules must be locked before scoring is started.

### 6.2 No re-roll

If a paired test fails at branch 4, the result stands. No re-running with a different judge, different prompt, or different decoding to "fix" the verdict. A new PREREG with a clearly different protocol may be filed.

### 6.3 Quran-as-baseline is the *floor*, not the *ceiling*

`Ψ_coherence(quran)` could be high or low in absolute terms; the claim is *only relative to the imitation pool*. Even a "perfect" Quran score does not entail unforgeability — a future LLM-generated text could in principle achieve the same Ψ. The claim is "pairwise above the imitation pool currently on disk", not "unbeatable".

### 6.4 LLM-judge limitations

The judge is itself an AI model with its own training distribution; if the judge has been trained on the Quran (almost all current frontier LLMs have), its predictions are biased toward Quran-like continuations. **This is a design weakness**, and the clean-room future test (the LLM that has *not* seen the Quran) is the right next step. `exp103` is honest about this: it measures a relative coherence floor under the *current* generation of judges, knowing that a clean-room judge would be a stricter measurement.

---

## 7. What the experiment does NOT do

- It does **not** establish unforgeability. It only adds a complementary axis to the structural-fingerprint test.
- It does **not** make any theological or literary claim. `Ψ_coherence` is a chrF score, not a literary judgement.
- It does **not** affect F57. Phase 2 stands or falls on its own.
- It does **not** change `results_lock.json`.

---

## 8. Future amendments

If H58 is run and PASSes, the natural follow-ups are:

- `exp103b`: re-run with a different (stronger / weaker) judge to test judge-invariance.
- `exp103c`: replace chrF with a semantic-embedding similarity (e.g. AraBERT-large) to test metric-invariance.
- Phase-5 clean-room LLM as both *generator* and *judge*.

Each follow-up requires a new hash-locked PREREG with a new H-number.

---

## 9. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any judge call is issued or any score is opened. The hash is written to `experiments/exp103_semantic_coherence_floor/PREREG_HASH.txt`. **No `run.py` exists at the time of this PREREG-lock**, by design — the locked decision rules are fixed before the implementation is written. When `run.py` is added, its `_PREREG_EXPECTED_HASH` must match this file's hash; mismatch invalidates the run.

---

## 10. Cross-references

- Sister test (structural fingerprint): `experiments/exp102_imitation_battery/PREREG.md`.
- Locked Φ_master receipt: `results/experiments/exp96a_phi_master/exp96a_phi_master.json`.
- Adversarial Markov-3 baseline already on disk: `results/experiments/exp99_adversarial_complexity/exp99_adversarial_complexity.json`.
- Integrity protocol: `docs/INTEGRITY_PROTOCOL.md`.
