# exp95b_local_ncd_adiyat — Pre-registration

**Frozen**: 2026-04-26 (before any run).
**Hypothesis ID**: H34 — Window-local NCD lifts the Adiyat-864 ceiling above 0.999 without violating FPR.
**Origin**: External-AI reviewer feedback 2026-04-26 ("Step 1: phonetic-modulated R12, expected to close 99.07 % → 99.9 %"). The literal phonetic-modulated formulation was already executed as `exp95_phonetic_modulation` (verdict `FAIL_ctrl_stratum_overfpr`, recall 0.985 < flat baseline 0.991). This experiment tests an alternative root cause: **full-document NCD dilutes a 1-letter edit across 11 verses' worth of bytes**, and a 3-verse window centred on the edit position should amplify the signal ~3.5×.
**Parent experiments**:
- `exp41_gzip_formalised` — already implements `_window_ncd` primitive (3-verse window, `WINDOW_L0=3`)
- `exp94_adiyat_864` — R12-only flat baseline = 0.990741 (856/864), 8 misses
- `exp95_phonetic_modulation` — bucketed-tau approach FAILED; misses are NOT phonetic-distance-correlated

## 1. Claim under test

For each Adiyat-864 variant, replace the document-level NCD

```
NCD_doc(canon, variant) = NCD( letters_28(" ".join(canon_verses)),
                                letters_28(" ".join(variant_verses)) )
```

with a **window-local NCD centred on the perturbed verse**:

```
NCD_window(canon, variant, vi) = NCD( letters_28(" ".join(canon[lo:hi])),
                                       letters_28(" ".join(variant[lo:hi])) )

with [lo, hi] = 3-verse window centred on vi:
   lo = max(0, vi - 1)
   hi = min(len(verses), lo + WINDOW_L0)
   lo = max(0, hi - WINDOW_L0)         # right-clip if vi is near end
```

For Adiyat-864 every perturbation hits `v1` (verse index 0), so the window is `verses[0:3]` = `{v1, v2, v3}`. For ctrl null perturbations the window is centred on whichever interior verse the random perturbation hit (byte-equal to the `vi` returned by `_apply_perturbation` in `exp41/94/95`).

**Three sub-claims**:

- **C1 — Window-local NCD lifts recall above 0.999**: Adiyat-864 recall under window-local NCD ≥ 0.999 (at most 1 miss).
- **C2 — Ctrl FPR is controlled at 5 %**: ctrl-pool window-local NCD at the same threshold has empirical FPR ≤ 0.05 + 1e-6.
- **C3 — Lift over flat baseline is positive**: recall_window − 0.990741 > 0. (If equal-or-lower than the flat baseline, the window approach did not help.)

## 2. Formula (pre-registered, no parameter scan)

For canonical surah `x` with verses `[x_0, x_1, ..., x_{n-1}]` and a single-letter-edited variant `x'` differing from `x` only at verse `vi`:

```
WINDOW_L0          = 3   (frozen; no parameter scan)

[lo, hi]           = 3-verse window:
                       lo₀ = max(0, vi - 1)
                       hi  = min(n, lo₀ + 3)
                       lo  = max(0, hi - 3)            # right-clip

NCD_window(x, x', vi) = NCD( letters_28(" ".join(x[lo:hi])),
                              letters_28(" ".join(x'[lo:hi])) )

τ_window           = empirical 95th percentile of NCD_window over the
                     4 000-edit ctrl-pool null (200 ctrl units × 20
                     internal perturbations, byte-equal to exp94 setup,
                     but using window-local NCD instead of doc-level).

DETECT_window(x, x', vi) = (NCD_window(x, x', vi) ≥ τ_window)
```

## 3. Evaluation protocol

**Step 1 — Null calibration**: byte-equal to `exp94` Step 1, except the recorded NCD is `NCD_window` (the perturbation function `_apply_perturbation` already returns `vi`, so the window is fully determined per ctrl edit).

**Step 2 — Adiyat-864 scoring**: enumerate the 864 single-letter substitutions of Surah 100 v1 (byte-equal to `exp43/94/95`). For each variant, vi=0; window = `verses[0:3]`. Compute `NCD_window(canon, variant, 0)`. Fire flag = `NCD_window ≥ τ_window`.

**Step 3 — Compute lift**: `lift = recall_window − exp94.R12_only_baseline = recall_window − 0.990741`.

**Step 4 — Per-position audit**: for each position `pos ∈ [0, len(v1))`, report n_variants_at_that_pos, n_fired, recall_at_that_pos. (864 variants spread over ~25 positions in v1; the 8 missed variants at flat-doc-NCD should clump at specific pos values.)

**Step 5 — Honesty diagnostic**: also compute `NCD_doc` (flat) on the same setup as a sanity check; recall_flat must reproduce `0.990741 ± 0.001`. If not, the protocol has drifted from `exp94`.

**Step 6 — Self-check**: protected files unchanged at start vs end (via `_lib.self_check_begin/end`).

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_exp94_baseline_missing` | `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` not on disk |
| `FAIL_protocol_drift` | recall_flat (this experiment's reproduction of exp94) deviates from 0.990741 by more than 0.001 |
| `FAIL_window_overfpr` | ctrl-pool empirical FPR at `τ_window` > 0.05 + 1e-6 |
| `FAIL_window_no_lift` | `recall_window ≤ exp94.R12_only_baseline` (window approach did not improve over flat) |
| `PARTIAL_window_lifts_below_999` | recall_window > exp94 baseline AND recall_window < 0.999 |
| `PASS_window_999` | recall_window ≥ 0.999 AND FPR ≤ 0.05 |
| `PASS_window_100` | recall_window == 1.0 AND FPR ≤ 0.05 |

## 5. Honesty clauses

- **HC1 — Window size is frozen at 3 verses**. No scan over `WINDOW_L0`. The 3-verse choice is byte-equal to the existing `exp41._window_ncd` primitive; using a different window size requires a new experiment number.
- **HC2 — Single threshold, no stratification**. The previous `exp95_phonetic_modulation` failed because per-stratum thresholds had discreteness artifacts that pushed FPR above 0.05. This experiment uses one global ctrl-p95 threshold over all 4 000 window-local NCDs, so FPR is exactly 0.05 ± discreteness at n=4000, which is much tighter than per-stratum at n≈150-1500.
- **HC3 — Adiyat-864 is a single-surah benchmark**. A PASS does NOT generalise to other surahs without a corpus-scale replication. The claim is Q:100-specific.
- **HC4 — Edge case: vi near end**. For ctrl perturbations near the last verse, the window is right-clipped (lo = max(0, hi − 3)). For Adiyat the perturbation always hits v1 (vi=0), so the window is `verses[0:3]` exactly. No edge case for the headline result.
- **HC5 — Honest negative is acceptable**. If `recall_window` does NOT exceed 0.991 the verdict is `FAIL_window_no_lift` and we publish the negative result. The reviewer's hypothesis was a guess; the empirical answer wins.
- **HC6 — `vi` tracking is byte-equal to exp94 `_apply_perturbation` return value**. No re-implementation; the existing function is imported directly via `from experiments.exp94_adiyat_864.run import _apply_perturbation` is NOT done (to avoid circular sandbox concerns); instead the function body is inlined byte-equal and audit-checked against the source.

## 6. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. All new scalars tagged `(v7.10 cand.)`. The `exp94`, `exp95`, and `exp41` receipts are read-only.

## 7. Frozen constants

```python
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
WINDOW_L0 = 3   # 3-verse window centred on perturbed verse
PROTOCOL_DRIFT_TOL = 0.001  # how close exp94 baseline reproduction must be
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Reads (receipt): `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`
- Reads (receipt): `results/experiments/exp95_phonetic_modulation/exp95_phonetic_modulation.json` (cross-reference for negative-result sister experiment)
- Writes only: `results/experiments/exp95b_local_ncd_adiyat/exp95b_local_ncd_adiyat.json`
- Paper hook: candidate `docs/PAPER.md` §4.25 (Adiyat 864) footnote on the window-local NCD lift.

---

*Pre-registered 2026-04-26 night. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`. Authored in response to external-AI reviewer feedback documented in `docs/REVIEWER_FEEDBACK_2026-04-26.md`.*
