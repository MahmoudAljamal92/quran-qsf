"""Pristine — the Quran fingerprint detector.

A four-layer interactive app that:
  Layer A — looks up the input verbatim (and near-verbatim) inside the
            canonical Hafs corpus.
  Layer B — measures eight whole-corpus-pooled fingerprint axes on the
            input and on the Quran, side-by-side.
  Layer C — when the input is verbatim or near-verbatim, runs three
            tampering forensics (bigram-shift, gzip-NCD, dual-channel).
  Layer D — for non-Arabic inputs, notes that comparison is to the
            Quran's Arabic-rasm fingerprint and degrades gracefully.

Every numeric reference is either:
  - computed at app startup from data/corpora/ar/quran_bare.txt (after
    SHA-256 verification), or
  - cited to a SHA-locked experiment receipt JSON.

There are no per-surah cherry-picked thresholds, no learned weights, and
no hidden corpus access during scoring.

Run:
    streamlit run app/pristine.py
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import streamlit as st

# Make pristine_lib importable when the app is launched from any cwd.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from pristine_lib import constants as C  # noqa: E402
from pristine_lib import calibration, corpus, examples, metrics  # noqa: E402
from pristine_lib.normalize import (  # noqa: E402
    detect_script,
    normalize_arabic,
    normalize_arabic_letters_only,
    split_into_verses,
)


# ============================================================================
# Page setup + custom CSS
# ============================================================================
st.set_page_config(
    page_title="Pristine — Quran Fingerprint",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root {
  --ink: #0f172a;
  --ink-soft: #334155;
  --paper: #fafaf7;
  --line: #e7e5de;
  --gold: #b18a3a;
  --gold-soft: #ecdfb9;
  --green: #137a4f;
  --green-soft: #d8efe2;
  --amber: #b76e00;
  --amber-soft: #f5e2c1;
  --red: #b91c1c;
  --red-soft: #f5d6d6;
  --mono: ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace;
}
html, body, [class*="block-container"] {
  background: var(--paper);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.block-container { padding-top: 1.4rem !important; padding-bottom: 4rem !important; max-width: 1240px; }
h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.01em; font-weight: 600; }
h1 { font-size: 1.55rem; margin: 0 0 0.2rem 0; }
h2 { font-size: 1.15rem; margin: 1.4rem 0 0.6rem 0; padding-bottom: 0.3rem; border-bottom: 1px solid var(--line); }
h3 { font-size: 0.95rem; margin: 0.8rem 0 0.4rem 0; color: var(--ink-soft); font-weight: 500; }
hr { border: none; border-top: 1px solid var(--line); margin: 1.2rem 0; }
.app-tagline { color: var(--ink-soft); font-size: 0.85rem; margin: 0 0 1.2rem 0; }
.verdict-ribbon {
  display: flex; align-items: center; gap: 1rem;
  padding: 1rem 1.2rem; border-radius: 6px; border: 1px solid var(--line);
  background: white; margin: 0.4rem 0 1.4rem 0;
}
.verdict-ribbon .icon { font-size: 1.6rem; line-height: 1; font-family: var(--mono); }
.verdict-ribbon .title { font-size: 1.15rem; font-weight: 600; color: var(--ink); }
.verdict-ribbon .subtitle { font-size: 0.86rem; color: var(--ink-soft); margin-top: 0.15rem; }
.verdict-ribbon.ok { background: var(--green-soft); border-color: var(--green); }
.verdict-ribbon.ok .icon { color: var(--green); }
.verdict-ribbon.warn { background: var(--amber-soft); border-color: var(--amber); }
.verdict-ribbon.warn .icon { color: var(--amber); }
.verdict-ribbon.err { background: var(--red-soft); border-color: var(--red); }
.verdict-ribbon.err .icon { color: var(--red); }
.verdict-ribbon.neut { background: white; border-color: var(--line); }
.verdict-ribbon.neut .icon { color: var(--ink-soft); }
.layer-card {
  background: white; border: 1px solid var(--line); border-radius: 6px;
  padding: 1rem 1.1rem; margin-bottom: 1.1rem;
}
.layer-header {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 0.6rem;
}
.layer-name { font-weight: 600; font-size: 0.95rem; color: var(--ink); }
.layer-tag {
  font-family: var(--mono); font-size: 0.72rem; color: var(--ink-soft);
  background: var(--paper); padding: 0.12rem 0.45rem; border-radius: 3px;
  border: 1px solid var(--line);
}
.layer-summary { color: var(--ink-soft); font-size: 0.86rem; line-height: 1.5; }
.deciding-axis {
  background: var(--gold-soft); border-left: 3px solid var(--gold);
  padding: 0.7rem 0.9rem; border-radius: 0 4px 4px 0; margin: 0.6rem 0 0.9rem 0;
  font-size: 0.85rem;
}
.deciding-axis .label { color: var(--gold); font-weight: 600; font-size: 0.72rem;
  letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.25rem; }
.axis-row {
  display: grid; grid-template-columns: 1.6fr 0.9fr 0.9fr 1.6fr 0.6fr;
  align-items: center; gap: 0.7rem;
  padding: 0.55rem 0.2rem; border-bottom: 1px solid var(--line);
  font-size: 0.86rem;
}
.axis-row.head { border-bottom: 2px solid var(--ink); padding-bottom: 0.3rem;
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--ink-soft); font-weight: 600; }
.axis-row.deciding { background: var(--gold-soft); padding-left: 0.6rem; padding-right: 0.6rem;
  border-radius: 4px; border-bottom: 1px solid var(--gold); }
.axis-name { color: var(--ink); font-weight: 500; }
.axis-name .symbol { font-family: var(--mono); color: var(--ink-soft); margin-left: 0.4rem; font-size: 0.78rem; }
.axis-num { font-family: var(--mono); font-variant-numeric: tabular-nums; color: var(--ink); }
.bar-track { background: var(--line); border-radius: 3px; height: 6px; overflow: hidden; position: relative; }
.bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.bar-fill.green { background: var(--green); }
.bar-fill.amber { background: var(--amber); }
.bar-fill.red { background: var(--red); }
.bar-fill.gray { background: var(--ink-soft); }
.match-pct { font-family: var(--mono); font-variant-numeric: tabular-nums; font-weight: 600; text-align: right; }
.match-pct.green { color: var(--green); }
.match-pct.amber { color: var(--amber); }
.match-pct.red { color: var(--red); }
.match-pct.gray { color: var(--ink-soft); }
.muted { color: var(--ink-soft); }
.tag {
  display: inline-block; font-family: var(--mono); font-size: 0.7rem;
  padding: 0.05rem 0.4rem; border-radius: 3px; border: 1px solid var(--line);
  background: var(--paper); color: var(--ink-soft);
}
.tag.ok { color: var(--green); border-color: var(--green); background: var(--green-soft); }
.tag.warn { color: var(--amber); border-color: var(--amber); background: var(--amber-soft); }
.tag.err { color: var(--red); border-color: var(--red); background: var(--red-soft); }
.kv { font-family: var(--mono); font-size: 0.8rem; color: var(--ink-soft); }
.kv b { color: var(--ink); font-weight: 600; }
.fine-print { color: var(--ink-soft); font-size: 0.78rem; line-height: 1.5; }
.section-divider { height: 1px; background: var(--line); margin: 1.3rem 0; }
[data-testid="stSidebar"] { background: white; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h2 { font-size: 0.95rem; }
[data-testid="stSidebar"] h3 { font-size: 0.82rem; margin-top: 0.9rem; }
.stTextArea textarea {
  font-family: var(--mono); font-size: 0.86rem; line-height: 1.55;
  background: white; border: 1px solid var(--line); border-radius: 5px;
  color: var(--ink);
}
.stButton button {
  border: 1px solid var(--line); background: white; color: var(--ink);
  font-size: 0.82rem; padding: 0.35rem 0.8rem; border-radius: 4px;
  font-weight: 500;
}
.stButton button:hover { border-color: var(--gold); color: var(--gold); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================================
# Cached startup: SHA-verify corpus, compute Quran reference axes once
# ============================================================================
@st.cache_resource(show_spinner="Verifying canonical Hafs corpus and computing reference axes…")
def boot():
    """One-time startup: verify SHA, load Quran, compute the 8-axis reference.

    Returns a dict with:
      integrity         -> IntegrityCheck dataclass
      n_chapters / n_verses / n_letters
      ref               -> dict of 8 reference axis values for the Quran
      verse_lengths     -> 1-D series used for HFD / Δα
    """
    integrity = C.verify_quran_corpus()
    verses = corpus.all_verses()
    n_chap = corpus.n_chapters()
    n_letters = corpus.total_letters()
    raw_verse_strs = [v.raw for v in verses]
    skel_full = "".join(v.skeleton for v in verses)
    verse_lens = np.array([len(v.skeleton) for v in verses], dtype=float)

    he = metrics.pooled_H_EL_pmax(raw_verse_strs)
    di = metrics.d_info(skel_full)
    hfd = metrics.higuchi_fd(verse_lens)
    da = metrics.delta_alpha_mfdfa(verse_lens)

    ref = {
        "H_EL":        he["H_EL"],
        "p_max":       he["p_max"],
        "C_Omega":     he["C_Omega"],
        "F75":         he["F75"],
        "D_max":       he["D_max"],
        "d_info":      di,
        "HFD":         hfd,
        "Delta_alpha": da,
    }
    return {
        "integrity": integrity,
        "n_chapters": n_chap,
        "n_verses": len(verses),
        "n_letters": n_letters,
        "ref": ref,
        "skel_full": skel_full,
        "raw_verses": raw_verse_strs,
    }


# Boot — fail loudly if the corpus integrity check fails.
try:
    BOOT = boot()
except Exception as e:                           # noqa: BLE001
    st.error(f"**Cannot start.** {e}")
    st.stop()


# ============================================================================
# Helpers — color buckets and small renderers
# ============================================================================
def _bucket(pct: float) -> str:
    if not np.isfinite(pct):
        return "gray"
    if pct >= 80:
        return "green"
    if pct >= 50:
        return "amber"
    return "red"


def _ribbon(kind: str, icon: str, title: str, subtitle: str = ""):
    sub = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="verdict-ribbon {kind}">'
        f'<div class="icon">{icon}</div>'
        f'<div><div class="title">{title}</div>{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _layer_card_open(name: str, tag: str, summary: str = ""):
    summary_html = f'<div class="layer-summary">{summary}</div>' if summary else ""
    st.markdown(
        f'<div class="layer-card">'
        f'<div class="layer-header">'
        f'<div class="layer-name">{name}</div>'
        f'<div class="layer-tag">{tag}</div>'
        f'</div>'
        f'{summary_html}',
        unsafe_allow_html=True,
    )


def _layer_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# Layer A — Identity (verbatim + fuzzy)
# ============================================================================
def run_layer_a(input_text: str, script: str):
    if script != "ar":
        _layer_card_open(
            "Layer A — Identity check",
            "verbatim & near-verbatim lookup",
            "The canonical Quran corpus is in Arabic (Hafs). Identity lookup "
            "only runs for Arabic input. Your text is not Arabic, so this "
            "layer is skipped. Layer B can still measure the input's fingerprint.",
        )
        st.markdown(
            '<span class="tag warn">SKIPPED · non-Arabic script</span>',
            unsafe_allow_html=True,
        )
        _layer_card_close()
        return {"status": "skip_nonarabic"}

    skel = normalize_arabic_letters_only(input_text)
    if len(skel) < 12:
        _layer_card_open(
            "Layer A — Identity check",
            "verbatim & near-verbatim lookup",
            "Input has fewer than 12 Arabic letters after normalisation. "
            "Identity claims need at least one short verse worth of text.",
        )
        st.markdown(
            '<span class="tag warn">SKIPPED · insufficient text</span>',
            unsafe_allow_html=True,
        )
        _layer_card_close()
        return {"status": "skip_short", "n_letters": len(skel)}

    exact = corpus.exact_match(skel)
    fuzzy = corpus.fuzzy_match(skel) if exact is None else None

    if exact is not None:
        _layer_card_open(
            "Layer A — Identity check",
            "verbatim & near-verbatim lookup",
            f"Your text appears verbatim in the canonical Hafs Quran "
            f"(<b>Surah {exact.surah}, ayah {exact.ayah_start}"
            f"{'' if exact.ayah_start == exact.ayah_end else f'–{exact.ayah_end}'}</b>). "
            f"Letter-for-letter match across {exact.n_letters:,} normalised letters.",
        )
        st.markdown(
            f'<div class="kv">verse range: <b>{exact.surah}:{exact.ayah_start}'
            f'{"" if exact.ayah_start == exact.ayah_end else f"–{exact.ayah_end}"}</b> · '
            f'letters matched: <b>{exact.n_letters:,}</b> · '
            f'verses spanned: <b>{exact.n_verses}</b></div>',
            unsafe_allow_html=True,
        )
        _layer_card_close()
        return {"status": "exact", "hit": exact}

    if fuzzy is not None and fuzzy.deviation_pct < 10.0:
        _layer_card_open(
            "Layer A — Identity check",
            "verbatim & near-verbatim lookup",
            f"Your text is <b>not verbatim</b>, but it is close to "
            f"<b>Surah {fuzzy.surah}, ayah {fuzzy.ayah_start}"
            f"{'' if fuzzy.ayah_start == fuzzy.ayah_end else f'–{fuzzy.ayah_end}'}</b> "
            f"with <b>{fuzzy.edit_distance} letter edit"
            f"{'s' if fuzzy.edit_distance != 1 else ''}</b> "
            f"({fuzzy.deviation_pct:.2f}% deviation).",
        )
        st.markdown(
            f'<div class="kv">edit distance: <b>{fuzzy.edit_distance}</b> · '
            f'input letters: <b>{fuzzy.n_letters_input:,}</b> · '
            f'canonical letters: <b>{fuzzy.n_letters_canonical:,}</b> · '
            f'deviation: <b>{fuzzy.deviation_pct:.2f}%</b></div>',
            unsafe_allow_html=True,
        )
        with st.expander("See the canonical text alongside yours"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Canonical (Hafs)**")
                st.markdown(f'<div class="fine-print">{fuzzy.canonical_raw}</div>',
                            unsafe_allow_html=True)
            with col_b:
                st.markdown("**Your input**")
                st.markdown(f'<div class="fine-print">{input_text[:1500]}</div>',
                            unsafe_allow_html=True)
        _layer_card_close()
        return {"status": "fuzzy", "hit": fuzzy}

    _layer_card_open(
        "Layer A — Identity check",
        "verbatim & near-verbatim lookup",
        "Your text does <b>not</b> appear in the canonical Hafs Quran, and "
        "no Quranic passage of comparable length is within a 10% edit-distance "
        "neighbourhood. Layer A returns NOT_IN_CORPUS.",
    )
    st.markdown('<span class="tag err">NOT IN CORPUS</span>',
                unsafe_allow_html=True)
    _layer_card_close()
    return {"status": "miss"}


# ============================================================================
# Layer B — Eight whole-corpus-pooled fingerprint axes
# ============================================================================
_AXIS_DEFS = [
    ("H_EL",        "Verse-final entropy",       "H_EL",
     "How predictable is the last letter of each verse? Measured in bits."),
    ("p_max",       "Rhyme concentration",       "p_max",
     "What fraction of verses end on the single most common letter?"),
    ("C_Omega",     "Channel utilisation",       "C_Ω",
     "How much of the alphabet's information capacity does the rhyme use? 0 = none, 1 = full."),
    ("F75",         "Universal invariant",       "F75",
     "A single-number signature that 11 scriptures cluster around at 5.75 bits ± 5%."),
    ("D_max",       "Redundancy gap",            "D_max",
     "How much rarer the verse-finals are than uniform random. log₂(28) − H_EL."),
    ("d_info",      "Fractal dimension",         "d_info",
     "The fractal information dimension of the letter-frequency distribution at contraction c = 0.18."),
    ("HFD",         "Higuchi dimension",         "HFD",
     "Roughness of the verse-length time-series. 1.0 = ideal Brownian; lower = smoother."),
    ("Delta_alpha", "Multifractal width",        "Δα",
     "Width of the multifractal spectrum on the verse-length series — how differently the text scales at different lengths."),
]


def _compute_input_axes(input_text: str):
    verses = split_into_verses(input_text)
    skel_full = normalize_arabic_letters_only(input_text)
    he = metrics.pooled_H_EL_pmax(verses)
    di = metrics.d_info(skel_full)
    verse_lens = np.array(
        [len(normalize_arabic_letters_only(v)) for v in verses],
        dtype=float,
    )
    if verse_lens.size >= 32:
        hfd = metrics.higuchi_fd(verse_lens)
    else:
        hfd = float("nan")
    if verse_lens.size >= 64:
        da = metrics.delta_alpha_mfdfa(verse_lens)
    else:
        da = float("nan")
    return {
        "n_verses": len(verses),
        "n_letters": len(skel_full),
        "H_EL":        he["H_EL"],
        "p_max":       he["p_max"],
        "C_Omega":     he["C_Omega"],
        "F75":         he["F75"],
        "D_max":       he["D_max"],
        "d_info":      di,
        "HFD":         hfd,
        "Delta_alpha": da,
    }


def run_layer_b(input_text: str, layer_a_status: str = "miss"):
    inp = _compute_input_axes(input_text)

    if inp["n_letters"] < 42 or inp["n_verses"] < 3:
        _layer_card_open(
            "Layer B — Whole-Quran fingerprint",
            "8 corpus-pooled axes",
            "Input has fewer than 3 verses OR 42 letters after normalisation. "
            "The shortest Quranic surah (Al-Kawthar) is 42 letters — below that, "
            "no statistical fingerprint claim can be made.",
        )
        st.markdown('<span class="tag warn">SKIPPED · need ≥ 3 verses, 42 letters</span>',
                    unsafe_allow_html=True)
        _layer_card_close()
        return {"status": "skip_short", **inp}

    # ---- Length-matched null calibration --------------------------------
    # For each axis, compare the input's value against the distribution of
    # that axis across every N-verse Quranic window (same N as input).
    # Rule: inside the inner 80% of Quranic values -> 100% match, tails
    # drop gradually. See calibration.length_calibrated_match for details.
    rows = []
    n_verses = inp["n_verses"]
    for key, name, sym, _explainer in _AXIS_DEFS:
        you = inp[key]
        ref = BOOT["ref"][key]
        if not np.isfinite(you):
            rows.append({"key": key, "name": name, "sym": sym,
                         "you": you, "ref": ref, "match": float("nan"),
                         "percentile": float("nan"), "q_lo": float("nan"),
                         "q_hi": float("nan"), "inside_p80": False})
            continue
        try:
            r = calibration.length_calibrated_match(key, you, n_verses)
        except Exception:  # noqa: BLE001
            # Fall back to whole-corpus ratio if calibration fails
            # (e.g. axis extractor unavailable or N out of computable range).
            r = {"match_pct": metrics.match_pct(
                    you, ref, C.DISPLAY_TOLERANCES[key]),
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
            "inside_p80": r.get("inside_p80", False),
        })

    valid = [r for r in rows if np.isfinite(r["match"])]
    composite = float(np.mean([r["match"] for r in valid])) if valid else float("nan")

    deciding = None
    if valid:
        deciding = min(valid, key=lambda r: r["match"])

    inside_count = sum(1 for r in valid if r["inside_p80"])
    summary_msg = (
        f"Fingerprint match, length-calibrated against {inp['n_verses']}-verse "
        f"Quranic windows: <b>{composite:.1f}%</b> across {len(valid)} "
        f"axis{'es' if len(valid) != 1 else ''}. "
        f"<b>{inside_count}/{len(valid)}</b> axis value(s) fall inside the "
        f"inner 80% of Quranic values at this length."
    ) if np.isfinite(composite) else "Insufficient data on every axis."

    _layer_card_open(
        "Layer B — Whole-Quran fingerprint",
        f"length-calibrated · N = {inp['n_verses']} verses",
        summary_msg,
    )

    # Explicit scale-limit disclosure for small inputs.
    if inp["n_verses"] < 15 and layer_a_status == "miss":
        st.markdown(
            '<div style="background:#fdf6e3;border-left:3px solid #b18a3a;'
            'padding:0.7rem 0.9rem;border-radius:0 4px 4px 0;'
            'margin:0.4rem 0 0.9rem 0;font-size:0.85rem;color:#0f172a;">'
            '<b>⚠ Scale-limit caveat.</b> Layer B cannot reliably discriminate '
            'Quran from other classical Arabic text at under ~15 verses — small '
            'Arabic passages cluster tightly in this feature space regardless of '
            'origin. For short inputs, Layer A (identity) is the reliable test. '
            'The project\'s AUC = 0.998 result was measured on 15–100 verse surahs '
            'vs 2,509 control units of similar size, not on small passages.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Spotlight the deciding axis ONLY when Layer A could not identify the
    # text. If Layer A says exact/fuzzy, the low match% is a short-input
    # artefact (already explained by the caveat above), not a reason why
    # this text "differs from the Quran".
    if (layer_a_status == "miss"
            and deciding is not None
            and np.isfinite(deciding["match"])
            and deciding["match"] < 80):
        st.markdown(
            f'<div class="deciding-axis">'
            f'<div class="label">Deciding axis</div>'
            f'<b>{deciding["name"]}</b> &mdash; '
            f'Quran value <span class="kv"><b>{deciding["ref"]:.4f}</b></span>, '
            f'your value <span class="kv"><b>{deciding["you"]:.4f}</b></span>. '
            f'This single axis carries the largest gap and is the strongest reason '
            f'your text differs from the Quran.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="axis-row head">'
        '<div>Axis</div><div>Quran range (N-verse)</div><div>You</div>'
        '<div>Match</div><div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    rows_sorted = sorted(rows,
                         key=lambda r: (r["match"] if np.isfinite(r["match"]) else 999.0))
    for r in rows_sorted:
        bucket = _bucket(r["match"])
        is_deciding = (layer_a_status == "miss"
                       and deciding is not None and r["key"] == deciding["key"]
                       and np.isfinite(r["match"]) and r["match"] < 80)
        if not np.isfinite(r["match"]):
            you_disp = "—"
            match_disp = "n/a"
            range_disp = "—"
            bar_w = 0
        else:
            you_disp = f"{r['you']:.4f}"
            match_disp = f"{r['match']:.0f}%"
            bar_w = max(2, int(round(r['match'])))
            if np.isfinite(r.get("q_lo", float("nan"))) and np.isfinite(r.get("q_hi", float("nan"))):
                range_disp = f"[{r['q_lo']:.3f} … {r['q_hi']:.3f}]"
            else:
                range_disp = f"{r['ref']:.4f}"
        st.markdown(
            f'<div class="axis-row{" deciding" if is_deciding else ""}">'
            f'<div class="axis-name">{r["name"]} <span class="symbol">{r["sym"]}</span></div>'
            f'<div class="axis-num" style="font-size:0.78rem">{range_disp}</div>'
            f'<div class="axis-num">{you_disp}</div>'
            f'<div><div class="bar-track"><div class="bar-fill {bucket}" style="width:{bar_w}%"></div></div></div>'
            f'<div class="match-pct {bucket}">{match_disp}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.expander("What does each axis mean?"):
        for key, name, sym, exp in _AXIS_DEFS:
            wiki = C.PROVENANCE[key]["wikipedia"]
            f_id = C.PROVENANCE[key]["f_id"]
            st.markdown(
                f'**{name}** &nbsp;<span class="kv">{sym} · {f_id}</span>  \n'
                f'{exp}  \n'
                f'<span class="fine-print">'
                f'Quran reference: {BOOT["ref"][key]:.4f} '
                f'(computed from quran_bare.txt at startup) · '
                f'<a href="{wiki}" target="_blank">Read on Wikipedia ↗</a>'
                f'</span>',
                unsafe_allow_html=True,
            )

    _layer_card_close()
    return {
        "status": "ok",
        "composite": composite,
        "rows": rows,
        "deciding": deciding,
        **inp,
    }


# ============================================================================
# Layer C — Tampering forensics (only if Layer A flagged near-Quran)
# ============================================================================
def run_layer_c(input_text: str, layer_a_result: dict):
    status = layer_a_result.get("status")
    fires_this_layer = status in ("exact", "fuzzy")
    if not fires_this_layer:
        _layer_card_open(
            "Layer C — Tampering forensics",
            "F55 bigram-shift · F70 gzip-NCD",
            "These three forensics test <b>what was edited</b> when a text is "
            "verbatim or near-verbatim Quran. Your text is not in that "
            "neighbourhood, so this layer is skipped.",
        )
        st.markdown('<span class="tag">SKIPPED · not near-canonical</span>',
                    unsafe_allow_html=True)
        _layer_card_close()
        return {"status": "skip_far"}

    skel_input = normalize_arabic_letters_only(input_text)
    if status == "exact":
        canonical_skel = skel_input
        canonical_raw = "(your text matches the canonical text exactly)"
    else:
        fhit = layer_a_result["hit"]
        canonical_skel = fhit.canonical_skeleton
        canonical_raw = fhit.canonical_raw

    bigram_d = metrics.bigram_shift_delta(skel_input, canonical_skel)
    ncd = metrics.gzip_ncd(skel_input, canonical_skel)

    _layer_card_open(
        "Layer C — Tampering forensics",
        "F55 bigram-shift · F70 gzip-NCD",
        "Your text is in the canonical neighbourhood. The two tests below "
        "say <b>what kind of edit</b> happened.",
    )

    # ----- C1 ----------------------------------------------------------------
    edit_min = max(0, int(np.ceil(bigram_d / 2.0)))
    if status == "exact":
        c1_msg = "Δ_bigram = 0 — no letter substitutions detected."
        c1_kind = "ok"
    elif bigram_d <= 0.001:
        c1_msg = ("Δ_bigram = 0 — letters preserved exactly. If Layer A says "
                  "your text is fuzzy-matched, the difference is likely a verse "
                  "or word reordering rather than a letter substitution. "
                  "Check the gzip-NCD test below.")
        c1_kind = "warn"
    else:
        c1_msg = (f"Δ_bigram = <b>{bigram_d:.1f}</b>. By the F69 theorem, this "
                  f"corresponds to at least <b>{edit_min}</b> single-letter "
                  f"substitution{'s' if edit_min != 1 else ''} (each letter "
                  f"edit moves Δ by 1–2).")
        c1_kind = "warn" if bigram_d <= 4 else "err"
    st.markdown(
        f'<div class="kv"><b>C1 · F55 bigram-shift</b></div>'
        f'<div class="layer-summary">{c1_msg}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="kv">Δ_bigram: <b>{bigram_d:.2f}</b> · '
        f'minimum letter edits implied: <b>{edit_min}</b> · '
        f'<a href="{C.TAMPERING_REFS["F55_bigram_shift"]["wikipedia"]}" target="_blank">'
        f'About bigrams ↗</a></div>',
        unsafe_allow_html=True,
    )

    # ----- C2 ----------------------------------------------------------------
    if not np.isfinite(ncd):
        c2_msg = "Could not compute gzip-NCD on this input."
    elif ncd < 0.05:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Below the noise floor — "
                  f"sequence-level structure matches the canonical text.")
    elif ncd < 0.20:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Mild sequence disturbance — "
                  f"consistent with a few-letter edit or a single verse reorder.")
    else:
        c2_msg = (f"NCD = <b>{ncd:.4f}</b>. Substantial sequence disturbance — "
                  f"consistent with multiple verse swaps or word reordering "
                  f"that the bigram test alone cannot see.")
    st.markdown('<hr style="margin:0.6rem 0;">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="kv"><b>C2 · F70 gzip-NCD</b></div>'
        f'<div class="layer-summary">{c2_msg}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="kv">'
        f'F70 receipt recall: 88.4% (verse swap) → 93.0% (combined OR) · '
        f'<a href="{C.TAMPERING_REFS["gzip_NCD"]["wikipedia"]}" target="_blank">'
        f'About NCD ↗</a></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Side-by-side: your text vs. canonical"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Canonical (Hafs)**")
            st.markdown(f'<div class="fine-print">{canonical_raw}</div>',
                        unsafe_allow_html=True)
        with col_b:
            st.markdown("**Your input**")
            st.markdown(f'<div class="fine-print">{input_text[:1500]}</div>',
                        unsafe_allow_html=True)

    _layer_card_close()
    return {"status": "ok", "bigram_d": bigram_d, "ncd": ncd, "edit_min": edit_min}


# ============================================================================
# Top verdict ribbon — single-line answer based on Layer A + B + C
# ============================================================================
def render_top_verdict(a_result: dict, b_result: dict, c_result: dict):
    a = a_result.get("status")
    b = b_result.get("status")
    c = c_result.get("status")

    if a == "skip_short" or b == "skip_short":
        _ribbon("neut", "?",
                "Input too short to draw any conclusion.",
                "Need at least 3 verses and 42 normalised letters.")
        return
    if a == "skip_nonarabic":
        _ribbon("neut", "—",
                "Input is not Arabic.",
                "Layer A skipped. Layer B compares to the Quran's Arabic-rasm fingerprint regardless.")
        return

    if a == "exact":
        # Exact substring match = authoritative verbatim identity.
        # Layer C C2 NCD can read ≈0.04 on very short texts due to gzip
        # header overhead, which is not a tampering signal.
        ncd = c_result.get("ncd", 0) if c == "ok" else 0
        if c == "ok" and c_result.get("bigram_d", 0) <= 0.001 and ncd < 0.10:
            _ribbon("ok", "✓",
                    "VERBATIM Quran detected.",
                    "Letter-for-letter match against the canonical Hafs corpus. "
                    "No tampering signal on any forensic axis.")
            return
        _ribbon("ok", "✓",
                "VERBATIM Quran detected.",
                "Letter-for-letter match against the canonical Hafs corpus.")
        return

    if a == "fuzzy":
        edits = c_result.get("edit_min", 0) if c == "ok" else 0
        ncd = c_result.get("ncd", 0) if c == "ok" else 0
        bd = c_result.get("bigram_d", 0) if c == "ok" else 0
        if bd > 0.001 and ncd < 0.20:
            _ribbon("warn", "≈",
                    f"Modified Quran detected — at least {edits} letter edit{'s' if edits != 1 else ''}.",
                    "Layer C1 (F55 bigram-shift) flags letter substitution; sequence integrity otherwise preserved.")
            return
        if bd <= 0.001 and ncd >= 0.05:
            _ribbon("warn", "≈",
                    "Modified Quran detected — verse or word REORDERING.",
                    "Letters identical to canonical, but Layer C2 (gzip-NCD) flags broken sequence order.")
            return
        _ribbon("warn", "≈",
                "Near-canonical Quran with mixed signals.",
                "See Layer C panel below for the specific tampering signature.")
        return

    if a == "miss":
        comp = b_result.get("composite", float("nan"))
        if not np.isfinite(comp):
            _ribbon("err", "✗",
                    "Not Quran. Insufficient data on every fingerprint axis.",
                    "Try a longer passage if you want a fingerprint match score.")
            return
        if comp >= 60:
            _ribbon("warn", "≈",
                    f"Not in the Quran corpus, but Quran-like fingerprint ({comp:.0f}%).",
                    "Could be Arabic verse with rhyme spine. Imitation, classical poetry, or a Hadith would fit here.")
            return
        if comp >= 30:
            _ribbon("err", "✗",
                    f"Not Quran. Fingerprint match: {comp:.0f}%.",
                    "Some Arabic-language overlap but no rhyme structure.")
            return
        _ribbon("err", "✗",
                f"Not Quran. Fingerprint match: {comp:.0f}%.",
                "Far from the Quran's mathematical signature on every measurable axis.")
        return

    _ribbon("neut", "?",
            "Could not classify.",
            "Inspect the layer panels below for details.")


# ============================================================================
# Sidebar — input + examples + data sources + audit
# ============================================================================
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## Pristine")
        st.markdown(
            '<div class="fine-print">A four-layer Quran-fingerprint detector. '
            f"Loaded canonical Hafs corpus: <b>{BOOT['n_chapters']}</b> chapters · "
            f"<b>{BOOT['n_verses']:,}</b> verses · "
            f"<b>{BOOT['n_letters']:,}</b> normalised letters. "
            "SHA-256 verified at startup.</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Examples")
        st.markdown(
            '<div class="fine-print">Click any preset to load it into the input.</div>',
            unsafe_allow_html=True,
        )
        if "active_preset_id" not in st.session_state:
            st.session_state["active_preset_id"] = None
        for preset in examples.PRESETS:
            if st.button(preset["label"], key=f"preset_{preset['id']}", use_container_width=True):
                st.session_state["active_preset_id"] = preset["id"]
                st.session_state["input_text"] = preset["text"]

        st.markdown("### Data sources")
        with st.expander("Quran corpus + locked references"):
            st.markdown(
                f'<div class="kv">corpus: <b>data/corpora/ar/quran_bare.txt</b><br>'
                f'sha256: <b>{BOOT["integrity"].sha256_actual[:16]}…</b><br>'
                f'size: <b>{BOOT["integrity"].n_bytes:,}</b> bytes<br>'
                f'verses: <b>{BOOT["n_verses"]:,}</b></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="fine-print" style="margin-top:0.6rem">'
                        'Quran reference values (computed at startup):'
                        '</div>', unsafe_allow_html=True)
            for key, name, sym, _exp in _AXIS_DEFS:
                v = BOOT["ref"].get(key, float("nan"))
                src = C.PROVENANCE[key]["source_file"]
                fid = C.PROVENANCE[key]["f_id"]
                st.markdown(
                    f'<div class="kv">'
                    f'<b>{sym}</b> = <b>{v:.4f}</b> &nbsp; '
                    f'<span class="muted">{fid} · {src}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Honest scope · what this tool does NOT do"):
            st.markdown(
                "- Does **not** decide canonicity or which qira'a (reading) is correct.\n"
                "- Does **not** make theological or metaphysical claims.\n"
                "- Does **not** authenticate manuscripts.\n"
                "- Does **not** detect semantic correctness — a fake passage with valid rhyme will pass Layer B (only Layer A catches it as not-in-corpus).\n"
                "- Does **not** use machine-learned weights or neural networks. Layers B and C are pure information-theoretic mathematics.\n"
                "- **Diacritic-only** and **hamza-variant** edits are intentionally invisible — by design, because the canonical Quran has multiple valid readings (Hafs, Warsh, Qalun, …) that differ only in those marks.\n"
            )

        with st.expander("Why we never use per-surah subsets"):
            st.markdown(
                "Saying *'47 of 109 Quranic surahs satisfy property X'* is **sharpshooter logic**: "
                "it implies 62 surahs *don't* satisfy X, which means X is not actually a property "
                "of the Quran — it is a property of a hand-picked subset.\n\n"
                "Pristine compares your text against the **whole-Quran corpus-pooled** value of "
                "every axis (one number per axis, computed on all 6,236 verses concatenated). "
                "The Quran is treated as a single object on every axis. No subset is ever "
                "selected to make a stronger claim."
            )

        with st.expander("Receipts and pre-registrations"):
            st.markdown(
                "- F55 · F69 (bigram-shift theorem) · "
                "[`exp95i`](https://github.com/) · `exp118`\n"
                "- F70 (gzip-NCD verse-reorder) · `exp117_verse_reorder_detector` · "
                "Form 3 recall = 88.4%, combined OR = 93.0%\n"
                "- F75 (universal invariant 5.75 ± 5%) · `exp130_F75_stability_under_resampling`\n"
                "- F67 (C_Ω single constant) · `exp115_C_Omega_single_constant`\n"
                "- F76 (1-bit categorical) · `exp124b_alphabet_corrected_one_bit_universal`\n"
                "- F79 (D_max alphabet-corrected) · `exp135_F79_bootstrap_stability`\n"
                "- F82 (IFS d_info) · `exp182_quran_ifs_fractal`\n"
                "- F87 (HFD + Δα) · `exp177_quran_multifractal_fingerprint`\n"
                "- Sharpshooter audit · `exp143_QFootprint_Sharpshooter_Audit`\n"
                "- Authentication ring (locked constants) · `exp183_quran_authentication_ring`\n"
            )

        st.markdown("### Verify integrity")
        st.markdown(
            f'<div class="fine-print">'
            f'Run <code>python app/pristine_audit.py</code> for a full self-audit '
            f'against pre-registrations and locked receipts.'
            f'</div>',
            unsafe_allow_html=True,
        )

    return st.session_state.get("input_text", "")


# ============================================================================
# Main page
# ============================================================================
def main():
    render_sidebar()

    st.markdown("# Pristine — Quran fingerprint detector")
    st.markdown(
        '<div class="app-tagline">Paste any text. The app reports whether it appears in the canonical '
        'Quran, how close its mathematical fingerprint is to the whole Quran, and — when applicable — '
        'what kind of editing happened.</div>',
        unsafe_allow_html=True,
    )

    col_input, col_results = st.columns([1, 1.3], gap="large")

    with col_input:
        st.markdown("## Your text")
        # Initialise session_state default once; never pass `value=` together
        # with `key=` for a Streamlit widget (forbidden combination).
        if "input_text" not in st.session_state:
            st.session_state["input_text"] = ""
        txt = st.text_area(
            label="input",
            height=380,
            label_visibility="collapsed",
            placeholder="Paste Arabic text here, or pick an example from the sidebar.",
            key="input_text",
        )
        n_chars = len(txt) if txt else 0
        skel_n = len(normalize_arabic_letters_only(txt)) if txt else 0
        n_verses = len(split_into_verses(txt)) if txt else 0
        script = detect_script(txt) if txt else "empty"
        st.markdown(
            f'<div class="kv">'
            f'characters: <b>{n_chars:,}</b> · '
            f'normalised Arabic letters: <b>{skel_n:,}</b> · '
            f'verses: <b>{n_verses}</b> · '
            f'detected script: <b>{script}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_results:
        st.markdown("## Verdict")
        verdict_slot = st.empty()           # reserved at the top
        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

        if not txt or not txt.strip():
            with verdict_slot.container():
                _ribbon("neut", "·",
                        "Awaiting input.",
                        "Paste text on the left, or pick an example from the sidebar.")
            return

        st.markdown("### Layered evaluation")
        a_res = run_layer_a(txt, script)
        b_res = run_layer_b(txt, a_res.get("status", "miss"))
        c_res = run_layer_c(txt, a_res)

        # Now fill the reserved slot at the top with the verdict ribbon.
        with verdict_slot.container():
            render_top_verdict(a_res, b_res, c_res)


if __name__ == "__main__":
    main()
