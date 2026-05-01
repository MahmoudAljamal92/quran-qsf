"""exp169_phoneme_class_markov — frozen-PREREG Markov-1 transition test
on 8-class Arabic phoneme sequence from Hafs vocalised Quran.

Operating principle: Quran is the reference. No external corpus comparison.
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ────────────────────────────────────────────────────────────────────
# 8-class phoneme scheme (frozen)
# ────────────────────────────────────────────────────────────────────
SHORT_VOWELS = {"\u064E": 0, "\u0650": 0, "\u064F": 0}
TANWEEN = {"\u064B": 1, "\u064C": 1, "\u064D": 1}
MADD_DIACRITICS = {
    "\u0653": 2, "\u0670": 2, "\u0656": 2, "\u0655": 2, "\u0657": 2, "\u065E": 2,
}
MADD_LETTERS = set("\u0627\u0671")  # ا and alef-wasla as madd/long-vowel
NASAL_LETTERS = set("\u0645\u0646")
LIQUID_LETTERS = set("\u0644\u0631")
GLIDE_LETTERS = set("\u0648\u064A")
EMPHATIC_LETTERS = set("\u0635\u0636\u0637\u0638\u0642\u0639\u062D\u062E\u063A"
                       "\u0621\u0623\u0625\u0622\u0624\u0626\u0647")
OBSTRUENT_LETTERS = set("\u0628\u062A\u062B\u062C\u062F\u0630\u0632\u0633"
                        "\u0634\u0641\u0643\u0629\u0649")

SHADDA = "\u0651"
SUKUN = "\u0652"

DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F)]
DROP_SINGLES = {0x00A0, 0x0640}


def is_dropped(ch: str) -> bool:
    cp = ord(ch)
    if cp < 128:
        return True
    if cp in DROP_SINGLES:
        return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def char_to_class(ch: str) -> int | None:
    if ch in SHORT_VOWELS:
        return 0
    if ch in TANWEEN:
        return 1
    if ch in MADD_DIACRITICS or ch in MADD_LETTERS:
        return 2
    if ch in NASAL_LETTERS:
        return 3
    if ch in LIQUID_LETTERS:
        return 4
    if ch in GLIDE_LETTERS:
        return 5
    if ch in EMPHATIC_LETTERS:
        return 6
    if ch in OBSTRUENT_LETTERS:
        return 7
    return None


def text_to_class_seq(text: str) -> np.ndarray:
    out: list[int] = []
    last_cls: int | None = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r"):
            continue
        if is_dropped(ch):
            continue
        if ch == SUKUN:
            continue
        if ch == SHADDA:
            if last_cls is not None:
                out.append(last_cls)
            continue
        cls = char_to_class(ch)
        if cls is None:
            continue
        out.append(cls)
        last_cls = cls
    return np.asarray(out, dtype=np.int8)


# ────────────────────────────────────────────────────────────────────
# Markov stats
# ────────────────────────────────────────────────────────────────────
K = 8


def transition_matrix(seq: np.ndarray, k: int = K, alpha: float = 1.0) -> np.ndarray:
    """Return row-normalised transition matrix with Laplace smoothing α."""
    counts = np.full((k, k), alpha, dtype=float)
    a = seq[:-1]
    b = seq[1:]
    np.add.at(counts, (a, b), 1.0)
    return counts / counts.sum(axis=1, keepdims=True)


def stationary(P: np.ndarray) -> np.ndarray:
    """Stationary distribution of P (left-eigenvector of eigenvalue 1)."""
    w, V = np.linalg.eig(P.T)
    i = int(np.argmin(np.abs(w - 1)))
    pi = np.real(V[:, i])
    pi = np.abs(pi)
    pi = pi / pi.sum()
    return pi


def entropy_H0(seq: np.ndarray, k: int = K) -> float:
    counts = np.bincount(seq, minlength=k).astype(float)
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def conditional_entropy_H1(P: np.ndarray, pi: np.ndarray) -> float:
    H = 0.0
    for i in range(P.shape[0]):
        row = P[i]
        m = row > 0
        H -= pi[i] * (row[m] * np.log2(row[m])).sum()
    return float(H)


def max_off_diag(P: np.ndarray) -> float:
    Q = P.copy()
    np.fill_diagonal(Q, 0.0)
    return float(Q.max())


def spectral_gap(P: np.ndarray) -> float:
    w = np.linalg.eigvals(P)
    mags = np.sort(np.abs(w))[::-1]
    return float(1.0 - mags[1])


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"


def main():
    out_dir = ROOT / "results" / "experiments" / "exp169_phoneme_class_markov"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp169] Loading vocalised Quran ...", flush=True)
    text = QURAN_VOCAL.read_text(encoding="utf-8")
    S = text_to_class_seq(text)
    N = len(S)
    counts = np.bincount(S, minlength=K).tolist()
    print(f"[exp169] N={N}  class counts: {counts}", flush=True)

    print("\n[exp169] === observed Markov-1 stats ===", flush=True)
    P_obs = transition_matrix(S)
    pi_obs = stationary(P_obs)
    H0_obs = entropy_H0(S)
    H1_obs = conditional_entropy_H1(P_obs, pi_obs)
    I_obs = H0_obs - H1_obs
    pmax_obs = max_off_diag(P_obs)
    gap_obs = spectral_gap(P_obs)
    print(f"  H_0 = {H0_obs:.4f} bits", flush=True)
    print(f"  H_1 = {H1_obs:.4f} bits", flush=True)
    print(f"  I = H_0 - H_1 = {I_obs:.4f} bits", flush=True)
    print(f"  max off-diagonal P = {pmax_obs:.4f}", flush=True)
    print(f"  spectral gap (1 - |λ₂|) = {gap_obs:.4f}", flush=True)
    print(f"  π = {np.round(pi_obs, 4).tolist()}", flush=True)

    print("\n[exp169] === shuffle null (n=2000) ===", flush=True)
    rng = np.random.default_rng(20260501)
    Sc = S.copy()
    H1_n = np.empty(2000); I_n = np.empty(2000); pmax_n = np.empty(2000); gap_n = np.empty(2000)
    t0 = time.time()
    for i in range(2000):
        rng.shuffle(Sc)
        P_n = transition_matrix(Sc)
        pi_n = stationary(P_n)
        H1_n[i] = conditional_entropy_H1(P_n, pi_n)
        I_n[i] = H0_obs - H1_n[i]
        pmax_n[i] = max_off_diag(P_n)
        gap_n[i] = spectral_gap(P_n)
        if (i + 1) % 200 == 0:
            print(f"    [shuffle] {i+1}/2000  elapsed {time.time()-t0:.1f}s", flush=True)

    p_H1 = float((1 + (H1_n <= H1_obs).sum()) / (1 + len(H1_n)))      # one-tailed lower
    p_I = float((1 + (I_n >= I_obs).sum()) / (1 + len(I_n)))           # one-tailed upper
    p_pmax = float((1 + (pmax_n >= pmax_obs).sum()) / (1 + len(pmax_n)))  # one-tailed upper
    p_gap = float((1 + (gap_n <= gap_obs).sum()) / (1 + len(gap_n)))   # one-tailed lower

    z_H1 = (H1_obs - H1_n.mean()) / (H1_n.std() + 1e-30)
    z_I = (I_obs - I_n.mean()) / (I_n.std() + 1e-30)
    z_pmax = (pmax_obs - pmax_n.mean()) / (pmax_n.std() + 1e-30)
    z_gap = (gap_obs - gap_n.mean()) / (gap_n.std() + 1e-30)

    print(f"\n[exp169] ── shuffle null summary ──", flush=True)
    print(f"  T1 H_1 : obs={H1_obs:.4f}  null=({H1_n.mean():.4f}±{H1_n.std():.4f})  z={z_H1:+.2f}  p={p_H1:.4g}", flush=True)
    print(f"  T2 I   : obs={I_obs:.4f}  null=({I_n.mean():.4f}±{I_n.std():.4f})  z={z_I:+.2f}  p={p_I:.4g}", flush=True)
    print(f"  T3 P_max:obs={pmax_obs:.4f}  null=({pmax_n.mean():.4f}±{pmax_n.std():.4f})  z={z_pmax:+.2f}  p={p_pmax:.4g}", flush=True)
    print(f"  T4 gap : obs={gap_obs:.4f}  null=({gap_n.mean():.4f}±{gap_n.std():.4f})  z={z_gap:+.2f}  p={p_gap:.4g}", flush=True)

    alpha = 0.0125
    pH1 = p_H1 < alpha; pI = p_I < alpha; pPm = p_pmax < alpha; pG = p_gap < alpha
    n_pass = sum([pH1, pI, pPm, pG])
    if n_pass >= 3 and pH1:
        verdict = "PASS_MARKOV_STRUCTURE_QURAN_REFERENCE"
    elif n_pass >= 1:
        verdict = f"PASS_PARTIAL_{n_pass}of4"
    else:
        verdict = "FAIL"

    print(f"\n[exp169] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp169] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp169] ║ H_0 = {H0_obs:.4f}   H_1 = {H1_obs:.4f}   I = {I_obs:.4f} bits", flush=True)
    print(f"[exp169] ║ P_max = {pmax_obs:.4f}   spectral gap = {gap_obs:.4f}", flush=True)
    print(f"[exp169] ║ n_pass = {n_pass}/4", flush=True)
    print(f"[exp169] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp169_phoneme_class_markov",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "audit": {"N": int(N), "class_counts": counts},
        "alpha_per_test": alpha,
        "stats": {
            "H_0_bits": H0_obs,
            "H_1_bits": H1_obs,
            "I_bits": I_obs,
            "P_max_off_diag": pmax_obs,
            "spectral_gap": gap_obs,
            "stationary_pi": pi_obs.tolist(),
            "P_matrix": P_obs.tolist(),
        },
        "shuffle_null": {
            "n_perm": 2000,
            "T1_H1": {"null_mean": float(H1_n.mean()), "null_std": float(H1_n.std()), "z": float(z_H1), "p": p_H1, "pass": bool(pH1)},
            "T2_I": {"null_mean": float(I_n.mean()), "null_std": float(I_n.std()), "z": float(z_I), "p": p_I, "pass": bool(pI)},
            "T3_Pmax": {"null_mean": float(pmax_n.mean()), "null_std": float(pmax_n.std()), "z": float(z_pmax), "p": p_pmax, "pass": bool(pPm)},
            "T4_gap": {"null_mean": float(gap_n.mean()), "null_std": float(gap_n.std()), "z": float(z_gap), "p": p_gap, "pass": bool(pG)},
        },
        "n_pass": int(n_pass),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(P_obs, cmap="viridis", aspect="auto")
        labels = ["short-V", "tanween", "madd", "nasal", "liquid", "glide", "emphatic", "obstruent"]
        ax.set_xticks(range(K)); ax.set_xticklabels(labels, rotation=45)
        ax.set_yticks(range(K)); ax.set_yticklabels(labels)
        for i in range(K):
            for j in range(K):
                ax.text(j, i, f"{P_obs[i, j]:.2f}", ha="center", va="center", color="w", fontsize=7)
        plt.colorbar(im, ax=ax)
        ax.set_title(f"exp169 P(class_t | class_{{t-1}})\nH_1={H1_obs:.3f}b  I={I_obs:.3f}b  gap={gap_obs:.3f}")
        fig.tight_layout(); fig.savefig(out_dir / "fig_P.png", dpi=120); plt.close(fig)

        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        for ax, (label, obs, null) in zip(
            axes.flat,
            [("H_1", H1_obs, H1_n), ("I", I_obs, I_n), ("P_max", pmax_obs, pmax_n), ("spectral gap", gap_obs, gap_n)],
        ):
            ax.hist(null, bins=40, color="#888", alpha=0.7, density=True, label="null")
            ax.axvline(obs, color="r", linewidth=2, label=f"obs {obs:.4f}")
            ax.set_title(label); ax.legend()
        fig.suptitle(f"exp169 — verdict {verdict}")
        fig.tight_layout(); fig.savefig(out_dir / "fig_nulls.png", dpi=120); plt.close(fig)
        print(f"[exp169] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp169] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
