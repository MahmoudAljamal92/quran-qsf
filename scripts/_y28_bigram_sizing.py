"""scripts/_y28_bigram_sizing.py
====================================
Sanity check before drafting exp108_F55_y28_bigram PREREG.

Question: does F55's analytic-bound bigram-shift detector (tau = 2.0)
give a clean recall-1 / FPR-0 separation on Avestan Yasna 28 (the
opening chapter of the Ahunavaiti Gatha, oldest canonical layer of
the Zoroastrian Avesta), replicating the prior four F55 cross-tradition
results in a fifth language family (Indo-Iranian / Old Iranian)?

Computes:
1) **Variant audit (theorem)** -- analytic delta_bigram for a sample of
   single-Avestan-letter substitutions of Yasna 28. Theorem predicts
   max <= 2.0 in any alphabet.
2) **Peer audit (FPR floor)** -- exact delta_bigram between Yasna 28
   and each of the other 72 yasnas (no length matching; matches the
   Quran-side exp95j and Greek-side exp106 protocols).

Decision rule (PROCEED-to-PREREG):
- variant max <= 2.0 STRICTLY (theorem holds)
- peer min  >  2.0 with safety margin >= 5x  (FPR = 0 plausible)
- peer pool >= 50 (relaxed F55-family floor; F55 is calibration-free
  so the F53 inherited floor of 100 is over-engineered for this
  detector class -- justified in PREREG §2)

NO-COMPRESSION-CALL diagnostic; runs in seconds.

Avestan transliteration: Geldner / Pope edition with HTML-entity
encoded diacritics (â, î, ô, û, ê, å, ã, ñ, ý). After
NFD-decompose + Mn-strip + casefold the residual alphabet is
ASCII a-z (26 letters); empirical coverage will be lower as some
Latin letters (q, l) are rare or absent in Avestan.
"""
from __future__ import annotations

import html
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
# F55 frozen analytic-bound tau (locked at exp95j PREREG)
# -----------------------------------------------------------------------------
TAU_HIGH = 2.0
SAFETY_MARGIN = 5.0
N_VARIANT_SAMPLE = 1000

# F55-family peer-pool floor (relaxed from exp104c F53 100-floor;
# F55 is calibration-free and only needs a stable min(peer_Δ) statistic).
PEER_AUDIT_FLOOR_F55 = 50

# Avestan post-normalisation alphabet: 26 lowercase ASCII letters.
# (Empirical Avestan transliteration uses a subset; q and l are
# essentially absent.)
AVESTAN_ALPHABET_26 = "abcdefghijklmnopqrstuvwxyz"
AVESTAN_ALPHABET_SET = set(AVESTAN_ALPHABET_26)

# Target chapter: Yasna 28 (start of the Ahunavaiti Gatha; first hymn of
# Zarathushtra; oldest canonical Avestan layer; structurally analogous
# to Mark 1 / DN 1 / Quran V1 as a "canonical opener").
TARGET_YASNA = 28

# -----------------------------------------------------------------------------
# Avestan corpus loader
# -----------------------------------------------------------------------------

_AVESTAN_ROOT = _ROOT / "data" / "corpora" / "ae"

# Single-file-per-chapter and multi-chapter file layout
_AVESTAN_FILES = [
    "y0to8.htm", "y9to11.htm", "y12.htm", "y13to27.htm",
    "y28to34.htm", "y35to42.htm", "y43to46.htm", "y47to50.htm",
    "y51.htm", "y52.htm", "y53.htm", "y54to72.htm",
]

# Match <H3>...</H3> bodies. Three patterns observed in Avesta.org HTML:
#   <H3>0. Introduction </H3>             (y0to8.htm intro)
#   <H3>Chapter 28.</H3>                  (first chapter in multi-chapter files)
#   <H3>YASNA - Chapter 29.</H3>          (subsequent chapters in multi-chapter files)
# We extract the H3 body and parse a chapter number from it via _CHAP_NUM_RE.
_H3_RE = re.compile(r"<H3\b[^>]*>([\s\S]*?)</H3>", re.IGNORECASE)
_CHAP_NUM_RE = re.compile(r"(\d+)")

# Match a verse <DT>NN ... <DD>... block. We grab the verse number from
# <DT>NN and concatenate all <DD> content until the next <DT> or </DL>.
# We also accept stage-direction <DT>(zôt, ...) lines but skip them.
_DT_RE = re.compile(r"<DT>([^<]*?)(?=<DT>|<DD>|</DL>|<H3>|$)",
                    re.IGNORECASE | re.DOTALL)
_DD_RE = re.compile(r"<DD>(.*?)(?=<DT>|</DL>|<H3>|$)",
                    re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html_tags(s: str) -> str:
    return _TAG_RE.sub(" ", s)


def _normalise_avestan(s: str) -> str:
    """Avestan transliteration -> 26-letter ASCII skeleton.

    Pipeline:
      1. HTML entity decode (`&acirc;` -> â etc).
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
    """Parse one y*.htm file, return list of {yasna, n_verses, text_raw,
    letters_26, n_letters} dicts."""
    raw = path.read_text(encoding="latin-1", errors="replace")
    # Find all <H3>...</H3> bodies and the chapter number from each body.
    h3_matches = list(_H3_RE.finditer(raw))
    matches: list[tuple[int, int, int]] = []  # (yasna_n, content_start, content_end_exclusive)
    for i, m in enumerate(h3_matches):
        body = m.group(1)
        nm = _CHAP_NUM_RE.search(body)
        if nm is None:
            continue  # subtitle / non-chapter H3 (defensive)
        yasna_n = int(nm.group(1))
        content_start = m.end()
        content_end = (h3_matches[i + 1].start()
                       if i + 1 < len(h3_matches) else len(raw))
        matches.append((yasna_n, content_start, content_end))
    if not matches:
        return []
    out: list[dict] = []
    for (yasna_n, start, end) in matches:
        chunk = raw[start:end]
        # Extract verse <DD> blocks; skip stage-direction <DT> lines
        # (parenthesised priest names like "(zôt, u râspî,)").
        dd_blocks = _DD_RE.findall(chunk)
        verses_text: list[str] = []
        for dd in dd_blocks:
            text = _strip_html_tags(html.unescape(dd))
            text = text.strip()
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
            print(f"# WARN: {fname} missing", file=sys.stderr)
            continue
        out.extend(_parse_avestan_file(p))
    # Dedupe by yasna number (each yasna should appear exactly once
    # across all files; multi-chapter files split correctly).
    seen: set[int] = set()
    uniq: list[dict] = []
    for c in sorted(out, key=lambda r: r["yasna"]):
        if c["yasna"] in seen:
            print(f"# WARN: duplicate Yasna {c['yasna']} (kept first)",
                  file=sys.stderr)
            continue
        seen.add(c["yasna"])
        uniq.append(c)
    return uniq


# -----------------------------------------------------------------------------
# Bigram primitives
# -----------------------------------------------------------------------------

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


def main() -> int:
    t0 = time.time()
    print("# _y28_bigram_sizing.py  --  sanity for exp108 F55 -> Avestan Yasna 28")
    print()

    # 1) Sentinel
    sentinel_raw = "ahy&acirc; &yacute;&acirc;s&acirc; nemangh&acirc;"
    sentinel_norm = _normalise_avestan(sentinel_raw)
    sentinel_expected = "ahyayasanemangha"
    print("# Avestan normaliser sentinel:")
    print(f"#   raw       = {sentinel_raw!r}")
    print(f"#   normalised = {sentinel_norm!r}")
    print(f"#   expected  = {sentinel_expected!r}")
    print(f"#   match     = {sentinel_norm == sentinel_expected}")
    if sentinel_norm != sentinel_expected:
        print("ERROR: Avestan normaliser sentinel failed", file=sys.stderr)
        return 2
    print()

    # 2) Load Avestan corpus
    yasnas = _load_avestan_yasnas()
    print(f"# Avestan Yasna corpus loaded: {len(yasnas)} chapters")
    if yasnas:
        print(f"#   yasna numbers: "
              f"{min(c['yasna'] for c in yasnas)}-"
              f"{max(c['yasna'] for c in yasnas)}")
    distinct_letters_total: Counter = Counter()
    for c in yasnas:
        distinct_letters_total.update(c["letters_26"])
    used_letters = sorted(distinct_letters_total)
    print(f"#   distinct alphabet chars across corpus: "
          f"{len(used_letters)} / 26 = {''.join(used_letters)}")
    print()

    target_match = [c for c in yasnas if c["yasna"] == TARGET_YASNA]
    if not target_match:
        print(f"ERROR: Yasna {TARGET_YASNA} not found", file=sys.stderr)
        return 2
    target = target_match[0]
    canon_str = target["letters_26"]
    n_letters = len(canon_str)
    n_verses = target["n_verses"]
    print(f"# Target: Yasna {TARGET_YASNA} (Ahunavaiti Gatha, ch. 1)")
    print(f"#   raw text length    = {len(target['text_raw'])} chars")
    print(f"#   skeleton (a-z)     = {n_letters} chars")
    print(f"#   verses (<DD>)      = {n_verses}")
    print(f"#   distinct skeleton chars = {len(set(canon_str))} / 26")
    if n_letters < 1000:
        print(f"# WARN: target skeleton {n_letters} < 1000 floor",
              file=sys.stderr)
    print()

    # 3) Build peer pool: ALL other yasnas (no length match)
    peers = [c for c in yasnas if c["yasna"] != TARGET_YASNA]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} Avestan yasnas "
          f"(all yasnas except {TARGET_YASNA}; "
          f"NO length matching; F55-family floor = {PEER_AUDIT_FLOOR_F55})")

    if n_peers < PEER_AUDIT_FLOOR_F55:
        print(f"# WARN: peer pool {n_peers} < {PEER_AUDIT_FLOOR_F55} F55 floor",
              file=sys.stderr)

    # 4) Variant audit
    print()
    print("# --- Variant audit (theorem replication on Avestan alphabet) ---")
    av_positions = [
        i for i, ch in enumerate(canon_str)
        if ch in AVESTAN_ALPHABET_SET
    ]
    print(f"#   alphabet positions in canon = {len(av_positions)}")
    if not av_positions:
        print("ERROR: no Avestan-letter positions found", file=sys.stderr)
        return 2

    # For variant substitutions, restrict to letters actually used in
    # the corpus (so we don't substitute "q" or "l" if they never occur).
    used_alphabet = "".join(used_letters)
    print(f"#   substitution alphabet (corpus-attested) = {len(used_alphabet)} letters")

    var_rng = random.Random(43)
    sample_specs: list[tuple[int, str, str]] = []
    while len(sample_specs) < N_VARIANT_SAMPLE:
        pos = var_rng.choice(av_positions)
        repl = var_rng.choice(used_alphabet)
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
    peer_deltas: list[tuple[int, float, int]] = []
    for peer in peers:
        peer_str = peer["letters_26"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_deltas.append((peer["yasna"], d, peer["n_letters"]))
    deltas_only = sorted(d for (_, d, _) in peer_deltas)
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

    closest = sorted(peer_deltas, key=lambda r: r[1])[:5]
    print(f"#   5 closest peers:")
    for (y, d, n_l) in closest:
        print(f"#     Yasna {y:<3d}  n_letters={n_l:<6d}  delta={d:.2f}")

    # 6) Decision
    print()
    print("# --- Decision ---")
    theorem_ok = (var_max <= TAU_HIGH + 1e-9) and (n_above_tau == 0)
    fpr_floor_ok = (peer_min > TAU_HIGH) and (peer_min >= TAU_HIGH * SAFETY_MARGIN)
    pool_ok = n_peers >= PEER_AUDIT_FLOOR_F55

    if theorem_ok and fpr_floor_ok and pool_ok:
        verdict = "PROCEED_TO_PREREG"
        msg = (f"Variant theorem holds (max = {var_max:.2f} <= 2.0); "
               f"peer min = {peer_min:.2f} >= {SAFETY_MARGIN}x safety "
               f"margin; peer pool {n_peers} >= F55-family floor "
               f"{PEER_AUDIT_FLOOR_F55}. Cross-tradition F55 on "
               f"Avestan Yasna 28 is safe to PREREG and run.")
    elif not pool_ok:
        verdict = "BLOCK_PEER_POOL_BELOW_F55_FLOOR"
        msg = (f"Peer pool {n_peers} < F55-family floor "
               f"{PEER_AUDIT_FLOOR_F55}.")
    elif theorem_ok and not fpr_floor_ok:
        verdict = "BLOCK_FPR_RISK"
        msg = (f"Variant theorem OK (max = {var_max:.2f}) but peer_min "
               f"= {peer_min:.2f} below {SAFETY_MARGIN}x safety margin.")
    elif not theorem_ok:
        verdict = "BLOCK_THEOREM_BROKEN"
        msg = (f"Variant theorem FAILED: max variant delta = "
               f"{var_max:.2f} > 2.0 ({n_above_tau} variants above tau).")
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
    out_path = out_dir / "_y28_bigram_sizing.json"
    receipt = {
        "schema": "y28_bigram_sizing_v1",
        "filed_as": "exploratory_diagnostic",
        "purpose": "Sanity check before exp108_F55_y28_bigram PREREG draft",
        "target_yasna": TARGET_YASNA,
        "target_n_verses": n_verses,
        "target_n_letters_skeleton": n_letters,
        "target_n_distinct_letters": len(set(canon_str)),
        "tau_high": TAU_HIGH,
        "safety_margin_x": SAFETY_MARGIN,
        "peer_audit_floor_f55": PEER_AUDIT_FLOOR_F55,
        "alphabet_size_locked": len(AVESTAN_ALPHABET_26),
        "alphabet_size_corpus_attested": len(used_alphabet),
        "alphabet_attested": used_alphabet,
        "alphabet_string_locked": AVESTAN_ALPHABET_26,
        "peer_pool_strategy":
            "all_other_yasna_chapters_no_length_matching"
            "_matches_exp95j_arabic_and_exp106_greek_protocol",
        "n_yasnas_total": len(yasnas),
        "n_peers": n_peers,
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
            "pool_above_f55_floor": pool_ok,
            "five_closest": [
                {"yasna": y, "delta": d, "n_letters": n_l}
                for (y, d, n_l) in closest
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
