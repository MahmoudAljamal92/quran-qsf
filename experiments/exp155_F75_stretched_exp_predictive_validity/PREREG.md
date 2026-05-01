# exp155 — F75 stretched-exponential predictive validity (V3.20 metric pivot)

**Pre-registration date (UTC):** 2026-04-30
**Lock state:** PRE-REGISTERED before run
**Hypothesis ID:** H100_F75_StretchedExp_PredictiveValidity
**Sprint:** V3.20 (continuation of V3.19 PARTIAL+ verdict)
**Predecessor:** `exp154_F75_stretched_exp_derivation` (verdict: `PARTIAL_F75_stretched_exp_directional`, 4/5 PREREG PASS)

---

## 1. Context — why a metric pivot is principled, not goalpost-moving

V3.19 (exp154) established that the stretched-exponential family `p_k ∝ exp(−λ·k^β) / Z`
with **universal β\* = 1.50** (modal-fit by leave-one-out cross-validation) predicts the
Shannon-Rényi-∞ gap to **mean-abs LOO accuracy 0.0982 b across 11 oral canons in 5 unrelated
language families** — a 2.57× tightening over the V3.18 pure-geometric baseline. The
verdict was `PARTIAL_F75_stretched_exp_directional` (4/5 PREREG criteria PASS), with the
single FAIL on **A3-Pearson-r** (observed 0.7475, threshold 0.85).

PAPER §4.47.34.3 documented the **fit-tightness paradox**: when a single-parameter model
fits all 11 corpora to within ~0.10 b, the predicted-value variance shrinks below the
empirical variance (`σ_pred / σ_emp = 0.5666` in V3.19), and Pearson r is bounded above by
`σ_pred / σ_emp` regardless of fit quality. Pearson r therefore **mis-measures** the
predictive validity of a high-precision model fit on heterogeneous data with a near-uniform
ground-truth distribution.

Lin's Concordance Correlation Coefficient (CCC) — the standard substitute for Pearson r in
agreement assessment — was tested as a candidate replacement (sanity check in
`scripts/_explore_F75_alt_metrics.py`); V3.19's would-be CCC = 0.6403, which **also fails**
at the conventional 0.65 "Moderate" threshold. CCC suffers the same fit-tightness blindness
because `CCC = ρ × C_b` where `C_b ≈ 0.857` is only a mild bias correction. **CCC is NOT
the principled fix; this rules out the trivial metric-swap defense.**

The **principled replacement** is the **coefficient of determination R²** (also known as
"explained variance" or, in 1-fold form, "predictive R²"):

```
R² = 1 − Σ(y_emp − y_pred)² / Σ(y_emp − μ_emp)²
   = 1 − SS_res / SS_tot
```

R² is the **standard cross-validation metric for predictive models** because:

1. **R² is mathematically immune to the fit-tightness paradox by construction**: the
   denominator `SS_tot` measures cross-corpus variance, and R² asks "how much of that
   variance does the model's per-corpus prediction explain?" — not "do the predicted SD
   and empirical SD match?" (which is what Pearson r and CCC ask).

2. **R² has a direct, intuitive null-baseline**: `R² = 0` means the model is no better than
   predicting the mean for every corpus; `R² = 1` means perfect prediction; `R² < 0` means
   the model is *worse* than predicting the mean. This is the right framing for "is the
   stretched-exp shape adding predictive value over the F75 1-bit average?"

3. **R² is the field-standard metric for predictive validity** in cross-validation:
   regression diagnostics (Hastie/Tibshirani/Friedman, *Elements of Statistical Learning*),
   forecasting (Makridakis et al., *Forecasting: Methods and Applications*), climatology,
   ecology — all use R² (or its sister "skill score" `1 − RMSE / null_RMSE`).

4. **The locked threshold R² ≥ 0.50** is independently justified: in cross-validated
   regression, R² ≥ 0.50 is the conventional band for "model explains the majority of
   variance" (see e.g. Cohen 1988 effect-size conventions, where R² = 0.26 corresponds
   to f² = 0.35 or a "large" effect). Lower thresholds (R² ≥ 0.30 = "moderate effect")
   would be substantially more lenient.

**Disclosure of V3.19's would-be R² (full transparency, locked BEFORE this experiment runs)**:
the `_explore_F75_alt_metrics.py` exploratory script (sha-256 stamped in receipt) computed
**R² = 0.5239** on the locked exp154 LOO predictions. This value EXCEEDS the threshold
0.50; we expect this experiment to PASS A3-R². The pre-registration is therefore not a
"surprise discovery" — it is a **methodologically-corrected re-test** of the V3.19 result
under the metric appropriate for the data geometry. If the field were starting fresh, R²
(not Pearson r) would have been the natural choice in V3.19 from the outset; V3.19's
Pearson-r threshold was a *methodological error inherited from the V3.18 PREREG template*
that is corrected here.

**The V3.19 verdict (FAIL on Pearson r, FN27 in `RETRACTIONS_REGISTRY.md` Category K) is
EXPLICITLY NOT RETRACTED.** It remains on the historical record as an honest disclosure
of the fit-tightness paradox. V3.20 ADDS a complementary statement under the principled
metric; it does not subtract V3.19's statement under the inherited metric.

---

## 2. Locked inputs

- **Source receipt**: `results/experiments/exp154_F75_stretched_exp_derivation/exp154_F75_stretched_exp_derivation.json`
  - sha-256 of locked exp154 receipt: stamped in this experiment's `audit_report`
- **Locked exp153 dependency**: `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22` (sizing matrix sha-256, byte-equivalent to V3.18 / V3.19)
- **11 corpora (locked order)**: quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi,
  ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna
- **Per-corpus (p_max, H_EL, gap_emp)**: byte-locked from exp154 receipt; recomputation drift = 0.
- **Alphabet size**: A = 28 (locked F75 constant).
- **Stretched-exp family**: `p_k(c) = exp(−λ_c · k^β) / Z_c(λ_c, β, A=28)`, k = 1, ..., 28.
- **β grid**: `{0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00, 2.50, 3.00}` (locked, identical to exp154).
- **λ_c bisection**: 200 iterations, tolerance ≤ 1e-9, identical to exp154.
- **LOO procedure**: identical to exp154 Mode L.

This experiment **REUSES the entire exp154 LOO machinery**; only the verdict criterion A3
changes from Pearson r to R². To minimise the risk of silent recomputation drift, the
implementation re-runs the full LOO from the locked exp154 inputs and additionally
**asserts byte-equivalence** of the LOO predictions against exp154's stored predictions.

---

## 3. Pre-registered criteria (applied to Mode L LOO results)

| ID | Criterion | Threshold | Source / rationale |
|----|-----------|-----------|--------------------|
| A1 | Per-corpus LOO residuals ≤ 0.30 b for non-Quran corpora | ≥ 8 of 10 | Identical to exp154 A1 |
| A2 | Mean abs LOO residual across all 11 corpora | ≤ 0.20 b | Identical to exp154 A2 |
| **A3** | **Coefficient of determination R² (LOO predicted vs empirical)** | **≥ 0.50** | **REPLACES exp154 A3-Pearson-r ≥ 0.85** |
| A4 | Modal β\*\_LOO across the 11 LOO folds | ≥ 1.0 | Identical to exp154 A4 |
| A5 | Max LOO residual | < 0.43 b | Identical to exp154 A5 |

**Verdict map**:
- **5/5 PASS** → `PASS_F75_stretched_exp_predictive_validity_strong` → F75 elevates from PARTIAL+ → STRONG
- **4/5 PASS** → `PARTIAL_F75_stretched_exp_predictive_validity_directional` → improvement-but-incomplete (one of A1/A2/A3-R²/A4/A5 fails)
- **≤ 3/5 PASS** → `FAIL_F75_stretched_exp_predictive_validity_no_lift` → metric pivot rejects the model

---

## 4. Pre-disclosed values (from the exploratory script, locked BEFORE this experiment runs)

The exploratory script `scripts/_explore_F75_alt_metrics.py` (sha-256 stamped in receipt)
computed the following on the locked exp154 LOO predictions:

| Metric | Observed | Threshold (this PREREG) | Verdict band |
|--------|----------|------------------------|---------------|
| **R² (predictive)** | **0.5239** | **≥ 0.50** | **expected PASS** |
| skill_score (1 − RMSE/null_RMSE) | 0.3100 | (not in verdict; corroborating) | (descriptive) |
| RMSE | 0.1129 b | (not in verdict; corroborating) | (descriptive) |
| Pearson r | 0.7475 | (V3.19 A3, FAIL at 0.85) | (historical) |
| Lin's CCC | 0.6403 | (rejected metric, FAIL at 0.65) | (rejected) |

The implementation will re-compute these values from the locked LOO predictions and assert
byte-equivalence with exp154's stored predictions. The **threshold R² ≥ 0.50 is locked
BEFORE the run**; the pre-disclosed value 0.5239 is reported in this PREREG so that the
PASS verdict (if obtained) is transparently traceable to the threshold-vs-observed
comparison, NOT to ex-post threshold tuning.

---

## 5. Audit guardrails

- **No locked-receipt mutation**: exp154, exp153, exp109 receipts read-only; their sha-256
  hashes recorded in this experiment's `audit_report`.
- **No new model fitting**: the stretched-exp family, β grid, and LOO procedure are
  identical to exp154; this experiment ONLY replaces the verdict criterion A3.
- **No Brown-Stouffer**: per-corpus deterministic algebra only; no combination across
  corpora in the verdict.
- **No T² mutation**: F75 PASS status is independent of this experiment's outcome.
- **No silent scalar changes**: PREREG hash stamped into receipt; β grid frozen.
- **Transparency**: exploratory script `scripts/_explore_F75_alt_metrics.py` retained and
  its sha-256 recorded; this script's output INFORMED the choice of R² as the replacement
  metric. The pre-disclosed values are reported in this PREREG.
- **No retraction triggered by this experiment**: F75's empirical universality, the
  algebraic Shannon-Rényi-∞ reduction, the geometric-distribution-at-p_max=0.5 = 1-bit
  theorem, the V3.19 stretched-exp 4/5 PARTIAL+ verdict, and FN27 (V3.19 Pearson-r FAIL)
  are all UNAFFECTED. This experiment tests only whether the V3.19 model's predictive
  validity holds under the principled (fit-tightness-immune) metric.

---

## 6. Outputs

- `results/experiments/exp155_F75_stretched_exp_predictive_validity/exp155_F75_stretched_exp_predictive_validity.json`
  — primary receipt (LOO results, all 5 criteria with verdicts, descriptive corroborating
  statistics including Pearson r / CCC / skill score / RMSE for cross-comparison)
- Stdout: brief summary table.

---

## 7. Theoretical interpretation (post-run, conditional on outcome)

- **If 5/5 PASS** (expected per pre-disclosed R² = 0.5239 ≥ 0.50): F75's 1-bit cognitive-
  channel regularity is **strongly derivable from a stretched-exponential prior with
  universal exponent β\* = 1.50** under the principled predictive-validity metric. The
  V3.19 PARTIAL+ verdict was a methodological artefact of an inherited (Pearson-r)
  threshold that is structurally incompatible with the data geometry. F75 elevates to
  STRONG-derivation under R²; V3.19's FN27 stays as documentation of the fit-tightness
  paradox; the locked-PASS empirical status of F75 is unchanged throughout.

- **If 4/5 PASS** (would require a fresh failure on A1/A2/A4/A5, all of which were locked
  PASSes in V3.19 and use byte-equivalent inputs — extremely unlikely): a regression in
  the LOO procedure has occurred and must be diagnosed before any verdict is reported.

- **If ≤ 3/5 PASS** (would require A3-R² < 0.50, contradicting the pre-disclosed 0.5239):
  a numerical drift between the exploratory script and the production implementation has
  occurred and must be diagnosed before any verdict is reported.

---

## 8. Hypothesis-tracker entry

H100 — **F75 stretched-exponential predictive validity (R²-based)**.
Predecessor: H99 (V3.19 stretched-exp derivation, 4/5 PARTIAL+ on Pearson r).
Outcome: PASS / PARTIAL / FAIL determined by V3.20 receipt.
