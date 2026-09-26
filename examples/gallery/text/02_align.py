"""Aligning text

p.text_align() says which point of the text the (x, y) you give is: left, center or right,
then top, center, baseline or bottom. Each red cross below is the (x, y) passed to p.text().
text_ascent() and text_descent() measure how far letters reach above and below the baseline.
"""
import playground as p


def cross(x, y):
    p.stroke("red")
    p.stroke_width(1)
    p.line(x - 6, y, x + 6, y)
    p.line(x, y - 6, x, y + 6)


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("black")
    p.no_stroke()
    p.text_size(20)
    for row, vertical in enumerate(["top", "center", "baseline", "bottom"]):
        y = 50 + row * 80
        for column, horizontal in enumerate(["left", "center", "right"]):
            x = 70 + column * 250
            p.text_align(horizontal, vertical)
            p.fill("black")
            p.text(f"{horizontal} {vertical}", x, y)
            cross(x, y)
            p.no_stroke()

    # the measurements behind the alignment
    p.text_align("left", "baseline")
    p.text_size(14)
    p.fill("gray")
    p.text(f"ascent {p.text_ascent():.1f} px, descent {p.text_descent():.1f} px at size 14", 10, 390)


p.run()
