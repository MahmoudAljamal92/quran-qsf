"""Pristine — the Quran fingerprint detector.

Four-layer analysis of any text against the canonical Hafs corpus:
  Layer A — verbatim + near-verbatim lookup
  Layer B — 8 whole-corpus fingerprint axes, length-calibrated
  Layer C — tampering forensics (F55 bigram-shift, F70 gzip-NCD)
  Layer D — cross-tradition context (non-Arabic input)

Every numeric reference is either computed at startup from the
SHA-256-locked Quran corpus, or cited to a locked experiment receipt.
No learned weights, no per-surah cherry-picking, no hidden corpus access.

Run:
    streamlit run app/pristine.py
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import streamlit as st

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from pristine_lib import constants as C  # noqa: E402
from pristine_lib import calibration, corpus, examples, metrics  # noqa: E402
from pristine_lib.normalize import (  # noqa: E402
    detect_script,
    normalize_arabic_letters_only,
    split_into_verses,
)


# =============================================================================
# Page setup + modern CSS (monochrome + single gold accent)
# =============================================================================
st.set_page_config(
    page_title="Pristine — Quran fingerprint",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
/* ---- Typography (TWO families only) ------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --ink:        #0b0d10;
  --ink-2:      #1f242c;
  --ink-soft:   #535a66;
  --ink-muted:  #9099a8;
  --line:       #e6e3dc;
  --line-soft:  #efeee8;
  --paper:      #fbfaf5;
  --paper-2:    #ffffff;

  --gold:       #b18a3a;
  --gold-soft:  #f2e9c8;
  --gold-tint:  #fdf6e3;

  --green:      #0d6b47;
  --green-soft: #d6ecdf;
  --amber:      #9a5a00;
  --amber-soft: #f5e2c1;
  --red:        #a91e1e;
  --red-soft:   #f5d8d8;

  --sans:   'Inter', -apple-system, 'Segoe UI', Roboto, system-ui, sans-serif;
  --mono:   'JetBrains Mono', ui-monospace, SFMono-Regular, Consolas, monospace;

  --shadow-sm: 0 1px 2px rgba(11,13,16,0.04), 0 0 0 1px rgba(11,13,16,0.04);
  --shadow-md: 0 4px 18px -4px rgba(11,13,16,0.08), 0 0 0 1px rgba(11,13,16,0.04);
}

/* ---- Global page -------------------------------------------------------- */
html, body, [class*="block-container"], [data-testid="stAppViewContainer"] {
  background: var(--paper) !important;
  color: var(--ink);
  font-family: var(--sans);
  font-feature-settings: "ss01", "cv11";
}
.block-container {
  padding-top: 1.6rem !important;
  padding-bottom: 6rem !important;
  max-width: 1280px;
}

/* Hide Streamlit chrome we don't want */
#MainMenu, header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }

/* ---- Typography hierarchy (Inter only, weight-driven) ------------------ */
h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.02em; font-family: var(--sans); }
h1 {
  font-weight: 800;
  font-size: 2.0rem;
  line-height: 1.1;
  margin: 0 0 0.3rem 0;
  letter-spacing: -0.03em;
}
h2 {
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--ink-soft);
  margin: 1.6rem 0 0.7rem 0;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.55rem;
}
h3 {
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--ink);
  margin: 1rem 0 0.4rem 0;
}
p, li { color: var(--ink-2); line-height: 1.55; }

/* ---- Eyebrow + tagline -------------------------------------------------- */
.eyebrow {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
  background: var(--gold-tint);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  margin-bottom: 0.8rem;
  border: 1px solid var(--gold-soft);
}
.tagline {
  font-family: var(--sans);
  font-weight: 400;
  font-size: 1.0rem;
  color: var(--ink-soft);
  margin: 0.4rem 0 1.6rem 0;
  max-width: 760px;
  line-height: 1.55;
}

/* ---- Verdict ribbon (hero card) ---------------------------------------- */
.verdict {
  display: grid;
  grid-template-columns: 58px 1fr auto;
  align-items: center;
  gap: 1.2rem;
  padding: 1.2rem 1.4rem;
  border-radius: 10px;
  background: var(--paper-2);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--line);
  margin: 0.4rem 0 1.6rem 0;
}
.verdict .sigil {
  width: 46px; height: 46px;
  display: grid; place-items: center;
  font-family: var(--mono);
  font-size: 1.4rem; font-weight: 600;
  border-radius: 10px;
  background: var(--paper); color: var(--ink-soft);
  border: 1px solid var(--line);
}
.verdict .title {
  font-family: var(--sans);
  font-weight: 700;
  font-size: 1.3rem;
  color: var(--ink);
  letter-spacing: -0.02em;
  line-height: 1.25;
}
.verdict .subtitle {
  font-size: 0.86rem;
  color: var(--ink-soft);
  margin-top: 0.18rem;
  max-width: 70ch;
  line-height: 1.5;
}
.verdict .score {
  font-family: var(--mono);
  font-size: 1.4rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.verdict .score .pct {
  font-size: 0.66rem; color: var(--ink-muted);
  font-family: var(--sans); letter-spacing: 0.1em;
  text-transform: uppercase; display: block;
  margin-top: 0.05rem; font-weight: 500;
}

.verdict.ok         { background: linear-gradient(180deg, #f7fcf9 0%, var(--paper-2) 100%); border-color: var(--green-soft); }
.verdict.ok .sigil  { background: var(--green); color: white; border-color: var(--green); }
.verdict.ok .score  { color: var(--green); }

.verdict.warn       { background: linear-gradient(180deg, #fdf7ec 0%, var(--paper-2) 100%); border-color: var(--gold-soft); }
.verdict.warn .sigil{ background: var(--gold); color: white; border-color: var(--gold); }
.verdict.warn .score{ color: var(--gold); }

.verdict.err        { background: linear-gradient(180deg, #fcf2f2 0%, var(--paper-2) 100%); border-color: var(--red-soft); }
.verdict.err .sigil { background: var(--red); color: white; border-color: var(--red); }
.verdict.err .score { color: var(--red); }

.verdict.neut .sigil{ background: var(--ink); color: white; border-color: var(--ink); }

/* ---- Layer card --------------------------------------------------------- */
.layer {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 1.1rem 1.3rem 1.2rem 1.3rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow-sm);
}
.layer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  margin-bottom: 0.7rem;
}
.layer-name {
  display: flex; align-items: baseline; gap: 0.6rem;
  font-weight: 600; font-size: 0.95rem; color: var(--ink);
}
.layer-name .num {
  font-family: var(--mono); font-size: 0.7rem;
  color: var(--ink-muted); letter-spacing: 0.1em;
  font-weight: 500;
}
.layer-tag {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--ink-muted);
  padding: 0.12rem 0.5rem;
  border-radius: 3px;
  background: var(--line-soft);
}
.layer-summary {
  color: var(--ink-2);
  font-size: 0.9rem;
  line-height: 1.58;
  margin-bottom: 0.4rem;
}
.layer .kv, .kv {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--ink-soft);
  font-variant-numeric: tabular-nums;
}
.kv b { color: var(--ink); font-weight: 600; }

.pill {
  display: inline-block;
  font-family: var(--mono); font-size: 0.66rem;
  text-transform: uppercase; letter-spacing: 0.1em;
  padding: 0.17rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink-soft);
  font-weight: 500;
}
.pill.ok   { color: var(--green); background: var(--green-soft); border-color: var(--green-soft); }
.pill.warn { color: var(--amber); background: var(--amber-soft); border-color: var(--amber-soft); }
.pill.err  { color: var(--red);   background: var(--red-soft);   border-color: var(--red-soft); }
.pill.gold { color: var(--gold);  background: var(--gold-tint);  border-color: var(--gold-soft); }

/* ---- Axis table --------------------------------------------------------- */
.axis-table { margin-top: 0.6rem; }
.axis-row {
  display: grid;
  grid-template-columns: 1.7fr 1.3fr 0.8fr 1.6fr 0.6fr;
  align-items: center; gap: 0.9rem;
  padding: 0.62rem 0.2rem;
  border-bottom: 1px solid var(--line-soft);
  font-size: 0.87rem;
}
.axis-row:last-child { border-bottom: none; }
.axis-row.head {
  border-bottom: 1.5px solid var(--ink);
  padding-bottom: 0.38rem;
  font-family: var(--mono);
  font-size: 0.66rem; text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-soft); font-weight: 500;
}
.axis-row.deciding {
  background: var(--gold-tint);
  border-radius: 6px;
  padding: 0.62rem 0.6rem;
  border-bottom-color: var(--gold-soft);
}
.axis-name { color: var(--ink); font-weight: 500; font-size: 0.9rem; }
.axis-name .symbol {
  font-family: var(--mono);
  color: var(--ink-muted);
  margin-left: 0.4rem; font-size: 0.76rem;
}
.axis-num {
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  color: var(--ink); font-size: 0.82rem;
}
.axis-num.range { color: var(--ink-soft); font-size: 0.75rem; }
.bar-track {
  background: var(--line-soft);
  border-radius: 999px;
  height: 5px;
  overflow: hidden;
}
.bar-fill {
  height: 100%; border-radius: 999px;
  transition: width 0.4s ease;
}
.bar-fill.green { background: var(--green); }
.bar-fill.amber { background: var(--amber); }
.bar-fill.red   { background: var(--red); }
.bar-fill.gray  { background: var(--ink-muted); }
.match-pct {
  font-family: var(--mono);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  text-align: right;
  font-size: 0.88rem;
}
.match-pct.green { color: var(--green); }
.match-pct.amber { color: var(--amber); }
.match-pct.red   { color: var(--red); }
.match-pct.gray  { color: var(--ink-muted); }

/* ---- Callout + deciding axis ------------------------------------------- */
.deciding {
  background: var(--gold-tint);
  border: 1px solid var(--gold-soft);
  border-left: 3px solid var(--gold);
  padding: 0.75rem 0.95rem;
  border-radius: 0 6px 6px 0;
  margin: 0.5rem 0 0.8rem 0;
  font-size: 0.88rem;
  line-height: 1.55;
}
.deciding .label {
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--gold);
  font-weight: 600;
  margin-bottom: 0.2rem;
}
.callout {
  background: var(--paper);
  border: 1px solid var(--line);
  border-left: 3px solid var(--ink-muted);
  padding: 0.75rem 0.95rem;
  border-radius: 0 6px 6px 0;
  margin: 0.5rem 0 0.8rem 0;
  font-size: 0.86rem;
  line-height: 1.55;
  color: var(--ink-2);
}
.callout.info { border-left-color: var(--gold); background: var(--gold-tint); }
.callout.note { border-left-color: var(--ink-soft); }

.fine-print {
  color: var(--ink-soft);
  font-size: 0.8rem;
  line-height: 1.55;
}

/* ---- Stat grid (input meta) -------------------------------------------- */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.8rem;
  margin: 0.5rem 0 0.8rem 0;
}
.stat-card {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.65rem 0.8rem;
}
.stat-card .lbl {
  font-family: var(--mono); font-size: 0.64rem;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--ink-muted); font-weight: 500;
}
.stat-card .val {
  font-family: var(--mono); font-size: 1.1rem;
  font-weight: 600; color: var(--ink);
  font-variant-numeric: tabular-nums;
  margin-top: 0.1rem;
}

/* ---- Input area (Arabic-first: RTL by default, browser flips for LTR via dir=auto) - */
.stTextArea textarea {
  font-family: 'Amiri', 'Scheherazade New', 'Traditional Arabic', var(--mono);
  font-size: 1.05rem;
  line-height: 1.9;
  background: var(--paper-2) !important;
  border: 1px solid var(--line) !important;
  border-radius: 8px !important;
  color: var(--ink) !important;
  caret-color: var(--gold);
  direction: rtl;
  text-align: right;
  unicode-bidi: plaintext;
}
.stTextArea textarea:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px var(--gold-tint) !important;
}
.stTextArea textarea::placeholder {
  direction: ltr;
  text-align: left;
  opacity: 0.55;
  font-family: var(--sans);
  font-size: 0.92rem;
}

/* ---- Buttons ----------------------------------------------------------- */
.stButton > button {
  border: 1px solid var(--line);
  background: var(--paper-2);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 0.86rem;
  font-weight: 500;
  padding: 0.45rem 0.95rem;
  border-radius: 8px;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}
.stButton > button:hover {
  border-color: var(--gold);
  color: var(--gold);
  transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* Primary action button — force WHITE text on every child element */
button[kind="primary"],
button[kind="primary"] *,
.stButton button[kind="primary"],
.stButton button[kind="primary"] *,
.stButton button[kind="primary"] p,
.stButton button[kind="primary"] div,
.stButton button[kind="primary"] span,
.stButton button[kind="primary"] [data-testid="stMarkdownContainer"] p {
  background: var(--ink) !important;
  color: #ffffff !important;
  border-color: var(--ink) !important;
  -webkit-text-fill-color: #ffffff !important;
}
.stButton button[kind="primary"] {
  font-weight: 700 !important;
  letter-spacing: 0.01em;
  font-size: 0.9rem !important;
  padding: 0.55rem 1.05rem !important;
}
.stButton button[kind="primary"]:hover {
  background: #1f242c !important;
  border-color: #1f242c !important;
  transform: translateY(-1px);
}
.stButton button[kind="primary"]:disabled,
.stButton button[kind="primary"][disabled] {
  background: #c9c8c0 !important;
  border-color: #c9c8c0 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  cursor: not-allowed;
  transform: none;
}

/* ---- Sidebar ---------------------------------------------------------- */
[data-testid="stSidebar"] {
  background: var(--paper-2) !important;
  border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.2rem !important;
}
[data-testid="stSidebar"] h2 { font-size: 0.68rem; margin-top: 1.2rem; }
[data-testid="stSidebar"] h3 { font-size: 0.84rem; margin-top: 0.9rem; }
[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  text-align: left;
  padding: 0.4rem 0.7rem;
  font-size: 0.82rem;
  justify-content: flex-start;
  border-radius: 6px;
  box-shadow: none;
}
[data-testid="stSidebar"] .brand {
  font-family: var(--sans);
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: -0.03em;
  margin-bottom: 0.15rem;
}
[data-testid="stSidebar"] .brand-sub {
  font-family: var(--mono);
  font-size: 0.66rem;
  color: var(--ink-muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 0.9rem;
}

/* ---- Expanders --------------------------------------------------------- */
details[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 8px !important;
  background: var(--paper-2) !important;
}
details[data-testid="stExpander"] summary { font-size: 0.88rem; font-weight: 500; }

/* ---- Progress bar ----------------------------------------------------- */
[data-testid="stProgress"] > div > div > div { background: var(--gold) !important; }

/* ---- Small text, links ----------------------------------------------- */
a { color: var(--gold); text-decoration: none; border-bottom: 1px dotted var(--gold-soft); }
a:hover { color: var(--ink); border-bottom-color: var(--ink); }
hr { border: none; border-top: 1px solid var(--line); margin: 1.2rem 0; }
.muted { color: var(--ink-soft); }

/* RTL support for Arabic text display */
.rtl-text {
  direction: rtl;
  text-align: right;
  font-family: 'Amiri', 'Scheherazade New', 'Traditional Arabic', serif;
  font-size: 1.15rem;
  line-height: 2;
  background: var(--paper);
  padding: 0.6rem 0.9rem;
  border-radius: 6px;
  border: 1px solid var(--line);
}

/* ---- Per-axis row hover + expander chevron ---------------------------- */
.axis-detail {
  background: var(--line-soft);
  border-radius: 6px;
  padding: 0.7rem 0.95rem;
  margin: 0.3rem 0 0.5rem 0;
  font-size: 0.84rem;
  color: var(--ink-2);
  line-height: 1.55;
}
.axis-detail .label {
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-soft);
  font-weight: 600;
  margin-bottom: 0.3rem;
}
.axis-detail .ranges {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.7rem;
  margin-top: 0.45rem;
}
.axis-detail .range-card {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 0.45rem 0.6rem;
}
.axis-detail .range-card .lbl {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-muted);
  font-weight: 500;
}
.axis-detail .range-card .val {
  font-family: var(--mono);
  font-size: 0.85rem;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  margin-top: 0.1rem;
}

/* ---- Section sub-headers within the input panel --------------------- */
.section-eyebrow {
  font-family: var(--mono);
  font-size: 0.66rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-muted);
  font-weight: 500;
  margin-bottom: 0.4rem;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =============================================================================
# Boot: verify corpus, compute Quran references, warm k-gram index
# =============================================================================
@st.cache_resource(show_spinner="Loading canonical Hafs corpus…")
def boot():
    integrity = C.verify_quran_corpus()
    verses = corpus.all_verses()
    raw_verse_strs = [v.raw for v in verses]
    skel_full = "".join(v.skeleton for v in verses)
    verse_lens = np.array([len(v.skeleton) for v in verses], dtype=float)

    he = metrics.pooled_H_EL_pmax(raw_verse_strs)
    di = metrics.d_info(skel_full)
    hfd = metrics.higuchi_fd(verse_lens)
    da = metrics.delta_alpha_mfdfa(verse_lens)

    # Warm the k-gram index for fuzzy lookups.
    corpus._kgram_index()  # noqa: SLF001

    return {
        "integrity": integrity,
        "n_chapters": corpus.n_chapters(),
        "n_verses": len(verses),
        "n_letters": corpus.total_letters(),
        "ref": {
            "H_EL": he["H_EL"],
            "p_max": he["p_max"],
            "C_Omega": he["C_Omega"],
            "F75": he["F75"],
            "D_max": he["D_max"],
            "d_info": di,
            "HFD": hfd,
            "Delta_alpha": da,
        },
    }


try:
    BOOT = boot()
except Exception as e:  # noqa: BLE001
    st.error(f"**Cannot start.** {e}")
    st.stop()


# =============================================================================
# Analysis pipeline — computed ONCE per "Run" click, cached in session_state.
# =============================================================================
_AXIS_DEFS = [
    ("H_EL",        "Verse-final entropy",       "H_EL",
     "How predictable is the last letter of each verse (in bits)."),
    ("p_max",       "Rhyme concentration",       "p_max",
     "Fraction of verses ending on the single most common letter."),
    ("C_Omega",     "Channel utilisation",       "C_Ω",
     "How much of the alphabet's information capacity the rhyme uses. 0 = none, 1 = full."),
    ("F75",         "Universal invariant",       "F75",
     "Single-number signature at which 11 scriptures cluster (5.75 bits ± 5%)."),
    ("D_max",       "Redundancy gap",            "D_max",
     "How much rarer verse-final letters are than uniform random. log₂(28) − H_EL."),
    ("d_info",      "Fractal dimension",         "d_info",
     "Information dimension of the letter-frequency distribution at contraction c = 0.18."),
    ("HFD",         "Higuchi dimension",         "HFD",
     "Roughness of the verse-length series. 1.0 = Brownian; lower = smoother."),
    ("Delta_alpha", "Multifractal width",        "Δα",
     "Width of the multifractal spectrum — scale-dependence of verse-length variability."),
]


def _hash_input(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _compute_input_axes(input_text: str):
    verses = split_into_verses(input_text)
    skel_full = normalize_arabic_letters_only(input_text)
    he = metrics.pooled_H_EL_pmax(verses)
    di = metrics.d_info(skel_full)
    verse_lens = np.array(
        [len(normalize_arabic_letters_only(v)) for v in verses],
        dtype=float,
    )
    hfd = metrics.higuchi_fd(verse_lens) if verse_lens.size >= 32 else float("nan")
    da = metrics.delta_alpha_mfdfa(verse_lens) if verse_lens.size >= 64 else float("nan")
    return {
        "n_verses": len(verses),
        "n_letters": len(skel_full),
        "H_EL": he["H_EL"], "p_max": he["p_max"], "C_Omega": he["C_Omega"],
        "F75": he["F75"], "D_max": he["D_max"],
        "d_info": di, "HFD": hfd, "Delta_alpha": da,
    }


def analyse(input_text: str, progress=None):
    """Run the full 4-layer pipeline. `progress` is a callable(frac, msg)."""
    out = {"input_text": input_text, "hash": _hash_input(input_text)}

    def step(frac, msg):
        if progress:
            progress(frac, msg)

    # --- Normalisation + script detection --------------------------------
    step(0.05, "Normalising input…")
    script = detect_script(input_text)
    skel = normalize_arabic_letters_only(input_text)
    out["script"] = script
    out["skel"] = skel
    out["n_letters"] = len(skel)

    # --- Layer A: identity -----------------------------------------------
    step(0.15, "Layer A · verbatim lookup…")
    a_status = "miss"
    a_hit = None
    if script == "ar" and len(skel) >= 12:
        exact = corpus.exact_match(skel)
        if exact is not None:
            a_status = "exact"
            a_hit = exact
        else:
            step(0.28, "Layer A · near-verbatim search…")
            fh = corpus.fuzzy_match(skel)
            if fh is not None and fh.deviation_pct < 10.0:
                a_status = "fuzzy"
                a_hit = fh
    elif script != "ar":
        a_status = "skip_nonarabic"
    else:
        a_status = "skip_short"
    out["layer_a"] = {"status": a_status, "hit": a_hit}

    # --- Layer B: fingerprint --------------------------------------------
    step(0.45, "Layer B · computing 8 fingerprint axes…")
    inp = _compute_input_axes(input_text)
    out["input_axes"] = inp

    layer_b = {"status": "skip_short", **inp, "rows": [], "composite": float("nan")}
    if inp["n_letters"] >= 42 and inp["n_verses"] >= 3:
        rows = []
        n_axes = len(_AXIS_DEFS)
        for i, (key, name, sym, _exp) in enumerate(_AXIS_DEFS):
            step(0.5 + 0.35 * (i / n_axes), f"Layer B · calibrating {sym}…")
            you = inp[key]
            ref = BOOT["ref"][key]
            if not np.isfinite(you):
                rows.append({"key": key, "name": name, "sym": sym,
                             "you": you, "ref": ref, "match": float("nan"),
                             "percentile": float("nan"), "q_lo": float("nan"),
                             "q_hi": float("nan"), "q_median": float("nan"),
                             "inside_p80": False})
                continue
            try:
                r = calibration.length_calibrated_match(key, you, inp["n_verses"])
            except Exception:  # noqa: BLE001
                r = {"match_pct": metrics.match_pct(you, ref, C.DISPLAY_TOLERANCES[key]),
                     "percentile": float("nan"), "inside_p80": False,
                     "distribution": None}
            dist = r.get("distribution")
            rows.append({
                "key": key, "name": name, "sym": sym,
                "you": you, "ref": ref,
                "match": r["match_pct"],
                "percentile": r["percentile"],
                "q_lo": dist.vmin if dist is not None else float("nan"),
                "q_hi": dist.vmax if dist is not None else float("nan"),
                "q_median": dist.median if dist is not None else float("nan"),
                "p10": dist.p10 if dist is not None else float("nan"),
                "p90": dist.p90 if dist is not None else float("nan"),
                "n_windows": dist.n_windows if dist is not None else 0,
                "inside_p80": r.get("inside_p80", False),
                "explainer": _exp,
            })
        valid = [r for r in rows if np.isfinite(r["match"])]
        composite = float(np.mean([r["match"] for r in valid])) if valid else float("nan")
        deciding = min(valid, key=lambda r: r["match"]) if valid else None
        layer_b = {
            "status": "ok", "rows": rows, "composite": composite,
            "deciding": deciding,
            "inside_count": sum(1 for r in valid if r["inside_p80"]),
            "n_axes": len(valid),
            **inp,
        }
    out["layer_b"] = layer_b

    # --- Layer C: tampering forensics ------------------------------------
    step(0.88, "Layer C · tampering forensics…")
    layer_c = {"status": "skip_far"}
    if a_status in ("exact", "fuzzy"):
        if a_status == "exact":
            canonical_skel = skel
            canonical_raw = "(canonical text matches your input exactly)"
        else:
            canonical_skel = a_hit.canonical_skeleton
            canonical_raw = a_hit.canonical_raw
        bd = metrics.bigram_shift_delta(skel, canonical_skel)
        ncd = metrics.gzip_ncd(skel, canonical_skel)
        edit_min = max(0, int(np.ceil(bd / 2.0))) if bd > 0 else 0
        layer_c = {
            "status": "ok",
            "bigram_d": bd, "ncd": ncd, "edit_min": edit_min,
            "canonical_raw": canonical_raw,
        }
    out["layer_c"] = layer_c

    step(1.0, "Done.")
    return out


# =============================================================================
# Rendering helpers
# =============================================================================
def _bucket(pct: float) -> str:
    if not np.isfinite(pct):
        return "gray"
    if pct >= 80:
        return "green"
    if pct >= 50:
        return "amber"
    return "red"


def render_verdict(result: dict):
    a = result["layer_a"]["status"]
    b = result["layer_b"]
    c = result["layer_c"]
    n_verses = result["input_axes"]["n_verses"]
    n_letters = result["input_axes"]["n_letters"]
    composite = b.get("composite", float("nan"))

    def _row(kind, sigil, title, subtitle, score_num="", score_lbl=""):
        score_html = ""
        if score_num:
            score_html = (f'<div class="score">{score_num}'
                          f'<span class="pct">{score_lbl}</span></div>')
        st.markdown(
            f'<div class="verdict {kind}">'
            f'<div class="sigil">{sigil}</div>'
            f'<div><div class="title">{title}</div>'
            f'<div class="subtitle">{subtitle}</div></div>'
            f'{score_html}</div>',
            unsafe_allow_html=True,
        )

    if a == "skip_short" or b.get("status") == "skip_short":
        _row("neut", "?", "Input too short to decide",
             f"Need at least 3 verses AND 42 normalised Arabic letters "
             f"(shortest Quranic surah, Al-Kawthar). You gave {n_verses} verses, "
             f"{n_letters} letters.")
        return

    if a == "exact":
        ncd = c.get("ncd", 0.0) if c.get("status") == "ok" else 0.0
        bd = c.get("bigram_d", 0.0) if c.get("status") == "ok" else 0.0
        hit = result["layer_a"]["hit"]
        loc = (f"Surah {hit.surah}, ayah {hit.ayah_start}"
               f"{'' if hit.ayah_start == hit.ayah_end else f'–{hit.ayah_end}'}")
        sub = (f"Letter-for-letter match against the SHA-locked Hafs corpus · "
               f"{loc} · {hit.n_letters:,} normalised letters across {hit.n_verses} verse"
               f"{'s' if hit.n_verses != 1 else ''}.")
        if bd > 0.001 or ncd >= 0.10:
            sub += " Tampering forensics flagged — see Layer C."
        _row("ok", "✓", "Verbatim Quran", sub, "100%", "identity match")
        return

    if a == "fuzzy":
        hit = result["layer_a"]["hit"]
        bd = c.get("bigram_d", 0.0) if c.get("status") == "ok" else 0.0
        ncd = c.get("ncd", 0.0) if c.get("status") == "ok" else 0.0
        edits = c.get("edit_min", 0) if c.get("status") == "ok" else 0
        loc = (f"Surah {hit.surah}, ayah {hit.ayah_start}"
               f"{'' if hit.ayah_start == hit.ayah_end else f'–{hit.ayah_end}'}")
        preservation = 100.0 - hit.deviation_pct
        if bd > 0.001 and ncd < 0.20:
            kind_desc = (f"At least {edits} letter substitution"
                         f"{'s' if edits != 1 else ''} detected "
                         "(F55 bigram-shift). Sequence order preserved.")
        elif bd <= 0.001 and ncd >= 0.05:
            kind_desc = ("Letters identical to canonical but sequence order broken "
                         "(F70 gzip-NCD) — verse or word reordering.")
        elif bd > 0.001 and ncd >= 0.20:
            kind_desc = ("Both letter edits AND sequence reordering detected — "
                         "mixed tampering signature.")
        else:
            kind_desc = f"{hit.edit_distance} letter edit(s), {hit.deviation_pct:.2f}% deviation."
        _row("warn", "≈", "Modified Quran",
             f"{loc} · {kind_desc}",
             f"{preservation:.1f}%", "preservation")
        return

    if a == "skip_nonarabic":
        if np.isfinite(composite):
            _row("neut", "—", "Not Arabic — fingerprint compared anyway",
                 "Your text is not in the Arabic script so identity lookup is skipped. "
                 "The fingerprint below is computed regardless, on character-level statistics.",
                 f"{composite:.0f}%", "fingerprint")
        else:
            _row("neut", "—", "Not Arabic",
                 "Identity lookup is skipped. Too short for a fingerprint claim.")
        return

    # a == "miss"  —  Layer A says "not in the Quran corpus". The remaining
    # verdict is about whether the text is in the broad Arabic-rasm
    # rhymed-scripture CLASS (high Layer B) vs outside it (low Layer B).
    # It is NOT a Quran-identity claim: Layer B at short N cannot separate
    # Quran from well-formed classical Arabic poetry.
    n_verses = result["input_axes"]["n_verses"]

    if not np.isfinite(composite):
        _row("err", "✗", "Not Quran",
             "Not found in the canonical Hafs corpus, and too short to compute "
             "a class fingerprint. Provide a longer passage for more structural "
             "information.")
        return

    if composite >= 95:
        # Inside the Arabic-rasm rhymed-scripture class.
        if n_verses < 32:
            label = "Not Quran · in the Arabic-rasm rhymed-scripture class"
            desc = (f"Not a verbatim or near-verbatim Quranic passage. Its "
                    f"structural values sit inside the Quranic range on every "
                    f"measurable axis at N = {n_verses} — consistent with "
                    f"classical Arabic verse, rhymed prose, hadith, or an "
                    f"imitation. <b>At N &lt; 32 verses these axes measure "
                    f"class membership, not Quran-specific identity</b>, so "
                    f"this score is <u>expected</u> for Mu'allaqa-style "
                    f"classical poetry too. The Quran-unique signatures "
                    f"(F87 multifractal fingerprint, F76 corpus-aggregate) "
                    f"require N ≥ 64 or a whole-surah input and cannot fire here.")
        else:
            label = "Not Quran · but structurally Quran-like"
            desc = (f"Not a verbatim or near-verbatim Quranic passage. At "
                    f"N = {n_verses} the full fingerprint including HFD "
                    f"(and Δα at N ≥ 64) is active and your values still sit "
                    f"inside the Quranic range — rare for non-Quranic text at "
                    f"this length. Possible: long classical saj' composition, "
                    f"very skilled imitation, or data that shares the Quran's "
                    f"multifractal signature.")
        _row("warn", "≈", label, desc, f"{composite:.0f}%", "class-match")
        return

    if composite >= 60:
        _row("warn", "≈", "Not Quran · partial class membership",
             f"Not in the corpus. Some axes land inside the Quranic range, "
             f"others don't. At N = {n_verses} this suggests Arabic text "
             f"with partial overlap with the rhymed-scripture class "
             f"(e.g. some rhyme structure without full channel saturation).",
             f"{composite:.0f}%", "class-match")
        return

    if composite >= 30:
        _row("err", "✗", "Not Quran",
             f"Not in the corpus. Structurally outside the Arabic-rasm "
             f"rhymed-scripture class on the deciding axes.",
             f"{composite:.0f}%", "class-match")
        return

    _row("err", "✗", "Not Quran",
         f"Not in the corpus. Structural profile is far from the Arabic-rasm "
         f"rhymed-scripture class on every measurable axis.",
         f"{composite:.0f}%", "class-match")


# -----------------------------------------------------------------------------
def _layer_open(n, name, tag, summary=""):
    sum_html = f'<div class="layer-summary">{summary}</div>' if summary else ""
    st.markdown(
        f'<div class="layer">'
        f'<div class="layer-header">'
        f'<div class="layer-name"><span class="num">LAYER {n}</span> {name}</div>'
        f'<div class="layer-tag">{tag}</div>'
        f'</div>{sum_html}',
        unsafe_allow_html=True,
    )


def _layer_close():
    st.markdown("</div>", unsafe_allow_html=True)


def render_layer_a(result: dict):
    a = result["layer_a"]
    status = a["status"]

    if status == "skip_nonarabic":
        _layer_open("A", "Identity",
                    "verbatim + near-verbatim",
                    "Input is not Arabic; the canonical Hafs corpus is Arabic only. "
                    "This layer is skipped — Layer B still runs on character statistics.")
        st.markdown('<span class="pill">skipped · non-Arabic script</span>',
                    unsafe_allow_html=True)
        _layer_close()
        return

    if status == "skip_short":
        _layer_open("A", "Identity", "verbatim + near-verbatim",
                    "Input has fewer than 12 Arabic letters — too short for a "
                    "meaningful identity check.")
        st.markdown('<span class="pill warn">skipped · under 12 letters</span>',
                    unsafe_allow_html=True)
        _layer_close()
        return

    if status == "exact":
        h = a["hit"]
        rng = f"{h.surah}:{h.ayah_start}" if h.ayah_start == h.ayah_end \
              else f"{h.surah}:{h.ayah_start}–{h.ayah_end}"
        _layer_open("A", "Identity", "verbatim match",
                    f"Your text appears <b>verbatim</b> in the canonical Hafs Quran at "
                    f"<b>{rng}</b> — letter-for-letter across "
                    f"{h.n_letters:,} normalised letters, "
                    f"{h.n_verses} verse{'s' if h.n_verses != 1 else ''}.")
        st.markdown('<span class="pill ok">✓ verbatim in corpus</span>',
                    unsafe_allow_html=True)
        _layer_close()
        return

    if status == "fuzzy":
        h = a["hit"]
        rng = f"{h.surah}:{h.ayah_start}" if h.ayah_start == h.ayah_end \
              else f"{h.surah}:{h.ayah_start}–{h.ayah_end}"
        _layer_open("A", "Identity", "near-verbatim match",
                    f"Your text is <b>not verbatim</b>, but is within a short edit "
                    f"distance of <b>{rng}</b>: <b>{h.edit_distance} letter edit"
                    f"{'s' if h.edit_distance != 1 else ''}</b> "
                    f"({h.deviation_pct:.2f}% deviation).")
        st.markdown(
            f'<div class="kv">edit distance <b>{h.edit_distance}</b> · '
            f'input letters <b>{h.n_letters_input:,}</b> · '
            f'canonical letters <b>{h.n_letters_canonical:,}</b> · '
            f'deviation <b>{h.deviation_pct:.2f}%</b></div>',
            unsafe_allow_html=True,
        )
        with st.expander("Show canonical Hafs text side by side"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Canonical (Hafs)**")
                st.markdown(f'<div class="rtl-text">{h.canonical_raw}</div>',
                            unsafe_allow_html=True)
            with col_b:
                st.markdown("**Your input**")
                st.markdown(f'<div class="rtl-text">{result["input_text"][:1500]}</div>',
                            unsafe_allow_html=True)
        _layer_close()
        return

    # miss
    _layer_open("A", "Identity", "verbatim + near-verbatim",
                "Your text does <b>not</b> appear in the canonical Hafs Quran and is "
                "not within a 10% edit-distance neighbourhood of any Quranic passage. "
                "Identity returns <b>NOT IN CORPUS</b>.")
    st.markdown('<span class="pill err">✗ not in corpus</span>',
                unsafe_allow_html=True)
    _layer_close()


def _axis_status_for(r: dict, a_status: str, deciding_key: str | None) -> tuple:
    """Return (verdict_text, verdict_class) describing where the input sits
    on this axis relative to the Quranic distribution."""
    if not np.isfinite(r["match"]):
        return ("Insufficient data on this axis at the input length.", "gray")
    if r["match"] >= 100.0:
        return ("Inside the inner-80% Quranic band — typical Quranic value.", "green")
    if r["match"] >= 75.0:
        return ("In the outer 10–20% tail of Quranic values — still inside the "
                "Quranic range, but unusual for the Quran.", "amber")
    if r["match"] >= 25.0:
        return ("In the extreme tail of Quranic values, near the edge of the "
                "Quranic distribution.", "amber")
    return ("Outside the Quranic distribution entirely — value never observed "
            "in any Quranic N-verse window.", "red")


def render_layer_b(result: dict):
    b = result["layer_b"]
    a_status = result["layer_a"]["status"]
    script = result.get("script", "ar")

    if b.get("status") == "skip_short":
        _layer_open("B", "Fingerprint", "8 corpus-pooled axes",
                    f"Input has {b.get('n_letters', 0)} normalised letters in "
                    f"{b.get('n_verses', 0)} verse(s). The shortest Quranic surah "
                    f"(Al-Kawthar) is 42 letters in 3 verses — below that, no "
                    f"statistical fingerprint claim can be made.")
        st.markdown('<span class="pill warn">skipped · need ≥ 3 verses, 42 letters</span>',
                    unsafe_allow_html=True)
        _layer_close()
        return

    composite = b["composite"]
    inside_count = b["inside_count"]
    n_axes = b["n_axes"]
    n_verses = b["n_verses"]

    # Determine what this layer can actually claim at this length.
    # The Quran-unique signatures we documented all need either corpus-
    # aggregate scale (F76, F67, F79), long-surah fractal scale (F87:
    # HFD at N≥32, Δα at N≥64), or the Quran reference itself (F55, F69
    # — which is Layer A/C). Everything at short N is class-membership
    # only.
    if n_verses >= 64:
        scope_label = "full fingerprint active"
        scope_note = ("At N ≥ 64 verses, all 8 axes including HFD and Δα are "
                      "available — the F87 multifractal fingerprint "
                      "(Quran-unique at rank 1/7 with LOO-z = 22.59) can "
                      "be tested on your input.")
    elif n_verses >= 32:
        scope_label = "partial fingerprint · Δα disabled"
        scope_note = ("At 32 ≤ N < 64, HFD is available but Δα is not. "
                      "The F87 multifractal uniqueness test is only partial "
                      "at this length; full F87 needs N ≥ 64.")
    elif n_verses >= 15:
        scope_label = "class-membership scale"
        scope_note = ("At 15 ≤ N < 32, both fractal axes (HFD, Δα) are "
                      "mathematically unavailable. The remaining 6 axes "
                      "measure <b>Arabic-rasm rhymed-scripture class "
                      "membership</b>, not Quran-specific identity. Other "
                      "rhymed Arabic texts (classical qasida, some modern "
                      "nasheed) legitimately pass these axes.")
    else:
        scope_label = "sub-discrimination scale"
        scope_note = ("At N < 15, Layer B cannot reliably distinguish Quran "
                      "from any other classical Arabic text. Use Layer A "
                      "(identity) and Layer C (forensics) as the primary "
                      "signals; Layer B is informational only.")

    summary = (
        f"Length-calibrated class-match against Quranic {n_verses}-verse windows: "
        f"<b>{composite:.1f}%</b> across {n_axes} axes. "
        f"<b>{inside_count}/{n_axes}</b> axis value{'s' if inside_count != 1 else ''} "
        f"fall inside the inner 80% of Quranic values at this length. "
        f"<br><br>{scope_note}"
    )
    _layer_open("B", "Class fingerprint",
                f"N = {n_verses} · {scope_label}",
                summary)

    # Separate, prominent honesty note about what passing Layer B means.
    if n_verses < 32:
        st.markdown(
            '<div class="callout note">'
            '<b>What a high Layer B score means at this length.</b> '
            '<b>100%</b> on an axis = your value is inside the observed '
            'Quranic range at this length — your text is <b>consistent '
            'with</b> being Quran on that axis. It does <b>not</b> mean '
            'your text <b>is</b> uniquely the Quran on that axis. The '
            'Quran\'s documented uniqueness signatures (F87 multifractal, '
            'F76 corpus-aggregate H_EL &lt; 1 bit, F67 C_Ω rank-1 across '
            '12 corpora) all require either N ≥ 64 or whole-corpus '
            'aggregation — neither is possible on your input at length '
            f'{n_verses}. Use Layer A for identity and Layer C for '
            'tampering forensics.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Strong caveat for non-Arabic input (Hebrew, Latin, …): we still compute
    # the axes on the raw character stream, but they are not directly
    # comparable to a corpus calibrated on the 28-letter Arabic rasm.
    if script != "ar":
        st.markdown(
            '<div class="callout note" style="border-left-color: var(--red)">'
            f'<b>Cross-script comparison caveat.</b> Your input is not Arabic '
            f'(detected: <b>{script}</b>). The 8 axes are still computed on the '
            f'raw character stream, but they are calibrated on the Quran\'s '
            f'<b>28-letter Arabic rasm distribution</b>. A high match% here does '
            f'<b>not</b> mean the text resembles the Quran — it means the input\'s '
            f'character statistics happen to fall inside the Arabic-rasm envelope. '
            f'Treat the numbers below as illustrative only.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Scale-limit caveat for small inputs that aren't in the corpus.
    if n_verses < 15 and a_status == "miss" and script == "ar":
        st.markdown(
            '<div class="callout note">'
            '<b>Scale-limit caveat.</b> Layer B cannot reliably distinguish Quran '
            'from other classical Arabic text below ~15 verses — small Arabic '
            'passages cluster tightly in this feature space regardless of origin. '
            'The project\'s AUC = 0.998 discrimination was measured on 15–100 '
            'verse surahs vs 2,509 control units of similar size.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Deciding axis callout (only if Layer A missed and a clear weak axis exists).
    dec = b.get("deciding")
    if (a_status == "miss" and dec is not None
            and np.isfinite(dec["match"]) and dec["match"] < 80):
        st.markdown(
            f'<div class="deciding">'
            f'<div class="label">Deciding axis</div>'
            f'<b>{dec["name"]}</b> — typical Quran band '
            f'<span class="kv">[{dec.get("p10", float("nan")):.3f} … '
            f'{dec.get("p90", float("nan")):.3f}]</span>, '
            f'your value <span class="kv"><b>{dec["you"]:.4f}</b></span>. '
            f'This axis carries the largest gap and is the strongest structural '
            f'reason your text differs from the Quran.'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Axis table — header
    st.markdown('<div class="axis-table">', unsafe_allow_html=True)
    st.markdown(
        '<div class="axis-row head">'
        '<div>Axis</div>'
        '<div>Quran typical band (p10–p90)</div>'
        '<div>You</div>'
        '<div>Match</div>'
        '<div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    rows_sorted = sorted(
        b["rows"],
        key=lambda r: (r["match"] if np.isfinite(r["match"]) else 999.0),
    )
    deciding_key = dec["key"] if dec is not None else None
    for r in rows_sorted:
        bucket = _bucket(r["match"])
        is_deciding = (a_status == "miss" and dec is not None
                       and r["key"] == dec["key"] and np.isfinite(r["match"])
                       and r["match"] < 80)
        if not np.isfinite(r["match"]):
            you_disp, match_disp, range_disp, bar_w = "—", "n/a", "—", 0
        else:
            you_disp = f"{r['you']:.4f}"
            match_disp = f"{r['match']:.0f}%"
            bar_w = max(2, int(round(r["match"])))
            if np.isfinite(r.get("p10", float("nan"))):
                range_disp = f"[{r['p10']:.3f} … {r['p90']:.3f}]"
            else:
                range_disp = f"{r['ref']:.4f}"

        # Row + per-axis expander details.
        st.markdown(
            f'<div class="axis-row{" deciding" if is_deciding else ""}">'
            f'<div class="axis-name">{r["name"]} <span class="symbol">{r["sym"]}</span></div>'
            f'<div class="axis-num range">{range_disp}</div>'
            f'<div class="axis-num">{you_disp}</div>'
            f'<div><div class="bar-track"><div class="bar-fill {bucket}" '
            f'style="width:{bar_w}%"></div></div></div>'
            f'<div class="match-pct {bucket}">{match_disp}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Per-axis details expander
        with st.expander(
            f"  ↳ Details — what {r['sym']} measures, the Quran band, and where you sit",
            expanded=False,
        ):
            wiki = C.PROVENANCE[r["key"]]["wikipedia"]
            fid = C.PROVENANCE[r["key"]]["f_id"]
            verdict_text, _ = _axis_status_for(r, a_status, deciding_key)

            # Special handling for HFD / Δα when N is too small.
            if not np.isfinite(r["match"]):
                if r["key"] == "HFD":
                    explanation = ("Higuchi fractal dimension requires a series of "
                                   "≥ 32 numbers (your input has fewer verses). "
                                   "This axis cannot be computed at this length — "
                                   "this is a mathematical requirement, not a missing "
                                   "feature.")
                elif r["key"] == "Delta_alpha":
                    explanation = ("Multifractal spectrum width (MFDFA) requires "
                                   "a series of ≥ 64 numbers for stable percentile "
                                   "estimation. This axis cannot be computed at this "
                                   "length — paste a longer surah (e.g. Al-Baqarah, "
                                   "286 verses) to enable it.")
                else:
                    explanation = "Could not compute this axis on the input."
                st.markdown(
                    f'<div class="axis-detail">'
                    f'<div class="label">Why n/a</div>'
                    f'{explanation}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="axis-detail">'
                    f'<div class="label">What this measures</div>'
                    f'{r["explainer"]}'
                    f'<div class="ranges">'
                    f'<div class="range-card">'
                    f'<div class="lbl">Typical Quran (inner 80% · p10–p90)</div>'
                    f'<div class="val">[{r["p10"]:.4f} … {r["p90"]:.4f}]</div>'
                    f'</div>'
                    f'<div class="range-card">'
                    f'<div class="lbl">Extreme Quran range (full p0–p100)</div>'
                    f'<div class="val">[{r["q_lo"]:.4f} … {r["q_hi"]:.4f}]</div>'
                    f'</div>'
                    f'</div>'
                    f'<div class="ranges">'
                    f'<div class="range-card">'
                    f'<div class="lbl">Your value</div>'
                    f'<div class="val">{r["you"]:.4f}</div>'
                    f'</div>'
                    f'<div class="range-card">'
                    f'<div class="lbl">Quran median</div>'
                    f'<div class="val">{r["q_median"]:.4f}</div>'
                    f'</div>'
                    f'</div>'
                    f'<div style="margin-top:0.6rem"><b>Verdict:</b> {verdict_text}</div>'
                    f'<div style="margin-top:0.4rem" class="kv">'
                    f'Empirical CDF: <b>{(r["percentile"]*100):.1f}%</b> · '
                    f'Whole-Quran reference: <b>{BOOT["ref"][r["key"]]:.4f}</b> · '
                    f'{r["n_windows"]:,} N-verse windows · '
                    f'F-id <b>{fid}</b> · '
                    f'<a href="{wiki}" target="_blank">Wikipedia ↗</a>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown('</div>', unsafe_allow_html=True)

    # Calibration legend — match the current scoring in calibration.py.
    st.markdown(
        '<div class="fine-print" style="margin-top:0.7rem">'
        '<b>How match% is calibrated.</b> For each axis, every N-verse '
        'Quranic window is computed (~5,000 windows) and your value is '
        'placed against this empirical distribution. '
        '<b>100%</b> = value is inside <code>[vmin, vmax]</code>, the full '
        'observed Quranic range at this length — your text is '
        '<b>consistent with</b> being Quran on that axis. '
        '<b>&lt;100%</b> = value falls outside the observed range; score '
        'decays linearly in units of the Quranic range-width, reaching 0 '
        'at one full range-width beyond the extreme. '
        'The per-axis <i>details</i> also show whether the value lands '
        'in the <b>inner-80% typical band</b> (p10–p90) — a secondary '
        'typicality indicator orthogonal to the primary identity score.'
        '</div>',
        unsafe_allow_html=True,
    )

    _layer_close()


def render_layer_c(result: dict):
    c = result["layer_c"]
    a_status = result["layer_a"]["status"]

    if c.get("status") == "skip_far":
        _layer_open("C", "Tampering forensics",
                    "F55 bigram-shift · F70 gzip-NCD",
                    "These forensics only fire when Layer A identifies a verbatim or "
                    "near-verbatim Quranic passage, because they measure <b>what was "
                    "edited relative to the canonical text</b>. Your input is not in "
                    "that neighbourhood, so Layer C is not applicable.")
        st.markdown('<span class="pill">skipped · not near-canonical</span>',
                    unsafe_allow_html=True)
        _layer_close()
        return

    bd = c["bigram_d"]
    ncd = c["ncd"]
    edit_min = c["edit_min"]

    _layer_open("C", "Tampering forensics",
                "F55 bigram-shift · F70 gzip-NCD",
                "Your text sits near the canonical Quran. These two tests say <b>what "
                "kind of edit</b> happened (letter substitution vs. sequence reordering).")

    # C1
    if a_status == "exact":
        c1_msg = "Δ<sub>bigram</sub> = 0 · no letter substitutions detected."
        c1_pill = "ok"
        c1_pill_text = "✓ no letter edits"
    elif bd <= 0.001:
        c1_msg = ("Δ<sub>bigram</sub> = 0 · letters preserved exactly. The difference "
                  "must therefore be a verse or word <b>reordering</b> — check the "
                  "gzip-NCD test below.")
        c1_pill = "warn"
        c1_pill_text = "sequence-only edit"
    else:
        c1_msg = (f"Δ<sub>bigram</sub> = <b>{bd:.1f}</b>. By the F69 theorem, each "
                  f"letter substitution moves Δ by 1–2, so this corresponds to at "
                  f"least <b>{edit_min}</b> letter edit{'s' if edit_min != 1 else ''}.")
        c1_pill = "warn" if bd <= 4 else "err"
        c1_pill_text = f"≥ {edit_min} letter edit{'s' if edit_min != 1 else ''}"

    st.markdown(
        f'<div class="kv"><b>C1 · F55 bigram-shift</b></div>'
        f'<div class="layer-summary">{c1_msg}</div>'
        f'<span class="pill {c1_pill}">{c1_pill_text}</span>'
        f'<div class="kv" style="margin-top:0.5rem">'
        f'Δ<sub>bigram</sub> <b>{bd:.2f}</b> · min edits <b>{edit_min}</b> · '
        f'<a href="{C.TAMPERING_REFS["F55_bigram_shift"]["wikipedia"]}" target="_blank">about bigrams ↗</a>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr style="margin:0.9rem 0">', unsafe_allow_html=True)

    # C2
    if not np.isfinite(ncd):
        c2_msg = "Could not compute gzip-NCD on this input."
        c2_pill, c2_pill_text = "gray", "n/a"
    elif ncd < 0.05:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Below the noise floor — "
                  f"sequence-level structure matches the canonical text.")
        c2_pill, c2_pill_text = "ok", "✓ sequence preserved"
    elif ncd < 0.20:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Mild disturbance — consistent with "
                  f"a few-letter edit or a single verse reorder.")
        c2_pill, c2_pill_text = "warn", "mild disturbance"
    else:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Substantial disturbance — consistent "
                  f"with multiple verse swaps or word reordering that the bigram "
                  f"test alone cannot see.")
        c2_pill, c2_pill_text = "err", "strong reordering"

    st.markdown(
        f'<div class="kv"><b>C2 · F70 gzip-NCD</b></div>'
        f'<div class="layer-summary">{c2_msg}</div>'
        f'<span class="pill {c2_pill}">{c2_pill_text}</span>'
        f'<div class="kv" style="margin-top:0.5rem">'
        f'F70 receipt: 88.4% recall on 2-verse swaps; 93.0% combined · '
        f'<a href="{C.TAMPERING_REFS["gzip_NCD"]["wikipedia"]}" target="_blank">about NCD ↗</a>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _layer_close()


# =============================================================================
# Sidebar — examples, data, honest scope
# =============================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">Pristine</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Quran fingerprint detector</div>',
                    unsafe_allow_html=True)

        st.markdown(
            f'<div class="fine-print">'
            f'<b>{BOOT["n_chapters"]}</b> chapters · '
            f'<b>{BOOT["n_verses"]:,}</b> verses · '
            f'<b>{BOOT["n_letters"]:,}</b> letters, SHA-verified.'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("## Examples")
        if "active_preset_id" not in st.session_state:
            st.session_state["active_preset_id"] = None
        for preset in examples.PRESETS:
            if st.button(preset["label"],
                         key=f"preset_{preset['id']}",
                         use_container_width=True):
                st.session_state["active_preset_id"] = preset["id"]
                st.session_state["input_text"] = preset["text"]
                st.session_state["pending_analysis"] = True
                # Clear old result to force re-run after preset change.
                st.session_state.pop("result", None)

        st.markdown("## How it works")
        with st.expander("What the math CAN and CANNOT do"):
            st.markdown(
                "**Can do — with 100% mathematical certainty:**\n"
                "- Detect verbatim text (any length ≥ 12 letters): deterministic substring search.\n"
                "- Measure edit distance exactly for near-Quranic text (Levenshtein).\n"
                "- Detect single-letter edits via the F69 theorem (Δ<sub>bigram</sub> ∈ [1,2] per edit — provably guaranteed).\n"
                "- Detect verse/word reordering via gzip-NCD (88–93% recall per locked receipt).\n"
                "\n"
                "**Cannot do — mathematical limits:**\n"
                "- Identify Quranic origin without access to the canonical text. To say "
                "'this is Quran', you must compare against a reference. We use the "
                "SHA-256-locked Hafs corpus — no training, no weights.\n"
                "- Discriminate Quran from classical Arabic at under ~15 verses. "
                "Small Arabic samples cluster tightly regardless of origin.\n"
                "- Judge authenticity of unknown verses ab initio. Semantic/theological "
                "correctness is outside the QSF scope.\n"
            )

        with st.expander("The canonical corpus"):
            st.markdown(
                f'<div class="kv">'
                f'file: <b>data/corpora/ar/quran_bare.txt</b><br>'
                f'sha256: <b>{BOOT["integrity"].sha256_actual[:16]}…</b><br>'
                f'size: <b>{BOOT["integrity"].n_bytes:,}</b> bytes<br>'
                f'verses: <b>{BOOT["n_verses"]:,}</b>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="fine-print" style="margin-top:0.5rem">'
                        'Quran reference values (computed at startup):'
                        '</div>', unsafe_allow_html=True)
            for key, _name, sym, _exp in _AXIS_DEFS:
                v = BOOT["ref"].get(key, float("nan"))
                fid = C.PROVENANCE[key]["f_id"]
                st.markdown(
                    f'<div class="kv"><b>{sym}</b> = {v:.4f} &nbsp;'
                    f'<span class="muted">{fid}</span></div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Scope — what this tool does NOT do"):
            st.markdown(
                "- Does **not** decide canonicity or select between readings "
                "(Hafs, Warsh, Qalun, …).\n"
                "- Does **not** make theological or metaphysical claims.\n"
                "- Does **not** authenticate manuscripts.\n"
                "- Does **not** detect semantic or meaning errors.\n"
                "- Does **not** use any machine-learned weights or neural networks.\n"
                "- Ignores diacritics by design — canonical readings legitimately differ in diacritics.\n"
            )

        with st.expander("Why no per-surah subsets"):
            st.markdown(
                "Claims like *'47 of 109 surahs satisfy X'* are **sharpshooter logic**: "
                "if 62 surahs don't satisfy X, then X isn't a property of the Quran — "
                "it's a property of a hand-picked subset.\n\n"
                "Pristine compares your text against the **whole-Quran corpus-pooled** "
                "value of every axis (one number, computed on all 6,236 verses "
                "concatenated). The Quran is treated as a single object. "
                "No subset is ever selected to make a stronger claim."
            )

        with st.expander("Receipts & audit"):
            st.markdown(
                "- F55 · F69 bigram-shift theorem · `exp95i` · `exp118`\n"
                "- F70 gzip-NCD · `exp117_verse_reorder_detector` · "
                "88.4% form-3 / 93.0% combined\n"
                "- F75 universal invariant · `exp130`\n"
                "- F67 C_Ω · `exp115`\n"
                "- F82 IFS fractal · `exp182`\n"
                "- F87 HFD + Δα · `exp177`\n"
                "- Sharpshooter pre-registration · `exp143`\n"
                "- Ring of locked constants · `exp183`\n\n"
                "Run `python app/pristine_audit.py` for a 9-check reproducibility "
                "audit against these receipts."
            )


# =============================================================================
# Main
# =============================================================================
def main():
    render_sidebar()

    st.markdown(
        '<div class="eyebrow">◈ Pristine · v1</div>',
        unsafe_allow_html=True,
    )
    st.markdown("# The Quran fingerprint detector.")
    st.markdown(
        '<div class="tagline">Paste any text. Pristine reports whether it appears '
        'in the canonical Hafs Quran, how closely its eight-axis mathematical '
        'fingerprint overlaps the whole Quran, and — when applicable — exactly '
        'what kind of edit was made.</div>',
        unsafe_allow_html=True,
    )

    # --- Initialise session state -------------------------------------------
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "result" not in st.session_state:
        st.session_state["result"] = None
    if "pending_analysis" not in st.session_state:
        st.session_state["pending_analysis"] = False

    # --- Input column + run trigger -----------------------------------------
    col_input, col_results = st.columns([1, 1.25], gap="large")

    with col_input:
        st.markdown("## Your text")

        txt = st.text_area(
            label="input",
            height=340,
            label_visibility="collapsed",
            placeholder="Paste Arabic text here, or click an example in the sidebar →",
            key="input_text",
        )

        # Input stats
        n_chars = len(txt) if txt else 0
        skel_n = len(normalize_arabic_letters_only(txt)) if txt else 0
        n_verses = len(split_into_verses(txt)) if txt else 0
        script = detect_script(txt) if txt else "—"

        st.markdown(
            f'<div class="stat-grid">'
            f'<div class="stat-card"><div class="lbl">Characters</div>'
            f'<div class="val">{n_chars:,}</div></div>'
            f'<div class="stat-card"><div class="lbl">Arabic letters</div>'
            f'<div class="val">{skel_n:,}</div></div>'
            f'<div class="stat-card"><div class="lbl">Verses</div>'
            f'<div class="val">{n_verses}</div></div>'
            f'<div class="stat-card"><div class="lbl">Script</div>'
            f'<div class="val">{script}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # The Run / Clear buttons
        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            run_clicked = st.button(
                "Analyse  →",
                use_container_width=True,
                type="primary",
                disabled=not (txt and txt.strip()),
            )
        with btn_col2:
            clear_clicked = st.button("Clear",
                                      use_container_width=True)

        # Status hint
        has_result = st.session_state["result"] is not None
        current_hash = _hash_input(txt) if txt else ""
        stale = has_result and st.session_state["result"].get("hash") != current_hash

        if clear_clicked:
            st.session_state["input_text"] = ""
            st.session_state["result"] = None
            st.rerun()

        if run_clicked or st.session_state.get("pending_analysis"):
            st.session_state["pending_analysis"] = False
            if txt and txt.strip():
                prog_slot = st.empty()
                t_start = time.time()
                bar = prog_slot.progress(0, text="0% · starting…")

                def progress(frac, msg):
                    f = max(0.0, min(1.0, float(frac)))
                    elapsed_so_far = time.time() - t_start
                    if f > 0.05:
                        eta = elapsed_so_far / f * (1.0 - f)
                        eta_str = f"{eta:.0f}s left"
                    else:
                        eta_str = "estimating…"
                    bar.progress(
                        f,
                        text=f"{int(f*100)}% · {msg} · {elapsed_so_far:.1f}s elapsed · {eta_str}",
                    )

                try:
                    result = analyse(txt, progress=progress)
                except Exception as e:  # noqa: BLE001
                    prog_slot.empty()
                    st.error(f"Analysis failed: {e}")
                    return
                elapsed = time.time() - t_start
                bar.progress(1.0, text=f"100% · complete · {elapsed:.1f}s total")
                time.sleep(0.25)
                prog_slot.empty()
                result["elapsed"] = elapsed
                st.session_state["result"] = result
                st.rerun()

        if stale:
            st.markdown(
                '<div class="callout note" style="margin-top:0.7rem">'
                '<b>Input changed.</b> Click <b>Analyse</b> to re-run on the current text.'
                '</div>',
                unsafe_allow_html=True,
            )

    with col_results:
        st.markdown("## Result")

        result = st.session_state.get("result")
        if result is None:
            st.markdown(
                '<div class="verdict neut">'
                '<div class="sigil">·</div>'
                '<div><div class="title">Awaiting input</div>'
                '<div class="subtitle">Paste text on the left, or pick an example '
                'from the sidebar. Then click <b>Analyse</b>.</div></div></div>',
                unsafe_allow_html=True,
            )
            return

        render_verdict(result)

        st.markdown(
            f'<div class="fine-print" style="margin:-0.8rem 0 0.7rem 0">'
            f'Analysis completed in <b>{result.get("elapsed", 0):.2f}s</b>. '
            f'Input SHA-16: <code>{result["hash"]}</code>.</div>',
            unsafe_allow_html=True,
        )

        # Inline explainer: separate corpus-free universal laws from
        # corpus-dependent identity claims. This is the philosophical heart
        # of the project — we discovered constants from the Quran that, once
        # published, anyone can test any text against without ever loading
        # the Quran again.
        with st.expander(
            "What does the math know on its own? — universal laws vs Quran lookup",
            expanded=False,
        ):
            ref = BOOT["ref"]
            st.markdown(
                "**Two completely different questions are being mixed when "
                "people ask 'do you really need the Quran corpus?':**\n\n"
                "### Question A — *Is this exact text the Quran?*\n"
                "**Yes, this requires the Quran.** No amount of pure math can "
                "tell you whether a given paragraph is verbatim Quran without "
                "comparing it to the Quran. We hold the corpus as a "
                "SHA-256-locked text file (viewable in the sidebar) — it's a "
                "published reference, not a trained model. That's Layer A and "
                "the bigram/gzip parts of Layer C.\n\n"
                "### Question B — *Does this text obey the universal laws we discovered?*\n"
                "**No — this needs only the text itself.** The whole point of "
                "the project is that the Quran exposed a small set of "
                "constants that, once measured and published, are *properties "
                "of the Arabic-rasm scripture class*, not properties of any "
                "specific corpus. You can test any text against these "
                "constants without ever opening the Quran again.\n\n"
                "Here are the constants this app measures and what they "
                "*mean independently of the Quran*:\n\n"
                "| Symbol | Universal claim (corpus-free) | Quran-measured value |\n"
                "|---|---|---|\n"
                f"| **F75** | Universal Shannon-entropy invariant for "
                f"Arabic-rasm scripture (Source-Code Constant). Any "
                f"Arabic-rasm scripture should land in **[4.81, 5.92]**, "
                f"target ≈ **5.75 ± 5%**. Falls outside ⇒ text is not in "
                f"the scripture class. | `{ref['F75']:.4f}` |\n"
                f"| **p_max** | Rhyme concentration of verse-final letters. "
                f"`p_max ≥ 0.4` ⇒ deliberately rhymed text. `p_max ≈ 1/28` "
                f"⇒ unrhymed prose. Measured intrinsically per text. | `{ref['p_max']:.4f}` |\n"
                f"| **H_EL** | Verse-final letter entropy. Low = rhymed, "
                f"high = no rhyme spine. Tied to `p_max` by Shannon's "
                f"inequality. | `{ref['H_EL']:.4f}` |\n"
                f"| **C_Ω** | Channel-utilisation: how much of the 28-letter "
                f"alphabet the text actually uses, weighted by frequency. "
                f"Arabic-rasm scripture sits in **[0.43, 1.00]**; Quran ≈ "
                f"**1.0** = full channel. | `{ref['C_Omega']:.4f}` |\n"
                f"| **D_max** | Bigram redundancy gap (max-entropy minus "
                f"observed). Higher = more predictable / more compressible. | `{ref['D_max']:.4f}` |\n"
                f"| **d_info** | IFS information dimension of letter "
                f"distribution. Arabic-rasm scripture clusters around "
                f"**1.55–1.66**. | `{ref['d_info']:.4f}` |\n"
                f"| **HFD / Δα** | Higuchi & multifractal-spectrum width "
                f"of verse-length series. Captures rhythmic structure that "
                f"plain entropy misses. (Need long surahs.) | depends on N |\n\n"
                "**These are the dimensions you discovered.** You can compute "
                "every one of them on a brand-new text without ever opening "
                "the Quran. If F75 lands at 8.3, the text is *demonstrably* "
                "outside the Arabic-rasm scripture class — no comparison to "
                "the Quran was performed. If d_info lands at 1.42 with "
                "p_max = 0.05, you have unrhymed text with statistically "
                "non-scripture letter distribution — again, no Quran lookup "
                "occurred.\n\n"
                "### What the Quran corpus *adds on top* (Layer B match%)\n\n"
                "The numbers in the table above tell you whether a text **is "
                "in the Arabic-rasm scripture class at all**. The Quran "
                "corpus then sharpens that to **where in the class** — at "
                "which percentile of *the Quran's specific distribution at "
                "your input length* your value sits. That extra precision "
                "*does* require comparing N-verse windows against N-verse "
                "windows, which requires the Quran.\n\n"
                "### The honest map\n\n"
                "| Question you might ask | Needs corpus? | How |\n"
                "|---|---|---|\n"
                "| Is this *the* Quran? | yes | substring + Levenshtein |\n"
                "| Was a Quranic passage tampered with? | yes | F55 bigram-shift, F70 gzip-NCD |\n"
                "| Is this in the Arabic-rasm scripture class? | **no** | F75 ∈ [4.81, 5.92] alone |\n"
                "| Is this rhymed text? | **no** | p_max ≥ 0.4 alone |\n"
                "| What's the rhythmic complexity? | **no** | HFD / Δα alone |\n"
                "| Is this even Arabic? | **no** | Unicode script lookup |\n"
                "| What percentile of Quran-N-verse windows does this hit? | yes | calibrated match% |\n"
                "| Who wrote this? | n/a | out of scope; no tool can do this |\n"
            )

        st.markdown("## Layered evaluation")
        render_layer_a(result)
        render_layer_b(result)
        render_layer_c(result)


if __name__ == "__main__":
    main()
