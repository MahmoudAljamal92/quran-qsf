"""experiments/exp112_F55_daodejing_bigram/run.py
======================================================
F55 universal symbolic forgery detector on Classical Chinese Daodejing
Chapter 1. Tests F55 on the first LOGOGRAPHIC writing system in the
cross-tradition series (extending from 5 alphabetic / IAST-Roman /
Latin-transliterated traditions: Arabic, Hebrew, Greek, Pāli, Avestan).

By Theorem 3.2 (`exp95j` PREREG), F55 must pass with recall = 1.000.
The empirical question is whether peer FPR = 0 against the 80-chapter
Daodejing peer pool with frozen τ = 2.0.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
PREREG_PATH = HERE / "PREREG.md"
RECEIPT_PATH = (
    ROOT / "results" / "experiments" /
    "exp112_F55_daodejing_bigram" / "exp112_F55_daodejing_bigram.json"
)
DAODEJING_PATH = ROOT / "data" / "corpora" / "zh" / "daodejing_wangbi.txt"
DAODEJING_MANIFEST = ROOT / "data" / "corpora" / "zh" / "manifest.json"

TAU = 2.0
PEER_AUDIT_FLOOR = 50
TARGET_LETTERS_FLOOR = 30


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ============================================================================
# CJK Ideograph normaliser (locked at PREREG seal)
# ============================================================================
def _is_cjk_ideograph(c: str) -> bool:
    """True if c is in CJK Unified Ideographs (U+4E00-U+9FFF) or
    CJK Unified Ideographs Ext-A (U+3400-U+4DBF) or
    CJK Compatibility Ideographs (U+F900-U+FAFF)."""
    if not c:
        return False
    o = ord(c)
    return (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF
            or 0xF900 <= o <= 0xFAFF)


def normalise_chinese(s: str) -> str:
    return "".join(c for c in s if _is_cjk_ideograph(c))


def load_daodejing_chapters() -> list[dict]:
    text = DAODEJING_PATH.read_text(encoding="utf-8")
    parts = re.split(r"第[一二三四五六七八九十百零]+章\s*", text)
    parts = [p.strip() for p in parts if p.strip()]
    out = []
    for i, p in enumerate(parts, start=1):
        out.append({"chapter": i, "raw": p,
                    "skeleton": normalise_chinese(p)})
    return out


def bigram_dist_l1_half(a: str, b: str) -> float:
    """L1 norm of bigram-histogram difference, halved (= the 'Δ_bigram'
    statistic from F55 protocol, theorem upper-bound = 2 for any single
    char substitution)."""
    if len(a) < 2 and len(b) < 2:
        return 0.0
    ha = Counter(a[i:i+2] for i in range(len(a) - 1))
    hb = Counter(b[i:i+2] for i in range(len(b) - 1))
    keys = set(ha) | set(hb)
    return 0.5 * sum(abs(ha.get(k, 0) - hb.get(k, 0)) for k in keys)


def main() -> int:
    print("# === exp112_F55_daodejing_bigram — execution ===")
    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    prereg_bytes = PREREG_PATH.read_bytes()
    prereg_hash = _sha256(prereg_bytes)
    print(f"# PREREG hash: {prereg_hash}")

    # Audit A0: source-file SHA-256 vs manifest
    man = json.loads(DAODEJING_MANIFEST.read_text(encoding="utf-8"))
    expected_sha = man["files"][0]["sha256"]
    actual_sha = _sha256(DAODEJING_PATH.read_bytes())
    a0_ok = (expected_sha == actual_sha)
    print(f"# A0 (corpus SHA-256): "
          f"{'OK' if a0_ok else f'FAIL drift {actual_sha[:16]} vs expected {expected_sha[:16]}'}")

    # Load chapters
    chapters = load_daodejing_chapters()
    print(f"# loaded {len(chapters)} chapters")

    target = chapters[0]  # Chapter 1
    target_skel = target["skeleton"]
    print(f"# target chapter 1 skeleton: {target_skel}")
    print(f"# target skeleton chars: {len(target_skel)}")

    # Audit A3: target chapter floor
    a3_ok = len(target_skel) >= TARGET_LETTERS_FLOOR
    print(f"# A3 (target chapter ≥ {TARGET_LETTERS_FLOOR} ideographs): "
          f"{'OK' if a3_ok else 'FAIL'}; actual = {len(target_skel)}")

    # Audit A5: skeleton sentinel
    expected_prefix = "道可道非常道"
    a5_ok = target_skel.startswith(expected_prefix)
    print(f"# A5 (skeleton sentinel '{expected_prefix}'): "
          f"{'OK' if a5_ok else 'FAIL'}; actual prefix = {target_skel[:6]}")

    # Build corpus-attested distinct character alphabet
    full_corpus_skeleton = "".join(c["skeleton"] for c in chapters)
    alphabet = sorted(set(full_corpus_skeleton))
    print(f"# corpus distinct CJK ideographs: {len(alphabet)}")
    print(f"# total corpus skeleton characters: {len(full_corpus_skeleton)}")

    # Audit A2: peer pool size
    peers = chapters[1:]  # chapters 2-81
    a2_ok = len(peers) >= PEER_AUDIT_FLOOR
    print(f"# A2 (peer pool ≥ {PEER_AUDIT_FLOOR}): "
          f"{'OK' if a2_ok else 'FAIL'}; actual = {len(peers)}")

    # Recall test: every single-char substitution
    # F55 detector fires when 0 < Δ ≤ τ (per exp95j convention; τ is an
    # UPPER BOUND on Δ, not a lower bound). By theorem any single-char
    # substitution has Δ ≤ 2, so all variants must fire if real (Δ > 0).
    print(f"\n# 1. Recall test ({len(target_skel)} positions × "
          f"{len(alphabet) - 1} substitutes per position):")
    n_variants = 0
    n_passing = 0
    max_delta = 0.0
    min_delta = float("inf")
    rec_t0 = time.time()
    for i in range(len(target_skel)):
        original_ch = target_skel[i]
        for c in alphabet:
            if c == original_ch:
                continue
            variant = target_skel[:i] + c + target_skel[i+1:]
            d = bigram_dist_l1_half(target_skel, variant)
            n_variants += 1
            if 0 < d <= TAU:
                n_passing += 1
            if d > max_delta:
                max_delta = d
            if d < min_delta:
                min_delta = d
    recall = n_passing / n_variants
    print(f"#   total variants: {n_variants}")
    print(f"#   firing (0 < Δ ≤ τ={TAU}): {n_passing}")
    print(f"#   recall: {recall:.6f}")
    print(f"#   max(variant Δ): {max_delta:.6f}")
    print(f"#   min(variant Δ): {min_delta:.6f}")
    rec_t = time.time() - rec_t0
    print(f"#   recall wall-time: {rec_t:.2f}s")

    # Audit A1: theorem
    a1_ok = max_delta <= TAU + 1e-9
    print(f"# A1 (theorem max Δ ≤ 2.0): "
          f"{'OK' if a1_ok else 'FAIL'}; observed max = {max_delta}")

    # Peer FPR test
    print(f"\n# 2. Peer FPR test (target vs each of {len(peers)} peers):")
    peer_deltas = []
    for p in peers:
        d = bigram_dist_l1_half(target_skel, p["skeleton"])
        peer_deltas.append((p["chapter"], d, len(p["skeleton"])))
    peer_deltas.sort(key=lambda t: t[1])
    # FPR = peer fires under (0 < Δ ≤ τ) — same firing rule as recall.
    # A peer fire = false positive (the detector mistakes a different
    # chapter for a single-char-variant of the target).
    n_peer_fail = sum(1 for (_, d, _) in peer_deltas if 0 < d <= TAU)
    n_peer_total = len(peer_deltas)
    fpr = n_peer_fail / n_peer_total
    min_peer_delta = peer_deltas[0][1]
    closest_peer = peer_deltas[0][0]
    print(f"#   peer FPR: {fpr:.6f}")
    print(f"#   min(peer Δ): {min_peer_delta:.4f} (from chapter {closest_peer})")
    print(f"#   5 closest peers (chapter, Δ, skeleton_len):")
    for c, d, n in peer_deltas[:5]:
        print(f"#     chapter {c:>2d}: Δ = {d:>10.4f}, skeleton = {n} chars")
    print(f"#   safety margin (min_peer / τ): {min_peer_delta / TAU:.2f}×")
    if len(target_skel) > 0:
        norm_margin = min_peer_delta / len(target_skel)
        print(f"#   length-normalised per-char margin: {norm_margin:.4f}")
    else:
        norm_margin = 0.0

    # Audit A4: determinism re-score (10 random variants)
    print(f"\n# 3. Determinism re-score (10 random variants):")
    import random
    rng = random.Random(112)
    variant_set = []
    for _ in range(10):
        i = rng.randrange(len(target_skel))
        c = rng.choice([a for a in alphabet if a != target_skel[i]])
        variant = target_skel[:i] + c + target_skel[i+1:]
        d1 = bigram_dist_l1_half(target_skel, variant)
        d2 = bigram_dist_l1_half(target_skel, variant)
        variant_set.append((i, c, d1, d2, d1 == d2))
    a4_ok = all(t[4] for t in variant_set)
    print(f"# A4 (determinism, 10 re-scored): "
          f"{'OK (all byte-identical)' if a4_ok else 'FAIL'}")

    # Verdict
    cond_recall = abs(recall - 1.0) < 1e-9
    cond_fpr = (fpr == 0.0)
    cond_audits = a0_ok and a1_ok and a2_ok and a3_ok and a4_ok and a5_ok

    if cond_recall and cond_fpr and cond_audits:
        verdict = "PASS_universal_perfect_recall_zero_fpr"
    elif not cond_recall:
        verdict = "FAIL_recall_below_unity"
    elif not cond_fpr:
        verdict = "FAIL_peer_fpr_nonzero"
    else:
        verdict = "FAIL_audit"

    print(f"\n# VERDICT: {verdict}")
    wall = time.time() - t0
    finished_at = datetime.now(timezone.utc)
    print(f"# wall-time: {wall:.1f}s")

    receipt = {
        "experiment": "exp112_F55_daodejing_bigram",
        "hypothesis_id": "H67",
        "verdict": verdict,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "wall_seconds": wall,
        "prereg_path": str(PREREG_PATH.relative_to(ROOT)),
        "prereg_sha256": prereg_hash,
        "tau": TAU,
        "scope": ("F55 universal symbolic forgery detector on Classical "
                  "Chinese Daodejing Chapter 1 (Wang Bi recension; CJK "
                  "Unified Ideograph skeleton; first logographic / "
                  "character-based writing system tested)"),
        "corpus": {
            "name": "daodejing_wangbi",
            "source": "Project Gutenberg eBook #7337",
            "license": "PUBLIC DOMAIN",
            "sha256": actual_sha,
            "n_chapters": len(chapters),
            "total_skeleton_chars": len(full_corpus_skeleton),
            "distinct_corpus_chars": len(alphabet),
        },
        "target": {
            "chapter": 1,
            "skeleton_chars": len(target_skel),
            "skeleton_first_30": target_skel[:30],
        },
        "recall": {
            "n_variants": n_variants,
            "n_passing": n_passing,
            "recall": recall,
            "max_variant_delta": max_delta,
        },
        "peer_fpr": {
            "n_peers": n_peer_total,
            "n_failing": n_peer_fail,
            "fpr": fpr,
            "min_peer_delta": min_peer_delta,
            "min_peer_chapter": closest_peer,
            "5_closest_peers": [
                {"chapter": c, "delta": float(d), "skeleton_len": n}
                for (c, d, n) in peer_deltas[:5]
            ],
            "safety_margin_over_tau": min_peer_delta / TAU,
            "length_normalised_per_char_margin": norm_margin,
        },
        "audit_report": {
            "ok": bool(cond_audits),
            "a0_corpus_sha256": {"ok": a0_ok,
                                 "expected": expected_sha[:16],
                                 "actual": actual_sha[:16]},
            "a1_theorem_max_delta_le_2": {"ok": a1_ok,
                                          "observed_max": max_delta},
            "a2_peer_pool_size": {"ok": a2_ok,
                                  "actual": len(peers),
                                  "floor": PEER_AUDIT_FLOOR},
            "a3_target_chapter_floor": {"ok": a3_ok,
                                        "actual": len(target_skel),
                                        "floor": TARGET_LETTERS_FLOOR},
            "a4_determinism_rescore": {"ok": a4_ok,
                                       "n_rescored": len(variant_set)},
            "a5_skeleton_sentinel": {"ok": a5_ok,
                                     "expected_prefix": expected_prefix,
                                     "actual_prefix": target_skel[:6]},
        },
        "calibration_source": ("none — analytic theorem-bound τ = 2.0; "
                                "no empirical calibration"),
        "language_family": "Sino-Tibetan / Sinitic",
        "writing_system": "logographic (CJK Unified Ideographs)",
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"# receipt: {RECEIPT_PATH}")
    return 0 if verdict.startswith("PASS_") else 1


if __name__ == "__main__":
    sys.exit(main())
