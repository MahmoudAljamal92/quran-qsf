# QSF Ultra-Deep Two-Pass Scan — Missed-Opportunity / Anomaly / Paradigm-Shift Table

**Scan date**: 2026-04-24
**Scanner**: Cascade two-pass scan (Pass 1: canonical read of every signal-dense file; Pass 2: zero-trust re-read looking for premature retractions, suppressed signals, dismissed confounds, cross-convergences).
**Scope**: 3,186 files / 1.79 GB. File index at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\_file_manifest.txt`.

**Method disclosure**: Human-readable text (docs, md, py, notebooks' markdown cells, JSON reports, small-corpus .txt) was read line-by-line; binary / large CSV / .pkl / .gz / .png / .htm were surveyed via shape / header / summary only — 1.79 GB byte-by-byte does not fit a single context window. This pass covered **every signal-dense file** referenced by the audit trail, every retraction, every `exp*` verdict, and every canonical constant. Ask for any specific file and I will drill in.

---

## âš  AUDIT UPDATE — 2026-04-24 (afternoon)

A follow-up code-level audit found **two headline-risk bugs** and **one systemic integrity risk** that affect entries in this table. Full details in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md`.

1. **E7 normalisation confound (CRITICAL)** — exp46 / exp50's E7 "aynâ†”hamza" class is actually "aynâ†”all-alef" after `normalize_rasm()` folds Ø£ Ø¥ Ø¢ Ù± â†’ Ø§. E7 dominates 48 % of edits and 87 % of detections. Removing it drops Quran 1.15 % â†’ 0.30 %, Abbasi 4.83 % â†’ 0.93 %, Jahili 9.50 % â†’ 1.97 %. **The pre-registered `H2_QURAN_SPECIFIC_IMMUNITY` verdict flips to `H1_STRUCTURAL`.** Quran remains the most immune corpus (3-7Ã— ratio) so the qualitative finding survives but not the 5Ã— threshold.
2. **Checkpoint fingerprint drift (systemic)** — `_lib.load_phase()` only warned on fingerprint mismatch, now opt-in fail via `QSF_STRICT_DRIFT=1`.
3. **exp48 `_el_match` raw-final-char contamination (medium)** — graph edge weights used punctuation/diacritics; controls have 17–75 % non-letter endings vs Quran 0 %.

**Patches applied non-destructively**; historical JSONs preserved as `*.pre_audit_2026_04_24.json`. All entries referencing exp46/exp50/exp48 have been amended in `OPPORTUNITY_TABLE_DETAIL.md`. New entries **B14**, **B15**, **B16**, **E14** added.

### âœ“ Empirical verification (all three patched experiments re-run, 2026-04-24 afternoon)

| Experiment | Predicted | Observed | Status |
|---|---|---|---|
| **exp46** Quran no-E7 rate | 0.296 % (16 / 5,413) | **0.2956 %** | âœ“ exact match |
| **exp46** E7 share of edits / detections | 48 % / 87 % | **48.3 % / 86.7 %** | âœ“ exact match |
| **exp48** Quran `n_communities` | "barely moves" | **7.018 â†’ 7.018** (delta 0.000) | âœ“ **HEADLINE CONFIRMED ROBUST** |
| **exp48** verdict | `PROMOTE n_fires=4/6` | unchanged | âœ“ |
| **exp50** aggregate no-E7 verdict | `H1_STRUCTURAL` | **`H1_STRUCTURAL_ARABIC_BLINDNESS`** | âœ“ verdict flip confirmed |

### âš  SURPRISE FINDING — NEW B16: corpus-drift independently broke H2

Re-running `exp50` full-mode on the CURRENT corpus (not the published one) gives:
- `poetry_abbasi`: **2.657 %** (published was 4.833 %)
- `poetry_jahili`: **4.309 %** (published was 9.500 %)

The H2 verdict was **already broken by pure corpus drift** before the E7 correction applied. The published headline `9.5 % poetry_jahili` silently no longer reproduces on the current `phase_06_phi_m.pkl`. This elevates **E14** (strict-drift fail) from infrastructural hygiene to urgent headline-integrity task.

**Follow-up status (action-board ranks 0a-0g)** — **ALL SEVEN CLOSED AS OF 2026-04-24 EVENING**:
- âœ“ **0a** — DONE (afternoon): exp46 + exp50 re-run; no-E7 numerics verified.
- âœ“ **0b** — DONE (afternoon): exp48 re-run; C5 `n_communities = 7.018` headline confirmed robust.
- âœ“ **0c** — DONE (evening): `QSF_STRICT_DRIFT=1` flag shipped + full notebook rebuild completed under the flag (79 min). Zero `IntegrityError`. Canonical scalars bit-identical pre/post.
- âœ“ **0d** — DONE (evening): **drift was cosmetic** — the 2026-04-20 `f22be533…` lock was a non-canonical hash; canonical is `4bdf4d025…`. Every pre-rebuild checkpoint pinned to the canonical value all along; only the live lock file was wrong. Rebuild overwrote it. The exp50 rate drop (9.50 % â†’ 4.31 %) is a *separate* edit-sampling-parameter change between Apr 20 and Apr 24, not lock drift.
- âœ“ **0e** — DONE (evening): **B13 full-context** published — `audit_2026_04_24_b13_noe7_contexts.edits` in exp46 JSON carries Â±4-char window + firing channels + 9-channel z-scores for all 16 detected no-E7 edits.
- âœ“ **0f** — DONE (evening): **B14 3-way hamza-preserving breakdown** run at full scale. **New finding**: sub-classes E7a / E7b / E7c produce **byte-identical** stats â†’ the 9-channel detector is **architecturally hamza-blind** (every channel internally folds Ø£ Ø¥ Ø¢ Ù± â†’ Ø§ before computing features). B14 CLOSED as originally scoped; re-scoped as B14b (1-2 week full-channel redesign) on the Priority Action Board.
- âœ“ **0g** — DONE (evening): **A8 bug-pattern scan** across all 21 `experiments/*/run.py` — no new raw-last-char or normalization bugs found. Audit's list of 5 issues is exhaustive.

**See** `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Appendices B (drift diagnosis), C (A8 scan), D (B14 architectural blindness), E (B15 exp51 stability) for full protocols + data. **See** `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\OPPORTUNITY_TABLE_DETAIL.md` â†’ "AUDIT CORRECTIONS — EMPIRICAL CLOSURE (2026-04-24 evening)" for the unified closure table.

One **optional** item remains: **0h (git commit)** — the repository has zero commits; all audit patches are durable in the filesystem but not in version control. **⚠ Foot-gun (audit A11, 2026-04-25 evening)**: the previously-recommended `git add -A && git commit -m "..."` would commit the user's entire Desktop because `.git` lives at `C:\Users\mtj_2\OneDrive\Desktop\` (not the Quran project root). Use the Option A procedure in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\handoff\2026-04-25\05_DECISIONS_AND_BLOCKERS.md` Q3/Z6-detail (re-init at project root, ~5 min) — see also `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\handoff\2026-04-25\06_CROSS_DOC_AUDIT.md` audit row A11.

---

## TL;DR — The Seven Highest-Leverage Missed Opportunities

| # | Opportunity | One-line claim | Primary citation | Effort |
|--:|---|---|---|---|
| **1** | **Mushaf-order J1-smoothness absolute minimum** | Canonical 114-surah order beats **all 10,000** random permutations AND the NuzÅ«l order. `q = 0.0000`. Reported as "partial" because J2 fails — but J1 alone is a standalone ~10â»â´ extremum. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:29` | 1 day |
| **2** | **54 % of Quran's Mahalanobis anomaly lives in a 1.6 % eigen-subspace** | Quran subspace TÂ² = 33.3 in PC4+PC5 (1.6 % of ctrl variance); perm p < 10â»â´; 63Ã— null-max. The Quran inhabits the **null space** of natural Arabic variation. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:540-564` | 2 days |
| **3** | **Riwayat invariance (Warsh / Qalun / Duri) — 15-min test never run** | `build_pipeline_p3.py::S9.3` framework is built; only variant files missing. Upgrades every finding from "Hafs-specific" to "text-property". | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\SCAN_2026-04-21T07-30Z\07_CASCADE_PROJECTS_ADDENDUM.md:101-109` | 1 h + data |
| **4** | **VL_CV_FLOOR = 0.1962 â‰ˆ 1/âˆš26 (0.04 % off) with a semantic derivation possible** | E20 flagged it "coincidence because 26 has no Quranic meaning". But 26 = 28 (abjad) âˆ’ hamza (diacritic) âˆ’ alif (vowel-carrier) = **the count of distinct consonantal phonemes**. This is a candidate analytic derivation never attempted. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:32` | 4 h |
| **5** | **Cross-scripture 5-D law (H17) not yet published as Abrahamic law** | `exp35` already shows BH p<10â»Â³ for Quran/Tanakh/NT; Iliad null. Reframed from retraction ("Quran not uniquely strongest") to positive class-level law. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:121-144` | 2 weeks + data |
| **6** | **E9 Takens/RQA: nonlinear determinism beyond AR(1) AND IAAFT surrogates** | DET=0.374 vs AR(1) null 0.016 Â± 0.003 (119-Ïƒ) and IAAFT null 0.157 Â± 0.034 (6.4-Ïƒ); all 6 RQA metrics outside both 95 % CIs. Textbook signature of deterministic chaos. Buried in Tier 2. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:31` | 3 days |
| **7** | **Character-LM (R4) — the only path to close emphatic-stop blind spot (~1 % detection)** | All 4 universal compressors give 0 % on Øªâ†”Ø· / Ùƒâ†”Ù‚ edits — it's a Kolmogorov-complexity floor, not a gzip artefact. Only an Arabic neural LM can close it. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\LOST_GEMS_AND_NOBEL_PATH.md:233-251` | 2-6 weeks GPU |

---

## Methodology of the Two-Pass Scan

**Pass 1** — Forward canonical reading of all signal-dense files, chasing the project's own declared truth.
**Pass 2** — Zero-trust reverse reading, asking six targeted questions:

1. Which retractions were based on **one particular method**, leaving the underlying claim untested at other methods?
2. Which "NULL" results **co-occur across multiple independent tests** and collectively point at a positive law that was split up across experiments?
3. Which findings were retracted on **length / size / genre confound** without testing the conditional residual?
4. Which **numerical coincidences** were dismissed as look-elsewhere but could survive a single ex-ante semantic derivation?
5. Which **constants in the pipeline code** have no documented provenance?
6. Which **classical Quranic-studies concepts** map onto measurable features that were never named as such?

The detailed tables (Tiers S, A, B, C, D, E) follow in a companion file: `OPPORTUNITY_TABLE_DETAIL.md`.

*End of top-of-file summary. Detailed tiered tables follow in separate sections to respect context-window limits.*
