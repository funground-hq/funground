# Design note: colour mode, gradients, blend modes, opacity and shadows

**Status:** decided (D-003 alpha, 24 Sept 2026; D-011 Cairo, 25 Sept 2026; D-031 and D-032 colour mode
and grey numbers, 1 Oct 2026; gradients and compositing needed no decision). Built in Sprint 6 (S-050,
S-051) and Sprint 7 (S-082). Contract rows S13 to S16 in [Semantic_Contract.md](Semantic_Contract.md).
Code: `funground/color.py`, `funground/paint.py`, the colour and compositing methods of
`funground/sketch.py`, and `CairoRenderer` in `funground/renderers/cairo2d.py`.

## The problem

Learners ask for four things that sound alike:
- colours from hue and brightness, or from 0 to 1 numbers (`color_mode`, grey numbers);
- a smooth blend from one colour to another (gradients);
- translucent shapes and ways of mixing with what is underneath (opacity, blend modes);
- a soft shadow.

Each must work in the window, in PNG, and, where it can, stay vector in PDF and SVG.

## Colour mode (S15, S16)

`Color` is funground's own frozen RGBA of four ints. Every colour form is read in one place,
`Sketch.read_color`, which calls `color.parse_in_mode(value, mode, ranges)`.

- The mode is state: `GraphicsState.color_mode` and `color_ranges`, one four-number range per mode
  (rgb, hsb, hsl). So `push` and `pop` save it, and switching back remembers each mode's ranges.
- Only numbers change meaning. Names, hex strings, colour objects and `hsb()`/`hsl()` go straight
  to `Color.parse`.
- **The default mode (rgb, 255) returns `Color.parse(value)` unchanged.** That is how S1 survives
  exactly, fractional truncation included, and why no old snapshot moved.
- One number is a grey and two are grey and alpha (S16). The grey is read on the mode's *third*
  range, so `fill(0)` is black in every mode. In rgb it fills all three channels.
- `read_color(255, 0, 0)` equals `read_color((255, 0, 0))`. A `bool`, or extra numbers after a
  name, is an error.
- Hue wraps and the other parts are clamped. In the default mode an out-of-range number is a
  `ValueError`, as before (S1).
- The packed-integer form was removed (D-032, an approved v0.5 change). D-017's "no
  `color_mode()`" was superseded (D-031).

## Gradients (S13)

`paint.Gradient` is frozen data: `kind`, `points`, `stops` (offset, `Color`). A gradient is a
*paint*: it goes wherever a colour goes (`fill`, `stroke`, `background`, `text(color=)`).

- `parse_paint` lets a `Gradient` pass and parses anything else as a colour.
- `api.linear_gradient` and `radial_gradient` read their colour list with `read_color`, so the
  mode of the moment is used when the gradient is made. Stops must be non-decreasing in 0 to 1.
- It rides in the IR as data. `ir._value_to_jsonable` writes `{"gradient": ..., "points": ...,
  "stops": ...}` and `_paint_from_jsonable` reads it back.
- `CairoRenderer._source` builds a Cairo `LinearGradient`, or a `RadialGradient` with inner radius
  0, and adds the stops with alpha times the current opacity. Cairo's default extend mode is pad,
  which is the "padded beyond its ends" of S13.
- Coordinates are in the user space *at draw time*, so a gradient follows `translate`,
  `rotate` and `scale` with its shape (DrawBot).
- PDF keeps a Cairo gradient as a shading (`tests/test_gradients.py` looks for `/ShadingType`).
- `tint` rejects a gradient with a `ValueError`.

## Blend modes, opacity (S14)

Three state fields: `blend_mode`, `opacity` (0 to 255), `shadow`. They are copied onto
`FillPath` and `StrokePath` ops and read from `style` on shape ops. They are recorded only when
not default (`OMIT_WHEN_DEFAULT`).

```
op ─► _composite_of(op) ── None when normal, 255, no shadow ──► draw as before
        │ (blend, opacity, shadow)
        ▼
  ctx.save(); ctx.set_operator(_BLENDS[blend]); self._alpha = opacity / 255
  [ _draw_shadow ]   then the op itself   then ctx.restore(); self._alpha = 1.0
```

- `_DRAWING` lists the ops that composite: circle, ellipse, rect, line, point, text, fill, stroke
  and `Image`. `Clear` (`background`, `clear`) never does.
- Each of the 17 modes is exactly one Cairo operator (`_BLENDS`): `multiply` to
  `OPERATOR_MULTIPLY`, `dodge` to `OPERATOR_COLOR_DODGE`, `burn` to `OPERATOR_COLOR_BURN`, `hue` to
  `OPERATOR_HSL_HUE`, `saturation`, `color` and `luminosity` likewise HSL, `add` to
  `OPERATOR_ADD`, `normal` to `OPERATOR_OVER`. A test compares each against Cairo.
- Opacity is **not a group.** `_source` multiplies every alpha by `self._alpha`, in colours and
  in gradient stops. Fill and stroke are separate, so a stroke over its own fill shows both
  (DrawBot, Core Graphics). There is no off-screen buffer and no cost.
- An `Image` op carries blend and opacity but no shadow field, so shadows never apply to pictures.

## Shadows: layered and vector-friendly (`_draw_shadow`)

Cairo has no blur. A pixel blur in pure Python is too slow (S-051 notes), and it would turn a PDF
into a picture. So a shadow is made of shapes.

- `_geometry(ctx, op)` gives the op's outline as parts `(make_path, filled, stroke_width)`.
  Text gives one part per glyph.
- N layers, `n = min(12, ceil(blur))` (one when blur is 0). Layer k grows the shape outward by
  `blur * (n - k + 1) / n`: fill, then a stroke of twice the growth with round joins.
- Each layer is one `push_group`, so overlapping parts do not double up. Layers go largest first.
- The layer alphas are `(total / n) / (1 - total * (k - 1) / n)`. After k layers on top of each
  other the alpha is `k * total / n`. A point covered by k layers ends at k/n of the shadow's
  alpha: it fades evenly from the edge to `blur` pixels out. It is not a Gaussian.
- The offset and blur are in canvas pixels whatever the transform. The offset goes through
  `_base_matrix`, the blur is `per_px` user units, and the translate is applied in device space.
- The shadow uses the same operator and opacity (`total` includes `self._alpha`). Its colour is
  always solid, even if the shape is a gradient. The default colour is not read through the
  colour mode (`DEFAULT_SHADOW_COLOR`).

### Why shadows stay vector in PDF

A layer is only a fill, a stroke, a group and a constant-alpha paint. PDF can hold all four.
Nothing in the shadow is a pixel. The same code runs for the window, PNG, PDF and SVG, through
`CairoRenderer.draw`.

## Alternatives rejected

- **Gaussian blur on a pixel buffer:** raster-only and slow in Python (see above).
- **Opacity as a group:** S-051 chose per-fill and per-stroke alpha, as DrawBot does: no groups, no cost.
- **No colour mode, only `hsb()` and `hsl()` constructors (D-017 C):** chosen on 25 Sept 2026 for
  clarity. D-031 replaced it with p5's `color_mode`, so p5 sketches port by renaming.
- **A packed integer as a colour (v0.5):** removed for p5's grey meaning (D-032).

## Invariants and edge cases

- Fewer than two gradient colours, bad stops, or a radius of 0 or less: `ValueError`.
- Unknown mode, opacity outside 0 to 255, negative blur: `ValueError` listing the choices.
- A gradient given with extra numbers (`fill(grad, 5)`) is an error (`_paint`).
- Blend, opacity and shadow are saved by `push` and carried by a picture's own state (P2).

## Limits and open questions

- At most 12 layers: a blur over 12 pixels fades in steps wider than a pixel.
- How a PDF viewer shows each Cairo blend operator is not tested. No test saves a shadow or a
  blend mode to PDF, so "stays vector" rests on the construction above.
- A gradient from `f.linear_gradient` reads the *main* sketch's colour mode, even when used on a
  picture. Pictures have no gradient methods of their own.
- `FormattedString.append(color=...)` reads the active sketch's mode in the same way.

## Tests

`tests/test_color.py`, `test_colour_objects.py` (S1, S12), `test_color_mode.py` (S15, S16),
`test_gradients.py` (S13), `test_compositing.py` (S14: operators, opacity, shadow offset, state, defaults).
Related: [ADR-002](ADR-002-renderer-selection-reopened.md) for why Cairo is the renderer.
