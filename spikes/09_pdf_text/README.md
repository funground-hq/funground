# Spike S-093: selectable, searchable text in funground PDFs

Research only. Nothing outside this folder was changed. Date: 1 October 2026.
Question: can funground's PDFs carry real text (select, search, copy) without giving up the
exact look that D-006 bought us (text drawn as glyph outlines)?

## Answer in one paragraph

**Yes, with one new dependency, `pypdf`.** Keep drawing outlines for the look. After Cairo has written
the PDF, a post-processing step adds an *invisible* text layer (PDF text rendering mode 3, the same
trick scanned-document OCR uses) on top of the outlines, using HarfBuzz's own glyph ids and positions.
In the experiment the page looked **pixel-for-pixel identical** (0 differing pixels at 4x), the text
copied out correctly (including the `fi` and `ffi` ligatures and Hebrew and Arabic words), search
found every word in Chrome/Edge's engine (pdfium) and MuPDF, and the cost was about **+6% file size**
on a text-heavy page. No route that uses Cairo's own font support works, because the pycairo wheel
cannot load a font file at all. Recommendation is in section 4.

## 1. Results by route

"Engines" below are the four independent extractors I ran on every PDF: **pypdf** `extract_text`,
**PyMuPDF** (MuPDF; also behind SumatraPDF and many others), **pdfminer.six**, and **pypdfium2**
(pdfium, the engine inside Chrome and Edge). All run in the throwaway venv.

| # | Route | Works? (evidence) | New dependencies (licence, size) | Effort | Risks |
|---|---|---|---|---|---|
| 0 | **Today: outlines only** (baseline, `exp0`) | Looks right. No text: all four engines extract `''`, zero search hits, no fonts in the file. 10.2 KB for the 4-line test | none | none | The D-006 limitation: no select, search, copy, accessibility |
| 1a | **Cairo font face from a TTF file** (`exp1`) | **No.** pycairo 1.29.1 on Windows: `cairo.HAS_FT_FONT == 0`; the only face classes are `FontFace` (abstract) and `ToyFontFace`; there is no file-path factory. Cairo is statically linked into `_cairo.pyd` with no FreeType, user-font or Win32 face symbols, so `ctypes` cannot reach one either | none | not buildable | Dead end |
| 1b | **`ToyFontFace("DejaVu Sans")` + `show_glyphs` with HarfBuzz ids** (`exp1`) | **No.** DejaVu is not installed on this Windows machine, so Cairo silently substituted Arial; HarfBuzz's DejaVu glyph ids then index Arial's glyphs and the extracted text is garbage (`'� o�ce'`). The PDF embeds Arial, not DejaVu. A missing family also silently falls back to Arial, with no error | none | n/a | Machine-dependent output, wrong glyphs, breaks the "same on every machine" rule (T2) |
| 1c | `ToyFontFace` + `show_text` (let Cairo shape) | Text is extractable (`'fi office'`) but in the OS's font (Arial here), shaped by the OS, not HarfBuzz; positions differ from our outlines; no learner fonts | none | n/a | Same objection as the Text Subsystem Note gives |
| 2 | **Invisible text layer added after Cairo, by our own code + pypdf** (`exp2`, variants A/B/C) | **Yes.** Variant B (glyphs written in logical order, each placed by its own text matrix): all four engines find `office` and `Search`; MuPDF, pdfium and pdfminer give correct Hebrew and Arabic in reading order and find the words; **pypdf** gives them reversed (see 3.4). Ligatures: HarfBuzz produced glyphs `fi` and `uniFB03` (ffi); they copy as `fi` and `ffi`, so `office` is found. Look unchanged: 0 differing pixels. Text boxes sit within 0.5 to 2.3 pt of the ink (side bearings) at 24 px (`exp4`). Size: +3.9 KB on the 4-line page, **+14.4 KB (+6%) on a 40-line page** (`exp5`) | **pypdf**: BSD-3, pure Python, 395 KB wheel (4 MB installed), no dependencies. Also `fontTools` (already a dependency) for subsetting | **M** | See section 3 |
| 2b | Same, with **pikepdf** instead of pypdf | Not run (same job as route 2, I judged it not worth a second implementation). pikepdf can write the same objects | pikepdf: MPL-2.0, 3.9 MB wheel, pulls in `lxml`, `Pillow`, `packaging` (about 4 MB installed plus those) | M | Heavier and more transitive packages than pypdf for no gain here |
| 2c | Same, but **reportlab** writes the invisible text and embeds the TTF, merged onto Cairo's page with pypdf (`exp6` C) | **Yes** for Latin; for Hebrew and Arabic the same pattern as route 2 (pdfium, MuPDF, pdfminer right; pypdf reversed). Embeds a DejaVu subset. Costs **+32.9 KB** on the 4-line page (2.5x route 2 on that page, subset is not compact) and leaves a non-embedded `Helvetica` reference in the file | reportlab: BSD, 2.0 MB wheel, 9 MB installed, pulls `Pillow`, `charset-normalizer`; plus pypdf | M | Needs pypdf anyway; saves only about 40 lines of font and CMap code and adds more weight |
| 2d | Same, with **fpdf2** (`exp6` D, `INVISIBLE` text mode, its own HarfBuzz shaping) | **Partly.** Latin copies and searches fine, +16.6 KB. Hebrew and Arabic are written in visual order, so 3 of 4 engines return them reversed and the search misses; would need pre-reversed strings | fpdf2: **LGPL-3.0**, 341 KB wheel; pulls `Pillow`, `defusedxml`; plus pypdf | M | LGPL is a licence question for a PyPI package; RTL needs work |
| 3a | **Cairo PDF tagging** (`tag_begin`, `exp7`) | **No.** Cairo 1.18 only offers `TAG_CONTENT`, `TAG_LINK`, `TAG_DEST`; with them the output has no structure tree, no `ActualText`, and no text-show operator, so nothing is extractable | none | n/a | Dead end |
| 3b | **Skia as the PDF backend for text** (`skia-python`, `exp8`) | **Works for plain text** (real embedded Type0 DejaVu, 7.8 KB), but ligatures and Arabic come out as presentation-form characters (`ﬁ oﬃce`, `ﻣﺮﺣﺒﺎ`), so searching `office` or `مرحبا` fails in 3 to 4 of 4 engines (only pdfium normalises them). Hebrew order is wrong in pdfminer. Skia has no invisible mode (a transparent paint is skipped), so it cannot be a text-only overlay; it would replace Cairo for PDF entirely | skia-python: BSD, **11 MB wheel, ~15 MB installed**, new native dependency; pybind11 | **L** to XL (a second renderer for every IR op; D-011 chose Cairo for exports) | Biggest change, worst copy-out quality of the working routes |
| 3c | **PyMuPDF** to insert text | Not built; it could do the job but is **AGPL-3.0** (or commercial), which is unacceptable for a permissive PyPI package. Used here only as a test-time extractor, never as a recommendation | 20 MB wheel, 55 MB installed | n/a | Licence |

Effort scale: S = under a day, M = one story of a few days with tests, L = a sprint.

## 2. What each experiment shows

Run all with `sh run_all.sh` (creates `.venv` if missing). Output of my last run is in `out/run_all.txt`;
the PDFs are in `out/`. Every script is a few dozen lines and imports `common.py`
(HarfBuzz shaping, a Cairo outline drawer that mimics funground's own, and the four-engine `report()`).

| Script | What it does |
|---|---|
| `exp0_baseline.py` | Outlines-only PDF, as funground produces today. Nothing extractable |
| `exp1_cairo_faces.py` | Probes pycairo for a file-based font face; tries `ToyFontFace` + HarfBuzz glyph ids; shows `show_text` |
| `exp2_invisible_layer.py` | The recommended route: subset the TTF, write `Tr 3` text, merge with pypdf. Three variants: A one `TJ` in visual order, B per-glyph text matrix in logical order (best), C = B plus `/ActualText` (no benefit in any engine tested) |
| `exp3_check_ligatures.py` | Confirms DejaVu makes real `fi`, `ffi` and joined Arabic glyphs, so the copy test means something |
| `exp4_positions.py` | Renders outlines-only and layered at 4x: pixel diff, and text-box versus ink x-extent |
| `exp5_size.py` | File-size cost on 40 lines / 2,030 characters |
| `exp6_library_overlays.py` | reportlab and fpdf2 as overlay writers |
| `exp7_cairo_tags.py` | Cairo's tagging API (dead end) |
| `exp8_skia_pdf.py` | Skia as an alternative PDF text backend |

## 3. Details that matter for the recommended route (2)

1. **How it works.** (a) While replaying text for a PDF, record each text run: string, font file, size, baseline
   origin, the current transform, and HarfBuzz's glyph ids and positions (funground already has all of
   these in `TextRun`; its `outline_ops` is where the outlines are made). (b) After `surface.finish()`, open the
   file with pypdf and append one extra content stream per page, wrapped so Cairo's stream is untouched.
   (c) Embed one subsetted DejaVu (fontTools, `retain` only used glyphs) as a Type0 / CIDFontType2 font with Identity-H,
   plus a ToUnicode CMap that maps each glyph id to the text of its HarfBuzz cluster. That mapping is what
   makes the `fi` ligature glyph copy as "fi" and a joined Arabic glyph copy as the plain letter.
2. **Cairo's content stream is not balanced.** It begins with `1 0 0 -1 0 H cm` and never undoes it. My first version
   inherited that flip and the text box landed on the wrong line; wrapping Cairo's stream in `q ... Q` fixes it.
   (The invisible layer must use the same transform as the visible text; for rotated or scaled text put the
   current matrix into `Tm`. **I did not test rotated or skewed text.**)
3. **Order of glyphs.** HarfBuzz returns right-to-left runs in visual order. Writing them that way makes
   pdfium and MuPDF return reversed Hebrew and Arabic. Writing glyphs in *logical* order (reverse for RTL), each at
   its visual position by its own `Tm`, gives correct copy and search in pdfium, MuPDF and pdfminer. `/ActualText` did not change any result.
4. **pypdf's own `extract_text` reverses RTL words in the logical-order file** (and is right for the visual-order
   file). It is the one engine of four that disagrees. pypdf is not what users copy with; Chrome, Edge, Acrobat,
   Preview and Sumatra are. But Acrobat, Preview and pdf.js were **not tested**; the choice between
   visual and logical order cannot be settled without them. Logical order is the PDF-standard expectation
   (copy follows content-stream order) and matches pdfium, the most widely used engine.
5. **Size.** Fixed cost about 3.5 KB (the subset font and CMap) plus about 5 bytes per character after compression.
   Today's outlines already cost about 110 bytes per character (a full path per glyph), so the layer is small.
6. **Mixed-direction lines** (Latin and Hebrew in one string) were not tested. I put each script on its own line, because
   funground shapes a run as one direction (HarfBuzz `guess_segment_properties`) and does no bidi splitting;
   that is a drawing question for T2, not for this spike, and the invisible layer simply mirrors whatever is drawn.

## 4. Recommendation

**Adopt route 2 as an optional, default-on PDF step: invisible text layer written by funground, using `pypdf`
(BSD, pure Python, 0.4 MB) as the only new dependency.** Do not use Cairo font faces (impossible), Skia (heavy, and ligature/Arabic copy-out fails),
fpdf2 (LGPL, RTL wrong), reportlab or pikepdf (more weight for no gain).

Why this route: it keeps D-006's guarantee that the visible page is exactly the outlines (verified identical, 0 pixel
difference), adds real text with correct ligature and RTL copy-out in Chrome/Edge's and MuPDF's engines, costs
about 6% in file size, reuses `fontTools` and `uharfbuzz` which funground already depends on, and the dependency is
pure Python, so there is no wheel risk on Python 3.14 or Windows.

Effort: **M.** About 150 lines (font subset and CMap, content stream writer, merge), a hook in the Cairo renderer that
collects text runs for PDF targets (single PDFs, `save_document`, and `save_picture` replay), tests that extract
text with pypdf or pdfium, and a guide note. Follow-ups, each separate: loaded OpenType/CFF `.otf` fonts (needs
a CFF-flavoured embed), variable fonts (subset at the chosen axis location), `text_tracking`, and mixed-direction strings.

**What the maintainer would have to decide (D-034):**
1. **Add `pypdf` as a runtime dependency?** The alternative is no new dependency by writing the PDF
   objects ourselves as an incremental update (about 100 more lines and a real chance of subtle PDF bugs); I advise against it.
   Also note pypdf rewrites the whole file on save (it did not enlarge Cairo's output in my runs).
2. **Optional extra or always on?** One option is `pip install funground[pdf-text]` with silent fallback to
   outlines when pypdf is absent; that keeps the core light and respects D-006.
3. **Font licences.** A subset of the font is embedded. DejaVu allows it. For a learner's `load_font` file, honour the
   font's `fsType` embedding bits (skip the layer when embedding is forbidden), and say so in the guide.
4. **"Ghost text" behaviour.** The text layer can be selected even where the outlines are covered by another shape or
   clipped away, exactly like OCR'd scans. Acceptable for sketches? Decide whether to hide runs that are fully clipped.
5. Which **contract rows** change: T2's "known limitation" line and T11 ("stays vector in PDF/SVG"), and whether SVG gets the same
   (SVG would use `<text>` with `opacity=0`; not investigated here).

If the maintainer prefers no new dependency and no extra code, **keeping outlines (D-006) remains a valid outcome**;
nothing here is needed for correctness, only for selection, search, copy and accessibility.

## 5. What I could not test

- Real viewers: Acrobat, macOS Preview, pdf.js (Firefox) and interactive selection by mouse. pdfium (pypdfium2) stands in for Chrome and Edge;
  MuPDF for Sumatra.
- Rotated, skewed or clipped text, text inside `with saved_state()` transforms, multi-page documents (`save_document`),
  `save_picture`, and an actual change to funground (the spike calls fontTools and HarfBuzz directly and draws outlines like the renderer does).
- `.otf` (CFF) and variable fonts; DejaVu Bold, Oblique and Bold Oblique (same file format, expected identical).
- Mixed-direction strings; combining marks with vertical offsets (the layer ignores `y_offset` of marks beyond a per-glyph `Tm`
  y, which I did pass but did not check visually).
- pikepdf (judged by metadata only), PyMuPDF insertion (excluded on licence), SVG output.
- Linux and macOS: only Windows 11, Python 3.14, pycairo 1.29.1 (Cairo 1.18.4). On Linux or macOS a pycairo built with FreeType
  might expose a file-based face; the wheel funground ships on PyPI for Windows does not, so no route that relies on it can be portable.

## 6. Tools used to check

pypdf 6.19 `extract_text`; PyMuPDF 1.28 `get_text` and `search_for`; pdfminer.six 20260107 `extract_text`; pypdfium2 5.13
`get_text_range` (pdfium). Rendering and pixel comparison: PyMuPDF at 4x and numpy. Throwaway venv in `.venv/` (git-ignored by
`spikes/.gitignore`); the project venv was only read to inspect pycairo.
