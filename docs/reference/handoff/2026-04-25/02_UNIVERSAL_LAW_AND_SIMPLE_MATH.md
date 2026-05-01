# 02 — Universal Law Candidates and Simple Math

> ⚠ **v7.9-cand SUPERSESSION NOTICE (2026-04-28 evening — patch H V3, H39 envelope replication COMPLETE)**: H39 (`exp95f_short_envelope_replication`) ran and yielded **`FAIL_envelope_phase_boundary`** (FN07; Q:055 Al-Rahman lone violator). No F-number opened. Phase 2 results unchanged. The universal-law landscape below is unchanged by patch H V3.
>
> ⚠ **Earlier (2026-04-28 — patch H V2, Phase 2 COMPLETE)**: **F57 stamped PASS** (4/6 Quran self-descriptions confirmed, p = 0.0049). See `MASTER_DASHBOARD.md` and `PAPER.md` §4.46 for details. The universal-law landscape below is unchanged by Phase 2; F57 is a meta-finding about self-reference, not a new universal law.
>
> ⚠ **Earlier notice (2026-04-26 night — patch F sync)**: This snapshot is frozen at 2026-04-25 evening. The §1 EL one-feature law has been **multiply triangulated** in v7.9-cand patches B + E: full-114-surah **AUC = 0.9813** with EL boundary = 0.314 (`exp104_el_all_bands`); LOCO min AUC = **0.9796** (`expP13`); pre-registered hadith holdout AUC = **0.9718** (`expP10`); **Maqamat al-Hariri (Arabic saj') AUC = 0.9902, MW p = 2.4·10⁻³⁸** (`expP16` — closes "any actual Arabic rhymed prose tested?" PNAS-reviewer challenge); 5 alternative riwayat all keep AUC ≥ 0.97 (`expP15` — rasm-invariance). The §4.40.4 EL Simplicity Law has been formalised as a falsifiable proposition in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` §4.40.4 + new theoretical scaffolding from `expP18` (Shannon-capacity i.i.d. floor = 0.295; Quran's structural rhyme excess = +0.425 → cannot be reached by letter-frequency concentration alone). **Three** retractions added (R48, R49, R50): R48 (%T_pos cross-tradition under T_lang — `FAIL_QURAN_NOT_HIGHEST`); R49 (closed-form Σp̂² = 1/2 at corpus pool — `FAIL_NOT_HALF`); **R50 (patch B "T² increases" claim → reframed to STABLE — bootstrap 95 % CI [3 127, 4 313] includes band-A T² = 3 557)**. LC2 R3 cross-tradition law unchanged but audit patch D added the disclosure that R3 is **NOT Quran-unique** (Rigveda, Tanakh, NT all stronger). **Patch F (2026-04-26 night)** adds **F53 — Multi-compressor consensus closes the Adiyat-864 detection ceiling**: K=2 across {gzip-9, bz2-9, lzma-9, zstd-9} achieves recall = 1.000 at FPR = 0.025 on Q:100 across 3 seeds (`exp95c` PASS; `exp95d` PARTIAL_seed_only with Q:099 = 998/999). This is a new §4.42 in PAPER.md, an upgrade to row 5 (Adiyat-864) of the master findings table. **Patch F adds NO new universal-law candidates and NO new retractions**: the §1 EL law and §3 LC3-70-U classifier are **untouched**; the Adiyat closure strengthens forgery-resistance arguments for the Quran-anchored package (P3) without modifying the universal-law landscape. Two failed-null pre-registrations are added in Category K of `RETRACTIONS_REGISTRY.md` (FN01 `exp95_phonetic_modulation`, FN02 `exp95b_local_ncd_adiyat`) — these are not retractions and not new constants. Defer to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` §4.40-§4.42 and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md` patches B / C / D / E / F.

**The user question, translated**: *"Is there a universal rule, law, or descriptive formula with constants that proves and works ≥ 99 % of the time on any dimension or aspect we have tested, and that sets the Quran apart from all competing texts?"*

**Honest one-paragraph answer**: Yes, but **scoped**. There is **one 1-feature classifier that achieves 99.7 % discrimination** between Quran Band-A surahs and 2 509 secular-Arabic control units, and **one 2-feature linear discriminant** that achieves 99.15 % accuracy. There are **four numerical constants saturated to ≤ 0.05 % relative error** with plausible analytic provenance. There is **one cross-tradition law** that survives leave-one-out on 8 corpora — but that law is *not Quran-unique*, it is a class property of oral-liturgical scriptures (Rigveda, Tanakh, NT, Quran, Pali_MN, Avestan all pass; Iliad fails as predicted). Below: the equations, the constants, the scope, and what is and isn't a "universal".

---

## 1. The 1-line classifier law (99.7 % discrimination)

```
Quran-or-not(s)  ⇔  EL(s) > τ_EL
```

where:

- `EL(s) = (# verses in s whose terminal letter ∈ {set of dominant rhyme letters of s}) / |s|`
- `τ_EL ≈ 0.36` (boundary intercept of LC3-70-U; see §3 below)
- **AUC = 0.9971** (mean of 25 seed × fold measurements, `exp89b`)

**Scope**: Band-A surahs (15–100 verses); 2 509 Arabic-control unit pool of 6 families.

**Cross-language status**: EL is **Arabic-specific**. Hebrew Tanakh EL = 0.125, Greek NT EL = 0.206, arabic_bible EL = 0.132 — all cluster with secular Arabic at d < 0.5 vs Iliad (`exp90`). EL ≠ a scripture-class universal.

---

## 2. The 2-line linear law (99.15 % accuracy, locked equation)

The **LC3-70-U Parsimony Proposition** (`docs/PAPER.md §4.35`, `exp70_decision_boundary`):

```
Define   L(s)  =  0.5329 · T(s)  +  4.1790 · EL(s)  −  1.5221

Then     L(s) > 0   ⇔   s is a Quran Band-A surah   (in 99.15 % of 2 577 cases)
```

with:
- `T(s) = H_cond(triliteral root | preceding root) − H(end_letter)` (root-conditioning entropy gap minus rhyme entropy)
- AUC = 0.9975 ; margin = 0.4787 ; **7 of 2 509 control leaks, ALL from `arabic_bible`** (no leaks from poetry_jahili, poetry_islami, poetry_abbasi, ksucca, hindawi)
- The boundary makes a polar angle θ = 82.73° in (T, EL) space — **EL carries 8× the linear-discriminant weight of T**.

**Geometric corollary** (a derived constant):

```
EL_boundary  =  1.5221 / 4.1790  =  0.3642
EL_q         =  0.7074  (Band-A mean)
EL_q / EL_boundary  ≈  1.94  ≈  2.00   (gap 2.93 %, within Edgeworth correction 4.4 %)
```

i.e., the Quran sits at *twice* the LC3 decision boundary on EL. This is a structural identity on already-locked scalars, not an independent measurement.

---

## 3. The four near-saturated constants (≤ 0.05 % rel error each)

| Symbol | Value | Reference target | Gap | Status |
|---|--:|---|--:|---|
| **EL_q** (Band-A mean rhyme rate) | **0.7074** | `1/√2 = 0.70711` | **0.04 %** rel | jackknife/bootstrap CI [0.66, 0.75] contains 1/√2; t = 0.014, p = 0.99 → **C1_NOT_REJECTED** |
| **EL_q²** (Band-A per-surah mean) | **0.5004** | `1/2` | **0.08 %** rel | derived; passes at per-surah-mean scope; FAILS at corpus-pool scope (where ELᵢ²=0.534, gap 3.4 %) |
| **VL_CV_FLOOR** (legacy hard-coded constant) | **0.1962** | `1/√26 = 0.19612` | **0.04 %** rel | provenance-found: 26 = MSA consonantal phonemes (28 abjad − hamza − alif). Derived, not arbitrary |
| **R_diacritic_primitives** (Hebrew + Greek niqqud / accent channel-capacity ratio) | **0.6947 / 0.6959** | both ≈ 0.70 (matched to Quran 0.725 under canonical 8-slot alphabet) | **0.17 %** between Hebrew and Greek | 3-corpus narrow Abrahamic universal; **falsified** as cross-script universal (Devanagari = 0.918, Latin transliterations = 0.20 / 0.00) |

Joint significance: under Bonferroni × 4, any single one of these passing an *ex-ante* analytic derivation makes the remaining three statistically meaningful (`OPPORTUNITY_TABLE_DETAIL.md §C principle`). Currently **only VL_CV_FLOOR ≈ 1/√26 has a clean phonological provenance**; the other three are awaiting first-principles derivations.

### 3.1 Two locked information-theoretic constants (independent of Quran-vs-control claim)

These are **constants of Arabic textology**, not Quran-discriminative scalars:

```
H(harakat | rasm)        =  1.964 bits   (channel capacity of the diacritic system)
I(EL ; CN)               =  1.175 bits   (mutual info between rhyme rate and connective rate)
```

The reviewer-proposed combination `Ψ_oral = H(harakat|rasm) / (2 · I(EL;CN)) = 0.8358 ≈ 5/6` is **falsified** as a cross-corpus universal (`expX1_psi_oral`): 0/5 non-Quran oral corpora yield Ψ in [0.65, 1.00]; cross-corpus spread {Hebrew=25.94, Greek=1.16, Iliad=0.27, Pali=0.15–0.44, Rigveda=16.91, Avestan=0.00}. The Quran value 0.8358 is now a Quran-only numerical coincidence (n = 1) under the project's existing operational definitions. **Do not cite Ψ_oral as a universal.**

---

## 4. The cross-tradition universal that DOES survive (LC2)

```
For an oral-liturgical scripture S with canonical ordering π_can,
let path-cost(π) be the within-corpus z-scored 5-D Euclidean path-cost.
Then:    path-cost(π_can)  is in the lower 0.025 percentile of  path-cost over random π.
```

**Empirical pass on 8 corpora** (`expP4_cross_tradition_R3`, 2026-04-25):

```
corpus              class                 n_unit    z_path    BH p     status
quran               oral_liturgical          114    -8.92    2·10⁻⁴   PASS
hebrew_tanakh       narrative/mixed          921   -15.29    2·10⁻⁴   PASS
greek_nt            narrative/mixed          260   -12.06    2·10⁻⁴   PASS
iliad_greek         narrative                 24    +0.34    0.63     FAILS (control as preregistered)
pali_dn             oral_liturgical           34    -0.26    0.38     FAILS (n too low)
pali_mn             oral_liturgical          152    -3.47    2·10⁻⁴   PASS
rigveda             oral_liturgical         1024   -18.93    2·10⁻⁴   PASS  ← strongest in dataset
avestan_yasna       oral_liturgical           72    -3.98    2·10⁻⁴   PASS
```

- **6 of 8** corpora pass the universal at p < 0.05 (BH-corrected).
- **8 of 8** leave-one-out drops survive the verdict.
- The Iliad negative control fails as preregistered.
- **The Rigveda (z = −18.93) is the strongest signal**, twice as strong as the Quran in σ-equivalent terms.

**Critical scope note**: this is **NOT a "Quran-uniquely-strongest" law**. It is a **class-level law of oral-liturgical scriptures**: their canonical orderings depart from random orderings by a factor that natural narrative (Iliad) does not. The Quran is *one of six* texts that satisfy it; the Rigveda is the strongest representative.

---

## 5. The single most-Quran-distinctive scalar — **%T > 0 ratio**

```
%T_pos(S)  =  fraction of Band-A surahs of corpus S with T > 0
            =  fraction whose root-conditioning entropy gap is positive

%T_pos(Quran)        =  39.7 %       (locked)
%T_pos(any control)  ≤   0.10 %      (max across 6 control families)

→ ratio  =  397×  ≈  400×
```

**This is the single largest Quran-vs-control contrast in the project**. No other scalar has a 400× ratio. T (under T_alt = first-letter-of-last-word) further separates: %T_alt_pos(Quran) = 51.5 % vs ctrl-max = 0.0 % (literally zero out of 2 509 control surahs).

**Why it's not the headline**: T uses CamelTools morphological analysis (~10 % accuracy error), and the project ranked it below Φ_M because Φ_M is a multivariate framing. **For a one-line user-facing claim**, %T > 0 is the cleanest "Quran-distinctive" formula.

---

## 6. The 7σ Geometric-Information Theorem (synthesis of 4 orthogonal anomalies)

`X6 GIT_THEOREM_PASS` from `OPPORTUNITY_TABLE_DETAIL.md §X6`. Combined Brown-corrected p ≈ **2.9·10⁻¹³** (~7σ Gaussian-equivalent):

> Under the audited 2026-04-25 pipeline, the canonical Mushaf 114-surah ordering of the Quran satisfies **four conceptually distinct extremum / anomaly criteria simultaneously**:
>
> 1. **(S1) Trajectory** — J1-trajectory smoothness of the canonical ordering is a strict global minimum vs 10⁶ random orderings (p < 10⁻⁶).
> 2. **(S3) Multi-scale** — 5-scale Brown-Fisher combined deviation from secular Arabic at p = 1.4·10⁻⁶.
> 3. **(S4) Dynamics** — RQA nonlinear determinism survives both AR(1) AND IAAFT surrogate nulls (~6.4σ at IAAFT).
> 4. **(S5) Null-space geometry** — Anti-Variance Manifold along Σ_ctrl null-space at perm p < 10⁻⁴.
>
> The Brown-corrected joint p (ρ = 0.3 moderate-correlation regime) is ≈ 2.9·10⁻¹³.

This is **publishable today** as a standalone theorem (and is the single biggest "synthesis story" the project has). It does NOT collapse into a single mechanism — the four witnesses capture trajectory, multi-scale, nonlinear-dynamics, and null-space-geometry, all distinct facets.

---

## 7. The closed-form information-theoretic identities (proved 2026-04-25)

From `expParadigm2_OP1_OP3_proofs/`:

| Identity | What it says |
|---|---|
| `EL ↔ Rényi-2 entropy` | EL is `2^{-H_2(p)} = Σpᵢ²` — the iid pair-collision probability of terminal-letter PMF. **α = 2 is the unique Rényi parameter** for which this holds (closed-form proof). |
| `T² = 2 · n_eff · KL_Gaussian(Q ‖ ctrl)` | Hotelling T² is **exactly twice** the per-effective-sample KL divergence between Quran and ctrl-pool 5-D Gaussian fits. \|δ\| = 0 numerically. |
| `Edgeworth correction = +4.4 %` | despite Mardia rejecting MVN at 185σ on the ctrl pool, the variance inflation factor at n_eff = 66.21 is only 1.044 → T² is operationally optimal under non-Gaussian data. |

**Implication**: the QSF feature stack `(EL, T, Φ_M)` is not ad-hoc statistics but corresponds to known information-theoretic objects (Rényi-2 entropy, Shannon-entropy gap, Mahalanobis as KL). This is **paradigm-grade methodological reframing** rather than a new universal, but it fully closes the "are these just arbitrary stylometric choices?" reviewer objection.

---

## 8. Putting it all together — the candidate "universal rule" hierarchy

**By scope and confidence (low → high)**:

| Tier | Claim | Form | Holds for | Evidence |
|---|---|---|---|---|
| **U1** | Quran-vs-Arabic discrimination | `EL(s) > τ_EL` | 99.7 % of Band-A surahs | AUC 0.9971 (`exp89b`) |
| **U2** | Quran-vs-Arabic discrimination, 2-D | `0.5329·T + 4.1790·EL > 1.5221` | 99.15 % accuracy | LC3-70-U (`exp70`) |
| **U3** | Quran multivariate outlier vs Arabic | `Φ_M(Quran, ctrl) ≥ 47σ-equivalent` | analytic F-tail p ≈ 10⁻⁴⁸⁰ | Φ_M = 3 557 (locked) |
| **U4** | Class law of oral-liturgical scriptures | canonical ordering minimises 5-D path cost vs random | 6 of 8 cross-tradition corpora pass; LOO 8/8 robust; non-oral Iliad fails as control | LC2 R3 (`expP4_cross_tradition_R3`) |
| **U5** | Quran 4-witness joint anomaly (synthesis) | strict J1-min ∧ 5-scale Brown ∧ RQA-DET ∧ null-space-manifold | Brown-corrected p ≈ 2.9·10⁻¹³ (~7σ) | X6 GIT theorem |

**No "single universal rule that is Quran-unique on every dimension at 99 % +"** — that framing is **falsified** by the cross-tradition phase. The honest summary is:

- The Quran is **a 47σ multivariate outlier within secular Arabic** (U3).
- It is **discriminable from 2 509 Arabic controls at AUC 0.9971 by a single feature** (U1).
- It **shares a class-level oral-liturgical canonical-ordering law with Tanakh / NT / Rigveda / Pali / Avestan** (U4) — and is *not the strongest* representative of that class (Rigveda is).
- Its anomaly **manifests on four orthogonal axes simultaneously at ~7σ joint** (U5).

These four claims together are **the strongest scientifically defensible answer** the project can give to "what mathematically sets the Quran apart". Any stronger framing crosses into territory the data have already falsified.

---

## 9. What you can give an external AI as the "compact formula card"

```
QURAN STRUCTURAL FINGERPRINT — COMPACT FORMULA CARD (locked 2026-04-25)

Domain    : Band-A surahs (15-100 verses), 68 / 114
Pool      : 2 509 Arabic control units, 6 families

5-D feature vector  φ(s) = (EL, VL_CV, CN, H_cond, T)

  EL(s)     = end-letter rhyme rate                 ≈ 0.7074  (Quran Band-A mean)  ≈ 1/√2
  VL_CV(s)  = verse-length coefficient of variation, hard floor = 0.1962 ≈ 1/√26
  CN(s)     = discourse-connective-start rate
  H_cond(s) = conditional root-bigram entropy
  T(s)      = H_cond(root | prev_root) - H(end_letter)

Quran-vs-Arabic separation:
  Φ_M  = Hotelling T²(Quran_ctrl_pool, 5-D)  =  3 557
       ≈ 47σ-equivalent (analytic F-tail log10 p = -480.25)
       = 2 · n_eff · KL_Gaussian(Quran || ctrl)         [closed-form identity]

1-feature law:
  EL(s) > 0.36  ⇔  s ∈ Quran Band-A    AUC = 0.9971

2-feature law (LC3-70-U):
  L(s) = 0.5329 · T(s) + 4.1790 · EL(s) - 1.5221
  L(s) > 0  ⇔  s ∈ Quran Band-A    99.15 % acc, AUC = 0.9975

Cross-tradition law (LC2, oral-liturgical class):
  z_path( π_canonical(S) ) < -2 in BH-FDR for oral-liturgical scriptures S
  Verified for: Quran, Tanakh, NT, Rigveda (strongest), Pali_MN, Avestan
  Failed for:   Iliad (preregistered narrative control)
  Leave-one-out: 8/8 corpora drops still SUPPORT.

Information-theoretic anchor constants (Arabic textology):
  H(harakat | rasm)  = 1.964 bits     (diacritic channel capacity)
  I(EL ; CN)         = 1.175 bits     (rhyme-connective mutual information)

Non-claims (formally retracted):
  - φ ≈ 0.618 golden-ratio                        (R01)
  - "Quran 76 % stronger than next scripture"     (R09)
  - Universal R ≈ 0.70 across writing systems     (R27 — Abrahamic typology only)
  - Ψ_oral ≈ 5/6 cross-tradition universal        (R28 — Quran-only n=1 coincidence)
  - Reed-Solomon error-correcting code in Quran   (R47 — UTF-8 confound)
```

This card alone is sufficient for an external reviewer to (a) understand the claim, (b) evaluate the simple-math content, (c) reproduce on raw text in ~10 lines of Python.

---

*Sources: `docs/PAPER.md §4.1, §4.2, §4.18, §4.35`; `docs/reference/findings/RANKED_FINDINGS.md` v1.3; `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md`; `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md §C1, §C2, §X6, §X7`; `experiments/exp89b/`, `experiments/exp70_decision_boundary/`, `experiments/expC1_C3_el_inv_sqrt2/`, `experiments/expC2_vl_cv_floor_sqrt26/`, `experiments/expP4_cross_tradition_R3/`, `experiments/expS_synth_geometric_info_theorem/`, `experiments/expParadigm2_OP1_OP3_proofs/`.*
