"""A star from vertices

begin_shape(), a vertex() for each corner, end_shape(close=True). Closed shapes are filled;
open ones are only stroked.
"""
import math

import funground as f


def star(cx, cy, outer, inner, points):
    f.begin_shape()
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        a = math.pi * i / points - math.pi / 2
        f.vertex(cx + r * math.cos(a), cy + r * math.sin(a))
    f.end_shape(close=True)


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("gold")
    f.stroke("darkorange")
    f.stroke_width(4)
    star(200, 200, 140, 60, 5)
    f.no_fill()
    f.stroke("navy")
    f.begin_shape()                  # an open zig-zag: stroked, never filled
    for i in range(8):
        f.vertex(380 + i * 30, 140 if i % 2 else 260)
    f.end_shape()


f.run()
