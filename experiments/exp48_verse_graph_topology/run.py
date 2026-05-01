"""
exp48_verse_graph_topology/run.py
=================================
Port of DEEPSCAN Gem #4 — per-unit verse-graph topology.

Motivation
    The current R6 implementation in ``ultimate2_pipeline.run_R6`` uses
    word-as-node graphs, one-graph-per-corpus, and a custom one-level
    Louvain. It scores a 0.143 rank-ratio (below the 0.50 target).

    The gem that inspired R6 (archive:
    ``archive/pipeline2_backup/qsf_new_anomaly_tests.py`` TEST 3) used a
    **different** graph family: verse-as-node, one-graph-per-unit, with
    SIX topology metrics compared between Quran and pooled controls via
    Cohen d + Mann-Whitney p. That version reported d = +0.47,
    p = 5.2·10⁻⁷ on a legacy (pre-audit) Pipeline-2 checkpoint.

    This experiment re-runs the archive method on the current SHA-locked
    clean-data corpora. See ``notes.md`` for the pre-registered decision
    rule and the 6-D Hotelling follow-up.

Protocol (pre-registered; see notes.md)
    For every unit with >= 5 verses, build a verse-transition graph
        edge weight = 0.5 * EL_match + 0.5 * (1 - |Δw| / max(w_i, w_{i+1}))
    Compute on the undirected version:
        clustering, avg_path_norm, modularity, n_communities, bc_cv,
        small_world_sigma
    Pool per-corpus means; compute Cohen d + MW p for Quran vs pooled
    Arabic controls (hadith quarantined).

Decision rule (pre-registered)
    FIRE on a metric  = |d| > 0.3 AND p < 0.01
    PROMOTE           = n_fires >= 3 of 6

Reads (integrity-checked)
    phase_06_phi_m.pkl  →  CORPORA

Writes ONLY under results/experiments/exp48_verse_graph_topology/

Runtime estimate  ~5-15 min on a modern laptop (greedy_modularity_
communities dominates; per-unit graph is tiny).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

# AUDIT 2026-04-24: pattern matching an Arabic letter (+ standalone hamza).
# Used by _el_match to find the last true "letter" of a verse, bypassing
# editorial punctuation, digits, and combining marks that contaminate the
# raw-final-char implementation. Range covers the Arabic block U+0621-U+064A
# which includes all 28 base consonants plus alef/hamza variants.
_ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A]")

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

try:
    import networkx as nx  # noqa: E402
    HAS_NX = True
except ImportError:
    HAS_NX = False

try:
    from scipy import stats  # noqa: E402
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


EXP = "exp48_verse_graph_topology"
SEED = 42

# --- Pre-registered constants (notes.md) -------------------------------------
METRICS = [
    "clustering",
    "avg_path_norm",
    "modularity",
    "n_communities",
    "bc_cv",
    "small_world_sigma",
]
FIRE_D_THRESHOLD = 0.3
FIRE_P_THRESHOLD = 0.01
PROMOTE_N_FIRES = 3
MIN_VERSES = 5

# Hadith quarantine per v7.4 policy. These corpora enter the control pool
# for Quran-vs-controls comparison; any other corpus name in CORPORA is
# still reported but excluded from the pooled-control comparison.
CONTROL_CORPORA = {
    "poetry_abbasi", "poetry_jahili", "hindawi", "ksucca", "arabic_bible",
}


# --------------------------------------------------------------------------- #
# Edge-weight primitives                                                       #
# --------------------------------------------------------------------------- #
def _last_arabic_letter(s: str) -> str:
    """Return the last Arabic-letter character in ``s``, or '' if none.

    AUDIT 2026-04-24: replaces the ``a.strip()[-1]`` heuristic that folded
    punctuation/digits/diacritics into the "end letter". Non-letter final
    chars rates were: Quran 0%, poetry 49.8%, KSUCCA 54.6%, Bible 74.8%,
    Hindawi 17.5% — so the legacy _el_match was contaminated on controls.
    Legacy behaviour restored with env var QSF_EL_MATCH_LEGACY=1.
    """
    if not s:
        return ""
    matches = _ARABIC_LETTER_RE.findall(s)
    return matches[-1] if matches else ""


def _el_match(a: str, b: str) -> float:
    """1.0 if the last Arabic letter of a == last Arabic letter of b.

    AUDIT 2026-04-24: the original archive implementation used raw
    ``a.strip()[-1]`` which compared punctuation/diacritics on corpora
    where verses end in non-letter marks. This version uses the last
    Arabic-letter character explicitly. Set QSF_EL_MATCH_LEGACY=1 to
    restore the original raw-final-char comparison for exact
    reproducibility of the pre-audit published JSON.
    """
    a = (a or "").strip()
    b = (b or "").strip()
    if not a or not b:
        return 0.0
    if os.environ.get("QSF_EL_MATCH_LEGACY", "").strip() in ("1", "true", "True", "yes", "YES"):
        return 1.0 if a[-1] == b[-1] else 0.0
    la = _last_arabic_letter(a)
    lb = _last_arabic_letter(b)
    if not la or not lb:
        return 0.0
    return 1.0 if la == lb else 0.0


def _length_ratio(a: str, b: str) -> float:
    """1 - |Δw| / max(w_a, w_b, 1) — matches archive line 379."""
    wa = len(a.split())
    wb = len(b.split())
    return 1.0 - abs(wa - wb) / max(wa, wb, 1)


# --------------------------------------------------------------------------- #
# Per-unit graph topology                                                      #
# --------------------------------------------------------------------------- #
def _unit_metrics(verses: list[str]) -> dict[str, float] | None:
    """Compute the six graph-topology metrics for one unit.

    Returns None if the unit is too small (<MIN_VERSES) or networkx is
    unavailable. All failures inside the metric computation fall back to
    a finite default so partial results are still aggregable.
    """
    if not HAS_NX:
        return None
    n = len(verses)
    if n < MIN_VERSES:
        return None

    # Build directed graph with symmetric edges (archive convention).
    G = nx.DiGraph()
    for i in range(n):
        G.add_node(i)
    for i in range(n - 1):
        w = 0.5 * _el_match(verses[i], verses[i + 1]) \
            + 0.5 * _length_ratio(verses[i], verses[i + 1])
        G.add_edge(i, i + 1, weight=w)
        G.add_edge(i + 1, i, weight=w)

    Gu = G.to_undirected()
    out: dict[str, float] = {}

    # clustering
    try:
        out["clustering"] = float(nx.average_clustering(Gu, weight="weight"))
    except Exception:
        out["clustering"] = 0.0

    # avg_path
    try:
        if nx.is_connected(Gu):
            avg_path = nx.average_shortest_path_length(Gu)
        else:
            largest = max(nx.connected_components(Gu), key=len)
            avg_path = nx.average_shortest_path_length(Gu.subgraph(largest))
    except Exception:
        avg_path = float(n)
    out["avg_path_norm"] = float(avg_path / n) if n else 0.0

    # modularity + n_communities (greedy community detection)
    try:
        communities = list(nx.community.greedy_modularity_communities(Gu))
        out["modularity"] = float(nx.community.modularity(Gu, communities))
        out["n_communities"] = float(len(communities))
    except Exception:
        out["modularity"] = 0.0
        out["n_communities"] = 1.0

    # bc_cv
    try:
        bc = list(nx.betweenness_centrality(Gu, weight="weight").values())
        bc_arr = np.asarray(bc, dtype=float)
        mean_bc = float(bc_arr.mean())
        out["bc_cv"] = float(bc_arr.std() / max(mean_bc, 1e-10))
    except Exception:
        out["bc_cv"] = 0.0

    # small-world sigma (C/C_rand) * (L_rand/L)
    # AUDIT-FIX A2: l_rand fallback set to n/3 to match the archive
    # reference implementation (qsf_new_anomaly_tests.py:420). Without this,
    # rare disconnected Watts-Strogatz samples diverge from the d=0.47 baseline.
    try:
        Gr = nx.watts_strogatz_graph(n, 2, 0.5, seed=SEED)
        c_rand = nx.average_clustering(Gr)
        if nx.is_connected(Gr):
            l_rand = nx.average_shortest_path_length(Gr)
        else:
            l_rand = n / 3.0   # archive fallback (A2)
        if c_rand > 0 and avg_path > 0:
            out["small_world_sigma"] = float(
                (out["clustering"] / c_rand) * (l_rand / avg_path)
            )
        else:
            out["small_world_sigma"] = 0.0
    except Exception:
        out["small_world_sigma"] = 0.0

    return out


# --------------------------------------------------------------------------- #
# Stats                                                                        #
# --------------------------------------------------------------------------- #
def _cohens_d(a: list[float], b: list[float]) -> float:
    """Pooled-SD Cohen's d, ddof=1 (matches v7.4 convention)."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    var_a = aa.var(ddof=1)
    var_b = bb.var(ddof=1)
    pooled = np.sqrt(
        ((len(aa) - 1) * var_a + (len(bb) - 1) * var_b)
        / (len(aa) + len(bb) - 2)
    )
    if pooled <= 0:
        return 0.0
    return float((aa.mean() - bb.mean()) / pooled)


def _mw_p(a: list[float], b: list[float]) -> float:
    """Two-sided Mann-Whitney U p-value. Falls back to 1.0 on failure."""
    if not HAS_SCIPY or len(a) < 2 or len(b) < 2:
        return 1.0
    try:
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        return float(p)
    except Exception:
        return 1.0


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def _unit_verses(u) -> list[str]:
    """Extract a list[str] of verses from a unit, defensively."""
    vs = getattr(u, "verses", None)
    if vs is None:
        return []
    if isinstance(vs, (list, tuple)):
        return [str(v) for v in vs]
    if isinstance(vs, str):
        return vs.splitlines()
    try:
        return [str(v) for v in vs]
    except Exception:
        return []


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    if not HAS_NX:
        raise RuntimeError(
            "networkx is required for exp48. Install with: "
            "pip install networkx>=3.0  (or re-run pip install -r requirements.txt)"
        )

    # --- Load read-only pinned checkpoint ---
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    corpus_names = sorted(CORPORA.keys())
    print(f"[{EXP}] corpora: {corpus_names}")

    # --- Per-unit metrics, grouped by corpus ---
    per_corpus: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    per_corpus_n_units_used: dict[str, int] = defaultdict(int)
    per_corpus_n_units_skipped: dict[str, int] = defaultdict(int)

    for name in corpus_names:
        units = CORPORA.get(name, []) or []
        for u in units:
            vs = _unit_verses(u)
            m = _unit_metrics(vs)
            if m is None:
                per_corpus_n_units_skipped[name] += 1
                continue
            for k, v in m.items():
                per_corpus[name][k].append(float(v))
            per_corpus_n_units_used[name] += 1
        used = per_corpus_n_units_used[name]
        skipped = per_corpus_n_units_skipped[name]
        print(f"  {name:20s}: used={used:>4d}  skipped={skipped:>4d}")

    # --- Per-corpus means ---
    corpus_means: dict[str, dict[str, float]] = {}
    for name, metric_lists in per_corpus.items():
        corpus_means[name] = {
            k: float(np.mean(vals)) if vals else 0.0
            for k, vals in metric_lists.items()
        }

    # --- Pre-registered contrasts: Quran vs pooled Arabic controls ---
    # AUDIT-FIX A3: also compute per-corpus pair-wise d and p so the Quran's
    # rank across individual controls is visible (archive reported ranks too).
    # Additive: does NOT affect the pre-registered decision rule.
    contrasts: dict[str, dict] = {}
    for metric in METRICS:
        q_vals = list(per_corpus.get("quran", {}).get(metric, []))
        ctrl_vals: list[float] = []
        ctrl_breakdown: dict[str, int] = {}
        per_corpus_contrast: dict[str, dict[str, float]] = {}
        for name, metric_lists in per_corpus.items():
            if name == "quran":
                continue
            if name not in CONTROL_CORPORA:
                continue
            vals = list(metric_lists.get(metric, []))
            ctrl_vals.extend(vals)
            ctrl_breakdown[name] = len(vals)
            # Per-corpus d, p, and rank signal (additive, A3)
            if q_vals and vals:
                pc_d = _cohens_d(q_vals, vals)
                pc_p = _mw_p(q_vals, vals)
                per_corpus_contrast[name] = {
                    "n": len(vals),
                    "mean": float(np.mean(vals)),
                    "cohens_d_vs_quran": float(pc_d),
                    "mw_p_vs_quran": float(pc_p),
                }
        # Compute Quran's rank among {Quran} U {controls} on the metric mean.
        # Rank 1 = highest mean. Rank 1/N means Quran is the extreme.
        means_for_rank = [(float(np.mean(q_vals)) if q_vals else 0.0, "quran")]
        for name in sorted(ctrl_breakdown):
            vals = per_corpus.get(name, {}).get(metric, [])
            means_for_rank.append(
                (float(np.mean(vals)) if vals else 0.0, name)
            )
        means_for_rank.sort(key=lambda x: x[0], reverse=True)
        quran_rank_high = next(
            (i + 1 for i, (_, n_) in enumerate(means_for_rank) if n_ == "quran"),
            0,
        )
        d = _cohens_d(q_vals, ctrl_vals) if q_vals and ctrl_vals else 0.0
        p = _mw_p(q_vals, ctrl_vals)       if q_vals and ctrl_vals else 1.0
        fires = (abs(d) > FIRE_D_THRESHOLD) and (p < FIRE_P_THRESHOLD)
        contrasts[metric] = {
            "n_quran": len(q_vals),
            "n_ctrl": len(ctrl_vals),
            "ctrl_breakdown": ctrl_breakdown,
            "quran_mean": float(np.mean(q_vals)) if q_vals else 0.0,
            "ctrl_mean":  float(np.mean(ctrl_vals)) if ctrl_vals else 0.0,
            "cohens_d": float(d),
            "mw_p": float(p),
            "fires_prereg": bool(fires),
            "quran_rank_high_mean": quran_rank_high,
            "n_corpora_in_ranking": len(means_for_rank),
            "per_corpus_contrast": per_corpus_contrast,
        }

    n_fires = sum(1 for c in contrasts.values() if c["fires_prereg"])
    # AUDIT-FIX A4: independence-assumed joint p (sanity check, not a decision rule).
    # Under H0 of per-metric p iid uniform[0,1], P(>=k of 6 below 0.01) follows
    # Binomial(6, 0.01).sf(k-1). For k=3: P ~= 2e-5. Additive transparency only.
    firing_ps = [c["mw_p"] for c in contrasts.values() if c["fires_prereg"]]
    if HAS_SCIPY and firing_ps:
        try:
            from scipy.stats import binom
            joint_p_independence = float(
                binom.sf(n_fires - 1, len(METRICS), FIRE_P_THRESHOLD)
            )
        except Exception:
            joint_p_independence = -1.0
    else:
        joint_p_independence = -1.0
    verdict_before_6d = (
        "PROMOTE" if n_fires >= PROMOTE_N_FIRES else "NOT PROMOTED"
    )
    strongest_metric = max(
        contrasts.keys(), key=lambda m: abs(contrasts[m]["cohens_d"])
    ) if contrasts else None

    # --- Compose report ---
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "hadith_policy": "quarantined (not in control pool)",
        "prereg": {
            "metrics": METRICS,
            "fire_rule": f"|d| > {FIRE_D_THRESHOLD} AND p < {FIRE_P_THRESHOLD}",
            "promote_rule": f"n_fires >= {PROMOTE_N_FIRES} of {len(METRICS)}",
            "min_verses_per_unit": MIN_VERSES,
            "control_corpora": sorted(CONTROL_CORPORA),
        },
        "corpus_means": corpus_means,
        "n_units_used_per_corpus": dict(per_corpus_n_units_used),
        "n_units_skipped_per_corpus": dict(per_corpus_n_units_skipped),
        "contrasts_quran_vs_pooled_ctrl": contrasts,
        "n_metrics_fired": n_fires,
        "strongest_metric": strongest_metric,
        "strongest_d": (
            contrasts[strongest_metric]["cohens_d"] if strongest_metric else 0.0
        ),
        "verdict_before_6d_test": verdict_before_6d,
        "joint_p_independence_sanity": joint_p_independence,
        "caveats": {
            "A1_mild_circularity": (
                "Edge weights use EL_match (blessed D03) and word-length ratio "
                "(related to D01 VL_CV). Graph metric is NOT fully orthogonal "
                "to Phi_M by construction. The pre-registered 6-D Hotelling "
                "rule T^2_6D >= 4269 is the guard against redundant features."
            ),
            "A3_sample_size_asymmetry": (
                "Pooled control pool is dominated by hindawi (~7k units) vs "
                "Quran (114). Per-corpus contrasts in contrasts[metric]"
                "['per_corpus_contrast'] and Quran rank in "
                "contrasts[metric]['quran_rank_high_mean'] let you see the "
                "Quran's position without the size artefact."
            ),
            "A4_family_wise_error": (
                "Per-metric fire rule p<0.01 is NOT Bonferroni corrected. "
                "Composite n_fires>=3 is strict: under independence, "
                "joint P ~= 2e-5 (see joint_p_independence_sanity). "
                "Under realistic correlation between graph metrics, joint P "
                "is larger; treat joint_p as a loose upper bound on significance."
            ),
            "A5_min_verses_filter": (
                f"Units with <{MIN_VERSES} verses are skipped. "
                "This disproportionately removes short Quran surahs (Al-Kawthar, "
                "Al-Ikhlas, Al-Asr, etc.). Per-corpus skip counts above."
            ),
            "A6_strongest_metric_is_post_hoc": (
                "strongest_metric is chosen AFTER seeing the data. The 6-D "
                "Hotelling rule T^2_6D >= 4269 is the guard: even a cherry-"
                "picked metric cannot game the T^2 threshold because adding "
                "a redundant column cannot push T^2 past the 6/5 factor."
            ),
        },
        "next_step_if_promoted": (
            "Compute 6-D Hotelling T² with the strongest metric added to the "
            "5-D Phi_M feature vector on Band-A matched data (same Σ-"
            "regularisation 1e-6·I). PROMOTE iff T²_6D >= 5-D T² × 6/5 = 4269. "
            "Otherwise label SIGNIFICANT BUT REDUNDANT."
        ),
        "reference": {
            "original_archive": (
                "archive/pipeline2_backup/qsf_new_anomaly_tests.py TEST 3"
            ),
            "ranked_findings_row": 33,
            "deepscan_reference": "docs/DEEPSCAN_ULTIMATE_FINDINGS.md §3.1 GEM 4",
        },
        "runtime_seconds": round(time.time() - t0, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console summary ---
    print(f"\n[{EXP}] DONE in {report['runtime_seconds']:.1f}s")
    print(f"[{EXP}] Quran vs pooled Arabic controls (hadith quarantined):")
    for m, c in contrasts.items():
        flag = "FIRE" if c["fires_prereg"] else "----"
        print(
            f"   {m:<20s}  n_Q={c['n_quran']:>4d}  n_ctrl={c['n_ctrl']:>4d}  "
            f"d={c['cohens_d']:+.3f}  p={c['mw_p']:.2e}  {flag}"
        )
    print(
        f"[{EXP}] n_fires = {n_fires}/{len(METRICS)}  "
        f"verdict = {verdict_before_6d}  "
        f"strongest = {strongest_metric} (d={report['strongest_d']:+.3f})"
    )

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
