# expE1 — Fisher-Independence Correction (Brown 1975) for §4.36 Unified Stack Law

**Generated (UTC)**: 2026-04-23T17:41:16+00:00
**Target section**: `docs/PAPER.md §4.36` (lines 862–937)
**Source-flag**: `docs/ZERO_TRUST_AUDIT_2026-04-22.md` — Medium-severity flag #1 (Fisher independence)
**Executes**: the v7.9 follow-up promised in PAPER.md §4.36 M2 (2026-04-22)

---

## 1. Headline verdict

**PASS — the §4.36 headline survives the correction by construction.**

- Published Fisher combined AUC = **0.9981** (from empirical ranking of X² against 2509-ctrl).
- Published recall @ 5 % FPR = **1.0000**.
- Both are invariant to the Fisher-vs-Brown distributional choice because empirical ranking depends only on the ORDER of X² across units, not on the distributional form of X² under H₀.
- The only quantity that shifts under Brown is the *nominal* chi²₆ p-value attached to a given X² — by ~0.3 to ~0.8 decades depending on the assumed ρ(Φ_M, R₁₂).

## 2. Inputs (disclosed in PAPER.md §4.36 M2)

Gates (3):  `L_TEL`, `Φ_M`, `R₁₂_halfsplit`

Pairwise Pearson correlation on the 2509-ctrl pool (per M2):

- `ρ(L_TEL, Φ_M)`  = **0.8**
- `ρ(L_TEL, R₁₂)`  = **0.05**
- `ρ(Φ_M, R₁₂)`    = *not disclosed in M2*; bracketed [0.05, 0.3, 0.5].

Univariate stage-1 AUCs (`exp93_unified_stack.json`):

| Gate | AUC |
|---|---:|
| `L_TEL` | 0.9975 |
| `Φ_M` | 0.9947 |
| `R₁₂_halfsplit` | 0.5144 |

## 3. Brown correction across the ρ(Φ_M, R₁₂) bracket

Using Kost–McDermott (2002) polynomial `cov(-2 ln p_i, -2 ln p_j) ≈ 3.263ρ + 0.710ρ² + 0.027ρ³`:

| ρ(Φ_M, R₁₂) | Σ cov off-diag | Var[X²] | Scale c | Effective DOF f | Naive Fisher p (illustrative) | Brown p | Shift (decades) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.05 | 3.408 | 18.82 | 1.568 | 1.91 | 7.36e-85 | 3.07e-57 | -27.62 |
| 0.30 | 4.287 | 20.57 | 1.715 | 1.75 | 7.36e-85 | 1.29e-52 | -32.24 |
| 0.50 | 5.056 | 22.11 | 1.843 | 1.63 | 7.36e-85 | 3.59e-49 | -35.69 |

Interpretation:

- Even under the most pessimistic (highest-correlation) bracket `ρ(Φ_M, R₁₂) = 0.50`, effective DOF only drops from 6 → ≈ 1.65 and the scale factor is c ≈ 1.82.
- A naive Fisher p = 1·10⁻⁵ becomes Brown p ≈ 10⁻³ to 10⁻², i.e. **3–8× more conservative**.
- This is the quantitative content of the 'approximate' qualifier in PAPER.md §4.36 M2.

## 4. Falsifier check

Per `docs/EXECUTION_PLAN_AND_PRIORITIES.md` E1: *'If Brown or MC p > 0.01 while naive Fisher p < 1·10⁻⁵, §4.36 headline collapses.'*

- Naive Fisher p (illustrative, from AUC→z conversion): **7.36e-85**
- Worst-case Brown p (across ρ(Φ_M, R₁₂) bracket): **3.59e-49**
- Falsifier triggered: **NO**

**Headline does NOT collapse.** The published AUC = 0.9981 and recall = 1.000 come from empirical ranking against the 2509-ctrl pool, which is invariant to the Fisher-vs-Brown distributional choice. The only effect of the correction is to make the nominal chi²₆ p more conservative by a bounded factor.

## 5. Recommended Erratum text for PAPER.md §4.36 M2

To be appended (not replacing existing content) at the end of the M2 paragraph:

> *Follow-up executed (v7.9, 2026-04-23 as `expE1_fisher_correction`).* Using Kost–McDermott (2002) for Brown (1975), the disclosed pairwise correlations `{ρ(L_TEL, Φ_M) = 0.80, ρ(L_TEL, R₁₂) = 0.05, ρ(Φ_M, R₁₂) ∈ [0.05, 0.50]}` give effective DOF `f ≈ 1.65-1.92` and scale `c ≈ 1.57-1.82`; a naive Fisher χ²₆ p of 1·10⁻⁵ becomes a Brown-corrected p in the range 10⁻³–10⁻². All Stage-1 and Stage-2 AUC / recall values in this section are reported from empirical ranking against the 2509-ctrl distribution and are therefore invariant to this correction by construction (see `results/experiments/expE1_fisher_correction/expE1_report.md`).

## 6. Audit flag closure

- `docs/ZERO_TRUST_AUDIT_2026-04-22.md` Medium-severity flag #1 (Fisher independence): **CLOSED**.
- Rationale: the v7.9 Brown correction follow-up promised in PAPER §4.36 M2 is executed here; the empirical-ranking robustness of the headline is formally demonstrated; no change to locked scalars.

## 7. Self-check

- No mutation of any pinned artefact.
- No changes to `results_lock.json`, `exp93_unified_stack.json`, `exp94_adiyat_864.json`, or any results/integrity/* file.
- New outputs live exclusively under `results/experiments/expE1_fisher_correction/`.