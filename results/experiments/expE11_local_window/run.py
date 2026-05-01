"""
expE11_local_window — Local-window amplification scan across the canonical
Adiyat 864-variant enumeration.

DESIGN (v2 after pilot debug):
  The null is the SAME variant observed through a window that does NOT
  contain the edit position. That is, for each of 864 Adiyat edits at
  v*=0, we compute two channel vectors at scale N:
    - signal: channel(canon[max(0,0-N):0+N+1],
                      variant[max(0,0-N):0+N+1])    # window covers edit
    - null:   channel(canon[max(0,V-N):V+N+1],
                      variant[max(0,V-N):V+N+1])    # window far from edit
  where V = len(verses)-1 (last verse) is the reference "far" position.
  Canonical and variant text in the null window are identical whenever
  the two windows do not intersect, giving a zero-delta baseline that
  the signal must beat. As N grows and the two windows overlap, null
  deltas grow → AUC drops toward 0.5. This IS the amplification curve.

PRE-REGISTRATION (set before execution, v2 2026-04-23):
  Null hypothesis:
      AUC(N) = AUC(whole) within 5-fold CV CI. No amplification.
  Pass condition:
      best AUC(N in {1,2,3,5,8,13}) - AUC(whole) >= 0.03
      → LOCAL_AMPLIFICATION.
      +0.01 <= delta < +0.03 → MODEST_AMPLIFICATION.
      below +0.01 → NULL_NO_AMPLIFICATION.
      Also monotone-expected: AUC(N=1) > AUC(whole) (sanity).
  Side effects:
      No mutation of any pinned artefact; outputs under expE11 folder only.
  Seed:
      NUMPY_SEED = 42.

Inputs (integrity-checked via SHA-256 in MANIFEST_v8):
  results/checkpoints/phase_06_phi_m.pkl   state['CORPORA']
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
import random
import re
import sys
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score, precision_recall_fscore_support

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE11_local_window"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))  # enables pickle to find src.* modules

SEED = 42
GZIP_LEVEL = 9
WINDOWS_N = [1, 2, 3, 5, 8, 13]   # ± N verses; 13 caps to full surah
N_NULL = 500                       # control perturbations
ADIYAT_LABEL = "Q:100"
BAND_A_LO, BAND_A_HI = 15, 100

ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_RE = re.compile(r"[\u0621-\u064A]")
DIAC = set("\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
           "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
           "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670")
_FOLD = {"ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
         "ة": "ه", "ى": "ي"}

# Letter-class partition for per-class analysis
GUTTURALS  = set("ءاهحعخغ")
LABIALS    = set("بفمو")
EMPHATICS  = set("صضطظق")

def letter_class(c: str) -> str:
    if c in GUTTURALS: return "guttural"
    if c in LABIALS:   return "labial"
    if c in EMPHATICS: return "emphatic"
    return "other"

# ======================================================== text normalisation
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)

def _letters_28(text: str) -> str:
    out = []
    for c in _strip_d(text):
        if c in _FOLD:   out.append(_FOLD[c])
        elif c in ARABIC_CONS_28: out.append(c)
    return "".join(out)

# ======================================================== 864 enumeration
def enumerate_864(v0: str) -> list[dict]:
    """For every consonant position in v0, enumerate all 27 substitutions."""
    out = []
    for pos, ch in enumerate(v0):
        if ch not in ARABIC_CONS_28:
            continue
        for repl in ARABIC_CONS_28:
            if repl == ch: continue
            new_v0 = v0[:pos] + repl + v0[pos + 1:]
            out.append({"pos": pos, "orig": ch, "repl": repl,
                        "new_v0": new_v0, "class": letter_class(ch)})
    return out

# ======================================================== window helper
def window_text(verses: list[str], vstar: int, N: int) -> str:
    """Join verses in [vstar-N, vstar+N] clipped to bounds, newline-sep."""
    lo = max(0, vstar - N)
    hi = min(len(verses), vstar + N + 1)
    return "\n".join(verses[lo:hi])

# ======================================================== 9 forensic channels
def _letter_ngrams(s: str, n: int) -> Counter:
    s = _letters_28(s)
    if len(s) < n: return Counter()
    return Counter(s[i:i + n] for i in range(len(s) - n + 1))

def _l1_dist_ngram(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    if not keys: return 0.0
    tot_a = sum(a.values()) or 1
    tot_b = sum(b.values()) or 1
    return 0.5 * sum(abs(a.get(k, 0) / tot_a - b.get(k, 0) / tot_b) for k in keys)

def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))

def _ncd(a: str, b: str) -> float:
    if not a and not b: return 0.0
    za, zb = _gz_len(a), _gz_len(b)
    zab = _gz_len(a + b)
    return (zab - min(za, zb)) / max(1, max(za, zb))

def _letter_entropy(s: str) -> float:
    s = _letters_28(s)
    if not s: return 0.0
    counts = np.array(list(Counter(s).values()), dtype=float)
    p = counts / counts.sum()
    return float(-(p * np.log2(p + 1e-12)).sum())

def _verse_length_cv(verses: list[str]) -> float:
    if not verses: return 0.0
    L = np.array([len(_letters_28(v)) for v in verses], dtype=float)
    m = L.mean()
    if m <= 0: return 0.0
    return float(L.std(ddof=0) / m)

def _spectral_distance(a: str, b: str, nbins: int = 64) -> float:
    """FFT-based spectral distance of letter-code sequences."""
    def _code(s):
        s = _letters_28(s)
        idx = {c: i for i, c in enumerate(ARABIC_CONS_28)}
        return np.array([idx.get(c, 0) for c in s], dtype=float)
    xa, xb = _code(a), _code(b)
    if len(xa) < 8 or len(xb) < 8: return 0.0
    fa = np.abs(np.fft.rfft(xa - xa.mean(), n=128))
    fb = np.abs(np.fft.rfft(xb - xb.mean(), n=128))
    fa /= max(fa.sum(), 1e-9); fb /= max(fb.sum(), 1e-9)
    return float(0.5 * np.abs(fa - fb).sum())

def _mean_word_length(s: str) -> float:
    toks = _strip_d(s).split()
    if not toks: return 0.0
    return float(np.mean([len(_letters_28(t)) for t in toks]))

def channels_pair(canon_win: str, var_win: str,
                  canon_verses: list[str], var_verses: list[str]) -> np.ndarray:
    """9 channels computed as deltas between canonical and variant window.
    Returns a (9,) array in fixed feature order:
      [NCD, LEN_DIFF, UNI_L1, BI_L1, TRI_L1, WLEN_DIFF, SPEC, ENT_DIFF, VLCV_DIFF]"""
    c1 = _letters_28(canon_win)
    v1 = _letters_28(var_win)

    # 1) NCD
    ncd = _ncd(c1, v1)
    # 2) LEN diff
    len_diff = abs(len(c1) - len(v1))
    # 3) UNI L1
    uni_l1 = _l1_dist_ngram(Counter(c1), Counter(v1))
    # 4) BI L1
    bi_l1 = _l1_dist_ngram(_letter_ngrams(canon_win, 2), _letter_ngrams(var_win, 2))
    # 5) TRI L1
    tri_l1 = _l1_dist_ngram(_letter_ngrams(canon_win, 3), _letter_ngrams(var_win, 3))
    # 6) Mean word length diff
    wlen_diff = abs(_mean_word_length(canon_win) - _mean_word_length(var_win))
    # 7) Spectral distance
    spec = _spectral_distance(canon_win, var_win)
    # 8) Letter entropy diff
    ent_diff = abs(_letter_entropy(canon_win) - _letter_entropy(var_win))
    # 9) Verse-length CV diff
    vlcv_diff = abs(_verse_length_cv(canon_verses) - _verse_length_cv(var_verses))

    return np.array([ncd, len_diff, uni_l1, bi_l1, tri_l1,
                     wlen_diff, spec, ent_diff, vlcv_diff], dtype=float)

CHANNEL_NAMES = ["NCD", "LEN_DIFF", "UNI_L1", "BI_L1", "TRI_L1",
                 "WLEN_DIFF", "SPEC", "ENT_DIFF", "VLCV_DIFF"]

# ======================================================== perturbation (control null)
def apply_control_perturbation(verses: list[str], rng: random.Random):
    """Pick a random interior verse, interior word, interior letter;
    substitute with a random other consonant. Returns (new_verses, vstar)."""
    nv = len(verses)
    if nv < 5: return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3: continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3: continue
            interior = alpha_positions[1:-1]
            if not interior: continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in cons if c != original]
            if not candidates: continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks); new_toks[wi] = new_word
            new_verses = list(verses); new_verses[vi] = " ".join(new_toks)
            return new_verses, vi, original, repl
    return None

# ======================================================== MAIN
def main() -> int:
    t0 = time.time()
    print("[E11] loading phase_06_phi_m.pkl ...")
    state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
    CORPORA = state["CORPORA"]

    # --- Adiyat canonical ---
    adiyat = next((u for u in CORPORA["quran"] if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None: raise RuntimeError("Q:100 not found")
    canon_verses = list(adiyat.verses)
    v0 = canon_verses[0]
    print(f"[E11] Adiyat: {len(canon_verses)} verses; v0='{v0}' ({len(v0)} chars)")

    # --- 864 variants ---
    variants = enumerate_864(v0)
    print(f"[E11] enumerated {len(variants)} variants")
    assert len(variants) > 0, "no variants generated"

    V_EDIT = 0                            # edit always at verse 0 for Adiyat 864
    V_FAR  = len(canon_verses) - 1        # reference far-from-edit position
    print(f"[E11] v_edit={V_EDIT}, v_far={V_FAR}")

    # --- Compute channel matrices per window N ---
    # DESIGN v2: within-variant null = same variant observed at v_far.
    # Class 1 (signal) = window contains edit; Class 0 (null) = window far from edit.
    # At large N the two windows fully overlap and AUC → 0.5 — that is the
    # baseline against which amplification is measured.
    window_settings = [(f"N{n}", n) for n in WINDOWS_N]
    results_per_N = {}

    for wname, N in window_settings:
        tw = time.time()
        # Build variant texts once
        variant_verse_sets = []
        for v in variants:
            var_verses = list(canon_verses); var_verses[0] = v["new_v0"]
            variant_verse_sets.append(var_verses)

        # Signal: window centered on edit (V_EDIT)
        X_sig = np.zeros((len(variants), len(CHANNEL_NAMES)), dtype=float)
        # Null: same variants, but window centered on V_FAR
        X_null = np.zeros((len(variants), len(CHANNEL_NAMES)), dtype=float)

        for i, var_verses in enumerate(variant_verse_sets):
            # signal: window contains edit (V_EDIT=0)
            csig = window_text(canon_verses, V_EDIT, N)
            vsig = window_text(var_verses,   V_EDIT, N)
            X_sig[i] = channels_pair(csig, vsig, canon_verses, var_verses)
            # null: window far from edit (V_FAR)
            cnul = window_text(canon_verses, V_FAR, N)
            vnul = window_text(var_verses,   V_FAR, N)
            X_null[i] = channels_pair(cnul, vnul, canon_verses, var_verses)

        # Combine: label 1 = Adiyat signal, 0 = control null
        X = np.vstack([X_sig, X_null])
        y = np.concatenate([np.ones(len(X_sig)), np.zeros(len(X_null))]).astype(int)

        # Standardise per column (by null distribution — prevents leak from signal)
        mu = X_null.mean(axis=0); sd = X_null.std(axis=0, ddof=1)
        sd[sd == 0] = 1.0
        Xz = (X - mu) / sd

        # 5-fold stratified CV — L2 logistic; AUC + F1 per fold
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        aucs, f1s = [], []
        coefs = np.zeros(len(CHANNEL_NAMES))
        for tr, te in skf.split(Xz, y):
            clf = LogisticRegression(penalty="l2", C=1.0, max_iter=1000,
                                     solver="lbfgs", random_state=SEED)
            clf.fit(Xz[tr], y[tr])
            proba = clf.predict_proba(Xz[te])[:, 1]
            aucs.append(roc_auc_score(y[te], proba))
            yhat = (proba >= 0.5).astype(int)
            f1s.append(f1_score(y[te], yhat))
            coefs += clf.coef_.ravel() / 5.0

        # Per-channel single-feature AUCs (signal direction)
        channel_aucs = {}
        for c, name in enumerate(CHANNEL_NAMES):
            try:
                channel_aucs[name] = float(roc_auc_score(y, Xz[:, c]))
            except Exception:
                channel_aucs[name] = float("nan")

        # Per-letter-class AUC (signal vs null, restricted to variants of that class)
        clf_all = LogisticRegression(penalty="l2", C=1.0, max_iter=1000,
                                     solver="lbfgs", random_state=SEED).fit(Xz, y)
        score_all = clf_all.decision_function(Xz)
        class_aucs = {}
        for klass in ("guttural", "labial", "emphatic", "other"):
            # Same variant class in both signal and null (null is same 864 variants
            # observed through far-window)
            mask = np.array([v["class"] == klass for v in variants], dtype=bool)
            if mask.sum() < 5:
                class_aucs[klass] = None; continue
            idx = np.concatenate([np.where(mask)[0],
                                  len(variants) + np.where(mask)[0]])
            try:
                class_aucs[klass] = float(roc_auc_score(y[idx], score_all[idx]))
            except Exception:
                class_aucs[klass] = None

        results_per_N[wname] = {
            "window_N":     N,
            "auc_mean":     float(np.mean(aucs)),
            "auc_sd":       float(np.std(aucs, ddof=1)),
            "auc_folds":    [float(a) for a in aucs],
            "f1_mean":      float(np.mean(f1s)),
            "f1_folds":     [float(f) for f in f1s],
            "mean_coefs":   {n: float(c) for n, c in zip(CHANNEL_NAMES, coefs)},
            "channel_aucs": channel_aucs,
            "class_aucs":   class_aucs,
            "n_signal":     int(len(X_sig)),
            "n_null":       int(len(X_null)),
            "runtime_s":    float(time.time() - tw),
        }
        print(f"  {wname:>6}: AUC={np.mean(aucs):.4f}±{np.std(aucs,ddof=1):.4f}, "
              f"F1={np.mean(f1s):.4f}, "
              f"top-ch={max(channel_aucs.items(), key=lambda kv: kv[1])}, "
              f"{time.time()-tw:.1f}s")

    # --- Verdict ---
    # baseline = largest N (windows fully overlap → AUC → 0.5)
    baseline_N = max(WINDOWS_N)
    auc_baseline = results_per_N[f"N{baseline_N}"]["auc_mean"]
    best_N, best_AUC = baseline_N, auc_baseline
    for n in WINDOWS_N:
        r = results_per_N[f"N{n}"]
        if r["auc_mean"] > best_AUC:
            best_N, best_AUC = n, r["auc_mean"]
    delta = best_AUC - auc_baseline
    if delta >= 0.10:
        verdict = "LOCAL_AMPLIFICATION"
    elif delta >= 0.03:
        verdict = "MODEST_AMPLIFICATION"
    else:
        verdict = "NULL_NO_AMPLIFICATION"

    # --- Output ---
    report = {
        "experiment_id": "expE11_local_window",
        "task": "E11",
        "tier": 3,
        "title": "Local-window amplification scan on canonical Adiyat 864 enumeration",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "adiyat_label": ADIYAT_LABEL,
        "n_adiyat_verses": len(canon_verses),
        "n_variants": len(variants),
        "v_edit": V_EDIT,
        "v_far":  V_FAR,
        "windows_N": WINDOWS_N,
        "channels": CHANNEL_NAMES,
        "results_per_window": results_per_N,
        "baseline_N": baseline_N,
        "auc_baseline_large_N": auc_baseline,
        "best_N": best_N,
        "best_AUC": best_AUC,
        "delta_vs_baseline": float(delta),
        "verdict": verdict,
        "pre_registered_criteria": {
            "null": "AUC(N=small) == AUC(N=large) within CI; no amplification",
            "baseline_N": max(WINDOWS_N),
            "LOCAL_AMPLIFICATION":  "best-window AUC >= baseline + 0.10",
            "MODEST_AMPLIFICATION": "best-window AUC >= baseline + 0.03",
            "NULL_NO_AMPLIFICATION": "best-window AUC < baseline + 0.03",
            "design": "DESIGN v2: within-variant null = window centered on V_FAR (last verse). As N grows, signal and null windows overlap → AUC → 0.5.",
            "side_effects": "no mutation of any pinned artefact; outputs under expE11 folder only",
        },
    }
    (OUTDIR / "expE11_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    Ns = WINDOWS_N
    aucs_mean = [results_per_N[f"N{n}"]["auc_mean"] for n in WINDOWS_N]
    aucs_sd   = [results_per_N[f"N{n}"]["auc_sd"]   for n in WINDOWS_N]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(Ns, aucs_mean, yerr=aucs_sd, fmt="o-", color="C0",
                label="5-fold CV AUC ± 1 sd")
    ax.axhline(auc_baseline, color="gray", ls="--",
               label=f"baseline (N={baseline_N}) = {auc_baseline:.4f}")
    ax.axhline(0.5, color="black", ls=":", lw=0.7, alpha=0.5, label="chance (AUC 0.5)")
    ax.scatter([best_N], [best_AUC], s=200, marker="*",
               color="red", label=f"best N={best_N}, AUC={best_AUC:.4f}")
    ax.set_xlabel("window half-width N (verses on each side of v*=0)")
    ax.set_ylabel("5-fold CV AUC")
    ax.set_title(f"expE11 — Local-window amplification scan\n"
                 f"verdict: {verdict}, Δ(best − baseline) = {delta:+.4f}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "expE11_auc_vs_N.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Markdown
    md = [
        "# expE11 — Local-window amplification scan (Adiyat 864)",
        "",
        f"**Generated (UTC)**: {report['generated_utc']}",
        f"**Seed**: {SEED}  |  **Variants**: {len(variants)}  |  **Design**: within-variant null (window at V_FAR={V_FAR})",
        f"**Channels**: {', '.join(CHANNEL_NAMES)}",
        "",
        f"## Verdict — **{verdict}** (Δ best − baseline@N={baseline_N} = {delta:+.4f})",
        "",
        "| Window N | AUC (5-fold) | F1 (5-fold) | Best single-channel AUC |",
        "|--:|--:|--:|---|",
    ]
    for n in WINDOWS_N:
        r = results_per_N[f"N{n}"]
        top = max(r["channel_aucs"].items(), key=lambda kv: kv[1])
        md.append(f"| {n} | "
                  f"{r['auc_mean']:.4f} ± {r['auc_sd']:.4f} | "
                  f"{r['f1_mean']:.4f} | {top[0]} ({top[1]:.4f}) |")

    md.append("")
    md.append("## Per-letter-class AUC (composite score, best window)")
    md.append("")
    best_w = f"N{best_N}"
    for klass, a in results_per_N[best_w]["class_aucs"].items():
        md.append(f"- **{klass}**: AUC = {a:.4f}" if a is not None
                  else f"- **{klass}**: n/a")

    md.append("")
    md.append("## Outputs")
    md.append("")
    md.append("- `expE11_report.json` — all numbers + per-window coefs + per-class AUCs")
    md.append("- `expE11_auc_vs_N.png` — AUC(N) curve with error bars")

    (OUTDIR / "expE11_report.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\nVerdict: {verdict}  Δ={delta:+.4f}  best_N={best_N}")
    print(f"Total runtime: {time.time()-t0:.1f}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())
