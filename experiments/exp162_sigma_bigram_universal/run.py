"""experiments/exp162_sigma_bigram_universal/run.py
=====================================================
V3.23 candidate -- LENGTH-INDEPENDENT SYMBOLIC FORGERY DETECTOR.

This is the previously-pre-registered Path C from
docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md (`exp95i`),
never executed. Replaces compressor-based detectors (gzip, bz2, lzma,
zstd consensus from F53) with a pure-symbolic histogram-shift statistic.

Question:
    For 1-letter substitutions on the Quran's rasm-collapsed canonical
    text, does sigma_bigram = L1 distance between canon and variant
    bigram-frequency histograms detect every variant at a per-surah
    recall >= 0.99 with FPR <= 0.05?

Why this matters:
    The F53 multi-compressor consensus (R53) was retracted at full-114
    scope: aggregate K=2 = 0.190 vs target >= 0.999. Universal compressors
    have a Kolmogorov floor on emphatic-stop substitutions and a
    length-dependent dictionary-window blind spot. A *symbolic* detector
    has neither limitation: bigram frequencies move by exactly 4/N_bg
    per single-letter substitution, regardless of length.

Approach:
    1. Build a 28-consonant rasm-collapsed alphabet (drop hamza variants,
       drop alif vowel-carrier as a separate class).
    2. For each Quran surah and each of n_s_v1=27 single substitutions
       (one per non-self consonant, at a deterministic position chosen by
       hash-seeded RNG), compute the variant's bigram histogram and
       sigma = L1 distance to canon.
    3. For each of the 6 Arabic-peer control corpora, sample N_ctrl_pairs=
       5000 random length-stratified peer-pair sigmas to estimate the
       null distribution of "natural Arabic bigram drift".
    4. sigma_thr = 95th percentile of the control-pair null.
    5. recall_per_surah = fraction of 27 variant sigmas >= sigma_thr.
    6. FPR = ctrl_pair_sigmas at threshold by construction (= 0.05).
    7. Verdict: PASS at 99% if min_per_surah_recall >= 0.99.

Frozen constants:
    N_S_V1 = 27           (Latin-square style: 27 non-self consonants)
    SIGMA_PCT = 95         (FPR = 5%)
    N_CTRL_PAIRS = 5000
    SEED = 42

PREREG  : experiments/exp162_sigma_bigram_universal/PREREG.md
Inputs  : phase_06_phi_m.pkl (CORPORA dict, drift-relax env recommended)
Output  : results/experiments/exp162_sigma_bigram_universal/exp162_sigma_bigram_universal.json
"""
from __future__ import annotations

import io
import json
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402

EXP = "exp162_sigma_bigram_universal"
SEED = 42
N_S_V1 = 27
SIGMA_PCT = 95
N_CTRL_PAIRS = 5000

# ---- Rasm-collapsed 28-consonant alphabet --------------------------------
# Standard Hafs-rasm 28 letters (no hamza variants treated separately,
# alif kept as 1 letter). Hamza forms collapse to alif/ya carrier.
ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
LETTER_TO_IDX = {c: i for i, c in enumerate(ARABIC_28)}
N_LETTERS = len(ARABIC_28)
assert N_LETTERS == 28, f"expected 28 letters got {N_LETTERS}"

# Diacritic removal (Arabic combining marks)
DIACRITIC_RANGES = (
    (0x0610, 0x061A), (0x064B, 0x065F), (0x06D6, 0x06ED),
    (0x0670, 0x0670),
)
TATWEEL = "\u0640"

# Hamza collapse map (carrier -> base letter)
HAMZA_FOLD = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ئ": "ي", "ؤ": "و", "ء": "",
    "ة": "ه", "ى": "ي",
}


def is_diacritic(ch: str) -> bool:
    cp = ord(ch)
    for lo, hi in DIACRITIC_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def to_28_letters(text: str) -> str:
    """Strip diacritics, fold hamza variants, keep only the 28 consonants."""
    text = unicodedata.normalize("NFKD", text)
    out: list[str] = []
    for ch in text:
        if is_diacritic(ch) or ch == TATWEEL:
            continue
        if ch in HAMZA_FOLD:
            ch = HAMZA_FOLD[ch]
            if not ch:
                continue
        if ch in LETTER_TO_IDX:
            out.append(ch)
    return "".join(out)


def bigram_hist(s: str) -> np.ndarray:
    """Return 28x28 normalised bigram count matrix as a flat (784,) array."""
    if len(s) < 2:
        return np.zeros(N_LETTERS * N_LETTERS, dtype=np.float64)
    idx = np.array([LETTER_TO_IDX[c] for c in s], dtype=np.int32)
    flat_bg = idx[:-1] * N_LETTERS + idx[1:]
    counts = np.bincount(flat_bg, minlength=N_LETTERS * N_LETTERS).astype(np.float64)
    total = counts.sum()
    if total > 0:
        counts /= total
    return counts


def sigma_l1(h1: np.ndarray, h2: np.ndarray) -> float:
    return float(np.abs(h1 - h2).sum())


# ---------------------------------------------------------------------------

def run() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    out_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    quran_units = corpora["quran"]
    print(f"  quran: {len(quran_units)} surahs")

    # ---- 1. Build canonical 28-letter strings per surah --------------
    surah_canon: dict[str, str] = {}
    for u in quran_units:
        text = "".join(u.verses)
        s28 = to_28_letters(text)
        surah_canon[u.label] = s28

    # ---- 2. Build canonical bigram histograms --------------------------
    canon_hist: dict[str, np.ndarray] = {
        lbl: bigram_hist(s) for lbl, s in surah_canon.items()
    }

    # ---- 3. Generate 27 single-letter variants per surah ----------------
    # For each surah, deterministically choose one position and substitute
    # each of 27 non-self consonants -> 27 variants per surah.
    print(f"[{EXP}] Generating {N_S_V1} variants per surah ...")
    surah_variant_sigmas: dict[str, list[float]] = {}
    surah_variant_subs: dict[str, list[tuple[int, str, str, float]]] = {}
    for u in quran_units:
        s = surah_canon[u.label]
        if len(s) < 50:
            surah_variant_sigmas[u.label] = []
            continue
        h_canon = canon_hist[u.label]
        # deterministic per-surah RNG so substitutions are reproducible
        sub_rng = np.random.default_rng(
            int.from_bytes(u.label.encode(), "little") ^ SEED
        )
        # pick a single position per substitution (different per sub) so each
        # variant is a valid 1-letter edit. Position chosen uniformly.
        sigmas: list[float] = []
        recs: list[tuple[int, str, str, float]] = []
        for sub_letter in ARABIC_28:
            # pick any position whose current letter != sub_letter
            attempts = 0
            while attempts < 50:
                pos = int(sub_rng.integers(0, len(s)))
                if s[pos] != sub_letter:
                    break
                attempts += 1
            if attempts >= 50:
                continue
            variant = s[:pos] + sub_letter + s[pos + 1:]
            h_var = bigram_hist(variant)
            sigma = sigma_l1(h_canon, h_var)
            sigmas.append(sigma)
            recs.append((pos, s[pos], sub_letter, sigma))
        # Drop the self-substitution (sigma = 0) if any survived
        sigmas = [v for v in sigmas if v > 1e-12]
        surah_variant_sigmas[u.label] = sigmas
        surah_variant_subs[u.label] = recs

    # ---- 4. Build control null: pair sigmas across Arabic peers ----------
    print(f"[{EXP}] Building control null from peer-pair sigmas ...")
    arab_ctrl_keys = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                      "ksucca", "arabic_bible", "hindawi", "hadith_bukhari"]
    ctrl_units = []
    for k in arab_ctrl_keys:
        ctrl_units.extend(corpora.get(k, []))
    print(f"  total control units: {len(ctrl_units)}")
    ctrl_canon: dict[int, str] = {}
    ctrl_hists: dict[int, np.ndarray] = {}
    for i, u in enumerate(ctrl_units):
        text = "".join(u.verses)
        s28 = to_28_letters(text)
        if len(s28) >= 50:
            ctrl_canon[i] = s28
            ctrl_hists[i] = bigram_hist(s28)
    valid_idx = list(ctrl_hists.keys())
    print(f"  usable controls (>= 50 letters): {len(valid_idx)}")

    # Sample N_CTRL_PAIRS pairs; restrict to length-matched pairs
    # so the null reflects within-distribution drift, not cross-genre shifts.
    pair_sigmas = []
    for _ in range(N_CTRL_PAIRS):
        a, b = rng.choice(valid_idx, size=2, replace=False)
        # length stratification: redraw if length ratio is >5x
        for _ in range(5):
            la, lb = len(ctrl_canon[a]), len(ctrl_canon[b])
            if min(la, lb) > 0 and max(la, lb) / min(la, lb) <= 5.0:
                break
            a, b = rng.choice(valid_idx, size=2, replace=False)
        pair_sigmas.append(sigma_l1(ctrl_hists[a], ctrl_hists[b]))
    pair_sigmas = np.array(pair_sigmas)
    sigma_thr = float(np.percentile(pair_sigmas, SIGMA_PCT))
    print(f"  ctrl-pair sigma 95th percentile = {sigma_thr:.4f}  "
          f"(median {np.median(pair_sigmas):.4f}, mean {pair_sigmas.mean():.4f})")

    # ---- 5. Per-surah recall under sigma_thr -----------------------------
    per_surah_recall = {}
    n_skipped = 0
    for lbl, sigs in surah_variant_sigmas.items():
        if not sigs:
            n_skipped += 1
            continue
        rec = float(np.mean(np.array(sigs) >= sigma_thr))
        per_surah_recall[lbl] = {"n_variants": len(sigs),
                                 "recall_at_sigma_95": rec,
                                 "min_sigma": float(min(sigs)),
                                 "median_sigma": float(np.median(sigs)),
                                 "max_sigma": float(max(sigs))}

    recalls = np.array([d["recall_at_sigma_95"] for d in per_surah_recall.values()])
    aggregate_recall = float(recalls.mean())
    min_recall = float(recalls.min())
    n_at_999 = int((recalls >= 0.999).sum())
    n_at_99 = int((recalls >= 0.99).sum())
    n_at_95 = int((recalls >= 0.95).sum())
    fpr_observed = float((pair_sigmas >= sigma_thr).mean())  # by construction = 0.05

    if min_recall >= 0.999:
        verdict = "PASS_BIGRAM_UNIVERSAL_999"
    elif min_recall >= 0.99:
        verdict = "PASS_BIGRAM_UNIVERSAL_99"
    elif aggregate_recall >= 0.95 and n_at_99 >= 100:  # 100 of 114
        verdict = "PARTIAL_BIGRAM_P90_AGGREGATE"
    elif aggregate_recall >= 0.50:
        verdict = "WEAK_BIGRAM_AGGREGATE_HALF"
    else:
        verdict = "FAIL_BIGRAM_NOT_UNIVERSAL"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": ("Length-independent symbolic bigram-shift detector: "
                       "for every 1-letter substitution on rasm-collapsed Quran "
                       "text, sigma_L1(canon_bigram, variant_bigram) >= "
                       "ctrl-pair p95, at per-surah recall >= 0.99 with "
                       "FPR = 0.05 by construction."),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "N_LETTERS": N_LETTERS, "N_S_V1": N_S_V1,
            "SIGMA_PCT": SIGMA_PCT, "N_CTRL_PAIRS": N_CTRL_PAIRS,
            "SEED": SEED, "ARABIC_28": "".join(ARABIC_28),
        },
        "results": {
            "n_quran_surahs": len(quran_units),
            "n_skipped_short_surahs": n_skipped,
            "ctrl_pool_size": len(valid_idx),
            "sigma_threshold_95": sigma_thr,
            "ctrl_pair_sigma_summary": {
                "median": float(np.median(pair_sigmas)),
                "mean": float(pair_sigmas.mean()),
                "p25": float(np.percentile(pair_sigmas, 25)),
                "p75": float(np.percentile(pair_sigmas, 75)),
                "p95": sigma_thr,
                "p99": float(np.percentile(pair_sigmas, 99)),
            },
            "fpr_at_threshold_observed": fpr_observed,
            "aggregate_recall": aggregate_recall,
            "min_recall_per_surah": min_recall,
            "n_surahs_recall_geq_999": n_at_999,
            "n_surahs_recall_geq_99": n_at_99,
            "n_surahs_recall_geq_95": n_at_95,
            "per_surah_recall": per_surah_recall,
        },
    }
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  aggregate recall = {aggregate_recall:.4f}")
    print(f"  min per-surah recall = {min_recall:.4f}")
    print(f"  surahs recall>=0.999: {n_at_999}/114")
    print(f"  surahs recall>=0.99 : {n_at_99}/114")
    print(f"  surahs recall>=0.95 : {n_at_95}/114")
    print(f"  ctrl-FPR at threshold = {fpr_observed:.4f} (target 0.05)")
    print(f"  wall-time = {receipt['wall_time_s']:.2f} s")
    print(f"  receipt: {out_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    run()
