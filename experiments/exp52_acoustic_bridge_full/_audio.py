"""
exp52 audio utilities.

1. setup_ffmpeg()                     add imageio-ffmpeg binary to PATH (Windows)
2. load_audio(path, sr=16000)         MP3 -> float32 ndarray (mono, target sr)
3. extract_acoustic_features()        Praat F0/intensity/HNR + librosa spectral
4. class CTCAligner                   Wav2Vec2 CTC forced alignment w/ chunking
"""
from __future__ import annotations

import os
import sys
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


# -------------------------------------------------------------------------
# FFmpeg shim (Windows-safe)
# -------------------------------------------------------------------------
def setup_ffmpeg() -> str:
    """Prepend imageio-ffmpeg's bundled binary dir to PATH so librosa/audioread
    can find `ffmpeg` without requiring a system install. Idempotent.
    """
    import imageio_ffmpeg as iff
    ffbin = iff.get_ffmpeg_exe()
    ffdir = os.path.dirname(ffbin)
    current = os.environ.get("PATH", "")
    if ffdir not in current.split(os.pathsep):
        os.environ["PATH"] = ffdir + os.pathsep + current
    return ffbin


# -------------------------------------------------------------------------
# MP3 loader
# -------------------------------------------------------------------------
def load_audio(path: str, sr: int = 16000) -> Tuple[np.ndarray, int]:
    """Load any audio file (MP3/WAV/FLAC/OGG) at target sample-rate, mono.
    Returns (samples float32 in [-1, 1], sr).
    """
    setup_ffmpeg()
    import librosa
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # noisy UserWarning from audioread
        y, out_sr = librosa.load(path, sr=sr, mono=True)
    return y.astype(np.float32), int(out_sr)


# -------------------------------------------------------------------------
# Praat-based acoustic features
# -------------------------------------------------------------------------
@dataclass
class AcousticFeatures:
    Duration_s: float
    Mean_Pitch_Hz: float
    Pitch_Variance: float
    Pitch_Range_Hz: float
    Pitch_Voiced_Frames: int
    Pitch_Total_Frames: int
    Mean_Intensity_dB: float
    HNR_dB: float
    Mean_RMS: float
    Spectral_Centroid_Hz: float
    Spectral_Rolloff85_Hz: float
    Silence_before_s: float

    def to_dict(self) -> Dict[str, float]:
        return {k: float(getattr(self, k)) for k in self.__dataclass_fields__}


def extract_acoustic_features(
    y_full: np.ndarray,
    sr: int,
    t_start: float,
    t_end: float,
    prev_t_end: Optional[float] = None,
    pitch_floor: float = 75.0,
    pitch_ceiling: float = 500.0,
) -> AcousticFeatures:
    """
    Extract all acoustic features for the segment [t_start, t_end] of y_full.
    Silently returns zeros on too-short / silent / errored segments.
    """
    import parselmouth as pm
    import librosa as lb

    n0, n1 = int(t_start * sr), int(t_end * sr)
    n1 = min(n1, len(y_full))
    n0 = max(0, n0)
    y_seg = y_full[n0:n1]

    dur = (n1 - n0) / sr
    if len(y_seg) < int(sr * 0.05):  # < 50 ms
        return AcousticFeatures(
            Duration_s=dur, Mean_Pitch_Hz=0.0, Pitch_Variance=0.0, Pitch_Range_Hz=0.0,
            Pitch_Voiced_Frames=0, Pitch_Total_Frames=0, Mean_Intensity_dB=0.0,
            HNR_dB=0.0, Mean_RMS=0.0, Spectral_Centroid_Hz=0.0,
            Spectral_Rolloff85_Hz=0.0,
            Silence_before_s=(t_start - prev_t_end) if prev_t_end is not None else 0.0,
        )

    y64 = y_seg.astype(np.float64)
    snd = pm.Sound(y64, sampling_frequency=sr)

    # --- F0 via Praat autocorrelation
    mean_f0 = var_f0 = rng_f0 = 0.0
    n_voiced = n_total = 0
    try:
        pitch = snd.to_pitch_ac(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
        f0 = pitch.selected_array["frequency"]
        n_total = int(len(f0))
        voiced = f0[f0 > 0]
        n_voiced = int(len(voiced))
        if n_voiced > 0:
            mean_f0 = float(np.mean(voiced))
            var_f0  = float(np.std(voiced))
            rng_f0  = float(np.max(voiced) - np.min(voiced))
    except Exception:
        pass

    # --- Intensity
    mean_int = 0.0
    try:
        intensity = snd.to_intensity(minimum_pitch=pitch_floor)
        vals = intensity.values.flatten()
        vals = vals[np.isfinite(vals)]
        if len(vals) > 0:
            mean_int = float(np.mean(vals))
    except Exception:
        pass

    # --- HNR
    mean_hnr = 0.0
    try:
        hnr = snd.to_harmonicity_cc(minimum_pitch=pitch_floor)
        hnr_vals = hnr.values.flatten()
        hnr_vals = hnr_vals[(hnr_vals > -100) & np.isfinite(hnr_vals)]
        if len(hnr_vals) > 0:
            mean_hnr = float(np.mean(hnr_vals))
    except Exception:
        pass

    # --- Librosa spectral
    try:
        n_fft = min(2048, max(512, 1 << (int(np.log2(len(y_seg)))))) if len(y_seg) > 512 else 512
        S = np.abs(lb.stft(y_seg, n_fft=n_fft, hop_length=n_fft // 4))
        cent = lb.feature.spectral_centroid(S=S, sr=sr, n_fft=n_fft)
        rolloff = lb.feature.spectral_rolloff(S=S, sr=sr, n_fft=n_fft, roll_percent=0.85)
        spec_centroid = float(np.mean(cent)) if cent.size else 0.0
        spec_rolloff = float(np.mean(rolloff)) if rolloff.size else 0.0
    except Exception:
        spec_centroid = spec_rolloff = 0.0

    rms = float(np.sqrt(np.mean(y_seg ** 2))) if len(y_seg) > 0 else 0.0
    sil_before = (t_start - prev_t_end) if prev_t_end is not None else 0.0
    sil_before = float(max(0.0, sil_before))

    return AcousticFeatures(
        Duration_s=dur,
        Mean_Pitch_Hz=mean_f0,
        Pitch_Variance=var_f0,
        Pitch_Range_Hz=rng_f0,
        Pitch_Voiced_Frames=n_voiced,
        Pitch_Total_Frames=n_total,
        Mean_Intensity_dB=mean_int,
        HNR_dB=mean_hnr,
        Mean_RMS=rms,
        Spectral_Centroid_Hz=spec_centroid,
        Spectral_Rolloff85_Hz=spec_rolloff,
        Silence_before_s=sil_before,
    )


# -------------------------------------------------------------------------
# CTC forced alignment
# -------------------------------------------------------------------------
@dataclass
class CharSegment:
    """A single aligned character (token in the CTC vocab, NOT in the original
    Uthmani string — use _text.normalize_for_ctc back_index to map back).

    Two duration views:
      * [start_s, end_s]      : BOUNDARY-BASED span — start of this char to
                                 start of the next char. This is the
                                 articulation duration (includes blank frames
                                 between chars, which belong to this char's
                                 acoustic sustain). Use for tajweed analysis.
      * [start_s, fire_end_s] : FIRING-ONLY span — frames where CTC actually
                                 emitted this token. Use for alignment QC
                                 (very short = peaky, typical ~20-80 ms).
    """
    idx: int          # position in the normalised target string
    token_id: int
    char: str
    start_s: float
    end_s: float
    fire_end_s: float  # when CTC stopped emitting this token
    score: float       # mean log-prob over the firing frames


class CTCAligner:
    """Wraps a HuggingFace Wav2Vec2 CTC model for Arabic forced alignment.

    Single-pass alignment is used for audio <= `max_seconds_single` (default 30 s).
    Longer audio is processed in overlapping 30 s windows; the alignments of each
    window's central portion are stitched.
    """

    def __init__(
        self,
        model_name: str = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic",
        device: Optional[str] = None,
        fp16: bool = True,
        max_seconds_single: float = 60.0,
    ):
        import torch
        from transformers import AutoProcessor, AutoModelForCTC

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.fp16 = fp16 and self.device.startswith("cuda")

        self.processor = AutoProcessor.from_pretrained(model_name)
        mdl = AutoModelForCTC.from_pretrained(model_name).to(self.device)
        if self.fp16:
            mdl = mdl.half()
        mdl.eval()
        self.model = mdl

        self.tokenizer = self.processor.tokenizer
        self.vocab = self.tokenizer.get_vocab()
        self.blank_id = int(self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else 0)
        self.id_to_tok = {i: t for t, i in self.vocab.items()}

        # Wav2Vec2 conv stack stride at 16kHz = 20ms per output frame
        self.frame_s = 0.02
        self.sr = 16000
        self.max_seconds_single = max_seconds_single

        # Quick vocab diagnostic
        print(f"[CTCAligner] model={model_name}  device={self.device}  fp16={self.fp16}  "
              f"vocab_size={len(self.vocab)}  blank_id={self.blank_id}", file=sys.stderr)

    # --------------------------------------------------------------
    def _encode_text(self, text: str):
        """Manually map chars to token IDs (skip OOV, spaces -> '|').
        Returns (torch.LongTensor target_ids, list[str] target_chars).
        """
        import torch
        ids: List[int] = []
        chars: List[str] = []
        for c in text:
            if c == " ":
                c = "|"
            if c in self.vocab:
                ids.append(self.vocab[c])
                chars.append(c)
            # Silently skip anything else (caller should have normalised).
        return torch.tensor(ids, dtype=torch.long), chars

    # --------------------------------------------------------------
    def _emissions(self, audio_chunk: np.ndarray):
        """Run the CTC head over one audio chunk. Returns (T, V) float32 log-probs on GPU."""
        import torch
        inp = self.processor(audio_chunk, sampling_rate=self.sr,
                             return_tensors="pt").input_values.to(self.device)
        if self.fp16:
            inp = inp.half()
        with torch.no_grad():
            logits = self.model(inp).logits  # (1, T, V)
        log_probs = torch.log_softmax(logits.float(), dim=-1).squeeze(0)  # (T, V)
        return log_probs

    # --------------------------------------------------------------
    def _forced_align_single(self, emissions, target_ids):
        """emissions: (T, V), target_ids: (L,). Returns list[CharSegment]
        in the same order as target_ids, with time stamps in SECONDS."""
        import torch
        import torchaudio.functional as taf

        T, V = emissions.shape
        L = int(target_ids.numel())
        if L == 0 or T < L:
            return None  # impossible

        aln, scores = taf.forced_align(
            emissions.unsqueeze(0),
            target_ids.unsqueeze(0).to(emissions.device).int(),
            blank=self.blank_id,
        )
        aln = aln.squeeze(0).cpu().numpy()
        scores = scores.squeeze(0).cpu().numpy()

        # Collapse repeats into per-target-char time spans.
        segs: List[CharSegment] = []
        i = 0
        target_idx = 0
        # aln has length T; non-blank runs correspond to target positions in order.
        while i < T and target_idx < L:
            if aln[i] == self.blank_id:
                i += 1
                continue
            # We expect aln[i] == tgt_ids_list[target_idx] (guaranteed by CTC)
            j = i
            run_score = 0.0
            n_run = 0
            while j < T and aln[j] == aln[i]:
                run_score += scores[j]
                n_run += 1
                j += 1
            tok_id = int(aln[i])
            segs.append(CharSegment(
                idx=target_idx,
                token_id=tok_id,
                char=self.id_to_tok.get(tok_id, "?"),
                start_s=i * self.frame_s,
                end_s=j * self.frame_s,        # placeholder, replaced below
                fire_end_s=j * self.frame_s,   # CTC-firing end (peaky)
                score=run_score / max(n_run, 1),
            ))
            target_idx += 1
            i = j
        if len(segs) != L:
            # This should not happen if forced_align succeeded.
            return None

        # end_s == fire_end_s here (CTC firing end); the caller applies a
        # global boundary + sustain cap via _apply_boundary_and_cap().
        return segs

    # --------------------------------------------------------------
    def align(self, audio: np.ndarray, clean_text: str
              ) -> Optional[List[CharSegment]]:
        """Single-pass alignment of `clean_text` against `audio`.

        Use this ONLY when the audio is short enough to fit in a single CTC
        emission pass (<= max_seconds_single). For longer audio, the caller
        must split text into per-verse slices and use `align_per_verse`; a
        single-pass alignment across many verses stretches text into verse
        silences (see RUNBOOK).
        """
        target_ids, _ = self._encode_text(clean_text)
        if target_ids.numel() == 0:
            return None

        dur = len(audio) / self.sr
        if dur > self.max_seconds_single:
            raise ValueError(
                f"align() called with {dur:.1f}s audio, exceeding "
                f"max_seconds_single={self.max_seconds_single}s. Use "
                f"align_per_verse() for long-audio surahs.")
        emissions = self._emissions(audio)
        segs = self._forced_align_single(emissions, target_ids)
        if segs is None:
            return None
        return self._apply_boundary_and_cap(segs, dur)

    # --------------------------------------------------------------
    @staticmethod
    def _apply_boundary_and_cap(segs: List[CharSegment], audio_dur_s: float,
                                sustain_cap_s: float = 2.0
                                ) -> List[CharSegment]:
        """Global boundary-based end_s with a sustain cap.

        end_s[k] = min(start_s[k+1], fire_end_s[k] + sustain_cap_s).
        No Arabic letter sustains longer than ~2 s (a 6-count madd fills
        ~1.2 s max). Without the cap, chunk boundaries or trailing silences
        would inflate the last letter's apparent duration.
        """
        segs = sorted(segs, key=lambda s: s.idx)
        for k in range(len(segs) - 1):
            next_start = segs[k + 1].start_s
            if next_start <= segs[k].start_s:
                next_start = segs[k].fire_end_s
            max_end = segs[k].fire_end_s + sustain_cap_s
            segs[k].end_s = max(segs[k].start_s, min(next_start, max_end))
        if segs:
            last = segs[-1]
            last.end_s = min(last.fire_end_s + sustain_cap_s, audio_dur_s)
        return segs

    # --------------------------------------------------------------
    def align_per_verse(self,
                        audio: np.ndarray,
                        verse_clean_texts: List[str],
                        ) -> Tuple[List[Optional[List[CharSegment]]], List[Tuple[float, float]]]:
        """
        Verse-by-verse CTC alignment for long audio.

        Uses silence-based segmentation to find per-verse audio windows, then
        aligns each verse's clean text against just its window independently.
        This avoids the cross-verse text leakage that plagues chunked alignment
        for Murattal recitations, at the cost of an extra librosa pass.

        Parameters
        ----------
        audio              : (N,) float32 at self.sr
        verse_clean_texts  : list of clean verse strings (preamble first if any)

        Returns
        -------
        per_verse_segs  : list[list[CharSegment]|None]
                          segments with GLOBAL timestamps, idx LOCAL to each
                          verse's clean text (0..L_i-1). run.py re-maps to
                          global clean-text indices.
        per_verse_windows : list[(t_start, t_end)]
                            the audio window used per verse, in seconds.
        """
        import librosa
        import torch

        n_v = len(verse_clean_texts)
        if n_v == 0:
            return [], []
        verse_char_counts = [
            sum(1 for c in vt if c == " " or c in self.vocab)
            for vt in verse_clean_texts
        ]

        # 1) Detect non-silent regions surah-wide
        try:
            raw_regions = librosa.effects.split(
                audio, top_db=25, frame_length=2048, hop_length=512)
        except Exception:
            raw_regions = np.empty((0, 2), dtype=int)
        regions = [(int(s), int(e)) for s, e in raw_regions
                   if (e - s) >= int(0.1 * self.sr)]
        if not regions:
            print("[CTCAligner] no speech regions found!", file=sys.stderr)
            return [None] * n_v, [(0.0, 0.0)] * n_v

        # 2) Strict linear char-position -> sample-position map.
        # For each char-count c in [0, total_chars], time_at_char(c) walks the
        # regions (speech only) and returns the global sample index whose
        # CUMULATIVE speech sample count equals c / chars_per_sample.
        # Verse boundaries are then at cum_chars[0], cum_chars[1], ...
        # This guarantees:
        #   (a) each verse gets speech proportional to its char count,
        #   (b) no accumulating drift near the tail of long surahs,
        #   (c) every verse gets a NON-EMPTY window (unless chars=0).
        total_speech_samples = sum(e - s for s, e in regions)
        total_chars = sum(verse_char_counts)
        if total_chars == 0 or total_speech_samples == 0:
            return [None] * n_v, [(0.0, 0.0)] * n_v
        samples_per_char = total_speech_samples / total_chars

        def sample_at_char(char_pos: float) -> int:
            """Sample index whose cumulative speech-sample count == char_pos × samples_per_char."""
            target_speech = char_pos * samples_per_char
            cum = 0
            for (rs, re) in regions:
                L = re - rs
                if cum + L >= target_speech:
                    return rs + int(target_speech - cum)
                cum += L
            # Exhausted regions: return end of last region
            return regions[-1][1]

        cum_chars = [0]
        for cc in verse_char_counts:
            cum_chars.append(cum_chars[-1] + cc)
        verse_boundaries = [sample_at_char(c) for c in cum_chars]

        # Snap boundaries to the NEAREST region edge if within 0.25 s — this
        # keeps verse ends aligned with silences when the reciter's pace
        # matches our estimate closely (common for Murattal), without causing
        # the drift that the previous per-verse snap did.
        region_edges = sorted(set([rs for rs, _ in regions] + [re for _, re in regions]))
        region_edges_arr = np.array(region_edges)
        snap_tol = int(0.25 * self.sr)
        for i in range(1, len(verse_boundaries) - 1):  # don't snap first/last
            b = verse_boundaries[i]
            # nearest region edge
            j = int(np.argmin(np.abs(region_edges_arr - b)))
            if abs(region_edges_arr[j] - b) <= snap_tol:
                verse_boundaries[i] = int(region_edges_arr[j])

        # Ensure strictly monotonic (edge-case: identical boundaries)
        for i in range(1, len(verse_boundaries)):
            if verse_boundaries[i] <= verse_boundaries[i - 1]:
                verse_boundaries[i] = verse_boundaries[i - 1] + int(0.05 * self.sr)

        verse_windows: List[Tuple[float, float]] = [
            (verse_boundaries[i] / self.sr, verse_boundaries[i + 1] / self.sr)
            for i in range(n_v)
        ]

        # 3) Align each verse against its audio window
        per_verse_segs: List[Optional[List[CharSegment]]] = []
        for vi, (t0, t1) in enumerate(verse_windows):
            if t1 - t0 < 0.1:
                per_verse_segs.append(None)
                continue
            # Add a small audio padding (100 ms) on each side to catch
            # the start / end of the verse that might have been clipped
            pad_s = 0.1
            s0 = max(0, int((t0 - pad_s) * self.sr))
            s1 = min(len(audio), int((t1 + pad_s) * self.sr))
            window = audio[s0:s1]
            vt = verse_clean_texts[vi]
            vt_ids, _ = self._encode_text(vt)
            if vt_ids.numel() == 0:
                per_verse_segs.append(None)
                continue
            try:
                emi = self._emissions(window)
                vsegs = self._forced_align_single(emi, vt_ids)
            except (RuntimeError,) as e:  # CUDA OOM etc.
                print(f"[CTCAligner] verse {vi} align failed: {type(e).__name__}: {e}",
                      file=sys.stderr)
                per_verse_segs.append(None)
                torch.cuda.empty_cache()
                continue
            if vsegs is None:
                per_verse_segs.append(None)
                continue
            # Shift timestamps to global audio time
            off_s = s0 / self.sr
            for seg in vsegs:
                seg.start_s += off_s
                seg.end_s += off_s
                seg.fire_end_s += off_s
            # Apply sustain cap WITHIN this verse
            self._apply_boundary_and_cap(vsegs, audio_dur_s=t1 + pad_s)
            per_verse_segs.append(vsegs)
            del emi
            torch.cuda.empty_cache()

        return per_verse_segs, verse_windows
