# PREREG — exp114_alphabet_independent_pmax: alphabet-independent p_max and H_EL universal test

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H69.
**Author intent**: test whether **p_max ≈ 0.5** or some alphabet-normalised statistic (e.g., **H_EL / log(A)**) is a **universal constant** across oral-tradition canons spanning 5 alphabet sizes (A ∈ {22, 24, 26, 28, 31, 47}). This formalises the user's "fine-structure constant for oral text" hypothesis as a falsifiable cross-alphabet test on already-locked data.

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **The Quran's p_max = 0.7273 is FAR above any naive 0.5 universal**. Looking at the raw F63/F64 medians, the cross-tradition canons cluster as:
   - Quran (A=28): 0.7273 (uniquely high)
   - Pāli (A=31): 0.4808 (closest to 0.5)
   - Avestan (A=26): 0.3750
   - Greek NT (A=24): 0.3333
   - Rigveda (A=47): 0.3333
   - Hebrew Tanakh (A=22): 0.2414 (well below 0.5)
   
   So the user's "p_max ≈ 0.5 universal" hypothesis (H69-form-1) is **expected to FAIL**: only 1 of 6 traditions hits 0.5 ± 0.05.

2. **An alternative hypothesis is: H_EL / log(A) ≈ const** across oral-tradition canons. This is alphabet-normalised and dimensionless. Pre-run sizing diagnostic (computed from already-locked F63/F64 medians):
   - Quran: H_EL/log(A) = 0.969 / 3.332 = **0.291** (uniquely low)
   - Pāli: 2.090 / 3.434 = 0.609
   - Avestan: 2.118 / 3.258 = 0.650
   - Greek NT: 2.434 / 3.178 = 0.766
   - Rigveda: 2.288 / 3.850 = 0.594
   - Hebrew Tanakh: 3.053 / 3.091 = 0.988
   
   So even on the normalised metric, the Quran is the **unique outlier**, not an example of a shared universal. H69-form-2 is also expected to FAIL as a Quran-shared-with-others claim.

3. **The most informative HONEST hypothesis (H69-form-3)**: define a "rhyme-concentration normalised statistic" `R(C, A) = H_EL(C) / log(A)`; test whether the Quran is in the bottom 5 % of this distribution across 12+ corpora (Quran, 6 Arabic peers, Hebrew Tanakh, Greek NT, Pāli, Avestan, Rigveda). This is the alphabet-independent re-framing of F48 / F63 / F64.

4. **All three forms are tested and reported**. Forms 1 and 2 are pre-registered to FAIL (transparent disclosure of the reasoning); form 3 is pre-registered to PASS based on the existing locked data.

5. **No new data collection is needed** — exp114 is a derivation from already-locked F63/F64 medians (`results/auxiliary/_phi_universal_xtrad_sizing.json` and `exp111` Rigveda receipt) plus locked alphabet-size constants.

---

## 1. Question

Is there an alphabet-independent universal rhyme-concentration constant across cross-tradition oral-religious canons, and where does the Quran sit on it?

---

## 2. Data — locked

**Source receipts (byte-locked SHA-256)**:
- F63 medians: `results/auxiliary/_phi_universal_xtrad_sizing.json` (Quran + 6 Arabic peers + Tanakh + Greek NT + Pāli + Avestan)
- F64 Rigveda median: `results/experiments/exp111_F63_rigveda_falsification/exp111_F63_rigveda_falsification.json`

**Locked alphabet sizes** (from prior F55/F63/F64 PREREGs):
- Arabic (28 letters)
- Hebrew (22 consonants — WLC consonant skeleton)
- Greek (24 letters — post-normaliser, sigma-folded)
- Pāli (31 letters — IAST: 8 vowels + 22 consonants + 1 niggahīta)
- Avestan (26 letters — Latin transliteration via HTML entities)
- Devanagari (47 letters — 33 consonants + 14 vowels per F64 normaliser)

**Pool**: 12 corpora — Quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible (all A=28); hebrew_tanakh (A=22); greek_nt (A=24); pali (A=31); avestan_yasna (A=26); rigveda (A=47).

---

## 3. Protocol

For each corpus C with measured (p_max, H_EL) and locked alphabet size A:

1. Compute `R_pmax(C) = p_max(C)` (raw)
2. Compute `R_pmax_normalised(C) = p_max(C) × A` (uniformity excess factor; = 1 under uniform end-letter distribution)
3. Compute `R_HEL(C) = H_EL(C) / log(A)` (normalised rhyme entropy; = 1 under uniform end-letter distribution)

**Three forms tested**:

**H69-form-1**: `mean(p_max | oral-tradition canons) = 0.5 ± 0.05` AND `std(p_max) ≤ 0.10`. Decision: reject if mean falls outside 0.5 ± 0.05 OR std > 0.10.

**H69-form-2**: `mean(R_HEL | oral-tradition canons) = 0.5 ± 0.10` AND `std(R_HEL) ≤ 0.15`. Same decision rule on R_HEL = H_EL/log(A).

**H69-form-3**: `Quran R_HEL is bottom 5 % of the 12-corpus distribution` AND `Quran R_HEL ≤ 0.5 × median(R_HEL_others)`. Quran is the unique outlier, not a member of a shared universal.

**Permutation null** (form-3): 10,000 random label-shuffles of corpus identity preserving R_HEL values; count how often the Quran-position lands in the bottom 1 of 12 ranks. Expected null = 1/12 ≈ 0.083. Empirical < 0.05 confirms Quran is non-randomly the lowest.

---

## 4. Decision rule (locked)

- PASS_quran_unique_outlier: H69-form-1 FAILS, H69-form-2 FAILS, H69-form-3 PASSES (Quran is the unique alphabet-normalised rhyme-concentration outlier, not a shared universal).
- PASS_universal_constant_form_1: H69-form-1 PASSES (raw p_max is the universal).
- PASS_universal_constant_form_2: H69-form-2 PASSES (normalised R_HEL is the universal).
- FAIL_no_clean_signal: all three forms fail.

---

## 5. Audit hooks

- A1: source receipts SHA-256 byte-match locked.
- A2: 12 corpora present with both p_max and H_EL non-NaN.
- A3: alphabet sizes locked from prior PREREGs (no re-derivation; byte-fingerprint match required).
- A4: rerun-determinism (deterministic computation; no randomness except permutation null with seed = 42).

---

## 6. Receipt path

`results/experiments/exp114_alphabet_independent_pmax/exp114_alphabet_independent_pmax.json`

---

## 7. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H69 reserved in `HYPOTHESES_AND_TESTS.md`.
