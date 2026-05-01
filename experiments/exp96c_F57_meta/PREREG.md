# PREREG — exp96c_F57_meta (H51)

**Hypothesis ID**: H51
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Pre-registered before any meta-finding score is reported.**

**Scope directive**: Whole 114-surah Quran. No band gates. The
6-corpus Arabic null pool is the reference null distribution for
"random Arabic corpus would satisfy each claim."

---

## 1. Background

The Quran makes **six specific, independently falsifiable, structural
claims about itself**. The QSF project has by 2026-04-27 morning
operationalised three of them (54:17, 2:23, 15:9), partially
operationalised one (41:42), and left two untested (11:1, 39:23).
The 2026-04-27 afternoon feedback observed: **the *self-describing
accuracy* of the text is itself a measurable, computable, and
falsifiable property** — and it has never been formally pre-
registered as a meta-finding.

This PREREG locks the meta-finding's definition, the per-claim test,
the null distribution, and the verdict ladder *before* the three
remaining experiments (`exp97`, `exp98`, `exp99`) are run. The
**partial F57 score** (currently 3 of 6 fully confirmed, 1 partial,
2 pending) is **reported here as a status snapshot**; the full F57
verdict is **deferred to a single recomputation after Phase 2** —
this PREREG is the lock that prevents post-hoc test-set selection.

---

## 2. The six claims and their tests

| Claim | Verse | Op-test | Pass criterion | Receipt |
|---|---|---|---|---|
| **C1** memory-optimised | Q 54:17 | LC2 path-minimality across λ-grid | Quran median L-rank ≤ 5th percentile in ≥ 3 of 5 λ values | `expE16_lc2_signature` |
| **C2** Tahaddi (bring like it) | Q 2:23, 10:38, 17:88 | Universal 1-letter detector at frozen τ = 2.0 (F55) | Recall = 1.000 on all 114 surahs AND FPR = 0.000 vs full Arabic peer pool | `exp95j_bigram_shift_universal` |
| **C3** preserved | Q 15:9 | 5-riwayat invariance | min AUC ≥ 0.95 across {Hafs, Warsh, Qalun, Duri, Shuba, Sousi} | `expP15_riwayat_invariance` |
| **C4** verses made precise | Q 11:1 | Per-verse MDL via multi-compressor min | Quran median MDL/length is rank 1 (lowest) of 7 Arabic corpora | `exp98_per_verse_mdl` (PENDING) |
| **C5** self-similar (mutashābih) | Q 39:23 | Multifractal singularity spectrum width Δα | Δα(Quran) is rank 1 (smallest = most monofractal) of 7 corpora | `exp97_multifractal_spectrum` (PENDING) |
| **C6** falsehood cannot approach | Q 41:42 | Joint adversarial robustness over 10⁶ EL+rhyme+root-aware Markov-3 forgeries | 0 of 10⁶ forgeries pass Gate 1 ∧ F55 ∧ F56 simultaneously | `exp99_adversarial_complexity` (PENDING) |

---

## 3. Hypothesis (H51)

**H51** (one-sided, hash-locked).

Define `S_obs = #{i ∈ {C1,…,C6} : claim i passes its op-test}`.

Under the **independent-claim null hypothesis** that a random
Arabic-corpus author writing 6 self-description claims has
independent probability `p_pass = 1/7` of matching each test
(Quran is rank 1 of 7 corpora by chance for each claim), we have

```
S_null ~ Binomial(n=6, p=1/7)
P_null(S_obs ≥ s) = sum_{k=s}^{6} C(6,k) (1/7)^k (6/7)^(6-k)
```

**H51 PASS criterion**: `S_obs ≥ 4` AND `P_null(S_obs ≥ 4) < 0.05`,
i.e. at least 4 of the 6 self-descriptions are independently
confirmed under the project's pre-registered tests.

**H51 STRICT criterion**: `S_obs ≥ 5`, with `P_null(≥ 5) ≈ 0.000306`.

**H51 EXTREMUM criterion**: `S_obs = 6`, with
`P_null(= 6) = (1/7)^6 ≈ 8.5 · 10⁻⁶`.

The naive `p_pass = 1/7` null is the *most permissive* honest null:
each claim is treated as independent, and the per-claim pass
probability under "random Arabic corpus" is taken as 1 / number of
corpora in the pool. The actual null is likely much smaller because
(i) C2's pass is theorem-grade and would not occur for any random
control (FPR_actual ≈ 0 on 548,796 peer pairs), and (ii) C3's pass
has no analogue in any control corpus (no other tested corpus has
5 transmission chains).

---

## 4. Frozen constants

```python
N_CLAIMS         = 6
PASS_PROB_NULL   = 1.0 / 7.0   # naive null: 1 of 7 Arabic corpora
H51_PASS_FLOOR   = 4           # S_obs >= 4 -> H51 PASS
H51_STRICT_FLOOR = 5           # S_obs >= 5 -> H51 STRICT
H51_EXTREMUM     = 6           # S_obs = 6  -> H51 EXTREMUM

# Source receipt hashes for the 3 currently-completed claims
EXPE16_HASH_REF  = "expE16_lc2_signature/expE16_report.json"   # has its own seed/lock; no PREREG hash field
EXP95J_HASH_REF  = "a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd"
EXPP15_HASH_REF  = "16f4f0ff0d9a3e6137628ab3801855a172eda02bac9cf351219d2dc03186da87"

# Pending experiment IDs (Phase 2)
EXP97_ID = "exp97_multifractal_spectrum"
EXP98_ID = "exp98_per_verse_mdl"
EXP99_ID = "exp99_adversarial_complexity"
```

---

## 5. Audit hooks (block PASS if any fire)

1. **A1** All 3 currently-completed source receipts exist and are loadable.
2. **A2** `expE16_lc2_signature` reports `WEAK_LC2` or `LC2_SIGNATURE` verdict (i.e. C1 PASSES).
3. **A3** `exp95j_bigram_shift_universal` reports `PASS_universal_perfect_recall_zero_fpr` (i.e. C2 PASSES).
4. **A4** `expP15_riwayat_invariance` reports min AUC across riwayat ≥ 0.95 (i.e. C3 PASSES).
5. **A5** `exp97`, `exp98`, `exp99` receipts EITHER (a) all exist with passing verdicts (full F57 score) OR (b) the pending count is correctly reported as `pending = 3` and partial score is computed honestly with `S_obs ∈ {0, 1, 2, 3}` from the completed tests only.

---

## 6. Verdict ladder (strict order)

1. `FAIL_audit_<hook>` — any audit hook fired.
2. `PARTIAL_pending_<n>` — `n` of 6 claims pending (Phase 2 not yet run); partial S_obs reported, full verdict deferred.
3. `FAIL_S_obs_below_floor` — All 6 claims tested AND `S_obs < 4`.
4. `PASS_F57_meta_finding` — All 6 tested AND `S_obs ≥ 4` AND `P_null(≥ S_obs) < 0.05`.
5. `PASS_F57_strict` — All 6 tested AND `S_obs ≥ 5`.
6. `PASS_F57_extremum` — All 6 tested AND `S_obs = 6`.

`PASS_F57_meta_finding` (or stricter) is the only outcome that
supports adding **F57 — Quran self-description meta-finding** to
`RANKED_FINDINGS.md`.

---

## 7. What this PREREG does NOT claim

- Does **not** un-retract any prior retraction (R01–R56 stand).
- Does **not** assert F57 today; the partial report is `PARTIAL_pending_3`.
- Does **not** treat C4/C5/C6 outcomes as known — they are committed to be re-evaluated against this PREREG only after their respective experiment receipts exist.
- Does **not** make a metaphysical claim of any kind. The meta-finding measures *self-description accuracy*, which is a **stylometric-self-reference** property, not a divinity claim.

---

## 8. Outputs

- `results/experiments/exp96c_F57_meta/exp96c_F57_meta.json` — receipt with per-claim pass status, S_obs (currently 3 of 6 completed; full S_obs after Phase 2), null-binomial p, audit hooks, verdict.
- This PREREG hash logged in receipt as `prereg_hash_actual`.
