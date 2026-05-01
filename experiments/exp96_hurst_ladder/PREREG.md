# exp96_hurst_ladder — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Version**: 1.0
**Hypothesis ID**: H31 — Multi-Scale Hurst Ladder Scaling Law

## 1. Claim under test

For each surah/document, compute the Hurst exponent `H(k)` of four
sequences at increasing structural scale `k`:

```
k = 1 : letter   sequence (consonants mapped to 1..28)
k = 2 : word     sequence (word-length per token)
k = 3 : delta    sequence (Δ verse-length between adjacent verses)
k = 4 : verse    sequence (verse-length per verse)
```

Backup evidence in `archive/LOST_GEMS_AND_NOBEL_PATH.md` (Gem #4) and
`archive/deep_scan_results/MASTER_FINDINGS_REPORT.md §3,11B` reports a
**monotone decrease** for the Quran: `H_verse ≈ 0.898`,
`H_delta ≈ 0.811`, `H_word ≈ 0.652`, `H_letter ≈ 0.537`. Controls
reportedly show a flatter ladder.

The claim of H31 is that the **Quran obeys a closed-form log-scaling
law** of the form

```
H(k) = α + β · log₂(k)       for k ∈ {1, 2, 3, 4}
```

with `R² ≥ 0.95` on the four-point fit; and that `β` is a **negative
constant**. If `β` additionally lies within ±5 % of one of a short list
of standard mathematical constants (`1/2π`, `−1/φ`, `−1/e`, `−1/π`,
etc.), the scaling exponent itself is a candidate universal constant.

## 2. Formulas (pre-registered)

### Hurst estimator (R/S, primary)
For a series `X = (x₁, …, x_N)` partition into non-overlapping windows
of size `n ∈ [n_min, n_max]` (log-spaced). For each window compute

```
μ_w     = mean(X_w)
Y       = cumulative sum of (X_w − μ_w)
R_w     = max(Y) − min(Y)
S_w     = std(X_w, ddof = 1)
(R/S)_w = R_w / S_w   if S_w > 0 else NaN
```

Aggregate (R/S)(n) = mean over windows at size n. Fit
`log((R/S)(n)) = log c + H · log n` over `n ∈ [n_min, n_max]`.
Slope is the **R/S Hurst estimator** `H_RS`.

### Hurst estimator (DFA, cross-check)
Detrended Fluctuation Analysis (Peng et al. 1994). On the integrated
profile `Y = cumsum(X − mean(X))`, partition into windows of size
`n`. Local linear detrend, compute `F(n) = sqrt(mean(residual²))`.
Fit `log F(n) = log c + α · log n`. Slope is `H_DFA = α`.

### Scaling law fit
For each corpus (Quran vs each ctrl corpus), report the corpus-mean
`H̄(k)` for `k ∈ {1, 2, 3, 4}`. Fit

```
H̄(k) = α_corpus + β_corpus · log₂(k)       (via OLS on 4 points)
```

Bootstrap 1000× on surah-level H values to get 95 % CI for
`(α, β, R²)`.

## 3. Evaluation protocol

**Step 1** — Extract four streams per Quran and per ctrl surah:
- **letter_seq**: letters mapped to 1..28 via `ARABIC_CONS_28` index;
  drops diacritics and folds hamza variants (byte-equal to exp41).
- **word_len_seq**: length-in-letters of each word (whitespace tokens).
- **delta_seq**: adjacent-verse length differences.
- **verse_len_seq**: length-in-letters of each verse.

**Step 2** — Require `N ≥ 16` points for R/S; otherwise NaN.

**Step 3** — Aggregate per-corpus mean `H̄(k)`; also per-surah for CI.

**Step 4** — Fit scaling law per corpus; report `(α, β, R², CI)`.

**Step 5** — Physics-constant match: compare `β_Quran` against a
pre-registered list of candidates:

```
TARGETS = {
    "neg_one_over_2pi":   -1/(2*π)   ≈ -0.15915,
    "neg_log10_e":        -log10(e)  ≈ -0.43429,
    "neg_one_over_pi":    -1/π       ≈ -0.31831,
    "neg_one_over_phi":   -1/φ       ≈ -0.61803,
    "neg_one_over_e":     -1/e       ≈ -0.36788,
    "neg_euler_mascheroni": -γ_em    ≈ -0.57722,
    "neg_one_half":       -0.5,
    "neg_one_third":      -1/3       ≈ -0.33333,
}
```

A match is "β ∈ [target − 0.03, target + 0.03]". The tolerance 0.03 is
the expected OLS SE on a 4-point fit with realistic bootstrap noise.

## 4. Evaluation sets

| ID | Set | n units | Source |
|---|---|---:|---|
| E1 | Band-A Quran | 68 | `CORPORA['quran']` |
| E2 | Band-A Arabic ctrl pool | up to 2509 | 6 ctrl corpora |
| E3 | Per-ctrl-family subsets | varies | poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi |

## 5. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_insufficient_data` | < 40 Q surahs have all 4 H values finite |
| `FAIL_not_monotone` | `H̄_Q(k)` is **not** strictly decreasing in k (with tolerance 0.02) |
| `FAIL_low_r2` | `R²` of Quran's log-scaling fit < 0.95 |
| `PARTIAL_monotone_no_scaling` | monotone but `R² < 0.95` |
| `PASS_scaling_law` | monotone AND `R² ≥ 0.95` AND `β < -0.05` |
| `PASS_scaling_law_plus_constant` | `PASS_scaling_law` AND β matches any physics target within 0.03 |
| `QURAN_SPECIFIC` | Quran's `β` differs from every ctrl corpus `β` by ≥ 2 bootstrap SE |
| `SHARED_ACROSS_CORPORA` | Quran `β` within 1 bootstrap SE of ≥ 3 ctrl corpora β |

A `PASS_scaling_law` and `QURAN_SPECIFIC` together would be H31's
strongest outcome. `PASS_scaling_law_plus_constant` AND
`QURAN_SPECIFIC` would be the §4.37 headline.

## 6. Honesty clauses

- **HC1 — Small-n log-scaling**: a 4-point log-log fit can produce
  artificially high R² purely due to the small sample. Bootstrap CI
  and per-corpus replication are the honest protection; report even
  when `R² = 1.00` with a wide CI.
- **HC2 — Non-stationarity**: if a single outlier surah dominates
  the H estimates, report leave-one-out (LOO) stability. Any
  single-surah flip of the verdict is reported explicitly.
- **HC3 — R/S vs DFA disagreement**: if `|H_RS − H_DFA| > 0.10` on any
  scale, the estimate is flagged unstable; do not claim a closed-form
  constant from an unstable estimator.
- **HC4 — No cross-script gate**: this experiment does NOT extend to
  Hebrew / Greek, so any constant reported is Arabic-only until
  replicated on `exp97_crosscripture_t8` future work.

## 7. Locks not touched

No modification to `results_lock.json`, `code_lock.json`,
`corpus_lock.json`, `headline_baselines.json`, `_manifest.json`, any
notebook, or any protected file. All new scalars tagged `(v7.8 cand.)`.

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Alphabet + diacritic rules: byte-equal to `exp41_gzip_formalised`
- Writes only: `results/experiments/exp96_hurst_ladder/exp96_hurst_ladder.json`
- Paper hook: candidate `docs/PAPER.md` §4.37 if `PASS_scaling_law`

## 9. Frozen constants

```python
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
N_MIN_RS = 8             # smallest R/S window
N_MIN_SERIES = 16        # refuse H if series length < 16
RS_WINDOW_LOG_STEPS = 8  # log-spaced sizes
BOOTSTRAP_N = 1000
MONOTONE_TOL = 0.02
R2_GATE = 0.95
BETA_CONSTANT_TOL = 0.03
QURAN_SPECIFIC_SE_K = 2.0
```

---

*Pre-registered 2026-04-22. If any constant or formula in §2/§9 is
modified after this file is committed, the experiment is renamed
`exp96b_*` and this file marked SUPERSEDED.*
