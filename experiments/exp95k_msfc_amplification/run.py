"""
exp95k_msfc_amplification — H44 (Multi-Scale Forgery Cascade Gate-2A
Quran-amplification claim).

For each Arabic corpus C in phase_06_phi_m, designate C as "canon" and
all other Arabic corpora's units as "peers". Compute
    safety_margin(C) := min over u in C, p not-in C of
                        bigram_l1(hist_2(letters_28(u)),
                                  hist_2(letters_28(p))) / 2

H44 (locked in PREREG.md): Quran has the strictly largest safety margin
across the 7 Arabic corpora in phase_06_phi_m, by > 5% over next.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp95k_msfc_amplification/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95k_msfc_amplification/
      exp95k_msfc_amplification.json (receipt)
      per_corpus_summary.csv (rank, n_units, min, p05, median)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    letters_28,
)

EXP = "exp95k_msfc_amplification"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "a6331765ac99eb9388fb82b811326310c86b77e971d0522050a8107dab3ac822"
)

# Frozen constants (must match PREREG §4)
TAU_HIGH = 2.0
EPS_TOP1 = 0.05
MIN_UNITS_PER_CORPUS = 20
ARABIC_POOL = (
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "ksucca",
    "arabic_bible",
    "hindawi",
)
QURAN_REPRO_TARGET = 73.5
QURAN_REPRO_TOL = 0.5


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bigrams_of(s: str) -> Counter:
    return Counter(s[i : i + 2] for i in range(len(s) - 1))


def main() -> None:
    out_dir = safe_output_dir(EXP)
    t0 = time.time()

    # ---- 1. Lock PREREG hash ----
    actual_hash = _sha256(PREREG_PATH)
    if actual_hash != EXPECTED_PREREG_HASH:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift:\n"
            f"  expected: {EXPECTED_PREREG_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"REFUSING TO RUN."
        )

    # ---- 2. Load corpora and build per-unit bigram counters ----
    print(f"[{EXP}] loading corpus phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Build per-corpus list of (label, str, bigram_counter)
    by_corpus: dict[str, list[tuple[str, str, Counter]]] = {}
    for cname in ARABIC_POOL:
        items = CORPORA.get(cname, [])
        bucket: list[tuple[str, str, Counter]] = []
        for u in items:
            label = getattr(u, "label", f"{cname}:?")
            try:
                pstr = letters_28(" ".join(u.verses))
            except Exception:
                continue
            if len(pstr) >= 2:
                bucket.append((label, pstr, bigrams_of(pstr)))
        by_corpus[cname] = bucket
        print(f"[{EXP}]   {cname}: {len(bucket)} units (>=2 letters)")

    # ---- 3. Build universal bigram vocabulary and dense vectors ----
    print(f"[{EXP}] vectorising bigram counters...")
    all_bigrams: set[str] = set()
    for cname in ARABIC_POOL:
        for _label, _pstr, bg in by_corpus.get(cname, []):
            all_bigrams.update(bg.keys())
    vocab = sorted(all_bigrams)
    bigram_idx = {bg: i for i, bg in enumerate(vocab)}
    V = len(vocab)
    print(f"[{EXP}]   vocab size V = {V}")

    by_corpus_vec: dict[str, np.ndarray] = {}
    by_corpus_labels: dict[str, list[str]] = {}
    for cname in ARABIC_POOL:
        bucket = by_corpus.get(cname, [])
        if not bucket:
            by_corpus_vec[cname] = np.zeros((0, V), dtype=np.int32)
            by_corpus_labels[cname] = []
            continue
        mat = np.zeros((len(bucket), V), dtype=np.int32)
        labels: list[str] = []
        for i, (label, _pstr, bg) in enumerate(bucket):
            for k, cnt in bg.items():
                mat[i, bigram_idx[k]] = cnt
            labels.append(label)
        by_corpus_vec[cname] = mat
        by_corpus_labels[cname] = labels

    # ---- 4. Compute safety_margin(C) for each C in pool ----
    per_corpus: dict[str, dict[str, Any]] = {}
    print(f"[{EXP}] computing safety margins (numpy-vectorised)...")
    for canon_name in ARABIC_POOL:
        C_mat = by_corpus_vec[canon_name]
        n_canon = C_mat.shape[0]
        if n_canon == 0:
            per_corpus[canon_name] = {
                "n_units": 0,
                "safety_margin": None,
                "delta_p05": None,
                "delta_median": None,
                "_excluded_lt_min_units": True,
            }
            continue

        # Build peer matrix = vstack of all OTHER Arabic corpora's vectors
        peer_blocks = [
            by_corpus_vec[p] for p in ARABIC_POOL
            if p != canon_name and by_corpus_vec[p].shape[0] > 0
        ]
        if not peer_blocks:
            per_corpus[canon_name] = {
                "n_units": n_canon,
                "safety_margin": None,
                "delta_p05": None,
                "delta_median": None,
                "_excluded_no_valid_peers": True,
            }
            continue
        peers = np.vstack(peer_blocks)
        n_peers = peers.shape[0]

        # For each canon unit, distance to each peer in one numpy op
        per_unit_min = np.empty(n_canon, dtype=np.float64)
        for i in range(n_canon):
            d = np.abs(C_mat[i] - peers).sum(axis=1) // 2  # (n_peers,) int
            per_unit_min[i] = float(d.min())

        per_corpus[canon_name] = {
            "n_units": n_canon,
            "n_peer_units": int(n_peers),
            "safety_margin": float(per_unit_min.min()),
            "delta_p05": float(np.percentile(per_unit_min, 5)),
            "delta_median": float(np.median(per_unit_min)),
            "delta_max": float(per_unit_min.max()),
        }
        print(
            f"[{EXP}]   {canon_name}: safety_margin = "
            f"{per_corpus[canon_name]['safety_margin']:.2f}, "
            f"p05 = {per_corpus[canon_name]['delta_p05']:.2f}, "
            f"median = {per_corpus[canon_name]['delta_median']:.2f}"
        )

    # ---- 4. Audit hooks ----
    audit_quran_drift = False
    audit_quran_drift_value = None
    if per_corpus.get("quran", {}).get("safety_margin") is not None:
        audit_quran_drift_value = per_corpus["quran"]["safety_margin"]
        if abs(audit_quran_drift_value - QURAN_REPRO_TARGET) > QURAN_REPRO_TOL:
            audit_quran_drift = True

    eligible: list[tuple[str, float]] = []
    for cname, summary in per_corpus.items():
        if summary.get("safety_margin") is None:
            continue
        if summary.get("n_units", 0) < MIN_UNITS_PER_CORPUS:
            continue
        eligible.append((cname, summary["safety_margin"]))
    eligible.sort(key=lambda x: -x[1])

    # ---- 5. Verdict ladder ----
    verdict = "UNDETERMINED"
    quran_rank = None
    quran_margin = None
    next_corpus = None
    next_margin = None
    margin_ratio = None

    if audit_quran_drift:
        verdict = "FAIL_audit_quran_drift"
    else:
        for ix, (cname, sm) in enumerate(eligible):
            if cname == "quran":
                quran_rank = ix + 1
                quran_margin = sm
                if ix + 1 < len(eligible):
                    next_corpus = eligible[ix + 1][0]
                    next_margin = eligible[ix + 1][1]
                break

        if quran_rank is None:
            verdict = "FAIL_quran_not_eligible"
        elif quran_rank != 1:
            verdict = "FAIL_quran_not_top_1"
        else:
            if next_margin is None or next_margin <= 0:
                margin_ratio = float("inf")
                verdict = "PASS_quran_strict_max"
            else:
                margin_ratio = (quran_margin - next_margin) / next_margin
                if margin_ratio > EPS_TOP1:
                    verdict = "PASS_quran_strict_max"
                else:
                    verdict = "PARTIAL_quran_top_1_within_eps"

    # ---- 6. Receipt ----
    elapsed = time.time() - t0
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H44",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "TAU_HIGH": TAU_HIGH,
            "EPS_TOP1": EPS_TOP1,
            "MIN_UNITS_PER_CORPUS": MIN_UNITS_PER_CORPUS,
            "ARABIC_POOL": list(ARABIC_POOL),
            "QURAN_REPRO_TARGET": QURAN_REPRO_TARGET,
            "QURAN_REPRO_TOL": QURAN_REPRO_TOL,
        },
        "per_corpus": per_corpus,
        "ranking": [
            {"rank": ix + 1, "corpus": cname, "safety_margin": sm}
            for ix, (cname, sm) in enumerate(eligible)
        ],
        "quran_rank": quran_rank,
        "quran_safety_margin": quran_margin,
        "next_corpus": next_corpus,
        "next_safety_margin": next_margin,
        "margin_ratio_quran_over_next": margin_ratio,
        "audit": {
            "quran_drift_value": audit_quran_drift_value,
            "quran_drift_target": QURAN_REPRO_TARGET,
            "quran_drift_tol": QURAN_REPRO_TOL,
            "quran_drift_violated": audit_quran_drift,
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
            "rank", "corpus", "n_units", "n_peer_units",
            "safety_margin", "delta_p05", "delta_median", "delta_max",
        ])
        for ix, (cname, sm) in enumerate(eligible):
            row = per_corpus[cname]
            w.writerow([
                ix + 1, cname, row["n_units"], row.get("n_peer_units", ""),
                row["safety_margin"], row["delta_p05"],
                row["delta_median"], row.get("delta_max", ""),
            ])
        # also append excluded corpora
        for cname, summary in per_corpus.items():
            if summary.get("safety_margin") is None or summary.get(
                "n_units", 0
            ) < MIN_UNITS_PER_CORPUS:
                w.writerow([
                    "excl", cname, summary.get("n_units", 0),
                    summary.get("n_peer_units", ""),
                    summary.get("safety_margin", ""),
                    summary.get("delta_p05", ""),
                    summary.get("delta_median", ""),
                    summary.get("delta_max", ""),
                ])

    print(f"\n[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] csv:     {csv_path}")
    print(f"[{EXP}] elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
