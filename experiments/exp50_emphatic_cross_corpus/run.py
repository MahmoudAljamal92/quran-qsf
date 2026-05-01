"""
exp50_emphatic_cross_corpus/run.py
==================================
Cross-corpus emphatic substitution audit.

Motivation
    exp46 reported Quran emphatic-class detection rate = 1.15 %
    (overall, 9-channel >= 3/9 rule, full mode, 114 surahs,
    10 461 edits). That is a STRIKINGLY LOW rate even against the
    most phonetically similar substitutions Arabic can host.

    Two competing explanations:
      H1 STRUCTURAL     : any Arabic corpus scored the same way would
                          also sit near 1 % (emphatic blindness is
                          baked into Arabic phonology / orthography,
                          not a Quran-specific property).
      H2 QURAN-SPECIFIC : Arabic controls score MUCH higher than 1 %
                          when subjected to the same emphatic-swap
                          enumeration (Quran is genuinely harder to
                          forge with phonetically plausible edits).

    This experiment runs the exact exp46 pipeline on two major Arabic
    control corpora (poetry_abbasi, poetry_jahili) and reports their
    rates alongside the Quran baseline. The decision rule below
    discriminates between H1 and H2 on pre-registered thresholds.

Protocol (pre-registered; frozen before any run)
    For each TARGET corpus in TARGETS:
      1. Build control references (ref_bi, root_lm) from the other
         five Arabic corpora (leave-TARGET-out). Matches exp46's
         methodology exactly: Quran's run used 5 controls excluding
         Quran itself; here we leave the test corpus out.
      2. Build swap-type null (random single-letter swap) from the
         target corpus's own units (same sample sizes as exp46).
      3. Enumerate every emphatic-class substitution in every sampled
         unit and score through exp09's 9-channel detector.
      4. Report per-class and overall detection rates
         (>= 3 of 9 channels |z| > 2) and max|z| stats.

Decision rule (pre-registered)
    Let R_Q = Quran's exp46 overall rate (1.15 %).
    Let R_X = the tested Arabic control's overall rate.
      * R_X <= 2.0 %   =>  H1 supported ("structural Arabic blindness").
      * R_X >= 5.0 %   =>  H2 supported (Quran-specific immunity:
                            ctrl detection is >=4.3x higher).
      * 2.0 % < R_X < 5.0 %  =>  INCONCLUSIVE.

Reads (integrity-checked)
    phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp50_emphatic_cross_corpus/

Runtime estimates
    --fast  :  ~6 min  (2 corpora x 20 units)
    default :  ~40 min (2 corpora x 60 units)
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from experiments._ultimate2_helpers import (  # noqa: E402
    CharNGramLM,
    normalize_rasm,
    random_single_letter_swap,
    words,
    load_corpora,
    extract_verses,
)
from experiments.exp09_R1_variant_forensics_9ch.run import (  # noqa: E402
    nine_channel_features,
    CHANNELS_ALL,
    _triliteral_root,
)
from experiments.exp46_emphatic_substitution.run import (  # noqa: E402
    EMPHATIC_CLASSES,
    E7_CONFOUNDED_CLASSES,
    _EMPHATIC_MAP,
    _emphatic_positions,
    _zscore,
)


EXP = "exp50_emphatic_cross_corpus"
SEED = 42

# Pre-registered targets and reference pool (frozen before any run).
TARGETS = ["poetry_abbasi", "poetry_jahili"]
REFERENCE_POOL_FULL = [
    "poetry_abbasi", "poetry_jahili", "poetry_islami",
    "ksucca", "arabic_bible", "hindawi",
]

# Quran baseline from exp46 (full-mode, locked)
QURAN_BASELINE_RATE_EXP46 = 0.011471
QURAN_BASELINE_EDITS_EXP46 = 10461
QURAN_BASELINE_DET_EXP46 = 120

# Pre-registered decision-rule thresholds.
H1_STRUCTURAL_MAX_RATE = 0.020
H2_QURAN_SPECIFIC_MIN_RATE = 0.050


# --------------------------------------------------------------------------- #
# Reference-stats builder (same as exp46 but parameterised by reference set)  #
# --------------------------------------------------------------------------- #
def _build_reference_stats(
    ref_corpora: dict[str, list],
) -> tuple[Counter, CharNGramLM]:
    ref_bi: Counter = Counter()
    root_texts: list[str] = []
    for _name, units in ref_corpora.items():
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
# Null distribution (random single-letter swap within the test corpus)         #
# --------------------------------------------------------------------------- #
def _build_null_distributions(
    test_units: list,
    ref_bi: Counter,
    root_lm: CharNGramLM,
    rng: random.Random,
    n_units: int,
    n_null_per_unit: int,
) -> dict[str, list[float]]:
    null_deltas: dict[str, list[float]] = {ch: [] for ch in CHANNELS_ALL}
    if not test_units:
        return null_deltas
    sample = rng.sample(test_units, min(n_units, len(test_units)))
    for u in sample:
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        norm_vs = [normalize_rasm(v) for v in vs]
        canon_text = " ".join(norm_vs)
        canon_feats = nine_channel_features(
            norm_vs, ref_bi, root_lm, canonical_text=canon_text)
        for _ in range(n_null_per_unit):
            vi = rng.randrange(len(norm_vs))
            new_v, _, orig_l, _ = random_single_letter_swap(norm_vs[vi], rng)
            if not orig_l:
                continue
            new_vs = list(norm_vs)
            new_vs[vi] = new_v
            new_feats = nine_channel_features(
                new_vs, ref_bi, root_lm, canonical_text=canon_text)
            for ch in CHANNELS_ALL:
                null_deltas[ch].append(new_feats[ch] - canon_feats[ch])
    return null_deltas


# --------------------------------------------------------------------------- #
# Score emphatic substitutions in one corpus                                   #
# --------------------------------------------------------------------------- #
def _score_emphatic_on_corpus(
    target_name: str,
    target_units: list,
    ref_bi: Counter,
    root_lm: CharNGramLM,
    null_deltas: dict[str, list[float]],
    rng: random.Random,
    n_test_units: int,
    max_per_unit: int,
) -> dict:
    if not target_units:
        return {
            "n_units_tested": 0,
            "total_edits": 0,
            "total_detected": 0,
            "overall_detection_rate": 0.0,
            "per_class_summary": {},
            "per_unit_results": [],
        }

    if n_test_units and n_test_units < len(target_units):
        test_pool = rng.sample(target_units, n_test_units)
    else:
        test_pool = list(target_units)

    per_class: dict[str, dict] = {
        cls: {"n_edits": 0, "n_detected_3of9": 0, "max_z_all": [],
              "example_variants": []}
        for cls in EMPHATIC_CLASSES
    }
    per_unit: list[dict] = []
    total_edits = 0
    total_detected = 0

    for u_idx, u in enumerate(test_pool):
        vs = extract_verses(u)
        if len(vs) < 2:
            continue
        norm_vs = [normalize_rasm(v) for v in vs]
        canon_text = " ".join(norm_vs)
        canon_feats = nine_channel_features(
            norm_vs, ref_bi, root_lm, canonical_text=canon_text)

        all_positions: list[tuple[int, int, str, str, str]] = []
        for vi, verse in enumerate(norm_vs):
            for abs_pos, orig, partner, cls in _emphatic_positions(verse):
                all_positions.append((vi, abs_pos, orig, partner, cls))

        if len(all_positions) > max_per_unit:
            all_positions = rng.sample(all_positions, max_per_unit)

        u_edits = 0
        u_detected = 0
        for vi, abs_pos, orig, partner, cls in all_positions:
            verse = norm_vs[vi]
            new_verse = verse[:abs_pos] + partner + verse[abs_pos + 1:]
            new_vs = list(norm_vs)
            new_vs[vi] = new_verse
            new_feats = nine_channel_features(
                new_vs, ref_bi, root_lm, canonical_text=canon_text)
            deltas = {ch: new_feats[ch] - canon_feats[ch] for ch in CHANNELS_ALL}
            zscores = {ch: _zscore(null_deltas[ch], d) for ch, d in deltas.items()}
            n_fired = sum(1 for z in zscores.values() if abs(z) > 2.0)
            detected = n_fired >= 3

            per_class[cls]["n_edits"] += 1
            per_class[cls]["n_detected_3of9"] += int(detected)
            per_class[cls]["max_z_all"].append(max(abs(z) for z in zscores.values()))
            if len(per_class[cls]["example_variants"]) < 3:
                per_class[cls]["example_variants"].append({
                    "unit_label": getattr(u, "label", f"{target_name}_unit_{u_idx}"),
                    "verse_idx": vi,
                    "pos": abs_pos,
                    "orig": orig,
                    "partner": partner,
                    "n_channels_fired": n_fired,
                    "detected": detected,
                    "z_scores": {k: round(v, 3) for k, v in zscores.items()},
                })
            total_edits += 1
            u_edits += 1
            if detected:
                total_detected += 1
                u_detected += 1

        if u_edits > 0:
            per_unit.append({
                "unit_label": getattr(u, "label", f"{target_name}_unit_{u_idx}"),
                "n_emphatic_edits": u_edits,
                "n_detected": u_detected,
                "detection_rate": round(u_detected / u_edits, 4),
            })

    # Aggregate per-class
    class_summary: dict[str, dict] = {}
    for cls, data in per_class.items():
        n = data["n_edits"]
        det = data["n_detected_3of9"]
        zall = data["max_z_all"]
        a, b = EMPHATIC_CLASSES[cls]
        class_summary[cls] = {
            "pair": f"{a} <-> {b}",
            "n_edits": n,
            "n_detected_3of9": det,
            "detection_rate": round(det / n, 4) if n else 0.0,
            "max_z_mean": round(float(np.mean(zall)), 3) if zall else 0.0,
            "max_z_median": round(float(np.median(zall)), 3) if zall else 0.0,
            "max_z_p95": round(float(np.percentile(zall, 95)), 3) if zall else 0.0,
            "example_variants": data["example_variants"],
        }

    rate = total_detected / total_edits if total_edits else 0.0

    # AUDIT 2026-04-24: E7-excluded sensitivity rate. See exp46 block comment
    # near EMPHATIC_CLASSES and docs/_SCAN_2026-04-24/AUDIT_MEMO_2026-04-24.md.
    sens_edits = sum(
        d["n_edits"] for cls, d in per_class.items()
        if cls not in E7_CONFOUNDED_CLASSES
    )
    sens_detected = sum(
        d["n_detected_3of9"] for cls, d in per_class.items()
        if cls not in E7_CONFOUNDED_CLASSES
    )
    rate_no_e7 = sens_detected / sens_edits if sens_edits else 0.0

    return {
        "n_units_tested": len([x for x in per_unit if x["n_emphatic_edits"] > 0]),
        "total_edits": total_edits,
        "total_detected": total_detected,
        "overall_detection_rate": round(rate, 6),
        "overall_detection_rate_without_E7": round(rate_no_e7, 6),
        "sensitivity_no_e7": {
            "class_excluded": sorted(E7_CONFOUNDED_CLASSES),
            "edits_excluded": total_edits - sens_edits,
            "detected_excluded": total_detected - sens_detected,
            "remaining_edits": sens_edits,
            "remaining_detected": sens_detected,
        },
        "per_class_summary": class_summary,
        "per_unit_results": per_unit,
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def _verdict_for_rate(rate: float) -> str:
    if rate <= H1_STRUCTURAL_MAX_RATE:
        return "H1_STRUCTURAL_ARABIC_BLINDNESS"
    if rate >= H2_QURAN_SPECIFIC_MIN_RATE:
        return "H2_QURAN_SPECIFIC_IMMUNITY"
    return "INCONCLUSIVE"


def main(fast: bool = False) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    rng = random.Random(SEED)

    # Sample-size budget (matches exp46 conventions)
    n_null_units = 15 if fast else 40
    n_null_per_unit = 8 if fast else 20
    n_test_units = 20 if fast else 60
    max_per_unit = 30 if fast else 100

    corpora = load_corpora()
    available = [c for c in REFERENCE_POOL_FULL if c in corpora]
    if not available:
        raise RuntimeError("No Arabic controls found in phase_06 CORPORA.")
    print(f"[{EXP}] available Arabic controls: {available}")

    per_target: dict[str, dict] = {}
    for target in TARGETS:
        if target not in corpora:
            print(f"[{EXP}] SKIP {target}: not in CORPORA")
            continue
        print(f"\n[{EXP}] === TARGET = {target} ===")
        ref_names = [c for c in available if c != target]
        ref_corpora = {n: corpora[n] for n in ref_names}
        print(f"[{EXP}]   refs (leave-{target}-out): {ref_names}")
        t_ref = time.time()
        ref_bi, root_lm = _build_reference_stats(ref_corpora)
        print(f"[{EXP}]   ref_bi={len(ref_bi)}  root_lm_vocab={len(root_lm.vocab)}"
              f"  ({time.time() - t_ref:.1f}s)")

        target_units = corpora[target]
        print(f"[{EXP}]   target units available: {len(target_units)}")

        t_null = time.time()
        null_deltas = _build_null_distributions(
            target_units, ref_bi, root_lm, rng,
            n_units=n_null_units, n_null_per_unit=n_null_per_unit)
        null_sizes = {ch: len(v) for ch, v in null_deltas.items()}
        print(f"[{EXP}]   null built ({time.time() - t_null:.1f}s) sizes={null_sizes}")

        t_score = time.time()
        corpus_result = _score_emphatic_on_corpus(
            target_name=target,
            target_units=target_units,
            ref_bi=ref_bi,
            root_lm=root_lm,
            null_deltas=null_deltas,
            rng=rng,
            n_test_units=n_test_units,
            max_per_unit=max_per_unit,
        )
        print(f"[{EXP}]   scored in {time.time() - t_score:.1f}s  "
              f"rate={corpus_result['overall_detection_rate']:.3%}  "
              f"n_edits={corpus_result['total_edits']}")

        corpus_result["reference_pool"] = ref_names
        corpus_result["null_distribution_sizes"] = null_sizes
        corpus_result["verdict_vs_prereg"] = _verdict_for_rate(
            corpus_result["overall_detection_rate"])
        corpus_result["verdict_vs_prereg_without_E7"] = _verdict_for_rate(
            corpus_result["overall_detection_rate_without_E7"])
        per_target[target] = corpus_result

    # --- Cross-target summary ---
    overall_rates = {t: d["overall_detection_rate"] for t, d in per_target.items()}
    max_ctrl_rate = max(overall_rates.values()) if overall_rates else 0.0
    aggregate_verdict = _verdict_for_rate(max_ctrl_rate)

    # AUDIT 2026-04-24: parallel aggregates with E7 excluded.
    overall_rates_no_e7 = {
        t: d.get("overall_detection_rate_without_E7", 0.0)
        for t, d in per_target.items()
    }
    max_ctrl_rate_no_e7 = (
        max(overall_rates_no_e7.values()) if overall_rates_no_e7 else 0.0
    )
    aggregate_verdict_no_e7 = _verdict_for_rate(max_ctrl_rate_no_e7)

    if max_ctrl_rate <= QURAN_BASELINE_RATE_EXP46 * 2:
        quran_vs_ctrls = "QURAN_RATE_WITHIN_2X_OF_CTRL_MAX"
    elif QURAN_BASELINE_RATE_EXP46 == 0:
        quran_vs_ctrls = "UNDEFINED"
    else:
        ratio = max_ctrl_rate / QURAN_BASELINE_RATE_EXP46
        quran_vs_ctrls = (
            f"CTRL_MAX_{ratio:.1f}X_HIGHER_THAN_QURAN"
            if ratio >= 1 else
            f"QURAN_{1/ratio:.1f}X_HIGHER_THAN_CTRL_MAX"
        )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "fast_mode": fast,
        "seed": SEED,
        "prereg": {
            "targets": TARGETS,
            "reference_pool_full": REFERENCE_POOL_FULL,
            "reference_builder": "leave-target-out (5 controls per test)",
            "null_builder": "random_single_letter_swap within target corpus",
            "detector": "exp09 9-channel, |z|>2 fire rule, >=3 of 9 detect",
            "h1_structural_max_rate": H1_STRUCTURAL_MAX_RATE,
            "h2_quran_specific_min_rate": H2_QURAN_SPECIFIC_MIN_RATE,
            "inconclusive_band": [H1_STRUCTURAL_MAX_RATE,
                                  H2_QURAN_SPECIFIC_MIN_RATE],
            "quran_baseline_source": "exp46_emphatic_substitution (full mode)",
            "quran_baseline_rate": QURAN_BASELINE_RATE_EXP46,
            "quran_baseline_edits": QURAN_BASELINE_EDITS_EXP46,
            "quran_baseline_detected": QURAN_BASELINE_DET_EXP46,
            "sample_budget": {
                "n_null_units": n_null_units,
                "n_null_per_unit": n_null_per_unit,
                "n_test_units": n_test_units,
                "max_edits_per_unit": max_per_unit,
            },
        },
        "per_target": per_target,
        "overall_rates_by_target": overall_rates,
        "max_control_rate": max_ctrl_rate,
        "quran_vs_controls_summary": quran_vs_ctrls,
        "aggregate_verdict": aggregate_verdict,
        "audit_2026_04_24_e7_confound": {
            "note": (
                "E7_ayn_alef is normalisation-confounded (ع ↔ all-alef "
                "rather than ع ↔ hamza). Fields below replay the verdict "
                "rule on rates that exclude E7. See "
                "docs/_SCAN_2026-04-24/AUDIT_MEMO_2026-04-24.md."
            ),
            "overall_rates_by_target_without_E7": overall_rates_no_e7,
            "max_control_rate_without_E7": max_ctrl_rate_no_e7,
            "aggregate_verdict_without_E7": aggregate_verdict_no_e7,
            "quran_baseline_rate_exp46_context": (
                "Quran exp46 published rate 1.15% drops to ~0.30% once "
                "E7 is excluded (104/120 detections were E7). Interpret "
                "the no-E7 aggregate_verdict against the Quran no-E7 rate "
                "for an apples-to-apples cross-corpus comparison."
            ),
        },
        "interpretation": (
            "H1 (structural Arabic blindness) = the emphatic detection rate "
            "is an artefact of how phonetically similar the emphatic pairs "
            "are, independent of corpus. Controls also score ~1%. "
            "H2 (Quran-specific immunity) = controls score noticeably higher "
            "(>= 5x Quran); the Quran is genuinely harder to forge with "
            "plausible scribal errors. INCONCLUSIVE = controls in the gray "
            "band; additional corpora / full-mode runs required."
        ),
        "runtime_seconds": round(time.time() - t0, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console summary ---
    print(f"\n[{EXP}] DONE in {report['runtime_seconds']:.1f}s")
    print(f"[{EXP}] Quran baseline (exp46): {QURAN_BASELINE_RATE_EXP46:.3%} "
          f"({QURAN_BASELINE_DET_EXP46}/{QURAN_BASELINE_EDITS_EXP46})")
    for target, d in per_target.items():
        print(f"[{EXP}] {target:<16s} rate={d['overall_detection_rate']:.3%}  "
              f"n_edits={d['total_edits']:>5d}  "
              f"verdict={d['verdict_vs_prereg']}")
        print(f"[{EXP}]                  no-E7 rate="
              f"{d['overall_detection_rate_without_E7']:.3%}  "
              f"verdict_no_e7={d['verdict_vs_prereg_without_E7']}")
    print(f"[{EXP}] Max control rate = {max_ctrl_rate:.3%}   "
          f"aggregate = {aggregate_verdict}")
    print(f"[{EXP}] AUDIT no-E7    = {max_ctrl_rate_no_e7:.3%}   "
          f"aggregate_no_e7 = {aggregate_verdict_no_e7}")
    print(f"[{EXP}] Quran-vs-ctrls : {quran_vs_ctrls}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    fast = "--fast" in sys.argv
    sys.exit(main(fast=fast))
