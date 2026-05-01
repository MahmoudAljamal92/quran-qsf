# expP4_cross_tradition_profile — pre-registered prediction

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** the run.py
ever produced a multi-axis profile.

---

## 1. Background

Today's four cross-tradition experiments produced a per-corpus signal on three orthogonal axes:

| Axis | Source experiment | Description |
|---|---|---|
| **R3 z_path** | `expP4_cross_tradition_R3` | path-minimality of canonical ordering vs 5000 permutations on 5-D language-agnostic features (z-score within corpus) |
| **A2 R_primitives** | `expP4_diacritic_capacity_cross_tradition` | diacritic-channel capacity ratio H(d\|c) / log2(\|primitive marks\|) |
| **Hurst z (canon vs perm null)** | `expP4_quran_hurst_forensics` | R/S Hurst of unit-word-count canonical-order series vs 5000-permutation empirical null |

Each axis tells a different story: R3 indexes structural ordering optimality, A2 indexes orthographic-channel utilisation, Hurst indexes long-range temporal memory. **This experiment combines them into a single per-corpus 3-D profile vector and asks whether the 8 corpora occupy a coherent design space.**

## 2. Pre-registered predictions

> **PRED-PRO-1 (oral cluster)**: In the standardised 3-D profile space,
> the 4 oral-liturgical corpora (Quran, Pali_MN, Rigveda, Avestan) sit
> closer (smaller mean pairwise Euclidean distance) than they do to the
> 3 narrative-or-mixed corpora (Tanakh, NT, Iliad).
>
> **PRED-PRO-2 (Iliad outlier)**: The Iliad has the LARGEST mean
> distance to all other 7 corpora in the profile space. It is the
> single most-isolated corpus.
>
> **PRED-PRO-3 (Rigveda extremity)**: The Rigveda has the LONGEST
> Euclidean norm in the (positive-direction) standardised profile
> space — i.e. it is the corpus furthest from the centroid in the
> direction of "more path-minimal + more diacritic-saturated + more
> Hurst-extreme". This formalises the "Rigveda is #1 on every metric"
> intuition from earlier today.
>
> **PRED-PRO-4 (R3 dominates the design-space variance)**: R3 z_path
> is the highest-loading axis on the first PCA component of the 8×3
> profile matrix. I.e. R3 is the single best one-axis summary of the
> cross-tradition design space.

## 3. Falsifiers

- **F1**: The 4 oral-liturgical corpora do NOT have smaller mean
  inter-cluster distance than to the narrative-or-mixed corpora.
  Falsifies PRED-PRO-1.
- **F2**: The Iliad is NOT the most-isolated corpus (some other
  corpus has a larger mean-distance-to-all-others). Falsifies
  PRED-PRO-2.
- **F3**: The Rigveda is NOT in the corner of the design space
  furthest from the centroid in the positive direction.

## 4. Method (locked)

For each of the 8 corpora, gather the 3 axis values:

  - R3 z_path (already computed; lookup from
    `results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json`)
  - A2 R_primitives (look up; for Iliad we compute fresh via the
    Greek polytonic pair extractor, since Iliad shares the Greek
    script with NT; for Pali_DN we compute fresh via the Latin-
    IAST extractor, splitting from the previous DN+MN combined run)
  - Hurst z (lookup from `expP4_quran_hurst_forensics`; Iliad and
    Pali_DN have no unit-level Hurst due to n<10. For these, we
    use the verse-level Hurst as a substitute, computed with its
    own per-corpus permutation null. Use the 5000-perm seed = 42
    to match the forensics experiment.)

After collecting the 8×3 raw profile matrix, **z-score each column
across the 8 corpora** so the 3 axes are on the same scale. Sign
convention: more negative R3 z_path (more path-minimal) → MORE positive
profile_R3 (so that all three axes point in the same direction "more
canonical-religious-like"). Equivalently: profile_R3 = − R3_z_path.

Then compute:
  - 8×8 pairwise Euclidean distance matrix
  - Mean distance among the 4 oral-liturgical corpora vs mean distance
    between oral-liturgical and narrative-or-mixed
  - Each corpus's mean distance to all other 7 (isolation index)
  - Profile-norm of each corpus from the centroid (Mahalanobis-like,
    but since axes are z-scored just Euclidean from origin)
  - PCA on the 8×3 standardised matrix; report variance explained per
    component and the loading vector of PC1.

## 5. Reads / writes

- Reads only: locked JSON outputs of the four prior cross-tradition
  experiments + `data/corpora/{el,pi}/...` for the two missing values.
- Writes only under `results/experiments/expP4_cross_tradition_profile/`.

## 6. Recovery / supersession

This experiment **synthesises** the four prior cross-tradition
experiments. It does not produce new primary measurements except for
two specific gap-fills (Iliad A2, Pali_DN A2), which must reproduce
the existing pair-extractor algorithms byte-for-byte.
