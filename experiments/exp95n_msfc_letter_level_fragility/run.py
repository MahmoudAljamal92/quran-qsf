"""
exp95n_msfc_letter_level_fragility — H47 (MSFC sub-gate 2D Quran-amplification
under letter-level features).

For each Arabic corpus C, compute the per-unit letter-level 5-D feature
vector Ψ_L = [H_2, H_3, Gini, gzip_ratio, log10_n_distinct_bigrams]
on the unit's letters_28 skeleton. Estimate per-corpus mu_C and Sinv_C.
Sample K_CANON=3 median-length canon units; for each canon unit,
generate N_EDITS=20 random consonant substitutions at ANY position
(interior-permitting), recompute Ψ_L, and measure
d_M(canon, edit; Sinv_C). Per-corpus median d_M = phim_lvl_fragility.

H47 (locked in PREREG.md): Quran has the strictly largest
phim_lvl_fragility, by margin > 1.5x over next-ranked corpus.

Reads:
  - phase_06_phi_m.pkl
  - experiments/exp95n_msfc_letter_level_fragility/PREREG.md (hash-lock)
Writes:
  - results/experiments/exp95n_msfc_letter_level_fragility/
      exp95n_msfc_letter_level_fragility.json (receipt)
      per_corpus_summary.csv (rank, fragility, ...)
"""
from __future__ import annotations

import csv
import gzip as gz
import hashlib
import json
import math
import random
import sys
import time
from collections import Counter
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

EXP = "exp95n_msfc_letter_level_fragility"
PREREG_PATH = _HERE / "PREREG.md"
EXPECTED_PREREG_HASH = (
    "3d5cfcc94d215c3fc992647108a025de6550df8e86ffa60085fdf4c702ed8eaf"
)

# Frozen constants (must match PREREG §4)
EPS_TOP1 = 1.5
K_CANON = 3
N_EDITS = 20
MIN_VERSES_PER_UNIT = 2
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
SMALLEST_EIG_FLOOR = 1e-12
ZERO_DM_FRAC_CEIL = 0.5
GZIP_LEVEL = 9


def _sha256(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _consonant_positions(verse: str) -> list[int]:
    cons_set = set(ARABIC_CONS_28) | {
        "ء", "أ", "إ", "آ", "ؤ", "ئ", "ة", "ى",
    }
    return [i for i, c in enumerate(verse) if c in cons_set]


def _h2(s: str) -> float:
    """Shannon entropy (bits) of bigram distribution over s."""
    if len(s) < 2:
        return 0.0
    bigs = Counter(s[i:i + 2] for i in range(len(s) - 1))
    n = sum(bigs.values())
    if n == 0:
        return 0.0
    h = 0.0
    for c in bigs.values():
        p = c / n
        if p > 0:
            h -= p * math.log2(p)
    return h


def _h3(s: str) -> float:
    """Shannon entropy of trigram distribution over s."""
    if len(s) < 3:
        return 0.0
    trigs = Counter(s[i:i + 3] for i in range(len(s) - 2))
    n = sum(trigs.values())
    if n == 0:
        return 0.0
    h = 0.0
    for c in trigs.values():
        p = c / n
        if p > 0:
            h -= p * math.log2(p)
    return h


def _gini(s: str) -> float:
    """Gini coefficient of unigram letter-frequency distribution.
    0 = perfectly uniform, 1 = single-letter dominance."""
    if not s:
        return 0.0
    cnt = Counter(s)
    counts = sorted(cnt.values())
    n = len(counts)
    if n == 0:
        return 0.0
    s_total = sum(counts)
    if s_total == 0:
        return 0.0
    cum = 0.0
    for i, c in enumerate(counts, start=1):
        cum += i * c
    return (2.0 * cum) / (n * s_total) - (n + 1.0) / n


def _gzip_ratio(s: str) -> float:
    """|gzip(s)| / |s| for s as UTF-8 bytes."""
    if not s:
        return 0.0
    raw = s.encode("utf-8")
    if len(raw) == 0:
        return 0.0
    comp = gz.compress(raw, compresslevel=GZIP_LEVEL)
    return len(comp) / len(raw)


def _log10_n_distinct_bigrams(s: str) -> float:
    if len(s) < 2:
        return 0.0
    bigs = set(s[i:i + 2] for i in range(len(s) - 1))
    n = len(bigs)
    return math.log10(n) if n > 0 else 0.0


def features_letter(s: str) -> np.ndarray:
    """5-D letter-level feature vector. Inputs the 28-letter skeleton
    string and returns [H_2, H_3, Gini, gzip_ratio,
    log10(n_distinct_bigrams)]."""
    return np.array([
        _h2(s),
        _h3(s),
        _gini(s),
        _gzip_ratio(s),
        _log10_n_distinct_bigrams(s),
    ], dtype=float)


def _random_letter_edit(
    verses: list[str], rng: random.Random
) -> list[str] | None:
    """Return a copy of `verses` with one random consonant-position
    substitution at any verse position."""
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

    # ---- 3. Compute per-unit letter-level 5-D features ----
    print(f"[{EXP}] computing letter-level 5-D features per unit...")
    by_corpus_units: dict[str, list[Any]] = {}
    by_corpus_features: dict[str, np.ndarray] = {}
    by_corpus_labels: dict[str, list[str]] = {}
    by_corpus_letter_counts: dict[str, list[int]] = {}

    feat_t0 = time.time()
    audit_non_finite = []
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
                s = letters_28(" ".join(verses))
            except Exception:
                continue
            if len(s) < 2:
                continue
            try:
                f = features_letter(s)
            except Exception as e:
                print(f"[{EXP}]   skip {getattr(u, 'label', '?')}: {e}")
                continue
            if not np.all(np.isfinite(f)):
                audit_non_finite.append({
                    "corpus": cname,
                    "label": getattr(u, "label", "?"),
                    "feature": [float(x) for x in f],
                })
                continue
            units.append(u)
            feats.append(f)
            labels.append(getattr(u, "label", f"{cname}:?"))
            letter_counts.append(len(s))
        by_corpus_units[cname] = units
        by_corpus_features[cname] = np.array(feats, dtype=float)
        by_corpus_labels[cname] = labels
        by_corpus_letter_counts[cname] = letter_counts
        print(
            f"[{EXP}]   {cname}: {len(units)} units, "
            f"feature matrix {by_corpus_features[cname].shape}, "
            f"elapsed {time.time() - feat_t0:.1f}s"
        )

    # ---- 4. Per-corpus mu, Sinv, canon-pick, edit sampling ----
    print(f"[{EXP}] computing per-corpus mu/Sinv and edit displacements...")
    per_corpus: dict[str, dict[str, Any]] = {}
    audit_singular_cov = []
    audit_zero_dm_fraction = []
    audit_dm_non_finite = []

    for cname in ARABIC_POOL:
        X = by_corpus_features[cname]
        units = by_corpus_units[cname]
        labels = by_corpus_labels[cname]
        letter_counts = by_corpus_letter_counts[cname]
        n_units = X.shape[0]
        if n_units < K_CANON:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_lvl_fragility": None,
                "_excluded_lt_k_canon": True,
            }
            continue

        mu = X.mean(axis=0)
        S = np.cov(X, rowvar=False, ddof=1)
        eigvals = np.linalg.eigvalsh(S)
        smallest_eig = float(eigvals.min())
        if smallest_eig < SMALLEST_EIG_FLOOR:
            audit_singular_cov.append({
                "corpus": cname,
                "smallest_eig": smallest_eig,
            })
        try:
            Sinv = np.linalg.pinv(S)
        except Exception as e:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_lvl_fragility": None,
                "_excluded_singular_cov": str(e),
            }
            continue

        # Pick canon units around median letter-count rank
        order = np.argsort(letter_counts)
        median_idx = len(order) // 2
        half = K_CANON // 2
        lo = max(0, median_idx - half)
        hi = lo + K_CANON
        if hi > len(order):
            hi = len(order)
            lo = max(0, hi - K_CANON)
        canon_indices = [int(order[k]) for k in range(lo, hi)]

        per_canon: list[dict[str, Any]] = []
        unit_d_medians: list[float] = []
        n_dm_total = 0
        n_dm_zero = 0
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
                    s_edit = letters_28(" ".join(edited))
                    if len(s_edit) < 2:
                        continue
                    phi_edit = features_letter(s_edit)
                except Exception:
                    continue
                if not np.all(np.isfinite(phi_edit)):
                    continue
                d = phi_canon - phi_edit
                d_M = float(np.sqrt(d @ Sinv @ d))
                if not np.isfinite(d_M):
                    audit_dm_non_finite.append({
                        "corpus": cname,
                        "canon_label": label,
                        "d_M": d_M,
                    })
                    continue
                edit_dists.append(d_M)
                n_dm_total += 1
                if d_M == 0.0:
                    n_dm_zero += 1

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

        zero_frac = (n_dm_zero / n_dm_total) if n_dm_total > 0 else 1.0
        if zero_frac > ZERO_DM_FRAC_CEIL:
            audit_zero_dm_fraction.append({
                "corpus": cname,
                "n_dm_total": n_dm_total,
                "n_dm_zero": n_dm_zero,
                "zero_frac": zero_frac,
            })

        if not unit_d_medians:
            per_corpus[cname] = {
                "n_units": n_units,
                "phim_lvl_fragility": None,
                "_excluded_no_finite_edits": True,
                "per_canon": per_canon,
            }
            continue

        per_corpus[cname] = {
            "n_units": n_units,
            "K_canon_used": len(per_canon),
            "phim_lvl_fragility": float(np.median(unit_d_medians)),
            "phim_lvl_fragility_min_unit": float(min(unit_d_medians)),
            "phim_lvl_fragility_max_unit": float(max(unit_d_medians)),
            "smallest_cov_eig": smallest_eig,
            "zero_dm_fraction": float(zero_frac),
            "n_dm_total": int(n_dm_total),
            "n_dm_zero": int(n_dm_zero),
            "per_canon": per_canon,
            "mu_C": [float(x) for x in mu],
            "cov_C_diag": [float(x) for x in np.diag(S)],
        }
        print(
            f"[{EXP}]   {cname}: phim_lvl_fragility = "
            f"{per_corpus[cname]['phim_lvl_fragility']:.4f} "
            f"(min={per_corpus[cname]['phim_lvl_fragility_min_unit']:.4f}, "
            f"max={per_corpus[cname]['phim_lvl_fragility_max_unit']:.4f}), "
            f"zero_dm={zero_frac:.3f}, smallest_eig={smallest_eig:.2e}"
        )

    # ---- 5. Verdict ladder ----
    eligible: list[tuple[str, float]] = []
    for cname, summary in per_corpus.items():
        if summary.get("phim_lvl_fragility") is None:
            continue
        eligible.append((cname, summary["phim_lvl_fragility"]))
    eligible.sort(key=lambda x: -x[1])

    verdict = "UNDETERMINED"
    quran_rank = None
    quran_frag = None
    next_corpus = None
    next_frag = None
    margin_ratio = None

    if audit_non_finite:
        verdict = "FAIL_audit_features_finite"
    elif audit_singular_cov:
        verdict = "FAIL_audit_singular_cov"
    elif audit_zero_dm_fraction:
        verdict = "FAIL_audit_zero_displacement"
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

    # ---- 6. Receipt ----
    elapsed = time.time() - t0
    record: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H47",
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
            "SMALLEST_EIG_FLOOR": SMALLEST_EIG_FLOOR,
            "ZERO_DM_FRAC_CEIL": ZERO_DM_FRAC_CEIL,
            "GZIP_LEVEL": GZIP_LEVEL,
        },
        "audit": {
            "non_finite_features": audit_non_finite,
            "singular_cov": audit_singular_cov,
            "zero_dm_fraction_violations": audit_zero_dm_fraction,
            "dm_non_finite": audit_dm_non_finite,
        },
        "per_corpus": per_corpus,
        "ranking": [
            {"rank": ix + 1, "corpus": cname, "phim_lvl_fragility": fr}
            for ix, (cname, fr) in enumerate(eligible)
        ],
        "quran_rank": quran_rank,
        "quran_phim_lvl_fragility": quran_frag,
        "next_corpus": next_corpus,
        "next_phim_lvl_fragility": next_frag,
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
            "phim_lvl_fragility", "min_unit", "max_unit",
            "zero_dm_fraction", "smallest_cov_eig",
        ])
        for ix, (cname, fr) in enumerate(eligible):
            row = per_corpus[cname]
            w.writerow([
                ix + 1, cname, row["n_units"],
                row.get("K_canon_used", ""),
                row["phim_lvl_fragility"],
                row.get("phim_lvl_fragility_min_unit", ""),
                row.get("phim_lvl_fragility_max_unit", ""),
                row.get("zero_dm_fraction", ""),
                row.get("smallest_cov_eig", ""),
            ])
        for cname, summary in per_corpus.items():
            if summary.get("phim_lvl_fragility") is None:
                w.writerow([
                    "excl", cname, summary.get("n_units", 0), "",
                    "", "", "", "", "",
                ])

    print(f"\n[{EXP}] verdict: {verdict}")
    if quran_rank is not None:
        print(
            f"[{EXP}] quran rank = {quran_rank}, "
            f"phim_lvl_fragility = {quran_frag:.4f}"
        )
        if next_corpus is not None:
            mr_str = (
                f"{margin_ratio:.3f}" if margin_ratio is not None else "n/a"
            )
            print(
                f"[{EXP}] next corpus = {next_corpus}, "
                f"phim_lvl_fragility = {next_frag:.4f}, "
                f"margin ratio = {mr_str}"
            )
    print(f"[{EXP}] receipt: {receipt_path}")
    print(f"[{EXP}] csv:     {csv_path}")
    print(f"[{EXP}] elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
