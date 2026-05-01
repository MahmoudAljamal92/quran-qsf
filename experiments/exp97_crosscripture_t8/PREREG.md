# exp97_crosscripture_t8 — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H34 — Cross-scripture canonical-path optimality is a **shared Abrahamic property**, not a Quran-specific fingerprint.
**Parent experiment**: `exp35_R3_cross_scripture_redo` (v7.2, 2026-04-20) — already executed with Quran z = −8.920, Tanakh z = −15.286, NT z = −12.063, Iliad z = +0.336.

## 1. Scope

This experiment is deliberately **thin**: a read-only wrapper over the `exp35` receipt. It does NOT re-execute the 5 000-permutation canonical-path test (that would be redundant and may drift the frozen v7.2 numbers).

**What this experiment adds**:
1. **A §4.37-shaped corpus-scale statistic sheet** — each scripture's `z_path`, empirical `p_one_sided`, and the BH-pooled `q_value` at `α = 0.05` — in a format the Fisher combiner of §4.37 can directly consume.
2. **An explicit Abrahamic-property verdict** — "three of three Abrahamic scriptures pass BH AND Iliad (negative control) fails BH" — which is what the Gem C entry of the opportunity scan actually claims. This verdict is derivable from `exp35` but never stated there.
3. **A machine-readable receipt** for downstream integration (§4.37 draft, `exp95`, any future adversarial-forgery test) that does not have to re-parse `exp35`'s schema.

## 2. Formula (pre-registered)

For each scripture `s ∈ {quran, hebrew_tanakh, greek_nt, iliad_greek}` read `z_s`, `p_s_one_sided`, and `n_perm` from the `exp35` receipt. Then:

```
p_corpus(s)  =  max(p_s_one_sided, 1 / (n_perm + 1))    # floor at the Monte-Carlo resolution
q_corpus(s)  =  BH-adjusted p_s across the four scriptures at alpha = 0.05
pass_BH(s)   =  (q_corpus(s) <= 0.05)
```

The §4.37 Fisher combiner consumes `p_corpus(quran)` as the **corpus-scale term**.

## 3. Evaluation protocol

**Step 1 — Read `exp35`**: load `results/experiments/exp35_R3_cross_scripture_redo/exp35_R3_cross_scripture_redo.json`. Verify `n_perm == 5000` and that all four scriptures are present. Cache the file's SHA-256 into the output JSON as `exp35_receipt_sha256` so any future drift is detectable.

**Step 2 — Floor the empirical p at the MC resolution**: the v7.2 receipt already reports `p = 0.0001999...` = `1/5001` for all three Abrahamic scriptures (i.e. zero permutations below canonical). We re-express this as `p_corpus = 1/(n_perm + 1)` per standard Monte-Carlo convention and log the floor source.

**Step 3 — Re-compute BH across the 4 p-values** using the same Benjamini-Hochberg adjuster as `exp35`. Sanity-check the BH-adjusted q-values against `exp35.BH_pooling.per_scripture` (should match within 1e-9).

**Step 4 — Emit `corpus_scale_evidence_sheet`** dict containing, for each scripture:
- `z_path`, `p_one_sided`, `p_corpus` (floored), `q_bh`, `pass_BH`, `cohort_label ∈ {abrahamic_scripture, secular_control}`, `n_units`, `alphabet`.

**Step 5 — Verdict dispatch** on the four cohort-labels.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_exp35_missing`                 | `exp35` receipt not on disk |
| `FAIL_exp35_schema_drift`            | `exp35` missing any of {quran, hebrew_tanakh, greek_nt, iliad_greek} or `n_perm != 5000` |
| `FAIL_bh_reproduction`               | re-computed BH q-values differ from `exp35.BH_pooling.per_scripture` by > 1e-9 |
| `FAIL_shared_abrahamic_property`     | any of Quran / Tanakh / NT does **not** pass BH, OR Iliad **does** pass BH |
| `PARTIAL_no_negative_control_separation` | Abrahamic three pass BH AND Iliad passes BH — canonical-path minimality is not scripture-specific at all (would break the Gem C claim) |
| `PASS_shared_abrahamic`              | Abrahamic three all pass BH AND Iliad fails BH (the expected and historically replicated structural outcome) |

## 5. Honesty clauses

- **HC1 — Legacy number mismatch**: the opportunity-scan rev-1 quoted `Tanakh z = −5.02` and `NT z = −4.97` from `D:\backup\Pipeline 2\qsf_breakthrough_results.json::test_b_cross_linguistic_t8`. The `exp35` v7.2 values are **stronger** (−15.286 and −12.063 respectively) because `exp35` uses Band-A language-agnostic 5-D features (EL, VL_CV, CN, H_cond_initials, T_lang), not the legacy v10.3c scoring that was used by the deleted `qsf_breakthrough_tests.py`. We **authoritatively cite the `exp35` numbers** going forward. The legacy numbers are preserved only for historical audit.
- **HC2 — Direction of the opportunity-scan correction**: the rev-1 scan said Gem C was "not executed in current pipeline". This is **wrong**; `exp35` executes the same test. Rev-2 of the scan corrects this. The present experiment (`exp97`) is therefore an adapter/repackager, not a re-execution.
- **HC3 — No claim of Quran specificity**: the Abrahamic-path-optimality result does NOT support a "Quran is unique" claim at the corpus scale. It supports a "canonical ordering of Abrahamic scripture optimises 5-D structural transitions, relative to a negative secular control (Iliad)" claim. This is actually the *correct* answer to the "Arabic-only?" reviewer objection on `exp90_cross_language_el` — the canonical-path property generalises; the EL-level property does not.
- **HC4 — Monte-Carlo floor**: Quran, Tanakh, NT all report `p_one_sided = 0.0001999600079984` which equals `1/5001`. This means ZERO of the 5 000 permutations came in below the canonical path. The true p is therefore `< 1/5001`; we report `1/5001` as the Monte-Carlo resolution floor, not the true p. Any stronger p-claim requires `n_perm ≥ 1e5`.

## 6. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. The `exp35` receipt is read-only; this experiment writes only to `results/experiments/exp97_crosscripture_t8/`.

## 7. Frozen constants

```python
SEED = 42
EXPECTED_SCRIPTURES = ["quran", "hebrew_tanakh", "greek_nt", "iliad_greek"]
ABRAHAMIC_COHORT = {"quran", "hebrew_tanakh", "greek_nt"}
SECULAR_COHORT = {"iliad_greek"}
EXPECTED_N_PERM = 5000
BH_ALPHA = 0.05
BH_REPRODUCTION_TOL = 1e-9
```

## 8. Provenance

- Reads (receipt): `results/experiments/exp35_R3_cross_scripture_redo/exp35_R3_cross_scripture_redo.json`
- Writes only: `results/experiments/exp97_crosscripture_t8/exp97_crosscripture_t8.json`
- Paper hook: feeds the corpus-scale `p_corpus(x)` term into the proposed §4.37 Multi-Scale Stack Law Fisher combiner

---

*Pre-registered 2026-04-22 late. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`.*
