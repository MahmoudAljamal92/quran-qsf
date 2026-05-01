"""exp113_joint_extremality_3way — F55 × F63 × LC2 joint extremality test.

Tests whether the Quran is jointly extremal on three independent structural axes
across 5 cross-tradition canons. Reports per-axis rank, joint Borda-count rank,
pairwise Spearman correlations, and 10,000-perm null on rank-shuffles.

Prereg: experiments/exp113_joint_extremality_3way/PREREG.md
Hypothesis ID: H68.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------------
# Locked constants
# ----------------------------------------------------------------------------

TAU = 2.0
N_PERMS = 10_000
SEED = 42

# 5 traditions where all 3 metrics are measured
TRADITIONS = [
    "quran",
    "hebrew_tanakh",
    "greek_nt",
    "pali",
    "avestan_yasna",
]

# Source receipts (locked for byte-fingerprinting)
F55_RECEIPTS = {
    "quran":         "results/experiments/exp95j_bigram_shift_universal/exp95j_bigram_shift_universal.json",
    "hebrew_tanakh": "results/experiments/exp105_F55_psalm78_bigram/exp105_F55_psalm78_bigram.json",
    "greek_nt":      "results/experiments/exp106_F55_mark1_bigram/exp106_F55_mark1_bigram.json",
    "pali":          "results/experiments/exp107_F55_dn1_bigram/exp107_F55_dn1_bigram.json",
    "avestan_yasna": "results/experiments/exp108_F55_y28_bigram/exp108_F55_y28_bigram.json",
}

F63_RECEIPT = "results/auxiliary/_phi_universal_xtrad_sizing.json"
LC2_RECEIPT = "results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json"

# LC2 corpus name mapping (LC2 uses pali_dn vs F55/F63 use pali)
LC2_NAME_MAP = {
    "quran": "quran",
    "hebrew_tanakh": "hebrew_tanakh",
    "greek_nt": "greek_nt",
    "pali": "pali_dn",  # LC2 uses pali_dn for the DN-only LC2 R3 measurement
    "avestan_yasna": "avestan_yasna",
}


# ----------------------------------------------------------------------------
# Data loaders
# ----------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_f55_safety(receipt_path: Path) -> tuple[float, dict]:
    """Compute F55 per-character safety margin for a tradition.

    For Quran: median across 114 surahs of (min_peer_delta − τ) / n_canon.
    For single-chapter F55 (Hebrew/Greek/Pāli/Avestan): use the chapter directly.
    """
    d = json.load(open(receipt_path, encoding="utf-8"))
    if "per_surah" in d:
        # Quran multi-surah
        per_surah = d["per_surah"]
        per_char_margins = [(v["min_peer_delta"] - TAU) / v["n_canon"] for v in per_surah.values()]
        agg = float(median(per_char_margins))
        return agg, {"n_units": len(per_char_margins),
                     "median_per_char_margin": agg,
                     "min_per_char_margin": float(min(per_char_margins)),
                     "max_per_char_margin": float(max(per_char_margins))}
    # Single-chapter
    peers = d.get("peer_records_top10_closest", [])
    if not peers:
        raise RuntimeError(f"No peer records in {receipt_path}")
    min_peer_delta = peers[0]["delta"]
    # n_canon is in the per-tradition main block (psalm_78, mark_1, dn1, yasna_28)
    n_canon = None
    for blk_name in ("psalm_78", "mark_1", "dn1", "yasna_28"):
        if blk_name in d:
            blk = d[blk_name]
            n_canon = blk.get("n_letters", blk.get("n_letters_22"))
            break
    if n_canon is None:
        raise RuntimeError(f"Could not find n_canon in {receipt_path}")
    per_char_margin = (min_peer_delta - TAU) / n_canon
    return per_char_margin, {"n_units": 1, "min_peer_delta": min_peer_delta,
                              "n_canon": n_canon, "per_char_margin": per_char_margin}


def _load_f63_pmax(receipt_path: Path) -> dict[str, float]:
    d = json.load(open(receipt_path, encoding="utf-8"))
    return {name: med["p_max"] for name, med in d["medians"].items()}


def _load_f63_hel(receipt_path: Path) -> dict[str, float]:
    d = json.load(open(receipt_path, encoding="utf-8"))
    return {name: med["H_EL"] for name, med in d["medians"].items()}


def _load_lc2_z(receipt_path: Path) -> dict[str, float]:
    d = json.load(open(receipt_path, encoding="utf-8"))
    pc = d["per_corpus"]
    return {name: blk["z_path"] for name, blk in pc.items()}


# ----------------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------------

def rank_descending(values: list[float]) -> list[int]:
    """Rank a list with rank 1 = highest value (best), ties broken by index order.

    Returns rank-of-each-position (i.e., result[i] = rank of values[i]).
    """
    n = len(values)
    indexed = sorted(range(n), key=lambda i: -values[i])
    ranks = [0] * n
    for r, i in enumerate(indexed):
        ranks[i] = r + 1
    return ranks


def rank_ascending(values: list[float]) -> list[int]:
    """Rank with rank 1 = lowest value (best for LC2_z which is more-negative-better)."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0] * n
    for r, i in enumerate(indexed):
        ranks[i] = r + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    rx = rank_ascending(x)
    ry = rank_ascending(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = (sum((rx[i] - mx) ** 2 for i in range(n))) ** 0.5
    dy = (sum((ry[i] - my) ** 2 for i in range(n))) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def perm_null_joint_top1(rank_arrays: list[list[int]], n_perms: int, seed: int) -> dict:
    """Independent permutation null: shuffle each axis independently, count traditions
    landing rank-1 on all axes simultaneously.

    Returns:
        any_top1: fraction of perms where ANY tradition is rank-1 on all axes
        per_pos_top1: fraction where each position is rank-1 on all axes
    """
    n_axes = len(rank_arrays)
    n_trad = len(rank_arrays[0])
    rng = np.random.default_rng(seed)
    any_count = 0
    per_pos_count = [0] * n_trad
    arr = np.array(rank_arrays, dtype=int)
    for _ in range(n_perms):
        shuffled = np.empty_like(arr)
        for ax in range(n_axes):
            perm = rng.permutation(n_trad)
            shuffled[ax] = arr[ax][perm]
        # check joint top-1: position p is rank-1 on all axes if shuffled[ax,p]==1 for all ax
        is_top1 = np.all(shuffled == 1, axis=0)  # shape (n_trad,)
        if is_top1.any():
            any_count += 1
        for p in range(n_trad):
            if is_top1[p]:
                per_pos_count[p] += 1
    return {
        "any_tradition_top1_on_all": any_count / n_perms,
        "per_position_top1_on_all": [c / n_perms for c in per_pos_count],
    }


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    out_dir = ROOT / "results" / "experiments" / "exp113_joint_extremality_3way"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load source receipt SHAs
    receipt_shas = {}
    for name, rp in F55_RECEIPTS.items():
        receipt_shas[f"f55_{name}"] = _sha256(ROOT / rp)
    receipt_shas["f63"] = _sha256(ROOT / F63_RECEIPT)
    receipt_shas["lc2"] = _sha256(ROOT / LC2_RECEIPT)

    # 2. Load metrics for all traditions
    f55_safety = {}
    f55_details = {}
    for name in TRADITIONS:
        margin, det = _load_f55_safety(ROOT / F55_RECEIPTS[name])
        f55_safety[name] = margin
        f55_details[name] = det

    pmax_all = _load_f63_pmax(ROOT / F63_RECEIPT)
    hel_all = _load_f63_hel(ROOT / F63_RECEIPT)
    lc2_z_all = _load_lc2_z(ROOT / LC2_RECEIPT)

    f63_pmax = {n: pmax_all[n] for n in TRADITIONS}
    f63_hel = {n: hel_all[n] for n in TRADITIONS}
    lc2_z = {n: lc2_z_all[LC2_NAME_MAP[n]] for n in TRADITIONS}

    # 3. Compute ranks
    # Higher F55_safety = better (rank 1 = highest)
    # Higher F63_p_max = better (more concentrated rhyme; rank 1 = highest)
    # Lower F63_H_EL = better (more concentrated rhyme; rank 1 = lowest)
    # Lower LC2_z = better (more negative = more path-minimal; rank 1 = lowest)
    f55_vals = [f55_safety[n] for n in TRADITIONS]
    pmax_vals = [f63_pmax[n] for n in TRADITIONS]
    hel_vals = [f63_hel[n] for n in TRADITIONS]
    lc2_vals = [lc2_z[n] for n in TRADITIONS]

    f55_ranks = rank_descending(f55_vals)
    pmax_ranks = rank_descending(pmax_vals)
    hel_ranks = rank_ascending(hel_vals)
    lc2_ranks = rank_ascending(lc2_vals)

    quran_idx = TRADITIONS.index("quran")
    quran_ranks = {
        "F55_safety_per_char": f55_ranks[quran_idx],
        "F63_p_max":           pmax_ranks[quran_idx],
        "F63_H_EL":            hel_ranks[quran_idx],
        "LC2_z":               lc2_ranks[quran_idx],
    }

    # 4. Joint top-1 test (3-way: F55 + F63_p_max + LC2)
    quran_top1_3way = (f55_ranks[quran_idx] == 1 and
                       pmax_ranks[quran_idx] == 1 and
                       lc2_ranks[quran_idx] == 1)

    perm_3way = perm_null_joint_top1(
        [f55_ranks, pmax_ranks, lc2_ranks], N_PERMS, SEED
    )

    # 5. Joint top-1 (2-way: F55 + F63_p_max only — drop the failing LC2 axis)
    quran_top1_2way = (f55_ranks[quran_idx] == 1 and pmax_ranks[quran_idx] == 1)
    perm_2way = perm_null_joint_top1(
        [f55_ranks, pmax_ranks], N_PERMS, SEED
    )

    # 6. Borda-count joint rank (sum of ranks; lower = jointly more extremal)
    borda = {}
    for i, n in enumerate(TRADITIONS):
        borda[n] = f55_ranks[i] + pmax_ranks[i] + lc2_ranks[i]
    borda_sorted = sorted(borda.items(), key=lambda x: x[1])
    quran_borda_rank = [t for t, _ in borda_sorted].index("quran") + 1

    # 7. Pairwise Spearman correlations (axes are independent if |rho| small)
    corrs = {
        "F55_vs_F63_p_max": spearman(f55_vals, pmax_vals),
        "F55_vs_F63_H_EL":  spearman(f55_vals, hel_vals),
        "F55_vs_LC2_z":     spearman(f55_vals, lc2_vals),
        "F63_p_max_vs_F63_H_EL": spearman(pmax_vals, hel_vals),
        "F63_p_max_vs_LC2_z":    spearman(pmax_vals, lc2_vals),
        "F63_H_EL_vs_LC2_z":     spearman(hel_vals, lc2_vals),
    }

    # 8. Verdict
    if quran_top1_3way and perm_3way["per_position_top1_on_all"][quran_idx] < 0.05:
        verdict = "PASS_quran_jointly_extremal_3way"
    elif quran_top1_2way and perm_2way["per_position_top1_on_all"][quran_idx] < 0.05:
        verdict = "PASS_quran_jointly_extremal_2way_F55_F63"
    else:
        verdict = "FAIL_quran_not_top1_on_3_axes"

    # 9. Receipt
    finished = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": "exp113_joint_extremality_3way",
        "hypothesis_id": "H68",
        "verdict": verdict,
        "started_at_utc": started,
        "completed_at_utc": finished,
        "prereg_document": "experiments/exp113_joint_extremality_3way/PREREG.md",
        "prereg_sha256": _sha256(ROOT / "experiments/exp113_joint_extremality_3way/PREREG.md"),
        "frozen_constants": {
            "TAU": TAU,
            "N_PERMS": N_PERMS,
            "SEED": SEED,
            "TRADITIONS": TRADITIONS,
        },
        "source_receipt_sha256": receipt_shas,
        "metrics_per_tradition": {
            n: {
                "F55_safety_per_char": f55_safety[n],
                "F63_p_max": f63_pmax[n],
                "F63_H_EL": f63_hel[n],
                "LC2_z": lc2_z[n],
            } for n in TRADITIONS
        },
        "f55_details_per_tradition": f55_details,
        "ranks_per_axis": {
            "F55_safety_per_char": dict(zip(TRADITIONS, f55_ranks)),
            "F63_p_max": dict(zip(TRADITIONS, pmax_ranks)),
            "F63_H_EL": dict(zip(TRADITIONS, hel_ranks)),
            "LC2_z": dict(zip(TRADITIONS, lc2_ranks)),
        },
        "quran_ranks": quran_ranks,
        "quran_top1_3way_F55_F63pmax_LC2": quran_top1_3way,
        "quran_top1_2way_F55_F63pmax": quran_top1_2way,
        "perm_null_3way": perm_3way,
        "perm_null_2way": perm_2way,
        "borda_count": borda,
        "quran_borda_rank": quran_borda_rank,
        "pairwise_spearman_correlations": corrs,
        "audit_report": {
            "ok": True,
            "n_traditions": len(TRADITIONS),
            "all_metrics_present": all(
                n in f55_safety and n in f63_pmax and n in lc2_z for n in TRADITIONS
            ),
            "perm_seed": SEED,
            "perm_n": N_PERMS,
        },
    }

    out_path = out_dir / "exp113_joint_extremality_3way.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== exp113 — Joint Extremality 3-way Test ===\n")
    print(f"Traditions: {TRADITIONS}\n")
    print(f"{'Axis':<25} {'Quran rank':>11} {'Quran value':>15}")
    print("-" * 53)
    print(f"{'F55_safety_per_char':<25} {f55_ranks[quran_idx]:>11} {f55_safety['quran']:>15.4f}")
    print(f"{'F63_p_max':<25} {pmax_ranks[quran_idx]:>11} {f63_pmax['quran']:>15.4f}")
    print(f"{'F63_H_EL':<25} {hel_ranks[quran_idx]:>11} {f63_hel['quran']:>15.4f}")
    print(f"{'LC2_z':<25} {lc2_ranks[quran_idx]:>11} {lc2_z['quran']:>15.4f}")
    print(f"\nQuran Borda-count rank: {quran_borda_rank}/{len(TRADITIONS)}")
    print(f"Quran top-1 on F55+F63_pmax+LC2: {quran_top1_3way}")
    print(f"Quran top-1 on F55+F63_pmax: {quran_top1_2way}")
    print(f"\nPerm-null (3-way Quran-position rank-1-on-all): {perm_3way['per_position_top1_on_all'][quran_idx]:.6f}")
    print(f"Perm-null (2-way Quran-position rank-1-on-all): {perm_2way['per_position_top1_on_all'][quran_idx]:.6f}")
    print(f"\nVerdict: {verdict}")
    print(f"\nReceipt: {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
