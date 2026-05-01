"""Audit check: verify Quran/Bible/Hadith ن rates."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from collections import Counter
from src import raw_loader

CORPORA = raw_loader.load_all(include_extras=True,
                               include_cross_lang=False,
                               include_cross_tradition=False)


def verse_final_letter(v):
    s = v.strip()
    for c in reversed(s):
        if '\u0621' <= c <= '\u064A':
            return c
    return None


NOON = '\u0646'  # ن
ALIF = '\u0627'  # ا


def stats(units, label):
    fin = []
    for u in units:
        for v in u.verses:
            f = verse_final_letter(v)
            if f:
                fin.append(f)
    c = Counter(fin)
    n = sum(c.values())
    p_n = c[NOON] / n if n else 0
    p_a = c[ALIF] / n if n else 0
    print(f'{label:20s} n={n:6d}  p(noon)={p_n:.4f}  '
          f'p(alif)={p_a:.4f}  dominant={c.most_common(1)[0][0]} '
          f'@ {c.most_common(1)[0][1]/n:.4f}')
    return c, n


for name in ['quran', 'arabic_bible', 'poetry_jahili', 'poetry_islami',
             'poetry_abbasi', 'ksucca', 'hindawi']:
    if name in CORPORA:
        stats(CORPORA[name], name)

# Hadith separately
hadith = raw_loader.load_hadith_bukhari()
stats(hadith, 'hadith_bukhari')
