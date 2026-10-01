# Design note: paths, drawing modes, booleans and rounded corners

**Status:** decided (D-037 by the maintainer, ADR-005, 1 Oct 2026; D-038 and D-039 by Claude under D-034,
1 Oct 2026; D-040 by the maintainer, 1 Oct 2026; D-030 for modes, 1 Oct 2026). Built in Sprint 4
(S-028), Sprint 5 (S-074), Sprint 7 (S-081), Sprint 9 (S-086 to S-088), Sprint 10 (S-089).
Contract rows F3, F9, F10, F11, F12, F13, F14 in [Semantic_Contract.md](Semantic_Contract.md).
Code: `funground/geometry.py`, `paths.py`, `shapes.py`, `pathops.py`, and the shape methods of
`funground/sketch.py`.

## The problem

Learners draw outlines with corners and curves, cut holes, combine shapes and turn letters into
shapes. Cairo draws a path but cannot compute a new one. So funground needs its own path type,
and a geometry library for the new-outline work.

## The route

```
f.begin_shape()/vertex()...   ShapeBuilder (shapes.py) ──build()──┐
f.path().move_to()...         PathBuilder (paths.py) ─────────────┼──► geometry.Path  (immutable)
f.text_path(), f.svg_paths()  PathBuilder ────────────────────────┘          │
                                                                             ▼
          Sketch._emit_path ──► ir.FillPath (closed only) + ir.StrokePath ──► Cairo _path()
          Sketch.clip       ──► ir.ClipPath
          a | b, expand_stroke, contains ──► pathops.py ──► skia-pathops ──► Path again
```

- `Path` holds tuples: `("move", pt)`, `("line", pt)`, `("cubic", c1, c2, pt)`, `("close",)`.
  There is one curve kind. `Path.quad_to` stores the exact cubic, so every consumer needs one case.
- `PathBuilder` wraps a `Path`. Building methods return the same builder (chaining). Booleans,
  `expand_stroke` and the transforms return a **new** builder (D-038, as DrawBot does).
- `_emit_path` fills only a closed path (`Path.is_closed`) and then strokes. Fill is before
  stroke (S5) and uses the non-zero rule, set once in `CairoRenderer.context_for` (F3).
- `ShapeBuilder` only records vertices. `end_shape` builds the `Path`, because a Catmull-Rom
  curve needs the points on both sides (`catmull_rom_controls`). Fewer than four `curve_vertex`
  points in a row draw nothing and warn. One-call `bezier()` and `curve()` are open, so they
  are stroked and never filled (F9).
- Holes (`begin_contour`) are reversed when their winding matches the outline's. The sign is
  the shoelace area of every point, control points included, so it is a good guess, not exact.

## Drawing modes (F10, D-030)

`rect_mode`, `ellipse_mode` and `image_mode` are fields of `GraphicsState`, so `push` and `pop`
save them. They are resolved in the Sketch (`_rect_box`, `_ellipse_box`, `draw_image`) before an op
is made. So the IR always holds top-left rectangles and images and centre ellipses. Renderers
never see a mode. Mode fields are in `OMIT_WHEN_DEFAULT`, so old snapshots did not change.

## Booleans through skia-pathops (ADR-005)

`pathops.py` is the only module that imports `pathops`. `test_boundaries.py` enforces it.

- `to_skia` keeps only **closed sub-paths** (`_closed_subpaths`) and sets `WINDING`. Skia would
  otherwise close and fill an open sub-path (F11).
- `union`, `intersection`, `difference`, `xor` call `pathops.op`. `remove_overlap` calls
  `simplify(fix_winding=True)`.
- `from_skia` turns a quadratic into its exact cubic. A conic would raise `ValueError`, so the
  only producer of conics is converted first: `expand_stroke` calls `convertConicsToQuads()`
  (round caps and joins). Result: close quadratics, raised to cubics (F12).
- `even_odd_to_nonzero` re-reads a path with the even-odd rule and returns an equal non-zero
  shape. The SVG importer uses it (see [SVG_Import_Note.md](SVG_Import_Note.md)).
- `expand_stroke` uses `_stroked_skia`, which keeps open sub-paths too, then Skia's `stroke`
  and `simplify`. An odd dash list is doubled, as in SVG. Bad values give `ValueError`.
- `exact_bounds` uses Skia's tight `bounds`, so a bulging curve is smaller than its control box.
  `Path.bounds()` in `geometry.py` is the older loose box (corners, not x, y, w, h). They are
  different on purpose.
- `contains` ignores open sub-paths, as booleans do.
- The pinned result is the drawn shape, not the point order. Skia's output may differ from
  DrawBot's in order and in how a self-touching outline is split.

## Text as a path (F13, D-039)

`Sketch.text_path` uses `_line_layout` (or `_fs_layout` for a `FormattedString`), the same layout
`text` and `text_box` use, so they cannot drift. It joins every glyph's outline into one `Path`.
Drawn with `draw_path` that is one fill, while `text()` fills each glyph (`FillPath` per glyph).
Where letters touch, anti-aliasing differs by up to 9/255 (D-039). The shape is identical.

## Rounded corners (F14, D-040)

- `geometry.rect_radii` turns 0, 1 or 4 numbers into four radii and caps each at half the shorter
  side, as p5 does. Negative radii and other counts are `ValueError`.
- `Sketch._emit_rect` reads the radii first, so errors appear even for an empty box. A negative
  width or height is flipped, then the radii are clamped again. A sharp result emits a plain
  `ir.Rect`, so old snapshots stay unchanged.
- `ir.Rect.radii` holds four numbers or `()`. `CairoRenderer._rect_path` calls
  `Path.rounded_rect`, which builds quarter arcs with `arc_to`. Shadows share `_rect_path`.
- `PathBuilder.rect` takes the same radii, but the drawing modes do not apply to builders.

## Alternatives rejected

- **`booleanOperations` + `pyclipper` (D-037 B)**: smaller, but it flattens curves and refits them,
  and it has no stroke expansion.
- **Either as an optional extra (C)** and **no booleans in 0.1 (D)**: the maintainer chose A after
  checking the wheel (1.8 MB on Windows, no other dependencies).
- **Per-glyph sub-paths so `text_path` matches `text` exactly (D-039)**: not worth a renderer
  change for a few edge pixels.
- **A per-call `anchor=` option (D-030 C)** instead of modes: p5 portability won (B).

## Invariants and edge cases

- Clips are lifted by the `pop` of the enclosing `push` and never survive the frame (F2, F3).
- `clip()` with an empty path warns and is ignored, because it would hide everything after it.
- An empty boolean result is an empty path, drawn as nothing. `bounds()` of it is `None`.
- `a.rotate` turns clockwise on screen about `(cx, cy)`. `scale` is about the origin.

## Limits and follow-ups

- F14 says "quarter-ellipse arcs". Each corner has one radius, so the arcs are quarter circles
  (`rounded_rect` passes the same value for both radii). No elliptical corners exist.
- `PathBuilder.polygon` needs three points; `Sketch.polygon` needs two (F5). Both match their rows.

## Tests

`tests/test_paths.py` (F3, F9 holes), `test_curves.py` (F9), `test_modes.py` (F10),
`test_path_booleans.py` (F11), `test_path_outlines.py` (F12), `test_text_path.py` (F13),
`test_rounded.py` (F14), `test_boundaries.py` (one importer of `pathops`).
Decisions: [Decision_Log.md](Decision_Log.md); library choice: [ADR-005](ADR-005-path-operations.md).
