# 5. Fill, stroke and lines

Every shape has an inside (**fill**) and an outline (**stroke**).

| Function | Effect on later shapes |
|---|---|
| `f.fill(colour)` / `f.no_fill()` | Colour the inside / leave it empty |
| `f.stroke(colour)` / `f.no_stroke()` | Colour the outline / draw no outline |
| `f.stroke_width(n)` | Outline and line thickness in pixels (at least 1) |

The defaults are a white fill, a black stroke and a stroke width of 1. The stroke is **centred
on the edge**: a 10-pixel outline is 5 pixels outside the shape and 5 inside.

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("whitesmoke")
    f.fill("gold")
    f.stroke("black")
    f.stroke_width(3)
    f.circle(120, 140, 140)
    f.no_fill()
    f.stroke("tomato")
    f.stroke_width(10)
    f.rect(240, 70, 140, 140)
    f.fill("skyblue")
    f.no_stroke()
    f.ellipse(520, 140, 160, 100)


f.run()
```

![Fill and stroke](../gallery/images/lines-01_fill_and_stroke.png)

Settings stay in force until you change them — including into the next frame. To change them
for a few shapes only, see `with f.saved_state():` in [8. Transforms](08_transforms.md).

## Line ends, corners and dashes

| Function | Choices |
|---|---|
| `f.stroke_cap(cap)` | `"round"` (default), `"square"` (sticks out half the width past the end), `"butt"` (stops flat at the end) |
| `f.stroke_join(join)` | `"round"` (default), `"miter"` (sharp point), `"bevel"` (corner cut off) |
| `f.miter_limit(n)` | How far a sharp miter corner may stick out before it is cut off (default 10) |
| `f.stroke_dash(pattern, offset=0)` | Dashes: `f.stroke_dash(10)` or a list of dash and gap lengths, `f.stroke_dash([12, 4, 2, 4])` |
| `f.no_dash()` | Solid lines again |

These are part of the style, like `fill`: a `saved_state` block puts them back.

![Caps, joins and dashes](../gallery/images/lines-02_caps_joins_dashes.png)

## Sharp pixels

Edges are normally smoothed. `f.no_smooth()` switches that off, so every pixel is either the
shape's colour or not — just right for pixel art. `f.smooth()` switches it back. This is a
setting for the whole sketch, not part of the style: `saved_state` does not undo it.

```python
import funground as f


def setup():
    f.size(320, 200)
    f.no_smooth()


def draw():
    f.background("black")
    f.no_stroke()
    f.fill("lime")
    f.scale(20)
    f.rect(2, 2, 3, 3)
    f.rect(8, 4, 2, 4)


f.run()
```

![Pixel art](../gallery/images/lines-03_pixel_art.png)

## Mixing, see-through and shadows

Three settings change how everything drawn after them lands on the canvas. Like `f.fill()`,
they last until you change them, and `with f.saved_state():` restores them.

| Function | What it does |
|---|---|
| `f.blend_mode(mode)` | How new drawing mixes with what is there. `"multiply"` darkens like overlapping inks, `"screen"` and `"add"` lighten like overlapping lights, `"difference"` inverts. `"normal"` is the default. |
| `f.opacity(amount)` | Makes everything see-through: 0 is invisible, 255 is solid. |
| `f.shadow(x, y, blur, color)` | A shadow moved by `(x, y)` and softened by `blur` pixels. The colour defaults to half-transparent black. |
| `f.no_shadow()` | No more shadows. |

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background("white")
    f.no_stroke()
    f.blend_mode("multiply")
    for i, colour in enumerate(["cyan", "magenta", "yellow"]):
        f.fill(colour)
        f.circle(250 + i * 70, 100, 140)
    f.blend_mode("normal")


f.run()
```

![Blend modes, opacity and shadows](../gallery/images/compositing-01_blend_opacity_shadow.png)

`f.background()` ignores all three, so each frame still starts clean.

**Next:** [6. Text](06_text.md)
