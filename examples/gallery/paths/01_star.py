"""A star from vertices

begin_shape(), a vertex() for each corner, end_shape(close=True). Closed shapes are filled;
open ones are only stroked.
"""
import math

import playground as p


def star(cx, cy, outer, inner, points):
    p.begin_shape()
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        a = math.pi * i / points - math.pi / 2
        p.vertex(cx + r * math.cos(a), cy + r * math.sin(a))
    p.end_shape(close=True)


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("darkorange")
    p.stroke_width(4)
    star(200, 200, 140, 60, 5)
    p.no_fill()
    p.stroke("navy")
    p.begin_shape()                  # an open zig-zag: stroked, never filled
    for i in range(8):
        p.vertex(380 + i * 30, 140 if i % 2 else 260)
    p.end_shape()


p.run()
