"""
exp83_order_sensitivity/run.py
================================
H31: Negative-Control Degradation Hierarchy / Order Sensitivity Index.

Motivation
    NC3 (verse-order scramble) frequently fails the pipeline gate,
    meaning features are mostly distributional. The ratio
    OSI = d_NC3 / d_NC2 quantifies how much structure depends on
    verse ordering. If OSI_Quran is uniquely high, the canonical
    ordering carries real Quran-specific signal.

Approach (self-contained, no classifier)
    For each corpus, compute features_5d on each unit under:
      - Canonical order (baseline)
      - NC2: within-unit word shuffle (10 reps)
      - NC3: within-unit verse-order scramble (10 reps)
    Degradation = mean |Phi_M_canonical - Phi_M_perturbed| / Phi_M_canonical
    OSI = degradation_NC3 / degradation_NC2

Protocol (frozen before execution)
    T1. Compute 5D features per unit (canonical).
    T2. NC2: shuffle words within each verse, recompute features.
    T3. NC3: shuffle verse order, recompute features.
    T4. Compute degradation for NC2 and NC3.
    T5. OSI = d_NC3 / d_NC2 per corpus.
    T6. Compare Quran OSI to controls.

Pre-registered thresholds
    SIGNIFICANT:  OSI_Quran >= 1.5 * median(OSI_ctrl) AND p < 0.05
    SUGGESTIVE:   OSI_Quran > median(OSI_ctrl)
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

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
from src.features import (  # noqa: E402
    el_rate, vl_cv, cn_rate, h_el, ARABIC_CONN,
    h_cond_initials,
)

EXP = "exp83_order_sensitivity"
SEED = 42
N_REPS = 10
MIN_VERSES = 10

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _features_fast(verses: list[str]) -> np.ndarray:
    """5D features without CamelTools."""
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, ARABIC_CONN)
    hc = h_cond_initials(verses)
    he = h_el(verses)
    T = hc - he
    return np.array([el, cv, cn, hc, T])


def _nc2_word_shuffle(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle words within each verse."""
    out = []
    for v in verses:
        words = v.split()
        rng.shuffle(words)
        out.append(" ".join(words))
    return out


def _nc3_verse_shuffle(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle verse order."""
    out = list(verses)
    rng.shuffle(out)
    return out


def _feature_distance(f1: np.ndarray, f2: np.ndarray) -> float:
    """Euclidean distance between two feature vectors."""
    return float(np.linalg.norm(f1 - f2))


def _analyse_corpus(units, n_reps=N_REPS) -> dict:
    """Compute NC2/NC3 degradation and OSI for a corpus."""
    rng = random.Random(SEED)
    nc2_dists = []
    nc3_dists = []
    canonical_norms = []
    n_used = 0

    for u in units:
        if len(u.verses) < MIN_VERSES:
            continue
        n_used += 1

        f_canon = _features_fast(u.verses)
        f_norm = float(np.linalg.norm(f_canon))
        canonical_norms.append(f_norm)

        # NC2: word shuffle
        for _ in range(n_reps):
            shuffled = _nc2_word_shuffle(u.verses, rng)
            f_nc2 = _features_fast(shuffled)
            nc2_dists.append(_feature_distance(f_canon, f_nc2))

        # NC3: verse-order shuffle
        for _ in range(n_reps):
            shuffled = _nc3_verse_shuffle(u.verses, rng)
            f_nc3 = _features_fast(shuffled)
            nc3_dists.append(_feature_distance(f_canon, f_nc3))

    if not nc2_dists or not nc3_dists:
        return {"n_used": 0}

    mean_canon = np.mean(canonical_norms)
    d_nc2 = np.mean(nc2_dists)
    d_nc3 = np.mean(nc3_dists)

    # Normalised degradation
    d_nc2_norm = d_nc2 / mean_canon if mean_canon > 0 else 0
    d_nc3_norm = d_nc3 / mean_canon if mean_canon > 0 else 0

    osi = d_nc3_norm / d_nc2_norm if d_nc2_norm > 1e-10 else float("inf")

    return {
        "n_used": n_used,
        "d_nc2_raw": round(float(d_nc2), 6),
        "d_nc3_raw": round(float(d_nc3), 6),
        "d_nc2_norm": round(float(d_nc2_norm), 6),
        "d_nc3_norm": round(float(d_nc3_norm), 6),
        "osi": round(float(osi), 4),
        "mean_canon_norm": round(float(mean_canon), 6),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        t_start = time.time()
        r = _analyse_corpus(units)
        dt = time.time() - t_start
        results[cname] = r
        osi_str = f"{r['osi']:.4f}" if r.get("osi") else "N/A"
        print(f"[{EXP}] {cname:20s}: n={r['n_used']:4d}  "
              f"d_NC2={r.get('d_nc2_norm', 0):.4f}  "
              f"d_NC3={r.get('d_nc3_norm', 0):.4f}  "
              f"OSI={osi_str}  ({dt:.1f}s)")

    # --- T6: Comparison ---
    print(f"\n[{EXP}] === T6: OSI comparison ===")
    q_osi = results["quran"]["osi"]
    ctrl_osis = [results[c]["osi"] for c in ARABIC_CTRL
                 if results[c].get("osi") is not None and results[c]["n_used"] > 0]

    if ctrl_osis:
        median_ctrl = float(np.median(ctrl_osis))
        mean_ctrl = float(np.mean(ctrl_osis))
        std_ctrl = float(np.std(ctrl_osis, ddof=1))
        z_osi = (q_osi - mean_ctrl) / std_ctrl if std_ctrl > 0 else 0

        print(f"  Quran OSI = {q_osi:.4f}")
        print(f"  Ctrl OSI: median={median_ctrl:.4f}, mean={mean_ctrl:.4f}, std={std_ctrl:.4f}")
        print(f"  z(OSI) = {z_osi:+.2f}")
        print(f"  Ratio Quran / median(ctrl) = {q_osi / median_ctrl:.4f}" if median_ctrl > 0 else "")

        for c in ARABIC_CTRL:
            r = results[c]
            if r["n_used"] > 0:
                print(f"    {c:20s}: OSI={r['osi']:.4f}")

        # Mann-Whitney on per-unit basis not available since we have corpus-level OSIs
        # Use z-score for verdict
        ratio = q_osi / median_ctrl if median_ctrl > 0 else 0
    else:
        ratio = 0
        z_osi = 0

    # --- Hierarchy test ---
    print(f"\n[{EXP}] === Hierarchy d_NC2 > d_NC3 universality ===")
    hierarchy_holds = 0
    for cname in all_names:
        r = results[cname]
        if r["n_used"] == 0:
            continue
        holds = r["d_nc2_norm"] > r["d_nc3_norm"]
        hierarchy_holds += int(holds)
        flag = "✓" if holds else "✗"
        print(f"  {cname:20s}: d_NC2={r['d_nc2_norm']:.4f} vs d_NC3={r['d_nc3_norm']:.4f}  {flag}")
    n_total = sum(1 for c in all_names if results[c]["n_used"] > 0)
    print(f"  Hierarchy holds: {hierarchy_holds}/{n_total}")

    # --- Verdict ---
    if ratio >= 1.5 and abs(z_osi) >= 2.0:
        verdict = "SIGNIFICANT"
    elif q_osi > median_ctrl if ctrl_osis else False:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran OSI = {q_osi:.4f}")
    print(f"  Ctrl median OSI = {median_ctrl:.4f}" if ctrl_osis else "")
    print(f"  Ratio = {ratio:.4f}, z = {z_osi:+.2f}")
    print(f"  d_NC2 > d_NC3 universal: {hierarchy_holds}/{n_total}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H31 — Is OSI = d_NC3/d_NC2 a Quran-specific discriminator?",
        "schema_version": 1,
        "n_reps": N_REPS,
        "per_corpus": results,
        "comparison": {
            "quran_osi": q_osi,
            "ctrl_median_osi": median_ctrl if ctrl_osis else None,
            "ctrl_mean_osi": mean_ctrl if ctrl_osis else None,
            "ratio": round(ratio, 4),
            "z_osi": round(z_osi, 4),
        },
        "hierarchy_universal": {
            "holds": hierarchy_holds,
            "total": n_total,
        },
        "verdict": verdict,
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
