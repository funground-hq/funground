# 4. Colour

Wherever Playground wants a colour, you can give it in any of these forms:

| Form | Example | Notes |
|---|---|---|
| A name | `"tomato"`, `"skyblue"`, `"gray50"` | Hundreds of names; capitals and spaces are ignored |
| An `(r, g, b)` tuple | `(255, 99, 71)` | Red, green, blue, each 0–255 |
| An `(r, g, b, a)` tuple | `(255, 0, 0, 120)` | The last number is opacity: 0 invisible, 255 solid |
| Hex | `"#FF6347"`, `"#FF634780"` | As on web pages; the optional last pair is opacity |

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    p.fill((255, 0, 0, 120))
    p.circle(260, 305, 150)
    p.fill((0, 0, 255, 120))
    p.circle(360, 305, 150)
    p.fill((0, 200, 0, 120))
    p.circle(310, 245, 150)


p.run()
```

![Four ways to say a colour](../gallery/images/colour-01_colour_forms.png)

Translucent colours mix where they overlap.

*Coming in Sprint 5:* `p.hsb(...)`, `p.hsl(...)` for hue-based colour, colour objects and
`p.lerp_color`. Playground has no `color_mode()`: a tuple always means red, green, blue.

**Next:** [5. Fill, stroke and lines](05_fill_stroke_lines.md)
