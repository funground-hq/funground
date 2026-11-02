funground is a Python library for drawing, animation, typography, print and sound, made for learning, in the
spirit of Processing, p5.js and DrawBot. It is not p5 and not DrawBot: names, defaults and units differ, and
code written from memory of those libraries is often wrong here. Follow these rules, and look names up in the
API reference instead of guessing.

Install: `python -m pip install funground` (Python 3.11 or newer). On Linux, install the Cairo library first:
`sudo apt install libcairo2-dev pkg-config python3-dev`.

## Two kinds of program

A **sketch** animates: define `setup()` (once) and `draw()` (every frame), and call `f.run()` as the last line.

```python
import funground as f


def setup():
    f.size(400, 300)


def draw():
    f.background("ivory")
    f.no_stroke()
    f.fill("tomato")
    f.circle(f.mouse_x, f.mouse_y, 60)


f.run()
```

A **script** draws once, from top to bottom, with no `draw()`; `f.show()` at the end opens a window on it, and
`f.save()` writes a file. A script never calls `f.run()`.

```python
import funground as f

f.size("A4", margin=f.mm(15))          # a real page: 595 x 842 points, 15 mm kept free on each side
f.background("white")
f.fill(f.cmyk(0, 80, 90, 0))           # exact printing inks in a saved PDF
f.circle(f.width / 2, f.height / 2, 300)
f.save("poster.pdf", bleed=f.mm(3), marks=True)
f.show()
```

## The shorter style

`from funground import *` gives every name without `f.`, and `width`, `mouse_x` and the other live values stay
current. Four names are left out of the star import so that Python's own built-ins keep working: use
`set_pixel` (not `set`), `apply_filter` (not `filter`), `random_number` (not `random`) and `stop` (not `exit`).

```python
from funground import *

size(300, 200)
background("navy")
fill("gold")
for i in range(5):
    circle(40 + i * 55, height / 2, random_number(20, 50))
show()
```

## Rules that differ from p5 and DrawBot

- **Names are snake_case:** `stroke_width` (not `strokeWeight`), `no_fill`, `text_size`, `text_leading` (DrawBot's
  `lineHeight`), `is_mouse_pressed` (a value), `key_pressed()` (a function you define), `map_range` (p5's `map`),
  `distance` (p5's `dist`). There is no `createCanvas`, no `angleMode`, no `oval` and no `BezierPath`: use
  `f.size`, degrees, `f.ellipse` and `f.path()`.
- **Every name has the `f.` prefix** (`import funground as f`), unless the program uses `from funground import *`.
  Never name a variable `f`.
- **Angles are in degrees**, everywhere: `f.rotate(45)`, `f.arc(..., 0, 90)`. `f.radians()` and `f.degrees()`
  convert.
- **The origin is the top-left corner and y grows downwards**, as in p5 (DrawBot's y grows upwards: a DrawBot
  `y` becomes `f.height - y`).
- **`f.circle(x, y, diameter)`**: the centre and the *diameter*. `f.ellipse(x, y, w, h)` takes the centre too;
  `f.rect(x, y, w, h)` takes the top-left corner. `f.rect_mode()` and `f.ellipse_mode()` change that.
- **Colours** are a name (`"tomato"`), a hex string (`"#F05A45"`), a tuple `(r, g, b)` or `(r, g, b, a)` with
  0 to 255, numbers (`f.fill(255, 99, 71)`), `f.hsb(h, s, b)`, `f.cmyk(c, m, y, k)` or a gradient. One number
  is a grey. `f.color_mode("rgb", 1)` makes numbers run from 0 to 1, as in DrawBot; `f.color_mode("hsb")` makes
  them hue 0-360, saturation and brightness 0-100.
- **Text** is placed by its top-left corner by default; `f.text_align("left", "baseline")` places it by its
  baseline, as DrawBot does. `f.text_box(text, x, y, w, h)` wraps text in a box and returns what did not fit.
- **Shapes have a black outline and a white fill to start with.** Call `f.no_stroke()` for DrawBot's look.
- **Sizes are in units:** pixels on screen, points (1/72 inch) on a page. `f.mm()` and `f.inch()` convert real
  measurements, and `f.size("A3")` knows the paper sizes.
- **Randomness:** `f.random(10)` is 0 up to 10, `f.random(5, 10)` is 5 up to 10; `f.random_seed(7)` repeats a
  result. `f.noise(x)` is smooth, from 0 to 1.
- **No `async` or `await`** in sketches, and no `time.sleep()` in `draw()`: funground keeps the time.
- **In the browser** (the Play page, or beside github.dev) the same code runs unchanged. Files from `f.save()`
  stay inside the page; `input()`, MP4 export and choosing a microphone by name work on a computer only.

## Libraries

Sound, the music of India and the camera are libraries, not names on `f`. Sound needs `from funground import sound`;
music of India needs `from funground import sangeet`; the camera needs `from funground import camera`. Then write
`sound.note("C4", 1).play()`, `sangeet.tala("Teentaal")` or `cam = camera.open()`. The 0.1 spellings on `f` do not
exist now: the error says what to write. Two names lost a word on the way: `create_sound` is now `sound.create`, and
`load_sound` is now `sound.load`. The camera's names are `camera.open()`, `camera.names()` and `camera.load_clip()`
(the old `camera`, `cameras` and `load_clip` on `f` do not exist). Name the camera object `cam`, never `camera`, which would hide
the library. The reference has a section for each library.

## Versions

A name with "Since 0.2." under it in the reference needs funground 0.2 or newer. A person with an older funground
(`python -m pip install funground` gives the latest release, which may be older than the documentation) gets an
`AttributeError` for it. Names with no such line work in every release.

## When unsure

Look the name up in the API reference (it lists every public name, its arguments and an example) and the
comparison with p5 and DrawBot. Do not invent a function: if a name is not in the reference, it does not exist.
