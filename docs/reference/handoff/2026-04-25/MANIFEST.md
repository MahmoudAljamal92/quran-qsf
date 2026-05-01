# MANIFEST — External-AI Handoff Pack 2026-04-25

**Purpose**: minimal self-contained set of Markdown files an external AI can ingest without referring to any other file in the repository.

**Total files**: 7 (this manifest + 6 content files).

**Order of presentation**:

1. `00_START_HERE.md` — orientation, scope, what to claim and not to claim
2. `01_RANKED_FINDINGS_TABLE.md` — single ranked table of every positive finding
3. `02_UNIVERSAL_LAW_AND_SIMPLE_MATH.md` — equations, constants, scope, the "compact formula card"
4. `03_NOBEL_AND_PNAS_OPPORTUNITIES.md` — overlooked / under-packaged opportunities ranked by leverage
5. `04_RETRACTIONS_LEDGER.md` — 47 honest retractions, do-not-reopen
6. `05_DECISIONS_AND_BLOCKERS.md` — direct answers on §4.4 T_alt + OSF + the rest of the user's open questions
7. `06_CROSS_DOC_AUDIT.md` — zero-trust contradiction audit + patches applied

## How to use this pack

### As an external-AI prompt input

> *"I'm running the Quranic Structural Fingerprint project. Here are 7 Markdown files describing the project state. Please read them in order, then answer my questions about (a) what the strongest single-feature law is, (b) what the strongest cross-tradition law is, (c) what overlooked opportunities exist, (d) what blocks submission today. Do not propose to reopen any retraction in `04_RETRACTIONS_LEDGER.md` without specifying fresh data and fresh methodology."*

### As a human onboarding pack

Read `00_START_HERE.md`, then `01_RANKED_FINDINGS_TABLE.md`, then `02_UNIVERSAL_LAW_AND_SIMPLE_MATH.md`. Stop there if you want the headline; continue if you want the opportunity tree.

### As a handoff packet

Concatenate all 7 files into a single context window (~80 KB total). The full handoff packet **is the entire content of this folder**, nothing else needed.

## File-level contents

| File | Lines | Bytes (approx) | Self-contained? |
|---|--:|--:|:--:|
| `MANIFEST.md` | ~60 | 2 KB | ✓ this file |
| `00_START_HERE.md` | ~110 | 5 KB | ✓ |
| `01_RANKED_FINDINGS_TABLE.md` | ~120 | 16 KB | ✓ |
| `02_UNIVERSAL_LAW_AND_SIMPLE_MATH.md` | ~190 | 14 KB | ✓ |
| `03_NOBEL_AND_PNAS_OPPORTUNITIES.md` | ~150 | 12 KB | ✓ |
| `04_RETRACTIONS_LEDGER.md` | ~110 | 12 KB | ✓ |
| `05_DECISIONS_AND_BLOCKERS.md` | ~140 | 9 KB | ✓ |
| `06_CROSS_DOC_AUDIT.md` | ~150 | 8 KB | ✓ |
| **Total** | **~1 030** | **~78 KB** | — |

Fits within a single 200 K-token context window with substantial slack for chat history.

## Source-of-truth citations

Every claim in the 6 content files traces to one of the following authoritative project sources:

- `docs/PAPER.md` v7.7 (manuscript)
- `docs/REFERENCE.md` v7.7 (technical handbook)
- `docs/reference/findings/RANKED_FINDINGS.md` v1.3 (43 positive + 28 retraction master table)
- `docs/reference/findings/RETRACTIONS_REGISTRY.md` (47-entry canonical ledger)
- `docs/reference/findings/01_PROJECT_STATE.md` (claim-control dashboard)
- `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md` (5 publishable packages)
- `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md` (cross-tradition phase)
- `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md` (1 030-line tiered backlog)
- `results/integrity/results_lock.json` (58 locked scalars, hash `3ecaf4b048…`)

If you find a contradiction between this pack and any of the above, the **above wins** ; this pack is a snapshot, not a primary source.

## Versioning

- **Pack version**: 1.1 (2026-04-25 evening ; cross-tradition phase complete + §4.4 LOCKED C1)
- **Project version**: v7.7 (paper-grade) + v7.8-candidate work in flight
- **Audit status**: 0 HIGH-data / 1 HIGH-recommendation (A11 git topology, patched) / 2 MED (A1 + A2, patched) / 1 LOW (A10, deferred) / 1 RESOLVED (A3 §4.4 → C1 LOCKED) — total 10 findings
- **Decisions pending**: 0 (§4.4 T_alt RESOLVED 2026-04-25 evening: C1 LOCKED — see `05_DECISIONS_AND_BLOCKERS.md` Q1)
- **External actions pending**: 1 (OSF DOI upload — see `05_DECISIONS_AND_BLOCKERS.md` Q2)

## Update protocol

When the project state changes meaningfully (new locked scalar, new retraction, new submission package), regenerate this pack. The pack is **not** automatically updated — it's a checkpoint. The canonical state is always in the repository.

To regenerate:
1. Re-read the 9 source-of-truth docs above.
2. Update `01_RANKED_FINDINGS_TABLE.md` with any new rows / strength % changes.
3. Update `04_RETRACTIONS_LEDGER.md` with any new retractions.
4. Update `05_DECISIONS_AND_BLOCKERS.md` with current blocker tracker.
5. Run the cross-doc audit (`06_CROSS_DOC_AUDIT.md` methodology) and patch any contradictions in source docs.
6. Bump pack version.

---

*Manifest assembled 2026-04-25 ~17:30 UTC+02. End of pack.*
