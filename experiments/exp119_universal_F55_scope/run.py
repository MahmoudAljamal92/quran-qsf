"""exp119_universal_F55_scope — Test F55 forgery detector across 5 traditions.

Tests:
  Form 1 — theorem universality: Δ ≤ 2k for k-letter substitutions on all corpora.
  Form 2 — per-tradition recall ≥ 0.99 with τ_k = 2k.
  Form 3 — per-tradition peer FPR ≤ 0.05.
  Form 4 — exploratory cross-tradition edge sharpness.

Prereg: experiments/exp119_universal_F55_scope/PREREG.md
Hypothesis ID: H74.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _load_quran,
    _load_hebrew_tanakh,
    _load_greek_nt,
    _load_pali,
    _normalise_arabic,
    _normalise_hebrew,
    _normalise_greek,
    _normalise_pali,
)

# --- Sanskrit normaliser (Devanagari skeleton) -----------------------------
_DEVANAGARI_LETTERS = (
    "अआइईउऊऋॠऌॡएऐओऔ"
    "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"
    "ळऍऎऩ"
)
_DEVANAGARI_SET = set(_DEVANAGARI_LETTERS)


def _normalise_sanskrit(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c for c in s if c in _DEVANAGARI_SET)


def _load_rigveda() -> list[dict]:
    """Loads Rigveda sūktas as units. Each sūkta -> verses split on \\n\\n."""
    out: list[dict] = []
    sa_dir = ROOT / "data" / "corpora" / "sa"
    if not sa_dir.exists():
        return []
    files = sorted(sa_dir.glob("rigveda_mandala_*.json"))
    for fp in files:
        try:
            items = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        for it in items:
            mandala = it.get("mandala")
            sukta = it.get("sukta")
            text = it.get("text") or ""
            verses = [v.strip() for v in text.split("\n\n") if v.strip()]
            if len(verses) < 5:
                continue
            label = f"RV:{mandala}.{sukta:03d}" if isinstance(sukta, int) else f"RV:{mandala}.{sukta}"
            out.append({
                "corpus": "rigveda",
                "label": label,
                "verses": verses,
                "normaliser": "sanskrit",
            })
    return out


NORMALISERS = {
    "arabic":    _normalise_arabic,
    "hebrew":    _normalise_hebrew,
    "greek":     _normalise_greek,
    "pali":      _normalise_pali,
    "sanskrit":  _normalise_sanskrit,
}

ALPHABETS = {
    "arabic":    list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"),
    "hebrew":    list("אבגדהוזחטיכלמנסעפצקרשת"),
    "greek":     list("αβγδεζηθικλμνξοπρστυφχψω"),
    "pali":      list("a\u0101i\u012Bu\u016Beokg\u1E45cj\u00F1\u1E6D\u1E0D\u1E47tdnpbmyrl\u1E37vsh\u1E41"),
    "sanskrit":  list(_DEVANAGARI_LETTERS),
}

# --- Constants -------------------------------------------------------------
K_VALUES = [1, 2, 3]
N_SUBS_PER_UNIT = 200
N_FPR_PAIRS = 2000
SEED_BASE = 1119
RECALL_FLOOR = 0.99
FPR_CEILING = 0.05
PREREG_PATH = ROOT / "experiments/exp119_universal_F55_scope/PREREG.md"


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalize_unit(unit: dict) -> str:
    """Apply the unit's normaliser to all verses, joined by space."""
    fn = NORMALISERS[unit["normaliser"]]
    parts = [fn(v) for v in unit["verses"]]
    parts = [p for p in parts if p]
    return " ".join(parts)


def bigram_histogram(text: str) -> dict:
    """Bigram counts within words (ignore space-letter and letter-space transitions)."""
    h: dict = {}
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i + 2]
            h[bg] = h.get(bg, 0) + 1
    return h


def delta_bigram(h1: dict, h2: dict) -> float:
    keys = set(h1) | set(h2)
    return sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys) / 2.0


def pick_k_subs(text: str, k: int, alphabet: list, alph_set: set,
                rng: random.Random) -> dict | None:
    """Pick k random in-alphabet positions and pick replacement letters.
    Returns dict {pos: new_char} or None if text too short. Preserves the
    exact RNG-call sequence of the un-optimised version (rng.sample then
    rng.choice per position) so seeded results are identical.
    """
    positions = [i for i, c in enumerate(text) if c in alph_set]
    if len(positions) < k:
        return None
    chosen = rng.sample(positions, k)
    subs = {}
    for p in chosen:
        old = text[p]
        new = rng.choice([L for L in alphabet if L != old])
        subs[p] = new
    return subs


def delta_after_k_subs(text: str, subs: dict) -> float:
    """Compute Δ_bigram between text and (text with chars replaced per subs)
    in O(k) time — only the bigrams that contain a substituted position
    can change. Used for the recall / theorem loop.
    """
    if not subs:
        return 0.0
    affected_bp = set()
    L = len(text)
    for p in subs:
        # bigram (p-1, p): valid if both chars are non-space
        if p > 0 and text[p - 1] != " " and text[p] != " ":
            affected_bp.add(p - 1)
        # bigram (p, p+1): valid if both chars are non-space
        if p + 1 < L and text[p] != " " and text[p + 1] != " ":
            affected_bp.add(p)
    diff: dict = {}
    for bp in affected_bp:
        old_c1 = text[bp]
        old_c2 = text[bp + 1]
        new_c1 = subs.get(bp, old_c1)
        new_c2 = subs.get(bp + 1, old_c2)
        old_bg = old_c1 + old_c2
        new_bg = new_c1 + new_c2
        if old_bg != new_bg:
            diff[old_bg] = diff.get(old_bg, 0) - 1
            diff[new_bg] = diff.get(new_bg, 0) + 1
    return sum(abs(v) for v in diff.values()) / 2.0


def run_corpus(name: str, units: list, normaliser_name: str) -> dict:
    """Run all 4 forms for one corpus."""
    alphabet = ALPHABETS[normaliser_name]
    alph_set = set(alphabet)
    print(f"\n=== {name} ({len(units)} units, {normaliser_name} alphabet={len(alphabet)}) ===")

    # Pre-normalize all units
    normed = {}
    for u in units:
        nt = normalize_unit(u)
        if len(nt) >= 50:  # min sizing
            normed[u["label"]] = nt
    print(f"  Usable units after normalisation: {len(normed)}")
    if len(normed) < 5:
        return {"corpus": name, "skipped": True, "reason": "too_few_units"}

    median_skel_len = float(np.median([len(t) for t in normed.values()]))

    # Cache bigram histograms once per unit (used for FPR comparisons; the
    # recall loop uses the O(k) delta_after_k_subs and never needs them).
    print("  Pre-computing per-unit bigram histograms (cache)...")
    hist_cache = {label: bigram_histogram(text) for label, text in normed.items()}

    out = {
        "corpus": name,
        "alphabet_size": len(alphabet),
        "n_units_used": len(normed),
        "median_skeleton_length": median_skel_len,
        "per_k": {},
    }

    for k in K_VALUES:
        rng = random.Random(SEED_BASE * 100 + k * 13 + hash(name) % 997)

        # Form 1+2: theorem + recall on this corpus (incremental Δ — O(k) per sub)
        all_deltas = []
        n_violations = 0
        n_zero = 0
        for label, text in normed.items():
            for _ in range(N_SUBS_PER_UNIT):
                subs = pick_k_subs(text, k, alphabet, alph_set, rng)
                if subs is None:
                    continue
                d = delta_after_k_subs(text, subs)
                all_deltas.append(d)
                if d > 2 * k + 1e-9:
                    n_violations += 1
                if d == 0.0:
                    n_zero += 1
        all_deltas = np.array(all_deltas)
        n_total = len(all_deltas)
        n_fired = int(((all_deltas > 0) & (all_deltas <= 2 * k)).sum())
        recall = n_fired / max(1, n_total)

        # Form 3: peer FPR (within-corpus distinct-chapter pairs) — use cache
        keys = list(normed.keys())
        fpr_rng = random.Random(SEED_BASE * 100 + k * 13 + hash(name + "fpr") % 997)
        n_fpr_below = 0
        peer_deltas = []
        for _ in range(N_FPR_PAIRS):
            if len(keys) < 2:
                break
            a, b = fpr_rng.sample(keys, 2)
            d = delta_bigram(hist_cache[a], hist_cache[b])
            peer_deltas.append(d)
            if d <= 2 * k:
                n_fpr_below += 1
        peer_deltas = np.array(peer_deltas) if peer_deltas else np.array([0.0])
        fpr = n_fpr_below / max(1, len(peer_deltas))

        out["per_k"][k] = {
            "tau_k": 2 * k,
            "n_subs": n_total,
            "max_delta": float(all_deltas.max()),
            "mean_delta": float(all_deltas.mean()),
            "n_violations": n_violations,
            "theorem_holds": n_violations == 0,
            "n_zero_delta": n_zero,
            "n_fired": n_fired,
            "recall": recall,
            "recall_pass": recall >= RECALL_FLOOR,
            "n_fpr_pairs": int(len(peer_deltas)),
            "n_fpr_below": n_fpr_below,
            "fpr": fpr,
            "fpr_pass": fpr <= FPR_CEILING,
            "peer_min_delta": float(peer_deltas.min()),
            "peer_median_delta": float(np.median(peer_deltas)),
            "peer_max_delta": float(peer_deltas.max()),
        }
        r = out["per_k"][k]
        print(f"  k={k}: max(Δ)={r['max_delta']:.2f} (≤{2*k}? {r['theorem_holds']}), "
              f"recall={recall:.4f} (≥{RECALL_FLOOR}? {r['recall_pass']}), "
              f"FPR={fpr:.4f} (≤{FPR_CEILING}? {r['fpr_pass']}), "
              f"peer_min={r['peer_min_delta']:.1f}")

    # Form 4 (exploratory): edge metric using k=1 peer_min_delta
    pmd1 = out["per_k"][1]["peer_min_delta"]
    out["edge_k1"] = pmd1 / max(1.0, median_skel_len)
    return out


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    out_dir = ROOT / "results" / "experiments" / "exp119_universal_F55_scope"
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus_loaders = [
        ("quran",         _load_quran,         "arabic"),
        ("hebrew_tanakh", _load_hebrew_tanakh, "hebrew"),
        ("greek_nt",      _load_greek_nt,      "greek"),
        ("pali",          _load_pali,          "pali"),
        ("rigveda",       _load_rigveda,       "sanskrit"),
    ]

    all_results = []
    for name, loader, normaliser_name in corpus_loaders:
        try:
            units = loader()
        except Exception as e:
            print(f"# WARN: loader for {name} failed: {e}", file=sys.stderr)
            all_results.append({"corpus": name, "skipped": True, "reason": f"loader_error: {e}"})
            continue
        if not units:
            all_results.append({"corpus": name, "skipped": True, "reason": "no_units"})
            continue
        all_results.append(run_corpus(name, units, normaliser_name))

    # Aggregate verdict
    active = [r for r in all_results if not r.get("skipped")]
    theorem_ok_all = all(
        all(pk["theorem_holds"] for pk in r["per_k"].values())
        for r in active
    )
    recall_ok_all = all(
        all(pk["recall_pass"] for pk in r["per_k"].values())
        for r in active
    )
    fpr_ok_all = all(
        all(pk["fpr_pass"] for pk in r["per_k"].values())
        for r in active
    )

    if not theorem_ok_all:
        verdict = "FAIL_theorem_violated"
    elif not recall_ok_all:
        verdict = "PARTIAL_PASS_recall_uneven"
    elif not fpr_ok_all:
        verdict = "PARTIAL_PASS_FPR_too_high_in_some_traditions"
    else:
        verdict = "PASS_F55_universal_across_5_traditions"

    finished = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": "exp119_universal_F55_scope",
        "hypothesis_id": "H74",
        "verdict": verdict,
        "started_at_utc": started,
        "completed_at_utc": finished,
        "prereg_document": "experiments/exp119_universal_F55_scope/PREREG.md",
        "prereg_sha256": _sha256(PREREG_PATH),
        "frozen_constants": {
            "K_VALUES": K_VALUES,
            "N_SUBS_PER_UNIT": N_SUBS_PER_UNIT,
            "N_FPR_PAIRS": N_FPR_PAIRS,
            "SEED_BASE": SEED_BASE,
            "RECALL_FLOOR": RECALL_FLOOR,
            "FPR_CEILING": FPR_CEILING,
        },
        "n_traditions_tested": len(active),
        "per_corpus": all_results,
    }
    out_path = out_dir / "exp119_universal_F55_scope.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== exp119 — F55 Universal-Language Scope ===\n")
    print(f"Active traditions: {len(active)}/{len(corpus_loaders)}")
    print(f"Theorem holds everywhere:  {theorem_ok_all}")
    print(f"Recall ≥ {RECALL_FLOOR} everywhere:  {recall_ok_all}")
    print(f"FPR ≤ {FPR_CEILING} everywhere:    {fpr_ok_all}")
    print(f"\nVerdict: {verdict}")
    print(f"Receipt: {out_path.relative_to(ROOT)}")

    # Edge ranking (descriptive)
    print("\nForm 4 (descriptive) — edge_k1 = peer_min_Δ(k=1) / median_skeleton_length:")
    edges = [(r["corpus"], r["edge_k1"], r["per_k"][1]["peer_min_delta"], r["median_skeleton_length"])
             for r in active]
    edges.sort(key=lambda x: x[1], reverse=True)
    for name, edge, pmd, mlen in edges:
        print(f"  {name:<14s}  edge={edge:.5f}  peer_min_Δ={pmd:.1f}  median_skel={mlen:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
