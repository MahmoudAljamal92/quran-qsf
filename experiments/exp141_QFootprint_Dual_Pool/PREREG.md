# Pre-Registration — exp141 — Q-Footprint Dual-Pool (Arabic vs non-Arabic vs combined)

**Status**: PRE-REGISTERED V3.15.2 final-pinnacle batch (sub-experiment 2 of 3)
**Author**: project leader (Cascade-assisted)
**Pre-reg date**: 2026-04-29 night

## 1. Background and motivation

V3.15.1's `exp138_Quran_Footprint_Joint_Z` reported the Quran's joint Stouffer Z = 12.149σ across all 12 corpora pooled together. This combines:
- 7 **Arabic** corpora (Quran + 6 Arabic peers spanning Jāhilī/Islāmī/ʿAbbāsī poetry, Hindawi modern prose, Ksūcca classical prose, Arabic Bible)
- 5 **non-Arabic** sacred-canon corpora (Hebrew Tanakh, Greek NT, Pāli Tipiṭaka, Avestan Yasna, Rigveda Saṃhitā)

These two pools are mechanistically different: Arabic peers share the 28-letter alphabet and grammatical morphology with Quran but differ in genre and chronology, while non-Arabic peers differ in alphabet (22-47), morphology, and tradition but share the canon-of-recitation function. The user's substantive question in V3.15.2: **"is the Quran's joint distinctiveness equally extreme in both comparison universes, or do the two stories differ?"**

This experiment splits exp138's joint Z into its (Arabic-only, non-Arabic-only, combined) components and reports the conservative claim "Quran is alone at the joint extremum in BOTH pools simultaneously".

## 2. Hypothesis

**H94-Dual-Pool** (pre-registered): The Quran's joint Stouffer Z (Brown-adjusted) over the same 8 axes from exp138 satisfies all of:
1. Arabic-only pool (n=7): Quran rank-1 with Z_brown ≥ 10.0 (substantively trivial extremum within Arabic)
2. Non-Arabic-only pool (n=6): Quran rank-1 with Z_brown ≥ 5.0 (non-trivial extremum across oral-canon traditions)
3. Combined pool (n=12): Quran rank-1 with Z_brown ≥ 8.0 (= exp138's reproduced result)
4. Min of (Z_arabic, Z_nonArabic) ≥ 5.0 (the "bilateral" claim — Quran wins both pools)

## 3. Sub-tasks

**Sub-task A — Pool definitions**:
- Pool A (Arabic-only): {quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible} — 7 corpora
- Pool B (non-Arabic-only, Quran-included): {quran, hebrew_tanakh, greek_nt, pali, avestan_yasna, rigveda} — 6 corpora
- Pool C (combined): all 12 (= exp138 pool)

**Sub-task B — Per-pool Q-Footprint**: For each pool, recompute (a) raw 8-axis values per corpus (already locked in exp138), (b) per-axis z-score using non-Quran rows IN THAT POOL as cluster (so each pool has its own standardization), (c) Quran joint Stouffer Z (Brown-adjusted with K_eff from per-pool axis correlation), (d) Hotelling T² with per-pool covariance.

**Sub-task C — Per-pool column-shuffle null** (N=10,000): For each pool, run column-shuffle on the per-pool z-matrix and compute fraction of permutations where max-corpus joint Z ≥ Quran's actual.

**Sub-task D — Bilateral synthesis**: Report (Z_A, Z_B, Z_C) tuple, gap-to-rank-2 in each pool, and the "min-pool" conservative claim.

**Sub-task E — Per-axis decomposition by pool**: For each axis, report Quran's z in each pool. Identify which axes are Quran-strong in each pool.

## 4. Acceptance criteria

A1: Pool A (Arabic) — Quran rank-1 with Z_brown ≥ 10.0. Expected: should pass easily (Quran is the rhyme extremum within Arabic by F76 / F78).  
A2: Pool B (non-Arabic) — Quran rank-1 with Z_brown ≥ 5.0. The harder test (Pāli/Rigveda are the closest peers).  
A3: Pool C (combined) — Quran rank-1 with Z_brown ≥ 8.0 (exp138 reproduction).  
A4: Bilateral — min(Z_A, Z_B, Z_C) ≥ 5.0.  
A5: Per-pool column-shuffle p_Z < 0.001 in all three pools.

Verdict ladder:
- All 5 PASS → `PASS_dual_pool_quran_alone_in_both` → promote as F80 / O7
- 3-4 PASS → `PARTIAL_dual_pool_directional`
- ≤ 2 PASS → `FAIL_dual_pool_inhomogeneous`

## 5. Audit hooks

- `prereg_hash` SHA256 of this file written into receipt.
- `frozen_constants`: K=8 axes (= exp138), N_PERM=10000, RIDGE=1e-3, SEED=42.
- `audit_report`: SHA256 of per-pool z-matrices; cross-check that Pool C reproduces exp138's Z_brown = 12.149 within 0.05 numerical noise.

## 6. Honest scope

This experiment splits the existing exp138 finding into two principled sub-pools. It does NOT introduce new data or new axes. The non-Arabic pool n=6 (5 non-Arabic peers + Quran) is small for stable z-standardization (n_non_quran = 5), so the Z_B estimate has wider uncertainty than Z_A or Z_C. A FAIL outcome in Pool B would be substantively informative: it would mean Pāli/Rigveda are close enough that the Quran is NOT alone at the cross-tradition oral-canon level, which would weaken the pool-C 12.149σ claim.

This is a finer-resolution lens on exp138, not a stronger or weaker test.
