# INTEGRITY PROTOCOL — How this project resists inflation, leaks, fake numbers, and wrong methods

> **Why this document exists**: a concern was raised that because this project's code was largely AI-assisted, results may be inflated, leaked, post-hoc, or methodologically wrong without the user being able to catch it. This document codifies the guardrails that make the *output* verifiable regardless of *how the code was written*. Anyone — human, AI, or external auditor — running the pipeline either reproduces the locked numbers or does not. The audit trail is mechanical, not a matter of opinion.
>
> **Status**: protocol v1.0, frozen 2026-04-28 evening (patch H V3).
>
> **One-line summary**: *if a receipt JSON cannot pass `scripts/integrity_audit.py`, the result is not citable.*

---

## 0. The five failure modes this protocol blocks

| # | Failure mode | What it looks like | How this protocol blocks it |
|---|---|---|---|
| 1 | **Number inflation** | Headline gets larger between draft and publication without a re-run | `results_lock.json` + `MANIFEST_v8.json` SHA-256 + every receipt's `prereg_hash` field. Any drift raises `HallucinationError` at notebook re-run time. |
| 2 | **Data leakage** | Test set used during model selection; cross-validation broken | Nested CV is locked; held-out splits SHA-pinned; `LOCO` and `bootstrap` are **separate** experiments with their own PREREGs. |
| 3 | **Fake numbers (hallucination)** | LLM-written report cites a value that doesn't exist in any receipt | Every published number must trace to a receipt JSON with a SHA-256 hash; `integrity_audit.py` walks every claimed scalar back to its receipt or flags it. |
| 4 | **Wrong source data** | Wrong corpus / wrong revision / wrong tokenisation used | `corpus_lock.json` lists every corpus file's SHA-256 and load path; `_warn_fingerprint_drift` triggers if the loader returns a different hash than expected. |
| 5 | **Wrong scientific method** | Post-hoc threshold tuning, multiple-testing without correction, p-hacking | **Pre-registration before data is opened** (PREREG.md + PREREG_HASH.txt); verdict ladder has **first-match-wins** so post-hoc selection of a "better" branch is mechanically impossible; multiple-testing is corrected by Brown / Bonferroni / BH where families are declared in the PREREG. |

If any of these five modes were *successfully* exploited in this project, that exploit would have to defeat *all* of the lock layers below simultaneously. No human or AI has demonstrated that capability against this stack.

---

## 1. Pre-registration discipline (the single most important guardrail)

Every hypothesis-scale experiment in this project follows a fixed pattern:

1. Author writes `experiments/<exp_name>/PREREG.md` containing:
   - Hypothesis ID (H##)
   - Substantive claim in one paragraph
   - **Frozen constants** (τ thresholds, seeds, corpora, compressor levels)
   - **Verdict ladder** with first-match-wins (e.g. ladder branches numbered 1–7, first matching condition fires)
   - **Audit hooks** (file integrity, drift sentinels, sanity-floor checks)
   - **Honesty clauses** (what cannot be done post-hoc)
2. SHA-256 of the finalised PREREG.md is written to `experiments/<exp_name>/PREREG_HASH.txt`.
3. The run script reads `PREREG_HASH.txt` into a constant `_PREREG_EXPECTED_HASH`.
4. The run script's first action is to compute SHA-256 of `PREREG.md` and compare against `_PREREG_EXPECTED_HASH`. **Mismatch aborts the run.**
5. Only then is data loaded.

This means: **the substantive claim is locked in a SHA-256 before a single line of data is read**. Any post-hoc edit to the PREREG breaks the hash and invalidates the run.

**Where to verify**: every receipt under `results/experiments/<exp_name>/<exp_name>.json` has a `prereg_hash` field. Examples currently on disk:

- `exp95f_short_envelope_replication.json` → `83a7b25ac69e703604a82be5c6f7c1d597ccd953f07df7f624ccc1c55d972a14` ✓
- `exp99_adversarial_complexity.json` → `78884b8d0e31cdda94aaeebbe25c4e4e87c01ad2eed5fa0bb8d2cf2f02c0ddb6` (verify via `python scripts/integrity_audit.py`)
- `exp96c_F57_meta.json` → `ba2b5af4a10f07b66446da29898224deb8b97ec0ce3ff42bfc169e8d0bd063a4` ✓

---

## 2. Verdict ladders with first-match-wins

The most subtle form of post-hoc bias is to **report whichever verdict happens to be friendliest** after looking at the data. This protocol blocks it by requiring **strict ordered ladders** in the PREREG.

Example from `experiments/exp95f_short_envelope_replication/PREREG.md` §2.2:

| # | Branch | Trigger |
|---|---|---|
| 1 | `FAIL_short_run_did_not_complete` | receipt missing/malformed |
| 2 | `FAIL_short_tau_drift` | τ drift > 1·10⁻¹² |
| 3 | `FAIL_q100_drift_short` | embedded Q:100 K=2 < 0.99 OR gzip-solo < 0.98 |
| 4 | `FAIL_envelope_correlation` | Pearson r > −0.70 |
| 5 | `FAIL_envelope_phase_boundary` | any band violator |
| 6 | `PARTIAL_envelope_replicates` | both pass AND r ∈ (−0.85, −0.70] |
| 7 | `PASS_envelope_replicates` | both pass AND r ≤ −0.85 |

**Rule**: first matching branch fires. Branch 4 cannot be skipped to "find" branch 7. The verdict applier (`scripts/verdict_h39_envelope.py`) enumerates branches in order and returns at the first match.

**Why this matters**: with this discipline, a "good" verdict is unambiguously the result of the data, not of branch-shopping. With 60 retractions and 10 failed-null pre-registrations on record, the ladder discipline has actively *killed* would-be findings; that is the most direct evidence it works.

---

## 3. Audit hooks (fail-closed)

Every non-trivial experiment carries audit hooks that **stop the run or invalidate the verdict** if any of the locked invariants drift. Examples:

- **τ-drift sentinel**: `max_drift ≤ 1·10⁻¹²` against the locked τ snapshot.
- **PREREG-hash sentinel**: SHA-256 of PREREG.md must match `_PREREG_EXPECTED_HASH`.
- **Embedded Q:100 regression**: every long-run Adiyat experiment re-computes the locked Q:100 K=2 and gzip-solo recall; deviation aborts the verdict.
- **Variant-count sanity**: SHORT scope must produce 300 K – 500 K variants; outside that range the run is suspect.
- **`audit_A2`-style root-coverage gates**: e.g. `exp100_verse_precision` requires ≥ 95 % CamelTools root coverage; below that, the verdict is `FAIL_audit_A2` regardless of how the substantive numbers look.

**Crucially**: when an audit hook fires, the substantive numbers are still computed and reported — but the receipt's verdict is the audit-failure verdict, not the substantive verdict. This is a deliberate "fail-closed" design: a passing substantive number does not buy you a published claim if the audit hook caught a method-level problem.

This is how `exp100_verse_precision` ended up as FN05 even though the substantive numbers were also unhelpful (rank 5/7) — the audit fired first and the failure category is `FAIL_audit_A2`, not `FAIL_not_rank_1`.

---

## 4. Frozen seeds + locked corpora (reproducibility)

- Default RNG seed for the entire project: **`SEED = 42`**.
- Specific experiments use additional seeds (e.g. `exp95d_multi_compressor_robust` checks {42, 137, 2024}).
- Every corpus file under `corpora/` has its SHA-256 in `results/integrity/corpus_lock.json`.
- The loader (`experiments/_lib.py::_warn_fingerprint_drift`) warns/aborts if a checkpoint was built against a different corpus hash than the current code.
- `MANIFEST_v8.json` lists the SHA-256 of every locked checkpoint, locked report, and locked figure.

Re-running the notebook on the same raw corpora **bit-reproduces every locked scalar**; this was last verified in patch I (2026-04-27 night, 22/22 phases, 0 drift across 127 scalars).

---

## 5. self_check_begin / self_check_end (mid-run drift detection)

Critical-path experiments call `experiments._lib.self_check_begin()` *before* loading data and `self_check_end(pre, exp_name)` immediately *after* writing the receipt. The two snapshots SHA-256 every protected file under `experiments/`, `src/`, and `notebooks/`. Any difference between begin and end means **the codebase was mutated mid-run**, and the receipt is invalidated.

These self-check files live alongside the receipt:

```
results/experiments/<exp_name>/self_check_<timestamp>.json
```

They are part of the audit trail the integrity script verifies.

---

## 6. SHA-256 receipt provenance

Every published-grade receipt JSON contains, at minimum:

| Field | Purpose |
|---|---|
| `experiment` | Name of the experiment |
| `hypothesis_id` | H## tying back to `HYPOTHESES_AND_TESTS.md` |
| `prereg_document` | Path to PREREG.md |
| `prereg_hash` | SHA-256 of PREREG.md (must match `_PREREG_EXPECTED_HASH`) |
| `frozen_constants` | All τ thresholds, seeds, ranges (numerically) |
| `audit_report` | Per-hook OK/FAIL block |
| `verdict` | Single string from the closed ladder |
| `verdict_block` | Diagnostics specific to the matched branch |
| `completed_at_utc` | ISO 8601 UTC timestamp |

The integrity audit script (`scripts/integrity_audit.py`) requires every receipt to carry these fields. Receipts that don't are flagged.

---

## 7. Anti-leakage and anti-circularity hooks

The 2026-04-27 reviewer feedback raised the **circularity objection**: "if Φ_master uses Quran-vs-controls statistics, isn't the headline ratio circular by construction?"

The protocol that defeats it:

1. **`exp96b_bayes_factor` (H50)** — leave-one-control-corpus-out (LOCO): hold out one of the 6 control corpora, recompute Φ_master from the remaining 5, repeat 6 times. Result: LOCO-min = 1,634.49 nats. Bootstrap (n=500) of the control pool: p05 = 1,759.72.
2. **`expP12_bootstrap_t2_ci`** — non-parametric bootstrap of T² with hadith dropped from controls: 95 % CI [3 127, 4 313]. Band-A T² = 3 557 sits inside the CI.
3. **`expP15_riwayat_invariance`** — 5 alternative Quran reading traditions (Warsh, Qaloun, Douri, Shuba, Sousi); all keep AUC ≥ 0.97 → the headline is rasm-invariant.

**Net effect**: every potential leak path is closed by a separately-pre-registered robustness experiment, each with its own audit hooks.

---

## 8. Multiple-testing correction (where applied)

- **F57 self-description meta-finding (`exp96c`)**: explicitly uses the family null `P(S ≥ 4 | Bin(6, 1/7)) = 0.0049`. The "1 of 6" individual-claim p-values are **not** the headline — the family-corrected p is.
- **PNAS-grade cross-tradition tests (`expE16_lc2_signature`)**: 8-corpus path-minimality uses BH (Benjamini-Hochberg) for the 8 z-tests; min BH-corrected p = 3·10⁻⁴.
- **Brown ρ-correction**: where witness statistics are correlated (e.g. AR(1) + Hurst H_delta + Benford in `expX3_prose_extremum_brown`), Brown's correction with empirical inter-witness correlation ρ̄ ≈ 0.4 is used; the result is reported under correction (Brown-corrected p ≈ 6.7·10⁻³⁴).

What is **NOT** done: a Bonferroni correction across "all 57 tolerance-gated scalars". That would be the wrong correction because the scalars are not a single hypothesis family — each is its own pre-registered claim with its own ladder.

---

## 9. Retraction discipline (the ultimate fraud-detector)

The single strongest evidence that this protocol works is that **60 once-claimed results have been retracted by the project itself** when the stricter null caught them. They live in:

- Canonical: `docs/reference/findings/RETRACTIONS_REGISTRY.md`
- Top-level mirror: `docs/RETRACTIONS_REGISTRY.md` (byte-exact copy of canonical, enforced by `scripts/integrity_audit.py` SHA-256 parity check)
- Compact handoff: `docs/reference/handoff/2026-04-25/04_RETRACTIONS_LEDGER.md`

Plus 9 failed-null pre-registrations in Category K (FN01–FN09).

A project that keeps fake numbers and never retracts produces zero retractions. A project that lets ladders fire honestly produces many. **60 retractions / 9 failed nulls is unusual rigor**, not weakness.

---

## 10. The integrity audit script (`scripts/integrity_audit.py`)

This is the executable form of the protocol. Run it after every new experiment:

```powershell
python scripts/integrity_audit.py
```

It walks every receipt under `results/experiments/`, applies the checks in §6, and writes a Markdown + JSON summary to `results/integrity/integrity_audit_<timestamp>.{md,json}`. Output verdicts:

| Verdict | Meaning |
|---|---|
| `PASS` | All required fields present; PREREG hash matches; audit report all-green; verdict in closed set |
| `WARN` | Receipt parses but is missing optional provenance (e.g. self-check files) |
| `FAIL_prereg_hash_mismatch` | PREREG.md SHA-256 disagrees with receipt's `prereg_hash` |
| `FAIL_no_verdict` | Receipt has no `verdict` field |
| `FAIL_audit_red` | At least one audit-hook block has `ok = false` and the receipt verdict does not reflect that audit failure |
| `FAIL_unparseable` | JSON malformed |

Any `FAIL_*` row blocks publication of that result until repaired.

---

## 11. Doc-sync discipline

After every experiment, the following docs are updated atomically as a single sprint:

1. `docs/reference/findings/HYPOTHESES_AND_TESTS.md` — H## row flipped from PENDING to verdict
2. `docs/reference/findings/RANKED_FINDINGS.md` — F## row added/updated
3. `docs/reference/findings/RETRACTIONS_REGISTRY.md` — R## or FN## entry if applicable
4. `docs/RANKED_FINDINGS.md` (top-level mirror) — supersession notice
5. `docs/RETRACTIONS_REGISTRY.md` (top-level mirror) — synced
6. `docs/PROGRESS.md` — header bumped
7. `docs/README.md` — header bumped
8. `docs/PAPER.md` — relevant § amended
9. `CHANGELOG.md` — new patch entry
10. `docs/HANDOFF_*` files — supersession block updated

**Rule**: no PR / commit / re-publication may declare a sprint complete until all 10 of these files are mutually consistent. The `integrity_audit.py` script also flags scoreboard-arithmetic inconsistencies between mirrors (e.g. canonical says 7 failed-nulls, mirror says 6 → **FAIL**).

---

## 12. AI-assistance disclosure (for full transparency)

This project's code, statistical methodology, and manuscript drafting were performed in collaboration with large language models. The author designed all experimental questions, supervised all decisions, made all retraction calls, and verified all final outputs. **All code is open-source; all results are reproducible from the pre-registrations and locked seeds; no result depends on AI judgment that is not numerically verifiable.**

The integrity protocol above is precisely the answer to the question "how do we know AI-assisted code didn't insert hallucinated numbers?". The answer is: the locked checkpoints + SHA-256 manifests + audit hooks + verdict ladders + retraction discipline make every claim mechanically verifiable. Anyone re-running the pipeline either reproduces the published numbers or does not. The pipeline does not require the reader to trust the author *or* the AI.

---

## 13. Quickstart for an external auditor

If you want to verify this project's headline numbers without trusting any human or AI claim:

```powershell
# 1. Verify corpus integrity
python scripts/_verify_corpus_lock.py

# 2. Verify every experiment receipt against its PREREG hash
python scripts/integrity_audit.py

# 3. Re-run the master notebook (FAST mode, ~80 min wall)
jupyter nbconvert --to notebook --execute notebooks/ultimate/full_pipeline.ipynb --output _re-run.ipynb

# 4. Verify locked scalars
python -c "import json; d=json.load(open('results/integrity/results_lock.json')); print('OK' if abs(d['Phi_M_hotelling_T2']['value'] - 3557.3394545046353) < 1e-9 else 'DRIFT')"
```

If steps 1–4 all return PASS / OK, the headline numbers are real. If any step fails, the failure mode tells you exactly which lock was broken.

---

*This protocol document is itself version-locked (SHA-256 of this file is appended to `MANIFEST_v8.json` at the next manifest refresh). Edits require a new patch entry in `CHANGELOG.md` and a fresh manifest line.*
