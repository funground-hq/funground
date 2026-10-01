# Design note: SVG files as vector pictures

**Status:** decided (D-041 = A, the maintainer, 1 Oct 2026). Built in Sprint 10 (S-092, commit ced4386).
Contract row P11 in [Semantic_Contract.md](Semantic_Contract.md). Code: `funground/svg.py`,
`Sketch.load_svg` in `funground/sketch.py`, `svg_paths` in `funground/api.py`,
`pathops.even_odd_to_nonzero` in `funground/pathops.py`.

## The problem

Learners have SVG files: logos, icons, drawings. `load_image` cannot read them (pygame-ce rasterises
SVG and gives pixels, and funground refuses with a pointer to `load_svg`, see `imaging.decode`).
Pixels lose the point of SVG. The picture should stay sharp when scaled, and in a PDF it should
still be shapes. The shapes should also be usable as paths, for booleans and clips.

## The route

```
file.svg ──ElementTree──► size + paint servers + parked masks/markers/symbols
        └─svgelements (reify=False, ppi=96)──► shapes with transforms applied
              │  svg._shape(): geometry, fill, fill_geometry, stroke, width, cap, join, dash
              ▼
       SvgDocument(width, height, shapes)
        ├─ svg.draw(doc, picture) ─► picture.draw_path ... ─► Picture history (vector)   f.load_svg
        └─ svg.shapes_as_paths(doc) ─► [PathBuilder, ...]                                f.svg_paths
```

- `svg.py` is the only module that imports `svgelements` (`test_boundaries.py`). It is MIT, pure
  Python, 0.14 MB, with no dependencies (D-041).
- The drawing goes through the picture's ordinary commands. So a loaded SVG is a normal
  [Picture](Pictures_and_Images_Note.md) with a history, and PDF and SVG export replay it as
  vectors (P3).

## Reading

- `read` parses with `xml.etree` first. It finds the size, collects gradient and pattern elements
  by id, and moves `mask`, `marker` and `symbol` into `<defs>` (`_park_unrendered`) so they draw
  only where something uses them. Then svgelements parses with `on_error="ignore"`.
- Size (`_size`): `width` and `height` in CSS units (96 per inch), else the `viewBox`. One side
  plus a `viewBox` keeps the viewBox shape. The result is written back onto the root, so
  svgelements sees it. Percent sizes count as missing. No size at all gives
  `ValueError`.
- `_geometry` converts every segment to funground's four kinds. Arcs and quadratics become
  cubics (`_arc` uses `as_cubic_curves`; a flat arc becomes a line).
- Paint: `_paint` reads colour, `fill-opacity` and `opacity`. A gradient or pattern becomes its
  first colour (`_first_colour`, with a written fallback colour, following `href` up to 8 deep).

## What is supported and what is ignored

- **Supported:** paths; rect, circle, ellipse, line, polyline, polygon; groups; `<use>`;
  transforms; solid fill and stroke with opacity; stroke width, caps, joins, miter limit, dashes
  and dash offset; `fill-rule`; `visibility: hidden` and `display: none`.
- **Fallback:** gradients and patterns paint with their first colour.
- **Ignored:** `<text>`, embedded images, filters, masks, `clip-path`, CSS animation. A group's
  opacity applies to each shape separately.
- SVG's own defaults apply: butt caps, miter joins, miter limit 4. `miter-clip` and `arcs` are
  drawn as miter.

## Fill and stroke are separate ops

`svg.draw` draws each shape in up to two steps: `no_stroke` + `fill` + `draw_path(fill_geometry)`,
then `no_fill` + `stroke` + `draw_path(geometry)`. Reasons:

- The fill needs different geometry. SVG fills an open path as if closed, so `_closed` closes
  every sub-path for `fill_geometry`. The stroke must keep it open.
- funground only fills with the non-zero rule (F3). For `fill-rule="evenodd"`,
  `pathops.even_odd_to_nonzero` builds an equal non-zero outline (a Skia `simplify` of the
  even-odd path, with winding fixed). The stroke still follows the original edges.
- Stroke widths are often fractions. `f.stroke_width()` truncates to whole numbers, so `draw`
  sets the width straight on the state (`_states.update`). SVG widths and dashes are scaled by
  the element transform.
- The result: state is pushed once and popped after, so a loaded picture starts with the default
  state afterwards (tested).

## The 2x raster

A picture draws on a Cairo surface. The window shows that surface's pixels, not a replay. So
`Sketch.load_svg` makes the picture at `max(window scale, 2.0)`, or the window's scale alone when
the long side is over 2048 pixels. Drawn up to about twice its size it stays sharp, and beyond
that it softens. PDF and SVG export replay the history, so they are vector at any size. Cost: a
2x surface is four times the pixels of a 1x one.

`svg.draw` ends with `picture._flush()`, which draws the recorded ops onto the surface.

## `svg_paths`

`f.svg_paths(path)` returns one `PathBuilder` per shape, in document order, in the SVG's own
coordinates after transforms. It uses `shape.geometry`, the outline as written, not
`fill_geometry`. So an evenodd shape keeps both of its sub-paths. Shapes with neither fill nor
stroke are dropped. Each call gives independent builders.

## Alternatives rejected (D-041)

- **picosvg** (Google): needs lxml.
- **SVG as a picture only, via pygame-ce** (C): no new dependency, but no vectors.
- **Our own reader for common SVG** (D): offered in the log. The maintainer chose A; no further
  reason is recorded.

## Invariants and edge cases

- Missing file: `FileNotFoundError` naming both places looked. Not SVG, or no size and no
  `viewBox`: `ValueError`.
- Over about 5 000 shapes (two ops each) the history passes 10 000 and the picture goes into PDF
  and SVG as pixels (P3).
- The picture's size is rounded to whole pixels (`max(1, round(width))`).

## Limits and open questions

- `svg_paths` for an evenodd shape, drawn with `draw_path`, fills the hole. P11 does not say what
  `svg_paths` returns for even-odd shapes. The test pins the sub-path count only.
- Gradients and patterns are the first colour only (P11).

## Tests

`tests/test_svg.py`: sizes and units, every shape, styles, even-odd, paint fallbacks, ignored parts,
window drawing at any size, vector PDF and SVG output, `svg_paths`, errors. SVG files are written by
the tests. `tests/test_boundaries.py` guards the one importer.
