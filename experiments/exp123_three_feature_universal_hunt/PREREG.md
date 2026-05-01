# exp123_three_feature_universal_hunt — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 evening, V3.14 candidate sprint, sub-task 3 of 3)
**Hypothesis ID**: H80
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

Generalising exp122 (which searched ~500 candidates over 1- and 2-feature combinations and found F75 at CV = 1.94 %), is there a **3-feature closed-form equation** that gives a **TIGHTER universal** (CV < 1 %) across the 10 non-Quran corpora, with the Quran as the unique outlier?

If found, the new candidate F-row would supersede F75 as the project's tightest Zipf-class universal.

## 2. Pool

Identical to exp122 / exp124 / exp125:
- **Corpora (N=11)**: same 11 corpora as locked in `_phi_universal_xtrad_sizing.json`.
- **Features (D=5)**: same 5 features.

## 3. Candidate space

We expand exp122's Cat-3 (which had ~200 three-feature candidates) by exhaustively enumerating:

**Triple-feature compositions** (10 triples × ~20 algebraic forms × ~5 transform pairs):

For each `(f_i, f_j, f_k)` triple from `C(5, 3) = 10` combinations, generate:
- **Sums**: `f_i + f_j + f_k`, `log f_i + log f_j + log f_k`
- **Differences/sums**: `f_i + f_j − f_k`, `f_i − f_j + f_k`, `f_i − f_j − f_k`
- **Products**: `f_i · f_j · f_k`, `sqrt(f_i · f_j · f_k)`
- **Ratios**: `f_i / (f_j · f_k)`, `(f_i · f_j) / f_k`, `(f_i + f_j) / f_k`
- **Information-theoretic**: `f_i + log₂(f_j · f_k · 28)` (F75-class generalisations)
- **Mixed**: `f_i · log₂(f_j) + f_k`, `sqrt(f_i) + f_j · f_k`

Estimated candidates: ~10 triples × ~20 forms = **~200 candidates**.

NaN/inf-producing transforms are skipped (recorded in receipt).

## 4. Acceptance criteria (pre-registered, frozen)

A candidate `g` is **PASS_tighter_than_F75** iff **all four**:
- **(a) STRICTER tightness**: `CV_non_quran(g) < 0.01` (1 % spread, vs F75's 1.94 %)
- **(b) Quran extreme outlier**: `|z_quran(g)| ≥ 5.0`
- **(c) No competing outliers**: `max_{c≠quran} |z_c(g)| ≤ 1.5` (stricter than exp122's 2.0)
- **(d) Genuine 3-feature**: the candidate uses ≥ 2 distinct features beyond just F75's `(p_max, H_EL)` pair

A candidate is **PASS_zipf_class_3feature** iff **all three**:
- **(a) Tightness**: `CV_non_quran(g) < 0.10` (matches exp122's bar)
- **(b) Quran outlier**: `|z| ≥ 5.0`
- **(c) No competitor**: `max_{c≠quran} |z_c(g)| ≤ 2.0`

(This is the same acceptance ladder as exp122 but on 3-feature candidates only.)

A candidate is **PARTIAL_TIGHTER** iff `CV < 0.01` but `|z| < 5` — extreme tightness without Quran-distinctiveness (a non-Quran-specific universal).

## 5. Verdict ladder

```
PASS_tighter_than_F75               (CV<0.01 AND |z|>=5 AND comp|z|<=1.5)
  > PASS_zipf_class_3feature        (CV<0.10 AND |z|>=5 AND comp|z|<=2.0)
  > PARTIAL_TIGHTER                 (CV<0.01 only — universal but not Quran-specific)
  > PARTIAL_3feature_outlier        (|z|>=5 only — Quran-extreme but not tight)
  > FAIL_no_3feature_zipf
  > FAIL_audit_*
```

## 6. Audit hooks

- **A1**: input sizing receipt SHA-256 must match `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22`.
- **A2**: feature names match `FEATURE_NAMES` exactly.
- **A3**: corpus names match `EXPECTED_CORPORA` exactly (N=11).
- **A4**: candidate-evaluation determinism: re-run produces byte-identical receipt.
- **A5**: Bonferroni threshold satisfied — best candidate's `|z| ≥ 5` AND `n_candidates_evaluated ≤ 300`.
- **A6**: at least one candidate uses each pair of features (no triple is trivially excluded).

## 7. What this experiment does NOT do

- It does **not** test 4- or 5-feature combinations (would explode candidate count beyond Bonferroni-safe range; deferred to exp123b if motivated).
- It does **not** test an extended N≥18 pool — Path C is the cross-validation track.
- It does **not** introduce non-feature variables (no corpus-length, no genre-tag, etc.).

## 8. Honest scope

If **PASS_tighter_than_F75**: the project gains a **tighter universal than F75**; the new candidate is the F76-or-F77 candidate (pending exp124/125 verdicts). This would supersede F75 as the headline universal.

If **PASS_zipf_class_3feature** but not tighter: another 3-feature equation exists at F75's tightness level, but doesn't beat it. Multiple-discovery — interesting but not headline-altering.

If **PARTIAL_TIGHTER**: a tight 3-feature universal exists but isn't Quran-distinctive — important honest negative datum showing the universality is general, not Quran-specific.

If **FAIL_no_3feature_zipf**: F75 is essentially as good as the 3-feature search space allows. Honest closure of this exploration.

## 9. Output

Receipt: `results/experiments/exp123_three_feature_universal_hunt/exp123_three_feature_universal_hunt.json` containing:
- `verdict`
- `n_candidates_evaluated` / `n_skipped`
- `top_pass` (3-feature candidates passing all PREREG criteria)
- `top_partial_tighter` (CV<0.01, any z)
- `top_3feature_by_z`
- `top_3feature_by_cv`
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 10. Wall-time estimate

Pure Python, ~200 candidates × 11 evaluations = ~2,200 evaluations of constant-time arithmetic. Expected wall-time: < 0.5 s.

---

**Filed**: 2026-04-29 evening (V3.14 candidate sprint, sub-task 3)
