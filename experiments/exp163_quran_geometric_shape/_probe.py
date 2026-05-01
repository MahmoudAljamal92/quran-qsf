import sys
sys.path.insert(0, r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from experiments._lib import load_phase
phi = load_phase("phase_06_phi_m")
s = phi["state"]
print("FEAT_COLS:", s["FEAT_COLS"])
print("X_QURAN shape:", s["X_QURAN"].shape, "X_CTRL_POOL:", s["X_CTRL_POOL"].shape)
print("BAND_A:", s["BAND_A_LO"], "..", s["BAND_A_HI"])
print()

print("FEATS type:", type(s["FEATS"]).__name__)
if isinstance(s.get("FEATS"), dict):
    for k, v in list(s["FEATS"].items())[:8]:
        if hasattr(v, "shape"):
            print(f"  FEATS[{k}].shape = {v.shape}")
        elif isinstance(v, dict):
            print(f"  FEATS[{k}] dict keys: {list(v.keys())[:5]}")
        else:
            tname = type(v).__name__
            ln = len(v) if hasattr(v, "__len__") else "?"
            print(f"  FEATS[{k}] = {tname}, len={ln}")
print()

print("ARABIC_CTRL_POOL type:", type(s["ARABIC_CTRL_POOL"]).__name__)
if isinstance(s.get("ARABIC_CTRL_POOL"), dict):
    for k, v in s["ARABIC_CTRL_POOL"].items():
        if hasattr(v, "shape"):
            print(f"  ARABIC_CTRL_POOL[{k}].shape = {v.shape}")
        else:
            tname = type(v).__name__
            ln = len(v) if hasattr(v, "__len__") else "?"
            print(f"  ARABIC_CTRL_POOL[{k}] = {tname}, len={ln}")
print()

# Look for per-corpus feature matrices
print("Are there per-corpus matrices? ALL_RESULTS:")
if isinstance(s.get("ALL_RESULTS"), dict):
    print(" keys:", list(s["ALL_RESULTS"].keys())[:20])
elif s.get("ALL_RESULTS") is not None:
    print(" type:", type(s["ALL_RESULTS"]).__name__)
