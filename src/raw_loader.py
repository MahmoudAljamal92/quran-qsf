# -*- coding: utf-8 -*-
"""
src/raw_loader.py
=================
Clean loaders that read every corpus directly from its raw file in
data/corpora/<lang>/.  DOES NOT read any pickle checkpoint.

Each loader returns a list of `Unit(corpus, label, verses)`. Every unit
must pass a per-unit sanity invariant (min verses, min distinct words),
enforced in `src/verify_corpora.py`.

Canonical corpora (Arabic, data/corpora/ar/):
    quran           -- 114 surahs                    (quran_bare.txt)
    poetry_jahili   -- pre-Islamic + Mukhadramun     (poetry_raw.csv)
    poetry_islami   -- Early Islamic + Umayyad       (poetry_raw.csv)
    poetry_abbasi   -- Abbasid                        (poetry_raw.csv)
    ksucca          -- historical prose chunks       (ksucca.txt, by 'ذكر' marker)
    arabic_bible    -- Bible chapters                (arabic_bible.xlsx)
    hadith_bukhari  -- Sahih al-Bukhari by chapter   (hadith.json)
    hindawi         -- modern Arabic stories         (hindawi.txt)

Cross-language (data/corpora/<el|he>/):
    iliad_greek     -- Homer Iliad, 24 books         (el/iliad_perseus.xml)
    greek_nt        -- NT 27 books                   (el/opengnt_v3_3.csv)
    hebrew_tanakh   -- Tanakh WLC                     (he/tanakh_wlc.txt)
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
DATA_AR = ROOT / "data" / "corpora" / "ar"
DATA_HE = ROOT / "data" / "corpora" / "he"
DATA_EL = ROOT / "data" / "corpora" / "el"
DATA_PI = ROOT / "data" / "corpora" / "pi"   # Pali (SuttaCentral)
DATA_SA = ROOT / "data" / "corpora" / "sa"   # Sanskrit / Vedic
DATA_AE = ROOT / "data" / "corpora" / "ae"   # Avestan
ILIAD = DATA_EL / "iliad_perseus.xml"
GREEK_NT = DATA_EL / "opengnt_v3_3.csv"
HEBREW_TANAKH = DATA_HE / "tanakh_wlc.txt"
POETRY_CSV = DATA_AR / "poetry_raw.csv"

# Back-compat alias (older code referenced DATA directly)
DATA = DATA_AR


# ---------------------------------------------------------------- types
@dataclass
class Unit:
    corpus: str
    label: str
    verses: list[str] = field(default_factory=list)

    def n_verses(self) -> int:
        return len(self.verses)

    def n_words(self) -> int:
        return sum(len(v.split()) for v in self.verses)


# ---------------------------------------------------------------- utils
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_AR_TATWEEL = "\u0640"


def _clean_arabic(t: str) -> str:
    """Normalise Arabic text: drop tatweel, collapse whitespace.
    DIACRITICS ARE KEPT (we strip only at the feature-extraction step)."""
    t = t.replace(_AR_TATWEEL, "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _is_mostly_arabic(t: str, min_ratio: float = 0.4) -> bool:
    if not t:
        return False
    arab = sum(1 for c in t if "\u0600" <= c <= "\u06FF")
    alpha = sum(1 for c in t if c.isalpha())
    return alpha > 0 and arab / max(alpha, 1) >= min_ratio


# ---------------------------------------------------------------- Quran
def load_quran_bare(path: Path = DATA / "quran_bare.txt") -> list[Unit]:
    """
    Return 114 surahs.  File format: 'S|V|text'.
    """
    units: dict[int, Unit] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            sid = int(parts[0])
            _vid = parts[1]
            verse = _clean_arabic(parts[2])
            if not verse:
                continue
            u = units.setdefault(
                sid, Unit(corpus="quran", label=f"Q:{sid:03d}")
            )
            u.verses.append(verse)
    return [units[k] for k in sorted(units)]


# ---------------------------------------------------------------- Poetry
_ERA_MAP = {
    "العصر الجاهلي": "poetry_jahili",
    "المخضرمون": "poetry_jahili",
    "العصر الاسلامي": "poetry_islami",
    "العصر الاموي": "poetry_islami",
    "العصر العباسي": "poetry_abbasi",
}


def _split_poem_into_verses(
    poem: str, words_per_verse: int = 7
) -> list[str]:
    """
    Classical Arabic poems in the CSV come as one long string.
    We split by whitespace into words, then chunk every
    `words_per_verse` words as one "verse" (~= hemistich).
    """
    w = poem.split()
    if not w:
        return []
    out = []
    for i in range(0, len(w), words_per_verse):
        chunk = " ".join(w[i:i + words_per_verse])
        if chunk:
            out.append(chunk)
    return out


def load_poetry_by_era(
    csv_path: Path = POETRY_CSV,
    words_per_verse: int = 7,
    min_verses: int = 5,
) -> dict[str, list[Unit]]:
    """
    Returns {'poetry_jahili': [...], 'poetry_islami': [...], 'poetry_abbasi': [...]}.
    Each poem in the CSV becomes one Unit; the poem's text is split into
    `words_per_verse`-word hemistichs to create the verse list.
    """
    out: dict[str, list[Unit]] = {
        "poetry_jahili": [], "poetry_islami": [], "poetry_abbasi": []
    }
    with csv_path.open("r", encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f)
        for i, row in enumerate(rd):
            era_ar = (row.get("era") or "").strip()
            corpus = _ERA_MAP.get(era_ar)
            if not corpus:
                continue
            poem_text = _clean_arabic(row.get("poem") or "")
            if not poem_text or not _is_mostly_arabic(poem_text):
                continue
            verses = _split_poem_into_verses(poem_text, words_per_verse)
            if len(verses) < min_verses:
                continue
            label = f"{corpus}:{row.get('poem_id') or i}"
            out[corpus].append(Unit(corpus=corpus, label=label, verses=verses))
    return out


# ---------------------------------------------------------------- Ksucca
_DHIKR_RE = re.compile(r"^\s*ذكر\b")


def load_ksucca(
    path: Path = DATA / "ksucca.txt", min_verses: int = 5
) -> list[Unit]:
    """
    Chunk by 'ذكر ...' chapter markers (historical Arabic 'mention of...').
    Each chapter is one Unit whose verses are the lines that follow it up
    to the next 'ذكر' line.
    """
    out: list[Unit] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    # strip BOM
    raw = raw.lstrip("\ufeff")
    lines = [ln.rstrip("\r") for ln in raw.split("\n")]
    # Find chapter boundaries
    boundaries = [i for i, ln in enumerate(lines) if _DHIKR_RE.match(ln)]
    if not boundaries:
        # fallback: fixed-size chunks
        boundaries = list(range(0, len(lines), 40))
    boundaries.append(len(lines))
    for idx in range(len(boundaries) - 1):
        start = boundaries[idx]
        end = boundaries[idx + 1]
        header = lines[start].strip()
        chunk = [_clean_arabic(ln) for ln in lines[start + 1:end]
                 if ln.strip() and _is_mostly_arabic(ln)]
        if len(chunk) < min_verses:
            continue
        label = f"ksucca:{idx:03d}"
        out.append(Unit(corpus="ksucca", label=label, verses=chunk))
    return out


# ---------------------------------------------------------------- Bible
def load_arabic_bible_xlsx(
    path: Path = DATA / "arabic_bible.xlsx", min_verses: int = 5
) -> list[Unit]:
    """
    arabic_bible.xlsx columns:  'Smith Van Dyke' (Verse ID, Book Name,
    Book Number, Chapter, Verse, Text). Group by (Book Name, Chapter).
    """
    import pandas as pd
    xl = pd.ExcelFile(path)
    df = xl.parse(xl.sheet_names[0])
    # The first few rows are metadata; real data starts when the first
    # column becomes an integer verse ID.
    # Rename columns using the header row
    hdr_row = None
    for i, row in df.iterrows():
        if str(row.iloc[0]).strip() == "Verse ID":
            hdr_row = i; break
    if hdr_row is None:
        raise RuntimeError("Could not find header row in arabic_bible.xlsx")
    df.columns = [str(c).strip() for c in df.iloc[hdr_row].tolist()]
    df = df.iloc[hdr_row + 1:].reset_index(drop=True)
    df = df.dropna(subset=["Book Name", "Chapter", "Text"])
    df["Chapter"] = df["Chapter"].astype(int)
    df["Verse"] = df["Verse"].astype(int)
    out: list[Unit] = []
    for (book, chap), sub in df.groupby(["Book Name", "Chapter"]):
        sub = sub.sort_values("Verse")
        verses = [_clean_arabic(str(t)) for t in sub["Text"]
                  if isinstance(t, str) and _is_mostly_arabic(str(t))]
        if len(verses) < min_verses:
            continue
        label = f"bible:{book}:{chap}"
        out.append(Unit(corpus="arabic_bible", label=label, verses=verses))
    return out


# ---------------------------------------------------------------- Hadith
def load_hadith_bukhari(
    path: Path = DATA / "hadith.json", min_verses: int = 5
) -> list[Unit]:
    """
    Group hadiths by (Book == 'Sahih al-Bukhari', Chapter_Number).
    Each chapter becomes one Unit with its Arabic_Text list as verses.
    """
    data = json.load(path.open("r", encoding="utf-8"))
    chapters: dict[int, list[str]] = {}
    for h in data:
        if h.get("Book") != "Sahih al-Bukhari":
            continue
        ch = h.get("Chapter_Number")
        txt = h.get("Arabic_Text") or ""
        txt = _clean_arabic(txt)
        if not txt or not _is_mostly_arabic(txt):
            continue
        chapters.setdefault(int(ch), []).append(txt)
    out: list[Unit] = []
    for ch, verses in sorted(chapters.items()):
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus="hadith_bukhari",
            label=f"bukhari:ch{ch:03d}", verses=verses
        ))
    return out


# ---------------------------------------------------------------- Hindawi
def load_hindawi(
    path: Path = DATA / "hindawi.txt", min_verses: int = 5,
) -> list[Unit]:
    """
    Hindawi corpus is a book of short stories with repeating headers.
    Split by 3+ newlines, skip repeating header blocks, each remaining
    block is one 'story' unit whose lines become verses.
    """
    raw = path.read_text("utf-8", errors="replace").lstrip("\ufeff")
    blocks = re.split(r"\n\s*\n\s*\n+", raw)
    out: list[Unit] = []
    seen_titles: set[str] = set()
    for i, b in enumerate(blocks):
        lines = [ln.strip() for ln in b.split("\n") if ln.strip()]
        if len(lines) < min_verses:
            continue
        title = lines[0][:60]
        # skip repeating header "القصيرة القصص من مختارات" and its variants
        if re.search(r"القصص", title) and re.search(r"مختارات", title):
            continue
        verses = [_clean_arabic(ln) for ln in lines
                  if _is_mostly_arabic(ln)]
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus="hindawi",
            label=f"hindawi:{i:03d}", verses=verses
        ))
    return out


# ---------------------------------------------------------------- Iliad
def _strip_greek_accents(t: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", t)
        if unicodedata.category(c) != "Mn"
    )


def load_iliad(
    path: Path = ILIAD, min_verses: int = 5
) -> list[Unit]:
    """
    Parse the Perseus Iliad TEI-XML. Each Book -> one Unit whose lines
    become the verse list. (Used for cross-language controls only.)
    """
    raw = path.read_text("utf-8", errors="replace")
    book_pat = re.compile(
        r'<div[^>]+type="textpart"[^>]+subtype="Book"[^>]+n="(\d+)"[^>]*>'
        r'(.*?)</div>', re.DOTALL
    )
    line_pat = re.compile(r'<l\s+n="\d+"[^>]*>(.*?)</l>', re.DOTALL)
    out: list[Unit] = []
    for m in book_pat.finditer(raw):
        n = m.group(1)
        block = m.group(2)
        verses = []
        for lm in line_pat.finditer(block):
            t = re.sub(r"<[^>]+>", " ", lm.group(1))
            t = _strip_greek_accents(t)
            t = re.sub(r"[^\u0370-\u03FF\u1F00-\u1FFF\s]", " ", t)
            t = re.sub(r"\s+", " ", t).strip()
            if t:
                verses.append(t)
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus="iliad_greek",
            label=f"iliad:book{int(n):02d}", verses=verses
        ))
    return out


# ---------------------------------------------------------------- Hebrew Tanakh
_HEBREW_BOOK_HEADER = re.compile(r"^[^\s]+\s*$")  # single Hebrew word on its own line
_HEBREW_CHAPTER_HEADER = re.compile(r"^פרק\s+[א-ת]+\s*$")  # "chapter X"


def load_hebrew_tanakh(
    path: Path = HEBREW_TANAKH, min_verses: int = 5,
) -> list[Unit]:
    """
    tanakh_wlc.txt (Westminster Leningrad Codex, public domain).
    Each file is: book title on its own line, then "פרק <letter>" chapter
    headers, then verses labelled with Hebrew letters. One Unit = one
    chapter; verses are its labelled lines.
    """
    raw = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    lines = [ln.rstrip("\r") for ln in raw.split("\n")]

    out: list[Unit] = []
    cur_book = None
    cur_chap = None
    cur_verses: list[str] = []

    def flush():
        nonlocal cur_verses, cur_book, cur_chap
        if cur_book and cur_chap and len(cur_verses) >= min_verses:
            out.append(Unit(
                corpus="hebrew_tanakh",
                label=f"tanakh:{cur_book}:{cur_chap}",
                verses=list(cur_verses),
            ))
        cur_verses = []

    for raw_ln in lines:
        ln = raw_ln.strip()
        if not ln:
            continue
        # Chapter header
        m_chap = _HEBREW_CHAPTER_HEADER.match(ln)
        if m_chap:
            flush()
            cur_chap = ln.split()[1]
            continue
        # Book title (single hebrew word, no verse content)
        if len(ln.split()) == 1 and any("\u0590" <= c <= "\u05FF" for c in ln):
            if cur_book is None or cur_book != ln:
                flush()
                cur_book = ln
                cur_chap = None
            continue
        # Verse line
        # Strip cantillation marks, keep letters + vowel points + basic spaces
        v = re.sub(r"[\u0591-\u05AF\u05BD\u05C0\u05C3-\u05C6]", "", ln)
        v = re.sub(r"\s+", " ", v).strip()
        if v:
            cur_verses.append(v)

    flush()
    return out


# ---------------------------------------------------------------- Greek NT
def load_greek_nt(
    path: Path = GREEK_NT, min_verses: int = 5,
) -> list[Unit]:
    """
    OpenGNT v3.3 CSV.  Each row = one word; the 7th column contains a
    `〔Book｜Chapter｜Verse〕` triple. Group by (book, chapter), form each
    verse as the concatenated words, return one Unit per (book, chapter).
    """
    import csv as _csv
    verse_key_re = re.compile(r"〔(\d+)｜(\d+)｜(\d+)〕")
    greek_token_re = re.compile(r"〔[^｜]+｜[^｜]+｜([^｜]+)｜")

    chapters: dict[tuple[int, int], list[list[str]]] = {}
    with path.open(encoding="utf-8", errors="replace", newline="") as f:
        rd = _csv.reader(f, delimiter="\t")
        header = next(rd, None)  # skip header
        for row in rd:
            if len(row) < 10:
                continue
            bcv_field = row[6] if len(row) > 6 else ""
            token_field = row[9] if len(row) > 9 else ""
            m_bcv = verse_key_re.search(bcv_field)
            m_tok = greek_token_re.search(token_field)
            if not (m_bcv and m_tok):
                continue
            book = int(m_bcv.group(1))
            chap = int(m_bcv.group(2))
            verse = int(m_bcv.group(3))
            word = m_tok.group(1).strip()
            if not word:
                continue
            key = (book, chap)
            verses_of_chap = chapters.setdefault(key, [])
            while len(verses_of_chap) < verse:
                verses_of_chap.append([])
            verses_of_chap[verse - 1].append(word)

    out: list[Unit] = []
    for (book, chap), vlists in sorted(chapters.items()):
        verses = [" ".join(ws) for ws in vlists if ws]
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus="greek_nt",
            label=f"gnt:b{book:02d}:c{chap:03d}",
            verses=verses,
        ))
    return out


# ---------------------------------------------------------------- Pali (Tipiṭaka, SuttaCentral)
# SuttaCentral segment-key conventions differ between collections:
#   - Dīgha (long) suttas use 3-level keys ``dn1:1.1.1`` for verse segments.
#   - Majjhima (mid) suttas use 2-level keys ``mn1:1.1`` for verse segments.
# Both use ``X:0.*`` keys for sutta-level metadata (collection name + sutta
# title). We keep every value whose key has chapter >= 1, then drop anything
# that is too short to be a real verse (single-word section titles like
# ``Brahmajālasutta`` or numbered headers like ``1. Paribbājakakathā``).
_PI_SEGKEY = re.compile(r"^[a-z]+\d+:(\d+)\.\d+(?:\.\d+)?$")
_PI_LATIN_NOISE = re.compile(r"\(.*?\)")  # parentheticals (e.g. translit. notes)
_PI_LIST_MARKER = re.compile(r"^\d+(?:\.\d+)*\.\s+")
_PI_MIN_WORDS_PER_VERSE = 3   # filter out section-title segments


def _clean_pali(t: str) -> str:
    """Normalise Pali text: collapse whitespace, drop list-number prefixes
    and parentheticals. Diacritics (ā ī ū ṃ ñ ṅ ṇ ṭ ḍ ḷ) are PRESERVED
    (they are the analogue of Arabic harakat for the diacritic-channel
    capacity test)."""
    if not t:
        return ""
    t = _PI_LATIN_NOISE.sub(" ", t)
    t = _PI_LIST_MARKER.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_pali_collection(
    coll_dir: Path, coll_id: str, min_verses: int = 5,
) -> list[Unit]:
    """
    Read every ``<sutta>_root-pli-ms.json`` file in ``coll_dir``. Each file
    is one sutta and becomes one Unit. The unit's ``verses`` are the
    segment-level Pali strings (key matches ``X:Y.Z[.W]`` with Y >= 1, and
    the value has at least ``_PI_MIN_WORDS_PER_VERSE`` whitespace-separated
    tokens after cleaning).
    """
    out: list[Unit] = []
    for fpath in sorted(coll_dir.glob("*_root-pli-ms.json")):
        sutta_id = fpath.stem.split("_", 1)[0]
        try:
            data = json.load(fpath.open("r", encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        verses: list[str] = []
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            m = _PI_SEGKEY.match(k)
            if not m:
                continue
            if int(m.group(1)) == 0:  # skip sutta-level metadata
                continue
            txt = _clean_pali(v)
            if txt and len(txt.split()) >= _PI_MIN_WORDS_PER_VERSE:
                verses.append(txt)
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus=f"pali_{coll_id}",
            label=f"pali:{coll_id}:{sutta_id}",
            verses=verses,
        ))
    return out


def load_pali(
    base: Path = DATA_PI, min_verses: int = 5,
) -> list[Unit]:
    """
    Pali Tipiṭaka, Mahāsaṃghīti edition (SuttaCentral, CC0).
    Loads Dīgha Nikāya (34 long suttas) + Majjhima Nikāya (152 mid-length
    suttas). Each sutta -> one Unit; each verse-level segment -> one verse.
    """
    out: list[Unit] = []
    for coll_id in ("dn", "mn"):
        coll_dir = base / coll_id
        if coll_dir.is_dir():
            out.extend(load_pali_collection(
                coll_dir, coll_id, min_verses=min_verses,
            ))
    return out


# ---------------------------------------------------------------- Vedic Sanskrit (Rigveda Saṃhitā)
# Each ``rigveda_mandala_N.json`` is a JSON array of sūkta records:
#   [{"veda": "rigveda", "mandala": 1, "sukta": 1, "text": "<verses>"}, ...]
# The ``text`` field contains the full sūkta as a single string with verses
# separated by blank lines (``\n\n+`` in practice). The first verse often
# carries a non-Devanagari preamble (deity / ṛṣi / chandas line) which we
# drop. We keep verses as raw Devanagari (the analogue of Arabic harakat
# is the udātta / anudātta / svarita accent marks; for this corpus they
# are not always preserved, so we use the diacritic-free Devanagari rasm).
_SA_DEV_BLOCK = re.compile(r"[\u0900-\u097F]")
_SA_VERSE_SEP = re.compile(r"\n\s*\n+")
_SA_DANDA = re.compile(r"[\u0964\u0965]+")           # daṇḍa, double daṇḍa
_SA_VERSE_NUM = re.compile(r"\u0964\u0964\s*\d+\s*\u0965+|\d+\s*$")


def _is_mostly_devanagari(t: str, min_ratio: float = 0.4) -> bool:
    if not t:
        return False
    dev = len(_SA_DEV_BLOCK.findall(t))
    alpha = sum(1 for c in t if c.isalpha() or "\u0900" <= c <= "\u097F")
    return alpha > 0 and dev / max(alpha, 1) >= min_ratio


def _clean_vedic(t: str) -> str:
    """Normalise a single Rigveda verse: strip verse numbers, collapse
    whitespace. Daṇḍas (verse-end punctuation) are kept (they mark prosodic
    boundaries; analogue of Arabic verse-end marks).
    """
    if not t:
        return ""
    t = _SA_VERSE_NUM.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_vedic(
    base: Path = DATA_SA, min_verses: int = 3,
) -> list[Unit]:
    """
    Rigveda Saṃhitā: 10 maṇḍalas, ~1028 sūktas, ~10 552 ṛc-s (verses).
    Each sūkta becomes one Unit; ``text`` is split on blank-line boundaries
    into individual ṛc-s.
    """
    out: list[Unit] = []
    for fpath in sorted(base.glob("rigveda_mandala_*.json")):
        try:
            data = json.load(fpath.open("r", encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for record in data:
            if not isinstance(record, dict):
                continue
            mandala = record.get("mandala")
            sukta = record.get("sukta")
            text = record.get("text") or ""
            if mandala is None or sukta is None or not text:
                continue
            raw_verses = _SA_VERSE_SEP.split(text)
            verses = []
            for v in raw_verses:
                v = _clean_vedic(v)
                if v and _is_mostly_devanagari(v):
                    verses.append(v)
            if len(verses) < min_verses:
                continue
            out.append(Unit(
                corpus="rigveda",
                label=f"rv:m{int(mandala):02d}:s{int(sukta):03d}",
                verses=verses,
            ))
    return out


# ---------------------------------------------------------------- Avestan (Yasna, avesta.org Jamasp-Asa)
# Source HTML stores each line character-reversed (RTL display convention).
# Each chapter starts with ``<H3>Yasna N.</H3>``; verses are <BR>-separated
# lines whose first non-space character (after reversal) is the verse number.
_AE_CHAPTER_RE = re.compile(
    r"<H3[^>]*>\s*Yasna\s+(\d+)\.?\s*</H3>(.*?)(?=<H3[^>]*>\s*Yasna|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_AE_TAG_STRIP = re.compile(r"<[^>]+>")
_AE_LEADING_NUM = re.compile(r"^\s*\d+(?:\.\d+)?\s*[\.\)]?\s*")


def _clean_avestan_line(raw: str) -> str:
    """Take one HTML line (character-reversed) and produce canonical LTR
    Avestan transliteration: reverse the chars, strip the leading verse
    number, normalise whitespace."""
    if not raw:
        return ""
    # Strip any residual HTML tags first
    raw = _AE_TAG_STRIP.sub(" ", raw)
    # Reverse character order to get canonical LTR text
    txt = raw[::-1]
    # Strip a leading verse number (1, 2, 3, ... or 1.1, 1.2, ...)
    txt = _AE_LEADING_NUM.sub("", txt)
    # Collapse whitespace
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def load_avestan(
    path: Path = DATA_AE / "yasna_jamaspa.html", min_verses: int = 5,
) -> list[Unit]:
    """
    Avestan Yasna (sacred liturgy), 72 chapters, Jamasp-Asa transliteration
    from avesta.org. Each chapter -> one Unit; each <BR>-separated line in
    the chapter's HTML body -> one verse (after reversal of char order).
    """
    if not path.is_file():
        return []
    html = path.read_text(encoding="utf-8", errors="replace")
    out: list[Unit] = []
    for m in _AE_CHAPTER_RE.finditer(html):
        chap = int(m.group(1))
        body = m.group(2)
        # Cut body at end-of-chapter markers
        body = re.split(r"<HR\b|<H[1-6]\b|</?BODY", body, 1)[0]
        # Each <BR> separates one line; some lines wrap across multiple <BR>
        # but since each starts with its own verse number we treat them as
        # independent verse units.
        raw_lines = re.split(r"<BR\s*/?>", body, flags=re.IGNORECASE)
        verses: list[str] = []
        for ln in raw_lines:
            v = _clean_avestan_line(ln)
            # filter out very short lines (titles, fragments)
            if v and len(v.split()) >= 2:
                verses.append(v)
        if len(verses) < min_verses:
            continue
        out.append(Unit(
            corpus="avestan_yasna",
            label=f"yasna:y{chap:02d}",
            verses=verses,
        ))
    return out


# ---------------------------------------------------------------- orchestrator
def load_all(include_extras: bool = True,
             include_cross_lang: bool = False,
             include_cross_tradition: bool = False) -> dict[str, list[Unit]]:
    """
    Returns the canonical Arabic corpora plus optional extras.

    Parameters
    ----------
    include_extras : bool
        Load hadith, hindawi, iliad (the v1 default).
    include_cross_lang : bool
        Also load Hebrew Tanakh + Greek NT (slower, large files).
    include_cross_tradition : bool
        Also load the three pre-/non-Abrahamic religious-text corpora
        (Pali Tipiṭaka, Vedic Saṃhitā, Avestan Yasna). Used by the
        cross-tradition R3 reproducibility test (P4).
    """
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(
        sys.stdout, "reconfigure"
    ) else None
    corpora: dict[str, list[Unit]] = {}
    print("[loader] quran_bare.txt ...", end="", flush=True)
    corpora["quran"] = load_quran_bare()
    print(f" {len(corpora['quran'])} units")
    print("[loader] poetry_raw.csv (era-labeled) ...", end="", flush=True)
    pe = load_poetry_by_era()
    for k, v in pe.items():
        corpora[k] = v
    print(" " + ", ".join(f"{k}={len(v)}" for k, v in pe.items()))
    print("[loader] ksucca.txt ...", end="", flush=True)
    corpora["ksucca"] = load_ksucca()
    print(f" {len(corpora['ksucca'])} units")
    print("[loader] arabic_bible.xlsx ...", end="", flush=True)
    try:
        corpora["arabic_bible"] = load_arabic_bible_xlsx()
        print(f" {len(corpora['arabic_bible'])} units")
    except Exception as e:
        # AUDIT FIX 2026-04-21: fail-closed on required corpus.
        raise RuntimeError(
            f"Required corpus 'arabic_bible' failed to load: {e}\n"
            f"Cannot proceed with an incomplete evidence base."
        ) from e

    if include_extras:
        print("[loader] hadith.json (Bukhari only) ...", end="", flush=True)
        corpora["hadith_bukhari"] = load_hadith_bukhari()
        print(f" {len(corpora['hadith_bukhari'])} units")
        print("[loader] hindawi.txt ...", end="", flush=True)
        corpora["hindawi"] = load_hindawi()
        print(f" {len(corpora['hindawi'])} units")
        print("[loader] iliad_perseus.xml ...", end="", flush=True)
        try:
            corpora["iliad_greek"] = load_iliad()
            print(f" {len(corpora['iliad_greek'])} units")
        except Exception as e:
            # AUDIT FIX 2026-04-21: fail-closed.
            raise RuntimeError(
                f"Corpus 'iliad_greek' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e

    if include_cross_lang:
        print("[loader] tanakh_wlc.txt (Hebrew) ...", end="", flush=True)
        try:
            corpora["hebrew_tanakh"] = load_hebrew_tanakh()
            print(f" {len(corpora['hebrew_tanakh'])} units")
        except Exception as e:
            # AUDIT FIX 2026-04-21: fail-closed.
            raise RuntimeError(
                f"Corpus 'hebrew_tanakh' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e
        print("[loader] opengnt_v3_3.csv (Greek NT) ...", end="", flush=True)
        try:
            corpora["greek_nt"] = load_greek_nt()
            print(f" {len(corpora['greek_nt'])} units")
        except Exception as e:
            # AUDIT FIX 2026-04-21: fail-closed.
            raise RuntimeError(
                f"Corpus 'greek_nt' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e

    if include_cross_tradition:
        print("[loader] pali Tipiṭaka (DN+MN) ...", end="", flush=True)
        try:
            pali_units = load_pali()
            # split by collection so downstream code can use them as separate
            # control corpora (matching how Arabic poetry is split by era)
            from collections import defaultdict
            by_coll: dict[str, list[Unit]] = defaultdict(list)
            for u in pali_units:
                by_coll[u.corpus].append(u)
            for k, v in by_coll.items():
                corpora[k] = v
            print(" " + ", ".join(
                f"{k}={len(v)}" for k, v in sorted(by_coll.items())))
        except Exception as e:
            raise RuntimeError(
                f"Corpus 'pali' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e
        print("[loader] rigveda (10 maṇḍalas) ...", end="", flush=True)
        try:
            corpora["rigveda"] = load_vedic()
            print(f" {len(corpora['rigveda'])} units")
        except Exception as e:
            raise RuntimeError(
                f"Corpus 'rigveda' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e
        print("[loader] avestan Yasna ...", end="", flush=True)
        try:
            corpora["avestan_yasna"] = load_avestan()
            print(f" {len(corpora['avestan_yasna'])} units")
        except Exception as e:
            raise RuntimeError(
                f"Corpus 'avestan_yasna' failed to load: {e}\n"
                f"Cannot proceed with an incomplete evidence base."
            ) from e
    return corpora


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    corpora = load_all(include_extras=True)
    print("\n=== summary ===")
    for name, units in corpora.items():
        if not units:
            print(f"  {name:<20s}  0 units")
            continue
        nv = np.array([u.n_verses() for u in units])
        nw = np.array([u.n_words() for u in units])
        print(
            f"  {name:<20s}  {len(units):>4d} units  "
            f"verses median={int(np.median(nv)):4d} [min={int(nv.min())}, "
            f"max={int(nv.max())}]  "
            f"words median={int(np.median(nw)):5d}"
        )
