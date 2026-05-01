"""exp118_multi_letter_F55_theorem — Multi-letter F55 detection with Δ ≤ 2k bound.

Tests:
  - Theorem F55-multi: any k-letter substitution gives Δ ≤ 2k (mathematical certainty)
  - Empirical recall: under τ_k = 2k, recall = 1 on all k-letter variants
  - Peer FPR: peer-text bigram histograms differ from Quran by Δ > 2k

Prereg: experiments/exp118_multi_letter_F55_theorem/PREREG.md
Hypothesis ID: H73.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import random
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PHASE_PKL = ROOT / "results/checkpoints/phase_06_phi_m.pkl"
ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
ALPH_SET = set(ARABIC_28)

K_VALUES = [1, 2, 3, 4, 5]
N_SUBS_PER_SURA = 1000
N_FPR_PAIRS_PER_K = 5000
SEED_BASE = 42
RECALL_FLOOR = 0.999
FPR_CEILING = 0.05

PEER_CORPORA = ["poetry_jahili", "poetry_islami", "poetry_abbasi", "hindawi", "ksucca", "arabic_bible"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    """Strip diacritics, normalize hamzas, fold ta-marbuta and alif-maksura.
    Returns a string consisting only of the 28 Arabic consonants and spaces.
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    replacements = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ؤ": "و", "ئ": "ي", "ء": "",
        "ة": "ه", "ى": "ي",
    }
    for o, n in replacements.items():
        text = text.replace(o, n)
    keep = ALPH_SET | {" "}
    text = "".join(c if c in keep else "" for c in text)
    text = " ".join(text.split())
    return text


def bigram_histogram(text: str) -> dict:
    """Bigram counts within words (ignore space-letter and letter-space transitions)."""
    h = {}
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i + 2]
            h[bg] = h.get(bg, 0) + 1
    return h


def delta(h1: dict, h2: dict) -> float:
    keys = set(h1) | set(h2)
    return sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys) / 2.0


def k_letter_substitution(text: str, k: int, rng: random.Random) -> str:
    """Pick k random distinct letter positions, replace each with a uniformly random
    different letter from the alphabet."""
    positions = [i for i, c in enumerate(text) if c in ALPH_SET]
    if len(positions) < k:
        return text
    chosen = rng.sample(positions, k)
    chars = list(text)
    for p in chosen:
        old = chars[p]
        new = rng.choice([L for L in ARABIC_28 if L != old])
        chars[p] = new
    return "".join(chars)


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    out_dir = ROOT / "results" / "experiments" / "exp118_multi_letter_F55_theorem"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading phase_06_phi_m from {PHASE_PKL.relative_to(ROOT)}...")
    with open(PHASE_PKL, "rb") as f:
        state = pickle.load(f)
    inner = state.get("state", state)
    quran_units = inner["CORPORA"].get("quran")
    if quran_units is None:
        return 1

    # Pre-normalize all Quran suras as concatenated text
    quran_normalized = {}
    for unit in quran_units:
        verses = list(unit.verses) if hasattr(unit, "verses") else list(unit.get("verses", []))
        label = str(unit.label) if hasattr(unit, "label") else str(unit.get("label", "?"))
        quran_normalized[label] = normalize(" ".join(verses))

    # Pre-normalize peer chapters (sample at most 50 per peer corpus to keep memory manageable)
    peer_normalized = []
    for c in PEER_CORPORA:
        units = inner["CORPORA"].get(c, [])
        for unit in units:
            verses = list(unit.verses) if hasattr(unit, "verses") else list(unit.get("verses", []))
            if len(verses) < 5:
                continue
            label = str(unit.label) if hasattr(unit, "label") else str(unit.get("label", "?"))
            txt = normalize(" ".join(verses))
            if len(txt) >= 50:
                peer_normalized.append((label, txt))

    print(f"Pool: {len(quran_normalized)} Quran suras, {len(peer_normalized)} peer chapters")

    per_k_results = {}
    for k in K_VALUES:
        print(f"\n--- k = {k} ---")
        rng = random.Random(SEED_BASE * 1000 + k)

        # Step 1+2: theorem verification + recall
        all_deltas = []
        n_violations = 0
        n_zero = 0  # Δ = 0 → recall miss (substitution accidentally identity)
        for label, text in quran_normalized.items():
            h_orig = bigram_histogram(text)
            for _ in range(N_SUBS_PER_SURA):
                edited = k_letter_substitution(text, k, rng)
                h_edit = bigram_histogram(edited)
                d = delta(h_orig, h_edit)
                all_deltas.append(d)
                if d > 2 * k + 1e-9:
                    n_violations += 1
                if d == 0.0:
                    n_zero += 1

        all_deltas = np.array(all_deltas)
        max_delta = float(all_deltas.max())
        mean_delta = float(all_deltas.mean())
        n_total = len(all_deltas)
        n_fired = int(((all_deltas > 0) & (all_deltas <= 2 * k)).sum())
        recall_k = n_fired / n_total

        # Step 3: peer FPR
        fpr_rng = random.Random(SEED_BASE * 1000 + k + 99)
        n_fpr_below_threshold = 0
        peer_deltas = []
        quran_keys = list(quran_normalized.keys())
        for _ in range(N_FPR_PAIRS_PER_K):
            qk = fpr_rng.choice(quran_keys)
            pl, pt = fpr_rng.choice(peer_normalized)
            d = delta(bigram_histogram(quran_normalized[qk]), bigram_histogram(pt))
            peer_deltas.append(d)
            if d <= 2 * k:
                n_fpr_below_threshold += 1
        peer_deltas = np.array(peer_deltas)
        fpr_k = n_fpr_below_threshold / N_FPR_PAIRS_PER_K
        peer_min_delta = float(peer_deltas.min())
        peer_median_delta = float(np.median(peer_deltas))

        per_k_results[k] = {
            "tau_k": 2 * k,
            "n_variants": n_total,
            "max_delta_observed": max_delta,
            "mean_delta_observed": mean_delta,
            "n_theorem_violations": n_violations,
            "theorem_holds": n_violations == 0 and max_delta <= 2 * k,
            "n_zero_delta": n_zero,
            "n_fired": n_fired,
            "recall_k": recall_k,
            "recall_pass": recall_k >= RECALL_FLOOR,
            "n_fpr_pairs": N_FPR_PAIRS_PER_K,
            "n_fpr_below_threshold": n_fpr_below_threshold,
            "fpr_k": fpr_k,
            "fpr_pass": fpr_k <= FPR_CEILING,
            "peer_min_delta": peer_min_delta,
            "peer_median_delta": peer_median_delta,
        }

        print(f"  Theorem: max(Δ) = {max_delta:.4f}, bound = {2*k} → {'HOLDS' if per_k_results[k]['theorem_holds'] else 'VIOLATED'}")
        print(f"  Recall:  {recall_k:.4f} (n_fired = {n_fired} / {n_total}; floor = {RECALL_FLOOR})")
        print(f"  FPR:     {fpr_k:.4f} (n_fpr = {n_fpr_below_threshold} / {N_FPR_PAIRS_PER_K}; ceiling = {FPR_CEILING})")
        print(f"  Peer Δ: min = {peer_min_delta:.2f}, median = {peer_median_delta:.2f}")

    # Verdict
    theorem_holds_all = all(r["theorem_holds"] for r in per_k_results.values())
    recall_pass_all = all(r["recall_pass"] for r in per_k_results.values())
    fpr_pass_all = all(r["fpr_pass"] for r in per_k_results.values())

    if not theorem_holds_all:
        verdict = "FAIL_theorem_violated"
    elif not recall_pass_all:
        verdict = "FAIL_recall_below_floor"
    elif not fpr_pass_all:
        verdict = "FAIL_FPR_above_ceiling"
    else:
        verdict = "PASS_F55_multi_k_universal"

    finished = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": "exp118_multi_letter_F55_theorem",
        "hypothesis_id": "H73",
        "verdict": verdict,
        "started_at_utc": started,
        "completed_at_utc": finished,
        "prereg_document": "experiments/exp118_multi_letter_F55_theorem/PREREG.md",
        "prereg_sha256": _sha256(ROOT / "experiments/exp118_multi_letter_F55_theorem/PREREG.md"),
        "frozen_constants": {
            "K_VALUES": K_VALUES,
            "N_SUBS_PER_SURA": N_SUBS_PER_SURA,
            "N_FPR_PAIRS_PER_K": N_FPR_PAIRS_PER_K,
            "SEED_BASE": SEED_BASE,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEILING": FPR_CEILING,
            "PEER_CORPORA": PEER_CORPORA,
        },
        "source_pkl_sha256": _sha256(PHASE_PKL),
        "n_quran_suras": len(quran_normalized),
        "n_peer_chapters": len(peer_normalized),
        "per_k_results": per_k_results,
    }
    out_path = out_dir / "exp118_multi_letter_F55_theorem.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== exp118 — Multi-letter F55 Theorem (Δ ≤ 2k) ===\n")
    print(f"Theorem holds for all k:  {theorem_holds_all}")
    print(f"Recall ≥ {RECALL_FLOOR} for all k:  {recall_pass_all}")
    print(f"FPR ≤ {FPR_CEILING} for all k:    {fpr_pass_all}")
    print(f"\nVerdict: {verdict}")
    print(f"Receipt: {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
