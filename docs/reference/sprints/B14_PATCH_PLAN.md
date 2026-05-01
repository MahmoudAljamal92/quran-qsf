# B14 + B13 exp46 patch plan (to apply post-rebuild)

**Status**: draft. Will be applied after the rebuild (in flight since 17:09) finishes so `_ultimate2_helpers.py` can be safely edited without risk of mid-build hash drift.

## Scope

Single patched run of `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py` that delivers both:

- **B14**: 3-way E7 sub-class breakdown using a new hamza-preserving normalizer — `ع ↔ ا` (bare), `ع ↔ أ إ` (hamza-bearing), `ع ↔ آ` (madda).
- **B13**: per-edit context capture for the 16 no-E7 detections (surah label, verse index, char position, ±4-char context, firing channels, full 9-channel z-scores).

Both land as NEW audit-block keys in the JSON; the canonical published fields (`overall_detection_rate`, `per_class_summary`, etc.) are untouched.

## Patch 1 — `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py`

Add a new fold map and wrapper, immediately after `_FOLD_MAP_STRICT` / `normalize_rasm_strict`:

```python
# Hamza-preserving map (audit 2026-04-24, B14): folds NOTHING for alef.
# Keeps every alef variant (ا أ إ آ ٱ) mutually distinct so the exp46 E7
# confound can be split into phonologically-separate sub-classes.
_FOLD_MAP_HAMZA_PRESERVING: dict[str, str] = {}


def normalize_rasm_hamza_preserving(text: str) -> str:
    """Hamza-preserving normaliser (audit 2026-04-24, B14).

    Strips diacritics + tatweel ONLY. Folds no alef variants — keeps
    ا / أ / إ / آ / ٱ mutually distinct. Used by exp46 for the
    B14 3-way E7 sub-class breakdown:
        E7a_ayn_bare_alef   ع ↔ ا
        E7b_ayn_hamza_alef  ع ↔ أ / إ
        E7c_ayn_madda       ع ↔ آ
    """
    return _normalize_with(text, _FOLD_MAP_HAMZA_PRESERVING)
```

## Patch 2 — `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py`

### Imports
Add `normalize_rasm_hamza_preserving` to the existing `_ultimate2_helpers` import block.

### Data capture during main loop
In the detection loop (`for vi, abs_pos, orig_ch, partner, cls_name in all_emp:`), when `detected` is True and `cls_name` is in E1..E6, append to a new module-level list `detected_noe7`:

```python
if detected and cls_name not in E7_CONFOUNDED_CLASSES:
    v = verse
    detected_noe7.append({
        "class":       cls_name,
        "pair":        f"{orig_ch}↔{partner}",
        "surah":       getattr(u, "label", f"unit_{u_idx}"),
        "verse_idx":   vi,
        "pos":         abs_pos,
        "orig":        orig_ch,
        "partner":     partner,
        "context_left_4":  v[max(0, abs_pos-4): abs_pos],
        "context_right_4": v[abs_pos+1: abs_pos+5],
        "n_channels_fired": n_fired,
        "z_scores": {k: round(x, 3) for k, x in zscores.items()},
    })
```

### Post-loop B14 sub-experiment

After the E1-E7 main loop completes, run an additional E7-only sub-experiment using `normalize_rasm_hamza_preserving` as the base normalizer and partition edits by source char:

```python
# --- B14 3-way E7 sub-experiment (hamza-preserving normalizer) ---
print(f"[{EXP}] B14: running 3-way E7 sub-experiment with hamza-preserving normaliser...")
b14_subclasses = {
    "E7a_ayn_bare_alef":  {"pair": "ع↔ا",      "src_chars": {"ا"}},
    "E7b_ayn_hamza_alef": {"pair": "ع↔أ/إ",    "src_chars": {"أ", "إ"}},
    "E7c_ayn_madda":      {"pair": "ع↔آ",      "src_chars": {"آ"}},
}
# Re-build null distributions under the new normalizer (~40 surahs × 20 swaps)
null_deltas_hp = _build_null_distributions_hp(  # helper that uses normalize_rasm_hamza_preserving
    quran_units, ref_bi, root_lm, rng,
    n_surahs=n_null_surahs, n_null_per_surah=n_null_per)

b14_results = {cls: {"n_edits": 0, "n_detected": 0, "z_all": []} for cls in b14_subclasses}

for u in test_units:
    vs = extract_verses(u)
    if len(vs) < 2: continue
    hp_vs = [normalize_rasm_hamza_preserving(v) for v in vs]
    canon_text = " ".join(hp_vs)
    canon_feats = nine_channel_features(hp_vs, ref_bi, root_lm, canonical_text=canon_text)
    # Find ayn positions
    for vi, verse in enumerate(hp_vs):
        for abs_pos, ch in enumerate(verse):
            if ch != "ع": continue
            # Pick a random hamza-variant partner for each ayn position and test ع→partner
            for partner, cls_name in [
                ("ا",  "E7a_ayn_bare_alef"),
                ("أ",  "E7b_ayn_hamza_alef"),
                ("آ",  "E7c_ayn_madda")]:
                new_verse = verse[:abs_pos] + partner + verse[abs_pos+1:]
                new_vs = list(hp_vs); new_vs[vi] = new_verse
                new_feats = nine_channel_features(new_vs, ref_bi, root_lm, canonical_text=canon_text)
                deltas = {ch_: new_feats[ch_] - canon_feats[ch_] for ch_ in CHANNELS_ALL}
                zscores = {ch_: _zscore(null_deltas_hp[ch_], d) for ch_, d in deltas.items()}
                n_fired = sum(1 for z in zscores.values() if abs(z) > 2.0)
                detected = n_fired >= 3
                b14_results[cls_name]["n_edits"] += 1
                b14_results[cls_name]["n_detected"] += int(detected)
                b14_results[cls_name]["z_all"].append(max(abs(z) for z in zscores.values()))
```

Time budget: adds ~5-8 min to exp46 full-mode runtime (one extra pass per ع position × 3 partners). Still <30 min total.

### New JSON fields (audit block)

```json
"audit_2026_04_24_b13_noe7_contexts": {
  "edits": [<list of detected no-E7 edit records as defined above>]
},
"audit_2026_04_24_b14_e7_breakdown": {
  "note": "3-way E7 sub-classes under normalize_rasm_hamza_preserving.",
  "normalizer": "normalize_rasm_hamza_preserving",
  "subclasses": {
    "E7a_ayn_bare_alef":  {"pair": "ع↔ا",   "n_edits": N, "n_detected_3of9": N, "detection_rate": X},
    "E7b_ayn_hamza_alef": {"pair": "ع↔أ/إ", "n_edits": N, "n_detected_3of9": N, "detection_rate": X},
    "E7c_ayn_madda":      {"pair": "ع↔آ",   "n_edits": N, "n_detected_3of9": N, "detection_rate": X}
  }
}
```

### Console summary addition

```
[exp46] B14 E7 3-way breakdown:
   E7a_ayn_bare_alef   ع↔ا     n=XXXX  det=X.X%
   E7b_ayn_hamza_alef  ع↔أ/إ   n=XXX   det=X.X%
   E7c_ayn_madda       ع↔آ     n=XX    det=X.X%
```

## Pre-registered interpretation

- If `E7b` rate > `E7a` rate (hamza-bearing alef easier to detect than bare alef): **phonetic hypothesis supported** — the detector IS sensitive to the genuine ع ↔ hamza phonetic distinction; the published E7 rate is a mixture of a detection signal buried under a bare-alef null floor.
- If `E7b` ≈ `E7a` ≈ `E7c`: **rasm hypothesis supported** — the detector is blind to hamza-specific distinctions. The published E7 signal is all from alef-frequency effects regardless of hamza status.
- `E7c` sample size will be small (`آ` is rare). Primary signal is `E7a` vs `E7b`.

## Runtime estimate

- Code work: ~15 min (apply patches, verify imports).
- exp46 `--fast` smoke test: ~2 min.
- exp46 full re-run (with B14 + B13 extras): ~25 min.

## Dependencies

- Rebuild must complete first (phase_06_phi_m.pkl is re-consumed by `self_check_begin()` via the protected file list).
- `QSF_STRICT_DRIFT=1` should be set when running to prove the re-run uses only clean checkpoints.
