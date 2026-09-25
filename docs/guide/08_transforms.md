# 8. Transforms and saved_state

Transforms move, turn and resize **everything you draw afterwards**.

| Function | Effect |
|---|---|
| `p.translate(dx, dy)` | Moves the origin by `(dx, dy)` |
| `p.rotate(degrees)` | Turns around the current origin — `90` is a quarter turn clockwise |
| `p.scale(s)` / `p.scale(sx, sy)` | Grows or shrinks; two numbers stretch differently across and down |
| `p.push()` / `p.pop()` | Save the current transform **and** style; bring them back |
| `with p.saved_state():` | `push()` at the start of the block, `pop()` at the end — even if something goes wrong |

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("black")
    for angle in range(0, 360, 30):
        with p.saved_state():
            p.translate(200, 200)
            p.rotate(angle)
            p.rect(60, -8, 80, 16)


p.run()
```

![saved_state](../gallery/images/transforms-02_saved_state.png)

## Order matters

`p.translate(100, 0)` then `p.rotate(45)` turns the drawing around the **new** origin. The other
way round, the translation itself is turned. Read transforms bottom-up: the last one written is
the first applied to your shape.

## What resets and what stays

- **Transforms reset at the start of every frame.** A `rotate()` in one `draw()` does not carry
  into the next.
- **Style stays.** A `p.fill("blue")` in `draw()` is still in force next frame — unless it was
  inside a `saved_state` block or between `push()` and `pop()`.
- A `push()` without its `pop()` is closed for you at the end of the frame, with a warning.

## Angles

`rotate()` takes **degrees**. Python's `math.sin` and `math.cos` want radians, so convert:
`math.sin(p.radians(30))`, and back with `p.degrees(math.atan2(dy, dx))`.

![Rotating squares](../gallery/images/transforms-01_rotating_squares.png)

**Next:** [9. Paths and clipping](09_paths_and_clipping.md)
