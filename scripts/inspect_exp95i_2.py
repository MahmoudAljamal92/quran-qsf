"""Deeper diagnostic: would exp95i have passed without Q:108?"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
recpath = ROOT / "results" / "experiments" / "exp95i_bigram_shift_detector" / "exp95i_bigram_shift_detector.json"
r = json.load(open(recpath, encoding="utf-8"))
ps = r["per_surah"]

# Variant delta histogram
print("Variant Delta_bigram summary:")
print(f"  min/max: {r['variant_delta_summary']['min']} / {r['variant_delta_summary']['max']}")
print(f"  p01/p50/p99: {r['variant_delta_summary']['p01']} / {r['variant_delta_summary']['p50']} / {r['variant_delta_summary']['p99']}")
print()
# Per-surah variant delta range
print("Per-surah var_delta_min and var_delta_max (sorted by max):")
sorted_by_max = sorted(ps.items(), key=lambda x: x[1]['var_delta_max'] or 0, reverse=True)
for label, p in sorted_by_max[:5]:
    print(f"  {label}: var_delta_min={p['var_delta_min']}, var_delta_max={p['var_delta_max']}, n_variants={p['n_variants']}")
print()

# Per-surah ctrl_delta_min and p05 distribution (where n_ctrl > 0)
print("Per-surah ctrl_delta_min and ctrl_delta_p05 (10 lowest ctrl_delta_min):")
ctrl_items = [(label, p) for label, p in ps.items() if p['n_ctrl_matched'] > 0]
sorted_by_ctrl_min = sorted(ctrl_items, key=lambda x: x[1]['ctrl_delta_min'])
for label, p in sorted_by_ctrl_min[:10]:
    print(f"  {label}: n_canon={p['n_canon']:5d}, n_ctrl={p['n_ctrl_matched']:3d}, ctrl_delta_min={p['ctrl_delta_min']:.2f}, ctrl_delta_p05={p['ctrl_delta_p05_per_surah']:.2f}, ctrl_delta_max={p['ctrl_delta_max']:.2f}")
print()
print("10 highest ctrl_delta_min:")
for label, p in sorted_by_ctrl_min[-10:]:
    print(f"  {label}: n_canon={p['n_canon']:5d}, n_ctrl={p['n_ctrl_matched']:3d}, ctrl_delta_min={p['ctrl_delta_min']:.2f}, ctrl_delta_p05={p['ctrl_delta_p05_per_surah']:.2f}")

# Hypothetical: if Q:108 had been excluded or if we had used global ctrl pool
print()
print("--- Hypothetical re-evaluation (excluding Q:108, with tau set on global ctrl pool) ---")
print()

# Recompute global ctrl pool (excluding any from Q:108 — but Q:108 had 0 anyway)
all_ctrl_d = []  # We don't have per-ctrl-Δ in receipt, only per-surah summary stats.
# We need to estimate. Use the global ctrl summary.
print("Global ctrl-null summary (from receipt):")
cn = r["ctrl_null_summary"]
print(f"  n_pool: {cn['n_pool']}")
print(f"  min/p01/p05/p25/p50/p95/max: {cn['min']:.2f} / {cn['p01']:.2f} / {cn['p05']:.2f} / {cn['p25']:.2f} / {cn['p50']:.2f} / {cn['p95']:.2f} / {cn['max']:.2f}")

tau_high = cn['p05']
print(f"\n  Implied tau_high = p05 = {tau_high:.4f}")

# Variant delta is bounded by 2.0 — so any tau_high >= 2 gives recall = 1 
# (since 0 < Delta <= 2 <= tau_high).
# What is the smallest variant delta we observed? Should be 0.5 from edge substitutions.
# Question: is variant min > 0?
print()
print(f"  Variant Delta range: [{r['variant_delta_summary']['min']}, {r['variant_delta_summary']['max']}]")
print(f"  Implied recall (variants with 0 < Delta <= tau_high): for tau_high >= 2.0, = 100%")

# If the smallest variant delta is > 0, every variant fires with tau_high >= 2.0
if tau_high >= 2.0:
    print(f"  Since tau_high ({tau_high:.2f}) >= 2.0 (max variant delta), all variants would fire.")
    print(f"  Predicted aggregate recall: 1.0000 (perfect closure across the 113 surahs that have ctrl).")
else:
    print(f"  WARNING: tau_high = {tau_high:.4f} < 2.0; some variants would NOT fire.")
    print(f"  Need per-surah Delta detail to compute exact recall.")

# Per-surah ctrl_delta_p05 — for surahs where this is < 2.0, the per-surah-FPR bound is exceeded
print()
print("Per-surah where ctrl_delta_p05 < 2.0 (i.e., per-surah FPR > 0.05 even with global tau):")
problematic = [(l, p) for l, p in ctrl_items if p['ctrl_delta_p05_per_surah'] is not None and p['ctrl_delta_p05_per_surah'] < 2.0]
print(f"  {len(problematic)} surahs")
for label, p in problematic[:20]:
    print(f"    {label}: ctrl_p05={p['ctrl_delta_p05_per_surah']:.3f}, ctrl_min={p['ctrl_delta_min']:.3f}")
