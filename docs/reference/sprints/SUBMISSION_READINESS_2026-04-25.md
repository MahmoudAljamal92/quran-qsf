# Submission-Readiness Memo — 2026-04-25

> ⚠ **v7.9-cand SUPERSESSION NOTICE (2026-04-28 evening — patch H V3, H39 envelope replication COMPLETE)**: H39 (`exp95f_short_envelope_replication`) ran and yielded **`FAIL_envelope_phase_boundary`** (FN07; Q:055 Al-Rahman lone violator). No F-number opened. Total: 58 positive findings + 53 retractions + **7 failed-null pre-registrations**. Publishable packages below remain unchanged.
>
> ⚠ **Earlier (2026-04-28 — patch H V2, Phase 2 COMPLETE)**: **F57 stamped PASS** (4/6 Quran self-descriptions confirmed, p = 0.0049). C6 CONFIRMED via `exp99`; C4/C5 each failed 2 op-tests (FN03–FN06). F57 PASS strengthens PAPER.md §4.46 but does not change venue strategy.
>
> ⚠ **Earlier notice (2026-04-26 night — patch F sync)**: This memo is frozen at 2026-04-25 evening. **Four** of the five "publishable packages" have evolved meaningfully:
>
> **P3 (EL Simplicity Law) — strongly upgraded by patch E**:
> - 1-feature AUC = 0.9813 on all 114 surahs (`exp104_el_all_bands`, patch B)
> - LOCO min AUC = **0.9796** (`expP13`, patch E) — robust
> - Pre-registered hadith holdout AUC = **0.9718** (`expP10`, patch E) — formal
> - **Maqamat al-Hariri (Arabic saj') AUC = 0.9902, MW p = 2.4·10⁻³⁸** (`expP16`, patch E) — closes the "any actual Arabic rhymed prose tested?" reviewer challenge
> - 5 alternative riwayat all keep AUC ≥ 0.97 (`expP15`, patch E) — rasm-invariance
> - Shannon-capacity i.i.d. floor = 0.295 + structural rhyme excess = +0.425 (`expP18`, patch E) — theoretical scaffolding for §4.40.4
> - Brown joint p = **5.24·10⁻²⁷** under empirical R (`expP11`, patch E) — ~11 OOM tighter than ρ=0.5 prior
>
> **P4 (cross-tradition) — status unchanged from patch D**: 2 confirmed corpora (Hebrew Tanakh AUC = 0.982, Greek NT AUC = 0.962) gained; R3 / Hurst disclosed as not-uniquely-Quran (4 corpora more extreme).
>
> **P2 (5-D T² outlier) — reframed by patch E R50**: full-Quran T² = 3 685 with bootstrap 95 % CI = [3 127, 4 313] (median 3 693, `expP12`); band-A T² = 3 557 is INSIDE the CI → the two values are statistically indistinguishable. Patch B language "T² INCREASES under full-Quran" is **reframed to "T² STABLE"** (R50 retraction).
>
> **P3 (Quran-anchored paper, Adiyat authentication case) — additionally strengthened by patch F (2026-04-26 night, F53)**: the gzip-only Adiyat-864 detection ceiling (99.07 %, finding #5 → row 53 of `RANKED_FINDINGS.md`) is **closed at 100 %** under K=2 multi-compressor consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} (`exp95c`, **PASS_consensus_100**) at K=2 ctrl FPR = 0.0248 (half of gzip-only's 0.05). Robustness sweep (`exp95d`, **PARTIAL_seed_only**): K=2 recall identical 1.000 on Q:100 across seeds {42, 137, 2024} (span = 0.000); cross-surah Q:099 al-Zalzalah K=2 recall = 998/999 = 0.999 (one bāʾ↔wāw substitution at K=1, saved by gzip-solo). The forgery-resistance argument tightens correspondingly: any forged Quran-imitation must now defeat four structurally different compressors simultaneously. Two earlier closure attempts are logged transparently as failed nulls (Category K of `RETRACTIONS_REGISTRY.md`): FN01 phonetic-Hamming-modulation (`exp95`, recall dropped to 0.985 with stratum FPR overshoot) and FN02 window-local NCD (`exp95b`, recall collapsed to 0.399 — useful negative datum constraining the design space).
>
> Other patch B/C/D evidence still valid: ن-dominance forensics (Quran 4.6× ن-rate any Arabic, 6.7× hadith; 2.43× dominant-letter-of-any-kind ratio per `expP14`); Brown conservative-prior p = 2.95·10⁻⁵. Defer to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` §4.40-§4.42 and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md` patches B / C / D / E / F for the post-2026-04-25 record.

**Status (rev 2026-04-26 patch E + reviewer-feedback memo)**: **Six** publishable packages remain empirically locked (**P0 NEW**, P1, P2, P3, P4, P7). The new **Package P0 — LC2 cross-tradition paper** was added 2026-04-26 in response to external reviewer feedback (`docs/REVIEWER_FEEDBACK_2026-04-26.md`) advising that LC2 should be the headline frame, not finding #13 of 52. P0 uses the same data as P4 but reorganises the manuscript so that **canonical-ordering path-minimality across 6 oral-liturgical traditions** is the headline thesis and the Quran 5-D fingerprint becomes the most-detailed anchor case study. P0 venue ladder: **PNAS / Cognition / Cognitive Science / Glottometrics**. P3 (Quran-anchored paper) remains the safe parallel option targeting **CL / DH / IEEE Trans. Info. Theory**.

**Status (rev 2026-04-25 evening — cross-tradition phase complete; pre-feedback)**: **Five** publishable packages remain empirically locked (P1, P2, P3, P4, P7). Cross-tradition phase executed today reframes P1 (R-universal → R-typology) and confirms LC2 R3 path-minimality as the single surviving cross-tradition universal in P4. Of the three derived constants in §1, **§1.1 Î¨_oral is retracted at n=1** (cross-tradition universal falsified by `expX1_psi_oral`, retraction #28) and **the four-leg §1.4 optimality synthesis is retracted** (3/4 legs do not survive independently). §1.2 γ_gzip and §1.3 EL/EL_b framings remain valid. Paths A / C / D + X7 Paradigm-Stage 2 closures pre-empt five referee objections; the cross-tradition phase preempts a sixth ("is the Quran fingerprint actually n=1, or do you have replication?" → LC2 path-minimality replicates on Rigveda at z = −18.93). Honest ceiling is top-tier domain journal, **not** Nobel.

**Scope**: Companion to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md` and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md`. This memo does NOT introduce new empirical claims; it organises already-locked results into a submission plan.

**Decision requests**: (1) four/five papers vs one paper (Â§4) ; (2) **NEW — T_alt vs T_canon as canonical headline T** (Â§4.4) — affects every paper's Î¦_M numeric.

---

## Package P0 — LC2 cross-tradition paper (NEW, 2026-04-26 reviewer-feedback addition)

> **Origin**: Added 2026-04-26 in response to external feedback that LC2 (currently buried at finding #13 of 52) is the genuine non-specialist-significance finding and should be the headline frame. Documented in `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/REVIEWER_FEEDBACK_2026-04-26.md`.

### Headline thesis

*"Canonical ordering in oral-liturgical scriptures minimizes structural path cost: a cross-tradition information-theoretic study"* — 6 oral-liturgical canons spanning 4 language families, 4 scripts, and 3 millennia all minimize feature-space path-cost under canonical ordering; the negative control (Iliad narrative) fails as predicted; LOO 8/8 robust.

### Data already in hand (no new experiments required to ship a defensible draft)

| Corpus | Tradition / era / script | z (R3 path-cost) | BH p_adj |
|---|---|:--:|:--:|
| Rigveda | Vedic Sanskrit / Devanagari / ~1500 BCE | **−18.93** | 3·10⁻⁴ |
| Tanakh | Hebrew / 5th–2nd c. BCE | **−15.29** | 3·10⁻⁴ |
| NT | Greek / 50–100 CE | **−12.06** | 3·10⁻⁴ |
| Quran | Arabic / 610–632 CE | **−8.92** | 3·10⁻⁴ |
| Avestan Yasna | Old Iranian / ~6th c. BCE | **−3.98** | 3·10⁻⁴ |
| Pali Majjhima | Pali / ~3rd c. BCE | **−3.46** | 3·10⁻⁴ |
| Iliad | Greek narrative epic / ~8th c. BCE | **+0.34** | 0.6274 (fails as predicted ✓) |
| LOO | 8/8 single-corpus drops | all still SUPPORT | ✓ |

Source: `@C:/Users/mtj_2/OneDrive/Desktop/Quran/results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json` + `@C:/Users/mtj_2/OneDrive/Desktop/Quran/results/experiments/expP4_cross_tradition_R3_loo/expP4_cross_tradition_R3_loo.json`. Already pre-registered (`@C:/Users/mtj_2/OneDrive/Desktop/Quran/experiments/expP4_cross_tradition_R3/PREREG.md`).

### What still needs to happen for P0 to ship

**Mandatory** (~2 h):
- **Draft new abstract + §1 introduction** in a separate file `docs/PAPER_LC2_FRAME.md` so the existing `docs/PAPER.md` (the P3 manuscript) is not disturbed. Title under consideration: *"Canonical ordering in oral-liturgical scriptures minimizes structural path cost: a cross-tradition information-theoretic study."*
- **Reorganise existing §4.36–§4.39** (cross-tradition material) into the new §2–§4 (results) of the LC2-frame manuscript.
- **Demote** existing §4.1–§4.34 to "§5 Anchor case: the Quran fingerprint" — the same content, different organising thesis.

**Strongly recommended** (each ~1 day):
- **expP19** — add 2–3 more oral-liturgical corpora (Adi Granth, Mahabharata, Coptic Liturgy, Egyptian Book of the Dead, Sumerian Enheduanna hymns). Pushes n from 6 → 8–9 and pre-empts the "only n=6" reviewer objection.
- **expP20** — closed-form Shannon-capacity sketch: derive which of {R3, J1, Hurst, AR(1)} should minimize under noisy-channel oral-transmission optimization. **This is the gate from "empirically replicated" to "theoretical universal"** — a 1-day sketch suffices for the LC2 paper; a full theorem is the 6–12-month gate to a Phys. Rev. E / IEEE Trans. Info. Theory submission.
- **expP21** — meta-regression of z-score against canon properties (era, oral/written ratio, alphabet size, syllable rate, canon size). Quantifies *what makes a tradition's LC2 effect strong*.
- **expP22** — within-corpus style-preserving permutation null (replaces book-shuffle null). Closes the "are you measuring style or content organisation?" objection.

**Required for two-team replication-grade** (6–12 months, external):
- Independent replication on a fresh corpus pool by an unaffiliated team.

### Venue ladder (P0)

| Venue | Realistic odds | Why this venue |
|---|---:|---|
| **PNAS** (Anthropology + Social Sciences section) | medium | The cross-tradition-cognitive-cultural significance is exactly what PNAS means by "significance beyond the specific domain." Probably needs A3+A5 (abstract draft + Shannon-capacity sketch) at minimum. |
| **Cognition** | medium-high | Information-theoretic + cross-cultural memory transmission. Excellent fit. |
| **Cognitive Science** | high | Established venue for cross-cultural information processing claims. Lower bar than PNAS. |
| **Glottometrics** / **Journal of Quantitative Linguistics** | very high | Domain venues; would accept the empirical claim straightforwardly but with lower visibility. |
| Phys. Rev. E / IEEE Trans. Info. Theory | low without expP20 full theorem | Requires Shannon-capacity formal proof, not just a sketch. 6–12 month track. |

### Relationship to P3 (Quran-anchored paper)

P0 and P3 share **all underlying data and experiments** — they differ only in thesis and headline framing. Both can ship in parallel:

| | P0 (LC2 frame) | P3 (Quran frame, current `PAPER.md`) |
|---|---|---|
| Headline thesis | Cross-tradition oral-transmission universal | Quran is a multivariate stylometric outlier |
| Anchor evidence | 8-corpus z-score table | T² = 3 685, AUC = 0.9932 |
| Quran's role | Most-detailed anchor case study | The phenomenon being characterised |
| Cross-tradition role | The headline universal | A §4.36–§4.39 supplement |
| Venue ceiling | PNAS / Cognition / Cogn. Sci. | CL / DH / IEEE TIT |
| Effort to ship | A3 (abstract draft, 1.5 h) + reorganise existing sections | Already drafted (current `PAPER.md`) |

---

## Bottom line — what ships today, what's 2 weeks out, what's 6 months out

| Horizon | Package | Strongest locked scalar | Target venue (best fit) | Blocker |
|---|---|---|---|---|
| **TODAY** (reframed 2026-04-25 evening) | **P1** Abrahamic-script diacritic typology (was "universal") | R ∈ [0.55, 0.70] across Arabic / Hebrew / Greek (n=3 Abrahamic combining-mark scripts); Devanagari R = 0.918 places Indic scripts in a typologically distinct higher-R regime; Latin transliterations (Pali IAST, Avestan Geldner) are encoding artefacts — retraction #27 closes the script-universal claim, reframes as a positive Abrahamic-typology finding | *Computational Linguistics* / *Language* | Writing only (reframe from universal → typology) ; data + cross-tradition experiment (`expP4_diacritic_capacity_cross_tradition`) executed |
| **TODAY** | **P2** Quran geometric-info-theoretic theorem (X6 + A10 + A3 + **X3** + **D7**) | X6 Brown p â‰ˆ 2.9 Ã— 10â»Â¹Â³ ; **X3 `PROSE_EXTREMUM_BROWN` p â‰ˆ 6.7 Ã— 10â»Â³â´** (AR(1)+Hurst 2-witness) ; A10 J1 p < 10â»â¶ ; A3 STOT 4/5 ; **D7 `JUZ_J1_DOMINANT` q = 0.002** (cross-scale) ; Î¦_M = 3557 (47.03Ïƒ canonical) **or 3868 (48.36Ïƒ T_alt, +1.33Ïƒ)** at Band-A | *Entropy* / *PRX Information* / *IEEE Trans. Inf. Theory* | Writing + robustness section (Paths A/C/D + X7 closures done) |
| **TODAY** | **P3** LC3-70-U single-scalar classifier (EL-monovariate) | AUC 0.9975 ; 7/2509 leaks all from arabic_bible | *PLOS ONE* / *Digital Scholarship in the Humanities* | Writing only |
| **TODAY (NEW)** | **P7** T_alt = H_cond(first_letter_of_last_word) âˆ’ H(end_letter) refinement (X7 P2_OP2) | **Î¦_M 3557â†’3868 (+8.7 %)** ; Cohen d +3.999â†’**+5.279 (+33 %)** ; logâ‚â‚€ p_F âˆ’480â†’**âˆ’508** (mpmath 80-dps) ; **+1.33Ïƒ** Band-A ; CamelTools-free ; length-conditioned (Band-C reverses, âˆ’4.4 %) | *PLOS ONE* methodology, or supp. to P2/P3 | Writing only ; **canonical-T decision needed** (Â§4.4) ; T_alt not yet in `results_lock.json` |
| **DONE 2026-04-25 evening** | **P4** Cross-tradition A2/LC2 extension (Vedic Devanagari + Avestan + Pali) | **R diacritic spread 0.717 across {0.20, 0.47, 0.69, 0.70, 0.92}** — not a script-universal (retraction #27); **LC2 path-minimality SUPPORT (`expP4_cross_tradition_R3`, Rigveda z = −18.93 stronger than Quran's −8.92, leave-one-out 8/8 robust)** | *Language* / *PNAS* (LC2 headline only) | Writing only ; data + 7 experiments executed |
| **DONE 2026-04-25 evening** | **P5** Î¨_oral cross-corpus measurement | **`expX1_psi_oral` verdict NO_SUPPORT**: Quran reproduces 0.8358 sanity but 0/5 oral corpora yield Î¨ in pre-registered band [0.65, 1.00]; cross-corpus spread {hebrew=25.94, greek=1.16, iliad=0.27, pali_dn=0.15, pali_mn=0.44, rigveda=16.91, avestan=0.00} — retraction #28 | (no submission) | n=1 numerical coincidence ; not publishable |
| **6+ MONTHS** | **P6** Riwayat invariance (A4) | Need Warsh / Qalun / Duri text files | Supplementary to P2 | **Data ; manual upload only** (`build_pipeline_p3.py:560-563` auto-download disabled by design) |

P1 + P2 + P3 + **P7** are independent and can run in parallel. P4 + P5 are sequential (same pipeline, different corpora). P6 is data-blocked.

---

## Â§1 — The three derived constants under correct framing

Three algebraic combinations of already-locked scalars were proposed in this session's feedback round. All three verify arithmetically; interpretive caveats are as follows. None gates submission; all belong in a **"derived invariants"** subsection of whichever paper hosts them.

### 1.1 Î¨_oral = H(harakat | rasm) / (2 Â· I(EL; CN)) = 0.8357 — RETRACTED as cross-tradition universal (2026-04-25 evening)

> **POST-MEASUREMENT UPDATE 2026-04-25 evening**: Pre-registered cross-corpus experiment `experiments/expX1_psi_oral/` reproduces the locked Quran value to drift 3×10⁻⁵ (sanity PASS) but **falsifies** the cross-tradition universal: 0 of 5 oral corpora yield Î¨ in pre-registered loose band [0.65, 1.00]. Filed as retraction #28 in `RANKED_FINDINGS.md`. The 0.8357 number is now classified as a **Quran-only numerical coincidence at n=1** under the project's existing operational definitions of `H(harakat|rasm)` (T7 anchor) and `I(EL;CN)` (T7 Band-A with `ARABIC_CONN`). Do **NOT** carry the Î¨_oral ratio into any P1/P2 supplementary section; mention only as a transparent non-reproduction if at all. The full cross-corpus measurement and reasoning live in `experiments/expX1_psi_oral/SUMMARY.md` and `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md §5`.

- **Locked inputs**: `H(harakat|rasm) = 1.964 bits` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:187`, T7 corpus-level) ; `I(EL; CN) = 1.175 bits` (same line, T7-family).
- **Arithmetic**: `1.964 / (2 Â· 1.175) = 0.83574`. Gap to `5/6 = 0.8333` is `0.0024` (0.29 % rel).
- **Cross-corpus measurement (`expX1_psi_oral`, pre-registered, executed 2026-04-25)**: Quran 0.8358 (anchor); Hebrew Tanakh 25.94; Greek NT 1.16; Iliad 0.27; Pali_DN 0.15; Pali_MN 0.44; Rigveda 16.91; Avestan Yasna 0.00. Spread > 25 × the n=1 anchor. Verdict `NO_SUPPORT`. **Root cause**: I(EL;CN) varies by two orders of magnitude across corpora because the Quran uses the curated 14-item `ARABIC_CONN` connective list while every other corpus falls back to top-20-frequency stop-words via `derive_stopwords`; H(d|b) varies by script combining-mark inventory.
- **Correct framing** (post-measurement): "*Quran-specific numerical coincidence (n=1) at the locked operational definitions of (H_harakat|rasm, I(EL;CN)). Pre-registered cross-tradition extension on 7 other corpora produced spread 0–26, falsifying universality at the 5/6 attractor. A re-curated Î¨_oral with per-language discourse-connective lists and per-script diacritic-equivalence rules is well-defined work (≈1 day) but is out of scope for the present submission.*"
- **Critical context — A2 also retracted**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md:154-171` delivered R = 0.725 / 0.695 / 0.696 on Arabic / Hebrew / Greek (n=3 within Abrahamic combining-mark scripts); the 6-corpus extension (`expP4_diacritic_capacity_cross_tradition`) yields R_primitives spread 0.717, falsifying script-universality (retraction #27). Both n=3 R-cluster and the Î¨_oral ratio reduce to **typological** observations within Abrahamic combining-mark scripts, not script-universals.
- **Submission placement (REVISED)**: P1 reframes around the Abrahamic-typology claim with R ∈ [0.55, 0.70] for combining-mark scripts and R = 0.918 for Devanagari as a typologically distinct regime. Î¨_oral does **not** appear in the P1 manuscript at all. The surviving cross-tradition universal is **LC2 R3 path-minimality** (P4 main result, leave-one-out 8/8 robust).

### 1.2 Î³_gzip = 28Ã— single-edit Shannon-counting floor

- **Locked inputs**: `Î³_gzip = +0.0716` (length-controlled, `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp41_gzip_formalised\exp41_gzip_formalised.json`) ; `Î³_floor = logâ‚‚(800) / (800 Â· logâ‚‚(28)) = 0.002507` (trivial Shannon-counting bound for a 1-letter edit in an nÌ„=800-letter document over a 28-letter alphabet).
- **Arithmetic**: `0.0716 / 0.002507 = 28.56Ã—`.
- **LANDMINE — do NOT frame as "Kolmogorov-theoretic enrichment"**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\prereg\PREREG_GAMMA_KOLMOGOROV.md:89-108` (Â§2.5) and Â§12 retracted the gzipâ†’K bridge on 2026-04-22 because `exp103` found CV(Î³) = 2.95 across compressors (Î³_gzip = +0.0716, Î³_brotli = +0.0871, Î³_zstd = âˆ’0.0294, Î³_bzip2 = âˆ’0.0483 ; all p < 0.01 ; **two positive, two negative**). The phrase "enrichment over Kolmogorov floor" implicitly licenses exactly the gzip = K substitution that Â§2.4 explicitly forbids as unproven at finite length.
- **Correct framing**: "*Î³_gzip = 0.0716 is 28Ã— the trivial Shannon-counting floor for a single-letter edit in an nÌ„=800-letter document over a 28-letter alphabet. This is a within-gzip enrichment ratio — not a Kolmogorov-theoretic bound — and inherits the per-compressor non-universality from `S10` (gzip / brotli positive ; zstd / bzip2 negative). Any universal structural interpretation is falsified by exp103.*"
- **Submission placement**: P2 supplementary, as a **gzip-specific** scalar with `S10` cross-reference. Do NOT publish in isolation. Do NOT claim universality.

### 1.3 EL_Q / EL_boundary(LC3-70-U) â‰ˆ 2

- **Locked inputs**: `EL_q = 0.7074` (expC1 bootstrap CI [0.66, 0.75] contains 1/âˆš2) ; LC3-70-U: `L(s) = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221 = 0` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` Â§4.35).
- **Arithmetic**: `EL_boundary = 1.5221 / 4.1790 = 0.3642`. `EL_Q / EL_boundary = 0.7071 / 0.3642 = 1.9415`. Gap to 2 = 0.0585 (2.93 % rel).
- **Paths-A upgrade — no longer bookkeeping**: Path A (row 24 closure, 2026-04-25 03:02 UTC+02) measured the natural Edgeworth non-Gaussian correction band at **+4.4 %** (variance inflation factor `(1 + Î´) = 1.044`, `Î´ = +0.0443`) for this data at `n_eff = 66.21`. The 2.93 % gap is **smaller than the empirically-measured first-order non-Gaussian correction scale**. Under pre-registration discipline this is no longer a post-hoc curve fit ; it's a prediction whose residual sits inside the natural error budget of TÂ².
- **Correct framing**: "*Geometric consequence of `EL_q â‰ˆ 1/âˆš2` (C1) and the locked LC3-70-U LDA. The predicted bias `lda_bias = lda_EL / (2âˆš2) = 1.4775` vs observed `1.5221` differs by 2.93 %, comfortably within the 4.4 % empirical Edgeworth correction band for TÂ² at n_eff = 66.21 (Path A, row 24). Not an independent measurement ; is a structural identity on already-locked scalars.*"
- **Submission placement**: P2 geometric-info-theoretic theorem, in the "derived invariants" subsection. Bookkeeping value is now ~75 % of a real error-budgeted result ; still Tier C.

### 1.4 Optimality Theorem (LC2 extended) — RETRACTED as a four-leg synthesis (2026-04-25 evening)

> **POST-MEASUREMENT UPDATE 2026-04-25 evening**: P5 (Î¨_oral) measurement returned `NO_SUPPORT` (§1.1 above), removing the first leg of the four-condition synthesis. Combined with the previously-known issues with legs (ii) and (iii), only leg (iv) STOT v2 survives independently — and STOT v2 alone is not an "optimality theorem". The framing is therefore retracted in this form. The honestly-supported cross-tradition universal at n>1 is **LC2 R3 path-minimality** (P4 main result, leave-one-out 8/8 robust).

- Four-condition synthesis proposed in the feedback: (i) `Î¨_oral â‰ˆ 5/6` ; (ii) `Î³ = 28Ã— floor` ; (iii) `EL/EL_b â‰ˆ 2` ; (iv) STOT v2 4/5 PASS.
- **Status at 2026-04-25 evening**:
  - (i) `Î¨_oral â‰ˆ 5/6` **FALSIFIED** as cross-tradition universal (`expX1_psi_oral`, retraction #28). Quran-only n=1 coincidence under the locked operational definitions.
  - (ii) `Î³ = 28Ã— floor` already known **gzip-only**, non-universal across compressors (`exp103`).
  - (iii) `EL/EL_b â‰ˆ 2` already known to be an **algebraic identity** between two locked scalars; not an independent measurement.
  - (iv) STOT v2 **4/5 PASS** locked, but independence failed (max |Ï| = 0.567 > 0.3 threshold, `A3` caveat).
- **One-leg-of-four** is not an optimality theorem; the synthesis is retracted in this form.
- **Submission placement (REVISED)**: do **NOT** reference the four-leg synthesis in any paper. The surviving cross-tradition headline is the LC2 R3 path-minimality result (`expP4_cross_tradition_R3`), which goes into P4 as the main universal claim. P2 (the Quran paper) and P3 (the EL classifier paper) make no claim of multi-leg optimality.

---

## Â§2 — Robustness pre-empts (Paths A/C/D + X7 Paradigm-Stage 2 closures + X3 + D7)

Paths A / C / D (row 24, 2026-04-25 03:02 UTC+02) plus the X7 Paradigm-Stage 2 closures (rows 846-949 of `OPPORTUNITY_TABLE_DETAIL.md`, 2026-04-25 02:42-03:48 UTC+02) close five specific reviewer objections that would otherwise return P2 (and downstream P3) from referee round 1. X3 and D7 are not pre-empts — they are independent positive witnesses whose joint Brown-corrected p â‰ˆ 10â»Â³â´ is paragraph-grade headline material in their own right.

### 2.1 Path A — Edgeworth non-Gaussian correction is negligible (4.4 %)

- **Pre-empts**: *"Mardia rejects MVN at 185Ïƒ for the control pool. Is TÂ² fragile to the distributional assumption?"*
- **Answer (locked)**: `bâ‚ = 20.33, bâ‚‚ = 93.65` ; `Î´ = (bâ‚‚ âˆ’ p(p+2)) / (4 n_eff p) = +0.0443` ; `(1+Î´) = 1.044`. Variance inflation factor is **4.4 %** at `n_eff = 66.21`. `EDGEWORTH_CORRECTION_NEGLIGIBLE_<5%`.
- **Submission placement**: P2 robustness section, one paragraph + one table row. Also closes the `P2_OP3` caveat in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md:919` row 24 ("non-Gaussian correction is remaining work" â†’ now empirically closed).

### 2.2 Path C — 5-D is task-specific minimal (classification yes, representation no)

- **Pre-empts**: *"You claim the 5-D fingerprint is minimal. How do you know a 6th channel doesn't help?"*
- **Answer (locked, nuanced)**: TWO claims, both true, both defensible.
  - **Classification minimality** (B12): F6 fails per-dim gain â‰¥ 1.0 (full 0.54, fair subset 0.84) ; AR(1) Ï†â‚ and n_communities both also rejected under the same gate. The 5-D triple is **minimal-sufficient for Quran-vs-control discrimination**.
  - **Representation non-minimality** (Path C): 5-D regressed onto F6 lag-k gives mean RÂ² = 0.111 across k âˆˆ {1, …, 5}. F6 carries **89 % per-surah variance orthogonal to the discriminative axis**. 5-D is **not minimal-sufficient for per-surah representation**.
- **Publishable framing**: *"The 5-D fingerprint is task-specific minimal: minimal for classification, not for representation. F6 lag-k carries â‰ˆ 89 % per-surah variance orthogonal to the Quran-vs-control discriminative axis. This is a feature, not a bug — it means F6 is a candidate for tasks beyond binary classification (e.g. surah typology, cross-tradition genre comparison) without inflating the headline AUC."*
- **Submission placement**: P2 discussion, plus P3 parsimony section.

### 2.3 Path D — TÂ² dominates non-linear discriminators by 3-7Ã— Ïƒ

- **Pre-empts**: *"Why use a linear discriminant on non-Gaussian data? Wouldn't MMD or energy distance catch more?"*
- **Answer (locked)**:

  | Statistic | Observed | Null mean Â± sd | z (Ïƒ-equivalent) | p_perm |
  |---|--:|--:|--:|--:|
  | MMDÂ² (RBF) | 0.6594 | âˆ’1.9 Ã— 10â»â´ Â± 4.2 Ã— 10â»Â³ | **+157Ïƒ** | 5 Ã— 10â»â´ |
  | Energy distance | 2.279 | +0.013 Â± 0.007 | **+334Ïƒ** | 5 Ã— 10â»â´ |
  | Hotelling TÂ² | 3 557.34 | 5.06 Â± 3.31 | **+1 073Ïƒ** | 5 Ã— 10â»â´ |

  TÂ² dominates MMD by **6.8Ã—** Ïƒ-equivalent and energy distance by **3.2Ã—** Ïƒ-equivalent at the same B=2000 perm null. All three hit the permutation-null floor (p = 5 Ã— 10â»â´) — operational equivalence at the p-value but unambiguous Ïƒ-strength ordering.
- **Interpretation**: although the data is non-Gaussian (Mardia 185Ïƒ), the first-order mean shift dominates so completely that linear discrimination is operationally optimal. MMD/energy would only outperform when distributions overlap in mean but differ in shape — not the QSF setting.
- **Verdict**: `T2_DOMINATES_OR_PERM_FLOOR_HIT`. The "non-linear discriminator beats TÂ²" hypothesis is empirically falsified for this dataset.
- **Submission placement**: P2 robustness section, one paragraph + the table above. Also strengthens `S2` null-space subspace framing: linearity here is **operational**, not distributional.

### 2.4 X7 — Paradigm-Stage 2 closures (P2_OP1 PROVED + P2_OP3 PROVED + P2_OP2 T_alt refinement)

- **Pre-empts**: *"Are EL, T, and Î¦_M info-theoretically derivable, or are they ad-hoc statistics?"* AND *"Is the canonical T = H_cond(triliteral root) âˆ’ H(end_letter) optimal among feature pairs?"*
- **P2_OP1 âœ… PROVED** (2026-04-25 02:42 UTC+02 ; `expParadigm2_OP1_OP3_proofs/`): Among RÃ©nyi-Î±, **Î± = 2 is the unique Î±** with `2^{âˆ’H_Î±(p)} = Î£páµ¢Â²` (the iid pair-collision probability). Closed-form proof + numerical verification on Quran 28-letter terminal PMF (only Î±=2 hits target across {0.5, 1, 2, 3, 4, 5, âˆž}). Means **EL â†” RÃ©nyi-2 entropy is not arbitrary** — it is the unique Î±-RÃ©nyi parameterisation with pair-collision-probability semantics.
- **P2_OP3 âœ… PROVED + Edgeworth-tightened** (same session): Closed-form identity `TÂ² = 2 n_eff Â· KL_Gaussian` exact (`|Î´| = 0`) â‡’ **Î¦_M is information-theoretically twice the per-effective-sample KL divergence** between Quran and ctrl-pool 5-D Gaussian fits. Mardia rejects MVN at 185Ïƒ for ctrl pool, BUT Path A's Edgeworth correction shows variance inflation is only **+4.4 %** at n_eff = 66.21. TÂ² is operationally optimal under the actual non-Gaussian data.
- **P2_OP2 âš  NEAR-OPTIMUM ; T_alt REFINEMENT FOUND** (2026-04-25 03:36-03:48 UTC+02 ; `expParadigm2_OP2_T_alt_validation/` + `expParadigm2_OP2_T_alt_band_robustness/`): 16 candidate (X, Y) pairings tested at full scale. Results:

  | Statistic | Canonical T (locked) | T_alt = H_cond(first_letter_of_last_word) âˆ’ H(end_letter) | Î” |
  |---|--:|--:|--:|
  | Hotelling TÂ² (Band-A) | 3557.34 | **3867.79** | **+8.7 %** |
  | F (5, 2571) | 710.36 | 772.36 | +8.7 % |
  | Single-feature Cohen d | +3.999 | **+5.279** | **+33 %** |
  | Quran T_pct_pos | 39.7 % | **51.5 %** | +30 % rel |
  | Ctrl-pool max T_pct_pos | 0.001 (1 / 2509) | **0.000 (0 / 2509)** | absolute zero |
  | logâ‚â‚€ p_F (mpmath 80-dps) | **âˆ’480.25** | **âˆ’507.80** | **âˆ’27.55** |
  | Ïƒ-equivalent | ~47.03Ïƒ | **~48.36Ïƒ** | **+1.33Ïƒ** |
  | F-tail p reduction | — | **3.6 Ã— 10Â²â· Ã— smaller** | — |

  **Length-conditioning (band robustness)**:

  | Band | n_q | n_c | TÂ²_canon | TÂ²_alt | Verdict |
  |---|--:|--:|--:|--:|---|
  | Band-A (15-100 v) | 68 | 2509 | 3557 | **3868** | âœ… T_alt HOLDS (+8.7 %) |
  | Band-B (5-14 v) | 23 | 2068 | 442 | **459** | âœ… T_alt HOLDS (+3.9 %) |
  | Band-C (>100 v) | 18 | 142 | **1908** | 1825 | âŒ T_alt FAILS (âˆ’4.4 %) |

  **Mechanistic interpretation**: CamelTools triliteral-root extraction has ~10 % accuracy error. For short/medium surahs noise dominates signal — surface-token X (`first_letter_of_last_word`) wins. For long surahs sample size overcomes noise AND morphological richness becomes capturable — canonical T wins. **The optimal X is length-conditioned.**
- **Publishable framing (refined)**: *"Replacing the canonical CamelTools-based T with the CamelTools-free T_alt = H_cond(first_letter_of_last_word) âˆ’ H(end_letter) strictly dominates Hotelling TÂ² at typical surah lengths (Band-A: +8.7 %, +1.33Ïƒ ; Band-B: +3.9 %, +0.35Ïƒ) but underperforms at very long surahs (Band-C: âˆ’4.4 %). The optimal feature is length-conditioned. A length-adaptive T = Î±(n) Â· T_alt + (1âˆ’Î±(n)) Â· T_canon is the natural unified statistic."*
- **Submission placement** (4 viable, ranked best-first):
  1. **P7 standalone methodology paper** (*PLOS ONE* / *DSH*): atomic, ~3000 words, ships in 2-3 weeks.
  2. **P2 supplementary**: T_alt as robustness pre-empt — closes the "CamelTools-dependent" critique vector.
  3. **P3 supplementary**: parsimony argument — T_alt and T_canon both give AUC > 0.99.
  4. **Replace canonical T as headline** (requires `results_lock.json` write + downstream JSON updates ; major decision, see Â§4.4).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md:846-949` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_OP2_T_alt_validation\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_OP2_T_alt_validation\expParadigm2_OP2_T_alt_validation.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_OP2_T_alt_band_robustness\expParadigm2_OP2_T_alt_band_robustness.json`.

### 2.5 X3 — Prose-extremum theorem `PROSE_EXTREMUM_BROWN_PASS` (Brown p â‰ˆ 6.7 Ã— 10â»Â³â´)

- **Pre-empts**: *"Is the Quran genuinely an extremum, or just one outlier among several?"*
- **Answer (locked, 2026-04-25 02:13 UTC+02 ; `expX3_prose_extremum_brown/`)**: Among {Quran, 3 poetry corpora, arabic_bible, 2 prose}, the Quran sits at the prose-side extremum on (AR(1) Ï†â‚, Hurst H_delta) jointly at **Brown-corrected p â‰ˆ 6.7 Ã— 10â»Â³â´** (Fisher-independence p â‰ˆ 3.2 Ã— 10â»âµâ´ ; Brown Ï-correction with empirical inter-witness correlation ÏÌ„ â‰ˆ 0.4). 2-strong-witness theorem: W1 (AR(1) p = 8.2 Ã— 10â»Â²Â³, Quran Ï†â‚ â‰ˆ 0.167 vs poetry Ï†â‚ = 0) + W4 (Hurst H_delta p = 2.2 Ã— 10â»Â³â¶, Quran anti-persistent vs poetry persistent).
- **Honest caveat** (already in opportunity table): 3 additional witnesses (Benford, fractal dim, scale hierarchy) qualitatively concur but contribute negligibly under correlation correction (rank-p hard-floored at 1/7 by n_ctrl = 6).
- **Submission placement**: P2 main results (alongside X6 GIT theorem). **Provides a second independent paragraph-grade headline at p â‰ˆ 10â»Â³â´ on temporal dynamics**, complementing X6's geometric-information theorem on spatial geometry.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md:814-835`.

### 2.6 D7 — JuzÊ¾ smoothness `JUZ_J1_DOMINANT` (cross-scale liturgical-structure law)

- **Pre-empts**: *"Is the Mushaf-J1 extremum a one-off, or does it generalise across liturgical layers?"*
- **Answer (locked, 2026-04-25 02:00 UTC+02 ; `expD7_juz_partition_smoothness/`)**: Canonical 30-juzÊ¾ J1 = 234.90 vs random null mean = 382.18 Â± 61.38 â‡’ âˆ’2.40Ïƒ below null mean ; q = 2/1000 random size-preserving partitions ; verdict `JUZ_J1_DOMINANT`.
- **Cross-scale interpretation**: Surah granularity (114 partitions, 10â¶ perms) yields **strict global extremum** (A10, p < 10â»â¶). JuzÊ¾ granularity (30 partitions, 10Â³ perms) yields **dominant but not strict-extremum** (q = 0.002). Plausible: surah ordering culturally-curated to a strict optimum ; juzÊ¾ partition is a mechanical equal-recitation cut that lands near (not at) the optimum. **Both layers smoothness-aligned**.
- **D8 (á¸¥izb 60, rubÊ¿ 240, rukÅ«Ê¿ ~558) — deferred** (additional boundary lists not on disk).
- **Submission placement**: P2 main results, as second-axis cross-scale confirmation of A10 Mushaf J1.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md:669-682`.

---

## Â§3 — Target venue tree

Ranked by fit Ã— acceptance-probability Ã— time-to-decision, based on the submitted-result inventory at this date.

### 3.1 Tier-1 fits (recommended first submission targets)

| Package | Best fit | Why | Expected outcome | Time-to-decision |
|---|---|---|---|---|
| **P1** Diacritic universal | ***Computational Linguistics*** | Abrahamic orthography universal ; n=3 locked ; clean methodology paper ; matches journal scope exactly | Accept with minor revisions | 4-6 months |
| **P1** (alt) | ***Language*** | If they'd take it ; headline finding + cross-tradition extension via P4 would strengthen | Major revisions ; conditional accept | 6-9 months |
| **P2** Geometric-info-theoretic theorem (X6 + X3 + D7 + A10 + A3 + X7 closures) | ***Entropy*** (MDPI) | Open-access, scope-exact, fast turnaround ; **two independent ~10â»Â³â´ Brown-corrected witnesses** (X3 prose-extremum + X6 GIT) | Accept with minor revisions | 2-3 months |
| **P2** (alt — UPGRADED PROBABILITY) | ***PRX Information*** | Paths A/C/D + X7 closures pre-empt **five** referee objections (was three) ; X7 P2_OP1 + P2_OP3 closed-form proofs + X3 + D7 strengthen scope fit ; **promote ~50-70 % â†’ ~70-80 % accept** | 70-80 % accept | 6-9 months |
| **P3** LC3-70-U classifier | ***PLOS ONE*** | 1-D sufficient discriminator + explicit Bible-leakage analysis ; clean empirical paper | Accept with minor revisions | 2-3 months |
| **P3** (alt) | ***Digital Scholarship in the Humanities*** | Stylometric methodology angle ; more visible in Digital Humanities | Accept | 3-4 months |
| **P7 (NEW)** T_alt methodology refinement | ***PLOS ONE*** | Atomic methodology paper: "A CamelTools-free T-alternative for the QSF 5-D fingerprint, with length-conditioning" | Accept with minor revisions | 2-3 months |
| **P7** (alt) | ***Digital Scholarship in the Humanities*** | Length-adaptive feature engineering for stylometric classification of religious-vs-secular Arabic | Accept | 3-4 months |

### 3.2 Tier-2 fits (stretch, only with P4 in hand)

| Package | Stretch fit | Condition for submission |
|---|---|---|
| **P2 + P4** combined | ***PNAS*** | Requires P4 (Vedic + Avestan + Pali) landing with R âˆˆ [0.65, 0.75] ; then universal is cross-language-family not just Abrahamic. **X3 + X7 strengthen the case** — joint Brown p â‰ˆ 10â»Â³â´ + closed-form proofs are PNAS-grade independent of P4 |
| **P2 + P4** combined | ***Phys. Rev. E*** | Same condition ; framed as "information-theoretic universals across oral-transmission corpora". X7 P2_OP1 (RÃ©nyi-2 uniqueness) + P2_OP3 (TÂ² â†” KL) closed-form proofs are venue-fit |
| **P2 + P4** combined | ***IEEE Trans. Inf. Theory*** | Same condition ; framed as "bounded diacritic channel capacity across scripts". P2_OP3 closed-form proof is core to scope |
| **P2 + P7** combined (no P4 needed) | ***Phys. Rev. E*** (alt) | If T_alt promotion lands AND P4 deferred: "Length-adaptive information-theoretic discrimination of religious-vs-secular Arabic at 48Ïƒ" — even without P4, +1.33Ïƒ T_alt + X3 + X6 + D7 already sit at PRX-Inf-grade |

### 3.3 Not-targets (explicit)

- ***Nature*** / ***Science*** — project scope is too narrow, venue mismatch. `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\LOST_GEMS_AND_NOBEL_PATH.md:282-316` says so explicitly ; this memo concurs.
- ***Nobel venues*** — N/A per `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\prereg\PREREG_GAMMA_KOLMOGOROV.md:347-349`. Do NOT frame any submission around Nobel language.
- Theological venues — project deliberately makes no theological claims (per `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\prereg\PREREG_GAMMA_KOLMOGOROV.md:344-350`). Any venue asking for theological interpretation declines.

---

## Â§4 — Four/five papers or one? + canonical-T decision (decision requests)

### Option A — Five independent papers (SAFE, FAST) — was four ; X7 adds P7

P1 â†’ Comp. Ling. ; P2 â†’ Entropy ; P3 â†’ PLOS ONE ; **P7 â†’ PLOS ONE (NEW)** ; P4 (when ready) â†’ Language.

- **Pros**: each paper is atomic, small, low-risk. Each has a clear methodology claim. Rejection of any one doesn't sink the others. Fast turnaround on PLOS ONE / Entropy. Paper count is higher.
- **Cons**: no single paper carries the headline "Quran has a locked multi-axis structural fingerprint". Reviewers of paper N don't see papers 1..Nâˆ’1 unless cited. Cross-references are weaker.
- **Effort**: 4-6 weeks writing Ã— 5 = 20-30 weeks writing total, but parallel-able. Compute cost: zero incremental (everything is locked).
- **Recommendation**: default option for time-efficient shipping.

### Option B — One headline paper + supplementary

Single *PRX Information* or *IEEE TIT* submission combining P1 + P2 + P3 + **P7** under one umbrella claim: *"Multi-axis information-theoretic structural signature of the Quran vs secular Arabic and cross-Abrahamic scripture."*

- **Pros**: one big claim ; one bibliography entry ; forcing function on the synthesis narrative ; higher impact if accepted. **X7 + X3 + D7 promote acceptance probability ~50-70 % â†’ ~70-80 %** (five referee pre-empts, two independent ~10â»Â³â´ joint witnesses, two cross-scale liturgical-structure laws, closed-form info-theoretic derivations).
- **Cons**: ~20-30 % rejection probability at PRX Information / IEEE TIT (was ~30-50 %) ; 9+ months to first decision ; if rejected, the fallback is 5 separate papers anyway but delayed by 9 months. Writing effort is ~2-3Ã— a single paper (not 5Ã— — there's leverage).
- **Effort**: 10-14 weeks writing. Compute: zero incremental.
- **Recommendation**: now meaningfully tractable given X7 closures. Worth considering if P4 delivers.

### Option C — Hybrid (RECOMMENDED)

- **Week 1-4**: Submit P3 (LC3-70-U to PLOS ONE) + P1 (diacritic universal to Comp. Ling.) **+ P7 (T_alt to PLOS ONE)** in parallel. Three fastest venues, cleanest single-axis claims.
- **Week 2-6**: Run P4 (Vedic + Avestan + Pali) + P5 (Î¨_oral cross-corpus) compute. Both use the A2 pipeline infrastructure already locked.
- **Week 4-10**: Write P2 (geometric-info-theoretic theorem) incorporating Paths A/C/D + X7 closures + P4/P5 results if available. Target *Entropy* (safe ; ~95 % accept given current evidence) or *PRX Information* (stretch ; ~70-80 % accept given X7 + X3 + D7).
- **Week 10+**: If P4 delivered cross-language-family universal, write P2 + P4 combined for PNAS/*Phys. Rev. E*/*IEEE TIT*. If not, P4 ships as Comp. Ling. follow-up.

### Â§4.4 DECISION LOCKED — T_alt vs T_canon as canonical headline T

**Decision**: **C1 — Keep T_canon as canonical** (locked 2026-04-25 evening, UTC+02).

**Rationale**: at Î¦_M â‰ˆ 47.03Ïƒ-equivalent, the +1.33Ïƒ refinement to 48.36Ïƒ is statistically inert for any reviewer (both numbers are ~10Ã— above the particle-physics 5Ïƒ discovery threshold ; Fisher-tail p moves from 10â»â´â¸â° to 10â»â�°â·, both effectively zero in any defensible decimal expansion). The decision separates writing from bookkeeping cost: C1 unblocks P2 + P7 writing immediately with zero `results_lock.json` churn. C2 was the recommended path *only* if Option B / PRX TIT / PNAS had been the committed target ; we are not committed to that target. T_alt's value is preserved by being **the headline of P7** (atomic CamelTools-free methodology paper to *PLOS ONE*), which extracts every reviewer-pre-empt benefit of T_alt without disturbing P2.

**Effects of C1 lock**:

| Aspect | State |
|---|---|
| `results_lock.json` | UNCHANGED ; `Phi_M_hotelling_T2 = 3557.34` remains canonical |
| PAPER.md headline (Â§4.1) | UNCHANGED ; cites TÂ² = 3 557, ~47Ïƒ-equivalent, log10 p_F = âˆ’480.25 |
| RANKED_FINDINGS row 2 | UNCHANGED ; cites TÂ² = 3 557 |
| All cross-tradition references (LC2, etc.) | UNCHANGED |
| T_alt scalar (Î¦_M_alt = 3 868, log10 p_F = âˆ’507.80) | retained in `expParadigm2_OP2_T_alt_validation.json` ; **becomes P7 headline scalar** ; explicitly NOT promoted to lock |
| T_alt mention in P2 | becomes a one-paragraph robustness pre-empt: "a CamelTools-free alternative T_alt = H_cond(first_letter_of_last_word) âˆ’ H(end_letter) yields TÂ² = 3 868 (+8.7 %, +1.33Ïƒ at Band-A); see P7 for the standalone methodology treatment" |
| T_alt mention in P3 | one-line citation in supplementary as a CamelTools-free single-feature alternative |
| C2 / C3 status | C2 NOT TAKEN this cycle ; revisitable if Option B / PRX / TIT / PNAS becomes the target. C3 deferred to a future P8 methodology paper, not on the critical path. |

| Choice (decision matrix preserved for audit) | What it would have meant | Verdict |
|---|---|---|
| **C1 — Keep T_canon as canonical** | All papers continue citing Î¦_M = 3 557 / 47.03Ïƒ ; T_alt becomes P7 standalone | âœ… **CHOSEN 2026-04-25** |
| **C2 — Promote T_alt as Band-A canonical** | Î¦_M_Band-A = 3 868 / 48.36Ïƒ becomes new headline ; ~1-2 days bookkeeping | âŒ NOT TAKEN ; reopen iff Option B / PRX / TIT / PNAS becomes target |
| **C3 — Length-adaptive blend** | Î±(n) blend ; new locked scalar `Phi_M_blend` | âŒ DEFERRED to a follow-up P8 methodology paper |

**Reopen protocol**: should the project later commit to Option B (single PRX / TIT / PNAS umbrella paper), this decision should be revisited within Week 1 of that re-targeting and migrated to C2. The locking work is bounded: a `results_lock.json` write of `Phi_M_T_alt_band_A = 3867.79` + `Phi_M_T_canon_band_C = 1908` plus PAPER.md Â§4.1 + RANKED_FINDINGS row 2 amendments. Estimated bookkeeping time: 1-2 days. Decision authority: project lead.

**Status**: this section is now a **closed decision record**, not an open decision request. The rest of this memo is unaffected ; any downstream reader can treat Î¦_M = 3 557 as canonical for all v7.7+ submissions.

---

## Â§5 — 4-6 week timeline (Option C assumed)

Wall-clock, calendar weeks. Updated to include P7 in parallel with P1/P3.

| Week | P1 (Comp. Ling.) | P2 (Entropy / PRX Inf) | P3 (PLOS ONE) | **P7 (PLOS ONE — NEW)** | P4 + P5 (compute) |
|:--:|---|---|---|---|---|
| **1** | Outline + Â§1 Intro + Â§2 Methods ; fix `raw_loader.py:434` row[7] doc-bug | Outline + Â§1 Intro ; **finalise Â§4.4 T_alt-vs-T_canon decision** | Outline + Â§1 Intro + Â§2 Methods | Outline + Â§1 Intro (T_alt vs T_canon framing) | Data acquisition: Vedic Saá¹ƒhitÄ (á¹šgveda), Avestan Yasna, Pali Canon |
| **2** | Â§3 Results (A2 table locked) + Â§4 Discussion | Â§2 Methods + Â§3.1-3.3 (5-D fingerprint ; Î¦_M = 3557 / 47Ïƒ canonical) | Â§3 Results (LC3-70-U + 7-Bible-leakage) | Â§2 Methods (16-pair search) + Â§3 Results (T_alt validation table + band robustness) | Run A2 pipeline on 3 new scripts ; ~1 day compute |
| **3** | Â§5 Cross-references, supp. tables (Î¨_oral n=1 caveat) ; internal review | Â§3.4-3.6 (Paths A/C/D + X7 robustness) ; Â§3.7 (X6 GIT Brown p â‰ˆ 3 Ã— 10â»Â¹Â³) ; **Â§3.8 (X3 prose-extremum p â‰ˆ 6.7 Ã— 10â»Â³â´)** ; **Â§3.9 (D7 juzÊ¾ smoothness)** | Â§4 Discussion, supp. tables ; internal review | Â§4 Discussion (length-conditioning + Î±(n) blend as future work) ; internal review | Run P5 (Î¨ on Tanakh + Rigveda) ; ~2 hours compute |
| **4** | Submit to Comp. Ling. | Â§3.10 (A10 Mushaf J1 p < 10â»â¶) ; Â§3.11 (A3 STOT v2 4/5) ; **Â§3.12 (X7 P2_OP1 + P2_OP3 closed-form proofs)** ; Â§4 Discussion | Submit to PLOS ONE | Submit to PLOS ONE | If P4 R âˆˆ [0.65, 0.75] across 3 new scripts: promote P2 to PNAS/*Phys. Rev. E*. Else: ship as P1 follow-up |
| **5** | — | Supp. mat. (derived invariants: Î¨_oral, Î³_enrich, EL/EL_b ; all Tier-C from Â§1) ; internal review | — | — | Write P4 Results + Discussion ; ~1 week writing |
| **6** | — | Submit to Entropy (safe ; ~95 % accept) OR PRX Information (stretch ; ~70-80 % accept given X7 + X3 + D7) | — | — | Submit P4 to Comp. Ling. or Language |

**Total time to 5 submissions**: 6 calendar weeks from memo date (2026-04-25).
**Total incremental compute**: ~1.5 days (P4 + P5). T_alt validation already done — no extra compute for P7.
**Total writing effort**: ~5-6 person-weeks (was 4-5 ; P7 adds ~1 week).
**Blockers**: P6 (riwayat invariance, A4) remains data-blocked. *(Â§4.4 T_alt canonical decision LOCKED C1 on 2026-04-25 ; no longer a blocker.)*

---

## Â§6 — What this memo explicitly does NOT do

- **Does not introduce new empirical claims.** Everything cited is locked in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\integrity\results_lock.json` or a result JSON under `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\`.
- **Does not frame any submission as Nobel-grade.** Per pre-registration discipline (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\prereg\PREREG_GAMMA_KOLMOGOROV.md:347-349`) the honest ceiling is PNAS (stretch with P4), PRX Information / IEEE TIT (stretch without P4), or *Entropy* / *Computational Linguistics* / *PLOS ONE* (default).
- **Does not claim divine authorship.** Per `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\prereg\PREREG_GAMMA_KOLMOGOROV.md:348`. All results are stylometric.
- **Does not modify any locked scalar.** This memo is additive-only ; no entry in `results_lock.json` is touched. **Note**: T_alt validation result (Î¦_M_alt = 3868 / 48.36Ïƒ) is published in `expParadigm2_OP2_T_alt_validation.json` and explicitly NOT promoted to `results_lock.json` per the C1 lock in Â§4.4. T_alt becomes the headline of the P7 standalone methodology paper.
- **Â§4.4 decision LOCKED 2026-04-25**: C1 (keep T_canon canonical). The Option A / B / C choice (Â§4) remains user-driven ; default recommendation is Option C (Hybrid).

---

## Â§7 — Open risks, not blockers

- **P6 (riwayat invariance, A4)**: blocked on Warsh / Qalun / Duri text files. Auto-download disabled by design. Every published finding is currently "Hafs-specific until riwayat invariance lands". If `|Î”Q_COV| â‰¤ 0.02` across 3+ qirÄÊ¾Ät, every finding upgrades from Hafs-specific to Uthmanic-skeleton-level. If it fails, localises which reading carries the structural signal. 15-minute runtime once data is in place.
- **Î¨_oral n=1 â†’ n=3**: P5 is low-effort but a negative result (Î¨ â‰  0.83 on Tanakh or Rigveda) would downgrade the "oral-transmission optimality" framing. Acceptable risk ; does not kill any other paper.
- **Î³_gzip non-universality**: known, retracted. Any paper citing Î³ must wrap the `S10 / Â§2.5` retraction explicitly or it re-opens the landmine.
- **LC3-70-U Bible leakage**: 7/2509 leaks all from arabic_bible clustering with `exp33` narrative surahs. Not a bug ; is a publishable sub-claim. Explicit in P3.
- **A2 Greek row[7] vs row[9] doc-bug**: A2's locked result used row[7] directly (polytonic OGNTa). Any downstream consumer of `load_greek_nt()` via `src/raw_loader.py:433-434` operates on row[9] Latin transliteration. Separate doc-bug ; does not affect A2's locked numbers.
- **RESOLVED â€” T_alt vs T_canon canonical decision (Â§4.4 LOCKED C1, 2026-04-25)**: T_alt gives +8.7 % TÂ² / +1.33Ïƒ at Band-A but FAILS at Band-C (âˆ’4.4 %). C1 chosen: T_canon stays canonical (Î¦_M = 3 557 / 47.03Ïƒ remains the v7.7+ headline). T_alt becomes the headline of P7 (atomic methodology paper). Reopen iff target migrates to Option B / PRX / TIT / PNAS.
- **NEW — STOT independence caveat carried forward**: A3 STOT v2 4/5 PASS, but max pairwise |Spearman Ï| across {EL, VL_CV, H_cond, T} = 0.567 (exceeds pre-reg 0.3 independence threshold). Future paper writing must drop "5 independent gates" framing and present STOT v2 as a "5-fold sufficiency battery with known correlations".

---

## Â§8 — What to do in the next hour
1. **Decide Option A / B / C** (Â§4). *(Â§4.4 C1 LOCKED 2026-04-25 â€” no longer pending.)*
2. **If Option C (recommended)**: start P3 (LC3-70-U paper) outline today ; it's the fastest venue and uses a single locked scalar (AUC 0.9975). Fast validation of the submission pipeline.
3. **`results_lock.json` UNCHANGED** under C1. T_alt validation (Î¦_M_alt = 3 868) stays in `expParadigm2_OP2_T_alt_validation.json` and feeds P7 only. No Week-1 bookkeeping required.
4. **Fix `raw_loader.py:433-434` row[7] doc-bug** before any P4 compute — it doesn't affect A2's locked numbers, but downstream A4/A9/cross-scripture consumers need the correct polytonic column.
5. **Do NOT start P2 synthesis writing until P3 is submitted.** P3 is the dress rehearsal ; catches writing-style issues cheaply.
6. **P5 Î¨_oral compute** can run in a 2-hour background session any time this week ; the result decides whether Î¨_oral enters the P2 paper as a "locked n=3 universal" or as a "future-work footnote".
7. **P7 outline drafting** can start today in parallel with P3 — both use locked numerics and need no additional compute.

---

*Memo frozen 2026-04-25 ; revised 2026-04-25 ~10:30 UTC+02 to sync with X7 Paradigm-Stage 2 closures (P2_OP1 PROVED, P2_OP3 PROVED + Edgeworth, P2_OP2 T_alt refinement), X3 prose-extremum theorem, D7 juzÊ¾ smoothness in `OPPORTUNITY_TABLE_DETAIL.md`. Re-revised 2026-04-25 evening to lock Â§4.4 as **C1 (keep T_canon canonical)** ; T_alt becomes P7 headline. Companion: `OPPORTUNITY_TABLE_DETAIL.md` (tiered catalogue of 130+ findings) and `AUDIT_MEMO_2026-04-24.md` (code-level audit). No empirical re-runs were required to produce this revision. Decision request in Â§4 (Option A/B/C) remains user-driven ; Â§4.4 is now a closed decision record (C1 chosen).*
