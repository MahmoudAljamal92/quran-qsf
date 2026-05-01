"""exp106_F55_mark1_bigram/run.py
==================================
H61: F55 universal symbolic forgery detector (analytic-bound bigram-shift,
frozen tau = 2.0, no calibration) generalises off-shelf to Greek NT
Mark 1, replicating F59 (Hebrew Psalm 78) in a different language family
(Hellenic Indo-European vs Northwest Semitic).

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol: byte-for-byte compatible with exp95j (Quran V1) and exp105
(Hebrew Psalm 78) at the detector level. Deltas:
  - Greek normaliser via experiments/exp104d_F53_mark1/run.py::_normalise_greek
    (24-letter Greek; sigma-fold + casefold + diacritic strip)
  - OpenGNT v3.3 TSV loader via experiments/exp104d_F53_mark1/run.py
  - Mark 1 chapter target (book 41 in OpenGNT internal numbering)
  - NO length matching (matches exp95j Arabic-side F55 protocol byte-exact;
    Hebrew exp105's length-match was inherited from exp104c controlled
    comparison, not from F55 itself)

This run uses ZERO compression calls; predicted wall-time < 30 s.
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

from experiments.exp104d_F53_mark1.run import (  # noqa: E402
    GREEK_LETTERS_24,
    TARGET_BOOK_NUMBER,
    TARGET_CHAPTER,
    _NORMALISER_SENTINEL_INPUT,
    _NORMALISER_SENTINEL_EXPECTED,
    _normalise_greek,
    _load_greek_nt_chapters,
)

EXP = "exp106_F55_mark1_bigram"

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
    "8397a433112e607c78a010b046725cc2ebcdd00db380fc0673bb58cbee0880e8"
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


# ---- Frozen constants (PREREG §2) --------------------------------------
TARGET_MIN_LETTERS = 1000
TARGET_MIN_VERSES = 10
TAU_HIGH = 2.0
AUDIT_TOL = 1e-9
RECALL_FLOOR = 1.000
FPR_CEIL = 0.000
PARTIAL_FPR_BAND_HI = 0.05
PEER_AUDIT_FLOOR = 100
SEED = 42


# ---- Bigram primitives (byte-for-byte aligned with exp95j/exp105) ------

def bigrams_of(s: str) -> Counter:
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
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
    normaliser_ok: bool,
    max_var_delta: float | None,
    variant_recall: float | None,
    peer_fpr: float | None,
) -> tuple[str, str]:
    if target_meta is None:
        return ("BLOCKED_corpus_missing",
                "OpenGNT corpus or Mark 1 chapter not found.")
    if (target_meta["n_letters"] < TARGET_MIN_LETTERS
            or target_meta["n_verses"] < TARGET_MIN_VERSES):
        return ("BLOCKED_mark_1_too_short",
                f"Mark 1 has {target_meta['n_letters']} letters / "
                f"{target_meta['n_verses']} verses (need >= "
                f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES}).")
    if n_peers < PEER_AUDIT_FLOOR:
        return ("FAIL_audit_peer_pool_size",
                f"Peer pool has {n_peers} chapters "
                f"(need >= {PEER_AUDIT_FLOOR}).")
    if not normaliser_ok:
        return ("FAIL_audit_normaliser_sentinel",
                "Greek normaliser sentinel does not match locked value.")
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
            f"generalises off-shelf to Greek NT Mark 1.")


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
        "hypothesis_id": "H61",
        "hypothesis": (
            "F55 analytic-bound bigram-shift detector (frozen tau = 2.0, "
            "no calibration) generalises off-shelf to Greek NT Mark 1 "
            "with per-variant recall = 1.000 and per-(canon, peer)-pair "
            "FPR = 0.000 against the full Greek NT peer pool of all 259 "
            "other chapters."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at,
        "wall_time_s": time.time() - t_start,
        "prereg_hash": actual_hash,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp106_F55_mark1_bigram/PREREG.md",
        "amendment_chain": [
            "exp95j_bigram_shift_universal "
            "(F55 PASS_universal_perfect_recall_zero_fpr on Quran V1)",
            "exp105_F55_psalm78_bigram "
            "(F59 PASS_universal_perfect_recall_zero_fpr on Hebrew Psalm 78)",
            "exp106_F55_mark1_bigram (this run; F55 -> Greek NT Mark 1)",
        ],
        "frozen_constants": {
            "SEED": SEED,
            "TAU_HIGH": TAU_HIGH,
            "AUDIT_TOL": AUDIT_TOL,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEIL": FPR_CEIL,
            "PARTIAL_FPR_BAND_HI": PARTIAL_FPR_BAND_HI,
            "TARGET_BOOK_NUMBER": TARGET_BOOK_NUMBER,
            "TARGET_CHAPTER": TARGET_CHAPTER,
            "TARGET_MIN_LETTERS": TARGET_MIN_LETTERS,
            "TARGET_MIN_VERSES": TARGET_MIN_VERSES,
            "PEER_AUDIT_FLOOR": PEER_AUDIT_FLOOR,
            "PEER_POOL_STRATEGY":
                "all_other_greek_nt_chapters_no_length_matching",
            "GREEK_LETTERS_24": GREEK_LETTERS_24,
            "calibration_source": "frozen_analytic_theorem_no_data_calibration",
        },
        "audit_report": audit,
        "pre_stage_diagnostic_receipt":
            "results/auxiliary/_mark1_bigram_sizing.json",
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
        "n_letters": chap["n_letters"],
    }


# ---- Driver ------------------------------------------------------------

def main() -> int:
    _log(f"# {EXP} -- starting (F55 -> Greek NT Mark 1, H61)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # A5: normaliser sentinel check (cheap, do early)
    sentinel_actual = _normalise_greek(_NORMALISER_SENTINEL_INPUT)
    normaliser_ok = (sentinel_actual == _NORMALISER_SENTINEL_EXPECTED)
    audit["checks"]["normaliser_sentinel"] = (
        "OK" if normaliser_ok else
        f"FAIL: expected={_NORMALISER_SENTINEL_EXPECTED!r} "
        f"actual={sentinel_actual!r}"
    )
    _log(f"# Greek normaliser sentinel: "
         f"{'OK' if normaliser_ok else 'FAIL'}")
    if not normaliser_ok:
        audit["ok"] = False
        audit["errors"].append("normaliser_sentinel_mismatch")
        return _write_receipt(
            "FAIL_audit_normaliser_sentinel",
            "Greek normaliser sentinel does not match locked value.",
            audit, t_start, started_at_utc, actual_hash, {})

    # 1) Load OpenGNT + locate Mark 1
    _log("# Step 1: loading OpenGNT v3.3 ...")
    chapters = _load_greek_nt_chapters()
    audit["checks"]["n_chapters_total"] = len(chapters)
    _log(f"#   {len(chapters)} chapters loaded")

    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK_NUMBER
                    and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append("mark_1_not_found")
        return _write_receipt(
            "BLOCKED_corpus_missing",
            "Mark 1 not found in OpenGNT corpus.",
            audit, t_start, started_at_utc, actual_hash, {})
    target = target_match[0]
    canon_str = target["letters_24"]
    _log(f"#   Mark 1: {target['n_verses']} verses, "
         f"{target['n_letters']} letter-skeleton chars")
    audit["checks"]["target_book_number"] = TARGET_BOOK_NUMBER
    audit["checks"]["target_chapter"] = TARGET_CHAPTER
    audit["checks"]["target_n_verses"] = target["n_verses"]
    audit["checks"]["target_n_letters"] = target["n_letters"]

    if (target["n_letters"] < TARGET_MIN_LETTERS
            or target["n_verses"] < TARGET_MIN_VERSES):
        audit["ok"] = False
        return _write_receipt(
            "BLOCKED_mark_1_too_short",
            (f"Mark 1 has {target['n_letters']} letters / "
             f"{target['n_verses']} verses (need >= "
             f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES})."),
            audit, t_start, started_at_utc, actual_hash,
            {"mark_1": _meta(target)})

    # 2) Build peer pool: ALL Greek NT chapters except Mark 1
    peers = [c for c in chapters
             if not (c["book"] == TARGET_BOOK_NUMBER
                     and c["chapter"] == TARGET_CHAPTER)]
    n_peers = len(peers)
    _log(f"# Peer pool: {n_peers} Greek NT chapters "
         f"(NO length matching, matches exp95j Arabic-side F55 protocol)")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_pool_strategy"] = (
        "all_other_greek_nt_chapters_no_length_matching")
    if n_peers < PEER_AUDIT_FLOOR:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_floor:{n_peers}<{PEER_AUDIT_FLOOR}")
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool {n_peers} < {PEER_AUDIT_FLOOR}.",
            audit, t_start, started_at_utc, actual_hash,
            {"mark_1": _meta(target), "peers_n": n_peers})

    # 3) Variant enumeration (full n_letters × 23 substitutions)
    _log("# Step 3: enumerating + scoring all V1 variants ...")
    cons_list = list(GREEK_LETTERS_24)
    var_deltas: list[float] = []
    var_fires = 0
    max_var_delta = 0.0
    n_zero = 0
    n_above_tau = 0
    audit_violation_examples: list[dict] = []

    n_letters = len(canon_str)
    t_var_start = time.time()
    for p in range(n_letters):
        old_ch = canon_str[p]
        # Defensive: skip if char somehow not in alphabet (post-normaliser
        # this should never trigger)
        if old_ch not in GREEK_LETTERS_24:
            continue
        for repl in cons_list:
            if repl == old_ch:
                continue
            d = variant_delta_analytic(canon_str, p, repl)
            var_deltas.append(d)
            if d > max_var_delta:
                max_var_delta = d
            if d == 0.0:
                n_zero += 1
            if d > TAU_HIGH + AUDIT_TOL:
                n_above_tau += 1
                if len(audit_violation_examples) < 5:
                    audit_violation_examples.append({
                        "pos": p,
                        "old_ch": old_ch,
                        "new_ch": repl,
                        "delta": d,
                    })
            if 0 < d <= TAU_HIGH:
                var_fires += 1
        if (p + 1) % 1000 == 0:
            _log(f"#   variant pos {p+1}/{n_letters} "
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
            {"mark_1": _meta(target),
             "peers_n": n_peers,
             "audit_violation_examples": audit_violation_examples})

    # 4) Peer audit: exact bigram-shift Delta vs each of 259 chapters
    _log(f"# Step 4: scoring {n_peers} peer chapter pairs ...")
    canon_bigrams = bigrams_of(canon_str)
    peer_records: list[dict] = []
    peer_fires = 0
    min_peer_delta = float("inf")
    for peer in peers:
        peer_str = peer["letters_24"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_records.append({
            "book": peer["book"],
            "chapter": peer["chapter"],
            "n_letters": peer["n_letters"],
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
        _log(f"#     book={c['book']:<4} chap={c['chapter']:<4}  "
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
    sentinel_ok = True
    sentinel_err: str | None = None
    for ix in sentinel_var_idx:
        # Decode (pos, repl) from index ix:
        # variant index ix corresponds to (pos = ix // 23, repl_index_in_23 = ix % 23)
        p = ix // 23
        old_ch = canon_str[p]
        non_old = [c for c in cons_list if c != old_ch]
        repl_idx = ix % 23
        repl = non_old[repl_idx]
        d_first = var_deltas[ix]
        d_second = variant_delta_analytic(canon_str, p, repl)
        if d_first != d_second:
            sentinel_ok = False
            sentinel_err = (
                f"variant idx {ix} (pos={p}, repl={repl}) "
                f"non-deterministic: first={d_first}, second={d_second}")
            break
    audit["checks"]["sentinel_determinism"] = "OK" if sentinel_ok else (
        f"FAIL: {sentinel_err}")
    if not sentinel_ok:
        audit["warnings"].append(
            f"sentinel_determinism_warning:{sentinel_err}")
        # not a verdict-flip; recorded as warning only

    # 5) Decide verdict
    target_meta_for_ladder = {
        "book": target["book"],
        "chapter": target["chapter"],
        "n_verses": target["n_verses"],
        "n_letters": target["n_letters"],
    }
    verdict, verdict_reason = _decide_verdict(
        target_meta_for_ladder, n_peers, normaliser_ok,
        max_var_delta, variant_recall, peer_fpr,
    )

    return _write_receipt(
        verdict, verdict_reason, audit,
        t_start, started_at_utc, actual_hash,
        {"mark_1": _meta(target),
         "peers_n": n_peers,
         "peer_records_top10_closest":
             [{"book": r["book"], "chapter": r["chapter"],
               "n_letters": r["n_letters"], "delta": r["delta"]}
              for r in peer_records_sorted[:10]]},
    )


if __name__ == "__main__":
    sys.exit(main())
