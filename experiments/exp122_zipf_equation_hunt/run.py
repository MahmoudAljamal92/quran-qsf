"""experiments/exp122_zipf_equation_hunt/run.py — Zipf-class equation hunt.

Search ~500 closed-form candidate equations g(features) = const for one that:
  (a) is tight (CV < 0.10) across the 10 non-Quran corpora;
  (b) has Quran at |z| >= 5;
  (c) has no other corpus at |z| > 2.

If found: PASS_zipf_class_equation_found.
If only some criteria: PARTIAL_*.
If none: FAIL_no_zipf_class_equation.

PREREG: experiments/exp122_zipf_equation_hunt/PREREG.md
Input:  results/auxiliary/_phi_universal_xtrad_sizing.json (SHA-256 locked in PREREG A1)
Output: results/experiments/exp122_zipf_equation_hunt/exp122_zipf_equation_hunt.json
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
EXP_NAME = "exp122_zipf_equation_hunt"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
INPUT_SIZING = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# Locked from PREREG §6 audit hook A1
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

# Acceptance criteria (PREREG §4)
CV_TIGHT = 0.10
Z_OUTLIER = 5.0
Z_NO_COMPETITOR = 2.0
# Partial fallback thresholds
CV_PARTIAL = 0.20
Z_PARTIAL = 3.0


# ---------------------------------------------------------------------------
# Candidate algebra. Every candidate is a (label, lambda f -> value) where
# `f` is a dict mapping feature_name -> per-corpus median value.
#
# We build candidates dynamically so the count is reproducible from the code.
# ---------------------------------------------------------------------------


def _safe_log(x: float) -> float:
    if x <= 0.0:
        return float("nan")
    return math.log(x)


def _safe_log2(x: float) -> float:
    if x <= 0.0:
        return float("nan")
    return math.log2(x)


def _safe_div(num: float, den: float) -> float:
    if den == 0.0:
        return float("nan")
    return num / den


def _safe_sqrt(x: float) -> float:
    if x < 0.0:
        return float("nan")
    return math.sqrt(x)


def _safe_pow(x: float, p: float) -> float:
    if x < 0.0 and not float(p).is_integer():
        return float("nan")
    try:
        return x ** p
    except (OverflowError, ValueError):
        return float("nan")


def _binary_entropy(p: float) -> float:
    """H_2(p) = -p log2 p - (1-p) log2 (1-p), with continuity at 0/1."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def build_candidates():
    """Return list of (label, callable f->value). Deterministic order."""
    cands = []

    # ---- Cat-1: single-feature transforms ---------------------------------
    transforms = [
        ("{}", lambda v: v),
        ("log({})", lambda v: _safe_log(v)),
        ("log2({})", lambda v: _safe_log2(v)),
        ("log(1-{})", lambda v: _safe_log(1.0 - v)),
        ("sqrt({})", lambda v: _safe_sqrt(v)),
        ("1/{}", lambda v: _safe_div(1.0, v)),
        ("{}^2", lambda v: v * v),
        ("1-{}", lambda v: 1.0 - v),
    ]
    for fname in FEATURE_NAMES:
        for tlabel, tfn in transforms:
            label = "Cat1::" + tlabel.format(fname)
            cands.append((label, _make_unary(fname, tfn)))

    # ---- Cat-2: two-feature compositions ----------------------------------
    for fi, fj in itertools.permutations(FEATURE_NAMES, 2):
        # symmetric (compute once per unordered pair)
        if fi < fj:
            cands.append((f"Cat2::{fi}*{fj}",
                          _make_binary(fi, fj, lambda a, b: a * b)))
            cands.append((f"Cat2::{fi}+{fj}",
                          _make_binary(fi, fj, lambda a, b: a + b)))
            cands.append((f"Cat2::{fi}^2+{fj}^2",
                          _make_binary(fi, fj, lambda a, b: a * a + b * b)))
            cands.append((f"Cat2::{fi}^2-{fj}^2",
                          _make_binary(fi, fj, lambda a, b: a * a - b * b)))
            cands.append((f"Cat2::sqrt({fi}*{fj})",
                          _make_binary(fi, fj, lambda a, b: _safe_sqrt(a * b))))
            cands.append((f"Cat2::log({fi})+log({fj})",
                          _make_binary(fi, fj,
                                       lambda a, b: _safe_log(a) + _safe_log(b))))

        # asymmetric
        cands.append((f"Cat2::{fi}/{fj}",
                      _make_binary(fi, fj, lambda a, b: _safe_div(a, b))))
        cands.append((f"Cat2::{fi}-{fj}",
                      _make_binary(fi, fj, lambda a, b: a - b)))
        cands.append((f"Cat2::{fi}+log({fj})",
                      _make_binary(fi, fj,
                                   lambda a, b: a + _safe_log(b))))
        cands.append((f"Cat2::{fi}*log({fj})",
                      _make_binary(fi, fj,
                                   lambda a, b: a * _safe_log(b))))
        cands.append((f"Cat2::{fi}/log({fj})",
                      _make_binary(fi, fj,
                                   lambda a, b: _safe_div(a, _safe_log(b)))))

    # ---- Cat-3: three-feature compositions --------------------------------
    for triple in itertools.permutations(FEATURE_NAMES, 3):
        fi, fj, fk = triple
        cands.append((f"Cat3::{fi}*{fj}/{fk}",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: _safe_div(a * b, c))))
        cands.append((f"Cat3::{fi}/({fj}*{fk})",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: _safe_div(a, b * c))))
        cands.append((f"Cat3::{fi}+{fj}-{fk}",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: a + b - c)))
        cands.append((f"Cat3::{fi}*{fj}-{fk}",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: a * b - c)))
        cands.append((f"Cat3::{fi}*{fj}+{fk}",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: a * b + c)))
        cands.append((f"Cat3::({fi}+{fj})/{fk}",
                      _make_ternary(fi, fj, fk,
                                    lambda a, b, c: _safe_div(a + b, c))))

    # ---- Cat-4: information-theoretic combinations ------------------------
    # alphabet for each corpus: we use the Quran 28-letter Arabic skeleton as
    # the canonical reference here (the 5-D space is already alphabet-agnostic
    # via H_EL having been computed in each corpus's own alphabet).
    A_REF = 28
    LOG2_A = math.log2(A_REF)

    cands.append(("Cat4::H_EL/log2(28)",
                  lambda f: f["H_EL"] / LOG2_A))
    cands.append(("Cat4::1-H_EL/log2(28)",
                  lambda f: 1.0 - f["H_EL"] / LOG2_A))
    cands.append(("Cat4::H_EL+log2(p_max*28)",
                  lambda f: f["H_EL"] + _safe_log2(f["p_max"] * A_REF)))
    cands.append(("Cat4::H_EL-log2(1/p_max)",
                  lambda f: f["H_EL"] - _safe_log2(_safe_div(1.0, f["p_max"]))))
    cands.append(("Cat4::H2(p_max)",
                  lambda f: _binary_entropy(f["p_max"])))
    cands.append(("Cat4::H_EL/H2(p_max)",
                  lambda f: _safe_div(f["H_EL"], _binary_entropy(f["p_max"]))))
    cands.append(("Cat4::H_EL-H2(p_max)",
                  lambda f: f["H_EL"] - _binary_entropy(f["p_max"])))
    cands.append(("Cat4::H_EL*p_max",
                  lambda f: f["H_EL"] * f["p_max"]))
    cands.append(("Cat4::p_max*log2(28)-H_EL",
                  lambda f: f["p_max"] * LOG2_A - f["H_EL"]))
    cands.append(("Cat4::gzip_efficiency*bigram_distinct_ratio*log2(28)",
                  lambda f: f["gzip_efficiency"] * f["bigram_distinct_ratio"]
                  * LOG2_A))
    cands.append(("Cat4::VL_CV*p_max",
                  lambda f: f["VL_CV"] * f["p_max"]))
    cands.append(("Cat4::VL_CV/H_EL",
                  lambda f: _safe_div(f["VL_CV"], f["H_EL"])))
    cands.append(("Cat4::p_max-(1/log2(28))*H_EL",
                  lambda f: f["p_max"] - (1.0 / LOG2_A) * f["H_EL"]))
    cands.append(("Cat4::H_EL+p_max*log2(28)",
                  lambda f: f["H_EL"] + f["p_max"] * LOG2_A))
    cands.append(("Cat4::p_max*H_EL/(1-p_max)",
                  lambda f: _safe_div(f["p_max"] * f["H_EL"],
                                      1.0 - f["p_max"])))
    cands.append(("Cat4::log2(p_max)+H_EL",
                  lambda f: _safe_log2(f["p_max"]) + f["H_EL"]))
    cands.append(("Cat4::log2(p_max)*H_EL",
                  lambda f: _safe_log2(f["p_max"]) * f["H_EL"]))
    cands.append(("Cat4::sqrt(VL_CV*p_max)",
                  lambda f: _safe_sqrt(f["VL_CV"] * f["p_max"])))
    cands.append(("Cat4::VL_CV*p_max/H_EL",
                  lambda f: _safe_div(f["VL_CV"] * f["p_max"], f["H_EL"])))
    cands.append(("Cat4::gzip_efficiency-bigram_distinct_ratio",
                  lambda f: f["gzip_efficiency"] - f["bigram_distinct_ratio"]))
    cands.append(("Cat4::gzip_efficiency/bigram_distinct_ratio",
                  lambda f: _safe_div(f["gzip_efficiency"],
                                      f["bigram_distinct_ratio"])))

    # Effective alphabet usage candidates
    cands.append(("Cat4::log2(28)*bigram_distinct_ratio",
                  lambda f: LOG2_A * f["bigram_distinct_ratio"]))
    cands.append(("Cat4::log2(28)*gzip_efficiency",
                  lambda f: LOG2_A * f["gzip_efficiency"]))
    cands.append(("Cat4::H_EL*bigram_distinct_ratio",
                  lambda f: f["H_EL"] * f["bigram_distinct_ratio"]))
    cands.append(("Cat4::H_EL*gzip_efficiency",
                  lambda f: f["H_EL"] * f["gzip_efficiency"]))

    return cands


def _make_unary(fname, fn):
    return lambda f: fn(f[fname])


def _make_binary(fi, fj, fn):
    return lambda f: fn(f[fi], f[fj])


def _make_ternary(fi, fj, fk, fn):
    return lambda f: fn(f[fi], f[fj], f[fk])


# ---------------------------------------------------------------------------
# Statistics


def evaluate_candidate(label, fn, per_corpus):
    """Return per-corpus dict + summary stats. NaN-skip if any value is non-finite."""
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
    # F12 fix 2026-04-29: cross-corpus z-score uses unbiased sample variance
    # (ddof=1) over the n=11 non-Quran cluster, matching exp109/exp137/exp138.
    n_o = len(others)
    var_o = (sum((v - mean_o) ** 2 for v in others) / (n_o - 1)) if n_o > 1 else 0.0
    std_o = math.sqrt(var_o)
    if std_o == 0.0:
        return {"label": label, "skipped": True, "reason": "zero_std"}

    cv = std_o / abs(mean_o) if mean_o != 0.0 else float("inf")
    z_quran = (quran_v - mean_o) / std_o

    # Per-corpus z (relative to the same mean / std as Quran z)
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
    """Apply PREREG verdict ladder to a single candidate evaluation."""
    if stats.get("skipped"):
        return "SKIPPED"
    cv = stats["cv_others"]
    az = stats["abs_z_quran"]
    moa = stats["max_other_abs_z"]

    if cv < CV_TIGHT and az >= Z_OUTLIER and moa <= Z_NO_COMPETITOR:
        return "PASS"
    if az >= Z_OUTLIER and (cv >= CV_TIGHT or moa > Z_NO_COMPETITOR):
        return "PARTIAL_OUTLIER_NO_TIGHTNESS"
    if cv < CV_TIGHT and az < Z_OUTLIER:
        return "PARTIAL_TIGHTNESS_NO_OUTLIER"
    if az >= Z_PARTIAL and cv < CV_PARTIAL:
        return "WEAK_DIRECTIONAL"
    return "FAIL"


def aggregate_verdict(per_candidate):
    """Map per-candidate classifications to overall PREREG verdict."""
    cls = [r["classification"] for r in per_candidate if not r.get("skipped")]
    if "PASS" in cls:
        return "PASS_zipf_class_equation_found"
    if "PARTIAL_OUTLIER_NO_TIGHTNESS" in cls and "PARTIAL_TIGHTNESS_NO_OUTLIER" in cls:
        return "PARTIAL_outlier_and_tightness_separately"
    if "PARTIAL_OUTLIER_NO_TIGHTNESS" in cls:
        return "PARTIAL_only_outlier_no_tightness"
    if "PARTIAL_TIGHTNESS_NO_OUTLIER" in cls:
        return "PARTIAL_only_tightness_no_outlier"
    return "FAIL_no_zipf_class_equation"


# ---------------------------------------------------------------------------
# Main


def main():
    t0 = time.time()

    # ---- A1: input SHA-256 -----------------------------------------------
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

    # ---- A2/A3: feature/corpus presence ----------------------------------
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

    per_candidate = []
    for label, fn in candidates:
        stats = evaluate_candidate(label, fn, per_corpus)
        stats["classification"] = classify(stats)
        per_candidate.append(stats)

    n_skipped = sum(1 for r in per_candidate if r.get("skipped"))
    n_evaluated = n_candidates - n_skipped

    overall_verdict = aggregate_verdict(per_candidate)

    # ---- Top-K rankings ---------------------------------------------------
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

    # PASS-quality candidates first; then PARTIAL outliers; then PARTIAL tight.
    pass_cands = [r for r in evaluated if r["classification"] == "PASS"]
    pass_cands.sort(key=lambda r: (-r["abs_z_quran"], r["cv_others"]))

    partial_outlier = [r for r in evaluated
                       if r["classification"] == "PARTIAL_OUTLIER_NO_TIGHTNESS"]
    partial_outlier.sort(key=lambda r: -r["abs_z_quran"])

    partial_tight = [r for r in evaluated
                     if r["classification"] == "PARTIAL_TIGHTNESS_NO_OUTLIER"]
    partial_tight.sort(key=lambda r: r["cv_others"])

    weak = [r for r in evaluated if r["classification"] == "WEAK_DIRECTIONAL"]
    weak.sort(key=lambda r: -r["abs_z_quran"])

    top_pass = [_slim(r) for r in pass_cands[:10]]
    top_z = sorted(evaluated, key=lambda r: -r["abs_z_quran"])[:10]
    top_z = [_slim(r) for r in top_z]
    top_cv = sorted(evaluated, key=lambda r: r["cv_others"])[:10]
    top_cv = [_slim(r) for r in top_cv]
    top_partial_outlier = [_slim(r) for r in partial_outlier[:5]]
    top_partial_tight = [_slim(r) for r in partial_tight[:5]]

    # ---- prereg hash ------------------------------------------------------
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    # ---- audit -----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_input_sha256_match": actual_sha == EXPECTED_INPUT_SHA256,
            "A2_features_match": True,
            "A3_corpora_match": True,
            "A5_n_candidates_le_500": n_candidates <= 500,
            "n_candidates": n_candidates,
            "n_evaluated": n_evaluated,
            "n_skipped": n_skipped,
        },
    }

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H77",
        "hypothesis": (
            "There exists a closed-form g(features) such that "
            "g is approximately constant across the 10 non-Quran corpora "
            "(CV<0.10) AND the Quran is the unique global outlier "
            "(|z|>=5, max other |z|<=2)."
        ),
        "verdict": overall_verdict,
        "verdict_reason": (
            f"{len(pass_cands)} PASS candidate(s); "
            f"{len(partial_outlier)} PARTIAL_OUTLIER; "
            f"{len(partial_tight)} PARTIAL_TIGHT."
        ),
        "prereg_hash": prereg_hash,
        "input_sizing_sha256": actual_sha,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "FEATURE_NAMES": FEATURE_NAMES,
            "CV_TIGHT": CV_TIGHT,
            "Z_OUTLIER": Z_OUTLIER,
            "Z_NO_COMPETITOR": Z_NO_COMPETITOR,
            "CV_PARTIAL": CV_PARTIAL,
            "Z_PARTIAL": Z_PARTIAL,
        },
        "results": {
            "n_candidates_evaluated": n_evaluated,
            "n_skipped": n_skipped,
            "n_pass": len(pass_cands),
            "n_partial_outlier": len(partial_outlier),
            "n_partial_tightness": len(partial_tight),
            "n_weak": len(weak),
            "top_pass": top_pass,
            "top_partial_outlier": top_partial_outlier,
            "top_partial_tightness": top_partial_tight,
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
    print(f"# PASS={len(pass_cands)}  partial_outlier={len(partial_outlier)}  "
          f"partial_tight={len(partial_tight)}  weak={len(weak)}")
    if pass_cands:
        print("\n## PASS candidates (best 5):")
        for r in pass_cands[:5]:
            print(f"  {r['label']:60s} |z|={r['abs_z_quran']:5.2f} "
                  f"CV={r['cv_others']:.4f} max_other|z|={r['max_other_abs_z']:.2f}")
    print("\n## Top 5 by |z_quran|:")
    for r in sorted(evaluated, key=lambda r: -r["abs_z_quran"])[:5]:
        print(f"  {r['label']:60s} |z|={r['abs_z_quran']:5.2f} "
              f"CV={r['cv_others']:.4f} max_other|z|={r['max_other_abs_z']:.2f} "
              f"({r['classification']})")
    print("\n## Top 5 by tightness (lowest CV) -- universal-but-not-Quran-distinct:")
    for r in sorted(evaluated, key=lambda r: r["cv_others"])[:5]:
        print(f"  {r['label']:60s} CV={r['cv_others']:.4f} "
              f"|z|={r['abs_z_quran']:5.2f} ({r['classification']})")
    print(f"\n# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
