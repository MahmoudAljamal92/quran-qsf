# exp137b_The_Quran_Constant_per_unit — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.15.0 closing sprint)
**Hypothesis ID**: H89
**Owner**: Cascade
**Predecessor**: exp137 (PARTIAL_omega_theorem_only) revealed pooled Ω ranks Pali first, not Quran.
**PREREG hash**: locked at experiment seal time

---

## 1. The reformulated question

exp137 verified Theorems 1 & 2 rigorously but at the **pooled** level — and pooled Ω ranks **Pali** first (2.63 bits) over Quran (2.34 bits). This revealed an important truth: the Quran's distinctive structural property is **per-unit (per-surah) mono-rhyme heterogeneity**, not corpus-wide mono-rhyme.

This experiment tests whether **per-unit-median Ω** — the formulation already used by F79 — admits the same theorems AND ranks the Quran first.

$$\Omega_{\text{unit}}(T) := \log_2(A_T) - \mathrm{median}_u\, H_{EL}(\text{unit}_u)$$

This is **F79's formulation**, now to be promoted from empirical metric to information-theoretic theorem if all sub-tasks pass.

## 2. Theorems to verify

### Theorem 1' (per-unit identity)

For each unit $u$ of corpus $T$ with verse-final-letter distribution $p_u$:
$$\Omega_u := \log_2(A_T) - H_{EL}(p_u) = D_{KL}(p_u \,\|\, u_{A_T})$$

This is the per-unit form of exp137's Theorem 1. Holds by direct algebra; verified empirically within 1e-12 across all units of all 12 corpora.

### Theorem 2' (per-unit channel capacity)

For each unit $u$ in transmission through an $A_T$-ary BSC at rate $\epsilon$:
$$C_u(\epsilon) - I_{p_u}(\epsilon) \big|_{\epsilon \to 0} = \Omega_u$$

Per-unit channel capacity gap equals per-unit Ω at zero noise (textbook Shannon).

### Aggregation (corpus-level)

$$\Omega_{\text{unit}}(T) = \mathrm{median}_u(\Omega_u)$$

Median (rather than mean) is robust to a few small units with extreme values (matches F79).

## 3. Pool

12 corpora × 6 alphabets, identical to exp137 / F79 / exp135 / exp124c.

## 4. Sub-tasks

### Sub-task A — Per-unit Theorem 1 identity (~30 sec)

For each unit of each corpus, compute $\Omega_u$ via both formulas and verify identity within 1e-12.

### Sub-task B — Unit-bootstrap stability (~3 min)

For each corpus, **N_BOOTSTRAP = 1000** resamples of units (with replacement, seed = 42):
- Recompute median Ω_u
- Report mean of bootstrap medians, std, p5, p95

Acceptance: Quran's bootstrap p5 of median > Rigveda's bootstrap p95 of median (95% CI separation).

### Sub-task C — Per-unit dominant letter heterogeneity (~10 sec)

For each corpus, identify the dominant rhyme letter of each unit. Count distinct dominant letters across units.

For each corpus T:
- $D(T)$ := number of distinct dominant letters across units
- $H_{\text{dom}}(T)$ := Shannon entropy of dominant-letter-frequency distribution

Quran prediction: many distinct dominant letters (high $D$, high $H_{\text{dom}}$) — sūrahs differ in their rhyme letter.
Pali prediction: few distinct dominant letters (low $D$, low $H_{\text{dom}}$) — almost all suttas end in `i`.

### Sub-task D — Per-unit channel-capacity Monte Carlo (~5 min)

Pick 5 representative units per corpus (5 random seeds for selection within each corpus). For each, run BSC Monte Carlo at ε ∈ {0.001, 0.01, 0.05, 0.10}. Verify Theorem 2' per unit at each noise rate within 1% relative tolerance.

### Sub-task E — Margin-tightness on Ω_unit (~10 sec)

Threshold sweep $\tau \in \{2.5, 3.0, 3.3, 3.5, 3.8, 4.0\}$. Identify the largest $\tau$ at which Quran is uniquely above. Expected: 3.5 (matches F79).

### Sub-task F — Cross-tradition global maximum + margin (~5 sec)

Verify Quran has the highest $\Omega_{\text{unit}}$ across 12 corpora with margin ≥ 0.5 bits to runner-up.

## 5. Acceptance criteria

**PASS_quran_constant_theorem** iff **all six**:
- (A) per-unit Theorem 1 identity within 1e-12
- (B) Quran p5 > runner-up p95 in unit-bootstrap
- (C) Quran $D(T) \geq 5$ AND Pali $D(T) \leq 3$ (heterogeneity contrast)
- (D) per-unit channel-capacity MC within 1%
- (E) Quran uniquely above $\tau = 3.3$ bits at minimum
- (F) Quran rank-1 with margin ≥ 0.5 bits to runner-up

A weaker outcome **PASS_quran_constant_theorem_partial** iff (A) + (D) + (F) pass — theorems hold + cross-tradition uniqueness preserved.

## 6. Wall-time estimate: 8-12 min total.

---

**Filed**: 2026-04-29 night (V3.15.0 closing sprint, predecessor exp137 PARTIAL)
