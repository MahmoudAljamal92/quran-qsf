"""
exp95i_bigram_shift_detector — Path C of post-V1 rescue paths.

Hypothesis H42 (locked in PREREG.md):
    Under the bigram-shift statistic
        Delta_bigram(canon, candidate) = ||hist_2(canon) - hist_2(candidate)||_1 / 2
    and the detector "fires iff 0 < Delta <= tau_high" with tau_high
    calibrated as the 5th percentile of the global length-matched
    (canon_X, peer_P) Delta distribution, single-consonant-substitution
    forgeries on every Quran surah are detected at per-surah recall >= 0.99
    with global ctrl-null FPR <= 0.05.

Reads:
  - phase_06_phi_m.pkl (corpus checkpoint, SHA-256 verified)
  - experiments/exp95i_bigram_shift_detector/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95i_bigram_shift_detector/
      exp95i_bigram_shift_detector.json (receipt)
      per_surah_summary.csv (diagnostic)
      ctrl_null_distribution.csv (diagnostic)
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
    enumerate_v1,
    letters_28,
)

EXP = "exp95i_bigram_shift_detector"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "9a67de356aff74aef306d38b2e6df829943a1472e7b544345814b4887b03e53c"
)

# Frozen constants (must match PREREG.md §6)
K_PEERS = 50
LENGTH_LO_FRAC = 0.5
LENGTH_HI_FRAC = 1.5
TAU_PERCENTILE = 5
PER_SURAH_BAR = 0.99
PER_SURAH_BAR_STRICT = 0.999
AGGREGATE_BAR = 0.99
AGGREGATE_BAR_STRICT = 0.999
FLOOR_P90 = 0.90
FPR_TARGET = 0.05
MAX_VARIANT_DELTA_AUDIT = 2.0


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bigrams_of(s: str) -> Counter:
    """Bigram counter for letters_28-encoded string."""
    return Counter(s[i : i + 2] for i in range(len(s) - 1))


def bigram_l1(c1: Counter, c2: Counter) -> int:
    """L1 distance between two bigram counters."""
    keys = set(c1) | set(c2)
    return sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def main() -> None:
    out_dir = safe_output_dir(EXP)
    t0 = time.time()

    # ---- 1. Lock PREREG hash ----------------------------------------------
    actual_hash = _sha256(PREREG_PATH)
    if actual_hash != EXPECTED_PREREG_HASH:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift:\n"
            f"  expected: {EXPECTED_PREREG_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"REFUSING TO RUN. Restore PREREG.md before continuing."
        )

    # ---- 2. Load corpus ---------------------------------------------------
    print(f"[{EXP}] loading corpus checkpoint phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    quran = list(CORPORA.get("quran", []))
    if len(quran) != 114:
        raise SystemExit(f"[{EXP}] expected 114 quran surahs, got {len(quran)}")

    # Build peer pool: all non-Quran items, in iteration order (deterministic)
    peer_pool: list[tuple[str, str, str]] = []  # (corpus_name, label, letters_28-string)
    for cname, items in CORPORA.items():
        if cname == "quran":
            continue
        for u in items:
            label = getattr(u, "label", f"{cname}:?")
            try:
                pstr = letters_28(" ".join(u.verses))
            except Exception:
                continue
            if len(pstr) >= 2:
                peer_pool.append((cname, label, pstr))
    print(f"[{EXP}] peer pool size: {len(peer_pool)}")

    # ---- 3. Per-surah scoring ---------------------------------------------
    per_surah: dict[str, dict[str, Any]] = {}
    audit_max_var_delta = 0.0
    surahs_with_zero_ctrl: list[str] = []
    n_quran_done = 0

    for u in quran:
        label = getattr(u, "label", "?")
        canon_str = letters_28(" ".join(u.verses))
        n_canon = len(canon_str)
        if n_canon < 2:
            print(f"[{EXP}] skipping {label}: canon length {n_canon} < 2")
            continue
        canon_bg = bigrams_of(canon_str)

        # Length-matched ctrl peers (deterministic CORPORA-iteration order)
        len_lo = LENGTH_LO_FRAC * n_canon
        len_hi = LENGTH_HI_FRAC * n_canon
        ctrl_deltas: list[float] = []
        for _cn, _cl, pstr in peer_pool:
            if len(ctrl_deltas) >= K_PEERS:
                break
            n_p = len(pstr)
            if len_lo <= n_p <= len_hi:
                p_bg = bigrams_of(pstr)
                d = bigram_l1(canon_bg, p_bg) / 2
                ctrl_deltas.append(d)
        if not ctrl_deltas:
            surahs_with_zero_ctrl.append(label)

        # V1 variant scoring
        v1_specs = enumerate_v1(u.verses)
        var_deltas: list[float] = []
        for v in v1_specs:
            new_verses = list(u.verses)
            new_verses[v["verse_idx"]] = v["v1_variant"]
            var_str = letters_28(" ".join(new_verses))
            var_bg = bigrams_of(var_str)
            d = bigram_l1(canon_bg, var_bg) / 2
            var_deltas.append(d)
            if d > audit_max_var_delta:
                audit_max_var_delta = d

        per_surah[label] = {
            "n_canon": n_canon,
            "n_variants": len(var_deltas),
            "n_ctrl_matched": len(ctrl_deltas),
            "var_delta_min": float(min(var_deltas)) if var_deltas else None,
            "var_delta_max": float(max(var_deltas)) if var_deltas else None,
            "ctrl_delta_min": float(min(ctrl_deltas)) if ctrl_deltas else None,
            "ctrl_delta_max": float(max(ctrl_deltas)) if ctrl_deltas else None,
            "ctrl_delta_p05_per_surah": (
                float(np.percentile(ctrl_deltas, TAU_PERCENTILE)) if ctrl_deltas else None
            ),
            "_var_deltas": var_deltas,
            "_ctrl_deltas": ctrl_deltas,
        }
        n_quran_done += 1
        if n_quran_done % 20 == 0:
            print(
                f"[{EXP}]   {n_quran_done:3d}/114 surahs done, "
                f"max_var_delta_so_far = {audit_max_var_delta:.3f}"
            )

    # Pool ctrl-Δ globally
    all_ctrl_deltas = [
        d for ps in per_surah.values() for d in ps["_ctrl_deltas"]
    ]
    all_var_deltas = [
        d for ps in per_surah.values() for d in ps["_var_deltas"]
    ]

    # ---- 4. Audit-hook checks (ladder branch 1) ---------------------------
    audit_violations: list[str] = []
    if audit_max_var_delta > MAX_VARIANT_DELTA_AUDIT + 1e-9:
        audit_violations.append(
            f"max_variant_delta={audit_max_var_delta:.6f} > {MAX_VARIANT_DELTA_AUDIT}"
        )
    if surahs_with_zero_ctrl:
        audit_violations.append(
            f"{len(surahs_with_zero_ctrl)} surah(s) with zero length-matched ctrl peers"
        )
    if not all_ctrl_deltas:
        audit_violations.append("global ctrl pool empty")

    # ---- 5. Calibrate τ_high ---------------------------------------------
    if audit_violations:
        tau_high = None
    else:
        tau_high = float(np.percentile(all_ctrl_deltas, TAU_PERCENTILE))
        if tau_high <= 0:
            audit_violations.append(f"tau_high={tau_high:.6f} <= 0")

    # ---- 6. Apply detector to variants and per-surah ctrl -----------------
    if tau_high is not None and tau_high > 0:
        for label, ps in per_surah.items():
            var_deltas = ps["_var_deltas"]
            ctrl_deltas = ps["_ctrl_deltas"]
            n_v = len(var_deltas)
            n_c = len(ctrl_deltas)
            n_fire_v = sum(1 for d in var_deltas if 0 < d <= tau_high)
            n_fire_c = sum(1 for d in ctrl_deltas if 0 < d <= tau_high)
            ps["recall"] = (n_fire_v / n_v) if n_v else None
            ps["fpr_per_surah"] = (n_fire_c / n_c) if n_c else None
            ps["n_fires_v"] = n_fire_v
            ps["n_fires_c"] = n_fire_c

    # Strip temp keys
    for ps in per_surah.values():
        ps.pop("_var_deltas", None)
        ps.pop("_ctrl_deltas", None)

    # ---- 7. Aggregate stats ----------------------------------------------
    if tau_high is not None and tau_high > 0:
        total_v = sum(ps["n_variants"] for ps in per_surah.values())
        agg_recall = (
            sum(ps["recall"] * ps["n_variants"] for ps in per_surah.values()) / total_v
        )
        total_c = sum(ps["n_ctrl_matched"] for ps in per_surah.values())
        agg_fpr = (
            sum(ps["fpr_per_surah"] * ps["n_ctrl_matched"] for ps in per_surah.values())
            / total_c
        ) if total_c else None
        recalls = [ps["recall"] for ps in per_surah.values() if ps.get("recall") is not None]
        min_recall = min(recalls)
        max_recall = max(recalls)
        n_below_99 = sum(1 for r in recalls if r < PER_SURAH_BAR)
        n_below_999 = sum(1 for r in recalls if r < PER_SURAH_BAR_STRICT)
        n_perfect = sum(1 for r in recalls if r >= 1.0 - 1e-9)
    else:
        agg_recall = None
        agg_fpr = None
        min_recall = None
        max_recall = None
        n_below_99 = None
        n_below_999 = None
        n_perfect = None

    # ---- 8. Q:100 regression check (ladder branch 3) ---------------------
    q100_entry = per_surah.get("Q:100")
    q100_recall = q100_entry.get("recall") if q100_entry else None
    q100_pass = q100_recall is not None and q100_recall >= PER_SURAH_BAR_STRICT

    # ---- 9. Verdict ladder ----------------------------------------------
    if audit_violations:
        verdict = "FAIL_audit_hook_violated"
    elif tau_high is None or tau_high <= 0:
        verdict = "FAIL_tau_zero"
    elif not q100_pass:
        verdict = "FAIL_q100_regression"
    elif agg_recall < AGGREGATE_BAR:
        verdict = "FAIL_aggregate_below_floor"
    elif min_recall < FLOOR_P90:
        verdict = "FAIL_per_surah_floor"
    elif agg_fpr is not None and agg_fpr > FPR_TARGET + 1e-3:
        verdict = "FAIL_global_fpr_overflow"
    elif min_recall < PER_SURAH_BAR:
        # All surahs >= 0.90 but at least one in [0.90, 0.99)
        verdict = "PARTIAL_p99_aggregate_with_p90_floor"
    elif min_recall >= 1.0 - 1e-9 and max_recall >= 1.0 - 1e-9:
        verdict = "PASS_universal_100_bigram"
    elif min_recall >= PER_SURAH_BAR_STRICT and agg_recall >= AGGREGATE_BAR_STRICT:
        verdict = "PASS_universal_999_bigram"
    else:
        verdict = "PASS_universal_99_bigram"

    # ---- 10. Write receipt ----------------------------------------------
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H42",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "parent_planning_doc": "docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md",
        "frozen_constants": {
            "K_PEERS": K_PEERS,
            "LENGTH_LO_FRAC": LENGTH_LO_FRAC,
            "LENGTH_HI_FRAC": LENGTH_HI_FRAC,
            "TAU_PERCENTILE": TAU_PERCENTILE,
            "MAX_VARIANT_DELTA_AUDIT": MAX_VARIANT_DELTA_AUDIT,
            "PER_SURAH_BAR": PER_SURAH_BAR,
            "PER_SURAH_BAR_STRICT": PER_SURAH_BAR_STRICT,
            "AGGREGATE_BAR": AGGREGATE_BAR,
            "AGGREGATE_BAR_STRICT": AGGREGATE_BAR_STRICT,
            "FPR_TARGET": FPR_TARGET,
            "FLOOR_P90": FLOOR_P90,
        },
        "n_surahs_scored": len(per_surah),
        "n_variants_total": len(all_var_deltas),
        "n_ctrl_matched_total": len(all_ctrl_deltas),
        "n_peers_in_pool": len(peer_pool),
        "tau_high": tau_high,
        "audit": {
            "max_variant_delta": audit_max_var_delta,
            "max_variant_delta_le_2": audit_max_var_delta <= MAX_VARIANT_DELTA_AUDIT + 1e-9,
            "surahs_with_zero_ctrl": surahs_with_zero_ctrl,
            "audit_violations": audit_violations,
        },
        "aggregate": {
            "recall": agg_recall,
            "fpr": agg_fpr,
            "min_per_surah_recall": min_recall,
            "max_per_surah_recall": max_recall,
            "n_surahs_below_99": n_below_99,
            "n_surahs_below_999": n_below_999,
            "n_surahs_perfect": n_perfect,
        },
        "q100_regression": {
            "recall": q100_recall,
            "passes_999": q100_pass,
        },
        "ctrl_null_summary": (
            {
                "n_pool": len(all_ctrl_deltas),
                "min": float(min(all_ctrl_deltas)),
                "max": float(max(all_ctrl_deltas)),
                "p01": float(np.percentile(all_ctrl_deltas, 1)),
                "p05": float(np.percentile(all_ctrl_deltas, 5)),
                "p25": float(np.percentile(all_ctrl_deltas, 25)),
                "p50": float(np.percentile(all_ctrl_deltas, 50)),
                "p95": float(np.percentile(all_ctrl_deltas, 95)),
            }
            if all_ctrl_deltas
            else None
        ),
        "variant_delta_summary": (
            {
                "n_pool": len(all_var_deltas),
                "min": float(min(all_var_deltas)),
                "max": float(max(all_var_deltas)),
                "p01": float(np.percentile(all_var_deltas, 1)),
                "p50": float(np.percentile(all_var_deltas, 50)),
                "p99": float(np.percentile(all_var_deltas, 99)),
            }
            if all_var_deltas
            else None
        ),
        "per_surah": per_surah,
        "wall_time_s": round(time.time() - t0, 3),
    }
    receipt_path = out_dir / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    # ---- 11. CSV diagnostics --------------------------------------------
    csv_path = out_dir / "per_surah_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "surah",
            "n_canon",
            "n_variants",
            "n_ctrl_matched",
            "var_delta_min",
            "var_delta_max",
            "ctrl_delta_min",
            "ctrl_delta_max",
            "ctrl_delta_p05_per_surah",
            "recall",
            "fpr_per_surah",
            "n_fires_v",
            "n_fires_c",
        ])
        for label, ps in per_surah.items():
            w.writerow([
                label,
                ps.get("n_canon"),
                ps.get("n_variants"),
                ps.get("n_ctrl_matched"),
                ps.get("var_delta_min"),
                ps.get("var_delta_max"),
                ps.get("ctrl_delta_min"),
                ps.get("ctrl_delta_max"),
                ps.get("ctrl_delta_p05_per_surah"),
                ps.get("recall"),
                ps.get("fpr_per_surah"),
                ps.get("n_fires_v"),
                ps.get("n_fires_c"),
            ])

    # ---- 12. Console summary --------------------------------------------
    print("=" * 70)
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] tau_high = {tau_high}")
    print(
        f"[{EXP}] aggregate recall = "
        f"{agg_recall if agg_recall is not None else 'N/A'}"
    )
    print(
        f"[{EXP}] aggregate FPR    = "
        f"{agg_fpr if agg_fpr is not None else 'N/A'}"
    )
    print(
        f"[{EXP}] per-surah recall: min={min_recall}, max={max_recall}, "
        f"n<99={n_below_99}, n<999={n_below_999}, n_perfect={n_perfect}"
    )
    print(f"[{EXP}] Q:100 regression recall = {q100_recall} (passes_999={q100_pass})")
    print(
        f"[{EXP}] audit: max_var_delta = {audit_max_var_delta:.4f} "
        f"(<= 2.0 ? {audit_max_var_delta <= MAX_VARIANT_DELTA_AUDIT + 1e-9})"
    )
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] CSV:     {csv_path}")
    print(f"[{EXP}] wall_time_s = {round(time.time() - t0, 1)}")


if __name__ == "__main__":
    main()
