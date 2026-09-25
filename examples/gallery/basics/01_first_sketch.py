"""Your first sketch

A window, a background and one circle: the three lines every sketch starts from.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("tomato")
    p.circle(320, 200, 120)


p.run()
