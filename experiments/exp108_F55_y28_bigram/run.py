"""exp108_F55_y28_bigram/run.py
==================================
H63: F55 universal symbolic forgery detector (analytic-bound bigram-shift,
frozen tau = 2.0, no calibration) generalises off-shelf to Avestan
Yasna 28 (Ahunavaiti Gatha, ch. 1; Old Avestan, oldest canonical
Zoroastrian layer, ~5th c BCE composition / ~6th c CE editorial close).

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol: byte-for-byte compatible with exp95j (Quran V1), exp105
(Hebrew Psalm 78), exp106 (Greek NT Mark 1), and exp107 (Pali DN 1)
at the detector level. Deltas:
  - Avestan normaliser (NEW): HTML-entity decode + tag strip + NFD
    decompose + Mn-strip + casefold + 26-letter Latin whitelist.
  - Avestan loader (NEW): parse Avesta.org Geldner-edition y*.htm
    files; <H3...>...</H3> chapter markers (3 observed formats);
    <DD>...</DD> verse blocks; concatenate verses per chapter.
  - Yasna 28 target (Ahunavaiti Gatha, ch. 1).
  - F55-family peer pool floor amendment to 50 (PREREG §2.1).
  - NO length matching.

Predicted wall-time < 5 s for ~41K variants on the 1.6K-letter Yasna 28
skeleton.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import random
import re
import sys
import time
import unicodedata
from collections import Counter
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

EXP = "exp108_F55_y28_bigram"

# ---- Live progress log -------------------------------------------------
_PROGRESS_LOG = _ROOT / "results" / "experiments" / EXP / "progress.log"
_PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
_progress_fh = open(_PROGRESS_LOG, "w", encoding="utf-8", buffering=1)


def _log(msg: str) -> None:
    print(msg, flush=True)
    _progress_fh.write(msg + "\n")
    _progress_fh.flush()


# ---- PREREG hash sentinel ----------------------------------------------
_PREREG_EXPECTED_HASH = (
    "585acd8d8bdd6302e6536911981e8126b3f824ef185ac8c43a48ee8c736eb62b"
)


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
            f"PREREG.md was modified after run.py was locked."
        )
    return actual


# ---- Frozen constants (PREREG §2) --------------------------------------
TARGET_YASNA = 28
TARGET_MIN_LETTERS = 1000
TARGET_MIN_VERSES = 10
ALPHABET_COVERAGE_FLOOR = 18
N_YASNAS_EXPECTED = 73  # A7: 0..72 inclusive
TAU_HIGH = 2.0
AUDIT_TOL = 1e-9
RECALL_FLOOR = 1.000
FPR_CEIL = 0.000
PARTIAL_FPR_BAND_HI = 0.05
PEER_AUDIT_FLOOR_F55 = 50  # F55-family amendment, see PREREG §2.1
SEED = 42

AVESTAN_ALPHABET_26 = "abcdefghijklmnopqrstuvwxyz"
AVESTAN_ALPHABET_SET = set(AVESTAN_ALPHABET_26)
N_SUBSTITUTIONS_PER_POS = len(AVESTAN_ALPHABET_26) - 1  # 25

_NORMALISER_SENTINEL_INPUT = (
    "ahy&acirc; &yacute;&acirc;s&acirc; nemangh&acirc;"
)
_NORMALISER_SENTINEL_EXPECTED = "ahyayasanemangha"


# ---- Avestan corpus loader ---------------------------------------------

_AVESTAN_ROOT = _ROOT / "data" / "corpora" / "ae"

_AVESTAN_FILES = [
    "y0to8.htm", "y9to11.htm", "y12.htm", "y13to27.htm",
    "y28to34.htm", "y35to42.htm", "y43to46.htm", "y47to50.htm",
    "y51.htm", "y52.htm", "y53.htm", "y54to72.htm",
]

# H3 chapter-heading extractor; tolerates attributes (e.g., <H3 id="y54">).
_H3_RE = re.compile(r"<H3\b[^>]*>([\s\S]*?)</H3>", re.IGNORECASE)
_CHAP_NUM_RE = re.compile(r"(\d+)")
# DD verse-content extractor; lazy match until next DT, DD, DL close, or H3.
_DD_RE = re.compile(
    r"<DD>(.*?)(?=<DT>|</DL>|<H3|$)",
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html_tags(s: str) -> str:
    return _TAG_RE.sub(" ", s)


def _normalise_avestan(s: str) -> str:
    """Avestan transliteration -> 26-letter Latin skeleton.

    Pipeline (locked at PREREG §2):
      1. HTML entity decode (&acirc; -> â etc).
      2. Strip HTML tags.
      3. NFD decompose; drop combining marks (Mn category).
      4. casefold().
      5. Whitelist a-z; drop everything else.
    """
    if not s:
        return ""
    s = html.unescape(s)
    s = _strip_html_tags(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.casefold()
    return "".join(ch for ch in s if ch in AVESTAN_ALPHABET_SET)


def _parse_avestan_file(path: Path) -> list[dict]:
    raw = path.read_text(encoding="latin-1", errors="replace")
    h3_matches = list(_H3_RE.finditer(raw))
    matches: list[tuple[int, int, int]] = []
    for i, m in enumerate(h3_matches):
        body = m.group(1)
        nm = _CHAP_NUM_RE.search(body)
        if nm is None:
            continue
        yasna_n = int(nm.group(1))
        content_start = m.end()
        content_end = (h3_matches[i + 1].start()
                       if i + 1 < len(h3_matches) else len(raw))
        matches.append((yasna_n, content_start, content_end))
    out: list[dict] = []
    for (yasna_n, start, end) in matches:
        chunk = raw[start:end]
        dd_blocks = _DD_RE.findall(chunk)
        verses_text: list[str] = []
        for dd in dd_blocks:
            text = _strip_html_tags(html.unescape(dd)).strip()
            if not text:
                continue
            verses_text.append(text)
        text_raw = " ".join(verses_text)
        letters_26 = _normalise_avestan(text_raw)
        out.append({
            "yasna": yasna_n,
            "n_verses": len(verses_text),
            "text_raw": text_raw,
            "letters_26": letters_26,
            "n_letters": len(letters_26),
            "source_file": path.name,
        })
    return out


def _load_avestan_yasnas() -> list[dict]:
    out: list[dict] = []
    for fname in _AVESTAN_FILES:
        p = _AVESTAN_ROOT / fname
        if not p.is_file():
            _log(f"# WARN: {fname} missing")
            continue
        out.extend(_parse_avestan_file(p))
    seen: set[int] = set()
    uniq: list[dict] = []
    for c in sorted(out, key=lambda r: r["yasna"]):
        if c["yasna"] in seen:
            _log(f"# WARN: duplicate Yasna {c['yasna']} (kept first)")
            continue
        seen.add(c["yasna"])
        uniq.append(c)
    return uniq


# ---- Bigram primitives -------------------------------------------------

def bigrams_of(s: str) -> Counter:
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    n = len(canon)
    old_ch = canon[p]
    diff: dict[str, int] = {}
    if p > 0:
        b_old_l = canon[p - 1] + old_ch
        b_new_l = canon[p - 1] + new_ch
        diff[b_old_l] = diff.get(b_old_l, 0) - 1
        diff[b_new_l] = diff.get(b_new_l, 0) + 1
    if p < n - 1:
        b_old_r = old_ch + canon[p + 1]
        b_new_r = new_ch + canon[p + 1]
        diff[b_old_r] = diff.get(b_old_r, 0) - 1
        diff[b_new_r] = diff.get(b_new_r, 0) + 1
    return 0.5 * sum(abs(v) for v in diff.values())


# ---- Verdict ladder (PREREG §4) ----------------------------------------

def _decide_verdict(
    target_meta: dict | None,
    n_yasnas_total: int,
    n_peers: int,
    normaliser_ok: bool,
    alphabet_coverage_ok: bool,
    max_var_delta: float | None,
    variant_recall: float | None,
    peer_fpr: float | None,
) -> tuple[str, str]:
    if target_meta is None:
        return ("BLOCKED_corpus_missing",
                "Avestan corpus or Yasna 28 not found.")
    if n_yasnas_total != N_YASNAS_EXPECTED:
        return ("BLOCKED_corpus_incomplete",
                f"Loaded {n_yasnas_total} yasnas; expected "
                f"{N_YASNAS_EXPECTED} (A7 violation).")
    if (target_meta["n_letters"] < TARGET_MIN_LETTERS
            or target_meta["n_verses"] < TARGET_MIN_VERSES):
        return ("BLOCKED_yasna_28_too_short",
                f"Yasna 28 has {target_meta['n_letters']} letters / "
                f"{target_meta['n_verses']} verses (need >= "
                f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES}).")
    if n_peers < PEER_AUDIT_FLOOR_F55:
        return ("FAIL_audit_peer_pool_size",
                f"Peer pool {n_peers} < F55-family floor "
                f"{PEER_AUDIT_FLOOR_F55}.")
    if not normaliser_ok:
        return ("FAIL_audit_normaliser_sentinel",
                "Avestan normaliser sentinel does not match locked value.")
    if not alphabet_coverage_ok:
        return ("FAIL_audit_alphabet_coverage",
                f"Yasna 28 uses fewer than {ALPHABET_COVERAGE_FLOOR} "
                f"of 26 alphabet letters; pathological input.")
    if max_var_delta is not None and max_var_delta > TAU_HIGH + AUDIT_TOL:
        return ("FAIL_audit_theorem",
                f"max(variant_delta) = {max_var_delta:.6f} > "
                f"{TAU_HIGH} + {AUDIT_TOL} (theorem violation).")
    if variant_recall is None:
        return ("BLOCKED_no_variant_scoring",
                "Variant scoring did not complete.")
    if variant_recall < RECALL_FLOOR:
        return ("FAIL_recall_below_floor",
                f"variant recall = {variant_recall:.6f} < "
                f"{RECALL_FLOOR}.")
    if peer_fpr is None:
        return ("BLOCKED_no_fpr_scoring",
                "Peer FPR scoring did not complete.")
    if peer_fpr > FPR_CEIL:
        if peer_fpr <= PARTIAL_FPR_BAND_HI:
            return ("PARTIAL_fpr_below_band",
                    f"variant recall = {variant_recall:.6f} but "
                    f"peer FPR = {peer_fpr:.6f} > {FPR_CEIL} "
                    f"(within partial band {PARTIAL_FPR_BAND_HI}).")
        return ("FAIL_fpr_above_ceiling",
                f"peer FPR = {peer_fpr:.6f} > {FPR_CEIL}.")
    return ("PASS_universal_perfect_recall_zero_fpr",
            f"variant recall = {variant_recall:.6f} >= {RECALL_FLOOR} AND "
            f"peer FPR = {peer_fpr:.6f} <= {FPR_CEIL}. F55 detector "
            f"generalises off-shelf to Avestan Yasna 28.")


# ---- Receipt writer ----------------------------------------------------

def _write_receipt(
    verdict: str,
    verdict_reason: str,
    audit: dict,
    t_start: float,
    started_at_utc: str,
    actual_hash: str,
    extra: dict,
) -> int:
    completed_at = datetime.now(timezone.utc).isoformat()
    out_dir = _ROOT / "results" / "experiments" / EXP
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": EXP,
        "hypothesis_id": "H63",
        "hypothesis": (
            "F55 analytic-bound bigram-shift detector (frozen tau = 2.0, "
            "no calibration) generalises off-shelf to Avestan Yasna 28 "
            "(Ahunavaiti Gatha, ch. 1) with per-variant recall = 1.000 "
            "and per-(canon, peer)-pair FPR = 0.000 against the full "
            "72-yasna peer pool of all other Yasna chapters."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at,
        "wall_time_s": time.time() - t_start,
        "prereg_hash": actual_hash,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp108_F55_y28_bigram/PREREG.md",
        "amendment_chain": [
            "exp95j_bigram_shift_universal "
            "(F55 PASS_universal_perfect_recall_zero_fpr on Quran V1)",
            "exp105_F55_psalm78_bigram "
            "(F59 PASS on Hebrew Psalm 78)",
            "exp106_F55_mark1_bigram "
            "(F60 PASS on Greek NT Mark 1)",
            "exp107_F55_dn1_bigram "
            "(F61 PASS on Pali Digha Nikaya 1)",
            "exp108_F55_y28_bigram (this run; F55 -> Avestan Yasna 28)",
        ],
        "frozen_constants": {
            "SEED": SEED,
            "TAU_HIGH": TAU_HIGH,
            "AUDIT_TOL": AUDIT_TOL,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEIL": FPR_CEIL,
            "PARTIAL_FPR_BAND_HI": PARTIAL_FPR_BAND_HI,
            "TARGET_YASNA": TARGET_YASNA,
            "TARGET_MIN_LETTERS": TARGET_MIN_LETTERS,
            "TARGET_MIN_VERSES": TARGET_MIN_VERSES,
            "ALPHABET_COVERAGE_FLOOR": ALPHABET_COVERAGE_FLOOR,
            "N_YASNAS_EXPECTED": N_YASNAS_EXPECTED,
            "PEER_AUDIT_FLOOR_F55": PEER_AUDIT_FLOOR_F55,
            "PEER_POOL_STRATEGY":
                "all_other_yasna_chapters_no_length_matching",
            "AVESTAN_ALPHABET_26": AVESTAN_ALPHABET_26,
            "N_SUBSTITUTIONS_PER_POS": N_SUBSTITUTIONS_PER_POS,
            "calibration_source":
                "frozen_analytic_theorem_no_data_calibration",
        },
        "audit_report": audit,
        "pre_stage_diagnostic_receipt":
            "results/auxiliary/_y28_bigram_sizing.json",
    }
    receipt.update(extra)
    out_path = out_dir / f"{EXP}.json"
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    _log(f"# VERDICT: {verdict}")
    _log(f"# Reason: {verdict_reason}")
    _log(f"# Receipt: {out_path}")
    return 0 if verdict.startswith("PASS") else 1


def _meta(yasna: dict) -> dict:
    return {
        "yasna": yasna["yasna"],
        "n_verses": yasna["n_verses"],
        "n_letters": yasna["n_letters"],
        "source_file": yasna["source_file"],
    }


# ---- Driver ------------------------------------------------------------

def main() -> int:
    _log(f"# {EXP} -- starting (F55 -> Avestan Yasna 28, H63)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # A5: normaliser sentinel
    sentinel_actual = _normalise_avestan(_NORMALISER_SENTINEL_INPUT)
    normaliser_ok = (sentinel_actual == _NORMALISER_SENTINEL_EXPECTED)
    audit["checks"]["normaliser_sentinel"] = (
        "OK" if normaliser_ok else
        f"FAIL: expected={_NORMALISER_SENTINEL_EXPECTED!r} "
        f"actual={sentinel_actual!r}"
    )
    _log(f"# Avestan normaliser sentinel: "
         f"{'OK' if normaliser_ok else 'FAIL'}")
    if not normaliser_ok:
        audit["ok"] = False
        audit["errors"].append("normaliser_sentinel_mismatch")
        return _write_receipt(
            "FAIL_audit_normaliser_sentinel",
            "Avestan normaliser sentinel does not match locked value.",
            audit, t_start, started_at_utc, actual_hash, {})

    # 1) Load Avestan corpus
    _log("# Step 1: loading Avestan Yasna corpus (Geldner edition) ...")
    yasnas = _load_avestan_yasnas()
    n_total = len(yasnas)
    yasna_nums = sorted(c["yasna"] for c in yasnas)
    _log(f"#   {n_total} yasnas loaded "
         f"(min={yasna_nums[0] if yasna_nums else '-'}, "
         f"max={yasna_nums[-1] if yasna_nums else '-'})")
    audit["checks"]["n_yasnas_total"] = n_total

    # A7: corpus completeness
    corpus_complete = (n_total == N_YASNAS_EXPECTED)
    audit["checks"]["corpus_complete"] = corpus_complete
    if not corpus_complete:
        audit["ok"] = False
        audit["errors"].append(
            f"corpus_incomplete:{n_total}!={N_YASNAS_EXPECTED}")
        return _write_receipt(
            "BLOCKED_corpus_incomplete",
            (f"Loaded {n_total} yasnas; expected "
             f"{N_YASNAS_EXPECTED} (A7 violation)."),
            audit, t_start, started_at_utc, actual_hash, {})

    target_match = [c for c in yasnas if c["yasna"] == TARGET_YASNA]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append(f"yasna_{TARGET_YASNA}_not_found")
        return _write_receipt(
            "BLOCKED_corpus_missing",
            f"Yasna {TARGET_YASNA} not found.",
            audit, t_start, started_at_utc, actual_hash, {})
    target = target_match[0]
    canon_str = target["letters_26"]
    distinct_chars = len(set(canon_str))
    _log(f"#   Yasna {TARGET_YASNA} (Ahunavaiti Gatha, ch. 1): "
         f"{target['n_verses']} verses, {target['n_letters']} letters, "
         f"{distinct_chars}/26 distinct alphabet chars")
    audit["checks"]["target_yasna"] = TARGET_YASNA
    audit["checks"]["target_n_verses"] = target["n_verses"]
    audit["checks"]["target_n_letters"] = target["n_letters"]
    audit["checks"]["target_n_distinct_chars"] = distinct_chars

    if (target["n_letters"] < TARGET_MIN_LETTERS
            or target["n_verses"] < TARGET_MIN_VERSES):
        audit["ok"] = False
        return _write_receipt(
            "BLOCKED_yasna_28_too_short",
            (f"Yasna 28 has {target['n_letters']} letters / "
             f"{target['n_verses']} verses (need >= "
             f"{TARGET_MIN_LETTERS} / {TARGET_MIN_VERSES})."),
            audit, t_start, started_at_utc, actual_hash,
            {"yasna_28": _meta(target)})

    # A6: alphabet coverage
    alphabet_coverage_ok = distinct_chars >= ALPHABET_COVERAGE_FLOOR
    audit["checks"]["alphabet_coverage_ok"] = alphabet_coverage_ok
    if not alphabet_coverage_ok:
        audit["ok"] = False
        audit["errors"].append(
            f"alphabet_coverage:{distinct_chars}<"
            f"{ALPHABET_COVERAGE_FLOOR}")
        return _write_receipt(
            "FAIL_audit_alphabet_coverage",
            (f"Yasna 28 uses {distinct_chars} of 26 alphabet letters "
             f"(need >= {ALPHABET_COVERAGE_FLOOR})."),
            audit, t_start, started_at_utc, actual_hash,
            {"yasna_28": _meta(target)})

    # 2) Build peer pool
    peers = [c for c in yasnas if c["yasna"] != TARGET_YASNA]
    n_peers = len(peers)
    _log(f"# Peer pool: {n_peers} Avestan yasnas "
         f"(F55-family floor = {PEER_AUDIT_FLOOR_F55})")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_pool_strategy"] = (
        "all_other_yasna_chapters_no_length_matching")
    if n_peers < PEER_AUDIT_FLOOR_F55:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_f55_floor:{n_peers}<{PEER_AUDIT_FLOOR_F55}")
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool {n_peers} < F55-family floor "
            f"{PEER_AUDIT_FLOOR_F55}.",
            audit, t_start, started_at_utc, actual_hash,
            {"yasna_28": _meta(target), "peers_n": n_peers})

    # 3) Variant enumeration: full n_letters x 25 substitutions
    _log("# Step 3: enumerating + scoring all V1 variants ...")
    cons_list = list(AVESTAN_ALPHABET_26)
    var_deltas: list[float] = []
    var_fires = 0
    max_var_delta = 0.0
    n_zero = 0
    n_above_tau = 0
    audit_violation_examples: list[dict] = []

    n_letters = len(canon_str)
    t_var_start = time.time()
    for p in range(n_letters):
        old_ch = canon_str[p]
        if old_ch not in AVESTAN_ALPHABET_SET:
            continue
        for repl in cons_list:
            if repl == old_ch:
                continue
            d = variant_delta_analytic(canon_str, p, repl)
            var_deltas.append(d)
            if d > max_var_delta:
                max_var_delta = d
            if d == 0.0:
                n_zero += 1
            if d > TAU_HIGH + AUDIT_TOL:
                n_above_tau += 1
                if len(audit_violation_examples) < 5:
                    audit_violation_examples.append({
                        "pos": p,
                        "old_ch": old_ch,
                        "new_ch": repl,
                        "delta": d,
                    })
            if 0 < d <= TAU_HIGH:
                var_fires += 1
        if (p + 1) % 500 == 0:
            _log(f"#   variant pos {p+1}/{n_letters} "
                 f"({time.time()-t_var_start:.1f}s)")

    n_variants_total = len(var_deltas)
    variant_recall = var_fires / n_variants_total if n_variants_total else 0.0
    _log(f"#   variants total      = {n_variants_total}")
    _log(f"#   max(variant_delta)  = {max_var_delta:.6f}")
    _log(f"#   n_above_tau (=2.0)  = {n_above_tau}")
    _log(f"#   n_zero_delta        = {n_zero}")
    _log(f"#   n_variants_fired    = {var_fires}")
    _log(f"#   variant_recall      = {variant_recall:.6f}")
    audit["checks"]["max_variant_delta"] = max_var_delta
    audit["checks"]["n_variants_total"] = n_variants_total
    audit["checks"]["n_variants_fired"] = var_fires
    audit["checks"]["n_variants_zero_delta"] = n_zero
    audit["checks"]["n_variants_above_tau"] = n_above_tau
    audit["checks"]["variant_recall"] = variant_recall

    if max_var_delta > TAU_HIGH + AUDIT_TOL:
        audit["ok"] = False
        audit["errors"].append(
            f"theorem_violation:max_variant_delta={max_var_delta}")
        return _write_receipt(
            "FAIL_audit_theorem",
            (f"max(variant_delta) = {max_var_delta:.6f} > "
             f"{TAU_HIGH} + {AUDIT_TOL} (theorem violation)."),
            audit, t_start, started_at_utc, actual_hash,
            {"yasna_28": _meta(target),
             "peers_n": n_peers,
             "audit_violation_examples": audit_violation_examples})

    # 4) Peer audit
    _log(f"# Step 4: scoring {n_peers} peer yasna pairs ...")
    canon_bigrams = bigrams_of(canon_str)
    peer_records: list[dict] = []
    peer_fires = 0
    min_peer_delta = float("inf")
    for peer in peers:
        peer_str = peer["letters_26"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_records.append({
            "yasna": peer["yasna"],
            "n_letters": peer["n_letters"],
            "delta": d,
        })
        if 0 < d <= TAU_HIGH:
            peer_fires += 1
        if d < min_peer_delta:
            min_peer_delta = d
    n_peer_pairs_total = len(peer_records)
    peer_fpr = peer_fires / n_peer_pairs_total if n_peer_pairs_total else 0.0
    peer_records_sorted = sorted(peer_records, key=lambda r: r["delta"])
    five_closest = [
        {"yasna": r["yasna"], "n_letters": r["n_letters"],
         "delta": r["delta"]}
        for r in peer_records_sorted[:5]
    ]
    _log(f"#   peer pairs total       = {n_peer_pairs_total}")
    _log(f"#   min(peer_delta)        = {min_peer_delta:.2f}")
    _log(f"#   peer pairs fired       = {peer_fires}")
    _log(f"#   peer FPR               = {peer_fpr:.6f}")
    _log(f"#   5 closest peers (raw bigram delta):")
    for c in five_closest:
        _log(f"#     Yasna {c['yasna']:<3d}  n_letters={c['n_letters']:<6d}"
             f"  delta={c['delta']:.2f}")
    audit["checks"]["min_peer_delta"] = min_peer_delta
    audit["checks"]["n_peer_pairs_total"] = n_peer_pairs_total
    audit["checks"]["n_peer_pairs_fired"] = peer_fires
    audit["checks"]["peer_fpr"] = peer_fpr
    audit["checks"]["five_closest_peers"] = five_closest

    # A4 audit: sentinel determinism
    _log("# Step 5: A4 sentinel determinism check ...")
    sentinel_rng = random.Random(SEED + 13)
    var_indices = list(range(n_variants_total))
    sentinel_rng.shuffle(var_indices)
    sentinel_var_idx = var_indices[:100]
    sentinel_ok = True
    sentinel_err: str | None = None
    for ix in sentinel_var_idx:
        p = ix // N_SUBSTITUTIONS_PER_POS
        old_ch = canon_str[p]
        non_old = [c for c in cons_list if c != old_ch]
        repl_idx = ix % N_SUBSTITUTIONS_PER_POS
        repl = non_old[repl_idx]
        d_first = var_deltas[ix]
        d_second = variant_delta_analytic(canon_str, p, repl)
        if d_first != d_second:
            sentinel_ok = False
            sentinel_err = (
                f"variant idx {ix} (pos={p}, repl={repl}) "
                f"non-deterministic: first={d_first}, second={d_second}")
            break
    audit["checks"]["sentinel_determinism"] = "OK" if sentinel_ok else (
        f"FAIL: {sentinel_err}")
    if not sentinel_ok:
        audit["warnings"].append(
            f"sentinel_determinism_warning:{sentinel_err}")

    # 5) Decide verdict
    target_meta_for_ladder = {
        "yasna": target["yasna"],
        "n_verses": target["n_verses"],
        "n_letters": target["n_letters"],
    }
    verdict, verdict_reason = _decide_verdict(
        target_meta_for_ladder, n_total, n_peers, normaliser_ok,
        alphabet_coverage_ok, max_var_delta, variant_recall, peer_fpr,
    )

    return _write_receipt(
        verdict, verdict_reason, audit,
        t_start, started_at_utc, actual_hash,
        {"yasna_28": _meta(target),
         "peers_n": n_peers,
         "peer_records_top10_closest":
             [{"yasna": r["yasna"], "n_letters": r["n_letters"],
               "delta": r["delta"]}
              for r in peer_records_sorted[:10]]},
    )


if __name__ == "__main__":
    sys.exit(main())
