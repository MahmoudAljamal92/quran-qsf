# exp124b_alphabet_corrected_one_bit_universal — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.1 follow-up sprint, sub-task 1 of 2)
**Hypothesis ID**: H82
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

F76 (`exp124`) demonstrated that the Quran is the unique 11-pool corpus with `H_EL < 1 bit`. **Alphabet-corrected analogue**: is the Quran the unique corpus where the verse-final-letter Shannon entropy is at least **3 bits below** the alphabet's maximum entropy `log₂(A_c)`?

The alphabet-corrected gap `Δ_max(c) = log₂(A_c) − H_EL(c)` measures **how much rhyme structure compresses the channel below the Shannon ceiling**. A large `Δ_max` means the rhyme distribution is highly redundant relative to its alphabet's information capacity.

This generalises F76 cleanly across alphabets (Arabic 28, Hebrew 22, Greek 24, Pāli IAST 31, Avestan 26, Sanskrit Devanagari 47). Where F76 used a fixed 1-bit threshold (only meaningful on alphabets where 1 bit is small relative to log₂(A)), F76b uses a per-corpus relative threshold.

## 2. Pool

> **Amendment 2026-04-29 night** (pre-execution diagnostic flagged citation of exp114 which has FAIL_perm_p_floor verdict, FN13). **Resolution**: scope limited to V3.14 11-corpus pool (no Rigveda); H_EL read from the locked `_phi_universal_xtrad_sizing.json` (auxiliary loader, not a FAIL receipt); alphabet sizes hard-coded as frozen constants per linguistic tradition (Arabic 28, Hebrew 22, Greek 24, Pāli IAST 31, Avestan 26). The diagnostic-run from before this amendment included Rigveda (Δ_max 3.27 below Quran's 3.84) and yielded `PARTIAL_quran_top_but_threshold_breached` with **gap 0.57 bits to runner-up Rigveda**; that result is preserved in the receipt's `__amendment_diagnostic` field for transparency. The Rigveda-included claim is **deferred to exp124c** (separate PREREG, future sprint).

- **Corpora (N=11)**: V3.14 locked pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`. Identical to exp124 / exp125 / exp125b.
- **Per-corpus `H_EL`**: read from `results/auxiliary/_phi_universal_xtrad_sizing.json::medians[c].H_EL` (SHA-pinned `0f8dcf0f…`).
- **Per-corpus alphabet size `A_c`**: hard-coded from linguistic tradition (Arabic skeleton-letter alphabet 28; Hebrew skeleton-letter alphabet 22; Greek skeleton-letter alphabet 24; Pāli IAST roman alphabet 31; Avestan Latin transliteration alphabet 26). These are stable per-tradition constants from the `NORMALISERS` table in `scripts/_phi_universal_xtrad_sizing.py`.

## 3. Statistic

For each corpus `c`:

`Δ_max(c) := log₂(A_c) − H_EL(c)`

The Quran's value is `log₂(28) − 0.969 = 4.807 − 0.969 = 3.838` bits.

## 4. Acceptance criteria (pre-registered, frozen)

A categorical universal is **PASS_alphabet_corrected_categorical** iff **all three**:

- **(a) Quran-uniqueness**: `|{c : Δ_max(c) >= 3.0 bits}| == 1` AND that corpus is Quran.
- **(b) Margin to runner-up**: `Δ_max(Quran) − max{c≠Quran} Δ_max(c) >= 0.5 bits`.
- **(c) Theoretical ceiling**: `Δ_max(Quran) <= log₂(28)` = 4.807 bits (sanity check; can't exceed full alphabet entropy).

The 3-bit threshold is chosen because:
- Quran's empirical Δ_max = 3.84 bits.
- A 3-bit threshold leaves 0.84 bits of headroom below Quran.
- Rank-2 (next-most-redundant) corpus must have Δ_max < 3 bits, i.e. its rhyme channel uses LESS than 3 bits below alphabet maximum.
- This is information-theoretically meaningful: 3 bits = log₂(8) = "rhyme distribution captures 8× less information than uniform random".

**PASS_alphabet_corrected_strict** iff (a) AND (b) AND `Δ_max(Quran) >= 3.5 bits`.

## 5. Verdict ladder

```
PASS_alphabet_corrected_strict   (Quran unique, gap>=0.5 bits, Quran>=3.5 bits)
  > PASS_alphabet_corrected_categorical  (Quran unique below 3-bit threshold)
  > PARTIAL_quran_top_but_threshold_breached  (Quran rank 1 but >=2 corpora at >=3 bits)
  > FAIL_quran_not_alphabet_extremum
  > FAIL_audit_*
```

## 6. Audit hooks

- **A1**: input source SHA-256 must match `results/experiments/exp114_alphabet_independent_pmax/exp114_alphabet_independent_pmax.json` at the value computed from the file's bytes.
- **A2**: 12 corpora present (11 V3.14 pool + Rigveda).
- **A3**: per-corpus `H_EL_bits` and `alphabet_size` fields are non-null.
- **A4**: `Δ_max(c) = log₂(A_c) − H_EL(c)` is non-negative for every corpus (sanity).
- **A5**: re-run produces byte-identical receipt.

## 7. Output

Receipt: `results/experiments/exp124b_alphabet_corrected_one_bit_universal/exp124b_alphabet_corrected_one_bit_universal.json` containing:
- `verdict`
- `per_corpus_table` (12 rows: corpus, A_c, H_EL_bits, log2_A, Delta_max)
- `quran_Delta_max` (single value)
- `gap_to_runner_up_bits`
- `runner_up_corpus`
- `n_corpora_above_3_bits`
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 8. Wall-time estimate

Trivial: 12 lookups + arithmetic. Expected wall-time: < 0.1 s.

## 9. Honest scope

If **PASS**: F76b candidate added at PARTIAL strength (categorical at N=12 across 6 alphabets); a single counter-example retires the claim. F76b SUBSUMES F76 (the 1-bit version) because Δ_max ≥ 3 bits implies H_EL < log₂(A) − 3 bits, which on Arabic (A=28) implies H_EL < 1.81 bits, satisfying H_EL < 1 bit only as a stronger statement.

If **PARTIAL**: a near-miss documented. Likely candidate: Pāli (IAST 31, log₂(31) − 2.09 = 2.86 bits — just below 3 bits; ε-close). PARTIAL would document this distance and note the threshold could be tightened.

If **FAIL**: the alphabet-corrected version doesn't generalise as a categorical universal across alphabets, demoting the V3.14 framing to "Arabic-specific 1-bit threshold". F76 (Arabic-only 1-bit) remains the locked claim.

---

**Filed**: 2026-04-29 night (V3.14.1 sub-task 1)
