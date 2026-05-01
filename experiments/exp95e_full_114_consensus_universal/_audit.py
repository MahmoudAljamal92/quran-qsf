"""
exp95e_full_114_consensus_universal/_audit.py
=============================================
Audit / verification helpers used by `run.py`. These run BEFORE scoring
(τ-drift sentinel, fingerprint sentinel, PREREG hash) and AFTER scoring
(missed-variant clustering, per-pair miss-rate, Q:100 regression check,
self-check end).

Every function here returns plain dicts; `run.py` collates them into the
``audit_report`` block of the receipt.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------
def sha256_of_file(path: Path) -> str:
    """Compute the SHA-256 of `path` (chunked, memory-safe)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_of_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# τ-drift sentinel
# ---------------------------------------------------------------------------
def check_tau_drift(
    locked_tau: dict[str, float],
    receipt_tau: dict[str, float],
    tol: float = 1e-12,
) -> dict[str, Any]:
    """Compare locked τ snapshot against the τ values just loaded from the
    exp95c receipt.

    Returns ``{"ok": bool, "max_drift": float, "per_compressor": {...}}``.
    """
    per: dict[str, dict[str, float]] = {}
    max_drift = 0.0
    ok = True
    for name in sorted(locked_tau.keys()):
        locked = float(locked_tau[name])
        actual = float(receipt_tau.get(name, float("nan")))
        drift = abs(locked - actual)
        if drift > tol:
            ok = False
        if drift > max_drift:
            max_drift = drift
        per[name] = {
            "locked": locked,
            "from_exp95c_receipt": actual,
            "abs_drift": drift,
            "ok": drift <= tol,
        }
    return {
        "ok": ok,
        "max_drift": max_drift,
        "tol": tol,
        "per_compressor": per,
    }


# ---------------------------------------------------------------------------
# PREREG fingerprint sentinel
# ---------------------------------------------------------------------------
def check_prereg_fingerprint(
    prereg_path: Path, expected_hash: str | None
) -> dict[str, Any]:
    """Hash the PREREG.md and compare to the expected SHA-256.

    If `expected_hash` is None or the literal sentinel "FILL_AFTER_PREREG_FROZEN",
    the check is reported as "deferred" (informational only, not a hard fail).
    This lets the very first run produce a hash that gets pinned afterwards.
    """
    actual = sha256_of_file(prereg_path) if prereg_path.exists() else None
    if expected_hash in (None, "", "FILL_AFTER_PREREG_FROZEN"):
        return {
            "ok": True,
            "deferred": True,
            "note": (
                "PREREG hash not yet pinned in run.py. After this run, "
                "copy `actual_hash` into run.py::_PREREG_EXPECTED_HASH."
            ),
            "actual_hash": actual,
            "expected_hash": expected_hash,
        }
    return {
        "ok": actual == expected_hash,
        "deferred": False,
        "actual_hash": actual,
        "expected_hash": expected_hash,
    }


# ---------------------------------------------------------------------------
# Missed-variant clustering
# ---------------------------------------------------------------------------
def cluster_missed_variants(
    missed: list[dict], cluster_warn_threshold: float = 0.10
) -> dict[str, Any]:
    """Group missed variants by (orig, repl) consonant pair and report
    miss-rate per pair.

    A "missed" variant is one with ``K_fired < 2`` (failed the headline
    K = 2 consensus). The function takes the missed-variants list and
    cross-tabulates orig→repl frequencies.

    Returns ``{"by_pair": {...}, "warnings": [...]}``.
    """
    by_pair: dict[tuple[str, str], int] = defaultdict(int)
    by_orig: dict[str, int] = defaultdict(int)
    by_repl: dict[str, int] = defaultdict(int)
    by_surah: dict[str, int] = defaultdict(int)
    for m in missed:
        orig = m.get("orig", "?")
        repl = m.get("repl", "?")
        surah = m.get("surah", "?")
        by_pair[(orig, repl)] += 1
        by_orig[orig] += 1
        by_repl[repl] += 1
        by_surah[surah] += 1

    # Convert to JSON-friendly form, sorted by descending count
    pair_list = sorted(
        ((f"{o}->{r}", n) for (o, r), n in by_pair.items()),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return {
        "n_missed": len(missed),
        "top_pairs": pair_list[:20],
        "by_orig_consonant": dict(sorted(by_orig.items(), key=lambda kv: -kv[1])),
        "by_replacement_consonant": dict(sorted(by_repl.items(), key=lambda kv: -kv[1])),
        "by_surah": dict(sorted(by_surah.items(), key=lambda kv: -kv[1])),
        "warnings": [],  # populated by caller if any pair exceeds threshold
        "warn_threshold": cluster_warn_threshold,
    }


# ---------------------------------------------------------------------------
# Q:100 regression check
# ---------------------------------------------------------------------------
def check_q100_regression(
    per_surah: dict[str, dict],
    exp94_baseline_gzip_recall: float,
    drift_tol: float = 0.001,
) -> dict[str, Any]:
    """Verify the Q:100 sub-result inside the universal run reproduces:
        (a) K = 2 recall = 1.000  (exp95c headline)
        (b) gzip-solo recall = 0.990741 ± 0.001  (exp94 baseline)

    Returns a dict with `ok`, the deltas, and the actual recalls.
    """
    q100 = per_surah.get("Q:100", {})
    k2_actual = float(q100.get("recall_K2", float("nan")))
    gzip_actual = float(q100.get("recall_solo_gzip", float("nan")))
    k2_ok = abs(k2_actual - 1.0) <= drift_tol
    gzip_ok = abs(gzip_actual - exp94_baseline_gzip_recall) <= drift_tol
    return {
        "ok": bool(k2_ok and gzip_ok),
        "K2_recall_q100": {
            "expected": 1.0,
            "actual": k2_actual,
            "abs_diff": abs(k2_actual - 1.0),
            "tol": drift_tol,
            "ok": bool(k2_ok),
        },
        "gzip_solo_recall_q100": {
            "expected": exp94_baseline_gzip_recall,
            "actual": gzip_actual,
            "abs_diff": abs(gzip_actual - exp94_baseline_gzip_recall),
            "tol": drift_tol,
            "ok": bool(gzip_ok),
        },
    }


# ---------------------------------------------------------------------------
# Per-surah variant-count sanity
# ---------------------------------------------------------------------------
def check_variant_counts_v1(per_surah: dict[str, dict]) -> dict[str, Any]:
    """For V1 scope, every surah's variant count must equal
    ``len(letters_28(v1)) * 27``. The per_surah entries store
    ``n_canon_consonants_v1`` so this can be checked without re-reading
    the corpus.

    Returns ``{"ok": bool, "mismatches": [...]}``.
    """
    mismatches = []
    for label, row in per_surah.items():
        n = int(row.get("n_variants", -1))
        n_canon = int(row.get("n_canon_consonants_v1", -1))
        expected = n_canon * 27 if n_canon >= 0 else None
        if expected is not None and n != expected:
            mismatches.append({
                "surah": label,
                "n_variants": n,
                "expected": expected,
                "n_canon_consonants_v1": n_canon,
            })
    return {"ok": not mismatches, "n_surahs": len(per_surah), "mismatches": mismatches}


# ---------------------------------------------------------------------------
# Convenience: collate everything into one audit_report block
# ---------------------------------------------------------------------------
def collate_audit_report(
    tau_drift: dict[str, Any],
    prereg_fingerprint: dict[str, Any],
    q100_regression: dict[str, Any],
    variant_counts: dict[str, Any] | None,
    missed_clusters: dict[str, Any],
    self_check_pre_ts: str,
    runtime_seconds: float,
    scope: str,
) -> dict[str, Any]:
    """Produce the audit_report block of the receipt."""
    # Promote any cluster pair above the warn threshold to a warning
    warnings: list[str] = []
    cwt = missed_clusters.get("warn_threshold", 0.10)
    n_missed_total = max(1, missed_clusters.get("n_missed", 0))
    for label, n in missed_clusters.get("top_pairs", []):
        rate = n / n_missed_total
        if rate >= cwt:
            warnings.append(
                f"missed-variant cluster {label} = {n} / {n_missed_total} "
                f"({rate:.2%}) ≥ warn threshold {cwt:.0%}"
            )
    missed_clusters["warnings"] = warnings
    return {
        "scope": scope,
        "tau_drift_sentinel": tau_drift,
        "prereg_fingerprint": prereg_fingerprint,
        "q100_regression": q100_regression,
        "variant_count_sanity": variant_counts,
        "missed_variant_clusters": missed_clusters,
        "self_check_pre_ts": self_check_pre_ts,
        "runtime_seconds": runtime_seconds,
    }
