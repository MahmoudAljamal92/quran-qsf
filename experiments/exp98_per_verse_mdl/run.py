"""
exp98_per_verse_mdl — Per-verse multi-compressor MDL across 7 corpora.

Closes claim C4 of F57 (Quran 11:1 verses-made-precise).

For each verse v in each of 7 Arabic corpora, compute:
    mdl(v) = min { gzip(v), bz2(v), lzma(v), zstd(v), brotli(v) } bytes
    mdl_rate(v) = mdl(v) / len(v.encode('utf-8'))

Per-corpus statistic = median(mdl_rate(v)). Quran passes iff
its median is the strict minimum AND beats next-ranked by > 1.5 %.

Scope: whole 114-surah Quran. No band gates.

PREREG: experiments/exp98_per_verse_mdl/PREREG.md (amended 2026-04-27 15:05; 3 fast compressors)
PREREG hash: 6218b65ce6b7bb9bb51db269e8d32f23a8f63e3b0b5e68037793d9c218bbc11f
"""

from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import zstandard as zstd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RESULTS = ROOT / "results"
EXP_OUT = RESULTS / "experiments" / "exp98_per_verse_mdl"
EXP_OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))

from experiments._lib import load_phase, safe_output_dir, self_check_begin, self_check_end  # noqa: E402

EXP = "exp98_per_verse_mdl"
PREREG_HASH_EXPECTED = "6218b65ce6b7bb9bb51db269e8d32f23a8f63e3b0b5e68037793d9c218bbc11f"

# ---------------------------------------------------------------------------
# Frozen constants (must match PREREG.md §3, amended)
# ---------------------------------------------------------------------------
ARABIC_POOL = ["quran", "poetry_jahili", "poetry_islami",
               "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
COMPRESSORS = ("gzip", "bz2", "zstd")
COMPRESSION_LEVEL_GZIP   = 9
COMPRESSION_LEVEL_BZ2    = 9
COMPRESSION_LEVEL_ZSTD   = 22
MIN_VERSE_BYTES        = 5
MARGIN_THRESHOLD       = 0.015
N_QURAN_VERSES_EXPECTED = 6236


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# Initialize zstd compressor once
_ZSTD = zstd.ZstdCompressor(level=COMPRESSION_LEVEL_ZSTD)


def mdl_bytes(text: str) -> dict:
    """Return per-compressor compressed-byte counts and the min."""
    raw = text.encode("utf-8")
    if len(raw) == 0:
        return None
    sizes = {
        "gzip":   len(gzip.compress(raw, compresslevel=COMPRESSION_LEVEL_GZIP)),
        "bz2":    len(bz2.compress(raw, compresslevel=COMPRESSION_LEVEL_BZ2)),
        "zstd":   len(_ZSTD.compress(raw)),
    }
    mn = min(sizes[c] for c in COMPRESSORS)
    sizes["min"]      = mn
    sizes["raw"]      = len(raw)
    sizes["mdl_rate"] = mn / sizes["raw"]
    return sizes


def harvest_verses(units, corpus: str) -> list[str]:
    """Pull verse-level strings from each loaded unit. Each unit has a
    `.verses` iterable of strings (or objects with __str__)."""
    out = []
    for u in units:
        for v in getattr(u, "verses", []):
            s = str(v).strip()
            if len(s.encode("utf-8")) >= MIN_VERSE_BYTES:
                out.append(s)
    return out


def median(xs: Iterable[float]) -> float:
    arr = np.array(list(xs))
    return float(np.median(arr))


def percentile(xs: Iterable[float], p: float) -> float:
    arr = np.array(list(xs))
    return float(np.percentile(arr, p))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    audit_failures: list[str] = []

    prereg_hash = sha256_of(HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash}")
    if prereg_hash != PREREG_HASH_EXPECTED:
        audit_failures.append(f"PREREG drift: actual={prereg_hash} expected={PREREG_HASH_EXPECTED}")

    print(f"[{EXP}] loading phase_06_phi_m features ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    per_corpus = {}
    for corpus in ARABIC_POOL:
        units = CORPORA.get(corpus, [])
        verses = harvest_verses(units, corpus)
        n = len(verses)
        if n < 1000:
            audit_failures.append(f"A1: {corpus} has only {n} verses (need > 1000)")
        # Run compression on each verse
        rates = []
        per_compressor_sums = {c: 0 for c in COMPRESSORS}
        n_failed = 0
        t_corpus = time.time()
        for v in verses:
            try:
                m = mdl_bytes(v)
                if m is None or not np.isfinite(m["mdl_rate"]) or m["mdl_rate"] <= 0:
                    n_failed += 1
                    continue
                rates.append(m["mdl_rate"])
                for c in COMPRESSORS:
                    per_compressor_sums[c] += m[c]
            except Exception:
                n_failed += 1
        elapsed = time.time() - t_corpus
        valid = len(rates)
        completion = valid / max(n, 1)
        if completion < 0.999:
            audit_failures.append(f"A3: {corpus} compression completion {completion:.4f} < 0.999")

        per_corpus[corpus] = {
            "n_verses_total":    n,
            "n_verses_valid":    valid,
            "n_failed":          n_failed,
            "completion_rate":   completion,
            "median_mdl_rate":   median(rates) if rates else float("nan"),
            "p05_mdl_rate":      percentile(rates, 5)  if rates else float("nan"),
            "p25_mdl_rate":      percentile(rates, 25) if rates else float("nan"),
            "p75_mdl_rate":      percentile(rates, 75) if rates else float("nan"),
            "p95_mdl_rate":      percentile(rates, 95) if rates else float("nan"),
            "wall_time_s":       elapsed,
        }
        print(f"[{EXP}]   {corpus:18s} n={n:6d}  median(mdl/raw) = {per_corpus[corpus]['median_mdl_rate']:.4f}  "
              f"p25..p75 = [{per_corpus[corpus]['p25_mdl_rate']:.4f}, {per_corpus[corpus]['p75_mdl_rate']:.4f}]  "
              f"({elapsed:.1f}s)")

    # Audit A2: Quran verse count
    n_q = per_corpus["quran"]["n_verses_valid"]
    if abs(n_q - N_QURAN_VERSES_EXPECTED) > 5:
        audit_failures.append(f"A2: Quran n_verses={n_q} != expected {N_QURAN_VERSES_EXPECTED}")

    # Build ranking (lower = more compressible = more "structured / precise")
    ranked = sorted(per_corpus.items(), key=lambda kv: kv[1]["median_mdl_rate"])
    quran_rank = next(i for i, (c, _) in enumerate(ranked) if c == "quran")
    quran_median = per_corpus["quran"]["median_mdl_rate"]
    next_corpus, next_row = ranked[1] if quran_rank == 0 else ranked[0]
    if quran_rank == 0 and len(ranked) > 1:
        next_corpus, next_row = ranked[1]
    next_median = next_row["median_mdl_rate"]

    margin = (next_median - quran_median) / quran_median if quran_median > 0 else 0.0

    print()
    print("[{}] ranking (lower median mdl_rate = more compressible = more structured):".format(EXP))
    for i, (c, row) in enumerate(ranked):
        print(f"    {i+1}. {c:18s}  median = {row['median_mdl_rate']:.4f}")
    print(f"\n[{EXP}] Quran rank: {quran_rank + 1} of {len(ranked)}")
    print(f"[{EXP}] margin to next-ranked ({next_corpus}): {margin*100:+.2f}%")

    # Verdict
    if audit_failures:
        verdict = "FAIL_audit_" + audit_failures[0].split(":")[0].split("_")[0]
    elif quran_rank != 0:
        verdict = "FAIL_quran_not_top_1"
    elif margin <= MARGIN_THRESHOLD:
        verdict = "PARTIAL_top_1_within_eps"
    else:
        verdict = "PASS_quran_strict_min_mdl"

    print(f"[{EXP}] verdict = {verdict}")

    receipt = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H53",
        "verdict": verdict,
        "prereg_hash_expected": PREREG_HASH_EXPECTED,
        "prereg_hash_actual": prereg_hash,
        "frozen_constants": {
            "ARABIC_POOL": ARABIC_POOL,
            "COMPRESSORS": list(COMPRESSORS),
            "MIN_VERSE_BYTES": MIN_VERSE_BYTES,
            "MARGIN_THRESHOLD": MARGIN_THRESHOLD,
            "N_QURAN_VERSES_EXPECTED": N_QURAN_VERSES_EXPECTED,
        },
        "per_corpus": per_corpus,
        "ranking": [{"rank": i + 1, "corpus": c,
                     "median_mdl_rate": row["median_mdl_rate"]}
                    for i, (c, row) in enumerate(ranked)],
        "headline": {
            "quran_rank":   quran_rank + 1,
            "quran_median_mdl_rate": quran_median,
            "next_corpus":  next_corpus,
            "next_median_mdl_rate":  next_median,
            "margin_pct":   margin * 100.0,
        },
        "audit_failures": audit_failures,
        "wall_time_s": time.time() - t0,
    }
    out_path = out_dir / f"{EXP}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] receipt: {out_path}")

    self_check_end(pre, exp_name=EXP)
    return 0 if verdict == "PASS_quran_strict_min_mdl" else 2


if __name__ == "__main__":
    sys.exit(main())
