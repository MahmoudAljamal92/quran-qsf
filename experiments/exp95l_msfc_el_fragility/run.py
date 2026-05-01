"""
exp95l_msfc_el_fragility — H45 (MSFC sub-gate 2C Quran-amplification).

For each Arabic corpus C in phase_06_phi_m, compute:
    p_max(C) = max over l in 28-letter alphabet of
               (verses ending in l) / (total verses with valid final letter)
    EL_fragility(C) = p_max(C) * (27/28) + (1 - p_max(C)) * (1/28)

H45 (locked in PREREG.md): Quran has the strictly largest EL_fragility
among the 7 Arabic corpora, by a margin > 1.5x over the next-ranked
corpus.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp95l_msfc_el_fragility/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95l_msfc_el_fragility/
      exp95l_msfc_el_fragility.json (receipt)
      per_corpus_summary.csv (rank, p_max, EL_fragility, ...)
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    letters_28,
)

EXP = "exp95l_msfc_el_fragility"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "49cea95bade2dea3dd79c1cf29f5d9c98545d7d50b2cebf2ff44dc6f6debf965"
)

# Frozen constants (must match PREREG §4)
EPS_TOP1 = 1.5
MIN_VERSES_PER_CORPUS = 100
ARABIC_POOL = (
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "ksucca",
    "arabic_bible",
    "hindawi",
)
PMAX_QURAN_TARGET = 0.501
PMAX_QURAN_TOL = 0.02
EMPIRICAL_N_SAMPLES = 10_000
EMPIRICAL_TOL = 0.01
RNG_SEED = 95_000  # frozen RNG seed for reproducibility


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> None:
    out_dir = safe_output_dir(EXP)
    t0 = time.time()
    rng = random.Random(RNG_SEED)

    # ---- 1. Lock PREREG hash ----
    actual_hash = _sha256(PREREG_PATH)
    if actual_hash != EXPECTED_PREREG_HASH:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift:\n"
            f"  expected: {EXPECTED_PREREG_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"REFUSING TO RUN."
        )

    # ---- 2. Load corpora ----
    print(f"[{EXP}] loading corpus phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # ---- 3. Per-corpus verse-final-letter distribution ----
    print(f"[{EXP}] tallying verse-final letters per corpus...")
    per_corpus: dict[str, dict[str, Any]] = {}
    # Cache per-corpus verse-final letter list for empirical sampling
    finals_by_corpus: dict[str, list[str]] = {}

    for cname in ARABIC_POOL:
        items = CORPORA.get(cname, [])
        finals: list[str] = []
        n_units = 0
        n_verses_total = 0
        n_verses_valid = 0
        for u in items:
            n_units += 1
            for v in u.verses:
                n_verses_total += 1
                v_letters = letters_28(v)
                if len(v_letters) >= 1:
                    finals.append(v_letters[-1])
                    n_verses_valid += 1

        finals_by_corpus[cname] = finals
        if n_verses_valid == 0:
            per_corpus[cname] = {
                "n_units": n_units,
                "n_verses_total": n_verses_total,
                "n_verses_valid": 0,
                "p_max": None,
                "p_max_letter": None,
                "EL_fragility": None,
                "EL_fragility_empirical": None,
                "_excluded_no_valid_verses": True,
            }
            continue

        ctr = Counter(finals)
        p_max_letter, p_max_count = ctr.most_common(1)[0]
        p_max = p_max_count / n_verses_valid

        # Analytical EL_fragility
        el_fragility = p_max * (27.0 / 28.0) + (1.0 - p_max) * (1.0 / 28.0)

        # Empirical EL_fragility: sample EMPIRICAL_N_SAMPLES (verse-index,
        # new-letter) pairs uniformly; count fraction where the verse-final
        # letter equivalence-class flips (was-pmax vs new-pmax).
        # Since substitutions are at the verse-final position with uniform
        # over 27 alternative letters, we use:
        #   for each sample:
        #     pick verse i uniform from finals
        #     pick new letter uniform from {28 letters} - {finals[i]}
        #     was = (finals[i] == p_max_letter)
        #     now = (new == p_max_letter)
        #     flip = (was != now)
        # Empirical EL_fragility = mean(flip).
        # Use 28-letter alphabet derived from observed letters across all
        # corpora (the union of letters_28 outputs over all verse-finals).
        # We construct the 28 set lazily from the corpus.
        n_flips = 0
        all_letters_set: set[str] = set()
        for fc in finals_by_corpus.values():
            all_letters_set.update(fc)
        all_letters = sorted(all_letters_set)
        # Sanity: 28-letter alphabet expected; report actual size
        n_alpha = len(all_letters)
        if n_alpha < 2:
            empirical = None
        else:
            for _ in range(EMPIRICAL_N_SAMPLES):
                i = rng.randrange(len(finals))
                old = finals[i]
                # uniform over alphabet excluding old
                new = old
                while new == old:
                    new = all_letters[rng.randrange(n_alpha)]
                was = (old == p_max_letter)
                now = (new == p_max_letter)
                if was != now:
                    n_flips += 1
            empirical = n_flips / EMPIRICAL_N_SAMPLES

        per_corpus[cname] = {
            "n_units": n_units,
            "n_verses_total": n_verses_total,
            "n_verses_valid": n_verses_valid,
            "n_alphabet_letters_observed": n_alpha,
            "p_max": float(p_max),
            "p_max_letter": p_max_letter,
            "p_max_count": int(p_max_count),
            "EL_fragility": float(el_fragility),
            "EL_fragility_empirical": (
                float(empirical) if empirical is not None else None
            ),
            "EL_fragility_analytical_minus_empirical": (
                float(el_fragility - empirical)
                if empirical is not None else None
            ),
        }
        print(
            f"[{EXP}]   {cname}: n_verses={n_verses_valid:6d}, "
            f"p_max={p_max:.4f} ({p_max_letter!r}), "
            f"EL_frag(an)={el_fragility:.4f}, "
            f"EL_frag(em)={empirical:.4f}"
        )

    # ---- 4. Audit hooks ----
    audit_pmax_quran_drift = False
    audit_pmax_quran_value = per_corpus.get("quran", {}).get("p_max")
    if audit_pmax_quran_value is not None:
        if abs(audit_pmax_quran_value - PMAX_QURAN_TARGET) > PMAX_QURAN_TOL:
            audit_pmax_quran_drift = True

    audit_emp_an_disagree = []
    for cname, summary in per_corpus.items():
        diff = summary.get("EL_fragility_analytical_minus_empirical")
        if diff is not None and abs(diff) > EMPIRICAL_TOL:
            audit_emp_an_disagree.append({"corpus": cname, "diff": diff})

    # ---- 5. Verdict ladder ----
    eligible: list[tuple[str, float]] = []
    for cname, summary in per_corpus.items():
        if summary.get("EL_fragility") is None:
            continue
        if summary.get("n_verses_valid", 0) < MIN_VERSES_PER_CORPUS:
            continue
        eligible.append((cname, summary["EL_fragility"]))
    eligible.sort(key=lambda x: -x[1])

    verdict = "UNDETERMINED"
    quran_rank = None
    quran_frag = None
    next_corpus = None
    next_frag = None
    margin_ratio = None

    if audit_pmax_quran_drift:
        verdict = "FAIL_audit_pmax_quran_drift"
    else:
        for ix, (cname, fr) in enumerate(eligible):
            if cname == "quran":
                quran_rank = ix + 1
                quran_frag = fr
                if ix + 1 < len(eligible):
                    next_corpus = eligible[ix + 1][0]
                    next_frag = eligible[ix + 1][1]
                break

        if quran_rank is None:
            verdict = "FAIL_quran_not_eligible"
        elif quran_rank != 1:
            verdict = "FAIL_quran_not_top_1"
        else:
            if next_frag is None or next_frag <= 0:
                margin_ratio = float("inf")
                verdict = "PASS_quran_strict_max"
            else:
                margin_ratio = quran_frag / next_frag
                if margin_ratio > EPS_TOP1:
                    verdict = "PASS_quran_strict_max"
                else:
                    verdict = "PARTIAL_quran_top_1_within_eps"

    # ---- 6. Receipt ----
    elapsed = time.time() - t0
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H45",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "EPS_TOP1": EPS_TOP1,
            "MIN_VERSES_PER_CORPUS": MIN_VERSES_PER_CORPUS,
            "ARABIC_POOL": list(ARABIC_POOL),
            "PMAX_QURAN_TARGET": PMAX_QURAN_TARGET,
            "PMAX_QURAN_TOL": PMAX_QURAN_TOL,
            "EMPIRICAL_N_SAMPLES": EMPIRICAL_N_SAMPLES,
            "EMPIRICAL_TOL": EMPIRICAL_TOL,
            "RNG_SEED": RNG_SEED,
        },
        "per_corpus": per_corpus,
        "ranking": [
            {"rank": ix + 1, "corpus": cname, "EL_fragility": fr}
            for ix, (cname, fr) in enumerate(eligible)
        ],
        "quran_rank": quran_rank,
        "quran_EL_fragility": quran_frag,
        "next_corpus": next_corpus,
        "next_EL_fragility": next_frag,
        "margin_ratio_quran_over_next": margin_ratio,
        "audit": {
            "pmax_quran_value": audit_pmax_quran_value,
            "pmax_quran_target": PMAX_QURAN_TARGET,
            "pmax_quran_tol": PMAX_QURAN_TOL,
            "pmax_quran_drift_violated": audit_pmax_quran_drift,
            "empirical_analytical_disagreements": audit_emp_an_disagree,
        },
        "wall_time_s": round(elapsed, 2),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    receipt_path = out_dir / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    csv_path = out_dir / "per_corpus_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "rank", "corpus", "n_units", "n_verses_valid",
            "p_max", "p_max_letter", "EL_fragility",
            "EL_fragility_empirical",
        ])
        for ix, (cname, fr) in enumerate(eligible):
            row = per_corpus[cname]
            w.writerow([
                ix + 1, cname, row["n_units"], row["n_verses_valid"],
                row["p_max"], row["p_max_letter"], row["EL_fragility"],
                row.get("EL_fragility_empirical"),
            ])
        for cname, summary in per_corpus.items():
            if summary.get("EL_fragility") is None or summary.get(
                "n_verses_valid", 0
            ) < MIN_VERSES_PER_CORPUS:
                w.writerow([
                    "excl", cname, summary.get("n_units", 0),
                    summary.get("n_verses_valid", 0),
                    summary.get("p_max", ""),
                    summary.get("p_max_letter", ""),
                    summary.get("EL_fragility", ""),
                    summary.get("EL_fragility_empirical", ""),
                ])

    print(f"\n[{EXP}] verdict: {verdict}")
    if quran_rank is not None:
        print(
            f"[{EXP}] quran rank = {quran_rank}, "
            f"EL_fragility = {quran_frag:.4f}"
        )
        if next_corpus is not None:
            print(
                f"[{EXP}] next corpus = {next_corpus}, "
                f"EL_fragility = {next_frag:.4f}, "
                f"margin ratio = {margin_ratio:.3f}"
            )
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] csv:     {csv_path}")
    print(f"[{EXP}] elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
