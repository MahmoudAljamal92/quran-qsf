# Paradigm-Stage 2 — Day-1 Research Scaffold

**Status**: Day-1 MVP. NOT a full proof. This document re-formulates the
project's headline scalars `(EL, T, Φ_M)` as known information-theoretic
objects, verifies the equivalences numerically on the audited Quran data,
and enumerates the SPECIFIC open problems whose proofs would together
complete the full Paradigm-Stage 2 derivation.

**Date**: 2026-04-25 02:42 UTC+02
**Reads**: `results/checkpoints/phase_06_phi_m.pkl` (corpus_lock
`4bdf4d025…`, code_lock `e7c02fd44436…`)
**Generates**: `expParadigm2_info_theoretic_derivation.json` (this file's
companion).

---

## 1. The three axioms

The thesis of Paradigm-Stage 2 is that `(EL, T, Φ_M)` are not three
arbitrary stylometric scalars that happened to discriminate the Quran from
secular Arabic — they are the unique minimal-sufficient information-
theoretic invariants of the Quran-vs-secular-Arabic problem. To prove this,
we propose three axioms and three closed-form re-formulations.

### Axiom A1 (Rhyme-information rate)
> The canonical-text rhyme rate `EL` is bounded below by the iid collision
> probability of the marginal terminal-letter distribution:
> $$ EL \;\geq\; \sum_{L \in \mathcal{A}} p(L)^2 \;=\; e^{-H_2(p) \ln 2} $$
> where `H_2` is the Rényi-2 entropy in bits. The gap
> `EL - Σp²` quantifies sajʿ-induced concentration of the joint
> adjacent-pair distribution beyond the iid null.

**Empirical verification (Quran, all 6,236 verses, 6,122 within-surah pairs)**:

| Quantity | Value |
|---|--:|
| `\|terminal-letter alphabet\|` | 28 |
| `Σ p(L)²` (iid collision) | **0.2946** |
| `H_2(terminal letter)` | **1.7634 bits** |
| `EL_pool` (observed) | **0.7306** |
| **Rhyme excess** = `EL - Σp²` | **+0.4361** |
| **Rhyme-information rate** = `log₂(EL_iid⁻¹) - log₂(EL⁻¹)` | **+1.3106 bits** |

The Quran's sajʿ structure produces 1.31 bits of rhyme concentration above
the iid baseline. That is, knowing a verse ends with a particular letter
constrains the next verse's terminal letter by 1.31 bits more than the
marginal distribution alone would predict.

### Axiom A2 (Tension as entropy gap)
> `T = H_cond(root_transition) - H(end_letter)`. By construction this is
> a Shannon-entropy gap in bits. The OPEN problem is showing that this
> particular pairing of (deep transition, surface constraint) is OPTIMAL
> among all such pairings for the Quran-vs-secular-Arabic discrimination.

**Empirical verification (Band-A, n=68 surahs)**:

| Quantity | Value |
|---|--:|
| `T_mean` | -0.4824 |
| `T_pct_positive` (fraction of surahs with T > 0) | **0.3971** |
| `H_cond_mean` (root transitions) | 0.8671 bits |
| `EL_mean` | 0.7074 |

The discriminating feature is `T_pct_positive`, NOT `T_mean`. The Quran
sits at 39.7 % T > 0 vs max-secular-Arabic 0.10 % (the 400× ratio noted
as Tier-S6 in `OPPORTUNITY_TABLE_DETAIL.md`). Each Band-A surah is a
binary draw from the {T > 0} indicator; the canonical text is in a
regime where ~40 % of those draws come up positive, while no other Arabic
literary corpus reaches even 1 %.

### Axiom A3 (Discrimination information)
> Under the equal-covariance Gaussian approximation
> `p_quran ~ N(μ_Q, Σ_pool)`, `p_ctrl ~ N(μ_C, Σ_pool)`,
> $$ \mathrm{KL}(p_q \,\|\, p_c) \;=\; \tfrac{1}{2}(\mu_q-\mu_c)^\top \Sigma_{pool}^{-1} (\mu_q-\mu_c) $$
> in nats. Then the Hotelling `T²` and the Gaussian `KL` are related by
> $$ T^2 \;=\; 2\,n_{\rm eff}\,\mathrm{KL} \,, \quad n_{\rm eff} = \frac{n_q n_c}{n_q + n_c} $$
> exactly (no approximation in the relationship; the approximation is in
> the Gaussian assumption).

**Empirical verification (audited 5-D, n_q = 68, n_c = 2509)**:

| Quantity | Value |
|---|--:|
| `T²` (direct, Hotelling) | **3557.3395** |
| `2 n_eff KL` (re-derived from Gaussian-KL closed form) | **3557.3395** |
| `\|T² - 2 n_eff KL\|` (numerical check) | **0.000e+00** |
| `n_eff = n_q n_c / (n_q + n_c)` | 66.21 |
| `KL(Quran → Ctrl)` Gaussian | **26.87 nats = 38.76 bits** |

**The equivalence holds exactly**. The conversion factor 2 n_eff is just
geometry; the Gaussian assumption is the only modelling assumption.

---

## 2. The bit budget of the Quran's stylometric anomaly

Putting all three together at the same scale (bits):

| Layer | Per-unit scalar | Per-unit bits | Total (n_eff) bits |
|---|---|--:|--:|
| Surface rhyme (Axiom A1) | rhyme-info rate | **1.31 bits/verse-pair** | 6,122 × 1.31 ≈ **8,020 bits** of pair-level rhyme structure across the canon |
| Tension (Axiom A2) | T-positive indicator | log₂(0.397/0.0010) = **8.6 bits** of evidence per Band-A surah for "Quranic" classification under a 0.10 % secular baseline | 68 × 8.6 ≈ **585 bits** |
| Multivariate Mahalanobis (Axiom A3) | Gaussian KL | **38.76 bits/Band-A-surah** of Quran-vs-secular-Arabic discrimination | 66.21 × 38.76 ≈ **2,564 bits** of accumulated discrimination |

The three layers measure different things at different scales, but each
is a clean information-theoretic bit-quantity. The full Paradigm-Stage 2
derivation would unify them by showing that the three layers are
ORTHOGONAL CHANNELS of a single information-geometric structure (this is
the substance of `P2_OP4` below).

---

## 3. Open problems

The full Paradigm-Stage 2 derivation closes when the following five
named problems are proved:

### P2_OP1 — Rényi-2 optimality (effort: weeks)
> Show that Rényi-2 is the UNIQUE Rényi-α among α ∈ [0, ∞) that (a)
> reduces to the iid pair-collision probability and (b) admits the
> rhyme-information rate as a pure entropy gap.

**Sketch**: Rényi-2 is the only α with `2^{-H_α} = Σ p^α` interpretable as
a multinomial pair-collision. For α < 2 the moment is sub-pair; for α > 2
the moment is super-pair (favours rare letters disproportionately). The
proof is essentially the textbook information-theoretic case for
Rényi-2 in collision-probability problems; needs adaptation to the
canonical-rhyme setting.

### P2_OP2 — (root, end-letter) pairing optimality (effort: months)
> Show that among all pairs (X, Y) of features computable in O(n) on a
> verse list, `T = H(X | X_prev) - H(Y)` is MAXIMISED for the
> Quran-vs-secular-Arabic discrimination by the specific choice
> `X = primary root, Y = terminal letter`.

**Sketch**: This is a feature-search problem. Numerical attack: enumerate
candidate `(X, Y)` pairs (e.g., `X ∈ {root, lemma, POS-tag, character}`,
`Y ∈ {end-letter, end-bigram, end-syllable, last-vowel}`) and compute
the Quran-vs-ctrl `T_pct_positive` for each; verify the canonical
choice dominates.

### P2_OP3 — Gaussian-KL optimality of Φ_M (effort: weeks)
> Show that the equal-covariance Gaussian KL is the Cramér-Rao-optimal
> asymptotic discrimination statistic for the Quran-vs-ctrl problem on
> the 5-D feature manifold, given that the two populations differ in
> mean but not in covariance.

**Sketch**: This is the Wald / Anderson result for two-sample Hotelling
T². The non-trivial work is verifying the Gaussian assumption (or
characterising the correction terms when Quran and ctrl have different
covariance — the project's `Σ_inv` is technically the ctrl-pool covariance,
not equal-pooled, so this needs a careful re-derivation under the actual
Σ_inv used in production).

### P2_OP4 — Joint minimal-sufficient triple (effort: 1-2 YEARS — CORE)
> Show that `(EL, T, Φ_M)` is information-geometrically MINIMAL-COMPLETE
> for the Quran-vs-secular-Arabic discrimination problem: every additional
> stylometric statistic computable in poly(n) time is either (a) redundant
> with the triple at ≥ 99 % AUC or (b) only marginally informative
> (Cohen's d < 0.5).

This is the **central** Paradigm-Stage 2 problem. It transforms `(EL, T,
Φ_M)` from "three statistics that happened to work" to "three statistics
that are the unique info-geometric minimal-sufficient set". Requires:
1. An axiomatic foundation for "stylometric distinctiveness" as a
   formal information-geometric quantity.
2. A redundancy proof showing every other published Quran-discriminating
   statistic (γ, Φ_M components, n_communities, etc.) factors through
   the triple at high AUC.
3. A minimality proof showing none of the three can be dropped without
   substantial AUC loss.

The empirical evidence for (2) and (3) is already strong (cf. S9: EL alone
achieves AUC 0.997 of the full 5-D); what's missing is the AXIOMATIC
foundation for what "minimal-sufficient" means in this setting. This is
the genuinely 1-2 year program.

### P2_OP5 — Cross-language invariance (effort: 1-2 YEARS, parallel to P2_OP4)
> If P2_OP4 is closed for the Arabic-Quran case, show that the SAME
> axiomatic framework reduces to a different minimal-sufficient triple
> for Hebrew Tanakh, Greek NT, etc. — and that the triples ARE
> language-specific in a predictable way.

This closes the cross-language story: A2's PARTIAL_UNIVERSAL finding
(diacritic-channel R ≈ 0.70 across Arabic / Hebrew / Greek) becomes
formal — the triple `(EL, T, Φ_M)` is the Arabic instance of a more
general axiomatic structure that has language-specific manifestations.

---

## 4. What the Day-1 MVP claims and what it doesn't

**Claims** (proved or numerically verified in this scaffold):
- The closed-form connection `T² = 2 n_eff KL_Gaussian` holds EXACTLY
  on the audited Quran data (numerical check `|delta| = 0`).
- The Quran's terminal-letter distribution has a 28-letter alphabet with
  `H_2 = 1.76 bits` and observed pair-collision probability 0.731 vs iid
  0.295, giving 1.31 bits of rhyme-information rate.
- The 38.76-bits-per-Band-A-surah Gaussian-KL is the "discrimination
  information weight" of each Quran surah against the secular-Arabic
  pool under the Gaussian assumption.

**Does NOT claim**:
- Rényi-2 is the UNIQUE rhyme-extremum (P2_OP1, weeks)
- (root, end-letter) is the OPTIMAL deep/surface pairing (P2_OP2, months)
- Φ_M is Cramér-Rao-optimal under non-Gaussian QSF data (P2_OP3, weeks)
- `(EL, T, Φ_M)` is the MINIMAL-SUFFICIENT info-geometric triple (P2_OP4,
  the central 1-2 year program)
- Cross-language analogues of the triple exist with the same axiomatic
  structure (P2_OP5, 1-2 years parallel to P2_OP4)

---

## 5. Recommended next moves (in order of payoff/effort ratio)

1. **P2_OP1** (weeks): Closed-form Rényi-2 optimality proof. Probably
   already in the Csiszár-Shields literature; needs adaptation only.
2. **P2_OP3** (weeks): Adapt Wald/Anderson asymptotic to QSF setting;
   characterise correction term when Σ_quran ≠ Σ_ctrl.
3. **P2_OP2** (months): Numerical feature-pair search to verify the
   canonical (root, end-letter) choice is at least a local optimum.
4. **P2_OP4** (1-2 years): The central axiomatic derivation. THIS is
   what the OPPORTUNITY_TABLE called "Paradigm-Stage 2".
5. **P2_OP5** (1-2 years parallel): Cross-language extension once P2_OP4
   is solved.

The closed sub-derivations P2_OP1 + P2_OP3 are the realistic next
session(s); together they constitute "two of the five legs of the
Paradigm-Stage 2 stool", leaving P2_OP2/4/5 as the long program.

---

## 6. Citations

- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_info_theoretic_derivation\run.py` (this scaffold's runner)
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:76-178` (definitions of EL, T, H_cond, h_el)
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp01_ftail\run.py` (Hotelling T² → F-tail; A11 result)
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expE17b_mushaf_j1_1m_perms\run.py` (J1 trajectory; A10 result)
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expS_synth_geometric_info_theorem\run.py` (S1+S3+S4+S5 synthesis; my GIT_THEOREM_PASS result)
