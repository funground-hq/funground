"""Bounce

Change a variable a little in every draw() and you have motion; flip the speed at the edges and
it bounces.
"""
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
        speed = -speed


p.run()
