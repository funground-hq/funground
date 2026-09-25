# 9. Paths and clipping

## Shapes from points

List the corners between `p.begin_shape()` and `p.end_shape()`:

```python
import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("darkorange")
    p.stroke_width(4)
    p.begin_shape()
    for i in range(10):
        r = 140 if i % 2 == 0 else 60
        a = math.pi * i / 5 - math.pi / 2
        p.vertex(200 + r * math.cos(a), 200 + r * math.sin(a))
    p.end_shape(close=True)


p.run()
```

![A star from vertices](../gallery/images/paths-01_star.png)

`end_shape(close=True)` joins the last point to the first and fills the shape.
`end_shape()` leaves it **open**: open shapes are only stroked, never filled.

## Reusable paths

`p.path()` builds a shape once so you can draw it many times:

```py
leaf = p.path().move_to(0, -40).line_to(24, 0).line_to(0, 40).line_to(-24, 0).close()
p.draw_path(leaf)
```

`move_to`, `line_to`, `curve_to` and `quad_to` add to the path; `close()` closes it.
`p.draw_path(path)` fills (if closed) and strokes it with the current style, and transforms
apply to it like to any shape.

## Clipping

`p.clip(path)` keeps everything drawn afterwards **inside** the path. It lasts until the end of
the `saved_state` block (or the matching `pop()`), so always clip inside one:

```py
with p.saved_state():
    p.clip(window)
    ...                       # drawn only inside window
```

![Paths and clipping](../gallery/images/paths-02_path_and_clip.png)

`p.no_clip()` switches clipping off until the end of its own `saved_state` block; when that block
ends, the clip from outside it comes back.

![Clipping on and off](../gallery/images/paths-03_no_clip.png)

## Curves

Inside a shape, three kinds of curve follow Processing's names:

| Function | What it does |
|---|---|
| `p.bezier_vertex(cx1, cy1, cx2, cy2, x, y)` | A curve from the previous point to `(x, y)` that bends toward two control points |
| `p.quadratic_vertex(cx, cy, x, y)` | The same with one control point |
| `p.curve_vertex(x, y)` | A smooth curve **through** the points. The first and last points only steer the curve, so give at least four |
| `p.curve_tightness(t)` | 0 (default) for smooth curves, up to 1 for straight lines |

For a single curve there are `p.bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)` and
`p.curve(x1, y1, x2, y2, x3, y3, x4, y4)` (from point 2 to point 3). They are open, so they
are drawn as lines, never filled. `p.bezier_point(a, b, c, d, t)` gives one coordinate of a point
along the curve for `t` from 0 to 1 — call it once for x and once for y.

![Curves](../gallery/images/curves-01_curves.png)

## Holes

List a hole's corners between `p.begin_contour()` and `p.end_contour()`, inside the shape:

```python
import playground as p


def setup():
    p.size(320, 320)


def draw():
    p.background("white")
    p.fill("gold")
    p.begin_shape()
    for x, y in [(40, 40), (280, 40), (280, 280), (40, 280)]:
        p.vertex(x, y)
    p.begin_contour()
    for x, y in [(100, 100), (220, 100), (220, 220), (100, 220)]:
        p.vertex(x, y)
    p.end_contour()
    p.end_shape(close=True)


p.run()
```

Playground cuts the hole out whichever way round you list its corners.

![Holes](../gallery/images/curves-02_holes.png)

**Next:** [10. Interaction](10_interaction.md)
