# exp95i_bigram_shift_detector — Pre-registration

**Hypothesis ID**: H42
**Status**: pre-registered, frozen 2026-04-26 night (Asia/Riyadh), **before opening any bigram-shift scoring on the V1 variant set**.
**Patch context**: v7.9-cand patch G post-V1, rescue-path C from `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md`.
**Supersedes**: nothing. Sits alongside `exp95e_full_114_consensus_universal` (H37 / R53, falsified at V1 scope), `exp95f_short_envelope_replication` (H39, in flight), and `exp95h_asymmetric_detector` (H41, FAIL_no_clean_split_p90 — no length-band split rescues universal detection at fixed τ).

---

## 0. Why this exists (1 paragraph)

After path B (`exp95h_asymmetric_detector`) returned `FAIL_no_clean_split_p90`, no asymmetric combination of the locked NCD detectors rescues universal single-letter forgery detection. The remaining question is whether a **non-NCD, length-independent, symbolic statistic** detects single-letter edits universally. This document locks the bigram-shift statistic, the detector geometry (one-sided "low-Δ" interval), the τ-calibration procedure, and the verdict ladder **before** any scoring is performed.

---

## 1. Hypothesis (one paragraph)

**H42 (bigram-shift universal closure)**: under the bigram-shift statistic
> `Δ_bigram(canon, candidate) = ||hist_2(canon) − hist_2(candidate)||₁ / 2`
where `hist_2(s)` is the multiset-counter of consecutive-letter-pairs after `letters_28(...)` normalisation, and the detector
> *"fires (forgery flagged) iff `0 < Δ_bigram(canon_X, candidate) ≤ τ_high`"*
with `τ_high` calibrated **once globally** as the 5th percentile of the empirical `Δ_bigram(canon_X, peer_P)` distribution over length-matched (canon, peer) pairs across all 114 surahs, single-consonant-substitution forgeries on **every** Quran surah are detected at per-surah recall ≥ 0.99 with global ctrl-null FPR ≤ 0.05.

The directionality (one-sided low-Δ interval) is required by the geometry: for a single-letter substitution, `Δ_bigram ∈ {0.5, 1, 1.5, 2}` (analytic bound, see §3.4); for length-matched non-canon Arabic peer texts, `Δ_bigram` is overwhelmingly larger because the Quran's bigram distribution is highly distinctive (consistent with the project's existing CN, EL, T² findings).

---

## 2. What this is and is not

**This IS**: a length-independent, alignment-aware (canon-keyed but not position-keyed) symbolic forgery detector that uses no compression. It directly tests whether a pure-bigram statistic suffices for universal Quran forgery detection across the full 114-surah corpus.

**This is NOT**:
- A replacement for the deployable trivial detector (Levenshtein edit distance / SHA-256). Those still detect any edit at certainty 1 by definition.
- A claim about the Quran's special structural properties beyond what the V1 receipt already shows (CN, EL, T², F53 Q:100 closure stand independently).
- A re-litigation of R53. R53 retracted the universal *NCD-consensus* extrapolation; H42 is a different detector class entirely.

---

## 3. Locked statistical specification

### 3.1 Letter normalisation

`letters_28(s)` from `experiments.exp95e_full_114_consensus_universal._enumerate.letters_28` — identical to the function used by `exp94`/`exp95c`/`exp95e`. SHA-locked via `experiments.exp95e_full_114_consensus_universal._enumerate.py`.

### 3.2 Bigram histogram

For a normalised letter-string `s` of length `n ≥ 2`, `hist_2(s)` is the `Counter` of all length-2 substrings `s[i:i+2]` for `i ∈ {0, …, n−2}`. There are `n−1` bigrams; the alphabet is the 28 Arabic consonants, so the bigram space has `28² = 784` possible bigrams.

### 3.3 Δ_bigram statistic

`Δ_bigram(canon, candidate) = ||hist_2(canon) − hist_2(candidate)||₁ / 2`.

The factor of 2 normalises so that **a single substitution at an interior position with no aliasing has Δ = 2 exactly**. This makes the variant signal-magnitude scale-free and human-readable.

### 3.4 Variant Δ_bigram bounds (proven, used as audit hook)

For a single-consonant substitution at position `p` of canon `c` with new consonant `c'_p ≠ c_p`:

- **Interior position (`0 < p < n−1`)**:
  - Removed bigrams: `(c[p−1], c[p])` and `(c[p], c[p+1])`
  - Added bigrams: `(c[p−1], c'[p])` and `(c'[p], c[p+1])`
  - L1 ≤ 4, ≥ 2 (depending on aliasing across these 4 bigrams). Hence Δ ∈ {1, 1.5, 2}.
- **Edge position (`p = 0` or `p = n−1`)**:
  - Only one bigram removed and one added.
  - L1 ≤ 2, ≥ 1. Hence Δ ∈ {0.5, 1}.
- **Worst-case ceiling**: `max Δ_bigram(canon, single-substitution variant) = 2.0` exactly.

This bound is reproduced as an explicit audit assertion in the run-time receipt (`audit_hook_max_variant_delta_le_2`).

### 3.5 τ_high calibration (frozen procedure)

1. **Length-matched (canon_X, peer_P) pairs**: for each surah `X` (114 of them), select up to `K_PEERS = 50` peer texts `P` from `CORPORA[non-quran corpora]` such that
   `0.5 · n_canon(X) ≤ n_peer(P) ≤ 1.5 · n_canon(X)`,
   where `n_canon(X) = |letters_28(canon_X)|` and `n_peer(P) = |letters_28(P)|`. Peer selection is **deterministic**: take peers in their existing CORPORA-iteration order until 50 are found or the pool is exhausted.
2. Compute `Δ_bigram(canon_X, P)` for each (X, P) pair → the **ctrl-null Δ pool**.
3. `τ_high = numpy.percentile(ctrl_null_pool, 5)` — the 5th percentile.
4. By construction, FPR (fraction of length-matched peer pairs with `0 < Δ ≤ τ_high`) is **≤ 0.05** globally; per-surah FPR is reported in the receipt as a diagnostic.

**No τ refit, no per-surah τ, no τ from variants.** Calibration is purely on (canon, peer) pairs.

### 3.6 Variant scoring

For each surah `X`, enumerate V1 variants using the **byte-equal** `enumerate_v1` from `experiments.exp95e_full_114_consensus_universal._enumerate`. For each variant `V`:
- Compute the full V1-replaced letter sequence `letters_28(" ".join([V_v0, c.v1, c.v2, …]))` matching the procedure used by `exp95e`.
- `Δ_V = Δ_bigram(canon_X_letters, variant_X_letters)`.
- Variant fires iff `0 < Δ_V ≤ τ_high`.

Per-surah recall = fraction of variants that fire.

---

## 4. Verdict ladder (strict order; first-match wins)

| # | Branch | Trigger |
|---|---|---|
| 1 | `FAIL_audit_hook_violated` | Any variant has `Δ > 2.0` (proves enumerator drift or normalisation drift) OR length-matched ctrl pool is empty for any surah |
| 2 | `FAIL_tau_zero` | `τ_high ≤ 0` (ctrl pool too narrow to discriminate) |
| 3 | `FAIL_q100_regression` | Q:100 K = 1.000 closure under K=2 multi-compressor consensus (`exp95c` baseline) is not preserved by the bigram detector at 100 % on Q:100 (regression check that the new detector at least matches F53 on the closed case) |
| 4 | `FAIL_aggregate_below_floor` | Aggregate variant recall `< 0.99` |
| 5 | `FAIL_per_surah_floor` | Some surah has variant recall `< 0.99` (aggregate may be `≥ 0.99`) |
| 6 | `FAIL_global_fpr_overflow` | Global ctrl-null FPR `> 0.05` (sanity check; should equal 0.05 by construction) |
| 7 | `PARTIAL_p99_aggregate_only` | Aggregate `≥ 0.99`, some surah `< 0.99` but all surahs `≥ 0.90` |
| 8 | `PARTIAL_p99_aggregate_with_p90_floor` | Aggregate `≥ 0.99`, some surah `[0.90, 0.99)` |
| 9 | `PASS_universal_99_bigram` | Every surah `≥ 0.99` AND aggregate `≥ 0.99` |
| 10 | `PASS_universal_999_bigram` | Every surah `≥ 0.999` AND aggregate `≥ 0.999` |
| 11 | `PASS_universal_100_bigram` | Every surah = 1.000 (perfect closure across 114 surahs) |

---

## 5. Honesty clauses

### 5.1 No detector tweaking

If the verdict is `FAIL_*`, the next step is **not** to widen `τ_high` to a higher percentile, change the length-match ratio, or move to bigram weighting / TF-IDF / etc. Each of those is a different detector and would require a fresh PREREG. Path C as defined is exhaustive on this PREREG's locked grid.

### 5.2 No bidirectional re-statement

The detector is one-sided: fire iff `0 < Δ ≤ τ_high`. The complementary half (`Δ > τ_high` → "fire") detects different-text rather than 1-letter-edit and is explicitly NOT this experiment.

### 5.3 No retroactive un-retraction

A `PASS` here does not un-retract R53. R53 retracted the universal NCD-consensus extrapolation; H42 is a fresh hypothesis for a different statistic. A PASS opens candidate finding F55 (length-independent symbolic detector); R53 stays retracted regardless.

### 5.4 No silent corpus shopping

Length-matched ctrl peers are taken in CORPORA-iteration order, not selected by Δ value. The `K_PEERS = 50` cap is a fixed compute-budget bound; if a surah has fewer than `K_PEERS` length-matched peers, we use all of them and record `n_ctrl_matched` in the receipt.

### 5.5 Q:100 regression is informational, not exclusion

The Q:100 regression sub-check (verdict ladder branch 3) confirms the new detector at least matches F53 on the closed case. A failure there would be surprising and suggests detector miscoding, not a substantive reason to abandon path C; the ladder still fires `FAIL_q100_regression` so it is visible in the receipt.

### 5.6 What this does NOT do

- Does NOT replace the trivial Levenshtein detector for deployable forensic integrity.
- Does NOT establish that bigram-shift is universally bounded by `τ_high = 2.5` regardless of corpus — that is a property of *Quran-vs-Arabic-peers* and would need to be re-tested on cross-tradition corpora before any cross-language claim is made (out of scope here, but logged).

---

## 6. Frozen constants (must reproduce these to compute the verdict)

- Variant enumeration: `experiments.exp95e_full_114_consensus_universal._enumerate.enumerate_v1` (byte-equal to `exp95c` / `exp95e` V1 path; SHA-locked via the run-time receipt's parent imports).
- Letter normalisation: `letters_28` from same module.
- Corpus checkpoint: `phase_06_phi_m` (SHA-256 verified by `experiments._lib.load_phase` at run time).
- `K_PEERS = 50` per surah (length-matched ctrl cap).
- Length-match window: `[0.5 · n_canon, 1.5 · n_canon]`.
- τ_high percentile: `5` (from numpy.percentile interpolation default).
- Per-surah recall floor: `0.99` for `PASS_universal_99_bigram`, `0.999` for `PASS_universal_999_bigram`, `1.000` for `PASS_universal_100_bigram`.
- Aggregate recall floor: same as per-surah (every PASS branch requires both).

---

## 7. Protocol (deterministic)

1. Load `phase_06_phi_m` and verify SHA-256 via `experiments._lib.load_phase`.
2. For each non-Quran corpus key in `CORPORA` (in iteration order), collect all peer texts as `(corpus_name, label, letters_28-string)`. This is the global peer pool.
3. For each Quran surah `X`:
   - Compute `canon_X_letters = letters_28(" ".join(canon_verses))`, `n_canon = len(canon_X_letters)`.
   - Length-match peers: take peers with length in `[0.5 n_canon, 1.5 n_canon]` in iteration order, capped at 50.
   - Compute `Δ_bigram(canon_X, peer)` for each matched peer → per-surah ctrl-Δ list.
   - Enumerate V1 variants via `enumerate_v1(canon_verses)`. For each variant: build full `variant_letters` and compute `Δ_bigram(canon_X, variant)` → per-surah variant-Δ list.
4. Pool all per-surah ctrl-Δ → global ctrl-null pool. `τ_high = numpy.percentile(global_pool, 5)`.
5. For each surah: variant fires iff `0 < Δ ≤ τ_high`. Per-surah recall = mean fire rate. Per-surah ctrl FPR = mean fire rate of that surah's ctrl-Δ.
6. Aggregate recall = `Σ_s (recall_s · n_variants_s) / Σ_s n_variants_s`. Aggregate FPR = `Σ_s (fpr_s · n_ctrl_s) / Σ_s n_ctrl_s` (sanity check that this equals 0.05 to within precision).
7. Apply audit hooks: `max_variant_delta ≤ 2.0`, `min n_ctrl_matched ≥ 1`, `τ_high > 0`, Q:100 regression.
8. Apply verdict ladder.
9. Write receipt to `results/experiments/exp95i_bigram_shift_detector/exp95i_bigram_shift_detector.json` with `prereg_hash_actual` matching this document's SHA-256.

---

## 8. Reproduction recipe

```powershell
python experiments\exp95i_bigram_shift_detector\run.py
# verdict appears at:
#   results/experiments/exp95i_bigram_shift_detector/exp95i_bigram_shift_detector.json
```

Wall-time: ~ 1–3 min on 1 core (no compression — pure Counter math; 139 K variants + 5 K ctrl pairs).

---

## 9. Cross-references

- Parent V1 receipt: `results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json`
- Path B receipt (FAIL_no_clean_split_p90): `results/experiments/exp95h_asymmetric_detector/exp95h_asymmetric_detector.json`
- Sibling SHORT replication (in flight): `experiments/exp95f_short_envelope_replication/PREREG.md`
- Planning doc: `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` §2.3
- Hypothesis ledger: `docs/reference/findings/HYPOTHESES_AND_TESTS.md` row H42 (added on launch)
- Related prior work: `exp45_two_letter_746k` (2-letter variants at recall ~ 0.95 via related statistic; this experiment extends to 1-letter and to all 114 surahs).

---

## 10. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any bigram scoring is performed. The hash is logged in:

- `experiments/exp95i_bigram_shift_detector/PREREG_HASH.txt`
- The run-time receipt's `prereg_hash_actual` field.
