"""scripts/_audit_f63_real_verse_only_perm.py
==================================================
Run the F63 permutation null on the cleaner 6-corpus pool: only
real-verse-boundary canonical religious texts (no synthetic chunking).

This is the publishable scope of F63: the Quran is the rhyme-extremum
across cross-tradition CANONICAL RELIGIOUS TEXTS.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

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

SEED = 42
N_PERMUTATIONS = 10000

print("# F63 robustness — 6-corpus real-verse-boundary perm null")
print(f"# seed={SEED}, n_perms={N_PERMUTATIONS}")
print()

print("# loading corpora ...")
quran = _load_quran()
arabic = _load_arabic_peers()
arabic_bible = arabic.get("arabic_bible", [])
hebrew = _load_hebrew_tanakh()
greek = _load_greek_nt()
pali = _load_pali()
avestan = _load_avestan()
print(f"#   quran: {len(quran)}; "
      f"arabic_bible: {len(arabic_bible)}; "
      f"hebrew_tanakh: {len(hebrew)}; "
      f"greek_nt: {len(greek)}; "
      f"pali: {len(pali)}; "
      f"avestan_yasna: {len(avestan)}")

CORPORA = ["quran", "arabic_bible", "hebrew_tanakh", "greek_nt",
           "pali", "avestan_yasna"]
units_by_corpus = {
    "quran": quran,
    "arabic_bible": arabic_bible,
    "hebrew_tanakh": hebrew,
    "greek_nt": greek,
    "pali": pali,
    "avestan_yasna": avestan,
}

print("# extracting universal features ...")
feats = {c: [] for c in CORPORA}
for c in CORPORA:
    for u in units_by_corpus[c]:
        try:
            feats[c].append(_features_universal(u))
        except Exception as e:
            pass
    print(f"#   {c}: {len(feats[c])} units")
print()

# Per-corpus medians
print("# === medians ===")
print(f"# {'corpus':<14s}  {'n':>5s}  {'p_max':>10s}  {'H_EL':>10s}")
medians = {}
for c in CORPORA:
    fs = feats[c]
    pmax = float(np.median([f["p_max"] for f in fs]))
    hel  = float(np.median([f["H_EL"]  for f in fs]))
    medians[c] = (pmax, hel)
    print(f"# {c:<14s}  {len(fs):>5d}  {pmax:>10.4f}  {hel:>10.4f}")
print()

# Decision rule
qpmax, qhel = medians["quran"]
others = [(c, p, h) for c, (p, h) in medians.items() if c != "quran"]
next_p_max_corpus, next_p_max_val, _ = max(others, key=lambda t: t[1])
next_h_el_corpus, _, next_h_el_val = min(others, key=lambda t: t[2])
ratio_p_max = qpmax / next_p_max_val
ratio_h_el  = qhel  / next_h_el_val
print(f"# Quran p_max = {qpmax:.4f}; next-highest = {next_p_max_corpus} = {next_p_max_val:.4f}; ratio = {ratio_p_max:.4f}")
print(f"# Quran H_EL  = {qhel:.4f}; next-lowest  = {next_h_el_corpus} = {next_h_el_val:.4f}; ratio = {ratio_h_el:.4f}")
print()

# Permutation null
print(f"# running {N_PERMUTATIONS}-permutation null on 6-corpus pool ...")
all_pmax = []
all_hel = []
all_origin = []
for c in CORPORA:
    for f in feats[c]:
        all_pmax.append(f["p_max"])
        all_hel.append(f["H_EL"])
        all_origin.append(c)
all_pmax = np.array(all_pmax)
all_hel = np.array(all_hel)
n_total = len(all_origin)
sizes = [len(feats[c]) for c in CORPORA]
quran_idx = CORPORA.index("quran")

H_EL_MARGIN = 0.5
P_MAX_MARGIN = 1.4

rng = np.random.default_rng(SEED)
n_h_passes = 0
n_p_passes = 0
t0 = time.time()
for it in range(N_PERMUTATIONS):
    perm = rng.permutation(n_total)
    offsets = np.cumsum([0] + sizes)
    h_meds = np.empty(len(CORPORA))
    p_meds = np.empty(len(CORPORA))
    for j in range(len(CORPORA)):
        idx = perm[offsets[j]:offsets[j+1]]
        if len(idx) == 0:
            h_meds[j] = np.inf; p_meds[j] = -np.inf
        else:
            h_meds[j] = np.median(all_hel[idx])
            p_meds[j] = np.median(all_pmax[idx])
    fh = h_meds[quran_idx]
    fp = p_meds[quran_idx]
    others_h = np.delete(h_meds, quran_idx)
    others_p = np.delete(p_meds, quran_idx)
    nlh = float(others_h.min())
    nhp = float(others_p.max())
    rh = fh / nlh if nlh > 0 else np.inf
    rp = fp / nhp if nhp > 0 else 0
    if fh < nlh and rh < H_EL_MARGIN:
        n_h_passes += 1
    if fp > nhp and rp > P_MAX_MARGIN:
        n_p_passes += 1
    if (it + 1) % 1000 == 0:
        print(f"#   {it+1}/{N_PERMUTATIONS} ({time.time()-t0:.1f}s); "
              f"H_EL_passes={n_h_passes}, p_max_passes={n_p_passes}")

perm_p_h = n_h_passes / N_PERMUTATIONS
perm_p_p = n_p_passes / N_PERMUTATIONS
PERM_ALPHA_BONF = 0.001 / 2
print(f"# perm_p (H_EL extremum)  = {perm_p_h:.6f}  (need < {PERM_ALPHA_BONF})")
print(f"# perm_p (p_max extremum) = {perm_p_p:.6f}  (need < {PERM_ALPHA_BONF})")
print()

verdict = "PASS_quran_rhyme_extremum_real_verse_only"
if not (qhel < next_h_el_val and ratio_h_el < H_EL_MARGIN
        and qpmax > next_p_max_val and ratio_p_max > P_MAX_MARGIN
        and perm_p_h < PERM_ALPHA_BONF and perm_p_p < PERM_ALPHA_BONF):
    verdict = "FAIL_one_or_more_conditions"
print(f"# 6-corpus verdict: {verdict}")
print(f"# wall-time: {time.time() - t0:.1f}s")

# Save
out = ROOT / "results" / "auxiliary" / "_f63_real_verse_only_perm.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "audit": "f63_real_verse_only_perm",
    "scope": "6 cross-tradition canonical religious texts; real-verse-boundary only",
    "corpora": CORPORA,
    "medians": {c: {"p_max": p, "H_EL": h} for c, (p, h) in medians.items()},
    "n_units_per_corpus": {c: len(feats[c]) for c in CORPORA},
    "quran_p_max": qpmax,
    "quran_h_el": qhel,
    "next_highest_p_max": {"corpus": next_p_max_corpus, "value": next_p_max_val},
    "next_lowest_h_el":   {"corpus": next_h_el_corpus,  "value": next_h_el_val},
    "p_max_ratio": ratio_p_max,
    "h_el_ratio":  ratio_h_el,
    "perm_p_h_el":  perm_p_h,
    "perm_p_p_max": perm_p_p,
    "perm_alpha_bonf": PERM_ALPHA_BONF,
    "verdict": verdict,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"# receipt: {out}")
