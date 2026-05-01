"""
exp51_exp48_sensitivity_islami/run.py
=====================================
Sensitivity re-run of exp48 verse-graph topology with poetry_islami
added to the control pool.

Motivation
    The exp48 pre-registration froze the control pool to
        {poetry_abbasi, poetry_jahili, hindawi, ksucca, arabic_bible}
    which accidentally omitted `poetry_islami` even though
    `_build.py::Cell 22` treats it as a first-class Arabic control
    (see `ARABIC_CTRL_POOL`). The headline exp48 result (n_communities
    d = +0.937, 4 metrics fired, verdict PROMOTE) stands as the
    locked pre-registered headline. This experiment is a transparency
    sensitivity test: would adding the missing corpus flip the
    verdict?

    Pre-registered DECISION RULE (frozen before any run):
      * If the verdict under the extended pool = PROMOTE and
        |strongest_d_ext - 0.937| < 0.30  =>  STABLE.
      * If verdict changes to NOT PROMOTED or strongest_d moves
        >= 0.30 in either direction  =>  FRAGILE (paper MUST
        disclose the softening / tightening).

Protocol
    1. Load phase_06_phi_m CORPORA (same SHA-pinned source exp48
       uses).
    2. Recompute the six per-unit graph metrics for every corpus
       (same code as exp48._unit_metrics).
    3. Pool Arabic controls as {poetry_abbasi, poetry_jahili,
       poetry_islami, hindawi, ksucca, arabic_bible} -- poetry_islami
       ADDED. Compute Cohen d + MW p vs Quran per metric.
    4. Apply exp48's pre-registered FIRE / PROMOTE rule unchanged.
    5. Compute a side-by-side delta vs exp48 headline.

Reads (integrity-checked)
    phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp51_exp48_sensitivity_islami/

Runtime ~5-15 min (same as exp48; greedy_modularity_communities
dominates).
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

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
from experiments.exp48_verse_graph_topology.run import (  # noqa: E402
    METRICS,
    FIRE_D_THRESHOLD,
    FIRE_P_THRESHOLD,
    PROMOTE_N_FIRES,
    MIN_VERSES,
    _unit_metrics,
    _unit_verses,
    _cohens_d,
    _mw_p,
)

try:
    from scipy.stats import binom  # noqa: E402
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


EXP = "exp51_exp48_sensitivity_islami"
SEED = 42

# exp48 pre-registered control pool (reproduced here for the diff)
EXP48_PREREG_POOL = {
    "poetry_abbasi", "poetry_jahili", "hindawi", "ksucca", "arabic_bible",
}
# Extended pool = exp48 pre-reg + poetry_islami.
EXTENDED_POOL = EXP48_PREREG_POOL | {"poetry_islami"}

# exp48 locked headline (from
# results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.json)
EXP48_HEADLINE = {
    "verdict": "PROMOTE",
    "n_fires": 4,
    "strongest_metric": "n_communities",
    "strongest_d": 0.936693591090282,
    "fires_per_metric": {
        "clustering": False,
        "avg_path_norm": True,
        "modularity": True,
        "n_communities": True,
        "bc_cv": True,
        "small_world_sigma": False,
    },
    "d_per_metric": {
        "clustering": 0.0,
        "avg_path_norm": -0.5499983756570271,
        "modularity": 0.6720875125496218,
        "n_communities": 0.936693591090282,
        "bc_cv": -0.4998875493371675,
        "small_world_sigma": 0.0,
    },
}
STABLE_ABS_DELTA_D = 0.30  # pre-registered wiggle room on strongest_d


def _contrasts(
    per_corpus: dict[str, dict[str, list[float]]],
    control_pool: set[str],
) -> tuple[dict, int]:
    """exp48's Quran-vs-pooled-controls contrast, parameterised by
    the control pool. Returns (contrasts_dict, n_fires)."""
    contrasts: dict[str, dict] = {}
    q_metric_lists = per_corpus.get("quran", {})
    for metric in METRICS:
        q_vals = list(q_metric_lists.get(metric, []))
        ctrl_vals: list[float] = []
        ctrl_breakdown: dict[str, int] = {}
        per_corpus_contrast: dict[str, dict[str, float]] = {}
        for name, ml in per_corpus.items():
            if name == "quran" or name not in control_pool:
                continue
            vals = list(ml.get(metric, []))
            ctrl_vals.extend(vals)
            ctrl_breakdown[name] = len(vals)
            if q_vals and vals:
                per_corpus_contrast[name] = {
                    "n": len(vals),
                    "mean": float(np.mean(vals)),
                    "cohens_d_vs_quran": _cohens_d(q_vals, vals),
                    "mw_p_vs_quran": _mw_p(q_vals, vals),
                }
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
            "per_corpus_contrast": per_corpus_contrast,
        }
    n_fires = sum(1 for c in contrasts.values() if c["fires_prereg"])
    return contrasts, n_fires


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    corpus_names = sorted(CORPORA.keys())
    print(f"[{EXP}] corpora: {corpus_names}")
    print(f"[{EXP}] exp48 pre-reg pool:  {sorted(EXP48_PREREG_POOL)}")
    print(f"[{EXP}] extended pool (+islami): {sorted(EXTENDED_POOL)}")

    # --- Per-unit metrics (same as exp48) ---
    per_corpus: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))
    n_used: dict[str, int] = defaultdict(int)
    n_skip: dict[str, int] = defaultdict(int)
    for name in corpus_names:
        units = CORPORA.get(name, []) or []
        for u in units:
            vs = _unit_verses(u)
            m = _unit_metrics(vs)
            if m is None:
                n_skip[name] += 1
                continue
            for k, v in m.items():
                per_corpus[name][k].append(float(v))
            n_used[name] += 1
        print(f"[{EXP}]   {name:20s}: used={n_used[name]:>4d}  "
              f"skipped={n_skip[name]:>4d}")

    # --- Per-corpus means (for reference) ---
    corpus_means: dict[str, dict[str, float]] = {}
    for name, metric_lists in per_corpus.items():
        corpus_means[name] = {k: float(np.mean(vals)) if vals else 0.0
                              for k, vals in metric_lists.items()}

    # --- Contrasts under both pools ---
    contrasts_prereg, n_fires_prereg = _contrasts(per_corpus, EXP48_PREREG_POOL)
    contrasts_ext, n_fires_ext = _contrasts(per_corpus, EXTENDED_POOL)

    def _verdict(n_fires: int) -> str:
        return "PROMOTE" if n_fires >= PROMOTE_N_FIRES else "NOT PROMOTED"
    verdict_prereg = _verdict(n_fires_prereg)
    verdict_ext = _verdict(n_fires_ext)

    strongest_prereg = max(
        contrasts_prereg.keys(),
        key=lambda m: abs(contrasts_prereg[m]["cohens_d"])
    ) if contrasts_prereg else None
    strongest_ext = max(
        contrasts_ext.keys(),
        key=lambda m: abs(contrasts_ext[m]["cohens_d"])
    ) if contrasts_ext else None
    strongest_d_prereg = (
        contrasts_prereg[strongest_prereg]["cohens_d"] if strongest_prereg else 0.0)
    strongest_d_ext = (
        contrasts_ext[strongest_ext]["cohens_d"] if strongest_ext else 0.0)

    # --- Joint p sanity (unchanged formula from exp48) ---
    if _HAS_SCIPY and n_fires_ext > 0:
        joint_p_ext = float(
            binom.sf(n_fires_ext - 1, len(METRICS), FIRE_P_THRESHOLD))
    else:
        joint_p_ext = -1.0

    # --- Diff report: exp48 pre-reg vs extended ---
    delta_strongest = strongest_d_ext - EXP48_HEADLINE["strongest_d"]
    delta_per_metric: dict[str, dict[str, float]] = {}
    for metric in METRICS:
        prereg_d = EXP48_HEADLINE["d_per_metric"].get(metric, 0.0)
        ext_d = contrasts_ext[metric]["cohens_d"]
        delta_per_metric[metric] = {
            "d_exp48_prereg": prereg_d,
            "d_extended_pool": ext_d,
            "delta_d": ext_d - prereg_d,
            "fires_exp48_prereg": bool(
                EXP48_HEADLINE["fires_per_metric"].get(metric, False)),
            "fires_extended_pool": bool(contrasts_ext[metric]["fires_prereg"]),
        }

    stability_verdict = (
        "STABLE"
        if (verdict_ext == EXP48_HEADLINE["verdict"]
            and abs(delta_strongest) < STABLE_ABS_DELTA_D)
        else "FRAGILE"
    )

    # --- Report ---
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "prereg": {
            "exp48_prereg_pool": sorted(EXP48_PREREG_POOL),
            "extended_pool": sorted(EXTENDED_POOL),
            "added_corpus": "poetry_islami",
            "fire_rule": f"|d| > {FIRE_D_THRESHOLD} AND p < {FIRE_P_THRESHOLD}",
            "promote_rule": f"n_fires >= {PROMOTE_N_FIRES} of {len(METRICS)}",
            "stability_rule": (
                f"STABLE iff verdict unchanged AND "
                f"|delta_strongest_d| < {STABLE_ABS_DELTA_D}"
            ),
            "hadith_policy": "quarantined (not in control pool)",
            "min_verses_per_unit": MIN_VERSES,
        },
        "exp48_locked_headline": EXP48_HEADLINE,
        "under_prereg_pool": {
            "n_fires": n_fires_prereg,
            "verdict": verdict_prereg,
            "strongest_metric": strongest_prereg,
            "strongest_d": strongest_d_prereg,
            "contrasts": contrasts_prereg,
        },
        "under_extended_pool": {
            "n_fires": n_fires_ext,
            "verdict": verdict_ext,
            "strongest_metric": strongest_ext,
            "strongest_d": strongest_d_ext,
            "contrasts": contrasts_ext,
            "joint_p_independence_sanity": joint_p_ext,
        },
        "diff_prereg_vs_extended": {
            "verdict_unchanged": verdict_ext == EXP48_HEADLINE["verdict"],
            "delta_strongest_d": float(delta_strongest),
            "per_metric": delta_per_metric,
        },
        "stability_verdict": stability_verdict,
        "corpus_means": corpus_means,
        "n_units_used_per_corpus": dict(n_used),
        "n_units_skipped_per_corpus": dict(n_skip),
        "reference": {
            "parent_experiment": "exp48_verse_graph_topology",
            "parent_result": (
                "results/experiments/exp48_verse_graph_topology/"
                "exp48_verse_graph_topology.json"
            ),
            "input_checkpoint": "phase_06_phi_m.pkl",
        },
        "notes": (
            "This is a sensitivity appendix, NOT a rebless of exp48. "
            "The exp48 pre-reg headline (d=+0.937, verdict=PROMOTE) is "
            "the locked finding; this experiment quantifies how much "
            "the accidental omission of poetry_islami from the pool "
            "moved the result."
        ),
        "runtime_seconds": round(time.time() - t0, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console summary ---
    print(f"\n[{EXP}] DONE in {report['runtime_seconds']:.1f}s")
    print(f"[{EXP}] exp48 locked headline: "
          f"verdict={EXP48_HEADLINE['verdict']}  "
          f"n_fires={EXP48_HEADLINE['n_fires']}/6  "
          f"strongest={EXP48_HEADLINE['strongest_metric']} "
          f"(d={EXP48_HEADLINE['strongest_d']:+.3f})")
    print(f"[{EXP}] under pre-reg pool  (sanity): "
          f"verdict={verdict_prereg}  n_fires={n_fires_prereg}/6  "
          f"strongest={strongest_prereg} (d={strongest_d_prereg:+.3f})")
    print(f"[{EXP}] under extended pool (+islami): "
          f"verdict={verdict_ext}  n_fires={n_fires_ext}/6  "
          f"strongest={strongest_ext} (d={strongest_d_ext:+.3f})")
    print(f"[{EXP}] delta strongest d = {delta_strongest:+.4f}   "
          f"verdict unchanged = {verdict_ext == EXP48_HEADLINE['verdict']}")
    print(f"[{EXP}] STABILITY VERDICT: {stability_verdict}")
    print(f"[{EXP}] per-metric fire deltas:")
    for m, d in delta_per_metric.items():
        arrow = " " if d["fires_exp48_prereg"] == d["fires_extended_pool"] else "*"
        print(
            f"   {arrow} {m:<20s}  d: {d['d_exp48_prereg']:+.3f} -> "
            f"{d['d_extended_pool']:+.3f}  (Δ={d['delta_d']:+.3f})  "
            f"fires: {d['fires_exp48_prereg']} -> {d['fires_extended_pool']}"
        )

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
