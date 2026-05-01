"""
expE13_auth_gate — Formalize the 1-of-865 authentication gate as a single
scalar statistic. Given 864 single-letter variants of Adiyat v1 + the canonical
text, compute a per-text composite score and test whether the detector ranks
the canonical text first out of all 865 candidates under random permutation.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Detector assigns no preferential rank to the canonical; under a uniform
      prior, P(canonical in top-1 of 865) = 1/865 ≈ 1.16e-3.
  Pass condition:
      Empirical rank of canonical text = 1 on all 5 independent seeds
      (seeds = {42, 43, 44, 45, 46}); empirical 1-of-865 p-value <= 0.01
      → GATE_SOLID.
      Ranks all <= 10 (top-1.2 %) but not uniformly 1 → GATE_USEFUL.
      Any rank > 10 → NULL_GATE_FAILS.
  Side effects:
      No mutation of any pinned artefact; outputs under expE13 folder only.

Design:
  For each of the 865 texts (canonical + 864 variants), compute two
  channel-vectors at window N=5: signal_i = channel(canon[0:N+1], text[0:N+1])
  and null_i = channel(canon[V_FAR-N:V_FAR+N+1], text[V_FAR-N:V_FAR+N+1]).
  Train the KDE Bayesian fusion detector (E12) on the 864 variants (labels
  known: signal class) and score the canonical the same way; the canonical's
  signal vector at N=5 is channel(canon_window, canon_window) = all zeros,
  which should correspond to "NO EDIT" -> null class.

  The gate statistic:
      s(text) = logP(no_edit | signal_features) - logP(edit | signal_features)
  under the KDE fusion model. Higher s → more confident the text is canonical.
  Rank the 865 scores; canonical should be rank 1.
"""
from __future__ import annotations

import importlib.util
import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.neighbors import KernelDensity

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE13_auth_gate"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

WINDOW_N = 5
SEEDS = [42, 43, 44, 45, 46]
ADIYAT_LABEL = "Q:100"

# Reuse E11
E11_PATH = ROOT / "results" / "experiments" / "expE11_local_window" / "run.py"
spec = importlib.util.spec_from_file_location("expE11_run", E11_PATH)
e11 = importlib.util.module_from_spec(spec)
sys.modules["expE11_run"] = e11
spec.loader.exec_module(e11)
channels_pair, CHANNEL_NAMES = e11.channels_pair, e11.CHANNEL_NAMES
enumerate_864, window_text = e11.enumerate_864, e11.window_text

# --------------------------------------------------------------- LOAD
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
adiyat = next(u for u in state["CORPORA"]["quran"] if getattr(u, "label", "") == ADIYAT_LABEL)
canon_verses = list(adiyat.verses)
v0 = canon_verses[0]
variants = enumerate_864(v0)
V_EDIT, V_FAR = 0, len(canon_verses) - 1
N = WINDOW_N

# --------------------------------------------------------------- Build 865-text dataset
print(f"[E13] building 865-text feature matrix at N={N}")
# First text: canonical (edit position = 0 but no edit) — feature = channels(canon, canon)
X_all = np.zeros((865, len(CHANNEL_NAMES)))
texts_meta = []

# canonical as "text 0"
cwin = window_text(canon_verses, V_EDIT, N)
# canonical "variant" = canonical itself
X_all[0] = channels_pair(cwin, cwin, canon_verses, canon_verses)
texts_meta.append({"idx": 0, "kind": "canonical", "pos": None, "orig": None, "repl": None})

# 864 variants
for i, v in enumerate(variants, start=1):
    var_verses = list(canon_verses); var_verses[0] = v["new_v0"]
    vwin = window_text(var_verses, V_EDIT, N)
    X_all[i] = channels_pair(cwin, vwin, canon_verses, var_verses)
    texts_meta.append({"idx": i, "kind": "variant", "pos": v["pos"],
                       "orig": v["orig"], "repl": v["repl"], "class": v["class"]})

print(f"[E13] canonical features (should be ~0): {X_all[0]}")
print(f"[E13] variant features: mean={X_all[1:].mean(axis=0)}")

# --------------------------------------------------------------- Null features (from V_FAR windows)
X_null = np.zeros((len(variants), len(CHANNEL_NAMES)))
for i, v in enumerate(variants):
    var_verses = list(canon_verses); var_verses[0] = v["new_v0"]
    cnul = window_text(canon_verses, V_FAR, N)
    vnul = window_text(var_verses,   V_FAR, N)
    X_null[i] = channels_pair(cnul, vnul, canon_verses, var_verses)

# Standardize by null std (all classes)
mu = X_null.mean(axis=0); sd = X_null.std(axis=0, ddof=1); sd[sd == 0] = 1.0
X_all_z = (X_all - mu) / sd
X_null_z = (X_null - mu) / sd
# Training data for Bayesian: signal = 864 variants at V_EDIT (labels=1), null = 864 variants at V_FAR (labels=0)
X_sig_z = X_all_z[1:]  # skip canonical
X_train = np.vstack([X_sig_z, X_null_z])
y_train = np.concatenate([np.ones(len(X_sig_z)), np.zeros(len(X_null_z))]).astype(int)

# --------------------------------------------------------------- KDE-NB training
def train_kde_nb(X, y, bandwidth=0.25):
    keep = np.ones(X.shape[1], dtype=bool)
    for c in (0, 1):
        keep &= X[y == c].std(axis=0, ddof=1) > 1e-9
    if keep.sum() == 0: keep[:] = True
    classes = (0, 1)
    kdes = {}
    for c in classes:
        Xc = X[y == c][:, keep]
        kdes[c] = [KernelDensity(bandwidth=bandwidth).fit(
                      Xc[:, j].reshape(-1, 1))
                   for j in range(Xc.shape[1])]
    priors = np.array([(y == c).mean() for c in classes])
    return {"keep": keep, "kdes": kdes, "classes": classes,
            "log_prior": np.log(np.clip(priors, 1e-9, 1.0))}

def log_posterior(model, X):
    Xk = X[:, model["keep"]]
    lj = np.zeros((X.shape[0], 2))
    for ci, c in enumerate(model["classes"]):
        lj[:, ci] = model["log_prior"][ci] + sum(
            model["kdes"][c][j].score_samples(Xk[:, j].reshape(-1, 1))
            for j in range(Xk.shape[1])
        )
    # normalize
    m = lj.max(axis=1, keepdims=True)
    logp = lj - (m + np.log(np.exp(lj - m).sum(axis=1, keepdims=True)))
    return logp  # shape (n, 2); col 0 = log P(no_edit), col 1 = log P(edit)

# --------------------------------------------------------------- Run across seeds
print("\nAuthentication gate across {} seeds:".format(len(SEEDS)))
ranks_per_seed = []
for sd_val in SEEDS:
    rng = np.random.default_rng(sd_val)
    # Bootstrap the training set (with replacement) to introduce seed variability
    idx_bs = rng.choice(len(X_train), size=len(X_train), replace=True)
    model = train_kde_nb(X_train[idx_bs], y_train[idx_bs], bandwidth=0.25)

    # Gate statistic for each of 865 texts
    logp_all = log_posterior(model, X_all_z)
    # Authentication score: log P(no_edit) - log P(edit). Higher = more canonical-like.
    gate_score = logp_all[:, 0] - logp_all[:, 1]
    canon_score = gate_score[0]
    # rank: 1 + number of texts with strictly higher gate_score
    rank_canonical = int(1 + (gate_score > canon_score).sum())
    ranks_per_seed.append(rank_canonical)
    p_emp = rank_canonical / 865.0
    print(f"  seed={sd_val}: canonical gate score = {canon_score:+.4f}, "
          f"rank = {rank_canonical}/865 (emp p={p_emp:.4e})")

# --------------------------------------------------------------- Verdict
ranks_per_seed = np.array(ranks_per_seed, dtype=int)
all_rank_1   = bool(np.all(ranks_per_seed == 1))
all_top_10   = bool(np.all(ranks_per_seed <= 10))
p_emp_mean   = float(ranks_per_seed.mean() / 865.0)
if all_rank_1 and p_emp_mean <= 0.01:
    verdict = "GATE_SOLID"
elif all_top_10:
    verdict = "GATE_USEFUL"
else:
    verdict = "NULL_GATE_FAILS"

# --------------------------------------------------------------- Permutation null
# For comparison, under uniform prior: 10_000 random rankings of 865 items.
rng_null = np.random.default_rng(0)
perm_ranks_top1 = (rng_null.integers(1, 866, size=10000) == 1).sum() / 10000
perm_p = 1.0 / 865.0
print(f"\nTheoretical null P(rank=1 | uniform) = 1/865 = {perm_p:.4e}")
print(f"Empirical mean rank across seeds = {ranks_per_seed.mean():.2f} / 865")

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id": "expE13_auth_gate",
    "task": "E13",
    "tier": 3,
    "title": "1-of-865 authentication gate: single-scalar composite statistic",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "window_N": WINDOW_N,
    "seeds": SEEDS,
    "n_texts": 865,
    "n_variants": len(variants),
    "gate_definition": "s(text) = logP(no_edit | channel_features) - logP(edit | channel_features) under KDE-NB fusion",
    "canon_feature_norm_whole": float(np.linalg.norm(X_all_z[0])),
    "canon_rank_per_seed": ranks_per_seed.tolist(),
    "canon_rank_mean":     float(ranks_per_seed.mean()),
    "canon_rank_max":      int(ranks_per_seed.max()),
    "empirical_p_mean":    p_emp_mean,
    "theoretical_uniform_p": perm_p,
    "verdict": verdict,
    "pre_registered_criteria": {
        "null": "Under uniform prior, P(rank=1 | canonical) = 1/865",
        "GATE_SOLID":     "rank=1 on all 5 seeds AND empirical p<=0.01",
        "GATE_USEFUL":    "rank<=10 on all 5 seeds (top 1.2%)",
        "NULL_GATE_FAILS": "any seed has rank>10",
        "side_effects":   "no mutation of any pinned artefact; outputs under expE13 folder only",
    },
}
(OUTDIR / "expE13_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Gate-score distribution at one representative seed (42)
rng = np.random.default_rng(42)
idx_bs = rng.choice(len(X_train), size=len(X_train), replace=True)
model = train_kde_nb(X_train[idx_bs], y_train[idx_bs], bandwidth=0.25)
logp_all = log_posterior(model, X_all_z)
gate_score = logp_all[:, 0] - logp_all[:, 1]
canon_score = gate_score[0]

fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(gate_score[1:], bins=40, color="C0", alpha=0.7,
        label=f"864 variants (range {gate_score[1:].min():.2f} .. {gate_score[1:].max():.2f})")
ax.axvline(canon_score, color="red", lw=2,
           label=f"canonical (rank {ranks_per_seed[0]}/865, s={canon_score:+.3f})")
ax.set_xlabel("gate statistic  s = logP(no_edit | features) - logP(edit | features)")
ax.set_ylabel("count")
ax.set_title(f"expE13 — 1-of-865 authentication gate\n"
             f"verdict: {verdict}, mean rank = {ranks_per_seed.mean():.2f}/865 "
             f"(theoretical uniform p = {perm_p:.4e})")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "expE13_gate_histogram.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE13 — 1-of-865 authentication gate (Adiyat)",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Window N**: {WINDOW_N}  |  **Seeds**: {SEEDS}  |  **Texts**: 865 (1 canonical + 864 variants)",
    f"**Channels**: {', '.join(CHANNEL_NAMES)}",
    "",
    "## Gate definition",
    "",
    "```",
    "s(text) = log P(no_edit | channel_features(canon, text))",
    "        - log P(edit    | channel_features(canon, text))",
    "```",
    "",
    "where `channel_features` is the 9-vector from expE11 at window N=5, and",
    "`log P(·)` comes from a KDE Naive-Bayes model trained on the 864 variants",
    "(class 1 = edit-in-window) vs their far-window counterparts (class 0).",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: canonical text rank = 1 with probability 1/865 ≈ 0.00116 under uniform prior.",
    "- **GATE_SOLID**: rank = 1 on all 5 seeds AND empirical p ≤ 0.01.",
    "- **GATE_USEFUL**: rank ≤ 10 on all 5 seeds.",
    "- **NULL_GATE_FAILS**: any seed rank > 10.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "| Seed | canonical rank / 865 | empirical p |",
    "|---|--:|--:|",
]
for sd_val, r in zip(SEEDS, ranks_per_seed):
    md.append(f"| {sd_val} | {r} | {r/865:.4e} |")

md.append("")
md.append(f"- **Mean rank**: {ranks_per_seed.mean():.2f} / 865")
md.append(f"- **Max rank**:  {ranks_per_seed.max()} / 865")
md.append(f"- **Mean empirical p**: {p_emp_mean:.4e}")
md.append(f"- **Theoretical uniform p**: {perm_p:.4e}")

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE13_report.json` — gate stats + verdict")
md.append("- `expE13_gate_histogram.png` — canonical vs variants histogram")

(OUTDIR / "expE13_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}")
print(f"Total runtime: {time.time()-t0:.1f}s")
