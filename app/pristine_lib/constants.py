"""constants.py — locked references + provenance.

Every number returned by this module is either:
  (1) computed once at startup from quran_bare.txt (after SHA-256 verify), OR
  (2) cited to a SHA-locked experiment receipt JSON.

Nothing is hand-tuned.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

# ----- Project paths ---------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]                      # app/pristine_lib/.. -> repo root
QURAN_TXT = _ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"

# SHA-256 of quran_bare.txt locked at project closure 2026-04-30.
# If this fails, the app refuses to start (integrity guard).
QURAN_TXT_SHA256 = (
    "228df2a717671aeb9d2ff573002bd28d6b3f973f4bc7153554e3a81663d67610"
)

# ----- Arabic 28-letter skeleton (locked across the project) ---------------
ARABIC_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ALPHABET_SIZE = 28
LOG2_A = 4.807354922057604     # log2(28); analytic, not measured.

# ----- IMPORTANT METHODOLOGICAL NOTE -----------------------------------------
# All eight axis reference values used by Pristine are computed AT STARTUP
# from quran_bare.txt as WHOLE-CORPUS POOLED statistics on the concatenated
# 6,236 verses (one number per axis, no subset selection).
#
# This INTENTIONALLY DIFFERS from the project's earlier locked receipts:
#   exp183 used per-chapter medians (e.g. H_EL = 0.969, p_max = 0.7273)
#   exp177 used per-surah Higuchi averages (HFD = 0.9653, Δα = 0.5099)
#
# Those receipts are scientifically valid in their own right but are
# **per-unit aggregates**, which the project's own sharpshooter audit
# (`exp143_QFootprint_Sharpshooter_Audit/PREREG.md`) flagged as carrying
# sharpshooter risk — i.e. claims like "47/109 surahs satisfy X" implicitly
# imply "62 surahs do not", which means X is a property of a hand-picked
# subset, not the Quran-as-an-object.
#
# Pristine therefore re-computes the same axes on the WHOLE corpus pooled
# (no per-surah / per-juz' selection) and uses those values as the reference.
# These values are the unique pooled measurements the corpus carries; any
# input is compared to the same pooled measurement.
# ----------------------------------------------------------------------------

# ----- Match-formula tolerances (NOT thresholds — purely cosmetic for %) ---
# These are the *display tolerances* for the per-axis match bar.
# They are NOT pre-registered cutoffs; they are the natural scale of each
# axis used to convert |you - quran| into a 0-100% bar.
# A tolerance equal to the Quran's value reduces match% to 50% at 2x the gap.
DISPLAY_TOLERANCES: Dict[str, float] = {
    "H_EL":         0.50,     # bits; ~half a bit difference = 0% match
    "p_max":        0.30,     # 30 percentage-points gap = 0%
    "C_Omega":      0.30,
    "F75":          0.50,     # bits
    "D_max":        0.50,     # bits
    "d_info":       0.30,
    "HFD":          0.30,
    "Delta_alpha":  0.30,
}

# ----- Provenance table (cited in the app's "Data sources" panel) ----------
PROVENANCE: Dict[str, dict] = {
    "H_EL": {
        "name": "Verse-final letter entropy",
        "symbol": "H_EL",
        "unit": "bits",
        "source_file": "data/corpora/ar/quran_bare.txt (whole-corpus pooled)",
        "source_line": "Shannon entropy of the verse-final letter histogram across all 6,236 verses",
        "f_id": "F76 (pooled variant)",
        "computed_at_startup": True,
        "exp_locked_value": "exp183 per-chapter median = 0.969 (different methodology)",
        "wikipedia": "https://en.wikipedia.org/wiki/Entropy_(information_theory)",
    },
    "p_max": {
        "name": "Most-frequent verse-final letter share",
        "symbol": "p_max",
        "unit": "fraction",
        "source_file": "data/corpora/ar/quran_bare.txt (whole-corpus pooled)",
        "source_line": "Most common verse-final letter (ن) frequency across all 6,236 verses",
        "f_id": "F63 (pooled variant)",
        "computed_at_startup": True,
        "exp_locked_value": "exp183 per-chapter median = 0.7273 (different methodology)",
        "wikipedia": "https://en.wikipedia.org/wiki/Mode_(statistics)",
    },
    "C_Omega": {
        "name": "Rhyme channel utilisation",
        "symbol": "C_Ω",
        "unit": "fraction",
        "source_file": "derived: C_Ω = 1 - H_EL / log2(28)",
        "source_line": "From pooled H_EL above",
        "f_id": "F67 (pooled variant)",
        "computed_at_startup": True,
        "wikipedia": "https://en.wikipedia.org/wiki/Channel_capacity",
    },
    "F75": {
        "name": "Universal invariant",
        "symbol": "F75",
        "unit": "bits",
        "source_file": "derived: F75 = H_EL + log2(p_max * 28)",
        "source_line": "From pooled H_EL and p_max above",
        "f_id": "F75 (pooled variant)",
        "computed_at_startup": True,
        "wikipedia": "https://en.wikipedia.org/wiki/Information_theory",
    },
    "D_max": {
        "name": "Redundancy gap",
        "symbol": "D_max",
        "unit": "bits",
        "source_file": "derived: D_max = log2(28) - H_EL",
        "source_line": "From pooled H_EL above",
        "f_id": "F79 (pooled variant)",
        "computed_at_startup": True,
        "wikipedia": "https://en.wikipedia.org/wiki/Redundancy_(information_theory)",
    },
    "d_info": {
        "name": "IFS fractal information dimension",
        "symbol": "d_info",
        "unit": "dimensionless",
        "source_file": "data/corpora/ar/quran_bare.txt + d_info = H_nats / log(1/0.18)",
        "source_line": "Computed on whole-corpus letter-frequency distribution",
        "f_id": "F82",
        "computed_at_startup": True,
        "exp_locked_value": "exp182 = 1.667 (whole-corpus, matches our computation)",
        "wikipedia": "https://en.wikipedia.org/wiki/Information_dimension",
    },
    "HFD": {
        "name": "Higuchi fractal dimension",
        "symbol": "HFD",
        "unit": "dimensionless",
        "source_file": "data/corpora/ar/quran_bare.txt (whole-Quran verse-length series)",
        "source_line": "Higuchi 1988 algorithm on the 6,236-point series of verse lengths",
        "f_id": "F87a (pooled variant)",
        "computed_at_startup": True,
        "exp_locked_value": "exp177 per-surah mean = 0.9653 (different methodology)",
        "wikipedia": "https://en.wikipedia.org/wiki/Higuchi_dimension",
    },
    "Delta_alpha": {
        "name": "Multifractal spectrum width",
        "symbol": "Δα",
        "unit": "dimensionless",
        "source_file": "data/corpora/ar/quran_bare.txt (whole-Quran verse-length series)",
        "source_line": "MFDFA (Kantelhardt 2002) on the 6,236-point series of verse lengths",
        "f_id": "F87b (pooled variant)",
        "computed_at_startup": True,
        "exp_locked_value": "exp177 per-surah aggregate = 0.5099 (different methodology)",
        "wikipedia": "https://en.wikipedia.org/wiki/Multifractal_system",
    },
}

# ----- Tampering forensics references ---------------------------------------
TAMPERING_REFS: Dict[str, dict] = {
    "F55_bigram_shift": {
        "theorem": "F69 — single-letter edit causes Δ_bigram ∈ [1, 2]",
        "source_file": "experiments/exp95i_bigram_shift_detector/PREREG.md",
        "expected_per_edit": (1.0, 2.0),
        "wikipedia": "https://en.wikipedia.org/wiki/Bigram",
    },
    "gzip_NCD": {
        "theorem": "F70 — gzip catches verse-reorder at 88.4% recall",
        "source_file": "results/experiments/exp117_verse_reorder_detector.json",
        "form3_recall": 0.884,
        "form4_combined_recall": 0.930,
        "wikipedia": "https://en.wikipedia.org/wiki/Normalized_compression_distance",
    },
}


@dataclass(frozen=True)
class IntegrityCheck:
    ok: bool
    sha256_actual: str
    sha256_expected: str
    n_bytes: int


def verify_quran_corpus() -> IntegrityCheck:
    """Verify quran_bare.txt SHA-256 matches the locked hash. Raises if mismatch.

    Called at app cold-start. Failure -> the app refuses to render and
    instructs the user to re-pull the locked corpus.
    """
    if not QURAN_TXT.exists():
        raise FileNotFoundError(
            f"quran_bare.txt missing at {QURAN_TXT}. The app cannot start."
        )
    raw = QURAN_TXT.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    ok = actual == QURAN_TXT_SHA256
    if not ok:
        raise ValueError(
            f"quran_bare.txt SHA-256 mismatch.\n"
            f"  expected: {QURAN_TXT_SHA256}\n"
            f"  actual:   {actual}\n"
            f"Refusing to start. Re-pull the locked corpus."
        )
    return IntegrityCheck(
        ok=ok,
        sha256_actual=actual,
        sha256_expected=QURAN_TXT_SHA256,
        n_bytes=len(raw),
    )


__all__ = [
    "ARABIC_28", "ALPHABET_SIZE", "LOG2_A",
    "QURAN_TXT", "QURAN_TXT_SHA256",
    "DISPLAY_TOLERANCES", "PROVENANCE", "TAMPERING_REFS",
    "verify_quran_corpus", "IntegrityCheck",
]
