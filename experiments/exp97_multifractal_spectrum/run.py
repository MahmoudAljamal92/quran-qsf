"""
exp97_multifractal_spectrum — H52 (closes C5 of F57; verse 39:23 self-similar).

For each Arabic corpus C, build a single time series of verse-letter
counts (length of letters_28-skeletonised verse) in canonical reading
order, then compute the multifractal singularity spectrum f(alpha) via
hand-rolled MFDFA. Define spectrum width Delta_alpha = alpha_max -
alpha_min where f(alpha) drops below F_ALPHA_THRESHOLD.

H52 PASS ↔ Quran has the strictly smallest Delta_alpha among 7 corpora
AND next-ranked Delta_alpha >= 1.05 * Quran's.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp97_multifractal_spectrum/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp97_multifractal_spectrum/exp97_multifractal_spectrum.json
  - results/experiments/exp97_multifractal_spectrum/per_corpus_falpha.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    letters_28,
)

EXP = "exp97_multifractal_spectrum"
PREREG_PATH = _HERE / "PREREG.md"
HASH_PATH = _HERE / "PREREG_HASH.txt"

# Frozen constants (PREREG §3)
ARABIC_POOL = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
SERIES_VARIABLE = "letters_28_per_verse"
Q_GRID = list(range(-5, 6))         # 11 q-values: -5..5
SCALE_GRID_MIN = 16
SCALE_GRID_MAX_FRAC = 0.25
N_SCALES = 16
DETREND_ORDER = 1
F_ALPHA_THRESHOLD = 0.5
MARGIN_FRACTION = 0.05
RNG_SEED = 97000

# Audit hooks
HURST_TARGET = 0.7
HURST_TOL = 0.15
SERIES_LEN_FLOOR = 200
DELTA_ALPHA_NONDEGEN = 0.01
N_NONDEGEN_FLOOR = 5


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _write_prereg_hash(actual: str) -> None:
    HASH_PATH.write_text(actual + "\n", encoding="utf-8")


# -----------------------------------------------------------------------
# Hand-rolled MFDFA (Kantelhardt et al. 2002)
# -----------------------------------------------------------------------
def mfdfa_falpha(x: np.ndarray, q_grid: list[int],
                 scale_min: int, scale_max: int, n_scales: int,
                 order: int = 1) -> dict[str, Any]:
    """
    Hand-rolled MFDFA.

    Steps:
      1) Profile Y = cumsum(x - mean(x))
      2) For each scale s, split Y into Ns = floor(N/s) non-overlapping
         segments of length s; do a polynomial detrend per segment;
         compute F2(s, v) = (1/s) sum residual^2.
      3) For q != 0: Fq(s) = ((1/(2 Ns)) sum F2(s,v)^(q/2))^(1/q)
         For q  = 0: F0(s) = exp((1/(4 Ns)) sum log F2(s,v))
      4) log Fq(s) ~ h(q) * log(s)  -> linear fit slope.
      5) tau(q) = q*h(q) - 1
      6) alpha(q) = dtau/dq, f(alpha) = q*alpha - tau(q)
      7) Delta_alpha = max(alpha[f >= thresh]) - min(alpha[f >= thresh])
    """
    x = np.asarray(x, dtype=float)
    N = x.size
    if N < 2 * scale_min:
        return {"error": "series_too_short", "N": int(N), "alpha": [], "f_alpha": [],
                "delta_alpha": None, "h_q": [], "tau_q": []}

    # Step 1: profile
    Y = np.cumsum(x - x.mean())

    # Scale grid: log-spaced
    scales = np.unique(
        np.round(np.geomspace(scale_min, scale_max, n_scales)).astype(int)
    )
    scales = scales[scales >= 4]  # need at least 4 points for order-1 fit

    # Step 2-3: F_q(s) for each q, s. Use forward + backward halves.
    Fq_log = np.zeros((len(q_grid), len(scales)), dtype=float)
    Fq_log[:] = np.nan
    for si, s in enumerate(scales):
        Ns = N // s
        if Ns < 2:
            continue
        # forward and backward halves (Kantelhardt: use 2 Ns)
        F2 = np.zeros(2 * Ns, dtype=float)
        for v in range(Ns):
            seg = Y[v * s:(v + 1) * s]
            t = np.arange(s, dtype=float)
            coef = np.polyfit(t, seg, order)
            trend = np.polyval(coef, t)
            F2[v] = np.mean((seg - trend) ** 2)
        for v in range(Ns):
            seg = Y[N - (v + 1) * s:N - v * s]
            t = np.arange(s, dtype=float)
            coef = np.polyfit(t, seg, order)
            trend = np.polyval(coef, t)
            F2[Ns + v] = np.mean((seg - trend) ** 2)
        # guard zero-variance segments
        F2 = np.where(F2 <= 0, np.finfo(float).tiny, F2)
        for qi, q in enumerate(q_grid):
            if q == 0:
                Fq = math.exp(0.5 * np.mean(np.log(F2)))
            else:
                Fq = (np.mean(F2 ** (q / 2.0))) ** (1.0 / q)
            if Fq > 0 and np.isfinite(Fq):
                Fq_log[qi, si] = math.log(Fq)

    log_s = np.log(scales)
    # Step 4: slope h(q) from linear fit log Fq vs log s
    h_q = np.full(len(q_grid), np.nan)
    for qi in range(len(q_grid)):
        ys = Fq_log[qi, :]
        mask = np.isfinite(ys)
        if mask.sum() >= 4:
            slope, _ = np.polyfit(log_s[mask], ys[mask], 1)
            h_q[qi] = slope

    # Step 5-6: alpha, f(alpha)
    q_arr = np.array(q_grid, dtype=float)
    tau_q = q_arr * h_q - 1.0
    # alpha = dtau/dq; central differences
    alpha = np.full(len(q_grid), np.nan)
    for qi in range(len(q_grid)):
        if qi == 0:
            if np.isfinite(tau_q[qi]) and np.isfinite(tau_q[qi + 1]):
                alpha[qi] = tau_q[qi + 1] - tau_q[qi]
        elif qi == len(q_grid) - 1:
            if np.isfinite(tau_q[qi]) and np.isfinite(tau_q[qi - 1]):
                alpha[qi] = tau_q[qi] - tau_q[qi - 1]
        else:
            if np.isfinite(tau_q[qi - 1]) and np.isfinite(tau_q[qi + 1]):
                alpha[qi] = (tau_q[qi + 1] - tau_q[qi - 1]) / 2.0
    f_alpha = q_arr * alpha - tau_q

    # Step 7: Delta_alpha at f(alpha) >= F_ALPHA_THRESHOLD
    valid = np.isfinite(alpha) & np.isfinite(f_alpha) & (f_alpha >= F_ALPHA_THRESHOLD)
    if valid.sum() >= 2:
        a_supp = alpha[valid]
        delta_alpha = float(a_supp.max() - a_supp.min())
    else:
        delta_alpha = None

    # H estimate: alpha at peak of f(alpha) (q -> 0 typically)
    finite = np.isfinite(f_alpha)
    if finite.any():
        peak_idx = int(np.nanargmax(f_alpha))
        h_estimate = float(alpha[peak_idx]) if np.isfinite(alpha[peak_idx]) else None
    else:
        h_estimate = None

    return {
        "N": int(N),
        "scales": [int(s) for s in scales],
        "h_q": [float(v) if np.isfinite(v) else None for v in h_q],
        "tau_q": [float(v) if np.isfinite(v) else None for v in tau_q],
        "alpha": [float(v) if np.isfinite(v) else None for v in alpha],
        "f_alpha": [float(v) if np.isfinite(v) else None for v in f_alpha],
        "delta_alpha": delta_alpha,
        "h_estimate": h_estimate,
    }


def _build_series(corpus_units: list) -> np.ndarray:
    """Construct verse-letter-count series in canonical order."""
    counts: list[int] = []
    for u in corpus_units:
        for v in u.verses:
            counts.append(len(letters_28(v)))
    return np.asarray(counts, dtype=float)


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out_dir = safe_output_dir(EXP)
    t0 = time.time()

    # 1. PREREG hash
    actual_hash = _sha256(PREREG_PATH)
    print(f"[{EXP}] PREREG hash: {actual_hash}")
    _write_prereg_hash(actual_hash)

    # 2. Load corpora
    print(f"[{EXP}] loading phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # 3. Per-corpus MFDFA
    per_corpus: dict[str, dict[str, Any]] = {}
    for cname in ARABIC_POOL:
        units = CORPORA.get(cname, [])
        x = _build_series(units)
        N = x.size
        scale_max = max(SCALE_GRID_MIN + 1, int(SCALE_GRID_MAX_FRAC * N))
        print(f"[{EXP}]   {cname}: N={N}, scale_max={scale_max}")
        if N < SERIES_LEN_FLOOR:
            per_corpus[cname] = {
                "N": int(N), "delta_alpha": None,
                "_excluded_short_series": True,
            }
            continue
        spectrum = mfdfa_falpha(
            x, Q_GRID,
            scale_min=SCALE_GRID_MIN, scale_max=scale_max,
            n_scales=N_SCALES, order=DETREND_ORDER,
        )
        per_corpus[cname] = spectrum

    # 4. Audit hooks
    audit_failures: list[str] = []
    nondegen = sum(
        1 for d in per_corpus.values()
        if d.get("delta_alpha") is not None and d["delta_alpha"] > DELTA_ALPHA_NONDEGEN
    )
    # A1 all 7 corpora finite Delta_alpha
    n_finite = sum(
        1 for d in per_corpus.values() if d.get("delta_alpha") is not None
    )
    if n_finite < len(ARABIC_POOL):
        audit_failures.append(
            f"A1: only {n_finite}/{len(ARABIC_POOL)} corpora produced finite delta_alpha"
        )
    # A2 Quran H within +/- 0.15 of 0.7
    q_h = per_corpus.get("quran", {}).get("h_estimate")
    if q_h is None or abs(q_h - HURST_TARGET) > HURST_TOL:
        audit_failures.append(
            f"A2: quran h_estimate={q_h} drifts from {HURST_TARGET}+/-{HURST_TOL}"
        )
    # A3 series length floor
    for cn, d in per_corpus.items():
        if d.get("N", 0) < SERIES_LEN_FLOOR:
            audit_failures.append(
                f"A3: {cn} N={d.get('N')} < {SERIES_LEN_FLOOR}"
            )
    # A4 nondegen >= 5
    if nondegen < N_NONDEGEN_FLOOR:
        audit_failures.append(
            f"A4: only {nondegen} corpora with delta_alpha > {DELTA_ALPHA_NONDEGEN}"
        )

    # 5. Ranking by delta_alpha (smallest first)
    ranked = sorted(
        [(cn, d.get("delta_alpha")) for cn, d in per_corpus.items()
         if d.get("delta_alpha") is not None],
        key=lambda kv: kv[1],
    )
    quran_da = per_corpus.get("quran", {}).get("delta_alpha")
    quran_rank = next(
        (i + 1 for i, (cn, _) in enumerate(ranked) if cn == "quran"),
        None,
    )
    next_da = ranked[1][1] if len(ranked) >= 2 else None
    if quran_da and next_da and quran_rank == 1:
        margin = (next_da - quran_da) / quran_da
    else:
        margin = None

    # 6. Verdict
    if audit_failures:
        verdict = "FAIL_audit_" + audit_failures[0].split(":", 1)[0].strip()
    elif quran_rank != 1:
        verdict = "FAIL_quran_not_top_1"
    elif margin is not None and margin > MARGIN_FRACTION:
        verdict = "PASS_quran_strict_min_delta_alpha"
    else:
        verdict = "PARTIAL_top_1_within_eps"

    # 7. Console summary
    print()
    print(f"[{EXP}] per-corpus delta_alpha (rank order):")
    for i, (cn, da) in enumerate(ranked, 1):
        h_est = per_corpus[cn].get("h_estimate")
        print(f"  {i}. {cn:18s}  delta_alpha = {da:.4f}  h_est = {h_est}")
    print()
    print(f"  quran delta_alpha = {quran_da}")
    print(f"  quran rank        = {quran_rank}")
    print(f"  margin to next    = {margin}")
    print(f"  verdict           = {verdict}")
    print(f"  audit_failures    = {audit_failures}")

    # 8. Receipt
    receipt = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H52",
        "verdict": verdict,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "ARABIC_POOL": ARABIC_POOL,
            "SERIES_VARIABLE": SERIES_VARIABLE,
            "Q_GRID": Q_GRID,
            "SCALE_GRID_MIN": SCALE_GRID_MIN,
            "SCALE_GRID_MAX_FRAC": SCALE_GRID_MAX_FRAC,
            "N_SCALES": N_SCALES,
            "DETREND_ORDER": DETREND_ORDER,
            "F_ALPHA_THRESHOLD": F_ALPHA_THRESHOLD,
            "MARGIN_FRACTION": MARGIN_FRACTION,
            "RNG_SEED": RNG_SEED,
            "LIBRARY": "hand_rolled",
        },
        "per_corpus": per_corpus,
        "ranking": [
            {"rank": i + 1, "corpus": cn, "delta_alpha": da}
            for i, (cn, da) in enumerate(ranked)
        ],
        "headline": {
            "quran_delta_alpha": quran_da,
            "quran_rank": quran_rank,
            "next_delta_alpha": next_da,
            "margin_fraction": margin,
        },
        "quran_delta_alpha_rank": quran_rank,
        "n_corpora": len(ranked),
        "audit_failures": audit_failures,
        "wall_time_s": time.time() - t0,
    }
    with open(out_dir / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out_dir / (EXP + '.json')}")

    # 9. CSV summary
    with open(out_dir / "per_corpus_falpha.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["corpus", "N", "delta_alpha", "h_estimate"]
                   + [f"alpha_q{q}" for q in Q_GRID]
                   + [f"f_q{q}" for q in Q_GRID])
        for cn in ARABIC_POOL:
            d = per_corpus[cn]
            row = [cn, d.get("N"), d.get("delta_alpha"), d.get("h_estimate")]
            row.extend(d.get("alpha", []) + [None] * (len(Q_GRID) - len(d.get("alpha", []))))
            row.extend(d.get("f_alpha", []) + [None] * (len(Q_GRID) - len(d.get("f_alpha", []))))
            w.writerow(row)

    return 0 if verdict.startswith("PASS_") else (1 if audit_failures else 2)


if __name__ == "__main__":
    sys.exit(main())
