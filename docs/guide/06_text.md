# 6. Text

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("black")
    f.text_size(40)
    message = "Hello, funground!"
    x = (f.width - f.text_width(message)) / 2      # centred
    f.text(message, x, 60)
    f.text_size(18)
    f.text(f"frame {f.frame_count}", 40, 240, color="tomato")


f.run()
```

![Text](../gallery/images/text-01_text.png)

| Function | What it does |
|---|---|
| `f.text(message, x, y)` | Draws `message` with its **top-left** corner at `(x, y)`. Numbers and other values are turned into text. |
| `f.text(..., color=...)` | A colour for this text only; otherwise the fill colour is used (or the stroke if there is no fill). |
| `f.text_size(n)` | The size of later text, in pixels. |
| `f.text_width(message)` | How wide `message` will be at the current size — use it to centre or right-align text. |

funground draws text with its own built-in font (DejaVu Sans), so text looks the same on every
computer. Letters from many alphabets work, including Greek and Cyrillic.

## Lining text up

`f.text_align()` says which point of the text your `(x, y)` is. The first word is `"left"`,
`"center"` or `"right"`; the second is `"top"`, `"center"`, `"baseline"` or `"bottom"`. The
default is left and top, so without `text_align` the `(x, y)` is the top-left corner.

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background("white")
    f.fill("black")
    f.text_size(36)
    f.text_align("center", "center")
    f.text(f"frame {f.frame_count}", f.width / 2, f.height / 2)   # stays centred as it changes


f.run()
```

![Aligning text](../gallery/images/text-02_align.png)

| Function | What it does |
|---|---|
| `f.text_align(horizontal, vertical)` | Which point of the text `(x, y)` is. Leave out `vertical` to keep the current one. |
| `f.text_ascent()` | How far letters reach above the **baseline**, the line letters sit on. |
| `f.text_descent()` | How far letters such as g and y hang below the baseline. |

The alignment is part of the drawing state, so `with f.saved_state():` restores it.

## Several lines and text boxes

A `"\n"` inside the message starts a new line. `f.text_leading(n)` sets the distance from one
line to the next; `f.text_leading(None)` goes back to the automatic 1.25 × the text size.

For longer text, `f.text_box(message, x, y, width, height)` wraps the words inside a box. It
**returns the text that did not fit**, so you can pour the rest into another box, the way
DrawBot's `textBox()` works:

```py
rest = f.text_box(story, 40, 140, 260, 220)     # first column
rest = f.text_box(rest, 340, 140, 260, 220)     # the rest carries on here
```

`f.text_align()` works inside the box: `"center"` centres each line in the box's width, and
`"bottom"` sits the text on the box's bottom edge.

![Text in boxes and columns](../gallery/images/text-03_text_box.png)

| Function | What it does |
|---|---|
| `f.text_leading(n)` | Distance between lines, in pixels. `None` means automatic. |
| `f.text_box(message, x, y, width, height)` | Wraps `message` inside the box and returns what did not fit. Leave out `height` for a box that grows downwards. |

## Fonts and styles

Every example so far has used funground's built-in font, DejaVu Sans, which is why text looks
the same on every computer. `f.text_style(style)` picks one of its four real styles: `"normal"`
(the default), `"bold"`, `"italic"`, or `"bold_italic"`.

If you want a font of your own, `f.load_font(path)` reads a `.ttf` or `.otf` file from disk and
gives you back a font. A relative path is looked for next to your sketch file first, then in the
current folder. `f.text_font(font)` switches later text to use it; `f.text_font(None)` goes back
to the built-in family, remembering whichever style you last chose with `f.text_style()`. While a
loaded font is in use, `f.text_style()` has no effect — load the bold or italic file itself
instead, the way you would with any font on your computer.

```python
import funground as f


def setup():
    f.size(640, 200)


def draw():
    f.background("white")
    f.fill("black")
    f.text_size(28)
    f.text_style("bold")
    f.text("Bold, built in", 30, 30)
    f.text_style("italic")
    f.text("Italic, built in", 30, 80)
    f.text_style("normal")               # back to the default built-in style
    f.text("Normal again", 30, 130)


f.run()
```

Loading a font of your own looks like this:

```py
mono = f.load_font("fonts/DejaVuSansMono.ttf")
f.text_font(mono)
f.text("Now in a loaded font", 30, 30)
f.text_font(None)                        # back to the built-in family
```

`f.text_font(font, size=n)` sets the text size at the same time, so you don't need a separate
call to `f.text_size()`.

![Fonts and styles](../gallery/images/text-04_fonts.png)

| Function | What it does |
|---|---|
| `f.text_style(style)` | Choose one of the built-in family's four styles. |
| `f.load_font(path)` | Load a font file; pass the result to `f.text_font()`. |
| `f.text_font(font, size=None)` | Use a loaded font (or a path, or `None` for the built-in family) for later text. |

Both are part of the drawing state, so `with f.saved_state():` restores them, exactly like
`f.fill()` or `f.text_size()`.

**Next:** [7. Animation and time](07_animation_and_time.md)
