# STATUS — arxiv_submission/ is a FROZEN v3.0 snapshot

**This directory is a frozen submission packet from 2026-04-17 (v3.0).**
**It is NOT the current paper.** It is preserved here verbatim so that (a) the OSF deposit zip's SHA can be reproduced, and (b) the v3.0 numbers can be cited unambiguously.

**`paper.md` in this directory now carries an explicit top-of-file DEPRECATED banner** pointing to `../docs/PAPER.md` v7.5; any reviewer or automated pipeline hitting this directory will see the banner before the body. Do not edit the banner, the body, or the SHA-pinned companion files.

## For the current paper, go to:

- `../docs/PAPER.md` — **v7.5** full manuscript (879 lines, 2026-04-21 evening; §§4.32–4.34 close exp48 promotion, cross-corpus emphatic audit, and poetry_islami sensitivity)
- `../docs/QSF_COMPLETE_REFERENCE.md` — **v7.5** reference handbook
- `../docs/RANKED_FINDINGS.md` — **v1.1 (v7.5 sync)** 40 findings + roadmap to 100 %
- `../docs/ADIYAT_CASE_SUMMARY.md` — **v7.5** Adiyat answer (supersedes `supplementary/ADIYAT_CASE.md` which is v3.0)
- `../docs/DEEPSCAN_ULTIMATE_FINDINGS.md` — **2026-04-21 deep-scan inventory** (v7.5 addenda in Parts 1, 4, 7, 9)
- `../docs/ADIYAT_AR.md` — **2026-04-21** plain-language Arabic reader-friendly Adiyat doc (includes exp50 cross-corpus result)

## What lives here

| File | Role |
|---|---|
| `paper.md` | **v3.0 paper** (21 kB) — the 2026-04-17 markdown manuscript. Do NOT update; this is a citable snapshot. |
| `README.md` | v3.0 arXiv-submission instructions (pandoc → PDF, etc.) |
| `requirements.txt` | Pinned Python deps as of v3.0 |
| `preregistration_v73_addendum.md` | Post-hoc code-state lock for v7.3 R12 tests (2026-04-20) |
| `osf_deposit_v73/` | OSF deposit zip + SHA manifest (v7.3) |
| `supplementary/` | Frozen v3.0 supplementary: `QSF_REPRODUCE.ipynb`, `REPLICATION.md`, `FINDINGS_SCORECARD.md`, `ADIYAT_CASE.md`, `ADIYAT_ANALYSIS_AR.pdf` |

## Why keep a stale packet?

1. **Reproducibility of v3.0 claims.** Reviewers / readers citing v3.0 need to find the exact text they cited.
2. **OSF deposit integrity.** `osf_deposit_v73/qsf_v73_deposit.zip` has a SHA that must hash-verify against the packet contents.
3. **Diff-able history.** `docs/PAPER.md` v7.4 vs `arxiv_submission/paper.md` v3.0 shows exactly what changed across 4 versions.

## Do NOT

- Edit `paper.md` here — update `../docs/PAPER.md` instead.
- Treat `supplementary/ADIYAT_CASE.md` as the current Adiyat doc — use `../docs/ADIYAT_CASE_SUMMARY.md`.
- Treat `supplementary/FINDINGS_SCORECARD.md` as the current scorecard — use `../docs/RANKED_FINDINGS.md`.
- Treat `supplementary/QSF_REPRODUCE.ipynb` as the reproducibility notebook — use `../notebooks/ultimate/QSF_ULTIMATE.ipynb`.

## If you need to update this packet for a NEW submission

1. Archive this entire directory to `archive/arxiv_submission_v3.0_snapshot/`.
2. Create a fresh `arxiv_submission/` from the current `docs/PAPER.md` + build a fresh OSF deposit zip.
3. Write a fresh `STATUS.md` noting the new submission version.

---

*Created 2026-04-21 as part of the v7.4 workspace cleanup; updated 2026-04-21 (v7.5 doc-reconciliation patch) to point to the v7.5 current-paper set and add the top-of-file DEPRECATED banner note for `paper.md`. See `../PROJECT_MAP.md` for the full legacy → current doc index.*
