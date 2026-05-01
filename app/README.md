# Forgery-Detection Web App (F55 + F68)

A self-contained Streamlit interface for the project's forgery-detection
toolchain: paste two Arabic passages and get an instant Δ_bigram report
plus an order-sensitive gzip fingerprint.

## Quick start

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_forgery.py
```

Then open the printed URL (default `http://localhost:8501`) in any browser.

## Modes

| Mode | What it does |
|---|---|
| **Compare two texts** | The Ṣanʿāʾ-style audit. Paste canonical vs candidate; get Δ_bigram, k_min, gzip fingerprint, verdicts. |
| **Plant a k-letter edit** | Live demo of the F69 theorem: pick a passage, substitute k random letters, watch Δ ≤ 2k hold. |
| **Verse-reorder test** | Demonstrate F55's permutation-invariance and F68's order-sensitivity together. |
| **About** | Honest scope statement — what F55 can and cannot prove. |

## Honest scope

- **F55 measures distance, not authenticity.** Δ_bigram is a single
  reproducible number, but it cannot tell you which reading is canonical.
- **Diacritic-only disputes are invisible** by design (so the metric stays
  reproducible across Mushaf editions).
- **Δ ≤ 2k is a theorem** (F69 / `experiments/exp118_multi_letter_F55_theorem`).
  Observing Δ = X always gives a hard lower bound `k ≥ ⌈X/2⌉` on the actual
  letter-edit count.
- **Word-internal anagrams** (e.g. `كتب` vs `تكب`) leave the bigram
  histogram unchanged at the rasm level — use a trigram or LC2 detector
  for those.

---

# Ring of Truth — 8-channel Quran-fingerprint meter (V3.31 closure)

A second Streamlit app: `ring_of_truth.py`. Runs the 8 Authentication-Ring channels (`exp183`) on any pasted/uploaded text and returns a continuous similarity-to-Quran percentage plus per-channel deviation bars. Supports 6 scripts (Arabic / Hebrew / Greek / Pāli / Avestan / Rigveda-Devanagari).

Launch locally:

```bash
pip install -r app/requirements.txt
streamlit run app/ring_of_truth.py
```

Deploy on Streamlit Cloud (free tier):

1. Push the repo to GitHub (see `../_release/github/README.md`).
2. Go to https://streamlit.io/cloud → **New app** → connect the repo.
3. Main file path: `app/ring_of_truth.py`. Click **Deploy**. (no config file needed.)

Verdict categories: ≥ 95 % QURAN-CLASS · 80–95 % QURAN-LIKE · 50–80 % RHYMED LITERARY CORPUS · < 50 % NON-RHYMED / MODERN PROSE. Channel weights: T1/T6/T7 count 2×, T2/T3/T4/T5/T8 count 1×. Short-input rules: < 10 chapters skip T6; < 100 letters skip T7.

---

## Files

- `ring_of_truth.py` — 8-channel Quran-fingerprint meter (multi-language)
- `streamlit_forgery.py` — main UI
- `requirements.txt` — Python dependencies
- `../tools/sanaa_compare.py` — pure-Python comparator (also usable as CLI)
- `../experiments/exp118_multi_letter_F55_theorem` — Δ ≤ 2k theorem & empirics
- `../experiments/exp117_verse_reorder_detector` — sequence-aware F68 detector
