# Studio vocabulary: assessment of the six paired studios

**Status:** for the maintainer's review (S-132, the "six studios written twice" milestone). Written
7 October 2026, after Ground, Area and Grid, Mark and Play were merged (D-069 to D-073, contract rows
G1, G2, K1 to K3, E1, E2).

## What was done

Six studios, each written twice, drawing the same picture:

| # | Studio | With the vocabulary (gallery) | Without it (before) |
|---|---|---|---|
| 1 | Placement | `examples/gallery/studios/01_placement.py` | `examples/studios/01_placement_before.py` |
| 2 | Proximity | `examples/gallery/studios/02_proximity.py` | `examples/studios/02_proximity_before.py` |
| 3 | Rhythm | `examples/gallery/studios/03_rhythm.py` | `examples/studios/03_rhythm_before.py` |
| 4 | Boolean shapes | `examples/gallery/studios/04_boolean_shapes.py` | `examples/studios/04_boolean_shapes_before.py` |
| 5 | Text as geometry | `examples/gallery/studios/05_text_as_geometry.py` | `examples/studios/05_text_as_geometry_before.py` |
| 6 | Poster series | `examples/gallery/studios/06_poster_series.py` | `examples/studios/06_poster_series_before.py` |

Both versions of every studio are printed in full in `docs/guide/19_studios.md`, the "before" one in a
folded section. `tests/test_studios.py` renders both versions headless and compares the pixels, and
checks that the chapter prints each file exactly. The guide test runs every printed version, and the
gallery test pins the six gallery versions with goldens and op snapshots.

**The pictures.** Studios 1 to 4 are pixel-equal. Studios 5 and 6 differ only in anti-aliased edge
pixels (largest channel difference 20 and 15 of 255; mean difference per channel 0.066 and 0.018). The
cause is one documented property, not a bug in either version: K1 lets a mark's bounds be up to 1/32
unit larger than the ink, and in practice they are rounded outwards to a 1/32 grid. The "before"
versions measure with `path.bounds()`, which is exact. The test allows at most 32 per channel and a
mean of 0.1, and fails if a pair becomes pixel-equal, so the exception list cannot go stale.

**Boolean shapes.** funground already has path Booleans (`|`, `&`, `-`, `^`, `remove_overlap`,
`expand_stroke`; ADR-005), so Studio 4 uses them in both versions. The vocabulary does not touch them,
which is the design (Booleans stay on paths; `mark.outline()` is deferred).

**Gallery coverage.** `NOT_YET_IN_GALLERY` in `tests/test_gallery.py` is now empty. Every name it
listed (`area`, `grid`, `ground`, `inch`, `mm`, `mark`, `variations`, `keep`) is used by at least one
gallery studio, each in a way the picture depends on, not mentioned for the count.

## How the numbers were counted

- **Lines:** lines of code after the module docstring, without blank lines and comment lines.
- **Arithmetic:** binary operations and augmented assignments in the file (`ast.BinOp`,
  `ast.AugAssign`). This counts unit conversions such as `12 * MM` as well as layout sums, so it
  overstates the work slightly for the "before" versions; it is the same rule for both.
- **Transforms:** uses of `push`, `pop`, `translate`, `scale` and `saved_state`.

| Studio | Lines before → after | Arithmetic before → after | Transforms before → after |
|---|---|---|---|
| 1 Placement | 34 → 24 | 36 → 6 | 3 → 0 |
| 2 Proximity | 36 → 18 | 25 → 0 | 0 → 0 |
| 3 Rhythm | 58 → 43 | 21 → 6 | 5 → 0 |
| 4 Boolean shapes | 44 → 27 | 45 → 8 | 9 → 0 |
| 5 Text as geometry | 49 → 21 | 44 → 14 | 9 → 0 |
| 6 Poster series | 91 → 52 | 76 → 5 | 8 → 0 |
| **All six** | **312 → 185** (about 40% fewer) | **247 → 39** (about 85% fewer) | **34 → 0** |

The line saving is moderate; the arithmetic saving is large. Most of what disappears is layout sums
(margins, gutters, cell positions) and the bookkeeping of a drawing's own extent.

## Studio by studio

### 1. Placement (atlas 01)

Nine frames on an A5 page, the same small drawing placed at a different anchor point in each.

- **Clearer.** `anchor="top-right"` says the intention. The "before" version must carry four numbers
  for how far the drawing reaches from its origin (`PEBBLE_LEFT`, `PEBBLE_TOP`, `PEBBLE_W`,
  `PEBBLE_H`) and keep them in step with the drawing by hand; change the ellipse and the placement is
  silently wrong. With a mark, the bounds follow the drawing. `f.size("A5", margin=f.mm(12))` and
  `f.grid(3, 3, gutter=...)` remove all the page arithmetic.
- **Worse or still awkward.** The point *in the cell* still has to be computed:
  `inside.left + inside.width * cell.col / 2`. A mark has nine named anchors, but an Area has no way to
  give the matching point, so the code needs an `ANCHORS` list in grid order and a `col / 2` trick that
  only works for a 3 by 3 grid. See friction item 1.

### 2. Proximity (atlas 04)

Four panels of the same 36 dots, grouped only by spacing: even, rows, columns, clusters.

- **Clearer.** Nested grids are the whole idea of the studio, and `field.grid()` then `group.grid()`
  say it directly. The "before" version needs a helper, `span()`, applied at three levels, and four
  nested loops. This is the cleanest win of the six: 0 arithmetic operations after.
  `panel.inset(bottom=28)` for the caption strip reads well. `f.inch()` is a small, honest use.
- **Worse or still awkward.** Nothing worse. No mark is needed: a dot is `f.circle()`, which is the
  note's own rule ("where the existing API already says it clearly, use it").

### 3. Rhythm (atlas 10)

Five rows repeating one beat: even, faster, long-short, accents, grouped 3 + 2.

- **Clearer.** `beat.place(x, base, anchor="bottom", scale=size)` stands a scaled beat on its line.
  The "before" version translates, scales, then translates back by the stem length (`STEM`), a
  constant that must match the drawing. `row.inset(left=LABEL, bottom=8)` replaces the row sums.
- **Unchanged.** The rhythms themselves (the "Rules") are identical Python in both versions. That is
  as designed: the vocabulary adds nothing to rules.
- **Worse or still awkward.** Lines saved are fewer here (58 → 43), because most of the file is the
  rule functions. `f.grid(1, 5)` to get rows is slightly indirect; `g.rows` exists but needs a grid
  first.

### 4. Boolean shapes (atlas 20/23)

A circle and a square, outlined as a pair, and their union, intersection, difference and xor.

- **Clearer.** `f.mark(path, fill=...)` gives each result its colour once.
  `pair.place(..., anchor="center", height=...)` fits the outlined pair, *including its stroke*; the
  "before" version must add half the stroke width to `path.bounds()` by hand (a classic off-by-a-
  stroke error). `grid.span(0, 0, cols=4)` and `grid.cell(i, 1)` name the layout.
- **Worse or still awkward.** The four results need one shared scale so they stay comparable. There
  is no "fit these together", so the code computes `scale` from `union.width` in both versions.
  `f.mark(path, ...)` takes the current stroke unless `stroke=None` is passed; with the default style
  that adds a black outline (friction item 4).

### 5. Text as geometry (atlas 30)

"FUN" as outlines cut by stripes, as dots along its outlines, and crossed with a circle.

- **Clearer.** The biggest proportional saving (49 → 21 lines). Fitting three different kinds of
  drawing (a cut path, a set of dots, an xor path) into rows is one line each with
  `place(..., anchor="center", width=..., height=...)`. The "before" version needs a `fit()`
  function, and for the dots it must compute an extent from the points plus the dot radius, because
  a list of points has no bounds. Wrapping the dots in `with f.mark()` gives them bounds for free.
- **Worse or still awkward.** The fitted result is not exactly flush: the mark's bounds are rounded
  outwards to 1/32 unit, so the "after" picture differs from the exact fit by a fraction of a pixel
  (the reason this pair is not pixel-equal). For text designers who align ink to a margin, that is a
  small but real imprecision (friction item 2).

### 6. Poster series (Project 01)

One `poster(event)` function, four events, shown as a contact sheet; K keeps the sheet.

- **Clearer.** The largest absolute saving (91 → 52 lines, 76 → 5 arithmetic operations). Without
  `variations`, about a quarter of the file is the sheet: the cell layout, one shared scale, a clip, a
  transform, re-seeding before each poster, a frame and a label. With it, one line. Two details are
  real wins, not just shorter: `background()` inside a study paints only that poster (the "before"
  version must paint with `f.rect()`, because `background()` ignores transforms and would cover the
  sheet), and the same-seed rule is automatic. `f.keep()` writes picture, source and a full record in
  one call; the "before" version writes a PNG and a hand-made JSON note in six lines and records far
  less. `f.area(f.ground.left, ...)` for a full-bleed band reads as intended.
- **Worse or still awkward.**
  - The default layout was wrong for this sheet. Without `columns=2`, four portrait A4 posters are
    put in one row, each 124 units wide, leaving about three quarters of the page empty; 2 by 2 makes each
    poster twice as wide. The row rule (E1) checks only that pictures are at least 100 units wide
    (friction item 3).
  - The label `event = Book fair` cannot be changed or hidden (friction item 5).
  - Because every cell uses the same seed, every poster has its spots in the same cells. That is the
    documented purpose (cells differ only in the parameter), but for a *series* a designer may want
    the opposite. It is reachable by seeding inside the study; a sentence in the guide would help.
  - `keep` could not be shown in a script example: a script that calls `f.keep()` writes a `studio/`
    folder next to the file, and the gallery test and `tools/make_gallery.py` run gallery files in
    place, so the repository would gain files on every run. The studio uses a K key in an animated
    sketch instead, which never fires headless (friction item 6). That is an honest workflow, but it
    means the gallery never exercises `keep` itself; `tests/test_studios.py` does, in a temporary
    copy.

## What each term added

- **Ground** (`size` with page names and margins, `ground`, `mm`, `inch`): removes the unit
  constants and margin sums from every studio. Small per use, present everywhere.
- **Area and Grid**: the largest share of the arithmetic saved. Nesting (`area.grid`) and `span` were
  each decisive in one studio. `inset` is used in five of six.
- **Mark**: decisive wherever a drawing must be *positioned by its own extent* (anchors, fit,
  stroke-inclusive bounds). Not needed where a drawing is one primitive (Studio 2).
- **Play**: decisive for the poster series; nothing else in funground does what `variations` does.
  `keep` is short and records more than a learner would by hand.
- **Where the existing API stays better.** Path Booleans, `text_path`, `text_to_points`, plain
  `f.circle()` for a dot, and Python for the rules. The studios use them unchanged.

## Friction list

Concrete rough edges met while writing the studios. None is implemented here.

1. **An Area cannot give its anchor points.** Marks have nine named anchors; Areas have only `cx`,
   `cy` and the edges, so "put the mark's top-right on the cell's top-right" needs a hand-written
   table. *Suggested fix:* `area.point(anchor)` (or `area.at(...)`) with the same names as
   `place(anchor=)`, returning `(x, y)`; then `pebble.place(*inside.point(name), anchor=name)`.
   Optionally `mark.place_in(area, anchor=...)` later.
2. **Mark bounds are rounded outwards to 1/32 unit, and not symmetrically.** A stroked circle of
   diameter 40 and stroke 6, centred on (0, 0), measures `(-23.0, -23.03125, 46.0, 46.03125)`, so
   `anchor="center"` is 1/64 unit off and `width=` fits slightly small. Text paths are rounded on every
   side. The contract (K1) allows it, but it makes fits not flush and stops "same picture" tests from
   being exact. *Suggested fix:* use exact bounds where they are known (shapes, paths, strokes with
   known joins) and keep the conservative margin only for estimated parts (glyph boxes, shadows); if
   rounding stays, round each side symmetrically.
3. **`variations` prefers a row even when a grid makes every picture much larger.** Four portrait
   posters on a portrait page come out as one row of 124-unit pictures. *Suggested fix* (before E1 is
   relied on): choose the layout that makes pictures largest, and use a single row only when it is
   within, say, 10% of that size; keep `columns=` as the override. This changes a pinned rule, so it
   is a decision for 0.1, not after.
4. **`f.mark(path, ...)` inherits the current stroke.** With the default style (black, 1 unit) a
   filled result gets an outline unless `stroke=None` is passed; Studios 4 and 5 pass it every time.
   It follows the documented rule, so this is a teaching point more than a bug. *Suggested fix:* keep
   the rule, but show `stroke=None` in the Quick Reference example (it is already there) and in the
   guide, or consider a default of fill only when `fill=` is given and `stroke=` is not.
5. **`variations` labels are fixed.** `event = Book fair` repeats the parameter name on every cell.
   *Suggested fix:* `labels=` taking `False`, or a function from the values dict to a string.
6. **`keep` in a script always writes next to the sketch file.** Examples that live in the repository
   cannot call it at the top level without writing into the repository when the tests or the gallery
   tool run them. *Suggested fix:* an override such as a `FUNGROUND_STUDIO` environment variable (the
   test harness and `make_gallery.py` would set it to a temporary folder), or write into the current
   folder when `FUNGROUND_HEADLESS` is set.
7. **No shared fit for several marks.** Comparing results at one scale (Studio 4) needs a hand
   computation from one mark's width. *Suggested fix:* none in the API for now; Python handles it, and
   a helper would be a second layout system. Worth a guide example instead.
8. **The gallery browser does not know the new area.** `examples/gallery/studios/` is shown last,
   titled by its folder name ("Studios"), because `AREAS` in `funground/gallery.py` does not list it.
   The side panel still fits (22 rows). *Suggested fix:* add `"studios": "Studios"` to `AREAS` where
   the maintainer wants it in the order (library change, not made here).
9. **Three spellings for a grid over an area:** `f.grid(..., area=a)`, `a.grid(...)` and, for the
   ground, `f.grid(...)`. All work; the guide uses `area.grid()` for nesting and `f.grid()` for the
   page. *Suggested fix:* none needed; say in the Quick Reference which one to prefer.

No bug in `funground/` blocked any studio, and no workaround was needed apart from item 6.

## Recommendation for 0.1

**Pin the vocabulary for 0.1, after one decision.** The six studios show the terms working together
without surprises: about 40% fewer lines and 85% less arithmetic, the same pictures, and the
existing API left in charge of what it already did well (Booleans, text outlines, rules in Python).
Every name earned its place in at least one studio.

The decision to take first is item 3, the `variations` row rule, because it is pinned in E1 and
changing it after 0.1 would change existing contact sheets. Item 2 can be tightened later within K1's
wording ("never smaller, at most 1/32 larger"). Items 1, 5 and 6 are additions that change nothing
already pinned, so they can follow 0.1.

Not covered by this milestone: the maintainer's three Mark demonstrations (a simple mark, a composite
mark, and repeated placements including vector export) are not written here, and no studio uses
`f.mark("file.svg")` or `style="current"` (both are covered by `tests/test_marks.py`).
