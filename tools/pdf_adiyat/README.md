# Adiyat PDFs — Custom Build

Two custom PDFs about Surah Al-Adiyat, replacing the four in `Downloads/`:

| File | Size | Pages | Purpose |
|---|---|:-:|---|
| `out/Adiyat_Infographic.pdf` | A3 landscape | 1 | Infographic-first visual summary (poster) |
| `out/Adiyat_Analysis.pdf`    | A4 portrait  | 6 | Medium-depth Arabic explanatory reading |

Both share the same visual system (palette, typography, components) and draw their content directly from `docs/reference/adiyat/ADIYAT_AR.md`, `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md`, and `docs/reference/findings/RANKED_FINDINGS.md`.

---

## How to build

### Option 1 — run the script (recommended)

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

or, to open the PDFs as soon as they're done:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -OpenWhenDone
```

The script finds Microsoft Edge (or Chrome) automatically and converts each HTML source to a PDF in `out/`. No Python, no pip, no Node.

**First run needs internet** so Google Fonts (Amiri, Amiri Quran, Reem Kufi, Inter) can download. After that, Chromium caches them and the script works offline.

### Option 2 — print from browser manually

Open either HTML file in Edge or Chrome, then `Ctrl+P`:

- `poster.html`   â†’ Page size **A3**, Orientation **Landscape**, Margins **None**, Background graphics **ON**
- `analysis.html` â†’ Page size **A4**, Orientation **Portrait**,  Margins **Default**, Background graphics **ON**

Both HTML files carry `@page` CSS so the browser will usually auto-pick the right size and orientation.

---

## Files

```
tools/pdf_adiyat/
â”œâ”€â”€ poster.html        # A3 landscape, single-page infographic (Arabic RTL)
â”œâ”€â”€ analysis.html      # A4 portrait, 6-page explanatory study (Arabic RTL)
â”œâ”€â”€ build.ps1          # headless-Edge/Chrome builder
â”œâ”€â”€ README.md          # this file
â””â”€â”€ out/               # generated PDFs land here
    â”œâ”€â”€ Adiyat_Infographic.pdf
    â””â”€â”€ Adiyat_Analysis.pdf
```

---

## Editing

Both HTML files are self-contained (CSS embedded, only external asset is Google Fonts). To tweak a number, wording, or layout just edit the HTML and re-run `build.ps1`.

Design tokens (colours, spacing, fonts) live at the top of each file inside `:root { ... }` — edit once, everything updates.

---

## Design notes

- **Palette**: warm cream paper (`#FAF7F0`), deep teal ink (`#0E5E6F`), muted gold accents (`#B8862F`), with coloured states for success / warn / flag.
- **Typography**: Reem Kufi for headings, Amiri for Arabic body, Amiri Quran for the verse itself, Inter for numerals and Latin.
- **No emojis**, no visual noise — editorial/academic aesthetic.
- **Print-colour-adjust: exact** so gradients and fills survive the PDF pipeline.
- Running **page header/footer** on the analysis PDF, none on the poster.
