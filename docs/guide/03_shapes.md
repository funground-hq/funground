# 3. Shapes

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("skyblue")
    f.rect(40, 60, 160, 100)            # top-left x, y, width, height
    f.fill("tomato")
    f.circle(320, 110, 100)             # centre x, y, diameter
    f.fill("gold")
    f.ellipse(520, 110, 160, 80)        # centre x, y, width, height
    f.stroke("navy")
    f.stroke_width(4)
    f.line(40, 260, 600, 340)           # from (x1, y1) to (x2, y2)
    f.stroke_width(12)
    for x in range(60, 600, 60):
        f.point(x, 230)


f.run()
```

![The basic shapes](../gallery/images/shapes-01_basic_shapes.png)

| Function | Placed by |
|---|---|
| `f.rect(x, y, w, h)` | its **top-left** corner |
| `f.circle(x, y, d)` | its **centre**; `d` is the diameter, not the radius |
| `f.ellipse(x, y, w, h)` | its **centre** |
| `f.line(x1, y1, x2, y2)` | its two ends; uses the stroke colour only |
| `f.point(x, y)` | a dot, as wide as the stroke |

Coordinates can have decimals — `f.circle(100.5, 80.25, 40)` — and edges are smoothed.

## More shapes

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("skyblue")
    f.square(30, 30, 100)                                  # top-left corner and size
    f.fill("gold")
    f.triangle(170, 130, 270, 130, 220, 30)                # three corners
    f.fill("seagreen")
    f.quad(310, 40, 420, 30, 400, 130, 330, 120)           # four corners, in order
    f.fill("orchid")
    f.polygon([(520, 30), (600, 70), (580, 130), (480, 130), (460, 70)])
    f.fill("tomato")
    f.arc(100, 280, 140, 140, 0, 270)                      # open (the default)
    f.arc(280, 280, 140, 140, 0, 270, "chord")
    f.arc(460, 280, 140, 140, 0, 270, "pie")


f.run()
```

![More shapes](../gallery/images/shapes-02_more_shapes.png)

| Function | Notes |
|---|---|
| `f.square(x, y, size)` | Placed by its top-left corner, like `rect` |
| `f.triangle(...)`, `f.quad(...)` | Corners in order; the shape is closed and filled |
| `f.polygon(points)` | A list of `(x, y)` points; closed and filled |
| `f.arc(x, y, w, h, start, stop, mode)` | Part of an ellipse centred at `(x, y)`. Angles are in **degrees**, starting at the right (3 o'clock) and turning **clockwise**: 90 is straight down. `"open"` fills the slice but draws the outline only along the curve; `"chord"` closes it with a straight line; `"pie"` closes it through the centre |

For any other outline, build it from points: see [9. Paths and clipping](09_paths_and_clipping.md).

**Next:** [4. Colour](04_colour.md)
