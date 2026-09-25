# 3. Shapes

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("skyblue")
    p.rect(40, 60, 160, 100)            # top-left x, y, width, height
    p.fill("tomato")
    p.circle(320, 110, 100)             # centre x, y, diameter
    p.fill("gold")
    p.ellipse(520, 110, 160, 80)        # centre x, y, width, height
    p.stroke("navy")
    p.stroke_width(4)
    p.line(40, 260, 600, 340)           # from (x1, y1) to (x2, y2)
    p.stroke_width(12)
    for x in range(60, 600, 60):
        p.point(x, 230)


p.run()
```

![The basic shapes](../gallery/images/shapes-01_basic_shapes.png)

| Function | Placed by |
|---|---|
| `p.rect(x, y, w, h)` | its **top-left** corner |
| `p.circle(x, y, d)` | its **centre**; `d` is the diameter, not the radius |
| `p.ellipse(x, y, w, h)` | its **centre** |
| `p.line(x1, y1, x2, y2)` | its two ends; uses the stroke colour only |
| `p.point(x, y)` | a dot, as wide as the stroke |

Coordinates can have decimals — `p.circle(100.5, 80.25, 40)` — and edges are smoothed.

## More shapes

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("skyblue")
    p.square(30, 30, 100)                                  # top-left corner and size
    p.fill("gold")
    p.triangle(170, 130, 270, 130, 220, 30)                # three corners
    p.fill("seagreen")
    p.quad(310, 40, 420, 30, 400, 130, 330, 120)           # four corners, in order
    p.fill("orchid")
    p.polygon([(520, 30), (600, 70), (580, 130), (480, 130), (460, 70)])
    p.fill("tomato")
    p.arc(100, 280, 140, 140, 0, 270)                      # open (the default)
    p.arc(280, 280, 140, 140, 0, 270, "chord")
    p.arc(460, 280, 140, 140, 0, 270, "pie")


p.run()
```

![More shapes](../gallery/images/shapes-02_more_shapes.png)

| Function | Notes |
|---|---|
| `p.square(x, y, size)` | Placed by its top-left corner, like `rect` |
| `p.triangle(...)`, `p.quad(...)` | Corners in order; the shape is closed and filled |
| `p.polygon(points)` | A list of `(x, y)` points; closed and filled |
| `p.arc(x, y, w, h, start, stop, mode)` | Part of an ellipse centred at `(x, y)`. Angles are in **degrees**, starting at the right (3 o'clock) and turning **clockwise**: 90 is straight down. `"open"` fills the slice but draws the outline only along the curve; `"chord"` closes it with a straight line; `"pie"` closes it through the centre |

For any other outline, build it from points: see [9. Paths and clipping](09_paths_and_clipping.md).

**Next:** [4. Colour](04_colour.md)
