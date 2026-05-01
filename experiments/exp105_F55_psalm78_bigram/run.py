"""exp105_F55_psalm78_bigram/run.py
====================================
H60: F55 universal symbolic forgery detector (analytic-bound bigram-shift,
frozen tau = 2.0, no calibration) generalises to Hebrew Tanakh Psalm 78.

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol: byte-for-byte compatible with exp95j (F55 Quran V1) at the
detector level; the only deltas are (a) Hebrew 22-consonant skeleton via
exp104's _hebrew_skeleton_with_spaces, (b) Psalm 78 chapter target with
peer pool from exp104c's locked +/- 30% narrative-Hebrew window.

This run uses ZERO compression calls (analytic variant scoring is O(1)
per call; peer scoring is one Counter per chapter); predicted wall-time
< 60 s.
"""
from __future__ import annotations

import hashlib
import io
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments.exp104_F53_tanakh_pilot.run import (  # noqa: E402
    HEBREW_CONS_22,
    LENGTH_MATCH_FRAC,
    PEER_AUDIT_FLOOR,
    PEER_BOOKS,
    SEED,
    TARGET_N_PEERS,
    _hebrew_skeleton_with_spaces,
    _load_tanakh_chapters,
)

EXP = "exp105_F55_psalm78_bigram"

# ---- Live progress log (always-flushing) -------------------------------
_PROGRESS_LOG = _ROOT / "results" / "experiments" / EXP / "progress.log"
_PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
_progress_fh = open(_PROGRESS_LOG, "w", encoding="utf-8", buffering=1)


def _log(msg: str) -> None:
    print(msg, flush=True)
    _progress_fh.write(msg + "\n")
    _progress_fh.flush()


# ---- PREREG hash sentinel ----------------------------------------------
_PREREG_EXPECTED_HASH = (
    "c4aad4f49c4fba7bc7cb4271bab211cc95e80e0f25dd38c6da561aa9f3ff55ca"
)


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _enforce_prereg_hash() -> str:
    actual = _prereg_hash()
    if actual != _PREREG_EXPECTED_HASH:
        raise RuntimeError(
            f"PREREG hash mismatch:\n"
            f"  expected: {_PREREG_EXPECTED_HASH}\n"
            f"  actual  : {actual}\n"
            f"PREREG.md was modified after run.py was locked. "
            f"This run is invalidated per integrity protocol."
        )
    return actual


# ---- Frozen constants (pulled directly from PREREG §2) -----------------
TARGET_BOOK = "תהלים"
TARGET_CHAPTER = "עח"
TARGET_MIN_LETTERS = 1000
TARGET_MIN_VERSES = 10
TAU_HIGH = 2.0
AUDIT_TOL = 1e-9
RECALL_FLOOR = 1.000
FPR_CEIL = 0.000
PARTIAL_FPR_BAND_HI = 0.05


# ---- Bigram primitives (byte-for-byte aligned with exp95j) -------------

def bigrams_of(s: str) -> Counter:
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    """O(1) delta for a single substitution canon[p] -> new_ch."""
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
    return 0.5 * sum(abs(v) for v in diff.values())


# ---- Verdict ladder (PREREG §4) ----------------------------------------

def _decide_verdict(
    target_meta: dict | None,
    n_peers: int,
    max_var_delta: float | None,
    variant_recall: float | None,
    peer_fpr: float | None,
) -> tuple[str, str]:
    if target_meta is None:
        return ("BLOCKED_corpus_missing",
                "Hebrew Tanakh corpus or Psalm 78 chapter not found.")
    if (target_meta["n_letters"] < TARGET_MIN_LETTERS
            or target_meta["n_verses"] < TARGET_MIN_VERSES):
        return ("BLOCKED_psalm_78_too_short",
                f"Psalm 78 has {target_meta['n_letters']} letters / "
                f"{target_meta['n_verses']} verses (need >= "
                f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES}).")
    if n_peers < PEER_AUDIT_FLOOR:
        return ("FAIL_audit_peer_pool_size",
                f"Peer pool has {n_peers} chapters after length-matching "
                f"(need >= {PEER_AUDIT_FLOOR}).")
    if max_var_delta is not None and max_var_delta > TAU_HIGH + AUDIT_TOL:
        return ("FAIL_audit_theorem",
                f"max(variant_delta) = {max_var_delta:.6f} > "
                f"{TAU_HIGH} + {AUDIT_TOL} (theorem violation).")
    if variant_recall is None:
        return ("BLOCKED_no_variant_scoring",
                "Variant scoring did not complete.")
    if variant_recall < RECALL_FLOOR:
        return ("FAIL_recall_below_floor",
                f"variant recall = {variant_recall:.6f} < "
                f"{RECALL_FLOOR}.")
    if peer_fpr is None:
        return ("BLOCKED_no_fpr_scoring",
                "Peer FPR scoring did not complete.")
    if peer_fpr > FPR_CEIL:
        if peer_fpr <= PARTIAL_FPR_BAND_HI:
            return ("PARTIAL_fpr_below_band",
                    f"variant recall = {variant_recall:.6f} but "
                    f"peer FPR = {peer_fpr:.6f} > {FPR_CEIL} "
                    f"(within partial band {PARTIAL_FPR_BAND_HI}). "
                    f"Soft PASS, not paper-grade.")
        return ("FAIL_fpr_above_ceiling",
                f"peer FPR = {peer_fpr:.6f} > {FPR_CEIL}.")
    return ("PASS_universal_perfect_recall_zero_fpr",
            f"variant recall = {variant_recall:.6f} >= {RECALL_FLOOR} AND "
            f"peer FPR = {peer_fpr:.6f} <= {FPR_CEIL}. F55 detector "
            f"generalises off-shelf to Hebrew Tanakh Psalm 78.")


# ---- Receipt writer ----------------------------------------------------

def _write_receipt(
    verdict: str,
    verdict_reason: str,
    audit: dict,
    t_start: float,
    started_at_utc: str,
    actual_hash: str,
    extra: dict,
) -> int:
    completed_at = datetime.now(timezone.utc).isoformat()
    out_dir = _ROOT / "results" / "experiments" / EXP
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": EXP,
        "hypothesis_id": "H60",
        "hypothesis": (
            "F55 analytic-bound bigram-shift detector (frozen tau = 2.0, "
            "no calibration) generalises off-shelf to Hebrew Tanakh "
            "Psalm 78 with per-variant recall = 1.000 and per-(canon, "
            "peer)-pair FPR = 0.000."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at,
        "wall_time_s": time.time() - t_start,
        "prereg_hash": actual_hash,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp105_F55_psalm78_bigram/PREREG.md",
        "amendment_chain": [
            "exp95j_bigram_shift_universal "
            "(F55 PASS_universal_perfect_recall_zero_fpr on Quran V1)",
            "exp105_F55_psalm78_bigram (this run; F55 -> Hebrew Psalm 78)",
        ],
        "frozen_constants": {
            "SEED": SEED,
            "TAU_HIGH": TAU_HIGH,
            "AUDIT_TOL": AUDIT_TOL,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEIL": FPR_CEIL,
            "PARTIAL_FPR_BAND_HI": PARTIAL_FPR_BAND_HI,
            "LENGTH_MATCH_FRAC": LENGTH_MATCH_FRAC,
            "TARGET_BOOK": TARGET_BOOK,
            "TARGET_CHAPTER": TARGET_CHAPTER,
            "TARGET_MIN_LETTERS": TARGET_MIN_LETTERS,
            "TARGET_MIN_VERSES": TARGET_MIN_VERSES,
            "PEER_BOOKS": list(PEER_BOOKS),
            "TARGET_N_PEERS": TARGET_N_PEERS,
            "PEER_AUDIT_FLOOR": PEER_AUDIT_FLOOR,
        },
        "audit_report": audit,
        "pre_stage_diagnostic_receipt":
            "results/auxiliary/_psalm78_bigram_sizing.json",
    }
    receipt.update(extra)
    out_path = out_dir / f"{EXP}.json"
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    _log(f"# VERDICT: {verdict}")
    _log(f"# Reason: {verdict_reason}")
    _log(f"# Receipt: {out_path}")
    return 0 if verdict.startswith("PASS") else 1


def _meta(chap: dict) -> dict:
    return {
        "book": chap["book"],
        "chapter": chap["chapter"],
        "n_verses": chap["n_verses"],
        "n_letters_22": chap["n_letters"],
    }


# ---- Driver ------------------------------------------------------------

def main() -> int:
    _log(f"# {EXP} -- starting (F55 -> Hebrew Psalm 78, H60)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # 1) Load Tanakh + locate Psalm 78
    _log("# Step 1: loading Hebrew Tanakh ...")
    chapters = _load_tanakh_chapters()
    audit["checks"]["n_chapters_total"] = len(chapters)
    _log(f"#   {len(chapters)} chapters loaded")

    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK
                    and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append("psalm_78_not_found")
        return _write_receipt("BLOCKED_corpus_missing",
                              "Psalm 78 not found in WLC.",
                              audit, t_start, started_at_utc,
                              actual_hash, {})
    target = target_match[0]
    canon_no_spaces = target["letters_22"]
    canon_with_spaces = _hebrew_skeleton_with_spaces(target["verses_raw"])
    _log(f"#   Psalm 78: {target['n_verses']} verses, "
         f"{len(canon_no_spaces)} letters_22, "
         f"{len(canon_with_spaces)} chars with verse-spaces")
    audit["checks"]["target_book"] = TARGET_BOOK
    audit["checks"]["target_chapter"] = TARGET_CHAPTER
    audit["checks"]["target_n_verses"] = target["n_verses"]
    audit["checks"]["target_n_letters_22"] = len(canon_no_spaces)
    audit["checks"]["target_n_chars_with_spaces"] = len(canon_with_spaces)

    if (len(canon_no_spaces) < TARGET_MIN_LETTERS
            or target["n_verses"] < TARGET_MIN_VERSES):
        audit["ok"] = False
        return _write_receipt(
            "BLOCKED_psalm_78_too_short",
            (f"Psalm 78 has {len(canon_no_spaces)} letters / "
             f"{target['n_verses']} verses (need >= "
             f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES})."),
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_78": _meta(target)})

    # 2) Build peer pool (locked +/- 30% on letters_22 count)
    target_len = len(canon_no_spaces)
    lo = int(target_len * (1 - LENGTH_MATCH_FRAC))
    hi = int(target_len * (1 + LENGTH_MATCH_FRAC))
    peers_raw = [c for c in chapters
                 if c["book"] in PEER_BOOKS
                 and lo <= c["n_letters"] <= hi]
    rng = random.Random(SEED)
    rng.shuffle(peers_raw)
    peers = peers_raw[:TARGET_N_PEERS]
    n_peers = len(peers)
    _log(f"# Peer pool: {n_peers} narrative-Hebrew chapters "
         f"in [{lo}, {hi}] letters_22")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_length_window"] = [lo, hi]
    if n_peers < PEER_AUDIT_FLOOR:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_floor:{n_peers}<{PEER_AUDIT_FLOOR}")
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool {n_peers} < {PEER_AUDIT_FLOOR}.",
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_78": _meta(target),
             "peers_n": n_peers,
             "peer_length_window": [lo, hi]})

    # 3) Variant enumeration (full 50,064 substitutions)
    _log("# Step 3: enumerating + scoring all V1 variants ...")
    # Build the no-space-pos -> with-space-pos map
    pos_no_to_with: list[int] = []
    for i, ch in enumerate(canon_with_spaces):
        if ch in HEBREW_CONS_22:
            pos_no_to_with.append(i)
    assert len(pos_no_to_with) == len(canon_no_spaces), (
        f"position mapping inconsistent: "
        f"{len(pos_no_to_with)} vs {len(canon_no_spaces)}")

    cons_list = list(HEBREW_CONS_22)
    var_deltas: list[float] = []
    var_fires = 0
    max_var_delta = 0.0
    n_zero = 0
    n_above_tau = 0
    audit_violation_examples: list[dict] = []

    n_letters = len(canon_no_spaces)
    t_var_start = time.time()
    for p_no in range(n_letters):
        old_ch = canon_no_spaces[p_no]
        p_with = pos_no_to_with[p_no]
        for repl in cons_list:
            if repl == old_ch:
                continue
            d = variant_delta_analytic(canon_with_spaces, p_with, repl)
            var_deltas.append(d)
            if d > max_var_delta:
                max_var_delta = d
            if d == 0.0:
                n_zero += 1
            if d > TAU_HIGH + AUDIT_TOL:
                n_above_tau += 1
                if len(audit_violation_examples) < 5:
                    audit_violation_examples.append({
                        "pos_no_space": p_no,
                        "pos_with_space": p_with,
                        "old_ch": old_ch,
                        "new_ch": repl,
                        "delta": d,
                    })
            if 0 < d <= TAU_HIGH:
                var_fires += 1
        if (p_no + 1) % 500 == 0:
            _log(f"#   variant pos {p_no+1}/{n_letters} "
                 f"({time.time()-t_var_start:.1f}s)")

    n_variants_total = len(var_deltas)
    variant_recall = var_fires / n_variants_total if n_variants_total else 0.0
    _log(f"#   variants total      = {n_variants_total}")
    _log(f"#   max(variant_delta)  = {max_var_delta:.6f}")
    _log(f"#   n_above_tau (=2.0)  = {n_above_tau}")
    _log(f"#   n_zero_delta        = {n_zero}")
    _log(f"#   n_variants_fired    = {var_fires}")
    _log(f"#   variant_recall      = {variant_recall:.6f}")
    audit["checks"]["max_variant_delta"] = max_var_delta
    audit["checks"]["n_variants_total"] = n_variants_total
    audit["checks"]["n_variants_fired"] = var_fires
    audit["checks"]["n_variants_zero_delta"] = n_zero
    audit["checks"]["n_variants_above_tau"] = n_above_tau
    audit["checks"]["variant_recall"] = variant_recall

    # A1 audit: theorem
    if max_var_delta > TAU_HIGH + AUDIT_TOL:
        audit["ok"] = False
        audit["errors"].append(
            f"theorem_violation:max_variant_delta={max_var_delta}")
        return _write_receipt(
            "FAIL_audit_theorem",
            (f"max(variant_delta) = {max_var_delta:.6f} > "
             f"{TAU_HIGH} + {AUDIT_TOL} (theorem violation; would be "
             f"unprecedented across alphabets)."),
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_78": _meta(target),
             "peers_n": n_peers,
             "audit_violation_examples": audit_violation_examples})

    # 4) Peer audit: exact bigram-shift Delta vs each of n_peers chapters
    _log(f"# Step 4: scoring {n_peers} peer chapter pairs ...")
    canon_bigrams = bigrams_of(canon_with_spaces)
    peer_records: list[dict] = []
    peer_fires = 0
    min_peer_delta = float("inf")
    for peer in peers:
        peer_str = _hebrew_skeleton_with_spaces(peer["verses_raw"])
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_records.append({
            "book": peer["book"],
            "chapter": peer["chapter"],
            "n_letters_22": peer["n_letters"],
            "n_chars_with_spaces": len(peer_str),
            "delta": d,
        })
        if 0 < d <= TAU_HIGH:
            peer_fires += 1
        if d < min_peer_delta:
            min_peer_delta = d
    n_peer_pairs_total = len(peer_records)
    peer_fpr = peer_fires / n_peer_pairs_total if n_peer_pairs_total else 0.0

    peer_records_sorted = sorted(peer_records, key=lambda r: r["delta"])
    five_closest = [
        {"book": r["book"], "chapter": r["chapter"], "delta": r["delta"]}
        for r in peer_records_sorted[:5]
    ]
    _log(f"#   peer pairs total       = {n_peer_pairs_total}")
    _log(f"#   min(peer_delta)        = {min_peer_delta:.2f}")
    _log(f"#   peer pairs fired       = {peer_fires}")
    _log(f"#   peer FPR               = {peer_fpr:.6f}")
    _log(f"#   5 closest peers (raw bigram delta):")
    for c in five_closest:
        _log(f"#     {c['book']:<12s} {c['chapter']:<6s}  "
             f"delta = {c['delta']:.2f}")
    audit["checks"]["min_peer_delta"] = min_peer_delta
    audit["checks"]["n_peer_pairs_total"] = n_peer_pairs_total
    audit["checks"]["n_peer_pairs_fired"] = peer_fires
    audit["checks"]["peer_fpr"] = peer_fpr
    audit["checks"]["five_closest_peers"] = five_closest

    # A4 audit: sentinel determinism (re-run a 100-pair sample)
    _log("# Step 5: A4 sentinel determinism check ...")
    sentinel_rng = random.Random(SEED + 13)
    var_indices = list(range(n_variants_total))
    sentinel_rng.shuffle(var_indices)
    sentinel_var_idx = var_indices[:100]
    n_letters_redo = len(canon_no_spaces)
    cons_redo = list(HEBREW_CONS_22)
    sentinel_ok = True
    sentinel_err: str | None = None
    for ix in sentinel_var_idx:
        # decode (p_no, repl) from index ix
        p_no = ix // 21
        # within the 21 substitutes, skipping old_ch
        old_ch = canon_no_spaces[p_no]
        repl_idx_in_full22 = ix % 21
        # build the sub-substitute list (cons minus old_ch) preserving
        # order
        non_old = [c for c in cons_redo if c != old_ch]
        repl = non_old[repl_idx_in_full22]
        p_with = pos_no_to_with[p_no]
        d_first = var_deltas[ix]
        d_second = variant_delta_analytic(canon_with_spaces, p_with, repl)
        if d_first != d_second:
            sentinel_ok = False
            sentinel_err = (
                f"variant idx {ix} (pos_no={p_no}, repl={repl}) "
                f"non-deterministic: first={d_first}, second={d_second}")
            break
    audit["checks"]["sentinel_determinism"] = "OK" if sentinel_ok else (
        f"FAIL: {sentinel_err}")
    if not sentinel_ok:
        audit["ok"] = False
        audit["warnings"].append(
            f"sentinel_determinism_warning:{sentinel_err}")
        # Not a verdict-flip; just a warning recorded in audit.

    # 5) Decide verdict
    target_meta_for_ladder = {
        "book": target["book"],
        "chapter": target["chapter"],
        "n_verses": target["n_verses"],
        "n_letters": len(canon_no_spaces),
    }
    verdict, verdict_reason = _decide_verdict(
        target_meta_for_ladder, n_peers, max_var_delta,
        variant_recall, peer_fpr,
    )

    return _write_receipt(
        verdict, verdict_reason, audit,
        t_start, started_at_utc, actual_hash,
        {"psalm_78": _meta(target),
         "peers_n": n_peers,
         "peer_length_window": [lo, hi],
         "peer_records_top10_closest":
             [{"book": r["book"], "chapter": r["chapter"],
               "n_letters_22": r["n_letters_22"], "delta": r["delta"]}
              for r in peer_records_sorted[:10]]},
    )


if __name__ == "__main__":
    sys.exit(main())
