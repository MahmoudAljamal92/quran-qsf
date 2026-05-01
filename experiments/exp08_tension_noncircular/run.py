"""
exp08_tension_noncircular/run.py
================================
Circularity stress-test of Approach C (the Tension-Asymmetry Law).

exp07 reported P(T>0) ≈ 6.14·max(0, RD·EL − 0.013), R² = 0.868 across
7 Arabic corpora. The audit flagged a circularity risk: T ≡ H_cond − H_EL
and RD·EL contains EL; so the "law" could be a disguised identity.

This experiment runs the **full 4 × 4 circularity matrix**:

    4 tension proxies (dependent variable = P(proxy > 0)):
      T0 = H_cond − H_EL         (the original; has EL inside)
      T1 = H_cond                  (drop H_EL; pure unpredictability)
      T2 = H_cond − H_word_init    (replace H_EL with a different
                                    phonological entropy at word START,
                                    not word END — uncorrelated with EL)
      T3 = H_cond / max(H_EL, ε)  (ratio form; still EL-dependent but
                                    in a different algebraic shape)

    4 predictors (independent variable):
      P0 = RD · EL         (the original; has EL inside)
      P1 = RD              (no EL term; pure root-diversity)
      P2 = EL              (no RD term; pure rhyme-consistency)
      P3 = RD · H_cond     (joint with H_cond; no EL term)

For each of the 16 cells we fit P(proxy > 0) ~ a + b · predictor on the
same 7 Arabic corpora (hadith quarantined per preregistration) and
report R², Pearson r, and the one-sided p (Quran-vs-rest).

**Rule of classification** (decided BEFORE seeing any exp08 result):

  - A cell is *circular* iff the dependent and independent variables
    share a common algebraic term (EL or H_cond appearing on both
    sides).
  - A cell is *non-circular* iff they share nothing.
  - The LAW holds iff **every non-circular cell has R² ≥ 0.5**.
  - The LAW is a tautology iff every non-circular cell has R² < 0.3
    while circular cells have R² > 0.7.
  - Intermediate outcomes are explicitly labelled "ambiguous / needs
    more corpora".

Reads (read-only):
  - phase_06_phi_m.pkl    (CORPORA)

Writes ONLY under results/experiments/exp08_tension_noncircular/:
  - exp08_tension_noncircular.json
  - fig_circularity_matrix.png
  - fig_best_noncircular_scatter.png
  - self_check_<ts>.json
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src import features as ft  # noqa: E402
from src import roots as rc  # noqa: E402

EXP = "exp08_tension_noncircular"

ARABIC_CORPORA = [
    "quran",
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Classification of the 16 cells (dependent × predictor) as
# circular / non-circular / mixed, decided before any result is
# computed. "Contains EL": dependent-side: T0 (−H_EL), T3 (÷H_EL).
# predictor-side: P0 (RD·EL), P2 (EL).
# "Contains H_cond": dependent-side: all four (all build on H_cond).
# predictor-side: P3 (RD·H_cond).
SHARED_TERMS = {
    # dep: set of shared algebraic terms
    "T0": {"H_cond", "H_EL"},
    "T1": {"H_cond"},
    "T2": {"H_cond", "H_word_init"},
    "T3": {"H_cond", "H_EL"},
    # predictor: set of terms
    "P0": {"RD", "H_EL"},
    "P1": {"RD"},
    "P2": {"H_EL"},
    "P3": {"RD", "H_cond"},
}


def _strip_d(s: str) -> str:
    return ft._strip_d(s)


def _final_root(verse: str) -> str:
    v = _strip_d(verse).strip()
    toks = v.split()
    if not toks:
        return ""
    return rc.primary_root_normalized(toks[-1]) or "<unk>"


def _h_word_initial(verses: list[str]) -> float:
    """Shannon entropy of the distribution of verse-initial letters.
    Mirror of h_el but at the START of each verse, which should be
    uncorrelated with H_EL for any non-palindromic corpus."""
    firsts = []
    for v in verses:
        s = _strip_d(v).strip()
        for ch in s:
            if ch.isalpha():
                firsts.append(ch)
                break
    if not firsts:
        return 0.0
    c = Counter(firsts)
    total = sum(c.values())
    h = 0.0
    for n in c.values():
        p = n / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def _unit_stats(verses: list[str]) -> dict | None:
    """Per-unit extraction: EL, RD_unit, H_cond, H_EL, H_word_init and
    the four tension proxies. Returns None if too short."""
    if len(verses) < 2:
        return None
    try:
        el = float(ft.el_rate(verses))
        h_cond = float(ft.h_cond_roots(verses))
        h_el = float(ft.h_el(verses))
        h_wi = float(_h_word_initial(verses))
        # Per-unit RD for the average-over-units variant
        roots = [_final_root(v) for v in verses]
        roots_nz = [r for r in roots if r and r != "<unk>"]
        rd_unit = (len(set(roots_nz)) / len(roots)) if roots else 0.0
    except Exception:
        return None
    # Tension proxies
    T0 = h_cond - h_el
    T1 = h_cond
    T2 = h_cond - h_wi
    T3 = h_cond / max(h_el, 1e-6)
    return {
        "EL": el, "RD_unit": rd_unit,
        "H_cond": h_cond, "H_EL": h_el, "H_word_init": h_wi,
        "T0": T0, "T1": T1, "T2": T2, "T3": T3,
    }


def _corpus_stats(units: list) -> dict:
    ELs, RDs_unit, all_roots, n_verses_total = [], [], [], 0
    T0s, T1s, T2s, T3s = [], [], [], []
    Hconds, HELs, HWIs = [], [], []
    for u in units:
        s = _unit_stats(u.verses)
        if s is None:
            continue
        ELs.append(s["EL"])
        RDs_unit.append(s["RD_unit"])
        T0s.append(s["T0"]); T1s.append(s["T1"])
        T2s.append(s["T2"]); T3s.append(s["T3"])
        Hconds.append(s["H_cond"]); HELs.append(s["H_EL"]); HWIs.append(s["H_word_init"])
        for v in u.verses:
            all_roots.append(_final_root(v))
        n_verses_total += len(u.verses)
    if not ELs:
        return None
    unique_roots = len(set(r for r in all_roots if r and r != "<unk>"))
    RD_corpus = unique_roots / n_verses_total if n_verses_total else 0.0
    EL_mean = float(np.mean(ELs))
    RD_unit_mean = float(np.mean(RDs_unit))
    H_cond_mean = float(np.mean(Hconds))

    def _p_pos(lst):
        return float(np.mean([1.0 if x > 0 else 0.0 for x in lst]))

    return {
        "n_units": len(ELs), "n_verses": n_verses_total,
        "EL": EL_mean,
        "RD_corpus": RD_corpus,       # unique roots / total verses
        "RD_unit_mean": RD_unit_mean, # mean per-unit RD
        "H_cond": H_cond_mean,
        "H_EL": float(np.mean(HELs)),
        "H_word_init": float(np.mean(HWIs)),
        # P(proxy > 0) for the 4 proxies
        "P_T0_pos": _p_pos(T0s),
        "P_T1_pos": _p_pos(T1s),
        "P_T2_pos": _p_pos(T2s),
        "P_T3_pos": _p_pos(T3s),
        # Predictors (we compute both RD_corpus and RD_unit_mean variants
        # and report the RD_unit_mean variant as primary since it matches
        # the per-surah convention your synthesis used)
        "P0_RD_EL":     RD_unit_mean * EL_mean,
        "P1_RD":        RD_unit_mean,
        "P2_EL":        EL_mean,
        "P3_RD_Hcond":  RD_unit_mean * H_cond_mean,
        # Cross-check: also the corpus-wide RD·EL (exp07's convention)
        "P0_alt_RDcorpus_EL": RD_corpus * EL_mean,
    }


def _fit(xs: np.ndarray, ys: np.ndarray) -> dict:
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    mask = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[mask], ys[mask]
    if len(xs) < 3:
        return {"slope": None, "intercept": None, "R2": None,
                "pearson_r": None, "n": int(len(xs))}
    slope, intercept = np.polyfit(xs, ys, 1)
    pred = slope * xs + intercept
    ss_res = float(((ys - pred) ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else math.nan
    r = float(np.corrcoef(xs, ys)[0, 1]) if len(xs) > 1 else math.nan
    # one-sided p via Pearson
    from scipy import stats as _st
    if not np.isfinite(r) or abs(r) >= 1 - 1e-9:
        p_one = 0.0
    else:
        tval = r * math.sqrt((len(xs) - 2) / (1 - r * r))
        p_one = float(_st.t.sf(abs(tval), df=len(xs) - 2))
    return {
        "slope": float(slope), "intercept": float(intercept),
        "R2": float(R2), "pearson_r": r, "n": int(len(xs)),
        "p_one_sided": p_one,
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Per-corpus aggregate
    stats_by = {}
    for c in ARABIC_CORPORA:
        if c not in CORPORA:
            continue
        s = _corpus_stats(CORPORA[c])
        if s is not None:
            stats_by[c] = s
    for c, s in stats_by.items():
        print(f"[{EXP}] {c:<18s}  n_units={s['n_units']:>4d}  "
              f"EL={s['EL']:.3f}  RD_unit={s['RD_unit_mean']:.3f}  "
              f"H_cond={s['H_cond']:.3f}  H_EL={s['H_EL']:.3f}  "
              f"P(T0>0)={s['P_T0_pos']:.3f}  P(T1>0)={s['P_T1_pos']:.3f}  "
              f"P(T2>0)={s['P_T2_pos']:.3f}")

    # 4 × 4 matrix: dep (T0..T3) × pred (P0..P3)
    dep_names = ["T0", "T1", "T2", "T3"]
    pred_names = ["P0", "P1", "P2", "P3"]
    pred_keys = {"P0": "P0_RD_EL", "P1": "P1_RD", "P2": "P2_EL", "P3": "P3_RD_Hcond"}
    dep_keys = {"T0": "P_T0_pos", "T1": "P_T1_pos",
                "T2": "P_T2_pos", "T3": "P_T3_pos"}

    corpora_used = [c for c in stats_by if c != "hadith_bukhari"]
    matrix = {}
    for dep in dep_names:
        for pred in pred_names:
            xs = [stats_by[c][pred_keys[pred]] for c in corpora_used]
            ys = [stats_by[c][dep_keys[dep]] for c in corpora_used]
            fit = _fit(np.array(xs), np.array(ys))
            shared = SHARED_TERMS[dep] & SHARED_TERMS[pred]
            matrix[f"{dep}_vs_{pred}"] = {
                **fit,
                "dep": dep, "pred": pred,
                "dep_key": dep_keys[dep], "pred_key": pred_keys[pred],
                "shared_terms": sorted(shared),
                "is_circular": bool(shared),
            }

    # Classification verdict — decided by the pre-registered rule above
    noncirc_R2s = [v["R2"] for v in matrix.values()
                   if not v["is_circular"] and v["R2"] is not None]
    circ_R2s = [v["R2"] for v in matrix.values()
                if v["is_circular"] and v["R2"] is not None]
    min_noncirc = float(min(noncirc_R2s)) if noncirc_R2s else math.nan
    max_noncirc = float(max(noncirc_R2s)) if noncirc_R2s else math.nan
    mean_noncirc = float(np.mean(noncirc_R2s)) if noncirc_R2s else math.nan
    mean_circ = float(np.mean(circ_R2s)) if circ_R2s else math.nan

    if not noncirc_R2s:
        verdict = "no non-circular cells computable"
    elif min_noncirc >= 0.5:
        verdict = "LAW HOLDS (every non-circular cell has R² ≥ 0.5)"
    elif max_noncirc < 0.3 and mean_circ > 0.7:
        verdict = "TAUTOLOGY (non-circular R² < 0.3 while circular R² > 0.7)"
    elif max_noncirc >= 0.5:
        verdict = "AMBIGUOUS — some non-circular cells support; others don't"
    else:
        verdict = "LAW FAILS (no non-circular cell has R² ≥ 0.5)"

    # Best non-circular cell (highest R²)
    best_nc = None
    for k, v in matrix.items():
        if v["is_circular"] or v["R2"] is None:
            continue
        if best_nc is None or v["R2"] > best_nc["R2"]:
            best_nc = {**v, "cell": k}

    # ---------- Plots ----------
    # 4x4 heatmap of R² with circular cells hatched
    fig, ax = plt.subplots(figsize=(7, 6))
    R2_grid = np.full((4, 4), np.nan)
    for i, dep in enumerate(dep_names):
        for j, pred in enumerate(pred_names):
            v = matrix[f"{dep}_vs_{pred}"]
            if v["R2"] is not None:
                R2_grid[i, j] = v["R2"]
    im = ax.imshow(R2_grid, vmin=-0.2, vmax=1.0, cmap="RdYlGn")
    for i, dep in enumerate(dep_names):
        for j, pred in enumerate(pred_names):
            v = matrix[f"{dep}_vs_{pred}"]
            txt = f"R²={v['R2']:.2f}\nr={v['pearson_r']:.2f}" if v["R2"] is not None else "--"
            if v["is_circular"]:
                ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                        color="black",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow",
                                  alpha=0.6, edgecolor="none"))
            else:
                ax.text(j, i, txt, ha="center", va="center", fontsize=9,
                        color="black", fontweight="bold")
    ax.set_xticks(range(4))
    ax.set_xticklabels([f"{p}\n({','.join(sorted(SHARED_TERMS[p])) or '∅'})"
                        for p in pred_names], fontsize=9)
    ax.set_yticks(range(4))
    ax.set_yticklabels([f"{d}\n({','.join(sorted(SHARED_TERMS[d])) or '∅'})"
                        for d in dep_names], fontsize=9)
    ax.set_xlabel("predictor")
    ax.set_ylabel("dependent (P(proxy > 0))")
    ax.set_title(f"Circularity matrix (yellow = circular)\nVerdict: {verdict}")
    plt.colorbar(im, ax=ax, label="R² (OLS)")
    fig.tight_layout()
    fig.savefig(out / "fig_circularity_matrix.png", dpi=130)
    plt.close(fig)

    # Best non-circular scatter
    if best_nc is not None:
        fig, ax = plt.subplots(figsize=(7, 5))
        xs = [stats_by[c][best_nc["pred_key"]] for c in corpora_used]
        ys = [stats_by[c][best_nc["dep_key"]] for c in corpora_used]
        for c, x, y in zip(corpora_used, xs, ys):
            col = "crimson" if c == "quran" else "#2b8cbe"
            mk = "*" if c == "quran" else "o"
            ms = 220 if c == "quran" else 90
            ax.scatter([x], [y], color=col, marker=mk, s=ms,
                       edgecolor="black", linewidth=0.5, zorder=5)
            ax.annotate(c, (x, y), fontsize=8,
                        xytext=(5, 5), textcoords="offset points")
        xline = np.linspace(min(xs), max(xs), 50)
        yline = best_nc["slope"] * xline + best_nc["intercept"]
        ax.plot(xline, yline, "r-", lw=1.5,
                label=f"OLS: y = {best_nc['slope']:.3f}·x + {best_nc['intercept']:+.3f}"
                      f"\n  R² = {best_nc['R2']:.3f}, r = {best_nc['pearson_r']:.3f}, "
                      f"p = {best_nc['p_one_sided']:.4f}")
        ax.set_xlabel(f"{best_nc['pred']}  ({best_nc['pred_key']})")
        ax.set_ylabel(f"{best_nc['dep']}  ({best_nc['dep_key']})")
        ax.set_title(f"Best NON-CIRCULAR cell: {best_nc['cell']}")
        ax.legend(fontsize=9, loc="best")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(out / "fig_best_noncircular_scatter.png", dpi=130)
        plt.close(fig)

    # ---------- JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            "4×4 circularity matrix for Approach C. Tests whether the "
            "P(T>0) ~ RD·EL relationship survives when one or both sides "
            "lose their shared algebraic terms (H_EL / RD)."
        ),
        "classification_rule_preregistered": (
            "LAW HOLDS iff every non-circular cell has R² ≥ 0.5; "
            "TAUTOLOGY iff all non-circular R² < 0.3 AND circular R² > 0.7; "
            "otherwise AMBIGUOUS or LAW FAILS."
        ),
        "corpora_used": corpora_used,
        "n_corpora": len(corpora_used),
        "dependents": {
            "T0": "H_cond − H_EL (original, has EL)",
            "T1": "H_cond (no EL)",
            "T2": "H_cond − H_word_initial (replaces H_EL)",
            "T3": "H_cond / H_EL (ratio form, has EL)",
        },
        "predictors": {
            "P0": "RD · EL (original, has EL)",
            "P1": "RD (no EL)",
            "P2": "EL (no RD)",
            "P3": "RD · H_cond (no EL)",
        },
        "shared_terms": {k: sorted(v) for k, v in SHARED_TERMS.items()},
        "per_corpus_stats": stats_by,
        "matrix_16_cells": matrix,
        "summary": {
            "n_noncircular_cells": len(noncirc_R2s),
            "n_circular_cells": len(circ_R2s),
            "mean_R2_noncircular": mean_noncirc,
            "mean_R2_circular": mean_circ,
            "min_R2_noncircular": min_noncirc,
            "max_R2_noncircular": max_noncirc,
        },
        "best_noncircular_cell": best_nc,
        "verdict": verdict,
    }
    with open(out / "exp08_tension_noncircular.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console table
    print(f"\n[{EXP}] === 4×4 CIRCULARITY MATRIX (R²) ===")
    print(f"  {'':>8s}  {'P0(RD·EL)':>10s}  {'P1(RD)':>8s}  {'P2(EL)':>8s}  {'P3(RD·Hc)':>10s}")
    for dep in dep_names:
        row = [f"{dep:>8s}"]
        for pred in pred_names:
            v = matrix[f"{dep}_vs_{pred}"]
            mark = "*" if v["is_circular"] else " "
            r2 = f"{v['R2']:.3f}" if v["R2"] is not None else "  -- "
            row.append(f"{mark}{r2:>9s}")
        print("  " + "  ".join(row))
    print("    (* = circular)")
    print(f"\n[{EXP}] mean R² non-circular = {mean_noncirc:.3f}  "
          f"(min {min_noncirc:.3f}, max {max_noncirc:.3f})")
    print(f"[{EXP}] mean R² circular     = {mean_circ:.3f}")
    print(f"[{EXP}] VERDICT: {verdict}")
    if best_nc is not None:
        print(f"[{EXP}] Best non-circular cell: {best_nc['cell']}  "
              f"R²={best_nc['R2']:.3f}  p={best_nc['p_one_sided']:.4f}")
    print(f"[{EXP}] wrote: {out}")
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
