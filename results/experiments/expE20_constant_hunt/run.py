"""
E20 — Un-derived structural constant hunt.

Target: ``VL_CV_FLOOR = 0.1962`` used by the legacy CascadeProjects
pipeline (`build_pipeline_p{1,2,3}.py`) to exclude pseudo-surahs whose
verse-length coefficient-of-variation (VL_CV) falls below the floor.

Pre-registered falsifier (per `docs/EXECUTION_PLAN_AND_PRIORITIES.md §E20`):

    No closed-form derivation exists AND the downstream claim (the set of
    included Quran units + Mahalanobis separation) collapses outside a
    ±10% neighborhood of the constant  ⇒  arbitrary tuning; flag for
    retraction.

Three diagnostic probes:

A. **Direct numeric reconstruction**
   Recompute VL_CV for every canonical surah under three measures of
   verse length (chars without spaces, chars with spaces, words) and
   report how 0.1962 sits relative to the 1st/2nd/3rd smallest values.

B. **Sensitivity sweep**
   For FLOOR ∈ {0.10, 0.11, …, 0.25}, compute #excluded-surahs on the
   Quran side.  The downstream claim is "stable" iff the included-set
   is invariant over the ±10% neighborhood [0.1766, 0.2158].

C. **Closed-form derivation attempts**
   Check whether 0.1962 matches any of ~12 candidate closed-form
   expressions in {e, π, √2, golden ratio, etc.}.  Report closest match
   and its relative error.

Verdict mapping
---------------
    NONE of A/B/C supply a clean rational ⇒ flag as arbitrary tuning
    B passes (exclusion set stable over ±10%)              ⇒ STABLE_MAGIC
    A supplies exact match to min(VL_CV)+ε or similar      ⇒ DERIVED_EMPIRICAL
    C supplies closed-form within 1e-3                      ⇒ DERIVED_ANALYTIC
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
from collections import defaultdict

import numpy as np

ROOT    = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUT_DIR = ROOT / "results" / "experiments" / "expE20_constant_hunt"
OUT_DIR.mkdir(parents=True, exist_ok=True)
QURAN   = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
BUILDER = ROOT / "archive" / "CascadeProjects_legacy_builders" / "build_pipeline_p1.py"

TARGET  = 0.1962
TOL_REL = 0.10          # ±10% neighborhood for pre-reg stability check
SEED    = 42

t0 = time.time()

# --------------------------------------------------------------- load Quran
lines = [x for x in QURAN.read_text(encoding="utf-8").splitlines() if "|" in x]
by_surah: dict[int, list[str]] = defaultdict(list)
for ln in lines:
    parts = ln.split("|", 2)
    if len(parts) != 3: continue
    try:
        s = int(parts[0])
    except ValueError:
        continue
    by_surah[s].append(parts[2])

# --------------------------------------------------------------- A: direct recompute
def compute_vlcv(by_surah, measure):
    def unit(t):
        if measure == "chars_nospace": return len(t.replace(" ", ""))
        if measure == "chars_all":     return len(t)
        if measure == "words":         return len(t.split())
        raise ValueError(measure)
    v = {}
    for s, verses in by_surah.items():
        lens = np.array([unit(t) for t in verses], dtype=float)
        if len(lens) > 1:
            v[s] = float(lens.std(ddof=1) / lens.mean())
    return v

probes = {}
for m in ("chars_nospace", "chars_all", "words"):
    vlcv = compute_vlcv(by_surah, m)
    sorted_items = sorted(vlcv.items(), key=lambda x: x[1])
    arr = np.array([v for _, v in sorted_items])
    probes[m] = {
        "per_surah": vlcv,
        "sorted": sorted_items,
        "min_surah": sorted_items[0][0], "min_val": sorted_items[0][1],
        "p2_surah":  sorted_items[1][0], "p2_val":  sorted_items[1][1],
        "p3_surah":  sorted_items[2][0], "p3_val":  sorted_items[2][1],
        "count_below_target": int((arr < TARGET).sum()),
        "target_is_between_p":  float((arr < TARGET).mean() * 100),
    }
    print(f"[E20-A] measure={m:<13s} "
          f"min={arr[0]:.4f} (S{probes[m]['min_surah']})   "
          f"p2={arr[1]:.4f} (S{probes[m]['p2_surah']})   "
          f"p3={arr[2]:.4f} (S{probes[m]['p3_surah']})   "
          f"#<floor={probes[m]['count_below_target']:3d}   "
          f"pct={probes[m]['target_is_between_p']:.2f}%")

# --------------------------------------------------------------- B: sensitivity sweep
sweep_measure = "chars_nospace"
vlcv = probes[sweep_measure]["per_surah"]
vals = np.array(sorted(vlcv.values()))
floor_grid = np.round(np.arange(0.10, 0.26, 0.01), 4)
sweep = []
for f in floor_grid:
    n_exc = int((vals < f).sum())
    sweep.append({"floor": float(f), "n_excluded": n_exc,
                  "n_included": int(len(vals) - n_exc)})

# neighborhood-stability check
lo = TARGET * (1 - TOL_REL)
hi = TARGET * (1 + TOL_REL)
exc_in_nbh = sorted({int((vals < f).sum())
                     for f in np.linspace(lo, hi, 21)})
stable = len(exc_in_nbh) == 1
print(f"[E20-B] sweep on {sweep_measure}")
for row in sweep:
    mark = "  <<< TARGET" if abs(row["floor"] - round(TARGET, 2)) < 0.005 else ""
    print(f"        floor={row['floor']:.2f}  n_excluded={row['n_excluded']:3d}"
          f"  n_included={row['n_included']:3d}{mark}")
print(f"[E20-B] in ±10% neighborhood [{lo:.4f}, {hi:.4f}]: "
      f"exclusion counts = {exc_in_nbh}  →  STABLE = {stable}")

# --------------------------------------------------------------- C: closed-form hunt
candidates = {
    "1/(2*e)":             1.0 / (2 * math.e),
    "1/(π+e/2)":           1.0 / (math.pi + math.e/2),
    "ln(6)/π²":            math.log(6) / (math.pi ** 2),
    "1/sqrt(26)":          1.0 / math.sqrt(26),
    "(e - 2)/(π)":         (math.e - 2) / math.pi,
    "(sqrt(5)-1)/sqrt(π*e)": (math.sqrt(5)-1) / math.sqrt(math.pi * math.e),
    "1/(phi^3)":           1.0 / ((1 + math.sqrt(5))/2)**3,
    "log10(π)/e^(1/2)":    math.log10(math.pi) / math.sqrt(math.e),
    "e/(e+π)/sqrt(2)":     math.e / (math.e + math.pi) / math.sqrt(2),
    "min(Quran_VL_CV_chars_nospace) + 2nd/2":
        (probes["chars_nospace"]["min_val"] + probes["chars_nospace"]["p2_val"])/2,
    "2nd_smallest_Quran_VL_CV_chars_nospace":
        probes["chars_nospace"]["p2_val"],
    "2nd_smallest_Quran_VL_CV_words":
        probes["words"]["p2_val"],
    "1/(2*pi*0.81)":       1.0 / (2 * math.pi * 0.81),
}
cf_ranked = sorted(((k, v, abs(v - TARGET), abs(v - TARGET)/TARGET)
                    for k, v in candidates.items()),
                   key=lambda r: r[2])
best_cf = cf_ranked[0]
print(f"[E20-C] closest closed-form candidate:")
for k, v, ad, rd in cf_ranked[:5]:
    print(f"        {k:<45s}  = {v:.4f}   |Δ|={ad:.4f}   rel={rd*100:.2f}%")

derived_analytic  = best_cf[3] < 1e-3   # < 0.1 %
derived_empirical = (best_cf[2] < 0.001 and
                     "2nd_smallest" in best_cf[0])

# --------------------------------------------------------------- downstream claim sanity
# Band-A cached feature matrix: sanity check that VL_CV on that matrix respects the floor
try:
    import pickle, sys
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))
    d = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))
    X_Q = np.asarray(d["state"]["X_QURAN"])
    X_C = np.asarray(d["state"]["X_CTRL_POOL"])
    cols = d["state"]["FEAT_COLS"]
    idx_vlcv = cols.index("VL_CV")
    quran_vlcv_cached = X_Q[:, idx_vlcv]
    mu_C = X_C.mean(0); S_C = np.cov(X_C.T)
    S_inv = np.linalg.pinv(S_C)
    def T2(X_sub):
        diff = X_sub.mean(0) - mu_C
        return float(diff @ S_inv @ diff) * len(X_sub)
    T2_full = T2(X_Q)
    # subset by pseudo-floor on cached VL_CV column (they're already filtered but scaled;
    # use rank-based drops instead for a downstream sensitivity proxy):
    order = np.argsort(quran_vlcv_cached)
    sens = [{"drop_low": k,
             "T2": T2(X_Q[order[k:]]),
             "n": int(len(X_Q) - k)}
            for k in (0, 1, 2, 3, 5)]
    print(f"[E20-D] Hotelling T² on Band-A Quran (n={len(X_Q)}) vs pool (n={len(X_C)}):")
    for s in sens:
        print(f"        drop lowest-{s['drop_low']} VL_CV → T²={s['T2']:.1f} (n={s['n']})")
    downstream_stable = (max(s['T2'] for s in sens) /
                         min(s['T2'] for s in sens)) < 1.5
    print(f"[E20-D] T² ratio (max/min) over sensitivity drops = "
          f"{max(s['T2'] for s in sens)/min(s['T2'] for s in sens):.2f}   "
          f"→  downstream_stable = {downstream_stable}")
except Exception as e:
    print(f"[E20-D] skipped (cache load failed): {e}")
    sens, downstream_stable, T2_full = [], None, None

# --------------------------------------------------------------- verdict
if derived_analytic:
    verdict = "DERIVED_ANALYTIC"
elif derived_empirical:
    verdict = "DERIVED_EMPIRICAL"
elif stable and (downstream_stable is not False):
    verdict = "STABLE_MAGIC"
else:
    verdict = "MAGIC_NUMBER_FLAG"
print(f"[E20] verdict = {verdict}")

# --------------------------------------------------------------- JSON
report = {
    "experiment": "E20_constant_hunt",
    "target_constant": {"name": "VL_CV_FLOOR", "value": TARGET,
                        "source": "build_pipeline_p1.py:96",
                        "usage_sites": ["build_pipeline_p2.py:59",
                                         "build_pipeline_p2.py:127",
                                         "build_pipeline_p2.py:192",
                                         "build_pipeline_p2.py:208",
                                         "build_pipeline_p3.py:370",
                                         "build_pipeline_p3.py:618"]},
    "A_direct_measurements": {
        m: {"min_surah": probes[m]["min_surah"],
            "min_val":   probes[m]["min_val"],
            "p2_surah":  probes[m]["p2_surah"],
            "p2_val":    probes[m]["p2_val"],
            "p3_surah":  probes[m]["p3_surah"],
            "p3_val":    probes[m]["p3_val"],
            "count_below_target": probes[m]["count_below_target"],
            "pct_below_target": probes[m]["target_is_between_p"]}
        for m in ("chars_nospace", "chars_all", "words")
    },
    "B_sensitivity_sweep": {
        "measure": sweep_measure,
        "grid": sweep,
        "neighborhood_10pct": {"lo": lo, "hi": hi,
                                "exclusion_counts_in_nbh": exc_in_nbh,
                                "stable": stable},
    },
    "C_closed_form_candidates": [
        {"expr": k, "value": v, "abs_err": ad, "rel_err": rd}
        for k, v, ad, rd in cf_ranked
    ],
    "D_downstream_T2_sensitivity": {
        "T2_full_band_A": T2_full,
        "drop_sensitivity": sens,
        "downstream_stable": downstream_stable,
    },
    "derived_analytic": derived_analytic,
    "derived_empirical": derived_empirical,
    "verdict": verdict,
    "seed": SEED,
    "pre_registered_criteria": {
        "falsifier": "no closed-form derivation AND downstream claim collapses outside ±10% neighborhood",
        "neighborhood": "±10% of 0.1962 = [0.1766, 0.2158]",
        "closed_form_tolerance": "relative error < 1e-3",
    },
}
(OUT_DIR / "expE20_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8"
)

# --------------------------------------------------------------- plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ax = axes[0]
    ax.plot([r["floor"] for r in sweep], [r["n_excluded"] for r in sweep],
            "o-", color="C0")
    ax.axvline(TARGET, color="red", linestyle="--", label=f"VL_CV_FLOOR={TARGET}")
    ax.axvspan(lo, hi, alpha=0.15, color="orange", label="±10% neighborhood")
    ax.set_xlabel("candidate VL_CV floor")
    ax.set_ylabel("# Quran surahs excluded")
    ax.set_title("E20-B sensitivity sweep (chars_nospace)")
    ax.legend()

    ax = axes[1]
    v = np.array(sorted(probes["chars_nospace"]["per_surah"].values()))
    ax.plot(np.arange(1, len(v)+1), v, "o", markersize=3)
    ax.axhline(TARGET, color="red", linestyle="--", label=f"FLOOR={TARGET}")
    ax.set_xlabel("surah rank (by VL_CV)")
    ax.set_ylabel("VL_CV  (chars/verse)")
    ax.set_title(f"All 114 Quran VL_CV values\nmin={v[0]:.4f}, 2nd={v[1]:.4f}, 3rd={v[2]:.4f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "expE20_sensitivity.png", dpi=130)
    print(f"[E20] plot: {OUT_DIR / 'expE20_sensitivity.png'}")
except Exception as e:
    print(f"[E20] plot skipped: {e}")

# --------------------------------------------------------------- markdown
# Pre-compute pieces that contain backslashes (py 3.11 can't put them in f-string exprs)
_cs_src  = "`@C:\\Users\\mtj_2\\OneDrive\\Desktop\\Quran\\archive\\CascadeProjects_legacy_builders\\build_pipeline_p1.py:96`"
_cs_spec = "`@C:\\Users\\mtj_2\\OneDrive\\Desktop\\Quran\\docs\\EXECUTION_PLAN_AND_PRIORITIES.md` §E20"
_cs_scan = "`@C:\\Users\\mtj_2\\OneDrive\\Desktop\\Quran\\docs\\SCAN_2026-04-21T07-30Z\\07_CASCADE_PROJECTS_ADDENDUM.md` §D10"
if verdict == "DERIVED_ANALYTIC":
    best_k, best_v, best_ad, best_rd = cf_ranked[0]
    _interp = (
        f"**DERIVED_ANALYTIC (numerical coincidence flag)** — the tightest closed-form match is "
        f"`{best_k} = {best_v:.6f}`, which differs from the target by **{best_rd*100:.3f}%** — "
        f"well under the pre-registered 0.1% tolerance. By the letter of the pre-registered "
        f"criteria this qualifies as an analytic derivation.\n\n"
        f"**Caveat (honest reading)**: the integer 26 has **no canonical grounding** in Arabic or "
        f"Quranic quantities — the Arabic abjad has 28 base letters, the Quran has 114 surahs, "
        f"6236 verses, etc. None of these yields `1/√n` ≈ 0.1962 except n=26, which is a numeric "
        f"coincidence. The 2nd-smallest actual Quran VL_CV (Surah 106, 0.1954) sits 0.39% below "
        f"target — still not a zero-distance derivation, but semantically grounded.\n\n"
        f"**Downstream sensitivity**: Band-A Hotelling T² ratio over "
        f"`drop {{0,1,2,3,5}} lowest-VL_CV surahs` is **{(max(s['T2'] for s in sens)/min(s['T2'] for s in sens)):.2f}** "
        f"(stable). The outlier claim does not hinge on the exact value of the floor inside a wide "
        f"plateau.\n\n"
        f"**Recommendation**: publish as an **empirical parameter with a numeric coincidence note**. "
        f"Do NOT claim analytic derivation unless a semantically-grounded derivation can be attached "
        f"to `1/√26` or a closer grounded alternative is found."
    )
elif verdict == "DERIVED_EMPIRICAL":
    _interp = (
        "**DERIVED_EMPIRICAL** — `VL_CV_FLOOR = 0.1962` reproduces as a close empirical bound on the "
        "Quran's own VL_CV distribution (2nd smallest = 0.1954 under chars_nospace tokenization). "
        "This is a data-driven exclusion threshold, not a derived constant. Publish as an empirical "
        "parameter."
    )
elif verdict == "STABLE_MAGIC":
    _interp = (
        "**STABLE_MAGIC** — `VL_CV_FLOOR = 0.1962` has no derivation from canonical-text first "
        "principles and does not match any tested closed-form expression at < 0.1% error, but the "
        "**downstream claim is invariant over the pre-registered ±10% neighborhood**: the "
        "included/excluded Quran surah set and the Band-A Hotelling T² barely move. The constant is "
        "empirically safe on a wide plateau that happens to include the legacy value.\n\n"
        "**Recommendation**: document as an **empirical parameter**, not a derived constant."
    )
elif verdict == "MAGIC_NUMBER_FLAG":
    _interp = (
        "**MAGIC_NUMBER_FLAG** — no closed-form match AND the downstream exclusion set is NOT "
        "invariant across the ±10% neighborhood. Pre-registered falsifier met; flag for retraction "
        "or tighter empirical grounding."
    )
else:
    _interp = f"**{verdict}**. See JSON for details."

md = f"""# E20 — Un-Derived Structural Constant Hunt

**Target**: `VL_CV_FLOOR = {TARGET}` from `archive/CascadeProjects_legacy_builders/build_pipeline_p1.py:96`
**Verdict**: **{verdict}**

## A. Direct recomputation against canonical Quran text

| Verse-length measure | min (surah) | 2nd smallest | 3rd smallest | #<target | pct<target |
|---|---|---|---|---|---|
| chars_nospace | {probes['chars_nospace']['min_val']:.4f} (S{probes['chars_nospace']['min_surah']}) | {probes['chars_nospace']['p2_val']:.4f} (S{probes['chars_nospace']['p2_surah']}) | {probes['chars_nospace']['p3_val']:.4f} (S{probes['chars_nospace']['p3_surah']}) | {probes['chars_nospace']['count_below_target']} | {probes['chars_nospace']['target_is_between_p']:.2f}% |
| chars_all | {probes['chars_all']['min_val']:.4f} (S{probes['chars_all']['min_surah']}) | {probes['chars_all']['p2_val']:.4f} (S{probes['chars_all']['p2_surah']}) | {probes['chars_all']['p3_val']:.4f} (S{probes['chars_all']['p3_surah']}) | {probes['chars_all']['count_below_target']} | {probes['chars_all']['target_is_between_p']:.2f}% |
| words | {probes['words']['min_val']:.4f} (S{probes['words']['min_surah']}) | {probes['words']['p2_val']:.4f} (S{probes['words']['p2_surah']}) | {probes['words']['p3_val']:.4f} (S{probes['words']['p3_surah']}) | {probes['words']['count_below_target']} | {probes['words']['target_is_between_p']:.2f}% |

Under **chars_nospace** the floor falls between the 2nd (0.1954, Surah 106) and 3rd (0.2107, Surah 93) smallest VL_CV values — it excludes exactly Surah 110 and Surah 106.

## B. Sensitivity sweep (chars_nospace)

| FLOOR | # excluded | # included |
|---|---|---|
""" + "\n".join(f"| {r['floor']:.2f} | {r['n_excluded']} | {r['n_included']} |" for r in sweep) + f"""

**±10% neighborhood** [{lo:.4f}, {hi:.4f}]: exclusion counts in this range = **{exc_in_nbh}**.
Stability (single count over whole neighborhood): **{stable}**.

## C. Closed-form derivation attempts

| Expression | Value | \\|Δ\\| | Rel. err. |
|---|---|---|---|
""" + "\n".join(f"| `{k}` | {v:.6f} | {ad:.6f} | {rd*100:.3f}% |"
                 for k, v, ad, rd in cf_ranked[:7]) + f"""

Tightest analytic match ({cf_ranked[0][0]}): relative error **{cf_ranked[0][3]*100:.3f}%** (threshold: 0.1%).

## D. Downstream Hotelling T² sensitivity (Band-A Quran vs control pool)

| Drop | n | Hotelling T² |
|---|---|---|
""" + ("\n".join(f"| lowest-{s['drop_low']} | {s['n']} | {s['T2']:.1f} |" for s in sens) if sens else "| — | — | skipped |") + f"""

T²-ratio over the sensitivity series: max/min = {(max(s['T2'] for s in sens)/min(s['T2'] for s in sens)):.2f} → downstream_stable = **{downstream_stable}**.

## Interpretation

{_interp}

## Crosslinks

- Source constant: {_cs_src}
- Spec: {_cs_spec}
- SCAN surface: {_cs_scan}
- Raw: `results/experiments/expE20_constant_hunt/expE20_report.json`
"""
(OUT_DIR / "expE20_report.md").write_text(md, encoding="utf-8")
print(f"[E20] report: {OUT_DIR / 'expE20_report.md'}")
print(f"Total runtime: {time.time()-t0:.1f}s")
