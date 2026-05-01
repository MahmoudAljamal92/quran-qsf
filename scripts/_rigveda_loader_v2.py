"""scripts/_rigveda_loader_v2.py
=====================================
Loader + universal-feature normaliser for Rigveda Saṃhitā (DharmicData
edition, Devanāgarī script). Intended for the F63 falsification test
(exp111 cross-tradition Quran-rhyme-extremum, with Rigveda added).

NOTE: The pre-existing scripts/_rigveda_sizing.py and
experiments/expP4_rigveda_deepdive use a different feature space
(LC2 path-minimality / R3, Hurst). This loader is fresh and tailored to
the F63 universal feature set (VL_CV, p_max, H_EL, etc.).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ============================================================================
# Devanagari Sanskrit normaliser
# ============================================================================
# Skeleton: consonants + independent vowels (post-NFD, after stripping
# combining marks). Excludes: vowel signs (दीर्घ a, e etc; combining
# marks), virama (्), candrabindu, anusvara/visarga (treated as diacritic
# even though some scholars argue they should be letters).
# This is the most defensible "skeleton" akin to the Arabic 28-consonant
# skeleton (which strips all diacritics).
_DEVANAGARI_LETTERS = (
    # 14 vowels (independent forms only)
    "अआइईउऊऋॠऌॡएऐओऔ"
    # 33 consonants (standard varga + semivowels + sibilants + ha)
    "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"
    # 4 less-common but standard letters
    "ळऍऎऩ"
)
_DEVANAGARI_SET = set(_DEVANAGARI_LETTERS)

# Verse separator markers in Rigveda text — these are the danda + verse
# number patterns like "॥१॥", "॥1॥", "॥4-5॥" etc. Used to split text into
# pada/verse units.
_VERSE_END_PATTERN = re.compile(r"॥\s*[\d०-९]+\s*[-–]?\s*[\d०-९]*\s*॥")


def _normalise_sanskrit(s: str) -> str:
    """Strip combining marks (vowel signs, accents, virama, anusvara/visarga,
    udatta/anudatta), then keep only Devanagari skeleton letters."""
    if not s:
        return ""
    # NFD decomposition splits combined characters into base + combining marks
    s = unicodedata.normalize("NFD", s)
    # Remove all combining marks (category Mn)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Keep only base Devanagari skeleton letters
    return "".join(c for c in s if c in _DEVANAGARI_SET)


def _split_verses(text: str) -> list[str]:
    """Split a sukta text into individual verses (padas/mantras) on the
    canonical danda+number end markers."""
    # Strategy: split on the verse-end pattern, keeping the chunks between.
    parts = _VERSE_END_PATTERN.split(text)
    # Strip empty / whitespace-only parts and trailing newlines
    verses = [p.strip() for p in parts if p.strip()]
    return verses


def load_rigveda() -> list[dict]:
    """Returns list of unit-dicts for all Rigveda sūktas across 10 mandalas.
    Each unit = one sūkta with its constituent verses (mantras).

    Schema: {"corpus": "rigveda", "label": f"RV:{m}.{s}", "verses": [...],
             "normaliser": "sanskrit"}.
    """
    out: list[dict] = []
    sa_dir = ROOT / "data" / "corpora" / "sa"
    files = sorted(sa_dir.glob("rigveda_mandala_*.json"),
                   key=lambda p: int(p.stem.split("_")[-1]))
    for fp in files:
        items = json.loads(fp.read_text(encoding="utf-8"))
        for it in items:
            mandala = it.get("mandala")
            sukta = it.get("sukta")
            text = it.get("text") or ""
            verses = _split_verses(text)
            if len(verses) < 2:
                # too short to be a real sukta unit
                continue
            out.append({
                "corpus": "rigveda",
                "label": f"RV:{mandala}.{sukta:03d}" if isinstance(sukta, int)
                          else f"RV:{mandala}.{sukta}",
                "verses": verses,
                "normaliser": "sanskrit",
            })
    return out


# ============================================================================
# Universal feature extractor (Sanskrit-aware)
# ============================================================================
def features_universal_sanskrit(unit: dict) -> dict:
    """Compute the F63 universal 5-D feature set for a Sanskrit sukta.

    Mirrors scripts._phi_universal_xtrad_sizing._features_universal,
    but uses Sanskrit normaliser.
    """
    from collections import Counter
    import math
    import gzip as gz

    verses = unit["verses"]
    # Per-verse word count
    word_counts = [len(v.split()) for v in verses]
    if not word_counts:
        raise ValueError(f"empty unit: {unit.get('label')}")
    mean_w = sum(word_counts) / len(word_counts)
    if mean_w == 0:
        vl_cv = 0.0
    else:
        var_w = sum((w - mean_w) ** 2 for w in word_counts) / len(word_counts)
        vl_cv = (var_w ** 0.5) / mean_w

    # End-letter distribution (last skeleton letter of each verse)
    ends = []
    for v in verses:
        norm = _normalise_sanskrit(v)
        if norm:
            ends.append(norm[-1])
    if not ends:
        raise ValueError(f"unit has no skeleton-letter verse endings: "
                         f"{unit.get('label')}")
    ec = Counter(ends)
    n = len(ends)
    p_max = max(ec.values()) / n
    h_el = -sum((c / n) * math.log2(c / n) for c in ec.values() if c > 0)

    # Bigram + gzip on concatenated skeleton
    skeleton = "".join(_normalise_sanskrit(v) for v in verses)
    if len(skeleton) < 2:
        bigram_distinct_ratio = 0.0
        gzip_efficiency = 1.0
    else:
        bigrams = [skeleton[i:i+2] for i in range(len(skeleton) - 1)]
        bigram_distinct_ratio = len(set(bigrams)) / max(1, len(bigrams))
        skel_bytes = skeleton.encode("utf-8")
        gz_bytes = gz.compress(skel_bytes, compresslevel=9)
        gzip_efficiency = len(gz_bytes) / max(1, len(skel_bytes))

    return {
        "VL_CV": vl_cv,
        "p_max": p_max,
        "H_EL": h_el,
        "bigram_distinct_ratio": bigram_distinct_ratio,
        "gzip_efficiency": gzip_efficiency,
        "n_verses": n,
        "n_letters_skeleton": len(skeleton),
    }


if __name__ == "__main__":
    units = load_rigveda()
    print(f"# loaded {len(units)} Rigveda sūktas across 10 mandalas")
    if units:
        sample = units[0]
        print(f"# first: {sample['label']}; n_verses = {len(sample['verses'])}")
        print(f"# first verse (first 200 chars):")
        print(f"#   {sample['verses'][0][:200]}")
        feats = features_universal_sanskrit(sample)
        print(f"# features for {sample['label']}: {feats}")

    # Sizing snapshot
    import statistics
    pmaxes = []
    hels = []
    for u in units:
        try:
            f = features_universal_sanskrit(u)
            pmaxes.append(f["p_max"])
            hels.append(f["H_EL"])
        except Exception as e:
            print(f"# WARN: feature failed for {u.get('label')}: {e}")
    if pmaxes:
        print(f"\n# === Rigveda sizing ===")
        print(f"#   n sūktas with valid features: {len(pmaxes)}")
        print(f"#   median p_max : {statistics.median(pmaxes):.4f}")
        print(f"#   median H_EL  : {statistics.median(hels):.4f}")
        print(f"#   mean   p_max : {statistics.mean(pmaxes):.4f}")
        print(f"#   mean   H_EL  : {statistics.mean(hels):.4f}")
