"""scripts/_audit_f63_robustness.py
=========================================
Three robustness checks on F63's headline:

R1: Drop all synthetic-unit corpora (poetry × 3, hindawi, ksucca).
    Compare Quran ONLY against real-verse-boundary corpora
    (Hebrew Tanakh, Greek NT, Pali DN+MN, Avestan, Arabic Bible).
    If Quran still ranks 1/6 with same margins -> F63 is robust.

R2: Destroy Quran's real verse boundaries by re-chunking into 7-word
    blocks (the same chunking poetry suffers). If Quran's per-chunk
    p_max plummets to poetry's range, then F63's strength came from
    unit definition. If it stays high, the Quran's word-distribution
    is genuinely rhyme-clustered even at random word-window granularity.

R3: Compare Quran vs Arabic Bible HEAD-TO-HEAD. Both are real-verse
    religious prose in Arabic. If Quran beats Arabic Bible by ≥ 2x,
    that's a within-language within-genre clean comparison untainted
    by unit-mismatch.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _load_quran,
    _load_arabic_peers,
    _load_hebrew_tanakh,
    _load_greek_nt,
    _load_pali,
    _load_avestan,
    _features_universal,
)

print("# F63 robustness audit -- 3 checks\n")

# ============================================================
# R1 — restrict to real-verse-boundary corpora only
# ============================================================
print("# R1: drop synthetic-unit corpora; compare Quran vs real-verse only")
quran = _load_quran()
arabic = _load_arabic_peers()
arabic_bible = arabic.get("arabic_bible", [])
hebrew = _load_hebrew_tanakh()
greek = _load_greek_nt()
pali = _load_pali()
avestan = _load_avestan()

real_corpora = {
    "quran":         quran,
    "arabic_bible":  arabic_bible,
    "hebrew_tanakh": hebrew,
    "greek_nt":      greek,
    "pali":          pali,
    "avestan_yasna": avestan,
}

print("# corpus            n_units    median p_max    median H_EL  unit_type")
print("# -----------------  -------   -------------  -------------  ----------")
real_meds = {}
for name, units in real_corpora.items():
    fs = []
    for u in units:
        try:
            fs.append(_features_universal(u))
        except Exception:
            pass
    if not fs:
        continue
    pmax = statistics.median(f["p_max"] for f in fs)
    h_el = statistics.median(f["H_EL"] for f in fs)
    real_meds[name] = (pmax, h_el)
    print(f"#  {name:<17s} {len(fs):>5d}  "
          f"{pmax:>14.4f}  {h_el:>14.4f}  REAL_VERSE")

# Quran vs others
qpmax, qhel = real_meds["quran"]
others = [(n, p, h) for n, (p, h) in real_meds.items() if n != "quran"]
others_pmax = max((p for _, p, _ in others))
others_hel = min((h for _, _, h in others))
print()
print(f"# Quran p_max = {qpmax:.4f}  vs next-highest non-Quran = {others_pmax:.4f}  "
      f"-> ratio {qpmax/others_pmax:.4f} (need > 1.4 to pass F63 thresh)")
print(f"# Quran H_EL  = {qhel:.4f}  vs next-lowest  non-Quran = {others_hel:.4f}  "
      f"-> ratio {qhel/others_hel:.4f} (need < 0.5 to pass F63 thresh)")
r1_pass = (qpmax / others_pmax > 1.4) and (qhel / others_hel < 0.5)
print(f"# R1 verdict: {'PASS — F63 robust to dropping synthetic-unit corpora' if r1_pass else 'FAIL — F63 was driven by synthetic units'}")
print()

# ============================================================
# R2 — re-chunk Quran into 7-word blocks (destroy real verse boundaries)
# ============================================================
print("# R2: destroy Quran's real verse boundaries; chunk into 7-word blocks")
print("#     Compare to poetry's 7-word-chunk p_max")

# Re-chunk Quran
quran_chunked = []
for surah_unit in quran:
    all_words = " ".join(surah_unit["verses"]).split()
    if len(all_words) < 35:
        continue
    chunked_verses = [
        " ".join(all_words[k:k+7])
        for k in range(0, len(all_words), 7)
    ]
    if len(chunked_verses) < 5:
        continue
    quran_chunked.append({
        "corpus": "quran_chunked",
        "label": surah_unit["label"] + ":7w",
        "verses": chunked_verses,
        "normaliser": "arabic",
    })

quran_chunked_feats = []
for u in quran_chunked:
    try:
        quran_chunked_feats.append(_features_universal(u))
    except Exception:
        pass
qc_pmax = statistics.median(f["p_max"] for f in quran_chunked_feats)
qc_hel = statistics.median(f["H_EL"] for f in quran_chunked_feats)

# Poetry 7-word chunks (current locked F63 unit)
poetry_islami = arabic.get("poetry_islami", [])
pi_feats = []
for u in poetry_islami:
    try:
        pi_feats.append(_features_universal(u))
    except Exception:
        pass
pi_pmax = statistics.median(f["p_max"] for f in pi_feats)
pi_hel = statistics.median(f["H_EL"] for f in pi_feats)

print(f"#   Quran natural-ayat (F63 unit)      : p_max = {qpmax:.4f}, H_EL = {qhel:.4f}")
print(f"#   Quran re-chunked into 7-word blocks: p_max = {qc_pmax:.4f}, H_EL = {qc_hel:.4f}")
print(f"#   poetry_islami 7-word blocks (F63)  : p_max = {pi_pmax:.4f}, H_EL = {pi_hel:.4f}")
print()
if qc_pmax > pi_pmax * 1.2:
    print(f"# R2 verdict: ROBUST — even when Quran is forcibly chunked the SAME WAY")
    print(f"#                       as poetry, its p_max ({qc_pmax:.4f}) is still")
    print(f"#                       {qc_pmax/pi_pmax:.2f}x poetry's ({pi_pmax:.4f}).")
    print(f"#                       The Quran's rhyme-extremum is NOT a unit artefact.")
else:
    print(f"# R2 verdict: WEAK — Quran chunked-p_max only {qc_pmax/pi_pmax:.2f}x poetry's.")
    print(f"#                    Most of F63's apparent advantage came from real-verse-")
    print(f"#                    boundaries vs synthetic chunking. Need to re-do.")
print()

# ============================================================
# R3 — Quran vs Arabic Bible head-to-head (within-language clean)
# ============================================================
print("# R3: Quran vs Arabic Bible head-to-head (same language, both real-verse)")
ab_meds = real_meds["arabic_bible"]
print(f"#   Quran        : p_max = {qpmax:.4f}, H_EL = {qhel:.4f}  (114 surahs, real ayat)")
print(f"#   Arabic Bible : p_max = {ab_meds[0]:.4f}, H_EL = {ab_meds[1]:.4f}  (1183 chapters, real verse)")
print(f"#   p_max ratio (Quran / Arabic Bible)  = {qpmax / ab_meds[0]:.4f}")
print(f"#   H_EL  ratio (Quran / Arabic Bible)  = {qhel / ab_meds[1]:.4f}")
r3_pass = (qpmax / ab_meds[0] > 2.0) and (qhel / ab_meds[1] < 0.5)
print(f"# R3 verdict: {'STRONG — within-language religious-prose comparison cleanly' if r3_pass else 'weak — within-language gap less than expected'}")
print(f"#                     {'shows Quran 2x+ more rhyme-concentrated than Arabic Bible.' if r3_pass else 'check why.'}")
print()

# Save audit report
out = {
    "audit": "f63_robustness",
    "R1_real_verse_only": {
        "corpora_used": list(real_corpora.keys()),
        "medians": {n: {"p_max": float(p), "H_EL": float(h)}
                    for n, (p, h) in real_meds.items()},
        "quran_p_max_ratio_to_next_highest": float(qpmax / others_pmax),
        "quran_h_el_ratio_to_next_lowest":   float(qhel / others_hel),
        "next_highest_corpus":
            max(real_meds.items(), key=lambda kv: kv[1][0] if kv[0] != "quran" else 0)[0],
        "next_lowest_corpus":
            min(real_meds.items(), key=lambda kv: kv[1][1] if kv[0] != "quran" else 999)[0],
        "verdict_pass": bool(r1_pass),
    },
    "R2_quran_rechunked_7word": {
        "quran_natural_p_max": float(qpmax),
        "quran_chunked_p_max": float(qc_pmax),
        "quran_chunked_h_el":  float(qc_hel),
        "poetry_islami_p_max": float(pi_pmax),
        "poetry_islami_h_el":  float(pi_hel),
        "ratio_quran_chunked_to_poetry": float(qc_pmax / pi_pmax),
    },
    "R3_quran_vs_arabic_bible": {
        "quran":  {"p_max": float(qpmax), "H_EL": float(qhel)},
        "arabic_bible": {"p_max": float(ab_meds[0]), "H_EL": float(ab_meds[1])},
        "p_max_ratio": float(qpmax / ab_meds[0]),
        "h_el_ratio":  float(qhel / ab_meds[1]),
        "verdict_pass": bool(r3_pass),
    },
}
out_path = ROOT / "results" / "auxiliary" / "_f63_robustness.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                    encoding="utf-8")
print(f"# receipt: {out_path}")
