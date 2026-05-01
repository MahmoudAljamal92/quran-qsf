"""Quick inspect: print the exp157 sensitivity grid in a readable form."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECEIPT = ROOT / "results" / "experiments" / "exp157_beta_from_cognitive_channel" / "exp157_beta_from_cognitive_channel.json"

d = json.loads(RECEIPT.read_text(encoding="utf-8"))
grid = d["results"]["route_b_finite_buffer"]["sensitivity_grid"]

print("Sensitivity grid (B=Miller buffer, eps=leak target):")
print(f"{'cell':<14} {'B':<3} {'eps':<6} {'beta_opt':<10} {'pmax_at_opt':<12}")
for k, v in grid.items():
    if "beta_opt" in v:
        print(f"{k:<14} {v['B']:<3} {v['eps']:<6} {v['beta_opt']:<10.4f} {v['pmax_at_opt']:<12.4f}")
    else:
        print(f"{k:<14} ERROR: {v.get('error', '?')}")

print()
print("Pool stats from V3.21:")
print(json.dumps(d["pool_statistics_from_v321"], indent=2))
print()
print("Route C details:")
print(json.dumps(d["results"]["route_c_regression"], indent=2))
print()
print("Route B central:")
print(json.dumps(d["results"]["route_b_finite_buffer"]["central_operating_point"], indent=2))
