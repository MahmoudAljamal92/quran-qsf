# Post-V1 paths forward — F53 universal-detection rescue

**Authored**: 2026-04-26 night, immediately after `exp95e_full_114_consensus_universal` V1-scope receipt landed (verdict `FAIL_per_surah_floor`, R53).
**Status**: planning document. Locks the **design space** for the three candidate rescue experiments so that tomorrow's choice is between **pre-registered alternatives**, not invented post-hoc.
**Decision deferred**: the SHORT-scope replication of `exp95e` (H39, in flight, ETA ~ 03:30) materially changes which path is most informative. Final selection happens **after** SHORT lands and **before** any rescue experiment is launched.

---

## 0. Why this document exists

The user asked the deeper question: *"can we detect any 1-letter add / remove / replace in any location, by pure math, without cheating, without memorising?"*. The honest answer split into two parts:

1. **Trivial deployable detector**: Levenshtein edit distance against the locked Hafs ʿan ʿĀṣim canon catches any 1-letter edit at certainty `1 − 2^−n` by definition. Pure math, O(n²) time, no calibration. **This is true today and should be the explicit forensic baseline in the paper.**
2. **Research-grade compression-based witness** (the F53 line): does a *length-independent, alignment-free, compressed* statistic also detect every 1-letter edit? Tonight's V1 result says: at fixed τ from `exp95c`, **no** — only 8 / 114 surahs. The question for the rescue experiments is whether a different *calibration* or a different *statistic* lifts that to all 114 without sacrificing the FPR control or the pre-registration discipline.

This doc pre-registers three candidate rescue experiments (paths A / B / C) so that tomorrow's choice is locked-in advance.

---

## 1. The information-theoretic ceiling (so we don't pretend any path will trivially close the gap)

Single-letter edit in an `n`-letter surah:

| Surah | n (letters_28) | Edit signal as fraction of corpus | Where this puts us |
|---|---|---|---|
| Q:108 al-Kawthar | 42 | 1 / 42 = 2.4 % | Far above any reasonable compressor noise floor |
| Q:100 al-ʿĀdiyāt | 188 | 0.53 % | Above gzip noise floor; K=2 closes |
| Q:001 al-Fātiḥa | 138 | 0.72 % | Above noise; K=2 = 0.998 |
| Q:099 al-Zalzalah | 184 | 0.54 % | At noise edge; 998/999 |
| Q:055 ar-Raḥmān | ~ 1 700 | 0.06 % | At edge of compressor sensitivity |
| Q:002 al-Baqarah | ~ 25 700 | 0.004 % | Below typical NCD noise; gzip happens to fire (anomalously) |
| Q:003 Āl ʿImrān | ~ 14 500 | 0.007 % | Below NCD noise on all 4 compressors at fixed τ |

**Implication**: any compression-based detector at *fixed τ* must fail somewhere in `1 700 ≤ n ≤ 14 500`. The question is whether *adaptive* τ pushes the boundary out, and how far. **No path among A / B / C is information-theoretically guaranteed to reach 100 % across all 114 surahs**; the design space is bounded.

---

## 2. Three pre-registered paths

### 2.1 Path A — `exp95g_per_surah_tau` (per-surah τ recalibration)

**H40 (locked)**: under K = 2 multi-compressor consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} with τ values **per-surah-recalibrated** at FPR = 0.05 against a length-matched Arabic ctrl null pool, single-letter consonant-substitution forgeries are detected at per-surah recall ≥ 0.99 across **all 114 surahs**, with mean per-surah ctrl-null FPR ≤ 0.05 and tail-FPR (max across surahs) ≤ 0.10.

**Protocol**:

1. For each surah `s ∈ 114`:
   - Build a length-matched ctrl null pool of `≥ 200` Arabic peer texts whose `total_letters_28` lies in `[0.7·n_s, 1.3·n_s]`. (Use the existing 2 509-corpus Arabic peer pool with length-stratified sampling.)
   - For each compressor `c ∈ {gzip, bz2, lzma, zstd}`, compute NCD(s, ctrl_i) for each ctrl_i, take the 5 %-quantile of the resulting distribution as `τ_s_c`.
   - Score the same 27 × n_s_v1 V1 variants from the V1 receipt at thresholds `(τ_s_gzip, τ_s_bz2, τ_s_lzma, τ_s_zstd)`. Apply K = 2 vote.
2. Embedded Q:100 regression: re-score Q:100 at the recalibrated τ_Q100 and verify K = 2 ≥ 0.999. (If τ_Q100 disagrees with the locked `exp95c` τ by more than ~ 30 %, the per-surah ctrl pool is mis-specified.)
3. Aggregate verdict ladder (strict order):

| # | Branch | Trigger |
|---|---|---|
| 1 | `FAIL_recalib_q100_drift` | Recalibrated Q:100 K = 2 falls below 0.999 (would mean recalibration broke the proven case) |
| 2 | `FAIL_per_surah_fpr_blowup` | Mean per-surah ctrl FPR `> 0.05` OR tail-FPR (max) `> 0.10` |
| 3 | `FAIL_per_surah_floor_recalib` | Per-surah K = 2 recall `< 0.99` for any surah |
| 4 | `PARTIAL_p90_recalib` | Per-surah K = 2 recall ≥ 0.90 (not 0.99) on every surah, plus FPR controls hold |
| 5 | `PASS_universal_99_recalib` | Per-surah K = 2 recall ≥ 0.99 on every surah, plus FPR controls hold |
| 6 | `PASS_universal_999_recalib` | Per-surah K = 2 recall ≥ 0.999 on every surah, plus FPR controls hold |

**Audit hooks** (must reproduce):

- Recalibrated τ for Q:100 stored alongside locked τ; absolute drift recorded.
- Per-surah ctrl FPR distribution included in receipt.
- Q:100 K = 2 recall under recalibrated τ ≥ 0.999.

**What this path tests**: whether F53's failure on long surahs is a **calibration** problem (τ frozen on Q:100's NCD scale doesn't match al-Baqarah's NCD scale) rather than a **signal** problem. If the receipts show that recalibrated τ matches each surah's NCD distribution and the variant signal is still above the recalibrated noise floor, recall lifts. If the variant signal is below the noise floor at any sustainable FPR, recall stays low and we know the limit is information-theoretic.

**Wall-time estimate**: per-surah ctrl-pool construction ~ 30 min on 6 cores; scoring ~ 1 h. Total ~ 2 h.

**Risk of failure**: HIGH on surahs where lzma / zstd NCDs are < 0.005 even on legitimate Arabic ctrl. There may be ~ 10–30 surahs where the variant signal is genuinely below the FPR-respecting noise floor. The verdict would be `FAIL_per_surah_floor_recalib` or `PARTIAL_p90_recalib`. **That is still a useful negative result**: it cleanly establishes the information-theoretic limit and confirms the bounded-domain reading of F53.

---

### 2.2 Path B — `exp95h_asymmetric_detector` (length-band split)

**H41 (locked)**: there exists a deterministic decision rule of the form `(if total_letters_28 ≤ L₀ then K=2 consensus else gzip-solo)` with `L₀ ∈ [188, 873]` such that single-letter consonant-substitution forgeries are detected at per-surah recall ≥ 0.99 across **all 114 surahs**.

**Protocol**:

1. Re-use V1 receipt directly (no new variants).
2. For each candidate split `L₀ ∈ {188, 250, 350, 500, 700, 873}`:
   - Apply rule to each surah; compute per-surah recall and aggregate.
   - Compute decision-rule FPR on V1 ctrl-null pool by applying the same rule to ctrl items length-matched to each surah.
3. Verdict: smallest `L₀` such that per-surah recall ≥ 0.99 holds; if no such `L₀` exists, `FAIL_no_clean_split`.

**Audit hooks**: decision rule must be a single deterministic function of `total_letters_28`; no per-surah hand-tuning of `L₀`; gzip-only τ for the long branch is the locked `exp95c` τ_gzip = 0.0496.

**What this path tests**: whether **the existing V1 data already supports a deployable decision rule** that uses the right tool at the right length, without any new compute. Failure mode: if gzip-solo also fails on Q:003 / Q:005 / Q:006 / etc. (which the V1 receipt shows it does — those surahs' gzip K=1 = 0), the asymmetric rule won't reach 99 % at any `L₀`.

**Wall-time**: < 5 min (purely an analysis of the V1 receipt).

**Honest assessment**: **likely to fail** at the 99 % bar because the V1 receipt shows ≥ 30 surahs at K=1=0 *and* K=2=0 on gzip-only. Path B's value is **as a clean negative result**: it documents that no length-band split rescues F53 without recalibration, which strengthens path A's necessity.

---

### 2.3 Path C — `exp95i_bigram_shift_detector` (length-independent statistic)

**H42 (locked)**: under a bigram-frequency-shift statistic `Δ_bigram(canon, candidate) = ||hist_2(canon) − hist_2(candidate)||₁ / 2`, single-letter consonant-substitution forgeries on every Quran surah produce `Δ_bigram ≥ Δ_τ` at recall ≥ 0.999 with ctrl-null FPR ≤ 0.05, where `Δ_τ` is calibrated **once globally** at FPR 0.05 on the Arabic peer ctrl pool.

**Why this is length-independent in theory**: a single substitution at position `i` removes 2 bigrams (positions `(i-1, i)` and `(i, i+1)`) and adds 2 different bigrams. Δ_bigram on histograms therefore shifts by exactly 4 / N_bigrams in `L₁` norm, where N_bigrams = n − 1. For n = 26 000 this is a tiny relative shift (~ 1.5·10⁻⁴), but it is **deterministic and not noise-floored** in the same way NCD is — there is no compressor window absorbing the change. The question is whether the *ctrl-null distribution* of Δ_bigram on legitimate Arabic peer texts has a tight enough p95 that the variant shift sits above it.

**Protocol**:

1. Build a global Arabic-peer ctrl null pool (~ 2 000 length-stratified peer texts).
2. For each ctrl peer `p`, compute Δ_bigram(p, p_perturbed_random) where p_perturbed_random is a randomly-chosen single-position substitution.
3. Set `Δ_τ` at the 95th percentile of the resulting null distribution.
4. Score the same 27 × n_s_v1 V1 variants against canon for each surah; flag fires if Δ_bigram ≥ Δ_τ.
5. Verdict ladder (strict order):

| # | Branch | Trigger |
|---|---|---|
| 1 | `FAIL_bigram_q100_drift` | Q:100 recall under Δ_bigram < 0.999 (regression check; should match or exceed K=2 NCD) |
| 2 | `FAIL_bigram_overfpr` | Ctrl FPR > 0.05 |
| 3 | `FAIL_bigram_per_surah_floor` | Per-surah recall < 0.99 |
| 4 | `PARTIAL_bigram_p90` | Per-surah recall ≥ 0.90 |
| 5 | `PASS_bigram_universal_99` | Per-surah recall ≥ 0.99 |
| 6 | `PASS_bigram_universal_999` | Per-surah recall ≥ 0.999 |

**Audit hooks**: bigram histogram built on the canonical 28-consonant alphabet (no Hamza, ʾalif-tashkīl); Δ measured in `L₁` after normalisation by total bigram count; canon's own `hist_2` cached and stored alongside receipt.

**What this path tests**: whether a **length-independent symbolic** statistic (no compression involved) detects all 1-letter edits universally. This is conceptually the cleanest test of the user's question (*"by pure math, length-invariant"*).

**Honest assessment**: **plausibly succeeds at 99 %, unlikely to reach 99.9 %**. The bigram-shift signal is exactly the same magnitude (4 / N_bigrams) for every position in a surah, but the *ctrl-null distribution* has its own variance because legitimate Arabic peer texts differ in bigram frequency by larger amounts than one-letter edits do. The discriminating power depends on how separable the variant Δ is from the cross-text Δ baseline. Empirically this is the question.

**Wall-time**: ~ 30 min on 1 core (no compression — pure histogram math).

**Existing related work**: `exp45_two_letter_746k` already tested **2-letter** variants at recall ~ 0.95 using a related statistic. exp95i would extend that to 1-letter and to all 114 surahs.

---

## 3. Decision tree for tomorrow (depends on SHORT outcome)

The SHORT-scope replication of `exp95e` (H39 envelope replication) is in flight. Its outcome materially changes which path is most informative:

| SHORT outcome | Implication | Recommended next experiment |
|---|---|---|
| `PASS_envelope_replicates` (Pearson r ≤ −0.85, phase boundary holds) | Detection failure on long surahs is a **clean, replicating, length-driven signal** — F53's domain is bounded by a real mechanistic law | **Path A first** (per-surah τ recalibration). If A passes universally → F53 widens honestly. If A produces `PARTIAL_p90` with a clean information-theoretic floor → write up the bounded-domain finding as F55 + add edit-distance baseline to paper. |
| `PARTIAL_envelope_replicates` (r ∈ (−0.85, −0.70], boundary holds) | Envelope is real but weaker than V1 — replication confirms but partially | **Path A first**, same reasoning |
| `FAIL_envelope_correlation` or `FAIL_envelope_phase_boundary` | V1 envelope was a single-corpus quirk; the per-surah failure pattern is *not* explained by length | **Path C** (bigram-shift) — if the failure isn't length-driven, per-surah τ won't help; we need a different statistic |
| Any audit-hook failure on SHORT (τ-drift, Q:100-drift, variant-count) | Run is invalid; investigate before any rescue experiment | Diagnose drift; do not run any of A / B / C until the SHORT receipt audit passes |

**Path B** (asymmetric) is a 5-minute analysis of the existing V1 receipt regardless of SHORT outcome and can be done as a sidebar at any time. It mostly serves to document the negative result *no clean length-band split exists*, which strengthens the case for path A or C as the actual fix.

---

## 4. Paper-level baseline (independent of A / B / C outcomes)

Regardless of which rescue experiment is run, `PAPER.md` should gain a paragraph (probably as `§4.43.0a` or as a new `§4.43.2`) making the **trivial deployable detector** explicit:

> *"For practical forensic integrity of the canonical text against any 1-letter add / remove / replace, Levenshtein edit distance against the locked Hafs ʿan ʿĀṣim canon detects all such edits with certainty `1 − 2^−n` by definition; SHA-256 hashing of the canonical UTF-8 encoding is equivalent at cryptographic security. Both are O(n) or O(n²) deterministic algorithms requiring no calibration. The `exp95c` / `exp95e` line of work investigates a strictly stronger question: whether a **length-independent, alignment-free, compressed** statistic is also a forensic witness to the same property. The answer from `exp95e` V1 is partial: K = 2 multi-compressor consensus closes the test on 8 short surahs (`total_letters_28 ≤ 188`) at recall ≥ 0.999 with FPR ≤ 0.025; per-surah τ recalibration (`exp95g`, pre-registered) tests whether closure extends to all 114 surahs."*

This paragraph removes any reading of the V1 falsification as "the project lost its forgery-detection capability". The deployable forensic detector is unconditionally available; F53 is a research finding about a stronger statistic.

This addition is **deferred** — final wording depends on what SHORT and the rescue experiment(s) eventually return. Locking the paragraph tonight would over-commit before evidence lands.

---

## 5. What this document does NOT do

- It does **not** un-retract R53 — the universal-extrapolation hypothesis under the locked `exp95c` τ stays falsified regardless of A / B / C outcomes.
- It does **not** launch any rescue experiment tonight — the SHORT replication owns the CPU until ~ 03:30, and choice of A / B / C / sequence depends on SHORT outcome.
- It does **not** add the edit-distance paragraph to `PAPER.md` tonight — wording depends on SHORT + first rescue experiment outcomes.
- It does **not** open new finding rows F55, F56, F57 — those are only earned by passing verdicts, not by registration.
- It does **not** weaken the F53 closure on Q:100 — `exp95c` stands at recall 1.000, FPR 0.0248, reproduced inside the V1 receipt.

---

## 6. Audit-trail requirements

When any of A / B / C is launched tomorrow:

1. The launching commit must reference this planning doc by file path and add a SHA-256 hash of this doc to the experiment's PREREG.md `parent_planning_hash` field.
2. The launching commit must also reference the SHORT-replication receipt (or its absence with explicit acknowledgement that the rescue experiment is being run blind to SHORT — undesirable but allowed if explicitly logged).
3. No new hypothesis number (H40 / H41 / H42) may be re-used for a re-formulation; if H40 (path A) is run and fails, a follow-up must be H43+ with a new pre-registration, not a re-fit of H40.

---

## 7. Frozen-time fingerprint

This document is **not** hash-locked because it is a planning sketch, not a pre-registration. The three sub-experiments' PREREG.md files (when written) will each carry their own SHA-256 lock. This document's role is to ensure the design space for tomorrow's choice is **already fixed tonight** — A / B / C are the only options that can be filed without further design work, and any path-D would require a fresh planning round.

*Authored 2026-04-26 ≈ 00:35, post-V1, pre-SHORT-completion. Cascade.*
