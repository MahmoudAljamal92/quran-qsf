"""
exp03_adiyat/run.py
===================
Ādiyāt (Sūra 100) deep-dive — *sandboxed*.

Hypothesis: the locked `Adiyat_blind = 4/7 = 0.571` is partly a power
problem (sūra 100 has 11 verses; Band-A starts at 15), not a failure of
the 5-D framework. This experiment isolates Ādiyāt and asks four tight
questions, using the locked μ_ctrl / S^-1 so answers are *comparable*
to the paper's Φ_M axis.

Questions
---------
Q1. Where does sūra 100 sit in 5-D? Mahalanobis rank among all 114 Quran
    surahs, and among the 46 out-of-band (< 15 verses) short surahs.
Q2. Does the *oath-opening* sub-class (sūrahs whose first content verse
    starts with و + noun) form a tight 5-D cluster, and is Ādiyāt an
    outlier within that sub-class?
Q3. Plosive-consonant density ("galloping-horse" phonetics). Is sūra 100
    elevated vs. the rest of the Quran AND vs. the Arabic control pool?
Q4. Letter-distribution χ² anomaly of sūra 100 vs. the whole-Quran
    letter profile.

Reads (through the integrity-checked loader):
  - phase_06_phi_m.pkl         (CORPORA, μ_ctrl, S_inv, X_CTRL_POOL)

Imports:
  - src.features               (canonical 5-D extractor; extends on-disk
                                CamelTools cache, which is NOT protected)

Writes ONLY under results/experiments/exp03_adiyat/:
  - exp03_adiyat.json          (all numbers)
  - fig_phi_m_rank.png
  - fig_oath_subclass.png
  - fig_plosive_density.png
  - self_check_<ts>.json

Does not touch the main notebook, ULTIMATE_REPORT.json, or any locked result.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # no GUI
import matplotlib.pyplot as plt
from scipy import stats

# Sandbox import path
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
from src import features as ft  # noqa: E402  (canonical 5-D extractor)

EXP = "exp03_adiyat"


# ---------------------------------------------------------------------------
# Arabic helpers (consonantal-rasm level, diacritic-stripped)
# ---------------------------------------------------------------------------
ARABIC_LETTERS = list(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"  # 28 consonants (plus ى will be folded)
    "ىء"
)

# "Galloping" onomatopoeia — stops + emphatic stops heavy in Ādiyāt.
# Linguistic note: al-Ādiyāt is a canonical example of mimetic phonology
# (Ibn al-Athīr 1224; Reynolds 2011). Plosive / stop letters:
PLOSIVES = set("بتدطضقكءطث")  # voiced + voiceless stops + emphatic + glottal
# Strict "gallop" subset often highlighted by classical commentators:
GALLOP = set("بتدطقك")


def _strip_d(s: str) -> str:
    return ft._strip_d(s)


def plosive_density(text: str, charset: set[str]) -> float:
    s = _strip_d(text)
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c in charset) / len(letters)


def letter_profile(text: str) -> Counter:
    s = _strip_d(text)
    return Counter(c for c in s if c.isalpha())


# ---------------------------------------------------------------------------
# Oath-opening detection (وَ + noun at verse 1)
# ---------------------------------------------------------------------------
# Canonical list of sūrahs opening with a و-oath, from classical tafsīr.
# Surah numbers 1-indexed. This list is fixed at the start of the experiment
# (no post-hoc selection).
OATH_SURAHS = {37, 51, 52, 53, 77, 79, 85, 86, 89, 91, 92, 93, 95, 100, 103}


def _surah_num(label: str) -> int | None:
    """Extract integer surah number from labels like 'Q:100'."""
    try:
        return int(str(label).split(":")[-1])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    S_inv = np.asarray(state["S_inv"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    X_CTRL = np.asarray(state["X_CTRL_POOL"], dtype=float)

    # ---------- Q1: position of sūra 100 in 5-D ----------
    quran_units = CORPORA["quran"]
    X_Q_all = []
    labels_all = []
    n_verses_all = []
    for u in quran_units:
        try:
            f = ft.features_5d(u.verses)
            X_Q_all.append(f)
            labels_all.append(u.label)
            n_verses_all.append(len(u.verses))
        except Exception as ex:
            print(f"[warn] features failed for {u.label}: {ex}")
    X_Q_all = np.asarray(X_Q_all, dtype=float)
    labels_all = np.asarray(labels_all)
    n_verses_all = np.asarray(n_verses_all)

    # Φ_M of every surah
    diff_all = X_Q_all - mu_ctrl[None, :]
    phi_m_all = np.sqrt(np.einsum("ij,jk,ik->i", diff_all, S_inv, diff_all))

    # Locate sūra 100
    idx_100 = int(np.where(labels_all == "Q:100")[0][0])
    phi100 = float(phi_m_all[idx_100])
    rank_all = int(np.sum(phi_m_all > phi100)) + 1  # 1 = biggest Φ_M
    rank_pct = float((rank_all - 1) / len(phi_m_all))  # 0 = top

    # Among short (< 15 verses) surahs only
    short_mask = n_verses_all < 15
    short_idx = np.where(short_mask)[0]
    short_phi = phi_m_all[short_idx]
    rank_short = int(np.sum(short_phi > phi100)) + 1
    n_short = int(short_mask.sum())

    # Locked baseline: phi_m of the Band-A control pool for comparison
    diff_C = X_CTRL - mu_ctrl[None, :]
    phi_m_ctrl = np.sqrt(np.einsum("ij,jk,ik->i", diff_C, S_inv, diff_C))

    q1 = {
        "surah_100_features": dict(zip(feat_cols, X_Q_all[idx_100].tolist())),
        "surah_100_phi_m": phi100,
        "surah_100_n_verses": int(n_verses_all[idx_100]),
        "rank_all_surahs": {"rank": rank_all, "n": int(len(phi_m_all)),
                            "top_fraction": rank_pct},
        "rank_short_surahs": {"rank": rank_short, "n": n_short},
        "quran_mean_phi_m": float(phi_m_all.mean()),
        "quran_median_phi_m": float(np.median(phi_m_all)),
        "control_pool_mean_phi_m": float(phi_m_ctrl.mean()),
        "control_pool_95pct_phi_m": float(np.quantile(phi_m_ctrl, 0.95)),
        "control_pool_max_phi_m": float(phi_m_ctrl.max()),
    }

    # ---------- Q2: oath-opening sub-class ----------
    surah_nums = np.array([_surah_num(l) or -1 for l in labels_all])
    oath_mask = np.isin(surah_nums, list(OATH_SURAHS))
    X_oath = X_Q_all[oath_mask]
    phi_oath = phi_m_all[oath_mask]
    labels_oath = labels_all[oath_mask]

    # Sub-class centroid + Mahalanobis distance of sūra 100 to THAT centroid.
    # AUDIT FIX 2026-04-19 (critical): use LEAVE-ONE-OUT so each member is
    # NOT part of the centroid / covariance it is measured against. The
    # previous non-LOO version biased every member's distance downward.
    if len(X_oath) >= 5:
        # Non-LOO reference values (kept for reproducibility of old table;
        # flagged as biased in the JSON output).
        mu_oath_full = X_oath.mean(axis=0)
        S_oath_full = np.cov(X_oath, rowvar=False, ddof=1) + 1e-6 * np.eye(5)

        # LEAVE-ONE-OUT Mahalanobis per member
        d_each_oath_loo = np.empty(len(X_oath))
        for i in range(len(X_oath)):
            others = np.delete(X_oath, i, axis=0)
            mu_i = others.mean(axis=0)
            S_i = np.cov(others, rowvar=False, ddof=1) + 1e-6 * np.eye(5)
            S_i_inv = np.linalg.pinv(S_i)
            diff_i = X_oath[i] - mu_i
            d_each_oath_loo[i] = math.sqrt(
                max(float(diff_i @ S_i_inv @ diff_i), 0.0)
            )

        # Ādiyāt-specific LOO distance
        i100 = labels_oath.tolist().index("Q:100") if "Q:100" in labels_oath.tolist() else None
        d_100_oath = float(d_each_oath_loo[i100]) if i100 is not None else None
        rank_100_within_oath = (
            int(np.sum(d_each_oath_loo > d_100_oath)) + 1 if i100 is not None else None
        )

        # Non-LOO version (biased, for cross-check only)
        S_oath_inv_full = np.linalg.pinv(S_oath_full)
        d_each_oath_biased = np.sqrt(np.einsum(
            "ij,jk,ik->i",
            X_oath - mu_oath_full[None, :],
            S_oath_inv_full,
            X_oath - mu_oath_full[None, :],
        ))

        # For downstream plotting we use the LOO values
        d_each_oath = d_each_oath_loo
        mu_oath = mu_oath_full
    else:
        mu_oath = None
        d_100_oath = None
        rank_100_within_oath = None
        d_each_oath = None
        d_each_oath_loo = None
        d_each_oath_biased = None

    q2 = {
        "oath_surah_numbers": sorted(OATH_SURAHS),
        "oath_labels_found": labels_oath.tolist(),
        "n_oath_surahs_found": int(len(X_oath)),
        "oath_centroid_5d": None if mu_oath is None else dict(zip(feat_cols, mu_oath.tolist())),
        "d_surah100_to_oath_centroid_local_maha_LOO": d_100_oath,
        "rank_surah100_within_oath_subclass_LOO": rank_100_within_oath,
        "oath_local_maha_distances_LOO": {
            lbl: float(d) for lbl, d in zip(
                labels_oath.tolist(),
                (d_each_oath_loo.tolist() if d_each_oath_loo is not None else []),
            )
        },
        "oath_local_maha_distances_biased_non_LOO": {
            lbl: float(d) for lbl, d in zip(
                labels_oath.tolist(),
                (d_each_oath_biased.tolist() if d_each_oath_biased is not None else []),
            )
        },
        "audit_note": (
            "2026-04-19 fix: distances are computed LEAVE-ONE-OUT (the "
            "target surah is excluded from μ and Σ estimation). The previous "
            "non-LOO numbers are retained under 'oath_local_maha_distances_"
            "biased_non_LOO' for transparency; do not cite them as primary."
        ),
    }

    # ---------- Q3: plosive / galloping density ----------
    adi_text = " ".join(quran_units[idx_100].verses)
    adi_plo = plosive_density(adi_text, PLOSIVES)
    adi_gal = plosive_density(adi_text, GALLOP)

    # Per-Quran-surah densities
    quran_plo = np.array([
        plosive_density(" ".join(u.verses), PLOSIVES) for u in quran_units
    ])
    quran_gal = np.array([
        plosive_density(" ".join(u.verses), GALLOP) for u in quran_units
    ])

    # Arabic control pool densities (exclude hadith_bukhari, quarantined
    # per preregistration.json honest_adjustments_2026_04_18)
    ctrl_corpora = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                    "ksucca", "arabic_bible", "hindawi"]
    ctrl_plo_list = []
    ctrl_gal_list = []
    ctrl_src = []
    for c in ctrl_corpora:
        for u in CORPORA.get(c, []):
            txt = " ".join(u.verses)
            if not txt.strip():
                continue
            ctrl_plo_list.append(plosive_density(txt, PLOSIVES))
            ctrl_gal_list.append(plosive_density(txt, GALLOP))
            ctrl_src.append(c)
    ctrl_plo = np.array(ctrl_plo_list)
    ctrl_gal = np.array(ctrl_gal_list)

    # Rank of sūra 100 on galloping density among all Quran surahs
    rank_adi_gal_quran = int(np.sum(quran_gal > adi_gal)) + 1
    # Tail probability from controls (one-sided >= adi_gal)
    p_tail_ctrl_gal = float((np.sum(ctrl_gal >= adi_gal) + 1) / (len(ctrl_gal) + 1))
    # z-score of Ādiyāt against control mean/std
    z_adi_ctrl_gal = float((adi_gal - ctrl_gal.mean()) / max(ctrl_gal.std(ddof=1), 1e-9))

    q3 = {
        "plosive_set": "".join(sorted(PLOSIVES)),
        "gallop_set": "".join(sorted(GALLOP)),
        "surah_100_plosive_density": adi_plo,
        "surah_100_gallop_density": adi_gal,
        "quran_plosive_density_mean": float(quran_plo.mean()),
        "quran_plosive_density_std": float(quran_plo.std(ddof=1)),
        "quran_gallop_density_mean": float(quran_gal.mean()),
        "quran_gallop_density_std": float(quran_gal.std(ddof=1)),
        "surah_100_gallop_rank_in_quran": rank_adi_gal_quran,
        "n_quran_surahs": int(len(quran_gal)),
        "control_gallop_mean": float(ctrl_gal.mean()),
        "control_gallop_std": float(ctrl_gal.std(ddof=1)),
        "surah_100_z_vs_ctrl_gallop": z_adi_ctrl_gal,
        "p_tail_surah_100_vs_ctrl_gallop": p_tail_ctrl_gal,
        "n_ctrl_units": int(len(ctrl_gal)),
    }

    # ---------- Q4: letter-distribution χ² anomaly ----------
    # Expected = Quran-wide letter distribution (excluding sūra 100 itself)
    not_100 = [u for u in quran_units if _surah_num(u.label) != 100]
    ref_counter = Counter()
    for u in not_100:
        ref_counter.update(letter_profile(" ".join(u.verses)))
    adi_counter = letter_profile(adi_text)

    letters_common = sorted(set(ref_counter) | set(adi_counter))
    obs = np.array([adi_counter[l] for l in letters_common], dtype=float)
    ref = np.array([ref_counter[l] for l in letters_common], dtype=float)
    # Normalise ref distribution to observed total
    ref_p = ref / ref.sum() if ref.sum() > 0 else ref
    expected = ref_p * obs.sum()
    mask = expected > 5  # chi2 validity
    chi2 = float(((obs[mask] - expected[mask]) ** 2 / expected[mask]).sum())
    df_chi2 = int(mask.sum() - 1)
    p_chi2 = float(stats.chi2.sf(chi2, df_chi2)) if df_chi2 > 0 else float("nan")

    # Per-letter deviation, signed
    ratio = np.where(expected > 0, obs / np.maximum(expected, 1e-9), 0.0)
    deviations = {
        l: {"obs": int(o), "expected": float(e), "obs_over_exp": float(r)}
        for l, o, e, r in zip(letters_common, obs, expected, ratio)
        if e > 5  # only letters with enough data to interpret
    }

    q4 = {
        "chi2": chi2,
        "df": df_chi2,
        "p_chi2": p_chi2,
        "letters_used": [l for l, d in deviations.items()],
        "top_overrepresented": sorted(
            deviations.items(), key=lambda kv: -kv[1]["obs_over_exp"]
        )[:5],
        "top_underrepresented": sorted(
            deviations.items(), key=lambda kv: kv[1]["obs_over_exp"]
        )[:5],
    }

    # ---------- Plots ----------
    # Fig A: Φ_M rank of all 114 surahs, sūra 100 highlighted
    fig, ax = plt.subplots(figsize=(8, 4))
    order = np.argsort(phi_m_all)
    ax.plot(np.arange(len(order)), phi_m_all[order], lw=0.8, color="#444")
    pos = int(np.where(order == idx_100)[0][0])
    ax.scatter([pos], [phi_m_all[idx_100]], color="crimson", zorder=5, s=60,
               label=f"Sūra 100 (Φ_M = {phi100:.2f})")
    ax.axhline(np.quantile(phi_m_ctrl, 0.95), color="navy", ls="--", lw=0.8,
               label=f"Ctrl-pool 95th pct = {np.quantile(phi_m_ctrl, 0.95):.2f}")
    ax.set_xlabel("Quran surah index (sorted by Φ_M ascending)")
    ax.set_ylabel("Φ_M (Mahalanobis to Arabic-ctrl centroid)")
    ax.set_title("Sūra 100 in the Quran Φ_M distribution")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_phi_m_rank.png", dpi=130)
    plt.close(fig)

    # Fig B: oath-opening sub-class positions
    if mu_oath is not None:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        xs = [d for d in (d_each_oath.tolist() if d_each_oath is not None else [])]
        ax.bar(range(len(xs)), xs, color="#2b8cbe")
        lbls_short = [l.replace("Q:", "Q") for l in labels_oath]
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(lbls_short, rotation=45, fontsize=8)
        # highlight 100
        idx_100_oath = labels_oath.tolist().index("Q:100")
        ax.bar([idx_100_oath], [xs[idx_100_oath]], color="crimson")
        ax.set_ylabel("Local Mahalanobis to oath-subclass centroid (LOO)")
        ax.set_title(
            f"Oath-opening sūrahs (n={len(xs)}) — LEAVE-ONE-OUT: "
            f"Ādiyāt = {xs[idx_100_oath]:.2f}, rank {rank_100_within_oath}/{len(xs)}"
        )
        fig.tight_layout()
        fig.savefig(out / "fig_oath_subclass.png", dpi=130)
        plt.close(fig)

    # Fig C: plosive (gallop) density histogram
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(ctrl_gal, bins=40, alpha=0.55, label=f"Arabic controls (n={len(ctrl_gal)})",
            color="#999")
    ax.hist(quran_gal, bins=30, alpha=0.65, label=f"Quran surahs (n={len(quran_gal)})",
            color="#2b8cbe")
    ax.axvline(adi_gal, color="crimson", lw=2,
               label=f"Sūra 100 = {adi_gal:.3f}  (z={z_adi_ctrl_gal:+.2f})")
    ax.set_xlabel("Gallop-plosive density (fraction of letters in {" +
                  "".join(sorted(GALLOP)) + "})")
    ax.set_ylabel("count")
    ax.set_title("Ādiyāt galloping-consonant density vs. baseline")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_plosive_density.png", dpi=130)
    plt.close(fig)

    # ---------- Final JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            "Sūra 100 (Ādiyāt) deep-dive. Uses locked μ_ctrl and S_inv from "
            "phase_06_phi_m; computes 5-D features fresh via src.features "
            "(canonical CamelTools-backed extractor). "
            "Sandbox: no writes outside results/experiments/exp03_adiyat/."
        ),
        "Q1_position_in_5D": q1,
        "Q2_oath_subclass": q2,
        "Q3_plosive_density": q3,
        "Q4_letter_chi2": q4,
        "caveats": [
            "Sūra 100 has 11 verses, below Band-A lower cutoff of 15.",
            "Oath-opening surah list fixed from classical tafsīr, not data-driven.",
            "Plosive set 'gallop' is a fixed phonetic hypothesis; see notes.md.",
            "χ² uses only letters with expected count > 5 (Cochran's rule).",
        ],
    }
    with open(out / "exp03_adiyat.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print(f"[{EXP}] === Q1: position in 5-D ===")
    print(f"  Sūra 100 Φ_M = {phi100:.3f}   "
          f"rank among 114 Quran surahs: {rank_all}/{len(phi_m_all)}   "
          f"(top {rank_pct*100:.1f}%)")
    print(f"  Ctrl-pool Φ_M: mean {q1['control_pool_mean_phi_m']:.2f}, "
          f"95th pct {q1['control_pool_95pct_phi_m']:.2f}, "
          f"max {q1['control_pool_max_phi_m']:.2f}")
    print(f"[{EXP}] === Q2: oath sub-class ===")
    print(f"  Oath surahs found: {len(labels_oath)} / 15 expected")
    print(f"  Ādiyāt local-Maha to oath centroid: {d_100_oath}")
    print(f"  Rank within oath sub-class: {rank_100_within_oath}/{len(labels_oath)}")
    print(f"[{EXP}] === Q3: galloping plosive density ===")
    print(f"  Ādiyāt gallop density = {adi_gal:.4f}")
    print(f"  Quran mean  = {quran_gal.mean():.4f}   Quran rank: "
          f"{rank_adi_gal_quran}/{len(quran_gal)}")
    print(f"  Ctrl mean   = {ctrl_gal.mean():.4f}   z = {z_adi_ctrl_gal:+.2f}   "
          f"p_tail = {p_tail_ctrl_gal:.4f}")
    print(f"[{EXP}] === Q4: χ² letter anomaly ===")
    print(f"  χ² = {chi2:.2f}   df = {df_chi2}   p = {p_chi2:.4g}")
    print(f"[{EXP}] wrote: {out / 'exp03_adiyat.json'}")
    print(f"[{EXP}] wrote: 3 figures under {out}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
