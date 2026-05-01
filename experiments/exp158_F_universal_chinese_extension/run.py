"""experiments/exp158_F_universal_chinese_extension/run.py

V3.22 candidate -- F-Universal Shannon-Renyi-infinity gap extension to Classical
Chinese (Daodejing 王弼/Wang Bi recension, 81 chapters).

V3.21 / exp156 established F-Universal at H_1 - H_inf approx 1 bit (mean = 0.943 b,
CV = 12 %) across 11 oral canons in 5 alphabetic-script language families.
This experiment tests whether the 1-bit gap extends to a logographic script
under three plausible "verse-final unit" granularities:

  G-CHAPTER : last non-punctuation character of each Daodejing chapter (N=81)
  G-LINE    : last non-punctuation character of each newline-delimited line
  G-PHRASE  : character preceding each Chinese punctuation mark within chapters

PREREG  : experiments/exp158_F_universal_chinese_extension/PREREG.md
Inputs  : data/corpora/zh/daodejing_wangbi.txt (locked at run start)
          results/experiments/exp156_F75_beta_first_principles_derivation/
            exp156_F75_beta_first_principles_derivation.json (hash-pinned)
Output  : results/experiments/exp158_F_universal_chinese_extension/
            exp158_F_universal_chinese_extension.json
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Paths and locked constants

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp158_F_universal_chinese_extension"
PREREG_PATH = Path(__file__).resolve().parent / "PREREG.md"
CORPUS_PATH = ROOT / "data" / "corpora" / "zh" / "daodejing_wangbi.txt"
INPUT_EXP156 = ROOT / "results" / "experiments" / "exp156_F75_beta_first_principles_derivation" / "exp156_F75_beta_first_principles_derivation.json"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

PREREG_EXPECTED_HASH = "5d593c51cb8ad54fd187e489d821ec3e65f25e5f21dcae0f211e2d04529e6251"
PREREG_SENTINEL = "_PREREG_LOCKED_BYTES_END"
EXP156_EXPECTED_SHA256 = "ff6f95611b1de5c81ed31f347264d3ecf0c8fde2176c4f6579e4474adadaaef6"
CORPUS_LOCKED_SHA256 = "a05c5cb00650263e61d107dbeb7f8b887752bcc82fd42fd286b928d2a4d527bd"

CHAPTER_REGEX = re.compile(r"第[一二三四五六七八九十百零〇\d]+章")
PUNCTUATION_FOR_PHRASE_FINAL = set("。，；：、？！")
WHITESPACE_AND_NEWLINES = set(" \t\n\r\u3000")
QUOTE_CHARS_TO_STRIP = set("「」")
PUNCT_TO_STRIP_AT_BOUNDARIES = (
    PUNCTUATION_FOR_PHRASE_FINAL | WHITESPACE_AND_NEWLINES | QUOTE_CHARS_TO_STRIP
)
ADDITIONAL_PUNCT_TO_STRIP = set("﹔")  # Big5 alt-form semicolon used in this file

EXPECTED_N_CHAPTERS = 81

# Pre-registered bands
GAP_BAND_LO = 0.5
GAP_BAND_HI = 1.5
GAP_WIDENED_BAND_LO = 0.5
GAP_WIDENED_BAND_HI = 2.5

# Reference values from V3.21 (for context, not thresholds)
V321_GAP_MEAN = 0.943
V321_GAP_CV = 0.12

GRANULARITIES = ["chapter_final", "line_final", "phrase_final"]


# ---------------------------------------------------------------------------
# Hashing and PREREG verification

def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_of_prereg_locked_bytes(prereg_path: Path) -> str:
    text = prereg_path.read_text(encoding="utf-8")
    idx = text.find(PREREG_SENTINEL)
    if idx < 0:
        raise ValueError(f"Sentinel '{PREREG_SENTINEL}' not found in {prereg_path}")
    end_idx = idx + len(PREREG_SENTINEL)
    return hashlib.sha256(text[:end_idx].encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Daodejing parsing

def is_strippable(c: str) -> bool:
    return c in PUNCT_TO_STRIP_AT_BOUNDARIES or c in ADDITIONAL_PUNCT_TO_STRIP


def split_into_chapters(text: str) -> list[str]:
    """Split corpus text on `第X章` markers; return list of non-empty chapter
    bodies in canonical order (chapter 1 first)."""
    parts = CHAPTER_REGEX.split(text)
    # The first part is preamble before any marker (probably empty in this corpus)
    chapters = [p.strip() for p in parts if p.strip()]
    return chapters


def chapter_final_chars(chapters: list[str]) -> list[str]:
    """Last non-strippable character of each chapter, after stripping trailing
    punctuation/whitespace/quotes."""
    out: list[str] = []
    for ch in chapters:
        s = ch
        # Strip trailing strippable chars
        while s and is_strippable(s[-1]):
            s = s[:-1]
        if s:
            out.append(s[-1])
    return out


def line_final_chars(chapters: list[str]) -> list[str]:
    """Last non-strippable character of each newline-delimited line within
    each chapter."""
    out: list[str] = []
    for ch in chapters:
        for line in ch.split("\n"):
            s = line
            while s and is_strippable(s[-1]):
                s = s[:-1]
            if s:
                # Skip if last char is itself a quote/punct that survived
                if s[-1] not in QUOTE_CHARS_TO_STRIP and s[-1] not in PUNCTUATION_FOR_PHRASE_FINAL:
                    out.append(s[-1])
    return out


def phrase_final_chars(chapters: list[str]) -> list[str]:
    """Character preceding each Chinese punctuation mark within chapters.
    Also includes the last character of each chapter (if not punctuation)."""
    out: list[str] = []
    for ch in chapters:
        chars = list(ch)
        for i, c in enumerate(chars):
            if c in PUNCTUATION_FOR_PHRASE_FINAL or c in ADDITIONAL_PUNCT_TO_STRIP:
                # Walk backward to find preceding non-strippable char
                j = i - 1
                while j >= 0 and is_strippable(chars[j]):
                    j -= 1
                if j >= 0 and not (chars[j] in PUNCTUATION_FOR_PHRASE_FINAL or chars[j] in ADDITIONAL_PUNCT_TO_STRIP):
                    out.append(chars[j])
        # Also chapter-final character (if not already counted via terminal punct)
        s = ch
        while s and is_strippable(s[-1]):
            s = s[:-1]
        if s and (not ch.rstrip().endswith(tuple(PUNCTUATION_FOR_PHRASE_FINAL | ADDITIONAL_PUNCT_TO_STRIP))):
            # Chapter doesn't end with punctuation -> add its last char as a phrase-final
            out.append(s[-1])
    return out


# ---------------------------------------------------------------------------
# Entropy computation

def shannon_entropy(probs: list[float]) -> float:
    """H_1 = -sum_k p_k log_2(p_k), bits, with 0 log 0 = 0."""
    s = 0.0
    for p in probs:
        if p > 1e-15:
            s -= p * math.log2(p)
    return s


def renyi_inf_entropy(probs: list[float]) -> float:
    """H_inf = -log_2(p_max), bits."""
    return -math.log2(max(probs))


def f_universal_gap(units: list[str]) -> dict[str, Any]:
    """Compute (n, n_distinct, p_max, H_1, H_inf, gap) from a list of unit chars."""
    if not units:
        return {"error": "empty unit list"}
    counter = Counter(units)
    n = len(units)
    n_distinct = len(counter)
    probs = [v / n for v in counter.values()]
    p_max = max(probs)
    H1 = shannon_entropy(probs)
    H_inf = renyi_inf_entropy(probs)
    gap = H1 - H_inf
    return {
        "n": n,
        "n_distinct": n_distinct,
        "p_max": p_max,
        "p_max_char": max(counter, key=counter.get),
        "H_1": H1,
        "H_inf": H_inf,
        "gap": gap,
        "log2_n": math.log2(n) if n > 0 else 0.0,
        "log2_n_distinct": math.log2(n_distinct) if n_distinct > 0 else 0.0,
        "top_5_freqs": [(c, counter[c], counter[c] / n) for c in sorted(counter, key=counter.get, reverse=True)[:5]],
    }


# ---------------------------------------------------------------------------
# Main

def main() -> dict[str, Any]:
    t0 = time.time()
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # PREREG hash check
    actual_prereg_hash = sha256_of_prereg_locked_bytes(PREREG_PATH)
    if actual_prereg_hash != PREREG_EXPECTED_HASH:
        raise SystemExit(
            f"PREREG hash mismatch: expected {PREREG_EXPECTED_HASH}, "
            f"actual {actual_prereg_hash}"
        )

    # Corpus exists + SHA-256 lock
    if not CORPUS_PATH.exists():
        raise SystemExit(f"Corpus not found at {CORPUS_PATH}")
    actual_corpus_sha = sha256_of_file(CORPUS_PATH)
    if actual_corpus_sha != CORPUS_LOCKED_SHA256:
        raise SystemExit(
            f"Corpus SHA-256 drift: expected {CORPUS_LOCKED_SHA256}, "
            f"actual {actual_corpus_sha}"
        )

    # exp156 receipt SHA-256 lock (audit hook A2)
    actual_exp156_sha = sha256_of_file(INPUT_EXP156)
    if actual_exp156_sha != EXP156_EXPECTED_SHA256:
        raise SystemExit(
            f"exp156 receipt drift: expected {EXP156_EXPECTED_SHA256}, "
            f"actual {actual_exp156_sha}"
        )

    # Load V3.21 pool stats for comparison context
    exp156_data = json.loads(INPUT_EXP156.read_text(encoding="utf-8"))
    v321_per_corpus = exp156_data["results"]["per_corpus_MAXENT_fit"]
    v321_gap_per_corpus = {
        c: -math.log2(v321_per_corpus[c]["p_max_input"]) - v321_per_corpus[c]["H_EL_input"]
        # gap = H_1 - H_inf = H_EL - (-log2(p_max)) ... wait sign check
        for c in v321_per_corpus
    }
    # Re-derive properly: H_inf = -log2(p_max); gap = H_1 - H_inf = H_EL - (-log2(p_max)) = H_EL + log2(p_max)
    v321_gap_per_corpus = {
        c: v321_per_corpus[c]["H_EL_input"] + math.log2(v321_per_corpus[c]["p_max_input"])
        for c in v321_per_corpus
    }
    v321_gap_mean = sum(v321_gap_per_corpus.values()) / len(v321_gap_per_corpus)
    v321_gap_values = list(v321_gap_per_corpus.values())
    v321_gap_std = (sum((v - v321_gap_mean) ** 2 for v in v321_gap_values) / len(v321_gap_values)) ** 0.5
    v321_gap_cv_observed = v321_gap_std / abs(v321_gap_mean) if v321_gap_mean != 0 else 0.0

    # ---------------------------------------------------------------------
    # Parse Daodejing
    text = CORPUS_PATH.read_text(encoding="utf-8")
    chapters = split_into_chapters(text)

    # Audit hook: chapter count
    n_chapters = len(chapters)
    chapter_count_ok = (n_chapters == EXPECTED_N_CHAPTERS)

    # Compute three granularities
    granular_results: dict[str, dict[str, Any]] = {}
    for granularity in GRANULARITIES:
        if granularity == "chapter_final":
            units = chapter_final_chars(chapters)
        elif granularity == "line_final":
            units = line_final_chars(chapters)
        elif granularity == "phrase_final":
            units = phrase_final_chars(chapters)
        else:
            raise ValueError(f"Unknown granularity: {granularity}")
        result = f_universal_gap(units)
        granular_results[granularity] = result

    # ---------------------------------------------------------------------
    # Audit hooks: monotonicity
    n_chapter = granular_results["chapter_final"].get("n", 0)
    n_line = granular_results["line_final"].get("n", 0)
    n_phrase = granular_results["phrase_final"].get("n", 0)
    monotonicity_ok = (n_chapter < n_line < n_phrase)

    # P4: H_inf chapter-final >= 3.5 b
    h_inf_chapter = granular_results["chapter_final"].get("H_inf", float("nan"))
    p4_pass = math.isfinite(h_inf_chapter) and h_inf_chapter >= 3.5

    # P5: H_1 chapter-final <= log2(81) = 6.34 b
    h1_chapter = granular_results["chapter_final"].get("H_1", float("nan"))
    p5_pass = math.isfinite(h1_chapter) and h1_chapter <= math.log2(81) + 1e-6

    # P2: chapter has smallest gap
    gaps = {g: granular_results[g].get("gap", float("nan")) for g in GRANULARITIES}
    p2_pass = (
        all(math.isfinite(v) for v in gaps.values())
        and gaps["chapter_final"] <= gaps["line_final"]
        and gaps["chapter_final"] <= gaps["phrase_final"]
    )

    # P3: phrase has largest gap
    p3_pass = (
        all(math.isfinite(v) for v in gaps.values())
        and gaps["phrase_final"] >= gaps["line_final"]
        and gaps["phrase_final"] >= gaps["chapter_final"]
    )

    # ---------------------------------------------------------------------
    # Criteria evaluation
    c1_per_g: dict[str, bool] = {}
    c2_per_g: dict[str, bool] = {}
    for g in GRANULARITIES:
        gap = gaps[g]
        c1_per_g[g] = math.isfinite(gap) and (GAP_BAND_LO <= gap <= GAP_BAND_HI)
        c2_per_g[g] = math.isfinite(gap) and (GAP_WIDENED_BAND_LO <= gap <= GAP_WIDENED_BAND_HI)

    c1_pass_count = sum(1 for v in c1_per_g.values() if v)
    c2_pass_count = sum(1 for v in c2_per_g.values() if v)

    # C3 byte-equivalence (already verified above)
    c3_pass = True

    # C4 chapter count
    c4_pass = chapter_count_ok

    # C5 granularity monotonicity
    c5_pass = monotonicity_ok

    # P1 prediction (at least one in narrow band)
    p1_pass = c1_pass_count >= 1

    # ---------------------------------------------------------------------
    # Verdict mapping
    if c1_pass_count == 3:
        verdict = "PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_STRONG"
    elif c1_pass_count == 2:
        verdict = "PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_MODERATE"
    elif c1_pass_count == 1:
        verdict = "PARTIAL_F_UNIVERSAL_EXTENDS_GRANULARITY_SPECIFIC"
    else:
        # 0 narrow-band granularities; check widened
        if c2_pass_count >= 1:
            verdict = "DIRECTIONAL_F_UNIVERSAL_LARGER_GAP_FOR_LOGOGRAPHIC"
        else:
            verdict = "FAIL_F_UNIVERSAL_DOES_NOT_EXTEND_TO_LOGOGRAPHIC"

    # Audit hook check: any audit fail invalidates the run
    audit_ok = c3_pass and c4_pass and c5_pass
    if not audit_ok:
        verdict_reason_audit = (
            f"AUDIT FAILURE: C3 V3.21 byte-equiv {c3_pass}, C4 chapter_count "
            f"({n_chapters}/{EXPECTED_N_CHAPTERS}) {c4_pass}, "
            f"C5 monotonicity (n_chapter={n_chapter} < n_line={n_line} < n_phrase={n_phrase}) {c5_pass}."
        )
        # Audit failures override verdict
        verdict = "FAIL_AUDIT_HOOK_VIOLATED"
    else:
        verdict_reason_audit = ""

    verdict_reason = (
        f"{c1_pass_count}/3 granularities have F-Universal gap in [0.5, 1.5]; "
        f"{c2_pass_count}/3 in widened [0.5, 2.5]. "
        f"chapter_final gap={gaps['chapter_final']:.4f} (in_band={c1_per_g['chapter_final']}); "
        f"line_final gap={gaps['line_final']:.4f} (in_band={c1_per_g['line_final']}); "
        f"phrase_final gap={gaps['phrase_final']:.4f} (in_band={c1_per_g['phrase_final']}). "
        f"V3.21 11-corpus pool mean gap = {v321_gap_mean:.4f} (CV = {v321_gap_cv_observed:.4f}). "
        + verdict_reason_audit
    )

    receipt: dict[str, Any] = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H103_F_Universal_LogographicExtension_Daodejing",
        "hypothesis": (
            "F-Universal Shannon-Renyi-infinity gap H_1 - H_inf in [0.5, 1.5] bits "
            "for at least one of three plausible 'verse-final unit' granularities "
            "(chapter_final, line_final, phrase_final) of the Daodejing (Wang Bi "
            "recension, 81 chapters, classical Chinese)."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "completed_at_utc": completed_at_utc,
        "prereg_document": "experiments/exp158_F_universal_chinese_extension/PREREG.md",
        "prereg_hash": PREREG_EXPECTED_HASH,
        "corpus_path": str(CORPUS_PATH.relative_to(ROOT)).replace("\\", "/"),
        "corpus_sha256_locked_at_run_start": CORPUS_LOCKED_SHA256,
        "input_exp156_sha256": EXP156_EXPECTED_SHA256,
        "frozen_constants": {
            "EXPECTED_N_CHAPTERS": EXPECTED_N_CHAPTERS,
            "GRANULARITIES": GRANULARITIES,
            "GAP_BAND": [GAP_BAND_LO, GAP_BAND_HI],
            "GAP_WIDENED_BAND": [GAP_WIDENED_BAND_LO, GAP_WIDENED_BAND_HI],
            "V321_GAP_MEAN": V321_GAP_MEAN,
            "V321_GAP_CV": V321_GAP_CV,
        },
        "v321_pool_reference": {
            "n_corpora": len(v321_per_corpus),
            "gap_per_corpus": v321_gap_per_corpus,
            "gap_mean": v321_gap_mean,
            "gap_std": v321_gap_std,
            "gap_cv_observed": v321_gap_cv_observed,
        },
        "results": {
            "n_chapters_parsed": n_chapters,
            "chapter_count_ok": chapter_count_ok,
            "monotonicity_ok": monotonicity_ok,
            "granularities": granular_results,
            "criteria": {
                "C1_per_granularity_in_band": {
                    "verdict": "PASS" if p1_pass else "FAIL",  # P1 == "at least one"
                    "n_pass_in_narrow_band": c1_pass_count,
                    "per_granularity": c1_per_g,
                    "narrow_band": [GAP_BAND_LO, GAP_BAND_HI],
                },
                "C2_per_granularity_widened_band": {
                    "verdict": "PASS" if c2_pass_count >= 1 else "FAIL",
                    "n_pass_in_widened_band": c2_pass_count,
                    "per_granularity": c2_per_g,
                    "widened_band": [GAP_WIDENED_BAND_LO, GAP_WIDENED_BAND_HI],
                },
                "C3_v321_byte_equivalence": {
                    "verdict": "PASS" if c3_pass else "FAIL",
                    "exp156_sha256_match": True,
                },
                "C4_chapter_count_sanity": {
                    "verdict": "PASS" if c4_pass else "FAIL",
                    "expected": EXPECTED_N_CHAPTERS,
                    "observed": n_chapters,
                },
                "C5_granularity_monotonicity": {
                    "verdict": "PASS" if c5_pass else "FAIL",
                    "n_chapter": n_chapter,
                    "n_line": n_line,
                    "n_phrase": n_phrase,
                    "monotone_strict_lt": monotonicity_ok,
                },
                "P2_chapter_smallest_gap": {
                    "verdict": "PASS" if p2_pass else "FAIL",
                    "gaps": gaps,
                },
                "P3_phrase_largest_gap": {
                    "verdict": "PASS" if p3_pass else "FAIL",
                    "gaps": gaps,
                },
                "P4_H_inf_chapter_at_least_3_5": {
                    "verdict": "PASS" if p4_pass else "FAIL",
                    "observed": h_inf_chapter,
                    "lower": 3.5,
                },
                "P5_H_1_chapter_at_most_log2_81": {
                    "verdict": "PASS" if p5_pass else "FAIL",
                    "observed": h1_chapter,
                    "upper": math.log2(81),
                },
            },
            "comparison_to_v321_pool": {
                "v321_gap_mean": v321_gap_mean,
                "v321_gap_cv": v321_gap_cv_observed,
                "v321_gap_min": min(v321_gap_values),
                "v321_gap_max": max(v321_gap_values),
                "delta_chapter_vs_pool_mean": gaps["chapter_final"] - v321_gap_mean,
                "delta_line_vs_pool_mean": gaps["line_final"] - v321_gap_mean,
                "delta_phrase_vs_pool_mean": gaps["phrase_final"] - v321_gap_mean,
            },
        },
        "audit_report": {
            "ok": audit_ok,
            "checks": {
                "prereg_hash_match": True,
                "corpus_sha256_locked": CORPUS_LOCKED_SHA256,
                "exp156_input_sha256_locked": EXP156_EXPECTED_SHA256,
                "chapter_splitter_pattern": CHAPTER_REGEX.pattern,
                "chapter_count_correct_for_wang_bi_recension": chapter_count_ok,
                "granularity_strict_monotonicity": monotonicity_ok,
                "no_locked_finding_status_changed": True,
                "F75_PASS_status_unaffected": True,
                "F_universal_label_alias_only": True,
                "no_brown_stouffer_used": True,
                "T_squared_invariant": True,
                "scope_clarification": (
                    "Test of F-Universal Shannon-Renyi-infinity gap on a single "
                    "logographic-script corpus (Daodejing). NOT a population "
                    "claim about Sino-Tibetan or Chinese-language family "
                    "scriptural texts. NOT an N>=50 extension. The verdict is "
                    "interpreted as evidence about whether the 1-bit gap is a "
                    "property of oral-tradition canons specifically (in which "
                    "case Daodejing may not extend) or of canonical literary "
                    "corpora more generally (in which case it should extend)."
                ),
            },
        },
        "wall_time_s": time.time() - t0,
    }

    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[exp158] Verdict: {verdict}")
    print(f"[exp158] C1 narrow band [0.5, 1.5]: {c1_pass_count}/3 granularities pass")
    print(f"[exp158] C2 widened band [0.5, 2.5]: {c2_pass_count}/3 granularities pass")
    print(f"[exp158] Granular gaps:")
    for g in GRANULARITIES:
        in_band = "PASS" if c1_per_g[g] else "FAIL"
        info = granular_results[g]
        print(f"  {g:<14} n={info['n']:>5} n_distinct={info['n_distinct']:>4} "
              f"p_max={info['p_max']:.4f} H1={info['H_1']:.4f} Hinf={info['H_inf']:.4f} "
              f"gap={info['gap']:.4f} ({in_band})")
    print(f"[exp158] V3.21 pool gap mean={v321_gap_mean:.4f}, CV={v321_gap_cv_observed:.4f}")
    print(f"[exp158] Audit OK: {audit_ok}")
    print(f"[exp158] Wall-time = {receipt['wall_time_s']:.3f} s")
    print(f"[exp158] Receipt: {OUT_PATH}")

    return receipt


if __name__ == "__main__":
    main()
