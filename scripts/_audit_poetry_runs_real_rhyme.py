"""scripts/_audit_poetry_runs_real_rhyme.py
=================================================
Use the flat hemistich-per-line poetry.txt to estimate the upper bound
of Arabic poetry per-poem rhyme uniformity.

Idea: in classical qasida tradition (rāwī rule), every bayt's second
hemistich ends with the rhyme letter. If poetry.txt is a flat dump of
hemistichs from many qasidas, then within each qasida, every-other-line
ends with the rhyme letter (lines 1, 3, 5, ...).

Detect "runs" of same-end-letter spaced 2 lines apart (rhyming structure)
and report.

Also: take the longest runs of same-end-letter and treat them as
"approximately one qasida" — within those, p_max should be high.
"""
from __future__ import annotations

import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_ARABIC_LETTERS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ARABIC_SET = set(_ARABIC_LETTERS_28)


def end_letter(s: str) -> str | None:
    s = s.replace("\u0640", "")
    s = _AR_DIAC.sub("", s)
    folds = {"\u0622": "\u0627", "\u0623": "\u0627", "\u0625": "\u0627",
             "\u0671": "\u0627", "\u0649": "\u064a", "\u0629": "\u0647"}
    for k, v in folds.items():
        s = s.replace(k, v)
    s = "".join(c for c in s if c in _ARABIC_SET)
    return s[-1] if s else None


lines = Path("data/corpora/ar/poetry.txt").read_text(
    encoding="utf-8").splitlines()
ends = [end_letter(L) for L in lines if L.strip()]
ends = [e for e in ends if e]
n = len(ends)
print(f"# Total hemistichs with valid end-letter: {n}")

# Pooled corpus-level p_max
ec = Counter(ends)
top_letter, top_count = ec.most_common(1)[0]
print(f"# Pooled corpus-level p_max = {top_count / n:.4f} "
      f"(letter '{top_letter}', {top_count}/{n})")

# Even-only (every-other-hemistich = candidate ‘ajuz lines that rhyme)
evens = [ends[i] for i in range(1, n, 2)]
ec_e = Counter(evens)
top_e_letter, top_e_count = ec_e.most_common(1)[0]
print(f"# Even-line-only (candidate ‘ajuz, every other hemistich) p_max = "
      f"{top_e_count / len(evens):.4f}")

# Sliding window analysis: in 50-line windows, what's the median p_max?
window_pmaxes = []
for w_start in range(0, n - 50, 25):
    w = ends[w_start:w_start + 50]
    wc = Counter(w)
    p = wc.most_common(1)[0][1] / len(w)
    window_pmaxes.append(p)
print(f"\n# 50-hemistich sliding windows (n={len(window_pmaxes)}):")
print(f"#   median p_max = {statistics.median(window_pmaxes):.4f}")
qs = statistics.quantiles(window_pmaxes, n=10)
print(f"#   p10 = {qs[0]:.4f}; p90 = {qs[8]:.4f}")

# Same but for EVERY-OTHER-LINE windows (presumed 'ajuz alternation)
even_windows = []
for w_start in range(0, len(evens) - 25, 12):
    w = evens[w_start:w_start + 25]
    wc = Counter(w)
    p = wc.most_common(1)[0][1] / len(w)
    even_windows.append(p)
print(f"\n# 25-line windows on EVEN-only (every-other-line) "
      f"(n={len(even_windows)}):")
print(f"#   median p_max = {statistics.median(even_windows):.4f}")
qs = statistics.quantiles(even_windows, n=10)
print(f"#   p10 = {qs[0]:.4f}; p90 = {qs[8]:.4f}")

# Long runs of same end-letter (treat as proxies for one qasida's
# rhyme-line accumulation)
print(f"\n# RUNS of same end-letter (length >= 30 = approx one qasida):")
runs = []
cur, length = None, 0
for e in ends:
    if e == cur:
        length += 1
    else:
        if length > 0:
            runs.append((cur, length))
        cur, length = e, 1
if length > 0:
    runs.append((cur, length))
big = sorted([r for r in runs if r[1] >= 30], key=lambda t: -t[1])
print(f"#   Number of >= 30-line same-letter runs: {len(big)}")
print(f"#   Top 10 lengths: {[r[1] for r in big[:10]]}")
print(f"#   Sum of all >=30-runs: {sum(r[1] for r in big)} hemistichs")

# In a window CONTAINING a long run, what fraction of lines end with that
# letter? If qasidas truly rhyme uniformly, in a window of ~100 hemistichs
# containing a 50-line same-letter run, p_max should be 50% (one qasida's
# rhymes are ~half the lines if non-rhyming hemistich is interleaved).
print(f"\n# Conclusion check: {top_count}/{n} = {top_count/n:.4f} pooled "
      f"means letter '{top_letter}' is overall most common. If qasidas "
      f"rhyme uniformly per-poem, the BEST case for one qasida is p_max=1.0 "
      f"(if poetry.txt is per-bayt) or p_max=0.5 (if poetry.txt is "
      f"per-hemistich and only ‘ajuz rhymes). The 50-hemistich-window "
      f"median p_max gives an empirical upper bound from real data.")
