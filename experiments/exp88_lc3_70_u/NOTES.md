# Notes

## Verified access pattern (matches exp70's `run.py`)

Loaded via `experiments._lib.load_phase("phase_06_phi_m")` (SHA-verified loader), then:

- `phi["state"]["X_QURAN"]` — `(68, 5)`, Band-A Quran surahs
- `phi["state"]["X_CTRL_POOL"]` — `(2509, 5)`, Band-A controls concatenated in `ARABIC_CTRL_POOL` order
- `phi["state"]["FEAT_COLS"]` — `["EL", "VL_CV", "CN", "H_cond", "T"]`, giving `T_idx = 4`, `EL_idx = 0`
- `phi["state"]["ARABIC_CTRL_POOL"]` — list of corpus names in concatenation order
- `phi["state"]["FEATS"][cname]` — list of per-unit records, each with `"n_verses"`; filter by `BAND_A_LO <= n_verses <= BAND_A_HI` to recover the row set in `X_CTRL_POOL`
- `phi["state"]["BAND_A_LO"] = 15`, `phi["state"]["BAND_A_HI"] = 100`

## Verified reproducible output (first successful run)

```
[exp88] Quran-side=53/68 (expected 53/68)
[exp88] Per-family leak into Quran side:
         poetry_jahili        n=  65  leaks=0
         poetry_islami        n= 211  leaks=0
         poetry_abbasi        n=1167  leaks=0
         ksucca               n=  19  leaks=0
         arabic_bible         n= 977  leaks=7
         hindawi              n=  70  leaks=0
```

Per-family counts match `exp70_decision_boundary.json::per_corpus` exactly; 7 leakers all from `arabic_bible`; zero leakage from the other 5 families. Every locked scalar in PAPER.md §4.35 reproduces.

## Fingerprint-drift warnings

`load_phase` emits two `UserWarning: [FINGERPRINT DRIFT]` lines because the checkpoint's `corpus_sha` and `code_sha` differ from the current `corpus_lock.json` / `code_lock.json` combined hashes. This is informational only — the Band-A feature matrix used by `§4.35` reproduces `exp70`'s locked counts byte-for-byte, so the drift affects some downstream file not the LC3-70 inputs. The warnings are retained (not suppressed) so any future consumer sees them.
