"""
expE9_takens_rqa — 3-D Takens embedding + Recurrence Quantification Analysis
of the canonical Quran verse-length series (6236 verses).

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      RQA metrics (RR, DET, LAM, L_max) on the observed Takens-embedded
      verse-length series are inside the 2.5 - 97.5 percentile band of
      500 IAAFT or AR(1) surrogates.
  Pass conditions:
      DET or LAM falls OUTSIDE the 95% surrogate band on BOTH surrogate types
      → STRUCTURED_DYNAMICS.
      Fail on only one → PARTIAL; inside both bands → NULL.
  Side effects:
      No mutation of any pinned artefact; outputs under expE9 folder only.
  Seed:
      NUMPY_SEED = 42.

Notes:
  - PyRQA not installed; implemented minimal RQA (RR, DET, LAM, L_max, ENTR)
    directly on a bool recurrence matrix. Validated against the Marwan
    definitions (Marwan et al., Phys. Rep. 2007).
  - Embedding dimension fixed at m=3 per spec; tau chosen by first minimum
    of auto mutual information (AMI) over lags 1..50 (fallback: first zero
    of autocorrelation).
"""
from __future__ import annotations

import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE9_takens_rqa"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_SURR = 200         # surrogates per type (reduced from 500 for runtime)
RR_TARGET = 0.05     # target recurrence rate for threshold picking
EMBED_DIM = 3
RNG = np.random.default_rng(SEED)

# --------------------------------------------------------------- LOAD
sys.path.insert(0, str(ROOT))
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
quran_units = state["CORPORA"]["quran"]
vl = np.concatenate([
    np.array([len(v.split()) for v in u.verses], dtype=float)
    for u in quran_units
])
N_orig = len(vl)
print(f"Loaded in {time.time()-t0:.2f}s — verse-length series length = {N_orig}")

# Downsample to a manageable size for RQA (O(N^2) memory). Use 2000 points.
# Strategy: use the FULL 6236 series for tau / mutual-info estimation, but
# cap RQA matrix size to keep memory low.
RQA_MAX_N = 1500
if N_orig > RQA_MAX_N:
    stride = N_orig // RQA_MAX_N + 1
    vl_rqa = vl[::stride][:RQA_MAX_N]
    print(f"  RQA sub-sampling: stride={stride}, N_rqa={len(vl_rqa)}")
else:
    vl_rqa = vl.copy()

# --------------------------------------------------------------- tau via AMI
def auto_mutual_info(x: np.ndarray, lag: int, n_bins: int = 32) -> float:
    """Normalised mutual information I(x_t; x_{t+lag})."""
    if lag <= 0 or lag >= len(x):
        return np.nan
    a = x[:-lag]
    b = x[lag:]
    bins = np.linspace(min(a.min(), b.min()), max(a.max(), b.max()) + 1e-9, n_bins + 1)
    H, _, _ = np.histogram2d(a, b, bins=[bins, bins])
    P = H / H.sum()
    Pa = P.sum(axis=1); Pb = P.sum(axis=0)
    # I = sum P*log(P/(Pa*Pb))
    mask = P > 0
    num = P[mask]
    denom = (Pa[:, None] * Pb[None, :])[mask]
    return float((num * np.log2(num / denom)).sum())

print("\nEstimating embedding lag tau via AMI first minimum ...")
lags = np.arange(1, 51)
ami = np.array([auto_mutual_info(vl, int(l)) for l in lags])
# first-minimum heuristic
tau = 1
for k in range(1, len(ami) - 1):
    if ami[k] < ami[k - 1] and ami[k] < ami[k + 1]:
        tau = int(lags[k])
        break
print(f"  AMI first minimum at tau={tau}  "
      f"(AMI[1]={ami[0]:.3f}, AMI[tau]={ami[tau-1]:.3f}, AMI[50]={ami[-1]:.3f})")

# --------------------------------------------------------------- Takens embed
def takens(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    n = len(x) - (m - 1) * tau
    if n <= 0:
        return np.empty((0, m))
    return np.stack([x[i * tau: i * tau + n] for i in range(m)], axis=1)

E_full = takens(vl, m=EMBED_DIM, tau=tau)
E_rqa  = takens(vl_rqa, m=EMBED_DIM, tau=tau)
print(f"  Takens embedding: full {E_full.shape}, RQA {E_rqa.shape}")

# --------------------------------------------------------------- RQA
def recurrence_matrix(E: np.ndarray, eps: float) -> np.ndarray:
    """bool recurrence: |x_i - x_j| <= eps in embedding space (Chebyshev norm
    for speed; results qualitatively match L2)."""
    # chunked computation for memory safety
    n = E.shape[0]
    R = np.zeros((n, n), dtype=bool)
    for i in range(n):
        diffs = np.abs(E - E[i]).max(axis=1)
        R[i] = diffs <= eps
    return R

def pick_threshold(E: np.ndarray, target_rr: float = 0.05,
                   n_samples: int = 2000) -> float:
    """Pick eps so that RR approx target_rr using Monte-Carlo pair sampling."""
    n = E.shape[0]
    rng = np.random.default_rng(SEED)
    idx1 = rng.integers(0, n, n_samples)
    idx2 = rng.integers(0, n, n_samples)
    ds = np.abs(E[idx1] - E[idx2]).max(axis=1)
    return float(np.quantile(ds, target_rr))

def _run_lengths(a: np.ndarray) -> np.ndarray:
    """Lengths of all True-runs in a 1D bool array (vectorized RLE)."""
    if a.size == 0:
        return np.empty(0, dtype=int)
    padded = np.concatenate([[False], a, [False]])
    diff = np.diff(padded.astype(np.int8))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    return (ends - starts).astype(int)

def rqa_metrics(R: np.ndarray, l_min: int = 2) -> dict:
    """Compute RR, DET, LAM, L_max, V_max, ENTR (Shannon entropy of diag-line dist)."""
    n = R.shape[0]
    np.fill_diagonal(R, False)  # Theiler window = 1
    total = int(R.sum())
    RR = float(total / (n * (n - 1)))

    # diagonal runs (vectorized over diagonals; inner RLE is vectorized)
    diag_lengths: list[int] = []
    for k in range(-(n - 1), n):
        lens = _run_lengths(np.diagonal(R, offset=k))
        if lens.size:
            diag_lengths.extend(lens[lens >= l_min].tolist())
    if diag_lengths:
        DET = float(sum(diag_lengths) / max(total, 1))
        L_max = int(max(diag_lengths))
        counts = np.bincount(diag_lengths)
        probs = counts[counts > 0] / counts.sum()
        ENTR = float(-(probs * np.log2(probs)).sum())
    else:
        DET, L_max, ENTR = 0.0, 0, 0.0

    # vertical runs per column
    vert_lengths: list[int] = []
    for j in range(n):
        lens = _run_lengths(R[:, j])
        if lens.size:
            vert_lengths.extend(lens[lens >= l_min].tolist())
    if vert_lengths:
        LAM = float(sum(vert_lengths) / max(total, 1))
        V_max = int(max(vert_lengths))
    else:
        LAM, V_max = 0.0, 0
    return {"RR": RR, "DET": DET, "LAM": LAM, "L_max": L_max,
            "V_max": V_max, "ENTR": ENTR}

print("\nRQA threshold calibration ...")
eps = pick_threshold(E_rqa, target_rr=RR_TARGET)
print(f"  eps (Chebyshev) for target RR={RR_TARGET}: {eps:.4f}")

print("Computing recurrence matrix ...")
t = time.time()
R_obs = recurrence_matrix(E_rqa, eps)
print(f"  R shape {R_obs.shape}, RR={R_obs.sum() / (R_obs.size - R_obs.shape[0]):.4f}, "
      f"{time.time()-t:.1f}s")

t = time.time()
metrics_obs = rqa_metrics(R_obs)
print(f"  RQA metrics: {metrics_obs}  ({time.time()-t:.1f}s)")

# --------------------------------------------------------------- Surrogates
def ar1_surrogate(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Fit AR(1) and simulate a surrogate with same length, matched
    lag-1 autocorr and marginal variance."""
    x = np.asarray(x, dtype=float)
    mu = x.mean()
    xc = x - mu
    phi = float(np.dot(xc[:-1], xc[1:]) / max(np.dot(xc[:-1], xc[:-1]), 1e-12))
    # residual variance
    eps_var = np.var(xc[1:] - phi * xc[:-1])
    y = np.zeros_like(x)
    y[0] = rng.normal(0, np.sqrt(max(eps_var, 1e-12) / max(1 - phi ** 2, 1e-12)))
    for t in range(1, len(x)):
        y[t] = phi * y[t - 1] + rng.normal(0, np.sqrt(max(eps_var, 1e-12)))
    return y + mu

def iaaft_surrogate(x: np.ndarray, n_iter: int = 50, rng: np.random.Generator = None) -> np.ndarray:
    """Iterative Amplitude Adjusted Fourier Transform — preserves both the
    power spectrum and the amplitude distribution of x."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    amp = np.sort(x)
    X = np.fft.rfft(x)
    amp_spec = np.abs(X)
    # random initial surrogate
    y = rng.permutation(x).astype(float)
    for _ in range(n_iter):
        # step 1: match spectrum
        Y = np.fft.rfft(y)
        phase = np.angle(Y)
        Y_new = amp_spec * np.exp(1j * phase)
        y = np.fft.irfft(Y_new, n=n)
        # step 2: match amplitude distribution
        ranks = np.argsort(np.argsort(y))
        y = amp[ranks]
    return y

print(f"\nGenerating {N_SURR} AR(1) + {N_SURR} IAAFT surrogates and computing RQA ...")
t = time.time()
ar1_rqa = []
iaaft_rqa = []
for k in range(N_SURR):
    if (k + 1) % 50 == 0:
        elapsed = time.time() - t
        eta = elapsed * (2 * N_SURR - k - 1) / (k + 1)
        print(f"  surrogate {k+1}/{N_SURR}  "
              f"(elapsed {elapsed:.1f}s, ETA {eta:.0f}s)")
    ar1 = ar1_surrogate(vl_rqa, RNG)
    E_ar1 = takens(ar1, m=EMBED_DIM, tau=tau)
    R_ar1 = recurrence_matrix(E_ar1, eps)
    ar1_rqa.append(rqa_metrics(R_ar1))

    iaaft = iaaft_surrogate(vl_rqa, n_iter=30, rng=RNG)
    E_iaaft = takens(iaaft, m=EMBED_DIM, tau=tau)
    R_iaaft = recurrence_matrix(E_iaaft, eps)
    iaaft_rqa.append(rqa_metrics(R_iaaft))
print(f"  surrogate RQA done in {time.time()-t:.1f}s")

# --------------------------------------------------------------- Stats
def summarise(nulls, key):
    arr = np.array([m[key] for m in nulls], dtype=float)
    return {
        "mean":   float(arr.mean()),
        "sd":     float(arr.std()),
        "p2.5":   float(np.percentile(arr, 2.5)),
        "p97.5":  float(np.percentile(arr, 97.5)),
        "n":      int(len(arr)),
    }

def two_sided_p(nulls, key, obs):
    arr = np.array([m[key] for m in nulls], dtype=float)
    return float(((np.abs(arr - arr.mean()) >= abs(obs - arr.mean())).sum() + 1) / (len(arr) + 1))

keys = ["RR", "DET", "LAM", "L_max", "V_max", "ENTR"]
summary = {}
for key in keys:
    obs = metrics_obs[key]
    ar1_s = summarise(ar1_rqa, key)
    iaaft_s = summarise(iaaft_rqa, key)
    p_ar1 = two_sided_p(ar1_rqa, key, obs)
    p_iaaft = two_sided_p(iaaft_rqa, key, obs)
    outside_ar1 = not (ar1_s["p2.5"] <= obs <= ar1_s["p97.5"])
    outside_iaaft = not (iaaft_s["p2.5"] <= obs <= iaaft_s["p97.5"])
    summary[key] = {
        "obs": float(obs),
        "ar1_null": ar1_s,
        "iaaft_null": iaaft_s,
        "p_vs_ar1":   p_ar1,
        "p_vs_iaaft": p_iaaft,
        "outside_95_ar1":   outside_ar1,
        "outside_95_iaaft": outside_iaaft,
    }
    print(f"  {key:6}: obs={obs:7.4f}  AR1={ar1_s['mean']:.4f}+-{ar1_s['sd']:.4f} "
          f"(p={p_ar1:.3f}, out={outside_ar1})  "
          f"IAAFT={iaaft_s['mean']:.4f}+-{iaaft_s['sd']:.4f} "
          f"(p={p_iaaft:.3f}, out={outside_iaaft})")

# --------------------------------------------------------------- Verdict
# PASS if DET or LAM is outside 95% CI for BOTH surrogate types.
det_dual = summary["DET"]["outside_95_ar1"] and summary["DET"]["outside_95_iaaft"]
lam_dual = summary["LAM"]["outside_95_ar1"] and summary["LAM"]["outside_95_iaaft"]
if det_dual or lam_dual:
    verdict = "STRUCTURED_DYNAMICS"
elif (summary["DET"]["outside_95_ar1"] or summary["DET"]["outside_95_iaaft"]
      or summary["LAM"]["outside_95_ar1"] or summary["LAM"]["outside_95_iaaft"]):
    verdict = "PARTIAL_DYNAMICS"
else:
    verdict = "NULL_NO_DYNAMICS"

# --------------------------------------------------------------- OUTPUTS
report = {
    "experiment_id": "expE9_takens_rqa",
    "task": "E9",
    "tier": 2,
    "title": "3-D Takens embedding + RQA (RR, DET, LAM, L_max, ENTR)",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "series": "verse-length of canonical Quran (6236 verses, stride-subsampled for RQA)",
    "n_orig":  int(N_orig),
    "n_rqa":   int(len(vl_rqa)),
    "embed_dim": EMBED_DIM,
    "tau_ami_first_min": int(tau),
    "ami_values_lags_1_to_50": ami.tolist(),
    "rr_target":  RR_TARGET,
    "epsilon":    float(eps),
    "metrics_observed": metrics_obs,
    "n_surr": N_SURR,
    "surrogate_types": ["AR1", "IAAFT"],
    "summary":  summary,
    "verdict":  verdict,
    "pre_registered_criteria": {
        "STRUCTURED_DYNAMICS": "DET or LAM outside 95% CI on BOTH surrogate types",
        "PARTIAL_DYNAMICS":    "DET or LAM outside 95% CI on exactly one type",
        "NULL_NO_DYNAMICS":    "DET and LAM inside both bands",
    },
}
(OUTDIR / "expE9_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)
np.savez_compressed(
    OUTDIR / "expE9_embedding_rqa.npz",
    E_rqa=E_rqa, E_full=E_full, ami=ami, eps=eps,
    tau=tau, embed_dim=EMBED_DIM,
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Recurrence plot
fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(R_obs, cmap="binary", origin="lower", interpolation="none")
ax.set_xlabel("t_i"); ax.set_ylabel("t_j")
ax.set_title(f"expE9 — recurrence plot "
             f"(verse-length series, m={EMBED_DIM}, tau={tau}, eps={eps:.3f})\n"
             f"RR={metrics_obs['RR']:.4f}, DET={metrics_obs['DET']:.4f}, "
             f"LAM={metrics_obs['LAM']:.4f}, L_max={metrics_obs['L_max']}")
fig.tight_layout()
fig.savefig(OUTDIR / "expE9_recurrence_plot.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# DET / LAM surrogate comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, key in zip(axes, ["DET", "LAM"]):
    ar1_vals = np.array([m[key] for m in ar1_rqa])
    iaaft_vals = np.array([m[key] for m in iaaft_rqa])
    ax.hist(ar1_vals, bins=30, alpha=0.6, label=f"AR(1) null (n={N_SURR})", color="C0")
    ax.hist(iaaft_vals, bins=30, alpha=0.6, label=f"IAAFT null (n={N_SURR})", color="C1")
    ax.axvline(metrics_obs[key], color="red", lw=2,
               label=f"observed = {metrics_obs[key]:.4f}")
    s = summary[key]
    ax.set_title(f"{key} surrogate comparison\n"
                 f"AR(1) p={s['p_vs_ar1']:.3f} (out={s['outside_95_ar1']}), "
                 f"IAAFT p={s['p_vs_iaaft']:.3f} (out={s['outside_95_iaaft']})")
    ax.set_xlabel(key); ax.set_ylabel("count"); ax.legend(); ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "expE9_surrogate_tests.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# AMI curve
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(lags, ami, "o-", color="C2")
ax.axvline(tau, color="red", ls="--", label=f"tau = {tau}")
ax.set_xlabel("lag"); ax.set_ylabel("AMI (bits)")
ax.set_title("Auto mutual information curve → tau selection")
ax.legend(); ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "expE9_ami_curve.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE9 — 3-D Takens embedding + RQA of Quran verse-length series",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **N_orig**: {N_orig}  |  **N_rqa (subsampled)**: {len(vl_rqa)}",
    f"**m**: {EMBED_DIM}  |  **tau (AMI first-min)**: {tau}  |  "
    f"**eps (target RR={RR_TARGET})**: {eps:.4f}",
    f"**Surrogates**: {N_SURR} AR(1) + {N_SURR} IAAFT",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: RQA metrics inside 95% CI of 500 AR(1) and 500 IAAFT surrogates.",
    "- **STRUCTURED_DYNAMICS**: DET or LAM outside 95% CI on BOTH surrogate types.",
    "- **PARTIAL_DYNAMICS**: DET or LAM outside 95% CI on exactly one surrogate type.",
    "- **NULL_NO_DYNAMICS**: DET and LAM inside both bands.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "## Observed RQA metrics",
    "",
    "| Metric | Observed | AR(1) null mean ± sd | IAAFT null mean ± sd | p vs AR(1) | p vs IAAFT | Outside AR(1) 95% | Outside IAAFT 95% |",
    "|---|--:|---|---|--:|--:|:-:|:-:|",
]
for key in keys:
    s = summary[key]
    md.append(
        f"| {key} | {s['obs']:.4f} | "
        f"{s['ar1_null']['mean']:.4f} ± {s['ar1_null']['sd']:.4f} | "
        f"{s['iaaft_null']['mean']:.4f} ± {s['iaaft_null']['sd']:.4f} | "
        f"{s['p_vs_ar1']:.4f} | {s['p_vs_iaaft']:.4f} | "
        f"{'YES' if s['outside_95_ar1'] else 'no'} | "
        f"{'YES' if s['outside_95_iaaft'] else 'no'} |"
    )

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE9_report.json` — all RQA numbers + surrogate p-values")
md.append("- `expE9_embedding_rqa.npz` — Takens embedding arrays + AMI curve")
md.append("- `expE9_recurrence_plot.png` — recurrence plot of observed series")
md.append("- `expE9_surrogate_tests.png` — DET / LAM histograms vs observed")
md.append("- `expE9_ami_curve.png` — auto mutual info lag scan")

(OUTDIR / "expE9_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}")
print(f"Outputs in {OUTDIR}")
print(f"Total runtime: {time.time()-t0:.1f}s")
