# 6. Text

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("black")
    p.text_size(40)
    message = "Hello, Playground!"
    x = (p.width - p.text_width(message)) / 2      # centred
    p.text(message, x, 60)
    p.text_size(18)
    p.text(f"frame {p.frame_count}", 40, 240, color="tomato")


p.run()
```

![Text](../gallery/images/text-01_text.png)

| Function | What it does |
|---|---|
| `p.text(message, x, y)` | Draws `message` with its **top-left** corner at `(x, y)`. Numbers and other values are turned into text. |
| `p.text(..., color=...)` | A colour for this text only; otherwise the fill colour is used (or the stroke if there is no fill). |
| `p.text_size(n)` | The size of later text, in pixels. |
| `p.text_width(message)` | How wide `message` will be at the current size — use it to centre or right-align text. |

Playground draws text with its own built-in font (DejaVu Sans), so text looks the same on every
computer. Letters from many alphabets work, including Greek and Cyrillic.

## Lining text up

`p.text_align()` says which point of the text your `(x, y)` is. The first word is `"left"`,
`"center"` or `"right"`; the second is `"top"`, `"center"`, `"baseline"` or `"bottom"`. The
default is left and top, so without `text_align` the `(x, y)` is the top-left corner.

```python
import playground as p


def setup():
    p.size(640, 200)


def draw():
    p.background("white")
    p.fill("black")
    p.text_size(36)
    p.text_align("center", "center")
    p.text(f"frame {p.frame_count}", p.width / 2, p.height / 2)   # stays centred as it changes


p.run()
```

![Aligning text](../gallery/images/text-02_align.png)

| Function | What it does |
|---|---|
| `p.text_align(horizontal, vertical)` | Which point of the text `(x, y)` is. Leave out `vertical` to keep the current one. |
| `p.text_ascent()` | How far letters reach above the **baseline**, the line letters sit on. |
| `p.text_descent()` | How far letters such as g and y hang below the baseline. |

The alignment is part of the drawing state, so `with p.saved_state():` restores it.

*Coming in Sprint 6:* several lines, word wrap and choosing a font.

**Next:** [7. Animation and time](07_animation_and_time.md)
