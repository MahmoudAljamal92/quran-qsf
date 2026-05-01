"""scripts/_mark1_bigram_sizing.py
====================================
Sanity check before drafting exp106_F55_mark1_bigram PREREG.

Question: does F55's analytic-bound bigram-shift detector (tau = 2.0)
give a clean recall-1 / FPR-0 separation on Greek NT Mark 1, replicating
the Hebrew Psalm 78 result (exp105) in a different language family
(Indo-European vs Northwest Semitic)?

Computes:
1) **Variant audit (theorem)** — analytic delta_bigram for a sample of
   single-Greek-letter substitutions of Mark 1. Theorem predicts max
   <= 2.0 in any alphabet.
2) **Peer audit (FPR floor)** — exact delta_bigram between Mark 1 and
   each of the 259 other Greek NT chapters (no length matching;
   matches the Quran-side exp95j protocol exactly).

Decision rule (PROCEED-to-PREREG):
- variant max <= 2.0 STRICTLY (theorem holds)
- peer min  >  2.0 with safety margin >= 5x  (FPR = 0 plausible)

NO-COMPRESSION-CALL diagnostic; runs in seconds.
"""
from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments.exp104d_F53_mark1.run import (  # noqa: E402
    TARGET_BOOK_NUMBER,
    TARGET_CHAPTER,
    _normalise_greek,
    _load_greek_nt_chapters,
)

# F55 frozen analytic-bound tau (locked at exp95j PREREG)
TAU_HIGH = 2.0
SAFETY_MARGIN = 5.0  # require peer-min / tau >= 5x to PROCEED

# Variant audit: how many variants to sample
N_VARIANT_SAMPLE = 1000

# Greek alphabet for substitutions: 24 lowercase letters
# (after diacritic stripping + sigma fold; the normaliser produces
# medial sigma 'σ' for all sigma forms)
GREEK_ALPHABET_24 = (
    "αβγδεζηθικλμνξοπρστυφχψω"
)


def bigrams_of(s: str) -> Counter:
    """Counter of all consecutive 2-character substrings (raw counts)."""
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    """Delta_bigram = 1/2 * sum_k |c1[k] - c2[k]| (raw counts)."""
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    """Analytic O(1) delta for substitution canon[p] -> new_ch."""
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
    print("# _mark1_bigram_sizing.py  --  sanity for exp106 F55 -> Greek NT Mark 1")
    print()

    # 1) Load Greek NT + locate Mark 1
    chapters = _load_greek_nt_chapters()
    print(f"# Greek NT (OpenGNT v3.3) loaded: {len(chapters)} chapters")
    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK_NUMBER
                    and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        print("ERROR: Mark 1 not found in OpenGNT corpus", file=sys.stderr)
        return 2
    target = target_match[0]
    canon_str = target["letters_24"]  # pure 24-letter skeleton (no spaces; whitelist drops them)
    n_letters = len(canon_str)
    print(f"# Mark 1: {target['n_verses']} verses, "
          f"{n_letters} letter-skeleton chars (Greek-letter whitelist; "
          f"matches exp95j convention)")

    # 2) Build peer pool: ALL Greek NT chapters EXCEPT Mark 1 (no length
    # matching, matches exp95j Arabic-side F55 protocol byte-exact)
    peers = [c for c in chapters
             if not (c["book"] == TARGET_BOOK_NUMBER
                     and c["chapter"] == TARGET_CHAPTER)]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} Greek NT chapters "
          f"(all chapters except target; NO length matching, "
          f"matches exp95j Arabic-side F55 protocol)")

    # 3) Variant audit: sample N_VARIANT_SAMPLE single-letter substitutions
    # The skeleton may include spaces (verse separators); we substitute
    # only at positions where the char is in GREEK_ALPHABET_24.
    print()
    print("# --- Variant audit (theorem replication on Greek alphabet) ---")
    greek_positions = [
        i for i, ch in enumerate(canon_str)
        if ch in GREEK_ALPHABET_24
    ]
    print(f"#   Greek-letter positions in canon = {len(greek_positions)}")
    if not greek_positions:
        print("ERROR: no Greek-letter positions found", file=sys.stderr)
        return 2

    var_rng = random.Random(43)
    sample_specs: list[tuple[int, str, str]] = []
    while len(sample_specs) < N_VARIANT_SAMPLE:
        pos = var_rng.choice(greek_positions)
        repl = var_rng.choice(GREEK_ALPHABET_24)
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

    # 4) Peer audit: full Delta on each of the 259 peer chapters
    print()
    print("# --- Peer audit (FPR floor) ---")
    canon_bigrams = bigrams_of(canon_str)
    peer_deltas: list[tuple[str, str, str, float]] = []
    for peer in peers:
        peer_str = peer["letters_24"]
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_deltas.append((
            str(peer["book"]),
            str(peer["chapter"]),
            peer_str,
            d,
        ))
    deltas_only = sorted([d for (_, _, _, d) in peer_deltas])
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

    closest = sorted(peer_deltas, key=lambda r: r[3])[:5]
    print(f"#   5 closest peers:")
    for (book, chap, _pstr, d) in closest:
        print(f"#     book={book:<20s} ch={chap:<5s}  delta = {d:.2f}")

    # 5) Decision
    print()
    print("# --- Decision ---")
    theorem_ok = (var_max <= TAU_HIGH + 1e-9) and (n_above_tau == 0)
    fpr_floor_ok = (peer_min > TAU_HIGH) and (peer_min >= TAU_HIGH * SAFETY_MARGIN)

    if theorem_ok and fpr_floor_ok:
        verdict = "PROCEED_TO_PREREG"
        msg = (f"Variant theorem holds (max = {var_max:.2f} <= 2.0); "
               f"peer min = {peer_min:.2f} >= {SAFETY_MARGIN}x safety "
               f"margin of tau = 2.0. Cross-tradition F55 on Greek NT "
               f"Mark 1 is safe to PREREG and run.")
    elif theorem_ok and not fpr_floor_ok:
        verdict = "BLOCK_FPR_RISK"
        msg = (f"Variant theorem OK (max = {var_max:.2f}) but peer_min "
               f"= {peer_min:.2f} below {SAFETY_MARGIN}x safety margin "
               f"of tau = 2.0.")
    elif not theorem_ok:
        verdict = "BLOCK_THEOREM_BROKEN"
        msg = (f"Variant theorem FAILED on Greek: max variant delta = "
               f"{var_max:.2f} > 2.0 ({n_above_tau} variants above tau). "
               f"Unexpected; investigate before any PREREG.")
    else:
        verdict = "BLOCK_UNKNOWN"
        msg = "Unhandled branch."

    print(f"# verdict: {verdict}")
    print(f"# {msg}")
    print()
    print(f"# wall-time: {time.time() - t0:.1f}s")

    # 6) Persist receipt under results/auxiliary/
    out_dir = _ROOT / "results" / "auxiliary"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "_mark1_bigram_sizing.json"
    receipt = {
        "schema": "mark1_bigram_sizing_v1",
        "filed_as": "exploratory_diagnostic",
        "purpose": "Sanity check before exp106_F55_mark1_bigram PREREG draft",
        "target_book_number": TARGET_BOOK_NUMBER,
        "target_chapter": TARGET_CHAPTER,
        "target_n_verses": target["n_verses"],
        "target_n_letters_skeleton": n_letters,
        "target_n_chars_with_spaces": len(canon_str),
        "tau_high": TAU_HIGH,
        "safety_margin_x": SAFETY_MARGIN,
        "peer_pool_strategy":
            "all_other_greek_nt_chapters_no_length_matching"
            "_matches_exp95j_arabic_protocol",
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
                {"book": b, "chapter": c, "delta": d}
                for (b, c, _ps, d) in closest
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
