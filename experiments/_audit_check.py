# Retroactive zero-trust audit checks for exp69-73. Run once, safe to delete.
import sys, numpy as np
sys.path.insert(0, '.')
from experiments._lib import load_phase

phi = load_phase('phase_06_phi_m')
state = phi['state']

# 1. Verify Phi_M computation (exp69)
X_Q = np.asarray(state['X_QURAN'])
mu = np.asarray(state['mu'])
S_inv = np.asarray(state['S_inv'])
diffs = X_Q - mu
phi_m = [float(np.sqrt(d @ S_inv @ d)) for d in diffs]
print("=== exp69 Phi_M verification ===")
print(f"  Phi_M range: {min(phi_m):.3f} - {max(phi_m):.3f}, mean={np.mean(phi_m):.3f}")
print(f"  Known Q_COV: {state.get('QURAN_COV', '?')}")
print(f"  Band-A: {state.get('BAND_A_LO')}-{state.get('BAND_A_HI')}")

# 2. exp70 — Check if accuracy is in-sample (NO cross-val was done)
print("\n=== exp70 in-sample bias check ===")
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
feat_cols = list(state['FEAT_COLS'])
t_idx = feat_cols.index('T')
el_idx = feat_cols.index('EL')
X_Q_2D = X_Q[:, [t_idx, el_idx]]
X_C_2D = np.asarray(state['X_CTRL_POOL'])[:, [t_idx, el_idx]]
X_all = np.vstack([X_Q_2D, X_C_2D])
y_all = np.array([1]*len(X_Q_2D) + [0]*len(X_C_2D))
cv_scores = cross_val_score(SVC(kernel='linear', C=1.0), X_all, y_all, cv=5, scoring='roc_auc')
print(f"  In-sample AUC reported: 0.9975")
print(f"  5-fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  Inflation: {0.9975 - cv_scores.mean():.4f}")

# 3. exp71 — Verify poetry word counts (is 7 per line real?)
CORPORA = state['CORPORA']
for cname in ['poetry_jahili', 'poetry_abbasi']:
    units = CORPORA.get(cname, [])
    wcs = []
    for u in units:
        for v in u.verses:
            wcs.append(len(v.split()))
    wcs = np.array(wcs)
    print(f"\n=== exp71 {cname} word-count sanity ===")
    print(f"  n_verses={len(wcs)}, mean={wcs.mean():.1f}, median={np.median(wcs):.0f}")
    print(f"  mode={np.bincount(wcs).argmax()}, min={wcs.min()}, max={wcs.max()}")
    print(f"  pct(wc==7): {(wcs==7).mean()*100:.1f}%")
    print(f"  pct(wc in 6-8): {((wcs>=6)&(wcs<=8)).mean()*100:.1f}%")

# 4. exp73 — Permutation test was trivially p=1.0
print("\n=== exp73 permutation test audit ===")
quran_units = CORPORA.get('quran', [])
q_vc = [len(u.verses) for u in quran_units]
def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i*i <= n:
        if n % i == 0 or n % (i+2) == 0: return False
        i += 6
    return True
n_prime = sum(1 for vc in q_vc if is_prime(vc))
print(f"  Observed primes: {n_prime}")
print(f"  ISSUE: permutation shuffles same values => prime count is INVARIANT")
print(f"  This test was trivially p=1.0 — it tests nothing useful")
print(f"  Correct approach: compare to random draws from same distribution")

# Better test: bootstrap from empirical distribution
rng = np.random.RandomState(42)
boot_primes = []
for _ in range(10000):
    # Resample verse counts with replacement from all corpora
    sampled = rng.choice(q_vc, size=114, replace=True)
    boot_primes.append(sum(1 for vc in sampled if is_prime(vc)))
boot_primes = np.array(boot_primes)
p_boot = float(np.mean(boot_primes >= n_prime))
print(f"  Bootstrap (resample from Quran VCs): mean={boot_primes.mean():.1f}, p(>={n_prime})={p_boot:.4f}")
