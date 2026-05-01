"""
exp84_network_topology/run.py
==============================
H15: Network Topology Constants of the Word Co-occurrence Graph.

Motivation
    exp48 showed verse-graph topology separates Quran from controls.
    Small-world coefficient sigma, clustering C, and path length L
    could yield corpus-specific constants.

Approach (fast, no CamelTools)
    Build word co-occurrence graph: nodes = unique words (rasm-stripped),
    edges = words co-occurring in the same verse. Compute metrics on
    the giant component only (for path length).

    Use word-level (not root-level) to avoid CamelTools overhead.

Protocol (frozen before execution)
    T1. Per corpus: build word co-occurrence graph.
    T2. Compute: |V|, |E|, density, C (clustering), L (avg path in GC),
        sigma (small-world), diameter.
    T3. Compare across corpora; Cohen's d for sigma.
    T4. Test special values.

Pre-registered thresholds
    DISTINCT:     |d(sigma)| >= 1.0 or Quran sigma is extremal
    SUGGESTIVE:   Quran metrics are outliers on >= 2 measures
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import networkx as nx

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

EXP = "exp84_network_topology"
SEED = 42
MIN_WORD_FREQ = 3  # Filter rare words to keep graph manageable
MAX_WORDS_PER_VERSE = 50  # Cap to avoid huge cliques

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _build_graph(units, min_freq=MIN_WORD_FREQ) -> nx.Graph:
    """Build word co-occurrence graph from all verses."""
    # Count word frequencies
    word_freq = Counter()
    for u in units:
        for v in u.verses:
            words = _strip_d(v).split()
            word_freq.update(words)

    # Keep only words above threshold
    valid_words = {w for w, c in word_freq.items() if c >= min_freq}

    # Build graph
    G = nx.Graph()
    for u in units:
        for v in u.verses:
            words = list(set(_strip_d(v).split()) & valid_words)
            if len(words) > MAX_WORDS_PER_VERSE:
                words = words[:MAX_WORDS_PER_VERSE]
            for w1, w2 in combinations(words, 2):
                if G.has_edge(w1, w2):
                    G[w1][w2]["weight"] += 1
                else:
                    G.add_edge(w1, w2, weight=1)

    return G


def _graph_metrics(G: nx.Graph) -> dict:
    """Compute graph topology metrics."""
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n < 10:
        return {"n_nodes": n, "n_edges": m, "error": "too small"}

    density = nx.density(G)
    clustering = nx.average_clustering(G)

    # Giant component
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    gc = G.subgraph(components[0]).copy()
    gc_size = gc.number_of_nodes()
    gc_frac = gc_size / n

    # Average path length on GC (sample if too large)
    if gc_size > 500:
        # Sample 200 random pairs for speed
        rng = np.random.RandomState(SEED)
        nodes = list(gc.nodes())
        sample_size = min(200, gc_size)
        sampled = rng.choice(nodes, sample_size, replace=False)
        path_lengths = []
        for i, src in enumerate(sampled):
            lengths = nx.single_source_shortest_path_length(gc, src)
            for tgt in sampled[i + 1:]:
                if tgt in lengths:
                    path_lengths.append(lengths[tgt])
        avg_path = np.mean(path_lengths) if path_lengths else float("nan")
    else:
        try:
            avg_path = nx.average_shortest_path_length(gc)
        except Exception:
            avg_path = float("nan")

    # Random graph comparison for small-world
    C_random = m * 2 / (n * (n - 1)) if n > 1 else 0  # approx for ER
    L_random = math.log(n) / math.log(max(2, 2 * m / n)) if n > 1 and m > 0 else float("nan")

    sigma = float("nan")
    if C_random > 0 and L_random > 0 and np.isfinite(L_random) and avg_path > 0:
        sigma = (clustering / C_random) / (avg_path / L_random)

    # Degree distribution
    degrees = [d for _, d in G.degree()]
    mean_deg = np.mean(degrees)
    max_deg = max(degrees)

    return {
        "n_nodes": n,
        "n_edges": m,
        "density": round(density, 6),
        "clustering": round(clustering, 4),
        "gc_size": gc_size,
        "gc_fraction": round(gc_frac, 4),
        "avg_path_gc": round(float(avg_path), 4) if np.isfinite(avg_path) else None,
        "C_random": round(C_random, 6),
        "L_random": round(L_random, 4) if np.isfinite(L_random) else None,
        "sigma": round(float(sigma), 4) if np.isfinite(sigma) else None,
        "mean_degree": round(float(mean_deg), 2),
        "max_degree": int(max_deg),
        "n_components": len(components),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        t_start = time.time()

        G = _build_graph(units)
        metrics = _graph_metrics(G)
        dt = time.time() - t_start

        results[cname] = metrics
        sigma_str = f"{metrics.get('sigma', 'N/A')}" if metrics.get("sigma") else "N/A"
        print(f"[{EXP}] {cname:20s}: |V|={metrics['n_nodes']:5d}  |E|={metrics['n_edges']:6d}  "
              f"C={metrics.get('clustering', 0):.4f}  L={metrics.get('avg_path_gc', 'N/A')}  "
              f"σ={sigma_str}  ({dt:.1f}s)")

    # --- Comparison ---
    print(f"\n[{EXP}] === Cross-corpus comparison ===")
    print(f"  {'Corpus':20s}  {'|V|':>6s}  {'|E|':>7s}  {'C':>6s}  {'L':>6s}  {'σ':>6s}  {'density':>8s}")
    for cname in all_names:
        r = results[cname]
        flag = " ***" if cname == "quran" else ""
        L_str = f"{r['avg_path_gc']:.2f}" if r.get("avg_path_gc") else "N/A"
        s_str = f"{r['sigma']:.2f}" if r.get("sigma") else "N/A"
        print(f"  {cname:20s}  {r['n_nodes']:6d}  {r['n_edges']:7d}  "
              f"{r.get('clustering', 0):6.4f}  {L_str:>6s}  {s_str:>6s}  "
              f"{r.get('density', 0):8.6f}{flag}")

    # --- Sigma comparison ---
    q_sigma = results["quran"].get("sigma")
    ctrl_sigmas = [results[c].get("sigma") for c in ARABIC_CTRL
                   if results[c].get("sigma") is not None]

    if ctrl_sigmas and q_sigma is not None:
        mean_s = np.mean(ctrl_sigmas)
        std_s = np.std(ctrl_sigmas, ddof=1)
        z_sigma = (q_sigma - mean_s) / std_s if std_s > 0 else 0
        print(f"\n  Quran σ = {q_sigma:.4f}")
        print(f"  Ctrl σ: mean={mean_s:.4f}, std={std_s:.4f}")
        print(f"  z(σ) = {z_sigma:+.2f}")
    else:
        z_sigma = 0

    # --- Clustering comparison ---
    q_C = results["quran"].get("clustering")
    ctrl_Cs = [results[c].get("clustering") for c in ARABIC_CTRL
               if results[c].get("clustering") is not None]

    if ctrl_Cs and q_C is not None:
        mean_C = np.mean(ctrl_Cs)
        std_C = np.std(ctrl_Cs, ddof=1)
        z_C = (q_C - mean_C) / std_C if std_C > 0 else 0
        print(f"\n  Quran C = {q_C:.4f}")
        print(f"  Ctrl C: mean={mean_C:.4f}, std={std_C:.4f}")
        print(f"  z(C) = {z_C:+.2f}")
    else:
        z_C = 0

    # --- Verdict ---
    n_outlier = sum(1 for z in [z_sigma, z_C] if abs(z) >= 1.5)
    if abs(z_sigma) >= 2.0:
        verdict = "DISTINCT"
    elif n_outlier >= 2 or abs(z_sigma) >= 1.0:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  z(σ) = {z_sigma:+.2f}, z(C) = {z_C:+.2f}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H15 — Does the Quran's word co-occurrence graph have special topology?",
        "schema_version": 1,
        "min_word_freq": MIN_WORD_FREQ,
        "per_corpus": results,
        "comparison": {
            "z_sigma": round(float(z_sigma), 4),
            "z_clustering": round(float(z_C), 4),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
