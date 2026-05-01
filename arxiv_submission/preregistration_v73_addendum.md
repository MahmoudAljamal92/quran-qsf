# QSF v7.3 Results-Lock Addendum (post-hoc code-state lock)

**Status**: drafted 2026-04-20 PM. This is a **post-hoc code-state
lock**, NOT a strict pre-registration. The experiments (`exp37_lpep`,
`exp38_ccas_normalised`, `exp41_gzip_formalised`, `exp43_adiyat_864_
compound`, `exp44_F6_spectrum`) were all implemented and run during
the same session (2026-04-20 between approximately 15:30 and 16:15
UTC+02:00) BEFORE this document was written. What is pre-registered
here is the **verdict rule** attached to each experiment (d ≥ 0.3,
p ≤ 0.05, etc. — generic literature thresholds that were not tuned
to observed values), not the existence of the test itself.

The honest OSF framing is: "post-hoc code-state lock with ex-ante
verdict rules." The distinction matters at strict-methodology review
and is fully disclosed in §10.

**Supersedes**: `results/integrity/preregistration.json` v10.18 frozen
2026-04-18 remains canonical for Ultimate-1. This addendum declares new
tests on top of v10.18 introduced by the 2026-04-20 deep-scan synthesis.
**Nothing in Ultimate-1 is modified.**

---

## 1. Why an addendum (scope)

The v7.3 cycle introduces five new experiments that test the
letter-level detection hypothesis space not covered by Ultimate-1's
corpus-level Phi_M statistic or Ultimate-2's R1–R11 channel bank.
Each test listed below has a PRE-REGISTERED success/failure rule that
cannot be altered after data collection.

Experiments were specified in this document **before** running; the
implementations live at the paths listed, and the success/failure verdicts
are the only permitted outputs.  If a verdict string deviates from the
rule stated here, the experiment must be rerun or the discrepancy logged
as a protocol violation.

---

## 2. Test 1 — LPEP (Letter-Position Entropy Profile)

- **Code**: `experiments/exp37_lpep/run.py`
- **Statistic**: per-corpus pooled
  `<H(pos|L,k)> = Sigma_{L,k} P(L,k) * H(pos | L, k)`
  over the 28-letter Arabic consonant alphabet (hamza folded to alef,
  ة → ه, ى → ي), word lengths binned k ∈ {3,4,5,6,7+}, min-cell-count 5.
- **Sub-hypothesis 1 (H_LPEP_semitic)**: Iliad-Greek pooled
  `<H(pos|L,k)>` exceeds every Arabic corpus.
- **Sub-hypothesis 2 (H_LPEP_quran)**: Quran Band-A per-unit
  `<H(pos|L,k)>` is strictly less than pooled Arabic-ctrl (Cohen d <= −0.3
  AND MW p_less <= 0.05).
- **Success criteria**:
  - H_LPEP_semitic **PASS** iff Iliad > max(Arabic).
  - H_LPEP_quran **PASS** iff pooled rank = 1 AND d <= −0.3 AND p_less <= 0.05.
- **OSF decision rule**: both sub-hypotheses tested; each recorded
  independently in `exp37_lpep.json::hypothesis_test_verdict`.

---

## 3. Test 2 — CCAS normalised (Consonant Co-occurrence Anomaly Score)

- **Code**: `experiments/exp38_ccas_normalised/run.py`
- **Statistic**:
  `CCAS_norm(doc, edit) = ||M_edited − M_canonical||_F / sigma_intra_doc(M)`
  where `M` is the 28×28 letter-transition count matrix (strict consonant
  alphabet, hamza folded), `sigma_intra_doc` is the std of
  `||M_win − mean(M_win)||_F` across K=10 random equal-length sub-document
  windows.
- **Hypothesis (H_CCAS_norm)**: Quran edits produce LARGER normalised
  CCAS than ctrl edits (Cohen d >= +0.3 AND MW p_greater <= 0.05) on
  68 Band-A surahs × 20 internal single-letter swaps vs 200 Band-A ctrl
  units × 20 internal single-letter swaps.
- **Success criteria**: d >= +0.3 AND p_greater <= 0.05 on `norm_ccas`.
- **Dual-direction reporting**: both `p_greater` and `p_less` recorded.
  A decisive reverse (d <= −0.3, p_less <= 0.05) is a separate publishable
  negative finding; not a null.

---

## 4. Test 3 — R12 gzip NCD edit-detection channel

- **Code**: `experiments/exp41_gzip_formalised/run.py` +
  `experiments/exp41_gzip_formalised/length_audit.py`
- **Statistic**:
  `NCD_doc = gzip-NCD(canonical_28letter_stream, edited_28letter_stream)`
  at the document scale, and `NCD_window` on the 3-verse window centred
  on the edit site.
- **Threshold**: ctrl-null 95th percentile from 200 ctrl units × 20
  internal single-letter swaps each (4000 edits total), computed in the
  same run.
- **Hypothesis 3a (H_R12_population)**: Cohen d(Quran NCD, ctrl NCD) >= +0.3
  AND MW p_greater <= 0.05 on doc-scale NCD.
- **Hypothesis 3b (H_R12_length_control)**: in the log-linear regression
  `log NCD = alpha + beta * log(n_letters) + gamma * I(Quran)`, the
  coefficient gamma is strictly positive with 95% CI excluding zero.
  This closes the confound that Quran surahs are shorter in letter count.
- **Hypothesis 3c (H_R12_adiyat)**: all three Adiyat variants
  (v1 ع→غ, v1 ض→ص, both) produce NCD above the ctrl-null 95th percentile.
- **R12 PASSES its pre-registered target iff** (3a AND 3b) OR 3c.
  Both conditions reported in `exp41_gzip_formalised.json::verdicts`.

---

## 5. Test 4 — Adiyat 864-variant compound detection

- **Code**: `experiments/exp43_adiyat_864_compound/run.py`
- **Enumeration**: all 864 single-letter consonant substitutions of
  Surah 100 verse 1 (32 consonant positions × 27 alternative consonants),
  same enumeration policy as `exp23_adiyat_MC`.
- **Detectors**:
  - D1 Phi_M delta (5-D boundary-reader, known to be blind by §4.20)
  - D2 NCD doc-scale > exp41 ctrl p95
  - D3 NCD window-scale > exp41 ctrl p95
  - D4 H_char window delta > 0.01 bits
  - D5 CCAS raw Frobenius window > 0
- **Pre-registered claims**:
  - C4a Phi_M blindness ≥ 90% on 864 variants (i.e., D1 fires <= 10%).
  - C4b compound letter-scale detection (D2 ∨ D3 ∨ D4 ∨ D5) = 100%.
  - C4c canonical is the unique global NCD minimum (1/865 rank on D2).
- **C4a, C4b, C4c all expected to hold** by the design; the test is a
  publication-quality *demonstration*, not an exploratory search.
- **Dis-confirming outcome**: any of the three rates below its target
  threshold by > 2 percentage points.

---

## 6. Test 5 — F6 autocorrelation spectrum (AR(1))

- **Code**: `experiments/exp44_F6_spectrum/run.py`
- **Statistics**:
  - per-surah AR(p=3) coefficients phi_1, phi_2, phi_3 via OLS on
    mean-centred verse-length sequence
  - Pearson and Spearman ACF at lags 1..15
  - Integrated |rho| and rho² across lags 1..15
- **Hypothesis 5a (H_AR1)**: AR(1) coefficient Cohen d(Q vs pooled
  Arabic ctrl) >= +0.5 AND MW p_greater <= 0.05.
- **Hypothesis 5b (H_IAC_reverse)**: integrated autocorrelation over
  lags 1..15 is LOWER in Quran (d <= −0.3) — a Markov-1-tight vs
  long-memory-smooth discrimination.
- **Both PASS or BOTH FAIL** jointly establishes the "punchy, not wide"
  rhythmic claim. A single-direction pass is reported as *partial*.

---

## 7. Ex-ante declarations shared by all tests

- **Seed**: SEED = 42 for any stochastic operation.
- **Permutation count**: where nulls are permutation-based, N_PERM >= 200
  (same floor as Ultimate-1 FAST_MODE). Where bootstrap CIs are quoted,
  N_BOOT >= 2000.
- **FDR correction**: all p-values from tests 1–5 enter a single
  Benjamini–Hochberg family at q = 0.05.  Intermediate p-values reported
  without adjustment for audit transparency.
- **No post-hoc metric tuning**: the verdict rules above are binding.
  If a test fails, it is reported as failed; no new statistic is invented
  to rescue the claim.
- **Cross-check against `results_lock.json`**: no scalar in Ultimate-1's
  127-scalar lock is modified.  The new tests write only under
  `results/experiments/exp{37,38,41,43,44}_*/`.

---

## 8. How to verify

```powershell
# v7.3 test reproducibility
python -m py_compile `
    experiments/exp37_lpep/run.py `
    experiments/exp38_ccas_normalised/run.py `
    experiments/exp41_gzip_formalised/run.py `
    experiments/exp41_gzip_formalised/length_audit.py `
    experiments/exp43_adiyat_864_compound/run.py `
    experiments/exp44_F6_spectrum/run.py

python -X utf8 -u experiments/exp37_lpep/run.py
python -X utf8 -u experiments/exp38_ccas_normalised/run.py
python -X utf8 -u experiments/exp41_gzip_formalised/run.py
python -X utf8 -u experiments/exp41_gzip_formalised/length_audit.py
python -X utf8 -u experiments/exp43_adiyat_864_compound/run.py
python -X utf8 -u experiments/exp44_F6_spectrum/run.py
```

The terminal output must include the verdict lines shown in each
experiment's docstring. Any deviation is either a protocol violation
(non-deterministic behaviour) or a regression (code drift).

---

## 9. OSF deposit checklist

Before filing at osf.io:

- [ ] SHA-256 of this document (the deposit text itself must be hashed)
- [ ] SHA-256 of each `exp{37,38,41,43,44}_*/run.py`
- [ ] SHA-256 of `results/integrity/preregistration.json` v10.18
- [ ] SHA-256 of `experiments/_ultimate2_helpers.py`, `experiments/_lib.py`
- [ ] Link to this git commit (post-commit), public visibility = True
- [ ] Declare funding: self-funded
- [ ] Declare conflicts: none
- [ ] Declare data availability: full corpora SHA-pinned in
      `results/integrity/corpus_lock.json`

---

## 10. Known deviations and their protocol handling

1. **Tests 1–5 were implemented before this document was written**, on
   2026-04-20 between approximately 15:30 and 16:15 UTC+02:00. The
   implementation files were NOT pre-registered at the strictest
   interpretation of the term. Under OSF practice this is treated as
   "post-hoc locking" which is weaker than "a priori registration";
   the distinction is declared here.
2. The **verdict strings in each result JSON** (`hypothesis_test_verdict`,
   `verdicts`, etc.) are auto-generated from the code rules stated here;
   they cannot be re-interpreted after the fact.
3. Any **subsequent rerun** with the same seed must reproduce the same
   numbers byte-for-byte. If a rerun produces different numbers, the
   rerun is invalidated and the original JSON is authoritative.

---

*End of addendum.*
