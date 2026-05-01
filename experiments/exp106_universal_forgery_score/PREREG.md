# exp106_universal_forgery_score — Pre-registration (HANDOFF DOCUMENT)

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H38 — The Universal Forgery Score `UFS = −2·[ln p_EL + ln p_NCD]` is a single scalar that simultaneously performs Task A (is this text the Quran?) and Task B (has any letter been tampered with?) on texts of any length, strictly dominating R12-alone across four pre-registered threat models.
**Status**: PREREG written, run.py NOT IMPLEMENTED. This document is a **complete specification** — a fresh Cascade session should be able to implement `run.py` from this document alone, without re-reading the conversation that produced it.
**Parent experiments** (integrity-checked, on disk):
- `exp94_adiyat_864` (R12 baseline recall = 0.9907 on Adiyat-864; per-variant `NCD_edit` + `(pos, orig, repl)`; ctrl-edit null of 4 000 perturbations already built)
- `exp104_el_all_bands` (EL AUC overall = 0.9813; per-band AUC {0.9337, 0.9971, 1.0000} for bands B/A/C; per-unit EL receipts for all 114 Q + 4 719 ctrl)
- `exp105_harakat_restoration` (**null result**: MSA-morphology R13 did not close the 8 Adiyat-864 R12 misses; `recall_R12 ∪ R13 = recall_R12 = 0.9907` — proves the 8 misses are MSA-wellformed and require Quranic-LM to catch)
- `exp103_cross_compressor_gamma` (proves the d=1 emphatic blind spot is a **Kolmogorov floor** of the 28-letter rasm: CV(γ) = 2.95 across 4 universal compressors — so no compressor-based UFS term alone can close it)

## 1. Motivation — why UFS exists

The claim the paper currently **cannot** make is: *"one number detects all forgeries on any Quran surah"*. It has three specialised numbers instead:
- EL (Task A, corpus classifier, AUC = 0.9813 all-bands, 0.9971 Band-A only — `exp104`).
- R12 gzip NCD (Task B, internal-edit detector, recall = 0.9907 on Adiyat-864 — `exp94`).
- Fisher χ² stack of six features (Task B paper-grade, Band-A only — `§4.36`).

A user who asks *"I hand you any verse from any surah — will your system catch an edit?"* today gets the answer: *"depends on which Task, which Band, which edit position, which channel combination"*. That is a legitimate criticism. UFS is the minimal honest construction that turns that answer into a single scalar with a calibrated threshold at any length.

The **sequential-gating objection** (run EL → then R12) is architecturally clean but has three documented failure modes:
1. **Terminal-letter edits** — EL and R12 are BOTH affected but sequential gating processes them as Task B only.
2. **Multi-letter scattered forgeries** — individual edits sub-threshold for R12 but aggregate EL drift detectable; sequential gating runs EL once up-front, passes, then misses each individual R12 signal.
3. **Unknown-provenance text** — sequential gating requires the operator to pre-decide Task A vs Task B; UFS does both jobs in one score.

UFS addresses (1)–(3) by Fisher-combining the per-window EL and R12 p-values into a single χ²-distributed statistic, where both null distributions are **already on disk** as exp94 + exp104 by-products.

## 2. Formula (pre-registered, complete)

### 2.1 The per-window statistic

For a verse window `W = (v_a, v_{a+1}, …, v_{a+m-1})` of `m ≥ 3` consecutive verses:

```
EL(W)   = (1 / (m-1)) · Σ_{i=a}^{a+m-2}  1{ _terminal_alpha(v_i) == _terminal_alpha(v_{i+1})  AND  _terminal_alpha(v_i) != "" }
          [byte-equal to src.features.el_rate computed on list(W)]

canon(W)= the canonical (unperturbed) version of W from the same corpus.
          For Task A (classifier), canon(W) is undefined; p_NCD is
          computed against a self-consistent baseline instead
          (see §2.3.2). For Task B (edit detection), canon(W) is the
          pre-perturbation window.

NCD(W)  = NCD_gzip( canon(W), W )
          [byte-equal to src.gzip_ncd.ncd — R12 operator, already locked]
```

### 2.2 The two null distributions

Both are already on disk; exp106 rebuilds them from scratch to guarantee freshness and documents their provenance in the receipt.

#### 2.2.1 p_EL Quran-null (left-tail, length-stratified)

For each window size `m ∈ {3, 4, …, 291}` (smallest surah has 3 verses; largest has 290 verses + 1 for basmala → 291 max):

```
QuranNull_EL[m] = empirical distribution of EL(W) over all contiguous
                  m-verse windows W drawn from all 114 Quran surahs,
                  EXCLUDING the surah being scored (leave-one-surah-out
                  to prevent leakage on Task A).
```

For a window `W` of size `m`:
```
p_EL(W) = (1 + #{ e ∈ QuranNull_EL[m] : e ≤ EL(W) })
          / (1 + |QuranNull_EL[m]|)
```
(Laplace-smoothed left-tail CDF; never exactly 0 or 1 → ln is always finite.)

For a window drawn from a ctrl text, `p_EL(W)` is the **same formula** against the same Quran-null: the ctrl's EL will typically be far below the Quran-null median, so `p_EL` is small and the UFS term is large — that is the Task A classifier signal.

#### 2.2.2 p_NCD ctrl-edit-null (right-tail, length-stratified)

For each window size `m ∈ {3, 4, …, 291}`:

```
CtrlEditNull_NCD[m] = empirical distribution of NCD(W, W') where W is
                      a canonical m-verse window from the full Arabic
                      ctrl pool (any corpus in ARABIC_CTRL) and W' is
                      W with a single internal-letter perturbation
                      applied under exp94 / exp95's byte-equal policy
                      (non-initial / non-terminal letter of a non-
                      boundary word of a non-terminal verse).
```

Target size: **4 000 edits per window size** if feasible; otherwise pool all sizes and length-normalise via z-score (see §2.3.4).

For a tested window `W` with canon `canon(W)`:
```
p_NCD(W) = (1 + #{ n ∈ CtrlEditNull_NCD[m] : n ≥ NCD(W) })
           / (1 + |CtrlEditNull_NCD[m]|)
```
(Laplace-smoothed right-tail CDF.)

### 2.3 The Universal Forgery Score

```
UFS(W) = −2 · [ ln p_EL(W)  +  ln p_NCD(W) ]
```

Under independence of the two p-values, `UFS ~ χ²_4` (Fisher's method, two test statistics × 2 d.f. each).

Threshold:
```
τ_UFS = p95 of the ctrl-background UFS distribution at window size m,
        where ctrl-background means: ctrl windows unperturbed.
```

Firing rule:
```
fires_UFS(W) = 1{ UFS(W) ≥ τ_UFS(m) }
```

### 2.3.1 Task A mode (text identity)

Operator asks: is this unknown text W the Quran? Operator does **not** have `canon(W)`. Workaround:
```
p_NCD_taskA(W) = p-value of NCD( self-split halves of W )  against
                 ctrl-self-split null at the same window size.
                 [measures internal redundancy, the signal R12 uses]
```
Alternatively (simpler, honest alternative): **omit p_NCD for Task A** and use `UFS_A = −2 · ln p_EL` alone, which degenerates to the EL-based classifier and is byte-equal to exp104 in this mode. Pre-register the simpler fallback and flag the Task-A-NCD variant as exploratory.

### 2.3.2 Task B mode (edit detection)

Operator has `canon(W)` (the unperturbed verses); both p-values are defined directly per §2.2.1 / §2.2.2. This is the primary mode.

### 2.3.3 Joint mode (unknown-provenance + potentially-edited)

Operator has neither ground truth for identity nor for canonicity. Use Task A mode; any high UFS is flagged as either "not Quran" or "Quran but tampered".

### 2.3.4 If per-m ctrl-null is too small

If building a 4 000-edit ctrl-null at every m is compute-prohibitive, pool across m and z-score NCD relative to the per-m mean / sd:
```
z_NCD(W) = (NCD(W) − μ_NCD(m)) / σ_NCD(m)
```
then use the pooled `z_NCD` distribution as the null. Pre-register: if pooled-z is used, reported UFS is tagged `UFS_pooled_z`; if per-m is used, tagged `UFS_stratified`.

## 3. Evaluation protocol — four benchmarks

All four reported in the same receipt JSON.

### 3.1 Benchmark 1 — Task A on all 114 surahs (tie or beat exp104)

```
for each unit u in { all 114 Quran surahs  ∪  all ~4 719 ctrl units with n_verses ≥ 3 }:
    UFS_A(u) = −2 · ln p_EL(u)     # Task A mode, §2.3.1
fit: ROC of UFS_A as a classifier Quran vs ctrl.
report: AUC_overall, AUC per band (B / A / C), exp89b sanity (Band-A AUC ≥ 0.9971 − 0.005).
baseline: exp104's AUC = 0.9813 overall.
pre-registered pass: UFS_A AUC ≥ exp104.AUC − 0.005 at every band.
```

Expected: exact tie with exp104 (UFS_A = −2·ln p_EL is monotone in EL). Any deviation is a bug.

### 3.2 Benchmark 2 — Task B on Adiyat-864 (tie R12)

```
for each of the 864 Adiyat v1 substitution variants (byte-equal to exp94 enumeration):
    W_canon = full Adiyat (11 verses), canonical form
    W_var   = Adiyat with v1 replaced by variant
    UFS(W_var) = −2·[ln p_EL(W_var) + ln p_NCD(W_var)]   # Task B mode, §2.3.2
report: recall_UFS at τ_UFS calibrated at 5 % ctrl-FPR.
baseline: exp94's R12 recall = 0.9907 (= 856 / 864).
pre-registered tie-or-beat: recall_UFS ≥ recall_R12 − 0.003 (i.e., within 3 variants).
```

Expected: exact tie (~856/864). The 8 R12 misses are MSA-wellformed + non-terminal → both UFS terms silent. Documented tie, not a failure.

### 3.3 Benchmark 3 — Terminal-edit benchmark (NEW, the main UFS win)

This is the threat model sequential gating silently misses.

```
enumerate: for every verse v_i of every surah s of all 114 Quran surahs:
    for every terminal letter position (the last letter of v_i):
        for every repl ∈ ARABIC_CONS_28 \ {original terminal letter}:
            W_canon = full surah s
            W_var   = s with v_i's terminal letter replaced by repl
    [cap at 6 000 variants total to keep compute bounded; stratified uniform sample over all 114 surahs]
```

For each variant, compute UFS(W_var) and compare to τ_UFS calibrated at 5 % ctrl-FPR on the **same** terminal-edit null over ctrl corpora.

Pre-registered baseline: R12 recall on terminal edits is ESTIMATED at ~70–85 % (not measured; exp94 excludes terminals by policy). Pre-registered UFS recall ~99 %+ because p_EL drops to ≈ 0 for any terminal letter change in a rhyming surah.

Verdict: `recall_UFS_terminal ≥ recall_R12_terminal + 0.10` for a `PASS_terminal_lift` tag. The specific numbers are secondary — the categorical claim is that UFS strictly dominates R12 on terminal edits.

### 3.4 Benchmark 4 — Multi-edit benchmark (k = 3 scattered edits)

```
held-out: sample 20 surahs stratified across the 3 length bands (7 Band-B + 7 Band-A + 6 Band-C).
for each held-out surah s:
    for 100 random k=3 multi-edit forgeries:
        pick 3 distinct (verse, position, repl) triples under exp94's internal-edit policy
        apply all 3 to s → W_var
    compute UFS(W_var), fires_UFS under τ_UFS
    also compute R12(W_var), fires_R12 under the same 5 %-FPR threshold
report: recall_UFS vs recall_R12 on 2 000 multi-edits.
baseline: R12 recall on multi-edits is UNMEASURED; exp94 only runs single-edits.
```

Pre-registered expected gap: UFS outperforms R12 because k=3 scattered edits aggregate EL drift across 3 verse pairs while each individual edit may be sub-threshold for R12. Minimum lift for `PASS_multi_edit_lift` tag: `recall_UFS ≥ recall_R12 + 0.05`.

### 3.5 Null-calibration quality check

Before any of the 4 benchmarks are scored, verify the Fisher independence assumption empirically:
```
for each window W in the ctrl-background (unperturbed ctrl windows):
    record (p_EL(W), p_NCD(W))
compute Pearson and Spearman correlations.
```
If `|ρ| ≥ 0.30` the independence assumption is badly violated and χ²_4 is not a valid null. Emit `FAIL_broken_independence`; drop UFS back to a max-of-p rule or a logistic combiner that doesn't assume independence (fit on ctrl-null + a small Quran-canonical-window positive set).

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_broken_independence` | Ctrl-null Pearson (p_EL, p_NCD) correlation ≥ 0.30 → Fisher invalid |
| `FAIL_benchmark1_regression` | Benchmark 1 AUC < exp104.AUC − 0.005 at any band → implementation bug |
| `FAIL_benchmark2_regression` | Benchmark 2 recall < exp94.recall − 0.003 → implementation bug |
| `PARTIAL_redundant` | All 4 benchmarks show UFS ≈ R12 / EL (no ≥ 0.05 lift anywhere) — what the "sequential gating" feedback predicted |
| `PASS_terminal_lift` | Benchmark 3 shows `recall_UFS − recall_R12 ≥ 0.10` on terminal edits |
| `PASS_multi_edit_lift` | Benchmark 4 shows `recall_UFS − recall_R12 ≥ 0.05` on k=3 multi-edits |
| `PASS_strict_superset_of_R12` | UFS recall ≥ R12 recall on **all four** benchmarks (tie allowed on 1 and 2, strict lift on 3 and 4) |
| `PASS_universal_forgery_machine` | UFS AUC ≥ 0.99 on Benchmark 1 AND UFS recall ≥ 0.99 on Benchmarks 2, 3, 4 |

Honest prior distribution over outcomes (documented for calibration check):

| Outcome | Prior |
|---:|---:|
| PASS_strict_superset_of_R12 | 55 % — most likely; UFS can't hurt relative to R12 alone, and terminal-edit / multi-edit physics favour lift |
| PASS_terminal_lift but not multi_edit | 20 % — terminal edits are an easy win for EL; multi-edit lift depends on p_EL's sensitivity to k=3 which is untested |
| PARTIAL_redundant | 15 % — possible if ctrl-null p_EL is already high-variance enough that legitimate Quran windows also get low p_EL by noise |
| PASS_universal_forgery_machine | 5 % — the dream outcome; requires ≥ 0.99 on all 4 which is a high bar especially on Benchmark 4 |
| FAIL_broken_independence | 5 % — EL and NCD could be correlated via "both respond to verse-length shifts", check via §3.5 |

## 5. Honesty clauses

- **HC1 — UFS does NOT close the 8 Adiyat-864 R12 misses.** Pre-registered. The 8 misses are MSA-wellformed internal single-edit variants where both `p_EL ≈ 1` (internal → EL silent) and `p_NCD` is above p95 (proven by exp94 and corroborated by exp105's null). UFS = R12 on Adiyat-864 by construction; no claim of closure is made. The route to closing that floor is a **Quranic-LM R4 channel**, which is separate future work (exp107+).
- **HC2 — Fisher independence is an assumption**, not a proven property. §3.5 gates the whole experiment: if `|ρ| ≥ 0.30`, drop to a logistic combiner. No cherry-picking of ρ thresholds post-hoc.
- **HC3 — Multi-edit threat model is synthetic.** Real forgers target specific semantics (e.g., changing a Quranic ruling); random-position multi-edits are a best-case benchmark for aggregate detectors, not a realistic adversary model. Clearly tagged in the receipt.
- **HC4 — Window size m is a nuisance parameter**. Results stratified by m. If a single value of m dominates (e.g., m = surah length), the stratification is reported but not aggregated.
- **HC5 — Task-A-NCD is exploratory, not pre-registered as the primary statistic**. The primary Task A UFS is the EL-only degenerate form `UFS_A = −2 ln p_EL`.
- **HC6 — Terminal-edit benchmark uses a sample of ≤ 6 000 variants**, not the full exhaustive enumeration across all 114 surahs (which would be ~40 000+ variants). Stratified uniform sample, documented.
- **HC7 — No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`**. Integrity `self_check_end` must pass.
- **HC8 — No modification to existing `exp94` / `exp104` / `exp105` receipts**. All new nulls rebuilt from corpora; existing nulls read only for sanity cross-checks.

## 6. Locks not touched

All new scalars tagged `(v7.9 cand.)`. No modification to protected paths. Integrity `self_check_end` must pass.

## 7. Frozen constants

```python
SEED = 42
FPR_TARGET = 0.05
N_PERT_PER_CTRL_WINDOW = 4000     # preferred; falls back to pooled-z if compute-prohibitive
MULTI_EDIT_K = 3                   # Benchmark 4 edit count
MULTI_EDIT_N_PER_SURAH = 100       # variants per held-out surah
MULTI_EDIT_N_HELDOUT = 20          # 7 B + 7 A + 6 C
TERMINAL_EDIT_CAP = 6000           # Benchmark 3 sample size
TERMINAL_EDIT_STRATIFIED = True    # uniform over 114 surahs
INDEPENDENCE_THRESHOLD = 0.30      # §3.5 Pearson / Spearman gate
FISHER_DF = 4                      # χ²_4 under Fisher's method
MIN_WINDOW_VERSES = 3              # EL undefined for < 2 pairs
MAX_WINDOW_VERSES = 291            # Surah Al-Baqara has 286 verses + basmala prefix in pickle = 287; cap at 291 for safety
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
EXP94_NCD_P95_THRESHOLD = 0.049608  # for R12 comparison on Benchmarks 2-4
EXP104_AUC_BASELINE = 0.9813         # for Benchmark 1 regression gate
EXP94_R12_RECALL_BASELINE = 0.9907   # for Benchmark 2 regression gate
BENCHMARK1_AUC_TOL = 0.005           # FAIL_benchmark1_regression threshold
BENCHMARK2_RECALL_TOL = 0.003        # FAIL_benchmark2_regression threshold
TERMINAL_LIFT_MIN = 0.10             # PASS_terminal_lift threshold
MULTI_EDIT_LIFT_MIN = 0.05           # PASS_multi_edit_lift threshold
UFS_UNIVERSAL_AUC_MIN = 0.99         # PASS_universal_forgery_machine gate
UFS_UNIVERSAL_RECALL_MIN = 0.99      # PASS_universal_forgery_machine gate
```

## 8. Implementation map (for next-session Cascade)

**File to create**: `experiments/exp106_universal_forgery_score/run.py`.

**Imports allowed** (byte-equal to existing experiments):
```python
from experiments._lib import load_phase, safe_output_dir, self_check_begin, self_check_end
from src.features import el_rate
from src.gzip_ncd import ncd  # or whatever exp94 imports as its R12 operator (verify via `grep R12 or ncd experiments/exp94_adiyat_864/run.py`)
```

**Key functions to implement** (specification-complete):

```python
def build_quran_null_EL(CORPORA, min_m=MIN_WINDOW_VERSES, max_m=MAX_WINDOW_VERSES):
    """Returns dict[m -> np.ndarray of empirical EL values] with
    leave-one-surah-out enforcement (the scored surah is excluded from
    its own null). Implementation: for each surah s, for each m, slide
    a window of m verses across s with stride 1, compute el_rate,
    collect by m. Then when scoring surah s' at size m, use the pool
    of all (s, m, window) EXCEPT s=s'. Cache the inclusion mask per s."""

def build_ctrl_edit_null_NCD(CORPORA, N=N_PERT_PER_CTRL_WINDOW):
    """For each m, perturb N ctrl windows under exp94's policy and
    compute NCD(canon_window, perturbed_window). If total budget
    exceeds ~200k perturbations, fall back to pooled-z mode §2.3.4
    and tag receipt accordingly."""

def p_EL(W, canon_source_surah, quran_null_EL):
    """Left-tail Laplace-smoothed CDF, LOO on canon_source_surah.
    §2.2.1 formula exactly."""

def p_NCD(W, canon_W, ctrl_null_NCD):
    """Right-tail Laplace-smoothed CDF. §2.2.2 formula exactly."""

def UFS(W, canon_W, canon_source_surah, quran_null_EL, ctrl_null_NCD,
        task_a_mode=False):
    """Returns (ufs_value, (p_el, p_ncd)) tuple. task_a_mode=True
    degenerates to UFS = -2 ln p_EL per HC5 / §2.3.1."""

def check_fisher_independence(ctrl_windows, quran_null_EL, ctrl_null_NCD):
    """§3.5 gate. Returns (pearson_r, spearman_r, passes). If not
    passes, emit FAIL_broken_independence."""

def benchmark_1_task_A(CORPORA, quran_null_EL):
    """§3.1. Returns {auc_overall, auc_per_band, exp104_sanity_ok}."""

def benchmark_2_adiyat_864(CORPORA, quran_null_EL, ctrl_null_NCD,
                            exp94_receipt):
    """§3.2. Returns {recall_UFS, per_variant_rows}. Enumerates
    Adiyat-864 byte-equal to exp94's _enumerate_864."""

def benchmark_3_terminal_edits(CORPORA, quran_null_EL, ctrl_null_NCD,
                                cap=TERMINAL_EDIT_CAP):
    """§3.3. For each surah, for each verse's terminal letter position
    (last alphabetic char in _terminal_alpha sense), enumerate
    substitutions. Stratified uniform sample across 114 surahs.
    Returns {recall_UFS, recall_R12_same_variants, lift}."""

def benchmark_4_multi_edit(CORPORA, quran_null_EL, ctrl_null_NCD,
                            k=MULTI_EDIT_K):
    """§3.4. Held-out 20 surahs; 100 k-edit forgeries each. Returns
    {recall_UFS, recall_R12, per_band_breakdown}."""

def assign_verdict(results):
    """Applies §4 verdict table in order. Returns verdict_code."""
```

**Expected compute** (on user's machine based on exp104 / exp105 timing):
- Quran-null EL build: ~5 s (all 114 surahs, stride 1, m ∈ [3, 291])
- Ctrl-edit-null NCD build: ~60 – 300 s (4 000 per m × ~50 m values; parallelise across m). Most expensive step; consider pooled-z fallback on first run.
- Benchmark 1: ~3 s (ROC on ~4 800 units)
- Benchmark 2: ~30 s (864 × 2 NCD calls + EL)
- Benchmark 3: ~60 s (6 000 variants × 2 NCD calls)
- Benchmark 4: ~60 s (2 000 variants × 2 NCD calls)
- **Total budget**: ~5 – 15 min depending on null strategy.

**Fingerprint drift**: `load_phase('phase_06_phi_m')` will emit the known warnings (`@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\ZERO_TRUST_AUDIT_2026-04-22.md:180-207` F-05). Expected; does not block.

## 9. Receipts to load

- `results/checkpoints/phase_06_phi_m.pkl` — full CORPORA (integrity-checked via load_phase)
- `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` — keys: `adiyat_864_per_variant[i] = {pos, orig, repl, dL, NCD_edit, dPhi}`; `null_stats.NCD_p95_threshold = 0.049608`; `recalls_at_5pct_fpr.R12_only_baseline = 0.990741`
- `results/experiments/exp104_el_all_bands/exp104_el_all_bands.json` — baseline AUCs per band for regression gate §4
- `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` — optional, for citing the MSA-morphology null in the receipt narrative

## 10. Writes (sandbox-enforced by safe_output_dir)

- `results/experiments/exp106_universal_forgery_score/exp106_universal_forgery_score.json`
- `results/experiments/exp106_universal_forgery_score/self_check_*.json`

## 11. Paper hook

Candidate paper section:
- `docs/PAPER.md §4.38` — **Universal Forgery Score: unifying Task A and Task B into a single χ²₄-distributed scalar**

Structure:
1. Motivation: sequential gating's three failure modes (terminal, multi-edit, unknown-provenance).
2. Formula: §2.3.
3. Null calibration: §2.2.
4. Four-benchmark table.
5. Honest limitation: the Adiyat d=1 emphatic floor remains (HC1) — requires Quranic-LM.

## 12. What this PREREG does NOT cover (deliberate out-of-scope)

- **Quranic-LM (R4) channel** — needs a separate PREREG (exp107+) with a frozen training corpus choice (Quran-only vs Quran + pre-Islamic poetry) and a BPE / char-LM architecture commitment.
- **Full-corpus R13 rerun at exp46 scale** (the follow-up recommendation from exp105's null). Different experiment.
- **Sequential gating benchmark** — already implicit via the sequential argument in the paper; no new code needed.
- **Production deployment form** — the paper claim is scientific (UFS exists, it's well-defined, it dominates R12 on 2 of 4 benchmarks). Engineering the operator-facing tool is separate.

---

*Pre-registered 2026-04-22. Prereg hash is computed at run-time by the not-yet-implemented `run.py` and stored in the output JSON under `prereg_hash` (SHA-256 of this file). Any edit to this file before `run.py` executes invalidates the prereg; re-register and re-timestamp in §Frozen.*

## Appendix — Quick-start for the next Cascade session

If you're a fresh Cascade opening this file, here's the minimal context you need:

1. **What exists on disk**: read `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` and `results/experiments/exp104_el_all_bands/exp104_el_all_bands.json` — these are your two baselines. Their receipts give you the canonical 864 enumeration format (§9) and the ctrl-null structure.

2. **What to model your run.py after**: `experiments/exp104_el_all_bands/run.py` (for the classifier + per-band pattern) and `experiments/exp105_harakat_restoration/run.py` (for the byte-equal enumeration with `_enumerate_864_with_word` and alignment checks against exp94).

3. **Critical invariants**:
   - Byte-equal Adiyat-864 enumeration to exp94 (walk raw `v1 = canon_verses[0]`, filter `ch ∈ ARABIC_CONS_28`, 27 replacements each). Verify via the `alignment_ok` sanity check copied from `exp105/run.py`.
   - Leave-one-surah-out EL null (§2.2.1). If you pool all surahs including the scored one, Benchmark 1 will inflate to AUC ≈ 1.0 by leakage.
   - Laplace smoothing on both p-values (§2.2.1, §2.2.2). Never let p = 0 or 1 → ln blows up.

4. **First sanity run**: implement just `p_EL` + Benchmark 1 and confirm AUC matches exp104 within 0.005 BEFORE building the NCD null. This is your implementation-correctness gate.

5. **If time-budget constrained**: implement Benchmarks 1 + 3 only (Task A + terminal edits). Those are the novel contributions. Benchmarks 2 (tie with exp94) and 4 (multi-edit) can ship in exp106b if needed.

6. **Commit discipline**: all new scalars tagged `(v7.9 cand.)`. Integrity `self_check_end` must pass. No writes outside `results/experiments/exp106_universal_forgery_score/`.
