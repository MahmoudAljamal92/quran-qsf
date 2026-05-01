"""
tools/qsf_score.py
==================
Stand-alone scoring CLI for an arbitrary Arabic text.

Given a block of Arabic text where each non-blank line is treated as a
"verse", this tool reports:

    EL       end-letter rhyme rate
    VL_CV    verse-length coefficient of variation
    CN       discourse-connective start rate
    H_cond   conditional root-bigram entropy (bits)
    T        structural tension (= H_cond - H_el)
    Phi_M    Mahalanobis distance to the Arabic-control centroid
             from the locked phase_06 checkpoint
    Grade    A+/A/B/C/D at the exp pre-reg cutoffs (6/4/2/1 sigma)

Usage
    python tools/qsf_score.py < path/to/text.txt
    python tools/qsf_score.py --file path/to/text.txt
    echo "verse1`nverse2" | python tools/qsf_score.py --json

Flags
    --file PATH    Read text from PATH (otherwise read stdin).
    --json         Emit a single JSON object instead of human-readable.
    --csv          Emit a single CSV row.
    --verbose      Include intermediate stats and the canonical
                   feature-vector components.

This tool reads but never writes the locked checkpoints, and it does
NOT modify anything under results/ or notebooks/.

See also: tools/qsf_score_app.py (Streamlit UI layer that wraps this).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np

from experiments._lib import load_phase  # noqa: E402
from src import features as ft  # noqa: E402


GRADE_CUTOFFS = [("A+", 6.0), ("A", 4.0), ("B", 2.0), ("C", 1.0)]


def grade(phi_m: float) -> str:
    if not np.isfinite(phi_m):
        return "?"
    for g, cut in GRADE_CUTOFFS:
        if phi_m > cut:
            return g
    return "D"


def score(verses: list[str]) -> dict:
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    mu = np.asarray(state["mu"], dtype=float)
    Sinv = np.asarray(state["S_inv"], dtype=float)

    # Individual features. Uses paper §2.2 default ARABIC_CONN (14-word
    # connective set) -- NOT an empirical derive_stopwords list, which
    # would drift the CN component across inputs.
    stops = ft.ARABIC_CONN
    el = float(ft.el_rate(verses))
    cv = float(ft.vl_cv(verses))
    cn = float(ft.cn_rate(verses, stops))
    hc = float(ft.h_cond_roots(verses))
    he = float(ft.h_el(verses))
    T = hc - he
    feat = np.array([el, cv, cn, hc, T], dtype=float)
    phi_m = float(ft.phi_m(feat, mu, Sinv).ravel()[0])
    g = grade(phi_m)
    return {
        "n_verses": len(verses),
        "EL": el,
        "VL_CV": cv,
        "CN": cn,
        "H_cond": hc,
        "H_el": he,
        "T": T,
        "Phi_M": phi_m,
        "grade": g,
        "grade_cutoffs": dict(GRADE_CUTOFFS),
        "phase_06_mu_head": mu[:3].tolist(),
    }


def _read_verses(source: str) -> list[str]:
    verses = [ln.strip() for ln in source.splitlines() if ln.strip()]
    return verses


def _emit_human(r: dict, verbose: bool) -> str:
    lines = [
        f"n_verses  = {r['n_verses']}",
        f"EL        = {r['EL']:.4f}",
        f"VL_CV     = {r['VL_CV']:.4f}",
        f"CN        = {r['CN']:.4f}",
        f"H_cond    = {r['H_cond']:.4f}",
        f"T         = {r['T']:+.4f}",
        f"Phi_M     = {r['Phi_M']:.3f}",
        f"grade     = {r['grade']}  "
        f"(cutoffs A+ > 6.0, A > 4.0, B > 2.0, C > 1.0, D else)",
    ]
    if verbose:
        lines.append(f"H_el      = {r['H_el']:.4f}")
        lines.append(f"mu head   = {r['phase_06_mu_head']}")
    return "\n".join(lines)


def _emit_csv(r: dict) -> str:
    headers = ["n_verses", "EL", "VL_CV", "CN", "H_cond", "H_el",
               "T", "Phi_M", "grade"]
    row = [str(r["n_verses"])] + [
        f"{r[k]:.6f}" for k in ["EL", "VL_CV", "CN", "H_cond", "H_el",
                                  "T", "Phi_M"]
    ] + [r["grade"]]
    return ",".join(headers) + "\n" + ",".join(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--file", type=str, default="",
                    help="Read text from PATH (else stdin)")
    ap.add_argument("--json", action="store_true",
                    help="Emit a JSON object")
    ap.add_argument("--csv", action="store_true",
                    help="Emit a single CSV row")
    ap.add_argument("--verbose", action="store_true",
                    help="Include intermediate stats")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    verses = _read_verses(text)
    if not verses:
        print("No verses found in input (empty text).", file=sys.stderr)
        return 2

    r = score(verses)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.csv:
        print(_emit_csv(r))
    else:
        print(_emit_human(r, args.verbose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
