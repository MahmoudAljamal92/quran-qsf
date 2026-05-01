# QSF External-AI Handoff Pack — 2026-04-25

**Read order**: `00 → 01 → 02 → 03 → 04 → 05 → 06`. All seven files are self-contained; you do not need any other file in the repository to interpret the claims.

---

## 0. What this project is

The **Quranic Structural Fingerprint (QSF)** project asks **one question**:

> *Is there a measurable, reproducible mathematical signature that distinguishes the Quran from every other classical-Arabic text and, ideally, generalises to a cross-tradition law that singles it out at ≥ 99 % accuracy along ≥ 1 dimension?*

The original framing was Quran-as-Arabic-reference, with optional generalisation across other languages and oral-liturgical scriptures. The project has run for one calendar year (Apr 2025 → Apr 2026), produced **47 honest retractions** and **43 surviving positive findings**, and is currently at the brink of a 5-paper submission round.

## 1. What is locked vs what is in flux

**Locked** (machine-checkable in `results/integrity/results_lock.json`, hash pinned, 58 tolerance-gated scalars):

- 5-D fingerprint `(EL, VL_CV, CN, H_cond, T)` on Band-A surahs (15–100 verses)
- `Φ_M = Hotelling T² = 3 557` between 68 Quran Band-A surahs and 2 509 Arabic-control units
- Analytic F-tail `log10 p_F = −480.25` (~47σ-equivalent)
- Nested-CV AUC = 0.998 (5-D); EL-only AUC = 0.9971
- LC3-70-U linear discriminant: `L = 0.5329·T + 4.1790·EL − 1.5221`, AUC = 0.9975
- Cross-tradition R3 path-minimality: SUPPORT (8/8 leave-one-out robust)
- Mushaf J1 smoothness: strict global extremum at 10⁶ permutations (p < 10⁻⁶)
- 4 Tier-grade audits passed (Tiers 2–5, 0 HIGH / 1 MED / 24 LOW cumulative flags)

**Recently resolved** (2026-04-25 evening):

- **§4.4 T_alt decision — LOCKED C1**. T_canon stays canonical (Φ_M = 3 557 / ~47σ-equivalent). T_alt (Φ_M = 3 868, +1.33σ at Band-A; FAILS at Band-C) becomes the headline of P7 (atomic methodology paper). `results_lock.json` is unchanged. Reopen iff project re-targets to Option B / PRX TIT / PNAS. See `05_DECISIONS_AND_BLOCKERS.md` Q1.

**In flux** (external blockers):

- **OSF DOI** — pre-registration deposit prepared, SHA `2f90a87a…` in `arxiv_submission/osf_deposit_v73/`. **Not yet uploaded**. See `05_DECISIONS_AND_BLOCKERS.md` Q2.
- **Riwayat invariance (Warsh / Qalun / Duri)** — pipeline exists, data missing. 15-min test once files arrive.
- **Two-team external replication** — required to upgrade any "law" claim from empirical to externally validated.

## 2. What this pack contains

| File | Role |
|---|---|
| `00_START_HERE.md` | This file — orientation + read order |
| `01_RANKED_FINDINGS_TABLE.md` | The single ranked table of all findings, in significance order, with strength %, scalar, and submission-readiness verdict |
| `02_UNIVERSAL_LAW_AND_SIMPLE_MATH.md` | The simple-math synthesis: which equations, which constants, which 1-feature/2-feature laws, what is and isn't a "universal" |
| `03_NOBEL_AND_PNAS_OPPORTUNITIES.md` | Specifically what was overlooked or only partly tested; ranked by reach × tractability |
| `04_RETRACTIONS_LEDGER.md` | All 47 honest retractions, compact, do-not-reopen |
| `05_DECISIONS_AND_BLOCKERS.md` | Decision tracker: §4.4 T_alt resolved (C1 LOCKED 2026-04-25), OSF pre-reg pending, plus the rest of the user's open questions |
| `06_CROSS_DOC_AUDIT.md` | Zero-trust audit: scalar contradictions found across the project's docs, with the canonical value chosen and the patches applied |

## 3. What the project deliberately does NOT claim

- No theology, no divinity, no "miracle" framing.
- No claim that "Quran is uniquely strongest on every metric" — it is not. Tanakh and NT beat Quran on R3 path-minimality magnitude; Rigveda is the strongest signal in the dataset on path-minimality (z = −18.93).
- No Nobel-tier framing in the public submission plan. PNAS is the stretch ceiling, *Entropy* / *PRX Information* / *PLOS ONE* / *Computational Linguistics* are the realistic ceiling.
- No universal "Ψ_oral ≈ 5/6" constant — falsified 2026-04-25 (retraction #28).
- No universal "R ≈ 0.70 across writing systems" — falsified 2026-04-25 (retraction #27); reframed as Abrahamic-script typology.
- No literal "Reed-Solomon-like error-correcting code" embedded in the Quran — falsified, UTF-8 confound (retraction #47).

## 4. Data on disk you can pull from if you want raw inputs

- `data/corpora/ar/` — Arabic raw texts (9 corpora, ~25 MB)
- `data/corpora/he/` — Hebrew Tanakh
- `data/corpora/el/` — Greek Iliad + NT
- `data/corpora/sa/` — Vedic Rigveda Saṃhitā (10 maṇḍalas, added 2026-04-25)
- `data/corpora/pi/` — Pali Tipiṭaka DN+MN (added 2026-04-25)
- `data/corpora/ae/` — Avestan Yasna (added 2026-04-25)
- `results/experiments/expNN_*/expNN_*.json` — 130+ per-experiment result JSONs
- `results/integrity/results_lock.json` — locked scalars
- `results/integrity/corpus_lock.json` — corpus SHA-256 ledger

## 5. Scope guardrail for any external advice you give

If you (the external AI being fed this pack) are asked to **propose new experiments**, please respect:

1. Do not propose to reopen any retraction in `04_RETRACTIONS_LEDGER.md` without specifying *fresh data* AND *fresh methodology*.
2. Do not propose theology-adjacent framings; this project is descriptive-stylometric only.
3. Honest ceiling is **PNAS stretch / IEEE Trans. Inf. Theory / Phys. Rev. E**, not Nature/Science.
4. If proposing a "universal law", you must specify (i) the corpora it generalises over, (ii) the falsification null, (iii) the leave-one-out robustness rule.
5. Default to the smallest viable experiment that decides a binary question.

---

*Pack assembled 2026-04-25 from `docs/reference/findings/RANKED_FINDINGS.md` v1.3, `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md`, `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md`, `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md`, `docs/reference/findings/RETRACTIONS_REGISTRY.md`, `docs/reference/findings/01_PROJECT_STATE.md`. Source-of-truth scalars trace to `results/integrity/results_lock.json` (58 entries, hash `3ecaf4b048…`).*
