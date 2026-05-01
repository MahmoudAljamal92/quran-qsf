"""
expParadigm2_OP2_T_canon_plus_T_alt_6D/run.py
==============================================
Tests whether T_canon and T_alt are COMPLEMENTARY or REDUNDANT in the
multivariate setting by stacking both as a 6-D matrix and computing
Hotelling T².

Three matrices, all per Band-A surah (n_q = 68, n_c = 2509):
  X_canon (5-D) : (EL, VL_CV, CN, H_cond, T_canonical)
  X_alt   (5-D) : (EL, VL_CV, CN, H_cond, T_alt)
  X_6D    (6-D) : (EL, VL_CV, CN, H_cond, T_canonical, T_alt)

Verdict matrix:
  T²_6D > max(T²_canon, T²_alt) by > 1 % → COMPLEMENTARY
                                          (T_canon and T_alt carry
                                           orthogonal information; the
                                           6-D gain proves both should
                                           be retained)
  T²_6D ≈ T²_alt  > T²_canon  → T_ALT_DOMINATES (T_canon is redundant
                                                  given T_alt)
  T²_6D ≈ T²_canon                 → T_CANON_DOMINATES
  T²_6D < max(T²_canon, T²_alt)    → COVARIANCE_PENALTY (collinearity)

Also computes the per-dim gain (B12-style):
  per_dim_gain_T_alt_over_5D_canon = T²_6D / T²_5D_canon
  per_dim_gain_T_canon_over_5D_alt = T²_6D / T²_5D_alt

If per_dim_gain_T_alt_over_5D_canon > 1 → T_alt adds information beyond
the 5-D canonical baseline (admissible 6th channel).

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl

Writes:
  - results/experiments/expParadigm2_OP2_T_canon_plus_T_alt_6D/
      expParadigm2_OP2_T_canon_plus_T_alt_6D.json
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import mpmath as mp
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

EXP = "expParadigm2_OP2_T_canon_plus_T_alt_6D"
BAND_A_LO, BAND_A_HI = 15, 100
RIDGE_LAMBDA = 1e-6
ARABIC_LETTER = re.compile(r"[\u0621-\u064A]")
CTRL_POOL_NAMES = ("poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "arabic_bible", "hindawi")


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


def _t_alt(verses: list[str]) -> float:
    if len(verses) < 2:
        return float("nan")
    x_seq = [_first_letter_of_last_word(v) for v in verses]
    y_seq = [_terminal_letter(v) for v in verses]
    x_seq_clean = [t for t in x_seq if t]
    y_seq_clean = [t for t in y_seq if t]
    if len(x_seq_clean) < 2 or not y_seq_clean:
        return float("nan")
    return _conditional_entropy_bits(x_seq_clean) - _shannon_entropy_bits(y_seq_clean)


def _hotelling_T2(X1: np.ndarray, X2: np.ndarray, ridge: float = RIDGE_LAMBDA) -> dict:
    n1, p = X1.shape
    n2 = X2.shape[0]
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
        "n_eff": float(n_eff), "n_quran": int(n1), "n_ctrl": int(n2),
        "p_F_tail": p_val,
        "scipy_log10_p_F_tail": scipy_log10,
        "highprec_log10_p_F_tail": hp_log10,
        "p_dim": int(p),
    }


def _band_a_records(corpus_name: str, corpora: dict, feats: dict):
    units = corpora.get(corpus_name, [])
    label_to_unit = {
        str(getattr(u, "label", "")).strip(): u for u in units
    }
    for r in feats.get(corpus_name, []):
        if BAND_A_LO <= r.get("n_verses", 0) <= BAND_A_HI:
            u = label_to_unit.get(r.get("label", ""))
            if u is None:
                continue
            yield r, u


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feats = state["FEATS"]
    corpora = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])
    if feat_cols != ["EL", "VL_CV", "CN", "H_cond", "T"]:
        raise RuntimeError(f"FEAT_COLS drift: {feat_cols}")

    print(f"[{EXP}] building 6-D matrices (Band-A)...")
    t_build = time.time()
    q_canon, q_alt, q_6d = [], [], []
    for r, u in _band_a_records("quran", corpora, feats):
        verses = list(u.verses)
        ta = _t_alt(verses)
        if not math.isfinite(ta):
            continue
        if not isinstance(r["T"], (int, float)) or not math.isfinite(r["T"]):
            continue
        feat4 = [r["EL"], r["VL_CV"], r["CN"], r["H_cond"]]
        q_canon.append(feat4 + [r["T"]])
        q_alt.append(feat4 + [ta])
        q_6d.append(feat4 + [r["T"], ta])
    c_canon, c_alt, c_6d = [], [], []
    for c_name in CTRL_POOL_NAMES:
        for r, u in _band_a_records(c_name, corpora, feats):
            verses = list(u.verses)
            ta = _t_alt(verses)
            if not math.isfinite(ta):
                continue
            if not isinstance(r["T"], (int, float)) or not math.isfinite(r["T"]):
                continue
            feat4 = [r["EL"], r["VL_CV"], r["CN"], r["H_cond"]]
            c_canon.append(feat4 + [r["T"]])
            c_alt.append(feat4 + [ta])
            c_6d.append(feat4 + [r["T"], ta])
    print(f"[{EXP}]   built in {time.time() - t_build:.1f}s")

    X_Q_canon = np.asarray(q_canon, dtype=float)
    X_C_canon = np.asarray(c_canon, dtype=float)
    X_Q_alt   = np.asarray(q_alt, dtype=float)
    X_C_alt   = np.asarray(c_alt, dtype=float)
    X_Q_6D    = np.asarray(q_6d, dtype=float)
    X_C_6D    = np.asarray(c_6d, dtype=float)

    print(f"[{EXP}]   X_Q_canon {X_Q_canon.shape}  X_C_canon {X_C_canon.shape}")
    print(f"[{EXP}]   X_Q_alt   {X_Q_alt.shape}    X_C_alt   {X_C_alt.shape}")
    print(f"[{EXP}]   X_Q_6D    {X_Q_6D.shape}     X_C_6D    {X_C_6D.shape}")

    # Hotelling T²
    print(f"\n[{EXP}] === Hotelling T² comparison ===")
    t_canon = _hotelling_T2(X_Q_canon, X_C_canon)
    t_alt   = _hotelling_T2(X_Q_alt,   X_C_alt)
    t_6d    = _hotelling_T2(X_Q_6D,    X_C_6D)
    for name, td in [("5-D canonical", t_canon),
                     ("5-D alt",       t_alt),
                     ("6-D both",      t_6d)]:
        print(f"[{EXP}]   {name:<14s}  T²={td['T2']:.4f}  F={td['F']:.4f}  "
              f"df=({td['df1']},{td['df2']})  "
              f"log₁₀p_hp={td['highprec_log10_p_F_tail']}")

    # Per-dim gain (B12-style)
    gain_alt_over_canon = (t_6d["T2"] / t_canon["T2"]) ** (1.0)  # raw ratio
    gain_canon_over_alt = (t_6d["T2"] / t_alt["T2"]) ** (1.0)
    per_dim_gain_alt = (t_6d["T2"] / t_canon["T2"]) ** (5 / 6)
    per_dim_gain_canon = (t_6d["T2"] / t_alt["T2"]) ** (5 / 6)
    print(f"\n[{EXP}] Per-dim gain (B12 style: T²_6D / T²_5D)^{{(5/6)}}:")
    print(f"[{EXP}]   gain T_alt over 5D canonical = "
          f"{per_dim_gain_alt:.4f}  "
          f"(raw T²_6D / T²_canon = {gain_alt_over_canon:.4f})")
    print(f"[{EXP}]   gain T_canon over 5D alt   = "
          f"{per_dim_gain_canon:.4f}  "
          f"(raw T²_6D / T²_alt = {gain_canon_over_alt:.4f})")

    # Verdict
    eps = 0.01
    t2_canon, t2_alt, t2_6d = t_canon["T2"], t_alt["T2"], t_6d["T2"]
    if t2_6d > max(t2_canon, t2_alt) * (1 + eps):
        verdict = "COMPLEMENTARY_T_CANON_AND_T_ALT_BOTH_RETAINED"
    elif abs(t2_6d - t2_alt) < t2_alt * eps and t2_alt > t2_canon * (1 + eps):
        verdict = "T_ALT_DOMINATES_T_CANON_REDUNDANT"
    elif abs(t2_6d - t2_canon) < t2_canon * eps:
        verdict = "T_CANON_DOMINATES_T_ALT_REDUNDANT"
    elif t2_6d < max(t2_canon, t2_alt) * (1 - eps):
        verdict = "COLLINEARITY_PENALTY_BOTH_REDUNDANT"
    else:
        verdict = "INTERMEDIATE_BOTH_PARTIALLY_REDUNDANT"
    print(f"\n[{EXP}] verdict: {verdict}")

    # σ-equivalent for the 6-D
    log10_p_6d = t_6d["highprec_log10_p_F_tail"]
    if log10_p_6d is None:
        log10_p_6d = t_6d["scipy_log10_p_F_tail"]
    sigma_6d = (math.sqrt(-2.0 * log10_p_6d * math.log(10))
                if math.isfinite(log10_p_6d) and log10_p_6d < 0
                else float("nan"))
    log10_p_canon = t_canon["highprec_log10_p_F_tail"]
    log10_p_alt = t_alt["highprec_log10_p_F_tail"]
    sigma_canon = (math.sqrt(-2.0 * log10_p_canon * math.log(10))
                   if math.isfinite(log10_p_canon) and log10_p_canon < 0
                   else float("nan"))
    sigma_alt = (math.sqrt(-2.0 * log10_p_alt * math.log(10))
                 if math.isfinite(log10_p_alt) and log10_p_alt < 0
                 else float("nan"))
    print(f"\n[{EXP}] σ-equivalent under F-tail null:")
    print(f"[{EXP}]   5-D canonical : {sigma_canon:.2f}σ "
          f"(log₁₀p = {log10_p_canon:.2f})")
    print(f"[{EXP}]   5-D alt       : {sigma_alt:.2f}σ "
          f"(log₁₀p = {log10_p_alt:.2f})")
    print(f"[{EXP}]   6-D both      : {sigma_6d:.2f}σ "
          f"(log₁₀p = {log10_p_6d:.2f})")

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "P2_OP2 follow-up — 6-D (T_canon + T_alt) joint Hotelling T²",
        "title": (
            "Tests whether stacking T_canon and T_alt as a 6-D matrix "
            "produces strictly stronger discrimination than either 5-D "
            "matrix alone (i.e., are they complementary or redundant?)."
        ),
        "band_A_range": [BAND_A_LO, BAND_A_HI],
        "n_quran_band_A": int(X_Q_6D.shape[0]),
        "n_ctrl_band_A":  int(X_C_6D.shape[0]),
        "matrices": {
            "5D_canonical": {"shape_Q": list(X_Q_canon.shape),
                             "shape_C": list(X_C_canon.shape)},
            "5D_alt":       {"shape_Q": list(X_Q_alt.shape),
                             "shape_C": list(X_C_alt.shape)},
            "6D_both":      {"shape_Q": list(X_Q_6D.shape),
                             "shape_C": list(X_C_6D.shape)},
        },
        "hotelling_T2_5D_canonical": t_canon,
        "hotelling_T2_5D_alt":       t_alt,
        "hotelling_T2_6D_both":      t_6d,
        "T2_ratios": {
            "T2_6D_over_T2_5D_canon": t2_6d / t2_canon,
            "T2_6D_over_T2_5D_alt":   t2_6d / t2_alt,
            "T2_5D_alt_over_T2_5D_canon": t2_alt / t2_canon,
        },
        "per_dim_gain_B12_style": {
            "gain_T_alt_over_5D_canon":  per_dim_gain_alt,
            "gain_T_canon_over_5D_alt":  per_dim_gain_canon,
            "passes_1_0_gate_alt_over_canon":
                bool(per_dim_gain_alt > 1.0),
            "passes_1_0_gate_canon_over_alt":
                bool(per_dim_gain_canon > 1.0),
        },
        "sigma_equivalent": {
            "5D_canonical": sigma_canon,
            "5D_alt":       sigma_alt,
            "6D_both":      sigma_6d,
        },
        "delta_sigma": {
            "6D_minus_5D_canonical": (sigma_6d - sigma_canon
                if (math.isfinite(sigma_6d) and math.isfinite(sigma_canon))
                else None),
            "6D_minus_5D_alt": (sigma_6d - sigma_alt
                if (math.isfinite(sigma_6d) and math.isfinite(sigma_alt))
                else None),
        },
        "verdict": verdict,
        "interpretation": [
            "If verdict = COMPLEMENTARY_T_CANON_AND_T_ALT_BOTH_RETAINED, "
            "T_canon and T_alt carry orthogonal information. The 6-D "
            "model would be the strongest discriminator and BOTH should "
            "be retained as project features.",
            "If verdict = T_ALT_DOMINATES_T_CANON_REDUNDANT, T_alt is a "
            "strict replacement: the 6-D adds no info beyond T_alt, so "
            "T_canon can be DROPPED from the project.",
            "If verdict = COLLINEARITY_PENALTY, both features carry the "
            "SAME information; adding both reduces T² due to df penalty. "
            "Pick whichever is cleaner (T_alt — CamelTools-free).",
        ],
        "runtime_seconds": round(runtime, 2),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   T²_5D_canon = {t2_canon:.2f}   ~{sigma_canon:.2f}σ")
    print(f"[{EXP}]   T²_5D_alt   = {t2_alt:.2f}   ~{sigma_alt:.2f}σ")
    print(f"[{EXP}]   T²_6D_both  = {t2_6d:.2f}   ~{sigma_6d:.2f}σ")
    print(f"[{EXP}]   verdict     = {verdict}")
    print(f"[{EXP}]   runtime     = {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
