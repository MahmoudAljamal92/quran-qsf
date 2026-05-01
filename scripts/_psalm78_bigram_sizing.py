"""scripts/_psalm78_bigram_sizing.py
====================================
Sanity check before drafting exp105_F55_psalm78_bigram PREREG.

Question: does F55's analytic-bound bigram-shift detector (tau = 2.0)
give a clean recall-1 / FPR-0 separation on Hebrew Psalm 78 the same
way it did on Quran V1?

Computes:
1) **Variant audit (theorem replication)** — analytic delta_bigram for
   a sample of single-Hebrew-consonant variants of Psalm 78.
   Theorem predicts max <= 2.0 in any alphabet, because substituting
   one consonant changes at most 4 raw bigram counts (2 lost on the
   left+right neighbours, 2 gained).
2) **Peer audit (FPR floor)** — exact delta_bigram between Psalm 78
   and each of the 114 narrative-Hebrew chapters in the locked
   exp104c +/- 30 % length window.

Decision rule (PROCEED-to-PREREG):
- variant max <= 2.0 STRICTLY (theorem holds)
- peer min  >  2.0 with safety margin >= 5x  (FPR = 0 plausible)

This is a NO-COMPRESSION-CALL sanity check (analytic only); should run
in a few seconds.

No PREREG; no receipt under results/; this script writes a single JSON
under results/auxiliary/_psalm78_bigram_sizing.json for traceability,
but is filed as an exploratory diagnostic, not an experiment.
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

from experiments.exp104_F53_tanakh_pilot.run import (  # noqa: E402
    HEBREW_CONS_22,
    SEED,
    LENGTH_MATCH_FRAC,
    PEER_BOOKS,
    TARGET_N_PEERS,
    PEER_AUDIT_FLOOR,
    _hebrew_skeleton,
    _hebrew_skeleton_with_spaces,
    _load_tanakh_chapters,
)

TARGET_BOOK = "תהלים"  # Psalms
TARGET_CHAPTER = "עח"  # Psalm 78 (ayin-chet = 70+8)

# F55 frozen analytic-bound tau (locked at exp95j PREREG)
TAU_HIGH = 2.0
SAFETY_MARGIN = 5.0  # require peer-min / tau >= 5x to PROCEED

# Variant audit: how many variants to sample (full enumeration also fine)
N_VARIANT_SAMPLE = 500


# ---- Bigram primitives (byte-for-byte aligned with exp95j) ------------

def bigrams_of(s: str) -> Counter:
    """Counter of all consecutive 2-character substrings (raw counts)."""
    return Counter(s[i:i + 2] for i in range(len(s) - 1))


def bigram_l1_div2(c1: Counter, c2: Counter) -> float:
    """Delta_bigram = 1/2 * sum_k |c1[k] - c2[k]|  (in raw bigram counts)."""
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) - c2.get(k, 0)) for k in keys)


def variant_delta_analytic(canon: str, p: int, new_ch: str) -> float:
    """Analytic delta for substitution canon[p] -> new_ch. O(1)."""
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


# ---- Driver ------------------------------------------------------------

def main() -> int:
    t0 = time.time()
    print("# _psalm78_bigram_sizing.py  --  sanity for exp105 F55 -> Hebrew Psalm 78")
    print()

    # 1) Load Tanakh + locate Psalm 78
    chapters = _load_tanakh_chapters()
    print(f"# Tanakh loaded: {len(chapters)} chapters total")
    target_match = [c for c in chapters
                    if c["book"] == TARGET_BOOK and c["chapter"] == TARGET_CHAPTER]
    if not target_match:
        print("ERROR: Psalm 78 not found in WLC", file=sys.stderr)
        return 2
    target = target_match[0]
    canon_skel_with_spaces = _hebrew_skeleton_with_spaces(target["verses_raw"])
    canon_skel_no_spaces = target["letters_22"]
    print(f"# Psalm 78: {target['n_verses']} verses, "
          f"{len(canon_skel_no_spaces)} consonant-only letters, "
          f"{len(canon_skel_with_spaces)} chars with verse-spaces.")

    # F55 protocol uses the WITH-SPACE skeleton (matches exp95j Arabic
    # protocol where peers are letters_28(" ".join(u.verses))).
    canon_str = canon_skel_with_spaces

    # 2) Build the same 114-chapter peer pool exp104c used
    target_len_no_spaces = len(canon_skel_no_spaces)
    lo = int(target_len_no_spaces * (1 - LENGTH_MATCH_FRAC))
    hi = int(target_len_no_spaces * (1 + LENGTH_MATCH_FRAC))
    peers_raw = [c for c in chapters
                 if c["book"] in PEER_BOOKS
                 and lo <= c["n_letters"] <= hi]
    rng = random.Random(SEED)
    rng.shuffle(peers_raw)
    peers = peers_raw[:TARGET_N_PEERS]
    n_peers = len(peers)
    print(f"# Peer pool: {n_peers} narrative-Hebrew chapters in [{lo}, {hi}] "
          f"consonant-only letters (locked +/- {LENGTH_MATCH_FRAC:.0%} window)")
    if n_peers < PEER_AUDIT_FLOOR:
        print(f"# WARN: peer pool below floor ({n_peers} < {PEER_AUDIT_FLOOR})")

    # 3) Variant audit: sample N_VARIANT_SAMPLE single-letter variants of
    # Psalm 78 (full enumeration would be ~2384 * 21 = 50k, too noisy).
    # Note: variants substitute consonants only, so we work over the
    # no-space skeleton to pick positions, but the analytic delta is
    # computed on the WITH-SPACE skeleton (the F55 protocol skeleton)
    # by mapping no-space-pos -> with-space-pos.
    print()
    print("# --- Variant audit (theorem replication on Hebrew) ---")
    pos_no_space_to_with = []
    j = 0
    for i, ch in enumerate(canon_skel_with_spaces):
        if ch in HEBREW_CONS_22:
            pos_no_space_to_with.append(i)
            j += 1
    assert j == len(canon_skel_no_spaces), \
        f"position mapping inconsistent: {j} vs {len(canon_skel_no_spaces)}"

    var_rng = random.Random(SEED + 1)
    cons_list = list(HEBREW_CONS_22)
    n_letters = len(canon_skel_no_spaces)
    sample_specs: list[tuple[int, str, str]] = []
    while len(sample_specs) < N_VARIANT_SAMPLE:
        p_no = var_rng.randrange(n_letters)
        repl = var_rng.choice(cons_list)
        old_ch = canon_skel_no_spaces[p_no]
        if repl == old_ch:
            continue
        sample_specs.append((p_no, old_ch, repl))

    var_deltas: list[float] = []
    for (p_no, _old, repl) in sample_specs:
        p_with = pos_no_space_to_with[p_no]
        d = variant_delta_analytic(canon_str, p_with, repl)
        var_deltas.append(d)
    var_max = max(var_deltas)
    var_min = min(var_deltas)
    var_mean = sum(var_deltas) / len(var_deltas)
    n_zero = sum(1 for d in var_deltas if d == 0.0)
    n_above_tau = sum(1 for d in var_deltas if d > TAU_HIGH)
    print(f"#   N_sampled        = {len(var_deltas)}")
    print(f"#   variant_delta_min  = {var_min:.4f}")
    print(f"#   variant_delta_mean = {var_mean:.4f}")
    print(f"#   variant_delta_max  = {var_max:.4f}")
    print(f"#   n_zero_delta       = {n_zero}  (substitutions whose "
          f"left+right bigrams happen to coincide before/after)")
    print(f"#   n_above_tau (=2.0) = {n_above_tau}  (theorem violation if > 0)")

    # 4) Peer audit: full Delta on each of the 114 peers.
    print()
    print("# --- Peer audit (FPR floor) ---")
    canon_bigrams = bigrams_of(canon_str)
    peer_deltas: list[tuple[str, str, float]] = []
    for peer in peers:
        peer_str = _hebrew_skeleton_with_spaces(peer["verses_raw"])
        peer_bigrams = bigrams_of(peer_str)
        d = bigram_l1_div2(canon_bigrams, peer_bigrams)
        peer_deltas.append((peer["book"], peer["chapter"], d))
    deltas_only = [d for (_, _, d) in peer_deltas]
    deltas_only.sort()
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

    # Print the 5 closest peers (potential FPR risks)
    closest = sorted(peer_deltas, key=lambda r: r[2])[:5]
    print(f"#   5 closest peers (raw bigram delta):")
    for (book, chap, d) in closest:
        print(f"#     {book:<12s} {chap:<6s}  delta = {d:.2f}")

    # 5) Decision
    print()
    print("# --- Decision ---")
    theorem_ok = (var_max <= TAU_HIGH + 1e-9) and (n_above_tau == 0)
    fpr_floor_ok = (peer_min > TAU_HIGH) and (peer_min >= TAU_HIGH * SAFETY_MARGIN)

    if theorem_ok and fpr_floor_ok:
        verdict = "PROCEED_TO_PREREG"
        msg = (f"Variant theorem holds (max = {var_max:.2f} <= 2.0); "
               f"peer min = {peer_min:.2f} >= {SAFETY_MARGIN}x safety margin "
               f"of tau = 2.0. Cross-tradition F55 on Hebrew Psalm 78 is "
               f"safe to PREREG and run.")
    elif theorem_ok and not fpr_floor_ok:
        verdict = "BLOCK_FPR_RISK"
        msg = (f"Variant theorem OK (max = {var_max:.2f}) but peer_min = "
               f"{peer_min:.2f} below {SAFETY_MARGIN}x safety margin of "
               f"tau = 2.0. Real Hebrew chapters too close to detection "
               f"threshold; F55 cross-tradition would likely fail FPR.")
    elif not theorem_ok:
        verdict = "BLOCK_THEOREM_BROKEN"
        msg = (f"Variant theorem FAILED on Hebrew: max variant delta = "
               f"{var_max:.2f} > 2.0  ({n_above_tau} variants above tau). "
               f"This would be unexpected and worth investigating before "
               f"any PREREG.")
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
    out_path = out_dir / "_psalm78_bigram_sizing.json"
    receipt = {
        "schema": "psalm78_bigram_sizing_v1",
        "filed_as": "exploratory_diagnostic",
        "purpose": "Sanity check before exp105_F55_psalm78_bigram PREREG draft",
        "target_book": TARGET_BOOK,
        "target_chapter": TARGET_CHAPTER,
        "target_n_verses": target["n_verses"],
        "target_n_letters_22": len(canon_skel_no_spaces),
        "target_n_chars_with_spaces": len(canon_skel_with_spaces),
        "tau_high": TAU_HIGH,
        "safety_margin_x": SAFETY_MARGIN,
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
            "length_window": [lo, hi],
            "min": peer_min,
            "p5": peer_p5,
            "median": peer_median,
            "mean": peer_mean,
            "max": peer_max,
            "min_over_tau_ratio": peer_min / TAU_HIGH,
            "fpr_floor_ok": fpr_floor_ok,
            "five_closest": [
                {"book": b, "chapter": c, "delta": d}
                for (b, c, d) in closest
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
