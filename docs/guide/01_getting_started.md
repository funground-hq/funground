# 1. Getting started

funground is a small Python library for drawing and animation. You write a short Python file,
run it, and a window opens with your picture in it.

## Install

You need Python 3.11 or newer. In a terminal, in the folder where you keep your sketches:

```py
python -m venv .venv
.venv\Scripts\activate        # Windows;  on macOS/Linux:  source .venv/bin/activate
python -m pip install funground
```

On Linux, install the Cairo library first: `sudo apt install libcairo2-dev pkg-config python3-dev`
(Debian or Ubuntu; other distributions have an equivalent package).

## Your first sketch

Save this as `first.py` and run it with `python first.py`:

```python
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("tomato")
    f.circle(320, 200, 120)


f.run()
```

We write `import funground as f` and then use `f.` in front of every funground command. Don't use
`f` as a name for your own variables, for example `with open(...) as f:` — that would hide
funground, and the next `f.circle(...)` would fail.

![Your first sketch](../gallery/images/basics-01_first_sketch.png)

- `import funground as f` — every funground function starts with `f.`
- `setup()` runs once at the start; `f.size(640, 400)` opens a window 640 pixels wide and 400 high.
- `draw()` runs again and again, about 60 times a second. Here it paints the background white,
  chooses a tomato-red fill and draws a circle.
- `f.run()` starts everything. It finds your `setup()` and `draw()` by their names.

Press **Escape** or close the window to stop.

## Where things are

The origin `(0, 0)` is the **top-left** corner. `x` grows to the right and `y` grows **down**.
`f.width` and `f.height` are the size of the window, so the centre is `(f.width / 2, f.height / 2)`.

## More examples

The [Examples Gallery](../gallery/README.md) shows every part of funground with a picture and
the code that makes it. To browse it in a window, run `python tools/gallery_browser.py`. Click
a picture to read its code, and press **Enter** to run it.

**Next:** [2. The sketch: setup, draw and run](02_the_sketch.md)
