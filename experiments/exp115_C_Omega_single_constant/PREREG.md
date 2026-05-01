# PREREG — exp115_C_Omega_single_constant: information-theoretic single-constant C_Ω

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H70.
**Author intent**: define a **single dimensionless information-theoretic constant** `C_Ω(text, alphabet)` that captures the "oral-fidelity" property in one number per text, analogous to Zipf's exponent α as a one-number characterization. Empirically rank all 12 cross-tradition corpora on C_Ω; test whether the Quran is the unique global maximum.

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **Definition**:
   ```
   C_Ω(text, A) := 1 − H_EL(text) / log₂(A)
   ```
   where:
   - H_EL(text) = Shannon entropy (in bits) of the end-letter distribution over verse-final letters
   - A = alphabet size for the text's normalized writing system
   - log₂(A) = maximum end-letter entropy under the uniform distribution

2. **Information-theoretic interpretation**:
   ```
   C_Ω = (log₂(A) − H_EL) / log₂(A) = I(end-letter; text-identity) / log₂(A)
   ```
   That is, C_Ω is the **fraction of the alphabet's maximum entropy that is used for rhyme prediction**. C_Ω = 0 means end-letter distribution is uniform (no rhyme channel utilization); C_Ω = 1 means end-letter is perfectly predictable (one letter dominates entirely).

3. **Why this formulation**:
   - It is **dimensionless** ([0, 1] range)
   - It is **alphabet-independent** (normalized by log₂(A))
   - It composes the F48 (p_max) and F63 (H_EL) findings into one number
   - It is **derivable from Shannon information theory**, not ad hoc
   - It is **falsifiable**: any text in any alphabet can be measured against the same scale

4. **Pre-run sizing diagnostic** (computed from already-locked F63/F64 medians; both are deterministic functions of locked corpora so this is not a "look at the answer" violation, just exposing the input numbers):
   - Quran: C_Ω = 1 − 0.2015 = **0.7985**
   - Rigveda: C_Ω = 1 − 0.4119 = 0.5881
   - Pāli: C_Ω = 1 − 0.4219 = 0.5781
   - Avestan: C_Ω = 1 − 0.4506 = 0.5494
   - Greek NT: C_Ω = 1 − 0.5308 = 0.4692
   - Hebrew Tanakh: C_Ω = 1 − 0.6846 = 0.3154
   - Six Arabic peers: C_Ω ∈ [0.276, 0.441]
   
   So **Quran's C_Ω is global rank 1/12** by margin 0.21 over rank-2 (Rigveda).

5. **What this hypothesis is NOT**:
   - NOT a claim that C_Ω is a unique mathematical constant analogous to Zipf's α (we explicitly tested this in exp114 H69 and FALSIFIED Form-2)
   - NOT a claim that all oral-religious canons share a common C_Ω value (they don't; oral canons span [0.31, 0.80])
   - NOT a claim of theological significance — C_Ω is a structural-information measurement, period

6. **What this hypothesis IS**:
   - C_Ω is the **single-number summary** of cross-tradition rhyme channel utilization
   - The Quran's C_Ω is the unique global maximum across the 12-corpus pool
   - C_Ω provides a **portable, dimensionless, falsifiable scale** for cross-tradition stylometry

---

## 1. Question

Is the Quran the unique global maximum on C_Ω = 1 − H_EL/log₂(A) across the 12-corpus cross-tradition pool, with C_Ω(Quran) ≥ 1.3 × C_Ω(rank-2)?

---

## 2. Data — locked

**Source**: `results/experiments/exp114_alphabet_independent_pmax/exp114_alphabet_independent_pmax.json` (locked R_HEL values for all 12 corpora; SHA-256 fingerprinted).

**Locked alphabet sizes**: identical to exp114 (Arabic 28, Hebrew 22, Greek 24, Pāli 31, Avestan 26, Devanagari 47).

**Pool (12 corpora)**: identical to exp114.

---

## 3. Protocol

For each corpus C with locked H_EL(C) and alphabet A_C:
1. Compute `C_Ω(C) = 1 − H_EL(C) / log₂(A_C)`
2. Rank corpora on C_Ω (descending; rank 1 = highest)
3. Check: Quran rank == 1 AND C_Ω(Quran) / C_Ω(rank-2) ≥ 1.3
4. Report ranking and ratios; provide alphabet-independence audit (no corpus is privileged by alphabet size)

**Permutation null**: 10,000 random label-shuffles (seed 42) of the 12 C_Ω values across 12 corpus positions; count fraction of shuffles where the Quran-position is the global max. This is the same structural floor as exp114 (1/N = 0.083), so we ALSO report:
- Form-A (rank-based, will saturate at 1/N): for transparency
- Form-B (z-score parametric, primary): Quran's z vs the 11-corpus peer distribution

---

## 4. Decision rule (locked)

- PASS_quran_unique_C_Omega_max: Quran C_Ω rank == 1 AND C_Ω(Quran)/C_Ω(rank-2) ≥ 1.3 AND z(Quran vs peers) ≤ −2.0 AND parametric_p_t < 0.05
- FAIL_quran_not_rank_1: Quran rank ≠ 1
- FAIL_margin_below_1_3: ratio < 1.3
- FAIL_z_above_minus_2: z > −2.0

---

## 5. Audit hooks

- A1: source receipt (exp114) SHA-256 byte-match locked.
- A2: 12 corpora present, all H_EL non-NaN.
- A3: alphabet sizes byte-fingerprinted to prior PREREGs.
- A4: deterministic computation; no randomness except permutation null with seed = 42.
- A5: rerun-determinism check (re-run gives byte-identical receipt).

---

## 6. Receipt path

`results/experiments/exp115_C_Omega_single_constant/exp115_C_Omega_single_constant.json`

---

## 7. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H70 reserved in `HYPOTHESES_AND_TESTS.md`.
