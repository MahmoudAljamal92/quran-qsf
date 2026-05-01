"""
expP14_cross_script_dominant_letter/run.py
==========================================
Cross-script clean dominant-terminal-letter table for the v7.9-cand
§4.41.x supplementary.

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP14_cross_script_dominant_letter/expP14_cross_script_dominant_letter.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)

EXP = "expP14_cross_script_dominant_letter"

# Combining marks / punctuation we treat as non-alphabetic for the
# "natural letter" question. (Pali transliteration uses ॥ / .; some
# Arabic units use punctuation around verses.)
NON_ALPHA_PUNCT = set(".,;:!?\"'()[]{}-—–…॥।。、，；：！？「」『』〈〉«»‹›")


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _terminal_natural_letter(verse: str) -> str | None:
    """Return the last unicode-alphabetic character that is NOT a combining
    mark or punctuation. None if no such letter exists."""
    for c in reversed(verse.strip()):
        # Skip combining marks / spacing modifiers
        cat = unicodedata.category(c)
        if cat.startswith("M"):
            continue
        if c in NON_ALPHA_PUNCT:
            continue
        if c.isalpha():
            return c
    return None


def _per_corpus_stats(units: list) -> dict:
    finals = []
    for u in units:
        for v in u.verses:
            ch = _terminal_natural_letter(v)
            if ch is not None:
                finals.append(ch)
    if not finals:
        return {"n_finals": 0, "p_max": None, "top_letter": None, "top5": []}
    cnt = Counter(finals)
    tot = sum(cnt.values())
    top = cnt.most_common(5)
    p_max = top[0][1] / tot
    return {
        "n_finals": tot,
        "n_distinct": len(cnt),
        "p_max": float(p_max),
        "top_letter": top[0][0],
        "top_letter_codepoint": f"U+{ord(top[0][0]):04X}",
        "top5": [
            {"letter": l, "codepoint": f"U+{ord(l):04X}", "count": c, "p": c / tot}
            for l, c in top
        ],
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    print(f"[{EXP}] Per-corpus terminal-letter dominance:")
    table: dict[str, dict] = {}
    for name, units in CORPORA.items():
        stats = _per_corpus_stats(units)
        table[name] = stats
        if stats["p_max"] is not None:
            print(f"[{EXP}]   {name:20s} n_finals={stats['n_finals']:>7d}  "
                  f"top {stats['top_letter']} ({stats['top_letter_codepoint']}) "
                  f"p_max={stats['p_max']:.4f}")
        else:
            print(f"[{EXP}]   {name:20s} (empty)")

    # Verdict on Quran ن-dominance ratio
    quran_pmax = table.get("quran", {}).get("p_max")
    pmaxes_arabic_other = []
    for k, v in table.items():
        if k == "quran":
            continue
        if v.get("p_max") is None:
            continue
        # Restrict ratio claim to Arabic-corpus comparators (avoiding
        # transliteration-marker dominance in Pali/Vedic/Avesta).
        if k in ("hadith_bukhari", "poetry_jahili", "poetry_islami",
                 "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"):
            pmaxes_arabic_other.append((k, v["p_max"]))
    pmaxes_arabic_other.sort(key=lambda x: -x[1])
    next_arabic = pmaxes_arabic_other[0] if pmaxes_arabic_other else (None, None)
    ratio = (quran_pmax / next_arabic[1]) if (quran_pmax and next_arabic[1]) else None

    if ratio is None:
        verdict = "INSUFFICIENT_DATA"
    elif ratio >= 4.0:
        verdict = "QURAN_DOMINANCE_CONFIRMED"
    elif ratio >= 2.0:
        verdict = "QURAN_DOMINANCE_PARTIAL"
    else:
        verdict = "QURAN_DOMINANCE_REJECTED"

    print(f"[{EXP}] Quran p_max = {quran_pmax}  next-Arabic = {next_arabic}  "
          f"ratio = {ratio}  -> {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "table": table,
        "quran_p_max": quran_pmax,
        "next_arabic_p_max": {"corpus": next_arabic[0], "p_max": next_arabic[1]},
        "ratio_quran_over_next_arabic": ratio,
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
