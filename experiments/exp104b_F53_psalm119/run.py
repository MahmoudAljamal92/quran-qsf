"""
exp104b_F53_psalm119/run.py
===========================
H59b: F53 multi-compressor consensus K=2 cross-tradition Hebrew Psalm 119
amendment pilot.

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

This is a chapter amendment of `exp104_F53_tanakh_pilot` after that pilot
returned `BLOCKED_psalm_19_too_short`. The protocol is byte-for-byte
identical EXCEPT the target chapter changes from Psalm 19 (533 letters)
to Psalm 119 (5,104 letters; longest Psalm).

NO Arabic tau is transferred. NO post-hoc K change. NO chapter re-roll
beyond Psalm 119.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
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

# Re-use the entire exp104 protocol, but override the target chapter and
# re-bind the verdict-decision step to use the Psalm-119 chapter selector.
from experiments.exp104_F53_tanakh_pilot import run as exp104_run  # noqa: E402
from experiments._lib import safe_output_dir  # noqa: E402

EXP = "exp104b_F53_psalm119"

# --- PREREG-hash sentinel (audit hook) ---------------------------------
_PREREG_EXPECTED_HASH = (
    "ba88273c27738c764d3f0b06448a75049f2ec0b48535a925b94c946ea3e5998d"
)

# --- Override the target chapter (only difference from exp104) ---------
TARGET_BOOK = "תהלים"  # Psalms (WLC spelling)
TARGET_CHAPTER = "קיט"  # Psalm 119 (qof-yod-tet = 100+10+9 = 119)


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
            f"PREREG.md was modified after run.py was locked."
        )
    return actual


def main() -> int:
    print(f"# {EXP} -- starting (Psalm 119 amendment of exp104 Psalm 19 pilot)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    print(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # Step 1: load Tanakh + locate Psalm 119
    print("# Step 1: loading Hebrew Tanakh ...")
    try:
        chapters = exp104_run._load_tanakh_chapters()
    except Exception as e:
        audit["ok"] = False
        audit["errors"].append(f"corpus_load_failed: {type(e).__name__}: {e}")
        return _write_receipt("BLOCKED_corpus_missing",
                              "WLC corpus load failed.",
                              audit, t_start, started_at_utc, actual_hash, {})

    audit["checks"]["n_chapters_total"] = len(chapters)

    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append(
            f"psalm_119_not_found (book={TARGET_BOOK!r} chapter={TARGET_CHAPTER!r})"
        )
        return _write_receipt("BLOCKED_corpus_missing",
                              f"Psalm 119 not found under book={TARGET_BOOK!r} "
                              f"chapter={TARGET_CHAPTER!r}.",
                              audit, t_start, started_at_utc, actual_hash, {})

    target = target_match[0]
    print(f"# Psalm 119 located: {target['n_verses']} verses, "
          f"{target['n_letters']} consonant-skeleton letters.")
    audit["checks"]["target_book"] = TARGET_BOOK
    audit["checks"]["target_chapter"] = TARGET_CHAPTER
    audit["checks"]["target_n_verses"] = target["n_verses"]
    audit["checks"]["target_n_letters"] = target["n_letters"]

    # Branch 2 floor
    if (target["n_letters"] < exp104_run.PSALM_19_MIN_LETTERS or
            target["n_verses"] < exp104_run.PSALM_19_MIN_VERSES):
        return _write_receipt(
            "BLOCKED_psalm_119_too_short",
            f"Psalm 119 has {target['n_letters']} letters / "
            f"{target['n_verses']} verses (need >= "
            f"{exp104_run.PSALM_19_MIN_LETTERS} / "
            f"{exp104_run.PSALM_19_MIN_VERSES}).",
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_119": _meta(target)},
        )

    # Step 2: peer pool (length-matched ± 30 %)
    target_len = target["n_letters"]
    lo = int(target_len * (1 - exp104_run.LENGTH_MATCH_FRAC))
    hi = int(target_len * (1 + exp104_run.LENGTH_MATCH_FRAC))
    peers_raw = [c for c in chapters
                 if c["book"] in exp104_run.PEER_BOOKS
                 and lo <= c["n_letters"] <= hi]
    import random
    rng = random.Random(exp104_run.SEED)
    rng.shuffle(peers_raw)
    peers = peers_raw[:exp104_run.TARGET_N_PEERS]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} chapters in [{lo}, {hi}] letters")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_length_range"] = [lo, hi]

    if n_peers < exp104_run.PEER_AUDIT_FLOOR:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_floor:{n_peers}<{exp104_run.PEER_AUDIT_FLOOR}"
        )
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool has {n_peers} chapters (need >= "
            f"{exp104_run.PEER_AUDIT_FLOOR}).",
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_119": _meta(target), "peers_n": n_peers,
             "peer_length_range": [lo, hi]},
        )

    # Step 3: per-peer Delta calibration
    print(f"# Step 3: calibrating tau ({n_peers} peers × "
          f"{exp104_run.N_CALIB_VARIANTS_PER_PEER} variants/peer × 4 compressors)...")
    import numpy as np
    calib_deltas: dict[str, list[float]] = {n: [] for n in exp104_run._COMPRESSOR_NAMES}
    for i, peer in enumerate(peers):
        skel = peer["letters_22"]
        all_vars = exp104_run._enumerate_variants(skel)
        if len(all_vars) <= exp104_run.N_CALIB_VARIANTS_PER_PEER:
            sampled = all_vars
        else:
            local_rng = random.Random(exp104_run.SEED + i)
            sampled = local_rng.sample(all_vars, exp104_run.N_CALIB_VARIANTS_PER_PEER)
        for (pos, _orig, repl) in sampled:
            variant = exp104_run._apply_variant(skel, pos, repl)
            deltas = exp104_run._per_compressor_deltas(skel, variant)
            for name, d in deltas.items():
                calib_deltas[name].append(d)
        if (i + 1) % 25 == 0:
            print(f"#   {i+1}/{n_peers} peers calibrated "
                  f"(elapsed: {time.time() - t_start:.1f} s)")

    tau: dict[str, float] = {
        name: float(np.percentile(np.asarray(arr, dtype=float),
                                  exp104_run.TAU_PERCENTILE))
        if arr else float("nan")
        for name, arr in calib_deltas.items()
    }
    print(f"# Locked Hebrew tau (5th percentile of peer Delta):")
    for name, t in tau.items():
        print(f"#   tau_{name:5s} = {t:.6f} (n_calib = {len(calib_deltas[name])})")

    # Step 4: bootstrap tau stability
    tau_cv: dict[str, float] = {}
    boot_rng = np.random.default_rng(exp104_run.SEED)
    for name in exp104_run._COMPRESSOR_NAMES:
        arr = np.asarray(calib_deltas[name], dtype=float)
        if len(arr) < 2:
            tau_cv[name] = float("nan"); continue
        boot_taus = []
        for _ in range(exp104_run.BOOTSTRAP_N):
            idx = boot_rng.integers(0, len(arr), len(arr))
            boot_taus.append(np.percentile(arr[idx], exp104_run.TAU_PERCENTILE))
        boot_taus = np.asarray(boot_taus, dtype=float)
        mean = float(np.mean(boot_taus))
        std = float(np.std(boot_taus, ddof=1))
        cv = std / abs(mean) if abs(mean) > 1e-12 else float("inf")
        tau_cv[name] = cv
    audit["checks"]["tau_locked"] = tau
    audit["checks"]["tau_bootstrap_cv"] = tau_cv

    worst_cv = max((c for c in tau_cv.values()
                    if not np.isnan(c)), default=0.0)
    if worst_cv > exp104_run.BOOTSTRAP_CV_CEIL:
        return _write_receipt(
            "FAIL_audit_tau_unstable",
            f"Bootstrap CV worst = {worst_cv:.3f} > {exp104_run.BOOTSTRAP_CV_CEIL}.",
            audit, t_start, started_at_utc, actual_hash,
            {"psalm_119": _meta(target), "peers_n": n_peers,
             "tau": tau, "tau_bootstrap_cv": tau_cv},
        )

    # Step 5: enumerate ALL Psalm 119 variants and score
    psalm_skel = target["letters_22"]
    variants = exp104_run._enumerate_variants(psalm_skel)
    n_var = len(variants)
    print(f"# Step 5: scoring {n_var} Psalm 119 variants ...")
    fires_at_k = {1: 0, 2: 0, 3: 0, 4: 0}
    n_proc = 0
    for (pos, _orig, repl) in variants:
        variant = exp104_run._apply_variant(psalm_skel, pos, repl)
        deltas = exp104_run._per_compressor_deltas(psalm_skel, variant)
        n_above = sum(1 for name in exp104_run._COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        for k in (1, 2, 3, 4):
            if n_above >= k:
                fires_at_k[k] += 1
        n_proc += 1
        if n_proc % 5000 == 0:
            elapsed = time.time() - t_start
            eta = elapsed * (n_var - n_proc) / max(1, n_proc)
            print(f"#   {n_proc}/{n_var} ({100.0*n_proc/n_var:.1f}%) "
                  f"elapsed {elapsed:.0f}s ETA {eta:.0f}s")

    recalls = {f"K={k}": fires_at_k[k] / n_var for k in (1, 2, 3, 4)}
    recall_k2 = recalls["K=2"]
    print(f"# Psalm 119 recalls: {recalls}")
    audit["checks"]["psalm_119_recalls"] = recalls
    audit["checks"]["psalm_119_n_variants"] = n_var

    # Step 6: FPR on peer-vs-peer pairs
    pair_rng = random.Random(exp104_run.SEED + 1000)
    fpr_fires = 0
    n_fpr_eval = 0
    for _ in range(exp104_run.N_FPR_PAIRS):
        a, b = pair_rng.sample(peers, 2)
        sa, sb = a["letters_22"], b["letters_22"]
        if not sa or not sb:
            continue
        deltas = exp104_run._per_compressor_deltas(sa, sb)
        n_above = sum(1 for name in exp104_run._COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        if n_above >= exp104_run.CONSENSUS_K:
            fpr_fires += 1
        n_fpr_eval += 1
    fpr_k2 = fpr_fires / n_fpr_eval if n_fpr_eval > 0 else float("nan")
    print(f"# K=2 FPR = {fpr_fires}/{n_fpr_eval} = {fpr_k2:.4f}")
    audit["checks"]["fpr_k2"] = fpr_k2
    audit["checks"]["fpr_n_pairs_evaluated"] = n_fpr_eval

    # Step 7: verdict ladder
    if recall_k2 < exp104_run.RECALL_FLOOR:
        if (recall_k2 >= exp104_run.PARTIAL_RECALL_FLOOR and
                fpr_k2 <= exp104_run.FPR_CEIL):
            verdict, msg = ("PARTIAL_recall_above_99",
                            f"Recall = {recall_k2:.4f} ∈ "
                            f"[{exp104_run.PARTIAL_RECALL_FLOOR}, "
                            f"{exp104_run.RECALL_FLOOR}); FPR = {fpr_k2:.4f} OK. "
                            f"Indicative; not paper-grade.")
        else:
            verdict, msg = ("FAIL_recall_below_floor",
                            f"K=2 recall = {recall_k2:.4f} < "
                            f"{exp104_run.RECALL_FLOOR}.")
    elif fpr_k2 > exp104_run.FPR_CEIL:
        verdict, msg = ("FAIL_fpr_above_ceiling",
                        f"K=2 FPR = {fpr_k2:.4f} > {exp104_run.FPR_CEIL}.")
    else:
        verdict, msg = ("PASS_consensus_100",
                        f"recall = {recall_k2:.4f} >= {exp104_run.RECALL_FLOOR} "
                        f"AND FPR = {fpr_k2:.4f} <= {exp104_run.FPR_CEIL}. "
                        f"F53 rule generalises to Hebrew Psalm 119.")

    print(f"# VERDICT: {verdict}")
    print(f"# Reason: {msg}")

    return _write_receipt(
        verdict, msg, audit, t_start, started_at_utc, actual_hash,
        {
            "psalm_119": _meta(target),
            "peers_n": n_peers,
            "peer_length_range": [lo, hi],
            "tau": tau,
            "tau_bootstrap_cv": tau_cv,
            "psalm_119_recalls": recalls,
            "psalm_119_n_variants": n_var,
            "fpr_k2": fpr_k2,
            "fpr_n_pairs": n_fpr_eval,
        },
    )


def _meta(chap: dict) -> dict:
    return {k: v for k, v in chap.items() if k != "verses_raw"}


def _write_receipt(verdict: str, msg: str, audit: dict, t_start: float,
                   started_at_utc: str, prereg_hash_actual: str,
                   extras: dict) -> int:
    out_dir = safe_output_dir(EXP)
    receipt_path = out_dir / f"{EXP}.json"
    elapsed = time.time() - t_start
    completed_at_utc = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": EXP,
        "hypothesis_id": "H59b",
        "hypothesis": (
            "F53 multi-compressor consensus K=2 with Hebrew-side tau "
            "calibration closes single-letter forgery on Psalm 119 at "
            "recall >= 0.999 / FPR <= 0.05. Amendment of H59 after "
            "Psalm-19 BLOCKED (length floor)."
        ),
        "verdict": verdict,
        "verdict_reason": msg,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": elapsed,
        "prereg_hash": prereg_hash_actual,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp104b_F53_psalm119/PREREG.md",
        "amendment_of": "exp104_F53_tanakh_pilot",
        "amendment_reason": (
            "exp104 (Psalm 19) returned BLOCKED_psalm_19_too_short; "
            "this amendment changes the target chapter only."
        ),
        "frozen_constants": {
            "SEED": exp104_run.SEED,
            "consensus_K": exp104_run.CONSENSUS_K,
            "tau_percentile": exp104_run.TAU_PERCENTILE,
            "length_match_frac": exp104_run.LENGTH_MATCH_FRAC,
            "compressors": list(exp104_run._COMPRESSOR_NAMES),
            "compressor_levels": {
                "gzip": exp104_run.GZIP_LEVEL,
                "bz2": exp104_run.BZ2_LEVEL,
                "lzma": exp104_run.LZMA_PRESET,
                "zstd": exp104_run.ZSTD_LEVEL,
            },
            "target_book": TARGET_BOOK,
            "target_chapter": TARGET_CHAPTER,
            "target_min_letters": exp104_run.PSALM_19_MIN_LETTERS,
            "target_min_verses": exp104_run.PSALM_19_MIN_VERSES,
            "peer_books": list(exp104_run.PEER_BOOKS),
            "target_n_peers": exp104_run.TARGET_N_PEERS,
            "peer_audit_floor": exp104_run.PEER_AUDIT_FLOOR,
            "n_calib_variants_per_peer": exp104_run.N_CALIB_VARIANTS_PER_PEER,
            "bootstrap_n": exp104_run.BOOTSTRAP_N,
            "bootstrap_cv_ceil": exp104_run.BOOTSTRAP_CV_CEIL,
            "recall_floor": exp104_run.RECALL_FLOOR,
            "fpr_ceil": exp104_run.FPR_CEIL,
            "n_fpr_pairs": exp104_run.N_FPR_PAIRS,
        },
        "audit_report": audit,
        **extras,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"# Receipt written: {receipt_path}")
    print(f"# Wall time: {elapsed:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
