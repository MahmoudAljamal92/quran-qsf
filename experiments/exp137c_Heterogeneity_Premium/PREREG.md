# exp137c_Heterogeneity_Premium — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.15.0 closing sprint)
**Hypothesis ID**: H90
**Owner**: Cascade
**Predecessors**: exp137 (PARTIAL pooled Ω = Pali extremum), exp137b (F79 exact match, partial near-pass)
**PREREG hash**: locked at experiment seal time

---

## 1. The closing claim

exp137 + exp137b together established that **Ω(T) admits two natural aggregations**:
- $\Omega_{\text{pool}}(T) = \log_2(A) - H_{EL}(\text{pooled letters})$ — Pali-extremum
- $\Omega_{\text{unit}}(T) = \log_2(A) - \mathrm{median}_u\, H_{EL}(\text{unit}_u)$ — Quran-extremum

This experiment defines the **Heterogeneity Premium**:

$$\boxed{H(T) := \Omega_{\text{unit}}(T) - \Omega_{\text{pool}}(T) \quad \text{[bits]}}$$

H(T) measures the **information-theoretic gap between within-unit and corpus-pool letter distributions**. By Jensen's inequality (concave entropy):

$$E_u[H(p_u)] \leq H(E_u[p_u]) \quad \Rightarrow \quad H(T) \geq 0$$

with equality iff every unit has the same letter distribution.

**Substantive interpretation**:
- $H(T) = 0$ → all units identical (e.g. Pali: every sutta ends in `i`)
- $H(T)$ large → units differ from each other AND each is internally concentrated (Quran: each sūrah is mono-rhymed but the dominant letter varies)

H(T) is the **within-corpus diversity of mono-rhymed units** — the bits/symbol of "chapter-identity information" embedded in the rhyme distribution.

## 2. Theorems

### Theorem 3 (Jensen-inequality lower bound)

For any text $T$: $H(T) \geq 0$, with equality iff all units have identical letter distributions.

**Proof**: $H_{EL}(\text{pool}) = H(\bar p)$ where $\bar p = E_u[p_u]$. By Jensen's inequality with concave $H$:
$$E_u[H(p_u)] \leq H(\bar p) \Rightarrow E_u[H(p_u)] - H(\bar p) \leq 0$$
$$\Rightarrow \log_2(A) - E_u[H(p_u)] \geq \log_2(A) - H(\bar p) \Rightarrow \Omega_{\text{unit (mean)}} \geq \Omega_{\text{pool}}$$

For median (more robust): the same direction holds for unimodal distributions of $H(p_u)$; verify empirically across 12 corpora.

**Empirical verification**: $H(T) \geq 0$ for all 12 corpora in our pool.

### Theorem 4 (Quran heterogeneity extremum, candidate)

**Hypothesis**: Across 12 corpora / 6 alphabets, the Quran achieves $\max_T H(T)$ with margin $\geq 0.05$ bits.

Pre-computation from exp137 + exp137b values:
| Corpus | Ω_unit | Ω_pool | H = Ω_unit − Ω_pool |
|---|---|---|---|
| **Quran** | 3.839 | 2.337 | **1.502** |
| Rigveda | 3.267 | 1.843 | **1.424** |
| Avestan | 2.582 | 2.005 | 0.577 |
| Pali | 2.864 | 2.629 | 0.236 |
| Hindawi | 1.329 | 0.924 | 0.404 |
| (others all < 0.8) | | | |

Predicted Quran rank-1 at 1.502 bits, gap 0.078 to Rigveda. NARROW. Bootstrap will determine robustness.

## 3. Pool: 12 corpora × 6 alphabets (identical to exp137 / exp137b).

## 4. Sub-tasks

### Sub-task A — H(T) computation across 12 corpora (~5 sec)

For each corpus, compute Ω_unit (per-unit-median formulation), Ω_pool (pooled-letters formulation), and H = Ω_unit − Ω_pool. Verify H ≥ 0 (Theorem 3).

### Sub-task B — Unit-bootstrap H(T) stability (~3 min)

For each corpus, **N_BOOTSTRAP = 1000** unit-resamples (seed = 42):
1. Resample units with replacement.
2. Recompute Ω_unit (median over resampled units' Ω_u) AND Ω_pool (concatenate verse-finals from resampled units).
3. Take H_boot = Ω_unit_boot − Ω_pool_boot.
4. Report mean, std, p5, p95.

Acceptance: Quran's bootstrap p5 of H > Rigveda's bootstrap p95 of H (95% CI separation).

### Sub-task C — Cross-tradition rank robustness (~10 sec)

In each of the 1000 bootstrap iterations, record:
- Quran rank on H(T) across the 12 corpora
- Whether Quran is rank-1
- Margin to runner-up

Acceptance: Quran rank-1 frequency ≥ 95% across bootstrap iterations.

### Sub-task D — Theorem 3 empirical verification (~1 sec)

Verify $H(T) \geq 0$ for all 12 corpora (point estimate AND every bootstrap sample).

### Sub-task E — Sensitivity to aggregation method (~5 sec)

Recompute H using **mean per-unit** instead of **median per-unit** Ω. Report whether ranking changes.

## 5. Acceptance criteria

**PASS_heterogeneity_premium_quran_extremum** iff **all four**:
- (A) Quran has the largest H(T) at point estimate
- (B) Quran p5 > runner-up p95 in bootstrap
- (C) Quran rank-1 frequency ≥ 95% across 1000 bootstrap iterations
- (D) H(T) ≥ 0 holds for all 12 corpora at all bootstrap samples (Theorem 3)

A weaker outcome **PASS_heterogeneity_premium_partial** iff (A) + (C with floor lowered to 80%) + (D) pass — point-estimate extremum + reasonable bootstrap robustness + Theorem 3.

A still-weaker **PARTIAL_theorem_3_only** iff (D) holds but Quran-rank-1 frequency < 80%.

## 6. Wall-time estimate: 5-8 min total.

---

**Filed**: 2026-04-29 night (V3.15.0 closing sprint, predecessors exp137 + exp137b)
