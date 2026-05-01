# PREREG — exp118_multi_letter_F55_theorem: k-letter substitution Δ ≤ 2k bound

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.10.
**Hypothesis ID**: H73.

---

## 0. The mathematical theorem (locked, derivable from F55 PREREG)

**Theorem F55-multi**: For any text T over alphabet Σ and any k-letter symbolic substitution T → T' (i.e., k positions in T are changed to other letters from Σ, with the rest unchanged), the L1 bigram-distance satisfies:

```
Δ_bigram(T, T') := ‖hist_2(T) − hist_2(T')‖_1 / 2  ≤  2k
```

**Proof**: a single-position substitution at character index i affects at most 4 bigram-counts (the bigrams (T[i-1], T[i]), (T[i], T[i+1]), and their replacements (T[i-1], T'[i]), (T'[i], T[i+1])). The L1 distance increment from one substitution is therefore at most 4 (2 bigrams decremented, 2 incremented). Dividing by 2 gives Δ ≤ 2 per substitution. By the triangle inequality, k independent substitutions give Δ ≤ 2k. ∎

This generalises the F55 single-letter theorem (k=1, Δ ≤ 2) to arbitrary k.

---

## 1. Question

Given the F55 universal symbolic forgery detector with frozen τ = 2.0, can we generalise to a k-letter detector with frozen τ_k = 2k?

**Empirical verification**: for k ∈ {1, 2, 3, 4, 5}, sample 1,000 random k-letter substitutions per Quran sura (across all 114 suras, total 114,000 variants per k), verify:
1. Theorem holds: max(Δ) ≤ 2k empirically
2. Recall = 1.000: all k-letter substitutions fire under firing rule `0 < Δ ≤ 2k`
3. FPR via peer pool: any non-Quran chapter pair (sampled from same 7-corpus pool used in F55) gives Δ > 2k

---

## 2. Data — locked

**Source**: `results/checkpoints/phase_06_phi_m.pkl` (Quran + 6 Arabic peer corpora; SHA-256 fingerprinted).

**Sampling**:
- 114 Quran suras
- 1,000 random k-letter substitutions per sura per k ∈ {1, 2, 3, 4, 5}
- Total: 5 × 114 × 1,000 = 570,000 variants
- Seeds locked: SEED_BASE = 42, per-k seed = SEED_BASE * 1000 + k

**Peer FPR pool**: all pairs (sura_a, peer_b) where a ∈ {114 Quran suras}, b ∈ {non-Quran chapters from poetry_jahili / poetry_islami / poetry_abbasi / hindawi / ksucca / arabic_bible}. Total: 114 × ~2,000 ≈ 228,000 pairs. Subsample 5,000 random pairs per k for FPR test.

---

## 3. Protocol

For each k ∈ {1, 2, 3, 4, 5}:

**Step 1 (theorem verification)**: for each of 1,000 random k-letter substitutions per sura:
- Sample k distinct positions uniformly from sura's letter-skeleton (after Arabic 28-letter normaliser)
- For each position, sample a different letter from Σ uniformly
- Compute Δ_bigram(orig, edited)
- Verify: Δ ≤ 2k

**Step 2 (recall)**: count fraction of substitutions where 0 < Δ ≤ 2k. Recall_k = #{Δ ∈ (0, 2k]} / 114,000.

**Step 3 (FPR)**: sample 5,000 random (Quran_sura_a, peer_chapter_b) pairs. For each, compute Δ_bigram(a, b). Count fraction where Δ ≤ 2k. FPR_k = #{Δ ≤ 2k} / 5,000.

---

## 4. Decision rules (locked)

- PASS_F55_multi_k_universal: for each k ∈ {1,2,3,4,5}: max_Δ ≤ 2k AND recall_k ≥ 0.999 AND FPR_k ≤ 0.05.
- PASS_F55_multi_partial: holds for at least k ∈ {1, 2, 3} but fails for k ≥ 4.
- FAIL_theorem_violated: any k where max_Δ > 2k (would falsify the theorem; should be impossible by construction).
- FAIL_recall_below_floor: any k where recall_k < 0.999.
- FAIL_FPR_above_ceiling: any k where FPR_k > 0.05 (peer signal is too close to Quran-edit signal).

---

## 5. Audit hooks

- A1: source pkl SHA-256 byte-match locked.
- A2: 114 suras + ≥ 1,000 peer chapters present.
- A3: deterministic seeds.
- A4: rerun-determinism (seed-fixed → byte-identical receipt).

---

## 6. Receipt path

`results/experiments/exp118_multi_letter_F55_theorem/exp118_multi_letter_F55_theorem.json`

---

## 7. Author signature

Locked under v7.9-cand patch H V3.10, 2026-04-29 morning. Hypothesis ID H73 reserved in `HYPOTHESES_AND_TESTS.md`.
