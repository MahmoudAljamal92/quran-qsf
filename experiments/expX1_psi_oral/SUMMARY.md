# expX1_psi_oral — Summary

**Date**: 2026-04-25
**Status**: COMPLETE. Pre-registered (PREREG.md frozen before any cross-corpus number was consulted). Self-check OK.

## Verdict: NO_SUPPORT (sanity gate PASS)

The reviewer's proposed universal `Ψ_oral = H(diac|base) / (2·I(EL;CN)) ≈ 5/6` is **falsified** as a cross-tradition constant by direct measurement on 7 non-Quran corpora, while the Quran sanity gate reproduces the locked `0.83574` to a drift of `3 · 10⁻⁵` (well below the pre-registered `5 · 10⁻³` tolerance).

| Pre-reg gate | Verdict |
|---|:---:|
| **PSI-S1** (sanity: Quran reproduces locked 0.8357 to ±5e-3) | **PASS** (drift 3e-5) |
| **PSI-1** (loose: ≥3 of 5 oral corpora yield Ψ ∈ [0.65, 1.00]) | **FAIL** (0 of 5) |
| **PSI-2** (tight: ≥3 of 5 oral corpora yield Ψ ∈ [0.7733, 0.8933]) | **FAIL** (0 of 5) |
| **PSI-3** (negative control: Iliad outside tight band) | **PASS** |

## Per-corpus measurements

| Corpus | Class | n_units | H(d|b) bits | I(EL;CN) bits | **Ψ_oral** |
|---|---|---:|---:|---:|---:|
| **quran** (Arabic, T7-anchored) | oral_liturgical | 114 | 1.9639 | 1.1749 | **0.8358** |
| hebrew_tanakh (Hebrew, niqqud + cantillation) | narrative_or_mixed | 921 | 2.7159 | 0.0523 | **25.94** |
| greek_nt (Greek polytonic) | narrative_or_mixed | 260 | 0.8760 | 0.3771 | **1.161** |
| iliad_greek (Greek polytonic) | narrative_or_mixed | 24 | 1.0856 | 2.0000* | 0.271 |
| pali_dn (Latin IAST) | oral_liturgical | 34 | 0.4699 | 1.5269 | 0.154 |
| pali_mn (Latin IAST) | oral_liturgical | 152 | 0.4632 | 0.5277 | 0.439 |
| rigveda (Devanagari, full mātrās + svaras) | oral_liturgical | 1024 | 3.7540 | 0.1110 | **16.91** |
| avestan_yasna (Latin Geldner) | oral_liturgical | 72 | 0.0000 | 1.0164 | **0.000** |

*Iliad I(EL;CN) = 2.000 bits is the maximum achievable on 10×10 quantile bins with n=24 — small-sample saturation, not a real measurement.

## Why the universal fails

Ψ_oral is a ratio of two quantities that are **not commensurable across scripts** under uniform code:

1. **Numerator H(d|b)** is dominated by the script's combining-mark inventory size:
   - Avestan Geldner = 0 bits (transliteration uses ASCII letters for special phonemes; no combining marks).
   - Pali IAST = 0.46 bits (5 distinct combining marks: macron, dot-below, dot-above, n-tilde, ring).
   - Quran (curated harakat) = 1.96 bits (27 distinct harakat strings, T7-anchored).
   - Greek NT = 0.88 bits (combining acute, grave, circumflex, smooth/rough breathings, iota subscript).
   - Hebrew Tanakh = 2.72 bits (niqqud + cantillation marks combined; the WLC text mixes both, vocab=104).
   - Devanagari Rigveda = 3.75 bits (mātrās + anusvara + visarga + svara + halant; vocab=94).

2. **Denominator I(EL;CN)** is dominated by the per-corpus stop-word definition:
   - Quran uses the linguistically curated `ARABIC_CONN` (14-item discourse-connective set, paper §2.2).
   - Every other corpus uses `derive_stopwords(verses, top_n=20)` — the 20 most frequent tokens, which for narrative texts are pronouns and articles (non-connectives).
   - Result: I(EL;CN) varies by **two orders of magnitude** across corpora (0.05 to 2.00 bits) and is dominated by stop-list construction artefact, not by genuine information-theoretic coupling.

The two scaling problems compound multiplicatively in Ψ_oral, producing measurements that span more than four orders of magnitude across our 8-corpus universe.

## What this closes

| Question | Answer |
|---|---|
| Does the formula `Ψ_oral = H(harakat|rasm) / (2·I(EL;CN)) = 0.8357` reproduce on the Quran? | **YES**, byte-faithfully (drift 3e-5). |
| Was the formula in the codebase before this experiment? | The arithmetic identity was in `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md:31`. The cross-corpus computation was not. |
| Is `Ψ_oral ≈ 5/6` a cross-tradition universal? | **NO** under the operational definition tested here. |
| Is the proposed universal *rescuable*? | Possibly, if (a) the diacritic set is curated per script with cross-script equivalence rules, and (b) I(EL;CN) is computed against a linguistically curated discourse-connective set per corpus (not top-20 frequency stop-words). Both are non-trivial linguistic curation tasks. **Without those, the universal is operationally undefined**, which means the n=1 Quran value at 5/6 is a numerical coincidence, not the leading edge of a universal. |
| What does this mean for the **5/6 oral-transmission optimality** working hypothesis from `SUBMISSION_READINESS §1.4`? | Three of its four legs are already known not to survive (`Ψ_oral` n=1, `γ_gzip` non-universal across compressors, `EL/EL_b ≈ 2` algebraic identity); the cross-corpus Ψ_oral measurement reported here is the empirical confirmation of the n=1 status of the first leg. Working hypothesis remains a working hypothesis; not a publishable claim without curated-stop-list re-test. |

## What this opens

The cross-tradition R3 (LC2 path-minimality) result remains **the** surviving cross-tradition universal, with Rigveda *z* = −18.93 actually stronger than Quran *z* = −8.92. **That** is the publishable headline. Ψ_oral is now correctly classifiable as a Quran-only numerical coincidence requiring a more sophisticated cross-corpus operationalisation before any universality claim can survive.

## Files

```
experiments/expX1_psi_oral/PREREG.md                      pre-registration (frozen)
experiments/expX1_psi_oral/run.py                         the experiment
experiments/expX1_psi_oral/SUMMARY.md                     this file
results/experiments/expX1_psi_oral/expX1_psi_oral.json    full per-corpus JSON
results/experiments/expX1_psi_oral/self_check_*.json      integrity receipt
```

Authoritative numbers are the JSON. This summary is narrative.

## Next actions (no user input required)

1. Update `RANKED_FINDINGS.md` retraction registry with retraction #28: "Ψ_oral as cross-tradition universal at 5/6". Add as the natural companion to retraction #27 (R diacritic universal) — both are 2026-04-25 cross-tradition falsifications of v7.6 working-hypothesis universals.
2. Update `corpus_lock.json :: cross_tradition_experiments_2026-04-25` with the expX1 verdict.
3. Update `docs/PROGRESS.md` banner to reflect that the Ψ_oral block is now CLOSED (no longer "blocked on reviewer formula").
4. Update `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md` §5 from "the only thing that did NOT close today" to "now closed: 5/6 universality falsified".

## What this does NOT close (out of scope)

- Whether a *different* operationalisation of Ψ_oral, with curated per-language stop sets and per-script diacritic sets aligned to the source's actual phonological augmentation system, would yield convergence to 5/6. That experiment is well-defined and would take ~1 day of linguistic curation. It is **not** what the reviewer asked for and we don't claim to have tested it.
