"""
exp46_emphatic_substitution/run.py
==================================
Emphatic-class substitution audit — semantic-aware forgery detection.

Motivation
    The most plausible historical scribal errors in Arabic manuscripts
    are substitutions between phonetically similar consonants, especially
    the **emphatic classes**:

        E1  ص ↔ س   (Sad / Sin)            — emphatic / plain sibilant
        E2  ض ↔ د   (Dad / Dal)            — emphatic / plain voiced stop
        E3  ط ↔ ت   (Tta / Ta)             — emphatic / plain voiceless stop
        E4  ظ ↔ ذ   (Dha / Dhal)           — emphatic / plain interdental
        E5  ق ↔ ك   (Qaf / Kaf)            — uvular / velar stop
        E6  ح ↔ ه   (Hha / Ha)             — pharyngeal / glottal
        E7  ع ↔ ء   (Ayn / Hamza)          — voiced / voiceless pharyngeal
        (E7 is tested on normalised text where ء→ا, so mapped as ع↔ا)

    These are harder to detect than random substitutions because:
      a) The phonetic similarity means many linguistic features (word
         length, syllable count, wazn shape) are preserved.
      b) Emphatic pairs share articulatory features, so bigram statistics
         shift minimally compared to cross-class swaps.

    This experiment enumerates ALL emphatic-class substitutions across
    ALL surahs (or a sample in fast mode) and measures detection using
    the 9-channel forensic detector from R1 (exp09).

Protocol
    For every surah, for every emphatic letter at position p in the
    rasm-normalised surah text, replace it with its class partner:

        canonical verse  →  emphatic-swapped verse

    Then score the swapped surah through the 9-channel detector,
    compute z-scores against the per-edit-type null distribution
    (swap null), and report:
      • per-class detection rate (fraction with ≥ 3 of 9 channels |z|>2)
      • per-surah detection rate
      • overall detection rate
      • comparison with the random-swap baseline from R1

    A LOWER emphatic detection rate vs the R1 random-swap rate would
    confirm that emphatic substitutions are genuinely harder to detect,
    quantifying the "semantic-aware forgery" gap.

Reads (integrity-checked)
    phase_06_phi_m.pkl   →  corpus data
    R1 null distributions (built inline from the same control training)

Writes ONLY under results/experiments/exp46_emphatic_substitution/

Runtime estimate  ~30 min full (all 114 surahs);  ~2 min fast (20 surahs).
"""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from experiments._ultimate2_helpers import (  # noqa: E402
    ARABIC_CONSONANTS,
    CharNGramLM,
    normalize_rasm,
    normalize_rasm_hamza_preserving,
    random_single_letter_swap,
    letters_only,
    words,
    load_corpora,
    extract_verses,
)
from experiments.exp09_R1_variant_forensics_9ch.run import (  # noqa: E402
    nine_channel_features,
    CHANNELS_ALL,
    _triliteral_root,
)

EXP = "exp46_emphatic_substitution"
SEED = 42

# --------------------------------------------------------------------------- #
# Emphatic phonetic classes                                                     #
# --------------------------------------------------------------------------- #
EMPHATIC_CLASSES: dict[str, tuple[str, str]] = {
    "E1_sad_sin":     ("ص", "س"),
    "E2_dad_dal":     ("ض", "د"),
    "E3_tta_ta":      ("ط", "ت"),
    "E4_dha_dhal":    ("ظ", "ذ"),
    "E5_qaf_kaf":     ("ق", "ك"),
    "E6_hha_ha":      ("ح", "ه"),
    "E7_ayn_alef":    ("ع", "ا"),   # ع ↔ hamza (→ alef after normalisation)
}

# AUDIT 2026-04-24 (CRITICAL): E7 is a KNOWN CONFOUNDED CLASS.
# After ``normalize_rasm()`` folds أ إ آ ٱ → ا, the E7 class targets
# EVERY alef position, not just hamza-bearing onsets. Because bare alef ا
# is one of the most common Arabic letters, E7 dominates the edit
# denominator (~48 % of all emphatic edits in exp46 Quran run). Removing
# E7 drops the Quran rate from 1.15 % to 0.30 % and flips the cross-corpus
# H2 verdict (see docs/_SCAN_2026-04-24/AUDIT_MEMO_2026-04-24.md).
# The constant below is used by the result aggregator to emit BOTH the
# full-mode rate AND a sensitivity rate that excludes E7, so any future
# claim can cite both and the reader can choose.
E7_CONFOUNDED_CLASSES = {"E7_ayn_alef"}

# Build a quick lookup: letter → (class_name, partner)
_EMPHATIC_MAP: dict[str, tuple[str, str]] = {}
for _cls, (_a, _b) in EMPHATIC_CLASSES.items():
    _EMPHATIC_MAP[_a] = (_cls, _b)
    _EMPHATIC_MAP[_b] = (_cls, _a)


def _emphatic_positions(text: str) -> list[tuple[int, str, str, str]]:
    """Return list of (abs_pos, original, partner, class_name) for every
    emphatic consonant in ``text``."""
    hits = []
    for i, ch in enumerate(text):
        if ch in _EMPHATIC_MAP:
            cls, partner = _EMPHATIC_MAP[ch]
            hits.append((i, ch, partner, cls))
    return hits


# --------------------------------------------------------------------------- #
# Build R1-compatible reference stats (control-only)                            #
# --------------------------------------------------------------------------- #
def _build_control_references(
    ctrl_corpora: dict[str, list],
) -> tuple[Counter, CharNGramLM]:
    """Train root-bigram counts and root-trigram LM on control corpora."""
    ref_bi = Counter()
    root_texts: list[str] = []
    for name, units in ctrl_corpora.items():
        for u in units:
            vs = extract_verses(u)
            full = " ".join(vs)
            wlist = words(full)
            roots = [_triliteral_root(w) for w in wlist]
            for a, b in zip(roots[:-1], roots[1:]):
                ref_bi[(a, b)] += 1
            root_texts.append(" ".join(roots))

    root_lm = CharNGramLM(n=3, delta=0.5)
    root_lm.fit(root_texts)
    return ref_bi, root_lm


# --------------------------------------------------------------------------- #
# Build null distributions (swap-type, per-channel)                             #
# --------------------------------------------------------------------------- #
def _build_null_distributions(
    quran_units: list,
    ref_bi: Counter,
    root_lm: CharNGramLM,
    rng: random.Random,
    n_surahs: int = 20,
    n_null_per_surah: int = 10,
) -> dict[str, list[float]]:
    """Build swap-type null distributions for each of the 9 channels.
    Returns {channel_name: [delta_values]}."""
    null_deltas: dict[str, list[float]] = {ch: [] for ch in CHANNELS_ALL}
    sample = rng.sample(quran_units, min(n_surahs, len(quran_units)))

    for u in sample:
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        norm_vs = [normalize_rasm(v) for v in vs]
        canon_text = " ".join(norm_vs)
        canon_feats = nine_channel_features(
            norm_vs, ref_bi, root_lm, canonical_text=canon_text)

        for _ in range(n_null_per_surah):
            # Random swap in a random verse (same edit type as emphatic)
            vi = rng.randrange(len(norm_vs))
            new_v, _, orig_l, new_l = random_single_letter_swap(norm_vs[vi], rng)
            if not orig_l:
                continue
            new_vs = list(norm_vs)
            new_vs[vi] = new_v
            new_feats = nine_channel_features(
                new_vs, ref_bi, root_lm, canonical_text=canon_text)
            for ch in CHANNELS_ALL:
                null_deltas[ch].append(new_feats[ch] - canon_feats[ch])

    return null_deltas


def _zscore(null_vals: list[float], v: float) -> float:
    if not null_vals:
        return 0.0
    arr = np.array(null_vals)
    mu = arr.mean()
    sd = arr.std(ddof=1)
    if sd < 1e-15:
        return 0.0
    return float((v - mu) / sd)


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main(fast: bool = False) -> int:
    # Ensure console can print Arabic characters on Windows.
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    rng = random.Random(SEED)

    # Load corpora
    corpora = load_corpora()
    quran_units = corpora["quran"]
    ctrl_names = ["poetry_abbasi", "poetry_jahili", "ksucca",
                  "arabic_bible", "hindawi"]
    ctrl_corpora = {n: corpora[n] for n in ctrl_names if n in corpora}

    print(f"[{EXP}] building control references...")
    ref_bi, root_lm = _build_control_references(ctrl_corpora)
    print(f"[{EXP}] ref_bi entries: {len(ref_bi)}  "
          f"root_lm vocab: {len(root_lm.vocab)}")

    # Build null distributions
    n_null_surahs = 15 if fast else 40
    n_null_per = 8 if fast else 20
    print(f"[{EXP}] building null distributions "
          f"({n_null_surahs} surahs × {n_null_per} swaps)...")
    null_deltas = _build_null_distributions(
        quran_units, ref_bi, root_lm, rng,
        n_surahs=n_null_surahs, n_null_per_surah=n_null_per)
    null_sizes = {ch: len(v) for ch, v in null_deltas.items()}
    print(f"[{EXP}] null sizes: {null_sizes}")

    # Select surahs to test
    if fast:
        test_units = rng.sample(quran_units, min(20, len(quran_units)))
    else:
        test_units = list(quran_units)

    print(f"[{EXP}] testing {len(test_units)} surahs for emphatic "
          f"substitutions...")

    # --- Enumerate emphatic substitutions ---
    per_class_results: dict[str, dict] = {
        cls: {"n_edits": 0, "n_detected_3of9": 0, "z_scores_all": [],
              "example_variants": []}
        for cls in EMPHATIC_CLASSES
    }
    per_surah_results: list[dict] = []
    total_edits = 0
    total_detected = 0

    # AUDIT 2026-04-24 (B13): capture full per-edit context for detected
    # non-E7 edits so the 16 actually-detected emphatic swaps can be
    # characterised post-hoc.  Does not affect the canonical numerics.
    detected_noe7_contexts: list[dict] = []

    for u_idx, u in enumerate(test_units):
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        norm_vs = [normalize_rasm(v) for v in vs]
        canon_text = " ".join(norm_vs)
        canon_feats = nine_channel_features(
            norm_vs, ref_bi, root_lm, canonical_text=canon_text)

        surah_edits = 0
        surah_detected = 0

        # Collect ALL emphatic positions in this surah, then sample
        all_emp: list[tuple[int, int, str, str, str]] = []
        for vi, verse in enumerate(norm_vs):
            for abs_pos, orig_ch, partner, cls_name in _emphatic_positions(verse):
                all_emp.append((vi, abs_pos, orig_ch, partner, cls_name))

        # Cap per-surah to keep runtime feasible
        max_per_surah = 30 if fast else 100
        if len(all_emp) > max_per_surah:
            all_emp = rng.sample(all_emp, max_per_surah)

        for vi, abs_pos, orig_ch, partner, cls_name in all_emp:
            # Apply emphatic swap on the correct verse
            verse = norm_vs[vi]
            new_verse = verse[:abs_pos] + partner + verse[abs_pos + 1:]
            new_vs = list(norm_vs)
            new_vs[vi] = new_verse
            new_feats = nine_channel_features(
                new_vs, ref_bi, root_lm, canonical_text=canon_text)

            # Z-scores against null
            deltas = {ch: new_feats[ch] - canon_feats[ch]
                      for ch in CHANNELS_ALL}
            zscores = {ch: _zscore(null_deltas[ch], d)
                       for ch, d in deltas.items()}
            n_fired = sum(1 for z in zscores.values() if abs(z) > 2.0)
            detected = n_fired >= 3

            per_class_results[cls_name]["n_edits"] += 1
            per_class_results[cls_name]["n_detected_3of9"] += int(detected)
            per_class_results[cls_name]["z_scores_all"].append(
                max(abs(z) for z in zscores.values()))

            # Store a few examples
            if len(per_class_results[cls_name]["example_variants"]) < 5:
                per_class_results[cls_name]["example_variants"].append({
                    "surah_label": getattr(u, "label", f"unit_{u_idx}"),
                    "verse_idx": vi,
                    "pos": abs_pos,
                    "orig": orig_ch,
                    "partner": partner,
                    "n_channels_fired": n_fired,
                    "detected": detected,
                    "z_scores": {k: round(v, 3) for k, v in zscores.items()},
                })

            # AUDIT 2026-04-24 (B13): record contexts of detected non-E7 edits.
            if detected and cls_name not in E7_CONFOUNDED_CLASSES:
                detected_noe7_contexts.append({
                    "class": cls_name,
                    "pair": f"{orig_ch}↔{partner}",
                    "surah": getattr(u, "label", f"unit_{u_idx}"),
                    "verse_idx": vi,
                    "pos": abs_pos,
                    "orig": orig_ch,
                    "partner": partner,
                    "context_left_4":  verse[max(0, abs_pos - 4): abs_pos],
                    "context_right_4": verse[abs_pos + 1: abs_pos + 5],
                    "n_channels_fired": n_fired,
                    "z_scores": {k: round(v, 3) for k, v in zscores.items()},
                })

            total_edits += 1
            surah_edits += 1
            if detected:
                total_detected += 1
                surah_detected += 1

        if surah_edits > 0:
            per_surah_results.append({
                "label": getattr(u, "label", f"unit_{u_idx}"),
                "n_emphatic_edits": surah_edits,
                "n_detected": surah_detected,
                "detection_rate": round(surah_detected / surah_edits, 4),
            })

        if (u_idx + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(f"  [{u_idx+1:>3d}/{len(test_units)}]  "
                  f"{total_edits} edits so far, "
                  f"{total_detected} detected ({elapsed:.0f}s)")

    elapsed_total = time.time() - t0

    # --- AUDIT 2026-04-24 (B14): 3-way E7 sub-class breakdown ---
    # Under normalize_rasm_hamza_preserving, all 4 alef variants (ا أ إ آ) are
    # kept distinct, so the exp46 E7 confound (ع ↔ all-alef) can be split into
    # phonologically-separable edit types.  Nulls and refs are rebuilt under
    # this normalizer so z-scores are calibrated on matching alphabet.
    b14_start = time.time()
    print(f"[{EXP}] B14: building hamza-preserving refs + nulls...")

    def _norm_hp(v: str) -> str:
        return normalize_rasm_hamza_preserving(v)

    # ref_bi and root_lm under the hamza-preserving normaliser
    hp_ref_bi: Counter = Counter()
    hp_root_texts: list[str] = []
    for name, units in ctrl_corpora.items():
        for u in units:
            vs = extract_verses(u)
            full = " ".join(vs)
            hp_full = _norm_hp(full)
            wlist = hp_full.split()
            roots = [_triliteral_root(w) for w in wlist]
            for a, b in zip(roots[:-1], roots[1:]):
                hp_ref_bi[(a, b)] += 1
            hp_root_texts.append(" ".join(roots))
    hp_root_lm = CharNGramLM(n=3, delta=0.5)
    hp_root_lm.fit(hp_root_texts)

    # hamza-preserving null distributions (smaller budget — sub-experiment)
    hp_null_surahs = 10 if fast else 30
    hp_null_per = 6 if fast else 15
    hp_null_deltas: dict[str, list[float]] = {ch: [] for ch in CHANNELS_ALL}
    hp_rng = random.Random(SEED + 1)
    hp_null_sample = hp_rng.sample(quran_units, min(hp_null_surahs, len(quran_units)))
    for u in hp_null_sample:
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        hp_vs = [_norm_hp(v) for v in vs]
        canon_text = " ".join(hp_vs)
        canon_feats = nine_channel_features(
            hp_vs, hp_ref_bi, hp_root_lm, canonical_text=canon_text)
        for _ in range(hp_null_per):
            vi = hp_rng.randrange(len(hp_vs))
            new_v, _, orig_l, _ = random_single_letter_swap(hp_vs[vi], hp_rng)
            if not orig_l:
                continue
            new_vs = list(hp_vs)
            new_vs[vi] = new_v
            new_feats = nine_channel_features(
                new_vs, hp_ref_bi, hp_root_lm, canonical_text=canon_text)
            for ch in CHANNELS_ALL:
                hp_null_deltas[ch].append(new_feats[ch] - canon_feats[ch])

    # 3-way E7 sub-classes (each tests ع -> {ا, أ, آ} in turn at each ع)
    B14_SUBCLASSES = {
        "E7a_ayn_bare_alef":  {"pair": "ع↔ا",    "partner": "ا"},
        "E7b_ayn_hamza_alef": {"pair": "ع↔أ",    "partner": "أ"},
        "E7c_ayn_madda":      {"pair": "ع↔آ",    "partner": "آ"},
    }
    b14_results: dict[str, dict] = {
        cls: {"n_edits": 0, "n_detected_3of9": 0, "z_scores_all": []}
        for cls in B14_SUBCLASSES
    }

    print(f"[{EXP}] B14: testing {len(test_units)} surahs with 3-way E7 split...")
    for u_idx, u in enumerate(test_units):
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        hp_vs = [_norm_hp(v) for v in vs]
        canon_text = " ".join(hp_vs)
        canon_feats = nine_channel_features(
            hp_vs, hp_ref_bi, hp_root_lm, canonical_text=canon_text)
        # ayn positions
        ayn_positions = []
        for vi, verse in enumerate(hp_vs):
            for abs_pos, ch in enumerate(verse):
                if ch == "ع":
                    ayn_positions.append((vi, abs_pos))
        # cap per-surah (B14 samples 3 edits per ayn, so budget is 3x)
        max_ayn = 10 if fast else 40
        if len(ayn_positions) > max_ayn:
            ayn_positions = hp_rng.sample(ayn_positions, max_ayn)

        for vi, abs_pos in ayn_positions:
            verse = hp_vs[vi]
            for cls_name, meta in B14_SUBCLASSES.items():
                partner = meta["partner"]
                new_verse = verse[:abs_pos] + partner + verse[abs_pos + 1:]
                new_vs = list(hp_vs)
                new_vs[vi] = new_verse
                new_feats = nine_channel_features(
                    new_vs, hp_ref_bi, hp_root_lm, canonical_text=canon_text)
                deltas = {c: new_feats[c] - canon_feats[c] for c in CHANNELS_ALL}
                zscores = {c: _zscore(hp_null_deltas[c], d) for c, d in deltas.items()}
                n_fired = sum(1 for z in zscores.values() if abs(z) > 2.0)
                detected = n_fired >= 3
                b14_results[cls_name]["n_edits"] += 1
                b14_results[cls_name]["n_detected_3of9"] += int(detected)
                b14_results[cls_name]["z_scores_all"].append(
                    max(abs(z) for z in zscores.values()))

    b14_elapsed = time.time() - b14_start
    print(f"[{EXP}] B14: sub-experiment complete in {b14_elapsed:.1f}s")

    b14_summary: dict[str, dict] = {}
    for cls, data in b14_results.items():
        n = data["n_edits"]
        det = data["n_detected_3of9"]
        zall = data["z_scores_all"]
        b14_summary[cls] = {
            "pair": B14_SUBCLASSES[cls]["pair"],
            "n_edits": n,
            "n_detected_3of9": det,
            "detection_rate": round(det / n, 6) if n else 0.0,
            "max_z_mean": round(float(np.mean(zall)), 3) if zall else 0.0,
        }

    # --- Aggregate per-class stats ---
    class_summary: dict[str, dict] = {}
    for cls, data in per_class_results.items():
        n = data["n_edits"]
        det = data["n_detected_3of9"]
        zall = data["z_scores_all"]
        a, b = EMPHATIC_CLASSES[cls]
        class_summary[cls] = {
            "pair": f"{a} ↔ {b}",
            "n_edits": n,
            "n_detected_3of9": det,
            "detection_rate": round(det / n, 4) if n else 0.0,
            "max_z_mean": round(float(np.mean(zall)), 3) if zall else 0.0,
            "max_z_median": round(float(np.median(zall)), 3) if zall else 0.0,
            "max_z_p95": round(float(np.percentile(zall, 95)), 3) if zall else 0.0,
            "example_variants": data["example_variants"],
        }

    overall_rate = total_detected / total_edits if total_edits else 0.0

    # --- AUDIT 2026-04-24: E7-excluded sensitivity rate ---
    # E7_ayn_alef is a normalisation-confounded class (see block comment at
    # EMPHATIC_CLASSES above). Emit a second rate that excludes E7 so the
    # phonologically-valid emphatic blindness claim can be cited directly.
    sens_edits = 0
    sens_detected = 0
    for cls, data in per_class_results.items():
        if cls in E7_CONFOUNDED_CLASSES:
            continue
        sens_edits += data["n_edits"]
        sens_detected += data["n_detected_3of9"]
    overall_rate_no_e7 = sens_detected / sens_edits if sens_edits else 0.0

    # --- Surah-level stats ---
    surah_rates = [s["detection_rate"] for s in per_surah_results]
    surah_stats = {
        "n_surahs_tested": len(per_surah_results),
        "mean_detection_rate": round(float(np.mean(surah_rates)), 4) if surah_rates else 0.0,
        "median_detection_rate": round(float(np.median(surah_rates)), 4) if surah_rates else 0.0,
        "min_detection_rate": round(float(min(surah_rates)), 4) if surah_rates else 0.0,
        "max_detection_rate": round(float(max(surah_rates)), 4) if surah_rates else 0.0,
    }

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "fast_mode": fast,
        "seed": SEED,
        "emphatic_classes": {k: list(v) for k, v in EMPHATIC_CLASSES.items()},
        "n_surahs_tested": len(per_surah_results),
        "total_emphatic_edits": total_edits,
        "total_detected_3of9": total_detected,
        "overall_detection_rate": round(overall_rate, 6),
        "overall_detection_rate_without_E7": round(overall_rate_no_e7, 6),
        "audit_2026_04_24_e7_confound": {
            "class_excluded": sorted(E7_CONFOUNDED_CLASSES),
            "excluded_edits": total_edits - sens_edits,
            "excluded_detected": total_detected - sens_detected,
            "remaining_edits": sens_edits,
            "remaining_detected": sens_detected,
            "note": (
                "E7_ayn_alef is a known normalisation-confounded class: "
                "normalize_rasm() folds أ إ آ ٱ → ا, so E7 tests ع ↔ all-alef "
                "positions rather than ع ↔ hamza. Cite "
                "overall_detection_rate_without_E7 for the phonologically-"
                "valid claim. See docs/_SCAN_2026-04-24/AUDIT_MEMO_2026-04-24.md."
            ),
        },
        "audit_2026_04_24_b13_noe7_contexts": {
            "note": (
                "Full per-edit context (±4-char window, firing channels, full "
                "9-channel z-scores) for every detected non-E7 emphatic swap. "
                "Diagnostic-only — not used by any published summary statistic."
            ),
            "n_detected_total": len(detected_noe7_contexts),
            "edits": detected_noe7_contexts,
        },
        "audit_2026_04_24_b14_e7_breakdown": {
            "note": (
                "3-way E7 sub-class breakdown under normalize_rasm_hamza_"
                "preserving (keeps ا أ إ آ distinct at the TEXT level). "
                "Tests ع against each alef variant separately at every ayn "
                "position. Null distributions and root-bigram refs are "
                "rebuilt under the hamza-preserving normaliser. "
                "EMPIRICAL FINDING (2026-04-24 fast smoke + full): the "
                "three sub-classes produce BYTE-IDENTICAL detection "
                "rates / max_z_mean, differing only in the 'pair' label. "
                "Root cause: every one of the 9 channels internally re-"
                "normalises via normalize_rasm() or letters_only() before "
                "computing features (see "
                "experiments/exp09_R1_variant_forensics_9ch/run.py:151,188,"
                "228,252 and :333). The hamza-preserving alphabet is thus "
                "collapsed inside the feature extractor, making the 9-"
                "channel detector ARCHITECTURALLY BLIND to hamza status. "
                "A genuinely hamza-sensitive detector would require "
                "re-architecting all 9 channels with a hamza-preserving "
                "alphabet — out of scope for this audit. Conclusion: the "
                "E7 confound cannot be cleanly split by swapping "
                "normalisers; the reported overall_detection_rate_without_"
                "E7 remains the correct audit-level sensitivity figure."
            ),
            "normalizer": "normalize_rasm_hamza_preserving",
            "null_sample_size": sum(len(v) for v in hp_null_deltas.values()) // len(CHANNELS_ALL),
            "runtime_seconds": round(b14_elapsed, 2),
            "subclasses": b14_summary,
            "architectural_blindness_confirmed": True,
        },
        "per_class_summary": class_summary,
        "per_surah_results": per_surah_results,
        "surah_level_stats": surah_stats,
        "null_distribution_sizes": null_sizes,
        "comparison_vs_R1": {
            "note": (
                "R1 tested RANDOM single-letter swaps with headline rate "
                "measured over canonical variants. Emphatic swaps are the "
                "hardest class of single-letter edits because phonetic "
                "similarity preserves linguistic features. A LOWER "
                "emphatic detection rate vs R1's headline rate quantifies "
                "the 'semantic-aware forgery gap'. If the emphatic rate "
                "is still high (≥ 0.50), the framework is robust even "
                "against the most plausible scribal errors."
            ),
        },
        "runtime_seconds": round(elapsed_total, 2),
        "verdict": (
            f"Emphatic-class detection: {total_detected}/{total_edits} "
            f"({overall_rate:.1%}).  Per-class breakdown available in "
            f"per_class_summary."
        ),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console ---
    print(f"\n[{EXP}] DONE in {elapsed_total:.1f}s")
    print(f"[{EXP}] Total emphatic edits: {total_edits}")
    print(f"[{EXP}] Overall detection rate (>=3/9 channels): "
          f"{total_detected}/{total_edits} = {overall_rate:.1%}")
    print(f"[{EXP}] AUDIT sensitivity rate (E7 excluded): "
          f"{sens_detected}/{sens_edits} = {overall_rate_no_e7:.3%} "
          f"— see docs/_SCAN_2026-04-24/AUDIT_MEMO_2026-04-24.md")
    print(f"[{EXP}] PER-CLASS RATES:")
    for cls, data in class_summary.items():
        print(f"   {cls:<18s} {data['pair']:<7s}  "
              f"n={data['n_edits']:>5d}  "
              f"det={data['detection_rate']:.1%}  "
              f"max|z|_mean={data['max_z_mean']:.2f}")
    print(f"[{EXP}] SURAH-LEVEL: "
          f"mean={surah_stats['mean_detection_rate']:.1%}  "
          f"median={surah_stats['median_detection_rate']:.1%}  "
          f"range=[{surah_stats['min_detection_rate']:.1%}, "
          f"{surah_stats['max_detection_rate']:.1%}]")

    # AUDIT 2026-04-24 (B13 + B14): dual console footer
    print(f"[{EXP}] B13: {len(detected_noe7_contexts)} detected non-E7 "
          f"edits captured with ±4-char context (see "
          f"audit_2026_04_24_b13_noe7_contexts in JSON)")
    print(f"[{EXP}] B14 3-WAY E7 BREAKDOWN (hamza-preserving):")
    for cls, data in b14_summary.items():
        print(f"   {cls:<22s} {data['pair']:<7s}  "
              f"n={data['n_edits']:>4d}  "
              f"det={data['detection_rate']:.3%}  "
              f"max|z|_mean={data['max_z_mean']:.2f}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    fast = "--fast" in sys.argv
    sys.exit(main(fast=fast))
