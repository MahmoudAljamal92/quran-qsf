# QSF ULTIMATE-2

Complementary letter-level tampering-detection pipeline, stacked on top of
Ultimate-1's locked 5-D Φ_M claim.

> **Audit status (2026-04-20):** two rounds of zero-trust audit have been
> applied. Round 1 closed 13 FATAL + 21 WARN findings
> ([`AUDIT_ULTIMATE2.md`](./AUDIT_ULTIMATE2.md) +
> [`AUDIT_ULTIMATE2_FIXES.md`](./AUDIT_ULTIMATE2_FIXES.md)). Round 2 closed
> 5 further FATAL + 8 WARN findings including three headline-flippers
> ([`AUDIT_ULTIMATE2_ROUND2.md`](./AUDIT_ULTIMATE2_ROUND2.md)). Current
> schema is `SCHEMA_VERSION = 3`.

## Files

| Path                                                       | Role                                                |
| ---------------------------------------------------------- | --------------------------------------------------- |
| `QSF_ULTIMATE_2.ipynb`                                     | Orchestrator notebook (42 cells, FAST/FULL modes)   |
| `_build_ultimate2.py`                                      | Regenerates the notebook from source — always the source of truth |
| `../experiments/ultimate2_pipeline.py`                     | R2–R11 + MASTER implementations (callable)          |
| `../experiments/exp09_R1_variant_forensics_9ch/run.py`     | R1 standalone (kept separate because of its size)   |
| `../experiments/_ultimate2_helpers.py`                     | Arabic normaliser, letter-edit, char-LM, nulls      |
| `../experiments/LOST_GEMS_AND_NOBEL_PATH.md`               | Scientific rationale & dead-ends to avoid           |

## How to run

```powershell
# 1) (optional) regenerate the notebook from the .py source
python notebooks/ultimate/_build_ultimate2.py

# 2) open the notebook
jupyter lab notebooks/ultimate/QSF_ULTIMATE_2.ipynb
```

### Toggles

Inside the notebook:

* `FAST = True`        fast smoke-run (≈10–25 min total once all caches are cold)
* `FAST = False`       full run (hours) — paper numbers
* `FORCE_RERUN = True` ignore on-disk result caches and recompute every R

## What each R does

| R   | Question                                                      | Expected signal                         |
| --- | ------------------------------------------------------------- | --------------------------------------- |
| R1  | 9 independent channels — does a letter swap fire ≥ 3?          | ≥ 3 channels at \|z\| > 2 for canonical variants |
| R2  | Does a local 3-verse window amplify the swap vs whole surah?    | median amp ≥ 2× (backup: 8.5×)          |
| R3  | Permutation test on canonical path across scriptures            | Quran \|z\| ≫ any other scripture       |
| R4  | Char 5-gram LM separates canonical from swapped Quran           | AUC ≥ 0.90                              |
| R5  | Can any forgery strategy (G0-G4) match real Quran path?         | 0 % forgeries below real                |
| R6  | Word-graph modularity Q — is Quran rank 1?                      | Quran rank 1                            |
| R7  | Φ-degradation curve across noise rates 1-20 %                   | Quran/control ratio > 2× at all rates    |
| R8  | Null ladder N0–N7 on verse order                               | Quran rate decays slowly; controls crash|
| R9  | Cross-scale propagation L1→L4                                   | VIS > 1                                 |
| R10 | Verse-internal word-order permutation                          | Quran sig-rate > all controls            |
| R11 | Symbolic formula Φ_sym = H_nano_ln + RST − VL_CV               | AUC ≈ 0.98 (if features available)       |

## Output

Every R writes to `results/experiments/expNN_*/expNN_*.json`.
MASTER aggregates these and writes
`results/experiments/exp20_MASTER_composite/ULTIMATE2_REPORT.json`.

Nothing outside `results/experiments/` is ever touched; a protected-file
self-check runs at notebook start and end and refuses to publish if any
Ultimate-1 artefact has drifted.

## Tampering Detection Law (TDL) — candidate form

> For any single-letter edit to the canonical Hafs rasm, at least 2 of N
> independent Ultimate-2 channels fire at \|z\| > 2 with probability ≥ P_detect.

`P_detect` is computed by MASTER as `1 − Π_k (1 − p_k)` under a (deliberately
optimistic) channel-independence assumption. A calibrated, correlation-aware
version is the natural next milestone.

## Relationship to Ultimate-1

Ultimate-1 is the locked, peer-review-ready scorecard for the 5-D Φ_M claim.
Ultimate-2 is a stress-test layer: it assumes Ultimate-1's frozen feature
space and asks *how much tampering can we detect, given that space and a few
extras?* Ultimate-1 should never be modified by work done in Ultimate-2.
