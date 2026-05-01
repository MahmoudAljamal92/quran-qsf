"""
expParadigm2_OP2_T_alt_validation/run.py
=========================================
P2_OP2 follow-up: validate the surprising P2_OP2 search result by
re-running Hotelling T² with a REPLACEMENT T definition.

The P2_OP2 search (`expParadigm2_OP2_feature_pair_search`) found that
    T_alt = H_cond(first_letter_of_last_word | X_prev) - H(end_letter)
produces Quran T_alt_pct_pos = 51.5 %, vs canonical T (using primary
triliteral root via CamelTools) at 39.7 %. The alternative has NO
CamelTools cost and DOMINATES the canonical by 30 % on the T_pct_pos
discrimination gap.

This experiment asks: does swapping T → T_alt in the 5-D feature
vector (EL, VL_CV, CN, H_cond, T_alt) produce a LARGER Hotelling T²
than the canonical (EL, VL_CV, CN, H_cond, T_canonical)?

If Hotelling T² grows, T_alt is a publishable refinement of the
project's T definition.

Method:
  1. Load `state['FEATS']` for the canonical (EL, VL_CV, CN, H_cond,
     T_canonical) values per Band-A surah for every corpus.
  2. Recompute T_alt per Band-A surah by iterating over CORPORA verse
     lists (no CamelTools; pure surface-token extraction).
  3. Assemble two 5-D matrices:
       X_Q_canon = [EL, VL_CV, CN, H_cond, T_canonical]
       X_Q_alt   = [EL, VL_CV, CN, H_cond, T_alt]
     and similarly for X_C.
  4. Compute Hotelling T² for both. Also compute (a) Cohen d on the
     T / T_alt column alone, (b) per-dim gain of T_alt vs T_canonical
     in the 5-D ensemble.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl

Writes:
  - results/experiments/expParadigm2_OP2_T_alt_validation/
      expParadigm2_OP2_T_alt_validation.json
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

EXP = "expParadigm2_OP2_T_alt_validation"
BAND_A_LO, BAND_A_HI = 15, 100
RIDGE_LAMBDA = 1e-6
ARABIC_LETTER = re.compile(r"[\u0621-\u064A]")
CTRL_POOL_NAMES = ("poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "arabic_bible", "hindawi")


# ============================================================================
# T_alt extraction
# ============================================================================
def _alphabetic(s: str) -> str:
    return "".join(ARABIC_LETTER.findall(s))


def _first_letter_of_last_word(verse: str) -> str:
    """X for T_alt: first Arabic letter of the last whitespace-separated
    token of the verse."""
    toks = verse.strip().split()
    if not toks:
        return ""
    s = _alphabetic(toks[-1])
    return s[0] if s else ""


def _terminal_letter(verse: str) -> str:
    """Y for T_alt (same as canonical Y): last Arabic letter of the verse."""
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
    """H(X_t | X_{t-1}) on a sequence."""
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
    """T_alt = H_cond(first_letter_of_last_word) - H(end_letter)."""
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
# Hotelling T²  helpers
# ============================================================================
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
    F = ((n1 + n2 - p - 1) / ((n1 + n2 - 2) * p)) * t2 if df2 > 0 else float("nan")
    # Cohen d pooled (multivariate)
    d_maha = math.sqrt(max(quad, 0.0))
    return {
        "T2": t2, "F": F, "df1": int(df1), "df2": int(df2),
        "n_eff": float(n_eff), "n_quran": int(n1), "n_ctrl": int(n2),
        "cohen_d_pooled_mahalanobis": d_maha,
    }


def _cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    s2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / max(
        1, len(a) + len(b) - 2
    )
    s = math.sqrt(s2)
    if s <= 1e-12:
        return float("nan")
    return float((a.mean() - b.mean()) / s)


# ============================================================================
# Main
# ============================================================================
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feats = state["FEATS"]
    corpora = state["CORPORA"]
    X_Q_locked = np.asarray(state["X_QURAN"], dtype=float)
    X_C_locked = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    if feat_cols != ["EL", "VL_CV", "CN", "H_cond", "T"]:
        raise RuntimeError(f"FEAT_COLS drift: {feat_cols}")
    t_col = feat_cols.index("T")

    print(f"[{EXP}] X_Q_locked {X_Q_locked.shape}  X_C_locked {X_C_locked.shape}")

    # ========== Step 1: per-surah alignment — Band-A Quran + per-ctrl-corpus ==
    # The Band-A unit lists in CORPORA are the SAME units that populated FEATS.
    # Iterate CORPORA[c], filter Band-A, compute T_alt per unit by matching
    # label order with FEATS[c] (both share iteration order).
    def _band_a_records(c: str):
        """Yield (feat_rec, unit_obj) pairs for Band-A units of corpus c.
        Both FEATS[c] and CORPORA[c] are lexically aligned in the pipeline."""
        units = corpora.get(c, [])
        label_to_unit = {}
        for u in units:
            lbl = str(getattr(u, "label", "")).strip()
            label_to_unit[lbl] = u
        for r in feats.get(c, []):
            if BAND_A_LO <= r["n_verses"] <= BAND_A_HI:
                u = label_to_unit.get(r.get("label", ""))
                if u is None:
                    continue
                yield r, u

    # ========== Step 2: compute T_alt for Band-A Quran and ctrl pool ==========
    t_build = time.time()
    # Quran Band-A
    q_t_alt = []
    q_T_canonical = []
    q_rows = []
    for r, u in _band_a_records("quran"):
        verses = list(u.verses)
        t_alt_val = _t_alt_per_surah(verses)
        q_t_alt.append(t_alt_val)
        q_T_canonical.append(r["T"])
        q_rows.append([r["EL"], r["VL_CV"], r["CN"], r["H_cond"], t_alt_val])
    q_t_alt = np.asarray(q_t_alt, dtype=float)
    q_T_canonical = np.asarray(q_T_canonical, dtype=float)

    # Ctrl pool Band-A, per corpus then stacked
    c_rows = []
    c_t_alt_list = []
    c_T_canonical_list = []
    for c in CTRL_POOL_NAMES:
        for r, u in _band_a_records(c):
            verses = list(u.verses)
            t_alt_val = _t_alt_per_surah(verses)
            c_t_alt_list.append(t_alt_val)
            c_T_canonical_list.append(r["T"])
            c_rows.append([r["EL"], r["VL_CV"], r["CN"], r["H_cond"], t_alt_val])
    c_t_alt = np.asarray(c_t_alt_list, dtype=float)
    c_T_canonical = np.asarray(c_T_canonical_list, dtype=float)

    # Drop rows with NaN T_alt
    q_rows_arr = np.asarray(q_rows, dtype=float)
    c_rows_arr = np.asarray(c_rows, dtype=float)
    q_mask = np.isfinite(q_rows_arr[:, -1])
    c_mask = np.isfinite(c_rows_arr[:, -1])
    X_Q_alt = q_rows_arr[q_mask]
    X_C_alt = c_rows_arr[c_mask]
    print(f"[{EXP}] X_Q_alt {X_Q_alt.shape}  X_C_alt {X_C_alt.shape}   "
          f"(built in {time.time() - t_build:.1f}s)")
    print(f"[{EXP}] n_dropped: q={int((~q_mask).sum())}  c={int((~c_mask).sum())}")

    # ========== Step 3: sanity check — Band-A Quran T_alt pct_pos ==========
    q_t_alt_clean = q_t_alt[np.isfinite(q_t_alt)]
    c_t_alt_clean = c_t_alt[np.isfinite(c_t_alt)]
    q_t_alt_pct_pos = float((q_t_alt_clean > 0).mean())
    c_t_alt_pct_pos = float((c_t_alt_clean > 0).mean())
    print(f"[{EXP}] Quran T_alt_pct_pos = {q_t_alt_pct_pos:.4f}  "
          f"(P2_OP2 reported 0.5147; match?)")
    print(f"[{EXP}] Ctrl  T_alt_pct_pos (pooled) = {c_t_alt_pct_pos:.4f}")

    # ========== Step 4: Hotelling T² comparison ==========
    print(f"\n[{EXP}] === Hotelling T² comparison ===")
    # Canonical (use locked X_Q_locked / X_C_locked directly)
    t2_canon = _hotelling_T2(X_Q_locked, X_C_locked)
    print(f"[{EXP}]   CANONICAL (EL, VL_CV, CN, H_cond, T): "
          f"T² = {t2_canon['T2']:.4f}   "
          f"F = {t2_canon['F']:.4f}  "
          f"df = ({t2_canon['df1']}, {t2_canon['df2']})")

    # T_alt — replace the T column in X_Q_locked/X_C_locked with T_alt values
    # Need to make sure alignment is identical: rebuild alt matrices from
    # the locked 4-dim (EL, VL_CV, CN, H_cond) columns plus T_alt.
    # We built X_Q_alt / X_C_alt from FEATS in the same order as X_Q_locked /
    # X_C_locked (since both come from the same Band-A filter), but let's
    # verify by comparing the first 4 columns.
    delta_q_first4 = np.abs(X_Q_alt[:, :4] - X_Q_locked[q_mask, :4]).max() if q_mask.sum() == X_Q_locked.shape[0] else float("inf")
    delta_c_first4 = np.abs(X_C_alt[:, :4] - X_C_locked[c_mask, :4]).max() if c_mask.sum() == X_C_locked.shape[0] else float("inf")
    print(f"[{EXP}]   first-4-cols alignment check: "
          f"max |Δ| Q = {delta_q_first4:.3e}, C = {delta_c_first4:.3e}")

    t2_alt = _hotelling_T2(X_Q_alt, X_C_alt)
    print(f"[{EXP}]   ALTERNATE (EL, VL_CV, CN, H_cond, T_alt): "
          f"T² = {t2_alt['T2']:.4f}   "
          f"F = {t2_alt['F']:.4f}  "
          f"df = ({t2_alt['df1']}, {t2_alt['df2']})")

    # ========== Step 5: Per-feature Cohen d on T vs T_alt ==========
    d_T_canon = _cohen_d(q_T_canonical, c_T_canonical)
    d_T_alt   = _cohen_d(q_t_alt_clean, c_t_alt_clean)
    print(f"\n[{EXP}] Cohen d on the single feature:")
    print(f"[{EXP}]   T_canonical (Quran vs ctrl-pool): d = {d_T_canon:+.4f}")
    print(f"[{EXP}]   T_alt       (Quran vs ctrl-pool): d = {d_T_alt:+.4f}")

    # ========== Step 6: Verdict ==========
    t2_ratio = t2_alt["T2"] / t2_canon["T2"] if t2_canon["T2"] > 0 else float("nan")
    print(f"\n[{EXP}] T²_alt / T²_canonical = {t2_ratio:.4f}")
    if t2_ratio > 1.05:
        verdict = "T_ALT_REFINES_PHI_M_POSITIVELY"
    elif t2_ratio > 0.95:
        verdict = "T_ALT_EQUIVALENT_TO_CANONICAL"
    else:
        verdict = "T_ALT_WEAKENS_PHI_M"
    print(f"[{EXP}] verdict: {verdict}")

    # ========== Step 7: T_pct_pos comparison reconciled with P2_OP2 ==========
    # The P2_OP2 experiment used CORPORA iteration (not FEATS alignment),
    # so Quran n could differ. Report both and explain any drift.
    print(f"\n[{EXP}] T_pct_pos reconciliation:")
    canonical_q_pct_pos = float((q_T_canonical > 0).mean())
    print(f"[{EXP}]   T_canon Quran pct_pos (locked): {canonical_q_pct_pos:.4f}  "
          f"(headline 0.397)")
    print(f"[{EXP}]   T_alt   Quran pct_pos:          {q_t_alt_pct_pos:.4f}  "
          f"(P2_OP2 reported 0.515)")

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "Paradigm-Stage 2 — P2_OP2 follow-up: T_alt Φ_M validation",
        "title": (
            "Does replacing the canonical T = H_cond(primary_root) − "
            "H(end_letter) with T_alt = H_cond(first_letter_of_last_word) "
            "− H(end_letter) PRODUCE a stronger Hotelling T² on the 5-D "
            "feature matrix?"
        ),
        "band_A_range": [BAND_A_LO, BAND_A_HI],
        "n_quran_band_A": int(q_rows_arr.shape[0]),
        "n_ctrl_band_A": int(c_rows_arr.shape[0]),
        "n_quran_dropped_t_alt_nan": int((~q_mask).sum()),
        "n_ctrl_dropped_t_alt_nan":  int((~c_mask).sum()),
        "T_alt_pct_pos_quran": q_t_alt_pct_pos,
        "T_alt_pct_pos_ctrl_pooled": c_t_alt_pct_pos,
        "T_canon_pct_pos_quran": canonical_q_pct_pos,
        "cohen_d_single_feature": {
            "T_canonical": d_T_canon,
            "T_alt":       d_T_alt,
        },
        "hotelling_T2_canonical": t2_canon,
        "hotelling_T2_alt":       t2_alt,
        "T2_ratio_alt_over_canon": t2_ratio,
        "alignment_check": {
            "max_abs_delta_first4_cols_Q": float(delta_q_first4),
            "max_abs_delta_first4_cols_C": float(delta_c_first4),
            "clean_alignment":
                bool(delta_q_first4 < 1e-9 and delta_c_first4 < 1e-9),
        },
        "verdict": verdict,
        "interpretation": [
            "If T²_alt > T²_canonical by > 5 %, the P2_OP2 refinement "
            "REFINES the project's Φ_M headline: replacing T (CamelTools-"
            "root-based) with T_alt (CamelTools-free surface-token-based) "
            "produces a stronger multivariate separation.",
            "The single-feature Cohen d comparison helps interpret: "
            "d_T_alt > d_T_canonical means T_alt carries MORE marginal "
            "discrimination, which usually translates to higher T² in the "
            "multivariate matrix (unless there's strong redundancy with "
            "the other 4 features).",
            "A positive verdict here would make T_alt a publishable "
            "replacement for the canonical T, validated at the same 5-D "
            "Hotelling level that Φ_M = 3557.34 was originally "
            "established at.",
        ],
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   T²_canonical = {t2_canon['T2']:.2f}")
    print(f"[{EXP}]   T²_alt       = {t2_alt['T2']:.2f}")
    print(f"[{EXP}]   ratio        = {t2_ratio:.4f}")
    print(f"[{EXP}]   d_T_canon    = {d_T_canon:+.4f}")
    print(f"[{EXP}]   d_T_alt      = {d_T_alt:+.4f}")
    print(f"[{EXP}]   verdict      = {verdict}")
    print(f"[{EXP}]   runtime      = {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
