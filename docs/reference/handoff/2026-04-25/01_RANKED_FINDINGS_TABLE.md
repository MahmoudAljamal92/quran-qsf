# 01 — Master Ranked Findings Table

> ⚠ **v7.9-cand SUPERSESSION NOTICE (2026-04-28 evening — patch H V3, H39 envelope replication COMPLETE)**: H39 (`exp95f_short_envelope_replication`) ran on the SHORT receipt and yielded **`FAIL_envelope_phase_boundary`** (FN07): correlation passes at full V1 strength (r = −0.8519) but phase boundary fails at one surah — **Q:055 Al-Rahman**. No F-number opened; the V1 envelope remains exploratory only. Phase 2 results unchanged.
>
> ⚠ **Earlier (2026-04-28 — patch H V2, Phase 2 COMPLETE)**: This snapshot is frozen at 2026-04-25 evening (pre-v7.9-cand sprint). For the current findings record, **defer to** `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` **§4.40-§4.46** (including §4.46 Φ_master + robust OOS Bayes-factor floor + F57 PASS meta-finding), the **MASTER_DASHBOARD.md** single-page consolidation, the **OSF_DEPOSIT.md** formal pre-registration package, and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md` **patches B through H V3**. Tier A's ordering is unchanged but **eighteen** new findings (F44–F58 in `RANKED_FINDINGS.md` v2.4 + F57 PASS) would slot in, plus 7 failed-null pre-registrations FN01–FN07 in Category K and **6** retractions R51–R56 in Category L of `RETRACTIONS_REGISTRY.md`.
>
> **Patch H pre-V2 (Φ_master corrected master scalar, 2026-04-27 afternoon)** — F58 + H50 + F57 partial + OSF deposit + PAPER §4.46
> - **F58 (`exp96a_phi_master`, H49)** — **Φ_master(quran whole 114) = 1,862.31 nats**, log₁₀ BF = 808.85 (BF ≈ 10⁸⁰⁹), Quran rank 1 of 7, ratio 965× to next-ranked. Per-term: T1 = 1842.73 (½·T² with whole-Quran T² = 3,685.45 from expP7), T2 = 2.64 (p_max=0.501), T3 = 0.67 (EL_AUC=0.981), T4 = 0.80 (EL_frag/median), **T5 = 12.12 (Clopper-Pearson 95% upper on 0/548,796 — honest, NOT the previous ad-hoc 100)**, T6 = 3.35 (5-riwayat sum). PASS_phi_master_locked. PREREG hash `ab816b3e81bd1bfc7be0bb349ee4e3e49b7db56f288ac7c792ecc861d847db3e`. The earlier internal `I² = 6.22` framing is rejected (multiplicative weights + fiat 100-nat constant broke probabilistic interpretation).
> - **`exp96b_bayes_factor` (H50)** — **PASS_robust_oos_locked**. LOCO-min = 1,634.49 nats (BF ≥ 10⁷⁰⁹ even when poetry_abbasi held out, halving Σ rank), LOCO-median = 1,846.26, LOCO-max = 1,990.97. Bootstrap (n=500): p05 = 1,759.72, p50 = 1,870.77, p95 = 1,975.03. Both well above 1,500-nat floor. PREREG hash `39d6d977d964e1d4c1319edbc62fba9826ea41f0937206d98d4ff25a26af150a`. **Defeats the circularity objection materially**: Σ in T1 is from 6 controls (Quran held out), then a 7th control held out per LOCO split.
> - **F57 PASS (`exp96c_F57_meta`, H51)** — **PASS_F57_meta_finding** (updated 2026-04-28 after Phase 2 completion). 4 of 6 Quran self-descriptions confirmed: C1 (54:17) via `expE16_lc2_signature`; C2 (2:23) via `exp95j_bigram_shift_universal` theorem-grade F55; C3 (15:9) via `expP15_riwayat_invariance` 5-riwayat AUC; **C6 (41:42) via `exp99_adversarial_complexity`** (H54 PASS_H54_zero_joint: 0/1,000,000 Markov-3 forgeries passed joint gate; 13.82 nats). **C4 (11:1) FAILED 2 op-tests** (FN03 `exp98` + FN05 `exp100`); **C5 (39:23) FAILED 2 op-tests** (FN04 `exp97` + FN06 `exp101`); both reclassified as not-yet-operationalised. `P_null(S ≥ 4 | Bin(6, 1/7)) = 0.0049` (significant at 1%). Phase 2 complete; no pending claims remain.
> - **PAPER §4.46 added** — 6 sub-sections: motivation; corrected formula (no ad-hoc constants); headline + robustness tables; F57 meta-finding; why this defeats circularity; bottom-line scientific sentence.
> - **MASTER_DASHBOARD.md** — single-page consolidation of every locked numerical claim. Reads like a scoreboard.
> - **OSF_DEPOSIT.md** — formal OSF pre-registration package. Manual upload required by user.
> - **Whole-Quran scope locked** — user mandate (2026-04-27 13:55 UTC+02:00) that all new Φ_master / Phase 2 / Phase 3 experiments use the full 114-surah Quran. No band-A / band-B / band-C restrictions.
>
> **Patch G post-V1-vi (Bayesian joint-extremum likelihood scaffold, 2026-04-27 morning)** — H48 DOUBLE-FAIL + R56 + honest sprint closure
> - **H48 (`exp95o_joint_extremum_likelihood`)** — user-asked closing question: *"is there anything more to advance the experiment further or prove the Quran's uniqueness — beyond science?"*. The cleanest single-step calculation: joint per-dimension extremum across 10-feature panel (5-D Φ_M + 5-D Ψ_L) with 100,000 unit-level permutations for correlation correction. Verdict: **DOUBLE-FAIL**. (1) Pre-reg verdict `FAIL_audit_el_rate_quran_drift` (band-A vs MIN_VERSES_PER_UNIT=2 mismatch in PREREG audit hook; actual el_rate(quran) = 0.7063 vs locked 0.7271, drift 0.0208). Companion audit `p_max(quran) ≈ 0.501` PASSED (drift 4·10⁻⁵). (2) Substantive numbers (independent of audit): Quran S_obs = **4 of 10**; per-corpus extremum count: ksucca 7, **quran 4**, poetry_jahili 3, poetry_islami 2, poetry_abbasi 2, hindawi 2, arabic_bible 0. Naive null `P(S ≥ 4 | Bin(10, 2/7))` = 0.313; permutation null = 1.000.
> - **R56 added** (`RETRACTIONS_REGISTRY.md` Category L) — joint per-dimension extremum claim retracted. PREREG hash `31eaf358d10a500405348a65e29dc52245003e923d29426628a878e591fbc660` matched.
> - **Honest substructure** (the interesting refinement): Quran's 4 extrema are *all* on rhyme / verse-structural axes (el_rate=rank 1, cn_rate=rank 1, Gini=rank 1, h_el=rank 7); **0** on rhyme-blind letter-level axes (H_2, H_3, gzip_ratio, log10_nb all at rank 4–5). Mechanistically consistent with R55 (letter-level fragility Quran rank 6 of 7) and Gate 1 AUC = 0.998 (rhyme-aware multivariate hyperplane). **Quran-distinctiveness lives at the rhyme / verse-structural scale, NOT at the letter-level scale.**
> - **§4.45 added to `PAPER.md`** — 6 sub-sections: motivation, pre-reg verdict, substantive numbers, honest substructure, locked-claim impact table, bottom-line defensible-scientific-sentence (§4.45.6).
> - **v7.9-cand sprint at honest closure**: 56 positive findings + 56 retractions + 2 failed-null pre-regs. The scientific question of Quran-distinctiveness within Arabic is *closed* at the rhyme / verse-structural scale. Any further advance moves into Bayesian-inference-under-priors (philosophical) or metaphysical territory — outside the project's scope.
>
> **Patch G post-V1-v (MSFC sub-gate 2D letter-level rescue, 2026-04-27 morning)** — H47 FAIL + R55
> - **H47 (`exp95n_msfc_letter_level_fragility`)** verdict `FAIL_quran_not_top_1`. Letter-level 5-D vector `Ψ_L = [H_2, H_3, Gini, gzip_ratio, log10_n_distinct_bigrams]` resolves the H46 structural blind spot (zero_dm_fraction = 0 for all 7 corpora — features DO respond to interior consonant substitutions), but Quran ranks **6 of 7** by median Mahalanobis edit-fragility: poetry_islami (0.1641), poetry_abbasi (0.1357), poetry_jahili (0.1163), hindawi (0.0928), arabic_bible (0.0678), **quran (0.0623)**, ksucca (0.0224). **Mechanism**: Quran's smallest cov eigenvalue (3.14·10⁻⁴) is the *largest* among 7 corpora — Quran's per-surah letter-level features are MORE dispersed than poetry units within their corpora; poetry's tighter clustering amplifies Mahalanobis displacement per edit. PREREG hash `3d5cfcc94d215c3fc992647108a025de6550df8e86ffa60085fdf4c702ed8eaf` matched.
> - **R55 added** (`RETRACTIONS_REGISTRY.md` Category L) — letter-level multivariate fingerprint Quran-amplification claim retracted. The MSFC sub-gate 2D fails under both candidate feature sets tested (H46 canonical 5-D blocked structurally by interior-blind features; H47 letter-level 5-D rejected by ranking). The MSFC's Quran-distinctive backbone is empirically settled: **Gate 1 multivariate fingerprint** (T²=3,557, AUC=0.998) **+ Gate 2C EL-fragility** (F56, 2.04×) only.
> - **`PAPER.md §4.44.4` extended** with H47 ranking table + mechanism explanation; §4.44.5 audit trail updated.
>
> **Patch G post-V1-iv (MSFC sub-gate amplification audit, 2026-04-27 morning)** — H45 PASSES + R54 added
> - **F56 added** (row 56 of `RANKED_FINDINGS.md` v1.9) — "MSFC sub-gate 2C: Quran-amplified EL-fragility under verse-final 1-letter substitutions", strength 86 %, paper-grade. `exp95l_msfc_el_fragility` (H45, PREREG hash `49cea95bade2dea3dd79c1cf29f5d9c98545d7d50b2cebf2ff44dc6f6debf965`) verdict **`PASS_quran_strict_max`**. **Per-corpus ranking** (descending): (1) **Quran 0.5009** (`p_max(ن)=0.5010`, n_verses=6,236), (2) poetry_islami 0.2453, (3) ksucca 0.2312, (4) arabic_bible 0.2259, (5) poetry_jahili 0.2243, (6) poetry_abbasi 0.2142, (7) hindawi 0.1895. **Margin ratio Quran/next = 2.042×**. Audit `p_max(quran)=0.5010` matches `PAPER §4.5` locked target. Empirical confirmation on 10,000 random verse-final substitutions per corpus. Wall-time 3.6 s. **Replaces the falsified Gate 2A amplification claim (H44 / R54)** as the Quran-distinctive amplification layer in the MSFC.
> - **R54 added** (`RETRACTIONS_REGISTRY.md` Category L) — H44 (`exp95k_msfc_amplification`) `FAIL_quran_not_top_1`. Quran rank **4 of 7** on Δ_bigram safety margin (ksucca 427, hindawi 100, arabic_bible 84, **quran 55**, poetry_jahili 39, poetry_islami 11, poetry_abbasi 11). The bigram-shift safety margin is universal mathematics, not Quran-distinctive. **F55 detector receipt unaffected** (recall = 1.000 by theorem; FPR = 0.000 vs Arabic peers).
> - **H46 BLOCKED by structural insensitivity** — `exp95m_msfc_phim_fragility` `FAIL_audit_features_drift` AND all 7 corpora produced `phim_fragility = 0.0000` because canonical 5-D Φ_M features are sensitive only to verse-final letter changes and verse-first-word changes; > 96 % of random consonant positions are mid-verse-and-mid-word. Consistent with §4.20 / R5. Documented as **design constraint, NOT a retraction**.
> - **§4.44 added to `PAPER.md`** — consolidated MSFC architecture (Gate 1 multivariate membership, locked AUC 0.998 + Gate 2C EL-fragility, PASS, Quran-amplified 2.04×), with explicit "what the cascade claims and does not claim" framing.
>
> **Patch G post-V1-iii (rescue paths B + C executed 2026-04-26 night)** — F55 universal symbolic detector PASSES
> - **F55 added** (row 55 of `RANKED_FINDINGS.md` v1.8) — "Universal symbolic single-letter forgery detection by frozen-τ bigram-shift", strength 86 %, paper-grade. `exp95j_bigram_shift_universal` (H43, PREREG hash `a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd`) verdict **`PASS_universal_perfect_recall_zero_fpr`**. **Headline numbers**: aggregate recall = **1.000** (139,266 / 139,266 V1 variants fire across all 114 surahs); aggregate FPR = **0.000** (0 / 548,796 canon-peer pairs fire); per-surah recall and FPR are 1.000 / 0.000 on every surah; min peer Δ across full pool = 73.5 ≫ frozen τ = 2.0. Detector: `Δ_bigram(canon, candidate) = ‖hist_2(canon) − hist_2(candidate)‖₁ / 2`; fire iff `0 < Δ ≤ τ` with **τ = 2.0 derived from analytic theorem** (proven in `PAPER.md §4.43.2`: any single-letter substitution has `Δ_bigram ≤ 2`). Wall-time: 311 s on 1 core. **F55 does NOT un-retract R53** — F55 is a fundamentally different detector class (symbolic bigram, no compression, no calibration). The compression-based F53 / F54 thread is a separate research question about NCD's coverage envelope.
> - **Path B (`exp95h_asymmetric_detector`, H41)** — `FAIL_no_clean_split_p90`. 108-rule asymmetric grid `{K1, K2, K3, K4} × {gzip, bz2, lzma, zstd}`, best rule (`L0=138`, `D_short=K2`, `D_long=gzip_or_lzma`) at `min_per_surah=0.0000` and aggregate=0.270. **Documented negative result**: no length-band split rescues universal NCD detection at fixed locked-`exp95c` τ thresholds.
> - **Path C-calibrated (`exp95i_bigram_shift_detector`, H42)** — `FAIL_audit_hook_violated`. Q:108 (62 letters) has zero peers in the `[31, 93]` length-match window; the per-surah ctrl-coverage audit hook (locked in PREREG) fired correctly. Substantive numbers (had the audit not blocked): variant Δ ∈ [1.0, 2.0] across all 139,266 V1 variants; matched-peer Δ ≥ 58.5 across all 5,589 matched pairs. Pre-reg discipline honoured; design space pivoted to path C-strict (frozen-τ, calibration-free) above.
>
> **Patch G post-V1 (`exp95e` V1-scope run completed 2026-04-26 night)**
> - **F54 FALSIFIED** — `exp95e_full_114_consensus_universal` V1 scope, 139,266 variants, runtime 3 287 s on 6 workers, verdict **`FAIL_per_surah_floor`**. Aggregate K=2 = 0.190 (target ≥ 0.999); 70 / 114 surahs at K=2 = 0; only 8 / 114 surahs at K=2 ≥ 0.999 (Q:093, Q:100, Q:101, Q:102, Q:103, Q:104, Q:108, Q:112 — all short late-Meccan, `total_letters_28 ≤ 188`). ctrl-null FPR K=2 = 0.0248 (≤ 0.05 ✓); embedded Q:100 regression K=2 = 1.000, gzip-solo = 0.9907 (matches `exp94`/`exp95c` exactly ✓). bz2-solo recall = 0.000 across all 114 surahs (τ_bz2 inherited from `exp95c` is too strict to fire on V1 variants under this corpus; K=2 unaffected). **F54 row of `RANKED_FINDINGS.md` flipped from PENDING → ❌ FALSIFIED**.
> - **R53 added** to `RETRACTIONS_REGISTRY.md` Category L: only the universal-extrapolation hypothesis (H37 / F54) is retracted; **F53's Q:100 closure (§4.42) stands** unchanged.
> - **Mechanistic envelope (post-hoc observation, NOT a claim)**: across 114 surahs, `log10(total_letters_28) → K=2 recall` Pearson r = **−0.85**, Spearman ρ = −0.85; phase boundary `total_letters_28 ≤ 188` perfect / `≥ 873` zero. Mechanism: bz2 / lzma / zstd dictionary windows absorb V1 changes against long surah canons.
> - **H39 pre-registered + replication in flight**: `experiments/exp95f_short_envelope_replication/PREREG.md` (SHA-256 `83a7b25ac69e703604a82be5c6f7c1d597ccd953f07df7f624ccc1c55d972a14`) locks the envelope claim **before** the SHORT receipt is opened; SHORT-scope re-run is in flight (≈ 355 K variants, ETA ~ 2–4 h). If H39 passes, the envelope is promoted to candidate finding F55; otherwise it stays as a single-corpus exploratory pattern only.
>
> **Patch G earlier (universal scaling + risk-vector audit, 2026-04-26 night)** *(historical context — superseded by patch G post-V1 above)*
> - **F54** (was PENDING) — universal scaling of F53 across all 114 surahs pre-registered as `exp95e_full_114_consensus_universal` (PREREG hash `ec14a1f6dcb81c3a54b0daeafa2b10f8707457ee4305de07d58ee7ede568e9a7`). V1 scope (≈ 145 K variants, 30 min – 2.5 h) is the headline. Verdict ladder: `FAIL_tau_drift` / `FAIL_q100_drift` / `FAIL_consensus_overfpr` / `FAIL_per_surah_floor` / `FAIL_aggregate_below_floor` / `PARTIAL_per_surah_99_aggregate_99` / `PASS_universal_999` / `PASS_universal_100`. **The V1 run fired branch 4 (`FAIL_per_surah_floor`); see patch G post-V1 above for verdict-anchored numbers.**
> - **R51** (Category L) — γ universality across compressor families (`exp103` `FAIL_not_universal`); CV_γ = 2.95; signs disagree across {gzip +0.072, bzip2 −0.048, zstd −0.029, brotli +0.087}. **F53 / F54 are unaffected** because K = 2 consensus is *designed for* compressor disagreement.
> - **R52** (Category L) — Ψ_oral 5/6 oral-tradition universality (`expX1` `NO_SUPPORT`); 0/5 non-Quran corpora produce Ψ in the loose pre-registered band [0.65, 1.00]; cross-corpus spread is two orders of magnitude.
> - **H38 (BLOCKED)** — cross-tradition F53 pre-registered at `experiments/expP4_F53_cross_tradition/PREREG.md` as a corpus-acquisition-blocked stub. **No claim about cross-tradition F53 universality is made by the v7.9 paper.**
> - **3-tool framing prelude** added to `PAPER.md §4.42`: EL alone (classification simplicity, AUC = 0.9971), 5-D Hotelling T² (separation magnitude, T² = 3 557 / CI [3 127, 4 313]), and F53 multi-compressor consensus (forensic integrity, recall ≥ 0.999) answer three distinct questions and should not be conflated. All three are scoped to **Quran-vs-Arabic-peers**; cross-tradition extensions are pre-registered futures (R09, R48, R52 already document what cross-tradition data has refuted at the per-feature level).
> - **Audit memo** `docs/reference/sprints/AUDIT_MEMO_2026-04-26_RISK_VECTORS.md` cross-checks every older experiment against three risk vectors (γ universality, cross-tradition uniqueness, T² band-A vs full); confirms zero downstream impact on standing claims.
>
> **Patches B / D / E / F (preserved from previous supersession notice)**:
>
> **Patch B (full-Quran extension)**
> - Full-Quran 5-D **T² = 3 685** — **bootstrap 95 % CI = [3 127, 4 313]** (median 3 693) per `expP12`; **band-A T² = 3 557 is INSIDE the CI**, so the two T² values are **statistically indistinguishable** (R50 reframe replaces patch B's "INCREASES" claim with "STABLE")
> - EL one-feature law **AUC = 0.9813** on all 114 surahs; **LOCO min AUC = 0.9796** (drop poetry_abbasi) per `expP13` → ROBUST_STRONG
>
> **Patch D (zero-trust audit corrections)**
> - Bible ن rate corrected 14.7 % → **7.53 %** (gap = 42.6 pp not 35.4 pp)
> - Brown joint p tightened 3.28·10⁻⁵ → **2.95·10⁻⁵** (conservative ρ=0.5 prior)
>
> **Patch E (quick-wins sprint)**
> - **F44** Pre-registered hadith N1: AUC = **0.9718**, MW p = 4.05·10⁻³² (`expP10`)
> - **F45** Brown empirical R: p_joint = **5.24·10⁻²⁷** (~11 OOM tighter than ρ=0.5 prior 1.41·10⁻¹⁶) (`expP11`)
> - **F46** Bootstrap T² CI [3 127, 4 313] → STABLE (triggers R50) (`expP12`)
> - **F47** LOCO EL min AUC = **0.9796** (`expP13`)
> - **F48** Cross-script clean dominance: 2.43× ratio for any-letter-of-any-kind (4.6× is for ن specifically) (`expP14`)
> - **F49** 5 riwayat all keep AUC ≥ 0.97; Warsh largest drift (`expP15`)
> - **F50** **Maqamat al-Hariri (Arabic saj') AUC = 0.9902, MW p = 2.4·10⁻³⁸** → QURAN_DISTINCT_FROM_SAJ — closes the highest-leverage external test (`expP16`)
> - **F51** Markov saj' adversarial mode 1 done: max EL = 0.20 (< 0.314 boundary); modes 2–4 RUNNING overnight (`expP17`)
> - **F52** Shannon-capacity i.i.d. floor for EL = 0.295 → Quran's structural rhyme excess = **+0.425** (`expP18`)
>
> **Patch F (multi-compressor consensus closure of Adiyat-864, 2026-04-26 night)**
> - **F53** K=2 multi-compressor consensus across {gzip-9, bz2-9, lzma-9, zstd-9} on Adiyat-864 (Q:100): recall = **864/864 = 1.000** at K=2 ctrl FPR = **0.0248** (half of gzip-only's 0.05); lzma-9 and zstd-9 each unilaterally close the gap. (`exp95c` PASS_consensus_100). Reframes finding #5 (Adiyat 864) from "ceiling 99.07 %" to "ceiling closed; gzip-only 99.07 % was a compressor-specific artefact"
> - **Robustness** (`exp95d` PARTIAL_seed_only): K=2 recall identical 1.000 across seeds {42, 137, 2024} on Q:100 (span = 0.000); cross-surah Q:099 al-Zalzalah recall = 998/999 = **0.998999** (one bāʾ↔wāw substitution at K=1, saved by gzip-solo and by K=1 any-compressor at FPR 0.177)
> - **FN01** (Category K, NOT a retraction): `exp95_phonetic_modulation` FAIL_ctrl_stratum_overfpr; phonetic-Hamming-modulated R12 dropped recall to 0.985 with stratum FPR overshoot
> - **FN02** (Category K, NOT a retraction): `exp95b_local_ncd_adiyat` FAIL_window_overfpr; 3-verse window-local NCD collapsed recall to 0.399 — useful negative datum: window-NCD's noise floor scales together with the 1-letter signal, so it is *strictly worse* than full-doc NCD for single-letter forensics on short surahs
>
> See `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PROGRESS.md` §1 for the post-sprint summary.

**Single ranked table** covering every scientifically meaningful finding in the QSF project, ordered by **strength to science (%)** combining the four 25-point axes (Stat × Rob × Gen × Pub) defined in `RANKED_FINDINGS.md §1`.

**Status legend**: ✅ PROVED+ (paper-grade, exceeds v2 baseline) · ✅ PROVED · ⚠ PARTIAL · 🔶 SUGGESTIVE · 💎 PENDING (lost gem) · ❌ FALSIFIED.

---

## Tier A — paper-grade, ready to ship (strength ≥ 86 %)

| Rank | Finding | Scalar | Strength % | Status | Submission package |
|--:|---|---|:--:|:--:|:--:|
| 1 | Classifier AUC (nested 5-fold CV, 5-D fingerprint `(EL, VL_CV, CN, H_cond, T)`) | **AUC = 0.998** | **93** | ✅ PROVED+ | P2/P3 |
| 2 | Φ_M Hotelling T² (Band-A: 68 Quran vs 2 509 Arabic ctrl) | **T² = 3 557**, perm p ≤ 5·10⁻³ (locked); **analytic F-tail log10 p = −480.25** (≈ 47σ-equivalent) | **92** | ✅ PROVED+ | P2 headline |
| 3 | (T, EL) sufficiency + LC3-70-U linear discriminant | `L = 0.5329·T + 4.1790·EL − 1.5221`, AUC = 0.9975, 99.15 % acc, 7/2 509 leaks (all `arabic_bible`); **EL alone AUC = 0.9971** | **92** | ✅ PROPOSITION (PARTIAL on strict Fisher gate) | P3 headline |
| 4 | LC2 — Cross-tradition R3 path-minimality (8 corpora) | Rigveda z = −18.93 (strongest), Tanakh z = −15.29, NT z = −12.06, Quran z = −8.92, Avestan z = −3.98, Pali_MN z = −3.47; Iliad control z = +0.34 fails as preregistered; BH min p = 3·10⁻⁴; **8/8 leave-one-out robust** | **88** | ✅ SUPPORT, LOO-ROBUST | P4 headline |
| 5 | R12 gzip NCD length-controlled residual | γ = +0.0716, 95 % CI [+0.066, +0.078], p ≈ 0; **28× single-edit Shannon-counting floor** | **90** | ✅ PAPER-GRADE (gzip-specific, retracted as universal) | P2 supplementary |
| 6 | Adiyat 864-variant compound detection (Surah 100, single-letter enumeration) | **99.1 %** fire at ctrl-p95 calibration; 0 / 864 exceed canonical Φ_M | **89** | ✅ PAPER-GRADE | Adiyat case study |
| 7 | Two-letter 72 900-variant enumeration (FAST mode) | **100 %** compound detection | **87** | ✅ PAPER-GRADE | Adiyat |
| 8 | Perturbation scale hierarchy `d(word) > d(verse) > d(letter)` | d(word) = 2.45, d(verse) = 1.77, d(letter) = 0.80 | **87** | ✅ PROVED (n = 1) | P2 |
| 9 | LOFO Φ_M robustness (pre-registered Test A) | min Cohen d = 5.26 across 6/6 family splits | **86** | ✅ PRE-REG PASS | P2 |
| 10 | R2 sliding-window amplification | log_amp_med = 3.14, 95 % CI [2.32, 3.23] | **86** | ✅ PRE-REG PASS | Adiyat |
| 11 | Bootstrap Ω stability (pre-registered Test C) | 100 % > 2.0, median = 10.0 | **86** | ✅ PRE-REG PASS+ | P2 |

## Tier B — solid, supplementary (strength 78–85 %)

| Rank | Finding | Scalar | Strength % | Status | Notes |
|--:|---|---|:--:|:--:|---|
| 12 | Quran H_unit_words = **0.9139** + 3-pass forensic survival (cross-tradition LC-Hurst, v7.8) | n = 114 surahs; H = 0.914; vs perm null z = +3.70, p = 2·10⁻⁴; descending-ceiling 1.007; linear-detrended H = 0.841 | **78** | ✅ 3-PASS FORENSIC | P2 supp. |
| 13 | AR(1) φ₁ per-surah (candidate 6th feature) | d = +1.095, MW p = 1.8·10⁻¹² | **84** | ⚠ candidate (rejected as 6th channel by per-dim-gain 0.84 < 1.0 gate) | P2 supp. |
| 14 | %T > 0 Quran-unique tension `T = H_cond − H_el` | Quran 39.7 % vs ctrl max 0.10 % → **397× ratio** | **83** | ✅ PROVED+ | P2 |
| 15 | D14 verse-internal word-order gap | Quran +5.80, 100 % canon-farther | **79** | ✅ PROVED+ | P2 supp. |
| 16 | Subset-centroid stationarity (N = 50) | T² = 3 081, drift 3.3 % vs full | **79** | ✅ PROVED | P2 supp. |
| 17 | 10-fold internal CV (D24/T12) | min d = 5.08, median = 6.89 | **77** | ✅ PROVED+ | P2 supp. |
| 18 | R3 path-minimality is the primary cross-tradition axis (PCA, v7.8) | PC1 captures 68.9 % of variance, R3 loading −0.71 dominates; Hurst is orthogonal (PC2, 30.4 %) | **70** | ✅ PROVED | P4 |

## Tier C — solid but narrower (strength 70–77 %)

| Rank | Finding | Scalar | Strength % | Status |
|--:|---|---|:--:|:--:|
| 19 | R11 Φ_sym AUC vs poetry | 0.976–0.987 per-poetry; 0.897 pooled | **76** | ✅ NEAR-PASS |
| 20 | Scale-free Fisher (D07) | −log10 p @ W=10 = 16.08 | **76** | ✅ PROVED |
| 21 | Terminal-position depth (T26) | d(−1) = 1.43, d(−2) = 2.40, d(−3) = 0.65 | **75** | ✅ PROVED+ |
| 22 | F6 length-coherence (candidate 6th, rejected) | d = +0.877, p = 1.4·10⁻¹¹; per-dim gain 0.54 < 1.0 | **74** | ⚠ univariate only |
| 23 | Canonical path minimality (D17/T8) | z = −3.96, 0/2 000 perms beat | **74** | ✅ PROVED |
| 24 | RD × EL composite product (D22) | 0.632 vs 0.179 next (3.5×) | **72** | ✅ PROVED+ |
| 25 | Adiyat A/B/C firings on R12 | z ∈ {+5.58, +5.58, +9.14} | **72** | ✅ PAPER narrow |
| 26 | EL rhyme rate (D03) | EL_q = **0.7074** (4.5× next), Band-A mean **statistically indistinguishable from 1/√2 = 0.7071** (jackknife/bootstrap CI [0.66, 0.75]; t = 0.014, p = 0.99) | **71** | ✅ PROVED |
| 27 | LC1 phonetic-distance → detection (`exp54`/M1_hamming) | best r = +0.929 (FULL mode, 114 surahs) | **70** | ✅ LAW_CONFIRMED |
| 28 | LC-Hurst 4-corpus narrow universal (Quran/Tanakh/NT/Rigveda, v7.8) | all 4 native-script religious-text orderings z > +3 vs corpus-specific perm null; detrended residual H > 0.78 | **65** | ✅ NARROW SUPPORT |

## Tier C-low — supplementary (strength 60–69 %)

| Rank | Finding | Scalar | Strength % | Status |
|--:|---|---|:--:|:--:|
| 29 | Verse-graph modularity (`exp48`+`exp49`, 6-D closed) | n_communities d = +0.937, modularity d = +0.672; **6-D T² = 3 823 < 4 269 gate → SIGNIFICANT BUT REDUNDANT** (5-D Φ_M already spans this axis) | **68** | ✅ replicates, redundant |
| 30 | I(EL; CN) corpus-level | 1.175 bits | **68** | ✅ RE-USABLE |
| 31 | Hurst DFA (Quran) | 0.901; v7.8 caveat: textbook H = 0.5 reference does NOT apply at standard chunk grid; corpus-specific perm null = 0.59 | **66** | ✅ LOCKED supp. |
| 32 | VL_CV anti-metric (D01) | d = 1.40 pool; 2.5 vs poetry; **floor = 0.1962 ≈ 1/√26** (provenance: 26 = MSA consonantal phonemes after subtracting hamza+alif) | **65** | ⚠ weaker vs v2; constant pinned |
| 33 | CN connective rate (D04) | 0.086, 2.5× next | **65** | ✅ PROVED |
| 34 | Emphatic-class edit detection (`exp46` FULL + `exp50` cross-corpus) | Quran 1.15 % vs poetry_abbasi 4.83 % vs poetry_jahili 9.50 %; **post-audit no-E7 normalisation: Quran 0.296 %, Abbasi 0.93 %, Jahili 1.97 % → H1_STRUCTURAL_ARABIC_BLINDNESS** (downgraded from H2_QURAN_SPECIFIC_IMMUNITY by 5×-threshold gate) | **64** | ⚠ qualitative only after E7 audit |
| 35 | Root bigram sufficiency H₃/H₂ (T11) | Quran 0.222 (#1 lowest of 7) | **62** | ✅ partial |
| 36 | Harakat channel capacity (E3/T23) | H(harakat ∣ rasm) = **1.964 bits** (Arabic-textology constant); reproduced in Hebrew + Greek at R ≈ 0.70 (3-corpus Abrahamic typology) | **71** | ✅ RE-USABLE |

## Tier D — partial / suggestive (strength 50–59 %)

| Rank | Finding | Scalar | Strength % | Status |
|--:|---|---|:--:|:--:|
| 37 | Phonetic-distance → detection (`exp47`/LC1) | best r = +0.747 (below pre-reg r ≥ 0.85) | **55** | 🔶 |
| 38 | Anti-repetition (Gem #2, *tabdil*) — historical d = −0.475 | re-audit `exp67`: d = +0.330 (sign reversed); per-corpus split: Quran d ≈ +1.0 vs poetry, d = −2.14 vs ksucca | **53** | ❌ retracted as written; reframable |
| 39 | R1 9-channel variant forensics | 50 % fire ≥ 3 ch (45× chance floor) | **51** | ⚠ PARTIAL |
| 40 | Multi-level Hurst ladder (Gem #4) | H_verse = 0.898 → H_delta = 0.811 → H_word = 0.652 (orig); **`exp96` v7.8 retracted: monotone shape shared by all 6 ctrl corpora** | **0 (retracted)** | ❌ R26 |

## Tier E — Tier-S "missed framings" (PASS but not yet packaged as their own paper)

These are findings that **already pass** but have not been written up as standalone results. From `OPPORTUNITY_TABLE_DETAIL.md` Tier S.

| ID | Finding | Scalar | Why missed |
|---|---|---|---|
| **S1** | Mushaf-order J1-smoothness absolute extremum | quantile = 0/10⁶ random perms (p < 10⁻⁶); also beats Nuzūl ordering | Reported as "partial" because J2 fails; J1 alone is publishable |
| **S2** | Anti-Null-Space Theorem | 54 % of Quran's Mahalanobis mass lives in the 1.6 %-variance PC4+PC5 subspace; perm p < 10⁻⁴; 63× null-max | Buried in hypothesis register, never promoted |
| **S3** | Multi-scale Fisher Law (E14) | 5 scales: Brown χ² p = 1.41·10⁻⁶; Shapley shares {S1=−3 %, S2=14 %, S3=5 %, S4=40 %, S5=44 %} | Negative S1 share never discussed as structurally informative |
| **S4** | Takens / RQA nonlinear determinism | DET = 0.374 vs AR(1)-null 0.016 ± 0.003 (**119σ**); IAAFT-null 0.157 ± 0.034 (6.4σ) | Buried in Tier 2 audit |
| **S5** | Anti-Variance Manifold (E15) | along 2 smallest-eigenvalue ctrl directions: Quran/ctrl ratio 2.33×; percentile 98.53 %; perm p < 10⁻⁴ | Standalone publishable; never named |
| **S6** | %T > 0 = 39.7 % vs 0.10 % = **397× enrichment ≈ 400** | single binary scalar, larger ratio than any other Quran-vs-ctrl contrast | Ranked 14, not in abstract |
| **S7** | LC3-70-U Bible-only leakage pattern | 0/5 secular Arabic family leaks; 7/2 509 leaks ALL from `arabic_bible` | Translation-of-scripture sub-claim never named |
| **S8** | Verse-graph n_communities ≈ **7.02** (rank 1/10) | robust to seeds (delta = 0.000 across audit re-runs) | The "seven loaded number" coincidence never tested |
| **S9** | 5-D fingerprint reduces to 1-D EL | AUC(EL alone) = 0.9971 vs AUC(5-D) = 0.998; gap < 0.001 | Paper foregrounds 5-D when 1-D suffices for 99.7 % of signal |
| **S10** | Cross-compressor γ split (LZ77 vs BWT) | γ_gzip = +0.0716, γ_brotli = +0.0871; γ_zstd = −0.029, γ_bzip2 = −0.048 | Retracted as "non-universal"; pattern-of-signs is itself a finding |
| **S11** | Mushaf-ordering 4-witness convergence | E6 Moran's I + E8 Mantel(NCD, mushaf) r = +0.59 + E17 J1 + exp63 VAR(1) ρ = 0.677 | 4 independent methodologies agree, never unified |
| **S12** | EL-dominance 4-witness convergence | exp70 LDA θ = 82.7° + exp74 PC4 50.2 % mass + exp89 AUC(EL) = 0.9971 + exp90 cross-language | Paper presents 5-D when EL is the discriminative variable |

## X — synthesis-grade theorems (passed combined p tests)

| ID | Theorem | Combined p | Status |
|---|---|---|:--:|
| **X3** | Prose-extremum (AR(1) + Hurst H_delta + Benford + fractal dim + scale hierarchy) | Brown ρ=0.4 corrected p ≈ **6.7·10⁻³⁴** (effectively a 2-strong-witness theorem on AR(1) + Hurst H_delta) | ✅ PASS |
| **X6** | Geometric-Information-Theory Theorem (S1 trajectory + S3 multi-scale + S4 dynamics + S5 null-space) | Brown ρ=0.3 p ≈ **2.9·10⁻¹³** (~7σ); Brown ρ=0.6 p ≈ 1.3·10⁻⁹ (~6σ) | ✅ PASS |
| **X7 P2_OP1** | Rényi-α=2 uniqueness (`2^{-H_α(p)} = Σpᵢ²`) | closed-form proof + numerical verification on Quran 28-letter PMF | ✅ PROVED |
| **X7 P2_OP3** | `T² = 2·n_eff·KL_Gaussian` exact identity | \|δ\| = 0; Edgeworth correction +4.4 % at n_eff = 66.21 | ✅ PROVED + Edgeworth-tightened |
| **X7 P2_OP2** | T_alt = `H_cond(first_letter_of_last_word) − H(end_letter)` | Φ_M = 3 557 → **3 868 (+8.7 %)**, σ +1.33; FAILS at Band-C (−4.4 %) | ⚠ length-conditioned refinement; **§4.4 LOCKED C1 (2026-04-25)** — T_canon stays canonical, T_alt becomes P7 headline |
| **X7 Path D** | Linear T² beats non-linear discriminators | T² σ-equivalent = +1 073 vs MMD² +157, Energy +334 → T² dominates by 3–7× | ✅ falsifies "non-linear-beats-T²" hypothesis |

## Z — direct cross-reference to live blockers

These belong in `05_DECISIONS_AND_BLOCKERS.md` but are surfaced here so the table is self-contained.

- ~~**Z1 §4.4 T_alt decision**~~ — **RESOLVED 2026-04-25 evening: C1 LOCKED**. T_canon stays canonical (Φ_M = 3 557); T_alt becomes P7 headline. P2 + P7 writing unblocked.
- **Z2 OSF pre-registration upload** (15 min user) — public DOI for the deposit at `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip` (SHA `2f90a87a…`); unblocks P3 submission.
- **Z3 Riwayat data upload** (manual, external) — Warsh / Qalun / Duri text files in Tanzil `S|V|text` format → 15-min runtime → upgrades every Hafs-specific finding to Uthmanic-skeleton-level.
- **Z4 Two-team external replication** — required to upgrade any "law" claim from empirical-replicated to externally-validated.

## Retractions (not on this table)

The full **50 retractions** (R47 closure 2026-04-23, R48–R49 patch B, R50 patch E) are catalogued in `04_RETRACTIONS_LEDGER.md` with do-not-reopen guidance. Notable: R01 golden-ratio φ ≈ 0.618, R09 "Quran 76 % stronger than next scripture", R26 multi-level Hurst ladder, R27 universal R ≈ 0.70 (now Abrahamic-script typology), R28 Ψ_oral ≈ 5/6 (n = 1 numerical coincidence), R47 Reed-Solomon-like error-correcting code (UTF-8 confound).

---

*Sources: `docs/reference/findings/RANKED_FINDINGS.md` v1.3 (43 positive + 28 retraction rows); `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md` Tier-S synthesis (S1–S12, X3, X6, X7); `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md` (LC2 cross-tradition v7.8 numbers); `results/integrity/results_lock.json` (58 locked scalars).*
