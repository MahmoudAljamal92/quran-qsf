# -*- coding: utf-8 -*-
"""
expP4_cross_tradition_R3_loo: leave-one-out robustness of the LC2 universal.

PURPOSE
-------
The parent experiment expP4_cross_tradition_R3 tests the pre-registered
LC2 universal ("R3 path-minimality") on 8 corpora and reports a verdict
of SUPPORT (3 of 4 new oral corpora pass z<-2; BH min p = 0.0003;
Iliad control fails). This experiment quantifies the *robustness* of
that verdict to dropping any single corpus.

For each corpus C in the parent's corpus_order:
  1. Remove C from the corpus set.
  2. Re-evaluate the three pre-registered LC2 predictions on the
     remaining 7 corpora.
  3. Re-run BH-correction on the surviving 7 p-values.
  4. Record whether the overall LC2 verdict still SUPPORTS.

NOT a re-run of the 5000-permutation null. Per-corpus z-scores are
independent of each other (each corpus is permuted only against itself),
so leave-one-out is a deterministic recomputation of pre-reg gates and
BH adjustment on a subset of the parent's per-corpus results.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Dict, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
PARENT_JSON = ROOT / "results" / "experiments" / "expP4_cross_tradition_R3" / "expP4_cross_tradition_R3.json"
OUT_DIR = ROOT / "results" / "experiments" / "expP4_cross_tradition_R3_loo"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "expP4_cross_tradition_R3_loo.json"

# Pre-registered thresholds (mirror the parent experiment)
Z_PASS_THRESHOLD = -2.0
ALPHA_BH = 0.05
NEW_ORAL_CORPORA = {"pali_dn", "pali_mn", "rigveda", "avestan_yasna"}
LC2_PRED_1_MIN_NEW_ORAL_PASSES = 2  # parent uses "two_of_four"; we re-evaluate at this same floor
NEGATIVE_CONTROLS = {"iliad_greek"}


def bh_adjust(pvals: List[float]) -> List[float]:
    """Benjamini-Hochberg step-up (matches scipy.stats.false_discovery_control('bh'))."""
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    adj = [0.0] * n
    running_min = 1.0
    # Walk from largest p back to smallest, applying the BH transform p_i * n / rank.
    for k in range(n - 1, -1, -1):
        i = order[k]
        rank = k + 1  # 1-indexed
        running_min = min(running_min, pvals[i] * n / rank)
        adj[i] = min(running_min, 1.0)
    return adj


def evaluate_subset(per_corpus: Dict[str, dict], corpora_kept: List[str]) -> dict:
    """Re-evaluate the LC2 pre-registered gates on a subset of the per_corpus dict."""
    kept = [c for c in corpora_kept if c in per_corpus]
    raw_p = [per_corpus[c]["p_one_sided"] for c in kept]
    bh_p = bh_adjust(raw_p)

    new_oral_passes = [
        c for c in kept
        if c in NEW_ORAL_CORPORA and per_corpus[c]["z_path"] < Z_PASS_THRESHOLD
    ]
    new_oral_present = [c for c in kept if c in NEW_ORAL_CORPORA]

    # PRED-LC2.1: at least 2 of the new oral corpora present pass z<-2
    pred_1 = "PASS" if len(new_oral_passes) >= min(LC2_PRED_1_MIN_NEW_ORAL_PASSES, len(new_oral_present)) else "FAIL"
    if not new_oral_present:
        pred_1 = "VACUOUS"

    # PRED-LC2.2: BH-pool min p < alpha
    pred_2 = "PASS" if (bh_p and min(bh_p) < ALPHA_BH) else "FAIL"

    # PRED-LC2.3: at least one negative control kept and it fails BH (p > alpha)
    controls_present = [c for c in kept if c in NEGATIVE_CONTROLS]
    if not controls_present:
        pred_3 = "VACUOUS"
    else:
        # control "fails" = its BH-adjusted p > alpha (canonical order indistinguishable from null)
        c_idx = kept.index(controls_present[0])
        pred_3 = "PASS" if bh_p[c_idx] > ALPHA_BH else "FAIL"

    # Overall verdict: SUPPORT iff pred_1 PASS, pred_2 PASS, pred_3 PASS-or-VACUOUS
    if pred_1 == "PASS" and pred_2 == "PASS" and pred_3 in ("PASS", "VACUOUS"):
        verdict = "SUPPORT"
    else:
        verdict = "FAIL"

    return {
        "n_corpora": len(kept),
        "kept_corpora": kept,
        "n_new_oral_present": len(new_oral_present),
        "n_new_oral_pass": len(new_oral_passes),
        "new_oral_passes": new_oral_passes,
        "min_bh_p": min(bh_p) if bh_p else None,
        "control_present": controls_present,
        "PRED_LC2_1_two_or_more_new_oral_pass": pred_1,
        "PRED_LC2_2_BH_min_p_lt_alpha": pred_2,
        "PRED_LC2_3_negative_control_fails": pred_3,
        "verdict": verdict,
    }


def main() -> None:
    if not PARENT_JSON.exists():
        raise SystemExit(f"Parent experiment JSON not found: {PARENT_JSON}")

    with open(PARENT_JSON, "r", encoding="utf-8") as f:
        parent = json.load(f)

    parent_hash = hashlib.sha256(PARENT_JSON.read_bytes()).hexdigest()
    per_corpus = parent["per_corpus"]
    corpora = parent["corpus_order"]

    # Sanity: full-set verdict must reproduce parent
    full = evaluate_subset(per_corpus, corpora)
    parent_verdict = parent["pre_registered_predictions"]["overall_LC2_verdict"]
    sanity = "OK" if full["verdict"] == parent_verdict else f"MISMATCH (full={full['verdict']}, parent={parent_verdict})"

    # Leave-one-out
    loo: Dict[str, dict] = {}
    for c in corpora:
        kept = [x for x in corpora if x != c]
        loo[c] = evaluate_subset(per_corpus, kept)
        loo[c]["dropped"] = c
        loo[c]["dropped_z"] = per_corpus[c]["z_path"]
        loo[c]["dropped_class"] = per_corpus[c]["tradition_class"]

    # Aggregate
    n_total = len(loo)
    n_still_support = sum(1 for v in loo.values() if v["verdict"] == "SUPPORT")
    fragile_drops = [c for c, v in loo.items() if v["verdict"] != "SUPPORT"]

    out = {
        "experiment": "expP4_cross_tradition_R3_loo",
        "parent_experiment": "expP4_cross_tradition_R3",
        "parent_json_sha256": parent_hash,
        "schema_version": 1,
        "method": "deterministic recomputation of LC2 pre-registered gates and BH-adjustment after removing each corpus in turn from the parent's per_corpus dict; per-corpus z-scores are independent so no re-permutation is needed.",
        "thresholds": {
            "z_pass": Z_PASS_THRESHOLD,
            "alpha_BH": ALPHA_BH,
            "min_new_oral_passes": LC2_PRED_1_MIN_NEW_ORAL_PASSES,
        },
        "full_set_sanity": {
            "full_verdict": full["verdict"],
            "parent_verdict": parent_verdict,
            "match": sanity,
        },
        "leave_one_out": loo,
        "robustness_summary": {
            "n_drops_tested": n_total,
            "n_still_SUPPORT": n_still_support,
            "fraction_robust": n_still_support / n_total if n_total else None,
            "fragile_drops": fragile_drops,
            "interpretation": (
                f"The LC2 SUPPORT verdict is robust to {n_still_support}/{n_total} single-corpus drops. "
                f"Fragile drops: {fragile_drops if fragile_drops else 'none'}."
            ),
        },
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"OK: wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"  full-set sanity         : {sanity}")
    print(f"  drops tested            : {n_total}")
    print(f"  still SUPPORT after drop: {n_still_support}/{n_total}")
    print(f"  fragile drops           : {fragile_drops if fragile_drops else '(none)'}")
    print()
    print("  Leave-one-out detail:")
    print(f"    {'dropped':18s} {'class':25s} {'z':>8s}  P1   P2   P3   verdict")
    for c, v in loo.items():
        print(
            f"    {c:18s} {v['dropped_class']:25s} {v['dropped_z']:8.2f}  "
            f"{v['PRED_LC2_1_two_or_more_new_oral_pass']:4s} "
            f"{v['PRED_LC2_2_BH_min_p_lt_alpha']:4s} "
            f"{v['PRED_LC2_3_negative_control_fails']:7s} "
            f"{v['verdict']}"
        )


if __name__ == "__main__":
    main()
