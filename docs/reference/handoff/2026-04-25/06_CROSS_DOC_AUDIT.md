# 06 — Cross-Doc Zero-Trust Audit (2026-04-25)

> **Post-audit note (2026-04-26 morning)**: `PROJECT_MAP.md` (root) was merged into `README.md` and deleted on 2026-04-26 ; the references to `PROJECT_MAP.md` and its line numbers in the audit body below are **historical citations** valid at the time of audit (2026-04-25 evening). The same content now lives in `README.md` appendix sections "Canonical documentation", "Legacy doc-name index", "Integrity files", and "Where to look when…". See the "Patch log" entry dated 2026-04-26 morning for details. The audit body is preserved unchanged for historical accuracy.

**Method**: scanned the 6 highest-authority docs for scalar drift, version drift, and counter-of-things drift across the project's main claims. Each row is a finding with the canonical source-of-truth and the patch (if applicable).

**Scope of this audit**: only the docs the user reads end-to-end:

- `README.md`
- `PROJECT_MAP.md`
- `docs/PAPER.md`
- `docs/reference/findings/RANKED_FINDINGS.md`
- `docs/reference/findings/01_PROJECT_STATE.md`
- `docs/reference/findings/RETRACTIONS_REGISTRY.md`
- `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md`
- `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md`

Lower-authority docs (CHANGELOG.md, individual experiment JSONs, archived material) are out of scope; per `RETRACTIONS_REGISTRY.md` "Authority chain", any conflict resolves to the higher item.

---

## Audit findings

### A1 — Version-string drift in `README.md` (LOW)

**Issue**: `README.md:5` declares `**Current version**: **v7.6**`, but every other authority doc is at v7.7 (paper, reference handbook, ranked findings v1.3 v7.7, project map v7.7) and there is v7.8-candidate work in flight (`docs/PAPER.md §4.36–4.39`).

**Canonical**: v7.7 (per `PAPER.md:5`, `PROJECT_MAP.md:5`, `RANKED_FINDINGS.md:3`).

**Patch**: bump `README.md` version banner.

**Status**: PATCH APPLIED 2026-04-25 (this audit cycle).

---

### A2 — Retraction-count drift across docs (LOW)

**Issue**: count of "honest retractions" disagrees across docs.

| Doc | Cited count | Source |
|---|--:|---|
| `README.md:3` (headline) | 25 | stale, pre-v7.7 |
| `README.md:53` (headlines table) | 25 | stale |
| `README.md:152` (§v2→v7.5 paragraph) | 25 | stale |
| `RANKED_FINDINGS.md:39` (§2 master table caption) | 28 | curated subset (R1–R28) |
| `RANKED_FINDINGS.md:208` (§5 header) | 28 | curated subset |
| `RANKED_FINDINGS.md:283` (§7 venues table arXiv row) | 25 | stale |
| `RETRACTIONS_REGISTRY.md` | **47** | canonical |
| `PROJECT_MAP.md:28` | 47 | correct |
| `01_PROJECT_STATE.md` | (not cited) | – |

**Canonical**: 47 distinct retractions in `RETRACTIONS_REGISTRY.md` (the project's append-only authoritative ledger). The "28" in `RANKED_FINDINGS.md §5` is a deliberately curated subset (the most-prominent retractions per ranked-finding row); the "25" in `README.md` and the `RANKED_FINDINGS.md §7` venues table is **stale** (pre-cross-tradition-phase, pre-v7.7-sprint).

**Patch**:
- `README.md:3` — `25 honest retractions` → `47 honest retractions` (canonical) with parenthetical "(28 highlighted in `RANKED_FINDINGS.md §5`)"
- `README.md:53` — "Honest retractions" headline-table row: `**25**` → `**47**` (canonical)
- `README.md:152` — `25 honest retractions, 51 sandbox experiments` → `47 honest retractions, 130+ experiments`
- `RANKED_FINDINGS.md:283` — `25 retractions` → `47 retractions (28 in §5)` for consistency

**Status**: PATCHES APPLIED 2026-04-25 (this audit cycle).

---

### A3 — Φ_M scalar drift (RESOLVED 2026-04-25 evening: §4.4 LOCKED C1)

**Issue**: `Φ_M = 3 557` (canonical) vs `Φ_M = 3 868` (T_alt refinement) appear in different docs.

| Doc | Cited Φ_M | Notes |
|---|--:|---|
| `README.md` headline | 3 557 | canonical T_canon |
| `PAPER.md §4.1` | 3 557 | canonical |
| `RANKED_FINDINGS.md` row 2 | 3 557 | canonical |
| `01_PROJECT_STATE.md` | 3 557 | canonical |
| `SUBMISSION_READINESS_2026-04-25.md §4.4` | 3 557 (canonical) ; 3 868 noted as P7-headline refinement | LOCKED C1 2026-04-25 |
| `OPPORTUNITY_TABLE_DETAIL.md §X7 P2_OP2` | 3 868 (T_alt at Band-A) | P7 headline scalar (not promoted to lock under C1) |
| `results_lock.json` | 3 557 | locked, UNCHANGED under C1 |

**Canonical**: 3 557 (per `results_lock.json` lock entry `Phi_M_hotelling_T2`). 3 868 is the T_alt refinement, **explicitly NOT promoted to lock under the C1 decision**. T_alt becomes the headline of P7 (atomic methodology paper).

**Patch**: §4.4 of `SUBMISSION_READINESS_2026-04-25.md` rewritten 2026-04-25 evening from "DECISION REQUEST" → "DECISION LOCKED — C1". Handoff pack files 00, 01, 05 updated to reflect resolution. CHANGELOG entry appended. No `results_lock.json` mutation.

**Status**: PATCH APPLIED 2026-04-25 evening (this audit cycle). Reopen iff project re-targets to Option B / PRX TIT / PNAS.

---

### A4 — OSF DOI is `10.17605/OSF.IO/N46Y5` across all docs (NOT a contradiction)

**Issue**: `PAPER.md:7`, `README.md:9` both say `10.17605/OSF.IO/N46Y5`. The deposit zip exists at `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip` with SHA `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`. The upload checklist exists at `docs/reference/prereg/OSF_UPLOAD_CHECKLIST.md`.

**Canonical**: pending, by design. The user has not yet uploaded.

**Patch**: none. Once uploaded, replace `10.17605/OSF.IO/N46Y5` with the real DOI in `PAPER.md`, `README.md`, and any other doc referencing it. **This is the single highest-ROI external action remaining** per `05_DECISIONS_AND_BLOCKERS.md` Q2.

**Status**: NO PATCH (user-blocker, not a doc-internal inconsistency).

---

### A5 — `RANKED_FINDINGS.md` row 13 cross-tradition update applied; row 28 / row 32 / row 36 / row 38 are v7.5–v7.6 retraction-tagged correctly

**Issue check**: rows 13 (LC2 R3 cross-tradition), 28 (Hurst caveat), 32 (emphatic immunity), 34 (acoustic bridge retraction), 36 (anti-repetition pending), 38 (Hurst ladder pending) — all carry the right post-v7.5/v7.6 status flags (LOO_ROBUST, downgraded, immunity confirmed, retracted, planned, retracted respectively).

**Canonical**: row 13 properly cites `expP4_cross_tradition_R3_loo` 8/8 robustness ; row 34 properly cites the v7.6 `exp52_acoustic_bridge_full` retraction ; row 38 properly notes the v7.8 `exp96_hurst_ladder` retraction.

**Patch**: none required.

**Status**: NO PATCH ; row-level statuses are sync'd.

---

### A6 — `RANKED_FINDINGS.md §0` "Is there a universal law?" reads as honest after cross-tradition phase

**Issue check**: the §0 paragraph properly says "empirically n>1 cross-tradition replication landed 2026-04-25; formal universal-law status still requires Shannon-capacity derivation + two-team external replication." This matches `CROSS_TRADITION_FINDINGS_2026-04-25.md` TL;DR.

**Patch**: none required.

**Status**: NO PATCH ; framing is consistent with v7.8.

---

### A7 — `01_PROJECT_STATE.md` exp95/exp105/exp106 status notes are correct

**Issue check**: the "Patch stale references" section correctly flags `exp95 = FAIL_ctrl_stratum_overfpr`, `exp105 = PARTIAL_null_saturated`, `exp106 = prereg only / no result`, `E14 = MULTISCALE_LAW confirmed`, `execution plan = closed, 20/20 audited`. These match `EXECUTION_PLAN_AND_PRIORITIES.md` final status.

**Patch**: none required.

**Status**: NO PATCH.

---

### A8 — `SUBMISSION_READINESS_2026-04-25.md` §1.1 (Ψ_oral) and §1.4 (4-leg synthesis) carry the right retractions

**Issue check**: §1.1 has the post-measurement update with `expX1_psi_oral` NO_SUPPORT verdict (filed as retraction R28). §1.4 properly retracts the 4-leg optimality synthesis. Headline P5 correctly downgraded from "TODAY" to "DONE 2026-04-25 evening — Ψ_oral cross-corpus measurement → not publishable".

**Patch**: none required.

**Status**: NO PATCH.

---

### A9 — `arxiv_submission/paper.md` carries DEPRECATED banner (verified)

**Issue check**: `arxiv_submission/STATUS.md` and `PROJECT_MAP.md:31` both note that `arxiv_submission/paper.md` carries a DEPRECATED banner pointing to `docs/PAPER.md` v7.5 as the current paper.

**Patch**: none required.

**Status**: NO PATCH ; behaviour is by design (frozen v3.0 snapshot).

---

### A10 — `RANKED_FINDINGS.md §7` venues "PNAS-grade paper" Above-row says "Above + full-mode perm + cross-corpus acoustic + full exp45/46 + BPE-LM"

**Issue**: the cross-corpus acoustic scope was retracted v7.6 (Simpson's-paradox); the "BPE-LM" is `A8` Tier-A item still pending. The wording "Above + full-mode perm + cross-corpus acoustic + …" is post-v7.5 wording that should be updated.

**Canonical**: per `RANKED_FINDINGS.md` row 34 + §6 immediate item 2, the acoustic-bridge claim is retracted; only pitch-variance arm survives. The "PNAS-grade" row should drop "cross-corpus acoustic" and reference X6/X3 instead.

**Patch**: low-priority text edit; not blocking. Documenting here for next doc-reconciliation pass.

**Status**: PATCH NOT APPLIED ; flagged for next reconciliation pass.

---

### A11 — Git repository topology foot-gun: `.git` at Desktop, not project root (HIGH — recommendation-level, not data-level)

**Issue**: `05_DECISIONS_AND_BLOCKERS.md §Q3 Z6` previously recommended `git add -A && git commit -m "..."` to durably commit the audit + C1-lock patches. Direct verification 2026-04-25 evening shows the `.git` directory lives at `C:\Users\mtj_2\OneDrive\Desktop\` (the user's Desktop), **not** at `C:\Users\mtj_2\OneDrive\Desktop\Quran\` (the project root). Running the recommended command from anywhere inside `Quran/` would have ingested the user's entire Desktop on the first commit (Cover Letter.docx, Cover Letter.pdf, CV.lnk, Games/, BIM MODELER/, Softwares/, MS Office lock files `~$\*.docx` / `~$\*.rtf`, and ~10 other personal items).

**Verification commands and outputs** (run 2026-04-25 evening):

```powershell
git -C "C:\Users\mtj_2\OneDrive\Desktop\Quran" rev-parse --show-toplevel
# → C:/Users/mtj_2/OneDrive/Desktop      (NOT the Quran folder!)

Test-Path "C:\Users\mtj_2\OneDrive\Desktop\Quran\.git"   # → False
Test-Path "C:\Users\mtj_2\OneDrive\Desktop\.git"         # → True
git -C "C:\Users\mtj_2\OneDrive\Desktop" log --oneline -n 5
# → fatal: your current branch 'master' does not have any commits yet
git -C "C:\Users\mtj_2\OneDrive\Desktop\Quran" status --porcelain | Measure-Object | % Count
# → 19   (19 untracked items at Desktop level, including Quran/ itself)
```

**Canonical**: project docs (`docs/reference/...`, `arxiv_submission/...`, `results/integrity/results_lock.json`, `PROJECT_MAP.md`) all use paths that are project-root-relative. The repo topology is therefore meant to be `C:\Users\mtj_2\OneDrive\Desktop\Quran\.git`, with the project root as the git toplevel. The current Desktop-rooted topology is a historical artefact (probably an accidental `git init` in the parent folder at some point) that has caused zero damage so far only because nobody has actually run `git add -A` yet.

**Patch**:
- `handoff/05_DECISIONS_AND_BLOCKERS.md §Q3` Z6 row: replaced naive `git add -A && git commit` recommendation with a topology warning pointing here.
- `handoff/05_DECISIONS_AND_BLOCKERS.md` new sub-section "Z6 detail — git topology and safe commit options" added immediately under the Q3 table, giving copy-pasteable PowerShell for **Option A** (recommended: `Remove-Item …\Desktop\.git ; git init …\Quran ; git add . ; git commit …` — safe because parent has zero commits) and **Option B** (fragile: scoped `git -C Desktop add Quran ; git commit`).
- `handoff/05_DECISIONS_AND_BLOCKERS.md §Q5` step 5: now explicitly references "Option A" + warns about the foot-gun + cross-references this audit row.
- **Propagation patches (2026-04-26 morning)** — extended A11 scope to non-handoff sprint docs that carried the same prescriptive foot-gun:
  - `docs/reference/sprints/OPPORTUNITY_TABLE.md:50` (item 0h "git commit") — replaced bare command with topology-aware redirect to Z6 detail / Option A.
  - `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md:988` (Priority Action Board row 0h) — same patch.
  - `docs/reference/sprints/AUDIT_MEMO_2026-04-24.md:375` (Appendix B.7 Git history) — replaced bare command with topology-aware redirect to Z6 detail / Option A; cross-ref to A11 added.

**Why HIGH severity at the recommendation level (but not the data level)**: no data has been corrupted yet (zero commits in either potential location), and `results_lock.json` is unaffected (locked-scalar drift is detected by SHA, not by repo topology). But the previous recommendation, if executed by a user trusting the canonical doc, would have leaked private Desktop content (CV, cover letters, lock files) into a repo intended for public publication. That is exactly the class of cross-doc bug this audit exists to catch.

**Status**: PATCH APPLIED 2026-04-25 evening (this audit cycle, post-C1-lock). User-side command execution still required to actually commit the patches; recommended path is Option A.

---

## Audit scoreboard

| Severity | Count |
|---|---:|
| HIGH at recommendation level (would have leaked private content if followed) | 1 (A11 git topology) |
| HIGH at data level (blocks submission) | 0 |
| MED (causes confusion to external reader) | 2 (A1 version + A2 retraction count) |
| LOW (cosmetic / stale wording) | 1 (A10 PNAS-row wording) |
| RESOLVED (decision-pending state closed this cycle) | 1 (A3 Φ_M → §4.4 LOCKED C1) |
| NO_PATCH (intentional or external blocker) | 5 (A4 OSF, A5–A9) |
| **Total findings** | **10** |

**Patches applied**: A1, A2 (3 sub-patches in `README.md`, 1 in `RANKED_FINDINGS.md`), A3 (§4.4 LOCKED C1 in `SUBMISSION_READINESS_2026-04-25.md` + 4 propagations across handoff pack), A11 (Z6 row + new Z6 detail sub-section + Q5 step 5 warning in `05_DECISIONS_AND_BLOCKERS.md`).

**Patches deferred**: A10 (next reconciliation pass).

---

## Patch log

| Date | File | Section | Old | New | Audit ID |
|---|---|---|---|---|---|
| 2026-04-25 | `README.md` | line 5 (Current version) | `**v7.6**` | `**v7.7**` (with v7.8-candidate parenthetical) | A1 |
| 2026-04-25 | `README.md` | line 3 (headline) | `25 honest retractions` | `47 honest retractions` | A2 |
| 2026-04-25 | `README.md` | line 53 (headlines table) | `**25**` | `**47**` | A2 |
| 2026-04-25 | `README.md` | line 152 (v2→v7.5 paragraph) | `25 honest retractions` | `47 honest retractions` | A2 |
| 2026-04-25 | `RANKED_FINDINGS.md` | line 283 (§7 venues row) | `25 retractions` | `47 retractions (28 in §5)` | A2 |
| 2026-04-25 evening | `SUBMISSION_READINESS_2026-04-25.md` | §4.4 | `NEW DECISION` (3-way request) | `DECISION LOCKED — C1` (T_canon stays canonical, T_alt → P7) | A3 |
| 2026-04-25 evening | `SUBMISSION_READINESS_2026-04-25.md` | §6 / §7 / §8 | "decision pending" wording | "LOCKED C1" wording | A3 |
| 2026-04-25 evening | `handoff/00_START_HERE.md` | §1 In flux → Recently resolved | T_alt listed as in-flux | T_alt listed as resolved C1 | A3 |
| 2026-04-25 evening | `handoff/01_RANKED_FINDINGS_TABLE.md` | X7 P2_OP2 row + Z1 | "§4.4 decision pending" | "§4.4 LOCKED C1" + Z1 struck | A3 |
| 2026-04-25 evening | `handoff/05_DECISIONS_AND_BLOCKERS.md` | Q1, Z1 row, P2/P7 rows, Q5 | "5-min decision pending" | "RESOLVED C1 LOCKED 2026-04-25" | A3 |
| 2026-04-25 evening | `handoff/05_DECISIONS_AND_BLOCKERS.md` | Q3 Z6 row | `git add -A && git commit ...` (foot-gun: parent `.git` at Desktop) | topology warning + cross-ref to A11 | A11 |
| 2026-04-25 evening | `handoff/05_DECISIONS_AND_BLOCKERS.md` | new sub-section under Q3 | (didn't exist) | "Z6 detail — git topology and safe commit options" with verified Option A + Option B PowerShell | A11 |
| 2026-04-25 evening | `handoff/05_DECISIONS_AND_BLOCKERS.md` | Q5 step 5 | "`git commit` the audit + C1-lock patches" | same + "⚠ use Option A; see A11" | A11 |
| 2026-04-26 morning | `sprints/OPPORTUNITY_TABLE.md` | line 50 (item 0h) | bare `git add -A && git commit -m "audit 2026-04-24..."` | foot-gun warning + redirect to Z6 detail / Option A + A11 cross-ref | A11 |
| 2026-04-26 morning | `sprints/OPPORTUNITY_TABLE_DETAIL.md` | line 988 (Priority Action Board row 0h) | bare `git add -A && git commit -m "audit 2026-04-24..."` | foot-gun warning + redirect to Z6 detail / Option A | A11 |
| 2026-04-26 morning | `sprints/AUDIT_MEMO_2026-04-24.md` | line 375 (Appendix B.7 Git history) | bare `git add -A && git commit -m "audit 2026-04-24 patches"` | foot-gun warning + redirect to Z6 detail / Option A + A11 cross-ref | A11 |
| 2026-04-26 morning | (root) `PROJECT_MAP.md` | entire file (167 lines) | standalone doc | **MERGED into `README.md`** as 4 new appendix sections (Canonical documentation, Legacy doc-name index, Integrity files, Where to look when…) ; `PROJECT_MAP.md` deleted ; backup at `README.md.bak.20260426` | hygiene-merge (root cleanup ; user-approved Path 1) |
| 2026-04-26 morning | `README.md` | bullet "What you're looking at" + file-tree code-block + "Citing" version | listed PROJECT_MAP.md as a separate doc ; v7.6 bullet ; v7.6 citation | removed PROJECT_MAP.md self-reference ; v7.6 → v7.8-cand bullet ; v7.6 → v7.7 citation ; new appendix sections inserted | hygiene-merge |
| 2026-04-26 morning | `docs/PROGRESS.md` | line 575 | "`PROJECT_MAP.md` (root)" | "`README.md` (root) — see appendix sections …" | hygiene-merge propagation |
| 2026-04-26 morning | `docs/reference/sprints/README.md` | line 54 (Pass 1 scan-coverage row) | "(README.md, PROJECT_MAP.md, CHANGELOG.md) \| 3 \| 877" | "(README.md, CHANGELOG.md) \| 2 \| ~1024" | hygiene-merge propagation |
| 2026-04-26 morning | `docs/reference/findings/RETRACTIONS_REGISTRY.md` | line 159 (footer) | "cross-reference … from `PROJECT_MAP.md` integrity-locks section" | "cross-reference … from `README.md` 'Integrity files' appendix section (merged in 2026-04-26)" | hygiene-merge propagation |
| 2026-04-26 morning | `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md` | lines 122, 131, 144, 167 | 4× `PROJECT_MAP.md` citations | repointed to `README.md` appendix sections with provenance notes | hygiene-merge propagation |
| 2026-04-26 morning | `handoff/06_CROSS_DOC_AUDIT.md` | top banner + patch log | (no banner) | post-audit banner explaining PROJECT_MAP.md historical citations are preserved as-is ; this patch log row | hygiene-merge propagation |

---

## What this audit deliberately did NOT touch

- **`results_lock.json`** — never edited by audit. Locked-scalar drift is detected by SHA, not by doc audit.
- **`results/checkpoints/`** — same.
- **Individual experiment JSONs under `results/experiments/expNN_*/`** — out of scope; each experiment's self-check handles its own drift.
- **`archive/`** — frozen by design; do not edit.
- **Docs prefixed with `DEPRECATED`** (e.g., `arxiv_submission/paper.md`) — frozen by design.
- **CHANGELOG.md** — append-only release history; not in audit scope.

---

*Audit assembled 2026-04-25 by Cascade. Authority precedence per `RETRACTIONS_REGISTRY.md`: PAPER.md → RANKED_FINDINGS.md → CHANGELOG.md → ULTIMATE_SCORECARD.md ; canonical source-of-truth for any locked scalar is `results_lock.json`.*
