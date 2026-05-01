"""exp88 - LC3-70 boundary figure (Fig. 7 of PAPER.md 4.35).

Zero new computation. Reads locked coefficients from exp70, (T, EL) coordinates
from the phase_06_phi_m checkpoint, and emits fig7 + CSV + SHA receipt.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
# The checkpoint pickle references src.* classes and experiments._lib provides
# the SHA-verified loader; make both importable before any pickle.load runs.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP70 = ROOT / "results" / "experiments" / "exp70_decision_boundary" / "exp70_decision_boundary.json"
CKPT = ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl"
OUT = Path(__file__).resolve().parent


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


FAMILY_COLORS = {
    "poetry_jahili": "#bbbbbb",
    "poetry_islami": "#888888",
    "poetry_abbasi": "#555555",
    "ksucca": "#aa77aa",
    "arabic_bible": "#e4a020",
    "hindawi": "#6ca0dc",
}


def main() -> None:
    # Lazy import so the sys.path insertion above is in effect.
    from experiments._lib import load_phase

    exp70 = json.loads(EXP70.read_text(encoding="utf-8"))
    eq = exp70["svm"]["equation_raw"]
    w_T = float(eq["w_T"])
    w_EL = float(eq["w_EL"])
    b = float(eq["b"])
    margin = float(exp70["svm"]["margin"])

    # Load the SHA-verified phase_06 checkpoint exactly as exp70 does.
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q_5D = np.asarray(state["X_QURAN"], dtype=float)
    X_C_5D = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    feats = state["FEATS"]
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))

    t_idx = feat_cols.index("T")
    el_idx = feat_cols.index("EL")

    # Build family label list for control rows in the same order as X_CTRL_POOL.
    # exp70 concatenates corpora in ARABIC_CTRL_POOL order, each filtered to Band-A.
    families: list[str] = []
    for cname in ctrl_pool:
        recs = [r for r in feats.get(cname, []) if band_lo <= r["n_verses"] <= band_hi]
        families.extend([cname] * len(recs))
    if len(families) != X_C_5D.shape[0]:
        raise RuntimeError(
            f"Family-label alignment failed: {len(families)} labels vs "
            f"{X_C_5D.shape[0]} control rows. Check BAND_A bounds / ARABIC_CTRL_POOL order."
        )
    families_arr = np.asarray(families)

    # (T, EL) columns.
    T_Q = X_Q_5D[:, t_idx]
    EL_Q = X_Q_5D[:, el_idx]
    T_C = X_C_5D[:, t_idx]
    EL_C = X_C_5D[:, el_idx]

    # Boundary and margin lines in the (T, EL) plane (T on x, EL on y).
    T_lo = min(T_C.min(), T_Q.min()) - 0.5
    T_hi = max(T_C.max(), T_Q.max()) + 0.5
    T_grid = np.linspace(T_lo, T_hi, 200)
    EL_boundary = (-b - w_T * T_grid) / w_EL
    EL_upper = (-b + margin - w_T * T_grid) / w_EL
    EL_lower = (-b - margin - w_T * T_grid) / w_EL

    # Scores.
    L_Q = w_T * T_Q + w_EL * EL_Q + b
    L_C = w_T * T_C + w_EL * EL_C + b
    n_q_side = int((L_Q > 0).sum())
    n_c_side = int((L_Q <= 0).sum())
    n_q_total = int(X_Q_5D.shape[0])

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for cname in ctrl_pool:
        mask = families_arr == cname
        if not np.any(mask):
            continue
        color = FAMILY_COLORS.get(cname, "#999999")
        leak_mask = mask & (L_C > 0)
        normal_mask = mask & ~(L_C > 0)
        ax.scatter(
            T_C[normal_mask], EL_C[normal_mask],
            s=8, alpha=0.4, c=color,
            label=f"{cname} (n={int(mask.sum())})",
        )
        if np.any(leak_mask):
            ax.scatter(
                T_C[leak_mask], EL_C[leak_mask],
                s=46, facecolor=color, edgecolor="black", linewidth=0.8, marker="D",
                label=f"{cname} leak ({int(leak_mask.sum())})",
            )
    ax.scatter(
        T_Q[L_Q > 0], EL_Q[L_Q > 0],
        c="red", s=36, marker="o", edgecolor="black", linewidth=0.6,
        label=f"Quran (Q-side, n={n_q_side})",
    )
    ax.scatter(
        T_Q[L_Q <= 0], EL_Q[L_Q <= 0],
        facecolor="none", edgecolor="red", s=36, marker="o", linewidth=1.4,
        label=f"Quran (C-side, n={n_c_side})",
    )
    ax.plot(T_grid, EL_boundary, "k-", lw=1.5, label="L = 0 (boundary)")
    ax.plot(T_grid, EL_upper, "k--", lw=0.8, alpha=0.6)
    ax.plot(T_grid, EL_lower, "k--", lw=0.8, alpha=0.6,
            label=f"+/-margin = {margin:.3f}")
    ax.set_xlabel("T (structural tension)")
    ax.set_ylabel("EL (end-letter rhyme rate)")
    ax.set_title(
        f"LC3-70: {w_T:+.4f}*T + {w_EL:+.4f}*EL + {b:+.4f} = 0   "
        f"(AUC = {exp70['svm']['auc']:.4f})"
    )
    ax.legend(loc="lower left", fontsize=6.5, framealpha=0.9, ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_lc3_70_pareto.png", dpi=150)
    plt.close(fig)

    # --- CSV dump ---
    with (OUT / "fig7_data.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "family", "T", "EL", "L"])
        for i in range(len(T_C)):
            writer.writerow(["ctrl", families[i],
                             f"{T_C[i]:.6f}", f"{EL_C[i]:.6f}", f"{L_C[i]:.6f}"])
        for i in range(len(T_Q)):
            writer.writerow(["quran", "quran",
                             f"{T_Q[i]:.6f}", f"{EL_Q[i]:.6f}", f"{L_Q[i]:.6f}"])

    # --- Per-family leak sanity ---
    per_family_leak = {}
    for cname in ctrl_pool:
        mask = families_arr == cname
        per_family_leak[cname] = {
            "n": int(mask.sum()),
            "leaks_into_quran": int(((L_C > 0) & mask).sum()),
        }

    # --- Receipt ---
    receipt = {
        "experiment": "exp88_lc3_70_u",
        "purpose": "Fig. 7 re-emission for PAPER.md 4.35",
        "no_new_computation": True,
        "inputs_sha256": {
            "exp70_decision_boundary.json": _sha(EXP70),
            "phase_06_phi_m.pkl": _sha(CKPT),
        },
        "outputs_sha256": {
            "fig7_lc3_70_pareto.png": _sha(OUT / "fig7_lc3_70_pareto.png"),
            "fig7_data.csv": _sha(OUT / "fig7_data.csv"),
        },
        "locked_constants_used": {
            "w_T": w_T, "w_EL": w_EL, "b": b, "margin": margin,
            "auc": exp70["svm"]["auc"],
            "accuracy": exp70["svm"]["accuracy"],
        },
        "classification_check": {
            "n_quran_total": n_q_total,
            "n_ctrl_total": int(X_C_5D.shape[0]),
            "quran_side": n_q_side,
            "ctrl_side_in_quran": n_c_side,
            "expected_quran_side": int(exp70["svm"]["quran_correct"]),
            "expected_quran_total": int(exp70["svm"]["quran_total"]),
        },
        "per_family_leak": per_family_leak,
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    print(f"[exp88] Fig. 7 + CSV + receipt written to {OUT}")
    print(f"[exp88] Quran-side={n_q_side}/{n_q_total} "
          f"(expected {int(exp70['svm']['quran_correct'])}/{int(exp70['svm']['quran_total'])})")
    print(f"[exp88] Per-family leak into Quran side:")
    for cname, d in per_family_leak.items():
        print(f"         {cname:20s} n={d['n']:4d}  leaks={d['leaks_into_quran']}")


if __name__ == "__main__":
    main()
