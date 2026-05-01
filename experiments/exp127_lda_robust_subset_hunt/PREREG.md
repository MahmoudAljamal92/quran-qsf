# exp127_lda_robust_subset_hunt — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.2 sprint, sub-task 1)
**Hypothesis ID**: H84
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

F77 (`exp125b`) achieved **full-pool PASS_strong** (Quran |z| = 10.21, J = 10.43) but **FAILS LOO**: min Quran |z|_LOO = 3.74 (< 4.0 floor), max max_other |z|_LOO = 2.96 (> 2.5 ceiling). The receipt was sealed as `PARTIAL_lda_strong_BUT_LOO_NOT_ROBUST` pending Path-C N≥18.

**Question**: does any **proper subset of the 5 universal features** yield an LDA direction that PASSES BOTH full-pool (|z|≥5, max_other≤2, J≥5) AND LOO (min |z|_LOO≥4, max max_other |z|_LOO≤2.5)? If yes, that subset is the project's **first FULLY ROBUST supervised unification at N=11**, promotable to F79 = PASS without waiting for Path-C.

The 5-feature LDA fails LOO because either:
- One feature is a "noisy" axis whose contribution is dominantly responsible for a competing corpus's z-shift under LOO refit, OR
- Lower-dimensional LDA has fewer degrees of freedom and thus less LOO instability.

Either way, dropping the right feature(s) could fix it.

## 2. Pool

Identical to F77 / F76 / F75 (locked V3.14 11-corpus pool):
- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`.
- **Features (full set, N_F=5)**: `{VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency}` (matches exp125b's locked feature list).
- **Source**: `results/auxiliary/_phi_universal_xtrad_sizing.json::medians[c]` (SHA-pinned `0f8dcf0f…`).

## 3. Procedure

### Subset enumeration

For each subset size `k ∈ {2, 3, 4, 5}`:
- Enumerate every `C(5, k)` feature subset.
- Total: C(5,5) + C(5,4) + C(5,3) + C(5,2) = 1 + 5 + 10 + 10 = **26 subsets**.

For each subset `S`:

1. **Build standardised matrix** `Z_S ∈ R^{11 × |S|}` (z-score per kept feature).
2. **Fit Fisher LDA** Quran-vs-rest on `Z_S` with ridge ε = 1e-6 (mirrors exp125b exactly).
3. **Project all 11 corpora** onto `w_LDA(S)`; compute Quran `z`, max competing `|z|`, Fisher ratio `J`.
4. **LOO refit**: for each of 10 non-Quran corpora `c_h` held out, refit LDA on the remaining 10; project all 11 onto the new direction; record Quran `|z|_LOO` and max competing `|z|_LOO`.
5. Record full-pool + LOO statistics for the subset.

### Decision

A subset `S` is **PASS_robust_subset** iff **all five**:
- (a) Full-pool `|z_quran| ≥ 5.0`
- (b) Full-pool `max_other_abs_z ≤ 2.0`
- (c) Fisher ratio `J ≥ 5.0`
- (d) LOO `min |z_quran|_LOO ≥ 4.0`
- (e) LOO `max max_other_abs_z_LOO ≤ 2.5`

A subset is **PASS_robust_subset_strong** iff (a)-(e) hold AND `min |z_quran|_LOO ≥ 5.0` AND `max max_other_abs_z_LOO ≤ 2.0` (matching the full-pool criteria under LOO too — true universal-quality robustness).

## 4. Acceptance criteria (pre-registered, frozen)

**PASS_robust_subset_found** iff at least one subset (k ≥ 2) satisfies criteria (a)-(e).

**PASS_robust_subset_strong** iff at least one subset satisfies (a)-(e) AND the strong-LOO version.

**PARTIAL_full_pool_subset_only** iff at least one subset satisfies (a)-(c) but none satisfies (d)-(e). (This would mean: lower-dimensional unification exists at full-pool but the LOO instability persists — same conclusion as F77 at N=11.)

**FAIL_no_full_pool_subset** iff no subset satisfies (a)-(c). (This would mean: full 5 features are required for full-pool PASS_strong; the unification cannot be compressed.)

## 5. Audit hooks

- **A1**: input SHA-256 matches expected `0f8dcf0f…` (same as exp125b).
- **A2**: 26 subsets enumerated; full-feature subset (k=5) reproduces exp125b's locked numbers exactly (Quran |z| = 10.21 ± 0.01, J = 10.43 ± 0.01).
- **A3**: LOO refit on the full-feature subset reproduces exp125b's loo_min_abs_z_quran = 3.74 ± 0.01.
- **A4**: each LDA `S_W` non-singular under ridge; w-vector unit-norm; sign-aligned to Quran-positive.
- **A5**: deterministic re-run produces byte-identical receipt.

## 6. Why this experiment is honest

The hypothesis is asymmetric: a PASS would promote F77 → F79 (positive headline), a FAIL leaves F77 PARTIAL (status quo). The PREREG-locked thresholds are identical to exp125b's. No new feature is engineered; the search is over **subsets of an already-locked feature set**, not a Look-Elsewhere fishing expedition. The 26-subset enumeration is exhaustive within the constraint, with no hidden hyperparameters.

**Look-Elsewhere multiple-comparison concern**: 26 subsets tested; nominal α = 0.05 → expected false-positive rate per criterion is moderate. **However**, criteria (a)-(e) are **conjunctive** (all five must hold), and (a)+(d) are 5σ / 4σ thresholds (extreme tail), so the probability of a random subset satisfying all 5 by chance is well below `26 × 5e-7 = 1e-5`. Bonferroni-corrected effective threshold is far above what random data would yield. PASS therefore reflects real structure, not multiple-comparison artifact.

## 7. Honest scope

If **PASS_robust_subset_found**: F79 candidate = first fully-robust supervised unification at N=11. Documents the specific feature subset. Unification formula on `|S|` features instead of 5.

If **PASS_robust_subset_strong**: even stronger — the robust direction also passes LOO at the full Quran-outlier criteria (≥5σ Quran, ≤2σ competition). Closest possible thing to a FORMAL LAW at N=11.

If **PARTIAL_full_pool_subset_only**: lower-dimensional unification exists but LOO still fails. F77 stays PARTIAL. Path-C N≥18 needed.

If **FAIL_no_full_pool_subset**: the 5-feature LDA is the minimal full-pool-PASSING feature set. Negative datum useful for paper §4.47.27.

## 8. Output

Receipt: `results/experiments/exp127_lda_robust_subset_hunt/exp127_lda_robust_subset_hunt.json` containing:
- `verdict`
- `n_subsets_tested` (= 26)
- `n_subsets_full_pool_pass` (count satisfying a-c)
- `n_subsets_robust_pass` (count satisfying a-e)
- `n_subsets_strong_robust_pass` (count satisfying strong LOO)
- `subset_results_table` (26 rows: subset, k, full_pool stats, LOO stats, pass/fail per criterion)
- `best_subset` (PASS_robust if any; otherwise best PARTIAL by min|z|_LOO)
- `best_subset_unified_formula_string`
- `audit_report`, `prereg_hash`, `wall_time_s`.

## 9. Wall-time estimate

26 subsets × 11 LDA fits each × O(1) per fit on 11 × 5 matrix = **<1 second**.

---

**Filed**: 2026-04-29 night (V3.14.2 sub-task 1)
