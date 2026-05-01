# exp154 — F75 stretched-exponential derivation (Task B extension)

**Pre-registration date (UTC):** 2026-04-30
**Lock state:** PRE-REGISTERED before run
**Hypothesis ID:** H99_F75_StretchedExp_Derivation
**Sprint:** V3.19 (continuation of V3.18 partial derivation)
**Predecessor:** `exp153_F75_derivation_check` (verdict: `FAIL_F75_geometric_derivation_no_match`, 3/5 PREREG PASS)

---

## 1. Context

V3.18 established F75 as algebraically equivalent to the **Shannon-Rényi-∞ gap** `H_1 - H_∞`,
with empirical mean ≈ 0.94 ± 0.12 bits across 11 oral canons. The pure-geometric
single-parameter derivation (`p_k = (1-r)·r^(k-1)`) achieved only 3/5 PREREG criteria:

- **A1** (≥ 8/10 non-Quran residuals ≤ 0.30 b): **6/10 FAIL**
- **A2** (mean abs residual ≤ 0.25 b): **0.252 b FAIL**
- A3 (Pearson r ≥ 0.70): 0.744 PASS
- A4 (gap_geom(0.5) = 1.00 exact): PASS
- A5 (Quran rank-1 lowest gap): PASS

**Empirical pattern from exp153**: `gap_geom > gap_emp` for **10 of 11 corpora**, indicating
real verse-final-letter distributions are **MORE concentrated** than pure geometric for the
same `p_max`. A successful 2-parameter family must therefore admit **super-geometric tail
decay** — i.e., be **steeper than exp(-k)** beyond the dominant letter.

Two candidate families satisfy this:

- **M1 (mixture-with-uniform)**: `p_k = w·(1-r)·r^(k-1) + (1-w)/A`. Dilutes geometric with
  uniform background. **Empirically does NOT help** (dilution is in the wrong direction;
  see exploratory analysis in `scripts/_explore_F75_mixture.py`).

- **M2 (stretched exponential)**: `p_k ∝ exp(-λ·k^β) / Z(λ, β, A=28)` with β > 1 giving
  super-geometric concentration. **Empirically works** (β ≈ 1.5 yields ~10/10 A1 and
  mean_abs ≈ 0.10 b in exploratory fit).

This pre-registration commits to M2 as the **primary** family with full leave-one-out
cross-validation and reports M1 as a **documented-failure** alternative. The exploratory
script that revealed M2's superiority is included verbatim in the receipt for full
disclosure.

---

## 2. Locked inputs

- **Source receipt**: `results/experiments/exp153_F75_derivation_check/exp153_F75_derivation_check.json`
  - sha-256 of input feature matrix (`results/auxiliary/_phi_universal_xtrad_sizing.json`):
    `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22`
- **11 corpora (locked order)**: quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi,
  ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna
- **Per-corpus (p_max, H_EL)**: byte-locked from exp153 receipt; recomputation drift = 0.
- **Empirical gap**: `gap_emp(c) = H_EL(c) + log₂(p_max(c))` (Shannon-Rényi-∞ gap).
- **Alphabet size**: A = 28 (locked F75 constant).

---

## 3. Primary model: stretched exponential (M2)

### 3.1 Family

For each corpus `c` with empirical `p_max(c)`:

```
p_k(c) = exp(-λ_c · k^β) / Z_c(λ_c, β)        for k = 1, ..., 28
Z_c    = Σ_{k=1}^{28} exp(-λ_c · k^β)
```

- **β** is **universal** (single global parameter, shared across all 11 corpora).
- **λ_c** is **per-corpus**, fit by bisection s.t. `p_1(c) = p_max(c)`.
- This family reduces to **pure exponential / discrete-geometric-like** at β = 1, and to
  **gaussian-like** at β = 2.

### 3.2 Predicted observable

Predicted Shannon entropy per corpus:
```
H_EL_pred(c)  = -Σ_{k=1}^{28} p_k(c) · log₂(p_k(c))
gap_pred(c)   = H_EL_pred(c) + log₂(p_max(c))
residual(c)   = | gap_pred(c) - gap_emp(c) |
```

### 3.3 Pre-registered β grid

`β ∈ {0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00, 2.50, 3.00}`

Optimization criterion: **β\* minimizes SSR(β) = Σ_c residual(c, β)²** over the grid.

### 3.4 Cross-validation protocol (Mode L — primary verdict input)

For each held-out corpus `c_h`:

1. Restrict to the other 10 corpora.
2. Compute SSR_LOO(β) on those 10; choose β\*\_LOO(c_h) on the pre-registered grid.
3. Use β\*\_LOO(c_h) and `p_max(c_h)` to fit `λ_{c_h}` and predict `H_EL_pred(c_h)`.
4. Record `residual_LOO(c_h) = | gap_pred(c_h) - gap_emp(c_h) |`.

This eliminates in-sample β-tuning bias.

### 3.5 In-sample reference (Mode P — sensitivity only)

In addition to LOO, the receipt records the global β\* (minimizing all-11-corpora SSR)
and the in-sample residuals at β\*. **Mode P is reported for transparency only and does
NOT enter the PASS/FAIL verdict.**

---

## 4. Pre-registered criteria (applied to Mode L LOO results)

| ID | Criterion | Threshold | Note |
|----|-----------|-----------|------|
| A1 | Per-corpus LOO residuals ≤ 0.30 b for non-Quran corpora | ≥ 8 of 10 | Strict; matches exp153 A1 |
| A2 | Mean abs LOO residual across all 11 corpora | ≤ 0.20 b | Tighter than exp153 (0.25); demands real improvement |
| A3 | Pearson r between gap_pred_LOO and gap_emp | ≥ 0.85 | Tighter than exp153 (0.70) |
| A4 | Modal β\*\_LOO across the 11 LOO folds | ≥ 1.0 | Confirms super-geometric concentration (β=1 = pure exponential ≈ geometric) |
| A5 | Max LOO residual | < 0.43 b | Improves on pure-geometric worst (0.427 b, avestan_yasna) |

**Verdict map**:
- **5/5 PASS** → `PASS_F75_stretched_exp_strong` → F75 elevates from PARTIAL → STRONG-derivation
- **4/5 PASS** → `PARTIAL_F75_stretched_exp_directional` → improvement-but-incomplete
- **≤ 3/5 PASS** → `FAIL_F75_stretched_exp_no_lift` → model rejected; F75 remains PARTIAL at V3.18 framing

---

## 5. Sensitivity analysis (M1, mixture-with-uniform — NOT verdict-bearing)

The receipt also fits **Model M1** for transparency:

```
p_k(c) = w·(1-r_c)·r_c^(k-1) + (1-w)/28
```

- Universal `w` over grid `{0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.96, 0.98, 0.99, 0.995, 0.999}`.
- Per-corpus `r_c` solved analytically from `p_max(c)`.
- **Expected outcome (per exploratory analysis)**: optimal w\* → 1, residuals do not improve
  meaningfully on pure geometric. M1 will be reported as **failed alternative** in the
  receipt's sensitivity block, NOT applied to PASS/FAIL.

---

## 6. Audit guardrails

- **No locked-receipt mutation**: exp153 and exp109 receipts read-only; their sha-256 hashes
  recorded in this receipt's `audit_report`.
- **No Brown-Stouffer**: per-corpus deterministic algebra only; no combination across corpora
  in the verdict.
- **No T² mutation**: F75 PASS status is independent of this experiment's outcome (F75 holds
  empirically regardless of which derivation is correct).
- **No silent scalar changes**: PREREG hash stamped into receipt; β grid and w grid frozen.
- **Transparency**: exploratory script `scripts/_explore_F75_mixture.py` retained and its
  sha-256 recorded; this script's output INFORMED the choice of M2 as primary.
- **No retraction triggered by this experiment**: F75's empirical universality, the
  algebraic Shannon-Rényi-∞ reduction, and the geometric-distribution-at-p_max=0.5 = 1-bit
  theorem are all UNAFFECTED. This experiment tests only whether a 2-parameter family
  improves on pure geometric.

---

## 7. Outputs

- `results/experiments/exp154_F75_stretched_exp_derivation/exp154_F75_stretched_exp_derivation.json`
  — primary receipt (β grid sweep, LOO results, M1 sensitivity, all 5 criteria with verdicts)
- Stdout: brief summary table.

---

## 8. Theoretical interpretation (post-run, conditional on outcome)

- **If 5/5 PASS**: F75's 1-bit cognitive-channel regularity is **derivable from a stretched-
  exponential prior** with universal exponent β\* > 1. The substantive interpretation is that
  verse-final-letter cascades follow super-geometric decay — likely arising from **finite
  working-memory constraints** that compress the secondary-letter distribution beyond pure
  geometric memorylessness. F75 elevates to STRONG-derivation.

- **If 4/5 PASS**: stretched exponential is directionally correct but quantitatively
  incomplete. F75 remains PARTIAL but with stronger framing.

- **If ≤ 3/5 PASS**: stretched exponential is rejected; F75 remains at V3.18 PARTIAL with
  no improvement. The cognitive-channel conjecture remains untestable from per-corpus
  (p_max, H_EL) alone.

---

## 9. Hypothesis-tracker entry

H99 — **F75 stretched-exponential derivation**.
Predecessor: H98 (V3.18 geometric derivation, FAIL 3/5).
Outcome: PASS / PARTIAL / FAIL determined by V3.19 receipt.
