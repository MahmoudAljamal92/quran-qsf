"""
exp23_adiyat_MC/run.py
======================
Monte-Carlo over ALL single-letter substitutions in verse 1 of Adiyat
(Q:100). For each (position, consonant) pair, construct a variant,
recompute the 5-D features for the full surah (only verse 1 changes),
compute Phi_M, and report the percentile of the canonical reading.

Motivation: external review (2026-04-20) flagged that the three hand-
picked alternatives in docs/ADIYAT_ANALYSIS_AR.md (al-adiyat ->
al-ghadiyat / al-badiyat / al-hadiyat) are vulnerable to the
"cherry-picked three" critique. This experiment enumerates every
single-letter variant of verse 1 and asks whether the canonical sits
at the extreme of the full distribution.

v0 scaffold (2026-04-20): substitution policy is **purely positional**
-- every consonant replaced by every other Arabic consonant -- and
therefore includes many linguistically invalid forms. A v1 follow-up
should gate variants by a roots whitelist (CamelTools) or a CharLM
score threshold. See notes.md for the v1 plan.

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (CORPORA, mu, S_inv, FEAT_COLS)

Writes ONLY under results/experiments/exp23_adiyat_MC/:
  - exp23_adiyat_MC.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import features as ft  # noqa: E402

EXP = "exp23_adiyat_MC"

ARABIC_CONS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
ADIYAT_LABEL = "Q:100"


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu = np.asarray(state["mu"], dtype=float)
    Sinv = np.asarray(state["S_inv"], dtype=float)

    adiyat = None
    for u in CORPORA.get("quran", []):
        if u.label == ADIYAT_LABEL:
            adiyat = u
            break
    if adiyat is None:
        raise RuntimeError(
            f"surah {ADIYAT_LABEL} not found in CORPORA['quran']"
        )

    f_canon = ft.features_5d(adiyat.verses)
    phi_canon = float(ft.phi_m(f_canon, mu, Sinv).ravel()[0])

    v1 = adiyat.verses[0]
    variants = []
    for pos, ch in enumerate(v1):
        if ch not in ARABIC_CONS:
            continue
        for repl in ARABIC_CONS:
            if repl == ch:
                continue
            new_v1 = v1[:pos] + repl + v1[pos + 1:]
            new_verses = [new_v1] + list(adiyat.verses[1:])
            try:
                f_var = ft.features_5d(new_verses)
                phi_var = float(ft.phi_m(f_var, mu, Sinv).ravel()[0])
            except Exception:
                continue
            variants.append({
                "pos": pos,
                "orig": ch,
                "repl": repl,
                "phi_m": phi_var,
                "verse1": new_v1,
            })

    phis = np.asarray([v["phi_m"] for v in variants], dtype=float)
    if len(phis):
        pct_canon_below = float(np.mean(phis <= phi_canon) * 100.0)
        pct_canon_above = float(np.mean(phis >= phi_canon) * 100.0)
    else:
        pct_canon_below = float("nan")
        pct_canon_above = float("nan")

    report = {
        "experiment": EXP,
        "adiyat_label": ADIYAT_LABEL,
        "canonical_verse1": v1,
        "canonical_phi_m": phi_canon,
        "canonical_features": dict(zip(
            ["EL", "VL_CV", "CN", "H_cond", "T"], f_canon.tolist()
        )),
        "n_variants": int(len(variants)),
        "variant_phi_m_mean": float(phis.mean()) if len(phis) else None,
        "variant_phi_m_median": float(np.median(phis)) if len(phis) else None,
        "variant_phi_m_max": float(phis.max()) if len(phis) else None,
        "variant_phi_m_min": float(phis.min()) if len(phis) else None,
        "canonical_percentile_below": pct_canon_below,
        "canonical_percentile_above": pct_canon_above,
        "caveat_v0": (
            "purely positional substitution -- does not gate by root validity. "
            "Many variants are linguistically implausible; see notes.md for the "
            "follow-up v1 plan (roots-whitelist or CharLM gate)."
        ),
        "variants_sample": variants[:20],
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(
        f"[{EXP}] {len(variants)} variants; canonical Phi_M = {phi_canon:.3f}; "
        f"canonical percentile below = {pct_canon_below:.2f}%"
    )

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
