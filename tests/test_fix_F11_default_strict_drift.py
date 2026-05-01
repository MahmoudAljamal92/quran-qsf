"""Regression test for Finding F11 - experiments/_lib.py default-strict drift
+ extended _PROTECTED_FILES.

Validates two changes:
1. _PROTECTED_FILES now includes the three feature extractors that drive
   every Quran-distinctiveness claim (src/features.py, src/raw_loader.py,
   scripts/_phi_universal_xtrad_sizing.py).
2. Fingerprint drift defaults to strict (raises IntegrityError) and is
   downgraded to a warning only when QSF_RELAX_DRIFT=1 is in the env.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from experiments import _lib  # noqa: E402


def test_protected_files_include_feature_extractors() -> None:
    """The _PROTECTED_FILES list must include the three feature extractors
    flagged by F11 audit; these drive every H_EL / p_max / VL_CV-based result."""
    paths = [str(p) for p in _lib._PROTECTED_FILES]
    expected = [
        str(_REPO_ROOT / "src" / "features.py"),
        str(_REPO_ROOT / "src" / "raw_loader.py"),
        str(_REPO_ROOT / "scripts" / "_phi_universal_xtrad_sizing.py"),
    ]
    for e in expected:
        assert e in paths, f"_PROTECTED_FILES missing required entry: {e}"


def test_drift_defaults_to_strict_raises(monkeypatch) -> None:
    """With QSF_RELAX_DRIFT unset and a checkpoint whose fingerprint disagrees
    with the lock, _warn_fingerprint_drift must raise IntegrityError."""
    monkeypatch.delenv("QSF_RELAX_DRIFT", raising=False)
    monkeypatch.delenv("QSF_STRICT_DRIFT", raising=False)
    fake_entry = {
        "fingerprint": {
            "corpus_sha": "deadbeef" * 8,
            "code_sha": "feedface" * 8,
        }
    }
    cl = _lib._INTEGRITY / "corpus_lock.json"
    if not cl.exists():
        pytest.skip("corpus_lock.json missing; cannot test drift behaviour.")
    with pytest.raises(_lib.IntegrityError) as excinfo:
        _lib._warn_fingerprint_drift("phase_test_fake.pkl", fake_entry)
    assert "default-strict" in str(excinfo.value).lower() or \
           "refusing to load" in str(excinfo.value).lower()


def test_drift_relaxed_with_env_does_not_raise(monkeypatch) -> None:
    """With QSF_RELAX_DRIFT=1, drift is downgraded to a warning, not raised."""
    monkeypatch.setenv("QSF_RELAX_DRIFT", "1")
    monkeypatch.delenv("QSF_STRICT_DRIFT", raising=False)
    fake_entry = {
        "fingerprint": {
            "corpus_sha": "deadbeef" * 8,
            "code_sha": "feedface" * 8,
        }
    }
    cl = _lib._INTEGRITY / "corpus_lock.json"
    if not cl.exists():
        pytest.skip("corpus_lock.json missing; cannot test drift behaviour.")
    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _lib._warn_fingerprint_drift("phase_test_fake.pkl", fake_entry)
    assert any("FINGERPRINT DRIFT" in str(w.message) for w in caught), (
        "Expected a FINGERPRINT DRIFT warning when QSF_RELAX_DRIFT=1"
    )


def test_lib_source_uses_qsf_relax_drift_default() -> None:
    """Source-code regression: _lib.py must compute strict from QSF_RELAX_DRIFT
    (inverted), not from QSF_STRICT_DRIFT alone."""
    src = _REPO_ROOT / "experiments" / "_lib.py"
    text = src.read_text(encoding="utf-8")
    assert 'os.environ.get("QSF_RELAX_DRIFT"' in text, (
        "_lib.py must read QSF_RELAX_DRIFT environment variable for opt-out"
    )
    assert "strict = not relax" in text, (
        "_lib.py must default strict=True with relax-only opt-out"
    )
