# Design note: real text in PDFs

**Status:** decided (D-043 = D, by the maintainer, 1 Oct 2026). Evidence: spike S-093
(`spikes/09_pdf_text/`). Built in Sprint 10 (S-094). Contract row T15 in
[Semantic_Contract.md](Semantic_Contract.md); it lifts the PDF half of T2's known limitation.
Code: `funground/export/pdf_text.py`, the `pdf_text` hook in `funground/renderers/cairo2d.py`,
`_write_pdf` in `funground/export/__init__.py`, `Glyph.cluster` and `TextRun.placements` in
`funground/typography.py`.

## The problem

funground draws text as glyph outlines ([Text_Subsystem_Note.md](Text_Subsystem_Note.md)). That
gives the same look on every machine, but a PDF made that way holds no text: nothing can be
selected, searched, copied or read aloud. It is also large, at about 110 bytes per character,
because every letter is a full path.

We want real text in the PDF, with funground's own fonts and HarfBuzz shaping. It must sit at
exactly the place the outlines would: same stacking order, transform, clip, colour or gradient,
opacity and blend mode.

## Why this is awkward

- **Cairo cannot embed our fonts.** The pycairo wheel has no FreeType and no way to load a font
  file (spike, route 1a). Cairo's toy font API picks a system font by name, so it is
  machine-dependent and wrong.
- **Text can't simply be added on top afterwards.** The spike's invisible layer works, but visible
  text added afterwards would lose the stacking order and every clip, blend and opacity that
  applied to it.

## The route

```text
 IR Text op ──► CairoRenderer (pdf_text set)
                  push_group · clip(marker) · set source (colour/gradient) · paint · pop · paint
                  └─► PdfTextCollector.add(run, x, y, matrix)  → records glyphs, font, location
 surface.finish() ──► Cairo's PDF: each run is its own Form XObject, at the right place in the
                      stream, inside the right clip / blend / opacity, with the marker as a clip path
 PdfTextCollector.finish(path)  (pypdf)
     walk pages, XObjects (nested), patterns, soft masks
     find each marker clip · decode its run number · read the transform from its corners
     replace the marker with  BT … 7 Tr (glyphs, each with its own Tm) ET   ← text becomes the clip
     embed one font subset per (font file, variation location) per document
```

1. **Marker groups.** With `renderer.pdf_text` set (only by the PDF export path), the `ir.Text`
   branch draws a group: it clips to a marker shape, sets the run's paint exactly as the outline
   fill would, and paints. Cairo keeps each group as its own XObject, in draw order, with the outer
   clip, blend mode (`/BM`) and opacity (`/CA`) on the way in. A gradient becomes a shading inside
   the group.
2. **Swapping in the text.** After Cairo finishes, pypdf rewrites each XObject. The marker's clip
   path is replaced by the run's glyphs in text render mode 7 (add to clip). Whatever Cairo painted
   next (a colour, a gradient) now fills exactly the glyphs.
3. **The marker carries its own transform and id.** Cairo writes paths with its transform built
   into the coordinates. The marker is a four-sided shape P0, P1, Q, P2:
   - P0, P1 and P2 give the full affine map from user space to the XObject's space, including
     rotation, skew, Cairo's page flip and the group's shifted origin.
   - Q = P0 + a(P1 − P0) + b(P2 − P0) encodes the run number in (a, b) on a 0.001 grid. That is up
     to 160 000 runs per file, and any beyond fall back to outlines. Affine maps preserve a and b,
     so the id reads back under any transform.

   A rectangle would not do: Cairo writes an axis-aligned rectangle clip as `re`, cut to the page,
   which loses the corners. As a safety check, the decoded map must agree with the matrix recorded
   at draw time.
4. **Fonts.**
   - **TrueType:** Type0 + CIDFontType2, Identity-H, `/CIDToGIDMap /Identity`, subset with
     `retain_gids`, widths from `hmtx`.
   - **CFF `.otf`:** Type0 + CIDFontType0 with `FontFile3 /Subtype /OpenType`.
   - **Variable fonts:** instanced at the run's location with `fontTools.varLib.instancer`, then
     subset; one embedded font per location.
5. **Copy and search.**
   - A ToUnicode CMap maps glyphs to characters, so a ligature copies as its letters.
   - Glyphs are written in logical (reading) order, each placed by its own `Tm` at HarfBuzz's
     position.
   - Right-to-left runs, clusters of several glyphs, and glyphs whose meaning differs elsewhere in
     the document also get an `/ActualText` span. Without it, pdfium swapped the words of two-word
     Hebrew and Arabic and read an accent's glyph id as a character.
6. **Fallbacks**, all silent and all drawing exactly the old outlines:
   - the font forbids embedding (`fsType` bit 0x0002), per run;
   - a CFF2 variable font, or a font that can't be embedded;
   - any error in `finish()`: `_write_pdf` draws the whole document again as outlines.

   A PDF with no text keeps Cairo's bytes untouched.

## Why not the alternatives

| Option | Why not |
|---|---|
| Keep outlines (D-006) | No selection, search, copy or accessibility; files about 10× larger |
| Invisible text layer over the outlines (D-043 A, the spike's route) | Text is "ghost" text, selectable even where it's covered or clipped; files keep the outline size. The maintainer preferred real text |
| Split Cairo's output into layers with our text between them | Has to reproduce clips, transforms, blends and opacity by hand; the marker route gets all of them from Cairo for free |
| Skia's PDF backend | 11 MB native dependency, a second renderer for every op; ligatures and Arabic copy out as presentation forms (spike, route 3b) |
| reportlab, fpdf2, PyMuPDF | More weight, LGPL or AGPL, or wrong RTL order (spike, routes 2c, 2d, 3c) |

## Invariants

- Window, PNG and SVG output are byte-for-byte unchanged; no golden or snapshot moved.
- No IR or public API change. `text_path` (F13) is still a path.
- Shadows of text stay shapes: `_draw_shadow` uses the outlines.
- The renderer never imports pypdf; only `funground/export/` does (boundary test).

## Measurements (Windows 11, S-094)

- **Size:** a 50-line page of 73 characters is 59.7 KB with real text, against 620 KB as
  outlines.
- **Looks:** rendered by pdfium at 4×, compared with the outline PDF: mean difference ≤ 0.11 (the
  limit is 0.3). A half-pixel shift gives ≥ 0.66, and a missing glyph gives 255 in a cell, so the
  test would catch both.

## Limits and follow-ups

- **Rectangular glyphs ("l", "I", "-") differ by up to one device pixel between real-text and outline
  PDFs in pdfium (Chrome, Edge), and it is the *outline* PDF that is off.** Measured in Sprint 13
  (S-109), against Cairo's own drawing of the same frame: clip-mode text matches it (ink ratio 1.00,
  mean difference ≤ 0.17), while pdfium draws the outline PDF heavier (ink ratio up to 1.80 at 1×),
  because it snaps rectangular fill paths outward. Fill mode (`0 Tr`) was built, measured and dropped:
  it came out heavier than clip mode. Nothing to fix; the tests compare against the outline PDF, so
  their worst cells show pdfium's error, not ours.
- **Viewers draw the glyphs themselves,** with their own hinting: the look matches within
  anti-aliasing, not pixel for pixel.
- **pypdf's own `extract_text` reverses Hebrew and Arabic.** pdfium and MuPDF read them correctly.
  Acrobat, macOS Preview and pdf.js (Firefox) have not been tested.
- **pypdf rewrites the whole file,** and we use one private call, `PdfWriter._add_object`. Pin the
  pypdf version range if that call changes.
- **SVG output still draws text as shapes.** Real `<text>` in SVG would be its own story.
- **Silent fallback could hide a regression.** The tests assert that fonts are present.

## Tests

`tests/test_pdf_text.py` (29 tests):
- extraction with pypdf and pdfium: ligatures, tracking, `text_box`, `FormattedString` with two
  fonts, a loaded font, a variable font at two weights, CFF, accents, RTL;
- rendering compared with the outline PDF: rotated, skewed, clipped, blended, gradient, covered by
  a shape, with a shadow, inside nested pictures; plus a control showing the comparison catches
  errors;
- fonts embedded once in a multi-page document;
- fallback for an `fsType`-restricted font;
- file size.

Test fonts are generated by `tests/fontmaker.py` (`make_static_font`); none are downloaded.
