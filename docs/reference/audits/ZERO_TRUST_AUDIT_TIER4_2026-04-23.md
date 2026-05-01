# Zero-Trust Audit — Tier 4 Experiments (E15, E16, E17)

**Date**: 2026-04-23
**Scope**: Tier 4 block from `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md` (law-candidate experiments). **E14 is DEFERRED** (expected runtime > 15 min; queued for an optimization pass).
**Successor closure note**: E14 was later executed and audited in `docs/reference/audits/ZERO_TRUST_AUDIT_TIER5_2026-04-23.md` with verdict **MULTISCALE_LAW**; the execution plan is now closed at 20/20 audited tasks.
**Driver**: `results/experiments/_tier4_audit.py` â†’ `results/experiments/_tier4_audit_report.json`
**Final disposition**: **0 HIGH / 0 MED / 4 LOW flags**; all three verdicts re-derived from raw numbers match the reported verdicts; **0 drift** against the 7 manifest-tracked run-of-record artefacts.

---

## Audit Dimensions & Checks

| # | Dimension | Check | Result |
|---|---|---|---|
| A1 | File hygiene | Every expected `expE{15,16,17}_report.{json,md}` + plot exists and parses | PASS |
| A2 | Pre-registration | Each JSON declares `pre_registered_criteria`, `seed`, `verdict` | PASS |
| A3 | Verdict re-derivation | Re-compute verdict from raw stats; compare to reported verdict | PASS — all 3 match |
| A4 | Pinned-artefact integrity | SHA-256 re-check vs `MANIFEST_v8.json` | PASS — 7/7 entries clean |
| A5 | Sanity bounds | percentile âˆˆ [0,100], p âˆˆ [0,1], quantile âˆˆ [0,1], eigenvalue count = 5 | PASS |
| A6 | Known design caveats / follow-up | Documented | 4 LOW flags filed |

---

## Per-Experiment Results (short form)

| Task | Verdict | Key Numbers | Audit Disposition |
|---|---|---|---|
| **E15** Anti-Variance Manifold | **ANTI_VARIANCE_LAW** | Quran mean anti-distance 2.91 vs control 1.25; percentile 98.53 %; label-shuffle p < 10â»â´ (N=10000); anti-basis = 2 smallest-eigenvalue eigenvectors of Î£_ctrl (Î»â‚=0.286, Î»â‚‚=0.783). | PASS. LOW flag: permutation reestimates Î£ per shuffle (correct null); observed basis uses true-data Î£. |
| **E16** LC2 Memorization Signature | **WEAK_LC2** (honest partial pass) | At Î» âˆˆ {0.1, 0.5, 1, 2, 5}: Quran median rank goes 44.6% â†’ 23.2% â†’ 6.4% â†’ 1.5% â†’ 1.4%; 2/5 Î» â‰¤ 5th pct, 3/5 â‰¤ 10th pct â†’ WEAK per pre-registered thresholds. | PASS. LOW flag: signal is V-dominated at high Î» — re-encodes the pre-existing high-EL outlier property rather than a joint M+V optimization. |
| **E17** Mushaf vs Nuzul dual-opt | **MUSHAF_ONE_AXIS_DOMINANT** (honest partial pass) | J1 (Mahalanobis smoothness) quantile = **0.0000** (Mushaf beats all 10 000 random perms AND Nuzul); J2 (sign-direction entropy) quantile = 0.84 — NOT extremised. Mushaf Pareto-beats Nuzul jointly but not random perms on J2. | PASS. LOW flags: (a) dual-opt hypothesis falsified on J2; only the smoothness finding survives; (b) Nuzul = Egyptian Standard Edition; alternative chronologies not tested. |

---

## What Tier 4 Actually Establishes

1. **The "anti-variance manifold" is a real geometric law (E15).** The Quran is 2.33Ã— farther from the control centroid along the two lowest-variance directions of the Arabic 5-D feature covariance than controls are on average — percentile 98.5, perm p < 10â»â´. An explicit closed-form hyperplane definition is published in the report.
2. **Mushaf ordering extremises inter-surah smoothness (E17, J1 axis).** Across 10 000 random 114-surah permutations, Mushaf's Mahalanobis sum-of-transition-squares is lower than every single shuffle AND lower than the Egyptian/Azhar Nuzul order. This is a strong standalone finding, even though the broader dual-optimisation claim fails on J2.
3. **The LC2 memorization-optimization signature survives at WEAK level (E16)**, with the key caveat that the "signature" at high Î» essentially rediscovers the already-documented high verse-final-letter-entropy outlier rather than a genuinely new joint M+V phenomenon.

## What Tier 4 Does **Not** Establish

- **Multi-scale Fisher combination law** (E14) — deferred; no data yet.
- **Rhythmically uniform transition pattern in the Mushaf** (E17, J2 axis) — falsified. The sign-direction entropy is higher than 84 % of random orderings, not lower.
- **True chronological-order sensitivity** (E17) — the Nuzul proxy is a single reconstruction (Egyptian Standard Edition); alternative chronologies (e.g., NÃ¶ldeke) not tested.
- **Generalisation of LC2 beyond Quran's high-EL property** (E16) — the signal is dominated by V at high Î».

---

## LOW Flags (Follow-Ups Queued)

| ID | Task | Flag | Suggested Follow-Up |
|---|---|---|---|
| F4-L-01 | E15 | Î£ reestimated per shuffle | Documented; no action needed — the permutation null correctly randomises class membership and recomputes the anti-basis under each permutation. |
| F4-L-02 | E16 | V-dominated at high Î» | Decompose the contribution of M and V separately; report the Pareto front in (M, V) space. |
| F4-L-03 | E17 | J2 not extremised | Replace J2 with a better-motivated rhythmicity metric (autocorrelation of transition magnitudes, or Mann-Kendall monotonicity), OR drop the dual-opt framing and publish the J1-only smoothness law. |
| F4-L-04 | E17 | Nuzul source = Egyptian only | Re-run with NÃ¶ldeke chronology; check whether Mushaf still Pareto-beats. |

None of these change Tier 4 verdicts — they refine scope or suggest follow-up work.

---

## Crosslinks

- Raw audit numbers: `results/experiments/_tier4_audit_report.json`
- Per-experiment JSON + MD: `results/experiments/expE{15,16,17}_*/expE{15,16,17}_report.{json,md}`
- Tier 1 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_2026-04-22.md`
- Tier 2 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md`
- Tier 3 audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER3_2026-04-23.md`
- Execution plan tracker: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md`
- Manifest of record: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE4_sha_manifest\MANIFEST_v8.json`

---

## Audit Closure

**Tier 4 is CLEAN on the three executed experiments.** E14 is explicitly DEFERRED with a documented runtime bottleneck; the remaining three give one strong new law (E15 ANTI_VARIANCE_LAW), one strong partial claim (E17 J1 smoothness quantile = 0.0), and one honest weak pass (E16 WEAK_LC2). Proceed to Tier 5 (speculative E18–E20) or stop on user direction.
