"""
expP17_markov_saj_adversarial/run.py
====================================
Adversarial Markov saj‛ generator: can a character-level Markov model
trained on the 3 highest-EL Arabic-prose families defeat the EL Simplicity
Law (i.e., generate Markov samples with EL ≥ 0.40)?

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP17_markov_saj_adversarial/expP17_markov_saj_adversarial.json
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import el_rate  # noqa: E402

EXP = "expP17_markov_saj_adversarial"
SEED = 42
N_GEN = 100
MARKOV_ORDER = 3
TARGET_VERSES_PER_SAMPLE = 50
TARGET_WORDS_PER_VERSE = 10


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _train_word_markov(verses: list[str], order: int) -> dict:
    """Train a word-level order-`order` Markov model and a verse-end
    sub-model that conditions next-word on the *current verse position*
    (encouraging rhyme-saturation at verse-end)."""
    transitions: dict[tuple, Counter] = defaultdict(Counter)
    verse_end_words: list[str] = []
    for v in verses:
        words = v.split()
        if len(words) < order + 1:
            continue
        # Pad with start tokens
        padded = ("<s>",) * order + tuple(words) + ("</s>",)
        for i in range(len(padded) - order):
            ctx = padded[i:i + order]
            nxt = padded[i + order]
            transitions[ctx][nxt] += 1
        verse_end_words.append(words[-1])
    # Verse-end-word distribution by terminal letter (we will resample
    # verse-final words to match the empirical terminal-letter rhyme
    # distribution observed in the training corpus).
    end_letter_dist: Counter = Counter()
    for w in verse_end_words:
        if w:
            ch = next((c for c in reversed(w) if c.isalpha()), "")
            if ch:
                end_letter_dist[ch] += 1
    return {
        "order": order,
        "transitions": transitions,
        "end_letter_dist": end_letter_dist,
        "all_end_words": verse_end_words,
    }


def _generate_verse(model: dict, max_words: int, target_letter: str | None,
                    rng: random.Random) -> str:
    """Generate one verse by sampling Markov transitions. If
    `target_letter` is given, the verse ends with a word ending in that
    letter (drawn from `all_end_words` filtered to that letter; if no
    such word exists, just end on </s>)."""
    order = model["order"]
    transitions = model["transitions"]
    ctx = ("<s>",) * order
    out_words: list[str] = []
    for _ in range(max_words):
        nxt_dist = transitions.get(ctx)
        if not nxt_dist:
            break
        words, counts = zip(*nxt_dist.items())
        total = sum(counts)
        probs = [c / total for c in counts]
        nxt = rng.choices(words, weights=probs, k=1)[0]
        if nxt == "</s>":
            break
        out_words.append(nxt)
        ctx = tuple((*ctx[1:], nxt))
    if target_letter and out_words:
        # Replace last word with one ending in target_letter (resample-and-attack)
        candidates = [w for w in model["all_end_words"]
                      if w and next((c for c in reversed(w) if c.isalpha()), "") == target_letter]
        if candidates:
            out_words[-1] = rng.choice(candidates)
    return " ".join(out_words)


def _generate_sample(model: dict, n_verses: int, max_words: int,
                     mode: str, rng: random.Random) -> list[str]:
    """Generate one sample of `n_verses` verses.
    mode='free' : no rhyme target
    mode='saj_attack' : sample target letter from end_letter_dist with
                        replacement; force every verse to end on it (one
                        target across the entire sample, mimicking the
                        Quran's per-surah rhyme targeting).
    """
    target = None
    if mode == "saj_attack":
        ed = model["end_letter_dist"]
        if ed:
            letters, counts = zip(*ed.items())
            total = sum(counts)
            probs = [c / total for c in counts]
            target = rng.choices(letters, weights=probs, k=1)[0]
    return [_generate_verse(model, max_words, target, rng) for _ in range(n_verses)]


def _verdict(max_el: float) -> str:
    if max_el < 0.40:
        return "EL_LAW_DEFENDED"
    if max_el < 0.55:
        return "EL_LAW_QUALIFIED"
    return "EL_LAW_FALSIFIED"


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    rng = random.Random(SEED)

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # --- Gather training verses from poetry families ---
    train_corpora = ["poetry_jahili", "poetry_islami", "poetry_abbasi"]
    train_verses: list[str] = []
    for cn in train_corpora:
        for u in CORPORA.get(cn, []):
            train_verses.extend(u.verses)
    print(f"[{EXP}] Trained on {len(train_verses)} verses from {train_corpora}")

    # Sanity baseline: training-corpus EL on full pool
    train_el = el_rate(train_verses) if len(train_verses) >= 2 else float("nan")
    print(f"[{EXP}] Training-corpus pooled EL (sanity): {train_el:.4f}")

    print(f"[{EXP}] Training order-{MARKOV_ORDER} word Markov ...")
    model_poetry = _train_word_markov(train_verses, MARKOV_ORDER)

    # Quran self-baseline (sanity: Markov-on-Quran reaches EL ≈ 0.50?)
    quran_verses: list[str] = []
    for u in CORPORA.get("quran", []):
        quran_verses.extend(u.verses)
    print(f"[{EXP}] Training control: Quran-trained Markov ({len(quran_verses)} verses)")
    model_quran = _train_word_markov(quran_verses, MARKOV_ORDER)

    # --- Generate samples ---
    print(f"[{EXP}] Generating {N_GEN} samples per mode ...")
    results: dict[str, dict] = {}
    for label, model in (("poetry_free", model_poetry),
                          ("poetry_saj_attack", model_poetry),
                          ("quran_free", model_quran),
                          ("quran_saj_attack", model_quran)):
        mode = "saj_attack" if label.endswith("saj_attack") else "free"
        els: list[float] = []
        for i in range(N_GEN):
            sample = _generate_sample(model, TARGET_VERSES_PER_SAMPLE,
                                       TARGET_WORDS_PER_VERSE, mode,
                                       random.Random(SEED + i + hash(label) % 1000))
            if len(sample) >= 2:
                els.append(el_rate(sample))
        els = np.array(els, dtype=float)
        results[label] = {
            "n_samples": len(els),
            "mean": float(els.mean()) if els.size else None,
            "median": float(np.median(els)) if els.size else None,
            "max": float(els.max()) if els.size else None,
            "min": float(els.min()) if els.size else None,
            "std": float(els.std(ddof=1)) if els.size > 1 else None,
            "p_above_0.314": float((els >= 0.314).mean()) if els.size else None,
            "p_above_0.40": float((els >= 0.40).mean()) if els.size else None,
            "p_above_0.55": float((els >= 0.55).mean()) if els.size else None,
        }
        print(f"[{EXP}] {label:24s}  n={len(els):3d}  EL mean={els.mean():.4f}  "
              f"max={els.max():.4f}  >=0.314: {(els>=0.314).mean()*100:.1f}%  "
              f">=0.40: {(els>=0.40).mean()*100:.1f}%  "
              f">=0.55: {(els>=0.55).mean()*100:.1f}%")

    poetry_max_el = max(results["poetry_free"]["max"] or 0,
                        results["poetry_saj_attack"]["max"] or 0)
    verdict = _verdict(poetry_max_el)
    print(f"[{EXP}] Max EL across poetry-Markov samples: {poetry_max_el:.4f}  "
          f"-> verdict: {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "n_train_verses_poetry": len(train_verses),
        "n_train_verses_quran": len(quran_verses),
        "markov_order": MARKOV_ORDER,
        "n_samples_per_mode": N_GEN,
        "target_verses_per_sample": TARGET_VERSES_PER_SAMPLE,
        "target_words_per_verse": TARGET_WORDS_PER_VERSE,
        "training_corpus_pooled_EL": float(train_el),
        "results_per_mode": results,
        "max_EL_poetry_markov": poetry_max_el,
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
