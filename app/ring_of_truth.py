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


def verdict_label(similarity_pct):
    if similarity_pct >= 95:
        return ("QURAN-CLASS", "Matches the Quran fingerprint within minor-variant "
                "tolerance (e.g. canonical qira'at).")
    if similarity_pct >= 80:
        return ("QURAN-LIKE", "Highly structured rhymed text; same information-theoretic "
                "régime as the Quran, but not identical.")
    if similarity_pct >= 50:
        return ("RHYMED LITERARY CORPUS", "Poetic / rhymed but not a Quran fingerprint match.")
    return ("NON-RHYMED / MODERN PROSE", "No literary-rhyme signature detected.")


# ======================================================================
# UI
# ======================================================================
st.set_page_config(page_title="Ring of Truth — QSF", page_icon="◎", layout="wide")

st.title("◎ Ring of Truth")
st.caption(
    "An 8-channel information-theoretic meter for Quran-fingerprint "
    "authenticity. Paste any text; the tool reports how close it is to the "
    "Quran's locked statistical signature."
)

with st.sidebar:
    st.header("Language")
    lang_code = st.selectbox(
        "Input script",
        options=list(_LANGS.keys()),
        format_func=lambda c: _LANGS[c]["name"],
        index=0,
    )
    st.markdown(f"**Alphabet size A = {_LANGS[lang_code]['A']}**")
    if lang_code != "ar":
        st.info(
            "ℹ︎ Reference values are the Quran's locked Arabic scalars. "
            "A perfect score in a non-Arabic script would mean the text "
            "matches the Quran's information-theoretic fingerprint in a "
            "different alphabet — exceptionally rare."
        )
    st.markdown("---")
    st.subheader("How to score")
    st.markdown("""
- Each channel outputs a **deviation d ∈ [0,1]** from the Quran reference.
- Channels **T1, T6, T7** count **2×** (hard-to-forge structural tests).
- T2–T5, T8 count **1×** (entropy tests).
- **Similarity = 1 − Σ(wᵢ·dᵢ) / Σ(wᵢ)**, displayed as a percentage.
- N/A channels (short input, missing structure) are excluded from the mean.
    """)

# Input panel
left, right = st.columns([2, 1])
with left:
    st.subheader("Input text")
    up = st.file_uploader("Upload a .txt file", type=["txt", "md"])
    default_text = ""
    if up is not None:
        default_text = up.read().decode("utf-8", errors="replace")
    text = st.text_area(
        "…or paste text directly. Use `|` to separate verses, or newlines. "
        "Pipe-delimited `sura|ayah|text` is auto-detected.",
        value=default_text,
        height=280,
    )
with right:
    st.subheader("Quran reference values")
    st.markdown(f"""
| Scalar | Value |
|---|---|
| median H_EL | **{QURAN_H_EL_REF:.4f} bits** |
| median p_max | **{QURAN_P_MAX_REF:.4f}** |
| C_Ω | **{QURAN_F67_C_OMEGA_REF:.4f}** |
| D_max | **{QURAN_F79_DMAX_REF:.3f} bits** |
| F75 invariant | **{QURAN_F75_CONSTANT_REF:.3f} bits** |
| IFS d_info | **{QURAN_D_INFO_REF:.3f}** |
    """)

run_btn = st.button("Compute Ring of Truth", type="primary", use_container_width=True)

if run_btn and text.strip():
    data = segment_text(text)
    n_letters = len(normalise_text(text, lang_code))
    n_verses = len(data["verses"])
    n_chaps = len(data["surah_verses"])

    # Warnings for fragile-size input
    warn_short_words = len(text.split()) < 10
    if warn_short_words:
        st.warning(
            "Input has fewer than 10 words. Results may be unstable; "
            "consider pasting a longer passage."
        )

    with st.spinner("Scoring 8 channels…"):
        channels = score_channels(data, lang_code)
        similarity = composite_similarity(channels)
        similarity_pct = 100.0 * similarity
        verdict, verdict_desc = verdict_label(similarity_pct)

    st.markdown("### Input summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Format", data["format"])
    c2.metric("Verses", f"{n_verses:,}")
    c3.metric("Chapters", f"{n_chaps:,}")
    c4.metric("Letters (normalised)", f"{n_letters:,}")

    st.markdown("### Per-channel deviation")
    cols = st.columns(4)
    for i, ch in enumerate(channels):
        with cols[i % 4]:
            # Colour: green near 0, red near 1
            d = ch["d"]
            pct_good = (1 - d) * 100 if ch["status"] != "N/A" else 0
            color = "#2ecc71" if d < 0.2 else ("#f1c40f" if d < 0.5 else "#e74c3c")
            if ch["status"] == "N/A":
                color = "#95a5a6"
            badge = {"PASS": "✅", "FAIL": "❌", "N/A": "⊘"}[ch["status"]]
            st.markdown(
                f"""
<div style='padding:10px;border-radius:12px;background:#181818;margin-bottom:8px;'>
  <div style='font-size:14px;color:#ddd;'>{badge} <b>{ch['label']}</b> · weight {ch['weight']:.0f}×</div>
  <div style='height:10px;border-radius:6px;background:#2a2a2a;margin:6px 0;'>
    <div style='width:{pct_good:.0f}%;height:100%;border-radius:6px;background:{color};'></div>
  </div>
  <div style='font-size:13px;color:#bbb;'>value: <b style='color:#fff;'>{ch['value']}</b></div>
  <div style='font-size:13px;color:#bbb;'>deviation d = <b style='color:{color};'>{ch['d']:.3f}</b></div>
  <div style='font-size:11px;color:#888;margin-top:4px;'>{ch['note']}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # Big similarity meter
    st.markdown("### Overall similarity to the Quran fingerprint")
    meter_color = (
        "#2ecc71" if similarity_pct >= 95
        else "#27ae60" if similarity_pct >= 80
        else "#f1c40f" if similarity_pct >= 50
        else "#e74c3c"
    )
    st.markdown(
        f"""
<div style='padding:24px;border-radius:16px;background:#111;text-align:center;'>
  <div style='font-size:72px;font-weight:700;color:{meter_color};line-height:1;'>{similarity_pct:.1f}%</div>
  <div style='height:14px;border-radius:7px;background:#2a2a2a;margin:14px 80px;'>
    <div style='width:{similarity_pct:.1f}%;height:100%;border-radius:7px;background:{meter_color};'></div>
  </div>
  <div style='font-size:28px;font-weight:600;color:#fff;margin-top:8px;'>{verdict}</div>
  <div style='font-size:14px;color:#aaa;margin-top:4px;'>{verdict_desc}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Notes")
    st.markdown("""
- The 8 channels test **information-theoretic universals** (entropy, redundancy,
  rhyme concentration, fractal dimension, dual-mode contrast), not semantics or theology.
  A high score means the text's measurable **statistical structure** matches the Quran's,
  to within the tolerance each channel pre-registers — nothing more, nothing less.
- Passing **every** channel does *not* prove authenticity in any metaphysical sense;
  a deliberately forged text that exactly copied the Quran's letter frequencies and verse-final
  distribution would pass T2–T5. Channels **T1**, **T6**, **T7** (higher-weighted) are
  specifically designed to catch structural forgeries that preserve letter frequencies.
- The underlying constants (H_EL=0.9685, p_max=0.7273, C_Ω=0.7985, D_max=3.84,
  F75=5.316) were re-verified from raw corpus data at project closure;
  see `results/audit/TOP_FINDINGS_AUDIT.md` for the audit.
- Future versions may replace the fixed Quran reference with a configurable
  per-language reference set (currently only Arabic has empirically-locked scalars).
    """)

elif run_btn:
    st.error("Please paste or upload some text first.")
