# PREREG — exp116_RG_scaling_collapse: renormalization-group / coarse-graining scaling-law collapse test

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H71.
**Author intent**: test whether the locked 5-D features `[EL_rate, VL_CV, p_max, H_EL, H_cond]` exhibit **power-law scaling under verse-aggregation coarse-graining** with a universal exponent across multiple features ("RG collapse"), and whether the Quran's exponent differs significantly from peer-corpus exponents.

This is the project's first **physics-style scaling-law** test on text data. Pre-registered as EXPLORATORY-LIKELY since the universal-collapse hypothesis is a strong claim that may or may not hold.

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **What "RG collapse" means here**: for a text with N verses, define scale L ∈ {1, 2, 4, 8, 16}. At scale L, group consecutive L verses into "super-verses" by concatenating their text. Compute the per-feature distribution across super-verses. Look for power-law scaling:
   ```
   feature_moment(L) ∝ L^α
   ```
   "Universal collapse" = different features have **the same exponent α** (within tolerance). "Quran-distinctive scaling" = Quran's α differs from peer-corpus α.

2. **What might be expected from physics intuition**:
   - **VL_CV** (verse-length CV) should DECREASE with L like L^(−1/2) under central-limit-theorem averaging if verse lengths are i.i.d. (which they are NOT in the Quran due to rhyme/meter)
   - **p_max** (top end-letter freq) should INCREASE with L → 1 (more dominant letter at coarse scale)
   - **H_EL** should DECREASE with L (concentration at coarse scale)
   - **EL_rate** is a fraction; should be roughly scale-invariant (no power law)
   - **H_cond** (conditional entropy of root transitions) depends on text structure, hard to predict
   
   If all features scale with the SAME exponent up to a sign, that would be a non-trivial universal scaling.

3. **Three forms of the hypothesis**:
   - **Form-1 (universal)**: Quran's per-feature exponents have std(α) < 0.1 (universal exponent across 5 features) AND mean(α) is similar to peer-corpus mean(α) (cross-tradition universal exponent).
   - **Form-2 (Quran-distinctive)**: Quran's per-feature exponents differ from peer-corpus exponents at z > 2.0.
   - **Form-3 (decorrelation)**: at increasing L, the inter-feature correlation matrix changes structure (Quran shows different decorrelation pattern).

4. **Pre-registered honest expectation**: most likely outcome is Form-1 FAIL (different features scale differently), Form-2 PASS for at least one feature (Quran has distinctive scaling on at least one axis). The test is PRIMARILY EXPLORATORY because we have no prior theoretical reason to expect universal collapse.

5. **Why this matters even if it FAILS**: a clean negative result on RG-collapse establishes that text-feature scaling is inherently multi-dimensional (not reducible to a single exponent), which is itself a publishable finding. A POSITIVE result would be PNAS-tier.

---

## 1. Question

Do the 5-D Φ_M features exhibit power-law scaling under verse-aggregation coarse-graining, with a universal exponent across features (RG collapse) AND/OR a Quran-distinctive exponent vs. peer corpora?

---

## 2. Data — locked

**Source**: `results/checkpoints/phase_06_phi_m.pkl` (locked Phase-06 checkpoint with all 7 Arabic corpora; SHA-256 fingerprinted).

**Pool (per-corpus)**: filter to surahs / chapters with `n_verses ≥ 32` (so we have data at L = 16). Expected pool sizes:
- Quran: 56 surahs (those with ≥ 32 verses out of 114)
- poetry_jahili / poetry_islami / poetry_abbasi / hindawi / ksucca / arabic_bible: variable

**Locked alphabet**: 28 Arabic consonants (per F48 / F55 / F63 normaliser).

---

## 3. Protocol

For each corpus C and each surah/chapter `s` with `n_verses(s) ≥ 32`:
1. For scale L ∈ {1, 2, 4, 8, 16}:
   - Truncate `s` to the largest multiple of L: `n' = (n_verses // L) × L`
   - Group consecutive L verses into `n'/L` super-verses (concatenate text)
   - Compute 5 features on the super-verse list:
     - `EL_rate`: end-letter rate (fraction of super-verses ending in the corpus's top letter)
     - `VL_CV`: super-verse length coefficient of variation
     - `p_max`: top-frequency super-verse-final letter
     - `H_EL`: super-verse-final letter Shannon entropy (bits)
     - `H_cond`: not computed at scale L (root-level structure breaks down at super-verse aggregation; SKIP for this exp)
   - Store `(corpus, surah, L, EL_rate, VL_CV, p_max, H_EL)`

2. Per-corpus aggregation: at each L, compute the cross-surah median of each feature.
3. Per-feature scaling fit: regress `log(feature_median(L))` on `log(L)` for L ∈ {1, 2, 4, 8, 16} → slope α_feature.
4. Per-corpus universality test: compute `std({α_EL, α_VL, α_pmax, α_HEL})`. If std < 0.1 → universal collapse PASS.
5. Quran-distinctiveness test: for each feature, compute Quran's α minus peer corpora's α. Compute z-score using peer std.

**Deterministic**: no randomness; reproducible from locked pkl.

---

## 4. Decision rules (locked)

- PASS_universal_collapse (Form-1): per-corpus std of feature exponents < 0.1 AND cross-corpus mean exponent for at least 3 of 4 features matches within tolerance (z < 2 from cross-corpus mean).
- PASS_quran_distinctive_scaling (Form-2): Quran's per-feature exponent z vs peer-corpus exponents > 2.0 for at least 1 of 4 features.
- PASS_both: both Form-1 and Form-2 pass.
- FAIL_no_clean_signal: neither form passes.

---

## 5. Audit hooks

- A1: source pkl SHA-256 byte-match locked.
- A2: ≥ 30 surahs in Quran pool with ≥ 32 verses.
- A3: ≥ 5 peer corpora in pool with ≥ 5 chapters each at n_verses ≥ 32.
- A4: deterministic computation; rerun-determinism check.
- A5: at L = 1, super-verses are individual verses → features should match the canonical per-surah median values from `phase_06_phi_m.pkl`.

---

## 6. Receipt path

`results/experiments/exp116_RG_scaling_collapse/exp116_RG_scaling_collapse.json`

---

## 7. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H71 reserved in `HYPOTHESES_AND_TESTS.md`.
