# expP4_F53_cross_tradition — Pre-registration (BLOCKED on corpus acquisition)

**Hypothesis ID**: H38
**Status**: pre-registered, **BLOCKED on corpus-acquisition** (sealed; no scoring code may be executed until §6 corpora are ingested with full SHA-256 manifest discipline).
**Frozen**: 2026-04-26 night (Asia/Riyadh) under v7.9-cand patch G doc-hygiene.
**Patch context**: v7.9-cand patch G — cross-tradition extension of F53 / F54 (multi-compressor consensus single-letter forgery detection), gated by the same per-tradition corpus discipline used for the Arabic peer pool.
**Supersedes**: nothing yet — H38 is the cross-tradition counterpart to H37 (`exp95e_full_114_consensus_universal`).

---

## 0. Why this PREREG exists *before* its corpora

This pre-registration is filed **specifically to lock the design before any
peer corpus is acquired**. The single most common failure mode in cross-
tradition stylometry is corpus-shopping: an experimenter compares Quran-vs-
Hebrew, sees a verdict they like, then ingests another Hebrew corpus, etc.
Locking the protocol here — including which compressors, which τ rule,
which consensus rule, which acceptance criteria, and which native peer pool
acquisition manifest — eliminates that degree of freedom.

**No scoring code in this directory will execute** until §6's corpus
manifest is filled in and SHA-256-locked. The blocking gate is enforced
both by the absence of `run.py` (only `PREREG.md` exists in this folder
at registration time) and by a runtime check that `data/corpora/<tradition>/_manifest.json`
exists for every tradition listed in §6 before the run can dispatch.

---

## 1. Hypothesis

**H38 (cross-tradition closure of F53)**: Under the same K = 2 multi-
compressor consensus rule across {gzip-9, bz2-9, lzma-preset-9, zstd-9}
that closes Adiyat-864 in `exp95c` and (pending) all 114 surahs in
`exp95e`, single-letter consonant-substitution forgeries on **canonical
scriptures of other oral-liturgical traditions** are detected at
**aggregate recall ≥ 0.999** with **per-canon recall ≥ 0.99**, **using
τ thresholds calibrated on each tradition's own native peer-corpus
ctrl-null pool** (matching the Arabic protocol exactly). The five
candidate canonical scriptures are: Hebrew Tanakh, Greek New Testament,
Pali Tipiṭaka (DN + MN canon), Sanskrit Rigveda Saṃhitā (10 maṇḍalas),
Avestan Yasna (72 chapters).

**What this is NOT**: H38 does **not** claim that the Quran's F53 closure
is *stronger* than other traditions' closures. It claims the K = 2 rule
*generalises*. A PASS verdict means F53 is a transmission-fidelity tool
that works on *any* canonical-scripture corpus given a per-tradition
calibration; it does **not** elevate the Quran above other traditions on
F53. Comparative-magnitude claims are explicitly out of scope (we do not
have a length-controlled effect-size scale that is calibrated cross-
linguistically).

**What this is also NOT**: H38 does **not** test cross-script edits
(transliteration-class substitutions, e.g. Devanagari ट → ठ in Sanskrit,
or Greek θ → φ in NT). It tests within-script consonant substitutions
analogous to the Arabic 28-letter consonant set, on each tradition's
native script. Cross-script confounds are out of scope.

---

## 2. Why this experiment is needed

`exp95e` (H37) closes F53 within the Quran corpus. The natural reviewer
question — "does the K = 2 rule work on other oral-canonical traditions
or is the Quran special?" — is the H38 question. **H38 is *not* the same
question** as cross-tradition Quran-uniqueness (which is about *whether
the Quran outranks other canons on a given feature*, e.g. R3, EL, Hurst);
H38 is about *whether the F53 detector itself generalises as a forgery-
detection tool across canon-scripture corpora.* These are orthogonal
questions, and the published cross-tradition data (`expP4_*` family,
`CROSS_TRADITION_FINDINGS_2026-04-25.md`) settles only the former.

If H38 passes, F53 widens from "Quran-specific paper-grade" to
"transmission-fidelity universal", and the deployable detector becomes
a *generic single-letter forgery tool* for any oral-canonical scripture
with a native peer-corpus pool. If H38 partially passes (some traditions
pass, some don't), we obtain a per-tradition landscape — equally
publishable, and arguably more interesting because it would tell us
*which* corpus structural properties make F53 work.

If H38 fails uniformly, F53 reduces to a "tool that works on Arabic"
and the §4.43.1 PAPER.md text must be re-scoped accordingly.

---

## 3. Frozen constants (locked before any corpus is acquired)

| Symbol | Value | Source |
|---|---|---|
| `SEED` | 42 | matches `exp95c` / `exp95e` |
| `N_PERT_PER_UNIT` | 20 | matches `exp95c` / `exp95e` |
| `CTRL_N_UNITS_PER_TRADITION` | 200 | matches `exp95c` *per tradition*, not aggregate |
| `GZIP_LEVEL` | 9 | matches `exp95c` |
| `BZ2_LEVEL` | 9 | matches `exp95c` |
| `LZMA_PRESET` | 9 | matches `exp95c` |
| `ZSTD_LEVEL` | 9 | matches `exp95c` |
| `FPR_TARGET` | 0.05 (per tradition) | matches `exp95c` |
| `BAND_A_LO`, `BAND_A_HI` | 15, 100 | matches `exp95c` (in canon-units, e.g. surahs / books / suttas / maṇḍalas / yasna) |
| `HEADLINE_K` | 2 | matches `exp95c` / `exp95e` |
| `PROTOCOL_DRIFT_TOL` | 0.001 | matches `exp95c` / `exp95e` |
| `MIN_CONSONANT_INVENTORY_SIZE` | 20 | per-tradition; below this, the substitution alphabet is too small to enumerate at scale |
| `tau_per_compressor_per_tradition` | **calibrated per tradition on its own ctrl-null pool** | not transferred from Arabic; each tradition gets its own τ |

### 3.1 Why τ is *not* transferred from Arabic

The Arabic τ values in `exp95c` are calibrated on a 4 000-edit ctrl-null
pool drawn from the 6 Arabic peer corpora at Band-A. Hebrew, Pali,
Sanskrit, Greek, and Avestan have different orthographic densities,
different word-length distributions, and (for Pali / Greek / Hebrew)
different consonant-cluster structures. Using Arabic τ on a Hebrew text
would conflate "what NCD looks like for an edit" with "what NCD looks
like for any pair of Hebrew-corpus units". Each tradition gets its own
τ_per_compressor calibrated on its own native peer pool, with the same
ctrl-p95 quantile rule. **The K = 2 consensus rule is fixed; the
per-compressor thresholds vary per tradition.**

### 3.2 What stays frozen across traditions

The compressor stack `{gzip-9, bz2-9, lzma-preset-9, zstd-9}` does not
change. The K = 2 consensus rule does not change. The single-letter
within-script consonant-substitution edit class does not change. The
SEED, FPR_TARGET, and PROTOCOL_DRIFT_TOL do not change. **What changes
between traditions is only the corpus pool, the consonant inventory of
each script, and the calibrated τ values.**

---

## 4. Verdict ladder (per-tradition, then joint)

For each tradition `t ∈ {tanakh, nt, pali, rigveda, avestan}`:

1. `FAIL_t_corpus_unavailable` — `data/corpora/<t>/_manifest.json` missing or any peer-corpus SHA mismatches its lock.
2. `FAIL_t_inventory_too_small` — tradition `t`'s consonant inventory size `< MIN_CONSONANT_INVENTORY_SIZE`.
3. `FAIL_t_ctrl_overfpr` — at least one peer-corpus K = 2 ctrl FPR `> FPR_TARGET + 1·10⁻⁶`.
4. `FAIL_t_per_canon_floor` — at least one canonical sub-unit (book / sutta / maṇḍala / chapter) has K = 2 recall `< 0.99` on the V1 scope.
5. `FAIL_t_aggregate_below_floor` — aggregate K = 2 recall (variants pooled across the canon) `< 0.999`.
6. `PARTIAL_t_per_canon_99` — every sub-unit `≥ 0.99` AND aggregate `≥ 0.99` BUT aggregate `< 0.999`.
7. `PASS_t_999` — every sub-unit `≥ 0.99` AND aggregate `≥ 0.999`.
8. `PASS_t_100` — every sub-unit K = 2 recall = 1.000 AND aggregate = 1.000.

Across all five traditions:

- `PASS_universal_F53` — every tradition with sufficient corpus achieves at least `PASS_t_999`.
- `PARTIAL_F53_some_traditions` — at least one tradition reaches `PASS_t_999` but at least one fails the per-canon or aggregate floor.
- `FAIL_F53_not_cross_tradition` — no tradition reaches `PASS_t_999`.

The joint verdict is reported alongside each per-tradition verdict; no single tradition's PASS or FAIL overrides another's.

---

## 5. Strict honesty clauses

- **HC1** — H38 is a **generalisation test**, not a Quran-vs-other comparison. PASS does **not** rank traditions; FAIL does **not** "demote" the Quran's F53 closure (which is independent and already pre-registered as H37). Comparative-magnitude framing is explicitly out of scope.
- **HC2** — τ is calibrated **per tradition** on its own ctrl-null pool. Cross-tradition τ transfer is forbidden; doing so conflates "edit signal" with "corpus-pair NCD baseline".
- **HC3** — Each tradition's verdict is conditioned on the availability of its native peer corpus. Native peer corpora must (i) match the canonical scripture's language and script, (ii) span comparable Band-A unit counts, (iii) be ingested with full SHA-256 lock discipline matching `results/integrity/corpus_lock.json`.
- **HC4** — A `FAIL_t_corpus_unavailable` is **not** a verdict on the tradition's transmission fidelity; it is a verdict on the project's data-acquisition status. The PREREG explicitly distinguishes "corpus-blocked" from "experiment-failed".
- **HC5** — H38 does **not** test multi-letter / word-level / cross-script edits. The single-letter within-script enumeration is the only edit class.
- **HC6** — A PASS does **not** claim that the K = 2 consensus rule is "the canonical detection rule for canonical scripture". Other detection rules (e.g. K = 3 unanimous) may be tested in follow-up experiments and may be more or less appropriate per tradition. K = 2 is fixed here for protocol consistency with `exp95c` / `exp95e`.
- **HC7** — A PASS in any tradition does **not** generalise to non-canonical scripture in that tradition. The protocol is bound to the canonical scripture as defined by each tradition's own canonical-scripture authority (e.g. for the Tanakh, the Masoretic text; for the NT, the Nestle-Aland 28).
- **HC8** — Honest negatives are accepted. If F53 fails universally, the negative is published as is; the §4.42 / §4.43 PAPER text is re-scoped to "F53 is an Arabic-specific transmission-fidelity tool" without retracting the Arabic verdicts.

---

## 6. Required peer corpora (acquisition gate, BLOCKING)

Before any scoring code can execute, the following peer corpora must be
ingested and SHA-256-locked. Each row must be filled in and signed off
before this PREREG transitions from BLOCKED to ARMED.

| Tradition | Canonical scripture | Required native peer pool | Status | Manifest SHA-256 |
|---|---|---|---|---|
| Hebrew | Tanakh (Masoretic) — already in repo | Hebrew narrative + Hebrew poetic peers (≥ 6 corpora, ≥ 200 Band-A-equivalent units total). Candidates: Mishnah, Talmud Bavli (selected tractates), Aggadic midrashim, Hebrew piyyutim, modern Hebrew prose | **BLOCKED** | — |
| Greek | New Testament (Nestle-Aland 28) — already in repo | Koine Greek prose + Koine letters + Atticist prose (≥ 6 corpora, ≥ 200 Band-A-equivalent units total). Candidates: Septuagint historical books, Josephus, Philo, Plutarch's Moralia, Epictetus | **BLOCKED** | — |
| Pali | Tipiṭaka DN + MN — already in repo | Pali Vinaya + Pali commentaries + Pali later texts (≥ 6 corpora, ≥ 200 sutta-equivalent units total). Candidates: Vinaya Pitaka books, Visuddhimagga, Milindapañha, Abhidhamma | **BLOCKED** | — |
| Sanskrit | Rigveda Saṃhitā 10 maṇḍalas — already in repo | Sanskrit prose + Sanskrit later poetry + Vedic peer corpora (≥ 6 corpora, ≥ 200 Band-A-equivalent units total). Candidates: Atharvaveda, Sama Veda, Brāhmaṇas, Upanishads, Sanskrit kāvya | **BLOCKED** | — |
| Avestan | Yasna 72 chapters — already in repo | Avestan ritual + Old Avestan + Younger Avestan peers (≥ 4 corpora; the Avestan corpus is small by nature, so the floor is relaxed). Candidates: Visperad, Vendidad, Yashts, Khorda Avesta | **BLOCKED** | — |

**Acquisition discipline**: each peer corpus must (a) be plain text or
raw structured data (no OCR'd PDF chains), (b) be ingested under the
same `src/raw_loader.py` discipline already used for the Arabic peer
pool, (c) have its SHA-256 lock written to `results/integrity/corpus_lock.json`
under a new section `cross_tradition_peer_pools_2026-XX-XX`, and (d)
pass the same G1-G5 sanity gate (`min_units ≥ 10`, no single-token
units, no identical units, valid CV, character-set coverage ≥ 0.95
matching the tradition's primary script) used for the Arabic peer pool.

---

## 7. Inputs (read-only when un-blocked, integrity-checked)

- `data/corpora/<tradition>/` — canonical scripture + native peer pool, per the §6 manifest, all SHA-256-locked.
- `experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json` — protocol drift sentinel reference (the per-compressor parameters and protocol ladder must reproduce on the Quran corpus before scoring any cross-tradition run).
- `experiments/_lib.py` — read-only loader + self-check.

The run uses **no LLM tools, no machine-translation tools, no morphological
analysers**. Compressor primitives + per-script consonant-substitution
enumerators are the entire toolchain. The full output is a deterministic
function of (corpus SHAs, scope flag, seed).

---

## 8. Outputs (write-only under sandboxed dir, when un-blocked)

All outputs under `results/experiments/expP4_F53_cross_tradition/<tradition>/`:

- `expP4_F53_cross_tradition_<tradition>.json` — per-tradition receipt (per-canon-unit recall + FPR, per-compressor solo recalls, missed-variant indices, verdict, runtime, hashes)
- `missed_variants_<tradition>.csv` — every variant where K_fired < 2
- `per_canon_table_<tradition>.csv` — one row per canonical sub-unit
- `audit_report_<tradition>.json` — drift sentinels, fingerprint hashes, missed-variant clustering analysis
- `joint_verdict.json` — top-level joint verdict combining the per-tradition verdicts

---

## 9. Audit hooks (always executed when un-blocked)

1. **τ-drift sentinel per tradition** — each tradition's τ is calibrated and locked on its own ctrl-null pool *before* any variant scoring begins; if any per-compressor τ drifts during the run, the run aborts.
2. **Quran regression sub-run** — even cross-tradition, the run includes a Quran K = 2 regression sub-run that must reproduce `exp95c` PASS_consensus_100 on Q:100 (recall = 1.000, gzip-solo = 0.990741) within `PROTOCOL_DRIFT_TOL`. This sentinel guards against accidental compressor-version drift across machines.
3. **Self-check** — `experiments._lib.self_check_begin/end` verifies protected-file integrity before and after.
4. **Fingerprint sentinel** — re-hashes `PREREG.md` and `run.py` at run start; the hash is stamped on every output JSON.
5. **Missed-variant clustering per tradition** — for every (orig, repl) consonant pair in each tradition's script, log the K = 2 miss rate; a pair with miss rate ≥ 0.10 produces a `cluster_warning` (informational; not a verdict failure).
6. **Per-canon-unit variant-count sanity check** — each canonical sub-unit's V1 variant count must equal `len(consonant_positions(unit_first_segment)) × (consonant_inventory_size − 1)`.

---

## 10. Replication recipe (when un-blocked)

```bash
# Per-tradition (V1 scope, ~30 min – 4 h depending on tradition)
python -m experiments.expP4_F53_cross_tradition.run --tradition tanakh
python -m experiments.expP4_F53_cross_tradition.run --tradition nt
python -m experiments.expP4_F53_cross_tradition.run --tradition pali
python -m experiments.expP4_F53_cross_tradition.run --tradition rigveda
python -m experiments.expP4_F53_cross_tradition.run --tradition avestan

# Joint verdict (after all 5 per-tradition runs complete)
python -m experiments.expP4_F53_cross_tradition.join_verdicts
```

---

## 11. What this experiment does NOT claim

- It does **not** claim cross-tradition Quran-uniqueness. F53 generalisation is orthogonal to per-feature Quran-vs-other comparisons; the latter are settled by the `expP4_*` family + `CROSS_TRADITION_FINDINGS_2026-04-25.md` and have already produced **R09**, **R48**, and **R52** retractions.
- It does **not** test cross-script transliteration edits. Within-script consonant substitution is the only edit class.
- It does **not** elevate the Quran or any other tradition above the others on F53 magnitude. PASS / FAIL is per-tradition; cross-tradition magnitude comparison would require length-control and inventory-size control that are out of scope here.
- It does **not** claim *replication* of any per-tradition PASS. Single-team single-codebase results require external two-team replication before they can be cited as community-validated.

---

## 12. Pre-registration locking checklist (BLOCKED gates)

- [x] §3 frozen constants pinned (locked 2026-04-26 night)
- [x] §4 verdict ladder pinned in strict-order form
- [x] §5 honesty clauses listed
- [x] §6 native peer corpus list pinned (acquisition status BLOCKED for all 5 traditions)
- [x] §7 inputs and §8 outputs listed
- [x] §9 audit hooks listed
- [x] §11 explicit list of what is NOT claimed
- [ ] §6 corpus manifests filled and SHA-256-locked (transitions BLOCKED → ARMED)
- [ ] PREREG SHA-256 hash embedded in `run.py::_PREREG_EXPECTED_HASH` (filled when run.py is created at ARMED transition)
- [ ] First per-tradition run executed (filled per-tradition at run time)
- [ ] Joint verdict computed and locked (filled after last per-tradition run)

**Until the 5 corpus-manifest checkboxes are filled, this experiment must not produce numerical output.** This PREREG is the evidence-of-pre-registration trail; the corpus-acquisition transition will append a `## 13. Corpus-acquisition lock` block (with per-tradition manifests, SHAs, and dates) below before any scoring runs.

---

*Pre-registered 2026-04-26 night under v7.9-cand patch G doc-hygiene. Companion to `experiments/exp95e_full_114_consensus_universal/PREREG.md` (H37 within-Quran universal scaling). H38 stays BLOCKED until peer-corpus acquisition is complete; this enforces that no implicit cross-tradition Quran-uniqueness claim can be smuggled in via H38 before the protocol is fully scoped.*
