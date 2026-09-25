# 1. Getting started

Playground is a small Python library for drawing and animation. You write a short Python file,
run it, and a window opens with your picture in it.

## Install

You need Python 3.11 or newer. In a terminal, in the folder where you keep your sketches:

```py
python -m venv .venv
.venv\Scripts\activate        # Windows;  on macOS/Linux:  source .venv/bin/activate
python -m pip install playground
```

## Your first sketch

Save this as `first.py` and run it with `python first.py`:

```python
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("tomato")
    p.circle(320, 200, 120)


p.run()
```

![Your first sketch](../gallery/images/basics-01_first_sketch.png)

- `import playground as p` — every Playground function starts with `p.`
- `setup()` runs once at the start; `p.size(640, 400)` opens a window 640 pixels wide and 400 high.
- `draw()` runs again and again, about 60 times a second. Here it paints the background white,
  chooses a tomato-red fill and draws a circle.
- `p.run()` starts everything. It finds your `setup()` and `draw()` by their names.

Press **Escape** or close the window to stop.

## Where things are

The origin `(0, 0)` is the **top-left** corner. `x` grows to the right and `y` grows **down**.
`p.width` and `p.height` are the size of the window, so the centre is `(p.width / 2, p.height / 2)`.

**Next:** [2. The sketch: setup, draw and run](02_the_sketch.md)
