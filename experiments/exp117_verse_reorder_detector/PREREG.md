# PREREG — exp117_verse_reorder_detector: sequence-aware verse-reorder forgery detector

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H72.

---

## 0. The gap this addresses

F55 (`exp95j`) detects single-letter and multi-letter symbolic substitutions with recall = 1 / FPR = 0 on per-verse bigram histograms. **But F55 cannot detect verse REORDERING within a sura**: if you swap verses V_i and V_j in a sura, the per-sura bigram histogram is unchanged (bigrams within each verse are preserved; word-internal bigrams are commutative across verse boundaries). This is a real protocol gap.

This experiment closes the gap with a **sequence-aware** statistic.

---

## 1. The detector — Markov transition matrix on verse-final letters

For a sura with N verses, let `e_1, e_2, ..., e_N` be the verse-final consonant letters (after Arabic 28-letter normaliser). Define the transition matrix:

```
T_ij(sura) = #{k : e_k = letter_i AND e_{k+1} = letter_j} / (N − 1)
```

This is a 28×28 stochastic-row matrix. **Verse-reordering changes T_ij directly**: swapping verses V_p and V_q changes the transitions (e_{p−1} → e_p) and (e_p → e_{p+1}) and (e_{q−1} → e_q) and (e_q → e_{q+1}).

**The detector statistic**: `Δ_T(sura, edited) = ‖T(sura) − T(edited)‖_1 / 2 ∈ [0, 1]`.

**Theorem 1 (transition-matrix L1 bound under k-verse reordering)**: any reordering that displaces k verses changes at most 4k transitions. Therefore `Δ_T ≤ 4k / (N − 1)`. For a single 2-verse swap (k = 2): `Δ_T ≤ 8 / (N − 1)`. For N = 50: `Δ_T ≤ 0.163`.

**Theorem 2 (transition-matrix L1 lower bound under uniform random shuffle)**: under uniform random verse-shuffling, expected Δ_T → 1 − 1/A as N → ∞ (where A is the alphabet size). For Quran A = 28: expected Δ_T → 0.964.

So the detector signal is: small reorders give small Δ_T; large reorders give large Δ_T. Calibrate threshold τ_T to separate these regimes.

---

## 2. Question

For Quran suras with N ≥ 20 verses:
1. **Recall**: under a random 2-verse swap, is `Δ_T` non-zero with probability ≥ 0.95? (i.e., does the swap actually change the transition matrix?)
2. **FPR**: under no edit, is `Δ_T = 0`? (trivially yes)
3. **Detection**: under a random 2-verse swap, is `Δ_T` distinguishable from 0 by a threshold τ_T = 4 / (N − 1) = analytic bound for k = 1?

---

## 3. Data — locked

**Source**: `results/checkpoints/phase_06_phi_m.pkl` Quran corpus, 114 suras (filtered to N ≥ 20 verses → expected ~70 suras).

**Permutation null**: 1,000 random 2-verse swaps per sura (10 distinct swap pairs × 100 reps; uniform over all N(N−1)/2 unordered pairs). Seed = 42.

---

## 4. Protocol

For each sura `s` with `N ≥ 20`:
1. Compute T(s) the original transition matrix.
2. For 100 random 2-verse swaps (i, j) drawn uniformly from all pairs:
   - Form edited sura by swapping verses i and j
   - Compute T(edited)
   - Compute Δ_T(s, edited)
3. Report:
   - Per-sura recall: fraction of swaps with Δ_T > 0
   - Per-sura mean Δ_T across swaps
   - Per-sura mean Δ_T normalised by (N−1) [scale-invariant]
4. Aggregate-recall = mean per-sura recall. Aggregate-Δ_T = mean per-sura mean Δ_T.

---

## 5. Decision rules (locked)

- PASS_verse_reorder_detector: aggregate-recall ≥ 0.95 (most 2-verse swaps detected) AND mean Δ_T > 0.02 (substantively non-trivial signal).
- FAIL_recall_below_floor: aggregate recall < 0.95 (many swaps undetected).
- FAIL_signal_below_floor: mean Δ_T < 0.02 (signal too small to be useful).

**Honest disclosure**: we expect SOME 2-verse swaps to be undetected when both swapped verses end with the same letter (most common case for Quran since 73% of verses end with ن). This is the analytic prediction. The recall floor of 0.95 would be EASY to fail — let's see what the data show.

---

## 6. Audit hooks

- A1: source pkl SHA-256 byte-match locked.
- A2: ≥ 50 suras in pool with N ≥ 20.
- A3: deterministic seed = 42 for permutation generator.
- A4: rerun-determinism (fixed seed → byte-identical receipt).

---

## 7. Receipt path

`results/experiments/exp117_verse_reorder_detector/exp117_verse_reorder_detector.json`

---

## 8. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H72 reserved in `HYPOTHESES_AND_TESTS.md`.
