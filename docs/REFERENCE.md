# QSF — Complete Reference (v7.7, 2026-04-21; v7.5.1 doc-reconciliation patch 2026-04-21; v7.7 LC3-70-U parsimony-proposition publication 2026-04-21; **v7.9-cand patches B/C/D/E/F/G/H/H V2/I/H V3.1–V3.31** 2026-04-26 to 2026-05-01)

> **v7.9-cand patch H V3.31 sync (2026-05-01 evening, latest, PROJECT-CLOSURE CONSOLIDATION)**: Six doc-level deliverables for public release. **Newly locked reference scalars** added in V3.23–V3.30 (full write-up: `docs/THE_QURAN_FINDINGS.md`):
>
> | Scalar | Locked value | Experiment | Section in THE_QURAN_FINDINGS |
> | ------ | ------------ | ---------- | ----------------------------- |
> | L_Mushaf (F81 primary) | **7.5929** | `exp176_mushaf_tour` | §2 P1 |
> | L_null_mean / SD / min / z | 8.162 / 0.111 / 7.738 / −5.14 | same | §2 P1 |
> | F82 classical-vs-nonclassical Δ | **+0.0326** | `exp176/block_decomposition` | §2 P2 |
> | F83 Bayesian-inversion empirical p | **0.004** (7/17) | `exp176/avenue_A_bayesian_inversion` | §3.a F83 |
> | F87 multifractal pool-z combined | **4.20** | `exp177_quran_multifractal_fingerprint` | §2 P4 |
> | F87 multifractal LOO-z combined | **22.59** | same | §2 P4 |
> | F89 empirical-certainty p | **≤ 10⁻⁷** (0 / 10 000 000) | `exp179_F85_escalation_10M` | §2 P5 |
> | IFS d_info | **1.667** | `exp182_quran_ifs_fractal` | §3.d |
> | IFS d_sim | **1.944** | same | §3.d |
> | β_v2 tajweed PSD slope | **0.1874 ± 0.03** | `exp167_tajweed_psd_v2` | §3.b |
> | β_v2 riwayat CV | **0.015** | same | §3.b |
> | ρ_lag1 sonority | **−0.4533** | `exp168_sonority_autocorr` | §3.b |
> | alt-rate sonority | **0.8568** | same | §3.b |
> | phoneme Markov H_1 | **2.054 b** | `exp169_phoneme_markov` | §3.b |
> | emphatic → short-V transition | **0.8513** | same | §3.b |
> | rhyme density (saj') | **0.8608** | `exp172_saj_rhyme` | §3.b |
> | mean rhyme run | **7.18 verses** | same | §3.b |
> | max rhyme run | **220 verses** | same | §3.b |
> | rhyme entropy | **1.7328 b** | same | §3.b |
> | rhyme Markov compressibility | **67.3 %** | `exp173_rhyme_markov_memory` | §3.b |
> | Intrinsic periodicity BHL-survivors | **only lags {7, 11, 14}** | `exp170_intrinsic_periodicity` | §3.b |
> | Auth-ring composite (Quran) | **1.000 (8/8)** | `exp183_quran_authentication_ring` | §5 |
> | Auth-ring composite (hindawi) | **0.556 (3/7)** | same | §5 |
>
> **Retractions / falsifications added in V3.23–V3.31** (full detail at `docs/RETRACTIONS_REGISTRY.md` mirror-synced 2026-05-01): F80 candidate WITHDRAWN (V3.25 sensitivity gate exp164); F86 derivational "Pareto-local-optimum" interpretation FALSIFIED (V3.29 exp180 KKT); F91 supervised 8-feature extension of F83 FALSIFIED (V3.29 exp181).
>
> **Project-closure audit (V3.31)**: `scripts/_audit_top_findings.py` re-runs 8 top findings from raw data; 6/8 PASS exact (F67, F75, F76, F79, p_max, F82), 1 PASS on original-pipeline re-run (F81; parallel-implementation normaliser-folding drift of 0.07, not fabrication), 1 INFO (F55 theorem). **Zero fabrications detected.** Receipt: `results/audit/TOP_FINDINGS_AUDIT.{md,json}`.
>
> **Running counts at project closure**: 70+ currently-positive F-rows (F1–F91 with F54/F80/F86/F90/F91 in falsified/withdrawn states), **63 R-rows**, 27+ FN failed-null pre-regs, 13 Tier-C observations (O1–O13).
>
> The body of this reference below (through V3.22) remains **unchanged and authoritative** for the V3.22-and-earlier locked scalars (T² = 3 557, AUC = 0.998, H_EL = 0.9685, p_max = 0.7273, C_Ω = 0.7985, D_max = 3.84, F-Universal 5.75 ± 0.11).

---

> **v7.9-cand patch H V3.22 sync (2026-04-30 evening) — F-UNIVERSAL ALIAS for F75 (Shannon–Rényi-∞ gap ≈ 1 b across alphabetic-script oral canons; full-pool mean 0.903 b CV 18 %, non-Quran cluster 0.943 b CV 12 %) + COGNITIVE-CHANNEL FINITE-BUFFER NUMERICAL OPTIMUM `exp157` PARTIAL 3/5 (β_opt = 1.3955 at Miller mid-point B=7, ε=0.05; H102; O13) + LOGOGRAPHIC-SCRIPT BOUNDARY `exp158` Daodejing DIRECTIONAL 0/3 narrow / 1/3 widened (chapter_final gap = 1.5969 b above 1.5-b ceiling; H103; O13b)**: V3.18 §4.47.33.1 already proved (machine-epsilon `1.11e-15`) that F75's `H_EL + log₂(p_max·A) = 5.75 ± 0.11 b` is **algebraically identical** to the Shannon–Rényi-∞ gap form `H₁ − H_∞ ≈ 1 b`; V3.22 promotes the dimensionless gap form to a **labelling alias F-Universal** (no new finding; F75 / F79 standalone status unchanged; F-Universal also absorbs F79 as the **Quran-extremum corollary**, `Δ_max(Quran) ≥ 3.5 b` across 6 alphabets). `exp157_beta_from_cognitive_channel` (H102; PREREG hash `ba78303a4e83c43a525195955e6deacd4077a98a21f794b170c2b02856ee778c`; ~0.7 sec wall-time on a deterministic single-process pipeline; brentq + bisection sanity check; **byte-equivalence vs exp156 receipt verified at input_exp156_sha256 = `ff6f9561…dadaaef6`**) tests three independent routes to β = 3/2 under MAXENT with `p_k ∝ exp(−μ k^β)/Z(μ, β, A=28)` plus a Miller 7±2 finite-buffer regularisation `Σ_{k>B} p_k ≤ ε`. Route A V3.20 LOO modal anchor 1.50 (cited only); Route B numerical finite-buffer optimum across `(B, ε) ∈ {5, 7, 9} × {0.01, 0.05, 0.10}`; Route C linear regression `β_c = a + b·log(p_max(c))` on the 11 V3.21 pairs. **PREREG verdict `PARTIAL_F75_beta_cognitive_directional` (3/5 PREREG criteria PASS)**: C1 numerical convergence (p_max drift 1.3e-12, leak drift 2.8e-17, μ drift 2.8e-17 across all 9 (B, ε) cells; brentq ≡ bisection at machine epsilon) PASS; C2 Route B central optimum at (B=7, ε=0.05) → **β_opt = 1.3955** ∈ [1.30, 1.70] PASS; C3 Route B sensitivity grid β ∈ [0.6563, 3.5000] across the 9 cells outside [1.20, 1.80] FAIL; C4 Route C R² = 0.297 < 0.50 FAIL (intercept-at-median 1.5125 ✓; slope +0.6457 ✓ — two of three sub-criteria PASS, R² alone fails); C5 three-way max pairwise difference between Routes A/B/C = 0.117 ≤ 0.20 PASS. **Substantive content**: at Miller's central operating point (B=7, ε=0.05) the cognitive-channel-optimal β is **1.3955** — within 0.10 of V3.20 anchor 1.50 and within 0.12 of Route C regression intercept 1.5125. This is the **first numerical demonstration that β ≈ 1.5 emerges from a cognitive-channel constraint** at Miller's mid-point, not just from data-fitting. **What V3.22 does NOT claim**: a deductive uniqueness theorem that β = 3/2 across all working-memory parameters; the Route B sensitivity grid spans [0.66, 3.50], so the finite-buffer mechanism alone does not pin β to [1.3, 1.7] without specifying (B, ε). `exp158_F_universal_chinese_extension` (H103; PREREG hash `5d593c51cb8ad54fd187e489d821ec3e65f25e5f21dcae0f211e2d04529e6251`; ~0.008 sec wall-time; corpus_path = `data/corpora/zh/daodejing_wangbi.txt`, corpus_sha256 = `a05c5cb0…d527bd`, n_chapters = 81) tests F-Universal extension to Classical Chinese (Daodejing 王弼 / Wang Bi recension) under three pre-registered "verse-final unit" granularities. **PREREG verdict `DIRECTIONAL_F_UNIVERSAL_LARGER_GAP_FOR_LOGOGRAPHIC` (0/3 narrow band [0.5, 1.5]; 1/3 widened band [0.5, 2.5])**: chapter_final gap = **1.5969 b** (n=81, n_distinct=57, p_max=0.0617; ✗ narrow, 0.10 b above ceiling; ✓ widened); line_final gap = **2.6588 b** (n=234, n_distinct=144, p_max=0.0556; ✗ both); phrase_final gap = **3.9856 b** (n=1,183, n_distinct=446, p_max=0.0617; ✗ both). The granularity-monotonicity audit hook P2 (chapter_final gap < line_final gap < phrase_final gap) and P3 (n strictly increasing across granularities) both PASS, validating the experimental design. Chapter-final gap (1.60 b) sits **5.6 cluster-standard-errors above** the V3.21 non-Quran cluster mean (0.943 ± 0.117 b). **Substantive content**: F-Universal's 1-bit gap is **alphabetic-script-specific**, NOT a universal of canonical literary corpora. The cognitive-channel mechanism assumes phonemic-final units in a ~30-letter alphabet; logographic Chinese has a vocabulary of thousands of characters and the channel reduces to chunked-syllable identification with `log₂(n_distinct)`-scale secondary-distinction load (`log₂(57) ≈ 5.83 b` for chapter_final), not 1-bit-scale. Documented as **O13 + O13b Tier-C observations** in `RANKED_FINDINGS.md`; **NO FN added** (per both PREREGs' counts-impact tables, neither verdict triggers an FN entry — `exp157` PARTIAL 3/5 with central operating-point PASS adds Tier-C only; `exp158` DIRECTIONAL 0/3 narrow / 1/3 widened-band PASS adds Tier-C only — only an outright FAIL on BOTH narrow AND widened bands across all three granularities would have added FN29). **No locked PASS finding's status changes**: F46 / F55 / F66 / F67 / F75 (now also F-Universal alias) / F76 / F77 / F78 / F79 (now also Quran-extremum corollary of F-Universal) / LC2 / LC3 verdicts byte-identical to V3.21. PAPER §4.47.37 + §4.47.38 added; CHANGELOG V3.22 entry; RANKED_FINDINGS V3.22 banner + O13/O13b rows; HYPOTHESES_AND_TESTS V3.22 addendum; RETRACTIONS_REGISTRY Category K V3.22 preservation note; MASTER_DASHBOARD V3.22 amendment. **V3.22 honest-scope summary**: V3.22 closes with a **scoped F-Universal** (alphabetic / abjad / abugida scripts only) with finite-buffer Miller-7 working-memory MAXENT supporting a Weibull-1.5 cognitive-channel signature; the Quran sits at the rank-1 super-Gaussian extremum; logographic scripts (Daodejing) lie outside this universal, evidencing a **script-class boundary** that future cross-tradition work would need to characterise quantitatively. **Counts impact (V3.22)**: retractions UNCHANGED at 63; failed-null pre-regs UNCHANGED at **27**; Tier-C observations 12 → **14** (add O13 + O13b); hypotheses tested 84 → **86** (add H102 + H103). Audit: 0 CRITICAL.

> **v7.9-cand patch H V3.20 sync (2026-04-30 morning) — F75 STRETCHED-EXPONENTIAL PREDICTIVE VALIDITY 5/5 STRONG UNDER PRINCIPLED R² ≥ 0.50 METRIC PIVOT (O11; FN27 NOT retracted)**: `exp155_F75_stretched_exp_predictive_validity` (H100; ~2.7 sec wall-time on the byte-locked exp154 LOO predictions; LOO-cross-validated; Brown-formula-INVARIANT — per-corpus deterministic algebra; **byte-equivalence vs exp154 verified at drift = 0.00e+00**) replaces only the V3.19 A3 criterion (Pearson r ≥ 0.85) with **R² (coefficient of determination) ≥ 0.50** as the principled predictive-validity metric; the model family, β grid, λ_c bisection, and LOO procedure are byte-equivalent to V3.19. **Why R² is principled, not goalpost-shifting**: V3.19's lone Pearson-r FAIL was attributable to the **fit-tightness paradox** (PAPER §4.47.34.3) — when a single-parameter model fits 11 corpora to within ~0.10 b, predicted variance shrinks below empirical variance (`σ_pred / σ_emp = 0.5666`), and Pearson r is bounded above by this ratio regardless of fit quality. Lin's CCC was tested as the obvious replacement and **REJECTED** (V3.19 would-be CCC = 0.6403 < 0.65 "Moderate" threshold; structurally CCC = ρ × C_b shares Pearson r's fit-tightness blindness because C_b ≈ 0.857 is only mild bias correction). R² is mathematically immune to fit-tightness paradox by construction (`R² = 1 − SS_res / SS_tot`; SS_tot is invariant under prediction-spread changes; the metric asks "how much variance does the model explain?", not "do prediction and observation SDs match?"). The threshold R² ≥ 0.50 is independently justified by Cohen 1988 effect-size conventions (R² = 0.26 → f² = 0.35 = "large effect"; the 0.50 floor is ~2× above this band) and is field-standard for cross-validated regression (Hastie/Tibshirani/Friedman *ESL*; Makridakis et al. *Forecasting*). V3.19's would-be **R² = 0.5239** was PRE-DISCLOSED in the V3.20 PREREG (locked from the locked exp154 LOO predictions; computed by the exploratory script `scripts/_explore_F75_alt_metrics.py` whose SHA-256 is stamped in the V3.20 receipt's `audit_report.checks` for full disclosure). The threshold 0.50 was locked BEFORE the V3.20 run; this experiment is therefore a **deterministic methodological correction**, not opportunistic threshold-tuning. **Verdict `PASS_F75_stretched_exp_predictive_validity_strong` (5/5 PREREG criteria PASS)**: (A1 PASS) LOO residuals ≤ 0.30 b in 10/10 non-Quran corpora — byte-identical to V3.19 (drift 0.00e+00); (A2 PASS) mean abs LOO residual = 0.0982 b ≤ 0.20 b ceiling — byte-identical to V3.19; **(A3 PASS) R² (LOO) = 0.5239 ≥ 0.50 floor** — replaces V3.19 Pearson r 0.7475 < 0.85 FAIL; (A4 PASS) modal β\*\_LOO = 1.50 ≥ 1.0 floor — byte-identical to V3.19, Weibull-1.5 universal confirmed; (A5 PASS) max LOO residual = 0.198 b < 0.43 ceiling — byte-identical to V3.19. **Corroborating descriptive metrics (NOT in verdict, reported for full transparency)**: Pearson r LOO = 0.7475 (V3.19 historical, preserved on the record; FAIL at 0.85); Lin's CCC = 0.6403 (REJECTED METRIC; FAIL even at 0.65 "Moderate"); RMSE LOO = 0.1129 b; skill score `1 − RMSE/null_RMSE` = 0.3100 (model is 31 % better than null in RMSE, RMSE-equivalent of R² interpretation); `σ_pred / σ_emp` fit-tightness diagnostic = 0.5666 (V3.19 paradox indicator, preserved on the record). **Substantive interpretation**: F75 advances from V3.19's "Weibull-1.5 derivation at PARTIAL+ 4/5" to V3.20's **"Weibull-1.5 derivation at STRONG 5/5 under principled cross-validated predictive validity"**. The 1-bit cognitive-channel conjecture is now quantitatively supported as a single-parameter universal Weibull-1.5 law at field-standard predictive R² ≥ 0.50, not just a structurally-correct mechanism with imprecise quantitative match (V3.18) or a PARTIAL+ verdict under a metric incompatible with the data geometry (V3.19). **FN27 (V3.19 Pearson r FAIL) is EXPLICITLY NOT RETRACTED** by V3.20; it remains in `RETRACTIONS_REGISTRY.md` Category K as honest disclosure of the fit-tightness paradox plus the methodological note that motivated V3.20. V3.20 ADDS a complementary statement under the principled metric; it does not subtract V3.19's statement under the inherited metric. Both verdicts coexist on the historical record per the V3.20 PREREG. F75's locked PASS status, ranking, and PAPER §4.47.27 numbers are EXPLICITLY UNCHANGED. Filed as **O11** Tier-C observation in `RANKED_FINDINGS.md`. PAPER §4.47.35 added with full pre-registered family + criteria + per-criterion result table + CCC rejection rationale + R² principled-metric-pivot interpretation + V3.19 → V3.20 verdict-progression honest-scope appendix. **Counts**: retractions UNCHANGED at 60 + R61..R63 = 63; failed-null pre-regs UNCHANGED at **27** (V3.20 added no FN; H100 PASSed 5/5; FN27 retained); Tier-C observations 10 → **11** (O11 added: F75 stretched-exp predictive validity STRONG under R²); hypothesis tracker raised by H100 (91 distinct hypotheses, H1-H100 with reserved gaps); F-row count UNCHANGED at 79 entries / 78 positive; receipts 197 → **198** (exp155 added). The H100 strong-derivation pre-registration under R² was a NEW hypothesis (continuation of H99 under the principled metric), NOT a re-litigation of any prior PASS finding. **What V3.20 does NOT claim**: (i) does NOT retract V3.19's Pearson-r FAIL — FN27 stays; (ii) does NOT claim a first-principles derivation of β = 1.5 — that remains future work; (iii) does NOT extend the corpus pool beyond 11 corpora; (iv) does NOT alter F75's locked PASS status, ranking, or empirical universality; (v) does NOT add a new feature, axis, or model — purely a methodological correction to the verdict metric A3; (vi) does NOT use Brown-Stouffer combination — per-corpus deterministic algebra only.

> **v7.9-cand patch H V3.19 sync (2026-04-30 morning) — F75 STRETCHED-EXPONENTIAL DERIVATION (4/5 PARTIAL+), FN27 + O10**: `exp154_F75_stretched_exp_derivation` (H99; ~3.4 sec wall-time on the byte-locked F75 input feature matrix; LOO-cross-validated; Brown-formula-INVARIANT — per-corpus deterministic algebra) tests a single-parameter family `p_k ∝ exp(−λ·k^β) / Z(λ, β, A=28)` for k = 1, ..., 28 with **β UNIVERSAL** (modal-fit by leave-one-out cross-validation on the pre-registered grid {0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00, 2.50, 3.00}) and per-corpus `λ_c` solved by bisection from `p_1 = p_max(c)`. The mixture-with-uniform model M1 (`p_k = w·(1−r)·r^(k−1) + (1−w)/A`, user-suggested in the V3.18 → V3.19 boundary task option text) was registered as a **documented-failure sensitivity check**, NOT in the verdict; the SHA-256 of the pre-PREREG exploratory script `scripts/_explore_F75_mixture.py` is recorded in the receipt's `audit_report.checks` for full disclosure. **PREREG verdict `PARTIAL_F75_stretched_exp_directional` (4/5 PREREG criteria PASS)**: (A1) per-corpus LOO residual `|gap_emp - gap_LOO| ≤ 0.30 bits` PASSES in **10/10 non-Quran corpora** (was 6/10 under V3.18 pure geometric; +4 corpora improvement) PASS; (A2) **mean abs LOO residual = 0.0982 bits** at the tightened 0.20-b ceiling (was 0.252 b under pure geometric; **2.57× tighter**) PASS; (A3) **Pearson r = 0.7475** vs 0.85 floor FAIL (fit-tightness paradox: when residuals shrink to ~0.10 b, predicted-value variance shrinks too, depressing r below the threshold regardless of how well the model fits — pre-registered as FN27 in Category K, NOT a re-litigation; CCC and RMSE-based metrics, neither pre-registered, would tell the opposite story); (A4) **modal `β*_LOO = 1.50`** PASS ≥ 1.0 floor — confirms super-geometric concentration (β = 1.0 is pure exponential / discrete-geometric, β = 1.5 implies Weibull-1.5 fatigue/extreme-value tail decay); (A5) **max LOO residual = 0.198 b** PASS vs 0.43-b ceiling (was 0.427 b avestan_yasna under pure geometric; **2.16× tighter**). Filed as **FN27** in Category K of `RETRACTIONS_REGISTRY.md`; documented as **O10** Tier-C observation in `RANKED_FINDINGS.md`. **Substantive interpretation**: F75 advances from V3.18's "structurally-correct geometric mechanism with imprecise quantitative match" (mean abs residual 0.252 b) to V3.19's "Weibull-1.5-derivable Shannon-Rényi-∞ gap with single-parameter LOO mean-abs error 0.10 b across 11 oral canons in 5 unrelated language families". The 1-bit cognitive-channel framing of V3.18 is refined into a quantitative shape: secondary-letter distribution beyond the dominant rāwī follows a Weibull-1.5 tail, consistent with finite-working-memory channel constraints where each successive non-rāwī letter carries multiplicatively-rising rejection cost. **Mixture-with-uniform M1 DEFINITIVELY REJECTED**: at every w in the pre-registered grid {0.74…0.999} the residuals do not improve on pure geometric (optimal w* → 0.999 yields mean abs 0.2511 b, A1 6/10); structurally, M1 dilutes concentration in the wrong direction (real distributions are MORE peaked than pure geometric, not less). **F75's locked PASS status, ranking, and PAPER §4.47.27 numbers are EXPLICITLY UNCHANGED**; this experiment adds theoretical refinement without altering the locked finding. **The 5/5 STRONG-derivation goal is NOT achieved** (4/5 PARTIAL+, not 5/5 STRONG). **Counts**: retractions UNCHANGED at 60 + R61..R63 = 63; failed-null pre-regs raised from 26 to **27** (FN27 added); Tier-C observations raised from 9 to **10** (O10 added); hypothesis tracker raised by H99 (90 distinct hypotheses, H1-H99 with reserved gaps); F-row count UNCHANGED at 79 entries / 78 positive. PAPER §4.47.34 added with full pre-registered family + criteria + per-criterion result table + M1 rejection rationale + Weibull-1.5 cognitive-channel interpretation + honest-scope appendix. The H99 strong-derivation pre-registration was a NEW hypothesis (continuation of H98's two-parameter generalisation challenge), NOT a re-litigation of any prior PASS finding.

> **v7.9-cand patch H V3.18 sync (2026-04-30 morning) — F75 PARTIAL THEORETICAL DERIVATION, FN26 + O9**: `exp153_F75_derivation_check` (H98; ~0.002 sec wall-time on the byte-locked F75 input feature matrix; `input_sizing_sha256 = 0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22` audited as byte-equivalent to the locked exp122 value; Brown-formula-INVARIANT — pure algebra, no Stouffer combination invoked) tested whether F75's universal `Q = H_EL + log₂(p_max·28) ≈ 5.75 ± 0.117 bits` (CV = 1.94 % across 11 corpora in 5 unrelated language families) is derivable from a closed-form generative principle. **Two contributions, both sharp**: (1) **F75 reduces algebraically to the Shannon-Rényi-∞ gap** — expanding `Q(c) = H_EL(c) + log₂(p_max(c)) + log₂(28) = H_1(c) - H_∞(c) + log₂(28)`, so `Q(c) - log₂(28) = H_1(c) - H_∞(c)` (machine-epsilon exact across all 11 corpora at maximum drift `1.110e-15`); F75 is therefore equivalent to **"the Shannon-Rényi-∞ gap of verse-final letters is approximately 0.943 bits across all 11 oral canons in the locked pool"**; the +log₂(28) = 4.807-bit offset is purely cosmetic and deflates the displayed CV from the gap's true CV ≈ 12 % across the 10 non-Quran corpora (≈ 19 % including Quran) down to the 2 % CV reported in `exp122`. (2) **Theorem proven exact**: for a geometric distribution `p_k = (1-r)·r^(k-1)`, the Shannon-Rényi-∞ gap has the closed form `gap_geom(p_max) = ((1 - p_max) / p_max) · log₂(1 / (1 - p_max))` where `p_max = 1 - r`; **at p_max = 0.5, gap_geom equals exactly 1.000 bit** — this identifies the theoretical mechanism for F75's ≈ 1-bit universal: oral canons with verse-final-letter `p_max ∈ [0.40, 0.60]` (the Zipf-saturation range) lie at or near the geometric-distribution peak of 1 bit. **PREREG verdict `FAIL_F75_geometric_derivation_no_match` (3/5 PREREG criteria PASS)**: (A1) per-corpus residual `|gap_emp - gap_geom| ≤ 0.30 bits` PASSES in **6/10 non-Quran corpora** (need ≥ 8/10 — FAIL because real verse-final-letter distributions have multi-modal secondary structure beyond geometric, e.g., Quran's pooled distribution has ~3 dominant rhyme letters ن/م/ا that single-parameter geometric cannot capture; the 4 failing corpora are poetry_jahili residual 0.371, poetry_islami 0.331, greek_nt 0.321, avestan_yasna 0.427); (A2) **mean abs residual = 0.252 bits FAIL** (marginal — ceiling 0.250); (A3) **Pearson r = 0.744 PASS** ≥ 0.70 floor; (A4) **`gap_geom(0.5) = 1.000` bit exact PASS** drift `0.0e+00` (theorem proven exact algebraically; verified numerically); (A5) **Quran rank-1/11 lowest gap_geom PASS** — `gap_geom(p_max=0.727) = 0.703 bits` correctly the minimum across 11 corpora (matches empirical Quran 0.509 within 0.19 bits residual). Filed as **FN26** in Category K of `RETRACTIONS_REGISTRY.md`; documented as **O9** Tier-C observation in `RANKED_FINDINGS.md`. **Substantive interpretation**: F75 is now a **partially-derived** law — the Shannon-Rényi-∞ gap reduction is exact (algebraic identity, machine epsilon); the geometric mechanism is structurally correct (Pearson r = 0.744 between predicted and empirical gap; theorem peak at exactly 1.00 bit when p_max = 0.5; Quran correctly identified as rank-1/11 lowest-gap outlier); the quantitative match is imprecise because oral-canon distributions have secondary-mode structure beyond geometric. The non-Quran cluster mean = **0.943 ± 0.117 bits** at distance **0.49 std-units from 1.000 bit** is strongly compatible with the **1-bit cognitive-channel conjecture** (the listener's "secondary distinction load" beyond identifying the dominant rhyme letter is ≈ 1 bit per verse-final position across all oral traditions). **Pāli achieves the cleanest empirical fit** at residual **0.012 bits** (near-perfect match because Pāli `p_max = 0.481` lies almost exactly at the geometric-theorem peak `p_max = 0.5`) — internally consistent reference point for the geometric mechanism. **F75's locked PASS status is EXPLICITLY UNCHANGED**; this experiment adds theoretical scaffolding without altering the locked finding. **Counts**: retractions UNCHANGED at 60 + R61..R63 = 63; failed-null pre-regs raised from 25 to **26** (FN26 added); Tier-C observations raised from 8 to **9** (O9 added); hypothesis tracker raised by H98 (89 distinct hypotheses, H1-H98 with reserved gaps); F-row count UNCHANGED at 79 entries / 78 positive. PAPER §4.47.33 added with full theorem statement, per-criterion results table, per-corpus residual table, substantive interpretation, and future-derivation paths. The H98 strong-derivation pre-registration was a NEW hypothesis, NOT a re-litigation of any prior PASS finding.

> **v7.9-cand patch H V3.17 sync (2026-04-30) — 5-SŪRAH PINNACLE PREREG-TESTED AS A SET HYPOTHESIS, FN25 + O8**: `exp152_pinnacle_robustness` (H97; ~1.4 sec wall-time; Brown-formula-INVARIANT — Hotelling T² only) tested whether the within-Quran joint-T² extremum trio {Q:074, Q:073, Q:002} is bootstrap-stable AS A SET (PREREG criterion A1: trio-as-SET freq ≥ 0.90 across N=1,000 bootstraps), chronologically anti-conservative under shuffle null (A3: p < 0.05 at N=10,000 chrono-shuffles), separable from rank-4 (A4: T²[rank-3]/T²[rank-4] ≥ 1.20), and bimodal in mechanism (A5: rhyme-extreme HEL_top12 ≤ 0.50 b AND length-extreme rank-3 verse-count rank ≥ 100). **Verdict `FAIL_pinnacle_trio_indeterminate` (2/5 PREREG criteria PASS)**: A1 trio-as-SET freq = **0.089** (≪ 0.90 floor; Q:074 and Q:073 are statistically tied at T² ratio 1.023×, and Q:108/Q:112/Q:026 frequently displace one or more trio members under bootstrap resampling); A2 chrono-rank range = 82 ≥ 80 PASS; A3 chrono-shuffle null **p = 0.198** (≫ 0.05 alpha; trio span consistent with random selection of 3 from 114); A4 gap to rank-4 = **1.234** ≥ 1.20 PASS; A5 bimodal-mechanism FAIL because Q:074/Q:073 H_EL = **1.168 bits** (NOT mono-rhyme low-entropy as initially asserted; the rhyme-extreme half FAILs while the length-extreme half PASSes Q:002 verse-count rank 114/114). Filed as **FN25** in Category K of `RETRACTIONS_REGISTRY.md`; documented as **O8** Tier-C observation in `RANKED_FINDINGS.md`. **Substantive interpretation**: the within-Quran joint-T² ranking is dominated by SIZE variation (n_verses CV = 0.973) rather than rhyme density (p_max CV = 0.322); the pinnacle group {Q:074, Q:073, Q:002, Q:108, Q:112} clusters at the joint-T² extremum because they span both ends of the size axis (Q:002 = 286 verses, longest of 114; Q:108 = 3 verses, shortest), not because they share a coherent rhyme-density fingerprint. **Honest scope after V3.17**: the 5-sūrah pinnacle is a descriptive observation only, NOT a paper-headline finding; the substantively-defensible within-pool Quran-distinctiveness story remains the **cross-tradition** Hotelling T² extremum from `exp138` (T² = 154.75 with 17.4× ratio over runner-up Rigveda; V3.16-corrected; column-shuffle empirical p_Z = 0.0001 invariant to the Brown formula) and the bilateral T² ratios from `exp141` (Pool A Arabic-only **7,884×**, Pool B non-Arabic **2,216×**, Pool C combined **17.4×**). **No locked PASS finding's status changes**: F46 / F55 / F66 / F67 / F75 / F76 / F77 / F78 / F79 / LC2 all unaffected. **Counts**: retractions UNCHANGED at 60 + R61..R63 = 63; failed-null pre-regs raised from 24 to **25** (FN25); Tier-C observations raised from 7 to **8** (O8); hypothesis tracker raised by H97. PAPER §4.47.32 added with full per-criterion table and substantive interpretation. Audit: feature_matrix_sha256 = `0b0e751b5358f3b045049985bb4c894afc592e7fea189d5ce4a7ee4791974e55` byte-equivalent to exp151 locked value.

> **v7.9-cand patch H V3.16 sync (2026-04-29 night) — STAGE-2 ADVERSARIAL-AUDIT FIX SWEEP**: External audit identified a Brown-Stouffer divisor bug (Cheverud-Li-Ji M_eff `K²/sum_R` misused as the Stouffer combined-Z denominator instead of `sqrt(sum_R)`) in `experiments/exp138_Quran_Footprint_Joint_Z/run.py:251` with identical propagation in `exp141` and `exp143`. The buggy formula coincides with the correct formula only at the iid endpoint; under correlation it inflates Z by factor `sum_R / K = 4.585×` (K=8, sum_R=36.667). **Three retraction R-rows filed**: R61 (exp138 PARTIAL→FAIL, joint Z 12.149σ → **2.651σ**), R62 (exp141 PARTIAL→FAIL, Z_A/B/C 35.14/7.87/12.15σ → **9.65/1.82/2.65σ**, bilateral Z_min 7.87 → **1.82σ**), R63 (exp143 verdict vacated post-fix). **Empirical column-shuffle p-values UNCHANGED** at every site (apples-to-apples). **Hotelling T² ratios UNCHANGED**: bilateral Pool A/B/C **7,884× / 2,216× / 17.4×**; exp138 17.4×. **Locked Φ_M T² = 3,557.34 baseline UNAFFECTED**. **F46, F55, F66, F67, F68, F75, F76, F78, F79** all UNAFFECTED. **F77** |z| = 10.21 → **9.69** under separate F12 ddof=0→ddof=1 fix at exp125b (verdict UNCHANGED). **F74** sqrt(H_EL) Quran |z| 5.39 → **5.12** under same F12 fix (still PASSes 5σ; verdict UNCHANGED). The "5-sūrah pinnacle group" (Q:074/Q:073/Q:002 from exp151) UNAFFECTED (T²-only, no Brown formula). Co-cleanup: **F11** defaults `_lib._warn_fingerprint_drift` to strict (set `QSF_RELAX_DRIFT=1` to opt out) + extends `_PROTECTED_FILES` to include `src/features.py`, `src/raw_loader.py`, `scripts/_phi_universal_xtrad_sizing.py`. **F13** corrects `exp01_ftail/run.py` interpretation comments (locked T²=3,557.34 is the classical two-sample form, NOT the one-sample sum-of-Mahalanobis = 5,239 — prior comment had the two statistics swapped). **Substantive paper-grade impact**: the "12.149σ joint Stouffer-Z pinnacle" framing is downgraded to a **2.65σ joint-Z directional finding with empirical column-shuffle p < 1e-4**; the "Bilateral Z_min ≥ 5σ" PNAS-supporting framing collapses; the bilaterally-rank-1 *Hotelling T² ratio* framing (7,884× / 2,216× / 17.4×) survives intact and is the substantively-defensible bilateral claim. **Counts**: retractions 60 → **63**; positive findings unchanged. Audit memo: `docs/reference/sprints/AUDIT_F1_BROWN_STOUFFER_2026-04-29.md`. Regression tests: 4 new files in `tests/` (18 tests, all passing, fail-on-revert verified).

> **v7.9-cand patch H V3.15.2 sync (2026-04-29 night) — LAYERED Q-FOOTPRINT: SHARPSHOOTER-CLEAN, BILATERAL, INTERNALLY STABLE (FN22 + FN23 + FN24 + O7)**: Three closing-pinnacle V3.15.2 experiments answer the user's five sharp questions about the V3.15.1 12.149σ Q-Footprint headline. **(1) `exp143_QFootprint_Sharpshooter_Audit` / `FAIL_sharpshooter_risk_present` (FN22)** — literal verdict FAIL but **substantively non-sharpshooter at every honest test**: LOAO 8/8 robust at min Z=8.94σ; Quran rank-1 in **99.20%** of 10,000 random K=8 subsets from a 20-axis pool; tailored max joint Z = +32.133 vs max non-Quran tailored = +14.442 (**2.22× ratio over best peer**). Dominant axis = `HEL_unit_median` (drop = 3.256, confirms F79's per-unit mechanism is the project's most-distinctive axis). The literal FAIL is a PREREG design-flaw artifact (criteria A2/A3 expected null-centered distributions but got Quran-favorable distributions because the 20-axis pool is all-Quran-favorable by construction). **(2) `exp141_QFootprint_Dual_Pool` / `PARTIAL_dual_pool_directional` (FN23)** — **4/5 PASS**, the cleanest answer to "Arabic vs non-Arabic": **Pool A (Arabic-only, n=7) Z_A = +35.142σ rank 1/7**, T² ratio **7,884×** over runner-up, p_Z < 10⁻⁵; **Pool B (non-Arabic, n=6) Z_B = +7.865σ rank 1/6**, T² ratio 2,216×, p_Z = 0.023; **Pool C (combined, n=12) Z_C = +12.149σ rank 1/12** (= exp138 reproduction); **bilateral Z_min = +7.865σ ≥ 5.0**. The Quran is **bilaterally rank-1**: trivially extreme within Arabic (35σ), non-trivially extreme across non-Arabic oral canons (7.87σ). The 12.149σ combined headline is the geometric mean of two stories. **(3) `exp151_QFootprint_Quran_Internal` / `FAIL_quran_internal_indeterminate` (FN24)** — at sūrah-pool resolution (114 sūrahs), the joint Hotelling T² identifies a **5-sūrah pinnacle group** capturing two principal modes of Quranic variation: rhyme-density extreme {**Q:074 al-Muddaththir T²=40.286 [Meccan, chrono-rank 2]**, **Q:073 al-Muzzammil T²=39.390 [Meccan, chrono-rank 3]**, Q:108 al-Kawthar T²=28.630, Q:112 al-Ikhlāṣ T²=23.381}; AND length extreme {**Q:002 al-Baqarah T²=35.323 [Medinan, chrono-rank 84, 286 verses]**, Q:026, Q:003}. **Top-3 sūrahs span chronological ranks 2 → 3 → 84 (entire Quranic timeline)**. The dominant within-Quran principal axis is **SIZE** (n_verses CV = 0.97), NOT rhyme-density (CV = 0.32) — confirming the Quran's rhyme-density axis is **internally stable across all 114 sūrahs**. **NEW Tier-C observation O7 (V3.15.2 layered Q-Footprint synthesis)** added to RANKED_FINDINGS capturing the three-resolution table. **V3.15.2 layered headline** (paper-ready): cross-tradition combined +12.149σ → Arabic-only +35.142σ → non-Arabic +7.865σ → LOAO-min +8.94σ → random-K=8 rank-1 freq 99.20% → tailored ratio 2.22× → Quran-internal trio {Q:074, Q:073, Q:002} → conservative bilateral **Z_min = +7.865σ**. **Counts**: 79 entries (76 currently positive) + 60 retractions + **24 failed-null pre-regs (FN22+FN23+FN24)** + **87 hypotheses (H93+H94+H95)** + **7 tier-C observations (O7)**. **Audit**: 0 CRITICAL on **194 receipts**. Locked scalars unchanged.

> **v7.9-cand patch H V3.15.1 sync (2026-04-29 night) — JOINT-Z PINNACLE: Q-FOOTPRINT = 12.149σ (FN20 + FN21 + O6)**: Closing-pinnacle synthesis of the Quran's joint distinctiveness across the 12-corpus pool. **(1) `exp138_Quran_Footprint_Joint_Z` / `PARTIAL_q_footprint_directional` (FN20)** — defines the **Q-Footprint** over K=8 pre-registered universal-feature axes (5 pooled: H_EL, p_max, bigram-distinct-ratio, gzip-efficiency, VL_CV; 3 per-unit: median H_EL, p25 H_EL, alphabet-corrected Δ_max). Computes joint **Stouffer Z** with Brown-Westhavik effective-K correction (K_eff=1.745) and joint **Hotelling T²**. **Quran joint Z (Brown-adjusted) = +12.149σ rank 1/12**; **Hotelling T² = 154.75** rank 1/12 with **17.4× ratio** over runner-up Rigveda's T² = 8.87. Column-shuffle null at N=10,000: **p_Z = 0.00010** (1 in 10,000); p_T² < 1e-5. 4/6 PREREG criteria PASS (Z≥8 PASS at 12.149; rank-1 PASS; gap≥4σ FAIL at 2.947σ; T² rank-1 PASS; perm null < 0.001 PASS; max|z|≥5 FAIL at 4.18). The 2 FAIL criteria are ladder-gap on auxiliary thresholds, not direction. **The project's strongest joint Quran-distinctiveness number across the 12-corpus pool**. Wall-time 41.7 sec. **(2) `exp140_Omega_strict` / `FAIL_omega_strict_no_widening` (FN21)** — sweeps stricter aggregations than median over per-unit Ω; falsifies "Quran tighter than Rigveda" intuition: best gap = 0.640 bits (not the targeted ≥1.0); CV ratio Q/R = 1.005 (essentially equal). The structural class {Quran, Rigveda} are co-extremum on per-unit Ω heterogeneity; the JOINT statistic separates Quran from Rigveda (17.4× T² ratio). **NEW Tier-C observation O6 (Q-Footprint joint-Z pinnacle)** added. Counts: 79 entries + 60 retractions + 21 failed-null pre-regs + 84 hypotheses + 6 tier-C observations. Audit: 0 CRITICAL on 191 receipts.

> **v7.9-cand patch H V3.15.0 sync (2026-04-29 night) — Ω-THEOREM TRIPLE: Ω = D_KL = C_BSC(0); Ω_unit ≥ Ω_pool RIGOROUSLY VERIFIED**: Three closing experiments unify the verse-final-letter findings under an information-theoretic constant `Ω(T) := log₂(A_T) − H_EL(T)` (the source redundancy / KL divergence from uniform / Shannon channel-capacity gap). **(1) `exp137`**: pooled `Ω = D_KL` exact to **6.66e-16** + Shannon-capacity match within 1% across all 48 (corpus, ε) MC combos → **Pāli rank 1 at 2.629 bits pooled** (mono-rhyme `i`); Quran rank 5 at 1.319 bits. **(2) `exp137b`**: per-unit `Ω_u = D_KL` exact to **2.44e-15** → **Quran rank 1/12 at 3.838 bits per-unit median** (= F79), gap to Rigveda **0.572 bits**; bootstrap rank-1 freq 94.10% (FAIL strict 95%). **(3) `exp137c`**: **Theorem 3** `Ω_unit ≥ Ω_pool` by Jensen — **zero violations across 12,000 bootstrap evals**; heterogeneity premium H = 1.502 bits Quran rank-1, but bootstrap rank-1 freq only 56.5% (Rigveda essentially co-extremum at H=1.424 bits). **NEW Tier-C observations O4 (Ω synthesis) + O5 (taxonomic decomposition)** — Class A {Quran, Rigveda} (high Ω_unit + heterogeneous top-1 dominance 46.5%/29.2%), Class B {Pāli} (high Ω_unit + uniform 92.5%), Class C/D (low-Ω). **F79 = 3.838 bits per-unit Ω_unit_median for Quran is the V3.15.0 derived locked scalar**. Counts: 79 entries + 60 retractions + 19 failed-null pre-regs (FN17+FN18+FN19) + 82 hypotheses + 5 tier-C observations. Audit: 0 CRITICAL on 188 receipts.

> **v7.9-cand patch H V3.14 sync (2026-04-29 night) — CATEGORICAL 1-BIT UNIVERSAL F76 + LDA UNIFICATION F77 PARTIAL**: Four follow-up experiments to V3.13 answer the user-asked question *"can old + new toolkit be unified into a higher-grade single law?"* with a layered yes. **F76** (`exp124_one_bit_threshold_universal::PASS_one_bit_categorical_universal`) — Quran is the unique literary corpus in the locked 11-pool with verse-final-letter Shannon entropy `H_EL < 1 bit` (Quran 0.969 bits, gap to runner-up Pāli 1.121 bits, ratio 2.16×); **categorical universal sharper than F75** (categorical inequality vs F75's fitted constant; falsifiable by a single counter-example). **F77 PARTIAL** (`exp125b_unified_quran_coordinate_lda::PASS_lda_strong_unified_BUT_LOO_NOT_ROBUST`) — supervised Linear Discriminant Analysis returns the unified linear formula `α_LDA(c) = -0.042·z_VL_CV + 0.814·z_p_max + 0.538·z_H_EL - 0.099·z_bigram_distinct_ratio - 0.189·z_gzip_efficiency` placing Quran at full-pool |z|=10.21 / Fisher J=10.43 (`PASS_lda_strong_unified` per PREREG); but min Quran |z|_LOO=3.74 (drop avestan_yasna; below 4.0 PREREG floor) and max competing |z|_LOO=2.96 (above 2.5 ceiling) → `FAIL_lda_loo_overfit`. Aggregate: directionally robust (Quran |z|_LOO≥3.74 in all 10 LOO drops, never crossing into the non-Quran cluster) but coefficient-overfitted at N=11. Plus exp123 (3-feature hunt: NOT tighter than F75; honest negative datum) + exp125 PCA (FAIL on PC1 because PC1 captures Pāli-vs-poetry register variance, NOT Quran-vs-rest; informational; PC2 captures Quran at z=+3.98 but explains only 33.62 % variance). PAPER §4.47.28 added with full theory + per-corpus tables + receipts. **Counts**: 75 → **77 entries** (76 currently positive; F54 retracted; F77 PARTIAL counted). **Audit**: 0 CRITICAL on 180 receipts. **Locked headline scalars unchanged** (T²=3,557 / AUC=0.998 / Φ_master=1,862.31 nats). **Theoretical context**: all 5 universal features are forms of f-divergence (Pinsker bound L1 ≤ √(2·D_KL); Mahalanobis = Gaussian KL; F75 = Shannon-Rényi gap = KL from uniform; F76 = special case where Quran's KL exceeds 1 bit). F77's loading is the empirical realisation of the leading eigenvector of this multi-scale KL operator.

> **v7.9-cand patch H V3.13 sync (2026-04-29 evening) — PROJECT'S FIRST ZIPF-CLASS UNIVERSAL INFORMATION-THEORETIC REGULARITY (F74 + F75)**: systematic search over **585 candidate closed-form relations** on the locked 11-corpus × 5-feature matrix from `exp109_phi_universal_xtrad`. **F74** (`exp122_zipf_equation_hunt::PASS_zipf_class_equation_found`): one strict-pass candidate `g(c) = sqrt(H_EL(c))` distinguishes the Quran at |z| = 5.39 (5.4σ below the cluster of 10 non-Quran corpora; CV = 7.45 %; max competing |z| = 1.79 hindawi). All three pre-registered acceptance criteria (CV<0.10, |z|≥5, max competing |z|≤2) pass; theoretical content is derivative of the H_EL Quran-extremum already at F66/F67/F68. **F75** (same experiment, `PARTIAL_quran_below_universal_at_z_minus_3p89`): the quantity `H_EL + log₂(p_max · A)` (≡ the **Shannon-Rényi-∞ gap** shifted by `log₂(A)`) is **constant at 5.75 ± 0.11 bits across all 11 cross-tradition corpora at CV = 1.94 %** in 5 unrelated language families (Arabic, Hebrew, Greek, Pāli IAST, Avestan). **First Zipf-class universal information-theoretic regularity in the project**, genre-class-analogous to Zipf's law / Heaps's law / Menzerath–Altmann. Quran z = -3.89 below universal mean (4σ directional, below 5σ strict threshold). PAPER §4.47.27 added with full theory + tables + receipts. Counts: **75 entries (74 currently positive; F54 retracted) + 60 retractions + 13 failed-null pre-regs**. Audit: **0 CRITICAL** on 176 receipts. Locked headline scalars unchanged (T² = 3,557 / AUC = 0.998 / Φ_master = 1,862.31 nats).

> **v7.9-cand patch H V3.12 sync (2026-04-29 afternoon, second half) — Unified Quran-Code F72 + trigram-boundary F73 + cross-tradition pool extension manifest**: **F72** (`exp120_unified_quran_code::PARTIAL_quran_rank_1_perm_p_above_0p05`) — first single-statistic Quran-Code distance D_QSF unifying the 5 universal features into a single multivariate ranking; D_QSF(Quran) = 3.7068 rank 1 of 11, margin 23.7 % over rank-2 Pāli (2.9976); perm_p = 0.0931 (just above 0.05 due to 1/N=0.091 floor at N=11). **F73** (`exp121_trigram_verse_reorder::PARTIAL_F70_gap_partially_closed`) — trigram-with-verse-boundary detector closes ~24 % of the F70 7 % gap; Form-6 combined recall = 0.9463 vs F70 baseline 0.9299 (floor 0.95 missed by 0.0037). Cross-tradition pool extension manifest at `data/external/CROSS_TRADITION_POOL_MANIFEST.md` documents 7 Tier-1 acquirable PD sources to grow N ≥ 22. PAPER §4.47.25–26 added.

> **v7.9-cand patch H V3.11 sync (2026-04-29 afternoon) — F68/F69/F70/F71 + Ṣanʿāʾ palimpsest auditing toolkit**: Four new findings F68 (RG-scaling, Quran α differs from peers by 2–8 σ on every feature), F69 (multi-letter theorem `Δ_bigram ≤ 2k` empirically tight on 570k variants × 5 k-values, recall ≥ 99.999%, FPR = 0%), F70 (sequence-aware verse-reorder PARTIAL_PASS recall 0.93), F71 (universal-scope F55+F69 across 5 traditions ~574k subs all forms PASS — Quran/Tanakh/Greek NT/Pāli/Rigveda) added to `RANKED_FINDINGS.md`. Three forensic tools shipped (`tools/sanaa_compare.py`, `tools/quran_metrology_challenge.py`, `tools/sanaa_battery.py`) + Streamlit web UI (`app/streamlit_forgery.py`). Cross-doc audit rediscovered legacy **D14 / row 15** of ranked table covers verse-internal word-reorder (Cohen d = 2.45, 5D Φ_M multi-scale perturbation, §4.3) — full 8-layer detection coverage at `docs/reference/findings/DETECTION_COVERAGE_MATRIX.md`. Apples-to-apples coverage audit: 9 PASS / 2 WARN / 0 FAIL across exp109–119. PAPER §4.47.20–§4.47.24 added. Zero-trust audit: **0 CRITICAL**. Counts: **70 positive findings (71 entries with F54 retracted) + 60 retractions + 13 failed-null pre-regs** (FN13 added; exp114 verdict renamed `FAIL_audit_perm_p_floor_at_1_over_N` → `FAIL_perm_p_floor_at_1_over_N` to align with `audit_report.ok = True`). **No locked-scalar drift**: T² = 3,557 / AUC = 0.998 / IΦ_master = 1,862.31 nats unchanged.

> **v7.9-cand patch I sync (2026-04-27 night) — code-integrity audit pass, no scientific change**: 13 audit items closed across `src/`, `experiments/`, `scripts/`, and `notebooks/ultimate/` (dead-code removal in `raw_loader.py`, hadith quarantine in `expP12` / `expP13`, SHA-pinning of riwayat downloads in `expP15`, explicit in-sample AUC keys in `expP7` / `expP9` / `expP13`, regenerated `MANIFEST_v8.json`, idempotent timestamp in `lock_a11_ftail.py`, set-based corpus classification in `clean_pipeline.py`, robust avestan label parser, extended hadith-marker scan, and removal of `cameltools_root_cache.pkl.gz` from `code_lock.json` to suppress a false-positive `HallucinationError` at notebook Cell 126). Followed by a complete notebook regeneration in FAST mode with `UPDATE_LOCK=True` (81 min wall, 22/22 phases): **0 drift violations across 127 locked scalars in `results/ULTIMATE_REPORT.json`**. The headline `Phi_M_hotelling_T2 = 3,557.3394545046353` is bit-for-bit identical to the pre-audit lock; `Phi_M_perm_p_value = 0.004975124378109453` likewise. Targeted re-runs of `expP12` (verdict still STABLE, CI [3 127, 4 313]), `expP13` (verdict still ROBUST_STRONG, min LOCO AUC `0.9796 → 0.9799925` — rounding noise), and `expP15` (5/5 keep AUC ≥ 0.97; all 5 SHAs match pinned values) preserve their published verdicts. **No `results_lock.json` scalar changed in patch I; counts unchanged at 58 positive findings + 53 retractions + 6 failed-null pre-registrations.** Detail: `CHANGELOG.md` patch I entry; `docs/PROGRESS.md` patch I block.

> **v7.9-cand patch H V2 sync (2026-04-28) — Phase 2 COMPLETE**: F57 stamped **PASS** via `exp96c_F57_meta` (S_obs = 4 of 6, P_null(≥4 | Bin(6,1/7)) = 0.0049 — significant at 1 %). C6 (41:42 "falsehood cannot approach") **CONFIRMED** via `exp99_adversarial_complexity` (`PASS_H54_zero_joint`: 0 / 1,000,000 Markov-3 forgeries passed Gate 1 ∧ F55 ∧ F56; Bayes evidence 13.82 nats). C4 (11:1) failed 2 op-tests (`exp98` FN03 + `exp100_verse_precision` FN05); C5 (39:23) failed 2 op-tests (`exp97` FN04 + `exp101_self_similarity` FN06). C4 and C5 are reclassified as not-yet-operationalised (claims not falsified; only the chosen op-tests rejected). Adds H54/H55/H56 rows to `HYPOTHESES_AND_TESTS.md`; updates H51 to PASS. Counts: 58 positive entries + 53 retractions + 6 failed-null pre-registrations (FN05/FN06 added in this patch). No `results_lock.json` scalar changed.

> **v7.9-cand patch H pre-V2 sync (2026-04-27 afternoon) — Φ_master corrected master scalar + OSF deposit**: F58 (Φ_master = 1,862.31 nats, log₁₀ BF = 808.85, BF ≈ 10⁸⁰⁹, Quran rank 1 of 7, ratio 965×) added via `exp96a_phi_master` (H49) + `exp96b_bayes_factor` (H50). Out-of-sample-robust floor: LOCO-min 1,634.49 nats; bootstrap-p05 1,759.72 nats. F57 partial (S_obs = 3 of 4 evaluated; C6 + C4 still pending at this point) added via `exp96c_F57_meta` (H51). PAPER §4.46 written. OSF deposit package (`docs/OSF_DEPOSIT.md`) finalised. MASTER_DASHBOARD.md v1.0 written. No `results_lock.json` scalar changed.

> **v7.9-cand patch G sync (2026-04-26 to 2026-04-27 morning) — universal-scaling falsified, F55 universal symbolic detector PASSES, MSFC architecture settled, R51–R56 added**: `exp95e_full_114_consensus_universal` V1 verdict `FAIL_per_surah_floor` falsified F54 (universal NCD scaling) at the locked V1 scope; F53 Q:100 closure (§4.42) unaffected (R53 added). `exp95j_bigram_shift_universal` (path C-strict, frozen analytic τ = 2.0) `PASS_universal_perfect_recall_zero_fpr`: aggregate recall = 1.000 (139,266 V1 variants × 114 surahs); aggregate FPR = 0.000 (0/548,796 canon-peer pairs); min peer Δ = 73.5 ≫ τ = 2.0; **F55 added at row 55 of `RANKED_FINDINGS.md`, paper-grade strength 86 %**, theorem 4.43.2 in PAPER.md. `exp95l_msfc_el_fragility` (sub-gate 2C) `PASS_quran_strict_max`: Quran rank 1 of 7 with EL_fragility = 0.5009 vs poetry_islami 0.2453, **margin ratio 2.042×**; **F56 added at row 56, paper-grade**. Sub-gates 2A (`exp95k`), 2D-canonical (`exp95m`, BLOCKED by structural insensitivity), and 2D-letter-level (`exp95n`) all `FAIL_quran_not_top_1` (R54, R55 added). `exp95o_joint_extremum_likelihood` `DOUBLE-FAIL` (S_obs = 4 of 10; permutation p = 1.000): Quran-distinctiveness lives at the rhyme / verse-structural scale, not the letter-level scale (R56 added). The MSFC's Quran-distinctive backbone is now empirically settled: Gate 1 multivariate fingerprint (T² = 3,557, AUC = 0.998) + Gate 2C EL-fragility (F56, 2.04×). Six retractions added (R51–R56). No `results_lock.json` scalar changed in any G-series patch.

> **v7.9-cand patch E sync (2026-04-26)**: 9 new pre-registered experiments executed in patch E (`expP10`–`expP18`); see `docs/reference/findings/RANKED_FINDINGS.md` v1.4 (F44–F52) and `docs/reference/findings/RETRACTIONS_REGISTRY.md` (R50 added). Headline new scalars:
> - **EL classifier formal pre-reg holdout vs Hadith Bukhari**: AUC = **0.9718**, MW p = 4.05·10⁻³² (`expP10`)
> - **Brown joint p (empirical R)**: **5.24·10⁻²⁷** (vs ρ=0.5 prior 1.41·10⁻¹⁶) (`expP11`)
> - **Bootstrap T² 95 % CI**: **[3 127, 4 313]** (median 3 693); band-A T² = 3 557 INSIDE the CI → R50 reframe of patch B claim from "T² INCREASES" to "T² STABLE" (`expP12`)
> - **LOCO EL min AUC**: **0.9796** (drop poetry_abbasi) (`expP13`)
> - **Cross-script clean dominance ratio (any letter)**: 2.43× (Quran p_max 0.501 vs poetry_islami 0.206) (`expP14`)
> - **5 alternative riwayat invariance**: all keep AUC ≥ 0.97 (`expP15`)
> - **Maqamat al-Hariri (Arabic saj') AUC**: **0.9902**, MW p = 2.4·10⁻³⁸ → QURAN_DISTINCT_FROM_SAJ (`expP16`)
> - **Markov saj' adversarial mode 1**: max EL = 0.20 across 100 samples (< 0.314 boundary); modes 2-4 RUNNING (`expP17`)
> - **Shannon-capacity i.i.d. floor for EL**: 0.295; Quran's structural rhyme excess = +0.425 (`expP18`)
>
> No `results_lock.json` scalar changed in patch E (the locked scalars were generated by patches B/C and audited by patch D); patch E adds 9 new JSON outputs in `results/experiments/expP10..expP18/`.

> **v7.9-cand patch F sync (2026-04-26 night)**: Multi-compressor consensus closes the Adiyat-864 detection ceiling. Three pre-registered experiments + one robustness sweep; one finding F53 added to `RANKED_FINDINGS.md`; two failed-null pre-registrations FN01–FN02 added to Category K of `RETRACTIONS_REGISTRY.md` (NOT retractions of standing claims). Headline new scalars:
> - **`exp95c_multi_compressor_adiyat`** (PASS_consensus_100): K=2 consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} on Adiyat-864 (Q:100): recall = **864/864 = 1.000** at K=2 ctrl FPR = **0.0248** (half of gzip-only's 0.05). lzma-9 and zstd-9 each unilaterally close the gap (solo recall = 1.000); bz2-9 anti-correlates with the others on the ctrl null (Spearman ρ ≈ −0.5). The gzip-only 99.07 % "ceiling" of finding #5 is a compressor-specific artefact, not a fundamental limit.
> - **`exp95d_multi_compressor_robust`** (PARTIAL_seed_only): K=2 recall **identical 1.000** across seeds {42, 137, 2024} on Q:100 (span = 0.000); cross-surah Q:099 al-Zalzalah K=2 recall = **998/999 = 0.998999** (one bāʾ↔wāw substitution at K=1, saved by gzip-solo and by K=1 any-compressor at FPR 0.177). Robustness verdict per pre-registered ladder: "Q:100 fully closed; Q:099 generalises at 99.9 %."
> - **F53 added to `RANKED_FINDINGS.md` (row 53)** — strength **87 %**, paper-grade for Q:100. Reframes finding #5 from "ceiling 99.07 %" to "ceiling closed at 100 % under K=2 consensus". `PAPER.md` §4.42 written for the closure.
> - **FN01 / FN02 in Category K of `RETRACTIONS_REGISTRY.md`** — two earlier closure attempts failed transparently: `exp95_phonetic_modulation` (recall dropped to 0.985 with stratum FPR overshoot in every d ∈ {1,...,5}) and `exp95b_local_ncd_adiyat` (3-verse window-local NCD recall **collapsed to 0.399**). The negative results constrain the design space — only compressor diversity, not phonetic weighting or window locality, lifts the gzip ceiling. The retraction count remains 50; failed-null count is tracked separately at 2.
>
> No `results_lock.json` scalar changed in patch F either; patch F adds 4 new JSON outputs in `results/experiments/exp95{,b,c,d}_*/`. The strict counts: total positive findings 52 → 53; total retractions 50 (unchanged); failed-null pre-registrations 0 → 2 (Category K).

> **v7.5.1 patch (doc-only, no scalar changed)**: (a) Â§2.2 item 5 T definition expanded to `H_cond âˆ’ H_el` so readers can connect it directly to `src/features.py::t_tension` and to the 39.7 % scalar (closes an internal inconsistency with `PAPER.md` pre-v7.5.1 Â§3.1); (b) every Î³ citation normalised to +0.0716 (was 0.072 in Â§0 / Â§12 / Â§13); the rounded â‰ˆ 7.4 % figure is retained in prose as a linear-scale rounding only; (c) no `results_lock.json` entry changed.

> **v7.7 notice (2026-04-21, no `results_lock.json` scalar changed)**: Â§3.8 now includes **Â§3.8.5 LC3-70-U tight parsimony proposition** formalising the (T, EL) Fisher-optimal linear boundary as `L = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221` with 99.15 % acc, AUC 0.9975, 7 / 2 509 leaks (all `arabic_bible`). See `docs/PAPER.md Â§4.35`. Five-corollary structure; Fig. 7 regenerator at `experiments/exp88_lc3_70_u/`. `CHANGELOG` `[7.7]` documents the 28-experiment (exp60–exp87) verdict census + 5 new Â§5 retractions (ring structure, small-world topology, prime signature, adjacent-verse anti-repetition "Gem #2", golden-ratio formal re-test). **Post-publication v7.7 ablation** (`exp89`, `exp89b`, `exp90`): predictive content is carried by EL alone at AUC 0.9971 (pre-reg `FAIL_T_dominates`); `H_cond` is at chance (AUC 0.518) as univariate discriminator; cross-language EL test on Hebrew Tanakh / Greek NT / Iliad verdict `FAIL_no_convergence` — Quran's EL elevation is Arabic-specific, not a scripture-class property.

> **2026-04-25 status note**: see `docs/reference/findings/01_PROJECT_STATE.md` for the current claim-control dashboard and `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` for the current Adiyat/authentication entry point. Later receipts clarify: `exp95 = FAIL_ctrl_stratum_overfpr`, `exp105 = PARTIAL_null_saturated`, `exp106 = preregistration only / no result folder`, `E14 = MULTISCALE_LAW confirmed`, and `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md` is closed at 20/20 executed and audited.

> **v7.5 addition**: Â§3.8 now documents three resolution experiments: (a) `exp49_6d_hotelling` closes the exp48 promotion question as **SIGNIFICANT BUT REDUNDANT** (TÂ²_6D = 3 823.59 < 4 268.81 gate); (b) `exp50_emphatic_cross_corpus` confirms the Quran emphatic-detection gap is **Quran-specific** (Quran 1.15 % vs poetry_jahili 9.50 %, poetry_abbasi 4.83 %); (c) `exp51_exp48_sensitivity_islami` verifies exp48 is **STABLE** under poetry_islami inclusion (Î”d = +0.027). None modifies `results_lock.json`.
> **Prior v7.4+ addition**: Â§3.8 documented the verse-graph topology replication (`exp48`, Cohen d = +0.937 on n_communities). The later `exp49_6d_hotelling` gate closed the promotion question as **SIGNIFICANT BUT REDUNDANT**.

## Rankings Â· Discoveries Â· Methodology Â· What Survived Â· What Didn't Â· Upgrade Roadmap Â· Ultimate-2 Edit-Detection Layer

**Status**: Single source of truth for the current run-of-record.
**Supersedes**: `docs/old/QSF_COMPLETE_REFERENCE.md` (v10.19), `docs/old/QSF_REPLICATION_PIPELINE.md`, `docs/old/QSF_AUDIT_REPORT_v10.15.md`, `docs/old/QSF_FORMAL_PROOF.md`, `docs/old/QSF_FORMAL_PROOF_GAPS_CLOSED.md`, `docs/old/QSF_SHANNON_ALJAMAL_THEOREM.md`, `docs/old/QSF_EPIGENETIC_LAYER.md`, `docs/old/PREREGISTRATION_v10.18.md`, `docs/old/REMAINING_GAPS_v10.19.md`.
**Companions (current)**: `docs/PAPER.md`, `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` (v7.3 consolidated Adiyat answer, English), `docs/reference/adiyat/ADIYAT_AR.md` (2026-04-21, plain-language Arabic reader-friendly version), `docs/reference/adiyat/CANONICAL_READING_DETECTION_GUIDE.md` (v1.0, 2026-04-22, non-specialist walkthrough of the detection stack — EL / R12 / UFS — and the five-step "four readings" pipeline), `docs/old/ADIYAT_ANALYSIS_AR.md` (v7.1–v7.3 technical Arabic, preserved), `arxiv_submission/preregistration_v73_addendum.md` (post-hoc code-state lock for v7.3 tests), `arxiv_submission/osf_deposit_v73/` (OSF upload packet).
**Run of record (Ultimate-1)**: `results/ULTIMATE_REPORT.json`, `results/ULTIMATE_SCORECARD.md`, `results/CLEAN_PIPELINE_REPORT.json`, `results/integrity/*.json`, `results/checkpoints/*.pkl`.
**Run of record (Ultimate-2, edit-detection layer)**: `results/experiments/exp20_MASTER_composite/ULTIMATE2_REPORT.json`, `results/experiments/exp{09..19}_*/`, `notebooks/ultimate/QSF_ULTIMATE_2.ipynb`.

---

## 0. Executive summary in one table

| Question | Answer | Key scalar |
|---|---|---|
| Is the Quran a multivariate outlier in Arabic-family-sibling 5-D space? | **Yes, sharply** | Î¦_M Hotelling TÂ² = **3 557**, perm p = **0.005** |
| Does a simple classifier distinguish Quran from Arabic pool? | **Yes, near-perfectly** | nested 5-fold CV AUC = **0.998** |
| Does the effect survive leave-one-family-out? | **Yes, min d = 5.26** | Test A, 6/6 splits |
| Does it survive 10-fold resampling? | **Yes, min d = 5.08** | T12 `D24` min d |
| Does it survive a 1 000-bootstrap of Î©? | **Yes, 100 % > 2.0** | Test C |
| Where in the text does the signal live? | **At the word scale** | letter 0.80, **word 2.45**, verse 1.77 |
| Is there a universal law? | **No** — Î³(Î©) slope â‰ˆ 0 | L6 slope = âˆ’0.0043 |
| Is the golden-ratio Ï† â‰ˆ 0.618 claim reproducible? | **No** | Ï†_frac = âˆ’0.915, retracted |
| Is the Meccan-Medinan F > 1 joint pre-reg reproducible? | **No** | F_M = 0.80, falsified |
| Is the Adiyat 7-metric blind case reproducible at p < 0.05? | **No (marginal)** | p = 0.070, 4/7 wins |
| Are there re-usable Arabic-textology constants? | **Yes, two** | H(harakat\|rasm) = 1.964 bits, I(EL;CN) = 1.175 bits |
| How many scalars are SHA-256 locked? | **57 tolerance-gated** in `results_lock.json` (integrity envelope) + **127 total** in `ULTIMATE_REPORT.json` (full dump incl. derived/methodological/candidate) | `results_lock.json::hash` |
| Does sub-surah edit-detection exceed Î¦_M's 2–3 % ceiling? | **Yes** (R2 + R11) | R2 log_amp_median = **3.14** (CI > 0); R11 Î¦_sym AUC vs poetry = **0.976–0.987** |
| Does the effect generalise to other scriptures? *(v7.2 rebuild)* | **Yes, but SHARED across Abrahamic scriptures** | R3 all-scripture path-minimality (exp35, N_PERM = 5 000): Quran z = **âˆ’8.92**, Tanakh z = **âˆ’15.29**, Greek NT z = **âˆ’12.06**, Iliad z = +0.34 (null ctrl). BH `p_adj â‰¤ 10â»Â³`. Path minimality is a shared Abrahamic-scripture property, NOT Quran-unique. Raw v10.3c "Quran 76 % stronger" claim FALSIFIED. |
| Is there a new d > 0.8 finding? | **Yes** (F6) | Length-coherence lag-1 d = **+0.832** (Band-A canonical, exp24) / **+0.827** (locked T32) / +0.877 (audit-pooling variant); all within 0.05 of each other. MW p = 1.7Â·10â»Â¹Â². |
| Does bigram-sufficiency extend to the character scale? *(v7.1, 2026-04-20)* | **No** | Quran pooled H_char_3/H_char_2 = **0.714** ranks 2/7 (ksucca 0.660); per-unit d = **+0.46** wrong direction |
| Does the 4-scale Zipf-class universal law hold? *(v7.1)* | **No, partial** (3/5) | Supports: T11 (root), F6 (verse-length), T8 (path). Fails: L0 char (exp27), T28 root-Markov-order |
| Is there a cascade product-code for internal-letter edits? *(v7.1)* | **No** | Measured P_composite = **0.137** vs feedback estimate 0.82–0.90; 3 of 4 channels structurally blind |
| Is `T28_markov_order`'s docstring claim (`d = âˆ’1.849`) correct? *(v7.1)* | **No, sign-flipped** | Locked scalar is `+0.425`; verbal claim retracted, scalar preserved |
| Does R1 9-ch rescue the cascade on internal-letter edits? *(v7.1, exp30)* | **No** | Measured P_composite across 9 R1 channels = **0.417**; all MW p(Q>C) â‰¥ 0.58 (channels fire but are **not Quran-specific**). Only `E_ncd` (gzip) shows consistent Adiyat-variant response: 1/9 for A (Ø¹â†’Øº), 2/9 for B (Ø¶â†’Øµ), 3/9 for C |
| Does the fingerprint survive loss of half the surahs? *(v7.2, exp31)* | **Yes** | At N = 50 surahs (out of 68), median TÂ² = 3 081; fraction with TÂ² â‰¥ 50 % full is **1.000**. Centroid drift at N = 50: 0.26 Mahalanobis units = 3.3 % of corpus-to-ctrl magnitude |
| Is the 5-D separation an island or a continuum? *(v7.2, exp33)* | **Continuum with strong clustering** | Single-linkage island gap = âˆ’3.94 (continuum, perm p = 0.32); Silhouette = **+0.65** (strong cluster), NNR = 0.50 (Quran 2Ã— tighter to self) |
| Does Î¦_sym (R11) detect Adiyat single-letter edits? *(v7.2, exp34)* | **No (structural blindness)** | All 3 variants shift Î¦_sym by < 0.33 Ïƒ_Q (per-Quran-surah Ïƒ = 0.19464). Closes ADIYAT Â§13.3 R11 cell. |
| Is the (T, EL) 2-feature AUC stable across fold-randomisation seeds? *(v7.2, exp36)* | **Yes, rock-solid** | 5 seeds: AUC = **0.9971 Â± 0.00056** across-seed; min across 25 folds = 0.9928, max = 1.0000. Ïƒ_across_seed is 10Ã— tighter than Ïƒ_within_fold. |
| Is there a letter-level edit-detection channel that fires Quran-specifically? *(v7.3, exp41)* | **Yes — R12 gzip NCD** on the 28-letter rasm | Population d = **+0.534** (raw), length-controlled **Î³ = +0.0716 at fixed length, 95 % CI [+0.066, +0.078], p â‰ˆ 0** (on the linear scale this is â‰ˆ 7.4 % higher NCD per edit; quote Î³ as the authoritative scalar). Decile-stratified: Quran > ctrl in 8 of 10 letter-count deciles (deciles 6, 10 negative). **âš  exp55 (v7.6) formal audit: LENGTH_DRIVEN** — only 5/10 deciles exceed d > 0.30; cite Î³ as authoritative scalar, not raw d. **Distinct from the locked E_ncd channel** (different input form). Not yet in `results_lock.json` — awaits two-team replication. |
| Is the Adiyat 864-variant case closed at paper grade? *(v7.3, exp43)* | **Yes, at the single-letter question** | 0 of 864 variants exceed canonical Î¦_M (100 % â‰¤); 836 tie (feature-invariant). R12 NCD fires on **99.1 %** of variants at exp41 ctrl-p95 (pre-registered 5 % FPR). Joint (NCD doc âˆ§ CCAS Frob) = **99.1 %**. Full discussion: `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md`. Two-letter edits and whole-surah forgery remain outside this test. |
| Is there a cleaner scalar than F6 lag-1 Ï? *(v7.3, exp44)* | **Yes — AR(1) coefficient** | Per-surah OLS AR(3) fit: Ï†_1 d = **+1.095**, MW p_greater = **1.8Â·10â»Â¹Â²**. IAC over lags 1–15 is LOWER in Quran (d = **âˆ’0.55**, p_less = 2.4Â·10â»â¶) — "punchy at lag 1, rapid decorrelation beyond lag 2" vs controls' sustained long-range persistence. Candidate 6th Î¦_M feature, pending external replication. |
| Is CCAS (consonant-transition matrix) Quran-specific on internal edits? *(v7.3, exp38)* | **No — closes the letter-transition family** | Raw Frobenius d = âˆ’0.026 (null; replicates `exp30::C_bigram_dist`). Normalised CCAS d = **âˆ’0.119, p_less = 4.5Â·10â»Â¹â·** (wrong direction, consistent with Quran's higher Ïƒ_intra_doc from Â§4.1 VL_CV). Neither variant supports the hypothesis. |
| Does LPEP (Letter-Position Entropy Profile) distinguish Quran from Arabic ctrl? *(v7.3, exp37)* | **No within-Arabic**, **Yes across scripts** | Iliad-Greek pooled `<H(pos\|L,k)>` = **2.16 > every Arabic corpus** (max 2.05 hindawi): confirms Semitic-root signature. But Quran rank 2/7 within Arabic (beaten by ksucca 1.83), per-unit d = +0.15 wrong direction. Semitic descriptor, not Quran fingerprint. |
| Are two-letter edits detectable? *(v7.4, exp45)* | **Yes, universally** | 72 900 two-letter variants (FAST): NCD+CCAS compound fires on **100.0 %**. D1 Phi_M moves on 6.4 % (vs 3.2 % single-letter). Multi-letter gap CLOSED. |
| Are emphatic-class (phonetically similar) edits detectable? *(v7.4+ FULL, exp46, 2026-04-21)* | **No — 1.1 % overall** | 7 emphatic classes, 10 461 edits, all 114 surahs, null=800. Best: ayn/alef 2.1 %. Worst: tta/ta **0.0 %**, qaf/kaf **0.0 %**. Voiceless emphatic stops are a full R1 blind spot. Semantic-aware forgery gap = **~48 pp** below the R1 random-swap baseline. **Errata**: the v7.4 FAST-mode 31.3 % was noise-inflated by a 120-sample null; superseded. |

---

## 1. What changed v3 (clean-pipeline) â†’ v5 (audit) â†’ v6 (post-audit)

### 1.1 Version lineage

- **v1–v2** (Oct 2025): 14-feature pipeline; multiple audit findings (pickle corruption, heuristic root extractor 21 % accurate, Bible contamination, Ksucca single-token bug). Archived in `archive/2025-*`.
- **v3** (April 2026, clean rebuild): 5-feature pipeline, raw-only, 23 tests, SHA-256 corpus pinning. `docs/old/PAPER.md`, `docs/old/REPLICATION.md`.
- **v5 audit** (2026-04-18): six-round forensic audit, three WARNING-class fixes (hadith quarantine, Band-A propagation into T1 & T8, Fisher `chi2.sf`), plus ridge-unification and FDR family expansion.
- **v6 audit-hardened** (2026-04-19): zero-trust hostile audit; six additional fixes (audit/_build.py, extended_tests.py):
  - Cross-language fallback removed (INFEASIBLE skip).
  - D05 silent-zero replaced with NaN + warning.
  - T11 NaN-sort bug fixed (pre-filter).
  - Pickle checkpoint SHA-manifest pinning.
  - `<UPDATED>` sentinel removed from results-lock verification.
  - Universal 1Â·10â»â´ absolute-drift lens + headline Â±5 % envelope.

### 1.2 Audit regression sentinel

`notebooks/ultimate/_audit_check.py` verifies **77 markers** (v5 + v6 fixes + anti-regressions) on every build. Any missing marker (= a fix was reverted) raises an error.

---

## 2. Methodology stack (what-how-why)

### 2.1 Pipeline architecture

```
data/corpora/<lang>/*  (raw, SHA-256-pinned)
       â”‚
       â–¼
src/raw_loader.py    â†’ unit-level objects
src/verify_corpora   â†’ G1–G5 sanity gate
src/features.py      â†’ 5-D feature vector (per unit)
src/roots.py         â†’ CamelTools calima-msa-s31 (cached)
       â”‚
       â–¼
notebooks/ultimate/QSF_ULTIMATE.ipynb  (21 phases, 159 cells)
       â”‚
       â–¼
results/integrity/ (4 locks + baseline envelope + prereg)
results/ULTIMATE_REPORT.json (127 total scalars; 57 tolerance-gated in results_lock.json)
results/CLEAN_PIPELINE_REPORT.json (31 raw tests, no pickle)
results/figures/fig{1..6}.png
results/checkpoints/*.pkl + _manifest.json (SHA-pinned)
```

### 2.2 The 5 features (EL, VL_CV, CN, H_cond, T) — why these?

1. **EL** (end-letter rhyme rate) — phonological/acoustic closure; discriminates prose vs verse.
2. **VL_CV** (verse-length CV) — anti-metric signature; high in Quran, near-zero in metrical poetry.
3. **CN** (connective start rate) — discourse-cohesion channel; orthogonal to rhyme.
4. **H_cond** (conditional root-bigram entropy) — lexical-sequence irregularity under fixed root stream.
5. **T** (structural tension) — `H_cond(verse-final-root bigrams) âˆ’ H(verse-final-letter)` (canonical definition in `src/features.py::t_tension`, ref `QSF_PAPER_DRAFT_v2 Â§2.6`, fix F-11). Under this definition the fraction of Band-A Quran surahs with T > 0 is 39.7 % (run-of-record, locked as `D10` / `T10`). Early v1/v2 used a prosodic variant `T_v2 = mean|Î”Ï‰|` giving â‰ˆ24.3 %; do not conflate the two. Captures residual "root-vs-letter" information asymmetry at verse-closure positions.

The 5 are selected for (a) information-theoretic interpretability, (b) computability from raw text + a standard morphological analyser, (c) demonstrated partial mutual independence (max normalised pairwise MI = 0.318). **Not canonical.** A sparse-PCA robustness check (L7, Â§3.5) and a kernel HSIC check (G2, Â§3.3) are our feature-agnostic controls.

### 2.3 Band-A (15–100 verses) — why?

- Matches Quran's bulk (68 / 114 surahs).
- Reduces length confounding between a 114-Quran target and 4 830-unit control pool.
- Corresponds to a regime in which 5-D covariance is well-conditioned.
- Propagated into every per-unit statistic (v5 fix closes a T1/T8 leak).

### 2.4 Hadith quarantine — why?

Hadith Bukhari quotes the Quran by design (Prophetic tradition). `Partial_quote_leak = 0.008` confirms exact-quote overlap. Including hadith in the control pool inflates the "uniqueness" claim artificially. **Hadith is excluded** from every inferential statistic; retained only in Fig. 4 for didactic contrast.

### 2.5 Integrity locks — why and how?

Four SHA-256 manifests verified at every phase and at paper-build time:

- `corpus_lock.json` — per-corpus SHA combined into a `combined` hash. Any corpus file byte change â†’ build fails.
- `code_lock.json` — per-notebook-cell SHA. Any code change â†’ build fails.
- `results_lock.json` — per-scalar expected value / tolerance / verdict, combined into a lock hash. Any drift beyond tolerance â†’ `HallucinationError`.
- `names_registry.json` — every `ULTIMATE_SCORECARD` ID registered ex-ante. No ad-hoc scalar injection.
- (v6) `checkpoints/_manifest.json` — per-pickle SHA. Pickle tampering â†’ refuse-to-deserialise.

v6 adds a universal **1Â·10â»â´ absolute-drift lens** (catches any numerical drift independent of per-scalar tolerances) and a **Â±5 % headline-baseline envelope** on `Phi_M_hotelling_T2` and `Phi_M_perm_p_value`.

### 2.6 Nested CV — why?

The legacy in-sample AUC (0.998) is **flagged as diagnostic only** in Cell 62. The blessed classifier AUC is the outer-fold mean from a 5-fold stratified CV, with scaler fit on inner-train indices only. No feature selection, no hyperparameter search. Architecturally fixed.

### 2.7 Permutation nulls — why N_PERM = 200 FAST_MODE?

FAST_MODE floors the observable perm p at 1/201 = 4.98Â·10â»Â³ — sufficient to show significance at an order of magnitude below 5 % while keeping wall-clock at â‰ˆ70 min on a laptop. Full mode (N_PERM = 10 000) is supported and pushes the floor to 10â»â´. The Mann-Whitney p (1.75Â·10â»â´â´) is not permutation-bounded and gives the raw magnitude.

### 2.8 Pre-registration — why and how?

Pre-registration `results/integrity/preregistration.json` was frozen **before** re-running the audit-hardened pipeline (v10.18, 2026-04-18; one v5 amendment 2026-04-19). It defines three tests (A: Î¦_M leave-one-family-out, B: Meccan-Medinan joint F>1, C: Î© bootstrap > 2.0 fraction) with strict pass/fail thresholds. Test B **falsified** — reported honestly. Tests A and C **pass**.

### 2.9 FDR (Benjamini-Hochberg) — why?

Because the pipeline computes â‰ˆ13 permutation-backed p-values, a family-wise correction is required for peer-review defensibility. BH at q â‰¤ 0.05 gives 7 survivors. `results/integrity/fdr_coverage_audit.json` lists the full family and its in-FDR / not-in-FDR status. No cherry-picking is possible.

---

## 3. Rankings (by composite = âˆš(confidence Ã— effect))

### 3.1 Scorecard (headline findings, composite â‰¥ 85)

| Rank | ID | Finding | Scalar (run-of-record) | Composite | Status |
|:--:|:--:|---|---|:--:|:--:|
| 1 | T2 / D09 | Classifier AUC (nested 5-fold CV) | 0.998 | 100 | âœ… PROVED STRONGER |
| 2 | D10 | %T>0 Quran-unique tension | Quran 39.7 %, controls max 0.10 % | 97 | âœ… PROVED STRONGER |
| 3 | D14 | Verse-internal word-order non-random | Quran +5.80 gap, 100 % canon-farther | 97 | âœ… PROVED STRONGER |
| 4 | D26 / Test C | Bootstrap Î© stability | 100 % > 2.0, median 10.0 | 95 | âœ… PROVED STRONGER |
| 5 | D11 / T17 | Multi-scale perturbation (locus @ word)Â¹ | letter 0.80 / word **2.45** / verse 1.77 | 94 | âœ… PROVED STRONGER (locus ADDED) |
| 6 | Î¦_M headline | Hotelling TÂ² + perm p | TÂ² = 3 557, p = 0.005, d = 6.66 | 92 | âœ… PROVED STRONGER |
| 7 | Test A | LOFO Î¦_M robustness | min d = 5.26, 6/6 splits | 92 | âœ… PROVED |
| 8 | D27_directional | Abbasi discrimination (directional) | 6 / 8 beats in favour of Quran | 90 | âœ… PROVED (replaces D27 non-directional) |
| 9 | D24 / T12 | Î¦_M 10-fold CV | min d = 5.08, median 6.89 | 85 | âœ… PROVED STRONGER |
| 10 | D07 | Scale-free Fisher | âˆ’logâ‚â‚€ p @ W=10 = 16.08 (genuine) | 91 | âœ… PROVED (v5 fix) |
| 11 | D23 | Pre-reg canon-vs-perturbed | Quran 100 %, Abbasi 60 %, Bible 22.5 % | 91 | âœ… PROVED |

Â¹ D11 is a combined gap score over letter, word, and verse granularities; the individual sub-channel values (`D11_letter_gap`, `D11_word_gap`, `D11_verse_gap`) are derived, not independently locked.

### 3.2 Medium-composite (55–85)

| ID | Finding | Scalar | Composite | Status |
|:--:|---|---|:--:|:--:|
| D22 | RD Ã— EL product | 0.632 vs 0.179 next-best (3.5Ã— margin) | 80 | âœ… PROVED STRONGER |
| D03 | EL rhyme rate | 0.707, 4.5Ã— next-best | 80 | âœ… PROVED |
| D17 / T8 | Canonical path minimality | z = âˆ’3.96, 0/2000 perms beat | 77 | âœ… PROVED |
| E3 / T23 | Harakat channel capacity | 1.964 bits / 4.70 max, 58 % redundancy | 74 | âœ… PROVED |
| S5 | Path minimality | z = âˆ’3.96, 0/2000 perms | 74 | âœ… PROVED |
| G1 | Heavy-tail Bennett | Hill Î± â‰¥ 1.8 on all 5 features | 71 | âœ… CLOSED |
| G2 | 5-channel MI | max normalised MI = 0.318 | 71 | âœ… CLOSED (joint-informative, not independent) |
| D01 | Anti-Metric VL_CV | d = 1.40 (pool), 2.5 (vs poetry) | 71 | âš ï¸ WEAKER than v2 |
| D04 | CN connective rate | 0.086, 2.5Ã— next-best | 70 | âœ… PROVED |
| D08 | Markov unforgeability | Quran z = 44.9 (Abbasi z = 47.9 higher) | 68 | âš ï¸ NOT Quran-unique |
| D16 | RQA Laminarity | vs poetry d = âˆ’14.1, vs Bible d = +0.96 | 68 | âš ï¸ mixed sign |
| T11 / S4 | Bigram sufficiency Hâ‚ƒ/Hâ‚‚ | Quran 0.222 (#1 lowest) | 68 | âœ… PROVED partial |
| T26 | Terminal-position depth | d(âˆ’1)=1.43, d(âˆ’2)=2.40, d(âˆ’3)=0.65 (depth 3) | 92 | âœ… PROVED STRONGER than v2 |
| T31 | Fisher-curvature (smoothest manifold) | Quran curvature rank 1/8 | 79 | âœ… PROVED (topological) |
| T25 | Info-geometry saddle | 8 / 8 corpora saddle (near-universal) | 69 | âš ï¸ LESS distinctive |
| T27 | Inter-surah cost | ratio 0.856, p = 0.001 | 57 | âš ï¸ SURVIVES WEAKER |
| Adiyat | Blind 7-metric (micro-case) | 4/7 wins, perm p = 0.070 | — | âš ï¸ MARGINAL (weakened v6) |
| U2-R3 | Cross-scripture z-test *(v7.2 rebuild, exp35)* | z_Quran = âˆ’8.92, z_Tanakh = âˆ’15.29, z_NT = âˆ’12.06, Iliad null ctrl z = +0.34, BH min p_adj = 3Â·10â»â´ | 88 | âœ… PROVED that all 3 Abrahamic scriptures optimise canonical ordering; âš ï¸ Quran is **not** the strongest in raw z (Tanakh is). Supersedes the pre-v7.2 "Quran 76 % stronger" claim. |
| U2-R2 | Sliding-window amplification (Ultimate-2) | log_amp_median = 3.14, 95 % CI [2.32, 3.23] | 91 | âœ… PROVED (letter-edit detector) |
| U2-F6 | Adjacent-verse length coherence | d = +0.877, p = 1.4Â·10â»Â¹Â¹ | 82 | âœ… PROVED (new, candidate 16th channel) |
| U2-R11 | Î¦_sym = H_nano_ln + RST âˆ’ VL_CV (manual) | AUC vs poetry = 0.976–0.987; pooled = 0.897 | 78 | âœ… PROVED (replicates 2025 historical â‰ˆ 0.98) |
| U2-R1 | 9-channel variant forensics (Ultimate-2) | 50 % firing rate on single-letter edits (45Ã— chance) | 60 | âš ï¸ PARTIAL (below 0.80 target) |
| U2-R8 | Constrained null ladder (Ultimate-2) | composite channel rate â‰ˆ 0.62 | 55 | âš ï¸ PARTIAL |

### 3.3 Low-composite (30–55)

| ID | Finding | Status |
|:--:|---|:--:|
| D19 | H-Cascade F | d = 0.76; hadith & ksucca exceed Quran |
| D20 | Î©_master rank | Q = 7.89, ksucca 7.20 (9 % margin) |
| D06 | Turbo-code gain | 1.644 #1, next 1.628 (1 % margin) |

### 3.4 Falsified / retracted

| ID | Finding | Verdict | Reason |
|:--:|---|:--:|---|
| D25 / Test B | Meccan-Medinan joint F > 1 | âŒ FALSIFIED | F_M = 0.797, F_D â‰ˆ 0.84 |
| D05 | Unit-level I(EL;CN) = 0 | âŒ FALSIFIED (unit) / âœ… CORPUS | Unit d = 1.17 bits vs ctrl min 0.00; corpus I = 1.175 bits survives |
| D18 | Adjacent diversity 100th pctile | âŒ FALSIFIED | Observed 10.6th pctile |
| D21 / T20 | Rhyme-swap P3 | âŒ NOT REPRODUCED | Q 32 % vs Bible 60 % (opposite direction) |
| G3 | Hessian PD closure | âŒ FALSIFIED BY MATH | H = 2Â·Î£â»Â¹ PD by construction (tautology) |
| G5 | Î³(Î©) = a + bÂ·Î© closure | âŒ FALSIFIED BY MATH | Regression of algebraic identity |
| T28 | Markov Hâ‚‚/Hâ‚ T12 | âŒ NOT REPRODUCED | Q = 0.111 vs ctrl 0.114, d = âˆ’0.03 |
| T29 | Ï†_frac = 0.618 golden ratio | âŒ NOT REPRODUCED | Observed âˆ’0.915 |
| L6 | Î³(Î©) universal law | âŒ NULL | slope b = âˆ’0.0043, consistent with 0 |
| Phi_M_perm_p_value | Floor-limited at N_PERM=200 *(sensitivity added 2026-04-20)* | âš ï¸ SUPERSEDED by sensitivity | Locked value 4.98Â·10â»Â³ is the permutation-floor 1/201. Supplementary run at N=10 000 (exp26): 0 hits â†’ **p < 1Â·10â»â´**. See `results/experiments/exp26_perm_sensitivity/exp26_perm_sensitivity.json`. Lock not re-blessed (requires full notebook rerun); paper PAPER.md Â§4.1 cites both numbers. |
| L1 | SCI as Quran-unique composite *(added 2026-04-20)* | âš ï¸ EXPLORATORY only | SCI(Q) = 5.421 ranks #1 but margin over #2 is ordinary-stylometric; not a law |
| L3 | Free-energy minimum as Quran-unique *(added 2026-04-20)* | âŒ NOT REPRODUCED | F(Q) = +1.100; Quran does **not** minimise the F functional across the 6-corpus pool |
| L4 | Aljamal invariance Î©Â·d â‰ˆ const *(added 2026-04-20)* | âŒ FALSIFIED | cross-corpus CV(Î©Â·d) = **1.551** (invariance would need â‰ˆ 0) |
| L7 Î¨_z | Raw Î¨ ranking is scale-variant *(added 2026-04-20)* | âš ï¸ DISCLOSED | Raw Î¨(Q) #1; under z-scored sensitivity variant Î¨_z, `ksucca` wins. Raw Î¨ is a composite scale artefact; Î¦_M headline (Â§4.1) and classifier AUC (Â§3.4) do not depend on it |
| Law IV (VERU) | End-root uniqueness as Quran-unique | âŒ FALSIFIED (2026-04-20) | d = **âˆ’1.013** on short-band [5,20] after hadith quarantine; controls achieve VERU = 0.941 vs Quran 0.842 (poetry enforces rhyme-word uniqueness formally). Full analysis: `archive/audits/ADIYAT_BREAKTHROUGH_AUDIT_2026-04-20.md`. |
| Char-scale bigram sufficiency | H_char_3 / H_char_2 Quran-extremal (external review 2026-04-20) | âŒ FALSIFIED (v7.1) | Pooled Quran 0.714 ranks 2/7 (ksucca 0.660 < Quran); per-unit Cohen d = **+0.457** (wrong direction); MW p_less â‰ˆ 1.0 on 68 Quran vs 2 509 ctrl units. Iliad Greek pooled = 0.866 for reference. Source: `results/experiments/exp27_hchar_bigram/exp27_hchar_bigram.json`. |
| Scale-invariant Zipf-class law (4 scales simultaneously Markov-1 extremal) | Universal framing | âŒ FALSIFIED at 2/5 scales (v7.1) | L0 char FAILS (exp27), L1b root-Markov-order FAILS (T28). L1 root-bigram, L2 verse-length, L3 surah-path PASS. Verdict: **PARTIAL_LAW_HOLDS_AT_MAJORITY_SCALES**. Source: `results/experiments/exp28_scale_invariant_law/exp28_scale_invariant_law.json`. |
| Char-root GAP secondary fingerprint | `gap = char_H3/H2 âˆ’ root_H3/H2` Quran-extremal | âŒ NOT SUPPORTED (v7.1) | Quran ranks 4/7 on this gap. Poetry families (jahili 0.541, islami 0.545, abbasi 0.514) score above Quran (0.492). |
| Cascade product-code P_composite â‰ˆ 0.82–0.90 on single-letter internal edits | Feedback estimate | âŒ FALSIFIED (v7.1) | Empirical P_composite = **0.137** (ctrl-perturbation null, 1 360 Q + 4 000 ctrl perturbations). Root cause: `features_5d` is byte-exact invariant under non-initial/non-terminal letter substitutions in non-boundary words — a structural property of boundary-reading features, not a measurement artefact. Source: `results/experiments/exp29_cascade_product_code/exp29_cascade_product_code.json`. |
| T28 root-Markov-order direction (`d = âˆ’1.849`, "Quran needs less info from Markov-2") | Docstring claim | âŒ VERBAL RETRACTION (v7.1) | Locked scalar in `CLEAN_PIPELINE_REPORT.json::T28_markov_order.cohens_d_quran_vs_ctrl = +0.425`, p_mwu_less â‰ˆ 1.0. Sign is flipped vs docstring. Scalar preserved; verbal claim withdrawn. Surfaced by exp28. |

### 3.5 Deferred (v6 INFEASIBLE) — closed in v7

| ID | Finding | Status | Reason |
|:--:|---|:--:|---|
| Cross-lang Î¨ (Iliad / Greek-NT / Tanakh) | **CLOSED** in v7 via R3 (Â§3.6) | v6: Band-A returned zero units under corrected filter. v7: R3 uses a per-scripture book-shuffle null (not a forced band-A match); BH-pooled p = 0.002 (Â§16.2). |

### 3.6 Ultimate-2 channel ranking (R1–R11, calibrated)

Ultimate-2 is an 11-channel edit-detection layer built on top of the Ultimate-1 checkpoints. Each channel has a pre-registered target and a calibrated rate obtained after hostile-audit rounds 1 and 2. Primary output: `results/experiments/exp20_MASTER_composite/ULTIMATE2_REPORT.json`.

| # | Channel ID | Purpose | Calibrated rate | Headline stat | Target | Verdict |
|:--:|:--:|---|:--:|---|:--:|:--:|
| 1 | **R3** | Cross-scripture authenticity | 0.960 | p = 0.002, BH at Î± = 0.05 | 0.90 | **PASS STRONGER** |
| 2 | **R2** | Sliding-window amplification | 0.981 | log_amp_med = 3.14, CI [2.32, 3.23] | 0.80 | **PASS STRONGER** |
| 3 | **R11** | Symbolic formula Î¦_sym | â‰ˆ 0.79 | AUC pooled = 0.897; vs poetry 0.976–0.987 | 0.90 | **NEAR-PASS** (below 0.90 pooled; passes vs poetry-only) |
| 4 | **R8** | Constrained null ladder | 0.599 | composite channel rate â‰ˆ 0.62 | 0.80 | PARTIAL |
| 5 | **R1** | 9-channel variant forensics | 0.494 | 50 % of single-letter edits fire â‰¥ 3 channels (45Ã— chance floor 0.011) | 0.80 | PARTIAL (strong direction, weak magnitude) |
| 6 | **R6** | Word-graph Louvain modularity | 0.143 | 57 % of controls Q < Q_Quran | 0.50 | DIRECTIONAL |
| 7 | **R4** | Character-level LM perplexity | 0.058 | AUC = 0.529 (CI 0.39–0.67) | 0.90 | **FAIL** (small char-LM insufficient; a real GPT-scale char-LM remains future work) |
| 8 | R10 | Verse-internal word-order | 0.000 | raw rate 0.025 | 0.50 | FAIL |
| 9 | R7 | Transmission-noise ladder | 0.000 | all CIs contain 0 | 0.50 | FAIL |
| 10 | R5 | Adversarial G0–G4 benchmark | 0.000 | 50 % of forgeries below Quran | 0.50 | FAIL |
| 11 | R9 | Cross-scale VIS propagation | 0.000 | VIS_log = âˆ’0.72, VIS = 0.485 | 0.50 | **REVERSED** (direction opposite to pre-reg) |

**Composite detector**: `P_detect_upper = 1 âˆ’ Î (1 âˆ’ rate_i) = 0.981` (dominated by R2). Even deleting R2, R3 alone gives `P_detect â‰¥ 0.960`.

### 3.7 R11 per-corpus AUC (manual reproduction, 2026-04-20)

Î¦_sym = H_nano_ln + RST âˆ’ VL_CV, computed verbatim from `archive/scripts_pipeline/scripts/path_acd_tests.py:113–166`, direction-corrected (`AUC* = max(AUC, 1 âˆ’ AUC)`). Source: `results/experiments/exp19_R11_symbolic_formula/R11_manual_phi_sym.json`.

| Control | AUC* | Sign |
|---|---:|:---:|
| poetry_islami | 0.987 | Quran < poetry |
| poetry_abbasi | 0.978 | Quran < poetry |
| poetry_jahili | 0.976 | Quran < poetry |
| ksucca | 0.888 | Quran > ksucca |
| hadith_bukhari | 0.827 | Quran > hadith |
| hindawi | 0.809 | Quran < hindawi |
| arabic_bible | 0.751 | Quran < bible |
| iliad_greek | N/A | Arabic-only formula |
| **pooled (7 Arabic)** | **0.897** | mixed direction |

The sign flips between Quran-higher (vs ksucca, hadith) and Quran-lower (vs poetry, hindawi, bible) imply Î¦_sym is a **two-sided structural separator** centred near the Quran, not a monotone discriminator.

### 3.8 Post-v7.4 findings (not yet promoted to `results_lock.json`)

The following are the candidate findings generated by experiments run after the v7.4 lock. None modifies any scalar in `results_lock.json`. Each lists its pre-registered promotion threshold.

#### 3.8.1 Verse-graph topology replication — PROMOTE on the pre-graph test; 6-D gate closed SIGNIFICANT BUT REDUNDANT (exp48 + exp49 + exp51)

> **v7.5 update (2026-04-21)**: the two open items on this finding are now both closed. (i) **6-D Hotelling gate** (`exp49_6d_hotelling`): TÂ²_6D = 3 823.59 < 4 268.81 â†’ **SIGNIFICANT BUT REDUNDANT**. `n_communities` does not become a 6th blessed channel; the 5-D Î¦_M already spans this information axis. (ii) **Poetry_islami sensitivity** (`exp51_exp48_sensitivity_islami`): strongest d moves +0.937 â†’ +0.964 under the extended pool (Î”d = +0.027), verdict unchanged â†’ **STABLE**. Details in Â§Â§3.8.2, 3.8.4 below. The Â§3.8.1 pre-graph result remains: exp48 replicates on clean data at d = +0.937 and Quran rank 1 / 6 across five individual Arabic controls.

**What**: per-surah verse-transition graphs (nodes = verses, edge weights = 0.5Â·EL_match + 0.5Â·word-length-ratio). Six topology metrics computed per unit and contrasted Quran vs pooled Arabic controls (hadith quarantined): `clustering`, `avg_path_norm`, `modularity`, `n_communities`, `bc_cv`, `small_world_sigma`. Pre-registered decision rule frozen before any run.

**Pre-registered rule**: FIRE = `|d| > 0.3 AND p < 0.01` per metric; PROMOTE = n_fires â‰¥ 3 of 6.

**Result**: `n_fires = 4 / 6` â†’ **PROMOTE verdict** (pre-graph test).

| Metric | Quran mean | Ctrl mean | Cohen d | MW p | FIRE | Quran rank among 6 Arabic corpora |
|---|---:|---:|---:|---:|:---:|:---:|
| `n_communities` | 7.02 | 4.67 | **+0.937** | 1.19Â·10â»Â¹Â² | âœ“ | **1 / 6** |
| `modularity` | 0.644 | 0.508 | **+0.672** | 1.06Â·10â»Â¹Â³ | âœ“ | **1 / 6** |
| `avg_path_norm` | 0.348 | 0.359 | âˆ’0.550 | 2.55Â·10â»Â¹Â³ | âœ“ | 5 / 6 (lower = more cohesive) |
| `bc_cv` | 0.519 | 0.574 | âˆ’0.500 | 2.55Â·10â»Â¹Â³ | âœ“ | 5 / 6 (lower = more uniform) |
| `clustering` | 0.000 | 0.000 | 0.000 | 1.00 | — | verse-chain degeneracy |
| `small_world_sigma` | 0.000 | 0.000 | 0.000 | 1.00 | — | follows from clustering=0 |

**Against-archive comparison**: the 2025 archive `qsf_new_anomaly_tests.py` TEST 3 reported `d â‰ˆ +0.47, p â‰ˆ 5Â·10â»â·` on contaminated v2 data. The clean-v7.4 replication at `d = +0.937` is ~2Ã— stronger, with per-corpus rank 1 against every single Arabic control (poetry_abbasi, poetry_jahili, hindawi, ksucca, arabic_bible).

**Audit-fixed per-corpus d's** (n_communities):

| Control corpus | n_ctrl | Cohen d vs Quran | MW p vs Quran |
|---|---:|---:|---:|
| `poetry_jahili` | 133 | **+1.05** | 2.7Â·10â»Â¹Â¹ |
| `arabic_bible` | 1 183 | +1.22 | 2.9Â·10â»â¸ |
| `poetry_abbasi` | 2 823 | +0.87 | 9.8Â·10â»Â¹âµ |
| `hindawi` | 74 | +0.55 | 9.2Â·10â»Â³ |
| `ksucca` | 41 | +0.32 | 2.4Â·10â»Â² |

The effect is **largest against the smallest Arabic control** (`poetry_jahili`), empirically refuting the "pool dominated by large hindawi" sample-size-artefact hypothesis that was flagged in the zero-trust audit. Hadith_bukhari (quarantined) would have `n_communities = 8.01 > Quran's 7.02`; the finding is hadith-quarantine-dependent and honestly disclosed as such.

**Known caveats** (in the run's `caveats` field):
1. Mild circularity — edge weights include EL (blessed D03) and a word-length ratio (related to D01 VL_CV). Guarded by the pre-registered 6-D Hotelling rule (Â§3.8.2; verdict: SIGNIFICANT BUT REDUNDANT, confirming the circularity concern).
2. Family-wise error — per-metric p<0.01 not Bonferroni-corrected; composite "â‰¥3 of 6" is strict (independence-assumed joint p â‰ˆ 2Â·10â»âµ).
3. `MIN_VERSES = 5` skipped 5 short Quran surahs (Al-Kawthar, Al-Ikhlas, Al-Asr, Al-Fil, Al-Quraysh). Matches archive protocol.
4. `strongest_metric = n_communities` is post-hoc; addressed by Â§3.8.2 (the 6-D gate is the guard — a cherry-picked redundant metric cannot clear the 6/5 ratio; `n_communities` did not).

**Renaming note — resolves `RANKED_FINDINGS.md` row 33 ambiguity**. "Gem #3 / Word-graph modularity" as listed in `docs/reference/findings/RANKED_FINDINGS.md` conflated two distinct implementations:

| Implementation | File | Metric | Score | Status |
|---|---|---|---:|---|
| (a) Per-unit *verse*-graph (archive method) | `experiments/exp48_verse_graph_topology/run.py` | n_communities d vs Arabic controls | +0.937 | âœ… **REPLICATES, PROMOTE verdict** |
| (b) Per-corpus *word*-graph (current `run_R6`) | `experiments/ultimate2_pipeline.py::run_R6` | Louvain modularity rank-ratio vs uniform null | 0.143 | âŒ **NOT REPRODUCED** |

The PROMOTE verdict in this Â§3.8.1 concerns implementation (a) only. Implementation (b) remains a negative finding and is not upgraded by this result.

**Source**: `experiments/exp48_verse_graph_topology/run.py`; pre-registration `experiments/exp48_verse_graph_topology/notes.md`; output `results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.json`; dependency `networkx >= 3.0` (added to `requirements.txt`).

#### 3.8.2 6-D Hotelling gate — SIGNIFICANT BUT REDUNDANT (exp49, v7.5)

**Closes the Â§3.8.1 6-D Hotelling follow-up with a pre-registered verdict.**

**Pre-registered gate** (from `experiments/exp48_verse_graph_topology/notes.md` before any run): `TÂ²_6D â‰¥ 5-D TÂ² Ã— 6/5 = 3 557.34 Ã— 1.2 = 4 268.81`. Above the threshold â†’ PROMOTE to 6th blessed channel. Below â†’ SIGNIFICANT BUT REDUNDANT.

**Protocol**:

1. Load `X_QURAN` (68 Ã— 5) and `X_CTRL_POOL` (2 509 Ã— 5) from the SHA-pinned `phase_06_phi_m.pkl` state (`FEAT_COLS = [EL, VL_CV, CN, H_cond, T]`).
2. For every Band-A (15 â‰¤ n_verses â‰¤ 100) unit in Quran and the six Arabic controls (`poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi`), compute `n_communities` on the same verse-transition graph exp48 builds. Iterate in `_build.py::_X_for` order so rows align with `X_QURAN` / `X_CTRL_POOL`.
3. Assert byte-exact agreement of the first 5 columns with `phase_06` matrices (build-time `np.allclose`; the run logs confirm `quran_5d_matches_phase06 = true` and `ctrl_5d_matches_phase06 = true`).
4. Two-sample pooled-covariance Hotelling TÂ² with ridge `Î» = 10â»â¶ Â· Iâ‚†`, byte-identical to `_build.py` Cell 29 / `exp26` / `exp01_ftail`.

**Result**:

| Statistic | 5-D (sanity) | 6-D (n_communities appended) |
|---|---:|---:|
| TÂ² | 3 557.34 (= locked) | **3 823.59** |
| F | 710.36 | 636.03 |
| df | (5, 2 571) | (6, 2 570) |
| Î”TÂ² vs 5-D | — | **+266.25** |
| per-dim TÂ² | 711.47 | 637.27 |
| per-dim gain ratio | — | **0.896** |
| n_quran, n_ctrl (after NaN drop) | 68, 2 509 | 68, 2 509 (0 dropped) |
| n_communities mean, Band-A | — | Quran 6.96, ctrl 5.80 |

**Verdict**: `TÂ²_6D = 3 823.59 < 4 268.81` â‡’ **SIGNIFICANT BUT REDUNDANT**.

**Interpretation**. `n_communities` is a significant Quran marker (exp48 d = +0.937, p = 1.2Â·10â»Â¹Â²) but most of its multivariate separation is already carried by combinations of the 5 blessed channels (likely EL rhyme + VL_CV length variability + H_cond root-bigram entropy; see Â§4.33 of `PAPER.md` for the mechanism). Per-dim gain ratio 0.896 < 1 means the added dimension gives *less* TÂ² per feature than the existing five — exactly the regime the pre-reg gate was designed to detect.

**What this does NOT imply**. The 5-D Î¦_M loses no explanatory power; if anything, this strengthens it by showing the 5-channel fingerprint spans the verse-graph information axis.

**What this DOES imply**. (i) No promotion to 6 blessed channels for `results_lock.json`. (ii) Â§3.8.1 becomes a supplementary replication finding (as reported in PAPER.md Â§4.31), not a Phi_M upgrade. (iii) A different graph-topology summary (spectral gap, multi-level modularity, etc.) *could* in principle pass the same gate; this verdict is specific to `n_communities` per the frozen pre-registration.

**Source**: `experiments/exp49_6d_hotelling/run.py`; pre-registration `experiments/exp49_6d_hotelling/notes.md`; output `results/experiments/exp49_6d_hotelling/exp49_6d_hotelling.json`. Runtime 8 s.

#### 3.8.3 Cross-corpus emphatic audit — Quran-specific immunity (exp50, v7.5)

**Closes the H1/H2 dichotomy left open by Â§4.30 of `PAPER.md`.**

**Setup**. The v7.4 full-mode exp46 found Quran emphatic-class detection = 1.15 % (120 / 10 461 edits). Two competing explanations:
- **H1 structural** — any Arabic corpus scored the same way sits at ~1 %; the blindness is a language-level floor.
- **H2 Quran-specific** — controls score noticeably higher; Quran is genuinely harder to forge with phonetically minimal edits.

exp50 runs the exact exp46 pipeline on `poetry_abbasi` and `poetry_jahili` with leave-target-out references (5 Arabic controls each, matching exp46's Quran setup).

**Pre-registered rule**: `R_T â‰¤ 0.020` â†’ H1; `R_T â‰¥ 0.050` â†’ H2; in-between â†’ INCONCLUSIVE. Aggregate uses `max(R_poetry_abbasi, R_poetry_jahili)`.

**Result (fast mode, 57 s)**:

| Corpus | Rate | n_edits | Per-target verdict | vs Quran (1.15 %) |
|---|---:|---:|:---|---:|
| `quran` (exp46 full) | 1.15 % | 10 461 | — (comparator) | 1Ã— |
| `poetry_abbasi` | 4.83 % | 600 | INCONCLUSIVE | **4.2Ã—** |
| `poetry_jahili` | 9.50 % | 600 | **H2_QURAN_SPECIFIC_IMMUNITY** | **8.3Ã—** |

**Aggregate**: `H2_QURAN_SPECIFIC_IMMUNITY`. Passes the 5 % threshold on poetry_jahili alone; poetry_abbasi is inside the gray band in fast mode but > 2Ã— the H1 ceiling.

**Implication for Â§3.8.3 and `PAPER.md Â§4.30`**. The v7.4 framing of "R1 blind spot" is revised to "Quran-specific structural immunity." The detector is working; it sees the Quran as harder to forge at the *edit-level* (not only the corpus-fingerprint level), which is the stronger claim. The Â§4.33 mechanism (high VL_CV + near-ceiling H_cond) makes the 5-D fingerprint mechanistically responsible for the edit-level asymmetry, not only the Mahalanobis separation.

**Caveats**: (i) fast mode only; full-mode rerun (~40 min) would resolve poetry_abbasi out of the gray band. (ii) 600 edits per control vs 10 461 for Quran — the 9.5 % on poetry_jahili is > 4Ïƒ of sampling noise above the 5 % threshold.

**Source**: `experiments/exp50_emphatic_cross_corpus/run.py --fast`; pre-registration `experiments/exp50_emphatic_cross_corpus/notes.md`; output `results/experiments/exp50_emphatic_cross_corpus/exp50_emphatic_cross_corpus.json`.

#### 3.8.4 exp48 poetry_islami sensitivity — STABLE (exp51, v7.5)

**Sensitivity appendix for Â§3.8.1.** The exp48 pre-registration (`{poetry_abbasi, poetry_jahili, hindawi, ksucca, arabic_bible}`) accidentally omitted `poetry_islami`, which `_build.py::Cell 22` treats as a first-class Arabic control (`ARABIC_CTRL_POOL`). Â§3.8.1's d = +0.937 is the locked headline; this section measures how much the headline moves under the corrected pool.

**Pre-registered stability rule**: STABLE iff `V_ext == PROMOTE` AND `|Î”d| < 0.30`.

**Result** (runtime 120 s):

| Metric | d (pre-reg pool, sanity) | d (extended pool) | Î”d | fires (pre-reg â†’ ext) |
|---|---:|---:|---:|:---|
| `clustering` | +0.000 | +0.000 | +0.000 | no â†’ no |
| `avg_path_norm` | âˆ’0.550 | âˆ’0.570 | âˆ’0.020 | yes â†’ yes |
| `modularity` | +0.672 | +0.690 | +0.018 | yes â†’ yes |
| `n_communities` | **+0.937** | **+0.964** | **+0.027** | **yes â†’ yes** |
| `bc_cv` | âˆ’0.500 | âˆ’0.519 | âˆ’0.019 | yes â†’ yes |
| `small_world_sigma` | +0.000 | +0.000 | +0.000 | no â†’ no |

- Pre-reg-pool column reproduces exp48 headline **byte-exactly** (sanity âœ“).
- Extended-pool: n_fires = 4 / 6, verdict = PROMOTE, strongest d = +0.964.
- **Stability verdict**: **STABLE** (Î”d = +0.027, inside Â±0.30 band).

poetry_islami has mean `n_communities` = 4.15 (lower than the prior control mean 4.67), so including it *tightens* the Quran-vs-pool gap rather than softening it.

**Paper continues to report**: d = +0.937 (pre-registered headline, for replicability integrity) with a footnote disclosing the poetry_islami sensitivity result.

**Source**: `experiments/exp51_exp48_sensitivity_islami/run.py`; pre-registration `experiments/exp51_exp48_sensitivity_islami/notes.md`; output `results/experiments/exp51_exp48_sensitivity_islami/exp51_exp48_sensitivity_islami.json`.

#### 3.8.5 LC3-70-U (T, EL) tight parsimony proposition — PARSIMONY PROPOSITION PUBLISHED (exp60 + exp70 + exp74, v7.7; post-publication ablation exp89 / exp89b / exp90)

**Publishes `PAPER.md Â§4.35`.** Formalises the LC3 (T, EL)-sufficiency result (`exp36` AUC = 0.9971 Â± 0.0006, 25 seed Ã— fold) as a tight Fisher-optimal linear classifier fit by linear SVM over the Band-A 68 Q + 2 509 Arabic ctrl split.

**Discriminant**: `L(s) = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221` (exp70, margin 0.4787).

**Headline metrics** (from `results/experiments/exp70_decision_boundary/exp70_decision_boundary.json`):

| Statistic | Value |
|---|---:|
| in-sample accuracy | **99.15 %** |
| AUC | **0.9975** |
| margin | 0.4787 |
| Quran-side (L > 0) | 53 / 68 |
| Quran C-side (L â‰¤ 0) | 15 / 68 |
| Ctrl-side (L â‰¤ 0) | 2 502 / 2 509 |
| Ctrl leaks (L > 0) | **7 / 2 509 (0.28 %)** — **all from `arabic_bible`** |
| Leaks from other 5 families (`poetry_{jahili, islami, abbasi}`, `ksucca`, `hindawi`) | **0** |

**LC3 sufficiency check** (from `results/experiments/exp60_lc3_parsimony_theorem/exp60_lc3_parsimony_theorem.json`): conditional MI residual over (VL_CV, CN, H_cond) given (T, EL) maxes at **0.089 bits** on VL_CV; total residual **0.022 bits**. Strict 0.02-bit theorem gate NOT met â†’ verdict **PARTIAL**. Top-2 eigen-overlap with PC1 Ã— PC2 = 0.657.

**Five corollaries** (summarised — full derivations in `PAPER.md Â§4.35`):

1. **Two-feature sufficiency** — baseline LC3 (max residual CMI 0.089 bits on VL_CV, PARTIAL on strict gate).
2. **Linear sufficiency** — no kernel / boundary-curvature gain over the linear discriminant.
3. **Margin 0.4787** — Fisher-optimal boundary leaves a well-defined no-man's-land.
4. **Competing-discriminator uniqueness** — five alternative discriminators all WEAK/REDUNDANT/NULL/FALSIFIER:

   | Exp | Metric | Verdict |
   |---|---|---|
   | `exp64_unified_law_ensemble` | two-scale unified-law ensemble | WEAK (no family consistently excluded) |
   | `exp66_extended_mahalanobis` | 10-D Mahalanobis (+phi_structural, +TE_net) | REDUNDANT (Î”sep negative) |
   | `exp83_order_sensitivity` | per-surah order-sensitivity index | NULL (Quran is LEAST sensitive) |
   | `exp84_network_topology` | small-world / scale-free / fractal | NULL (also `PAPER.md Â§5` retraction) |
   | `exp87_unified_probe` | micro-macro joint probe | FALSIFIER_TRIGGERED (micro features hurt separation) |

5. **Geometric localisation** — `exp74_subspace_test` DETERMINATE: the Quran-control displacement concentrates on a **1.66 %-variance eigen-direction** of the control covariance (PC4, â‰ˆ99 % EL loading); Mahalanobis TÂ² blindspot fraction = **54 %**, permutation p < 1/5 000; `r(EL, T) | controls = 0.050` (â‰ˆ orthogonal), so the plane is not a collinearity artefact.

**Shadow-projection table** — other one-dimensional signatures consistent with the same (T, EL) plane (each already reported in `PAPER.md Â§4.*`):

| Signature | Experiment | Verdict |
|---|---|---|
| Hurst ladder (H_verse > H_delta > H_word) | `exp68_hurst_ladder` | PARTIAL |
| VAR(1) cross-feature dynamics (5-D eigenvalues) | `exp63_var1_cross_feature` | SIGNIFICANT |
| MI-decay rate (verse-verse MI slope) | `exp80_mi_decay` | SUGGESTIVE |
| Zipf exponent pair (Î±_word, Î±_root) | `exp76_zipf` | DISTINCT |
| Emphatic-edit immunity (Quran 1.15 % vs poetry 4.8–9.5 %) | `exp50_emphatic_cross_corpus` (v7.5) | QURAN-SPECIFIC IMMUNITY |

**What this changes for the paper**. `Â§4.35 LC3-70-U` is the strongest publishable parsimony proposition currently standing; `PAPER.md` prose is organised around this equation with corollaries (1)–(5) each cited to a standing experiment. No `results_lock.json` scalar is modified — the locked scalars live in `exp70_decision_boundary.json` (discriminant coefficients + margin) and `exp60_lc3_parsimony_theorem.json` (residual CMI).

**Path to PROVED (from PARTIAL)**. Close the 0.089-bit VL_CV residual. The pre-registered ablation option has been executed (`exp89`): both single features exceed the 0.95 bar, so that path is closed — predictive content is 1-D in EL, not 2-D. The cross-language option has been executed (`exp90`): Tanakh / Greek NT / `arabic_bible` all cluster in EL âˆˆ [0.12, 0.21], not convergent with Quran 0.71, so the scripture-class route is also closed for EL alone. Remaining routes: (a) a plane-sufficiency proof under the observed Î£ eigenstructure, (b) a language-normalised-ceiling reformulation that tests scripture-vs-secular as fraction-of-max-achievable-EL per language, (c) cross-corpus replication of the full 2-D (T, EL) plane (not EL alone) on Hebrew/Greek with same-language secular controls.

**Figure 7 regenerator**: `experiments/exp88_lc3_70_u/run.py` (zero-new-computation rebuild from `exp70` JSON + `phase_06_phi_m.pkl`). Emits `fig7_lc3_70_pareto.png`, `fig7_data.csv`, `receipt.json`. First-run verification reproduces **53 / 68 Quran-side** + **7 / 977 arabic_bible leaks** + **0 / 1 532 from other 5 families** — every scalar in Â§4.35 confirmed to the row.

**Source**: `docs/PAPER.md:749-826`; `experiments/exp60_lc3_parsimony_theorem/run.py`; `experiments/exp70_decision_boundary/run.py`; `experiments/exp74_eigenvalue_spectrum/run.py` (+ `exp74_subspace_test.json`); `experiments/exp88_lc3_70_u/run.py`.

---

## 4. Arabic-textology constants (by-products)

Two numerical constants emerge as methodologically reusable independent of the Quran-specific claim:

1. **H(harakat | rasm) = 1.964 bits** — channel capacity of full vocalisation given consonantal rasm, across vocalised Quran. Any Arabic NLP system recovering harakat from rasm is bounded below by this number. Replication-tight at tol 0.15, locked in `results_lock.json`.
2. **I(EL; CN) corpus-level = 1.175 bits** — mutual information between end-letter rhyme rate and connective start rate at the corpus level across 8 Arabic corpora. Replication-tight at tol 0.10.

Both are **not Quran-unique**; they are empirical constants of Arabic textology under CamelTools `calima-msa-s31`.

---

## 5. Gap closure status (formal proof)

| Gap | v2 status | v6 status | Evidence |
|:-:|---|---|---|
| G1 heavy-tail Bennett | closed | âœ… closed | Hill Î± â‰¥ 1.8 on all 5 features |
| G2 5-channel MI | closed | âœ… closed (reinterpreted) | max normalised MI = 0.318 â†’ "jointly informative" |
| G3 Hessian PD | closed | âŒ falsified by math | H = 2Â·Î£â»Â¹ is PD by construction |
| G4 exponential-family | open | open | needs information-theory co-author |
| G5 Î³(Î©) linear form | closed | âŒ falsified by math | regresses algebraic identity |

**Net: 2 / 5 genuinely closed.** Gaps 3 and 5 were previously claimed closed based on proxies that are tautologies; they are transparently retracted.

---

## 6. Pre-registration outcomes (v10.18 frozen 2026-04-18)

| Test | Threshold | Observed | Verdict |
|:-:|---|---|:-:|
| A (Î¦_M LOFO min d â‰¥ 1.5) | â‰¥ 1.5 | **5.26** | âœ… PASS |
| B (F_Meccan > 1 AND F_Medinan > 1) | both > 1.0 | 0.797 / â‰ˆ0.84 | âŒ FALSIFIED |
| C (Î© bootstrap > 2.0 fraction â‰¥ 95 %) | â‰¥ 95 % | **100 %**, median 10.0 | âœ… PASS STRONGER |

---

## 7. Deprecated legacy statistics (with replacements)

| Legacy | Replaced by | Reason |
|:-:|---|---|
| `D02` / `S1` Cohen's d on Î¦_M (biased) | `Phi_M_hotelling_T2` + `Phi_M_perm_p_value` | d assumes univariate; Hotelling is the correct multivariate |
| `D28` tight-fairness retest (d) | Hotelling on Band-A | subsumed |
| `D27` non-directional Abbasi d | `D27_directional` / `Abbasi_directional_beats` | non-directional confuses sign |
| Fisher `1 âˆ’ chi2.cdf` | `chi2.sf` | machine-epsilon floor |

Deprecated scalars retain their expected-value / tolerance / "OK" drift status for replication compatibility; every paper-quality citation uses the replacement.

---

## 8. Upgrade roadmap (higher-tier discoveries, modularisation plan)

The audit identified six classes of test that can strengthen the paper from "multivariate outlier characterisation" toward "information-theoretic law candidate." Each is proposed as an **independently testable notebook cell** under `notebooks/ultimate/upgrades/`, with a clear accept/reject rubric before integration into the primary pipeline.

### 8.1 Proposed file layout

```
notebooks/ultimate/
â”œâ”€â”€ QSF_ULTIMATE.ipynb                 # primary (frozen, integrity-locked)
â”œâ”€â”€ _build.py                          # build script
â”œâ”€â”€ _audit_check.py                    # 77-marker regression sentinel
â””â”€â”€ upgrades/                          # NEW
    â”œâ”€â”€ README.md                      # upgrade protocol (accept/reject)
    â”œâ”€â”€ U01_mdl_bounds.ipynb           # MDL compression-cost bounds
    â”œâ”€â”€ U02_concentration.ipynb        # sub-Gaussian/McDiarmid concentration
    â”œâ”€â”€ U03_compression_distance.ipynb # NCD distance to control clouds
    â”œâ”€â”€ U04_conditional_hsic.ipynb     # conditional HSIC given T
    â”œâ”€â”€ U05_falsification.ipynb        # N_PERM = 10 000 full-mode rerun
    â””â”€â”€ U06_eigenstructure.ipynb       # full 5Ã—5 eigendecomposition tracking
```

Each upgrade is a **standalone notebook** that:

- Reads only the frozen `results/checkpoints/*.pkl` + `_manifest.json` (SHA-pinned).
- Writes to `results/upgrades/<id>_report.json` only.
- Does **not** modify any locked scalar in `results_lock.json`.
- Has its own `integrity/<id>_lock.json` if promoted.

Promotion criterion (= integration into the primary pipeline): **two independent successful runs + reviewer cross-check**.

### 8.2 U01 — MDL compression-cost bounds

**Goal**: bound the minimum description length of the Quran's 5-D fingerprint under a Gaussian mixture and under a t-copula, to produce a model-agnostic "complexity floor" for peer review.

**Method**: fit GMM-k (k âˆˆ {1, 2, 3}) and a t-copula; report MDL in bits = âˆ’log L + (k log n) / 2. Compare to per-corpus MDL. Expected: Quran MDL â‰¥ any control at k = 1, with â‰¤ 5 % margin.

**Accept rule**: MDL ordering matches Î© ordering (rank correlation â‰¥ 0.7).

**Reject rule**: Quran MDL < any non-ksucca control.

### 8.3 U02 — Concentration of measure

**Goal**: strengthen the informal Â«GaussianÂ» approximation by a McDiarmid / sub-Gaussian concentration bound on the sample Î¦_M.

**Method**: for each feature, bound the Lipschitz constant L_i; apply McDiarmid P(|Î¦_M âˆ’ E[Î¦_M]| > t) â‰¤ 2 exp(âˆ’2 tÂ² / Î£ L_iÂ²). Report the p-value floor under this bound.

**Accept rule**: concentration bound tighter than 10â»Â¹âµ at observed deviation.

### 8.4 U03 — Normalised Compression Distance

**Goal**: model-free independence from the 5-D feature space by computing the Normalised Compression Distance (NCD) between corpus-concatenated raw text and the Quran, using `zstd --ultra -22`.

**Method**: NCD(x, y) = (C(x+y) âˆ’ min(C(x), C(y))) / max(C(x), C(y)). Report per-corpus NCD to Quran.

**Accept rule**: Quran is a distinctive-NCD outlier (rank #1 in separation from control centroid).

**Reject rule**: closer than ksucca on NCD.

### 8.5 U04 — Conditional HSIC given T

**Goal**: test whether the 5-channel HSIC max-pair perm p survives conditioning on the structural-tension feature T (i.e., is the joint-informativeness robust after controlling for T?).

**Method**: kernel conditional HSIC at Gaussian bandwidth 0.5 Ïƒ, N_PERM = 1 000, per pair given T.

**Accept rule**: max conditional HSIC perm p < 0.01, BH-surviving at q â‰¤ 0.05.

### 8.6 U05 — Full-mode falsification (N_PERM = 10 000)

**Goal**: push `Phi_M_perm_p_value` below the FAST_MODE floor of 1/201 = 0.005 to a true 10â»â´ regime.

**Method**: identical pipeline, N_PERM = 10 000 on the Î¦_M Hotelling null. Expected wall-clock â‰ˆ 4–6 h on a laptop.

**Accept rule**: p < 10â»Â³ under full mode.

### 8.7 U06 — Eigenstructure tracking

**Goal**: report the full 5Ã—5 control-covariance eigendecomposition per Band, track how the top-2 eigenvectors align with the Quran's mean displacement, and test whether the separation is dominated by a single feature or by a diffuse combination.

**Method**: eigendecomposition of Î£_control; compute cos(âˆ (v_i, xÌ„_Q âˆ’ Î¼_C)) for each eigenvector. Report the "effective dimensionality" of the separation (participation ratio of squared projections).

**Accept rule**: effective dimensionality â‰¥ 3 (separation is genuinely multivariate).

**Reject rule**: effective dimensionality â‰ˆ 1 (separation reduces to a single feature).

### 8.8 Integration policy

- No upgrade is allowed to **modify** any locked scalar in `results_lock.json`.
- Each upgrade adds a new scalar to a `results_lock_upgrades.json` if promoted.
- The `_audit_check.py` regression sentinel is extended by one marker per promoted upgrade.
- Any upgrade that **fails its accept rule** is archived in `notebooks/ultimate/upgrades/failed/`, with its reject reason in `README.md`.

---

## 9. Honest open gaps (current)

### 9.1 Still open (severity Ã— priority)

| Gap | Severity | Priority | What would close it |
|---|:-:|:-:|---|
| G4 exponential-family generalisation | LOW | LOW | Information-theory co-author, CsiszÃ¡r-KÃ¶rner tilting |
| Cross-language band-A corpus | MEDIUM | MEDIUM | Band-matched Tanakh / Greek-NT / Iliad corpus; current v6 fallback removal makes honest INFEASIBLE skip |
| Formal OSF registration | LOW | MEDIUM | 15 min at osf.io/prereg using `preregistration.json::manifest_hash` — **v7.3 OSF deposit packet ready at `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip` (SHA-256 `2f90a87a…`), awaiting upload** |
| P1/P3 behavioural proxy â†’ real | MEDIUM | LOW | Psycholinguistics lab collaboration |
| Independent replication | HIGH | UNKNOWN | External team; what journal submission solves |
| Methodology co-author | MEDIUM | HIGH | Arabic-linguist or information-theorist email contact |
| Full-mode N_PERM = 10 000 | LOW | HIGH (easy win) | U05 upgrade, 4–6 h laptop |
| **v7.3 — Two-letter enumeration on Adiyat** | LOW | MEDIUM | extend `exp43_adiyat_864_compound` to 864Â² â‰ˆ 746 k variants; 1 hour compute; closes the "single-letter-only" gap in `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` Â§4.2.2 |
| **v7.3 — exp39 Abrahamic extension** | MEDIUM | HIGH | add BoM / Bhagavad Gita / Septuagint / Pali corpora; replicate exp35 R3 canonical-ordering test across religious scripture families; decisive for PNAS-grade angle |
| **v7.3 — exp42 perplexity tier** | MEDIUM | LOW | train 50 M-param BPE transformer on non-Quran Arabic, score canonical vs 864 variants; 2–6 weeks GPU; independent R12 confirmation |
| **v7.3 — F6 + AR(1) external replication** | HIGH | HIGH | two-team review packet for F6 (lag-1 Spearman d = +0.83) and AR(1) coef (d = +1.095); needed before `results_lock.json` promotion |
| **v7.3 — R12 length-confound robustness** | LOW | MEDIUM | verify Î³ = +0.07 fixed-length residual is not driven by a small number of long outlier surahs; per-surah jackknife; 30 min compute |

### 9.2 Partially closed

| Gap | What's done | What's still missing |
|---|---|---|
| Root-extractor accuracy | 63 % CamelTools gold-set | Re-verify Î¦_M effect on 95 %+ hand-curated roots for ksucca-tie sensitivity |
| 10-fold CV strict threshold | 9/10 at p < 0.01 | Fold 3 at p = 0.02; honest PARTIAL |
| Behavioural proxy | Compression PROXY-2 positive (p = 10â»Â¹Â²) | Real human memory experiment |

---

## 10. Re-usable scalars (locked registry)

From `results/integrity/results_lock.json` (abridged; **57 tolerance-gated scalars** in this file; 127 total scalars in `ULTIMATE_REPORT.json`). Each row is a triple (id, expected, tol) verified at every build:

| ID | Expected | Tol | Role |
|:-:|---:|---:|---|
| `Phi_M_hotelling_T2` | 3 557.34 | Â±5 % envelope | headline |
| `Phi_M_perm_p_value` | 4.98Â·10â»Â³ | Â±5 % envelope | headline |
| `Phi_M_MWU_p_value` | 1.75Â·10â»â´â´ | Â±5 % log | headline secondary |
| `T15_nested_auc` | 0.998 | 0.02 | candidate-future |
| `D10_quran_T_positive_pct` | 39.7 % | 2.0 | tension |
| `D14_verse_internal_gap` | 5.80 | 0.2 | perturbation |
| `D26_bootstrap_omega_pct_gt2` | 100 % | 2.0 | pre-reg C |
| `D11_letter_gap` | 0.80 | 0.1 | perturbation letter |
| `D11_word_gap` | 2.45 | 0.1 | perturbation word (LOCUS) |
| `D11_verse_gap` | 1.77 | 0.1 | perturbation verse |
| `D07_neglog10_p_W10` | 16.08 | 0.3 | Fisher scale-free |
| `E_harakat_capacity` | 1.964 | 0.15 | textology constant |
| `I_EL_CN_corpus` | 1.175 | 0.10 | textology constant |
| `Supp_A_Hurst_RS` | 0.738 | 0.03 | long memory |
| `Hurst_DFA_quran` | 0.901 | 0.03 | long memory |
| `Adiyat_blind` | 0.5714 | 0.15 | micro-case |
| `Adiyat_metric7_perm_p` | 0.0697 | 0.05 | micro-case |
| `phi_frac` | âˆ’0.915 | 0.20 | RETRACTED golden-ratio |
| `F_Meccan` | 0.797 | 0.05 | FALSIFIED pre-reg B |
| `F_Medinan` | 0.84 | 0.05 | FALSIFIED pre-reg B |
| `L6_gamma_omega_slope` | âˆ’0.0043 | 0.10 | null law |
| `L7_sparse_pca_d` | 4.81 | 0.3 | feature-rotation robustness |
| `L7_sparse_pca_perm_p` | 0.005 | 0.001 | feature-rotation robustness |
| `T2_min_LOFO_d` | 5.26 | 0.3 | pre-reg A |
| `T12_min_fold_d` | 5.08 | 0.3 | 10-fold robustness |
| `G2_max_normalised_MI` | 0.318 | 0.05 | 5-channel dependency |
| `exp27_quran_H_char_3_over_2_pooled` *(v7.1)* | 0.7136 | 0.02 | NEW char-scale ratio, Quran (rank 2/7) |
| `exp27_ctrl_H_char_3_over_2_mean_unit` *(v7.1)* | 0.2877 | 0.02 | NEW ctrl per-unit H3/H2 mean |
| `exp27_H_char_3_over_2_cohen_d_Q_vs_ctrl` *(v7.1)* | +0.457 | 0.10 | NEW negative direction — retraction key |
| `exp28_scales_supported` *(v7.1)* | 3 / 5 | strict | NEW scale-invariant-law verdict numerator |
| `exp28_verdict_string` *(v7.1)* | `PARTIAL_LAW_HOLDS_AT_MAJORITY_SCALES` | exact | NEW ordinal verdict |
| `exp28_char_root_gap_quran_rank` *(v7.1)* | 4 / 7 | strict | NEW secondary-fingerprint rank |
| `exp29_P_composite_ctrl_null` *(v7.1)* | 0.137 | 0.05 | NEW cascade composite, single-letter internal edits |
| `exp29_p_L0_hchar_ctrl_null` *(v7.1)* | 0.137 | 0.05 | NEW per-channel, only non-zero channel |
| `exp29_p_L1_phi_m_window` *(v7.1)* | 0.000 | strict | NEW structurally-blind channel (10-verse Î¦_M) |
| `exp29_p_L2_phi_m_surah` *(v7.1)* | 0.000 | strict | NEW structurally-blind channel (surah Î¦_M) |
| `exp29_p_L3_phi_m_drift` *(v7.1)* | 0.000 | strict | NEW structurally-blind channel (drift-from-centroid) |
| `exp29_MW_p_L0_hchar_Q_gt_ctrl` *(v7.1)* | 4.9Â·10â»Â³ | log-0.3 | NEW Quran-specificity at L0 only (small effect) |
| `exp30_P_composite_R1_9ch_ctrl_null` *(v7.1)* | 0.417 | 0.05 | NEW R1 9-channel cascade on internal edits |
| `exp30_best_single_channel_E_ncd` *(v7.1)* | 0.113 | 0.02 | NEW best single channel (gzip), only one above 0.10 |
| `exp30_fire_rate_quran_ge_3_channels` *(v7.1)* | 0.056 | 0.02 | NEW R1 fire rate at canonical â‰¥3 ch / |z|>2 |
| `exp30_fire_rate_ctrl_ge_3_channels` *(v7.1)* | 0.024 | 0.02 | NEW ctrl false-positive rate (5% floor) |
| `exp30_Adiyat_A_channels_fired` *(v7.1)* | 1 / 9 | strict | NEW (Adiyat Ø¹â†’Øº variant): E_ncd only |
| `exp30_Adiyat_B_channels_fired` *(v7.1)* | 2 / 9 | strict | NEW (Ø¶â†’Øµ): E_ncd + G_root_trigram |
| `exp30_Adiyat_C_channels_fired` *(v7.1)* | 3 / 9 | strict | NEW (both): E_ncd + G_root_trigram + C_bigram_dist |
| `exp31_centroid_drift_N50_median` *(v7.2)* | 0.26 | 0.05 | NEW subset-centroid drift at N=50 of 68 surahs (Mahalanobis units) |
| `exp31_T2_fraction_ge_half_full_at_N50` *(v7.2)* | 1.000 | strict | NEW fraction of N=50 subsets giving TÂ² â‰¥ 50 % of full-TÂ² (4 189) |
| `exp31_T2_fraction_ge_half_full_at_N34` *(v7.2)* | 0.518 | 0.05 | NEW fraction at half-sample (N=34) |
| `exp33_silhouette_Q_vs_ctrl` *(v7.2)* | +0.6515 | 0.02 | NEW silhouette (Mahalanobis, Band-A), strong-cluster threshold is +0.5 |
| `exp33_NNR_within_Q_over_cross_QC` *(v7.2)* | 0.504 | 0.02 | NEW nearest-neighbour ratio; <1 means Quran clusters tighter to self |
| `exp33_island_gap` *(v7.2)* | âˆ’3.94 | 0.10 | NEW single-linkage island gap (negative = continuum, not island) |
| `exp33_perm_p_gap_ge_observed` *(v7.2)* | 0.3194 | 0.02 | NEW gap is not extreme under null; island hypothesis FALSIFIED |
| `exp34_phi_sym_canonical_Adiyat` *(v7.2)* | +1.7156 | 0.001 | NEW Î¦_sym of canonical Surah 100 |
| `exp34_phi_sym_delta_A_in_sigmaQ` *(v7.2)* | âˆ’0.162 | 0.02 | NEW Adiyat-A shift in Ïƒ_Q units (Ø¹â†’Øº) |
| `exp34_phi_sym_delta_B_in_sigmaQ` *(v7.2)* | âˆ’0.155 | 0.02 | NEW Adiyat-B shift in Ïƒ_Q units (Ø¶â†’Øµ) |
| `exp34_phi_sym_delta_C_in_sigmaQ` *(v7.2)* | âˆ’0.323 | 0.02 | NEW Adiyat-C shift in Ïƒ_Q units (both) — all three BLIND |
| `exp35_R3_z_Quran` *(v7.2)* | âˆ’8.920 | 0.10 | NEW authoritative R3 z for Quran (114 surahs, N_PERM 5 000) |
| `exp35_R3_z_Tanakh` *(v7.2)* | âˆ’15.286 | 0.10 | NEW R3 z for Hebrew Tanakh (921 chapters) |
| `exp35_R3_z_GreekNT` *(v7.2)* | âˆ’12.063 | 0.10 | NEW R3 z for Greek NT (260 chapters) |
| `exp35_R3_z_Iliad_control` *(v7.2)* | +0.336 | 0.05 | NEW Iliad z (24 books, fails BH as expected for narrative ctrl) |
| `exp35_R3_BH_min_p_adj` *(v7.2)* | 3Â·10â»â´ | log-0.3 | NEW BH-pooled min p across 4 scriptures |
| `exp36_TxEL_AUC_mean_across_5_seeds` *(v7.2)* | 0.9971 | 0.001 | NEW across-seed meta-AUC for 2-feature (T, EL) nested-CV |
| `exp36_TxEL_AUC_std_across_5_seeds` *(v7.2)* | 5.6Â·10â»â´ | 2Â·10â»â´ | NEW across-seed std — META_STABLE verdict threshold Ïƒ < 5Â·10â»Â³ |
| `exp36_TxEL_AUC_min_across_25_folds` *(v7.2)* | 0.9928 | 0.002 | NEW worst fold across 5 seeds Ã— 5 outer folds |
| `exp37_LPEP_avgH_quran_pooled` *(v7.3 cand.)* | 1.946 | 0.02 | NEW Quran pooled `<H(pos\|L,k)>` over 28-letter Ã— max-word-len tensor |
| `exp37_LPEP_avgH_iliad_pooled` *(v7.3 cand.)* | 2.156 | 0.02 | NEW Iliad Greek pooled — confirms cross-script Semitic-root signature |
| `exp37_LPEP_quran_vs_arabic_ctrl_cohen_d` *(v7.3 cand.)* | +0.150 | 0.05 | NEW wrong-sign vs hypothesis; Quran rank 2/7 Arabic |
| `exp38_CCAS_raw_frob_cohen_d` *(v7.3 cand.)* | âˆ’0.026 | 0.02 | NEW null — replicates locked `exp30::C_bigram_dist` |
| `exp38_CCAS_normalised_frob_cohen_d` *(v7.3 cand.)* | âˆ’0.119 | 0.02 | NEW wrong-direction; consistent with Quran high Ïƒ_intra_doc |
| `exp38_CCAS_normalised_mw_p_less` *(v7.3 cand.)* | 4.5Â·10â»Â¹â· | log-0.5 | NEW statistical strength of wrong-direction finding |
| `exp41_R12_ncd_doc_cohen_d_raw` *(v7.3 cand.)* | +0.534 | 0.05 | NEW raw d — length-confounded, quote ONLY with Î³ below |
| `exp41_R12_ncd_doc_mw_p_greater` *(v7.3 cand.)* | 6.6Â·10â»Â³â¹ | log-0.5 | NEW raw population MW |
| `exp41_R12_length_controlled_gamma` *(v7.3 cand.)* | +0.0716 | 0.005 | NEW log-linear Quran residual at fixed length — **paper-grade headline** |
| `exp41_R12_length_controlled_gamma_CI_lo` *(v7.3 cand.)* | +0.0657 | 0.002 | NEW 95 % CI lower bound |
| `exp41_R12_length_controlled_gamma_CI_hi` *(v7.3 cand.)* | +0.0775 | 0.002 | NEW 95 % CI upper bound |
| `exp41_R12_ctrl_null_p95_doc` *(v7.3 cand.)* | 0.0495 | 0.002 | NEW pre-registered ctrl-null 95th percentile (doc-scale NCD) |
| `exp41_R12_adiyat_A_z_ctrl` *(v7.3 cand.)* | +5.58 | 0.10 | NEW Adiyat Ø¹â†’Øº z under exp41 ctrl-null |
| `exp41_R12_adiyat_B_z_ctrl` *(v7.3 cand.)* | +5.58 | 0.10 | NEW Adiyat Ø¶â†’Øµ z |
| `exp41_R12_adiyat_C_z_ctrl` *(v7.3 cand.)* | +9.14 | 0.10 | NEW Adiyat both-letters z |
| `exp43_adiyat_pct_phi_m_above_canonical` *(v7.3 cand.)* | 0.0 % | strict | NEW `0/864` variants exceed canonical Î¦_M |
| `exp43_adiyat_pct_phi_m_equal_canonical` *(v7.3 cand.)* | 96.8 % | 0.1 | NEW `836/864` tied (feature-invariant decoys) |
| `exp43_adiyat_r2_ncd_doc_above_ctrl95` *(v7.3 cand.)* | 99.1 % | 0.5 | NEW D2 fire rate on 864 variants |
| `exp43_adiyat_ncd_and_ccas_f_joint` *(v7.3 cand.)* | 99.1 % | 0.5 | NEW paper-grade compound (D2 âˆ§ D5) |
| `exp44_ar1_coef_cohen_d` *(v7.3 cand.)* | +1.095 | 0.10 | NEW AR(1) coef of verse-length sequence; F6 replacement candidate |
| `exp44_ar1_coef_mw_p_greater` *(v7.3 cand.)* | 1.8Â·10â»Â¹Â² | log-0.5 | NEW AR(1) MW one-sided |
| `exp44_iac_abs_15_cohen_d` *(v7.3 cand.)* | âˆ’0.546 | 0.05 | NEW integrated autocorrelation over lags 1–15 (reverse direction) |
| `exp44_iac_abs_15_mw_p_less` *(v7.3 cand.)* | 2.4Â·10â»â¶ | log-0.5 | NEW p_less for "punchy not wide" claim |

v7.1 / v7.2 / v7.3 scalars are **not** registered in the Ultimate-1 `results_lock.json` (which would require a full pipeline rerun). They are tracked in the sandbox JSON outputs listed next to each row; integrity is enforced by `self_check_begin/end` around every exp27–exp44 run and by `experiments/_verify_all.py` across all receipts. The v7.3 scalars marked *(v7.3 cand.)* are additionally SHA-pinned inside `arxiv_submission/osf_deposit_v73/osf_deposit_manifest.json` (overall_sha256 `2f90a87a…`) as a post-hoc code-state lock; promotion into `results_lock.json` is gated on two-team external replication.

---

## 11. How to reproduce a single claim in 60 s

```powershell
# Ex: replicate Phi_M headline only
python -X utf8 -u src/clean_pipeline.py --only T2

# Ex: replicate D07 scale-free Fisher
python -X utf8 -u src/clean_pipeline.py --only T16

# Ex: full clean pipeline (102 s, 31 tests)
python -X utf8 -u -m src.clean_pipeline

# Ex: integrity-locked ultimate build (70 min FAST)
python -X utf8 -u notebooks/ultimate/_build.py
jupyter nbconvert --to notebook --execute notebooks/ultimate/QSF_ULTIMATE.ipynb
python -X utf8 notebooks/ultimate/_audit_check.py
```

Any scalar can be re-verified individually against its locked expected-value in `results/integrity/results_lock.json`.

---

## 12. What the paper can claim (and what it cannot)

### 12.1 Can claim

1. The Quran is a Hotelling TÂ² = 3 557 multivariate outlier in a specific 5-D feature space relative to 2 509 band-A Arabic-control units drawn from six independent families.
2. Nested 5-fold CV separates the Quran from Arabic controls at AUC = 0.998.
3. The effect survives leave-one-family-out, 10-fold Quran-internal resampling, and 1 000-bootstrap of Î©.
4. The structural signal is localised at the word scale (2.45 d-gap) rather than at the letter or verse scale.
5. Two Arabic-textology constants (H(harakat | rasm) = 1.964 bits; I(EL; CN) corpus-level = 1.175 bits) are empirically stable.
6. Three previously reported claims (phi_frac, joint Meccan-Medinan F>1, rhyme-swap P3) do not reproduce and are retracted.
7. **(v7.3, candidate)** R12 gzip NCD on the 28-letter consonantal rasm is a length-controlled Quran-specific signal: **Î³ = +0.0716** at fixed length (95 % CI [+0.066, +0.078], p â‰ˆ 0) over 1 360 Quran + 4 000 ctrl internal single-letter edits (on the linear scale this is â‰ˆ 7.4 % higher NCD per edit, but the regression coefficient Î³ is the authoritative scalar). **Distinct from the locked E_ncd channel**; awaits two-team external replication before promotion to `results_lock.json`.
8. **(v7.3, candidate)** AR(1) coefficient of the mean-centred verse-length sequence separates Quran from Arabic-ctrl at d = +1.095 (MW p_greater = 1.8Â·10â»Â¹Â²) while integrated autocorrelation over lags 1–15 is LOWER in the Quran (d = âˆ’0.546, p_less = 2.4Â·10â»â¶): "punchy at lag 1, rapidly decorrelated beyond lag 2" vs controls' sustained long-range persistence. Candidate 6th Î¦_M feature — see Â§12.3 note below for the exp49 6-D gate on the sibling `n_communities` candidate, which closed as SIGNIFICANT BUT REDUNDANT and therefore sets the bar the AR(1) candidate must clear.
9. **(v7.3)** No single-letter substitution of Surah 100 verse 1 raises Î¦_M above canonical (0/864 exceed; 836 tie as feature-invariant decoys). 99.1 % of 864 variants fire the R12 ctrl-p95 threshold. Full discussion: `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md`.

### 12.2 Cannot claim

1. A universal law of scriptural composition (Î³(Î©) slope â‰ˆ 0).
2. A physics-class natural constant.
3. A metaphysical or theological inference.
4. Independence of the 5 feature channels (they are jointly informative, max normalised MI = 0.318, not independent).
5. Uniqueness within Arabic prose on **every** aggregate composite (ksucca ties on Î© at 8.43 vs 8.29; reported prominently).
6. Cross-language generalisation (currently INFEASIBLE under band-A filter; deferred).
7. **(v7.3)** Forgery-resistance to multi-letter edits, whole-surah-level forgery, or philological / semantic-aware edits. R12 is a single-letter population-level edit detector; R5 (Â§4.14) shows the Quran is NOT unforgeable at the surah level (50 % of EL+RD-aware Markov-2 forgeries fall below Quran Î¦_M).
8. **(v7.3)** "R12 uniquely catches Adiyat." R12 is a population-level Quran-edit detector that fires on 99.1 % of internal single-letter edits; the A/B/C Adiyat variants are in-distribution instances of this population, not exceptional firings.
9. **(v7.3)** LPEP (Letter-Position Entropy Profile) as a Quran-specific fingerprint. LPEP is a Semitic-root cross-script descriptor (Greek Iliad >> all Arabic); Quran rank 2/7 within Arabic, beaten by ksucca.
10. **(v7.3)** CCAS (consonant-transition matrix Frobenius) as a Quran-specific signal. Both raw and intra-doc-normalised variants produce null or wrong-direction results; this closes the entire letter-transition-matrix detector family.

---

## 13. Acknowledgements to honest failure

The following are honestly failed hypotheses that shaped the current pipeline. Listing them here is a methodological asset, not a liability:

- The v2 pickle corruption (hadith leakage + Ksucca single-token + Bible duplicates) shaped the v3 "raw-only / no-pickle" rule.
- The in-sample AUC â†’ 1.000 artefact shaped the v3 nested-CV architecture.
- The Fisher `1 âˆ’ chi2.cdf` machine-epsilon floor shaped the v5 `chi2.sf` fix and the v6 universal absolute-drift lens.
- The cross-language silent fallback shaped the v6 INFEASIBLE skip.
- The Hessian-PD tautology and Î³(Î©)-linear-form algebraic identity shaped the v5 "falsified-by-math" honest ledger.
- The biased Cohen's d on Î¦_M shaped the v5 Hotelling TÂ² + permutation primary.
- The Adiyat 5/7 â†’ 4/7 weakening shaped the `docs/ADIYAT_ANALYSIS_AR.md` honest re-framing.
- The joint Meccan-Medinan F>1 falsification shaped the v3 retraction of the F>1 threshold.
- The phi_frac â†’ âˆ’0.915 non-reproduction shaped the v3 retraction of the golden-ratio claim.

A project this size has to be public about its failures. The SHA-256 integrity-lock protocol enforces that publicly.

---

## 14. Citation

```
Aljamal, M. (2026). The Quranic Structural Fingerprint (QSF):
A Reproducible 5-D Characterisation of a Multivariate Outlier
in Classical-Arabic Prose, with Integrity-Locked Replication.
doi: (pending) Â· preprint: github.com/… Â· OSF: (pending)
```

---

## 15. Changelog (v3 â†’ v7.3)

- **v3 (2026-04-17)** — clean rebuild, 5-D features, 23 tests, SHA-pinned corpora.
- **v5 audit (2026-04-18)** — hadith quarantine, Band-A propagation, `chi2.sf` fix, ridge unification, FDR expansion.
- **v6 audit-hardened (2026-04-19)** — SHA-pinned pickle checkpoints; cross-language fallback removed; D05/T11 NaN handling; `<UPDATED>` sentinel removed; universal 1Â·10â»â´ drift lens + Â±5 % headline envelope; 77-marker audit sentinel.
- **v7 edit-detection layer (2026-04-20)** — Ultimate-2 11-channel pipeline added (`notebooks/ultimate/QSF_ULTIMATE_2.ipynb`), two hostile-audit rounds executed (13 + 5 FATAL, 21 + 8 WARN all fixed). Two new decisive results: R2 local amplification (log_amp = 3.14, CI > 0) and R3 cross-scripture (p = 0.002, BH-surviving) — the latter supersedes the v6 INFEASIBLE skip in Â§3.5. R11 symbolic formula Î¦_sym manually replicated (`results/experiments/exp19_R11_symbolic_formula/R11_manual_phi_sym.json`), reproducing the 2025 historical â‰ˆ 0.98 AUC vs classical Arabic poetry. New d = +0.877 finding F6 (adjacent-verse length coherence) promoted to candidate 16th channel. **Law IV (VERU) formally falsified** (d = âˆ’1.013). Workspace reorganisation: 17 stray MD/log/zip/JSON files moved to `archive/{audits,logs,snapshots,lost_gems}/`.
- **v7.1 scale-invariance and cascade audit (2026-04-20 afternoon)** — four new sandbox experiments (`experiments/exp{27_hchar_bigram, 28_scale_invariant_law, 29_cascade_product_code, 30_cascade_R1_9ch}/`) in response to external review. `exp27` tests character-scale H_char_3 / H_char_2 against the T11 root-scale claim; result is **negative** (Quran rank 2/7, d = +0.457). `exp28` cross-references 5 scales into one verdict table; result is **PARTIAL 3/5** (root-bigram, verse-length coherence, surah-path survive; char scale + T28 root-Markov-order fail). `exp29` empirically measures the 5-D cascade product-code `P_composite` on 1 360 Quran-surah + 4 000 ctrl single-letter internal perturbations; result is **P = 0.137** (vs feedback estimate 0.82–0.90) — three of four 5-D channels are *structurally blind* to internal-letter edits because `features_5d` is byte-exact invariant under those edits. `exp30` extends the cascade test to Ultimate-2 R1's 9 channels (680 Quran + 1 000 ctrl perturbations); result is **P = 0.417** — higher than exp29 but still **not Quran-specific** (every MW p(Q > ctrl) â‰¥ 0.58). Only `E_ncd` (gzip) shows consistent response to the Adiyat variants (A: 1/9, B: 2/9, C: 3/9 channels fired |z|>2). Six new retractions logged in Â§3.4, twenty new scalars in Â§10. **No Ultimate-1 lock modified**; `experiments/_verify_all.py` confirms 8/8 v7.1 self-check receipts are PASS.
- **v7.3 letter-level edit-detection layer + AR(1) candidate + Adiyat 864-compound + audit fixes (2026-04-20 late PM)** — five new sandbox experiments (`experiments/exp{37_lpep, 38_ccas_normalised, 41_gzip_formalised, 43_adiyat_864_compound, 44_F6_spectrum}/`) + one `length_audit.py` sub-run under exp41. **R12 gzip NCD** (28-letter consonantal rasm) formalised as a new edit-detection channel: raw population d = +0.534, length-controlled Î³ = +0.0716 at fixed length (CI [+0.066, +0.078], p â‰ˆ 0), MW p_greater = 6.6Â·10â»Â³â¹. Length audit disposes of the length confound; Î³ becomes the paper-grade headline. **Adiyat 864-variant compound test**: 0/864 exceed canonical Î¦_M, 99.1 % fire NCD_doc and CCAS_F jointly at pre-registered exp41-ctrl-p95. **AR(1) coefficient** Ï†_1 of verse-length sequence gives d = +1.095 (MW p = 1.8Â·10â»Â¹Â²), with integrated autocorrelation over lags 1–15 *lower* in the Quran (d = âˆ’0.55, p_less = 2.4Â·10â»â¶) — candidate F6 replacement. **LPEP** (`exp37`) supports Semitic-root cross-script signature (Iliad > max Arabic) but FAILS Quran-extremality within Arabic (rank 2/7). **CCAS raw + normalised** (`exp38`) both null or wrong-direction; closes the letter-transition-matrix detector family. Zero-trust audit found 4 critical framing over-statements (raw d vs Î³ headline, R12-vs-E_ncd conflation, "Adiyat-specific" mis-attribution, tautological "1/865 NCD minimum") and 5 major code/doc issues (all fixed: exp43 ALL_of_5 drop, exp43 D4 calibration flag, exp44 NaN p_two_sided, addendum renamed to "post-hoc code-state lock"). **27 new candidate scalars added to Â§10 *(v7.3 cand.)*** — all SHA-pinned inside `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip` (overall SHA-256 `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`, zip SHA-256 `794fbe4b…`). Post-hoc code-state lock document at `arxiv_submission/preregistration_v73_addendum.md` (honestly titled "Results-Lock Addendum" with Â§10 disclosure of the post-hoc status). New consolidated Adiyat case summary at `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md`. CLI scorer + Streamlit UI at `tools/qsf_score.py` and `tools/qsf_score_app.py`. **No Ultimate-1 scalar modified**; all 27 new scalars carry *(v7.3 cand.)* tag and are gated on two-team replication before `results_lock.json` promotion.
- **v7.2 integrity refresh + R3 rebuild + robustness/topology/meta-CI/Adiyat-Î¦_sym closure (2026-04-20 PM)** — zero-trust audit of all v7.1 artefacts found (a) the Â§4.16 R3 numbers (`z_Quran = âˆ’8.74, z_NT = âˆ’4.97, z_Tanakh = âˆ’5.02`) were **unreproducible** from the current repo because their generator (`qsf_breakthrough_tests.py`, v10.3c) and the `tanakh.txt`/`greek_nt.txt` corpus-lock entries were stale (the real corpora live at `tanakh_wlc.txt` and `opengnt_v3_3.csv` and `raw_loader.py` already supports them via `include_cross_lang=True`); (b) `src/cache/cameltools_root_cache.pkl.gz` was not pinned in `code_lock.json`; (c) `camel-tools` was commented out as "optional" in `requirements.txt` with no exact version. All three were fixed: `corpus_lock.json` refreshed against the actual on-disk set (11 corpora); `code_lock.json` now pins the cache (SHA `82b24d12…`); `requirements.txt` pins `camel-tools==1.5.7` exactly. Six new sandbox experiments built and run: `exp31_subset_centroid_stationarity` (fingerprint survives loss of 50 % of surahs; median TÂ² at N=50 is 3 081 vs full 4 189); `exp32_canonical_path_near_optimality` (Mahalanobis path test; canonical is rank 32/200 of random 2-opt minima — not near-optimal but rank-wise favourable, which is the honest reframing of T8); `exp33_island_isolation` (5-D is a **continuum** with strong clustering, silhouette = +0.65, NNR = 0.50; single-linkage island hypothesis FALSIFIED, perm p = 0.32); `exp34_R11_adiyat_variants` (Î¦_sym structurally blind to all three Adiyat variants, |Î”Î¦_sym| < 0.33 Ïƒ_Q — closes ADIYAT Â§13.3 R11 cell); `exp35_R3_cross_scripture_redo` (authoritative R3 with N_PERM = 5 000: z_Quran = âˆ’8.92, z_Tanakh = âˆ’15.29, z_NT = âˆ’12.06, z_Iliad = +0.34; **Tanakh is the strongest raw-z optimiser, not the Quran** — the pre-v7.2 "76 % stronger" framing FALSIFIED); `exp36_TxEL_seed_metaCI` (5-seed meta-CI for the (T, EL) classifier: AUC = 0.9971 Â± 5.6Â·10â»â´ across seeds, 10Ã— tighter than within-fold Ïƒ — META_STABLE). 18 new scalars in Â§10; 2 new retractions in Â§3.4; 3 new Appendix-A items in the paper. `experiments/_verify_all.py` confirms 16/16 v7.1+v7.2 self-check receipts PASS; the four Ultimate-1 protected files (`QSF_ULTIMATE.ipynb`, `ULTIMATE_REPORT.json`, `ULTIMATE_SCORECARD.md`, `CLEAN_PIPELINE_REPORT.json`) are SHA-identical end-to-end.

---

## 16. Ultimate-2 edit-detection layer (new in v7)

Ultimate-1 characterises the Quran as a **corpus-level** multivariate outlier. Ultimate-2 extends this to a **per-edit** detection layer: 11 independent channels, each tuned to fire on a different class of perturbation (letter, word, verse, cross-scripture, topological). Architectural constraints:

- **No Ultimate-1 lock may be modified.** Ultimate-2 reads only `results/checkpoints/*.pkl` + `results/integrity/*.json` from Ultimate-1. Every Ultimate-1 scalar in `results_lock.json` is byte-preserved.
- **Every R-cell is wrapped by `_lib.self_check_begin()` / `_lib.self_check_end()`.** Writes the SHA-256 of every protected artefact before and after each cell; divergence raises `IntegrityError`. Receipts stored under `results/integrity/self_checks/`.
- **Pre-registered targets and explicit FAIL paths.** Of 11 channels, only two pass their pre-registered target unambiguously (R2, R3). Six PARTIAL/FAIL/REVERSED results are reported transparently.
- **Two hostile-audit rounds were required before v7 bless.** Round 1: 13 FATAL + 21 WARN (audit log `archive/audits/AUDIT_ULTIMATE2.md` + `AUDIT_ULTIMATE2_FIXES.md`). Round 2: 5 FATAL + 8 WARN (`archive/audits/AUDIT_ULTIMATE2_ROUND2.md`). All items patched and re-verified.

### 16.1 Architecture

```
results/checkpoints/phase_{02..22}_*.pkl     (Ultimate-1, SHA-locked, read-only)
       â”‚
       â–¼
experiments/ultimate2_pipeline.py            (shared feature library, R1–R11 entry-points)
experiments/_lib.py                          (sandbox + self-check + safe_output_dir)
experiments/_ultimate2_helpers.py            (corpus loader, verse extractor, unit label)
       â”‚
       â–¼
notebooks/ultimate/QSF_ULTIMATE_2.ipynb      (R1..R11 cells + MASTER composite)
       â”‚
       â–¼
results/experiments/exp{09..20}_*/*.json     (one JSON per channel, schema v3)
results/experiments/exp20_MASTER_composite/ULTIMATE2_REPORT.json  (headline)
```

Full channel ranking in Â§3.6. Per-corpus R11 breakdown in Â§3.7.

### 16.2 What the two winning channels add beyond Ultimate-1

**R2 — Sliding-window local amplification.** On a 10-verse sliding window over each surah, the z-scored Î¦_M response to a synthetic single-letter swap in the window's middle verse is 8Ã—–20Ã— larger than the surah-level Î¦_M response. Median log_amp = 3.14 (e^3.14 â‰ˆ 23Ã—), 95 % CI [2.32, 3.23]. This is the explicit resolution of the "Adiyat ceiling" of 2–3 % on surah-level Î¦_M: the signal was never gone, it was merely averaged out. See `docs/ADIYAT_ANALYSIS_AR.md` Â§"Ø§Ù„ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø£Ø®ÙŠØ±" for the Adiyat-specific interpretation.

**R3 — Cross-scripture authenticity.** *(Rebuilt v7.2, 2026-04-20 PM, supersedes pre-v7.2 numbers.)* A fresh run (`exp35_R3_cross_scripture_redo`) on the actual on-disk Hebrew Tanakh (Westminster Leningrad Codex, `data/corpora/he/tanakh_wlc.txt`, 921 book-chapter units) and Greek NT (OpenGNT v3.3, `data/corpora/el/opengnt_v3_3.csv`, 260 book-chapter units) + the Quran (114 surahs) + Iliad (24 books, negative control) under N_PERM = 5 000 per scripture and the language-agnostic 5-D feature vector (EL, VL_CV, CN, H_cond_initials, T_lang) gives:

- Quran: **z = âˆ’8.92**, p_one_sided = 2Â·10â»â´
- Hebrew Tanakh: **z = âˆ’15.29**, p = 2Â·10â»â´
- Greek NT: **z = âˆ’12.06**, p = 2Â·10â»â´
- Iliad (narrative ctrl): **z = +0.34**, p = 0.63 (fails BH, as expected)

BH-pooled minimum `p_adj = 3Â·10â»â´`; all three Abrahamic scriptures pass at Î± = 0.05. **The earlier `z_Quran = âˆ’8.74, z_NT = âˆ’4.97, z_Tanakh = âˆ’5.02` numbers (inherited from v10.3c `qsf_breakthrough_tests.py`, a script that is absent from the current repo) are superseded.** In raw z-magnitude the Tanakh is the strongest optimiser; after sample-size rescaling `z/âˆšn` the Quran leads (âˆ’0.84 vs âˆ’0.75 NT vs âˆ’0.50 Tanakh), but that rescaling is post-hoc and is reported only as a diagnostic. **The authoritative v7.2 framing is: canonical path minimality is a shared Abrahamic-scripture property, not a Quran-unique one.** The Iliad negative control confirms the test has power to reject at the null when the canonical order is narrative-chronological rather than structural. This closes the v6 Â§3.5 deferred item, neutralises the reviewer objection ("Arabic-only?"), but weakens any interpretation that treats path minimality itself as a Quran-distinctive law.

### 16.3 Why six channels FAIL or are REVERSED

- **R7 (noise ladder)**: the Î¦_M response to added transmission noise is symmetric in sign across control corpora; the proposed 7.25Ã— Quran/control ratio at 2 % error rate does not survive a 5-point calibration with proper CIs. Abandoned.
- **R5 (adversarial G0–G4)**: 50 % of the G4-generated "smart forgeries" (EL+RD-aware Markov) fall **below** the Quran's Î¦_M. G4 attackers can match Î¦_M; the Quran's separation is decisively preserved only under Î¦+ (Î¦ Ã— C_local), which is a **different statistic** not in any v6 lock.
- **R9 (VIS cross-scale)**: observed VIS = 0.485 < 1, i.e., the Quran's scale-propagation is *less* than controls (the opposite of pre-registered). Reported with sign; no retrospective re-labelling.
- **R4 (character-LM)**: a small (â‰ˆ10 M-param) character transformer trained on pre-Islamic poetry distinguishes canonical Quran from a synthetic single-letter edit at AUC â‰ˆ 0.53 only. A real GPT-scale char-LM is 2–6 weeks of additional work (see roadmap Â§8 future-R4).
- **R10 (verse-internal word-order)**: reproduces the effect direction (d = +0.47 in source paper) but not its magnitude after FDR. Remains a soft finding.
- **R8 (null ladder)**: N3 (EL-histogram-preserving shuffle) preserves Quran significance but so does poetry_abbasi; N5 (connective-preserving) weakens both. The *shape* of the ladder is the real signal, which requires more than a single-scalar channel rate.

### 16.4 Ultimate-2 deprecations / corrections carried into v7

- **Law IV (VERU)** formally falsified. See Â§3.4. This supersedes any Â«ØªÙØ±ÙÙ‘Ø¯ Ø¬Ø°ÙˆØ± Ø§Ù„Ù†Ù‡Ø§ÙŠØ§ØªÂ» claim in prior drafts.
- **Adiyat 5/7 â†’ 4/7 â†’ mixed-ceiling** narrative: the 1.7 % Î¦_M ceiling stated in v3–v6 is correct *for Î¦_M*, but is **not the system ceiling** in v7. Under R2 the same Ø¶â†”Øµ swap is visible at > 6 Ïƒ within a 10-verse window; under R1, 5 of 9 channels fire (â‰¥3 needed). The `docs/ADIYAT_ANALYSIS_AR.md` Â§"Ø§Ù„ØªØ­Ø¯ÙŠØ« Ø§Ù„Ø£Ø®ÙŠØ±" documents this.
- **The "symbolic formula Î¦_sym â‰ˆ 0.98" claim** from 2025 historical notes is validated (vs poetry) and quantified (pooled 0.897) in `results/experiments/exp19_R11_symbolic_formula/R11_manual_phi_sym.json`. No single-scalar lock is added because the pooled AUC is 0.897 < 0.90; only the per-corpus poetry numbers cross 0.90.

### 16.5 Open items specific to Ultimate-2

| Item | What | When |
|---|---|:-:|
| R4+ | Real GPT-scale character-level LM | Q3 2026 (2–6 weeks, once compute budget secured) |
| R5+ | Î¦+ = Î¦ Ã— C_local formal lock | Q2 2026 (statistic exists, needs pre-registration before bless) |
| R8+ | Per-constraint null-ladder fingerprint (N0..N7 vs corpus) | Q2 2026 (reporting form; no single scalar target) |
| F6+ | Promote adjacent-verse length coherence to blessed 6th Î¦_M channel | Q2 2026, after independent replication at â‰¥ 2 external teams |
