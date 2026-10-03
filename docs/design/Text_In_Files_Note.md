# Design note: live text in SVG files

**Status:** built in S-097 to contract row **T19**, decision **D-059 = A**. Code:
`funground/export/svg_text.py`, the `svg_text` hook in `funground/renderers/cairo2d.py`, and
`_write_svg` in `funground/export/__init__.py`. The marker geometry is shared with PDF text
(`marker_corners`, `marker_number`, `marker_map` in `funground/export/pdf_text.py`). The PDF half
of this idea is [PDF_Text_Note.md](PDF_Text_Note.md) (T15).

## The problem

funground draws text as glyph outlines (T2). An SVG made that way looks the same everywhere, but its
text cannot be edited, found or copied. The maintainer moves SVG files between Adobe Illustrator and
Inkscape and edits them there.

## Two routes, and the choice

- **A. Live `<text>`.** Each line of text becomes a `<text>` element that names its font by family.
  The program that opens the file draws it in the installed font, and the text stays editable. A
  subset of each font is embedded as a CSS `@font-face`, so a browser shows the right font too.
- **B. Outlines plus invisible `<text>`.** Keep the outlines and lay the words over them,
  invisible. An earlier S-097 draft built this (branch `worktree-agent-a46993293e7afec42`,
  commit 2956389). It keeps the look exact, but nothing can be edited.

The maintainer chose **A** (D-059):

> "keeping the text live and having the font installed locally on the system is the absolute best
> approach when you are actively editing an SVG between Adobe Illustrator and Inkscape"

Editability comes before a pixel-exact look. Route B's draft is reused only for its marker
machinery.

### Trade-offs accepted with A

- **The look depends on the installed font.** Illustrator and Inkscape use the font installed on
  the computer, as far as we know, and do not load the embedded `@font-face`. Without the font they
  substitute another one. The guide (chapter 13) says how to install funground's bundled fonts.
- **Spacing can drift slightly.** The program that opens the file shapes the text itself, with its
  own kerning, ligatures and rounding. Each line keeps one `x` and one `y`, so the drift stays
  inside the line and never moves the line's start.
- **Complex scripts are shaped by the viewer.** Devanagari conjuncts, Arabic joining and ligatures
  come from the viewer's shaping engine. The embedded subset keeps GSUB, GPOS and GDEF with the
  glyph closure, so browsers shape them from the subset exactly as from the whole font (tested).
  Illustrator shapes Indian scripts correctly only with the World-Ready Paragraph Composer; the
  guide says so.
- **Licences.** A font whose OS/2 `fsType` forbids embedding is not embedded. Its text still names
  its family, so it stays live; a browser without that font installed substitutes another.

## How it works

```text
 IR Text op ──► CairoRenderer (svg_text set)
                  push_group · clip(marker) · paint the line's colour or gradient · pop · paint
                  └─► SvgTextCollector.add(line, x, y, matrix, style) → records the line
 surface.finish() ──► Cairo's SVG: <g clip-path="url(#marker)"><rect fill="..."/></g>, in a group
                      in <defs> drawn by <use>
 LayerMarkers.finish_svg   (S-096: layers first)
 SvgTextCollector.finish(path)
     find each marker clipPath · decode its line number · read the transform from its corners
     replace the painted <rect> by the line's <text>, taking over its fill and opacity
     move a gradient into the text's own space · drop the marker clip
     add <style> with one @font-face per font used · draw each text in place, not through <use>
```

1. **One marker per line.** One `ir.Text` op is one marker, fallback runs (T18) included, so a line
   becomes one `<text>`. The marker is the four-cornered shape P0, P1, Q, P2 of PDF text, on the
   same grid, so the line's number and transform read back the same way. The renderer paints the
   line's paint inside it, as for a PDF, instead of its outlines: there are no glyph paths to remove
   afterwards.
2. **Mapping Cairo's group to `<text>`.** The group that uses the marker clip holds one painted
   element. It is replaced by the `<text>`, which takes its `fill`, `fill-opacity` and `opacity`.
   The text's `transform` is the `marker_map` affine (user space to the space Cairo wrote the
   marker in), its offsets rounded to 0.01 (the marker's corners are on Cairo's 1/256 grid). The
   group keeps every other clip and attribute; an empty wrapper gives way to the text. Any other
   form raises, and `_write_svg` writes the file again with outlines.
3. **Gradients.** Cairo's `<linearGradient>`/`<radialGradient>` is in `userSpaceOnUse` of the
   painted element. The text has its own transform, so the gradient gets
   `gradientTransform = inverse(text transform) × painted transform × Cairo's gradientTransform`,
   and the text says `fill="url(#...)"`. A gradient used only once is changed in place; one used
   more often is copied under a new id.
4. **The `<text>` element:** `x` at the line's start, `y` on its baseline, `font-size`, and plain
   content in reading order, with `xml:space="preserve"`.
   - `font-family`: the family from the `name` table (typographic family, ID 16, else ID 1), quoted,
     then a generic family: `monospace` for a fixed-pitch font, `serif` when PANOSE says serif,
     otherwise `sans-serif`.
   - `font-weight` (`bold`, or the OS/2 weight class) and `font-style` (`oblique` or `italic`), only
     when not normal.
   - `letter-spacing` (`text_tracking`), `font-feature-settings` (`text_features`) and
     `font-variation-settings` (the variation location), only when set.
   - Fallback runs are `<tspan>` elements with their own `font-family` (and weight, style and
     variations where they differ). They have no `x`: they follow on, so an edit flows.
   - A single-font run that is right to left (its first strong character is Hebrew or Arabic, which
     is how HarfBuzz guessed its direction) gets `direction="rtl"` and `x` at its right end. The
     characters stay in logical order; nothing is reversed in the file.
5. **Single `x`, not per-glyph `x` lists.** Per-glyph positions would reproduce funground's spacing
   exactly, but Illustrator turns them into text that is hard to edit (each glyph pinned), and an
   edit in any program leaves the old positions behind. D-059 puts editing first, so each line has
   one `x` and one `y`. `textLength` is not used either: it would squeeze or stretch edited text to
   the old width.
6. **Embedded fonts.** One `@font-face` per font file used, in a `<style>` at the top of the SVG:
   the same family, weight and style as the text, and a fontTools subset holding the characters
   drawn in it, with every layout feature (`layout_features=['*']`, closure on, GSUB/GPOS/GDEF
   kept), hinting dropped. TrueType outlines as `font/ttf`, `format('truetype')`; CFF as `font/otf`,
   `format('opentype')`. `brotli` is not installed, so there is no WOFF2. A variable font is
   embedded whole-axis; `font-variation-settings` picks the instance.
7. **Out of `<use>`.** Inkscape shows text inside a `<use>` as a clone that cannot be edited, and
   browsers do not select it. Each `<use>` in the document body that leads to a text, and is the
   only reference to its group, is replaced by the group itself, nested pictures included.
8. **Kept as shapes:** text drawn while erasing (F15: the renderer draws it before asking for a
   marker) and text shadows (drawn from outlines before the line). `text_path` (F13) stays a path.
9. **Fallbacks:**
   - any error in the text step: `_write_svg` draws the file again without it, as outlines
     (exactly what funground wrote before S-097);
   - an SVG with no text is left exactly as Cairo and the layer step wrote it.

## Invariants

- Window, PNG and PDF output are unchanged; no golden or snapshot moved.
- Text in a layer (F16) stays inside its Inkscape layer group; hidden layers keep `display:none`.
- No glyph outline path is left for a line that became text.

## Measurements (Windows 11, S-097)

- **A text-heavy page** (50 lines of 73 characters, 12 px): **49.8 KB** with live text, of which
  the DejaVu Sans subset is 16.7 KB (about 22 KB as base64), against **2.83 MB** as outlines.
- **Subset sizes** for a page of four short lines (42.4 KB in all): DejaVu Sans 13.1 KB, DejaVu
  Sans Bold 11.4 KB, Noto Sans Devanagari for "नमस्ते" 4.0 KB (TTF, before base64; base64 adds a
  third). DejaVu's subsets are mostly its layout tables, kept so browsers can shape.
- **Devanagari shaping:** shaping "क्षत्रिय नमस्ते" with HarfBuzz gives the same glyph outlines and
  positions from the subset as from the whole Noto Sans Devanagari.

## Limits and follow-ups

- **Not checked in Illustrator, Inkscape or a browser.** None is installed on the build machine.
  The checks are structural: the file parses, each `<text>` has the right string, family, style,
  size, fill and settings, sits in the document body inside its clip and layer, and no outlines
  are left. A manual check in Illustrator, Inkscape, Chrome and Firefox is worth doing once,
  including whether Illustrator accepts the `<style>` block and `direction="rtl"`.
- **A line drawn with a blend mode other than normal** is drawn by Cairo through filters and masks
  in `<defs>`; its text is in the file, inside a filter's input, and may not be editable there.
- **Two different font files with the same family, weight and style** would give two `@font-face`
  rules a browser cannot tell apart.
- **A line in several fonts (T18) is laid out left to right,** run after run, as funground draws it;
  a right-to-left line with an emoji keeps that order.
- **`f.load_svg` ignores `<text>`,** so loading a funground SVG back gives no text.

## Text as shapes, per file (S-116, T20, D-060)

Live text needs the font on the viewer's computer. The maintainer's "golden rule of SVG handoffs"
is to save one copy live for editing and one with letters as shapes for people who lack the font.
`f.save(path, text="shapes")` and `picture.save(path, text="shapes")` do the second.

The switch is one line in each of `_write_pdf` and `_write_svg` (`funground/export/__init__.py`):
with `text="shapes"` the text step starts switched off, so the text collector is never set up and
the renderer draws outlines exactly as it did before T15 and T19. The layer step still runs, so
layers stay layers. The mode is passed from `save` through `save_frame`, `save_document` and
`save_picture`; an animated sketch's queued save stores it with the path. The value is checked at
the call (`"live"` or `"shapes"`, else `ValueError`), also for PNG, GIF and MP4, which then ignore it.
`tests/test_text_shapes.py` covers it.

## Tests

`tests/test_svg_text.py`: the string, family, weight, style, size, fill, position and plain content;
no outline paths left; marker clips gone; exact strings for markup characters, spaces, Hebrew,
Arabic, Devanagari, ligatures and accents, never as shapes; right-to-left direction and logical
order; `text_box` lines; tracking, features and variations; opacity; linear and radial gradients
placed where Cairo put them; a blended line; a turned and a clipped line; text in nested pictures and
in a picture saved as SVG; shadows and erased text kept as shapes; two fonts; fallback `<tspan>`s;
embedded subsets and their families; a font that forbids embedding; the Devanagari subset shaping
like the whole font; text in a shown and a hidden layer; an SVG without text unchanged; the
fallback when the text step fails; file size.
