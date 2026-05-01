# expP4_diacritic_capacity_cross_tradition — pre-registered prediction

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** the run.py
ever produced a number for the three new corpora.

---

## 1. Background

The locked `expA2_diacritic_capacity_universal` measured the diacritic-channel
capacity ratio

> R = H(diacritic | base letter) / log2(|diacritic alphabet|)

for the three Abrahamic-script religious corpora (Quran, Hebrew Tanakh, Greek
NT). Its locked headline (under the **primitives** denominator convention,
which counts each combining mark independently) is:

| Corpus | R_primitives |
|---|---:|
| Quran (Arabic) | 0.4683 |
| Tanakh (Hebrew) | 0.6947 |
| NT (Greek) | 0.6959 |

Hebrew and Greek both land near 0.70; Arabic is the outlier. The pre-registered
"narrow band [0.55, 0.75], max spread ≤ 0.10" verdict was **PARTIAL_2_OF_3**
under primitives, **NARROW_AGREEMENT_OUTSIDE_PREREG_BAND** under combinations.

The **R ≈ 0.70** value (the cluster point of the two non-Arabic corpora)
is the candidate "Abrahamic orthographic constant" that motivates this
follow-up. We now extend to three pre/non-Abrahamic religious orthographies:

- **Devanagari Rigveda Saṃhitā** — Indic abugida, vowel-signs (mātrās) +
  Vedic accents (udātta U+0951, anudātta U+0952, svarita U+0953, dīrgha-
  svarita U+0954) all attach as combining marks. The original "tight oral-
  mnemonic" test case for cross-tradition extension.
- **Latin-IAST Pāli Tipiṭaka** — Latin alphabet with combining macrons
  (ā ī ū), tilde (ñ), dot-below (ṭ ḍ ḷ ṇ), dot-above (ṅ ṃ). After NFD
  decomposition these are pure base+combining pairs.
- **Latin-Geldner Avestan Yasna** — Latin alphabet with circumflex (â ê î
  ô û), caron (ǎ š ž), macron (ē ō), tilde (ñ), plus the precomposed letters
  ə (schwa) and ŋ (eng) which NFD does not decompose (these are SEPARATE
  base letters, not diacritic-modified).

## 2. Pre-registered predictions

> **PRED-A2-EXT-1 (universal-band membership)**: At least one of
> {Devanagari Vedic, Latin-IAST Pāli, Latin-Geldner Avestan} lands inside
> the [0.55, 0.75] band under the primitives convention, joining Hebrew
> and Greek near R ≈ 0.70.
>
> **PRED-A2-EXT-2 (cross-script clustering)**: The 6-corpus spread under
> primitives is ≤ 0.30. Even allowing the Arabic outlier and the new
> outliers, all 6 R values cluster within 30 percentage points.
>
> **PRED-A2-EXT-3 (Vedic accent prediction)**: Vedic Devanagari with
> svaras has more "diacritic" types than any other corpus (mātrās +
> svaras + visarga + anusvāra), so its primitives R is expected to be
> the LOWEST or near-lowest of the 6. The combinations R may be higher
> because attested mātrā+svara strings are far fewer than the cartesian
> product would allow.

## 3. Falsifiers

- **F1**: All 3 new R_primitives > 0.85. Indicates the Indic / Iranian
  scripts use FAR more of their diacritic channel than the Abrahamic
  scripts — anti-supports the universality claim.
- **F2**: All 3 new R_primitives < 0.30. Indicates the new scripts use
  vastly less of their channel — also anti-supports.
- **F3**: The 6-corpus spread > 0.50. The "cluster near 0.70" claim is
  effectively dead.

## 4. Method (locked)

- Pair extraction: walk the joined verse-text character-by-character;
  on hitting a base letter, gather all subsequent combining marks until
  the next non-mark; record the (base, "".join(marks) or "<none>") pair.
- For Latin scripts (Pāli, Avestan), NFD-decompose the text first so
  precomposed letters split into base + combining mark.
- Reuse the entropy helpers from `expA2_diacritic_capacity_universal`
  byte-for-byte:
  - `H(d|c) = sum_c p(c) H(d|c=c)`
  - `H_max_combinations = log2(|distinct combination strings observed|)`
  - `H_max_primitives   = log2(|distinct primitive marks observed|)`
  - `R_combinations = H(d|c) / H_max_combinations`
  - `R_primitives   = H(d|c) / H_max_primitives`
- Sanity check: the 3 Abrahamic corpora MUST reproduce the locked A2
  numbers to within 1e-6.

## 5. Reads / writes

- Reads only:
  - `data/corpora/ar/quran_vocal.txt` (Quran Hafs vocalised)
  - `data/corpora/he/tanakh_wlc.txt` (WLC Hebrew Tanakh)
  - `data/corpora/el/opengnt_v3_3.csv` (OpenGNT Greek NT)
  - `data/corpora/sa/rigveda_mandala_*.json` (Rigveda Saṃhitā, via loader)
  - `data/corpora/pi/{dn,mn}/*_root-pli-ms.json` (Pāli, via loader)
  - `data/corpora/ae/y*.htm` (Avestan Yasna, via loader)
- Writes only under `results/experiments/expP4_diacritic_capacity_cross_tradition/`.

## 6. Recovery / supersession

This experiment **extends** `expA2_diacritic_capacity_universal`. It does not
supersede it; the locked 3-corpus A2 numbers remain the reference, and this
experiment must reproduce them. The new value-add is the 3-corpus extension
to non-Abrahamic religious orthographies.
