# exp46 — Context of the 16 no-E7 detections (B13)

**Source**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp46_emphatic_substitution\exp46_emphatic_substitution.json`
**Generated**: 2026-04-24 (pending full B14 re-run for per-edit contexts)

## Class-level summary (already in JSON)

| Class | Pair | n edits | n detected | det. rate | max\|z\| mean |
|---|---|--:|--:|--:|--:|
| E1_sad_sin  | ص ↔ س | 662   | 5 | 0.8 % | 0.78 |
| E2_dad_dal  | ض ↔ د | 553   | 3 | 0.5 % | 0.78 |
| E3_tta_ta   | ط ↔ ت | 848   | 0 | 0.0 % | 0.67 |
| E4_dha_dhal | ظ ↔ ذ | 476   | 2 | 0.4 % | 0.70 |
| E5_qaf_kaf  | ق ↔ ك | 1211  | 0 | 0.0 % | 0.67 |
| E6_hha_ha   | ح ↔ ه | 1663  | 6 | 0.4 % | 0.76 |
| **Σ no-E7** | — | **5,413** | **16** | **0.296 %** | — |
| E7_ayn_alef | ع ↔ ا | 5,048 | 104 | 2.06 % | 1.24 |

## Immediate conclusions

1. **E3 (ط↔ت) and E5 (ق↔ك) are detection-proof at this sample size**. Zero detections out of 2,059 edits combined. Both involve pairs that share a single-rasm skeleton (ط/ت differ only by one dot; ق/ك differ only by the hamza-marker on kaf). Under `normalize_rasm()` the rasm/dots are preserved but the pairs remain orthographically very similar. The detector is structurally blind to these.

2. **E1 (ص↔س) has the highest no-E7 rate (0.8 %)**. The emphatic ص vs. plain س differ by a single dot plus the closed-vs-open bottom loop — the largest orthographic distance among the remaining pairs. Consistent with the intuition that "more visual distance → easier to detect".

3. **E6 (ح↔ه) accounts for 6/16 detections (38 %)** despite only being 30.7 % of no-E7 edits. Highest relative detection share after E1.

4. **Max-|z| means are all below 1.0 for E1-E6** (0.67–0.78), whereas E7's mean is **1.24** — confirming E7 dominates *not only* the denominator but the z-score distribution. The no-E7 detector is operating near the noise floor.

## What's NOT available in the JSON

The canonical `per_class_summary.example_variants` field carries only **5 sample edits per class**, none of which are guaranteed to be from the detected subset. The per-surah records (`per_surah_results`) aggregate all classes together (E1–E7 mixed), so per-surah no-E7 detection counts are not recoverable from the published JSON either.

**To characterise the 16 individual detections** (surah, verse, char position, ±N-gram context) a patched exp46 run that saves a `detected_edits_no_e7_contexts` auxiliary field is required. Plan folded into the **B14** patch (see below).

## B14 plan (pending rebuild completion)

When exp46 is re-run with the hamza-preserving detector, add a diagnostic-only list of detected no-E7 edits in the JSON under a new key:

```json
"audit_2026_04_24_b13_noe7_contexts": {
  "edits": [
    {"class": "E1_sad_sin", "surah": "Q:...", "verse_idx": N,
     "pos": N, "orig": "ص", "partner": "س",
     "context_left_4":  "…4 chars before…",
     "context_right_4": "…4 chars after…",
     "word":            "…enclosing word…",
     "n_channels_fired": N,
     "z_scores": {"A_spectral": …, …}},
    …
  ]
}
```

This keeps the published headline numerics unchanged while adding the per-edit diagnostics B13 asks for.

## Interim verdict

The 16 no-E7 detections, combined with max-|z| means well below 1.0, strongly suggest the no-E7 emphatic-substitution detection is **noise-level** on the Quran: ~0.3 % detection rate is within the 1-%-per-class chance floor implied by the 9-channel / 3-of-9 fire rule. Any published claim that the Quran "selectively detects emphatic swaps" should be read as **"the Quran has the lowest emphatic detection rate among Arabic corpora, consistent with structural indistinguishability from null"** — not as positive detection.

*End of B13 preliminary note. Final version will be appended after B14 re-run.*
