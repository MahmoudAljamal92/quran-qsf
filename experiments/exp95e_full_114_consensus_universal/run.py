"""
exp95e_full_114_consensus_universal/run.py
==========================================
H37 — universal scaling of F53: K = 2 multi-compressor consensus closes
single-letter forgery detection on every surah of the Quran.

Pre-registered in PREREG.md (frozen 2026-04-26 night). This module is the
entry point: ``python -m experiments.exp95e_full_114_consensus_universal.run``

Reads (integrity-checked):
    phase_06_phi_m.pkl                                CORPORA['quran'] (114 surahs)
    results/experiments/exp94_adiyat_864/...json      gzip-only Q:100 baseline
    results/experiments/exp95c_multi_compressor_adiyat/...json
                                                      locked τ + K=2 Q:100 target

Writes ONLY under results/experiments/exp95e_full_114_consensus_universal/<scope>/.

Verdict ladder (PREREG §5):
    FAIL_tau_drift              τ values drift from exp95c receipt
    FAIL_q100_drift             Q:100 regression sub-run misses target
    FAIL_consensus_overfpr      aggregate K=2 ctrl FPR > 0.05
    FAIL_per_surah_floor        any surah K=2 recall < 0.99
    FAIL_aggregate_below_floor  aggregate K=2 recall < 0.999
    PARTIAL_per_surah_99        per-surah ≥ 0.99, aggregate ≥ 0.99 but < 0.999
    PASS_universal_999          per-surah ≥ 0.99 and aggregate ≥ 0.999
    PASS_universal_100          per-surah = 1.000 and aggregate = 1.000
"""
from __future__ import annotations

import argparse
import bz2
import csv
import gzip
import json
import lzma
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

try:
    import zstandard as zstd
    _ZSTD_AVAILABLE = True
except ImportError:
    _ZSTD_AVAILABLE = False
    zstd = None  # type: ignore

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
from experiments.exp95e_full_114_consensus_universal._enumerate import (  # noqa: E402
    ARABIC_CONS_28,
    enumerate_for_scope,
    letters_28,
    materialise,
)
from experiments.exp95e_full_114_consensus_universal._audit import (  # noqa: E402
    check_prereg_fingerprint,
    check_q100_regression,
    check_tau_drift,
    check_variant_counts_v1,
    cluster_missed_variants,
    collate_audit_report,
    sha256_of_file,
)

EXP = "exp95e_full_114_consensus_universal"

# ---------------------------------------------------------------------------
# Frozen constants (mirror PREREG §3)
# ---------------------------------------------------------------------------
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9
FPR_TARGET = 0.05
HEADLINE_K = 2
PROTOCOL_DRIFT_TOL = 0.001
EXP94_BASELINE_GZIP_RECALL = 0.990741  # exp94's R12-only recall on Q:100
NAMES = ("gzip", "bz2", "lzma", "zstd")

# Locked τ snapshot — must reproduce exp95c receipt to 1e-12.
# These will be re-loaded from the exp95c receipt at runtime; the snapshot
# below is the τ-drift sentinel reference.
_LOCKED_TAU = {
    "gzip": 0.04960835509138381,
    "bz2": 0.29584120982986767,
    "lzma": 0.02857142857142857,
    "zstd": 0.029978586723768737,
}

# PREREG hash sentinel — pinned 2026-04-26 night, after the PREREG was
# frozen. Any whitespace-level edit to PREREG.md will be caught by the
# fingerprint sentinel at run start (see _audit.check_prereg_fingerprint).
_PREREG_EXPECTED_HASH = (
    "ec14a1f6dcb81c3a54b0daeafa2b10f8707457ee4305de07d58ee7ede568e9a7"
)


# ---------------------------------------------------------------------------
# Compressor primitives (byte-equal to exp95c / _detector.py)
# ---------------------------------------------------------------------------
# We hold a single zstd compressor at module level. Because each worker
# process fork-/spawn-imports this module, every worker gets its own.
_ZSTD_CCTX = zstd.ZstdCompressor(level=ZSTD_LEVEL) if _ZSTD_AVAILABLE else None


def _gz_len(b: bytes) -> int:
    return len(gzip.compress(b, compresslevel=GZIP_LEVEL))


def _bz2_len(b: bytes) -> int:
    return len(bz2.compress(b, compresslevel=BZ2_LEVEL))


def _lzma_len(b: bytes) -> int:
    return len(lzma.compress(b, preset=LZMA_PRESET))


def _zstd_len(b: bytes) -> int:
    if _ZSTD_CCTX is None:
        raise RuntimeError("zstd not available")
    return len(_ZSTD_CCTX.compress(b))


_LEN_FNS = {
    "gzip": _gz_len,
    "bz2": _bz2_len,
    "lzma": _lzma_len,
    "zstd": _zstd_len,
}


def _ncd_pair(a_bytes: bytes, b_bytes: bytes, ab_bytes: bytes,
              length_fn) -> float:
    if not a_bytes and not b_bytes:
        return 0.0
    za = length_fn(a_bytes)
    zb = length_fn(b_bytes)
    zab = length_fn(ab_bytes)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


# ---------------------------------------------------------------------------
# Worker: score a chunk of variants on a single surah
# ---------------------------------------------------------------------------
def _score_surah_chunk(args: tuple[str, str, list[tuple[str, dict]],
                                   dict[str, float]]) -> dict[str, Any]:
    """Worker: receives ``(surah_label, canon_letters, variant_pairs, tau)``
    where each variant_pair is ``(variant_letters_28, meta)``.

    Returns aggregate counters for the chunk plus the list of missed
    variants (K_fired < 2).
    """
    surah_label, canon_letters, variant_pairs, tau = args

    # Pre-encode the canonical bytes once — this is the only redundancy
    # gzip/bz2/lzma/zstd have to repeat (their internal state has no
    # public reset between calls).
    canon_bytes = canon_letters.encode("utf-8")
    canon_lens = {n: _LEN_FNS[n](canon_bytes) for n in NAMES}

    # Counters per-K, per-compressor solo
    fires_K = [0, 0, 0, 0, 0]   # index by K (0..4)
    fires_solo = {n: 0 for n in NAMES}
    n_total = 0
    missed: list[dict[str, Any]] = []
    ncd_min = {n: float("inf") for n in NAMES}
    ncd_max = {n: float("-inf") for n in NAMES}

    for var_letters, meta in variant_pairs:
        var_bytes = var_letters.encode("utf-8")
        ab_bytes = canon_bytes + var_bytes  # canonical first, variant second
        # Inline the NCD for each compressor with the cached za = canon_lens.
        K = 0
        fires_this: dict[str, bool] = {}
        ncd_this: dict[str, float] = {}
        for n in NAMES:
            za = canon_lens[n]
            zb = _LEN_FNS[n](var_bytes)
            zab = _LEN_FNS[n](ab_bytes)
            denom = max(1, max(za, zb))
            ncd = (zab - min(za, zb)) / denom
            ncd_this[n] = ncd
            fired = ncd >= tau[n]
            fires_this[n] = fired
            if fired:
                fires_solo[n] += 1
                K += 1
            if ncd < ncd_min[n]:
                ncd_min[n] = ncd
            if ncd > ncd_max[n]:
                ncd_max[n] = ncd
        # Increment cumulative K-of counters: variant fires "≥k" for every
        # k ≤ K_fired. Storing fires_K[k] = #variants with K_fired ≥ k makes
        # the recall_at_K aggregation downstream a single dict read.
        for k in range(K + 1):
            fires_K[k] += 1
        n_total += 1
        if K < HEADLINE_K:
            missed.append({
                "surah": surah_label,
                "K_fired": K,
                "ncd": {n: round(ncd_this[n], 6) for n in NAMES},
                "fires": fires_this,
                **meta,
            })

    return {
        "surah_label": surah_label,
        "n_total": n_total,
        "fires_K_atleast": fires_K,
        "fires_solo": fires_solo,
        "ncd_min": ncd_min,
        "ncd_max": ncd_max,
        "missed": missed,
    }


# ---------------------------------------------------------------------------
# Receipt loaders
# ---------------------------------------------------------------------------
def _load_exp95c_receipt() -> dict[str, Any]:
    p = (_ROOT / "results" / "experiments" / "exp95c_multi_compressor_adiyat"
         / "exp95c_multi_compressor_adiyat.json")
    if not p.exists():
        raise FileNotFoundError(
            f"exp95c receipt missing at {p}. exp95e cannot run without it "
            "(τ values are loaded from exp95c)."
        )
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_exp94_receipt() -> dict[str, Any]:
    p = (_ROOT / "results" / "experiments" / "exp94_adiyat_864"
         / "exp94_adiyat_864.json")
    if not p.exists():
        raise FileNotFoundError(f"exp94 receipt missing at {p}.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# ctrl-null FPR re-computation (re-uses the locked τ + a fresh ctrl pool)
# ---------------------------------------------------------------------------
def _ctrl_null_fpr(corpora: dict[str, list], tau: dict[str, float],
                   *, seed: int = 42, n_units: int = 200,
                   n_pert_per_unit: int = 20,
                   band_a: tuple[int, int] = (15, 100)) -> dict[str, Any]:
    """Reproduce the exp95c ctrl-null FPR computation. Identical seeding,
    identical compressors, identical sources — should reproduce the
    exp95c FPR_by_K to within sampling noise.
    """
    import random
    arabic_ctrl = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "arabic_bible", "hindawi"]
    pool: list = []
    lo, hi = band_a
    for name in arabic_ctrl:
        for u in corpora.get(name, []):
            n = len(u.verses)
            if lo <= n <= hi:
                pool.append(u)
    rng_pool = random.Random(seed + 1)
    rng_pool.shuffle(pool)
    units = pool[:n_units]
    rng_c = random.Random(seed + 2)

    null_per: dict[str, list[float]] = {n: [] for n in NAMES}

    for u in units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        for _ in range(n_pert_per_unit):
            pair = _apply_ctrl_perturbation(u.verses, rng_u)
            if pair is None:
                continue
            pert_verses = pair[0]
            ca = letters_28(" ".join(u.verses)).encode("utf-8")
            cb = letters_28(" ".join(pert_verses)).encode("utf-8")
            cab = ca + cb
            for n in NAMES:
                fn = _LEN_FNS[n]
                za, zb, zab = fn(ca), fn(cb), fn(cab)
                denom = max(1, max(za, zb))
                null_per[n].append((zab - min(za, zb)) / denom)

    # Per-K FPR
    null_fires = {n: (np.asarray(null_per[n]) >= tau[n]).astype(int)
                  for n in NAMES}
    n_null = len(null_per[NAMES[0]])
    null_K = sum(null_fires[n] for n in NAMES)
    fpr_by_K = {str(K): float((null_K >= K).mean()) for K in (1, 2, 3, 4)}
    fpr_per_compressor = {n: float((np.asarray(null_per[n]) >= tau[n]).mean())
                          for n in NAMES}
    return {
        "n_null_pool": n_null,
        "fpr_per_compressor_at_locked_tau": fpr_per_compressor,
        "fpr_by_consensus_K": fpr_by_K,
    }


def _apply_ctrl_perturbation(verses, rng):
    """Identical to exp95c::_apply_perturbation. Used only for the ctrl-null
    FPR re-computation."""
    nv = len(verses)
    if nv < 5:
        return None
    diac_set = set(
        "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
        "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
        "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
    )

    def strip_d(s: str) -> str:
        return "".join(c for c in str(s) if c not in diac_set)

    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in cons if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------
def _build_chunks(quran_units: list, scope: str,
                  chunk_size: int = 64) -> list[tuple]:
    """For each surah, enumerate variants under `scope`, materialise letter
    pairs, and split into chunks of `chunk_size` for the worker pool.

    Returns a list of (surah_label, canon_letters, [(var_letters, meta), ...], tau)
    placeholders WITHOUT τ — τ is added in the dispatcher because workers
    need it but it's small.
    """
    chunks: list[tuple] = []
    for u in quran_units:
        label = getattr(u, "label", "?")
        verses = list(u.verses)
        specs = enumerate_for_scope(scope, verses)
        if not specs:
            # Empty surah for this scope (e.g. FULL on a < 5-verse surah)
            chunks.append((label, "", [], 0))
            continue
        # Materialise all (canon_letters, var_letters, meta) tuples for this
        # surah; canon_letters is constant across the surah so we cache it.
        materialised = list(materialise(label, verses, specs, scope))
        canon_letters = materialised[0][1]
        # Verify every entry shares the same canonical letters (sanity)
        assert all(m[1] == canon_letters for m in materialised), (
            f"canonical drift inside surah {label}: enumerator produced "
            "different canon_letters for different variants"
        )
        pairs = [(m[2], m[3]) for m in materialised]
        # Split pairs into fixed-size chunks
        for i in range(0, len(pairs), chunk_size):
            chunks.append((label, canon_letters, pairs[i:i + chunk_size],
                           len(specs)))
    return chunks


def _aggregate(per_surah: dict[str, dict],
               chunk_results: list[dict[str, Any]],
               surah_n_canon_consonants_v1: dict[str, int]) -> None:
    """Merge worker chunk_results into per_surah[label] aggregate dict.
    Mutates per_surah in place."""
    for cr in chunk_results:
        label = cr["surah_label"]
        if label not in per_surah:
            per_surah[label] = {
                "n_variants": 0,
                "fires_K_atleast": [0, 0, 0, 0, 0],
                "fires_solo": {n: 0 for n in NAMES},
                "ncd_min": {n: float("inf") for n in NAMES},
                "ncd_max": {n: float("-inf") for n in NAMES},
                "missed": [],
                "n_canon_consonants_v1": surah_n_canon_consonants_v1.get(label, 0),
            }
        row = per_surah[label]
        row["n_variants"] += cr["n_total"]
        for k in range(5):
            row["fires_K_atleast"][k] += cr["fires_K_atleast"][k]
        for n in NAMES:
            row["fires_solo"][n] += cr["fires_solo"][n]
            if cr["ncd_min"][n] < row["ncd_min"][n]:
                row["ncd_min"][n] = cr["ncd_min"][n]
            if cr["ncd_max"][n] > row["ncd_max"][n]:
                row["ncd_max"][n] = cr["ncd_max"][n]
        row["missed"].extend(cr["missed"])


def _per_surah_finalise(per_surah: dict[str, dict]) -> None:
    """Compute recall_K1..K4 and recall_solo_* per surah from raw counters."""
    for label, row in per_surah.items():
        n = max(1, row["n_variants"])
        row["recall_K1"] = row["fires_K_atleast"][1] / n
        row["recall_K2"] = row["fires_K_atleast"][2] / n
        row["recall_K3"] = row["fires_K_atleast"][3] / n
        row["recall_K4"] = row["fires_K_atleast"][4] / n
        for c in NAMES:
            row[f"recall_solo_{c}"] = row["fires_solo"][c] / n
        # ncd_min/max may still be inf if no variants enumerated; replace
        for c in NAMES:
            if row["ncd_min"][c] == float("inf"):
                row["ncd_min"][c] = None
            if row["ncd_max"][c] == float("-inf"):
                row["ncd_max"][c] = None


def _aggregate_global(per_surah: dict[str, dict]) -> dict[str, Any]:
    """Compute pooled-variant recall across all surahs."""
    total = sum(row["n_variants"] for row in per_surah.values())
    if total == 0:
        return {
            "n_variants": 0, "recall_K1": float("nan"),
            "recall_K2": float("nan"),
            "recall_K3": float("nan"), "recall_K4": float("nan"),
            "recall_solo": {n: float("nan") for n in NAMES},
        }
    sum_K = [sum(row["fires_K_atleast"][k] for row in per_surah.values())
             for k in range(5)]
    sum_solo = {c: sum(row["fires_solo"][c] for row in per_surah.values())
                for c in NAMES}
    return {
        "n_variants": total,
        "recall_K1": sum_K[1] / total,
        "recall_K2": sum_K[2] / total,
        "recall_K3": sum_K[3] / total,
        "recall_K4": sum_K[4] / total,
        "recall_solo": {c: sum_solo[c] / total for c in NAMES},
    }


def _verdict(scope: str, tau_drift: dict, q100_reg: dict,
             ctrl_null: dict, per_surah: dict[str, dict],
             agg: dict, drift_tol: float) -> str:
    """Apply the strict-order PREREG §5 verdict ladder."""
    if not tau_drift["ok"]:
        return "FAIL_tau_drift"
    if scope == "v1" and not q100_reg["ok"]:
        return "FAIL_q100_drift"
    fpr_k2 = ctrl_null["fpr_by_consensus_K"].get(str(HEADLINE_K), 0.0)
    if fpr_k2 > FPR_TARGET + 1e-6:
        return "FAIL_consensus_overfpr"
    # Per-surah floor: every surah with ≥ 1 variant must meet ≥ 0.99
    eligible = [(lbl, row) for lbl, row in per_surah.items()
                if row["n_variants"] > 0]
    if not eligible:
        return "FAIL_no_variants"
    min_recall_K2 = min(row["recall_K2"] for _, row in eligible)
    if min_recall_K2 < 0.99:
        return "FAIL_per_surah_floor"
    if agg["recall_K2"] < 0.999:
        if agg["recall_K2"] >= 0.99:
            return "PARTIAL_per_surah_99_aggregate_99"
        return "FAIL_aggregate_below_floor"
    # PASS branches
    if (
        all(row["recall_K2"] >= 0.99999 for _, row in eligible)
        and agg["recall_K2"] >= 0.99999
    ):
        return "PASS_universal_100"
    return "PASS_universal_999"


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------
def _write_per_surah_csv(per_surah: dict[str, dict], path: Path) -> None:
    cols = [
        "surah_label", "n_variants",
        "recall_K1", "recall_K2", "recall_K3", "recall_K4",
        "recall_solo_gzip", "recall_solo_bz2",
        "recall_solo_lzma", "recall_solo_zstd",
        "ncd_min_gzip", "ncd_max_gzip",
        "ncd_min_bz2", "ncd_max_bz2",
        "ncd_min_lzma", "ncd_max_lzma",
        "ncd_min_zstd", "ncd_max_zstd",
        "n_canon_consonants_v1",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for lbl in sorted(per_surah.keys()):
            row = per_surah[lbl]
            line = [
                lbl, row["n_variants"],
                row["recall_K1"], row["recall_K2"],
                row["recall_K3"], row["recall_K4"],
                row["recall_solo_gzip"], row["recall_solo_bz2"],
                row["recall_solo_lzma"], row["recall_solo_zstd"],
                row["ncd_min"]["gzip"], row["ncd_max"]["gzip"],
                row["ncd_min"]["bz2"], row["ncd_max"]["bz2"],
                row["ncd_min"]["lzma"], row["ncd_max"]["lzma"],
                row["ncd_min"]["zstd"], row["ncd_max"]["zstd"],
                row.get("n_canon_consonants_v1", 0),
            ]
            w.writerow(line)


def _write_missed_csv(missed: list[dict], path: Path) -> None:
    cols = [
        "surah", "scope", "verse_idx", "char_pos_in_v1", "char_pos_in_verse",
        "word_idx", "char_pos_in_word",
        "orig", "repl", "K_fired",
        "ncd_gzip", "ncd_bz2", "ncd_lzma", "ncd_zstd",
        "fires_gzip", "fires_bz2", "fires_lzma", "fires_zstd",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for m in missed:
            line = [
                m.get("surah", "?"), m.get("scope", "?"),
                m.get("verse_idx", ""), m.get("char_pos_in_v1", ""),
                m.get("char_pos_in_verse", ""),
                m.get("word_idx", ""), m.get("char_pos_in_word", ""),
                m.get("orig", ""), m.get("repl", ""), m.get("K_fired", ""),
                m["ncd"].get("gzip", ""), m["ncd"].get("bz2", ""),
                m["ncd"].get("lzma", ""), m["ncd"].get("zstd", ""),
                m["fires"].get("gzip", ""), m["fires"].get("bz2", ""),
                m["fires"].get("lzma", ""), m["fires"].get("zstd", ""),
            ]
            w.writerow(line)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="exp95e_full_114_consensus_universal.run",
        description=(
            "H37: scale F53 K=2 multi-compressor consensus across all 114 "
            "Quran surahs."
        ),
    )
    p.add_argument(
        "--scope",
        choices=("v1", "short", "sample", "quarter", "half", "full"),
        default="v1",
        help=("Variant enumeration scope (default v1, the headline scope). "
              "v1 = first verse only, ~145K variants, ~30-90 min. "
              "short = first 3 verses, ~377K, ~2-4h. "
              "sample = random 10%% of full, ~370K, ~2-4h. "
              "quarter = random 25%% of full, ~925K, ~5-8h. "
              "half = random 50%% of full, ~1.85M, ~10-18h. "
              "full = every interior letter, ~3.7M, ~18-36h."),
    )
    p.add_argument(
        "--workers", type=int, default=max(1, (os.cpu_count() or 4) - 1),
        help="Number of worker processes (default: cpu_count() - 1).",
    )
    p.add_argument(
        "--chunk", type=int, default=64,
        help="Variants per chunk dispatched to a worker (default 64).",
    )
    p.add_argument(
        "--surahs", type=str, default=None,
        help=("Optional comma-separated list of surah labels to score "
              "(e.g. 'Q:001,Q:100'). Default: all 114."),
    )
    p.add_argument(
        "--no-progress", action="store_true",
        help="Suppress per-chunk progress output.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:  # noqa: C901  (long but linear)
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = _parse_args(argv)
    scope = args.scope

    # Sandboxed output dir
    out_root = safe_output_dir(EXP)
    out = out_root / scope
    out.mkdir(parents=True, exist_ok=True)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H37 — universal scaling of F53 (scope={scope})")

    # --- Sentinel 1: zstd available -----------------------------------------
    if not _ZSTD_AVAILABLE:
        verdict = "FAIL_compressor_unavailable"
        report = {
            "experiment": EXP, "verdict": verdict, "scope": scope,
            "error": "zstandard library not importable. `pip install zstandard`.",
        }
        outfile = out / f"{EXP}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] {verdict}")
        return 2

    # --- Load receipts ------------------------------------------------------
    exp95c = _load_exp95c_receipt()
    exp94 = _load_exp94_receipt()
    receipt_tau = {n: float(exp95c["tau_per_compressor"][n]) for n in NAMES}

    # --- Sentinel 2: τ-drift ------------------------------------------------
    tau_drift = check_tau_drift(_LOCKED_TAU, receipt_tau, tol=1e-12)
    print(f"[{EXP}] τ-drift sentinel ok={tau_drift['ok']} "
          f"max_drift={tau_drift['max_drift']:.2e}")
    if not tau_drift["ok"]:
        verdict = "FAIL_tau_drift"
        report = {
            "experiment": EXP, "verdict": verdict, "scope": scope,
            "audit": {"tau_drift_sentinel": tau_drift},
        }
        outfile = out / f"{EXP}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] {verdict}")
        return 3

    tau = receipt_tau  # use receipt values; locked snapshot has been verified

    # --- PREREG fingerprint -------------------------------------------------
    prereg_fp = check_prereg_fingerprint(_HERE / "PREREG.md",
                                         _PREREG_EXPECTED_HASH)
    print(f"[{EXP}] PREREG hash = {prereg_fp.get('actual_hash', '?')[:16]}... "
          f"(deferred={prereg_fp.get('deferred', False)})")

    # --- Load corpora -------------------------------------------------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    quran_all = list(CORPORA.get("quran", []))
    if args.surahs:
        wanted = {s.strip() for s in args.surahs.split(",") if s.strip()}
        quran = [u for u in quran_all if getattr(u, "label", "") in wanted]
        if not quran:
            raise SystemExit(f"None of {wanted} matched a CORPORA['quran'] label.")
    else:
        quran = quran_all
    print(f"[{EXP}] Will score {len(quran)} surahs (of {len(quran_all)} total).")

    # Cache n_canon_consonants_v1 for the variant-count sanity check
    n_canon_v1: dict[str, int] = {
        getattr(u, "label", "?"): len(letters_28(u.verses[0])) for u in quran
    }

    # --- Build chunks -------------------------------------------------------
    print(f"[{EXP}] Enumerating variants (scope={scope}) ...")
    t_enum = time.time()
    chunks = _build_chunks(quran, scope, chunk_size=args.chunk)
    n_total_variants = sum(len(c[2]) for c in chunks if isinstance(c, tuple)
                           and len(c) >= 3 and isinstance(c[2], list))
    elapsed_enum = time.time() - t_enum
    print(f"[{EXP}] Enumerated {n_total_variants:,} variants in "
          f"{elapsed_enum:.1f}s; dispatching to {args.workers} workers "
          f"({len([c for c in chunks if c[2]])} non-empty chunks).")

    # --- Run worker pool ----------------------------------------------------
    per_surah: dict[str, dict] = {
        getattr(u, "label", "?"): {
            "n_variants": 0,
            "fires_K_atleast": [0, 0, 0, 0, 0],
            "fires_solo": {n: 0 for n in NAMES},
            "ncd_min": {n: float("inf") for n in NAMES},
            "ncd_max": {n: float("-inf") for n in NAMES},
            "missed": [],
            "n_canon_consonants_v1": n_canon_v1.get(getattr(u, "label", "?"), 0),
        }
        for u in quran
    }

    score_inputs = []
    for label, canon_letters, pairs, _n_specs in chunks:
        if not pairs:
            continue
        score_inputs.append((label, canon_letters, pairs, tau))

    n_chunks = len(score_inputs)
    n_done = 0
    t_score = time.time()
    chunk_results: list[dict[str, Any]] = []

    if args.workers <= 1:
        # Single-process path (useful for debugging and CI)
        for ci in score_inputs:
            chunk_results.append(_score_surah_chunk(ci))
            n_done += 1
            if not args.no_progress and n_done % max(1, n_chunks // 50) == 0:
                _print_progress(n_done, n_chunks, t_score)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = [ex.submit(_score_surah_chunk, ci) for ci in score_inputs]
            for fut in as_completed(futures):
                chunk_results.append(fut.result())
                n_done += 1
                if not args.no_progress and n_done % max(1, n_chunks // 50) == 0:
                    _print_progress(n_done, n_chunks, t_score)

    elapsed_score = time.time() - t_score
    print(f"[{EXP}] Scored {n_total_variants:,} variants in "
          f"{elapsed_score:.1f}s "
          f"({n_total_variants / max(1.0, elapsed_score):.0f} variants/s).")

    # --- Aggregate ----------------------------------------------------------
    _aggregate(per_surah, chunk_results, n_canon_v1)
    _per_surah_finalise(per_surah)
    agg = _aggregate_global(per_surah)

    # --- Q:100 regression sub-result ---------------------------------------
    q100_reg = check_q100_regression(per_surah, EXP94_BASELINE_GZIP_RECALL,
                                     drift_tol=PROTOCOL_DRIFT_TOL)
    print(f"[{EXP}] Q:100 regression: K2={q100_reg['K2_recall_q100']['actual']:.6f} "
          f"gzip={q100_reg['gzip_solo_recall_q100']['actual']:.6f} "
          f"ok={q100_reg['ok']}")

    # --- ctrl-null FPR re-computation --------------------------------------
    print(f"[{EXP}] Re-computing ctrl-null FPR with locked τ ...")
    ctrl_null = _ctrl_null_fpr(CORPORA, tau)
    print(f"[{EXP}] ctrl-null K=2 FPR = "
          f"{ctrl_null['fpr_by_consensus_K']['2']:.4f} "
          f"(target ≤ {FPR_TARGET})")

    # --- Variant-count sanity (V1 only) ------------------------------------
    if scope == "v1":
        var_counts = check_variant_counts_v1(per_surah)
    else:
        var_counts = {"ok": True, "skipped_for_scope": scope}

    # --- Missed-variant clustering -----------------------------------------
    all_missed: list[dict] = []
    for row in per_surah.values():
        all_missed.extend(row.get("missed", []))
    clusters = cluster_missed_variants(all_missed)

    # --- Verdict ------------------------------------------------------------
    elapsed_total = time.time() - t0
    verdict = _verdict(scope, tau_drift, q100_reg, ctrl_null, per_surah,
                       agg, PROTOCOL_DRIFT_TOL)

    audit_report = collate_audit_report(
        tau_drift=tau_drift, prereg_fingerprint=prereg_fp,
        q100_regression=q100_reg, variant_counts=var_counts,
        missed_clusters=clusters,
        self_check_pre_ts=pre["ts_start"],
        runtime_seconds=round(elapsed_total, 2),
        scope=scope,
    )

    # --- Headline print -----------------------------------------------------
    print(f"\n{'=' * 68}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  scope                 : {scope}")
    print(f"  surahs scored         : {sum(1 for r in per_surah.values() if r['n_variants'] > 0)}"
          f" / {len(per_surah)}")
    print(f"  total variants        : {agg['n_variants']:,}")
    print(f"  aggregate recall K=1  : {agg['recall_K1']:.6f}")
    print(f"  aggregate recall K=2  : {agg['recall_K2']:.6f}  ← headline")
    print(f"  aggregate recall K=3  : {agg['recall_K3']:.6f}")
    print(f"  aggregate recall K=4  : {agg['recall_K4']:.6f}")
    print(f"  ctrl null K=2 FPR     : {ctrl_null['fpr_by_consensus_K']['2']:.4f}")
    print(f"  Q:100 K=2 recall      : {q100_reg['K2_recall_q100']['actual']:.6f}")
    print(f"  Q:100 gzip-solo recall: {q100_reg['gzip_solo_recall_q100']['actual']:.6f}")
    print(f"{'=' * 68}")

    # --- Worst-10 surahs ---------------------------------------------------
    eligible = [(lbl, row) for lbl, row in per_surah.items() if row["n_variants"] > 0]
    eligible.sort(key=lambda kv: kv[1]["recall_K2"])
    print(f"\n[{EXP}] 10 weakest surahs (K=2 recall):")
    for lbl, row in eligible[:10]:
        print(f"  {lbl}  n={row['n_variants']:>5}  "
              f"K1={row['recall_K1']:.6f}  K2={row['recall_K2']:.6f}  "
              f"gzip={row['recall_solo_gzip']:.6f}")

    # --- Receipt ------------------------------------------------------------
    # Drop the bulky `missed` lists from per_surah for the JSON receipt;
    # they go into missed_variants.csv. Keep summary counts only.
    per_surah_compact = {}
    for lbl, row in per_surah.items():
        compact = {k: v for k, v in row.items()
                   if k not in ("missed", "fires_K_atleast", "fires_solo",
                                "ncd_min", "ncd_max")}
        compact["fires_K_atleast"] = list(row["fires_K_atleast"])
        compact["fires_solo"] = dict(row["fires_solo"])
        compact["ncd_min"] = dict(row["ncd_min"])
        compact["ncd_max"] = dict(row["ncd_max"])
        per_surah_compact[lbl] = compact

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "H37 — multi-compressor consensus K=2 across {gzip-9, bz2-9, "
            "lzma-preset-9, zstd-9} with τ frozen from exp95c closes "
            "single-letter forgery detection on every Quran surah at "
            "recall ≥ 0.999 aggregate, ≥ 0.99 per-surah."
        ),
        "prereg_document": "experiments/exp95e_full_114_consensus_universal/PREREG.md",
        "prereg_hash_actual": prereg_fp.get("actual_hash"),
        "prereg_hash_expected": _PREREG_EXPECTED_HASH,
        "scope": scope,
        "frozen_constants": {
            "gzip_level": GZIP_LEVEL, "bz2_level": BZ2_LEVEL,
            "lzma_preset": LZMA_PRESET, "zstd_level": ZSTD_LEVEL,
            "fpr_target": FPR_TARGET, "headline_k": HEADLINE_K,
            "protocol_drift_tol": PROTOCOL_DRIFT_TOL,
            "exp94_baseline_gzip_recall": EXP94_BASELINE_GZIP_RECALL,
        },
        "tau_per_compressor": tau,
        "tau_locked_snapshot": _LOCKED_TAU,
        "ctrl_null": ctrl_null,
        "n_surahs_scored": len(per_surah_compact),
        "n_variants_total": agg["n_variants"],
        "aggregate": agg,
        "per_surah": per_surah_compact,
        "audit_report": audit_report,
        "verdict": verdict,
        "runtime_seconds": round(elapsed_total, 2),
        "phase_pkl_sha256": sha256_of_file(
            _ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl"),
        "exp95c_receipt_sha256": sha256_of_file(
            _ROOT / "results" / "experiments"
            / "exp95c_multi_compressor_adiyat"
            / "exp95c_multi_compressor_adiyat.json"),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    _write_per_surah_csv(per_surah, out / "per_surah_table.csv")
    _write_missed_csv(all_missed, out / "missed_variants.csv")
    with open(out / "audit_report.json", "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False, default=float)

    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Wrote {out / 'per_surah_table.csv'}")
    print(f"[{EXP}] Wrote {out / 'missed_variants.csv'}")
    print(f"[{EXP}] Wrote {out / 'audit_report.json'}")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    print(f"[{EXP}] Runtime: {elapsed_total:.1f}s")
    return 0 if verdict.startswith("PASS") else (
        1 if verdict.startswith("PARTIAL") else 4
    )


def _print_progress(n_done: int, n_total: int, t_start: float) -> None:
    elapsed = time.time() - t_start
    rate = n_done / max(0.001, elapsed)
    eta = (n_total - n_done) / max(0.001, rate)
    print(f"  [{n_done:>5}/{n_total:>5} chunks  "
          f"{n_done/max(1,n_total)*100:>5.1f}%  "
          f"elapsed {elapsed:>5.0f}s  ETA {eta:>5.0f}s]")


if __name__ == "__main__":
    sys.exit(main())
