"""exp107_F55_dn1_bigram/run.py
==================================
H62: F55 universal symbolic forgery detector (analytic-bound bigram-shift,
frozen tau = 2.0, no calibration) generalises off-shelf to Pali Digha
Nikaya 1 (DN 1, the Brahmajala Sutta), replicating F59 (Hebrew Psalm 78)
and F60 (Greek NT Mark 1) in a fourth language family (Indo-Aryan / Indic).

Hash-locked PREREG: ../PREREG.md (SHA-256 must match _PREREG_EXPECTED_HASH).

Protocol: byte-for-byte compatible with exp95j (Quran V1), exp105 (Hebrew
Psalm 78), and exp106 (Greek NT Mark 1) at the detector level. Deltas:
  - Pali normaliser (NEW): NFC + casefold + niggahita-fold + 31-letter
    whitelist. The 31 letters are the IAST/PTS Roman-Pali alphabet
    (8 vowels + 22 consonants + 1 niggahita).
  - Pali loader (NEW): SuttaCentral root-pli-ms Bilara JSON, scans
    data/corpora/pi/dn/ and data/corpora/pi/mn/ for *_root-pli-ms.json
    files; concatenates JSON values in insertion order to produce the
    per-sutta raw text stream.
  - DN 1 target (Brahmajala, the canonical opener of the Pali Canon).
  - NO length matching (matches exp95j Arabic-side, exp106 Greek-side).
  - Peer pool = all OTHER DN+MN suttas (185 suttas; full DN=34, MN=152).

This run uses ZERO compression calls; predicted wall-time < 60 s for
~1.8M variants on the 60K-letter DN 1 skeleton.
"""
from __future__ import annotations

import hashlib
import io
import json
import random
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

EXP = "exp107_F55_dn1_bigram"

# ---- Live progress log (always-flushing) -------------------------------
_PROGRESS_LOG = _ROOT / "results" / "experiments" / EXP / "progress.log"
_PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
_progress_fh = open(_PROGRESS_LOG, "w", encoding="utf-8", buffering=1)


def _log(msg: str) -> None:
    print(msg, flush=True)
    _progress_fh.write(msg + "\n")
    _progress_fh.flush()


# ---- PREREG hash sentinel ----------------------------------------------
_PREREG_EXPECTED_HASH = (
    "2bbb70ec86ebcd67f8779f0075293490de068554e4790081f65e046ee0a915fa"
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
            f"PREREG.md was modified after run.py was locked. "
            f"This run is invalidated per integrity protocol."
        )
    return actual


# ---- Frozen constants (PREREG §2) --------------------------------------
TARGET_SUTTA_ID = "dn1"
TARGET_COLLECTION = "dn"
TARGET_MIN_LETTERS = 1000
TARGET_MIN_SEGMENTS = 10
ALPHABET_COVERAGE_FLOOR = 25  # require >= 25 of 31 alphabet letters used
TAU_HIGH = 2.0
AUDIT_TOL = 1e-9
RECALL_FLOOR = 1.000
FPR_CEIL = 0.000
PARTIAL_FPR_BAND_HI = 0.05
PEER_AUDIT_FLOOR = 100
SEED = 42

# Pali alphabet 31 (IAST / PTS Roman, locked at PREREG seal):
#   vowels: a ā i ī u ū e o                                   (8)
#   consonants: k g ṅ c j ñ ṭ ḍ ṇ t d n p b m y r l ḷ v s h    (22)
#   niggahita: ṁ (U+1E41 m + dot above)                       (1)
PALI_ALPHABET_31 = (
    "a\u0101i\u012Bu\u016Beo"   # a ā i ī u ū e o
    "kg\u1E45c"                  # k g ṅ c
    "j\u00F1"                    # j ñ
    "\u1E6D\u1E0D\u1E47"         # ṭ ḍ ṇ
    "tdn"                        # t d n
    "pbm"                        # p b m
    "yrl\u1E37"                  # y r l ḷ
    "vsh"                        # v s h
    "\u1E41"                     # ṁ
)
assert len(PALI_ALPHABET_31) == 31, (
    f"Pali alphabet has {len(PALI_ALPHABET_31)} letters, expected 31"
)
PALI_ALPHABET_SET = set(PALI_ALPHABET_31)
N_SUBSTITUTIONS_PER_POS = len(PALI_ALPHABET_31) - 1  # 30

# Niggahīta fold: ṃ (U+1E43, m + dot below) -> ṁ (U+1E41, m + dot above).
# Both denote anusvāra in Pāli; SuttaCentral Bilara uses U+1E41.
NIGGAHITA_FOLD = {"\u1E43": "\u1E41"}

_NORMALISER_SENTINEL_INPUT = "Eva\u1E41 me suta\u1E41"      # "Evaṁ me sutaṁ"
_NORMALISER_SENTINEL_EXPECTED = "eva\u1E41mesuta\u1E41"     # "evaṁmesutaṁ"


def _normalise_pali(s: str) -> str:
    """Pali text -> 31-letter skeleton (lowercase Roman-IAST).

    Pipeline:
      1. NFC normalise (canonical-composed; 'ā' stays U+0101).
      2. casefold() to lowercase.
      3. Niggahīta fold ṃ -> ṁ.
      4. Whitelist only PALI_ALPHABET_31; drop everything else.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.casefold()
    for src, dst in NIGGAHITA_FOLD.items():
        s = s.replace(src, dst)
    return "".join(ch for ch in s if ch in PALI_ALPHABET_SET)


# ---- Pali corpus loader (SuttaCentral root-pli-ms Bilara JSON) ---------

_PALI_ROOT = _ROOT / "data" / "corpora" / "pi"


def _sutta_id_from_filename(filename: str) -> str:
    """`dn1_root-pli-ms.json` -> `dn1` ; `mn152_root-pli-ms.json` -> `mn152`."""
    return filename.split("_", 1)[0]


def _load_pali_suttas() -> list[dict]:
    """Load all DN + MN suttas from disk.

    Returns a list of dicts (one per sutta) with keys:
      collection, sutta_id, file, text_raw, n_segments, letters_31, n_letters
    """
    out: list[dict] = []
    for collection in ("dn", "mn"):
        coll_dir = _PALI_ROOT / collection
        if not coll_dir.is_dir():
            continue
        files = sorted(coll_dir.glob("*_root-pli-ms.json"))
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception as exc:
                _log(f"# WARN: failed to parse {f.name}: {exc}")
                continue
            if not isinstance(data, dict):
                continue
            raw = "".join(str(v) for v in data.values())
            skel = _normalise_pali(raw)
            out.append({
                "collection": collection,
                "sutta_id": _sutta_id_from_filename(f.name),
                "file": str(f),
                "text_raw": raw,
                "n_segments": len(data),
                "letters_31": skel,
                "n_letters": len(skel),
            })
    return out


# ---- Bigram primitives (byte-for-byte aligned with exp95j/95j/106) -----

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
    n_peers: int,
    normaliser_ok: bool,
    alphabet_coverage_ok: bool,
    max_var_delta: float | None,
    variant_recall: float | None,
    peer_fpr: float | None,
) -> tuple[str, str]:
    if target_meta is None:
        return ("BLOCKED_corpus_missing",
                "Pali corpus or DN 1 sutta not found.")
    if (target_meta["n_letters"] < TARGET_MIN_LETTERS
            or target_meta["n_segments"] < TARGET_MIN_SEGMENTS):
        return ("BLOCKED_dn1_too_short",
                f"DN 1 has {target_meta['n_letters']} letters / "
                f"{target_meta['n_segments']} segments (need >= "
                f"{TARGET_MIN_LETTERS} / {TARGET_MIN_SEGMENTS}).")
    if n_peers < PEER_AUDIT_FLOOR:
        return ("FAIL_audit_peer_pool_size",
                f"Peer pool has {n_peers} suttas "
                f"(need >= {PEER_AUDIT_FLOOR}).")
    if not normaliser_ok:
        return ("FAIL_audit_normaliser_sentinel",
                "Pali normaliser sentinel does not match locked value.")
    if not alphabet_coverage_ok:
        return ("FAIL_audit_alphabet_coverage",
                f"DN 1 uses fewer than {ALPHABET_COVERAGE_FLOOR} of 31 "
                f"Pali alphabet letters; pathological input.")
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
                    f"(within partial band {PARTIAL_FPR_BAND_HI}). "
                    f"Soft PASS, not paper-grade.")
        return ("FAIL_fpr_above_ceiling",
                f"peer FPR = {peer_fpr:.6f} > {FPR_CEIL}.")
    return ("PASS_universal_perfect_recall_zero_fpr",
            f"variant recall = {variant_recall:.6f} >= {RECALL_FLOOR} AND "
            f"peer FPR = {peer_fpr:.6f} <= {FPR_CEIL}. F55 detector "
            f"generalises off-shelf to Pali Digha Nikaya 1.")


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
        "hypothesis_id": "H62",
        "hypothesis": (
            "F55 analytic-bound bigram-shift detector (frozen tau = 2.0, "
            "no calibration) generalises off-shelf to Pali Digha Nikaya 1 "
            "(Brahmajala Sutta) with per-variant recall = 1.000 and "
            "per-(canon, peer)-pair FPR = 0.000 against the full DN+MN "
            "peer pool of all 185 other suttas."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at,
        "wall_time_s": time.time() - t_start,
        "prereg_hash": actual_hash,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp107_F55_dn1_bigram/PREREG.md",
        "amendment_chain": [
            "exp95j_bigram_shift_universal "
            "(F55 PASS_universal_perfect_recall_zero_fpr on Quran V1)",
            "exp105_F55_psalm78_bigram "
            "(F59 PASS_universal_perfect_recall_zero_fpr on Hebrew Psalm 78)",
            "exp106_F55_mark1_bigram "
            "(F60 PASS_universal_perfect_recall_zero_fpr on Greek NT Mark 1)",
            "exp107_F55_dn1_bigram (this run; F55 -> Pali DN 1)",
        ],
        "frozen_constants": {
            "SEED": SEED,
            "TAU_HIGH": TAU_HIGH,
            "AUDIT_TOL": AUDIT_TOL,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEIL": FPR_CEIL,
            "PARTIAL_FPR_BAND_HI": PARTIAL_FPR_BAND_HI,
            "TARGET_SUTTA_ID": TARGET_SUTTA_ID,
            "TARGET_COLLECTION": TARGET_COLLECTION,
            "TARGET_MIN_LETTERS": TARGET_MIN_LETTERS,
            "TARGET_MIN_SEGMENTS": TARGET_MIN_SEGMENTS,
            "ALPHABET_COVERAGE_FLOOR": ALPHABET_COVERAGE_FLOOR,
            "PEER_AUDIT_FLOOR": PEER_AUDIT_FLOOR,
            "PEER_POOL_STRATEGY":
                "all_other_dn_mn_suttas_no_length_matching",
            "PALI_ALPHABET_31": PALI_ALPHABET_31,
            "N_SUBSTITUTIONS_PER_POS": N_SUBSTITUTIONS_PER_POS,
            "calibration_source":
                "frozen_analytic_theorem_no_data_calibration",
        },
        "audit_report": audit,
        "pre_stage_diagnostic_receipt":
            "results/auxiliary/_dn1_bigram_sizing.json",
    }
    receipt.update(extra)
    out_path = out_dir / f"{EXP}.json"
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    _log(f"# VERDICT: {verdict}")
    _log(f"# Reason: {verdict_reason}")
    _log(f"# Receipt: {out_path}")
    return 0 if verdict.startswith("PASS") else 1


def _meta(sutta: dict) -> dict:
    return {
        "collection": sutta["collection"],
        "sutta_id": sutta["sutta_id"],
        "n_segments": sutta["n_segments"],
        "n_letters": sutta["n_letters"],
    }


# ---- Driver ------------------------------------------------------------

def main() -> int:
    _log(f"# {EXP} -- starting (F55 -> Pali DN 1, H62)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # A5: normaliser sentinel check (cheap, do early)
    sentinel_actual = _normalise_pali(_NORMALISER_SENTINEL_INPUT)
    normaliser_ok = (sentinel_actual == _NORMALISER_SENTINEL_EXPECTED)
    audit["checks"]["normaliser_sentinel"] = (
        "OK" if normaliser_ok else
        f"FAIL: expected={_NORMALISER_SENTINEL_EXPECTED!r} "
        f"actual={sentinel_actual!r}"
    )
    _log(f"# Pali normaliser sentinel: "
         f"{'OK' if normaliser_ok else 'FAIL'}")
    if not normaliser_ok:
        audit["ok"] = False
        audit["errors"].append("normaliser_sentinel_mismatch")
        return _write_receipt(
            "FAIL_audit_normaliser_sentinel",
            "Pali normaliser sentinel does not match locked value.",
            audit, t_start, started_at_utc, actual_hash, {})

    # 1) Load Pali corpus
    _log("# Step 1: loading Pali Tipitaka (SuttaCentral root-pli-ms) ...")
    suttas = _load_pali_suttas()
    n_total = len(suttas)
    by_coll = Counter(s["collection"] for s in suttas)
    n_dn = by_coll.get("dn", 0)
    n_mn = by_coll.get("mn", 0)
    _log(f"#   {n_total} suttas loaded (DN={n_dn}, MN={n_mn})")
    audit["checks"]["n_suttas_total"] = n_total
    audit["checks"]["n_dn"] = n_dn
    audit["checks"]["n_mn"] = n_mn

    target_match = [s for s in suttas if s["sutta_id"] == TARGET_SUTTA_ID]
    if not target_match:
        audit["ok"] = False
        audit["errors"].append("dn1_not_found")
        return _write_receipt(
            "BLOCKED_corpus_missing",
            "DN 1 not found in Pali corpus.",
            audit, t_start, started_at_utc, actual_hash, {})
    target = target_match[0]
    canon_str = target["letters_31"]
    distinct_chars = len(set(canon_str))
    _log(f"#   DN 1 (Brahmajala): {target['n_segments']} segments, "
         f"{target['n_letters']} letters, "
         f"{distinct_chars}/31 distinct alphabet chars")
    audit["checks"]["target_sutta_id"] = TARGET_SUTTA_ID
    audit["checks"]["target_collection"] = target["collection"]
    audit["checks"]["target_n_segments"] = target["n_segments"]
    audit["checks"]["target_n_letters"] = target["n_letters"]
    audit["checks"]["target_n_distinct_chars"] = distinct_chars

    if (target["n_letters"] < TARGET_MIN_LETTERS
            or target["n_segments"] < TARGET_MIN_SEGMENTS):
        audit["ok"] = False
        return _write_receipt(
            "BLOCKED_dn1_too_short",
            (f"DN 1 has {target['n_letters']} letters / "
             f"{target['n_segments']} segments (need >= "
             f"{TARGET_MIN_LETTERS} / {TARGET_MIN_SEGMENTS})."),
            audit, t_start, started_at_utc, actual_hash,
            {"dn1": _meta(target)})

    # A6: alphabet coverage check
    alphabet_coverage_ok = distinct_chars >= ALPHABET_COVERAGE_FLOOR
    audit["checks"]["alphabet_coverage_ok"] = alphabet_coverage_ok
    if not alphabet_coverage_ok:
        audit["ok"] = False
        audit["errors"].append(
            f"alphabet_coverage:{distinct_chars}<{ALPHABET_COVERAGE_FLOOR}")
        return _write_receipt(
            "FAIL_audit_alphabet_coverage",
            (f"DN 1 uses {distinct_chars} of 31 alphabet letters "
             f"(need >= {ALPHABET_COVERAGE_FLOOR})."),
            audit, t_start, started_at_utc, actual_hash,
            {"dn1": _meta(target)})

    # 2) Build peer pool: ALL DN+MN except DN 1
    peers = [s for s in suttas if s["sutta_id"] != TARGET_SUTTA_ID]
    n_peers = len(peers)
    _log(f"# Peer pool: {n_peers} Pali suttas "
         f"(NO length matching, matches exp95j/exp106 protocol)")
    audit["checks"]["peer_pool_size"] = n_peers
    audit["checks"]["peer_pool_strategy"] = (
        "all_other_dn_mn_suttas_no_length_matching")
    if n_peers < PEER_AUDIT_FLOOR:
        audit["ok"] = False
        audit["errors"].append(
            f"peer_pool_size_below_floor:{n_peers}<{PEER_AUDIT_FLOOR}")
        return _write_receipt(
            "FAIL_audit_peer_pool_size",
            f"Peer pool {n_peers} < {PEER_AUDIT_FLOOR}.",
            audit, t_start, started_at_utc, actual_hash,
            {"dn1": _meta(target), "peers_n": n_peers})

    # 3) Variant enumeration: full n_letters x 30 substitutions
    _log("# Step 3: enumerating + scoring all V1 variants ...")
    cons_list = list(PALI_ALPHABET_31)
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
        if old_ch not in PALI_ALPHABET_SET:
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
        if (p + 1) % 5000 == 0:
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

    # A1 audit: theorem
    if max_var_delta > TAU_HIGH + AUDIT_TOL:
        audit["ok"] = False
        audit["errors"].append(
            f"theorem_violation:max_variant_delta={max_var_delta}")
        return _write_receipt(
            "FAIL_audit_theorem",
            (f"max(variant_delta) = {max_var_delta:.6f} > "
             f"{TAU_HIGH} + {AUDIT_TOL} (theorem violation; would be "
             f"unprecedented across alphabets)."),
            audit, t_start, started_at_utc, actual_hash,
            {"dn1": _meta(target),
             "peers_n": n_peers,
             "audit_violation_examples": audit_violation_examples})

    # 4) Peer audit
    _log(f"# Step 4: scoring {n_peers} peer sutta pairs ...")
    canon_bigrams = bigrams_of(canon_str)
    peer_records: list[dict] = []
    peer_fires = 0
    min_peer_delta = float("inf")
    for peer in peers:
        peer_str = peer["letters_31"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_records.append({
            "collection": peer["collection"],
            "sutta_id": peer["sutta_id"],
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
        {"collection": r["collection"], "sutta_id": r["sutta_id"],
         "n_letters": r["n_letters"], "delta": r["delta"]}
        for r in peer_records_sorted[:5]
    ]
    _log(f"#   peer pairs total       = {n_peer_pairs_total}")
    _log(f"#   min(peer_delta)        = {min_peer_delta:.2f}")
    _log(f"#   peer pairs fired       = {peer_fires}")
    _log(f"#   peer FPR               = {peer_fpr:.6f}")
    _log(f"#   5 closest peers (raw bigram delta):")
    for c in five_closest:
        _log(f"#     {c['collection']:<2s} {c['sutta_id']:<6s} "
             f"n_letters={c['n_letters']:<6d} delta={c['delta']:.2f}")
    audit["checks"]["min_peer_delta"] = min_peer_delta
    audit["checks"]["n_peer_pairs_total"] = n_peer_pairs_total
    audit["checks"]["n_peer_pairs_fired"] = peer_fires
    audit["checks"]["peer_fpr"] = peer_fpr
    audit["checks"]["five_closest_peers"] = five_closest

    # A4 audit: sentinel determinism (re-run a 100-pair sample)
    _log("# Step 5: A4 sentinel determinism check ...")
    sentinel_rng = random.Random(SEED + 13)
    var_indices = list(range(n_variants_total))
    sentinel_rng.shuffle(var_indices)
    sentinel_var_idx = var_indices[:100]
    sentinel_ok = True
    sentinel_err: str | None = None
    for ix in sentinel_var_idx:
        # Decode (pos, repl) from index ix:
        # variant index ix -> (pos = ix // 30, repl_index_in_30 = ix % 30)
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
        # not a verdict-flip; recorded as warning only

    # 5) Decide verdict
    target_meta_for_ladder = {
        "collection": target["collection"],
        "sutta_id": target["sutta_id"],
        "n_segments": target["n_segments"],
        "n_letters": target["n_letters"],
    }
    verdict, verdict_reason = _decide_verdict(
        target_meta_for_ladder, n_peers, normaliser_ok,
        alphabet_coverage_ok, max_var_delta, variant_recall, peer_fpr,
    )

    return _write_receipt(
        verdict, verdict_reason, audit,
        t_start, started_at_utc, actual_hash,
        {"dn1": _meta(target),
         "peers_n": n_peers,
         "peer_records_top10_closest":
             [{"collection": r["collection"], "sutta_id": r["sutta_id"],
               "n_letters": r["n_letters"], "delta": r["delta"]}
              for r in peer_records_sorted[:10]]},
    )


if __name__ == "__main__":
    sys.exit(main())
