# expP4_diacritic_capacity_cross_tradition — Result summary

**Run:** 2026-04-25, ~5 s compute (no permutation null; closed-form information-theory).
**Self-check:** OK (17 protected files unchanged during run).
**Sanity check:** the 3-Abrahamic subset reproduces locked `expA2` R values to **0.0e+00 numerical drift**.

## Per-corpus result

| Corpus | n_pairs | \|base\| | \|combo\| | \|prim\| | H(d\|c) bits | R_combo | R_prim |
|---|---:|---:|---:|---:|---:|---:|---:|
| quran_arabic | 320 543 | 36 | 60 | 25 | 2.175 | 0.368 | 0.468 |
| tanakh_hebrew | 1 261 611 | 27 | 111 | 15 | 2.714 | 0.400 | **0.695** |
| nt_greek | 362 642 | 7 | 24 | 8 | 2.088 | 0.455 | **0.696** |
| **rigveda_devanagari** | 512 219 | 45 | 79 | 17 | **3.753** | **0.595** | **0.918** |
| **pali_iast** | 2 807 810 | 21 | 5 | 5 | 0.467 | 0.201 | 0.201 |
| **avestan_geldner** | 148 051 | 25 | 6 | 6 | 0.539 | 0.208 | 0.208 |

## Pre-registered prediction outcomes

| Prediction | Combinations | Primitives |
|---|---|---|
| **PRED-A2-EXT-1** ≥ 1 of 3 new corpora R ∈ [0.55, 0.75] | **PASS** (Vedic 0.595) | **FAIL** (Vedic 0.918 above; Pali/Avestan 0.20 below) |
| **PRED-A2-EXT-2** 6-corpus spread ≤ 0.30 | FAIL (0.394) | FAIL (0.717) |
| **PRED-A2-EXT-3** Vedic R_prim is lowest or 2nd-lowest | — | **FAIL** (Vedic is **highest**; rank 5 of 6 from low) |
| **Overall verdict** | — | **NO_SUPPORT** for universal R ≈ 0.70 |

## Reading the result

**The locked `expA2` "R ≈ 0.70 Abrahamic-orthographic-constant" hypothesis is falsified at the cross-tradition scope.** The 6 corpora split into three regimes:

1. **Abrahamic phonological diacritics** (Hebrew, Greek): R_prim ≈ 0.69–0.70. Tight cluster.
2. **Devanagari Vedic** (own script, mātrās + svaras + nukta): R_prim = **0.918**. Near-saturated. The mātrā × svara × visarga lattice is used very nearly uniformly given the consonant.
3. **Latin transliterations** of Pali (IAST) and Avestan (Geldner): R_prim ≈ 0.20. Sparse: only 5–6 distinct combining marks across millions of pairs, dominated by the `<none>` no-diacritic case.

The Quran sits at R_prim = 0.47, intermediate between Hebrew/Greek and the Latin-transliteration corpora.

Two new findings emerged:

### 1. Vedic Devanagari is *near-saturated* (R_prim = 0.918)

Devanagari encodes vowel-quality (mātrās), nasalisation (anusvāra), aspiration (visarga), nukta, and **prosodic pitch** (Vedic accents udātta U+0951, anudātta U+0952, svarita U+0953, dīrgha-svarita U+0954) all as combining marks attaching to the consonant. The conditional entropy H(d|c) = 3.75 bits is the highest of any corpus tested, against log2(17) ≈ 4.09 bits of theoretical capacity. The Rigveda Saṃhitā uses **91.8 %** of its diacritic-channel's information capacity — far more than any Abrahamic script.

Combined with the locked R3 result (`expP4_cross_tradition_R3` Rigveda z = −18.93, the strongest path-minimality of any corpus), this makes the Rigveda the **most extreme oral-mnemonic-coding signal** in our entire corpus universe.

### 2. The Latin-transliteration regime is artefactual

Pali_iast (R_prim = 0.20) and avestan_geldner (R_prim = 0.21) both show very low diacritic capacity, but this is an **orthographic-choice artefact** of Latin transliteration, not a property of the source phonology. The IAST scheme uses ≤ 5 distinct combining marks (macron, dot-above, dot-below, tilde, ring) regardless of how rich the phonology is. The Geldner Avestan transliteration adds caron and circumflex but is similarly sparse.

A fairer comparison would test Pali in its native Brahmi-derived script (e.g. Sinhala or Burmese akṣara) and Avestan in its native script (37 consonants + 16 vowel signs, fully precomposed). In both, the diacritic channel is far richer. **This is a known limitation that the cross-tradition test cannot currently address** — the available digital editions are the Latin transliterations, not the native scripts.

## Honest interpretation for the manuscript

The pre-registered universal-band R ≈ 0.70 hypothesis was **falsified** the moment we measured the Vedic Devanagari result (R_prim = 0.918). Even allowing for the Latin-transliteration confound, the spread across the *original-script* subset (Arabic, Hebrew, Greek, Devanagari) is

> R_prim ∈ {0.468, 0.695, 0.696, 0.918}, spread = 0.450.

This is too wide to call a constant. The Hebrew + Greek cluster at 0.70 looks like a regional convergence (Levantine + Aegean phonological-diacritic systems) rather than a script-universal.

**The honest takeaway**: diacritic-channel capacity is **not** an orthographic universal. It's a script-and-tradition-specific design choice. This refines (and partly retracts) the speculation in the locked A2 report.

## Files

- `PREREG.md` — pre-registered hypothesis + falsifiers (authored 2026-04-25 before any compute)
- `run.py` — experiment driver (deterministic, closed-form, ~5 s)
- `SUMMARY.md` — this file
- `../../results/experiments/expP4_diacritic_capacity_cross_tradition/expP4_diacritic_capacity_cross_tradition.json` — full results
- `../../results/experiments/expP4_diacritic_capacity_cross_tradition/self_check_*.json` — integrity log
