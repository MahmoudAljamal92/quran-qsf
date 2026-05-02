"""pristine_lib — backend for the Pristine Quran-fingerprint app.

Modules:
  constants  — locked Quran reference values + provenance manifest
  normalize  — Arabic 28-letter skeleton normaliser
  corpus     — Hafs Quran corpus loader, verbatim & fuzzy lookup
  metrics    — eight whole-corpus-pooled fingerprint axes + tampering tests
  examples   — eight demo presets covering every detection mode

Design rule: every numeric constant in this package is either
  (a) loaded at runtime from `data/corpora/ar/quran_bare.txt`
      (verified by SHA-256), or
  (b) derived analytically from (a) (e.g., log2(28) = 4.807),
or
  (c) cited to a SHA-locked experiment receipt under
      `results/experiments/expNNN_*/...json`.

There are NO hand-tuned thresholds, NO per-surah cherry-picked subsets,
and NO hidden fitted weights. See `pristine_audit.py` for the formal audit.
"""

__version__ = "1.0.0"
