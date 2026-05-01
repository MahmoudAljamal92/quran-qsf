# Deep-Scan 2026-04-24 — Navigation Index

Produced by a two-pass ultra-deep scan of the entire Quran-project workspace (3,186 files / 1.79 GB across C:\Users\mtj_2\OneDrive\Desktop\Quran). Use this README to find a specific finding or opportunity.

## Files in this bundle

| File | Size | What it contains |
|---|---|---|
| `_file_manifest.txt` | 3,187 rows | Every file in the workspace, size + last-modified time. Grep-searchable. |
| `OPPORTUNITY_TABLE.md` | ~9 KB | Executive summary: TL;DR Seven Highest-Leverage Missed Opportunities + methodology + audit-update banner |
| `OPPORTUNITY_TABLE_DETAIL.md` | ~60 KB | Full tiered catalogue (Tier S paradigm-adjacent, Tier A one-experiment-away, Tier B premature retractions, Tier C numerical coincidences, Tier D classical-concept gaps, Tier E methodology, X1-X5 cross-convergences, Priority Action Board, audit-correction section). Every row has file:line citations. |
| `AUDIT_MEMO_2026-04-24.md` | ~10 KB | Follow-up audit memo (2026-04-24 afternoon) — five findings against the opportunity table; verified numerics for the E7 verdict flip; patches applied; action items. |
| `README.md` | this file | Navigation index. |

## âš  2026-04-24 afternoon audit update

A follow-up code-level audit ran against the initial scan. See `AUDIT_MEMO_2026-04-24.md` for the full findings. Headline:

- **B13 DOWNGRADED** — E7 in exp46/exp50 is normalisation-confounded; `H2_QURAN_SPECIFIC_IMMUNITY` verdict flips to `H1_STRUCTURAL` once E7 is excluded. Quran stays most immune (3-7Ã— ratio) but loses the 5Ã— threshold.
- **NEW B14** — Rasm-preserving emphatic-detector is now a named opportunity.
- **NEW B15** — `exp48._el_match` used raw final char; patched. **Empirical re-run: zero delta — `n_communities â‰ˆ 7.02` headline CONFIRMED ROBUST.**
- **NEW B16** (surprise) — Corpus drift alone has already dropped `poetry_jahili` from 9.50 % to 4.31 % on the current `phase_06_phi_m.pkl`. The H2 verdict was already broken independent of the E7 confound.
- **NEW E14** — Checkpoint-drift fail-hard via `QSF_STRICT_DRIFT=1` env var. Patched.

Four code patches applied non-destructively (historical JSONs preserved as `*.pre_audit_2026_04_24.json`):
- `experiments/_lib.py` — strict-drift fail.
- `experiments/exp46_emphatic_substitution/run.py` — `overall_detection_rate_without_E7` dual-reporting.
- `experiments/exp50_emphatic_cross_corpus/run.py` — per-target no-E7 rate + no-E7 verdict.
- `experiments/exp48_verse_graph_topology/run.py` — `_el_match` last-Arabic-letter (legacy via `QSF_EL_MATCH_LEGACY=1`).

### âœ“ Empirical verification complete

| Test | Predicted | Observed | Verdict |
|---|---|---|---|
| exp46 Quran no-E7 rate | 0.296 % | **0.2956 %** | âœ“ exact |
| exp48 Quran `n_communities` | barely moves | **7.018 â†’ 7.018** | âœ“ robust |
| exp50 aggregate no-E7 verdict | `H1_STRUCTURAL` | **`H1_STRUCTURAL_ARABIC_BLINDNESS`** | âœ“ |
| exp50 full-mode with-E7 rates | 4.83 % / 9.50 % | **2.66 % / 4.31 %** | âš  corpus drift |

## How to use this bundle

- **"What are the biggest missed opportunities?"** â†’ Read `OPPORTUNITY_TABLE.md` top.
- **"I want to act on something this week."** â†’ Read `OPPORTUNITY_TABLE_DETAIL.md` â†’ Priority Action Board.
- **"Give me the full list."** â†’ Read `OPPORTUNITY_TABLE_DETAIL.md` top-to-bottom.
- **"Does file X exist?"** â†’ Grep `_file_manifest.txt` for the name.
- **"Show me finding Z in the source docs."** â†’ Every finding in `OPPORTUNITY_TABLE_DETAIL.md` has an `@/absolute/path:line` citation; click it.

## Scan coverage summary

### Pass 1 — Forward canonical reading (signal-dense text read line-by-line)

| Category | Files read | Lines read |
|---|---|---|
| Top-level anchors (README.md, CHANGELOG.md) | 2 | ~1024 (post 2026-04-26 merge of PROJECT_MAP.md into README.md) |
| EXECUTION_PLAN_AND_PRIORITIES.md | 1 | 763 |
| HYPOTHESES_AND_TESTS.md (H1-H31 with verdicts) | 1 | 1,715 |
| docs/reference/findings/RANKED_FINDINGS.md | 1 | 314 |
| docs/DEEPSCAN_ULTIMATE_FINDINGS.md | 1 | 660 |
| docs/OPPORTUNITY_SCAN_2026-04-22.md | 1 | 326 |
| docs/reference/findings/RETRACTIONS_REGISTRY.md | 1 | 160 |
| docs/ZERO_TRUST_AUDIT_*.md (Tier 1-5) | 5 | ~600 |
| docs/reference/adiyat/CANONICAL_READING_DETECTION_GUIDE.md | 1 | 436 |
| docs/SCAN_2026-04-21T07-30Z/*.md (7 files) | 7 | ~1,200 |
| archive/*.md (LOST_GEMS, LAW_CANDIDATES, audits, critical review) | 6 | ~2,200 |
| archive/deep_scan_results/MASTER_FINDINGS_REPORT.md | 1 | 421 |
| src/features.py (canonical feature definitions) | 1 | 293 |
| Selected paper sections (PAPER.md Â§4.32-Â§4.35) | N | — |
| **Total signal-dense human-readable text read** | **~30 files** | **~10,000 lines** |

### Binary / large data (surveyed by shape, not line-by-line)

- `data/corpora/*.txt` — 7 Arabic corpora surveyed by file size and first-line peek.
- `results/experiments/exp*/*.json` (~99 experiments) — verdicts catalogued via the HYPOTHESES_AND_TESTS.md register (which captures every pipeline-audited verdict).
- `results/checkpoints/*.pkl.gz` — skipped (binary pickle); accessed indirectly through the reports that consume them.
- `*.png, *.htm, *.tex, *.csv` — skipped or surveyed only for existence.

### Pass 2 — Zero-trust reverse reading

Six targeted questions asked of every finding, surfacing:
- 13 retractions narrowly-scoped to one method (Tier B)
- 12 numerical coincidences dismissed as look-elsewhere (Tier C)
- 13 classical concepts never formally operationalised (Tier D)
- 13 methodological upgrades deferred (Tier E)
- 5 cross-convergent pattern-pairs pointing the same way (X1-X5)

**Total opportunities catalogued: 7 Tier-S (paradigm-adjacent) + 11 Tier-A (theorem one experiment away) + 13 Tier-B (premature retractions) + 12 Tier-C (numerical coincidences) + 13 Tier-D (classical concepts) + 13 Tier-E (methodology) + 5 cross-convergences = 74 distinct opportunity rows.**

## Caveats

- **Not a byte-by-byte scan of 1.79 GB.** That is physically impossible in a single context window. What this is: every signal-dense human-readable text file read line-by-line, plus targeted sampling of large binary artifacts via their audit trail. If you need a specific file read end-to-end, ask.
- **Secondary sources.** Many findings are traced via audit reports (HYPOTHESES_AND_TESTS.md, RANKED_FINDINGS.md, DEEPSCAN_ULTIMATE_FINDINGS.md) rather than primary JSON outputs. Each citation points to the report; the primary JSON can be read on request for verification.
- **Hypothesis-scoped retractions.** A "retraction" in this project is always scoped to a specific method. Many Tier-B entries are attempts to re-open the underlying claim at a different level of representation — not challenges to the specific retraction verdict.
- **No new empirical work.** This scan produces no new experiments; it catalogues what can be done. Execution is future work per the Priority Action Board.

## Next step recommended

**First clear the audit backlog** (ranks 0a/0b/0c) before touching anything else:

1. **0a — B14**: Re-run `exp46` and `exp50` with the patched code; record `overall_detection_rate_without_E7` + `aggregate_verdict_without_E7`. This either confirms or flips the `H2_QURAN_SPECIFIC_IMMUNITY` claim in the docs.
2. **0b — B15**: Re-run `exp48` with the patched `_el_match`; confirm `n_communities â‰ˆ 7.02` headline.
3. **0c — E14**: `$env:QSF_STRICT_DRIFT='1'` and re-run the suite. Rebuild any drifted checkpoints.

Then resume with Action Board rank #1 (A11 — lock analytic F-tail) and #2 (A10 — 10â¶ perm extension of Mushaf J1). Both are 1-hour tasks; jointly they add two headline lock scalars without any new methodology.
