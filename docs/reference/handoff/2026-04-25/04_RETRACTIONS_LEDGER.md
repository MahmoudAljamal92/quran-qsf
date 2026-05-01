# 04 — Retractions Ledger (53 retractions + 7 failed-null pre-registrations as of v7.9-cand patch H V3, do not reopen)

> ⚠ **v7.9-cand SUPERSESSION NOTICE (2026-04-26 night — patch G post-V1 sync)**: Three new retractions added under patch G (R51, R52, R53) bringing the total to 53 retractions + 2 failed-null pre-registrations. R51 + R52 were doc-hygiene formalisations of existing receipt verdicts; **R53 is a substantive falsification**: the V1-scope run of `exp95e_full_114_consensus_universal` fired the pre-registered `FAIL_per_surah_floor` branch and revoked the universal-extrapolation hypothesis (H37 / finding F54). The original Q:100 closure F53 is **unaffected** — the embedded regression sub-run inside `exp95e` reproduces K=2 = 1.000 and gzip-solo = 0.9907 exactly.
>
> **Patch G post-V1 (2026-04-26 night) — F53 universal-scaling falsified**:
> - **R53** (patch G post-V1) — F53 multi-compressor consensus K = 2 across {gzip-9, bz2-9, lzma-preset-9, zstd-9} with τ frozen from `exp95c` does **not** scale to all 114 Quran surahs at recall ≥ 0.999 / per-surah ≥ 0.99 under V1 scope. `exp95e_full_114_consensus_universal` V1 verdict `FAIL_per_surah_floor`: aggregate K=2 = 0.190 (target ≥ 0.999); 70 / 114 surahs at K=2 = 0; only 8 / 114 at K=2 ≥ 0.999 (Q:093, Q:100, Q:101, Q:102, Q:103, Q:104, Q:108, Q:112 — all short late-Meccan, `total_letters_28 ≤ 188`); ctrl-null FPR K=2 = 0.0248 ✓; embedded Q:100 regression K=2 = 1.000, gzip-solo = 0.9907 ✓. **Preserved**: F53 Q:100 closure (§4.42); ctrl-null FPR control; the K=2 rule itself. **Killed**: any reading of F53 as a Quran-universal forgery detector under the locked τ thresholds and V1 enumeration. **Mechanistic envelope (post-hoc observation, NOT a claim)**: across 114 surahs, `log10(total_letters_28) → K=2 recall` Pearson r = −0.85; phase boundary `total_letters ≤ 188` perfect / `≥ 873` zero. Pre-registered envelope replication launched as `exp95f_short_envelope_replication` (PREREG SHA-256 `83a7b25ac69e703604a82be5c6f7c1d597ccd953f07df7f624ccc1c55d972a14`); H39 ladder fixed *before* the SHORT receipt is opened.
>
> **Patch G earlier (2026-04-26 night) — risk-vector closures**:
> - **R51** (patch G) — γ universality across compressor families — `exp103` `FAIL_not_universal`; CV_γ = 2.95; γ_gzip = +0.072, γ_bzip2 = −0.048, γ_zstd = −0.029, γ_brotli = +0.087; signs disagree. **Preserved**: γ_gzip = +0.0716 as a length-controlled gzip-family-specific scalar. **Killed**: the Kolmogorov-derivation programme (`docs/PREREG_GAMMA_KOLMOGOROV.md` Theorem 1). **F53 is unaffected**: K = 2 multi-compressor consensus is *designed for* compressor disagreement (note: F54 was *separately* falsified post-V1 as R53; that falsification was per-surah recall, not γ-universality).
> - **R52** (patch G) — Ψ_oral ≈ 0.836 as a 5/6 oral-tradition universal — `expX1` `NO_SUPPORT`; 0/5 non-Quran corpora produce Ψ in the loose pre-registered band [0.65, 1.00]; cross-corpus spread is two orders of magnitude. **Preserved**: Quran Ψ_oral = 0.836 as a within-corpus T7-derived constant. **Killed**: the Class-2 Law-Closure timeline that depended on Ψ_oral as a cross-tradition universal.
>
> **Patch G also pre-registers H38 (cross-tradition F53)** at `experiments/expP4_F53_cross_tradition/PREREG.md` as a **BLOCKED-on-corpus-acquisition** stub; no scoring code may execute until the 5 native peer corpus pools (Hebrew narrative, Koine Greek prose, Pali Vinaya/commentaries, Sanskrit prose/Vedic peers, Avestan ritual) are ingested under SHA-256 lock discipline. **No claim about cross-tradition F53 universality is made by the v7.9 paper.**
>
> **Earlier patch F retractions (preserved)**:
> - **R48** (patch B) — `%T_pos` cross-tradition under language-agnostic T_lang — `FAIL_QURAN_NOT_HIGHEST`; the 397× ratio is T_canon-Arabic-morphology-specific
> - **R49** (patch B) — closed-form Σp̂² = 1/2 corpus-pool — `FAIL_NOT_HALF`; per-surah median formulation survives at `PASS_at_half`
> - **R50** (patch E, 2026-04-26) — patch B claim that full-Quran T² = 3 685 is HIGHER than band-A T² = 3 557 → **REFRAMED to STABLE**: bootstrap 95 % CI [3 127, 4 313] includes the band-A T²; the two values are statistically indistinguishable.
>
> **Patch F (2026-04-26 night) — Category K failed-null pre-registrations (NOT retractions)**:
> - **FN01** — `exp95_phonetic_modulation` `FAIL_ctrl_stratum_overfpr`
> - **FN02** — `exp95b_local_ncd_adiyat` `FAIL_window_overfpr`
>
> **Why FN01/FN02 are NOT retractions**: neither was ever a standing claim. Tracking them in Category K of `RETRACTIONS_REGISTRY.md` is for **discoverability only**, not as reversals.
>
> **Patch H V3 (2026-04-28 evening) — H39 envelope replication COMPLETE**:
> - **FN07** — `exp95f_short_envelope_replication` `FAIL_envelope_phase_boundary`. H39.1 (correlation) PASSES at full V1 strength (Pearson r = −0.8519); H39.2 (phase boundary) FAILS at one surah — **Q:055 Al-Rahman** (`total = 1 666`, K=2 = 0.267 > 0.10). 71/72 upper-band and 21/21 lower-band surahs obey. Per H39 PREREG §2.3, **no F-number opened**; the V1 envelope remains exploratory only.
>
> **Patch H V2 (2026-04-28) — Phase 2 COMPLETE, F57 stamped PASS**:
> - **FN03** — `exp98_per_verse_mdl` `FAIL_quran_not_top_1` (C4 first op-test failure)
> - **FN04** — `exp97_multifractal_spectrum` `FAIL_audit_hurst` (C5 first op-test failure)
> - **FN05** — `exp100_verse_precision` `FAIL_audit_A2` (C4 second op-test failure)
> - **FN06** — `exp101_self_similarity` `FAIL_not_rank_1` (C5 second op-test failure)
> - R54–R56 added under patches G post-V1-iii through G post-V1-vi (MSFC sub-gate + joint-extremum closures).
>
> Total **retractions = 53** (R01–R56, with R54–R56 from patch G). Failed-null pre-registrations: **7** (FN01–FN07). Grand total ledger entries: **60**. Defer to canonical source `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md`.

**Authority**: this is a compact form of `docs/reference/findings/RETRACTIONS_REGISTRY.md` (canonical **53-retraction + 7 failed-null** source as of v7.9-cand patch H V3). For any retraction below, do NOT propose to reopen it without **fresh data AND fresh methodology**. Failed nulls (FN01–FN07) are not subject to a re-opening protocol because they are not reversals of any standing claim.

**Why this matters**: the project's single biggest credibility asset is its retraction discipline. Each row below represents a once-claimed result that was disproven by the project itself or by external review.

---

## Compact 47-row table

| # | Claim | Verdict | Evidence | Date |
|--:|---|---|---|---|
| R01 | Golden-ratio φ-fraction ≈ 0.618 | NOT REPRODUCED ; observed −0.915 ; formally NULL in `exp72` | `T29_phi_frac` | v5 / v7.7 |
| R02 | Joint Meccan-Medinan F > 1 | FALSIFIED at joint threshold (F_M = 0.797, F_D ≈ 0.84) | pre-reg Test B | v5 |
| R03 | Rhyme-swap P3 d = −0.28 | NOT REPRODUCED at advertised magnitude (observed −0.16) | T20 / D21 | v5 |
| R04 | Law IV VERU end-root uniqueness as Quran-unique | FALSIFIED ; controls beat Quran (d = −1.013) | ADIYAT audit | 2026-04-20 |
| R05 | Scale-invariant universal law at all 5 scales | RETRACTED ; only 3/5 scales survive | `exp28` | 2026-04-20 |
| R06 | Cascade product-code P = 0.82–0.90 | RETRACTED ; measured 0.137 | `exp29` | 2026-04-20 |
| R07 | Char-scale bigram-sufficiency law | NOT REPRODUCED ; Quran rank 2/7 | `exp27` | 2026-04-20 |
| R08 | Tension-Asymmetry "law" | FALSIFIED — algebraically circular | `exp08` | v5 |
| R09 | R3 "Quran 76 % stronger than next scripture" | FALSIFIED ; Tanakh z = −15.29 > Quran z = −8.92 | `exp35` | 2026-04-20 |
| R10 | T6 Complementarity as Quran-unique | RETRACTED ; poetry_jahili 14.7 % | HONEST_STATUS | v5 |
| R11 | Variational principle as Quran-unique | RETRACTED ; Greek NT 65.6 % > Quran 59.7 % | HONEST_STATUS | v5 |
| R12 | D7 self-prediction law | RETRACTED ; cv_r² = −42.1, holdout p = 0.90 | HONEST_STATUS | v5 |
| R13 | Onomatopoeia O-index | RETRACTED ; held-out t = −0.48, p = 0.68 | `exp04` | v5 |
| R14 | Sub-class tight clusters | RETRACTED ; solid null | `exp05` | v5 |
| R15 | Criticality exponent as Quran-unique | RETRACTED ; solid null | `exp02` | v5 |
| R16 | Muqattaat topological keys | RETRACTED ; χ² p = 0.4495 | F4 | v5 |
| R17 | Global Hurst word-lengths Q-unique | RETRACTED ; gap too small vs Hadith | F1 | v5 |
| R18 | LPEP Quran fingerprint | RETRACTED ; Q rank 2/7 (ksucca higher) | `exp37` | v5 |
| R19 | CCAS letter-transition Q-specific | RETRACTED ; null / wrong direction | `exp38` | v5 |
| R20 | R9 cross-scale VIS direction | FALSIFIED (reversed) ; VIS = 0.485 < 1 | Ultimate-2 | 2026-04-20 |
| R21 | Gematria / abjad weight | DEAD END | archive | pre-v5 |
| R22 | Base-19 / base-7 numerology | DEAD END | archive | pre-v5 |
| R23 | Shannon-Aljamal γ(Ω) equation | RETRACTED — tautology | LAW_CANDIDATES | v5 |
| R24 | Half-life law S17 | NOT CONFIRMED | LAW_CANDIDATES | v5 |
| R25 | T28 root-Markov-order verbal claim | VERBAL CLAIM RETRACTED ; sign-flipped scalar | `exp28` | 2026-04-20 |
| R26 | Gem #4 multi-level Hurst ladder (monotone) | RETRACTED ; H_delta anti-persistent ; all 6 ctrl share ladder shape | `exp96_hurst_ladder` | 2026-04-22 |
| R27 | A2 universal R ~ 0.70 (script-universal) | FALSIFIED ; 6-corpus spread = 0.92 ; reframed as Abrahamic-script typology | `expP4_diacritic_capacity_cross_tradition` | 2026-04-25 |
| R28 | Ψ_oral = H(harakat\|rasm)/(2·I(EL;CN)) ≈ 5/6 cross-tradition | FALSIFIED ; 0/5 oral corpora in [0.65,1.00] ; Quran 0.836 = n=1 numerical coincidence | `expX1_psi_oral` | 2026-04-25 |
| R29 | Adjacent-verse anti-repetition Gem #2 (d = −0.475) | FAILS ; observed d = +0.330 (sign reversed) | `exp67_adjacent_jaccard` | 2026-04-21 |
| R30 | Ring-composition / chiasmus as Quran-wide signature | NULL at lexical AND feature level (Fisher p = 0.604) | `exp86`, `expE19` | 2026-04-21/23 |
| R31 | Small-world / scale-free network-topology uniqueness | NULL ; all 6 Arabic corpora satisfy small-world within CIs | `exp84` | 2026-04-21 |
| R32 | Prime-number structural signature | NULL ; runs-test z = −0.71, p = 0.479 | `exp73` | 2026-04-21 |
| R33 | L1 — SCI as Quran-unique composite | DIRECTIONAL ONLY ; margin within ordinary range | `ULTIMATE_REPORT.json::L1` | 2026-04-20 |
| R34 | L3 — Free-energy minimum as Quran-unique | NOT REPRODUCED ; poetry families rank lower | `ULTIMATE_REPORT.json::L3` | 2026-04-20 |
| R35 | L4 — Aljamal invariance Ω·d ≈ const | FALSIFIED ; cross-corpus CV = 1.551 | `ULTIMATE_REPORT.json::L4` | 2026-04-20 |
| R36 | L6 — Empirical γ(Ω) slope | NULL ; b = −0.00428 indistinguishable from zero | `ULTIMATE_REPORT.json::L6` | 2026-04-20 |
| R37 | L7 — Ψ ranking is scale-invariant | DISCLOSED AS SCALE-VARIANT | `ULTIMATE_REPORT.json::L7` | 2026-04-20 |
| R38 | E1 transmission-noise EL-survival as Quran-specific | RETIRED ; noise model too weak | `exp21` | 2026-04-20 |
| R39 | R5 adversarial G4 forgeries unforgeable | CLARIFIED ; 50 % of EL+RD-aware Markov forgeries below Φ_M | v7.1 audit | 2026-04-20 |
| R40 | Char-root GAP as secondary fingerprint | NOT SUPPORTED ; Q rank 4/7 | `exp28` | 2026-04-20 |
| R41 | Adiyat ع→غ-specific 8×–20× amplification | DOWNGRADED ; R2 byte-exact identical windows for ع→غ ; macro-claim holds for B/C variants | `exp29` | 2026-04-20 |
| R42 | Φ_sym (R11 symbolic) as Adiyat edit-detector | STRUCTURAL BLINDNESS ; ΔΦ_sym < 0.33σ_Q | `exp34` | 2026-04-20 |
| R43 | D02 / D28 / S1 legacy Phi_M Cohen d | DEPRECATED (biased) ; supersede with `Phi_M_hotelling_T2` | `ULTIMATE_SCORECARD` | v5 |
| R44 | D06 Turbo gain | WEAKENED (1.644) | `ULTIMATE_SCORECARD` | v5 |
| R45 | D27 LEGACY Abbasi (non-directional) | DEPRECATED ; use `D27_directional` | `ULTIMATE_SCORECARD` | v5 |
| R46 | D05 I(EL;CN) unit-level | FALSIFIED at unit-level (0.09957 vs 0.1) ; corpus T7 = 1.175 still PROVED | `ULTIMATE_SCORECARD` | v5 |
| R47 | D18 adjacent-diversity 100 % | RETRACTED in v2 (10.6 percentile observed) | PAPER §5 | v2 |
| R48 | VL_CV_FLOOR = 0.1962 in archived `build_pipeline_p1.py` | METHODOLOGICAL-LEAK DISCLOSURE ; archived legacy code only ; active 5-D pipeline unaffected. **Provenance now found**: 1/√26 where 26 = MSA consonantal phonemes (`expE20` + `expC2`) | `exp61`, `expE20`, `expC2` | 2026-04-21/23/25 |
| R49 | Reed–Solomon-like self-correcting error-correction code | NULL_UTF8_CONFOUND ; signal vanishes on compact 32-letter alphabet | `expE18_reed_solomon` | 2026-04-23 |

(Numbering above follows the canonical registry; rows R45/R46 in the registry correspond to D27 + D05 ; R47 in the registry is the Reed-Solomon entry. The numbering is left as published.)

---

## Categorisation

| Category | Count | What it means |
|---|---:|---|
| A — Named statistical laws that failed under stricter null | 26 | The bulk ; classical "go-to" stylometric / numerological claims |
| B — v7.7 sprint retractions (2026-04-21) | 4 | Adjacent-verse anti-repetition, ring composition, small-world topology, prime-density signature |
| C — EXPLORATORY metrics downgraded by external review (Apr 2026) | 5 | L1/L3/L4/L6/L7 from `ULTIMATE_REPORT.json` |
| D — Scope / mechanism disclosures (not retractions of scalars) | 5 | E1 noise model, R5 forgeries, char-root GAP, Adiyat ع→غ, Φ_sym blindness |
| E — Deprecated legacy locked scalars | 4 | D02/D28/S1 biased; D06 Turbo weakened; D27 non-directional; D05 unit-level |
| F — Historical (preserved for audit trail) | 1 | D18 — retracted in v2 already |
| G — Methodological-leak disclosure (active pipeline unaffected) | 1 | VL_CV_FLOOR provenance now confirmed (1/√26) |
| H — Tier 5 closures (2026-04-23) | 1 | Reed-Solomon UTF-8 confound |
| I — Cross-tradition phase additions (2026-04-25) | 2 | A2 R-universal, Ψ_oral 5/6 universal |

**Total: 47 distinct retractions** (registry numbering keeps the legacy 47-row scoreboard ; the cross-tradition phase additions reused the slot count ; canonical source is `RETRACTIONS_REGISTRY.md`).

---

## Reopening protocol

Per `RETRACTIONS_REGISTRY.md`:
1. **Fresh data** (not a re-analysis of existing cached results)
2. **Pre-registered null hypothesis** with explicit gates
3. **PR-style review** to this file ; verdict logged as a NEW entry with `[REOPENED]` prefix
4. Never silently overwrite an existing entry

**Reverse-dependency rule**: if a new claim in `PAPER.md`, `RANKED_FINDINGS.md`, or any experiment relies on a retracted claim, the new claim is automatically suspect and must be re-derived from non-retracted scalars.

---

## What this list deliberately preserves

It deliberately **does not** delete the retracted scalars from any locked file. The locked scalar values stay in `results_lock.json` for audit-trail integrity, but the **interpretation** is downgraded to "DEPRECATED" or "FALSIFIED". This is an intentional design choice: the project's reproducibility-first ethic depends on never silently rewriting history.

---

*Source: `docs/reference/findings/RETRACTIONS_REGISTRY.md` (**50 entries** as of v7.9-cand patch E; R47 added 2026-04-23, R48–R49 in patch B, R50 in patch E) ; cross-references in `docs/PAPER.md §5`, `docs/reference/findings/RANKED_FINDINGS.md §5`, `CHANGELOG.md`, `results/ULTIMATE_SCORECARD.md`. Last revised 2026-04-25 evening to include the cross-tradition phase additions (R27, R28).*
