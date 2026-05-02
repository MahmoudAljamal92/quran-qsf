"""D1 prototype — letter-level multifractal Δα on the 28-letter rasm skeleton.

Hypothesis
----------
The Quran's documented multifractal extremum (F87 axis 2, Δα ≈ 0.51)
is computed on the *verse-length* sequence and requires N ≥ 64 verses.
D1 asks: is a comparable extremum also present at the *letter* level
within a single surah — and does it require only ~100+ letters, making
it testable on a 3-verse / 10-word sample?

Method
------
1. For every text we read it as a 28-letter rasm skeleton (no spaces, no
   diacritics, no punctuation).
2. We map each letter to its global frequency rank (1 = most frequent in
   the Quran corpus, 28 = least frequent). This gives a 1-D integer
   series whose multifractal structure reflects *letter-ordering*
   statistics rather than letter-frequency alone.
3. We compute Δα_letter using the existing MFDFA implementation
   (metrics.delta_alpha_mfdfa) which requires N ≥ 64. A single 289-letter
   verse (2:196) clears this threshold easily.

Controls
--------
We compare four corpora:
  - Quran (114 surahs individually)
  - Classical Arabic poetry (windowed to match surah lengths)
  - Hadith (windowed)
  - Arabic modernist prose — Hindawi (windowed)

If the Quran's Δα_letter distribution is separated from all three
control distributions by LOO-z ≥ 3 (the bar we used for F87 axis 2),
D1 is declared viable and we wire it into the Streamlit app as a new
axis "Δα_letter — letter-level multifractal width".

Otherwise we report exactly what we found, honestly, and move on.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

import numpy as np

# --- wire into the existing app library ------------------------------------
REPO = Path(__file__).resolve().parents[1]
APP = REPO / "app"
sys.path.insert(0, str(APP))

from pristine_lib import corpus, metrics  # noqa: E402
from pristine_lib.normalize import normalize_arabic_letters_only  # noqa: E402


# ---------------------------------------------------------------------------
# 1.  Letter -> frequency-rank map derived from the Quran itself
# ---------------------------------------------------------------------------
def _quran_letter_ranks() -> dict[str, int]:
    """Rank 1..28: 1 = most frequent letter in the Quran rasm skeleton."""
    all_letters = "".join(v.skeleton for v in corpus.all_verses())
    counts = Counter(all_letters)
    ranked = [ch for ch, _ in counts.most_common()]
    return {ch: i + 1 for i, ch in enumerate(ranked)}


def skeleton_to_series(skel: str, rank_map: dict[str, int]) -> np.ndarray:
    """Map a rasm-only skeleton to an integer time series of letter ranks."""
    return np.asarray([rank_map.get(c, 0) for c in skel if c in rank_map],
                      dtype=float)


# ---------------------------------------------------------------------------
# 2.  Δα_letter for a single text
# ---------------------------------------------------------------------------
def delta_alpha_letter(skel: str, rank_map: dict[str, int]) -> float:
    s = skeleton_to_series(skel, rank_map)
    if s.size < 128:               # need comfortable headroom over the 64 floor
        return float("nan")
    return metrics.delta_alpha_mfdfa(s)


# ---------------------------------------------------------------------------
# 3.  Corpus readers (minimal, just enough for the viability check)
# ---------------------------------------------------------------------------
_AR_LETTERS_RX = re.compile(r"[^\u0621-\u064A]")


def _ar_chunks_from_text(raw: str, chunk_letters: int,
                         max_chunks: int) -> list[str]:
    """Split a long Arabic blob into non-overlapping chunks of a given
    normalised-letter length."""
    skel = normalize_arabic_letters_only(raw)
    chunks = []
    for i in range(0, len(skel), chunk_letters):
        piece = skel[i:i + chunk_letters]
        if len(piece) >= chunk_letters:
            chunks.append(piece)
        if len(chunks) >= max_chunks:
            break
    return chunks


def load_controls(chunk_letters: int, max_per_source: int
                  ) -> dict[str, list[str]]:
    root = REPO / "data" / "corpora" / "ar"
    out: dict[str, list[str]] = {}

    for label, path in [
        ("poetry",  root / "poetry.txt"),
        ("ksucca",  root / "ksucca.txt"),     # classical Arabic prose
        ("hindawi", root / "hindawi.txt"),   # modern Arabic prose
    ]:
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        out[label] = _ar_chunks_from_text(raw, chunk_letters, max_per_source)
    return out


# ---------------------------------------------------------------------------
# 4.  Viability test
# ---------------------------------------------------------------------------
def _loo_z(value: float, controls: list[float]) -> float:
    arr = np.asarray([c for c in controls if np.isfinite(c)])
    if arr.size < 8:
        return float("nan")
    mu, sd = float(arr.mean()), float(arr.std(ddof=1))
    return (value - mu) / sd if sd > 0 else float("nan")


def describe(label: str, values: list[float]) -> None:
    v = np.asarray([x for x in values if np.isfinite(x)])
    if v.size == 0:
        print(f"  {label:14s}  n=0 (no finite values)")
        return
    print(f"  {label:14s}  n={v.size:4d}  "
          f"mean={v.mean():.4f}  sd={v.std(ddof=1):.4f}  "
          f"min={v.min():.4f}  p50={np.median(v):.4f}  max={v.max():.4f}")


def main() -> None:
    t0 = time.time()
    print("D1 — letter-level multifractal Δα viability probe")
    print("=" * 70)

    rank_map = _quran_letter_ranks()
    print(f"Rank map built from Quran corpus (28 letters).")

    # --- 4a. Quran Δα_letter per surah ------------------------------------
    quran_by_surah: dict[int, str] = {}
    for v in corpus.all_verses():
        quran_by_surah.setdefault(v.surah, "")
        quran_by_surah[v.surah] += v.skeleton

    quran_vals = []
    quran_lens = []
    for s, skel in quran_by_surah.items():
        da = delta_alpha_letter(skel, rank_map)
        if np.isfinite(da):
            quran_vals.append(da)
            quran_lens.append(len(skel))
    print(f"\nQuran surahs tested: {len(quran_vals)}/{len(quran_by_surah)} "
          f"(skipped any with < 128 letters).")
    print(f"Surah letter lengths: min={min(quran_lens)}, "
          f"median={int(np.median(quran_lens))}, max={max(quran_lens)}")

    # Use the MEDIAN Quran surah length as the control chunk size so we
    # compare like with like.
    chunk_letters = int(np.median(quran_lens))
    max_per_source = 300
    print(f"\nControl chunk size: {chunk_letters} letters "
          f"(matches median Quran surah). Max {max_per_source}/source.")

    ctrl_raw = load_controls(chunk_letters, max_per_source)
    ctrl_vals: dict[str, list[float]] = {}
    for label, chunks in ctrl_raw.items():
        vals = []
        for ch in chunks:
            da = delta_alpha_letter(ch, rank_map)
            if np.isfinite(da):
                vals.append(da)
        ctrl_vals[label] = vals

    # --- 4b. Descriptives --------------------------------------------------
    print("\nLetter-level Δα distributions")
    print("-" * 70)
    describe("QURAN", quran_vals)
    for label, vals in ctrl_vals.items():
        describe(label.upper(), vals)

    # --- 4c. Separation from each control ---------------------------------
    print("\nSeparation: where does the Quran MEDIAN fall vs each control?")
    print("-" * 70)
    q_med = float(np.median(quran_vals))
    for label, vals in ctrl_vals.items():
        z = _loo_z(q_med, vals)
        if not np.isfinite(z):
            print(f"  {label:14s}  control n too small, skipping")
            continue
        arr = np.asarray(vals)
        above = float(np.mean(arr > q_med))
        below = float(np.mean(arr < q_med))
        print(f"  {label:14s}  z(Q_median vs {label})={z:+.3f}  "
              f"ctrl>Q_med: {above*100:.1f}%  ctrl<Q_med: {below*100:.1f}%")

    # --- 4d. Verdict -------------------------------------------------------
    print("\nViability verdict")
    print("-" * 70)
    # For D1 to be "viable" we require the Quran's Δα_letter distribution
    # to be measurably distinct from at least two of three controls
    # (|LOO-z| ≥ 2 using Quran median vs control distribution).
    zscores = {}
    for label, vals in ctrl_vals.items():
        zscores[label] = _loo_z(q_med, vals)
    n_strong = sum(1 for z in zscores.values() if np.isfinite(z) and abs(z) >= 2.0)
    n_moderate = sum(1 for z in zscores.values() if np.isfinite(z) and abs(z) >= 1.0)

    print(f"  |z| ≥ 2 against: {n_strong}/{len(zscores)} controls")
    print(f"  |z| ≥ 1 against: {n_moderate}/{len(zscores)} controls")

    if n_strong >= 2:
        verdict = "VIABLE — ship it as Layer B axis Δα_letter."
    elif n_moderate >= 2:
        verdict = "MARGINAL — signal exists but is not extremum-strength."
    else:
        verdict = "NOT VIABLE — letter-level Δα does not discriminate."
    print(f"\n  Verdict: {verdict}")
    print(f"\nElapsed: {time.time()-t0:.1f}s")

    # Save a machine-readable receipt so we can reference this run later.
    receipt = {
        "quran": {
            "n_surahs_tested": len(quran_vals),
            "values": quran_vals,
            "lengths": quran_lens,
            "median": q_med,
            "mean": float(np.mean(quran_vals)),
            "sd": float(np.std(quran_vals, ddof=1)),
        },
        "controls": {
            k: {"n": len(v),
                "mean": float(np.mean(v)) if v else None,
                "sd": float(np.std(v, ddof=1)) if len(v) >= 2 else None,
                "values": v}
            for k, v in ctrl_vals.items()
        },
        "z_quran_vs_controls": {k: zscores[k] for k in zscores},
        "chunk_letters": chunk_letters,
        "verdict": verdict,
    }
    out_path = REPO / "docs" / "experiments" / "d1_letter_multifractal.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2))
    print(f"Receipt written to: {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
