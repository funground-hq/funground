"""saved_state and angles

with f.saved_state(): is push() and pop() in one block: whatever the block changes is undone at
the end. rotate() takes degrees; f.radians() converts for math.sin and math.cos.
"""
import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("gold")
    f.stroke("black")
    for angle in range(0, 360, 30):
        with f.saved_state():
            f.translate(200, 200)
            f.rotate(angle)
            f.rect(60, -8, 80, 16)
    # the same ring drawn with trigonometry instead of rotate()
    f.fill("skyblue")
    for angle in range(0, 360, 30):
        x = 460 + 100 * math.cos(f.radians(angle))
        y = 200 + 100 * math.sin(f.radians(angle))
        f.circle(x, y, 20)
    f.fill("black")
    f.text(f"atan2 of (1, 1) is {f.degrees(math.atan2(1, 1)):.0f} degrees", 20, 360)


f.run()
