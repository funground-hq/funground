# Sprint 21 review — typographic, print-ready posters (E-32)

**Dates:** 11–12 October 2026, on `release-0.2-web` (merged to `main` with S-177; released in 0.1.0a1).
**Not yet signed off.**

## Outcome

Goal met: a learner can set a typographic poster (justified and hyphenated text, type on a curve, a fitted
headline) and hand a print shop an A-size PDF with bleed, crop marks and exact CMYK inks, or a 300 dpi PNG.

| Story | Result | Commit |
|---|---|---|
| S-162 Fitted headlines | `f.fit_text_size(message, width, height=None)` (T21), example `text-11_fitted_headline` | `f3a9720` |
| S-164 Print-ready PDF | `save(..., bleed=, marks=True)`: bleed, crop marks, TrimBox and BleedBox (D2) | `f3a9720` |
| S-163 Print resolution | `save("poster.png", dpi=300)`, pHYs written, 120-megapixel limit (D3) | `f3a9720` |
| S-159 Justified text | `text_align("justify")` in `text_box` (T22); the last line stays left | `f6494eb` |
| S-160 Soft hyphens | `text_box` breaks at the last soft hyphen that fits (T23, D-085 = a) | `f6494eb` |
| S-161 Type on a path | `f.text_on_path(message, path, offset=0)` (T24); live text per letter in PDF and SVG | `048119a` |
| S-171 Fractional text sizes | sizes keep their fraction (T3, T21); shaping cached per text, rescaled per size: benchmark (400 letters, 120 frames) 2.4–2.6 s with fractional sizes, was 5.1 s | `b1d7797` |
| S-165 Spike: CMYK and PDF/X | `spikes/11_cmyk/RESULTS.md`: rewrite to CMYK works but is not colour-managed; littleCMS not in Pyodide; no CMYK profile can be bundled | `a67f759` |
| S-170 CMYK colour model | `f.cmyk(c, m, y, k)` (S17); exact DeviceCMYK in PDFs, checked by read-back; RGB tagged sRGB with an output intent; marks in registration (D4, D5) | `2b5822d`, `2059bcd` |
| S-166 Teaching | chapter 6 sections, chapter 13 "Preparing a file for print", Event posters stage 4 (A3, print-ready), glossary | `533964f` |

**Tests:** full suite 3819 (S-162/163/164) → 3880 (S-159/160) → 3904 (S-171) → 3946 (S-161) → 4008 (S-170) →
4014 passed (S-166; guide tests 287 passed after the CMYK note). Four new gallery examples with goldens.

**Goldens changed on purpose (S-171, as the story planned):** `text-11_fitted_headline` (golden and
snapshot) and `projects-05_typographic_portrait` (golden), because sizes stopped being rounded to whole
points. Every whole-size drawing stayed byte-identical.

## Decisions

- **D-085 = a** soft hyphens only (dictionary hyphenation is S-169 in the backlog).
- **D-086:** the poster features ship with 0.2 (in practice with 0.1, by D-091).
- **D-087 = e + b:** CMYK as a colour model (`f.cmyk()` only, no colour mode: D-017 stands), RGB tagged sRGB.

## Findings that change later work

1. **funground's A3 is 842 x 1191 pt**, so a 300 dpi A3 PNG is 3508 x 4963 px; true A3 would be 4961. A rounding
   choice in the page-size table, harmless for print shops, worth a line in chapter 13 if anyone asks.
2. CMYK in PDFs works by stand-in colours swapped after Cairo. It is exact and checked on read-back, but it is
   a pypdf rewrite: a failed rewrite deletes the file and raises rather than writing wrong inks.
3. Text on a path defaults to vertical alignment "top", like `text()`; the maintainer may still want "baseline".

## Built by

Not recorded at the time; the commits are the main session's.

## Retrospective

- Ordering the small, dependency-free stories first (S-162, S-164) gave usable posters on day one.
- The spike before S-170 stopped a heavier design (colour-managed conversion) that could not have run in the
  browser.
- S-171 changed goldens on purpose; doing it as its own story, with the reason in
  the commit, kept the reference trustworthy.
