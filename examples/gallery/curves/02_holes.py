"""Shapes with holes

Between begin_contour() and end_contour(), list the corners of a hole. Playground makes the hole
cut out of the shape whichever way round you draw it.
"""
import math

import playground as p


def ring_of_points(cx, cy, r, n):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("darkorange")
    p.stroke_width(3)

    p.begin_shape()                       # a square frame
    for x, y in [(40, 60), (280, 60), (280, 300), (40, 300)]:
        p.vertex(x, y)
    p.begin_contour()
    for x, y in [(100, 120), (220, 120), (220, 240), (100, 240)]:
        p.vertex(x, y)
    p.end_contour()
    p.end_shape(close=True)

    p.fill("skyblue")
    p.stroke("navy")
    p.begin_shape()                       # a wheel: many-sided outline, hexagonal hole
    for x, y in ring_of_points(460, 180, 130, 40):
        p.vertex(x, y)
    p.begin_contour()
    for x, y in ring_of_points(460, 180, 60, 6):
        p.vertex(x, y)
    p.end_contour()
    p.end_shape(close=True)


p.run()
