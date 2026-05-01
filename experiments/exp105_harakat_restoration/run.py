"""
exp105_harakat_restoration/run.py
=================================
H37: R13 (diacritic-restoration error) is an edit-detection channel
orthogonal to R12 / gzip NCD and closes the voiceless-emphatic-stop
d=1 blind spot (ط↔ت, ق↔ك) that exp103 proved cannot be closed under
any universal compressor on the 28-letter rasm.

Builds a minimal R13 score from CamelTools morphological analyses:
  s_R13(w_c, w_e) = levenshtein(plur_diac(rasm(w_c)), plur_diac(rasm(w_e)))
                    + alpha * max(0, n_an(w_c) - n_an(w_e)) / max(1, n_an(w_c))
  with alpha = len(plur_diac(rasm(w_c))).

Calibrates tau_R13 on the same 4000 ctrl-edits used by exp41 / exp94 /
exp95, then scores Adiyat-864 and reports: overall recall, union with
R12, per-d-hamming stratum recall, E3/E5 voiceless-stop recovery.

Pre-registered in PREREG.md (frozen 2026-04-22).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                   state['CORPORA']
    results/experiments/exp94_adiyat_864/...json         R12 per-variant fire-flags
    results/experiments/exp95_phonetic_modulation/...json d_hamming per variant (optional)

Writes ONLY under results/experiments/exp105_harakat_restoration/
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp105_harakat_restoration"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
VOICELESS_STOP_PAIRS = [("ت", "ط"), ("ط", "ت"), ("ك", "ق"), ("ق", "ك")]

# --- Shared with exp41 / exp94 / exp95 -------------------------------------
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_HAMZA_MAP = str.maketrans("\u0623\u0625\u0624\u0626\u0622", "\u0621" * 5)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _rasm_word(w: str) -> str:
    """Same normalisation as src/roots.py::_norm_word: diacritics stripped,
    hamza folded to bare alef-form. Does NOT apply the 28-letter
    consonant_only fold (we want ة / ى preserved for CamelTools)."""
    return _strip_d(str(w)).translate(_HAMZA_MAP).strip()


def _letters_28(text: str) -> str:
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


# --- Phonetic feature table (byte-equal to exp54 / exp95) ------------------
PHONETIC_FEATURES = {
    "ا": (8.0, 0.5, 0, 0, 0), "ب": (1.0, 0.0, 1, 0, 0),
    "ت": (2.0, 0.0, 0, 0, 0), "ث": (2.5, 1.0, 0, 0, 0),
    "ج": (4.0, 0.5, 1, 0, 0), "ح": (7.0, 1.0, 0, 0, 0),
    "خ": (5.0, 1.0, 0, 0, 0), "د": (2.0, 0.0, 1, 0, 0),
    "ذ": (2.5, 1.0, 1, 0, 0), "ر": (2.0, 4.0, 1, 0, 0),
    "ز": (3.0, 1.0, 1, 0, 1), "س": (3.0, 1.0, 0, 0, 1),
    "ش": (3.5, 1.0, 0, 0, 1), "ص": (3.0, 1.0, 0, 1, 1),
    "ض": (2.0, 0.0, 1, 1, 0), "ط": (2.0, 0.0, 0, 1, 0),
    "ظ": (2.5, 1.0, 1, 1, 0), "ع": (7.0, 1.0, 1, 0, 0),
    "غ": (5.0, 1.0, 1, 0, 0), "ف": (1.0, 1.0, 0, 0, 0),
    "ق": (6.0, 0.0, 0, 0, 0), "ك": (5.0, 0.0, 0, 0, 0),
    "ل": (2.0, 3.0, 1, 0, 0), "م": (1.0, 2.0, 1, 0, 0),
    "ن": (2.0, 2.0, 1, 0, 0), "ه": (8.0, 1.0, 0, 0, 0),
    "و": (1.0, 5.0, 1, 0, 0), "ي": (4.0, 5.0, 1, 0, 0),
}


def _place_bin(p: float) -> int:
    if p <= 1.5:
        return 0
    if p <= 3.25:
        return 1
    if p <= 4.5:
        return 2
    if p <= 6.5:
        return 3
    if p <= 7.5:
        return 4
    return 5


def hamming_phonetic(a: str, b: str) -> int:
    if a not in PHONETIC_FEATURES or b not in PHONETIC_FEATURES:
        return 5
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    d = 0
    d += int(_place_bin(fa[0]) != _place_bin(fb[0]))
    d += int(round(fa[1]) != round(fb[1]))
    d += int(fa[2] != fb[2])
    d += int(fa[3] != fb[3])
    d += int(fa[4] != fb[4])
    return d


# --- Levenshtein (pure python, small strings) ------------------------------
def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


# --- CamelTools analyser (lazy; same DB as src/roots.py) -------------------
_ANALYZER = None
_CAMEL_ERR: str | None = None


def _get_analyzer():
    global _ANALYZER, _CAMEL_ERR
    if _ANALYZER is not None:
        return _ANALYZER
    try:
        from camel_tools.morphology.database import MorphologyDB
        from camel_tools.morphology.analyzer import Analyzer
        db = MorphologyDB.builtin_db()
        _ANALYZER = Analyzer(db)
    except Exception as e:
        _CAMEL_ERR = f"{type(e).__name__}: {e}"
        _ANALYZER = None
    return _ANALYZER


# --- Analyses cache (in-memory, per-run) -----------------------------------
_ANALYSES_CACHE: dict[str, tuple[tuple[str, ...], int]] = {}


def _analyses_diacs(rasm: str) -> tuple[tuple[str, ...], int]:
    """Return (tuple of plurality-sorted unique `diac` strings,
               total n_analyses)."""
    if rasm in _ANALYSES_CACHE:
        return _ANALYSES_CACHE[rasm]
    ana = _get_analyzer()
    if ana is None or not rasm:
        _ANALYSES_CACHE[rasm] = ((), 0)
        return _ANALYSES_CACHE[rasm]
    try:
        results = ana.analyze(rasm)
    except Exception:
        results = []
    if not results:
        _ANALYSES_CACHE[rasm] = ((), 0)
        return _ANALYSES_CACHE[rasm]
    from collections import Counter
    diacs: list[str] = []
    for r in results:
        d = r.get("diac", "") or ""
        d = d.replace("#", "")
        if d:
            diacs.append(d)
    c = Counter(diacs)
    sorted_diacs = tuple(
        d for d, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    )
    _ANALYSES_CACHE[rasm] = (sorted_diacs, len(results))
    return _ANALYSES_CACHE[rasm]


def plur_diac(rasm: str) -> str:
    diacs, _ = _analyses_diacs(rasm)
    return diacs[0] if diacs else ""


def n_analyses(rasm: str) -> int:
    _, n = _analyses_diacs(rasm)
    return n


def r13_score(w_c: str, w_e: str) -> tuple[float, dict]:
    """R13 raw score for a single word-edit, plus per-component diagnostics.

    s = lev(plur_diac(rasm(w_c)), plur_diac(rasm(w_e)))
        + alpha * max(0, n_an(w_c) - n_an(w_e)) / max(1, n_an(w_c))
      with alpha = len(plur_diac(rasm(w_c))).
    """
    r_c = _rasm_word(w_c)
    r_e = _rasm_word(w_e)
    pc = plur_diac(r_c)
    pe = plur_diac(r_e)
    nc = n_analyses(r_c)
    ne = n_analyses(r_e)
    lev = levenshtein(pc, pe)
    alpha = len(pc)
    ana_drop = max(0, nc - ne) / max(1, nc)
    s = float(lev) + alpha * ana_drop
    return s, {
        "rasm_canon": r_c,
        "rasm_edit": r_e,
        "plur_diac_canon": pc,
        "plur_diac_edit": pe,
        "n_analyses_canon": nc,
        "n_analyses_edit": ne,
        "lev": lev,
        "alpha": alpha,
        "analysis_collapse_ratio": ana_drop,
    }


# --- Perturbation (byte-equal to exp95 but returns the edited word) --------
def _apply_perturbation_with_word(verses, rng: random.Random):
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in cons if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            return {
                "vi": vi, "wi": wi, "pos": pos,
                "orig": original, "repl": repl,
                "canon_word": w, "edited_word": new_word,
            }
    return None


# --- 864 enumeration: identify the word containing the edited position ----
def _enumerate_864_with_word(v1_raw: str) -> list[dict]:
    """Enumerate byte-equal to exp94 / exp95 (walk the raw diacritized v1,
    keep positions where ch in ARABIC_CONS_28, 27 replacements each), and
    additionally identify the rasm-stripped word containing each edit so
    the R13 scorer can operate on just that word.

    Enumeration order is guaranteed identical to exp94's
    `adiyat_864_per_variant` list, so the ith element here matches the
    ith element there by construction.
    """
    out: list[dict] = []
    # Build token-boundary map on v1_raw (diacritics preserved). Since
    # tokens may contain diacritics, we walk char-by-char and at every
    # whitespace advance the token index.
    n = len(v1_raw)
    tok_idx_of = [0] * n
    tok_intra = [0] * n
    wi = 0
    intra = 0
    for i, ch in enumerate(v1_raw):
        if ch.isspace():
            # space belongs to no token; mark it as -1 so we can skip it
            # on the consonant filter (ARABIC_CONS_28 doesn't contain ' ')
            tok_idx_of[i] = -1
            tok_intra[i] = -1
            # on whitespace, advance token pointer & reset intra
            wi += 1
            intra = 0
        else:
            tok_idx_of[i] = wi
            tok_intra[i] = intra
            intra += 1
    # Collect each raw token (diacritics preserved).
    raw_tokens = v1_raw.split()
    # Rasm-strip each token for R13 input to CamelTools.
    rasm_tokens = [_rasm_word(t) for t in raw_tokens]

    for pos, ch in enumerate(v1_raw):
        if ch not in ARABIC_CONS_28:
            continue
        this_wi = tok_idx_of[pos]
        if this_wi < 0 or this_wi >= len(raw_tokens):
            continue
        raw_word = raw_tokens[this_wi]
        rasm_word = rasm_tokens[this_wi]
        # Locate `ch` inside the rasm-stripped form: since rasm-stripping
        # only removes diacritics and folds hamza, the k-th consonant of
        # raw_word (by position in the raw string) maps to the k-th
        # consonant of rasm_word (by position after stripping).
        # We identify intra_word_pos in the RASM form by counting
        # consonants of raw_word up to `pos - (start_of_this_raw_word)`.
        # Find start of this raw word in v1_raw:
        #  cumulative count of the first `this_wi` raw_tokens + spaces.
        start = 0
        for k in range(this_wi):
            start += len(raw_tokens[k]) + 1  # +1 for the separator
        intra_raw = pos - start
        # Count how many ARABIC_CONS_28 characters of raw_word come
        # before position `intra_raw` (inclusive). Those map 1:1 into
        # rasm_word (after hamza-fold some of them may land on ا).
        rasm_intra = 0
        for k in range(intra_raw):
            if raw_word[k] in ARABIC_CONS_28:
                rasm_intra += 1
        for repl in ARABIC_CONS_28:
            if repl == ch:
                continue
            # Apply the edit directly to the rasm-normalised word.
            if rasm_intra < len(rasm_word):
                edited_rasm_word = (
                    rasm_word[:rasm_intra] + repl
                    + rasm_word[rasm_intra + 1:]
                )
            else:
                # edge case (shouldn't fire for Adiyat v1); skip variant
                continue
            out.append({
                "abs_pos": pos,
                "wi": this_wi,
                "intra_raw_pos": intra_raw,
                "intra_rasm_pos": rasm_intra,
                "orig": ch,
                "repl": repl,
                "canon_word_raw": raw_word,
                "canon_word_rasm": rasm_word,
                "edited_word_rasm": edited_rasm_word,
            })
    return out


# --- Receipt loaders -------------------------------------------------------
def _load_exp94() -> dict:
    path = (_ROOT / "results" / "experiments"
            / "exp94_adiyat_864" / "exp94_adiyat_864.json")
    if not path.exists():
        raise FileNotFoundError(f"exp94 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_exp95() -> dict | None:
    path = (_ROOT / "results" / "experiments"
            / "exp95_phonetic_modulation" / "exp95_phonetic_modulation.json")
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


# --- Main ------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H37 -- R13 diacritic-restoration channel on Adiyat-864")

    # --- Step 0: CamelTools sanity ---
    ana = _get_analyzer()
    if ana is None:
        # Fail fast; write a minimal receipt so downstream tooling can see why.
        print(f"[{EXP}] FAIL_cameltools_missing: {_CAMEL_ERR}")
        outfile = out / f"{EXP}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump({
                "experiment": EXP,
                "verdict": "FAIL_cameltools_missing",
                "error": _CAMEL_ERR,
                "prereg_hash": _prereg_hash(),
            }, f, indent=2, ensure_ascii=False)
        self_check_end(pre, EXP)
        return 2

    # --- Load baselines ---
    exp94 = _load_exp94()
    exp95 = _load_exp95()
    print(f"[{EXP}] Loaded exp94 (R12 baseline recall = "
          f"{exp94['recalls_at_5pct_fpr']['R12_only_baseline']:.4f})")
    if exp95 is not None:
        print(f"[{EXP}] Loaded exp95 (per-variant d_hamming available)")

    # --- Load corpora ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    adiyat = next((u for u in CORPORA.get("quran", [])
                   if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None:
        raise RuntimeError(f"{ADIYAT_LABEL} not found in CORPORA['quran']")
    canon_verses = list(adiyat.verses)

    # Enumeration walks the RAW v1 (diacritics preserved), byte-equal
    # to exp94 / exp95, so the ith exp105 variant matches the ith
    # exp94.adiyat_864_per_variant record. Per-word R13 input is the
    # rasm-stripped form of the token containing each edit.
    v1_raw = canon_verses[0]
    v1_letters_28 = _letters_28(v1_raw)
    print(f"[{EXP}] Canonical v1 raw (with diacritics): {v1_raw}")
    print(f"[{EXP}] Canonical v1 28-letter stream: {v1_letters_28}")

    # --- Step 1: Ctrl-null calibration ---
    print(f"[{EXP}] Step 1: {CTRL_N_UNITS} ctrl units x {N_PERT_PER_UNIT} edits ...")
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(SEED + 2)

    ctrl_scores: list[float] = []
    ctrl_zero_score = 0
    ctrl_n_canon_0 = 0
    ctrl_per_d: dict[int, list[float]] = {d: [] for d in range(6)}
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        for _ in range(N_PERT_PER_UNIT):
            ed = _apply_perturbation_with_word(u.verses, rng_u)
            if ed is None:
                continue
            s, diag = r13_score(ed["canon_word"], ed["edited_word"])
            ctrl_scores.append(s)
            if s == 0:
                ctrl_zero_score += 1
            if diag["n_analyses_canon"] == 0:
                ctrl_n_canon_0 += 1
            d = hamming_phonetic(ed["orig"], ed["repl"])
            ctrl_per_d[d].append(s)
    n_ctrl = len(ctrl_scores)
    if n_ctrl == 0:
        raise RuntimeError("ctrl-null is empty; perturbation failed on every unit")
    ctrl_scores_arr = np.asarray(ctrl_scores, dtype=float)

    tau_R13 = float(np.quantile(ctrl_scores_arr, 1 - FPR_TARGET))
    # Bootstrap CI on tau
    rng_boot = np.random.RandomState(SEED)
    boots = [
        float(np.quantile(
            ctrl_scores_arr[rng_boot.choice(n_ctrl, n_ctrl, replace=True)],
            1 - FPR_TARGET))
        for _ in range(1000)
    ]
    tau_ci = (float(np.percentile(boots, 2.5)),
              float(np.percentile(boots, 97.5)))
    ctrl_zero_frac = ctrl_zero_score / n_ctrl
    ctrl_n_canon_0_frac = ctrl_n_canon_0 / n_ctrl
    print(f"[{EXP}] Ctrl-null: n={n_ctrl}  "
          f"mean={ctrl_scores_arr.mean():.4f}  sd={ctrl_scores_arr.std():.4f}  "
          f"p95={tau_R13:.4f}  max={ctrl_scores_arr.max():.4f}")
    print(f"[{EXP}]   tau_R13 = {tau_R13:.4f}  "
          f"CI95 = [{tau_ci[0]:.4f}, {tau_ci[1]:.4f}]")
    print(f"[{EXP}]   ctrl score==0 : {ctrl_zero_score}/{n_ctrl} "
          f"({ctrl_zero_frac:.3f})   "
          f"canon-unanalysable: {ctrl_n_canon_0}/{n_ctrl} "
          f"({ctrl_n_canon_0_frac:.3f})")

    # --- Step 2: Adiyat-864 scoring ---
    print(f"[{EXP}] Step 2: enumerating Adiyat 864 variants ...")
    v864 = _enumerate_864_with_word(v1_raw)
    n_var = len(v864)
    print(f"[{EXP}] Enumerated {n_var} variants (expected {EXPECTED_N_VARIANTS})")

    # Load exp94 per-variant R12 fires (same enumeration order by construction).
    per_var_exp94 = exp94.get("adiyat_864_per_variant")
    if per_var_exp94 is None or len(per_var_exp94) != n_var:
        print(f"[{EXP}] Warn: exp94 per-variant receipt missing / mismatched "
              f"(got {len(per_var_exp94) if per_var_exp94 else None}, "
              f"expected {n_var}); R12 union stats will be N/A.")
        per_var_exp94 = None

    # Byte-alignment sanity: every (pos, orig, repl) triple in our
    # enumeration must equal exp94's (pos, orig, repl) at the same index.
    alignment_ok = True
    if per_var_exp94 is not None:
        for idx, (ours, theirs) in enumerate(zip(v864, per_var_exp94)):
            if (ours["abs_pos"] != theirs["pos"]
                    or ours["orig"] != theirs["orig"]
                    or ours["repl"] != theirs["repl"]):
                alignment_ok = False
                print(f"[{EXP}] ALIGNMENT MISMATCH at idx={idx}: "
                      f"ours=({ours['abs_pos']},{ours['orig']},{ours['repl']})"
                      f" vs exp94=({theirs['pos']},{theirs['orig']},"
                      f"{theirs['repl']})")
                break
    if not alignment_ok:
        print(f"[{EXP}] Refusing to join with exp94 R12 flags: "
              f"enumeration order drifted.")
        per_var_exp94 = None

    ncd_p95 = float(exp94.get("null_stats", {})
                    .get("NCD_p95_threshold", float("inf")))

    per_variant: list[dict] = []
    for idx, vv in enumerate(v864):
        s, diag = r13_score(vv["canon_word_rasm"], vv["edited_word_rasm"])
        d = hamming_phonetic(vv["orig"], vv["repl"])
        fires_r13 = bool(s >= tau_R13)
        fires_r12 = None
        ncd_edit = None
        if per_var_exp94 is not None:
            rec = per_var_exp94[idx]
            ncd_edit = float(rec.get("NCD_edit", -1.0))
            fires_r12 = bool(ncd_edit >= ncd_p95)
        per_variant.append({
            "idx": idx,
            "abs_pos": vv["abs_pos"],
            "orig": vv["orig"],
            "repl": vv["repl"],
            "d_hamming": d,
            "canon_word_rasm": vv["canon_word_rasm"],
            "edited_word_rasm": vv["edited_word_rasm"],
            "s_R13": round(s, 6),
            "lev": diag["lev"],
            "analysis_collapse": round(diag["analysis_collapse_ratio"], 6),
            "n_an_canon": diag["n_analyses_canon"],
            "n_an_edit": diag["n_analyses_edit"],
            "plur_diac_canon": diag["plur_diac_canon"],
            "plur_diac_edit": diag["plur_diac_edit"],
            "fires_R13": fires_r13,
            "fires_R12": fires_r12,
            "NCD_edit_from_exp94": ncd_edit,
        })

    n_r13 = sum(1 for v in per_variant if v["fires_R13"])
    recall_r13 = n_r13 / n_var if n_var else float("nan")
    if per_var_exp94 is not None:
        n_r12 = sum(1 for v in per_variant if v["fires_R12"])
        n_union = sum(1 for v in per_variant
                      if v["fires_R12"] or v["fires_R13"])
        n_inter = sum(1 for v in per_variant
                      if v["fires_R12"] and v["fires_R13"])
        recall_r12 = n_r12 / n_var
        recall_union = n_union / n_var
        recall_inter = n_inter / n_var
    else:
        recall_r12 = None
        recall_union = None
        recall_inter = None

    # --- Step 3: voiceless-stop recovery audit ---
    voiceless_variants = [
        v for v in per_variant
        if (v["orig"], v["repl"]) in VOICELESS_STOP_PAIRS
    ]
    n_voice = len(voiceless_variants)
    n_voice_r13 = sum(1 for v in voiceless_variants if v["fires_R13"])
    n_voice_r12 = (
        sum(1 for v in voiceless_variants if v["fires_R12"])
        if per_var_exp94 is not None else None
    )
    voiceless_r13_rate = (
        n_voice_r13 / n_voice if n_voice > 0 else float("nan")
    )

    # --- Step 4: per-d-hamming stratum audit ---
    stratum_audit: dict[int, dict] = {}
    for d in range(6):
        in_stratum = [v for v in per_variant if v["d_hamming"] == d]
        n_s = len(in_stratum)
        n_s_r13 = sum(1 for v in in_stratum if v["fires_R13"])
        rec: dict = {
            "n_variants": n_s,
            "n_fired_R13": n_s_r13,
            "recall_R13": (n_s_r13 / n_s) if n_s else None,
            "ctrl_n_at_d": len(ctrl_per_d[d]),
            "ctrl_median_s_R13_at_d": (
                float(np.median(ctrl_per_d[d])) if ctrl_per_d[d] else None
            ),
        }
        if per_var_exp94 is not None:
            n_s_r12 = sum(1 for v in in_stratum if v["fires_R12"])
            n_s_un = sum(1 for v in in_stratum
                         if v["fires_R12"] or v["fires_R13"])
            rec["n_fired_R12"] = n_s_r12
            rec["recall_R12"] = (n_s_r12 / n_s) if n_s else None
            rec["recall_union"] = (n_s_un / n_s) if n_s else None
        stratum_audit[d] = rec

    # --- Verdict ---
    null_saturated_hard = ctrl_zero_frac > 0.50
    null_saturated_soft = 0.05 < ctrl_zero_frac <= 0.50

    if null_saturated_hard:
        verdict = "FAIL_null_saturated"
    elif n_voice == 0:
        verdict = "FAIL_no_voiceless_variants_in_adiyat_v1"
    elif voiceless_r13_rate <= 0.20:
        verdict = "PARTIAL_no_voiceless_lift"
    elif voiceless_r13_rate <= 0.50:
        verdict = "PARTIAL_partial_voiceless_lift"
    else:
        # voiceless_r13_rate > 0.50
        if recall_union is not None and recall_union >= 0.999:
            verdict = "PASS_universal_edit_coverage"
        else:
            verdict = "PASS_closes_voiceless_gap"
        if null_saturated_soft:
            verdict = "PARTIAL_null_saturated"

    elapsed = time.time() - t0

    # --- Headline printout ---
    print(f"\n{'=' * 68}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  n_variants (Adiyat-864) : {n_var}")
    print(f"  n_ctrl edits             : {n_ctrl}")
    print(f"  tau_R13 (p95)            : {tau_R13:.4f}")
    print(f"  recall_R13 (all 864)     : {recall_r13:.4f} ({n_r13}/{n_var})")
    if recall_r12 is not None:
        print(f"  recall_R12 (all 864)     : {recall_r12:.4f} "
              f"({sum(1 for v in per_variant if v['fires_R12'])}/{n_var})")
        print(f"  recall_union (R12 | R13) : {recall_union:.4f} "
              f"({sum(1 for v in per_variant if v['fires_R12'] or v['fires_R13'])}/{n_var})")
        print(f"  recall_intersect         : {recall_inter:.4f} "
              f"({sum(1 for v in per_variant if v['fires_R12'] and v['fires_R13'])}/{n_var})")
    print(f"  voiceless stops (E3 U E5): n={n_voice}  R13 fire rate = "
          f"{voiceless_r13_rate:.3f} ({n_voice_r13}/{n_voice})")
    if n_voice_r12 is not None:
        print(f"                              R12 fire rate = "
              f"{(n_voice_r12 / n_voice) if n_voice else float('nan'):.3f} "
              f"({n_voice_r12}/{n_voice})")
    print(f"{'=' * 68}")
    for d in range(6):
        rec = stratum_audit[d]
        line = (f"  d={d}  n_var={rec['n_variants']:3d}  "
                f"fired_R13={rec['n_fired_R13']:3d}  "
                f"recall_R13={rec['recall_R13']}")
        if "recall_R12" in rec:
            line += (f"   fired_R12={rec['n_fired_R12']}  "
                     f"recall_R12={rec['recall_R12']}  "
                     f"recall_union={rec['recall_union']}")
        print(line)

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": (
            "H37 -- R13 diacritic-restoration channel (CamelTools MSA) "
            "orthogonal to R12 closes the voiceless-emphatic-stop d=1 gap."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp105_harakat_restoration/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED,
            "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS,
            "fpr_target": FPR_TARGET,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "adiyat_label": ADIYAT_LABEL,
            "expected_n_variants": EXPECTED_N_VARIANTS,
            "arabic_ctrl": ARABIC_CTRL,
            "voiceless_stop_pairs": VOICELESS_STOP_PAIRS,
        },
        "cameltools": {
            "loaded": ana is not None,
            "analyses_cache_size": len(_ANALYSES_CACHE),
        },
        "ctrl_null": {
            "n": n_ctrl,
            "mean": float(ctrl_scores_arr.mean()),
            "sd": float(ctrl_scores_arr.std()),
            "p95_tau_R13": tau_R13,
            "p95_CI95": list(tau_ci),
            "max": float(ctrl_scores_arr.max()),
            "frac_zero_score": ctrl_zero_frac,
            "frac_canon_unanalysable": ctrl_n_canon_0_frac,
            "per_d_n": {str(d): len(ctrl_per_d[d]) for d in range(6)},
            "per_d_median": {
                str(d): (float(np.median(ctrl_per_d[d])) if ctrl_per_d[d] else None)
                for d in range(6)
            },
        },
        "adiyat_864": {
            "n_variants": n_var,
            "recall_R13": recall_r13,
            "recall_R12_from_exp94": recall_r12,
            "recall_union": recall_union,
            "recall_intersect": recall_inter,
        },
        "voiceless_stop_audit": {
            "pairs": VOICELESS_STOP_PAIRS,
            "n_voiceless_variants": n_voice,
            "n_fired_R13": n_voice_r13,
            "voiceless_R13_rate": voiceless_r13_rate,
            "n_fired_R12_from_exp94": n_voice_r12,
            "voiceless_R12_rate_from_exp94": (
                (n_voice_r12 / n_voice) if (n_voice and n_voice_r12 is not None)
                else None
            ),
        },
        "stratum_audit": {str(d): stratum_audit[d] for d in range(6)},
        "per_variant": per_variant,
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
