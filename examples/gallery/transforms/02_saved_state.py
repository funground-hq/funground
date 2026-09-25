"""saved_state and angles

with p.saved_state(): is push() and pop() in one block: whatever the block changes is undone at
the end. rotate() takes degrees; p.radians() converts for math.sin and math.cos.
"""
import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("black")
    for angle in range(0, 360, 30):
        with p.saved_state():
            p.translate(200, 200)
            p.rotate(angle)
            p.rect(60, -8, 80, 16)
    # the same ring drawn with trigonometry instead of rotate()
    p.fill("skyblue")
    for angle in range(0, 360, 30):
        x = 460 + 100 * math.cos(p.radians(angle))
        y = 200 + 100 * math.sin(p.radians(angle))
        p.circle(x, y, 20)
    p.fill("black")
    p.text(f"atan2 of (1, 1) is {p.degrees(math.atan2(1, 1)):.0f} degrees", 20, 360)


p.run()
