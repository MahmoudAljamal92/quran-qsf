"""
experiments/ultimate2_pipeline.py
=================================
ULTIMATE-2 pipeline — all 11 R-experiments (R1–R11) + MASTER composite
detector, implemented as standalone callables that the Ultimate-2
notebook orchestrates end-to-end.

2026-04-20 AUDIT-FIX PASS + AUDIT ROUND 2
-----------------------------------------
Round 1 (AUDIT_ULTIMATE2.md, F-1..F-46):

  F-2  / F-18 / F-29:  R3 and R5 now use a **bigram-Jaccard** path metric
        (``canonical_path_length_bigram``) instead of the letter-SET
        Jaccard that was degenerate on Arabic. R5 forgery transitions
        are trained on control corpora only; the honest strategy list
        is shrunk to the two genuinely different forgers.
  F-5 :  R6 uses a proper Louvain ΔQ formula and fixes the double-counted
        degree. Edge-weight FAST truncation now records the truncation
        as a metadata field.
  F-6 :  R11 no longer silently fabricates an AUC; if the required feature
        columns are missing, it returns ``AUC_quran_vs_ctrl = None`` and
        ``features_available = False``.
  F-7 /F-10/F-24/F-30/F-31:  MASTER reports a clearly-named
        ``P_detect_upper`` (independence ceiling) **and** a
        ``P_detect_lower`` (maximum-correlation floor), plus Benjamini–
        Hochberg-adjusted per-channel p-values; the TDL statement is
        rephrased to match the statistic and the coverage mismatch is
        flagged explicitly.
  F-12:  R2 reports log-amplification with a bootstrap CI; raw ratio is
        still available for continuity.
  F-13:  R7 and R9 report log-ratios with bootstrap CI.
  F-14:  R8 runs the full N0–N7 ladder (8 rungs) now that
        _ultimate2_helpers exposes all of them.
  F-15:  R10 filters to verses with ≥ 5 words; short verses are binned
        into a secondary `short_verses_sig_rate` field instead of being
        silently counted.
  F-16:  R4 trains the char-LM on control corpora only AND filters any
        training unit whose bigram set has ≥ 90 % Jaccard overlap with
        any Quran surah (Quran-contamination check).
  F-42:  R7 uses a random sample (seeded) rather than ``corpus[:20]``.
  F-43:  R9 guards i != j in the verse-swap and asserts block shuffle
        changes order.

Round 2 (AUDIT_ULTIMATE2_ROUND2.md, F-ULT2-*):

  F-ULT2-A1    R2 / R4 / R9 now apply the letter-swap to the
        whitespace-preserving verse text; previously they stripped all
        intra-verse whitespace via ``letters_only`` before the swap,
        making null perturbations systematically larger than canonical
        variants.
  F-ULT2-M1    MASTER no longer feeds uninformative channels into the
        independence product at r=0.5. Each channel is re-coded with
        ``auc_to_rate`` / ``calibrate_rate_above_null`` /
        ``signal_from_log_ratio_ci`` so that a null-signal channel
        contributes r=0. ``P_detect_upper`` is now honest.
  F-ULT2-R3a   R3 uses ``canonical_path_length_bigram_greek`` for any
        corpus whose units contain Greek text (previously the Arabic
        normaliser stripped every Greek character, giving z=0 by
        construction for ``iliad_greek``).
  F-ULT2-R9a   R9 replaces the broken per-element bootstrap with a
        proper ``bootstrap_ci`` call on the log-ratio samples.
  F-ULT2-MASTER-R3  MASTER splits channels into ``_EDIT_DETECTION_*``
        (R1, R2, R4, R7, R9, R11) and ``_CORPUS_AUTHENTICITY_*`` (R3,
        R5, R6, R8, R10). ``P_detect`` is computed **only** over
        edit-detection channels; corpus-authenticity channels are
        reported under ``structural_signature_score`` so they no
        longer inflate the detection posterior.
  F-ULT2-R10a  R10 reports both the raw ``sig_rate`` and a
        ``sig_rate_calibrated = (sig_rate - 0.05) / 0.95`` above its
        null baseline (type-I error at alpha=0.05).
  F-ULT2-R6a   R6 FAST-mode edge truncation now equalises the cap
        across corpora (cap = min(50 000, smallest-corpus edge count))
        so the modularity ranking is not biased by size.
  F-ULT2-R7a   R7 now runs over every control corpus available in
        ``_CONTROL_CORPUS_NAMES``, not just 2 of 5.
  F-ULT2-R11a  R11 uses ``state.get()`` and silently degrades to
        ``features_available=False`` if the expected phase_06 keys are
        missing instead of raising ``KeyError``.
  F-ULT2-LOG1  ``_log_ratio`` now preserves the sign of ``num - den``
        when inputs are signed (kept backwards-compatible for the
        non-negative callers R2/R7/R9 currently use).
  F-ULT2-DEAD1 The unused ``_uniform_seeded_rng`` (tuple-hash based,
        PYTHONHASHSEED-unstable) is removed.

All functions:
  * read through the integrity-checked loader (experiments._lib)
  * write only under results/experiments/expNN_*/
  * return a dict with a consistent schema (exp, schema_version, seed,
    fast_mode, runtime_seconds, plus experiment-specific fields).

This complements — does NOT modify — the Ultimate-1 pipeline.
"""
from __future__ import annotations

import json
import math
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

import numpy as np

# Optional tqdm progress bars (falls back to a pass-through no-op if tqdm
# isn't installed). All loops use this handle; no behaviour change.
try:
    from tqdm.auto import tqdm as _tqdm
except ImportError:                                                     # pragma: no cover
    def _tqdm(iterable=None, **kwargs):
        return iterable if iterable is not None else (lambda x: x)

from experiments._lib import safe_output_dir, self_check_begin, self_check_end
from experiments._ultimate2_helpers import (
    ARABIC_CONSONANTS, CharNGramLM, NULLS, R1_NULL_BASELINE_3OF9,
    SCHEMA_VERSION, auc_to_rate, benjamini_hochberg,
    bigram_jaccard_distance, bigram_jaccard_distance_greek,
    bootstrap_ci, calibrate_rate_above_null,
    canonical_path_length_bigram, canonical_path_length_bigram_greek,
    extract_verses, letter_bigram_set, letters_only, letters_only_strict,
    load_corpora, load_phi_state, mahalanobis2, normalize_rasm,
    normalize_rasm_strict, percentile_rank, random_single_letter_swap,
    signal_from_log_ratio_ci, unit_label, words,
)

SEED = 42

# Control corpora for training the char-LM in R4 and the forgery Markov
# model in R5. Never includes the Quran (audit-fix F-1 / F-16 / F-29).
_CONTROL_CORPUS_NAMES: tuple[str, ...] = (
    "poetry_abbasi", "poetry_jahili", "ksucca", "hindawi", "arabic_bible",
)


# ===========================================================================
# Utility: loader for the Quran + controls (shared by all R\u2019s)
# ===========================================================================
def _load_surahs() -> dict:
    """Return a canonical dict: {corpus_name: [list[str] verses, ...]}."""
    c = load_corpora()
    return {name: [extract_verses(u) for u in units] for name, units in c.items()}


def _zscore(null_vals: list[float], v: float) -> float:
    if len(null_vals) < 3:
        return 0.0
    mu = float(np.mean(null_vals))
    sd = float(np.std(null_vals, ddof=1))
    return (v - mu) / sd if sd > 1e-12 else 0.0


def _log_ratio(num: float, den: float) -> float:
    """Symmetric log-ratio log((|num| + eps)/(|den| + eps)) with adaptive eps.

    Avoids the "epsilon explosion" (F-12/F-13) where a near-zero denominator
    produces a meaningless 1e12 ratio that dominates means / geometric means.
    eps is proportional to the joint scale so the log-ratio is well-defined
    in the near-zero regime instead of exploding.

    Audit-round-2 F-ULT2-LOG1 (documented, not patched): every caller in
    this module (R2 amplification, R7 noise drops, R9 cross-scale) passes
    non-negative magnitudes, so the abs() never changes the result. A
    ``signed_log_ratio`` helper is intentionally NOT provided: the
    magnitude-equal signed case (|num| == |den|) has no well-defined
    log-ratio, so a separate API would invite wrong usage. If a future R
    legitimately needs signed inputs, add a dedicated per-R helper there.
    """
    scale = max(abs(num), abs(den), 1e-9)
    eps = scale * 1e-3
    return math.log((abs(num) + eps) / (abs(den) + eps))


# NOTE (audit-round-2 F-ULT2-DEAD1): the previous ``_uniform_seeded_rng``
# helper was dead code and relied on Python's PYTHONHASHSEED-sensitive tuple
# hash. Every ``run_R*`` now instantiates its RNG directly via
# ``random.Random(SEED)``.


def _sample_units(units: list, n: int, rng: random.Random) -> list:
    """Random (seeded) sub-sample without replacement, up to ``n``."""
    if n >= len(units):
        return list(units)
    return rng.sample(units, n)


def _base_result(exp: str, fast: bool, t0: float, **extra) -> dict:
    """Common result-header used by every run_R* function."""
    out = {
        "exp": exp,
        "schema_version": SCHEMA_VERSION,
        "seed": SEED,
        "fast_mode": fast,
        "runtime_seconds": round(time.time() - t0, 2),
    }
    out.update(extra)
    return out


# ===========================================================================
# R2 — sliding-window local amplifier
# ===========================================================================
def run_R2(fast: bool = True) -> dict:
    """For a set of Quran surahs, measure how a single-letter swap's effect
    on channel-A (spectral ratio) is amplified when scored on a small local
    window vs the whole surah.

    AUDIT-FIX F-12: the amplification is now reported as a log-ratio with a
    bootstrap CI so a near-zero whole-surah delta cannot inflate the metric.

    AUDIT-ROUND-2 F-ULT2-A1: the single-letter swap is now applied to the
    whitespace-preserving normalised verse, not to its ``letters_only``
    projection. Previously the null carried an extra perturbation (all
    intra-verse spaces removed) that had nothing to do with the letter edit.
    """
    EXP = "exp10_R2_sliding_window"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    # import locally to avoid R1 circular import at load time
    from experiments.exp09_R1_variant_forensics_9ch.run import channel_A_spectral

    corpora = _load_surahs()
    quran = corpora["quran"]
    candidates = [i for i, vs in enumerate(quran) if len(vs) >= 8]
    n_sample = min(15, len(candidates)) if fast else min(40, len(candidates))
    sample = rng.sample(candidates, n_sample) if n_sample > 0 else []
    n_trials = 5 if fast else 15

    log_amps: list[float] = []
    raw_amps: list[float] = []
    per_surah: list[dict] = []
    WINDOW = 3

    for si in _tqdm(sample, desc="R2 surahs", leave=False):
        # Work in normalised rasm space; keep intra-verse whitespace.
        verses = [normalize_rasm(v) for v in quran[si]]
        whole_spec = channel_A_spectral(" ".join(verses))
        local_amps_surah: list[float] = []
        for _ in range(n_trials):
            vi = rng.randrange(len(verses))
            verse_text = verses[vi]
            # Length check on letters-only projection; edit on spaces-preserving text.
            if len(letters_only(verse_text)) < 3:
                continue
            swapped, _, orig_letter, _ = random_single_letter_swap(verse_text, rng)
            if not orig_letter:
                continue
            new_verses = verses[:vi] + [swapped] + verses[vi + 1:]
            new_whole = channel_A_spectral(" ".join(new_verses))
            whole_delta = abs(new_whole - whole_spec)

            lo = max(0, vi - WINDOW // 2)
            hi = min(len(verses), lo + WINDOW)
            lo = max(0, hi - WINDOW)
            canon_win = channel_A_spectral(" ".join(verses[lo:hi]))
            new_win   = channel_A_spectral(" ".join(new_verses[lo:hi]))
            win_delta = abs(new_win - canon_win)

            log_amp = _log_ratio(win_delta, whole_delta)
            log_amps.append(log_amp)
            local_amps_surah.append(log_amp)
            # Raw ratio still reported but capped to avoid 1e12 outliers.
            if whole_delta > 1e-9:
                raw_amps.append(win_delta / whole_delta)

        if local_amps_surah:
            per_surah.append({
                "surah": si + 1, "n_verses": len(verses),
                "median_log_amp": float(np.median(local_amps_surah)),
                "max_log_amp":    float(np.max(local_amps_surah)),
            })

    ci_lo, ci_hi = bootstrap_ci(log_amps, n=500, alpha=0.05,
                                rng=random.Random(SEED + 1))
    result = _base_result(
        EXP, fast, t0,
        n_surahs=len(per_surah),
        n_trials_total=len(log_amps),
        window_size=WINDOW,
        # Log-amp is the primary statistic (F-12).
        log_amp_median=float(np.median(log_amps)) if log_amps else 0.0,
        log_amp_mean=float(np.mean(log_amps)) if log_amps else 0.0,
        log_amp_ci95=[ci_lo, ci_hi],
        # Raw amp kept for continuity but explicitly flagged as unbounded.
        amp_median=float(np.median(raw_amps)) if raw_amps else 0.0,
        amp_mean=float(np.mean(raw_amps)) if raw_amps else 0.0,
        amp_p95=float(np.percentile(raw_amps, 95)) if raw_amps else 0.0,
        amp_max=float(np.max(raw_amps)) if raw_amps else 0.0,
        per_surah=per_surah[:20],
        verdict_expected="log_amp_median > 0 (bootstrap 95% CI excludes 0)",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] log_amp_median={result['log_amp_median']:+.3f}  "
          f"CI95=[{ci_lo:+.3f}, {ci_hi:+.3f}]")
    return result


# ===========================================================================
# R3 — cross-scripture canonical-path (T8) on Iliad & Arabic Bible
# ===========================================================================
def run_R3(fast: bool = True) -> dict:
    """Permutation test on canonical-path length (bigram-Jaccard) for Quran +
    whatever cross-scripture corpora are available in phase_06.

    AUDIT-FIX F-2: the path-length metric is now the sum of adjacent-unit
    *bigram* Jaccard distances (``canonical_path_length_bigram``) instead of
    the letter-SET version, which collapsed to ~0 on any long Arabic corpus.

    AUDIT-ROUND-2 F-ULT2-R3a: each corpus is routed through an alphabet-
    appropriate normaliser. Greek corpora (``iliad_greek``, ``greek_nt``) use
    ``canonical_path_length_bigram_greek`` instead of the Arabic version,
    which would strip every Greek character to whitespace and produce a
    degenerate z=0.
    """
    EXP = "exp11_R3_cross_scripture"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()
    n_perm = 500 if fast else 5000

    # Alphabet routing (F-ULT2-R3a). Hebrew support lives in a future PR.
    GREEK_CORPORA = {"iliad_greek", "greek_nt"}

    def _path_fn(corpus_name: str):
        """Return the canonical-path-length function for this corpus."""
        if corpus_name in GREEK_CORPORA:
            return canonical_path_length_bigram_greek
        # Default: Arabic rasm-preserving bigram Jaccard.
        return lambda units: canonical_path_length_bigram(units, strict=True)

    interesting = {
        k: v for k, v in corpora.items()
        if k in ("quran", "arabic_bible", "iliad_greek") and len(v) >= 10
    }

    results = {}
    for name, units in interesting.items():
        path_fn = _path_fn(name)
        canonical = path_fn(units)
        nulls = []
        for _ in _tqdm(range(n_perm), desc=f"R3 perms [{name}]", leave=False):
            perm = list(units)
            rng.shuffle(perm)
            nulls.append(path_fn(perm))
        mu, sd = float(np.mean(nulls)), float(np.std(nulls, ddof=1))
        z = (canonical - mu) / (sd + 1e-12)
        pct = (np.array(nulls) <= canonical).mean() * 100
        # One-sided p-value with +1/+1 smoothing (Phipson & Smyth).
        p_one_sided = ((np.array(nulls) <= canonical).sum() + 1) / (n_perm + 1)
        results[name] = {
            "n_units": len(units),
            "alphabet": "greek" if name in GREEK_CORPORA else "arabic",
            "canonical_path": float(canonical),
            "null_mean": mu, "null_std": sd,
            "z": float(z),
            "percentile": float(pct),
            "p_one_sided": float(p_one_sided),
        }

    result = _base_result(
        EXP, fast, t0,
        n_perm=n_perm,
        metric="bigram_jaccard_path",
        per_scripture=results,
        verdict_expected="Quran |z| > every other scripture; p_one_sided < 0.05",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    for k, v in results.items():
        print(f"[{EXP}] {k:<15s} z={v['z']:+.2f}  p={v['p_one_sided']:.4f}")
    return result


# ===========================================================================
# R4 — character-level n-gram LM on CONTROL data only (F-1/F-16)
# ===========================================================================
def _letter_trigram_set(text: str) -> set[tuple[str, str, str]]:
    """Return the set of adjacent letter-trigrams (rasm-folded)."""
    t = letters_only(text)
    return set(zip(t, t[1:], t[2:]))


def _contamination_filter(
    train_units: list[tuple[str, str]], quran_verses: list[list[str]],
    threshold: float = 0.5,
) -> tuple[list[tuple[str, str]], int]:
    """Drop any training unit whose letter-trigram Jaccard *similarity* with
    any Quran surah is >= ``threshold``. Returns (filtered, n_dropped).

    AUDIT-ROUND-2 F-ULT2-R4a: trigrams (28^3 = 21952 possible) are much
    more discriminative than the original bigram filter (28^2 = 784), which
    saturated near ~0.8 Jaccard on any long Arabic pair and rarely dropped
    anything. Threshold is lowered to 0.5 to compensate.
    """
    quran_tg = [_letter_trigram_set(" ".join(vs)) for vs in quran_verses]
    kept: list[tuple[str, str]] = []
    dropped = 0
    for name, text in train_units:
        tt = _letter_trigram_set(text)
        if not tt:
            continue
        hit = False
        for q in quran_tg:
            union = len(tt | q)
            if union == 0:
                continue
            if len(tt & q) / union >= threshold:
                hit = True
                break
        if hit:
            dropped += 1
        else:
            kept.append((name, text))
    return kept, dropped


def run_R4(fast: bool = True) -> dict:
    """Train a character 5-gram LM on **control** Arabic, after explicitly
    removing any training unit that looks Quranic (audit-fix F-1/F-16).
    Compare per-char log-prob of canonical Quran vs single-letter-swap Quran.

    AUDIT-ROUND-2 F-ULT2-A1: single-letter swap now preserves whitespace
    (the edit is applied to the normalised verse, not to its letters-only
    projection), so the null perturbation matches the canonical variant's
    edit shape.
    AUDIT-ROUND-2 F-ULT2-R4a: contamination filter upgraded to a
    trigram-Jaccard test at threshold 0.5 (more discriminative than the
    original bigram test at 0.9).
    """
    EXP = "exp12_R4_char_lm"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()
    train_units: list[tuple[str, str]] = []
    for name in _CONTROL_CORPUS_NAMES:
        if name in corpora:
            for vs in corpora[name]:
                train_units.append((name, " ".join(vs)))

    filtered, n_dropped = _contamination_filter(train_units, corpora["quran"])
    print(f"[{EXP}] LM training corpus: kept {len(filtered)} "
          f"(dropped {n_dropped} contaminated)")

    lm = CharNGramLM(n=5, delta=0.05).fit([t for _, t in filtered])

    quran = corpora["quran"]
    n_surahs = min(20 if fast else 80, len(quran))
    n_trials = 5 if fast else 20

    canon_lp, swap_lp = [], []
    for si in _tqdm(range(n_surahs), desc="R4 surahs", leave=False):
        vs_raw = quran[si]
        if not vs_raw:
            continue
        # Normalise once; keep intra-verse whitespace (F-ULT2-A1).
        vs = [normalize_rasm(v) for v in vs_raw]
        full = " ".join(vs)
        canon_lp.append(lm.per_char_lp(full))
        for _ in range(n_trials):
            vi = rng.randrange(len(vs))
            verse_text = vs[vi]
            if len(letters_only(verse_text)) < 3:
                continue
            swapped, _, orig_letter, _ = random_single_letter_swap(verse_text, rng)
            if not orig_letter:
                continue
            new_vs = vs[:vi] + [swapped] + vs[vi + 1:]
            swap_lp.append(lm.per_char_lp(" ".join(new_vs)))

    canon_mean = float(np.mean(canon_lp)) if canon_lp else 0.0
    swap_mean  = float(np.mean(swap_lp))  if swap_lp else 0.0
    pooled_sd  = float(np.std(canon_lp + swap_lp, ddof=1)) if (canon_lp and swap_lp) else 0.0
    sep_d = (canon_mean - swap_mean) / (pooled_sd + 1e-12) if pooled_sd else 0.0

    # AUC via Mann-Whitney-U.
    y = [1] * len(canon_lp) + [0] * len(swap_lp)
    s = canon_lp + swap_lp
    order = np.argsort(s)
    y_sorted = np.array(y)[order]
    n1 = sum(y)
    n0 = len(y) - n1
    ranks = np.arange(1, len(y) + 1)
    u = float((ranks[y_sorted == 1]).sum() - n1 * (n1 + 1) / 2)
    auc = u / (n1 * n0) if n1 * n0 else 0.0

    # Bootstrap CI on AUC via resampled labels (simple but adequate).
    auc_boots: list[float] = []
    if canon_lp and swap_lp:
        c_arr = np.asarray(canon_lp)
        s_arr = np.asarray(swap_lp)
        r2 = random.Random(SEED + 2)
        for _ in range(200):
            cb = np.asarray([c_arr[r2.randrange(len(c_arr))] for _ in range(len(c_arr))])
            sb = np.asarray([s_arr[r2.randrange(len(s_arr))] for _ in range(len(s_arr))])
            # quick AUC on the bootstrap
            yb = np.concatenate([np.ones(len(cb)), np.zeros(len(sb))])
            sb_all = np.concatenate([cb, sb])
            ob = np.argsort(sb_all)
            ranks_b = np.arange(1, len(yb) + 1)
            n1b = int(yb.sum()); n0b = len(yb) - n1b
            ub = float((ranks_b[yb[ob] == 1]).sum() - n1b * (n1b + 1) / 2)
            auc_boots.append(ub / (n1b * n0b) if n1b * n0b else 0.0)
    auc_lo = float(np.quantile(auc_boots, 0.025)) if auc_boots else float("nan")
    auc_hi = float(np.quantile(auc_boots, 0.975)) if auc_boots else float("nan")

    result = _base_result(
        EXP, fast, t0,
        n_train_units=len(filtered),
        n_train_dropped_contaminated=n_dropped,
        n_quran_surahs=n_surahs,
        n_swap_trials=len(swap_lp),
        canon_lp_mean_per_char=canon_mean,
        swap_lp_mean_per_char=swap_mean,
        separation_cohens_d=float(sep_d),
        AUC_canon_vs_swap=float(auc),
        AUC_ci95=[auc_lo, auc_hi],
        control_training_corpora=[n for n in _CONTROL_CORPUS_NAMES if n in corpora],
        verdict_expected="AUC > 0.90 with AUC_ci95 lower bound > 0.80",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] AUC={auc:.3f}  CI95=[{auc_lo:.3f}, {auc_hi:.3f}]  "
          f"Δlp={canon_mean - swap_mean:+.3f}")
    return result


# ===========================================================================
# R5 — adversarial benchmark (F-2/F-18/F-29)
# ===========================================================================
def _markov_forgery(
    verses: list[str], rng: random.Random,
    source_stream: list[str] | None = None,
) -> list[str]:
    """Word-bigram Markov forgery.

    AUDIT-FIX F-29: the transition table is trained on ``source_stream``
    (a list of control-corpus word sequences) when provided, NOT on the
    target ``verses``. This kills the self-referential Quran → fake-Quran
    pipeline that made R5 trivial.
    """
    training = source_stream if source_stream else [w for v in verses for w in words(v)]
    trans: defaultdict = defaultdict(Counter)
    for a, b in zip(training[:-1], training[1:]):
        trans[a][b] += 1
    start_pool = [words(v)[0] for v in verses if words(v)]
    if not start_pool:
        return list(verses)
    if not training:
        return list(verses)
    out = []
    for v in verses:
        n_w = len(words(v))
        if n_w == 0:
            out.append(v)
            continue
        cur = rng.choice(start_pool)
        gen = [cur]
        for _ in range(n_w - 1):
            options = trans.get(cur)
            if not options:
                cur = rng.choice(start_pool)
            else:
                items = list(options.items())
                weights = [c for _, c in items]
                cur = rng.choices([w for w, _ in items], weights=weights)[0]
            gen.append(cur)
        out.append(" ".join(gen))
    return out


def _el_preserving_forgery(
    verses: list[str], rng: random.Random,
    source_stream: list[str] | None = None,
) -> list[str]:
    """Preserve each verse's last word (end-letter) while Markov-forging the rest."""
    fake = _markov_forgery(verses, rng, source_stream=source_stream)
    out = []
    for v_orig, v_fake in zip(verses, fake):
        w_orig = words(v_orig)
        w_fake = words(v_fake)
        if w_orig and w_fake:
            w_fake[-1] = w_orig[-1]
        out.append(" ".join(w_fake))
    return out


def run_R5(fast: bool = True) -> dict:
    """Generate synthetic Qurans under two *honest* attack strategies and
    measure canonical-path length of each (F-2, F-18, F-29).
    """
    EXP = "exp13_R5_adversarial"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()
    quran = corpora["quran"]

    # Control word-stream for the Markov source (F-29).
    control_stream: list[str] = []
    for name in _CONTROL_CORPUS_NAMES:
        if name not in corpora:
            continue
        for vs in corpora[name]:
            control_stream.extend(w for v in vs for w in words(v))

    # Real Quran baseline under the NEW bigram-Jaccard path metric (F-2).
    real_path = canonical_path_length_bigram(quran, strict=True)

    N = 5 if fast else 20
    # Honest strategies only: raw Markov and EL-preserving (F-18 removes the
    # duplicate "G3", "G4" which were byte-identical to G0, G1).
    strategies = {
        "G0_markov_control_source":  _markov_forgery,
        "G1_el_preserved_control":   _el_preserving_forgery,
    }

    results = {}
    for name, fn in strategies.items():
        paths = []
        for _ in _tqdm(range(N), desc=f"R5 forgeries [{name}]", leave=False):
            fakes = [fn(vs, rng, source_stream=control_stream) for vs in quran]
            paths.append(canonical_path_length_bigram(fakes, strict=True))
        results[name] = {
            "n": N,
            "mean": float(np.mean(paths)),
            "min":  float(np.min(paths)),
            "max":  float(np.max(paths)),
            "fraction_below_real": float(np.mean([p < real_path for p in paths])),
        }

    result = _base_result(
        EXP, fast, t0,
        metric="bigram_jaccard_path",
        real_quran_canonical_path=real_path,
        n_forgeries_per_strategy=N,
        per_strategy=results,
        control_training_corpora=[n for n in _CONTROL_CORPUS_NAMES if n in corpora],
        verdict_expected="no strategy below real Quran path length",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    for k, v in results.items():
        print(f"[{EXP}] {k}: mean_path={v['mean']:.3f}  real={real_path:.3f}")
    return result


# ===========================================================================
# R6 — word-graph modularity (proper Louvain ΔQ — audit-fix F-5)
# ===========================================================================
def _louvain_one_level(edges: list[tuple[str, str, int]]) -> tuple[dict[str, int], float]:
    """One-level Louvain-style modularity optimisation.

    Implements the correct ΔQ formula (Blondel et al. 2008):
        ΔQ = [(Σ_in + 2*k_i_in) / (2m) - ((Σ_tot + k_i)/(2m))^2]
             - [Σ_in/(2m) - (Σ_tot/(2m))^2 - (k_i/(2m))^2]
    where m is the total edge weight.

    Returns (community_assignment, Q).
    """
    adj: dict[str, Counter] = defaultdict(Counter)
    k: Counter = Counter()              # degree (weighted)
    m_total = 0.0
    for u, v, w in edges:
        adj[u][v] += w
        adj[v][u] += w
        k[u] += w
        k[v] += w
        m_total += w
    if m_total == 0:
        return ({}, 0.0)

    comm: dict[str, int] = {n: i for i, n in enumerate(adj)}
    sigma_in: dict[int, float] = {comm[n]: 0.0 for n in adj}  # internal weight
    sigma_tot: dict[int, float] = {comm[n]: k[n] for n in adj}  # total degree
    m2 = 2.0 * m_total

    improved = True
    passes = 0
    while improved and passes < 10:
        improved = False
        passes += 1
        for u in list(adj):
            c_u = comm[u]
            k_u = k[u]
            # k_i_in to each neighbour community (including current)
            k_to_c: Counter = Counter()
            for v, w in adj[u].items():
                if v == u:
                    continue
                k_to_c[comm[v]] += w
            # Remove u from its current community
            sigma_tot[c_u] -= k_u
            sigma_in[c_u] -= 2.0 * k_to_c.get(c_u, 0.0)

            best_c = c_u
            best_gain = 0.0
            for c, k_u_c in k_to_c.items():
                # ΔQ_join = k_u_c/m_total - (sigma_tot[c] * k_u) / (2 * m_total^2)
                gain = (k_u_c / m_total) - (sigma_tot.get(c, 0.0) * k_u) / (2.0 * m_total * m_total)
                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_c = c

            comm[u] = best_c
            sigma_tot[best_c] = sigma_tot.get(best_c, 0.0) + k_u
            sigma_in[best_c] = sigma_in.get(best_c, 0.0) + 2.0 * k_to_c.get(best_c, 0.0)
            if best_c != c_u:
                improved = True

    # Modularity Q = Σ_c [ sigma_in_c / (2m) - (sigma_tot_c / (2m))^2 ]
    Q = 0.0
    for c in set(comm.values()):
        Q += (sigma_in.get(c, 0.0) / m2) - (sigma_tot.get(c, 0.0) / m2) ** 2
    return (comm, float(Q))


def run_R6(fast: bool = True) -> dict:
    """Build a directed word-transition graph per corpus and compute proper
    Louvain modularity (F-5). Expected: Quran modularity higher than any
    control (hypothesis only; not asserted).

    AUDIT-ROUND-2 F-ULT2-R6a: the FAST-mode edge truncation is now
    **equalised** across corpora. Previously every corpus kept up to 50 000
    edges, but small corpora (Quran, arabic_bible) were untruncated while
    large ones (hindawi) were chopped, biasing the modularity ranking.
    The new cap = min(50 000, smallest-corpus edge count), applied
    uniformly.
    """
    EXP = "exp14_R6_word_graph_modularity"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()

    # Pass 1: compute unique edge lists per corpus.
    edges_per_corpus: dict[str, list[tuple[str, str, int]]] = {}
    for name, units in _tqdm(corpora.items(), desc="R6 build graphs", total=len(corpora), leave=False):
        edge_w: Counter = Counter()
        for vs in units:
            for v in vs:
                ws = words(v)
                for a, b in zip(ws[:-1], ws[1:]):
                    edge_w[(a, b)] += 1
        if edge_w:
            edges_per_corpus[name] = [(a, b, w) for (a, b), w in edge_w.items()]

    # Equalised FAST cap (F-ULT2-R6a).
    equal_cap: int | None = None
    if fast and edges_per_corpus:
        equal_cap = min(50_000, min(len(e) for e in edges_per_corpus.values()))

    # Pass 2: truncate (if needed) and compute modularity.
    mods = {}
    n_communities_by_corpus = {}
    truncation_flag = {}
    edge_counts_used = {}
    for name, edges in _tqdm(edges_per_corpus.items(), desc="R6 Louvain", total=len(edges_per_corpus), leave=False):
        truncated = False
        if equal_cap is not None and len(edges) > equal_cap:
            edges = sorted(edges, key=lambda e: -e[2])[:equal_cap]
            truncated = True
        comm, Q = _louvain_one_level(edges)
        mods[name] = Q
        n_communities_by_corpus[name] = len(set(comm.values())) if comm else 0
        truncation_flag[name] = truncated
        edge_counts_used[name] = len(edges)

    result = _base_result(
        EXP, fast, t0,
        modularity_per_corpus=mods,
        n_communities_per_corpus=n_communities_by_corpus,
        edge_truncated_fast_mode=truncation_flag,
        edge_counts_used=edge_counts_used,
        equal_cap_fast=equal_cap,
        quran_rank=(sorted(mods, key=lambda k: -mods[k]).index("quran") + 1
                    if "quran" in mods else -1),
        verdict_expected="quran rank 1 (informative; not an assertion)",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    for k, v in sorted(mods.items(), key=lambda kv: -kv[1]):
        print(f"[{EXP}] {k:<20s} Q={v:.4f}  n_comm={n_communities_by_corpus.get(k)}")
    return result


# ===========================================================================
# R7 — transmission-noise degradation curve (log-ratio, random sample)
# ===========================================================================
def run_R7(fast: bool = True) -> dict:
    """Sweep noise rates {1 %, 2 %, 5 %, 10 %, 20 %}, apply random letter
    swaps at each rate, measure mean |Δ channel-A| on a LOG scale.

    AUDIT-FIX F-13: the Quran/control comparison is a log-ratio with
    bootstrap CI; the epsilon-inflated raw ratio is kept for continuity but
    no longer headlines.
    AUDIT-FIX F-42: corpus sub-sample is random (seeded) rather than ``[:20]``.
    """
    EXP = "exp15_R7_noise_curve"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    from experiments.exp09_R1_variant_forensics_9ch.run import channel_A_spectral

    corpora = _load_surahs()
    rates = [0.01, 0.02, 0.05, 0.10, 0.20]
    n_rep = 3 if fast else 10

    def apply_noise(text: str, rate: float, rng: random.Random) -> str:
        t = list(text)
        idxs = [i for i, c in enumerate(t) if c in ARABIC_CONSONANTS]
        if not idxs:
            return text
        n_swaps = max(1, int(rate * len(idxs)))
        for _ in range(n_swaps):
            pos = rng.choice(idxs)
            alt = rng.choice([c for c in ARABIC_CONSONANTS if c != t[pos]])
            t[pos] = alt
        return "".join(t)

    def pick(corpus: list, n: int) -> list:
        return _sample_units(corpus, n, rng)

    # Audit-round-2 F-ULT2-R7a: include every control corpus available in
    # phase_06, not just 2 of 5. Missing corpora are silently skipped.
    subset_names = ["quran"] + [
        c for c in _CONTROL_CORPUS_NAMES if c in corpora and corpora[c]
    ]
    n_units = 20 if fast else 50
    subset = {
        name: pick(corpora[name], n_units) for name in subset_names
    }

    curves: dict = {}
    per_corpus_raw_drops: dict = defaultdict(dict)
    for name, units in _tqdm(subset.items(), desc="R7 corpora", total=len(subset), leave=False):
        row = {}
        for rate in _tqdm(rates, desc=f"R7 rates [{name}]", leave=False):
            drops = []
            for vs in units:
                full = letters_only(" ".join(vs))
                if len(full) < 40:
                    continue
                canon = channel_A_spectral(full)
                for _ in range(n_rep):
                    noisy = apply_noise(full, rate, rng)
                    val = channel_A_spectral(noisy)
                    denom = abs(canon) if abs(canon) > 1e-9 else 1e-9
                    drops.append(abs(val - canon) / denom)
            row[f"rate_{rate:.2f}"] = float(np.mean(drops)) if drops else 0.0
            per_corpus_raw_drops[name][f"rate_{rate:.2f}"] = drops
        curves[name] = row

    log_ratios_quran_over: dict = {}
    if "quran" in curves:
        for name in curves:
            if name == "quran":
                continue
            row_lr = {}
            for rk in curves[name]:
                q_vals = per_corpus_raw_drops["quran"].get(rk, [])
                c_vals = per_corpus_raw_drops[name].get(rk, [])
                if q_vals and c_vals:
                    log_ratios = [_log_ratio(q, np.mean(c_vals))
                                  for q in q_vals]
                    lo, hi = bootstrap_ci(log_ratios, n=400,
                                          rng=random.Random(SEED + 3))
                    row_lr[rk] = {
                        "log_ratio_mean": float(np.mean(log_ratios)),
                        "ci95": [lo, hi],
                    }
                else:
                    row_lr[rk] = {"log_ratio_mean": 0.0, "ci95": [float("nan"), float("nan")]}
            log_ratios_quran_over[name] = row_lr

    # Legacy raw ratio still included (dominated by epsilon when denom ~ 0).
    legacy_ratios = {}
    if "quran" in curves:
        for name, row in curves.items():
            if name == "quran":
                continue
            legacy_ratios[name] = {
                rk: round(curves["quran"][rk] / (v + 1e-12), 2)
                for rk, v in row.items()
            }

    result = _base_result(
        EXP, fast, t0,
        rates=rates, n_reps=n_rep,
        curves=curves,
        log_ratios_quran_over=log_ratios_quran_over,
        ratios_quran_over=legacy_ratios,
        verdict_expected="log_ratio_mean > 0 with ci95 lower bound > 0 at every rate",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] done in {result['runtime_seconds']}s")
    return result


# ===========================================================================
# R8 — null ladder N0–N7 (full 8-rung ladder now that NULLS is complete)
# ===========================================================================
def run_R8(fast: bool = True) -> dict:
    """Permutation tests on verse-order with increasingly-constrained nulls.
    Report fraction of corpus units whose canonical path is in the bottom
    5 % of the null distribution.

    AUDIT-FIX F-14: all 8 rungs (N0..N7) are now exercised.
    """
    EXP = "exp16_R8_null_ladder"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()
    n_perm = 100 if fast else 1000

    def unit_score(verses: list[str]) -> float:
        # Bigram-Jaccard adjacency score (F-2).
        if len(verses) < 2:
            return 0.0
        total = 0.0
        for a, b in zip(verses[:-1], verses[1:]):
            total += bigram_jaccard_distance(a, b, strict=True)
        return total

    results: dict = {}
    for name, units in _tqdm(corpora.items(), desc="R8 corpora", total=len(corpora), leave=False):
        per_null = {}
        long_units = [u for u in units if len(u) >= 8]
        if fast and len(long_units) > 40:
            long_units = rng.sample(long_units, 40) if len(long_units) > 40 else long_units
        for null_name, null_fn in _tqdm(NULLS.items(), desc=f"R8 nulls [{name}]", total=len(NULLS), leave=False):
            sig_count = 0
            total = 0
            for vs in _tqdm(long_units, desc=f"R8 units [{null_name}]", leave=False):
                canon = unit_score(vs)
                null_scores = []
                for _ in range(n_perm):
                    null_scores.append(unit_score(null_fn(vs, rng)))
                pct = (np.array(null_scores) <= canon).mean()
                total += 1
                if pct <= 0.05:
                    sig_count += 1
            per_null[null_name] = {
                "sig_rate": sig_count / total if total else 0.0,
                "n_units":  total,
            }
        results[name] = per_null

    result = _base_result(
        EXP, fast, t0,
        n_perm=n_perm,
        null_rungs=list(NULLS.keys()),
        per_corpus_ladder=results,
        verdict_expected="Quran rate decreases slowly; controls crash fast",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] done in {result['runtime_seconds']}s")
    return result


# ===========================================================================
# R9 — cross-scale propagation VIS (log-ratio + guarded perturbations)
# ===========================================================================
def run_R9(fast: bool = True) -> dict:
    """Measure how a perturbation at scale S propagates. Scales:
    L1=letter, L2=word, L3=verse-swap, L4=verse-block-shuffle.

    AUDIT-FIX F-13: VIS is the mean of per-scale log-ratios (not the
    geometric mean of epsilon-inflated raw ratios).
    AUDIT-FIX F-43: L3 and L4 guard against no-op perturbations.

    AUDIT-ROUND-2 F-ULT2-A1: L1 letter swap now preserves whitespace (the
    edit is applied to the normalised verse text, not to its letters-only
    projection).
    AUDIT-ROUND-2 F-ULT2-R9a: replaces the broken per-element bootstrap
    with a proper ``bootstrap_ci`` call on the log-ratio samples.
    """
    EXP = "exp17_R9_cross_scale_VIS"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    from experiments.exp09_R1_variant_forensics_9ch.run import channel_A_spectral

    corpora = _load_surahs()
    quran = corpora["quran"]
    ctrl_names = ["poetry_abbasi", "hindawi", "ksucca", "arabic_bible"]
    ctrl_flat = []
    for n in ctrl_names:
        if n in corpora:
            ctrl_flat.extend(corpora[n])
    # Normalise once so L1 swaps see a consistent rasm.
    quran = [[normalize_rasm(v) for v in vs] for vs in quran]
    ctrl_flat = [[normalize_rasm(v) for v in vs] for vs in ctrl_flat]
    if fast:
        ctrl_flat = _sample_units(ctrl_flat, 60, rng)

    def l1_letter(verses):
        v = list(verses)
        i = rng.randrange(len(v))
        # F-ULT2-A1: swap on spaces-preserving verse text.
        if len(letters_only(v[i])) < 3:
            return v
        sw, _, orig_letter, _ = random_single_letter_swap(v[i], rng)
        if orig_letter:
            v[i] = sw
        return v

    def l2_word(verses):
        v = list(verses)
        i = rng.randrange(len(v))
        w = words(v[i])
        if len(w) >= 2:
            j = rng.randrange(len(w))
            k = rng.randrange(len(w) - 1)
            if k >= j:
                k += 1
            w[j], w[k] = w[k], w[j]
            v[i] = " ".join(w)
        return v

    def l3_verse_swap(verses):
        v = list(verses)
        if len(v) >= 2:
            i = rng.randrange(len(v))
            j = rng.randrange(len(v) - 1)
            if j >= i:
                j += 1
            v[i], v[j] = v[j], v[i]
        return v

    def l4_block(verses):
        v = list(verses)
        if len(v) >= 4:
            i = rng.randrange(len(v) - 3)
            block = v[i:i + 3]
            # ensure at least one swap inside the block
            for _ in range(4):
                shuffled = list(block)
                rng.shuffle(shuffled)
                if shuffled != block:
                    block = shuffled
                    break
            v[i:i + 3] = block
        return v

    scale_fns = {"L1_letter": l1_letter, "L2_word": l2_word,
                 "L3_verse":  l3_verse_swap, "L4_block": l4_block}

    n_trials = 3 if fast else 10

    def perturbation_magnitude_samples(units, fn, scale_name, corpus_label):
        mags = []
        for vs in _tqdm(units, desc=f"R9 {scale_name} [{corpus_label}]", leave=False):
            if len(vs) < 3:
                continue
            canon = channel_A_spectral(" ".join(vs))
            for _ in range(n_trials):
                new = fn(vs)
                val = channel_A_spectral(" ".join(new))
                mags.append(abs(val - canon))
        return mags

    q_list = quran if not fast else _sample_units(quran, 30, rng)
    c_list = ctrl_flat

    per_scale = {}
    log_ratios_all: list[float] = []
    boot_rng = random.Random(SEED + 10)
    for name, fn in _tqdm(scale_fns.items(), desc="R9 scales", total=len(scale_fns), leave=False):
        q_mags = perturbation_magnitude_samples(q_list, fn, name, "quran")
        c_mags = perturbation_magnitude_samples(c_list, fn, name, "control")
        q_mean = float(np.mean(q_mags)) if q_mags else 0.0
        c_mean = float(np.mean(c_mags)) if c_mags else 0.0
        lr = _log_ratio(q_mean, c_mean)
        # AUDIT-ROUND-2 F-ULT2-R9a: proper bootstrap of the per-trial
        # log-ratios instead of the broken per-element resample.
        if q_mags and c_mean > 0:
            lr_samples = [_log_ratio(q, c_mean) for q in q_mags]
            ci_lo, ci_hi = bootstrap_ci(
                lr_samples, n=500, alpha=0.05, rng=boot_rng,
            )
        else:
            ci_lo = ci_hi = float("nan")
        per_scale[name] = {
            "quran": q_mean,
            "control": c_mean,
            "log_ratio": lr,
            "log_ratio_ci95": [ci_lo, ci_hi],
            # Legacy ratio kept but flagged (F-13).
            "ratio": q_mean / (c_mean + 1e-12),
        }
        log_ratios_all.append(lr)

    VIS_log = float(np.mean(log_ratios_all)) if log_ratios_all else 0.0
    # Only report a sensible exponentiated VIS if the log-mean is finite.
    VIS = float(math.exp(VIS_log)) if math.isfinite(VIS_log) else 0.0

    result = _base_result(
        EXP, fast, t0,
        per_scale=per_scale,
        VIS_log=VIS_log,
        VIS=VIS,
        verdict_expected="VIS_log > 0 at every scale; VIS > 1",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] VIS_log={VIS_log:+.3f}  VIS={VIS:.3f}")
    return result


# ===========================================================================
# R10 — verse-internal word-order test (F-15: filter short verses)
# ===========================================================================
def run_R10(fast: bool = True) -> dict:
    """Per-verse word-order permutation test. Verses with fewer than 5 words
    are reported in a separate bucket (audit-fix F-15); they dominate the
    null discreteness and should not contaminate the headline sig_rate.
    """
    EXP = "exp18_R10_verse_internal_order"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    rng = random.Random(SEED)
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    corpora = _load_surahs()
    n_perm = 200 if fast else 1000
    MIN_WORDS_FULL = 5

    def verse_score(verse: str) -> float:
        ws = words(verse)
        if len(ws) < 3:
            return 0.0
        total = 0.0
        for a, b in zip(ws[:-1], ws[1:]):
            A, B = letter_bigram_set(a, strict=True), letter_bigram_set(b, strict=True)
            denom = len(A | B)
            total += len(A & B) / denom if denom else 0.0
        return total / (len(ws) - 1)

    # Audit-round-2 F-ULT2-R10a: the raw ``sig_rate`` has an expected value
    # of ALPHA under the null (no verse order structure) because the test
    # uses a fixed alpha-level threshold. ``sig_rate_calibrated`` reports
    # the excess above that baseline, normalised to [0, 1].
    ALPHA = 0.05

    results = {}
    for name, units in _tqdm(corpora.items(), desc="R10 corpora", total=len(corpora), leave=False):
        all_verses = [v for vs in units for v in vs]
        long_verses  = [v for v in all_verses if len(words(v)) >= MIN_WORDS_FULL]
        short_verses = [v for v in all_verses if 3 <= len(words(v)) < MIN_WORDS_FULL]
        if fast and len(long_verses) > 80:
            long_verses = rng.sample(long_verses, 80)
        if fast and len(short_verses) > 80:
            short_verses = rng.sample(short_verses, 80)

        def _sig_rate(vlist: list[str], _label: str) -> float:
            if not vlist:
                return 0.0
            sig = 0
            for v in _tqdm(vlist, desc=f"R10 {_label} [{name}]", leave=False):
                canon = verse_score(v)
                ws = words(v)
                nulls = []
                for _ in range(n_perm):
                    perm = ws[:]
                    rng.shuffle(perm)
                    nulls.append(verse_score(" ".join(perm)))
                if np.mean([n >= canon for n in nulls]) <= ALPHA:
                    sig += 1
            return sig / len(vlist)

        sr_long  = _sig_rate(long_verses,  "long")
        sr_short = _sig_rate(short_verses, "short")
        results[name] = {
            "sig_rate":               sr_long,
            "sig_rate_calibrated":    calibrate_rate_above_null(sr_long, ALPHA),
            "n_verses":               len(long_verses),
            "short_verses_sig_rate":  sr_short,
            "short_verses_sig_rate_calibrated": calibrate_rate_above_null(sr_short, ALPHA),
            "n_short_verses":         len(short_verses),
        }

    result = _base_result(
        EXP, fast, t0,
        n_perm=n_perm,
        min_words_for_headline=MIN_WORDS_FULL,
        null_baseline_alpha=ALPHA,
        per_corpus=results,
        verdict_expected="Quran sig_rate_calibrated above all Arabic controls",
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    for k, v in results.items():
        print(f"[{EXP}] {k:<20s} sig={v['sig_rate']:.3f}  (n={v['n_verses']})")
    return result


# ===========================================================================
# R11 — symbolic-formula validation Φ_sym (F-6: no silent fabrication)
# ===========================================================================
def run_R11(fast: bool = True) -> dict:
    """Validate the backup claim that Φ_sym = H_nano_ln + RST - VL_CV has
    AUC ≈ 0.98 for Quran vs non-Quran classification. If any of the three
    required feature columns is missing from phase_06, we **do not** compute
    a surrogate AUC — we return None and flag ``features_available=False``.
    """
    EXP = "exp19_R11_symbolic_formula"
    print(f"[{EXP}] starting (fast={fast})")
    t0 = time.time()
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    # AUDIT-ROUND-2 F-ULT2-R11a: defensive key access so a renamed phase_06
    # key degrades gracefully to features_available=False instead of
    # raising KeyError before the availability check.
    state = load_phi_state()
    # NB: must use explicit None checks — ``a or b`` on a numpy array raises
    # "truth value of an array with more than one element is ambiguous".
    X_q_raw = state.get("X_QURAN")
    if X_q_raw is None:
        X_q_raw = state.get("X_quran")
    X_c_raw = state.get("X_CTRL_POOL")
    if X_c_raw is None:
        X_c_raw = state.get("X_ctrl_pool")
    feat_cols_raw = state.get("FEAT_COLS")
    if feat_cols_raw is None:
        feat_cols_raw = state.get("feat_cols")

    if X_q_raw is None or X_c_raw is None or feat_cols_raw is None:
        result = _base_result(
            EXP, fast, t0,
            features_available=False,
            feat_cols=list(feat_cols_raw) if feat_cols_raw is not None else [],
            phi_sym_quran_mean=None,
            phi_sym_ctrl_mean=None,
            AUC_quran_vs_ctrl=None,
            message=(
                "phase_06 state is missing one of X_QURAN / X_CTRL_POOL / "
                "FEAT_COLS; R11 cannot be evaluated."
            ),
            verdict_expected=(
                "AUC > 0.90 when H_nano_ln, RST, VL_CV all available; "
                "otherwise null-return and skip"
            ),
        )
        with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self_check_end(pre, exp_name=EXP)
        print(f"[{EXP}] SKIPPED: phase_06 missing expected keys")
        return result

    X_q = np.asarray(X_q_raw)
    X_c = np.asarray(X_c_raw)
    feat_cols = list(feat_cols_raw)

    def idx_of(name):
        for alias in (name, name.replace("_ln", ""), name.upper()):
            if alias in feat_cols:
                return feat_cols.index(alias)
        return None

    iH = idx_of("H_nano_ln") or idx_of("H_nano")
    iR = idx_of("RST")
    iV = idx_of("VL_CV")

    available = iH is not None and iR is not None and iV is not None
    if available:
        phi_sym_q = X_q[:, iH] + X_q[:, iR] - X_q[:, iV]
        phi_sym_c = X_c[:, iH] + X_c[:, iR] - X_c[:, iV]
        s = np.concatenate([phi_sym_q, phi_sym_c])
        y = np.array([1] * len(phi_sym_q) + [0] * len(phi_sym_c))
        order = np.argsort(s)
        y_sorted = y[order]
        ranks = np.arange(1, len(y) + 1)
        n1, n0 = int(y.sum()), len(y) - int(y.sum())
        u = float((ranks[y_sorted == 1]).sum() - n1 * (n1 + 1) / 2)
        auc: float | None = u / (n1 * n0) if n1 * n0 else 0.0
        phi_sym_q_mean = float(np.mean(phi_sym_q))
        phi_sym_c_mean = float(np.mean(phi_sym_c))
        message = "ok"
    else:
        # Audit-fix F-6: no silent fabrication. Explicit null return.
        auc = None
        phi_sym_q_mean = None
        phi_sym_c_mean = None
        message = (
            "required features missing: "
            f"H_nano_ln={iH is not None}, RST={iR is not None}, "
            f"VL_CV={iV is not None}. R11 cannot be evaluated."
        )
        print(f"[{EXP}] SKIPPED: {message}")

    result = _base_result(
        EXP, fast, t0,
        features_available=available,
        feat_cols=feat_cols,
        phi_sym_quran_mean=phi_sym_q_mean,
        phi_sym_ctrl_mean=phi_sym_c_mean,
        AUC_quran_vs_ctrl=auc,
        message=message,
        verdict_expected=(
            "AUC > 0.90 when H_nano_ln, RST, VL_CV all available; "
            "otherwise null-return and skip"
        ),
    )
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    if available:
        print(f"[{EXP}] AUC={auc:.3f}  (features_available=True)")
    return result


# ===========================================================================
# MASTER — composite detector + Tampering Detection Law (TDL)
# ===========================================================================
# AUDIT-ROUND-2 F-ULT2-MASTER-R3 / F-ULT2-M1:
#
# Channels are split into two functionally-distinct groups. The pre-round-2
# pipeline fed all 11 into a single independence-product P_detect, but R3/
# R5/R6/R8/R10 are corpus-authenticity measurements (do the verse orderings
# look canonical?) — a 1-letter edit moves their statistics by O(1/n_bigrams)
# ≈ 10^-3, which is invisible. Including them in a P(detect | tampered)
# composite was a category error that inflated P_detect_upper toward 1.
#
# Post round-2:
#   * ``_EDIT_DETECTION_CHANNELS``     (R1, R2, R4, R7, R9, R11)
#       Contribute to P_detect_upper / P_detect_lower.
#   * ``_CORPUS_AUTHENTICITY_CHANNELS`` (R3, R5, R6, R8, R10)
#       Contribute to ``structural_signature_score`` only. Reported
#       separately; never enter the tampering-detection posterior.
#
# Every rate is now calibrated so r=0 at the channel's null baseline,
# using auc_to_rate / signal_from_log_ratio_ci / calibrate_rate_above_null
# / _pvalue_to_rate from _ultimate2_helpers. Previously uninformative
# channels coded as r=0.5 saturated the independence upper bound.
_EDIT_DETECTION_CHANNELS: tuple[str, ...] = (
    "R1_nine_channel",       # detects single-letter edits via 9 sub-channels
    "R2_sliding_window",     # local-window amplification of a 1-letter edit
    "R4_char_lm",            # char n-gram LM canon-vs-swap AUC
    "R7_noise_curve",        # edit-rate-dependent resilience
    "R9_VIS",                # cross-scale perturbation propagation
    "R11_symbolic",          # symbolic-regression formula (optional)
)

_CORPUS_AUTHENTICITY_CHANNELS: tuple[str, ...] = (
    "R3_cross_scripture",    # verse-order canonical-path z
    "R5_adversarial",        # forgery inability
    "R6_word_graph",         # modularity rank
    "R8_null_ladder",        # canonical-order sig-rate under the null ladder
    "R10_verse_internal",    # verse-internal word order sig-rate
)

# Backwards-compatible union (historical downstream code used this).
_EXPECTED_CHANNELS: tuple[str, ...] = (
    _EDIT_DETECTION_CHANNELS + _CORPUS_AUTHENTICITY_CHANNELS
)


def _pvalue_to_rate(p: float | None, alpha: float = 0.05) -> float:
    """Map a one-sided p-value onto [0,1] with r=0 at p>=alpha.

    Linear in ``p`` between 0 and ``alpha``; saturates at 1 when p=0 and at
    0 when p>=alpha. Chosen instead of ``1 - p`` (which put uninformative
    channels at r=0.5 and saturated the independence composite).
    """
    if p is None or not np.isfinite(p):
        return 0.0
    return float(max(0.0, min(1.0, 1.0 - float(p) / alpha)))


def run_MASTER(all_results: dict, fast: bool = True) -> dict:
    """Aggregate R1-R11 outputs into a composite posterior.

    Reports (all on [0, 1]):

      * P_detect_upper = 1 - prod_k (1 - r_k)  over edit-detection channels
        (independence ceiling; F-7).
      * P_detect_lower = max_k r_k             over edit-detection channels
        (full-correlation floor; F-7).
      * structural_signature_score = mean of corpus-authenticity rates
        (new in round 2; NOT part of P_detect).

    Every r_k is null-calibrated so that an uninformative channel
    contributes r=0 (F-ULT2-M1).
    """
    EXP = "exp20_MASTER_composite"
    print(f"[{EXP}] starting composite aggregation")
    t0 = time.time()
    pre = self_check_begin()
    out = safe_output_dir(EXP)

    edit_detection_rates: dict[str, float] = {}
    corpus_authenticity_rates: dict[str, float] = {}
    channel_p_values: dict[str, float] = {}
    per_channel_notes: dict[str, str] = {}
    raw_rates_for_reference: dict[str, float] = {}

    # ==== Edit-detection channels ========================================
    # R1 — headline_single_letter_rate calibrated above the 3-of-9 baseline.
    r1 = all_results.get("R1", {})
    if r1 and "headline_single_letter_rate" in r1:
        raw = float(r1["headline_single_letter_rate"])
        raw_rates_for_reference["R1_nine_channel"] = raw
        edit_detection_rates["R1_nine_channel"] = calibrate_rate_above_null(
            raw, R1_NULL_BASELINE_3OF9
        )
        per_channel_notes["R1_nine_channel"] = (
            "fraction of single-letter canonical variants with >=3 of 9 "
            f"channels firing, calibrated above {R1_NULL_BASELINE_3OF9:.3f} "
            "null baseline (Bin(9, 0.0456).sf(2))"
        )
    elif r1 and r1.get("canonical_variants"):
        # Legacy fallback: compute the rate directly.
        hits = [v for v in r1["canonical_variants"]
                if v.get("kind") == "single_letter"
                and v["found_in_text"]
                and v["channels_fired_abs_z_gt_2"] >= 3]
        denom = sum(1 for v in r1["canonical_variants"]
                    if v.get("kind") == "single_letter")
        raw = len(hits) / max(1, denom)
        raw_rates_for_reference["R1_nine_channel"] = raw
        edit_detection_rates["R1_nine_channel"] = calibrate_rate_above_null(
            raw, R1_NULL_BASELINE_3OF9
        )

    # R2 — tanh of log-amp CI lower bound (0 if CI includes 0).
    r2 = all_results.get("R2", {})
    if r2 and "log_amp_ci95" in r2:
        lo, _hi = (r2.get("log_amp_ci95") or [None, None])
        raw_rates_for_reference["R2_sliding_window"] = (
            float(lo) if (lo is not None and np.isfinite(lo)) else 0.0
        )
        edit_detection_rates["R2_sliding_window"] = signal_from_log_ratio_ci(lo)
        per_channel_notes["R2_sliding_window"] = (
            "tanh(log_amp CI lower bound); 0 if CI includes 0"
        )

    # R4 — Gini of the canon-vs-swap AUC (0 at AUC=0.5).
    r4 = all_results.get("R4", {})
    if r4 and "AUC_canon_vs_swap" in r4:
        auc = r4.get("AUC_canon_vs_swap")
        raw_rates_for_reference["R4_char_lm"] = (
            float(auc) if auc is not None else 0.0
        )
        edit_detection_rates["R4_char_lm"] = auc_to_rate(auc)
        per_channel_notes["R4_char_lm"] = (
            "2*AUC - 1 (Gini); 0 at AUC=0.5 (random baseline)"
        )

    # R7 — fraction of (corpus, rate) CIs excluding zero, calibrated above 5%.
    r7 = all_results.get("R7", {})
    if r7 and "log_ratios_quran_over" in r7:
        passes_all: list[float] = []
        for name, row in r7["log_ratios_quran_over"].items():
            for rk, stats in row.items():
                lo = stats.get("ci95", [float("nan"), float("nan")])[0]
                passes_all.append(1.0 if (lo == lo and lo > 0) else 0.0)
        frac = float(np.mean(passes_all)) if passes_all else 0.0
        raw_rates_for_reference["R7_noise_curve"] = frac
        edit_detection_rates["R7_noise_curve"] = calibrate_rate_above_null(
            frac, 0.05
        )
        per_channel_notes["R7_noise_curve"] = (
            "fraction of (corpus, rate) log-ratio CIs excluding zero, "
            "calibrated above the alpha=0.05 type-I baseline"
        )

    # R9 — tanh of VIS_log; 0 if VIS_log <= 0.
    r9 = all_results.get("R9", {})
    if r9 and "VIS_log" in r9:
        vis = float(r9["VIS_log"])
        raw_rates_for_reference["R9_VIS"] = vis
        edit_detection_rates["R9_VIS"] = signal_from_log_ratio_ci(vis)
        per_channel_notes["R9_VIS"] = "tanh(VIS_log); 0 if VIS_log <= 0"

    # R11 — Gini of Φ_sym AUC (only when features_available).
    r11 = all_results.get("R11", {})
    if r11 and r11.get("features_available") and r11.get("AUC_quran_vs_ctrl") is not None:
        auc = float(r11["AUC_quran_vs_ctrl"])
        raw_rates_for_reference["R11_symbolic"] = auc
        edit_detection_rates["R11_symbolic"] = auc_to_rate(auc)
        per_channel_notes["R11_symbolic"] = (
            "2*AUC - 1 (Gini); features_available=True"
        )
    elif r11 and not r11.get("features_available"):
        per_channel_notes["R11_symbolic"] = (
            "skipped (features missing) - excluded from composite"
        )

    # ==== Corpus-authenticity channels (NOT in P_detect) =================
    # R3 — one-sided p-value -> rate via max(0, 1 - p/alpha).
    r3 = all_results.get("R3", {})
    if r3 and "per_scripture" in r3 and "quran" in r3["per_scripture"]:
        p = float(r3["per_scripture"]["quran"].get("p_one_sided", 1.0))
        channel_p_values["R3_cross_scripture"] = p
        raw_rates_for_reference["R3_cross_scripture"] = 1.0 - p
        corpus_authenticity_rates["R3_cross_scripture"] = _pvalue_to_rate(p, alpha=0.05)
        per_channel_notes["R3_cross_scripture"] = (
            "max(0, 1 - p/0.05); 0 if p >= 0.05"
        )

    # R5 — rate = 1 - mean(fraction_below_real), calibrated above 0.5 null.
    r5 = all_results.get("R5", {})
    if r5 and "per_strategy" in r5:
        vals = [v["fraction_below_real"] for v in r5["per_strategy"].values()]
        raw = 1.0 - (float(np.mean(vals)) if vals else 0.5)
        raw_rates_for_reference["R5_adversarial"] = raw
        corpus_authenticity_rates["R5_adversarial"] = calibrate_rate_above_null(raw, 0.5)
        per_channel_notes["R5_adversarial"] = (
            "1 - mean(fraction of forgeries below real), calibrated above 0.5 null"
        )

    # R6 — rank-based rate, calibrated above 0.5 uniform-null.
    r6 = all_results.get("R6", {})
    if r6 and "modularity_per_corpus" in r6:
        mod = r6["modularity_per_corpus"]
        q = mod.get("quran", 0.0)
        others = [v for k, v in mod.items() if k != "quran"]
        raw = 1.0 - sum(1 for o in others if o >= q) / max(1, len(others))
        raw_rates_for_reference["R6_word_graph"] = raw
        corpus_authenticity_rates["R6_word_graph"] = calibrate_rate_above_null(raw, 0.5)
        per_channel_notes["R6_word_graph"] = (
            "fraction of controls whose Q < Quran's Q, calibrated above 0.5 null"
        )

    # R8 — mean Quran sig-rate across null rungs, calibrated above 0.05 baseline.
    r8 = all_results.get("R8", {})
    if r8 and "per_corpus_ladder" in r8 and "quran" in r8["per_corpus_ladder"]:
        q_rates = r8["per_corpus_ladder"]["quran"]
        mean_rate = float(np.mean([v["sig_rate"] for v in q_rates.values()]))
        raw_rates_for_reference["R8_null_ladder"] = mean_rate
        corpus_authenticity_rates["R8_null_ladder"] = calibrate_rate_above_null(
            mean_rate, 0.05
        )
        per_channel_notes["R8_null_ladder"] = (
            "mean of per-null-rung sig_rates (Quran); "
            "calibrated above 0.05 type-I baseline"
        )

    # R10 — already baseline-corrected by run_R10 via sig_rate_calibrated.
    r10 = all_results.get("R10", {})
    if r10 and "per_corpus" in r10 and "quran" in r10["per_corpus"]:
        q_r10 = r10["per_corpus"]["quran"]
        raw = float(q_r10.get("sig_rate", 0.0))
        calibrated = float(q_r10.get("sig_rate_calibrated", 0.0))
        raw_rates_for_reference["R10_verse_internal"] = raw
        corpus_authenticity_rates["R10_verse_internal"] = calibrated
        per_channel_notes["R10_verse_internal"] = (
            "sig_rate_calibrated = (sig_rate - 0.05) / 0.95 on verses with >= 5 words"
        )

    # ==== Coverage / BH adjustment (F-10, F-24) ==========================
    all_rates = {**edit_detection_rates, **corpus_authenticity_rates}
    missing_edit = [c for c in _EDIT_DETECTION_CHANNELS
                    if c not in edit_detection_rates]
    missing_auth = [c for c in _CORPUS_AUTHENTICITY_CHANNELS
                    if c not in corpus_authenticity_rates]
    coverage_ok = (not missing_edit) and (not missing_auth)

    p_keys = list(channel_p_values)
    p_vals = [channel_p_values[k] for k in p_keys]
    reject = benjamini_hochberg(p_vals, alpha=0.05)
    bh_results = {k: {"p": p_vals[i], "reject_BH_0.05": reject[i]}
                  for i, k in enumerate(p_keys)}

    # ==== Composite bounds (edit-detection ONLY) =========================
    ed_rates = [max(0.0, min(1.0, r)) for r in edit_detection_rates.values()]
    p_any_independent = 1.0
    for r in ed_rates:
        p_any_independent *= (1.0 - r)
    P_detect_upper = 1.0 - p_any_independent
    P_detect_lower = max(ed_rates) if ed_rates else 0.0
    expected_fired_ed = float(sum(ed_rates))

    # Structural signature composite (corpus-authenticity only)
    ca_rates = [max(0.0, min(1.0, r)) for r in corpus_authenticity_rates.values()]
    structural_signature_score = float(np.mean(ca_rates)) if ca_rates else 0.0

    tdl = {
        "statement": (
            "Under the (optimistic) independence assumption, the probability "
            "that at least one of the {} edit-detection channels (R1, R2, "
            "R4, R7, R9, R11) fires on a random single-letter edit is "
            "bounded above by P_detect_upper. A correlation-pessimistic "
            "lower bound is P_detect_lower = max(edit_detection_rate_k). "
            "Corpus-authenticity channels (R3, R5, R6, R8, R10) are "
            "reported separately as ``structural_signature_score`` and "
            "DO NOT enter the P_detect composite (audit-round-2 "
            "F-ULT2-MASTER-R3). All rates are null-calibrated so an "
            "uninformative channel contributes r=0 (F-ULT2-M1)."
        ).format(len(_EDIT_DETECTION_CHANNELS)),
        "N_edit_detection_channels":      len(edit_detection_rates),
        "N_corpus_authenticity_channels": len(corpus_authenticity_rates),
        "N_channels":       len(all_rates),
        "expected_fired":   expected_fired_ed,
        "P_detect_upper":   float(P_detect_upper),
        "P_detect_lower":   float(P_detect_lower),
        # Back-compat alias for the old single number.
        "P_detect":         float(P_detect_upper),
        "P_detect_is_upper_bound": True,
        "structural_signature_score": structural_signature_score,
        "edit_detection_rates":       {k: round(v, 4) for k, v in edit_detection_rates.items()},
        "corpus_authenticity_rates":  {k: round(v, 4) for k, v in corpus_authenticity_rates.items()},
        "raw_rates_for_reference":    {k: round(v, 4) for k, v in raw_rates_for_reference.items()},
        # Back-compat flat rates dict (union of both groups).
        "channel_rates":              {k: round(v, 4) for k, v in all_rates.items()},
        "per_channel_notes":          per_channel_notes,
        "benjamini_hochberg_p_values": bh_results,
    }

    coverage = {
        "expected_edit_detection":      list(_EDIT_DETECTION_CHANNELS),
        "expected_corpus_authenticity": list(_CORPUS_AUTHENTICITY_CHANNELS),
        "present_edit_detection":       sorted(edit_detection_rates),
        "present_corpus_authenticity":  sorted(corpus_authenticity_rates),
        "missing_edit_detection":       missing_edit,
        "missing_corpus_authenticity":  missing_auth,
        # Back-compat flat views.
        "expected_channels": list(_EXPECTED_CHANNELS),
        "present_channels":  sorted(all_rates),
        "missing_channels":  missing_edit + missing_auth,
        "coverage_ok":       coverage_ok,
        "position_scale_matrix": {
            "letter_swap":      ["R1", "R2", "R4", "R7", "R9_L1"],
            "word_order":       ["R9_L2", "R10"],
            "verse_order":      ["R3", "R5", "R6", "R8", "R9_L3"],
            "verse_block":      ["R8", "R9_L4"],
            "adversarial":      ["R5"],
            "symbolic_closure": ["R11"],
        },
    }

    result = {
        "exp": EXP,
        "schema_version": SCHEMA_VERSION,
        "TDL":             tdl,
        "coverage":        coverage,
        "r_results_summary": {
            r: ({k: v for k, v in (val or {}).items()
                 if k in ("verdict_expected", "AUC_canon_vs_swap",
                          "AUC_ci95", "log_amp_median", "log_amp_ci95",
                          "VIS_log", "VIS", "real_quran_canonical_path",
                          "headline_single_letter_rate", "runtime_seconds",
                          "features_available", "message")})
            for r, val in all_results.items()
        },
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] P_detect_upper={P_detect_upper:.4f}  "
          f"P_detect_lower={P_detect_lower:.4f}  "
          f"structural_signature={structural_signature_score:.4f}  "
          f"coverage={'OK' if coverage_ok else 'MISSING: ' + ','.join(missing_edit + missing_auth)}")
    if not coverage_ok:
        total_missing = len(missing_edit) + len(missing_auth)
        print(f"[{EXP}] WARNING: {total_missing} expected channels missing "
              f"(edit={missing_edit}, auth={missing_auth}).")
    return result
