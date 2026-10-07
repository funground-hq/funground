# Studio vocabulary: Ground, Mark, Rules, Play

**Status:** proposal for release 0.1 (D-069). The names and signatures below await the maintainer's
approval before they are built. Player is parked.

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
| **Ground** | The composition surface: page size, background, margins, units, coordinates | `f.size(...)` gains page names and `margin=`; `f.ground`; `f.grid()`; `f.mm()`, `f.inch()` |
| **Mark** | A reusable static drawing: one shape, or a composition of shapes, text, images and other marks | the new `Mark` type, made with `f.mark()` |
| **Rules** | The decisions that place, repeat and vary marks | ordinary Python: variables, `for`, `if`, functions. No new API |
| **Play** | Deliberate exploration: vary, compare, choose, keep reproducible versions | `f.variations()`, `f.keep()`, plus the existing `f.random_seed()` and controls |
| **Player** | An actor with state and behaviour (movement, collision, response) | **parked.** Animated sketches with `Vector` already do this. If it returns, it may use a Mark as its look |

## Ground

```py
f.size("A5", margin=f.mm(12))       # a named page, margins in millimetres
f.background("paper")
f.ground.left, f.ground.top          # the area inside the margins
for cell in f.grid(3, 4, gutter=f.mm(4)):
    f.circle(cell.cx, cell.cy, cell.w * 0.6)
```

- **`f.size(width, height, ..., margin=0)`** also accepts a page name, as in `f.size("A4")` and
  `f.size("A4", landscape=True)`. The names are the existing `page_size()` table. `margin` is one
  number, or four as `(top, right, bottom, left)`.
- **`f.ground`** is read-only and live, like `f.width`. It has `left`, `top`, `right`, `bottom`,
  `width`, `height`, `cx`, `cy`. The **canvas** is the whole surface; the **ground** is the composed
  area inside the margins. Without a margin the two are the same.
- **Margins are a guide, not a clip.** Drawing outside the ground is allowed.
- **`f.grid(cols, rows, gutter=0, area=None)`** returns cells over the ground, or over `area`. Each cell
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

flower.draw(150, 200)                                  # its origin (0, 0) at (150, 200)
flower.draw(400, 200, scale=0.5, rotate=15, opacity=0.6)

leaf = f.mark(f.path().ellipse(0, 0, 40, 16), fill="olive")   # a simple mark from a path

with f.mark() as border:             # marks nest: a composite made of marks
    for i in range(8):
        flower.draw(i * 70, 0, scale=0.4)
border.draw(f.ground.left, f.ground.bottom, anchor="bottom-left")
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

**3. What happens when it is reused?** A mark is an **immutable value**. When its block ends it cannot
change.
- Placing it never changes it, and one placement never affects another. They share nothing that can be
  changed.
- A variation is a new mark. The idiom is a function that returns one:
  `def flower(petals, colour): ...`. That is the "Rules" part.
- Copying is never needed, so there is no `copy()`.

### Further semantics

- **Style is part of the mark.** Each element keeps the fill, stroke and font it was drawn with.
  - Placing ignores the current fill and stroke.
  - Recording starts from the current style and an identity transform.
  - The transform and style return to what they were when the block ends, as with `push`/`pop`.
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
        f.circle(f.ground.left + i * gap, f.ground.cy, 20)

f.variations(study, gap=[10, 20, 35, 60])     # a contact sheet: four labelled versions side by side
f.keep("gap 35 reads as a rhythm")             # keeps this version, reproducibly
```

- **`f.variations(fn, **values)`** calls `fn` once for each value, or for each combination when two
  parameters are given, and draws the results as a labelled contact sheet over the ground.
  - Each cell is `fn`'s drawing recorded as a mark and placed scaled.
  - Each cell is drawn with the **same random seed**, so the cells differ only in the parameter.
  - It works in scripts and in `setup()`.
- **`f.keep(note="", **settings)`** saves the current picture into a `studio/` folder next to the
  sketch, numbered in order:
  - `007.png`;
  - `007.py`, a copy of the source;
  - `007.json`, holding the note, the settings passed, every control's value, the random seed, the
    size and margin, the date and the funground version.

  It prints where it saved. It is the atlas's exploration record, written by the tool.
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

## Open questions for the maintainer

1. **The names:** `f.mark`, `mark.draw(x, y, scale=, rotate=, opacity=, anchor=)`, `f.ground`,
   `f.grid`, `f.mm`/`f.inch`, `f.variations`, `f.keep`. Is `place` better than `draw` for marks?
   `draw` matches `f.draw_path` and reads naturally. `place` matches the brief's word "placement".
2. **Should `f.keep` also save a PDF next to the PNG?** The proposal: no by default, with `f.keep(..., pdf=True)`.
