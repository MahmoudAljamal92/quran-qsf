"""
expP9_v79_batch_diagnostics/run_N7_noon_forensics.py
====================================================
Morphological forensic analysis of the Quran's verse-final ن-dominance.

For each of the ~3 100 Quranic verses ending in ن (50.1 % of 6 236), extract
the verse-final word and run the CamelTools MorphologyAnalyzer. Categorise
the analyses to determine whether ن-dominance is (a) the Arabic plural
masculine -īna / -ūna case ending, (b) a 1p pronoun suffix -nā / -nī,
(c) verbal endings, or (d) deliberate rhyme choice on roots that happen
to terminate in ن.

Compare against the Arabic Bible's ن-final words as control.

Writes:
  results/experiments/expP9_v79_batch_diagnostics/N7_noon_morphology.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import safe_output_dir, self_check_begin, self_check_end  # noqa: E402
from src import raw_loader  # noqa: E402

EXP = "expP9_v79_batch_diagnostics"


def _verse_final_word(v: str) -> str | None:
    """Last whitespace-delimited token of a verse, stripped."""
    parts = v.strip().split()
    if not parts:
        return None
    last = parts[-1]
    # Strip Arabic punctuation marks (e.g. trailing diacritics already in text)
    while last and last[-1] in '۝،؟!.,؛':
        last = last[:-1]
    return last if last else None


def _categorise(analysis: dict) -> str:
    """Categorise a CamelTools analysis dict by its grammatical role.

    Categories (mutually exclusive):
      'plural_masc_genitive': sound masc plural -īna (num=p, gen=m, cas=g)
      'plural_masc_nominative': sound masc plural -ūna (num=p, gen=m, cas=n)
      'pron_suffix_1p': enclitic 1p pronoun -nā / -nī
      'verb_pl_3p_or_2p': verb conjugation ending in ن
      'energetic_emphatic': energetic / emphatic verb ending
      'noun_sing_term_n': lexically-terminal-ن noun (e.g. لا, إن, لكن style)
      'demonstrative_or_pron': inherent ن in demonstratives / pronouns
      'other': fallthrough
    """
    pos = analysis.get('pos', '')
    num = analysis.get('num', '')
    gen = analysis.get('gen', '')
    cas = analysis.get('cas', '')
    enc0 = analysis.get('enc0', '0')
    prc0 = analysis.get('prc0', '0')

    if enc0 in ('1p_dobj', '1p_poss', '1p_pron') or '1p' in str(enc0):
        return 'pron_suffix_1p'
    if pos in ('noun', 'adj', 'noun_prop'):
        if num == 'p' and gen == 'm':
            if cas == 'g':
                return 'plural_masc_genitive'
            elif cas == 'n':
                return 'plural_masc_nominative'
            else:
                return 'plural_masc_other_case'
        if num == 'd' and gen == 'm':
            return 'dual_masc'
        return 'noun_sing_term_n'
    if pos in ('verb', 'verb_pseudo'):
        if num == 'p':
            return 'verb_pl_3p_or_2p'
        return 'verb_other'
    if pos in ('pron', 'pron_dem', 'pron_rel'):
        return 'demonstrative_or_pron'
    return 'other'


def _gather_noon_words(units, max_units: int | None = None) -> list[str]:
    """Collect verse-final words ending in ن (or ـن with diacritics)."""
    out = []
    for u in units[:max_units] if max_units else units:
        for v in u.verses:
            w = _verse_final_word(v)
            if not w:
                continue
            # Strip trailing diacritics to test the bare letter
            stripped = ''.join(c for c in w if "\u0621" <= c <= "\u064A")
            if stripped and stripped[-1] == "\u0646":  # ن
                out.append(w)
    return out


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    print(f"[{EXP}] N7: ن-dominance morphological forensics")

    print(f"[{EXP}] Loading CamelTools MorphologyAnalyzer ...")
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.utils.dediac import dediac_ar
    db = MorphologyDB.builtin_db()
    analyzer = Analyzer(db)
    print(f"[{EXP}] CamelTools loaded.")

    print(f"[{EXP}] raw_loader.load_all() ...")
    CORPORA = raw_loader.load_all(include_extras=True,
                                   include_cross_lang=False,
                                   include_cross_tradition=False)

    # Quran ن-final words
    q_units = CORPORA.get("quran", [])
    quran_noon = _gather_noon_words(q_units)
    print(f"[{EXP}] Quran ن-final verse words: {len(quran_noon)}")

    # Arabic-Bible ن-final words (control)
    bible_units = CORPORA.get("arabic_bible", [])
    bible_noon = _gather_noon_words(bible_units, max_units=300)
    print(f"[{EXP}] Arabic-Bible ن-final verse words (sampled): "
          f"{len(bible_noon)}")

    def analyse(words: list[str], label: str) -> dict:
        cats = Counter()
        unique_lex = Counter()
        unanalysed = 0
        ambiguous = 0
        sample_per_cat: dict[str, list[str]] = defaultdict(list)
        for w in words:
            try:
                w_dediac = dediac_ar(w)
                results = analyzer.analyze(w_dediac)
            except Exception:
                results = []
            if not results:
                cats['unanalysable'] += 1
                unanalysed += 1
                if len(sample_per_cat['unanalysable']) < 10:
                    sample_per_cat['unanalysable'].append(w)
                continue
            if len(results) > 1:
                ambiguous += 1
            # Take the most-frequent category across all analyses
            sub_cats = Counter(_categorise(r) for r in results)
            top_cat = sub_cats.most_common(1)[0][0]
            cats[top_cat] += 1
            lex = results[0].get('lex', '')
            if lex:
                unique_lex[lex] += 1
            if len(sample_per_cat[top_cat]) < 10:
                sample_per_cat[top_cat].append(w_dediac)
        n = len(words)
        cat_pct = {k: (v, round(100 * v / n, 2)) for k, v in cats.most_common()}
        return {
            "label": label,
            "n_words": n,
            "category_counts_and_pct": cat_pct,
            "n_unanalysable": unanalysed,
            "n_ambiguous": ambiguous,
            "top_lexemes": dict(unique_lex.most_common(20)),
            "sample_per_category": {k: v for k, v in sample_per_cat.items()},
        }

    print(f"\n[{EXP}] === Quran ن-final morphological breakdown ===")
    quran_res = analyse(quran_noon, "quran")
    for cat, (count, pct) in quran_res["category_counts_and_pct"].items():
        print(f"[{EXP}]   {cat:32s} n={count:5d}  ({pct:5.2f} %)")

    print(f"\n[{EXP}] === Arabic-Bible ن-final morphological breakdown ===")
    bible_res = analyse(bible_noon, "arabic_bible")
    for cat, (count, pct) in bible_res["category_counts_and_pct"].items():
        print(f"[{EXP}]   {cat:32s} n={count:5d}  ({pct:5.2f} %)")

    # Headline interpretation
    q_pct = quran_res["category_counts_and_pct"]
    plural_total_pct = (
        q_pct.get('plural_masc_genitive', (0, 0))[1]
        + q_pct.get('plural_masc_nominative', (0, 0))[1]
        + q_pct.get('plural_masc_other_case', (0, 0))[1]
    )
    pron_pct = q_pct.get('pron_suffix_1p', (0, 0))[1]
    verb_pct = (q_pct.get('verb_pl_3p_or_2p', (0, 0))[1]
                + q_pct.get('verb_other', (0, 0))[1])
    if plural_total_pct >= 70:
        verdict = "MORPHOLOGICAL_plural_dominant"
    elif plural_total_pct >= 50:
        verdict = "MORPHOLOGICAL_plural_majority"
    elif plural_total_pct + pron_pct >= 60:
        verdict = "MORPHOLOGICAL_mixed"
    else:
        verdict = "STYLISTIC_rhyme_choice_dominant"

    print(f"\n[{EXP}] Quran ن-final: plural-marker total = "
          f"{plural_total_pct:.1f} %, 1p-pronoun = {pron_pct:.1f} %, "
          f"verb = {verb_pct:.1f} %")
    print(f"[{EXP}] verdict = {verdict}")

    payload = {
        "experiment": EXP,
        "schema_version": 1,
        "payload_tag": "N7_noon_morphology",
        "frozen_constants": {
            "min_verses": 2,
        },
        "quran_breakdown": quran_res,
        "arabic_bible_breakdown": bible_res,
        "headline_pcts": {
            "plural_masc_total_pct": plural_total_pct,
            "pron_suffix_1p_pct": pron_pct,
            "verb_total_pct": verb_pct,
        },
        "verdict": verdict,
        "interpretation_key": (
            "MORPHOLOGICAL_plural_dominant means >= 70% of ن-finals are sound "
            "plural masc -īna/-ūna; MORPHOLOGICAL_plural_majority means "
            "50-70%; MORPHOLOGICAL_mixed means plural+pronoun together >= 60% "
            "but plural alone < 50%; STYLISTIC_rhyme_choice_dominant means "
            "the bulk of ن-finals are not -īna/-ūna case endings, suggesting "
            "deliberate rhyme choice on lexically-terminal-ن roots."
        ),
        "runtime_seconds": round(time.time() - t0, 2),
    }
    p = out / "N7_noon_morphology.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=True)
    print(f"\n[{EXP}] wrote {p}")
    print(f"[{EXP}] runtime = {payload['runtime_seconds']} s")
    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
