"""scripts/_audit_poetry_unit_definition.py
==============================================
Critical audit: does the Arabic poetry CSV preserve real verse-line
boundaries (one bayt or hemistich per row), or is each `poem` a flat string
that gets chunked into 7-word blocks for analysis?

If chunked: p_max(poetry) is NOT comparable to p_max(Quran) which uses
real ayat boundaries. F63 may be on a unit-mismatch confound.

This script samples the CSV, inspects the poem field, looks for any line
delimiters or boundary markers, and reports.
"""
from __future__ import annotations

import csv
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "corpora" / "ar" / "poetry_raw.csv"

print(f"# audit: {CSV}")
print(f"# size : {CSV.stat().st_size:,} bytes")

with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    print(f"# columns : {reader.fieldnames}")
    cnt_total = 0
    delim_counts: Counter = Counter()
    delim_chars = ["\n", "\t", "*", "~", "|", "/", ";", "،", "؛", "."]
    sample_rows = []
    for i, row in enumerate(reader):
        cnt_total += 1
        poem = (row.get("poem") or "")
        for ch in delim_chars:
            n = poem.count(ch)
            if n > 0:
                delim_counts[ch] += n
        if i < 3:
            sample_rows.append((i, row))
    print(f"# total rows: {cnt_total}")
    print()
    print("# delimiter character occurrence counts across ALL poems:")
    for ch, n in delim_counts.most_common():
        cat = unicodedata.category(ch)
        print(f"#   {ch!r:>10s}  count={n:>10d}  unicat={cat}")
    print()
    for (i, row) in sample_rows:
        poem = (row.get("poem") or "")
        print(f"# === sample poem {i} (era={row.get('era')!r}, "
              f"poem_id={row.get('poem_id')!r}) ===")
        print(f"#   chars: {len(poem):>8d}  words: {len(poem.split()):>6d}")
        print(f"#   first 400 chars (repr):")
        print(f"#   {repr(poem[:400])}")
        print()

# Hypothesis check: if poems have NO line markers, each "poem" is flat.
# The locked loader chunks into 7-word blocks. Quran averages how many
# words per verse?
print("# === Quran verse-length comparison ===")
quran = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
n_verses = 0
total_words = 0
verse_word_lens = []
for line in quran.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    parts = line.split("|", 2)
    if len(parts) != 3:
        continue
    txt = parts[2].strip()
    if not txt:
        continue
    n_verses += 1
    nw = len(txt.split())
    verse_word_lens.append(nw)
    total_words += nw
print(f"#   total Quran verses: {n_verses}")
print(f"#   mean words/verse  : {total_words/n_verses:.2f}")
import statistics as stx
print(f"#   median words/verse: {stx.median(verse_word_lens):.1f}")
print(f"#   p25 / p75         : "
      f"{stx.quantiles(verse_word_lens, n=4)[0]:.1f} / "
      f"{stx.quantiles(verse_word_lens, n=4)[2]:.1f}")
print()

# Now: per-Arabic-poetry-poem, what does p_max look like AT THE POEM LEVEL
# under the existing 7-word chunking, vs at the unit-as-whole-poem level?
import re
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_ARABIC_LETTERS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ARABIC_SET = set(_ARABIC_LETTERS_28)

def normalise(s: str) -> str:
    s = s.replace("\u0640", "")
    s = _AR_DIAC.sub("", s)
    s = (s.replace("\u0622", "\u0627")
          .replace("\u0623", "\u0627")
          .replace("\u0625", "\u0627")
          .replace("\u0671", "\u0627")
          .replace("\u0649", "\u064a")
          .replace("\u0629", "\u0647"))
    return "".join(c for c in s if c in _ARABIC_SET)

print("# === per-poem p_max under 7-word chunking vs alternative chunking ===")
print("# (compare what F63 measures vs what a real qasida rhyme should look like)")
print()
n_done = 0
chunked_pmax = []
last3word_pmax = []  # alternative: split on every 3 words (closer to a hemistich)
realbayt_pmax = []   # split on every 14 words (1 bayt = 2 hemistichs ~ 14 words)
with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        era = (row.get("era") or "").strip()
        if era not in (
            "العصر الجاهلي", "المخضرمون",
            "العصر الاسلامي", "العصر الاموي", "العصر العباسي",
        ):
            continue
        poem = (row.get("poem") or "").strip()
        if not poem:
            continue
        ws = poem.split()
        if len(ws) < 35:
            continue
        n_done += 1
        for chunk_size, dest in [(7, chunked_pmax),
                                 (3, last3word_pmax),
                                 (14, realbayt_pmax)]:
            verses = [" ".join(ws[k:k+chunk_size])
                      for k in range(0, len(ws), chunk_size)]
            ends = []
            for v in verses:
                norm = normalise(v)
                if norm:
                    ends.append(norm[-1])
            if not ends:
                continue
            top = Counter(ends).most_common(1)[0][1]
            dest.append(top / len(ends))
        if n_done >= 200:
            break

import statistics
print(f"# Sample of {n_done} qasidas; per-poem p_max distribution:")
for label, vals in [
    ("CURRENT 7-word chunking (locked F63 unit)", chunked_pmax),
    ("3-word chunking (smaller unit)            ", last3word_pmax),
    ("14-word chunking (real-bayt unit)         ", realbayt_pmax),
]:
    if not vals:
        continue
    print(f"#   {label}: n={len(vals)}; "
          f"mean={statistics.mean(vals):.4f}; "
          f"median={statistics.median(vals):.4f}; "
          f"p10={statistics.quantiles(vals, n=10)[0]:.4f}; "
          f"p90={statistics.quantiles(vals, n=10)[8]:.4f}")
print()
print("# CONCLUSION:")
print("#   If the medians under different chunkings are wildly different,")
print("#   then 7-word chunking is an arbitrary unit choice that may")
print("#   not capture qasida-level rhyme. F63's poetry comparison")
print("#   needs a different unit definition.")
