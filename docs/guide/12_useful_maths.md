# 12. Useful maths

Playground adds a few helpers that come up all the time in drawing. For everything else —
`sqrt`, `sin`, `cos`, `atan2`, `pi`, `floor` — use Python's own `math` module
(`import math`). Remember that `p.rotate()` takes degrees while `math.sin` wants radians:
convert with `p.radians()` and `p.degrees()`.

| Helper | What it gives | Example |
|---|---|---|
| `p.map_range(v, a1, b1, a2, b2)` | `v` re-scaled from the range `a1..b1` to `a2..b2` | `p.map_range(p.mouse_x, 0, p.width, 0, 255)` |
| `p.map_range(..., clamp=True)` | the same, kept inside `a2..b2` | |
| `p.lerp(a, b, t)` | the number `t` of the way from `a` to `b` (0 → `a`, 1 → `b`) | `p.lerp(0, 100, 0.25)` is `25` |
| `p.norm(v, a, b)` | where `v` sits between `a` and `b`, as 0 to 1 | `p.norm(15, 10, 20)` is `0.5` |
| `p.mag(x, y)` | the length of the arrow `(x, y)` | `p.mag(3, 4)` is `5` |
| `p.constrain(v, low, high)` | `v`, kept between `low` and `high` | |
| `p.distance(x1, y1, x2, y2)` | how far apart two points are | |

(It is called `map_range`, not `map`, so it never hides Python's own `map`.)

```python
import playground as p


def setup():
    p.size(640, 200)


def draw():
    p.background("white")
    p.no_stroke()
    for i in range(12):
        x = p.map_range(i, 0, 11, 40, 600)
        shade = p.map_range(i, 0, 11, 230, 30)
        p.fill((shade, shade, 255))
        p.circle(x, 100, 40)


p.run()
```

![Mapping and blending](../gallery/images/maths-01_map_and_lerp.png)

**Next:** [13. Saving your work](13_saving_your_work.md)
