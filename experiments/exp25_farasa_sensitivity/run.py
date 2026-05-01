"""
exp25_farasa_sensitivity/run.py
===============================
Root-extractor sensitivity: re-compute H_cond under an alternative root
analyser (Farasa) and compare to the CamelTools-based locked H_cond.

Motivation: external review (2026-04-20) flagged that CamelTools'
Arabic root analysis has a documented ~63 % precision ceiling on modern
gold sets; any law built on H_cond (including Phi_M directly, since
H_cond is feature #4) inherits that ceiling. If |delta T^2| < 5 % when
roots come from a different analyser, the robustness claim is
supported; if > 15 %, the H_cond channel is analyser-dependent and must
be flagged.

Current status: SKELETON. Farasa requires a manual install
(https://farasa.qcri.org/ or `pip install farasapy`). This script fails
CLOSED with an actionable message if Farasa is not available. Once
installed, implement `_root_via_farasa()` below and re-run.

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (CORPORA, mu, S_inv, FEAT_COLS)

Writes ONLY under results/experiments/exp25_farasa_sensitivity/:
  - exp25_farasa_sensitivity.json
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp25_farasa_sensitivity"


def _farasa_available() -> bool:
    """Return True only if (a) java is on PATH AND (b) a Farasa Python
    wrapper is importable. Returning False makes the script fail CLOSED
    with an actionable install message."""
    if shutil.which("java") is None:
        return False
    try:
        import farasa  # type: ignore   # noqa: F401
        return True
    except Exception:
        return False


def _root_via_farasa(word: str) -> str:
    """TODO: wire to your Farasa wrapper. Must return the consonantal
    root in the same convention as
    `src.arabic_roots.primary_root_normalized` (triliteral, no weak
    radical marker)."""
    raise NotImplementedError(
        "Farasa wrapper not wired. Edit exp25_farasa_sensitivity/run.py: "
        "_root_via_farasa() to return a consonantal root from Farasa, "
        "then update _farasa_available() to actually return True."
    )


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    if not _farasa_available():
        report = {
            "experiment": EXP,
            "status": "NOT_INSTALLED",
            "message": (
                "Farasa not available on this system. Install it from "
                "https://farasa.qcri.org/ (Java 8+ required), or install a "
                "Python wrapper (`pip install farasapy`). Then edit "
                "_root_via_farasa() in this file to return a consonantal "
                "root, and re-run. Skeleton preserves the self-check "
                "receipt so the sandbox stays consistent."
            ),
            "next_steps": [
                "1. Install Java 8+ and Farasa, OR `pip install farasapy`.",
                "2. Implement _root_via_farasa(word) to return a "
                "consonantal root string.",
                "3. Re-run: python -m experiments.exp25_farasa_sensitivity.run",
                "4. Expected output: |delta T^2 (Farasa vs CamelTools)| per "
                "corpus, plus pairwise H_cond correlation across the Arabic "
                "family.",
            ],
        }
        with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] status = NOT_INSTALLED -- see {out / (EXP + '.json')}")
        self_check_end(pre, EXP)
        return 0

    # --- Farasa is available: scientific implementation to be filled in ---
    #
    # Sketch (once _root_via_farasa is wired):
    #
    #   import numpy as np
    #   from experiments._lib import load_phase
    #   from src import features as ft
    #
    #   phi = load_phase("phase_06_phi_m")
    #   state = phi["state"]
    #   CORPORA = state["CORPORA"]
    #   mu = np.asarray(state["mu"], dtype=float)
    #   Sinv = np.asarray(state["S_inv"], dtype=float)
    #
    #   per_corpus = {}
    #   for c, units in CORPORA.items():
    #       hc_camel, hc_farasa = [], []
    #       for u in units:
    #           # Replace CamelTools-based H_cond with a Farasa-based one
    #           # at the verse-final-token level, recompute features_5d.
    #           ...
    #       per_corpus[c] = {
    #           "n": len(units),
    #           "pearson_r_H_cond": ...,
    #           "delta_T2": ...,
    #       }
    #
    #   with open(out / f"{EXP}.json", "w") as f:
    #       json.dump({"per_corpus": per_corpus, ...}, f, indent=2)

    raise NotImplementedError(
        "Farasa is available but the scientific implementation block is "
        "still TODO. See the docstring for the required computation."
    )


if __name__ == "__main__":
    sys.exit(main())
