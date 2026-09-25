# 7. Animation and time

`draw()` runs again and again. Change a number a little each time and the picture moves.

```python
import playground as p

x = 60
speed = 7


def setup():
    p.size(640, 400)


def draw():
    global x, speed
    p.background("white")
    p.fill("tomato")
    p.circle(x, p.height / 2, 80)
    x += speed
    if x > p.width - 40 or x < 40:
        speed = -speed          # bounce


p.run()
```

![Bounce](../gallery/images/animation-01_bounce.png)

## Moving by time, not by frames

A slow computer runs fewer frames per second, so `x += 7` moves more slowly there.
`p.delta_time` is the number of seconds the previous frame took; multiply a speed by it and the
motion is the same everywhere:

```py
x += 150 * p.delta_time      # 150 pixels per second
```

| Value | Meaning |
|---|---|
| `p.frame_count` | Frames completed since the start |
| `p.delta_time` | Seconds taken by the previous frame (`0.0` in the first) |
| `p.size(..., fps=30)` | Ask for 30 frames per second instead of 60 |

## Pausing: no_loop, loop and redraw

| Function | What it does |
|---|---|
| `p.no_loop()` | Stop calling `draw()` every frame. The window stays open. `draw()` still runs **once** at the start — even if `no_loop()` is in `setup()` — so a still picture needs nothing else |
| `p.loop()` | Call `draw()` every frame again |
| `p.redraw()` | Call `draw()` just once more, e.g. when a key is pressed |
| `p.is_looping()` | `True` while `draw()` runs every frame |
| `p.exit()` | End the sketch — the same as `p.stop()` |

`p.frame_count` only counts frames that were actually drawn.

## Clocks and timers

| Function | Gives |
|---|---|
| `p.millis()` | Whole milliseconds since the sketch started |
| `p.frame_rate()` | Frames per second actually achieved |
| `p.second()`, `p.minute()`, `p.hour()` | The computer's clock |
| `p.day()`, `p.month()`, `p.year()` | Today's date |

![A clock](../gallery/images/animation-03_clock.png)

**Next:** [8. Transforms and saved_state](08_transforms.md)
