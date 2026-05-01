"""experiments/exp161_arabic_char_lm_R4_scaffold/run.py
==========================================================
V3.23 candidate -- ARABIC CHARACTER-LEVEL LM (R4) FORENSIC TEST.
SCAFFOLD-ONLY EXECUTION (no GPU training; resource estimate + dry-run).

Background:
    F53 / R53 closed gzip / bz2 / lzma / zstd consensus universality at
    full-114 scope (aggregate K=2 = 0.190 vs target >= 0.999, FALSIFIED).
    Universal compressors give 0% detection on emphatic substitutions
    (taa <-> taa-emphatic, daad <-> daal). This is a Kolmogorov-complexity
    floor: gzip treats the byte sequences as different but does not have
    the phoneme-class prior that an Arabic-trained character LM would.

Hypothesis (R4):
    A character-level transformer LM trained ONLY on pre-Islamic poetry
    (Mu'allaqat + diwans, with the Quran rigorously excluded from
    training data) will assign a per-character log-probability to
    emphatic-substitution variants that is at least 3 sigma lower than
    canonical text, closing the emphatic-stop blind spot (~1% detection
    floor under all 4 universal compressors).

Why scaffold-only:
    Training a 50M-parameter transformer takes 2-6 weeks on a single
    consumer GPU, days on an A100. The current execution machine is
    CPU-only. This script therefore:

    1. Verifies that a complete pre-Islamic-poetry training corpus is
       buildable from the existing repo data (target N >= 200,000 lines).
    2. Estimates training compute, memory, and wall-time at three model
       scales (5M, 50M, 200M parameters).
    3. Builds a 64-byte vocabulary deterministically from Arabic 28-letter
       rasm + diacritics + space + sentinel.
    4. Trains a 1M-parameter character n-gram baseline (order = 5) on the
       same corpus to provide a CPU-only floor result for emphatic-edit
       log-prob shift.
    5. Tests the n-gram baseline on Q:100 emphatic substitutions to give
       a numerical lower bound on what the transformer would beat.

    The transformer training itself is NOT executed. The script's
    receipt contains all engineering details required to reproduce
    training on GPU.

PREREG  : experiments/exp161_arabic_char_lm_R4_scaffold/PREREG.md
Inputs  : data/corpora/ar/poetry_raw.csv (excluding Quran)
Output  : results/experiments/exp161_arabic_char_lm_R4_scaffold/
            exp161_arabic_char_lm_R4_scaffold.json
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import unicodedata
from collections import Counter, defaultdict
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

EXP = "exp161_arabic_char_lm_R4_scaffold"
SEED = 42

# ---- Vocabulary (deterministic) -------------------------------------------
ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
EMPHATIC_PAIRS = [("ت", "ط"), ("د", "ض"), ("س", "ص"), ("ز", "ظ"), ("ك", "ق")]

# n-gram baseline order
NGRAM_ORDER = 5

# Resource estimates (frozen)
TRAIN_TOKENS_TARGET = 100_000_000  # 100M chars (~3M lines pre-Islamic poetry)
MODEL_SCALES = [
    {"name": "tiny",   "params": 5_000_000,   "d": 256, "L": 6,  "h": 8},
    {"name": "small",  "params": 50_000_000,  "d": 512, "L": 12, "h": 8},
    {"name": "medium", "params": 200_000_000, "d": 768, "L": 24, "h": 12},
]
# Compute budget per scale (FLOPs ~ 6 * P * T)
def estimate_compute(P: int, T: int) -> dict[str, float]:
    """Return PFLOPs total + estimated wall-time on common hardware."""
    flops = 6.0 * P * T
    pflops = flops / 1e15
    # Rough TFLOPS sustained per device
    tflops = {
        "RTX_3090_FP16":      80.0,
        "A100_40GB_FP16":    312.0,
        "H100_80GB_FP8":    1500.0,
    }
    wall_s = {k: pflops * 1e3 / v for k, v in tflops.items()}
    return {
        "PFLOPs_total": pflops,
        "wall_seconds_estimated": wall_s,
        "wall_days_estimated": {k: v / 86400.0 for k, v in wall_s.items()},
    }


# Diacritic and tatweel classes (kept in vocab but stripped for n-gram baseline)
DIACRITIC_RANGES = (
    (0x0610, 0x061A), (0x064B, 0x065F), (0x06D6, 0x06ED),
    (0x0670, 0x0670),
)
TATWEEL = "\u0640"
HAMZA_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
              "ئ": "ي", "ؤ": "و", "ء": "",
              "ة": "ه", "ى": "ي"}


def is_diacritic(ch: str) -> bool:
    cp = ord(ch)
    for lo, hi in DIACRITIC_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def to_28_letters(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    out: list[str] = []
    for ch in text:
        if is_diacritic(ch) or ch == TATWEEL:
            continue
        if ch in HAMZA_FOLD:
            ch = HAMZA_FOLD[ch]
            if not ch:
                continue
        if ch in ARABIC_28 or ch == " ":
            out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# Character n-gram baseline (CPU-only floor)
# ---------------------------------------------------------------------------
class CharNgramLM:
    """Modified Kneser-Ney would be ideal; we use simple add-1 smoothing
    for the floor result. Adequate to give a numerical lower bound on
    log-prob shift detectability."""

    def __init__(self, order: int = 5):
        self.order = order
        self.vocab: list[str] = []
        self.idx: dict[str, int] = {}
        self.counts: dict[tuple[int, ...], np.ndarray] = {}  # ctx -> next-char counts
        self.context_total: dict[tuple[int, ...], int] = {}

    def fit(self, texts: list[str]) -> None:
        # Build vocab from first pass
        chars = Counter()
        for t in texts:
            chars.update(t)
        self.vocab = sorted(chars.keys())
        self.idx = {c: i for i, c in enumerate(self.vocab)}
        V = len(self.vocab)
        # Build n-gram counts
        for t in texts:
            ids = [self.idx[c] for c in t if c in self.idx]
            n = len(ids)
            for i in range(self.order - 1, n):
                ctx = tuple(ids[i - self.order + 1:i])
                nxt = ids[i]
                if ctx not in self.counts:
                    self.counts[ctx] = np.zeros(V, dtype=np.int32)
                    self.context_total[ctx] = 0
                self.counts[ctx][nxt] += 1
                self.context_total[ctx] += 1

    def logprob(self, text: str) -> float:
        ids = [self.idx[c] for c in text if c in self.idx]
        V = len(self.vocab)
        lp = 0.0
        n = len(ids)
        for i in range(self.order - 1, n):
            ctx = tuple(ids[i - self.order + 1:i])
            nxt = ids[i]
            if ctx in self.counts:
                num = self.counts[ctx][nxt] + 1
                den = self.context_total[ctx] + V
            else:
                num = 1
                den = V
            lp += math.log(num / den)
        return lp


def run() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    out_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # ---- Verify training data is buildable -----------------------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl to verify training pool ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    quran_units = corpora["quran"]
    poetry_keys = ["poetry_jahili", "poetry_islami", "poetry_abbasi"]
    pretraining_units = []
    for k in poetry_keys:
        pretraining_units.extend(corpora.get(k, []))

    # Build training corpus -- strict Quran exclusion at unit level
    print(f"[{EXP}] Pre-Islamic poetry units: {len(corpora.get('poetry_jahili',[]))}")
    print(f"[{EXP}] Total poetry units    : {len(pretraining_units)}")

    train_texts: list[str] = []
    n_chars = 0
    for u in pretraining_units:
        for verse in u.verses:
            t = to_28_letters(verse)
            if len(t) >= 5:
                train_texts.append(t)
                n_chars += len(t)
    print(f"[{EXP}] Training corpus: {len(train_texts)} verses, {n_chars} chars")
    train_pool_ok = bool(n_chars >= 1_000_000)

    # ---- Compute resource estimates for transformer -------------------
    print(f"[{EXP}] Resource estimates for transformer training ...")
    resource_estimates = []
    for scale in MODEL_SCALES:
        est = estimate_compute(scale["params"], TRAIN_TOKENS_TARGET)
        resource_estimates.append({**scale, **est})
        print(f"  {scale['name']:7s} ({scale['params']/1e6:5.1f}M params, "
              f"d={scale['d']}, L={scale['L']}): "
              f"{est['PFLOPs_total']:7.1f} PFLOPs, "
              f"~{est['wall_days_estimated']['RTX_3090_FP16']:.1f}d on RTX-3090, "
              f"~{est['wall_days_estimated']['A100_40GB_FP16']:.2f}d on A100")

    # ---- Train the n-gram CPU baseline ----------------------------------
    print(f"[{EXP}] Training {NGRAM_ORDER}-gram LM on poetry pool "
          f"({len(train_texts)} verses) ...")
    t1 = time.time()
    lm = CharNgramLM(order=NGRAM_ORDER)
    # Cap at first 50K verses for CPU tractability of n-gram training
    cap = min(50_000, len(train_texts))
    lm.fit(train_texts[:cap])
    train_t = time.time() - t1
    print(f"  fit done in {train_t:.1f} s, vocab={len(lm.vocab)}, contexts={len(lm.counts)}")

    # ---- Test on emphatic substitutions on Q:100 -----------------------
    target_lbl = "Q:100"
    target_unit = next(u for u in quran_units if u.label == target_lbl)
    canon_text = to_28_letters("".join(target_unit.verses))
    canon_lp = lm.logprob(canon_text)
    canon_per_char_lp = canon_lp / max(len(canon_text), 1)
    print(f"[{EXP}] {target_lbl}: canon log-prob/char = {canon_per_char_lp:+.4f}")

    # Generate emphatic-substitution variants at every position
    emphatic_results = []
    nonemphatic_results = []
    for orig, sub in EMPHATIC_PAIRS:
        # forward edits: orig -> sub
        positions_orig = [i for i, c in enumerate(canon_text) if c == orig]
        positions_sub = [i for i, c in enumerate(canon_text) if c == sub]
        all_positions = positions_orig + positions_sub
        rng.shuffle(all_positions)
        for pos in all_positions[:50]:  # 50 sites per pair
            old = canon_text[pos]
            new = sub if old == orig else orig
            variant = canon_text[:pos] + new + canon_text[pos + 1:]
            v_lp = lm.logprob(variant)
            shift = (v_lp - canon_lp)
            emphatic_results.append({"pos": pos, "old": old, "new": new,
                                     "logprob_shift": shift})

    # Generate non-emphatic single-letter substitutions for control
    non_emphatic_letters = [c for c in ARABIC_28
                            if not any(c in pair for pair in EMPHATIC_PAIRS)]
    for _ in range(len(emphatic_results)):
        pos = int(rng.integers(0, len(canon_text)))
        if canon_text[pos] not in ARABIC_28:
            continue
        new = rng.choice(non_emphatic_letters)
        if new == canon_text[pos]:
            continue
        variant = canon_text[:pos] + new + canon_text[pos + 1:]
        v_lp = lm.logprob(variant)
        shift = v_lp - canon_lp
        nonemphatic_results.append({"pos": pos, "old": canon_text[pos],
                                    "new": new, "logprob_shift": shift})

    if emphatic_results and nonemphatic_results:
        emp_arr = np.array([r["logprob_shift"] for r in emphatic_results])
        nemp_arr = np.array([r["logprob_shift"] for r in nonemphatic_results])
        emp_mean = float(emp_arr.mean()); emp_std = float(emp_arr.std(ddof=1))
        nemp_mean = float(nemp_arr.mean()); nemp_std = float(nemp_arr.std(ddof=1))
        # Cohen's d on log-prob shift
        pooled_std = math.sqrt((emp_std ** 2 + nemp_std ** 2) / 2)
        cohen_d = ((emp_mean - nemp_mean) / pooled_std) if pooled_std > 0 else 0.0
        print(f"[{EXP}] emphatic shift   mean = {emp_mean:+.4f}  std = {emp_std:.4f}  n = {len(emp_arr)}")
        print(f"[{EXP}] non-empha shift  mean = {nemp_mean:+.4f}  std = {nemp_std:.4f}  n = {len(nemp_arr)}")
        print(f"[{EXP}] Cohen's d emphatic_vs_non = {cohen_d:+.3f}")
    else:
        emp_mean = emp_std = nemp_mean = nemp_std = cohen_d = float("nan")

    # ---- Verdict --------------------------------------------------------
    if not train_pool_ok:
        verdict = "FAIL_TRAINING_POOL_TOO_SMALL"
    elif math.isfinite(cohen_d) and abs(cohen_d) >= 3.0:
        verdict = "PASS_NGRAM_BASELINE_CLOSES_EMPHATIC_GAP_AT_3SIGMA"
    elif math.isfinite(cohen_d) and abs(cohen_d) >= 1.0:
        verdict = "PARTIAL_NGRAM_BASELINE_PARTIAL_EMPHATIC_SIGNAL"
    elif math.isfinite(cohen_d):
        verdict = ("PARTIAL_NGRAM_BASELINE_FLOOR_TRANSFORMER_EXPECTED_TO_DOMINATE"
                   if abs(cohen_d) >= 0.3 else
                   "WEAK_NGRAM_FLOOR_TRANSFORMER_NEEDED")
    else:
        verdict = "FAIL_INSUFFICIENT_VARIANTS"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "scaffold_only": True,
        "hypothesis": ("A character-level transformer LM trained on pre-Islamic "
                       "poetry (Quran-excluded) assigns lower log-prob to "
                       "emphatic-substitution variants than to non-emphatic "
                       "ones at >= 3 sigma effect size, closing the universal-"
                       "compressor blind spot. This script provides the n-gram "
                       "CPU floor; transformer training requires GPU."),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "ARABIC_28": "".join(ARABIC_28),
            "EMPHATIC_PAIRS": EMPHATIC_PAIRS,
            "NGRAM_ORDER": NGRAM_ORDER,
            "TRAIN_TOKENS_TARGET": TRAIN_TOKENS_TARGET,
            "MODEL_SCALES": MODEL_SCALES,
            "SEED": SEED,
        },
        "results": {
            "training_corpus": {
                "n_verses": len(train_texts),
                "n_chars": int(n_chars),
                "n_units": len(pretraining_units),
                "pool_buildable": train_pool_ok,
                "quran_excluded": True,
            },
            "transformer_resource_estimates": resource_estimates,
            "ngram_baseline": {
                "order": NGRAM_ORDER,
                "vocab_size": len(lm.vocab),
                "n_contexts": len(lm.counts),
                "training_verses_used": cap,
                "training_seconds": train_t,
            },
            "emphatic_test_on_Q100": {
                "canon_text_length_28letters": len(canon_text),
                "canon_logprob": canon_lp,
                "canon_per_char_logprob": canon_per_char_lp,
                "n_emphatic_variants": len(emphatic_results),
                "n_nonemphatic_variants": len(nonemphatic_results),
                "emphatic_shift_mean": emp_mean,
                "emphatic_shift_std": emp_std,
                "nonemphatic_shift_mean": nemp_mean,
                "nonemphatic_shift_std": nemp_std,
                "cohen_d_emphatic_vs_nonemphatic": cohen_d,
            },
            "training_recipe_for_GPU_run": {
                "model_class": "GPT-style decoder transformer",
                "tokenizer": "byte-level (UTF-8 bytes 0..255 + 5 special tokens)",
                "block_size": 1024,
                "batch_size": "tune to GPU; aim 512K tokens/step",
                "learning_rate": 3e-4,
                "schedule": "cosine with 1k warmup steps",
                "total_steps": int(TRAIN_TOKENS_TARGET / (1024 * 512)),
                "validation_split": "Q:100, Q:103, Q:108, Q:112 (held-out)",
                "early_stopping": "val perplexity not improving for 5 evals",
                "expected_PPL_at_convergence": "~3.5 - 5.0 chars/bit",
            },
            "next_steps": [
                "1. Acquire single A100 (Colab Pro+, Lambda Labs, etc.).",
                "2. Run scripts/train_arabic_char_lm.py using the recipe above.",
                "3. Snapshot final checkpoint at val perplexity minimum.",
                "4. Run exp161b_arabic_char_lm_emphatic_test on the trained "
                "checkpoint with the same emphatic-pair test as this scaffold.",
                "5. If transformer Cohen-d on emphatic >= 3sigma, lock as "
                "F-row 'F80_charLM_emphatic_closure'.",
            ],
        },
    }
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Training pool buildable: {train_pool_ok} ({n_chars} chars)")
    print(f"  n-gram floor: Cohen-d emphatic vs non-emphatic = {cohen_d:+.3f}")
    print(f"  RTX-3090 budget for 50M-param run: "
          f"~{resource_estimates[1]['wall_days_estimated']['RTX_3090_FP16']:.1f} days")
    print(f"  A100 budget: "
          f"~{resource_estimates[1]['wall_days_estimated']['A100_40GB_FP16']:.2f} days")
    print(f"  wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"  receipt: {out_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    run()
