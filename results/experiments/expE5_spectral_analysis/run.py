"""
expE5_spectral_analysis — Fourier + multitaper spectral analysis on the
canonical Mushaf verse-length (6236 pts) and end-letter (6236 pts) series.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Shuffled-null PSD envelope is indistinguishable from the observed PSD;
      the series is 1/f^α persistent noise with no discrete rhythm.
  Pass condition:
      ≥1 frequency bin survives Bonferroni-corrected shuffle null (p < 0.05/n_freq)
      AND the peak-to-baseline ratio is > 1.5× the 95th-pctile of the 1000-shuffle
      envelope. Outcome tagged SUGGESTIVE if 1-5 bins pass; RHYTHMIC if ≥6 pass.
  Side effects:
      No mutation of any pinned artefact. Outputs live exclusively under
      results/experiments/expE5_spectral_analysis/.
  Seed:
      NUMPY_SEED = 42 (matches the rest of the QSF pipeline).
"""
from __future__ import annotations

import json
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.signal import periodogram, windows

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT   = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE5_spectral_analysis"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_SHUFFLES = 1000
NW = 4            # multitaper time-bandwidth product
K_TAPERS = 7      # number of DPSS tapers (Slepian rule: 2·NW - 1 = 7)
RNG = np.random.default_rng(SEED)

# ------------------------------------------------------------------ LOAD
sys.path.insert(0, str(ROOT))
import pickle
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
quran_units = state["CORPORA"]["quran"]         # 114 Unit objects in mushaf order
n_surahs = len(quran_units)
assert n_surahs == 114, f"expected 114 Quran units, got {n_surahs}"

ARABIC_RE = re.compile(r"[\u0621-\u064A]")        # Arabic letter range

def last_letter(verse: str) -> str:
    letters = ARABIC_RE.findall(verse)
    return letters[-1] if letters else ""

# ----- Build the two canonical time series in mushaf order --------
vl_series: list[int]  = []   # words per verse
el_series: list[str]  = []   # last Arabic letter per verse
verse_index: list[tuple[int,int]] = []    # (surah_idx, verse_idx)

for s_idx, u in enumerate(quran_units):
    for v_idx, verse in enumerate(u.verses):
        nw = len(verse.split())
        vl_series.append(nw)
        el_series.append(last_letter(verse))
        verse_index.append((s_idx + 1, v_idx + 1))

vl = np.asarray(vl_series, dtype=float)
# Encode end-letter as integer index by sorted unique letters
uniq_letters = sorted({l for l in el_series if l})
letter_to_idx = {l: i for i, l in enumerate(uniq_letters)}
el = np.asarray([letter_to_idx.get(l, -1) for l in el_series], dtype=float)
# drop any positions where end-letter was empty (rare)
mask = el >= 0
vl_aligned = vl[mask]
el_aligned = el[mask]
n_pts = int(mask.sum())

print(f"Loaded in {time.time()-t0:.2f}s — {n_surahs} surahs, {n_pts} verses retained")
print(f"  unique end-letters: {len(uniq_letters)}")

# ------------------------------------------------------------------ CORE
def multitaper_psd(x: np.ndarray, fs: float = 1.0, NW: float = NW,
                   K: int = K_TAPERS) -> tuple[np.ndarray, np.ndarray]:
    """Return (freqs, mean-of-tapered periodogram) using K DPSS windows.
    Detrends x by removing mean; zero-pads to even length.
    """
    x = x - x.mean()
    n = len(x)
    if n % 2:
        x = np.concatenate([x, [0.0]])
        n += 1
    tapers = windows.dpss(n, NW, K)           # (K, n)
    psds = []
    for w in tapers:
        f, pxx = periodogram(x * w, fs=fs, scaling="spectrum")
        psds.append(pxx)
    mean_psd = np.mean(psds, axis=0)
    return f, mean_psd

def ar1_surrogate(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Yule-Walker AR(1) surrogate preserving phi_1 and noise variance."""
    x = x - x.mean()
    if len(x) < 10:
        return rng.standard_normal(len(x))
    phi = np.corrcoef(x[:-1], x[1:])[0, 1]
    sigma = np.std(x) * np.sqrt(max(1 - phi ** 2, 1e-9))
    out = np.empty_like(x)
    out[0] = rng.standard_normal() * sigma
    for i in range(1, len(x)):
        out[i] = phi * out[i - 1] + sigma * rng.standard_normal()
    return out

def spectral_slope(f: np.ndarray, psd: np.ndarray) -> tuple[float, float]:
    """Fit log(psd) = -alpha * log(f) + b on f > 0; return (alpha, b)."""
    m = (f > 0) & (psd > 0)
    lf, lp = np.log10(f[m]), np.log10(psd[m])
    alpha, b = np.polyfit(lf, lp, 1)
    return float(-alpha), float(b)        # alpha > 0 = reddening

def analyze(series: np.ndarray, name: str) -> dict:
    t = time.time()
    f_obs, psd_obs = multitaper_psd(series)
    alpha_obs, b_obs = spectral_slope(f_obs, psd_obs)

    # 1000 shuffle nulls (within-series permutation)
    shuffle_psds = np.empty((N_SHUFFLES, len(f_obs)))
    shuffle_alphas = np.empty(N_SHUFFLES)
    for i in range(N_SHUFFLES):
        _, psd_s = multitaper_psd(RNG.permutation(series))
        shuffle_psds[i] = psd_s
        shuffle_alphas[i], _ = spectral_slope(f_obs, psd_s)

    # AR(1) surrogate nulls
    ar1_psds = np.empty((200, len(f_obs)))    # 200 AR(1) is enough
    ar1_alphas = np.empty(200)
    for i in range(200):
        _, psd_a = multitaper_psd(ar1_surrogate(series, RNG))
        ar1_psds[i] = psd_a
        ar1_alphas[i], _ = spectral_slope(f_obs, psd_a)

    # Per-frequency p-value vs shuffle null (one-sided: obs > shuffle)
    p_shuffle = (shuffle_psds >= psd_obs[None, :]).mean(axis=0)
    # Bonferroni threshold: alpha / number of frequencies tested (skip f=0)
    n_tests = np.sum(f_obs > 0)
    bonf = 0.05 / n_tests
    sig_mask = (p_shuffle < bonf) & (f_obs > 0)
    n_sig = int(sig_mask.sum())

    # Peak-to-baseline ratio on the shuffled 95-pct envelope
    pct95 = np.percentile(shuffle_psds, 95, axis=0)
    ratio = psd_obs / np.where(pct95 > 0, pct95, np.inf)
    big_peaks = np.where(sig_mask & (ratio > 1.5))[0]

    print(f"  {name}: n={len(series)}, alpha_obs={alpha_obs:.3f}, "
          f"AR(1)-alpha mean={ar1_alphas.mean():.3f}, "
          f"sig bins={n_sig}/{n_tests}, big_peaks={len(big_peaks)}, "
          f"{time.time()-t:.1f}s")

    # Top 10 peaks (by ratio, restricted to significant)
    top_peaks = []
    if n_sig > 0:
        sig_idx = np.where(sig_mask)[0]
        sorted_by_ratio = sig_idx[np.argsort(-ratio[sig_idx])]
        for idx in sorted_by_ratio[:10]:
            top_peaks.append({
                "freq":       float(f_obs[idx]),
                "period":     float(1.0 / f_obs[idx]) if f_obs[idx] > 0 else None,
                "psd":        float(psd_obs[idx]),
                "shuffle_p95": float(pct95[idx]),
                "ratio":      float(ratio[idx]),
                "p_shuffle":  float(p_shuffle[idx]),
                "passes_bonferroni": bool(p_shuffle[idx] < bonf),
            })

    return {
        "n_points":             int(len(series)),
        "n_freq_bins":          int(len(f_obs)),
        "alpha_observed":       float(alpha_obs),
        "intercept_observed":   float(b_obs),
        "alpha_shuffle_mean":   float(shuffle_alphas.mean()),
        "alpha_shuffle_sd":     float(shuffle_alphas.std()),
        "alpha_ar1_mean":       float(ar1_alphas.mean()),
        "alpha_ar1_sd":         float(ar1_alphas.std()),
        "alpha_z_vs_shuffle":   float((alpha_obs - shuffle_alphas.mean()) /
                                     max(shuffle_alphas.std(), 1e-9)),
        "bonferroni_threshold": float(bonf),
        "n_sig_bins":           int(n_sig),
        "n_big_peaks":          int(len(big_peaks)),
        "top_peaks":            top_peaks,
        "_freqs":               f_obs.tolist(),
        "_psd_observed":        psd_obs.tolist(),
        "_psd_shuffle_p05":     np.percentile(shuffle_psds, 5, axis=0).tolist(),
        "_psd_shuffle_p95":     pct95.tolist(),
        "_psd_ar1_mean":        ar1_psds.mean(axis=0).tolist(),
    }

# ------------------------------------------------------------------ RUN
print("\nRunning spectral analysis on verse-length series ...")
res_vl = analyze(vl_aligned, "vl")
print("Running spectral analysis on end-letter series ...")
res_el = analyze(el_aligned, "el")

# ----- Per-surah spectral scan (verse-length only, surahs with n>=40) -----
print("\nPer-surah spectral scan (verse-length series, n_verses >= 40) ...")
per_surah = []
for s_idx, u in enumerate(quran_units):
    vl_s = np.asarray([len(v.split()) for v in u.verses], dtype=float)
    if len(vl_s) < 40:
        continue
    f_s, psd_s = multitaper_psd(vl_s)
    # Spectral slope
    alpha_s, _ = spectral_slope(f_s, psd_s)
    # Top peak
    m = f_s > 0
    top_idx = np.argmax(psd_s[m])
    per_surah.append({
        "surah":         s_idx + 1,
        "label":         u.label,
        "n_verses":      len(vl_s),
        "alpha":         alpha_s,
        "top_peak_freq": float(f_s[m][top_idx]),
        "top_peak_period": float(1.0 / f_s[m][top_idx]) if f_s[m][top_idx] > 0 else None,
        "top_peak_psd":  float(psd_s[m][top_idx]),
    })

top_peak_periods = [p["top_peak_period"] for p in per_surah if p["top_peak_period"] is not None]
print(f"  analysed {len(per_surah)} surahs; "
      f"median top-peak period={np.median(top_peak_periods):.2f} verses")

# ----------------------------------------------------------- DECISION
def verdict_for(res: dict) -> str:
    n_big = res["n_big_peaks"]
    n_sig = res["n_sig_bins"]
    if n_big >= 6:
        return "RHYTHMIC"
    if n_big >= 1 or n_sig >= 1:
        return "SUGGESTIVE"
    return "NULL_CHAOTIC_PERSISTENT"

v_vl = verdict_for(res_vl)
v_el = verdict_for(res_el)

# ----------------------------------------------------------- OUTPUTS
report = {
    "experiment_id":   "expE5_spectral_analysis",
    "task":            "E5",
    "tier":            2,
    "title":           "Fourier + multitaper spectral analysis on verse-length and end-letter series",
    "generated_utc":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed":            SEED,
    "n_shuffles":      N_SHUFFLES,
    "n_ar1_surrogates": 200,
    "multitaper":      {"NW": NW, "K": K_TAPERS, "taper_family": "DPSS"},
    "inputs": {
        "source": "results/checkpoints/phase_06_phi_m.pkl state['CORPORA']['quran']",
        "n_surahs": n_surahs,
        "n_verses_total": n_pts,
        "n_unique_end_letters": len(uniq_letters),
    },
    "verdicts": {
        "verse_length_series": v_vl,
        "end_letter_series":   v_el,
    },
    "results_verse_length": res_vl,
    "results_end_letter":   res_el,
    "per_surah_scan": {
        "n_surahs_analysed": len(per_surah),
        "min_n_verses": 40,
        "top_peak_period_median_verses": float(np.median(top_peak_periods)) if top_peak_periods else None,
        "top_peak_period_mean_verses":   float(np.mean(top_peak_periods)) if top_peak_periods else None,
        "per_surah": per_surah,
    },
    "notes": (
        "PSD computed via DPSS (K=7, NW=4) multitaper; shuffle null is 1000 within-series "
        "random permutations; AR(1) surrogate is Yule-Walker phi_1-matched. Bonferroni "
        "threshold = 0.05 / (n_freq_bins - 1). A 'big peak' additionally requires "
        "obs/shuffle_p95 > 1.5."
    ),
}

# Strip the bulky _* arrays from the compact JSON; save full arrays to .npz
compact = json.loads(json.dumps(report, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
for key in ("results_verse_length", "results_end_letter"):
    compact[key] = {k: v for k, v in compact[key].items() if not k.startswith("_")}
(OUTDIR / "expE5_report.json").write_text(json.dumps(compact, indent=2, ensure_ascii=False), encoding="utf-8")

np.savez_compressed(
    OUTDIR / "expE5_spectra.npz",
    f_vl=np.asarray(res_vl["_freqs"]),
    psd_vl=np.asarray(res_vl["_psd_observed"]),
    psd_vl_shuf_p05=np.asarray(res_vl["_psd_shuffle_p05"]),
    psd_vl_shuf_p95=np.asarray(res_vl["_psd_shuffle_p95"]),
    psd_vl_ar1_mean=np.asarray(res_vl["_psd_ar1_mean"]),
    f_el=np.asarray(res_el["_freqs"]),
    psd_el=np.asarray(res_el["_psd_observed"]),
    psd_el_shuf_p05=np.asarray(res_el["_psd_shuffle_p05"]),
    psd_el_shuf_p95=np.asarray(res_el["_psd_shuffle_p95"]),
    psd_el_ar1_mean=np.asarray(res_el["_psd_ar1_mean"]),
    vl=vl_aligned,
    el=el_aligned,
)

# ---- Plots ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

for series_name, res in [("verse_length", res_vl), ("end_letter", res_el)]:
    f = np.asarray(res["_freqs"])
    psd = np.asarray(res["_psd_observed"])
    p05 = np.asarray(res["_psd_shuffle_p05"])
    p95 = np.asarray(res["_psd_shuffle_p95"])
    ar1 = np.asarray(res["_psd_ar1_mean"])
    m = f > 0

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.fill_between(f[m], p05[m], p95[m], alpha=0.25, color="0.6",
                    label="shuffle null (5–95 pct)")
    ax.loglog(f[m], ar1[m], color="C1", lw=1.0, ls="--",
              label=f"AR(1) surrogate mean")
    ax.loglog(f[m], psd[m], color="C0", lw=1.0,
              label=f"observed (α={res['alpha_observed']:.2f})")
    for peak in res["top_peaks"][:5]:
        if peak["freq"] > 0:
            ax.axvline(peak["freq"], color="red", alpha=0.4, lw=0.6)
    ax.set_xlabel("frequency (cycles/verse)")
    ax.set_ylabel("power spectral density")
    ax.set_title(f"expE5 — multitaper PSD, {series_name} series ({res['n_points']} verses)\n"
                 f"sig bins (Bonferroni) = {res['n_sig_bins']}   big peaks = {res['n_big_peaks']}")
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTDIR / f"expE5_psd_{series_name}.png", dpi=150)
    plt.close(fig)

# ---- Markdown report ----
md = [
    f"# expE5 — Fourier + multitaper spectral analysis",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Shuffles**: {N_SHUFFLES}  |  **Multitaper**: DPSS K={K_TAPERS}, NW={NW}",
    f"**Input**: `results/checkpoints/phase_06_phi_m.pkl → state['CORPORA']['quran']` ({n_surahs} surahs, {n_pts} verses)",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: Shuffled PSD envelope indistinguishable from observed; series is 1/f^α persistent noise with no discrete rhythm.",
    "- **Pass**: ≥ 1 frequency bin survives Bonferroni shuffle null AND obs/shuffle_p95 > 1.5.",
    "- **RHYTHMIC** verdict if ≥ 6 such peaks; **SUGGESTIVE** if 1–5; **NULL_CHAOTIC_PERSISTENT** if 0.",
    "",
    "## Verdicts",
    "",
    "| Series | Verdict | α_obs | α_shuffle | α_AR(1) | sig bins / n_freq | big peaks |",
    "|---|---|---:|---:|---:|---:|---:|",
    f"| verse-length | **{v_vl}** | {res_vl['alpha_observed']:.3f} | "
    f"{res_vl['alpha_shuffle_mean']:.3f} ± {res_vl['alpha_shuffle_sd']:.3f} | "
    f"{res_vl['alpha_ar1_mean']:.3f} ± {res_vl['alpha_ar1_sd']:.3f} | "
    f"{res_vl['n_sig_bins']} / {res_vl['n_freq_bins']} | {res_vl['n_big_peaks']} |",
    f"| end-letter | **{v_el}** | {res_el['alpha_observed']:.3f} | "
    f"{res_el['alpha_shuffle_mean']:.3f} ± {res_el['alpha_shuffle_sd']:.3f} | "
    f"{res_el['alpha_ar1_mean']:.3f} ± {res_el['alpha_ar1_sd']:.3f} | "
    f"{res_el['n_sig_bins']} / {res_el['n_freq_bins']} | {res_el['n_big_peaks']} |",
    "",
]

for series_name, res in [("Verse-length", res_vl), ("End-letter", res_el)]:
    md.append(f"## {series_name} — top peaks")
    md.append("")
    if res["top_peaks"]:
        md.append("| # | Freq (1/verse) | Period (verses) | PSD | shuffle p95 | obs/p95 | p_shuffle | Bonferroni |")
        md.append("|--:|---:|---:|---:|---:|---:|---:|:--:|")
        for i, p in enumerate(res["top_peaks"], 1):
            md.append(
                f"| {i} | {p['freq']:.5f} | "
                f"{p['period']:.2f} | "
                f"{p['psd']:.3e} | {p['shuffle_p95']:.3e} | "
                f"{p['ratio']:.2f} | {p['p_shuffle']:.2e} | "
                f"{'✔' if p['passes_bonferroni'] else '—'} |"
            )
    else:
        md.append("_No peak survived the Bonferroni-corrected shuffle null._")
    md.append("")

md.append("## Per-surah scan (verse-length series, surahs with ≥ 40 verses)")
md.append("")
md.append(f"- **Surahs analysed**: {len(per_surah)}")
if top_peak_periods:
    md.append(f"- **Median top-peak period**: {np.median(top_peak_periods):.2f} verses")
    md.append(f"- **Mean top-peak period**: {np.mean(top_peak_periods):.2f} verses")
    md.append(f"- **Range**: {np.min(top_peak_periods):.2f}–{np.max(top_peak_periods):.2f} verses")
md.append("")
md.append("## Outputs")
md.append("")
md.append(f"- `expE5_report.json` — machine-readable summary")
md.append(f"- `expE5_spectra.npz` — full PSD arrays + shuffle envelopes + input series")
md.append(f"- `expE5_psd_verse_length.png` — PSD figure for verse-length series")
md.append(f"- `expE5_psd_end_letter.png` — PSD figure for end-letter series")

(OUTDIR / "expE5_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdicts: verse_length={v_vl}, end_letter={v_el}")
print(f"Outputs in {OUTDIR}")
print(f"Total runtime: {time.time()-t0:.1f}s")
