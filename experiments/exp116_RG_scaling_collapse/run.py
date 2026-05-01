"""exp116_RG_scaling_collapse — renormalization-group / coarse-graining scaling-law test.

For each corpus and each surah/chapter with n_verses >= 32, group consecutive L verses
into super-verses at scales L ∈ {1, 2, 4, 8, 16}. Compute 4 features at each scale.
Fit per-feature power-law exponent. Test universal-collapse and Quran-distinctive-scaling
hypotheses.

Prereg: experiments/exp116_RG_scaling_collapse/PREREG.md
Hypothesis ID: H71.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import pickle
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats as scs

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PHASE_PKL = ROOT / "results/checkpoints/phase_06_phi_m.pkl"
SCALES = [1, 2, 4, 8, 16]
MIN_VERSES = 32  # ≥ 2 super-verses at L=16
TOLERANCE_UNIVERSAL = 0.10  # std(alpha) tolerance for "universal collapse" pass
Z_TOLERANCE_QURAN_DISTINCTIVE = 2.0

ARABIC_CONSONANTS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strip_diacritics(text: str) -> str:
    """Strip Arabic diacritics (harakat / shadda / etc) to leave the consonant skeleton."""
    DIAC = set(
        "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
        "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
        "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
    )
    return "".join(c for c in str(text) if c not in DIAC)


def last_consonant(verse: str) -> str | None:
    """Return last Arabic consonant of the last word in a verse."""
    stripped = _strip_diacritics(verse).strip()
    tokens = stripped.split()
    if not tokens:
        return None
    last = tokens[-1]
    for ch in reversed(last):
        if ch in ARABIC_CONSONANTS:
            return ch
    return None


def features_at_scale(verses: list[str], L: int) -> dict | None:
    """Compute 4 features at scale L by grouping consecutive L verses into super-verses.
    Returns None if the surah has fewer than 2 super-verses at this scale.
    """
    n = len(verses)
    n_groups = n // L
    if n_groups < 2:
        return None
    super_verses = []
    for i in range(n_groups):
        block = verses[i * L:(i + 1) * L]
        super_verses.append(" ".join(block))

    # 1. EL_rate: fraction of super-verses ending with the modal end-letter
    el_letters = [last_consonant(v) for v in super_verses]
    el_letters = [c for c in el_letters if c is not None]
    if not el_letters:
        return None
    counter = Counter(el_letters)
    top_letter, top_count = counter.most_common(1)[0]
    el_rate = top_count / len(el_letters)
    p_max = el_rate  # by definition same here at the super-verse level

    # 2. H_EL: end-letter Shannon entropy (bits)
    total = sum(counter.values())
    h_el = -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)

    # 3. VL_CV: coefficient of variation of super-verse character lengths
    lengths = [len(_strip_diacritics(v).replace(" ", "")) for v in super_verses]
    if len(lengths) < 2:
        return None
    mean_len = float(np.mean(lengths))
    std_len = float(np.std(lengths, ddof=1))
    vl_cv = std_len / mean_len if mean_len > 0 else 0.0

    return {
        "L": L,
        "n_super_verses": n_groups,
        "EL_rate": el_rate,
        "p_max": p_max,
        "H_EL": h_el,
        "VL_CV": vl_cv,
    }


def fit_loglog_slope(x_vals: list[float], y_vals: list[float]) -> tuple[float, float, float]:
    """Fit y = A * x^alpha → log(y) = log(A) + alpha * log(x).
    Returns (alpha, intercept, r_squared).
    """
    log_x = np.log(np.array(x_vals))
    log_y = np.log(np.array(y_vals))
    # Drop NaN/Inf entries
    mask = np.isfinite(log_x) & np.isfinite(log_y)
    if mask.sum() < 3:
        return float("nan"), float("nan"), float("nan")
    slope, intercept, r_value, _, _ = scs.linregress(log_x[mask], log_y[mask])
    return float(slope), float(intercept), float(r_value ** 2)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    out_dir = ROOT / "results" / "experiments" / "exp116_RG_scaling_collapse"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading phase_06_phi_m from {PHASE_PKL.relative_to(ROOT)}...")
    with open(PHASE_PKL, "rb") as f:
        state = pickle.load(f)
    inner = state.get("state", state)
    corpora_units = inner.get("CORPORA")
    if corpora_units is None:
        print(f"ERROR: no CORPORA in state. Keys: {list(inner.keys())[:25]}")
        return 1

    print(f"Available corpora: {list(corpora_units.keys())}")

    # Per-corpus, per-surah/chapter, per-scale feature matrix
    per_surah_data: dict[str, list[dict]] = {}
    for corpus_name, units in corpora_units.items():
        if not units:
            continue
        rows = []
        for unit in units:
            verses = list(unit.verses) if hasattr(unit, "verses") else list(unit.get("verses", []))
            if len(verses) < MIN_VERSES:
                continue
            label = str(unit.label) if hasattr(unit, "label") else str(unit.get("label", "?"))
            row = {"corpus": corpus_name, "label": label, "n_verses": len(verses), "scales": {}}
            for L in SCALES:
                f_at_L = features_at_scale(verses, L)
                if f_at_L is None:
                    continue
                row["scales"][L] = f_at_L
            if len(row["scales"]) >= 3:  # need at least 3 scales for slope fit
                rows.append(row)
        if rows:
            per_surah_data[corpus_name] = rows

    print(f"\nPool size per corpus (n_chapters with ≥ {MIN_VERSES} verses, ≥ 3 scales):")
    for c, r in per_surah_data.items():
        print(f"  {c:<20s} {len(r)}")

    # Per-corpus, per-scale, per-feature MEDIAN
    feature_names = ["EL_rate", "p_max", "H_EL", "VL_CV"]
    per_corpus_medians: dict[str, dict[int, dict[str, float]]] = {}
    for corpus, rows in per_surah_data.items():
        per_corpus_medians[corpus] = {}
        for L in SCALES:
            feat_vals = {f: [] for f in feature_names}
            for row in rows:
                if L in row["scales"]:
                    for f in feature_names:
                        feat_vals[f].append(row["scales"][L][f])
            if any(len(v) >= 3 for v in feat_vals.values()):
                per_corpus_medians[corpus][L] = {
                    f: float(np.median(vals)) if vals else float("nan")
                    for f, vals in feat_vals.items()
                }

    # Per-corpus, per-feature power-law slope (alpha)
    per_corpus_slopes: dict[str, dict[str, dict]] = {}
    for corpus, scale_data in per_corpus_medians.items():
        slopes = {}
        for f in feature_names:
            x_vals, y_vals = [], []
            for L, feats in scale_data.items():
                v = feats[f]
                if v > 0 and not math.isnan(v):
                    x_vals.append(L)
                    y_vals.append(v)
            if len(x_vals) >= 3:
                alpha, intercept, r2 = fit_loglog_slope(x_vals, y_vals)
                slopes[f] = {"alpha": alpha, "intercept": intercept, "r_squared": r2,
                             "n_scales_used": len(x_vals)}
            else:
                slopes[f] = {"alpha": float("nan"), "intercept": float("nan"),
                             "r_squared": float("nan"), "n_scales_used": len(x_vals)}
        per_corpus_slopes[corpus] = slopes

    # Form-1: per-corpus universal collapse — std of feature exponents within each corpus
    form1_per_corpus: dict[str, dict] = {}
    for corpus, slopes in per_corpus_slopes.items():
        alphas = [slopes[f]["alpha"] for f in feature_names if not math.isnan(slopes[f]["alpha"])]
        if len(alphas) >= 3:
            mean_alpha = float(np.mean(alphas))
            std_alpha = float(np.std(alphas, ddof=1))
            form1_per_corpus[corpus] = {
                "mean_alpha": mean_alpha,
                "std_alpha": std_alpha,
                "n_features": len(alphas),
                "universal_pass_strict": std_alpha < TOLERANCE_UNIVERSAL,
            }
        else:
            form1_per_corpus[corpus] = {"mean_alpha": float("nan"), "std_alpha": float("nan"),
                                         "n_features": len(alphas), "universal_pass_strict": False}

    universal_collapse_pass = all(b.get("universal_pass_strict", False) for b in form1_per_corpus.values()
                                   if not math.isnan(b["mean_alpha"]))

    # Form-2: Quran-distinctive scaling per feature
    quran_slopes = per_corpus_slopes.get("quran", {})
    form2_per_feature: dict[str, dict] = {}
    for f in feature_names:
        if f not in quran_slopes or math.isnan(quran_slopes[f]["alpha"]):
            continue
        peer_alphas = [
            slopes[f]["alpha"]
            for c, slopes in per_corpus_slopes.items()
            if c != "quran" and f in slopes and not math.isnan(slopes[f]["alpha"])
        ]
        if len(peer_alphas) >= 3:
            peer_mean = float(np.mean(peer_alphas))
            peer_std = float(np.std(peer_alphas, ddof=1))
            quran_alpha = quran_slopes[f]["alpha"]
            z = (quran_alpha - peer_mean) / peer_std if peer_std > 0 else 0.0
            form2_per_feature[f] = {
                "quran_alpha": quran_alpha,
                "peer_alphas": peer_alphas,
                "peer_mean": peer_mean,
                "peer_std": peer_std,
                "z": z,
                "abs_z": abs(z),
                "distinctive_pass": abs(z) > Z_TOLERANCE_QURAN_DISTINCTIVE,
            }
    quran_distinctive_pass = any(b["distinctive_pass"] for b in form2_per_feature.values())
    n_features_distinctive = sum(b["distinctive_pass"] for b in form2_per_feature.values())

    # Verdict
    if universal_collapse_pass and quran_distinctive_pass:
        verdict = "PASS_both_universal_and_quran_distinctive"
    elif universal_collapse_pass:
        verdict = "PASS_universal_collapse_only"
    elif quran_distinctive_pass:
        verdict = "PASS_quran_distinctive_scaling_only"
    else:
        verdict = "FAIL_no_clean_signal"

    finished = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": "exp116_RG_scaling_collapse",
        "hypothesis_id": "H71",
        "verdict": verdict,
        "started_at_utc": started,
        "completed_at_utc": finished,
        "prereg_document": "experiments/exp116_RG_scaling_collapse/PREREG.md",
        "prereg_sha256": _sha256(ROOT / "experiments/exp116_RG_scaling_collapse/PREREG.md"),
        "frozen_constants": {
            "SCALES": SCALES,
            "MIN_VERSES": MIN_VERSES,
            "TOLERANCE_UNIVERSAL": TOLERANCE_UNIVERSAL,
            "Z_TOLERANCE_QURAN_DISTINCTIVE": Z_TOLERANCE_QURAN_DISTINCTIVE,
            "FEATURE_NAMES": feature_names,
        },
        "source_pkl_sha256": _sha256(PHASE_PKL),
        "pool_sizes": {c: len(r) for c, r in per_surah_data.items()},
        "per_corpus_medians": per_corpus_medians,
        "per_corpus_slopes": per_corpus_slopes,
        "form1_universal_collapse_per_corpus": form1_per_corpus,
        "form1_universal_collapse_pass": universal_collapse_pass,
        "form2_quran_distinctive_per_feature": form2_per_feature,
        "form2_quran_distinctive_pass": quran_distinctive_pass,
        "form2_n_features_distinctive": n_features_distinctive,
    }
    out_path = out_dir / "exp116_RG_scaling_collapse.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    # Pretty-print summary
    print(f"\n=== exp116 — RG / Coarse-Graining Scaling-Law Collapse ===\n")
    print(f"Per-corpus slope α for each feature (log-log fit over scales {SCALES}):")
    print(f"{'Corpus':<20s} {'EL_rate':>10s} {'p_max':>10s} {'H_EL':>10s} {'VL_CV':>10s} {'std(α)':>10s}")
    print("-" * 78)
    for corpus, slopes in per_corpus_slopes.items():
        row = [f"{slopes[f]['alpha']:>10.4f}" for f in feature_names]
        std_a = form1_per_corpus[corpus]["std_alpha"]
        print(f"{corpus:<20s} {row[0]} {row[1]} {row[2]} {row[3]} {std_a:>10.4f}")

    print(f"\n--- Form-1 (universal collapse, std(α) < {TOLERANCE_UNIVERSAL} per corpus) ---")
    for corpus, b in form1_per_corpus.items():
        flag = "PASS" if b["universal_pass_strict"] else "fail"
        print(f"  {corpus:<20s} mean(α) = {b['mean_alpha']:.4f}; std(α) = {b['std_alpha']:.4f}  [{flag}]")

    print(f"\n--- Form-2 (Quran-distinctive scaling, |z| > {Z_TOLERANCE_QURAN_DISTINCTIVE} per feature) ---")
    for f, b in form2_per_feature.items():
        flag = "PASS" if b["distinctive_pass"] else "fail"
        print(f"  {f:<10s} Quran α = {b['quran_alpha']:+.4f}; peer α mean = {b['peer_mean']:+.4f} ± {b['peer_std']:.4f}; z = {b['z']:+.4f}  [{flag}]")

    print(f"\nVerdict: {verdict}")
    print(f"Receipt: {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
