"""
exp100_verse_precision/run.py
==============================
Re-test C4 ("verses made precise", Q 11:1) using two metrics:
  Metric A — Root density (unique roots / words per verse)
  Metric B — Predictive tightness (within-verse bigram surprisal)

Pre-registered in PREREG.md (frozen 2026-04-27, v7.9-cand patch H pre-V2).

Reads:  phase_06_phi_m.pkl :: state[CORPORA]
Writes: results/experiments/exp100_verse_precision/exp100_verse_precision.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import _strip_d  # noqa: E402
from src import roots as _rc  # noqa: E402

# ---------------------------------------------------------------------------
# Constants (frozen per PREREG §3)
# ---------------------------------------------------------------------------
EXP = "exp100_verse_precision"
CORPORA_NAMES = ["quran", "poetry_jahili", "poetry_islami",
                 "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
MIN_VERSES = 2
MIN_WORDS_PER_V = 3
SEED = 100000
BIGRAM_SMOOTHING = 1e-8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _words(verse: str) -> list[str]:
    """Tokenise a verse into stripped, non-empty words."""
    return [w for w in _strip_d(verse).split() if w]


# ---------------------------------------------------------------------------
# Metric A: Root density
# ---------------------------------------------------------------------------
def _roots_of_words(words: list[str]) -> list[str]:
    """Return list of roots (one per word); '' if CamelTools has no analysis."""
    return [_rc.primary_root_normalized(w) for w in words]


def root_density_verse(words: list[str]) -> float | None:
    """RD(v) = n_unique_roots / n_words.
    <unk> (empty root) excluded from numerator but counted in denominator."""
    if len(words) < MIN_WORDS_PER_V:
        return None
    roots = _roots_of_words(words)
    n_total = len(words)
    known = [r for r in roots if r]
    n_unique = len(set(known))
    return n_unique / n_total if n_total > 0 else None


def root_density_unit(verses: list[str]) -> float | None:
    """Average RD across verses of a unit."""
    vals = []
    for v in verses:
        ws = _words(v)
        rd = root_density_verse(ws)
        if rd is not None:
            vals.append(rd)
    return float(np.mean(vals)) if vals else None


# ---------------------------------------------------------------------------
# Metric B: Predictive tightness (within-corpus bigram surprisal)
# ---------------------------------------------------------------------------
def train_bigram_model(all_verses: list[str]) -> dict[str, Counter]:
    """Train a word-level bigram model from all verses."""
    model: dict[str, Counter] = defaultdict(Counter)
    for v in all_verses:
        ws = _words(v)
        if len(ws) < 2:
            continue
        for w1, w2 in zip(ws[:-1], ws[1:]):
            model[w1][w2] += 1
    return dict(model)


def bigram_surprisal_verse(words: list[str],
                           model: dict[str, Counter],
                           vocab_size: int) -> float | None:
    """Mean surprisal: S(v) = -1/(n-1) Σ log P(w_i | w_{i-1})."""
    if len(words) < MIN_WORDS_PER_V:
        return None
    n = len(words)
    log_sum = 0.0
    for w1, w2 in zip(words[:-1], words[1:]):
        ctx = model.get(w1)
        if ctx is None:
            p = BIGRAM_SMOOTHING
        else:
            total = sum(ctx.values())
            count = ctx.get(w2, 0)
            p = (count + BIGRAM_SMOOTHING) / (total + BIGRAM_SMOOTHING * vocab_size)
        log_sum += math.log2(p)
    return -log_sum / (n - 1)


def surprisal_unit(verses: list[str],
                   model: dict[str, Counter],
                   vocab_size: int) -> float | None:
    """Average per-verse surprisal across a unit."""
    vals = []
    for v in verses:
        ws = _words(v)
        s = bigram_surprisal_verse(ws, model, vocab_size)
        if s is not None:
            vals.append(s)
    return float(np.mean(vals)) if vals else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre_check = self_check_begin()
    t0 = time.time()

    prereg_hash = sha256_of(_HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash}")

    audit_failures: list[str] = []

    # -------------------------------------------------------------------
    # Load corpus data
    # -------------------------------------------------------------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl …")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    corpus_units: dict[str, list] = {}
    for cn in CORPORA_NAMES:
        units = CORPORA.get(cn, [])
        # Filter units with enough verses
        filtered = [u for u in units if len(u.verses) >= MIN_VERSES]
        corpus_units[cn] = filtered
        print(f"[{EXP}]   {cn}: {len(filtered)} units "
              f"({len(units)} raw, {len(units)-len(filtered)} dropped)")
        if len(filtered) < 10:
            audit_failures.append(f"A1: {cn} has only {len(filtered)} units (< 10)")

    # -------------------------------------------------------------------
    # Pre-warm CamelTools root cache for all words
    # -------------------------------------------------------------------
    print(f"[{EXP}] Collecting vocabulary for root cache …")
    all_words: set[str] = set()
    for cn, units in corpus_units.items():
        for u in units:
            for v in u.verses:
                all_words.update(_words(v))
    print(f"[{EXP}] Warming root cache for {len(all_words):,} unique words …")
    _rc.warm_cache(list(all_words), verbose=True)

    # -------------------------------------------------------------------
    # Audit A2: root extraction coverage
    # -------------------------------------------------------------------
    total_words = 0
    covered_words = 0
    for w in all_words:
        total_words += 1
        roots, n = _rc.roots_for(w)
        if n > 0:
            covered_words += 1
    coverage = covered_words / total_words if total_words > 0 else 0
    print(f"[{EXP}] A2: root coverage = {coverage:.4f} "
          f"({covered_words:,}/{total_words:,})")
    if coverage < 0.95:
        audit_failures.append(f"A2: root coverage {coverage:.4f} < 0.95")

    # -------------------------------------------------------------------
    # Metric A: Root density per corpus
    # -------------------------------------------------------------------
    print(f"[{EXP}] Computing Metric A (root density) …")
    rd_by_corpus: dict[str, list[float]] = {}
    for cn, units in corpus_units.items():
        rd_vals = []
        for u in units:
            rd = root_density_unit(u.verses)
            if rd is not None:
                rd_vals.append(rd)
        rd_by_corpus[cn] = rd_vals
        med = float(np.median(rd_vals)) if rd_vals else float("nan")
        print(f"[{EXP}]   {cn}: median RD = {med:.4f} (n={len(rd_vals)})")

    # Rank by median (higher = more precise = rank 1)
    rd_medians = {cn: float(np.median(vals)) if vals else 0.0
                  for cn, vals in rd_by_corpus.items()}
    rd_ranked = sorted(rd_medians.items(), key=lambda x: -x[1])
    rd_ranks = {cn: i + 1 for i, (cn, _) in enumerate(rd_ranked)}

    print(f"[{EXP}] Metric A ranks (higher RD = rank 1):")
    for cn, med in rd_ranked:
        print(f"[{EXP}]   #{rd_ranks[cn]}  {cn}: {med:.4f}")

    # -------------------------------------------------------------------
    # Metric B: Predictive tightness per corpus
    # -------------------------------------------------------------------
    print(f"[{EXP}] Computing Metric B (predictive tightness) …")
    surp_by_corpus: dict[str, list[float]] = {}
    for cn, units in corpus_units.items():
        # Train bigram model on ALL verses of this corpus
        all_verses_corpus = []
        for u in units:
            all_verses_corpus.extend(u.verses)
        model = train_bigram_model(all_verses_corpus)
        vocab = set()
        for v in all_verses_corpus:
            vocab.update(_words(v))
        vocab_size = len(vocab)

        surp_vals = []
        for u in units:
            s = surprisal_unit(u.verses, model, vocab_size)
            if s is not None:
                surp_vals.append(s)
        surp_by_corpus[cn] = surp_vals
        med = float(np.median(surp_vals)) if surp_vals else float("nan")
        print(f"[{EXP}]   {cn}: median surprisal = {med:.4f} bits (n={len(surp_vals)})")

    # Rank by median (lower surprisal = more tightly constrained = rank 1)
    surp_medians = {cn: float(np.median(vals)) if vals else float("inf")
                    for cn, vals in surp_by_corpus.items()}
    surp_ranked = sorted(surp_medians.items(), key=lambda x: x[1])
    surp_ranks = {cn: i + 1 for i, (cn, _) in enumerate(surp_ranked)}

    print(f"[{EXP}] Metric B ranks (lower surprisal = rank 1):")
    for cn, med in surp_ranked:
        print(f"[{EXP}]   #{surp_ranks[cn]}  {cn}: {med:.4f}")

    # -------------------------------------------------------------------
    # Audit A3: corpus unit/verse counts
    # -------------------------------------------------------------------
    corpus_stats = {}
    for cn, units in corpus_units.items():
        n_units = len(units)
        n_verses = sum(len(u.verses) for u in units)
        corpus_stats[cn] = {"n_units": n_units, "n_verses": n_verses}

    # -------------------------------------------------------------------
    # Audit A4: Cohen's d for each metric
    # -------------------------------------------------------------------
    def cohens_d(a: list[float], b: list[float]) -> float:
        if len(a) < 2 or len(b) < 2:
            return float("nan")
        na, nb = np.array(a), np.array(b)
        pooled_std = np.sqrt(((len(na)-1)*na.var(ddof=1) +
                              (len(nb)-1)*nb.var(ddof=1)) /
                             (len(na) + len(nb) - 2))
        if pooled_std == 0:
            return float("inf")
        return float((na.mean() - nb.mean()) / pooled_std)

    # RD: Quran vs next-ranked
    quran_rd_rank = rd_ranks["quran"]
    if quran_rd_rank == 1 and len(rd_ranked) > 1:
        next_cn = rd_ranked[1][0]
        rd_d = cohens_d(rd_by_corpus["quran"], rd_by_corpus[next_cn])
    else:
        # Find rank-1 corpus for comparison
        rank1_cn = rd_ranked[0][0]
        rd_d = cohens_d(rd_by_corpus["quran"], rd_by_corpus[rank1_cn])

    # Surprisal: Quran vs next-ranked
    quran_surp_rank = surp_ranks["quran"]
    if quran_surp_rank == 1 and len(surp_ranked) > 1:
        next_cn = surp_ranked[1][0]
        surp_d = cohens_d(surp_by_corpus["quran"], surp_by_corpus[next_cn])
    else:
        rank1_cn = surp_ranked[0][0]
        surp_d = cohens_d(surp_by_corpus["quran"], surp_by_corpus[rank1_cn])

    print(f"[{EXP}] A4: Cohen's d — RD: {rd_d:.3f}, Surprisal: {surp_d:.3f}")

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    quran_rd_rank = rd_ranks["quran"]
    quran_surp_rank = surp_ranks["quran"]
    rd_pass = (quran_rd_rank == 1)
    surp_pass = (quran_surp_rank == 1)

    # Self-check
    post_check = self_check_end(pre_check, EXP)
    if post_check.get("drift"):
        audit_failures.append(f"self_check: {post_check['drift']}")

    if audit_failures:
        verdict = f"FAIL_audit_{'_'.join(a.split(':')[0] for a in audit_failures)}"
    elif rd_pass and surp_pass:
        verdict = "PASS_H55_both_metrics"
    elif rd_pass or surp_pass:
        verdict = "PARTIAL_one_metric"
    else:
        verdict = "FAIL_both_metrics"

    print(f"\n[{EXP}] === RESULTS ===")
    print(f"  Quran RD rank       = {quran_rd_rank}/7  {'PASS' if rd_pass else 'FAIL'}")
    print(f"  Quran surprisal rank= {quran_surp_rank}/7  {'PASS' if surp_pass else 'FAIL'}")
    print(f"  verdict = {verdict}")

    # -------------------------------------------------------------------
    # Write receipt
    # -------------------------------------------------------------------
    record = {
        "experiment": EXP,
        "prereg_sha256": prereg_hash,
        "hypothesis": "H55",
        "metric_A_root_density": {
            "medians": {cn: rd_medians[cn] for cn in CORPORA_NAMES},
            "ranks": {cn: rd_ranks[cn] for cn in CORPORA_NAMES},
            "quran_rank": quran_rd_rank,
            "cohens_d_vs_next": rd_d,
        },
        "metric_B_surprisal": {
            "medians": {cn: surp_medians[cn] for cn in CORPORA_NAMES},
            "ranks": {cn: surp_ranks[cn] for cn in CORPORA_NAMES},
            "quran_rank": quran_surp_rank,
            "cohens_d_vs_next": surp_d,
        },
        "corpus_stats": corpus_stats,
        "audit": {
            "a2_root_coverage": coverage,
            "failures": audit_failures,
        },
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }

    receipt_path = out / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] receipt: {receipt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
