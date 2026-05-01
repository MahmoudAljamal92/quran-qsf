"""
exp104d_F53_mark1/run.py
========================
H59d: F53 multi-compressor consensus K=2 cross-tradition Greek NT Mark 1
amendment pilot (fourth PREREG in the H59 amendment chain; first non-Semitic).

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol byte-for-byte identical to exp104c EXCEPT:
- target language: Hebrew -> Koine Greek
- target chapter: Psalm 78 -> Mark 1 (NT book 41 chapter 1)
- corpus: WLC Tanakh -> OpenGNT v3.3 (data/corpora/el/opengnt_v3_3.csv)
- alphabet: 22 Hebrew consonants -> 24 Greek letters (vowels written)
- normaliser: NFD + strip-marks + casefold + final-sigma fold + 24-letter whitelist
- peer pool: narrative Tanakh books -> NT narrative books outside Mark
  (Matthew=40, Luke=42, John=43, Acts=44, Hebrews=58)

All numeric thresholds inherited verbatim from experiments/exp104_F53_tanakh_pilot.
No tau transfer from Hebrew or Arabic; calibration is from-scratch on Greek peers.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Inherit compressor primitives and locked numerics from exp104
from experiments.exp104_F53_tanakh_pilot import run as exp104_run  # noqa: E402
from experiments._lib import safe_output_dir  # noqa: E402

EXP = "exp104d_F53_mark1"
HYPOTHESIS_ID = "H59d"

# Live-progress log file (immediate-flush; tail with PowerShell Get-Content -Wait)
_PROGRESS_LOG = _ROOT / "results" / "experiments" / EXP / "progress.log"
_PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
_progress_fh = open(_PROGRESS_LOG, "w", encoding="utf-8", buffering=1)


def _log(msg: str) -> None:
    print(msg, flush=True)
    _progress_fh.write(msg + "\n")
    _progress_fh.flush()


# PREREG hash from PREREG_HASH.txt (written when PREREG was finalised)
_PREREG_EXPECTED_HASH = (
    "48ddbef186060365e7bb6db4b71bd1b6e31621effab283b994eb093fb8e139e3"
)

# Greek-specific frozen constants
GREEK_LETTERS_24 = "αβγδεζηθικλμνξοπρστυφχψω"
assert len(GREEK_LETTERS_24) == 24, f"alphabet length: {len(GREEK_LETTERS_24)}"

TARGET_BOOK_NUMBER = 41        # Mark in OpenGNT internal numbering
TARGET_CHAPTER = 1
TARGET_NAME = "Mark 1"

# Peer pool: NT narrative books outside Mark
PEER_BOOK_NUMBERS = (40, 42, 43, 44, 58)  # Matt, Luke, John, Acts, Hebrews

# Normaliser sentinel from PREREG §4.3 (post-erratum 2026-04-28 night:
# expected output applies the §2.1 final-sigma fold rule, yielding 14 chars
# ending in medial σ rather than final ς; pre-erratum value was a typo).
_NORMALISER_SENTINEL_INPUT = "Ἐν ἀρχῇ ἦν ὁ λόγος"
_NORMALISER_SENTINEL_EXPECTED = "εναρχηηνολογοσ"

# Per-chapter floors (inherited from exp104.PSALM_19_MIN_*)
TARGET_MIN_LETTERS = exp104_run.PSALM_19_MIN_LETTERS  # 1000
TARGET_MIN_VERSES = exp104_run.PSALM_19_MIN_VERSES    # 10


# ---------------------------------------------------------------------------
# Greek normaliser
# ---------------------------------------------------------------------------
# Sigma-fold map: all sigma forms collapse to medial σ (U+03C3).
# Source forms encountered in OpenGNT v3.3:
#   σ U+03C3  GREEK SMALL LETTER SIGMA               -> σ (identity)
#   ς U+03C2  GREEK SMALL LETTER FINAL SIGMA         -> σ
#   ϲ U+03F2  GREEK LUNATE SIGMA SYMBOL              -> σ (used in OGNTk column)
#   Σ U+03A3  GREEK CAPITAL LETTER SIGMA             -> σ (via casefold)
#   Ϲ U+03F9  GREEK CAPITAL LUNATE SIGMA SYMBOL      -> σ
_SIGMA_FOLD_MAP = {
    "ς": "σ",
    "ϲ": "σ",
    "Ϲ": "σ",  # capital lunate sigma; casefold may not lower it on all builds
}


def _normalise_greek(text: str) -> str:
    """Greek 24-letter skeleton.

    Steps (locked from PREREG §2.1, with sigma-fold extended to all sigma
    variants encountered in OpenGNT v3.3):
    1. Unicode NFD decomposition
    2. Drop all combining marks (Unicode category 'Mn')
    3. casefold() to lowercase (Greek-aware)
    4. Fold all sigma variants (ς, ϲ, Ϲ) -> medial σ
    5. Whitelist only the 24 lowercase Greek letters; drop everything else
       (whitespace, punctuation, digits, Latin letters, etc.)
    """
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.combining(ch):
            continue
        cf = ch.casefold()
        for sub in cf:
            sub = _SIGMA_FOLD_MAP.get(sub, sub)
            if sub in GREEK_LETTERS_24:
                out.append(sub)
    return "".join(out)


def _normaliser_sentinel_check() -> bool:
    """Verify the locked sentinel from PREREG §4.3."""
    actual = _normalise_greek(_NORMALISER_SENTINEL_INPUT)
    return actual == _NORMALISER_SENTINEL_EXPECTED


# ---------------------------------------------------------------------------
# OpenGNT v3.3 TSV loader
# ---------------------------------------------------------------------------
def _opengnt_path() -> Path:
    return _ROOT / "data" / "corpora" / "el" / "opengnt_v3_3.csv"


# OpenGNT v3.3 compound-field syntax (verified by Python repr() inspection):
#   〔 U+3014  LEFT TORTOISE SHELL BRACKET              (opening bracket)
#   〕 U+3015  RIGHT TORTOISE SHELL BRACKET             (closing bracket)
#   ｜ U+FF5C  FULLWIDTH VERTICAL LINE                  (inner separator)
# These are NOT the ASCII | nor French «». Pre-erratum draft of run.py
# assumed « / » / | which yielded 0-chapter loader output; corrected after
# pre-stage diagnostic (no compression calls issued).
_OPENGNT_BRACKET_OPEN = "〔"
_OPENGNT_BRACKET_CLOSE = "〕"
_OPENGNT_INNER_SEP = "｜"


def _strip_brackets(field: str) -> str:
    """Strip OpenGNT v3.3 outer brackets (〔 ... 〕), tolerating ASCII / French variants."""
    s = field.strip()
    while s and s[0] in (_OPENGNT_BRACKET_OPEN, "«", "‹", "<"):
        s = s[1:]
    while s and s[-1] in (_OPENGNT_BRACKET_CLOSE, "»", "›", ">"):
        s = s[:-1]
    return s.strip()


def _split_inner(s: str) -> list[str]:
    """Split on OpenGNT v3.3 fullwidth inner separator ｜, tolerating ASCII |."""
    if _OPENGNT_INNER_SEP in s:
        return s.split(_OPENGNT_INNER_SEP)
    return s.split("|")


def _parse_bcv(bcv_field: str) -> tuple[int, int, int] | None:
    """Parse a 'Book｜Chapter｜Verse' compound field. Returns (b, c, v) or None."""
    s = _strip_brackets(bcv_field)
    parts = _split_inner(s)
    if len(parts) < 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _parse_text_compound(text_field: str) -> str:
    """Compound field: 〔OGNTk｜OGNTu｜OGNTa｜lexeme｜rmac｜sn〕.

    Per PREREG §2.1 we use OGNTk (first sub-field, Koine Greek primary form).
    """
    s = _strip_brackets(text_field)
    parts = _split_inner(s)
    return parts[0] if parts else ""


def _load_greek_nt_chapters() -> list[dict]:
    """Parse OpenGNT v3.3 TSV; return per-chapter aggregates with normalised skeleton."""
    csv_path = _opengnt_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"OpenGNT corpus missing: {csv_path}")

    # Group tokens by (book, chapter, verse)
    grouped: dict[tuple[int, int], dict[int, list[str]]] = {}

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        try:
            _header = next(reader)
        except StopIteration:
            return []

        for row in reader:
            if len(row) < 8:
                continue
            # OpenGNT v3.3 column layout (0-indexed):
            #   0: OGNTsort   1: TANTTsort   2: FEATURESsort1
            #   3: LevinsohnClauseID   4: OTquotation
            #   5: «BGBsort|LTsort|STsort»   6: «Book|Chapter|Verse»
            #   7: «OGNTk|OGNTu|OGNTa|lexeme|rmac|sn»
            #   8+: BDAG / EDNT / Mounce / GK / LN, transliterations, glosses
            bcv = _parse_bcv(row[6])
            if bcv is None:
                continue
            book, chapter, verse = bcv
            token = _parse_text_compound(row[7])
            if not token:
                continue
            grouped.setdefault((book, chapter), {}).setdefault(verse, []).append(token)

    # Build per-chapter records
    out: list[dict] = []
    for (book, chapter), verses_dict in sorted(grouped.items()):
        verse_keys = sorted(verses_dict.keys())
        verse_strings = [" ".join(verses_dict[v]) for v in verse_keys]
        full_text = " ".join(verse_strings)
        skeleton = _normalise_greek(full_text)
        out.append({
            "book": book,
            "chapter": chapter,
            "n_verses": len(verse_keys),
            "n_letters": len(skeleton),
            "letters_24": skeleton,
            # raw kept for receipt traceability; small enough at chapter scope
            "verses_raw": verse_strings,
        })
    return out


# ---------------------------------------------------------------------------
# Variant enumeration (Greek 24-letter alphabet)
# ---------------------------------------------------------------------------
def _enumerate_variants_greek(skeleton: str) -> list[tuple[int, str, str]]:
    """Single-letter substitution enumeration on Greek skeleton.

    Returns (position, original, replacement) for every position × every other
    of the 24 Greek letters. Total = n_letters × 23.
    """
    out: list[tuple[int, str, str]] = []
    alphabet = list(GREEK_LETTERS_24)
    for pos, ch in enumerate(skeleton):
        if ch not in GREEK_LETTERS_24:
            continue  # should not happen post-normaliser, but defensive
        for repl in alphabet:
            if repl == ch:
                continue
            out.append((pos, ch, repl))
    return out


# ---------------------------------------------------------------------------
# PREREG hash enforcement
# ---------------------------------------------------------------------------
def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _enforce_prereg_hash() -> str:
    actual = _prereg_hash()
    if actual != _PREREG_EXPECTED_HASH:
        raise RuntimeError(
            f"PREREG hash mismatch:\n"
            f"  expected: {_PREREG_EXPECTED_HASH}\n"
            f"  actual  : {actual}"
        )
    return actual


# ---------------------------------------------------------------------------
# Receipt writer
# ---------------------------------------------------------------------------
def _meta(chap: dict) -> dict:
    return {k: v for k, v in chap.items() if k != "verses_raw"}


def _write_receipt(verdict, msg, audit, t_start, started_at_utc,
                   prereg_hash_actual, extras):
    out_dir = safe_output_dir(EXP)
    receipt_path = out_dir / f"{EXP}.json"
    elapsed = time.time() - t_start
    completed_at_utc = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": EXP,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis": (
            "F53 K=2 multi-compressor consensus with Greek-side tau "
            "calibration closes single-letter forgery on Mark 1 at "
            "recall >= 0.999 / FPR <= 0.05. Fourth PREREG in H59 chain "
            "(first non-Semitic, first Indo-European)."
        ),
        "verdict": verdict,
        "verdict_reason": msg,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": elapsed,
        "prereg_hash": prereg_hash_actual,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp104d_F53_mark1/PREREG.md",
        "amendment_chain": [
            "exp104_F53_tanakh_pilot   (Psalm 19,  BLOCKED_psalm_19_too_short)",
            "exp104b_F53_psalm119      (Psalm 119, FAIL_audit_peer_pool_size)",
            "exp104c_F53_psalm78       (Psalm 78,  see receipt for verdict)",
            "exp104d_F53_mark1         (Mark 1,    this run)",
        ],
        "frozen_constants": {
            "SEED": exp104_run.SEED,
            "consensus_K": exp104_run.CONSENSUS_K,
            "tau_percentile": exp104_run.TAU_PERCENTILE,
            "length_match_frac": exp104_run.LENGTH_MATCH_FRAC,
            "compressors": list(exp104_run._COMPRESSOR_NAMES),
            "compressor_levels": {
                "gzip": exp104_run.GZIP_LEVEL,
                "bz2": exp104_run.BZ2_LEVEL,
                "lzma": exp104_run.LZMA_PRESET,
                "zstd": exp104_run.ZSTD_LEVEL,
            },
            "target_book_number": TARGET_BOOK_NUMBER,
            "target_chapter": TARGET_CHAPTER,
            "target_name": TARGET_NAME,
            "target_min_letters": TARGET_MIN_LETTERS,
            "target_min_verses": TARGET_MIN_VERSES,
            "peer_book_numbers": list(PEER_BOOK_NUMBERS),
            "target_n_peers": exp104_run.TARGET_N_PEERS,
            "peer_audit_floor": exp104_run.PEER_AUDIT_FLOOR,
            "n_calib_variants_per_peer": exp104_run.N_CALIB_VARIANTS_PER_PEER,
            "bootstrap_n": exp104_run.BOOTSTRAP_N,
            "bootstrap_cv_ceil": exp104_run.BOOTSTRAP_CV_CEIL,
            "recall_floor": exp104_run.RECALL_FLOOR,
            "fpr_ceil": exp104_run.FPR_CEIL,
            "n_fpr_pairs": exp104_run.N_FPR_PAIRS,
            "alphabet_size": len(GREEK_LETTERS_24),
            "alphabet": GREEK_LETTERS_24,
        },
        "audit_report": audit,
        **extras,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"# Receipt written: {receipt_path}")
    print(f"# Wall time: {elapsed:.1f} s")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    _log(f"# {EXP} -- starting (Mark 1 amendment, fourth in H59 chain; first non-Semitic)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # Audit 0: normaliser sentinel (PREREG §4.3)
    sentinel_actual = _normalise_greek(_NORMALISER_SENTINEL_INPUT)
    audit["checks"]["normaliser_sentinel_input"] = _NORMALISER_SENTINEL_INPUT
    audit["checks"]["normaliser_sentinel_expected"] = _NORMALISER_SENTINEL_EXPECTED
    audit["checks"]["normaliser_sentinel_actual"] = sentinel_actual
    if sentinel_actual != _NORMALISER_SENTINEL_EXPECTED:
        audit["ok"] = False
        audit["errors"].append("normaliser_sentinel_drift")
        return _write_receipt(
            "FAIL_audit_normaliser_drift",
            f"Greek normaliser sentinel drifted: input={_NORMALISER_SENTINEL_INPUT!r} "
            f"expected={_NORMALISER_SENTINEL_EXPECTED!r} actual={sentinel_actual!r}",
            audit, t_start, started_at_utc, actual_hash, {},
        )
    _log(f"# Normaliser sentinel OK: {_NORMALISER_SENTINEL_INPUT!r} -> {sentinel_actual!r}")

    # Step 1: load Greek NT
    _log("# Step 1: loading OpenGNT v3.3 Greek NT ...")
    try:
        chapters = _load_greek_nt_chapters()
    except FileNotFoundError as e:
        audit["ok"] = False
        audit["errors"].append(f"corpus_missing:{e}")
        return _write_receipt("BLOCKED_corpus_missing", str(e),
                              audit, t_start, started_at_utc, actual_hash, {})
    audit["checks"]["n_chapters_total"] = len(chapters)
    _log(f"# Loaded {len(chapters)} NT chapters from OpenGNT.")

    # Locate Mark 1
    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK_NUMBER
                    and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append("mark_1_not_found")
        return _write_receipt(
            "BLOCKED_corpus_missing",
            f"Mark 1 (book={TARGET_BOOK_NUMBER}, chapter={TARGET_CHAPTER}) "
            f"not found in OpenGNT.",
            audit, t_start, started_at_utc, actual_hash, {},
        )
    target = target_match[0]
    _log(f"# Mark 1 located: {target['n_verses']} verses, "
         f"{target['n_letters']} consonant-and-vowel-skeleton letters.")
    audit["checks"]["target_book_number"] = TARGET_BOOK_NUMBER
    audit["checks"]["target_chapter"] = TARGET_CHAPTER
    audit["checks"]["target_n_verses"] = target["n_verses"]
    audit["checks"]["target_n_letters"] = target["n_letters"]

    if target["n_letters"] < TARGET_MIN_LETTERS or target["n_verses"] < TARGET_MIN_VERSES:
        audit["ok"] = False
        return _write_receipt(
            "BLOCKED_mark1_too_short",
            f"Mark 1 has {target['n_letters']} letters / "
            f"{target['n_verses']} verses (need >= "
            f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES}).",
            audit, t_start, started_at_utc, actual_hash,
            {"mark_1": _meta(target)},
        )

    # Step 2: peer pool (NT narrative outside Mark, length-matched ±30%)
    target_len = target["n_letters"]
    lo = int(target_len * (1 - exp104_run.LENGTH_MATCH_FRAC))
    hi = int(target_len * (1 + exp104_run.LENGTH_MATCH_FRAC))
    peers_raw = [c for c in chapters
                 if c["book"] in PEER_BOOK_NUMBERS
                 and lo <= c["n_letters"] <= hi]
    rng = random.Random(exp104_run.SEED)
    rng.shuffle(peers_raw)
    peers = peers_raw[:exp104_run.TARGET_N_PEERS]
    n_peers = len(peers)
    _log(f"# Peer pool: {n_peers} chapters in [{lo}, {hi}] letters "
         f"(NT books {PEER_BOOK_NUMBERS}, Mark excluded by construction)")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_length_range"] = [lo, hi]

    if n_peers < exp104_run.PEER_AUDIT_FLOOR:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_floor:{n_peers}<{exp104_run.PEER_AUDIT_FLOOR}"
        )
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool {n_peers} < floor {exp104_run.PEER_AUDIT_FLOOR}.",
            audit, t_start, started_at_utc, actual_hash,
            {"mark_1": _meta(target),
             "peers_n": n_peers,
             "peer_length_range": [lo, hi]},
        )

    # Step 3: tau calibration on Greek-NT-narrative peers
    _log(f"# Step 3: calibrating tau ({n_peers} peers x "
         f"{exp104_run.N_CALIB_VARIANTS_PER_PEER} variants) ...")
    import numpy as np  # noqa: E402
    calib_deltas: dict[str, list[float]] = {n: [] for n in exp104_run._COMPRESSOR_NAMES}

    for i, peer in enumerate(peers):
        skel = peer["letters_24"]
        all_vars = _enumerate_variants_greek(skel)
        if len(all_vars) <= exp104_run.N_CALIB_VARIANTS_PER_PEER:
            sampled = all_vars
        else:
            local_rng = random.Random(exp104_run.SEED + i)
            sampled = local_rng.sample(all_vars, exp104_run.N_CALIB_VARIANTS_PER_PEER)
        for (pos, _orig, repl) in sampled:
            variant = exp104_run._apply_variant(skel, pos, repl)
            deltas = exp104_run._per_compressor_deltas(skel, variant)
            for name, d in deltas.items():
                calib_deltas[name].append(d)
        if (i + 1) % 10 == 0:
            _log(f"#   calib peer {i+1}/{n_peers} "
                 f"({time.time()-t_start:.1f}s)")

    tau: dict[str, float] = {
        name: float(np.percentile(np.asarray(arr, dtype=float),
                                  exp104_run.TAU_PERCENTILE))
        if arr else float("nan")
        for name, arr in calib_deltas.items()
    }
    _log(f"# Locked Greek tau:")
    for name, t in tau.items():
        _log(f"#   tau_{name:5s} = {t:.6f}  (n_calib={len(calib_deltas[name])})")

    # Step 4: bootstrap stability
    tau_cv: dict[str, float] = {}
    boot_rng = np.random.default_rng(exp104_run.SEED)
    for name in exp104_run._COMPRESSOR_NAMES:
        arr = np.asarray(calib_deltas[name], dtype=float)
        if len(arr) < 2:
            tau_cv[name] = float("nan"); continue
        boot_taus = []
        for _ in range(exp104_run.BOOTSTRAP_N):
            idx = boot_rng.integers(0, len(arr), len(arr))
            boot_taus.append(np.percentile(arr[idx], exp104_run.TAU_PERCENTILE))
        boot_taus = np.asarray(boot_taus, dtype=float)
        mean = float(np.mean(boot_taus))
        std = float(np.std(boot_taus, ddof=1))
        cv = std / abs(mean) if abs(mean) > 1e-12 else float("inf")
        tau_cv[name] = cv
    audit["checks"]["tau_locked"] = tau
    audit["checks"]["tau_bootstrap_cv"] = tau_cv
    _log(f"# Bootstrap CV per tau:")
    for name, cv in tau_cv.items():
        _log(f"#   CV(tau_{name:5s}) = {cv:.4f}")

    worst_cv = max((c for c in tau_cv.values() if not np.isnan(c)), default=0.0)
    if worst_cv > exp104_run.BOOTSTRAP_CV_CEIL:
        audit["ok"] = False
        return _write_receipt(
            "FAIL_audit_tau_unstable",
            f"Bootstrap CV worst = {worst_cv:.3f} > {exp104_run.BOOTSTRAP_CV_CEIL}.",
            audit, t_start, started_at_utc, actual_hash,
            {"mark_1": _meta(target),
             "peers_n": n_peers,
             "tau": tau,
             "tau_bootstrap_cv": tau_cv},
        )

    # Step 5: enumerate ALL Mark 1 single-letter variants
    mark_skel = target["letters_24"]
    variants = _enumerate_variants_greek(mark_skel)
    n_var = len(variants)
    _log(f"# Step 5: scoring {n_var} Mark 1 variants ...")
    fires_at_k = {1: 0, 2: 0, 3: 0, 4: 0}
    n_proc = 0
    t_score_start = time.time()
    for (pos, _orig, repl) in variants:
        variant = exp104_run._apply_variant(mark_skel, pos, repl)
        deltas = exp104_run._per_compressor_deltas(mark_skel, variant)
        n_above = sum(1 for name in exp104_run._COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        for k in (1, 2, 3, 4):
            if n_above >= k:
                fires_at_k[k] += 1
        n_proc += 1
        if n_proc % 2000 == 0:
            scoring_elapsed = time.time() - t_score_start
            rate = n_proc / max(1.0, scoring_elapsed)
            eta = (n_var - n_proc) / max(1.0, rate)
            _log(f"#   variant {n_proc}/{n_var} ({100.0*n_proc/n_var:.1f}%) "
                 f"scoring_elapsed {scoring_elapsed:.0f}s rate {rate:.1f}/s "
                 f"ETA {eta:.0f}s")

    recalls = {f"K={k}": fires_at_k[k] / n_var for k in (1, 2, 3, 4)}
    recall_k2 = recalls["K=2"]
    _log(f"# Mark 1 recalls: {recalls}")
    audit["checks"]["mark_1_recalls"] = recalls
    audit["checks"]["mark_1_n_variants"] = n_var

    # Step 6: FPR (peer-vs-peer pairs at length-match)
    pair_rng = random.Random(exp104_run.SEED + 1000)
    fpr_fires = 0
    n_fpr_eval = 0
    n_target_pairs = exp104_run.N_FPR_PAIRS
    for _ in range(n_target_pairs):
        if len(peers) < 2:
            break
        a, b = pair_rng.sample(peers, 2)
        deltas = exp104_run._per_compressor_deltas(a["letters_24"], b["letters_24"])
        n_above = sum(1 for name in exp104_run._COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        if n_above >= exp104_run.CONSENSUS_K:
            fpr_fires += 1
        n_fpr_eval += 1
    fpr_k2 = fpr_fires / n_fpr_eval if n_fpr_eval > 0 else float("nan")
    _log(f"# K=2 FPR = {fpr_fires}/{n_fpr_eval} = {fpr_k2:.4f}")
    audit["checks"]["fpr_k2"] = fpr_k2
    audit["checks"]["fpr_n_pairs_evaluated"] = n_fpr_eval

    # Step 7: verdict ladder (PREREG §2.4)
    if recall_k2 < exp104_run.RECALL_FLOOR:
        if (recall_k2 >= exp104_run.PARTIAL_RECALL_FLOOR and
                fpr_k2 <= exp104_run.FPR_CEIL):
            verdict, msg = ("PARTIAL_recall_above_99",
                            f"Recall = {recall_k2:.4f} in partial band; FPR = "
                            f"{fpr_k2:.4f} OK. Indicative; not paper-grade.")
        else:
            verdict, msg = ("FAIL_recall_below_floor",
                            f"K=2 recall = {recall_k2:.4f} < "
                            f"{exp104_run.RECALL_FLOOR}.")
    elif fpr_k2 > exp104_run.FPR_CEIL:
        verdict, msg = ("FAIL_fpr_above_ceiling",
                        f"K=2 FPR = {fpr_k2:.4f} > {exp104_run.FPR_CEIL}.")
    else:
        verdict, msg = ("PASS_consensus_100",
                        f"recall = {recall_k2:.4f} >= {exp104_run.RECALL_FLOOR} "
                        f"AND FPR = {fpr_k2:.4f} <= {exp104_run.FPR_CEIL}. "
                        f"F53 generalises to Greek NT Mark 1 (first non-Semitic "
                        f"cross-tradition F53 datapoint).")

    _log(f"# VERDICT: {verdict}")
    _log(f"# Reason: {msg}")

    return _write_receipt(
        verdict, msg, audit, t_start, started_at_utc, actual_hash,
        {
            "mark_1": _meta(target),
            "peers_n": n_peers,
            "peer_length_range": [lo, hi],
            "tau": tau,
            "tau_bootstrap_cv": tau_cv,
            "mark_1_recalls": recalls,
            "mark_1_n_variants": n_var,
            "fpr_k2": fpr_k2,
            "fpr_n_pairs": n_fpr_eval,
        },
    )


if __name__ == "__main__":
    sys.exit(main())
