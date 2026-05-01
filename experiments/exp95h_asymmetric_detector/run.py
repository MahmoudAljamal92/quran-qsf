"""
exp95h_asymmetric_detector — pure analysis of `exp95e` V1 receipt against
the locked 108-rule asymmetric-detector grid (H41).

Reads:
  - results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json
  - results/experiments/exp95e_full_114_consensus_universal/v1/envelope_table.csv
  - experiments/exp95h_asymmetric_detector/PREREG.md (for prereg-hash audit)

Writes:
  - results/experiments/exp95h_asymmetric_detector/exp95h_asymmetric_detector.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path

EXP = "exp95h_asymmetric_detector"
ROOT = Path(__file__).resolve().parents[2]

V1_RECEIPT = (
    ROOT
    / "results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json"
)
ENVELOPE_CSV = (
    ROOT
    / "results/experiments/exp95e_full_114_consensus_universal/v1/envelope_table.csv"
)
PREREG_PATH = ROOT / "experiments/exp95h_asymmetric_detector/PREREG.md"
OUT_DIR = ROOT / "results/experiments/exp95h_asymmetric_detector"

# ---- Frozen grid (must match PREREG.md §2.1 and §2.2 exactly) -----------

L0_GRID = [138, 188, 250, 350, 500, 700, 873, 1000, 1500]

# (D_short, D_long) — names must match keys in `detector_recall_per_surah`
G_PAIRS = [
    ("K2", "gzip"),
    ("K2", "K1"),
    ("K2", "lzma"),
    ("K2", "zstd"),
    ("K2", "gzip_or_lzma"),
    ("K2", "gzip_and_not_bz2"),
    ("K1", "gzip"),
    ("K1", "K1"),
    ("gzip", "gzip"),
    ("gzip", "K1"),
    ("K3", "gzip"),
    ("K3", "K2"),
]

PER_SURAH_BAR = 0.99
PER_SURAH_BAR_STRICT = 0.999
AGGREGATE_BAR = 0.99
AGGREGATE_BAR_STRICT = 0.999


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _detector_recall(d_name: str, surah_entry: dict) -> float:
    """Look up the receipt's per-surah recall for a named detector.

    For composite detectors (`gzip_or_lzma`, `gzip_and_not_bz2`) we use a
    Bonferroni *upper bound* on per-surah recall, computed from the locked
    per-compressor solo recalls. The PREREG flags these as upper bounds; if
    they happen to be the winning rule we also flag the rule as
    `composite_upper_bound_only` in the receipt so reviewers know.
    """
    if d_name in ("K1", "K2", "K3", "K4"):
        k = int(d_name[1])
        return float(surah_entry[f"recall_K{k}"])
    if d_name in ("gzip", "bz2", "lzma", "zstd"):
        return float(surah_entry[f"recall_solo_{d_name}"])
    if d_name == "gzip_or_lzma":
        rg = float(surah_entry["recall_solo_gzip"])
        rl = float(surah_entry["recall_solo_lzma"])
        # Bonferroni upper bound on the OR (correlated detectors): can't
        # exceed min(rg+rl, 1).
        return min(rg + rl, 1.0)
    if d_name == "gzip_and_not_bz2":
        # bz2-solo recall = 0 across all 114 surahs → AND-NOT degenerates to
        # gzip-solo. Recorded as such.
        return float(surah_entry["recall_solo_gzip"])
    raise ValueError(f"unknown detector name: {d_name}")


def _detector_fpr(d_name: str, ctrl_null: dict) -> float:
    if d_name in ("K1", "K2", "K3", "K4"):
        k = int(d_name[1])
        return float(ctrl_null["fpr_by_consensus_K"][str(k)])
    if d_name in ("gzip", "bz2", "lzma", "zstd"):
        return float(ctrl_null["fpr_per_compressor_at_locked_tau"][d_name])
    if d_name == "gzip_or_lzma":
        fg = float(ctrl_null["fpr_per_compressor_at_locked_tau"]["gzip"])
        fl = float(ctrl_null["fpr_per_compressor_at_locked_tau"]["lzma"])
        return min(fg + fl, 1.0)
    if d_name == "gzip_and_not_bz2":
        # AND-NOT is bounded above by gzip-solo's FPR.
        return float(ctrl_null["fpr_per_compressor_at_locked_tau"]["gzip"])
    raise ValueError(f"unknown detector name: {d_name}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # ---- 1. Load PREREG hash (lock at run-time) ------------------------
    prereg_hash = _sha256(PREREG_PATH)
    expected_hash = (
        "9e45134f70ac9f6d9e254f860c36c7b1897ffa322c76fdfec58d7585d7f35d5c"
    )
    if prereg_hash != expected_hash:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift: got {prereg_hash}, expected {expected_hash}"
        )

    # ---- 2. Load V1 receipt + envelope CSV ----------------------------
    with open(V1_RECEIPT, "r", encoding="utf-8") as f:
        v1 = json.load(f)
    parent_v1_sha256 = _sha256(V1_RECEIPT)

    surah_lengths: dict[str, int] = {}
    with open(ENVELOPE_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            surah_lengths[row["surah"]] = int(row["n_total_letters"])

    per_surah = v1["per_surah"]  # dict keyed by 'Q:001' style
    if len(per_surah) != 114:
        raise SystemExit(f"[{EXP}] expected 114 surahs in receipt, got {len(per_surah)}")
    if set(per_surah.keys()) != set(surah_lengths.keys()):
        miss_a = set(per_surah.keys()) - set(surah_lengths.keys())
        miss_b = set(surah_lengths.keys()) - set(per_surah.keys())
        raise SystemExit(f"[{EXP}] surah-key mismatch: receipt-only={miss_a}, csv-only={miss_b}")

    ctrl_null = v1["ctrl_null"]

    # ---- 3. Evaluate every cell of the 108-rule grid -------------------
    rules = []  # list of dicts, one per cell
    for l0 in L0_GRID:
        for d_short, d_long in G_PAIRS:
            per_surah_recall: dict[str, float] = {}
            n_variants_per_surah: dict[str, int] = {}
            n_short = 0
            for sid, entry in per_surah.items():
                tot = surah_lengths[sid]
                d = d_short if tot <= l0 else d_long
                if tot <= l0:
                    n_short += 1
                per_surah_recall[sid] = _detector_recall(d, entry)
                n_variants_per_surah[sid] = int(entry["n_variants"])
            min_recall = min(per_surah_recall.values())
            total_v = sum(n_variants_per_surah.values())
            agg_recall = (
                sum(per_surah_recall[s] * n_variants_per_surah[s] for s in per_surah_recall)
                / total_v
            )
            n_below_99 = sum(1 for v in per_surah_recall.values() if v < PER_SURAH_BAR)
            n_below_999 = sum(1 for v in per_surah_recall.values() if v < PER_SURAH_BAR_STRICT)
            n_perfect = sum(1 for v in per_surah_recall.values() if v >= 0.99999)
            fpr_upper = max(_detector_fpr(d_short, ctrl_null), _detector_fpr(d_long, ctrl_null))

            rules.append({
                "L0": l0,
                "D_short": d_short,
                "D_long": d_long,
                "n_short": n_short,
                "n_long": 114 - n_short,
                "min_per_surah_recall": min_recall,
                "aggregate_recall": agg_recall,
                "n_surahs_below_99": n_below_99,
                "n_surahs_below_999": n_below_999,
                "n_surahs_perfect": n_perfect,
                "fpr_upper_bound": fpr_upper,
                "composite_upper_bound_only": d_short in ("gzip_or_lzma", "gzip_and_not_bz2")
                or d_long in ("gzip_or_lzma", "gzip_and_not_bz2"),
                "per_surah_recall": per_surah_recall,
            })

    # ---- 4. Pick the winner (max min_per_surah, tiebreak as in PREREG) ---
    pair_order = {p: i for i, p in enumerate(G_PAIRS)}
    rules.sort(
        key=lambda r: (
            -r["min_per_surah_recall"],
            -r["aggregate_recall"],
            r["L0"],
            pair_order[(r["D_short"], r["D_long"])],
        )
    )
    winner = rules[0]

    # ---- 5. Apply verdict ladder ---------------------------------------
    if winner["min_per_surah_recall"] < 0.90:
        verdict = "FAIL_no_clean_split_p90"
    elif (
        winner["aggregate_recall"] >= AGGREGATE_BAR_STRICT
        and winner["min_per_surah_recall"] < PER_SURAH_BAR
    ):
        verdict = "PARTIAL_p99_aggregate_only"
    elif winner["min_per_surah_recall"] < PER_SURAH_BAR:
        verdict = "FAIL_no_clean_split"
    elif (
        winner["min_per_surah_recall"] >= PER_SURAH_BAR_STRICT
        and winner["aggregate_recall"] >= AGGREGATE_BAR_STRICT
    ):
        verdict = "PASS_asymmetric_999"
    else:
        verdict = "PASS_asymmetric_99"

    # ---- 6. Write receipt ----------------------------------------------
    record = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H41",
        "verdict": verdict,
        "prereg_hash_expected": expected_hash,
        "prereg_hash_actual": prereg_hash,
        "parent_v1_receipt_sha256": parent_v1_sha256,
        "parent_planning_doc": "docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md",
        "n_rules_evaluated": len(rules),
        "winner": {k: v for k, v in winner.items() if k != "per_surah_recall"},
        "winner_per_surah_recall": winner["per_surah_recall"],
        "top_5_rules": [
            {k: v for k, v in r.items() if k != "per_surah_recall"} for r in rules[:5]
        ],
        "all_rules_summary": [
            {k: v for k, v in r.items() if k != "per_surah_recall"} for r in rules
        ],
        "wall_time_s": round(time.time() - t0, 3),
    }
    out_path = OUT_DIR / f"{EXP}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    # ---- 7. Console summary --------------------------------------------
    print(f"[{EXP}] verdict: {verdict}")
    print(
        f"[{EXP}] winner: L0={winner['L0']} "
        f"D_short={winner['D_short']} D_long={winner['D_long']} "
        f"min_per_surah={winner['min_per_surah_recall']:.4f} "
        f"aggregate={winner['aggregate_recall']:.4f} "
        f"n_below_99={winner['n_surahs_below_99']} "
        f"n_below_999={winner['n_surahs_below_999']} "
        f"n_perfect={winner['n_surahs_perfect']} "
        f"fpr_upper={winner['fpr_upper_bound']:.4f}"
    )
    print(f"[{EXP}] receipt: {out_path}")
    print(f"[{EXP}] top 5 rules (sorted):")
    for r in rules[:5]:
        print(
            f"  L0={r['L0']:<5} {r['D_short']:>16}/{r['D_long']:<16} "
            f"min={r['min_per_surah_recall']:.4f} agg={r['aggregate_recall']:.4f} "
            f"n<99={r['n_surahs_below_99']:3d} n<999={r['n_surahs_below_999']:3d} "
            f"perfect={r['n_surahs_perfect']:3d} fpr<={r['fpr_upper_bound']:.4f}"
        )


if __name__ == "__main__":
    main()
