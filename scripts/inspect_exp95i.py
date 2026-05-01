"""Quick diagnostic for exp95i receipt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
recpath = ROOT / "results" / "experiments" / "exp95i_bigram_shift_detector" / "exp95i_bigram_shift_detector.json"
r = json.load(open(recpath, encoding="utf-8"))
ps = r["per_surah"]

print("Audit violations:", r["audit"]["audit_violations"])
print("Surahs with zero ctrl:", r["audit"]["surahs_with_zero_ctrl"])
print()
q108 = ps.get("Q:108")
if q108:
    print("Q:108 entry:")
    for k, v in q108.items():
        print(f"  {k}: {v}")

# Sort by canon length
sorted_surahs = sorted(ps.items(), key=lambda x: x[1]["n_canon"])
print()
print("10 shortest surahs:")
for label, p in sorted_surahs[:10]:
    print(f"  {label:8s}: n_canon={p['n_canon']:5d}, n_ctrl_matched={p['n_ctrl_matched']:3d}, n_variants={p['n_variants']}")

print()
print("10 longest surahs:")
for label, p in sorted_surahs[-10:]:
    print(f"  {label:8s}: n_canon={p['n_canon']:5d}, n_ctrl_matched={p['n_ctrl_matched']:3d}, n_variants={p['n_variants']}")

# Distribution of n_ctrl_matched
print()
print("Distribution of n_ctrl_matched across 114 surahs:")
import collections
c = collections.Counter(p["n_ctrl_matched"] for p in ps.values())
for k in sorted(c):
    print(f"  n_ctrl={k}: {c[k]} surahs")
