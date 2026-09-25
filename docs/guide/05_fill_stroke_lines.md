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

*Coming in Sprint 5:* line caps, joins, dashes and `no_smooth()`.

**Next:** [6. Text](06_text.md)
