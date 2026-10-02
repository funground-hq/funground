"""Layers: a sky that stays and a trail that builds up

`with f.layer("name"):` sends everything drawn inside the block to a see-through layer that
sits over the canvas. A layer keeps its drawing from one frame to the next. Here the canvas is
wiped and redrawn every frame, yet the "trail" layer keeps every dot the ball leaves behind.
The "sky" layer is drawn once, in the first frame, and never again. hide_layer() and
show_layer() switch it off and on; it keeps its stars while it is hidden.
"""
import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("midnightblue")            # the canvas starts afresh every frame

    if f.frame_count == 0:
        with f.layer("sky"):                # drawn once: the layer remembers it
            f.no_stroke()
            f.fill("white")
            for i in range(40):
                f.circle((i * 97) % 640, (i * 53) % 170, 2 + i % 3)
            f.fill("khaki")
            f.circle(540, 70, 50)

    t = f.frame_count
    if t % 40 == 20:                        # the sky blinks off for a moment...
        f.hide_layer("sky")
    elif t % 40 == 25:
        f.show_layer("sky")                 # ...and back on: it kept its stars all the time
    x = 40 + t * 10
    y = 260 + 80 * math.sin(t * 0.3)

    with f.layer("trail"):                  # one dot a frame, and each one stays
        f.no_stroke()
        f.fill(255, 140, 60, 140)
        f.circle(x, y, 14)

    f.fill("tomato")                        # the ball itself is on the canvas, under the layers
    f.no_stroke()
    f.circle(x, y, 30)


f.run()
