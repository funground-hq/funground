"""Combining shapes

Two shapes can be joined, overlapped, cut and mixed with union, intersection, difference and xor.
Each one gives back a new path. The bottom panel shows remove_overlap, which turns a crossing
outline into one clean edge.
"""
import math

import funground as f


def star_points(cx, cy, r):
    """Every second corner of a pentagon, so the outline crosses itself."""
    return [(cx + r * math.cos(math.radians(-90 + i * 144)), cy + r * math.sin(math.radians(-90 + i * 144)))
            for i in range(5)]


def two_shapes(cx, cy):
    ring = f.path().circle(cx - 12, cy, 60)
    star = f.path().polygon(star_points(cx + 14, cy + 4, 44))
    return ring, star


def panel(x, label):
    f.fill(245)
    f.no_stroke()
    f.rect(x, 20, 140, 150)
    f.fill(60)
    f.text(label, x + 70, 156)


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.text_size(15)
    f.text_align("center", "center")

    names = ["union", "intersection", "difference", "xor"]
    for i, name in enumerate(names):
        x = 25 + i * 150
        ring, star = two_shapes(x + 70, 88)
        result = {"union": ring | star, "intersection": ring & star,
                  "difference": ring - star, "xor": ring ^ star}[name]
        panel(x, name)
        f.fill("tomato")
        f.stroke("darkred")
        f.stroke_width(2)
        f.draw_path(result)

    # remove_overlap: the same self-crossing star, before and after
    star = f.path().polygon(star_points(150, 290, 70))
    clean = star.remove_overlap()
    f.fill(245)
    f.no_stroke()
    f.rect(25, 190, 590, 195)
    f.no_fill()
    f.stroke("navy")
    f.stroke_width(3)
    f.draw_path(star)
    f.push()
    f.translate(320, 0)
    f.draw_path(clean)
    f.pop()
    f.fill(60)
    f.no_stroke()
    f.text("a star that crosses itself", 150, 372)
    f.text("remove_overlap: one clean outline", 470, 372)


f.run()
