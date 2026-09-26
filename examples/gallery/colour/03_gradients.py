"""Gradients

p.linear_gradient() blends colours along a line; p.radial_gradient() blends them outward
from a centre. Either can be used wherever a colour goes - fill, stroke or background - and
it follows p.translate() and p.rotate() like any shape. Saved as PDF or SVG, it stays smooth.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    sky = p.linear_gradient(0, 0, 0, 400, ["midnightblue", "darkorchid", "coral"])
    p.background(sky)

    sun = p.radial_gradient(320, 300, 110, ["lightyellow", "gold", (255, 140, 0, 0)], stops=[0, 0.5, 1])
    p.no_stroke()
    p.fill(sun)
    p.circle(320, 300, 220)

    hills = p.linear_gradient(0, 300, 0, 400, ["darkgreen", "black"])
    p.fill(hills)
    p.rect(0, 320, 640, 80)

    p.stroke(p.linear_gradient(40, 0, 600, 0, ["white", (255, 255, 255, 0)]))
    p.stroke_width(3)
    p.line(40, 60, 600, 60)

    with p.saved_state():                          # a gradient turns with the shape
        p.translate(540, 150)
        p.rotate(30)
        p.no_stroke()
        p.fill(p.linear_gradient(-40, 0, 40, 0, ["hotpink", "cyan"]))
        p.rect(-40, -20, 80, 40)


p.run()
