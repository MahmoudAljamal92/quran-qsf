"""
exp44_F6_spectrum/run.py
========================
F6 lag-autocorrelation spectrum — extension of exp24_F6_autocorr.

exp24 already confirmed F6 lag-1 d=+0.83 and documented weak lag-2 (d=+0.28),
null lag-4, and a lag-5 rebound (d=+0.27). This experiment extends the
investigation in two directions:

    (a) Lag coverage extended to 1..15 per unit, so rhythmic structure
        beyond the 5-verse horizon is observable.
    (b) AR(p) autoregressive fits per surah. For each unit we fit an
        AR(3) with OLS on the mean-centred verse-length sequence and
        report the three coefficients plus the integrated squared
        autocorrelation (IAC15 = sum_{k=1..15} rho_k^2).

    The claim under test: if F6 is purely a lag-1 phenomenon, lag-k>1
    Cohen d should drop to ~0 and AR(1) should dominate AR(2)/AR(3) in
    BIC. If the Quran has multi-step rhythmic structure, IAC15 should
    separate Q from ctrl and the AR(2)/(3) coefficients should be
    non-zero.

Reads (integrity-checked):
    phase_06_phi_m.pkl   state['CORPORA']

Writes ONLY under results/experiments/exp44_F6_spectrum/:
    exp44_F6_spectrum.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
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

EXP = "exp44_F6_spectrum"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100
LAGS = list(range(1, 16))           # 1..15
AR_P = 3
SEED = 42


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _verse_lengths(verses) -> np.ndarray:
    return np.asarray([len(v.split()) for v in verses], dtype=float)


def _spearman_lag(lens: np.ndarray, k: int) -> float:
    if len(lens) < k + 2:
        return float("nan")
    a = lens[:-k]; b = lens[k:]
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    rho, _ = stats.spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else float("nan")


def _pearson_lag(lens: np.ndarray, k: int) -> float:
    if len(lens) < k + 2:
        return float("nan")
    a = lens[:-k]; b = lens[k:]
    sa, sb = np.std(a, ddof=1), np.std(b, ddof=1)
    if sa < 1e-9 or sb < 1e-9:
        return float("nan")
    r = float(np.corrcoef(a, b)[0, 1])
    return r if math.isfinite(r) else float("nan")


def _iac(lens: np.ndarray, lags: list[int]) -> float:
    """Integrated absolute autocorrelation: sum |rho_k| over given lags."""
    s = 0.0
    valid = 0
    for k in lags:
        r = _pearson_lag(lens, k)
        if math.isfinite(r):
            s += abs(r)
            valid += 1
    return s if valid > 0 else float("nan")


def _iac_sq(lens: np.ndarray, lags: list[int]) -> float:
    """Integrated squared autocorrelation."""
    s = 0.0
    valid = 0
    for k in lags:
        r = _pearson_lag(lens, k)
        if math.isfinite(r):
            s += r * r
            valid += 1
    return s if valid > 0 else float("nan")


def _ar_fit(lens: np.ndarray, p: int = AR_P) -> np.ndarray:
    """OLS fit of AR(p) on mean-centred series.  Returns length-p coefs
    (phi_1..phi_p) or NaNs if the series is too short."""
    n = len(lens)
    if n <= p + 2:
        return np.full(p, np.nan)
    y = lens - lens.mean()
    X = np.column_stack([y[p - k - 1:n - k - 1] for k in range(p)])
    t = y[p:]
    try:
        coefs, *_ = np.linalg.lstsq(X, t, rcond=None)
        return np.asarray(coefs, dtype=float)
    except Exception:
        return np.full(p, np.nan)


def _cohen_d(a, b):
    a = np.asarray([x for x in a if np.isfinite(x)], dtype=float)
    b = np.asarray([x for x in b if np.isfinite(x)], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pool = np.sqrt(
        ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
        / (len(a) + len(b) - 2)
    )
    return float((a.mean() - b.mean()) / pool) if pool > 1e-12 else float("nan")


def _mw(a, b, alt):
    a = [x for x in a if np.isfinite(x)]
    b = [x for x in b if np.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        return float(stats.mannwhitneyu(a, b, alternative=alt).pvalue)
    except ValueError:
        return float("nan")


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = _band_a(CORPORA.get("quran", []))
    ctrl_units = []
    for name in ARABIC_CTRL:
        ctrl_units.extend(_band_a(CORPORA.get(name, [])))

    def _collect(units):
        rows = []
        for u in units:
            lens = _verse_lengths(u.verses)
            if len(lens) < max(LAGS) + 3:
                continue
            acf = {f"lag_{k}_pearson": _pearson_lag(lens, k) for k in LAGS}
            acf_s = {f"lag_{k}_spearman": _spearman_lag(lens, k) for k in LAGS}
            ar = _ar_fit(lens, AR_P)
            rows.append({
                "label": getattr(u, "label", ""),
                "n_verses": len(lens),
                **acf, **acf_s,
                "ar1": float(ar[0]) if ar.size > 0 else float("nan"),
                "ar2": float(ar[1]) if ar.size > 1 else float("nan"),
                "ar3": float(ar[2]) if ar.size > 2 else float("nan"),
                "iac_abs_15": _iac(lens, LAGS),
                "iac_sq_15": _iac_sq(lens, LAGS),
            })
        return rows

    q_rows = _collect(q_units)
    c_rows = _collect(ctrl_units)

    # Aggregate per-lag statistics
    per_lag: dict = {}
    for k in LAGS:
        qp = [r[f"lag_{k}_pearson"] for r in q_rows]
        cp = [r[f"lag_{k}_pearson"] for r in c_rows]
        qs = [r[f"lag_{k}_spearman"] for r in q_rows]
        cs = [r[f"lag_{k}_spearman"] for r in c_rows]
        per_lag[f"lag_{k}"] = {
            "pearson_q_median": float(np.nanmedian(qp)) if qp else float("nan"),
            "pearson_c_median": float(np.nanmedian(cp)) if cp else float("nan"),
            "pearson_cohen_d": _cohen_d(qp, cp),
            "pearson_mw_p_greater": _mw(qp, cp, "greater"),
            "spearman_q_median": float(np.nanmedian(qs)) if qs else float("nan"),
            "spearman_c_median": float(np.nanmedian(cs)) if cs else float("nan"),
            "spearman_cohen_d": _cohen_d(qs, cs),
            "spearman_mw_p_greater": _mw(qs, cs, "greater"),
        }

    # AR coefficient distributions -- audit-fix M-4: compute both
    # one-sided p values and a two-sided p explicitly; no more NaN stub.
    ar_summary = {}
    for key in ("ar1", "ar2", "ar3"):
        qv = [r[key] for r in q_rows]
        cv = [r[key] for r in c_rows]
        ar_summary[key] = {
            "q_median": float(np.nanmedian(qv)) if qv else float("nan"),
            "c_median": float(np.nanmedian(cv)) if cv else float("nan"),
            "cohen_d": _cohen_d(qv, cv),
            "mw_p_greater": _mw(qv, cv, "greater"),
            "mw_p_less": _mw(qv, cv, "less"),
            "mw_p_two_sided": _mw(qv, cv, "two-sided"),
        }

    # IAC summaries -- audit-fix M-4: p_less reported so the
    # "punchy not wide" direction claim is substantiated rather than
    # implied from a single-direction p.
    q_iac = [r["iac_abs_15"] for r in q_rows]
    c_iac = [r["iac_abs_15"] for r in c_rows]
    q_iacq = [r["iac_sq_15"] for r in q_rows]
    c_iacq = [r["iac_sq_15"] for r in c_rows]
    iac_summary = {
        "iac_abs_15": {
            "q_median": float(np.nanmedian(q_iac)) if q_iac else float("nan"),
            "c_median": float(np.nanmedian(c_iac)) if c_iac else float("nan"),
            "cohen_d": _cohen_d(q_iac, c_iac),
            "mw_p_greater": _mw(q_iac, c_iac, "greater"),
            "mw_p_less": _mw(q_iac, c_iac, "less"),
            "mw_p_two_sided": _mw(q_iac, c_iac, "two-sided"),
        },
        "iac_sq_15": {
            "q_median": float(np.nanmedian(q_iacq)) if q_iacq else float("nan"),
            "c_median": float(np.nanmedian(c_iacq)) if c_iacq else float("nan"),
            "cohen_d": _cohen_d(q_iacq, c_iacq),
            "mw_p_greater": _mw(q_iacq, c_iacq, "greater"),
            "mw_p_less": _mw(q_iacq, c_iacq, "less"),
            "mw_p_two_sided": _mw(q_iacq, c_iacq, "two-sided"),
        },
    }

    # Best lag beyond lag-1
    best_beyond_lag1 = max(
        ((k, abs(per_lag[f"lag_{k}"]["pearson_cohen_d"]))
         for k in LAGS if k > 1
         and math.isfinite(per_lag[f"lag_{k}"]["pearson_cohen_d"])),
        key=lambda x: x[1],
        default=(None, 0.0),
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "lags": LAGS,
        "ar_order": AR_P,
        "n_quran_units": len(q_rows),
        "n_ctrl_units": len(c_rows),
        "per_lag_stats": per_lag,
        "ar_summary": ar_summary,
        "iac_summary": iac_summary,
        "best_pearson_d_beyond_lag1": {
            "lag": best_beyond_lag1[0],
            "abs_cohen_d": float(best_beyond_lag1[1]),
        },
        "notes": (
            "Extension of exp24 from lags 1..5 to 1..15, with AR(3) OLS "
            "fit per surah and integrated squared autocorrelation. Cohen "
            "d thresholds: d>=0.5 strong, 0.3<=d<0.5 moderate, d<0.3 weak."
        ),
        "per_unit_sample": {
            "quran": q_rows[:5],
            "ctrl": c_rows[:5],
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------- console ---------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] n_q={len(q_rows)} n_ctrl={len(c_rows)}")
    print(f"[{EXP}] Pearson lag-k Cohen d:")
    for k in LAGS:
        pl = per_lag[f"lag_{k}"]
        d = pl["pearson_cohen_d"]
        pg = pl["pearson_mw_p_greater"]
        marker = " ***" if math.isfinite(d) and abs(d) >= 0.5 else (
                 " **"  if math.isfinite(d) and abs(d) >= 0.3 else "")
        print(f"   lag {k:2d}  d = {d:+.3f}  MW p_g = {pg:.3e}{marker}")
    print(f"[{EXP}] AR(3) coefs Cohen d:")
    for key in ("ar1", "ar2", "ar3"):
        a = ar_summary[key]
        print(f"   {key}  Q med = {a['q_median']:+.3f}  "
              f"C med = {a['c_median']:+.3f}  d = {a['cohen_d']:+.3f}  "
              f"MW p_g = {a['mw_p_greater']:.3e}")
    for key, lab in [("iac_abs_15", "IAC |rho|"), ("iac_sq_15", "IAC rho^2")]:
        a = iac_summary[key]
        print(f"[{EXP}] {lab:10s}  Q med = {a['q_median']:.4f}  "
              f"C med = {a['c_median']:.4f}  d = {a['cohen_d']:+.3f}  "
              f"MW p_g = {a['mw_p_greater']:.3e}")
    bl, bd = best_beyond_lag1
    print(f"[{EXP}] Best Cohen d beyond lag-1: lag={bl}  |d|={bd:.3f}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
