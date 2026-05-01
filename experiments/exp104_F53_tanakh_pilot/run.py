"""
exp104_F53_tanakh_pilot/run.py
==============================
H59: F53 multi-compressor consensus K=2 cross-tradition Hebrew Psalm 19 pilot.

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol mirrors exp95c (Arabic Quran Q:100 single-letter forgery detection)
on Hebrew Tanakh:

    1. Load Hebrew Tanakh, locate Psalm 19, normalise to consonant skeleton
       (22 letters; finals folded; niqqud + te'amim stripped).
    2. Build narrative-Hebrew peer pool (Genesis/Exodus/Joshua/Judges/
       Samuel/Kings); length-match Psalm 19 ± 30 %.
    3. Sample n single-letter substitution variants from EACH peer chapter
       to build per-compressor Delta distributions; tau_c = 5th percentile.
    4. Bootstrap tau stability check (200 resamples; CV <= 0.30 per tau).
    5. Enumerate ALL single-letter substitutions on Psalm 19; for each
       variant compute per-compressor Delta vs unperturbed Psalm 19.
       Variant fires under K=2 iff at least 2 of 4 compressors have
       Delta_c >= tau_c.
    6. Compute FPR on peer-vs-peer length-matched pairs.
    7. Apply verdict ladder (8 branches; first match wins).

NO Arabic tau is transferred. NO post-hoc K change. NO chapter re-roll.
"""
from __future__ import annotations

import bz2
import gzip
import hashlib
import io
import json
import lzma
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

try:
    import zstandard as zstd
    _ZSTD_AVAILABLE = True
except ImportError:
    _ZSTD_AVAILABLE = False

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import safe_output_dir  # noqa: E402

EXP = "exp104_F53_tanakh_pilot"

# --- PREREG-hash sentinel (audit hook) ---------------------------------
_PREREG_EXPECTED_HASH = (
    "30694bfbcfd07f2076f2719e990fff732fd03cd90eed303f898856d27a58c5b9"
)

# --- Frozen constants (mirror PREREG.md §3) ----------------------------
SEED = 42
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9
CONSENSUS_K = 2
TAU_PERCENTILE = 5  # 5th percentile of peer Delta distribution
LENGTH_MATCH_FRAC = 0.30  # ± 30 %
TARGET_BOOK = "תהלים"  # Psalms (WLC spelling, no yod)
TARGET_CHAPTER = "יט"  # Psalm 19 (yod-tet = 10+9 = 19)
PSALM_19_MIN_LETTERS = 1000
PSALM_19_MIN_VERSES = 10
# WLC Hebrew Bible book names (verified by scripts/_diag_wlc2.py against
# tanakh_wlc.txt; WLC uses regular spaces in compound names, not hyphens)
PEER_BOOKS = (
    "בראשית", "שמות",        # Genesis, Exodus
    "יהושע", "שופטים",        # Joshua, Judges
    "שמואל א", "שמואל ב",   # 1 Sam, 2 Sam
    "מלכים א", "מלכים ב",   # 1 Kgs, 2 Kgs
)
TARGET_N_PEERS = 200
PEER_AUDIT_FLOOR = 100
N_CALIB_VARIANTS_PER_PEER = 30
BOOTSTRAP_N = 200
BOOTSTRAP_CV_CEIL = 0.30
RECALL_FLOOR = 0.999
FPR_CEIL = 0.05
PARTIAL_RECALL_FLOOR = 0.99
N_FPR_PAIRS = 500

# Hebrew consonant inventory (22 letters)
HEBREW_CONS_22 = "אבגדהוזחטיכלמנסעפצקרשת"
HEBREW_FINALS_FOLD = {
    "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ",
}
# Niqqud (vowel points) + te'amim (cantillation marks) to strip
HEBREW_DIACRITIC_RE = re.compile(
    r"[\u0591-\u05AF\u05B0-\u05BC\u05BD\u05BF\u05C0\u05C1\u05C2"
    r"\u05C3\u05C4\u05C5\u05C6\u05C7]"
)

# zstd compressor (re-used; shared across calls is safe)
_ZSTD_CCTX = zstd.ZstdCompressor(level=ZSTD_LEVEL) if _ZSTD_AVAILABLE else None


# --- Compression primitives (byte-equal to exp95c except level locks) ---
def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def _bz2_len(s: str) -> int:
    return len(bz2.compress(s.encode("utf-8"), compresslevel=BZ2_LEVEL))


def _lzma_len(s: str) -> int:
    return len(lzma.compress(s.encode("utf-8"), preset=LZMA_PRESET))


def _zstd_len(s: str) -> int:
    if _ZSTD_CCTX is None:
        raise RuntimeError("zstd not available")
    return len(_ZSTD_CCTX.compress(s.encode("utf-8")))


def _make_ncd(compress_len_fn):
    def ncd(a: str, b: str) -> float:
        if not a and not b:
            return 0.0
        za, zb = compress_len_fn(a), compress_len_fn(b)
        zab = compress_len_fn(a + b)
        denom = max(1, max(za, zb))
        return (zab - min(za, zb)) / denom
    return ncd


_NCD_FNS = {
    "gzip": _make_ncd(_gz_len),
    "bz2":  _make_ncd(_bz2_len),
    "lzma": _make_ncd(_lzma_len),
    "zstd": _make_ncd(_zstd_len),
}
_COMPRESSOR_NAMES = ("gzip", "bz2", "lzma", "zstd")


# --- Hebrew normalisation (rasm-equivalent: 22 consonants, finals folded) ---
def _hebrew_skeleton(text: str) -> str:
    """Strip niqqud + te'amim + non-Hebrew chars; fold finals to base form.

    Returns: pure 22-Hebrew-consonant string (no spaces, no punctuation).
    """
    # Strip niqqud + te'amim
    s = HEBREW_DIACRITIC_RE.sub("", text)
    # Collect only consonants, folding finals
    out: list[str] = []
    for c in s:
        if c in HEBREW_FINALS_FOLD:
            out.append(HEBREW_FINALS_FOLD[c])
        elif c in HEBREW_CONS_22:
            out.append(c)
        # everything else (spaces, punctuation, non-Hebrew) is dropped
    return "".join(out)


def _hebrew_skeleton_with_spaces(verses: list[str]) -> str:
    """Per-verse skeleton joined with single spaces (preserves verse boundaries)."""
    return " ".join(_hebrew_skeleton(v) for v in verses)


# --- Corpus loader -----------------------------------------------------
# Local Tanakh loader with explicit book whitelist. The shared
# src/raw_loader.py heuristic ("any single-Hebrew-word line is a book
# title") is too permissive and mis-attributes 90 % of Psalms to
# verse-internal single-word lines. We use the 24-book WLC whitelist below.
# WLC book titles (verified by diagnostic against tanakh_wlc.txt;
# WLC uses regular spaces in compound names, not hyphens; some books use
# shortened spellings without final yod/waw)
_WLC_BOOKS = {
    # Torah
    "בראשית", "שמות", "ויקרא", "במדבר", "דברים",
    # Former Prophets (note: שמואל א/ב + מלכים א/ב use ASCII space)
    "יהושע", "שופטים", "שמואל א", "שמואל ב", "מלכים א", "מלכים ב",
    # Latter Prophets (major) — ישעיה / ירמיה without final yod
    "ישעיה", "ירמיה", "יחזקאל",
    # Latter Prophets (Twelve)
    "הושע", "יואל", "עמוס", "עובדיה", "יונה", "מיכה",
    "נחום", "חבקוק", "צפניה", "חגי", "זכריה", "מלאכי",
    # Writings
    "תהלים", "משלי", "איוב",
    "שיר השירים", "רות", "איכה", "קהלת", "אסתר",
    "דניאל", "עזרא", "נחמיה",
    # 1 Chronicles in WLC has no explicit ב/א suffix on first occurrence
    "דברי הימים", "דברי הימים ב",
}
_HEBREW_CHAPTER_HEADER = re.compile(r"^פרק\s+([א-ת״]+)\s*$")


def _load_tanakh_chapters() -> list[dict]:
    """Stricter local loader for the WLC Tanakh.

    Returns: list of dicts {book, chapter, n_verses, verses_raw,
    letters_22, n_letters}, one per chapter, in canonical order.
    """
    path = _ROOT / "data" / "corpora" / "he" / "tanakh_wlc.txt"
    if not path.exists():
        raise FileNotFoundError(f"WLC corpus missing: {path}")
    raw = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    lines = [ln.rstrip("\r") for ln in raw.split("\n")]

    out: list[dict] = []
    cur_book: str | None = None
    cur_chap: str | None = None
    cur_verses: list[str] = []

    def flush() -> None:
        nonlocal cur_verses, cur_book, cur_chap
        if cur_book and cur_chap and cur_verses:
            skel = _hebrew_skeleton(" ".join(cur_verses))
            out.append({
                "book": cur_book,
                "chapter": cur_chap,
                "n_verses": len(cur_verses),
                "verses_raw": list(cur_verses),
                "letters_22": skel,
                "n_letters": len(skel),
            })
        cur_verses = []

    for raw_ln in lines:
        ln = raw_ln.strip()
        if not ln:
            continue
        # 1. Strict book-title check: must EXACTLY match the whitelist
        if ln in _WLC_BOOKS:
            flush()
            cur_book = ln
            cur_chap = None
            continue
        # 2. Chapter header: "פרק <hebrew-letter-numeral>"
        m_chap = _HEBREW_CHAPTER_HEADER.match(ln)
        if m_chap:
            flush()
            cur_chap = m_chap.group(1)
            continue
        # 3. Otherwise it's a verse line (or junk before first book; ignored)
        if cur_book and cur_chap:
            cur_verses.append(ln)

    flush()
    return out


# --- Variant enumeration (single Hebrew consonant substitution) ---------
def _enumerate_variants(skeleton: str) -> list[tuple[int, str, str]]:
    """Return list of (position, original_char, replacement_char).

    Every position in skeleton × every other-of-22 substitute. Total =
    n_letters × 21.
    """
    out: list[tuple[int, str, str]] = []
    cons = list(HEBREW_CONS_22)
    for pos, ch in enumerate(skeleton):
        if ch not in HEBREW_CONS_22:
            continue
        for repl in cons:
            if repl == ch:
                continue
            out.append((pos, ch, repl))
    return out


def _apply_variant(skeleton: str, pos: int, repl: str) -> str:
    return skeleton[:pos] + repl + skeleton[pos + 1:]


def _per_compressor_deltas(canon: str, variant: str) -> dict[str, float]:
    """For each compressor, return Delta = NCD(canon, variant) - NCD(canon, canon).

    NCD(canon, canon) is symmetric-zero-ish (depends on compressor framing
    overhead). Computed per-compressor.
    """
    out: dict[str, float] = {}
    for name in _COMPRESSOR_NAMES:
        fn = _NCD_FNS[name]
        ncd_self = fn(canon, canon)
        ncd_var = fn(canon, variant)
        out[name] = ncd_var - ncd_self
    return out


# --- PREREG hash + sentinel --------------------------------------------
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
            f"  actual  : {actual}\n"
            f"PREREG.md was modified after run.py was locked. "
            f"This run is invalidated per integrity protocol."
        )
    return actual


# --- Verdict ladder ----------------------------------------------------
def _decide_verdict(
    psalm_19: dict | None,
    n_peers: int,
    tau_cv: dict[str, float] | None,
    recall_k2: float | None,
    fpr_k2: float | None,
) -> tuple[str, str]:
    """Apply pre-registered verdict ladder; return (verdict, branch_msg)."""
    # Branch 1: corpus missing or chapter not found
    if psalm_19 is None:
        return ("BLOCKED_corpus_missing",
                "Hebrew Tanakh corpus or Psalm 19 chapter not found.")
    # Branch 2: Psalm 19 too short
    if (psalm_19["n_letters"] < PSALM_19_MIN_LETTERS or
            psalm_19["n_verses"] < PSALM_19_MIN_VERSES):
        return ("BLOCKED_psalm_19_too_short",
                f"Psalm 19 has {psalm_19['n_letters']} letters / "
                f"{psalm_19['n_verses']} verses (need >= "
                f"{PSALM_19_MIN_LETTERS} / {PSALM_19_MIN_VERSES}).")
    # Branch 3: peer pool too small
    if n_peers < PEER_AUDIT_FLOOR:
        return ("FAIL_audit_peer_pool_size",
                f"Peer pool has {n_peers} chapters after length-matching "
                f"(need >= {PEER_AUDIT_FLOOR}).")
    # Branch 4: tau unstable
    if tau_cv is not None:
        worst_cv = max(tau_cv.values())
        if worst_cv > BOOTSTRAP_CV_CEIL:
            return ("FAIL_audit_tau_unstable",
                    f"Bootstrap CV of tau (worst across compressors) = "
                    f"{worst_cv:.3f} > {BOOTSTRAP_CV_CEIL}.")
    # Branch 5: recall below floor
    if recall_k2 is None:
        return ("BLOCKED_no_psalm_scoring", "Psalm 19 scoring did not complete.")
    if recall_k2 < RECALL_FLOOR:
        # Branch 7 partial check before full FAIL
        if (recall_k2 >= PARTIAL_RECALL_FLOOR and
                fpr_k2 is not None and fpr_k2 <= FPR_CEIL):
            return ("PARTIAL_recall_above_99",
                    f"Recall = {recall_k2:.4f} (in [{PARTIAL_RECALL_FLOOR}, "
                    f"{RECALL_FLOOR})) AND FPR = {fpr_k2:.4f} <= {FPR_CEIL}. "
                    f"Partial closure; NOT paper-grade.")
        return ("FAIL_recall_below_floor",
                f"K=2 recall = {recall_k2:.4f} < {RECALL_FLOOR}.")
    # Branch 6: FPR above ceiling
    if fpr_k2 is None:
        return ("BLOCKED_no_fpr_scoring", "FPR scoring did not complete.")
    if fpr_k2 > FPR_CEIL:
        return ("FAIL_fpr_above_ceiling",
                f"K=2 FPR = {fpr_k2:.4f} > {FPR_CEIL}.")
    # Branch 8: PASS
    return ("PASS_consensus_100",
            f"recall = {recall_k2:.4f} >= {RECALL_FLOOR} AND "
            f"FPR = {fpr_k2:.4f} <= {FPR_CEIL}. F53 rule generalises to "
            f"Hebrew Psalm 19 at full pilot-grade.")


# --- Driver ------------------------------------------------------------
def main() -> int:
    print(f"# {EXP} -- starting")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()

    # Step 0: enforce PREREG hash
    actual_hash = _enforce_prereg_hash()
    print(f"# PREREG hash OK: {actual_hash[:16]}...")

    # Audit + sentinels collector
    audit: dict = {
        "ok": True,
        "checks": {},
        "warnings": [],
        "errors": [],
    }

    # Step 1: load Tanakh + locate Psalm 19
    print("# Step 1: loading Hebrew Tanakh ...")
    try:
        chapters = _load_tanakh_chapters()
    except Exception as e:
        audit["ok"] = False
        audit["errors"].append(f"corpus_load_failed: {type(e).__name__}: {e}")
        verdict, msg = _decide_verdict(None, 0, None, None, None)
        return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash, {})

    audit["checks"]["n_chapters_total"] = len(chapters)

    # Locate Psalm 19
    psalm_19_match = [c for c in chapters
                      if c["book"] == TARGET_BOOK and c["chapter"] == TARGET_CHAPTER]
    if not psalm_19_match:
        audit["ok"] = False
        audit["errors"].append(
            f"psalm_19_not_found (book={TARGET_BOOK!r} chapter={TARGET_CHAPTER!r})"
        )
        # Show top books for diagnostics
        from collections import Counter
        books_seen = Counter(c["book"] for c in chapters)
        audit["checks"]["books_seen_top10"] = dict(books_seen.most_common(10))
        verdict, msg = _decide_verdict(None, 0, None, None, None)
        return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash, {})

    psalm_19 = psalm_19_match[0]
    print(f"# Psalm 19 located: {psalm_19['n_verses']} verses, "
          f"{psalm_19['n_letters']} consonant-skeleton letters.")
    audit["checks"]["psalm_19_n_verses"] = psalm_19["n_verses"]
    audit["checks"]["psalm_19_n_letters"] = psalm_19["n_letters"]

    # Branch 2 early gate
    if (psalm_19["n_letters"] < PSALM_19_MIN_LETTERS or
            psalm_19["n_verses"] < PSALM_19_MIN_VERSES):
        verdict, msg = _decide_verdict(psalm_19, 0, None, None, None)
        return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash,
                              {"psalm_19": _meta(psalm_19)})

    # Step 2: build peer pool (length-matched ± 30 %)
    print("# Step 2: building Hebrew narrative peer pool ...")
    target_len = psalm_19["n_letters"]
    lo = int(target_len * (1 - LENGTH_MATCH_FRAC))
    hi = int(target_len * (1 + LENGTH_MATCH_FRAC))
    peers_raw = [c for c in chapters
                 if c["book"] in PEER_BOOKS
                 and lo <= c["n_letters"] <= hi]
    rng = random.Random(SEED)
    rng.shuffle(peers_raw)
    peers = peers_raw[:TARGET_N_PEERS]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} chapters in [{lo}, {hi}] letters from "
          f"{PEER_BOOKS}.")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_length_range"] = [lo, hi]

    # Branch 3 early gate
    if n_peers < PEER_AUDIT_FLOOR:
        verdict, msg = _decide_verdict(psalm_19, n_peers, None, None, None)
        return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash,
                              {"psalm_19": _meta(psalm_19), "peers_n": n_peers})

    # Step 3: per-peer Delta distributions (sampled n=30 variants per peer)
    print(f"# Step 3: calibrating tau per compressor "
          f"({n_peers} peers x {N_CALIB_VARIANTS_PER_PEER} sampled variants) ...")
    calib_deltas: dict[str, list[float]] = {n: [] for n in _COMPRESSOR_NAMES}
    for i, peer in enumerate(peers):
        skel = peer["letters_22"]
        all_vars = _enumerate_variants(skel)
        if len(all_vars) <= N_CALIB_VARIANTS_PER_PEER:
            sampled = all_vars
        else:
            local_rng = random.Random(SEED + i)
            sampled = local_rng.sample(all_vars, N_CALIB_VARIANTS_PER_PEER)
        for (pos, _orig, repl) in sampled:
            variant = _apply_variant(skel, pos, repl)
            deltas = _per_compressor_deltas(skel, variant)
            for name, d in deltas.items():
                calib_deltas[name].append(d)
        if (i + 1) % 25 == 0:
            print(f"#   {i+1}/{n_peers} peers processed "
                  f"(elapsed: {time.time() - t_start:.1f} s)")

    # Compute per-compressor tau (5th percentile)
    tau: dict[str, float] = {}
    for name in _COMPRESSOR_NAMES:
        arr = np.asarray(calib_deltas[name], dtype=float)
        if len(arr) == 0:
            tau[name] = float("nan")
            audit["warnings"].append(f"empty_calib_deltas:{name}")
        else:
            tau[name] = float(np.percentile(arr, TAU_PERCENTILE))
    print(f"# Locked Hebrew tau per compressor (5th-pctile of peer-Delta):")
    for name, t in tau.items():
        print(f"#   tau_{name:5s} = {t:.6f}  (n_calib_samples = {len(calib_deltas[name])})")

    # Step 4: bootstrap tau stability check
    print(f"# Step 4: bootstrap-{BOOTSTRAP_N} tau stability check ...")
    tau_cv: dict[str, float] = {}
    boot_rng = np.random.default_rng(SEED)
    for name in _COMPRESSOR_NAMES:
        arr = np.asarray(calib_deltas[name], dtype=float)
        if len(arr) < 2:
            tau_cv[name] = float("nan")
            continue
        boot_taus = []
        for _ in range(BOOTSTRAP_N):
            idx = boot_rng.integers(0, len(arr), len(arr))
            boot_taus.append(np.percentile(arr[idx], TAU_PERCENTILE))
        boot_taus = np.asarray(boot_taus, dtype=float)
        mean = float(np.mean(boot_taus))
        std = float(np.std(boot_taus, ddof=1))
        cv = std / abs(mean) if abs(mean) > 1e-12 else float("inf")
        tau_cv[name] = cv
    print(f"# Bootstrap CV per tau:")
    for name, cv in tau_cv.items():
        flag = " <-- exceeds ceiling" if cv > BOOTSTRAP_CV_CEIL else ""
        print(f"#   CV(tau_{name:5s}) = {cv:.4f}{flag}")

    audit["checks"]["tau_locked"] = tau
    audit["checks"]["tau_bootstrap_cv"] = tau_cv

    # Branch 4 early gate
    worst_cv = max(c for c in tau_cv.values() if not np.isnan(c)) if tau_cv else 0.0
    if worst_cv > BOOTSTRAP_CV_CEIL:
        verdict, msg = _decide_verdict(psalm_19, n_peers, tau_cv, None, None)
        return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash,
                              {"psalm_19": _meta(psalm_19), "peers_n": n_peers,
                               "tau": tau, "tau_bootstrap_cv": tau_cv})

    # Step 5: enumerate ALL Psalm 19 variants and score
    psalm_skel = psalm_19["letters_22"]
    psalm_variants = _enumerate_variants(psalm_skel)
    n_psalm_var = len(psalm_variants)
    print(f"# Step 5: enumerating {n_psalm_var} single-letter variants on Psalm 19 ...")
    fires_at_k = {1: 0, 2: 0, 3: 0, 4: 0}
    n_processed = 0
    for (pos, _orig, repl) in psalm_variants:
        variant = _apply_variant(psalm_skel, pos, repl)
        deltas = _per_compressor_deltas(psalm_skel, variant)
        n_above = sum(1 for name in _COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        for k in (1, 2, 3, 4):
            if n_above >= k:
                fires_at_k[k] += 1
        n_processed += 1
        if n_processed % 5000 == 0:
            elapsed = time.time() - t_start
            eta = elapsed * (n_psalm_var - n_processed) / max(1, n_processed)
            print(f"#   {n_processed}/{n_psalm_var} ({100.0*n_processed/n_psalm_var:.1f}%) "
                  f"elapsed: {elapsed:.0f}s, ETA: {eta:.0f}s")

    recalls = {f"K={k}": fires_at_k[k] / n_psalm_var for k in (1, 2, 3, 4)}
    recall_k2 = recalls["K=2"]
    print(f"# Psalm 19 recalls: {recalls}")
    audit["checks"]["psalm_19_recalls"] = recalls
    audit["checks"]["psalm_19_n_variants"] = n_psalm_var

    # Step 6: FPR on peer-vs-peer pairs
    print(f"# Step 6: FPR on {N_FPR_PAIRS} length-matched peer-vs-peer pairs ...")
    pair_rng = random.Random(SEED + 1000)
    fpr_fires = 0
    n_fpr_eval = 0
    for _ in range(N_FPR_PAIRS):
        # Pick two distinct length-matched peers
        a, b = pair_rng.sample(peers, 2)
        sa = a["letters_22"]
        sb = b["letters_22"]
        if not sa or not sb:
            continue
        deltas = _per_compressor_deltas(sa, sb)
        n_above = sum(1 for name in _COMPRESSOR_NAMES
                      if deltas[name] >= tau[name])
        if n_above >= CONSENSUS_K:
            fpr_fires += 1
        n_fpr_eval += 1
    fpr_k2 = fpr_fires / n_fpr_eval if n_fpr_eval > 0 else float("nan")
    print(f"# K=2 FPR = {fpr_fires}/{n_fpr_eval} = {fpr_k2:.4f}")
    audit["checks"]["fpr_k2"] = fpr_k2
    audit["checks"]["fpr_n_pairs_evaluated"] = n_fpr_eval

    # Step 7: verdict
    verdict, msg = _decide_verdict(psalm_19, n_peers, tau_cv, recall_k2, fpr_k2)
    print(f"# VERDICT: {verdict}")
    print(f"# Reason: {msg}")

    receipt_extras = {
        "psalm_19": _meta(psalm_19),
        "peers_n": n_peers,
        "peer_length_range": [lo, hi],
        "tau": tau,
        "tau_bootstrap_cv": tau_cv,
        "psalm_19_recalls": recalls,
        "psalm_19_n_variants": n_psalm_var,
        "fpr_k2": fpr_k2,
        "fpr_n_pairs": n_fpr_eval,
    }
    return _write_receipt(verdict, msg, audit, t_start, started_at_utc, actual_hash, receipt_extras)


def _meta(chap: dict) -> dict:
    """Strip raw-verse content from chapter dict for the receipt (size/clarity)."""
    return {k: v for k, v in chap.items() if k != "verses_raw"}


def _write_receipt(
    verdict: str,
    msg: str,
    audit: dict,
    t_start: float,
    started_at_utc: str,
    prereg_hash_actual: str,
    extras: dict,
) -> int:
    out_dir = safe_output_dir(EXP)
    receipt_path = out_dir / f"{EXP}.json"
    elapsed = time.time() - t_start
    completed_at_utc = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": EXP,
        "hypothesis_id": "H59",
        "hypothesis": (
            "F53 multi-compressor consensus K=2 with Hebrew-side tau "
            "calibration closes single-letter forgery on Psalm 19 at "
            "recall >= 0.999 / FPR <= 0.05."
        ),
        "verdict": verdict,
        "verdict_reason": msg,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": elapsed,
        "prereg_hash": prereg_hash_actual,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp104_F53_tanakh_pilot/PREREG.md",
        "frozen_constants": {
            "SEED": SEED,
            "consensus_K": CONSENSUS_K,
            "tau_percentile": TAU_PERCENTILE,
            "length_match_frac": LENGTH_MATCH_FRAC,
            "compressors": list(_COMPRESSOR_NAMES),
            "compressor_levels": {
                "gzip": GZIP_LEVEL, "bz2": BZ2_LEVEL,
                "lzma": LZMA_PRESET, "zstd": ZSTD_LEVEL,
            },
            "target_book": TARGET_BOOK,
            "target_chapter": TARGET_CHAPTER,
            "psalm_19_min_letters": PSALM_19_MIN_LETTERS,
            "psalm_19_min_verses": PSALM_19_MIN_VERSES,
            "peer_books": list(PEER_BOOKS),
            "target_n_peers": TARGET_N_PEERS,
            "peer_audit_floor": PEER_AUDIT_FLOOR,
            "n_calib_variants_per_peer": N_CALIB_VARIANTS_PER_PEER,
            "bootstrap_n": BOOTSTRAP_N,
            "bootstrap_cv_ceil": BOOTSTRAP_CV_CEIL,
            "recall_floor": RECALL_FLOOR,
            "fpr_ceil": FPR_CEIL,
            "n_fpr_pairs": N_FPR_PAIRS,
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


if __name__ == "__main__":
    sys.exit(main())
