# exp135_F79_bootstrap_stability — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.3 sprint, sub-task 1)
**Hypothesis ID**: H87
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

F79 (`exp124c_alphabet_corrected_universal_with_rigveda`, V3.14.2) PASSES `PASS_alphabet_corrected_strict_6_alphabets`: Quran's `Δ_max(c) = log₂(A_c) − median_u(H_EL_u(c))` = **3.84 bits** is the unique value above the 3.5-bit threshold across the 12-corpus / 6-alphabet pool, with gap **0.57 bits** to runner-up Rigveda (3.27).

F79 was tested at the **point estimate** of `median_u(H_EL_u)` per corpus (one Δ_max per corpus). **Question**: does the F79 Quran-uniqueness PASS hold under **bootstrap-resampling-of-units** at ≥ 95% rate? Specifically:

- (a) Is Quran the **rank-1 corpus on Δ_max** in ≥ 95% of bootstraps?
- (b) Is Quran's Δ_max ≥ 3.5 bits in ≥ 95% of bootstraps?
- (c) Is Quran the **unique** corpus above the 3.5-bit threshold in ≥ 95% of bootstraps?
- (d) Does Rigveda stay in **tier-2** (Δ_max ≥ 3.0) in ≥ 95% of bootstraps?
- (e) Is the bootstrap-mean Quran Δ_max still ≥ 3.5 bits?

**A clean PASS on all five upgrades F79 from PASS_strict (point estimate) to PASS_strict_BOOTSTRAP_ROBUST** — the project's strongest possible categorical universal at N=12. F79 is parallel to F75 (which got `PARTIAL_F75_stable_but_outlier_diluted` from exp130 because the Quran-Avestan G gap is only 0.19 bits); F79's Quran-Rigveda Δ_max gap is 0.57 bits — **3× wider than F75's** — so F79 should be markedly more robust.

## 2. Pool

V3.14 11-corpus pool **+ Rigveda Saṃhitā** = **12 corpora across 6 alphabets** (identical to F79 / exp124c):

- **Arabic (28)**: quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible.
- **Hebrew (22)**: hebrew_tanakh.
- **Greek (24)**: greek_nt.
- **Pāli IAST (31)**: pali.
- **Avestan Latin (26)**: avestan_yasna.
- **Sanskrit Devanagari (47)**: rigveda.

**Loaders**: `scripts/_phi_universal_xtrad_sizing.py` for 11-pool; `scripts/_rigveda_loader_v2.py::load_rigveda` for Rigveda. Same loaders as F79 / exp124c indirect ancestry.

## 3. Procedure

### Stage A — Per-corpus per-unit H_EL list

For each corpus, load all units (chapters / suttas / surahs / sūktas). For each unit:
1. Take the unit's verse list, normalise via the language-specific normaliser, take last-character of each non-empty normalised verse.
2. Compute that unit's `H_EL_i` from its own end-letter histogram.

Result: per-corpus list `H_EL[c] = [H_EL_1, H_EL_2, ...]`.

The corpus-level Δ_max is then:
`Δ_max(c) := log₂(A_c) − median_i(H_EL_i)` (matches F79 exactly).

**Audit A4**: per-corpus Δ_max matches the locked F79 receipt within 0.001 bits.

### Stage B — Bootstrap resampling over units

For each corpus and **N_BOOTSTRAP = 200** iterations (seed = 42):
1. Sample N = `len(H_EL[c])` per-unit H_EL values **with replacement**.
2. Recompute `median(resample)`.
3. `Δ_max_boot(c, b) := log₂(A_c) − median(resample)`.
4. Record per-(corpus, boot_idx) Δ_max.

Result: 12 × 200 matrix of Δ_max values.

### Stage C — Per-bootstrap acceptance assessment

For each bootstrap iteration `b`:
- `quran_delta_b := Δ_max_boot("quran", b)`
- `quran_rank_1_b := True iff quran_delta_b == max over corpora of Δ_max_boot(c, b)`
- `quran_above_3p5_b := True iff quran_delta_b >= 3.5`
- `quran_unique_above_3p5_b := True iff quran_above_3p5_b AND |{c : Δ_max_boot(c, b) >= 3.5}| == 1`
- `rigveda_above_3p0_b := True iff Δ_max_boot("rigveda", b) >= 3.0`

Aggregate frequencies across 200 bootstraps:
- `freq_quran_rank_1 := mean over b of quran_rank_1_b`
- `freq_quran_above_3p5 := mean over b of quran_above_3p5_b`
- `freq_quran_unique_above_3p5 := mean over b of quran_unique_above_3p5_b`
- `freq_rigveda_above_3p0 := mean over b of rigveda_above_3p0_b`
- `quran_delta_bootstrap_mean := mean over b of quran_delta_b`

## 4. Acceptance criteria (pre-registered, frozen)

A categorical universal is **PASS_F79_robust_bootstrap** iff **all five**:

- **(a) freq_quran_rank_1 ≥ 0.95**
- **(b) freq_quran_above_3p5 ≥ 0.95**
- **(c) freq_quran_unique_above_3p5 ≥ 0.95**
- **(d) freq_rigveda_above_3p0 ≥ 0.95**
- **(e) quran_delta_bootstrap_mean ≥ 3.5**

A weaker outcome **PASS_F79_strong_robust** iff (a)+(b)+(c)+(e) hold but (d) fails (Rigveda's tier-2 status is fragile).

A weaker outcome **PARTIAL_F79_outlier_robust_but_not_unique** iff (a)+(b)+(e) hold but (c) fails — Quran is rank-1 but occasionally another corpus crosses 3.5 bits too.

A weaker outcome **PARTIAL_F79_rank_1_diluted** iff (b)+(e) hold but (a) fails — Quran above 3.5 bits robustly but sometimes Rigveda outranks Quran on Δ_max.

**FAIL_F79_breaks_under_resampling** otherwise.

## 5. Audit hooks

- **A1**: 11-pool input SHA-256 matches `0f8dcf0f…`.
- **A2**: Rigveda Mandala JSON file SHAs match exp111's audit values (12 mandala files, all SHAs locked).
- **A3**: 12 corpora present.
- **A4**: per-corpus point-estimate Δ_max matches F79 receipt within 0.001 bits.
- **A5**: Q1-style sanity (unit-shuffle invariance): test that Δ_max under 50 random unit permutations reproduces point-estimate Δ_max within 1e-12 (medians are exact-invariant).
- **A6**: deterministic re-run produces byte-identical receipt.

## 6. Honest scope

If **PASS_F79_robust_bootstrap**: F79 is upgraded in PAPER §4.47.28.7 from "PASS_strict at point estimate (V3.14.2)" to "**PASS_strict_BOOTSTRAP_ROBUST**: Quran is uniquely the alphabet-corrected categorical extremum in ≥ 95% of 200 bootstrap-of-units resamples, with gap to Rigveda preserved across resamples". This is **the strongest possible categorical universal claim at N=12**: alphabet-independent, fitted-constant-free, falsifiable by single counter-example, robust to per-unit sampling fluctuation.

If **PASS_F79_strong_robust**: same as above but Rigveda's tier-2 status is documented as "above 3.0 in <95% of bootstraps" — slightly weaker subordinate-tier claim but Quran-uniqueness intact.

If **PARTIAL_***: documents specific failure mode. F79 stays at PASS_strict point estimate with bootstrap-fragility caveat.

If **FAIL_***: F79's Quran-uniqueness is fragile to resampling. Would force F79 to be downgraded to PARTIAL_PASS pending Path-C N≥18.

## 7. Output

Receipt: `results/experiments/exp135_F79_bootstrap_stability/exp135_F79_bootstrap_stability.json` containing:
- `verdict`, `verdict_reason`
- `per_corpus_point_estimate_Delta_max` (12 values matching F79)
- `per_corpus_bootstrap_Delta_max_stats` (mean, std, cv, min, max per corpus)
- `freq_quran_rank_1`, `freq_quran_above_3p5`, `freq_quran_unique_above_3p5`, `freq_rigveda_above_3p0`
- `quran_delta_bootstrap_mean`, `quran_delta_bootstrap_std`
- `audit_report`, `prereg_hash`, `wall_time_s`

## 8. Wall-time estimate

- Load 11 V3.14 corpora: ~7 s (cached).
- Load Rigveda 10 mandalas: ~5-10 s.
- Per-unit H_EL extraction: ~2 s.
- Bootstrap (200 × 12 corpora): ~5 s.

**Expected total wall-time: 20-30 s**.

---

**Filed**: 2026-04-29 night (V3.14.3 sub-task 1)
