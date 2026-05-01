"""
exp04_onomatopoeia/run.py
=========================
Directional onomatopoeia index (O-index) — follow-up to exp03 Q3/Q4.

Hypothesis (motivated by exp03 Q4): classical Arabic rhetoric on sūra 100
cites SPECIFIC consonants — ب for stomping (ضَبْح, نَقْع), ر for rolling
(قَدْح) — while Ādiyāt also *suppresses* certain others (ك, أ, ت). Bulk
plosive-density (exp03 Q3) missed this because the under-representation
cancelled the over-representation in a set average.

We define a SIGNED log-ratio onomatopoeia index:

    O(unit) = Σ_{c ∈ POS} log10((f_c + ε) / (p_c + ε))
            - Σ_{c ∈ NEG} log10((f_c + ε) / (p_c + ε))

where f_c is the observed letter frequency in the unit, p_c is the
reference Arabic corpus-wide frequency, POS = {ب, ر}, NEG = {ك, أ, ت},
ε = 1e-4 to regularise small counts.

**Pre-registration, no HARKing**: the POS/NEG set is locked from exp03
Q4's top ±5 deviations. We do not tune it based on the O-index result.
The classical-onomatopoeia sūrahs we test against the index are listed
in the code before any computation on them.

Reads (read-only via integrity-checked loader):
  - phase_06_phi_m.pkl  (CORPORA)

Writes (only under results/experiments/exp04_onomatopoeia/):
  - exp04_onomatopoeia.json
  - fig_o_index_distribution.png
  - fig_named_onomatopoeia_surahs.png
  - self_check_<ts>.json
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

EXP = "exp04_onomatopoeia"

# ---------------------------------------------------------------------------
# CIRCULARITY DISCLOSURE (AUDIT 2026-04-19):
# These letter sets were derived from exp03 Q4's top ±5 residuals computed
# on sūra 100 itself. Therefore:
#   - The O-index for sūra 100 is NOT independent of the index construction.
#     It is EXPECTED to be high and CANNOT be used as evidence of a real
#     phonetic effect. It is retained in the table as a descriptive anchor.
#   - The scientifically valid test is the GENERALISATION test: does the
#     index, derived from sūra 100, flag OTHER surahs that classical
#     rhetoric claims are onomatopoeic? This is the t_test_held_out below.
# ---------------------------------------------------------------------------
POS_LETTERS = set("بر")    # stomp + roll   (source: exp03 Q4 on sūra 100)
NEG_LETTERS = set("كأت")   # suppressed     (source: exp03 Q4 on sūra 100)
EPS = 1e-4

# Pre-registered "named onomatopoeia" sūrahs from classical rhetoric.
# Q100 is EXCLUDED from the held-out test below because it was used to
# derive POS/NEG. It is kept in NAMED_ONOMATOPOEIA for the descriptive table.
NAMED_ONOMATOPOEIA = {
    100: "al-ʿĀdiyāt (galloping horses) [IN-SAMPLE, EXCLUDED from t-test]",
    101: "al-Qāriʿa (crashing impact)",
    99:  "al-Zalzala (earthquake rumble)",
    77:  "al-Mursalāt (sending winds)",
    79:  "al-Nāziʿāt (plucking souls)",
    81:  "al-Takwīr (spinning collapse)",
    82:  "al-Infiṭār (splitting)",
    84:  "al-Inshiqāq (rending)",
}

# The HELD-OUT surahs for the circularity-free generalisation test.
# Q100 is NOT here because POS/NEG were fitted on it.
NAMED_ONOMATOPOEIA_HELDOUT = {
    k: v for k, v in NAMED_ONOMATOPOEIA.items() if k != 100
}


def _strip_d(s: str) -> str:
    return ft._strip_d(s)


def letter_counts(text: str) -> Counter:
    return Counter(c for c in _strip_d(text) if c.isalpha())


def o_index(counts: Counter, ref_freq: dict[str, float]) -> float:
    """Directional log-ratio onomatopoeia index of a single unit."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    score = 0.0
    for c in POS_LETTERS:
        f = (counts.get(c, 0) / total)
        p = ref_freq.get(c, EPS)
        score += math.log10((f + EPS) / (p + EPS))
    for c in NEG_LETTERS:
        f = (counts.get(c, 0) / total)
        p = ref_freq.get(c, EPS)
        score -= math.log10((f + EPS) / (p + EPS))
    return score


def _surah_num(label: str) -> int | None:
    try:
        return int(str(label).split(":")[-1])
    except Exception:
        return None


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # ---------- Reference Arabic letter distribution ----------
    # Computed from the non-hadith, non-Quran pool (so it's not circular vs Quran)
    ref_corpora = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "arabic_bible", "hindawi"]
    ref_counter: Counter = Counter()
    for c in ref_corpora:
        for u in CORPORA.get(c, []):
            ref_counter.update(letter_counts(" ".join(u.verses)))
    ref_total = sum(ref_counter.values())
    ref_freq = {c: n / ref_total for c, n in ref_counter.items()}

    # ---------- O-index for every Quran surah ----------
    quran_units = CORPORA["quran"]
    O_quran = []
    labels_q = []
    for u in quran_units:
        c = letter_counts(" ".join(u.verses))
        O_quran.append(o_index(c, ref_freq))
        labels_q.append(u.label)
    O_quran = np.array(O_quran)
    labels_q = np.array(labels_q)

    # ---------- O-index for every Arabic control unit ----------
    O_ctrl = []
    src_ctrl = []
    for c in ref_corpora:
        for u in CORPORA.get(c, []):
            cnt = letter_counts(" ".join(u.verses))
            if sum(cnt.values()) < 50:  # too short to trust
                continue
            O_ctrl.append(o_index(cnt, ref_freq))
            src_ctrl.append(c)
    O_ctrl = np.array(O_ctrl)

    # ---------- Key statistics ----------
    # Distribution summary
    q_mean, q_std = float(O_quran.mean()), float(O_quran.std(ddof=1))
    c_mean, c_std = float(O_ctrl.mean()), float(O_ctrl.std(ddof=1))

    # Where does each named onomatopoeia surah rank?
    named_results = {}
    for num, name in NAMED_ONOMATOPOEIA.items():
        lbl = f"Q:{num:03d}"
        idx = np.where(labels_q == lbl)[0]
        if len(idx) == 0:
            named_results[num] = {"name": name, "found": False}
            continue
        O_val = float(O_quran[idx[0]])
        rank_q = int(np.sum(O_quran > O_val)) + 1
        # one-sided p_tail vs controls (right tail)
        p_tail = float((np.sum(O_ctrl >= O_val) + 1) / (len(O_ctrl) + 1))
        z = (O_val - c_mean) / max(c_std, 1e-9)
        named_results[num] = {
            "name": name,
            "found": True,
            "label": lbl,
            "O_index": O_val,
            "z_vs_ctrl": float(z),
            "rank_in_quran": rank_q,
            "p_tail_vs_ctrl": p_tail,
        }

    # Cross-corpus mean O-index (positive = Quran-like)
    O_by_corpus = {}
    for c in ref_corpora:
        vals = [O_ctrl[i] for i in range(len(O_ctrl)) if src_ctrl[i] == c]
        if vals:
            O_by_corpus[c] = {"mean": float(np.mean(vals)),
                              "std": float(np.std(vals, ddof=1) if len(vals) > 1 else 0.0),
                              "n": int(len(vals))}
    O_by_corpus["quran"] = {"mean": q_mean, "std": q_std, "n": int(len(O_quran))}

    # AUDIT FIX 2026-04-19: Two t-tests.
    # (1) In-sample (includes Q100) — NOT circularity-free, descriptive only.
    # (2) Held-out (Q100 excluded) — the scientifically valid test since
    #     POS/NEG were fitted on Q100.
    named_nums_found = [n for n, r in named_results.items() if r.get("found")]
    named_O = np.array([named_results[n]["O_index"] for n in named_nums_found])
    rest_mask = np.array(
        [(_surah_num(l) not in set(named_nums_found)) for l in labels_q]
    )
    rest_O = O_quran[rest_mask]

    from scipy import stats as _st

    def _run_ttest(named_O_vec, rest_O_vec):
        if len(named_O_vec) < 3 or len(rest_O_vec) < 5:
            return None
        t_stat, p_one = _st.ttest_ind(named_O_vec, rest_O_vec,
                                      alternative="greater", equal_var=False)
        return {"t": float(t_stat), "p_one_sided": float(p_one),
                "n_named": int(len(named_O_vec)),
                "n_rest": int(len(rest_O_vec)),
                "mean_named": float(named_O_vec.mean()),
                "mean_rest": float(rest_O_vec.mean())}

    # In-sample (contains Q100 — circular)
    t_test_in_sample = _run_ttest(named_O, rest_O)

    # Held-out: exclude Q100 from the named side AND the rest side
    # (so Q100 doesn't leak by being in the control mean either)
    heldout_nums = [n for n in named_nums_found if n != 100]
    heldout_O = np.array([named_results[n]["O_index"] for n in heldout_nums])
    heldout_rest_mask = np.array(
        [(_surah_num(l) not in set(named_nums_found)) and (_surah_num(l) != 100)
         for l in labels_q]
    )
    heldout_rest_O = O_quran[heldout_rest_mask]
    t_test_held_out = _run_ttest(heldout_O, heldout_rest_O)

    t_test = {
        "in_sample_includes_Q100": t_test_in_sample,
        "held_out_Q100_excluded": t_test_held_out,
        "audit_note": (
            "Primary test is held_out_Q100_excluded (Q100 was used to "
            "derive POS/NEG letter sets). The in-sample result is biased "
            "and reported only for cross-reference."
        ),
    }

    # ---------- Plots ----------
    # Fig A: O-index distribution Quran vs controls + named highlights
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(O_ctrl, bins=60, alpha=0.55, color="#999",
            label=f"Arabic controls (n={len(O_ctrl)})")
    ax.hist(O_quran, bins=30, alpha=0.7, color="#2b8cbe",
            label=f"Quran (n={len(O_quran)})")
    ymax = ax.get_ylim()[1]
    for num in named_nums_found:
        r = named_results[num]
        ax.axvline(r["O_index"], color="crimson", lw=0.9, alpha=0.7)
        ax.text(r["O_index"], ymax * (0.85 - 0.06 * (num % 5)),
                f"Q{num}", fontsize=7, color="crimson", rotation=90, va="top")
    ax.set_xlabel("Directional onomatopoeia index O = Σ_{b,r} − Σ_{k,a,t}")
    ax.set_ylabel("count")
    ax.set_title("O-index: Quran vs. Arabic controls (red = named-onomatopoeia sūrahs)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_o_index_distribution.png", dpi=130)
    plt.close(fig)

    # Fig B: named-onomatopoeia surahs ranked vs. Quran background
    fig, ax = plt.subplots(figsize=(7, 4.5))
    # sort by O-index
    items = sorted(named_nums_found, key=lambda n: -named_results[n]["O_index"])
    xs = [named_results[n]["O_index"] for n in items]
    labels_disp = [f"Q{n}\n({named_results[n]['name'].split(' (')[0]})" for n in items]
    ax.bar(range(len(xs)), xs, color="#c44")
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(labels_disp, rotation=30, ha="right", fontsize=8)
    ax.axhline(q_mean, color="navy", ls="--", lw=0.8,
               label=f"Quran mean = {q_mean:.3f}")
    ax.axhline(c_mean, color="black", ls=":", lw=0.8,
               label=f"Ctrl mean = {c_mean:.3f}")
    ax.set_ylabel("O-index")
    ax.set_title("Named-onomatopoeia sūrahs vs. Quran/control means")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_named_onomatopoeia_surahs.png", dpi=130)
    plt.close(fig)

    # ---------- Report ----------
    report = {
        "experiment": EXP,
        "description": (
            "Directional onomatopoeia index. POS = {ب, ر}, NEG = {ك, أ, ت} "
            "locked pre-registration from exp03 Q4. Tests whether classical "
            "named-onomatopoeia sūrahs rank high on this axis and whether "
            "the Quran as a whole is elevated vs. Arabic controls."
        ),
        "preregistration": {
            "pos_letters": sorted(POS_LETTERS),
            "neg_letters": sorted(NEG_LETTERS),
            "ref_corpora": ref_corpora,
            "named_onomatopoeia_surahs": {
                str(k): v for k, v in NAMED_ONOMATOPOEIA.items()
            },
            "held_out_named_onomatopoeia_surahs": {
                str(k): v for k, v in NAMED_ONOMATOPOEIA_HELDOUT.items()
            },
            "note": (
                "POS/NEG letter sets were derived from exp03 Q4 on sūra 100; "
                "therefore the Q100 result is in-sample and excluded from the "
                "primary held-out t-test. See audit_note in named_vs_rest_t_test."
            ),
        },
        "reference_letter_frequencies": {
            c: round(f, 5) for c, f in sorted(
                ref_freq.items(), key=lambda kv: -kv[1]
            )[:20]
        },
        "O_index_by_corpus": O_by_corpus,
        "quran_vs_ctrl_summary": {
            "quran_mean": q_mean, "quran_std": q_std, "n_quran": int(len(O_quran)),
            "ctrl_mean": c_mean, "ctrl_std": c_std, "n_ctrl": int(len(O_ctrl)),
            "mean_diff": q_mean - c_mean,
        },
        "named_surah_rankings": named_results,
        "named_vs_rest_t_test": t_test,
    }

    with open(out / "exp04_onomatopoeia.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print(f"[{EXP}] Reference corpora: {ref_corpora}  (n_units = {len(O_ctrl)})")
    print(f"[{EXP}] Quran  O mean = {q_mean:+.4f}  std = {q_std:.4f}  n = {len(O_quran)}")
    print(f"[{EXP}] Ctrl   O mean = {c_mean:+.4f}  std = {c_std:.4f}  n = {len(O_ctrl)}")
    print(f"[{EXP}] Quran − Ctrl mean diff = {q_mean - c_mean:+.4f}")
    print(f"[{EXP}] Named-onomatopoeia surahs:")
    for num in sorted(named_nums_found, key=lambda n: -named_results[n]["O_index"]):
        r = named_results[num]
        print(f"  Q{num:3d} ({r['name']:<35s})  O={r['O_index']:+.4f}  "
              f"z={r['z_vs_ctrl']:+.2f}  rank={r['rank_in_quran']}/{len(O_quran)}  "
              f"p_tail={r['p_tail_vs_ctrl']:.4f}")
    if t_test["in_sample_includes_Q100"]:
        r = t_test["in_sample_includes_Q100"]
        print(f"[{EXP}] In-sample (n={r['n_named']}, includes Q100 — CIRCULAR, reference only):")
        print(f"    t={r['t']:+.3f}  p={r['p_one_sided']:.4g}  "
              f"mean_named={r['mean_named']:+.4f}  mean_rest={r['mean_rest']:+.4f}")
    if t_test["held_out_Q100_excluded"]:
        r = t_test["held_out_Q100_excluded"]
        print(f"[{EXP}] HELD-OUT (n={r['n_named']}, Q100 excluded — PRIMARY TEST):")
        print(f"    t={r['t']:+.3f}  p={r['p_one_sided']:.4g}  "
              f"mean_named={r['mean_named']:+.4f}  mean_rest={r['mean_rest']:+.4f}")
    print(f"[{EXP}] wrote: {out}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
