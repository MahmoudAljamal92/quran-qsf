"""
exp21_E1_EL_survival/run.py
===========================
Reframe of the E1 transmission-noise simulation: the paper currently
reports `P_e` (per-token substitution rate) in notebooks/ultimate/
QSF_ULTIMATE.ipynb Cell 103 -- a tautology of the noise model. External
review (2026-04-20) recommends measuring **EL-rate survival** instead:
after per-token noise at eps, what fraction of Band-A surahs retain
EL >= median(EL_before)?

Hypothesis: Quran EL survives better than Arabic control EL under equal
eps, i.e. Cohen d(EL_after_Quran, EL_after_ctrl) stays positive as eps
grows. If true, this closes the honesty-gap between Cell 103's numeric
output (just reprinting eps) and the Quran-robustness narrative.

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (CORPORA only)

Writes ONLY under results/experiments/exp21_E1_EL_survival/:
  - exp21_E1_EL_survival.json
  - self_check_<ts>.json
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
from src.raw_loader import Unit  # noqa: E402

EXP = "exp21_E1_EL_survival"

ARABIC_FAMILY = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100  # matches notebooks/ultimate/_build.py:1129
EPS_GRID = [0.01, 0.02, 0.05, 0.10]
ARABIC_CONS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
SEED = 42


def _noise_unit(u: Unit, eps: float, rng: np.random.Generator) -> Unit:
    new_verses = []
    for v in u.verses:
        toks = v.split()
        for i, tok in enumerate(toks):
            if len(tok) > 0 and rng.random() < eps:
                pos = int(rng.integers(0, len(tok)))
                letter = ARABIC_CONS[int(rng.integers(0, len(ARABIC_CONS)))]
                toks[i] = tok[:pos] + letter + tok[pos + 1:]
        new_verses.append(" ".join(toks))
    return Unit(corpus=u.corpus, label=u.label, verses=new_verses)


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _cohen_d(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pool = np.sqrt(
        ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
        / (len(a) + len(b) - 2)
    )
    return float((a.mean() - b.mean()) / pool) if pool > 1e-12 else float("nan")


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    rng = np.random.default_rng(SEED)

    per_corpus_baseline = {}
    per_corpus_survival = {}
    for c in ARABIC_FAMILY:
        units = _band_a(CORPORA.get(c, []))
        if not units:
            continue
        EL_before = np.asarray([ft.el_rate(u.verses) for u in units])
        per_corpus_baseline[c] = {
            "n": int(len(EL_before)),
            "EL_mean": float(EL_before.mean()),
            "EL_median": float(np.median(EL_before)),
        }
        survival = {}
        for eps in EPS_GRID:
            EL_after = np.asarray(
                [ft.el_rate(_noise_unit(u, eps, rng).verses) for u in units]
            )
            med = float(np.median(EL_before))
            retained = float(np.mean(EL_after >= med))
            survival[f"eps={eps:.2f}"] = {
                "EL_after_mean": float(EL_after.mean()),
                "EL_after_median": float(np.median(EL_after)),
                "frac_retained_ge_median_before": retained,
                "EL_after_values": EL_after.tolist(),
            }
        per_corpus_survival[c] = survival

    # Pairwise Cohen d (Quran vs pooled Arabic ctrl) at each eps
    eps_d = {}
    for eps in EPS_GRID:
        key = f"eps={eps:.2f}"
        q_vals = per_corpus_survival.get("quran", {}).get(key, {}).get(
            "EL_after_values", []
        )
        ctrl_vals = []
        for c in ARABIC_FAMILY:
            if c == "quran":
                continue
            ctrl_vals.extend(
                per_corpus_survival.get(c, {}).get(key, {}).get(
                    "EL_after_values", []
                )
            )
        eps_d[key] = {
            "cohen_d_quran_vs_ctrl": _cohen_d(q_vals, ctrl_vals),
            "n_quran": len(q_vals),
            "n_ctrl": len(ctrl_vals),
        }

    report = {
        "experiment": EXP,
        "seed": SEED,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "eps_grid": EPS_GRID,
        "per_corpus_baseline": per_corpus_baseline,
        "per_corpus_survival": per_corpus_survival,
        "eps_d_quran_vs_ctrl": eps_d,
        "note": (
            "EL-rate survival reframe of E1. Replaces Cell 103's tautological "
            "P_e with an information-preserving metric (end-letter rhyme "
            "survival after noise). Matches noise model in Cell 97 "
            "(per-token single-letter substitution). Hadith is quarantined "
            "per preregistration.json honest_adjustments_2026_04_18."
        ),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[{EXP}] wrote {out / (EXP + '.json')}")
    for k, v in eps_d.items():
        print(
            f"  {k}   d(Q vs ctrl) = {v['cohen_d_quran_vs_ctrl']:+.3f}   "
            f"(n_q={v['n_quran']}, n_c={v['n_ctrl']})"
        )

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
