"""Makes take.gif, the short clip that 08_play_a_take.py loads.

This is a funground script (no window, no draw()). Run it from this folder:

    python make_take.py

Every page is one frame of the GIF: a paper boat rocking on waves under a moving sun, two seconds at 12 frames a
second. It stands in for a take saved by the photo booth. Everything here is original and free to use (CC0).
"""
import math

import funground as f

WIDTH, HEIGHT = 160, 120
FRAMES = 24

f.size(WIDTH, HEIGHT)
f.frame_duration(1 / 12)
f.no_stroke()
for i in range(FRAMES):
    if i > 0:
        f.new_page()
    turn = i / FRAMES * 2 * math.pi                     # once round in the whole clip, so it loops smoothly
    f.background(f.linear_gradient(0, 0, 0, HEIGHT, ["#ffd6a5", "#a0c4ff"]))
    f.fill("#ffb703")
    f.circle(30 + i * 4, 30, 22)                        # the sun moves across
    f.fill("#023e8a")
    f.rect(0, 84, WIDTH, HEIGHT - 84)
    with f.saved_state():                               # the boat rocks on the water
        f.translate(WIDTH / 2, 82 + 3 * math.sin(turn))
        f.rotate(8 * math.sin(turn))
        f.fill("#fefae0")
        f.polygon([(-26, -4), (26, -4), (16, 10), (-16, 10)])
        f.triangle(-2, -6, -2, -34, 18, -8)
    f.fill("#0096c7")
    for x in range(0, WIDTH + 20, 20):                  # waves in front
        f.circle(x - 10 + 6 * math.sin(turn + x), 92, 18)

f.save("take.gif")
