# exp124_one_bit_threshold_universal — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 evening, V3.14 candidate sprint, sub-task 1 of 3)
**Hypothesis ID**: H78
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time (computed from this file's SHA-256 byte-content prior to first run.py invocation)

---

## 1. The question

Is the Quran the **unique literary corpus** in the locked 11-corpus pool whose verse-final-letter Shannon entropy `H_EL` is **below 1 bit**?

A 1-bit threshold is information-theoretically meaningful: `H_EL < 1` means a single binary distinction (e.g. "is the verse-final letter ن?") suffices to capture more than half the rhyme distribution's information content. Any corpus with `H_EL < 1` has rhyme structure essentially captured by **one yes/no question**.

If the Quran is the unique 11-pool corpus with `H_EL < 1`, this is a **categorical universal** stronger than F75:
- F75 says "Quran is at z = -3.89 below universal mean" (statistical, fitted)
- F76 candidate: "Quran alone has H_EL < 1" (categorical, sharp inequality, no fit)

## 2. Pool

Identical to exp122:
- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`
- **Feature**: `H_EL` (median of verse-final-letter Shannon entropy across the corpus's unit pool)
- **Per-corpus values**: from `_phi_universal_xtrad_sizing.json::medians[c].H_EL` (SHA-pinned)

## 3. Statistic

`H_EL_below_1bit(c) := 1 if H_EL(c) < 1 else 0`

Define:
- `S := sum over c of H_EL_below_1bit(c)` (number of corpora below 1 bit)
- `S_quran := H_EL_below_1bit(quran)` (1 iff Quran below 1 bit)
- `gap := H_EL_min_non_quran − H_EL_quran` (Quran's distance from the next-lowest non-Quran corpus)

## 4. Acceptance criteria (pre-registered, frozen)

- **PASS_one_bit_categorical_universal**: `S == 1` AND `S_quran == 1` AND `gap >= 0.30 bits` (Quran is the unique corpus below 1 bit, with ≥ 30 % of a bit's worth of separation from the runner-up).
- **PASS_one_bit_strict**: `S == 1` AND `S_quran == 1` (categorical separation, regardless of gap size).
- **PARTIAL_quran_minimum_but_not_alone**: `H_EL_quran == min over c` AND `S >= 2` (Quran is the smallest but ≥ 2 corpora are below 1 bit).
- **FAIL_quran_not_minimum**: some non-Quran corpus has `H_EL` ≤ Quran's `H_EL`.
- **FAIL_audit_*** — SHA-256 mismatch, etc.

The `0.30 bits` gap threshold is chosen because:
- 0.30 bits ≈ 30 % of a single binary distinction's information content.
- Quran's H_EL ≈ 0.97 bits (V3.13 receipt); next-lowest reported ≈ 1.45 bits. Empirical gap ≈ 0.48 bits.
- 0.30 leaves headroom: even if a future corpus has H_EL = 1.27 bits (within 0.30 of Quran), the Quran is still the only corpus below 1 bit (categorical) but the strict-PASS only fires if the runner-up is at ≥ 1.27 bits (i.e. gap ≥ 0.30).

## 5. Verdict ladder

```
PASS_one_bit_categorical_universal  (categorical + ≥0.30 bit margin)
  > PASS_one_bit_strict             (categorical, smaller margin)
  > PARTIAL_quran_minimum_but_not_alone
  > FAIL_quran_not_minimum
  > FAIL_audit_*
```

## 6. Audit hooks

- **A1**: input sizing receipt SHA-256 must match `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22` (locked from `_phi_universal_xtrad_sizing.json` at PREREG seal).
- **A2**: only the `H_EL` feature is read; no other features touched.
- **A3**: 11 corpora present; missing-corpus → `FAIL_audit_missing_corpus`.
- **A4**: re-run produces byte-identical receipt.

## 7. What this experiment does NOT do

- It does **not** test an extended N≥18 pool. PREREG locked to the same 11-corpus pool as exp122 / exp109. Path-C extension is the V3.14+ follow-up.
- It does **not** make a theoretical claim about *why* the 1-bit threshold should hold for non-Quran literary corpora. The mechanism (likely: most natural-language verse-final letter distributions span ≥ 3-4 letters with non-trivial probability mass) is left to PAPER §4.47.28 if PASS.
- It does **not** prove F76 is fundamental — only that it holds categorically on the 11-corpus pool. Falsification by a single corpus with `H_EL < 1` would retire F76 immediately.

## 8. Honest scope

If **PASS** at N=11:
- The 1-bit threshold is **empirically validated** at the 11-corpus pool but is not yet a universal proven across all literary traditions.
- Promotion to F-row: **F76 candidate** with PARTIAL strength (categorical at N=11, awaiting N≥18 confirmation).
- A single counter-example corpus at N≥12 retires F76.

If **PARTIAL** or **FAIL**:
- The 1-bit threshold is not a categorical universal at N=11.
- F75 (Shannon-Rényi-∞ gap, statistical) remains the project headline universal.
- This experiment serves as an **honest negative datum** documenting that simpler categorical universals don't exist at this pool size.

## 9. Output

Receipt: `results/experiments/exp124_one_bit_threshold_universal/exp124_one_bit_threshold_universal.json` containing:
- `verdict` (one of the 5 ladder values above)
- `H_EL_per_corpus` (full 11-value table)
- `n_below_one_bit` (S)
- `quran_is_unique_below_one_bit` (boolean)
- `gap_to_runner_up` (float, bits)
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 10. Wall-time estimate

Trivial: 11 lookups + 1 sort. Expected wall-time: < 0.01 s.

---

**Filed**: 2026-04-29 evening (V3.14 candidate sprint, sub-task 1)
