"""Bounce

Change a variable a little in every draw() and you have motion; flip the speed at the edges and
it bounces.
"""
import funground as f

x = 60
speed = 7


def setup():
    f.size(640, 400)


def draw():
    global x, speed
    f.background("white")
    f.fill("tomato")
    f.circle(x, f.height / 2, 80)
    x += speed
    if x > f.width - 40 or x < 40:
        speed = -speed


f.run()
