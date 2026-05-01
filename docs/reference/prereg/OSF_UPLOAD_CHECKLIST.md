# OSF Pre-Registration Upload Checklist

**Purpose**: Deposit the frozen v7.3 pre-registration packet to OSF and capture a permanent DOI **before** any arXiv submission. Once the preprint is posted without a registered pre-registration DOI, the "prospective-registration" claim is lost forever.

**Blocker**: 15 minutes of user time with an OSF account. No code change needed.

---

## 1. Pre-flight verification

Already done and verified as of 2026-04-22:

| Item | Path | Status | SHA-256 |
|---|---|---|---|
| Deposit zip | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\arxiv_submission\osf_deposit_v73\qsf_v73_deposit.zip` | ✅ exists | `794FBE4B32BC79E29742032788D94C33F39D247711922B26240A2A5601295F0F` |
| Manifest | `@c:\Users\mtj_2\OneDrive\Desktop\Quran\arxiv_submission\osf_deposit_v73\osf_deposit_manifest.json` | ✅ exists | documented inside |
| File count | 26 files | ✅ | — |
| Total bytes in zip | 240 375 | ✅ | — |
| Pre-reg doc | `arxiv_submission/preregistration_v73_addendum.md` | ✅ inside zip | `caf956f4…` |
| Live pre-reg JSON | `results/integrity/preregistration.json` | ✅ inside zip | `d9cf2b3c…` |
| Overall deposit fingerprint | see manifest `overall_sha256` | ✅ | `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205` |

Sanity command if you want to re-verify before uploading:

```powershell
Get-FileHash "C:\Users\mtj_2\OneDrive\Desktop\Quran\arxiv_submission\osf_deposit_v73\qsf_v73_deposit.zip" -Algorithm SHA256
# expected: 794FBE4B32BC79E29742032788D94C33F39D247711922B26240A2A5601295F0F
```

If the hash does **not** match, re-run the deposit builder (`arxiv_submission/osf_deposit_v73/build_deposit.py` or equivalent) before uploading.

---

## 2. OSF upload steps (15 min)

### 2.1 — Create / sign in

1. Go to https://osf.io
2. Sign in (or create an account with your institutional email — do NOT use a personal gmail if avoidable, because institutional email improves the registration's credibility).
3. Click **"Create new project"**.

### 2.2 — Project metadata (copy-paste ready)

| Field | Value |
|---|---|
| **Title** | `QSF v7.3 — Quranic Structural Fingerprint: pre-registration + integrity-locked code state` |
| **Description** | Pre-registered analysis plan and frozen code-state for the QSF pipeline, v7.3 release. The deposit contains the live `results/integrity/preregistration.json`, the post-hoc code-state lock document, and byte-exact copies of every experiment script used to produce the v7.3 locked scalars. Overall deposit SHA-256 = `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`. Companion paper posted at arXiv [TBD-after-OSF]. |
| **Category** | `Data` (or `Project` — either works; `Data` makes the deposit more discoverable) |
| **Tags** | `pre-registration`, `stylometry`, `Arabic`, `Quran`, `reproducibility`, `SHA-256`, `integrity-lock` |
| **License** | `CC-BY 4.0` (standard for OSF deposits that you want citable) |
| **Public?** | **Yes** — the whole point is citability. |

### 2.3 — Upload the deposit zip

1. In the project, click **"Files"** → **"OSF Storage"** → **"Upload"**.
2. Upload `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip` (240 KB).
3. Upload `arxiv_submission/osf_deposit_v73/osf_deposit_manifest.json` as a separate top-level file (so auditors can see the manifest without unzipping).

### 2.4 — **Create a Registration** (this is the critical step)

A plain OSF project gets a DOI, but only a **Registration** is time-stamped and immutable. The DOI of a bare project can in principle be edited; the DOI of a Registration cannot.

1. From the project page, click **"Registrations"** tab → **"New registration"**.
2. Choose the schema **"Open-Ended Registration"** (simplest; no schema-specific Q&A required).
3. Under "Registration metadata" paste a short summary:
   > *Pre-registration of the QSF v7.3 analysis pipeline. Deposit contents are
   > integrity-locked via SHA-256; overall deposit fingerprint is
   > `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`.
   > The frozen pre-registration JSON (`results/integrity/preregistration.json`)
   > defines all headline scalar names, tolerances, and pre-reg verdict labels
   > used in the companion paper.*
4. Attach the same two files (they will be included automatically from the parent project).
5. Submit. OSF will mint a DOI of the form `10.17605/OSF.IO/ABCDE`.

### 2.5 — Record the DOI

Once minted, fill it into the placeholder in `docs/PAPER.md` (see §3 below). Also add it to:

- `README.md` top — under "Cite as"
- `CHANGELOG.md` v7.7 entry — one line
- `results/integrity/preregistration.json` — a new top-level field `"osf_registration_doi"` (this is a metadata addition, not a scalar change; does not trigger results_lock drift)

---

## 3. Placeholder inserted into PAPER.md

Already added to `docs/PAPER.md` in the "Run of record" header line and the Reproducibility section. Search for the string `OSF_DOI_PENDING` and replace with your minted DOI:

```
OSF pre-registration DOI: OSF_DOI_PENDING (upload pending; deposit SHA-256 = 2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205)
```

After upload:

```
OSF pre-registration DOI: 10.17605/OSF.IO/ABCDE (uploaded YYYY-MM-DD; deposit SHA-256 = 2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205)
```

---

## 4. Why this matters (one paragraph for any co-author or reviewer)

A journal-style pre-registration claim hinges on the **order** of two events: (a) the analysis plan being stamped, (b) the results being publicly reported. If (a) precedes (b), the author can defensibly say "I pre-specified my analysis". If (b) precedes (a), the author cannot — the stamp is *retrospective* by construction. OSF issues a time-stamped immutable DOI the moment a Registration is submitted, which is the cheapest and most widely-accepted proof-of-(a). This deposit has been built, SHA-locked, and sitting on disk since 2026-04-20; the only thing preventing a formal "pre-registered" claim is the act of clicking **Submit** on the OSF Registration form. Doing so **before** posting any arXiv preprint is what converts a de-facto pre-registration into a de-jure one.

---

## 5. After-upload housekeeping (5 min)

Once the DOI is live:

1. Replace every `OSF_DOI_PENDING` string in `docs/PAPER.md` and `README.md` with the real DOI.
2. Add an entry to `CHANGELOG.md` under v7.7 or the next version:
   > `- OSF pre-registration deposited at <DOI> on YYYY-MM-DD. Deposit SHA-256 and file list in arxiv_submission/osf_deposit_v73/osf_deposit_manifest.json.`
3. Commit the three edits with message:
   > `OSF pre-reg DOI: <DOI>`
4. NOW you can arXiv-submit. The preprint's own DOI will cite the OSF DOI via `\href{}` in the first footnote.

---

*Prepared 2026-04-22. Blocker owner: user with OSF account access. Expected wall-clock time from now to minted DOI: 15 min.*
