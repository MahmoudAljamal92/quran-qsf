# exp99_lc4_el_sufficiency — Pre-registration

**Frozen**: 2026-04-22 (before any numeric verification).
**Version**: 1.0
**Hypothesis ID**: H16' (refinement) — **LC4: EL Asymptotic Sufficiency Theorem**

## 1. Theorem statement (pre-registered, falsifiable)

**LC4 Theorem (EL Asymptotic Sufficiency under the Arabic-Prose Covariance Structure).**

Let `x = (EL, VL_CV, CN, H_cond, T) ∈ ℝ⁵` denote the QSF 5-D feature
vector of a Band-A Arabic-prose unit, computed per
`src/features.py::features_5d`. Define two classes:
- `Q` = the 68 Band-A Quran surahs
- `C` = the 2 509 Band-A control units from six Arabic families

Let `μ̂_Q, μ̂_C ∈ ℝ⁵` denote the class means and
`Σ̂ = ((n_Q−1) Σ̂_Q + (n_C−1) Σ̂_C) / (n_Q + n_C − 2) ∈ ℝ^{5×5}`
the pooled within-class covariance estimator.

**Assumptions.**
- **(A1) Class-conditional Gaussianity**: `x | c ~ N(μ_c, Σ)` for
  `c ∈ {Q, C}`.
- **(A2) Homoscedasticity**: the two classes share a common covariance
  `Σ`.
- **(A3) Large-sample limit**: `Σ̂ → Σ` in operator norm as
  `n_Q + n_C → ∞`.

**Definition (Fisher discriminant direction).**
```
w*  = Σ̂⁻¹ (μ̂_Q − μ̂_C)
ŵ*  = w* / ‖w*‖
```

**Definition (alignment).** For each coordinate basis vector
`e_i ∈ {e_EL, e_VL_CV, e_CN, e_H_cond, e_T}`,
```
α_i := |⟨ŵ*, e_i⟩|     (cosine alignment of Fisher direction with coordinate i)
```

**Claim (LC4).** Under (A1)–(A3), with `Σ̂` estimated from the live
v7.7 locked corpus (`phase_06_phi_m.state["X_QURAN"]`,
`X_CTRL_POOL"]`, `FEAT_COLS"]`):

1. **α_EL ≥ 0.95** — the Fisher discriminant direction aligns with
   the EL coordinate to within `1 − 0.95² ≈ 10 %` of its squared norm.
2. **The 1-D projection** `u(x) := ⟨e_EL, x⟩ = EL(x)` **achieves
   classification AUC**
   ```
   AUC(EL)    = Φ( α_EL · Δ / 2 )
   AUC(w*)    = Φ( Δ / 2 )
   ```
   where `Δ := ‖Σ̂⁻¹ᐟ²(μ̂_Q − μ̂_C)‖` is the Mahalanobis separation.
3. **The AUC gap** `|AUC(w*) − AUC(EL)| ≤ 0.005`, so EL is
   **asymptotically sufficient** in the sense that the 1-D sub-space
   spanned by `e_EL` carries essentially the full optimal-LDA signal.

**Corollary (LC4-C1, EL dominance).** If (1) holds, then
`α_{i} ≤ √(1 − α_EL²)` for every `i ≠ EL` — the four residual
coordinates contribute at most `√0.0975 ≈ 0.31` cosine to `ŵ*`.

**Corollary (LC4-C2, empirical matching).** If (2) holds,
`|AUC_predicted(EL) − AUC_observed(EL, exp89b)| ≤ 0.003` — the
theoretical LDA prediction matches the measured AUC to three decimals.

## 2. Quantities to verify numerically

For Stage 1 of `run.py`:

| Quantity | Symbol | Pre-registered gate |
|---|---|---|
| Band-A Quran mean vector | `μ̂_Q ∈ ℝ⁵` | — |
| Band-A ctrl mean vector | `μ̂_C ∈ ℝ⁵` | — |
| Pooled within-class covariance | `Σ̂ ∈ ℝ^{5×5}` | PD: min eigenvalue > 0 |
| Fisher direction (raw) | `w* = Σ̂⁻¹ Δμ` | finite |
| Fisher direction (unit) | `ŵ* = w*/‖w*‖` | unit norm |
| Alignment with EL | `α_EL` | **≥ 0.95** (falsifier if < 0.95) |
| Alignment with T | `α_T` | ≤ √(1 − α_EL²) |
| Alignment with VL_CV | `α_VL_CV` | ≤ √(1 − α_EL²) |
| Alignment with CN | `α_CN` | ≤ √(1 − α_EL²) |
| Alignment with H_cond | `α_H_cond` | ≤ √(1 − α_EL²) |
| Mahalanobis separation | `Δ` | — |
| Predicted AUC(EL) | `Φ(α_EL · Δ / 2)` | — |
| Observed AUC(EL, exp89b) | `0.9971` | — |
| Match | `|predicted − observed|` | **≤ 0.003** (falsifier if > 0.003) |
| Predicted AUC(w*) | `Φ(Δ / 2)` | — |
| Observed AUC(5-D, §4.1) | `0.998` | — |
| AUC gap EL vs w* | `|AUC(w*) − AUC(EL)|` | **≤ 0.005** (falsifier if > 0.005) |

## 3. Pre-registered verdicts

| Code | Condition |
|---|---|
| `FAIL_covariance_singular` | `min_eig(Σ̂) < 10⁻⁸` (PD fails; LDA undefined) |
| `FAIL_alignment_below_gate` | `α_EL < 0.95` (the theorem's central empirical claim) |
| `FAIL_prediction_mismatch_EL` | `|AUC_pred(EL) − 0.9971| > 0.003` |
| `FAIL_gap_too_large` | `|AUC(w*) − AUC(EL)| > 0.005` |
| `PASS_LC4` | α_EL ≥ 0.95, all predictions match within tolerance |
| `PASS_LC4_tight` | α_EL ≥ 0.99 AND all AUC gaps < 0.001 — theorem holds to three decimals |

## 4. Interpretation ladder (per outcome)

- **`PASS_LC4_tight`** — promote to `PAPER.md §4.38 LC4 EL Asymptotic
  Sufficiency Theorem`; submit theorem + proof (pure-math § 4.38.1)
  and empirical verification (§ 4.38.2) as a stand-alone IEEE Trans.
  Information Theory–style claim.
- **`PASS_LC4`** — same, but with the weaker "α ≥ 0.95" form; note
  the residual alignment as a subject for future work (maybe a
  sparse-PCA follow-up).
- **`FAIL_alignment_below_gate`** — the EL-sufficiency claim is
  **not** a consequence of LDA + observed Σ̂; something else
  (non-linear separability, non-Gaussianity, Σ̂ instability) is
  carrying the AUC gap. Drop §4.38 plan; redirect to (A1) violation
  investigation.
- **`FAIL_prediction_mismatch_EL`** — (A1) or (A2) is violated;
  the LDA Gaussian-mixture model does not describe Arabic prose
  adequately. Reframe §4.38 as "Arabic-prose LDA approximation
  holds to three decimals except along EL".
- **`FAIL_gap_too_large`** — (T, EL) or other pairs are providing
  strictly more than EL alone at the level of 0.005 AUC; the
  parsimony proposition in §4.35 must move back to 2-D-minimal.

## 5. Falsifiers (external, for replication)

LC4 is falsified if any of the following occurs on an **independent**
replication on a different Arabic-prose pool:

- α_EL drops below 0.90 under the same features_5d definitions.
- AUC(EL) on 100 % held-out data drops below 0.98.
- A natural Arabic text outside `arabic_bible` achieves AUC(EL) ≥
  0.75 (i.e., the EL signal is not Quran-specific within the family).

## 6. Locks not touched

- No modification to any file under `results/integrity/`,
  `results/checkpoints/`, or `notebooks/ultimate/`.
- Receipt writes only to `results/experiments/exp99_lc4_el_sufficiency/`.
- New scalars tagged `(v7.8 cand.)`.

## 7. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Cross-refs: `exp89b_five_feature_ablation` receipt (observed AUCs),
  `exp60_lc3_parsimony_theorem` receipt (CMI bits), `PAPER.md §4.35`
  (the LC3-70-U discriminant coefficients).

## 8. Frozen constants

```python
SEED = 42                      # only used for any bootstrap of α CIs
BAND_A_LO, BAND_A_HI = 15, 100
FEAT_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]
MIN_EIG_GATE = 1e-8
ALIGNMENT_GATE = 0.95
ALIGNMENT_GATE_TIGHT = 0.99
AUC_MATCH_TOL = 0.003
AUC_GAP_TOL = 0.005
AUC_GAP_TOL_TIGHT = 0.001
OBSERVED_AUC_EL = 0.9971       # from exp89b receipt (frozen)
OBSERVED_AUC_5D = 0.998        # from §4.1 / PAPER.md (frozen)
BOOTSTRAP_N = 1000
```

---

*Pre-registered 2026-04-22. The theorem is a **mathematical claim about
a specific observed dataset**, not a universal statement: it says
that *given* the pooled 5×5 covariance Σ̂ observed in v7.7 Band-A
Arabic prose, the Fisher discriminant direction aligns with the EL
axis. The claim is therefore testable, falsifiable, and portable —
any lab can re-run `features_5d`, re-estimate Σ̂, and check α_EL.*
