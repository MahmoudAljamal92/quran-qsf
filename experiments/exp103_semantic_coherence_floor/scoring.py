"""
exp103_semantic_coherence_floor/scoring.py
==========================================

DESIGN-ONLY scoring helpers for H58 (semantic-coherence floor). The PREREG
explicitly defers run.py until a judge LLM is configured; this module
provides the *deterministic* parts of the scoring protocol so a future
run.py can simply wire them to a judge API.

What is here (deterministic, judge-independent):
  - `verse_prefix_split(verse, prefix_fraction=0.75)`: splits a verse into
    prefix + held-out continuation per PREREG §2.1.
  - `chrf_score(predicted, actual, n_char=6, beta=2)`: locked chrF
    parameters per PREREG §4.
  - `psi_coherence_text(per_verse_scores)`: text-level scalar = median
    over verses with >= min_prefix_tokens tokens.
  - `paired_wilcoxon(quran_psis, imitation_psis)`: paired Wilcoxon test
    for the "Quran > imitation" claim.
  - `arabic_skeleton_for_chrf(text)`: diacritics-stripped, whitespace-
    normalised Arabic for the chrF input.
  - `verdict_ladder(...)`: applies the 6-branch verdict ladder.

What is NOT here (judge-dependent; future run.py must add):
  - Judge LLM API call (`judge_predict_continuation(prefix, prev_verses)`).
  - Judge-fingerprint sentinel + JUDGE.json verification.
  - API-determinism sentinel (re-call with same prefix; same prediction).

Frozen constants (copied verbatim from PREREG §4):
  K = 3 (number of previous verses provided as context)
  prefix_fraction = 0.75
  min_prefix_tokens = 8
  seed = 42, temperature = 0, top_p = 1.0
  chrF: n_char = 6, beta = 2, case-folded, whitespace-normalised,
        diacritics-stripped (rasm equivalence)
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Iterable

# --- Frozen constants (mirror PREREG §4 exactly) -----------------------
K_CONTEXT = 3
PREFIX_FRACTION = 0.75
MIN_PREFIX_TOKENS = 8
SEED = 42
TEMPERATURE = 0.0
TOP_P = 1.0
CHRF_N_CHAR = 6
CHRF_BETA = 2

# Arabic diacritic (harakat + tashkeel + tanwin + small marks) range
_ARABIC_DIACRITIC_RE = re.compile(
    r"[\u064B-\u065F\u0670\u0610-\u061A\u06D6-\u06ED]"
)
# Hebrew niqqud + te'amim
_HEBREW_DIACRITIC_RE = re.compile(
    r"[\u0591-\u05AF\u05B0-\u05BC\u05BD\u05BF\u05C0-\u05C7]"
)


# --- Diacritic stripping (rasm-equivalent) -----------------------------
def strip_diacritics(text: str) -> str:
    """Strip Arabic and Hebrew diacritics, leaving consonant skeleton.

    For other scripts, falls back to NFD-decompose-then-strip-combining
    (handles Greek polytonic, Sanskrit / Vedic vowel signs, etc.).
    """
    s = _ARABIC_DIACRITIC_RE.sub("", text)
    s = _HEBREW_DIACRITIC_RE.sub("", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def normalise_for_chrf(text: str) -> str:
    """Whitespace-collapse + diacritic-strip + case-fold per PREREG §4."""
    s = strip_diacritics(text)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()


# --- Verse prefix / continuation split ---------------------------------
def verse_prefix_split(
    verse: str,
    prefix_fraction: float = PREFIX_FRACTION,
) -> tuple[str, str]:
    """Split a verse into prefix (first prefix_fraction of tokens) +
    held-out continuation (remainder).

    Returns: (prefix_text, continuation_text). Tokens are whitespace-split.
    """
    toks = verse.strip().split()
    if not toks:
        return ("", "")
    n_prefix = max(1, int(round(len(toks) * prefix_fraction)))
    n_prefix = min(n_prefix, len(toks) - 1)  # at least 1 token in continuation
    if n_prefix < 1:
        return (verse, "")
    return (" ".join(toks[:n_prefix]), " ".join(toks[n_prefix:]))


# --- chrF (locked parameters) ------------------------------------------
def _char_ngrams(text: str, n: int) -> Counter:
    """Character n-gram counts. Spaces preserved."""
    if len(text) < n:
        return Counter([text]) if text else Counter()
    return Counter(text[i:i + n] for i in range(len(text) - n + 1))


def chrf_score(
    predicted: str,
    actual: str,
    n_char: int = CHRF_N_CHAR,
    beta: int = CHRF_BETA,
) -> float:
    """chrF F-beta score over character n-grams up to n_char.

    Returns: float in [0, 1]. Both inputs are normalised via
    normalise_for_chrf before matching.
    """
    p = normalise_for_chrf(predicted)
    a = normalise_for_chrf(actual)
    if not p or not a:
        return 0.0

    f_scores: list[float] = []
    for n in range(1, n_char + 1):
        p_ngrams = _char_ngrams(p, n)
        a_ngrams = _char_ngrams(a, n)
        if not p_ngrams or not a_ngrams:
            f_scores.append(0.0)
            continue
        # Match counts
        matches = 0
        for ng, p_count in p_ngrams.items():
            matches += min(p_count, a_ngrams.get(ng, 0))
        precision = matches / sum(p_ngrams.values()) if p_ngrams else 0.0
        recall = matches / sum(a_ngrams.values()) if a_ngrams else 0.0
        if precision + recall == 0:
            f_scores.append(0.0)
            continue
        b2 = beta * beta
        f = (1 + b2) * precision * recall / (b2 * precision + recall)
        f_scores.append(f)
    return sum(f_scores) / n_char if f_scores else 0.0


# --- Text-level Psi_coherence (median over qualifying verses) ----------
def psi_coherence_text(
    per_verse_scores: Iterable[float],
    per_verse_prefix_tokens: Iterable[int],
    min_prefix_tokens: int = MIN_PREFIX_TOKENS,
) -> float:
    """Median Psi_coherence over verses with >= min_prefix_tokens.

    Args:
        per_verse_scores: chrF score per verse (list of floats in [0,1]).
        per_verse_prefix_tokens: number of prefix tokens per verse.
        min_prefix_tokens: filter floor.

    Returns: median, or NaN if no qualifying verses.
    """
    scores = list(per_verse_scores)
    n_toks = list(per_verse_prefix_tokens)
    if len(scores) != len(n_toks):
        raise ValueError("per_verse_scores and per_verse_prefix_tokens must match length.")
    qualifying = [s for s, t in zip(scores, n_toks) if t >= min_prefix_tokens]
    if not qualifying:
        return float("nan")
    qualifying.sort()
    n = len(qualifying)
    if n % 2 == 1:
        return qualifying[n // 2]
    return 0.5 * (qualifying[n // 2 - 1] + qualifying[n // 2])


# --- Paired Wilcoxon (no scipy import to keep this stdlib-only) --------
def paired_wilcoxon_one_sided(
    quran_psis: list[float],
    imitation_psis: list[float],
) -> dict:
    """One-sided paired Wilcoxon: H_alt: Quran > imitation per verse.

    Stdlib-only implementation suitable for moderate n (~10K). Returns
    dict with `n_pairs`, `n_pos`, `n_neg`, `T_plus`, `z`, `p_one_sided`.

    NOTE: this is a normal-approximation Wilcoxon. For small n (< 20)
    or for journal-grade reporting, future run.py should swap in
    scipy.stats.wilcoxon. The numbers here are rounded-but-honest for
    diagnostic dry-runs.
    """
    if len(quran_psis) != len(imitation_psis):
        raise ValueError("quran_psis and imitation_psis must match length.")
    diffs = [(q - i) for q, i in zip(quran_psis, imitation_psis) if q != i]
    n = len(diffs)
    if n == 0:
        return {"n_pairs": 0, "n_pos": 0, "n_neg": 0, "T_plus": 0.0,
                "z": float("nan"), "p_one_sided": float("nan")}
    abs_diffs = sorted(abs(d) for d in diffs)
    # Average ranks for ties
    ranks: dict[float, float] = {}
    i = 0
    while i < len(abs_diffs):
        j = i
        while j + 1 < len(abs_diffs) and abs_diffs[j + 1] == abs_diffs[i]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # 1-indexed
        for k in range(i, j + 1):
            ranks[abs_diffs[k]] = avg_rank
        i = j + 1
    T_plus = 0.0
    n_pos = 0
    n_neg = 0
    for d in diffs:
        if d > 0:
            T_plus += ranks[abs(d)]
            n_pos += 1
        elif d < 0:
            n_neg += 1
    mu = n * (n + 1) / 4.0
    sigma = (n * (n + 1) * (2 * n + 1) / 24.0) ** 0.5
    z = (T_plus - mu) / sigma if sigma > 0 else float("nan")
    # One-sided upper p (alt: T_plus > mu, i.e., Quran > imitation)
    # Standard normal CDF via erfc
    import math
    p_one_sided = 0.5 * math.erfc(z / (2 ** 0.5)) if not math.isnan(z) else float("nan")
    return {
        "n_pairs": n, "n_pos": n_pos, "n_neg": n_neg,
        "T_plus": T_plus, "z": z, "p_one_sided": p_one_sided,
    }


# --- Verdict ladder (mirrors PREREG §2.3) ------------------------------
def verdict_ladder(
    judge_configured: bool,
    exp102_receipt_loaded_ok: bool,
    judge_fingerprint_match: bool,
    quran_psi: float,
    imitation_results: dict,  # name -> {"psi": float, "p_one_sided": float}
    p_threshold: float = 0.01,
    median_lead_min: float = 0.05,
) -> tuple[str, str]:
    """Apply the 6-branch verdict ladder; return (verdict, branch_msg)."""
    if not judge_configured:
        return ("BLOCKED_no_judge", "Judge LLM not configured / API unreachable.")
    if not exp102_receipt_loaded_ok:
        return ("BLOCKED_imitations_missing",
                "exp102 receipt missing or BLOCKED; acquire imitations first.")
    if not judge_fingerprint_match:
        return ("FAIL_judge_drift",
                "Judge fingerprint drifts from locked JUDGE.json constants.")
    # Per-imitation pairwise checks
    failures = []
    leads_below_min: list[tuple[str, float]] = []
    for name, r in imitation_results.items():
        if r["p_one_sided"] >= p_threshold or quran_psi <= r["psi"]:
            failures.append(name)
            continue
        lead = quran_psi - r["psi"]
        if lead < median_lead_min:
            leads_below_min.append((name, lead))
    if failures:
        return ("FAIL_quran_not_above_imitation",
                f"Failed pairwise tests vs: {', '.join(failures)}.")
    if leads_below_min:
        msg_parts = [f"{n}={l:.3f}" for n, l in leads_below_min]
        return ("PARTIAL_quran_above_with_caveat",
                f"All p < {p_threshold} but median lead < {median_lead_min} on: "
                f"{', '.join(msg_parts)}.")
    return ("PASS_quran_strict_above",
            f"Quran median Psi > all imitation medians by >= "
            f"{median_lead_min} chrF; all pairwise p < {p_threshold}.")


# --- Smoke test (importable, not a real run) ---------------------------
if __name__ == "__main__":
    # Quick deterministic sanity check
    print("# exp103 scoring helpers — smoke test")
    test_verse = "wa-llaahu yasma3u du3aa-akum fi kulli waqtin"
    pre, cont = verse_prefix_split(test_verse, 0.75)
    print(f"  prefix       : {pre!r}")
    print(f"  continuation : {cont!r}")
    score_perfect = chrf_score(cont, cont)
    score_disjoint = chrf_score("xyz", cont)
    print(f"  chrF(cont, cont) = {score_perfect:.3f}  (should be 1.0)")
    print(f"  chrF(xyz,  cont) = {score_disjoint:.3f}  (should be small)")
    psi = psi_coherence_text(
        per_verse_scores=[0.9, 0.85, 0.6, 0.55, 0.7],
        per_verse_prefix_tokens=[10, 12, 9, 8, 4],  # last one excluded
    )
    print(f"  median psi (4 qualifying) = {psi:.3f}")
    res = paired_wilcoxon_one_sided(
        quran_psis=[0.85, 0.90, 0.80, 0.88, 0.92],
        imitation_psis=[0.40, 0.35, 0.50, 0.45, 0.30],
    )
    print(f"  paired Wilcoxon: n={res['n_pairs']}, z={res['z']:.3f}, "
          f"p_one_sided={res['p_one_sided']:.4g}")
    print("# all helpers callable; ready for future run.py")
