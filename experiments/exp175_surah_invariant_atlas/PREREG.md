# exp175_surah_invariant_atlas — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities intrinsic to the Quran.

## Hypothesis

There exists at least one **non-trivial intrinsic invariant** — a
quantity Q(s) computed from surah s's text — that is nearly constant
across all 114 surahs (CV < 0.05), after length-normalisation and
with a **theoretical interpretation** that makes the invariance
non-circular.

A CV < 0.01 invariant with non-trivial interpretation = paradigm-grade.
A CV < 0.05 invariant = strong candidate for locked reference constant.
Multiple independent low-CV invariants = structural-law suite.

## Candidate invariants (frozen before running)

18 candidates, computed per-surah on `quran_vocal.txt` after standard
cleaning (strip diacritics for letter stats; keep diacritics for sonority):

**Block A — Letter distribution**
- A1: **H_1** (Shannon letter entropy over 28 letters, bits).
- A2: **H_∞** (Rényi-∞ letter entropy = −log₂(p_max), bits).
- A3: **H_1 − H_∞** (F75 Rényi gap in bits) — the locked F75 invariant
  at surah scale.
- A4: **C_Ω = 1 − H_1 / log₂(28)** (F67 compactness).
- A5: **p_max** (single-letter max probability).

**Block B — Bigram / trigram**
- B1: **bigram distinct ratio** = (# unique bigrams) / (# total bigrams).
- B2: **bigram entropy H_2 / H_1** (ratio, dimensionless).

**Block C — Sonority / sequencing** (from exp168)
- C1: **ρ_lag1** of per-character sonority sequence.
- C2: **alt_rate** of per-character sonority.
- C3: **vowel fraction** (diacritics + alef + waw + yaa as vowel
  positions) / total characters.

**Block D — Verse-level**
- D1: **mean verse length** in letters.
- D2: **VL_CV** (coefficient of variation of verse lengths).
- D3: **nasal-rhyme fraction** (from exp172's 7-class rhyme scheme).
- D4: **rhyme entropy** H_EL.
- D5: **in-surah rhyme purity** = max-frequency rhyme class fraction.

**Block E — Compression**
- E1: **gzip compression ratio** = compressed_size / raw_size.
- E2: **letter-alphabet compression efficiency** = H_1 / log₂(28).
- E3: **redundancy** = 1 − H_1 / log₂(28) (alias of C_Ω-like).

## Procedure

1. Parse 114 surahs from `quran_vocal.txt`.
2. For each candidate Q ∈ {A1…E3}, compute per-surah vector of 114 values.
3. Report per-candidate: mean, std, CV, min, max, Spearman ρ with
   log(N_words) (length-robustness), Spearman ρ with surah-index
   (positional drift).
4. Flag candidates with **CV < 0.01**, **CV < 0.05**, and
   **CV < 0.10**.
5. For the **low-CV candidates** (CV < 0.05), perform a shuffle null:
   compute Q under 1 000 random permutations of each surah's letters
   (preserving multiset). Report whether observed CV is significantly
   lower than shuffled CV (one-tailed).

## Pre-registered verdict criteria

- **PASS_PARADIGM_INVARIANT** — ≥ 1 candidate has CV < 0.01 AND
  shuffle-null p < 0.01 AND is not trivially bounded (e.g., simple
  ratios of counts).
- **PASS_STRONG_INVARIANTS** — ≥ 3 candidates have CV < 0.05 with
  shuffle-null p < 0.01.
- **PASS_PARTIAL** — ≥ 1 candidate CV < 0.05 with p < 0.01.
- **FAIL** — no candidate below thresholds.

`frozen_at`: 2026-05-01.
