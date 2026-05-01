# 03 — Overlooked / Untouched Opportunities (Nobel × PNAS Path)

> ⚠ **v7.9-cand SUPERSESSION NOTICE (2026-04-28 evening — patch H V3, H39 envelope replication COMPLETE)**: H39 (`exp95f_short_envelope_replication`) ran and yielded **`FAIL_envelope_phase_boundary`** (FN07; Q:055 Al-Rahman lone violator). No F-number opened. Total: 58 positive findings + 53 retractions + **7 failed-null pre-registrations** (FN07 added). Opportunities below are unchanged.
>
> ⚠ **Earlier (2026-04-28 — patch H V2, Phase 2 COMPLETE)**: **F57 stamped PASS** (4/6 Quran self-descriptions confirmed, p = 0.0049). C6 CONFIRMED via `exp99`; C4/C5 each failed 2 op-tests (FN03–FN06). Opportunities below are unchanged by Phase 2 results.
>
> ⚠ **Earlier notice (2026-04-26 night — patch F sync)**: This snapshot is frozen at 2026-04-25 evening. **Many** "untouched opportunities" have now been executed across patches B / C / D / E / F:
>
> **Patch B/C/D executed**: full-Quran 5-D (`expP7`, T² = 3 685), EL one-feature law full-114 (`exp104` AUC = 0.9813), ن-dominance morphological forensics (`expP9.N7`), zero-trust audit (patch D — 5 corrections, 0 verdicts flipped).
>
> **Patch E executed (2026-04-26 sprint)**:
> - **✅ Pre-registered hadith N1** (was Path-A unlock #1): `expP10` AUC = **0.9718**, MW p = 4·10⁻³² → PASS_STRONG
> - **✅ Maqamat al-Hariri** (was Path-A unlock #2): `expP16` AUC = **0.9902**, MW p = 2.4·10⁻³⁸ → QURAN_DISTINCT_FROM_SAJ — closes the highest-leverage external test
> - **✅ N3 Riwayat invariance** (was PNAS-stretch): `expP15` — 5 riwayat (Warsh, Qaloun, Douri, Shuba, Sousi) sourced from `IshakiSmaili/QuranJSON` (MIT-licensed), all keep AUC ≥ 0.97 → PARTIAL_INVARIANT
> - **✅ Shannon-capacity for EL** (was 4-6 months theoretical): `expP18` — i.i.d. floor = 0.295, Quran's structural rhyme excess = +0.425 → THEOREM (closes the upper-bound derivation)
> - **✅ Brown empirical R**: `expP11` — p_joint = **5.24·10⁻²⁷** (~11 OOM tighter than ρ=0.5 prior)
> - **✅ Bootstrap T² CI**: `expP12` — [3 127, 4 313] → STABLE; triggers R50 reframe of patch B claim
> - **✅ LOCO EL ablation**: `expP13` — min AUC 0.9796 → ROBUST_STRONG
> - **✅ Cross-script clean dominance table**: `expP14` — Quran p_max(any letter) 2.43× next Arabic
> - **⏳ Markov saj' adversarial**: `expP17` — mode 1 done (max EL = 0.20 < 0.314); modes 2-4 RUNNING overnight
>
> **Patch F executed (2026-04-26 night, multi-compressor consensus closure of Adiyat-864)**:
> - **✅ F53 — Multi-compressor consensus** (was the gzip-only 99.07 % "ceiling" objection; previously listed as untouched-opportunity #4 "exhaustive forgery resistance"): `exp95c` PASS_consensus_100 — K=2 across {gzip-9, bz2-9, lzma-9, zstd-9} closes the Adiyat-864 ceiling at recall = **1.000** (864/864) with K=2 ctrl FPR = **0.0248** (half of gzip-only's 0.05). lzma-9 and zstd-9 each unilaterally close the gap (solo recall = 1.000). Strengthens the §4.18 forgery-resistance argument: any forged Quran-imitation must now defeat 4 structurally different compressors simultaneously, not just gzip's LZ77 dictionary
> - **✅ Robustness sweep**: `exp95d` PARTIAL_seed_only — K=2 recall identical 1.000 across seeds {42, 137, 2024} on Q:100 (span = 0.000); cross-surah Q:099 al-Zalzalah recall = 998/999 = 0.999 (one bāʾ↔wāw substitution at K=1)
> - **🚫 FN01 / FN02 (Category K, NOT retractions)** — two earlier closure attempts failed transparently: `exp95_phonetic_modulation` (recall dropped to 0.985 with stratum FPR overshoot) and `exp95b_local_ncd_adiyat` (recall collapsed to 0.399). The negative results constrain the design space — only compressor diversity, not phonetic weighting or window locality, lifts the gzip ceiling
>
> **Still untouched**: N2 LLM-forgery against the K=2 multi-compressor consensus (now scaffolded as `exp92_genai_adversarial_forge/`; GPU + LLM API credentials needed; ~$5K compute), cross-surah F53 confirmation on ≥ 3 more short Meccan surahs (Q:101, Q:103, Q:104) to escalate from "Q:100 paper-grade" to "Adiyat-class universal", full-mode `exp46`/`exp50` poetry retests, two-team external replication (the only path to ~95 % strength). Defer to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` §4.41-§4.42 and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md` patches B / C / D / E / F.

**Methodology of this list**: Two-pass scan of the entire repo (`OPPORTUNITY_TABLE_DETAIL.md`) cross-referenced against the v7.8 cross-tradition phase findings. Each row is either (i) a paradigm-adjacent finding that is **already PASS but not yet packaged**, or (ii) a hypothesis where one targeted experiment would substantially raise the publication tier.

**Honest ceiling guidance**: per `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md §3.3` and `docs/reference/prereg/PREREG_GAMMA_KOLMOGOROV.md:347-349`, this project's realistic ceiling is **PNAS stretch** + *PRX Information* / *IEEE Trans. Info. Theory* / *Phys. Rev. E*. Nobel-tier framing has been formally ruled out by the project lead and is preserved here only because the user asked.

---

## A. Top-7 already-PASS findings still un-packaged (highest leverage)

These rows are **already significant** and need only a writing pass — not new experiments.

| # | Opportunity | Status | Effort | Sub-tier ceiling |
|--:|---|---|---|---|
| **1** | **Mushaf-order J1-smoothness absolute extremum** at 10⁶ perms (`expE17b_mushaf_j1_1m_perms`) | PASS, p < 10⁻⁶ ; Mushaf beats every one of 10⁶ random orderings AND beats Nuzūl ordering by 39× the perm sd | 1 day write-up | Standalone *Entropy* / *PLOS ONE* — call it the **"Uthmanic-Order J1 Extremum Law"** |
| **2** | **54 % of Φ_M lives in 1.6 % of variance** (S2 anti-null-space theorem) | PASS, perm p < 10⁻⁴, 63× null-max ; orthogonal confirmation by S5 anti-variance manifold (98.53 percentile, p < 10⁻⁴) | 2 days write-up | *Entropy* — call it the **"Anti-Variance Manifold Theorem"** with an explicit hyperplane equation |
| **3** | **Geometric-Information-Theory Theorem (X6)** — 4-witness joint p ≈ 2.9·10⁻¹³ (~7σ) | PASS at Brown ρ=0.3 AND ρ=0.6 ; mechanistically distinct witnesses | 1 week write-up | *PRX Information* — call it the **"Quran 7σ Joint-Anomaly Theorem"** ; this is the single biggest synthesis story |
| **4** | **Prose-Extremum Theorem (X3)** — Brown-corrected p ≈ 6.7·10⁻³⁴ on AR(1) + Hurst H_delta | PASS as 2-strong-witness theorem (W1 AR(1) p=10⁻²³ + W4 H_delta p=10⁻³⁶) ; 3 supplementary witnesses concur | 3 days write-up | *Entropy* / paragraph in *PRX Inf* — **"Quran-at-Prose-Extremum Theorem"** |
| **5** | **Information-theoretic re-derivation of (EL, T, Φ_M)** — X7 P2_OP1 + P2_OP3 closed-form proofs | PROVED ; α=2 unique Rényi parameter ; T² = 2·n_eff·KL_Gaussian exact ; Edgeworth correction +4.4 % | 3-4 days write-up | *IEEE Trans. Inf. Theory* fit — closes the "are these ad-hoc statistics?" reviewer objection definitively |
| **6** | **EL is a 1-D sufficient classifier** (S9/S12) — AUC(EL alone) = 0.9971 vs AUC(5-D) = 0.998 | PASS ; 4 independent witnesses (LDA θ=82.7°, PC4 50.2 % mass, ablation, cross-language) | 2 days rewrite of P3 abstract around EL | *PLOS ONE* P3 — **abstract should lead with EL alone, not 5-D** ; clean parsimony narrative |
| **7** | **Mushaf-ordering 4-witness convergence (S11)** — Moran's I + Mantel + J1 + VAR(1) ρ | All 4 PASS independently ; never unified ; 4 different methodologies agree on non-randomness of canonical 114-surah order | 1 week write-up | *Computational Linguistics* — **"Canonical-Order Four-Witness Theorem"** |

These 7 rows alone, if written in parallel over 4-6 weeks, would produce **3-5 new submission-ready manuscripts** without any new compute.

---

## B. PNAS-stretch experiments — single-experiment unlocks

These are **one experiment away** from substantially upgrading the publication tier.

| # | Opportunity | Why it matters | Effort | Outcome if positive |
|--:|---|---|---|---|
| **B1** | **Riwayat invariance test** (Warsh / Qalun / Duri vs Hafs) | Every locked finding is currently "Hafs-specific". If `\|ΔΦ_M\| ≤ 0.02` across 3+ qirāʾāt, *every* finding upgrades from "Hafs property" to "Uthmanic-skeleton property" | 15 min runtime once Tanzil files are placed in `data/corpora/ar/quran_{warsh,qalun,duri}.txt` | Promotes the entire P2 paper from "single recitation" to "consonantal-skeleton-level" claim → PNAS-tractable |
| **B2** | **Two-team external replication** | Required to upgrade ANY law claim from "empirically replicated" to "externally validated". Only one pipeline author has run anything | 2-4 weeks coordination | Closes the only remaining structural objection PRX/PNAS will raise |
| **B3** | **Shannon-capacity derivation of LC2** | Turns the empirical cross-tradition law into a **theoretical** universal: "which canonical orderings are reachable under bounded oral-transmission noise?" — predicts the 5-D feature region | 2-6 months theory + 1 month verification | Promotes LC2 from empirical → formal universal law of oral transmission. Single highest-leverage long-term item per `RANKED_FINDINGS §6 long-term item 15`. |
| **B4** | **Cross-language perturbation hierarchy** on Tanakh + Iliad (`L1` law candidate) | Tests whether `d(word) > d(verse) > d(letter)` holds in non-Arabic scripts. Currently n = 1 | 2 weeks | Promotes L1 to formal cross-language law (Phys. Rev. E candidate) |
| **B5** | **Character-level BPE LM** (R4 upgrade) on pre-Islamic poetry | Closes the emphatic-stop blind spot (ت↔ط, ك↔ق): all 4 universal compressors give 0 % on these substitutions; only a phoneme-aware LM can detect them | 2-6 weeks GPU | Lifts detection ceiling from "statistical detector" → "authentication gate"; Adiyat case becomes externally bullet-proof |
| **B6** | **Kolmogorov-complexity derivation of γ** | Turns γ_gzip from empirical residual into a formal information-theoretic law | 2-3 months | Currently retracted via cross-compressor sign instability; would need a per-compressor universality framework first |

---

## C. Tier C — under-examined coincidences worth analytic derivation

Each of these is a numerical coincidence that has been **dismissed individually** under look-elsewhere effects. Joint significance under Bonferroni × 4 would survive at 0.01 level if **any one** had an ex-ante derivation.

| # | Coincidence | Match | Status |
|--:|---|---|---|
| **C1** | EL_q = 1/√2 | 0.04 % rel error ; jackknife/bootstrap CI [0.66, 0.75] contains 1/√2 ; t = 0.014, p = 0.99 | **NOT REJECTED** ; analytic upper-bound derivation under uniform-letter null is the single open theoretical task |
| **C2** | VL_CV_FLOOR = 1/√26 | 0.04 % rel error ; **provenance found** (26 = MSA consonantal phonemes after subtracting hamza+alif) | DERIVED ; analytic VL_CV-lower-bound proof under a Quran-relevant null still open |
| **C3** | EL_q² = 1/2 | derives from C1 ; passes at per-surah-mean scope (gap 0.0004) ; FAILS at corpus-pool scope (gap 0.034) | scope-conditional ; valid only at the C1-natural aggregation |
| **C8** | %T_pos ratio Quran/ctrl-max = 397× ≈ 400 = 20² | bootstrap 95 % CI never published | **un-tested** ; cheap CI test could promote to "near-integer" coincidence |
| **C9** | LC3-70-U polar angle θ = 82.73° | tan(82.73°) = 7.85 ≈ 2π only at 25 % gap (no tight match) | **likely coincidence** ; reflects EL is 8× T-weighted in the discriminant |

**One analytic derivation here is the cheapest path to a Tier-C upgrade**. C1 (EL_q ≈ 1/√2) is the most natural target because it has the cleanest information-geometric framing (Cauchy-Schwarz upper bound on rhyme-rate under symmetric binary terminal-letter null).

---

## D. Tier D — classical Quranic-studies concepts never formally tested

Each row is a **named feature in 1 400 years of classical Arabic / Islamic scholarship** that has a concrete computable surrogate but has never been operationalised.

| # | Classical concept | Computable surrogate | Status |
|--:|---|---|---|
| **D1** | *Munāsabāt* (inter-surah / inter-verse thematic coherence) | Arabic semantic-embedding cosine on adjacent-verse / adjacent-surah pairs (multilingual AraBERT) | NEVER ATTEMPTED ; deferred (model dependency) |
| **D2** | *Sajʿ* (rhymed/assonant prose) | qāfiya detector (final vowel + consonant + syllable structure post-tajwīd) | EL captures verse-final graphemic rhyme but NOT phonological qāfiya |
| **D3** | *Fawāṣil* (verse-end markers) — al-Rummānī's 3-class taxonomy | extend EL to (tamāthul / muqārib / tawāzun / unrelated) categorical | Current EL is binary ; 4-class never tested |
| **D4** | *Tajwīd* features (madd, ghunnah, qalqalah, ikhfāʾ, idghām) as primary features | 6-D tajwīd-feature Mahalanobis | Independent feature axis ; **never computed** |
| **D6** | *Muqaṭṭaʿāt* (mystery letters) as prediction feature | one-hot encoding of muqaṭṭaʿāt-grouping → ANOVA in 5-D | Only one χ² topological test (R16 NULL p = 0.4495) |
| **D8** | *Ḥizb* + *rukūʿ* (60 + ~558 nested liturgical divisions) | smoothness test at each granularity, mirroring D7 juzʾ | D7 (juzʾ) DONE → JUZ_J1_DOMINANT q=0.002 ; D8 deferred (data) |
| **D10** | *Tartīb al-Nuzūl* — multiple chronological orderings | E17 J1 smoothness vs Nöldeke / Ibn ʿĀshūr orderings | Only Egyptian-standard tested ; alternatives never run |
| **D11** | *Ziyādāt* (Ibn Masʿūd / Ubayy codex variants) | 5-D features on companion-codex reconstructions | Never attempted |
| **D12** | *Iʿjāz ʿadadī* (numerical inimitability) — distinct from retracted numerology | top 20 traditional balanced-pair claims (dunyā ↔ ākhira, mawt ↔ ḥayāt) verified by lemma/root count | Cheap, never run ; clean falsifiable list |
| **D13** | *Aḥruf sabʿa* ("seven letters" / seven modes) | possible link to n_communities ≈ 7.02 (S8) | Untested |

**The single most-promising row of these** is **D4 (tajwīd 6-D feature space)** — it's the only one that could plausibly produce an *independent* feature axis orthogonal to the 5-D Φ_M, and the project has the vocalised Hafs text on disk.

---

## E. Untouched PNAS-tier dimensions — what we have NOT looked at

These are entirely unexplored axes where the project has not even attempted a measurement. Listed in rough order of plausibility × tractability.

| # | Untouched dimension | Why it's PNAS-tier if it works | Why it might not |
|--:|---|---|---|
| **E1** | **Acoustic / phonetic Quran-vs-recitation acoustic signature across reciters** | Currently 1 reciter (Husary) at 5 190 verse-level acoustic samples ; multi-reciter would test whether the prosodic-excursion signal is text-property or reciter-specific | Reciter recordings as raw audio are not in the repo ; 2-6 weeks acquisition |
| **E2** | **Cross-language perturbation hierarchy on > 3 corpora** | If `d(word) > d(verse) > d(letter)` holds in Hebrew + Greek + Sanskrit + Pali + Avestan → cross-language scaling law of oral text | Currently n=1 (Quran only) |
| **E3** | **Pre-Islamic poetry external two-team replication** | Required gate for any "Quran-distinctive" claim to be externally validated | Coordination + 2-4 weeks |
| **E4** | **NCD-matrix cross-scripture clustering** (Quran 114 surahs × Tanakh 929 chapters × NT 260 chapters × Iliad 24 books) | Does Joseph/Yusuf cluster with Genesis 37-50 ? Does the Moses surah cluster with Exodus ? Inter-scriptural "genetic-distance" map | Compute is cheap (days) ; never attempted (`A9`) |
| **E5** | **Recitation-rule (tajwīd) Mahalanobis distance** to non-tajwīd-aware Arabic | Independent feature axis ; if Φ_tajwīd is significantly larger than Φ_M(5-D) → tajwīd captures distinct signal | D4 above ; never computed |
| **E6** | **Bayesian hierarchical priors** on per-surah / per-chapter parameters | Implicit causal model becomes explicit ; tightens every CI | E5 in `OPPORTUNITY_TABLE_DETAIL.md` ; never built |
| **E7** | **Causal DAG over (corpus, period, genre, length, harakat-density) → 5-D fingerprint** | Distinguishes correlation from causation in the discriminative axis ; foundational for any "structural cause" claim | Significant theory effort ; never attempted |
| **E8** | **Formal Lean / Coq proof of LC3 parsimony proposition** | Would close the strict Fisher-sufficiency gate (currently PARTIAL at 0.089 vs 0.02 target) | High effort ; uncertain value beyond reviewer optics |

---

## F. The PNAS-stretch package recipe

If you (the project lead or external AI) want to maximise the chance of a PNAS-grade submission **without** adding new experiments, the single recommended manuscript is:

**Title**: *"Multi-witness joint anomaly of the Quranic canonical ordering at 7σ Gaussian-equivalent: a synthesis of trajectory smoothness, multi-scale deviation, nonlinear dynamics, and null-space geometry"*

**Composition**:
- Headline: GIT theorem (X6, p ≈ 2.9·10⁻¹³)
- Robustness: Paths A/C/D + X7 P2_OP1 + P2_OP3 closed-form proofs (5 referee pre-empts)
- Cross-tradition complement: LC2 R3 path-minimality (8 corpora, LOO 8/8 robust)
- 1-feature parsimony: EL → AUC 0.9971 (rewrite of S9/S12)
- Honest retractions: §1.4 4-leg synthesis retraction + Ψ_oral retraction (turns weakness into rigor signal)

**Why this works**: it stops short of "universal Quran-uniqueness" framing (which is falsified) and lands on **multi-axis joint anomaly** (which is true at 7σ). PNAS reviewers reward this kind of disciplined synthesis on real cross-tradition data.

**Effort estimate**: 6-10 weeks writing ; **zero** new compute.

---

## G. What is NOT a viable path (briefly, so you don't waste time)

- ❌ "Quran is unique on every dimension" — falsified ; Tanakh/Rigveda beat Quran on multiple cross-tradition metrics.
- ❌ "Universal R ≈ 0.70 across writing systems" — falsified by Devanagari (R = 0.918) and Latin transliterations (R = 0.20).
- ❌ "Ψ_oral ≈ 5/6 cross-tradition universal" — falsified ; 0/5 oral corpora yield Ψ in the loose [0.65, 1.00] band.
- ❌ "Reed-Solomon error-correcting code in Quran byte stream" — UTF-8 confound ; vanishes on compact 32-letter alphabet.
- ❌ "Quran is a universal physical law / natural constant" — never claimed by the project; per `PREREG_GAMMA_KOLMOGOROV.md` is explicitly out of scope.
- ❌ "DNA-of-the-Quran / error-correcting structure at surah scale" — `expA7` falsified (F1 lift only 1.2× vs 2× threshold).

---

*Sources: `docs/reference/sprints/OPPORTUNITY_TABLE.md` (top-7 missed-opportunities list), `OPPORTUNITY_TABLE_DETAIL.md` (Tier S/A/C/D/E/X catalogue), `docs/reference/findings/RANKED_FINDINGS.md §6` (long-term roadmap items 13-16), `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md §3` (venue ladder).*
