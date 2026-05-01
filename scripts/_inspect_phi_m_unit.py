"""Inspect what attributes a unit object in phase_06_phi_m has."""
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._lib import load_phase  # noqa: E402

phi = load_phase("phase_06_phi_m")
state = phi.get("state", phi)
CORPORA = state.get("CORPORA", state.get("corpora"))

q = list(CORPORA.get("quran", []))
print(f"# n_quran units: {len(q)}")
if q:
    u = q[0]
    print(f"# unit type: {type(u).__name__}")
    attrs = [a for a in dir(u) if not a.startswith("_")]
    print(f"# unit attributes (non-dunder): {attrs}")
    for attr in attrs:
        val = getattr(u, attr, None)
        if callable(val):
            try:
                v2 = val()
                print(f"#   {attr}() -> {v2!r}")
            except Exception as e:
                print(f"#   {attr}: callable, error: {e}")
        elif hasattr(val, "__len__") and not isinstance(val, str):
            print(f"#   {attr}: type={type(val).__name__}, len={len(val)}")
        else:
            print(f"#   {attr}: {val!r}")
