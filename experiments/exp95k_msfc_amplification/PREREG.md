# PREREG — exp95k_msfc_amplification (H44)

**Hypothesis ID**: H44
**Filed**: 2026-04-26 night (v7.9-cand patch G post-V1-iv)
**Pre-registered before any scoring on the cross-corpus Δ_min sweep is performed.**

---

## 1. Background

`exp95j_bigram_shift_universal` (H43, PASS_universal_perfect_recall_zero_fpr)
demonstrated that the symbolic bigram-shift detector
`Δ_bigram(canon, candidate) = ‖hist_2(canon) − hist_2(candidate)‖₁ / 2`
under frozen `τ_high = 2.0` achieves recall = 1.000 across all 139,266 V1
single-letter forgery variants of all 114 Quran surahs and FPR = 0.000
across all 548,796 (Quran_canon, non-Quran_peer) pairs in
`phase_06_phi_m`. The closest peer pair sits at Δ_min = 73.5, more than
36× the firing threshold τ_high = 2.0.

The H43 result establishes a property of the bigram-shift detector with
**Quran as the designated canon**. It does NOT establish whether this
amplification (large safety margin between the τ_high firing threshold
and the closest peer) is **Quran-distinctive** vs other Arabic registers
that could also serve as "canon" in their own forgery-detection cascade.

This pre-registered experiment H44 closes that gap by computing the
analogous Δ_min sweep with **each Arabic corpus in turn as the
designated canon** and ranking the safety margins.

The architectural framing is the **Multi-Scale Forgery Cascade (MSFC)**:

- **Gate 1** — Quran-class membership via 5-D Φ_M Hotelling T² (locked
  AUC = 0.998; no analogous classifier exists for any other Arabic
  register, so Gate 1 is structurally Quran-only).
- **Gate 2** — multi-scale edit detection cascade. Sub-gate 2A is the
  bigram-shift Δ-statistic of `exp95j`. **This pre-reg targets the
  Quran-amplification claim for sub-gate 2A.**

---

## 2. Hypothesis

**H44** (one-sided, hash-locked).

Define `safety_margin(C) := min_{u ∈ C} min_{p ∉ C} Δ_bigram(u, p)`,
where the inner minimum is taken over all units `p` in the non-`C` peer
pool in `phase_06_phi_m` and the outer minimum over all units `u` of
corpus `C`. The safety margin is the worst-case bigram-shift distance
from any unit of `C` to any non-`C` peer; a larger value means the
bigram-shift detector with `C` as canon has a wider firing-rejection
gap and consequently a stronger forensic-discrimination property.

**H44**: among the 7 Arabic corpora in `phase_06_phi_m`
(`quran`, `poetry_jahili`, `poetry_islami`, `poetry_abbasi`, `ksucca`,
`arabic_bible`, `hindawi`), Quran has the strictly largest safety
margin.

Equivalently: the Δ_bigram detector's safety margin is uniquely
maximised by `canon = Quran` over the Arabic-corpus pool. This
establishes Quran-distinctive *amplification* of the bigram-shift gate
even though the gate itself (Δ_bigram ≤ 2 ⇒ 1-letter substitution) is
mathematically universal.

---

## 3. Verdict ladder (strict order)

The first matching branch fires.

1. `FAIL_audit_quran_drift` — `safety_margin(quran)` differs from the
   `exp95j` reproduction by more than 0.5 (sanity: should be 73.5).
2. `FAIL_quran_not_top_1` — Quran is not strictly the largest safety
   margin across the 7 Arabic corpora.
3. `PARTIAL_quran_top_1_within_eps` — Quran is the largest by ≤ 5%
   margin over the next-ranked corpus (weak Quran-amplification claim).
4. `PASS_quran_strict_max` — Quran's safety margin is strictly larger
   than any other Arabic corpus in the pool by > 5% margin.

The `PASS_quran_strict_max` verdict supports the MSFC sub-gate 2A
amplification claim: even though the bigram-shift gate is universal
(works for any canon), the Quran-as-canon instance has the *largest
safety margin* of any natural Arabic corpus.

---

## 4. Frozen constants

- `TAU_HIGH = 2.0` (the firing threshold from H43; for diagnostic FPR
  numbers per corpus only — not used in the H44 verdict).
- `EPS_TOP1 = 0.05` (5% margin for `PASS_quran_strict_max`).
- `MIN_UNITS_PER_CORPUS = 20` (corpora with fewer units are reported
  but excluded from the verdict rank to avoid degenerate tie-breaking).
- Corpus pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi,
  ksucca, arabic_bible, hindawi}` — 7 Arabic corpora in
  `phase_06_phi_m`. `hadith_bukhari` is excluded per the project's
  hadith-quarantine convention. `iliad_greek` is excluded as
  non-Arabic.
- Bigram normalisation: `letters_28` (per `exp95j`); identical to the
  pipeline used in H43.

---

## 5. Audit hooks

- `audit_quran_safety_margin_reproduction`: H43's reported
  `safety_margin(quran)` is 73.5; this run must reproduce it within
  ±0.5.
- `audit_min_units_per_corpus`: every corpus included in the
  rank-comparison must have ≥ `MIN_UNITS_PER_CORPUS` units.
- `audit_no_self_pair`: per-unit Δ_min must exclude the unit's own
  bigram histogram (only inter-corpus pairs).

---

## 6. Reproduction

```powershell
python -m experiments.exp95k_msfc_amplification.run
```

Single-process; in-memory bigram-counter cache; ~minutes wall-time on
a single core. Outputs:

- `results/experiments/exp95k_msfc_amplification/exp95k_msfc_amplification.json`
- `results/experiments/exp95k_msfc_amplification/per_corpus_summary.csv`

---

## 7. Scope and disclaimers

- **What this PREREG closes** (if PASS): the Quran-amplification claim
  for MSFC sub-gate 2A only. Other gates (Gate 1 membership, Gate 2B
  R2 sliding-window, Gate 2C per-verse EL) are addressed by
  pre-existing receipts (`§4.1`, `§4.5`, `§4.14` of `PAPER.md`) and
  are not re-proved by this experiment.

- **What this PREREG does NOT establish**: a cross-tradition claim
  (corpus pool is Arabic-only); a structural Quran-uniqueness *law*
  (all retracted laws stay retracted); a proof that no synthetic
  forger could produce a closer peer (we test against natural Arabic
  corpora).

- **Falsification clause**: if the verdict ladder fires
  `FAIL_quran_not_top_1`, the MSFC sub-gate 2A amplification claim is
  retracted and the bigram-shift gate is documented as a universal
  detector with no Quran-specific amplification beyond the recall
  theorem. The H43 PASS is unaffected (recall = 1.000 by theorem; FPR
  = 0.000 vs Arabic peers); only the *amplification ranking* claim is
  withdrawn.

---

*PREREG locked at this file's SHA-256 in `PREREG_HASH.txt`. Any change
to this file invalidates the lock and prevents `run.py` from
executing.*
