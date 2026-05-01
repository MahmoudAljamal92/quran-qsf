# QSF Experiments Sandbox

> **Rule #1: this folder never, ever, under any circumstance, modifies**
> - `notebooks/ultimate/QSF_ULTIMATE.ipynb`
> - anything in `results/checkpoints/`
> - anything in `results/integrity/`
> - `results/ULTIMATE_REPORT.json`
> - `results/ULTIMATE_SCORECARD.md`
> - `results/CLEAN_PIPELINE_REPORT.json`
> - `results/figures/*.png`
> - any `.zip` or `.log` already present in `results/`

## Purpose

This folder is a **write-isolated sandbox** for exploratory experiments built on top of the
locked, audited QSF pipeline. It allows new hypotheses (Ādiyāt deep-dive, analytic F-tail,
MI block-scaling, criticality tests, universality sweeps, etc.) to be tested *without
re-running* or *mutating* the main notebook.

## How safety is enforced

1. **Read-only loader** (`_lib.py::load_phase`) verifies every checkpoint's SHA-256 against
   `results/checkpoints/_manifest.json` before returning data. If a checkpoint has been
   modified, the loader raises `IntegrityError` and refuses to return anything.
2. **Output redirector** (`_lib.py::safe_output_dir`) guarantees every write goes under
   `results/experiments/<exp_name>/`. It rejects any path that resolves outside that tree.
3. **Pre/post self-check** (`_lib.py::self_check`) hashes every protected file at the start
   and end of each experiment run. If any protected hash changes, the experiment is flagged
   FAILED even if its computation succeeded.

## Layout

```
experiments/
├── README.md                (this file)
├── _lib.py                  (read-only loader, output guard, self-check)
└── <expNN_shortname>/       (one folder per experiment, e.g. exp03_adiyat/)
    ├── run.py  or  run.ipynb
    └── notes.md             (hypothesis, method, findings)

results/experiments/         (NEW — isolated output tree)
└── <expNN_shortname>/
    ├── <exp>.json
    ├── <exp>.png
    └── self_check_<timestamp>.json
```

**Scaffold-only experiments** (code present, no locked results): `exp25_farasa_sensitivity`, `exp29_phi_m_error_correction`, `exp42_*`. These were scoped but not executed; the scaffolds remain as documentation of the decision process.

## Canonical experiment template

```python
# experiments/expNN_name/run.py
from experiments._lib import (
    load_phase, load_integrity, safe_output_dir, self_check_begin, self_check_end,
)

EXP = "expNN_name"
OUT = safe_output_dir(EXP)
pre = self_check_begin()

# ---- read-only loads ----
phi_m   = load_phase("phase_06_phi_m")
core    = load_phase("phase_07_core")
names   = load_integrity("names_registry")

# ---- new computation here, writing ONLY under OUT ----
# (this script does not modify the main pipeline or locked results.)

post = self_check_end(pre)   # raises if any protected file changed
```

## Current experiments

| ID | Short name | Hypothesis | Status |
|:---|:---|:---|:---|
| — | (none yet) | sandbox just set up | ready |

## What this sandbox is **not** for

- Editing `QSF_ULTIMATE.ipynb`. That file is locked.
- Re-running the main pipeline. Use the pinned checkpoints instead.
- Overwriting `ULTIMATE_REPORT.json` / `ULTIMATE_SCORECARD.md`. Promotion into the main
  notebook is always a separate, explicit decision by the user.

---
*Created 2026-04-19 as part of the post-audit experimental phase.*
