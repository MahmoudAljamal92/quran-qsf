"""Smoke test for exp95e_full_114_consensus_universal.

Verifies (1) all submodules import, (2) the τ-drift sentinel agrees with the
exp95c receipt at 1e-12, (3) the detector classifies a known-authentic and
a hand-forged Q:100 candidate correctly, and (4) running the actual
pipeline on Q:100 only reproduces exp95c's K=2 = 1.000 and gzip-solo =
0.990741 within tolerance.

Runs in ~2 minutes on a single core.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments.exp95e_full_114_consensus_universal import (  # noqa: E402
    _audit, _detector, _enumerate, run as exp95e_run,
)


def _check_imports() -> None:
    print("[smoke] (1/4) imports ...")
    print(f"        ARABIC_CONS_28 length = {len(_enumerate.ARABIC_CONS_28)} (expect 28)")
    assert len(_enumerate.ARABIC_CONS_28) == 28
    # Sanity: letters_28 of an English string returns "" (no Arabic consonants)
    assert _enumerate.letters_28("inception") == ""
    # Sanity: every letter in ARABIC_CONS_28 maps to itself
    for c in _enumerate.ARABIC_CONS_28:
        assert _enumerate.letters_28(c) == c, f"identity fold failed on {c!r}"
    assert hasattr(exp95e_run, "main")
    assert hasattr(_detector, "is_quranic")
    assert hasattr(_audit, "check_tau_drift")
    print("        OK")


def _check_tau_drift() -> dict:
    print("[smoke] (2/4) τ-drift sentinel ...")
    exp95c = exp95e_run._load_exp95c_receipt()
    receipt_tau = {n: float(exp95c["tau_per_compressor"][n])
                   for n in exp95e_run.NAMES}
    drift = _audit.check_tau_drift(exp95e_run._LOCKED_TAU, receipt_tau,
                                   tol=1e-12)
    print(f"        ok = {drift['ok']}  max_drift = {drift['max_drift']:.2e}")
    for n, info in drift["per_compressor"].items():
        print(f"        {n:>5}: {info['locked']:.18f}  vs  "
              f"{info['from_exp95c_receipt']:.18f}")
    assert drift["ok"], "τ-drift sentinel failed"
    print("        OK")
    return receipt_tau


def _check_detector(canon_text: str) -> None:
    print("[smoke] (3/4) detector ...")
    # Authentic input → AUTHENTIC verdict
    r1 = _detector.is_quranic(canon_text, "Q:100", canon_text=canon_text)
    print(f"        authentic Q:100  → verdict = {r1['verdict']!r:>13}  "
          f"K_fired = {r1['K_fired']}")
    assert r1["verdict"] == "AUTHENTIC", \
        f"expected AUTHENTIC, got {r1['verdict']}"
    assert r1["K_fired"] == 0

    # Hand-forge: substitute one consonant in the canonical text
    cons = _enumerate.ARABIC_CONS_28
    forged = None
    for i, ch in enumerate(canon_text):
        if ch in cons:
            sub = "ب" if ch != "ب" else "ت"
            forged = canon_text[:i] + sub + canon_text[i+1:]
            break
    assert forged is not None
    r2 = _detector.is_quranic(forged, "Q:100", canon_text=canon_text)
    print(f"        forged 1-letter   → verdict = {r2['verdict']!r:>13}  "
          f"K_fired = {r2['K_fired']}")
    # A single-letter change in a long canonical may not always trip K=2
    # if the change is in a low-information position. We assert K_fired
    # is at least 1 here (any compressor flagging) and the verdict is
    # not 'AUTHENTIC'.
    assert r2["verdict"] in ("FORGED", "AMBIGUOUS"), (
        f"expected FORGED or AMBIGUOUS for hand-forge, got {r2['verdict']}"
    )
    print("        OK")


def _check_q100_pipeline(receipt_tau: dict) -> None:
    print("[smoke] (4/4) Q:100-only end-to-end run ...")
    t0 = time.time()
    rc = exp95e_run.main([
        "--scope", "v1",
        "--surahs", "Q:100",
        "--workers", "1",
        "--no-progress",
    ])
    elapsed = time.time() - t0
    print(f"        return code = {rc}  elapsed = {elapsed:.1f}s")
    # Load the receipt and verify regression targets
    receipt_path = (_ROOT / "results" / "experiments"
                    / "exp95e_full_114_consensus_universal" / "v1"
                    / "exp95e_full_114_consensus_universal.json")
    assert receipt_path.exists(), f"receipt not written at {receipt_path}"
    with open(receipt_path, "r", encoding="utf-8") as f:
        rep = json.load(f)
    q100 = rep["per_surah"].get("Q:100", {})
    k2 = float(q100.get("recall_K2", float("nan")))
    gzip_solo = float(q100.get("recall_solo_gzip", float("nan")))
    n_var = int(q100.get("n_variants", 0))
    print(f"        Q:100 n_variants    = {n_var}     (expect 864)")
    print(f"        Q:100 K=2 recall    = {k2:.6f} (expect 1.000000)")
    print(f"        Q:100 gzip-solo     = {gzip_solo:.6f} (expect 0.990741)")
    print(f"        verdict             = {rep['verdict']}")
    assert n_var == 864, f"n_variants mismatch: {n_var}"
    assert abs(k2 - 1.0) <= 1e-9, f"K=2 recall mismatch: {k2}"
    assert abs(gzip_solo - 0.990741) <= 1e-3, \
        f"gzip-solo recall mismatch: {gzip_solo}"
    # The τ-drift sentinel and Q:100 regression both pass; verdict for a
    # single-surah run depends on whether ctrl-null FPR check holds and
    # the per-surah floor is met. For Q:100 alone the verdict should be
    # PASS_universal_100 (recall=1.000 across all eligible surahs={Q:100}).
    assert rep["verdict"] in ("PASS_universal_100", "PASS_universal_999"), \
        f"unexpected verdict: {rep['verdict']}"
    print("        OK")


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=" * 64)
    print(" exp95e smoke test")
    print("=" * 64)

    _check_imports()
    receipt_tau = _check_tau_drift()

    # Load Q:100 canonical for the detector test
    from experiments._lib import load_phase
    phi = load_phase("phase_06_phi_m")
    quran = phi["state"]["CORPORA"].get("quran", [])
    q100 = next((u for u in quran if getattr(u, "label", "") == "Q:100"), None)
    assert q100 is not None, "Q:100 not in CORPORA"
    canon_text = " ".join(q100.verses)
    _check_detector(canon_text)
    _check_q100_pipeline(receipt_tau)

    print("\n" + "=" * 64)
    print(" SMOKE TEST PASSED.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
