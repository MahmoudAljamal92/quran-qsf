"""
scripts/lock_a11_ftail.py
=========================
Out-of-band lock refresh for opportunity A11 (OPPORTUNITY_TABLE_DETAIL.md).

Adds the analytic F-tail log10(p) for the Phi_M Hotelling T² to:
  - results/integrity/results_lock.json  (with hash recompute)
  - results/integrity/names_registry.json

Source-of-truth: notebooks/ultimate/_build.py (Cell 12 NAMES + Cell 13
RESULTS_LOCK) is also patched separately. This script lets the change
take effect immediately without re-running the 79-min notebook rebuild.

Idempotent: re-running with the same exp01 output is a no-op.

Hash recompute matches the verification logic in
notebooks/ultimate/_build.py:5505-5514:
    recomputed = sha256(json.dumps(entries, sort_keys=True, ensure_ascii=False))

Usage (from project root):
    python scripts/lock_a11_ftail.py

Flags:
    --dry-run    Compute new hashes and print diff, but do not write.
    --check      Verify the lock currently contains the F-tail entry and the
                 stored hash matches; exit code 0 if both pass, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_INT = _ROOT / "results" / "integrity"
_LOCK = _INT / "results_lock.json"
_NAMES = _INT / "names_registry.json"
_EXP01 = _ROOT / "results" / "experiments" / "exp01_ftail" / "exp01_ftail.json"


def _source_timestamp() -> str:
    """Return an ISO-8601 timestamp derived from the *source* (exp01 JSON)
    rather than from wall-clock `now()`. This makes re-runs of the script
    BYTE-IDEMPOTENT: same exp01 → same timestamp → same lock content →
    same hash. Audit-fix L3 2026-04-26.

    Wall-clock `now()` was the previous behaviour, which caused gratuitous
    diffs (and unnecessary lock-hash churn) every time the script was run
    even when the underlying numerical claim hadn't changed.

    Falls back to UTC `now()` only if `_EXP01` is missing — in that case
    we are running with the in-script `EXPECTED_DEFAULT` fallback anyway,
    so reproducibility is already lost.
    """
    if _EXP01.exists():
        mtime = _EXP01.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

NEW_ID = "Phi_M_F_tail_log10_p"
NEW_NAME = "Phi_M Hotelling T² analytic F-tail log10 p (mpmath 80-digit)"
NEW_TOL = 10.0
NEW_VERDICT = "PROVED HEADLINE (analytic, replaces perm-floor 1/(B+1))"
EXPECTED_DEFAULT = -480.25  # canonical headline value; refreshed from exp01 if available


def _hash_entries(entries: list) -> str:
    """Match notebooks/ultimate/_build.py:5506-5508 exactly."""
    return hashlib.sha256(
        json.dumps(entries, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_exp01_log10_p() -> float:
    """Pull the canonical mpmath log10 p from exp01_ftail.json.

    Falls back to EXPECTED_DEFAULT if exp01 hasn't been re-run since the
    headline_baselines were last updated. We round to 2 decimal places to
    avoid float-precision noise from numpy/scipy versions creeping into
    the lock baseline.
    """
    if not _EXP01.exists():
        print(f"[A11] WARNING exp01_ftail JSON missing at {_EXP01};"
              f" using fallback expected={EXPECTED_DEFAULT}.")
        return EXPECTED_DEFAULT
    d = _read_json(_EXP01)
    ts = d.get("two_sample_hotelling_T2_pooled_cov", {})
    val = ts.get("highprec_log10_p_F_tail")
    if val is None:
        print(f"[A11] WARNING exp01_ftail.json missing"
              f" two_sample_hotelling_T2_pooled_cov.highprec_log10_p_F_tail;"
              f" using fallback expected={EXPECTED_DEFAULT}.")
        return EXPECTED_DEFAULT
    rounded = round(float(val), 2)
    print(f"[A11] exp01 highprec_log10_p_F_tail raw  = {val!r}")
    print(f"[A11] exp01 rounded to 2 dp             = {rounded}")
    return rounded


def _new_lock_entry(expected: float) -> dict:
    return {
        "id": NEW_ID,
        "name": NEW_NAME,
        "expected": expected,
        "tol": NEW_TOL,
        "verdict_expected": NEW_VERDICT,
    }


def cmd_check(_args: argparse.Namespace) -> int:
    payload = _read_json(_LOCK)
    stored_hash = payload.get("hash")
    recomputed = _hash_entries(payload["entries"])
    hash_ok = stored_hash == recomputed
    has_entry = any(e.get("id") == NEW_ID for e in payload["entries"])
    names = _read_json(_NAMES).get("names", [])
    has_name = NEW_ID in names
    print(f"[check] results_lock hash:    {'OK' if hash_ok else 'MISMATCH'}"
          f"  stored={str(stored_hash)[:12]}..  recomputed={recomputed[:12]}..")
    print(f"[check] {NEW_ID} in lock:    {has_entry}")
    print(f"[check] {NEW_ID} in names:   {has_name}")
    return 0 if (hash_ok and has_entry and has_name) else 1


def cmd_refresh(args: argparse.Namespace) -> int:
    expected = _read_exp01_log10_p()

    # ---- (1) results_lock.json ----------------------------------------
    payload = _read_json(_LOCK)
    stored_hash = payload.get("hash")
    recomputed = _hash_entries(payload["entries"])
    if stored_hash != recomputed:
        print(f"[A11] ABORT: stored hash {str(stored_hash)[:12]}.. "
              f"!= recomputed {recomputed[:12]}..")
        print(f"[A11] The lock is already tampered. Refusing to overlay.")
        return 2

    entries = payload["entries"]
    existing = next((e for e in entries if e.get("id") == NEW_ID), None)
    new_entry = _new_lock_entry(expected)

    if existing is None:
        entries.append(new_entry)
        op = "ADDED"
    elif existing == new_entry:
        op = "UNCHANGED"
    else:
        existing.update(new_entry)
        op = "UPDATED"

    new_hash = _hash_entries(entries)

    # ---- (2) names_registry.json --------------------------------------
    names_payload = _read_json(_NAMES)
    names_set = set(names_payload.get("names", []))
    names_op = "UNCHANGED"
    if NEW_ID not in names_set:
        names_set.add(NEW_ID)
        names_op = "ADDED"
    new_names = sorted(names_set)

    print(f"[A11] lock entry  {op:9s}  (expected={expected})")
    print(f"[A11] names entry {names_op:9s}")
    print(f"[A11] new lock hash : {new_hash[:16]}..")

    if args.dry_run:
        print("[A11] --dry-run: no files written.")
        return 0

    _write_json(_LOCK, {
        "version": payload.get("version", 1),
        "hash": new_hash,
        "timestamp": _source_timestamp(),  # L3: from exp01 mtime, not wall-clock now()
        "entries": entries,
    })
    _write_json(_NAMES, {
        "version": names_payload.get("version", 1),
        "names": new_names,
    })

    # ---- (3) verify the write matches the verification logic in
    #         notebooks/ultimate/_build.py:5505-5514 byte-for-byte. -----
    re_payload = _read_json(_LOCK)
    re_recomputed = _hash_entries(re_payload["entries"])
    if re_payload.get("hash") != re_recomputed:
        print(f"[A11] FATAL: post-write hash MISMATCH.")
        print(f"[A11]   stored     = {re_payload.get('hash')}")
        print(f"[A11]   recomputed = {re_recomputed}")
        return 3
    print(f"[A11] post-write verify : OK"
          f"  ({len(re_payload['entries'])} entries; hash matches)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute new hash, print diff, do not write.")
    parser.add_argument("--check", action="store_true",
                        help="Verify the F-tail entry is locked; exit 0/1.")
    args = parser.parse_args(argv)

    if args.check:
        return cmd_check(args)
    return cmd_refresh(args)


if __name__ == "__main__":
    sys.exit(main())
