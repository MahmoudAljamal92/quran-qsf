# exp130_F75_stability_under_resampling — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.2 sprint, sub-task 3)
**Hypothesis ID**: H86
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

F75 (`exp122_zipf_equation_hunt`, V3.13) found that the **Shannon-Rényi-∞ gap** `G(c) := H_EL(c) + log₂(p_max(c) · A)` (with A = 28 fixed across all 11 corpora) is approximately **constant at 5.75 ± 0.11 bits** (CV = 1.94 %) across the V3.14 11-corpus pool — a Zipf-class universal regularity.

Two questions about F75's character:

**(Q1) Sequence-invariance**: by construction, G(c) depends only on the end-letter histogram (not on verse order). A trivial sanity check should confirm exact invariance under verse permutation. We pre-register this as a **mathematical-identity sanity check** — it must hold at machine precision.

**(Q2) Sampling stability**: is the constancy of G across corpora **robust to sampling variation**, or is it an artifact of the specific N_verses each corpus has? Test via bootstrap resampling — sample N verses **with replacement** from each corpus's verse-list, recompute G, check whether the cross-corpus mean stays at 5.75 with comparable CV.

If F75 survives **both** checks → it is a **stable frequency-distribution law** (not sequence-aware, not size-fragile). This would qualify F75 for upgrade from "empirical universal regularity" to "robust frequency-distribution law" in PAPER §4.47.21.

If Q1 fails → bug in feature implementation (mathematical contradiction).
If Q2 fails → F75 may be size-dependent and the constancy is an artifact of pool composition; pursue per-corpus mean-spread analysis to characterise the failure.

## 2. Pool

Identical to F75 / F76 / F77 / F78 (locked V3.14 11-corpus pool):
- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`.
- **Loader**: `scripts/_phi_universal_xtrad_sizing.py` (same loaders used by exp109 / exp125c).

## 3. Procedure

> **Pre-execution amendment 2026-04-29 night**: the original Stage A/B/C draft pooled all verses and computed G on the corpus-level histogram. This was discovered (via diagnostic v0 run, receipt preserved at `__amendment_diagnostic_v0`) to **misrepresent F75**, which is a per-UNIT MEDIAN statistic, not a corpus-pooled statistic. F75 G(c) is `median_u(H_EL(unit_u)) + log₂(median_u(p_max(unit_u)) · A)` per the locked `_phi_universal_xtrad_sizing.json` medians and exp122 receipt. The diagnostic v0 verdict `FAIL_F75_universal_breaks_under_resampling` was an implementation error (Quran's pooled G = 6.28 vs F75's per-unit-median G = 5.32; pooling diluted the per-surah rāwī concentration that F75 captures). Stages updated to per-unit median formulation below; thresholds unchanged.

### Stage A — Per-corpus per-unit (p_max, H_EL) lists

For each corpus, load all units (chapters / suttas / surahs). For each unit:
1. Take the unit's verse list, normalise each verse via the language-specific normaliser, take last-character of each non-empty normalised verse.
2. Compute that unit's `(p_max, H_EL)` pair from its own end-letter histogram.

Result: per-corpus list `units[c]` where each `units[c][i] = (p_max_i, H_EL_i)` for unit `i`.

The corpus-level G is then:
`G(c) := median_i(H_EL_i) + log₂(median_i(p_max_i) · 28)` (matches F75 exactly).

**Audit**: per-corpus G matches the locked F75 value within 0.01 bits.

### Stage B — Q1 unit-shuffle invariance sanity check

For each corpus and **N_PERM = 50** unit-order permutations (seed = 42 base + perm_idx):
1. Random-shuffle the unit list.
2. Recompute G(c).
3. Assert `|G_shuffled − G_original| < 1e-12` (medians are order-invariant).

**Pass criterion**: ALL 11 × 50 = 550 perms identical within 1e-12.

### Stage C — Q2 bootstrap-resampling stability over UNITS

For each corpus and **N_BOOTSTRAP = 200** bootstrap iterations (seed = 42 base + boot_idx):
1. Sample N = `len(units[c])` units **with replacement** from `units[c]`.
2. Recompute medians on the resampled unit list and G on those medians.
3. Record G value.

Aggregate per corpus:
- `G_mean(c) := mean over 200 bootstraps`
- `G_std(c)  := std over 200 bootstraps`
- `G_cv(c)   := G_std(c) / G_mean(c)`

Aggregate across corpora:
- `G_universal_mean := mean over (corpora c × 200 bootstraps) = mean over 2,200 measurements`
- `G_universal_std  := std over the same`
- `G_universal_cv   := G_universal_std / G_universal_mean`

### Stage D — Per-corpus stability check

For each corpus, compare bootstrap distribution to the locked F75 value:
- **Stable per corpus**: `|G_mean(c) − G_locked(c)| ≤ 0.05 bits` AND `G_cv(c) ≤ 0.05` (5%)

Where `G_locked(c)` = F75 per-corpus values from `results/auxiliary/f75_per_corpus_values.json` (re-derived from `_phi_universal_xtrad_sizing.json` medians).

## 4. Acceptance criteria (pre-registered, frozen)

A frequency-law upgrade is **PASS_F75_robust_frequency_law** iff **all four**:

- **(a) Q1 sanity**: all 550 verse-shuffle perms identical to original within 1e-12 (mathematical identity holds).
- **(b) Q2 cross-corpus universality**: `G_universal_mean = 5.75 ± 0.20` AND `G_universal_cv ≤ 0.04` (4%).
- **(c) Per-corpus stability**: `≥ 9 of 11` corpora satisfy `G_cv(c) ≤ 0.05` AND `|G_mean(c) − G_locked(c)| ≤ 0.05`.
- **(d) Quran outlier preserved**: Quran's bootstrap-mean G is the lowest of all 11 corpora (matches F75's Quran z = −3.89 below universal mean).

A weaker outcome **PARTIAL_F75_stable_but_outlier_diluted** iff (a)+(b)+(c) hold but Quran's bootstrap-mean rank is not 1 (rank 2 or worse). This would mean the universal regularity is robust but the Quran-specific outlier within it is fragile to resampling.

A weaker outcome **PARTIAL_F75_universal_only** iff (a)+(b) hold but per-corpus stability < 9.

**FAIL_F75_universal_breaks_under_resampling** otherwise.

## 5. Audit hooks

- **A1**: end-letter counts per corpus match exp109 sizing JSON within ±2 letters (allowance for normaliser deterministic re-runs that produce identical outputs but slightly different counts due to rounding in the median-aggregation; should be exactly 0 in practice).
- **A2**: Q1 sanity check: 550 permutations must yield byte-identical G values (1e-12 tolerance).
- **A3**: bootstrap RNG seed is deterministic; re-run produces byte-identical G values.
- **A4**: Quran G_mean must match F75's Quran G value (5.32) within ±0.10 bits.
- **A5**: receipt re-run produces byte-identical receipt.

## 6. Honest scope

If **PASS_F75_robust_frequency_law**: F75 is upgraded in PAPER §4.47.21 from "empirical universal regularity at CV 1.94 % across 11 corpora" to "**robust frequency-distribution law** invariant under verse-order permutation and stable under bootstrap resampling at CV ≤ 4 %, with the Quran consistently the rank-1 outlier (bootstrap mean lowest)". This is a **strengthening of F75**, not a new F-row. Documentation update only.

If **PARTIAL_F75_stable_but_outlier_diluted**: useful informational result. F75 universal stays at strength but the Quran-specific outlier becomes "median-rank 1 with ~5% bootstrap probability of rank 2-3". F75 stays at PARTIAL strength.

If **PARTIAL_F75_universal_only**: the universal mean is stable but some specific corpora have unstable G. Document the specific corpora and characterise the failure (likely small-N corpora like ksucca with only 13 chapters).

If **FAIL_F75_universal_breaks_under_resampling**: F75's stability is compromised; the locked CV 1.94% reflects a specific N composition that doesn't survive resampling. Document and downgrade F75's strength claim.

## 7. Output

Receipt: `results/experiments/exp130_F75_stability_under_resampling/exp130_F75_stability_under_resampling.json` containing:
- `verdict`
- `q1_sanity_check_results` (550 shuffles; max deviation expected 0)
- `q2_per_corpus_bootstrap_stats` (mean, std, cv for each of 11 corpora)
- `q2_universal_mean`, `q2_universal_std`, `q2_universal_cv`
- `q2_quran_rank_distribution` (out of 200 bootstraps, what fraction has Quran ranked 1 / 2 / 3 / etc.)
- `audit_report`, `prereg_hash`, `wall_time_s`

## 8. Wall-time estimate

- Load 11 corpora: ~10 s (uses cached files).
- Q1 (550 shuffles × 11 corpora): ~3 s.
- Q2 (200 bootstraps × 11 corpora): ~5 s.

**Expected total wall-time: 15–20 s**.

---

**Filed**: 2026-04-29 night (V3.14.2 sub-task 3)
