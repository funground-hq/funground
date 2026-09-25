# 5. Fill, stroke and lines

Every shape has an inside (**fill**) and an outline (**stroke**).

| Function | Effect on later shapes |
|---|---|
| `p.fill(colour)` / `p.no_fill()` | Colour the inside / leave it empty |
| `p.stroke(colour)` / `p.no_stroke()` | Colour the outline / draw no outline |
| `p.stroke_width(n)` | Outline and line thickness in pixels (at least 1) |

The defaults are a white fill, a black stroke and a stroke width of 1. The stroke is **centred
on the edge**: a 10-pixel outline is 5 pixels outside the shape and 5 inside.

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("whitesmoke")
    p.fill("gold")
    p.stroke("black")
    p.stroke_width(3)
    p.circle(120, 140, 140)
    p.no_fill()
    p.stroke("tomato")
    p.stroke_width(10)
    p.rect(240, 70, 140, 140)
    p.fill("skyblue")
    p.no_stroke()
    p.ellipse(520, 140, 160, 100)


p.run()
```

![Fill and stroke](../gallery/images/lines-01_fill_and_stroke.png)

Settings stay in force until you change them — including into the next frame. To change them
for a few shapes only, see `with p.saved_state():` in [8. Transforms](08_transforms.md).

## Line ends, corners and dashes

| Function | Choices |
|---|---|
| `p.stroke_cap(cap)` | `"round"` (default), `"square"` (sticks out half the width past the end), `"butt"` (stops flat at the end) |
| `p.stroke_join(join)` | `"round"` (default), `"miter"` (sharp point), `"bevel"` (corner cut off) |
| `p.miter_limit(n)` | How far a sharp miter corner may stick out before it is cut off (default 10) |
| `p.stroke_dash(pattern, offset=0)` | Dashes: `p.stroke_dash(10)` or a list of dash and gap lengths, `p.stroke_dash([12, 4, 2, 4])` |
| `p.no_dash()` | Solid lines again |

These are part of the style, like `fill`: a `saved_state` block puts them back.

![Caps, joins and dashes](../gallery/images/lines-02_caps_joins_dashes.png)

## Sharp pixels

Edges are normally smoothed. `p.no_smooth()` switches that off, so every pixel is either the
shape's colour or not — just right for pixel art. `p.smooth()` switches it back. This is a
setting for the whole sketch, not part of the style: `saved_state` does not undo it.

```python
import playground as p


def setup():
    p.size(320, 200)
    p.no_smooth()


def draw():
    p.background("black")
    p.no_stroke()
    p.fill("lime")
    p.scale(20)
    p.rect(2, 2, 3, 3)
    p.rect(8, 4, 2, 4)


p.run()
```

![Pixel art](../gallery/images/lines-03_pixel_art.png)

**Next:** [6. Text](06_text.md)
