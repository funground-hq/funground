"""Gradients

f.linear_gradient() blends colours along a line; f.radial_gradient() blends them outward
from a centre. Either can be used wherever a colour goes - fill, stroke or background - and
it follows f.translate() and f.rotate() like any shape. Saved as PDF or SVG, it stays smooth.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    sky = f.linear_gradient(0, 0, 0, 400, ["midnightblue", "darkorchid", "coral"])
    f.background(sky)

    sun = f.radial_gradient(320, 300, 110, ["lightyellow", "gold", (255, 140, 0, 0)], stops=[0, 0.5, 1])
    f.no_stroke()
    f.fill(sun)
    f.circle(320, 300, 220)

    hills = f.linear_gradient(0, 300, 0, 400, ["darkgreen", "black"])
    f.fill(hills)
    f.rect(0, 320, 640, 80)

    f.stroke(f.linear_gradient(40, 0, 600, 0, ["white", (255, 255, 255, 0)]))
    f.stroke_width(3)
    f.line(40, 60, 600, 60)

    with f.saved_state():                          # a gradient turns with the shape
        f.translate(540, 150)
        f.rotate(30)
        f.no_stroke()
        f.fill(f.linear_gradient(-40, 0, 40, 0, ["hotpink", "cyan"]))
        f.rect(-40, -20, 80, 40)


f.run()
