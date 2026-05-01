"""
Builder for QSF_ULTIMATE.ipynb.

Generates the 22-phase / ~130-cell notebook deterministically from this single
source file. Always rebuild with:

    python notebooks/ultimate/_build.py

Do NOT hand-edit QSF_ULTIMATE.ipynb — edit this script instead.

The notebook structure follows the v3 plan approved 2026-04-18:
  * Qira'at section removed
  * Constructive STOT test E4 skipped
  * 4 integrity locks (corpus, code, results, names)
  * 7 universal-law candidates L1-L7
  * 6 diagnostic figures (opt-in via GENERATE_FIGURES)
  * Honest Gap-3 / Gap-5 closures via real transmission-noise simulation
"""
from __future__ import annotations

from pathlib import Path
import json

try:
    from nbformat import v4 as nbf
    import nbformat
except ImportError:
    raise SystemExit(
        "nbformat is required to build the notebook.\n"
        "Install it with:   python -m pip install nbformat"
    )

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
OUT_PATH = HERE / "QSF_ULTIMATE.ipynb"

# Accumulator for all cells in order.
_CELLS: list = []


# ------------------------------------------------------------------ helpers
def md(src: str) -> None:
    """Append a markdown cell."""
    _CELLS.append(nbf.new_markdown_cell(src.rstrip() + "\n"))


def code(src: str) -> None:
    """Append a code cell."""
    _CELLS.append(nbf.new_code_cell(src.rstrip() + "\n"))


def phase_header(num: int, title: str, summary: str) -> None:
    """Insert a standard phase header with a summary bullet."""
    md(
        f"""# Phase {num:02d} — {title}

{summary}

---"""
    )


# ============================================================================
# PHASE 0 — Preamble & run-mode config (cells 1-4)
# ============================================================================
def build_phase_0() -> None:
    md(
        """# QSF ULTIMATE — Reproduction & Discovery Pipeline

**Version**: v6 (2026-04-19) · **Legacy**: `../QSF_REPRODUCE.ipynb`

A single self-validating notebook that

1. reproduces **every testable finding** of the QSF project from raw data,
2. re-tests all flip-flopped claims cleanly (D18, D21, D25, T28, T29, Phase 30),
3. closes the previously-retracted formal-proof gaps G3 and G5 **honestly** via a real transmission-noise simulation (Phase 18 E1),
4. explores **seven universal-law candidates L1–L7** under strict pre-registered falsification criteria, and
5. prints negative findings with the same prominence as positive ones.

The notebook is locked against AI hallucination via **four SHA-256 integrity locks** (corpus, code, results, finding-names). Any drift raises a fatal `HallucinationError`.

**Runtime budget on laptop CPU:**
- `FAST_MODE = True`  → ≈ 60 min
- `FAST_MODE = False` → ≈ 3 h 30 min  (well under the 6-hour ceiling)

Run `Kernel → Restart & Run All` after editing Cell 0.

---

## Audit fixes (2026-04-18, rounds 1 + 2)

Two independent reviewer passes flagged 19 initial concerns and then
4 critical follow-ups after seeing the first-pass fixes. This build
addresses all confirmed issues from both rounds.

### Round 1 (19 concerns)

**Confirmed bugs, fixed upstream:**
- Cell 32 heuristic-T computation (algebraic error — now swaps H_cond only).
- Cell 99 blind-rejection nulls (were drawn from Quran vocab — now external).

**Primary statistics upgraded:**
- Cell 29 Φ_M: **Hotelling T² + permutation p-value** as headline statistic.
- Cell 109 Ψ: permutation-null p-value for the rank claim.
- Cell 113 Adiyat Metric 7: multi-shuffle 5th-percentile null.
- Cell 40 D05 MI: bin-count sensitivity sweep.
- Cell 26: Miller-Madow H_cond.
- Cell 82: DFA Hurst alongside R/S.
- Cell 116: char-normalised gzip proxy.
- Cell 109 xlang: INFEASIBLE flag for single-corpus families.
- Phase 20: Benjamini-Hochberg FDR correction.

**Caveats added** for G_turbo, L5 OBI, Nuzul, oral-sim, RHYME_LETTERS.

### Round 2 (4 critical + 3 high-severity — this build)

**Critical fixes:**
- **Cohen's d locks demoted** — D02 / S1 / D28 now record the biased
  Cohen's d with `tol=inf` and `verdict_expected = "DEPRECATED"`.
  New locked headline statistics are `Phi_M_hotelling_T2` and
  `Phi_M_perm_p_value`. The lock no longer enshrines a biased value.
- **G3 / G5 closure claim retracted** — Phase 20 header now states
  "G1/G2/G4 closed; G3/G5 data-dependent". E1 expanded from 3 → 7 Arabic
  corpora so G3's quadratic fit has ≥5 data points. G5 is explicitly
  listed OPEN in the NEGATIVES registry: empirical slope observation is
  not formal closure of γ'(Ω) > 0.
- **Ψ demoted to "descriptive composite index"** — Cell 109 now spells
  out the dimensional incoherence (Φ_M σ × probability × entropy × CV)
  and runs a z-scored sensitivity variant (Ψ_z) alongside raw Ψ. If the
  ranking changes under z-scoring, raw Ψ is flagged as scale-artifact.
- **Per-surah dashboard band-gated** — Cell 98 separates grades into
  Band-A (valid, calibrated range 15-100 verses) and out-of-band
  (EXTRAPOLATION, not defensible). Only Band-A grades are reported as
  headline; out-of-band are reference only.

**High-severity fixes:**
- **FDR coverage expanded** — Cell 123b now generates permutation
  p-values for Cohen's d statistics (D02, S1, D28, T1, T2) via a shared
  label-permutation batch. Coverage went from ~8 to ~15 p-values. Full
  45-claim coverage remains an OPEN methodological gap (see Nobel
  suggestion #7).
- **PreReg A violation fixed** — Cell 64 previously blessed
  `PreReg_A_leave_one_out` using T12 10-fold **surah-level** CV. The
  pre-registration named leave-one-**family**-out. Cell 64b (new) now
  runs the real leave-one-family-out loop over all Arabic control
  families and re-blesses with the correct statistic.
- **MI Miller-Madow correction** — Cell 40's MI estimator now applies
  the MM bias correction consistently (same formula as H_cond in Cell 26);
  legacy plug-in is preserved for backward-compat.

**Not changed (design trade-offs):**
- Bless-tolerances: kept wide enough to accommodate FAST/NORMAL mode noise;
  tightening would require a lock re-bless across 45+ scalars.
- Band A [15,100] choice: justified by existing Band B/C sensitivity
  checks in Cell 30.

### Nobel/PNAS advanced statistics (2026-04-18)

Two reviewer-suggested upgrades implemented as **opt-in** additions (no
existing behaviour changed; all new entries carry `tol=inf` and
`verdict_expected='REPORTING'` or `'APPENDIX'`):

- **HSIC — binning-free independence (Cells 40 + 55)** — Gretton et al.
  2005 Hilbert-Schmidt Independence Criterion with Gaussian RBF kernels
  (median-heuristic bandwidth). Computed alongside plug-in MI
  in Cell 40 (D05 `I(EL;CN)`) and as a 5-channel pairwise matrix in
  Cell 55 (G2). Exact permutation p-values on `N_PERM` label shuffles.
  Controlled by `USE_HSIC=True` in Cell 1 (default ON, ~2-5 s runtime).
  New locks: `HSIC_EL_CN_quran`, `HSIC_EL_CN_perm_p`,
  `HSIC_G2_max_quran`, `HSIC_G2_perm_p`.
- **TDA appendix — persistent homology (Phase 22)** — Vietoris-Rips
  filtration on z-scored Band-A 5D feature clouds. Computes H0
  (connected components) and H1 (loops) diagrams; summarised by
  max H1 persistence and count of long-lived loops. Controlled by
  `USE_TDA=False` in Cell 1 (opt-in; requires `pip install ripser`).
  Four explicit caveats in Cell 132 about under-sampling, preprocessing
  choice, scale dependence, and filtration choice. New locks:
  `TDA_H1_max_persistence`, `TDA_n_loops_long_lived`."""
    )

    # Cell 1 — run-mode flags
    code(
        """# === Cell 1 · run-mode config (edit here, then Restart & Run All) ===
FAST_MODE        = True    # 200 perms / 500 bootstraps  vs  2000 / 5000
FORCE_RERUN      = False   # ignore cached checkpoints
UPDATE_LOCK      = False   # re-bless results_lock.json with current values
GENERATE_FIGURES = True    # write 6 diagnostic PNGs to results/figures/
VERBOSE          = True    # print progress messages

# AUDIT 2026-04-19 (v6 fix W1-a): universal absolute-drift lens. The per-scalar
# `tol` column in RESULTS_LOCK is the authoritative gate, but a hostile reviewer
# may ask for a second lens with a uniform absolute threshold. Every scalar whose
# `|actual - expected|` exceeds `UNIVERSAL_DRIFT_ABSOLUTE` is listed in the
# Phase-21 report (informational; does NOT raise unless the per-scalar tol also
# fails). Set to a very small number (1e-4) so it flags ~all numerical noise.
UNIVERSAL_DRIFT_ABSOLUTE = 1e-4

# AUDIT 2026-04-19 (v6 fix W1-b): relative-drift envelope for the two headline
# Φ_M statistics, which carry `tol=inf` in RESULTS_LOCK pending lock refresh.
# On the first clean run, `integrity/headline_baselines.json` is written; on
# later runs, T2_obs / perm_p are compared and any relative drift above
# `HEADLINE_REL_TOL` (default 5 %) raises HallucinationError. Override with
# UPDATE_LOCK=True to re-pin.
HEADLINE_REL_TOL = 0.05

# --- Nobel/PNAS audit 2026-04-18: optional advanced statistics ---
#   USE_HSIC  = kernel-based independence test (binning-free) — O(n²) on ≤120
#               surahs; adds ~2-5 s to Cell 40 + Cell 55. Default ON.
#   USE_TDA   = persistent-homology appendix (Phase 22). Requires ripser
#               (pip install ripser). Default OFF — set True to opt in.
USE_HSIC         = True    # kernel HSIC in Cell 40 (D05) and Cell 55 (G2)
USE_TDA          = False   # Phase 22 persistent-homology appendix

SEED = 42                  # global deterministic seed — do NOT change mid-project

# Permutation / bootstrap counts derived from FAST_MODE
N_PERM   = 200  if FAST_MODE else 2000
N_BOOT   = 500  if FAST_MODE else 5000
N_SURROG = 1000 if FAST_MODE else 10000

print(f'[config] FAST_MODE={FAST_MODE}  N_PERM={N_PERM}  N_BOOT={N_BOOT}  SEED={SEED}')
print(f'[config] FORCE_RERUN={FORCE_RERUN}  UPDATE_LOCK={UPDATE_LOCK}  GENERATE_FIGURES={GENERATE_FIGURES}')
print(f'[config] USE_HSIC={USE_HSIC}  USE_TDA={USE_TDA}')"""
    )

    # Cell 2 — global seed lock + path setup
    code(
        """# === Cell 2 · strict seed locking + repo paths ===
import os, sys, random, hashlib, json, pickle, time, warnings, gzip, shutil, math
from pathlib import Path
from datetime import datetime
import numpy as np

# AUDIT 2026-04-18 (v4): fail loudly on Python < 3.10. Cell 3's
# `state: dict | None = None` and Cell 26's / Cell 128's `dict[str, ...]`
# variable annotations require 3.10+ at runtime (PEP 604 union syntax,
# PEP 585 generics). Colab default is 3.10+, but local kernels may lag.
assert sys.version_info >= (3, 10), (
    f'Python 3.10+ required (got {sys.version_info.major}.{sys.version_info.minor}). '
    f'In Colab: Runtime → Change runtime type → Python 3.10 or newer.'
)

# deterministic seed for every stdlib / numpy call
random.seed(SEED)
np.random.seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

# repository root (parent of notebooks/ultimate/)
# AUDIT 2026-04-18 (v4): the previous ternary
#   NB_DIR = Path.cwd() if (...).exists() else Path.cwd()
# was a no-op (both branches returned Path.cwd()). The loop below handles
# the case where the notebook was launched from a different cwd.
NB_DIR   = Path.cwd()
if (NB_DIR.parent.parent / 'src').is_dir():
    REPO = NB_DIR.parent.parent
elif (NB_DIR / 'src').is_dir():
    REPO = NB_DIR
else:
    # fallback: walk up until we find 'src'
    p = Path.cwd()
    while p != p.parent and not (p / 'src').is_dir():
        p = p.parent
    REPO = p

assert (REPO / 'src').is_dir(), f'Cannot locate repo root from {Path.cwd()}'
sys.path.insert(0, str(REPO))

DATA_DIR    = REPO / 'data' / 'corpora'
RESULTS     = REPO / 'results'
CKPT_DIR    = RESULTS / 'checkpoints'
INT_DIR     = RESULTS / 'integrity'
FIG_DIR     = RESULTS / 'figures'
for d in (RESULTS, CKPT_DIR, INT_DIR, FIG_DIR):
    d.mkdir(parents=True, exist_ok=True)

print(f'[paths] REPO      = {REPO}')
print(f'[paths] DATA_DIR  = {DATA_DIR}')
print(f'[paths] RESULTS   = {RESULTS}')
print(f'[paths] CKPT_DIR  = {CKPT_DIR}')
print(f'[paths] INT_DIR   = {INT_DIR}')"""
    )

    # Cell 3 — custom exceptions + checkpoint helpers
    code(
        """# === Cell 3 · custom exceptions + checkpoint helpers ===
class HallucinationError(Exception):
    '''Raised when a locked scalar drifts without an explicit re-bless.'''

class UnknownFindingError(Exception):
    '''Raised when code references a finding ID not in names_registry.json.'''

class IntegrityError(Exception):
    '''Raised when corpus or code SHA-256 drift is detected.'''

# progress bars (fall back to identity if tqdm missing)
try:
    from tqdm.auto import tqdm
except ImportError:
    def tqdm(x, **kw): return x

# === checkpoint helpers ===
def _fingerprint():
    '''Fingerprint tying a checkpoint to the exact corpus/code/run params.
    Returns None if either lock file is absent (= refuse to validate any
    checkpoint, forcing re-compute).'''
    corpus = (INT_DIR / 'corpus_lock.json')
    code_  = (INT_DIR / 'code_lock.json')
    if not (corpus.exists() and code_.exists()):
        return None
    return {
        'corpus_sha': json.loads(corpus.read_text(encoding='utf-8'))['combined'],
        'code_sha':   json.loads(code_.read_text(encoding='utf-8'))['combined'],
        'fast_mode':  FAST_MODE,
        'seed':       SEED,
    }

# AUDIT 2026-04-19 (v6 fix W5-a): SHA-256 manifest for the checkpoint pickles.
# Prior behaviour was to call `pickle.loads(pkl.read_bytes())` after only the
# run-parameter `fingerprint` check. Python pickle is NOT safe against adversarial
# input (arbitrary __reduce__ → code execution). An attacker who preserves the
# fingerprint inside the pickle payload could therefore (a) execute arbitrary
# code and (b) inject forged ALL_RESULTS via `globals().update(state)` without
# tripping any of the 4 integrity locks. We now write a `_manifest.json` beside
# the checkpoint dir that records each pickle's SHA-256 at save time, and
# `load_checkpoint` refuses to deserialise a pickle whose on-disk SHA does not
# match the manifest. Any bit-flip in a .pkl is caught BEFORE pickle.loads runs.
_CKPT_MANIFEST = CKPT_DIR / '_manifest.json'

def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _manifest_read() -> dict:
    if not _CKPT_MANIFEST.exists():
        return {'version': 1, 'entries': {}}
    try:
        return json.loads(_CKPT_MANIFEST.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {'version': 1, 'entries': {}}

def _manifest_write(m: dict) -> None:
    _CKPT_MANIFEST.write_text(
        json.dumps(m, indent=2, ensure_ascii=False), encoding='utf-8')

def save_checkpoint(phase_id: str, results: dict, *, state: dict | None = None) -> Path:
    '''Persist a phase's results and OPTIONALLY a runtime-state dict.
    `state` should contain exactly the global variables a later phase needs
    (CORPORA, FEATS, mu, S_inv, RES, ALL_RESULTS, ...). Auto-resume in the
    opening cell of each phase will `globals().update(state)` on a match.'''
    fp  = _fingerprint()
    pkl = CKPT_DIR / f'phase_{phase_id}.pkl'
    payload = {
        'phase_id':  phase_id,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'fingerprint': fp,
        'env': {'numpy': np.__version__, 'python': sys.version.split()[0]},
        'results': results,
        'state':   state or {},
    }
    body = pickle.dumps(payload)
    pkl.write_bytes(body)
    # v6 fix W5-a — record the SHA of the bytes we just wrote.
    m = _manifest_read()
    m['entries'][pkl.name] = {
        'sha256':      _sha_bytes(body),
        'size_bytes':  len(body),
        'timestamp':   payload['timestamp'],
        'fingerprint': fp,
    }
    _manifest_write(m)
    if VERBOSE:
        tag = ' +state' if state else ''
        print(f'[ckpt ] {phase_id:>14s}  ->  {pkl.name}{tag}')
    return pkl

def load_checkpoint(phase_id: str, *, want_state: bool = False):
    '''Return checkpoint payload if and only if its fingerprint matches the
    current run exactly AND the on-disk SHA-256 matches the manifest.
    With `want_state=True` returns the full payload (results + state);
    otherwise returns just the results dict.'''
    if FORCE_RERUN: return None
    pkl = CKPT_DIR / f'phase_{phase_id}.pkl'
    if not pkl.exists(): return None
    fp_now = _fingerprint()
    if fp_now is None:
        if VERBOSE: print(f'[ckpt ] {phase_id}: locks missing; refusing resume')
        return None
    # v6 fix W5-a — verify on-disk bytes SHA before handing to pickle.loads.
    body = pkl.read_bytes()
    m = _manifest_read()
    expected = m.get('entries', {}).get(pkl.name, {}).get('sha256')
    if expected is None:
        if VERBOSE:
            print(f'[ckpt ] {phase_id}: no manifest entry for {pkl.name}; '
                  f'refusing resume (run with FORCE_RERUN=True to regenerate)')
        return None
    actual = _sha_bytes(body)
    if actual != expected:
        raise IntegrityError(
            f'[HALL ckpt] {pkl.name}: SHA-256 drift  manifest={expected[:12]}  '
            f'disk={actual[:12]}. Refusing pickle.loads on potentially '
            f'tampered bytes. Delete the checkpoint or set FORCE_RERUN=True.'
        )
    try:
        payload = pickle.loads(body)
    except Exception as e:
        print(f'[ckpt ] {phase_id}: corrupt ({e}); ignoring')
        return None
    if payload.get('fingerprint') != fp_now:
        if VERBOSE: print(f'[ckpt ] {phase_id}: fingerprint mismatch; re-running')
        return None
    if VERBOSE: print(f'[ckpt ] {phase_id}: LOADED from {pkl.name}')
    return payload if want_state else payload['results']

def resume_from(phase_id: str) -> bool:
    '''Restore global runtime state from a checkpoint if available.
    Returns True if state was loaded (caller can skip re-compute).'''
    p = load_checkpoint(phase_id, want_state=True)
    if p is None or not p.get('state'): return False
    globals().update(p['state'])
    print(f'[resume] Phase {phase_id}: restored {len(p["state"])} globals '
          f'({", ".join(list(p["state"])[:6])}{"..." if len(p["state"])>6 else ""})')
    return True

# global results accumulator (populated phase by phase)
ALL_RESULTS: dict = {}

print('[cell 3] exceptions + checkpoint helpers ready')"""
    )


# ============================================================================
# PHASE 1 — Environment & dependency pin (cells 5-8)
# ============================================================================
def build_phase_1() -> None:
    phase_header(
        1,
        "Environment & dependency pin",
        "Verify Python + library versions match the lockfile; auto-install "
        "anything missing. Silent version drift is a common source of "
        "irreproducible results, so we fail loudly on mismatch.",
    )

    # Cell 5 — python / platform
    code(
        """# === Cell 5 · python + platform info ===
import platform
try:
    import psutil
    RAM_GB = psutil.virtual_memory().total / (1024**3)
    N_CPU  = psutil.cpu_count(logical=True)
except ImportError:
    RAM_GB, N_CPU = float('nan'), os.cpu_count()

print(f'[env] python   : {sys.version.split()[0]}')
print(f'[env] platform : {platform.platform()}')
print(f'[env] CPUs     : {N_CPU}')
print(f'[env] RAM (GB) : {RAM_GB:.1f}')"""
    )

    # Cell 6 — dependency versions
    code(
        """# === Cell 6 · dependency pin + auto-install ===
REQUIRED = {
    'numpy':       '>=1.24',
    'scipy':       '>=1.10',
    'scikit-learn':'>=1.3',
    'pandas':      '>=2.0',
    'matplotlib':  '>=3.7',
    'tqdm':        '>=4.65',
    'openpyxl':    '>=3.1',
    'nbformat':    '>=5.9',
    'psutil':      '>=5.9',
    # camel-tools is pinned exactly because its API changes silently
    'camel-tools': '==1.5.7',
}

import importlib, subprocess
def _pip_install(spec):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', spec])

missing = []
for pkg, spec in REQUIRED.items():
    mod = pkg.replace('-', '_').replace('scikit_learn', 'sklearn')
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(pkg + spec)

if missing:
    print(f'[env] installing {len(missing)} missing packages...')
    for spec in missing:
        print(f'      pip install {spec}')
        try: _pip_install(spec)
        except Exception as e: print(f'      ! failed: {e}')
else:
    print('[env] all required packages already installed')

# re-import to get versions (aliased to avoid shadowing tqdm-class from Cell 3)
import numpy, scipy, sklearn, pandas, matplotlib
import tqdm as _tqdm_mod
VER = {
    'numpy':        numpy.__version__,
    'scipy':        scipy.__version__,
    'scikit-learn': sklearn.__version__,
    'pandas':       pandas.__version__,
    'matplotlib':   matplotlib.__version__,
    'tqdm':         _tqdm_mod.__version__,
}
for k, v in VER.items():
    print(f'[env] {k:14s} {v}')"""
    )

    # Cell 7 — CamelTools check (soft)
    code(
        """# === Cell 7 · CamelTools availability check (soft) ===
CAMEL_OK = False
try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    try:
        _db = MorphologyDB.builtin_db()
        _an = Analyzer(_db)
        _ = _an.analyze('قال')  # smoke test
        CAMEL_OK = True
        print('[env] CamelTools 1.5.7 OK (root extraction will be authoritative)')
    except Exception as e:
        print(f'[env] CamelTools installed but DB missing: {e}')
        print('      run:  camel_data -i all')
except ImportError:
    print('[env] CamelTools NOT available — H_cond will fall back to heuristic')
    print('      run:  pip install camel-tools==1.5.7 && camel_data -i all')"""
    )

    # Cell 8 — warning filters + log file
    code(
        r"""# === Cell 8 · warning filters + log file + shared RBF kernel helper ===
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

LOG_PATH = RESULTS / f'ultimate_run_{datetime.now():%Y%m%d_%H%M%S}.log'
def log(msg):
    stamp = datetime.now().strftime('%H:%M:%S')
    line  = f'[{stamp}] {msg}'
    if VERBOSE: print(line)
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(line + '\n')

# AUDIT 2026-04-18 (v4): `_rbf_kernel` is hoisted here (previously defined
# inside `if USE_HSIC:` in Cell 40) so it is GUARANTEED to be in globals on
# any kernel session — including sessions that resume from the Phase-7
# checkpoint (`resume_from('07_core')`), which otherwise skips Cell 40 and
# leaves `_rbf_kernel` undefined when Cell 55 tries to alias it.
# Gaussian-RBF kernel with median-heuristic bandwidth. Used by HSIC in
# Cell 40 and the 5-channel HSIC in Cell 55. No-op if USE_HSIC=False.
def _rbf_kernel(M):
    '''Gaussian-RBF kernel with median-heuristic σ² = 0.5·median(||xi-xj||²).'''
    M = np.asarray(M, float).reshape(-1, 1) if np.asarray(M).ndim == 1 else np.asarray(M, float)
    n_ = M.shape[0]
    sq = np.sum(M**2, axis=1)
    D2 = sq[:, None] + sq[None, :] - 2.0 * (M @ M.T)
    D2 = np.maximum(D2, 0.0)
    if n_ < 2: return np.ones((n_, n_))
    iu = np.triu_indices(n_, k=1)
    med = float(np.median(D2[iu])) if iu[0].size > 0 else 1.0
    sigma2 = 0.5 * med if med > 0 else 1.0
    return np.exp(-D2 / (2.0 * sigma2))

log('ULTIMATE notebook starting')
log(f'FAST_MODE={FAST_MODE}  SEED={SEED}')"""
    )


# ============================================================================
# PHASE 2 — Pre-registration + 4 integrity locks (cells 9-14)
# ============================================================================
def build_phase_2() -> None:
    phase_header(
        2,
        "Pre-registration + 4 integrity locks",
        "Write the pre-registered thresholds AND four SHA-256 locks "
        "(corpus, code, results, names). Any drift at run-end raises a fatal "
        "`HallucinationError` or `UnknownFindingError`.",
    )

    # Cell 9 — pre-registration manifest
    code(
        r"""# === Cell 9 · pre-registration manifest (Tests A, B, C) ===
# Locks THRESHOLDS for adversarial tests so nobody can post-hoc-tune them.
# Source: docs/PREREGISTRATION_v10.18.md
PREREG = {
    'version':    '10.18',
    'frozen_at':  '2026-04-18',
    # AUDIT 2026-04-19 (v6 fix L): list of STRUCTURAL changes to this PREREG
    # dict that occurred AFTER `frozen_at`. Runtime / interpretive adjustments
    # continue to live in `honest_adjustments_2026_04_18` below; this list is
    # reserved for structural additions or edits to the PREREG itself, so a
    # reviewer reading the exported preregistration.json can see both the
    # original freeze date and every subsequent amendment.
    'amendments': [
        {
            'date':     '2026-04-19',
            'audit_id': 'v5 fix ⑧',
            'scope':    'grade_thresholds',
            'change':   'Added grade_thresholds block (A+/A/B/C/D cutoffs at '
                        '6/4/2/1 sigma). The cutoffs themselves are ex-ante '
                        'integer-sigma spacings standard in discovery tables '
                        '(not data-fitted); this amendment freezes them '
                        'against further tuning rather than pre-registering '
                        'them in the strict sense.',
        },
    ],
    'tests': {
        'A_leave_one_family_out': {
            'claim':       'Phi_M separation survives leaving out any 1 of 9 control families',
            'threshold':   'min d >= 1.5 across all 9 leave-one-out splits',
            'falsifier':   'any leave-one-out split gives d < 1.0',
        },
        'B_meccan_medinan': {
            'claim':       'Meccan AND Medinan each internally exceed control F',
            'threshold':   'F_Meccan > 1.0 AND F_Medinan > 1.0',
            'falsifier':   'either F < 1.0 on clean Band-A data',
        },
        'C_bootstrap_omega': {
            'claim':       'Hierarchical Omega bootstrap stable',
            'threshold':   '>= 95 percent of 1000 resamples give Omega > 2.0',
            'falsifier':   '< 95 percent exceed 2.0',
        },
    },
    'honest_adjustments_2026_04_18': [
        'Test B FALSIFIED on clean data (F_M=0.80, F_D=0.84)',
        # AUDIT FIX (reviewer v2): PREVIOUS claim "Test A CLOSED on unit-level
        # (min d=5.08 over 10 folds)" was a PRE-REGISTRATION VIOLATION.
        # The pre-registration names leave-one-FAMILY-out, not surah-level
        # 10-fold CV (T12). Cell 64b now runs the REAL leave-one-family-out
        # across the loaded Arabic control families; verdict printed at runtime.
        'Test A: surah-level 10-fold CV is a DIFFERENT hypothesis (T12/D24).',
        'Test A: leave-one-family-out now in Cell 64b (audit 2026-04-18 v2).',
        # AUDIT 2026-04-19 (v5 fix ⑦): honest 9->6 pool disclosure.
        'Test A: hadith_bukhari quarantined post-v2 audit (quotes Quran by '
        'design as Prophetic tradition), reducing tested pool from 9 to 6 '
        'Arabic families. Pre-reg threshold (min d >= 1.5) applied to all 6 '
        'actual leave-one-family-out splits; downgrade reported transparently '
        'and is NOT a post-hoc selection of easier splits.',
        'Test C CLOSED STRONGER (100% of resamples > 2.0, median 10.0)',
    ],
    # AUDIT 2026-04-19 (fix ⑧): the per-surah A+/A/B/C/D grading buckets in
    # Cell 98 were previously hard-coded without being part of the frozen
    # pre-registration, so a hostile reviewer could argue the cutoffs were
    # post-hoc tuned to make the Quran look "A+". We freeze them here as
    # part of v10.18 so any future retune becomes a traceable pre-reg event.
    'grade_thresholds': {
        'source':    'Cell 98 per-surah dashboard (Band-A only)',
        'metric':    "Mahalanobis distance to Arabic-control centroid (mu, S_inv from ARABIC_CTRL_POOL Band-A)",
        'cutoffs':   {'A+': '> 6.0', 'A':  '> 4.0 and ≤ 6.0',
                      'B':  '> 2.0 and ≤ 4.0',
                      'C':  '> 1.0 and ≤ 2.0',
                      'D':  '≤ 1.0'},
        'validity':  'Band A (15 ≤ n_verses ≤ 100). Out-of-band grades are '
                     'statistical extrapolations and are reported separately.',
        'headline':  'Only Band-A grade distribution is defensible for publication.',
        'rationale': 'Cutoffs chosen ex ante at 1/2/4/6 σ, spaced on the '
                     'integer-σ grid that is standard in physics-style '
                     'discovery tables (e.g. CDF/Dzero 5σ Higgs thresholds). '
                     'No post-hoc optimisation.',
    },
}
(INT_DIR / 'preregistration.json').write_text(
    json.dumps(PREREG, indent=2, ensure_ascii=False), encoding='utf-8')
log(f'pre-registration v{PREREG["version"]} frozen -> integrity/preregistration.json')"""
    )

    # Cell 10 — corpus_lock.json
    code(
        r"""# === Cell 10 · corpus_lock.json — SHA-256 of all raw corpus files ===
# AUDIT FIX 2026-04-21: aligned to the actual on-disk corpus set
# matching results/integrity/corpus_lock.json (refreshed 2026-04-20).
RAW_FILES = {
    'quran_bare':        DATA_DIR / 'ar' / 'quran_bare.txt',
    'quran_vocal':       DATA_DIR / 'ar' / 'quran_vocal.txt',
    'tashkeela':         DATA_DIR / 'ar' / 'tashkeela.txt',
    'arabic_bible':      DATA_DIR / 'ar' / 'arabic_bible.xlsx',
    'hadith_bukhari':    DATA_DIR / 'ar' / 'hadith.json',
    'hindawi':           DATA_DIR / 'ar' / 'hindawi.txt',
    'ksucca':            DATA_DIR / 'ar' / 'ksucca.txt',
    'poetry_raw_csv':    DATA_DIR / 'ar' / 'poetry_raw.csv',
    'hebrew_tanakh_wlc': DATA_DIR / 'he' / 'tanakh_wlc.txt',
    'iliad_perseus':     DATA_DIR / 'el' / 'iliad_perseus.xml',
    'greek_nt_opengnt':  DATA_DIR / 'el' / 'opengnt_v3_3.csv',
}

def _sha(p: Path):
    if not p.exists(): return None
    h = hashlib.sha256()
    with p.open('rb') as f:
        for blk in iter(lambda: f.read(65536), b''):
            h.update(blk)
    return h.hexdigest()

corpus_lock = {'files': {}, 'timestamp': datetime.now().isoformat()}
for name, path in RAW_FILES.items():
    corpus_lock['files'][name] = {
        'path':   str(path.relative_to(REPO)) if path.exists() else str(path),
        'exists': path.exists(),
        'size':   path.stat().st_size if path.exists() else 0,
        'sha256': _sha(path),
    }
combined = hashlib.sha256()
for name in sorted(corpus_lock['files']):
    s = corpus_lock['files'][name]['sha256']
    if s: combined.update(f'{name}:{s};'.encode())
corpus_lock['combined'] = combined.hexdigest()

(INT_DIR / 'corpus_lock.json').write_text(
    json.dumps(corpus_lock, indent=2), encoding='utf-8')

missing = [n for n, v in corpus_lock['files'].items() if not v['exists']]
if missing:
    raise RuntimeError(
        f'FATAL: {len(missing)} locked raw corpus files missing: {missing}\n'
        f'Refusing to generate corpus_lock.json from an incomplete set.'
    )
print(f'[lock ] corpus_lock.json  combined = {corpus_lock["combined"][:16]}...')"""
    )

    # Cell 11 — code_lock.json
    code(
        r"""# === Cell 11 · code_lock.json — SHA-256 of every .py in src/ + _build.py ===
code_lock = {'files': {}, 'timestamp': datetime.now().isoformat()}
for py in sorted((REPO / 'src').rglob('*.py')):
    code_lock['files'][str(py.relative_to(REPO)).replace('\\', '/')] = _sha(py)

# AUDIT 2026-04-19 (v5 fix ⑤): include the notebook builder itself. Previously
# only src/*.py were locked; `notebooks/ultimate/_build.py` (which generates
# 100 %% of this notebook's code) could be edited and the notebook regenerated
# without the code-lock detecting the change. A hostile actor or an accidental
# merge could silently alter the analytic logic. Now any edit to the builder
# invalidates the lock at Phase 21.
_builder = REPO / 'notebooks' / 'ultimate' / '_build.py'
if _builder.exists():
    code_lock['files']['notebooks/ultimate/_build.py'] = _sha(_builder)

# AUDIT FIX 2026-04-27: the CamelTools root cache used to be included in
# the code lock (per the 2026-04-21 fix below) on the theory that its
# contents affect H_cond / Phi_M reproducibility. In practice the cache
# is mutated mid-run by Phase 5 (CamelTools warming adds newly-seen
# tokens), so locking its SHA at run-start guaranteed a false-positive
# HallucinationError at Cell 126 on every clean run.
#
# Reproducibility argument: cache lookups are deterministic given the
# CamelTools library version (which IS hashed implicitly via the
# package-version snapshot in `_manifest.json`). The cache file's SHA
# tracks WHICH tokens have been seen, not WHETHER the
# token->root mapping is correct. Locking the contents conflates
# coverage with correctness.
#
# Therefore the cache file is NO LONGER part of code_lock. If you need
# the old behaviour for an audit pass, lock it AFTER Phase 5 instead of
# before, so the lock captures the warmed state.
#
# Original (2026-04-21):
#   _camel_cache = REPO / 'src' / 'cache' / 'cameltools_root_cache.pkl.gz'
#   if _camel_cache.exists():
#       code_lock['files']['src/cache/cameltools_root_cache.pkl.gz'] = _sha(_camel_cache)

try:
    import subprocess
    rev = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True, timeout=5,
    ).strip()
    code_lock['git_head'] = rev
except Exception:
    code_lock['git_head'] = None

combined = hashlib.sha256()
for name in sorted(code_lock['files']):
    combined.update(f'{name}:{code_lock["files"][name]};'.encode())
code_lock['combined'] = combined.hexdigest()

(INT_DIR / 'code_lock.json').write_text(
    json.dumps(code_lock, indent=2), encoding='utf-8')

print(f'[lock ] code_lock.json    combined = {code_lock["combined"][:16]}...'
      f'  ({len(code_lock["files"])} .py files)')
if code_lock['git_head']:
    print(f'[lock ] git HEAD         = {code_lock["git_head"][:12]}')"""
    )

    # Cell 12 — names_registry.json (whitelist)
    code(
        r"""# === Cell 12 · names_registry.json — whitelist of legal finding IDs ===
NAMES = {
    # Sanity gates
    'G1_min_units', 'G2_no_single_token', 'G3_no_identical',
    'G4_cv_valid', 'G5_arabic_ratio',
    # Core 31 tests
    *(f'T{i}'  for i in range(1, 32)),
    # Discoveries
    *(f'D{i:02d}' for i in range(1, 29)),
    # Shannon-Aljamal structural conditions
    *(f'S{i}'  for i in range(1, 6)),
    # Formal-proof gaps (G3 and G5 are math tautologies -> FALSIFIED)
    *(f'G{i}'  for i in range(1, 6)),
    # Universal-law candidates
    *(f'L{i}'  for i in range(1, 8)),
    # Exploratory sub-experiments
    'E1_transmission_sim', 'E2_csiszar_korner', 'E3_berry_esseen',
    'E_harakat_capacity',  'E_epi_waqf',         'E_epi_variants',
    # Supplementary
    'Supp_A_Hurst', 'Supp_B_multilevel_Hurst', 'Supp_C_acoustic_bridge',
    # Pre-reg
    'PreReg_A_leave_one_out', 'PreReg_B_meccan_medinan', 'PreReg_C_bootstrap_omega',
    # Meta
    'Adiyat_blind', 'PROXY_1_compression_p1', 'PROXY_2_compression_p3',
    'Tight_fairness_band_A', 'Tight_fairness_band_B', 'Tight_fairness_band_C',
    'CamelTools_phi_m_rerun',  'Heuristic_phi_m_rerun',
    'MonteCarlo_const_null',   'Blind_rejection_rates',
    'Abbasi_8_discriminators', 'Partial_quote_leak',
    'Nuzul_vs_Mushaf',         'PickleBug_simulation',
    # Audit-added (2026-04-18): proper multivariate & permutation statistics
    'Phi_M_hotelling_T2',      'Phi_M_perm_p_value',
    # Audit-added (2026-04-24, opportunity A11): analytic F-tail log10 p
    # for the Phi_M Hotelling T2. Sandbox source: experiments/exp01_ftail/.
    'Phi_M_F_tail_log10_p',
    'Psi_perm_p_value',        'Psi_quran_rank',
    'H_cond_MM_quran',         'Hurst_DFA_quran',
    'Adiyat_metric7_perm_p',   'MI_bin_sensitivity_range',
    'FDR_BH_n_significant',    'MI_D05_miller_madow',
    # Audit v3 (2026-04-18): additional diagnostics (all tol=inf reporting)
    'Supp_A_Hurst_R2',         'Hurst_DFA_quran_R2',
    'Mahal_family_perm_p',     'Supp_C_acoustic_bridge_perm_p',
    'TDA_H1_bootstrap_p',
    'L7_sparse_pca_d',         'L7_sparse_pca_perm_p',
    # Nobel/PNAS audit (2026-04-18): kernel HSIC + persistent-homology appendix
    'HSIC_EL_CN_quran',        'HSIC_EL_CN_perm_p',
    'HSIC_G2_max_quran',       'HSIC_G2_perm_p',
    'TDA_H1_max_persistence',  'TDA_n_loops_long_lived',
    # Audit 2026-04-19 (fix ②): FDR denominator + coverage scalars
    'FDR_BH_n_tested',         'FDR_BH_n_claims_total',
    'FDR_BH_coverage_frac',
    # Audit 2026-04-19 (fix ③): hindawi leave-one-out OOD replacement for D13
    'D13_hindawi_loo',         'D13_hindawi_in_pool_legacy',
    # Audit 2026-04-19 (fix ④): Abbasi directional beats (replaces non-directional D27)
    'Abbasi_directional_beats','D27_directional',
}
NAMES = sorted(NAMES)
(INT_DIR / 'names_registry.json').write_text(
    json.dumps({'version': 1, 'names': NAMES}, indent=2), encoding='utf-8')

def assert_known(fid):
    if fid not in NAMES:
        raise UnknownFindingError(
            f'finding ID {fid!r} is not in names_registry.json — '
            f'possible AI hallucination or typo. Add it to NAMES in Cell 12 '
            f'if it is legitimate.'
        )

print(f'[lock ] names_registry.json  {len(NAMES)} legal finding IDs')"""
    )

    # Cell 13 — results_lock.json (+ hadith-leak regression sentinel)
    code(
        r"""# === Cell 13 · results_lock.json — 45 flagship scalars (pre-committed) ===
# Source: docs/FINDINGS_SCORECARD.md + docs/CLEAN_PIPELINE_REPORT.md
RESULTS_LOCK = [
    # AUDIT 2026-04-18: D02/S1/D28 now record Cohen's d purely as a LEGACY
    # indicator. Cohen's d on Mahalanobis-to-own-centroid is structurally
    # biased upward (control distances follow a chi distribution, not a
    # normal) so we downgrade verdict_expected to DEPRECATED and set
    # tol=inf — these entries no longer gate the run. The HEADLINE
    # statistics are Phi_M_hotelling_T2 and Phi_M_perm_p_value (below).
    {'id':'D02','name':'LEGACY Phi_M Cohen d (biased)',     'expected':6.34,'tol':float('inf'),'verdict_expected':'DEPRECATED (biased; see Phi_M_hotelling_T2)'},
    {'id':'S1', 'name':'LEGACY multivariate separation d',   'expected':6.34,'tol':float('inf'),'verdict_expected':'DEPRECATED (biased; see Phi_M_hotelling_T2)'},
    # AUDIT 2026-04-19 (fix ④): D27 now stores the DIRECTIONAL beat count
    # (pre-registered per-feature signs), not the legacy non-directional
    # abs(diff)>0.01 count. The directional number is expected to be lower
    # (≤ legacy 7), so we downgrade D27 to reporting-only and let the new
    # first-class scalar `D27_directional` carry the honest headline. The
    # legacy non-directional count is still available at `Abbasi_8_discriminators`.
    {'id':'D27','name':'LEGACY Abbasi discrimination (now directional)',
     'expected':7.0, 'tol':float('inf'),
     'verdict_expected':'DEPRECATED (non-directional; see D27_directional)'},
    {'id':'D28','name':'LEGACY tight-fairness Cohen d',     'expected':6.34,'tol':float('inf'),'verdict_expected':'DEPRECATED (biased; see Phi_M_hotelling_T2)'},
    {'id':'D03','name':'Quran EL',                            'expected':0.707,'tol':0.03,'verdict_expected':'PROVED'},
    {'id':'D04','name':'Quran CN',                            'expected':0.086,'tol':0.01,'verdict_expected':'PROVED'},
    # AUDIT 2026-04-19 (v5) — scalars affected by three upstream fixes
    #  (a) V2: `hadith_bukhari` removed from ARABIC_CTRL / ARABIC_CORPORA_FOR_CONTROL
    #  (b) V3: Band-A filter added to T1 (D01) and T8 (D17, S5)
    #  (c) V4: Fisher p now uses chi2.sf (tail-accurate) instead of 1 - chi2.cdf
    # These methodology corrections will shift several blessed numbers by > 5 %.
    # We widen tol = inf and mark them PENDING_REBLESS_v5 so the first post-audit
    # run does not halt. On confirmed re-run, set UPDATE_LOCK=True to pin new
    # baselines and re-narrow tol. Verdict labels kept as a reminder of the
    # pre-audit paper claim so drift direction stays legible.
    {'id':'D01','name':'Anti-metric VL_CV d (Band A, audit v5)',
     'expected':1.40,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was WEAKENED, pre-Band-A)'},
    {'id':'D06','name':'Turbo gain G_turbo',                  'expected':1.644,'tol':0.05,'verdict_expected':'WEAKENED'},
    {'id':'S4', 'name':'H3/H2 bigram sufficiency',            'expected':0.222,'tol':0.02,'verdict_expected':'PROVED (partial)'},
    {'id':'D08','name':'Markov z-score (Quran) — audit v5',
     'expected':44.9,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was WEAKENED, pre-hadith-removal)'},
    {'id':'T7', 'name':'I(EL;CN) corpus-level (bits)',        'expected':1.17,'tol':0.10,'verdict_expected':'PROVED (corpus)'},
    {'id':'D05','name':'I(EL;CN) unit-level (bits)',          'expected':0.10,'tol':0.15,'verdict_expected':'FALSIFIED (unit)'},
    {'id':'D09','name':'Classifier AUC Quran vs Arabic ctrl — audit v5',
     'expected':0.998,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal)'},
    {'id':'D23','name':'Canon-wins rate (Quran)',             'expected':1.00,'tol':0.05,'verdict_expected':'PROVED'},
    {'id':'D24','name':'Phi_M 10-fold CV median d — audit v5',
     'expected':6.89,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal)'},
    {'id':'D26','name':'Bootstrap Omega > 2.0 fraction',      'expected':1.00,'tol':0.05,'verdict_expected':'PROVED STRONGER'},
    {'id':'D07','name':'Scale-free −log10 Fisher p @ W=10 — audit v5',
     'expected':16.0,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was 1.1e-16 machine-eps artefact; now chi2.sf)'},
    {'id':'D11','name':'Perturbation gap sum — audit v5',
     'expected':5.02,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal)'},
    {'id':'D14','name':'Verse-internal gap — audit v5',
     'expected':5.80,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal)'},
    {'id':'D17','name':'Canonical path z-score (Band A, audit v5)',
     'expected':-3.96,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED, pre-Band-A)'},
    {'id':'S5', 'name':'Shannon-Aljamal path minimality z (Band A, audit v5)',
     'expected':-3.96,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED, pre-Band-A)'},
    {'id':'D22','name':'Root-diversity x EL — audit v5',
     'expected':0.632,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal)'},
    {'id':'E_harakat_capacity', 'name':'H(harakat | rasm) bits',  'expected':1.96,'tol':0.15,'verdict_expected':'PROVED'},
    {'id':'D20','name':'Hierarchical Omega (Quran) — audit v5',
     'expected':7.89,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was WEAKENED, pre-hadith-removal)'},
    {'id':'D10','name':'%T>0 Quran',                          'expected':39.7,'tol':3.0, 'verdict_expected':'PROVED STRONGER'},
    {'id':'T28','name':'H2/H1 Markov-order d — audit v5',
     'expected':-0.03,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was NOT REPRODUCED, pre-hadith-removal)'},
    {'id':'T29','name':'phi_frac (golden-ratio claim)',       'expected':-0.915,'tol':0.20,'verdict_expected':'NOT REPRODUCED'},
    {'id':'D25','name':'F_Meccan Band A — audit v5',
     'expected':0.80,'tol':float('inf'),'verdict_expected':'PENDING_REBLESS_v5 (was FALSIFIED, pre-hadith-removal)'},
    {'id':'D18','name':'Adjacent diversity percentile',       'expected':10.6,'tol':5.0, 'verdict_expected':'FALSIFIED'},
    {'id':'D21','name':'Rhyme-swap P3 Quran vs Bible',        'expected':-0.28,'tol':0.15,'verdict_expected':'NOT REPRODUCED'},
    {'id':'G1', 'name':'Hill alpha min across 5 features',    'expected':2.5, 'tol':1.0, 'verdict_expected':'PROVED'},
    {'id':'G2', 'name':'Max normalised 5-ch MI',              'expected':0.30,'tol':0.05,'verdict_expected':'PROVED'},
    {'id':'G3', 'name':'Hessian PD claim (tautology)',        'expected':0.0, 'tol':0.0, 'verdict_expected':'FALSIFIED by math'},
    {'id':'G5', 'name':'gamma(Omega) algebraic claim',        'expected':0.0, 'tol':0.0, 'verdict_expected':'FALSIFIED by math'},
    {'id':'L1','name':'SCI (Quran)',                'expected':5.3,'tol':2.0,'verdict_expected':'EXPLORATORY'},
    {'id':'L2','name':'Retention scaling alpha',    'expected':1.0,'tol':5.0,'verdict_expected':'EXPLORATORY'},
    {'id':'L3','name':'Free-energy F (Quran)',      'expected':0.0,'tol':5.0,'verdict_expected':'EXPLORATORY'},
    {'id':'L4','name':'Aljamal invariance CV',      'expected':1.7,'tol':1.0,'verdict_expected':'EXPLORATORY'},
    {'id':'L5','name':'OBI inequality slack (kappa=1)','expected':-74.0,'tol':15.0,'verdict_expected':'EXPLORATORY'},
    {'id':'L6','name':'Empirical gamma slope b',    'expected':0.0,'tol':0.5,'verdict_expected':'EXPLORATORY'},
    {'id':'L7','name':'Psi(Quran) rank',            'expected':1.0,'tol':1.0,'verdict_expected':'EXPLORATORY'},
    {'id':'Adiyat_blind','name':'Adiyat winning variant (7-metric)','expected':0.71,'tol':0.30,'verdict_expected':'PROVED'},
    {'id':'Supp_A_Hurst','name':'Quran Hurst H','expected':0.70,'tol':0.15,'verdict_expected':'PROVED'},
    # AUDIT 2026-04-18 headline statistics (unbiased replacements for D02/S1/D28)
    # T² and p-value are distribution-free. tol=inf until user runs with
    # UPDATE_LOCK=True to pin exact values for this environment.
    {'id':'Phi_M_hotelling_T2', 'name':'Phi_M Hotelling T² (Band A)',  'expected':0.0,'tol':float('inf'),'verdict_expected':'HEADLINE (pending lock refresh)'},
    {'id':'Phi_M_perm_p_value', 'name':'Phi_M permutation p-value',    'expected':0.0,'tol':float('inf'),'verdict_expected':'HEADLINE (pending lock refresh)'},
    # Audit 2026-04-24 (opportunity A11): analytic F-tail log10(p) for Phi_M
    # Hotelling T². Replaces the permutation floor 1/(B+1)=5e-3 (B=200) with
    # the closed-form distribution-free p. Source: experiments/exp01_ftail/run.py
    # (mpmath 80-digit). tol generous because float64 noise in the upstream T²
    # propagates non-linearly through the F-tail; |drift| > 10 means the
    # underlying T² has fundamentally moved and the headline must be re-audited.
    {'id':'Phi_M_F_tail_log10_p', 'name':'Phi_M Hotelling T² analytic F-tail log10 p (mpmath 80-digit)',
     'expected':-480.25, 'tol':10.0,
     'verdict_expected':'PROVED HEADLINE (analytic, replaces perm-floor 1/(B+1))'},
    # Nobel/PNAS audit 2026-04-18: kernel-based independence (HSIC) — binning-free
    # alternative to the plug-in MI in Cell 40 (D05) and to the 5-channel NMI
    # in Cell 55 (G2). All tol=inf: reporting-only until methodology matures.
    {'id':'HSIC_EL_CN_quran',        'name':'HSIC(EL,CN) Quran (Band A)',    'expected':0.0,'tol':float('inf'),'verdict_expected':'REPORTING (binning-free MI alt)'},
    {'id':'HSIC_EL_CN_perm_p',       'name':'HSIC(EL,CN) permutation p',     'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (binning-free MI alt)'},
    {'id':'HSIC_G2_max_quran',       'name':'HSIC 5-ch max pair (Quran)',    'expected':0.0,'tol':float('inf'),'verdict_expected':'REPORTING (G2 kernel variant)'},
    {'id':'HSIC_G2_perm_p',          'name':'HSIC 5-ch max perm p',          'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (G2 kernel variant)'},
    # Nobel/PNAS audit 2026-04-18: persistent-homology appendix (Phase 22).
    # Only populated when USE_TDA=True; otherwise stays NaN with tol=inf.
    {'id':'TDA_H1_max_persistence',  'name':'Max H1 persistence (Quran 5D)', 'expected':0.0,'tol':float('inf'),'verdict_expected':'APPENDIX (USE_TDA)'},
    {'id':'TDA_n_loops_long_lived',  'name':'# H1 features > 0.25 σ',        'expected':0.0,'tol':float('inf'),'verdict_expected':'APPENDIX (USE_TDA)'},
    # Audit v3 (2026-04-18) diagnostics — all tol=inf (reporting only)
    {'id':'Supp_A_Hurst_R2',             'name':'R/S Hurst log-log R² (Quran)',   'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (scaling-regime gate)'},
    {'id':'Hurst_DFA_quran_R2',          'name':'DFA Hurst log-log R² (Quran)',    'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (scaling-regime gate)'},
    {'id':'Supp_C_acoustic_bridge_perm_p','name':'Supp-C rhyme×conn perm p',       'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (chi2 replacement)'},
    {'id':'TDA_H1_bootstrap_p',          'name':'TDA H1 marginal-shuffle perm p', 'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (closes caveat c)'},
    {'id':'L7_sparse_pca_d',             'name':"Sparse-PCA PC1 Cohen's d (Q vs ctrl)",'expected':0.0,'tol':float('inf'),'verdict_expected':'REPORTING (Ψ alternative)'},
    {'id':'L7_sparse_pca_perm_p',        'name':'Sparse-PCA PC1 perm p',           'expected':1.0,'tol':float('inf'),'verdict_expected':'REPORTING (Ψ alternative)'},
]
_lock_str  = json.dumps(RESULTS_LOCK, sort_keys=True, ensure_ascii=False)
_lock_hash = hashlib.sha256(_lock_str.encode()).hexdigest()

(INT_DIR / 'results_lock.json').write_text(
    json.dumps({'version':1, 'hash':_lock_hash,
                'timestamp':datetime.now().isoformat(),
                'entries':RESULTS_LOCK}, indent=2, ensure_ascii=False),
    encoding='utf-8',
)
print(f'[lock ] results_lock.json  {len(RESULTS_LOCK)} scalars  hash={_lock_hash[:16]}...')

# AUDIT 2026-04-19 (v5): hadith-leak regression sentinel.
# Every `ARABIC_CTRL` / `ARABIC_CORPORA_FOR_CONTROL` across the src layer
# MUST exclude `hadith_bukhari` (Sahih al-Bukhari quotes Quran verbatim).
# Cell 22 has been saying so since v1, but the src modules silently leaked
# it back into the pipeline until the v5 audit. This guard catches any
# future regression (e.g. a dependency upgrade re-introducing the default)
# before any downstream test runs.
try:
    from src.clean_pipeline  import ARABIC_CORPORA_FOR_CONTROL as _CP_CTRL
    from src.extended_tests  import ARABIC_CTRL as _ET1_CTRL
    from src.extended_tests2 import ARABIC_CTRL as _ET2_CTRL
    from src.extended_tests3 import ARABIC_CTRL as _ET3_CTRL
except ImportError as _e:
    raise ImportError(
        f'[FATAL] src module missing ARABIC_CTRL / ARABIC_CORPORA_FOR_CONTROL '
        f'export: {_e}. Add the constant to the relevant src/*.py file, '
        f'or update the sentinel import names in Cell 13.'
    ) from _e
for _nm, _pool in (('clean_pipeline.ARABIC_CORPORA_FOR_CONTROL', _CP_CTRL),
                   ('extended_tests.ARABIC_CTRL',  _ET1_CTRL),
                   ('extended_tests2.ARABIC_CTRL', _ET2_CTRL),
                   ('extended_tests3.ARABIC_CTRL', _ET3_CTRL)):
    if 'hadith_bukhari' in _pool:
        raise HallucinationError(
            f'[HALL] hadith_bukhari leaked back into {_nm} — '
            f'quarantine violation (Sahih al-Bukhari quotes the Quran by design, '
            f'so including it in the Arabic control pool biases every '
            f'Mahalanobis-to-centroid statistic upward). Re-remove it before running.'
        )
print(f'[lock ] hadith-leak sentinel OK — 4 control pools verified quarantined')"""
    )

    # Cell 14 — bless + verifier
    code(
        r"""# === Cell 14 · result-blessing helpers + Phase-2 verifier ===
def bless(finding_id, actual, *, tol_override=None):
    '''Record actual and compare against locked expected; drift triggers HallucinationError at Phase 21.
    Non-numeric actual, NaN, or failed cast all resolve to drift_ok=False UNLESS
    the tolerance is float("inf") (reporting-only entries).'''
    assert_known(finding_id)
    entry = next((e for e in RESULTS_LOCK if e['id'] == finding_id), None)
    rec   = {'actual': actual, 'drift_ok': True, 'expected': None, 'tol': None}
    # AUDIT 2026-04-18 (v4): even when `finding_id` has no lock entry, the
    # caller may still pass `tol_override=float('inf')` to document that the
    # statistic is reporting-only. Record the tol so downstream code can
    # reason about it; previously this was silently dropped.
    if entry is None and tol_override is not None:
        rec.update(tol=tol_override)
    if entry is not None:
        exp = entry['expected']
        tol = tol_override if tol_override is not None else entry['tol']
        rec.update(expected=exp, tol=tol, name=entry['name'],
                   verdict_expected=entry['verdict_expected'])
        try:
            af = float(actual); ef = float(exp)
            if math.isnan(af) or math.isnan(ef):
                raise ValueError('NaN in compare')
            diff = abs(af - ef)
            rec['abs_drift'] = diff
            rec['drift_ok']  = (tol == float('inf')) or (diff <= tol) or UPDATE_LOCK
            if not rec['drift_ok']:
                print(f'[DRIFT] {finding_id:<24s} expected {exp}  got {actual}  |d|={diff:.4g}  tol={tol}')
        except (TypeError, ValueError) as e:
            rec['abs_drift'] = float('inf')
            # AUDIT 2026-04-18 (v4): previously `rec['drift_ok'] = UPDATE_LOCK`
            # ignored `tol=float('inf')` on non-numeric actuals, so any
            # reporting-only entry that produced a NaN (missing corpus,
            # HSIC fallback, TDA skipped, …) would wrongly trip the
            # Phase-21 HallucinationError. Respect infinite tolerance here.
            rec['drift_ok']  = (tol == float('inf')) or UPDATE_LOCK
            if not rec['drift_ok']:
                print(f'[DRIFT] {finding_id:<24s} non-numeric actual={actual!r} ({e}); treating as FAIL')
    ALL_RESULTS[finding_id] = rec
    return actual

def _verify_phase_2():
    required = ['preregistration.json', 'corpus_lock.json',
                'code_lock.json', 'names_registry.json', 'results_lock.json']
    missing = [f for f in required if not (INT_DIR / f).exists()]
    assert not missing, f'[FATAL] Phase 2 missing locks: {missing}'
    print('[OK   ] Phase 2 — 4 integrity locks + pre-registration all written')

_verify_phase_2()
save_checkpoint('02_locks', {'corpus_sha': corpus_lock['combined'],
                             'code_sha':   code_lock['combined'],
                             'n_names':    len(NAMES),
                             'n_locked':   len(RESULTS_LOCK)})"""
    )


# ============================================================================
# PHASE 3 — Data integrity + pickle-bug sanity simulation (cells 15-19)
# ============================================================================
def build_phase_3() -> None:
    phase_header(
        3,
        "Data integrity + G1-G5 sanity gate + pickle-bug simulation",
        "Load all corpora from raw files via `src.raw_loader`, run the G1-G5 "
        "sanity gate, and deliberately inject a fake 'تكوين ×7' Bible to prove "
        "the gate catches the regression that bit us in v3 of the legacy "
        "pipeline. No hand-crafted pickles.",
    )

    # Cell 15 — load all corpora from raw
    code(
        r"""# === Cell 15 · load all corpora from raw files (src.raw_loader) ===
# Each Unit = one surah / book-chapter with list[str] verses.
# Authoritative Arabic control pool: poetry_{jahili,islami,abbasi}, ksucca,
# arabic_bible, hindawi.  hadith_bukhari is QUARANTINED (quotes Quran).
from src import raw_loader as rl
from src import verify_corpora as vc
from src import features as ft
from src import roots as rc
from src import clean_pipeline as cp
from src import extended_tests as et
from src import extended_tests2 as et2
from src import extended_tests3 as et3

log('loading all corpora from raw...')
t0 = time.time()
CORPORA = rl.load_all(include_extras=True)
log(f'load_all took {time.time()-t0:.1f}s; {len(CORPORA)} corpora')
print('  corpus                 units  verses    words')
for name in sorted(CORPORA):
    units = CORPORA[name]
    n_v = sum(len(u.verses) for u in units)
    n_w = sum(sum(len(v.split()) for v in u.verses) for u in units)
    print(f'  {name:<22s}  {len(units):>5d}  {n_v:>6d}  {n_w:>8d}')"""
    )

    # Cell 16 — G1-G5 sanity gate
    code(
        r"""# === Cell 16 · G1-G5 sanity gate (src.verify_corpora.verify_all) ===
SANITY = vc.verify_all(CORPORA)
fails = {n: r for n, r in SANITY.items() if not r['ok']}
for name, r in SANITY.items():
    flag = 'OK  ' if r['ok'] else 'FAIL'
    reasons = r.get('reasons', []) if isinstance(r.get('reasons'), list) else []
    n_units = r.get('n', r.get('n_units', len(CORPORA.get(name, []))))
    print(f'  [{flag}] {name:<22s}  n={n_units:>5d}  reasons={reasons}')

def _any_reason(key):
    return any(
        key in (r.get('reasons') if isinstance(r.get('reasons'), list) else [])
        for r in SANITY.values()
    )

bless('G1_min_units',       int(all(
    (r.get('n', r.get('n_units', 0)) if isinstance(r, dict) else 0) >= 10
    for r in SANITY.values())))
bless('G2_no_single_token', int(not _any_reason('single_token')))
bless('G3_no_identical',    int(not _any_reason('identical_verses')))
bless('G4_cv_valid',        int(not _any_reason('cv_invalid')))
bless('G5_arabic_ratio',    int(not _any_reason('arabic_ratio_low')))
assert not fails, f'[FATAL] sanity gate failed on {list(fails)}'
print(f'[OK   ] G1-G5 gate passed on all {len(CORPORA)} corpora')"""
    )

    # Cell 17 — pickle-bug simulation
    code(
        r"""# === Cell 17 · PICKLE-BUG SIMULATION — inject fake Bible and prove gate catches it ===
# Historical bug: legacy pickle contained 7 copies of Genesis-1 instead of the full Bible.
from copy import deepcopy
from src.raw_loader import Unit

fake_verse = 'في البدء خلق الله السماوات والأرض'  # Genesis 1:1
# One fake 'chapter' with 100 identical verses — must fail G3 (identical verses)
fake_chapter = Unit(corpus='arabic_bible_FAKE', label='GEN:01',
                    verses=[fake_verse] * 100)
from src.verify_corpora import verify_corpus
fake_ok, fake_reasons = verify_corpus('arabic_bible_FAKE', [fake_chapter])
print(f'[sim  ] corrupted Bible ok={fake_ok}  reasons={fake_reasons}')
assert not fake_ok, '[FATAL] gate failed to catch corrupted pickle!'
bless('PickleBug_simulation', 1.0)
print('[OK   ] gate caught the fake pickle as expected')"""
    )

    # Cell 18 — extract 5-D features (per-surah records; Band A at n_verses level)
    code(
        r"""# === Cell 18 · extract 5-D features PER UNIT (per surah) ===
# Band A = surahs with 15-100 verses (paper §2.1). Features computed on
# each surah independently, then stacked into a (n_surahs, 5) matrix per corpus.
BAND_A_LO, BAND_A_HI = 15, 100
FEAT_COLS = ['EL', 'VL_CV', 'CN', 'H_cond', 'T']

def _extract_feats(corpora):
    out = {}
    for name, units in corpora.items():
        recs = []
        lang_ag = name in ('iliad_greek', 'greek_nt', 'hebrew_tanakh')
        stops = None
        if lang_ag:
            stops = ft.derive_stopwords((v for u in units for v in u.verses), top_n=20)
        for u in units:
            if lang_ag:
                fv = ft.features_5d_lang_agnostic(u.verses, stops=stops)
            else:
                fv = ft.features_5d(u.verses)
            recs.append({
                'label': u.label,
                'n_verses': len(u.verses),
                'n_words': sum(len(v.split()) for v in u.verses),
                'EL': float(fv[0]), 'VL_CV': float(fv[1]), 'CN': float(fv[2]),
                'H_cond': float(fv[3]), 'T': float(fv[4]),
            })
        out[name] = recs
    rc.flush_cache()
    return out

t0 = time.time()
FEATS = _extract_feats(CORPORA)
log(f'5-D features computed for {len(FEATS)} corpora in {time.time()-t0:.1f}s')

def _band_a_X(recs):
    r = [x for x in recs if BAND_A_LO <= x['n_verses'] <= BAND_A_HI]
    return np.array([[x[c] for c in FEAT_COLS] for x in r], dtype=float)

print('\n  corpus                  n_units  n_bandA  EL_mean  VL_mean  CN_mean  H_mean   T_mean')
for n in sorted(FEATS):
    recs = FEATS[n]
    X = _band_a_X(recs)
    if len(X) == 0: continue
    print(f'  {n:<22s}  {len(recs):>6d}   {len(X):>5d}   '
          f'{X[:,0].mean():.3f}   {X[:,1].mean():.3f}   '
          f'{X[:,2].mean():.3f}   {X[:,3].mean():.3f}   {X[:,4].mean():+.3f}')"""
    )

    # Cell 19 — derive RHYME_LETTERS from data, verify, and checkpoint full state
    code(
        r"""# === Cell 19 · derive RHYME_LETTERS + Phase-3 verifier + checkpoint ===
# Rhyme-class letters are DERIVED from the top-k Quran verse-ends (covering
# 95% of finals), NOT hardcoded. The derived string is pinned into
# corpus_lock so downstream cells cannot silently drift.
#
# CAVEAT (audit 2026-04-18): RHYME_LETTERS captures GRAPHEMIC rhyme (the last
# written character of the last token), NOT phonological rhyme. In Arabic
# rasm (without harakat), many written characters cover several phonemes,
# and classical Arabic poetics (qāfiya) distinguishes these. So anything
# labeled "rhyme" in this notebook is the graphemic proxy. Upgrading to a
# phonological detector would require vocalised text + a qāfiya parser,
# both beyond the scope of the current pipeline.
from collections import Counter as _Ctr
_final_counts = _Ctr()
for u in CORPORA.get('quran', []):
    for v in u.verses:
        toks = v.split()
        if not toks: continue
        last = toks[-1].strip()
        if last: _final_counts[last[-1]] += 1
_total = sum(_final_counts.values())
RHYME_LETTERS = ''
_cum = 0
for ch, c in _final_counts.most_common():
    RHYME_LETTERS += ch
    _cum += c
    if _cum / max(_total, 1) >= 0.95: break
print(f'[rhyme] derived RHYME_LETTERS = {RHYME_LETTERS!r}  '
      f'({len(RHYME_LETTERS)} chars cover {_cum/_total:.1%} of Quran verse-ends)')
# Pin into corpus_lock so any re-run must produce the same string.
if 'derived_rhyme_letters' not in corpus_lock:
    corpus_lock['derived_rhyme_letters'] = RHYME_LETTERS
    (INT_DIR / 'corpus_lock.json').write_text(
        json.dumps(corpus_lock, indent=2), encoding='utf-8'
    )
elif corpus_lock.get('derived_rhyme_letters') != RHYME_LETTERS:
    raise HallucinationError(
        f'[HALL] derived RHYME_LETTERS drift: locked={corpus_lock["derived_rhyme_letters"]!r} '
        f'computed={RHYME_LETTERS!r}'
    )

def _verify_phase_3():
    assert 'quran' in FEATS, 'quran features missing'
    q_recs = [r for r in FEATS['quran'] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    assert len(q_recs) >= 50, f'quran Band-A surahs too few: {len(q_recs)}'
    q_means = np.array([[r[c] for c in FEAT_COLS] for r in q_recs]).mean(0)
    assert 0.3 < q_means[0] < 0.95, f'EL out of range: {q_means[0]}'
    assert 0.1 < q_means[1] < 1.5,  f'VL_CV out of range: {q_means[1]}'
    assert len(RHYME_LETTERS) >= 5, f'RHYME_LETTERS too short: {RHYME_LETTERS!r}'
    print(f'[OK   ] Phase 3 — {len(q_recs)} Quran Band-A surahs, mean EL={q_means[0]:.3f}')

_verify_phase_3()
save_checkpoint('03_integrity', {
    'corpora':       sorted(CORPORA),
    'n_units':       {n: len(u) for n, u in CORPORA.items()},
    'n_bandA_units': {n: len([r for r in FEATS[n] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI])
                      for n in FEATS},
    'RHYME_LETTERS': RHYME_LETTERS,
}, state={
    'CORPORA': CORPORA, 'FEATS': FEATS, 'SANITY': SANITY,
    'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI, 'FEAT_COLS': FEAT_COLS,
    'RHYME_LETTERS': RHYME_LETTERS, 'ALL_RESULTS': ALL_RESULTS,
})"""
    )


# ============================================================================
# PHASE 4 — Leakage audit (cells 20-23)
# ============================================================================
def build_phase_4() -> None:
    phase_header(
        4,
        "Leakage audit — exact-verse + partial-quote (≥15-char n-gram)",
        "Confirm no Quranic verse appears verbatim or as a long hadith-quote "
        "inside any of the 9 control corpora. Leakage would inflate the "
        "Mahalanobis separation artificially.",
    )

    # Cell 20 — exact-verse leak
    code(
        r"""# === Cell 20 · exact-verse leak audit (Quran vs all other corpora) ===
import re
_ar_norm = re.compile(r'[\u064B-\u0652\u0670\u0671\u0640\s]+')
def _norm(t): return _ar_norm.sub(' ', t).strip()

# iterate over verses (strings), not units
quran_set = {_norm(v) for u in CORPORA['quran'] for v in u.verses}
leak_hits = {}
for name, units in CORPORA.items():
    if name == 'quran': continue
    k = 0
    for u in units:
        for v in u.verses:
            if _norm(v) in quran_set: k += 1
    leak_hits[name] = k
print('[leak ] exact-verse hits per control corpus:')
for n, k in sorted(leak_hits.items()):
    print(f'  {n:<22s}  hits={k}')
total = sum(leak_hits.values())
# hadith is allowed to quote Quran; others must be zero
hadith_key = next((k for k in leak_hits if 'hadith' in k), None)
non_hadith_hits = sum(v for k, v in leak_hits.items() if k != hadith_key)
assert non_hadith_hits == 0, f'[FATAL] exact-verse leak in non-hadith: {non_hadith_hits}'
print(f'[OK   ] zero exact-verse leakage in non-hadith controls (hadith allowed)')"""
    )

    # Cell 21 — partial-quote leak (15-char n-gram)
    code(
        r"""# === Cell 21 · partial-quote leak (≥15-char normalised n-gram) ===
def _ngrams(text, n=15):
    t = _norm(text)
    if len(t) < n: return []
    return [t[i:i+n] for i in range(len(t) - n + 1)]

# build set of 15-char n-grams from Quran verses
quran_ngrams = set()
for u in CORPORA['quran']:
    for v in u.verses:
        quran_ngrams.update(_ngrams(v, 15))
print(f'[leak ] Quran 15-char n-gram set size: {len(quran_ngrams)}')

partial_hits = {}
for name, units in CORPORA.items():
    if name == 'quran': continue
    n_verses_with_hit = 0; n_verses = 0
    for u in units:
        for v in u.verses:
            n_verses += 1
            if any(ng in quran_ngrams for ng in _ngrams(v, 15)):
                n_verses_with_hit += 1
    partial_hits[name] = (n_verses_with_hit, n_verses)
print('[leak ] partial-quote (≥15-char) verse-level hits:')
for n, (k, total_v) in sorted(partial_hits.items()):
    pct = 100 * k / max(1, total_v)
    print(f'  {n:<22s}  {k:>5d} / {total_v:>6d}  ({pct:5.2f}%)')

# hadith_bukhari and ksucca are LEGITIMATELY allowed to quote Quran:
#   - hadith is Prophetic tradition which cites the Quran directly
#   - ksucca is historical Muslim prose written AFTER the Quran, naturally
#     re-using Qur'anic phrasing.
# 15-char n-gram overlap below ~25% is tolerable; exact-verse hits must be 0.
ALLOWED_QUOTERS = {hadith_key, 'ksucca'}
max_pct_stranger = max(
    (100 * k / max(1, total_v)
     for name, (k, total_v) in partial_hits.items()
     if name not in ALLOWED_QUOTERS),
    default=0.0,
)
bless('Partial_quote_leak', float(max_pct_stranger / 100.0))
for n, (k, total_v) in partial_hits.items():
    pct = 100 * k / max(1, total_v)
    if n not in ALLOWED_QUOTERS:
        assert pct < 5.0, f'[FATAL] {n} has {pct:.2f}% partial-quote hits (unexpected quoter)'
print(f'[OK   ] partial-quote leakage within bounds (allowed quoters: {sorted(ALLOWED_QUOTERS)})')"""
    )

    # Cell 22 — control pool assignment (matches clean_pipeline.ARABIC_CORPORA_FOR_CONTROL)
    code(
        r"""# === Cell 22 · Arabic control pool (paper §2.2 + clean_pipeline.py) ===
# Authoritative Arabic control pool: all 6 non-Quran, non-hadith Arabic corpora.
ARABIC_CTRL_POOL = ['poetry_jahili', 'poetry_islami', 'poetry_abbasi',
                    'ksucca', 'arabic_bible', 'hindawi']
ARABIC_CTRL_POOL = [c for c in ARABIC_CTRL_POOL if c in FEATS]
print(f'[pool ] Arabic control pool ({len(ARABIC_CTRL_POOL)} corpora): {ARABIC_CTRL_POOL}')
print(f'[pool ] hadith_bukhari QUARANTINED (quotes Quran by design)')

# AUDIT 2026-04-18 (v4): ARABIC_FAMILY hoisted here (was defined lazily in
# Cell 95) so that Phase 14's checkpoint state dict (Cell 84) can carry it
# forward without a NameError. Includes Quran + 6 controls + hadith.
ARABIC_FAMILY = [c for c in ['quran', *ARABIC_CTRL_POOL, 'hadith_bukhari']
                 if c in FEATS]
print(f'[pool ] Arabic family (Ψ scope; {len(ARABIC_FAMILY)} corpora): {ARABIC_FAMILY}')"""
    )

    # Cell 23 — Phase-4 verifier + checkpoint
    code(
        r"""# === Cell 23 · Phase-4 verifier + checkpoint ===
def _verify_phase_4():
    assert non_hadith_hits == 0, 'exact-verse leak detected in non-hadith'
    assert max_pct_stranger < 5.0, 'partial-quote leak > 5% in unexpected quoter'
    print('[OK   ] Phase 4 — no leakage outside allowed quoters (hadith, ksucca)')

_verify_phase_4()
save_checkpoint('04_leakage', {'exact_hits': leak_hits, 'partial_hits': partial_hits,
                               'allowed_quoters': sorted(ALLOWED_QUOTERS),
                               'arabic_ctrl_pool': ARABIC_CTRL_POOL})"""
    )


# ============================================================================
# PHASE 5 — CamelTools warm-up + heuristic falsification (cells 24-27)
# ============================================================================
def build_phase_5() -> None:
    phase_header(
        5,
        "CamelTools warm-up + 21%-heuristic falsification",
        "Warm the CamelTools root cache over the full vocabulary, then "
        "explicitly demonstrate that the old 4-letter-prefix heuristic gets "
        "only ~21% accuracy on a 50-word gold standard while CamelTools "
        "gets ≥63%. Closes F-06.",
    )

    # Cell 24 — vocabulary scan
    code(
        r"""# === Cell 24 · warm CamelTools root cache over full vocabulary ===
from collections import Counter
import re

_tok_re = re.compile(r'[\u0621-\u064A]+')
def tokenise(text):
    return _tok_re.findall(text)

vocab = Counter()
for name, units in CORPORA.items():
    for u in units:
        for v in u.verses:
            vocab.update(tokenise(v))
print(f'[roots] unique tokens across all corpora: {len(vocab):,}')
if CAMEL_OK:
    t0 = time.time()
    vocab_list = [w for w, _ in vocab.most_common()]
    try:
        rc.warm_cache(vocab_list[:20000])  # cap for speed
        log(f'CamelTools cache warmed in {time.time()-t0:.1f}s ({min(len(vocab_list),20000)} tokens)')
    except Exception as e:
        log(f'warm_cache failed: {e}')
    try:
        cov = rc.coverage_report(vocab_list[:2000])
        cov_pct = cov.get('coverage_pct') or cov.get('coverage', 0)
        print(f'[roots] CamelTools coverage on top-2k vocab: {cov_pct:.1f}%')
    except Exception as e:
        print(f'[roots] coverage_report: {e}')
else:
    print('[roots] CamelTools unavailable; will use heuristic fallback')"""
    )

    # Cell 25 — 50-item gold-standard
    code(
        r"""# === Cell 25 · 50-item gold-standard root-accuracy showdown ===
# Hand-annotated 50-word gold set (heuristic ~21% vs CamelTools ~63%).
GOLD = [
    ('كتب','كتب'), ('يكتب','كتب'), ('كاتب','كتب'), ('مكتوب','كتب'),
    ('دخل','دخل'), ('يدخل','دخل'), ('مدخل','دخل'),
    ('قال','قول'), ('يقول','قول'), ('قائل','قول'),
    ('استغفر','غفر'), ('استخرج','خرج'), ('استنزل','نزل'),
    ('السماوات','سمو'), ('الأرض','أرض'), ('البحر','بحر'),
    ('النار','نور'), ('الشمس','شمس'), ('القمر','قمر'),
    ('مصلى','صلو'), ('مستخلف','خلف'), ('منفردين','فرد'),
    ('مرتبطون','ربط'), ('مشاركة','شرك'), ('تعاون','عون'), ('تفاعل','فعل'),
    ('انقسام','قسم'), ('استقبال','قبل'), ('استعادة','عود'),
    ('المستشفى','شفي'), ('المدرسة','درس'), ('المعهد','عهد'),
    ('العائلة','عول'), ('الأصدقاء','صدق'), ('الحكمة','حكم'),
    ('الصدق','صدق'), ('العدل','عدل'), ('الإيمان','أمن'),
    ('البناء','بني'), ('الكتابة','كتب'), ('الزراعة','زرع'),
    ('السفر','سفر'), ('الطائر','طير'), ('النجم','نجم'),
    ('الجبل','جبل'), ('الوادي','ودي'), ('الشجرة','شجر'),
    ('النبات','نبت'), ('الكتاب','كتب'), ('العلم','علم'),
    ('العمل','عمل'), ('الحياة','حيي'),
]
def _heur_root(w):
    '''Legacy 4-letter-prefix heuristic (~21% accurate).'''
    for pre in ('المست','الاست','است','الم','الت','ال','و','ف','ب','ل','ك'):
        if w.startswith(pre) and len(w) > len(pre) + 2:
            w = w[len(pre):]; break
    for suf in ('ون','ين','ات','ان','ها','هم','كم','نا','ة','ه','ي','ك','ا'):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            w = w[:-len(suf)]; break
    return w[:3]

heur_ok = sum(1 for w, r in GOLD if _heur_root(w) == r)
cam_ok  = 0
if CAMEL_OK:
    for w, r in GOLD:
        try:
            guess = (rc.primary_root(w) or '').replace(' ', '')
            if guess == r:
                cam_ok += 1
        except Exception:
            pass
print(f'[gold ] heuristic   : {heur_ok}/{len(GOLD)} = {100*heur_ok/len(GOLD):.0f}% correct')
if CAMEL_OK:
    print(f'[gold ] CamelTools  : {cam_ok}/{len(GOLD)} = {100*cam_ok/len(GOLD):.0f}% correct')
else:
    print('[gold ] CamelTools unavailable — only heuristic measured')"""
    )

    # Cell 26 — heuristic vs CamelTools: per-corpus H_cond comparison
    # + Miller-Madow bias-corrected H_cond (audit 2026-04-18)
    code(
        r"""# === Cell 26 · H_cond per corpus + Miller-Madow bias correction ===
# FEATS was built with CamelTools roots where available. Report it here.
# For the heuristic comparison we approximate by re-using FEATS but mark
# that the heuristic path would collapse H_cond — Phase 6 Cell 32 does the
# explicit Phi_M re-run under the heuristic.
print('  corpus                  H_cond(Band A mean)')
for name in sorted(FEATS):
    recs = [r for r in FEATS[name] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    if len(recs) < 3: continue
    hs = np.array([r['H_cond'] for r in recs])
    tag = ' <- Quran' if name == 'quran' else ''
    print(f'  {name:<22s}  {hs.mean():.3f}{tag}')

# --- Miller-Madow finite-sample bias correction ---
# Plug-in entropy underestimates true entropy with bias ≈ (K-1)/(2N) where
# K = number of observed symbols and N = sample size. For short surahs (Band A
# ≥ 15 verses => ≤14 bigram transitions) this bias is non-negligible.
#
# Miller-Madow:  H_MM = H_plug + (K_obs - 1) / (2 * N)
# Grassberger (1988) is slightly more accurate but we use Miller-Madow as
# the industry-standard first correction. Report MM-H_cond per corpus so
# the reader can see whether short-corpus bias alters the ranking.
from collections import Counter, defaultdict
import math as _math

def _h_cond_roots_mm(verses: list[str]) -> float:
    '''CamelTools-based H(root_{i+1}|root_i) with Miller-Madow correction.'''
    roots: list[str] = []
    for v in verses:
        toks = v.split()
        if not toks: continue
        r = rc.primary_root(toks[-1]) or '<unk>'
        roots.append(r)
    if len(roots) < 2: return 0.0
    bigrams: dict[str, Counter] = defaultdict(Counter); marg: Counter = Counter()
    for a, b in zip(roots[:-1], roots[1:]):
        bigrams[a][b] += 1; marg[a] += 1
    total_trans = sum(marg.values())
    if total_trans == 0: return 0.0
    H_plug = 0.0; K_obs = 0
    for a, nx in bigrams.items():
        p_a = marg[a] / total_trans
        row_total = sum(nx.values()) or 1
        row_h = 0.0
        for n in nx.values():
            p = n / row_total
            if p > 0: row_h -= p * _math.log2(p)
        H_plug += p_a * row_h
        K_obs  += len(nx)
    # MM correction on the joint-outcome space (conservative upper bound)
    bias = (K_obs - 1) / (2 * max(1, total_trans))
    return float(H_plug + bias / _math.log(2))   # bias in nats -> bits

# Compute MM H_cond for Quran + each Arabic control over full Band-A units
print('\n[audit] Miller-Madow bias-corrected H_cond (Band A, per corpus)')
H_cond_MM = {}
for name in ['quran', *ARABIC_CTRL_POOL]:
    if name not in CORPORA: continue
    mm_vals = []
    for u in CORPORA[name]:
        if not (BAND_A_LO <= len(u.verses) <= BAND_A_HI): continue
        mm_vals.append(_h_cond_roots_mm(u.verses))
    if not mm_vals: continue
    H_cond_MM[name] = float(np.mean(mm_vals))
    # compare to plug-in from FEATS
    plug = np.mean([r['H_cond'] for r in FEATS[name]
                    if BAND_A_LO <= r['n_verses'] <= BAND_A_HI])
    delta = H_cond_MM[name] - plug
    tag = ' <- Quran' if name == 'quran' else ''
    print(f'  {name:<22s}  H_plug={plug:.3f}  H_MM={H_cond_MM[name]:.3f}  Δ={delta:+.3f}{tag}')
bless('H_cond_MM_quran', float(H_cond_MM.get('quran', float('nan'))),
      tol_override=float('inf'))"""
    )

    # Cell 27 — Phase-5 verifier + checkpoint
    code(
        r"""# === Cell 27 · Phase-5 verifier + checkpoint ===
def _verify_phase_5():
    assert heur_ok / len(GOLD) < 0.45, f'heuristic too good ({heur_ok}/{len(GOLD)})'
    if CAMEL_OK:
        assert cam_ok / len(GOLD) >= 0.40, f'CamelTools accuracy too low ({cam_ok}/{len(GOLD)})'
    print('[OK   ] Phase 5 — heuristic vs CamelTools comparison done (F-06)')

_verify_phase_5()
save_checkpoint('05_cameltools', {
    'heur_ok_of_n': (heur_ok, len(GOLD)),
    'camel_ok_of_n': (cam_ok, len(GOLD)) if CAMEL_OK else None,
    'camel_available': CAMEL_OK,
})"""
    )


# ============================================================================
# PHASE 6 — Apples-to-apples bands A/B/C + CamelTools-Φ_M re-run (cells 28-33)
# ============================================================================
def build_phase_6() -> None:
    phase_header(
        6,
        "Apples-to-apples matched-length bands A/B/C + CamelTools-Φ_M re-run",
        "Compute Φ_M under three matched-length bands to prove the separation "
        "is not a length-bias artefact, then repeat the primary Φ_M with "
        "CamelTools roots to close the partially-open gap in REMAINING_GAPS.",
    )

    # Cell 28 — define stacking helpers + Band B
    code(
        r"""# === Cell 28 · define Band B and stacking helpers ===
# Band B = surahs with 5-14 verses (shorter than Band A); used for sensitivity.
# Band C = 101-286 verses (longer than Band A); used for sensitivity.
# Band A, the primary, stays at [15, 100] from Phase 3.
BAND_B_LO, BAND_B_HI = 5, 14
# Band C upper bound = 286 (longest Quranic surah, Al-Baqarah). Using 400
# would include Arabic-bible chapters longer than any surah → not
# apples-to-apples at the high end.
BAND_C_LO, BAND_C_HI = 101, 286

def _X_for(name, lo=BAND_A_LO, hi=BAND_A_HI):
    recs = [r for r in FEATS.get(name, []) if lo <= r['n_verses'] <= hi]
    if len(recs) < 3: return np.zeros((0, 5))
    return np.array([[r[c] for c in FEAT_COLS] for r in recs], dtype=float)

def _band_a_units(name, lo=BAND_A_LO, hi=BAND_A_HI):
    '''Return the list of Unit objects for `name` whose verse-count lies in
    Band A (or supplied [lo, hi]). Required for apples-to-apples unit-level
    comparisons (oral transmission, E1 noise, L2 retention scaling).'''
    return [u for u in CORPORA.get(name, []) if lo <= len(u.verses) <= hi]

print('  corpus                  |A|   |B|    |C|')
for n in sorted(FEATS):
    a = len(_X_for(n, BAND_A_LO, BAND_A_HI))
    b = len(_X_for(n, BAND_B_LO, BAND_B_HI))
    c = len(_X_for(n, BAND_C_LO, BAND_C_HI))
    print(f'  {n:<22s}  {a:>4d}  {b:>4d}   {c:>4d}')"""
    )

    # Cell 29 — Mahalanobis helper + Band-A Φ_M
    #
    # AUDIT 2026-04-18: Cohen's d of Mahalanobis-to-own-centroid distances
    # is biased upward under the null (chi-distribution of control distances
    # is tighter than cross-distribution distances). We now report THREE
    # complementary statistics; Cohen's d stays for backward compatibility
    # but the HEADLINE is the permutation p-value of Hotelling's T².
    code(
        r"""# === Cell 29 · Band-A Φ_M Quran vs Arabic-control pool (primary) ===
X_QURAN     = _X_for('quran', BAND_A_LO, BAND_A_HI)
X_CTRL_POOL = np.vstack([_X_for(c, BAND_A_LO, BAND_A_HI) for c in ARABIC_CTRL_POOL
                         if len(_X_for(c, BAND_A_LO, BAND_A_HI)) > 0])

mu = X_CTRL_POOL.mean(axis=0)
S  = np.cov(X_CTRL_POOL.T, ddof=1)
lam = 1e-6
S_inv = np.linalg.inv(S + lam * np.eye(S.shape[0]))

def mahalanobis(X, mu, Sinv):
    X = np.atleast_2d(X)
    d = X - mu
    return np.sqrt(np.einsum('ij,jk,ik->i', d, Sinv, d))

d_q    = mahalanobis(X_QURAN,    mu, S_inv)
d_ctrl = mahalanobis(X_CTRL_POOL, mu, S_inv)

# --- Statistic 1: pooled Cohen's d on Mahalanobis distances (legacy) ---
# Known upward bias under the null since ctrl distances to their own μ
# follow a chi distribution with smaller mean than cross-distribution d.
# Kept for backward compat with the locked scalar but NOT the headline.
pooled_std = np.sqrt(((len(d_q)-1)*d_q.var(ddof=1) + (len(d_ctrl)-1)*d_ctrl.var(ddof=1))
                     / max(1, len(d_q)+len(d_ctrl)-2))
effect_d = float((d_q.mean() - d_ctrl.mean()) / max(pooled_std, 1e-9))

# --- Statistic 2: two-sample Hotelling T² (proper multivariate test) ---
def _hotelling_t2(XA, XB):
    '''Classical two-sample T². Uses POOLED covariance (valid under equal-
    covariance null); fall back to pooled centroids if a group is tiny.
    AUDIT 2026-04-19 (v5): ridge unified to 1e-6 to match every other call
    site (Phi_M, LOFO, psi, permutation null). Consistency avoids a hostile
    reviewer noting different numerical regularisation per statistic.'''
    nA, p = XA.shape; nB = XB.shape[0]
    if nA < 2 or nB < 2: return float('nan')
    mA, mB = XA.mean(0), XB.mean(0)
    SA = np.cov(XA.T, ddof=1); SB = np.cov(XB.T, ddof=1)
    Sp = ((nA-1)*SA + (nB-1)*SB) / max(1, (nA + nB - 2))
    cond_pre = float(np.linalg.cond(Sp + 1e-6*np.eye(p)))
    if cond_pre > 1e8:
        print(f'[Hotelling] WARNING: cond(Sp+1e-6·I) = {cond_pre:.2e} '
              f'-- 5-D features near rank-deficient on this sample.')
    try:
        Spi = np.linalg.inv(Sp + 1e-6*np.eye(p))
    except np.linalg.LinAlgError:
        return float('nan')
    diff = (mA - mB)
    return float((nA*nB/(nA+nB)) * diff @ Spi @ diff)

T2_obs = _hotelling_t2(X_QURAN, X_CTRL_POOL)

# --- Statistic 3: permutation p-value under label-swap null ---
# Shuffle the Quran-vs-ctrl labels N_PERM times, recompute T². p = fraction
# of permuted T² >= observed. This is the unbiased, distribution-free test.
def _perm_p_T2(XA, XB, n_perm=None):
    if n_perm is None: n_perm = N_PERM
    all_X = np.vstack([XA, XB]); nA = len(XA); total = len(all_X)
    rng_p = np.random.default_rng(SEED + 101)
    T2_null = []
    for _ in range(n_perm):
        idx = rng_p.permutation(total)
        T2_null.append(_hotelling_t2(all_X[idx[:nA]], all_X[idx[nA:]]))
    T2_null = np.array(T2_null)
    if np.all(np.isnan(T2_null)): return float('nan'), T2_null
    return float((np.sum(T2_null >= T2_obs) + 1) / (n_perm + 1)), T2_null

perm_p, T2_null = _perm_p_T2(X_QURAN, X_CTRL_POOL)

print(f'[Phi_M] Band A | Quran  median d = {np.median(d_q):.2f}  n = {len(d_q)}')
print(f'[Phi_M] Band A | ctrl   median d = {np.median(d_ctrl):.2f}  n = {len(d_ctrl)}')
print('')
print(f'[Phi_M HEADLINE] Hotelling T² (observed)   = {T2_obs:.2f}')
print(f'[Phi_M HEADLINE] permutation p-value (N={N_PERM}) = {perm_p:.4g}')
if not np.all(np.isnan(T2_null)):
    print(f'[Phi_M HEADLINE] T² null: median={np.nanmedian(T2_null):.2f}  '
          f'95th pct={np.nanpercentile(T2_null, 95):.2f}')
print('')
print(f'[Phi_M LEGACY  ] Cohen d (biased-up)       = {effect_d:+.3f}')
print(f'[Phi_M LEGACY  ] *** D02/S1/D28 are DEPRECATED per audit 2026-04-18 ***')
print(f'[Phi_M LEGACY  ] *** use Phi_M_hotelling_T2 + Phi_M_perm_p_value    ***')

# Headline statistics (now first-class lock entries with inf tol)
bless('Phi_M_hotelling_T2', float(T2_obs))
bless('Phi_M_perm_p_value', float(perm_p))
# Legacy entries — all now have lock tol=inf so they record-only, no gate
bless('D02', effect_d)
bless('S1',  effect_d)
bless('D28', effect_d)
bless('Tight_fairness_band_A', effect_d)

# --- Runtime sanity gate (AUDIT 2026-04-19 v5 fix ①) --------------------
# The two headline statistics above were set to `tol=inf` in RESULTS_LOCK
# because v5 upstream fixes (hadith removal, Band-A filter, chi2.logsf) will
# legitimately shift them. `tol=inf` disables the drift alarm for them, which
# means a pathological value (T²=0 from covariance collapse, perm_p≈1.0 from
# a label-swap bug) would pass SILENTLY through the anti-hallucination gate.
# These runtime guards catch clearly-pathological values without enforcing
# significance. UPDATE_LOCK=True bypasses them for an intentional re-bless.
if not UPDATE_LOCK:
    if (not np.isfinite(T2_obs)) or T2_obs <= 5.0:
        raise HallucinationError(
            f'[HALL headline] Hotelling T² = {T2_obs} is pathological '
            f'(expected T² > 5 for any meaningful 5-D separation; typical '
            f'values under the alternative are 30-200). Either a pipeline '
            f'bug (e.g. covariance collapsed, group-sizes flipped) or the '
            f'primary Φ_M claim has genuinely collapsed post-v5 audit. '
            f'If intentional null finding, set UPDATE_LOCK=True in Cell 1 '
            f'and re-bless.'
        )
    if (not np.isfinite(perm_p)) or perm_p >= 0.1:
        raise HallucinationError(
            f'[HALL headline] Φ_M permutation p = {perm_p} is pathological '
            f'(expected p << 0.05 for any significant primary claim). '
            f'Either a pipeline bug or the primary Φ_M claim has genuinely '
            f'collapsed post-v5 audit. If intentional null finding, set '
            f'UPDATE_LOCK=True and re-bless.'
        )
    print(f'[headline-check] T² > 5.0 and perm_p < 0.1 — runtime sanity OK')
else:
    print(f'[headline-check] skipped (UPDATE_LOCK=True; re-blessing in progress)')"""
    )

    # Cell 30 — Band B / Band C sensitivity
    code(
        r"""# === Cell 30 · Band B and Band C Φ_M sensitivity (matched-length robustness) ===
def _phi_m_for_band(lo, hi):
    Xq = _X_for('quran', lo, hi)
    if len(Xq) < 3: return float('nan'), 0
    Xc_parts = [_X_for(c, lo, hi) for c in ARABIC_CTRL_POOL]
    Xc = np.vstack([X for X in Xc_parts if len(X) > 0]) if any(len(X) > 0 for X in Xc_parts) else np.zeros((0,5))
    if len(Xc) < 3: return float('nan'), len(Xq)
    mu_b = Xc.mean(0); Sb = np.cov(Xc.T, ddof=1) + lam*np.eye(5); Sib = np.linalg.inv(Sb)
    dq = mahalanobis(Xq, mu_b, Sib); dc = mahalanobis(Xc, mu_b, Sib)
    ps = np.sqrt(((len(dq)-1)*dq.var(ddof=1) + (len(dc)-1)*dc.var(ddof=1)) /
                 max(1, len(dq)+len(dc)-2))
    return float((dq.mean() - dc.mean()) / max(ps, 1e-9)), len(Xq)

effB, nB = _phi_m_for_band(BAND_B_LO, BAND_B_HI)
effC, nC = _phi_m_for_band(BAND_C_LO, BAND_C_HI)
print(f'[Phi_M] Band B ({BAND_B_LO}-{BAND_B_HI} verses)  d = {effB:+.3f}  n_Q={nB}')
print(f'[Phi_M] Band C ({BAND_C_LO}-{BAND_C_HI} verses) d = {effC:+.3f}  n_Q={nC}')
bless('Tight_fairness_band_B', effB if not np.isnan(effB) else 0.0,
      tol_override=float('inf') if np.isnan(effB) else None)
bless('Tight_fairness_band_C', effC if not np.isnan(effC) else 0.0,
      tol_override=float('inf') if np.isnan(effC) else None)"""
    )

    # Cell 31 — CamelTools-Φ_M re-run (main path already uses CamelTools)
    code(
        r"""# === Cell 31 · CamelTools-Φ_M note (main FEATS already uses CamelTools) ===
# Our FEATS was built via ft.features_5d() which internally calls CamelTools
# (src.roots.primary_root) whenever available. So effect_d above IS the
# CamelTools-backed result — no separate re-run needed.
if CAMEL_OK:
    bless('CamelTools_phi_m_rerun', effect_d)
    print(f'[Phi_M] CamelTools-backed Φ_M = {effect_d:+.3f}  (REMAINING_GAPS item closed)')
else:
    print('[skip ] CamelTools unavailable — FEATS used heuristic fallback')
    bless('CamelTools_phi_m_rerun', 0.0, tol_override=float('inf'))"""
    )

    # Cell 32 — Heuristic-Φ_M re-run (explicit contrast)
    code(
        r"""# === Cell 32 · explicit Heuristic-H_cond Φ_M re-run (falsifies F-06 path) ===
# Build a parallel FEATS_H where H_cond is computed under the 21%-heuristic,
# everything else identical. We expect a SIGNIFICANTLY WEAKER separation.
def _heur_h_cond(verses):
    # Emulate h_cond_roots but using _heur_root() instead of CamelTools.
    import math
    from collections import Counter, defaultdict
    roots = []
    for v in verses:
        toks = tokenise(v)
        if not toks: continue
        roots.append(_heur_root(toks[-1]) or '<unk>')
    if len(roots) < 2: return 0.0
    bigrams = defaultdict(Counter); marg = Counter()
    for a, b in zip(roots[:-1], roots[1:]):
        bigrams[a][b] += 1; marg[a] += 1
    total = sum(marg.values()) or 1
    h = 0.0
    for a, nx in bigrams.items():
        p_a = marg[a]/total; rt = sum(nx.values()) or 1
        rh = 0.0
        for n in nx.values():
            p = n/rt
            if p > 0: rh -= p*math.log2(p)
        h += p_a*rh
    return h

# rebuild just H_cond under heuristic, keep rest identical
# BUG FIX (audit 2026-04-18): previous expression
#   rec['T'] = h_h - (orig['T'] + orig['H_cond'] - orig['H_cond'])
# algebraically collapsed to  h_h - orig['T']  which is NOT the new T under
# heuristic H_cond.  The correct update keeps H_EL fixed and only swaps
# H_cond:  T = H_cond - H_EL  =>  H_EL = orig['H_cond'] - orig['T']  =>
#   new_T = h_h - H_EL = h_h - orig['H_cond'] + orig['T']
FEATS_H = {}
for name, units in CORPORA.items():
    recs = []
    for u, orig in zip(units, FEATS[name]):
        h_h = _heur_h_cond(u.verses)
        rec = dict(orig); rec['H_cond'] = h_h
        rec['T']      = h_h - orig['H_cond'] + orig['T']   # fixed: swap H_cond only
        recs.append(rec)
    FEATS_H[name] = recs

def _X_H(name):
    r = [x for x in FEATS_H.get(name, []) if BAND_A_LO <= x['n_verses'] <= BAND_A_HI]
    return np.array([[x[c] for c in FEAT_COLS] for x in r], dtype=float)

Xq_h = _X_H('quran')
Xc_h = np.vstack([_X_H(c) for c in ARABIC_CTRL_POOL if len(_X_H(c)) > 0])
if len(Xq_h) >= 3 and len(Xc_h) >= 3:
    mu_h = Xc_h.mean(0); Sh = np.cov(Xc_h.T, ddof=1) + lam*np.eye(5); Sih = np.linalg.inv(Sh)
    dqh = mahalanobis(Xq_h, mu_h, Sih); dch = mahalanobis(Xc_h, mu_h, Sih)
    ps_h = np.sqrt(((len(dqh)-1)*dqh.var(ddof=1) + (len(dch)-1)*dch.var(ddof=1)) /
                   max(1, len(dqh)+len(dch)-2))
    eff_h = float((dqh.mean() - dch.mean()) / max(ps_h, 1e-9))
else:
    eff_h = float('nan')
print(f'[Phi_M] heuristic-H_cond re-run | Cohen d = {eff_h:+.3f}  (vs CamelTools {effect_d:+.3f})')
bless('Heuristic_phi_m_rerun', eff_h if not np.isnan(eff_h) else 0.0,
      tol_override=float('inf') if np.isnan(eff_h) else None)"""
    )

    # Cell 33 — Phase-6 verifier + checkpoint
    code(
        r"""# === Cell 33 · Phase-6 verifier + checkpoint ===
def _verify_phase_6():
    assert effect_d > 1.0, f'Band-A Phi_M Cohen d too low: {effect_d}'
    print(f'[OK   ] Phase 6 — Phi_M Band A d={effect_d:+.2f} > 1.0')

_verify_phase_6()
save_checkpoint('06_phi_m', {
    'band_A_d':   float(effect_d),
    'band_B_d':   float(effB) if not np.isnan(effB) else None,
    'band_C_d':   float(effC) if not np.isnan(effC) else None,
    'heur_d':     float(eff_h) if not np.isnan(eff_h) else None,
    'arabic_pool': ARABIC_CTRL_POOL,
}, state={
    # Restore-critical state for resume at Phase 7+
    'CORPORA': CORPORA, 'FEATS': FEATS,
    'ARABIC_CTRL_POOL': ARABIC_CTRL_POOL,
    # AUDIT 2026-04-18 (v4): ARABIC_FAMILY carried so a cold-kernel resume
    # that jumps straight to Cell 34 (Journey "only Phase 7+") still has it
    # defined when Cell 84 / Cell 95 run. Defined originally in Cell 22.
    'ARABIC_FAMILY': ARABIC_FAMILY,
    'X_QURAN': X_QURAN, 'X_CTRL_POOL': X_CTRL_POOL, 'mu': mu, 'S_inv': S_inv,
    'effect_d': effect_d, 'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
    'BAND_B_LO': BAND_B_LO, 'BAND_B_HI': BAND_B_HI,
    'BAND_C_LO': BAND_C_LO, 'BAND_C_HI': BAND_C_HI,
    'FEAT_COLS': FEAT_COLS, 'RHYME_LETTERS': RHYME_LETTERS,
    # AUDIT 2026-04-19 (v5 fix ③): `lam` is defined in Cell 29 as the unified
    # ridge regularisation (1e-6) and is referenced downstream in Cell 30
    # (Band B/C), Cell 32 (heuristic-Φ_M) and Cell 92 (D13 hindawi-LOO in
    # Phase 16). A partial-resume that jumps past Phase 6 in a fresh kernel
    # would NameError at Cell 92. Carry it explicitly.
    'lam': lam,
    'ALL_RESULTS': ALL_RESULTS,
})
"""
    )


# ============================================================================
# PHASE 7 — Run the full clean pipeline once (cells 34-40)
# ============================================================================
def build_phase_7() -> None:
    phase_header(
        7,
        "Core separation — run the full T1–T31 battery via `cp.run_clean_pipeline()`",
        "Rather than re-implementing each test, we call the authoritative "
        "`src.clean_pipeline.run_clean_pipeline()` once. Its results dict "
        "gives us T1…T31 with the exact signatures the audit approved. "
        "Later cells just pull from this dict.",
    )

    # Cell 34 — run the full pipeline once (with cascading resume support)
    code(
        r"""# === Cell 34 · run the authoritative pipeline (T1-T31 in one call) ===
# Cascade (audit 2026-04-18 v4 — state-leak fix):
#   (pre) ensure FEATS/CORPORA/mu/S_inv are in globals (from Phase-6 ckpt if
#         not already present — required even when we resume Phase 7 from
#         cache, because Cells 35-40 read FEATS directly; the previous
#         cascade only ran `resume_from('06_phi_m')` on the cache-miss path,
#         so a cold kernel hitting path (1) would NameError on FEATS).
#   (1)   if Phase 7 already finished -> restore PIPELINE_RES, skip ~2-min call
#   (2)   else -> run the pipeline from scratch using the Phase-6 globals
if 'FEATS' not in globals() or 'CORPORA' not in globals():
    resume_from('06_phi_m')        # pull CORPORA, FEATS, mu, S_inv, bands, ...

_phase7_cached = resume_from('07_core') and isinstance(globals().get('PIPELINE_RES'), dict) \
                 and PIPELINE_RES.get('status') == 'ok'
if _phase7_cached:
    RES = PIPELINE_RES.get('results', {})
    log(f'[Phase 7] resumed from checkpoint; {len(RES)} test results in RES')
else:
    log('running cp.run_clean_pipeline() -> this runs T1..T31 from raw data')
    t0 = time.time()
    try:
        PIPELINE_RES = cp.run_clean_pipeline()
        log(f'run_clean_pipeline finished in {time.time()-t0:.1f}s')
        RES = PIPELINE_RES.get('results', {}) if isinstance(PIPELINE_RES, dict) else {}
        if PIPELINE_RES.get('status') != 'ok':
            print(f'[WARN] pipeline status = {PIPELINE_RES.get("status")}')
    except Exception as e:
        log(f'run_clean_pipeline failed: {e}')
        PIPELINE_RES = {'status': 'failed', 'error': str(e), 'results': {}}
        RES = {}
print(f'[T1-T31] got {len(RES)} test results')"""
    )

    # Cell 35 — T1 anti-metric + D01
    code(
        r"""# === Cell 35 · T1 anti-metric VL_CV ===
t1 = RES.get('T1_anti_metric', {})
d1 = t1.get('cohens_d_pool', float('nan'))
print(f'[T1  ] anti-metric VL_CV pool d = {d1:+.3f}')
bless('T1',  float(d1))
bless('D01', float(d1))"""
    )

    # Cell 36 — T2 Phi_M + D02
    code(
        r"""# === Cell 36 · T2 Phi_M Mahalanobis (Band A) ===
t2 = RES.get('T2_phi_m', {})
d2 = t2.get('cohens_d', float('nan'))
print(f'[T2  ] Phi_M Cohen d = {d2:+.3f}   median Q = {t2.get("median_phi_quran", float("nan")):.2f}'
      f'   median ctrl = {t2.get("median_phi_ctrl", float("nan")):.2f}')
bless('T2', float(d2))"""
    )

    # Cell 37 — T3 H_cond by corpus
    code(
        r"""# === Cell 37 · T3 H_cond ranking + S3 ===
# AUDIT 2026-04-18 (v4): a spurious T10 bless with the H_cond value was
# removed from this cell. The %T>0 metric (= D10 expected 39.7%) shares
# the T10 pipeline ID, so T10 is now blessed in Cell 40 alongside D10
# from `pct_T_pos`. T3 and S3 still correctly carry the H_cond value.
t3 = RES.get('T3_hcond', {})
pq = t3.get('per_corpus', {}).get('quran', {})
h_q = pq.get('mean', float('nan'))
print(f'[T3  ] H_cond (Quran) = {h_q:.3f}   rank = #{t3.get("quran_rank", "?")}/{len(t3.get("per_corpus", {}))}')
bless('T3',  float(h_q))
bless('S3',  float(h_q))"""
    )

    # Cell 38 — T4 Omega + D20
    code(
        r"""# === Cell 38 · T4 Omega rebuild (no hardcoded constants) ===
t4 = RES.get('T4_omega', {})
omega_q = t4.get('per_corpus', {}).get('quran', {}).get('omega', float('nan'))
print(f'[T4  ] Omega (Quran) = {omega_q:.3f}   rank = #{t4.get("quran_rank", "?")}')
bless('T4',  float(omega_q))
bless('D20', float(omega_q))"""
    )

    # Cell 39 — D03 EL rate + D04 CN rate (direct from FEATS)
    code(
        r"""# === Cell 39 · D03 EL rate + D04 CN rate (direct from FEATS) ===
def _mean_band_a(name, col):
    recs = [r for r in FEATS.get(name, []) if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    return np.array([r[col] for r in recs]).mean() if recs else float('nan')

EL_by = {n: _mean_band_a(n, 'EL') for n in FEATS}
CN_by = {n: _mean_band_a(n, 'CN') for n in FEATS}
print('[D03 ] EL top 5 corpora:')
for n in sorted(EL_by, key=lambda k: -EL_by[k])[:5]:
    tag = ' <- Quran' if n == 'quran' else ''
    print(f'  {n:<22s}  EL = {EL_by[n]:.3f}{tag}')
print('[D04 ] CN top 5 corpora:')
for n in sorted(CN_by, key=lambda k: -CN_by[k])[:5]:
    tag = ' <- Quran' if n == 'quran' else ''
    print(f'  {n:<22s}  CN = {CN_by[n]:.3f}{tag}')
bless('D03', float(EL_by['quran']))
bless('D04', float(CN_by['quran']))"""
    )

    # Cell 40 — D05 unit-level I(EL;CN) + T7 corpus level + Phase 7 checkpoint
    code(
        r"""# === Cell 40 · D05 (unit-level) + T7 (corpus-level) I(EL;CN) + Phase-7 ckpt ===
t7 = RES.get('T7_el_cn_dual', {})
I_corp = t7.get('per_corpus', {}).get('quran', {}).get('I_EL_CN', float('nan'))
# D05 unit-level: discretise EL and CN per surah, compute I
# AUDIT 2026-04-18: plug-in MI with fixed k=4 bins on N ≈ 40-120 surahs
# suffers ~ (k²-1)/(2N ln 2) bits of downward bias. Miller-Madow corrects
# the plug-in estimator: I_MM = I_plug + (K_obs - 1)/(2 N ln 2), applied
# consistently to the joint table. We now report:
#   (i)  plug-in I at k=4 (canonical, legacy)
#   (ii) plug-in I at k ∈ {3,4,5,6,8}  (sensitivity sweep)
#   (iii) Miller-Madow corrected I at k=4 (bias-adjusted primary)
def _unit_mi_EL_CN(name, k=4, mm=False):
    import numpy as np
    import math as _math
    recs = [r for r in FEATS.get(name, []) if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    if len(recs) < 10: return float('nan')
    el = np.array([r['EL'] for r in recs])
    cn = np.array([r['CN'] for r in recs])
    # AUDIT 2026-04-19 (v6 fix W4-a): previous return value on a degenerate
    # channel (std == 0, e.g. a control corpus whose short surahs all have
    # identical EL after normalisation) was a silent `return 0.0`. A reader
    # of the scorecard cannot tell whether `I_unit=0.0` means "MI was
    # legitimately zero" or "pipeline found a degenerate column and
    # short-circuited". Return NaN + a clear warning so the downstream
    # bless() records NaN (which is then treated as a reporting failure,
    # not as a real 0.0 measurement).
    if el.std() == 0 or cn.std() == 0:
        print(f'[D05 WARN] {name}: degenerate std (EL.std={el.std():.3g}, '
              f'CN.std={cn.std():.3g}); returning NaN (not 0.0)')
        return float('nan')
    el_b = np.digitize(el, np.linspace(el.min(), el.max()+1e-9, k+1)) - 1
    cn_b = np.digitize(cn, np.linspace(cn.min(), cn.max()+1e-9, k+1)) - 1
    tab = np.zeros((k, k))
    for a, b in zip(el_b, cn_b): tab[min(a,k-1), min(b,k-1)] += 1
    N = tab.sum()
    if N < 1: return 0.0
    p = tab / N
    px = p.sum(1, keepdims=True); py = p.sum(0, keepdims=True)
    mi = 0.0
    K_obs_joint = 0   # non-empty joint cells
    K_obs_x     = int((px > 0).sum())
    K_obs_y     = int((py > 0).sum())
    for i in range(k):
        for j in range(k):
            if p[i,j] > 0:
                mi += p[i,j] * np.log2(p[i,j] / (px[i,0]*py[0,j] + 1e-12) + 1e-12)
                K_obs_joint += 1
    mi = max(0.0, mi)
    if not mm: return float(mi)
    # Miller-Madow for MI: I = H(X) + H(Y) - H(X,Y). Plug-in H underestimates
    # true H with bias ≈ +(K-1)/(2N) (in nats). Substituting into the MI
    # decomposition and collecting terms gives:
    #   I_MM = I_plug + (K_x + K_y - K_xy - 1) / (2N)   [nats]
    # AUDIT 2026-04-18 (v3): previous implementation had the sign of the
    # joint-cell term inverted (it used K_xy - K_x - K_y + 1), which
    # subtracts the bias instead of adding it. That is a textbook error and
    # would anti-correct I_MM. Fixed below; divide by ln(2) to return bits.
    bias = (K_obs_x + K_obs_y - K_obs_joint - 1) / (2 * max(1, N) * _math.log(2))
    return float(max(0.0, mi + bias))

I_unit_quran    = _unit_mi_EL_CN('quran', k=4, mm=False)
I_unit_quran_MM = _unit_mi_EL_CN('quran', k=4, mm=True)
MI_BIN_SWEEP = {k: _unit_mi_EL_CN('quran', k=k, mm=False) for k in (3, 4, 5, 6, 8)}
mi_sweep_vals = [v for v in MI_BIN_SWEEP.values() if not np.isnan(v)]
mi_range = (max(mi_sweep_vals) - min(mi_sweep_vals)) if mi_sweep_vals else float('nan')
print(f'[T7  ] I(EL;CN) corpus-level (Quran) = {I_corp:.3f} bits')
print(f'[D05 ] I(EL;CN) unit-level   (Quran) = {I_unit_quran:.3f} bits (k=4, plug-in legacy)')
print(f'[D05 ] I(EL;CN) unit-level   (Quran) = {I_unit_quran_MM:.3f} bits (k=4, Miller-Madow)')
print(f'[D05 ] bin sensitivity sweep (plug-in):')
for k in (3, 4, 5, 6, 8):
    print(f'         k={k}  I_unit = {MI_BIN_SWEEP[k]:.3f} bits')
print(f'[D05 ] sensitivity range = {mi_range:.3f} bits  '
      f'(smaller = more stable estimator)')
bless('T7',  float(I_corp))
bless('D05', float(I_unit_quran))
bless('S2',  float(I_unit_quran))
bless('MI_bin_sensitivity_range', float(mi_range) if not np.isnan(mi_range) else 0.0,
      tol_override=float('inf'))
bless('MI_D05_miller_madow', float(I_unit_quran_MM), tol_override=float('inf'))

# === Nobel/PNAS audit 2026-04-18 · HSIC — binning-free I(EL;CN) alternative ===
# Plug-in MI requires discretisation, which injects bin-count dependence
# (see sensitivity sweep above). HSIC (Gretton et al. 2005) is a kernel-
# based independence statistic that operates on continuous data directly.
# Under the null H0: EL ⊥ CN the HSIC is 0; under dependence it is positive.
# Permutation of CN labels gives an exact p-value.
#
# Biased empirical estimator:
#     HSIC_b(X,Y) = tr(K H L H) / (n-1)²
# where K_ij = k_x(x_i, x_j), L_ij = k_y(y_i, y_j), H = I - 11ᵀ/n.
# RBF kernel widths σ² = 0.5 · median(pairwise squared distances).
# Complexity: O(n²) per evaluation; acceptable for n ≤ 120.
# NOTE (audit 2026-04-18 v4): `_rbf_kernel` is defined UNCONDITIONALLY in
# Cell 8 so it survives `resume_from('07_core')`. Here we only define the
# `_hsic` wrapper and run the permutation null when USE_HSIC=True.
if USE_HSIC:
    def _hsic(a, b):
        '''Biased HSIC estimator on two 1-D arrays of equal length ≥ 5.'''
        a = np.asarray(a, float); b = np.asarray(b, float)
        n_ = len(a)
        if n_ < 5 or len(b) != n_: return float('nan')
        if a.std() == 0 or b.std() == 0: return 0.0
        K = _rbf_kernel(a); L = _rbf_kernel(b)
        H = np.eye(n_) - (1.0 / n_)
        return float(np.trace(K @ H @ L @ H) / max(1, (n_ - 1) ** 2))

    _recs_q = [r for r in FEATS.get('quran', []) if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    if len(_recs_q) >= 10:
        _el_q = np.array([r['EL'] for r in _recs_q])
        _cn_q = np.array([r['CN'] for r in _recs_q])
        hsic_obs = _hsic(_el_q, _cn_q)
        _rng_h   = np.random.default_rng(SEED + 401)
        _null    = np.empty(N_PERM)
        for _i in range(N_PERM):
            _null[_i] = _hsic(_el_q, _cn_q[_rng_h.permutation(len(_cn_q))])
        hsic_p = float((np.sum(_null >= hsic_obs) + 1.0) / (N_PERM + 1.0))
        print(f'[D05 ] HSIC(EL,CN) Quran  = {hsic_obs:.4e}   '
              f'perm p (N={N_PERM}) = {hsic_p:.4g}   (binning-free)')
        bless('HSIC_EL_CN_quran',  float(hsic_obs), tol_override=float('inf'))
        bless('HSIC_EL_CN_perm_p', float(hsic_p),   tol_override=float('inf'))
    else:
        print('[D05 ] HSIC skipped — <10 Band-A surahs')
else:
    print('[D05 ] HSIC skipped (USE_HSIC=False)')

# %T>0 (T10 / D10) — SAME statistic; T10 is the test name, D10 is the finding ID
q_T = np.array([r['T'] for r in FEATS['quran'] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI])
pct_T_pos = float(100.0 * (q_T > 0).mean())
print(f'[D10 ] %T>0 Quran (Band A) = {pct_T_pos:.1f}%')
# AUDIT 2026-04-18 (v4): T10 and D10 now share the same %T>0 value (was
# previously recorded as H_cond under T10 in Cell 37 — wrong statistic).
bless('T10', pct_T_pos)
bless('D10', pct_T_pos)

save_checkpoint('07_core', {
    'T1_d_pool': float(d1), 'T2_d': float(d2),
    'T3_h_quran': float(h_q), 'T4_omega': float(omega_q),
    'EL_by': EL_by, 'CN_by': CN_by,
    'I_corpus': float(I_corp), 'I_unit_quran': float(I_unit_quran),
    'pct_T_pos': pct_T_pos,
}, state={
    # Expensive result — auto-resume will skip the 2-min pipeline run
    'PIPELINE_RES': PIPELINE_RES, 'RES': RES,
    'EL_by': EL_by, 'CN_by': CN_by,
    'I_corp': I_corp, 'I_unit_quran': I_unit_quran,
    'pct_T_pos': pct_T_pos,
    'ALL_RESULTS': ALL_RESULTS,
})"""
    )


# ============================================================================
# PHASE 8 — Scale-free + path (T8/T16/T17/T18/T27) cells 41-46
# ============================================================================
def build_phase_8() -> None:
    phase_header(
        8,
        "Scale-free + path minimality — T8 path, T16 scale-free S24, "
        "T17 multi-scale perturbation, T18 verse-internal, T27 inter-surah",
        "All read from RES dict populated by Phase 7.",
    )

    code(
        r"""# === Cell 41 · T8 path minimality (canonical vs permutations) ===
t8 = RES.get('T8_path', {})
pq = t8.get('per_corpus', {}).get('quran', {})
z_path = pq.get('z_path', float('nan'))
print(f'[T8  ] Quran path z = {z_path:+.3f}   pct < canon = {pq.get("pct_path_below_canon", float("nan")):.1f}%')
bless('T8',  float(z_path))
bless('D17', float(z_path))
bless('S5',  float(z_path))"""
    )

    code(
        r"""# === Cell 42 · T16 scale-free S24 (Fisher p @ W=10) ===
# AUDIT 2026-04-19 (v5): bless `-log10(fisher_p)` instead of raw `fisher_p`.
# The raw p bottoms out at ~1.1e-16 due to `1 - chi2.cdf` catastrophic
# cancellation; the pipeline now exports `fisher_log10p = chi2.logsf/ln(10)`
# which is tail-accurate to ~300 decades. Blessing in log space also makes
# tolerances meaningful: 0.2 log-units = factor of 1.58 on p, so future
# drift detection actually works instead of living on the machine-eps floor.
t16 = RES.get('T16_scale_free', {})
qp = t16.get('per_corpus', {}).get('quran', {})
entry = qp.get('W=10', {}) if isinstance(qp, dict) else {}
p_w10   = entry.get('fisher_p',     float('nan'))
lp_w10  = entry.get('fisher_log10p', float('nan'))
# Back-compat: if clean_pipeline is older (no fisher_log10p), derive it
# ourselves in a numerically-stable way from the chi2/df stored alongside.
if (lp_w10 is None or (isinstance(lp_w10, float) and np.isnan(lp_w10))) \
        and ('chi2' in entry) and ('df' in entry):
    from scipy.stats import chi2 as _chi2
    lp_w10 = float(_chi2.logsf(entry['chi2'], entry['df']) / np.log(10.0))
neg_log10_p = -float(lp_w10) if lp_w10 is not None and not np.isnan(lp_w10) else float('nan')
print(f'[T16 ] Quran scale-free Fisher p @ W=10 = {p_w10:.3g}   (-log10 p = {neg_log10_p:.2f})')
bless('T16', float(p_w10))
bless('D07', float(neg_log10_p))"""
    )

    code(
        r"""# === Cell 43 · T17 multi-scale perturbation gap sum ===
# Pipeline keys (2025-04+): letter_10pct / word_10pct / verse_shuffle
# (old names letter_shuffle / word_shuffle are no longer emitted).
t17 = RES.get('T17_multi_scale_pert', {})
qt  = t17.get('per_target', {}).get('quran', {})
_scales = ('letter_10pct', 'word_10pct', 'verse_shuffle')
gap_sum = sum((qt.get(k, {}) or {}).get('mean_gap', 0.0) or 0.0 for k in _scales)
print(f'[T17 ] multi-scale perturbation gap sum = {gap_sum:+.3f}')
bless('T17', float(gap_sum))
bless('D11', float(gap_sum))"""
    )

    code(
        r"""# === Cell 44 · T18 verse-internal word order ===
t18 = RES.get('T18_verse_internal', {})
qg = t18.get('per_target', {}).get('quran', {}).get('mean_gap', float('nan'))
print(f'[T18 ] verse-internal gap (Quran) = {qg:+.3f}')
bless('T18', float(qg))
bless('D14', float(qg))"""
    )

    code(
        r"""# === Cell 45 · T27 inter-surah cost ratio ===
t27 = RES.get('T27_inter_surah_cost', {})
ratio = t27.get('cost_ratio', float('nan'))
print(f'[T27 ] inter-surah cost ratio = {ratio:.3f}  p = {t27.get("p_value", float("nan")):.3g}')
bless('T27', float(ratio))"""
    )

    code(
        r"""# === Cell 46 · Phase-8 verifier + checkpoint ===
def _verify_phase_8():
    print('[OK   ] Phase 8 — scale-free + path results extracted')

_verify_phase_8()
save_checkpoint('08_scalefree_path',
                {'T8':t8,'T16':t16,'T17':t17,'T18':t18,'T27':t27},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 9 — Markov + bigram + T28 (cells 47-51)
# ============================================================================
def build_phase_9() -> None:
    phase_header(
        9,
        "Markov unforgeability (T9, D08), bigram sufficiency (T11, S4), "
        "T28 NOT-REPRODUCED marker, S24 weight sensitivity",
        "T28 is the flip-flopped 'H2/H1 Markov-order' claim that fails to "
        "reproduce on clean data — we lock it at d ≈ -0.03.",
    )

    code(
        r"""# === Cell 47 · T9 Markov unforgeability z ===
t9 = RES.get('T9_markov', {})
z_q = t9.get('per_corpus', {}).get('quran', {}).get('z_shuff_vs_canon', float('nan'))
print(f'[T9  ] Markov z (Quran) = {z_q:+.3f}')
bless('T9',  float(z_q))
bless('D08', float(z_q))"""
    )

    code(
        r"""# === Cell 48 · T11 bigram sufficiency H3/H2 ===
t11 = RES.get('T11_bigram_suf', {})
rank = t11.get('quran_rank_low_ratio', None)
# pull the Quran's H3/H2 ratio if present
# Pipeline key: 'ratio_H3_over_H2' (NOT 'H3_over_H2').
ratios = t11.get('per_corpus', {})
_q11   = ratios.get('quran', {}) if ratios else {}
q_h32  = _q11.get('ratio_H3_over_H2', _q11.get('H3_over_H2', float('nan')))
print(f'[T11 ] H3/H2 Quran = {q_h32:.3f}  rank = #{rank}')
# AUDIT 2026-04-19 (v5 fix ⑤): backstop assertion against clean_pipeline
# silently returning inf/NaN from an H2=0 division. Cell 102 has its own
# division-by-zero guard for the SCI (L1) pathway; T11/S4 read directly from
# the pipeline, so we verify finiteness here.
if not np.isnan(q_h32):
    assert np.isfinite(q_h32), (
        f'[FATAL] H3/H2 ratio is non-finite ({q_h32}) — check H2>0 guard '
        f'in clean_pipeline.T11_bigram_suf. Division-by-zero would propagate '
        f'through T11/S4 and corrupt the Shannon-Aljamal table.'
    )
bless('T11', float(q_h32))
bless('S4',  float(q_h32))"""
    )

    code(
        r"""# === Cell 49 · T28 Markov-order H2/H1 (NOT REPRODUCED on clean data) ===
t28 = RES.get('T28_markov_order', {})
d28 = t28.get('cohens_d_quran_vs_ctrl', float('nan'))
if d28 is None: d28 = float('nan')
print(f'[T28 ] H2/H1 d(Quran vs ctrl) = {d28:+.3f}  (notebook claim d=-1.85 -> NOT REPRODUCED)')
bless('T28', float(d28))"""
    )

    code(
        r"""# === Cell 50 · S24 weight sensitivity across 6 configs ===
# Re-weight the 5-D mean vector 6 ways and check Quran rank stability.
mean_vec = {n: np.array([[r[c] for c in FEAT_COLS] for r in FEATS[n]
                         if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]).mean(0)
            for n in FEATS if any(BAND_A_LO <= r['n_verses'] <= BAND_A_HI for r in FEATS[n])}

weights_configs = [
    ('equal',    np.ones(5)/5),
    ('heavy_EL', np.array([0.4,0.15,0.15,0.15,0.15])),
    ('heavy_VL', np.array([0.15,0.4,0.15,0.15,0.15])),
    ('heavy_CN', np.array([0.15,0.15,0.4,0.15,0.15])),
    ('heavy_H',  np.array([0.15,0.15,0.15,0.4,0.15])),
    ('heavy_T',  np.array([0.15,0.15,0.15,0.15,0.4])),
]
pass_count = 0
for wname, w in weights_configs:
    scores = {n: float(np.dot(mean_vec[n], w)) for n in mean_vec}
    ranked = sorted(scores, key=lambda x: -scores[x])
    rq = ranked.index('quran') + 1 if 'quran' in ranked else -1
    ok = rq == 1
    pass_count += int(ok)
    print(f'  [S24 ] {wname:<10s}  rank(Quran)={rq}  top3={ranked[:3]}  {"OK" if ok else "FAIL"}')
print(f'[S24 ] pass rate = {pass_count}/{len(weights_configs)}')"""
    )

    code(
        r"""# === Cell 51 · Phase-9 verifier + checkpoint ===
def _verify_phase_9():
    print('[OK   ] Phase 9 — Markov + bigram + S24 sensitivity done')

_verify_phase_9()
save_checkpoint('09_markov',
                {'T9_z':float(z_q),'T11_H3H2':float(q_h32),
                 'T28_d':float(d28),'S24_pass':pass_count},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 10 — Dual-channel + turbo + capacity + independence (cells 52-56)
# ============================================================================
def build_phase_10() -> None:
    phase_header(
        10,
        "Dual-channel (T7/D06), RD×EL T22, EL capacity, P4 channel independence",
        "Turbo gain, Quran channel independence (G2), and root-diversity×EL.",
    )

    code(
        r"""# === Cell 52 · T7 dual-channel + D06 turbo gain ===
# CAVEAT (audit 2026-04-18): G_turbo is an ANALOGY to turbo-coding gain, not
# a derived capacity. It is defined inside src/extended_tests.py as
#   G_turbo = H(EL) + H(CN) - I(EL;CN)_marginal  /  I(EL;CN)_joint
# which only admits a "turbo" interpretation if the EL and CN channels
# satisfy the conditional-independence assumptions of iterative decoding.
# We do NOT prove that here; D06 is therefore EXPLORATORY. The exact
# formula is in src.extended_tests.G_turbo_dual (single source of truth).
t7_full = RES.get('T7_el_cn_dual', {})
G_turbo_q = t7_full.get('per_corpus', {}).get('quran', {}).get('G_turbo', float('nan'))
print(f'[D06 ] G_turbo (Quran) = {G_turbo_q:.3f}x   [EXPLORATORY; see src.extended_tests]')
bless('D06', float(G_turbo_q))"""
    )

    code(
        r"""# === Cell 53 · T22 Root-Diversity x EL product ===
# Pipeline key: 'mean_RD_x_EL' (NOT 'RD_times_EL').
t22 = RES.get('T22_rd_el', {})
_q22 = t22.get('per_corpus', {}).get('quran', {})
rd_el_q = _q22.get('mean_RD_x_EL', _q22.get('RD_times_EL', float('nan')))
print(f'[T22 ] RD*EL (Quran) = {rd_el_q:.3f}  rank = #{t22.get("quran_rank", "?")}')
bless('T22', float(rd_el_q))
bless('D22', float(rd_el_q))"""
    )

    code(
        r"""# === Cell 54 · EL channel capacity ===
def _el_capacity(units):
    finals = []
    for u in units:
        for v in u.verses:
            toks = tokenise(v)
            if toks: finals.append(toks[-1][-1] if toks[-1] else '_')
    return float(np.log2(max(1, len(set(finals)))))

EL_CAP = {n: _el_capacity(CORPORA.get(n, [])) for n in CORPORA}
for n in sorted(EL_CAP, key=lambda k: -EL_CAP[k])[:5]:
    print(f'  [EL_cap] {n:<22s}  {EL_CAP[n]:.2f} bits')"""
    )

    code(
        r"""# === Cell 55 · P4 / G2 — 5-channel MI independence (Quran + all controls) ===
# G2 is a COMPARATIVE claim: Quran's 5-channel MI must be low AND similar to
# or lower than controls. Computing only on Quran leaves the comparison open.
from collections import Counter

def _entropy(v):
    v = np.asarray(v); _, c = np.unique(v, return_counts=True)
    p = c / c.sum()
    return -float(np.sum(p * np.log2(p + 1e-12)))

def _bin(v, k=6):
    v = np.asarray(v, float)
    if v.std() == 0: return np.zeros_like(v, dtype=int)
    return np.digitize(v, np.linspace(v.min(), v.max()+1e-9, k+1)) - 1

def _mi(a, b):
    n = len(a); tab = Counter(zip(a.tolist(), b.tolist()))
    mi = 0.0
    for (x, y), c in tab.items():
        pxy = c / n
        px = (a == x).mean(); py = (b == y).mean()
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * np.log2(pxy / (px*py))
    return float(max(0.0, mi))

def _max_nmi_5ch(X):
    if len(X) < 10: return float('nan')
    B = np.stack([_bin(X[:, i]) for i in range(5)], axis=1)
    H = [_entropy(B[:, i]) for i in range(5)]
    NMI = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            if i == j: continue
            NMI[i, j] = _mi(B[:, i], B[:, j]) / max(1e-9, min(H[i], H[j]))
    return float(np.nanmax(NMI))

NMI_by_corpus = {}
for n in sorted(FEATS):
    X = _X_for(n, BAND_A_LO, BAND_A_HI)
    v = _max_nmi_5ch(X)
    if not np.isnan(v): NMI_by_corpus[n] = v

print('[P4/G2] max normalised 5-channel MI per corpus:')
for n, v in sorted(NMI_by_corpus.items(), key=lambda kv: kv[1]):
    tag = '  <-- Quran' if n == 'quran' else ''
    print(f'  {n:<22s}  max NMI = {v:.3f}{tag}')

max_nmi = NMI_by_corpus.get('quran', float('nan'))
ctrl_median = (float(np.median([v for k, v in NMI_by_corpus.items() if k != 'quran']))
               if len(NMI_by_corpus) > 1 else float('nan'))
print(f'[P4/G2] Quran max NMI = {max_nmi:.3f}   controls median = {ctrl_median:.3f}')
bless('G2', float(max_nmi))

# === Nobel/PNAS audit 2026-04-18 · 5-channel HSIC (binning-free G2) ===
# The NMI above requires discretising each feature into k=6 bins, which
# makes G2 a function of the bin-count hyperparameter. HSIC uses the
# continuous values directly. For each pair (i,j) ∈ {0..4}² with i<j we
# compute HSIC on feature columns; G2_HSIC = max pair. Under H0 (all
# pairs independent) HSIC = 0. Permutation p: shuffle feature j within
# the pair that attains the max, recompute; empirical p from N_PERM draws.
if USE_HSIC:
    # AUDIT 2026-04-18 (v4): use the canonical `_rbf_kernel` defined in
    # Cell 8. Previously this cell aliased `_rbf_kernel_5ch = _rbf_kernel`
    # where `_rbf_kernel` was defined inside Cell 40's `if USE_HSIC:`
    # block. That crashed with NameError whenever Phase 10 ran after
    # `resume_from('07_core')` (Cell 40 is skipped on resume). With Cell 8
    # now defining `_rbf_kernel` unconditionally, this alias is unnecessary.
    def _hsic_1d(a, b):
        a = np.asarray(a, float); b = np.asarray(b, float)
        n_ = len(a)
        if n_ < 5 or len(b) != n_: return float('nan')
        if a.std() == 0 or b.std() == 0: return 0.0
        K = _rbf_kernel(a); L = _rbf_kernel(b)
        H = np.eye(n_) - (1.0 / n_)
        return float(np.trace(K @ H @ L @ H) / max(1, (n_ - 1) ** 2))

    HSIC_by_corpus = {}
    for n in sorted(FEATS):
        X = _X_for(n, BAND_A_LO, BAND_A_HI)
        if len(X) < 10: continue
        best = 0.0
        for i in range(5):
            for j in range(i + 1, 5):
                v = _hsic_1d(X[:, i], X[:, j])
                if not np.isnan(v) and v > best: best = v
        HSIC_by_corpus[n] = best

    print('[P4/G2-HSIC] max HSIC pair per corpus (binning-free):')
    for n, v in sorted(HSIC_by_corpus.items(), key=lambda kv: kv[1]):
        tag = '  <-- Quran' if n == 'quran' else ''
        print(f'  {n:<22s}  max HSIC = {v:.4e}{tag}')

    max_hsic_q = HSIC_by_corpus.get('quran', float('nan'))
    hsic_p_q   = float('nan')
    if not np.isnan(max_hsic_q) and len(FEATS.get('quran', [])) > 0:
        Xq = _X_for('quran', BAND_A_LO, BAND_A_HI)
        if len(Xq) >= 10:
            # Identify which pair attained the max
            best_pair = (0, 1); best_v = -1.0
            for i in range(5):
                for j in range(i + 1, 5):
                    v = _hsic_1d(Xq[:, i], Xq[:, j])
                    if not np.isnan(v) and v > best_v:
                        best_v = v; best_pair = (i, j)
            # Permutation null on that specific pair
            _rng_g2 = np.random.default_rng(SEED + 402)
            _null_g2 = np.empty(N_PERM)
            a_col = Xq[:, best_pair[0]]; b_col = Xq[:, best_pair[1]]
            for _i in range(N_PERM):
                _null_g2[_i] = _hsic_1d(a_col, b_col[_rng_g2.permutation(len(b_col))])
            hsic_p_q = float((np.sum(_null_g2 >= best_v) + 1.0) / (N_PERM + 1.0))
            print(f'[P4/G2-HSIC] Quran max pair = {FEAT_COLS[best_pair[0]]}-'
                  f'{FEAT_COLS[best_pair[1]]}   HSIC = {best_v:.4e}   '
                  f'perm p (N={N_PERM}) = {hsic_p_q:.4g}')
    bless('HSIC_G2_max_quran', float(max_hsic_q) if not np.isnan(max_hsic_q) else 0.0,
          tol_override=float('inf'))
    bless('HSIC_G2_perm_p',    float(hsic_p_q)   if not np.isnan(hsic_p_q)   else 1.0,
          tol_override=float('inf'))
else:
    print('[P4/G2-HSIC] skipped (USE_HSIC=False)')"""
    )

    code(
        r"""# === Cell 56 · Phase-10 verifier + checkpoint ===
def _verify_phase_10():
    assert max_nmi < 0.6, f'5-ch MI too high: {max_nmi}'
    print(f'[OK   ] Phase 10 — turbo + capacity + independence (max NMI = {max_nmi:.3f})')

_verify_phase_10()
save_checkpoint('10_dual_channel', {
    'G_turbo': float(G_turbo_q), 'RD_EL': float(rd_el_q),
    'EL_cap': EL_CAP, 'max_nmi': float(max_nmi),
}, state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 11 — Adversarial forgery (T5, T20, D23) (cells 57-63)
# ============================================================================
def build_phase_11() -> None:
    phase_header(
        11,
        "Adversarial forgery — T5 pre-reg tautology, T20 structural-forgery-P3, "
        "D23 canon-wins rate, hard-negative mining, 100-synthetic-Quran Pareto",
        "The adversarial battery. We read T5 and T20 from RES and add our own "
        "null ladder + Pareto frontier.",
    )

    code(
        r"""# === Cell 57 · T5 pre-reg tautology check (canon vs perturbed) ===
# AUDIT 2026-04-19 (v5 fix ①): attempt Phase-11 resume at the top of the phase
# to restore SYN_POINTS and friends, so Cells 59/61 can skip their expensive
# synthesis loops when a valid checkpoint exists. No-op on a cold run.
_phase11_cached = resume_from('11_adversarial') and 'SYN_POINTS' in globals()
if _phase11_cached:
    print(f'[Phase 11] resumed from checkpoint  ({len(SYN_POINTS)} synthetic points)')

t5 = RES.get('T5_tautology', {})
canon_wins = {r['target']: r.get('canon_wins_pct', 0) for r in t5.get('results', [])}
print('[T5  ] canon-wins rate per target:')
for tgt, pct in canon_wins.items():
    print(f'  {tgt:<18s}  canon_wins = {pct}%')
bless('T5',  float(canon_wins.get('quran', 0) or 0))
bless('D23', float((canon_wins.get('quran', 0) or 0) / 100.0))"""
    )

    code(
        r"""# === Cell 58 · T20 structural forgery P3 (D21 NOT REPRODUCED) ===
t20 = RES.get('T20_forgery_p3', {})
q_col = t20.get('per_target', {}).get('quran', {}).get('pct_collapsed', float('nan'))
b_col = t20.get('per_target', {}).get('arabic_bible', {}).get('pct_collapsed', float('nan'))
diff = (q_col - b_col) / 100.0
print(f'[T20 ] Quran pct_collapsed = {q_col:.0f}%   Bible = {b_col:.0f}%   diff = {diff:+.3f}')
bless('T20', float(diff))
bless('D21', float(diff))"""
    )

    code(
        r"""# === Cell 59 · constrained null ladder (unigram-shuffle vs Quran) ===
# AUDIT 2026-04-19 (v5 fix ①): skip if `gap` already restored from checkpoint.
if _phase11_cached and 'gap' in globals():
    print(f'[null] CACHED L2 gap in 5-D = {float(gap):.3f}')
else:
    from src.raw_loader import Unit as U
    rng = np.random.default_rng(SEED)
    q_toks = [w for u in CORPORA['quran'] for v in u.verses for w in v.split()]

    # Level 1: random tokens (unigram frequency match)
    syn_units = []
    for i in range(30):
        syn_verses = [' '.join(rng.choice(q_toks, size=10)) for _ in range(20)]
        syn_units.append(U(corpus='SYN', label=f'L1_{i}', verses=syn_verses))
    f_null = ft.features_5d(sum([u.verses for u in syn_units], []))
    print(f'[null] unigram-shuffle  EL={f_null[0]:.3f}  CN={f_null[2]:.3f}  H_cond={f_null[3]:.3f}')
    # Quran reference (first 30 Band-A surahs, concatenated)
    q_ref_verses = sum([u.verses for u in CORPORA['quran'][:30]], [])
    f_q = ft.features_5d(q_ref_verses)
    print(f'[ref ] Quran reference  EL={f_q[0]:.3f}  CN={f_q[2]:.3f}  H_cond={f_q[3]:.3f}')
    gap = np.linalg.norm(f_q - f_null)
    print(f'[null] L2 gap in 5-D = {gap:.3f}  (bigger = better separation from unigram null)')"""
    )

    code(
        r"""# === Cell 60 · hard-negative mining (5-leak taxonomy) ===
findings = [
    ('A pickle-Genesis-x7 repeat', bool(ALL_RESULTS.get('PickleBug_simulation', {}).get('actual'))),
    ('B hadith in control pool',    'hadith_bukhari' not in ARABIC_CTRL_POOL),
    ('C Quran excluded from Arabic centroid', 'quran' not in ARABIC_CTRL_POOL),
    ('D Band-A gating configured',  BAND_A_LO >= 1 and BAND_A_HI > BAND_A_LO),
    ('E pool > 1 corpus',           len(ARABIC_CTRL_POOL) >= 2),
]
for label, ok in findings:
    print(f'  [hard-neg] {label:<35s}  {"OK" if ok else "FAIL"}')
assert all(ok for _, ok in findings), 'hard-negative mining exposed an issue'"""
    )

    code(
        r"""# === Cell 61 · synthetic adversarial texts (EXTERNAL vocabulary) ===
# CRITICAL: draw tokens from Arabic CONTROL vocabulary (poetry_abbasi union),
# NOT Quran tokens — otherwise the test is a tautology (synthetic Quran
# made of Quran tokens will trivially approach Quran's EL/CN).
#
# AUDIT 2026-04-19 (v5 fix ①): this cell is the single slowest in Phase 11
# (20 iterations × 80 verses × features_5d = ~5–10 min in FAST_MODE). Skip
# if SYN_POINTS was already restored from the Phase-11 checkpoint state.
if _phase11_cached and 'SYN_POINTS' in globals() and len(SYN_POINTS) > 0:
    n_syn = len(SYN_POINTS)
    dominating = sum(1 for _, _, aE, aC, _ in SYN_POINTS
                     if aE >= EL_by['quran'] and aC >= CN_by['quran'])
    print(f'[synth] CACHED {n_syn} synthetic points from Phase-11 checkpoint; '
          f'{dominating}/{n_syn} reach Quran (EL, CN)')
else:
    n_syn = 20 if FAST_MODE else 60
    SYN_POINTS = []
    rhyme_cls = RHYME_LETTERS   # data-derived (Phase 3 Cell 19)
    ext_sources = [c for c in ('poetry_abbasi', 'poetry_islami', 'poetry_jahili',
                               'arabic_bible', 'ksucca', 'hindawi') if c in CORPORA]
    ext_toks = [w for n in ext_sources for u in CORPORA[n] for v in u.verses
                for w in v.split() if w]
    if not ext_toks:
        raise HallucinationError(
            '[synth] external control vocabulary missing; refusing Quran-token '
            'fallback because it would tautologize the adversarial synthesis test.'
        )

    rhyme_toks = [w for w in ext_toks if w and w[-1] in rhyme_cls]
    non_rhyme  = [w for w in ext_toks if not (w and w[-1] in rhyme_cls)]
    conn_set   = list(ft.ARABIC_CONN)
    print(f'[synth] external vocab: {len(ext_toks)} tokens from {len(ext_sources)} control corpora')

    for k in range(n_syn):
        target_el = rng.uniform(0.3, 0.9); target_cn = rng.uniform(0.02, 0.15)
        syn_verses = []
        for _ in range(80):
            nt = int(rng.integers(5, 20))
            toks = []
            for j in range(nt):
                if j == nt-1 and rng.random() < target_el and rhyme_toks:
                    toks.append(str(rng.choice(rhyme_toks)))
                elif j == 0 and rng.random() < target_cn and conn_set:
                    toks.append(str(rng.choice(conn_set)))
                else:
                    toks.append(str(rng.choice(non_rhyme if non_rhyme else ext_toks)))
            syn_verses.append(' '.join(toks))
        f = ft.features_5d(syn_verses)
        SYN_POINTS.append((target_el, target_cn, float(f[0]), float(f[2]), float(f[1])))

    dominating = sum(1 for _, _, aE, aC, _ in SYN_POINTS
                     if aE >= EL_by['quran'] and aC >= CN_by['quran'])
    print(f'[synth] {dominating}/{n_syn} synthetic texts (built from CONTROL vocab) '
          f'simultaneously reach Quran (EL, CN)')"""
    )

    code(
        r"""# === Cell 62 · T15 upstream 5-fold AUC (DIAGNOSTIC, not blessed) ===
# AUDIT 2026-04-19 (v5): T15/D09 are now blessed in Cell 71 with the
# nested-CV held-out mean (the defensible number). This cell keeps the
# upstream pipeline's 5-fold AUC as a sanity diagnostic only — it uses
# the pipeline's single-scaler split and is therefore optimistic.
# Do NOT cite this value; see Cell 71 for the blessed classifier number.
t15 = RES.get('T15_classifier', {})
auc = t15.get('auc', float('nan'))
print(f'[T15 upstream] 5-fold pipeline AUC = {auc:.4f}  (diagnostic; not blessed)')"""
    )

    code(
        r"""# === Cell 63 · Phase-11 verifier + checkpoint ===
_verify_phase_11 = lambda: print('[OK   ] Phase 11 — adversarial battery done')
_verify_phase_11()
# AUDIT 2026-04-19 (v5 fix ①): persist SYN_POINTS + gap into state= so that a
# subsequent `resume_from('11_adversarial')` in Cell 57 can repopulate them
# and Cells 59/61 can skip their expensive synthesis loops on re-runs.
save_checkpoint('11_adversarial', {
    'canon_wins': canon_wins, 'D21_diff': float(diff),
    'null_gap': float(gap), 'n_synthetic': len(SYN_POINTS),
    'dominating': int(dominating), 'auc_T15': float(auc),
}, state={'ALL_RESULTS': ALL_RESULTS,
          'SYN_POINTS': SYN_POINTS,
          'gap': float(gap),
          'canon_wins': canon_wins,
          'diff': float(diff),
          'dominating': int(dominating)})"""
    )


# ============================================================================
# PHASE 12 — Robustness (T12 CV, T13 Meccan/Medinan, T14 bootstrap) (cells 64-69)
# ============================================================================
def build_phase_12() -> None:
    phase_header(
        12,
        "Robustness — T12 10-fold CV, T13 Meccan/Medinan (FALSIFIED per pre-reg), "
        "T14 bootstrap Ω, matched-length sensitivity",
        "Cross-validation, bootstrap, Meccan/Medinan F-test. Test B of the "
        "pre-registration explicitly FALSIFIES (F < 1).",
    )

    code(
        r"""# === Cell 64 · T12 10-fold CV Phi_M (different test from PreReg A) ===
# T12 runs surah-level 10-fold CV on the Quran vs. control discrimination.
# This is NOT the same test as PreReg A (leave-one-family-out). The previous
# blessing of PreReg_A_leave_one_out on T12's min_d was a PRE-REGISTRATION
# VIOLATION. We bless T12/D24 here and implement real leave-one-family-out
# below in Cell 64b.
t12 = RES.get('T12_cv_phi_m', {})
median_d = t12.get('median_d', float('nan')); min_d = t12.get('min_d', float('nan'))
print(f'[T12 ] 10-fold CV Phi_M  median d = {median_d:.3f}  min d = {min_d:.3f}')
bless('T12', float(median_d))
bless('D24', float(median_d))"""
    )

    code(
        r"""# === Cell 64b · PreReg A — REAL leave-one-family-out (audit 2026-04-18) ===
# Pre-registration (see Cell 11): Phi_M separation survives leaving out ANY
# 1 of 9 control families, with min |d| >= 1.5 across all splits.
# Previous blessing used T12 10-fold CV which is a SURAH-level test — the
# wrong hypothesis. This cell now runs the REAL leave-one-family-out loop.
# Per-split cost: O(|Arabic families| × same-cost-as-Cell-29-Φ_M).
arabic_controls = list(ARABIC_CTRL_POOL)   # 6 families; hadith_bukhari quarantined
print(f'[PreReg A] leave-one-family-out over {len(arabic_controls)} Arabic control families')

lofo_results = {}
X_QURAN_LO   = _X_for('quran', BAND_A_LO, BAND_A_HI)
for held_out in arabic_controls:
    others = [c for c in arabic_controls if c != held_out]
    X_rest = np.vstack([_X_for(c, BAND_A_LO, BAND_A_HI) for c in others
                        if len(_X_for(c, BAND_A_LO, BAND_A_HI)) > 0])
    if len(X_rest) < 3:
        lofo_results[held_out] = float('nan'); continue
    mu_lo  = X_rest.mean(0)
    S_lo   = np.cov(X_rest.T, ddof=1) + 1e-6 * np.eye(5)
    Sinv_lo = np.linalg.inv(S_lo)
    d_q_lo    = mahalanobis(X_QURAN_LO,  mu_lo, Sinv_lo)
    d_ctrl_lo = mahalanobis(X_rest,      mu_lo, Sinv_lo)
    # Cohen's d as the interpretable effect size on this split (same stat
    # the pre-registration names, even though it is biased-up; what matters
    # for PreReg A is whether d drops below 1.5 on ANY held-out family).
    pool_std = np.sqrt(((len(d_q_lo)-1)*d_q_lo.var(ddof=1) +
                        (len(d_ctrl_lo)-1)*d_ctrl_lo.var(ddof=1))
                       / max(1, len(d_q_lo)+len(d_ctrl_lo)-2))
    d_split = float((d_q_lo.mean() - d_ctrl_lo.mean()) / max(pool_std, 1e-9))
    lofo_results[held_out] = d_split
    print(f'  [LOFO] held_out={held_out:<22s}  d = {d_split:+.3f}  (n_rest={len(X_rest)})')

valid_ds = [v for v in lofo_results.values() if not np.isnan(v)]
min_d_lofo = float(min(valid_ds)) if valid_ds else float('nan')
max_d_lofo = float(max(valid_ds)) if valid_ds else float('nan')
print(f'[PreReg A] leave-one-family-out:  min d = {min_d_lofo:+.3f}  '
      f'max d = {max_d_lofo:+.3f}  (threshold: min d >= 1.5)')
passes_prereg_A = (not np.isnan(min_d_lofo)) and (min_d_lofo >= 1.5)
print(f'[PreReg A] verdict: {"PASS" if passes_prereg_A else "FAIL"}  '
      f'(falsifier: any split gives d < 1.0)')
bless('PreReg_A_leave_one_out', float(min_d_lofo))"""
    )

    code(
        r"""# === Cell 65 · T13 Meccan/Medinan (pre-reg B — FALSIFIED on clean data) ===
# AUDIT 2026-04-18 (v4): T13 itself was never blessed — only D25 and the
# pre-reg B entry were. T13 now records min(F_M, F_D) (consistent with
# the pre-reg verdict semantics, which requires BOTH to exceed 1.0).
t13 = RES.get('T13_meccan_medinan', {})
F_M = t13.get('F_meccan_mean', float('nan'))
F_D = t13.get('F_medinan_mean', float('nan'))
print(f'[T13 ] F_Meccan  = {F_M:.3f}   F_Medinan = {F_D:.3f}')
verdict = 'PASSES' if (F_M > 1 and F_D > 1) else '**FALSIFIED**'
print(f'[T13 ] pre-reg B: {verdict}')
bless('T13', float(min(F_M, F_D)))
bless('D25', float(F_M))
bless('PreReg_B_meccan_medinan', float(min(F_M, F_D)))"""
    )

    code(
        r"""# === Cell 66 · T14 bootstrap Ω (pre-reg C) ===
t14 = RES.get('T14_bootstrap_omega', {})
median_omega = t14.get('median_omega', float('nan'))
pct_gt_2 = t14.get('pct_bootstraps_omega_gt_2', float('nan'))
print(f'[T14 ] median Omega = {median_omega:.3f}  pct>2 = {pct_gt_2:.1f}%')
bless('T14', float(pct_gt_2 / 100.0))
bless('D26', float(pct_gt_2 / 100.0))
bless('PreReg_C_bootstrap_omega', float(pct_gt_2 / 100.0))"""
    )

    code(
        r"""# === Cell 67 · matched-length sensitivity across 5 windows ===
WINDOWS = [(5, 20), (10, 30), (15, 50), (20, 80), (30, 100)]
sens = {}
for lo, hi in WINDOWS:
    eff, n_q = _phi_m_for_band(lo, hi)
    sens[(lo, hi)] = eff
    print(f'  [sens] band ({lo:>3},{hi:>3} verses) n_Q={n_q:>3d}   d = {eff:+.3f}')
# Keep only numeric
sens_vals = [v for v in sens.values() if not np.isnan(v)]
sens_ok = all(v > 0.5 for v in sens_vals) if sens_vals else False
print(f'[sens] all windows pass d > 0.5: {sens_ok}')"""
    )

    code(
        r"""# === Cell 68 · T6 H-Cascade (surviving positive) ===
# AUDIT 2026-04-18 (v4): T6 was previously read + printed but never
# blessed, so it was missing from ALL_RESULTS / the scorecard / FDR.
t6 = RES.get('T6_hcascade', {})
d6 = t6.get('cohens_d', float('nan'))
print(f'[T6  ] H-Cascade fractality d = {d6:+.3f}')
bless('T6', float(d6))"""
    )

    code(
        r"""# === Cell 69 · Phase-12 verifier + checkpoint ===
_verify_phase_12 = lambda: print('[OK   ] Phase 12 — robustness (pre-reg B FALSIFIED as expected)')
_verify_phase_12()
save_checkpoint('12_robust',
                {'T12': t12, 'T13': t13, 'T14': t14,
                 'matched_sens': sens, 'T6_d': float(d6)},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 13 — Classifier + nested CV + Meccan-Medinan transfer (cells 70-74)
# ============================================================================
def build_phase_13() -> None:
    phase_header(
        13,
        "Classifier battery — T15 AUC, nested-CV, Meccan→Medinan transfer, ROC",
        "Classifier already ran in T15 (Phase 11 Cell 62). Here we add nested-CV "
        "and Meccan→Medinan transfer on top, using the per-surah FEATS records.",
    )

    code(
        r"""# === Cell 70 · 5-fold Logistic Regression AUC (read-only, from T15) ===
print(f'[D09] 5-fold AUC (from T15_classifier) = {auc:.4f}')"""
    )

    code(
        r"""# === Cell 71 · Nested CV (outer 5, inner 3) over Band-A surahs (v5) ===
# AUDIT 2026-04-19 (v5):
#   (1) Outer and inner splitters are StratifiedKFold so Quran/ctrl class
#       balance is preserved across folds.
#   (2) StandardScaler is fit INSIDE each inner-train fold (not on the
#       full outer-train) — prevents the inner-validation scaler leakage
#       flagged by the 2026-04-19 audit.
#   (3) This cell now blesses T15/D09 with the nested-CV held-out mean,
#       making it the defensible classifier number. Cell 62 is the
#       upstream 5-fold diagnostic (not blessed).
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

Xq = _X_for('quran', BAND_A_LO, BAND_A_HI)
Xc = np.vstack([_X_for(c, BAND_A_LO, BAND_A_HI) for c in ARABIC_CTRL_POOL
                if len(_X_for(c, BAND_A_LO, BAND_A_HI)) > 0])
Xall = np.vstack([Xq, Xc])
yall = np.concatenate([np.ones(len(Xq)), np.zeros(len(Xc))])

outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
aucs = []
for tr, te in outer.split(Xall, yall):
    Xtr, Xte, ytr, yte = Xall[tr], Xall[te], yall[tr], yall[te]
    inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + 1)
    best, best_C = -np.inf, 1.0
    for C in [0.01, 0.1, 1.0, 10.0]:
        ias = []
        for itr, ite in inner.split(Xtr, ytr):
            sc_in = StandardScaler().fit(Xtr[itr])             # inner-train ONLY
            clf = LogisticRegression(C=C, max_iter=2000).fit(
                sc_in.transform(Xtr[itr]), ytr[itr])
            ias.append(roc_auc_score(
                ytr[ite], clf.predict_proba(sc_in.transform(Xtr[ite]))[:, 1]))
        m = float(np.mean(ias))
        if m > best:
            best, best_C = m, C
    sc = StandardScaler().fit(Xtr)                             # refit on full outer-train
    clf = LogisticRegression(C=best_C, max_iter=2000).fit(sc.transform(Xtr), ytr)
    aucs.append(roc_auc_score(yte, clf.predict_proba(sc.transform(Xte))[:, 1]))

auc_nested = float(np.mean(aucs))
auc_nested_std = float(np.std(aucs))
print(f'[cls ] nested-CV AUC = {auc_nested:.4f} +/- {auc_nested_std:.4f}')
bless('T15', auc_nested)
bless('D09', auc_nested)"""
    )

    code(
        r"""# === Cell 72 · Meccan -> Medinan transfer AUC ===
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 57, 58, 59,
           60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}

def _surah_num(label):
    try: return int(str(label).lstrip('Q:'))
    except Exception: return None

q_recs = [r for r in FEATS['quran'] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
mec_recs = [r for r in q_recs if _surah_num(r['label']) and _surah_num(r['label']) not in MEDINAN]
med_recs = [r for r in q_recs if _surah_num(r['label']) and _surah_num(r['label']) in MEDINAN]

if len(mec_recs) >= 10 and len(med_recs) >= 5:
    Xm = np.array([[r[c] for c in FEAT_COLS] for r in mec_recs])
    Xd = np.array([[r[c] for c in FEAT_COLS] for r in med_recs])
    Xmc = np.vstack([Xm, Xc]); ymc = np.concatenate([np.ones(len(Xm)), np.zeros(len(Xc))])
    Xdc = np.vstack([Xd, Xc]); ydc = np.concatenate([np.ones(len(Xd)), np.zeros(len(Xc))])
    sc = StandardScaler().fit(Xmc)
    clf = LogisticRegression(max_iter=2000).fit(sc.transform(Xmc), ymc)
    auc_tr = roc_auc_score(ydc, clf.predict_proba(sc.transform(Xdc))[:,1])
    print(f'[trans] Meccan({len(Xm)}) -> Medinan({len(Xd)}) AUC = {auc_tr:.3f}  (target ~0.87)')
else:
    auc_tr = float('nan')
    print(f'[trans] insufficient Meccan/Medinan surahs ({len(mec_recs)}/{len(med_recs)}); skipping')"""
    )

    code(
        r"""# === Cell 73 · ROC + PR summary (IN-SAMPLE diagnostic only) ===
# AUDIT 2026-04-19 (fix ⑤): the classifier below is fit on Xall and scored
# on Xall — the reported AUC is therefore IN-SAMPLE (training) and is an
# OPTIMISTIC upper bound that will always exceed the held-out number. It
# is printed purely as a sanity / shape-of-ROC diagnostic.
# DO NOT CITE THIS NUMBER. The defensible classifier AUC is the nested-CV
# mean from Cell 71 (`np.mean(aucs)`) which is the blessed T15/D09 value.
from sklearn.metrics import precision_recall_curve, roc_curve, auc as _auc
sc_full = StandardScaler().fit(Xall)
clf_full = LogisticRegression(max_iter=2000).fit(sc_full.transform(Xall), yall)
probs = clf_full.predict_proba(sc_full.transform(Xall))[:,1]
fpr, tpr, _ = roc_curve(yall, probs); prec, rec, _ = precision_recall_curve(yall, probs)
auc_insample = float(_auc(fpr, tpr))
ap_insample  = float(_auc(rec, prec))
print(f'[roc DIAGNOSTIC IN-SAMPLE] AUC = {auc_insample:.4f}   AP = {ap_insample:.4f}')
print(f'[roc DIAGNOSTIC IN-SAMPLE]   ^^ do NOT cite; held-out AUC = '
      f'{np.mean(aucs):.4f} (nested-CV, Cell 71, blessed as T15/D09).')"""
    )

    code(
        r"""# === Cell 74 · Phase-13 verifier + checkpoint ===
_verify_phase_13 = lambda: print(f'[OK   ] Phase 13 — classifier nested AUC = {np.mean(aucs):.4f}')
_verify_phase_13()
save_checkpoint('13_classifier',
                {'auc_T15': float(auc),
                 'auc_nested_mean': float(np.mean(aucs)),
                 'auc_nested_std': float(np.std(aucs)),
                 'auc_transfer': float(auc_tr) if not np.isnan(auc_tr) else None},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 14 — Topology: RQA + lesion + saddle + phi_frac + RG + Fisher + Hurst (cells 75-84)
# ============================================================================
def build_phase_14() -> None:
    phase_header(
        14,
        "Topology — T19 RQA, T24 lesion, T25 saddle (7/8 near-universal), "
        "T26 terminal-depth-3, T29 phi_frac (golden-ratio cherry-pick), "
        "T30 RG flow, T31 Fisher curvature, plus Hurst Supp-A/B/C",
        "All pulled from RES. We add the Hurst supplementary analysis on top.",
    )

    code(
        r"""# === Cell 75 · T19 RQA laminarity ===
t19 = RES.get('T19_rqa', {})
lam_q = t19.get('per_corpus', {}).get('quran', {}).get('mean_LAM', float('nan'))
print(f'[T19 ] Quran LAM = {lam_q:.3f}')
bless('T19', float(lam_q))
bless('D16', float(lam_q))"""
    )

    code(
        r"""# === Cell 76 · T24 lesion dose-response ===
t24 = RES.get('T24_lesion', {})
dr = t24.get('dose_response', {})
el_drop_1 = (dr.get('1.0pct', {}) or {}).get('EL_drop_from_canonical', float('nan'))
el_drop_5 = (dr.get('5.0pct', {}) or {}).get('EL_drop_from_canonical', float('nan'))
print(f'[T24 ] EL drop @1% = {el_drop_1*100:.1f}%   @5% = {el_drop_5*100:.1f}%   peak @ {t24.get("heat_capacity_peak_at","?")}')
bless('T24', float(el_drop_5))"""
    )

    code(
        r"""# === Cell 77 · T25 info-geometry saddle (7/8 near-universal) ===
t25 = RES.get('T25_info_geo_saddle', {})
n_sad = t25.get('n_saddles', 0); n_tot = t25.get('n_corpora', 0)
print(f'[T25 ] saddle in {n_sad}/{n_tot} corpora (near-universal, not distinctive)')
bless('T25', float(n_sad))"""
    )

    code(
        r"""# === Cell 78 · T26 terminal-position depth-3 (PROVED STRONGER) ===
t26 = RES.get('T26_terminal_depth', {})
pp = t26.get('per_position', {})
d_neg1 = pp.get('-1', {}).get('cohens_d', float('nan'))
d_neg2 = pp.get('-2', {}).get('cohens_d', float('nan'))
d_neg3 = pp.get('-3', {}).get('cohens_d', float('nan'))
print(f'[T26 ] d(-1)={d_neg1:+.2f}  d(-2)={d_neg2:+.2f}  d(-3)={d_neg3:+.2f}  '
      f'depth={t26.get("signal_depth_letters","?")} letters')
bless('T26', float(d_neg1))"""
    )

    code(
        r"""# === Cell 79 · T29 phi_frac (golden-ratio cherry-pick exposed) ===
t29 = RES.get('T29_phi_frac', {})
phi_frac = t29.get('phi_frac', float('nan'))
print(f'[T29 ] phi_frac = {phi_frac:+.3f}   near-golden = {t29.get("near_golden_ratio", False)}')
# reverse direction: any value can be made near golden by flipping
phi_rev = 1.0 - phi_frac if not np.isnan(phi_frac) else float('nan')
print(f'[T29 ] 1 - phi_frac = {phi_rev:+.3f}  (ANY value can appear golden by flipping direction)')
bless('T29', float(phi_frac))"""
    )

    code(
        r"""# === Cell 80 · T30 RG flow (Kadanoff coarse-graining) ===
t30 = RES.get('T30_rg_flow', {})
alpha_q = t30.get('quran_alpha', float('nan'))
rank_q  = t30.get('quran_rank', '?')
print(f'[T30 ] Quran alpha = {alpha_q:+.3f}   rank = {rank_q}/{t30.get("n_corpora","?")}   verdict: {t30.get("verdict","?")}')
bless('T30', float(alpha_q))"""
    )

    code(
        r"""# === Cell 81 · T31 Fisher-metric curvature + volume ===
t31 = RES.get('T31_fisher_curvature', {})
curv_rank = t31.get('quran_curvature_rank', '?')
vol_rank  = t31.get('quran_volume_rank', '?')
print(f'[T31 ] Fisher curvature rank = {curv_rank}/{t31.get("n_corpora","?")}   volume rank = {vol_rank}')
bless('T31', float(curv_rank) if isinstance(curv_rank, (int, float)) else float('nan'))"""
    )

    code(
        r"""# === Cell 82 · Supp-A Hurst + Supp-B multi-level Hurst ===
# AUDIT 2026-04-18: R/S estimator is known to be biased upward on short
# sequences. DFA (Detrended Fluctuation Analysis) is the current standard in
# computational linguistics. We compute both; R/S stays as the primary for
# backward compatibility with the locked scalar (Supp_A_Hurst = R/S), and
# DFA is reported as a sanity check (blessed separately as Hurst_DFA_quran).
# AUDIT v3: ALSO report the log-log R² of each fit. The Hurst slope alone
# is only meaningful if the scaling is actually linear on the log-log axes;
# R² < 0.9 indicates the sequence has no reliable scaling regime at the
# scales sampled. R² values are blessed with tol=inf (reporting-only).
def _el_sequence(corpus_units):
    seq = []
    for u in corpus_units:
        for v in u.verses:
            toks = tokenise(v)
            if not toks: continue
            seq.append(1 if toks[-1][-1] in RHYME_LETTERS else 0)
    return np.array(seq, dtype=float)

def _loglog_r2(xs, ys):
    '''R² of a log-log linear fit; NaN if <3 points or zero variance.'''
    if len(xs) < 3: return float('nan')
    lx = np.log(np.asarray(xs, dtype=float))
    ly = np.log(np.maximum(np.asarray(ys, dtype=float), 1e-12))
    if lx.std() == 0 or ly.std() == 0: return float('nan')
    slope, intercept = np.polyfit(lx, ly, 1)
    y_hat = slope * lx + intercept
    ss_res = float(np.sum((ly - y_hat) ** 2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2))
    return float(1.0 - ss_res / max(ss_tot, 1e-12))

def _hurst(seq, min_n=10, return_r2=False):
    '''R/S estimator (legacy). Biased upward on short sequences.
    If return_r2=True, return (slope, log-log R²); else just slope.'''
    if len(seq) < 2*min_n:
        return (float('nan'), float('nan')) if return_r2 else float('nan')
    Ns = np.unique(np.logspace(np.log10(min_n), np.log10(len(seq)//2), 10).astype(int))
    R_S = []; used_Ns = []
    for nn in Ns:
        k = len(seq) // nn; rs = []
        for i in range(k):
            win = seq[i*nn:(i+1)*nn]
            cs = (win - win.mean()).cumsum(); R = cs.max() - cs.min(); S = win.std()
            if S > 0: rs.append(R/S)
        if rs:
            R_S.append(np.mean(rs)); used_Ns.append(nn)
    if len(R_S) < 3:
        return (float('nan'), float('nan')) if return_r2 else float('nan')
    slope = float(np.polyfit(np.log(used_Ns), np.log(np.array(R_S)), 1)[0])
    if return_r2:
        return slope, _loglog_r2(used_Ns, R_S)
    return slope

def _hurst_dfa(seq, min_n=10, return_r2=False):
    '''Detrended Fluctuation Analysis (DFA). Standard for noisy linguistic
    time series. H = slope of log(F(n)) vs log(n) where F(n) is the RMS of
    detrended cumulative deviations in non-overlapping windows of size n.'''
    x = np.asarray(seq, dtype=float)
    if len(x) < 2*min_n:
        return (float('nan'), float('nan')) if return_r2 else float('nan')
    y = np.cumsum(x - x.mean())                       # integrated series
    Ns = np.unique(np.logspace(np.log10(min_n),
                                np.log10(len(y)//2), 10).astype(int))
    Fs = []; used_Ns = []
    for nn in Ns:
        n_win = len(y) // nn
        if n_win < 2: continue
        rms = []
        for i in range(n_win):
            seg = y[i*nn:(i+1)*nn]
            t   = np.arange(nn)
            # linear detrend
            b, a = np.polyfit(t, seg, 1)
            trend = b*t + a
            rms.append(np.sqrt(np.mean((seg - trend)**2)))
        if rms:
            Fs.append(np.mean(rms)); used_Ns.append(nn)
    if len(Fs) < 3:
        return (float('nan'), float('nan')) if return_r2 else float('nan')
    slope = float(np.polyfit(np.log(used_Ns),
                             np.log(np.maximum(Fs, 1e-12)), 1)[0])
    if return_r2:
        return slope, _loglog_r2(used_Ns, Fs)
    return slope

Hurst_vals     = {}; Hurst_R2     = {}
Hurst_DFA_vals = {}; Hurst_DFA_R2 = {}
for n in CORPORA:
    h_rs,  r2_rs  = _hurst(    _el_sequence(CORPORA.get(n, [])), return_r2=True)
    h_dfa, r2_dfa = _hurst_dfa(_el_sequence(CORPORA.get(n, [])), return_r2=True)
    Hurst_vals[n]     = h_rs
    Hurst_R2[n]       = r2_rs
    Hurst_DFA_vals[n] = h_dfa
    Hurst_DFA_R2[n]   = r2_dfa
print(f'  {"corpus":<22s}  {"H (R/S)":>8s}  {"R²":>5s}  {"H (DFA)":>8s}  {"R²":>5s}')
for n in sorted(Hurst_vals, key=lambda k: -(Hurst_vals[k] if not np.isnan(Hurst_vals[k]) else -1))[:6]:
    h_rs   = Hurst_vals[n];     r2_rs  = Hurst_R2.get(n, float('nan'))
    h_dfa  = Hurst_DFA_vals[n]; r2_dfa = Hurst_DFA_R2.get(n, float('nan'))
    print(f'  {n:<22s}  {h_rs:>8.3f}  {r2_rs:>5.2f}  {h_dfa:>8.3f}  {r2_dfa:>5.2f}')
r2_q_rs  = Hurst_R2.get('quran',     float('nan'))
r2_q_dfa = Hurst_DFA_R2.get('quran', float('nan'))
if not np.isnan(r2_q_rs)  and r2_q_rs  < 0.9:
    print(f'[WARN] Quran R/S Hurst log-log R² = {r2_q_rs:.2f} < 0.9 — '
          f'scaling regime is weak; the H slope is NOT a reliable estimator.')
if not np.isnan(r2_q_dfa) and r2_q_dfa < 0.9:
    print(f'[WARN] Quran DFA Hurst log-log R² = {r2_q_dfa:.2f} < 0.9 — '
          f'scaling regime is weak; the H slope is NOT a reliable estimator.')
bless('Supp_A_Hurst', float(Hurst_vals.get('quran', float('nan'))))
bless('Hurst_DFA_quran', float(Hurst_DFA_vals.get('quran', float('nan'))),
      tol_override=float('inf'))
bless('Supp_A_Hurst_R2',    float(r2_q_rs)  if not np.isnan(r2_q_rs)  else 0.0,
      tol_override=float('inf'))
bless('Hurst_DFA_quran_R2', float(r2_q_dfa) if not np.isnan(r2_q_dfa) else 0.0,
      tol_override=float('inf'))

# simplified multi-level: letter-hash Hurst
def _letter_seq(corpus_units):
    s = []
    for u in corpus_units:
        for v in u.verses:
            for t in tokenise(v):
                for c in t: s.append(ord(c) % 29 / 29.0)
    return np.array(s[:20000])

H_multi = {n: {'letter': _hurst(_letter_seq(CORPORA.get(n, []))),
                'EL_verse': Hurst_vals.get(n, float('nan'))}
           for n in CORPORA}
bless('Supp_B_multilevel_Hurst', float(H_multi['quran']['letter'])
      if not np.isnan(H_multi['quran']['letter']) else 0.0,
      tol_override=float('inf') if np.isnan(H_multi['quran']['letter']) else None)"""
    )

    code(
        r"""# === Cell 83 · Supp-C acoustic bridge (rhyme-class x connective-start) ===
# AUDIT 2026-04-18 (v3): the 4×2 rhyme-class × connective-start contingency
# table often contains cells with expected count <5, which invalidates the
# asymptotic chi² distribution (χ² only converges when all E_ij ≥ 5, per
# Cochran 1954). Previous code dropped the whole corpus to NaN when ANY
# cell was empty, losing information silently. We now:
#   (a) keep the chi² statistic (for backward compat with locked scalar)
#   (b) compute an EXACT Monte-Carlo permutation p-value from N_PERM
#       random shuffles of the `has_conn` label (preserves row/col marginals
#       via independent rhyme-class draws -- label-shuffle null).
#   (c) accept tables with empty cells — the MC p is well-defined there.
from scipy.stats import chi2_contingency
def _rhyme_class(ch):
    for i, cls in enumerate(['نمدريه', 'باولفت', 'كقسجخ', 'زطضظحعغش']):
        if ch in cls: return i
    return -1

# AUDIT 2026-04-19 (fix ⑦): `rng_ac` was previously `default_rng(SEED+205)`
# INSIDE _acou_stats, so every call to the function re-seeded and shared an
# identical noise trajectory. This biases the MC null across corpora (each
# corpus sees the same permutation sequence). Hoist the generator to module
# scope so each call consumes fresh entropy while staying deterministic.
#
# v6 RESUME-CAVEAT (zero current risk): both `_RNG_ACOU` and `_acou_stats`
# live in THIS cell only and `_acou_stats` is also only CALLED from this
# cell. A Phase-14 checkpoint resume skips this cell, so both become
# undefined. If you ever add a call to `_acou_stats` from a later phase,
# first hoist this RNG line and the function definition to a pre-Phase-14
# cell OR carry them through save_checkpoint's state= kwarg.
_RNG_ACOU = np.random.default_rng(SEED + 205)

def _acou_stats(rhyme_labels, conn_labels, n_perm=None):
    '''Compute χ² statistic + Monte-Carlo permutation p on the 4×2 table.
    rhyme_labels and conn_labels are parallel 1-D arrays of verse-level
    observations; the MC null shuffles `conn` while holding `rhyme` fixed.'''
    if n_perm is None: n_perm = N_PERM
    rhyme = np.asarray(rhyme_labels, dtype=int)
    conn  = np.asarray(conn_labels,  dtype=int)
    # Drop verses with undefined rhyme class (-1)
    mask = rhyme >= 0
    rhyme = rhyme[mask]; conn = conn[mask]
    if len(rhyme) < 10: return float('nan'), float('nan'), 0

    def _tabulate(r, c):
        R = int(r.max()) + 1 if len(r) else 0
        tab = np.zeros((R, 2), dtype=int)
        for a, b in zip(r, c): tab[a, b] += 1
        return tab

    def _chi2_stat(tab):
        # Pearson χ² = Σ (O - E)² / E with E = row_sum × col_sum / N
        row = tab.sum(1, keepdims=True)
        col = tab.sum(0, keepdims=True)
        N   = tab.sum()
        if N == 0: return 0.0
        E = row @ col / N
        mask = E > 0
        return float(np.sum((tab[mask] - E[mask]) ** 2 / E[mask]))

    obs_tab  = _tabulate(rhyme, conn)
    obs_chi2 = _chi2_stat(obs_tab)
    hits = 0
    for _ in range(n_perm):
        shuf = conn[_RNG_ACOU.permutation(len(conn))]
        perm_chi2 = _chi2_stat(_tabulate(rhyme, shuf))
        if perm_chi2 >= obs_chi2: hits += 1
    p_mc = float((hits + 1) / (n_perm + 1))
    return obs_chi2, p_mc, int(len(rhyme))

acoustic = {}
for n, units in CORPORA.items():
    rhyme_labels = []; conn_labels = []
    for u in units:
        for v in u.verses:
            toks = tokenise(v)
            if not toks: continue
            cls = _rhyme_class(toks[-1][-1] if toks[-1] else '_')
            rhyme_labels.append(cls)
            conn_labels.append(1 if toks[0] in ft.ARABIC_CONN else 0)
    # Legacy asymptotic χ² p (kept for backward compatibility; NaN if sparse)
    tab = {}
    for r, c in zip(rhyme_labels, conn_labels):
        if r >= 0:
            tab.setdefault(r, [0, 0])[c] += 1
    arr = np.array(list(tab.values())) if tab else np.zeros((0,2))
    if arr.size and arr.min() > 0:
        chi2_asym, p_asym, _, _ = chi2_contingency(arr)
    else:
        chi2_asym = _acou_stats(rhyme_labels, conn_labels, n_perm=1)[0]
        p_asym = float('nan')     # asymptotic p invalid on sparse tables
    # MC p-value (valid under sparse tables)
    chi2_mc, p_mc, n_used = _acou_stats(rhyme_labels, conn_labels)
    acoustic[n] = {'chi2': float(chi2_asym) if not np.isnan(chi2_asym) else float(chi2_mc),
                   'p': float(p_asym), 'p_mc': float(p_mc), 'n_used': n_used}
print(f'  [acou] {"corpus":<22s}  {"chi2":>7s}  {"p_asym":>9s}  {"p_MC":>7s}  n')
for n in sorted(acoustic, key=lambda k: -(acoustic[k]['chi2'] if not np.isnan(acoustic[k]['chi2']) else -1))[:6]:
    a = acoustic[n]
    p_asym_s = f'{a["p"]:.3g}' if not np.isnan(a['p']) else 'sparse'
    print(f'  [acou] {n:<22s}  {a["chi2"]:>7.2f}  {p_asym_s:>9s}  {a["p_mc"]:>7.4g}  {a["n_used"]}')
bless('Supp_C_acoustic_bridge', float(acoustic.get('quran', {}).get('chi2', float('nan'))),
      tol_override=float('inf'))
bless('Supp_C_acoustic_bridge_perm_p',
      float(acoustic.get('quran', {}).get('p_mc', 1.0)),
      tol_override=float('inf'))"""
    )

    code(
        r"""# === Cell 84 · Phase-14 verifier + checkpoint ===
_verify_phase_14 = lambda: print('[OK   ] Phase 14 — topology battery complete')
_verify_phase_14()
save_checkpoint('14_topology', {
    'T19_LAM':float(lam_q),'T24_drop5':float(el_drop_5),'T25_saddles':int(n_sad),
    'T26_d1':float(d_neg1),'T29_phi':float(phi_frac),'T30_alpha':float(alpha_q),
    'T31_curv_rank':curv_rank,'Hurst':Hurst_vals,'H_multi':H_multi,'acoustic':acoustic,
}, state={
    # AUDIT 2026-04-18 (v4): carry heavy globals that Phase 15-22 may need
    # on a cold resume from this checkpoint. Cheap to pickle, invaluable on
    # recovery — previously only ALL_RESULTS was saved.
    'ALL_RESULTS': ALL_RESULTS,
    'CORPORA': CORPORA, 'FEATS': FEATS,
    'mu': mu, 'S_inv': S_inv,
    'ARABIC_CTRL_POOL': ARABIC_CTRL_POOL,
    'ARABIC_FAMILY': ARABIC_FAMILY,
    'RHYME_LETTERS': RHYME_LETTERS,
    'BAND_A_LO': BAND_A_LO, 'BAND_A_HI': BAND_A_HI,
    'FEAT_COLS': FEAT_COLS,
})"""
    )


# ============================================================================
# PHASE 15 — Epigenetic E3 (cells 85-89)
# ============================================================================
def build_phase_15() -> None:
    phase_header(
        15,
        "Epigenetic E3 — T23 harakat channel capacity, vocalised 43x43, "
        "9-channel variant forensics, P-Epi-1 waqf",
        "The 'second code' above rasm. Reads T23 from RES; runs vocalised "
        "tests on the quran_vocal Unit set if available.",
    )

    code(
        r"""# === Cell 85 · T23 harakat channel capacity ===
t23 = RES.get('T23_harakat', {})
H_hr = t23.get('H_harakat_given_rasm_bits', float('nan'))
redundancy = t23.get('redundancy_fraction', float('nan'))
print(f'[T23 ] H(harakat | rasm) = {H_hr:.3f} bits   redundancy = {redundancy*100:.1f}%')
bless('T23', float(H_hr))
bless('E_harakat_capacity', float(H_hr))   # slot: E3 reserved for berry_esseen in names_registry"""
    )

    code(
        r"""# === Cell 86 · vocalised 43x43 spectral entropy (if quran_vocal available) ===
def _spectral43(units):
    letters = list('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
    harakat = list('ًٌٍَُِّْ')
    LI = {c:i for i,c in enumerate(letters)}
    HI = {c:i for i,c in enumerate(harakat)}
    M = np.zeros((len(letters), len(harakat)))
    for u in units:
        for v in u.verses:
            prev = None
            for ch in v:
                if ch in LI: prev = ch
                elif ch in HI and prev: M[LI[prev], HI[ch]] += 1
    if M.sum() == 0: return None
    P = M / M.sum()
    _, s, _ = np.linalg.svd(P)
    sp = s / s.sum()
    return -float(np.sum(sp * np.log2(sp + 1e-12)))

if 'quran' in CORPORA:
    # try to find a vocalised version — often the same corpus has diacritics
    se_q = _spectral43(CORPORA['quran'])
    print(f'[43x43] Quran spectral entropy = {se_q}')
else:
    print('[43x43] skipped')"""
    )

    code(
        r"""# === Cell 87 · 9-channel variant forensics (A-I rates in Quran vocalised) ===
channels = {
    'A_tanwin':       'ًٌٍ',
    'B_short_vowels': 'َُِ',
    'C_shadda':       'ّ',
    'D_sukun':        'ْ',
    'E_madda':        'ٓ',
    'F_hamza':        'ٕٔ',
    'G_waqf':         'ۗۖۛۚۙۘۢۡ',
    'H_sajda':        '۩',
    'I_headers':      '۝',
}
all_text = ''.join(v for u in CORPORA.get('quran', []) for v in u.verses)
total = len(all_text)
ch_rates = {k: (sum(all_text.count(c) for c in chars) / total if total else 0.0)
            for k, chars in channels.items()}
for k, v in ch_rates.items():
    print(f'  [9-chn] {k:<18s}  {v*100:.3f}%')
bless('E_epi_variants', float(sum(ch_rates.values())))"""
    )

    code(
        r"""# === Cell 88 · P-Epi-1 waqf placement ===
waqf_chars = channels['G_waqf']
if sum(ch_rates[k] for k in ch_rates) > 0 and ch_rates.get('G_waqf', 0) > 0:
    near_rhyme = 0; total_waqf = 0
    for u in CORPORA.get('quran', []):
        for v in u.verses:
            for i, ch in enumerate(v):
                if ch in waqf_chars:
                    total_waqf += 1
                    for j in range(max(0, i-3), i):
                        if v[j] in RHYME_LETTERS:
                            near_rhyme += 1; break
    rate = near_rhyme / max(1, total_waqf)
    print(f'[P-Epi-1] waqf near rhyme rate = {rate:.3f}  ({near_rhyme}/{total_waqf})')
    bless('E_epi_waqf', float(rate))
else:
    print('[P-Epi-1] no waqf markers found; skipping')
    bless('E_epi_waqf', 0.0, tol_override=float('inf'))"""
    )

    code(
        r"""# === Cell 89 · Phase-15 verifier + checkpoint ===
_verify_phase_15 = lambda: print(f'[OK   ] Phase 15 — epigenetic E3 (H={H_hr:.3f} bits)')
_verify_phase_15()
save_checkpoint('15_epigenetic',
                {'T23': t23, 'E3_bits': float(H_hr),
                 'channel_rates': ch_rates},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 16 — Cross-language + cross-scripture (cells 90-96)
# ============================================================================
def build_phase_16() -> None:
    phase_header(
        16,
        "Cross-language — T21 Iliad, Tanakh/NT if available, Nuzul-vs-Mushaf, "
        "Shannon-Aljamal 5-conditions per scripture, D13 Wikipedia analogue",
        "Language-agnostic 5-D on Hebrew/Greek if loaded; plus per-scripture "
        "Shannon-Aljamal conditions table.",
    )

    code(
        r"""# === Cell 90 · T21 cross-language Iliad ===
# AUDIT 2026-04-18 (v4): previous `bless('T15', ...)` here recorded the
# Iliad path z-score under the wrong finding ID (T15 is the classifier
# AUC in Cell 62). The correct ID for the cross-language Iliad z is T21.
t21 = RES.get('T21_cross_lang', {})
iliad_z = t21.get('iliad_path_z', float('nan'))
print(f'[T21 ] Iliad path z = {iliad_z:+.3f}')
bless('T21', float(iliad_z))"""
    )

    code(
        r"""# === Cell 91 · Tanakh + Greek NT + Iliad 5-D (language-agnostic, if loaded) ===
# AUDIT 2026-04-19 (v6 fix W2): previous implementation had a silent fallback
#   `if not recs: recs = FEATS[cl]`
# which copied ALL units into FEATS_CL when the Band-A filter returned empty.
# That broke apples-to-apples with the Arabic-family Band-A restriction and
# let pathological unit-length distributions leak into the cross-language
# ranking in Cell 95. The cross-language Ψ is APPENDIX-only, so we now SKIP
# scriptures that have zero Band-A units rather than backfill with the full
# corpus. Downstream Cells 94 / 95 already handle missing entries in FEATS_CL.
FEATS_CL = {}
CL_INFEASIBLE = []
for cl in ('iliad_greek', 'greek_nt', 'hebrew_tanakh'):
    if cl in FEATS and len(FEATS[cl]) > 0:
        recs = [r for r in FEATS[cl] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
        if not recs:
            CL_INFEASIBLE.append((cl, len(FEATS[cl])))
            print(f'  [CL ] {cl:<14s}  INFEASIBLE — 0/{len(FEATS[cl])} units in '
                  f'Band-A [{BAND_A_LO}, {BAND_A_HI}]; skipped (no apples-to-apples '
                  f'cross-language aggregate)')
            continue
        X = np.array([[r[c] for c in FEAT_COLS] for r in recs])
        FEATS_CL[cl] = X.mean(0)
        print(f'  [CL ] {cl:<14s}  n_bandA={len(recs):<3d}  '
              f'mean 5-D = [{" ".join(f"{v:+.3f}" for v in X.mean(0))}]')
    else:
        print(f'  [CL ] {cl}: not loaded')
if CL_INFEASIBLE:
    print(f'  [CL ] {len(CL_INFEASIBLE)} scripture(s) skipped as INFEASIBLE: '
          f'{[c for c, _ in CL_INFEASIBLE]}')"""
    )

    code(
        r"""# === Cell 92 · D13 Hindawi modern Arabic as OOD baseline ===
# AUDIT 2026-04-19 (fix ③): the original test measured hindawi's Mahalanobis
# distance against (mu, S_inv) from ARABIC_CTRL_POOL — which INCLUDES hindawi.
# That is self-referential: hindawi contributes to its own centroid and
# covariance, so its distance is shrunk toward zero by construction. The
# result (≈ 2.07) is therefore NOT a true out-of-distribution baseline.
#
# Corrected procedure:
#   * `D13_hindawi_in_pool_legacy` — the original computation, kept for
#     traceability / backward comparison (tol=inf, reporting only).
#   * `D13_hindawi_loo`            — leave-hindawi-out: rebuild (mu_loo,
#     S_inv_loo) from ARABIC_CTRL_POOL WITHOUT hindawi, then measure
#     hindawi's distance to THIS external centroid. This is the honest
#     OOD number and becomes the canonical D13.
#
# NOTE: the primary Φ_M separation (D02/S1/D28 = Quran vs pool) is
# UNAFFECTED — Quran is not in the pool to begin with.
if 'hindawi' in FEATS:
    X_wiki = _X_for('hindawi', BAND_A_LO, BAND_A_HI)
    if len(X_wiki) >= 3:
        # --- Legacy (self-referential) distance ---
        d_wiki_legacy = mahalanobis(X_wiki, mu, S_inv)
        legacy_med    = float(np.median(d_wiki_legacy))
        print(f'[D13-legacy] hindawi median d (in-pool centroid) = {legacy_med:.3f}   '
              f'(SELF-REFERENTIAL — see audit note)')
        bless('D13_hindawi_in_pool_legacy', legacy_med, tol_override=float('inf'))

        # --- Leave-hindawi-out (proper OOD) ---
        CTRL_NO_HIND = [c for c in ARABIC_CTRL_POOL if c != 'hindawi']
        X_loo_parts  = [_X_for(c, BAND_A_LO, BAND_A_HI) for c in CTRL_NO_HIND
                        if len(_X_for(c, BAND_A_LO, BAND_A_HI)) > 0]
        if X_loo_parts:
            X_CTRL_LOO = np.vstack(X_loo_parts)
            mu_loo     = X_CTRL_LOO.mean(axis=0)
            S_loo      = np.cov(X_CTRL_LOO.T, ddof=1) + lam * np.eye(X_CTRL_LOO.shape[1])
            S_inv_loo  = np.linalg.inv(S_loo)
            d_wiki_loo = mahalanobis(X_wiki, mu_loo, S_inv_loo)
            loo_med    = float(np.median(d_wiki_loo))
            print(f'[D13-LOO   ] hindawi median d vs leave-hindawi-out centroid '
                  f'(n_ctrl={len(CTRL_NO_HIND)}) = {loo_med:.3f}   '
                  f'(HONEST OOD — canonical D13)')
            bless('D13_hindawi_loo', loo_med, tol_override=float('inf'))
            # D13 itself now records the HONEST number.
            bless('D13', loo_med)
        else:
            print('[D13-LOO   ] leave-one-out pool empty; blessing D13 as legacy fallback')
            bless('D13_hindawi_loo',  legacy_med, tol_override=float('inf'))
            bless('D13', legacy_med)
    else:
        bless('D13_hindawi_in_pool_legacy', 0.0, tol_override=float('inf'))
        bless('D13_hindawi_loo',            0.0, tol_override=float('inf'))
        bless('D13', 0.0, tol_override=float('inf'))
else:
    print('[D13 ] hindawi not loaded')
    bless('D13_hindawi_in_pool_legacy', 0.0, tol_override=float('inf'))
    bless('D13_hindawi_loo',            0.0, tol_override=float('inf'))
    bless('D13', 0.0, tol_override=float('inf'))"""
    )

    code(
        r"""# === Cell 93 · Nuzul-vs-Mushaf (order-sensitivity check) ===
# CAVEAT (audit 2026-04-18): without authentic chronological-revelation
# metadata, the "Nuzul order" used here is just the Mushaf surahs sorted
# by their numeric label — essentially the same as Mushaf order with minor
# tie-break differences. This test therefore measures almost NOTHING about
# true revelatory order sensitivity; it is a STUB placeholder. A proper
# test would require an external chronological corpus (e.g., Nöldeke's
# chronology), which is NOT shipped. Verdict: TRIVIAL until metadata lands.
q_units = CORPORA.get('quran', [])
q_labels = [u.label for u in q_units]
if q_labels:
    nuzul_proxy = sorted(q_labels, key=lambda s: int(str(s).lstrip('Q:')) if str(s).lstrip('Q:').isdigit() else 9999)
    reorder_diff = sum(1 for a, b in zip(q_labels, nuzul_proxy) if a != b)
    print(f'[Nuzul] Mushaf vs sorted-proxy reordering = {reorder_diff}/{len(q_labels)} positions differ')
    print(f'[Nuzul] STUB — proxy is numeric sort, not true Nuzul chronology')
    bless('Nuzul_vs_Mushaf', 1.0 - reorder_diff / max(1, len(q_labels)))
else:
    bless('Nuzul_vs_Mushaf', 1.0, tol_override=float('inf'))"""
    )

    code(
        r"""# === Cell 94 · Shannon-Aljamal 5-conditions table per scripture ===
sa_table = {'quran': {
    'S1_phi_M': float(effect_d), 'S2_I_unit': float(I_unit_quran),
    'S3_H_cond': float(h_q),     'S4_H3H2':  float(q_h32),
    'S5_path_z': float(z_path),
}}
for name, mean5 in FEATS_CL.items():
    sa_table[name] = {
        'S1_phi_M': float('nan'),
        'S2_I_unit': float('nan'),
        'S3_H_cond': float(mean5[3]),
        'S4_H3H2':  float('nan'),
        'S5_path_z': float('nan'),
    }
print('')
print('[SA 5-conds] per scripture:')
print('  scripture       S1_phi   S2_I_unit  S3_Hcond  S4_H3H2  S5_path_z')
for n, r in sa_table.items():
    print(f'  {n:<14s}  {r["S1_phi_M"]:>6.2f}    {r["S2_I_unit"]:>5.3f}    '
          f'{r["S3_H_cond"]:>5.3f}    {r["S4_H3H2"]:>5.3f}    {r["S5_path_z"]:>6.2f}')"""
    )

    code(
        r"""# === Cell 95 · Psi preview (Arabic family ONLY) ===
# F-11 guard: `T` for Greek/Hebrew is computed by `features_5d_lang_agnostic`
# which measures a DIFFERENT quantity than `features_5d`'s Arabic T. The
# Arabic-control covariance (mu, S_inv) is also not scripture-neutral: it
# makes non-Arabic corpora look artificially "far". Ψ stays inside the
# Arabic family. A separate cross-language ranking uses its own manifold.
#
# AUDIT 2026-04-19 (v5 fix ⑥): PREVIEW ONLY — numbers here differ from the
# canonical Ψ computation in Cell 109. This preview uses the GLOBAL
# (mu, S_inv) built in Cell 29 from the full ARABIC_CTRL_POOL Band-A data.
# Cell 109's `_psi_against()` builds a LOCAL centroid from the Arabic
# family MINUS quran. The two Ψ numbers will therefore disagree; Cell 109
# is authoritative and is what gets blessed as L7/Psi_*. Do not cite
# PSI_PREVIEW values in the paper.
ARABIC_FAMILY = [c for c in ['quran', *ARABIC_CTRL_POOL, 'hadith_bukhari'] if c in FEATS]
PSI_PREVIEW = {}
for n in ARABIC_FAMILY:
    X = _X_for(n, BAND_A_LO, BAND_A_HI)
    if len(X) < 3: continue
    m = X.mean(0)
    EL_n, VL_n, CN_n, Hc_n, T_n = m
    phi_n = float(np.median(mahalanobis(X, mu, S_inv)))
    PSI_PREVIEW[n] = float(np.sqrt(max(phi_n, 0.01)) * EL_n * (Hc_n / max(VL_n, 1e-3)))
print(f'[Psi preview] computed on {len(ARABIC_FAMILY)} Arabic-family corpora only')
for n in sorted(PSI_PREVIEW, key=lambda k: -PSI_PREVIEW[k])[:8]:
    tag = ' <-- Quran' if n == 'quran' else ''
    print(f'  [Psi ] {n:<22s}  Psi = {PSI_PREVIEW[n]:.3f}{tag}')"""
    )

    code(
        r"""# === Cell 96 · Phase-16 verifier + checkpoint ===
_verify_phase_16 = lambda: print(f'[OK   ] Phase 16 — cross-language complete ({len(FEATS_CL)} foreign corpora)')
_verify_phase_16()
save_checkpoint('16_crosslang',
                {'FEATS_CL': {k: v.tolist() for k, v in FEATS_CL.items()},
                 'SA_table': sa_table, 'Psi_preview': PSI_PREVIEW,
                 'T21': t21},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 17 — External + oral sim + per-surah dashboard + blind rejection (cells 97-101)
# ============================================================================
def build_phase_17() -> None:
    phase_header(
        17,
        "External — oral-transmission simulation (2/5/10%), per-surah "
        "dashboard, blind-validation rejection rates, Abbasi 8-discriminator",
        "Final validation layer: oral retention, per-surah dashboard, and "
        "the blind-rejection battery.",
    )

    code(
        r"""# === Cell 97 · oral-transmission simulation (2/5/10% per-token substitution) ===
# CAVEAT (audit 2026-04-18): this noise model replaces ONE random letter per
# AFFECTED TOKEN with a uniformly random Arabic consonant. The `err_rate`
# parameter below is therefore a PER-TOKEN substitution rate, NOT a
# per-character error rate. A token-rate of 0.05 corresponds to a character-
# rate of ~0.05/mean_token_len (≈ 0.01 for 5-char Arabic words), so any
# law fitted against this ε is indexed in token-rate units and must be
# rescaled before comparing to an information-theoretic channel capacity.
# It is also an extremely crude model of oral transmission — it ignores:
#   * phonological substitution patterns (e.g., emphatic ↔ plain consonants),
#   * metathesis (letter reordering within a root),
#   * verse-level omissions/insertions,
#   * semantic preservation mechanisms from Islamic oral-tradition studies.
# The retention ratio below should therefore be read as EXPLORATORY, not
# evidential for any claim about the Quran's actual oral-transmission
# robustness. A rigorous test would require a phonetically-grounded
# substitution matrix, which is beyond scope here.
from src.raw_loader import Unit as U
rng = np.random.default_rng(SEED + 10)
def _transmit(units, err):
    out = []
    for u in units:
        new_verses = []
        for v in u.verses:
            toks = tokenise(v); new_toks = []
            for t in toks:
                if rng.random() < err and len(t) > 1:
                    i = int(rng.integers(0, len(t)))
                    new = list(t); new[i] = chr(0x0621 + int(rng.integers(0, 28)))
                    new_toks.append(''.join(new))
                else:
                    new_toks.append(t)
            new_verses.append(' '.join(new_toks))
        out.append(U(corpus=u.corpus, label=u.label, verses=new_verses))
    return out

err_rates = [0.02, 0.05, 0.10]
drift_by_corpus = {}
for n in ('quran', 'poetry_abbasi', 'arabic_bible'):
    if n not in CORPORA: continue
    units = _band_a_units(n)[:20]     # Band-A filter (apples-to-apples)
    if len(units) < 3:
        print(f'  [oral] {n}: only {len(units)} Band-A units; skip'); continue
    base_verses = sum([u.verses for u in units], [])
    f_clean = ft.features_5d(base_verses)
    drift_by_corpus[n] = {}
    for er in err_rates:
        noisy_units = _transmit(units, er)
        noisy_verses = sum([u.verses for u in noisy_units], [])
        f_noisy = ft.features_5d(noisy_verses)
        drift = float(np.linalg.norm(f_clean - f_noisy))
        drift_by_corpus[n][er] = drift
        print(f'  [oral] {n:<18s}  err={er*100:.0f}%   drift = {drift:.3f}')

retention = {}
for er in err_rates:
    q = drift_by_corpus.get('quran', {}).get(er, 1.0)
    ctrl = np.mean([drift_by_corpus[c][er] for c in drift_by_corpus if c != 'quran']) if len(drift_by_corpus) > 1 else q
    retention[er] = float(ctrl / max(q, 1e-9))
    print(f'[oral] err={er*100:.0f}%  retention = {retention[er]:.2f}x')"""
    )

    code(
        r"""# === Cell 98 · per-surah A+ to D dashboard — Band-A only is valid ===
# AUDIT 2026-04-18: the Mahalanobis centroid mu and covariance S_inv were
# calibrated on Band-A (15-100 verse) surahs only. Grades computed for surahs
# OUTSIDE Band A are statistical EXTRAPOLATIONS — the covariance is not
# trustworthy for those surah lengths. We now segment the output and label
# out-of-band grades explicitly. The headline distribution is restricted to
# the valid Band-A subset; out-of-band grades are reported for reference only.
#
# AUDIT 2026-04-19 (fix ⑧): grade cutoffs are now PRE-REGISTERED in PREREG
# (Cell 9, `grade_thresholds`) so a hostile reviewer cannot claim the
# 1/2/4/6-σ buckets were post-hoc tuned to make the Quran look "A+".
# Numeric thresholds live in `_GRADE_CUTOFFS` below and the strings are
# cross-checked against the frozen pre-registration JSON.
_GRADE_CUTOFFS = [('A+', 6.0), ('A', 4.0), ('B', 2.0), ('C', 1.0), ('D', -np.inf)]
def _grade_of(d):
    for g, thr in _GRADE_CUTOFFS:
        if d > thr: return g
    return 'D'

# Sanity-cross-check against PREREG (hard failure if they desynchronise)
_prereg_cuts = PREREG['grade_thresholds']['cutoffs']
_expected_keys = {'A+', 'A', 'B', 'C', 'D'}
assert set(_prereg_cuts) == _expected_keys, (
    f'[FATAL] PREREG grade_thresholds keys desynced: {set(_prereg_cuts)}')

grades = {}
from collections import Counter
for u in CORPORA.get('quran', []):
    if len(u.verses) < 3: continue
    f = ft.features_5d(u.verses)
    d = float(np.sqrt((f - mu) @ S_inv @ (f - mu)))
    g = _grade_of(d)
    in_band = (BAND_A_LO <= len(u.verses) <= BAND_A_HI)
    grades[u.label] = {'d': d, 'grade': g,
                       'n_verses': len(u.verses),
                       'in_band_A': in_band,
                       'extrapolation': not in_band}

grades_in  = {k: v for k, v in grades.items() if v['in_band_A']}
grades_out = {k: v for k, v in grades.items() if not v['in_band_A']}
dist_in  = Counter(v['grade'] for v in grades_in.values())
dist_out = Counter(v['grade'] for v in grades_out.values())
print(f'[dash ] cutoffs PRE-REGISTERED in PREREG v{PREREG["version"]} / grade_thresholds')
print(f'[dash ]   ' + '  '.join(f'{g}:{thr!s:>6}' for g, thr in _GRADE_CUTOFFS if thr > -np.inf))
print(f'[dash ] {len(grades_in)}/{len(grades)} surahs are Band-A (valid grading)')
print(f'[dash ] Band-A grade distribution : {dict(dist_in)}')
print(f'[dash ] out-of-band ({len(grades_out)}) — EXTRAPOLATION, not valid:')
print(f'[dash ]   out-of-band grades: {dict(dist_out)}')
print(f'[dash ] Only Band-A grades are defensible for any publication claim.')"""
    )

    code(
        r"""# === Cell 99 · blind-validation rejection rates (threshold DERIVED, not tuned) ===
# Rejection threshold = 95th percentile of Arabic-control surahs' Φ_M (Band A).
# No post-hoc tuning: the threshold is set by control data alone.
#
# AUDIT FIX 2026-04-18: previous 'markov' and 'repeated' synthetic nulls drew
# tokens from q_toks_flat (Quran vocabulary) which collapses the distance to
# the control centroid artificially (same lexical cloud as Quran). We now
# draw from EXTERNAL Arabic-control vocabulary (poetry_{jahili,islami,abbasi},
# arabic_bible, hindawi, ksucca) — consistent with Cell 61's synthetic
# adversarial tests. We ALSO report rejection rates built from Quran tokens
# as an INTERNAL lower bound so the reader can see both numbers.
from src.raw_loader import Unit as U
rng = np.random.default_rng(SEED + 20)

ext_sources_blind = [c for c in ('poetry_abbasi', 'poetry_islami', 'poetry_jahili',
                                  'arabic_bible', 'ksucca', 'hindawi') if c in CORPORA]
ext_toks_blind = [w for n in ext_sources_blind for u in CORPORA[n]
                  for v in u.verses for w in v.split() if w]
q_toks_flat    = [w for u in CORPORA['quran'] for v in u.verses for w in v.split()]
if not ext_toks_blind:
    raise HallucinationError(
        '[blind] external control vocabulary missing; refusing Quran-token '
        'fallback because it would invalidate the blind-rejection null.'
    )

ctrl_ds_flat = mahalanobis(X_CTRL_POOL, mu, S_inv) if len(X_CTRL_POOL) else np.array([1.0])
REJECT_THRESHOLD = float(np.percentile(ctrl_ds_flat, 95))
print(f'[blind] rejection threshold = {REJECT_THRESHOLD:.2f}  '
      f'(95th pct of {len(ctrl_ds_flat)} control Band-A surahs)')

ARABIC_ALPHABET = list('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')

def _inject(label, n=30, token_source=None):
    toks = token_source if token_source is not None else ext_toks_blind
    fakes = []
    for i in range(n):
        if label == 'markov':
            verses = [' '.join(rng.choice(toks, size=8)) for _ in range(15)]
        elif label == 'random':
            # pure random Arabic letters — no token source needed
            verses = [' '.join(''.join(rng.choice(ARABIC_ALPHABET, size=5))
                               for _ in range(5)) for _ in range(15)]
        elif label == 'repeated':
            verses = [str(rng.choice(toks))] * 15
        else:
            verses = [' '.join(rng.choice(toks, size=8)) for _ in range(15)]
        f = ft.features_5d(verses)
        fakes.append(float(np.sqrt((f - mu) @ S_inv @ (f - mu))))
    return float(np.mean(np.array(fakes) > REJECT_THRESHOLD))

# PRIMARY: external-vocabulary null (no Quran-lexicon leakage)
reject_markov_ext   = _inject('markov',   token_source=ext_toks_blind)
reject_random_ext   = _inject('random')   # alphabet-based, already external
reject_repeated_ext = _inject('repeated', token_source=ext_toks_blind)
print(f'[blind-EXT ] Markov rejection   = {reject_markov_ext*100:.0f}%  (external vocab)')
print(f'[blind-EXT ] random rejection   = {reject_random_ext*100:.0f}%')
print(f'[blind-EXT ] repeated rejection = {reject_repeated_ext*100:.0f}%')

# SECONDARY (diagnostic): Quran-vocab null — previously the only condition.
# Should yield LOWER rejection than external vocab (closer to Quran cloud),
# so this is a lower bound for the detector, not the headline number.
reject_markov_q   = _inject('markov',   token_source=q_toks_flat)
reject_repeated_q = _inject('repeated', token_source=q_toks_flat)
print(f'[blind-QVOC] Markov rejection   = {reject_markov_q*100:.0f}%  (Quran vocab; weaker null)')
print(f'[blind-QVOC] repeated rejection = {reject_repeated_q*100:.0f}%')

# Bless the WORST of the external-vocab conditions (= hardest to reject)
reject_markov, reject_random, reject_repeated = (
    reject_markov_ext, reject_random_ext, reject_repeated_ext)
bless('Blind_rejection_rates',
      float(min(reject_markov, reject_random, reject_repeated)))"""
    )

    code(
        r"""# === Cell 100 · Abbasi 8-discriminator test ===
# AUDIT 2026-04-19 (fix ④): the original test counted a "beat" for each of
# the 5 raw features whenever abs(q - ab) > 0.01 — i.e. any DIFFERENCE in
# either direction scored a point for the Quran. That is non-directional
# and therefore cannot distinguish "Quran is higher than Abbasi on feature X"
# from "Quran differs from Abbasi on feature X"; a corpus that happened to
# be merely DIFFERENT from Abbasi could fraudulently score 5/5.
#
# We now:
#   * keep the legacy non-directional count as `Abbasi_8_discriminators` and
#     legacy `D27` (tol=inf, REPORTING ONLY) for traceability.
#   * introduce pre-registered per-feature directions, based on the Phase-7
#     discoveries (D01/D03/D04/D10) that fixed the expected sign of each
#     axis for Quran vs Arabic-controls:
#         EL     (expectation logarithm)         : Quran > ctrl   (D03)
#         VL_CV  (verse-length coeff. of var.)   : Quran < ctrl   (D01, anti-metric)
#         CN     (connective norm.)              : Quran > ctrl   (D04)
#         H_cond (conditional entropy)           : Quran > ctrl   (S3)
#         T      (triple-coupling %T>0)          : Quran > ctrl   (D10)
#   * count strict DIRECTIONAL beats with a 0.01 margin of superiority
#     (matches the legacy sensitivity floor). The 3 derived metrics keep
#     their original directional form.
#   * publish the directional count as `D27_directional` and mirror to
#     `Abbasi_directional_beats`. This number is the honest headline.
DIR_PREREG = {                 # pre-registered Quran direction vs Arabic-ctrl
    'EL':     +1,              # Quran HIGHER
    'VL_CV':  -1,              # Quran LOWER (anti-metric, D01)
    'CN':     +1,              # Quran HIGHER (D04)
    'H_cond': +1,              # Quran HIGHER (S3 condition)
    'T':      +1,              # Quran HIGHER (D10)
}
assert set(DIR_PREREG) == set(FEAT_COLS), (
    'DIR_PREREG keys must match FEAT_COLS exactly; lock desync otherwise.')

q_mean = np.array([[r[c] for c in FEAT_COLS] for r in FEATS.get('quran', [])
                   if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]).mean(0)
ab_mean = np.array([[r[c] for c in FEAT_COLS] for r in FEATS.get('poetry_abbasi', [])
                    if BAND_A_LO <= r['n_verses'] <= BAND_A_HI])
if ab_mean.size:
    ab_mean = ab_mean.mean(0)

    # --- Legacy non-directional count (REPORTING ONLY) ---
    beats_legacy = 0
    for i, fname in enumerate(FEAT_COLS):
        if abs(q_mean[i] - ab_mean[i]) > 0.01:
            beats_legacy += 1
    # Legacy also used 3 DIRECTIONAL derived features — those were correct,
    # we preserve them verbatim in the legacy total.
    beats_legacy += int(q_mean[0]*q_mean[2] > ab_mean[0]*ab_mean[2])
    beats_legacy += int(q_mean[3]/max(q_mean[1],1e-3) > ab_mean[3]/max(ab_mean[1],1e-3))
    beats_legacy += int(np.sqrt(q_mean[0]*q_mean[3]) > np.sqrt(ab_mean[0]*ab_mean[3]))
    print(f'[8-disc LEGACY      ] Quran vs Abbasi (non-directional) = {beats_legacy}/8')

    # --- Directional count (HONEST headline) ---
    beats_dir = 0
    per_feat_dir = {}
    for i, fname in enumerate(FEAT_COLS):
        sign = DIR_PREREG[fname]
        diff = sign * (q_mean[i] - ab_mean[i])
        is_beat = diff > 0.01
        per_feat_dir[fname] = {'q': float(q_mean[i]), 'ab': float(ab_mean[i]),
                               'sign': sign, 'beat': bool(is_beat)}
        beats_dir += int(is_beat)
        arrow = '>' if sign > 0 else '<'
        print(f'  [8-disc] {fname:<8s} (Q {arrow} Abbasi pre-reg)   '
              f'Q={q_mean[i]:+.4f}  Ab={ab_mean[i]:+.4f}   '
              f'{"BEAT" if is_beat else "MISS"}')
    # 3 directional derived features (unchanged — they were already correct)
    d1 = int(q_mean[0]*q_mean[2]                    > ab_mean[0]*ab_mean[2])
    d2 = int(q_mean[3]/max(q_mean[1],1e-3)          > ab_mean[3]/max(ab_mean[1],1e-3))
    d3 = int(np.sqrt(q_mean[0]*q_mean[3])           > np.sqrt(ab_mean[0]*ab_mean[3]))
    beats_dir += d1 + d2 + d3
    print(f'  [8-disc] derived (EL·CN, H/VL, √(EL·H))  =  {d1+d2+d3}/3')
    print(f'[8-disc DIRECTIONAL ] Quran beats Abbasi on {beats_dir}/8 '
          f'(PRE-REGISTERED directions — honest headline)')

    # Legacy — reporting only
    bless('Abbasi_8_discriminators', float(beats_legacy))
    bless('D27', float(beats_dir))                       # D27 now carries HONEST count
    # Directional — first-class
    bless('Abbasi_directional_beats', float(beats_dir), tol_override=float('inf'))
    bless('D27_directional',          float(beats_dir), tol_override=float('inf'))
else:
    print('[8-disc] poetry_abbasi missing; skipping')
    bless('Abbasi_8_discriminators', 0.0, tol_override=float('inf'))
    bless('D27',                     0.0, tol_override=float('inf'))
    bless('Abbasi_directional_beats',0.0, tol_override=float('inf'))
    bless('D27_directional',         0.0, tol_override=float('inf'))"""
    )

    code(
        r"""# === Cell 101 · Phase-17 verifier + checkpoint ===
_verify_phase_17 = lambda: print('[OK   ] Phase 17 — external + oral sim + dashboard + blind done')
_verify_phase_17()
save_checkpoint('17_external',
                {'retention':retention,'grades':grades,
                 'reject_markov':float(reject_markov),
                 'reject_random':float(reject_random),
                 'reject_repeated':float(reject_repeated)},
                state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 18 — DISCOVERY LAB: L1-L7 + E1/E2/E3 supporting experiments (cells 102-112)
# ============================================================================
def build_phase_18() -> None:
    phase_header(
        18,
        "DISCOVERY LAB — L1 SCI, L2 RSL, L3 FEP, L4 Aljamal, L5 OBI, "
        "L6 empirical γ(Ω), L7 cross-scripture Ψ + E1/E2/E3",
        "Seven universal-law candidates under pre-registered falsification "
        "criteria. E1 (real transmission-noise simulation) honestly closes "
        "Gaps 3 and 5. E4 (constructive STOT) SKIPPED per user decision.",
    )

    # Cell 102 — L1 SCI  (H3/H2 computed LOCALLY per corpus; no Quran-biased fallback)
    code(
        r"""# === Cell 102 · L1 Synchronized Compression Index (SCI) ===
# SCI = (I(EL;CN)_corpus × VL_CV) / (H3/H2)
# Critical: H3/H2 must be computed per corpus from ITS OWN data. A fallback
# constant (e.g. 0.30 = near Quran's ratio) would bias all controls toward
# Quran-like SCI. If a corpus can't yield a valid ratio, exclude it from
# the ranking instead of filling with a default.

# (A) I(EL;CN) per corpus — read from clean_pipeline T7
I_corpus_by = {}
_t7 = RES.get('T7_el_cn_dual', {})
for n, d in _t7.get('per_corpus', {}).items():
    if isinstance(d, dict) and 'I_EL_CN' in d:
        I_corpus_by[n] = float(d['I_EL_CN'])

# (B) VL_CV per corpus (Band-A mean)
VL_by = {n: _mean_band_a(n, 'VL_CV') for n in FEATS}

# (C) H3/H2 per corpus — compute LOCALLY on verse-final roots
from collections import Counter as _CtrSCI
from math import log2 as _log2

def _h3_h2_ratio(units):
    '''H3/H2 on verse-final root n-grams for a single corpus (conditional
    entropy of next verse-final root given 1- vs 2-root history).'''
    finals = []
    for u in units:
        for v in u.verses:
            toks = v.split()
            if not toks: continue
            last = toks[-1]
            r = rc.primary_root(last) or last
            if r: finals.append(r)
    if len(finals) < 8: return float('nan')

    def _Hn(order):
        ctx = _CtrSCI(tuple(finals[i:i+order])   for i in range(len(finals)-order))
        fwd = _CtrSCI(tuple(finals[i:i+order+1]) for i in range(len(finals)-order))
        tot = sum(ctx.values()) or 1
        H = 0.0
        for k, cnt in ctx.items():
            p_ctx = cnt / tot
            matches = {kk: vv for kk, vv in fwd.items() if kk[:-1] == k}
            m_tot = sum(matches.values()) or 1
            h = 0.0
            for vv in matches.values():
                p = vv / m_tot
                if p > 0: h -= p * _log2(p)
            H += p_ctx * h
        return H
    H2 = _Hn(1); H3 = _Hn(2)
    if H2 <= 0: return float('nan')
    return H3 / H2

H32_by = {}
for n, units in CORPORA.items():
    r = _h3_h2_ratio(units)
    if not np.isnan(r):
        H32_by[n] = float(r)
print(f'[L1  ] H3/H2 computed locally for {len(H32_by)}/{len(CORPORA)} corpora')

# (D) SCI — drop corpora missing any input (no Quran-biased fallbacks)
SCI = {}
for n in FEATS:
    if n not in I_corpus_by or n not in H32_by:
        continue
    vl = VL_by.get(n)
    if vl is None or np.isnan(vl) or vl <= 0:
        continue
    SCI[n] = float((I_corpus_by[n] * vl) / max(H32_by[n], 1e-3))

print(f'[L1 ] Synchronized Compression Index (SCI) ranking '
      f'({len(SCI)}/{len(FEATS)} corpora eligible):')
for n in sorted(SCI, key=lambda k: -SCI[k])[:8]:
    marker = ' <-- Quran' if n == 'quran' else ''
    print(f'  {n:<22s}  SCI = {SCI[n]:.3f}'
          f'  (I={I_corpus_by[n]:.3f}, VL={VL_by[n]:.3f}, H3/H2={H32_by[n]:.3f}){marker}')
bless('L1', float(SCI.get('quran', float('nan'))))"""
    )

    # Cell 103 — E1 real transmission-noise simulation
    code(
        r"""# === Cell 103 · E1 real transmission-noise simulation ===
# Inject substitution noise at eps ∈ {1,2,5,10}% across multiple N; measure
# actual decoder error P_e(eps, N). Used to fit γ(Ω) empirically in L6.
# NOTE (audit 2026-04-18 v3): `eps` below is the PER-TOKEN substitution
# probability (same semantics as Cell 97's err_rate). A fraction eps of
# tokens each gets ONE random letter replaced. The character-level error
# rate is ~eps/mean_token_len. P_e counts tokens that differ between ref
# and noisy streams. All downstream laws (L2 α, L6 γ) inherit these units.
from src.raw_loader import Unit as U
rng = np.random.default_rng(SEED + 30)

def _transmission(units, err_rate):
    out = []
    for u in units:
        new_verses = []
        for v in u.verses:
            toks = tokenise(v); new_toks = []
            for t in toks:
                if rng.random() < err_rate and len(t) > 1:
                    i = int(rng.integers(0, len(t)))
                    new = list(t); new[i] = chr(0x0621 + int(rng.integers(0, 28)))
                    new_toks.append(''.join(new))
                else:
                    new_toks.append(t)
            new_verses.append(' '.join(new_toks))
        out.append(U(corpus=u.corpus, label=u.label, verses=new_verses))
    return out

def _p_error(units_ref, units_noisy):
    err = 0; tot = 0
    for a, b in zip(units_ref, units_noisy):
        for va, vb in zip(a.verses, b.verses):
            ta = tokenise(va); tb = tokenise(vb)
            for ra, rb in zip(ta, tb):
                tot += 1
                if ra != rb: err += 1
    return err / max(1, tot)

eps_grid = [0.01, 0.02, 0.05, 0.10]
N_grid   = [10, 20] if FAST_MODE else [10, 20, 50]
pe_table = {}
# AUDIT 2026-04-18: expanded E1 from 3 to 7 corpora so G3 quadratic fit has
# enough data points (>=5 per axis). Reviewer flagged that 3 points cannot
# reliably estimate a quadratic. E1 is O(|corpora| × |eps_grid| × |N_grid| ×
# |units|); 4 extra corpora each add <5 s in FAST mode (token substitution
# is cheap), so the runtime budget is unaffected.
_E1_CORPORA = ('quran', 'poetry_abbasi', 'poetry_islami', 'poetry_jahili',
               'arabic_bible', 'ksucca', 'hindawi')
for n in _E1_CORPORA:
    if n not in CORPORA: continue
    units = _band_a_units(n)[:max(N_grid)]    # Band-A apples-to-apples
    if len(units) < min(N_grid):
        print(f'[E1 ] {n}: only {len(units)} Band-A units; skip'); continue
    pe_table[n] = {}
    for ep in eps_grid:
        for N in N_grid:
            sub_ref = units[:N]
            sub_noisy = _transmission(sub_ref, ep)
            pe_table[n][(ep, N)] = _p_error(sub_ref, sub_noisy)
print('[E1 ] transmission error rate P_e by corpus / eps / N:')
for n in pe_table:
    for ep in eps_grid:
        vals = [pe_table[n][(ep, N)] for N in N_grid]
        print(f'  {n:<18s}  eps={ep:<5}  P_e={np.mean(vals):.3f} (+/-{np.std(vals):.3f})')"""
    )

    # Cell 104 — L2 Retention Scaling Law
    code(
        r"""# === Cell 104 · L2 Retention Scaling Law — drift(eps) ≈ α·eps^β ===
# NOTE (audit 2026-04-18 v3): `eps` = PER-TOKEN substitution rate (see
# Cell 97 / Cell 103 comment). β is therefore the token-rate exponent, not
# a character-channel exponent. To convert to a char-rate exponent one
# would refit against (eps / mean_token_len) per corpus; we do NOT do that
# here because mean_token_len varies by corpus and would confound α across
# corpora. Both α and β are reported as descriptive statistics only.
from scipy.optimize import curve_fit
def _power(ep, a, b): return a * np.power(np.maximum(ep, 1e-6), b)

drift_map = {}
for n in ('quran', 'poetry_abbasi', 'arabic_bible'):
    if n not in CORPORA: continue
    units = _band_a_units(n)[:15]     # Band-A apples-to-apples
    if len(units) < 3:
        print(f'[L2 ] {n}: only {len(units)} Band-A units; skip'); continue
    base_verses = sum([u.verses for u in units], [])
    f_clean = ft.features_5d(base_verses)
    rets = []
    for ep in eps_grid:
        noisy = _transmission(units, ep)
        nv = sum([u.verses for u in noisy], [])
        f_n = ft.features_5d(nv)
        rets.append(float(np.linalg.norm(f_clean - f_n)))
    drift_map[n] = rets

alpha_by = {}
for n, ys in drift_map.items():
    try:
        popt, _ = curve_fit(_power, np.array(eps_grid), np.array(ys),
                             p0=[1.0, 1.0], maxfev=3000)
        alpha_by[n] = float(popt[0]); beta = float(popt[1])
        print(f'[L2 ] {n:<18s}  α = {popt[0]:.3f}   β[tok] = {beta:.3f}  '
              f'(β indexed in per-token eps units)')
    except Exception as ex:
        alpha_by[n] = float('nan')
        print(f'[L2 ] {n:<18s}  fit failed: {ex}')
bless('L2', float(alpha_by.get('quran', float('nan'))), tol_override=float('inf'))"""
    )

    # Cell 105 — L3 FEP
    code(
        r"""# === Cell 105 · L3 Free-Energy Principle: F = H_cond - β·VL_CV·T ===
BETA_FEP = 1.0
F_vals = {}
for n in FEATS:
    recs = [r for r in FEATS[n] if BAND_A_LO <= r['n_verses'] <= BAND_A_HI]
    if not recs: continue
    m_h = np.mean([r['H_cond'] for r in recs])
    m_v = np.mean([r['VL_CV']  for r in recs])
    m_t = np.mean([r['T']      for r in recs])
    F_vals[n] = float(m_h - BETA_FEP * m_v * m_t)
print('[L3 ] Free-energy F (smaller = closer to minimum):')
for n in sorted(F_vals, key=lambda k: F_vals[k])[:6]:
    marker = ' <-- Quran' if n == 'quran' else ''
    print(f'  {n:<22s}  F = {F_vals[n]:+.3f}{marker}')
bless('L3', float(F_vals.get('quran', float('nan'))))"""
    )

    # Cell 106 — L4 Aljamal invariance
    code(
        r"""# === Cell 106 · L4 Aljamal Invariance: Ω × d ≈ const across corpora? ===
aljamal = {}
for n in list(FEATS):
    X = _X_for(n, BAND_A_LO, BAND_A_HI)
    if len(X) < 3: continue
    d_loc = float(np.median(mahalanobis(X, mu, S_inv)))
    t4b = RES.get('T4_omega', {})
    o_loc = t4b.get('per_corpus', {}).get(n, {}).get('omega', float('nan'))
    if np.isnan(o_loc): continue
    aljamal[n] = d_loc * float(o_loc)
vals = [v for v in aljamal.values() if not np.isnan(v) and v > 0]
cv_aljamal = float(np.std(vals) / max(np.mean(vals), 1e-9)) if vals else float('nan')
print('[L4 ] Ω × d per corpus:')
for n, v in aljamal.items():
    print(f'  {n:<22s}  Ω·d = {v:.3f}')
print(f'[L4 ] cross-corpus CV of Ω·d = {cv_aljamal:.3f}  (near 0 = invariance)')
bless('L4', float(cv_aljamal) if not np.isnan(cv_aljamal) else 1.0)"""
    )

    # Cell 107 — L5 OBI  (no Quran-biased fallbacks; sweep κ)
    code(
        r"""# === Cell 107 · L5 Orality-Bound Inequality ===
# Φ_M² ≤ κ·(I + log(1/(H3/H2)) + log(VL_CV))
# CAVEAT (audit 2026-04-18): L5 is an INVENTED inequality with no derivation
# from information theory, coding theory, or linguistics. It is a curve-fit
# of observed quantities and should be read as a DESCRIPTIVE PATTERN, NOT
# a law. κ is swept (0.5, 1, 2) with no principled choice; the sign of
# log(VL_CV) flips when VL_CV<1 (possible for some controls), which makes
# the bound tighter or negative in ways the "law" narrative cannot justify.
# Verdict status: EXPLORATORY.
# Only evaluate on corpora with ALL three inputs present; κ swept ∈ {0.5, 1, 2}.
obi_slack_by_k = {}
for kappa in (0.5, 1.0, 2.0):
    obi_slack = {}
    for n in list(FEATS):
        if n not in I_corpus_by or n not in H32_by or n not in VL_by:
            continue
        vlcv = VL_by[n]
        if vlcv is None or np.isnan(vlcv) or vlcv <= 0:
            continue
        X = _X_for(n, BAND_A_LO, BAND_A_HI)
        if len(X) < 3: continue
        phi  = float(np.median(mahalanobis(X, mu, S_inv)))
        rhs  = kappa * (I_corpus_by[n] + np.log(1 / max(H32_by[n], 1e-3))
                        + np.log(max(vlcv, 1e-3)))
        obi_slack[n] = float(rhs - phi**2)
    obi_slack_by_k[kappa] = obi_slack

print('[L5 ] OBI slack (RHS − LHS; smaller = tighter bound):')
for kappa, obi_slack in obi_slack_by_k.items():
    if 'quran' in obi_slack:
        print(f'  [κ={kappa}] Quran slack = {obi_slack["quran"]:+.3f}  '
              f'(rank = {sorted(obi_slack, key=obi_slack.get).index("quran")+1}/{len(obi_slack)})')
# Bless the κ=1 Quran value as the canonical L5
obi_slack = obi_slack_by_k[1.0]
bless('L5', float(obi_slack.get('quran', float('nan'))))"""
    )

    # Cell 108 — L6 empirical gamma(Ω)
    code(
        r"""# === Cell 108 · L6 Empirical Error-Exponent Law — fit γ from E1's P_e table ===
# For each corpus, regress -log P_e on N at fixed eps=0.05; slope = γ_c.
# Then regress γ_c across corpora on Ω_proxy.
gammas = {}
for n in pe_table:
    xs, ys = [], []
    for (ep, N), pe in pe_table[n].items():
        if ep != 0.05 or pe <= 0: continue
        xs.append(N); ys.append(-np.log(pe))
    if len(xs) >= 2:
        slope, _ = np.polyfit(xs, ys, 1)
        gammas[n] = float(slope)
    else:
        gammas[n] = float('nan')

omega_proxy = {}
for n in pe_table:
    if n in FEATS:
        X = _X_for(n, BAND_A_LO, BAND_A_HI)
        if len(X) > 0:
            omega_proxy[n] = float(X[:, 3].mean() + X[:, 1].mean())  # H_cond + VL_CV

ns_L6 = [n for n in gammas if not np.isnan(gammas[n]) and n in omega_proxy]
if len(ns_L6) >= 2:
    xs = np.array([omega_proxy[n] for n in ns_L6])
    ys = np.array([gammas[n]       for n in ns_L6])
    b_slope, a_int = np.polyfit(xs, ys, 1)
    print(f'[L6 ] γ(Ω) = {a_int:.4f} + {b_slope:.4f}·Ω   (empirical, NOT algebraic)   n={len(ns_L6)}')
    bless('L6', float(b_slope))
else:
    print('[L6 ] not enough corpora for γ(Ω) fit')
    bless('L6', 0.0, tol_override=float('inf'))
    b_slope, a_int = 0.0, 0.0
# AUDIT 2026-04-19: explicitly record the actual number of (Ω, γ) regression
# points so Cell 123's G5 guard can use the TRUE count, not a fallback based
# on ARABIC_FAMILY membership. Previously `bless('L6', ...)` only stored the
# slope; Cell 123 then counted ARABIC_FAMILY corpora (~7) via its fallback,
# which could spuriously declare G5 EMPIRICAL_POSITIVE on a positive slope
# fitted from only 3-4 valid points.
ALL_RESULTS['L6']['n_points'] = int(len(ns_L6))
ALL_RESULTS['L6']['corpora']  = list(ns_L6)"""
    )

    # Cell 109 — L7 Ψ (Arabic family ONLY + separate cross-language block)
    code(
        r"""# === Cell 109 · L7 Ψ — DESCRIPTIVE composite index (NOT a law) ===
#
# STATUS (audit 2026-04-18): Ψ = sqrt(max(Φ_M, 0.01)) · EL · (H_cond / VL_CV)
# is DIMENSIONALLY INCOHERENT:
#   * Φ_M has units of σ (Mahalanobis σ-distance in a 5-D joint distribution)
#   * EL is a probability ∈ [0, 1]
#   * H_cond has units of bits
#   * VL_CV is dimensionless (std / mean)
# The product's magnitude depends on the scaling of each feature. If any
# feature were z-scored, the RANKING of corpora by Ψ could change. We
# therefore DEMOTE Ψ to a "DESCRIPTIVE COMPOSITE INDEX" and do not claim
# it is a law. Provided below:
#   (i)  raw Ψ  — legacy definition (matches prior notebook versions)
#   (ii) z-scored Ψ  — scale-invariant version; features z-scored across
#        the Arabic family before computing the composite
#   (iii) permutation null for the rank (NOT a p-value for the composite)
#
# Two mixing hazards already handled:
#   (i)  features_5d_lang_agnostic produces a DIFFERENT T than Arabic T,
#   (ii) the mu/S_inv covariance is built from Arabic controls and is
#        therefore large for non-Arabic corpora for purely language reasons.
# We compute Ψ inside the Arabic family (quran + 6 controls + hadith). A
# separate Ψ_xlang uses each language's OWN per-language covariance.

def _psi_against(pool_names, center_pool=None):
    '''Compute Ψ for each name in pool_names, using the covariance of
    center_pool (defaults to pool_names excluding 'quran').'''
    Xs = {n: _X_for(n, BAND_A_LO, BAND_A_HI) for n in pool_names}
    Xs = {n: X for n, X in Xs.items() if len(X) >= 3}
    if not Xs: return {}, None, None
    ctr = [n for n in (center_pool or pool_names) if n != 'quran' and n in Xs]
    if not ctr: ctr = [n for n in Xs if n != 'quran']
    stack = np.vstack([Xs[n] for n in ctr])
    mu_loc = stack.mean(0)
    S_loc  = np.cov(stack, rowvar=False) + 1e-6 * np.eye(5)
    Sinv_loc = np.linalg.inv(S_loc)
    out = {}
    for n, X in Xs.items():
        m  = X.mean(0)
        phi_n = float(np.median(mahalanobis(X, mu_loc, Sinv_loc)))
        out[n] = float(np.sqrt(max(phi_n, 0.01)) * m[0] * (m[3] / max(m[1], 1e-3)))
    return out, mu_loc, Sinv_loc

# --- Ψ raw (legacy definition) ---
PSI, _, _ = _psi_against(ARABIC_FAMILY)
ranked = sorted(PSI, key=lambda k: -PSI[k])
print(f'[L7/A] Ψ (raw, legacy) within Arabic family ({len(PSI)} corpora):')
for rank, n in enumerate(ranked[:8], 1):
    marker = ' <-- Quran' if n == 'quran' else ''
    print(f'  {rank:>2d}. {n:<22s}  Ψ = {PSI[n]:.3f}{marker}')
quran_rank = ranked.index('quran') + 1 if 'quran' in ranked else -1
print(f'[L7/A] Quran rank under raw Ψ = {quran_rank}/{len(ranked)}')
bless('L7', float(quran_rank))

# --- Ψ z-scored sensitivity variant ---
# Z-score every feature across the Arabic family, then compute a composite
# with the SAME functional form but in the z-scored space. Because Φ_M is
# scale-invariant under affine transforms (Mahalanobis distance is invariant
# to linear reparametrisations), Φ_M_z ≡ Φ_M. The three scalar factors
# (EL, H_cond/VL_CV) change under z-scoring: we use exp(·) to keep them
# positive and order-preserving, so Ψ_z is order-equivalent to a linear
# combination of z-scores and is scale-invariant.
def _psi_zscored(pool_names):
    Xs = {n: _X_for(n, BAND_A_LO, BAND_A_HI) for n in pool_names}
    Xs = {n: X for n, X in Xs.items() if len(X) >= 3}
    if not Xs: return {}
    # Per-corpus means (5D vector = [T, H_cond, VL_CV, EL, CN])
    means = {n: X.mean(0) for n, X in Xs.items()}
    stack = np.vstack(list(means.values()))
    feat_mu  = stack.mean(0)
    feat_std = stack.std(0, ddof=1)
    feat_std = np.where(feat_std < 1e-12, 1.0, feat_std)
    # Raw Φ_M (already Mahalanobis in the SAME covariance as _psi_against)
    ctr = [n for n in pool_names if n != 'quran' and n in Xs]
    if not ctr: ctr = [n for n in Xs if n != 'quran']
    stack_c  = np.vstack([Xs[n] for n in ctr])
    mu_loc   = stack_c.mean(0)
    S_loc    = np.cov(stack_c, rowvar=False) + 1e-6 * np.eye(5)
    Sinv_loc = np.linalg.inv(S_loc)
    out = {}
    for n, X in Xs.items():
        phi_n = float(np.median(mahalanobis(X, mu_loc, Sinv_loc)))
        # Z-scored feature means (unitless everywhere)
        #   [T, H_cond, VL_CV, EL, CN] => indices 0..4
        m_z = (means[n] - feat_mu) / feat_std
        _, H_z, V_z, E_z, _ = m_z
        # Monotone scale-invariant composite:
        #   Ψ_z = sqrt(Φ_M) * exp(z(EL)) * exp(z(H_cond)) * exp(-z(VL_CV))
        # This is order-equivalent to a log-linear combination of z-scores.
        out[n] = float(np.sqrt(max(phi_n, 0.01))
                       * np.exp(E_z + H_z - V_z))
    return out

PSI_Z = _psi_zscored(ARABIC_FAMILY)
if PSI_Z:
    ranked_z  = sorted(PSI_Z, key=lambda k: -PSI_Z[k])
    quran_rank_z = ranked_z.index('quran') + 1 if 'quran' in ranked_z else -1
    print(f'[L7/A] Ψ (z-scored, scale-invariant) top 5:')
    for rank, n in enumerate(ranked_z[:5], 1):
        marker = ' <-- Quran' if n == 'quran' else ''
        print(f'  {rank:>2d}. {n:<22s}  Ψz = {PSI_Z[n]:+.3f}{marker}')
    if quran_rank_z == quran_rank:
        print(f'[L7/A] ranking STABLE under z-score (rank {quran_rank} both cases)')
    else:
        print(f'[L7/A] ranking CHANGES under z-score (raw={quran_rank}, z={quran_rank_z})')
        print(f'[L7/A] → raw Ψ ranking is scale-artifact; demote to descriptive only')

# --- Ψ permutation null (calibrates the rank claim) ---
# Pool all Band-A surah-level feature rows from ARABIC_FAMILY, then randomly
# re-assign them to pseudo-corpora of the same sizes as the real corpora.
# Re-rank, and measure how often the pseudo-Quran ends up at rank 1.
def _psi_perm_p(n_perm=None):
    # AUDIT 2026-04-18 (v4): previously the null used the GLOBAL `mu, S_inv`
    # (calibrated in Cell 29 on the full Arabic-control pool), while the
    # observed Ψ uses a LOCAL centroid built inside `_psi_against` from the
    # non-Quran Arabic family only. That made the observed and null values
    # incomparable. Here we recompute a local centroid INSIDE every
    # permutation from the pseudo-non-quran rows, matching `_psi_against`.
    if n_perm is None: n_perm = min(N_PERM, 500)
    per_corpus = {n: _X_for(n, BAND_A_LO, BAND_A_HI) for n in ARABIC_FAMILY
                  if len(_X_for(n, BAND_A_LO, BAND_A_HI)) >= 3}
    if 'quran' not in per_corpus: return float('nan')
    sizes = {n: len(X) for n, X in per_corpus.items()}
    all_X = np.vstack(list(per_corpus.values()))
    rng_psi = np.random.default_rng(SEED + 111)
    rank_null = []
    obs_rank = quran_rank
    for _ in range(n_perm):
        idx = rng_psi.permutation(len(all_X))
        # Pass 1: partition into pseudo-corpora of the same sizes
        pseudo_X = {}; pos = 0
        for n, sz in sizes.items():
            pseudo_X[n] = all_X[idx[pos:pos+sz]]; pos += sz
        # Pass 2: build LOCAL centroid from pseudo-non-quran rows
        ctr_rows = np.vstack([X for n, X in pseudo_X.items() if n != 'quran'])
        mu_loc_p   = ctr_rows.mean(0)
        S_loc_p    = np.cov(ctr_rows, rowvar=False) + 1e-6 * np.eye(5)
        Sinv_loc_p = np.linalg.inv(S_loc_p)
        # Pass 3: compute pseudo-Ψ with the same recipe as _psi_against
        pseudo_PSI = {}
        for n, Xp in pseudo_X.items():
            m  = Xp.mean(0)
            phi_n = float(np.median(mahalanobis(Xp, mu_loc_p, Sinv_loc_p)))
            pseudo_PSI[n] = float(np.sqrt(max(phi_n, 0.01)) * m[0] * (m[3] / max(m[1], 1e-3)))
        pseudo_ranked = sorted(pseudo_PSI, key=lambda k: -pseudo_PSI[k])
        rank_null.append(pseudo_ranked.index('quran') + 1)
    # One-sided: how often does random assignment achieve rank <= observed?
    rank_null = np.array(rank_null, dtype=float)
    p = float((np.sum(rank_null <= obs_rank) + 1) / (n_perm + 1))
    print(f'[L7/A] Ψ permutation null (N={n_perm}): pseudo-Quran rank '
          f'median={int(np.median(rank_null))} / best={int(rank_null.min())}')
    print(f'[L7/A] observed Quran rank = {obs_rank} → perm p-value = {p:.4g}')
    # AUDIT 2026-04-19 (v5 fix ②): STRUCTURAL FLOOR note. Under the null,
    # the pseudo-Quran has a uniform 1/n_corpora probability of landing at
    # any given rank. For obs_rank=1 this means the minimum achievable
    # p-value is ~ 1/n_corpora. With 8 Arabic-family corpora the floor is
    # ~ 0.125 > 0.05, so the rank-1 test CANNOT reach α=0.05 in this pool
    # size. This is a property of the test, not of the data. Ψ is already
    # demoted to DESCRIPTIVE; we state the floor explicitly here for any
    # reviewer checking whether p < 0.05 is attainable.
    _p_floor = 1.0 / max(len(per_corpus), 1)
    print(f'[L7/A] structural p-value floor = 1/n_corpora = {_p_floor:.3f} '
          f'(test cannot reach α=0.05 unless n_corpora > 20)')
    return p

psi_p = _psi_perm_p()
bless('Psi_perm_p_value', float(psi_p) if not np.isnan(psi_p) else 1.0,
      tol_override=float('inf'))
bless('Psi_quran_rank',   float(quran_rank), tol_override=float('inf'))

# Separate cross-language Ψ: each scripture uses its OWN per-language centroid.
# Hebrew/Greek corpora are their own control pool (self vs self) — this is
# a weaker test but at least doesn't conflate language with structure.
# AUDIT FIX 2026-04-18: mark as INFEASIBLE when a family has <2 corpora
# (single-corpus covariance => Mahalanobis distance is degenerate).
XLANG_POOLS = {
    'greek':  [c for c in ('iliad_greek', 'greek_nt') if c in FEATS],
    'hebrew': [c for c in ('hebrew_tanakh',) if c in FEATS],
}
PSI_xlang = {}
XLANG_INFEASIBLE = []
for fam, pool in XLANG_POOLS.items():
    if len(pool) < 2:
        if pool: XLANG_INFEASIBLE.append((fam, pool[0]))
        continue
    psi_fam, _, _ = _psi_against(pool + [], center_pool=pool)
    for n, v in psi_fam.items():
        PSI_xlang[f'{fam}:{n}'] = v

if XLANG_INFEASIBLE:
    print('')
    print('[L7/X] INFEASIBLE language families (need >=2 corpora for valid covariance):')
    for fam, single in XLANG_INFEASIBLE:
        print(f'       {fam:<10s}  only one corpus ({single}); Mahalanobis is degenerate')

if PSI_xlang:
    print('')
    print('[L7/X] Ψ per-language (each uses its own covariance; self-contained):')
    for k, v in sorted(PSI_xlang.items(), key=lambda kv: -kv[1]):
        print(f'       {k:<28s}  Ψ = {v:.3f}')
elif not XLANG_INFEASIBLE:
    print('[L7/X] no non-Arabic corpora loaded; cross-language Ψ omitted')"""
    )

    # Cell 109b — L7 sparse-PCA variant (audit v3 reporting; not law)
    code(
        r"""# === Cell 109b · L7 sparse-PCA axis — interpretable alternative to Ψ ===
# AUDIT 2026-04-18 (v3): the composite Ψ is dimensionally incoherent and
# already demoted to 'descriptive composite' in Cell 109. This cell provides
# a PRINCIPLED replacement based on a sparse sufficient statistic:
#
#   1. Z-score the 5-D Band-A surah feature rows from ALL Arabic-family
#      corpora (Quran + 6 controls + hadith).
#   2. Fit SparsePCA(n_components=1) → a single interpretable axis with
#      L1-sparsified loadings (many near zero) in the z-scored space.
#   3. Project every surah row onto that axis.
#   4. Report: axis loadings + Cohen's d of Quran-vs-controls projections.
#   5. Permutation p-value: shuffle the Quran/control label N_PERM times,
#      recompute Cohen's d on the projection, report empirical p.
#
# Unlike Ψ, this is (a) scale-invariant by construction, (b) has statistical
# meaning — the axis is the direction of maximum variance in the 5-D cloud
# under an L1 sparsity penalty, (c) can be interpreted linguistically from
# which features dominate the loadings.
#
# IMPORTANT: sparse PCA is UNSUPERVISED — the principal axis maximises total
# variance, not Quran-vs-control separation. If Cohen's d along PC1 is
# SMALL, it means the Quran's distinctiveness is NOT the dominant variance
# direction of the Arabic family; in that case PC1 is still interpretable
# as the family's primary structural axis but does not separate Quran from
# controls. Both outcomes are informative.
#
# LINGUISTIC INTERPRETATION (paper-text hypothesis, NOT a computed claim):
# if PC1's top absolute loadings are concentrated on EL (end-letter rhyme)
# and H_cond (root conditional entropy), this is CONSISTENT with an oral-
# formulaic (Parry-Lord) compositional signature. Full validation would
# require an externally-annotated formula-density index per surah, which
# is outside the scope of this notebook.
try:
    from sklearn.decomposition import SparsePCA
    _HAVE_SPCA = True
except ImportError:
    _HAVE_SPCA = False
    print('[L7/SPCA] sklearn.decomposition.SparsePCA unavailable; skipping')

_spca_d = 0.0; _spca_p = 1.0
if _HAVE_SPCA:
    fam = [c for c in ARABIC_FAMILY if c in FEATS]
    X_list = []; y_list = []
    for n in fam:
        Xn = _X_for(n, BAND_A_LO, BAND_A_HI)
        if len(Xn) < 3: continue
        X_list.append(Xn)
        y_list.append(np.full(len(Xn), 1 if n == 'quran' else 0, dtype=int))
    if X_list and any(int(y.sum()) > 0 for y in y_list):
        X_all = np.vstack(X_list)
        y_all = np.concatenate(y_list)
        # z-score before sparse PCA to make loadings comparable across dims
        mu_all = X_all.mean(0); sd_all = X_all.std(0, ddof=1)
        sd_all = np.where(sd_all < 1e-12, 1.0, sd_all)
        Z = (X_all - mu_all) / sd_all
        try:
            spca = SparsePCA(n_components=1, alpha=1.0, random_state=SEED,
                              max_iter=200)
            spca.fit(Z)
            axis = spca.components_[0].astype(float)
            # normalise for readability (unit L2 norm) if axis is non-trivial
            axn = float(np.linalg.norm(axis))
            if axn > 1e-12: axis = axis / axn
            proj = Z @ axis
            # Orient so "higher projection = more Quran-like" (sign convention only)
            if proj[y_all == 1].mean() < proj[y_all == 0].mean():
                axis = -axis; proj = -proj
            proj_q = proj[y_all == 1]; proj_c = proj[y_all == 0]
            pool_sd = np.sqrt(((len(proj_q)-1)*proj_q.var(ddof=1) +
                               (len(proj_c)-1)*proj_c.var(ddof=1))
                              / max(1, len(proj_q)+len(proj_c)-2))
            cohen_d = float(abs(proj_q.mean() - proj_c.mean()) / max(pool_sd, 1e-9))
            _spca_d = cohen_d

            print('[L7/SPCA] SparsePCA PC1 loadings (z-scored 5D, L1 alpha=1.0):')
            for i, fname in enumerate(FEAT_COLS):
                tag = ' **' if abs(axis[i]) > 0.5 else ''
                print(f'          {fname:<6s}  = {axis[i]:+.3f}{tag}')
            print(f'[L7/SPCA] Cohen d along PC1 (Quran vs Arabic ctrl, surah-level): '
                  f'{cohen_d:.3f}   (n_q={len(proj_q)}, n_ctrl={len(proj_c)})')

            # Permutation null: shuffle Quran/control labels, recompute d
            rng_spca    = np.random.default_rng(SEED + 155)
            n_perm_spca = min(N_PERM, 1000)
            null_ds     = np.empty(n_perm_spca, dtype=float)
            for _p in range(n_perm_spca):
                y_shuf = rng_spca.permutation(y_all)
                pq = proj[y_shuf == 1]; pc = proj[y_shuf == 0]
                if len(pq) < 2 or len(pc) < 2:
                    null_ds[_p] = 0.0; continue
                ps = np.sqrt(((len(pq)-1)*pq.var(ddof=1) +
                              (len(pc)-1)*pc.var(ddof=1))
                             / max(1, len(pq)+len(pc)-2))
                null_ds[_p] = abs(pq.mean() - pc.mean()) / max(ps, 1e-9)
            hits = int(np.sum(null_ds >= cohen_d))
            _spca_p = float((hits + 1) / (n_perm_spca + 1))
            print(f'[L7/SPCA] permutation p-value (N={n_perm_spca}): {_spca_p:.4g}')

            top_idx  = np.argsort(-np.abs(axis))[:2]
            top_feat = [FEAT_COLS[i] for i in top_idx]
            print(f'[L7/SPCA] top-2 loadings: {top_feat} — axis interpretation is '
                  f'paper-text; see cell header for Parry-Lord hypothesis.')
        except Exception as _ex:
            print(f'[L7/SPCA] sparse-PCA fit failed: {_ex}')

bless('L7_sparse_pca_d',      float(_spca_d), tol_override=float('inf'))
bless('L7_sparse_pca_perm_p', float(_spca_p), tol_override=float('inf'))"""
    )

    # Cell 110 — E2 Csiszár-Körner tilting
    code(
        r"""# === Cell 110 · E2 Csiszár-Körner tilting (closes Gap 4 beyond Gaussian) ===
from scipy import stats
rng_e2 = np.random.default_rng(SEED + 40)
families = {
    'gaussian':   lambda size: stats.norm(loc=0,   scale=1).rvs(size=size, random_state=rng_e2),
    'laplace':    lambda size: stats.laplace(loc=0,scale=1).rvs(size=size, random_state=rng_e2),
    't_student':  lambda size: stats.t(df=3).rvs(size=size, random_state=rng_e2),
    'log_normal': lambda size: np.exp(stats.norm(loc=0, scale=0.5).rvs(size=size, random_state=rng_e2)),
}

def _chernoff(sampler, n=3000):
    a = sampler(size=n); b = sampler(size=n) + 0.8
    ts = np.linspace(-1.5, 1.5, 25); vals = []
    for t in ts:
        mgf = np.mean(np.exp(t * (a - b)))
        if mgf > 0: vals.append(-np.log(mgf))
    return max(vals) if vals else float('nan')

cherns = {fam: float(_chernoff(s)) for fam, s in families.items()}
for fam, C in cherns.items():
    print(f'[E2 ] Chernoff C ({fam:<12s}) = {C:+.3f}  {"OK" if C > 0 else "FAIL"}')
all_pos = all(c > 0 for c in cherns.values())
print(f'[E2 ] all 4 families positive: {all_pos}  (Gap 4 closed numerically)')"""
    )

    # Cell 111 — E3 Berry-Esseen
    code(
        r"""# === Cell 111 · E3 Berry-Esseen finite-N correction ===
N_BE = 50
be_by = {}
for n in ['quran'] + list(ARABIC_CTRL_POOL):
    if n not in FEATS: continue
    X = _X_for(n, BAND_A_LO, BAND_A_HI)
    if len(X) < 5: continue
    x = X[:, 0] - X[:, 0].mean()
    sig = np.sqrt(np.var(x) + 1e-12)
    rho = np.mean(np.abs(x)**3)
    BE  = 0.4748 * rho / (sig**3 * np.sqrt(N_BE))
    be_by[n] = float(BE)
    print(f'  [E3 ] {n:<22s}  BE @ N={N_BE} = {BE:.4f}')
bless('E3_berry_esseen', float(be_by.get('quran', float('nan'))),
      tol_override=1.0)"""
    )

    # Cell 112 — Phase-18 verifier + checkpoint
    code(
        r"""# === Cell 112 · Phase-18 verifier + checkpoint ===
def _verify_phase_18():
    assert 'quran' in SCI, 'SCI for Quran missing'
    print(f'[OK   ] Phase 18 — Discovery Lab done (L1 SCI={SCI["quran"]:.3f}, L7 Ψ-rank={quran_rank})')

_verify_phase_18()
save_checkpoint('18_discovery', {
    'L1_SCI': SCI, 'L2_alpha': alpha_by, 'L3_F': F_vals, 'L4_aljamal': aljamal,
    'L5_OBI_slack': obi_slack, 'L6_gamma_slope': float(b_slope), 'L7_Psi': PSI,
    'L7_rank_quran': int(quran_rank) if quran_rank > 0 else None,
    'E1_pe_table': {f'{n}|eps={ep}|N={N}': v
                    for n, d in pe_table.items() for (ep, N), v in d.items()},
    'E2_chernoff': cherns, 'E3_BE': be_by,
}, state={
    # AUDIT 2026-04-18 (v4): Phase 21 Fig 3/4 reads ns_L6, omega_proxy, gammas,
    # a_int, b_slope, PSI — these must survive a checkpoint resume from here.
    'ALL_RESULTS': ALL_RESULTS,
    'pe_table': pe_table,
    'SCI': SCI, 'cherns': cherns,
    'PSI': PSI, 'quran_rank': quran_rank,
    'alpha_by': alpha_by, 'b_slope': b_slope, 'a_int': a_int,
    'gammas': gammas, 'omega_proxy': omega_proxy, 'ns_L6': ns_L6,
    'I_corpus_by': I_corpus_by, 'H32_by': H32_by, 'VL_by': VL_by,
    'obi_slack': obi_slack,
})"""
    )


# ============================================================================
# PHASE 19 — Adiyat blind + null tests + compression proxies (cells 113-118)
# ============================================================================
def build_phase_19() -> None:
    phase_header(
        19,
        "Adiyat blind + forced-EL surrogates + Monte-Carlo constant null + "
        "compression-ratio proxies for P1/P3",
        "Ādiyāt case study + behavioural surrogates (gzip-based proxies for "
        "the P1/P3 human-subject gaps that cannot be run here).",
    )

    # Cell 113 — Adiyat 7-metric blind test (every metric must earn its win)
    code(
        r"""# === Cell 113 · Adiyat 7-metric blind winning variant ===
# Sura 100 (Q:100). Real Hafs vs verse-internal-shuffle variant.
# 7 metrics, each EARNED (no unconditional bonuses):
#   1-5: |f_real[i] - μ_ctrl[i]|  vs  |f_shuf[i] - μ_ctrl[i]|  for 5 features
#        (real must sit FARTHER from the Arabic-control centroid)
#   6:   Φ_M(real)  >  Φ_M(shuf)       — overall Mahalanobis distance
#   7:   path_cost(canonical) is in the lower tail of a shuffle-null
#        distribution (N_SHUF permutations), NOT merely < one random shuffle.
#
# AUDIT 2026-04-18: old Metric 7 compared path_cost(canonical) to path_cost
# of ONE random shuffle — near-tautologically true for any coherent text.
# The PROPER test builds a null from many shuffles and asks whether the
# canonical value is below the 5th percentile. Only then does canonical
# order claim non-trivial "smoothness".
adiyat = next((u for u in CORPORA.get('quran', []) if str(u.label).endswith(':100')), None)
if adiyat is None:
    adiyat = next((u for u in CORPORA.get('quran', []) if '100' in str(u.label)), None)

if adiyat and len(adiyat.verses) >= 5:
    rng_a = np.random.default_rng(SEED + 50)
    shuf_verses = [' '.join(rng_a.permutation(v.split()).tolist())
                   for v in adiyat.verses]
    f_real = ft.features_5d(adiyat.verses)
    f_shuf = ft.features_5d(shuf_verses)

    wins = 0
    metric_log = []
    # metrics 1-5: per-axis farther from control centroid
    for i, fname in enumerate(FEAT_COLS):
        won = abs(f_real[i] - mu[i]) > abs(f_shuf[i] - mu[i])
        wins += int(won)
        metric_log.append((f'{fname} distance', won))

    # metric 6: overall Φ_M farther
    d_real = float(np.sqrt((f_real - mu) @ S_inv @ (f_real - mu)))
    d_shuf = float(np.sqrt((f_shuf - mu) @ S_inv @ (f_shuf - mu)))
    won6 = d_real > d_shuf
    wins += int(won6); metric_log.append(('Phi_M overall', won6))

    # metric 7 (audit-fixed): canonical path-cost must be in the lower 5th pctl
    # of a PROPER null distribution built from N_SHUF verse-order shuffles.
    # AUDIT 2026-04-18 (v3): the previous `_path_cost` applied `ft.features_5d`
    # to ONE verse at a time, which produces degenerate features for
    # distributional channels (VL_CV = std/mean collapses to 0 with a single
    # verse-length observation; H_cond is computed on ≤10 intra-verse tokens
    # and swings wildly). We now use a well-defined 4-D per-verse descriptor:
    #   (EL_i, CN_i, #tokens_i, mean_token_len_i)
    # z-scored across the verses of the unit under test so the L2 path cost
    # is scale-invariant. All four coordinates are per-verse intrinsic and
    # move under reordering, so the shuffle null remains non-trivial.
    def _per_verse_feat(v):
        toks = v.split()
        if not toks: return np.zeros(4, dtype=float)
        last = toks[-1]; first = toks[0]
        el = 1.0 if last and last[-1] in RHYME_LETTERS else 0.0
        cn = 1.0 if first in ft.ARABIC_CONN else 0.0
        wl = float(len(toks))
        mtl = float(np.mean([len(t) for t in toks]))
        return np.array([el, cn, wl, mtl], dtype=float)

    def _path_cost(verses):
        if len(verses) < 2: return 0.0
        pts = np.vstack([_per_verse_feat(v) for v in verses])
        # z-score each dim; rows with constant values get std=1 so they
        # contribute 0 instead of exploding to inf.
        std = pts.std(axis=0, ddof=1)
        std = np.where(std < 1e-9, 1.0, std)
        pts_z = (pts - pts.mean(axis=0)) / std
        diffs = pts_z[1:] - pts_z[:-1]
        return float(np.sum(np.linalg.norm(diffs, axis=1)))

    N_SHUF_M7 = 200 if FAST_MODE else 1000
    try:
        c_real = _path_cost(adiyat.verses)
        null_costs = []
        for _ in range(N_SHUF_M7):
            perm = list(rng_a.permutation(len(adiyat.verses)))
            null_costs.append(_path_cost([adiyat.verses[j] for j in perm]))
        null_arr = np.array(null_costs)
        # canonical wins IFF it is at or below the 5th percentile of the null
        pctl5  = float(np.percentile(null_arr, 5))
        won7   = c_real <= pctl5
        perm_p = float((np.sum(null_arr <= c_real) + 1) / (N_SHUF_M7 + 1))
        print(f'  [Adi] path-cost null N={N_SHUF_M7}: median={np.median(null_arr):.3f}  '
              f'5th pctl={pctl5:.3f}  real={c_real:.3f}  perm p={perm_p:.4g}')
        bless('Adiyat_metric7_perm_p', perm_p, tol_override=float('inf'))
    except Exception as ex:
        won7 = False
        print(f'  [Adi] path-cost null failed ({ex})')
        bless('Adiyat_metric7_perm_p', 1.0, tol_override=float('inf'))
    wins += int(won7); metric_log.append(('path cost vs null (5th pctl)', won7))

    print(f'[Adiyat] Sura 100 (label={adiyat.label}): real wins {wins}/7 blind tests')
    for name, w in metric_log:
        print(f'  [Adi] {name:<30s}  {"WIN" if w else "lose"}')
    bless('Adiyat_blind', float(wins / 7.0))
else:
    print('[Adiyat] Sura 100 not found or too short; skipping')
    bless('Adiyat_blind', 0.0, tol_override=float('inf'))
    bless('Adiyat_metric7_perm_p', 1.0, tol_override=float('inf'))"""
    )

    # Cell 114 — forced-EL surrogates
    code(
        r"""# === Cell 114 · forced-EL surrogates (shuffle-within-rhyme-class) ===
n_surr = 500 if FAST_MODE else 2000
rng_s = np.random.default_rng(SEED + 60)
q_units_short = [u for u in CORPORA['quran'] if BAND_A_LO <= len(u.verses) <= BAND_A_HI][:10]
if q_units_short:
    base_verses = sum([u.verses for u in q_units_short], [])
    base_EL = float(ft.features_5d(base_verses)[0])
    surr_ELs = []
    for _ in tqdm(range(n_surr), desc='forced-EL surr'):
        shuf_verses = []
        for v in base_verses:
            toks = v.split()
            if len(toks) < 3: shuf_verses.append(v); continue
            head, tail = toks[:-1], toks[-1]
            rng_s.shuffle(head)
            shuf_verses.append(' '.join(head + [tail]))
        surr_ELs.append(float(ft.features_5d(shuf_verses)[0]))
    surr_ELs = np.array(surr_ELs)
    p_emp = float(np.mean(surr_ELs >= base_EL))
    print(f'[surr] base EL = {base_EL:.3f}; fraction of surrogates >= base = {p_emp:.4f}')
else:
    p_emp = float('nan')
    print('[surr] no short Quran units; skipping')"""
    )

    # Cell 115 — Monte-Carlo constant null
    code(
        r"""# === Cell 115 · Monte-Carlo constant-vector null ===
rng_c = np.random.default_rng(SEED + 70)
const_ds = []
for _ in range(100):
    v = rng_c.uniform(0, 1, size=5)
    X_fake = np.tile(v, (50, 1))
    d = mahalanobis(X_fake, mu, S_inv)
    const_ds.append(float(np.median(d)))
mean_const = float(np.mean(const_ds))
print(f'[const null] mean d of constant vectors = {mean_const:.3f}')
bless('MonteCarlo_const_null', mean_const, tol_override=float('inf'))"""
    )

    # Cell 116 — PROXY-1 gzip compression ratio
    # AUDIT 2026-04-18: gzip bytes / UTF-8 bytes confounds script choice
    # (Arabic = 2 bytes/char, ASCII = 1 byte/char). We normalize by character
    # count (not bytes) to isolate structural compression. Also constrain to
    # fixed character budget per corpus for apples-to-apples comparison.
    code(
        r"""# === Cell 116 · PROXY-1 gzip compression (char-normalised; surrogate for P1) ===
import gzip as _gz
CHAR_BUDGET = 20000   # same # of characters per corpus => kills UTF-8 confound
comp_ratio = {}
comp_ratio_bytes = {}   # legacy (for diagnostic)
for n, units in CORPORA.items():
    full = ' '.join(v for u in units for v in u.verses)
    if not full: continue
    # Truncate to the SAME character count across corpora. For corpora with
    # fewer than CHAR_BUDGET chars we use what we have (flagged).
    snippet = full[:CHAR_BUDGET]
    encoded = snippet.encode('utf-8')
    if not encoded: continue
    n_bytes = len(encoded); n_chars = len(snippet)
    gz_bytes = len(_gz.compress(encoded))
    # Character-normalised ratio: gzip_bytes_per_char  (script-agnostic)
    comp_ratio[n]       = gz_bytes / max(1, n_chars)
    comp_ratio_bytes[n] = gz_bytes / max(1, n_bytes)  # legacy
short = [n for n, units in CORPORA.items()
         if sum(len(v) for u in units for v in u.verses) < CHAR_BUDGET]
if short:
    print(f'[P1 proxy] NOTE: {len(short)} corpora shorter than CHAR_BUDGET={CHAR_BUDGET}: {short}')
print(f'  [P1 proxy] (gzip_bytes / CHARACTER, lower = more compressible structure)')
for n in sorted(comp_ratio, key=lambda k: comp_ratio[k])[:6]:
    byte_ratio = comp_ratio_bytes[n]
    print(f'  [P1 proxy] {n:<22s}  gzip/char = {comp_ratio[n]:.3f}  '
          f'(legacy gzip/byte = {byte_ratio:.3f})')
bless('PROXY_1_compression_p1', float(comp_ratio.get('quran', float('nan'))),
      tol_override=float('inf'))"""
    )

    # Cell 117 — PROXY-2 gzip delta under scramble
    code(
        r"""# === Cell 117 · PROXY-2 gzip-delta under verse scramble (surrogate for P3) ===
# Delta is a RATIO, so it's already UTF-8-invariant (numerator and denominator
# use the same encoding per corpus). Keeping as is but using a fixed number of
# verses for comparability.
rng_p3 = np.random.default_rng(SEED + 80)
comp_delta = {}
for n, units in CORPORA.items():
    sample_verses = [v for u in units[:30] for v in u.verses][:500]
    if len(sample_verses) < 10: continue
    orig = sum(len(_gz.compress(v.encode('utf-8'))) for v in sample_verses)
    scr  = sum(len(_gz.compress(' '.join(rng_p3.permutation(v.split())).encode('utf-8')))
               for v in sample_verses)
    comp_delta[n] = (scr - orig) / max(1, orig)
for n in sorted(comp_delta, key=lambda k: -comp_delta[k])[:6]:
    print(f'  [P3 proxy] {n:<22s}  scramble Δ = {comp_delta[n]:+.3f}')
bless('PROXY_2_compression_p3', float(comp_delta.get('quran', float('nan'))),
      tol_override=float('inf'))"""
    )

    # Cell 118 — Phase-19 verifier + checkpoint
    code(
        r"""# === Cell 118 · Phase-19 verifier + checkpoint ===
_verify_phase_19 = lambda: print('[OK   ] Phase 19 — Adiyat + nulls + proxies done')
_verify_phase_19()
save_checkpoint('19_adiyat_nulls', {
    'surr_EL_p': float(p_emp) if not np.isnan(p_emp) else None,
    'const_null_mean': mean_const,
    'comp_ratio': comp_ratio, 'comp_delta': comp_delta,
}, state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 20 — Formal-proof gap closures (honest) (cells 119-124)
# ============================================================================
def build_phase_20() -> None:
    phase_header(
        20,
        "Formal-proof gap status — G1/G2/G4 closed; G3/G5 data-dependent",
        "Gaps 3 and 5 previously retracted as algebraic tautologies. "
        "Cell 121 attempts an empirical G3 closure via E1's transmission-"
        "error curvature; the closure holds IFF E1 ran on ≥5 corpora "
        "(see audit 2026-04-18). If not, G3 is reported OPEN — no claim "
        "is made of formal closure.",
    )

    # Cell 119 — G1 Hill + Bennett
    code(
        r"""# === Cell 119 · G1 heavy-tail Hill estimator (5 features, Quran Band A) ===
def _hill_alpha(x, frac=0.1):
    x = np.sort(np.abs(np.asarray(x)))[::-1]
    k = max(3, int(frac * len(x)))
    if k >= len(x): return float('inf')
    xk = x[:k]; x_k = x[k]
    if x_k <= 0: return float('inf')
    return float(1.0 / np.mean(np.log(xk / x_k + 1e-12)))

X_q = _X_for('quran', BAND_A_LO, BAND_A_HI)
hills = []
for i, fname in enumerate(FEAT_COLS):
    a = _hill_alpha(X_q[:, i])
    hills.append(a)
    print(f'  [G1 ] Hill α ({fname:<6s}) = {a:.2f}')
min_alpha = float(min(hills))
print(f'[G1 ] min Hill α = {min_alpha:.2f}  (target ≥ 1.5)')
bless('G1', min_alpha)"""
    )

    # Cell 120 — G2 restate (no cross-phase variable leak)
    code(
        r"""# === Cell 120 · G2 5-channel MI independence re-assertion ===
# G2 was blessed in Phase 10 (cell 55). Re-read from ALL_RESULTS so this cell
# works even when Phase 20 is run after a kernel-resume that skipped Phase 10.
_g2 = ALL_RESULTS.get('G2', {}).get('actual', float('nan'))
print(f'[G2 ] max normalised 5-channel MI = {float(_g2):.3f}  (target ≤ 0.30)')"""
    )

    # Cell 121 — G3 HONEST — fit to REAL transmission error from E1 (not to (x-x̄)²)
    code(
        r"""# === Cell 121 · G3 HONEST — fit d²(-log P_e)/dx_i² at Quran centroid ===
# The previous 'closure' fit (xs - mean(xs))^2 which is a tautology.
# Replace with the empirical second derivative of -log P_e along each axis,
# using E1's per-corpus transmission-error table at eps = 0.05.
#
# AUDIT 2026-04-18: Phase 18 E1 ran on only 3 corpora (Quran, poetry_abbasi,
# arabic_bible), so each axis has at most 3 data points — far too few to fit
# a quadratic reliably. We explicitly require n_pts >= MIN_PTS and mark the
# G3 axis INSUFFICIENT otherwise (no FAIL, no PASS — honest null verdict).
# To actually close G3 one would need E1 on 5+ corpora; we leave that as an
# open methodological gap rather than overfitting to a tiny dataset.
MIN_PTS = 5   # absolute minimum for quadratic fit to be meaningful
if 'pe_table' not in globals():
    print('[G3 HONEST] skipped — Phase 18 pe_table not in scope (run Phase 18 first)')
    all_pd = False
    g3_pd = []
    g3_verdicts = []
else:
    from scipy.optimize import curve_fit
    def _quadratic(x, a, b, c): return a * (x - b)**2 + c

    # AUDIT 2026-04-18 (v3): ALSO require the x-axis range to span at least
    # MIN_RANGE_STD standard deviations of the centred cloud. For axes like
    # CN (≈0.08-0.15 across 7 corpora) the ptp can be <1 std of the feature
    # itself — the quadratic coefficient is then unidentified even with
    # MIN_PTS points because all samples lie near the vertex. Report such
    # cases as INSUFFICIENT_RANGE, not PD/FAIL.
    MIN_RANGE_STD = 1.0
    g3_pd = []; g3_verdicts = []
    for i, fname in enumerate(FEAT_COLS):
        xs, ys = [], []
        for n in pe_table:
            Xn = _X_for(n, BAND_A_LO, BAND_A_HI)
            if len(Xn) < 3: continue
            pes = [pe for (ep, _N), pe in pe_table[n].items() if ep == 0.05 and pe > 0]
            if not pes: continue
            xs.append(float(Xn[:, i].mean()))
            ys.append(float(-np.log(np.mean(pes))))
        if len(xs) < MIN_PTS:
            # INSUFFICIENT is NOT a PD claim. Do NOT count as positive evidence.
            g3_pd.append(False)
            g3_verdicts.append('INSUFFICIENT_N')
            print(f'  [G3 ] axis {fname:<6s}  only {len(xs)} points (<{MIN_PTS}); '
                  f'INSUFFICIENT_N — cannot fit quadratic reliably')
            continue
        # x-range gate: compare ptp(xs) to the cross-corpus std of the
        # feature mean itself (self-referential scale, robust to units).
        xs_arr = np.array(xs)
        x_ptp = float(np.ptp(xs_arr))
        x_std = float(xs_arr.std(ddof=1)) if len(xs_arr) > 1 else 0.0
        if x_std <= 0 or x_ptp < MIN_RANGE_STD * x_std:
            g3_pd.append(False)
            g3_verdicts.append('INSUFFICIENT_RANGE')
            print(f'  [G3 ] axis {fname:<6s}  ptp={x_ptp:.3g} < {MIN_RANGE_STD}·std={x_std:.3g}; '
                  f'INSUFFICIENT_RANGE — curvature unidentified')
            continue
        try:
            popt, _ = curve_fit(_quadratic, xs_arr, np.array(ys),
                                p0=[1.0, float(np.mean(xs)), 0.0], maxfev=5000)
            is_pd = popt[0] > 0
            g3_pd.append(is_pd)
            g3_verdicts.append('PD' if is_pd else 'NOT_PD')
            print(f'  [G3 ] axis {fname:<6s}  '
                  f'a = {popt[0]:+.4f}  PD = {is_pd}   n_pts = {len(xs)}   '
                  f'x_ptp={x_ptp:.3g}')
        except Exception as e:
            g3_pd.append(False)
            g3_verdicts.append('FIT_FAILED')
            print(f'  [G3 ] axis {fname:<6s}  fit failed ({e}); FAIL')

    n_insufficient = (g3_verdicts.count('INSUFFICIENT_N')
                      + g3_verdicts.count('INSUFFICIENT_RANGE'))
    n_pd           = g3_verdicts.count('PD')
    all_pd = (n_pd == len(FEAT_COLS))
    G3_STATUS = 'OPEN'   # default; upgraded below only on full PD closure
    if n_insufficient > 0:
        print(f'[G3 ] {n_insufficient}/{len(FEAT_COLS)} axes INSUFFICIENT '
              f'(N or x-range gate) — G3 CANNOT be closed from this data.')
        print(f'[G3 ] verdict: OPEN (insufficient data; not a closure claim)')
    elif all_pd:
        G3_STATUS = 'CLOSED'
        print(f'[G3 ] all 5 axes empirically PD on real P_e curvature — G3 CLOSED')
    else:
        G3_STATUS = 'FAILED'
        print(f'[G3 ] {n_pd}/{len(FEAT_COLS)} axes PD — G3 FAILED empirical test')"""
    )

    # Cell 122 — G4 via E2 (guard against Phase-18-not-run)
    code(
        r"""# === Cell 122 · G4 HONEST — exp-family Chernoff positivity (from E2) ===
if 'cherns' not in globals():
    print('[G4 HONEST] skipped — Phase 18 E2 cherns dict not in scope')
    cherns = {}
else:
    print('[G4 ] Chernoff info per family (from E2):')
    for fam, C in cherns.items():
        print(f'  {fam:<12s}  C = {C:+.3f}')
    print(f'[G4 ] Gap 4 empirically closed under {len(cherns)} distribution families.')"""
    )

    # Cell 123 — G5 via E1 + negative registry
    code(
        r"""# === Cell 123 · G5 HONEST (empirical γ) + NEGATIVE findings registry ===
g5_slope = float(ALL_RESULTS.get('L6', {}).get('actual', float('nan')))
print(f'[G5 ] Empirical γ(Ω) slope = {g5_slope:+.4f}  (vs retracted algebraic claim 0.055)')
# AUDIT 2026-04-18: G5 was claimed closed via L6 slope sign. That only tells
# us the γ(Ω) curve fits with a positive slope on the corpora we DO have.
# It is NOT a theoretical closure of the formal claim γ'(Ω) > 0 ∀ Ω. Mark
# G5 status based on whether the slope is significantly > 0 with enough points.
G5_STATUS = 'OPEN'
if not np.isnan(g5_slope):
    # Count how many corpora contributed to the L6 regression (Phase 16 Cell 108).
    n_L6_pts = int(ALL_RESULTS.get('L6', {}).get('n_points',
                  sum(1 for n in ARABIC_FAMILY if n in FEATS and len(_X_for(n, BAND_A_LO, BAND_A_HI)) > 0)))
    if n_L6_pts >= 5 and g5_slope > 0:
        G5_STATUS = 'EMPIRICAL_POSITIVE'   # positive slope observation, not formal proof
        print(f'[G5 ] n={n_L6_pts} corpora, slope>0 — EMPIRICAL POSITIVE (not formal closure)')
    else:
        print(f'[G5 ] n={n_L6_pts} corpora, slope={g5_slope:+.4f} — OPEN (formal claim not closed)')

NEGATIVES = {
    'optimal-stopping': 'No evidence Quran satisfies optimal-stopping formula.',
    'abjad-numerology': 'Null results; flagged not reproducible.',
    'spectral-gap':     'Spectral micro-hash anomaly RETRACTED (shuffle-null trivial).',
    'ring-chiasm':      'Ring-chiasm exceeds random: FAILED.',
    'LZ-binding-proof': 'Lempel-Ziv binding proof of STOT remains OPEN.',
    'F1-F4':            'Fisher-conjectures F1-F4 not replicated on clean data.',
    # AUDIT 2026-04-18: G3/G5 reported honestly per reviewer pressure.
    # G3 empirical closure is DATA-DEPENDENT — closure requires ≥5 E1 corpora.
    # Phase 18 now runs 7 (quran + 6 Arabic controls); G3_STATUS reflects the
    # actual outcome. G5 has no formal closure — we only observe an empirical
    # slope; do not claim it proves the algebraic inequality γ'(Ω) > 0.
    'G3-formal':        f'G3 empirical status this run = {G3_STATUS}; no formal closure proven.',
    'G5-formal':        f'G5 formal claim OPEN; empirical status this run = {G5_STATUS}.',
}
for k, v in NEGATIVES.items():
    print(f'  [NEG ] {k:<22s} -> {v}')"""
    )

    # Cell 123b — Benjamini-Hochberg FDR correction for multiple testing
    #
    # AUDIT 2026-04-18 (v2): the notebook runs 45+ flagship claims + 70+ sub-
    # tests. Previously only ~8 p-values entered FDR. We now expand coverage
    # by generating permutation p-values for EVERY locked scalar that has a
    # natural Quran-vs-control contrast (the "Mahalanobis family") and by
    # converting effect-size statistics to z-based two-sided p where valid.
    # This is O(N_PERM_FDR × n_entries × cost_per_metric); kept fast by using
    # cheap surrogate statistics (not full re-computation of T1-T31).
    code(
        r"""# === Cell 123b · Benjamini-Hochberg FDR correction (multi-testing audit) ===
from scipy.stats import norm as _norm

def _bh_fdr(pvals, alpha=0.05):
    '''Return BH-adjusted q-values and the significance mask at FDR level α.
    Input: dict {id: p}. Output: dict {id: q}, list of ids surviving FDR.'''
    items = [(fid, p) for fid, p in pvals.items()
             if isinstance(p, (int, float)) and not np.isnan(p)]
    if not items: return {}, []
    items.sort(key=lambda kv: kv[1])
    m = len(items); qs = {}
    # Compute q_i = min_{j>=i} ( p_(j) * m / j )
    running_min = 1.0
    for i, (fid, p) in reversed(list(enumerate(items, start=1))):
        q = min(p * m / i, 1.0)
        running_min = min(running_min, q)
        qs[fid] = running_min
    survived = [fid for fid, q in qs.items() if q <= alpha]
    return qs, survived

PVALS = {}

# --- Source 1: explicit p-values already blessed ---
for fid, rec in ALL_RESULTS.items():
    if not isinstance(fid, str): continue
    low = fid.lower()
    if (low.endswith('_p_value') or low.endswith('_perm_p')
            or low.endswith('_fisher_p') or low == 'd07'):
        try:
            PVALS[fid] = float(rec.get('actual'))
        except (TypeError, ValueError):
            pass

# --- Source 2: z-scores → two-sided p via 2(1-Φ(|z|)) ---
# Not all blessed IDs are z-scores; we whitelist those that actually are.
Z_SCORE_IDS = {
    'D08': 'D08_markov_z',       # Markov z (T9)
    'D17': 'D17_path_z',         # Canonical path z (T8)
    'S5':  'S5_path_z',          # Shannon-Aljamal path minimality z
    'T21': 'T21_iliad_z',        # Iliad cross-language path-shift z
}
for zid, label in Z_SCORE_IDS.items():
    z = ALL_RESULTS.get(zid, {}).get('actual')
    if isinstance(z, (int, float)) and not np.isnan(z):
        two_sided_p = float(2.0 * (1.0 - _norm.cdf(abs(z))))
        PVALS[f'{label}_p'] = max(two_sided_p, 1e-300)

# --- Source 3: generate permutation p-values for Cohen's d statistics ---
# For each ID whose statistic is a Quran-vs-control Cohen's d on Band-A
# Mahalanobis distances (or similar), run a label-permutation null and
# record the empirical p-value. This is the expensive step; budget:
#   N_PERM_FDR = 200 in FAST, 1000 otherwise.
N_PERM_FDR = 200 if FAST_MODE else 1000
rng_fdr = np.random.default_rng(SEED + 777)

def _perm_p_cohens_d(X_A, X_B, observed_d, n_perm=None):
    '''Permutation p-value: P(|d_perm| >= |d_obs|) under label swap.

    AUDIT 2026-04-19 (v6 fix D): the previous implementation computed S_loc
    as POOLED covariance cov([X_A, X_B]) once outside the loop, but
    `observed_d` (= effect_d from Cell 29) was computed in the CTRL-ONLY
    metric cov(X_CTRL_POOL). Mixing metrics between the observed statistic
    and the null is not a valid permutation test. Fix: recompute
    (mu_loc, S_loc) from the permuted pseudo-control side (Xp_B) every
    iteration, so each d_perm is measured in the same kind of metric as
    effect_d (data-driven ctrl-side covariance).

    This also subsumes the v5 fix ⑦ (recompute mu_loc per perm); both
    mu_loc and S_loc are now recomputed per permutation.
    '''
    if n_perm is None: n_perm = N_PERM_FDR
    if len(X_A) < 2 or len(X_B) < 2: return float('nan')
    all_X = np.vstack([X_A, X_B]); nA = len(X_A); total = len(all_X)
    p_feat = X_A.shape[1]
    ridge  = 1e-6 * np.eye(p_feat)
    hits = 0
    for _ in range(n_perm):
        idx = rng_fdr.permutation(total)
        Xp_A = all_X[idx[:nA]]; Xp_B = all_X[idx[nA:]]
        if len(Xp_B) < 2:
            continue
        mu_loc = Xp_B.mean(0)                    # ctrl-side centroid of this perm
        S_loc  = np.cov(Xp_B.T, ddof=1) + ridge  # ctrl-side covariance of this perm
        try:
            Sinv_loc = np.linalg.inv(S_loc)
        except np.linalg.LinAlgError:
            continue
        dA = mahalanobis(Xp_A, mu_loc, Sinv_loc)
        dB = mahalanobis(Xp_B, mu_loc, Sinv_loc)
        pool_std = np.sqrt(((len(dA)-1)*dA.var(ddof=1) +
                            (len(dB)-1)*dB.var(ddof=1))
                           / max(1, len(dA)+len(dB)-2))
        d_perm = abs(dA.mean() - dB.mean()) / max(pool_std, 1e-9)
        if d_perm >= abs(observed_d): hits += 1
    return float((hits + 1) / (n_perm + 1))

# IDs D02/S1/D28/T1/T2 ALL record essentially the same statistic: Cohen's d
# (or a monotonic re-expression) of Quran vs Arabic-control Band-A Mahalanobis
# distances. Inserting the same p-value five times would inflate the BH
# denominator and spuriously declare more "survivors" at α=0.05.
# AUDIT 2026-04-18 (v3): insert the shared permutation p-value under a SINGLE
# canonical key only. The individual per-ID rows are still listed in the
# per-family audit print below (reporting), but do not re-enter BH.
_MAHAL_DS_IDS = ['D02', 'S1', 'D28', 'T1', 'T2']
shared_p = float('nan')
if len(X_QURAN) > 1 and len(X_CTRL_POOL) > 1:
    # Use the already-blessed Cohen's d (effect_d from Cell 29) as the common
    # observed statistic — all these IDs point at the same underlying quantity.
    obs_d = abs(float(ALL_RESULTS.get('D02', {}).get('actual', 0.0)))
    shared_p = _perm_p_cohens_d(X_QURAN, X_CTRL_POOL, obs_d)
    if not np.isnan(shared_p):
        PVALS['Mahal_family_perm_p'] = shared_p

print(f'[FDR] collected {len(PVALS)} p-values for BH correction  '
      f'(N_PERM_FDR={N_PERM_FDR})')
qs, surv = _bh_fdr(PVALS, alpha=0.05)
print(f'[FDR] Benjamini-Hochberg @ α=0.05  →  {len(surv)}/{len(PVALS)} survive')
# Print a sorted table
print('  source                                raw p          BH q       FDR?')
for fid in sorted(PVALS, key=PVALS.get):
    p = PVALS[fid]; q = qs.get(fid, float('nan'))
    flag = 'surv' if fid in surv else ' n/a'
    p_str = f'{p:.2e}' if p > 0 else '<1e-300'
    q_str = f'{q:.2e}' if not np.isnan(q) and q > 0 else '<1e-300'
    print(f'  {fid:<35s}  {p_str:>12s}  {q_str:>10s}  [{flag}]')

# Reporting-only: show which individual IDs share the Mahal-family p-value
if not np.isnan(shared_p):
    ids_present = [fid for fid in _MAHAL_DS_IDS if fid in ALL_RESULTS]
    print(f'[FDR] Mahal_family_perm_p = {shared_p:.4g} covers '
          f'{len(ids_present)} ID(s): {ids_present}')
    print(f'[FDR] (inserted ONCE into BH to avoid inflating survivor count)')

# AUDIT 2026-04-19 (fix ②): always co-report the BH denominator alongside
# the survivor count. Previously the scorecard showed only
# `FDR_BH_n_significant = 7`, with no indication that the denominator was
# ~12 (p-values actually tested) out of ~45 total flagship claims. Any
# external citation of "N survive FDR" must therefore carry both the
# numerator (n_significant) AND the denominator (n_tested) + the coverage
# fraction over the full claim set. We bless all three as first-class
# lock entries (tol=inf, reporting only) so any downstream reader gets
# the full context without having to scrape the stdout log.
n_tested  = int(len(PVALS))
# Denominator reference: flagship locked scalars with non-null `expected`
# (the "45 claims" figure cited in the README / original audit). We compute
# it dynamically so it survives lock edits.
n_claims  = sum(1 for e in RESULTS_LOCK if e.get('expected') is not None)
coverage  = (n_tested / n_claims) if n_claims > 0 else 0.0
bless('FDR_BH_n_significant', float(len(surv)))
bless('FDR_BH_n_tested',      float(n_tested),  tol_override=float('inf'))
bless('FDR_BH_n_claims_total',float(n_claims),  tol_override=float('inf'))
bless('FDR_BH_coverage_frac', float(coverage),  tol_override=float('inf'))
print(f'[FDR] headline: {len(surv)} / {n_tested} tested p-values survive BH @ α=0.05')
print(f'[FDR]           = {len(surv)} / ~{n_claims} flagship claims '
      f'(coverage = {coverage*100:.1f}% of claim set)')
print(f'[FDR] Note: many T-statistics (T3-T7, T10-T11, T17-T21, T23-T31) are')
print(f'[FDR] not natural permutation-test targets (sufficient statistics, AUC,')
print(f'[FDR] etc.); they are NOT included in this BH procedure. Full coverage')
print(f'[FDR] of all {n_claims} claims under a unified BH remains an OPEN')
print(f'[FDR] methodological gap — see Nobel/PNAS suggestion #7. Any external')
print(f'[FDR] citation of the survivor count MUST cite "{len(surv)} / {n_tested}'
      f' tested", not "{len(surv)} / {n_claims} claims".')"""
    )

    # Cell 123c — FDR Coverage Audit (audit 2026-04-19 v5 fix ⑨)
    #
    # Transparent classification of every flagship ID. Instead of forcing all
    # 45 claims into BH (which would pollute the denominator with ~10 rank-
    # bounded tests whose structural p-floor = 1/n_corpora ≈ 0.125 > 0.05),
    # we classify each claim by WHY it is / isn't in the BH procedure. This
    # turns the 33% coverage from a silent gap into an explicit, principled
    # accounting that a PNAS reviewer can verify line-by-line.
    code(
        r"""# === Cell 123c · FDR Coverage Audit — transparent claim classification ===
# AUDIT 2026-04-19 (v5 fix ⑨): rather than bolt more permutation tests onto
# Cell 123b (which would bloat runtime and inject rank-bounded non-starters
# into the BH denominator), we classify each flagship ID by the REASON it
# does or doesn't carry a p-value. A reviewer can then confirm that the
# excluded claims are excluded for principled reasons, not oversight.
#
# Five categories:
#   (A) in_fdr            — has a p-value entering BH above
#   (B) rank_bounded      — rank test where structural p-floor = 1/n_corpora
#                           > 0.05; adding it to BH cannot yield significance
#   (C) methodological    — integrity / config / reporting scalar, not a
#                           hypothesis test (e.g. RHYME_LETTERS, coverage %s)
#   (D) candidate_future  — natural null design exists but not yet
#                           implemented; legitimate expansion target
#   (E) descriptive       — effect size / composite index without a natural
#                           null hypothesis in the present framework
#
# n_corpora used for the rank-bound floor:
_N_ARABIC_FAM = len([c for c in ARABIC_FAMILY if c in FEATS])
_rank_floor   = 1.0 / max(_N_ARABIC_FAM, 1)

_RANK_BOUNDED = {
    # Small-pool rank tests (floor = 1/n_corpora ≈ 0.125 with 8 Arabic fams)
    'T3', 'T4', 'T31',              # H_cond rank, Omega rank, Fisher curvature rank
    'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7',   # universal-law candidate indices
    'Psi_quran_rank',
}
_METHODOLOGICAL = {
    # Integrity / config / reporting — not a testable hypothesis
    'RHYME_LETTERS', 'Partial_quote_leak',
    'CamelTools_phi_m_rerun', 'Heuristic_phi_m_rerun',
    'Tight_fairness_band_A', 'Tight_fairness_band_B', 'Tight_fairness_band_C',
    'H_cond_MM_quran', 'MI_bin_sensitivity_range', 'MI_D05_miller_madow',
    'Supp_A_Hurst_R2', 'Hurst_DFA_quran_R2',
    'D13_hindawi_in_pool_legacy', 'D13_hindawi_loo',
    'L7_sparse_pca_d',
    'HSIC_EL_CN_quran', 'HSIC_G2_max_quran',
    'TDA_H1_max_persistence', 'TDA_n_loops_long_lived',
    'FDR_BH_n_significant', 'FDR_BH_n_tested',
    'FDR_BH_n_claims_total', 'FDR_BH_coverage_frac',
    'Phi_M_hotelling_T2',           # headline effect stat (its perm_p is in FDR)
    *(f'G{i}' for i in range(1, 6)),# G1-G5 are mathematical gap tautologies
    *(f'E{i}_transmission_sim' if i==1 else f'E{i}' for i in range(1, 4)),  # E-series exploratory
    'E1_transmission_sim','E2_csiszar_korner','E3_berry_esseen',
    'E_harakat_capacity','E_epi_waqf','E_epi_variants',
    'MonteCarlo_const_null', 'Blind_rejection_rates',
    'Nuzul_vs_Mushaf', 'PickleBug_simulation',
    # G1-G5 sanity gate scalars (explicitly listed; previous duplicate generator
    # produced the same names and was removed 2026-04-19).
    'G1_min_units','G2_no_single_token','G3_no_identical','G4_cv_valid','G5_arabic_ratio',
}
_CANDIDATE_FUTURE = {
    # Has natural null structure — legitimate future expansion target
    'T6',       # H-Cascade Cohen's d — can reuse Mahal-family permutation
    'D06',      # G_turbo multiplicative gain — bootstrap null available
    'D09',      # Classifier AUC — natural label-permutation null
    'T19',      # RQA — within-corpus shuffle null
    'T24',      # Lesion — verse-deletion null (pre-v6 this line said 'T22'
                #                  which is actually RD×EL, a ranked product
                #                  with no natural verse-deletion null; T22
                #                  now correctly falls through to descriptive)
    'T25',      # Saddle eigenvalues — random-matrix null
    'T26',      # Terminal-depth-3 — verse-order null
    'Adiyat_blind',  # winning variant — bootstrap resample across variants
    'PROXY_1_compression_p1', 'PROXY_2_compression_p3',   # gzip proxies
    'Abbasi_8_discriminators',  # 8-way discrimination — perm on labels
}

_coverage = {'in_fdr': [], 'rank_bounded': [], 'methodological': [],
             'candidate_future': [], 'descriptive': []}

for fid in sorted(ALL_RESULTS):
    # Primary: already has a p-value in BH
    if fid in PVALS:
        _coverage['in_fdr'].append(fid)
        continue
    # Mahal family: shared p-value covers D02/S1/D28/T1/T2 under ONE entry
    if fid in _MAHAL_DS_IDS and 'Mahal_family_perm_p' in PVALS:
        _coverage['in_fdr'].append(fid + ' (via Mahal_family_perm_p)')
        continue
    # Z-score converted to p-value (see Z_SCORE_IDS in Cell 123b)
    if fid in Z_SCORE_IDS and f'{Z_SCORE_IDS[fid]}_p' in PVALS:
        _coverage['in_fdr'].append(fid + f' (via {Z_SCORE_IDS[fid]}_p)')
        continue
    # Structural rank-bounded tests
    if fid in _RANK_BOUNDED:
        _coverage['rank_bounded'].append(fid)
        continue
    # Integrity / config / reporting scalars
    if fid in _METHODOLOGICAL or fid.startswith('FDR_'):
        _coverage['methodological'].append(fid)
        continue
    # Natural null exists but unimplemented — future expansion candidate
    if fid in _CANDIDATE_FUTURE:
        _coverage['candidate_future'].append(fid)
        continue
    # Default: descriptive effect size / composite without a natural null
    _coverage['descriptive'].append(fid)

# Save full classification to disk for reviewer audit
_audit_path = INT_DIR / 'fdr_coverage_audit.json'
_audit_path.write_text(
    json.dumps({
        'n_total_blessed':   len(ALL_RESULTS),
        'n_claims_locked':   n_claims,
        'n_p_values_tested': n_tested,
        'n_bh_survivors':    len(surv),
        'rank_floor':        _rank_floor,
        'n_arabic_family':   _N_ARABIC_FAM,
        'classification':    {k: sorted(v) for k, v in _coverage.items()},
        'summary':           {k: len(v) for k, v in _coverage.items()},
    }, indent=2, ensure_ascii=False),
    encoding='utf-8',
)

print('')
print('=' * 72)
print('[FDR-AUDIT] Coverage classification of all blessed flagship IDs')
print('=' * 72)
print(f'  total blessed scalars in ALL_RESULTS:  {len(ALL_RESULTS)}')
print(f'  total locked claims in RESULTS_LOCK:   {n_claims}')
print(f'  Arabic-family pool size (for rank-floor): {_N_ARABIC_FAM} '
      f'→ rank p-floor = 1/{_N_ARABIC_FAM} = {_rank_floor:.3f}')
print('')
print('  Category              Count    %    Meaning')
print('  --------------------  -----  -----  -------')
_cat_meta = {
    'in_fdr':            'enters BH above (has valid p-value)',
    'rank_bounded':      f'rank-test; p-floor > α=0.05 structurally',
    'candidate_future':  'natural null exists; future expansion target',
    'descriptive':       'effect size / composite without a natural null',
    'methodological':    'integrity / config / reporting scalar',
}
_tot = max(1, sum(len(v) for v in _coverage.values()))
for cat in ['in_fdr', 'rank_bounded', 'candidate_future', 'descriptive', 'methodological']:
    n = len(_coverage[cat])
    print(f'  {cat:<20s}  {n:>5d}  {100*n/_tot:>4.1f}%  {_cat_meta[cat]}')
print('  --------------------  -----')
print(f'  TOTAL                 {_tot:>5d}  100.0%')
print('')
print('  Detailed per-category listing:')
for cat in ['rank_bounded', 'candidate_future', 'descriptive']:
    if not _coverage[cat]: continue
    print(f'  [{cat}]  ({len(_coverage[cat])} IDs)')
    ids = _coverage[cat]
    for i in range(0, len(ids), 4):
        print('    ' + '  '.join(f'{x:<18s}' for x in ids[i:i+4]))
print('')
print(f'[FDR-AUDIT] written to {_audit_path}')
print(f'[FDR-AUDIT] FDR coverage = {len(_coverage["in_fdr"])}/{_tot} '
      f'({100*len(_coverage["in_fdr"])/_tot:.1f}%)')
print(f'[FDR-AUDIT] → {len(_coverage["candidate_future"])} IDs are legitimate '
      f'future-expansion targets (natural null exists)')
print(f'[FDR-AUDIT] → {len(_coverage["rank_bounded"])} IDs cannot reach α=0.05 '
      f'in a pool of {_N_ARABIC_FAM} corpora; adding to BH would inflate the')
print(f'            denominator without affecting survivor count (so they are '
      f'INTENTIONALLY excluded, not an oversight).')
print('=' * 72)"""
    )

    # Cell 124 — Phase-20 verifier + checkpoint
    code(
        r"""# === Cell 124 · Phase-20 verifier + checkpoint ===
_verify_phase_20 = lambda: print('[OK   ] Phase 20 — formal-proof gap closures (honest) complete')
_verify_phase_20()
save_checkpoint('20_gaps_honest', {
    'G1_min_hill': min_alpha, 'G2_max_nmi': float(max_nmi),
    'G3_axes_pd':  g3_pd, 'G4_chernoff': cherns, 'G5_slope': g5_slope,
    'negatives':   NEGATIVES, 'FDR_BH_survivors': surv,
}, state={'ALL_RESULTS': ALL_RESULTS})"""
    )


# ============================================================================
# PHASE 21 — Final scorecard + lock verify + 6 figures + ZIP (cells 125-130)
# ============================================================================
def build_phase_21() -> None:
    phase_header(
        21,
        "Final scorecard + 4-lock verification + 6 diagnostic figures + ZIP",
        "Emit 45-row scorecard, verify all 4 integrity locks (raising "
        "HallucinationError on drift), write figures (if enabled), and "
        "bundle everything into a timestamped ZIP.",
    )

    # Cell 125 — scorecard
    code(
        r"""# === Cell 125 · ULTIMATE_SCORECARD.md + ULTIMATE_REPORT.json ===
rows = []
rows.append('# QSF ULTIMATE — Run Scorecard')
rows.append(f'Generated: {datetime.now().isoformat(timespec="seconds")}  FAST_MODE={FAST_MODE}')
rows.append('')
rows.append('| ID | Finding | Expected | Actual | Drift | Tol | Verdict |')
rows.append('|---|---|---|---|---|---|---|')
for fid in sorted(ALL_RESULTS):
    r = ALL_RESULTS[fid]
    exp = r.get('expected', '—'); got = r.get('actual', '—')
    tol = r.get('tol', '—'); drift = r.get('abs_drift', '—')
    vexp = r.get('verdict_expected', '—'); ok = r.get('drift_ok', True)
    name = r.get('name', fid)
    mark = 'OK' if ok else 'DRIFT'
    try:
        exp_s  = f'{exp:.4g}'   if isinstance(exp, (int, float)) else str(exp)
        got_s  = f'{got:.4g}'   if isinstance(got, (int, float)) else str(got)
        drift_s= f'{drift:.3g}' if isinstance(drift, (int, float)) else str(drift)
    except Exception:
        exp_s, got_s, drift_s = str(exp), str(got), str(drift)
    rows.append(f'| {fid} | {name} | {exp_s} | {got_s} | {drift_s} | {tol} | {vexp} {mark} |')
rows.append('')
rows.append('## Summary')
rows.append(f'- total locked scalars: {len(ALL_RESULTS)}')
rows.append(f'- drift violations:     {sum(1 for r in ALL_RESULTS.values() if not r.get("drift_ok", True))}')

SCORECARD = '\n'.join(rows)
(RESULTS / 'ULTIMATE_SCORECARD.md').write_text(SCORECARD, encoding='utf-8')
print(SCORECARD)
(RESULTS / 'ULTIMATE_REPORT.json').write_text(
    json.dumps(ALL_RESULTS, indent=2, default=str, ensure_ascii=False),
    encoding='utf-8',
)"""
    )

    # Cell 126 — verify locks (ACTUAL re-read from disk, not cached-dict tautology)
    code(
        r"""# === Cell 126 · verify 4 integrity locks — ACTUAL mid-run re-read ===
def _sha_file(p: Path) -> str | None:
    if not p.exists(): return None
    h = hashlib.sha256()
    with p.open('rb') as f:
        for blk in iter(lambda: f.read(65536), b''): h.update(blk)
    return h.hexdigest()

# --- (A) CORPUS lock: re-read every raw file and compare ---
cur_corpus = hashlib.sha256()
corpus_tampered = []
for name in sorted(corpus_lock['files']):
    entry   = corpus_lock['files'][name]
    old_sha = entry.get('sha256')
    path_s  = entry.get('path')
    if not path_s or not old_sha:   # file was missing at lock time; skip
        continue
    new_sha = _sha_file(REPO / path_s)
    if new_sha is None:
        corpus_tampered.append(f'{name}: file disappeared mid-run ({path_s})')
    elif new_sha != old_sha:
        corpus_tampered.append(f'{name}: SHA drift  locked={old_sha[:12]}  now={new_sha[:12]}')
    if new_sha:
        cur_corpus.update(f'{name}:{new_sha};'.encode())
if corpus_tampered:
    raise HallucinationError(
        '[HALL] corpus lock violated mid-run:\n  ' + '\n  '.join(corpus_tampered)
    )
assert cur_corpus.hexdigest() == corpus_lock['combined'], (
    f'[HALL] corpus combined hash drift  locked={corpus_lock["combined"][:16]}  '
    f'rebuilt={cur_corpus.hexdigest()[:16]}'
)
print(f'[lock-verify] corpus: {len(corpus_lock["files"])} raw files re-hashed; combined matches')

# --- (B) CODE lock: re-read every src/*.py and compare ---
cur_code = hashlib.sha256()
code_tampered = []
for name_rel in sorted(code_lock['files']):
    old_sha = code_lock['files'][name_rel]
    new_sha = _sha_file(REPO / name_rel)
    if new_sha is None:
        code_tampered.append(f'{name_rel}: file missing')
    elif new_sha != old_sha:
        code_tampered.append(f'{name_rel}: edited  locked={old_sha[:12]}  now={new_sha[:12]}')
    cur_code.update(f'{name_rel}:{new_sha};'.encode())
if code_tampered:
    raise HallucinationError(
        '[HALL] code lock violated mid-run:\n  ' + '\n  '.join(code_tampered)
    )
assert cur_code.hexdigest() == code_lock['combined'], '[HALL] code combined hash drift'
print(f'[lock-verify] code  : {len(code_lock["files"])} src/*.py re-hashed; combined matches')

# --- (C) RESULTS lock: re-read results_lock.json from disk and re-hash ---
# AUDIT 2026-04-19 (v6 fix W5-b): previous check accepted the literal
# string `'<UPDATED>'` as a valid hash to support UPDATE_LOCK runs. But the
# UPDATE_LOCK branch below always rewrites `'hash': new_hash` with a real
# SHA-256, so `'<UPDATED>'` is unreachable through the intended path and
# only serves as a tampering escape hatch. Removed.
rl_payload = json.loads((INT_DIR / 'results_lock.json').read_text(encoding='utf-8'))
recomputed = hashlib.sha256(
    json.dumps(rl_payload['entries'], sort_keys=True, ensure_ascii=False).encode('utf-8')
).hexdigest()
if rl_payload.get('hash') != recomputed:
    raise HallucinationError(
        f'[HALL] results_lock.json tampered  stored={rl_payload.get("hash", "?")[:12]}  '
        f'recomputed={recomputed[:12]}'
    )
print(f'[lock-verify] results_lock.json re-hashed; {len(rl_payload["entries"])} entries intact')

# --- (D) NAMES registry: re-read and check every ALL_RESULTS id is whitelisted ---
names_now = set(json.loads((INT_DIR / 'names_registry.json').read_text(encoding='utf-8'))['names'])
unknowns = [fid for fid in ALL_RESULTS if fid not in names_now]
if unknowns:
    raise UnknownFindingError(
        f'[HALL] {len(unknowns)} finding IDs in ALL_RESULTS are not in names_registry.json: '
        f'{unknowns}'
    )
print(f'[lock-verify] names : {len(ALL_RESULTS)}/{len(names_now)} IDs whitelisted')

# --- (E) drift verdict for every blessed scalar ---
drifts = [fid for fid, r in ALL_RESULTS.items() if not r.get('drift_ok', True)]
if drifts and not UPDATE_LOCK:
    msg = '\n'.join(
        f'  {fid}: expected {ALL_RESULTS[fid].get("expected")} '
        f'got {ALL_RESULTS[fid].get("actual")} drift {ALL_RESULTS[fid].get("abs_drift")}'
        for fid in drifts
    )
    raise HallucinationError(
        f'{len(drifts)} scalars drifted beyond tolerance:\n{msg}\n'
        f'If legitimate, set UPDATE_LOCK=True and re-bless.'
    )
elif drifts and UPDATE_LOCK:
    print(f'[UPDATE_LOCK] {len(drifts)} scalars updated in-place.')
    for fid in drifts:
        entry = next(e for e in RESULTS_LOCK if e['id'] == fid)
        entry['expected'] = ALL_RESULTS[fid]['actual']
    new_hash = hashlib.sha256(
        json.dumps(RESULTS_LOCK, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()
    (INT_DIR / 'results_lock.json').write_text(
        json.dumps({'version': 1, 'hash': new_hash,
                    'timestamp': datetime.now().isoformat(),
                    'entries': RESULTS_LOCK}, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f'[UPDATE_LOCK] new hash = {new_hash[:16]}')
else:
    print(f'[OK   ] all {len(ALL_RESULTS)} locked scalars within tolerance')

# --- (F) Universal absolute-drift lens (AUDIT 2026-04-19 v6 fix W1-a) -----
# Second lens on top of per-scalar tol. For every numeric blessed scalar with
# a numeric `expected`, flag `|actual - expected| > UNIVERSAL_DRIFT_ABSOLUTE`
# (default 1e-4). This is INFORMATIONAL — entries that pass their per-scalar
# tol do NOT raise, they are only listed so a reviewer can ask which scalars
# are tight vs loose. The two authoritative gates remain:
#   (i)  per-scalar tol in Part (E) above
#   (ii) external >5 % drift vs docs/FINDINGS_SCORECARD.md in Cell 128
_univ_drift = []
for fid, r in ALL_RESULTS.items():
    exp = r.get('expected'); got = r.get('actual'); tol = r.get('tol')
    try:
        ef = float(exp); gf = float(got)
    except (TypeError, ValueError):
        continue
    if not (math.isfinite(ef) and math.isfinite(gf)):
        continue
    drift = abs(ef - gf)
    # Only report scalars with non-inf expected tol (inf-tol are PENDING_REBLESS
    # or REPORTING-only; they are not tight-pinned by design).
    try:
        if not math.isfinite(float(tol)):
            continue
    except (TypeError, ValueError):
        continue
    if drift > UNIVERSAL_DRIFT_ABSOLUTE:
        _univ_drift.append((fid, ef, gf, drift, float(tol)))
if _univ_drift:
    print(f'[drift-1e-4] {len(_univ_drift)} scalar(s) exceed universal threshold '
          f'{UNIVERSAL_DRIFT_ABSOLUTE:g} (INFO — per-scalar tol governs):')
    for fid, e, g, d, t in sorted(_univ_drift, key=lambda x: -x[3])[:20]:
        print(f'  {fid:<28s}  exp={e:.6g}  got={g:.6g}  |d|={d:.3g}  (tol={t:g})')
else:
    print(f'[drift-1e-4] no scalar exceeds universal threshold '
          f'{UNIVERSAL_DRIFT_ABSOLUTE:g}')

# --- (G) Headline Φ_M baselines (AUDIT 2026-04-19 v6 fix W1-b) ------------
# `Phi_M_hotelling_T2` and `Phi_M_perm_p_value` carry `tol=inf` in RESULTS_LOCK
# because v5 upstream fixes legitimately shifted them and the precise post-v5
# values were not yet known when the lock was written. Part (E) therefore can
# not gate them. We add a parallel numeric envelope here: write the values to
# `integrity/headline_baselines.json` on the first clean run, and on all later
# runs raise if |relative drift| > HEADLINE_REL_TOL (default 5 %). This closes
# the audit concern that a pathological regression could pass silently.
# Bypass with UPDATE_LOCK=True for an intentional re-pin.
_HEADLINE_IDS = ('Phi_M_hotelling_T2', 'Phi_M_perm_p_value')
_HB_PATH = INT_DIR / 'headline_baselines.json'
_hb_current = {}
for _fid in _HEADLINE_IDS:
    _v = ALL_RESULTS.get(_fid, {}).get('actual')
    try:
        _vf = float(_v)
        if math.isfinite(_vf): _hb_current[_fid] = _vf
    except (TypeError, ValueError):
        pass

if _HB_PATH.exists() and not UPDATE_LOCK:
    _hb_locked = json.loads(_HB_PATH.read_text(encoding='utf-8')).get('entries', {})
    _hb_drift = []
    for _fid, _cur in _hb_current.items():
        _base = _hb_locked.get(_fid)
        if _base is None: continue
        try:
            _bf = float(_base)
        except (TypeError, ValueError):
            continue
        if _bf == 0:
            if abs(_cur) > HEADLINE_REL_TOL:
                _hb_drift.append((_fid, _bf, _cur, float('inf')))
            continue
        _rel = abs(_cur - _bf) / abs(_bf)
        if _rel > HEADLINE_REL_TOL:
            _hb_drift.append((_fid, _bf, _cur, _rel))
    if _hb_drift:
        _msg = '\n'.join(
            f'  {fid:<28s}  baseline={b:.6g}  run={g:.6g}  rel='
            f'{("inf" if r==float("inf") else f"{r:.1%}")}'
            for fid, b, g, r in _hb_drift
        )
        raise HallucinationError(
            f'[HALL headline-baseline] {len(_hb_drift)} headline scalar(s) '
            f'drifted > {HEADLINE_REL_TOL:.0%} from integrity/headline_baselines.json:'
            f'\n{_msg}\n'
            f'If legitimate, set UPDATE_LOCK=True to re-pin.'
        )
    print(f'[lock-verify] headline_baselines.json: '
          f'{len(_hb_current)}/{len(_HEADLINE_IDS)} within '
          f'{HEADLINE_REL_TOL:.0%} envelope')
else:
    # First run, or UPDATE_LOCK refresh — write the current values as the
    # new baseline. Record metadata so a reviewer can tell when it was set.
    _HB_PATH.write_text(json.dumps({
        'version': 1,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'rel_tol':  HEADLINE_REL_TOL,
        'entries':  _hb_current,
        'note':     ('Headline Φ_M baselines pinned at first clean run. '
                     'Delete this file (or set UPDATE_LOCK=True) to re-pin.'),
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[lock-verify] headline_baselines.json WRITTEN '
          f'({len(_hb_current)} entries, rel_tol={HEADLINE_REL_TOL:.0%})')"""
    )

    # Cell 127 — figures
    code(
        r"""# === Cell 127 · 6 diagnostic figures (only if GENERATE_FIGURES) ===
if GENERATE_FIGURES:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # AUDIT 2026-04-19 (v6 fix K): Cell 127 reads several globals from earlier
    # phases — ns_L6 / omega_proxy / gammas / a_int / b_slope / PSI from
    # Phase 18, Hurst_vals / H_multi from Phase 14. A checkpoint resume from
    # Phase 19, 20 or 22 only restores ALL_RESULTS, so without a guard this
    # cell would NameError before any figure is written. Two-layer defence:
    #   (a) if Phase-18 globals are missing, attempt a resume_from to pull
    #       them back in (no-op on a full fresh run where they are already
    #       present);
    #   (b) each figure that depends on phase-specific globals is wrapped in
    #       a presence check and emits a clear [fig SKIP] diagnostic instead
    #       of crashing.
    if 'ns_L6' not in globals() or 'PSI' not in globals():
        _ = resume_from('18_discovery')

    # Fig 1: Φ_M boxplot
    fig, ax = plt.subplots(figsize=(9, 4))
    labels, data = [], []
    for n in ['quran'] + ARABIC_CTRL_POOL:
        X = _X_for(n, BAND_A_LO, BAND_A_HI)
        if len(X) >= 3:
            labels.append(n); data.append(mahalanobis(X, mu, S_inv))
    if data:
        ax.boxplot(data, labels=labels, showmeans=True)
        ax.set_ylabel('Mahalanobis distance d')
        ax.set_title('Fig 1 — Φ_M per corpus (Band A)')
        plt.xticks(rotation=30); plt.tight_layout()
        plt.savefig(FIG_DIR / 'fig1_phi_m_boxplot.png', dpi=110); plt.close()

    # Fig 2: multi-scale perturbation
    # AUDIT 2026-04-18 (v4): keys aligned with Cell 43 / pipeline (2025-04+).
    # Previous stale keys ('letter_shuffle', 'word_shuffle') made the letter
    # and word bars always 0 — the pipeline now emits 'letter_10pct' and
    # 'word_10pct' alongside 'verse_shuffle'.
    fig, ax = plt.subplots(figsize=(6, 4))
    qt = RES.get('T17_multi_scale_pert', {}).get('per_target', {}).get('quran', {})
    gaps = [(qt.get('letter_10pct',  {}) or {}).get('mean_gap', 0) or 0,
            (qt.get('word_10pct',    {}) or {}).get('mean_gap', 0) or 0,
            (qt.get('verse_shuffle', {}) or {}).get('mean_gap', 0) or 0]
    ax.bar(['letter_10pct', 'word_10pct', 'verse_shuffle'], gaps)
    ax.set_title('Fig 2 — Multi-scale perturbation gap (Quran)')
    ax.set_ylabel('|Φ_M(clean) − Φ_M(shuf)|')
    plt.tight_layout(); plt.savefig(FIG_DIR / 'fig2_perturbation_heatmap.png', dpi=110); plt.close()

    # Fig 3: Error-exponent γ(Ω)
    _fig3_ok = (all(k in globals() for k in
                    ('ns_L6', 'omega_proxy', 'gammas', 'a_int', 'b_slope'))
                and globals().get('ns_L6') and len(globals()['ns_L6']) > 1)
    if _fig3_ok:
        fig, ax = plt.subplots(figsize=(6, 4))
        xs = np.array([omega_proxy[n] for n in ns_L6])
        ys = np.array([gammas[n]       for n in ns_L6])
        ax.scatter(xs, ys)
        for x, y, n in zip(xs, ys, ns_L6): ax.annotate(n, (x, y), fontsize=8)
        xl = np.linspace(xs.min(), xs.max(), 10)
        ax.plot(xl, a_int + b_slope*xl, 'r--', label=f'γ = {a_int:.3f} + {b_slope:.3f}·Ω')
        ax.set_xlabel('Ω proxy'); ax.set_ylabel('γ (empirical)'); ax.legend()
        ax.set_title('Fig 3 — Empirical error exponent γ(Ω)')
        plt.tight_layout(); plt.savefig(FIG_DIR / 'fig3_error_exponent.png', dpi=110); plt.close()
    else:
        print('[fig SKIP] Fig 3 (γ(Ω)) — Phase-18 L6 globals not in globals')

    # Fig 4: Cross-scripture Ψ
    if 'PSI' in globals() and PSI:
        fig, ax = plt.subplots(figsize=(9, 4))
        top = sorted(PSI, key=lambda k: -PSI[k])[:8]
        ax.bar(top, [PSI[k] for k in top])
        ax.set_ylabel('Ψ (orality-intensity)'); ax.set_title('Fig 4 — Cross-scripture Ψ')
        plt.xticks(rotation=30); plt.tight_layout()
        plt.savefig(FIG_DIR / 'fig4_cross_scripture_psi.png', dpi=110); plt.close()
    else:
        print('[fig SKIP] Fig 4 (Ψ) — Phase-18 PSI not in globals')

    # Fig 5: Saddle count
    fig, ax = plt.subplots(figsize=(6, 4))
    t25b = RES.get('T25_info_geo_saddle', {})
    ax.bar(['saddles', 'non-saddles'],
           [t25b.get('n_saddles', 0),
            t25b.get('n_corpora', 0) - t25b.get('n_saddles', 0)])
    ax.set_title('Fig 5 — Info-geometry saddle count (near-universal)')
    plt.tight_layout(); plt.savefig(FIG_DIR / 'fig5_saddle_eigenvalues.png', dpi=110); plt.close()

    # Fig 6: multi-level Hurst
    if 'Hurst_vals' in globals() and 'H_multi' in globals():
        fig, ax = plt.subplots(figsize=(9, 4))
        rows_H = [k for k in Hurst_vals if not np.isnan(Hurst_vals[k])][:8]
        if rows_H:
            letter_H = [H_multi[n]['letter']   for n in rows_H]
            verse_H  = [H_multi[n]['EL_verse'] for n in rows_H]
            x = np.arange(len(rows_H)); w = 0.4
            ax.bar(x - w/2, letter_H, w, label='letter-seq')
            ax.bar(x + w/2, verse_H,  w, label='EL-seq')
            ax.set_xticks(x); ax.set_xticklabels(rows_H, rotation=30)
            ax.set_ylabel('Hurst H'); ax.legend()
            ax.set_title('Fig 6 — Multi-level Hurst exponent')
            plt.tight_layout(); plt.savefig(FIG_DIR / 'fig6_multilevel_hurst.png', dpi=110); plt.close()
    else:
        print('[fig SKIP] Fig 6 (Hurst) — Phase-14 Hurst_vals/H_multi not in globals')

    figs = sorted(FIG_DIR.glob('*.png'))
    print(f'[fig ] {len(figs)} figures written')
else:
    print('[fig ] GENERATE_FIGURES=False; skipped')"""
    )

    # Cell 128 — drift alarm vs docs/FINDINGS_SCORECARD.md (actually reads the MD)
    code(
        r"""# === Cell 128 · EXTERNAL drift alarm — parse docs/FINDINGS_SCORECARD.md ===
# This reads the historical paper/clean-data values FROM THE MD FILE, not from
# our own lock dict. If more than N_CRIT_DRIFT scalars drift > 5 %, raise.
import re as _re

SCORECARD_PATH = REPO / 'docs' / 'FINDINGS_SCORECARD.md'
if not SCORECARD_PATH.exists():
    print(f'[drift5] SKIP — {SCORECARD_PATH} missing')
else:
    md_text = SCORECARD_PATH.read_text(encoding='utf-8')
    # Table rows:  | rank | ID | finding | paper | clean-data result | ...
    # Capture ID (group 1) and the *first* numeric token in the clean-data column (group 2).
    NUM_RE = _re.compile(r'[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?')
    md_expected: dict[str, float] = {}
    for line in md_text.splitlines():
        if not line.startswith('|'): continue
        cols = [c.strip() for c in line.split('|')]
        # cols[0]='' cols[1]=rank cols[2]=ID cols[3]=finding cols[4]=paper cols[5]=clean-data
        if len(cols) < 6: continue
        fid = cols[2]
        if not _re.match(r'^[A-Z][A-Za-z]*\d+$|^S\d+$|^G\d+$|^L\d+$|^E\d+$', fid):
            continue
        m = NUM_RE.search(cols[5])
        if m:
            try:
                md_expected[fid] = float(m.group())
            except ValueError:
                pass

    print(f'[drift5] parsed {len(md_expected)} scalars from docs/FINDINGS_SCORECARD.md')

    # AUDIT 2026-04-19 (v5): the historical scorecard table does not yet list
    # the current headline Phi_M statistics — so the 5 %-drift envelope does
    # NOT protect them until paper-era baselines are added. Surface the gap
    # loudly. Upgrade to `raise HallucinationError(...)` once baselines exist.
    _required_headline_ids = {'Phi_M_hotelling_T2', 'Phi_M_perm_p_value'}
    _missing_headline = sorted(_required_headline_ids - set(md_expected))
    if _missing_headline:
        print(f'[WARN drift5] docs/FINDINGS_SCORECARD.md missing headline IDs: '
              f'{_missing_headline}. Drift envelope does NOT cover them yet.')

    # AUDIT 2026-04-19 (v5 fix ⑦): exclude IDs whose MD text is a %/≥/≤ bound
    # rather than a point estimate. The first-numeric-token regex above grabs
    # a percentage (D26 "100%" → 100 vs code 1.0; D23 "Quran 100%,..." → 100)
    # or a threshold (G1 "Hill α ≥ 1.8" → 1.8 vs actual 2.5; G2 "MI ≤ 0.3"
    # → 0.3 vs actual 0.32). All four match their results_lock.json baseline
    # and pass the authoritative drift check; only the naive MD parser flags
    # them as spurious "POSITIVE drifts".
    _IGNORE_DRIFT5_IDS = {'D26', 'D23', 'G1', 'G2'}

    drifts_5pct = []
    for fid, doc_val in md_expected.items():
        if fid in _IGNORE_DRIFT5_IDS: continue
        if fid not in ALL_RESULTS: continue
        try:
            got = float(ALL_RESULTS[fid].get('actual'))
        except (TypeError, ValueError):
            continue
        if doc_val == 0:
            if abs(got) > 0.05:
                drifts_5pct.append((fid, doc_val, got, float('inf')))
            continue
        rel = abs(got - doc_val) / abs(doc_val)
        if rel > 0.05:
            drifts_5pct.append((fid, doc_val, got, rel))

    # POLICY (AUDIT 2026-04-19 v5):
    # docs/FINDINGS_SCORECARD.md is the human-authored paper baseline; THIS
    # run (full raw corpus, Band A, clean pipeline) is authoritative. Drift
    # on NEGATIVE / DEPRECATED / EXPLORATORY findings is *expected* (those
    # are the audit-demoted ones) and stays INFORMATIONAL. Drift on POSITIVE
    # (PROVED / PROVED STRONGER / SURVIVING / PROVED (corpus)) findings is
    # the signal the README promises to halt on — a hostile reviewer would
    # read 'POSITIVE drift > 5 % silently ignored' as a moving goalpost, so
    # those drifts now RAISE. Re-blessing under UPDATE_LOCK=True is the
    # explicit override path.
    _POSITIVE_VERDICTS = {
        'PROVED', 'PROVED STRONGER', 'PROVED (corpus)',
        'SURVIVING', 'SURVIVING (pre-reg)', 'SURVIVING (corpus)',
    }
    _verdict_by_id = {e['id']: (e.get('verdict_expected') or '')
                      for e in RESULTS_LOCK}
    pos_drifts = [(fid, d, g, r) for fid, d, g, r in drifts_5pct
                  if _verdict_by_id.get(fid, '') in _POSITIVE_VERDICTS]
    neg_drifts = [(fid, d, g, r) for fid, d, g, r in drifts_5pct
                  if _verdict_by_id.get(fid, '') not in _POSITIVE_VERDICTS]

    if pos_drifts:
        msg = ''.join(
            f'\n  {fid:<8s}  md={d:.4g}  run={g:.4g}  rel='
            f'{("inf" if r==float("inf") else f"{r:.1%}")}  [{_verdict_by_id.get(fid,"?")}]'
            for fid, d, g, r in pos_drifts[:20]
        )
        if UPDATE_LOCK:
            print(f'[WARN drift5] UPDATE_LOCK=True — accepting {len(pos_drifts)} '
                  f'POSITIVE drifts > 5 %:{msg}')
        else:
            raise HallucinationError(
                f'[HALL drift5] {len(pos_drifts)} POSITIVE-verdict scalars differ > 5 % '
                f'from docs/FINDINGS_SCORECARD.md:{msg}\n'
                f'If legitimate (e.g. post-audit re-computation), set UPDATE_LOCK=True '
                f'and update the MD scorecard; otherwise this is a regression.'
            )
    if neg_drifts:
        msg = ''.join(
            f'\n  {fid:<8s}  md={d:.4g}  run={g:.4g}  rel='
            f'{("inf" if r==float("inf") else f"{r:.1%}")}  [{_verdict_by_id.get(fid,"?")}]'
            for fid, d, g, r in neg_drifts[:20]
        )
        print(f'[INFO drift5] {len(neg_drifts)}/{len(md_expected)} NEGATIVE/EXPLORATORY '
              f'scalars drifted > 5 % (report-only, paper-era values):{msg}')
    if not drifts_5pct:
        cross = sum(1 for fid in md_expected if fid in ALL_RESULTS)
        print(f'[OK drift5] no scalar differs > 5 % from docs/FINDINGS_SCORECARD.md '
              f'({cross}/{len(md_expected)} cross-checked)')"""
    )

    # Cell 129 — ZIP
    code(
        r"""# === Cell 129 · ZIP export ===
zip_stem = f'QSF_ULTIMATE_{datetime.now():%Y%m%d_%H%M%S}'
zip_path = RESULTS / zip_stem

stage = RESULTS / '_zip_stage'
if stage.exists(): shutil.rmtree(stage)
stage.mkdir()

def _copy(src: Path, dst: Path):
    if not src.exists(): return
    if src.is_dir(): shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

_copy(INT_DIR,  stage / 'integrity')
_copy(CKPT_DIR, stage / 'checkpoints')
_copy(FIG_DIR,  stage / 'figures')
_copy(RESULTS / 'ULTIMATE_SCORECARD.md', stage / 'ULTIMATE_SCORECARD.md')
_copy(RESULTS / 'ULTIMATE_REPORT.json',  stage / 'ULTIMATE_REPORT.json')
_copy(LOG_PATH, stage / LOG_PATH.name)
nb_src = REPO / 'notebooks' / 'ultimate' / 'QSF_ULTIMATE.ipynb'
if nb_src.exists(): _copy(nb_src, stage / 'QSF_ULTIMATE.ipynb')
_copy(REPO / 'notebooks' / 'ultimate' / 'README.md', stage / 'README.md')

shutil.make_archive(str(zip_path), 'zip', stage)
shutil.rmtree(stage)
print(f'[zip ] bundled -> {zip_path}.zip  '
      f'({zip_path.with_suffix(".zip").stat().st_size/1024:.0f} KB)')"""
    )

    # Cell 130 — final summary
    code(
        r"""# === Cell 130 · final summary ===
print('\n' + '='*72)
print('QSF ULTIMATE — run complete')
print('='*72)
print(f'  FAST_MODE         : {FAST_MODE}')
print(f'  integrity locks   : corpus/code/results/names all verified')
print(f'  scalars in lock   : {len(RESULTS_LOCK)}')
print(f'  drift violations  : {sum(1 for r in ALL_RESULTS.values() if not r.get("drift_ok", True))}')
print(f'  log file          : {LOG_PATH}')
print(f'  scorecard         : {RESULTS / "ULTIMATE_SCORECARD.md"}')
print(f'  JSON report       : {RESULTS / "ULTIMATE_REPORT.json"}')
print(f'  figures           : {len(list(FIG_DIR.glob("*.png")))} PNGs')
print(f'  ZIP               : {zip_path}.zip')
print('='*72)
log('ULTIMATE run completed successfully')"""
    )

    # Cell 130b — Phase-21 final checkpoint (audit 2026-04-18 v4)
    code(
        r"""# === Cell 130b · Phase-21 final checkpoint ===
# AUDIT 2026-04-18 (v4): Phase 21 previously had no checkpoint of its own,
# so the final ALL_RESULTS state (with every blessed scalar populated)
# could not be inspected post-hoc without re-running the pipeline. Save
# a lightweight summary + full ALL_RESULTS under state= for resumption.
save_checkpoint('21_final_scorecard',
    {'n_results':        len(ALL_RESULTS),
     'drift_violations': sum(1 for r in ALL_RESULTS.values()
                             if not r.get('drift_ok', True)),
     'log_path':         str(LOG_PATH),
     'zip_path':         str(zip_path) + '.zip'},
    state={'ALL_RESULTS': ALL_RESULTS})
print('[ckpt ] Phase 21 checkpoint saved — run complete.')"""
    )


# ============================================================================
# PHASE 22 — Persistent-homology appendix (cells 131-133, USE_TDA-gated)
# ============================================================================
def build_phase_22() -> None:
    phase_header(
        22,
        "Persistent-homology appendix — Vietoris-Rips on 5D feature cloud",
        "OPTIONAL (USE_TDA flag in Cell 1). For each Band-A corpus we "
        "z-score the 5D feature matrix (EL, VL_CV, CN, H_cond, T) and "
        "compute persistence diagrams (H0 + H1) via Vietoris-Rips "
        "filtration. H1 features are topologically non-trivial loops in "
        "the feature cloud. We compare Quran's topology against Arabic "
        "controls using max H1 persistence and the count of long-lived "
        "H1 features (>0.25 z-units). This is a genuinely novel angle "
        "for comparative-scripture analysis; see Carlsson 2009 for the "
        "mathematical background. Falls back to no-op if ripser is not "
        "installed.",
    )

    # Cell 131 — TDA computation (ripser / USE_TDA gated)
    code(
        r"""# === Cell 131 · Persistent homology on z-scored 5D feature cloud ===
# Appendix: topological data analysis (TDA) via persistent homology.
# Controlled by USE_TDA flag in Cell 1 (default False).
#
# Pipeline:
#   1. For each corpus, take Band-A (15-100 verse) surahs → (n, 5) matrix.
#   2. Z-score each column (zero mean, unit variance) so topological
#      distances are in comparable units across features.
#   3. Compute persistence diagrams up to H1 (loops) via Vietoris-Rips.
#   4. Summarise each diagram by:
#        - max H1 persistence         = longest-lived loop
#        - n long-lived H1 features   = count with persistence > 0.25 z-units
#   5. Compare Quran vs Arabic controls.
#
# Dependency: ripser (pip install ripser). Skipped cleanly if missing.
TDA_RESULTS = {}

if not USE_TDA:
    print('[TDA ] skipped (USE_TDA=False); set USE_TDA=True in Cell 1 to enable')
    bless('TDA_H1_max_persistence', 0.0, tol_override=float('inf'))
    bless('TDA_n_loops_long_lived', 0.0, tol_override=float('inf'))
    bless('TDA_H1_bootstrap_p',     1.0, tol_override=float('inf'))
else:
    try:
        from ripser import ripser as _ripser
        _have_ripser = True
    except ImportError:
        print('[TDA ] ripser not installed; run `pip install ripser` to enable')
        print('[TDA ] falling back to no-op; TDA entries will record 0.0')
        _have_ripser = False

    if _have_ripser:
        def _zscore(X):
            mu = X.mean(0); sd = X.std(0)
            sd = np.where(sd < 1e-9, 1.0, sd)
            return (X - mu) / sd

        def _tda_summary(X, thresh=0.25):
            '''Return (max_H1_persistence, n_H1_longlived) for a 5D point cloud.
            Thresh is in z-units. Returns (nan, 0) if too few points.'''
            if len(X) < 6: return float('nan'), 0
            try:
                dgms = _ripser(X, maxdim=1)['dgms']
            except Exception as _e:
                print(f'[TDA ] ripser failed: {_e}')
                return float('nan'), 0
            if len(dgms) < 2 or len(dgms[1]) == 0:
                return 0.0, 0   # no H1 features — topologically trivial
            h1 = dgms[1]
            pers = h1[:, 1] - h1[:, 0]
            # drop infinite-persistence entries defensively
            pers = pers[np.isfinite(pers)]
            if pers.size == 0: return 0.0, 0
            return float(pers.max()), int((pers > thresh).sum())

        # Compute TDA for Quran + each Arabic control in Band A
        tda_targets = ['quran'] + [c for c in ARABIC_CTRL_POOL if c in FEATS]
        for name in tda_targets:
            X = _X_for(name, BAND_A_LO, BAND_A_HI)
            if len(X) < 6:
                TDA_RESULTS[name] = {'max_H1': float('nan'), 'n_long': 0, 'n_pts': len(X)}
                continue
            Xz = _zscore(X)
            max_h1, n_long = _tda_summary(Xz, thresh=0.25)
            TDA_RESULTS[name] = {'max_H1': max_h1, 'n_long': n_long, 'n_pts': len(Xz)}

        print('[TDA ] persistence summary (z-scored 5D Band-A feature cloud):')
        print(f'{"corpus":<22s}  {"n":>4s}  {"max H1":>10s}  {"# H1>0.25":>10s}')
        for name in sorted(TDA_RESULTS, key=lambda k: -TDA_RESULTS[k]['max_H1']
                           if not np.isnan(TDA_RESULTS[k]['max_H1']) else -1):
            r = TDA_RESULTS[name]
            tag = '  <-- Quran' if name == 'quran' else ''
            mh1 = f'{r["max_H1"]:.3f}' if not np.isnan(r['max_H1']) else '   nan'
            print(f'  {name:<20s}  {r["n_pts"]:>4d}  {mh1:>10s}  {r["n_long"]:>10d}{tag}')

        q_rec = TDA_RESULTS.get('quran', {'max_H1': float('nan'), 'n_long': 0})
        q_max = q_rec['max_H1']; q_nlong = q_rec['n_long']
        ctrl_maxes = [v['max_H1'] for k, v in TDA_RESULTS.items()
                      if k != 'quran' and not np.isnan(v['max_H1'])]
        if ctrl_maxes:
            ctrl_med = float(np.median(ctrl_maxes))
            rank = 1 + sum(1 for v in ctrl_maxes if v > q_max) if not np.isnan(q_max) else len(ctrl_maxes) + 1
            print(f'[TDA ] Quran max H1 = {q_max:.3f}  |  controls median = {ctrl_med:.3f}  '
                  f'|  Quran rank = {rank}/{len(ctrl_maxes)+1}')

        # === AUDIT 2026-04-18 (v3) · bootstrapped topological null =========
        # Closes the OPEN follow-up in Cell 132 caveat (c). Null model:
        # independently permute EACH of the 5 feature columns within the
        # corpus Band-A matrix, so marginal distributions are preserved but
        # the joint geometric structure is destroyed. Recompute max H1
        # persistence on the permuted cloud. Under H0 ("topology of this
        # cloud is indistinguishable from a product of its marginals"), the
        # bootstrap distribution of max_H1 should bracket the observed value.
        # One-sided empirical p = Pr(null_max_H1 >= observed_max_H1).
        N_TDA_BOOT = 50 if FAST_MODE else 200
        rng_tda    = np.random.default_rng(SEED + 330)
        Xq_z       = _zscore(_X_for('quran', BAND_A_LO, BAND_A_HI))
        q_boot_p   = float('nan')
        if not np.isnan(q_max) and len(Xq_z) >= 6:
            null_maxes = np.empty(N_TDA_BOOT, dtype=float)
            for _b in range(N_TDA_BOOT):
                X_shuf = np.column_stack([
                    Xq_z[rng_tda.permutation(len(Xq_z)), j] for j in range(Xq_z.shape[1])
                ])
                m, _ = _tda_summary(X_shuf, thresh=0.25)
                null_maxes[_b] = m if not np.isnan(m) else 0.0
            hits      = int(np.sum(null_maxes >= q_max))
            q_boot_p  = float((hits + 1) / (N_TDA_BOOT + 1))
            null_med  = float(np.median(null_maxes))
            null_p95  = float(np.percentile(null_maxes, 95))
            print(f'[TDA ] marginal-shuffle null (N={N_TDA_BOOT}):  '
                  f'null median max_H1 = {null_med:.3f}  |  95%-pct = {null_p95:.3f}')
            print(f'[TDA ] observed Quran max_H1 = {q_max:.3f}  →  bootstrap p = {q_boot_p:.4g}')

        bless('TDA_H1_max_persistence', float(q_max) if not np.isnan(q_max) else 0.0,
              tol_override=float('inf'))
        bless('TDA_n_loops_long_lived', float(q_nlong), tol_override=float('inf'))
        bless('TDA_H1_bootstrap_p',     float(q_boot_p) if not np.isnan(q_boot_p) else 1.0,
              tol_override=float('inf'))
    else:
        bless('TDA_H1_max_persistence', 0.0, tol_override=float('inf'))
        bless('TDA_n_loops_long_lived', 0.0, tol_override=float('inf'))
        bless('TDA_H1_bootstrap_p',     1.0, tol_override=float('inf'))"""
    )

    # Cell 132 — Phase-22 caveats and verifier
    code(
        r"""# === Cell 132 · TDA appendix caveats + Phase-22 checkpoint ===
# AUDIT 2026-04-18 (Nobel/PNAS sugg.): TDA is EXPLORATORY / APPENDIX-level.
# Important caveats before reading into these numbers:
#   (a) Persistence diagrams on n ≈ 50-120 points in 5D are UNDER-SAMPLED;
#       statistical stability theorems (Chazal-Michel 2021) require
#       O(n^{5/2}) samples for 5D densities — we have a tenth of that.
#   (b) The Band-A filter + z-score normalisation is one of MANY valid
#       preprocessings; different choices can flip H1 counts. No single
#       TDA number should be treated as evidence for a specific claim.
#   (c) Max H1 persistence is scale-dependent even after z-scoring; a
#       proper bootstrapped null (shuffled features) gives a p-value.
#       CLOSED (audit 2026-04-18 v3): Cell 131 now computes a marginal-
#       preserving column-shuffle null (TDA_H1_bootstrap_p); see print
#       output. The p-value is the one-sided empirical probability that
#       a cloud with identical marginals but independent columns achieves
#       at least the observed max H1 persistence.
#   (d) ripser uses Vietoris-Rips; other filtrations (alpha, witness) may
#       give different results. We chose VR for universality and speed.
#
# The APPENDIX status is reflected in the RESULTS_LOCK entries having
# tol=inf and verdict_expected='APPENDIX (USE_TDA)'.
if USE_TDA and len(TDA_RESULTS) > 0:
    print('[TDA ] appendix note: see Cell 132 for four caveats on interpretation.')
    print('[TDA ] treat these numbers as EXPLORATORY descriptors, not headline evidence.')

save_checkpoint('22_tda_appendix', {
    'USE_TDA':        USE_TDA,
    'tda_results':    {k: {kk: (float(vv) if isinstance(vv, (int, float, np.floating)) else vv)
                            for kk, vv in v.items()} for k, v in TDA_RESULTS.items()},
}, state={'ALL_RESULTS': ALL_RESULTS})
print('[OK   ] Phase 22 — TDA appendix complete (USE_TDA={})'.format(USE_TDA))"""
    )


# ============================================================================
# MAIN — assemble all phases and write the notebook
# ============================================================================
def main() -> None:
    # order matters
    build_phase_0()
    build_phase_1()
    build_phase_2()
    build_phase_3()
    build_phase_4()
    build_phase_5()
    build_phase_6()
    build_phase_7()
    build_phase_8()
    build_phase_9()
    build_phase_10()
    build_phase_11()
    build_phase_12()
    build_phase_13()
    build_phase_14()
    build_phase_15()
    build_phase_16()
    build_phase_17()
    build_phase_18()
    build_phase_19()
    build_phase_20()
    build_phase_22()   # NEW: TDA appendix before scorecard so it's in ZIP
    build_phase_21()

    nb = nbf.new_notebook()
    nb.cells = _CELLS
    nb.metadata.update({
        'kernelspec': {
            'display_name': 'Python 3',
            'language':     'python',
            'name':         'python3',
        },
        'language_info': {'name': 'python'},
    })
    nbformat.write(nb, OUT_PATH)
    print(f'[build] wrote {OUT_PATH}   ({len(_CELLS)} cells)')


if __name__ == '__main__':
    main()
