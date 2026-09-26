# 9. Paths and clipping

## Shapes from points

List the corners between `f.begin_shape()` and `f.end_shape()`:

```python
import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("gold")
    f.stroke("darkorange")
    f.stroke_width(4)
    f.begin_shape()
    for i in range(10):
        r = 140 if i % 2 == 0 else 60
        a = math.pi * i / 5 - math.pi / 2
        f.vertex(200 + r * math.cos(a), 200 + r * math.sin(a))
    f.end_shape(close=True)


f.run()
```

![A star from vertices](../gallery/images/paths-01_star.png)

`end_shape(close=True)` joins the last point to the first and fills the shape.
`end_shape()` leaves it **open**: open shapes are only stroked, never filled.

## Reusable paths

`f.path()` builds a shape once so you can draw it many times:

```py
leaf = f.path().move_to(0, -40).line_to(24, 0).line_to(0, 40).line_to(-24, 0).close()
f.draw_path(leaf)
```

`move_to`, `line_to`, `curve_to` and `quad_to` add to the path; `close()` closes it.
`f.draw_path(path)` fills (if closed) and strokes it with the current style, and transforms
apply to it like to any shape.

## Clipping

`f.clip(path)` keeps everything drawn afterwards **inside** the path. It lasts until the end of
the `saved_state` block (or the matching `pop()`), so always clip inside one:

```py
with f.saved_state():
    f.clip(window)
    ...                       # drawn only inside window
```

![Paths and clipping](../gallery/images/paths-02_path_and_clip.png)

`f.no_clip()` switches clipping off until the end of its own `saved_state` block; when that block
ends, the clip from outside it comes back.

![Clipping on and off](../gallery/images/paths-03_no_clip.png)

## Curves

Inside a shape, three kinds of curve follow Processing's names:

| Function | What it does |
|---|---|
| `f.bezier_vertex(cx1, cy1, cx2, cy2, x, y)` | A curve from the previous point to `(x, y)` that bends toward two control points |
| `f.quadratic_vertex(cx, cy, x, y)` | The same with one control point |
| `f.curve_vertex(x, y)` | A smooth curve **through** the points. The first and last points only steer the curve, so give at least four |
| `f.curve_tightness(t)` | 0 (default) for smooth curves, up to 1 for straight lines |

For a single curve there are `f.bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)` and
`f.curve(x1, y1, x2, y2, x3, y3, x4, y4)` (from point 2 to point 3). They are open, so they
are drawn as lines, never filled. `f.bezier_point(a, b, c, d, t)` gives one coordinate of a point
along the curve for `t` from 0 to 1 — call it once for x and once for y.

![Curves](../gallery/images/curves-01_curves.png)

## Holes

List a hole's corners between `f.begin_contour()` and `f.end_contour()`, inside the shape:

```python
import funground as f


def setup():
    f.size(320, 320)


def draw():
    f.background("white")
    f.fill("gold")
    f.begin_shape()
    for x, y in [(40, 40), (280, 40), (280, 280), (40, 280)]:
        f.vertex(x, y)
    f.begin_contour()
    for x, y in [(100, 100), (220, 100), (220, 220), (100, 220)]:
        f.vertex(x, y)
    f.end_contour()
    f.end_shape(close=True)


f.run()
```

funground cuts the hole out whichever way round you list its corners.

![Holes](../gallery/images/curves-02_holes.png)

**Next:** [10. Interaction](10_interaction.md)
