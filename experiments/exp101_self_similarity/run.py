"""
exp101_self_similarity/run.py
==============================
Re-test C5 ("self-similar / mutashābih", Q 39:23) using cross-scale
structural stability of the 5-D feature fingerprint.

Primary: cosine distance between short-surah centroid and long-surah centroid.
Secondary: mean intra-corpus feature CV.

Pre-registered in PREREG.md (frozen 2026-04-27, v7.9-cand patch H pre-V2).

Reads:  phase_06_phi_m.pkl :: state[CORPORA]
Writes: results/experiments/exp101_self_similarity/exp101_self_similarity.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import features_5d, ARABIC_CONN  # noqa: E402

# ---------------------------------------------------------------------------
# Constants (frozen per PREREG §4)
# ---------------------------------------------------------------------------
EXP = "exp101_self_similarity"
CORPORA_NAMES = ["quran", "poetry_jahili", "poetry_islami",
                 "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
MIN_VERSES = 2
FEATURE_DIM = 5
SEED = 101000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """1 - cos(a, b). Returns 0 if identical direction, 2 if opposite."""
    dot = np.dot(a, b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0  # undefined, treat as maximally dissimilar
    return float(1.0 - dot / (na * nb))


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
    pre_check = self_check_begin()
    t0 = time.time()

    prereg_hash = sha256_of(_HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash}")

    audit_failures: list[str] = []

    # -------------------------------------------------------------------
    # Load corpus data
    # -------------------------------------------------------------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl …")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    corpus_units: dict[str, list] = {}
    for cn in CORPORA_NAMES:
        units = CORPORA.get(cn, [])
        filtered = [u for u in units if len(u.verses) >= MIN_VERSES]
        corpus_units[cn] = filtered
        print(f"[{EXP}]   {cn}: {len(filtered)} units "
              f"({len(units)} raw, {len(units)-len(filtered)} dropped)")
        if len(filtered) < 10:
            audit_failures.append(f"A1: {cn} has only {len(filtered)} units (< 10)")

    # -------------------------------------------------------------------
    # Compute 5-D features for every unit
    # -------------------------------------------------------------------
    print(f"[{EXP}] Computing 5-D features for all units …")
    corpus_feats: dict[str, list[tuple[int, np.ndarray]]] = {}
    # Each entry: list of (n_verses, feature_vector)

    n_total_units = 0
    n_valid_units = 0
    for cn, units in corpus_units.items():
        feats = []
        for u in units:
            n_total_units += 1
            try:
                f = features_5d(u.verses)
                if np.any(np.isnan(f)) or np.any(np.isinf(f)):
                    continue
                feats.append((len(u.verses), f))
                n_valid_units += 1
            except Exception:
                continue
        corpus_feats[cn] = feats
        print(f"[{EXP}]   {cn}: {len(feats)} valid feature vectors")

    # Audit A2
    valid_rate = n_valid_units / n_total_units if n_total_units > 0 else 0
    print(f"[{EXP}] A2: feature success rate = {valid_rate:.4f} "
          f"({n_valid_units}/{n_total_units})")
    if valid_rate < 0.99:
        audit_failures.append(f"A2: feature success rate {valid_rate:.4f} < 0.99")

    # -------------------------------------------------------------------
    # Primary: cross-scale cosine distance
    # -------------------------------------------------------------------
    print(f"[{EXP}] Computing cross-scale cosine distances …")
    cos_dists: dict[str, float] = {}
    split_info: dict[str, dict] = {}

    for cn, feats in corpus_feats.items():
        if len(feats) < 4:
            cos_dists[cn] = float("inf")
            split_info[cn] = {"n_short": 0, "n_long": 0, "median_nv": 0}
            continue

        n_verses_list = [nv for nv, _ in feats]
        median_nv = float(np.median(n_verses_list))

        short_feats = [f for nv, f in feats if nv <= median_nv]
        long_feats = [f for nv, f in feats if nv > median_nv]

        # If split is too uneven, use strict median
        if len(short_feats) < 2 or len(long_feats) < 2:
            # Fallback: sort and split in half
            sorted_feats = sorted(feats, key=lambda x: x[0])
            mid = len(sorted_feats) // 2
            short_feats = [f for _, f in sorted_feats[:mid]]
            long_feats = [f for _, f in sorted_feats[mid:]]

        n_short = len(short_feats)
        n_long = len(long_feats)

        # Audit A3
        if n_short < 5 or n_long < 5:
            audit_failures.append(
                f"A3: {cn} SHORT={n_short} LONG={n_long} (need ≥ 5 each)")

        mu_short = np.mean(short_feats, axis=0)
        mu_long = np.mean(long_feats, axis=0)
        d = cosine_distance(mu_short, mu_long)
        cos_dists[cn] = d
        split_info[cn] = {
            "n_short": n_short, "n_long": n_long,
            "median_nv": median_nv,
            "mu_short": mu_short.tolist(),
            "mu_long": mu_long.tolist(),
        }
        print(f"[{EXP}]   {cn}: D = {d:.6f}  "
              f"(short={n_short}, long={n_long}, median_nv={median_nv:.0f})")

    # Rank (smallest D = rank 1 = most self-similar)
    cos_ranked = sorted(cos_dists.items(), key=lambda x: x[1])
    cos_ranks = {cn: i + 1 for i, (cn, _) in enumerate(cos_ranked)}

    print(f"[{EXP}] Primary ranks (smallest cosine distance = rank 1):")
    for cn, d in cos_ranked:
        print(f"[{EXP}]   #{cos_ranks[cn]}  {cn}: {d:.6f}")

    # -------------------------------------------------------------------
    # Secondary: mean intra-corpus feature CV
    # -------------------------------------------------------------------
    print(f"[{EXP}] Computing secondary metric (feature CV) …")
    mean_cvs: dict[str, float] = {}

    for cn, feats in corpus_feats.items():
        if len(feats) < 3:
            mean_cvs[cn] = float("inf")
            continue
        mat = np.array([f for _, f in feats])  # (n_units, 5)
        means = mat.mean(axis=0)
        stds = mat.std(axis=0, ddof=1)
        # CV per feature, avoid divide by zero
        cvs = []
        for i in range(FEATURE_DIM):
            if abs(means[i]) > 1e-12:
                cvs.append(stds[i] / abs(means[i]))
            else:
                cvs.append(0.0)
        mean_cvs[cn] = float(np.mean(cvs))
        print(f"[{EXP}]   {cn}: mean CV = {mean_cvs[cn]:.4f}")

    cv_ranked = sorted(mean_cvs.items(), key=lambda x: x[1])
    cv_ranks = {cn: i + 1 for i, (cn, _) in enumerate(cv_ranked)}

    print(f"[{EXP}] Secondary ranks (lower CV = rank 1):")
    for cn, cv in cv_ranked:
        print(f"[{EXP}]   #{cv_ranks[cn]}  {cn}: {cv:.4f}")

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    quran_cos_rank = cos_ranks["quran"]
    quran_cos_d = cos_dists["quran"]
    cos_pass = (quran_cos_rank == 1)

    # Strict: ratio of Quran D to next-ranked D >= 1.5×
    strict_pass = False
    ratio_to_next = None
    if cos_pass and len(cos_ranked) > 1:
        next_d = cos_ranked[1][1]
        if quran_cos_d > 0:
            ratio_to_next = next_d / quran_cos_d
            strict_pass = ratio_to_next >= 1.5
        elif next_d > 0:
            ratio_to_next = float("inf")
            strict_pass = True

    # Self-check
    post_check = self_check_end(pre_check, EXP)
    if post_check.get("drift"):
        audit_failures.append(f"self_check: {post_check['drift']}")

    if audit_failures:
        verdict = f"FAIL_audit_{'_'.join(a.split(':')[0] for a in audit_failures)}"
    elif strict_pass:
        verdict = "PASS_H56_strict"
    elif cos_pass:
        verdict = "PASS_H56_rank_1"
    else:
        verdict = "FAIL_not_rank_1"

    print(f"\n[{EXP}] === RESULTS ===")
    print(f"  Quran cosine distance = {quran_cos_d:.6f}")
    print(f"  Quran primary rank    = {quran_cos_rank}/7")
    print(f"  Quran secondary (CV)  = {mean_cvs['quran']:.4f} (rank {cv_ranks['quran']}/7)")
    if ratio_to_next is not None:
        print(f"  Ratio to next         = {ratio_to_next:.2f}×")
    print(f"  verdict = {verdict}")

    # -------------------------------------------------------------------
    # Write receipt
    # -------------------------------------------------------------------
    record = {
        "experiment": EXP,
        "prereg_sha256": prereg_hash,
        "hypothesis": "H56",
        "primary_cosine_distance": {
            "distances": {cn: cos_dists[cn] for cn in CORPORA_NAMES},
            "ranks": {cn: cos_ranks[cn] for cn in CORPORA_NAMES},
            "quran_rank": quran_cos_rank,
            "quran_distance": quran_cos_d,
            "ratio_to_next": ratio_to_next,
            "split_info": split_info,
        },
        "secondary_feature_cv": {
            "mean_cvs": {cn: mean_cvs[cn] for cn in CORPORA_NAMES},
            "ranks": {cn: cv_ranks[cn] for cn in CORPORA_NAMES},
            "quran_rank": cv_ranks["quran"],
        },
        "audit": {
            "a2_feature_success_rate": valid_rate,
            "failures": audit_failures,
        },
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }

    receipt_path = out / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] receipt: {receipt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
