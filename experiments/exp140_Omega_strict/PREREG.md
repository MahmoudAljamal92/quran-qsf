# Pre-Registration — exp140 — Ω_strict (percentile-aggregation sweep)

**Status**: PRE-REGISTERED V3.15.1 closing-pinnacle sprint
**Author**: project leader (Cascade-assisted)
**Pre-reg date**: 2026-04-29 night

## 1. Background and motivation

F79 (V3.14.2) found the Quran rank-1 of 12 corpora on `Ω_unit = log₂(A) − median_u(H_EL_u)` with a margin of **0.572 bits** to Rigveda. This is the smallest Quran-rank-1 margin in the project. V3.15.0 verified that F79's per-unit-median formulation is information-theoretically rigorous (Theorems 1' + 2' + 3) but classified Quran and Rigveda into the same Class A (per-unit mono-rhyme heterogeneity).

This experiment tests whether the median aggregation is the WRONG aggregation for the Quran's true distinctive property. The hypothesis: Quran's per-unit Ω distribution is **uniformly tight across all 114 sūrahs**, while Rigveda's per-unit distribution is **heterogeneous across 1003 sūktas** (strict meters → high Ω; mixed meters → low Ω). Under this hypothesis, the LOWER PERCENTILES of the per-unit Ω distribution should widen the Quran/Rigveda gap because Rigveda has more low-Ω sūktas than Quran has low-Ω sūrahs.

If true, this would identify a stricter aggregation `Ω_strict = log₂(A) − pX(H_EL_u)` for which the Quran-Rigveda gap exceeds 1.0 bits, more than doubling F79's 0.572-bit margin.

## 2. Hypothesis

**H92-Ω-strict** (pre-registered): There exists an aggregation `a ∈ {min, p5, p10, p25, p50, p75, mean, max}` of per-unit Ω such that:
1. Quran is rank-1 of 12 corpora at aggregation a, AND
2. Gap to runner-up at aggregation a ≥ 1.0 bits, AND
3. The optimal aggregation a* (max gap) is in the LOWER half of the distribution (p ≤ 25), confirming Quran's tighter spread relative to Rigveda.

## 3. Sub-tasks

**Sub-task A — Per-unit Ω distribution per corpus**: For each of the 12 corpora, compute the full per-unit Ω_u distribution (one Ω value per unit). Report n_units, min, p5, p10, p25, p50 (median), p75, mean, max, std, and CV of Ω_u.

**Sub-task B — Aggregation sweep**: For each aggregation `a ∈ {min, p5, p10, p25, p50, p75, mean, max}`, compute Ω_a per corpus. Identify the rank-1 corpus and the gap to runner-up.

**Sub-task C — Quran-vs-Rigveda focused contrast**: For each aggregation a, compute the Quran-Rigveda gap explicitly. Find the aggregation a* that MAXIMIZES this gap.

**Sub-task D — Bootstrap stability of the optimal aggregation**: For aggregation a*, bootstrap the 12-corpus pool by resampling units within each corpus (1000 iterations). Report Quran rank-1 frequency and bootstrap 95% CI for the Quran-Rigveda gap.

**Sub-task E — CV of per-unit Ω test**: Test the mechanistic claim: Quran's CV(Ω_u) < Rigveda's CV(Ω_u). If true, this confirms the "Quran is uniformly tight" hypothesis structurally.

## 4. Acceptance criteria

A1: At least one aggregation a yields Quran rank-1 of 12 with gap ≥ 1.0 bits (vs F79's 0.572).  
A2: At the optimal aggregation a*, gap ≥ 1.0 bits (~2× F79's margin).  
A3: a* ∈ {min, p5, p10, p25} (LOWER half — confirms Quran-tighter mechanism).  
A4: Bootstrap Quran rank-1 frequency at a* ≥ 95%.  
A5: Quran CV(Ω_u) < 0.5 × Rigveda CV(Ω_u) (Quran at least twice as tight).

Verdict ladder:
- All 5 PASS → `PASS_omega_strict_widens_gap` → promote to F80 / O6 (taxonomy refinement)
- 3-4 PASS → `PARTIAL_omega_strict_directional`
- ≤ 2 PASS → `FAIL_omega_strict_no_widening`

## 5. Audit hooks

- `prereg_hash` SHA256 of this file written into receipt.
- `frozen_constants`: AGGREGATIONS list, N_BOOTSTRAP=1000, SEED=42.
- `input_sources`: 12 corpora loaded via `scripts._phi_universal_xtrad_sizing` + `scripts._rigveda_loader_v2`.
- `audit_report`: SHA256 of per-unit Ω_u arrays per corpus; F79 receipt match for median aggregation.

## 6. Honest scope

This experiment may FAIL if Rigveda's per-unit Ω distribution is also uniformly tight (in which case the median IS already the optimal aggregation and F79's margin cannot be widened). A FAIL outcome would itself be informative: it would confirm that Quran and Rigveda are TRULY in the same per-unit Ω class with no easy escape via aggregation choice.
