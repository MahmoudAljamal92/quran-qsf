"""
exp95e_full_114_consensus_universal/_detector.py
================================================
Deployable forgery detector built on the K = 2 multi-compressor consensus
rule from F53. Loads frozen τ from the exp95c receipt at import time and
exposes a single public API:

    is_quranic(candidate_text: str, surah_label: str, *, canon_text: str | None = None) -> dict

Returns a verdict dict:

    {
        "verdict": "AUTHENTIC" | "FORGED" | "AMBIGUOUS",
        "K_fired": 0 | 1 | 2 | 3 | 4,
        "fires": {"gzip": bool, "bz2": bool, "lzma": bool, "zstd": bool},
        "ncd": {"gzip": float, "bz2": float, "lzma": float, "zstd": float},
        "tau_used": {<same keys>: float},  # locked from exp95c
        "confidence": float,                # K_fired / 4 (rough)
        "explanation": str,
        "surah_label": str,
        "canonical_letters_28_sha256": str,
        "candidate_letters_28_sha256": str,
    }

Decision rule:
    K_fired ≥ 2  →  FORGED        (the F53 headline rule, FPR ≤ 0.05 by construction)
    K_fired = 0  →  AUTHENTIC
    K_fired = 1  →  AMBIGUOUS     (single compressor flag; below the headline rule)

The detector is **stateless** apart from the locked τ table; it is safe to
import and call concurrently. It does NOT load the pickle corpus by
default — the caller can either pass `canon_text` directly (e.g. user-supplied
canonical Quran text) or rely on the lazy `default_canonical_loader()` which
will read `phase_06_phi_m.pkl` once and cache it.

Limitations (do not extend the verdict beyond these):
- Single-letter consonant substitutions on the Hafs ʿan ʿĀṣim text are the
  only forgery class for which F53 reports recall = 1.000 (Q:100) and
  recall ≥ 0.999 in our robustness study. Word-level edits, semantic
  substitutions, LLM-generated counterfeits, and cross-qirāʾāt confusions
  are NOT covered by this detector.
- The detector assumes the candidate is meant to BE the canonical surah
  identified by `surah_label`. It does not classify between canonical
  surahs.
- Returns AMBIGUOUS (not FORGED) at K = 1 — using K = 1 alone would inflate
  FPR to 0.177 (per the exp95c receipt). Callers who need a "loose" mode
  should examine `K_fired` directly.
"""
from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import lzma
import sys
from pathlib import Path
from typing import Any

try:
    import zstandard as zstd
    _ZSTD_AVAILABLE = True
except ImportError:
    _ZSTD_AVAILABLE = False
    zstd = None  # type: ignore

# Make sure we can import the enumerator helpers without cwd assumptions.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    letters_28,
)

# ---------------------------------------------------------------------------
# Locked compressor parameters (mirror exp95c PREREG)
# ---------------------------------------------------------------------------
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9

_NAMES = ("gzip", "bz2", "lzma", "zstd")

# ---------------------------------------------------------------------------
# Compressor primitives (byte-equal to exp95c)
# ---------------------------------------------------------------------------
_ZSTD_CCTX = zstd.ZstdCompressor(level=ZSTD_LEVEL) if _ZSTD_AVAILABLE else None


def _gz_len(b: bytes) -> int:
    return len(gzip.compress(b, compresslevel=GZIP_LEVEL))


def _bz2_len(b: bytes) -> int:
    return len(bz2.compress(b, compresslevel=BZ2_LEVEL))


def _lzma_len(b: bytes) -> int:
    return len(lzma.compress(b, preset=LZMA_PRESET))


def _zstd_len(b: bytes) -> int:
    if _ZSTD_CCTX is None:
        raise RuntimeError(
            "zstandard library not available. Install with `pip install zstandard`."
        )
    return _ZSTD_CCTX.compress(b).__len__()


_LEN_FNS = {
    "gzip": _gz_len,
    "bz2": _bz2_len,
    "lzma": _lzma_len,
    "zstd": _zstd_len,
}


def _ncd(a: str, b: str, length_fn) -> float:
    """Normalized Compression Distance between two strings."""
    if not a and not b:
        return 0.0
    ab = a.encode("utf-8")
    bb = b.encode("utf-8")
    cab = (a + b).encode("utf-8")
    za = length_fn(ab)
    zb = length_fn(bb)
    zab = length_fn(cab)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


# ---------------------------------------------------------------------------
# τ loader (locked from exp95c receipt)
# ---------------------------------------------------------------------------
_TAU_CACHE: dict[str, float] | None = None


def _exp95c_receipt_path() -> Path:
    return (
        _ROOT / "results" / "experiments"
        / "exp95c_multi_compressor_adiyat"
        / "exp95c_multi_compressor_adiyat.json"
    )


def load_locked_tau() -> dict[str, float]:
    """Load the four τ values from the exp95c receipt and cache them.

    These are the locked thresholds for the consensus rule. Callers should
    NOT recalibrate. The detector hard-fails if the receipt is missing.
    """
    global _TAU_CACHE
    if _TAU_CACHE is not None:
        return dict(_TAU_CACHE)
    p = _exp95c_receipt_path()
    if not p.exists():
        raise FileNotFoundError(
            f"Detector cannot find exp95c receipt at {p}. Run exp95c first "
            "(or pass --tau-overrides on the calling pipeline)."
        )
    with open(p, "r", encoding="utf-8") as f:
        j = json.load(f)
    tau = j.get("tau_per_compressor", {})
    if not all(name in tau for name in _NAMES):
        raise RuntimeError(
            f"exp95c receipt at {p} is missing one of the τ values "
            f"({sorted(_NAMES)}). Receipt is corrupt."
        )
    _TAU_CACHE = {n: float(tau[n]) for n in _NAMES}
    return dict(_TAU_CACHE)


# ---------------------------------------------------------------------------
# Default canonical loader (lazy; caches the pickle)
# ---------------------------------------------------------------------------
_CANON_CACHE: dict[str, str] = {}


def default_canonical_loader(surah_label: str) -> str:
    """Lazy loader: returns the canonical full-surah text for `surah_label`
    by reading `phase_06_phi_m.pkl` once and caching all 114 surahs.

    The text returned is `" ".join(surah.verses)` — i.e. the same form
    the exp95c protocol uses as input to `letters_28`.
    """
    if surah_label in _CANON_CACHE:
        return _CANON_CACHE[surah_label]
    from experiments._lib import load_phase  # local import to keep startup cheap
    phi = load_phase("phase_06_phi_m")
    quran = phi["state"]["CORPORA"].get("quran", [])
    for u in quran:
        label = getattr(u, "label", "")
        if label:
            _CANON_CACHE[label] = " ".join(u.verses)
    if surah_label not in _CANON_CACHE:
        raise KeyError(
            f"surah_label {surah_label!r} not found in CORPORA['quran']. "
            f"Known labels: {sorted(_CANON_CACHE.keys())[:5]}..."
        )
    return _CANON_CACHE[surah_label]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def is_quranic(
    candidate_text: str,
    surah_label: str,
    *,
    canon_text: str | None = None,
    tau_overrides: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Decide whether `candidate_text` is a faithful copy of the canonical
    surah identified by `surah_label`, using the K = 2 multi-compressor
    consensus rule from F53.

    Args:
        candidate_text: the text to be checked (Arabic, with or without
            diacritics; will be folded to the 28-consonant alphabet
            before comparison).
        surah_label: e.g. "Q:100" — used to fetch the canonical text via
            `canon_text` if provided, else via `default_canonical_loader`.
        canon_text: explicit canonical text (overrides loader). Useful for
            unit tests and for callers who want to bypass the pickle.
        tau_overrides: dict mapping compressor name → τ. ONLY for
            diagnostic use; the production path leaves this as None to
            use the locked exp95c values.

    Returns: a verdict dict; see module docstring.

    Raises:
        FileNotFoundError if the exp95c receipt is missing and τ_overrides
            is not provided.
        KeyError if `surah_label` cannot be resolved by the loader.
    """
    tau = tau_overrides if tau_overrides is not None else load_locked_tau()

    if canon_text is None:
        canon_text = default_canonical_loader(surah_label)

    canon_letters = letters_28(canon_text)
    cand_letters = letters_28(candidate_text)

    # Exact-match short-circuit. The τ thresholds in exp95c are
    # calibrated on the SIGNAL of a single-letter edit relative to the
    # canonical, NOT on the NCD-self-distance NCD(x, x). For short
    # surahs (most of the Quran), NCD(x, x) is ~0.03–0.05 due to
    # compression overhead — which exceeds τ_lzma (0.0286) and
    # τ_zstd (0.030). Without this short-circuit the detector would
    # falsely flag any byte-exact authentic candidate as FORGED.
    # The short-circuit is principled: if the letter-folded forms
    # match exactly, there is no single-letter edit to detect, so the
    # detector's output is trivially AUTHENTIC. Edits that are
    # entirely in diacritics / whitespace / non-consonant glyphs are
    # NOT in the F53 detection class either (those would require a
    # different detector calibrated on diacritic edits).
    if canon_letters == cand_letters:
        return {
            "verdict": "AUTHENTIC",
            "K_fired": 0,
            "fires": {n: False for n in _NAMES},
            "ncd": {n: 0.0 for n in _NAMES},
            "tau_used": {n: round(tau[n], 12) for n in _NAMES},
            "confidence": 0.0,
            "explanation": (
                "Letter-folded canonical and candidate are byte-identical "
                "(SHA-256 match on the 28-consonant projection). No "
                "single-letter edit to detect; AUTHENTIC by construction. "
                "NOTE: the F53 detector covers single-consonant "
                "substitutions on the 28-letter alphabet only; edits "
                "confined to diacritics / whitespace / non-consonant "
                "glyphs are out of scope."
            ),
            "surah_label": surah_label,
            "canonical_letters_28_sha256": hashlib.sha256(
                canon_letters.encode("utf-8")
            ).hexdigest(),
            "candidate_letters_28_sha256": hashlib.sha256(
                cand_letters.encode("utf-8")
            ).hexdigest(),
            "exact_match_short_circuit": True,
        }

    ncd_vals: dict[str, float] = {}
    fires: dict[str, bool] = {}
    for name in _NAMES:
        ncd_vals[name] = _ncd(canon_letters, cand_letters, _LEN_FNS[name])
        fires[name] = bool(ncd_vals[name] >= tau[name])
    K_fired = int(sum(fires.values()))

    if K_fired >= 2:
        verdict = "FORGED"
        explanation = (
            f"K = {K_fired} of 4 compressors flagged the candidate. "
            "Per the F53 K = 2 consensus rule (calibrated FPR ≤ 0.05), "
            "this is a FORGED variant of the canonical surah."
        )
    elif K_fired == 0:
        verdict = "AUTHENTIC"
        explanation = (
            "No compressor flagged the candidate at the locked τ thresholds. "
            "Under the F53 K = 2 rule, the candidate is consistent with the "
            "canonical surah at the single-letter granularity."
        )
    else:
        verdict = "AMBIGUOUS"
        explanation = (
            f"Exactly one compressor ({[n for n in _NAMES if fires[n]][0]}) "
            "flagged the candidate. Under the F53 K = 2 consensus rule, this "
            "is below the headline-fire threshold (which is 2 of 4). The "
            "candidate is AMBIGUOUS — likely authentic but at the boundary "
            "of detection."
        )

    return {
        "verdict": verdict,
        "K_fired": K_fired,
        "fires": fires,
        "ncd": {n: round(ncd_vals[n], 6) for n in _NAMES},
        "tau_used": {n: round(tau[n], 12) for n in _NAMES},
        "confidence": round(K_fired / 4.0, 4),
        "explanation": explanation,
        "surah_label": surah_label,
        "canonical_letters_28_sha256": hashlib.sha256(
            canon_letters.encode("utf-8")
        ).hexdigest(),
        "candidate_letters_28_sha256": hashlib.sha256(
            cand_letters.encode("utf-8")
        ).hexdigest(),
    }


# ---------------------------------------------------------------------------
# CLI for quick spot-checking
# ---------------------------------------------------------------------------
def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Single-letter forgery detector built on F53 K=2 consensus."
    )
    parser.add_argument("--surah", required=True, help="Surah label, e.g. Q:100")
    parser.add_argument(
        "--candidate-file", required=True,
        help="Path to UTF-8 text file containing the candidate (full surah).",
    )
    parser.add_argument(
        "--canon-file", default=None,
        help=("Optional override for the canonical text "
              "(default: load from phase_06_phi_m.pkl)."),
    )
    args = parser.parse_args()

    with open(args.candidate_file, "r", encoding="utf-8") as f:
        candidate = f.read()
    canon = None
    if args.canon_file:
        with open(args.canon_file, "r", encoding="utf-8") as f:
            canon = f.read()

    result = is_quranic(candidate, args.surah, canon_text=canon)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["verdict"] != "FORGED" else 1


if __name__ == "__main__":
    sys.exit(_cli())
