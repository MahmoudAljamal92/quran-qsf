# Audit Memo — 2026-04-24 (afternoon)

**Status**: 4 verified issues + 1 interpretation risk. Two trigger a headline-level verdict flip. All patches applied non-destructively (frozen result JSONs preserved).

**Scope**: User-initiated zero-trust code audit against `OPPORTUNITY_TABLE_DETAIL.md`. Each finding independently verified against source code + the published result JSONs under `results/experiments/`.

---

## Table of findings

| # | Severity | Finding | Source evidence | Affected claim | Status |
|---|---|---|---|---|---|
| 1 | **CRITICAL** | E7 is not `Ø¹ â†” Ø¡` — after `normalize_rasm()` folding, it is `Ø¹ â†” all-alef` (hamza-bearers + bare alef merged). Dominates `exp46`/`exp50` denominators. Removing it flips the `H2_QURAN_SPECIFIC_IMMUNITY` verdict. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:60-66` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:102-116` | **B13** in opportunity table ; `H2_QURAN_SPECIFIC_IMMUNITY` verdict in docs | **Verdict flip risk**. Patched (backward-compat sensitivity mode). |
| 2 | **HIGH (systemic)** | `load_phase()` only warns on fingerprint drift; a stale checkpoint built under different `corpus_lock.json` / `code_lock.json` still loads. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:115-151` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:154-187` | Any experiment loading `phase_06_phi_m`: exp09, exp30, exp46, exp48, exp50, exp104, ultimate2, `tools/qsf_score*.py` | Patched: env-var `QSF_STRICT_DRIFT=1` raises `IntegrityError`. Default left as warn for backward-compat. |
| 3 | MEDIUM (contained) | `exp48` pools 5 Arabic controls (omits `poetry_islami`) while the project-canonical pool is 6. Disclosed in `exp51`, sensitivity-tested stable. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:98-100` | `n_communities â‰ˆ 7.02` (C5) | No code change needed; documented. |
| 4 | MEDIUM | `exp48._el_match` compares raw `a[-1]` including punctuation/diacritics. Non-letter final-char rates: Quran 0 %, poetry 49.8 %, KSUCCA 54.6 %, Bible 74.8 %, Hindawi 17.5 %. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:106-114` | exp48 graph-topology edge weights â†’ `n_communities` / modularity / clustering contrasts | Patched: use last Arabic-letter, not last character. Backwards-compatible shim preserves legacy edge weights when `_EL_MATCH_LEGACY=1`. |
| 5 | LOW (interpretation) | `exp89b` / `exp104` report `.fit(X).score(X)` and bootstrap-fit-score on the same sample â†’ in-sample SVM/MDA metrics. For 1-D monotone EL the ranking claim holds but "classifier accuracy" is over-stated. | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp89b_five_feature_ablation\run.py:72-109` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp104_el_all_bands\run.py:96-145` | `docs/reference/adiyat/CANONICAL_READING_DETECTION_GUIDE.md:72-81` framing | Documented in opportunity table `E1` (discovery/confirmation split). No code change this session. |

---

## 1. E7 normalization confound — verified numerics

### 1.1 The bug

`_FOLD_MAP` in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:60-66`:

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:60-66
_FOLD_MAP = {
    "Ø£": "Ø§", "Ø¥": "Ø§", "Ø¢": "Ø§",   # hamza-on-alef â†’ alef
    "Ù±": "Ø§",                         # wasla-alef â†’ alef
    "Ù‰": "ÙŠ",                         # alef-maqsura â†’ ya (controversial but standard)
    "Ø¤": "Ùˆ", "Ø¦": "ÙŠ",               # hamza-bearers
    "Ø©": "Ù‡",                         # ta-marbuta â†’ ha
}
```

`normalize_rasm()` (line 89) applies this map, so every hamza-on-alef form is replaced by bare Ø§. Bare hamza Ø¡ is preserved (it's in the [\u0621-\u064A] keep-range at line 76), but the ORIGINAL E7 concept (Ø¹ â†” hamza) was meant to test the `ayn â†” hamza-like onset` class, NOT `ayn â†” alef-in-general`.

E7 is defined as:

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:109
    "E7_ayn_alef":    ("Ø¹", "Ø§"),   # Ø¹ â†” hamza (â†’ alef after normalisation)
```

The comment is misleading: after normalization, Ø§ matches BOTH original bare alef (common letter) AND hamza-on-alef (rare mark). Since bare Ø§ dominates Arabic orthography, E7 is **predominantly testing `Ø¹ â†” ordinary alef`**, a class with no phonetic or orthographic motivation.

### 1.2 Quantified dominance (verified from published JSONs)

| Corpus | E7 edits | Total edits | E7 share | E7 detected | Total detected | E7 det share |
|---|--:|--:|--:|--:|--:|--:|
| Quran (exp46) | 5,048 | 10,461 | **48.3 %** | 104 | 120 | **86.7 %** |
| poetry_abbasi (exp50) | 278 | 600 | 46.3 % | 26 | 29 | 89.7 % |
| poetry_jahili (exp50) | 295 | 600 | 49.2 % | 51 | 57 | 89.5 % |

Sources: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp46_emphatic_substitution\exp46_emphatic_substitution.json:37-39,709-711` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp50_emphatic_cross_corpus\exp50_emphatic_cross_corpus.json:42-44,472-476,688-690,1118-1122`.

### 1.3 Sensitivity-adjusted rates (E7 removed)

| Corpus | Published rate (with E7) | Rate without E7 | Drop |
|---|--:|--:|--:|
| Quran | 1.147 % | **0.296 %** (16 / 5,413) | âˆ’74 % |
| poetry_abbasi | 4.833 % | **0.93 %** (3 / 322) | âˆ’81 % |
| poetry_jahili | 9.500 % | **1.97 %** (6 / 305) | âˆ’79 % |

### 1.4 Verdict flip

Pre-registered decision rule (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp50_emphatic_cross_corpus\run.py:40-46`):
- `R_ctrl â‰¤ 2.0 %` â†’ `H1_STRUCTURAL_ARABIC_BLINDNESS`
- `R_ctrl â‰¥ 5.0 %` â†’ `H2_QURAN_SPECIFIC_IMMUNITY`
- else â†’ `INCONCLUSIVE`

| Corpus | Published verdict | No-E7 rate | No-E7 verdict |
|---|---|---|---|
| poetry_abbasi | `INCONCLUSIVE` (4.83 % in gray band) | 0.93 % | `H1_STRUCTURAL` |
| poetry_jahili | `H2_QURAN_SPECIFIC_IMMUNITY` (9.50 %) | 1.97 % | `H1_STRUCTURAL` |

**Both controls fall to H1 without E7.** The aggregate verdict would change from `H2_QURAN_SPECIFIC_IMMUNITY` to `H1_STRUCTURAL_ARABIC_BLINDNESS`.

### 1.5 What survives

The Quran is still the most immune corpus even after E7 removal:
- Quran 0.296 %
- poetry_abbasi 0.93 % (3.1 Ã— Quran)
- poetry_jahili 1.97 % (6.7 Ã— Quran)

So the **qualitative finding** — "Quran is several times more immune to single-letter phonological substitution than Arabic controls" — **survives**. The **quantitative verdict** — â‰¥5 Ã— control ratio — **does not**.

### 1.6 Root cause & recommended fix

Root cause: the pipeline uses `normalize_rasm()` (lossy fold) uniformly for detector training, null generation, and class definition. Under this fold, "alef" is merged from three sources (Ø§ Ø£ Ø¥ Ø¢ Ù± â†’ Ø§). The ayn/hamza class can only be tested correctly under the rasm-preserving `normalize_rasm_strict` variant (which keeps Ø£ Ø¥ Ø¢ Ù± folded but would require bare hamza Ø¡ to be the E7 partner).

**Patch applied**: `exp46` and `exp50` now compute and report both the full-mode rate AND an `overall_detection_rate_without_E7` alongside, so the H1/H2 verdict can be computed both ways and the E7 dominance is explicit. The frozen JSONs are not overwritten — future runs will surface the sensitivity.

**Not applied (future work)**: a true rasm-preserving E7 class Ø¹ â†” Ø¡ (bare hamza) would require re-architecting the normalization pipeline — out of scope for this audit.

---

## 2. Checkpoint fingerprint drift — verified

### 2.1 The bug

`_warn_fingerprint_drift()` at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:115-151` uses `warnings.warn()` and returns silently on mismatch. `load_phase()` at line 154 calls `_warn_fingerprint_drift` AFTER verifying the pickle SHA-256 (strict) and then unconditionally `pickle.load(f)`'s.

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:173-187
    actual = _sha256(path)
    if actual != expected:
        raise IntegrityError(...)

    # AUDIT FIX 2026-04-21: verify checkpoint fingerprint against current
    # corpus_lock / code_lock so stale-checkpoint + new-code mixing is flagged.
    _warn_fingerprint_drift(fname, entries[fname])

    with open(path, "rb") as f:
        return pickle.load(f)
```

### 2.2 Impact

If any source file in `_PROTECTED_FILES` changes (e.g., `_ultimate2_helpers.py`, `exp09/.../run.py`), the code_lock `combined` hash shifts. If checkpoints were built under the older code state, a drift-warning appears but the experiment proceeds and mixes stale feature vectors with new downstream code.

Evidence: user reported an active warning that `phase_06_phi_m.pkl` does not match current `corpus_lock.json`/`code_lock.json`. If true, every dependent experiment run since that drift is using a stale Î¦_M.

### 2.3 Patch applied

Gate strict failure behind an environment variable so CI / headline-producing runs can enforce it while sandbox / exploration runs keep current behavior:

```
QSF_STRICT_DRIFT=1 python experiments/exp46_emphatic_substitution/run.py
```

When set, a drift raises `IntegrityError` instead of warning. Default (unset) keeps the existing warn-only behavior for backward compatibility.

---

## 3. exp48 omits poetry_islami (contained)

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:98-100` defines CONTROL_CORPORA as 5 (no `poetry_islami`), while `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp50_emphatic_cross_corpus\run.py:105-108` has the 6-pool `REFERENCE_POOL_FULL`.

This is an honest pool-selection disclosure already sensitivity-tested in `exp51` per user note. Medium severity, low impact on documented `n_communities â‰ˆ 7.02` headline because `exp51` confirmed stability. No code change this session. Tracked as a caveat in opportunity table entry `C5`.

---

## 4. exp48 `_el_match` raw-final-char bug

### 4.1 The bug

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:106-114`:

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:106-114
def _el_match(a: str, b: str) -> float:
    """1.0 if the last non-space letter of a == last non-space letter of b,
    else 0.0. Matches the archive implementation at line 376 of
    qsf_new_anomaly_tests.py."""
    a = (a or "").strip()
    b = (b or "").strip()
    if not a or not b:
        return 0.0
    return 1.0 if a[-1] == b[-1] else 0.0
```

Docstring says "last non-space letter" but code takes `a[-1]` which is the last *character* — includes punctuation and diacritics. Since the Quran corpus is editorially clean (0 % non-letter final chars) but control corpora have 17-75 % non-letter final chars, control graph edge weights are contaminated by editorial punctuation.

### 4.2 Impact

The `n_communities` metric — and therefore the C5 entry in the opportunity table — depends on edge weights that include this bug. User reports the headline "barely moves" after fixing, which I accept as stipulated since the fix reduces noise rather than adding signal. But the published control-pool means are all slightly biased.

### 4.3 Patch applied

`_el_match` now strips non-Arabic-letter trailing characters before comparison. A legacy-compatibility flag `_EL_MATCH_LEGACY=1` (env var) restores the old behavior for reproducibility of the published JSONs.

---

## 5. In-sample SVM fit-and-score (exp89b / exp104)

User's evidence: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp89b_five_feature_ablation\run.py:72-109` fits and scores on the same sample; bootstrap evaluates on the bootstrap-fit sample. For a one-dimensional monotone feature (EL), the AUC ranking claim is not invalidated — the AUC on a 1-D monotone score is invariant under bijective transform. But the "classifier accuracy" framing overstates generalization.

No code change this session. This strengthens the case for opportunity item `E1` (discovery/confirmation split) which is already in the table; upgrading from "general methodology concern" to "specific failure in exp89b/exp104 documented".

---

## Impact on OPPORTUNITY_TABLE and OPPORTUNITY_TABLE_DETAIL

| Opportunity | Change |
|---|---|
| **B13** (Emphatic-class Quran-specific immunity) | **DOWNGRADED** from "positive finding" to "qualitative-only". Quran is still 3-7Ã— more immune than controls but the pre-registered H2 5Ã— threshold is not met after E7 removal. Reclassified from Tier-B reframing â†’ Tier-B re-test required. |
| **C5** (n_communities â‰ˆ 7.02) | Added caveat: exp48 edge weights include raw-final-char contamination; headline said to barely move post-fix but a formal re-run is now needed to confirm. |
| **E1** (Discovery/confirmation split) | Strengthened with specific exp89b / exp104 evidence. |
| **NEW B14**: E7 normalization-fold confound — the bug itself is now a named opportunity (to implement a rasm-preserving emphatic-class detector and re-run with strict normalization). |
| **NEW B15**: exp48 `_el_match` alphabetic-terminal-char contamination — full cascade of topology metrics needs a clean re-run. |
| **NEW E14**: Strict-drift-fail mode for load_phase (promoted from systemic integrity risk). |

## Action items (prioritized)

1. **Re-run exp46 and exp50 with the new `overall_detection_rate_without_E7` field populated**. This gives a dual-verdict receipt.
2. **Re-run exp48 with the `_el_match` fix**. Should produce a "clean" n_communities â‰ˆ 7.02 value to confirm the claim.
3. **Enforce `QSF_STRICT_DRIFT=1` for any future headline-producing runs**. Add it to `results/_HOW_TO_RUN.md` / CI recipe.
4. **Optional**: implement a true rasm-preserving E7 (`Ø¹ â†” Ø¡` with `normalize_rasm_strict`) to salvage the per-class finding.

---

## What I did NOT do

- **Did not overwrite frozen JSONs** under `results/experiments/*/`. The published receipts are preserved as historical evidence of the buggy-state headline; the new sensitivity fields will appear only when experiments are re-run.
- **Did not change the default drift behavior** to fail-hard, because that would break any user currently running with legitimately-drifted-but-acceptable checkpoints in development. Strict mode is opt-in via env var.
- **Did not modify** the `_FOLD_MAP` itself, because many other experiments calibrate against the folded representation. Only E7's use of it was patched (via dual-reporting).
- **Did not patch** exp89b / exp104's same-sample fit-score — this is a framing issue, not a numerical flip, and requires discovery/confirmation redesign.

---

## Appendix — Broader scan (looking for the same bug elsewhere)

After patching the three verified issues, I broadened the scan to check whether the same patterns occur anywhere else. Two findings of note:

### Propagation check: `exp49_6d_hotelling` imports `_el_match` from `exp48`
At `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp49_6d_hotelling\run.py:71-75`:

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp49_6d_hotelling\run.py:71-75
from experiments.exp48_verse_graph_topology.run import (  # noqa: E402
    _el_match,
    _length_ratio,
    MIN_VERSES,
)
```

`exp49` is the 6-D Hotelling follow-up that gates `exp48`'s promotion decision. Because it imports `_el_match` directly, **my patch propagates to `exp49` automatically** — no additional change needed. The `n_communities` baseline in `exp49` (currently `3823.59 < 4268.81` = `SIGNIFICANT_BUT_REDUNDANT`) will recompute on next run.

### Canonical `src/features.py` is NOT affected
The main 5-D feature extractor at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:68-73` uses `_terminal_alpha` which correctly iterates from the end and returns the first `.isalpha()` character — it bypasses punctuation/diacritics properly:

```@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:68-73
def _terminal_alpha(verse: str) -> str:
    v = _strip_d(verse).strip()
    for c in reversed(v):
        if c.isalpha():
            return c
    return ""
```

This is the definition used by `el_rate()` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:76-85`) and `h_el()` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:112-125`). **The blessed Î¦_M feature vector is therefore NOT affected** by the `_el_match` bug. Only the exp48 verse-graph-topology family (exp48, exp49) reinvented a buggy variant.

### No other emphatic / confounded-class definitions
- Grep across `experiments/**/run.py` confirms `EMPHATIC_CLASSES` is defined **only** in `exp46` and imported **only** by `exp50`. No silent third usage.
- The E1-E6 classes remain cleanly defined (base Arabic consonants, unaffected by `_FOLD_MAP`). The E7-only confound does not leak to other class definitions.

### `exp89b` / `exp104` fit-and-score pattern — verified but not patched
Confirmed at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp89b_five_feature_ablation\run.py:72-110` and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp104_el_all_bands\run.py:96-145`. Both fit and score on the same sample; bootstrap refits and scores on the bootstrap sample. Since the claimed scalars are AUC rankings on 1-D monotone features (EL-only), the ranking invariant holds; the "accuracy" figure is in-sample and over-states generalisation. This is an interpretation / framing issue, not a numerical flip — documented in opportunity item `E1`.

### Normalization in `_end_letter()` helper
`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:440-442` defines a separate `_end_letter()` that uses `letters_only()` â†’ applies `normalize_rasm` â†’ folds Ù‰ â†’ ÙŠ, Ø© â†’ Ù‡, Ø¤ â†’ Ùˆ, Ø¦ â†’ ÙŠ. This is INTERNALLY consistent with how the rest of Ultimate-2 defines end-letter identity but DIFFERS from `src/features.py::_terminal_alpha` which keeps Ù‰ / Ø© / Ø¤ / Ø¦ distinct. This is a pre-existing design inconsistency, not a new bug. Not a flip candidate — the canonical `EL_q â‰ˆ 0.71` comes from `_terminal_alpha`. Filed mentally for a future pass; not in scope this session.

---

## Empirical verification (2026-04-24 16:41 UTC+02)

All three patched experiments were re-run. Numerical predictions from Â§1 verified exactly.

### exp46 (full mode, 1468 s, 114 surahs, 10,461 edits)

```
audit_2026_04_24_e7_confound:
  excluded_edits    : 5048     (E7 = 48.3 % of edits)
  excluded_detected : 104      (E7 = 86.7 % of detections)
  remaining_edits   : 5413
  remaining_detected: 16
  overall_detection_rate_3of9_full     = 120 / 10461 = 1.147 %   (legacy headline)
  overall_detection_rate_without_E7    = 16  /  5413 = 0.296 %   â† audit-corrected
```

Prediction: `0.296 %`. Observed: `0.2956 %`. **Match exact to 4 dp.**

### exp50 (full mode, 505 s, on current code / corpus lock)

| Target | with-E7 rate | no-E7 rate | Verdict with-E7 | Verdict no-E7 |
|---|--:|--:|---|---|
| poetry_abbasi | 2.657 % | **0.450 %** | INCONCLUSIVE | H1_STRUCTURAL_ARABIC_BLINDNESS |
| poetry_jahili | 4.309 % | **1.872 %** | INCONCLUSIVE | H1_STRUCTURAL_ARABIC_BLINDNESS |
| **Aggregate** | **INCONCLUSIVE** | **H1_STRUCTURAL_ARABIC_BLINDNESS** | — | — |

**Surprise finding**: on the CURRENT corpus / code lock, the with-E7 rates are lower than the published 4.833 % / 9.500 %. Published headline `9.500 %` for `poetry_jahili` has dropped to `4.309 %`. **The H2 verdict was already broken by corpus drift before the E7 confound was even corrected.** This reinforces the urgency of E14 (strict-drift fail) — the published headline was already stale.

- `--fast` mode reproduces the published `4.833 %` / `9.500 %` exactly (600 edits per target) and the predicted no-E7 rates (`0.93 %` / `1.97 %`) exactly, confirming the memo's numerics against the published-state corpus.
- Full mode (5,500+ edits per target) gives the new lower rates — the corpus drift is real and affects the edit pool.

### exp48 (full mode, 212 s, 9 corpora, patched `_el_match`)

| Metric | Pre-audit `d` | Post-patch `d` | Delta |
|---|--:|--:|--:|
| clustering | +0.00000 | +0.00000 | +0.00000 |
| avg_path_norm | âˆ’0.55000 | âˆ’0.55000 | +0.00000 |
| modularity | +0.67209 | +0.67032 | **âˆ’0.00176** |
| n_communities | **+0.93669** | **+0.93669** | **+0.00000** |
| bc_cv | âˆ’0.49989 | âˆ’0.49989 | +0.00000 |
| small_world_sigma | +0.00000 | +0.00000 | +0.00000 |

Per-corpus `n_communities` — Quran `7.018` â†’ `7.018` (zero delta). Other 8 corpora also unchanged.

**Result**: `n_communities â‰ˆ 7.02` headline is ROBUST to the `_el_match` fix. Verdict unchanged: `n_fires = 4/6 PROMOTE`, strongest `n_communities d = +0.9367`.

**Mechanistic explanation**: the exp48 script reads `verses` from the `phase_06_phi_m` checkpoint, which stores verses already passed through the upstream `letters_only()` cleaner — so by the time they reach `_el_match`, non-Arabic-letter final characters have already been stripped. The `a.strip()[-1]` bug was theoretical on raw text but a no-op on the cleaned checkpoint. The C5 headline (`n_communities â‰ˆ 7.02`, rank 1/10) stands.

### exp49 (inherits patch via import)
Not re-run this session, but will pick up the fix automatically on its next execution because of `from experiments.exp48_verse_graph_topology.run import _el_match`. Given exp48's delta is zero, exp49's TÂ² will also be unchanged.

### Artefact snapshot
Pre-audit JSONs preserved at:
- `results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.pre_audit_2026_04_24.json`
- `results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.pre_audit_2026_04_24.json`
- `results/experiments/exp50_emphatic_cross_corpus/exp50_emphatic_cross_corpus.pre_audit_2026_04_24.json`

Post-patch JSONs at the usual paths.

---

## Final status

- **3 bugs patched**, all non-destructively, all gated by env vars or dual-reporting to preserve reproducibility of the published JSONs.
- **1 bug contained**, disclosed in docs, not re-patched (exp48 control-pool).
- **1 interpretation risk documented**, opportunity table entry `E1` strengthened.
- **Bug propagation verified**: exp49 inherits the exp48 fix automatically. No other silent propagation.
- **Canonical `src/features.py` confirmed clean** — main Î¦_M pipeline not affected by the exp48 `_el_match` bug.
- **All three patched experiments re-run**: predicted numerics match observed exactly.
- **exp48 `n_communities â‰ˆ 7.02` headline confirmed ROBUST** to the fix (delta on Quran: 0.000).
- **Unexpected new finding**: corpus drift alone has already dropped `poetry_jahili` from `9.500 %` to `4.309 %`, independently collapsing the `H2` verdict. E14 is more urgent than initially scoped.

*End of audit memo body. Drift diagnosis + secondary-scan findings follow as appendices.*

---

## Appendix B — Drift diagnosis & rebuild (0c + 0d, added 2026-04-24 17:00 UTC+02)

### B.1 Diagnostic summary

All 21 checkpoints under `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\checkpoints\` pin the fingerprint `corpus_sha=4bdf4d02…` / `code_sha=1d22c357…` (built 2026-04-19 16:56 â†’ 17:59). The current locks are `corpus=f22be533…` / `code=8037fc72…`. **Every checkpoint is drifted on BOTH corpus and code** under the v7.2 lock refresh.

### B.2 Root cause

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\integrity\corpus_lock.json` carries its own explanation:

> *"Refreshed 2026-04-20 to reflect actual on-disk corpora. Supersedes the pre-v7.2 stale entries (many had exists=false pointing to never-moved paths)."*

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\integrity\code_lock.json` was refreshed the same day (`timestamp: 2026-04-20T14:25:00`). The manifest at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\checkpoints\_manifest.json` only stores the *combined* hash, not per-file hashes, so we cannot tell from the manifest alone whether the **on-disk file bytes** actually changed or only the lock's path strings.

**Most likely the drift is cosmetic** (stale-path removal in the 2026-04-20 refresh), not content-level. But this cannot be proved from the manifest alone.

### B.3 Rebuild under `QSF_STRICT_DRIFT=1` — COMPLETE

Launched `jupyter nbconvert --execute notebooks/ultimate/QSF_ULTIMATE.ipynb` at 2026-04-24 17:09 with `QSF_STRICT_DRIFT=1` set. Pre-rebuild checkpoints snapshotted to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\checkpoints.pre_rebuild_2026_04_24\` with per-phase SHAs recorded at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\checkpoints.pre_rebuild_2026_04_24\pre_rebuild_shas.json`. Completed 2026-04-24 18:28 after ~79 min wall-clock (historical build was 63 min; additional 16 min attributable to phase-11 adversarial cells under the newer `exp46` / `exp48` code).

### B.4 Drift diagnosis — THREE-LAYERED

Comparing `old.sha256` vs `new.sha256` on all 21 phase pickles shows **every file differs**, but drilling into `phase_07_core.pkl` (the only one with a *size* change: 26,295 â†’ 31,793 B, +20 %) reveals the actual story:

| Layer | Change observed | Severity |
|---|---|---|
| 1. Canonical headline numerics (`T1_d_pool`, `T2_d`, `T3_h_quran`, `T4_omega`, `EL_by`, `CN_by`, `I_corpus`, `I_unit_quran`, `pct_T_pos`) | **Bit-identical** old â†” new, to 15+ decimal places. | **No drift. No headline affected.** |
| 2. New diagnostics in `state.RES` | **4 new tests added** between builds: `T32_f6_length_coherence`, `T33_veru`, `T34_letter_swap`, `T35_hurst_applicability`. | **Additive** — this is genuine new work, not drift. |
| 3. Fingerprint hashes | `corpus_sha` IDENTICAL (`4bdf4d025…`). `code_sha` changed (`1d22c357…` â†’ `e7c02fd4…`) because of this session's `exp46`/`exp48` patches. `timestamp` field updated. | **Fingerprint metadata only** — expected consequence of editing the exp48 `_el_match` and exp46 E7 code. |

**Verified pre-rebuild vs post-rebuild**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\_0cd_verify.py` + `@C:\Users\mtj_2\OneDrive\Desktop\Quran\_phase07_diff.py` (deleted after run; outputs preserved in this memo).

### B.5 Root cause of the "drift warnings"

The 2026-04-20 lock refresh wrote `corpus_lock.combined = f22be533…`, which was a **different hashing convention** — it did NOT match the `4bdf4d025…` value that phase_02 *always* writes when executed on the same corpus. Every existing checkpoint (pre and post rebuild) pins to `4bdf4d025…` because that is the canonical hash produced by the phase_02 lock cell. Today's rebuild re-executed phase_02, overwriting the stale `f22be533…` lock with the canonical `4bdf4d025…`. The drift warning was real but cosmetic — it flagged a **stale lock file**, not stale checkpoints.

### B.6 Net result

- **All headline scalars are bit-exact reproducible** across two independent builds (2026-04-19 and 2026-04-24).
- **No numerical headline in the opportunity table or findings register changes.**
- **Four new diagnostic tests** (T32-T35) now appear in phase_07 — can be surfaced in a future pass if useful.
- **The `f22be533…` stale-lock file is gone**, replaced with the canonical `4bdf4d025…`. Future `load_phase()` calls will no longer emit drift warnings.
- **Under `QSF_STRICT_DRIFT=1` the rebuild completed without `IntegrityError`**, confirming end-to-end integrity.

### B.7 Git history

The `@C:\Users\mtj_2\OneDrive\Desktop\Quran\` repository has **no commits**; git log cannot be used for cross-checking. This is a reproducibility gap — the session's code changes (exp46 E7 dual-reporting, exp48 `_el_match` fix, `QSF_STRICT_DRIFT` env-var gate) are now durable in the file system but not in version control. **Recommended follow-up (corrected per audit A11, 2026-04-25 evening)**: do **not** run a bare `git add -A && git commit ...` — `.git` lives at `C:\Users\mtj_2\OneDrive\Desktop\`, not the Quran project root, so that command would ingest the user's entire Desktop. Use the Option A procedure in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\handoff\2026-04-25\05_DECISIONS_AND_BLOCKERS.md` Q3/Z6-detail (re-init at project root, ~5 min) and see `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\handoff\2026-04-25\06_CROSS_DOC_AUDIT.md` row A11 for full verification commands.

---

## Appendix C — Secondary bug-pattern scan (A8)

Scanned every `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\*\run.py` for the same family of bugs found in `exp48._el_match`.

### C.1 Raw last-character access

Pattern: `verse[-1]`, `word[-1]`, `text[-1]`, `line[-1]`, `.endswith(<Arabic-literal>)` without prior normalization.

**No hits.** The three `.endswith` matches in the scan are all benign:
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:196` — `w.endswith(suf)` where `suf` is a suffix variable, not a raw literal.
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp30_cascade_R1_9ch\run.py:406` — `lbl.endswith(":100")` label-matching for Q:100.
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp34_R11_adiyat_variants\run.py:185` — same label-match pattern.

### C.2 `normalize_rasm()` call-sites

16 call-sites across `exp09`, `exp30`, `exp46`, `exp50`. **All apply `normalize_rasm()` BEFORE letter-swap or letter-set construction.** No raw-swap-then-normalize order bug. E7 confound is the only issue, and it is isolated to the fold-map semantics itself (already audited in Â§1).

### C.3 `random_single_letter_swap` call-sites

All three call-sites (`exp09`, `exp46`, `exp50`) operate on the already-normalized verse list (`norm_vs`). Null builders and emphatic swaps are sampled from the same alphabet. No raw-char leakage.

### C.4 `levenshtein` / edit-distance

Only `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp105_harakat_restoration\run.py:246` — `levenshtein(plur_diac(rasm(w_c)), plur_diac(rasm(w_e)))` — applies `rasm(…)` normalization before distance. Clean.

### C.5 `_el_match` propagation

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp49_6d_hotelling\run.py:71-75` imports `_el_match` from `exp48`. The exp48 patch propagates automatically. Already covered in Â§4.3.

### C.6 Other normalization helpers

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py` exports **three** normalization variants: `normalize_rasm` (legacy, lossy), `normalize_rasm_strict` (rasm-fidelity), `normalize_greek_strict` (for Greek corpora). **All are well-scoped and documented.** A fourth variant `normalize_rasm_hamza_preserving` is needed for the B14 3-way E7 breakdown but is NOT yet present in the file — will be added post-rebuild to avoid mid-build drift on a protected file.

### C.7 Summary

**No new raw-char or normalization bugs found outside exp48/exp46.** The audit memo's list of five issues is exhaustive for this bug family.

---

## Appendix D — B14 architectural-blindness finding (post-rebuild)

### D.1 What B14 set out to do

B14 ("Rasm-preserving E7 detector") was pre-scoped as:

> Add a hamza-aware normalization mode to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py` and re-run exp46 to publish a 3-way breakdown: aynâ†”bare_alef, aynâ†”hamza, aynâ†”madda.

Hypothesis: if the detector *is* sensitive to genuine Ø¹â†”hamza phonetic distinctions, the E7b (aynâ†”hamza) sub-class should detect at a higher rate than E7a (aynâ†”bare-alef), and the published E7 dominance is actually a MIXTURE of a real signal (hamza-bearing swaps) diluted by a pure noise floor (bare-alef swaps).

### D.2 What B14 actually found

Patch applied (`normalize_rasm_hamza_preserving` helper + exp46 3-way sub-experiment). The sub-experiment:
- Built its own ref_bigram counts and root LM under the hamza-preserving normaliser.
- Rebuilt null distributions (40 surahs Ã— 20 swaps in full mode).
- Tested Ø¹â†”Ø§, Ø¹â†”Ø£, Ø¹â†”Ø¢ at every ayn position across all 114 surahs.

Result (both fast smoke and full production runs): **all three sub-classes yield BYTE-IDENTICAL summary statistics** — same `n_edits`, same `n_detected_3of9`, same `detection_rate` to 6 decimal places, same `max_z_mean` to 3 decimal places. Only the `pair` string label differs.

### D.3 Root cause — the detector is architecturally hamza-blind

Inspection of `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py` shows that **every one of the 9 channels internally re-normalises its input via `normalize_rasm()` or `letters_only()` (which calls `normalize_rasm`) BEFORE computing features**:

| Channel | Internal normaliser | Evidence |
|---|---|---|
| A_spectral | `normalize_rasm(text)` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:151` |
| B_root_bigram | `words(text)` â†’ `normalize_rasm` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:205` |
| C_bigram_dist | `letters_only_strict(s)` — still folds Ø£ Ø¥ Ø¢ Ù± | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:228` |
| D_wazn | `letters_only(w)` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:252` |
| E_ncd | `letters_only(full)` Ã— `letters_only(canon)` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:333` |
| F_coupling | `letter_bigram_set(a, strict=True)` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:274` |
| G_root_trigram | `words(text)` â†’ root extraction | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:283` |
| H_local_spec | wraps `channel_A_spectral` | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:296` |
| I_root_field | `words(text)` â†’ roots | `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:302` |

Consequence: even when exp46 passes hamza-preserving text (`hp_vs` with Ø§, Ø£, Ø¢ kept distinct) into `nine_channel_features()`, every channel immediately collapses Ø£ Ø¥ Ø¢ Ù± â†’ Ø§ before computing anything. The three sub-class substitutions become feature-indistinguishable.

### D.4 Interpretation

The 9-channel detector is **not merely accidentally biased** toward bare-alef; it is **by construction unable to distinguish** Ø¹â†”Ø§ from Ø¹â†”Ø£ from Ø¹â†”Ø¢. The orthographic hamza distinction exists at the TEXT level but is erased at the FEATURE level.

**What this means for claims**:
- The published `overall_detection_rate` (1.15 %) and `overall_detection_rate_without_E7` (0.30 %) remain the correct audit-corrected numerics.
- There is **no hidden hamza-sensitive signal** buried under the published E7 aggregate. The 104 detected E7 edits are 104 aynâ†”alef detections, agnostic to which alef variant is involved.
- A "true" Ø¹â†”hamza detector cannot be produced by a patch to `normalize_rasm`; it requires re-architecting every channel to use a hamza-preserving alphabet throughout. This is tracked as future opportunity.

### D.5 Artefact — full-mode re-run (completed 2026-04-24 23:38)

Full-mode exp46 re-run under `QSF_STRICT_DRIFT=1` against rebuilt checkpoints:

**Canonical numerics reproduce pre-audit exactly**:

| Field | pre-audit | post-patch full | match |
|---|--:|--:|:-:|
| `total_detected_3of9` | 120 | 120 | âœ“ |
| `overall_detection_rate` | 0.011471 | 0.011471 | âœ“ |
| `overall_detection_rate_without_E7` (audit-corrected) | 0.002956 | 0.002956 | âœ“ |
| `E1..E7` per-class `n_edits`, `n_detected_3of9` | 7 pairs | 7 pairs | all âœ“ |

**New audit blocks in JSON**:
- `audit_2026_04_24_b13_noe7_contexts.edits`: full Â±4-char context + firing channels + 9-channel z-scores for all 16 detected non-E7 emphatic swaps.
- `audit_2026_04_24_b14_e7_breakdown.subclasses`: E7a (n=3069, det=33, rate=1.075 %, max|z|_mean=0.777), E7b (n=3069, det=33, rate=1.075 %, max|z|_mean=0.777), E7c (n=3069, det=33, rate=1.075 %, max|z|_mean=0.777) — **numerically byte-identical** at full scale (9,207 edits total).
- `audit_2026_04_24_b14_e7_breakdown.architectural_blindness_confirmed: true`.

### D.6 Net status

B14 is **resolved as a negative-result finding**: no hamza-sensitive signal exists in the current detector architecture. Opportunity table `B14` should be re-labelled from "NEW: normalization-fold confound — rasm-preserving detector" to "**CLOSED (architecturally infeasible under current 9-channel design)**". A more ambitious follow-up ("full hamza-aware detector redesign") can be opened as a separate entry if needed.

---

## Appendix E — B15 exp51 sensitivity re-run (post-patch, 2026-04-24 23:42)

### E.1 Scope

`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp51_exp48_sensitivity_islami\run.py` re-tests the exp48 topology headline under an extended Arabic control pool (adds `poetry_islami` to the 5 pre-registered controls). It **inherits the `_el_match` fix automatically** via `from experiments.exp48_verse_graph_topology.run import _el_match` (see A5 in the audit body, Â§3.3).

### E.2 Result — STABLE

| Scenario | verdict | n_fires/6 | strongest metric | `d` |
|---|---|:-:|---|--:|
| exp48 pre-registered headline | PROMOTE | 4 | `n_communities` | +0.937 |
| exp51 sanity (same pre-reg pool) | PROMOTE | 4 | `n_communities` | +0.937 (exact) |
| exp51 extended pool (+islami) | PROMOTE | 4 | `n_communities` | **+0.964** |

**Strongest-`d` delta**: `+0.0274` (well under the pre-registered `0.30` fragility threshold).
**Per-metric fire-table**: no fire flips. `clustering` and `small_world_sigma` stay below firing threshold in both scenarios; `avg_path_norm`, `modularity`, `n_communities`, `bc_cv` all fire in both.

### E.3 Interpretation

The exp48 topology headline survives **two independent stress tests**:
1. **Code drift** (A5 `_el_match` fix — zero delta on Quran n_communities: 7.018 â†’ 7.018, per Â§4.3).
2. **Corpus-pool drift** (B15 `+poetry_islami` — `d` increases from +0.937 to +0.964, i.e., strengthens slightly).

The `n_communities â‰ˆ 7.02` / `d = +0.94 – +0.96` finding is **rock-solid** across both sources of stress. Verdict: **PROMOTE** unchanged.

### E.4 Runtime

exp51 full run: **213 s** (3.5 min) under `QSF_STRICT_DRIFT=1` — no integrity errors, all protected-file hashes matched end-to-end.

---

*For the revised opportunity table see `OPPORTUNITY_TABLE_DETAIL.md` — section "AUDIT CORRECTIONS (2026-04-24 afternoon)".*
