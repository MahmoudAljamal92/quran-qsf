"""tools/quran_metrology_challenge.py — Quran-as-reference-standard challenger.

The Quran sets *locked extrema* on a suite of dimensionless features (F48 / F63 /
F64 / F66 / F67 / F68). This tool measures the *same* features on any candidate
text and asks: does the candidate match or beat the Quran's extremum?

If any text scores 5/5 (matches or beats Quran on every feature), the Quran's
distinctive-extremum claim is *operationally falsified* on that test. If most
texts score 0/5 to 2/5, the Quran's extremum is empirically robust.

Usage (CLI):
    python tools/quran_metrology_challenge.py path/to/candidate.txt
    python tools/quran_metrology_challenge.py --label "Sanaa-DAM01" path/to/...

The candidate text should be a multi-verse passage with verses on separate
lines (or with `|` / `.` separators).

Honest scope:
    * The 4 single-text features (p_max, H_EL, C_Omega, F55_safety_per_char)
      need a CHAPTER-sized passage (≥ 5 verses, ≥ 100 letters) to be meaningful.
    * The 1 multi-text feature (F68 RG slope) needs ≥ 5 chapters of similar
      length and is therefore not measured by this single-text tool.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

# ---- Arabic 28-letter skeleton normaliser (matches sanaa_compare.py) ------
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_AR_TATWEEL = "\u0640"
_ARABIC_LETTERS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ARABIC_SET = set(_ARABIC_LETTERS_28)

QURAN_ALPHABET = 28


# ---- Quran-locked target values (from RANKED_FINDINGS F48/F63/F64/F66/F67) ----
QURAN_LOCKED = {
    "p_max": {
        "value": 0.7273,
        "direction": "max",   # higher is more extreme
        "source": "F63 / F64 / F66 — Quran rank 1/12 cross-tradition",
        "tolerance_window_for_match": 0.02,
    },
    "H_EL": {
        "value": 0.9685,      # bits, alphabet=28
        "direction": "min",   # lower is more extreme
        "source": "F63 — lowest H_EL of 11 cross-tradition corpora",
        "tolerance_window_for_match": 0.05,
    },
    "C_Omega": {
        "value": 0.7985,
        "direction": "max",
        "source": "F67 — Quran C_Ω = 1 − H_EL/log₂(28); rank 1/12 with margin 1.36×",
        "tolerance_window_for_match": 0.02,
    },
    "F55_safety_per_char": {
        "value": 0.3202,
        "direction": "max",
        "source": "F66 — peer-pair Δ_min / chapter length; Quran rank 1/5",
        "tolerance_window_for_match": 0.05,
    },
    # F68 RG slope α requires multiple chapters ≥ 32 verses each → not measured here
}


def normalise_arabic(s: str) -> str:
    """28-letter skeleton normaliser. Drops diacritics, hamzas, ta-marbuta,
    folds alif variants. Returns space-separated word string."""
    if not s:
        return ""
    s = s.replace(_AR_TATWEEL, "")
    s = _AR_DIAC.sub("", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = (s.replace("\u0622", "\u0627")
          .replace("\u0623", "\u0627")
          .replace("\u0625", "\u0627")
          .replace("\u0671", "\u0627")
          .replace("\u0649", "\u064a")
          .replace("\u0629", "\u0647"))
    s = s.replace("\u0624", "\u0648").replace("\u0626", "\u064a").replace("\u0621", "")
    keep = _ARABIC_SET | {" ", "\n"}
    s = "".join(c if c in keep else " " for c in s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_verses(raw: str) -> list[str]:
    """Split a candidate passage into verses. Heuristic: split on linefeeds first,
    fall back to '|', then to '.'."""
    parts = [p.strip() for p in raw.splitlines() if p.strip()]
    if len(parts) >= 3:
        return parts
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) >= 3:
        return parts
    parts = [p.strip() for p in raw.split(".") if p.strip()]
    return parts


def bigram_histogram_within_words(text: str) -> dict:
    h: dict = {}
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i + 2]
            h[bg] = h.get(bg, 0) + 1
    return h


def measure(verses: list[str]) -> dict:
    """Compute the 4 single-text Quran-extremum features on a candidate passage."""
    finals = []
    for v in verses:
        n = normalise_arabic(v)
        if n:
            finals.append(n[-1] if n[-1] != " " else (n.rstrip()[-1] if n.rstrip() else None))
    finals = [f for f in finals if f and f in _ARABIC_SET]
    n_finals = len(finals)
    if n_finals == 0:
        return {"error": "no_skeleton_verse_finals", "n_verses": len(verses)}

    # F48 / F63: p_max(end_letter)
    counts: dict = {}
    for f in finals:
        counts[f] = counts.get(f, 0) + 1
    p_max = max(counts.values()) / n_finals

    # F63: H_EL (Shannon entropy of end-letter distribution, in bits)
    H_EL = -sum((c / n_finals) * math.log2(c / n_finals) for c in counts.values() if c > 0)

    # F67: C_Omega = 1 - H_EL / log2(A)
    C_Omega = 1.0 - H_EL / math.log2(QURAN_ALPHABET)

    # F55_safety_per_char: needs a peer pool. We approximate by computing the
    # WITHIN-passage chapter-pair Δ_bigram (verse-pair instead of chapter-pair),
    # divided by median verse-skeleton length. This is a *proxy*; full F55_safety
    # requires a multi-chapter peer pool. For a single-passage challenger, we
    # report the within-passage minimum verse-pair Δ as a lower bound.
    verse_skels = [normalise_arabic(v) for v in verses]
    verse_skels = [s for s in verse_skels if len(s.replace(" ", "")) >= 5]
    pair_deltas = []
    for i in range(len(verse_skels)):
        for j in range(i + 1, len(verse_skels)):
            h_i = bigram_histogram_within_words(verse_skels[i])
            h_j = bigram_histogram_within_words(verse_skels[j])
            keys = set(h_i) | set(h_j)
            d = sum(abs(h_i.get(k, 0) - h_j.get(k, 0)) for k in keys) / 2.0
            pair_deltas.append(d)
    if pair_deltas:
        peer_min_d = min(pair_deltas)
        median_skel_len = sorted(len(s.replace(" ", "")) for s in verse_skels)[len(verse_skels) // 2]
        f55_safety_proxy = peer_min_d / max(1.0, median_skel_len)
    else:
        peer_min_d = 0.0
        median_skel_len = 0
        f55_safety_proxy = 0.0

    return {
        "n_verses": len(verses),
        "n_finals": n_finals,
        "p_max": p_max,
        "H_EL": H_EL,
        "C_Omega": C_Omega,
        "F55_safety_per_char": f55_safety_proxy,
        "_peer_min_pair_delta": peer_min_d,
        "_median_verse_skel_len": median_skel_len,
    }


def challenge(measured: dict, label: str = "candidate") -> dict:
    """Compare measured values against Quran's locked extrema; return scorecard."""
    if "error" in measured:
        return {"label": label, "error": measured["error"], "n_verses": measured.get("n_verses")}

    rows = []
    score = 0
    for feature, lock in QURAN_LOCKED.items():
        c_val = measured[feature]
        q_val = lock["value"]
        direction = lock["direction"]
        if direction == "max":
            beats = c_val >= q_val
            within = abs(c_val - q_val) <= lock["tolerance_window_for_match"]
        else:  # min
            beats = c_val <= q_val
            within = abs(c_val - q_val) <= lock["tolerance_window_for_match"]
        if beats:
            score += 1
        rows.append({
            "feature": feature,
            "candidate": round(c_val, 5),
            "quran_locked": q_val,
            "direction": direction,
            "candidate_more_extreme_or_equal": beats,
            "within_tolerance_match": within,
            "delta": round(c_val - q_val, 5),
            "source": lock["source"],
        })

    return {
        "label": label,
        "n_verses": measured["n_verses"],
        "match_score": f"{score}/{len(QURAN_LOCKED)}",
        "match_score_int": score,
        "n_features_tested": len(QURAN_LOCKED),
        "verdict": _verdict(score, len(QURAN_LOCKED)),
        "rows": rows,
    }


def _verdict(score: int, total: int) -> str:
    if score == 0:
        return "FAR_FROM_QURAN_EXTREMA"
    if score == total:
        return "MATCHES_OR_BEATS_QURAN_ON_ALL_FEATURES_EXTRAORDINARY_CLAIM"
    if score >= total - 1:
        return "VERY_CLOSE_TO_QURAN_EXTREMA"
    if score >= total // 2:
        return "PARTIALLY_QURAN_LIKE"
    return "WEAKLY_QURAN_LIKE"


def _read_input(arg: str) -> str:
    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return arg


def paired_compare(canonical_text: str, candidate_text: str,
                   canonical_label: str = "canonical",
                   candidate_label: str = "candidate") -> dict:
    """Compare two passages directly (e.g. canonical Quran sūrah vs Sanaa
    reconstruction of the same sūrah). For each feature, report:
        canonical value | candidate value | which is more extreme
    Provides a face-to-face metrology test independent of the corpus-median.
    """
    can_v = split_verses(canonical_text)
    cand_v = split_verses(candidate_text)
    can_m = measure(can_v)
    cand_m = measure(cand_v)
    if "error" in can_m or "error" in cand_m:
        return {"error": "measurement_failed", "canonical_err": can_m.get("error"),
                "candidate_err": cand_m.get("error")}

    # Letter-level Δ_bigram between the two normalised passages (F55 axis).
    # Captures internal-letter edits invisible to verse-final rhyme features.
    can_norm = normalise_arabic(canonical_text)
    cand_norm = normalise_arabic(candidate_text)
    h_can = bigram_histogram_within_words(can_norm)
    h_cand = bigram_histogram_within_words(cand_norm)
    keys = set(h_can) | set(h_cand)
    delta_letter_level = sum(abs(h_can.get(k, 0) - h_cand.get(k, 0)) for k in keys) / 2.0
    k_min_letter_level = math.ceil(delta_letter_level / 2.0) if delta_letter_level > 0 else 0

    rows = []
    can_wins = 0
    cand_wins = 0
    for feature, lock in QURAN_LOCKED.items():
        c1 = can_m[feature]
        c2 = cand_m[feature]
        if lock["direction"] == "max":
            if c2 > c1:
                more_extreme = candidate_label
                cand_wins += 1
            elif c1 > c2:
                more_extreme = canonical_label
                can_wins += 1
            else:
                more_extreme = "tie"
        else:  # min
            if c2 < c1:
                more_extreme = candidate_label
                cand_wins += 1
            elif c1 < c2:
                more_extreme = canonical_label
                can_wins += 1
            else:
                more_extreme = "tie"
        rows.append({
            "feature": feature,
            "canonical": round(c1, 5),
            "candidate": round(c2, 5),
            "delta_candidate_minus_canonical": round(c2 - c1, 5),
            "direction_for_extremum": lock["direction"],
            "more_extreme_label": more_extreme,
        })
    return {
        "mode": "paired_comparison",
        "canonical_label": canonical_label,
        "candidate_label": candidate_label,
        "canonical_n_verses": can_m["n_verses"],
        "candidate_n_verses": cand_m["n_verses"],
        "canonical_wins": can_wins,
        "candidate_wins": cand_wins,
        "rows": rows,
        "letter_level": {
            "delta_bigram": delta_letter_level,
            "implied_k_min_letter_edits": k_min_letter_level,
            "skeleton_canonical_length": len(can_norm.replace(" ", "")),
            "skeleton_candidate_length": len(cand_norm.replace(" ", "")),
        },
        "summary": _paired_verdict(can_wins, cand_wins, len(QURAN_LOCKED)),
    }


def _paired_verdict(can: int, cand: int, total: int) -> str:
    if cand > can:
        return f"CANDIDATE_MORE_EXTREME_ON_{cand}_OF_{total}_FEATURES"
    if can > cand:
        return f"CANONICAL_MORE_EXTREME_ON_{can}_OF_{total}_FEATURES"
    return "TIE"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Quran-as-reference-standard challenger.")
    ap.add_argument("text", help="Candidate text — file path or inline string")
    ap.add_argument("--vs", help="Optional canonical text (file or inline) for PAIRED mode")
    ap.add_argument("--label", default="candidate")
    ap.add_argument("--canonical-label", default="canonical")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable")
    args = ap.parse_args(argv)

    raw = _read_input(args.text)

    if args.vs:
        # Paired-comparison mode
        canonical_raw = _read_input(args.vs)
        result = paired_compare(canonical_raw, raw, args.canonical_label, args.label)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if "error" in result:
            print(f"ERROR: {result['error']}")
            return 1
        print(f"\n=== Paired Comparison: {result['canonical_label']} vs {result['candidate_label']} ===")
        print(f"  {result['canonical_label']:<20s}  n_verses = {result['canonical_n_verses']}")
        print(f"  {result['candidate_label']:<20s}  n_verses = {result['candidate_n_verses']}")
        print()
        print(f"  {'Feature':<25s}  {'Canonical':>12s}  {'Candidate':>12s}  {'Δ':>10s}  {'More extreme':>30s}")
        print("  " + "-" * 100)
        for r in result["rows"]:
            d = f"{r['delta_candidate_minus_canonical']:+.5f}"
            print(f"  {r['feature']:<25s}  {r['canonical']:>12.5f}  {r['candidate']:>12.5f}  {d:>10s}  {r['more_extreme_label']:>30s}")
        print()
        print(f"  Summary: {result['summary']}")
        print(f"  Canonical wins: {result['canonical_wins']}/{len(result['rows'])}; "
              f"Candidate wins: {result['candidate_wins']}/{len(result['rows'])}")
        ll = result["letter_level"]
        print()
        print(f"  Letter-level (F55 axis):")
        print(f"    Δ_bigram                  = {ll['delta_bigram']:.2f}")
        print(f"    Implied k_min letter edits = ≥ {ll['implied_k_min_letter_edits']}")
        print(f"    Skeleton lengths           = {ll['skeleton_canonical_length']} vs {ll['skeleton_candidate_length']}")
        if ll["delta_bigram"] == 0 and result["summary"] == "TIE":
            print()
            print(f"  ⚠️  All rhyme features tied AND Δ_bigram = 0 — texts are bigram-identical")
            print(f"     after diacritic strip. Could be: (a) rasm-identical, OR (b) word-reorder")
            print(f"     within verses (F55 permutation-invariance gap — use F70 to disambiguate).")
        elif ll["delta_bigram"] == 0:
            print(f"  ⚠️  Δ_bigram = 0 but rhyme features differ — likely rounding / verse-count diff.")
        return 0

    # Default: corpus-median challenge mode
    verses = split_verses(raw)
    measured = measure(verses)
    report = challenge(measured, args.label)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    if "error" in report:
        print(f"ERROR: {report['error']}")
        return 1

    print(f"\n=== Quran Metrology Challenge: {report['label']} ===")
    print(f"  Verses analysed:  {report['n_verses']}")
    print(f"  Match score:      {report['match_score']}  → {report['verdict']}")
    print()
    print(f"  {'Feature':<25s}  {'Candidate':>12s}  {'Quran (locked)':>15s}  {'Δ':>10s}  {'Beats?':>8s}")
    print("  " + "-" * 80)
    for r in report["rows"]:
        beats = "YES" if r["candidate_more_extreme_or_equal"] else "no"
        d = f"{r['delta']:+.5f}"
        print(f"  {r['feature']:<25s}  {r['candidate']:>12.5f}  {r['quran_locked']:>15.5f}  {d:>10s}  {beats:>8s}")

    print()
    print("  Honest interpretation:")
    if report["match_score_int"] == report["n_features_tested"]:
        print("  >> CANDIDATE MATCHES OR BEATS QURAN ON EVERY MEASURED FEATURE.")
        print("  >> If reproducible on a chapter-sized passage, this would FALSIFY")
        print("  >> the Quran's unique-extremum claim on these axes.")
    elif report["match_score_int"] == 0:
        print("  >> Candidate is far from Quran-extremum on every feature.")
        print("  >> Consistent with the Quran being the rhyme-architecture extremum.")
    else:
        print(f"  >> Candidate matches Quran on {report['match_score_int']} of "
              f"{report['n_features_tested']} features.")

    print()
    print("  Note: F68 RG-slope and full F55_safety (vs peer pool) require multi-")
    print("  chapter input; this single-passage tool reports a within-passage")
    print("  proxy for F55_safety_per_char.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
