# exp122_zipf_equation_hunt — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 afternoon, V3.13 candidate sprint, Path B of "B + C in parallel")
**Hypothesis ID**: H77
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time (computed from this file's SHA-256 byte-content prior to first run.py invocation)

---

## 1. The question

Is there a **closed-form Zipf-class equation** `g(features) = c_universal` that holds tightly across the 10 non-Quran corpora of the locked exp109 / exp120 universal pool, with the Quran as the unique global outlier?

If found, this would be the project's first **derived** Quran-distinctiveness law — a single equation, not a multivariate ranking.

## 2. Pool

The locked **11-corpus, 5-feature** matrix from `exp120_unified_quran_code` (input from `results/auxiliary/_phi_universal_xtrad_sizing.json`):

- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`
- **Features (D=5)**: `{VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency}`
- **Per-corpus values**: per-corpus median of each feature over its unit pool (114 sūrahs / 921 chapters / etc.). Frozen at `_phi_universal_xtrad_sizing.json` SHA-256 (re-verified at run time).

## 3. Candidate space

Exhaustive evaluation of ~400 candidate functional forms across 4 categories:

**Cat-1 (single-feature transforms, ~30 candidates)**:
- `f`, `log(f)`, `log(1−f)`, `sqrt(f)`, `1/f`, `f²` — for each of the 5 features

**Cat-2 (two-feature compositions, ~150 candidates)**:
- `f_i · f_j`, `f_i / f_j`, `f_i + f_j`, `f_i − f_j`, `f_i² + f_j²`, `f_i + log(f_j)`

**Cat-3 (three-feature compositions, ~200 candidates)**:
- `f_i · f_j / f_k`, `f_i / (f_j · f_k)`, `f_i + f_j − f_k`, `(f_i · f_j) − f_k`

**Cat-4 (information-theoretic combinations, ~30 candidates)**:
- `H_EL / log₂(28)` (alphabet-normalised, dimensionless)
- `H_EL + log₂(p_max · 28)`
- `H_EL · p_max`
- `−p log p − (1−p) log(1−p)` (binary entropy of p_max)
- `gzip_efficiency · bigram_distinct_ratio · log(28)` (effective alphabet usage)
- `VL_CV · p_max` (rhyme × verse-consistency coupling)

**Total: ≤ 500 candidates**, deduplicated. NaN/inf-producing transforms are skipped (recorded in receipt).

## 4. Acceptance criteria (pre-registered, frozen)

A candidate `g` is classified as **Zipf-class PASS** iff **all three** conditions hold:

- **(a) Tight cluster across non-Quran**: `CV_non_quran(g) := std(g_{c∈non_quran}) / |mean(g_{c∈non_quran})| < 0.10` (10 % spread).
- **(b) Quran is extreme outlier**: `|z_quran(g)| := |g_quran − mean_non_quran| / std_non_quran ≥ 5.0` (5-sigma).
- **(c) No competing outliers**: `max_{c≠quran} |z_c(g)| ≤ 2.0` (no second corpus is also an outlier).

Threshold (b) of 5σ is chosen because: under a one-tailed Gaussian, p < 3·10⁻⁷; after Bonferroni on 500 candidates, family-wise α' = 1.5·10⁻⁴ < 0.05.

A candidate is **Zipf-class PARTIAL** iff (b) holds with `|z| ≥ 3.0` but (a) or (c) fails — the Quran is extreme but the relation isn't tight or has competing outliers.

## 5. Verdict ladder

- `PASS_zipf_class_equation_found` — at least one candidate satisfies all three criteria. Report the top 5 by tightness × outlier strength.
- `PARTIAL_only_outlier_no_tightness` — candidates exist with `|z| ≥ 5` but none satisfy `CV < 0.10`. The Quran is extreme but no universal equation exists.
- `PARTIAL_only_tightness_no_outlier` — tight equations exist (`CV < 0.10`) but none have Quran at `|z| ≥ 5`. Universal laws exist but Quran isn't distinctive on them.
- `FAIL_no_zipf_class_equation` — no candidate satisfies even `|z| ≥ 3.0` AND `CV < 0.20`. Honest null: the project's Quran-distinctiveness is empirical only, not derivable.
- `FAIL_audit_*` — input sizing receipt SHA-256 mismatch, NaN proliferation, etc.

## 6. Audit hooks

- **A1**: input sizing receipt SHA-256 must match `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22` (locked from `_phi_universal_xtrad_sizing.json` at PREREG seal).
- **A2**: feature names match `FEATURE_NAMES` exactly (no reordering).
- **A3**: corpus names match `EXPECTED_CORPORA` exactly (N=11).
- **A4**: candidate-evaluation determinism: re-run produces byte-identical receipt.
- **A5**: Bonferroni threshold satisfied — best candidate's `|z| ≥ 5` AND `n_candidates_evaluated ≤ 500`.

## 7. What this experiment does NOT do

- It does **not** test an extended pool (Path C handles that). PREREG is locked to the 11-corpus pool of exp120.
- It does **not** generate new corpora or new features. It is a re-analysis of locked data.
- It does **not** make theological / metaphysical claims. A passing candidate is a *descriptive* mathematical relation; its mechanistic interpretation is left to §4.47 of `PAPER.md`.
- It does **not** prove the equation is fundamental — only that it holds tightly on the 11-corpus pool. Extension to N ≥ 22 is the cross-validation test (Path C-validated rerun).

## 8. Honest scope

This experiment **searches** a finite space of ~500 candidates. If it finds a hit:
- The hit is a **Bonferroni-corrected** discovery, not a free single-shot test.
- The hit must **survive** Path C's pool extension (N ≥ 14) to be promoted to F-row.
- The hit's **mechanistic interpretation** is exploratory until validated.

If it finds nothing:
- Honest null result: the Quran-extremum is empirical only.
- Documented as `FAIL_no_zipf_class_equation`; project records that its strongest claim remains a multivariate ranking (F72 D_QSF), not a closed-form equation.

## 9. Output

Receipt: `results/experiments/exp122_zipf_equation_hunt/exp122_zipf_equation_hunt.json` containing:
- `verdict` (one of the 5 ladder values above)
- `n_candidates_evaluated`
- `n_skipped` (NaN/inf)
- `top_5_by_passing` (list of candidate descriptors with full per-corpus values, z-scores, CV)
- `top_5_by_z_only` (regardless of CV — descriptive)
- `top_5_by_cv_only` (universal laws regardless of Quran)
- `audit_report`
- `prereg_hash`, `seed`, `wall_time_s`

## 10. Wall-time estimate

Pure Python, 11 × 500 = 5,500 evaluations. Each is constant-time arithmetic. Expected wall-time: < 1 s.

---

**Filed**: 2026-04-29 afternoon (V3.13 candidate Path B Step 1)
