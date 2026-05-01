# exp95h_asymmetric_detector — Pre-registration

**Hypothesis ID**: H41
**Status**: pre-registered, frozen 2026-04-26 night (Asia/Riyadh), **before opening any decision-rule scoring on the `exp95e` V1 receipt**.
**Patch context**: v7.9-cand patch G post-V1, rescue-path B from `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md`.
**Supersedes**: nothing. Sits alongside `exp95e_full_114_consensus_universal` (H37 / R53, falsified at V1 scope) and `exp95f_short_envelope_replication` (H39, in flight).

---

## 0. Why this exists (1 paragraph)

After `exp95e` V1-scope returned `FAIL_per_surah_floor`, the user asked whether a deterministic length-band asymmetric decision rule (use detector A on short surahs, detector B on long surahs) rescues universal single-letter forgery detection across all 114 Quran surahs **without any new scoring compute** — purely as an analysis of the V1 receipt that already exists. This document locks the candidate-rule grid and the verdict ladder **before** any rule is evaluated on the receipt's per-surah numbers.

---

## 1. Hypothesis (one paragraph)

**H41 (asymmetric closure)**: there exists `(L₀, D_short, D_long)` with `L₀ ∈ {138, 188, 250, 350, 500, 700, 873, 1000, 1500}` (9 values) and `(D_short, D_long) ∈ G_pairs` (12 pairs, see §2.1) such that the decision rule

> *"if `total_letters_28(s) ≤ L₀` then fire when `D_short(s)` fires, else fire when `D_long(s)` fires"*

achieves per-surah recall ≥ 0.99 on the locked V1 receipt's per-surah-recall numbers, with the **rule's effective FPR upper-bounded by `max(FPR_short, FPR_long)`** under the receipt's locked-τ ctrl-null calibrations.

**Decision-rule grid is FROZEN here**: 9 × 12 = **108 candidate rules**. No rule outside this grid may be reported as PASS by this experiment.

---

## 2. Locked decision-rule grid

### 2.1 Detector pair set `G_pairs` (12 pairs)

Each pair is `(detector for short surahs, detector for long surahs)`. Detectors are exactly those whose per-surah solo / consensus recall is already computed in the V1 receipt (`per_surah[s].recall_solo_*` and `per_surah[s].recall_K*`):

| `D_short` | `D_long` |
|---|---|
| K=2 consensus | gzip-solo |
| K=2 consensus | K=1 consensus |
| K=2 consensus | lzma-solo |
| K=2 consensus | zstd-solo |
| K=2 consensus | gzip-OR-lzma (K=1 over {gzip, lzma}) |
| K=2 consensus | gzip-AND-NOT-bz2 (gzip-solo, but only count fires that bz2 doesn't) |
| K=1 consensus | gzip-solo |
| K=1 consensus | K=1 consensus |
| gzip-solo | gzip-solo |
| gzip-solo | K=1 consensus |
| K=3 consensus | gzip-solo |
| K=3 consensus | K=2 consensus |

Notes:
- `K=1 consensus` = at least 1 of {gzip, bz2, lzma, zstd} fires; FPR globally = receipt's `ctrl_null.fpr_by_consensus_K[1]`.
- `K=2 consensus` = at least 2 of 4 fire; FPR = `ctrl_null.fpr_by_consensus_K[2]`.
- `gzip-solo` = `recall_solo_gzip` per surah; FPR = `ctrl_null.fpr_per_compressor_at_locked_tau.gzip`.
- `gzip-OR-lzma` is computable from receipt's per-surah numbers via Bonferroni-bounded `1 - (1 - r_g)·(1 - r_l)` on per-surah recalls **only as an upper-bound**; the audit treats it as a valid candidate **iff** the bound is achieved by the receipt's underlying variant-level data, otherwise it is dropped from the grid.
- `gzip-AND-NOT-bz2` — included because the V1 receipt shows bz2-solo recall = 0 across all 114 surahs (τ_bz2 too strict at the locked value), which means `gzip-AND-NOT-bz2` reduces to `gzip-solo` here. Its inclusion is for completeness of the pre-registered grid.

### 2.2 L₀ candidate set (9 values)

`L₀ ∈ {138, 188, 250, 350, 500, 700, 873, 1000, 1500}` letters_28.

Anchor points:
- `188`: maximum `total_letters_28` among the 8 K=2-perfect surahs in V1.
- `873`: minimum `total_letters_28` among the 70 K=2-zero surahs in V1.
- Inner values 250 / 350 / 500 / 700 sample the (188, 873) gap.
- Outer values 138 (Al-Fatiha boundary), 1000, 1500 extend the search.

### 2.3 No continuous fitting

The grid is finite and frozen here. **No L₀ between grid points may be reported.** No detector outside `G_pairs` may be reported. If the best rule on the 108-cell grid does not satisfy the verdict ladder's PASS branch, the verdict is `FAIL_no_clean_split` regardless of how close the best non-grid rule could come.

---

## 3. Verdict ladder (strict order; first-match wins)

| # | Branch | Trigger |
|---|---|---|
| 1 | `FAIL_grid_evaluation_error` | Receipt missing required field for any cell of the 108-rule grid |
| 2 | `FAIL_no_clean_split_p90` | Best rule on the grid yields `min_per_surah_recall < 0.90` (i.e., even the loosest bar is unmet) |
| 3 | `FAIL_no_clean_split` | Best rule yields `min_per_surah_recall ∈ [0.90, 0.99)` |
| 4 | `PARTIAL_p99_aggregate_only` | Best rule yields `aggregate_recall ≥ 0.999` AND `min_per_surah_recall ∈ [0.90, 0.99)` (high aggregate but per-surah floor missed) |
| 5 | `PASS_asymmetric_99` | Best rule yields `min_per_surah_recall ≥ 0.99` AND `aggregate_recall ≥ 0.99` |
| 6 | `PASS_asymmetric_999` | Best rule yields `min_per_surah_recall ≥ 0.999` AND `aggregate_recall ≥ 0.999` |

**FPR bookkeeping** (audit-only, not part of the recall verdict): for the winning rule, the receipt records `fpr_upper_bound = max(FPR_short, FPR_long)` where `FPR_short = ctrl_null FPR of D_short at locked τ` and `FPR_long = ctrl_null FPR of D_long at locked τ`. The audit memo flags `fpr_upper_bound > 0.10` as a "loose-FPR" rule (acceptable but worth noting in the receipt). **The recall verdict above is independent of the FPR bookkeeping.**

---

## 4. Frozen constants (must reproduce these to compute the verdict)

- V1 receipt path: `results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json`
- V1 receipt SHA-256: recorded in `prereg_hash_actual` field at run-time; written into this experiment's receipt as `parent_v1_receipt_sha256`.
- Envelope table: `results/experiments/exp95e_full_114_consensus_universal/v1/envelope_table.csv` (provides `total_letters_28` per surah).
- L₀ grid: as in §2.2.
- Detector-pair grid: as in §2.1.
- Verdict ladder: as in §3.
- Per-surah recall bar: 0.99 for `PASS_asymmetric_99`, 0.999 for `PASS_asymmetric_999`.

---

## 5. Protocol (deterministic; no compute on variants)

1. Load V1 receipt JSON and `envelope_table.csv`.
2. Build a `(surah_id → {total_letters_28, recall_K1, recall_K2, recall_K3, recall_K4, recall_solo_gzip, recall_solo_bz2, recall_solo_lzma, recall_solo_zstd})` map for all 114 surahs.
3. For each `(L₀, D_short, D_long)` in the 108-rule grid:
   - For each surah `s`, compute `r_s = recall_{D_short}(s)` if `total_letters_28(s) ≤ L₀` else `recall_{D_long}(s)`.
   - Compute `min_per_surah_recall = min_s r_s` and `aggregate_recall = (sum_s r_s × n_variants(s)) / sum_s n_variants(s)`.
4. Find the rule with the highest `min_per_surah_recall`; tie-break by highest `aggregate_recall`; tie-break by smallest `L₀`; tie-break by lexicographic `(D_short, D_long)` order in §2.1.
5. Apply verdict ladder.
6. Write receipt to `results/experiments/exp95h_asymmetric_detector/exp95h_asymmetric_detector.json` with `prereg_hash_actual` matching this document's SHA-256.

---

## 6. Honesty clauses

### 6.1 No grid expansion

If the verdict is `FAIL_no_clean_split` or `PARTIAL_p99_aggregate_only`, the next step is **NOT** to expand the grid in search of a winning rule. The grid is frozen here precisely to prevent post-hoc grid-shopping. A failure of this experiment is a clean negative result that strengthens the case for path A (per-surah τ recalibration) or path C (bigram-shift) as genuine rescues, not the case for inventing a 13th detector pair.

### 6.2 No FPR rationalisation

If the winning rule has `fpr_upper_bound > 0.10`, the verdict is **NOT** softened to "PASS but loose-FPR". The recall verdict stands as-is; the loose FPR is a flag in the receipt for the paper's discussion of the rule's deployability.

### 6.3 No re-litigation of R53

A PASS verdict here does NOT reopen R53. The retracted hypothesis was "F53 with `exp95c`-locked τ scales universally"; H41 is a different hypothesis (asymmetric decision rule, not a single uniform rule). A PASS would open a candidate finding F55 or F56 (an *engineering* rescue rather than a single-detector rescue), not un-retract R53.

### 6.4 What this is NOT (cross-reference to deployable detector)

A PASS at path B does NOT replace the trivial Levenshtein-edit-distance forensic detector that catches all 1-letter edits at certainty `1 − 2^−n` by definition. The deployable forensic baseline is independent of any compression-based research finding. Path B asks specifically: *can the F53 line of compression-based detectors be rescued by length-band engineering?*

---

## 7. Reproduction recipe

```powershell
python -m experiments.exp95h_asymmetric_detector.run
# verdict appears at:
#   results/experiments/exp95h_asymmetric_detector/exp95h_asymmetric_detector.json
```

Wall-time: < 5 min on 1 core (pure analysis of V1 receipt; no NCD scoring).

---

## 8. Cross-references

- Parent V1 receipt (FAIL_per_surah_floor → R53): `results/experiments/exp95e_full_114_consensus_universal/v1/`
- V1 PREREG (matched hash): `experiments/exp95e_full_114_consensus_universal/PREREG.md`
- Sibling SHORT replication (in flight): `experiments/exp95f_short_envelope_replication/PREREG.md`
- Planning doc: `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` §2.2
- Hypothesis ledger: `docs/reference/findings/HYPOTHESES_AND_TESTS.md` row H41 (added on launch)

---

## 9. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** the V1 receipt is opened for scoring. The hash is logged in:

- `experiments/exp95h_asymmetric_detector/PREREG_HASH.txt`
- The run-time receipt's `prereg_hash_actual` field.
