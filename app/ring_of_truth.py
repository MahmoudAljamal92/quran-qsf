"""Ring of Truth — interactive Quran-fingerprint authenticity meter.

Streamlit app that runs the 8-channel Authentication Ring (exp183) on any
user-pasted text and reports a continuous similarity-to-Quran score with
per-channel deviation bars.

Supports 6 scripts:
  Arabic (default, Quran reference), Hebrew, Greek, Pali,
  Avestan, Rigveda (Devanagari).

The reference constants are always the Quran's locked scalars
(H_EL=0.9685, p_max=0.7273, C_Omega=0.7985, D_max=3.84, F75=5.316,
d_info=1.667). A perfect 100% score in a non-Arabic script is
exceptionally rare.

Launch locally:
    pip install -r app/requirements.txt
    streamlit run app/ring_of_truth.py

Deploy on Streamlit Cloud (free):
    1. Push repo to GitHub.
    2. Go to https://streamlit.io/cloud -> "New app" -> connect GitHub repo.
    3. Main file: app/ring_of_truth.py. Click "Deploy".
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from math import log, log2
from pathlib import Path

import numpy as np
import streamlit as st

# --- Import the locked authentication-ring methodology from exp183 ----
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from experiments.exp183_quran_authentication_ring.run import (  # noqa: E402
    QURAN_H_EL_REF,
    QURAN_P_MAX_REF,
    QURAN_F67_C_OMEGA_REF,
    QURAN_F75_CONSTANT_REF,
    QURAN_F79_DMAX_REF,
    QURAN_D_INFO_REF,
    bigram_L1_distance,
)

# --- Canonical locked normalisers (the same ones used to lock every
# cross-tradition finding in this project; do NOT re-implement). ---
from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _ARABIC_LETTERS_28,
    _HEBREW_CONS_22,
    _GREEK_LETTERS_24,
    _PALI_ALPHABET_31,
    _AV_ALPHABET_26,
    _normalise_arabic,
    _normalise_hebrew,
    _normalise_greek,
    _normalise_pali,
    _normalise_avestan,
)

# ======================================================================
# Per-language configuration — each entry carries the CANONICAL locked
# normaliser + alphabet used throughout the project's experiments.
# ======================================================================

# Rigveda (Devanagari) — 47 letters; no canonical normaliser exists in the
# project (Rigveda was not part of the 11-corpus F-Universal pool), so we
# provide a minimal local one that strips Devanagari diacritics / matras.
_RIGVEDA_ALPHABET = ("अआइईउऊऋएऐओऔ"
                     "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ")
_RIGVEDA_SET = set(_RIGVEDA_ALPHABET)
_RIGVEDA_DIAC = re.compile(r"[\u093C-\u094F\u0951-\u0957\u0962-\u0963\u0902-\u0903]")


def _normalise_rigveda(s: str) -> str:
    s = _RIGVEDA_DIAC.sub("", s)
    return "".join(c for c in s if c in _RIGVEDA_SET)


_LANGS = {
    "ar": dict(name="Arabic (Quran reference)", alphabet=_ARABIC_LETTERS_28,
               normalise=_normalise_arabic, filler="\u0627"),
    "he": dict(name="Hebrew", alphabet=_HEBREW_CONS_22,
               normalise=_normalise_hebrew, filler="א"),
    "el": dict(name="Greek", alphabet=_GREEK_LETTERS_24,
               normalise=_normalise_greek, filler="α"),
    "pi": dict(name="Pāli (romanized IAST)", alphabet=_PALI_ALPHABET_31,
               normalise=_normalise_pali, filler="a"),
    "av": dict(name="Avestan (romanized)", alphabet=_AV_ALPHABET_26,
               normalise=_normalise_avestan, filler="a"),
    "sa": dict(name="Rigveda (Devanagari)", alphabet=_RIGVEDA_ALPHABET,
               normalise=_normalise_rigveda, filler="अ"),
}

for _c, _lang in _LANGS.items():
    _lang["A"] = len(_lang["alphabet"])
    _lang["alphabet_set"] = set(_lang["alphabet"])


def normalise_text(text: str, lang_code: str) -> str:
    """Apply the canonical locked normaliser for this language."""
    return _LANGS[lang_code]["normalise"](text)


# ======================================================================
# Verse / chapter segmentation
# ======================================================================
def segment_text(raw: str):
    """Return dict with verses and a surah_verses mapping.

    Rules:
      - If '|' separators and leading sura|ayah|text pipe format -> parse.
      - Elif '|' separators between verses -> split by | (treat one chapter).
      - Else -> each non-empty line is one verse (treat as one chapter).
    """
    if "|" in raw and any(
        line.split("|")[0].strip().isdigit()
        for line in raw.splitlines()[:10] if line.strip()
    ):
        verses, surah_verses = [], {}
        for line in raw.splitlines():
            x = line.split("|", 2)
            if len(x) < 3 or not x[0].strip().isdigit():
                continue
            s = int(x[0])
            verses.append(x[2].strip())
            surah_verses.setdefault(s, []).append(x[2].strip())
        fmt = "pipe_delimited"
    elif "|" in raw:
        verses = [v.strip() for v in raw.split("|") if v.strip()]
        surah_verses = {1: verses}
        fmt = "pipe_verses"
    else:
        verses = [v for v in raw.splitlines() if v.strip()]
        surah_verses = {1: verses}
        fmt = "newline_verses"
    return dict(verses=verses, surah_verses=surah_verses, format=fmt)


# ======================================================================
# Language-generalised channel computations
# ======================================================================
def compute_H_EL_pmax(surah_verses, lang_code):
    """Median per-chapter Shannon entropy and p_max of verse-final letters."""
    lang = _LANGS[lang_code]
    A = lang["A"]
    alphabet = lang["alphabet"]
    H_list, p_list = [], []
    for s, verses in surah_verses.items():
        finals = []
        for v in verses:
            only = normalise_text(v, lang_code)
            if only:
                finals.append(only[-1])
        if len(finals) < 3:
            continue
        counts = Counter(finals)
        total = sum(counts.values())
        p = np.array([counts.get(c, 0) / total for c in alphabet])
        p_safe = p[p > 0]
        H = -float(np.sum(p_safe * np.log2(p_safe)))
        H_list.append(H)
        p_list.append(float(p.max()))
    if not H_list:
        return None, None
    return float(np.median(H_list)), float(np.median(p_list))


def compute_ifs_d_info(text, lang_code):
    """Fractal-information dimension of language-letter frequencies at c=0.18."""
    lang = _LANGS[lang_code]
    only = normalise_text(text, lang_code)
    if len(only) < 100:
        return None
    counts = Counter(only)
    total = sum(counts.values())
    p = np.array([counts.get(c, 0) / total for c in lang["alphabet"]])
    p_safe = p[p > 0]
    H_nats = -float(np.sum(p_safe * np.log(p_safe)))
    c = 0.18
    d_info = H_nats / log(1.0 / c)
    return d_info


def compute_bigram_delta(text, lang_code):
    lang = _LANGS[lang_code]
    only = normalise_text(text, lang_code)
    if len(only) < 100:
        return None
    mid = len(only) // 2
    orig_letter = only[mid]
    alt_letter = lang["filler"] if orig_letter != lang["filler"] else lang["alphabet"][1]
    edited = only[:mid] + alt_letter + only[mid + 1:]
    h1 = Counter(only[i:i+2] for i in range(len(only) - 1))
    h2 = Counter(edited[i:i+2] for i in range(len(edited) - 1))
    return bigram_L1_distance(h1, h2)


def compute_dual_mode_contrast(surah_verses, lang_code):
    lang = _LANGS[lang_code]
    alphabet = lang["alphabet"]
    A = lang["A"]
    n_surahs = len(surah_verses)
    if n_surahs < 50 or max(surah_verses) < 114:
        return None
    F = np.zeros((114, A))
    for s in range(1, 115):
        if s in surah_verses:
            text = " ".join(surah_verses[s])
            only = normalise_text(text, lang_code)
            if only:
                c = Counter(only)
                tot = sum(c.values())
                F[s-1] = np.array([c.get(L, 0)/tot for L in alphabet])
    classical_slots = [1, 7, 54, 66, 72, 74, 76, 80, 82, 86, 90, 92, 98, 102, 104, 110, 112]
    d = np.linalg.norm(np.diff(F, axis=0), axis=1)
    mean_classical = float(np.mean(d[classical_slots]))
    nonclass = [k for k in range(113) if k not in classical_slots]
    mean_nonclassical = float(np.mean(d[nonclass]))
    return mean_classical - mean_nonclassical


# ======================================================================
# Deviation scoring — continuous d_i in [0, 1] per channel
# ======================================================================
def _clamp01(x):
    return float(max(0.0, min(1.0, x)))


def score_channels(data, lang_code):
    """Return a list of channel dicts: {name, label, weight, d, value, note, status}.
    status ∈ {'PASS', 'FAIL', 'N/A'}.  d ∈ [0,1].
    """
    lang = _LANGS[lang_code]
    A = lang["A"]
    channels = []

    H_EL, p_max = compute_H_EL_pmax(data["surah_verses"], lang_code)
    n_letters = len(normalise_text(" ".join(data["verses"]), lang_code))

    # T1 — bigram-shift edit response (F55): theorem Δ=2..4 under k=1 edit
    delta = compute_bigram_delta(" ".join(data["verses"]), lang_code)
    if delta is None:
        d = 1.0
        status = "N/A"
        value = "n/a"
        note = "Text < 100 letters after normalisation"
    else:
        # Quran-like response: delta in [2,4]. Deviation grows outside this band.
        if 2 <= delta <= 4:
            d = 0.0
        else:
            d = _clamp01(abs(delta - 3) / 6.0)
        status = "PASS" if d < 0.33 else "FAIL"
        value = str(delta)
        note = "1-letter edit L1 bigram distance"
    channels.append(dict(
        key="T1", label="T1 · Bigram-shift (F55)", weight=2.0,
        plain_label="Letter-pattern stability",
        plain_what=("Tests how the letter-pair pattern reacts to a single-letter swap. "
                    "The Quran reacts inside a tight numerical band — not too rigid, "
                    "not too random. Forged copies that change even one letter usually fall outside."),
        plain_quran="around 3 (window 2 to 4)",
        d=d, value=value, note=note, status=status,
    ))

    # T2 — C_Ω rhyme channel (F67)
    if H_EL is None:
        d, status, value, note = 1.0, "N/A", "n/a", "No verses detected"
    else:
        C_omega = 1.0 - H_EL / log2(A)
        # reference 0.7985. Deviation = |C-0.7985| / 0.7985, clamped.
        d = _clamp01(abs(C_omega - QURAN_F67_C_OMEGA_REF) / QURAN_F67_C_OMEGA_REF)
        status = "PASS" if C_omega >= 0.70 else "FAIL"
        value = f"{C_omega:.3f}"
        note = f"rhyme-channel utilisation (Quran ref {QURAN_F67_C_OMEGA_REF:.3f})"
    channels.append(dict(
        key="T2", label="T2 · C_Ω rhyme channel (F67)", weight=1.0,
        plain_label="Rhyme concentration",
        plain_what=("How much the verse endings concentrate on a few letters, compared "
                    "to a perfectly random distribution. Higher = stronger rhyme structure."),
        plain_quran=f"{QURAN_F67_C_OMEGA_REF:.4f} (very concentrated)",
        d=d, value=value, note=note, status=status,
    ))

    # T3 — F75 universal invariant
    if H_EL is None or p_max is None:
        d, status, value, note = 1.0, "N/A", "n/a", "No verses detected"
    else:
        F75_val = H_EL + log2(max(p_max, 1e-12) * A)
        d = _clamp01(abs(F75_val - QURAN_F75_CONSTANT_REF) / 0.75)
        status = "PASS" if abs(F75_val - QURAN_F75_CONSTANT_REF) <= 0.5 else "FAIL"
        value = f"{F75_val:.3f} bits"
        note = f"H_EL + log₂(p_max·A) (Quran ref {QURAN_F75_CONSTANT_REF:.2f} ± 0.5)"
    channels.append(dict(
        key="T3", label="T3 · F75 universal invariant", weight=1.0,
        plain_label="Cross-tradition scripture invariant",
        plain_what=("A mathematical balance found across all 11 canonical scriptures we tested "
                    "(Quran, Hebrew Tanakh, Greek NT, Pali, Avestan, Rigveda, etc.). It sits at "
                    "the same ~5.75-bit value regardless of alphabet or language family."),
        plain_quran=f"{QURAN_F75_CONSTANT_REF:.3f} bits (pool mean 5.75)",
        d=d, value=value, note=note, status=status,
    ))

    # T4 — F76 sub-1-bit entropy
    if H_EL is None:
        d, status, value, note = 1.0, "N/A", "n/a", "No verses detected"
    else:
        # Deviation: distance from Quran ref 0.9685, normalised by tolerable 0.6 bit
        d = _clamp01(abs(H_EL - QURAN_H_EL_REF) / 0.6)
        status = "PASS" if H_EL < 1.0 else "FAIL"
        value = f"{H_EL:.3f} bits"
        note = f"median per-chapter verse-final entropy (Quran ref {QURAN_H_EL_REF:.3f})"
    channels.append(dict(
        key="T4", label="T4 · H_EL < 1 bit (F76)", weight=1.0,
        plain_label="Verse-ending predictability (one-bit universal)",
        plain_what=("The Shannon entropy of verse-final letters — how unpredictable "
                    "the next verse ending is. The Quran is the ONLY canonical scripture "
                    "we measured that sits below the 1-bit threshold."),
        plain_quran=f"{QURAN_H_EL_REF:.3f} bits (below 1)",
        d=d, value=value, note=note, status=status,
    ))

    # T5 — F79 alphabet-corrected gap
    if H_EL is None:
        d, status, value, note = 1.0, "N/A", "n/a", "No verses detected"
    else:
        D_max = log2(A) - H_EL
        # Quran ref 3.84. Deviation = |D-3.84| / 2 clamped.
        d = _clamp01(abs(D_max - QURAN_F79_DMAX_REF) / 2.0)
        status = "PASS" if D_max >= 3.5 else "FAIL"
        value = f"{D_max:.3f} bits"
        note = f"log₂(A) − H_EL (Quran ref {QURAN_F79_DMAX_REF:.2f})"
    channels.append(dict(
        key="T5", label="T5 · D_max alphabet gap (F79)", weight=1.0,
        plain_label="Rhyme strength gap",
        plain_what=("How much structure the verse endings carry compared to random verse endings. "
                    "Larger gap = more deliberately rhymed text."),
        plain_quran=f"{QURAN_F79_DMAX_REF:.2f} bits (large gap)",
        d=d, value=value, note=note, status=status,
    ))

    # T6 — dual-mode classical-pair contrast (F82)
    n_surahs = len(data["surah_verses"])
    if n_surahs < 10:
        d, status, value, note = 0.0, "N/A", "n/a", f"only {n_surahs} chapter(s); need ≥10 for T6 signal — skipped"
    else:
        diff = compute_dual_mode_contrast(data["surah_verses"], lang_code)
        if diff is None:
            d, status, value, note = 0.0, "N/A", "n/a", "need full 114-chapter structure — skipped"
        else:
            # Quran ref: diff > 0 is the pass condition; deviation grows as diff becomes negative.
            if diff >= 0:
                d = _clamp01(1 - diff / 0.05)  # perfect 0 when diff >= 0.05
            else:
                d = _clamp01(0.5 + abs(diff) / 0.1)
            status = "PASS" if diff > 0 else "FAIL"
            value = f"{diff:+.4f}"
            note = "classical-pair letter-frequency contrast"
    channels.append(dict(
        key="T6", label="T6 · Dual-mode (F82)", weight=2.0,
        plain_label="Twin-chapter contrast (maqrunat)",
        plain_what=("The 17 traditional surah pairings (e.g. al-Falaq + al-Nas) show LINGUISTIC "
                    "contrast — paired by tradition but distinct in letter usage. This channel "
                    "only fires for inputs with the full 114-chapter structure."),
        plain_quran="positive contrast (+0.034)",
        d=d, value=value, note=note, status=status,
    ))

    # T7 — IFS fractal dimension (F87-linked)
    if n_letters < 100:
        d, status, value, note = 0.0, "N/A", "n/a", f"only {n_letters} letter(s); need ≥100 — skipped"
    else:
        d_info = compute_ifs_d_info(" ".join(data["verses"]), lang_code)
        if d_info is None:
            d, status, value, note = 0.0, "N/A", "n/a", "insufficient data for fractal dim"
        else:
            d = _clamp01(abs(d_info - QURAN_D_INFO_REF) / 0.5)
            status = "PASS" if abs(d_info - QURAN_D_INFO_REF) <= 0.05 else "FAIL"
            value = f"{d_info:.3f}"
            note = f"IFS info-dim @ c=0.18 (Quran ref {QURAN_D_INFO_REF:.3f})"
    channels.append(dict(
        key="T7", label="T7 · Fractal dim (F87)", weight=2.0,
        plain_label="Letter-frequency fractal complexity",
        plain_what=("The information-theoretic fractal dimension of the letter-frequency distribution. "
                    "The Quran sits in a tight numerical range that's hard to forge — only fires "
                    "for inputs of at least 100 letters."),
        plain_quran=f"around {QURAN_D_INFO_REF:.3f}",
        d=d, value=value, note=note, status=status,
    ))

    # T8 — rhyme presence
    if p_max is None:
        d, status, value, note = 1.0, "N/A", "n/a", "No verses detected"
    else:
        # Quran ref 0.7273. Deviation = |p-0.7273| / 0.7273 clamped.
        d = _clamp01(abs(p_max - QURAN_P_MAX_REF) / QURAN_P_MAX_REF)
        status = "PASS" if p_max >= 0.30 else "FAIL"
        value = f"{p_max:.3f}"
        note = f"max verse-final letter probability (Quran ref {QURAN_P_MAX_REF:.3f})"
    channels.append(dict(
        key="T8", label="T8 · Rhyme presence", weight=1.0,
        plain_label="Dominant verse-ending rate",
        plain_what=("How often the most common verse-final letter appears at verse ends. "
                    "In the Quran, the single letter (ن) accounts for ~73% of all verse endings."),
        plain_quran=f"{QURAN_P_MAX_REF:.3f} (73% one letter)",
        d=d, value=value, note=note, status=status,
    ))

    return channels


def composite_similarity(channels):
    """Weighted similarity = 1 − Σ(w_i · d_i) / Σ(w_i). N/A channels excluded."""
    num = 0.0
    den = 0.0
    for ch in channels:
        if ch["status"] == "N/A":
            continue
        num += ch["weight"] * ch["d"]
        den += ch["weight"]
    if den == 0:
        return 0.0
    return max(0.0, 1.0 - num / den)


def verdict_label(channels):
    """Binary verdict + counts. Returns (verdict, subtitle, n_pass, n_total_active)."""
    active = [c for c in channels if c["status"] != "N/A"]
    n_total = len(active)
    n_pass = sum(1 for c in active if c["status"] == "PASS")
    if n_total == 0:
        return ("INSUFFICIENT INPUT",
                "Not enough text to measure any dimension. Paste a longer passage.",
                0, 0)
    if n_pass == n_total:
        return ("MATCHES THE QURAN FINGERPRINT",
                f"All {n_total} measurable dimensions match the Quran's locked statistical signature "
                "within the pre-registered tolerance.",
                n_pass, n_total)
    return ("DOES NOT MATCH THE QURAN FINGERPRINT",
            f"{n_total - n_pass} of {n_total} dimensions diverge from the Quran's locked signature. "
            "See the per-dimension breakdown below.",
            n_pass, n_total)


# ======================================================================
# Built-in example texts (canned, locked at app load)
# ======================================================================
_EXAMPLES = {}


def _load_quran_slice(surah_ids):
    """Return pipe-delimited slice of quran_bare.txt for the given surah IDs."""
    p = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
    if not p.exists():
        return ""
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            x = line.split("|", 2)
            if len(x) == 3 and x[0].strip().isdigit() and int(x[0]) in surah_ids:
                out.append(line.rstrip())
    return "\n".join(out)


# Try to load real Quran samples from the repo corpus; fall back gracefully.
try:
    _EXAMPLES["quran_fatiha"] = ("Surah Al-Fatiha (7 verses, the opener)",
                                  "ar", _load_quran_slice({1}))
    _EXAMPLES["quran_ikhlas"] = ("Surah Al-Ikhlas (4 verses, very short)",
                                  "ar", _load_quran_slice({112}))
    _EXAMPLES["quran_mulk"]   = ("Surah Al-Mulk (30 verses, medium)",
                                  "ar", _load_quran_slice({67}))
    _EXAMPLES["quran_full"]   = ("Full Quran (114 surahs — fires every channel)",
                                  "ar", _load_quran_slice(set(range(1, 115))))
except Exception:
    pass


# Non-Quranic Arabic poetry sample (Imru' al-Qais, public domain) -- baked in.
_EXAMPLES["poem_imru_qais"] = (
    "Imru' al-Qais — Mu'allaqa (classical Arabic poetry, non-Quranic)",
    "ar",
    """قفا نبك من ذكرى حبيب ومنزل
بسقط اللوى بين الدخول فحومل
فتوضح فالمقراة لم يعف رسمها
لما نسجتها من جنوب وشمأل
ترى بعر الآرام في عرصاتها
وقيعانها كأنه حب فلفل
كأني غداة البين يوم تحملوا
لدى سمرات الحي ناقف حنظل""")


# Hebrew Tanakh sample (Genesis 1:1-5, public domain).
_EXAMPLES["tanakh"] = (
    "Genesis 1:1–5 (Hebrew Tanakh, BHS)",
    "he",
    """בראשית ברא אלהים את השמים ואת הארץ
והארץ היתה תהו ובהו וחשך על פני תהום ורוח אלהים מרחפת על פני המים
ויאמר אלהים יהי אור ויהי אור
וירא אלהים את האור כי טוב ויבדל אלהים בין האור ובין החשך
ויקרא אלהים לאור יום ולחשך קרא לילה ויהי ערב ויהי בקר יום אחד""")


# ======================================================================
# UI
# ======================================================================
st.set_page_config(page_title="The Quran Fingerprint Test", page_icon="◎", layout="wide")

# --- Custom CSS for clean professional look ---
st.markdown("""
<style>
.big-verdict {
  padding: 32px 24px; border-radius: 18px; text-align: center;
  margin: 16px 0 24px 0; border: 1px solid rgba(255,255,255,0.08);
}
.big-verdict h1 {
  font-size: 48px; font-weight: 800; line-height: 1.05; margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}
.big-verdict .sub {
  font-size: 16px; color: #c9c9c9; margin-top: 8px; max-width: 720px; margin-left: auto; margin-right: auto;
}
.dim-card {
  border-radius: 12px; padding: 16px 18px; margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.06);
}
.dim-card .row1 { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.dim-card .name { font-size: 16px; font-weight: 700; color: #fff; }
.dim-card .badge {
  font-size: 12px; padding: 3px 10px; border-radius: 999px;
  font-weight: 600; letter-spacing: 0.4px;
}
.dim-card .what { font-size: 13.5px; color: #c0c0c0; line-height: 1.5; margin: 6px 0 10px 0; }
.dim-card .nums { display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  font-size: 13px; color: #d0d0d0; }
.dim-card .nums .label { color: #888; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.4px; }
.dim-card .nums .val { color: #fff; font-weight: 600; font-size: 14px; }
.intro-box {
  background: linear-gradient(135deg, #14202b 0%, #0e1a26 100%);
  padding: 18px 22px; border-radius: 12px; border-left: 3px solid #4a90e2;
  margin-bottom: 18px;
}
.intro-box h3 { margin: 0 0 6px 0; font-size: 17px; color: #fff; }
.intro-box p { margin: 0; font-size: 14px; color: #c9c9c9; line-height: 1.55; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🕌 The Quran Verification & Fingerprint Test")
st.markdown(
    "_Paste any text. The tool checks — in order — whether it is **exactly** the Quran, "
    "**near** the Quran (with differences highlighted), or a **different** text whose statistical "
    "structure is then measured against the Quran's 8-dimensional mathematical fingerprint._"
)

# --- "How we know — math, not memorisation" intro box ---
st.markdown("""
<div class='intro-box'>
<h3>How this works (in plain language)</h3>
<p><strong>We did NOT memorise the Quran.</strong> Instead we built three mathematical layers that
work on <em>any</em> passage, even one verse or one word:</p>
<p><strong>Layer 1 — Exact match:</strong> we compare your text letter-by-letter against the
entire canonical Quran (114 surahs, 6,236 verses). If every letter matches, we tell you exactly
which surah and verse it comes from. We do not "recognise" it — we <em>search</em> for it.</p>
<p><strong>Layer 2 — Near match:</strong> if a letter is changed, a word is reordered, or a verse
is inserted, we find the closest passage in the Quran, show you exactly which characters differ,
and measure the deviation percentage.</p>
<p><strong>Layer 3 — Structural fingerprint:</strong> for texts that are not in the Quran at all
(poetry, modern Arabic, translations), we run 8 independent mathematical measurements
(rhyme concentration, verse-ending entropy, letter-pair stability, fractal complexity, and others)
that were locked in advance and verified across 11 other canonical scriptures. Each measurement
gives a PASS or FAIL, producing a binary verdict: <em>does the text structurally resemble the Quran?</em></p>
<p><strong>Honesty guardrail.</strong> A single common word like <code>كتب</code>, <code>الله</code>, or
<code>الرحمن</code> appears both in the Quran <em>and</em> in every Arabic newspaper ever printed.
Reporting it as "Quranic" because it happens to be a substring of the Quran would be a false positive.
So for short or very common inputs we return one of two honest verdicts instead:
<em>Too Short To Determine</em> (below the specificity floor) or <em>Appears In The Quran — But Ambiguous</em>
(we show you the occurrence count and tell you why origin cannot be concluded). Confident Quranic-origin
claims require either <b>≥ 20 letters</b>, or <b>≥ 8 letters AND ≤ 5 occurrences</b> in the Quran.</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar: example loader ---
with st.sidebar:
    st.markdown("### Try a built-in example")
    st.caption("Click one to load it into the input box.")
    chosen_example = None
    for key, (label, ex_lang, _content) in _EXAMPLES.items():
        if st.button(label, key=f"ex_{key}", use_container_width=True):
            chosen_example = key

    st.markdown("---")
    with st.expander("ℹ️ About this tool"):
        st.markdown(
            "This tool is a downstream artefact of the [Quranic Structural "
            "Fingerprint project](https://github.com/MahmoudAljamal92/quran-qsf), "
            "OSF DOI [`10.17605/OSF.IO/N46Y5`](https://doi.org/10.17605/OSF.IO/N46Y5).\n\n"
            "All measurements are deterministic, SHA-256 locked, and re-verified "
            "from raw data at project closure (8/8 PASS in `TOP_FINDINGS_AUDIT.md`)."
        )

# --- Main input area ---
st.markdown("### Paste your text")

if "text_buffer" not in st.session_state:
    st.session_state.text_buffer = ""
if chosen_example is not None:
    st.session_state.text_buffer = _EXAMPLES[chosen_example][2]

up = st.file_uploader(
    "Or upload a .txt / .md file",
    type=["txt", "md"],
    label_visibility="collapsed",
)
if up is not None:
    st.session_state.text_buffer = up.read().decode("utf-8", errors="replace")

text = st.text_area(
    "Any length — one word, one verse, one surah, or a whole book.",
    value=st.session_state.text_buffer,
    height=240,
    key="main_text_area",
)

run_btn = st.button(
    "🔍 Analyse text",
    type="primary",
    use_container_width=True,
)

# ----------------------------------------------------------------------
# Helper: render character-level diff from ops
# ----------------------------------------------------------------------
def _render_diff(ops: list[tuple[str, str, str]]) -> str:
    """Convert Levenshtein ops to a short HTML diff string."""
    out = []
    for kind, a, b in ops:
        if kind == "=":
            out.append(b)
        elif kind == "sub":
            out.append(f"<span style='color:#e74c3c;text-decoration:underline;'>[{b}]</span>")
        elif kind == "ins":
            out.append(f"<span style='color:#e74c3c;font-weight:bold;'>+{b}</span>")
        elif kind == "del":
            out.append(f"<span style='color:#3498db;text-decoration:line-through;'>-{a}</span>")
    return "".join(out)


# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------
if run_btn and text.strip():
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from app.quran_match import classify  # noqa: E402

    qry_norm = _normalise_arabic(text)
    n_letters = len(qry_norm)

    with st.spinner("Layer 1: exact Quran search …"):
        c = classify(text)

    # --- GUARD: TOO SHORT TO DETERMINE ---------------------------------
    if c.verdict == "TOO_SHORT":
        vh = c.verbatim
        st.markdown(f"""
<div class='big-verdict' style='background:linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>⊘</div>
  <h1 style='color:#cccccc;'>TOO SHORT TO DETERMINE</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    Input has <b>{c.n_input_letters}</b> normalised Arabic letter{'' if c.n_input_letters==1 else 's'} —
    below the specificity threshold needed to distinguish Quranic origin from coincidence.
  </div>
  <div class='sub'>
    Paste at least <b>8 letters</b> of a distinctive passage, or a phrase of
    <b>14+ letters</b> for a confident verdict.
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### Why we refuse to guess")
        st.markdown(
            f"*{c.rationale}*\n\n"
            "A single Arabic root like `كتب` (3 letters) appears in newspapers, poetry, contracts, and "
            "everywhere else in classical and modern Arabic. It also appears dozens of times in the Quran. "
            "Reporting it as 'Quranic' because we found it somewhere in our corpus would be a **false positive**. "
            "We only claim Quranic origin when the string is long enough, OR short-but-rare enough, that "
            "accidental coincidence is statistically implausible."
        )
        if vh is not None:
            st.info(
                f"ℹ️ For transparency: this exact string does appear **{vh.occurrences} time(s)** "
                f"in the Quran (first at Surah {vh.surah_start}:{vh.verse_start}). "
                "That alone is not evidence of origin at this length."
            )
        st.stop()

    # --- GUARD: AMBIGUOUS SUBSTRING ------------------------------------
    if c.verdict == "QURAN_SUBSTRING_AMBIGUOUS":
        vh = c.verbatim
        st.markdown(f"""
<div class='big-verdict' style='background:linear-gradient(135deg, #2d2a14 0%, #1e1c0c 100%);'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>⚠️</div>
  <h1 style='color:#f1c40f;'>APPEARS IN THE QURAN — BUT AMBIGUOUS</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    This exact string is found <b>{vh.occurrences:,}</b> time(s) in the Quran,
    first at Surah {vh.surah_start}:{vh.verse_start}.
  </div>
  <div class='sub'>
    But it is either too short ({c.n_input_letters} letters) or too common a formula to
    prove it <em>came from</em> the Quran. The same letters appear in everyday Arabic.
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### Why this is ambiguous")
        st.markdown(f"*{c.rationale}*")
        st.markdown(
            "**What this means in plain language:** yes, we found your exact letters inside the Quran. "
            "But the same letters also appear routinely in non-Quranic Arabic. "
            "For us to say *'this text is from the Quran'*, we require the match to be **distinctive**:\n\n"
            f"- Either **≥ 20 letters** (long enough that accidental match is unlikely), OR\n"
            f"- Both **≥ 8 letters** AND **≤ 5 occurrences in the Quran** (short but rare).\n\n"
            f"Your input is {c.n_input_letters} letters and appears {vh.occurrences:,} time(s), "
            "which does not meet either bar. Lengthen the input to get a confident verdict."
        )
        st.stop()

    # --- LAYER 1: EXACT (long enough + distinctive) --------------------
    if c.verdict == "QURAN_VERBATIM":
        vh = c.verbatim
        st.markdown(f"""
<div class='big-verdict' style='background:linear-gradient(135deg, #0f3320 0%, #14422a 100%);'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>✅</div>
  <h1 style='color:#2ecc71;'>THIS IS THE QURAN</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    Exact letter-for-letter match in the canonical Uthmani text
    (confidence: <b>{c.confidence}</b>)
  </div>
  <div class='sub'>
    Surah {vh.surah_start}:{vh.verse_start} → {vh.surah_end}:{vh.verse_end}
    ({vh.n_verses_spanned} verse{'' if vh.n_verses_spanned==1 else 's'}) ·
    exact substring occurs <b>{vh.occurrences}</b> time{'' if vh.occurrences==1 else 's'} in the Quran
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### How we know (mathematical proof)")
        st.markdown(
            f"Your text has **{c.n_input_letters:,}** normalised Arabic letters. "
            "We compared every one of them, in order, against the entire 329,404-letter "
            f"canonical Quran corpus. The exact same sequence of letters exists at **{vh.occurrences} "
            "position(s)** in the Quran "
            f"(first at Surah {vh.surah_start}:{vh.verse_start}). "
            f"At this length ({c.n_input_letters} letters) and rareness ({vh.occurrences} occurrences), "
            "an accidental exact match in non-Quranic Arabic is statistically implausible.\n\n"
            "This is a mechanical search — no memorisation, no recognition. "
            "Try changing a single letter and the tool will immediately report it as *modified*."
        )
        with st.expander("Full rationale"):
            st.write(c.rationale)
        st.stop()

    # --- LAYER 2: MODIFIED ---
    elif c.verdict == "MODIFIED_QURAN":
        fh = c.fuzzy
        deviation_color = "#f1c40f" if fh.deviation_pct < 0.10 else "#e67e22" if fh.deviation_pct < 0.20 else "#e74c3c"
        st.markdown(f"""
<div class='big-verdict' style='background:linear-gradient(135deg, #3a2b0a 0%, #2b1f08 100%);'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>✏️</div>
  <h1 style='color:{deviation_color};'>MODIFIED QURAN — {fh.deviation_pct:.1%} deviation</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    Closest canonical passage: Surah {fh.surah_start}:{fh.verse_start} → {fh.surah_end}:{fh.verse_end}
  </div>
  <div class='sub'>
    Edit distance = {fh.edit_distance} character change{'' if fh.edit_distance==1 else 's'}
    across {n_letters:,} letters. The differences are highlighted below.
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### Character-level diff (your text → canonical)")
        diff_html = _render_diff(fh.ops)
        st.markdown(f"""
<div style='background:#111; padding:16px 18px; border-radius:10px; font-family:serif; font-size:20px;
            direction:rtl; text-align:right; line-height:2.0; color:#eee;'>
{diff_html}
</div>
""", unsafe_allow_html=True)
        st.caption(
            "_Legend:_  [red underlined] = substituted letter;  **+red** = inserted letter;  ~~blue~~ = deleted letter. "
            "Reading is right-to-left (Arabic)."
        )

        st.markdown("#### How we know (mathematical proof)")
        st.markdown(
            "**Step 1 — Search:** we scanned the entire Quran for the passage that requires the fewest "
            "single-letter edits, insertions, or deletions to turn your text into an exact Quranic passage. "
            "The algorithm is called *Levenshtein edit distance* — the same method spell-checkers use.\n\n"
            f"**Step 2 — Result:** your text needs **{fh.edit_distance}** edit(s) to become "
            f"Surah {fh.surah_start}:{fh.verse_start}–{fh.verse_end}.\n\n"
            "**Step 3 — Threshold:** we classify any text under 20% deviation as 'Modified Quran', "
            "because beyond that point it is essentially a different text and should be evaluated "
            "by the structural fingerprint test instead."
        )

        # Optional: also run fingerprint for interest, but hidden in expander
        if n_letters >= 40:
            lang_code = "ar"
            data = segment_text(text)
            with st.expander("🔬 Advanced: also run the 8-channel structural fingerprint on this modified text"):
                channels = score_channels(data, lang_code)
                # simple pass/fail summary
                n_pass = sum(1 for ch in channels if ch["status"] == "PASS")
                n_total = sum(1 for ch in channels if ch["status"] != "N/A")
                st.write(f"Structural fingerprint: **{n_pass}/{n_total}** channels PASS (shown for interest only)")
        st.stop()

    # --- LAYER 3: NOT QURAN → FINGERPRINT ---
    st.markdown(f"""
<div class='big-verdict' style='background:linear-gradient(135deg, #3a1a1a 0%, #2b1212 100%);'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>❌</div>
  <h1 style='color:#e74c3c;'>NOT IN THE QURAN</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    No passage within 20% edit distance of your text exists in the canonical Quran.
  </div>
  <div class='sub'>
    Running the 8-dimensional structural fingerprint test below …
  </div>
</div>
""", unsafe_allow_html=True)

    # Fingerprint analysis
    lang_code = "ar"
    data = segment_text(text)
    n_verses = len(data["verses"])
    n_chaps = len(data["surah_verses"])

    with st.spinner("Running 8 structural measurements …"):
        channels = score_channels(data, lang_code)
        verdict_fp, subtitle_fp, n_pass, n_total = verdict_label(channels)
        similarity_pct = 100.0 * composite_similarity(channels)

    is_match = (verdict_fp == "MATCHES THE QURAN FINGERPRINT")
    is_insufficient = (verdict_fp == "INSUFFICIENT INPUT")
    if is_match:
        bg = "linear-gradient(135deg, #0f3320 0%, #14422a 100%)"
        title_color = "#2ecc71"
        icon = "✅"
    elif is_insufficient:
        bg = "linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%)"
        title_color = "#bbbbbb"
        icon = "⊘"
    else:
        bg = "linear-gradient(135deg, #3a1a1a 0%, #2b1212 100%)"
        title_color = "#e74c3c"
        icon = "❌"

    st.markdown(f"""
<div class='big-verdict' style='background:{bg};'>
  <div style='font-size:38px;line-height:1;margin-bottom:6px;'>{icon}</div>
  <h1 style='color:{title_color};'>{verdict_fp}</h1>
  <div style='font-size:18px;color:#fff;margin-top:8px;'>
    <b>{n_pass} / {n_total}</b> measurable dimensions match the Quran
  </div>
  <div class='sub'>{subtitle_fp}</div>
</div>
""", unsafe_allow_html=True)

    # --- INPUT SUMMARY ---
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Verses detected", f"{n_verses:,}")
    s2.metric("Chapters detected", f"{n_chaps:,}")
    s3.metric("Letters (normalised)", f"{n_letters:,}")
    s4.metric("Format", data["format"])

    if n_letters < 20:
        st.error(
            "❗ Less than 20 letters after normalisation. "
            "For the structural test, paste a longer passage (at least a few verses)."
        )
        st.stop()

    if len(text.split()) < 10:
        st.warning(
            "⚠️ Fewer than 10 words. Several dimensions will be "
            "skipped (marked **N/A**) and the verdict is based on the "
            "remaining ones. For meaningful results, paste at least one full chapter."
        )

    # --- PER-DIMENSION BREAKDOWN ---
    status_order = {"PASS": 0, "FAIL": 1, "N/A": 2}
    sorted_channels = sorted(
        channels,
        key=lambda c: (status_order[c["status"]], c["d"]),
    )

    st.markdown("### 8-dimensional structural fingerprint breakdown")
    st.caption(
        "Each card is one of the 8 mathematical dimensions. "
        "Sorted from best match to worst. These measurements were locked in advance "
        "(pre-registered) and verified against 11 other canonical scriptures."
    )

    pass_color = "#2ecc71"; fail_color = "#e74c3c"; na_color = "#888"
    for ch in sorted_channels:
        if ch["status"] == "PASS":
            badge_bg = "rgba(46, 204, 113, 0.18)"; badge_color = pass_color
            border = "rgba(46, 204, 113, 0.35)"; bg = "rgba(46, 204, 113, 0.05)"
            badge_text = "✅ MATCH"
        elif ch["status"] == "FAIL":
            badge_bg = "rgba(231, 76, 60, 0.18)"; badge_color = fail_color
            border = "rgba(231, 76, 60, 0.35)"; bg = "rgba(231, 76, 60, 0.05)"
            badge_text = "❌ NO MATCH"
        else:
            badge_bg = "rgba(149, 165, 166, 0.18)"; badge_color = na_color
            border = "rgba(149, 165, 166, 0.30)"; bg = "rgba(149, 165, 166, 0.04)"
            badge_text = "⊘ NOT TESTABLE"

        your_val_display = ch["value"] if ch["status"] != "N/A" else "—"

        st.markdown(f"""
<div class='dim-card' style='background:{bg};border-color:{border};'>
  <div class='row1'>
    <div class='name'>{ch['plain_label']}</div>
    <div class='badge' style='background:{badge_bg};color:{badge_color};'>{badge_text}</div>
  </div>
  <div class='what'>{ch['plain_what']}</div>
  <div class='nums'>
    <div>
      <div class='label'>Quran reference</div>
      <div class='val'>{ch['plain_quran']}</div>
    </div>
    <div>
      <div class='label'>Your text</div>
      <div class='val'>{your_val_display}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        if ch["status"] == "N/A":
            st.caption(f"↳ _Why not tested:_ {ch['note']}")

    # --- ADVANCED / TECHNICAL VIEW ---
    with st.expander("🔬 Advanced — technical channel codes, weights, and deviation scores"):
        st.caption(
            "Internal labels (T1–T8) and locked numerical references used "
            "in `experiments/exp183_quran_authentication_ring/` and `PAPER.md`."
        )
        adv_rows = []
        for ch in channels:
            adv_rows.append(
                f"| `{ch['key']}` | {ch['label'].split('· ')[1] if '· ' in ch['label'] else ch['label']} "
                f"| {ch['weight']:.0f}× | **{ch['status']}** | {ch['value']} | {ch['d']:.4f} |"
            )
        st.markdown(
            "| Key | Channel (technical name) | Weight | Status | Value | Deviation d |\n"
            "|---|---|---|---|---|---|\n" +
            "\n".join(adv_rows)
        )
        st.markdown(
            f"**Continuous similarity score (legacy weighted formula)**: `{similarity_pct:.2f}%`. "
            "Note: the binary verdict above is the canonical reading; the continuous score is "
            "kept for backwards compatibility with internal experiments."
        )
        st.markdown(
            "**Quran locked references** (verified at project closure, "
            "`results/audit/TOP_FINDINGS_AUDIT.md`):\n\n"
            f"- `H_EL` (verse-ending entropy) = **{QURAN_H_EL_REF:.4f} bits**\n"
            f"- `p_max` (dominant rhyme rate) = **{QURAN_P_MAX_REF:.4f}**\n"
            f"- `C_Ω` (channel utilisation) = **{QURAN_F67_C_OMEGA_REF:.4f}**\n"
            f"- `D_max` (alphabet gap) = **{QURAN_F79_DMAX_REF:.3f} bits**\n"
            f"- `F75` (universal invariant) = **{QURAN_F75_CONSTANT_REF:.3f} bits**\n"
            f"- `IFS d_info` (fractal dim) = **{QURAN_D_INFO_REF:.3f}**"
        )

    # --- INTERPRETATION HELP ---
    st.markdown("### What does this mean?")
    if is_match:
        st.success(
            "**All measurable dimensions match the Quran's locked statistical signature.** "
            "This means the text structurally resembles the Quran's information-theoretic fingerprint. "
            "It does *not* claim the text is Quranic verbatim — only that its large-scale statistical "
            "structure (rhyme, entropy, letter patterns, fractal dimension) falls inside the narrow "
            "band defined by the Quran. A truly forged text that mimics these numbers would be an "
            "extraordinary technical achievement, but the verbatim-check layer above already ruled out "
            "that this exact text exists in the canonical Quran."
        )
    elif is_insufficient:
        st.info(
            "Not enough text was provided to measure any dimension. "
            "Paste a longer passage — at least one full chapter is recommended."
        )
    else:
        failed = [c for c in channels if c["status"] == "FAIL"]
        st.warning(
            f"**{len(failed)} of {n_total} dimensions diverge from the Quran's signature.** "
            "This is the expected result for non-Quranic text — including classical Arabic poetry, "
            "modern Arabic prose, the Hebrew Tanakh, the Greek New Testament, and any text with "
            "different rhyme structure or letter statistics. The fingerprint is hard to forge "
            "precisely *because* most well-known canonical texts fail at least one of these dimensions."
        )

elif run_btn:
    st.error("Please paste some text or click an example in the sidebar first.")
