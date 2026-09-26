# 4. Colour

Wherever funground wants a colour, you can give it in any of these forms:

| Form | Example | Notes |
|---|---|---|
| A name | `"tomato"`, `"skyblue"`, `"gray50"` | Hundreds of names; capitals and spaces are ignored |
| An `(r, g, b)` tuple | `(255, 99, 71)` | Red, green, blue, each 0–255 |
| An `(r, g, b, a)` tuple | `(255, 0, 0, 120)` | The last number is opacity: 0 invisible, 255 solid |
| Hex | `"#FF6347"`, `"#FF634780"` | As on web pages; the optional last pair is opacity |

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    f.fill((255, 0, 0, 120))
    f.circle(260, 305, 150)
    f.fill((0, 0, 255, 120))
    f.circle(360, 305, 150)
    f.fill((0, 200, 0, 120))
    f.circle(310, 245, 150)


f.run()
```

![Four ways to say a colour](../gallery/images/colour-01_colour_forms.png)

Translucent colours mix where they overlap.

## Colour by hue

A **tuple always means red, green, blue** in funground. For colour by hue, ask for it by name:

| Function | Makes a colour from |
|---|---|
| `f.hsb(hue, saturation, brightness, alpha=255)` | hue 0–360 (0 red, 120 green, 240 blue), saturation and brightness 0–100 |
| `f.hsl(hue, saturation, lightness, alpha=255)` | hue 0–360, saturation and lightness 0–100 (50 is the pure colour) |

Hue goes round: `f.hsb(370, 80, 90)` is the same as `f.hsb(10, 80, 90)`, so
`f.hsb(f.frame_count, 80, 90)` cycles through the rainbow forever.

## Colours you can read and mix

`f.color(...)` turns any colour into one you can ask about: `.red`, `.green`, `.blue`,
`.alpha` (0–255), `.hue` (0–360), `.saturation`, `.brightness` and `.lightness` (0–100).
`f.lerp_color(c1, c2, t)` mixes two colours: 0 gives `c1`, 1 gives `c2`.

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background("white")
    f.no_stroke()
    for i in range(24):
        f.fill(f.hsb(i * 15, 90, 95))
        f.rect(20 + i * 25, 30, 25, 60)
    start, end = f.color("tomato"), f.color("royalblue")
    for i in range(11):
        f.fill(f.lerp_color(start, end, i / 10))
        f.circle(47 + i * 54, 150, 44)


f.run()
```

![Hue-based colour](../gallery/images/colour-02_hsb_and_hsl.png)

*Coming from p5 or Processing?* There is no `colorMode()`: write `f.fill(f.hsb(200, 80, 90))`
instead of switching modes, so a tuple never changes meaning halfway through a sketch.

## Gradients

A gradient blends colours smoothly. Make one, then use it anywhere a colour goes: in
`f.fill()`, `f.stroke()`, `f.background()`, or `f.text(..., color=...)`.

| Function | Blends |
|---|---|
| `f.linear_gradient(x1, y1, x2, y2, colors)` | along the line from `(x1, y1)` to `(x2, y2)` |
| `f.radial_gradient(x, y, radius, colors)` | outward from the centre `(x, y)` to `radius` |

`colors` is a list of two or more colours. Add `stops=[0, 0.3, 1]`, one number from 0 to 1 per
colour, to say where each colour sits; otherwise they are spread evenly. A colour with a fourth
value fades to transparent.

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background(f.linear_gradient(0, 0, 0, 200, ["midnightblue", "coral"]))
    f.no_stroke()
    f.fill(f.radial_gradient(320, 160, 80, ["lightyellow", "gold", (255, 140, 0, 0)]))
    f.circle(320, 160, 160)


f.run()
```

![Gradients](../gallery/images/colour-03_gradients.png)

A gradient's positions are measured in the same space as the shapes, so after `f.translate()`
or `f.rotate()` the gradient moves and turns with the shape. Saved as PDF or SVG, a gradient
stays smooth at any zoom.

**Next:** [5. Fill, stroke and lines](05_fill_stroke_lines.md)
