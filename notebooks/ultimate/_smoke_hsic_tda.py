"""
Smoke test for the HSIC + TDA additions in QSF_ULTIMATE.ipynb (audit v3).

Runs the MINIMUM set of cells needed to execute:
  - HSIC block in Cell 40 (EL-CN independence)
  - HSIC 5-channel block at the tail of Cell 55
  - Phase 22 Cell 131 (TDA appendix; USE_TDA=False path and USE_TDA=True
    path when ripser is available).

Does NOT run the full pipeline; we stub out expensive state with synthetic
data so the new blocks execute end-to-end in < 5 s.
"""
from __future__ import annotations
import json, sys, traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NB = json.loads((HERE / "QSF_ULTIMATE.ipynb").read_text(encoding="utf-8"))


def _pick_cell(prefix: str) -> str:
    """Return the source of the (unique) code cell whose first non-blank
    line starts with ``prefix`` — typically '# === Cell NN · ...'."""
    for cell in NB["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        first = src.strip().splitlines()[0] if src.strip() else ""
        if first.startswith(prefix):
            return src
    raise KeyError(f"no code cell starts with {prefix!r}")


# --------------------------------------------------------- synthetic fixtures
SEED = 42
rng = np.random.default_rng(SEED)

# Feature columns and Band A range match the notebook
FEAT_COLS = ['EL', 'VL_CV', 'CN', 'H_cond', 'T']
BAND_A_LO, BAND_A_HI = 15, 100

# Fake FEATS dict shape: {corpus_name: [rec, rec, ...]} where rec has
# n_verses, EL, VL_CV, CN, H_cond, T.
def _fake_corpus(n_surahs: int, base_seed: int):
    r = np.random.default_rng(base_seed)
    out = []
    for _ in range(n_surahs):
        out.append({
            'n_verses': int(r.integers(20, 90)),
            'EL':      float(r.uniform(0.3, 0.9)),
            'VL_CV':   float(r.uniform(0.1, 0.4)),
            'CN':      float(r.uniform(0.0, 0.2)),
            'H_cond':  float(r.uniform(5.0, 7.5)),
            'T':       float(r.uniform(-0.2, 0.4)),
        })
    return out

FEATS = {
    'quran':         _fake_corpus(80, SEED + 1),
    'poetry_abbasi': _fake_corpus(50, SEED + 2),
    'arabic_bible':  _fake_corpus(60, SEED + 3),
    'poetry_umayyad':_fake_corpus(40, SEED + 4),
}
ARABIC_CTRL_POOL = ['poetry_abbasi', 'arabic_bible', 'poetry_umayyad']

# Mimic the notebook helper
def _X_for(name: str, lo: int = BAND_A_LO, hi: int = BAND_A_HI) -> np.ndarray:
    recs = [r for r in FEATS.get(name, []) if lo <= r['n_verses'] <= hi]
    if len(recs) < 3:
        return np.zeros((0, 5))
    return np.array([[r[c] for c in FEAT_COLS] for r in recs], dtype=float)

N_PERM = 100           # keep smoke-test fast
FAST_MODE = True
ALL_RESULTS: dict = {}

# Minimal stand-in for bless() — record but no drift checks
def bless(fid, actual, *, tol_override=None):
    ALL_RESULTS[fid] = {'actual': actual, 'drift_ok': True}
    return actual


# ------------------------------------------------------- HSIC block (Cell 40)
def _extract_rbf_kernel():
    """Extract the unconditional `_rbf_kernel` def from Cell 8 (audit v4).

    The definition was hoisted out of `if USE_HSIC:` in Cell 40 so it
    survives checkpoint resume. Cell 55 now calls it directly without
    aliasing. We pull it out of Cell 8 and exec it into a namespace so the
    downstream Cell-55 test can use it.
    """
    src8 = _pick_cell('# === Cell 8')
    # Take from the `def _rbf_kernel(M):` header through the closing
    # `return np.exp(...)` line. Everything below that is the log() call +
    # unrelated statements, which we don't need.
    start = src8.find('def _rbf_kernel(M):')
    if start == -1:
        raise AssertionError('_rbf_kernel not found in Cell 8 (audit v4)')
    end_marker = "return np.exp(-D2 / (2.0 * sigma2))"
    end = src8.find(end_marker, start)
    if end == -1:
        raise AssertionError('_rbf_kernel body truncated in Cell 8')
    rbf_src = src8[start:end + len(end_marker)]
    return rbf_src


def test_hsic_cell40() -> None:
    """Extract the HSIC block from Cell 40 and exec it in-place."""
    src40 = _pick_cell('# === Cell 40')
    # Grab from the HSIC banner through the %T>0 marker (audit v4: header
    # comment now reads '# %T>0 (T10 / D10) — SAME statistic; ...')
    banner = '# === Nobel/PNAS audit 2026-04-18 · HSIC — binning-free I(EL;CN) alternative ==='
    marker = '# %T>0 (T10 / D10)'
    if banner not in src40 or marker not in src40:
        raise AssertionError('HSIC block markers not found in Cell 40')
    hsic_block = src40.split(banner, 1)[1].split(marker, 1)[0]
    hsic_block = banner + hsic_block
    ns = {
        'np': np, 'FEATS': FEATS, 'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
        'N_PERM': N_PERM, 'SEED': SEED, 'bless': bless, 'USE_HSIC': True,
    }
    # AUDIT 2026-04-18 (v4): `_rbf_kernel` now lives in Cell 8 (hoisted out of
    # the `if USE_HSIC:` block). Inject it so Cell 40's HSIC block runs.
    exec(compile(_extract_rbf_kernel(), '<cell8_rbf>', 'exec'), ns)
    exec(compile(hsic_block, '<cell40_hsic>', 'exec'), ns)
    v  = ns.get('hsic_obs'); p = ns.get('hsic_p')
    assert v is not None and np.isfinite(v), f'hsic_obs missing/invalid: {v!r}'
    assert p is not None and 0.0 < p <= 1.0, f'hsic_p out of range: {p!r}'
    assert 'HSIC_EL_CN_quran'  in ALL_RESULTS, 'HSIC_EL_CN_quran not blessed'
    assert 'HSIC_EL_CN_perm_p' in ALL_RESULTS, 'HSIC_EL_CN_perm_p not blessed'
    print(f'  [pass] Cell-40 HSIC(EL,CN) = {v:.4e}   perm p = {p:.4g}')


# ------------------------------------------------------ HSIC block (Cell 55)
def test_hsic_cell55() -> None:
    """Simulate the Phase-10-after-resume path: Cell 55 runs without Cell 40.

    AUDIT 2026-04-18 (v4): this test enforces the regression guard — Cell
    55's 5-channel HSIC block MUST work when only Cell 8 has run (no
    Cell-40 HSIC block). Previously Cell 55 aliased `_rbf_kernel_5ch =
    _rbf_kernel` which NameError'd on resume; the fix removes the alias
    and relies on Cell 8's unconditional definition.
    """
    src55 = _pick_cell('# === Cell 55')
    banner = '# === Nobel/PNAS audit 2026-04-18 · 5-channel HSIC (binning-free G2) ==='
    if banner not in src55:
        raise AssertionError('5-channel HSIC banner not found in Cell 55')
    hsic_block = banner + src55.split(banner, 1)[1]
    ns = {
        'np': np, 'FEATS': FEATS, 'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
        'N_PERM': N_PERM, 'SEED': SEED, 'bless': bless, 'USE_HSIC': True,
        'FEAT_COLS': FEAT_COLS, '_X_for': _X_for,
    }
    # Inject _rbf_kernel from Cell 8 (this is exactly what a checkpoint
    # resume path would have in globals).
    exec(compile(_extract_rbf_kernel(), '<cell8_rbf>', 'exec'), ns)
    exec(compile(hsic_block, '<cell55_hsic>', 'exec'), ns)
    assert 'HSIC_G2_max_quran' in ALL_RESULTS, 'HSIC_G2_max_quran not blessed'
    assert 'HSIC_G2_perm_p'    in ALL_RESULTS, 'HSIC_G2_perm_p not blessed'
    hm = ALL_RESULTS['HSIC_G2_max_quran']['actual']
    hp = ALL_RESULTS['HSIC_G2_perm_p']['actual']
    assert np.isfinite(hm), f'G2 HSIC invalid: {hm!r}'
    print(f'  [pass] Cell-55 max 5-ch HSIC = {hm:.4e}  perm p = {hp:.4g}')


# ---------------------------------------------------- TDA Cell 131 (skip path)
def test_tda_cell131_skip() -> None:
    src = _pick_cell('# === Cell 131')
    ns = {
        'np': np, 'FEATS': FEATS, 'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
        'bless': bless, 'USE_TDA': False, 'ARABIC_CTRL_POOL': ARABIC_CTRL_POOL,
        '_X_for': _X_for,
    }
    exec(compile(src, '<cell131_skip>', 'exec'), ns)
    assert 'TDA_H1_max_persistence' in ALL_RESULTS
    assert 'TDA_n_loops_long_lived' in ALL_RESULTS
    assert ALL_RESULTS['TDA_H1_max_persistence']['actual'] == 0.0
    print('  [pass] Cell-131 USE_TDA=False skip path OK')


def test_tda_cell131_run() -> None:
    try:
        import ripser   # noqa: F401
    except ImportError:
        print('  [skip] Cell-131 run path — ripser not installed (pip install ripser)')
        return
    src = _pick_cell('# === Cell 131')
    ns = {
        'np': np, 'FEATS': FEATS, 'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
        'bless': bless, 'USE_TDA': True, 'ARABIC_CTRL_POOL': ARABIC_CTRL_POOL,
        '_X_for': _X_for,
    }
    exec(compile(src, '<cell131_run>', 'exec'), ns)
    mh = ALL_RESULTS['TDA_H1_max_persistence']['actual']
    nl = ALL_RESULTS['TDA_n_loops_long_lived']['actual']
    assert np.isfinite(mh), f'max_H1 invalid: {mh!r}'
    assert nl >= 0
    tda_res = ns.get('TDA_RESULTS', {})
    assert 'quran' in tda_res, 'quran entry missing from TDA_RESULTS'
    print(f'  [pass] Cell-131 USE_TDA=True: Quran max H1 = {mh:.3f}  # loops = {nl}')


# ------------------------------------------------------------------ run all
def main() -> int:
    print('[smoke] HSIC + TDA smoke test (audit v3)')
    tests = [
        ('Cell 40 HSIC(EL,CN)',           test_hsic_cell40),
        ('Cell 55 5-channel HSIC',        test_hsic_cell55),
        ('Cell 131 TDA skip path',        test_tda_cell131_skip),
        ('Cell 131 TDA run path',         test_tda_cell131_run),
    ]
    failures = 0
    for label, fn in tests:
        print(f'[smoke] {label}')
        try:
            fn()
        except Exception as e:
            failures += 1
            print(f'  [FAIL] {label}: {e.__class__.__name__}: {e}')
            traceback.print_exc(limit=2)
    print(f'\n[smoke] {len(tests)-failures}/{len(tests)} tests passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
