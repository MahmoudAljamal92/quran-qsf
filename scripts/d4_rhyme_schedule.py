"""D4 prototype — categorical rhyme-schedule match.

Hypothesis
----------
Unlike the smooth axes (H_EL, p_max, C_Ω, …) which need many verses to
be discriminating, the Quran has a *categorical* per-surah fingerprint:
each surah uses a dominant verse-final rasm letter chosen from only
~28 possible values, and that choice is a highly non-random property
of the text.  If we hash every surah as (dominant_final_letter,
fraction_of_verses_sharing_it), we obtain a rhyme-schedule that an
arbitrary Arabic passage is unlikely to reproduce *even with just 3
verses*.

Precise test
------------
For a candidate passage at some length L verses:

  1.  Compute its (dom_letter, dom_share).
  2.  Restrict the Quran rhyme-schedule to Quranic surahs with ≥ L
      verses.  For each such surah, ask:
          does the surah's dom_letter equal the candidate's dom_letter
          AND is its dom_share within ±0.10 of the candidate's?
      If yes → this Quranic surah is a "schedule match" for the input.
  3.  The match fraction across surahs is the Quran-schedule score.

  Compare this score on:
    - random windows of classical Arabic poetry (should land high —
      monorhyme is the rule)
    - random windows of classical Arabic prose (ksucca / hadith)
    - random windows of modern Arabic prose (hindawi)

The relevant quantity is NOT the raw score (poetry will often hit
too), it is the JOINT signature:
   (dom_letter matches Quran) AND
   (dom_share inside Quran's letter-specific band) AND
   (verse-length CV inside Quran's letter-specific band).

D4 is declared VIABLE if adding the length-CV constraint separates
Quran from every control at |LOO-z| ≥ 2 at N as small as 3 verses.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "app"
sys.path.insert(0, str(APP))

from pristine_lib import corpus  # noqa: E402
from pristine_lib.normalize import (  # noqa: E402
    normalize_arabic_letters_only,
    split_into_verses,
)


# ---------------------------------------------------------------------------
# 1.  Build the Quran per-surah rhyme schedule
# ---------------------------------------------------------------------------
def _final_letter(skel: str) -> str:
    return skel[-1] if skel else ""


def _verse_stats(verses: list[str]) -> tuple[str, float, float, int]:
    """Return (dominant_final_letter, dom_share, length_CV, n_verses)."""
    if not verses:
        return ("", 0.0, 0.0, 0)
    skels = [normalize_arabic_letters_only(v) for v in verses]
    skels = [s for s in skels if s]
    n = len(skels)
    if n == 0:
        return ("", 0.0, 0.0, 0)
    finals = [_final_letter(s) for s in skels if s]
    counts = Counter(finals)
    dom_letter, dom_count = counts.most_common(1)[0]
    dom_share = dom_count / n
    lens = np.asarray([len(s) for s in skels], dtype=float)
    cv = float(lens.std(ddof=0) / lens.mean()) if lens.mean() > 0 else 0.0
    return (dom_letter, dom_share, cv, n)


def quran_schedule():
    """List of (surah, dom_letter, dom_share, length_CV, n_verses) for
    every Quranic surah."""
    by_surah: dict[int, list[str]] = defaultdict(list)
    for v in corpus.all_verses():
        by_surah[v.surah].append(v.raw)
    sched = []
    for s, verses in by_surah.items():
        dl, ds, cv, n = _verse_stats(verses)
        sched.append((s, dl, ds, cv, n))
    return sched


# ---------------------------------------------------------------------------
# 2.  Score an input passage against the Quran schedule
# ---------------------------------------------------------------------------
def score_passage(verses: list[str], schedule,
                  share_tol: float = 0.10,
                  cv_tol: float = 0.20):
    """Match fraction of Quranic surahs (of ≥ this length) compatible
    with the candidate on (dom_letter, dom_share, length_CV).

    Returns a dict with per-constraint match counts.
    """
    dl, ds, cv, n = _verse_stats(verses)
    if n == 0:
        return {"n": 0, "letter_match": 0, "letter_and_share": 0,
                "letter_and_share_and_cv": 0, "denom": 0}
    # Compare only against surahs of comparable or greater length.
    comparable = [row for row in schedule if row[4] >= n]
    denom = len(comparable)
    letter_match = sum(1 for (_, DL, _, _, _) in comparable if DL == dl)
    letter_and_share = sum(
        1 for (_, DL, DS, _, _) in comparable
        if DL == dl and abs(DS - ds) <= share_tol
    )
    letter_and_share_and_cv = sum(
        1 for (_, DL, DS, CV, _) in comparable
        if DL == dl and abs(DS - ds) <= share_tol and abs(CV - cv) <= cv_tol
    )
    return {
        "n": n, "dom_letter": dl, "dom_share": ds, "cv": cv,
        "letter_match": letter_match,
        "letter_and_share": letter_and_share,
        "letter_and_share_and_cv": letter_and_share_and_cv,
        "denom": denom,
    }


# ---------------------------------------------------------------------------
# 3.  Control corpora: synthesise "verses" by splitting at periods / newlines
#     into chunks of N comparable to Quran surahs.
# ---------------------------------------------------------------------------
def _split_arabic_corpus_into_verse_chunks(path: Path,
                                            target_n: int,
                                            max_samples: int
                                            ) -> list[list[str]]:
    """Read an Arabic text and return `max_samples` chunks, each a list
    of `target_n` 'verses' (sentences delimited by ., ؟, !, or newline).
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Sentence split: end-of-sentence punctuation, dots, newlines
    parts = re.split(r"[\.\!\?\n؟!]+", raw)
    parts = [p.strip() for p in parts if p.strip()]
    samples = []
    for i in range(0, len(parts) - target_n, target_n):
        chunk = parts[i : i + target_n]
        # skip if any "verse" is empty after normalisation
        skels = [normalize_arabic_letters_only(v) for v in chunk]
        if all(len(s) >= 3 for s in skels):
            samples.append(chunk)
        if len(samples) >= max_samples:
            break
    return samples


def load_controls(target_n: int, max_samples: int) -> dict[str, list[list[str]]]:
    root = REPO / "data" / "corpora" / "ar"
    out: dict[str, list[list[str]]] = {}
    for label, fn in [
        ("poetry",  "poetry.txt"),
        ("ksucca",  "ksucca.txt"),
        ("hindawi", "hindawi.txt"),
    ]:
        p = root / fn
        if p.exists():
            out[label] = _split_arabic_corpus_into_verse_chunks(
                p, target_n, max_samples)
    return out


# ---------------------------------------------------------------------------
# 4.  Viability probe
# ---------------------------------------------------------------------------
def probe_at_n(target_n: int, schedule, max_samples: int = 500):
    """Compare the Quran's internal schedule-match (every surah of ≥N
    scored against the whole schedule) to schedule-match scores on
    control windows."""
    # --- 4a. For the Quran itself: a "self-match" baseline.
    # For every surah with ≥ target_n verses, take its first target_n
    # verses and score.  This tells us what score an actual Quran
    # passage achieves.
    by_surah: dict[int, list[str]] = defaultdict(list)
    for v in corpus.all_verses():
        by_surah[v.surah].append(v.raw)

    quran_scores = []
    for s, verses in by_surah.items():
        if len(verses) < target_n:
            continue
        head = verses[:target_n]
        sc = score_passage(head, schedule)
        if sc["denom"] > 0:
            quran_scores.append(sc["letter_and_share_and_cv"] / sc["denom"])

    # --- 4b. Controls
    ctrls = load_controls(target_n, max_samples)
    ctrl_scores: dict[str, list[float]] = {}
    for label, samples in ctrls.items():
        vals = []
        for sample in samples:
            sc = score_passage(sample, schedule)
            if sc["denom"] > 0:
                vals.append(sc["letter_and_share_and_cv"] / sc["denom"])
        ctrl_scores[label] = vals

    return {"quran": quran_scores, "controls": ctrl_scores}


def _descr(vals: list[float]) -> str:
    a = np.asarray([v for v in vals if np.isfinite(v)])
    if a.size == 0:
        return "n=0"
    return (f"n={a.size:3d}  mean={a.mean():.3f}  sd={a.std(ddof=1):.3f}  "
            f"p50={np.median(a):.3f}  max={a.max():.3f}")


def _z(quran_vals, ctrl_vals) -> float:
    q = np.asarray(quran_vals)
    c = np.asarray(ctrl_vals)
    if c.size < 8 or q.size == 0:
        return float("nan")
    return (q.mean() - c.mean()) / c.std(ddof=1) if c.std(ddof=1) > 0 else float("nan")


def main() -> None:
    t0 = time.time()
    print("D4 — categorical rhyme-schedule match (joint letter+share+CV)")
    print("=" * 74)

    sched = quran_schedule()
    print(f"Quran schedule: {len(sched)} surahs.")
    dl_counts = Counter(row[1] for row in sched)
    print("Dominant-final-letter distribution across Quran surahs:")
    for letter, cnt in dl_counts.most_common(6):
        print(f"  {letter!r}: {cnt} surahs")
    print("  (…)")

    any_viable = []
    results = {}
    for N in (3, 5, 7, 10, 15):
        print(f"\n--- N = {N} verses ---")
        r = probe_at_n(N, sched, max_samples=400)
        print(f"  Quran self-match :  {_descr(r['quran'])}")
        zs = {}
        for lbl, vals in r["controls"].items():
            print(f"  {lbl:8s}        :  {_descr(vals)}")
            zs[lbl] = _z(r["quran"], vals)
        for lbl, z in zs.items():
            print(f"    z(Quran vs {lbl:8s}) = {z:+.3f}")
        n_strong = sum(1 for z in zs.values() if np.isfinite(z) and z >= 2.0)
        if n_strong >= 2:
            any_viable.append(N)
        results[N] = {
            "quran_n": len(r["quran"]),
            "quran_mean": float(np.mean(r["quran"])) if r["quran"] else None,
            "controls": {
                k: {
                    "n": len(v),
                    "mean": float(np.mean(v)) if v else None,
                    "sd": float(np.std(v, ddof=1)) if len(v) >= 2 else None,
                }
                for k, v in r["controls"].items()
            },
            "z": zs,
        }

    print("\nViability verdict")
    print("-" * 74)
    if any_viable:
        print(f"  VIABLE at N ∈ {any_viable} (Quran separated from ≥ 2 controls "
              f"at z ≥ 2.0).")
    else:
        print("  NOT VIABLE — categorical schedule-match does not separate "
              "Quran from controls at any tested N.")

    out_path = REPO / "docs" / "experiments" / "d4_rhyme_schedule.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "viable_at_N": any_viable,
        "results_by_N": results,
    }, indent=2, default=str))
    print(f"  Receipt: {out_path.relative_to(REPO)}")
    print(f"\nElapsed: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
