"""Quick scan of existing p_max / H_EL data across corpora from F63/F64."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
exp109 = json.load(open(ROOT / "results/auxiliary/_phi_universal_xtrad_sizing.json", encoding="utf-8"))
exp111_path = ROOT / "results/experiments/exp111_F63_rigveda_falsification/exp111_F63_rigveda_falsification.json"
exp111 = json.load(open(exp111_path, encoding="utf-8"))

print(f"\n=== exp109 medians (11 corpora) ===")
print(f'{"corpus":<20} {"p_max":>10} {"H_EL":>10}')
print("-" * 42)
for k, v in exp109["medians"].items():
    print(f'{k:<20} {v["p_max"]:>10.4f} {v["H_EL"]:>10.4f}')

print(f"\n=== exp111 medians ===")
print(f'{"corpus":<20} {"p_max":>10} {"H_EL":>10}')
print("-" * 42)
if "medians" in exp111:
    for k, v in exp111["medians"].items():
        if isinstance(v, dict) and "p_max" in v:
            print(f'{k:<20} {v["p_max"]:>10.4f} {v["H_EL"]:>10.4f}')
else:
    print(json.dumps({k: v for k, v in exp111.items() if "median" in k.lower() or k in ["pool", "verdict"]}, indent=2)[:500])
