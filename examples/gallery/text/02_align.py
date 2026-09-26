"""Aligning text

f.text_align() says which point of the text the (x, y) you give is: left, center or right,
then top, center, baseline or bottom. Each red cross below is the (x, y) passed to f.text().
text_ascent() and text_descent() measure how far letters reach above and below the baseline.
"""
import funground as f


def cross(x, y):
    f.stroke("red")
    f.stroke_width(1)
    f.line(x - 6, y, x + 6, y)
    f.line(x, y - 6, x, y + 6)


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("black")
    f.no_stroke()
    f.text_size(20)
    for row, vertical in enumerate(["top", "center", "baseline", "bottom"]):
        y = 50 + row * 80
        for column, horizontal in enumerate(["left", "center", "right"]):
            x = 70 + column * 250
            f.text_align(horizontal, vertical)
            f.fill("black")
            f.text(f"{horizontal} {vertical}", x, y)
            cross(x, y)
            f.no_stroke()

    # the measurements behind the alignment
    f.text_align("left", "baseline")
    f.text_size(14)
    f.fill("gray")
    f.text(f"ascent {f.text_ascent():.1f} px, descent {f.text_descent():.1f} px at size 14", 10, 390)


f.run()
