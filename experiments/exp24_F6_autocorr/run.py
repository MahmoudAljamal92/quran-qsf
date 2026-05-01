"""
exp24_F6_autocorr/run.py
========================
F6 extension: the locked F6 finding (Cohen d = +0.877, p = 1.4e-11 for
adjacent-verse word-count correlation in Quran vs Arabic controls) is
lag-1 only. This experiment extends F6 to lag-k for k in {1,2,3,4,5}
and asks whether the Quran's local length coherence is a one-step
phenomenon or a multi-step autocorrelation.

If lag-2 and lag-3 retain d > 0.5, the Quran has a multi-verse rhythmic
structure beyond adjacent pairs, which unifies F6 with T12
(bigram-sufficiency).

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (CORPORA)

Writes ONLY under results/experiments/exp24_F6_autocorr/:
  - exp24_F6_autocorr.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

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

EXP = "exp24_F6_autocorr"

ARABIC_FAMILY = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100  # matches notebooks/ultimate/_build.py:1129
LAGS = [1, 2, 3, 4, 5]


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _spearman_lag(lens: np.ndarray, k: int) -> float:
    if len(lens) < k + 2:
        return float("nan")
    a = lens[:-k]
    b = lens[k:]
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    rho, _ = stats.spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else float("nan")


def _cohen_d(a, b):
    a = np.asarray([x for x in a if not np.isnan(x)], dtype=float)
    b = np.asarray([x for x in b if not np.isnan(x)], dtype=float)
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

    per_corpus = {}
    for c in ARABIC_FAMILY:
        units = _band_a(CORPORA.get(c, []))
        per_lag = {k: [] for k in LAGS}
        for u in units:
            lens = np.asarray(
                [len(v.split()) for v in u.verses], dtype=float
            )
            for k in LAGS:
                per_lag[k].append(_spearman_lag(lens, k))
        entry = {"n": int(len(units))}
        for k in LAGS:
            vals = per_lag[k]
            clean = [x for x in vals if not np.isnan(x)]
            entry[f"lag{k}_mean"] = float(np.mean(clean)) if clean else None
            entry[f"lag{k}_median"] = (
                float(np.median(clean)) if clean else None
            )
            entry[f"lag{k}_values"] = [float(x) for x in vals]
        per_corpus[c] = entry

    summary = {}
    for k in LAGS:
        q_vals = per_corpus.get("quran", {}).get(f"lag{k}_values", [])
        ctrl_vals = []
        for c in ARABIC_FAMILY:
            if c == "quran":
                continue
            ctrl_vals.extend(
                per_corpus.get(c, {}).get(f"lag{k}_values", [])
            )
        q_clean = [x for x in q_vals if not np.isnan(x)]
        c_clean = [x for x in ctrl_vals if not np.isnan(x)]
        if q_clean and c_clean:
            mw = stats.mannwhitneyu(q_clean, c_clean, alternative="greater")
            p_one = float(mw.pvalue)
        else:
            p_one = None
        summary[f"lag{k}"] = {
            "cohen_d_quran_vs_ctrl": _cohen_d(q_vals, ctrl_vals),
            "mannwhitney_p_one_sided": p_one,
            "n_quran": int(len(q_clean)),
            "n_ctrl": int(len(c_clean)),
        }

    report = {
        "experiment": EXP,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "lags": LAGS,
        "per_corpus": per_corpus,
        "summary_lag_d": summary,
        "locked_F6_lag1_d_reference": 0.877,
        "note": (
            "F6 extension to lag-k. Lag-1 should reproduce the locked "
            "d ~ 0.877 within sampling noise; lag-2/3 are new. If "
            "lag-2 d > 0.5 the Quran's local length coherence is multi-step, "
            "which unifies with T12 bigram sufficiency (Markov-2 structure "
            "is already sufficient)."
        ),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[{EXP}] Cohen d per lag (Quran vs Arabic ctrl):")
    for k in LAGS:
        row = summary[f"lag{k}"]
        d = row["cohen_d_quran_vs_ctrl"]
        p = row["mannwhitney_p_one_sided"]
        if p is None:
            print(f"  lag={k}  d={d:+.3f}  p=N/A")
        else:
            print(f"  lag={k}  d={d:+.3f}  p={p:.2e}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
