# expP4_cross_tradition_R3 — pre-registered prediction document

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** the run.py
ever produced an output for the three new corpora. Subsequent edits to this
PREREG.md must be visible in `git diff` against the pre-bless commit.

---

## 1. Hypothesis (LC2 universal-extension)

The locked finding `R3` (path-cost minimality of canonical chapter ordering)
already shows for the four exp35 corpora:

| Corpus | n_units | exp35 z_path |
|---|---|---|
| Quran | 114 surahs | strongly negative (≪ 0) |
| Hebrew Tanakh | book-chapters | not strongly negative |
| Greek NT | book-chapters | not strongly negative |
| Iliad | 24 books | not strongly negative |

The interpretation in `docs/PAPER.md` §4.16 is **LC2: oral-liturgical
canonical orderings are path-minimal under the 5-D language-agnostic
feature space; epic narrative orderings are not**. The Quran is one
member of the oral-liturgical class.

This experiment **operationalises LC2** by adding three new oral-liturgical
corpora:

- **Pāli Tipiṭaka** (Dīgha + Majjhima Nikāyas, n = 186 suttas) — the
  paradigmatic oral-mnemonic Indic Buddhist corpus.
- **Rigveda Saṃhitā** (10 maṇḍalas, n = 1024 sūktas) — the paradigmatic
  oral-Vedic corpus, transmitted with extreme phonetic fidelity for ≥ 3000 y.
- **Avestan Yasna** (n = 69 chapters) — the paradigmatic Old Iranian
  oral-liturgical corpus.

## 2. Pre-registered prediction (LC2)

Under LC2, every oral-liturgical corpus's canonical order should be
significantly path-minimal in its own 5-D feature space (within-corpus
z-score, 5000 random-permutation null, seed = 42). Specifically:

> **PRED-LC2.1**: ≥ 2 of 3 new oral-liturgical corpora (Pali_DN,
> Pali_MN, Rigveda, Avestan_Yasna) yield z_path < −2 with empirical
> p_one_sided < 0.025, replicating the Quran's negative-z pattern.
>
> **PRED-LC2.2**: When BH-pooled across all 8 corpora (Quran + Tanakh
> + GreekNT + Iliad + Pali_DN + Pali_MN + Rigveda + Avestan), the
> minimum BH-adjusted p ≤ 0.05.
>
> **PRED-LC2.3 (negative control)**: Iliad remains non-significant
> (BH p > 0.05). This is the *narrative-non-mnemonic* corpus and
> should not optimise under LC2.

## 3. Falsifiers

Any of:

- **F1**: ≥ 2 of the 3 new corpora yield z_path > 0 (canonical longer
  than random). Falsifies LC2 outright; the universal claim collapses.
- **F2**: All 3 new corpora yield |z_path| < 1.0. Insufficient signal;
  LC2 is unsupported.
- **F3**: Pāli + Rigveda + Avestan all yield significant POSITIVE z
  (canonical longer than random). LC2 is not just unsupported but
  *anti-supported*.

## 4. Method (locked)

Identical to `exp35_R3_cross_scripture_redo` but extended to the 8-corpus
universe.

- **Features**: 5-D `features_lang_agnostic` = (EL, VL_CV, CN,
  H_cond_initials, T_lang). Within-corpus z-score before path-cost.
- **Stopwords**: Quran uses `ARABIC_CONN` (paper §2.2). Every other
  corpus uses `derive_stopwords(verses, top_n=20)`.
- **Path metric**: Euclidean sum of adjacent-unit distances on the
  z-scored 5-D matrix.
- **Null**: 5000 RNG-shuffled orders per corpus, seed = 42.
- **Statistics**: `z = (canon_cost − perm_mean) / perm_std`, empirical
  one-sided p = `(perm_costs < canon_cost).mean()`, conservative floor
  `1 / (N_PERM + 1)`.
- **Pooling**: Benjamini–Hochberg one-sided across the 8 tests.

## 5. Reads / writes

- Reads only: `data/corpora/{ar,he,el,pi,sa,ae}/...` via `raw_loader`.
- Writes only under `results/experiments/expP4_cross_tradition_R3/`.

## 6. Recovery / supersession

This experiment **extends** `exp35_R3_cross_scripture_redo`. It does not
supersede it; the exp35 numbers remain locked. The 4-corpus subset of this
8-corpus run must agree with exp35's locked z values to within numerical
precision (sanity check; passes ⟺ stopword pipeline + z-score + RNG seed
all reproduce).
