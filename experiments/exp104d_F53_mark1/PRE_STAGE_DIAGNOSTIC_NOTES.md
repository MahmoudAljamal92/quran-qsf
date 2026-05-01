# exp104d_F53_mark1 — pre-stage diagnostic notes

**Status**: pre-staged with PREREG hash-locked (SHA-256 `48ddbef186060365…`); `run.py` implemented; pre-stage diagnostic via `scripts/_mark1_peer_sizing.py` complete; **launch BLOCKED on a substantive amendment decision**. NO compression calls have been issued. Discovered 2026-04-28 night, patch H V3.2.

---

## What pre-stage diagnostic found

Running `python scripts/_mark1_peer_sizing.py` on the locked PREREG protocol revealed four issues. Issues 1–3 are documentation / data-format details with zero protocol-substance impact; all are fixed in the PREREG and run.py without re-staging the science. Issue 4 is a substantive amendment decision that the human auditor must make.

### Issue 1 — Sentinel typo (FIXED, recorded as PREREG erratum)
- PREREG §4.3 expected the locked sentinel `"Ἐν ἀρχῇ ἦν ὁ λόγος" → "εναρχηηνολογος"` (16 chars, ending in final-sigma `ς`).
- Actual normaliser output: `"εναρχηηνολογοσ"` (14 chars, ending in medial sigma `σ`).
- Root cause: PREREG §4.3 sentinel was hand-typed and forgot to apply the §2.1 final-sigma fold (`ς → σ`) to itself; §2.1 substantive rule is unchanged.
- Fix: PREREG §4.3 erratum block added; expected value corrected to 14 chars ending in `σ`. PREREG re-hashed; run.py `_PREREG_EXPECTED_HASH` and `_NORMALISER_SENTINEL_EXPECTED` updated. New PREREG hash `48ddbef186060365e7bb6db4b71bd1b6e31621effab283b994eb093fb8e139e3`.

### Issue 2 — OpenGNT compound-field bracket characters (FIXED, run.py only)
- Compound fields in OpenGNT v3.3 are wrapped in `〔` (U+3014 LEFT TORTOISE SHELL BRACKET) and `〕` (U+3015 RIGHT TORTOISE SHELL BRACKET), NOT French `«` / `»` (U+00AB / U+00BB) as initially assumed.
- Fix: run.py `_OPENGNT_BRACKET_OPEN` / `_OPENGNT_BRACKET_CLOSE` constants set to the correct characters. Tolerant of French / ASCII variants for robustness.

### Issue 3 — OpenGNT inner separator (FIXED, run.py only)
- Inner field separator inside compound fields is `｜` (U+FF5C FULLWIDTH VERTICAL LINE), NOT ASCII `|` (U+007C) as initially assumed.
- Fix: run.py `_OPENGNT_INNER_SEP` constant set; `_split_inner()` helper added with ASCII fallback.

### Issue 3.5 — OGNTk uses lunate sigma (FIXED, run.py only)
- The OGNTk column in OpenGNT v3.3 uses `ϲ` (U+03F2 GREEK LUNATE SIGMA SYMBOL) as the standard sigma form throughout (e.g. `βιβλοϲ` for `βίβλος`).
- The PREREG §2.1 `ς → σ` fold rule must be extended to all sigma variants `{ς, ϲ, Ϲ}` for OpenGNT compatibility.
- Fix: run.py `_SIGMA_FOLD_MAP` dictionary added covering `{ς, ϲ, Ϲ} → σ`. `Σ` (capital medial sigma) folds via `casefold()`. The substantive rule (24-letter alphabet, sigma forms collapsed) is unchanged; the implementation now handles the variant typography correctly.

### Issue 4 — Peer pool size below floor (NOT FIXED; substantive amendment required)
- Locked PREREG §2.2: peer pool = NT-narrative books outside Mark = `{40 Matt, 42 Luke, 43 John, 44 Acts, 58 Heb}`, length-matched to Mark 1 ± 30 %.
- Pre-stage diagnostic found:
  - Mark 1 has **3,530** consonant-and-vowel-skeleton letters (clears 1,000-letter floor easily) and **45** verses.
  - Length window: **[2,471, 4,589]** letters.
  - Peer pool size: **75 chapters** of 114 candidates (clears the window).
  - PEER_AUDIT_FLOOR (locked from exp104): **100**.
  - Verdict: **`FAIL_audit_peer_pool_size`** would fire (parallel to FN10 / `exp104b_F53_psalm119`).

---

## Substantive amendment options for the human auditor

The H59d → H59d? amendment-chain decision parallels H59 → H59b → H59c. Four options, ranked by least-protocol-disturbance:

### Option A — Different target chapter, same NT-narrative peer pool
- Pick a Mark chapter with more length-matched peers in the NT-narrative pool. Quick scan of the diagnostic output suggests Mark chapters in the 2,000–2,500-letter band would have ≥ 100 length-matched peers because more short Synoptic chapters fall within ± 30 % of those targets.
- Amendment cost: small (one-PREREG amendment, target chapter only; new hash; new run).
- Substantive risk: zero (still tests F53 on a Greek NT chapter).
- **Pick**: Mark 13 (~2,200 letters, end-times discourse) or Matthew 5 (~2,800 letters, Sermon on the Mount opening). Either is a reasonable narrative target.

### Option B — Wider NT peer pool (add epistles)
- Expand `PEER_BOOK_NUMBERS` from 5 narrative books to all 27 NT books minus Mark, growing candidates from 114 to ~260.
- Amendment cost: medium (PREREG §2.2 substantively changed; new hash).
- Substantive risk: low — epistolary books (Romans, Corinthians, etc.) share Koine register but have a different rhetorical mode (theological argument vs narrative). The F53 detector tests letter-level signal not genre, so cross-genre mixing is acceptable; but a pure-narrative peer pool was the cleanest analogue to exp104's Tanakh-narrative peers.

### Option C — Septuagint Greek narrative as peer pool
- Add Septuagint Greek narrative chapters (Genesis, Exodus, Joshua, Samuel, Kings) — no genre mixing with Mark 1, and ~80–120 narrative chapters available.
- Amendment cost: high (requires LXX corpus acquisition + Greek-Septuagint loader).
- Substantive payoff: cleanest cross-genre-controlled test.
- Defer to a future amendment if time permits.

### Option D — Stop here, don't run exp104d
- The two-Hebrew-Psalm chain (H59 → H59b → H59c) plus the pre-stage diagnostic on Greek already constitute a publishable Phase-3 dataset, given the diagnostic is itself a finding.
- Move on to exp104e (Sanskrit) for a third language family.

---

## Recommendation

If exp104c (currently running, ETA ~23:38) PASSes, **Option A with Matthew 5 or Mark 13** is the cleanest path: small protocol change, zero substantive risk, deliverable in ~3 hours of compute. If exp104c FAILs, **Option D** plus moving to exp104e is more defensible — a Hebrew FAIL plus a Greek pre-stage diagnostic is sufficient for Phase 3 publication, and a fresh Sanskrit datapoint adds a third language family without spending more time on the Greek-pool design.

---

## What files exist on disk and what they say

| Path | Status |
|---|---|
| `experiments/exp104d_F53_mark1/PREREG.md` | Hash-locked at SHA-256 `48ddbef186060365…`; §4.3 sentinel erratum block added; substantive protocol unchanged. |
| `experiments/exp104d_F53_mark1/PREREG_HASH.txt` | Stores the hash above. |
| `experiments/exp104d_F53_mark1/run.py` | Implements the protocol; sentinel passes; loader returns 260 chapters; **would FAIL_audit_peer_pool_size on launch** under the current PEER_BOOK_NUMBERS set. |
| `experiments/exp104d_F53_mark1/__init__.py` | Empty package marker. |
| `scripts/_mark1_peer_sizing.py` | Pre-stage diagnostic. NO compression calls. Output: 260 chapters / Mark 1 found / 75 peers / WOULD-FAIL on peer-pool floor. |
| `experiments/exp104d_F53_mark1/PRE_STAGE_DIAGNOSTIC_NOTES.md` | This file. |

---

## Why this is honest pre-staging, not protocol fishing

Two PREREG provisions explicitly authorise this diagnostic:

1. **PREREG §3** ("Frozen constants"): "Pre-run sizing diagnostic (deferred until after PREREG-hash lock; protocol-correct because the diagnostic only filters the peer pool count, not the verdict) will confirm the chapter clears the locked 1,000-letter floor and that ≥ 100 length-matched NT-narrative peers exist."
2. **PREREG §5.1** ("Pre-run sizing was an objective check, not a fishing expedition"): "If pre-run sizing reveals Mark 1 is too short OR has too few peers, the verdict is BLOCKED / FAIL_audit per the ladder. The chapter is **not re-rolled** to 'find' one that meets the constraints. An amendment PREREG with a different chapter is required."

§5.1 is the binding constraint: if the user picks Option A or B above, it MUST go through a fresh hash-locked amendment PREREG (e.g., `experiments/exp104d2_F53_mark13/PREREG.md`), NOT a silent edit of the current PREREG. The current PREREG (and its hash `48ddbef186060365…`) stays as the audit trail of the H59d-as-originally-staged protocol; the amendment gets a new hash and a new H-number (H59d2 or H59e).
