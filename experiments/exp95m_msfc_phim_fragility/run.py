"""
exp95m_msfc_phim_fragility — H46 (MSFC sub-gate 2D Quran-amplification).

For each Arabic corpus C in phase_06_phi_m, compute the per-corpus
5-D feature matrix using src.features.features_5d, estimate the
corpus's natural mu/Sinv, then sample 1-letter substitutions of
K_CANON=3 median-length canon units per corpus and measure the
Mahalanobis displacement d_M(canon, edit; Sinv_C) per edit.

phim_fragility(C) := median over canon units of (median over edits of
                     d_M(canon, edit; Sinv_C))

H46 (locked in PREREG.md): Quran has the strictly largest
phim_fragility, by margin > 1.5x over next-ranked corpus.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp95m_msfc_phim_fragility/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95m_msfc_phim_fragility/
      exp95m_msfc_phim_fragility.json (receipt)
      per_corpus_summary.csv (rank, fragility, ...)
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    ARABIC_CONS_28,
    letters_28,
)
from src.features import features_5d, ARABIC_CONN  # noqa: E402

EXP = "exp95m_msfc_phim_fragility"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "8d4e7dbb6d7d7fd8948f560a1f0a5e260d338f35ad4213e3e1c3c633960328c6"
)

# Frozen constants (must match PREREG §4)
EPS_TOP1 = 1.5
K_CANON = 3
N_EDITS = 20
MIN_VERSES_PER_UNIT = 5
RNG_SEED = 95_000
ARABIC_POOL = (
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "ksucca",
    "arabic_bible",
    "hindawi",
)
T2_BANDA_TARGET = 3557.34
T2_BANDA_TOL = 30.0


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _consonant_positions(verse: str) -> list[int]:
    """Indices of characters in `verse` that are 28-alphabet consonants
    or hamza/taa-marbuta-like fold targets (so substitutions act on
    real letters, not diacritics or punctuation)."""
    cons_set = set(ARABIC_CONS_28) | {
        "ء", "أ", "إ", "آ", "ؤ", "ئ", "ة", "ى",
    }
    return [i for i, c in enumerate(verse) if c in cons_set]


def _random_letter_edit(
    verses: list[str], rng: random.Random
) -> list[str] | None:
    """Return a copy of `verses` with one random consonant-position
    substitution. Returns None if no eligible position is found."""
    eligible = [
        (i, _consonant_positions(v)) for i, v in enumerate(verses)
    ]
    eligible = [(i, ps) for i, ps in eligible if ps]
    if not eligible:
        return None
    vi, positions = rng.choice(eligible)
    pos = rng.choice(positions)
    v = verses[vi]
    old = v[pos]
    new = old
    for _ in range(50):
        cand = ARABIC_CONS_28[rng.randrange(28)]
        if cand != old:
            new = cand
            break
    if new == old:
        return None
    out = list(verses)
    out[vi] = v[:pos] + new + v[pos + 1:]
    return out


def main() -> None:
    out_dir = safe_output_dir(EXP)
    t0 = time.time()
    rng = random.Random(RNG_SEED)

    # ---- 1. Lock PREREG hash ----
    actual_hash = _sha256(PREREG_PATH)
    if actual_hash != EXPECTED_PREREG_HASH:
        raise SystemExit(
            f"[{EXP}] PREREG hash drift:\n"
            f"  expected: {EXPECTED_PREREG_HASH}\n"
            f"  actual:   {actual_hash}\n"
            f"REFUSING TO RUN."
        )

    # ---- 2. Load corpora ----
    print(f"[{EXP}] loading corpus phase_06_phi_m...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # ---- 3. Compute per-unit 5-D features for each corpus ----
    print(f"[{EXP}] computing per-unit 5-D features (this is the slow step)...")
    by_corpus_units: dict[str, list[Any]] = {}
    by_corpus_features: dict[str, np.ndarray] = {}
    by_corpus_labels: dict[str, list[str]] = {}
    by_corpus_letter_counts: dict[str, list[int]] = {}

    feat_t0 = time.time()
    for cname in ARABIC_POOL:
        items = CORPORA.get(cname, [])
        units: list[Any] = []
        feats: list[np.ndarray] = []
        labels: list[str] = []
        letter_counts: list[int] = []
        for u in items:
            verses = list(u.verses)
            if len(verses) < MIN_VERSES_PER_UNIT:
                continue
            try:
                f = features_5d(verses, ARABIC_CONN)
            except Exception as e:
                print(f"[{EXP}]   skip {getattr(u, 'label', '?')}: {e}")
                continue
            units.append(u)
            feats.append(f)
            labels.append(getattr(u, "label", f"{cname}:?"))
            letter_counts.append(len(letters_28(" ".join(verses))))
        by_corpus_units[cname] = units
        by_corpus_features[cname] = np.array(feats, dtype=float)
        by_corpus_labels[cname] = labels
        by_corpus_letter_counts[cname] = letter_counts
        print(
            f"[{EXP}]   {cname}: {len(units)} units, "
            f"feature matrix {by_corpus_features[cname].shape}, "
            f"elapsed {time.time() - feat_t0:.1f}s"
        )

    # ---- 4. Audit: reproduce band-A T2 ----
    # Band-A = Quran surahs with 15..100 verses vs Arabic controls (paper §2.2)
    print(f"[{EXP}] audit: reproducing band-A T2 vs Arabic controls...")
    quran_units = by_corpus_units.get("quran", [])
    band_a_idx = [
        i for i, u in enumerate(quran_units)
        if 15 <= len(list(u.verses)) <= 100
    ]
    X_q_banda = by_corpus_features["quran"][band_a_idx]
    ctrl_blocks = []
    for c in ARABIC_POOL:
        if c == "quran":
            continue
        ctrl_blocks.append(by_corpus_features[c])
    X_ctrl = np.vstack(ctrl_blocks) if ctrl_blocks else np.zeros((0, 5))
    nq, p_dim = X_q_banda.shape
    nc = X_ctrl.shape[0]
    if nq < 2 or nc < 2:
        raise SystemExit(f"[{EXP}] insufficient samples for T2 audit")
    mu_q = X_q_banda.mean(axis=0)
    mu_c = X_ctrl.mean(axis=0)
    Sq = np.cov(X_q_banda, rowvar=False, ddof=1)
    Sc = np.cov(X_ctrl, rowvar=False, ddof=1)
    Spool = ((nq - 1) * Sq + (nc - 1) * Sc) / max(nq + nc - 2, 1)
    Sinv_pool = np.linalg.pinv(Spool)
    diff = mu_q - mu_c
    t2_banda = float((nq * nc / (nq + nc)) * (diff @ Sinv_pool @ diff))
    audit_t2_drift = abs(t2_banda - T2_BANDA_TARGET) > T2_BANDA_TOL
    print(
        f"[{EXP}]   band-A T2 = {t2_banda:.2f} "
        f"(target {T2_BANDA_TARGET} +/- {T2_BANDA_TOL}, "
        f"drift = {audit_t2_drift})"
    )

    # ---- 5. Per-corpus mu_C, Sinv_C, canon-pick, edit sampling ----
    print(f"[{EXP}] sampling edits and computing Mahalanobis displacements...")
    per_corpus: dict[str, dict[str, Any]] = {}
    for cname in ARABIC_POOL:
        X = by_corpus_features[cname]
        units = by_corpus_units[cname]
        labels = by_corpus_labels[cname]
        letter_counts = by_corpus_letter_counts[cname]
        n_units = X.shape[0]
        if n_units < K_CANON:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_fragility": None,
                "_excluded_lt_k_canon": True,
            }
            continue

        # Per-corpus mu and Sinv (pooled within-corpus covariance)
        mu = X.mean(axis=0)
        S = np.cov(X, rowvar=False, ddof=1)
        try:
            Sinv = np.linalg.pinv(S)
        except Exception as e:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_fragility": None,
                "_excluded_singular_cov": str(e),
            }
            continue

        # Pick canon units: those at the median letter-count rank
        order = np.argsort(letter_counts)
        median_idx = len(order) // 2
        # Pick K_CANON indices around median
        half = K_CANON // 2
        lo = max(0, median_idx - half)
        hi = lo + K_CANON
        if hi > len(order):
            hi = len(order)
            lo = max(0, hi - K_CANON)
        canon_indices = [int(order[k]) for k in range(lo, hi)]

        per_canon: list[dict[str, Any]] = []
        unit_d_medians: list[float] = []
        for ci in canon_indices:
            u = units[ci]
            label = labels[ci]
            verses = list(u.verses)
            phi_canon = X[ci]

            edit_dists: list[float] = []
            for _ in range(N_EDITS):
                edited = _random_letter_edit(verses, rng)
                if edited is None:
                    continue
                try:
                    phi_edit = features_5d(edited, ARABIC_CONN)
                except Exception:
                    continue
                d = phi_canon - phi_edit
                d_M = float(np.sqrt(d @ Sinv @ d))
                if not np.isfinite(d_M):
                    continue
                edit_dists.append(d_M)

            if edit_dists:
                med = float(np.median(edit_dists))
                unit_d_medians.append(med)
                per_canon.append({
                    "label": label,
                    "letter_count": int(letter_counts[ci]),
                    "n_edits_kept": len(edit_dists),
                    "median_d_M": med,
                    "min_d_M": float(min(edit_dists)),
                    "max_d_M": float(max(edit_dists)),
                })

        if not unit_d_medians:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_fragility": None,
                "_excluded_no_finite_edits": True,
                "per_canon": per_canon,
            }
            continue

        per_corpus[cname] = {
            "n_units": n_units,
            "K_canon_used": len(per_canon),
            "phim_fragility": float(np.median(unit_d_medians)),
            "phim_fragility_min_unit": float(min(unit_d_medians)),
            "phim_fragility_max_unit": float(max(unit_d_medians)),
            "per_canon": per_canon,
            "mu_C": [float(x) for x in mu],
            "cov_C_diag": [float(x) for x in np.diag(S)],
        }
        print(
            f"[{EXP}]   {cname}: phim_fragility = "
            f"{per_corpus[cname]['phim_fragility']:.4f} "
            f"(min={per_corpus[cname]['phim_fragility_min_unit']:.4f}, "
            f"max={per_corpus[cname]['phim_fragility_max_unit']:.4f})"
        )

    # ---- 6. Verdict ladder ----
    eligible: list[tuple[str, float]] = []
    for cname, summary in per_corpus.items():
        if summary.get("phim_fragility") is None:
            continue
        eligible.append((cname, summary["phim_fragility"]))
    eligible.sort(key=lambda x: -x[1])

    verdict = "UNDETERMINED"
    quran_rank = None
    quran_frag = None
    next_corpus = None
    next_frag = None
    margin_ratio = None

    if audit_t2_drift:
        verdict = "FAIL_audit_features_drift"
    else:
        for ix, (cname, fr) in enumerate(eligible):
            if cname == "quran":
                quran_rank = ix + 1
                quran_frag = fr
                if ix + 1 < len(eligible):
                    next_corpus = eligible[ix + 1][0]
                    next_frag = eligible[ix + 1][1]
                break
        if quran_rank is None:
            verdict = "FAIL_quran_not_eligible"
        elif quran_rank != 1:
            verdict = "FAIL_quran_not_top_1"
        else:
            if next_frag is None or next_frag <= 0:
                margin_ratio = float("inf")
                verdict = "PASS_quran_strict_max"
            else:
                margin_ratio = quran_frag / next_frag
                if margin_ratio > EPS_TOP1:
                    verdict = "PASS_quran_strict_max"
                else:
                    verdict = "PARTIAL_quran_top_1_within_eps"

    # ---- 7. Receipt ----
    elapsed = time.time() - t0
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H46",
        "verdict": verdict,
        "prereg_hash_expected": EXPECTED_PREREG_HASH,
        "prereg_hash_actual": actual_hash,
        "frozen_constants": {
            "EPS_TOP1": EPS_TOP1,
            "K_CANON": K_CANON,
            "N_EDITS": N_EDITS,
            "MIN_VERSES_PER_UNIT": MIN_VERSES_PER_UNIT,
            "RNG_SEED": RNG_SEED,
            "ARABIC_POOL": list(ARABIC_POOL),
            "T2_BANDA_TARGET": T2_BANDA_TARGET,
            "T2_BANDA_TOL": T2_BANDA_TOL,
        },
        "audit": {
            "t2_banda_value": t2_banda,
            "t2_banda_target": T2_BANDA_TARGET,
            "t2_banda_tol": T2_BANDA_TOL,
            "t2_banda_drift": bool(audit_t2_drift),
            "n_band_a_units": int(nq),
            "n_ctrl_units": int(nc),
        },
        "per_corpus": per_corpus,
        "ranking": [
            {"rank": ix + 1, "corpus": cname, "phim_fragility": fr}
            for ix, (cname, fr) in enumerate(eligible)
        ],
        "quran_rank": quran_rank,
        "quran_phim_fragility": quran_frag,
        "next_corpus": next_corpus,
        "next_phim_fragility": next_frag,
        "margin_ratio_quran_over_next": margin_ratio,
        "wall_time_s": round(elapsed, 2),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    receipt_path = out_dir / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    csv_path = out_dir / "per_corpus_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "rank", "corpus", "n_units", "K_canon_used",
            "phim_fragility", "min_unit", "max_unit",
        ])
        for ix, (cname, fr) in enumerate(eligible):
            row = per_corpus[cname]
            w.writerow([
                ix + 1, cname, row["n_units"],
                row.get("K_canon_used", ""),
                row["phim_fragility"],
                row.get("phim_fragility_min_unit", ""),
                row.get("phim_fragility_max_unit", ""),
            ])
        for cname, summary in per_corpus.items():
            if summary.get("phim_fragility") is None:
                w.writerow([
                    "excl", cname, summary.get("n_units", 0), "",
                    "", "", "",
                ])

    print(f"\n[{EXP}] verdict: {verdict}")
    if quran_rank is not None:
        print(
            f"[{EXP}] quran rank = {quran_rank}, "
            f"phim_fragility = {quran_frag:.4f}"
        )
        if next_corpus is not None:
            print(
                f"[{EXP}] next corpus = {next_corpus}, "
                f"phim_fragility = {next_frag:.4f}, "
                f"margin ratio = {margin_ratio:.3f}"
            )
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] csv:     {csv_path}")
    print(f"[{EXP}] elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
