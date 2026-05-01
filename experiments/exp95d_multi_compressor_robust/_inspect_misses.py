"""Quick inspector for the Q:099 single miss in exp95d sub-run 4.

Read-only: only loads the sealed exp95d receipt and prints diagnostic info
on which variants were missed and whether any single compressor caught them.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RECEIPT = ROOT / "results" / "experiments" / "exp95d_multi_compressor_robust" / "exp95d_multi_compressor_robust.json"

with open(RECEIPT, "r", encoding="utf-8") as f:
    r = json.load(f)

print(f"exp95d verdict: {r['verdict']}")
print(f"summary.q99_K2_recall: {r['summary']['q99_K2_recall']}")
print()

for sub in r["sub_receipts"]:
    label = sub["surah_label"]
    seed = sub["seed"]
    if "per_variant" not in sub:
        continue  # exp95c slot
    misses_K2 = [v for v in sub["per_variant"] if v["K_fired"] < 2]
    misses_K1 = [v for v in sub["per_variant"] if v["K_fired"] < 1]
    fired_K1_count = sum(1 for v in sub["per_variant"] if v["K_fired"] >= 1)
    print(f"=== seed={seed}  label={label}  N={len(sub['per_variant'])} ===")
    print(f"  K=1 (any-compressor) recall: "
          f"{fired_K1_count}/{len(sub['per_variant'])} "
          f"= {fired_K1_count/len(sub['per_variant']):.6f}")
    print(f"  K=2 misses: {len(misses_K2)}    K=1 misses: {len(misses_K1)}")
    if misses_K2:
        print(f"  K=2 missed variants:")
        for m in misses_K2:
            saved_by_K1 = sum(m["fires"].values()) >= 1
            print(f"    pos={m['pos']:>2}  {m['orig']!r}->{m['repl']!r}  "
                  f"K_fired={m['K_fired']}  saved_by_K1={saved_by_K1}")
            print(f"      ncd: {m['ncd']}")
            print(f"      fires: {m['fires']}")
    print()
