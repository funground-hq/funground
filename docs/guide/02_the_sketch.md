# 2. The sketch: setup, draw and run

Every Playground program has the same shape:

```python
import playground as p


def setup():          # optional: runs once
    p.size(640, 400, title="my sketch", fps=60)


def draw():           # required: runs every frame
    p.background("midnightblue")
    p.fill("gold")
    p.no_stroke()
    p.circle(40 + p.frame_count * 8, p.height / 2, 30)
    if p.frame_count > 600:
        p.stop()


p.run()
```

![setup and draw](../gallery/images/basics-02_setup_and_draw.png)

| | What it does |
|---|---|
| `p.size(w, h, title=..., fps=...)` | Opens (or resizes) the window. Without `setup()`, you get a 640 × 480 window. |
| `draw()` | Called once per frame. Draw the whole picture again each time. |
| `p.frame_count` | Frames completed so far; `0` during the first `draw()`. |
| `p.width`, `p.height` | The window size. |
| `p.stop()` | Ends the sketch after this `draw()`. |
| `p.run(max_frames=300)` | Stops by itself after 300 frames — handy for tests and screenshots. |

## Variables that change

A variable made at the top of the file and changed inside `draw()` needs `global`:

```py
x = 50

def draw():
    global x          # draw() changes x, so Python needs this line
    x += 2
```

## Clearing the frame

`p.background(...)` paints the whole window. Call it first in `draw()` to start each frame
clean; leave it out and everything you drew before stays — useful for trails and paintings.

**Next:** [3. Shapes](03_shapes.md)
