"""scripts/_audit_poetry_verses_column.py
=============================================
The CSV has a `verses` column. The current loader ignores it.
Inspect what it contains and compute per-poem p_max under that
representation."""
from __future__ import annotations

import csv
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "corpora" / "ar" / "poetry_raw.csv"

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


print("# === inspect 'verses' column structure ===")
with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 3:
            break
        verses = (row.get("verses") or "")
        poem = (row.get("poem") or "")
        print(f"# --- poem {i} (era={row.get('era')!r}) ---")
        print(f"#   poem chars  : {len(poem):>8d}")
        print(f"#   verses chars: {len(verses):>8d}")
        print(f"#   verses[:600]: {repr(verses[:600])}")
        print()

# Key question: does the `verses` column contain newlines / explicit
# delimiters between bayts?
print("# === delimiter survey on `verses` column across ALL poems ===")
with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    total = 0
    counts: Counter = Counter()
    for row in reader:
        v = row.get("verses") or ""
        total += 1
        for ch in ("\n", "\t", "*", "~", "|", "/", "؛", "،", ".", "#"):
            n = v.count(ch)
            if n:
                counts[ch] += n
print(f"# total rows: {total}")
for ch, n in counts.most_common():
    print(f"#   {ch!r:>6s}  count={n:>10d}")

# Now compute per-poem p_max using `verses` column under several
# delimiter hypotheses
print()
print("# === per-poem p_max under different verses-column parsings ===")
n_done = 0
results: dict[str, list[float]] = {
    "current_7word_on_poem": [],
    "verses_split_newline":  [],
    "verses_split_pipe":     [],
    "verses_split_python_eval_if_list": [],
    "verses_split_starsplit": [],
}
ERA_OK = {"العصر الجاهلي", "المخضرمون",
          "العصر الاسلامي", "العصر الاموي", "العصر العباسي"}

import ast

with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if (row.get("era") or "").strip() not in ERA_OK:
            continue
        poem = (row.get("poem") or "").strip()
        verses_raw = (row.get("verses") or "").strip()
        ws = poem.split()
        if len(ws) < 35:
            continue
        n_done += 1

        # Method A: current locked F63 unit (7-word chunks of `poem`)
        v_a = [" ".join(ws[k:k+7]) for k in range(0, len(ws), 7)]
        # Method B: `verses` split on newline
        v_b = [v.strip() for v in verses_raw.split("\n") if v.strip()]
        # Method C: `verses` split on pipe |
        v_c = [v.strip() for v in verses_raw.split("|") if v.strip()]
        # Method D: try Python list literal
        v_d = []
        try:
            parsed = ast.literal_eval(verses_raw) if verses_raw else None
            if isinstance(parsed, list):
                v_d = [str(v).strip() for v in parsed if str(v).strip()]
        except (SyntaxError, ValueError):
            pass
        # Method E: split on '*'
        v_e = [v.strip() for v in verses_raw.split("*") if v.strip()]

        for label, vs in [
            ("current_7word_on_poem",         v_a),
            ("verses_split_newline",          v_b),
            ("verses_split_pipe",             v_c),
            ("verses_split_python_eval_if_list", v_d),
            ("verses_split_starsplit",        v_e),
        ]:
            if len(vs) < 5:
                continue
            ends = []
            for v in vs:
                norm = normalise(v)
                if norm:
                    ends.append(norm[-1])
            if not ends:
                continue
            top = Counter(ends).most_common(1)[0][1]
            results[label].append(top / len(ends))
        if n_done >= 500:
            break

print(f"# Sample of {n_done} qasidas:")
for label, vals in results.items():
    if not vals:
        print(f"#   {label:<40s}: NO VALID UNITS")
        continue
    print(f"#   {label:<40s}: n={len(vals):>4d}; "
          f"mean={statistics.mean(vals):.4f}; "
          f"median={statistics.median(vals):.4f}; "
          f"p10={statistics.quantiles(vals, n=10)[0]:.4f}; "
          f"p90={statistics.quantiles(vals, n=10)[8]:.4f}")
print()
print("# === SHOW one parsed-verses sample ===")
with CSV.open("r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if (row.get("era") or "").strip() not in ERA_OK:
            continue
        verses_raw = (row.get("verses") or "").strip()
        if not verses_raw:
            continue
        try:
            parsed = ast.literal_eval(verses_raw)
            if isinstance(parsed, list) and len(parsed) >= 5:
                print(f"# Parsed list: type={type(parsed).__name__}, "
                      f"len={len(parsed)}")
                for j, v in enumerate(parsed[:6]):
                    print(f"#   verse {j}: {repr(str(v)[:120])}")
                break
        except Exception:
            continue
