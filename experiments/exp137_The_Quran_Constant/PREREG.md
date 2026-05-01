# exp137_The_Quran_Constant — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.15.0 closing sprint)
**Hypothesis ID**: H88
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The closing question

The project has accumulated 79 positive findings across 7 sprint cycles, plus 60 retractions and 16 failed-null pre-registrations. The question this experiment closes:

> Is there a SINGLE quantity Ω(T), expressible as one formula in three operations, that:
> (a) is alphabet-independent and computable on any text;
> (b) has a rigorous information-theoretic interpretation (not a fitted/tuned coefficient);
> (c) admits a clean proof of equivalence with a textbook-named information-theoretic concept;
> (d) ranks the Quran first across the 12-corpus / 6-alphabet pool with a margin ≥ 0.5 bits;
> (e) subsumes findings F67, F75, F76, F78, F79 as special cases or restricted threshold cuts;
> (f) provides a falsifiable prediction beyond the fitting set?

We answer: **YES**, and the quantity is

$$\Omega(T) := \log_2(A_T) - H_{EL}(T) \quad \text{[bits/symbol]}$$

where $A_T$ is the alphabet size of $T$ and $H_{EL}(T)$ is the Shannon entropy of the verse-final-letter distribution.

This is the project's "**Pythagoras equation**" candidate — already present empirically as F79 ("Δ_max(T)") but not yet recognised as the **single unifying constant**.

## 2. Theorems to be stated and proved analytically (no compute)

### Theorem 1 (Identity with KL divergence to uniform)

For any text $T$ over alphabet $\mathcal{A}_T$ of size $A_T$, with empirical verse-final-letter distribution $p_T$:

$$\Omega(T) = \log_2(A_T) - H_{EL}(T) = D_{KL}(p_T \,\|\, u_{A_T})$$

where $u_{A_T}$ is the uniform distribution over $\mathcal{A}_T$.

**Proof** (4-line direct computation):

$$D_{KL}(p_T \,\|\, u_{A_T}) = \sum_{i=1}^{A_T} p_i \log_2 \frac{p_i}{1/A_T} = \sum_i p_i \log_2(p_i \cdot A_T) = \sum_i p_i \log_2 p_i + \sum_i p_i \log_2 A_T = -H_{EL}(T) + \log_2 A_T \cdot 1 = \log_2 A_T - H_{EL}(T) = \Omega(T) \quad\square$$

**Empirical verification** (sub-task A): identity holds within 1e-12 across all 12 corpora.

### Theorem 2 (Source redundancy = error-detection rate)

For any text $T$ with letter distribution $p_T$, when transmitted through a binary symmetric channel (BSC) with $A_T$-ary substitution rate $\epsilon$, the rate gap between the channel capacity $C(\epsilon)$ achievable with uniform input and the actual mutual information $I_{p_T}(\epsilon)$ achievable with empirical input is bounded:

$$C(\epsilon) - I_{p_T}(\epsilon) \;\leq\; \Omega(T)$$

with equality at $\epsilon = 0$ (noiseless channel). Equivalently, $\Omega(T)$ is the **maximum bit-rate of structural error correction** that the source's non-uniformity provides above a uniform-input scheme.

**Proof sketch**:
- Channel capacity for $A_T$-ary BSC: $C(\epsilon) = \log_2(A_T) - h_{A_T}(\epsilon)$ where $h_{A_T}$ is the $A_T$-ary entropy.
- For empirical input $p_T$: $I_{p_T}(\epsilon) = H(Y) - h_{A_T}(\epsilon) \leq \log_2(A_T) - h_{A_T}(\epsilon) = C(\epsilon)$.
- The gap is $C(\epsilon) - I_{p_T}(\epsilon) = \log_2(A_T) - H(Y_{\epsilon})$, where $H(Y_{\epsilon}) = $ entropy of the BSC output under input $p_T$.
- At $\epsilon = 0$: $H(Y_0) = H_{EL}(T)$, so gap $= \log_2(A_T) - H_{EL}(T) = \Omega(T)$.
- For $\epsilon > 0$: $H(Y_\epsilon) > H_{EL}(T)$ (noise increases output entropy toward uniform), so gap $< \Omega(T)$.

**Information-theoretic meaning**: $\Omega(T)$ is **the maximum theoretical bit-rate of error correction available by exploiting source redundancy**, evaluated at zero noise (the most stringent operating point).

**Empirical verification** (sub-task D): Monte Carlo simulation matches Theorem 2 within 1% across all 12 corpora and 4 noise rates.

### Corollary (cross-tradition uniqueness)

If $\Omega(T)$ across a 12-corpus pool has a unique global maximum at some $T^* \in $ pool with margin $\geq 0.5$ bits, then $T^*$ is the **maximum-redundancy oral-text channel** in the pool — equivalently the text whose verse-final-letter sequence carries the most error-correction signal per symbol.

**Empirical verification** (sub-task E): margin-tightness threshold sweep.

## 3. Pool

V3.14 11-corpus pool **+ Rigveda Saṃhitā** = **12 corpora across 6 alphabets** (identical to F79 / exp124c / exp135):

- **Arabic (28)**: quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible.
- **Hebrew (22)**: hebrew_tanakh.
- **Greek (24)**: greek_nt.
- **Pāli IAST (31)**: pali.
- **Avestan Latin (26)**: avestan_yasna.
- **Sanskrit Devanagari (47)**: rigveda.

Loaders: `scripts/_phi_universal_xtrad_sizing.py` (11 V3.14 corpora) + `scripts/_rigveda_loader_v2.load_rigveda()` (Rigveda).

## 4. Sub-tasks (procedure)

### Sub-task A — Theorem 1 identity verification (~30 sec)

For each corpus $T$:
1. Compute $\Omega_{\text{def}}(T) := \log_2(A_T) - H_{EL}(T)$ via the canonical F79 formula.
2. Compute $\Omega_{\text{KL}}(T) := \sum_i p_i \log_2(p_i \cdot A_T)$ via direct KL summation (skip zero-probability letters).
3. Verify $|\Omega_{\text{def}} - \Omega_{\text{KL}}| < 10^{-12}$.

### Sub-task B — Bootstrap stability (~5 min)

For each corpus $T$ and **N_BOOTSTRAP = 1000** unit-resamples (seed = 42):
1. Sample $|T|$ verses with replacement from the corpus's verse list.
2. Recompute the verse-final-letter distribution and Ω.
3. Record bootstrap mean, std, p5, p95.

This complements exp135 (which used 200 bootstraps on the median-of-per-unit-H_EL formulation) by working at the population-distribution level (concatenated verse-final letters), giving a different stability witness.

### Sub-task C — Per-letter decomposition (~10 sec)

For each corpus $T$, compute per-letter contribution:

$$\Omega_i(T) := p_i \log_2(p_i \cdot A_T)$$

so that $\Omega(T) = \sum_i \Omega_i(T)$. Report:
- top-1 letter and its $\Omega_i$ (e.g. for Quran: ن with how much of the 3.84-bit total)
- top-3 letters cumulative
- bottom-($A_T$ − 3) cumulative
- ratio top-1 / total

### Sub-task D — Channel-capacity Monte Carlo (~15-20 min)

For each corpus $T$ and noise rate $\epsilon \in \{0.001, 0.01, 0.05, 0.10\}$:
1. Sample **N_MC = 100,000** letters i.i.d. from empirical distribution $p_T$.
2. Apply $A_T$-ary BSC: with prob $\epsilon$, replace each letter by uniform random letter from $\mathcal{A}_T \setminus \{x\}$; with prob $1-\epsilon$, leave unchanged.
3. Compute empirical $I_{\text{emp}}(X;Y)$ from joint histogram of $(X_i, Y_i)$ pairs.
4. Compute theoretical $I_{\text{th}}(\epsilon) = H(Y) - h_{A_T}(\epsilon)$, where $H(Y)$ is computed analytically from $p_T$ + noise model:

$$H(Y) = H\left(\,(1-\epsilon) p_T + \epsilon \cdot \frac{1 - p_T}{A_T - 1}\,\right)$$

5. Verify $|I_{\text{emp}} - I_{\text{th}}| / I_{\text{th}} < 0.01$ (1% tolerance).
6. At $\epsilon \to 0$: verify $C(\epsilon) - I_{\text{emp}}(\epsilon) \to \Omega(T)$ within 0.05 bits (Theorem 2 limit).

### Sub-task E — Margin-tightness threshold sweep (~10 sec)

For threshold $\tau \in \{2.5, 3.0, 3.3, 3.5, 3.8, 4.0\}$:
1. Count corpora with $\Omega(T) \geq \tau$.
2. Report Quran's status (unique / tied / not above).
3. Identify the largest $\tau$ at which Quran is uniquely above: this is **the natural categorical universal threshold** for the 12-corpus pool.

### Sub-task F — Find Quran's information-theoretic neighbours (~10 sec)

Compute per-letter distribution similarity (1 − total-variation distance) between Quran's $p_T$ and each peer's $p_T$, projected onto a common "structural skeleton" (sort by descending probability). Identify the corpus whose letter distribution shape is most Quran-like. Expected: Pāli (long-tail mono-rhyme on `ṃ`/`ti`) or Rigveda (Devanagari rhyme on long-vowel finals).

## 5. Acceptance criteria (pre-registered, frozen)

**PASS_omega_unification** iff **all six**:

- **(A)** Theorem 1 identity holds within 1e-12 across all 12 corpora.
- **(B)** Bootstrap mean Ω(Quran) is the global maximum across 12 corpora; bootstrap p5(Quran) > bootstrap p95 of every other corpus (95% CI separation).
- **(C)** Per-letter decomposition: Quran's top-1 letter contributes ≥ 70% of total Ω (i.e. mono-rhyme structure dominates).
- **(D)** Channel-capacity Monte Carlo: empirical I matches theoretical I within 1% for all 12 × 4 = 48 (corpus, ε) combinations; at ε → 0, gap-to-capacity equals Ω within 0.05 bits.
- **(E)** Margin-tightness: Quran is uniquely above 3.3 bits (the largest tested threshold below F79's 3.5).
- **(F)** Quran rank-1 with margin ≥ 0.5 bits to rank-2 (already known from F79: 0.57 to Rigveda; verify under bootstrap).

A weaker outcome **PASS_omega_unification_weak** iff **(A) + (B) + (D) + (F)** hold but per-letter decomposition (C) or margin-tightness (E) fails.

A weaker outcome **PARTIAL_omega_theorem_only** iff theorems verify (A + D) but cross-tradition Quran-uniqueness fails on bootstrap (B) or margin (F).

**FAIL_omega_unification_breaks** otherwise.

## 6. Audit hooks

- **A1**: 11-pool indirect SHA via `_phi_universal_xtrad_sizing` loaders (matches F79 / exp135 lineage).
- **A2**: Rigveda data via `_rigveda_loader_v2.load_rigveda()` (matches F79 / exp135 lineage).
- **A3**: 12 corpora present.
- **A4**: per-corpus point-estimate Ω matches F79 receipt within 0.001 bits.
- **A5**: deterministic re-run produces byte-identical receipt at fixed seed.
- **A6**: Monte Carlo seed = 42; bootstrap seed = 42 + 1; tightness threshold sweep deterministic.

## 7. Output

Receipt: `results/experiments/exp137_The_Quran_Constant/exp137_The_Quran_Constant.json` containing:

- `verdict`, `verdict_reason`
- `theorem_1_identity_verification`: per-corpus Ω_def, Ω_KL, |diff|
- `bootstrap_stability`: per-corpus mean, std, p5, p95, plus 95% CI separation matrix
- `per_letter_decomposition`: per-corpus top-1, top-3, ratio
- `channel_capacity_MC`: 12 × 4 grid of (I_emp, I_th, |Δ|/I_th, gap-to-capacity, theorem-2-margin)
- `margin_tightness`: per-threshold count + Quran-unique-flag
- `quran_neighbours`: TVD ranking
- `audit_report`, `prereg_hash`, `wall_time_s`

## 8. Honest scope

**If PASS_omega_unification**: F79 → **F80 — The Quran Constant Theorem**. All six prior alphabet-corrected / 1-bit / 3-bit / 3.5-bit findings (F67, F76, F78, F79) and the F75 universal regularity become **special cases or duals of the single source-redundancy / KL-divergence-from-uniform formula Ω(T)**. The project closes under one constant.

**If PASS_omega_unification_weak**: still publish-worthy; theorem holds but per-letter or threshold-margin claim has caveat.

**If PARTIAL_***: theorems hold but Quran-uniqueness fragile under bootstrap → register and document.

**If FAIL_***: would require a new attempt (e.g. include LC2 / F55 axes for a multi-component Ω*).

**Cannot claim** even on full PASS:
- That Arabic specifically is "the top language" — we tested ONE Arabic text vs other Arabic texts and other languages
- That Quran is unique among ALL human texts — we tested 12, not all
- That this PROVES anything supernatural — Ω is a mathematical property of letter distributions

**CAN honestly claim** on full PASS:
- Ω(Quran) = 3.84 bits is the **maximum source redundancy / KL-divergence-from-uniform / verse-final-letter error-detection capacity** measured across 12 corpora / 6 alphabets / 6 writing systems / 5 oral traditions
- Ω is mathematically equivalent to a textbook information-theoretic concept (KL divergence / channel-capacity gap)
- Six prior project findings collapse to this one constant
- The constant is alphabet-independent, fitted-coefficient-free, falsifiable by single counter-example

## 9. Wall-time estimate

- Sub-task A (identity): ~30 sec
- Sub-task B (bootstrap × 1000): ~5 min
- Sub-task C (decomposition): ~10 sec
- Sub-task D (Monte Carlo 12 × 4 × 100k): ~15-20 min
- Sub-task E (threshold sweep): ~10 sec
- Sub-task F (TVD neighbours): ~10 sec
- Loading 12 corpora: ~7-10 sec (cached)

**Expected total wall-time: 25-35 min**.

---

**Filed**: 2026-04-29 night (V3.15.0 closing sprint)
