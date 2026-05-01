"""scripts/_mark1_peer_sizing.py

Pre-run sizing diagnostic for exp104d (Greek NT Mark 1). Counts the
length-matched NT-narrative peer pool and verifies Mark 1 clears the locked
chapter-length floor. NO compression calls are issued (allowed by PREREG
exp104d §3 which explicitly permits this diagnostic).
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from experiments.exp104d_F53_mark1 import run as exp104d_run  # noqa: E402


def main() -> int:
    print("# Pre-run sizing for exp104d_F53_mark1 (Greek NT Mark 1)")
    print("# This script issues NO compression calls.")
    print("")

    # 0. Normaliser sentinel
    sentinel_actual = exp104d_run._normalise_greek(
        exp104d_run._NORMALISER_SENTINEL_INPUT
    )
    print(f"# Normaliser sentinel:")
    print(f"#   input    = {exp104d_run._NORMALISER_SENTINEL_INPUT!r}")
    print(f"#   expected = {exp104d_run._NORMALISER_SENTINEL_EXPECTED!r}")
    print(f"#   actual   = {sentinel_actual!r}")
    if sentinel_actual != exp104d_run._NORMALISER_SENTINEL_EXPECTED:
        print("#   STATUS   = FAIL (sentinel drift; would block exp104d run)")
        return 2
    print(f"#   STATUS   = OK")
    print("")

    # 1. Load corpus
    print("# Loading OpenGNT v3.3 ...")
    chapters = exp104d_run._load_greek_nt_chapters()
    print(f"# {len(chapters)} chapters loaded.")
    print("")

    # 2. Locate Mark 1
    mark1 = [c for c in chapters
             if c["book"] == exp104d_run.TARGET_BOOK_NUMBER
             and c["chapter"] == exp104d_run.TARGET_CHAPTER]
    if not mark1:
        print("# FAIL: Mark 1 not found.")
        # show what books are present
        present_books = sorted({c["book"] for c in chapters})
        print(f"# books present: {present_books}")
        return 3
    target = mark1[0]
    print(f"# Mark 1 located:")
    print(f"#   n_verses                = {target['n_verses']}")
    print(f"#   n_letters (skeleton)    = {target['n_letters']}")
    print(f"#   target_min_letters       = {exp104d_run.TARGET_MIN_LETTERS}  "
          f"(verdict 'BLOCKED_mark1_too_short' fires if below)")
    print(f"#   target_min_verses        = {exp104d_run.TARGET_MIN_VERSES}")
    if target["n_letters"] < exp104d_run.TARGET_MIN_LETTERS:
        print(f"#   STATUS = WOULD-BLOCK (n_letters too small)")
        return 4
    if target["n_verses"] < exp104d_run.TARGET_MIN_VERSES:
        print(f"#   STATUS = WOULD-BLOCK (n_verses too small)")
        return 4
    print(f"#   STATUS = OK (clears letter and verse floors)")
    print("")

    # 3. Peer pool
    target_len = target["n_letters"]
    frac = exp104d_run.exp104_run.LENGTH_MATCH_FRAC
    lo = int(target_len * (1 - frac))
    hi = int(target_len * (1 + frac))
    peers = [c for c in chapters
             if c["book"] in exp104d_run.PEER_BOOK_NUMBERS
             and lo <= c["n_letters"] <= hi]
    print(f"# Peer pool sizing:")
    print(f"#   peer_books               = {exp104d_run.PEER_BOOK_NUMBERS}  "
          f"(Matt, Luke, John, Acts, Hebrews)")
    print(f"#   length_match_frac        = +-{frac:.0%}")
    print(f"#   length_window            = [{lo}, {hi}]")
    print(f"#   peer_pool_size           = {len(peers)}")
    print(f"#   peer_audit_floor         = {exp104d_run.exp104_run.PEER_AUDIT_FLOOR}  "
          f"(verdict 'FAIL_audit_peer_pool_size' fires if below)")
    if len(peers) < exp104d_run.exp104_run.PEER_AUDIT_FLOOR:
        print(f"#   STATUS = WOULD-FAIL (need amendment to widen window or change book set)")
        return 5
    print(f"#   STATUS = OK (clears 100-peer floor)")
    print("")

    # 4. Variant count estimate
    n_variants = target["n_letters"] * (len(exp104d_run.GREEK_LETTERS_24) - 1)
    print(f"# Variant scoring estimate:")
    print(f"#   n_letters x (alphabet-1) = {target['n_letters']} x 23 = {n_variants}")
    print(f"#   At observed exp104c rate (5.9 variants/sec on this machine):")
    print(f"#     wall_time_estimate     = {n_variants/5.9/60:.1f} min")
    print(f"#   Plus ~{exp104d_run.exp104_run.TARGET_N_PEERS * exp104d_run.exp104_run.N_CALIB_VARIANTS_PER_PEER / 5.9 / 60:.0f} min calibration "
          f"(target_n_peers={exp104d_run.exp104_run.TARGET_N_PEERS} x {exp104d_run.exp104_run.N_CALIB_VARIANTS_PER_PEER} variants/peer) "
          f"+ ~{exp104d_run.exp104_run.N_FPR_PAIRS / 5.9 / 60:.0f} min FPR.")
    print("")
    print("# All sizing checks PASSED. exp104d/run.py is launchable.")
    print("# Launch command: python -m experiments.exp104d_F53_mark1.run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
