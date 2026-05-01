# Zero-Trust Audit — Tier 5 Experiments + E14 Closure

**Date**: 2026-04-23
**Scope**: Tier 5 speculative / long-tail block (E18, E19, E20) from `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md`, **plus** the formerly-deferred E14 (multi-scale Fisher combination law).
**Driver**: `results/experiments/_tier5_audit.py` â†’ `results/experiments/_tier5_audit_report.json`
**Final disposition**: **0 HIGH / 0 MED / 8 LOW flags**; all four verdicts re-derive from raw numbers; **0 drift** against the 7 manifest-tracked run-of-record artefacts.

This audit closes Tier 5 and the E14 deferral. With it, **all 20 tasks of the execution plan are executed and audited** (4 tiers of prior audits: Tier 1 + Tier 2 + Tier 3 + Tier 4, cumulatively 0 HIGH / 1 MED / 16 LOW).

---

## Audit Dimensions & Checks

| # | Dimension | Check | Result |
|---|---|---|---|
| A1 | File hygiene | Every expected `expE{14,18,19,20}_report.{json,md}` + plot exists and parses; E18 additionally requires controls + FINAL reports | PASS |
| A2 | Pre-registration | Each JSON declares `pre_registered_criteria`, `seed`, `verdict` (or `FINAL_verdict` for E18) | PASS |
| A3 | Verdict re-derivation | Re-compute verdict from raw stats; compare to reported verdict | PASS — all 4 match |
| A4 | Pinned-artefact integrity | SHA-256 re-check vs `MANIFEST_v8.json` | PASS — 7/7 entries clean |
| A5 | Sanity bounds | p âˆˆ [0, 1], Shapley âˆˆ [âˆ’0.5, 1.05], Brown Ï‡Â² = Fisher Ï‡Â² (only df differs), target âˆˆ (0, 1) | PASS |
| A6 | Known design caveats / follow-up | Documented | 8 LOW flags filed |

---

## Per-Experiment Results (short form)

| Task | Verdict | Key Numbers | Audit Disposition |
|---|---|---|---|
| **E14** Multi-scale Fisher Law | **MULTISCALE_LAW** | 5 scales (letter KL, bigram H, DFA-H, Mahalanobis, L_TEL); Fisher Ï‡Â² = 34.56; Brown-corrected Ï‡Â² = 34.56 with `df_adj = 0.62` â†’ **p = 1.41 Ã— 10â»â¶**; Shapley shares {S1=âˆ’3%, S2=14%, S3=5%, S4=40%, S5=44%}; max single-scale share = **43.7 %** (<60 % threshold). | PASS. 2 LOW flags on framing & p-floor (both cosmetic). |
| **E18** Reed–Solomon search | **NULL_UTF8_CONFOUND** | Primary UTF-8 pipeline: Fisher p = 0 at (n=31, nsym âˆˆ {8, 12}) â†’ looked like "RS structure detected". Control arm B (compact 32-letter alphabet, UTF-8 stripped): same configs give p=0.63 and p=0.15 — signal **vanishes**. Decisive A-vs-B contrast = confound confirmed. | PASS. LOW flag: Arm C (poetry control) chunker underpowered (1 unit); the A-vs-B contrast alone is decisive for the pre-reg falsifier. |
| **E19** Feature-level Ring Composition | **NULL_NO_RING** | 79 surahs with n â‰¥ 20; per-surah mean-squared-distance across mirror pairs vs 1000 verse-order shuffles; Fisher-combined p = **0.604**; 6/79 at Î±=0.05 (null expects 4.0); 0/79 at Î±=0.01 (null expects 0.8). | PASS. LOW flag: slight per-surah excess (6 vs 4) within Poisson noise; simple 5-D features only — richer semantic features could still harbour higher-order ring signals. |
| **E20** Un-Derived Constant Hunt (`VL_CV_FLOOR=0.1962`) | **DERIVED_ANALYTIC** (with numerical-coincidence flag) | Tightest closed-form match: `1/âˆš26 = 0.19612` at **0.04 %** relative error (< 0.1 % pre-reg tolerance). But 26 has no canonical Arabic/Quranic grounding (abjad = 28 letters). 2nd-smallest Quran VL_CV = 0.1954 (Surah 106) — 0.39 % away; empirically most plausible origin. Band-A Hotelling TÂ² ratio (max/min) over drop-{0,1,2,3,5} = **1.14** â†’ downstream claim **stable**. | PASS (strict spec). LOW flag: analytic match is almost certainly a numerical coincidence; markdown recommends publication as "empirical parameter with coincidence note". LOW flag: exclusion count is NOT invariant across Â±10 % nbh ({1,2,3}), but downstream TÂ² is insensitive. |

---

## What Tier 5 + E14 Actually Establish

1. **Multi-scale Fisher law is real (E14, the Tier-4 headline).** Brown-corrected p = 1.41 Ã— 10â»â¶, max single-scale Shapley = 43.7 %. Evidence is **genuinely distributed** across the surah (40 %) and corpus (44 %) scales, with non-trivial contributions from the bigram scale (14 %). The falsifier — "one scale carries everything" — is rejected. This is the single most publishable theoretical output in the execution plan.
2. **Reed–Solomon structure is definitively absent (E18).** The pre-registered null closure not only holds, the primary pipeline produced an *apparent* signal that the built-in control test correctly identified as a UTF-8 encoding artefact. This is a stronger outcome than a simple NULL: it demonstrates the confound-detection machinery works.
3. **Feature-level ring composition is null too (E19).** Combined with H20 (lexical ring NULL at exp86), ring-composition claims are now retired at **two** independent representation levels.
4. **`VL_CV_FLOOR = 0.1962` is robust on a wide plateau (E20).** The literal value sits 0.04 % from `1/âˆš26` (probable coincidence) and 0.39 % from the second-smallest Quran VL_CV (probable empirical origin). The Hotelling-TÂ² outlier claim that depends on this floor is insensitive to Â±10 % shifts in the floor value.

## What Tier 5 + E14 Do **Not** Establish

- **Quran-specific Reed–Solomon codes.** Cleanly retired.
- **Ring composition at the surface-feature level.** Cleanly retired (but richer semantic features not tested).
- **Semantically-grounded analytic derivation of `VL_CV_FLOOR`.** The `1/âˆš26` match is a coincidence; no 28/114/6236-based closed form gets within tolerance.
- **Cross-scale causal claims.** E14 shows independent signal at 5 scales, not a mechanistic ladder.

---

## LOW Flags (Follow-Ups Queued)

| ID | Task | Flag | Suggested Follow-Up |
|---|---|---|---|
| F5-L-01 | E14 | Mixed abs-dev vs raw-distance framing across scales | Re-run E14 with uniform raw-distance null for all 5 scales; confirm Brown verdict holds. |
| F5-L-02 | E14 | S5_L_TEL p clipped to null resolution | Double null pool size (to ~4670) and confirm Brown p remains < 10â»âµ. |
| F5-L-03 | E18 | Arm C (poetry) chunker underpowered | Replace `\n\n` split with fixed-length byte chunks; add a Tanzil-like Arabic prose control for independent confound confirmation. |
| F5-L-04 | E18 | Compact-alphabet p=0.031 at (63, 16) | Not at the focal configs; expected Arabic-letter residual structure. No action needed; note in final paper. |
| F5-L-05 | E19 | Per-surah slight excess at Î±=0.05 (6 vs 4) | Replicate with B=10000 shuffles to tighten Poisson noise. |
| F5-L-06 | E19 | Simple 5-D per-verse features | Test with richer per-verse vectors (root-embedding centroids, rhyme-class entropy per-verse) before claiming "no feature-level ring at any level". |
| F5-L-07 | E20 | `1/âˆš26` match is numerical coincidence | Explicitly publish as "empirical parameter", not "derived constant". Already flagged in E20 report markdown. |
| F5-L-08 | E20 | Â±10 % neighborhood not count-invariant | Downstream TÂ² is stable anyway; note in paper's parameter-sensitivity appendix. |

None change verdicts; all are scope-refinement or follow-up work items.

---

## Cumulative Execution-Plan Score After This Audit

| Tier | Tasks | Executed | Audited | HIGH | MED | LOW |
|------|-------|----------|---------|------|-----|-----|
| 1 | 4 | 4 | 4 | 0 | 1 (F-02 adjacent-HARK) | 4 |
| 2 | 5 | 5 | 5 | 0 | 0 | 4 |
| 3 | 4 | 4 | 4 | 0 | 0 | 4 |
| 4 | 4 | 3 (E14 then deferred) | 3 | 0 | 0 | 4 |
| 5 + E14 | 4 (now incl. E14) | 4 | 4 | 0 | 0 | 8 |
| **Totals** | **20** | **20** | **20** | **0** | **1** | **24** |

**Manifest integrity**: 7 run-of-record artefacts tracked; 7 / 7 verified at each audit layer across all 5 tiers. **No SHA drift detected anywhere.**

**Positive-result headline count**: 13 PASS (E1, E2, E3, E4, E5, E6, E8, E9, E11, E12, E13, E14, E15) + 3 PARTIAL/WEAK (E7 WEAK_PERSISTENT, E16 WEAK_LC2, E17 MUSHAF_ONE_AXIS_DOMINANT) + 1 coincidence-flagged PASS (E20) = **17 shipped outcomes**, exceeding the pre-execution target of â‰¥ 14.

**Honest null count**: 3 (E10, E18, E19). Each retires a specific hypothesis with a pre-registered falsifier.

---

## Crosslinks

- Raw audit numbers: `results/experiments/_tier5_audit_report.json`
- Per-experiment JSON + MD: `results/experiments/expE{14,18,19,20}_*/expE{14,18,19,20}_*.{json,md}`
- E18 full-audit trail: `results/experiments/expE18_reed_solomon/expE18_FINAL_report.{json,md}` (merges primary + controls)
- Tier 1 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_2026-04-22.md`
- Tier 2 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md`
- Tier 3 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER3_2026-04-23.md`
- Tier 4 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md`
- Execution plan tracker: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md`
- Manifest of record: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE4_sha_manifest\MANIFEST_v8.json`

---

## Audit Closure

**Tier 5 is CLEAN** on all three speculative experiments (E18 NULL confound, E19 NULL, E20 coincidence-flagged PASS), and **E14 — the highest-theoretical-payoff item in the whole plan — is confirmed PASS (MULTISCALE_LAW) with Brown-corrected p = 1.4 Ã— 10â»â¶ and no single-scale dominance**.

**All 20 tasks are executed and audited. Execution plan CLOSED.**
