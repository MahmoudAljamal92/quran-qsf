"""
expC1plus_renyi2_closed_form/run.py
====================================
Closed-form Rényi-2 statement of opportunity C1 (EL_q ≈ 1/√2).

Promotes the C1 numerical coincidence

    Band-A mean EL = 0.7074  vs  1/√2 = 0.7071  (gap 0.04 %)

to the information-theoretic identity

    H_2(p̂_quran terminal-letter PMF)  ≈  1.000 bit
    Σp̂²                                ≈  0.500
    EL_q  ≈  √(Σp̂²)  ≈  1/√2  (under iid surrogate)

with bootstrap CI tested against the analytic reference 1/2.

Pre-registered in PREREG.md (2026-04-26 PRE-RUN).

Reads:
  - data/corpora/{ar,he,el,pi,sa,ae}/... via raw_loader.load_all
Writes ONLY under results/experiments/expC1plus_renyi2_closed_form/.
"""
from __future__ import annotations

import hashlib
import json
import math
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
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import raw_loader  # noqa: E402
from src.features import _terminal_alpha, el_rate  # noqa: E402

EXP = "expC1plus_renyi2_closed_form"
SEED = 42
N_BOOTSTRAP = 100_000
RENYI2_IDENTITY_BAND = (0.495, 0.505)
RENYI2_NEAR_HALF_BAND = (0.480, 0.520)
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
CROSS_TRADITION_NON_ARABIC = [
    "hebrew_tanakh", "greek_nt", "iliad_greek",
    "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
]


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _terminal_letters(units) -> list[str]:
    """Flatten all verse-final letters across every unit, ignoring
    empty / non-alphabetic finals (matches `el_rate` masking)."""
    finals: list[str] = []
    for u in units:
        for v in u.verses:
            f = _terminal_alpha(v)
            if f:
                finals.append(f)
    return finals


def _renyi_summary(letters: list[str]) -> dict:
    """Compute Σp̂², H_2, H_shannon, H_max for a flat letter sequence."""
    if not letters:
        return {
            "n": 0, "alphabet_size": 0,
            "sum_p2": float("nan"),
            "renyi2_bits": float("nan"),
            "shannon_bits": float("nan"),
            "h_max_uniform_alphabet_bits": float("nan"),
        }
    cnt = Counter(letters)
    n = sum(cnt.values())
    alphabet = sorted(cnt)
    p = np.array([cnt[c] / n for c in alphabet], dtype=np.float64)
    sum_p2 = float((p * p).sum())
    h2 = -math.log2(sum_p2) if sum_p2 > 0 else float("nan")
    h_shannon = float(-(p[p > 0] * np.log2(p[p > 0])).sum())
    h_max = math.log2(len(alphabet)) if alphabet else float("nan")
    return {
        "n": int(n),
        "alphabet_size": len(alphabet),
        "alphabet": alphabet,
        "pmf": dict(zip(alphabet, [float(x) for x in p])),
        "sum_p2": sum_p2,
        "renyi2_bits": float(h2),
        "shannon_bits": h_shannon,
        "h_max_uniform_alphabet_bits": float(h_max),
    }


def _bootstrap_sum_p2(
    letters: list[str], n_boot: int = N_BOOTSTRAP, seed: int = SEED
) -> dict:
    """Bootstrap CI on Σp̂². Resample letter sequence with replacement
    n_boot times, recompute Σp̂². Returns median, 2.5/97.5 percentiles,
    and tail probabilities w.r.t. the analytic reference 0.5."""
    n = len(letters)
    if n < 2:
        return {
            "n": 0, "median": None, "ci_lo": None, "ci_hi": None,
            "p_left_lt_half": None, "p_right_gt_half": None,
            "p_two_sided_extremity_vs_half": None,
        }
    # Encode the alphabet as integer indices for fast resampling.
    alphabet = sorted(set(letters))
    idx_of = {c: i for i, c in enumerate(alphabet)}
    arr = np.array([idx_of[c] for c in letters], dtype=np.int32)
    K = len(alphabet)
    rng = np.random.default_rng(seed)
    sums = np.empty(n_boot, dtype=np.float64)
    BATCH = 5_000
    written = 0
    while written < n_boot:
        b = min(BATCH, n_boot - written)
        idx = rng.integers(0, n, size=(b, n))
        sample = arr[idx]
        # bincount over rows
        for r in range(b):
            counts = np.bincount(sample[r], minlength=K).astype(np.float64)
            p = counts / n
            sums[written + r] = float((p * p).sum())
        written += b
    obs = sums.mean()  # not used directly but kept
    # Per-bootstrap quantiles
    ci_lo = float(np.quantile(sums, 0.025))
    ci_hi = float(np.quantile(sums, 0.975))
    p_left = float((sums < 0.5).mean())
    p_right = float((sums > 0.5).mean())
    # Two-sided "vs 0.5" tail under the bootstrap distribution
    centered = sums - sums.mean()
    abs_obs = abs(sums.mean() - 0.5)
    p_two = float((np.abs(centered) >= abs_obs).mean())
    return {
        "n": int(n),
        "n_boot": int(n_boot),
        "median": float(np.median(sums)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "p_left_lt_half": p_left,
        "p_right_gt_half": p_right,
        "p_two_sided_extremity_vs_half": p_two,
    }


def _per_surah_renyi2(units) -> dict:
    """Compute per-surah Σp̂²_s and the within-surah clustering
    residual c_s = EL_observed_s − Σp̂²_s."""
    rows = []
    for u in units:
        verses = list(u.verses)
        finals = [_terminal_alpha(v) for v in verses]
        finals_clean = [f for f in finals if f]
        n_v = len(finals_clean)
        if n_v < 2:
            continue
        cnt = Counter(finals_clean)
        N = sum(cnt.values())
        p = np.array([c / N for c in cnt.values()], dtype=np.float64)
        sum_p2 = float((p * p).sum())
        el_obs = float(el_rate(verses))
        rows.append({
            "label": getattr(u, "label", ""),
            "n_verses": len(verses),
            "n_alpha_finals": n_v,
            "el_observed": el_obs,
            "sum_p2_iid_predicted_el": sum_p2,
            "renyi2_bits": float(-math.log2(sum_p2)) if sum_p2 > 0
                           else float("nan"),
            "clustering_residual": float(el_obs - sum_p2),
        })
    return {"per_surah": rows}


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading corpora...")
    CORPORA = raw_loader.load_all(
        include_extras=True,
        include_cross_lang=True,
        include_cross_tradition=True,
    )

    # --- Quran corpus-level Rényi-2 ---
    quran_units = CORPORA.get("quran", [])
    quran_letters = _terminal_letters(quran_units)
    quran_summary = _renyi_summary(quran_letters)
    print(f"\n[{EXP}] === Quran corpus-level terminal-letter PMF ===")
    print(f"[{EXP}]   n_alpha_finals = {quran_summary['n']}")
    print(f"[{EXP}]   alphabet_size  = {quran_summary['alphabet_size']}")
    print(f"[{EXP}]   Σp̂²            = {quran_summary['sum_p2']:.6f}")
    print(f"[{EXP}]   H_2 (Rényi-2)  = {quran_summary['renyi2_bits']:.4f} bits")
    print(f"[{EXP}]   H_shannon      = {quran_summary['shannon_bits']:.4f} bits")
    print(f"[{EXP}]   H_max(uniform) = {quran_summary['h_max_uniform_alphabet_bits']:.4f} bits")

    # --- Quran bootstrap CI on Σp̂² ---
    print(f"\n[{EXP}] Bootstrap (B={N_BOOTSTRAP}) on Quran Σp̂² vs 0.5 ...")
    quran_boot = _bootstrap_sum_p2(quran_letters, N_BOOTSTRAP, SEED)
    print(f"[{EXP}]   median Σp̂² (bootstrap) = "
          f"{quran_boot['median']:.6f}")
    print(f"[{EXP}]   95 % CI                = "
          f"[{quran_boot['ci_lo']:.6f}, {quran_boot['ci_hi']:.6f}]")
    print(f"[{EXP}]   contains 0.5?          = "
          f"{quran_boot['ci_lo'] <= 0.5 <= quran_boot['ci_hi']}")
    print(f"[{EXP}]   p_two_sided_vs_0.5     = "
          f"{quran_boot['p_two_sided_extremity_vs_half']:.4f}")

    # --- Per-surah Rényi-2 ---
    per_surah = _per_surah_renyi2(quran_units)
    if per_surah["per_surah"]:
        ps = per_surah["per_surah"]
        sum_p2_band_a = [r["sum_p2_iid_predicted_el"] for r in ps
                         if 15 <= r["n_verses"] <= 100]
        el_band_a = [r["el_observed"] for r in ps
                     if 15 <= r["n_verses"] <= 100]
        clust_band_a = [r["clustering_residual"] for r in ps
                        if 15 <= r["n_verses"] <= 100]
        if sum_p2_band_a:
            mean_sum_p2_band_a = float(np.mean(sum_p2_band_a))
            mean_el_band_a = float(np.mean(el_band_a))
            mean_clust_band_a = float(np.mean(clust_band_a))
            print(f"\n[{EXP}] === Per-surah (Band-A 15..100) ===")
            print(f"[{EXP}]   n_band_a              = {len(sum_p2_band_a)}")
            print(f"[{EXP}]   mean Σp̂²_s (iid pred) = {mean_sum_p2_band_a:.4f}")
            print(f"[{EXP}]   mean EL_observed_s    = {mean_el_band_a:.4f}")
            print(f"[{EXP}]   √(mean Σp̂²_s)         = "
                  f"{math.sqrt(mean_sum_p2_band_a):.4f}")
            print(f"[{EXP}]   1/√2                  = "
                  f"{1/math.sqrt(2):.4f}")
            print(f"[{EXP}]   mean clustering c_s   = {mean_clust_band_a:+.4f}  "
                  f"(EL_obs − Σp̂²; positive = rhyme excess over iid)")

    # --- Cross-control Σp̂² ---
    print(f"\n[{EXP}] === Cross-control / cross-tradition Σp̂² ===")
    print(f"   {'corpus':<22s}  {'n':>8s}  {'alpha':>5s}  "
          f"{'Σp̂²':>8s}  {'H_2(bits)':>10s}  in_band")
    cross_results: dict = {}
    for name in ARABIC_CTRL + CROSS_TRADITION_NON_ARABIC:
        units = CORPORA.get(name, [])
        if not units:
            print(f"   {name:<22s}  MISSING")
            continue
        letters = _terminal_letters(units)
        summary = _renyi_summary(letters)
        in_strict = (
            RENYI2_IDENTITY_BAND[0] <= summary["sum_p2"]
            <= RENYI2_IDENTITY_BAND[1]
        ) if not math.isnan(summary["sum_p2"]) else False
        cross_results[name] = {
            "summary": summary,
            "in_renyi2_strict_band": in_strict,
        }
        if math.isnan(summary["sum_p2"]):
            continue
        print(f"   {name:<22s}  {summary['n']:>8d}  "
              f"{summary['alphabet_size']:>5d}  "
              f"{summary['sum_p2']:>8.4f}  "
              f"{summary['renyi2_bits']:>10.4f}  "
              f"{'YES' if in_strict else '-'}")

    # --- Pre-registered verdict ---
    quran_in_strict = (
        RENYI2_IDENTITY_BAND[0]
        <= quran_summary["sum_p2"]
        <= RENYI2_IDENTITY_BAND[1]
    )
    quran_in_partial = (
        RENYI2_NEAR_HALF_BAND[0]
        <= quran_summary["sum_p2"]
        <= RENYI2_NEAR_HALF_BAND[1]
    )

    arabic_ctrl_in_strict = [
        name for name in ARABIC_CTRL
        if cross_results.get(name, {}).get("in_renyi2_strict_band", False)
    ]

    if quran_in_strict and not arabic_ctrl_in_strict:
        verdict = "PASS_RENYI2_IDENTITY_AND_DISTINCT"
    elif quran_in_strict and arabic_ctrl_in_strict:
        verdict = "PASS_RENYI2_IDENTITY_QURAN_ONLY"
    elif quran_in_partial:
        verdict = "PARTIAL_NEAR_HALF"
    else:
        verdict = "FAIL_NOT_HALF"

    print(f"\n{'='*72}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  Quran Σp̂²              = {quran_summary['sum_p2']:.6f}")
    print(f"  Quran H_2 (bits)       = {quran_summary['renyi2_bits']:.4f}")
    print(f"  Quran in strict band   = {quran_in_strict}")
    print(f"  Quran in partial band  = {quran_in_partial}")
    print(f"  Arabic ctrls also in strict band: "
          f"{arabic_ctrl_in_strict if arabic_ctrl_in_strict else 'none'}")
    print(f"{'='*72}\n")

    elapsed = time.time() - t0

    # Strip alphabet/PMF dictionaries from cross_results to keep JSON small
    cross_results_clean = {}
    for name, rec in cross_results.items():
        s = dict(rec["summary"])
        # Keep PMF only for Quran; strip for others
        s.pop("pmf", None)
        s.pop("alphabet", None)
        cross_results_clean[name] = {
            "summary": s,
            "in_renyi2_strict_band": rec["in_renyi2_strict_band"],
        }

    # Strip per-surah for compactness; keep summary only
    per_surah_band_a = []
    if per_surah["per_surah"]:
        per_surah_band_a = [
            r for r in per_surah["per_surah"]
            if 15 <= r["n_verses"] <= 100
        ]

    band_a_summary = None
    if per_surah_band_a:
        sp = [r["sum_p2_iid_predicted_el"] for r in per_surah_band_a]
        el = [r["el_observed"] for r in per_surah_band_a]
        cl = [r["clustering_residual"] for r in per_surah_band_a]
        band_a_summary = {
            "n_band_a_surahs": len(per_surah_band_a),
            "mean_sum_p2_per_surah": float(np.mean(sp)),
            "median_sum_p2_per_surah": float(np.median(sp)),
            "mean_el_observed_per_surah": float(np.mean(el)),
            "mean_clustering_residual": float(np.mean(cl)),
            "sqrt_mean_sum_p2": float(math.sqrt(np.mean(sp))),
            "one_over_sqrt_2": float(1 / math.sqrt(2)),
        }

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_document": "experiments/expC1plus_renyi2_closed_form/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED,
            "n_bootstrap": N_BOOTSTRAP,
            "renyi2_identity_band": list(RENYI2_IDENTITY_BAND),
            "renyi2_near_half_band": list(RENYI2_NEAR_HALF_BAND),
        },
        "closed_form_quantities": {
            "claim": (
                "Σp̂² (the iid pair-collision probability of the verse-"
                "final-letter PMF) ≈ 1/2  ⟺  Rényi-2 entropy ≈ 1 bit"
            ),
            "analytic_reference_sum_p2": 0.5,
            "analytic_reference_renyi2_bits": 1.0,
            "analytic_reference_one_over_sqrt2": 1 / math.sqrt(2),
        },
        "quran_corpus_level": {
            "summary": quran_summary,
            "bootstrap_sum_p2_vs_half": quran_boot,
            "in_renyi2_strict_band": quran_in_strict,
            "in_renyi2_near_half_band": quran_in_partial,
        },
        "quran_band_a_per_surah_summary": band_a_summary,
        "cross_corpus": cross_results_clean,
        "verdict": verdict,
        "interpretation": (
            "PASS_RENYI2_IDENTITY_AND_DISTINCT means the Quran's verse-"
            "final-letter PMF satisfies the closed-form identity Σp̂² ≈ "
            "1/2 (equivalently, its Rényi-2 entropy is 1 bit) AND no "
            "Arabic-control corpus does. This converts the C1 numerical "
            "coincidence (EL_q ≈ 1/√2) to an information-theoretic "
            "statement about the corpus PMF, with a pre-registered band "
            "[0.495, 0.505] for the strict identity. PARTIAL_NEAR_HALF "
            "preserves the qualitative match within ±2 % but loses the "
            "tight identity. FAIL_NOT_HALF would falsify the closed-form "
            "framing entirely."
        ),
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
