# exp104e_F53_rigveda — PREREG (Phase 3, fifth in the H59 chain — Sanskrit Vedic Rigveda 1.1, **with a substantive structural finding caught at pre-stage**)

**Hypothesis ID**: H59e
**Status**: pre-registered, hash-locked, **and immediately diagnosed as `BLOCKED_rigveda_1_1_too_short` AND `FAIL_audit_peer_pool_size`** at pre-stage time. NO compression call has been or will be issued under this PREREG. The PREREG-as-written stays on the audit trail; the substantive amendment path is documented in §10.
**Patch context**: v7.9-cand patch H V3.2 (or later). Pre-staged 2026-04-28 night while `exp104c_F53_psalm78` is in flight.
**Position in chain**: fifth filed PREREG in the H59 amendment chain. Carries a substantive language-level structural finding (§10) about the Rigveda's protocol-fit.

---

## 0. Why this exists (one paragraph)

Sanskrit (Indo-Aryan branch of Indo-European) is a third language family for the F53 cross-tradition pilot — distinct from both Semitic (H59 → H59c, Hebrew) and Hellenic (H59d, Greek). The Rigveda Saṃhitā is the canonical text, oral-tradition since ~1500–1200 BCE, written codification ~500 BCE, ~1028 hymns (suktas) across 10 mandalas. The natural target analogue to "Mark 1" (Greek NT opener) is "Rigveda 1.1" (the first Agni hymn, the canonical opener). This PREREG is filed and hash-locked **before any Sanskrit compression call is issued**, and a pre-stage diagnostic was run via `scripts/_rigveda_sizing.py` immediately afterwards.

**The diagnostic returned a substantive structural finding** (§10): the Rigveda's sukta-length distribution is incompatible with the exp104-locked chapter protocol at the language level. This is recorded honestly here rather than amended away.

---

## 1. Hypothesis (one paragraph, as PREREGed)

**H59e (F53 cross-tradition Sanskrit Vedic Rigveda 1.1 pilot, as filed)**: Under the K=2 multi-compressor consensus rule with τ thresholds calibrated *on a Rigveda-internal peer pool* (per-compressor 5th percentile of length-matched ctrl-Δ NCD distribution; identical recipe to `exp95c`, `exp104`, `exp104b`, `exp104c`), single-letter substitution on **Rigveda 1.1** (33-Devanagari-consonant skeleton, vedic accents stripped, vowels stripped) achieves **recall ≥ 0.999** with **FPR ≤ 0.05** against the same calibration peer pool.

**Pilot scope**: one sukta only (Rigveda 1.1).

---

## 2. Locked decision rules

### 2.1 Frozen target text

- **Target**: Rigveda 1.1 (Agni Sukta, 9 verses, the canonical opener of the Rigveda Saṃhitā).
- **Source**: `data/corpora/sa/rigveda_mandala_1.json`, manifest-locked at SHA-256 `1abdf9cb9d71d1a2…` (per `data/corpora/sa/manifest.json`).
- **Letter normalisation**: 33 Devanagari consonants U+0915 to U+0939 (क-ह) + 11 nukta-modified U+0958 to U+0960 + ऩ (U+0929) + ऱ (U+0931) + ऴ (U+0934). Strip: vowels, vedic accent marks (udatta U+0951, anudatta U+0952), virama (U+094D), nukta (U+093C), danda (।), double-danda (॥), Devanagari numerals (U+0966 to U+096F), whitespace, Latin letters and punctuation. NFC-normalised before extraction.
- **Why the consonant-only skeleton**: parallel to the Hebrew 22-letter consonant skeleton in exp104c (Hebrew niqqud-stripped). Greek NT uses 24 letters (vowels written natively); Devanagari natively writes both consonants and vowels but the consonant-only choice is more conservative and gives the cleanest cross-tradition Semitic-style analogue.

### 2.2 Frozen peer pool

- Other Rigveda suktas across all 10 mandalas (1027 candidates, excluding Rigveda 1.1 itself).
- Length-matched to Rigveda 1.1 ± 30 % (locked window fraction inherited from exp104).
- `TARGET_N_PEERS = 200`, `PEER_AUDIT_FLOOR = 100` (inherited).

### 2.3, 2.4 — τ-calibration protocol, verdict ladder

Identical to exp104 §2.3 / §2.4 with the chapter target swapped. See `experiments/exp104_F53_tanakh_pilot/PREREG.md` for full text.

### 2.5 What promotion does NOT mean — same disclaimer as exp104d §2.5.

---

## 3. Frozen constants — same as exp104d §3, except `TARGET_LANG = "sa"`, `TARGET_MANDALA = 1`, `TARGET_SUKTA = 1`, `LETTER_ALPHABET = <33-Devanagari-consonants + nukta-modified>`, `CORPUS_PATH = "data/corpora/sa/rigveda_mandala_*.json"`.

---

## 4. Audit hooks — same as exp104d §4 with Sanskrit-specific normaliser sentinel substituted: input `"अ॒ग्निमी॑ळे"` (Rigveda 1.1.1 opening) → expected consonant-only output `"गनमळ"` (5 consonants: ग न म + ळ; the अ is a vowel and stripped). The exact PREREG-locked normaliser sentinel is committed below in §11; no Sanskrit compression call is issued under this PREREG.

---

## 5. Honesty clauses — same as exp104d §5; §5.1 binding.

---

## 6, 7, 8 — Reproduction, cross-references, status — same scaffolding as exp104d, with the H59e label and Sanskrit-corpus paths.

---

## 9. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above and below is final and **before** any Sanskrit compression call is issued. The hash is written to `experiments/exp104e_F53_rigveda/PREREG_HASH.txt`. No `run.py` exists at hash-lock time, by design.

---

## 10. Pre-stage diagnostic finding (substantive; the real result of this PREREG)

`scripts/_rigveda_sizing.py` was run immediately after this PREREG was hash-locked, on the same data the protocol references. The diagnostic issues NO compression calls; it only counts letters and peers. Its output is reproduced verbatim:

```
Total suktas: 1027
Consonant-skeleton length: min=71, median=395, mean=481, max=3072

Suktas with >=1000 consonants: 59 / 1027
Suktas with >=1500 consonants: 7 / 1027
Suktas with >=2000 consonants: 4 / 1027
Suktas with >=2500 consonants: 3 / 1027

Top 15 longest suktas (cleanest exp104e target candidates):
  RV 9.97: 3072 consonants
  RV 1.164: 2902 consonants
  RV 9.86: 2717 consonants
  RV 10.85: 2099 consonants
  RV 6.47: 1627 consonants
  RV 8.19: 1529 consonants    [...]

Rigveda 1.1 (the Agni opener): 275 consonants -- BELOW 1000 floor

Peer-pool feasibility (length-matched +/-30%) for top 5 candidates:
  RV 9.97  (n=3072): peers in [2150,3993] = 2   (WOULD-FAIL audit)
  RV 1.164 (n=2902): peers in [2031,3772] = 3   (WOULD-FAIL audit)
  RV 9.86  (n=2717): peers in [1901,3532] = 3   (WOULD-FAIL audit)
  RV 10.85 (n=2099): peers in [1469,2728] = 4   (WOULD-FAIL audit)
  RV 6.47  (n=1627): peers in [1138,2115] = 32  (WOULD-FAIL audit)
```

### 10.1 What this means (substantive)

**Rigveda 1.1 (275 consonants) is far below the locked 1,000-consonant floor.** The verdict ladder fires `BLOCKED_rigveda_1_1_too_short` immediately at branch 2.

**More importantly, NO single Rigveda sukta satisfies BOTH floors simultaneously**. The longest sukta (RV 9.97, 3,072 consonants) clears the 1,000-letter floor by 3× but has only 2 length-matched peers; the best peer-pool candidate (RV 6.47, 1,627 consonants) has 32 length-matched peers, still below the 100-peer floor. The Rigveda's sukta-length distribution is heavily skewed toward short hymns (median 395, mean 481), with the few long suktas appearing as outliers without length-matched siblings.

**This is a structural mismatch between the Rigveda's canonical-unit shape and the exp104-locked chapter protocol**, NOT a chapter-selection problem. The exp104 protocol was calibrated for chapter-length texts in the [1,500, 5,000]-consonant band (Hebrew Tanakh chapters, Greek NT chapters, Quran surahs). The Rigveda's atomic unit (sukta) is one order of magnitude smaller; the protocol's locked length-window-and-peer-floor rule is incompatible with Rigveda suktas as units of analysis.

### 10.2 Substantive amendment options for the human auditor

Three categories of amendment, ranked by least-protocol-disturbance:

#### 10.2.A — Multi-sukta unit (recommended)
Re-define the Rigveda canonical unit as a *sukta-cluster* rather than a single sukta. Natural choices:
- **Rigveda 1.1–1.10** (the first 10 Agni hymns, ~3,000 consonants combined)
- **Rigveda 1.1–1.30** (~9,000 consonants)
- A whole mandala (~30,000–50,000 consonants — too long; would break the variant-enumeration cost budget)

Substantive risk: re-defining the canonical unit is a substantive change. The Rigveda's mandala-level structure (10 mandalas, each composed of ~100 suktas grouped by deity) makes "first 10 suktas of a mandala" a natural unit, but it's not a tradition-recognised division. **The amendment requires a fresh hash-locked PREREG with a full §2.1 redefinition.**

#### 10.2.B — Different language with similar atomic-unit shape (recommended)
Pick a different Indo-Aryan / Indo-Iranian canon with chapter-shaped units:
- **Pali Tipiṭaka — Digha Nikaya** (long discourses; many suttas in the [2,000, 8,000]-letter range; data on disk at `data/corpora/pi/dn/`)
- **Avestan Yasna** (72 chapters, mid-length; data on disk at `data/corpora/ae/`)

Substantive cost: low (a fresh PREREG; Pali / Avestan loaders need writing).
Substantive payoff: cleanest cross-language test that doesn't require redefining the Rigveda's canonical unit.

#### 10.2.C — Relax the locked LENGTH_MATCH_FRAC
Change ±30 % to ±100 % (i.e., 0.5× to 2× target length). This brings RV 6.47 to ~150 peers but is a *substantive change to the locked exp104 protocol*. **Strongly NOT recommended** — would cascade-affect the Hebrew, Greek, and Quran-internal F53 results retroactively.

### 10.3 Recommendation
**10.2.B with Pali Tipiṭaka Digha Nikaya** — Pali is genealogically related to Sanskrit (both Indo-Aryan), the discourses are chapter-shaped, the data is on disk, and the protocol requires no re-definition of the canonical unit. Defer Sanskrit Rigveda to a future amendment with the multi-sukta unit (Option 10.2.A) once the chapter-shape canons are exhausted.

---

## 11. Frozen-time addendum: PREREG hash and verdict ladder behaviour

**Verdict if `run.py` were ever launched on this PREREG-as-filed**: the verdict ladder fires `BLOCKED_rigveda_1_1_too_short` at branch 2 (Rigveda 1.1 = 275 consonants < 1,000 floor). No compression call would be issued. This is an honest BLOCKED outcome; the science is unchanged.

**No `run.py` will be created for this PREREG.** The audit trail records: (a) PREREG drafted and hash-locked; (b) pre-stage diagnostic identified the structural mismatch documented in §10; (c) substantive amendment paths recorded in §10.2; (d) recommended next step is Pali Digha Nikaya under a fresh PREREG, NOT a `run.py` for this PREREG.

This file's SHA-256 stays as the audit trail for the H59e protocol-as-filed.
