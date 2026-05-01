# expP4_hurst_universal_cross_tradition — pre-registered prediction

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** the run.py
ever produced a Hurst value for any non-Rigveda cross-tradition corpus.

---

## 1. Background

Today's earlier experiments established:

- **`expP4_cross_tradition_R3`**: oral-liturgical canonical orderings are
  path-minimal. Quran (z=−8.92), Pali_MN (−3.47), Rigveda (−18.93) pass;
  Iliad fails as preregistered control.
- **`expP4_rigveda_deepdive`**: the Rigveda Saṃhitā shows
  R/S Hurst H = 0.786 on its canonical-order sūkta-word-count
  series — **higher** than the locked Quran R/S Hurst (Supp_A_Hurst =
  0.7381, ULTIMATE_SCORECARD).

This raises the natural cross-tradition question: **is high R/S Hurst
(H > 0.6) a property of every oral-liturgical canonical ordering, or is
it Rigveda-and-Quran-specific?**

## 2. Pre-registered predictions

> **PRED-HU-1 (universal long-range memory)**: All four oral-liturgical
> corpora (Quran, Pali_MN, Rigveda, Avestan_Yasna) yield R/S Hurst H > 0.6
> on at least one canonical-order time-series (verse word-count, unit
> word-count, or unit EL-rate). Pali_DN may not qualify because its
> unit count (34) is too small for reliable Hurst, and may be reported
> as NaN.
>
> **PRED-HU-2 (negative control)**: The Iliad's canonical book ordering
> shows H ≤ 0.55 on the verse word-count series (i.e. consistent with
> a random-walk null at the verse-level), since the Iliad's overall
> corpus structure is narrative-chronological rather than mnemonic.
>
> **PRED-HU-3 (cross-tradition floor)**: At least 3 of the 4 oral-
> liturgical corpora exceed the locked Quran R/S Hurst (0.7381). The
> Quran would be the FLOOR of the cross-tradition Hurst distribution,
> not the ceiling.

## 3. Falsifiers

- **F1**: ≥ 2 of {Pali_MN, Rigveda, Avestan_Yasna} yield H ≤ 0.55. Falsifies
  PRED-HU-1; Hurst long-range-memory is not a cross-tradition universal.
- **F2**: Iliad H > 0.7 on the verse word-count series. Falsifies PRED-HU-2;
  the negative control no longer separates cleanly. Reading: H is a
  *language* property, not a *tradition* property.
- **F3**: All cross-tradition Hurst values are below 0.6. The Rigveda
  result was an artefact and the cross-tradition Hurst extension fails
  outright.

## 4. Method (locked)

For each corpus C in {Quran, Tanakh, GreekNT, Iliad, Pali_DN, Pali_MN,
Rigveda, Avestan_Yasna}, with units in their canonical order, compute
three R/S Hurst values via `src/extended_tests4.py:_hurst_rs`:

  1. **H_verse_words**: verse-word-count sequence over all verses of C
     in canonical order (verses-within-units, units-in-canonical-order).
  2. **H_unit_words**: unit-word-count sequence (length = number of units).
  3. **H_unit_EL**: unit EL-rate sequence (length = number of units).

`_hurst_rs` returns NaN for sequences too short (need at least 2 chunk
sizes from {8, 12, 16, 24, 32, 48, 64, 96} with ≥4 windows each). Pali_DN
(34 units) and Avestan (69 units) may produce NaN on H_unit_words /
H_unit_EL but should produce valid H_verse_words.

Sanity check: the locked Quran R/S Hurst from `Supp_A_Hurst` (0.7381)
must be reproduced by H_verse_words on the Quran corpus to within ±0.05.
(Allowance for the Hurst algorithm difference: locked may use a different
window grid or detrending. We report drift but do not gate on exact match.)

## 5. Reads / writes

- Reads only: all corpora via `raw_loader.load_all(include_extras=True,
  include_cross_lang=True, include_cross_tradition=True)`.
- Writes only under `results/experiments/expP4_hurst_universal_cross_tradition/`.

## 6. Recovery / supersession

This experiment **extends** `expP4_rigveda_deepdive` to the full 8-corpus
universe. The Rigveda's three locked H values (H_verse_words = 0.7332,
H_unit_words = 0.7861, H_unit_EL = 0.5958) must reproduce exactly.
