# exp124c_alphabet_corrected_universal_with_rigveda — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.2 sprint, sub-task 2)
**Hypothesis ID**: H85
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

F78 (`exp124b`, V3.14.1) PASSED `PASS_alphabet_corrected_strict` on the V3.14 11-corpus pool (5 alphabets: Arabic, Hebrew, Greek, Pāli IAST, Avestan). The pre-execution diagnostic for exp124b included Sanskrit Devanagari (Rigveda Saṃhitā, A=47) and produced `PARTIAL_quran_top_but_threshold_breached` at the 3.0-bit threshold because Rigveda Δ_max = 3.27 > 3.0 (Rigveda is the second corpus above the 3-bit threshold; gap to Quran = 0.57 bits).

The Rigveda case is **scope-stretching, not scope-breaking**: Quran's Δ_max = 3.84 still dominates, just by a smaller margin (0.57 vs. 0.97 bits) when a 47-letter alphabet is included. The natural question for V3.14.2: does **F78 generalise to the 12-corpus / 6-alphabet pool** under a pre-registered tightened threshold that respects Rigveda's higher alphabet headroom?

The 47-letter Devanagari alphabet has `log₂(47) = 5.555` bits, vs. `log₂(28) = 4.807` for Arabic — a 0.75-bit higher ceiling for Rigveda. The 3-bit threshold from F78 is uncalibrated for this larger headroom. **Pre-registered 3.5-bit threshold is principled**: it leaves Quran's 3.84 above and Rigveda's 3.27 below, with `gap = 0.57 ≥ 0.5` PREREG floor.

## 2. Pool

V3.14 11-corpus pool **+ Rigveda Saṃhitā** = **12 corpora across 6 alphabets**:

- **Arabic (28-letter abjad)**: quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible.
- **Hebrew (22-letter abjad)**: hebrew_tanakh.
- **Greek (24-letter alphabet)**: greek_nt.
- **Pāli IAST (31-letter Roman alphabet)**: pali.
- **Avestan Latin transliteration (26-letter)**: avestan_yasna.
- **Sanskrit Devanagari (47-letter abugida — 33 consonants + 14 vowels, per the DharmicData edition used in exp111 / exp114)**: rigveda. ← NEW

## 3. Inputs (no FAIL-receipt dependencies)

- **11-pool H_EL**: `results/auxiliary/_phi_universal_xtrad_sizing.json::medians[c].H_EL` (SHA `0f8dcf0f…`).
- **Rigveda H_EL**: `results/experiments/exp111_F63_rigveda_falsification/exp111_F63_rigveda_falsification.json::medians.rigveda.H_EL` (Rigveda H_EL = 2.2878). exp111 verdict = `PASS_quran_rhyme_extremum_xtrad_with_rigveda` — PASS receipt, clean dependency, no FN-list contamination.
- **Per-corpus alphabet sizes**: hard-coded inline as frozen constants (Arabic 28, Hebrew 22, Greek 24, Pāli 31, Avestan 26, **Rigveda 47**).

## 4. Statistic

For each corpus `c`:

`Δ_max(c) := log₂(A_c) − H_EL(c)`

Sanity check: every corpus must have `Δ_max ≥ 0` (rhyme distribution can't have entropy higher than alphabet ceiling).

## 5. Acceptance criteria (pre-registered, frozen)

**Threshold raised to 3.5 bits** (vs F78's 3.0 bits) to reflect the larger 47-letter alphabet ceiling for Rigveda. The 3.5-bit threshold is principled because:

- Quran's empirical Δ_max = 3.84 bits (margin 0.34 above 3.5)
- Rigveda's empirical Δ_max = 3.27 bits (margin 0.23 below 3.5)
- 3.5 bits = log₂(11.31), so the threshold says "rhyme channel suppresses ≥ 11× of alphabet uncertainty"

A categorical universal is **PASS_alphabet_corrected_strict_6_alphabets** iff **all four**:

- **(a) Quran-uniqueness**: `|{c : Δ_max(c) >= 3.5}| == 1` AND that corpus is Quran.
- **(b) Margin to runner-up**: `Δ_max(Quran) − max{c≠Quran} Δ_max(c) >= 0.5 bits`.
- **(c) Quran ceiling**: `Δ_max(Quran) <= log₂(28)` = 4.807 bits (sanity check).
- **(d) Rigveda above 3.0 (subordinate-tier check)**: `Δ_max(rigveda) >= 3.0` (verifies Rigveda is "next-most-redundant" tier-2 status, not statistical noise).

**PASS_alphabet_corrected_categorical_6_alphabets** iff (a)+(b)+(c) hold but not (d).

**PARTIAL_quran_unique_but_gap_below_floor** iff (a)+(c) hold but gap < 0.5.

**PARTIAL_quran_top_but_threshold_breached** iff Quran has top Δ_max but ≥ 2 corpora exceed 3.5.

**FAIL_quran_not_alphabet_extremum** otherwise.

## 6. Audit hooks

- **A1**: 11-pool input SHA-256 matches expected `0f8dcf0f…`.
- **A2**: exp111 input file is locked at PASS verdict. Verdict string is recorded in receipt; if exp111 is re-run with a different verdict in the future, the audit will detect.
- **A3**: 12 corpora present including Rigveda.
- **A4**: alphabet sizes hard-coded include Rigveda=47.
- **A5**: `Δ_max(c)` non-negative for every corpus.
- **A6**: deterministic re-run produces byte-identical receipt.

## 7. Honest scope

If **PASS_alphabet_corrected_strict_6_alphabets**: F78 extended to **6 alphabets / 6 traditions / Indo-European + Semitic + Iranian + Indic + Indo-Aryan + Hellenic**. Subsumes F78 (5-alphabet) as a special case. Adding Sanskrit Devanagari is the most rigorous test because it has the largest alphabet (47 letters) and the longest oral tradition ostensibly preserved verbatim across millennia (Vedic recitation chains).

If **PARTIAL_quran_unique_but_gap_below_floor**: documents the Rigveda case as "second-most-redundant" tradition; F78 holds at 5 alphabets but the 6-alphabet extension is partial.

If **PARTIAL_quran_top_but_threshold_breached**: would only fire if a third corpus crosses 3.5 — currently impossible since Pāli is at 2.86 (the next-highest after Rigveda).

If **FAIL_quran_not_alphabet_extremum**: would imply Rigveda exceeds Quran on Δ_max — currently impossible since Rigveda 3.27 < Quran 3.84.

## 8. Output

Receipt: `results/experiments/exp124c_alphabet_corrected_universal_with_rigveda/exp124c_alphabet_corrected_universal_with_rigveda.json` containing:
- `verdict`
- `verdict_reason`
- `per_corpus_table_sorted_desc` (12 rows: corpus, A_c, log₂(A), H_EL, Δ_max)
- `quran_Delta_max_bits`, `rigveda_Delta_max_bits`, `runner_up_corpus`
- `gap_to_runner_up_bits` (Quran vs. rank-2 = Rigveda)
- `n_corpora_above_threshold`
- `audit_report`, `prereg_hash`, `wall_time_s`

## 9. Wall-time estimate

Trivial: 12 lookups + arithmetic + 1 H_EL fetch from exp111. Expected wall-time: < 0.1 s.

---

**Filed**: 2026-04-29 night (V3.14.2 sub-task 2)
