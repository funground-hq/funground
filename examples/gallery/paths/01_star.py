"""A star from vertices

A five-pointed star is built from ten corners, and an open zig-zag is drawn beside it. The star is
filled and the zig-zag is only a line.

How it works:
- f.begin_shape() starts a shape. Each f.vertex(x, y) adds a corner. f.end_shape() finishes it.
- f.end_shape(close=True) joins the last corner back to the first. A closed shape is filled and
  stroked. An open one is only stroked.
- The star() function alternates between a big radius and a small one. That makes the points and
  the dents.
- Each corner is found with cos and sin of an angle. math.pi * i / points steps round half a
  turn per two corners.
- f.no_fill() makes the zig-zag a plain line, and f.stroke() sets its colour.

Make it yours:
- Change the last number in star(200, 200, 140, 60, 5): try 7 for a seven-pointed star.
- Change the inner radius, 60: a bigger number gives fatter points.
- Change the colours in f.fill("gold") and f.stroke("darkorange"), or the f.stroke_width(4).
- Change the zig-zag's f.end_shape() to f.end_shape(close=True) and watch it join up.
- Draw a second star with a different size at another place: star(480, 80, 50, 20, 5).
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
