"""exp121_trigram_verse_reorder — Closing the F70 7% gap via trigram-boundary.

Replays the exp117 verse-reorder battery (79 surahs × 100 swaps, SEED=42)
under a Form-5 trigram-with-verse-boundary detector. Tests whether trigrams
crossing inserted `#` boundary tokens close the residual 7% gap that F70
Form-4 (combined OR(EL_transition, gzip)) leaves.

Verdict: PASS_F70_gap_closed_by_trigram_boundary
       / PARTIAL_F70_gap_partially_closed
       / FAIL_F70_gap_not_closed_by_trigram

Prereg: experiments/exp121_trigram_verse_reorder/PREREG.md
Hypothesis ID: H76.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import random
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ----- Frozen constants (mirror PREREG) ------------------------------------
SEED = 42
MIN_VERSES = 20
N_SWAPS_PER_SURA = 100
RECALL_FLOOR = 0.95
BOUNDARY_TOKEN = "#"

EXP_NAME = "exp121_trigram_verse_reorder"
HYPOTHESIS_ID = "H76"

PREREG_PATH = ROOT / "experiments" / EXP_NAME / "PREREG.md"
PHASE_PKL = ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl"
RECEIPT_DIR = ROOT / "results" / "experiments" / EXP_NAME
RECEIPT_PATH = RECEIPT_DIR / f"{EXP_NAME}.json"

# Reuse exp117 alphabet definition exactly
ARABIC_CONSONANTS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
assert len(ARABIC_CONSONANTS) == 28
ALPH_SET = set(ARABIC_CONSONANTS)


# ----- Helpers --------------------------------------------------------------
def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


_DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)


def _strip_diacritics(text: str) -> str:
    return "".join(c for c in str(text) if c not in _DIAC)


def normalise_verse_skeleton(verse: str) -> str:
    """Strip diacritics + fold hamzas/ta-marbuta/alif-maksura. Keep only
    the 28 consonants and spaces."""
    text = _strip_diacritics(verse)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    replacements = {
        "\u0622": "\u0627",  # آ → ا
        "\u0623": "\u0627",  # أ → ا
        "\u0625": "\u0627",  # إ → ا
        "\u0671": "\u0627",  # ٱ → ا
        "\u0649": "\u064a",  # ى → ي
        "\u0629": "\u0647",  # ة → ه
        "\u0640": "",        # tatweel → ∅
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    keep = ALPH_SET | {" "}
    text = "".join(c if c in keep else "" for c in text)
    text = " ".join(text.split())  # collapse runs of whitespace
    return text


def boundary_tagged_sura_string(verses: list[str]) -> str:
    """Return the sūrah text as `#v1#v2#...#vn#` with normalised verse
    skeletons separated and bracketed by the boundary token."""
    skeletons = [normalise_verse_skeleton(v) for v in verses]
    return BOUNDARY_TOKEN + BOUNDARY_TOKEN.join(skeletons) + BOUNDARY_TOKEN


def trigram_histogram(text: str) -> Counter:
    """Counter of length-3 substrings."""
    if len(text) < 3:
        return Counter()
    return Counter(text[i:i + 3] for i in range(len(text) - 2))


def delta_trigram_boundary(verses_orig: list[str], verses_edit: list[str]) -> float:
    """L1 distance / 2 between trigram histograms of the boundary-tagged
    versions of the original and edited verse lists."""
    h1 = trigram_histogram(boundary_tagged_sura_string(verses_orig))
    h2 = trigram_histogram(boundary_tagged_sura_string(verses_edit))
    keys = set(h1) | set(h2)
    return sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys) / 2.0


# Re-import the exp117 EL-transition + gzip detectors so we can compute
# Form-6 = OR(F1, F3, F5) without re-implementing.
from experiments.exp117_verse_reorder_detector.run import (  # noqa: E402
    transition_matrix,
    delta_T_l1,
    delta_gzip_normalized,
)


# ----- Main -----------------------------------------------------------------
def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{EXP_NAME}] Loading {PHASE_PKL.relative_to(ROOT)}...")
    with open(PHASE_PKL, "rb") as f:
        state = pickle.load(f)
    inner = state.get("state", state)
    quran_units = inner["CORPORA"].get("quran")
    assert quran_units is not None, "quran units not found in checkpoint"

    rng = random.Random(SEED)

    per_sura: list[dict] = []
    n_total_swaps = 0
    n_form1_hits = 0
    n_form3_hits = 0
    n_form5_hits = 0
    n_form4_hits = 0   # OR(F1, F3) — exp117 baseline
    n_form6_hits = 0   # OR(F1, F3, F5)

    sum_delta_trigram = 0.0

    for unit in quran_units:
        verses = list(unit.verses) if hasattr(unit, "verses") else list(unit.get("verses", []))
        N = len(verses)
        if N < MIN_VERSES:
            continue
        label = str(unit.label) if hasattr(unit, "label") else str(unit.get("label", "?"))

        T_orig = transition_matrix(verses)

        all_pairs = [(i, j) for i in range(N) for j in range(i + 1, N)]
        n_pairs = min(N_SWAPS_PER_SURA, len(all_pairs))
        chosen = rng.sample(all_pairs, n_pairs)

        sura_form1, sura_form3, sura_form5, sura_form4, sura_form6 = 0, 0, 0, 0, 0
        sura_delta_trigram = 0.0
        for (i, j) in chosen:
            edited = list(verses)
            edited[i], edited[j] = edited[j], edited[i]
            T_edited = transition_matrix(edited)
            d_T = delta_T_l1(T_orig, T_edited)
            d_gz = delta_gzip_normalized(verses, edited)
            d_tri = delta_trigram_boundary(verses, edited)
            sura_delta_trigram += d_tri

            f1 = d_T > 0
            f3 = d_gz > 0
            f5 = d_tri > 0
            sura_form1 += f1
            sura_form3 += f3
            sura_form5 += f5
            sura_form4 += (f1 or f3)
            sura_form6 += (f1 or f3 or f5)

        per_sura.append({
            "label": label,
            "N_verses": N,
            "n_swaps_tested": n_pairs,
            "form1_recall": sura_form1 / n_pairs,
            "form3_recall": sura_form3 / n_pairs,
            "form5_recall": sura_form5 / n_pairs,
            "form4_combined_F1_or_F3_recall": sura_form4 / n_pairs,
            "form6_combined_F1_or_F3_or_F5_recall": sura_form6 / n_pairs,
            "form5_mean_delta_trigram": sura_delta_trigram / n_pairs,
        })
        n_total_swaps += n_pairs
        n_form1_hits += sura_form1
        n_form3_hits += sura_form3
        n_form5_hits += sura_form5
        n_form4_hits += sura_form4
        n_form6_hits += sura_form6
        sum_delta_trigram += sura_delta_trigram

    aggregate = {
        "form1_EL_transition_recall": n_form1_hits / n_total_swaps,
        "form3_gzip_recall": n_form3_hits / n_total_swaps,
        "form5_trigram_boundary_recall": n_form5_hits / n_total_swaps,
        "form4_combined_F1_or_F3_recall": n_form4_hits / n_total_swaps,
        "form6_combined_F1_or_F3_or_F5_recall": n_form6_hits / n_total_swaps,
        "form5_mean_delta_trigram": sum_delta_trigram / n_total_swaps,
        "n_total_swaps": n_total_swaps,
        "n_suras": len(per_sura),
    }

    # ----- Verdict ---------------------------------------------------------
    EXP117_FORM4_RECALL = 0.9298734177215192  # locked baseline from exp117
    delta_recall_vs_F70 = aggregate["form6_combined_F1_or_F3_or_F5_recall"] - EXP117_FORM4_RECALL

    form5_alone_pass = aggregate["form5_trigram_boundary_recall"] >= RECALL_FLOOR
    form6_pass = aggregate["form6_combined_F1_or_F3_or_F5_recall"] >= RECALL_FLOOR

    if form5_alone_pass or form6_pass:
        verdict = "PASS_F70_gap_closed_by_trigram_boundary"
    elif delta_recall_vs_F70 > 0.001:
        verdict = "PARTIAL_F70_gap_partially_closed"
    else:
        verdict = "FAIL_F70_gap_not_closed_by_trigram"

    verdict_reason = (
        f"Form-5 (trigram+boundary) standalone recall = {aggregate['form5_trigram_boundary_recall']:.4f}; "
        f"Form-6 (combined OR F1+F3+F5) recall = {aggregate['form6_combined_F1_or_F3_or_F5_recall']:.4f}; "
        f"exp117 baseline Form-4 = {EXP117_FORM4_RECALL:.4f}; "
        f"Δ_recall = {delta_recall_vs_F70:+.4f}; floor = {RECALL_FLOOR}."
    )

    audit_report = {
        "ok": True,
        "checks": {
            "n_suras_matches_exp117": len(per_sura) == 79,
            "n_total_swaps_matches_exp117": n_total_swaps == 7900,
            "form4_recall_matches_exp117": abs(
                aggregate["form4_combined_F1_or_F3_recall"] - EXP117_FORM4_RECALL
            ) < 1e-6,
        },
    }
    if not all(audit_report["checks"].values()):
        audit_report["ok"] = False
        verdict = "FAIL_audit_" + ",".join(
            k for k, v in audit_report["checks"].items() if not v
        )

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": HYPOTHESIS_ID,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "prereg_hash": sha256_file(PREREG_PATH),
        "frozen_constants": {
            "SEED": SEED,
            "MIN_VERSES": MIN_VERSES,
            "N_SWAPS_PER_SURA": N_SWAPS_PER_SURA,
            "RECALL_FLOOR": RECALL_FLOOR,
            "BOUNDARY_TOKEN": BOUNDARY_TOKEN,
            "ALPHABET_SIZE": 30,
        },
        "audit_report": audit_report,
        "results": {
            "aggregate": aggregate,
            "exp117_form4_baseline_recall": EXP117_FORM4_RECALL,
            "delta_recall_vs_F70_form4": delta_recall_vs_F70,
        },
        "per_sura": per_sura,
        "phase_pkl_sha256": sha256_file(PHASE_PKL),
    }

    RECEIPT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[{EXP_NAME}] Wrote receipt: {RECEIPT_PATH}")
    print(f"[{EXP_NAME}] verdict: {verdict}")
    print(f"[{EXP_NAME}] {verdict_reason}")
    print(f"[{EXP_NAME}] aggregate:")
    for k, v in aggregate.items():
        print(f"   {k} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
