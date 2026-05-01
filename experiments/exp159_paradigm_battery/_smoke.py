import os, sys, time, numpy as np
os.environ.setdefault("QSF_RELAX_DRIFT", "1")
sys.path.insert(0, r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
import importlib.util
spec = importlib.util.spec_from_file_location("exp159", r"C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp159_paradigm_battery\run.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from experiments._lib import load_phase
phi = load_phase("phase_06_phi_m")
units = phi["state"]["CORPORA"]["quran"]
x = m.verse_lengths(units)
print("Quran series N =", len(x))
t0 = time.time()
r = m.rqa_metrics(x)
det = r["DET"]
print(f"RQA call: {time.time()-t0:.2f}s   N={r['N']} RR={r['RR']:.4f} DET={det:.4f} LAM={r['LAM']:.4f} L_max={r['L_max']}")
t0 = time.time()
xs = m.ar1_surrogate(x, np.random.default_rng(0))
r2 = m.rqa_metrics(xs)
det2 = r2["DET"]
print(f"AR1 surrogate + RQA: {time.time()-t0:.2f}s   DET={det2:.4f}")
t0 = time.time()
xs = m.iaaft_surrogate(x, np.random.default_rng(0), iters=30)
r3 = m.rqa_metrics(xs)
det3 = r3["DET"]
print(f"IAAFT surrogate + RQA: {time.time()-t0:.2f}s   DET={det3:.4f}")
