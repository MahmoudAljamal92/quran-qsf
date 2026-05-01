# Cross-tradition pool extension manifest (V3.12 deliverable #3)

**Purpose**: extend the 11-corpus universal-feature pool of `exp109_phi_universal_xtrad` to **≥ 22 corpora** so that rank-based permutation null reaches `perm_p < 0.05` (currently saturated at `1/N ≈ 0.091` for N=11; FN13 / F72 PARTIAL).

**Status**: SCAFFOLDING (2026-04-29 afternoon, V3.12). The harness is built; data acquisition is BLOCKED ON USER ACTION because most candidate sources require either academic library access, hand-translation, or non-trivial corpus-cleaning.

**Once acquired**: drop the cleaned UTF-8 plain-text into `data/corpora/<lang>/`, register the loader in `scripts/_phi_universal_xtrad_sizing.py`, re-run `exp109_phi_universal_xtrad` and `exp120_unified_quran_code`. The pre-registered V3.12 hypothesis is that with N ≥ 22, F72 will flip from PARTIAL_PASS to PASS at `perm_p < 0.05`.

---

## 1. Why N ≥ 22?

The `exp114_alphabet_independent_pmax` and `exp120_unified_quran_code` rank-based perm-null both saturate at `1/N` where N is pool size. Specifically for F72:

| N | floor `1/N` | minimum reachable perm_p | F72 verdict |
|---|---|---|---|
| 11 | 0.0909 | 0.0931 (locked) | PARTIAL_PASS (current) |
| 17 | 0.0588 | ~0.06 | still PARTIAL |
| 22 | **0.0455** | < 0.05 | **PASS** (target) |
| 30 | 0.0333 | < 0.05 | PASS with margin |

22 corpora is the strict minimum to break the PERM_ALPHA = 0.05 floor.

## 2. Already-acquired (11 corpora)

| Corpus | Family | Alphabet | Units | Source |
|---|---|---|---|---|
| Quran | Central Semitic | Arabic 28 | 114 sūrahs | `data/corpora/ar/quran-uthmani.txt` |
| Hebrew Tanakh | Northwest Semitic | Hebrew 22 | 921 chapters | `data/corpora/he/tanakh.json` |
| Greek NT | Hellenic IE | Greek 24 | 260 chapters | `data/corpora/el/greek_nt_sblgnt.txt` |
| Pāli Tipiṭaka | Indo-Aryan | IAST 31 | 186 suttas | `data/corpora/pi/` (PTS DN+MN) |
| Avestan Yasna | Indo-Iranian | Latin-Avestan 26 | 67 yasnas | `data/corpora/ae/` |
| Rigveda Saṃhitā | Indo-Aryan Vedic | Devanagari 51 | 1,011 sūktas | `data/corpora/sa/` |
| Arabic poetry (Jāhilī) | Central Semitic | Arabic 28 | 120 poems | `data/corpora/ar/poetry_jahili.txt` |
| Arabic poetry (Islāmī) | Central Semitic | Arabic 28 | 423 poems | `data/corpora/ar/poetry_islami.txt` |
| Arabic poetry (ʿAbbāsī) | Central Semitic | Arabic 28 | 2,575 poems | `data/corpora/ar/poetry_abbasi.txt` |
| Hindawī (modern) | Central Semitic | Arabic 28 | 72 chapters | `data/corpora/ar/hindawi.txt` |
| KSUCCA | Central Semitic | Arabic 28 | 42 docs | `data/corpora/ar/ksucca.txt` |
| Arabic Bible | Central Semitic | Arabic 28 | 1,183 chapters | `data/corpora/ar/arabic_bible.txt` |

**Total: 12 corpora** (N=11 in the locked exp109 because Arabic Bible is excluded as a near-translation of Hebrew Tanakh; can be optionally re-added).

## 3. Candidate corpora to acquire (target: 11 more for N ≥ 22)

### Tier 1 — high-quality public-domain, ready-to-use

| Corpus | Family | Alphabet (size) | Estimated units | Source URL | License | Status |
|---|---|---|---|---|---|---|
| **Old Tamil — Tirukkural** | Dravidian | Tamil 31 | 1,330 couplets (≈ 133 chapters of 10) | `https://www.projectmadurai.org/pmtexts/utf8/pmuni0153_01.html` | PD | ACQUIRABLE |
| **Coptic NT (Sahidic)** | Afro-Asiatic | Coptic 32 | 260 chapters (parallel Greek NT) | `https://github.com/CopticTreebank/coptic-treebank` | CC-BY-SA | ACQUIRABLE |
| **Latin Vulgate** | Italic IE | Latin 23 | 1,189 chapters | `https://www.vulgate.org/` or `clear-bible.github.io/data/vulgate.json` | PD | ACQUIRABLE |
| **Aramaic Targum Onkelos** | Northwest Semitic | Hebrew-Aramaic 22 | 187 chapters | `https://www.sefaria.org/Onkelos_Genesis` (API) | CC-BY-SA | ACQUIRABLE |
| **Mishnaic Hebrew (Mishnah)** | Northwest Semitic | Hebrew 22 | 524 chapters | Sefaria API | CC-BY-SA | ACQUIRABLE |
| **Classical Tibetan Kanjur** (Lhasa edition) | Tibetan-Burman | Tibetan 30 | 1,055 texts | `https://buddhanexus.net/` | CC-BY-NC | ACQUIRABLE |
| **Old Norse Poetic Edda** | Germanic IE | Latin 31 (Old Norse) | 35 poems | `https://heimskringla.no/wiki/` | PD | ACQUIRABLE |

### Tier 2 — academic / restricted access required

| Corpus | Family | Alphabet | Source | License barrier | Status |
|---|---|---|---|---|---|
| **Akkadian — Enūma Eliš** | East Semitic | Cuneiform / transliterated 24 | Lambert 2013 (Eisenbrauns); ORACC (`http://oracc.museum.upenn.edu/`) | Most ORACC texts are CC-BY but require lemmatised transliteration | NEEDS CLEANING |
| **Sumerian — ETCSL** | language isolate | Cuneiform / transliterated 28 | `https://etcsl.orinst.ox.ac.uk/` | CC-BY-NC; bibliographic transliteration only | NEEDS CLEANING |
| **Syriac Peshitta** | Aramaic NW Semitic | Syriac 22 | SEDRA (Beth Mardutho); `https://sedra.bethmardutho.org/` | Free for non-commercial; requires registration | ACADEMIC ACCESS |
| **Geʿez (Ethiopic) Bible** | Ethio-Semitic | Geʿez 26+vowels | `https://github.com/EthiopicBible` | PD; partial coverage | NEEDS COVERAGE-AUDIT |
| **Pahlavi Zand-i Wahman Yasn** | Indo-Iranian | Pahlavi 19 | TITUS Indogermanicum; `http://titus.uni-frankfurt.de/` | PD academic; transliteration only | ACADEMIC ACCESS |
| **Old Persian Behistun** | Indo-Iranian | Cuneiform 36 | TITUS / Achaemenid Royal Inscriptions Online | PD | ACQUIRABLE (small) |
| **Sanskrit Mahābhārata** | Indo-Aryan | Devanagari 51 | `https://gretil.sub.uni-goettingen.de/` | PD academic | ACQUIRABLE (large) |

### Tier 3 — speculative / future

| Corpus | Note |
|---|---|
| Pre-Islamic Arabic *kāhin* oracles | Hard: no surviving manuscripts; only quotations in later sources |
| Maqāmāt al-Ḥarīrī | Already used as F50 single-genre comparator; could be added to pool |
| Classical Chinese Daodejing | Already in `data/corpora/zh/`; harness needs a Chinese normaliser |

## 4. Harness API

The cross-tradition pool extension uses the same harness as `exp109_phi_universal_xtrad`. To add a new corpus:

1. Place cleaned UTF-8 plain text at `data/corpora/<lang_code>/<corpus_name>.txt`
2. Add a normaliser function `_normalise_<lang>` to `scripts/_phi_universal_xtrad_sizing.py` (skeleton-only; strip diacritics, fold variants, keep core letters)
3. Add a loader function `_load_<corpus>` that returns `list[list[str]]` (one inner list per unit; each unit is a list of verse strings)
4. Add the corpus name to the `EXPECTED_CORPORA` list in `scripts/_phi_universal_xtrad_sizing.py` and `experiments/exp120_unified_quran_code/run.py`
5. Re-run `python scripts/_phi_universal_xtrad_sizing.py` (refreshes per-corpus medians)
6. Re-run `python experiments/exp120_unified_quran_code/run.py` (refreshes F72 receipt)

The harness automatically:
- Computes the 5 universal features per unit (VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency)
- Aggregates per-corpus medians
- Updates pool centroid + std
- Recomputes D_QSF for every corpus
- Reruns the 10,000-permutation column-shuffle null
- Writes a fresh receipt to `results/experiments/exp120_unified_quran_code/`

## 5. Acquisition checklist

For each Tier-1 corpus (in order of difficulty):

- [ ] **Tirukkural (Tamil)**: download UTF-8 from Project Madurai → split into 133 chapters → register `_normalise_tamil` (Tamil block U+0B80–U+0BFF, strip pulli ◌்).
- [ ] **Vulgate (Latin)**: download from clear-bible JSON dump → keep 23-letter Latin alphabet (j→i, v→u folding).
- [ ] **Coptic NT**: clone CopticTreebank repo → use Sahidic glosses; alphabet 32 letters with diacritics stripped.
- [ ] **Aramaic Targum Onkelos**: query Sefaria API per book → 187 chapters; reuse Hebrew normaliser.
- [ ] **Mishnah**: query Sefaria API per tractate → 524 chapters; reuse Hebrew normaliser.
- [ ] **Old Norse Edda**: scrape heimskringla.no → 35 poems; Latin 31 with æ/ø/þ/ð.
- [ ] **Tibetan Kanjur**: BuddhaNexus API → choose 100–500 texts as random sample.

After 7 acquisitions: pool grows from 11 → 18. Two more (Coptic, Vulgate, Mishnah, Targum) take it to 22 — the FN13 floor break.

## 6. Honest scope

- This manifest does NOT acquire data; it documents what acquisition would entail.
- Some Tier-2 sources (Akkadian, Sumerian) require lemmatised cuneiform transliterations that may have non-trivial encoding choices affecting alphabet size. Treat each one as a separate experiment.
- If a corpus is acquired but its 5-feature medians ALSO place it as multivariate-extremum (rank 1 over Quran), F72 verdict flips to FAIL — this is the project's pre-committed honesty test. The hypothesis is *not* "Quran always wins"; it is "Quran wins under D_QSF in a sufficiently large pool".

## 7. Pre-registered re-run (frozen at this manifest's seal)

When N ≥ 22 is reached, re-running `experiments/exp120_unified_quran_code/run.py` produces a fresh receipt. The pre-registered decision rule is:

| Verdict | Condition |
|---|---|
| `PASS_unified_quran_code_F72_promoted_strength_85` | Quran rank 1 AND `perm_p < 0.05` AND margin > 0.5 |
| `PARTIAL_quran_rank_1_perm_p_above_0p05` (unchanged) | Quran rank 1 AND `perm_p ≥ 0.05` |
| `FAIL_quran_dethroned_under_DQSF_with_extended_pool` | another corpus has higher D_QSF; F72 retracted to a new R-row |

The PREREG hash of this manifest is committed in `experiments/exp120_unified_quran_code/PREREG.md` §10 as the locked re-run condition.

---

**Filed**: 2026-04-29 afternoon (V3.12 deliverable #3)
**Owner**: human researcher (must acquire data; harness ready)
**Cost to project (cascade-side)**: zero compute; only manifest + harness scaffolding.
