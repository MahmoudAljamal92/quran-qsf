# Adiyat and Authentication

**Date**: 2026-04-25 (updated late same day with Â§2.5)
**Scope**: Current single-entry document for the Adiyat case, canonical-reading detection, and forgery/authentication experiments.
**Status**: Consolidates `ADIYAT_CASE_SUMMARY.md`, `CANONICAL_READING_DETECTION_GUIDE.md`, Tier 3 audits, and later experiment receipts through `exp106` preregistration status.

> **READ THIS FIRST (banner, 2026-04-25 PM)** — Every Adiyat number below is computed against the **Hafs rasm only**. The framework can be re-run on Warsh / Qalun / Duri in â‰ˆ 15 minutes once the variant text files are placed in `data/corpora/ar/`. Until then, the 1-of-865 result and the 99.07 % R12 detection rate are *Hafs-specific authentication results*, not riwayat-invariant proofs. See Â§7 item 4.

---

## 1. The question

The Adiyat benchmark asks whether the canonical wording of Surah 100 verse 1 can be distinguished from plausible or mechanically generated alternatives.

Canonical text:

```text
ÙˆÙŽØ§Ù„Ù’Ø¹ÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ Ø¶ÙŽØ¨Ù’Ø­Ù‹Ø§
```

The benchmark has three levels:

1. **Classical hand-picked variants**
   - `Ø¹ -> Øº`
   - `Ø¶ -> Øµ`
   - both substitutions together

2. **Full single-letter enumeration**
   - 32 consonant positions Ã— 27 alternative Arabic consonants = 864 variants.
   - Canonical + 864 variants = 865 candidate texts.

3. **Harder / out-of-distribution attacks**
   - Multi-letter substitutions.
   - Insertions/deletions.
   - Cross-surah edits.
   - Whole-surah adversarial generation.
   - Riwayat/qira'at stability.

Only the first two levels are strongly solved in the current receipts.

---

## 2. Current headline answer

For the fixed Adiyat v1 benchmark, the canonical reading is identifiable.

| Test | Current result | Status |
|---|---:|---|
| 864 single-letter variants | R12 detects `99.07%` at the fixed control-calibrated threshold | Standing within benchmark |
| Two-letter sampled enumeration | R12/NCD compound detects `100%` of sampled two-letter variants | Standing, full-mode completeness still separate |
| Tier 3 local-window detector | Best AUC `1.000` at window `N=5` | Audit-verified |
| Tier 3 Bayesian fusion | Brier `0.000`, ECE `0.000` on the fixed benchmark | Audit-verified, saturated task |
| Tier 3 1-of-865 gate | Canonical rank `#1 of 865` on seeds 42-46 | Audit-verified |

Safe wording:

> On the fixed Adiyat 864-variant benchmark, the canonical reading ranks first under the audited authentication gate, and single-letter variants are detected at `99.07%` by R12 under the fixed calibration. This is a benchmark-specific authentication result, not a universal proof against every possible forgery.

---

## 2.5 Updates from the 2026-04-25 paradigm-stage closures

This section was added 2026-04-25 PM after the X3 / X6 / A10 / X7 closures landed. It contextualises the Adiyat result in the broader 2026-04-25 evidence stack without modifying any number above.

### 2.5.1 The Adiyat surah does not sit alone

- **A10 (`expE17b_mushaf_j1_1m_perms`)** — the canonical Mushaf ordering of the 114 surahs is a strict Jâ‚-smoothness extremum: 0 of 10â¶ random permutations beat it; q < 10â»â¶. So *Surah 100's position in the canonical ordering* is itself part of a 1-in-a-million-strict global structure. Any single-letter Adiyat edit is sub-dominant to this large-scale optimum.
- **X6 GIT theorem** — Adiyat's Î¦_M = 10.286 sits inside a population of 68 Band-A surahs whose joint geometric / information-theoretic / topological signature rejects the secular-Arabic null at Brown-corrected p â‰ˆ 2.9 Ã— 10â»Â¹Â³ (~7Ïƒ) vs 3 722 multi-tradition controls.
- **X3 prose-extremum** — joint AR(1) + Hurst + spectral-flatness + variance-floor 4-witness Brown p = 6.7 Ã— 10â»Â³â´.

*Net*: the 1-of-865 Adiyat gate is one card in a six-card joint hand; even if any single card were weakened, the joint statement survives by orders of magnitude.

### 2.5.2 T_alt context (X7 / P2_OP2)

`T_alt` (CamelTools-free, verse-final transition feature) is **+1.33Ïƒ stronger than `T_canon`** at Band-A (locked 2026-04-25). Because the 864-Adiyat enumeration already saturates R12 detection at 99.07 % and the gate already ranks #1/865 on five seeds, T_alt does not increase Adiyat *recall* (no headroom). What it does change is the **posterior P(canonical | observations)** under the KDE-NB Bayesian fusion (Tier 3 E12), which tightens monotonically. A T_alt re-run of `exp43_adiyat_864_compound` is â‰¤ 5 minutes once the Â§4.4 canonical decision is made (Option A keeps T_canon primary; Option B promotes T_alt). See `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md Â§4.4`.

### 2.5.3 Universal-forgery-score (UFS / exp106) — execute next

`exp106` is currently a preregistration without a result folder. It is the single open authentication-tier task. The minimum viable implementation is:

```
UFS(T) := Stouffer-or-Brown( p_EL(T), p_NCD(T), p_PhiM(T) )
```

where each `p_X(T)` is the right-tail probability under the calibrated control null for that detector. Adiyat 864 + the two-letter 72 900 enumeration are both already-computed inputs. Estimated effort: 1–2 days. Until executed, **UFS is a specification, not a result.**

### 2.5.4 Architectural blind spot for /Ø¹â†”Ø¡/ class — production patch deferred (B14b)

The 2026-04-24 audit (`AUDIT_MEMO_2026-04-24.md` Finding 1 + `B14_PATCH_PLAN.md`) showed that channels B (root-bigram) and G (root-trigram) of the 9-channel forensic stack are **architecturally hamza-blind** under the current `_FOLD_MAP` normaliser. The MVP B14 patch (audit-block additions to `exp46`/`exp50`) is in place; the production B14b (re-train channels B+G on the hamza-preserving alphabet, re-run `exp46`/`exp50`) is 1–2 weeks of work and is logged as the next Adiyat-stack code-only upgrade.

### 2.5.5 Riwayat invariance — the highest-leverage outstanding test

Moved out of Â§7 to flag importance: this is the single highest-leverage outstanding test for the entire authentication framework. 15-minute compute, blocked only on the Warsh / Qalun / Duri raw-text files being placed in `data/corpora/ar/`. Once data lands, every Adiyat claim above upgrades from "Hafs-specific" to "Uthmanic-skeleton-level" with no human re-derivation.

---

## 3. What each detector contributes

| Detector / layer | Contribution | Limitation |
|---|---|---|
| `Phi_M` 5-D Mahalanobis | Confirms corpus-level Quranic outlier status | Structurally blind to most internal single-letter edits |
| `(T, EL)` / `L_TEL` | Strong document-level classifier | Also mostly invariant under tiny internal edits |
| R12 gzip-NCD | Main single-letter edit detector | Compressor-specific; not a universal Kolmogorov constant |
| Local-window channels | Saturate on Adiyat v1 at small windows | Benchmark-specific; needs harder OOD tasks |
| Bayesian fusion / gate | Gives a single rank/posterior-style authentication score | Perfect calibration is partly because the task is separable |
| UFS | Preregistered unified future score | Not executed yet; no result folder |

---

## 4. Solved vs unsolved

### Solved within the current benchmark

- **Classical variants**: the hand-picked `Ø¹ -> Øº`, `Ø¶ -> Øµ`, and double substitution are detected by R12.
- **864 single-letter enumeration**: R12 detects `856 / 864`, or `99.07%`.
- **1-of-865 authentication**: Tier 3 E13 ranks the canonical text first out of all 865 candidates on five seeds.
- **Local-window detectability**: Tier 3 E11 shows simple channels reach `AUC = 1.000` at `N=5` on this benchmark.

### Not solved yet

- **Out-of-distribution attacks**: insertion/deletion, phrase replacement, cross-surah edits, whole-surah generation.
- **General forgery resistance**: no claim that all intelligent Arabic forgeries fail.
- **Riwayat/qira'at invariance**: variant-reading files are not yet incorporated.
- **Universal scripture transfer**: raw EL does not generalize across scriptures; cross-language authentication needs language-normalized features.
- **UFS validation**: `exp106_universal_forgery_score` is preregistered but has no result folder.

---

## 5. Updated status of the attempted Adiyat upgrades

| Experiment | Intended role | Actual current status | Consequence |
|---|---|---|---|
| `exp95_phonetic_modulation` | Close low-phonetic-distance / emphatic blind spot with distance-stratified thresholds | `FAIL_ctrl_stratum_overfpr` | Do not claim it solved the phonetic blind spot. It failed the control-stratum false-positive requirement. |
| `exp105_harakat_restoration` | Add a harakat-restoration channel, R13, to recover variants missed by R12 | `PARTIAL_null_saturated` | R13 recall is low and the union with R12 does not improve R12's `99.07%` recall. |
| `exp106_universal_forgery_score` | Define one scalar UFS combining EL and NCD p-values | Preregistered only; no result folder | UFS is a specification, not a validated result. |
| Tier 3 E10 | Optimal composite detector | `NULL_NO_GAIN` | Single channels already saturate on Adiyat v1, so composite gain cannot be measured there. |
| Tier 3 E11 | Local-window amplification | `LOCAL_AMPLIFICATION` | Strong benchmark result: `AUC = 1.000` at `N=5`. |
| Tier 3 E12 | Bayesian fusion | `BAYES_CALIBRATED` | Calibration works on the fixed benchmark, but posteriors saturate. |
| Tier 3 E13 | 1-of-865 authentication gate | `GATE_SOLID` | Best current one-number Adiyat result. |

---

## 6. The phonetic/emphatic blind spot

The project has two facts that must be kept separate:

1. **Random or mechanically enumerated Adiyat edits are mostly detected.**
   - R12 detects `99.07%` of the 864 single-letter variants.
   - Local-window features saturate on the fixed benchmark.

2. **Phonetically minimal emphatic-class substitutions remain hard.**
   - `exp46` showed the 9-channel detector has very low detection on Quran emphatic-class edits.
   - `exp50` showed this low rate is Quran-specific relative to poetry controls.
   - `exp95` did not safely fix the issue because the stratified control FPR exceeded the preregistered requirement.
   - `exp105` did not add useful recall over R12.

Safe wording:

> The Quran appears unusually hard to perturb with phonetically minimal substitutions, and the current detector stack has not yet closed that blind spot. This is an open authentication problem, not a solved one.

---

## 7. Recommended next Adiyat experiments

1. **Execute `exp106` UFS**
   - Treat UFS as a practical scoring rule.
   - Do not frame it as universal until tested.
   - Include lessons from `exp95` and `exp105`.

2. **OOD edit suite**
   - Insertions.
   - Deletions.
   - Multi-letter substitutions beyond sampled two-letter pairs.
   - Cross-surah substitutions.
   - Edits designed to preserve EL and local NCD.

3. **Hard phonetic suite**
   - Focus on `tta/ta`, `qaf/kaf`, and other low-distance substitutions.
   - Require per-stratum FPR control before claiming improvement.

4. **Riwayat invariance** â† *highest-leverage outstanding test (see Â§2.5.5)*
   - Add Warsh, Qalun, and Duri files to `data/corpora/ar/` if available.
   - Re-run the frozen 5-D pipeline + `exp43_adiyat_864_compound` + `expE13_auth_gate` against each riwaya.
   - Pre-registered acceptance: |Î”(EL, VL_CV, CN, H_cond, T)| â‰¤ 0.02 across riwayat â†’ claim upgrades from Hafs-specific to Uthmanic-skeleton-level.
   - Estimated compute: ~15 minutes once data lands.

5. **Whole-surah adversarial generation**
   - Requires Arabic LLM/API or local model.
   - Must be separated from single-letter detection claims.

---

## 8. File map

| File | Use |
|---|---|
| `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` | Current Adiyat/authentication entry point. |
| `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` | Older concise summary; should point here after update. |
| `docs/reference/adiyat/ADIYAT_AR.md` | Arabic/plain-language summary; should point here after update. |
| `docs/reference/adiyat/CANONICAL_READING_DETECTION_GUIDE.md` | Non-specialist guide; should point here for current experiment statuses. |
| `results/experiments/expE13_auth_gate/` | Tier 3 1-of-865 gate receipt. |
| `results/experiments/exp95_phonetic_modulation/` | Failed phonetic modulation receipt. |
| `results/experiments/exp105_harakat_restoration/` | Partial harakat restoration receipt. |
| `experiments/exp106_universal_forgery_score/PREREG.md` | UFS preregistration/specification. |

---

## 9. Safe short summary

> The Adiyat case is solved at paper-grade for the fixed 864 single-letter benchmark and the 1-of-865 authentication gate: the canonical reading ranks first, and R12 detects `99.07%` of single-letter variants. It is not yet solved for out-of-distribution forgeries, riwayat stability, whole-surah generation, or phonetically minimal substitutions. `exp95` and `exp105` were honest attempted upgrades, but neither currently closes the remaining blind spot; `exp106` UFS remains preregistered and unexecuted.

## 10. Cross-references

- `docs/MASTER_02_AUTHENTICATION.md` — top-of-document navigation for everything authentication-related.
- `docs/_INDEX_CARD.md` — one-card project overview.
- `docs/reference/sprints/AUDIT_MEMO_2026-04-24.md` — 2026-04-24 patch audit (Finding 1 = E7 confound; Finding 4 = `_el_match` Arabic-letter fix).
- `docs/reference/sprints/B14_PATCH_PLAN.md` — hamza-preserving normalizer patch plan.
- `docs/reference/prereg/PREREG_GAMMA_KOLMOGOROV.md` — Î³-Kolmogorov preregistration ledger and UFS spec.
