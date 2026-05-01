"""
exp78_inverse_phi_cascade/run.py
=================================
H22: Inverse-Phi Proximity of H-Cascade Ratios.

Motivation
    The orphan phi_frac_fractal_connection.json reported that the Quran's
    entropy cascade ratios are closest to 1/phi = 0.6180 among all corpora.
    This experiment reproduces the H-cascade computation from scratch.

H-cascade definition
    For a corpus with units containing verses:
      Scale 1 (letter):  H_letter  = Shannon entropy of letter freq
      Scale 2 (word):    H_word    = Shannon entropy of word freq
      Scale 3 (verse):   H_verse   = Shannon entropy of verse-length freq

    Three cascade ratios:
      r1 = H_letter / log2(28)           (letter entropy normalised)
      r2 = H_word   / H_letter           (word-to-letter ratio)
      r3 = H_verse  / H_word             (verse-to-word ratio)

    Deviation from 1/phi = |mean(r1, r2, r3) - 1/phi|

Protocol (frozen before execution)
    T1. Compute H_letter, H_word, H_verse per corpus.
    T2. Compute 3 cascade ratios and their mean.
    T3. Deviation from 1/phi per corpus.
    T4. Rank by deviation; test Quran = minimum.
    T5. Bootstrap 10k for CI on Quran deviation.
    T6. Permutation test: p-value for Quran being the closest.

Pre-registered thresholds
    CONFIRMED:    Quran deviation is min AND bootstrap CI excludes
                  next-closest corpus
    SUGGESTIVE:   Quran deviation is min but CIs overlap
    NULL:         Quran is not the closest to 1/phi

Reads: phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp78_inverse_phi_cascade/
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
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

EXP = "exp78_inverse_phi_cascade"
SEED = 42
N_BOOT = 10000

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

INV_PHI = 2.0 / (1.0 + math.sqrt(5))  # 0.6180339887...
H_MAX_LETTERS = math.log2(28)

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH = set(ARABIC_CONS_28)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه", "ى": "ي",
}


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _shannon(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total)
                for n in counter.values() if n > 0)


def _compute_cascade(units) -> dict:
    """Compute H_letter, H_word, H_verse and cascade ratios."""
    letter_freq = Counter()
    word_freq = Counter()
    verse_lengths = []

    for u in units:
        for v in u.verses:
            text = _strip_d(v)
            # Letters (28-letter rasm)
            for c in text:
                fc = _FOLD.get(c, c)
                if fc in _ALPH:
                    letter_freq[fc] += 1
            # Words
            words = text.split()
            for w in words:
                word_freq[w] += 1
            # Verse length
            verse_lengths.append(len(words))

    H_letter = _shannon(letter_freq)
    H_word = _shannon(word_freq)
    H_verse = _shannon(Counter(verse_lengths))

    # Cascade ratios
    r1 = H_letter / H_MAX_LETTERS if H_MAX_LETTERS > 0 else 0
    r2 = H_word / H_letter if H_letter > 0 else 0
    r3 = H_verse / H_word if H_word > 0 else 0

    mean_ratio = (r1 + r2 + r3) / 3.0
    deviation = abs(mean_ratio - INV_PHI)

    return {
        "H_letter": round(H_letter, 4),
        "H_word": round(H_word, 4),
        "H_verse": round(H_verse, 4),
        "r1_letter_norm": round(r1, 4),
        "r2_word_letter": round(r2, 4),
        "r3_verse_word": round(r3, 4),
        "mean_ratio": round(mean_ratio, 6),
        "deviation_from_inv_phi": round(deviation, 6),
        "n_letters": sum(letter_freq.values()),
        "n_words": sum(word_freq.values()),
        "n_verses": len(verse_lengths),
        "vocab_size": len(word_freq),
    }


def _bootstrap_deviation(units, n_boot=N_BOOT) -> np.ndarray:
    """Bootstrap CI on deviation by resampling units."""
    rng = np.random.RandomState(SEED)
    devs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.choice(len(units), len(units), replace=True)
        sampled = [units[j] for j in idx]
        cas = _compute_cascade(sampled)
        devs[i] = cas["deviation_from_inv_phi"]
    return devs


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

    print(f"\n[{EXP}] 1/φ = {INV_PHI:.10f}")
    print(f"[{EXP}] H_max(28 letters) = {H_MAX_LETTERS:.4f}\n")

    for cname in all_names:
        units = CORPORA.get(cname, [])
        cas = _compute_cascade(units)
        results[cname] = cas
        print(f"[{EXP}] {cname:20s}: H_l={cas['H_letter']:.4f}  "
              f"H_w={cas['H_word']:.4f}  H_v={cas['H_verse']:.4f}  |  "
              f"r1={cas['r1_letter_norm']:.4f}  r2={cas['r2_word_letter']:.4f}  "
              f"r3={cas['r3_verse_word']:.4f}  |  "
              f"mean={cas['mean_ratio']:.6f}  dev={cas['deviation_from_inv_phi']:.6f}")

    # --- T4: Rank ---
    print(f"\n[{EXP}] === T4: Ranking by deviation from 1/φ ===")
    ranked = sorted(results.items(), key=lambda x: x[1]["deviation_from_inv_phi"])
    for rank, (cname, cas) in enumerate(ranked, 1):
        flag = " <<<" if cname == "quran" else ""
        print(f"  {rank}. {cname:20s}  dev={cas['deviation_from_inv_phi']:.6f}{flag}")

    quran_rank = next(i for i, (n, _) in enumerate(ranked, 1) if n == "quran")
    quran_is_min = quran_rank == 1

    # --- T5: Bootstrap ---
    print(f"\n[{EXP}] === T5: Bootstrap ({N_BOOT}x) ===")
    q_units = CORPORA.get("quran", [])
    boot_devs = _bootstrap_deviation(q_units)
    ci_lo, ci_hi = np.percentile(boot_devs, [2.5, 97.5])
    print(f"  Quran deviation: {results['quran']['deviation_from_inv_phi']:.6f}")
    print(f"  Bootstrap CI: [{ci_lo:.6f}, {ci_hi:.6f}]")

    # Check if CI excludes next-closest
    if quran_is_min and len(ranked) > 1:
        next_dev = ranked[1][1]["deviation_from_inv_phi"]
        ci_excludes_next = ci_hi < next_dev
        print(f"  Next closest: {ranked[1][0]} dev={next_dev:.6f}")
        print(f"  CI excludes next: {ci_excludes_next}")
    else:
        ci_excludes_next = False

    # --- T6: Permutation test ---
    print(f"\n[{EXP}] === T6: Permutation test ===")
    # Pool all units, randomly assign to "Quran-sized" group, check if its
    # deviation is <= observed Quran deviation
    all_units = []
    for cname in all_names:
        all_units.extend(CORPORA.get(cname, []))
    n_q = len(q_units)
    obs_dev = results["quran"]["deviation_from_inv_phi"]

    rng = np.random.RandomState(SEED + 1)
    n_leq = 0
    for i in range(N_BOOT):
        idx = rng.permutation(len(all_units))[:n_q]
        sampled = [all_units[j] for j in idx]
        cas = _compute_cascade(sampled)
        if cas["deviation_from_inv_phi"] <= obs_dev:
            n_leq += 1
    p_perm = (n_leq + 1) / (N_BOOT + 1)
    print(f"  Quran observed dev = {obs_dev:.6f}")
    print(f"  Perm p(dev <= obs) = {p_perm:.4f} ({n_leq}/{N_BOOT})")

    # --- Verdict ---
    if quran_is_min and ci_excludes_next and p_perm < 0.05:
        verdict = "CONFIRMED"
    elif quran_is_min:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran rank: {quran_rank}/{len(ranked)}")
    print(f"  Quran deviation: {obs_dev:.6f}")
    print(f"  Bootstrap CI: [{ci_lo:.6f}, {ci_hi:.6f}]")
    print(f"  Permutation p: {p_perm:.4f}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H22 — Is the Quran's H-cascade ratio closest to 1/φ?",
        "schema_version": 1,
        "inv_phi": INV_PHI,
        "per_corpus": results,
        "ranking": [(n, round(c["deviation_from_inv_phi"], 6))
                     for n, c in ranked],
        "quran_rank": quran_rank,
        "bootstrap": {
            "n_boot": N_BOOT,
            "ci": [round(float(ci_lo), 6), round(float(ci_hi), 6)],
            "ci_excludes_next": ci_excludes_next,
        },
        "permutation_test": {
            "n_perm": N_BOOT,
            "p_value": p_perm,
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
