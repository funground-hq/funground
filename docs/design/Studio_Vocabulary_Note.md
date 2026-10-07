# Studio vocabulary: Ground, Mark, Rules, Play

**Status:** approved for release 0.1 (D-069, D-070, D-071). Ground, Mark and Play are in 0.1. Play is
prototyped first; its names, form and behaviour are agreed with the maintainer before they are pinned. Player and
`mark.outline()` are deferred. A second AI reviewer's conditions, accepted by the maintainer, are folded in.

**Why.** The 64-studio atlas teaches creativity: make, vary, notice, choose, explain. Inspired by John
Maeda's *Design By Numbers* (Paper, Pen, Line, Repeat), the maintainer proposed four terms that make
those exercises read as visual intentions. Most of what the studios need already exists in funground:
paths and Booleans, clipping, masks, shaped text and text outlines, layers, pages, and vector PDF/SVG.
The gaps are three: **setting up the page**, a **reusable drawing** that can be placed many times,
and **help with exploring** (keeping versions, comparing variants).

The layer stays thin. It is plain `f.` functions and one new type, with no parser and no second
language. Where the existing API already says it clearly, the studios use the existing API.

| Term | Meaning | In funground |
|---|---|---|
| **Ground** | The composition surface: page size, background, margins, units, coordinates | `f.size(...)` gains page names and `margin=`; `f.ground` and `f.ground.content`; `f.grid()`; `f.mm()`, `f.inch()` |
| **Mark** | A reusable static drawing: one shape, or a composition of shapes, text, images and other marks | the new `Mark` type, made with `f.mark()` |
| **Rules** | The decisions that place, repeat and vary marks | ordinary Python: variables, `for`, `if`, functions. No new API |
| **Play** | Deliberate exploration: vary, compare, choose, keep reproducible versions | `f.variations()`, `f.keep()`, plus the existing `f.random_seed()` and controls |
| **Player** | An actor with state and behaviour (movement, collision, response) | **parked.** Animated sketches with `Vector` already do this. If it returns, it may use a Mark as its look |

## Ground

```py
f.size("A5", margin=f.mm(12))       # a named page, margins in millimetres
f.background("paper")
f.ground.width, f.ground.height     # the whole surface (full-bleed backgrounds)
f.ground.content.left                # the area inside the margins
for cell in f.grid(3, 4, gutter=f.mm(4)):
    f.circle(cell.cx, cell.cy, cell.w * 0.6)
```

- **`f.size(width, height, ..., margin=0)`** also accepts a page name, as in `f.size("A4")` and
  `f.size("A4", landscape=True)`. The names are the existing `page_size()` table. `margin` is one
  number, or four as `(top, right, bottom, left)`.
- **`f.ground`** is the whole surface, read-only and live like `f.width`. It has `left`, `top`,
  `right`, `bottom`, `width`, `height`, `cx`, `cy` and `margin`, as `(top, right, bottom, left)`.
- **`f.ground.content`** is the area inside the margins, with the same fields. Full-bleed work uses
  `f.ground`, and margin-based composition uses `f.ground.content`. Without a margin the two are the same.
- **Margins are a guide, not a clip.** Drawing outside the ground is allowed.
- **`f.grid(cols, rows, gutter=0, area=None)`** returns cells over `f.ground.content`, or over `area`. Each cell
  has `x`, `y`, `w`, `h`, `cx`, `cy`, `col`, `row` and `index`. It is a list, so the loop is the learner's own.
- **`f.mm(n)` and `f.inch(n)`** convert to funground units: 1 unit = 1 point in a PDF, 72 to the inch.
- **Unchanged:** the origin stays top-left and y points down (contract C1).

## Mark

A mark is a **drawing kept as a value**. You make it once, then place it as often as you like, at any
position, scale, rotation or opacity. It stays vector everywhere: crisp on screen at any scale, and
real vector content in PDF and SVG.

```py
with f.mark() as flower:             # draws nothing yet: the drawing is recorded
    for a in range(0, 360, 60):
        with f.saved_state():
            f.rotate(a)
            f.fill("tomato")
            f.ellipse(0, -30, 18, 40)
    f.fill("gold")
    f.circle(0, 0, 24)

flower.place(150, 200)                                  # its origin (0, 0) at (150, 200)
flower.place(400, 200, scale=0.5, rotate=15, opacity=0.6)

leaf = f.mark(f.path().ellipse(0, 0, 40, 16), fill="olive")   # a simple mark from a path

with f.mark() as border:             # marks nest: a composite made of marks
    for i in range(8):
        flower.place(i * 70, 0, scale=0.4)
border.place(f.ground.content.left, f.ground.content.bottom, anchor="bottom-left")
```

### The three questions the maintainer's review raised

**1. Does a Mark keep its contents?** Yes. A mark keeps the drawing steps made inside its block (the
IR ops, with the style each was drawn in), not pixels.
- Placing a mark replays those steps inside a saved and transformed state.
- PDF and SVG therefore get the shapes and live text as vectors, and the screen redraws them crisp.
- There is no pixel size and nothing is clipped to a box.
- A picture drawn inside a mark stays the picture it is (pixels, or its own history, per contract P3).

**2. What decides its position?** Its own **local coordinates**.
- The mark's origin `(0, 0)` is the point that lands at `(x, y)` when it is placed. You draw around it,
  and negative coordinates are fine.
- `mark.bounds()` returns `(x, y, w, h)` in local coordinates. It is the area actually covered,
  including stroke widths and text.
- `anchor=` places by the bounds instead of the origin: `"origin"` (the default), `"center"`,
  `"top-left"`, `"top"`, `"top-right"`, `"left"`, `"right"`, `"bottom-left"`, `"bottom"` or `"bottom-right"`.
  This is for the alignment studios.
- Placement order is `translate(x, y)`, then `rotate`, then `scale`, around the anchor point. It works
  inside the current transform, so marks compose with `push`/`translate` as any drawing does.

**Bounds, precisely.**
- `bounds()` is **conservative**: never smaller than the ink, possibly a little larger. It includes
  stroke widths, joins and caps, and text by its glyph boxes.
- An **empty mark** gives `bounds()` → `None` and `is_empty` → `True`, as an empty path does.
  - Placing an empty mark draws nothing.
  - Placing it with an anchor other than `"origin"` raises `ValueError` ("the mark is empty").
- Anchors use the mark's own, untransformed bounds. `rotate` and `scale` then turn and size the mark
  around the anchor point, so `anchor="center"` keeps the centre where it was placed.

**3. What happens when it is reused?** A mark is an **immutable value**. When its block ends it cannot
change.
- Placing it never changes it, and one placement never affects another. They share nothing that can be
  changed.
- A variation is a new mark. The idiom is a function that returns one:
  `def flower(petals, colour): ...`. That is the "Rules" part.
- Copying is never needed, so there is no `copy()`.
- **Immutable does not mean fixed in place.** Every placement can have its own position, scale,
  rotation and opacity. Derived marks (`flower.scaled(0.5)`) would return new values; they are
  deferred until an exercise needs one.
- **Placing draws immediately** (funground is immediate-mode). A placement is not an object you can
  select and move afterwards. A retained "placement" would be a scene graph, a separate decision not
  taken here.

### Further semantics

- **Style is part of the mark.** Each element keeps the fill, stroke and font it was drawn with.
  - Placing ignores the current fill and stroke.
- **Capture is isolated.**
  - Recording **inherits the current style**: fill, stroke, stroke width, caps and joins, text font,
    size, alignment and leading, blend mode and colour mode.
  - It starts with the **identity transform**, so local coordinates are the mark's own.
  - When the block ends, the surrounding transform, style and clip are restored exactly, as with
    `push`/`pop`. This includes the case where the block raises an exception.
  - Nothing drawn inside a block reaches the canvas.
- **A failed or unfinished mark cannot be placed.** If the block raises, the exception propagates and
  the mark stays unfinished. Placing an unfinished mark, including inside its own block, raises
  `RuntimeError`, naming the problem.
- **Two phases inside, one type outside.** The implementation keeps a mutable recorder for the block,
  separate from the finished, immutable `Mark`. Learners see only `Mark`.
- **Direct construction.** `f.mark(path, fill=..., stroke=..., stroke_width=...)` makes a finished mark
  from a path, without a block. Unspecified style comes from the current style.
- **Vector fidelity.** Shapes, paths and gradients stay vector in PDF and SVG. Pictures and images
  inside a mark stay raster, or replay their own history (contract P3). Text follows the text-in-files
  rules (T15, T19, T20):
  - PDF embeds font subsets;
  - SVG live text needs the font installed where it is opened, and `text="shapes"` gives outlines for
    distribution.

  So "live text" depends on fonts and shaping, as everywhere in funground.
- **Opacity and blend apply to the whole.** `opacity=0.5` fades the mark as one group: overlapping
  petals do not show through each other. In PDF this is a transparency group.
- **Grouping is not Boolean geometry.** A mark keeps its elements separate, with their colours and
  overlap. Path Booleans (`|`, `&`, `-`, `^`) build new geometry and stay on paths.
  - The bridge is explicit: `mark.outline()` returns one path, the union of the mark's filled shapes.
  - `mark.outline()` is **deferred**, so the first version does not need it.
- **In animated sketches**, make marks in `setup()` (or at the top) and place them in `draw()`.
  Placing a mark is cheap.
- **Recording is not drawing.** Inside `with f.mark()`, calls that read pixels (`get`, `load_pixels`)
  or save files raise an error that names the mark. Controls cannot be made in a mark.
- **Layers.** A mark can be placed inside `with f.layer(...)`. A layer cannot be opened inside a mark.

### Placement additions (D-072, from the comparison with PShape)

**Style override.** `place(..., style="own" | "current")` is the analogue of PShape's `disableStyle()`.
- `"own"`, the default, draws the recorded style.
- `"current"` draws every element with the style in force at placement. You set that style the usual
  way first, so there are **no per-property keywords** and no long call:

  ```py
  f.fill("black")
  f.no_stroke()
  flower.place(x, y, style="current")          # a silhouette of a multicolour flower
  ```

  What `"current"` replaces:
  - **Closed shapes and paths:** fill, stroke, stroke width, caps, joins, miter limit and dash. A
    gradient fill becomes the current fill, and `no_fill()`/`no_stroke()` apply.
  - **Lines and open strokes:** stroke, width, caps and dash.
  - **Text:** its colour. Font, size and shaping are unchanged, because they are geometry.
  - **Images and pictures:** unchanged.
  - **Nested marks:** the same rules, all the way down.
  - **Opacity and blend:** they still come from `place()`'s own arguments.

**Fit.** `place(..., width=None, height=None)` is the analogue of `shape(s, x, y, w, h)`.
- Giving one of them scales the mark uniformly to that size, from its bounds.
- Giving both fits it inside the box, keeping its proportions and centring it.
- Using either with `scale=` raises an error.
- Typical use is a grid cell: `flower.place(cell.cx, cell.cy, anchor="center", width=cell.w * 0.8)`.

**From an SVG file.** `f.mark("leaf.svg")` is the analogue of `loadShape`.
- It makes a finished mark from the file's shapes, colours and groups, as vectors.
- Its origin is the file's top-left.
- `style="current"` can recolour it.

## Compared with Processing's PShape, p5 and DrawBot

| | PShape (Processing) | Mark |
|---|---|---|
| Construction | `createShape(...)`, `beginShape`/`vertex`, `createShape(GROUP)` with `addChild`, `loadShape("x.svg")` | A block capturing ordinary drawing, `f.mark(path, ...)` or `f.mark("x.svg")` |
| Contents | Shapes and vertices with styles; no text | Shapes, paths, gradients, shaped text, images, pictures and nested marks |
| Parts | `getChild`, `getVertex`/`setVertex`, editable | Opaque (editing parts deferred: it needs a mutable tree) |
| Style | Baked in; `disableStyle()` uses the current style | Baked in; `place(style="current")` uses the current style |
| Transforms | `s.rotate()` and the like change the shape and **accumulate**: a common beginner trap | Each placement has its own transform; the mark never changes |
| Placement and size | `shape(s, x, y[, w, h])`, `shapeMode` | `place(x, y, scale=, rotate=, anchor=, width=, height=)` |
| Group opacity | No group alpha in 2D | The whole mark fades as one (a transparency group in PDF) |

- **p5.js:** `createGraphics()` is a fixed-size off-screen bitmap, like funground's Picture.
  `buildGeometry()` captures drawing into reusable geometry, but only for WebGL 3D.
- **DrawBot:** `BezierPath` is reusable geometry with Booleans and transforms; style is supplied when it
  is drawn, like funground's Path.

Immutability is a design choice, not something the concept requires; PShape shows a mutable shape can
work. Its accumulating transforms are the strongest argument that immutability suits learners.
funground's contribution is the combination:
- capturing ordinary drawing, including text;
- anchors and fitting;
- group opacity;
- the studio workflow.

The six studios test that combination; the note does not claim it is new.

### How it relates to what exists

| | What it is | Use it for |
|---|---|---|
| **Path** (`f.path()`) | Geometry without style | Booleans, outlines, clipping, a shape to build marks from |
| **Mark** (`f.mark()`) | A styled drawing as a value, in local coordinates, vector | Motifs, families, compositions placed many times |
| **Picture** (`f.create_graphics()`, `f.load_image()`) | Pixels, with a fixed size | Images, pixel effects, masks, filters, painting that accumulates |
| **Layer** (`f.layer()`) | A named picture over the canvas | Separating parts of a sketch, layers in PDF and SVG |

## Rules

There is no new API: rules are Python. The guide shows three idioms:
- a mark-making **function** with parameters (a family);
- a **loop** over `f.grid()` or a range (repetition and rhythm);
- an **`if`** on the loop index (pattern and exception).

`f.random_seed()` stays the way to make chance repeatable.

## Play

```py
def study(gap):
    for i in range(12):
        f.circle(f.ground.content.left + i * gap, f.ground.content.cy, 20)

f.variations(study, gap=[10, 20, 35, 60])     # a contact sheet: four labelled versions side by side
f.keep("gap 35 reads as a rhythm")             # keeps this version, reproducibly
```

- **`f.variations(fn, **values)`** calls `fn` once for each value, or for each combination when two
  parameters are given, and draws the results as a labelled contact sheet over the ground.
  - Each cell is `fn`'s drawing recorded as a mark and placed scaled.
  - Each cell is drawn with the **same random seed**, so the cells differ only in the parameter.
  - Each cell starts from **isolated drawing state**: the style and an identity transform as at the
    call, so one cell's `fill()` cannot leak into the next.
  - Each cell is labelled with the parameter values that vary, such as `gap = 35`.
  - It works in scripts and in `setup()`.
- **`f.keep(note="", **settings)`** saves the current picture into a `studio/` folder next to the
  sketch, numbered in order:
  - `007.png`;
  - `007.py`, a copy of the source;
  - `007.json`, holding the note, the settings passed, every control's value, the random seed, the
    size and margin, the date and the funground version.

  It prints where it saved. It is the atlas's exploration record, written by the tool.
- `f.keep(note, pdf=True)` also saves `007.pdf`.
- **What a record cannot promise.** It also lists what it could not capture: fonts used, by name and
  file; image and data files the sketch read, by name and size; and the Python and platform versions.
  Source, seed and settings reproduce a picture only while those stay the same.
- **Every run gets a seed.** When the learner has not called `random_seed()`, funground picks one at
  the start and records it, so every kept version can be reproduced with `f.random_seed(n)`.

## Contract rows, to add once approved

- **G1 Ground:** page names in `size`, `margin`, `f.ground`, `f.grid`, `mm`/`inch`.
- **K1 Mark recording:** what is kept, the style, transform and state rules, and the errors.
- **K2 Mark placement:** local origin, anchors, transform order, group opacity, nesting.
- **K3 Mark in files:** vector replay in PDF and SVG, live text, pictures inside marks.
- **E1 Variations.**
- **E2 Keep and the automatic seed.**

## The first investigation (the maintainer's brief)

Six studios, each written **twice**: with funground as it is today, and with the vocabulary. Both
versions are tested by the guide test.
1. Placement (atlas 01)
2. Proximity (04)
3. Rhythm (10)
4. Boolean shapes (20/23)
5. Text as geometry (30)
6. A poster series (Project 01)

Plus the maintainer's three Mark demonstrations: a simple mark, a composite mark, and repeated
placements of the composite, including vector export.

The assessment then states, for each term, what it saved in lines and setup, what it made clearer,
what it added to exploration, and where the existing API remains the better choice.

## Decided (D-070, 7 October 2026)

- Names approved: `f.mark`, `mark.place(...)`, `f.ground` with `f.ground.content`, `f.grid`,
  `f.mm`/`f.inch`, `f.variations`, `f.keep`.
- `f.keep(..., pdf=True)` is optional.
- Mark is built on recorded ops, not on Picture. It is immutable once finished, and also constructible
  directly from a path.
- Added (D-072): `place(style="current")`, `place(width=, height=)`, `f.mark("file.svg")`.
- Deferred: `mark.outline()`, derived marks (`scaled`, `rotated`), editing parts, retained placements, Player.
- Scope: Ground and Mark in 0.1. Play also in 0.1 (D-071): prototyped first, then its shape agreed
  with the maintainer. Open: flat names (`f.variations`, `f.keep`) or a `f.play` namespace.

## Decided (D-073, 7 October 2026): Area, Grid and Play's shape

- **Area** is an immutable rectangle value.
  - It has `left`, `top`, `right`, `bottom`, `width`, `height`, `cx` and `cy`.
  - Make one with `f.area(x, y, w, h)`. `area.inset(all)` or `area.inset(top=, right=, bottom=, left=)` gives a smaller one.
  - An inset larger than the area is an error.
  - `area.grid(cols, rows, gutter=)` makes a grid inside it.
  - `f.ground`, `f.ground.content` and every cell are Areas.
- **Grid** is returned by `f.grid()` and `area.grid()`.
  - It iterates and indexes like a list, as before, but is a Grid: a public return-type change.
  - `g.cell(col, row)` is zero-based.
  - `g.span(col, row, cols=1, rows=1)` returns an Area that includes the inner gutters.
  - `g.column_count` and `g.row_count` are numbers. `g.columns` and `g.rows` are lists of Areas.
  - Invalid cells or spans raise clear errors.
  - A cell is an Area with `col`, `row` and `index`.
- **Guides.** `g.show()` draws thin guide lines and leaves the drawing state unchanged. It is excluded from
  saved files unless asked for. If on-screen-only drawing needs large renderer changes, guides are deferred
  and Area and Grid ship without them.
- **Play is flat:** `f.variations()` and `f.keep()`. "Play" stays the teaching word.
  - With one parameter, `variations` makes a row while the cells stay readable; `columns=` overrides.
  - It returns `(values, mark)` pairs. The labels belong to the sheet, not to the marks.
  - Every cell shares one scale and one coordinate frame, so changes in position stay visible.
  - `background()` inside a study paints only its own cell.
  - K in an animated sketch keeps the next drawn frame, recording that frame's state.
  - Random and noise seeds are both recorded. Explicit seeds are kept as given, with no range limit.
- **A recorded seed makes funground's randomness repeatable; it does not make every sketch reproducible.**
  The record's dependency list and its "not captured" list say so.
