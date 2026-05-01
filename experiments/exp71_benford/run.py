"""
exp71_benford/run.py
=====================
H8: Benford's Law on Verse Word-Counts.

Motivation
    Benford's law (first-digit law) appears in many natural datasets.
    Verse word-counts are a natural measurement of text structure.
    Does the Quran conform more or less than controls?

Protocol (frozen before execution)
    T1. Extract all verse word-counts per corpus (raw, not Band-A).
    T2. Compute first-digit distribution (digits 1-9).
    T3. Chi-squared GOF test vs Benford expected P(d)=log10(1+1/d).
    T4. KL divergence from Benford per corpus.
    T5. Second-digit analysis (Stigler generalization).
    T6. Rank corpora by Benford conformity.
    T7. Cohen's d on KL(Benford) between Quran and controls.

Pre-registered thresholds
    BENFORD_CONFORMING:  chi2 p > 0.05 for Quran AND p < 0.05 for ≥4 controls
    BENFORD_DEVIATING:   chi2 p < 0.05 for Quran AND direction is unique
    INCONCLUSIVE:        no clear pattern

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp71_benford/
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
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

EXP = "exp71_benford"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

POETRY_CORPORA = {"poetry_jahili", "poetry_islami", "poetry_abbasi"}


# ---------------------------------------------------------------------------
# Benford helpers
# ---------------------------------------------------------------------------
def _benford_expected() -> np.ndarray:
    """Expected first-digit probabilities P(d) = log10(1 + 1/d), d=1..9."""
    return np.array([math.log10(1 + 1/d) for d in range(1, 10)])


def _benford_second_expected() -> np.ndarray:
    """Expected second-digit probabilities (Stigler)."""
    probs = np.zeros(10)  # digits 0-9
    for d1 in range(1, 10):
        for d2 in range(0, 10):
            probs[d2] += math.log10(1 + 1 / (10 * d1 + d2))
    return probs


def _first_digits(word_counts: list[int]) -> list[int]:
    """Extract first digit of each word count (skip zeros)."""
    digits = []
    for wc in word_counts:
        if wc > 0:
            digits.append(int(str(wc)[0]))
    return digits


def _second_digits(word_counts: list[int]) -> list[int]:
    """Extract second digit of each word count (skip single-digit counts)."""
    digits = []
    for wc in word_counts:
        s = str(wc)
        if len(s) >= 2:
            digits.append(int(s[1]))
    return digits


def _digit_distribution(digits: list[int], n_bins: int, start: int = 1) -> np.ndarray:
    """Count distribution of digits into n_bins starting from start."""
    counts = np.zeros(n_bins, dtype=float)
    ctr = Counter(digits)
    for i in range(n_bins):
        counts[i] = ctr.get(start + i, 0)
    return counts


def _chi2_test(observed: np.ndarray, expected_probs: np.ndarray) -> dict:
    """Chi-squared GOF test."""
    n = observed.sum()
    if n < 10:
        return {"chi2": float("nan"), "p": float("nan"), "n": int(n)}
    expected = expected_probs * n
    # Avoid zero expected
    mask = expected > 0
    chi2, p = stats.chisquare(observed[mask], expected[mask])
    return {"chi2": round(float(chi2), 4), "p": float(p), "n": int(n)}


def _kl_divergence(observed: np.ndarray, expected_probs: np.ndarray) -> float:
    """KL(observed || Benford). observed is counts, not probabilities."""
    n = observed.sum()
    if n < 10:
        return float("nan")
    p_obs = observed / n
    # Add small epsilon to avoid log(0)
    eps = 1e-12
    p_obs = np.clip(p_obs, eps, None)
    q = np.clip(expected_probs, eps, None)
    return float(np.sum(p_obs * np.log(p_obs / q)))


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

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    benford_1st = _benford_expected()
    benford_2nd = _benford_second_expected()

    print(f"[{EXP}] Benford 1st-digit expected: {[f'{p:.4f}' for p in benford_1st]}")

    def _extract_word_counts(cname, units, pair_hemistichs=False):
        """Extract verse word-counts. If pair_hemistichs, concat
        consecutive verse-pairs for poetry corpora (hemistich→bayt)."""
        all_wc = []
        for u in units:
            verses = list(u.verses)
            if pair_hemistichs and cname in POETRY_CORPORA:
                # Pair consecutive hemistichs into full bayts
                i = 0
                while i < len(verses) - 1:
                    wc = len(verses[i].split()) + len(verses[i+1].split())
                    if wc > 0:
                        all_wc.append(wc)
                    i += 2
                if i == len(verses) - 1:  # odd trailing hemistich
                    wc = len(verses[i].split())
                    if wc > 0:
                        all_wc.append(wc)
            else:
                for v in verses:
                    wc = len(v.split())
                    if wc > 0:
                        all_wc.append(wc)
        return all_wc

    def _run_benford(label, all_wc):
        """Run Benford analysis on a word-count list, return result dict."""
        fd = _first_digits(all_wc)
        sd = _second_digits(all_wc)
        fd_counts = _digit_distribution(fd, 9, start=1)
        chi2_1st = _chi2_test(fd_counts, benford_1st)
        kl_1st = _kl_divergence(fd_counts, benford_1st)
        sd_counts = _digit_distribution(sd, 10, start=0)
        chi2_2nd = _chi2_test(sd_counts, benford_2nd)
        kl_2nd = _kl_divergence(sd_counts, benford_2nd)
        n_1st = fd_counts.sum()
        props_1st = fd_counts / n_1st if n_1st > 0 else fd_counts
        return {
            "n_verses": len(all_wc),
            "first_digit": {
                "counts": fd_counts.astype(int).tolist(),
                "proportions": [round(float(p), 4) for p in props_1st],
                "chi2": chi2_1st,
                "kl_divergence": round(kl_1st, 6),
            },
            "second_digit": {
                "n_two_digit": int(sd_counts.sum()),
                "chi2": chi2_2nd,
                "kl_divergence": round(kl_2nd, 6),
            },
        }, props_1st

    # === MODE 1: Raw hemistichs (original) ===
    print(f"\n{'='*60}")
    print(f"[{EXP}] MODE 1: Raw verses (hemistichs as-is)")
    print(f"{'='*60}")
    results = {}
    for cname in ["quran"] + ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        all_wc = _extract_word_counts(cname, units, pair_hemistichs=False)
        res, props_1st = _run_benford(cname, all_wc)
        results[cname] = res
        conf = "CONFORMS" if res["first_digit"]["chi2"]["p"] > 0.05 else "DEVIATES"
        print(f"  {cname:20s}: n={len(all_wc):6d}  "
              f"\u03c7\u00b2={res['first_digit']['chi2']['chi2']:8.2f}  "
              f"p={res['first_digit']['chi2']['p']:.3e}  "
              f"KL={res['first_digit']['kl_divergence']:.6f}  \u2192 {conf}")

    # === MODE 2: Paired bayts for poetry ===
    print(f"\n{'='*60}")
    print(f"[{EXP}] MODE 2: Poetry paired into bayts (2 hemistichs → 1 line)")
    print(f"{'='*60}")
    results_paired = {}
    for cname in ["quran"] + ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        all_wc = _extract_word_counts(cname, units, pair_hemistichs=True)
        res, props_1st = _run_benford(cname, all_wc)
        results_paired[cname] = res
        tag = " [PAIRED]" if cname in POETRY_CORPORA else ""
        conf = "CONFORMS" if res["first_digit"]["chi2"]["p"] > 0.05 else "DEVIATES"
        print(f"  {cname:20s}{tag}: n={len(all_wc):6d}  "
              f"\u03c7\u00b2={res['first_digit']['chi2']['chi2']:8.2f}  "
              f"p={res['first_digit']['chi2']['p']:.3e}  "
              f"KL={res['first_digit']['kl_divergence']:.6f}  \u2192 {conf}")

    # === Comparison ===
    print(f"\n[{EXP}] === Hemistich vs Bayt comparison (poetry only) ===")
    for cname in POETRY_CORPORA:
        kl_raw = results[cname]["first_digit"]["kl_divergence"]
        kl_pair = results_paired[cname]["first_digit"]["kl_divergence"]
        print(f"  {cname:20s}: KL_raw={kl_raw:.6f} → KL_paired={kl_pair:.6f}  "
              f"(\u0394={kl_pair - kl_raw:+.6f})")

    # Use paired results for final ranking (fairer comparison)
    use = results_paired

    # --- T6: Rank by conformity (KL divergence) ---
    print(f"\n[{EXP}] === T6: Ranking by Benford conformity (paired mode) ===")
    ranked = sorted(use.items(),
                    key=lambda x: x[1]["first_digit"]["kl_divergence"])
    for rank, (cname, res) in enumerate(ranked, 1):
        kl = res["first_digit"]["kl_divergence"]
        p = res["first_digit"]["chi2"]["p"]
        print(f"  {rank}. {cname:20s}  KL={kl:.6f}  \u03c7\u00b2 p={p:.3e}")

    # --- T7: Cohen's d on KL values ---
    q_kl = use["quran"]["first_digit"]["kl_divergence"]
    ctrl_kls = [use[c]["first_digit"]["kl_divergence"] for c in ARABIC_CTRL]
    mean_ctrl_kl = float(np.mean(ctrl_kls))
    std_ctrl_kl = float(np.std(ctrl_kls, ddof=1))
    d_kl = (q_kl - mean_ctrl_kl) / std_ctrl_kl if std_ctrl_kl > 1e-12 else 0.0

    print(f"\n[{EXP}] === T7: KL divergence comparison ===")
    print(f"  Quran KL = {q_kl:.6f}")
    print(f"  Ctrl mean KL = {mean_ctrl_kl:.6f} ± {std_ctrl_kl:.6f}")
    print(f"  Cohen's d(KL) = {d_kl:+.4f}")

    # --- Verdict ---
    q_p = use["quran"]["first_digit"]["chi2"]["p"]
    n_ctrl_deviate = sum(1 for c in ARABIC_CTRL
                         if use[c]["first_digit"]["chi2"]["p"] < 0.05)

    if q_p > 0.05 and n_ctrl_deviate >= 4:
        verdict = "BENFORD_CONFORMING"
    elif q_p < 0.05:
        verdict = "BENFORD_DEVIATING"
    else:
        verdict = "INCONCLUSIVE"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran χ² p = {q_p:.3e} ({'conforms' if q_p > 0.05 else 'deviates'})")
    print(f"  Controls deviating: {n_ctrl_deviate}/6")
    print(f"  Quran Benford-conformity rank: "
          f"{[c for c, _ in ranked].index('quran') + 1}/{len(ranked)}")
    print(f"  Cohen's d(KL) = {d_kl:+.4f}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H8 — Does the Quran's verse word-count distribution "
                      "conform to Benford's law?",
        "schema_version": 1,
        "benford_expected_1st": benford_1st.tolist(),
        "benford_expected_2nd": benford_2nd.tolist(),
        "per_corpus_raw": results,
        "per_corpus_paired": results_paired,
        "ranking_by_kl": [{"corpus": c, "kl": r["first_digit"]["kl_divergence"]}
                          for c, r in ranked],
        "kl_comparison": {
            "quran_kl": q_kl,
            "ctrl_mean_kl": round(mean_ctrl_kl, 6),
            "ctrl_std_kl": round(std_ctrl_kl, 6),
            "cohen_d": round(d_kl, 4),
        },
        "verdict": {
            "verdict": verdict,
            "quran_chi2_p": q_p,
            "n_ctrl_deviate": n_ctrl_deviate,
            "prereg": {
                "BENFORD_CONFORMING": "Quran p > 0.05 AND ≥4 controls p < 0.05",
                "BENFORD_DEVIATING": "Quran p < 0.05",
                "INCONCLUSIVE": "no clear pattern",
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
