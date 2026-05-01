# exp95_phonetic_modulation — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H33 — Phonetic-distance modulation closes the Adiyat-864 ceiling.
**Parent experiments**:
- `exp41_gzip_formalised` (R12 NCD threshold, `doc_ctrl_p95 ≈ 0.0495`)
- `exp54_phonetic_law_full` (M1_hamming detection law, r = 0.929, slope = +0.007265, intercept = −0.002388)
- `exp94_adiyat_864` (current R12-only recall = 0.990741 = 856/864, 8 misses on the closest phonetic pairs)
- `exp98_vlcv_floor` (structural-floor Boolean gate, Q min VL_CV = 0.2683, nominal ≥ 0.1962)

## 1. Claim under test

`exp94_adiyat_864` PASSES the pre-registered 99 % recall gate at the exp41 ctrl-p95 threshold, but leaves 8 of 864 variants undetected. `exp54_phonetic_law_full` established that single-letter-edit detection rate under the 9-channel forensics ladder is a linear function of the phonetic Hamming distance `d_hamming ∈ {0, 1, 2, 3}` between the original and substituted consonant:

```
detection_rate(d) = 0.007265 · d − 0.002388     (r = 0.929, n = 7 classes × 10 461 edits)
```

This experiment tests whether a **phonetic-distance-modulated** threshold

```
τ(d) = τ₀ − κ · d        with τ₀ = exp41 ctrl-p95 = 0.0495
                          and κ to be fitted from the per-`d` ctrl-null distribution
```

applied to the same Adiyat-864 enumeration closes the remaining 8 misses without lifting ctrl false-positive rate above 5 % at any `d`.

**Three sub-claims**:

- **C1 — Modulation recovers misses**: adding `τ(d_hamming(orig, repl))` to the R12 detector recalls all 864 variants (`recall ≥ 0.999` i.e. at most 1 miss).
- **C2 — Per-`d` FPR is controlled**: for every `d ∈ {1, 2, 3}` the ctrl-null FPR at the modulated threshold remains `≤ 0.05`. If any stratum exceeds 0.05, the modulation has bought specificity at the cost of calibration — this is a FAIL.
- **C3 — Conjunction with VL_CV floor adds no cost**: adding the Boolean `VL_CV(canonical_surah) ≥ 0.1962` gate from `exp98` to the modulated R12 does not change Q recall on Adiyat-864 (Q:100 VL_CV is well above 0.1962 — this is a sanity-only conjunction).

## 2. Formula (pre-registered)

For a canonical surah `x` and a single-letter-edited variant `x'`:

```
d_hamming(orig, repl) = Hamming distance on the 5-D discretised
                         articulatory feature vector from
                         src.exp54 PHONETIC_FEATURES
                         (place-bin, manner-round, voice, emphatic, sibilant).

NCD_edit(x, x')       = gzip NCD on the 28-letter consonantal rasm
                         (byte-equal to exp41/exp94).

τ(d)                  = empirical 95th percentile of NCD_edit on the
                         ctrl-pool perturbation subsample restricted
                         to phonetic distance d. Built exactly as in
                         exp94 null calibration, but bucketed by d.

DETECT_R12_modulated(x, x') =
        (NCD_edit(x, x') ≥ τ(d_hamming(orig, repl))) AND
        (VL_CV(x) ≥ 0.1962)
```

where `VL_CV(x)` is computed byte-equal to `src.features.vl_cv` (same as `exp98`).

## 3. Evaluation protocol

**Step 1 — Null calibration (per-`d` strata)**: replicate the `exp94` null — 200 ctrl surah-equivalents × 20 internal perturbations = 4 000 ctrl edits. Bucket each edit by its `d_hamming` (orig → repl). Expected stratum sizes under uniform random substitution:
- `d = 0`: phonetically identical pair — very rare (< 1 %), treat as the noise floor; if `n_d=0 < 30`, pool with `d = 1`.
- `d = 1, 2, 3`: the bulk of edits.
- `d = 4, 5`: some edits cross 4–5 features (e.g. `ب → ي`); these are the easiest to detect.

For each stratum compute the 95th percentile of `NCD_edit`. That is `τ(d)`.

**Step 2 — Adiyat-864 scoring**: enumerate the 864 single-letter substitutions of Surah 100 v1 (byte-equal to `exp43` / `exp94`). For each variant compute:
1. `d_hamming(orig, repl)` from the PHONETIC_FEATURES table.
2. `NCD_edit(canon, variant)`.
3. Fire flag = `NCD_edit ≥ τ(d_hamming)`.

**Step 3 — VL_CV conjunction**: Q:100 VL_CV is fixed (one number per canonical surah). Compute it once; verify `≥ 0.1962`; report the conjunction fire-rate.

**Step 4 — Compare to R12-only baseline**: report Δrecall vs the frozen `exp94.R12_only_baseline = 0.990741`.

**Step 5 — Stratum audit**: for each `d ∈ {1, 2, 3, 4, 5}` report {n_variants, n_fired, recall_in_stratum, n_ctrl_fired, ctrl_FPR_in_stratum}. The 8 misses from `exp94` should clump in the low-`d` strata.

**Step 6 — Self-check**: the `exp54` slope and intercept are loaded from the receipt; log their values and the `prereg_hash` of `exp54` for traceability.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_exp54_missing` | `results/experiments/exp54_phonetic_law_full/exp54_phonetic_law_full.json` not on disk or `overall_verdict != LAW_CONFIRMED` |
| `FAIL_exp94_baseline_missing` | `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` not on disk |
| `FAIL_ctrl_stratum_overfpr` | any stratum `d ∈ {1, 2, 3, 4, 5}` has ctrl FPR > 0.05 at `τ(d)` |
| `FAIL_vlcv_sanity` | Q:100 VL_CV < 0.1962 (would indicate a bug in `src.features.vl_cv` on the exp95 call path) |
| `PARTIAL_modulation_lifts_below_999` | recall improves over R12-only but < 0.999 |
| `PASS_modulation_99.9` | recall ≥ 0.999 AND no stratum FPR > 0.05 |
| `PASS_modulation_100` | recall == 1.0 AND no stratum FPR > 0.05 |

## 5. Honesty clauses

- **HC1 — Phonetic distance uses the `exp54` table verbatim**. No re-calibration of the PHONETIC_FEATURES vector. Any re-calibration is a post-hoc move and breaks the pre-registration.
- **HC2 — Adiyat-864 is a single-surah benchmark**. A PASS does NOT generalise to other surahs without a full replication at corpus scale. The claim is Q:100-specific.
- **HC3 — Ctrl-null bucketing relies on 4 000 edits across 200 surahs**. Expected stratum-level `n` per `d ∈ {1, 2, 3}` ≈ 1 000 each; `d = 4, 5` are rarer. If any live stratum has `n < 30`, we report a widened-CI verdict tag `_sparse_stratum_d{n}` and do not claim PASS for that stratum's FPR.
- **HC4 — VL_CV gate is sanity-only at Adiyat-864**. Q:100 VL_CV is known to be > 0.4. The gate is re-evaluated for its true purpose (screening ctrl-surahs) in `exp98`; this is just a consistency check.
- **HC5 — `κ` is NOT a new free parameter**. `τ(d)` is defined strictly as the empirical ctrl-null p95 at stratum `d`; no two-parameter `(τ₀, κ)` fit is done. The `κ` notation in the top of §1 is descriptive; the actual thresholds are non-parametric per-stratum quantiles.

## 6. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. All new scalars tagged `(v7.8 cand.)`. The `exp94` receipt is read-only.

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
VLCV_FLOOR = 0.1962
SPARSE_STRATUM_MIN_N = 30

# exp54 M1_hamming slope/intercept (descriptive; thresholds are non-parametric)
EXP54_SLOPE = 0.007265
EXP54_INTERCEPT = -0.002388
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Reads (receipt): `results/experiments/exp54_phonetic_law_full/exp54_phonetic_law_full.json`
- Reads (receipt): `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`
- Reads (receipt): `results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json`
- Writes only: `results/experiments/exp95_phonetic_modulation/exp95_phonetic_modulation.json`
- Paper hook: candidate `docs/PAPER.md` §4.25 footnote (phonetic modulation) + §4.37 letter-scale term

---

*Pre-registered 2026-04-22 late. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`.*
