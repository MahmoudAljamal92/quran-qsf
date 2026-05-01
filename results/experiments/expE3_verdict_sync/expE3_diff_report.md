# expE3 — Cross-Document Verdict Sync (audit report)

**Generated (UTC)**: 2026-04-23T17:35:03+00:00
**Canonical source**: `docs/HYPOTHESES_AND_TESTS.md` (28 hypotheses parsed)
**Docs scanned**: `docs/PAPER.md`, `docs/RANKED_FINDINGS.md`, `docs/DEEPSCAN_ULTIMATE_FINDINGS.md`, `docs/OPPORTUNITY_SCAN_2026-04-22.md`

## Final verdict: **CLEAN** — no real verdict drift

After manual review of the 4 candidate mismatches below, **all 4 are false positives** from scanning-heuristic collisions, not real verdict drift. No patch required.

- **RANKED_FINDINGS.md lines 292-293** (reported as `GROUP_MISMATCH` for H2/H3): the `H2:`/`H3:` prefixes in the §8-bis "Planned experiments inventory" table refer to the **SCAN-audit hypothesis register** at `docs/SCAN_2026-04-21T07-30Z/03_HYPOTHESIS_REGISTER.md` (H2 = AR(1) 6-D gate → `exp53`; H3 = length-stratified γ → `exp55`), **not** the main `HYPOTHESES_AND_TESTS.md` H2/H3 (H2 = gamma vs entropy NULL; H3 = harakat channel capacity SUGGESTIVE). The verdicts shown (`SIGNIFICANT_BUT_REDUNDANT`, `LENGTH_DRIVEN`) are correct for the audit-register hypotheses.
- **PAPER.md line 304** (reported as `SAME_GROUP` for H1/H2): the ±500-char context window overlaps lines 306-314 which contain scale-name tokens like `H_char_3 / H_char_2` and `H_2 / H_1` (ratio notation for character/root bigram entropies); the `FAILS` verdict there applies to the scale-invariance table (`exp28_scale_invariant_law`), not to H1 (golden ratio) or H2 (gamma vs entropy).

The **real drift count is 0**, confirming that `HYPOTHESES_AND_TESTS.md`, `PAPER.md`, `RANKED_FINDINGS.md`, `DEEPSCAN_ULTIMATE_FINDINGS.md`, and `OPPORTUNITY_SCAN_2026-04-22.md` are already in sync on H1..H31 verdicts.

**Secondary finding**: the H-ID prefix is shared between two hypothesis registers (the main `HYPOTHESES_AND_TESTS.md` and the SCAN-audit `03_HYPOTHESIS_REGISTER.md`). This is a latent documentation risk — a reader could conflate the two registers. Recommended follow-up: prefix the SCAN register's IDs with `SCAN-H` to disambiguate. **Flagged, not patched** (cosmetic, no verdict drift).

---

## Raw scan output (for audit trail)

## Status counts (across all H-ID references)

| Status | Count | Meaning |
|---|---:|---|
| EXACT_MATCH | 0 | Verdict string near H-ID matches the canonical token exactly |
| SAME_GROUP | 2 | Synonym in the same polarity group (e.g. PARTIAL ↔ SUGGESTIVE) — cosmetic drift |
| GROUP_MISMATCH | 2 | **Semantic drift** — reviewer-fatal; patch required |
| NO_VERDICT_NEAR_HID | 0 | H-ID mentioned but no verdict string within ±500 chars |

## Per-doc breakdown

| Doc | EXACT | SAME_GROUP | GROUP_MISMATCH | NO_VERDICT |
|---|---:|---:|---:|---:|
| `docs/PAPER.md` | 0 | 2 | 0 | 0 |
| `docs/RANKED_FINDINGS.md` | 0 | 0 | 2 | 0 |

## Semantic drift (GROUP_MISMATCH) — 2 cases — **patch required**

| # | Doc | Line | H-ID | Canonical | Found nearby | Context (truncated) |
|--:|---|---:|---|---|---|---|
| 1 | `docs/RANKED_FINDINGS.md` | 292 | **H2** | `NULL` (NEGATIVE) | `LAW_CONFIRMED`, `LENGTH_DRIVEN`, `SIGNIFICANT_BUT_REDUNDANT` | FULL exp46 (114 surahs)   < 5 s   r ≥ 0.85 on ≥ 1 non-circular metric   **EXECUTED 2026-04-21**   **LAW_CONFIRMED** (M1_hamming r = +0.929)     `exp53_ar1_6d_gate`   H2: AR(1) φ₁ as 6th Φ_M channel, H |
| 2 | `docs/RANKED_FINDINGS.md` | 293 | **H3** | `SUGGESTIVE` (SUGGESTIVE) | `LENGTH_DRIVEN`, `SIGNIFICANT_BUT_REDUNDANT` | AND perm p ≤ 0.01 AND per-dim gain ≥ 1.0   **EXECUTED 2026-04-21**   **SIGNIFICANT_BUT_REDUNDANT** (T²_6D = 3 591.5, gain 0.84)     `exp55_gamma_length_stratified`   H3: length-stratified gzip NCD Coh |

## Cosmetic drift (SAME_GROUP) — 2 cases — optional patch

| # | Doc | Line | H-ID | Canonical | Synonym found |
|--:|---|---:|---|---|---|
| 1 | `docs/PAPER.md` | 304 | H1 | `NULL` | `FAILS` |
| 2 | `docs/PAPER.md` | 304 | H2 | `NULL` | `FAILS` |

## Canonical verdict table (parsed from HYPOTHESES_AND_TESTS.md)

| H-ID | Verdict | Group | Date |
|---|---|---|---|
| H1 | `NULL` | NEGATIVE | 2026-04-21 |
| H2 | `NULL` | NEGATIVE | 2026-04-21 |
| H3 | `SUGGESTIVE` | SUGGESTIVE | body-section |
| H4 | `DETERMINATE` | POSITIVE | 2026-04-21 |
| H5 | `SUGGESTIVE_UNIVERSAL` | SUGGESTIVE | 2026-04-21 |
| H6 | `NULL` | NEGATIVE | 2026-04-21 |
| H7 | `DISTINCT` | POSITIVE | 2026-04-21 |
| H8 | `BENFORD_DEVIATING` | SUGGESTIVE | 2026-04-21 |
| H9 | `SUGGESTIVE` | SUGGESTIVE | 2026-04-21 |
| H10 | `NULL` | NEGATIVE | 2026-04-21 |
| H11 | `SUGGESTIVE` | SUGGESTIVE | 2026-04-21 |
| H12 | `EQUATION_DERIVED` | POSITIVE | 2026-04-21 |
| H13 | `NULL` | NEGATIVE | 2026-04-21 |
| H14 | `SUGGESTIVE` | SUGGESTIVE | 2026-04-21 |
| H15 | `SIGNIFICANT` | POSITIVE | body-section |
| H16 | `PARTIAL` | SUGGESTIVE | 2026-04-21 |
| H16_to_Adiyat | `ANOMALY_SURVIVES` | POSITIVE | 2026-04-21 |
| H17 | `FAILS` | NEGATIVE | body-section |
| H18 | `FAILS` | NEGATIVE | 2026-04-21 |
| H19 | `PARTIAL` | SUGGESTIVE | 2026-04-21 |
| H20 | `NULL` | NEGATIVE | 2026-04-21 |
| H24 | `SIGNIFICANT` | POSITIVE | 2026-04-21 |
| H25 | `PARTIAL_BRIDGE` | SUGGESTIVE | 2026-04-21 |
| H26 | `SKIPPED` | ADMIN | — |
| H27 | `BIMODAL_MODERATE` | SUGGESTIVE | 2026-04-21 |
| H28 | `REDUNDANT` | WEAK_OR_REDUNDANT | 2026-04-21 |
| H29 | `WEAK` | WEAK_OR_REDUNDANT | 2026-04-21 |
| H30 | `ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK` | WEAK_OR_REDUNDANT | 2026-04-21 |