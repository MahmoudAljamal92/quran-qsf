# exp52 — Runbook

Short, self-contained instructions for running the Acoustic Bridge experiment
safely on GTX 1060 6 GB without freezing the PC. Written to be executed **from
a terminal in Windsurf (or Windows PowerShell)**, not through the AI chat —
that way you see live progress per surah and can Ctrl-C at any time.

---

## 0. One-time setup (already done in your environment)

```powershell
# Should be on PATH / installed already:
#   python >= 3.11
#   torch, torchaudio  (CUDA 11 or 12 build)
#   transformers, librosa, praat-parselmouth, pydub, imageio-ffmpeg
#   pandas, numpy, scipy, matplotlib
python -c "import torch, librosa, parselmouth, transformers; print('OK')"
```

Audio files must live at:
```
D:\القرآن الكريم\Mohammed_Siddiq_Al-Minshawi\001.mp3 ... 114.mp3
```

---

## 1. Verify text features + fix status (should take < 5 s)

```powershell
cd C:\Users\mtj_2\OneDrive\Desktop\Quran
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full._audit
```

Expected: all hard checks pass, 1 soft warning (4.15 % strip rate — expected,
it's non-phonetic recitation marks). **If any hard check fails, STOP** and
re-audit before running anything else.

---

## 2. Pilot (5 short surahs; should finish in ~11 s once model is cached)

```powershell
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full.run `
  --surahs 1,103,108,112,114 --mode pilot
```

Expected:
- `aligned X/X verses` per surah
- 23 real verses aligned, ~1117 letters
- H2 (madd → pitch) r ≈ +0.42, p ≈ 0.04

First run will download the wav2vec2-large-xlsr-53-arabic model (~1.26 GB,
one-time, cached under `%USERPROFILE%\.cache\huggingface\hub`).

---

## 3. Stress-test the chunker on one medium-long surah (BEFORE the full run)

This is the critical safety check: if it freezes or OOMs here, **stop** and
tell me — otherwise the full run will waste hours. Surah 78 (~5 min) and 36
(~16 min) are good candidates. Start small.

```powershell
# Surah 78 — 5.3 min, 40 verses, ~15 s wall-clock
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full._chunker_smoke --surah 78

# Surah 36 Ya-Sin — 15.9 min, 83 verses, projected ~60 s wall-clock
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full._chunker_smoke --surah 36

# Surah 18 Al-Kahf — ~35 min, 110 verses, projected ~2.5 min wall-clock
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full._chunker_smoke --surah 18
```

Per-call success criteria:
- `PASS surah X ... aligned X/X verses ... mono=True`
- No "chunk FAILED" lines
- Wall-clock < 5 × audio duration (= at least 0.2× real-time)
- **PC remains responsive** throughout (per-verse alignment uses only short
  audio windows, so peak VRAM stays ≤ 2 GB)

---

## 4. Full 114-surah run (projected ~1–2 h)

```powershell
python -X utf8 -u -W ignore -m experiments.exp52_acoustic_bridge_full.run `
  --all --mode full --skip-existing
```

Key flags:
- `--all` : process surahs 1..114
- `--mode full` : final aggregated output prefix is `full_*`
- `--skip-existing` : **resumability** — if the run crashes, re-running
  this exact command picks up where it left off (per-surah CSVs live in
  `results/experiments/exp52_acoustic_bridge_full/per_surah/`)
- `--max-audio-s 3600` : (default) skips any surah longer than 1 h. For
  Al-Minshawi Murattal this affects only surah 2 (Baqarah, ~2 h 16 min).
  Set `--max-audio-s 0` to disable the ceiling (risky).
- `--max-single-s 60` : (default) audio ≤ 60 s uses single-pass CTC;
  longer audio uses **per-verse alignment** (silence-window-based).

Per-surah progress prints to the terminal. If the run ever freezes on a
particular surah, Ctrl-C, check `per_surah/XXX_diag.json` for the error,
re-run the command, and `--skip-existing` will skip the completed ones.

---

## 5. Outputs

Written under `results/experiments/exp52_acoustic_bridge_full/`:

- `full_per_verse.csv` : all aligned verses × text + acoustic features
- `full_per_letter.csv` : every aligned letter × timings × tajweed flags
- `full_correlations.csv` : 54-row correlation matrix (9 text features × 6 acoustic)
- `full_results.json` : hypothesis tests + per-surah diagnostics + settings
- `full_fig_scatter.png`, `full_fig_alignment.png` : visual QC
- `per_surah/{NNN}_{verses,letters,diag}.*` : incremental per-surah checkpoints

---

## Troubleshooting

- **Freeze / long hang on surah X**: Ctrl-C, open `per_surah/XXX_diag.json`.
  If the audio length exceeds the available VRAM budget, reduce `--max-single-s`
  (e.g. to 30) and re-run with `--skip-existing`.
- **"CUDA out of memory"**: close other GPU apps (browsers with hardware
  acceleration can eat 1-2 GB). Re-run with `--skip-existing`.
- **One surah fails repeatedly**: inspect its audio file; sometimes an MP3 is
  corrupted. You can exclude it with `--surahs 1,2,3,...` explicitly.
- **Results look wrong**: check `_audit.py` output; ensure `count_syllables`
  etc. have not been edited out of spec.
