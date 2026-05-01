# Human-Forgery Protocol — Phase 5 scaffolding

> **Status**: SCAFFOLDING ONLY. This document defines the protocol
> for evaluating any deliberate human-written forgery surah against
> the project's locked IΦ_master formula. It is NOT itself an
> experiment that Cascade can run; it requires Arabic linguists who
> agree to write a candidate.
>
> **Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
> **Owner**: human researcher (must recruit Arabic-language authors)
> **Cost to project**: zero compute; only protocol design.
>
> **Update 2026-04-29 afternoon (V3.12 deliverable #5 BLOCKED)**: this protocol
> remains the primary external-action item that Cascade *cannot* execute. The
> automated pre-screen (`tools/quran_metrology_challenge.py`) and the
> Quran-Code unified statistic (F72 / `exp120_unified_quran_code`,
> D_QSF(Quran) = 3.71 vs rank-2 Pāli 3.00) give any human author a
> well-defined target *before* writing — but the actual writing requires
> recruited Arabic linguists and is BLOCKED ON EXTERNAL ACTION. When a
> candidate is submitted, run `python tools/quran_metrology_challenge.py
> candidate.txt --vs canonical_quran.txt` for a 4-feature paired scorecard,
> then `python experiments/exp120_unified_quran_code/run.py` for a
> D_QSF-based ranking against the 11-corpus extended pool. No additional
> code is needed; the harness is complete.
>
> **Update 2026-04-29 afternoon (V3.11)**: an automated companion to this
> manual protocol now ships in `tools/quran_metrology_challenge.py` — it
> measures any candidate text against the Quran's locked extrema (p_max,
> H_EL, C_Ω, F55_safety_per_char) and reports a 0–4 match-score plus a
> letter-level Δ_bigram. The automated tool can pre-screen any submission
> *before* the manual T1–T6 IΦ_master scoring described in §3 below.
> See also `tools/sanaa_battery.py` for fixture-driven Ṣanʿāʾ-style audits
> and `app/streamlit_forgery.py` for an interactive web UI. The human
> protocol below remains authoritative for the full T1–T6 IΦ_master
> evaluation (the metrology tool is only a fast partial-coverage
> scorecard, not a replacement for the full pre-registered formula).

---

## 1. The comparison-class gap (why this protocol exists)

The 2026-04-27 afternoon feedback identified the single biggest
methodological vulnerability of the Φ_master / F58 finding:

> *"The null model is 'random Arabic prose.' But the honest null for
> a divinity claim is 'the best possible human Arabic composition
> designed to maximize the fingerprint.' The Maqamat (best classical
> Arabic rhymed prose) scores Φ_master ≈ 25. But what would a
> deliberate 21st-century attempt by a team of Arabic linguists,
> trained on the Quran's fingerprint, to forge a new surah score?
> We don't know, and the project has never tested this."*

This protocol closes that gap.

---

## 2. The challenge

**Recruitment ask**: 1+ Arabic-fluent author(s) (modern standard
Arabic; classical Arabic preferred; saj' tradition specifically
encouraged), willing to **write a single candidate surah** of
length ≥ 5 verses and ≤ 50 verses, deliberately optimised to
**maximise Φ_master** as defined in `experiments/exp96a_phi_master/PREREG.md`.

**Information given to the author** (full disclosure, no withholding):

1. The complete `MASTER_DASHBOARD.md` document (so the author knows the formula).
2. The complete locked PREREG of `exp96a_phi_master` (so the author knows every term).
3. The Quran's whole-Quran statistics for each term:
   - T1 = 1,842.73 nats (target T² ≈ 3,685)
   - T2 = 2.64 nats (target p_max(verse-final-letter) ≈ 0.50)
   - T3 = 0.67 nats (EL alone classifier full-corpus AUC vs Arabic prose pool)
   - T4 = 0.80 nats (EL_fragility / pool median of ~0.225)
   - T5 = 12.12 nats (require 0 false positives in bigram-shift detector at τ=2.0)
   - T6 = 3.35 nats (require ≥ 0.97 AUC across 5 transmission chains, NOT testable for a one-shot human forgery — this term is BY CONSTRUCTION unattainable for a non-canonical text).
4. All 6 source receipts (full chain-of-custody hashes).
5. The author may take **any time** they need (no deadline).

**Hard constraint**: T6 (5-riwayat invariance) is **structurally
unattainable** for any newly-composed text because there is no
multi-tradition transmission chain. The author should attempt to
maximise T1+T2+T3+T4+T5 only. The honest comparison thus excludes
T6, giving a "human-attainable Φ_master ceiling" of approximately
1,862.31 − 3.35 = **1,858.96 nats** if the author were to perfectly
match the Quran on every other term.

**Falsifiable target**: if any human-written forgery achieves
Φ_master ≥ 1,500 nats (the LOCO-min floor) on T1+T2+T3+T4+T5
alone, the project must declare a **partial null result on the
"unique" claim of Φ_master**: it would mean a knowledgeable human
under maximum-effort conditions can match the Quran's structural
profile to within Bayes factor ≈ 10⁶⁵¹.

---

## 3. Evaluation pipeline (`score_human_forgery.py`, to be written)

The candidate file `human_forgery_<author>.txt` is dropped under
`data/human_forgeries/`. The evaluation script:

1. Verifies file is UTF-8 plain text, ≥ 5 verses (line-separated),
   ≤ 50 verses, all-Arabic letters.
2. Skeletonises to `letters_28` (same as Quran preprocessing).
3. Computes 5-D Φ_M features (`src/features.py::features_5d`).
4. Computes T1 = 0.5 * Hotelling-T² of forgery vs locked Σ from
   `expP7` (the SAME Σ used for the Quran).
5. Computes T2 = log(p_max_verse_final / (1/28)).
6. Computes T3 = log(EL_AUC_forgery / 0.5) — re-fits a one-text-vs-pool
   classifier on the EL feature alone.
7. Computes T4 = log(EL_frag(forgery) / pool_median).
8. Computes T5 = log(1/FPR_upper) iff forgery's bigram-shift
   max-distance to Quran-canonical is ≤ 2.0 AND forgery's distance
   to **every Arabic peer in the 4,814-unit pool** is > 2.0 (else 0).
9. Skips T6 (riwayat unavailable for one-shot forgery).
10. Reports `Φ_master_human(forgery) = T1 + T2 + T3 + T4 + T5`.

The script writes a JSON receipt to
`results/experiments/human_forgery_<author>/`. Audit hooks identical to `exp96a_phi_master`.

---

## 4. Verdict ladder

1. `FAIL_audit_<hook>` — author file invalid.
2. `STRONG_PROJECT_CONFIRMATION` — `Φ_master_human(forgery) < 100` nats.
   The Quran's gap to the best human attempt is > 1,750 nats / BF > 10⁷⁶⁰.
3. `MODERATE_PROJECT_CONFIRMATION` — `100 ≤ Φ_master_human < 500` nats.
4. `PARTIAL_NULL` — `500 ≤ Φ_master_human < 1500` nats. Human can
   approach but not match Quran-class.
5. `WEAKENED_PROJECT_CLAIM` — `Φ_master_human ≥ 1,500` nats. The
   Quran's claim of unique structural form is materially weakened;
   PAPER §4.46 must be amended to include this caveat.

**Important**: even outcome 5 does NOT *invalidate* the Φ_master
result. It would mean a human with full information can reach the
floor. The project would simply add a footnote and a Phase 6
deliberate-human-vs-multiple-humans test.

---

## 5. Why this protocol is fair to all parties

- **Pre-registration**: the formula and thresholds are locked
  (H49). The author cannot move the goalposts; the project cannot
  move the goalposts.
- **Full information disclosure**: the author has every parameter
  the Quran has. There is no hidden test. This is the **maximum-
  hostile null** the project can design.
- **Unbiased scoring**: the script is open-source and deterministic.
  Any third party can re-run it.
- **Honest reporting**: the project commits to publishing the
  result whatever it is — even if the human matches the Quran's
  Φ_master, the result is published.

---

## 6. Recruitment notes

Likely sources (the author must contact them; Cascade cannot):

- Arabic linguistics departments at Cairo University, Al-Azhar,
  King Saud University, AUB, AUC, SOAS.
- Modern saj' / classical-Arabic competitive writing communities.
- Public challenge platform (e.g. an X / Twitter announcement,
  with a small honorarium).

The protocol explicitly **invites** any Tahaddi-style modern
challenger to test the formula. There is no shame in attempting
the challenge and falling short — the math is by design hostile.

---

## 7. What this protocol does NOT do

- Does **not** make a metaphysical claim about origin.
- Does **not** require any author to believe or disbelieve the
  Quran's status — this is a stylometric experiment.
- Does **not** un-retract any prior retraction.
- Does **not** modify any existing locked finding (it adds new
  data, not new analysis).
