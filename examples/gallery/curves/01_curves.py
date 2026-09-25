"""Curves

bezier_vertex bends toward two control points; curve_vertex draws a smooth curve through the
points (the first and last only steer it); curve_tightness straightens it. bezier and curve draw
one curve in a single call; bezier_point and bezier_tangent find places and directions along it.
"""
import math

import playground as p

points = [(40, 330), (80, 230), (160, 300), (240, 200), (300, 280), (340, 240)]


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_fill()

    # a Bezier segment and its two control points
    p.stroke("gray70")
    p.line(40, 150, 60, 30)
    p.line(260, 30, 280, 150)
    p.stroke("navy")
    p.stroke_width(4)
    p.begin_shape()
    p.vertex(40, 150)
    p.bezier_vertex(60, 30, 260, 30, 280, 150)
    p.quadratic_vertex(320, 30, 360, 150)       # one control point
    p.end_shape()

    # smooth curves through points, loose and tight
    for tightness, colour in ((0, "tomato"), (0.8, "seagreen")):
        p.curve_tightness(tightness)
        p.stroke(colour)
        p.begin_shape()
        for x, y in points:
            p.curve_vertex(x, y)
        p.end_shape()
    p.no_stroke()
    p.fill("black")
    for x, y in points:
        p.circle(x, y, 8)

    # one-call curves, with direction marks placed by the point and tangent helpers
    p.no_fill()
    p.stroke("orchid")
    p.bezier(400, 330, 420, 180, 600, 380, 600, 220)
    p.curve(0, 400, 420, 60, 600, 120, 300, 400)
    p.stroke("purple")
    p.stroke_width(3)
    for i in range(7):
        t = i / 6
        x, y = p.bezier_point(400, 420, 600, 600, t), p.bezier_point(330, 180, 380, 220, t)
        angle = math.atan2(p.bezier_tangent(330, 180, 380, 220, t), p.bezier_tangent(400, 420, 600, 600, t))
        with p.saved_state():
            p.translate(x, y)
            p.rotate(p.degrees(angle))
            p.line(-8, -8, 0, 0)          # a small arrowhead pointing along the curve
            p.line(-8, 8, 0, 0)
        x, y = p.curve_point(0, 420, 600, 300, t), p.curve_point(400, 60, 120, 400, t)
        angle = math.atan2(p.curve_tangent(400, 60, 120, 400, t), p.curve_tangent(0, 420, 600, 300, t))
        with p.saved_state():
            p.translate(x, y)
            p.rotate(p.degrees(angle))
            p.line(-8, -8, 0, 0)
            p.line(-8, 8, 0, 0)


p.run()
