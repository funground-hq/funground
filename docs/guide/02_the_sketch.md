# 2. The sketch: setup, draw and run

Every funground program has the same shape:

```python
import funground as f


def setup():          # optional: runs once
    f.size(640, 400, title="my sketch", fps=60)


def draw():           # required: runs every frame
    f.background("midnightblue")
    f.fill("gold")
    f.no_stroke()
    f.circle(40 + f.frame_count * 8, f.height / 2, 30)
    if f.frame_count > 600:
        f.stop()


f.run()
```

![setup and draw](../gallery/images/basics-02_setup_and_draw.png)

| | What it does |
|---|---|
| `f.size(w, h, title=..., fps=...)` | Opens (or resizes) the window. Without `setup()`, you get a 640 × 480 window. |
| `draw()` | Called once per frame. Draw the whole picture again each time. |
| `f.frame_count` | Frames completed so far; `0` during the first `draw()`. |
| `f.width`, `f.height` | The window size. |
| `f.stop()` | Ends the sketch after this `draw()`. |
| `f.run(max_frames=300)` | Stops by itself after 300 frames — handy for tests and screenshots. |

## Variables that change

A variable made at the top of the file and changed inside `draw()` needs `global`:

```py
x = 50

def draw():
    global x          # draw() changes x, so Python needs this line
    x += 2
```

## Clearing the frame

`f.background(...)` paints the whole window. Call it first in `draw()` to start each frame
clean; leave it out and everything you drew before stays — useful for trails and paintings.

## The window

| Function | What it does |
|---|---|
| `f.resize_canvas(width, height)` | A new size while the sketch runs; `f.width` and `f.height` follow. |
| `f.full_screen()` | Fill the whole screen. Use it in `setup()` instead of `f.size()`. `f.width` and `f.height` become the screen's size. Escape still ends the sketch. |
| `f.cursor(kind)` | The mouse pointer over the canvas: `"arrow"` (the default), `"cross"`, `"hand"`, `"move"`, `"text"` or `"wait"`. |
| `f.no_cursor()` | Hide the pointer, for example in a full-screen piece. |

A sketch that places everything using `f.width` and `f.height` fits any size, including full
screen.

![The window: cursor, size and full screen](../gallery/images/interaction-04_window.png)

**Next:** [3. Shapes](03_shapes.md)
