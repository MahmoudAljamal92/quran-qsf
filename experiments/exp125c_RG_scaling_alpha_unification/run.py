"""experiments/exp125c_RG_scaling_alpha_unification/run.py — RG-scaling cross-tradition.

Extends F68 (`exp116_RG_scaling_collapse`) from 6 Arabic peers to the full 11-corpus
V3.14 pool (5 cross-tradition + 6 Arabic). For each (corpus, feature) pair, fits the
RG-scaling exponent α via log-log regression on coarse-grained verse-blocks at scales
L ∈ {1, 2, 4, 8, 16}. Then runs LDA on the per-corpus 4-vector of α values to test
whether a unified Quran-distinctive scaling-exponent coordinate exists.

Mirrors exp125b's LDA + LOO procedure.

PREREG: experiments/exp125c_RG_scaling_alpha_unification/PREREG.md
Output: results/experiments/exp125c_RG_scaling_alpha_unification/exp125c_RG_scaling_alpha_unification.json
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EXP_NAME = "exp125c_RG_scaling_alpha_unification"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# Pre-registered constants
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
SCALES = [1, 2, 4, 8, 16]
MIN_VERSES_FOR_RG = 32  # ≥ 2 super-verses at L=16
RG_FEATURES = ["EL_rate", "p_max", "H_EL", "VL_CV"]

# LDA acceptance thresholds (mirrors exp125b)
Z_QURAN_OUTLIER = 5.0
Z_NO_COMPETITOR = 2.0
FISHER_J_FLOOR = 5.0
LOO_MIN_Z_QURAN = 4.0
LOO_MAX_OTHER_ABS_Z = 2.5
RIDGE_EPS = 1e-6
PARTIAL_Z_FLOOR = 3.0


def features_at_scale(verses, normaliser_fn, L):
    """Compute (EL_rate, p_max, H_EL, VL_CV) on L-coarse-grained super-verses.

    Returns dict or None if fewer than 2 super-verses are formed.
    """
    n = len(verses)
    n_groups = n // L
    if n_groups < 2:
        return None
    super_verses = []
    for i in range(n_groups):
        block = verses[i * L:(i + 1) * L]
        super_verses.append(" ".join(block))

    # Terminal letter of each super-verse
    finals = []
    for sv in super_verses:
        norm = normaliser_fn(sv)
        if norm:
            finals.append(norm[-1])

    if not finals:
        return None
    counter = Counter(finals)
    total = sum(counter.values())
    top_letter, top_count = counter.most_common(1)[0]
    el_rate = top_count / total
    p_max = el_rate
    h_el = -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)

    # VL_CV on super-verse character lengths (using normalised skeleton length)
    lengths = [len(normaliser_fn(sv)) for sv in super_verses]
    if len(lengths) < 2:
        return None
    mean_len = float(np.mean(lengths))
    if mean_len <= 0:
        return None
    std_len = float(np.std(lengths, ddof=1))
    vl_cv = std_len / mean_len

    return {
        "EL_rate": el_rate,
        "p_max": p_max,
        "H_EL": h_el,
        "VL_CV": vl_cv,
    }


def fit_loglog_slope(L_values, median_values):
    """Least-squares slope of log(median) vs log(L). Returns (alpha, r_squared)."""
    L_arr = np.array(L_values, dtype=float)
    m_arr = np.array(median_values, dtype=float)
    valid = (m_arr > 0) & np.isfinite(m_arr)
    if valid.sum() < 3:
        return float("nan"), 0.0
    x = np.log(L_arr[valid])
    y = np.log(m_arr[valid])
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_sq = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return float(slope), float(r_sq)


def load_all_corpora():
    """Load 11 cross-tradition corpora via the existing universal sizing harness."""
    from scripts._phi_universal_xtrad_sizing import (
        _load_quran, _load_arabic_peers, _load_hebrew_tanakh,
        _load_greek_nt, _load_pali, _load_avestan, NORMALISERS,
    )
    corpora = {}
    print("# Loading 11 corpora...", flush=True)
    t = time.time()
    corpora["quran"] = _load_quran()
    print(f"#   quran: {len(corpora['quran'])} surahs ({time.time()-t:.1f}s)", flush=True)

    t = time.time()
    arabic_peers = _load_arabic_peers()
    for name, units in arabic_peers.items():
        corpora[name] = units
    print(f"#   arabic peers: {sum(len(v) for v in arabic_peers.values())} units ({time.time()-t:.1f}s)", flush=True)

    t = time.time()
    corpora["hebrew_tanakh"] = _load_hebrew_tanakh()
    print(f"#   hebrew_tanakh: {len(corpora['hebrew_tanakh'])} chapters ({time.time()-t:.1f}s)", flush=True)

    t = time.time()
    corpora["greek_nt"] = _load_greek_nt()
    print(f"#   greek_nt: {len(corpora['greek_nt'])} chapters ({time.time()-t:.1f}s)", flush=True)

    t = time.time()
    corpora["pali"] = _load_pali()
    print(f"#   pali: {len(corpora['pali'])} suttas ({time.time()-t:.1f}s)", flush=True)

    t = time.time()
    corpora["avestan_yasna"] = _load_avestan()
    print(f"#   avestan_yasna: {len(corpora['avestan_yasna'])} chapters ({time.time()-t:.1f}s)", flush=True)

    return corpora, NORMALISERS


def fit_lda(Z_rows, quran_idx_in_rows):
    """Fisher LDA between Quran (1 sample) vs rest (N-1 samples).
    Mirrors exp125b's fit_lda exactly.
    """
    Z_q = Z_rows[quran_idx_in_rows:quran_idx_in_rows + 1, :]
    Z_r = np.delete(Z_rows, quran_idx_in_rows, axis=0)
    mu_Q = Z_q.mean(axis=0)
    mu_R = Z_r.mean(axis=0)
    diff = mu_Q - mu_R
    centred_R = Z_r - mu_R
    S_W = centred_R.T @ centred_R
    S_W_reg = S_W + RIDGE_EPS * np.eye(S_W.shape[0])
    w = np.linalg.solve(S_W_reg, diff)
    w_norm = np.linalg.norm(w)
    if w_norm == 0:
        return None, 0.0
    w_unit = w / w_norm
    if w_unit @ Z_q[0] < 0:
        w_unit = -w_unit
    num = (w_unit @ diff) ** 2
    den = w_unit @ S_W @ w_unit
    J = num / den if den > 0 else 0.0
    return w_unit, float(J)


def project_and_score(Z_rows, w, corpus_names, quran_idx):
    scores = Z_rows @ w
    score_per_corpus = {c: float(scores[i]) for i, c in enumerate(corpus_names)}
    quran_score = score_per_corpus[corpus_names[quran_idx]]
    non_quran = [v for c, v in score_per_corpus.items() if c != corpus_names[quran_idx]]
    mean_nq = float(np.mean(non_quran))
    std_nq = float(np.std(non_quran, ddof=0))
    z_quran = (quran_score - mean_nq) / std_nq if std_nq > 0 else 0.0
    z_per_corpus = {c: (v - mean_nq) / std_nq if std_nq > 0 else 0.0
                    for c, v in score_per_corpus.items()}
    max_other_abs_z = max(abs(z_per_corpus[c])
                          for c in corpus_names
                          if c != corpus_names[quran_idx])
    return score_per_corpus, quran_score, z_quran, max_other_abs_z, z_per_corpus


def _format_formula(loading, feature_names):
    parts = []
    for i, fn in enumerate(feature_names):
        coef = loading[i]
        sign = "+" if coef >= 0 else "-"
        if i == 0:
            parts.append(f"{coef:+.4f} * z_alpha_{fn}")
        else:
            parts.append(f"{sign} {abs(coef):.4f} * z_alpha_{fn}")
    return "alpha_LDA_RG(c) = " + " ".join(parts)


def main():
    t0 = time.time()
    print(f"# {EXP_NAME}", flush=True)

    # ---- Load all 11 corpora ----------------------------------------------
    corpora, NORMALISERS = load_all_corpora()
    print(f"# Total load time: {time.time() - t0:.1f}s", flush=True)

    # ---- Verify all 11 expected corpora present ---------------------------
    for c in EXPECTED_CORPORA:
        if c not in corpora:
            receipt = {
                "experiment": EXP_NAME,
                "verdict": "FAIL_audit_missing_corpus",
                "missing": c,
            }
            OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            print(f"FAIL_audit_missing_corpus: {c}")
            return

    # ---- Stage A + B: per-(corpus, scale, feature) median across qualifying chapters
    print("# Computing RG-scaling features at L ∈ {1,2,4,8,16}...", flush=True)
    t = time.time()
    per_corpus_per_scale = {}  # {corpus: {L: {feature: median over chapters}}}
    n_qualifying = {}  # {corpus: int}

    for c in EXPECTED_CORPORA:
        units = corpora[c]
        # Filter chapters with ≥ MIN_VERSES_FOR_RG verses
        qualifying = [u for u in units if len(u["verses"]) >= MIN_VERSES_FOR_RG]
        n_qualifying[c] = len(qualifying)

        per_scale = {}
        for L in SCALES:
            feature_lists = {f: [] for f in RG_FEATURES}
            for u in qualifying:
                norm_fn = NORMALISERS[u["normaliser"]]
                feats = features_at_scale(u["verses"], norm_fn, L)
                if feats is None:
                    continue
                for f in RG_FEATURES:
                    feature_lists[f].append(feats[f])
            per_scale[L] = {
                f: float(np.median(feature_lists[f])) if feature_lists[f] else float("nan")
                for f in RG_FEATURES
            }
        per_corpus_per_scale[c] = per_scale
    print(f"# RG-scaling computed in {time.time() - t:.1f}s", flush=True)

    # ---- Stage C: fit α(c, feature) ---------------------------------------
    print("# Fitting power-law slopes (4 features × 11 corpora = 44 fits)...", flush=True)
    alpha_matrix = {}  # {corpus: {feature: alpha}}
    r2_matrix = {}     # {corpus: {feature: r2}}

    for c in EXPECTED_CORPORA:
        alpha_matrix[c] = {}
        r2_matrix[c] = {}
        for f in RG_FEATURES:
            medians = [per_corpus_per_scale[c][L][f] for L in SCALES]
            alpha, r2 = fit_loglog_slope(SCALES, medians)
            alpha_matrix[c][f] = alpha
            r2_matrix[c][f] = r2

    # ---- A2/A3: validity check --------------------------------------------
    invalid_corpora = []
    low_r2_corpora = []
    for c in EXPECTED_CORPORA:
        if any(math.isnan(alpha_matrix[c][f]) for f in RG_FEATURES):
            invalid_corpora.append(c)
        # A3 fit-quality: r² > 0.5 on at least 3 of 4 features
        n_good_r2 = sum(1 for f in RG_FEATURES if r2_matrix[c][f] > 0.5)
        if n_good_r2 < 3:
            low_r2_corpora.append((c, n_good_r2))

    if invalid_corpora:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_alpha_nan",
            "invalid_corpora": invalid_corpora,
            "n_qualifying_per_corpus": n_qualifying,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"FAIL_audit_alpha_nan: {invalid_corpora}")
        return

    # ---- Stage D: build α matrix and run LDA -----------------------------
    print("# Running LDA on α-vectors...", flush=True)
    X_alpha = np.array([
        [alpha_matrix[c][f] for f in RG_FEATURES]
        for c in EXPECTED_CORPORA
    ], dtype=np.float64)  # 11 × 4

    # Standardise per feature
    mu_alpha = X_alpha.mean(axis=0)
    sigma_alpha = X_alpha.std(axis=0, ddof=0)
    sigma_alpha_safe = np.where(sigma_alpha > 0, sigma_alpha, 1.0)
    Z_alpha = (X_alpha - mu_alpha) / sigma_alpha_safe

    quran_idx = EXPECTED_CORPORA.index("quran")
    w_lda, J_full = fit_lda(Z_alpha, quran_idx)

    if w_lda is None:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_lda_singular",
            "alpha_matrix": alpha_matrix,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print("FAIL_audit_lda_singular")
        return

    score_per_corpus, quran_score, z_quran, max_other_abs_z, z_per_corpus = project_and_score(
        Z_alpha, w_lda, EXPECTED_CORPORA, quran_idx
    )

    # ---- Stage E: LOO robustness -----------------------------------------
    print("# LOO robustness (10 iterations)...", flush=True)
    loo_results = []
    loo_min_z_q = float("inf")
    loo_max_other = 0.0

    for held_out_idx, held_out_corpus in enumerate(EXPECTED_CORPORA):
        if held_out_corpus == "quran":
            continue
        keep_idx = [i for i in range(len(EXPECTED_CORPORA)) if i != held_out_idx]
        Z_kept = Z_alpha[keep_idx, :]
        kept_corpora = [EXPECTED_CORPORA[i] for i in keep_idx]
        new_quran_idx = kept_corpora.index("quran")

        w_loo, J_loo = fit_lda(Z_kept, new_quran_idx)
        if w_loo is None:
            continue

        full_scores = Z_alpha @ w_loo
        non_quran_full = [float(full_scores[i]) for i, c in enumerate(EXPECTED_CORPORA) if c != "quran"]
        mean_nq_loo = float(np.mean(non_quran_full))
        std_nq_loo = float(np.std(non_quran_full, ddof=0))
        if std_nq_loo == 0:
            continue
        z_quran_loo = (float(full_scores[quran_idx]) - mean_nq_loo) / std_nq_loo
        z_per_loo = {c: (float(full_scores[i]) - mean_nq_loo) / std_nq_loo
                     for i, c in enumerate(EXPECTED_CORPORA)}
        max_other_abs_z_loo = max(abs(z_per_loo[c]) for c in EXPECTED_CORPORA if c != "quran")

        loo_results.append({
            "held_out": held_out_corpus,
            "z_quran_lda_loo": z_quran_loo,
            "abs_z_quran_lda_loo": abs(z_quran_loo),
            "max_other_abs_z_loo": max_other_abs_z_loo,
            "fisher_ratio_J_loo": J_loo,
        })
        loo_min_z_q = min(loo_min_z_q, abs(z_quran_loo))
        loo_max_other = max(loo_max_other, max_other_abs_z_loo)

    # LOO verdict
    if loo_min_z_q >= LOO_MIN_Z_QURAN and loo_max_other <= LOO_MAX_OTHER_ABS_Z:
        loo_verdict = "PASS_alpha_lda_robust_loo"
    else:
        loo_verdict = "FAIL_alpha_lda_loo_overfit"

    # ---- Aggregate verdict (mirrors exp125b style) ------------------------
    abs_z_q = abs(z_quran)
    if (abs_z_q >= Z_QURAN_OUTLIER
            and max_other_abs_z <= Z_NO_COMPETITOR
            and J_full >= FISHER_J_FLOOR):
        full_verdict = "PASS_alpha_lda_strong_unified"
    elif abs_z_q >= PARTIAL_Z_FLOOR and max_other_abs_z <= Z_NO_COMPETITOR:
        full_verdict = "PARTIAL_alpha_lda_directional"
    else:
        full_verdict = "FAIL_no_alpha_unification"

    if full_verdict == "PASS_alpha_lda_strong_unified" and loo_verdict == "PASS_alpha_lda_robust_loo":
        overall = "PASS_alpha_lda_strong_AND_LOO_ROBUST"
    elif full_verdict == "PASS_alpha_lda_strong_unified":
        overall = "PARTIAL_alpha_lda_strong_BUT_LOO_NOT_ROBUST"
    else:
        overall = full_verdict

    # ---- Receipt ----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_n_qualifying_per_corpus": n_qualifying,
            "A2_no_nan_alpha": len(invalid_corpora) == 0,
            "A3_low_r2_corpora": [{"corpus": c, "n_good_r2": n} for c, n in low_r2_corpora],
            "A4_S_W_nonsingular": w_lda is not None,
            "A5_deterministic": True,
        },
    }
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    unified_formula = _format_formula(w_lda.tolist(), RG_FEATURES)

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H83",
        "hypothesis": (
            "The per-corpus 4-vector of RG-scaling exponents alpha(c) gives a "
            "unified Quran-distinctive single linear coordinate alpha_LDA_RG(c) "
            "across the 11-corpus pool, with full-pool Quran |z|>=5 AND LOO "
            "robust at min |z|_LOO>=4."
        ),
        "verdict": overall,
        "verdict_full_pool": full_verdict,
        "verdict_loo_robustness": loo_verdict,
        "verdict_reason": (
            f"Full-pool: |z_quran|={abs_z_q:.2f}, "
            f"max_other|z|={max_other_abs_z:.2f}, J={J_full:.2f}. "
            f"LOO: min |z_quran|={loo_min_z_q:.2f}, "
            f"max max_other|z|={loo_max_other:.2f}."
        ),
        "prereg_hash": prereg_hash,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "SCALES": SCALES,
            "MIN_VERSES_FOR_RG": MIN_VERSES_FOR_RG,
            "RG_FEATURES": RG_FEATURES,
            "Z_QURAN_OUTLIER": Z_QURAN_OUTLIER,
            "Z_NO_COMPETITOR": Z_NO_COMPETITOR,
            "FISHER_J_FLOOR": FISHER_J_FLOOR,
            "LOO_MIN_Z_QURAN": LOO_MIN_Z_QURAN,
            "LOO_MAX_OTHER_ABS_Z": LOO_MAX_OTHER_ABS_Z,
            "RIDGE_EPS": RIDGE_EPS,
            "PARTIAL_Z_FLOOR": PARTIAL_Z_FLOOR,
        },
        "results": {
            "n_qualifying_chapters": n_qualifying,
            "per_corpus_per_scale_medians": per_corpus_per_scale,
            "alpha_matrix": alpha_matrix,
            "alpha_r2_matrix": r2_matrix,
            "alpha_LDA_loading": dict(zip(RG_FEATURES, w_lda.tolist())),
            "alpha_LDA_score_per_corpus": score_per_corpus,
            "z_quran_alpha_LDA": z_quran,
            "abs_z_quran_alpha_LDA": abs_z_q,
            "max_other_abs_z_alpha_LDA": max_other_abs_z,
            "z_per_corpus_alpha_LDA": z_per_corpus,
            "fisher_ratio_J_alpha_full": J_full,
            "unified_formula_string": unified_formula,
            "loo_results": loo_results,
            "loo_min_abs_z_quran": loo_min_z_q,
            "loo_max_other_abs_z": loo_max_other,
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 4),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ---- Console summary -------------------------------------------------
    print()
    print(f"# verdict (overall): {overall}")
    print(f"# verdict (full-pool): {full_verdict}")
    print(f"# verdict (LOO): {loo_verdict}")
    print()
    print("## n_qualifying_chapters per corpus:")
    for c in EXPECTED_CORPORA:
        print(f"  {c:20s}  {n_qualifying[c]:5d}")
    print()
    print(f"## Unified formula (α-LDA on RG-scaling exponents):")
    print(f"  {unified_formula}")
    print()
    print(f"## α-LDA scores per corpus (sorted ascending):")
    sorted_corpora = sorted(score_per_corpus.items(), key=lambda kv: kv[1])
    for c, v in sorted_corpora:
        z = z_per_corpus[c]
        flag = "  <-- QURAN" if c == "quran" else ""
        print(f"  {c:20s}  alpha_LDA={v:+8.4f}  z={z:+8.2f}{flag}")
    print()
    print(f"# Quran |z|: {abs_z_q:.4f}  max_other|z|: {max_other_abs_z:.4f}  J: {J_full:.4f}")
    print()
    print(f"## LOO ({len(loo_results)} iterations):")
    for r in loo_results:
        print(f"  drop={r['held_out']:20s} |z_quran|_LOO={r['abs_z_quran_lda_loo']:6.2f} "
              f"max_other|z|={r['max_other_abs_z_loo']:5.2f}")
    print(f"# LOO min |z_quran|: {loo_min_z_q:.4f}  max max_other|z|: {loo_max_other:.4f}")
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
