"""
exp67_adjacent_jaccard/run.py
==============================
H18: Adjacent-Verse Jaccard Anti-Repetition — The 6th Blessed Channel?

Motivation
    MASTER_FINDINGS_REPORT §2 reports Quran adjacent-verse Jaccard = 0.042
    vs controls 0.190, d = −0.475 (tabdīl: deliberate lexical variation).
    The 5-D fingerprint captures acoustic/structural properties; semantic
    diversity is absent. This tests whether adjacent-verse Jaccard carries
    genuinely independent information via a 6-D Hotelling T² gate.

Protocol (frozen before execution)
    T1. Compute per-surah mean adjacent-verse Jaccard (word-sets after
        diacritic stripping) for ALL units.
    T2. Phase-1 acceptance: Cohen's d ≤ −0.30 AND MW p_less < 1e-5
        on Band-A.
    T3. 6-D Hotelling T²: append Jaccard as 6th column to the locked
        X_QURAN (68×5) and X_CTRL_POOL (2509×5).
        Gate: T²_6D ≥ T²_5D × 6/5 = 4268.81 AND per-dim gain ≥ 1.0.
    T4. Root-level Jaccard (CamelTools roots) as secondary check.
    T5. Per-corpus breakdown of Jaccard effect.

Pre-registered thresholds
    ACCEPT_AS_6TH_CHANNEL:       Phase-1 pass AND Hotelling gate pass
    SIGNIFICANT_BUT_REDUNDANT:   Phase-1 pass AND Hotelling gate fail
    FAILS:                       Phase-1 fail

Reads (integrity-checked):
    phase_06_phi_m.pkl -> X_QURAN, X_CTRL_POOL, CORPORA, FEATS

Writes ONLY under results/experiments/exp67_adjacent_jaccard/
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

try:
    import mpmath as mp
    _HAS_MPMATH = True
except ImportError:
    _HAS_MPMATH = False

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

EXP = "exp67_adjacent_jaccard"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Pre-registered parameters (frozen before any run)
FIVE_D_T2_BASELINE = 3557.339454504635
GATE_RATIO = 6.0 / 5.0
GATE_THRESHOLD = FIVE_D_T2_BASELINE * GATE_RATIO  # = 4268.81
RIDGE_LAMBDA = 1e-6

# Phase-1 thresholds
D_THRESHOLD = -0.30        # Cohen's d ≤ this
MW_P_THRESHOLD = 1e-5      # MW p_less < this
PER_DIM_GAIN_MIN = 1.0     # per-dim gain ratio ≥ this

# Tashkeel regex for stripping diacritics
_TASHKEEL = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
_TATWEEL = '\u0640'


# ---------------------------------------------------------------------------
# Jaccard helpers
# ---------------------------------------------------------------------------
def _strip(text: str) -> str:
    """Strip tashkeel and tatweel, collapse whitespace."""
    return re.sub(r'\s+', ' ', _TASHKEEL.sub('', text.replace(_TATWEEL, ''))).strip()


def _word_set(verse: str) -> set[str]:
    """Word set from a stripped verse."""
    return set(_strip(verse).split())


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if len(union) == 0:
        return 1.0
    return len(a & b) / len(union)


def _adjacent_jaccard(verses: list[str]) -> float:
    """Mean Jaccard between adjacent verse word-sets."""
    if len(verses) < 2:
        return float("nan")
    sets = [_word_set(v) for v in verses]
    jaccs = [_jaccard(sets[i], sets[i + 1]) for i in range(len(sets) - 1)]
    return float(np.mean(jaccs))


# ---------------------------------------------------------------------------
# Root-level Jaccard (secondary)
# ---------------------------------------------------------------------------
def _root_adjacent_jaccard(verses: list[str]) -> float:
    """Mean Jaccard over root-sets of adjacent verses."""
    try:
        from src.roots import extract_roots
    except ImportError:
        return float("nan")

    if len(verses) < 2:
        return float("nan")

    root_sets = []
    for v in verses:
        stripped = _strip(v)
        words = stripped.split()
        roots = set()
        for w in words:
            try:
                r = extract_roots(w)
                if r:
                    roots.add(r[0] if isinstance(r, (list, tuple)) else r)
            except Exception:
                pass
        root_sets.append(roots)

    jaccs = [_jaccard(root_sets[i], root_sets[i + 1])
             for i in range(len(root_sets) - 1)]
    return float(np.mean(jaccs)) if jaccs else float("nan")


# ---------------------------------------------------------------------------
# Hotelling T² (byte-exact from exp49)
# ---------------------------------------------------------------------------
def _hotelling_t2(XA: np.ndarray, XB: np.ndarray,
                  ridge: float = RIDGE_LAMBDA) -> tuple[float, float, int, int]:
    nA, p = XA.shape
    nB = XB.shape[0]
    mA, mB = XA.mean(0), XB.mean(0)
    SA = np.cov(XA.T, ddof=1)
    SB = np.cov(XB.T, ddof=1)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / max(1, (nA + nB - 2))
    Spi = np.linalg.inv(Sp + ridge * np.eye(p))
    diff = mA - mB
    T2 = float((nA * nB / (nA + nB)) * diff @ Spi @ diff)
    df1, df2 = p, nA + nB - p - 1
    F = ((nA + nB - p - 1) / ((nA + nB - 2) * p)) * T2
    return T2, float(F), int(df1), int(df2)


def _f_tail_p(F: float, df1: int, df2: int) -> dict:
    p_val = float(stats.f.sf(F, df1, df2))
    scipy_log10 = float(stats.f.logsf(F, df1, df2) / math.log(10))
    hp_log10 = None
    if _HAS_MPMATH and (not math.isfinite(scipy_log10) or p_val == 0.0):
        mp.mp.dps = 80
        F_mp = mp.mpf(F)
        df1_mp, df2_mp = mp.mpf(df1), mp.mpf(df2)
        x = df2_mp / (df2_mp + df1_mp * F_mp)
        sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
        hp_log10 = float(mp.log10(sf))
    return {"p_F_tail": p_val, "scipy_log10_p": scipy_log10,
            "hp_log10_p": hp_log10}


# ---------------------------------------------------------------------------
# Effect size helpers
# ---------------------------------------------------------------------------
def _cohen_d(a: list[float], b: list[float]) -> float:
    a = [x for x in a if math.isfinite(x)]
    b = [x for x in b if math.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = np.mean(a), np.mean(b)
    sa, sb = np.std(a, ddof=1), np.std(b, ddof=1)
    sp = math.sqrt((sa**2 + sb**2) / 2)
    return float((ma - mb) / sp) if sp > 1e-12 else 0.0


def _mw_p(a: list[float], b: list[float], alt: str = "less") -> float:
    a = [x for x in a if math.isfinite(x)]
    b = [x for x in b if math.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        _, p = stats.mannwhitneyu(a, b, alternative=alt)
        return float(p)
    except Exception:
        return float("nan")


# ---------------------------------------------------------------------------
# Build 6-D matrix (row-aligned with phase_06 X_QURAN / X_CTRL_POOL)
# ---------------------------------------------------------------------------
def _build_6d(corpus_name: str, corpora: dict, feats: dict,
              band_lo: int, band_hi: int, feat_cols: list[str],
              ) -> tuple[np.ndarray, list[str], int]:
    """Build 6-D matrix: first 5 cols from FEATS, 6th = adjacent Jaccard.
    Row order matches _X_for() iteration (Band-A filter on FEATS records)."""
    units = corpora.get(corpus_name, []) or []
    by_label: dict[str, object] = {}
    for i, u in enumerate(units):
        lab = getattr(u, "label", f"_idx_{i}")
        by_label[lab] = u

    recs = [r for r in feats.get(corpus_name, []) or []
            if band_lo <= r["n_verses"] <= band_hi]

    X = np.zeros((len(recs), len(feat_cols) + 1), dtype=float)
    labels: list[str] = []
    n_nan = 0
    for i, r in enumerate(recs):
        X[i, :-1] = [r[c] for c in feat_cols]
        label = r.get("label", "")
        labels.append(label)
        u = by_label.get(label)
        if u is None:
            X[i, -1] = float("nan")
            n_nan += 1
            continue
        v = _adjacent_jaccard(u.verses)
        if not np.isfinite(v):
            X[i, -1] = float("nan")
            n_nan += 1
        else:
            X[i, -1] = v
    return X, labels, n_nan


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q_5D = np.asarray(state["X_QURAN"], dtype=float)
    X_C_5D = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    corpora = state["CORPORA"]
    feats_data = state["FEATS"]

    print(f"[{EXP}] X_QURAN {X_Q_5D.shape}, X_CTRL_POOL {X_C_5D.shape}")
    print(f"[{EXP}] Band-A: [{band_lo}, {band_hi}]")

    # --- T1: Compute Jaccard for ALL units (not just Band-A) ---
    print(f"\n[{EXP}] === T1: Adjacent-verse Jaccard ===")
    all_q_jac = []
    quran_units = corpora["quran"]
    for u in quran_units:
        j = _adjacent_jaccard(u.verses)
        all_q_jac.append({"label": u.label, "n_verses": len(u.verses),
                          "jaccard": j})

    all_c_jac = {}
    for cname in ARABIC_CTRL:
        units = corpora.get(cname, [])
        jacs = []
        for u in units:
            j = _adjacent_jaccard(u.verses)
            jacs.append({"label": u.label, "n_verses": len(u.verses),
                         "jaccard": j})
        all_c_jac[cname] = jacs

    # Band-A subsets for Phase-1 test
    q_jac_banda = [r["jaccard"] for r in all_q_jac
                   if band_lo <= r["n_verses"] <= band_hi
                   and math.isfinite(r["jaccard"])]
    c_jac_banda = []
    for cname in ctrl_pool:
        for r in all_c_jac.get(cname, []):
            if band_lo <= r["n_verses"] <= band_hi and math.isfinite(r["jaccard"]):
                c_jac_banda.append(r["jaccard"])

    print(f"[{EXP}] Band-A Quran Jaccard: n={len(q_jac_banda)}, "
          f"mean={np.mean(q_jac_banda):.4f}, std={np.std(q_jac_banda, ddof=1):.4f}")
    print(f"[{EXP}] Band-A Ctrl  Jaccard: n={len(c_jac_banda)}, "
          f"mean={np.mean(c_jac_banda):.4f}, std={np.std(c_jac_banda, ddof=1):.4f}")

    # --- T2: Phase-1 acceptance ---
    d_obs = _cohen_d(q_jac_banda, c_jac_banda)
    mw_p_obs = _mw_p(q_jac_banda, c_jac_banda, "less")
    phase1_pass = (d_obs <= D_THRESHOLD) and (mw_p_obs < MW_P_THRESHOLD)

    print(f"\n[{EXP}] === T2: Phase-1 ===")
    print(f"[{EXP}] Cohen's d = {d_obs:+.4f} (threshold ≤ {D_THRESHOLD})")
    print(f"[{EXP}] MW p_less = {mw_p_obs:.3e} (threshold < {MW_P_THRESHOLD:.0e})")
    print(f"[{EXP}] Phase-1: {'PASS' if phase1_pass else 'FAIL'}")

    # --- T5: Per-corpus breakdown ---
    print(f"\n[{EXP}] === T5: Per-corpus Jaccard ===")
    per_corpus = {}
    for cname in ARABIC_CTRL:
        cj = [r["jaccard"] for r in all_c_jac.get(cname, [])
              if math.isfinite(r["jaccard"])]
        if len(cj) < 2:
            continue
        d_c = _cohen_d(q_jac_banda if cname in ctrl_pool else
                       [r["jaccard"] for r in all_q_jac if math.isfinite(r["jaccard"])],
                       cj)
        per_corpus[cname] = {
            "n": len(cj),
            "mean": round(float(np.mean(cj)), 4),
            "std": round(float(np.std(cj, ddof=1)), 4),
            "cohen_d_vs_quran": round(d_c, 4),
        }
        print(f"  {cname:20s}: n={len(cj):5d}  mean={np.mean(cj):.4f}  "
              f"d={d_c:+.3f}")

    # --- T3: 6-D Hotelling (only if Phase-1 passes) ---
    T2_5D = T2_6D = F_6D = per_dim_gain = 0.0
    df1_6D = df2_6D = 0
    p6 = {}
    hotelling_pass = False

    if phase1_pass:
        print(f"\n[{EXP}] === T3: 6-D Hotelling T² gate ===")

        # Build 6-D matrices in canonical iteration order
        XQ6, q_labels, q_nan = _build_6d(
            "quran", corpora, feats_data, band_lo, band_hi, feat_cols)
        assert np.allclose(XQ6[:, :-1], X_Q_5D), "Row-alignment check FAILED"
        print(f"[{EXP}] XQ6 {XQ6.shape}  n_nan_6th={q_nan}")

        ctrl_parts = []
        for name in ctrl_pool:
            Xc, _, n_nan = _build_6d(
                name, corpora, feats_data, band_lo, band_hi, feat_cols)
            if len(Xc) == 0:
                continue
            ctrl_parts.append(Xc)
        XC6 = np.vstack(ctrl_parts)
        assert np.allclose(XC6[:, :-1], X_C_5D), "Row-alignment check FAILED"

        # Drop NaN rows
        q_valid = np.isfinite(XQ6[:, -1])
        c_valid = np.isfinite(XC6[:, -1])
        XQ6c = XQ6[q_valid]
        XC6c = XC6[c_valid]
        print(f"[{EXP}] After NaN drop: Quran={XQ6c.shape[0]}, Ctrl={XC6c.shape[0]}")

        # 5-D baseline
        T2_5D, F_5D, df1_5D, df2_5D = _hotelling_t2(X_Q_5D, X_C_5D)
        print(f"[{EXP}] 5-D T²={T2_5D:.4f}  (locked={FIVE_D_T2_BASELINE:.4f})")

        # 6-D
        T2_6D, F_6D, df1_6D, df2_6D = _hotelling_t2(XQ6c, XC6c)
        p6 = _f_tail_p(F_6D, df1_6D, df2_6D)

        per_dim_5D = T2_5D / 5.0
        per_dim_6D = T2_6D / 6.0
        per_dim_gain = per_dim_6D / max(per_dim_5D, 1e-12)
        delta_T2 = T2_6D - T2_5D

        hotelling_pass = (T2_6D >= GATE_THRESHOLD) and (per_dim_gain >= PER_DIM_GAIN_MIN)

        print(f"[{EXP}] 6-D T²={T2_6D:.4f}  gate={GATE_THRESHOLD:.4f}")
        print(f"[{EXP}] ΔT²={delta_T2:+.4f}  per-dim gain={per_dim_gain:.4f}")
        print(f"[{EXP}] F={F_6D:.4f}  p={p6.get('p_F_tail', 'N/A')}")
        print(f"[{EXP}] Hotelling gate: {'PASS' if hotelling_pass else 'FAIL'}")
    else:
        print(f"\n[{EXP}] Skipping Hotelling gate (Phase-1 failed)")

    # --- T4: Root-level Jaccard (secondary, quick sample) ---
    print(f"\n[{EXP}] === T4: Root-level Jaccard (sample) ===")
    root_q_sample = []
    for u in quran_units[:20]:  # Sample first 20 surahs for speed
        rj = _root_adjacent_jaccard(u.verses)
        if math.isfinite(rj):
            root_q_sample.append(rj)
    if root_q_sample:
        print(f"[{EXP}] Root Jaccard (Quran sample, n={len(root_q_sample)}): "
              f"mean={np.mean(root_q_sample):.4f}")
    else:
        print(f"[{EXP}] Root Jaccard: could not compute (CamelTools not available?)")

    # --- Verdict ---
    if phase1_pass and hotelling_pass:
        verdict = "ACCEPT_AS_6TH_CHANNEL"
    elif phase1_pass:
        verdict = "SIGNIFICANT_BUT_REDUNDANT"
    else:
        verdict = "FAILS"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Phase-1: d={d_obs:+.4f}, MW p={mw_p_obs:.3e} → "
          f"{'PASS' if phase1_pass else 'FAIL'}")
    if phase1_pass:
        print(f"  Hotelling: T²_6D={T2_6D:.4f}, gate={GATE_THRESHOLD:.4f}, "
              f"gain={per_dim_gain:.4f} → {'PASS' if hotelling_pass else 'FAIL'}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H18 — Adjacent-verse Jaccard anti-repetition: "
                      "is it an independent 6th channel?",
        "schema_version": 1,
        "T1_jaccard": {
            "quran_banda_mean": round(float(np.mean(q_jac_banda)), 6),
            "quran_banda_std": round(float(np.std(q_jac_banda, ddof=1)), 6),
            "quran_banda_n": len(q_jac_banda),
            "ctrl_banda_mean": round(float(np.mean(c_jac_banda)), 6),
            "ctrl_banda_std": round(float(np.std(c_jac_banda, ddof=1)), 6),
            "ctrl_banda_n": len(c_jac_banda),
        },
        "T2_phase1": {
            "cohen_d": round(d_obs, 6),
            "mw_p_less": mw_p_obs,
            "d_threshold": D_THRESHOLD,
            "mw_threshold": MW_P_THRESHOLD,
            "pass": phase1_pass,
        },
        "T3_hotelling": {
            "T2_5D": round(T2_5D, 4),
            "T2_6D": round(T2_6D, 4),
            "gate_threshold": round(GATE_THRESHOLD, 4),
            "per_dim_gain": round(per_dim_gain, 4),
            "F_6D": round(F_6D, 4),
            "df": [df1_6D, df2_6D],
            **p6,
            "pass": hotelling_pass,
        },
        "T4_root_jaccard": {
            "quran_sample_mean": round(float(np.mean(root_q_sample)), 4)
            if root_q_sample else None,
            "n_sample": len(root_q_sample),
        },
        "T5_per_corpus": per_corpus,
        "verdict": {
            "verdict": verdict,
            "prereg": {
                "ACCEPT_AS_6TH_CHANNEL": "Phase-1 pass AND Hotelling gate pass",
                "SIGNIFICANT_BUT_REDUNDANT": "Phase-1 pass AND Hotelling gate fail",
                "FAILS": "Phase-1 fail",
            },
        },
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
