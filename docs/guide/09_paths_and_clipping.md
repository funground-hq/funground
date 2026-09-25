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

*Coming in Sprint 5:* Bézier, quadratic and smooth curves through points, holes in shapes,
and `bezier()` / `curve()` in one call (these follow Processing's names).

**Next:** [10. Interaction](10_interaction.md)
