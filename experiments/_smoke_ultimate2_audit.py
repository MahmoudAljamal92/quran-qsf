"""Throwaway smoke-import + light self-test for the audit-fix pass.
Run from the Quran/ folder with: python experiments/_smoke_ultimate2_audit.py

Rounds covered:
  * 2026-04-20 AUDIT round 1 (SCHEMA_VERSION=2) -- basic imports, Louvain,
    BH, CharNGramLM, log_ratio, bootstrap_ci, canonical_path_length_bigram.
  * 2026-04-20 AUDIT round 2 (SCHEMA_VERSION=3) -- new whitespace-preserving
    edit generators, Greek-aware canonical-path length, rate-calibration
    helpers (auc_to_rate, calibrate_rate_above_null, signal_from_log_ratio_ci),
    MASTER's _EDIT_DETECTION / _CORPUS_AUTHENTICITY split.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # Quran/
sys.path.insert(0, str(ROOT))

# Windows consoles default to cp1252 which can't encode Arabic/Greek. Force
# utf-8 on stdout so informational prints don't crash on the smoke run.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np

from experiments._ultimate2_helpers import (
    ARABIC_CONSONANTS, SCHEMA_VERSION, auc_to_rate, benjamini_hochberg,
    bigram_jaccard_distance, bigram_jaccard_distance_greek, bootstrap_ci,
    calibrate_rate_above_null, canonical_path_length_bigram,
    canonical_path_length_bigram_greek, CharNGramLM, detect_edit_type,
    letter_bigram_set, letters_only, letters_only_greek, normalize_greek_strict,
    normalize_rasm, normalize_rasm_strict, NULLS, percentile_rank,
    R1_NULL_BASELINE_3OF9, random_multi_word_replace, random_single_letter_delete,
    random_single_letter_insert, random_single_letter_swap,
    random_single_word_delete, signal_from_log_ratio_ci,
)
assert SCHEMA_VERSION == 3, f"expected schema 3, got {SCHEMA_VERSION}"
print("helpers ok  schema=", SCHEMA_VERSION, "  nulls=", list(NULLS))

from experiments.exp09_R1_variant_forensics_9ch.run import (
    main as run_R1, channel_A_spectral, channel_C_bigram_dist, channel_D_wazn,
    CANONICAL_VARIANTS, CHANNELS_ALL, SEED,
)
print("R1 ok  channels=", CHANNELS_ALL, "  SEED=", SEED)
print("      variant kinds:", sorted({v["kind"] for v in CANONICAL_VARIANTS}))

from experiments.ultimate2_pipeline import (
    run_R2, run_R3, run_R4, run_R5, run_R6, run_R7, run_R8, run_R9,
    run_R10, run_R11, run_MASTER, SEED as PSEED, _log_ratio,
    _EDIT_DETECTION_CHANNELS, _CORPUS_AUTHENTICITY_CHANNELS,
    _EXPECTED_CHANNELS, _louvain_one_level, _pvalue_to_rate,
)
print("pipeline ok  SEED=", PSEED, "  exp_channels=", len(_EXPECTED_CHANNELS),
      " (edit=", len(_EDIT_DETECTION_CHANNELS), " auth=",
      len(_CORPUS_AUTHENTICITY_CHANNELS), ")")

# ======================================================================
# ROUND 1 self-tests
# ======================================================================
print("bigram_jaccard_distance (identical):",
      bigram_jaccard_distance("abc def abc", "abc def abc"))
print("bigram_jaccard_distance (disjoint):",
      bigram_jaccard_distance("abc def", "xyz uvw"))

# Louvain toy graph with obvious 2-community structure
comm, Q = _louvain_one_level([
    ("a", "b", 3), ("b", "c", 3), ("c", "a", 3),
    ("d", "e", 5), ("e", "f", 5), ("f", "d", 5),
    ("a", "d", 1),
])
print("toy louvain  n_comm=", len(set(comm.values())), "  Q=", round(Q, 4))

print("BH [0.01, 0.5, 0.9] alpha=0.05 ->", benjamini_hochberg([0.01, 0.5, 0.9], 0.05))
print("BH [0.01, 0.02, 0.03] alpha=0.05 ->", benjamini_hochberg([0.01, 0.02, 0.03], 0.05))

lm = CharNGramLM(n=3).fit(["hello world", "hello there", "world peace"])
print("CharNGramLM per_char_lp:", round(lm.per_char_lp("hello"), 4))
print("bootstrap_ci on [1..10]:", bootstrap_ci(list(range(1, 11)), n=200))

print("log_ratio(0, 0):", _log_ratio(0.0, 0.0))
print("log_ratio(1e-20, 1e-20):", _log_ratio(1e-20, 1e-20))
print("log_ratio(1, 1):", _log_ratio(1.0, 1.0))
print("log_ratio(4, 1):", _log_ratio(4.0, 1.0))
# F-ULT2-LOG1 (documented not patched): _log_ratio is magnitude-only, so
# all four pipeline callers (non-negative) get the correct sign. We only
# assert the non-negative contract here.
assert _log_ratio(1.0, 2.0) < 0, "log_ratio(1, 2) should be negative (num < den)"
assert _log_ratio(2.0, 1.0) > 0, "log_ratio(2, 1) should be positive (num > den)"

fake = [["a b c", "d e f"], ["g h i", "j k l"], ["m n o", "p q r"]]
print("canonical_path_length_bigram (tiny fake):",
      canonical_path_length_bigram(fake))

# ======================================================================
# ROUND 2 self-tests  (2026-04-20 AUDIT_ULTIMATE2_ROUND2)
# ======================================================================
rng = random.Random(0)

# -- F-ULT2-A1 :: new edit generators preserve whitespace -----------------
arabic_verse = normalize_rasm("بسم الله الرحمن الرحيم")
assert " " in arabic_verse, "setup: expected spaces in normalised verse"
for fn_name, fn in [
    ("swap",   lambda t, r: random_single_letter_swap(t, r)[0]),
    ("delete", lambda t, r: random_single_letter_delete(t, r)[0]),
    ("insert", lambda t, r: random_single_letter_insert(t, r)[0]),
]:
    out = fn(arabic_verse, random.Random(0))
    assert " " in out, f"F-ULT2-A1 regression: {fn_name} stripped spaces"
    print(f"whitespace-preserving {fn_name}: OK  ({arabic_verse!r} -> {out!r})")

# Word-level edits.
out, idx, w = random_single_word_delete(arabic_verse, random.Random(1))
assert idx >= 0 and w, "random_single_word_delete did not fire"
out, idx, ws = random_multi_word_replace(arabic_verse, random.Random(2), n=2)
assert idx >= 0 and len(ws) == 2, "random_multi_word_replace did not fire"
print("word_delete + multi_word_replace: OK")

# -- F-ULT2-R1n1 :: detect_edit_type dispatcher -----------------------------
# Letter-level detection even when the outer word count is preserved (the
# 3:133 case: dropping a prefix waw inside a single attached word).
cases = {
    "swap":         ("ننشزها", "ننشرها"),          # same length, same word count
    "delete":       ("مالك", "ملك"),               # shorter word, same word count
    "insert":       ("ملك", "مالك"),               # longer word, same word count
    "delete-in-phrase": ("وسارعوا الى", "سارعوا الى"),  # letter deletion inside one of two words
    "word_delete":  ("قل هو الله احد", "قل الله احد"),  # whole-word deletion
    "word_insert":  ("قل الله احد", "قل هو الله احد"),  # whole-word insertion
    "multi_word":   ("وما خلق", "والذكر والانثى"),      # multiple words differ
    "null":         ("الحمد لله", "الحمد لله"),         # identity (Arabic so rasm-preserved)
}
expected_map = {
    "swap": "swap", "delete": "delete", "insert": "insert",
    "delete-in-phrase": "delete",
    "word_delete": "word_delete", "word_insert": "word_insert",
    "multi_word": "multi_word", "null": "null",
}
for label, (a, b) in cases.items():
    want = expected_map[label]
    got = detect_edit_type(normalize_rasm(a), normalize_rasm(b))
    assert got == want, (
        f"detect_edit_type[{label}]({a!r}, {b!r}) expected {want}, got {got}"
    )
print("detect_edit_type: OK (7 cases incl. prefix-waw deletion F-ULT2-R1n1)")

# -- F-ULT2-R3a :: Greek normaliser keeps Greek characters ----------------
GREEK_SAMPLE = "Ἀνδρὸς μοι ἔννεπε, Μοῦσα"
gn = normalize_greek_strict(GREEK_SAMPLE)
assert gn, f"Greek normaliser stripped everything: {GREEK_SAMPLE!r} -> {gn!r}"
assert len(letters_only_greek(GREEK_SAMPLE)) > 10, \
    f"letters_only_greek too aggressive: {letters_only_greek(GREEK_SAMPLE)!r}"
print(f"normalize_greek_strict: OK  ({GREEK_SAMPLE!r} -> {gn!r})")

# Canonical-path-length Greek smoke
fake_greek = [["Μῆνιν ἄειδε"], ["θεὰ Πηληϊάδεω"], ["Ἀχιλῆος οὐλομένην"]]
gp = canonical_path_length_bigram_greek(fake_greek)
assert gp > 0, "canonical_path_length_bigram_greek returned 0 on real Greek"
print("canonical_path_length_bigram_greek (tiny fake):", round(gp, 3))

# Sanity: Arabic normaliser should strip every Greek character.
from experiments._ultimate2_helpers import letters_only_strict
assert letters_only_strict(GREEK_SAMPLE) == "", \
    "letters_only_strict should be empty on Greek (reason R3 needed the Greek fix)"

# -- F-ULT2-M1 :: rate calibration helpers --------------------------------
# auc_to_rate: 0.5 -> 0 ; 1.0 -> 1 ; 0.4 -> 0 ; 0.75 -> 0.5
assert auc_to_rate(0.5)  == 0.0
assert auc_to_rate(1.0)  == 1.0
assert auc_to_rate(0.4)  == 0.0
assert abs(auc_to_rate(0.75) - 0.5) < 1e-9
assert auc_to_rate(None) == 0.0
# calibrate_rate_above_null: r=base -> 0 ; r=1 -> 1 ; r=base/2 -> 0
assert calibrate_rate_above_null(0.05, 0.05) == 0.0
assert calibrate_rate_above_null(1.0,  0.05) == 1.0
assert calibrate_rate_above_null(0.025, 0.05) == 0.0
assert abs(calibrate_rate_above_null(0.525, 0.05) - (0.525 - 0.05) / 0.95) < 1e-9
# signal_from_log_ratio_ci: lo<=0 -> 0 ; lo=+inf -> 1
assert signal_from_log_ratio_ci(None)  == 0.0
assert signal_from_log_ratio_ci(0.0)   == 0.0
assert signal_from_log_ratio_ci(-0.5)  == 0.0
assert signal_from_log_ratio_ci(100.0) == 1.0
# p-value -> rate
assert _pvalue_to_rate(0.05) == 0.0
assert _pvalue_to_rate(0.0)  == 1.0
assert abs(_pvalue_to_rate(0.025) - 0.5) < 1e-9
print("rate calibration (auc_to_rate, calibrate_rate_above_null, signal_from_log_ratio_ci, _pvalue_to_rate): OK")

# -- F-ULT2-MASTER-R3 :: channel split is disjoint + covers expected -----
ed = set(_EDIT_DETECTION_CHANNELS)
ca = set(_CORPUS_AUTHENTICITY_CHANNELS)
assert ed.isdisjoint(ca), "edit-detection and corpus-authenticity overlap"
assert set(_EXPECTED_CHANNELS) == ed | ca, \
    "_EXPECTED_CHANNELS is not the union of the two groups"
print(f"MASTER channel split: OK  (edit={len(ed)}  auth={len(ca)})")

# -- F-ULT2-M1 regression :: MASTER with all-null inputs -> P_detect=0 ----
# Synthetic "no signal" all_results. Every edit-detection channel is at its
# null baseline; corpus-authenticity channels similarly. A null MASTER must
# NOT saturate P_detect_upper as it did pre-round-2.
class _StubR11:
    pass
null_all_results = {
    "R1":  {"headline_single_letter_rate": R1_NULL_BASELINE_3OF9},   # exactly null
    "R2":  {"log_amp_ci95": [0.0, 0.0]},                                # CI touching zero
    "R3":  {"per_scripture": {"quran": {"p_one_sided": 0.5}}},          # uninformative p
    "R4":  {"AUC_canon_vs_swap": 0.5},                                  # random AUC
    "R5":  {"per_strategy": {"g": {"fraction_below_real": 0.5}}},       # forger-null
    "R6":  {"modularity_per_corpus": {"quran": 0.1, "c1": 0.5, "c2": 0.9}},  # worse than controls
    "R7":  {"log_ratios_quran_over": {}},                               # no signal
    "R8":  {"per_corpus_ladder": {"quran": {"N0": {"sig_rate": 0.05}}}},# baseline
    "R9":  {"VIS_log": 0.0},                                            # no signal
    "R10": {"per_corpus": {"quran": {"sig_rate": 0.05, "sig_rate_calibrated": 0.0}}},
    "R11": {"features_available": False, "AUC_quran_vs_ctrl": None},   # skipped
}
master = run_MASTER(null_all_results, fast=True)
P_upper = master["TDL"]["P_detect_upper"]
ss      = master["TDL"]["structural_signature_score"]
assert P_upper < 0.01, (
    f"F-ULT2-M1 regression: null MASTER should have P_detect_upper ~ 0, got {P_upper}"
)
assert ss < 0.05, (
    f"F-ULT2-M1 regression: null structural_signature should be ~ 0, got {ss}"
)
print(f"null MASTER: P_upper={P_upper:.4f}  structural={ss:.4f}  (both ~ 0): OK")

print("\nSMOKE OK")
