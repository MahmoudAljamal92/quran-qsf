"""experiments/exp123_three_feature_universal_hunt/run.py — 3-feature equation hunt.

Generalisation of exp122 to 3-feature combinations with stricter acceptance
(CV < 0.01 vs exp122's CV < 0.10). Searches for a universal tighter than F75.

PREREG: experiments/exp123_three_feature_universal_hunt/PREREG.md
Input:  results/auxiliary/_phi_universal_xtrad_sizing.json (SHA-256 locked)
Output: results/experiments/exp123_three_feature_universal_hunt/exp123_three_feature_universal_hunt.json
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and locked constants

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp123_three_feature_universal_hunt"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
INPUT_SIZING = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

EXPECTED_INPUT_SHA256 = (
    "0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22"
)

EXPECTED_CORPORA = [
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "hindawi",
    "ksucca",
    "arabic_bible",
    "hebrew_tanakh",
    "greek_nt",
    "pali",
    "avestan_yasna",
]
FEATURE_NAMES = [
    "VL_CV",
    "p_max",
    "H_EL",
    "bigram_distinct_ratio",
    "gzip_efficiency",
]

# Acceptance thresholds (PREREG §4)
CV_TIGHTER_THAN_F75 = 0.01      # stricter than exp122's 0.10; F75 was 0.0194
CV_TIGHT = 0.10                  # exp122's bar
Z_OUTLIER = 5.0
Z_NO_COMPETITOR_STRICT = 1.5    # stricter than exp122's 2.0
Z_NO_COMPETITOR = 2.0


# ---------------------------------------------------------------------------
# Safe ops

def _safe_log(x):
    if x <= 0.0:
        return float("nan")
    return math.log(x)


def _safe_log2(x):
    if x <= 0.0:
        return float("nan")
    return math.log2(x)


def _safe_div(num, den):
    if den == 0.0:
        return float("nan")
    return num / den


def _safe_sqrt(x):
    if x < 0.0:
        return float("nan")
    return math.sqrt(x)


# ---------------------------------------------------------------------------
# Candidate generation: 3-feature combinations

def build_candidates():
    """Return list of (label, callable f -> value) for 3-feature candidates only."""
    cands = []
    triples = list(itertools.combinations(FEATURE_NAMES, 3))

    for f_i, f_j, f_k in triples:
        # Sums
        cands.append((f"3F::{f_i}+{f_j}+{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: f[a] + f[b] + f[c]))
        cands.append((f"3F::log({f_i})+log({f_j})+log({f_k})",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_log(f[a]) + _safe_log(f[b]) + _safe_log(f[c])))

        # Differences/sums (6 sign permutations)
        cands.append((f"3F::{f_i}+{f_j}-{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: f[a] + f[b] - f[c]))
        cands.append((f"3F::{f_i}-{f_j}+{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: f[a] - f[b] + f[c]))
        cands.append((f"3F::-{f_i}+{f_j}+{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: -f[a] + f[b] + f[c]))
        cands.append((f"3F::{f_i}-{f_j}-{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: f[a] - f[b] - f[c]))

        # Products
        cands.append((f"3F::{f_i}*{f_j}*{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k: f[a] * f[b] * f[c]))
        cands.append((f"3F::sqrt({f_i}*{f_j}*{f_k})",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_sqrt(f[a] * f[b] * f[c])))

        # Ratios
        cands.append((f"3F::{f_i}/({f_j}*{f_k})",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_div(f[a], f[b] * f[c])))
        cands.append((f"3F::({f_i}*{f_j})/{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_div(f[a] * f[b], f[c])))
        cands.append((f"3F::({f_i}+{f_j})/{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_div(f[a] + f[b], f[c])))
        cands.append((f"3F::{f_i}/({f_j}+{f_k})",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_div(f[a], f[b] + f[c])))

        # Information-theoretic (F75-class generalisation: H_EL + log2(other features · 28))
        cands.append((f"3F::{f_i}+log2({f_j}*{f_k}*28)",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          f[a] + _safe_log2(f[b] * f[c] * 28)))
        cands.append((f"3F::{f_i}+log2({f_j}*28)+log2({f_k}*28)",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          f[a] + _safe_log2(f[b] * 28) + _safe_log2(f[c] * 28)))

        # Mixed transforms
        cands.append((f"3F::sqrt({f_i})+{f_j}*{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_sqrt(f[a]) + f[b] * f[c]))
        cands.append((f"3F::{f_i}*log2({f_j})+{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          f[a] * _safe_log2(f[b]) + f[c]))

        # Squared sums (2-norm-like)
        cands.append((f"3F::{f_i}^2+{f_j}^2+{f_k}^2",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          f[a] ** 2 + f[b] ** 2 + f[c] ** 2))

        # Mean of three
        cands.append((f"3F::({f_i}+{f_j}+{f_k})/3",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          (f[a] + f[b] + f[c]) / 3.0))

        # Weighted log-product (effective alphabet usage)
        cands.append((f"3F::log2({f_i})*log2({f_j})+{f_k}",
                      lambda f, a=f_i, b=f_j, c=f_k:
                          _safe_log2(f[a]) * _safe_log2(f[b]) + f[c]))

    return cands


# ---------------------------------------------------------------------------
# Statistics (mirrors exp122's evaluate_candidate / classify)


def evaluate_candidate(label, fn, per_corpus):
    values = {}
    for c in EXPECTED_CORPORA:
        try:
            v = fn(per_corpus[c])
        except (ZeroDivisionError, ValueError, OverflowError):
            return {"label": label, "skipped": True, "reason": "exception"}
        if v is None or (isinstance(v, float)
                         and (math.isnan(v) or math.isinf(v))):
            return {"label": label, "skipped": True, "reason": "nan_or_inf"}
        values[c] = float(v)

    quran_v = values["quran"]
    others = [v for c, v in values.items() if c != "quran"]

    mean_o = sum(others) / len(others)
    var_o = sum((v - mean_o) ** 2 for v in others) / len(others)
    std_o = math.sqrt(var_o)
    if std_o == 0.0:
        return {"label": label, "skipped": True, "reason": "zero_std"}

    cv = std_o / abs(mean_o) if mean_o != 0.0 else float("inf")
    z_quran = (quran_v - mean_o) / std_o
    z_per_corpus = {c: (v - mean_o) / std_o for c, v in values.items()}
    max_other_abs_z = max(abs(z_per_corpus[c]) for c in EXPECTED_CORPORA
                          if c != "quran")

    return {
        "label": label,
        "skipped": False,
        "values": values,
        "mean_others": mean_o,
        "std_others": std_o,
        "cv_others": cv,
        "z_quran": z_quran,
        "abs_z_quran": abs(z_quran),
        "max_other_abs_z": max_other_abs_z,
        "z_per_corpus": z_per_corpus,
    }


def classify(stats):
    if stats.get("skipped"):
        return "SKIPPED"
    cv = stats["cv_others"]
    az = stats["abs_z_quran"]
    moa = stats["max_other_abs_z"]

    # Strict: tighter than F75
    if (cv < CV_TIGHTER_THAN_F75 and az >= Z_OUTLIER
            and moa <= Z_NO_COMPETITOR_STRICT):
        return "PASS_tighter_than_F75"
    # Standard exp122-bar PASS at 3-feature
    if cv < CV_TIGHT and az >= Z_OUTLIER and moa <= Z_NO_COMPETITOR:
        return "PASS_zipf_class_3feature"
    # Tight but not Quran-specific
    if cv < CV_TIGHTER_THAN_F75 and az < Z_OUTLIER:
        return "PARTIAL_TIGHTER"
    # Quran-extreme but not tight
    if az >= Z_OUTLIER:
        return "PARTIAL_3feature_outlier"
    return "WEAK_OR_FAIL"


def aggregate_verdict(per_candidate):
    cls = [r["classification"] for r in per_candidate if not r.get("skipped")]
    if "PASS_tighter_than_F75" in cls:
        return "PASS_tighter_than_F75"
    if "PASS_zipf_class_3feature" in cls:
        return "PASS_zipf_class_3feature"
    if "PARTIAL_TIGHTER" in cls and "PARTIAL_3feature_outlier" in cls:
        return "PARTIAL_tightness_and_outlier_separate"
    if "PARTIAL_TIGHTER" in cls:
        return "PARTIAL_only_tightness_no_outlier"
    if "PARTIAL_3feature_outlier" in cls:
        return "PARTIAL_only_outlier_no_tightness"
    return "FAIL_no_3feature_zipf"


# ---------------------------------------------------------------------------
# Main


def main():
    t0 = time.time()

    # ---- A1: input SHA-256 ------------------------------------------------
    raw = INPUT_SIZING.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != EXPECTED_INPUT_SHA256:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_input_sha256_mismatch",
            "expected_sha256": EXPECTED_INPUT_SHA256,
            "actual_sha256": actual_sha,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_input_sha256_mismatch: {actual_sha}")
        return

    sizing = json.loads(raw.decode("utf-8"))
    medians = sizing["medians"]

    # ---- A2/A3: feature/corpus presence -----------------------------------
    for c in EXPECTED_CORPORA:
        if c not in medians:
            raise SystemExit(f"missing corpus: {c}")
        for fn in FEATURE_NAMES:
            if fn not in medians[c]:
                raise SystemExit(f"missing feature {fn} for corpus {c}")

    per_corpus = {c: {fn: float(medians[c][fn]) for fn in FEATURE_NAMES}
                  for c in EXPECTED_CORPORA}

    # ---- Build candidates -------------------------------------------------
    candidates = build_candidates()
    n_candidates = len(candidates)

    # Deduplicate by label
    seen_labels = set()
    deduped = []
    for label, fn in candidates:
        if label in seen_labels:
            continue
        seen_labels.add(label)
        deduped.append((label, fn))
    candidates = deduped
    n_candidates = len(candidates)

    per_candidate = []
    for label, fn in candidates:
        stats = evaluate_candidate(label, fn, per_corpus)
        stats["classification"] = classify(stats)
        per_candidate.append(stats)

    n_skipped = sum(1 for r in per_candidate if r.get("skipped"))
    n_evaluated = n_candidates - n_skipped

    overall_verdict = aggregate_verdict(per_candidate)

    # ---- Top-K rankings --------------------------------------------------
    evaluated = [r for r in per_candidate if not r.get("skipped")]

    def _slim(r):
        return {
            "label": r["label"],
            "classification": r["classification"],
            "cv_others": r["cv_others"],
            "abs_z_quran": r["abs_z_quran"],
            "z_quran": r["z_quran"],
            "max_other_abs_z": r["max_other_abs_z"],
            "mean_others": r["mean_others"],
            "std_others": r["std_others"],
            "values": r["values"],
            "z_per_corpus": r["z_per_corpus"],
        }

    pass_strict = [r for r in evaluated
                   if r["classification"] == "PASS_tighter_than_F75"]
    pass_strict.sort(key=lambda r: (-r["abs_z_quran"], r["cv_others"]))

    pass_standard = [r for r in evaluated
                     if r["classification"] == "PASS_zipf_class_3feature"]
    pass_standard.sort(key=lambda r: (-r["abs_z_quran"], r["cv_others"]))

    partial_tighter = [r for r in evaluated
                       if r["classification"] == "PARTIAL_TIGHTER"]
    partial_tighter.sort(key=lambda r: r["cv_others"])

    partial_outlier = [r for r in evaluated
                       if r["classification"] == "PARTIAL_3feature_outlier"]
    partial_outlier.sort(key=lambda r: -r["abs_z_quran"])

    top_pass_strict = [_slim(r) for r in pass_strict[:5]]
    top_pass_standard = [_slim(r) for r in pass_standard[:5]]
    top_partial_tighter = [_slim(r) for r in partial_tighter[:5]]
    top_partial_outlier = [_slim(r) for r in partial_outlier[:5]]
    top_z = [_slim(r) for r in
             sorted(evaluated, key=lambda r: -r["abs_z_quran"])[:10]]
    top_cv = [_slim(r) for r in
              sorted(evaluated, key=lambda r: r["cv_others"])[:10]]

    # ---- prereg hash ------------------------------------------------------
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    # ---- audit -----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_input_sha256_match": actual_sha == EXPECTED_INPUT_SHA256,
            "A2_features_match": True,
            "A3_corpora_match": True,
            "A5_n_candidates_le_300": n_candidates <= 300,
            "n_candidates": n_candidates,
            "n_evaluated": n_evaluated,
            "n_skipped": n_skipped,
        },
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H80",
        "hypothesis": (
            "There exists a 3-feature closed-form g(features) such that "
            "g is tighter than F75 (CV < 0.01) across the 10 non-Quran corpora "
            "AND the Quran is the unique global outlier (|z|>=5, max other |z|<=1.5)."
        ),
        "verdict": overall_verdict,
        "verdict_reason": (
            f"{len(pass_strict)} PASS_tighter_than_F75; "
            f"{len(pass_standard)} PASS_zipf_class_3feature; "
            f"{len(partial_tighter)} PARTIAL_TIGHTER; "
            f"{len(partial_outlier)} PARTIAL_3feature_outlier."
        ),
        "prereg_hash": prereg_hash,
        "input_sizing_sha256": actual_sha,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "FEATURE_NAMES": FEATURE_NAMES,
            "CV_TIGHTER_THAN_F75": CV_TIGHTER_THAN_F75,
            "CV_TIGHT": CV_TIGHT,
            "Z_OUTLIER": Z_OUTLIER,
            "Z_NO_COMPETITOR_STRICT": Z_NO_COMPETITOR_STRICT,
            "Z_NO_COMPETITOR": Z_NO_COMPETITOR,
        },
        "results": {
            "n_candidates_evaluated": n_evaluated,
            "n_skipped": n_skipped,
            "n_pass_strict_tighter": len(pass_strict),
            "n_pass_standard": len(pass_standard),
            "n_partial_tighter": len(partial_tighter),
            "n_partial_outlier": len(partial_outlier),
            "top_pass_tighter_than_F75": top_pass_strict,
            "top_pass_zipf_class_3feature": top_pass_standard,
            "top_partial_tighter": top_partial_tighter,
            "top_partial_outlier": top_partial_outlier,
            "top_10_by_abs_z": top_z,
            "top_10_by_tightness": top_cv,
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 4),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Console summary --------------------------------------------------------
    print(f"# {EXP_NAME}")
    print(f"# verdict: {overall_verdict}")
    print(f"# candidates: {n_candidates} evaluated={n_evaluated} skipped={n_skipped}")
    print(f"# PASS_tighter_than_F75={len(pass_strict)}  "
          f"PASS_zipf_class_3feature={len(pass_standard)}")
    print(f"# PARTIAL_TIGHTER={len(partial_tighter)}  "
          f"PARTIAL_3feature_outlier={len(partial_outlier)}")
    if pass_strict:
        print("\n## PASS_tighter_than_F75 (best 5):")
        for r in pass_strict[:5]:
            print(f"  {r['label']:55s} |z|={r['abs_z_quran']:5.2f} "
                  f"CV={r['cv_others']:.4f} max_other|z|={r['max_other_abs_z']:.2f}")
    if pass_standard:
        print("\n## PASS_zipf_class_3feature (best 5):")
        for r in pass_standard[:5]:
            print(f"  {r['label']:55s} |z|={r['abs_z_quran']:5.2f} "
                  f"CV={r['cv_others']:.4f} max_other|z|={r['max_other_abs_z']:.2f}")
    print("\n## Top 5 by tightness (lowest CV):")
    for r in sorted(evaluated, key=lambda r: r["cv_others"])[:5]:
        print(f"  {r['label']:55s} CV={r['cv_others']:.4f} "
              f"|z|={r['abs_z_quran']:5.2f} ({r['classification']})")
    print("\n## Top 5 by |z_quran|:")
    for r in sorted(evaluated, key=lambda r: -r["abs_z_quran"])[:5]:
        print(f"  {r['label']:55s} |z|={r['abs_z_quran']:5.2f} "
              f"CV={r['cv_others']:.4f} ({r['classification']})")
    print(f"\n# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
