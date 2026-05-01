"""
exp09_R1_variant_forensics_9ch
==============================
R1 — Multi-channel single-letter variant forensics.

2026-04-20 AUDIT-FIX PASS + AUDIT ROUND 2
-----------------------------------------
This file was rewritten to close the following findings from
AUDIT_ULTIMATE2 and AUDIT_ULTIMATE2_ROUND2:

Round 1 (F-1..F-40 in AUDIT_ULTIMATE2.md):
  * F-1   Reference statistics for channels B, G are now trained on
          **non-Quran control corpora only**. Previously they were built
          from the Quran itself, making every z-score circular.
  * F-3   ``CANONICAL_VARIANTS`` is cleaned: the self-equal "null control"
          entry is removed; word-level / multi-word entries are tagged
          ``kind != 'single_letter'`` and excluded from the single-letter
          detection-rate denominator.
  * F-4   Channels C (letter-bigram vector distance) and D (numeric wazn
          diversity) are now first-class members of ``per_channel_null`` so
          R1 actually reports 9 channels — the pre-audit code filled only
          7 and one of those (D) returned a string.
  * F-11  The triliteral-root heuristic is documented as a crude proxy and
          its output is now explicitly labelled as such.
  * F-28  ``_letter_transition_matrix`` uses a **fixed 34-character
          alphabet** (previously the alphabet was extended by whatever
          characters happened to be in the input, making matrices of
          different shapes for different inputs).
  * F-34  Variant injection now operates on the post-normalised verse so
          diacritics can't shift the replacement position.
  * F-35  Channel A is complemented by an explicit letter-sensitive bigram
          distance (channel C). Channel A alone was near-insensitive to
          single-letter swaps in mid-length surahs.
  * F-40  Null distribution is sampled from a **random subset** of surahs
          rather than the top-N by length (which biased the null toward
          long-surah statistics).

Round 2 (F-ULT2-* in AUDIT_ULTIMATE2_ROUND2.md):
  * F-ULT2-A1  The null loop no longer strips whitespace from the
          perturbed verse via ``letters_only``. Nulls and canonical
          variants now carry the **same kind of perturbation** (one-
          letter edit, spaces preserved) so z-scores are comparable.
  * F-ULT2-R1n1  Null is generated per edit type (swap, delete, insert,
          word_delete, multi_word) and each canonical variant is z-scored
          against the null whose edit-type matches ``detect_edit_type``
          of its ``(orig → var)`` pair.
  * F-ULT2-C1   Channel C (letter-bigram distance) is now documented in
          ``channel_notes`` as a *tautological* edit-magnitude measure,
          not an independent authenticity signal. MASTER downweights
          it accordingly.

Channels (all nine are computed; the first three are the headline ones)
-----------------------------------------------------------------------
A  Spectral fingerprint  — top-2 SVD ratio of a 34×34 letter-transition
   matrix (fixed alphabet).
B  Root-bigram log-likelihood under a *control-trained* reference.
C  Letter-bigram-vector L2 distance between canonical and tampered (the
   new, explicitly letter-sensitive channel).
D  Wazn diversity  — number of distinct C-L shape patterns per word,
   returned as a scalar.
E  Compression distance (gzip NCD) vs the canonical surah.
F  Verse-pair coupling strength (adjacent-verse letter-bigram Jaccard).
G  Root-trigram char-LM log-prob per char, *control-trained*.
H  Local 3-verse spectral window (the amplifier for R2).
I  Root semantic-field clustering (share of adjacent words with shared
   first-radical under the crude root heuristic).

Reads (checked): phase_06_phi_m.pkl via experiments._lib.load_phase.
Writes ONLY under results/experiments/exp09_R1_variant_forensics_9ch/.
"""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Callable

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Optional tqdm progress bars (pass-through no-op if not installed).
try:
    from tqdm.auto import tqdm as _tqdm
except ImportError:                                                     # pragma: no cover
    def _tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else (lambda x: x)

from experiments._lib import safe_output_dir, self_check_begin, self_check_end
from experiments._ultimate2_helpers import (
    ARABIC_CONSONANTS, ARABIC_EXTRA, CharNGramLM, SCHEMA_VERSION,
    bigram_jaccard_distance, detect_edit_type, extract_verses,
    letter_bigram_set, letters_only, letters_only_strict, load_corpora,
    normalize_rasm, normalize_rasm_strict,
    random_multi_word_replace, random_single_letter_delete,
    random_single_letter_insert, random_single_letter_swap,
    random_single_word_delete, words,
)

EXP = "exp09_R1_variant_forensics_9ch"
SEED = 42

# Fixed alphabet for the letter-transition matrix (F-28). Order is frozen so
# matrix cells have a stable semantic meaning across runs.
ALPHABET: str = ARABIC_CONSONANTS + ARABIC_EXTRA + " "   # 28 + 5 + 1 = 34
_ALPHABET_IDX: dict[str, int] = {c: i for i, c in enumerate(ALPHABET)}
ALPHABET_N: int = len(ALPHABET)

# Control corpora used to train channel-B / channel-G reference statistics.
# **Never** includes "quran" (F-1). Ordered by rough size; the helper takes
# what is actually present in the checkpoint and ignores missing names.
_CONTROL_CORPUS_NAMES: tuple[str, ...] = (
    "poetry_abbasi", "poetry_jahili", "ksucca", "hindawi", "arabic_bible",
)

# ---------------------------------------------------------------------------
# Canonical variants (audit-fix F-3)
# ---------------------------------------------------------------------------
# ``kind`` field lets downstream aggregators separate genuine single-letter
# variants from word-level / multi-word variants. Detection rate is reported
# per-kind and also filtered to the single-letter subset.
CANONICAL_VARIANTS: list[dict] = [
    {"surah": 1,  "orig": "\u0645\u0627\u0644\u0643",   "var": "\u0645\u0644\u0643",
     "name": "1:4_malik_malik",       "kind": "single_letter"},
    {"surah": 2,  "orig": "\u0646\u0646\u0634\u0632\u0647\u0627",  "var": "\u0646\u0646\u0634\u0631\u0647\u0627",
     "name": "2:259_nunshiz_nunshir", "kind": "single_letter"},
    # The following two are NOT single-letter edits. Kept for transparency
    # but excluded from the single-letter denominator. They are reported
    # under the 'word_level' / 'multi_word' buckets.
    {"surah": 3,  "orig": "\u0648\u0633\u0627\u0631\u0639\u0648\u0627", "var": "\u0633\u0627\u0631\u0639\u0648\u0627",
     "name": "3:133_word_deletion",   "kind": "word_level"},
    {"surah": 92, "orig": "\u0648\u0645\u0627 \u062e\u0644\u0642",      "var": "\u0648\u0627\u0644\u0630\u0643\u0631",
     "name": "92:3_ibn_masud",        "kind": "multi_word"},
]


# ---------------------------------------------------------------------------
# Channel implementations
# ---------------------------------------------------------------------------
def _letter_transition_matrix(text: str) -> np.ndarray:
    """Return the 34×34 letter-transition count matrix on the FIXED alphabet."""
    M = np.zeros((ALPHABET_N, ALPHABET_N), dtype=float)
    t = normalize_rasm(text)
    for a, b in zip(t[:-1], t[1:]):
        ia = _ALPHABET_IDX.get(a)
        ib = _ALPHABET_IDX.get(b)
        if ia is not None and ib is not None:
            M[ia, ib] += 1.0
    return M


def channel_A_spectral(text: str) -> float:
    """Top-2 singular-value ratio of the letter-transition matrix.

    Kept for backwards compatibility with R2/R7/R9, which import this symbol
    directly. Use channel_C_bigram_dist for a properly letter-sensitive
    signal.
    """
    M = _letter_transition_matrix(text)
    if M.size == 0 or not M.any():
        return 0.0
    try:
        s = np.linalg.svd(M, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0
    if len(s) < 2 or s[0] <= 0:
        return 0.0
    return float(s[1] / s[0])


def _triliteral_root(word: str) -> str:
    """Crude triliteral-root heuristic (F-11).

    Strips a short list of affixes then keeps the first three consonants.
    This is NOT a real Arabic stemmer — it is a deliberate simplification
    that is good enough to provide a Markov-style channel. Downstream code
    treats B/G as "first-order root-proxy Markov channels" not as
    morphology-aware detectors.
    """
    w = letters_only(word)
    for pref in ("\u0648\u0627\u0644", "\u0641\u0627\u0644", "\u0628\u0627\u0644", "\u0627\u0644",
                 "\u0648", "\u0641", "\u0628", "\u0643", "\u0644", "\u0633"):
        if w.startswith(pref) and len(w) > len(pref) + 2:
            w = w[len(pref):]
            break
    for suf in ("\u0648\u0646", "\u064a\u0646", "\u0627\u062a", "\u0627\u0646", "\u0647\u0627", "\u0643\u0645",
                "\u0647\u0645", "\u0646\u0627", "\u0646\u064a", "\u0643", "\u0647"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            w = w[:-len(suf)]
            break
    w = "".join(ch for ch in w if ch in ARABIC_CONSONANTS)
    return w[:3].ljust(3, "_")


def channel_B_root_bigram(text: str, ref_counts: Counter) -> float:
    """Log-likelihood of adjacent root-bigrams under a control-trained reference."""
    wlist = words(text)
    roots = [_triliteral_root(w) for w in wlist]
    total = sum(ref_counts.values()) or 1
    V = len(ref_counts) or 1
    lp = 0.0
    for a, b in zip(roots[:-1], roots[1:]):
        key = (a, b)
        c = ref_counts.get(key, 0)
        lp += math.log((c + 0.5) / (total + 0.5 * V))
    # Normalise by length so surahs of very different sizes are comparable.
    return lp / max(1, len(roots) - 1)


def channel_C_bigram_dist(canonical_text: str, tampered_text: str) -> float:
    """L2 distance between bigram-count vectors of canonical and tampered texts.

    This is the explicit letter-sensitive primary channel introduced by the
    F-35 audit-fix. Every single-letter swap inside the tampered text
    contributes at least ~2 bigram deltas, so the metric is monotonically
    responsive to edit count.
    """
    # Compute bigram counts over the strict-normalised letter stream.
    def counts(s: str) -> Counter:
        t = letters_only_strict(s)
        return Counter(zip(t, t[1:]))
    A = counts(canonical_text)
    B = counts(tampered_text)
    keys = set(A) | set(B)
    if not keys:
        return 0.0
    diff_sq = 0.0
    for k in keys:
        d = A.get(k, 0) - B.get(k, 0)
        diff_sq += d * d
    return math.sqrt(diff_sq)


def channel_D_wazn(text: str) -> float:
    """Numeric wazn-diversity score (F-19 audit-fix).

    Computes the C-L (consonant/long-vowel) shape of every word and returns
    the ratio ``n_distinct_shapes / n_words``. Bounded in [0, 1]; higher
    means more morphologically varied.
    """
    shapes: list[str] = []
    for w in words(text):
        s = "".join("L" if ch in "\u0627\u0648\u064a\u0649" else "C"
                    for ch in letters_only(w))
        if s:
            shapes.append(s)
    if not shapes:
        return 0.0
    return len(set(shapes)) / len(shapes)


def channel_E_gzip_ncd(a: str, b: str) -> float:
    """Normalised compression distance (gzip)."""
    def gz(x: str) -> int:
        return len(gzip.compress(x.encode("utf-8")))
    ga, gb, gab = gz(a), gz(b), gz(a + b)
    return (gab - min(ga, gb)) / max(1, max(ga, gb))


def channel_F_coupling(verses: list[str]) -> float:
    """Mean pairwise adjacent-verse Jaccard similarity on the bigram set."""
    if len(verses) < 2:
        return 0.0
    J = []
    for a, b in zip(verses[:-1], verses[1:]):
        A, B = letter_bigram_set(a, strict=True), letter_bigram_set(b, strict=True)
        denom = len(A | B)
        J.append(len(A & B) / denom if denom else 0.0)
    return float(np.mean(J))


def channel_G_root_trigram(text: str, lm: "CharNGramLM") -> float:
    """Char n-gram log-prob per char of the root-collapsed text, under a
    control-trained LM."""
    roots = [_triliteral_root(w) for w in words(text)]
    if not roots:
        return 0.0
    return lm.per_char_lp(" ".join(roots))


def channel_H_local_spectral(verses: list[str], window: int = 3) -> float:
    """Mean channel-A spectral ratio across overlapping k-verse windows."""
    if len(verses) < window:
        return 0.0
    vals = []
    for i in range(len(verses) - window + 1):
        chunk = " ".join(verses[i:i + window])
        vals.append(channel_A_spectral(chunk))
    return float(np.mean(vals))


def channel_I_root_field(text: str) -> float:
    """Share of adjacent word-pairs whose crude root starts with the same letter."""
    roots = [_triliteral_root(w) for w in words(text)]
    if len(roots) < 2:
        return 0.0
    hits = sum(1 for a, b in zip(roots[:-1], roots[1:])
               if a and b and a[0] == b[0] and a[0] != "_")
    return hits / (len(roots) - 1)


# ---------------------------------------------------------------------------
# Feature assembly
# ---------------------------------------------------------------------------
CHANNELS_ALL: tuple[str, ...] = (
    "A_spectral", "B_root_bigram", "C_bigram_dist",
    "D_wazn", "E_ncd", "F_coupling",
    "G_root_trigram", "H_local_spec", "I_root_field",
)


def nine_channel_features(
    verses: list[str],
    ref_bigram_counts: Counter,
    root_lm: CharNGramLM,
    canonical_text: str | None = None,
) -> dict[str, float]:
    full = " ".join(verses)
    canon = canonical_text if canonical_text is not None else full
    feats = {
        "A_spectral":     channel_A_spectral(full),
        "B_root_bigram":  channel_B_root_bigram(full, ref_bigram_counts),
        "C_bigram_dist":  channel_C_bigram_dist(canon, full),
        "D_wazn":         channel_D_wazn(full),
        "E_ncd":          channel_E_gzip_ncd(letters_only(full), letters_only(canon)),
        "F_coupling":     channel_F_coupling(verses),
        "G_root_trigram": channel_G_root_trigram(full, root_lm),
        "H_local_spec":   channel_H_local_spectral(verses),
        "I_root_field":   channel_I_root_field(full),
    }
    return feats


def zscore(vals: list[float], v: float) -> float:
    if len(vals) < 3:
        return 0.0
    mu = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    return (v - mu) / sd if sd > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# Control-corpus training helpers (audit-fix F-1)
# ---------------------------------------------------------------------------
def _train_control_references(
    corpora: dict, n_max_units_per_corpus: int | None = None,
) -> tuple[Counter, CharNGramLM, list[str]]:
    """Build (root-bigram counter, root-char LM, corpus names used) from the
    control corpora only. The Quran is NEVER part of this training pool."""
    used: list[str] = []
    ref_bi: Counter = Counter()
    root_stream: list[str] = []
    for name in _CONTROL_CORPUS_NAMES:
        if name not in corpora:
            continue
        used.append(name)
        units = corpora[name]
        if n_max_units_per_corpus is not None:
            units = units[:n_max_units_per_corpus]
        for u in units:
            verses = extract_verses(u)
            rts = [_triliteral_root(w) for w in words(" ".join(verses))]
            for a, b in zip(rts[:-1], rts[1:]):
                ref_bi[(a, b)] += 1
            root_stream.append(" ".join(rts))
    if not root_stream:
        raise RuntimeError(
            "No control corpora available for training references; "
            "pipeline cannot proceed without at least one non-Quran corpus."
        )
    root_lm = CharNGramLM(n=4).fit(root_stream)
    return ref_bi, root_lm, used


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------
def main(fast: bool = True) -> dict:
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    np.random.seed(SEED)

    pre = self_check_begin()
    out = safe_output_dir(EXP)

    # ---- Load corpora ----------------------------------------------------
    corpora = load_corpora()
    if "quran" not in corpora:
        raise RuntimeError("phase_06 checkpoint is missing the 'quran' corpus.")
    quran = corpora["quran"]
    quran_surahs = [extract_verses(s) for s in quran]
    n_surahs = len(quran_surahs)
    print(f"[{EXP}] loaded {n_surahs} surahs")

    # ---- Train reference statistics on CONTROL corpora only (F-1) -------
    ref_bi, root_lm, control_names = _train_control_references(corpora)
    print(f"[{EXP}] control training corpora: {control_names}  "
          f"root-bigrams: {sum(ref_bi.values())}")

    # ---- Sample surahs for the null distribution (F-40: random, not top-N) -
    # Filter to surahs with enough text to give a meaningful swap.
    candidates = [i for i, vs in enumerate(quran_surahs)
                  if sum(len(letters_only(v)) for v in vs) >= 200]
    k = min(20 if fast else 50, len(candidates))
    sample_idx = rng.sample(candidates, k) if k > 0 else []
    n_trials = 10 if fast else 30

    # ---- Build per-edit-type nulls (audit-round-2 F-ULT2-R1n1) -----------
    # Each canonical variant is compared to a null whose perturbation type
    # matches the variant. Nulls: swap / delete / insert (letter-level),
    # word_delete / multi_word (word-level). ``per_channel_null`` stays as
    # the "swap" null for backwards-compatible outputs.
    EDIT_TYPES_FOR_NULL: tuple[str, ...] = (
        "swap", "delete", "insert", "word_delete", "multi_word",
    )
    per_edit_type_null: dict[str, dict[str, list[float]]] = {
        et: {ch: [] for ch in CHANNELS_ALL} for et in EDIT_TYPES_FOR_NULL
    }
    n_cases_by_type: dict[str, int] = {et: 0 for et in EDIT_TYPES_FOR_NULL}

    def _apply_null_edit(et: str, verse_text: str
                         ) -> str | None:
        """Apply one random edit of type ``et`` to ``verse_text``.

        Whitespace is preserved (F-ULT2-A1). Returns the edited verse or
        ``None`` when the edit is a no-op / not applicable.
        """
        if et == "swap":
            new, _, a, _b = random_single_letter_swap(verse_text, rng)
            return new if a else None
        if et == "delete":
            new, pos, d = random_single_letter_delete(verse_text, rng)
            return new if pos >= 0 and d else None
        if et == "insert":
            new, pos, ins = random_single_letter_insert(verse_text, rng)
            return new if pos >= 0 and ins else None
        if et == "word_delete":
            new, idx, _w = random_single_word_delete(verse_text, rng)
            return new if idx >= 0 and new != verse_text else None
        if et == "multi_word":
            new, idx, _ws = random_multi_word_replace(verse_text, rng, n=2)
            return new if idx >= 0 and new != verse_text else None
        return None

    for si in _tqdm(sample_idx, desc="R1 surahs (null)", leave=False):
        verses = quran_surahs[si]
        # IMPORTANT: pre-normalise once so channels see a consistent rasm.
        verses_norm = [normalize_rasm(v) for v in verses]
        canon_text = " ".join(verses_norm)
        canon_feats = nine_channel_features(
            verses_norm, ref_bi, root_lm, canonical_text=canon_text)
        for _ in range(n_trials):
            vi = rng.randrange(len(verses_norm))
            verse_text = verses_norm[vi]
            # Length check is performed on the letters-only projection but
            # the edit is applied to the original (spaces-preserved) verse
            # so the null matches the canonical-variant injection pattern.
            if len(letters_only(verse_text)) < 3:
                continue
            for et in EDIT_TYPES_FOR_NULL:
                edited = _apply_null_edit(et, verse_text)
                if edited is None:
                    continue
                new_verses = verses_norm[:vi] + [edited] + verses_norm[vi + 1:]
                new_feats = nine_channel_features(
                    new_verses, ref_bi, root_lm, canonical_text=canon_text)
                for ch in CHANNELS_ALL:
                    per_edit_type_null[et][ch].append(
                        new_feats[ch] - canon_feats[ch]
                    )
                n_cases_by_type[et] += 1

    # Back-compat alias: the "swap" null is the historical default.
    per_channel_null: dict[str, list[float]] = per_edit_type_null["swap"]
    n_cases: int = n_cases_by_type["swap"]

    print(f"[{EXP}] null-distribution cases: "
          + "  ".join(f"{et}={n}" for et, n in n_cases_by_type.items()))

    # ---- Evaluate canonical variants (F-34: post-norm + F-ULT2-R1n1: matched null) -
    # Each variant's edit-type is detected from (orig_norm, var_norm) and its
    # z-scores are computed against the null distribution of *that* edit type,
    # not the generic swap null. This closes audit-round-2 F-ULT2-R1n1.
    NULL_KEY_MAP: dict[str, str] = {
        "swap":         "swap",
        "delete":       "delete",
        "insert":       "insert",
        "word_delete":  "word_delete",
        "word_insert":  "word_delete",   # symmetric; re-use delete null
        "multi_word":   "multi_word",
        "null":         "swap",           # degenerate no-op variant
    }

    canonical_results: list[dict] = []
    for entry in _tqdm(CANONICAL_VARIANTS, desc="R1 canonical variants", leave=False):
        surah_idx = entry["surah"]
        orig_raw, var_raw = entry["orig"], entry["var"]
        name, kind = entry["name"], entry["kind"]
        if surah_idx - 1 >= n_surahs:
            continue
        verses_raw = quran_surahs[surah_idx - 1]
        verses_norm = [normalize_rasm(v) for v in verses_raw]
        canon_text = " ".join(verses_norm)
        canon_feats = nine_channel_features(
            verses_norm, ref_bi, root_lm, canonical_text=canon_text)

        # Inject the variant POST-normalisation (F-34): normalise both orig
        # and var, then str.replace in the already-normalised verse list.
        orig_norm = normalize_rasm(orig_raw)
        var_norm = normalize_rasm(var_raw)
        new_verses: list[str] = []
        found = False
        for v in verses_norm:
            if not found and orig_norm and orig_norm in v:
                new_verses.append(v.replace(orig_norm, var_norm, 1))
                found = True
            else:
                new_verses.append(v)

        # Detect the actual edit type and pick the matching null.
        detected_edit = detect_edit_type(orig_norm, var_norm)
        null_key = NULL_KEY_MAP.get(detected_edit, "swap")
        null_for_variant = per_edit_type_null.get(null_key, per_channel_null)

        new_feats = nine_channel_features(
            new_verses, ref_bi, root_lm, canonical_text=canon_text)
        deltas = {k: new_feats[k] - canon_feats[k] for k in CHANNELS_ALL}
        zscores = {k: zscore(null_for_variant[k], v) for k, v in deltas.items()}
        fired = sum(1 for z in zscores.values() if abs(z) > 2.0)

        # Confidence thresholds recalibrated to 9 real channels (F-27).
        if fired >= 6:
            conf = "VERY HIGH"
        elif fired >= 4:
            conf = "HIGH"
        elif fired >= 2:
            conf = "MEDIUM"
        else:
            conf = "LOW"

        canonical_results.append({
            "name": name, "kind": kind, "surah": surah_idx,
            "detected_edit_type": detected_edit,
            "null_used": null_key,
            "found_in_text": found,
            "deltas":   {k: round(v, 4) for k, v in deltas.items()},
            "z_scores": {k: round(v, 3) for k, v in zscores.items()},
            "channels_fired_abs_z_gt_2": fired,
            "confidence": conf,
        })

    # ---- Per-kind detection rates (F-3) ---------------------------------
    rates_by_kind: dict[str, dict[str, float]] = {}
    for kind in {r["kind"] for r in canonical_results}:
        group = [r for r in canonical_results if r["kind"] == kind]
        if not group:
            continue
        fired_ge_3 = sum(1 for r in group
                         if r["found_in_text"]
                         and r["channels_fired_abs_z_gt_2"] >= 3)
        rates_by_kind[kind] = {
            "n_total":     len(group),
            "n_found":     sum(1 for r in group if r["found_in_text"]),
            "n_fired_ge_3": fired_ge_3,
            "rate":         fired_ge_3 / max(1, sum(1 for r in group
                                                    if r["found_in_text"])),
        }

    # Headline rate is restricted to genuine single-letter edits (F-3).
    headline_rate = rates_by_kind.get("single_letter", {}).get("rate", 0.0)

    # ---- Assemble result ------------------------------------------------
    def _null_summary(null: dict[str, list[float]]) -> dict:
        return {
            k: {
                "mean": float(np.mean(v)) if v else 0.0,
                "std":  float(np.std(v, ddof=1)) if len(v) > 1 else 0.0,
                "p95":  float(np.percentile(np.abs(v), 95)) if v else 0.0,
                "n":    len(v),
            } for k, v in null.items()
        }

    # Channel self-documentation (audit-round-2 F-ULT2-C1).
    channel_notes: dict[str, str] = {
        "A_spectral":     "top-2 SVD ratio of the 34x34 letter-transition matrix",
        "B_root_bigram":  "log-likelihood of root-bigrams under a CONTROL-trained reference (F-1)",
        "C_bigram_dist":  (
            "L2 distance of letter-bigram counts between canonical and tampered text. "
            "TAUTOLOGICAL: fires on any edit by construction (F-ULT2-C1). "
            "Useful as a sanity check, NOT as an independent authenticity signal; "
            "MASTER downweights it."
        ),
        "D_wazn":         "n_distinct C-L shapes / n_words (F-19)",
        "E_ncd":          "gzip normalised-compression-distance vs canonical",
        "F_coupling":     "mean adjacent-verse bigram-Jaccard coupling",
        "G_root_trigram": "char n-gram LM log-prob per char of the root-stream under a CONTROL-trained LM (F-1)",
        "H_local_spec":   "mean A_spectral over 3-verse rolling windows",
        "I_root_field":   "share of adjacent word-pairs sharing first consonant (crude root proxy)",
    }

    result = {
        "exp": EXP,
        "schema_version": SCHEMA_VERSION,
        "seed": SEED,
        "fast_mode": fast,
        "control_training_corpora": control_names,
        "n_surahs_sampled": len(sample_idx),
        "n_null_cases": n_cases,
        "n_cases_by_edit_type": n_cases_by_type,
        "channels_implemented": list(CHANNELS_ALL),
        "channel_notes": channel_notes,
        "per_channel_null_summary": _null_summary(per_channel_null),
        "per_edit_type_null_summary": {
            et: _null_summary(per_edit_type_null[et])
            for et in EDIT_TYPES_FOR_NULL
        },
        "canonical_variants": canonical_results,
        "rates_by_kind":      rates_by_kind,
        "headline_single_letter_rate": headline_rate,
        "verdict_expected": (
            "At least 3 of 9 channels fire (|z|>2) on every genuine "
            "single-letter canonical variant; headline rate >= 0.80."
        ),
        "runtime_seconds": round(time.time() - t0, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] wrote {out / (EXP + '.json')}")

    self_check_end(pre, exp_name=EXP)
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--fast", action="store_true", default=True)
    p.add_argument("--normal", dest="fast", action="store_false")
    args = p.parse_args()
    main(fast=args.fast)
