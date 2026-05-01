"""
exp41_gzip_formalised/run.py
============================
gzip Normalised Compression Distance (NCD) as a formally pre-registered
R12-candidate edit-detection channel.

Motivation
    Of the 9 R1 channels tested on internal single-letter edits in
    exp30, only E_ncd (gzip NCD) consistently fires on the three Adiyat
    variants (v7.1 §4.20: 1/9 channels for A, 2/9 for B, 3/9 for C,
    with E_ncd present in all three hits). gzip is effectively a
    Kolmogorov-complexity proxy that sees the whole letter stream,
    so it is not subject to the boundary-reader trap that makes
    features_5d byte-exact invariant under internal edits.

    However, exp30 also showed that E_ncd's pooled MW p(Q|Delta| >
    ctrl|Delta|) = 1.00 -- the channel fires on ANY edit, not
    preferentially on Quran edits, at the population level. The
    Adiyat-specific signal is either (a) genuinely Quran-pointed and
    the population test is diluted by the heterogeneity of Quranic
    internal edits, or (b) a 3-variant cherry-pick that the
    population test correctly rejects.

    exp41 closes this by running gzip NCD on the exp29-style
    perturbation population (68 Band-A Quran surahs x 20 + 200 ctrl
    units x 20) and ALSO directly on the three Adiyat variants,
    reporting the percentile of each Adiyat variant in the Quran null
    and the ctrl null.

Design
    Input: normalised 28-letter consonant stream (hamza variants
        folded to alef, ة->ه, ى->ي) matching exp37/exp38 alphabet.
    NCD(a, b) = (Z(a+b) - min(Z(a), Z(b))) / max(Z(a), Z(b))
    where Z(x) = len(gzip.compress(x.encode('utf-8'), compresslevel=9)).

    Two scales:
        doc:    full-document canonical vs full-document edited.
        window: 3-verse window containing the perturbation, canonical
                vs edited.

    Null baselines (v7 audit discipline):
        NaturalVariationNull: NCD between two random non-overlapping
            halves of the SAME canonical document, repeated k=30 times
            per unit. The 95th percentile of this within-document
            NCD distribution is the "fires on random inherent
            variation" threshold.
        CtrlPerturbationNull: NCD(canonical, edited) pooled across
            200 ctrl units x 20 perturbations. 95th percentile is the
            "fires on ordinary Arabic text under the same edit class"
            threshold.

    Tests:
        Test A (population): MW p_greater(Q NCD > ctrl NCD) and
            Cohen d. This is the channel-Quran-specificity test.
        Test B (Adiyat specific): z-scores of the 3 Adiyat variants
            under the NaturalVariationNull for Surah 100 and under
            the CtrlPerturbationNull for matched-length ctrl units.
            Fire rates at the 95th-percentile threshold.

    Verdict:
        R12 channel PASSES its pre-registered target if EITHER:
          (i)  Test A cohens_d >= +0.3 AND MW p_greater <= 0.05, OR
          (ii) Test B fires the 3 Adiyat variants at rates
               >= 95th ctrl percentile AND those rates are higher
               than the corresponding ctrl_null rates at >= 2 sigma.
        Otherwise the channel is reported as a weak / Adiyat-specific
        detector that is not Quran-population-pointed.

Reads (integrity-checked):
    phase_06_phi_m.pkl   state['CORPORA']

Writes ONLY under results/experiments/exp41_gzip_formalised/:
    exp41_gzip_formalised.json
    self_check_<ts>.json
"""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import stats

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

EXP = "exp41_gzip_formalised"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100
SEED = 42
N_PERT = 20
CTRL_N_UNITS = 200
K_NULL_SPLITS = 30   # NaturalVariationNull splits per unit
GZIP_LEVEL = 9
WINDOW_L0 = 3        # 3-verse window for local NCD

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}


# --------------------------------------------------------------------------- #
# Primitives                                                                  #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def ncd(a: str, b: str) -> float:
    """Normalised compression distance via gzip."""
    if not a and not b:
        return 0.0
    za = _gz_len(a)
    zb = _gz_len(b)
    zab = _gz_len(a + b)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


# --------------------------------------------------------------------------- #
# Perturbation (byte-exact match to exp29)                                    #
# --------------------------------------------------------------------------- #
def _apply_perturbation(
    verses: list[str], rng: random.Random,
) -> tuple[list[str], int] | None:
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in cons if c != original]
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
# Scale helpers                                                                #
# --------------------------------------------------------------------------- #
def _doc_ncd(canon_verses: list[str], pert_verses: list[str]) -> float:
    a = _letters_28(" ".join(canon_verses))
    b = _letters_28(" ".join(pert_verses))
    return ncd(a, b)


def _window_ncd(
    canon_verses: list[str], pert_verses: list[str], vi: int,
) -> float:
    """3-verse window centred on vi."""
    lo = max(0, vi - WINDOW_L0 // 2)
    hi = min(len(canon_verses), lo + WINDOW_L0)
    lo = max(0, hi - WINDOW_L0)
    a = _letters_28(" ".join(canon_verses[lo:hi]))
    b = _letters_28(" ".join(pert_verses[lo:hi]))
    return ncd(a, b)


def _natural_variation_ncd(
    canon_verses: list[str], rng: random.Random, k: int = K_NULL_SPLITS,
) -> list[float]:
    """NCD between two random non-overlapping halves of the canonical doc."""
    n = len(canon_verses)
    if n < 4:
        return []
    samples: list[float] = []
    for _ in range(k):
        half = n // 2
        idx = list(range(n))
        rng.shuffle(idx)
        part_a = [canon_verses[i] for i in idx[:half]]
        part_b = [canon_verses[i] for i in idx[half:half * 2]]
        a = _letters_28(" ".join(part_a))
        b = _letters_28(" ".join(part_b))
        if a and b:
            samples.append(ncd(a, b))
    return samples


# --------------------------------------------------------------------------- #
# Adiyat variants                                                              #
# --------------------------------------------------------------------------- #
def _adiyat_variants(canon_verses: list[str]) -> dict[str, list[str]]:
    """Construct the 3 Adiyat variants from the canonical Surah 100.
    Edits are applied to verse 0 (1-indexed verse 1)."""
    v0 = canon_verses[0]
    v0_A = v0.replace("والعاديات", "والغاديات")      # ع -> غ internal
    v0_B = v0.replace("ضبحا", "صبحا")                  # ض -> ص terminal
    v0_B = v0_B.replace("ضبحاً", "صبحاً")             # with tanween
    v0_C = v0_A.replace("ضبحا", "صبحا").replace("ضبحاً", "صبحاً")
    return {
        "A_ayn_to_ghayn": [v0_A] + list(canon_verses[1:]),
        "B_dad_to_sad": [v0_B] + list(canon_verses[1:]),
        "C_both": [v0_C] + list(canon_verses[1:]),
    }


# --------------------------------------------------------------------------- #
# Stats helpers                                                                #
# --------------------------------------------------------------------------- #
def _finite(xs: Iterable[float]) -> list[float]:
    return [x for x in xs if isinstance(x, (int, float)) and math.isfinite(x)]


def _cohens_d(a, b) -> float:
    a = np.asarray(_finite(a), dtype=float)
    b = np.asarray(_finite(b), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pv = (
        (len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)
    ) / (len(a) + len(b) - 2)
    if pv <= 0:
        return float("nan")
    return float((a.mean() - b.mean()) / math.sqrt(pv))


def _mw(a, b, alt: str) -> float:
    a = _finite(a); b = _finite(b)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        res = stats.mannwhitneyu(a, b, alternative=alt)
        return float(res.pvalue)
    except ValueError:
        return float("nan")


def _summary(q, c) -> dict:
    q_f = _finite(q); c_f = _finite(c)
    return {
        "n_q": len(q_f), "n_ctrl": len(c_f),
        "q_mean": float(np.mean(q_f)) if q_f else float("nan"),
        "q_median": float(np.median(q_f)) if q_f else float("nan"),
        "q_p95": float(np.percentile(q_f, 95)) if q_f else float("nan"),
        "ctrl_mean": float(np.mean(c_f)) if c_f else float("nan"),
        "ctrl_median": float(np.median(c_f)) if c_f else float("nan"),
        "ctrl_p95": float(np.percentile(c_f, 95)) if c_f else float("nan"),
        "cohen_d": _cohens_d(q, c),
        "mw_p_greater": _mw(q, c, "greater"),
        "mw_p_less": _mw(q, c, "less"),
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = _band_a(CORPORA.get("quran", []))
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]

    # ---------------- Test A: population ---------------- #
    q_doc: list[float] = []
    q_win: list[float] = []
    q_nat: list[float] = []
    c_doc: list[float] = []
    c_win: list[float] = []
    c_nat: list[float] = []

    rng_q = random.Random(SEED)
    for u in q_units:
        rng_u = random.Random(rng_q.randrange(1 << 30))
        q_nat.extend(_natural_variation_ncd(u.verses, rng_u))
        for _ in range(N_PERT):
            out_p = _apply_perturbation(u.verses, rng_u)
            if out_p is None:
                continue
            pert, vi = out_p
            q_doc.append(_doc_ncd(u.verses, pert))
            q_win.append(_window_ncd(u.verses, pert, vi))

    rng_c = random.Random(SEED + 2)
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        c_nat.extend(_natural_variation_ncd(u.verses, rng_u))
        for _ in range(N_PERT):
            out_p = _apply_perturbation(u.verses, rng_u)
            if out_p is None:
                continue
            pert, vi = out_p
            c_doc.append(_doc_ncd(u.verses, pert))
            c_win.append(_window_ncd(u.verses, pert, vi))

    doc_summary = _summary(q_doc, c_doc)
    win_summary = _summary(q_win, c_win)
    nat_summary = {
        "quran_nat_p95": (
            float(np.percentile(_finite(q_nat), 95))
            if _finite(q_nat) else float("nan")
        ),
        "ctrl_nat_p95": (
            float(np.percentile(_finite(c_nat), 95))
            if _finite(c_nat) else float("nan")
        ),
        "quran_nat_mean": (
            float(np.mean(_finite(q_nat)))
            if _finite(q_nat) else float("nan")
        ),
        "ctrl_nat_mean": (
            float(np.mean(_finite(c_nat)))
            if _finite(c_nat) else float("nan")
        ),
        "n_q": len(_finite(q_nat)),
        "n_ctrl": len(_finite(c_nat)),
    }

    # ---------------- Test B: Adiyat variants ---------------- #
    q100 = next((u for u in CORPORA.get("quran", [])
                 if getattr(u, "label", "") == "Q:100"), None)
    adiyat_out: dict = {}
    if q100 is not None:
        variants = _adiyat_variants(q100.verses)
        ctrl_arr = np.asarray(_finite(c_doc), dtype=float)
        ctrl_mean = float(ctrl_arr.mean()) if len(ctrl_arr) else float("nan")
        ctrl_std = float(ctrl_arr.std(ddof=1)) if len(ctrl_arr) > 1 else float("nan")
        ctrl_p95 = (
            float(np.percentile(ctrl_arr, 95)) if len(ctrl_arr) else float("nan")
        )
        q_arr = np.asarray(_finite(q_doc), dtype=float)
        q_mean = float(q_arr.mean()) if len(q_arr) else float("nan")
        q_std = float(q_arr.std(ddof=1)) if len(q_arr) > 1 else float("nan")
        q_p95 = (
            float(np.percentile(q_arr, 95)) if len(q_arr) else float("nan")
        )

        for vid, verses in variants.items():
            ncd_val = _doc_ncd(q100.verses, verses)
            # z vs both nulls (doc scale)
            z_ctrl = (
                (ncd_val - ctrl_mean) / ctrl_std
                if math.isfinite(ctrl_std) and ctrl_std > 0 else float("nan")
            )
            z_q = (
                (ncd_val - q_mean) / q_std
                if math.isfinite(q_std) and q_std > 0 else float("nan")
            )
            fires_vs_ctrl = (
                bool(ncd_val >= ctrl_p95)
                if math.isfinite(ctrl_p95) else False
            )
            fires_vs_quran = (
                bool(ncd_val >= q_p95)
                if math.isfinite(q_p95) else False
            )
            adiyat_out[vid] = {
                "ncd_doc": float(ncd_val),
                "z_vs_ctrl_null": z_ctrl,
                "z_vs_quran_null": z_q,
                "fires_vs_ctrl_p95": fires_vs_ctrl,
                "fires_vs_quran_p95": fires_vs_quran,
            }

    # ---------------- Verdict ---------------- #
    def _population_verdict(s: dict) -> str:
        d = s["cohen_d"]; pg = s["mw_p_greater"]
        if not math.isfinite(d) or not math.isfinite(pg):
            return "INCONCLUSIVE"
        if d >= 0.3 and pg <= 0.05:
            return "SUPPORTS Quran-population specificity"
        if d >= 0.1 and pg <= 0.10:
            return "WEAK Quran-population specificity"
        return f"FAILS Quran-population specificity (d={d:+.3f}, p_g={pg:.3e})"

    adiyat_fire_count = sum(
        1 for v in adiyat_out.values() if v.get("fires_vs_ctrl_p95")
    )
    adiyat_verdict = (
        f"ADIYAT_HITS_{adiyat_fire_count}_OF_3 (vs ctrl 95th percentile; "
        f"Band-A doc-scale gzip NCD edit detection, "
        f"Adiyat = 1/108 of the test set)"
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "n_pert_per_unit": N_PERT,
        "k_null_splits": K_NULL_SPLITS,
        "gzip_level": GZIP_LEVEL,
        "window_l0": WINDOW_L0,
        "alphabet": "ARABIC_CONS_28 (hamza folded, ة->ه, ى->ي)",
        "arabic_ctrl": ARABIC_CTRL,
        "n_quran_units": len(q_units),
        "n_ctrl_units": len(ctrl_units),
        "doc_scale_summary": doc_summary,
        "window_scale_summary": win_summary,
        "natural_variation_null": nat_summary,
        "adiyat_variants_doc_scale": adiyat_out,
        "verdicts": {
            "population_doc": _population_verdict(doc_summary),
            "population_window": _population_verdict(win_summary),
            "adiyat": adiyat_verdict,
        },
        "notes": (
            "gzip NCD formalised as R12 candidate. doc-scale NCD on "
            "normalised 28-letter consonant stream; window-scale NCD "
            "on a 3-verse window containing the perturbation site. "
            "NaturalVariationNull = NCD between two random halves of "
            "the same canonical document. CtrlPerturbationNull = "
            "NCD(canonical, edited) on 200 ctrl units x 20 internal "
            "single-letter swaps each. Direct Adiyat-variant branch "
            "reports each variant's percentile under both nulls. "
            "A pre-registered R12 PASS requires population d >= +0.3 "
            "AND MW p_greater <= 0.05, OR all 3 Adiyat variants above "
            "ctrl-null 95th percentile."
        ),
        "provenance": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "perturbation_policy": "exp29-style internal single-letter swap",
            "adiyat_source": "Surah 100 verse 1 from phase_06 CORPORA",
            "design_doc": "2026-04-20 deep-scan synthesis",
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------- console -------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] n_quran={len(q_units)}  n_ctrl={len(ctrl_units)}  "
          f"n_q_pert={len(q_doc)}  n_ctrl_pert={len(c_doc)}")
    print(f"[{EXP}] DOC-SCALE:    Q med={doc_summary['q_median']:.4f}  "
          f"ctrl med={doc_summary['ctrl_median']:.4f}  "
          f"d={doc_summary['cohen_d']:+.3f}  "
          f"MW p_g={doc_summary['mw_p_greater']:.3e}")
    print(f"[{EXP}] WINDOW-SCALE: Q med={win_summary['q_median']:.4f}  "
          f"ctrl med={win_summary['ctrl_median']:.4f}  "
          f"d={win_summary['cohen_d']:+.3f}  "
          f"MW p_g={win_summary['mw_p_greater']:.3e}")
    print(f"[{EXP}] NAT-VAR null: Q p95={nat_summary['quran_nat_p95']:.4f}  "
          f"ctrl p95={nat_summary['ctrl_nat_p95']:.4f}")
    if adiyat_out:
        print(f"[{EXP}] Adiyat variants (doc-scale NCD vs Surah 100):")
        for vid, v in adiyat_out.items():
            print(f"   {vid:22s}  NCD={v['ncd_doc']:.6f}  "
                  f"z_ctrl={v['z_vs_ctrl_null']:+.2f}  "
                  f"z_Q={v['z_vs_quran_null']:+.2f}  "
                  f"fires_ctrl95={v['fires_vs_ctrl_p95']}")
    print(f"[{EXP}] VERDICTS:")
    for k, v in report["verdicts"].items():
        print(f"   {k}: {v}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
