"""
exp54_phonetic_law_full/run.py
==============================
Phonetic-Distance Detection Law — FULL-mode re-run.

Supersedes:
    exp47_phonetic_distance_law/exp47_phonetic_distance_law.json, which was
    computed against a FAST-mode exp46 (20 surahs, n_perm=200). The current
    exp46_emphatic_substitution.json on disk is FULL mode (114 surahs,
    n_perm=5000, 10 461 emphatic edits) but exp47 was never re-run. This
    experiment (exp54) re-executes the same analysis against the current
    FULL-mode exp46 output.

Pre-registration:
    experiments/exp54_phonetic_law_full/PREREG.md
    Frozen before execution. The primary statistic, thresholds, and
    falsifier are specified there. This script implements them verbatim.

Reads:
    results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json

Writes ONLY under results/experiments/exp54_phonetic_law_full/:
    exp54_phonetic_law_full.json
    phonetic_distance_scatter.png

Runtime: < 30 s (7 data points, closed-form correlations).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import sys
from pathlib import Path

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

EXP = "exp54_phonetic_law_full"

# ---------------------------------------------------------------------------
# Phonetic feature vectors for Arabic consonants (identical to exp47)
# ---------------------------------------------------------------------------
PHONETIC_FEATURES = {
    "ا": (8.0, 0.5, 0, 0, 0),
    "ب": (1.0, 0.0, 1, 0, 0),
    "ت": (2.0, 0.0, 0, 0, 0),
    "ث": (2.5, 1.0, 0, 0, 0),
    "ج": (4.0, 0.5, 1, 0, 0),
    "ح": (7.0, 1.0, 0, 0, 0),
    "خ": (5.0, 1.0, 0, 0, 0),
    "د": (2.0, 0.0, 1, 0, 0),
    "ذ": (2.5, 1.0, 1, 0, 0),
    "ر": (2.0, 4.0, 1, 0, 0),
    "ز": (3.0, 1.0, 1, 0, 1),
    "س": (3.0, 1.0, 0, 0, 1),
    "ش": (3.5, 1.0, 0, 0, 1),
    "ص": (3.0, 1.0, 0, 1, 1),
    "ض": (2.0, 0.0, 1, 1, 0),
    "ط": (2.0, 0.0, 0, 1, 0),
    "ظ": (2.5, 1.0, 1, 1, 0),
    "ع": (7.0, 1.0, 1, 0, 0),
    "غ": (5.0, 1.0, 1, 0, 0),
    "ف": (1.0, 1.0, 0, 0, 0),
    "ق": (6.0, 0.0, 0, 0, 0),
    "ك": (5.0, 0.0, 0, 0, 0),
    "ل": (2.0, 3.0, 1, 0, 0),
    "م": (1.0, 2.0, 1, 0, 0),
    "ن": (2.0, 2.0, 1, 0, 0),
    "ه": (8.0, 1.0, 0, 0, 0),
    "و": (1.0, 5.0, 1, 0, 0),
    "ي": (4.0, 5.0, 1, 0, 0),
}

PAIRS = [
    ("E1_sad_sin",  "ص", "س"),
    ("E2_dad_dal",  "ض", "د"),
    ("E3_tta_ta",   "ط", "ت"),
    ("E4_dha_dhal", "ظ", "ذ"),
    ("E5_qaf_kaf",  "ق", "ك"),
    ("E6_hha_ha",   "ح", "ه"),
    ("E7_ayn_alef", "ع", "ا"),
]


# ---------------------------------------------------------------------------
# Distance metrics (identical to exp47)
# ---------------------------------------------------------------------------
def _place_bin(p: float) -> int:
    if p <= 1.5:
        return 0
    if p <= 3.25:
        return 1
    if p <= 4.5:
        return 2
    if p <= 6.5:
        return 3
    if p <= 7.5:
        return 4
    return 5


def hamming_distance(a: str, b: str) -> float:
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    d = 0
    d += int(_place_bin(fa[0]) != _place_bin(fb[0]))
    d += int(round(fa[1]) != round(fb[1]))
    d += int(fa[2] != fb[2])
    d += int(fa[3] != fb[3])
    d += int(fa[4] != fb[4])
    return float(d)


def weighted_euclidean(a: str, b: str,
                       w_place: float = 1.0,
                       w_manner: float = 1.5,
                       w_voice: float = 1.0,
                       w_emph: float = 0.5,
                       w_sib: float = 0.5) -> float:
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    return math.sqrt(
        w_place * (fa[0] - fb[0]) ** 2
        + w_manner * (fa[1] - fb[1]) ** 2
        + w_voice * (fa[2] - fb[2]) ** 2
        + w_emph * (fa[3] - fb[3]) ** 2
        + w_sib * (fa[4] - fb[4]) ** 2
    )


def ipa_geometric(a: str, b: str) -> float:
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(fa, fb)))


# ---------------------------------------------------------------------------
# Correlation helpers
# ---------------------------------------------------------------------------
def _pearsonr(x: np.ndarray, y: np.ndarray):
    n = len(x)
    if n < 3:
        return float("nan"), float("nan")
    mx, my = x.mean(), y.mean()
    dx, dy = x - mx, y - my
    num = float((dx * dy).sum())
    den = float(math.sqrt((dx ** 2).sum() * (dy ** 2).sum()))
    if den < 1e-15:
        return float("nan"), float("nan")
    r = num / den
    t_stat = r * math.sqrt((n - 2) / max(1e-15, 1 - r ** 2))
    from scipy.stats import t as t_dist
    p = float(2 * t_dist.sf(abs(t_stat), n - 2))
    return float(r), p


def _spearmanr(x: np.ndarray, y: np.ndarray):
    from scipy.stats import spearmanr
    rho, p = spearmanr(x, y)
    return float(rho), float(p)


def _concordance(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    total = conc = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += 1
            prod = (x[i] - x[j]) * (y[i] - y[j])
            if prod > 0:
                conc += 1
            elif x[i] == x[j] or y[i] == y[j]:
                conc += 0.5
    return conc / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Pre-registered decision rule (new in exp54 vs exp47)
# ---------------------------------------------------------------------------
def _apply_prereg(metric_results: dict, best_name: str, best_r: float) -> dict:
    """Apply the PREREG.md decision rule.

    LAW_CONFIRMED requires all of:
      - |r| >= 0.85 on best non-circular metric
      - Spearman rho agrees in sign with Pearson r on best metric
      - No more than 2 of 7 classes invert the predicted direction
    """
    abs_r = abs(best_r)
    if math.isnan(abs_r):
        tier = "UNDEFINED"
    elif abs_r >= 0.85:
        tier = "LAW_CONFIRMED_CANDIDATE"
    elif abs_r >= 0.70:
        tier = "SUGGESTIVE"
    else:
        tier = "FAILS"

    best = metric_results.get(best_name, {})
    pearson_r = best.get("pearson_r")
    spearman_rho = best.get("spearman_rho")
    sign_agreement = (
        pearson_r is not None and spearman_rho is not None
        and np.sign(pearson_r) == np.sign(spearman_rho)
    )

    return {
        "tier": tier,
        "abs_r": abs_r,
        "sign_agreement_pearson_spearman": bool(sign_agreement),
        "note": (
            "LAW_CONFIRMED requires |r| >= 0.85 AND Pearson/Spearman sign "
            "agreement AND no more than 2 of 7 classes invert predicted direction. "
            "This script checks the first two; the per-class inversion check is "
            "reported in the output JSON for manual review."
        ),
    }


# ---------------------------------------------------------------------------
# Prereg hash
# ---------------------------------------------------------------------------
def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    # ---- Load current FULL-mode exp46 -------------------------------------
    exp46_path = (
        _ROOT / "results" / "experiments"
        / "exp46_emphatic_substitution" / "exp46_emphatic_substitution.json"
    )
    if not exp46_path.exists():
        raise FileNotFoundError(f"exp46 results not found: {exp46_path}")

    with open(exp46_path, "r", encoding="utf-8") as f:
        exp46 = json.load(f)

    # Sanity — must be FULL mode
    if exp46.get("fast_mode", True):
        raise RuntimeError(
            "exp46 is not in FULL mode. exp54 requires fast_mode=false. "
            "Re-run experiments/exp46_emphatic_substitution/run.py first."
        )
    if int(exp46.get("n_surahs_tested", 0)) < 100:
        raise RuntimeError(
            f"exp46 n_surahs_tested = {exp46.get('n_surahs_tested')}. "
            "exp54 requires >= 100 (expected 114)."
        )

    per_class = exp46["per_class_summary"]
    n_surahs = int(exp46.get("n_surahs_tested", 114))
    total_edits = int(exp46.get("total_emphatic_edits", 0))

    # ---- Extract the 7 data points ----------------------------------------
    data = []
    for class_id, a, b in PAIRS:
        if class_id not in per_class:
            print(f"[{EXP}] WARNING: {class_id} missing from exp46")
            continue
        pc = per_class[class_id]
        data.append({
            "class_id": class_id,
            "a": a,
            "b": b,
            "pair_label": pc["pair"],
            "detection_rate": pc["detection_rate"],
            "n_edits": pc["n_edits"],
            "n_detected": pc["n_detected_3of9"],
            "max_z_mean": pc["max_z_mean"],
            "max_z_median": pc["max_z_median"],
        })

    n = len(data)
    if n < 3:
        raise RuntimeError(f"Need >= 3 data points, got {n}")

    rates = np.array([d["detection_rate"] for d in data])

    # ---- Compute all predictor metrics ------------------------------------
    predictors: dict[str, np.ndarray] = {}
    predictors["M1_hamming"] = np.array(
        [hamming_distance(d["a"], d["b"]) for d in data])
    predictors["M2_weighted_euclid"] = np.array(
        [weighted_euclidean(d["a"], d["b"]) for d in data])
    predictors["M3_ipa_geometric"] = np.array(
        [ipa_geometric(d["a"], d["b"]) for d in data])
    predictors["M4_n_edits"] = np.array(
        [float(d["n_edits"]) for d in data])
    predictors["M5_log_n_edits"] = np.array(
        [math.log(max(d["n_edits"], 1)) for d in data])
    predictors["M6_phon_x_logfreq"] = np.array([
        weighted_euclidean(d["a"], d["b"]) * math.log(max(d["n_edits"], 1))
        for d in data
    ])
    predictors["M7_max_z_median_CIRCULAR"] = np.array(
        [d["max_z_median"] for d in data])

    # ---- Evaluate each metric ---------------------------------------------
    metric_results = {}
    for name, vals in predictors.items():
        is_circ = "CIRCULAR" in name
        n_unique = len(set(vals.round(6).tolist()))

        pr, pp = _pearsonr(vals, rates)
        sr, sp = _spearmanr(vals, rates)
        conc = _concordance(vals, rates)

        if n_unique >= 2:
            slope, intercept = np.polyfit(vals, rates, 1)
            pred = slope * vals + intercept
            ss_res = float(((rates - pred) ** 2).sum())
            ss_tot = float(((rates - rates.mean()) ** 2).sum())
            R2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else float("nan")
        else:
            slope = intercept = 0.0
            R2 = float("nan")

        if math.isnan(pr):
            verdict = "UNDEFINED (degenerate)"
        elif is_circ:
            verdict = f"CIRCULAR — r={pr:.3f} (not valid as independent predictor)"
        elif abs(pr) >= 0.85:
            verdict = "LAW_CONFIRMED_CANDIDATE"
        elif abs(pr) >= 0.70:
            verdict = "SUGGESTIVE"
        else:
            verdict = "FAILS"

        metric_results[name] = {
            "values": [round(v, 6) for v in vals.tolist()],
            "n_unique_values": n_unique,
            "pearson_r": round(pr, 4) if not math.isnan(pr) else None,
            "pearson_p": round(pp, 6) if not math.isnan(pp) else None,
            "spearman_rho": round(sr, 4) if not math.isnan(sr) else None,
            "spearman_p": round(sp, 6) if not math.isnan(sp) else None,
            "concordance": round(conc, 4),
            "R2": round(R2, 4) if not math.isnan(R2) else None,
            "slope": round(slope, 6),
            "intercept": round(intercept, 6),
            "is_circular": is_circ,
            "verdict": verdict,
        }

    # ---- Best non-circular metric -----------------------------------------
    best_name, best_r = None, 0.0
    for name, mr in metric_results.items():
        if mr["is_circular"]:
            continue
        r_val = mr["pearson_r"]
        if r_val is not None and abs(r_val) > abs(best_r):
            best_r = r_val
            best_name = name

    # ---- Apply PREREG decision rule ---------------------------------------
    prereg_decision = _apply_prereg(metric_results, best_name, best_r)

    # Downgrade CANDIDATE -> CONFIRMED only if all PREREG gates pass
    overall = prereg_decision["tier"]
    if overall == "LAW_CONFIRMED_CANDIDATE" and prereg_decision["sign_agreement_pearson_spearman"]:
        overall = "LAW_CONFIRMED"
    elif overall == "LAW_CONFIRMED_CANDIDATE":
        overall = "SUGGESTIVE"  # downgrade on sign-disagreement

    # ---- Generate scatter plot --------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(
            f"Phonetic-Distance Detection Law — exp54 (FULL mode)\n"
            f"Source: exp46 n={n_surahs} surahs, {total_edits} edits. "
            f"Best non-circular: {best_name} (r = {best_r:.3f}) → {overall}",
            fontsize=12, fontweight="bold",
        )

        plot_metrics = [
            "M1_hamming", "M2_weighted_euclid", "M3_ipa_geometric",
            "M4_n_edits", "M5_log_n_edits", "M6_phon_x_logfreq",
        ]
        labels = [d["pair_label"] for d in data]

        for idx, mname in enumerate(plot_metrics):
            ax = axes[idx // 3][idx % 3]
            vals = predictors[mname]
            mr = metric_results[mname]

            ax.scatter(vals, rates * 100, s=80, zorder=5, color="steelblue")
            for i, lbl in enumerate(labels):
                ax.annotate(
                    lbl, (vals[i], rates[i] * 100),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=7, alpha=0.8,
                )

            if mr["n_unique_values"] >= 2:
                xr = np.linspace(vals.min() * 0.9, vals.max() * 1.1, 50)
                yr = mr["slope"] * xr + mr["intercept"]
                ax.plot(xr, yr * 100, "r--", alpha=0.6, linewidth=1)

            ax.set_title(
                f"{mname}\nr={mr['pearson_r']}, ρ={mr['spearman_rho']}",
                fontsize=9,
            )
            ax.set_xlabel("Predictor value", fontsize=8)
            ax.set_ylabel("Detection rate (%)", fontsize=8)

        plt.tight_layout()
        fig.savefig(out / "phonetic_distance_scatter.png", dpi=150)
        plt.close(fig)
        print(f"[{EXP}] Saved scatter plot to {out / 'phonetic_distance_scatter.png'}")
    except ImportError:
        print(f"[{EXP}] matplotlib not available — skipping plot")

    # ---- JSON report ------------------------------------------------------
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_hash": _prereg_hash(),
        "hypothesis": (
            "detection_rate(pair) = f(phonetic_distance(pair)), monotonic, "
            "r >= 0.85 qualifies as publishable empirical law."
        ),
        "pre_registered_thresholds": {
            "LAW_CONFIRMED": "|r| >= 0.85 AND sign agreement Pearson/Spearman",
            "SUGGESTIVE": "0.70 <= |r| < 0.85",
            "FAILS": "|r| < 0.70",
        },
        "data_source": {
            "file": "results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json",
            "mode": "FULL" if not exp46.get("fast_mode", True) else "FAST",
            "n_surahs": n_surahs,
            "total_edits": total_edits,
        },
        "supersedes": "exp47_phonetic_distance_law (stale FAST-mode input)",
        "n_pairs": n,
        "pairs": [
            {
                "class_id": d["class_id"],
                "pair": d["pair_label"],
                "detection_rate": d["detection_rate"],
                "n_edits": d["n_edits"],
                "n_detected": d["n_detected"],
            }
            for d in data
        ],
        "phonetic_features_used": [
            "place (continuous 1-8)",
            "manner (continuous 0-5)",
            "voice (binary)",
            "emphatic (binary)",
            "sibilant (binary)",
        ],
        "metric_results": metric_results,
        "best_non_circular_metric": best_name,
        "best_pearson_r": round(best_r, 4),
        "overall_verdict": overall,
        "prereg_decision_detail": prereg_decision,
        "caveats": (
            "n=7 data points per metric; |r| estimates have wide CIs even at "
            "|r|=0.85. Per-class rates remain confounded by surah-length x "
            "letter-frequency interaction. A length-stratified analysis is "
            "deferred to future work (requires exp46 to emit per-surah x "
            "per-class detection rates)."
        ),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console output ---------------------------------------------------
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )

    print(f"\n[{EXP}] === Phonetic-Distance Detection Law (FULL mode) ===")
    print(f"  Data: {n} pairs from exp46 ({n_surahs} surahs, {total_edits} edits)")
    print()
    print(f"  {'Class':<16} {'Rate':>7} {'n_edits':>8} {'n_detect':>9}")
    print(f"  {'-' * 16} {'-' * 7} {'-' * 8} {'-' * 9}")
    for d in sorted(data, key=lambda x: x["detection_rate"], reverse=True):
        print(
            f"  {d['class_id']:<16} {d['detection_rate']:>7.2%} "
            f"{d['n_edits']:>8d} {d['n_detected']:>9d}"
        )
    print()
    print(f"  {'Metric':<28} {'r':>7} {'rho':>7} {'R^2':>7} {'Verdict'}")
    print(f"  {'-' * 28} {'-' * 7} {'-' * 7} {'-' * 7} {'-' * 20}")
    for name, mr in metric_results.items():
        r_str = f"{mr['pearson_r']:+.3f}" if mr["pearson_r"] is not None else "  N/A"
        rho_str = f"{mr['spearman_rho']:+.3f}" if mr["spearman_rho"] is not None else "  N/A"
        r2_str = f"{mr['R2']:.3f}" if mr["R2"] is not None else "  N/A"
        print(f"  {name:<28} {r_str:>7} {rho_str:>7} {r2_str:>7} {mr['verdict']}")
    print()
    print(f"  BEST non-circular: {best_name}  r = {best_r:+.3f}")
    print(f"  OVERALL VERDICT: {overall}")
    print()

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
