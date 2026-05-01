"""scripts/_dn1_bigram_sizing.py
====================================
Sanity check before drafting exp107_F55_dn1_bigram PREREG.

Question: does F55's analytic-bound bigram-shift detector (tau = 2.0)
give a clean recall-1 / FPR-0 separation on Pali Digha Nikaya 1 (DN 1
- Brahmajala Sutta), replicating the Quran V1 (exp95j), Hebrew Psalm 78
(exp105/F59), and Greek NT Mark 1 (exp106/F60) results in a fourth
language family (Indo-Aryan/Indic, non-Indo-European-Hellenic,
non-Semitic)?

Computes:
1) **Variant audit (theorem)** -- analytic delta_bigram for a sample of
   single-Pali-letter substitutions of DN 1. Theorem predicts max
   <= 2.0 in any alphabet.
2) **Peer audit (FPR floor)** -- exact delta_bigram between DN 1 and
   each of the other 185 Pali suttas in DN+MN (no length matching;
   matches the Quran-side exp95j Arabic protocol exactly, like Greek
   F60 did with the full Greek NT pool).

Decision rule (PROCEED-to-PREREG):
- variant max <= 2.0 STRICTLY (theorem holds)
- peer min  >  2.0 with safety margin >= 5x  (FPR = 0 plausible)

NO-COMPRESSION-CALL diagnostic; runs in seconds.

Pali alphabet (31 letters, locked):
- 8 vowels:        a a-bar i i-bar u u-bar e o
- 22 consonants:   k g n-dot c j n-tilde t-dot d-dot n-dot t d n p b m
                   y r l l-dot v s h
- 1 niggahita:     m-dot (U+1E41)
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# -----------------------------------------------------------------------------
# Pali corpus loader (SuttaCentral root-pli-ms Bilara JSON)
# -----------------------------------------------------------------------------

# Pali alphabet 31 (IAST / PTS Roman):
#   vowels: a a-macron i i-macron u u-macron e o            (8)
#   consonants: k g n-dot c j n-tilde t-dot d-dot n-dot
#               t d n p b m y r l l-dot v s h               (22)
#   niggahita: m-dot above (U+1E41)                         (1)
PALI_ALPHABET_31 = (
    "a\u0101i\u012Bu\u016Beo"   # vowels: a, ā, i, ī, u, ū, e, o
    "kg\u1E45c"                  # k g ṅ c
    "j\u00F1"                    # j ñ
    "\u1E6D\u1E0D\u1E47"         # ṭ ḍ ṇ
    "tdn"                        # t d n
    "pbm"                        # p b m
    "yrl\u1E37"                  # y r l ḷ
    "vsh"                        # v s h
    "\u1E41"                     # ṁ (niggahīta, U+1E41 m with dot above)
)
assert len(PALI_ALPHABET_31) == 31, f"Pali alphabet has {len(PALI_ALPHABET_31)} letters, expected 31"
PALI_ALPHABET_SET = set(PALI_ALPHABET_31)


# Niggahīta canonicalisation: many editions use ṃ (U+1E43, m + dot below);
# Bilara/SuttaCentral uses ṁ (U+1E41, m + dot above). Both denote anusvāra.
# Fold to U+1E41 to match the source text for byte-exact reproducibility.
NIGGAHITA_FOLD = {"\u1E43": "\u1E41"}  # ṃ -> ṁ


def _normalise_pali(s: str) -> str:
    """Pali text -> 31-letter skeleton (lowercase Roman-IAST).

    Pipeline:
      1. NFC normalise (canonical-composed; "ā" stays as one codepoint).
      2. Lowercase (using casefold for safety).
      3. Fold ṃ -> ṁ (both denote niggahīta).
      4. Whitelist: keep only characters in PALI_ALPHABET_31; drop all
         whitespace, punctuation, em-dashes, digits, sutta-IDs, etc.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.casefold()
    for src, dst in NIGGAHITA_FOLD.items():
        s = s.replace(src, dst)
    return "".join(ch for ch in s if ch in PALI_ALPHABET_SET)


_PALI_ROOT = _ROOT / "data" / "corpora" / "pi"


def _sutta_id_from_filename(filename: str) -> str:
    """`dn1_root-pli-ms.json` -> `dn1` ; `mn152_root-pli-ms.json` -> `mn152`."""
    return filename.split("_", 1)[0]


def _load_pali_suttas() -> list[dict]:
    """Load all DN + MN suttas from disk.

    Returns a list of dicts, one per sutta:
      { "collection": "dn"|"mn",
        "sutta_id":   "dn1" | "mn34" | ... ,
        "file":       Path,
        "text_raw":   concatenated raw text (values of the JSON dict in order),
        "n_segments": number of Bilara segment IDs in the sutta,
        "letters_31": pali skeleton string,
        "n_letters":  len(letters_31) }
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
                print(f"# WARN: failed to parse {f.name}: {exc}", file=sys.stderr)
                continue
            if not isinstance(data, dict):
                continue
            # Bilara segment dict: keys are reference strings like "dn1:1.1.1",
            # values are Pali text. Concatenate values in insertion order
            # (the JSON file is a sutta-text stream).
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


# -----------------------------------------------------------------------------
# F55 frozen analytic-bound tau (locked at exp95j PREREG)
# -----------------------------------------------------------------------------
TAU_HIGH = 2.0
SAFETY_MARGIN = 5.0   # require peer-min / tau >= 5x to PROCEED

# Variant audit: how many variants to sample
N_VARIANT_SAMPLE = 1000

# Target chapter: DN 1, the Brahmajāla Sutta (the "Divine Net"), which is
# the canonical OPENING sutta of the Pāli Canon's first nikāya, structurally
# parallel to Mark 1 (Gospel opening) and Quran V1 (whole canon scope).
TARGET_SUTTA_ID = "dn1"


def bigrams_of(s: str) -> Counter:
    """Counter of all consecutive 2-character substrings (raw counts)."""
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    """Delta_bigram = 1/2 * sum_k |c1[k] - c2[k]| (raw counts)."""
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    """Analytic O(1) delta for substitution canon[p] -> new_ch.

    Bigram-shift theorem 3.2 (exp95j): for any single-letter substitution
    on any alphabet, this returns a value in (0, 2.0]. Equality at 2.0
    corresponds to interior positions where the two flanking bigrams
    are otherwise unchanged; values < 2 occur only at boundary positions
    (no left or no right bigram) which is rare in long chapters.
    """
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


def main() -> int:
    t0 = time.time()
    print("# _dn1_bigram_sizing.py  --  sanity for exp107 F55 -> Pali DN 1")
    print()

    # 1) Sentinel: normaliser test on a known Pali phrase
    sentinel_raw = "Eva\u1E41 me suta\u1E41"  # "Evaṁ me sutaṁ" (canonical opener)
    sentinel_norm = _normalise_pali(sentinel_raw)
    sentinel_expected = "eva\u1E41mesuta\u1E41"
    print(f"# Pali normaliser sentinel:")
    print(f"#   raw       = {sentinel_raw!r}")
    print(f"#   normalised = {sentinel_norm!r}")
    print(f"#   expected  = {sentinel_expected!r}")
    print(f"#   match     = {sentinel_norm == sentinel_expected}")
    if sentinel_norm != sentinel_expected:
        print("ERROR: Pali normaliser sentinel failed", file=sys.stderr)
        return 2
    print()

    # 2) Load Pali corpus
    suttas = _load_pali_suttas()
    print(f"# Pali corpus (SuttaCentral root-pli-ms) loaded: "
          f"{len(suttas)} suttas (DN+MN combined)")
    by_coll = Counter(s["collection"] for s in suttas)
    for coll, n in by_coll.items():
        print(f"#   {coll}: {n} suttas")
    print()

    target_match = [s for s in suttas if s["sutta_id"] == TARGET_SUTTA_ID]
    if not target_match:
        print(f"ERROR: {TARGET_SUTTA_ID} not found in Pali corpus",
              file=sys.stderr)
        return 2
    target = target_match[0]
    canon_str = target["letters_31"]
    n_letters = len(canon_str)
    n_segments = target["n_segments"]
    print(f"# Target: {TARGET_SUTTA_ID} (Brahmajāla Sutta)")
    print(f"#   raw text length         = {len(target['text_raw'])} chars")
    print(f"#   skeleton (Pali-31)      = {n_letters} chars")
    print(f"#   bilara segments         = {n_segments}")
    print(f"#   distinct skeleton chars = {len(set(canon_str))} / 31")
    if n_letters < 1000:
        print(f"# WARN: target skeleton {n_letters} < 1000 floor", file=sys.stderr)
    if n_segments < 10:
        print(f"# WARN: target n_segments {n_segments} < 10 floor", file=sys.stderr)
    print()

    # 3) Build peer pool: ALL other DN+MN suttas (no length matching;
    #    matches exp95j Arabic-side and exp106 Greek-side F55 protocol).
    peers = [s for s in suttas if s["sutta_id"] != TARGET_SUTTA_ID]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} Pali suttas "
          f"(all DN+MN except {TARGET_SUTTA_ID}; "
          f"NO length matching; matches exp95j/exp106 protocol)")

    if n_peers < 100:
        print(f"# WARN: peer pool {n_peers} < 100 floor", file=sys.stderr)

    # 4) Variant audit
    print()
    print("# --- Variant audit (theorem replication on Pali alphabet) ---")
    pali_positions = [
        i for i, ch in enumerate(canon_str)
        if ch in PALI_ALPHABET_SET
    ]
    print(f"#   Pali-letter positions = {len(pali_positions)} "
          f"(should equal n_letters)")
    if len(pali_positions) != n_letters:
        print(f"# WARN: skeleton has {n_letters - len(pali_positions)} "
              f"non-alphabet chars; investigate")

    var_rng = random.Random(43)
    sample_specs: list[tuple[int, str, str]] = []
    while len(sample_specs) < N_VARIANT_SAMPLE:
        pos = var_rng.choice(pali_positions)
        repl = var_rng.choice(PALI_ALPHABET_31)
        old_ch = canon_str[pos]
        if repl == old_ch:
            continue
        sample_specs.append((pos, old_ch, repl))

    var_deltas = [
        variant_delta_analytic(canon_str, pos, repl)
        for (pos, _old, repl) in sample_specs
    ]
    var_max = max(var_deltas)
    var_min = min(var_deltas)
    var_mean = sum(var_deltas) / len(var_deltas)
    n_zero = sum(1 for d in var_deltas if d == 0.0)
    n_above_tau = sum(1 for d in var_deltas if d > TAU_HIGH)
    print(f"#   N_sampled        = {len(var_deltas)}")
    print(f"#   variant_delta_min  = {var_min:.4f}")
    print(f"#   variant_delta_mean = {var_mean:.4f}")
    print(f"#   variant_delta_max  = {var_max:.4f}")
    print(f"#   n_zero_delta       = {n_zero}")
    print(f"#   n_above_tau (=2.0) = {n_above_tau}")

    # 5) Peer audit
    print()
    print("# --- Peer audit (FPR floor) ---")
    canon_bigrams = bigrams_of(canon_str)
    peer_deltas: list[tuple[str, str, float, int]] = []
    for peer in peers:
        peer_str = peer["letters_31"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_deltas.append((
            peer["collection"],
            peer["sutta_id"],
            d,
            peer["n_letters"],
        ))
    deltas_only = sorted(d for (_, _, d, _) in peer_deltas)
    peer_min = deltas_only[0]
    peer_p5 = deltas_only[max(0, int(len(deltas_only) * 0.05) - 1)]
    peer_median = deltas_only[len(deltas_only) // 2]
    peer_max = deltas_only[-1]
    peer_mean = sum(deltas_only) / len(deltas_only)
    print(f"#   peers evaluated    = {len(peer_deltas)}")
    print(f"#   peer_delta_min     = {peer_min:.2f}")
    print(f"#   peer_delta_p5      = {peer_p5:.2f}")
    print(f"#   peer_delta_median  = {peer_median:.2f}")
    print(f"#   peer_delta_mean    = {peer_mean:.2f}")
    print(f"#   peer_delta_max     = {peer_max:.2f}")
    print(f"#   tau_high (locked)  = {TAU_HIGH}")
    print(f"#   peer_min / tau     = {peer_min / TAU_HIGH:.1f}x")

    closest = sorted(peer_deltas, key=lambda r: r[2])[:5]
    print(f"#   5 closest peers:")
    for (coll, sid, d, n_l) in closest:
        print(f"#     {coll:<2s}  {sid:<6s}  n_letters={n_l:<6d}  delta={d:.2f}")

    # 6) Decision
    print()
    print("# --- Decision ---")
    theorem_ok = (var_max <= TAU_HIGH + 1e-9) and (n_above_tau == 0)
    fpr_floor_ok = (peer_min > TAU_HIGH) and (peer_min >= TAU_HIGH * SAFETY_MARGIN)

    if theorem_ok and fpr_floor_ok:
        verdict = "PROCEED_TO_PREREG"
        msg = (f"Variant theorem holds (max = {var_max:.2f} <= 2.0); "
               f"peer min = {peer_min:.2f} >= {SAFETY_MARGIN}x safety "
               f"margin of tau = 2.0. Cross-tradition F55 on Pali DN 1 "
               f"is safe to PREREG and run.")
    elif theorem_ok and not fpr_floor_ok:
        verdict = "BLOCK_FPR_RISK"
        msg = (f"Variant theorem OK (max = {var_max:.2f}) but peer_min "
               f"= {peer_min:.2f} below {SAFETY_MARGIN}x safety margin "
               f"of tau = 2.0.")
    elif not theorem_ok:
        verdict = "BLOCK_THEOREM_BROKEN"
        msg = (f"Variant theorem FAILED on Pali: max variant delta = "
               f"{var_max:.2f} > 2.0 ({n_above_tau} variants above tau). "
               f"Unexpected; investigate before any PREREG.")
    else:
        verdict = "BLOCK_UNKNOWN"
        msg = "Unhandled branch."

    print(f"# verdict: {verdict}")
    print(f"# {msg}")
    print()
    print(f"# wall-time: {time.time() - t0:.1f}s")

    # 7) Persist receipt
    out_dir = _ROOT / "results" / "auxiliary"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "_dn1_bigram_sizing.json"
    receipt = {
        "schema": "dn1_bigram_sizing_v1",
        "filed_as": "exploratory_diagnostic",
        "purpose": "Sanity check before exp107_F55_dn1_bigram PREREG draft",
        "target_sutta_id": TARGET_SUTTA_ID,
        "target_collection": target["collection"],
        "target_n_segments": n_segments,
        "target_n_letters_skeleton": n_letters,
        "target_n_distinct_letters": len(set(canon_str)),
        "tau_high": TAU_HIGH,
        "safety_margin_x": SAFETY_MARGIN,
        "alphabet_size": len(PALI_ALPHABET_31),
        "alphabet_string": PALI_ALPHABET_31,
        "peer_pool_strategy":
            "all_other_dn_mn_suttas_no_length_matching"
            "_matches_exp95j_arabic_and_exp106_greek_protocol",
        "n_peers": n_peers,
        "n_dn": by_coll.get("dn", 0),
        "n_mn": by_coll.get("mn", 0),
        "normaliser_sentinel": {
            "raw": sentinel_raw,
            "normalised": sentinel_norm,
            "expected": sentinel_expected,
            "ok": sentinel_norm == sentinel_expected,
        },
        "variant_audit": {
            "n_sampled": len(var_deltas),
            "min": var_min,
            "mean": var_mean,
            "max": var_max,
            "n_zero": n_zero,
            "n_above_tau": n_above_tau,
            "theorem_ok": theorem_ok,
        },
        "peer_audit": {
            "n_peers": n_peers,
            "min": peer_min,
            "p5": peer_p5,
            "median": peer_median,
            "mean": peer_mean,
            "max": peer_max,
            "min_over_tau_ratio": peer_min / TAU_HIGH,
            "fpr_floor_ok": fpr_floor_ok,
            "five_closest": [
                {"collection": c, "sutta_id": s, "delta": d, "n_letters": n_l}
                for (c, s, d, n_l) in closest
            ],
        },
        "verdict": verdict,
        "message": msg,
        "wall_time_s": time.time() - t0,
    }
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"# receipt: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
