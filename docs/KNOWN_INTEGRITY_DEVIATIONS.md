# KNOWN INTEGRITY DEVIATIONS

> **Purpose**: append-only ledger of integrity-audit FAIL rows that the project knows about and chooses to leave standing for transparency rather than silently rewrite. This file is the *open* part of the audit trail — every entry is something a hostile reviewer would catch with `python scripts/integrity_audit.py`, so we publish it ourselves first.
>
> **Authority**: this file is the public record. Do not edit existing entries. Add new entries only via the protocol in `docs/INTEGRITY_PROTOCOL.md`.
>
> **Last updated**: 2026-04-28 evening (patch H V3) — first entry filed.

---

## Why deviations exist at all

Pre-protocol receipts (before 2026-04-26 when the formal PREREG-hash discipline landed) used a variety of schemas. Most pass the audit as `PASS_grandfathered` — they were honest receipts written before the unified protocol existed. A few have actual protocol violations that the audit script (`scripts/integrity_audit.py`) flags as `FAIL_*`. Rather than rewrite history, we publish those flags here.

**Rule**: every `FAIL_*` row from the audit either lives in this file with a written explanation, or gets repaired and re-run. There is no third option ("just ignore it").

---

## Active deviations

### D01 — `exp103_cross_compressor_gamma` PREREG hash mismatch

| Field | Value |
|---|---|
| **First detected** | 2026-04-28 evening (`integrity_audit_20260428T153446Z.json`) |
| **Audit verdict** | `FAIL_prereg_hash_mismatch` |
| **Receipt** | `results/experiments/exp103_cross_compressor_gamma/exp103_cross_compressor_gamma.json` |
| **Hash claimed in receipt** | `d5b3d82788516813d33f66a26164b8d5b433375d8ea8e13d827eb23b2145a93f` |
| **Actual SHA-256 of `experiments/exp103_cross_compressor_gamma/PREREG.md`** | `37877d3dbd82f9828a1e27f9814cfce2d67ce9d24ea3a552f4212fc63f77a9bf` |
| **Underlying experiment verdict** | `FAIL_not_universal` (γ universality across compressor families is not universal) |
| **Standing claim affected** | None directly. The verdict already retracted the universality claim as **R51** in `RETRACTIONS_REGISTRY.md`. |

**What happened**: `experiments/exp103_cross_compressor_gamma/run.py` writes the PREREG.md SHA-256 into the receipt at runtime via `_prereg_hash()` but does **not** enforce a `_PREREG_EXPECTED_HASH` constant (unlike `exp95e`, `exp99`, `exp95f`, etc.). After the receipt was written, the PREREG.md was edited (most likely a small textual correction), changing its SHA-256. The receipt's recorded hash is now a stale snapshot from before that edit.

**Why the underlying claim is unaffected**: the experiment's verdict was a *failure of universality*, which became retraction R51 (`docs/reference/findings/RETRACTIONS_REGISTRY.md` Category L). Editing the PREREG.md *after* a failure does not smuggle in a positive claim — it cannot upgrade a retraction into a finding. The protocol violation here is a hygiene issue, not a science issue.

**What it tells us**: the integrity protocol works precisely as designed. The `integrity_audit.py` script caught a real PREREG-hash drift on the very first run. Modern (post-patch-G) experiments — `exp95e`, `exp95f`, `exp95j`, `exp99`, etc. — all enforce `_PREREG_EXPECTED_HASH` at run time and would have aborted instead of writing a drift-prone receipt.

**Disposition**: **leave as-is and disclose**. The receipt is preserved unchanged. R51 stands. No re-run is required because the experiment's contribution to the project (a retraction) is unaffected by the PREREG-text edit. Future re-runs of `exp103_cross_compressor_gamma` (if any) MUST follow the modern protocol with `_PREREG_EXPECTED_HASH` enforcement.

**External-auditor note**: an external auditor running `python scripts/integrity_audit.py` will see this exact `FAIL_prereg_hash_mismatch` flag. That is the correct behaviour. The audit telling the truth — including telling the truth about its own deviations — is what makes the rest of the project's claims credible. A project that produces zero audit flags after 154 receipts is a project hiding its flags.

---

### D02 — `RETRACTIONS_REGISTRY.md` scoreboard / body inconsistency caught by zero-trust audit L4

| Field | Value |
|---|---|
| **First detected** | 2026-04-28 evening (`results/integrity/zero_trust_audit_20260428T164555Z.json`) |
| **Audit verdict** | `L4_orphan_fail` × 11 + `L2_stale_dep_missing` × 1 (zero-trust audit, **CRITICAL** severity) |
| **Detector** | `scripts/zero_trust_audit.py` (new, written 2026-04-28 evening as a deeper companion to `integrity_audit.py`) |
| **Files affected** | `docs/RETRACTIONS_REGISTRY.md` (mirror) and `docs/reference/findings/RETRACTIONS_REGISTRY.md` (canonical) |
| **Standing claim affected** | None directly. All affected experiments already had FAIL_* verdicts; the gap was bookkeeping (no detailed R-row), not substantive science. |

**What the audit found**:
1. The canonical's scoreboard claimed Category L = 3 (R51–R56 mentioned but only counted as 3); the L heading actually lists 6 entries (R51–R56). Internal inconsistency: 50 (R01–R50) + 6 (R51–R56) = **56**, not the **53** the scoreboard reported.
2. The mirror at `docs/RETRACTIONS_REGISTRY.md` had only the R01–R50 detailed rows (R51–R56 entirely missing in the body) but a scoreboard total of **53** matching the canonical's broken total. So `integrity_audit.py`'s mirror-parity check passed, masking the row-content drift between the two files.
3. 11 FAIL_* receipts had no R-row (or FN-entry) anywhere in the registry: `exp89_lc3_ablation`, `exp90_cross_language_el`, `exp91_meccan_medinan_stability`, `exp95h_asymmetric_detector`, `exp95i_bigram_shift_detector`, `exp95k_msfc_amplification`, `exp95m_msfc_phim_fragility`, `exp95n_msfc_letter_level_fragility`, `exp95o_joint_extremum_likelihood`, `exp99_lc4_el_sufficiency`, `exp103_cross_compressor_gamma`. (The first 4 are pre-R-numbering ancients; the rest were patch-G post-V1 sprint outcomes that had been described in PROGRESS / CHANGELOG but never given registry rows.)
4. `exp95f_short_envelope_replication` cited `exp95e_full_114_consensus_universal` but the audit failed to find the latter because exp95e uses a multi-run subdirectory layout (`exp95e/v1/exp95e_full_114_consensus_universal.json`, not `exp95e/exp95e_full_114_consensus_universal.json`) — a structural-detection gap in the audit script itself.

**What was fixed (2026-04-28 evening, patch H V3.1)**:
- **Bumped the scoreboard math**: Category L count corrected from 3 → 6; new Category M added (R57–R60, the 4 grandfathered ancients); total retractions corrected from 53 → **60**; failed-null count bumped from 7 → **9** (added FN08, FN09 for V1 rescue paths exp95h, exp95i); grand-total corrected from 60 → **69**.
- **Backfilled R-rows**: R57 (exp89_lc3_ablation), R58 (exp90_cross_language_el), R59 (exp91_meccan_medinan_stability), R60 (exp99_lc4_el_sufficiency) added to both canonical and mirror.
- **Backfilled FN-rows**: FN08 (exp95h asymmetric detector), FN09 (exp95i bigram-shift calibrated detector) added to Category K.
- **Documented exp95m disposition**: `exp95m_msfc_phim_fragility` carries `FAIL_audit_features_drift` but is intentionally NOT a retraction (sub-gate 2D using 5-D Φ_M is structurally inadmissible by design — the Φ_M features are verse-final-aware only and structurally blind to interior consonant edits). A note explaining this disposition was added to the registry; no R-number is assigned.
- **exp103 already covered**: the canonical's R51 (γ universality) had documented exp103's substantive retraction since 2026-04-22; the mirror was simply stale because of bullet 2 above. The mirror is now an exact copy of the canonical and includes R51.
- **Mirror-content sync**: `docs/RETRACTIONS_REGISTRY.md` is now a byte-for-byte copy of `docs/reference/findings/RETRACTIONS_REGISTRY.md` after the registry edits, eliminating the row-content drift that masked the inconsistency.
- **Audit-script multi-run support**: `scripts/zero_trust_audit.py` was extended to recognise multi-run experiments (exp95e-style: `<exp>/<subdir>/<exp>.json`) and to downgrade L2 severity from CRITICAL → INFO when both citing and cited receipts are FAIL_* (one failure characterising another, not substantive reliance — e.g., exp95f's pre-registered envelope study of exp95e's failure).

**Disposition**: **REPAIRED**. After the fixes above, `python scripts/zero_trust_audit.py` returns 0 CRITICAL findings on 155 receipts. `python scripts/integrity_audit.py` continues to pass with `mirror_disagreement` = 0 (the mirror-canonical match is now byte-exact, not just scoreboard-number-equal).

**External-auditor note**: this entry is the public record of how a deeper audit script (zero-trust) caught real bookkeeping gaps that the surface-level audit missed. The standing scientific claims (`PAPER.md`, `RANKED_FINDINGS.md`, `results_lock.json`) are unaffected — every affected experiment was already a failure when this audit ran. The gap was administrative (registry rows + count arithmetic), not scientific. Both audits should be run together in CI from now on.

---

### D03 — `exp157_beta_from_cognitive_channel` PREREG hash mismatch

| Field | Value |
|---|---|
| **First detected** | 2026-04-30 evening (first audit run after the V3.22 sprint) |
| **Audit verdict** | `FAIL_prereg_hash_mismatch` |
| **Receipt** | `results/experiments/exp157_beta_from_cognitive_channel/exp157_beta_from_cognitive_channel.json` |
| **Hash claimed in receipt** | `ba78303a4e83c43a525195955e6deacd4077a98a21f794b170c2b02856ee778c` |
| **Actual SHA-256 of `experiments/exp157_beta_from_cognitive_channel/PREREG.md`** | `9e5dcd6428c97f574733ba6a4c0febb701ecd752704a79ac98c6aff7498ca63e` |
| **Underlying experiment verdict** | `PARTIAL_F75_beta_cognitive_directional` (3/5 PREREG criteria PASS; O13) |

**What happened**: same root cause as D01. `exp157`'s `run.py` stamped the PREREG.md hash into the receipt at runtime but did not enforce a `_PREREG_EXPECTED_HASH` constant; a small textual correction was applied to the PREREG.md after the receipt was written, changing its SHA-256. The scientific content (β = 1.3955 numerical optimum at B=7, ε=0.05, Route B feasibility) is unaffected.

**Why the underlying claim is unaffected**: the locked numbers (β_opt, drift, R²) are in the receipt itself, not in the PREREG. The PREREG edit was cosmetic.

**Disposition**: **leave as-is and disclose.** Modern protocol would abort; this legacy receipt remains for audit trail. No re-run required.

---

### D04 — `exp158_F_universal_chinese_extension` PREREG hash mismatch

| Field | Value |
|---|---|
| **First detected** | 2026-04-30 evening (first audit run after the V3.22 sprint) |
| **Audit verdict** | `FAIL_prereg_hash_mismatch` |
| **Receipt** | `results/experiments/exp158_F_universal_chinese_extension/exp158_F_universal_chinese_extension.json` |
| **Hash claimed in receipt** | `5d593c51cb8ad54fd187e489d821ec3e65f25e5f21dcae0f211e2d04529e6251` |
| **Actual SHA-256 of `experiments/exp158_F_universal_chinese_extension/PREREG.md`** | `8340cc3a7ea4db5c26c9e2b84d0d64dadacdeb08e3c29bbf40f5ef637196d400` |
| **Underlying experiment verdict** | Daodejing logographic directional 0/3 narrow / 1/3 widened (chapter_final gap = 1.5969 b above 1.5-b ceiling; H103; O13b) |

**What happened**: identical pattern to D01 / D03. The PREREG.md was edited after receipt write to clarify the directional / widened-gate scope note (no threshold changes). The observed scalar (1.5969 bits) is in the receipt and unaffected.

**Why the underlying claim is unaffected**: the directional "partial" verdict is a scope-limited finding, not a locked universal. The PREREG text edit clarified wording without changing the test.

**Disposition**: **leave as-is and disclose.** No re-run required.

---

## Closed (repaired) deviations

- **D02 (closed 2026-04-28 evening)** — see above. The fix is byte-tracked in `git log -- docs/RETRACTIONS_REGISTRY.md docs/reference/findings/RETRACTIONS_REGISTRY.md scripts/zero_trust_audit.py`.

---

## How to interpret the audit output

| Audit verdict | Meaning | Action required |
|---|---|---|
| `PASS` | Modern receipt, all required + recommended fields present, PREREG hash matches | none |
| `PASS_grandfathered` | Pre-protocol receipt; would-be missing fields are excused because the protocol was not yet in force when it was written | none (do not retro-add fields to legacy receipts) |
| `WARN_missing_optional_field` | Modern receipt missing one of `prereg_hash`, `prereg_document`, `completed_at_utc`, `audit_report` | optional cleanup; not blocking |
| `WARN_missing_self_check` | Modern receipt without a sibling `self_check_*.json` file | optional cleanup; not blocking |
| `FAIL_unparseable` | JSON malformed | repair receipt or re-run |
| `FAIL_no_verdict` | Modern receipt with PREREG.md but no verdict-like field anywhere | repair receipt or re-run |
| `FAIL_prereg_hash_mismatch` | Receipt's `prereg_hash` does not match SHA-256 of the PREREG.md on disk | document in this file OR re-run with locked PREREG |
| `FAIL_audit_red_unreported` | Receipt's `audit_report` has `ok=false` somewhere but the verdict is not an audit-failure verdict | repair the verdict or re-run |
| `FAIL_prereg_missing` | Receipt declares a `prereg_document` path but that file is missing | repair the path or restore PREREG |

---

## Reproducing the audit yourself

```powershell
python scripts/integrity_audit.py
# writes results/integrity/integrity_audit_<timestamp>.{json,md}
```

The script returns exit code 0 if there are zero `FAIL_*` rows AND the doc-sync arithmetic check passes; exit code 1 otherwise. CI / pre-publication gates should run this before any deploy.

---

*Authority: this file is part of the public integrity record. Linked from `docs/INTEGRITY_PROTOCOL.md` §13 and from every `CHANGELOG.md` patch that touches an experiment receipt.*
