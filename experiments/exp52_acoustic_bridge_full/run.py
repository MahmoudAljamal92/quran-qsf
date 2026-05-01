"""
exp52_acoustic_bridge_full — main orchestrator.

Usage (PowerShell):

    python -X utf8 -m experiments.exp52_acoustic_bridge_full.run --surahs 1,103,108,112,114 --mode pilot
    python -X utf8 -m experiments.exp52_acoustic_bridge_full.run --all --mode full

What it does, end-to-end for each surah:

  1. Load MP3 (librosa via bundled ffmpeg) at 16 kHz mono.
  2. Build CTC alignment target: [taawudh?] + [basmalah?] + verses.
  3. Normalise target for the xlsr-53-arabic vocab; keep back-index to original.
  4. Run Wav2Vec2 CTC forced alignment -> per-character timestamps.
  5. Segment into per-verse audio windows from the char timestamps.
  6. Extract Praat acoustic features per verse (F0, HNR, intensity, spectral).
  7. Compute text features per verse (syllable, madd, emphatic, ghunnah).

Writes to results/experiments/exp52_acoustic_bridge_full/:
  <mode>_per_verse.csv, <mode>_per_letter.csv, <mode>_results.json,
  <mode>_fig_scatter.png, <mode>_fig_alignment.png
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---- stdlib + numerics
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# ---- project-local safe I/O (write-only under results/experiments/<exp>/)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments._lib import safe_output_dir  # noqa: E402

# ---- this experiment's helpers
from experiments.exp52_acoustic_bridge_full._text import (  # noqa: E402
    load_quran_vocal, text_features, normalize_for_ctc,
    build_alignment_target,
)
from experiments.exp52_acoustic_bridge_full._audio import (  # noqa: E402
    setup_ffmpeg, load_audio, extract_acoustic_features, CTCAligner, CharSegment,
)

EXP = "exp52_acoustic_bridge_full"

QURAN_VOCAL_PATH = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
AUDIO_DIR = Path(r"D:\القرآن الكريم\Mohammed_Siddiq_Al-Minshawi")
PILOT_SURAHS = [1, 103, 108, 112, 114]


# =========================================================================
# 1. Per-verse bookkeeping after CTC alignment
# =========================================================================
@dataclass
class VerseRecord:
    surah_no: int
    verse_no: int                 # >0 for real verses, -1 taawudh, 0 basmalah
    text: str                     # original Uthmani
    n_letters_aligned: int
    ctc_mean_score: float         # mean log-prob of this verse's aligned chars
    t_start: float                # global seconds from start of audio
    t_end: float
    # text features (narrow = for replication of archived V_Acoustic_02)
    char_count: int = 0
    word_count: int = 0
    syllable_count: int = 0
    madd_count: int = 0
    emphatic_count: int = 0
    ghunnah_count: int = 0
    # text features (full = phonologically richer variants)
    syllable_count_full: int = 0    # adds tanween
    madd_count_full: int = 0        # adds natural madds (alif-after-fatha etc.)
    emphatic_count_full: int = 0    # adds خ, غ
    # acoustic features
    Duration_s: float = 0.0
    Mean_Pitch_Hz: float = 0.0
    Pitch_Variance: float = 0.0
    Pitch_Range_Hz: float = 0.0
    Pitch_Voiced_Frames: int = 0
    Pitch_Total_Frames: int = 0
    Mean_Intensity_dB: float = 0.0
    HNR_dB: float = 0.0
    Mean_RMS: float = 0.0
    Spectral_Centroid_Hz: float = 0.0
    Spectral_Rolloff85_Hz: float = 0.0
    Silence_before_s: float = 0.0


@dataclass
class LetterRecord:
    surah_no: int
    verse_no: int
    pos_in_clean: int             # index within the verse's clean_text
    original_idx: int             # index within the verse's raw Uthmani string
    uthmani_char: str             # the original Uthmani letter (or diacritic cluster)
    vocab_char: str               # the CTC-vocab char
    start_s: float
    end_s: float                  # boundary-based (= next letter's start_s)
    fire_end_s: float             # CTC-firing end (peaky, 1-4 frames)
    duration_s: float             # end_s - start_s (articulation, incl. sustain)
    fire_duration_s: float        # fire_end_s - start_s (CTC-firing only)
    ctc_score: float
    is_emphatic: bool
    # tajweed annotations (boolean features on the aligned letter)
    has_shadda: bool              # followed by ّ in Uthmani
    has_small_alif_after: bool    # followed by ٰ (long ā)
    has_madd_sign_after: bool     # followed by ٓ (explicit madd)
    has_sukun: bool               # followed by ْ
    following_vowel: str          # 'fatha' | 'damma' | 'kasra' | 'tanween' | 'none'


# =========================================================================
# 2. Per-surah alignment + feature extraction
# =========================================================================
def align_and_score_surah(
    surah_no: int,
    verses: List[Tuple[int, str]],
    audio: np.ndarray,
    sr: int,
    aligner: CTCAligner,
) -> Tuple[List[VerseRecord], List[LetterRecord], Dict[str, Any]]:
    """Align audio against [preamble + verses], segment per-verse, extract features.

    Returns (verse_records, letter_records, diagnostics).
    """
    target = build_alignment_target(surah_no, verses)

    # --- 2a. Build one concatenated clean text + per-pseudo-verse bounds
    clean_parts: List[str] = []
    back_parts: List[List[int]] = []   # back_index per pseudo-verse
    bounds: List[Dict[str, Any]] = []  # clean_start / clean_end (inclusive/exclusive) in the FULL clean string
    cursor = 0
    for v_num, raw_text in target:
        clean_v, back_v = normalize_for_ctc(raw_text)
        bounds.append({
            "v_num": v_num,
            "raw": raw_text,
            "clean": clean_v,
            "back": back_v,
            "clean_start": cursor,
            "clean_end":   cursor + len(clean_v),
        })
        clean_parts.append(clean_v)
        back_parts.append(back_v)
        cursor += len(clean_v) + 1  # +1 for the space we will join with

    full_clean = " ".join(clean_parts)  # spaces become '|' via tokenizer
    audio_dur_s = len(audio) / sr

    # --- 2b. Forced alignment
    # For SHORT audio: single-pass against the full concatenated text.
    # For LONG audio: per-verse alignment with silence-based windows
    # (robust against CTC leaking text across verse boundaries).
    t0 = time.time()
    verse_segs: Dict[int, List[CharSegment]] = {i: [] for i in range(len(bounds))}
    if audio_dur_s <= aligner.max_seconds_single:
        # Single-pass: align everything at once, then bucket by verse
        segs = aligner.align(audio, full_clean)
        if segs is None:
            raise RuntimeError(
                f"[surah {surah_no}] forced alignment FAILED (too few frames?)")
        for seg in segs:
            for i, b in enumerate(bounds):
                if b["clean_start"] <= seg.idx < b["clean_end"]:
                    verse_segs[i].append(seg)
                    break
    else:
        # Per-verse alignment
        per_verse, _windows = aligner.align_per_verse(audio, clean_parts)
        for vi, vsegs in enumerate(per_verse):
            if vsegs is None:
                continue
            # Map LOCAL-to-verse idx to GLOBAL clean-string idx
            b = bounds[vi]
            for seg in vsegs:
                seg.idx = seg.idx + b["clean_start"]
                verse_segs[vi].append(seg)
    align_s = time.time() - t0

    # --- 2d. Build verse + letter records
    verse_records: List[VerseRecord] = []
    letter_records: List[LetterRecord] = []
    prev_t_end: Optional[float] = None
    sr_int = int(sr)
    for i, b in enumerate(bounds):
        char_segs = verse_segs[i]
        if not char_segs:
            # Verse had no audio; record zeros but keep the row for accounting.
            vr = VerseRecord(
                surah_no=surah_no, verse_no=b["v_num"], text=b["raw"],
                n_letters_aligned=0, ctc_mean_score=float("nan"),
                t_start=float("nan"), t_end=float("nan"),
                **text_features(b["raw"]),
            )
            verse_records.append(vr)
            continue

        t_start = min(s.start_s for s in char_segs)
        t_end   = max(s.end_s   for s in char_segs)

        # Acoustic features on the verse's audio window
        ac = extract_acoustic_features(audio, sr_int, t_start, t_end, prev_t_end=prev_t_end)
        vr = VerseRecord(
            surah_no=surah_no, verse_no=b["v_num"], text=b["raw"],
            n_letters_aligned=len(char_segs),
            ctc_mean_score=float(np.mean([s.score for s in char_segs])),
            t_start=t_start, t_end=t_end,
            **text_features(b["raw"]),
            **ac.to_dict(),
        )
        verse_records.append(vr)
        prev_t_end = t_end

        # Per-letter records
        for s in char_segs:
            pos_in_clean = s.idx - b["clean_start"]
            if pos_in_clean < 0 or pos_in_clean >= len(b["back"]):
                continue  # space between pseudo-verses — shouldn't happen after filter
            orig_idx = b["back"][pos_in_clean]
            raw = b["raw"]
            uthmani = raw[orig_idx] if orig_idx < len(raw) else "?"
            # Look-ahead in the ORIGINAL raw text for diacritic annotations
            after = raw[orig_idx + 1: orig_idx + 5]
            letter_records.append(LetterRecord(
                surah_no=surah_no, verse_no=b["v_num"],
                pos_in_clean=pos_in_clean, original_idx=orig_idx,
                uthmani_char=uthmani, vocab_char=s.char,
                start_s=s.start_s, end_s=s.end_s,
                fire_end_s=s.fire_end_s,
                duration_s=s.end_s - s.start_s,
                fire_duration_s=s.fire_end_s - s.start_s,
                ctc_score=s.score,
                is_emphatic=(uthmani in "\u0635\u0636\u0637\u0638\u0642"),
                has_shadda=("\u0651" in after[:2]),
                has_small_alif_after=("\u0670" in after),
                has_madd_sign_after=("\u0653" in after),
                has_sukun=("\u0652" in after[:2]),
                following_vowel=_detect_following_vowel(after),
            ))

    n_chars_aligned_total = sum(len(v) for v in verse_segs.values())
    diag = {
        "n_verses_total": len(bounds),
        "n_verses_aligned": sum(1 for v in verse_records if v.n_letters_aligned > 0),
        "n_chars_clean": len(full_clean),
        "n_chars_aligned": n_chars_aligned_total,
        "alignment_time_s": round(align_s, 2),
        "mode": "single-pass" if audio_dur_s <= aligner.max_seconds_single else "per-verse",
    }
    return verse_records, letter_records, diag


def _detect_following_vowel(after: str) -> str:
    for c in after[:3]:
        if c == "\u064E":
            return "fatha"
        if c == "\u064F":
            return "damma"
        if c == "\u0650":
            return "kasra"
        if c in "\u064B\u064C\u064D":
            return "tanween"
        if c == "\u0652":
            return "sukun"
    return "none"


# =========================================================================
# 3. Aggregate analysis + pre-registered hypothesis tests
# =========================================================================
def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    text_feats     = ["syllable_count", "syllable_count_full",
                      "madd_count",     "madd_count_full",
                      "word_count",     "char_count",
                      "emphatic_count", "emphatic_count_full",
                      "ghunnah_count"]
    acoustic_feats = ["Duration_s", "Mean_Pitch_Hz", "Pitch_Variance",
                      "Mean_Intensity_dB", "HNR_dB", "Spectral_Centroid_Hz"]
    rows = []
    for tf in text_feats:
        for af in acoustic_feats:
            x = df[tf].astype(float).values
            y = df[af].astype(float).values
            m = np.isfinite(x) & np.isfinite(y) & (y != 0)
            if m.sum() < 5:
                rows.append(dict(text=tf, acoustic=af, r=np.nan, p=np.nan,
                                 rho=np.nan, p_rho=np.nan, n=int(m.sum())))
                continue
            r, p = pearsonr(x[m], y[m])
            rho, p_rho = spearmanr(x[m], y[m])
            rows.append(dict(text=tf, acoustic=af,
                             r=float(r), p=float(p),
                             rho=float(rho), p_rho=float(p_rho),
                             n=int(m.sum())))
    return pd.DataFrame(rows)


def evaluate_hypotheses(df_verse: pd.DataFrame, df_letter: pd.DataFrame) -> Dict[str, Any]:
    """Return pre-registered H1–H6 verdicts with the actual numbers."""
    out: Dict[str, Any] = {}

    # H1: syllable -> mean pitch (pooled, REAL verses only)
    real = df_verse[(df_verse["verse_no"] > 0) & (df_verse["Mean_Pitch_Hz"] > 0)]
    x = real["syllable_count"].astype(float).values
    y = real["Mean_Pitch_Hz"].astype(float).values
    if len(x) >= 5:
        r, p = pearsonr(x, y)
        out["H1_syllable_pitch"] = dict(
            r=float(r), p=float(p), n=int(len(x)),
            threshold="r >= 0.30 and p < 1e-10",
            pass_=(r >= 0.30 and p < 1e-10),
        )
    else:
        out["H1_syllable_pitch"] = dict(r=None, p=None, n=int(len(x)), pass_=False)

    # H2: madd -> mean pitch
    if len(x) >= 5:
        xm = real["madd_count"].astype(float).values
        r, p = pearsonr(xm, y)
        out["H2_madd_pitch"] = dict(
            r=float(r), p=float(p), n=int(len(xm)),
            threshold="r >= 0.25 and p < 1e-5",
            pass_=(r >= 0.25 and p < 1e-5),
        )
    else:
        out["H2_madd_pitch"] = dict(r=None, p=None, n=0, pass_=False)

    # H3: verse-shuffle null (per surah)  — only meaningful with many surahs
    out["H3_shuffle_null"] = dict(note="deferred to full run (needs many surahs)")

    # H4: long-vowel (alif-like) duration vs short-vowel mark duration
    # Long vowels: aligned chars whose ORIGINAL Uthmani char is ا/ٰ/ٓ/ٱ/ى (all map to long-ā or long-ī sounds).
    # Short vowels: aligned fatha/kasra/damma marks that are NOT followed by an alif.
    if not df_letter.empty:
        long_vowel_chars = ["\u0627", "\u0670", "\u0653", "\u0671", "\u0649"]   # ا ٰ ٓ ٱ ى
        short_vowel_marks = ["\u064E", "\u064F", "\u0650"]                      # فَ ُ ِ
        madd = df_letter[df_letter["uthmani_char"].isin(long_vowel_chars)]
        short = df_letter[
            df_letter["vocab_char"].isin(short_vowel_marks)
            & (~df_letter["has_small_alif_after"])
            & (~df_letter["has_madd_sign_after"])
        ]
        d_madd = madd["duration_s"].values
        d_short = short["duration_s"].values
        if len(d_madd) >= 20 and len(d_short) >= 20:
            med_madd = float(np.median(d_madd))
            med_short = float(np.median(d_short))
            ratio = med_madd / med_short if med_short > 0 else np.nan
            # Bootstrap CI on the ratio
            rng = np.random.default_rng(42)
            ratios = []
            for _ in range(1000):
                r_madd = rng.choice(d_madd, size=len(d_madd), replace=True)
                r_short = rng.choice(d_short, size=len(d_short), replace=True)
                m_m = float(np.median(r_madd))
                m_s = float(np.median(r_short))
                if m_s > 0:
                    ratios.append(m_m / m_s)
            if ratios:
                lo, hi = np.percentile(ratios, [2.5, 97.5])
                out["H4_madd_duration"] = dict(
                    median_madd_s=med_madd, median_short_s=med_short,
                    ratio=float(ratio), ci95=[float(lo), float(hi)],
                    n_madd=int(len(d_madd)), n_short=int(len(d_short)),
                    threshold="ratio >= 1.8 and CI95 excludes 1.0",
                    pass_=(ratio >= 1.8 and lo > 1.0),
                )
            else:
                out["H4_madd_duration"] = dict(pass_=False, note="bootstrap empty")
        else:
            out["H4_madd_duration"] = dict(
                pass_=False,
                note=f"insufficient letters (madd={len(d_madd)}, short={len(d_short)})",
            )

    # H5: verse-final silence vs internal silence
    if len(real) >= 5:
        sil = real["Silence_before_s"].astype(float).values
        # Internal silences we can't easily isolate without word-level alignment.
        # For pilot: report mean/median + distribution.
        out["H5_fawasil_silence"] = dict(
            mean_silence_before_s=float(np.mean(sil)),
            median_silence_before_s=float(np.median(sil)),
            max_silence_before_s=float(np.max(sil)),
            n=int(len(sil)),
            note="full comparison to internal silence deferred (needs word-level align)",
            pass_=None,
        )

    # H6: emphatic vs non-emphatic letter duration
    if not df_letter.empty:
        emph = df_letter[df_letter["is_emphatic"]]["duration_s"].values
        # Non-emphatic pairs: ص-س, ط-ت, ظ-ذ, ض-د, ق-ك (the phonetically closest)
        non_emph = df_letter[df_letter["uthmani_char"].isin(list("\u0633\u062A\u0630\u062F\u0643"))]["duration_s"].values
        if len(emph) >= 20 and len(non_emph) >= 20:
            mean_e = float(np.mean(emph))
            mean_n = float(np.mean(non_emph))
            diff_ms = (mean_e - mean_n) * 1000.0
            # Welch's t-test
            from scipy.stats import ttest_ind
            t_stat, p_val = ttest_ind(emph, non_emph, equal_var=False)
            out["H6_emphatic_duration"] = dict(
                mean_emphatic_s=mean_e, mean_non_emphatic_s=mean_n,
                diff_ms=float(diff_ms), p=float(p_val),
                n_emphatic=int(len(emph)), n_non_emphatic=int(len(non_emph)),
                threshold="diff_ms >= 20 and p < 0.01",
                pass_=(diff_ms >= 20 and p_val < 0.01),
            )
        else:
            out["H6_emphatic_duration"] = dict(pass_=False, note="insufficient letters")

    return out


# =========================================================================
# 4. Figures
# =========================================================================
def make_figures(df: pd.DataFrame, out_dir: Path, tag: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    real = df[(df["verse_no"] > 0) & (df["Mean_Pitch_Hz"] > 0)].copy()
    if len(real) < 3:
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    for surah_no, sub in real.groupby("surah_no"):
        ax.scatter(sub["syllable_count"], sub["Mean_Pitch_Hz"],
                   label=f"Surah {surah_no:03d}", s=36, alpha=0.75,
                   edgecolors="white", linewidth=0.4)
    x = real["syllable_count"].astype(float).values
    y = real["Mean_Pitch_Hz"].astype(float).values
    r, p = pearsonr(x, y)
    m, b = np.polyfit(x, y, 1)
    xfit = np.linspace(x.min(), x.max(), 100)
    ax.plot(xfit, m * xfit + b, "k--", lw=1.3, alpha=0.7)
    ax.set_xlabel("Syllable count (text)")
    ax.set_ylabel("Mean F0 Hz (recitation)")
    sig = "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 5e-2 else "ns"
    ax.set_title(f"exp52 [{tag}] — syllable → mean pitch    r={r:.3f}  p={p:.2e}  {sig}   n={len(x)}")
    ax.legend(fontsize=8, loc="best")
    plt.tight_layout()
    fig.savefig(out_dir / f"{tag}_fig_scatter.png", dpi=150)
    plt.close(fig)


def make_alignment_strip(df_letter: pd.DataFrame, out_dir: Path, tag: str,
                          surah_no: int = 1) -> None:
    """Strip-plot of the first surah's letter-level alignment for visual QC."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sub = df_letter[df_letter["surah_no"] == surah_no].head(120)
    if len(sub) < 5:
        return
    fig, ax = plt.subplots(figsize=(14, 3))
    for _, row in sub.iterrows():
        color = "#d62728" if row["is_emphatic"] else "#1f77b4"
        ax.plot([row["start_s"], row["end_s"]], [0, 0], color=color, lw=6, solid_capstyle="butt")
    ax.set_xlabel("time (s)")
    ax.set_yticks([])
    ax.set_title(f"exp52 [{tag}] — surah {surah_no} letter alignment (red = emphatic)   "
                 f"n_letters={len(sub)}")
    plt.tight_layout()
    fig.savefig(out_dir / f"{tag}_fig_alignment.png", dpi=150)
    plt.close(fig)


# =========================================================================
# 5. Entry point
# =========================================================================
def _per_surah_paths(out_dir: Path, surah_no: int) -> Tuple[Path, Path, Path]:
    d = out_dir / "per_surah"
    d.mkdir(parents=True, exist_ok=True)
    return (d / f"{surah_no:03d}_verses.csv",
            d / f"{surah_no:03d}_letters.csv",
            d / f"{surah_no:03d}_diag.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surahs", type=str, default="",
                    help="comma-sep surah numbers (e.g. '1,103,108,112,114')")
    ap.add_argument("--all", action="store_true", help="process all 114 surahs")
    ap.add_argument("--mode", choices=["pilot", "full"], default="pilot")
    ap.add_argument("--no-fp16", action="store_true", help="force fp32 (slower, safer)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip surahs that already have per-surah CSVs on disk")
    ap.add_argument("--max-audio-s", type=float, default=3600.0,
                    help="hard ceiling: skip any surah whose audio exceeds this "
                         "(default 3600 s = 1 h; set 0 to disable)")
    ap.add_argument("--max-single-s", type=float, default=60.0,
                    help="max audio duration for single-pass CTC (default 60 s; "
                         "longer audio triggers per-verse alignment)")
    args = ap.parse_args()

    if args.all:
        surahs = list(range(1, 115))
    elif args.surahs:
        surahs = [int(s.strip()) for s in args.surahs.split(",") if s.strip()]
    else:
        surahs = PILOT_SURAHS

    out_dir = Path(safe_output_dir(EXP))
    print(f"[exp52] mode={args.mode}  surahs={len(surahs)}  out={out_dir}")
    print(f"[exp52] max_audio_s={args.max_audio_s}  max_single_s={args.max_single_s}  "
          f"skip_existing={args.skip_existing}")

    # --- 1. Load corpus
    setup_ffmpeg()
    corpus = load_quran_vocal(QURAN_VOCAL_PATH)
    print(f"[exp52] corpus: {len(corpus)} surahs, "
          f"{sum(len(v) for v in corpus.values())} verses")

    # --- 2. Load aligner (GPU)
    aligner = CTCAligner(
        model_name="jonatasgrosman/wav2vec2-large-xlsr-53-arabic",
        fp16=not args.no_fp16,
        max_seconds_single=args.max_single_s,
    )

    # --- 3. Iterate with per-surah persistence + crash isolation + resumability
    all_verses: List[VerseRecord] = []
    all_letters: List[LetterRecord] = []
    per_surah_diag: Dict[int, Dict[str, Any]] = {}
    t_global = time.time()

    # Progress estimator: use cumulative char count as the proxy for work.
    # Each surah's verses' clean-text length is a better proxy for alignment
    # cost than audio duration (which we only know after loading the MP3).
    total_chars_target = sum(
        sum(len(v[1]) for v in corpus.get(sn, [])) for sn in surahs)
    total_verses_target = sum(len(corpus.get(sn, [])) for sn in surahs)
    processed_chars = 0
    processed_verses = 0

    def _fmt_hms(s: float) -> str:
        s = int(max(0, s))
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{h}h{m:02d}m" if h else f"{m}m{sec:02d}s"

    for i, surah_no in enumerate(surahs, 1):
        verses = corpus.get(surah_no, [])
        surah_chars = sum(len(v[1]) for v in verses)
        if not verses:
            print(f"  [{i:>3}/{len(surahs)}] surah {surah_no}: no text found, skipping")
            continue
        audio_path = AUDIO_DIR / f"{surah_no:03d}.mp3"
        if not audio_path.exists():
            print(f"  [{i:>3}/{len(surahs)}] surah {surah_no}: missing audio {audio_path}")
            continue

        verses_csv, letters_csv, diag_json = _per_surah_paths(out_dir, surah_no)

        # Resumability
        if args.skip_existing and verses_csv.exists() and letters_csv.exists() and diag_json.exists():
            try:
                dfv = pd.read_csv(verses_csv)
                dfl = pd.read_csv(letters_csv)
                with open(diag_json, encoding="utf-8") as f:
                    diag = json.load(f)
                all_verses.extend(VerseRecord(**row) for _, row in dfv.iterrows())
                all_letters.extend(LetterRecord(**row) for _, row in dfl.iterrows())
                per_surah_diag[surah_no] = {**diag, "resumed_from_disk": True}
                processed_chars += surah_chars
                processed_verses += len(verses)
                pct = 100 * processed_chars / max(1, total_chars_target)
                elapsed = time.time() - t_global
                eta = elapsed * (total_chars_target - processed_chars) / max(1, processed_chars) \
                    if processed_chars > 0 else 0
                print(f"  [{i:>3}/{len(surahs)}] surah {surah_no:03d} — resumed from disk "
                      f"({len(dfv)} verses, {len(dfl)} letters)  "
                      f"| {pct:5.1f}%  elapsed {_fmt_hms(elapsed)}  ETA {_fmt_hms(eta)}")
                continue
            except Exception as e:
                print(f"  [{i:>3}/{len(surahs)}] surah {surah_no:03d}: resume failed "
                      f"({type(e).__name__}), re-processing")

        t_surah = time.time()
        print(f"  [{i:>3}/{len(surahs)}] surah {surah_no:03d} — "
              f"{len(verses)} verses, loading {audio_path.name} ...",
              end="", flush=True)
        try:
            y, sr = load_audio(str(audio_path), sr=16000)
            dur_s = len(y) / sr
            print(f" {dur_s:.1f}s audio", end="", flush=True)
            if args.max_audio_s > 0 and dur_s > args.max_audio_s:
                raise RuntimeError(
                    f"audio {dur_s:.1f}s exceeds --max-audio-s {args.max_audio_s:.0f}s")
            v_recs, l_recs, diag = align_and_score_surah(
                surah_no, verses, y, sr, aligner)
            all_verses.extend(v_recs)
            all_letters.extend(l_recs)
            wall_s = round(time.time() - t_surah, 2)
            rt_factor = dur_s / max(0.01, wall_s)
            per_surah_diag[surah_no] = {**diag, "wall_s": wall_s,
                                        "audio_s": round(dur_s, 2),
                                        "rt_factor": round(rt_factor, 1)}
            # Persist this surah's results so a later crash doesn't waste them
            pd.DataFrame([asdict(r) for r in v_recs]).to_csv(
                verses_csv, index=False, encoding="utf-8-sig")
            pd.DataFrame([asdict(r) for r in l_recs]).to_csv(
                letters_csv, index=False, encoding="utf-8-sig")
            with open(diag_json, "w", encoding="utf-8") as f:
                json.dump(per_surah_diag[surah_no], f, ensure_ascii=False, indent=2)
            processed_chars += surah_chars
            processed_verses += len(verses)
            pct = 100 * processed_chars / max(1, total_chars_target)
            elapsed = time.time() - t_global
            eta = elapsed * (total_chars_target - processed_chars) / max(1, processed_chars) \
                if processed_chars > 0 else 0
            print(f"  -> {diag['n_verses_aligned']}/{diag['n_verses_total']} verses, "
                  f"{diag['n_chars_aligned']} chars, {wall_s:.1f}s ({rt_factor:.1f}x RT, {diag.get('mode','?')})  "
                  f"| {pct:5.1f}%  elapsed {_fmt_hms(elapsed)}  ETA {_fmt_hms(eta)}")
        except Exception as e:
            processed_chars += surah_chars  # count toward progress even on failure
            processed_verses += len(verses)
            elapsed = time.time() - t_global
            pct = 100 * processed_chars / max(1, total_chars_target)
            eta = elapsed * (total_chars_target - processed_chars) / max(1, processed_chars) \
                if processed_chars > 0 else 0
            print(f"  FAILED: {type(e).__name__}: {e}  "
                  f"| {pct:5.1f}%  elapsed {_fmt_hms(elapsed)}  ETA {_fmt_hms(eta)}")
            per_surah_diag[surah_no] = {"error": f"{type(e).__name__}: {e}",
                                        "wall_s": round(time.time() - t_surah, 2)}
            # Persist the error so --skip-existing still skips it on retry
            with open(diag_json, "w", encoding="utf-8") as f:
                json.dump(per_surah_diag[surah_no], f, ensure_ascii=False, indent=2)
        finally:
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    total_wall = time.time() - t_global

    # --- 4. Assemble DataFrames + outputs
    df_verse = pd.DataFrame([asdict(r) for r in all_verses])
    df_letter = pd.DataFrame([asdict(r) for r in all_letters])

    tag = args.mode
    df_verse.to_csv(out_dir / f"{tag}_per_verse.csv", index=False, encoding="utf-8-sig")
    df_letter.to_csv(out_dir / f"{tag}_per_letter.csv", index=False, encoding="utf-8-sig")

    corr = compute_correlations(df_verse)
    corr.to_csv(out_dir / f"{tag}_correlations.csv", index=False, encoding="utf-8-sig")

    hyp = evaluate_hypotheses(df_verse, df_letter)

    make_figures(df_verse, out_dir, tag)
    make_alignment_strip(df_letter, out_dir, tag, surah_no=(surahs[0] if surahs else 1))

    # --- 5. JSON report
    real_n = int(((df_verse["verse_no"] > 0) & (df_verse["Mean_Pitch_Hz"] > 0)).sum())
    report = {
        "experiment": EXP,
        "mode": args.mode,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "surahs_requested": surahs,
        "surahs_processed": sorted(per_surah_diag.keys()),
        "n_verses_total": int(len(df_verse)),
        "n_verses_real_with_pitch": real_n,
        "n_letters_total": int(len(df_letter)),
        "wall_s_total": round(total_wall, 2),
        "per_surah_diagnostics": per_surah_diag,
        "hypotheses": hyp,
        "correlations_pooled": corr.round(6).to_dict(orient="records"),
        "settings": {
            "model": "jonatasgrosman/wav2vec2-large-xlsr-53-arabic",
            "fp16": not args.no_fp16,
            "sample_rate": 16000,
            "pitch_floor_hz": 75.0,
            "pitch_ceiling_hz": 500.0,
            "max_seconds_single_alignment": aligner.max_seconds_single,
            "ctc_frame_s": aligner.frame_s,
        },
    }
    def _json_default(o):
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            v = float(o)
            return v if np.isfinite(v) else None
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    with open(out_dir / f"{tag}_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=_json_default)

    # --- 6. Summary to stdout
    print()
    print("=" * 70)
    print(f"exp52 [{args.mode}] COMPLETE in {total_wall:.1f}s")
    print(f"  verses (real, with pitch): {real_n}")
    print(f"  letters aligned:           {len(df_letter)}")
    print(f"  outputs in: {out_dir}")
    print()
    if "H1_syllable_pitch" in hyp and hyp["H1_syllable_pitch"].get("r") is not None:
        h1 = hyp["H1_syllable_pitch"]
        print(f"  H1  syllable -> pitch : r={h1['r']:+.4f}  p={h1['p']:.2e}  "
              f"n={h1['n']}   {'PASS' if h1['pass_'] else 'FAIL'}")
    if "H2_madd_pitch" in hyp and hyp["H2_madd_pitch"].get("r") is not None:
        h2 = hyp["H2_madd_pitch"]
        print(f"  H2  madd     -> pitch : r={h2['r']:+.4f}  p={h2['p']:.2e}  "
              f"n={h2['n']}   {'PASS' if h2['pass_'] else 'FAIL'}")
    if "H4_madd_duration" in hyp:
        h4 = hyp["H4_madd_duration"]
        if "ratio" in h4:
            print(f"  H4  madd/short dur    : {h4['ratio']:.2f}x  CI95=[{h4['ci95'][0]:.2f},{h4['ci95'][1]:.2f}]   "
                  f"{'PASS' if h4.get('pass_') else 'FAIL'}")
    if "H6_emphatic_duration" in hyp:
        h6 = hyp["H6_emphatic_duration"]
        if "diff_ms" in h6:
            print(f"  H6  emph - non-emph   : {h6['diff_ms']:+.1f} ms  p={h6['p']:.2e}   "
                  f"{'PASS' if h6.get('pass_') else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
