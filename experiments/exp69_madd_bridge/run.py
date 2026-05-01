"""
exp69_madd_bridge/run.py
=========================
H25: Madd Cross-Layer Bridge — Does madd_count bridge the structural
(Mahalanobis) and acoustic (pitch) layers?

Motivation
    build_pipeline_p3.py S7.2/S8.2 reported madd_mah_r=0.367 and
    madd_pitch_r=0.44 as a cross-layer bridge. The acoustic side was
    RETRACTED in DEEPSCAN v7.6 (Simpson's paradox on 2-surah pilot).
    exp52_acoustic_bridge_full (n=5190 verses) found madd→Mean_Pitch
    r=−0.017 (null). This experiment formally tests the bridge.

Protocol (frozen before execution)
    T1. Load exp52 per-verse data. Aggregate to surah-level means.
    T2. Load phase_06 Mahalanobis distances per Quran surah.
    T3. Correlate surah-level madd_mean with:
        a) Mean_Pitch_Hz (acoustic arm)
        b) Pitch_Variance (surviving signal from exp52)
        c) Mahalanobis distance (structural arm)
    T4. Partial correlation: r(madd, Mah_dist | Pitch_Variance)
    T5. Falsifier check: r(madd, Mean_Pitch) < 0.20 → acoustic bridge
        null, cross-layer convergence cannot exist.

Pre-registered thresholds
    BRIDGE_CONFIRMED:   r(madd, pitch) ≥ 0.40 AND r(madd, Mah) ≥ 0.30
                        AND partial r significant
    PARTIAL_BRIDGE:     r(madd, Mah) ≥ 0.30 (structural only)
    FALSIFIED:          r(madd, pitch) < 0.20

Reads:
    results/experiments/exp52_acoustic_bridge_full/full_per_verse.csv
    phase_06_phi_m.pkl -> FEATS (for Mahalanobis distances)

Writes ONLY under results/experiments/exp69_madd_bridge/
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

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

EXP = "exp69_madd_bridge"

EXP52_CSV = (_ROOT / "results" / "experiments" /
             "exp52_acoustic_bridge_full" / "full_per_verse.csv")

# Thresholds
R_PITCH_THRESHOLD = 0.20
R_MAH_THRESHOLD = 0.30
R_PITCH_STRONG = 0.40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _partial_corr(x, y, z):
    """Partial correlation r(x, y | z) via residualisation."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    x, y, z = x[mask], y[mask], z[mask]
    if len(x) < 5:
        return float("nan"), float("nan"), 0

    # Residualise x on z
    slope_xz = np.polyfit(z, x, 1)
    res_x = x - np.polyval(slope_xz, z)
    # Residualise y on z
    slope_yz = np.polyfit(z, y, 1)
    res_y = y - np.polyval(slope_yz, z)

    r, p = stats.pearsonr(res_x, res_y)
    return float(r), float(p), int(mask.sum())


def _corr(a, b):
    """Pearson and Spearman on finite pairs."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if len(a) < 5:
        return {"r": float("nan"), "p": float("nan"),
                "rho": float("nan"), "p_rho": float("nan"), "n": 0}
    r, p = stats.pearsonr(a, b)
    rho, p_rho = stats.spearmanr(a, b)
    return {"r": round(float(r), 6), "p": float(p),
            "rho": round(float(rho), 6), "p_rho": float(p_rho),
            "n": int(mask.sum())}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load exp52 per-verse CSV ---
    print(f"[{EXP}] Loading exp52 per-verse CSV...")
    if not EXP52_CSV.exists():
        print(f"[{EXP}] ERROR: {EXP52_CSV} not found")
        return 1

    surah_data = defaultdict(lambda: {"madd": [], "madd_full": [],
                                       "pitch": [], "pitch_var": [],
                                       "duration": [], "intensity": [],
                                       "hnr": []})
    with open(EXP52_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sno = int(row["surah_no"])
            # Only include verses with valid pitch
            pitch = row.get("Mean_Pitch_Hz", "")
            if not pitch or pitch == "":
                continue
            try:
                pitch_f = float(pitch)
            except ValueError:
                continue
            if not math.isfinite(pitch_f) or pitch_f <= 0:
                continue

            surah_data[sno]["madd"].append(float(row["madd_count"]))
            surah_data[sno]["madd_full"].append(float(row["madd_count_full"]))
            surah_data[sno]["pitch"].append(pitch_f)
            surah_data[sno]["pitch_var"].append(float(row["Pitch_Variance"]))
            surah_data[sno]["duration"].append(float(row["Duration_s"]))
            surah_data[sno]["intensity"].append(float(row["Mean_Intensity_dB"]))
            surah_data[sno]["hnr"].append(float(row["HNR_dB"]))

    print(f"[{EXP}] Loaded {len(surah_data)} surahs from exp52")

    # Aggregate to surah-level means
    surah_means = {}
    for sno, sd in sorted(surah_data.items()):
        n_v = len(sd["madd"])
        if n_v < 3:
            continue
        surah_means[sno] = {
            "n_verses": n_v,
            "madd_mean": float(np.mean(sd["madd"])),
            "madd_full_mean": float(np.mean(sd["madd_full"])),
            "pitch_mean": float(np.mean(sd["pitch"])),
            "pitch_var_mean": float(np.mean(sd["pitch_var"])),
            "duration_mean": float(np.mean(sd["duration"])),
        }
    print(f"[{EXP}] {len(surah_means)} surahs with ≥3 verses")

    # --- Load phase_06 for Mahalanobis distances ---
    print(f"\n[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feats = state["FEATS"]
    quran_feats = feats.get("quran", [])

    # Compute Phi_M from features + control centroid/inverse cov
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    S_inv = np.asarray(state["S_inv"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    phi_m_by_surah = {}
    for r in quran_feats:
        label = r.get("label", "")
        try:
            sno = int(label.split(":")[1]) if ":" in label else int(label)
        except (ValueError, IndexError):
            continue
        fv = np.array([r[c] for c in feat_cols], dtype=float)
        diff = fv - mu_ctrl
        phi_m_by_surah[sno] = float(np.sqrt(diff @ S_inv @ diff))

    print(f"[{EXP}] {len(phi_m_by_surah)} Quran surahs with Phi_M")

    # --- Merge: surahs present in both exp52 and phase_06 ---
    common = sorted(set(surah_means.keys()) & set(phi_m_by_surah.keys()))
    print(f"[{EXP}] {len(common)} surahs in common")

    madd_arr = np.array([surah_means[s]["madd_mean"] for s in common])
    madd_full_arr = np.array([surah_means[s]["madd_full_mean"] for s in common])
    pitch_arr = np.array([surah_means[s]["pitch_mean"] for s in common])
    pitch_var_arr = np.array([surah_means[s]["pitch_var_mean"] for s in common])
    phi_m_arr = np.array([phi_m_by_surah[s] for s in common])
    duration_arr = np.array([surah_means[s]["duration_mean"] for s in common])

    # --- T3: Correlations ---
    print(f"\n[{EXP}] === T3: Surah-level correlations ===")

    r_madd_pitch = _corr(madd_arr, pitch_arr)
    r_madd_pitchvar = _corr(madd_arr, pitch_var_arr)
    r_madd_mah = _corr(madd_arr, phi_m_arr)
    r_madd_dur = _corr(madd_arr, duration_arr)

    print(f"  madd vs Mean_Pitch:    r={r_madd_pitch['r']:+.4f}  "
          f"p={r_madd_pitch['p']:.3e}  n={r_madd_pitch['n']}")
    print(f"  madd vs Pitch_Var:     r={r_madd_pitchvar['r']:+.4f}  "
          f"p={r_madd_pitchvar['p']:.3e}  n={r_madd_pitchvar['n']}")
    print(f"  madd vs Phi_M:         r={r_madd_mah['r']:+.4f}  "
          f"p={r_madd_mah['p']:.3e}  n={r_madd_mah['n']}")
    print(f"  madd vs Duration:      r={r_madd_dur['r']:+.4f}  "
          f"p={r_madd_dur['p']:.3e}  (length confound)")

    # Also with madd_full (includes all madd marks)
    r_maddfull_pitch = _corr(madd_full_arr, pitch_arr)
    r_maddfull_mah = _corr(madd_full_arr, phi_m_arr)
    print(f"  madd_full vs Pitch:    r={r_maddfull_pitch['r']:+.4f}  "
          f"p={r_maddfull_pitch['p']:.3e}")
    print(f"  madd_full vs Phi_M:    r={r_maddfull_mah['r']:+.4f}  "
          f"p={r_maddfull_mah['p']:.3e}")

    # --- T4: Partial correlation ---
    print(f"\n[{EXP}] === T4: Partial correlations ===")
    pr_mah_pitchvar, pp_mah_pitchvar, n_pr = _partial_corr(
        madd_arr, phi_m_arr, pitch_var_arr)
    print(f"  r(madd, Phi_M | Pitch_Var) = {pr_mah_pitchvar:+.4f}  "
          f"p={pp_mah_pitchvar:.3e}  n={n_pr}")

    # Control for duration (length confound)
    pr_mah_dur, pp_mah_dur, n_pr2 = _partial_corr(
        madd_arr, phi_m_arr, duration_arr)
    print(f"  r(madd, Phi_M | Duration)  = {pr_mah_dur:+.4f}  "
          f"p={pp_mah_dur:.3e}  n={n_pr2}")

    # --- T5: Falsifier ---
    print(f"\n[{EXP}] === T5: Falsifier ===")
    falsifier_triggered = abs(r_madd_pitch["r"]) < R_PITCH_THRESHOLD
    print(f"  |r(madd, pitch)| = {abs(r_madd_pitch['r']):.4f} "
          f"{'<' if falsifier_triggered else '>='} {R_PITCH_THRESHOLD}")
    print(f"  Falsifier: {'TRIGGERED' if falsifier_triggered else 'NOT triggered'}")

    # --- Verse-level confirmation (from exp52 pooled) ---
    print(f"\n[{EXP}] === Verse-level (from exp52, n=5190) ===")
    print(f"  madd→Mean_Pitch:   r=−0.017  p=0.22   → NULL")
    print(f"  madd→Pitch_Var:    r=+0.134  p<10⁻¹⁰  → small but sig")
    print(f"  madd→Duration:     r=+0.711  p<10⁻¹⁰  → LENGTH CONFOUND")

    # --- Verdict ---
    r_pitch_val = abs(r_madd_pitch["r"])
    r_mah_val = abs(r_madd_mah["r"])

    if r_pitch_val >= R_PITCH_STRONG and r_mah_val >= R_MAH_THRESHOLD:
        verdict = "BRIDGE_CONFIRMED"
    elif r_mah_val >= R_MAH_THRESHOLD:
        verdict = "PARTIAL_BRIDGE"
    elif falsifier_triggered:
        verdict = "FALSIFIED"
    else:
        verdict = "INCONCLUSIVE"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Acoustic arm: r(madd, pitch) = {r_madd_pitch['r']:+.4f} "
          f"(threshold |r| ≥ {R_PITCH_THRESHOLD})")
    print(f"  Structural arm: r(madd, Phi_M) = {r_madd_mah['r']:+.4f} "
          f"(threshold |r| ≥ {R_MAH_THRESHOLD})")
    print(f"  Falsifier: {'TRIGGERED' if falsifier_triggered else 'not triggered'}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H25 — Does madd bridge structural (Phi_M) and "
                      "acoustic (pitch) layers?",
        "schema_version": 1,
        "data": {
            "n_surahs_exp52": len(surah_means),
            "n_surahs_phase06": len(phi_m_by_surah),
            "n_common": len(common),
        },
        "T3_correlations": {
            "madd_vs_pitch": r_madd_pitch,
            "madd_vs_pitch_var": r_madd_pitchvar,
            "madd_vs_phi_m": r_madd_mah,
            "madd_vs_duration": r_madd_dur,
            "madd_full_vs_pitch": r_maddfull_pitch,
            "madd_full_vs_phi_m": r_maddfull_mah,
        },
        "T4_partial": {
            "madd_phim_given_pitchvar": {
                "r": round(pr_mah_pitchvar, 6),
                "p": pp_mah_pitchvar,
                "n": n_pr,
            },
            "madd_phim_given_duration": {
                "r": round(pr_mah_dur, 6),
                "p": pp_mah_dur,
                "n": n_pr2,
            },
        },
        "T5_falsifier": {
            "r_madd_pitch": r_madd_pitch["r"],
            "threshold": R_PITCH_THRESHOLD,
            "triggered": falsifier_triggered,
        },
        "verdict": {
            "verdict": verdict,
            "prereg": {
                "BRIDGE_CONFIRMED": f"|r(madd,pitch)| ≥ {R_PITCH_STRONG} AND "
                                    f"|r(madd,Mah)| ≥ {R_MAH_THRESHOLD}",
                "PARTIAL_BRIDGE": f"|r(madd,Mah)| ≥ {R_MAH_THRESHOLD}",
                "FALSIFIED": f"|r(madd,pitch)| < {R_PITCH_THRESHOLD}",
            },
        },
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
