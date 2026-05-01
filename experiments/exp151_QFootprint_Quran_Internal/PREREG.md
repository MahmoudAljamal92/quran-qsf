# Pre-Registration — exp151 — Q-Footprint Quran-Internal (sūrah-pool resolution)

**Status**: PRE-REGISTERED V3.15.2 final-pinnacle batch (sub-experiment 3 of 3)
**Author**: project leader (Cascade-assisted)
**Pre-reg date**: 2026-04-29 night

## 1. Background and motivation

V3.15.1's `exp138` and V3.15.2's `exp141` operationalize the Q-Footprint at the **cross-corpus** level: each corpus is one row in a 12×8 (or 7×8 / 6×8) feature matrix. This experiment shifts the resolution **inside the Quran**: each of the 114 sūrahs becomes one row, and we ask "which sūrah is at the joint extremum of the Quran's own internal feature distribution?" This is the **local** counterpart of the cross-tradition pinnacle.

Pre-registered scientific question: under the same 8 universal feature axes (verse-final-letter Shannon entropy, p_max, alphabet-corrected Δ, verse-length CV, skeleton bigram diversity, gzip efficiency), which sūrah deviates most strongly from the Quran's own sūrah-mean centroid in joint 8-D feature space? The Mahalanobis distance from the centroid is the joint-extremum metric.

This question matters because:
1. If the joint-extremum sūrah is short-Meccan (al-Fātiḥah / al-Falaq / al-Nāṣ class), the 12.149σ cross-tradition extremum may be driven by these few sūrahs.
2. If the joint-extremum is mid-length-Medinan, the structural property is distributed across the whole Quran.
3. If multiple sūrahs share extremum status across both Meccan and Medinan periods, the joint signature is a **chronological invariant** of the Quran.

## 2. Hypothesis

**H95-Quran-Internal** (pre-registered): The Quran's joint Q-Footprint at the sūrah-pool resolution exhibits:
1. A clear top-1 sūrah by joint Mahalanobis distance from the 114-sūrah centroid (gap ≥ 1.5× to top-2)
2. Top-3 sūrahs span both Meccan and Medinan chronological periods (no chronological monopoly)
3. Top-1 sūrah is bootstrap-stable (rank-1 in ≥ 80% of 1000 sūrah-bootstraps)

## 3. The 8 axes at the sūrah level

Each sūrah is treated as a single "unit" with the following sūrah-level features:
1. `H_EL_surah`: Shannon entropy of verse-final letters within the sūrah
2. `p_max_surah`: most-frequent verse-final letter probability
3. `Delta_max_surah` = log₂(28) − H_EL_surah (alphabet-corrected redundancy)
4. `VL_CV_surah`: verse-length coefficient of variation in WORDS
5. `bigram_distinct_surah`: distinct-bigram ratio over the sūrah's skeleton
6. `gzip_eff_surah`: gzip-efficiency of the sūrah's skeleton
7. `n_verses_surah`: number of verses (size axis)
8. `mean_verse_words_surah`: mean verse length in words

These are sūrah-level analogs of the cross-corpus axes. Standardization uses 114-sūrah mean/std per axis.

## 4. Sub-tasks

**Sub-task A — Per-sūrah feature extraction**: Compute the 8-axis raw feature vector for each of the 114 sūrahs. Report sūrah-level descriptive statistics (median/p5/p95 per axis).

**Sub-task B — Sūrah-internal Hotelling T²**: Standardize each axis across all 114 sūrahs, compute Mahalanobis distance from the 114-sūrah centroid (Hotelling T²) for each sūrah using the 114-sūrah covariance matrix. Identify the top-10 sūrahs by T².

**Sub-task C — Joint Stouffer Z (sign-free)**: For each sūrah, compute the Stouffer-style joint statistic √Σ z² (= Mahalanobis distance for orthogonal axes) across the 8 axes. Identify the top-10 sūrahs by joint |Z|.

**Sub-task D — Chronological cross-tabulation**: Cross-reference the top-10 sūrahs with the Nöldeke-Schwally chronological classification (Meccan I/II/III/Medinan). Report the period distribution of the top-10.

**Sub-task E — Bootstrap stability**: Bootstrap-resample the 114 sūrahs (with replacement) 1000 times. For each resample, recompute joint T² per sūrah, find the top-1 sūrah. Report the top-1 sūrah's bootstrap rank-1 frequency.

## 5. Acceptance criteria

A1: A clear top-1 sūrah identified by joint Hotelling T² with gap ≥ 1.5× the top-2 T².  
A2: Top-3 sūrahs span both Meccan and Medinan periods (or at least 2 distinct Nöldeke periods).  
A3: Bootstrap rank-1 frequency of the point-estimate top-1 sūrah is ≥ 80%.  
A4 (descriptive): Report which axis has the highest Quran-internal CV (= where sūrahs differ most). Expected: H_EL_surah or Delta_max_surah (the rhyme-density axis varies most across sūrahs).  
A5 (descriptive): Identify whether the top-1 sūrah is short (n_verses ≤ 30), medium (31-100), or long (>100). All three classes are valid; this is descriptive only.

Verdict ladder:
- A1 + A2 + A3 PASS → `PASS_quran_internal_extremum_identified` → promote as O7 (descriptive observation)
- 2 of 3 PASS → `PARTIAL_quran_internal_directional`
- ≤ 1 PASS → `FAIL_quran_internal_indeterminate`

## 6. Audit hooks

- `prereg_hash` SHA256 of this file written into receipt.
- `frozen_constants`: AXES list, N_BOOTSTRAP=1000, SEED=42.
- `audit_report`: SHA256 of the 114×8 raw feature matrix; cross-check that the median sūrah H_EL matches F79's locked Quran value of 3.838834 within 0.001 (= same per-unit metric F79 uses).

## 7. Honest scope

This experiment is **descriptive/exploratory** at the local level. It does NOT test a Quran-vs-other-corpus claim. The sūrah-pool extremum identifies which sūrah is most "Quran-like-Quran" in the joint 8-D space. The result is an O-row observation, not an F-row finding (no cross-corpus null structure). Bootstrap stability is the closest thing to a hypothesis test, and ≥ 80% rank-1 frequency is the floor for "robust descriptive identification".

A FAIL outcome (e.g., top-1 sūrah varies wildly under bootstrap) would mean the sūrah-pool centroid is itself unstable, which would be substantively informative: it would suggest the Quran's per-sūrah feature distribution is multi-modal (no clean joint-extremum sūrah).
