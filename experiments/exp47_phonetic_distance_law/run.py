"""
exp47_phonetic_distance_law/run.py
===================================
Phonetic-Distance Detection Law — curve fit from exp46 data.

Hypothesis (Law Candidate 1):
    detection_rate(pair) = f(phonetic_distance(pair))
    If f is monotonic and r >= 0.85, this qualifies as a publishable
    empirical law linking Arabic phonology to information-theoretic
    edit detectability.

Data: 7 emphatic-class pairs from exp46_emphatic_substitution
(FAST mode, 20 surahs, 598 total edits).

Multiple distance / predictor metrics are tested:
    M1: Hamming distance on discretised binary articulatory features
    M2: Weighted Euclidean on continuous articulatory features
    M3: Unweighted Euclidean (IPA-chart geometric)
    M4: n_edits as frequency proxy (from exp46)
    M5: log(n_edits) frequency proxy
    M6: Combined phonetic_dist x log(n_edits)
    M7: max_z_median from exp46 (CIRCULAR — included for calibration only)

For each metric, reports:
    - Pearson r, R^2, p-value
    - Spearman rho (rank correlation, robust to non-linearity)
    - Kendall concordance fraction
    - Linear fit y = a + b*x
    - Verdict: LAW CONFIRMED / SUGGESTIVE / FAILS

Pre-registered verdict thresholds (set before computation):
    |r| >= 0.85  =>  LAW CONFIRMED
    0.70 <= |r| < 0.85  =>  SUGGESTIVE
    |r| < 0.70  =>  FAILS

CAVEAT: n=7 data points; even r=0.85 has wide CI.  This documents
the relationship honestly but cannot establish a law without more data
(full-mode exp46, additional consonant classes, cross-corpus replication).

Reads:
    results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json

Writes ONLY under results/experiments/exp47_phonetic_distance_law/:
    exp47_phonetic_distance_law.json
    phonetic_distance_scatter.png
"""
from __future__ import annotations

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

EXP = "exp47_phonetic_distance_law"

# ---------------------------------------------------------------------------
# Phonetic feature vectors for Arabic consonants
# ---------------------------------------------------------------------------
# Each consonant is encoded as (place, manner, voice, emphatic, sibilant)
#
# place (continuous articulatory continuum):
#   labial=1, dental=2, interdental=2.5, alveolar=3, postalveolar=3.5,
#   palatal=4, velar=5, uvular=6, pharyngeal=7, glottal=8
#
# manner (continuous):
#   stop=0, affricate=0.5, fricative=1, nasal=2, lateral=3, trill=4,
#   approximant=5
#
# voice:    0=voiceless, 1=voiced
# emphatic: 0=plain, 1=pharyngealized
# sibilant: 0=no, 1=yes
PHONETIC_FEATURES = {
    "ا": (8.0, 0.5, 0, 0, 0),  # glottal stop (hamza / alef)
    "ب": (1.0, 0.0, 1, 0, 0),  # bilabial stop voiced
    "ت": (2.0, 0.0, 0, 0, 0),  # dental stop voiceless
    "ث": (2.5, 1.0, 0, 0, 0),  # interdental fricative voiceless
    "ج": (4.0, 0.5, 1, 0, 0),  # palatal affricate voiced
    "ح": (7.0, 1.0, 0, 0, 0),  # pharyngeal fricative voiceless
    "خ": (5.0, 1.0, 0, 0, 0),  # velar fricative voiceless
    "د": (2.0, 0.0, 1, 0, 0),  # dental stop voiced
    "ذ": (2.5, 1.0, 1, 0, 0),  # interdental fricative voiced
    "ر": (2.0, 4.0, 1, 0, 0),  # alveolar trill voiced
    "ز": (3.0, 1.0, 1, 0, 1),  # alveolar fricative voiced sibilant
    "س": (3.0, 1.0, 0, 0, 1),  # alveolar fricative voiceless sibilant
    "ش": (3.5, 1.0, 0, 0, 1),  # postalveolar fric voiceless sibilant
    "ص": (3.0, 1.0, 0, 1, 1),  # alveolar fric voiceless emphatic sibilant
    "ض": (2.0, 0.0, 1, 1, 0),  # dental stop voiced emphatic
    "ط": (2.0, 0.0, 0, 1, 0),  # dental stop voiceless emphatic
    "ظ": (2.5, 1.0, 1, 1, 0),  # interdental fric voiced emphatic
    "ع": (7.0, 1.0, 1, 0, 0),  # pharyngeal fricative voiced
    "غ": (5.0, 1.0, 1, 0, 0),  # velar fricative voiced
    "ف": (1.0, 1.0, 0, 0, 0),  # labiodental fricative voiceless
    "ق": (6.0, 0.0, 0, 0, 0),  # uvular stop voiceless
    "ك": (5.0, 0.0, 0, 0, 0),  # velar stop voiceless
    "ل": (2.0, 3.0, 1, 0, 0),  # alveolar lateral voiced
    "م": (1.0, 2.0, 1, 0, 0),  # bilabial nasal voiced
    "ن": (2.0, 2.0, 1, 0, 0),  # alveolar nasal voiced
    "ه": (8.0, 1.0, 0, 0, 0),  # glottal fricative voiceless
    "و": (1.0, 5.0, 1, 0, 0),  # bilabial approximant voiced
    "ي": (4.0, 5.0, 1, 0, 0),  # palatal approximant voiced
}

# The 7 emphatic-class pairs from exp46 (keys match exp46 JSON)
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
# Distance metrics
# ---------------------------------------------------------------------------
def _place_bin(p: float) -> int:
    if p <= 1.5:
        return 0  # labial
    if p <= 3.25:
        return 1  # dental / alveolar / interdental
    if p <= 4.5:
        return 2  # palatal
    if p <= 6.5:
        return 3  # velar / uvular
    if p <= 7.5:
        return 4  # pharyngeal
    return 5       # glottal


def hamming_distance(a: str, b: str) -> float:
    """Number of differing discretised binary features."""
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    d = 0
    d += int(_place_bin(fa[0]) != _place_bin(fb[0]))
    d += int(round(fa[1]) != round(fb[1]))  # manner bin
    d += int(fa[2] != fb[2])                # voice
    d += int(fa[3] != fb[3])                # emphatic
    d += int(fa[4] != fb[4])                # sibilant
    return float(d)


def weighted_euclidean(a: str, b: str,
                       w_place: float = 1.0,
                       w_manner: float = 1.5,
                       w_voice: float = 1.0,
                       w_emph: float = 0.5,
                       w_sib: float = 0.5) -> float:
    """Weighted Euclidean on continuous articulatory features."""
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    return math.sqrt(
        w_place * (fa[0] - fb[0]) ** 2
        + w_manner * (fa[1] - fb[1]) ** 2
        + w_voice * (fa[2] - fb[2]) ** 2
        + w_emph * (fa[3] - fb[3]) ** 2
        + w_sib * (fa[4] - fb[4]) ** 2
    )


def ipa_geometric(a: str, b: str) -> float:
    """Unweighted Euclidean — raw IPA-chart distance."""
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(fa, fb)))


# ---------------------------------------------------------------------------
# Correlation helpers
# ---------------------------------------------------------------------------
def _pearsonr(x: np.ndarray, y: np.ndarray):
    """Pearson r + two-sided p-value (n >= 3)."""
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
    # t-test for significance
    t_stat = r * math.sqrt((n - 2) / max(1e-15, 1 - r ** 2))
    from scipy.stats import t as t_dist
    p = float(2 * t_dist.sf(abs(t_stat), n - 2))
    return float(r), p


def _spearmanr(x: np.ndarray, y: np.ndarray):
    """Spearman rho via scipy."""
    from scipy.stats import spearmanr
    rho, p = spearmanr(x, y)
    return float(rho), float(p)


def _concordance(x: np.ndarray, y: np.ndarray) -> float:
    """Fraction of concordant pairs (Kendall-style)."""
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
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    # ---- Load exp46 results ------------------------------------------------
    exp46_path = (
        _ROOT / "results" / "experiments"
        / "exp46_emphatic_substitution" / "exp46_emphatic_substitution.json"
    )
    if not exp46_path.exists():
        raise FileNotFoundError(f"exp46 results not found: {exp46_path}")

    with open(exp46_path, "r", encoding="utf-8") as f:
        exp46 = json.load(f)

    per_class = exp46["per_class_summary"]

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

    # M1: Hamming (binary feature count)
    predictors["M1_hamming"] = np.array(
        [hamming_distance(d["a"], d["b"]) for d in data]
    )
    # M2: Weighted Euclidean
    predictors["M2_weighted_euclid"] = np.array(
        [weighted_euclidean(d["a"], d["b"]) for d in data]
    )
    # M3: IPA geometric (unweighted Euclidean)
    predictors["M3_ipa_geometric"] = np.array(
        [ipa_geometric(d["a"], d["b"]) for d in data]
    )
    # M4: n_edits (raw frequency proxy)
    predictors["M4_n_edits"] = np.array(
        [float(d["n_edits"]) for d in data]
    )
    # M5: log(n_edits)
    predictors["M5_log_n_edits"] = np.array(
        [math.log(max(d["n_edits"], 1)) for d in data]
    )
    # M6: Combined phonetic × log(frequency)
    predictors["M6_phon_x_logfreq"] = np.array([
        weighted_euclidean(d["a"], d["b"]) * math.log(max(d["n_edits"], 1))
        for d in data
    ])
    # M7: max_z_median from exp46 (CIRCULAR — for calibration only)
    predictors["M7_max_z_median_CIRCULAR"] = np.array(
        [d["max_z_median"] for d in data]
    )

    # ---- Evaluate each metric ---------------------------------------------
    metric_results = {}
    for name, vals in predictors.items():
        is_circ = "CIRCULAR" in name
        n_unique = len(set(vals.round(6).tolist()))

        pr, pp = _pearsonr(vals, rates)
        sr, sp = _spearmanr(vals, rates)
        conc = _concordance(vals, rates)

        # Linear fit
        if n_unique >= 2:
            slope, intercept = np.polyfit(vals, rates, 1)
            pred = slope * vals + intercept
            ss_res = float(((rates - pred) ** 2).sum())
            ss_tot = float(((rates - rates.mean()) ** 2).sum())
            R2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else float("nan")
        else:
            slope = intercept = 0.0
            R2 = float("nan")

        # Verdict
        if math.isnan(pr):
            verdict = "UNDEFINED (degenerate)"
        elif is_circ:
            verdict = f"CIRCULAR — r={pr:.3f} (not valid as independent predictor)"
        elif abs(pr) >= 0.85:
            verdict = "LAW CONFIRMED"
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

    overall = (
        "LAW CONFIRMED" if abs(best_r) >= 0.85 else
        "SUGGESTIVE" if abs(best_r) >= 0.70 else
        "FAILS"
    )

    # ---- Confound analysis: surah-length effect ---------------------------
    # exp46 per-surah data shows detection is driven by surah length
    # (short surahs -> high detection, long -> 0%). Per-class rates
    # are confounded by which surahs each pair's letters appear in.
    per_surah = exp46.get("per_surah_results", [])
    surah_note = (
        f"exp46 tested {len(per_surah)} surahs. "
        f"Detection ranges from {min(s['detection_rate'] for s in per_surah):.0%} "
        f"to {max(s['detection_rate'] for s in per_surah):.0%} per surah. "
        "Long surahs show 0% detection; short surahs show >50%. "
        "Per-class detection rates are confounded by letter-frequency × "
        "surah-length interaction. A controlled analysis holding surah "
        "length constant is needed to isolate the phonetic-distance effect."
    )

    # ---- Generate scatter plot --------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(
            "Phonetic-Distance Detection Law — exp47\n"
            f"Best non-circular metric: {best_name} (r = {best_r:.3f}) → {overall}",
            fontsize=13, fontweight="bold",
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

            # Regression line
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
            ax.set_ylim(-5, 50)

        plt.tight_layout()
        fig.savefig(out / "phonetic_distance_scatter.png", dpi=150)
        plt.close(fig)
        print(f"[{EXP}] Saved scatter plot to {out / 'phonetic_distance_scatter.png'}")
    except ImportError:
        print(f"[{EXP}] matplotlib not available — skipping plot")

    # ---- JSON report ------------------------------------------------------
    report = {
        "experiment": EXP,
        "hypothesis": (
            "detection_rate(pair) = f(phonetic_distance(pair)), monotonic, "
            "r >= 0.85 qualifies as publishable empirical law."
        ),
        "pre_registered_thresholds": {
            "LAW_CONFIRMED": "|r| >= 0.85",
            "SUGGESTIVE": "0.70 <= |r| < 0.85",
            "FAILS": "|r| < 0.70",
        },
        "data_source": "exp46_emphatic_substitution (FAST mode, 20 surahs)",
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
        "confound_analysis": {
            "surah_length_effect": surah_note,
            "n_edits_confound": (
                "n_edits ranges from 20 (dha/dhal) to 269 (ayn/alef). "
                "Pairs with more edits have more short-surah contributions "
                "where detection is intrinsically easier. The frequency "
                "predictor (M4/M5) captures part of this confound."
            ),
        },
        "honest_assessment": (
            "With standard articulatory phonetic features, the 7 emphatic "
            "pairs yield only 2-3 distinct distance values (most pairs "
            "differ by a single [+/- emphatic] or [+/- place] feature). "
            "This degeneracy limits the discriminative power of any purely "
            "phonetic distance metric. The COMBINED predictor "
            "(phonetic × log_freq) may capture more variance. "
            "A better approach for future work: compute the actual "
            "bigram-transition KL divergence between letter pairs from "
            "the corpus, which would give a statistical (not purely "
            "articulatory) distance."
        ),
        "future_work": [
            "Full-mode exp46 (all 114 surahs) to reduce sampling noise",
            "Surah-length-controlled analysis (per-class rate within length bins)",
            "Bigram-transition KL divergence as an alternative distance metric",
            "Cross-corpus replication (emphatic detection in control corpora)",
            "Additional consonant pairs beyond the 7 emphatic classes",
        ],
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console output ---------------------------------------------------
    # Reconfigure stdout for UTF-8 to avoid cp1252 errors on Windows
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )

    print(f"\n[{EXP}] === Phonetic-Distance Detection Law ===")
    print(f"  Data: {n} pairs from exp46 (FAST mode)")
    print()
    print(f"  {'Class':<16} {'Rate':>6} {'M2_dist':>8} {'n_edits':>8}")
    print(f"  {'-' * 16} {'-' * 6} {'-' * 8} {'-' * 8}")
    for d in sorted(data, key=lambda x: x["detection_rate"], reverse=True):
        m2 = weighted_euclidean(d["a"], d["b"])
        print(
            f"  {d['class_id']:<16} {d['detection_rate']:>6.1%} "
            f"{m2:>8.3f} {d['n_edits']:>8d}"
        )
    print()
    print(f"  {'Metric':<28} {'r':>7} {'ρ':>7} {'R²':>7} {'Verdict'}")
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
