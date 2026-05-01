# exp157 — F75 β cognitive-channel derivation (Miller 7±2 finite-buffer MAXENT + 3-route convergence)

**Hypothesis ID**: H102_F75_Beta_CognitiveChannel_FiniteBufferMAXENT
**Parent**: H101 (V3.21 exp156, F75 first-principles MAXENT structural derivation)
**Authored**: 2026-04-30 evening (v7.9-cand patch H V3.22 candidate)
**Status**: PREREG-LOCKED. Hash committed below. Run.py reads this hash before executing; mismatch aborts.

---

## 1. Background and motivation

`exp156` (V3.21, H101) established that `p_k ∝ exp(−μ_c · k^{β_c}) / Z(μ_c, β_c, A=28)` is the
unique max-entropy distribution under the fractional-moment constraint
`Σ k^{β_c} · p_k = M_{β_c}` (analytic theorem; PAPER §4.47.36.1). Per-corpus
`(μ_c, β_c)` was solved by joint inversion of `(p_max(c), H_EL(c))` for the 11
locked corpora, yielding mean β = **1.5787**, median β = **1.4734**, with Quran a
super-Gaussian outlier (β = 2.5284) and Pāli a near-pure-exponential (β = 0.97).

**The V3.21 result establishes the FORM of the per-corpus distribution from
MAXENT; it does NOT explain why the empirical mean β concentrates near 1.5.**
That mid-pool clustering is the gap CRITICAL-2 in
`docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` flagged as the
single missing step for "law-of-nature" status (paradigm-shift potential
87% → 95% per the user's framing).

This experiment tests three independent routes that could explain the mid-pool
β ≈ 1.5 from cognitive-channel principles:

- **Route A (rigorous, REPLICATION)**: MAXENT analytic theorem already established in V3.21.
  Re-cited here as the foundation; no new claim.
- **Route B (numerical, NEW)**: under Miller 7±2 finite-buffer constraint
  `Σ_{k > B} p_k ≤ ε` with B = 7, the MAXENT optimum β converges to ≈ 1.5 across
  a range of (M_β, ε) operating points consistent with the V3.21 empirical mean.
- **Route C (empirical regression, NEW)**: per-corpus β_c is well-modelled as a
  monotone function of the rhyme-concentration index `p_max(c)`; the regression
  intercept at the V3.21 pool's median p_max ≈ 0.286 falls in [1.3, 1.7].

**This is NOT a deductive theorem-from-axioms derivation of β = 3/2 as a universal
constant.** β = 3/2 is the **mid-pool central tendency** under cognitive-channel
constraints (finite buffer + fractional moment). Per-corpus variation (Pāli 0.97,
Quran 2.53) reflects genuine rhyme-concentration differences — NOT a violation
of the cognitive-channel framework, but a quantitative diagnostic of where each
corpus sits within the cognitive-channel design space.

---

## 2. Frozen hypothesis (PREREG-locked)

**H102 (locked)**: under MAXENT with two simultaneous constraints — (1) probability normalisation
`Σ_{k=1}^{A} p_k = 1`, (2) fractional moment `Σ_{k=1}^{A} k^β · p_k = M_β` — and a
finite-buffer regularisation `Σ_{k > B} p_k ≤ ε` capturing Miller's 7±2 working-memory
limit, the MAXENT-optimal β at the V3.21 empirical operating point (`M_β` set to the
pool-mean of the 11-corpus V3.21 fits, B = 7, ε ∈ {0.01, 0.05, 0.10}) lies in **[1.3, 1.7]**
across the operating-point grid, with Route C empirical regression intercept also
in [1.3, 1.7].

The verdict is determined by 5 pre-registered criteria evaluated jointly. Verdict
mapping:

| Criteria PASS count | Verdict |
|---:|---|
| 5 / 5 | `PASS_F75_beta_cognitive_strong` |
| 4 / 5 | `PASS_F75_beta_cognitive_partial` |
| 3 / 5 | `PARTIAL_F75_beta_cognitive_directional` |
| ≤ 2 / 5 | `FAIL_F75_beta_cognitive_indeterminate` |

---

## 3. Frozen constants (PREREG-locked)

```
SEED = 42
A_ALPHABET = 28          # 28-letter Arabic-class abjad (matches V3.21 exp156)
B_BUFFER = 7             # Miller (1956) 7±2 central
B_BUFFER_RANGE = [5, 7, 9]  # Miller's 7±2 explicit range for sensitivity
EPS_BUFFER = 0.05        # leak past buffer (5% probability mass beyond k=B)
EPS_BUFFER_RANGE = [0.01, 0.05, 0.10]  # tightness sensitivity
M_BETA_FROM_EXP156 = "pool_mean of Σ k^{β_c} p_{k,c} across the 11 V3.21 corpora at each corpus's own β_c"
M_BETA_OPERATING_POINTS = [
  "low",     # 25th percentile of M_β across corpora
  "median",  # 50th
  "high",    # 75th
]
BETA_GRID = numpy.linspace(0.5, 3.5, 121)  # 0.025-step grid; finite-buffer MAXENT evaluated at each
ROUTE_A_BETA_OPT = 1.50  # V3.20 LOO modal (cited, not re-derived; provides anchor for "in-band")
ROUTE_C_REGRESSION_BAND_LO = 1.3
ROUTE_C_REGRESSION_BAND_HI = 1.7
ROUTE_B_OPT_BAND_LO = 1.3
ROUTE_B_OPT_BAND_HI = 1.7
ROUTE_B_SENSITIVITY_BAND_LO = 1.2
ROUTE_B_SENSITIVITY_BAND_HI = 1.8
THREE_WAY_AGREEMENT_TOL = 0.20  # |Route_X - Route_Y| ≤ 0.20 across all pairs
EXP156_RECEIPT_PATH = "results/experiments/exp156_F75_beta_first_principles_derivation/exp156_F75_beta_first_principles_derivation.json"
EXP156_EXPECTED_SHA256 = "<filled by run.py before computation; locked before any criterion is evaluated>"
```

---

## 4. Pre-registered criteria (each must independently PASS for the headline verdict)

### C1 — Numerical convergence at the central operating point (B=7, ε=0.05, M_β=median)

**PASS** iff the finite-buffer MAXENT optimization at the central (B, ε, M_β)
operating point terminates with **success status** AND the optimal `β_opt`
satisfies:
- All constraints respected to within 1e-6 (probability normalisation, fractional
  moment, buffer leak),
- Lagrangian gradient norm at optimum < 1e-5,
- Numerical Hessian positive-definite (Karush-Kuhn-Tucker satisfied at boundary).

### C2 — Route B central optimum in band [1.3, 1.7]

**PASS** iff `β_opt ∈ [ROUTE_B_OPT_BAND_LO, ROUTE_B_OPT_BAND_HI] = [1.3, 1.7]`
at the central operating point (B = 7, ε = 0.05, M_β = median pool value from exp156).

### C3 — Route B Miller 7±2 sensitivity stays in widened band [1.2, 1.8]

**PASS** iff at all 9 grid points (B, ε) ∈ {5, 7, 9} × {0.01, 0.05, 0.10} with
M_β = median, `β_opt ∈ [ROUTE_B_SENSITIVITY_BAND_LO, ROUTE_B_SENSITIVITY_BAND_HI]
= [1.2, 1.8]`.

### C4 — Route C empirical regression intercept in band [1.3, 1.7]

**PASS** iff the linear regression `β_c = a + b · log(p_max(c))` fitted on
the 11 V3.21 (β_c, p_max(c)) pairs satisfies:
- `R² ≥ 0.50`,
- intercept evaluated at the pool median `log(p_max) = log(median across 11 corpora)`
  yields a fitted β in [1.3, 1.7],
- coefficient `b > 0` (positive: more concentration → higher β, super-Gaussian regime).

### C5 — 3-way convergence within tolerance 0.20

**PASS** iff the three β estimates — Route A anchor (V3.20 LOO modal = 1.50,
literal constant, NOT re-fit), Route B central optimum (from C2), Route C
fitted-at-median (from C4) — all pairwise agree within `|Δ| ≤ 0.20`.

This is the strict "three independent routes converge" criterion. C5 PASS
provides the strongest version of the cognitive-channel claim.

---

## 5. Pre-registered audit hooks (must hold or the run is invalid)

A1. The exp156 receipt at `EXP156_RECEIPT_PATH` MUST exist and its SHA-256 MUST
    match the value frozen in `EXP156_EXPECTED_SHA256` (filled and locked at
    the start of this run; any drift aborts).

A2. The 11-corpus β values used in Routes B/C inputs MUST byte-match the
    `per_corpus_MAXENT_fit[*][beta]` field of the exp156 receipt (drift
    tolerance: 1e-12).

A3. Numerical operations MUST use `scipy.optimize` routines (one or more of
    `brentq`, `minimize_scalar`, `minimize`) where applicable, plus standard
    `numpy` for vectorised arithmetic. No hand-rolled solver invented purely
    for this experiment may be used as a primary optimizer; manual bisection
    is permitted ONLY as a sanity-check fallback when scipy.optimize is also
    invoked at the same operating point and the two agree to drift < 1e-6.

A4. The MAXENT functional form `p_k ∝ exp(−μ k^β)` (Route A) MUST NOT be re-derived
    or re-tuned in this run; it is cited from V3.21 PAPER §4.47.36.1 as a fixed
    analytic input. Any code path that adjusts the FORM of the distribution
    (e.g., adding a `c · k^γ` term) MUST raise an exception.

A5. No locked finding's PASS/PARTIAL/FAIL status MAY change as a side-effect of
    this run. F75 / F76 / F77 / F78 / F79 / F46 / F55 / F66 / F67 / LC2 verdicts
    MUST remain byte-identical to the V3.21 RANKED_FINDINGS.md text.

A6. Brown-Stouffer is NOT used; this experiment is purely numerical optimization
    plus regression. The post-V3.16 Brown-Stouffer audit fix is irrelevant here.

A7. The Tsallis q-exponential identity `q = 2 − 1/β` is mentioned in
    `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` as a candidate
    for cognitive-derivation route. This experiment does NOT use the Tsallis
    identity as a binding constraint; it is mentioned in the discussion section
    as a future path, not used as input.

---

## 6. Falsifiable predictions (commitments before run)

Pre-registered numerical predictions:

```
P1: β_opt at central operating point (B=7, ε=0.05, M_β=median) ∈ [1.3, 1.7]
P2: β_opt across 9-cell sensitivity grid stays in [1.2, 1.8]
P3: Route C intercept-at-median ∈ [1.3, 1.7], R² ≥ 0.50, b > 0
P4: 3-way pairwise agreement: max |Δ| ≤ 0.20
```

If P1 fails (central β_opt outside [1.3, 1.7]) the cognitive-channel
hypothesis with Miller 7±2 buffer is **falsified at the central operating point**
and the verdict can be no better than `PARTIAL_F75_beta_cognitive_directional`
(only Routes A + C remain).

If P3 fails (regression R² < 0.50 or intercept outside band), per-corpus
β-vs-rhyme-concentration is NOT a clean linear story; verdict drops at least one
tier.

If P2 succeeds and P1 also succeeds, the cognitive-channel claim is **robust to
B and ε within Miller-1956 bounds** — this is the substantive new contribution
of exp157 over exp156.

---

## 7. What this experiment does NOT claim

- It does **NOT** claim β = 3/2 is a universal constant of nature. β = 1.5
  is the mid-pool central tendency under finite-buffer MAXENT, with per-corpus
  variation reflecting rhyme-concentration design.
- It does **NOT** un-retract or re-strengthen any locked finding. F75's V3.21
  PASS status (5/5 strong) is unchanged; this experiment ADDS a cognitive-channel
  layer to F75's theoretical backing but does not change F75's empirical content.
- It does **NOT** establish that the Quran's β = 2.53 is "wrong" or "anomalous"
  in any cognitive-channel sense — it is the rank-1 super-Gaussian extremum
  predicted by F75's V3.21 framework, consistent with the Quran's documented
  73% ن-rāwī rhyme concentration.
- It does **NOT** address CRITICAL-1 (extending the pool to N≥50), CRITICAL-3
  (external replication), or any of the HIGH/MEDIUM tasks. Those remain blocked
  on data acquisition or external action.
- It does **NOT** use compression, NCD, gzip, or any data-tuned threshold.
  Pure analytic + numerical optimization.

---

## 8. Provenance and reproducibility

- This PREREG.md is hash-locked. The SHA-256 hash of THIS FILE'S BYTES is
  computed at run start and matched against `_PREREG_EXPECTED_HASH` in run.py
  (drift aborts).
- The exp156 receipt is hash-pinned via A1.
- No external network calls; all computation runs offline in scipy + numpy
  (versions are recorded in receipt).
- Wall-time estimate: < 5 seconds (small grid, closed-form gradients available).

---

## 9. Counts impact (post-run, conditional on verdict)

| Verdict | Tier-C observations | Failed-null pre-regs | Retractions |
|---|---|---|---|
| `PASS_F75_beta_cognitive_strong` | 12 → 13 (add O13) | unchanged 25 | unchanged 63 |
| `PASS_F75_beta_cognitive_partial` | 12 → 13 (add O13 PARTIAL) | unchanged 25 | unchanged 63 |
| `PARTIAL_F75_beta_cognitive_directional` | unchanged 12 | unchanged 25 | unchanged 63 |
| `FAIL_F75_beta_cognitive_indeterminate` | unchanged 12 | 25 → 26 (add FN29) | unchanged 63 |

No locked finding row is added/promoted/demoted by any verdict (this is a
mechanism-explanation experiment for an existing PASS finding, not a new
universal claim).

---

## 10. PREREG-locked file hash

The SHA-256 of THIS FILE'S BYTES (excluding this section after the next ruled
line — i.e., the `_PREREG_LOCKED_BYTES_END` sentinel below) is committed in
`run.py` as `_PREREG_EXPECTED_HASH` and verified at run start.

_PREREG_LOCKED_BYTES_END
