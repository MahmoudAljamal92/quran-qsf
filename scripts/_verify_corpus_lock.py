# -*- coding: utf-8 -*-
"""Quick smoke-test that corpus_lock.json parses and reports its contents."""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root = Path(__file__).resolve().parent.parent
p = root / "results" / "integrity" / "corpus_lock.json"

with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

print("OK: corpus_lock.json parses cleanly")
print(f"  files               : {len(data['files'])} entries")
print(f"  cross_tradition_corpora     : {list(data['cross_tradition_corpora'].keys())}")
print(f"  cross_tradition_loaders     : {list(data['cross_tradition_loaders'].keys())}")
ce = data['cross_tradition_experiments_2026-04-25']
print(f"  cross_tradition_experiments : {len(ce)} experiments")
print("  verdicts:")
for k, v in ce.items():
    print(f"    {k:50s}  {v['verdict']}")
print(f"  combined hash               : {data['combined']}")
print(f"  timestamp                   : {data['timestamp']}")
