# expX1_psi_oral — Pre-Registration

**Date**: 2026-04-25
**Status**: PRE-REGISTERED, code frozen at this commit before any cross-corpus number is consulted.

## Hypothesis

The reviewer's **Ψ_oral universal** (proposed 2026-04-25, derived from project-locked scalars) is:

> Ψ_oral(corpus) := H(diac | base) / (2 · I(EL ; CN))

where
- **H(diac | base)** is the conditional Shannon entropy (in bits) of script-specific diacritic / vowel-mark code points given their base character, computed across the full corpus text after NFD normalisation.
- **I(EL ; CN)** is the discrete plug-in mutual information (in bits) between end-letter rhyme rate (EL) and discourse-connective rate (CN), computed per-unit with each variable binned into 10 quantile bins.

For the Quran (locked):
- `H(harakat|rasm) = 1.964 bits` (`extended_tests2.py::test_harakat_channel_capacity`, T7 corpus-level, results_lock).
- `I(EL;CN) = 1.175 bits` (`extended_tests.py::test_el_cn_dual_channel`, Band-A only).
- ⇒ `Ψ_oral(quran) = 1.964 / (2 · 1.175) = 0.83574`.

The reviewer's working hypothesis is that this value is a **universal constant of oral-transmission texts**, near `5/6 ≈ 0.8333`, and that all oral-liturgical corpora (Pali, Vedic, Avestan, plus the Abrahamic reference corpora) should converge near this value while narrative-non-mnemonic corpora (Iliad) should not.

## Pre-registered predictions

Each prediction is binary PASS / FAIL.

### PSI-S1 (sanity gate; must pass for the experiment to be valid)
The reproduction of `Ψ_oral(quran)` from this script's measurements drifts from the locked value `0.83574` by less than `5 · 10⁻³` absolute.

### PSI-1 (loose oral cluster)
At least 3 of the 5 non-Quran oral-liturgical corpora `{hebrew_tanakh, greek_nt, pali_mn, rigveda, avestan_yasna}` yield Ψ_oral in the band `[0.65, 1.00]`.

(Hebrew and Greek NT are labelled "narrative_or_mixed" in expP4_cross_tradition_R3, but they passed LC2 as oral-liturgical; we test them here under the same conservative grouping. Pali_dn excluded for n_units < 36; Iliad is the negative control.)

### PSI-2 (tight 5/6-universal)
At least 3 of those 5 corpora yield Ψ_oral within `±0.06` of `5/6 ≈ 0.8333` — i.e. in `[0.7733, 0.8933]`.

### PSI-3 (negative control)
Iliad's Ψ_oral lies **outside** the tight band `[0.7733, 0.8933]`. Equivalently: |Ψ_oral(iliad) − 5/6| > 0.06.

### Verdict mapping
- `SUPPORT_TIGHT` — PSI-S1 + PSI-2 + PSI-3 all PASS.
- `SUPPORT_LOOSE` — PSI-S1 + PSI-1 PASS (regardless of PSI-2 / PSI-3).
- `NO_SUPPORT` — PSI-S1 PASS but neither PSI-1 nor PSI-2 PASS.
- `INVALID` — PSI-S1 FAIL (sanity broken; do not interpret).

## Method (frozen)

1. **Corpora**: 8-corpus universe of `expP4_cross_tradition_R3`.
   - quran (Arabic), hebrew_tanakh, greek_nt, iliad_greek, pali_dn, pali_mn, rigveda, avestan_yasna.
2. **H(diac | base)**: NFD-normalised concatenation of all unit verses; iterate code points; a *base* is any non-combining non-space character; a *diacritic* is any code point with `unicodedata.category(c) ∈ {"Mn", "Mc"}` (Mn = non-spacing mark, Mc = spacing combining mark — needed for Devanagari mātrās). Pairs `(base, "".join(diacritics_following))` are tallied; conditional entropy is `Σ_b p(b) · H(diacs | base=b)`.
3. **I(EL ; CN)**: per-unit (`u.verses` from `raw_loader`) computation of EL via `el_rate(u.verses)` and CN via `cn_rate(u.verses, stops)`; stops are `ARABIC_CONN` for Quran and `derive_stopwords(verses, top_n=20)` otherwise (matching expP4_cross_tradition_R3). Each variable is digitised into 10 quantile bins on the corpus's empirical quantiles. MI is the discrete plug-in estimator `Σ p(x,y) log₂(p(x,y)/(p(x)p(y)))`.
4. **Filtering**: Band-A definition `15 ≤ verse_count ≤ 100` is applied **only when computing I(EL;CN) for Quran** (to reproduce the locked 0.8357 sanity). For all other corpora, all units enter I(EL;CN). H(diac|base) is computed on the full text in every corpus.
5. **Outputs**: `results/experiments/expX1_psi_oral/expX1_psi_oral.json` with per-corpus `H_diac_given_base`, `I_EL_CN`, `psi_oral`, `n_units`, `n_units_band_a`, `n_diac_pairs`, `pred_*`, and `verdict`.

## Falsifiers

- The Quran reproduction may fail PSI-S1 if (a) the corpus loader's verse text differs from `quran_vocal.txt`, or (b) the Band-A filter applied to I(EL;CN) does not reproduce the T7 numerator. In that event the entire experiment is `INVALID` and the formula stays in pre-reg pending a code fix.
- The cross-corpus claim is falsified by `NO_SUPPORT`.

## Frozen 2026-04-25, expX1_psi_oral.

No corpus number is consulted before this PREREG.md is committed. All gates above are written from the locked Quran value alone.
