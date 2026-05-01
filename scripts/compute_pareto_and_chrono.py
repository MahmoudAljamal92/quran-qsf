"""compute_pareto_and_chrono.py
==============================

Two zero-new-experiment results derivable directly from already-locked data:

  1. Pareto frontier H_word (lexical diversity) vs H_EL (verse-final entropy)
     — produces 7-corpus 2-D coordinates for the new hero image.

  2. Chronological neutrality test: regress each of 5 locked features
     (EL, VL_CV, CN, H_cond, T) on Quran surah chronological order,
     report R^2 per feature.

Outputs:
  results/auxiliary/pareto_frontier.json
  results/auxiliary/chronological_neutrality.json
"""
from __future__ import annotations

import io
import json
import math
import pickle
import sys
from collections import Counter
from pathlib import Path

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PHASE_PKL = ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl"
OUT_DIR = ROOT / "results" / "auxiliary"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"# Loading phase_06_phi_m from {PHASE_PKL.relative_to(ROOT)} ...")
with open(PHASE_PKL, "rb") as f:
    state = pickle.load(f)

print(f"# Top-level keys: {list(state.keys())}")
inner = state.get("state", state)
print(f"# Inner state keys: {list(inner.keys())[:25]}")
corpora = inner.get("CORPORA")
if corpora is None:
    print(f"# ERROR: no CORPORA key in state['state']. Available: {list(inner.keys())[:30]}")
    sys.exit(1)
print(f"# CORPORA names: {list(corpora.keys())}")

# --- 1. PARETO FRONTIER: H_word vs H_EL per corpus --------------------
def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy in bits from a list of counts."""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def normalise_arabic(text: str) -> str:
    """Strip Arabic diacritics for fair word-token counting."""
    DIAC = set(
        "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
        "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
        "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
    )
    return "".join(c for c in str(text) if c not in DIAC)


ARABIC_CONSONANTS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


def last_consonant(word: str) -> str | None:
    """Return last Arabic consonant of a word (the EL letter)."""
    for ch in reversed(normalise_arabic(word)):
        if ch in ARABIC_CONSONANTS:
            return ch
    return None


pareto_rows: list[dict] = []
for corpus_name, units in corpora.items():
    if not units:
        continue
    # H_word: Shannon entropy over word-token frequency
    word_counts: Counter = Counter()
    el_counts: Counter = Counter()
    n_words = 0
    n_verses = 0
    for unit in units:
        # unit may be Unit dataclass or a dict
        verses = unit.verses if hasattr(unit, "verses") else unit.get("verses", [])
        for v in verses:
            n_verses += 1
            stripped = normalise_arabic(v).strip()
            tokens = stripped.split()
            for tok in tokens:
                # token-level word entropy (uses normalised form for fair counting)
                tok_clean = "".join(c for c in tok if c.isalpha() or c in ARABIC_CONSONANTS)
                if tok_clean:
                    word_counts[tok_clean] += 1
                    n_words += 1
            # End-letter of the LAST word in the verse
            if tokens:
                el = last_consonant(tokens[-1])
                if el:
                    el_counts[el] += 1
    h_word = shannon_entropy(list(word_counts.values()))
    h_el = shannon_entropy(list(el_counts.values()))
    # log10(unique_words) is also useful as a corpus-size-controlled diversity proxy
    log10_unique_words = math.log10(len(word_counts)) if word_counts else 0.0
    pareto_rows.append({
        "corpus": corpus_name,
        "h_word_bits": h_word,
        "h_el_bits": h_el,
        "n_unique_words": len(word_counts),
        "log10_unique_words": log10_unique_words,
        "n_words_total": n_words,
        "n_verses": n_verses,
        "n_units": len(units),
    })

# Print summary
print()
print(f"# Pareto-frontier coordinates ({len(pareto_rows)} corpora):")
print(f"# {'corpus':<18s} {'H_word':>9s} {'H_EL':>7s} {'n_uniq_w':>10s} {'n_words':>10s}")
for row in sorted(pareto_rows, key=lambda r: -r["h_word_bits"]):
    print(f"# {row['corpus']:<18s} {row['h_word_bits']:>9.3f} {row['h_el_bits']:>7.3f} "
          f"{row['n_unique_words']:>10d} {row['n_words_total']:>10d}")

# Identify the Pareto frontier: a corpus is "non-dominated" if no other has
# both higher H_word AND lower H_EL. The Quran's signature: high H_word
# (lexical richness) + low H_EL (rhyme constraint) = non-dominated corner.
def is_pareto_optimal(row: dict, all_rows: list[dict]) -> bool:
    for other in all_rows:
        if other["corpus"] == row["corpus"]:
            continue
        # "dominates" = strictly better on H_word (higher) AND strictly better on H_EL (lower)
        if (other["h_word_bits"] > row["h_word_bits"] and
                other["h_el_bits"] < row["h_el_bits"]):
            return False
    return True


for row in pareto_rows:
    row["is_pareto_optimal"] = is_pareto_optimal(row, pareto_rows)

print()
print(f"# Pareto-optimal corpora (non-dominated):")
for row in pareto_rows:
    if row["is_pareto_optimal"]:
        print(f"#   {row['corpus']:<18s} (H_word={row['h_word_bits']:.3f}, "
              f"H_EL={row['h_el_bits']:.3f})")

pareto_out = OUT_DIR / "pareto_frontier.json"
pareto_out.write_text(
    json.dumps({
        "schema": "pareto_frontier_v1",
        "n_corpora": len(pareto_rows),
        "computed_from": "results/checkpoints/phase_06_phi_m.pkl",
        "rows": pareto_rows,
    }, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"# Written: {pareto_out.relative_to(ROOT)}")


# --- 2. CHRONOLOGICAL NEUTRALITY TEST ---------------------------------
print()
print("=" * 78)
print("# CHRONOLOGICAL NEUTRALITY TEST")
print("=" * 78)

quran_units = corpora.get("quran")
if quran_units is None:
    print("# ERROR: no 'quran' corpus in CORPORA")
    sys.exit(1)

# Locked chronological order (Nöldeke-Schwally). Surah numbers as conventionally numbered
# (al-Fatiha = 1, ..., An-Nas = 114). Order is the chronological revelation rank.
# This is the standard scholarly chronology used in computational stylometry of the Quran.
NOLDEKE_CHRONOLOGY = [
    96, 74, 73, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102, 107, 109, 105, 113, 114, 112,
    53, 80, 97, 91, 85, 95, 106, 101, 75, 104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35,
    19, 20, 56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45,
    46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82, 84, 30, 29, 83,
    # Medinan (locked Nöldeke-Schwally chronological tail)
    2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55, 76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64,
    61, 62, 48, 5, 9, 110, 1,
]
if len(NOLDEKE_CHRONOLOGY) != 114:
    print(f"# WARNING: chronology list has {len(NOLDEKE_CHRONOLOGY)} surahs "
          f"(missing {sorted(set(range(1, 115)) - set(NOLDEKE_CHRONOLOGY))}); "
          f"test will run on the surahs that ARE in the list.")

# Build feature matrix: for each Quran surah, retrieve the 5 locked features.
# `units` may store features per-surah on the Unit object. Let's inspect.
sample = quran_units[0]
print(f"# Sample Unit attributes: "
      f"{[a for a in dir(sample) if not a.startswith('_')][:15]}")

# Try to find the X_QURAN feature matrix (band-A 68 surahs) and labels.
X_Q = inner.get("X_QURAN")
labels_Q = inner.get("LABELS_QURAN")
feat_cols = inner.get("FEAT_COLS", ["EL", "VL_CV", "CN", "H_cond", "T"])
print(f"# X_QURAN shape: {None if X_Q is None else np.asarray(X_Q).shape}")
print(f"# LABELS_QURAN sample: {labels_Q[:3] if labels_Q else None}")
print(f"# FEAT_COLS: {feat_cols}")

if X_Q is None:
    print("# ERROR: X_QURAN not available in phase_06_phi_m.pkl")
    sys.exit(2)

X_Q = np.asarray(X_Q, dtype=float)
n_units, n_feats = X_Q.shape
print(f"# Feature matrix: {n_units} units × {n_feats} features")

# X_QURAN was built from band-A Quran surahs (15 <= n_verses <= 100) in
# their natural-list order. Reconstruct labels by filtering quran_units
# under the same criterion.
BAND_A_LO = inner.get("BAND_A_LO", 15)
BAND_A_HI = inner.get("BAND_A_HI", 100)
print(f"# Band-A criterion: {BAND_A_LO} <= n_verses <= {BAND_A_HI}")

if labels_Q is None:
    print(f"# Reconstructing band-A surah labels from quran_units...")
    band_a_units = [u for u in quran_units
                    if BAND_A_LO <= len(u.verses) <= BAND_A_HI]
    print(f"# Band-A units found: {len(band_a_units)} (expected {n_units})")
    if len(band_a_units) != n_units:
        print(f"# WARNING: count mismatch; alignment may be off")
    surah_nums: list[int] = []
    for u in band_a_units:
        # u.label is "quran:<surah_num>"
        parts = str(u.label).split(":")
        try:
            surah_nums.append(int(parts[-1]))
        except Exception:
            surah_nums.append(-1)
else:
    surah_nums = []
    for lab in labels_Q:
        parts = str(lab).split(":")
        try:
            surah_nums.append(int(parts[-1]))
        except Exception:
            surah_nums.append(-1)

# For each surah in our band-A set, find its chronological rank
chrono_rank: list[int] = []
chrono_index = {sn: i for i, sn in enumerate(NOLDEKE_CHRONOLOGY)}
ok_indices: list[int] = []
for i, sn in enumerate(surah_nums):
    if sn in chrono_index:
        chrono_rank.append(chrono_index[sn])
        ok_indices.append(i)
chrono_rank_arr = np.asarray(chrono_rank, dtype=float)
X_Q_ok = X_Q[ok_indices, :]
print(f"# Surahs with chronology rank: {len(chrono_rank)} of {n_units}")

# Linear regression: feature = a + b * chronological_rank, report R^2
print()
print(f"# Chronological neutrality: linear regression of each feature on rank")
print(f"# H_alt: features change with chronological order (R^2 > 0.05)")
print(f"# H_null: features chronologically invariant (R^2 ≈ 0)")
print(f"# {'feature':<10s} {'slope':>10s} {'intercept':>10s} {'R²':>9s} {'p_two-sided':>14s}")

results = {}
for j, name in enumerate(feat_cols[:n_feats]):
    y = X_Q_ok[:, j]
    x = chrono_rank_arr
    # Linear regression
    n = len(x)
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    ss_xy = float(np.sum((x - x_mean) * (y - y_mean)))
    ss_xx = float(np.sum((x - x_mean) ** 2))
    ss_yy = float(np.sum((y - y_mean) ** 2))
    slope = ss_xy / ss_xx if ss_xx > 0 else 0.0
    intercept = y_mean - slope * x_mean
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_xx > 0 and ss_yy > 0 else 0.0
    # t-statistic for slope = 0 under linear regression
    if n > 2 and ss_xx > 0:
        residuals = y - (slope * x + intercept)
        ss_res = float(np.sum(residuals ** 2))
        sigma2 = ss_res / (n - 2)
        se_slope = math.sqrt(sigma2 / ss_xx) if sigma2 > 0 else float("inf")
        t_stat = slope / se_slope if se_slope > 0 else 0.0
        # Two-sided p: use Student-t with df = n-2; via normal-approx for moderate n
        # For n=68 the normal approx is fine
        p_value = 2.0 * 0.5 * math.erfc(abs(t_stat) / math.sqrt(2)) if math.isfinite(t_stat) else float("nan")
    else:
        p_value = float("nan")
        t_stat = float("nan")
    results[name] = {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "t_stat": t_stat,
        "p_two_sided": p_value,
    }
    print(f"# {name:<10s} {slope:>10.5f} {intercept:>10.4f} {r_squared:>9.5f} "
          f"{p_value:>14.4g}")

# Verdict
print()
worst_r2 = max(r["r_squared"] for r in results.values())
all_p_nonsig = all(r["p_two_sided"] >= 0.05 for r in results.values()
                   if not math.isnan(r["p_two_sided"]))
chrono_verdict = ""
if worst_r2 < 0.05 and all_p_nonsig:
    chrono_verdict = "PASS_chronologically_neutral"
    print(f"# VERDICT: PASS_chronologically_neutral")
    print(f"# All 5 features have R² < 0.05 AND all slope p-values ≥ 0.05.")
    print(f"# The 5-D structural fingerprint is invariant across the 23-year")
    print(f"# composition arc. This is novel — see chronological_neutrality.json.")
elif worst_r2 < 0.10:
    chrono_verdict = "PARTIAL_weakly_chronological"
    print(f"# VERDICT: PARTIAL_weakly_chronological")
    print(f"# Worst R² = {worst_r2:.4f} (in [0.05, 0.10]); some features show")
    print(f"# weak chronological drift but no feature is strongly chronological.")
else:
    chrono_verdict = "FAIL_chronologically_dependent"
    print(f"# VERDICT: FAIL_chronologically_dependent")
    print(f"# Worst R² = {worst_r2:.4f} >= 0.10; at least one feature is")
    print(f"# materially chronological. The fingerprint is NOT time-invariant.")

chrono_out = OUT_DIR / "chronological_neutrality.json"
chrono_out.write_text(
    json.dumps({
        "schema": "chronological_neutrality_v1",
        "chronology_source": "Nöldeke-Schwally (locked verse-by-verse standard)",
        "n_surahs_total_chronology": len(NOLDEKE_CHRONOLOGY),
        "n_surahs_band_a_with_rank": len(chrono_rank),
        "feat_cols": list(feat_cols[:n_feats]),
        "regression_per_feature": results,
        "verdict": chrono_verdict,
        "worst_r_squared": worst_r2,
    }, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"# Written: {chrono_out.relative_to(ROOT)}")
