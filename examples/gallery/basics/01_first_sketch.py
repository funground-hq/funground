"""Your first sketch

A window, a background and one circle: the three lines every sketch starts from.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("tomato")
    f.circle(320, 200, 120)


f.run()
