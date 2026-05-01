"""
exp29_cascade_product_code/run.py
=================================
Empirical verification of the cascade / product-code framing from the
2026-04-20 external review:

    P_composite = 1 - prod_k (1 - p_k)

where p_k is the single-channel detection probability of a single-letter
INTERNAL substitution at each of four scales:

    L0  character      H_char on 3-verse window centred on perturbed verse
    L1  word/verse     Phi_M 5D on 10-verse sliding window containing
                       perturbed verse
    L2  surah          Phi_M 5D on the full surah
    L3  corpus         Mahalanobis distance of perturbed surah from the
                       CANONICAL (unperturbed) Quran centroid

Protocol
    Target pool:   Band-A Quran surahs (Q: 15 <= n_verses <= 100, n=68).
    Perturbation:  pick a random NON-TERMINAL verse (so EL's terminal-
                   letter shortcut cannot catch it); within that verse
                   pick a random NON-BOUNDARY word (not first, not last
                   of the verse) with >= 3 letters; substitute a
                   non-terminal, non-initial letter with a different
                   Arabic consonant from the 28-letter alphabet. This
                   is by construction an 'internal' single-letter
                   substitution.
    N perturbations per surah:  N_PERT = 20 (1360 total perturbations).
    Null baseline per channel:  distribution of the channel statistic
                   under UNPERTURBED canonical variation (adjacent
                   windows, natural surah-to-surah spread).
    Threshold:     95th percentile of |null delta|  (alpha = 0.05).
    p_k:           fraction of perturbed surahs whose |perturbed delta|
                   exceeds the threshold (one-sided, "bigger than
                   natural noise").

Reads (integrity-checked):
    phase_06_phi_m.pkl   state['CORPORA']  (Band-A Quran units)

Writes ONLY under results/experiments/exp29_cascade_product_code/:
    exp29_cascade_product_code.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import features as ft  # noqa: E402

EXP = "exp29_cascade_product_code"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100
SEED = 42
N_PERT = 20                # perturbations per Quran surah
CTRL_N_UNITS = 200         # sample size of ctrl units for the ctrl-perturbation null
ALPHA = 0.05               # null-threshold quantile (95th percentile)
WINDOW_L0 = 3              # 3-verse window for L0 H_char
WINDOW_L1 = 10             # 10-verse sliding window for L1 Phi_M

ARABIC_CONS_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)


# --------------------------------------------------------------------------- #
# Primitives                                                                  #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _h_char_window(verses) -> float:
    """Total bigram entropy (intra-word, boundary-excluded) over a
    window of verses. Uses the same '#' boundary convention as exp27."""
    stream: list[str] = []
    first = True
    for v in verses:
        for w in _strip_d(v).split():
            letters = [c for c in w if c.isalpha()]
            if not letters:
                continue
            if not first:
                stream.append("#")
            stream.extend(letters)
            first = False
    if len(stream) < 4:
        return 0.0
    # H(bigram) - H(unigram) intra-word only
    bigrams = [
        (stream[i], stream[i + 1])
        for i in range(len(stream) - 1)
        if "#" not in (stream[i], stream[i + 1])
    ]
    unigrams = [c for c in stream if c != "#"]
    if not bigrams or not unigrams:
        return 0.0
    cb = Counter(bigrams); cu = Counter(unigrams)
    tb = sum(cb.values()); tu = sum(cu.values())
    hb = -sum((n / tb) * math.log2(n / tb) for n in cb.values())
    hu = -sum((n / tu) * math.log2(n / tu) for n in cu.values())
    return hb - hu


def _phi_m(x: np.ndarray, mu: np.ndarray, Sinv: np.ndarray) -> float:
    """Mahalanobis distance of x from mu under Sinv."""
    d = x - mu
    return float(math.sqrt(max(float(d @ Sinv @ d), 0.0)))


# --------------------------------------------------------------------------- #
# Single perturbation                                                          #
# --------------------------------------------------------------------------- #
def _apply_perturbation(verses, rng: random.Random) -> tuple[list[str], int] | None:
    """Return (new_verses, perturbed_verse_index) or None if no valid
    site found. The perturbation is a single NON-INITIAL, NON-TERMINAL
    letter in a NON-BOUNDARY word of a NON-TERMINAL verse."""
    nv = len(verses)
    if nv < 5:
        return None
    # Non-terminal verse: skip the last verse (EL shortcut) and the
    # first (BSM / opening effect). That keeps the perturbation deep
    # inside the surah.
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        word_choices = list(range(1, len(toks) - 1))
        rng.shuffle(word_choices)
        for wi in word_choices:
            w = toks[wi]
            letters = [c for c in w if c.isalpha()]
            if len(letters) < 3:
                continue
            # Internal letter positions in the original word (accounting
            # for non-alpha chars by building an index map).
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior_positions = alpha_positions[1:-1]
            if not interior_positions:
                continue
            pos = rng.choice(interior_positions)
            original = w[pos]
            candidates = [c for c in ARABIC_CONS_28 if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


# --------------------------------------------------------------------------- #
# Channel statistics                                                           #
# --------------------------------------------------------------------------- #
def _mahalanobis_norm(delta_feat: np.ndarray, Sinv: np.ndarray) -> float:
    """||delta||_M = sqrt(delta^T Sinv delta). Measures how many
    'natural control-pool standard deviations' the feature vector moved."""
    try:
        v = float(delta_feat @ Sinv @ delta_feat)
        return float(math.sqrt(max(v, 0.0)))
    except Exception:
        return 0.0


def _channel_stats(
    canon_verses, pert_verses, vi: int,
    canon_phi: np.ndarray, mu: np.ndarray, Sinv: np.ndarray,
    q_centroid: np.ndarray,
) -> dict[str, float]:
    """Compute |delta| on each of the 4 channels for one (canon, pert)
    pair with the perturbation at verse index vi.

    All Phi-channel deltas are Mahalanobis *norms* of the feature-vector
    difference (||f_p - f_c||_M), NOT differences of scalar Mahalanobis
    distances. The scalar-distance form is confounded: a feature vector
    can move perpendicular to the ctrl-centroid direction and leave the
    scalar distance unchanged even though the surah has shifted.
    """
    # L0: 3-verse window centred on vi
    lo = max(0, vi - WINDOW_L0 // 2)
    hi = min(len(canon_verses), lo + WINDOW_L0)
    lo = max(0, hi - WINDOW_L0)
    win_canon = canon_verses[lo:hi]
    win_pert = pert_verses[lo:hi]
    d_L0 = abs(_h_char_window(win_pert) - _h_char_window(win_canon))

    # L1: 10-verse sliding window; take max ||delta_features||_M across
    # all windows that CONTAIN the perturbed verse index vi.
    n = len(canon_verses)
    w = min(WINDOW_L1, n)
    max_delta = 0.0
    max_offset = None
    for start in range(max(0, vi - w + 1), min(n - w + 1, vi + 1)):
        end = start + w
        try:
            fc = ft.features_5d(canon_verses[start:end])
            fp = ft.features_5d(pert_verses[start:end])
            delta = _mahalanobis_norm(fp - fc, Sinv)
            if delta > max_delta:
                max_delta = delta
                max_offset = start
        except Exception:
            continue
    d_L1 = max_delta

    # L2: surah-level feature-vector drift, ||f_pert - f_canon||_M
    try:
        pert_phi = ft.features_5d(pert_verses)
        d_L2 = _mahalanobis_norm(pert_phi - canon_phi, Sinv)
    except Exception:
        pert_phi = canon_phi
        d_L2 = 0.0

    # L3: does the perturbed surah's 5D vector drift away from the
    # CANONICAL QURAN centroid by more than the natural Quran spread?
    # Measured as ||pert_phi - q_centroid||_M (scalar), with the null
    # being the distribution of this scalar under no perturbation (in
    # _null_distributions). This is the "did the surah fall out of the
    # Quran cloud" channel.
    d_L3 = _mahalanobis_norm(pert_phi - q_centroid, Sinv)

    return {
        "L0_hchar_3verse": d_L0,
        "L1_phi_m_10verse": d_L1,
        "L2_phi_m_surah": d_L2,
        "L3_phi_m_drift_from_canon": d_L3,
        "L1_window_start": max_offset if max_offset is not None else -1,
    }


# --------------------------------------------------------------------------- #
# Null baseline                                                                #
# --------------------------------------------------------------------------- #
def _null_distributions(
    units, mu: np.ndarray, Sinv: np.ndarray, rng: random.Random,
) -> tuple[dict, np.ndarray]:
    """Unperturbed natural variation per channel, plus the Quran centroid.

    Returns (null_dict, q_centroid) where null_dict has:
      L0: adjacent 3-verse windows in the same surah, |H_char(w) - H_char(w+1)|.
      L1: adjacent 10-verse sliding windows, ||f_a - f_b||_M.
      L2: pairwise surah-to-surah ||f_i - f_j||_M in Quran Band-A.
      L3: per-surah ||f_i - q_centroid||_M (natural spread around the Quran centroid).
    """
    L0_null = []
    L1_null = []
    feats: list[np.ndarray] = []
    for u in units:
        verses = u.verses
        n = len(verses)
        # L0: natural 3-verse H_char volatility
        for start in range(0, n - 2 * WINDOW_L0 + 1):
            a = verses[start:start + WINDOW_L0]
            b = verses[start + WINDOW_L0:start + 2 * WINDOW_L0]
            try:
                L0_null.append(abs(_h_char_window(a) - _h_char_window(b)))
            except Exception:
                pass
        # L1: natural 10-verse feature-vector drift
        if n >= 2 * WINDOW_L1:
            for start in range(0, n - 2 * WINDOW_L1 + 1):
                a = verses[start:start + WINDOW_L1]
                b = verses[start + WINDOW_L1:start + 2 * WINDOW_L1]
                try:
                    fa = ft.features_5d(a); fb = ft.features_5d(b)
                    L1_null.append(_mahalanobis_norm(fa - fb, Sinv))
                except Exception:
                    pass
        # surah features for L2, L3 nulls and the centroid
        try:
            feats.append(ft.features_5d(verses))
        except Exception:
            pass

    # Quran centroid (for L3 signal)
    q_centroid = np.asarray(feats).mean(axis=0) if feats else mu

    # L2 null: surah-to-surah feature drift
    L2_null = []
    for i in range(len(feats)):
        for j in range(i + 1, len(feats)):
            L2_null.append(_mahalanobis_norm(feats[i] - feats[j], Sinv))

    # L3 null: natural surah-to-Quran-centroid spread
    L3_null = [_mahalanobis_norm(f - q_centroid, Sinv) for f in feats]

    return (
        {
            "L0_hchar_3verse": L0_null,
            "L1_phi_m_10verse": L1_null,
            "L2_phi_m_surah": L2_null,
            "L3_phi_m_drift_from_canon": L3_null,
        },
        q_centroid,
    )


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # Build Arabic-ctrl-based Mahalanobis (mu, Sinv) on 5D features.
    # This is NOT the locked phase_06 inverse covariance (we don't want
    # to rely on a specific pickle schema), but it is the SAME protocol
    # (ctrl-pool centroid + pseudo-inverse covariance) used by
    # src/extended_tests.py:test_cv_phi_m.
    ctrl_vecs = []
    for name in ARABIC_CTRL:
        for u in _band_a(CORPORA.get(name, [])):
            try:
                ctrl_vecs.append(ft.features_5d(u.verses))
            except Exception:
                continue
    Xc = np.asarray(ctrl_vecs, dtype=float)
    if len(Xc) < 10:
        raise RuntimeError("insufficient Arabic ctrl feature vectors")
    mu = Xc.mean(axis=0)
    cov = np.cov(Xc.T) + 1e-9 * np.eye(Xc.shape[1])
    Sinv = np.linalg.pinv(cov)

    q_units = _band_a(CORPORA.get("quran", []))
    print(f"[{EXP}] ctrl vecs={len(Xc)}  Quran Band-A units={len(q_units)}  "
          f"N_PERT/unit={N_PERT}  seed={SEED}")

    # --------- null distributions ---------------------------------------- #
    rng_null = random.Random(SEED)
    null, q_centroid = _null_distributions(q_units, mu, Sinv, rng_null)
    thresholds = {}
    for k, v in null.items():
        if not v:
            thresholds[k] = float("inf")
            continue
        thresholds[k] = float(np.quantile(v, 1 - ALPHA))
    print(f"[{EXP}] 95%-null thresholds:")
    for k, t in thresholds.items():
        print(f"   {k:32s}  t = {t:.4f}  (n_null = {len(null[k])})")

    # --------- perturbations --------------------------------------------- #
    def _do_perturbations(units, rng_: random.Random, tag: str) -> list[dict]:
        """Apply N_PERT single-letter internal perturbations to every unit
        in `units`; return the channel-delta records."""
        canon_phi_cache: dict[str, np.ndarray] = {}
        for u in units:
            try:
                canon_phi_cache[u.label] = ft.features_5d(u.verses)
            except Exception:
                continue
        out_records: list[dict] = []
        for u in units:
            if u.label not in canon_phi_cache:
                continue
            canon_phi = canon_phi_cache[u.label]
            for pi in range(N_PERT):
                pair = _apply_perturbation(u.verses, rng_)
                if pair is None:
                    continue
                pert_verses, vi = pair
                stats = _channel_stats(
                    u.verses, pert_verses, vi, canon_phi, mu, Sinv,
                    q_centroid,
                )
                stats.update({
                    "pool": tag, "unit": u.label, "pert_idx": pi,
                    "verse_idx": vi, "n_verses": len(u.verses),
                })
                out_records.append(stats)
        return out_records

    rng_quran = random.Random(SEED + 1)
    rng_ctrl = random.Random(SEED + 2)
    rng_sanity = random.Random(SEED + 3)
    records = _do_perturbations(q_units, rng_quran, "quran")

    # Ctrl-perturbation null: apply the IDENTICAL perturbation procedure
    # to a sample of Arabic-ctrl Band-A units. This is the true
    # Quran-specificity null: does the perturbation shift the Quran's
    # channels MORE than it shifts the ctrl's channels?
    ctrl_units_all: list = []
    for name in ARABIC_CTRL:
        ctrl_units_all.extend(_band_a(CORPORA.get(name, [])))
    rng_sample = random.Random(SEED + 4)
    rng_sample.shuffle(ctrl_units_all)
    ctrl_units = ctrl_units_all[:CTRL_N_UNITS]
    print(f"[{EXP}] sampled ctrl pool: {len(ctrl_units)} units (of {len(ctrl_units_all)} Band-A ctrl)")
    ctrl_records = _do_perturbations(ctrl_units, rng_ctrl, "ctrl")

    # Sanity check: apply a BIG perturbation (reverse verse 1 text) to
    # every Quran surah. If L1/L2/L3 don't fire on this, the
    # implementation is broken. This is a positive control, not a
    # headline.
    def _big_perturb(verses, rng_):
        if len(verses) < 3:
            return None
        vi = rng_.randrange(1, len(verses) - 1)
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 2:
            return None
        rng_.shuffle(toks)  # shuffle ALL words in the verse
        new_verses = list(verses)
        new_verses[vi] = " ".join(toks)
        return new_verses, vi

    sanity_records = []
    sanity_cache = {u.label: ft.features_5d(u.verses) for u in q_units if True}
    for u in q_units:
        canon_phi = sanity_cache.get(u.label)
        if canon_phi is None:
            continue
        for pi in range(5):  # 5 big perturbations per surah
            pair = _big_perturb(u.verses, rng_sanity)
            if pair is None:
                continue
            pv, vi = pair
            s = _channel_stats(
                u.verses, pv, vi, canon_phi, mu, Sinv, q_centroid,
            )
            s.update({"pool": "sanity_big", "unit": u.label, "pert_idx": pi})
            sanity_records.append(s)

    # --------- detection rates ------------------------------------------ #
    channels = [
        "L0_hchar_3verse", "L1_phi_m_10verse",
        "L2_phi_m_surah", "L3_phi_m_drift_from_canon",
    ]

    def _rate_over_threshold(recs, ch, t):
        if not recs:
            return 0.0
        return sum(1 for r in recs if r[ch] > t) / len(recs)

    # p1: natural-variation null (kept for continuity with the original
    # design; high threshold, low rate).
    p_nat = {ch: _rate_over_threshold(records, ch, thresholds[ch])
             for ch in channels}

    # p2: ctrl-perturbation null -> 95th percentile of ctrl |delta|.
    # Detection = Quran |delta| > q95(ctrl |delta|). This is the real
    # Quran-specificity test: does the Quran respond to the edit MORE
    # than ctrl responds to the same edit?
    ctrl_thresh = {}
    for ch in channels:
        vals = [r[ch] for r in ctrl_records]
        ctrl_thresh[ch] = (
            float(np.quantile(vals, 1 - ALPHA)) if vals else float("inf")
        )
    p_ctrl = {ch: _rate_over_threshold(records, ch, ctrl_thresh[ch])
              for ch in channels}

    # p3: any-movement (epsilon=1e-9). Shows raw channel responsiveness,
    # ignoring magnitude. Should be ~100% for all channels (the edit
    # DID happen; the statistic SHOULD change by some amount).
    EPS_MOVE = 1e-9
    p_any = {ch: _rate_over_threshold(records, ch, EPS_MOVE) for ch in channels}

    # Mann-Whitney: is Quran |delta| stochastically LARGER than ctrl |delta|?
    from scipy import stats as _stats  # lazy import keeps cold-start fast
    mw_table = {}
    for ch in channels:
        q_vals = [r[ch] for r in records]
        c_vals = [r[ch] for r in ctrl_records]
        if len(q_vals) >= 2 and len(c_vals) >= 2:
            try:
                res = _stats.mannwhitneyu(q_vals, c_vals, alternative="greater")
                mw_table[ch] = {
                    "p_one_sided_greater": float(res.pvalue),
                    "quran_median": float(np.median(q_vals)),
                    "ctrl_median": float(np.median(c_vals)),
                    "quran_mean": float(np.mean(q_vals)),
                    "ctrl_mean": float(np.mean(c_vals)),
                }
            except Exception as e:
                mw_table[ch] = {"error": str(e)}
        else:
            mw_table[ch] = {"error": "insufficient samples"}

    # Sanity-check detection rate: big perturbations (word shuffle
    # within a verse). If the channels are wired correctly this should
    # be NON-ZERO (clearly higher than p_nat for single-letter edits).
    p_sanity = {ch: _rate_over_threshold(sanity_records, ch, thresholds[ch])
                for ch in channels}

    # Compose under each null choice for completeness
    def _composite(p_map):
        prod_miss = 1.0
        for ch in channels:
            prod_miss *= (1.0 - p_map[ch])
        return 1.0 - prod_miss

    P_composite_nat = _composite(p_nat)
    P_composite_ctrl = _composite(p_ctrl)

    # Pairwise-conditional detection under the ctrl-null (most meaningful)
    conditional = {}
    for i, ci in enumerate(channels):
        for cj in channels[i + 1:]:
            n_both = sum(
                1 for r in records
                if r[ci] > ctrl_thresh[ci] and r[cj] > ctrl_thresh[cj]
            )
            n_ci = sum(1 for r in records if r[ci] > ctrl_thresh[ci])
            cond = (n_both / n_ci) if n_ci else float("nan")
            conditional[f"P({cj} | {ci})"] = cond

    # --------- headline interpretation ---------------------------------- #
    best_single_ctrl = max(p_ctrl.values()) if p_ctrl else 0.0
    gain_over_best_ctrl = P_composite_ctrl - best_single_ctrl

    report = {
        "experiment": EXP,
        "schema_version": 2,
        "hypothesis": (
            "P_composite = 1 - prod_k (1 - p_k) under channel "
            "independence.  Empirical per-channel p_k is estimated on "
            "Band-A Quran single-letter internal substitutions using "
            "TWO null definitions: (a) natural variation across "
            "unperturbed windows/surahs (naive), and (b) IDENTICAL "
            "perturbation applied to Arabic-ctrl Band-A units "
            "(Quran-specificity null). Also reports Mann-Whitney "
            "p(Quran |delta| > ctrl |delta|) per channel."
        ),
        "config": {
            "seed": SEED, "n_pert_per_surah": N_PERT,
            "alpha_null_threshold": ALPHA,
            "window_L0_verses": WINDOW_L0,
            "window_L1_verses": WINDOW_L1,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "ctrl_n_units_sampled": CTRL_N_UNITS,
            "arabic_cons": "".join(ARABIC_CONS_28),
        },
        "n_quran_units": len(q_units),
        "n_perturbations_quran": len(records),
        "n_perturbations_ctrl": len(ctrl_records),
        "n_perturbations_sanity_big": len(sanity_records),
        "n_ctrl_vecs_for_Sinv": int(len(Xc)),
        "thresholds_natural_95q": thresholds,
        "thresholds_ctrl_perturbation_95q": ctrl_thresh,
        "null_sample_sizes": {k: len(v) for k, v in null.items()},

        "per_channel_p_detect_natural_null": p_nat,
        "per_channel_p_detect_ctrl_null": p_ctrl,
        "per_channel_p_any_movement": p_any,
        "per_channel_p_detect_sanity_big_vs_natural_null": p_sanity,

        "mannwhitney_quran_delta_vs_ctrl_delta": mw_table,

        "p_composite_natural_null": P_composite_nat,
        "p_composite_ctrl_null": P_composite_ctrl,
        "best_single_channel_ctrl_null": best_single_ctrl,
        "gain_over_best_single_ctrl_null": gain_over_best_ctrl,
        "conditional_pair_detections_ctrl_null": conditional,

        "feedback_estimates_2026_04_20": {
            "L0_hchar_3verse_estimate_range": [0.55, 0.70],
            "L1_phi_m_10verse_estimate": 0.20,
            "L2_phi_m_surah_estimate": 0.50,
            "L3_phi_m_drift_from_canon_estimate": 0.03,
            "p_composite_estimate_range": [0.82, 0.90],
        },
        "provenance": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "arabic_ctrl": ARABIC_CTRL,
            "hadith_quarantined": True,
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console --------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] n_perturbations_quran={len(records)}  "
          f"n_perturbations_ctrl={len(ctrl_records)}  "
          f"n_sanity_big={len(sanity_records)}")
    print(f"[{EXP}] --- any-movement rate (sanity: channel responsiveness) ---")
    for ch in channels:
        print(f"   {ch:32s}  p_any_move = {p_any[ch]:.3f}")
    print(f"[{EXP}] --- natural-null detection (threshold = 95q natural noise) ---")
    for ch in channels:
        feedback = report["feedback_estimates_2026_04_20"]
        est_key = next(
            (k for k in feedback if k.startswith(ch + "_estimate")), None
        )
        est = feedback[est_key] if est_key else None
        print(f"   {ch:32s}  p_nat = {p_nat[ch]:.3f}   (feedback est: {est})")
    print(f"[{EXP}] P_composite (natural null) = {P_composite_nat:.3f}")
    print(f"[{EXP}] --- ctrl-null detection (Quran-specificity test) ---")
    for ch in channels:
        print(f"   {ch:32s}  p_ctrl = {p_ctrl[ch]:.3f}   t_ctrl = {ctrl_thresh[ch]:.4f}")
    print(f"[{EXP}] P_composite (ctrl null)   = {P_composite_ctrl:.3f}  "
          f"(feedback est: {report['feedback_estimates_2026_04_20']['p_composite_estimate_range']})")
    print(f"[{EXP}] --- MW Quran|delta| > ctrl|delta| ---")
    for ch, row in mw_table.items():
        if "error" in row:
            print(f"   {ch:32s}  {row['error']}")
        else:
            print(f"   {ch:32s}  p = {row['p_one_sided_greater']:.3e}  "
                  f"Q_med={row['quran_median']:.4f}  C_med={row['ctrl_median']:.4f}")
    print(f"[{EXP}] --- sanity big-perturbation detection (should be HIGH) ---")
    for ch in channels:
        print(f"   {ch:32s}  p_big = {p_sanity[ch]:.3f}  (vs p_nat = {p_nat[ch]:.3f})")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
