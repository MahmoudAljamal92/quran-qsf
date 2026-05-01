# exp90_cross_language_el — PRE-REGISTRATION

**Timestamp**: 2026-04-21 (late evening, v7.7)
**Status**: Frozen BEFORE any run. No numerical result seen before this document committed.

---

## 1. Motivation

`exp89` and `exp89b` (both v7.7, today) revealed:
- `LC3` is a **1-feature theorem in EL** (AUC = 0.9971 on Band-A 68 Q + 2 509 Arabic ctrl).
- `T` is secondary (AUC 0.9677 alone), `H_cond` is at chance (AUC 0.518).
- 2-feature pairs (EL + anything) all land in 0.9970–0.9978; the second-feature choice is within bootstrap noise.

This simplifies the cross-language replication question to **one variable: does EL alone show scripture-class convergence across Arabic, Hebrew, and Greek?**

If yes, the cheapest PNAS-path step 1 (from `docs/RANKED_FINDINGS §3 row 3 Path-to-100% item (b)` and `DEEPSCAN §FINAL ASSESSMENT`) closes. If no, LC3-EL is Arabic-specific and the PNAS framing needs different evidence.

## 2. Corpora (all already on disk — zero new data needed)

| Group | Corpus | Source | Role |
|---|---|---|---|
| Arabic scripture | `quran` | `phase_06_phi_m.pkl` (Band-A) | Primary |
| Arabic scripture | `arabic_bible` | `phase_06_phi_m.pkl` (Band-A) | Secondary (translated scripture) |
| Arabic secular | `poetry_{jahili, islami, abbasi}`, `ksucca`, `hindawi` | `phase_06_phi_m.pkl` (Band-A) | Secular-Arabic control |
| Hebrew scripture | `hebrew_tanakh` | `data/corpora/he/tanakh_wlc.txt` via `raw_loader` | Test |
| Greek scripture | `greek_nt` | `data/corpora/el/opengnt_v3_3.csv` via `raw_loader` | Test |
| Greek secular | `iliad_greek` | `data/corpora/el/iliad_perseus.xml` via `raw_loader` | **Negative control** (narrative-chronological, NOT scripture) |

## 3. Hypotheses

**H-EL-CONV-GREEK**: Greek NT EL > Iliad EL at Cohen d ≥ 0.5 (scripture vs secular same-language).

**H-EL-CONV-HEBREW-PROXY**: Tanakh EL > secular Arabic pool EL at Cohen d ≥ 0.5 (best available comparison; no secular Hebrew corpus in project).

**H-EL-Q-THRESH**: ≥ 25 % of Tanakh units AND ≥ 25 % of Greek NT units cross the LC3-70-U EL threshold at EL = 0.364 (the (T=0) projection of `0.5329·T + 4.1790·EL − 1.5221 = 0`).

## 4. Methodology (frozen)

- **Data**: Arabic from `phase_06_phi_m.pkl::state` (Band-A already applied). Cross-language from `raw_loader.load_all(include_extras=True, include_cross_lang=True)`.
- **Feature**: `src.features.el_rate(verses)` — language-agnostic end-char rhyme rate (fraction of verses ending in the single most common end-character).
- **Band-A filter**: `15 ≤ n_verses ≤ 100` per unit, applied uniformly across all corpora.
- **Cohen d**: pooled-SD standardised mean difference, computed with `ddof=1`.
- **Threshold**: EL ≥ 0.364 → Quran-side classification. (Derived from `exp70_decision_boundary.json::svm.equation_raw`: at `T = 0`, `EL = 1.5221 / 4.1790 = 0.3642`.)

## 5. Pre-registered verdict ladder (evaluated in order; first match wins)

1. **FAIL_iliad_high** — Iliad mean EL > arabic-poetry pool mean EL. Means Greek alphabet is EL-permissive; NT-vs-Iliad comparison invalid. INCONCLUSIVE as cross-language test.

2. **PASS_full_convergence** — All three conditions hold:
   - Greek NT EL > Iliad EL at Cohen d ≥ 0.5 AND
   - Tanakh EL > secular-Arabic-pool EL at Cohen d ≥ 0.5 AND
   - ≥ 25 % of Tanakh + ≥ 25 % of Greek NT units clear EL ≥ 0.364.
   → First cross-language scripture-convergence evidence; PNAS-path step 1 confirmed.

3. **PASS_partial_convergence** — Exactly one of (Tanakh, Greek NT) passes its d ≥ 0.5 and 25 %-threshold conditions; the other fails.
   → Scripture signal is not universal; publishable but narrower.

4. **FAIL_no_convergence** — Neither Tanakh nor Greek NT clears d ≥ 0.5 vs its control AND fewer than 25 % cross EL = 0.364.
   → LC3-EL is Arabic-specific; no PNAS-grade cross-language finding via this route.

5. **MIXED** — any other combination.

## 6. Stakes

- **PASS_full_convergence** → directly unlocks a PNAS-grade replication argument: EL (verse-final rhyme rate) is a scripture-class fingerprint independent of language. Triggers follow-up preregistration for Vedic / Avestan.
- **PASS_partial** → targeted paper: "scripture-class EL convergence confirmed for <language> but not <other>; structural or translation reasons TBD."
- **FAIL_iliad_high** → need secular Hebrew control (Rabbinic corpus?) before judging. Expand corpus before concluding.
- **FAIL_no_convergence** → honest result; LC3-EL stays Arabic-specific; paper framing adjusted; cross-language path does NOT pass through EL alone. Would need T or a different feature.

## 7. No parameter tuning

EL threshold 0.364, Cohen d cut 0.5, crossing-rate cut 25 %, Band-A bounds [15, 100] are all frozen. Any deviation requires a new experiment number and new PREREG.

---

*Pre-registration committed 2026-04-21. No result seen before this file was written.*
