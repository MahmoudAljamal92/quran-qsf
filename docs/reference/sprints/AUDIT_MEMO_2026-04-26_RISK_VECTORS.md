# Audit Memo — 2026-04-26 (night) — Three Risk Vectors

**Status**: 3 of 3 risk vectors verified against existing retractions registry. 1 new minor finding (hypothesis-ID collision). All standing claims in `RANKED_FINDINGS.md`, `PAPER.md`, and `results/integrity/results_lock.json` survive.

**Scope**: Cross-check of older experiments against the three risk vectors raised pre-`exp95e` to ensure no surviving claim depends on a now-falsified premise.

**Companion document**: `AUDIT_MEMO_2026-04-24.md` (E7 fold + checkpoint drift + exp48 `_el_match` patches). This memo extends but does not supersede that one.

---

## TL;DR — three sentences

1. **Risk vector 1 (γ universality)** is closed by `exp103_cross_compressor_gamma` verdict `FAIL_not_universal` (CV_γ = 2.95; γ_gzip = +0.072, γ_bzip2 = −0.048, γ_zstd = −0.029, γ_brotli = +0.087); γ is now a **gzip-family-specific empirical scalar**, not an information-theoretic constant candidate. **No older experiment cites γ as universal that is not already retracted (R34 covers L6 γ(Ω)).**
2. **Risk vector 2 (cross-tradition uniqueness)** is closed by `R09` (R3 cross-scripture path-minimality is shared Abrahamic, not Quran-unique), `R48` (%T_pos cross-tradition fails under language-agnostic T_lang), and the `expX1_psi_oral` falsification (Ψ_oral 5/6 universality is a Quran n=1 numerical coincidence). **All three retractions are documented; no older experiment still claims cross-tradition Quran-uniqueness on a non-Arabic feature space.**
3. **Risk vector 3 (T² band-A vs full)** is closed by `R50` (bootstrap CI of full-Quran T² is `[3 127, 4 313]`, median 3 693, **includes** the band-A locked T² = 3 557; reframed `INCREASES → STABLE`). **No older experiment depends on the now-retracted "T² increases when band gate is removed" framing.**

---

## Findings table

| # | Risk vector | Status | Anchor experiment | Existing retraction(s) | New action required |
|---|---|---|---|---|---|
| 1 | **γ universality across compressor families** | **CLOSED — already retracted** | `exp103_cross_compressor_gamma` (`FAIL_not_universal`, CV_γ = 2.95) | R34 (L6 γ(Ω) slope NULL); programme-level decision in `exp103/run.py` | Add R51 to registry to make the γ-universality retraction citable as a primary entry, not just a side effect of R34. |
| 2 | **Cross-tradition Quran-uniqueness on non-Arabic feature spaces** | **CLOSED — already retracted** | `expP4_*` family + `expX1_psi_oral` + `expP8_T_pos_cross_tradition` | R09, R26, R48; `CROSS_TRADITION_FINDINGS_2026-04-25.md` §§3.1–5 | Tighten language in `RANKED_FINDINGS.md` and `PAPER.md` to explicitly scope all surviving Quran-vs-* claims to **Quran-vs-Arabic-peers**. |
| 3 | **Full-Quran T² ≈ 3 685 read as "stronger than" band-A T² = 3 557** | **CLOSED — reframed STABLE** | `expP12_bootstrap_t2_ci` (`STABLE`, CI `[3 127, 4 313]` includes band-A) | R50 | None — already reframed. |
| 4 | **NEW: hypothesis-ID collision H35** | **OPEN (cosmetic, no numerical impact)** | `exp103` (2026-04-22) labelled H35 = γ universality; `exp95c/d` (2026-04-26) re-used H35 = multi-compressor consensus; `HYPOTHESES_AND_TESTS.md` row 39 promotes the **later** definition as canonical. | none yet — discovered this audit | Relabel `exp103` PREREG/run.py header from H35 → **H35a** (γ-universality variant) or add an explicit collision note in `HYPOTHESES_AND_TESTS.md`. Cosmetic only — neither verdict changes. |
| 5 | **Audit hygiene: F53 unaffected by RV1** | **VERIFIED** | `exp95c/d/e` use `{gzip, bz2, lzma, zstd}` consensus | n/a | F53's design treats compressor *diversity* as a feature, not an assumption of γ-sign agreement. The bz2 and zstd γ signs being *opposite* to gzip's is **why K = 2 consensus works**: artefacts of one algorithm are washed out by the others. exp103's `FAIL_not_universal` is therefore consistent with — and arguably explains — exp95c's `PASS_consensus_100`. |

---

## 1. Risk vector 1 — γ universality

### 1.1 What was at risk

`exp41_gzip_formalised` reported γ_gzip = +0.0716 (95 % CI [+0.066, +0.078]) as the length-controlled "Quran indicator" in the log-linear NCD regression. Pre-`exp103`, two interpretations were live:
- **(a)** γ is a gzip-specific empirical scalar (safe; matches other compressor-calibrated quantities).
- **(b)** γ is a universal information-theoretic constant predicted by an underlying Kolmogorov-complexity argument (this is the path that would justify "Theorem 1" of `docs/PREREG_GAMMA_KOLMOGOROV.md`).

Older experiments that cite γ — `exp41`, `exp43_adiyat_864_compound`, `exp45_two_letter_746k`, `exp55_gamma_length_stratified`, `exp94_adiyat_864`, `expB5_gamma_scope_audit` — all use γ_gzip as a **gzip-specific** scalar. None implicitly upgrade it to interpretation (b).

### 1.2 What `exp103` actually found

```
gzip   γ = +0.07161   CI [+0.0657, +0.0775]
bzip2  γ = −0.04827   CI [−0.0532, −0.0433]
zstd   γ = −0.02942   CI [−0.0493, −0.0096]
brotli γ = +0.08710   CI [+0.0646, +0.1096]

CV_γ = 2.95   →   FAIL_not_universal (gate was CV ≤ 0.10)
```

All four CIs exclude zero, meaning each compressor produces a **statistically significant Quran indicator**, but **the sign disagrees**. Interpretation (b) is dead: γ is not invariant across the compressor population. Interpretation (a) survives — γ_gzip = +0.0716 remains a reproducible, length-controlled, gzip-family-specific scalar.

### 1.3 What this means for older experiments

| Experiment | Cites γ? | Risk under exp103 verdict | Action |
|---|---|---|---|
| `exp41_gzip_formalised` | yes (origin) | none — already gzip-scoped | none |
| `exp43_adiyat_864_compound` | yes (gzip ctrl-p95) | none — gzip-scoped | none |
| `exp45_two_letter_746k` | yes (gzip ctrl-p95) | none — gzip-scoped | none |
| `exp55_gamma_length_stratified` | yes (decile sign-test on γ_gzip) | none — already verdict `LENGTH_DRIVEN` (already disclosed) | none |
| `exp94_adiyat_864` | yes (gzip ctrl baseline 0.990741) | none — gzip-scoped | none |
| `expB5_gamma_scope_audit` | yes (γ-scope audit) | none — already a scope-audit experiment | none |
| `exp95c/d/e` (F53 family) | uses `{gzip, bz2, lzma, zstd}` consensus | none — F53 *predicts* compressor disagreement; consensus is the design response | none |
| **PAPER.md §4.41 / §5.5** | cites γ_gzip = +0.0716 | none — already labelled "compressor-calibrated edit-detection parameter" since patch F | none |

**Net**: zero downstream impact. The γ retraction is **already complete in spirit** (R34 covers L6 γ(Ω); the `exp103` decision section says explicitly "γ = +0.0716 survives as a gzip-specific reproducible empirical scalar only"). The only loose end is the **registry**: there is no R-number for this retraction. This memo recommends adding **R51**.

### 1.4 Recommended R51 entry

```markdown
| R51 | "γ is a universal information-theoretic constant across compressor families"
     | **FALSIFIED** (`FAIL_not_universal`, CV_γ = 2.95). γ_gzip = +0.072 and γ_brotli = +0.087 are
     positive; γ_bzip2 = −0.048 and γ_zstd = −0.029 are negative; signs disagree. **Preserved**:
     γ_gzip = +0.0716 as a length-controlled gzip-family-specific edit-detection scalar.
     **Killed**: the Kolmogorov-derivation programme (`PREREG_GAMMA_KOLMOGOROV.md` Theorem 1).
     | `exp103_cross_compressor_gamma.json` | 2026-04-22 (v7.8) | exp103 programme_decision field |
```

---

## 2. Risk vector 2 — cross-tradition Quran-uniqueness

### 2.1 What was at risk

Three old framings could have read as cross-tradition Quran-uniqueness in ways the data refuses to support:
- **(α)** "R3 path-minimality is Quran-strongest" — would have read as a cross-scripture universal beaten only by Quran.
- **(β)** "%T_pos = 397× ratio is universal across oral-canon traditions" — would have read as a multilingual T-feature property.
- **(γ)** "Ψ_oral = 0.836 is a 5/6 oral-tradition universal" — would have read as the Quran being one of many oral-canonical texts in a band.

### 2.2 Status of each

| Framing | Status | Evidence | Retraction |
|---|---|---|---|
| (α) R3 cross-scripture | **already FALSIFIED v7.2** — Tanakh z = −15.29 and NT z = −12.06 both exceed Quran z = −8.92 in raw form | `exp35_R3_cross_scripture_redo.json`; `expP4_cross_tradition_R3.json` | **R09** |
| (β) %T_pos | **already FALSIFIED v7.9-cand patch B** — under language-agnostic T_lang, Hebrew Tanakh + Greek NT + Pali_MN exceed Quran %T_pos = 6.45 % | `expP8_T_pos_cross_tradition.json` (`FAIL_QURAN_NOT_HIGHEST`) | **R48** |
| (γ) Ψ_oral | **already FALSIFIED 2026-04-25 evening** — 0/5 non-Quran oral corpora yield Ψ in `[0.65, 1.00]`; cross-corpus Ψ is dominated by per-language stop-set choice | `expX1_psi_oral.json` + `CROSS_TRADITION_FINDINGS_2026-04-25.md` §5 | **registered in CROSS_TRADITION_FINDINGS** as `NO_SUPPORT`, not yet given an R-number |

Additional cross-tradition results that **do not** flatter the Quran (already documented but worth re-citing in this audit):
- Hurst forensics: Rigveda z = +7.87, Hebrew z = +6.50 **both exceed** Quran z = +3.70 on permutation null (`expP4_quran_hurst_forensics.json`).
- Diacritic-channel R: Rigveda Devanagari R_prim = 0.918 is **above** the Abrahamic [0.55, 0.70] band, not below it.

### 2.3 Older experiments that touch RV2

| Experiment | Implicit cross-tradition claim? | Status |
|---|---|---|
| `exp35_R3_cross_scripture_redo` | yes — refuted (R09) | safe — verdict already published |
| `exp90_cross_language_el` | yes — `FAIL_no_convergence` (Hebrew, Greek, Arabic_bible all cluster with secular Arabic) | safe — verdict already published |
| `exp97_crosscripture_t8` | exists but has **no surviving cross-tradition uniqueness claim** | safe |
| `expP4_*` family (5 expts) | each correctly scoped to per-tradition pre-registered hypotheses | safe |
| `expP14_cross_script_dominant_letter` | dominant-letter analysis only, scope-correct | safe |
| `expX1_psi_oral` | falsified Ψ_oral 5/6 universality | safe |

**Net**: every older experiment touching cross-tradition territory is either already retracted (R09, R48) or correctly scoped pre-publication. **However**: the `RANKED_FINDINGS.md` Tier-A and Tier-B rows currently use language like *"Quran's EL elevation is Arabic-specific, not a scripture-class property"* in some places but slip into unscoped *"Quran shows the largest..."* phrasing in others. **Recommended action**: a one-pass tightening of `RANKED_FINDINGS.md` and `PAPER.md` headline language to use **"Quran vs Arabic peers"** as the explicit scope on every surviving comparison. This is Action 2 in this memo's action plan; no numerical change is required.

### 2.4 Recommended R52 entry (Ψ_oral)

```markdown
| R52 | Ψ_oral = H(d|b) / (2·I(EL;CN)) ≈ 0.836 as a 5/6 oral-tradition universal
     | **FALSIFIED** (n=1 numerical coincidence). 0/5 non-Quran oral-liturgical corpora produce
     Ψ in the loose pre-registered band [0.65, 1.00]; spread is two orders of magnitude wide
     (0.000 Avestan → 25.94 Hebrew). Cross-corpus value is dominated by per-language stop-set
     choice, not by structural information-theoretic content. **Preserved**: Quran Ψ_oral = 0.836
     as a within-corpus T7 derived constant; reproduces locked value to drift 3×10⁻⁵.
     **Killed**: the "Class-2 Law-Closure 1–2 year" timeline that depended on Ψ_oral as a
     cross-tradition universal.
     | `expX1_psi_oral.json` | 2026-04-25 (cross-tradition sprint) | `CROSS_TRADITION_FINDINGS_2026-04-25.md` §5 |
```

---

## 3. Risk vector 3 — T² band-A vs full

### 3.1 What was at risk

v7.9-cand patch B framing characterised the full-Quran T² = 3 685 as "HIGHER than" band-A T² = 3 557, suggesting that removing the band gate **strengthens** the multivariate separation. If this framing were right, downstream papers would have to choose between two T² values; if wrong, the choice doesn't matter and both can be cited as "T² ≈ 3 600".

### 3.2 What `expP12_bootstrap_t2_ci` actually found

```
point_estimate_T2     : 3 670.05
locked_band_A_T2      : 3 557.34   ← inside CI
locked_full_T2        : 3 685.45   ← inside CI
bootstrap_median      : 3 692.88
bootstrap_CI_2.5/97.5 : [3 127.19, 4 313.14]
bias_mean_minus_point : +30.51
verdict               : STABLE
```

Both locked T² values sit inside the 95 % bootstrap CI. The "increase" was bootstrap noise. This is correctly retracted as **R50**.

### 3.3 Older experiments that touch RV3

| Experiment | Cites T²? | Risk | Action |
|---|---|---|---|
| `exp49_6d_hotelling` | yes (6-D Hotelling T²) | none — independently scoped | none |
| `exp53_ar1_6d_gate` | yes (gate test) | none | none |
| `exp66_extended_mahalanobis` | yes (extended T²) | none | none |
| `expP7_phi_m_full_quran` | yes (point estimate 3 685.45) | none — labelled `point estimate` already | none |
| `expP12_bootstrap_t2_ci` | retraction-source | n/a | none |
| **PAPER.md §4.4 + §4.41** | cite both T² values | already reframed STABLE | none |

**Net**: zero downstream impact. RV3 is fully closed by R50.

---

## 4. New finding — hypothesis-ID collision H35

`HYPOTHESES_AND_TESTS.md` row 39 defines H35 as the **`exp95c` multi-compressor consensus** hypothesis. `exp103_cross_compressor_gamma` was authored 4 days earlier and also tagged its hypothesis as **H35** (γ universality across compressors). The two H35s are different claims with different verdicts:

```
H35 (exp103, 2026-04-22, registry-stale) = γ universality        → FAIL_not_universal
H35 (exp95c, 2026-04-26, registry-current) = K=2 consensus on Q:100 → PASS_consensus_100
H36 (exp95d, 2026-04-26)                  = K=2 robustness         → PARTIAL_seed_only
H37 (exp95e, 2026-04-26)                  = K=2 universal scaling  → PENDING
```

This is a **cosmetic ID-reuse**, not a numerical issue. Both H35 verdicts are correctly logged in their own receipts, and the canonical registry tracks the later-authored one. Recommended fix: relabel `exp103` PREREG and run.py header text from H35 → **H35a (γ-universality variant)**, and add an explicit collision note to `HYPOTHESES_AND_TESTS.md` near row 39. Optional — zero numerical impact, preserves audit-trail clarity.

---

## 5. F53 family is unaffected by all three risk vectors

It is worth stating this explicitly because the F53 closure (`exp95c/d/e`) is the **next headline-grade result** under v7.9-cand patch G:

- **RV1 (γ universality)**: F53 *uses* compressor disagreement as a feature, not an assumption. The K = 2 rule fires when ≥ 2 of `{gzip, bz2, lzma, zstd}` flag a variant; if all four agreed perfectly, K = 2 would carry no extra information vs gzip-only. exp103's `FAIL_not_universal` (signs disagree across {gzip, bz2, zstd, brotli}) is exactly the regime F53 is designed for.
- **RV2 (cross-tradition uniqueness)**: F53 makes **no** cross-tradition claim. Its scope is "Quran single-letter consonant edits, K = 2 consensus, 4 compressors". `exp95e` extends it to all 114 surahs *of the Quran*. Cross-tradition F53 is a separate future experiment (proposed H38 below) gated on acquiring native peer corpora.
- **RV3 (T² band-A vs full)**: F53 does not use T². The τ thresholds are independent ctrl-p95 quantiles per compressor, calibrated on the same Arabic-only ctrl pool exp94 used.

**F53 is safe to publish under the v7.9-cand patch G headline once `exp95e` produces a `PASS_universal_999` or `PASS_universal_100` verdict.**

---

## 6. Action items (this memo only)

These are the audit-induced edits. They are independent of the broader 5-action plan that follows the audit (`Action 1` paper sharpening, `Action 2` ranked findings, etc.).

1. **Add R51 (γ universality) and R52 (Ψ_oral) to `RETRACTIONS_REGISTRY.md`**. Both retractions exist in their experiment receipts but lack a registry R-number. R51 and R52 are the recommended IDs above.
2. **Relabel `exp103` hypothesis ID** from H35 → H35a in `experiments/exp103_cross_compressor_gamma/PREREG.md` line 4, `run.py` line 4 + line 432, and add a one-line note to `HYPOTHESES_AND_TESTS.md` near row 39 documenting the historical reuse. Cosmetic.
3. **Add F53-unaffected statement** to `RANKED_FINDINGS.md` row 53 footnote so future readers don't confuse exp103's `FAIL_not_universal` with F53's PASS.
4. *(No numerical re-runs required.)* Every existing receipt is correct as-published; the audit confirms no claim depends on a now-falsified premise.

---

## 7. What this memo does NOT do

- It does **not** re-open any retraction. R09, R34, R48, R50 stand as written.
- It does **not** modify any frozen result JSON. Receipts are append-only.
- It does **not** claim the audit is exhaustive across the 100+ experiment folders. It is targeted at the **three risk vectors raised in the v7.9-cand patch G discussion** — γ universality, cross-tradition uniqueness, T² band-A vs full. A full-corpus zero-trust audit was last run 2026-04-24 (`AUDIT_MEMO_2026-04-24.md`) and found 5 issues (E7 fold, checkpoint drift, exp48 `_el_match`, exp48 control pool, in-sample SVM) — all of which are independent of the three risk vectors covered here.
- It does **not** preempt the cross-tradition F53 experiment. `exp95e` is the universal-scaling-within-Quran result; cross-tradition F53 (H38, future) is gated on acquiring native peer corpora and is **not** part of the v7.9-cand patch G headline.

---

*Authored 2026-04-26 night, immediately before the user begins running `exp95e_full_114_consensus_universal --scope v1`. Frozen at this hash for audit-trail purposes; subsequent updates append below as `## 8. Update YYYY-MM-DD` blocks rather than rewriting the body.*

---

## 8. Update — 2026-04-26 night (post-V1)

The V1-scope run of `exp95e_full_114_consensus_universal` completed in 54.8 min on 6 workers and **fired the pre-registered verdict-ladder branch 4: `FAIL_per_surah_floor`**. Headline numbers (V1 scope, 139,266 variants):

- Aggregate K = 2 = **0.190** (target ≥ 0.999); K = 1 = 0.269; K = 3 = 0.114; K = 4 = 0.000.
- Per-surah K = 2: **8 / 114 surahs at K = 2 ≥ 0.999** (Q:093, Q:100, Q:101, Q:102, Q:103, Q:104, Q:108, Q:112 — all short late-Meccan, `total_letters_28 ≤ 188`); 36 / 114 in (0, 0.999); **70 / 114 at K = 2 = 0** (all long surahs, `total_letters_28 ≥ 873`).
- ctrl-null FPR K = 2 = **0.0248** (≤ 0.05 ✓ — the consensus rule itself is well-behaved against the null pool).
- Embedded Q:100 regression sub-run: K = 2 = **1.000**, gzip-solo = **0.9907** — matches `exp94` and `exp95c` exactly (no τ-drift, no Q:100-drift). **F53's Q:100 closure is therefore reproduced inside the V1 receipt**.
- bz2-solo recall = **0.000 across all 114 surahs** (τ_bz2 inherited from `exp95c` is too strict to fire on V1 variants under this corpus while still false-positing at the locked-τ rate of 0.0503; K = 2 unaffected because it requires only any 2 of {gzip, bz2, lzma, zstd} to agree).

### 8.1 Relationship to the three risk vectors covered by §1–§3

The V1 falsification is **independent** of RV1 / RV2 / RV3:

- **RV1 (γ universality across compressors)**: not engaged. The `FAIL_per_surah_floor` branch fired on per-surah K = 2 recall, not on any γ-universality assumption. F53's K = 2 rule remains designed for compressor disagreement; γ-sign mismatch is exactly what makes K = 2 useful, but here the failure mode is *non-detection* (lzma / zstd / bz2 all silent on long surahs) rather than *disagreement*.
- **RV2 (cross-tradition uniqueness)**: not engaged. The V1 scope is restricted to the Hafs ʿan ʿĀṣim Quran corpus; no cross-tradition claim is made or attempted.
- **RV3 (T² band-A vs full)**: not engaged. F53 does not use Hotelling T².

### 8.2 What changed between this audit memo and the post-V1 record

| Item | Pre-V1 (this memo §1–§7) | Post-V1 |
|---|---|---|
| F54 row of `RANKED_FINDINGS.md` | PENDING | **❌ FALSIFIED** with full V1 numbers |
| R53 retraction | not yet recorded | **Added to Category L of `RETRACTIONS_REGISTRY.md`** — universal-extrapolation hypothesis revoked; F53 Q:100 closure unaffected |
| F53 row footnote (`RANKED_FINDINGS.md` row 53) | "Path to widening: F54 below scales to 114 surahs" | "Path to widening: F54 fired `FAIL_per_surah_floor`; F53 universality retracted as R53; F53 Q:100 closure unaffected" |
| `PAPER.md §4.43` | PENDING block | Verdict-anchored block + §4.43.0 mechanistic envelope as observation only |
| H39 envelope replication | not yet pre-registered | **Pre-registered at `experiments/exp95f_short_envelope_replication/PREREG.md`** (SHA-256 `83a7b25ac69e703604a82be5c6f7c1d597ccd953f07df7f624ccc1c55d972a14`); SHORT-scope re-run launched and in flight |
| Total retractions | 52 (R01–R52) | **53** (R01–R53) |

### 8.3 Mechanistic envelope (post-hoc observation, NOT a finding)

Across all 114 surahs in the V1 receipt:

- `log10(total_letters_28) → per-surah K = 2 recall` Pearson r = **−0.85** (Spearman ρ = −0.85).
- `v1_letters_28 / total_letters_28 → per-surah K = 2 recall` Pearson r = **+0.83**.
- Phase boundary: **all 8** K = 2-perfect surahs satisfy `total_letters_28 ≤ 188`; **all 70** K = 2-zero surahs satisfy `total_letters_28 ≥ 873`. The middling 36 surahs occupy `92 ≤ total_letters_28 ≤ 2 065`.

Because this pattern was discovered on the V1 receipt, it is reported **as an observation, not a finding**, in `PAPER.md §4.43.0` and the F54 row footnote. The pre-registered envelope test (H39) is filed at `experiments/exp95f_short_envelope_replication/PREREG.md` and replicates the analysis on the SHORT-scope receipt produced by `python -m experiments.exp95e_full_114_consensus_universal.run --scope short --workers 6` (in flight, ETA ~ 2–4 h, ≈ 355 K variants). The H39 verdict ladder requires (i) Pearson `r(log10 total_letters, K = 2) ≤ −0.70` AND (ii) `K = 2 ≥ 0.90` for all surahs with `total ≤ 188` AND `K = 2 ≤ 0.10` for all surahs with `total ≥ 873`. If both hold, the envelope is promoted to candidate finding F55 in `RANKED_FINDINGS.md`; if either fails, the V1 envelope stays as a single-corpus exploratory pattern only.

### 8.4 What this update does NOT do

- It does **not** re-open R51 or R52 — those are unchanged and unrelated to the post-V1 result.
- It does **not** re-open any retraction R01–R50 — R53 is a new retraction, not a re-litigation.
- It does **not** modify the §4.42 F53 closure of Adiyat-864 — F53 stands at Q:100 K=2 = 1.000 with gzip-solo = 0.9907, reproduced inside the V1 receipt.
- It does **not** invent a post-hoc replacement hypothesis: the envelope claim is filed as a *separate* pre-registered hypothesis (H39) with locked decision rules **before** the SHORT receipt is opened.

*Update authored 2026-04-26 night, immediately after the V1 receipt landed. Frozen at this update's hash; further updates (e.g. when the SHORT receipt lands) will append as `## 9. Update YYYY-MM-DD` blocks rather than rewriting §8.*

---

## 9. Update — 2026-04-26 night (post-V1-iii: rescue paths B + C executed)

After §8 was authored, the user instructed Cascade to execute rescue paths B and C from `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` to determine whether the universal-coverage *question* (which F54 falsified for NCD-consensus extrapolation) is rescuable under any non-NCD detector class. Three pre-registered experiments were executed in this round.

### 9.1 Path B (asymmetric length-band detector, H41) — FAIL_no_clean_split_p90

`exp95h_asymmetric_detector` ran a 108-rule grid `{K1, K2, K3, K4} × {gzip, bz2, lzma, zstd}` solo combinations partitioned at any L0 against the V1 receipt. Best rule (`L0=138`, `D_short=K2`, `D_long=gzip_or_lzma`) achieves `min_per_surah_recall = 0.0000` and aggregate = 0.270; `n_below_0.99 = 89 / 114`. **Documented negative result**: no length-band split of the locked-τ NCD detectors rescues universal detection. This confirms that the F54 falsification cannot be rescued by recombining the NCD primitives at any partition.

### 9.2 Path C-calibrated (bigram-shift, calibrated τ, H42) — FAIL_audit_hook_violated

`exp95i_bigram_shift_detector` (PREREG hash `9a67de356aff74aef306d38b2e6df829943a1472e7b544345814b4887b03e53c`) introduced a non-NCD symbolic statistic `Δ_bigram(canon, candidate) = ‖hist_2(canon) − hist_2(candidate)‖₁ / 2` with τ calibrated as the 5th percentile of length-matched ctrl-Δ distribution (`[0.5n, 1.5n]` window, K_PEERS=50). The pre-registered audit hook required at least one length-matched ctrl peer per surah; Q:108 (62 letters) has zero peers in the `[31, 93]` length-match window in `phase_06_phi_m`, so the audit fired with verdict `FAIL_audit_hook_violated`.

**Substantive numbers** (had the audit not blocked): variant Δ ∈ [1.0, 2.0] across all 139,266 V1 variants; length-matched peer Δ ≥ 58.5 across all 5,589 matched pairs. Implied verdict (not pre-registered): aggregate recall = 1.000, aggregate FPR ≤ 0.05 by τ-calibration construction. The audit hook is honoured per pre-registration; the design space pivots to path C-strict.

### 9.3 Path C-strict (bigram-shift, frozen-τ analytic-bound, H43) — PASS_universal_perfect_recall_zero_fpr

`exp95j_bigram_shift_universal` (PREREG hash `a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd`) replaces τ-calibration with a **frozen** τ = 2.0 motivated by an analytic theorem.

**Theorem 4.43.2** (`PAPER.md §4.43.2`). For any string `c` of length `n ≥ 2` and any single-character substitution at position `p` producing `v`, `Δ_bigram(c, v) ≤ 2`, with equality only at interior positions in the absence of bigram aliasing. Proof in PAPER §4.43.2.

**Headline result** (frozen-τ run, no calibration data used): aggregate recall = **1.000** (139,266 / 139,266 V1 variants fire); per-surah recall = 1.000 on every one of 114 surahs; aggregate FPR = **0.000** across 548,796 (canon, peer) pairs in the full non-Quran peer pool; per-surah FPR = 0.000 on every surah; min peer Δ across the entire 548,796-pair pool = **73.5** (≫ τ = 2.0); audit hook `max_variant_delta ≤ 2.0` holds with equality (theorem confirmed empirically). Wall-time: 311 s on 1 core (analytic-shortcut variant Δ + cached peer bigram counters).

**F55 added** to `RANKED_FINDINGS.md` (row 55, strength 86 %, paper-grade, status `✅ PROVED (universal, theorem + empirical FPR=0)`). **§4.43.2 added** to `PAPER.md` with full theorem statement + proof + headline-result table + what-this-is/is-not framing + relationship to F53/F54/R53 + predecessor record.

### 9.4 Relationship to risk vectors A1–A3 and to R51–R53

The path-C-strict PASS is **independent** of the three risk vectors covered by §§A1–A3:

- **RV1 (γ universality across compressors)**: not engaged. F55 uses no compressor; the bigram-shift statistic is purely symbolic.
- **RV2 (cross-tradition uniqueness)**: not engaged. F55's empirical FPR = 0.000 is for Quran-vs-Arabic-peers in `phase_06_phi_m` only. Cross-tradition replication is logged as future work (H44 stub) and would need a fresh PREREG. The theorem (max Δ_bigram = 2 for 1-letter sub) is universal in mathematics, but the *empirical FPR* claim is corpus-bound.
- **RV3 (T² band-A vs full)**: not engaged. F55 does not use Hotelling T².

**F55 does NOT un-retract R53**: R53 retracted the *NCD-consensus* extrapolation (under fixed locked-τ); F55 is a fundamentally different detector class. R51, R52 are unrelated and unchanged. R01–R50 are unrelated.

### 9.5 What this update does NOT do

- Does **not** re-open or modify any existing retraction or finding.
- Does **not** modify the §4.42 F53 closure of Adiyat-864 (still K=2 = 1.000 / gzip-solo = 0.9907 on Q:100).
- Does **not** un-retract R53 or modify the R53 entry.
- Does **not** affect the H39 envelope replication SHORT-scope run (still in flight).
- Does **not** invent a post-hoc replacement hypothesis: F55 was pre-registered with hash-locked PREREG (`a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd`) **before** any frozen-τ scoring on V1 was performed.

*Update §9 authored 2026-04-26 night, immediately after the path C-strict receipt (`exp95j`) landed. Frozen at this update's hash; further updates will append as `## 10. Update YYYY-MM-DD` blocks rather than rewriting §9.*
