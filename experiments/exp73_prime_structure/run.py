"""
exp73_prime_structure/run.py
=============================
H13: Prime-Number Structure in Surah/Verse Counts.

Motivation
    The Quran has 114 surahs and 6236 verses. Are prime-length surahs
    distributed non-randomly? Does any numerical property of the
    verse-count sequence relate to a known number-theoretic quantity?

Protocol (frozen before execution)
    T1. Extract verse counts per surah from CORPORA.
    T2. Identify which are prime. Compute fraction.
    T3. Compare to expected prime density (Prime Number Theorem).
    T4. Runs test: are prime-length surahs clustered or dispersed?
    T5. Sum of prime-length surah verse counts; sum of positions.
    T6. Compare to Bible (chapter verse counts) as control.
    T7. Permutation test: shuffle verse counts among surahs 10k
        times, compute fraction of shuffles with ≥ as many primes.

Pre-registered thresholds
    SIGNIFICANT:    runs test p < 0.01 or permutation p < 0.01
    NULL:           no significant pattern

Reads: phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp73_prime_structure/
"""
from __future__ import annotations

import json
import math
import sys
import time
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

EXP = "exp73_prime_structure"
SEED = 42
N_PERM = 10000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _prime_density_expected(max_n: int) -> float:
    """Expected fraction of primes up to max_n (PNT: ~1/ln(n))."""
    if max_n < 2:
        return 0.0
    # Count actual primes up to max_n
    count = sum(1 for i in range(2, max_n + 1) if _is_prime(i))
    return count / max_n


def _runs_test(binary_seq: list[int]) -> dict:
    """Wald-Wolfowitz runs test on binary sequence."""
    n = len(binary_seq)
    if n < 10:
        return {"runs": 0, "z": float("nan"), "p": float("nan")}

    n1 = sum(binary_seq)
    n0 = n - n1
    if n0 == 0 or n1 == 0:
        return {"runs": 1, "z": float("nan"), "p": float("nan")}

    # Count runs
    runs = 1
    for i in range(1, n):
        if binary_seq[i] != binary_seq[i - 1]:
            runs += 1

    # Expected runs and variance
    mu = 1 + 2 * n0 * n1 / n
    var = (2 * n0 * n1 * (2 * n0 * n1 - n)) / (n**2 * (n - 1))
    if var <= 0:
        return {"runs": runs, "z": float("nan"), "p": float("nan")}

    z = (runs - mu) / math.sqrt(var)
    # Two-tailed p-value
    from scipy import stats
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return {"runs": runs, "z": round(float(z), 4), "p": float(p)}


def _analyse_corpus(name: str, verse_counts: list[int]) -> dict:
    """Full prime analysis for one corpus."""
    n = len(verse_counts)
    primes_mask = [_is_prime(vc) for vc in verse_counts]
    n_prime = sum(primes_mask)
    frac_prime = n_prime / n if n > 0 else 0.0

    # Expected density based on max verse count
    max_vc = max(verse_counts) if verse_counts else 0
    expected_frac = _prime_density_expected(max_vc)

    # Positions of prime-length units
    prime_positions = [i + 1 for i, p in enumerate(primes_mask) if p]
    prime_verse_counts = [vc for vc, p in zip(verse_counts, primes_mask) if p]

    # Runs test
    binary = [1 if p else 0 for p in primes_mask]
    runs = _runs_test(binary)

    # Sums
    sum_prime_vc = sum(prime_verse_counts)
    sum_prime_pos = sum(prime_positions)

    return {
        "n_units": n,
        "n_prime": n_prime,
        "frac_prime": round(frac_prime, 4),
        "expected_frac": round(expected_frac, 4),
        "max_verse_count": max_vc,
        "prime_positions": prime_positions[:20],  # truncate for JSON
        "sum_prime_verse_counts": sum_prime_vc,
        "sum_prime_positions": sum_prime_pos,
        "runs_test": runs,
        "verse_counts_sample": verse_counts[:20],
    }


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

    results = {}

    # --- Quran ---
    quran_units = CORPORA.get("quran", [])
    q_vc = [len(u.verses) for u in quran_units]
    results["quran"] = _analyse_corpus("quran", q_vc)

    print(f"\n[{EXP}] === Quran ===")
    r = results["quran"]
    print(f"  114 surahs, verse counts range: {min(q_vc)}-{max(q_vc)}")
    print(f"  Prime-length surahs: {r['n_prime']}/114 = {r['frac_prime']:.1%}")
    print(f"  Expected prime density (PNT, up to {r['max_verse_count']}): "
          f"{r['expected_frac']:.1%}")
    print(f"  Sum of prime verse counts: {r['sum_prime_verse_counts']}")
    print(f"  Sum of prime positions: {r['sum_prime_positions']}")
    print(f"  Total verses: {sum(q_vc)}")
    print(f"  Runs test: z={r['runs_test']['z']}, p={r['runs_test']['p']:.4f}")

    # Check notable numbers
    total = sum(q_vc)
    print(f"\n  Number checks:")
    print(f"    114 prime? {_is_prime(114)} (114 = 2×3×19)")
    print(f"    6236 prime? {_is_prime(6236)} (6236 = 4×1559, 1559 prime? {_is_prime(1559)})")
    print(f"    Sum prime VCs = {r['sum_prime_verse_counts']}, "
          f"prime? {_is_prime(r['sum_prime_verse_counts'])}")

    # --- T7: Permutation test ---
    print(f"\n[{EXP}] === T7: Permutation test ({N_PERM}x) ===")
    rng = np.random.RandomState(SEED)
    observed_n_prime = r["n_prime"]
    perm_counts = np.empty(N_PERM, dtype=int)
    for i in range(N_PERM):
        shuffled = rng.permutation(q_vc)
        perm_counts[i] = sum(1 for vc in shuffled if _is_prime(vc))

    # p-value: fraction with >= observed
    p_perm = float(np.mean(perm_counts >= observed_n_prime))
    print(f"  Observed prime count: {observed_n_prime}")
    print(f"  Permutation mean: {perm_counts.mean():.1f} ± {perm_counts.std():.1f}")
    print(f"  p(≥{observed_n_prime}) = {p_perm:.4f}")

    # --- Bible comparison ---
    bible_units = CORPORA.get("arabic_bible", [])
    b_vc = [len(u.verses) for u in bible_units]
    results["arabic_bible"] = _analyse_corpus("arabic_bible", b_vc)

    print(f"\n[{EXP}] === Arabic Bible ===")
    rb = results["arabic_bible"]
    print(f"  {rb['n_units']} chapters, verse counts range: "
          f"{min(b_vc) if b_vc else 0}-{max(b_vc) if b_vc else 0}")
    print(f"  Prime-length chapters: {rb['n_prime']}/{rb['n_units']} = "
          f"{rb['frac_prime']:.1%}")
    print(f"  Runs test: z={rb['runs_test']['z']}, p={rb['runs_test']['p']:.4f}")

    # --- All corpora summary ---
    print(f"\n[{EXP}] === Summary across corpora ===")
    for cname in ["quran", "arabic_bible"]:
        rc = results[cname]
        print(f"  {cname:20s}: {rc['n_prime']}/{rc['n_units']} prime "
              f"({rc['frac_prime']:.1%})  runs z={rc['runs_test']['z']}  "
              f"p={rc['runs_test']['p']:.4f}")

    # --- Verdict ---
    q_runs_p = r["runs_test"]["p"]
    significant = (q_runs_p < 0.01) or (p_perm < 0.01)
    verdict = "SIGNIFICANT" if significant else "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Runs test p = {q_runs_p:.4f} (threshold < 0.01)")
    print(f"  Permutation p = {p_perm:.4f} (threshold < 0.01)")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H13 — Is there a non-random prime-number structure "
                      "in the Quran's surah/verse counts?",
        "schema_version": 1,
        "per_corpus": results,
        "permutation_test": {
            "n_perm": N_PERM,
            "observed_n_prime": int(observed_n_prime),
            "perm_mean": round(float(perm_counts.mean()), 2),
            "perm_std": round(float(perm_counts.std()), 2),
            "p_value": p_perm,
        },
        "number_checks": {
            "n_surahs_114": {"prime": False, "factorization": "2×3×19"},
            "n_verses_6236": {"prime": False, "factorization": "4×1559"},
            "1559_prime": _is_prime(1559),
        },
        "verdict": {
            "verdict": verdict,
            "prereg": {
                "SIGNIFICANT": "runs p < 0.01 OR perm p < 0.01",
                "NULL": "no significant pattern",
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
