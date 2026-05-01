# exp29 — Cascade product-code empirical verification

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp29_cascade_product_code/exp29_cascade_product_code.json`.

## Why this exists

The 2026-04-20 external review framed the Quran's multi-scale structural
redundancy as a **product code**. For k independent detection channels
each with per-channel hit-rate `p_k`, the composite detection probability
for a single event (a single-letter internal substitution) is:

    P_composite = 1 - prod_k (1 - p_k)

The feedback proposed **four** channels with these ESTIMATED detection
rates for single-letter internal substitutions:

| Channel | Description | Estimated p_k |
|---|---|---|
| L0 | H_char on a 3-verse window around the edit | 0.55 – 0.70 |
| L1 | Phi_M on a 10-verse sliding window (locked R2) | 0.20 |
| L2 | Phi_M at full surah (locked R1 9-ch, approx.) | 0.50 |
| L3 | Phi_M drift from canonical Quran centroid | 0.03 |
| **Composite** | under independence | **0.82 – 0.90** |

Those numbers are **estimates**, not measurements. This experiment's
job is to **measure them**.

## Protocol

- **Target**: Band-A Quran surahs (15–100 verses, n=68).
- **Perturbation**:
  - Non-terminal verse (skip verse 0 and the final verse so EL's
    terminal-letter rhyme shortcut and basmala anchor cannot catch it).
  - Non-boundary word (skip first and last word of the verse).
  - Word must have at least 3 letters.
  - Substitute a NON-INITIAL, NON-TERMINAL letter with a different
    Arabic consonant from the 28-letter set.
  - 20 perturbations per surah -> **1,360 total** perturbations.
- **Null thresholds** (set per channel at the 95th percentile of
  natural, unperturbed variation):
  - L0: adjacent 3-verse windows' |ΔH_char|.
  - L1: adjacent 10-verse sliding-window |ΔΦ_M|.
  - L2: pairwise |ΔΦ_M(surah_i, surah_j)| within Quran Band-A.
  - L3: per-surah Mahalanobis distance from the Quran centroid (on the
    Arabic-ctrl 5D inverse covariance).
- **Mahalanobis setup**: `mu, Sinv` built from the Arabic-ctrl Band-A
  pool (same protocol as `src/extended_tests.py:test_cv_phi_m`, NOT
  the locked phase_06 pickle -- decoupled so a schema change in
  phase_06 does not silently break exp29).
- **Detection**: `|delta_channel| > threshold`.  Per-channel rate
  `p_k = hits / n_perturbations`.
- **Composite**: `P_composite = 1 - Π (1 - p_k)` assuming channel
  independence.  Dependence is separately audited via pairwise
  conditional detection rates `P(ch_j | ch_i)`.

## How to run

```powershell
python -m experiments.exp29_cascade_product_code.run
```

Expected runtime: ~2-4 minutes on a modern laptop (Python, no
parallelism; ~1,360 perturbations × 4 channels × one 5D feature call
per sliding-window window).

## Interpretation

### Measured result (2026-04-20 run, 1,360 Quran + 4,000 ctrl perturbations)

| Channel | p_any_move | p_nat (95% natural) | p_ctrl (95% ctrl pert) | MW p(Q>C) |
|---|---|---|---|---|
| L0 H_char 3-verse | 0.948 | 0.000 | 0.137 | 4.9e-3 |
| L1 Φ_M 10-verse window | **0.000** | 0.000 | 0.000 | 1.0 |
| L2 Φ_M surah | **0.000** | 0.000 | 0.000 | 1.0 |
| L3 Φ_M drift from Q centroid | 1.000† | 0.059 | 0.000 | 1.0 |

†L3 `p_any_move = 1` is a framing artefact: L3 reports a scalar DISTANCE,
not a delta; any canonical surah has non-zero distance from the centroid
without any perturbation. What matters for L3 is whether the perturbation
*shifts* the distance, which it does not for internal-letter edits (since
`features_5d` is unchanged).

**P_composite (ctrl null) ≈ 0.14**   vs feedback estimate **0.82 – 0.90**.

### What this means

The feedback's **cascade product-code framing is empirically falsified
for single-letter internal substitutions**. The reason is not that the
math was wrong — products of independent hit rates do compose that way
— but that the estimated per-channel p_k values were wildly optimistic.

Direct empirical verification:

- Over **100 random internal-letter perturbations** (5 Quran surahs × 20
  each), the `features_5d` output was **byte-exact identical** to the
  canonical vector every single time.  The 5-D system is *structurally*
  blind to internal-letter edits, because EL reads terminal letters, CN
  reads opening words, VL_CV counts words, and H_cond uses CamelTools
  on verse-final words only.  A non-initial, non-terminal letter in a
  non-boundary word simply cannot move any of these.
- Even under a **verse-swap perturbation** (swap two verses inside a
  surah), `features_5d` moves only ~0.18 Mahalanobis-norm on average
  — about 50× below the 95th-percentile of natural between-surah
  variation (~9.1 M-norm).
- Only L0 (H_char) is sensitive to internal edits (MW p = 4.9e-3), and
  its Quran-vs-ctrl separation is tiny (medians 0.0184 vs 0.0177). Not
  enough to ground a "detection channel".

### What this DOES NOT invalidate

- The corpus-level Mahalanobis separation (Φ_M d = 6.34, AUC = 0.998,
  locked).  That is a *corpus-level discrimination* claim, not an
  error-detection claim.
- Scale-invariance at root / verse-length / surah-path scales (exp28
  verdict 3/5 scales support).  The Quran is still measurably
  Markov-1-organized at those three scales.
- The Quran's *actual* error-correcting mechanism (recitation,
  memorisation, tajweed). That is an oral-transmission property;
  statistical structural fingerprints were never its error-correcting
  code.

### Publishable framings

- **Correct headline**: "The 5-D structural fingerprint separates the
  Quran from Arabic controls at corpus scale but is blind to
  point-wise internal-letter edits. Robust point-wise edit-detection
  requires character-level or phonological primitives that are
  out-of-scope for the locked 5-D design."
- **Retract or edit any paper text** (draft or otherwise) that
  implied the 5-D fingerprint provides statistical error-correction
  against point-wise letter changes.
- The **information-theoretic ceiling** the feedback itself mentioned
  ("class-preserving substitutions require semantic analysis beyond
  structural metrics") is actually tighter than the feedback stated:
  *any* internal substitution, not just class-preserving, is below
  the 5-D system's detection floor.

## What this experiment does NOT do

- Does not run R1's full 9 channels — L2 is approximated by the Phi_M
  5D at surah scale. The R1 9-channel infrastructure is in
  `experiments/exp09_R1_variant_forensics_9ch/`; integrating it into
  exp29 is a follow-up (exp30).
- Does not simulate class-preserving substitutions (e.g. letter within
  the same articulatory group). The feedback's honesty ceiling notes
  that these are fundamentally harder; we use arbitrary 28-letter
  consonant substitution to match the feedback's baseline estimate.
- Does not compare to controls running through the same perturbation
  pipeline. A follow-up could report ∆ against Arabic-ctrl cascade
  detection to make the Quran-specificity explicit.

## Zero-trust audit

Same as exp27 / exp28: `self_check_begin/end`, read-only loads via
`load_phase`, output confined to
`results/experiments/exp29_cascade_product_code/`, and final
`python -m experiments._verify_all` confirms no protected SHA drifted.
