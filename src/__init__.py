# -*- coding: utf-8 -*-
"""
QSF (Quranic Structural Fingerprint) — reproducibility package.

Layout:
    src.raw_loader       — reads data/corpora/<lang>/* into Unit objects
    src.verify_corpora   — G1-G5 sanity-check gate
    src.roots            — CamelTools-backed root extraction (cached)
    src.features         — 5-D feature extraction (EL, VL_CV, CN, H_cond, T)
    src.extended_tests   — tests T5-T15 (post-paper extensions, round 1)
    src.extended_tests2  — tests T16-T23 (last-mile tests, round 2)
    src.clean_pipeline   — single entrypoint: raw data -> 23 tests -> report

Run the full pipeline:
    python -X utf8 -u -m src.clean_pipeline
"""

__version__ = "2.0.0"
