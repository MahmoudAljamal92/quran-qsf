"""
tools/qsf_score_app.py
======================
Streamlit UI wrapper around tools/qsf_score.py.

Installation
    pip install streamlit
    python -m streamlit run tools/qsf_score_app.py

Features
    * Paste or upload Arabic text; it is split into verses on newlines.
    * Reports EL, VL_CV, CN, H_cond, T, Phi_M, and grade.
    * Plots the input on a 2-D (T, EL) scatter alongside the Quran
      Band-A cluster and the pooled Arabic-ctrl cluster from phase_06.
    * No network calls; all computation is local.

Disclaimer
    This is a SCORING tool, not a forensic detector. Phi_M above the
    A+ threshold is necessary but not sufficient for a Quran-like
    stylometric signature. Do not interpret a high score as authentication.

Compatible with Python 3.11+, streamlit >= 1.28.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np

try:
    import streamlit as st
except ImportError as e:
    print("Streamlit not installed. Run: pip install streamlit", file=sys.stderr)
    raise SystemExit(1) from e

from experiments._lib import load_phase  # noqa: E402
from src import features as ft  # noqa: E402
from tools.qsf_score import score, grade  # noqa: E402


@st.cache_resource(show_spinner="Loading phase_06 checkpoint...")
def _load_state() -> dict:
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    mu = np.asarray(state["mu"], dtype=float)
    Sinv = np.asarray(state["S_inv"], dtype=float)
    CORPORA = state["CORPORA"]

    # Pre-compute T, EL for all band-A units per corpus for the scatter.
    corpus_points: dict[str, list[tuple[float, float]]] = {}
    for name, units in CORPORA.items():
        pts: list[tuple[float, float]] = []
        for u in units:
            if 15 <= len(u.verses) <= 100:
                el = float(ft.el_rate(u.verses))
                he = float(ft.h_el(u.verses))
                hc = float(ft.h_cond_roots(u.verses))
                t = hc - he
                pts.append((t, el))
        if pts:
            corpus_points[name] = pts
    return {"mu": mu, "Sinv": Sinv, "corpus_points": corpus_points}


def main() -> None:
    st.set_page_config(page_title="QSF v7.2 scorer", layout="wide")
    st.title("QSF v7.2 — (T, EL, Φ_M) scorer")
    st.caption(
        "Scores an Arabic text against the 5-D Quranic Structural "
        "Fingerprint. Phi_M measures Mahalanobis distance from the "
        "Arabic-control centroid on the locked phase_06 checkpoint."
    )

    state = _load_state()

    with st.sidebar:
        st.header("Input")
        src = st.radio("Source", ["Paste text", "Upload file"], index=0)
        text = ""
        if src == "Paste text":
            text = st.text_area(
                "Arabic text (one verse per line)", height=300,
                placeholder="بسم الله الرحمن الرحيم\nالحمد لله رب العالمين\n...",
            )
        else:
            f = st.file_uploader("text file (utf-8)", type=["txt"])
            if f is not None:
                text = f.read().decode("utf-8", errors="ignore")
                st.caption(f"Uploaded: {f.name} ({len(text)} chars)")

        st.markdown("---")
        st.caption(
            "This is a scoring tool for RESEARCH use. A high Phi_M is "
            "necessary but not sufficient for authentication; the locked "
            "paper (docs/PAPER.md) specifies the edit-detection layer."
        )

    verses = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not verses:
        st.info("Paste or upload text to see its scores.")
        return

    try:
        r = score(verses)
    except Exception as e:  # surface any CamelTools / phase_06 load error
        st.error(f"Scoring failed: {e}")
        return

    # ---- metric row ---- #
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("n_verses", r["n_verses"])
    c2.metric("EL", f"{r['EL']:.4f}")
    c3.metric("VL_CV", f"{r['VL_CV']:.4f}")
    c4.metric("CN", f"{r['CN']:.4f}")
    c5.metric("H_cond", f"{r['H_cond']:.4f}")
    c6.metric("T", f"{r['T']:+.4f}")

    st.subheader(f"Φ_M = {r['Phi_M']:.3f}  →  grade {r['grade']}")
    st.caption(
        "cutoffs: A+ > 6.0, A > 4.0, B > 2.0, C > 1.0, D otherwise"
    )

    # ---- (T, EL) scatter ---- #
    st.markdown("---")
    st.subheader("Input vs phase_06 Band-A clusters")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    colour_map = {
        "quran": "black",
        "poetry_jahili": "#c67", "poetry_islami": "#b46",
        "poetry_abbasi": "#a24",
        "ksucca": "#48a", "arabic_bible": "#6a6",
        "hindawi": "#d90",
    }
    for name, pts in state["corpus_points"].items():
        if not pts:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.scatter(
            xs, ys,
            s=(50 if name == "quran" else 15),
            alpha=(0.7 if name == "quran" else 0.35),
            color=colour_map.get(name, "#888"), label=name,
        )
    ax.scatter(
        [r["T"]], [r["EL"]],
        s=180, marker="*", color="red",
        edgecolor="black", linewidth=1.2, label="YOUR INPUT",
    )
    ax.set_xlabel("T = H_cond − H_el (structural tension)")
    ax.set_ylabel("EL (end-letter rhyme rate)")
    ax.set_title("Band-A (15–100 verses) per-unit positions")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    st.pyplot(fig)

    with st.expander("Raw JSON"):
        st.json(r)


if __name__ == "__main__":
    main()
