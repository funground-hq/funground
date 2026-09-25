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

For any other outline, build it from points: see [9. Paths and clipping](09_paths_and_clipping.md).

*Coming in Sprint 5:* `square`, `triangle`, `quad`, `polygon` and `arc`.

**Next:** [4. Colour](04_colour.md)
