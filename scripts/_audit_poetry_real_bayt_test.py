"""scripts/_audit_poetry_real_bayt_test.py
==================================================
Honest test of the user's V3.9 critique: when Arabic poetry is chunked
into REAL-bayt-aligned units (using the per-poem bayt-count from the
poetry_raw.csv `verses` column to drive the chunk count), does Arabic
poetry beat the Quran on per-poem p_max?

If yes: F63 scope must be downgraded from "Quran is the cross-tradition
rhyme-extremum" to "Quran is the cross-tradition NON-RHYME-GENRE rhyme-
extremum" (or similar).

If no (unlikely given classical qasida tradition): we have an interesting
falsification of the literature-traditional belief that qasidas rhyme
uniformly.
"""
from __future__ import annotations

import csv
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_ARABIC_LETTERS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ARABIC_SET = set(_ARABIC_LETTERS_28)


def normalise(s: str) -> str:
    s = s.replace("\u0640", "")
    s = _AR_DIAC.sub("", s)
    folds = {"\u0622": "\u0627", "\u0623": "\u0627", "\u0625": "\u0627",
             "\u0671": "\u0627", "\u0649": "\u064a", "\u0629": "\u0647"}
    for k, v in folds.items():
        s = s.replace(k, v)
    return "".join(c for c in s if c in _ARABIC_SET)


CSV = ROOT / "data" / "corpora" / "ar" / "poetry_raw.csv"
ERA_OK = {"العصر الجاهلي", "المخضرمون", "العصر الاسلامي",
          "العصر الاموي", "العصر العباسي"}

print("# === Audit: Arabic poetry per-qasida p_max with REAL bayt count ===")
print("# Method: each poem's flat words are split into N equal chunks where")
print("#         N = verses_count from CSV `verses` column. Each chunk should")
print("#         end approximately at a bayt boundary; per-chunk end letter")
print("#         should be the rhyme letter for ≈ all chunks (since qasidas")
print("#         rhyme uniformly).")
print()

results: dict[str, list[float]] = {
    "synthetic_7word_chunks": [],     # the F63 confounded baseline
    "verses_count_chunks": [],        # NEW: bayt-aligned chunks
    "verses_count_chunks_no_bayt1": [],  # drop matla' (which is itself rhymed)
}
poem_metadata = []

with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        era = (row.get("era") or "").strip()
        if era not in ERA_OK:
            continue
        poem = (row.get("poem") or "").strip()
        verses_field = (row.get("verses") or "0").strip()
        try:
            n_bayts = int(verses_field)
        except ValueError:
            continue
        if not poem or n_bayts < 5:
            continue
        words = poem.split()
        if len(words) < 35:
            continue

        # Method A: synthetic 7-word chunks (F63 baseline)
        chunks_a = [" ".join(words[k:k+7]) for k in range(0, len(words), 7)]
        # Method B: split into n_bayts equal-word chunks (real-bayt-aligned)
        chunk_size_b = max(1, len(words) // n_bayts)
        chunks_b = [" ".join(words[k:k+chunk_size_b])
                    for k in range(0, len(words), chunk_size_b)]
        # Trim any tiny final chunk that's < 1/2 chunk-size (edge of poem)
        if chunks_b and len(chunks_b[-1].split()) < chunk_size_b // 2:
            chunks_b = chunks_b[:-1]

        for label, chunks in [("synthetic_7word_chunks", chunks_a),
                              ("verses_count_chunks", chunks_b)]:
            if len(chunks) < 5:
                continue
            ends = []
            for c in chunks:
                norm = normalise(c)
                if norm:
                    ends.append(norm[-1])
            if not ends:
                continue
            top = Counter(ends).most_common(1)[0][1]
            results[label].append(top / len(ends))

        # Method C: same as B but skip the first chunk (matla' may inflate)
        if len(chunks_b) >= 6:
            ends_no1 = []
            for c in chunks_b[1:]:
                norm = normalise(c)
                if norm:
                    ends_no1.append(norm[-1])
            if ends_no1:
                top = Counter(ends_no1).most_common(1)[0][1]
                results["verses_count_chunks_no_bayt1"].append(
                    top / len(ends_no1))

        poem_metadata.append({
            "id": row.get("poem_id"),
            "era": era,
            "n_words": len(words),
            "n_bayts_declared": n_bayts,
            "words_per_bayt": len(words) / n_bayts,
        })

# Summary
print("# Comparison: synthetic 7-word chunking vs real-bayt-aligned chunking\n")
print(f"# {'method':<35s}  {'n':>5s}  {'mean':>7s}  {'median':>7s}  "
      f"{'p10':>7s}  {'p50':>7s}  {'p90':>7s}")
for label, vals in results.items():
    if not vals:
        continue
    qs = statistics.quantiles(vals, n=10)
    print(f"# {label:<35s}  {len(vals):>5d}  "
          f"{statistics.mean(vals):>7.4f}  "
          f"{statistics.median(vals):>7.4f}  "
          f"{qs[0]:>7.4f}  {statistics.median(vals):>7.4f}  "
          f"{qs[8]:>7.4f}")

print()
print(f"# Quran reference values (from F63 / exp109):")
print(f"#   Quran median p_max (per surah, real ayat) = 0.7273")
print(f"#   Quran median H_EL  (per surah, real ayat) = 0.9685 bits")
print()

# Verdict
ours = results["verses_count_chunks"]
if ours:
    poetry_med = statistics.median(ours)
    print(f"# Poetry median per-qasida p_max under real-bayt-aligned chunking: "
          f"{poetry_med:.4f}")
    if poetry_med > 0.7273:
        print(f"# >>> POETRY BEATS QURAN <<< — F63 must be downgraded.")
        print(f"#     Margin: poetry {poetry_med:.4f} vs Quran 0.7273; "
              f"poetry wins by {poetry_med / 0.7273:.2f}×.")
    else:
        print(f"# >>> Quran still wins <<< — poetry per-qasida p_max "
              f"{poetry_med:.4f} < Quran 0.7273. F63 stands (against poetry "
              f"under this chunking).")

# Sanity check: examine bayt size distribution
print()
print(f"# Bayt-size sanity check (words per bayt):")
wpb = [m["words_per_bayt"] for m in poem_metadata]
qs = statistics.quantiles(wpb, n=10)
print(f"#   median: {statistics.median(wpb):.2f}, p10={qs[0]:.2f}, p90={qs[8]:.2f}")
print(f"#   ('bayt' in classical Arabic poetry typically has 8-16 words)")
