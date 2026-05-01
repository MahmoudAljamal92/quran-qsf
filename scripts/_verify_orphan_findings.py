"""Verify the 4 orphan findings replicate on raw-data calibration before
we promote them to 9-D Phi_M. Each finding must meet a minimum bar:
  - Measurable on all 5+ corpora (Quran + 4+ Arabic controls)
  - Band-A [15, 100] Cohen's d of Quran-vs-controls is >= 0.4 in MAGNITUDE
  - Effect direction matches the MASTER_FINDINGS_REPORT claim
    (signed check; a sign-flip vs the master claim fails the test even
    when |d| >= 0.4. Audit-fix M2 2026-04-26: previously |d| was used
    without sign and would have rubber-stamped a flipped finding.)

A finding fails for one of two reasons, distinguished in the verdict:
  [DROP_MAGNITUDE]  : |d| < 0.4, no useful effect
  [DROP_SIGN_FLIP]  : |d| >= 0.4 but sign opposite to MASTER claim
And passes only as:
  [KEEP]            : |d| >= 0.4 AND sign matches (or sign is informational)

Per-test expected_sign:
  F6 anti-length-regularity : -1  (MASTER d=-0.670; Quran rho < ctrl rho)
  F7 semantic anti-repetition: -1  (MASTER d=-0.475; Quran Jaccard < ctrl)
  F8a Hurst verse-length    :  0  (MASTER report contradicts itself on
                                   Quran-vs-ctrl direction; H=0.90 quoted
                                   in track1 vs "Bible HIGHER Hurst on
                                   most gap metrics" in followup. Sign
                                   is informational pending replication.)
  F8b Hurst delta           :  0  (same as F8a)
"""
from __future__ import annotations
import os, sys, math
from collections import Counter
import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.raw_loader import (
    load_quran_bare, load_poetry_by_era, load_ksucca,
    load_arabic_bible_xlsx, load_hindawi,
    # hadith_bukhari QUARANTINED — same policy as src/clean_pipeline.py
)

BAND_A = (15, 100)
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
def strip_d(s):
    return ''.join(c for c in str(s) if c not in DIAC)

# -------------------------------------------------------------------
# F6 Anti-length-regularity: Spearman rho(len_i, len_{i+1})
#     Interpretation: if rho < 0, adjacent verse lengths anti-correlate
#     (the next verse compensates the current one).
#     MASTER claim: Quran d = -0.670 (negative = "more anti-regular than ctrl")
# -------------------------------------------------------------------
def f6_anti_length_regularity(verses):
    lens = [len(strip_d(v).split()) for v in verses]
    if len(lens) < 4:
        return None
    a = np.array(lens[:-1])
    b = np.array(lens[1:])
    # Spearman
    r, _ = stats.spearmanr(a, b)
    if np.isnan(r):
        return None
    return float(r)

# -------------------------------------------------------------------
# F7 Semantic anti-repetition: mean Jaccard(adjacent verse token sets)
#     MASTER claim: Quran 0.042 vs ctrl 0.190, d = -0.475
# -------------------------------------------------------------------
def f7_adj_jaccard(verses):
    toks = [set(strip_d(v).split()) for v in verses]
    # drop empty
    toks = [t for t in toks if t]
    if len(toks) < 2:
        return None
    jacs = []
    for i in range(len(toks) - 1):
        a, b = toks[i], toks[i+1]
        u = a | b
        if not u:
            continue
        jacs.append(len(a & b) / len(u))
    if not jacs:
        return None
    return float(np.mean(jacs))

# -------------------------------------------------------------------
# F8 Hurst exponent via rescaled-range (R/S) on verse length sequence
#     Also F8b: on differenced (delta) sequence
#     MASTER claim: Quran H=0.90 at verse level, 0.81 at delta level
# -------------------------------------------------------------------
def hurst_rs(x, min_chunks=4):
    """Rescaled-range Hurst estimator. Returns None if sequence too short."""
    x = np.asarray(x, dtype=float)
    N = len(x)
    if N < 10:
        return None
    # use chunk sizes that produce at least min_chunks windows
    chunks = []
    for chunk in [8, 12, 16, 24, 32, 48, 64, 96]:
        if N // chunk >= min_chunks:
            chunks.append(chunk)
    if len(chunks) < 2:
        return None
    log_n, log_rs = [], []
    for n in chunks:
        n_windows = N // n
        rs_vals = []
        for i in range(n_windows):
            w = x[i*n:(i+1)*n]
            mean = w.mean()
            Y = np.cumsum(w - mean)
            R = Y.max() - Y.min()
            S = w.std(ddof=0)
            if S <= 0:
                continue
            rs_vals.append(R / S)
        if rs_vals:
            log_n.append(math.log(n))
            log_rs.append(math.log(np.mean(rs_vals)))
    if len(log_n) < 2:
        return None
    slope, _ = np.polyfit(log_n, log_rs, 1)
    return float(slope)

def f8a_hurst_verse_length(verses):
    lens = [len(strip_d(v).split()) for v in verses]
    return hurst_rs(lens)

def f8b_hurst_delta(verses):
    lens = np.array([len(strip_d(v).split()) for v in verses], dtype=float)
    if len(lens) < 12:
        return None
    d = np.diff(lens)
    return hurst_rs(d)

# -------------------------------------------------------------------
# Run on all corpora, Band-A only
# -------------------------------------------------------------------
def compute_feature(units, fn, band_a=True):
    out = []
    for u in units:
        n = u.n_verses()
        if band_a and not (BAND_A[0] <= n <= BAND_A[1]):
            continue
        val = fn(u.verses)
        if val is not None:
            out.append({'label': u.label, 'n': n, 'val': val,
                        'corpus': u.corpus})
    return out

def summarise(name, quran_vals, ctrl_vals):
    q = np.array([r['val'] for r in quran_vals])
    c = np.array([r['val'] for r in ctrl_vals])
    if len(q) < 2 or len(c) < 2:
        return {'name': name, 'error': 'no data'}
    # Pooled sample variance (ddof=1), matches src/clean_pipeline._cohens_d
    pv = ((len(q) - 1) * q.var(ddof=1) + (len(c) - 1) * c.var(ddof=1)) \
         / (len(q) + len(c) - 2)
    d = (q.mean() - c.mean()) / math.sqrt(pv) if pv > 0 else float('nan')
    u_stat, p_two = stats.mannwhitneyu(q, c, alternative='two-sided')
    return {
        'name': name,
        'q_n': len(q), 'q_mean': q.mean(), 'q_std': q.std(ddof=1),
        'c_n': len(c), 'c_mean': c.mean(), 'c_std': c.std(ddof=1),
        'cohens_d': float(d),
        'mwu_p_two': float(p_two),
    }

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
print('[load] corpora...')
quran = load_quran_bare()
poetry = load_poetry_by_era()
ksucca = load_ksucca()
bible = load_arabic_bible_xlsx()
hindawi = load_hindawi()
# hadith_bukhari QUARANTINED per src/clean_pipeline.py ARABIC_CORPORA_FOR_CONTROL
ctrls = {
    'poetry_jahili':  poetry['poetry_jahili'],
    'poetry_islami':  poetry['poetry_islami'],
    'poetry_abbasi':  poetry['poetry_abbasi'],
    'ksucca':         ksucca,
    'bible':          bible,
    'hindawi':        hindawi,
}
all_ctrl_units = []
for v in ctrls.values():
    all_ctrl_units.extend(v)
print(f'  quran: {len(quran)}  ctrl total: {len(all_ctrl_units)}')

# -------------------------------------------------------------------
# Test each feature
# -------------------------------------------------------------------
# Each row: (display_name, fn, expected_sign).
# expected_sign in {-1, 0, +1}; 0 means "MASTER report does not pin a sign,
# treat the magnitude alone as the verdict and report the sign as
# informational" (see module docstring for per-test justification).
for fname, fn, expected_sign in [
    ('F6 anti-length-regularity (Spearman rho adj lens)', f6_anti_length_regularity, -1),
    ('F7 semantic anti-repetition (adj Jaccard)',         f7_adj_jaccard,             -1),
    ('F8a Hurst verse-length R/S',                        f8a_hurst_verse_length,      0),
    ('F8b Hurst delta R/S',                               f8b_hurst_delta,             0),
]:
    print()
    print('=' * 78)
    print(f'{fname}')
    print('=' * 78)
    q_vals = compute_feature(quran, fn)
    c_vals = compute_feature(all_ctrl_units, fn)
    s = summarise(fname, q_vals, c_vals)
    if 'error' in s:
        print(f'  ERROR: {s["error"]}')
        continue
    print(f"  Quran (n={s['q_n']:4d}): mean={s['q_mean']:+.4f}  std={s['q_std']:.4f}")
    print(f"  Ctrl  (n={s['c_n']:4d}): mean={s['c_mean']:+.4f}  std={s['c_std']:.4f}")
    print(f"  Cohen d (Quran-ctrl)  : {s['cohens_d']:+.3f}")
    print(f"  MWU p two-sided        : {s['mwu_p_two']:.3g}")
    # Per-corpus breakdown
    print('  Per-corpus (Band A):')
    qv = np.array([r['val'] for r in q_vals])  # compute once
    for cname, cu in ctrls.items():
        cvs = compute_feature(cu, fn)
        if len(cvs) < 2:
            continue
        cv = np.array([r['val'] for r in cvs])
        # pooled sample variance (ddof=1)
        pv = ((len(qv) - 1) * qv.var(ddof=1) + (len(cv) - 1) * cv.var(ddof=1)) \
             / (len(qv) + len(cv) - 2)
        d_local = ((qv.mean() - cv.mean()) / math.sqrt(pv)
                   if pv > 0 else float('nan'))
        print(f"    {cname:15s} n={len(cv):4d} mean={cv.mean():+.4f}  d_quran={d_local:+.3f}")
    # Threshold 0.4 is the pre-declared "useful effect" bar — between
    # Cohen's conventional small (0.2) and medium (0.5). Audit-fix M2:
    # also require the SIGN to match the MASTER claim when one is pinned;
    # a sign-flip is fatal even with |d| >= 0.4.
    d = s['cohens_d']
    big = abs(d) >= 0.4
    if not big:
        verdict = '[DROP_MAGNITUDE]'
        reason = f'|d|={abs(d):.3f} < 0.4'
    elif expected_sign == 0:
        verdict = '[KEEP]'
        reason = f'|d|={abs(d):.3f} >= 0.4 (sign informational)'
    elif (d > 0 and expected_sign > 0) or (d < 0 and expected_sign < 0):
        verdict = '[KEEP]'
        reason = (f'|d|={abs(d):.3f} >= 0.4 and sign matches MASTER '
                  f'(expected={expected_sign:+d}, got={int(np.sign(d)):+d})')
    else:
        verdict = '[DROP_SIGN_FLIP]'
        reason = (f'|d|={abs(d):.3f} >= 0.4 BUT sign flipped vs MASTER '
                  f'(expected={expected_sign:+d}, got={int(np.sign(d)):+d})')
    print(f'  {verdict} ({reason})')
