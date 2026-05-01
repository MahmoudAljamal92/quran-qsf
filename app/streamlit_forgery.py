"""app/streamlit_forgery.py — Forgery-Detection Web UI (F55 + F68).

Run locally:
    streamlit run app/streamlit_forgery.py

Requirements (added in app/requirements.txt):
    streamlit>=1.30

Three modes:
  1. Compare two texts — paste / upload two Arabic Qur'ān-class passages and
     get the Δ_bigram + F68 gzip-fingerprint verdict (exactly the Ṣanʿāʾ-style
     audit).
  2. Plant an edit — paste one text, choose k random letter substitutions,
     watch the detector flag it (live demo of the F55 / F69 theorem).
  3. Verse-reorder test — paste 3+ verses, swap two at random, see if the
     gzip-form (F68) catches the permutation.

Honest UI: every output panel restates F55's scope limits (measures distance,
not authenticity).
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import streamlit as st

# Make the local tools/ importable
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.sanaa_compare import (  # noqa: E402
    bigram_histogram,
    compare_texts,
    delta_bigram,
    gzip_fingerprint_delta,
    normalise_arabic,
)

ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")

# ---------------------------------------------------------------------- UI

st.set_page_config(
    page_title="Qurʾān Forgery Detector — F55",
    page_icon="🪶",
    layout="wide",
)

st.title("🪶 Qurʾān Forgery Detector")
st.caption(
    "Bigram-distance (F55) + sequence-aware fingerprint (F68) "
    "— measures **how far** two Arabic texts are. "
    "_Cannot decide which text is correct: only the distance._"
)

mode = st.sidebar.radio(
    "Mode",
    ["Compare two texts", "Plant a k-letter edit", "Verse-reorder test", "About"],
    index=0,
)

# ---------------------------------------------------------------- helpers

def _show_metric_row(res: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Δ_bigram", f"{res['delta_bigram']:.2f}")
    c2.metric("Min letter-edits (k_min)", f"≥ {res['implied_k_min_letter_edits']}")
    c3.metric("Skeleton chars", f"{res['skeleton_chars1']} vs {res['skeleton_chars2']}")
    c4.metric("gzip-fingerprint Δ", f"{res['gzip_fingerprint_delta']:.4f}")


def _show_verdicts(res: dict) -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### F55 (bigram) verdict")
        verdict = res["f55_verdict"]
        if "IDENTICAL" in verdict:
            st.success(verdict)
        elif "NEAR_VARIANT" in verdict:
            st.info(verdict)
        elif "DISTANT" in verdict:
            st.error(verdict)
        else:
            st.warning(verdict)
    with c2:
        st.markdown("### F68 (gzip / order) verdict")
        f68 = res["f68_verdict"]
        if "BYTE_IDENTICAL" in f68:
            st.success(f68)
        elif "NEAR_IDENTICAL" in f68:
            st.info(f68)
        elif "MAJOR" in f68:
            st.error(f68)
        else:
            st.warning(f68)


def _honesty_panel() -> None:
    with st.expander("⚖️  Scope & honest limits"):
        st.markdown(
            """
- **Δ_bigram is a distance, not a truth-value.** A small Δ means the two texts
  share their bigram histogram closely; it does not tell you which (if any)
  is the canonical reading.
- **Diacritic-only disputes are invisible.** The 28-consonant skeleton strips
  ḥarakāt, hamza variants, and tatweel by design (so the metric stays
  reproducible across Mushaf editions).
- **Δ ≤ 2k is a theorem.** Any k-letter substitution gives Δ_bigram ≤ 2k —
  proved in F69 / exp118. So *if you observe Δ = 14 between two passages,
  at least 7 letters must differ*, regardless of any apologetic claim.
- **Verse-reordering is permutation-invariant for F55** but visible in F68
  (gzip fingerprint). Use both forms together for a full audit.
            """
        )


# ============================================================ Mode 1

if mode == "Compare two texts":
    st.header("Compare two texts")
    st.write(
        "Paste a canonical Qurʾān passage on the left and any candidate "
        "(e.g. a Ṣanʿāʾ palimpsest transcription) on the right. The detector "
        "reports their bigram distance and gzip fingerprint."
    )

    c1, c2 = st.columns(2)
    with c1:
        label1 = st.text_input("Label 1", value="canonical", key="lab1")
        text1 = st.text_area(
            "Text 1",
            height=240,
            key="t1",
            value=(
                "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
                "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ\n"
                "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
                "مَٰلِكِ يَوْمِ ٱلدِّينِ"
            ),
        )
    with c2:
        label2 = st.text_input("Label 2", value="candidate", key="lab2")
        text2 = st.text_area(
            "Text 2",
            height=240,
            key="t2",
            value=(
                "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
                "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمُونَ\n"   # one-letter edit (ين→ون)
                "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
                "مَٰلِكِ يَوْمِ ٱلدِّينِ"
            ),
        )

    if st.button("Compare", type="primary"):
        res = compare_texts(text1, text2, label1, label2)
        if "error" in res:
            st.error(f"Could not compare: {res['error']}")
        else:
            _show_metric_row(res)
            _show_verdicts(res)
            with st.expander("Normalised skeletons (28-letter rasm)"):
                st.code(normalise_arabic(text1), language="text")
                st.code(normalise_arabic(text2), language="text")
            _honesty_panel()


# ============================================================ Mode 2

elif mode == "Plant a k-letter edit":
    st.header("Plant a k-letter edit")
    st.write(
        "Paste one passage. Choose k. The app will randomly substitute k "
        "letters and show that Δ_bigram ≤ 2k (Theorem F69, exp118)."
    )

    text = st.text_area(
        "Original text",
        height=240,
        value=(
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ "
            "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ مَٰلِكِ يَوْمِ ٱلدِّينِ "
            "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ"
        ),
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        k = st.number_input("k (number of letters to change)", 1, 20, 3)
    with c2:
        seed = st.number_input("seed", 0, 99999, 42)
    with c3:
        n_trials = st.number_input("trials", 1, 50, 1)

    if st.button("Plant edit", type="primary"):
        rng = random.Random(int(seed))
        norm = normalise_arabic(text)
        if not norm or sum(1 for c in norm if c in ARABIC_28) < int(k):
            st.error("Text too short or empty after normalisation.")
        else:
            results = []
            for trial in range(int(n_trials)):
                positions = [i for i, c in enumerate(norm) if c in ARABIC_28]
                chosen = rng.sample(positions, int(k))
                edited_chars = list(norm)
                for p in chosen:
                    old = edited_chars[p]
                    new = rng.choice([L for L in ARABIC_28 if L != old])
                    edited_chars[p] = new
                edited = "".join(edited_chars)
                h_orig = bigram_histogram(norm)
                h_edit = bigram_histogram(edited)
                d = delta_bigram(h_orig, h_edit)
                gz = gzip_fingerprint_delta(norm, edited)
                results.append({
                    "trial": trial + 1,
                    "delta": d,
                    "bound": 2 * int(k),
                    "bound_holds": d <= 2 * int(k) + 1e-9,
                    "k_min_implied": math.ceil(d / 2.0),
                    "gzip_delta": gz,
                    "edited_skeleton": edited,
                })

            ok = all(r["bound_holds"] for r in results)
            if ok:
                st.success(
                    f"Theorem verified on {len(results)} trial(s): "
                    f"Δ ≤ 2k = {2 * int(k)} for every plant."
                )
            else:
                st.error("Theorem violated! This should not happen — please report.")

            for r in results:
                with st.container():
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Δ", f"{r['delta']:.2f}")
                    c2.metric("Bound 2k", f"{r['bound']}")
                    c3.metric("Implied k_min", f"≥ {r['k_min_implied']}")
                    c4.metric("gzip Δ", f"{r['gzip_delta']:.4f}")
            _honesty_panel()


# ============================================================ Mode 3

elif mode == "Verse-reorder test":
    st.header("Verse-reorder test")
    st.write(
        "Paste 3+ verses (one per line). The app swaps two verses at random "
        "and reports both F55 (bigram, permutation-invariant) and F68 "
        "(gzip fingerprint, order-sensitive)."
    )
    text = st.text_area(
        "Verses (one per line)",
        height=240,
        value=(
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
            "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ\n"
            "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ\n"
            "مَٰلِكِ يَوْمِ ٱلدِّينِ\n"
            "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ\n"
            "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ"
        ),
    )
    seed = st.number_input("seed", 0, 99999, 7, key="rseed")

    if st.button("Swap two verses & check", type="primary"):
        rng = random.Random(int(seed))
        verses = [v.strip() for v in text.splitlines() if v.strip()]
        if len(verses) < 3:
            st.error("Need at least 3 verses.")
        else:
            i, j = rng.sample(range(len(verses)), 2)
            swapped = verses.copy()
            swapped[i], swapped[j] = swapped[j], swapped[i]
            orig_text = "\n".join(verses)
            swap_text = "\n".join(swapped)
            res = compare_texts(orig_text, swap_text,
                                "canonical_order", f"swapped_{i}_{j}")
            st.write(f"Swapped verse {i + 1} ↔ verse {j + 1}.")
            _show_metric_row(res)
            _show_verdicts(res)
            if res["delta_bigram"] == 0 and res["gzip_fingerprint_delta"] > 0:
                st.warning(
                    "F55 (bigram) is permutation-invariant: it cannot see this "
                    "verse swap. F68 (gzip fingerprint) **does** detect it. "
                    "Always run both forms in production audits."
                )
            _honesty_panel()


# ============================================================ Mode 4

elif mode == "About":
    st.header("About this detector")
    st.markdown(
        """
**F55 — Bigram-distance forgery detector.**
For any two Arabic texts $T_1, T_2$, define
$$
\\Delta_{\\text{bigram}}(T_1, T_2) = \\frac{1}{2} \\sum_{ab} |c_{T_1}(ab) - c_{T_2}(ab)|.
$$
Theorem (F69, exp118): for any $k$-letter substitution within a single text,
$\\Delta_{\\text{bigram}} \\leq 2k$ — a mathematical certainty.

**F68 — gzip fingerprint.** Sequence-aware: detects verse re-orderings that
F55 misses (since bigrams are computed within words and ignore inter-word
order across the whole passage).

**Scope.** We test every Arabic Qurʾān sūrah, ~6 Arabic peer corpora,
Hebrew Tanakh, Greek NT, Pali Tipiṭaka, Sanskrit Rigveda, and Avestan Yasna.
The theorem is alphabet-independent; recall ≥ 99% holds in every tested
tradition.

**What it cannot do.**

- Decide which of two competing readings is canonical (that is a
  paleographic / chains-of-transmission question).
- See pure ḥarakāt / diacritic-only differences (stripped by design).
- See word-internal anagrams (e.g. `كتب` vs `تكب`) at the bigram level —
  use a trigram or LC2 detector for that.

Code: `tools/sanaa_compare.py`, `experiments/exp116-119/*`.
Replication receipts under `results/experiments/`.
        """
    )
