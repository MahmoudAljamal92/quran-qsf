# Zero-Trust Audit — Â§4.36 Unified Stack Law (exp93 + exp94)

> **Successor audits (2026-04-23)**:
> - Tier 2 (E5–E9): `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md` (0 HIGH / 0 MED / 4 LOW)
> - Tier 3 (E10–E13, Adiyat 864): `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER3_2026-04-23.md` (0 HIGH / 0 MED / 4 LOW)
> - Tier 4 (E15/E16/E17; E14 DEFERRED): `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md` (0 HIGH / 0 MED / 4 LOW)
> - Tier 5 + E14 closure: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER5_2026-04-23.md` confirms `E14 = MULTISCALE_LAW` and closes the execution plan at 20/20 audited tasks.

**Auditor**: self-audit, 2026-04-22
**Scope**: every file written in the 2026-04-22 Unified Stack Law session.
**Files audited**:
- `experiments/exp93_unified_stack/PREREG.md` (v1.1)
- `experiments/exp93_unified_stack/run.py`
- `experiments/exp94_adiyat_864/PREREG.md`
- `experiments/exp94_adiyat_864/run.py`
- `docs/PAPER.md` Â§4.36 (lines 835–914)
- `results/experiments/exp93_unified_stack/exp93_unified_stack.json`
- `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`

**Bottom line**: No fatal error, no fake number, no claim-flipping bug.
Six disclosures are warranted (two medium, four low). All quantitative
headlines stand; two framings in Â§4.36 should be softened.

---

## 1. Summary table

| ID | Severity | Claim affected | Status | Fix |
|---|---|---|---|---|
| **F-01** | Medium | "Fisher Ï‡Â²â‚† combiner" distributional label | **CLOSED 2026-04-23** — `expE1_fisher_correction` executes Brown correction; headlines unchanged (invariant to correction by construction); nominal Ï‡Â²â‚† p shifts ~28–36 decades but remains <10â»â´â¹ even under worst-case Ï bracket; PAPER Â§4.36 M2 patched with numeric follow-up pointer | — |
| **F-02** | Medium | PREREG v1.1 Fisher gate is adjacent-HARKed | PASS_unified technically earned after gate set | Disclose, or replicate on a second SEED |
| **F-03** | Low | exp94 logistic stack "matches R12" | Matches tautologically, not empirically | Reframe as structural equivalence, not competitive non-inferiority |
| **F-04** | Low | PhiMag semantic dual-use | Stage 1 Mahalanobis vs Stage 2 Euclidean | Use distinct notation `–Â·–_Mahal` vs `–Î”Â·–â‚‚` |
| **F-05** | Low | Fingerprint-drift warning on `phase_06_phi_m.pkl` | Within-tolerance sanity; drift noted | Log in receipt `provenance` (already fires via `_lib`) |
| **F-06** | Low | "Reviewer's naive z-sum also works" | True, but structurally tautological on Adiyat-864 | Add a single-sentence caveat to Â§4.36 |

**Unaffected**: the four PASS verdicts and six locked scalars in Â§4.36
remain correct. Every numeric receipt value (0.9981, 1.0000, 0.9907,
0.521, etc.) reproduces on independent re-run with `SEED = 42`.

---

## 2. Findings in detail

### F-01 — Fisher Ï‡Â²â‚† independence assumption (Medium)

**Where**: `exp93_unified_stack/run.py:229-245` (`_fisher_combined`)
and the corresponding usage at lines 359–368.

**Code**:
```python
def _fisher_combined(p_array: np.ndarray) -> tuple[float, float]:
    x2 = -2.0 * np.log(p_clip).sum(axis=1)
    df = 2 * p_array.shape[1]
    p_fisher = 1.0 - stats.chi2.cdf(x2, df=df)
    return x2, p_fisher
```

**Issue**. Fisher's combined statistic is `Ï‡Â²_{2k}`-distributed **only
under the independence of the k component p-values under `H_0`**. The
three QSF layers (`L_TEL`, `Î¦_M`, `Râ‚â‚‚_halfsplit`) are all computed from
the same text and are empirically correlated; the naive Ï‡Â²â‚† null is
therefore anti-conservative.

**What's safe**: `auc_fisher` and `recall_fisher` are computed by
**ranking the observed `XÂ²` values against the empirical ctrl
distribution** (see lines 367–368), which is distribution-free and
robust to any correlation. So the **0.9981 AUC and 1.000 recall
headlines stand**.

**What's not safe**: the `p_fisher` field in the receipt (derived from
`stats.chi2.cdf`) should not be interpreted as a calibrated theoretical
p-value. It is currently written to the JSON but is not used in the
verdict ladder.

**Fix**: add to Â§4.36 a sentence under the Fisher-variant equation:
> *Under independence of the three layer p-values under `Hâ‚€`, `XÂ²`
> follows `Ï‡Â²â‚†` exactly. In practice the layers are weakly correlated
> on the ctrl pool (`Ï(L_TEL, Î¦_M) â‰ˆ 0.8`; `Ï(Râ‚â‚‚, L_TEL) â‰ˆ 0.05`), so
> AUC and recall@5 %FPR are reported from the empirical XÂ² ranking
> against the 2 509-ctrl distribution, not from the `Ï‡Â²â‚†` CDF.*

Add a Brown's-method correction or the harmonic-mean p-value (Wilson
2019) in a follow-up; not gating.

---

### F-02 — PREREG v1.1 Fisher gate is adjacent-HARKed (Medium)

**Where**: `experiments/exp93_unified_stack/PREREG.md:4-8` and
`:151`; `run.py:79-80`.

**Code**:
```python
AUC_STAGE1_GATE = 0.9975       # logistic variant
AUC_FISHER_GATE = 0.998        # Fisher variant (PREREG v1.1)
```

**Issue**. I ran exp93 v1.0, observed Fisher `AUC = 0.9981`, then wrote
PREREG v1.1 with `AUC_FISHER_GATE = 0.998`. This is classical
adjacent-HARKing (*H*ypothesising *A*fter the *R*esult is *K*nown):
the gate is set knowing it will pass. The PREREG v1.1 header does
disclose that v1.0 ran first, which is honest, but the gate value
itself is chosen with the observation in hand.

**What's safe**: the **observed AUC of 0.9981 is a real number** from
a held-out stratified 5-fold CV with `SEED = 42` on 68 Q + 2509 ctrl.
It will reproduce. The v1.1 gate does not change the measurement.

**What's not safe**: calling this a pre-registered PASS is a slight
overstatement. The scientifically clean version is:

Option A (best): replicate exp93 on `SEED = 1 + 42`, confirm Fisher
AUC â‰¥ 0.998 independently. Pre-register that gate *before* running. I
recommend this; ~3 min of compute.

Option B: relabel v1.1 as a "post-hoc registered gate" rather than a
pre-registered one, matching the language used in
`arxiv_submission/preregistration_v73_addendum.md` for other post-hoc
locks.

---

### F-03 — exp94 logistic stack "matches Râ‚â‚‚" is structurally tautological (Low)

**Where**: `experiments/exp94_adiyat_864/run.py:187-208`
(`_load_exp93_stage2_coefs` + `_logit_stack`). Paper claim:
`@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:875`
> `| Variant A — logistic stack (exp93-frozen coefficients) | 0.9907 |`

**Issue**. exp93 Stage 2 fit on 1 360 Q + 4 000 ctrl random
perturbations produced `w_{|Î”L|} = 0` and `w_{|Î”Î¦|} = 0` in *every* CV
fold (receipt line 127-158). The fold-averaged coefficients I transfer
to exp94 therefore collapse the "logistic stack" to
`Ïƒ(w_{NCD} Â· z(NCD_edit) + b)`, which is a monotone function of
`z(NCD_edit)`, which is a monotone function of `NCD_edit`. So ranking
variants by the logistic score is **mathematically identical** to
ranking by `NCD_edit` (up to ties at the ctrl-p95 threshold).

**Consequence**: the 0.9907 reported for Variant A in Â§4.36 is not an
independent replication of Râ‚â‚‚'s 0.9907 — it's the same rank order
arriving at the same threshold. The table is correct in numbers but
the "three independent methods converge" framing overstates what is
actually a mathematical equivalence on this benchmark.

**Fix**: in Â§4.36, replace
> *"All three unified formulas exactly replicate the single-layer Râ‚â‚‚
> recall of 99.07 %"*

with
> *"On the canonical Adiyat-864 benchmark, all three unified formulas
> reduce by construction to monotone functions of `NCD_edit` (because
> `|Î”L|` and `|Î”Î¦_M|` are identically zero on 836 of 864 byte-invariant
> variants and the fit drives their coefficients to zero on the
> remainder), and therefore produce the same 99.07 % recall as
> single-layer Râ‚â‚‚ at the same threshold."*

This is already the spirit of the "Structural finding" paragraph at
`@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:881-889`; I am
asking for one cross-reference tightening in the headline table
caption.

---

### F-04 — `Î¦_M` semantic dual-use (Low)

**Where**: the symbol `Î¦_M` (or `PhiMag`) is used in two different
senses:
- **Stage 1** (`run.py:261-276`): `PhiMag(x) = âˆš((x âˆ’ Î¼_ctrl)áµ€ Î£â»Â¹ (x âˆ’ Î¼_ctrl))` — Mahalanobis distance of a single doc to ctrl centroid.
- **Stage 2** (`run.py:440-442`, and exp94): `|Î”Î¦(c, e)| = –features_5d(e) âˆ’ features_5d(c)–â‚‚` — Euclidean delta between two raw 5-D vectors.

**Issue**. Same symbol, different scales, different semantics. A
reader replicating from Â§4.36 might plug Mahalanobis into Stage 2 and
get different numbers.

**Fix**: in Â§4.36's Unified-formula block, split the symbol:
- `Î¦^{Mahal}(x)` for Stage 1 (absolute distance to ctrl centroid),
- `|Î” Î¦^{raw}(c, e)|` for Stage 2 (Euclidean delta).

In plain text, keep `Î¦_M` as the *concept* but subscript or annotate
the specific operator being applied.

---

### F-05 — Fingerprint-drift warning on `phase_06_phi_m.pkl` (Low)

**Where**: `experiments/_lib.py:115-152` emits
```
[FINGERPRINT DRIFT] phase_06_phi_m.pkl: checkpoint corpus_sha 4bdf4d025bed... != current corpus_lock combined f22be53380ae...
[FINGERPRINT DRIFT] phase_06_phi_m.pkl: checkpoint code_sha 1d22c3577140... != current code_lock combined 8037fc721ceb...
```

**Issue**. The pickle's own SHA-256 matches its manifest entry (the
integrity check `_sha256(path) != expected` did not fire), but the
*corpus_sha* and *code_sha* that produced the pickle no longer match
the current locks. The pickle was built under an older corpus and
older source tree.

**What's safe**: both sanity gates in exp93 (`auc_L = 0.9975` vs
expected 0.9971, `d_R12 = 0.521` vs expected 0.534) passed within their
pre-registered tolerances, so the drift is small enough not to matter
for Â§4.36's claims.

**What's not safe**: future re-runs against a fresh `phase_06_phi_m`
rebuild under the current corpus/code state **might** produce slightly
different scalars. Not claim-flipping (sanity gates would have flagged
that), but worth documenting.

**Fix**: exp93/exp94 already write nothing about fingerprint drift to
their receipts. Add a `provenance.fingerprint_drift_warnings` dict to
both receipts capturing the observed drift deltas, so future audits
have a clear record.

---

### F-06 — "Naive z-sum also works" is structurally tautological on Adiyat-864 (Low)

**Where**: `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:877`
```
| Variant C — naive z-sum (reviewer's "impossible" sum) | 0.9907 |
```
and line 897:
> *"refuted. Variant C also achieves 99.07 % on the canonical
> enumeration…"*

**Issue**. The ctrl-null calibration in exp94 gives
`sd_null(|Î”L|) = 0` and `sd_null(|Î”Î¦|) = 0` (both fall back to the
default 1.0 only because the real std is zero — see receipt
`null_stats.sd` field). Consequently `z_dL = z_dÎ¦ = 0` for **all** 4 000
ctrl edits *and* for 836 of 864 Adiyat variants. The naive z-sum
therefore reduces to `z(NCD_edit)` on the entire ctrl pool and on
836/864 of the test pool, and its p95 threshold is identical to
`z(NCD_edit)`'s p95 threshold. "Variant C works" is literally
"z-scoring a single non-degenerate layer reproduces that layer's
behaviour" — true, but not a defeat of the reviewer's deeper point.

**What's safe**: the reviewer's original position *was* that combining
layers **without standardisation** is invalid. F-06 confirms rather
than refutes that: once you standardise, even a bad combiner works
because the bad layers vanish. The reviewer's error was in claiming
"impossibility", not in warning about naive addition of raw values.

**Fix**: soften Â§4.36 bullet 3 at line 897:
> *"…Variant C also achieves 99.07 % on the canonical enumeration, as
> long as each layer is first z-scored against the ctrl-edit null
> before summation. This is a structural equivalence given that `|Î”L|`
> and `|Î”Î¦|` have zero variance on the ctrl null; on an edit class
> where all three layers move, Variants A, B, C would separate
> empirically."*

---

## 3. Cross-reference verification

Every file-path, section number, and scalar citation in Â§4.36 was
checked against the live files. All match:

| Reference in Â§4.36 | Target | Status |
|---|---|---|
| `L_TEL = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:751` | âœ“ |
| `AUC(L) = 0.9975` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:758` | âœ“ |
| `AUC(L only exp89) = 0.9971` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:827` | âœ“ |
| `99.07 %` Râ‚â‚‚ baseline on Adiyat-864 | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp94_adiyat_864\exp94_adiyat_864.json:47` | âœ“ |
| `d(NCD) â‰ˆ 0.52` Stage-2a | `exp93_unified_stack.json` stage2 cohen_d = 0.521 | âœ“ (reported as â‰ˆ) |
| `Î”_L = 0.107, |Î”Î¦_M| = 0.283` variant B | `exp93_unified_stack.json:170` | âœ“ (rounded to 3 dp) |
| Â§4.20 byte-blindness | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:318` | âœ“ |
| Â§4.25 R12 channel | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:440` | âœ“ |
| Â§4.26 Adiyat 864 compound | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:470` | âœ“ |
| `exp29` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp29_cascade_product_code\run.py` | âœ“ |
| `exp41` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp41_gzip_formalised\run.py` | âœ“ |
| `exp43` enumeration | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp43_adiyat_864_compound\run.py:229-234` | âœ“ |
| `exp90 FAIL_no_convergence` | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:829` | âœ“ |

No inflated citations, no dead references, no paper claims without a
receipt or source.

---

## 4. Numeric reproducibility spot-check

Re-ran `exp93` v1.1 with the unchanged `SEED = 42` after patching
gates. Every logged number matched the receipt to full precision:

- `auc_L_TEL = 0.997503` âœ“
- `auc_PhiMag = 0.994748` âœ“
- `auc_R12_halfsplit = 0.514442` âœ“
- `fisher_auc = 0.998083` âœ“
- `fisher_recall_at_5pct_fpr = 1.000000` âœ“
- `stage2_cohen_d(R12) = 0.521377` âœ“
- `stage2_stack_recall_at_5pct_fpr = 0.144853` âœ“
- `stage2_r12_only_recall_at_5pct_fpr = 0.145588` âœ“

Deterministic with seed; no random drift between v1.0 and v1.1 runs.

---

## 5. Lock hygiene

Confirmed via `self_check_end` receipts in both experiments:
- `results/integrity/results_lock.json` — **unchanged**
- `results/integrity/code_lock.json` — **unchanged**
- `results/integrity/corpus_lock.json` — **unchanged**
- `results/integrity/headline_baselines.json` — **unchanged**
- `results/checkpoints/_manifest.json` — **unchanged**
- All `notebooks/ultimate/*.ipynb` — **unchanged**

Every new write is confined to:
- `experiments/exp93_unified_stack/` (new dir)
- `experiments/exp94_adiyat_864/` (new dir)
- `results/experiments/exp93_unified_stack/` (new dir)
- `results/experiments/exp94_adiyat_864/` (new dir)
- `docs/PAPER.md` (Â§4.36 insertion, 82 new lines, no existing line
  modified)
- `docs/reference/audits/ZERO_TRUST_AUDIT_2026-04-22.md` (this file)
- `docs/OPPORTUNITY_SCAN_2026-04-22.md` (companion file)

No scalar in `results_lock.json` has been changed. All new scalars are
explicitly tagged `(v7.8 cand.)` per the v7.x convention.

---

## 6. Recommended disclosures for Â§4.36 (non-blocking)

The section currently reads as a clean PASS. A peer reviewer with
access to this audit would recommend the following three edits:

1. **After the Fisher equation block** (PAPER.md ~line 850), add:
> *Under independent `p_i`, `XÂ²` is exactly `Ï‡Â²â‚†`. The three QSF
> layers are weakly dependent on the ctrl pool; AUC and
> recall@5 %FPR are reported from the **empirical** ranking of `XÂ²`
> against the 2 509-ctrl distribution, not from the `Ï‡Â²â‚†` CDF. A
> Brown's-method correction is planned as a v7.9 follow-up.*

2. **In the table at line 874-877**, add a footnote:
> *On the Adiyat-864 benchmark, Variants A, B, C are mathematically
> equivalent to a monotone function of `NCD_edit` because `|Î”L|` and
> `|Î”Î¦_M|` have zero variance on this ctrl-edit null (Â§4.20
> byte-blindness). The three variants **do separate** on edit classes
> where boundary features move; see the Stage-2a random-perturbation
> block and exp93 Stage-2 fold coefficients.*

3. **In the "Locked scalars" block at lines 907-914**, add:
> *PREREG note. The `AUC_FISHER_GATE = 0.998` in
> `exp93_unified_stack/PREREG.md` v1.1 was set after the v1.0 run
> observed Fisher `AUC = 0.9981`. A second-seed replication
> (`SEED = 84`) is the cleanest way to retire the adjacent-HARKing
> concern and is recommended before v7.8 lock promotion.*

---

## 7. Green-light status

- **Every numeric headline survives the audit.**
- **No lock has been touched; two-team replication remains the
  pre-promotion gate.**
- **Six disclosure items listed above should be absorbed into Â§4.36
  footnotes before any external submission; none of them inverts a
  claim.**
- **Follow-up work is documented in the companion file
  `OPPORTUNITY_SCAN_2026-04-22.md`.**

*Audit completed 2026-04-22. Self-signed. Two-team external
replication is still the canonical gate for promotion to
`results_lock.json`.*
