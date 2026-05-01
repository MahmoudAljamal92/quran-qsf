"""Verify every self_check_*.json receipt reports ok=True, 0 mutations.
Also re-hash every protected file NOW and print live hashes for manual
comparison. NOTE: this script checks receipt consistency, not comparison
against an external golden baseline."""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import _protected_file_hashes, _protected_dir_hashes

receipts = sorted(glob.glob(str(_ROOT / "results" / "experiments" / "*" / "self_check_*.json")))

print(f"Found {len(receipts)} self-check receipts\n")
ok_total = 0
changed_total = 0
for r in receipts:
    with open(r, "r", encoding="utf-8") as f:
        d = json.load(f)
    ok = bool(d.get("ok", False))
    ch = len(d.get("changed", []))
    ok_total += int(ok)
    changed_total += ch
    short = r.split("results" + ("\\" if "\\" in r else "/"))[-1]
    print(f"  {'PASS' if ok else 'FAIL'}  changed={ch:2d}  {short}")

print(f"\nSummary: {ok_total}/{len(receipts)} PASS  |  total mutations: {changed_total}\n")

# Re-hash now and print live state for manual inspection.
# NOTE: we do NOT compare against a stored baseline — we only verify
# that receipts are internally consistent and print current hashes.
live_files = _protected_file_hashes()
live_dirs = _protected_dir_hashes()
n_live_files = len(live_files)
n_live_dir_files = sum(len(v) for v in live_dirs.values())
print(f"Live protected files: {n_live_files}")
print(f"Live protected-dir files: {n_live_dir_files}")

# Spot-check a few critical ones by name
critical = [
    "notebooks\\ultimate\\QSF_ULTIMATE.ipynb",
    "results\\ULTIMATE_REPORT.json",
    "results\\ULTIMATE_SCORECARD.md",
    "results\\CLEAN_PIPELINE_REPORT.json",
]
for c in critical:
    matches = [k for k in live_files if k.replace("/", "\\") == c]
    if matches:
        h = live_files[matches[0]]
        print(f"  {c:<55s}  sha256={h[:16]}...{h[-8:]}")
    else:
        print(f"  {c:<55s}  MISSING / NOT PROTECTED")

if changed_total == 0 and ok_total == len(receipts):
    print("\nALL RECEIPTS PASS, ZERO MUTATIONS. Sandbox integrity OK.")
    sys.exit(0)
else:
    print("\nMUTATION DETECTED. INVESTIGATE IMMEDIATELY.")
    sys.exit(1)
