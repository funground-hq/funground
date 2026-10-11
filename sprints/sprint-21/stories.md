# Sprint 21 — typographic, print-ready posters

**Dates:** started 11 October 2026 (the maintainer chose to start before Sprint 20 is signed off; its review follows). On `release-0.2-web`
(a library feature; it ships with 0.2, D-086). Epic **E-32**.

**Goal:** a learner can set a typographic poster in funground (justified and hyphenated text, type on a
curve, a headline fitted to its width) and hand a print shop an A-size PDF with bleed and crop marks, or a
300 dpi PNG. Gaps found in the 11 October review of poster support.

**Decisions:** D-085 = soft hyphens only for now (no dependency); D-086 = released with 0.2 (both accepted
11 October 2026). API names follow D-034 (DrawBot's model where it fits, decided in each story and recorded as
contract rows).

| Story | Value | Status |
|---|---|---|
| S-159 | Justified text: `f.text_align("justify")` in `text_box` (the last line of a paragraph stays left), for strings and FormattedStrings | planned |
| S-160 | Hyphenation by soft hyphens: `text_box` may break a word where the learner typed a soft hyphen (U+00AD, or `"\u00ad"` in Python), showing a hyphen there and nothing elsewhere; works with justify (D-085 = a) | planned |
| S-161 | Type on a path: `f.text_on_path(message, path, offset=0)` sets letters along any path (a circle, a wave), each turned to the curve; live text in PDF and SVG | planned |
| S-162 | A headline that fits: `f.fit_text_size(message, width, height=None)` returns the size that makes the text fill the width (and fit the height) with the current font, features and tracking | planned |
| S-163 | Print resolution: `f.save("poster.png", dpi=300)` writes a page at that resolution (A3 at 300 dpi is 3508 × 4961 px), in scripts and animated sketches, on the desktop and in the browser | planned |
| S-164 | Print-ready PDF: `f.save("poster.pdf", bleed=f.mm(3), marks=True)` adds the bleed, crop marks and the PDF's TrimBox and BleedBox; `f.mm()` and `f.inch()` give lengths in points | planned |
| S-165 | Spike: CMYK and PDF/X for print shops. Can funground write CMYK (or a PDF/X file a print shop accepts) without a heavy dependency? Criteria set before the work; a recommendation | planned |
| S-166 | Teaching: guide sections (justified columns, type on a path, fitted headlines, preparing a file for print), four gallery examples, and the "Event poster series" project made print-ready | planned |

Acceptance for the sprint: the full suite green; each story's contract row(s) pinned; goldens added for the
new drawing (justified box, hyphenated box, text on a circle); a 300 dpi A3 PNG and a bleed-and-marks PDF
checked by test (sizes, boxes, marks); every new function in the Quick Reference and the guide; the new
examples run in the browser editor too.

Order: S-162 and S-164 first (small, no dependency, immediately useful), then S-159 and S-160 (line
breaking), S-161, S-163, S-166 last; S-165 runs alongside (a spike, no product code).

- [ ] S-159
- [ ] S-160
- [ ] S-161
- [ ] S-162
- [ ] S-163
- [ ] S-164
- [ ] S-165
- [ ] S-166
