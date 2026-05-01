"""
exp30_cascade_R1_9ch/run.py
===========================
Empirical R1 9-channel detection rate on single-letter INTERNAL
substitutions -- the R1 analogue of exp29.

Motivation
----------
exp29 showed that L1/L2/L3 (Phi_M 5-D at window, surah, corpus level)
are STRUCTURALLY BLIND to internal-letter edits because `features_5d`
is byte-exact invariant under non-initial / non-terminal letters in
non-boundary words. The Ultimate-2 R1 9-channel pipeline includes
three surah-level channels (A_spectral 34x34 letter-transition SVD,
C_bigram_dist letter-bigram L2, E_ncd gzip compression distance) that
DO read internal letters. These were calibrated in exp09 on random
letter swaps at any position; whether they retain non-zero sensitivity
for the exp29 "non-boundary" restriction is untested.

This experiment runs R1's nine_channel_features on exp29-style
internal perturbations (restricted: non-initial, non-terminal letter
in non-boundary word of non-terminal verse) and reports:
  * per-channel |delta_ch| distribution for Quran and ctrl pools
  * p_ctrl_ch = fraction of Quran |delta_ch| above 95th percentile of
    ctrl |delta_ch| (Quran-specificity)
  * composite P = 1 - prod_k (1 - p_ctrl_ch) over 9 channels
  * Adiyat-specific rows: A (ع->غ), B (ض->ص), C (both) with per-channel
    |delta| and nearest-null z-score  -- directly cited in
    docs/ADIYAT_ANALYSIS_AR.md §13 to close the "not directly tested"
    caveat for rows 9, 11, 12 of the table in §6.

Reads (checked): phase_06_phi_m.pkl via experiments._lib.load_phase
                 (via load_corpora in experiments._ultimate2_helpers).
Writes ONLY under results/experiments/exp30_cascade_R1_9ch/.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir, self_check_begin, self_check_end,
)
from experiments._ultimate2_helpers import (  # noqa: E402
    ARABIC_CONSONANTS, extract_verses, load_corpora, normalize_rasm,
)
from experiments.exp09_R1_variant_forensics_9ch.run import (  # noqa: E402
    CHANNELS_ALL, _train_control_references, nine_channel_features,
)

EXP = "exp30_cascade_R1_9ch"
SEED = 42
ALPHA = 0.05
N_PERT_QURAN_PER_SURAH = 10   # 68 * 10 = 680 Quran perturbations
N_PERT_CTRL_PER_UNIT = 5      # 200 * 5 = 1000 ctrl perturbations
CTRL_N_UNITS = 200
BAND_A_LO, BAND_A_HI = 15, 100

ARABIC_CTRL_NAMES = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Adiyat variants (canonical vs three alternatives). These are cited
# directly in docs/ADIYAT_ANALYSIS_AR.md §13.
ADIYAT_VARIANTS: list[dict] = [
    {
        "name": "A_ayn_to_ghayn",
        "surah_index_1based": 100,
        "orig": "\u0648\u0627\u0644\u0639\u0627\u062f\u064a\u0627\u062a",  # والعاديات
        "var":  "\u0648\u0627\u0644\u063a\u0627\u062f\u064a\u0627\u062a",  # والغاديات
        "description": "internal letter substitution ع -> غ in verse 1",
    },
    {
        "name": "B_dad_to_sad",
        "surah_index_1based": 100,
        "orig": "\u0636\u0628\u062d\u0627",  # ضبحا
        "var":  "\u0635\u0628\u062d\u0627",  # صبحا
        "description": "terminal letter substitution ض -> ص in last word of verse 1",
    },
    {
        "name": "C_both",
        "surah_index_1based": 100,
        "orig": None,  # apply both A and B in sequence
        "var":  None,
        "description": "variant A + variant B simultaneously",
    },
]


# --------------------------------------------------------------------------- #
# Internal perturbation (parity with exp29 _apply_perturbation)               #
# --------------------------------------------------------------------------- #
def _apply_internal_perturbation(
    verses: list[str], rng: random.Random,
) -> tuple[list[str], int] | None:
    """Same perturbation design as exp29: non-initial, non-terminal
    letter in a non-boundary word of a non-terminal verse, substituted
    with a different Arabic consonant."""
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONSONANTS)
    for vi in vi_choices:
        toks = normalize_rasm(verses[vi]).split()
        if len(toks) < 3:
            continue
        word_choices = list(range(1, len(toks) - 1))
        rng.shuffle(word_choices)
        for wi in word_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            cand = [c for c in cons if c != original]
            if not cand:
                continue
            repl = rng.choice(cand)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


# --------------------------------------------------------------------------- #
# Per-perturbation delta on all 9 channels                                    #
# --------------------------------------------------------------------------- #
def _channel_deltas(
    canon_verses: list[str], pert_verses: list[str],
    ref_bi, root_lm, canon_feats: dict[str, float] | None = None,
) -> dict[str, float]:
    """|delta_ch| for each of the 9 R1 channels.

    canon_feats may be pre-computed once per surah to save compute;
    if None we compute it here.
    """
    canon_text = " ".join(canon_verses)
    if canon_feats is None:
        canon_feats = nine_channel_features(
            canon_verses, ref_bi, root_lm, canonical_text=canon_text,
        )
    pert_feats = nine_channel_features(
        pert_verses, ref_bi, root_lm, canonical_text=canon_text,
    )
    return {
        ch: abs(pert_feats[ch] - canon_feats[ch]) for ch in CHANNELS_ALL
    }


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(extract_verses(u)) <= BAND_A_HI]


# --------------------------------------------------------------------------- #
# Adiyat special-case injection (post-normalisation, parity with exp09)       #
# --------------------------------------------------------------------------- #
def _inject_adiyat_variant(
    verses_norm: list[str], variant: dict,
) -> list[str] | None:
    """Inject a pre-specified orig->var substitution. For variant C
    (both) we inject A then B sequentially."""
    name = variant["name"]
    if name == "C_both":
        first = _inject_adiyat_variant(verses_norm, ADIYAT_VARIANTS[0])
        if first is None:
            return None
        return _inject_adiyat_variant(first, ADIYAT_VARIANTS[1])
    orig = normalize_rasm(variant["orig"])
    var = normalize_rasm(variant["var"])
    out: list[str] = []
    found = False
    for v in verses_norm:
        if not found and orig and orig in v:
            out.append(v.replace(orig, var, 1))
            found = True
        else:
            out.append(v)
    return out if found else None


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> dict:
    t0 = time.time()
    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading corpora + training control references...")
    corpora = load_corpora()

    # Build R1 control-trained references (same protocol as exp09).
    # This builds ref_bi (root-bigram counter) and root_lm (CharNGramLM)
    # from non-Quran Arabic corpora only. CamelTools NOT required --
    # _triliteral_root is the crude in-file heuristic.
    ref_bi, root_lm, control_names = _train_control_references(corpora)
    print(f"[{EXP}] R1 control training corpora: {control_names}")

    q_units = [u for u in corpora.get("quran", [])
               if BAND_A_LO <= len(extract_verses(u)) <= BAND_A_HI]
    if len(q_units) < 5:
        raise RuntimeError("Too few Band-A Quran surahs")
    print(f"[{EXP}] Quran Band-A units: {len(q_units)}  "
          f"N_PERT_QURAN_PER_SURAH={N_PERT_QURAN_PER_SURAH}")

    ctrl_units_all = []
    for name in ARABIC_CTRL_NAMES:
        ctrl_units_all.extend(
            [u for u in corpora.get(name, [])
             if BAND_A_LO <= len(extract_verses(u)) <= BAND_A_HI]
        )
    rng_sample = random.Random(SEED + 4)
    rng_sample.shuffle(ctrl_units_all)
    ctrl_units = ctrl_units_all[:CTRL_N_UNITS]
    print(f"[{EXP}] sampled ctrl pool: {len(ctrl_units)} units  "
          f"N_PERT_CTRL_PER_UNIT={N_PERT_CTRL_PER_UNIT}")

    # ---- Run Quran perturbations -------------------------------------------
    rng_q = random.Random(SEED + 1)
    quran_deltas: list[dict] = []
    q_canon_feats_cache: dict[str, dict[str, float]] = {}
    for u in q_units:
        verses_raw = extract_verses(u)
        verses_norm = [normalize_rasm(v) for v in verses_raw]
        canon_text = " ".join(verses_norm)
        try:
            canon_feats = nine_channel_features(
                verses_norm, ref_bi, root_lm, canonical_text=canon_text,
            )
        except Exception:
            continue
        label = getattr(u, "label", None) or str(id(u))
        q_canon_feats_cache[label] = canon_feats
        for _ in range(N_PERT_QURAN_PER_SURAH):
            pair = _apply_internal_perturbation(verses_norm, rng_q)
            if pair is None:
                continue
            pv, vi = pair
            try:
                deltas = _channel_deltas(
                    verses_norm, pv, ref_bi, root_lm, canon_feats,
                )
            except Exception:
                continue
            deltas_rec = {
                "pool": "quran", "unit": label, "vi": vi, **deltas,
            }
            quran_deltas.append(deltas_rec)

    print(f"[{EXP}] Quran perturbations complete: {len(quran_deltas)} "
          f"({time.time() - t0:.0f}s)")

    # ---- Run ctrl perturbations --------------------------------------------
    rng_c = random.Random(SEED + 2)
    ctrl_deltas: list[dict] = []
    for u in ctrl_units:
        verses_raw = extract_verses(u)
        verses_norm = [normalize_rasm(v) for v in verses_raw]
        canon_text = " ".join(verses_norm)
        try:
            canon_feats = nine_channel_features(
                verses_norm, ref_bi, root_lm, canonical_text=canon_text,
            )
        except Exception:
            continue
        label = getattr(u, "label", None) or str(id(u))
        for _ in range(N_PERT_CTRL_PER_UNIT):
            pair = _apply_internal_perturbation(verses_norm, rng_c)
            if pair is None:
                continue
            pv, vi = pair
            try:
                deltas = _channel_deltas(
                    verses_norm, pv, ref_bi, root_lm, canon_feats,
                )
            except Exception:
                continue
            deltas_rec = {
                "pool": "ctrl", "unit": label, "vi": vi, **deltas,
            }
            ctrl_deltas.append(deltas_rec)

    print(f"[{EXP}] ctrl perturbations complete: {len(ctrl_deltas)} "
          f"({time.time() - t0:.0f}s)")

    # ---- Compute per-channel detection rates -------------------------------
    per_channel_ctrl_q95: dict[str, float] = {}
    per_channel_p_ctrl: dict[str, float] = {}
    per_channel_MW: dict[str, dict] = {}
    per_channel_stats: dict[str, dict] = {}
    from scipy import stats as _stats  # lazy import

    for ch in CHANNELS_ALL:
        q_vals = [r[ch] for r in quran_deltas]
        c_vals = [r[ch] for r in ctrl_deltas]
        if not q_vals or not c_vals:
            per_channel_ctrl_q95[ch] = float("inf")
            per_channel_p_ctrl[ch] = 0.0
            per_channel_MW[ch] = {"error": "insufficient samples"}
            per_channel_stats[ch] = {}
            continue
        q95 = float(np.quantile(c_vals, 1 - ALPHA))
        p_ctrl = sum(1 for v in q_vals if v > q95) / len(q_vals)
        try:
            res = _stats.mannwhitneyu(q_vals, c_vals, alternative="greater")
            mw_p = float(res.pvalue)
        except Exception:
            mw_p = float("nan")
        per_channel_ctrl_q95[ch] = q95
        per_channel_p_ctrl[ch] = p_ctrl
        per_channel_MW[ch] = {
            "p_one_sided_greater": mw_p,
            "quran_median": float(np.median(q_vals)),
            "ctrl_median": float(np.median(c_vals)),
            "quran_mean": float(np.mean(q_vals)),
            "ctrl_mean": float(np.mean(c_vals)),
        }
        per_channel_stats[ch] = {
            "n_quran": len(q_vals), "n_ctrl": len(c_vals),
            "quran_max": float(np.max(q_vals)), "ctrl_max": float(np.max(c_vals)),
        }

    # Composite: P = 1 - prod(1 - p_ch)
    prod_miss = 1.0
    for ch in CHANNELS_ALL:
        prod_miss *= (1.0 - per_channel_p_ctrl[ch])
    P_composite = 1.0 - prod_miss
    best_single = max(per_channel_p_ctrl.values()) if per_channel_p_ctrl else 0.0
    gain = P_composite - best_single

    # Fire-rate definition from exp09: |z| > 2 on >= 3 channels.
    # We compute z using the CTRL |delta| distribution as the null, per
    # channel. Fire rate = fraction of Quran perturbations with >= 3
    # channels |z| > 2.
    ctrl_mu_sd: dict[str, tuple[float, float]] = {}
    for ch in CHANNELS_ALL:
        c_vals = [r[ch] for r in ctrl_deltas]
        if len(c_vals) >= 3:
            mu = float(np.mean(c_vals))
            sd = float(np.std(c_vals, ddof=1))
            ctrl_mu_sd[ch] = (mu, sd)
        else:
            ctrl_mu_sd[ch] = (0.0, 1.0)
    n_fire_ge_3 = 0
    for r in quran_deltas:
        n_channels_fired = 0
        for ch in CHANNELS_ALL:
            mu, sd = ctrl_mu_sd[ch]
            if sd > 1e-12:
                z = (r[ch] - mu) / sd
                if abs(z) > 2.0:
                    n_channels_fired += 1
        if n_channels_fired >= 3:
            n_fire_ge_3 += 1
    fire_rate_quran = (
        n_fire_ge_3 / len(quran_deltas) if quran_deltas else 0.0
    )
    # Same computation for ctrl (leave-one-out would be cleaner, but
    # computing z against own-distribution will give an approx 5% FPR).
    n_fire_ge_3_ctrl = 0
    for r in ctrl_deltas:
        n_channels_fired = 0
        for ch in CHANNELS_ALL:
            mu, sd = ctrl_mu_sd[ch]
            if sd > 1e-12:
                z = (r[ch] - mu) / sd
                if abs(z) > 2.0:
                    n_channels_fired += 1
        if n_channels_fired >= 3:
            n_fire_ge_3_ctrl += 1
    fire_rate_ctrl = (
        n_fire_ge_3_ctrl / len(ctrl_deltas) if ctrl_deltas else 0.0
    )

    # ---- Adiyat-specific deltas (close docs/ADIYAT_ANALYSIS_AR.md §13) ----
    # NOTE: Al-Adiyat has only 11 verses, below the Band-A [15, 100] floor.
    # For this sub-test only, we pull from the FULL Quran corpus (all 114).
    adiyat_results: list[dict] = []
    q_all = corpora.get("quran", [])
    q100 = None
    for u in q_all:
        label = getattr(u, "label", "")
        lbl = str(label)
        # canonical label format is "Q:100"
        if lbl == "Q:100" or lbl.endswith(":100"):
            q100 = u
            break
    if q100 is None and len(q_all) >= 100:
        # fallback: canonical Quran order is 1..114; index 99 = surah 100
        q100 = q_all[99]

    if q100 is not None:
        verses_raw = extract_verses(q100)
        verses_norm = [normalize_rasm(v) for v in verses_raw]
        canon_text = " ".join(verses_norm)
        try:
            canon_feats_adiyat = nine_channel_features(
                verses_norm, ref_bi, root_lm, canonical_text=canon_text,
            )
            for variant in ADIYAT_VARIANTS:
                pv = _inject_adiyat_variant(verses_norm, variant)
                if pv is None:
                    adiyat_results.append({
                        "variant": variant["name"],
                        "description": variant["description"],
                        "error": "orig substring not found in surah 100",
                    })
                    continue
                pert_feats = nine_channel_features(
                    pv, ref_bi, root_lm, canonical_text=canon_text,
                )
                deltas = {
                    ch: abs(pert_feats[ch] - canon_feats_adiyat[ch])
                    for ch in CHANNELS_ALL
                }
                z_table = {}
                n_fire = 0
                for ch in CHANNELS_ALL:
                    mu, sd = ctrl_mu_sd[ch]
                    z = ((deltas[ch] - mu) / sd) if sd > 1e-12 else 0.0
                    z_table[ch] = round(z, 3)
                    if abs(z) > 2.0:
                        n_fire += 1
                adiyat_results.append({
                    "variant": variant["name"],
                    "description": variant["description"],
                    "deltas": {k: round(v, 4) for k, v in deltas.items()},
                    "z_vs_ctrl_null": z_table,
                    "n_channels_fired_abs_z_gt_2": n_fire,
                    "fired_channels": [
                        ch for ch in CHANNELS_ALL if abs(z_table[ch]) > 2.0
                    ],
                })
        except Exception as e:
            adiyat_results.append({"error": f"Adiyat computation failed: {e}"})
    else:
        adiyat_results.append({"error": "surah 100 (Al-Adiyat) not found in Band-A Quran units"})

    # ---- Assemble + write --------------------------------------------------
    feedback_r1_from_docs = {
        "exp09_calibrated_rate_any_position_swaps": 0.494,
        "feedback_estimate_for_internal_swaps": 0.50,
    }
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "Does R1's 9-channel surah-level fingerprint retain non-zero "
            "detection on INTERNAL single-letter substitutions (non-initial "
            "non-terminal letter in non-boundary word of non-terminal verse)? "
            "exp29 showed the 5-D Phi_M is byte-exact blind; R1 includes "
            "letter-bigram (C), gzip (E), and 34x34 spectral (A) channels "
            "that SHOULD have non-zero sensitivity."
        ),
        "config": {
            "seed": SEED,
            "alpha_null_threshold": ALPHA,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "n_pert_quran_per_surah": N_PERT_QURAN_PER_SURAH,
            "n_pert_ctrl_per_unit": N_PERT_CTRL_PER_UNIT,
            "ctrl_n_units_sampled": CTRL_N_UNITS,
            "perturbation": (
                "internal-letter: non-initial non-terminal letter in "
                "non-boundary word of non-terminal verse, replaced by a "
                "random distinct Arabic consonant from the 28-letter set"
            ),
        },
        "n_quran_units": len(q_units),
        "n_quran_perturbations": len(quran_deltas),
        "n_ctrl_units": len(ctrl_units),
        "n_ctrl_perturbations": len(ctrl_deltas),
        "r1_control_training_corpora": control_names,
        "channels": list(CHANNELS_ALL),
        "per_channel_ctrl_q95_threshold": per_channel_ctrl_q95,
        "per_channel_p_detect_ctrl_null": per_channel_p_ctrl,
        "per_channel_mannwhitney": per_channel_MW,
        "per_channel_stats": per_channel_stats,
        "per_channel_ctrl_mu_sd_for_z_fire_rate": {
            ch: {"mu": mu, "sd": sd} for ch, (mu, sd) in ctrl_mu_sd.items()
        },
        "p_composite_ctrl_null": P_composite,
        "best_single_channel_p_ctrl": best_single,
        "gain_composite_over_best_single": gain,
        "fire_rate_quran_ge_3_channels_abs_z_gt_2": fire_rate_quran,
        "fire_rate_ctrl_ge_3_channels_abs_z_gt_2": fire_rate_ctrl,
        "adiyat_variants": adiyat_results,
        "feedback_r1_reference": feedback_r1_from_docs,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    outfile = out_dir / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console summary ---------------------------------------------------
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] -- Per-channel detection rate (ctrl-null) --")
    for ch in CHANNELS_ALL:
        p = per_channel_p_ctrl[ch]
        mw = per_channel_MW[ch]
        if "p_one_sided_greater" in mw:
            mw_p = mw["p_one_sided_greater"]
            print(f"   {ch:18s}  p_ctrl = {p:.3f}   MW p(Q>C) = {mw_p:.2e}")
        else:
            print(f"   {ch:18s}  p_ctrl = {p:.3f}   MW = N/A")
    print(f"[{EXP}] P_composite (9-channel product-code) = {P_composite:.3f}")
    print(f"[{EXP}]   best single channel p            = {best_single:.3f}")
    print(f"[{EXP}]   gain over best single             = {gain:+.3f}")
    print(f"[{EXP}] Fire-rate (>=3 ch, |z|>2): Quran = {fire_rate_quran:.3f}  "
          f"ctrl = {fire_rate_ctrl:.3f}")
    print(f"[{EXP}] -- Adiyat variants on surah 100 --")
    for r in adiyat_results:
        if "error" in r:
            print(f"   {r.get('variant', '?'):20s}  ERROR: {r['error']}")
        else:
            n = r["n_channels_fired_abs_z_gt_2"]
            print(f"   {r['variant']:20s}  channels fired |z|>2: {n}/9   "
                  f"fired: {r['fired_channels']}")

    self_check_end(pre, exp_name=EXP)
    return report


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
