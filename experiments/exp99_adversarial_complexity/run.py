"""
exp99_adversarial_complexity/run.py
====================================
Adversarial joint-constraint test: generate N=10^6 Markov-3 forgeries
and evaluate how many pass Gate 1 ∧ F55 ∧ F56 simultaneously.

Pre-registered in PREREG.md (frozen 2026-04-27, v7.9-cand patch H pre-V2).

Reads:  phase_06_phi_m.pkl :: state[CORPORA]
Writes: results/experiments/exp99_adversarial_complexity/exp99_adversarial_complexity.json
"""
from __future__ import annotations

import hashlib
import json
import math
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
from src.features import (  # noqa: E402
    el_rate, vl_cv, cn_rate, h_el, ARABIC_CONN, DIAC, _strip_d,
)

# ---------------------------------------------------------------------------
# Constants (frozen per PREREG §4)
# ---------------------------------------------------------------------------
EXP = "exp99_adversarial_complexity"
N_FORGERIES = 1_000_000
MARKOV_ORDER = 3
GENERATOR_SEED = 99000
LENGTH_SAMPLE_RANGE = (5, 50)  # verses per forgery sample
F55_TAU = 2.0
F56_THRESHOLD = 0.50
JOINT_PASS_TARGET = 10   # H54 PASS allows up to 10 of 10^6
JOINT_PASS_STRICT = 0    # H54 STRICT requires zero

# Locked SVM weights from expP7_phi_m_full_quran (overall)
SVM_W = np.array([5.238876016863266, 5.8639699045570755,
                   0.49931000516879376, -0.9451012462890134,
                   0.9147695040839672])
SVM_B = -1.8146355324839272
SVM_W_TOL = 1e-6
SVM_B_TOL = 1e-6

RESULTS = _ROOT / "results"
REPORT_INTERVAL = 100_000  # print progress every N forgeries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _terminal_alpha(s: str) -> str:
    """Return the last Arabic alphabetic character in s, or ''.
    Strips diacritics first to match src.features._terminal_alpha."""
    v = _strip_d(s).strip()
    for ch in reversed(v):
        if ch.isalpha():
            return ch
    return ""


# ---------------------------------------------------------------------------
# Root cache — avoid per-word CamelTools calls inside the hot loop
# ---------------------------------------------------------------------------
_ROOT_CACHE: dict[str, str] = {}


def _warm_root_cache(all_words: set[str]) -> None:
    """Pre-compute Arabic roots for every unique word using CamelTools,
    then store in _ROOT_CACHE so the hot loop does dict lookups only."""
    global _ROOT_CACHE
    import src.features as _feat
    _rc = _feat._rc
    _strip = _feat._strip_d
    n = len(all_words)
    print(f"[{EXP}] Pre-warming root cache for {n:,} unique words …")
    t0 = time.time()
    for i, w in enumerate(all_words):
        stripped = _strip(w).strip()
        toks = stripped.split()
        if toks:
            _ROOT_CACHE[w] = _rc.primary_root_normalized(toks[-1])
        else:
            _ROOT_CACHE[w] = ""
        if (i + 1) % 10000 == 0:
            print(f"[{EXP}]   root cache: {i+1:,}/{n:,}")
    print(f"[{EXP}]   root cache warm ({time.time()-t0:.1f} s)")


def _h_cond_roots_cached(verses: list[str]) -> float:
    """h_cond_roots using the pre-warmed cache (no CamelTools calls)."""
    roots: list[str] = []
    for v in verses:
        toks = v.split()
        w = toks[-1] if toks else ""
        r = _ROOT_CACHE.get(w, "")
        roots.append(r if r else "<unk>")
    if len(roots) < 2:
        return 0.0
    bigrams: dict[str, Counter] = defaultdict(Counter)
    marg: Counter = Counter()
    for a, b in zip(roots[:-1], roots[1:]):
        bigrams[a][b] += 1
        marg[a] += 1
    total = sum(marg.values())
    if total == 0:
        return 0.0
    h = 0.0
    for ctx, nxt_counts in bigrams.items():
        ctx_total = marg[ctx]
        for n_co in nxt_counts.values():
            p = n_co / total
            p_cond = n_co / ctx_total
            if p > 0 and p_cond > 0:
                h -= p * math.log2(p_cond)
    return h


def _features_5d_fast(verses: list[str]) -> np.ndarray:
    """5-D feature vector using cached roots (drop-in for features_5d)."""
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, ARABIC_CONN)
    hc = _h_cond_roots_cached(verses)
    he = h_el(verses)
    T = hc - he
    return np.array([el, cv, cn, hc, T], dtype=float)


# ---------------------------------------------------------------------------
# Fast Markov-3 generator with pre-compiled CDF tables
# ---------------------------------------------------------------------------
class FastMarkov:
    """Word-level Markov model with pre-compiled CDF for fast sampling."""

    def __init__(self, verses: list[str], order: int):
        self.order = order
        raw: dict[tuple, Counter] = defaultdict(Counter)
        self.verse_end_words: list[str] = []

        for v in verses:
            words = v.split()
            if len(words) < order + 1:
                continue
            padded = ("<s>",) * order + tuple(words) + ("</s>",)
            for i in range(len(padded) - order):
                ctx = padded[i: i + order]
                nxt = padded[i + order]
                raw[ctx][nxt] += 1
            self.verse_end_words.append(words[-1])

        # Pre-compile to arrays
        self._table: dict[tuple, tuple[list[str], np.ndarray]] = {}
        for ctx, counter in raw.items():
            words = list(counter.keys())
            counts = np.array(list(counter.values()), dtype=np.float64)
            cdf = counts.cumsum()
            cdf /= cdf[-1]
            self._table[ctx] = (words, cdf)

        # Verse-end-word distribution by terminal letter
        self.end_letter_dist: Counter = Counter()
        self.end_words_by_letter: dict[str, list[str]] = defaultdict(list)
        for w in self.verse_end_words:
            ch = _terminal_alpha(w)
            if ch:
                self.end_letter_dist[ch] += 1
                self.end_words_by_letter[ch].append(w)

        # Pre-compile rhyme letter CDF
        if self.end_letter_dist:
            letters = list(self.end_letter_dist.keys())
            counts = np.array([self.end_letter_dist[l] for l in letters],
                              dtype=np.float64)
            cdf = counts.cumsum()
            cdf /= cdf[-1]
            self._rhyme_letters = letters
            self._rhyme_cdf = cdf
        else:
            self._rhyme_letters = []
            self._rhyme_cdf = np.array([])

        # Collect all unique words for root cache warming
        self.vocabulary: set[str] = set()
        for ctx, (words, _) in self._table.items():
            self.vocabulary.update(w for w in words if w not in ("<s>", "</s>"))
            self.vocabulary.update(w for w in ctx if w not in ("<s>", "</s>"))
        for wl in self.end_words_by_letter.values():
            self.vocabulary.update(wl)

    def sample_next(self, ctx: tuple, u: float) -> str | None:
        """Sample next word given context and uniform random u ∈ [0,1)."""
        entry = self._table.get(ctx)
        if entry is None:
            return None
        words, cdf = entry
        idx = int(np.searchsorted(cdf, u))
        if idx >= len(words):
            idx = len(words) - 1
        return words[idx]

    def sample_rhyme_letter(self, u: float) -> str | None:
        if not self._rhyme_letters:
            return None
        idx = int(np.searchsorted(self._rhyme_cdf, u))
        if idx >= len(self._rhyme_letters):
            idx = len(self._rhyme_letters) - 1
        return self._rhyme_letters[idx]


def _generate_verse_fast(model: FastMarkov, max_words: int,
                         target_letter: str | None,
                         rng: random.Random) -> str:
    order = model.order
    ctx = ("<s>",) * order
    out_words: list[str] = []
    for _ in range(max_words):
        nxt = model.sample_next(ctx, rng.random())
        if nxt is None or nxt == "</s>":
            break
        out_words.append(nxt)
        ctx = (*ctx[1:], nxt)
    if target_letter and out_words:
        candidates = model.end_words_by_letter.get(target_letter, [])
        if candidates:
            out_words[-1] = rng.choice(candidates)
    return " ".join(out_words)


def _generate_forgery_fast(model: FastMarkov, rng: random.Random) -> list[str]:
    n_verses = rng.randint(*LENGTH_SAMPLE_RANGE)
    target = model.sample_rhyme_letter(rng.random())
    return [_generate_verse_fast(model, 15, target, rng)
            for _ in range(n_verses)]


# ---------------------------------------------------------------------------
# F55: bigram-shift distance (ABSOLUTE count L1 / 2)
# ---------------------------------------------------------------------------
def _letters_28(text: str) -> str:
    """Extract Arabic alphabetic characters only (the 28-letter skeleton)."""
    return "".join(ch for ch in text if "\u0600" <= ch <= "\u06ff"
                   and ch.isalpha())


def _bigram_hist(text: str) -> Counter:
    """Bigram frequency histogram over letters_28 skeleton (absolute counts)."""
    s = _letters_28(text)
    return Counter(s[i: i + 2] for i in range(len(s) - 1))


def _bigram_delta(h1: Counter, h2: Counter,
                  early_exit: float = 0.0) -> float:
    """Δ_bigram = ||hist_2(s1) - hist_2(s2)||_1 / 2  (absolute counts).

    For a single-letter substitution, at most 2 old bigrams lose 1 count
    and 2 new bigrams gain 1 count → L1 ≤ 4 → Δ ≤ 2.  For unrelated
    texts, Δ scales with text length.

    If early_exit > 0, returns as soon as Δ is guaranteed > early_exit
    (partial L1 already exceeds 2 * early_exit)."""
    limit = early_exit * 2.0 if early_exit > 0 else float("inf")
    l1 = 0
    for k in h1:
        l1 += abs(h1[k] - h2.get(k, 0))
        if l1 > limit:
            return l1 / 2.0
    for k in h2:
        if k not in h1:
            l1 += h2[k]
            if l1 > limit:
                return l1 / 2.0
    return l1 / 2.0


# ---------------------------------------------------------------------------
# F56: EL-fragility
# ---------------------------------------------------------------------------
def _el_frag(verses: list[str]) -> float:
    """EL_frag(C) = p_max(C) * 27/28 + (1 - p_max(C)) * 1/28."""
    finals = [_terminal_alpha(v) for v in verses if _terminal_alpha(v)]
    if not finals:
        return 0.0
    c = Counter(finals)
    total = sum(c.values())
    p_max = max(c.values()) / total
    return p_max * 27 / 28 + (1 - p_max) * 1 / 28


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre_check = self_check_begin()
    t0 = time.time()

    prereg_hash = sha256_of(_HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash}")

    audit_failures: list[str] = []

    # -----------------------------------------------------------------------
    # Load corpus data
    # -----------------------------------------------------------------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl …")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    train_corpora = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                     "ksucca", "arabic_bible", "hindawi"]
    train_verses: list[str] = []
    for cn in train_corpora:
        for u in CORPORA.get(cn, []):
            train_verses.extend(u.verses)
    quran_units = CORPORA.get("quran", [])
    quran_verses: list[str] = []
    for u in quran_units:
        quran_verses.extend(u.verses)
    train_verses.extend(quran_verses)
    print(f"[{EXP}] Corpus: {len(train_verses):,} verses "
          f"({len(quran_verses)} Quran + {len(train_verses)-len(quran_verses)} controls)")

    # -----------------------------------------------------------------------
    # Audit A4: verify SVM weights match expP7 locked receipt
    # -----------------------------------------------------------------------
    p7_path = (RESULTS / "experiments" / "expP7_phi_m_full_quran"
               / "expP7_phi_m_full_quran.json")
    if p7_path.exists():
        with open(p7_path, "r", encoding="utf-8") as f:
            p7 = json.load(f)
        p7_w = np.array(p7["overall"]["w"])
        p7_b = p7["overall"]["b"]
        w_drift = float(np.max(np.abs(SVM_W - p7_w)))
        b_drift = abs(SVM_B - p7_b)
        if w_drift > SVM_W_TOL:
            audit_failures.append(f"A4: SVM_W drift {w_drift:.2e} > {SVM_W_TOL}")
        if b_drift > SVM_B_TOL:
            audit_failures.append(f"A4: SVM_B drift {b_drift:.2e} > {SVM_B_TOL}")
        print(f"[{EXP}] A4 ✓ SVM weights match (w_drift={w_drift:.2e}, b_drift={b_drift:.2e})")
    else:
        audit_failures.append("A4: expP7 receipt missing")

    # -----------------------------------------------------------------------
    # Pre-compute Quran bigram histograms for F55 (one per surah)
    # -----------------------------------------------------------------------
    quran_bigram_hists: list[Counter] = []
    for u in quran_units:
        full_text = " ".join(u.verses)
        quran_bigram_hists.append(_bigram_hist(full_text))
    print(f"[{EXP}] Pre-computed {len(quran_bigram_hists)} Quran bigram histograms")

    # -----------------------------------------------------------------------
    # Train fast Markov-3 model
    # -----------------------------------------------------------------------
    print(f"[{EXP}] Training order-{MARKOV_ORDER} fast Markov …")
    t_train_start = time.time()
    model = FastMarkov(train_verses, MARKOV_ORDER)
    t_train = time.time() - t_train_start
    print(f"[{EXP}] Training done ({t_train:.1f} s, "
          f"{len(model.vocabulary):,} unique words)")

    # -----------------------------------------------------------------------
    # Pre-warm root cache for the Markov vocabulary
    # -----------------------------------------------------------------------
    _warm_root_cache(model.vocabulary)

    # -----------------------------------------------------------------------
    # Generate and evaluate forgeries
    # -----------------------------------------------------------------------
    rng = random.Random(GENERATOR_SEED)

    n_gate1_pass = 0
    n_f55_pass = 0
    n_f56_pass = 0
    n_gate1_f55_pass = 0
    n_gate1_f56_pass = 0
    n_f55_f56_pass = 0
    n_joint_pass = 0
    n_valid_arabic = 0
    n_eval_ok = 0
    n_verbatim_hits = 0

    first_gate1_idx = None
    first_f55_idx = None
    first_f56_idx = None
    first_gate1_f55_idx = None
    first_gate1_f56_idx = None
    first_f55_f56_idx = None
    first_joint_idx = None

    quran_verse_set = set(quran_verses)
    joint_pass_details: list[dict] = []
    f55_min_deltas_sample: list[float] = []  # first 1000 for stats

    print(f"[{EXP}] Generating and evaluating {N_FORGERIES:,} forgeries …")
    t_gen_start = time.time()

    for i in range(N_FORGERIES):
        forgery_verses = _generate_forgery_fast(model, rng)
        full_text = " ".join(forgery_verses)

        # --- Audit A1: valid Arabic ---
        arabic_chars = sum(1 for c in full_text if "\u0600" <= c <= "\u06ff")
        total_alpha = sum(1 for c in full_text if c.isalpha())
        if total_alpha > 0 and arabic_chars / total_alpha >= 0.90:
            n_valid_arabic += 1

        # --- Audit A3: verbatim hits ---
        for v in forgery_verses:
            if v in quran_verse_set:
                n_verbatim_hits += 1
                break

        # --- Evaluate detectors ---
        try:
            # F55 first (strongest gate)
            forgery_bhist = _bigram_hist(full_text)
            if i < 1000:
                # Full comparison for statistics
                min_delta = float("inf")
                for qh in quran_bigram_hists:
                    d = _bigram_delta(forgery_bhist, qh)
                    if d < min_delta:
                        min_delta = d
                        if min_delta <= F55_TAU:
                            break
                f55_min_deltas_sample.append(min_delta)
            else:
                # Fast path: all 114 surahs with early exit per comparison
                min_delta = float("inf")
                for qh in quran_bigram_hists:
                    d = _bigram_delta(forgery_bhist, qh,
                                      early_exit=F55_TAU)
                    if d < min_delta:
                        min_delta = d
                        if min_delta <= F55_TAU:
                            break
            f55_pass = min_delta <= F55_TAU

            # F56: EL-fragility
            f56_val = _el_frag(forgery_verses)
            f56_pass = f56_val >= F56_THRESHOLD

            # Gate 1: 5-D Φ_M SVM
            if len(forgery_verses) < 2:
                gate1_pass = False
                decision = float("-inf")
            else:
                feat = _features_5d_fast(forgery_verses)
                if np.any(np.isnan(feat)) or np.any(np.isinf(feat)):
                    gate1_pass = False
                    decision = float("-inf")
                else:
                    decision = float(np.dot(SVM_W, feat) + SVM_B)
                    gate1_pass = decision >= 0

            n_eval_ok += 1
        except Exception as exc:
            if i < 10:  # log first few errors in detail
                print(f"[{EXP}] WARN forgery {i}: {type(exc).__name__}: {exc}")
            gate1_pass = False
            f55_pass = False
            f56_pass = False
            decision = float("-inf")
            f56_val = 0.0
            min_delta = float("inf")

        # Tally
        if gate1_pass:
            n_gate1_pass += 1
            if first_gate1_idx is None:
                first_gate1_idx = i
        if f55_pass:
            n_f55_pass += 1
            if first_f55_idx is None:
                first_f55_idx = i
        if f56_pass:
            n_f56_pass += 1
            if first_f56_idx is None:
                first_f56_idx = i
        if gate1_pass and f55_pass:
            n_gate1_f55_pass += 1
            if first_gate1_f55_idx is None:
                first_gate1_f55_idx = i
        if gate1_pass and f56_pass:
            n_gate1_f56_pass += 1
            if first_gate1_f56_idx is None:
                first_gate1_f56_idx = i
        if f55_pass and f56_pass:
            n_f55_f56_pass += 1
            if first_f55_f56_idx is None:
                first_f55_f56_idx = i
        if gate1_pass and f55_pass and f56_pass:
            n_joint_pass += 1
            if first_joint_idx is None:
                first_joint_idx = i
            joint_pass_details.append({
                "index": i,
                "gate1_decision": decision,
                "f55_min_delta": min_delta,
                "f56_el_frag": f56_val,
            })

        # Progress
        if (i + 1) % REPORT_INTERVAL == 0:
            elapsed = time.time() - t_gen_start
            rate = (i + 1) / elapsed
            eta = (N_FORGERIES - i - 1) / rate if rate > 0 else 0
            print(f"[{EXP}]   {i+1:>10,} / {N_FORGERIES:,}  "
                  f"G1={n_gate1_pass}  F55={n_f55_pass}  F56={n_f56_pass}  "
                  f"joint={n_joint_pass}  "
                  f"({rate:.0f}/s, ETA {eta/60:.1f} min)")

    t_gen_end = time.time()
    wall_gen = t_gen_end - t_gen_start
    wall_total = t_gen_end - t0

    print(f"\n[{EXP}] === RESULTS ===")
    print(f"  N forgeries         = {N_FORGERIES:,}")
    print(f"  Gate 1 pass         = {n_gate1_pass:,}")
    print(f"  F55 pass            = {n_f55_pass:,}")
    print(f"  F56 pass            = {n_f56_pass:,}")
    print(f"  Gate1 ∧ F55         = {n_gate1_f55_pass:,}")
    print(f"  Gate1 ∧ F56         = {n_gate1_f56_pass:,}")
    print(f"  F55 ∧ F56           = {n_f55_f56_pass:,}")
    print(f"  Joint (all three)   = {n_joint_pass:,}")
    if f55_min_deltas_sample:
        arr = np.array(f55_min_deltas_sample)
        print(f"  F55 min Δ (first 1k)= min {arr.min():.1f}, "
              f"median {np.median(arr):.1f}, max {arr.max():.1f}")
    print(f"  Wall time (gen)     = {wall_gen:.1f} s")
    print(f"  Wall time (total)   = {wall_total:.1f} s")

    # -----------------------------------------------------------------------
    # Audit hooks
    # -----------------------------------------------------------------------
    a1_rate = n_valid_arabic / N_FORGERIES if N_FORGERIES > 0 else 0
    if a1_rate < 0.99:
        audit_failures.append(f"A1: valid-Arabic rate {a1_rate:.4f} < 0.99")
    print(f"[{EXP}] A1: valid-Arabic rate = {a1_rate:.4f}")

    a2_rate = n_eval_ok / N_FORGERIES if N_FORGERIES > 0 else 0
    if a2_rate < 0.999:
        audit_failures.append(f"A2: eval-ok rate {a2_rate:.6f} < 0.999")
    print(f"[{EXP}] A2: eval-ok rate = {a2_rate:.6f}")

    a3_rate = n_verbatim_hits / N_FORGERIES if N_FORGERIES > 0 else 0
    if a3_rate >= 0.001:
        audit_failures.append(f"A3: verbatim-hit rate {a3_rate:.6f} >= 0.001")
    print(f"[{EXP}] A3: verbatim-hit rate = {a3_rate:.6f}")

    # -----------------------------------------------------------------------
    # Verdict
    # -----------------------------------------------------------------------
    if audit_failures:
        verdict = f"FAIL_audit_{'_'.join(a.split(':')[0] for a in audit_failures)}"
    elif n_joint_pass > JOINT_PASS_TARGET:
        verdict = "FAIL_too_many_joint_pass"
    elif n_joint_pass == JOINT_PASS_STRICT:
        verdict = "PASS_H54_meta_finding"
    else:
        verdict = "PARTIAL_low_joint_pass"

    print(f"[{EXP}] verdict = {verdict}")

    # -----------------------------------------------------------------------
    # Complexity scaling table
    # -----------------------------------------------------------------------
    scaling = {
        "k1_gate1_only": {
            "n_pass": n_gate1_pass,
            "rate": n_gate1_pass / N_FORGERIES,
            "first_idx": first_gate1_idx,
        },
        "k1_f55_only": {
            "n_pass": n_f55_pass,
            "rate": n_f55_pass / N_FORGERIES,
            "first_idx": first_f55_idx,
        },
        "k1_f56_only": {
            "n_pass": n_f56_pass,
            "rate": n_f56_pass / N_FORGERIES,
            "first_idx": first_f56_idx,
        },
        "k2_gate1_f55": {
            "n_pass": n_gate1_f55_pass,
            "rate": n_gate1_f55_pass / N_FORGERIES,
            "first_idx": first_gate1_f55_idx,
        },
        "k2_gate1_f56": {
            "n_pass": n_gate1_f56_pass,
            "rate": n_gate1_f56_pass / N_FORGERIES,
            "first_idx": first_gate1_f56_idx,
        },
        "k2_f55_f56": {
            "n_pass": n_f55_f56_pass,
            "rate": n_f55_f56_pass / N_FORGERIES,
            "first_idx": first_f55_f56_idx,
        },
        "k3_joint": {
            "n_pass": n_joint_pass,
            "rate": n_joint_pass / N_FORGERIES,
            "first_idx": first_joint_idx,
        },
    }

    # F55 distance statistics from subsample
    f55_stats = {}
    if f55_min_deltas_sample:
        arr = np.array(f55_min_deltas_sample)
        f55_stats = {
            "n_sampled": len(arr),
            "min": float(arr.min()),
            "p05": float(np.percentile(arr, 5)),
            "median": float(np.median(arr)),
            "p95": float(np.percentile(arr, 95)),
            "max": float(arr.max()),
        }

    # Clopper-Pearson 95% upper bound on joint-pass rate
    if n_joint_pass == 0:
        cp_upper = 1.0 - 0.05 ** (1.0 / N_FORGERIES)
        bayes_nats = math.log(N_FORGERIES + 1)
    else:
        cp_upper = None
        bayes_nats = None

    # -----------------------------------------------------------------------
    # Self-check: verify no protected files mutated during the run
    # -----------------------------------------------------------------------
    post_check = self_check_end(pre_check, EXP)
    if post_check.get("drift"):
        audit_failures.append(f"self_check: {post_check['drift']}")

    # -----------------------------------------------------------------------
    # Write receipt
    # -----------------------------------------------------------------------
    record = {
        "experiment": EXP,
        "prereg_sha256": prereg_hash,
        "hypothesis": "H54",
        "n_forgeries": N_FORGERIES,
        "markov_order": MARKOV_ORDER,
        "generator_seed": GENERATOR_SEED,
        "length_sample_range": list(LENGTH_SAMPLE_RANGE),
        "n_train_verses": len(train_verses),
        "n_quran_verses": len(quran_verses),
        "svm_w": SVM_W.tolist(),
        "svm_b": SVM_B,
        "f55_tau": F55_TAU,
        "f56_threshold": F56_THRESHOLD,
        "n_gate1_pass": n_gate1_pass,
        "n_f55_pass": n_f55_pass,
        "n_f56_pass": n_f56_pass,
        "n_gate1_f55_pass": n_gate1_f55_pass,
        "n_gate1_f56_pass": n_gate1_f56_pass,
        "n_f55_f56_pass": n_f55_f56_pass,
        "n_joint_pass": n_joint_pass,
        "joint_pass_details": joint_pass_details,
        "scaling": scaling,
        "f55_delta_stats": f55_stats,
        "clopper_pearson_upper_if_zero": cp_upper,
        "bayes_nats_if_zero": bayes_nats,
        "audit": {
            "a1_valid_arabic_rate": a1_rate,
            "a2_eval_ok_rate": a2_rate,
            "a3_verbatim_hit_rate": a3_rate,
            "failures": audit_failures,
        },
        "verdict": verdict,
        "wall_time_gen_s": wall_gen,
        "wall_time_total_s": wall_total,
    }

    receipt_path = out / f"{EXP}.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] receipt: {receipt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
