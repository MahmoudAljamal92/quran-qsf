# QSF tools

Two stand-alone utilities that wrap the locked 5-D feature extractor
for external use. Neither reads nor writes anything under
`results/checkpoints/`, `results/integrity/`, or the `notebooks/ultimate/`
protected files.

## `qsf_score.py` — CLI scorer

Scores an Arabic text on the 5-D feature space and reports `Phi_M`.

```powershell
# file input (recommended; avoids PowerShell stdin encoding quirks)
python -X utf8 tools/qsf_score.py --file path/to/text.txt

# JSON output for downstream scripts
python -X utf8 tools/qsf_score.py --file path/to/text.txt --json

# one-line CSV row for spreadsheet ingestion
python -X utf8 tools/qsf_score.py --file path/to/text.txt --csv
```

Stdin also works on Unix shells. On Windows PowerShell use `--file`
because here-strings sometimes insert a BOM or re-encode to CP1256
before the pipe, which corrupts the first bytes of Arabic text.

**Output format**

```
n_verses  = 7
EL        = 0.1667
VL_CV     = 0.5474
CN        = 0.0000
H_cond    = 0.3333
T         = -0.6519
Phi_M     = 6.729
grade     = A+  (cutoffs A+ > 6.0, A > 4.0, B > 2.0, C > 1.0, D else)
```

Grade cutoffs are the ex-ante 1/2/4/6 sigma cutoffs from
`results/integrity/preregistration.json::grade_thresholds` — NOT
post-hoc tuned.

## `qsf_score_app.py` — Streamlit UI

Interactive web UI over the same scoring function plus a `(T, EL)`
scatter showing Band-A per-surah positions of all 9 corpora in
`phase_06`.

```powershell
pip install streamlit matplotlib
python -m streamlit run tools/qsf_score_app.py
```

This opens `http://localhost:8501/`. Paste or upload text; the page
updates live.

## What this tool is NOT

- **Not a forensic detector.** A high Phi_M score is necessary but
  NOT sufficient for Quran-like authenticity. The proper edit-detection
  claim lives in the `R2` sliding-window and `R12` gzip channels
  (`experiments/exp10_R2_sliding_window/`, `experiments/exp41_gzip_formalised/`).
- **Not a theological verdict.** Phi_M is a descriptive stylometric
  distance, not a metric of truth, inspiration, or any normative property.
- **Not a generative filter.** Do NOT use this to filter outputs of a
  GPT-style model and keep only the "most Quran-like" candidates.
  That workflow overfits to GPT's distribution on the 5-D hypersurface
  and produces text that matches the 5-D signature while failing every
  other linguistic check (classic Goodhart's law). The R5 adversarial
  channel (`experiments/exp13_R5_adversarial/`) already documents that
  EL+RD-aware Markov forgeries clear 50 % of Phi_M thresholds on pure
  feature-matching grounds.

## Provenance

Both tools reload `results/checkpoints/phase_06_phi_m.pkl` which is
SHA-256-pinned in `results/checkpoints/_manifest.json`. If the pin
fails, the tools refuse to load with `IntegrityError` — do NOT bypass
this check.
