"""
exp95j_bigram_shift_universal — Path C-strict (frozen analytic-bound tau).

H43 (locked in PREREG.md): under the bigram-shift detector with FROZEN
threshold tau_high = 2.0 (motivated by analytic theorem; no calibration),
single-consonant-substitution forgeries on every Quran surah are detected
at per-surah recall = 1.000 with global FPR (full non-Quran peer pool,
all (surah, peer) pairs) <= 0.05.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp95j_bigram_shift_universal/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95j_bigram_shift_universal/
      exp95j_bigram_shift_universal.json (receipt)
      per_surah_summary.csv (diagnostic)
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

EXP = "exp95j_bigram_shift_universal"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd"
)

# Frozen constants (must match PREREG §6)
TAU_HIGH = 2.0
AUDIT_TOL = 1e-9
RECALL_FLOOR = 1.0
FPR_CEIL = 0.05
PARTIAL_FPR_BAND_HI = 0.50


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bigrams_of(s: str) -> Counter:
    return Counter(s[i : i + 2] for i in range(len(s) - 1))


def bigram_l1(c1: Counter, c2: Counter) -> int:
    keys = set(c1) | set(c2)
    return sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    """Δ_bigram between canon and canon with single substitution at position p.

    O(1) per call: only the (up to 4) bigrams touching position p change.
    """
    n = len(canon)
    old_ch = canon[p]
    diff: dict[str, int] = {}
    if p > 0:
        b_old_l = canon[p - 1] + old_ch
        b_new_l = canon[p - 1] + new_ch
        diff[b_old_l] = diff.get(b_old_l, 0) - 1
        diff[b_new_l] = diff.get(b_new_l, 0) + 1
    if p < n - 1:
        b_old_r = old_ch + canon[p + 1]
        b_new_r = new_ch + canon[p + 1]
        diff[b_old_r] = diff.get(b_old_r, 0) - 1
        diff[b_new_r] = diff.get(b_new_r, 0) + 1
    return sum(abs(v) for v in diff.values()) / 2


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

    # ---- 2. Load corpus ----
    print(f"[{EXP}] loading corpus phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    quran = list(CORPORA.get("quran", []))
    if len(quran) != 114:
        raise SystemExit(f"[{EXP}] expected 114 quran surahs, got {len(quran)}")

    # Build peer pool (no length matching)
    peer_pool: list[tuple[str, str, str, Counter]] = []
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
                peer_pool.append((cname, label, pstr, bigrams_of(pstr)))
    print(f"[{EXP}] peer pool size: {len(peer_pool)}")

    # ---- 3. Variant scoring (analytic) ----
    print(f"[{EXP}] scoring V1 variants analytically...")
    per_surah: dict[str, dict[str, Any]] = {}
    audit_max_var_delta = 0.0
    audit_violation_examples: list[dict[str, Any]] = []
    n_total_variants = 0
    n_total_var_fires = 0

    for u in quran:
        label = getattr(u, "label", "?")
        canon_str = letters_28(" ".join(u.verses))
        n_canon = len(canon_str)
        if n_canon < 2:
            print(f"[{EXP}] skipping {label}: canon length {n_canon} < 2")
            continue

        # Map char_pos_in_v1 -> position in canon_str (= position in letters_28(v0))
        # since V1 perturbs verse 0 only and verse 0 contributes the first letters.
        v0_raw = u.verses[0]
        v0_letters = letters_28(v0_raw)
        # prefix counts: prefix[i] = number of consonants in v0_raw[:i]
        prefix = [0] * (len(v0_raw) + 1)
        running = 0
        for i, ch in enumerate(v0_raw):
            prefix[i] = running
            if letters_28(ch):  # this returns either '' or a single character
                running += 1
        prefix[len(v0_raw)] = running
        assert running == len(v0_letters), (
            f"prefix walk inconsistent for {label}: running={running}, "
            f"len(v0_letters)={len(v0_letters)}"
        )

        v1_specs = enumerate_v1(u.verses)
        var_deltas: list[float] = []
        var_fires = 0
        for v in v1_specs:
            char_pos = v["char_pos_in_v1"]
            canon_p = prefix[char_pos]
            new_ch = v["repl"]
            d = variant_delta_analytic(canon_str, canon_p, new_ch)
            var_deltas.append(d)
            if d > audit_max_var_delta:
                audit_max_var_delta = d
            if d > TAU_HIGH + AUDIT_TOL:
                if len(audit_violation_examples) < 5:
                    audit_violation_examples.append({
                        "surah": label,
                        "char_pos_in_v1": char_pos,
                        "canon_p": canon_p,
                        "delta": d,
                        "old_ch": canon_str[canon_p],
                        "new_ch": new_ch,
                    })
            if 0 < d <= TAU_HIGH:
                var_fires += 1

        per_surah[label] = {
            "n_canon": n_canon,
            "n_variants": len(var_deltas),
            "var_delta_min": float(min(var_deltas)) if var_deltas else None,
            "var_delta_max": float(max(var_deltas)) if var_deltas else None,
            "n_var_fires": var_fires,
            "recall": (var_fires / len(var_deltas)) if var_deltas else None,
            "_var_deltas": var_deltas,
        }
        n_total_variants += len(var_deltas)
        n_total_var_fires += var_fires

    # ---- 4. Audit hook on variant theorem ----
    audit_hook_violated = audit_max_var_delta > TAU_HIGH + AUDIT_TOL
    print(
        f"[{EXP}] variant audit: max_var_delta = {audit_max_var_delta:.4f}, "
        f"theorem_holds = {not audit_hook_violated}"
    )

    # ---- 5. Peer pair scoring (full pool, all (surah, peer) pairs) ----
    if not audit_hook_violated:
        print(f"[{EXP}] scoring (surah x peer) pairs: 114 x {len(peer_pool)} = {114*len(peer_pool)}")
        n_total_pairs = 0
        n_total_pair_fires = 0
        for ix, u in enumerate(quran):
            label = getattr(u, "label", "?")
            canon_str = letters_28(" ".join(u.verses))
            if len(canon_str) < 2:
                continue
            canon_bg = bigrams_of(canon_str)

            n_pairs = 0
            n_fires = 0
            min_peer_d = float("inf")
            for _cn, _cl, _ps, peer_bg in peer_pool:
                d = bigram_l1(canon_bg, peer_bg) / 2
                n_pairs += 1
                if 0 < d <= TAU_HIGH:
                    n_fires += 1
                if d < min_peer_d:
                    min_peer_d = d

            per_surah[label]["n_peer_pairs"] = n_pairs
            per_surah[label]["n_peer_fires"] = n_fires
            per_surah[label]["fpr"] = n_fires / n_pairs if n_pairs else None
            per_surah[label]["min_peer_delta"] = min_peer_d if min_peer_d < float("inf") else None
            n_total_pairs += n_pairs
            n_total_pair_fires += n_fires

            if (ix + 1) % 20 == 0:
                print(
                    f"[{EXP}]   {ix+1:3d}/114 surahs done | "
                    f"min_peer_d_so_far = {min(per_surah[lbl].get('min_peer_delta', float('inf')) for lbl in list(per_surah.keys())[:ix+1] if per_surah[lbl].get('min_peer_delta') is not None):.2f}"
                )
    else:
        n_total_pairs = 0
        n_total_pair_fires = 0

    # Strip temp keys
    for ps in per_surah.values():
        ps.pop("_var_deltas", None)

    # ---- 6. Aggregate ----
    if n_total_variants > 0:
        agg_recall = n_total_var_fires / n_total_variants
    else:
        agg_recall = None

    if n_total_pairs > 0:
        agg_fpr = n_total_pair_fires / n_total_pairs
    else:
        agg_fpr = None

    recalls = [ps["recall"] for ps in per_surah.values() if ps.get("recall") is not None]
    min_recall = min(recalls) if recalls else None
    max_recall = max(recalls) if recalls else None

    fprs = [ps["fpr"] for ps in per_surah.values() if ps.get("fpr") is not None]
    min_fpr = min(fprs) if fprs else None
    max_fpr = max(fprs) if fprs else None

    # ---- 7. Verdict ladder ----
    if audit_hook_violated:
        verdict = "FAIL_audit_hook_violated"
    elif agg_recall is None or agg_recall < RECALL_FLOOR - AUDIT_TOL:
        verdict = "FAIL_recall_below_floor"
    elif min_recall is None or min_recall < RECALL_FLOOR - AUDIT_TOL:
        verdict = "FAIL_per_surah_floor"
    elif agg_fpr is not None and agg_fpr > FPR_CEIL + 1e-9:
        if agg_fpr <= PARTIAL_FPR_BAND_HI:
            verdict = "PARTIAL_fpr_band_5_to_50pct"
        else:
            verdict = "FAIL_global_fpr_overflow"
    elif agg_fpr == 0.0:
        verdict = "PASS_universal_perfect_recall_zero_fpr"
    else:
        verdict = "PASS_universal_perfect_recall"

    # ---- 8. Receipt ----
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H43",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "TAU_HIGH": TAU_HIGH,
            "AUDIT_TOL": AUDIT_TOL,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEIL": FPR_CEIL,
            "PARTIAL_FPR_BAND_HI": PARTIAL_FPR_BAND_HI,
        },
        "n_surahs_scored": len(per_surah),
        "n_variants_total": n_total_variants,
        "n_var_fires_total": n_total_var_fires,
        "n_peers_in_pool": len(peer_pool),
        "n_pair_total": n_total_pairs,
        "n_pair_fires_total": n_total_pair_fires,
        "audit": {
            "max_variant_delta": audit_max_var_delta,
            "theorem_holds": not audit_hook_violated,
            "violation_examples": audit_violation_examples,
        },
        "aggregate": {
            "recall": agg_recall,
            "fpr": agg_fpr,
            "min_per_surah_recall": min_recall,
            "max_per_surah_recall": max_recall,
            "min_per_surah_fpr": min_fpr,
            "max_per_surah_fpr": max_fpr,
        },
        "per_surah": per_surah,
        "wall_time_s": round(time.time() - t0, 3),
    }
    receipt_path = out_dir / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    # ---- 9. CSV diagnostic ----
    csv_path = out_dir / "per_surah_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "surah", "n_canon", "n_variants", "var_delta_min", "var_delta_max",
            "n_var_fires", "recall",
            "n_peer_pairs", "n_peer_fires", "fpr", "min_peer_delta",
        ])
        for label, ps in per_surah.items():
            w.writerow([
                label,
                ps.get("n_canon"),
                ps.get("n_variants"),
                ps.get("var_delta_min"),
                ps.get("var_delta_max"),
                ps.get("n_var_fires"),
                ps.get("recall"),
                ps.get("n_peer_pairs"),
                ps.get("n_peer_fires"),
                ps.get("fpr"),
                ps.get("min_peer_delta"),
            ])

    # ---- 10. Console summary ----
    print("=" * 70)
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] tau_high (frozen) = {TAU_HIGH}")
    print(f"[{EXP}] audit: max_variant_delta = {audit_max_var_delta:.4f} (theorem holds: {not audit_hook_violated})")
    print(f"[{EXP}] aggregate recall = {agg_recall}, FPR = {agg_fpr}")
    print(f"[{EXP}] per-surah recall: min={min_recall}, max={max_recall}")
    print(f"[{EXP}] per-surah FPR:    min={min_fpr},   max={max_fpr}")
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] CSV:     {csv_path}")
    print(f"[{EXP}] wall_time_s = {round(time.time() - t0, 1)}")


if __name__ == "__main__":
    main()
