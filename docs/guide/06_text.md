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

*Coming in Sprint 6:* alignment, several lines, word wrap and choosing a font.

**Next:** [7. Animation and time](07_animation_and_time.md)
