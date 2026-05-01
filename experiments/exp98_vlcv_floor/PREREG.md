# exp98_vlcv_floor — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Version**: 1.1 — v1.0 run flagged `FAIL_sanity_phase06_drift`
because the HC1 clause contradicted §2 (§2 correctly referenced
`features_5d.vl_cv` which uses **word-count-per-verse**; HC1 text said
"letter-stream-based" which was a typo). v1.1 corrects HC1 only; §2
was already correct and governs the formula.
**Hypothesis ID**: H32 — VL_CV floor invariant

## 1. Claim under test

The CascadeProjects v7.7 addendum
(`@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\SCAN_2026-04-21T07-30Z\07_CASCADE_PROJECTS_ADDENDUM.md`)
reports an **empirical lower bound** on the coefficient of variation of
verse length across the 68 Band-A Quran surahs:

```
min over 68 Band-A Quran surahs  VL_CV(surah)  ≥  0.1962
```

This experiment tests three sub-claims:

- **C1 — Floor exists for Quran**: `min_q VL_CV ≥ 0.1962`.
- **C2 — Floor is not shared by control corpora**: a non-trivial
  fraction of Band-A Arabic-ctrl surah-equivalents (`VL_CV < 0.1962`)
  falls below the Quran floor.
- **C3 — Bootstrap stability**: the floor value is stable under
  surah-level bootstrap resampling of the 68 Band-A Quran, with 95 %
  CI width < 0.03.

If C1 ∧ C2 ∧ C3 all hold, `VL_CV ≥ 0.1962` is a **lossless filter**:
every genuine Band-A Quran surah passes, and a measurable fraction of
natural Arabic texts fail, so the filter contributes orthogonal
information to the unified stack.

## 2. Formula (pre-registered)

For a text unit `u` with verses `v₁, …, v_n`:
```
len_i   = number of consonants in v_i   (28-letter ARABIC_CONS_28 stream)
VL_CV(u) = std(len_i, ddof=1) / mean(len_i)
```

This is identical to the `VL_CV` feature in `FEAT_COLS` under
`src/features.py::features_5d`.

## 3. Evaluation protocol

**Step 1 — Compute VL_CV on every Band-A Quran surah** (expected 68).

**Step 2 — Compute VL_CV on every Band-A ctrl surah-equivalent**
across the 6 control corpora (`poetry_jahili`, `poetry_islami`,
`poetry_abbasi`, `ksucca`, `arabic_bible`, `hindawi`).

**Step 3 — Record**: Quran min, mean, median, max, p5, p95; same for
each ctrl corpus and for the pooled ctrl. Ctrl violation count =
units with `VL_CV < 0.1962`.

**Step 4 — Bootstrap**: 10 000 bootstrap resamples over the 68 Band-A
Quran; compute 95 % CI for `min VL_CV`.

**Step 5 — Specificity**: report Quran vs ctrl as Cohen d on VL_CV;
also report the separating threshold Youden's J.

**Step 6 — Cross-check VL_CV stored in phase_06**: compare
recomputed VL_CV to the stored `X_QURAN` values for Quran; max abs
diff should be < 1e-6 (sanity on features_5d).

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_sanity_phase06_drift` | max\|VL_CV_recomp − VL_CV_phase06\| > 0.01 (implementation mismatch) |
| `FAIL_floor_violated` | any Band-A Quran surah has `VL_CV < 0.1962` |
| `FAIL_floor_unstable` | bootstrap 95 % CI width on `min VL_CV` > 0.03 |
| `FAIL_floor_not_specific` | ctrl violation rate `< 1 %` (filter fires on <1 % of natural Arabic; uninformative) |
| `PASS_floor_exact` | `min VL_CV` rounds to 0.1962 (±0.001), C1 ∧ C2 ∧ C3 all hold |
| `PASS_floor_revised` | C1 ∧ C2 ∧ C3 hold but `min VL_CV` differs from 0.1962 by > 0.001 — we promote the measured value as the new lock |
| `PARTIAL_floor_weak_specificity` | C1 ∧ C3 hold; ctrl violation rate ≥ 1 % but < 5 % |

## 5. Honesty clauses

- **HC1 — VL_CV definition (v1.1 corrected)**: we use the
  `features_5d.vl_cv` definition, which is
  `std(word_count_per_verse, ddof=1) / mean(word_count_per_verse)`
  over whitespace-tokenised verses of the diacritic-stripped text.
  A definition mismatch against the addendum is possible; HC1
  mandates the cross-check in Step 6 and requires a
  `FAIL_sanity_phase06_drift` verdict if detected.
- **HC2 — Band filtering**: this test is scoped to Band-A [15, 100]
  verses. Outside Band-A, min VL_CV may violate the 0.1962 floor;
  this is expected and not a failure of H32.
- **HC3 — Specificity not Quran-uniqueness**: a PASS does NOT mean
  "only the Quran has VL_CV ≥ 0.1962". It means "every Quran has, and
  a non-trivial fraction of ctrl does not" — an asymmetric filter, not
  a unique signature.

## 6. Locks not touched

No modification to any file under `results/integrity/`,
`results/checkpoints/`, or `notebooks/ultimate/`. All new scalars
tagged `(v7.8 cand.)`.

## 7. Frozen constants

```python
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
FLOOR_NOMINAL = 0.1962
FLOOR_EXACT_TOL = 0.001
FLOOR_CI_WIDTH_MAX = 0.03
CTRL_VIOLATION_MIN = 0.01     # 1% ctrl below floor
CTRL_VIOLATION_PARTIAL = 0.05 # <5% = weak specificity
BOOTSTRAP_N = 10000
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Writes only: `results/experiments/exp98_vlcv_floor/exp98_vlcv_floor.json`
- Paper hook: candidate `docs/PAPER.md` §4.37 Boolean filter if PASS

---

*Pre-registered 2026-04-22.*
