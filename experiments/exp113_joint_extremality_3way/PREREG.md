# PREREG — exp113_joint_extremality_3way: 3-way joint extremality test (F55_gap × F63_p_max × LC2_z)

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H68.
**Author intent**: test whether the Quran is **jointly extremal** on three independent structural axes — F55 bigram-uniqueness, F63 rhyme-extremum, and LC2 path-minimality — and quantify the joint extremality probability under a permutation null where the three axes are treated as independent. This produces the **single missing scatter figure** that determines whether the project's three positive findings are independent (multiplicative joint p) or correlated (one effective axis).

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **The three axes measure DIFFERENT statistics**:
   - F55 bigram-shift safety margin (per-character normalised) — measures within-tradition canon-vs-peer bigram distinctness
   - F63 median p_max (verse-final-letter top frequency) — measures rhyme concentration on positional channel
   - LC2 path-minimality z-score — measures canonical-ordering structural optimality
   They are mathematically distinct; correlation is an empirical question, not a theoretical one.

2. **Quran is already known to be top-1 on each axis individually** (F48/F55, F63, LC2 R3). The new question is the JOINT statistic: under the null hypothesis that the three rankings are independently shuffled, what is the probability that a single tradition wins on all three?

3. **The traditions in scope**: 5 cross-tradition canons where all three metrics have been measured: {Quran, Hebrew Tanakh, Greek NT, Pāli, Avestan}. Rigveda has F63 + LC2 but no F55 (different writing system at line-level); Daodejing has F55 + LC2 not yet computed but no F63 p_max yet.

4. **Pre-registered outcome**: 
   - PASS_quran_jointly_extremal_perm: Quran is top-1 on all 3 axes AND permutation-null p < 0.05
   - FAIL_not_top1_on_all_axes: Quran is NOT top-1 on at least one axis
   - FAIL_perm_p_above_threshold: Quran is top-1 but the joint pattern is consistent with chance under independent shuffles

5. **What this test does NOT do**:
   - Does not establish causality between the three axes
   - Does not test whether Quran's joint extremity is "expected under any specific theory"
   - Does not falsify F55 / F63 / LC2 individually (they are independent locked findings)

---

## 1. Question

Under independent permutation of corpus labels on each of three structural axes (F55_gap, F63_p_max, LC2_z), what is the empirical probability that any single corpus achieves rank 1 on all three? Is the Quran's joint top-1 extremality consistent with independent multiplicative null at p < 0.05?

---

## 2. Data — locked

**Source receipts (byte-locked SHA-256 in `frozen_constants`)**:
- F55_gap: `results/experiments/exp95j_bigram_shift_universal/exp95j_bigram_shift_universal.json` (Quran), `exp105_F55_psalm78_bigram/.json` (Hebrew), `exp106_F55_mark1_bigram/.json` (Greek), `exp107_F55_dn1_bigram/.json` (Pāli), `exp108_F55_y28_bigram/.json` (Avestan)
- F63_p_max: `results/auxiliary/_phi_universal_xtrad_sizing.json` (medians per corpus)
- LC2_z: `results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json` (per-corpus z)

**Traditions (locked)**: Quran, Hebrew Tanakh, Greek NT, Pāli, Avestan. n = 5.

**Metrics (locked formulas)**:
- F55_safety_per_char = (min_peer_delta − τ) / n_canon_letters; τ = 2.0
  - For Quran (multi-surah): use median across 114 surahs of `min_peer_delta / n_canon` then subtract τ/median(n_canon)
- F63_p_max = median per-unit p_max of verse-final letters
- LC2_z = path-minimality z-score from expP4_cross_tradition_R3

---

## 3. Protocol

1. Load receipts; extract scalars per tradition.
2. Rank traditions on each axis (lower z is better for LC2; higher is better for F55_safety and F63_p_max).
3. Check if Quran is rank 1 on all three axes (joint argmax).
4. Compute pairwise Spearman correlations across the 5 traditions.
5. **Permutation null**: independently shuffle the rank labels on each axis 10,000 times (seed = 42). For each shuffle, count whether any single tradition lands at rank 1 on all three axes simultaneously. Empirical perm_p = (count where ANY tradition is jointly rank-1) / 10,000.
6. Also compute perm_p_quran = (count where the Quran-position lands rank-1 on all three) / 10,000 — this is the more focused null.

---

## 4. Decision rule (locked)

- PASS: Quran is rank 1 on all three observed axes AND perm_p_quran < 0.05.
- FAIL_not_top1: Quran fails rank 1 on any axis.
- FAIL_perm_p: Quran is rank 1 but perm_p_quran ≥ 0.05.

---

## 5. Audit hooks

- A1: source receipts SHA-256 byte-match locked values.
- A2: 5 traditions present with all 3 metrics non-NaN.
- A3: ranks computed deterministically (ties: stable sort by tradition name alphabetical).
- A4: permutation seed = 42, n_perms = 10,000.
- A5: rerun-determinism check (same seed → same perm_p, byte-identical).

---

## 6. Receipt path

`results/experiments/exp113_joint_extremality_3way/exp113_joint_extremality_3way.json`

---

## 7. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H68 reserved in `HYPOTHESES_AND_TESTS.md`.
