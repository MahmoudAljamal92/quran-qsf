# PREREG — exp99_adversarial_complexity (H54; closes C6 of F57 + complexity reframe)

**Hypothesis ID**: H54
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Pre-registered before any adversarial generation is run.**

**Scope directive**: Whole 114-surah Quran as the canonical anchor. EL+rhyme+root-aware Markov-3 generator with optional joint constraints.

---

## 1. Background

The Quran (Q 41:42) describes itself as "لَا يَأْتِيهِ الْبَاطِلُ
مِنۢ بَيْنِ يَدَيْهِ وَلَا مِنْ خَلْفِهِ" — "falsehood cannot
approach it from before or behind." This claim has been *partially*
operationalised in the QSF project (R5 retraction notes 50 % of
EL-aware Markov forgeries fail on T) but never under a **joint
multi-constraint** test.

This experiment closes claim C6 of F57 by running an **adversarial
joint-constraint test**: generate `N = 10⁶` Markov-3 forgeries
with progressively-increasing constraint sets, measure how many
pass each combination of `Gate 1 ∧ F55 ∧ F56` simultaneously, and
report **(a) the empirical pass rate** (the H54 substantive claim)
and **(b) the empirical complexity scaling** of generating valid
forgeries as a function of joint-constraint count `k` (the
feedback-suggested theoretical reframing toward
constraint-satisfaction hardness).

---

## 2. Hypothesis (H54)

**H54** (one-sided, hash-locked).

Generate `N_FORGERIES = 10⁶` Markov-3 Arabic forgeries from the
project's locked Markov-3 generator (`expP17_markov_saj_adversarial`
seed = 99000, EL+rhyme+root-aware mode). For each forgery `f`,
evaluate three independent detectors:

- **Gate 1**: 5-D Φ_M Mahalanobis distance to Quran centroid; pass = inside hyperplane (`SVM·f ≥ 0`).
- **F55**: bigram-shift detector at frozen τ = 2.0; pass = `Δ_bigram(f, Quran-canonical) ≤ 2.0` (any 1-letter neighbourhood of Quran).
- **F56**: EL-fragility; pass = `EL_frag(f) ≥ 0.50` (matches Quran-class).

Define joint pass: `JointPass(f) = Gate1(f) ∧ F55(f) ∧ F56(f)`.

**H54 PASS criterion**: `n_joint_pass / N_FORGERIES ≤ 10⁻⁵`
(at most 10 forgeries out of 10⁶ pass all three).

**H54 STRICT criterion**: `n_joint_pass = 0` (no forgery passes
all three).

If `n_joint_pass = 0`, claim C6 (verse 41:42 falsehood-blocking)
is CONFIRMED, with empirical Bayes-factor evidence
`log(N_FORGERIES + 1) / 1 ≈ 13.8 nats` per Clopper-Pearson
on the joint-pass rate.

---

## 3. Empirical complexity scaling (the feedback-suggested deeper claim)

For `k ∈ {1, 2, 3}`, generate forgeries with progressively more
joint constraints active and measure **time-to-first-valid forgery**
`T_k`:

| k | Active constraints | Expected T_k scaling under "joint hardness" |
|---|---|---|
| 1 | Just Gate 1 | polynomial in N |
| 2 | Gate 1 ∧ F55 | exponential or polynomial-with-large-base |
| 3 | Gate 1 ∧ F55 ∧ F56 | exponential or unreachable |

If `log T_k` grows super-linearly in `k`, this is **empirical
evidence for joint-constraint forgery being computationally hard**
on the Markov-3 generator class. This is **not a proof of NP-hardness**
(which would require a polynomial reduction from a known-hard
problem), but it is a publishable empirical complexity scaling.

---

## 4. Frozen constants

```python
N_FORGERIES         = 1_000_000
MARKOV_ORDER        = 3
GENERATOR_SEED      = 99000
LENGTH_SAMPLE_RANGE = (5, 50)            # verses; matches Quran short-band envelope
GATE1_PASS_RULE     = "svm_decision >= 0"     # use expP7's locked SVM weights
F55_TAU             = 2.0
F56_THRESHOLD       = 0.50
JOINT_PASS_TARGET   = 10                  # H54 PASS allows up to 10 of 10^6
JOINT_PASS_STRICT   = 0                   # H54 STRICT requires zero
```

---

## 5. Audit hooks

1. **A1** Generator produces ≥ 99 % syntactically valid Arabic-letter sequences.
2. **A2** All three detectors evaluate without error on ≥ 99.9 % of forgeries.
3. **A3** Markov-3 generator does NOT memorise canonical Quran verses (verbatim-hit rate < 0.1 %).
4. **A4** Gate 1 SVM weights (`w`, `b`) match `expP7` locked values within tolerance.

---

## 6. Verdict ladder

1. `FAIL_audit_<hook>`
2. `FAIL_too_many_joint_pass` — `n_joint_pass > 10` of 10⁶
3. `PARTIAL_low_joint_pass` — `1 ≤ n_joint_pass ≤ 10`
4. `PASS_H54_meta_finding` — `n_joint_pass = 0` (strict criterion)

---

## 7. What this PREREG does NOT claim

- Does **not** prove NP-hardness of joint forgery (only empirical scaling).
- Does **not** test cross-tradition forgery (Phase 3).
- Does **not** un-retract R5 (R5 is about a different cascade, not this joint-constraint test).

---

## 8. Outputs

- `results/experiments/exp99_adversarial_complexity/exp99_adversarial_complexity.json` — per-forgery joint pass count, per-k time-to-first-valid, audit hooks, verdict.
- Optional: `results/figures/exp99_complexity_scaling.png` (log T_k vs k).
