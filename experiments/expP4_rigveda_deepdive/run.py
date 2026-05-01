"""
expP4_rigveda_deepdive/run.py
=============================
Deep-dive on the Rigveda's double-extreme signal:

  - `expP4_cross_tradition_R3`               z_path = -18.934 (most negative ever)
  - `expP4_diacritic_capacity_cross_tradition` R_prim = 0.918 (most saturated ever)

This experiment decomposes those two signals into per-maṇḍala measurements
and adds a long-range memory test (Hurst R/S), to see:

  PRED-DD-1: which maṇḍala carries the strongest path-minimality
  PRED-DD-2: how broadly the path-minimality signal is distributed
  PRED-DD-3: whether the Rigveda has Quran-like long-range memory (H > 0.6)
  PRED-DD-4: whether per-maṇḍala R_prim correlates with |z_path|

Reads only:
    data/corpora/sa/rigveda_mandala_*.json   (via raw_loader.load_vedic)

Writes ONLY under results/experiments/expP4_rigveda_deepdive/.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import raw_loader  # noqa: E402
from src.features import (  # noqa: E402
    derive_stopwords,
    el_rate,
    vl_cv,
    cn_rate,
    h_cond_initials,
    h_el,
)
from src.extended_tests4 import _hurst_rs  # noqa: E402

# Reuse Devanagari helpers from the cross-tradition diacritic experiment
from experiments.expP4_diacritic_capacity_cross_tradition.run import (  # noqa: E402
    _is_devanagari_base,
    _is_devanagari_diacritic,
)
from experiments.expA2_diacritic_capacity_universal.run import (  # noqa: E402
    _conditional_entropy_bits,
)

EXP = "expP4_rigveda_deepdive"
SEED = 42
N_PERM = 5000


# ---------------------------------------------------------------------------
# 5-D feature vector (matches expP4_cross_tradition_R3.run._features_lang_agnostic)
# ---------------------------------------------------------------------------
def _features_5d(verses: list[str], stops: set[str]) -> np.ndarray:
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, stops)
    hc = h_cond_initials(verses)
    he = h_el(verses)
    t = hc - he
    return np.array([el, cv, cn, hc, t], dtype=float)


def _z_score(X: np.ndarray) -> np.ndarray:
    X = X.astype(float).copy()
    for j in range(X.shape[1]):
        col = X[:, j]
        m = np.isnan(col)
        if m.any():
            col[m] = np.nanmedian(col)
            X[:, j] = col
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def _path_cost(X: np.ndarray) -> float:
    if len(X) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(X, axis=0), axis=1)))


def _r3_per_collection(units, seed: int) -> dict:
    """Run the path-cost test on one collection of units; mirrors
    expP4_cross_tradition_R3 byte-for-byte but parameterised by seed."""
    if not units or len(units) < 4:
        return {"n_units": len(units), "skipped": True, "reason": "n<4"}
    all_v = [v for u in units for v in u.verses]
    stops = derive_stopwords(all_v, top_n=20)
    X_raw = np.array(
        [_features_5d(u.verses, stops) for u in units], dtype=float,
    )
    n = X_raw.shape[0]
    X = _z_score(X_raw)
    canon = _path_cost(X)
    rng = np.random.default_rng(seed)
    perms = np.empty(N_PERM, dtype=float)
    for b in range(N_PERM):
        perms[b] = _path_cost(X[rng.permutation(n)])
    perm_mean = float(perms.mean())
    perm_std = float(perms.std())
    z = (canon - perm_mean) / (perm_std if perm_std > 0 else 1.0)
    pct_below = float((perms < canon).mean())
    p = max(pct_below, 1.0 / (N_PERM + 1))
    return {
        "n_units": int(n),
        "canonical_path_cost": float(canon),
        "perm_mean": perm_mean,
        "perm_std": perm_std,
        "z_path": float(z),
        "pct_perms_below_canon": pct_below,
        "p_one_sided": float(p),
        "n_perm": N_PERM,
        "seed": int(seed),
    }


# ---------------------------------------------------------------------------
# Per-maṇḍala A2 (Devanagari diacritic capacity)
# ---------------------------------------------------------------------------
def _devanagari_pairs(verses: list[str]) -> Counter:
    text = "\n".join(verses)
    pairs: Counter = Counter()
    chars = list(text)
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if _is_devanagari_diacritic(c) or c.isspace() or not c.isalpha():
            i += 1
            continue
        if not _is_devanagari_base(c):
            i += 1
            continue
        j = i + 1
        diacs: list[str] = []
        while j < n and _is_devanagari_diacritic(chars[j]):
            diacs.append(chars[j])
            j += 1
        pairs[(c, "".join(diacs) or "<none>")] += 1
        i = j
    return pairs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading Rigveda...")
    units = raw_loader.load_vedic()
    print(f"[{EXP}]   loaded {len(units)} sūktas")

    # --- group sūktas by maṇḍala from the label "rv:m{NN}:s{NNN}" ---
    by_mandala: dict[int, list] = defaultdict(list)
    for u in units:
        # label format: "rv:m01:s001"
        try:
            m = int(u.label.split(":")[1][1:])
        except (IndexError, ValueError):
            continue
        by_mandala[m].append(u)
    mandalas_present = sorted(by_mandala.keys())
    print(f"[{EXP}]   maṇḍalas present: {mandalas_present}")
    for m in mandalas_present:
        print(f"[{EXP}]     m{m:02d}: n_sukta={len(by_mandala[m])}")

    # ------------------------------------------------------------------ #
    # 1) Per-maṇḍala R3                                                  #
    # ------------------------------------------------------------------ #
    print(f"[{EXP}] computing per-maṇḍala R3 (5000 perms each)...")
    t0 = time.time()
    per_mandala_r3 = {}
    for m in mandalas_present:
        r = _r3_per_collection(by_mandala[m], seed=SEED + m)
        per_mandala_r3[f"m{m:02d}"] = r
        print(f"[{EXP}]     m{m:02d}  n={r['n_units']:>4d}  "
              f"z={r.get('z_path', float('nan')):+8.3f}  "
              f"p={r.get('p_one_sided', 1.0):.4f}")
    print(f"[{EXP}]   done in {time.time() - t0:.1f}s")

    # PRED-DD-1: which maṇḍala has most negative z?
    valid_z = [(k, v["z_path"]) for k, v in per_mandala_r3.items()
               if "z_path" in v]
    valid_z.sort(key=lambda kv: kv[1])  # most negative first
    most_negative = valid_z[0] if valid_z else (None, float("nan"))
    pred_dd_1 = "PASS" if (
        valid_z and most_negative[0] == "m09"
    ) else "FAIL"
    # PRED-DD-2: how many maṇḍalas pass z<-2 at p<0.025?
    n_pass = sum(
        1 for k, v in per_mandala_r3.items()
        if v.get("z_path", 0) < -2.0 and v.get("p_one_sided", 1.0) < 0.025
    )
    pred_dd_2 = "PASS" if n_pass >= 7 else "FAIL"

    # ------------------------------------------------------------------ #
    # 2) Per-maṇḍala A2 (Devanagari)                                     #
    # ------------------------------------------------------------------ #
    print(f"[{EXP}] computing per-maṇḍala diacritic capacity...")
    per_mandala_a2 = {}
    for m in mandalas_present:
        verses = [v for u in by_mandala[m] for v in u.verses]
        pairs = _devanagari_pairs(verses)
        ent = _conditional_entropy_bits(pairs)
        per_mandala_a2[f"m{m:02d}"] = ent
        print(f"[{EXP}]     m{m:02d}  n_pairs={ent.get('n_pairs', 0):>7d}  "
              f"R_combo={ent.get('ratio_R_combinations', 0):.4f}  "
              f"R_prim={ent.get('ratio_R_primitives', 0):.4f}")

    # ------------------------------------------------------------------ #
    # 3) Hurst on three Rigveda time-series in canonical order            #
    # ------------------------------------------------------------------ #
    print(f"[{EXP}] computing Hurst on canonical-order Rigveda series...")
    # 3a) Verse word-count sequence (18,079 ṛc-s)
    rc_words = []
    for u in units:                       # already in maṇḍala-then-sūkta order
        for v in u.verses:
            rc_words.append(len(v.split()))
    H_rc_words = _hurst_rs(rc_words)

    # 3b) Sūkta word-count sequence (1024)
    sukta_words = [u.n_words() for u in units]
    H_sukta_words = _hurst_rs(sukta_words)

    # 3c) Sūkta EL sequence (1024)
    sukta_el = [el_rate(u.verses) for u in units]
    H_sukta_el = _hurst_rs(sukta_el)

    print(f"[{EXP}]     H(verse word-count, n={len(rc_words)})    = {H_rc_words:.4f}")
    print(f"[{EXP}]     H(sūkta word-count, n={len(sukta_words)}) = {H_sukta_words:.4f}")
    print(f"[{EXP}]     H(sūkta EL,         n={len(sukta_el)})    = {H_sukta_el:.4f}")

    # PRED-DD-3: H > 0.6 on at least one of the three series
    H_values = [H_rc_words, H_sukta_words, H_sukta_el]
    H_max = max(h for h in H_values if not np.isnan(h)) if any(
        not np.isnan(h) for h in H_values
    ) else float("nan")
    pred_dd_3 = "PASS" if H_max > 0.6 else "FAIL"

    # ------------------------------------------------------------------ #
    # 4) Per-maṇḍala R_prim vs |z_path| correlation                       #
    # ------------------------------------------------------------------ #
    paired_rows = []
    for m in mandalas_present:
        key = f"m{m:02d}"
        r3 = per_mandala_r3[key]
        a2 = per_mandala_a2[key]
        if "z_path" not in r3 or "ratio_R_primitives" not in a2:
            continue
        paired_rows.append({
            "mandala":  key,
            "n_sukta":  r3["n_units"],
            "z_path":   r3["z_path"],
            "abs_z":    abs(r3["z_path"]),
            "p_one_sided": r3["p_one_sided"],
            "n_pairs":  a2.get("n_pairs", 0),
            "R_combo":  a2.get("ratio_R_combinations", 0.0),
            "R_prim":   a2.get("ratio_R_primitives", 0.0),
        })
    if len(paired_rows) >= 3:
        abs_z = [r["abs_z"]    for r in paired_rows]
        r_prim = [r["R_prim"]  for r in paired_rows]
        rho_prim, p_prim   = stats.spearmanr(abs_z, r_prim)
        r_combo = [r["R_combo"] for r in paired_rows]
        rho_combo, p_combo = stats.spearmanr(abs_z, r_combo)
    else:
        rho_prim = p_prim = rho_combo = p_combo = float("nan")
    pred_dd_4 = "PASS" if (not np.isnan(rho_prim)) and rho_prim > 0.4 else "FAIL"

    print(f"[{EXP}] per-maṇḍala correlations:")
    print(f"[{EXP}]   ρ(|z_path|, R_prim)  = {rho_prim:+.3f}  p={p_prim:.4f}")
    print(f"[{EXP}]   ρ(|z_path|, R_combo) = {rho_combo:+.3f}  p={p_combo:.4f}")

    # ------------------------------------------------------------------ #
    # 5) Bonus: compare Rigveda Hurst to locked Quran Hurst              #
    # ------------------------------------------------------------------ #
    locked_quran_H_rs = 0.7381   # ULTIMATE_SCORECARD: Supp_A_Hurst (R/S)
    H_compare = {
        "locked_quran_R_S_Hurst": locked_quran_H_rs,
        "rigveda_R_S_Hurst_rc_words": H_rc_words,
        "rigveda_R_S_Hurst_sukta_words": H_sukta_words,
        "rigveda_R_S_Hurst_sukta_EL": H_sukta_el,
        "rigveda_max_H": H_max,
        "rigveda_minus_quran_max_H": H_max - locked_quran_H_rs,
        "rigveda_long_range_memory_stronger": (H_max > locked_quran_H_rs),
    }

    overall = (
        "STRONG_DEEPDIVE_SUPPORT"   if (pred_dd_2 == "PASS" and pred_dd_3 == "PASS"
                                         and pred_dd_4 == "PASS")
        else "PARTIAL_DEEPDIVE_SUPPORT" if (pred_dd_2 == "PASS" or pred_dd_3 == "PASS")
        else "WEAK_DEEPDIVE_SUPPORT"
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "n_perm": N_PERM,
        "title": ("Per-maṇḍala R3 + diacritic-capacity + Hurst on the "
                  "Rigveda Saṃhitā: triangulating the double-extreme "
                  "signal observed in expP4_cross_tradition_R3 and "
                  "expP4_diacritic_capacity_cross_tradition."),
        "n_sukta_total": len(units),
        "n_rc_total": int(sum(u.n_verses() for u in units)),
        "mandalas_present": mandalas_present,
        "per_mandala_R3": per_mandala_r3,
        "per_mandala_A2_devanagari": per_mandala_a2,
        "paired_rows": paired_rows,
        "rigveda_Hurst": {
            "H_rc_words":    None if np.isnan(H_rc_words) else float(H_rc_words),
            "H_sukta_words": None if np.isnan(H_sukta_words) else float(H_sukta_words),
            "H_sukta_EL":    None if np.isnan(H_sukta_el) else float(H_sukta_el),
            "H_max":         None if np.isnan(H_max) else float(H_max),
            "n_rc":          len(rc_words),
            "n_sukta":       len(sukta_words),
        },
        "compare_to_locked_quran_Hurst": H_compare,
        "cross_correlation_per_mandala": {
            "spearman_rho_abs_z_vs_R_prim":  float(rho_prim) if not np.isnan(rho_prim) else None,
            "spearman_p_abs_z_vs_R_prim":    float(p_prim)   if not np.isnan(p_prim)   else None,
            "spearman_rho_abs_z_vs_R_combo": float(rho_combo) if not np.isnan(rho_combo) else None,
            "spearman_p_abs_z_vs_R_combo":   float(p_combo)   if not np.isnan(p_combo)   else None,
        },
        "pre_registered_outcomes": {
            "PRED_DD_1_mandala_9_strongest_z": pred_dd_1,
            "PRED_DD_1_actual_strongest_mandala": most_negative[0],
            "PRED_DD_1_actual_strongest_z":       float(most_negative[1])
                                                  if most_negative[0] else None,
            "PRED_DD_2_seven_of_ten_mandalas_significant": pred_dd_2,
            "PRED_DD_2_n_significant": int(n_pass),
            "PRED_DD_3_max_Hurst_over_0_6":   pred_dd_3,
            "PRED_DD_4_R_prim_z_path_corr_positive": pred_dd_4,
            "overall_verdict": overall,
        },
        "interpretation": [
            "If the Rigveda's path-minimality signal is broadly distributed "
            "across maṇḍalas (PRED_DD_2 PASS) AND the long-range memory "
            "holds (PRED_DD_3 PASS) AND the per-maṇḍala R_prim x |z_path| "
            "correlation is positive (PRED_DD_4 PASS), then the Rigveda "
            "is a coherent oral-mnemonic-coded corpus across all three "
            "axes (structural ordering, diacritic-channel utilisation, "
            "long-range temporal memory).",
            "Maṇḍala 9 (Soma hymns, the most ritually homogeneous "
            "stratum) carrying the strongest z would corroborate the "
            "ritual-mnemonic mechanism. Maṇḍala 9 NOT carrying the "
            "strongest z would hint that the path-minimality is not "
            "purely about ritual repetition.",
        ],
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print()
    print(f"[{EXP}] ========== summary ==========")
    print(f"[{EXP}] PRED-DD-1 (m09 strongest z): {pred_dd_1}  "
          f"actual = {most_negative[0]} (z={most_negative[1]:+.3f})")
    print(f"[{EXP}] PRED-DD-2 (≥7/10 mandalas pass z<-2 at p<0.025): "
          f"{pred_dd_2}  ({n_pass}/10)")
    print(f"[{EXP}] PRED-DD-3 (max H > 0.6): {pred_dd_3}  "
          f"H_rc={H_rc_words:.3f}  H_sukta_w={H_sukta_words:.3f}  "
          f"H_sukta_EL={H_sukta_el:.3f}  max={H_max:.3f}")
    print(f"[{EXP}] PRED-DD-4 (per-mandala R_prim, |z_path| ρ > 0.4): "
          f"{pred_dd_4}  rho={rho_prim:+.3f}  p={p_prim:.4f}")
    print(f"[{EXP}] OVERALL deep-dive verdict: {overall}")
    print(f"[{EXP}] (Locked Quran R/S Hurst = {locked_quran_H_rs:.4f}, "
          f"Rigveda max H = {H_max:.4f}, "
          f"diff = {H_max - locked_quran_H_rs:+.4f})")
    print(f"[{EXP}] wrote {outfile}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
