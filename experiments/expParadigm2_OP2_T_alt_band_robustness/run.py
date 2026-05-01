"""
expParadigm2_OP2_T_alt_band_robustness/run.py
==============================================
Robustness check for the T_alt refinement (`expParadigm2_OP2_T_alt_validation`).
The T_alt finding (Hotelling T² jumps from 3557 to 3868, +8.7 %; F-tail
log10 p from -480.25 to -507.80, +1.33σ) was established on Band-A
(15-100 verses) only. This experiment tests whether the refinement holds
on Band-B (5-14 verses) and Band-C (>100 verses).

Method (mirrors `expParadigm2_OP2_T_alt_validation`):
  1. For each band, build per-surah 5-D matrices for Quran and ctrl pool:
     - canonical (EL, VL_CV, CN, H_cond, T)
     - alternate  (EL, VL_CV, CN, H_cond, T_alt)
     where T_alt = H_cond(first_letter_of_last_word) - H(end_letter).
  2. Compute Hotelling T² and F-tail log10 p (mpmath 80-dps) for each
     band × {canonical, alt}.
  3. Verdict per band:
     - REFINEMENT_HOLDS_AT_BAND if T²_alt > T²_canonical AND log10 p_alt
       is more negative
     - REFINEMENT_FAILS_AT_BAND otherwise
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import mpmath as mp
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

EXP = "expParadigm2_OP2_T_alt_band_robustness"
RIDGE_LAMBDA = 1e-6
ARABIC_LETTER = re.compile(r"[\u0621-\u064A]")
CTRL_POOL_NAMES = ("poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "arabic_bible", "hindawi")

BANDS = {
    # name -> (lo_inclusive, hi_inclusive)
    "Band_A_15_100":    (15, 100),
    "Band_B_5_14":      (5, 14),
    "Band_C_101_inf":   (101, 10**9),
}


# ============================================================================
# Token extractors / entropies (same as expParadigm2_OP2_T_alt_validation)
# ============================================================================
def _alphabetic(s: str) -> str:
    return "".join(ARABIC_LETTER.findall(s))


def _first_letter_of_last_word(verse: str) -> str:
    toks = verse.strip().split()
    if not toks:
        return ""
    s = _alphabetic(toks[-1])
    return s[0] if s else ""


def _terminal_letter(verse: str) -> str:
    s = _alphabetic(verse)
    return s[-1] if s else ""


def _shannon_entropy_bits(seq: list) -> float:
    n = len(seq)
    if n == 0:
        return 0.0
    cnt = Counter(seq)
    h = 0.0
    for c in cnt.values():
        if c > 0:
            p = c / n
            h -= p * math.log2(p)
    return h


def _conditional_entropy_bits(seq: list) -> float:
    n = len(seq)
    if n < 2:
        return 0.0
    pairs = list(zip(seq[:-1], seq[1:]))
    cnt_pair = Counter(pairs)
    cnt_prev = Counter(seq[:-1])
    total = sum(cnt_pair.values())
    if total == 0:
        return 0.0
    by_prev: dict = {}
    for (a, b), n_ab in cnt_pair.items():
        by_prev.setdefault(a, Counter())[b] += n_ab
    h = 0.0
    for a, n_a in cnt_prev.items():
        p_a = n_a / total
        row = by_prev.get(a, Counter())
        row_total = sum(row.values())
        if row_total == 0:
            continue
        row_h = 0.0
        for c in row.values():
            if c > 0:
                p = c / row_total
                row_h -= p * math.log2(p)
        h += p_a * row_h
    return h


def _t_alt_per_surah(verses: list[str]) -> float:
    if len(verses) < 2:
        return float("nan")
    x_seq = [_first_letter_of_last_word(v) for v in verses]
    y_seq = [_terminal_letter(v) for v in verses]
    x_seq_clean = [t for t in x_seq if t]
    y_seq_clean = [t for t in y_seq if t]
    if len(x_seq_clean) < 2 or not y_seq_clean:
        return float("nan")
    return _conditional_entropy_bits(x_seq_clean) - _shannon_entropy_bits(y_seq_clean)


# ============================================================================
# Hotelling + mpmath F-tail
# ============================================================================
def _hotelling_T2(X1: np.ndarray, X2: np.ndarray, ridge: float = RIDGE_LAMBDA) -> dict:
    n1, p = X1.shape
    n2 = X2.shape[0]
    if n1 < 2 or n2 < 2 or n1 + n2 < p + 2:
        return {"T2": float("nan"), "F": float("nan"),
                "df1": int(p), "df2": int(max(0, n1 + n2 - p - 1)),
                "n_quran": int(n1), "n_ctrl": int(n2),
                "p_F_tail": float("nan"),
                "scipy_log10_p_F_tail": float("nan"),
                "highprec_log10_p_F_tail": float("nan")}
    m1, m2 = X1.mean(0), X2.mean(0)
    S1 = np.cov(X1, rowvar=False, ddof=1)
    S2 = np.cov(X2, rowvar=False, ddof=1)
    Sp = ((n1 - 1) * S1 + (n2 - 1) * S2) / max(1, (n1 + n2 - 2))
    Spi = np.linalg.inv(Sp + ridge * np.eye(p))
    diff = m1 - m2
    n_eff = (n1 * n2) / (n1 + n2)
    quad = float(diff @ Spi @ diff)
    t2 = float(n_eff * quad)
    df1, df2 = p, n1 + n2 - p - 1
    F = ((n1 + n2 - p - 1) / ((n1 + n2 - 2) * p)) * t2
    p_val = float(stats.f.sf(F, df1, df2))
    scipy_log10 = float(stats.f.logsf(F, df1, df2) / math.log(10))
    hp_log10 = None
    if not math.isfinite(scipy_log10) or p_val == 0.0:
        mp.mp.dps = 80
        F_mp = mp.mpf(F)
        df1_mp = mp.mpf(df1)
        df2_mp = mp.mpf(df2)
        x = df2_mp / (df2_mp + df1_mp * F_mp)
        sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
        hp_log10 = float(mp.log10(sf))
    return {
        "T2": t2, "F": F, "df1": int(df1), "df2": int(df2),
        "n_quran": int(n1), "n_ctrl": int(n2),
        "p_F_tail": p_val,
        "scipy_log10_p_F_tail": scipy_log10,
        "highprec_log10_p_F_tail": hp_log10,
    }


# ============================================================================
# Build per-band 5-D matrices
# ============================================================================
def _build_matrices_for_band(corpora: dict, feats: dict,
                             lo: int, hi: int) -> dict:
    """Build (X_canon_Q, X_alt_Q, X_canon_C, X_alt_C) for the given band."""
    label_to_unit_per_corpus = {}
    for c in ["quran"] + list(CTRL_POOL_NAMES):
        units = corpora.get(c, [])
        label_to_unit_per_corpus[c] = {
            str(getattr(u, "label", "")).strip(): u for u in units
        }

    def _rows_for_corpus(c: str) -> tuple[list, list, list]:
        """Return (canon_rows, alt_rows, t_alt_values_per_unit) for corpus c."""
        canon, alt, t_alts = [], [], []
        for r in feats.get(c, []):
            n_v = r.get("n_verses", 0)
            if not (lo <= n_v <= hi):
                continue
            T_canon = r.get("T")
            if not isinstance(T_canon, (int, float)) or not math.isfinite(T_canon):
                continue
            u = label_to_unit_per_corpus.get(c, {}).get(r.get("label", ""))
            if u is None:
                continue
            verses = list(u.verses)
            t_alt = _t_alt_per_surah(verses)
            if not math.isfinite(t_alt):
                continue
            canon.append([r["EL"], r["VL_CV"], r["CN"], r["H_cond"], T_canon])
            alt.append([r["EL"], r["VL_CV"], r["CN"], r["H_cond"], t_alt])
            t_alts.append(t_alt)
        return canon, alt, t_alts

    q_canon, q_alt, q_t_alts = _rows_for_corpus("quran")
    c_canon, c_alt, c_t_alts = [], [], []
    for c_name in CTRL_POOL_NAMES:
        cc, ca, ct = _rows_for_corpus(c_name)
        c_canon.extend(cc)
        c_alt.extend(ca)
        c_t_alts.extend(ct)

    return {
        "X_canon_Q": np.asarray(q_canon, dtype=float),
        "X_alt_Q":   np.asarray(q_alt, dtype=float),
        "X_canon_C": np.asarray(c_canon, dtype=float),
        "X_alt_C":   np.asarray(c_alt, dtype=float),
        "q_t_alts":  np.asarray(q_t_alts, dtype=float),
        "c_t_alts":  np.asarray(c_t_alts, dtype=float),
    }


# ============================================================================
# Main
# ============================================================================
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    feats = state["FEATS"]

    band_results = {}
    for band_name, (lo, hi) in BANDS.items():
        print(f"\n[{EXP}] === {band_name}  (n_verses ∈ [{lo}, {hi}]) ===")
        t_band = time.time()
        mats = _build_matrices_for_band(corpora, feats, lo, hi)
        n_q = mats["X_canon_Q"].shape[0]
        n_c = mats["X_canon_C"].shape[0]
        print(f"[{EXP}]   n_quran={n_q}  n_ctrl={n_c}  "
              f"(built in {time.time() - t_band:.1f}s)")

        if n_q < 2 or n_c < 2:
            print(f"[{EXP}]   SKIP — insufficient data")
            band_results[band_name] = {
                "lo": lo, "hi": hi, "n_quran": n_q, "n_ctrl": n_c,
                "skipped": True,
            }
            continue

        # Sanity — same first 4 cols
        delta_q = (
            float(np.abs(mats["X_canon_Q"][:, :4] - mats["X_alt_Q"][:, :4]).max())
            if mats["X_canon_Q"].shape[0] == mats["X_alt_Q"].shape[0]
            else float("inf")
        )
        delta_c = (
            float(np.abs(mats["X_canon_C"][:, :4] - mats["X_alt_C"][:, :4]).max())
            if mats["X_canon_C"].shape[0] == mats["X_alt_C"].shape[0]
            else float("inf")
        )

        t_canon = _hotelling_T2(mats["X_canon_Q"], mats["X_canon_C"])
        t_alt   = _hotelling_T2(mats["X_alt_Q"],   mats["X_alt_C"])

        ratio = (t_alt["T2"] / t_canon["T2"]
                 if t_canon["T2"] > 0 else float("nan"))
        # log10 p — prefer mpmath when available, else scipy
        canon_log10 = (t_canon["highprec_log10_p_F_tail"]
                       if t_canon["highprec_log10_p_F_tail"] is not None
                       else t_canon["scipy_log10_p_F_tail"])
        alt_log10 = (t_alt["highprec_log10_p_F_tail"]
                     if t_alt["highprec_log10_p_F_tail"] is not None
                     else t_alt["scipy_log10_p_F_tail"])
        delta_log10 = (alt_log10 - canon_log10
                       if (canon_log10 is not None and alt_log10 is not None
                           and math.isfinite(canon_log10)
                           and math.isfinite(alt_log10))
                       else float("nan"))

        # σ-equivalent
        sigma_canon = (math.sqrt(-2.0 * canon_log10 * math.log(10))
                       if canon_log10 is not None
                       and math.isfinite(canon_log10) and canon_log10 < 0
                       else float("nan"))
        sigma_alt = (math.sqrt(-2.0 * alt_log10 * math.log(10))
                     if alt_log10 is not None
                     and math.isfinite(alt_log10) and alt_log10 < 0
                     else float("nan"))

        # T_alt pct_pos
        q_t_alt_pos = float((mats["q_t_alts"] > 0).mean()) if mats["q_t_alts"].size else float("nan")
        c_t_alt_pos = float((mats["c_t_alts"] > 0).mean()) if mats["c_t_alts"].size else float("nan")

        # Verdict
        if (math.isfinite(t_alt["T2"]) and math.isfinite(t_canon["T2"])
                and t_alt["T2"] > t_canon["T2"] * 1.01
                and math.isfinite(delta_log10) and delta_log10 < 0):
            verdict = f"REFINEMENT_HOLDS_AT_{band_name}"
        elif (math.isfinite(t_alt["T2"]) and math.isfinite(t_canon["T2"])
              and t_alt["T2"] >= t_canon["T2"] * 0.99):
            verdict = f"REFINEMENT_NEUTRAL_AT_{band_name}"
        else:
            verdict = f"REFINEMENT_FAILS_AT_{band_name}"

        print(f"[{EXP}]   first-4-cols alignment: "
              f"|Δ| Q = {delta_q:.3e}, C = {delta_c:.3e}")
        print(f"[{EXP}]   canonical T²={t_canon['T2']:.4f}  F={t_canon['F']:.4f}  "
              f"log₁₀p={canon_log10}  ~{sigma_canon:.2f}σ")
        print(f"[{EXP}]   alt       T²={t_alt['T2']:.4f}  F={t_alt['F']:.4f}  "
              f"log₁₀p={alt_log10}  ~{sigma_alt:.2f}σ")
        print(f"[{EXP}]   T²_alt / T²_canon = {ratio:.4f}  "
              f"  ΔlogP = {delta_log10:+.4f}  Δσ = "
              f"{(sigma_alt - sigma_canon):+.4f}σ")
        print(f"[{EXP}]   Quran T_alt_pct_pos = {q_t_alt_pos:.4f}  "
              f"  ctrl pooled = {c_t_alt_pos:.4f}")
        print(f"[{EXP}]   verdict: {verdict}")

        band_results[band_name] = {
            "lo": int(lo), "hi": int(hi),
            "n_quran": int(n_q), "n_ctrl": int(n_c),
            "alignment_check": {
                "max_abs_delta_first4_Q": float(delta_q),
                "max_abs_delta_first4_C": float(delta_c),
            },
            "hotelling_T2_canonical": t_canon,
            "hotelling_T2_alt":       t_alt,
            "T2_ratio_alt_over_canon": float(ratio)
                if math.isfinite(ratio) else None,
            "delta_log10_p_alt_minus_canon": (float(delta_log10)
                if math.isfinite(delta_log10) else None),
            "sigma_canon": float(sigma_canon)
                if math.isfinite(sigma_canon) else None,
            "sigma_alt":   float(sigma_alt)
                if math.isfinite(sigma_alt) else None,
            "delta_sigma": (float(sigma_alt - sigma_canon)
                if (math.isfinite(sigma_canon) and math.isfinite(sigma_alt))
                else None),
            "T_alt_pct_pos_quran": q_t_alt_pos,
            "T_alt_pct_pos_ctrl":  c_t_alt_pos,
            "verdict": verdict,
        }

    # Cross-band verdict
    n_bands_holds = sum(1 for v in band_results.values()
                         if isinstance(v.get("verdict"), str)
                         and "REFINEMENT_HOLDS_AT" in v["verdict"])
    n_bands_neutral = sum(1 for v in band_results.values()
                           if isinstance(v.get("verdict"), str)
                           and "REFINEMENT_NEUTRAL_AT" in v["verdict"])
    n_bands_fails = sum(1 for v in band_results.values()
                         if isinstance(v.get("verdict"), str)
                         and "REFINEMENT_FAILS_AT" in v["verdict"])
    n_eligible = sum(1 for v in band_results.values()
                      if not v.get("skipped", False))

    if n_bands_holds == n_eligible:
        global_verdict = "T_ALT_REFINEMENT_HOLDS_ON_ALL_BANDS"
    elif n_bands_holds + n_bands_neutral == n_eligible:
        global_verdict = "T_ALT_REFINEMENT_NEUTRAL_OR_BETTER_ON_ALL_BANDS"
    elif n_bands_holds > 0:
        global_verdict = "T_ALT_REFINEMENT_HOLDS_AT_BAND_A_BUT_FAILS_ELSEWHERE"
    else:
        global_verdict = "T_ALT_REFINEMENT_FAILS"

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "P2_OP2 follow-up — Band-B / Band-C robustness for T_alt",
        "title": (
            "Tests whether the T_alt refinement (T² + 8.7 %, log10 p − 27.55, "
            "+1.33σ on Band-A) holds at Band-B (5-14 verses) and Band-C "
            "(>100 verses)."
        ),
        "bands_tested": {k: list(v) for k, v in BANDS.items()},
        "per_band": band_results,
        "n_bands_holds":   n_bands_holds,
        "n_bands_neutral": n_bands_neutral,
        "n_bands_fails":   n_bands_fails,
        "n_eligible":      n_eligible,
        "global_verdict":  global_verdict,
        "runtime_seconds": round(runtime, 2),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    for band_name, v in band_results.items():
        if v.get("skipped", False):
            continue
        print(f"[{EXP}]   {band_name:<18s}  n_q={v['n_quran']:>3d}  n_c={v['n_ctrl']:>4d}  "
              f"T²_alt/T²_canon={v.get('T2_ratio_alt_over_canon', float('nan')):.4f}  "
              f"ΔlogP={v.get('delta_log10_p_alt_minus_canon', float('nan')):+.4f}  "
              f"verdict: {v['verdict']}")
    print(f"[{EXP}] global verdict: {global_verdict}")
    print(f"[{EXP}] runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
