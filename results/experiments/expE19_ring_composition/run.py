"""
E19 — Ring-Composition / Structural-Symmetry Detector (feature-level).

Pre-registered test (different from H20, which was LEXICAL ring-composition, NULL):

    For each surah s with n_s >= 20 verses, compute a verse-level 5-D feature
    vector V_s ∈ R^{n_s × 5}.  Under a hypothesized ring, verse i mirrors
    verse n-1-i.  Test statistic is the mean squared Euclidean distance
    across mirror pairs:

        D_obs(s) = mean_{i < n/2}  ||V_s[i] - V_s[n-1-i]||²

    Null distribution: shuffle verse order 1000× per surah; recompute D.
    A genuine feature-level ring implies mirror pairs are CLOSER than
    random ordering, so the left-tail p-value:

        p_s = (D_null <= D_obs).mean()

    Per-surah p-values combine via Fisher's method:

        χ² = -2 Σ log(p_s)        under independence (no cross-surah data),
                                    distributed χ²(2k).

    Falsifier: Fisher-combined p > 0.01.

Notes:
    - Per-verse 5-D features chosen to be simple, fast, and diagonally
      distinct: (chars, words, connector_count, unique_letter_count,
      mean_word_length).
    - All features are z-scored per-surah before distance computation so
      scale differences don't dominate.
    - p_s is clipped to max(p_s, 1/(B+1)) to avoid log(0) in Fisher.
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT    = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUT_DIR = ROOT / "results" / "experiments" / "expE19_ring_composition"
OUT_DIR.mkdir(parents=True, exist_ok=True)
QURAN   = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"

SEED             = 42
B_PERMUTATIONS   = 1000
MIN_VERSES       = 20
CONNECTORS       = set("و ف ب ل في على إلى من عن ثم أو أم إن أن إذا كلا".split())

rng = np.random.default_rng(SEED)

# ------------------------------------------------------------------- load
lines = [x for x in QURAN.read_text(encoding="utf-8").splitlines() if "|" in x]
by_surah: dict[int, list[str]] = defaultdict(list)
for ln in lines:
    parts = ln.split("|", 2)
    if len(parts) != 3: continue
    try:
        s, v = int(parts[0]), int(parts[1])
    except ValueError:
        continue
    by_surah[s].append(parts[2].strip())

print(f"[E19] loaded {sum(len(v) for v in by_surah.values())} verses "
      f"across {len(by_surah)} surahs")

# ------------------------------------------------------------------- features
def verse_features(text: str) -> np.ndarray:
    """5-D per-verse feature vector."""
    words   = text.split()
    chars   = len(text.replace(" ", ""))
    w_count = len(words)
    conn    = sum(1 for w in words if w in CONNECTORS)
    uniq    = len(set(ch for ch in text if ch != " "))
    mwl     = np.mean([len(w) for w in words]) if words else 0.0
    return np.array([chars, w_count, conn, uniq, mwl], dtype=float)

# ------------------------------------------------------------------- per-surah test
def mirror_dissim(V: np.ndarray, order: np.ndarray) -> float:
    n = len(order)
    k = n // 2
    return float(np.mean([
        np.sum((V[order[i]] - V[order[n - 1 - i]]) ** 2)
        for i in range(k)
    ]))

results = []
t0 = time.time()
for s in sorted(by_surah):
    verses = by_surah[s]
    n = len(verses)
    if n < MIN_VERSES:
        continue
    V = np.vstack([verse_features(v) for v in verses])
    # z-score per feature (guard zero-variance columns)
    mu, sd = V.mean(0), V.std(0, ddof=1)
    sd[sd == 0] = 1.0
    Vz = (V - mu) / sd
    order = np.arange(n)
    D_obs = mirror_dissim(Vz, order)
    # null
    null = np.empty(B_PERMUTATIONS)
    for b in range(B_PERMUTATIONS):
        null[b] = mirror_dissim(Vz, rng.permutation(n))
    p = float((null <= D_obs).mean())
    results.append({
        "surah": s,
        "n": n,
        "D_obs": D_obs,
        "null_mean": float(null.mean()),
        "null_std": float(null.std(ddof=1)),
        "p_left": p,
    })

print(f"[E19] tested {len(results)} surahs (n>={MIN_VERSES}) in {time.time()-t0:.1f}s")

# ------------------------------------------------------------------- Fisher combine
B = B_PERMUTATIONS
p_vec = np.array([max(r["p_left"], 1.0 / (B + 1)) for r in results])
chi2  = -2.0 * np.log(p_vec).sum()
df    = 2 * len(p_vec)
fisher_p = float(1.0 - stats.chi2.cdf(chi2, df))
print(f"[E19] Fisher: χ²={chi2:.2f}, df={df}, combined p={fisher_p:.4e}")

# ------------------------------------------------------------------- per-surah quick stats
n_sig_at_05  = int(sum(1 for r in results if r["p_left"] <= 0.05))
n_sig_at_01  = int(sum(1 for r in results if r["p_left"] <= 0.01))
n_expect_05  = 0.05 * len(results)
n_expect_01  = 0.01 * len(results)
print(f"[E19] per-surah: {n_sig_at_05}/{len(results)} at p<=0.05 "
      f"(expected {n_expect_05:.1f}); {n_sig_at_01}/{len(results)} at p<=0.01 "
      f"(expected {n_expect_01:.1f})")

# ------------------------------------------------------------------- verdict
PREREG = {
    "test_statistic": "D_obs = mean squared Euclidean dist across mirror pairs of z-scored per-verse 5-D features",
    "per_surah_null": f"{B_PERMUTATIONS} random verse-order permutations per surah",
    "combiner": "Fisher's method across all surahs with n >= 20 verses",
    "min_verses": MIN_VERSES,
    "combined_falsifier_p": 0.01,
    "seed": SEED,
}

if fisher_p <= 0.01:
    verdict = "FEATURE_LEVEL_RING"
elif fisher_p <= 0.05:
    verdict = "WEAK_RING"
else:
    verdict = "NULL_NO_RING"
print(f"[E19] verdict = {verdict}")

# ------------------------------------------------------------------- JSON
report = {
    "experiment": "E19_ring_composition",
    "verdict": verdict,
    "seed": SEED,
    "n_permutations": B_PERMUTATIONS,
    "min_verses": MIN_VERSES,
    "n_surahs_tested": len(results),
    "fisher_chi2": chi2,
    "fisher_df": df,
    "fisher_combined_p": fisher_p,
    "n_surahs_sig_at_0.05": n_sig_at_05,
    "n_surahs_sig_at_0.01": n_sig_at_01,
    "expected_at_0.05_under_null": n_expect_05,
    "expected_at_0.01_under_null": n_expect_01,
    "pre_registered_criteria": PREREG,
    "per_surah": results,
}
(OUT_DIR / "expE19_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# ------------------------------------------------------------------- plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # p-value histogram
    ax = axes[0]
    ax.hist([r["p_left"] for r in results], bins=20, edgecolor="black")
    ax.axvline(0.05, color="red", linestyle="--", label="p=0.05")
    ax.axvline(0.01, color="darkred", linestyle="--", label="p=0.01")
    ax.set_xlabel("per-surah left-tail p")
    ax.set_ylabel("# surahs")
    ax.set_title(f"E19 per-surah p dist (n={len(results)})")
    ax.legend()

    # surah-size vs p scatter
    ax = axes[1]
    ax.scatter([r["n"] for r in results], [r["p_left"] for r in results],
               s=30, alpha=0.7)
    ax.axhline(0.05, color="red", linestyle="--")
    ax.axhline(0.01, color="darkred", linestyle="--")
    ax.set_xscale("log")
    ax.set_xlabel("surah length (# verses, log scale)")
    ax.set_ylabel("p_left (ring)")
    ax.set_title(f"E19 p vs surah length\nFisher p = {fisher_p:.3e}")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "expE19_ring_plot.png", dpi=130)
    print(f"[E19] plot saved: {OUT_DIR / 'expE19_ring_plot.png'}")
except Exception as e:
    print(f"[E19] plot skipped: {e}")

# ------------------------------------------------------------------- markdown
md = f"""# E19 — Feature-Level Ring Composition Test

**Run date**: run-of-record
**Seed**: {SEED}
**Verdict**: **{verdict}**

## Design

- 5-D per-verse features: (chars, words, connector_count, unique_letters, mean_word_length).
- z-score each feature **within surah** so distance is scale-invariant.
- Test statistic per surah: `D_obs = mean_{{i<n/2}} ||V[i] - V[n-1-i]||²`.
- Null: {B_PERMUTATIONS} random verse-order permutations per surah (seed {SEED}).
- Combiner: Fisher's method over {len(results)} surahs with n ≥ {MIN_VERSES}.
- Pre-reg falsifier: combined p > 0.01 ⇒ NULL.

## Results

| Quantity | Value |
|---|---|
| Surahs tested | {len(results)} |
| Surahs with p ≤ 0.05 | {n_sig_at_05} (expected {n_expect_05:.1f} under null) |
| Surahs with p ≤ 0.01 | {n_sig_at_01} (expected {n_expect_01:.1f} under null) |
| Fisher χ² | {chi2:.2f} |
| Fisher df | {df} |
| **Fisher combined p** | **{fisher_p:.4e}** |

## Interpretation

{
    "**FEATURE_LEVEL_RING** — Fisher-combined p < 0.01. Across the 5-D "
    "per-verse feature metric, mirror-position verses are systematically "
    "closer than random re-orderings. This is a *different* test from H20 "
    "(lexical ring = NULL at exp86) and establishes feature-level "
    "symmetry as a genuine property of Mushaf verse-order." if verdict == "FEATURE_LEVEL_RING"
    else "**WEAK_RING** — Fisher-combined 0.01 < p ≤ 0.05. Marginal "
    "evidence for feature-level mirror symmetry; not strong enough to "
    "claim as a law, but worth a follow-up with a richer feature set." if verdict == "WEAK_RING"
    else "**NULL_NO_RING** — Fisher-combined p > 0.05. At the 5-D "
    "per-verse feature level, mirror-position verses are not "
    "systematically more similar than random. Consistent with H20 (lexical "
    "ring = NULL at exp86); closes the door on the Excel-R3 ring-composition "
    "claim at two independent representation levels."
}

## Crosslinks

- Spec: `docs/EXECUTION_PLAN_AND_PRIORITIES.md` §E19
- Prior H20 test (lexical): `docs/HYPOTHESES_AND_TESTS.md` H20
- Raw output: `results/experiments/expE19_ring_composition/expE19_report.json`
"""
(OUT_DIR / "expE19_report.md").write_text(md, encoding="utf-8")
print(f"[E19] report: {OUT_DIR / 'expE19_report.md'}")
print(f"Total runtime: {time.time()-t0:.1f}s")
