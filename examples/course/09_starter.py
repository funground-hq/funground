# Original Funground course sketch. CC0; see ../LICENSE.

import math
import funground as f

CYCLE_FRAMES = 120

def setup():
    f.size(420, 260, fps=60)

def draw():
    f.background("#f3efe6")
    phase = (f.frame_count % CYCLE_FRAMES) / CYCLE_FRAMES
    progress = (1 - math.cos(2 * math.pi * phase)) / 2
    f.no_stroke()
    f.fill("#e76f51")
    f.circle(50 + progress*320, 120, 36)
    f.fill("#264653")
    f.text_size(16)
    f.text("One mark, one repeating journey", 30, 210)
    if f.frame_count == 0:
        f.save("09_starter.png")

f.run()
