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

## Colour by hue

A **tuple always means red, green, blue** in Playground. For colour by hue, ask for it by name:

| Function | Makes a colour from |
|---|---|
| `p.hsb(hue, saturation, brightness, alpha=255)` | hue 0–360 (0 red, 120 green, 240 blue), saturation and brightness 0–100 |
| `p.hsl(hue, saturation, lightness, alpha=255)` | hue 0–360, saturation and lightness 0–100 (50 is the pure colour) |

Hue goes round: `p.hsb(370, 80, 90)` is the same as `p.hsb(10, 80, 90)`, so
`p.hsb(p.frame_count, 80, 90)` cycles through the rainbow forever.

## Colours you can read and mix

`p.color(...)` turns any colour into one you can ask about: `.red`, `.green`, `.blue`,
`.alpha` (0–255), `.hue` (0–360), `.saturation`, `.brightness` and `.lightness` (0–100).
`p.lerp_color(c1, c2, t)` mixes two colours: 0 gives `c1`, 1 gives `c2`.

```python
import playground as p


def setup():
    p.size(640, 200)


def draw():
    p.background("white")
    p.no_stroke()
    for i in range(24):
        p.fill(p.hsb(i * 15, 90, 95))
        p.rect(20 + i * 25, 30, 25, 60)
    start, end = p.color("tomato"), p.color("royalblue")
    for i in range(11):
        p.fill(p.lerp_color(start, end, i / 10))
        p.circle(47 + i * 54, 150, 44)


p.run()
```

![Hue-based colour](../gallery/images/colour-02_hsb_and_hsl.png)

*Coming from p5 or Processing?* There is no `colorMode()`: write `p.fill(p.hsb(200, 80, 90))`
instead of switching modes, so a tuple never changes meaning halfway through a sketch.

**Next:** [5. Fill, stroke and lines](05_fill_stroke_lines.md)
