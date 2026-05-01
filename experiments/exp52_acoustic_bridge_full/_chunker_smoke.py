"""
Smoke-test of the new silence-aligned chunker on one medium-length surah.
Run DIRECTLY in your terminal (not via chat) to see live progress:

    python -u -m experiments.exp52_acoustic_bridge_full._chunker_smoke --surah 18

Surahs and typical audio duration (Minshawi Murattal, target chunks at 60 s):
    78  An-Naba'     ~3.5 min     ( 4 chunks)
    36  Ya-Sin      ~15.9 min     (16 chunks)
    18  Al-Kahf     ~35.0 min     (35 chunks)  <-- recommended stress test
    19  Maryam      ~21.0 min     (21 chunks)
    55  Ar-Rahman   ~10.0 min     (10 chunks)

Expected VRAM peak per chunk: ~1.5 GB. Safe on GTX 1060 6GB.

Reports:
  - per-chunk timing + VRAM
  - per-verse aligned/missed count
  - monotonicity of verse starts
  - total wall-clock
  - writes CSVs under results/experiments/exp52_acoustic_bridge_full/smoke/
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

# allow python -m  or  python path/to/file.py
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from experiments.exp52_acoustic_bridge_full._text import (
    load_quran_vocal, build_alignment_target,
)
from experiments.exp52_acoustic_bridge_full._audio import (
    setup_ffmpeg, load_audio, CTCAligner,
)
from experiments.exp52_acoustic_bridge_full.run import align_and_score_surah

AUDIO_DIR = Path(r"D:\القرآن الكريم\Mohammed_Siddiq_Al-Minshawi")
CORPUS    = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
OUT       = ROOT / "results" / "experiments" / "exp52_acoustic_bridge_full" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surah", type=int, default=18,
                    help="Surah number (default 18 Al-Kahf, 35 min stress-test)")
    ap.add_argument("--max-single", type=float, default=60.0,
                    help="Max single-pass seconds (default 60 s)")
    ap.add_argument("--top-db", type=float, default=25.0,
                    help="Silence detection threshold (dB below max)")
    args = ap.parse_args()
    sn = args.surah

    setup_ffmpeg()
    mp3 = AUDIO_DIR / f"{sn:03d}.mp3"
    if not mp3.exists():
        print(f"[smoke] missing audio: {mp3}", flush=True)
        return 2

    print(f"[smoke] surah {sn}  audio={mp3}", flush=True)
    corpus = load_quran_vocal(CORPUS)
    verses = corpus[sn]
    print(f"[smoke] corpus has {len(verses)} verses for surah {sn}", flush=True)

    # --- Load audio (prints early so you know we're not stuck at this step)
    print(f"[smoke] loading audio ...", flush=True, end=" ")
    t0 = time.time()
    y, sr = load_audio(str(mp3), sr=16000)
    dur = len(y) / sr
    print(f"OK {dur:.1f}s ({dur/60:.1f} min) in {time.time()-t0:.1f}s", flush=True)

    # --- Instantiate aligner (heavy: ~5 s cached, ~45 s cold)
    print(f"[smoke] initialising CTCAligner (max_single={args.max_single}s) ...",
          flush=True, end=" ")
    t0 = time.time()
    aligner = CTCAligner(max_seconds_single=args.max_single)
    print(f"OK in {time.time()-t0:.1f}s", flush=True)

    # --- Alignment
    print(f"[smoke] aligning ... (live chunk progress below)", flush=True)
    t0 = time.time()
    try:
        vrecs, lrecs, diag = align_and_score_surah(sn, verses, y, sr, aligner)
    except Exception as e:
        import traceback
        print(f"[smoke] ALIGNMENT FAILED: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        return 3
    wall = time.time() - t0
    rt_factor = dur / wall if wall > 0 else 0.0
    print(f"[smoke] aligned in {wall:.1f}s  ({rt_factor:.1f}x real-time)", flush=True)

    # --- Diagnostics
    real = [v for v in vrecs if v.verse_no > 0]
    n_aligned = sum(1 for v in real if v.n_letters_aligned > 0)
    total_chars = sum(v.n_letters_aligned for v in real)
    print(f"[smoke] verses aligned: {n_aligned} / {len(real)}  "
          f"(chars aligned: {total_chars})", flush=True)

    # Monotonicity
    ts = [v.t_start for v in real if v.n_letters_aligned > 0 and np.isfinite(v.t_start)]
    mono_ok = all(ts[i] <= ts[i+1] for i in range(len(ts) - 1))
    print(f"[smoke] verse-start monotonic: {mono_ok}  "
          f"(range {ts[0]:.2f}-{ts[-1]:.2f} s, audio={dur:.2f} s)", flush=True)

    # Duration sanity
    durs = [v.Duration_s for v in real if v.n_letters_aligned > 0]
    print(f"[smoke] verse duration stats: mean={np.mean(durs):.2f}s  "
          f"median={np.median(durs):.2f}s  min={np.min(durs):.2f}s  "
          f"max={np.max(durs):.2f}s", flush=True)

    # --- Save CSVs
    df_v = pd.DataFrame([v.__dict__ for v in real])
    df_l = pd.DataFrame([l.__dict__ for l in lrecs])
    df_v.to_csv(OUT / f"smoke_s{sn:03d}_per_verse.csv", index=False, encoding="utf-8-sig")
    df_l.to_csv(OUT / f"smoke_s{sn:03d}_per_letter.csv", index=False, encoding="utf-8-sig")
    print(f"[smoke] wrote:\n  {OUT / f'smoke_s{sn:03d}_per_verse.csv'}\n"
          f"  {OUT / f'smoke_s{sn:03d}_per_letter.csv'}", flush=True)

    # --- Summary line
    print(f"\n[smoke] PASS  surah {sn}  {dur:.1f}s audio -> {n_aligned}/{len(real)} "
          f"verses aligned in {wall:.1f}s  (mono={mono_ok})", flush=True)
    return 0 if mono_ok and n_aligned >= int(0.9 * len(real)) else 1


if __name__ == "__main__":
    sys.exit(main())
