"""The basic shapes

rect is placed by its top-left corner; circle and ellipse by their centre. line joins two
points; point is a dot in the stroke colour.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("skyblue")
    f.rect(40, 60, 160, 100)            # top-left x, y, width, height
    f.fill("tomato")
    f.circle(320, 110, 100)             # centre x, y, diameter
    f.fill("gold")
    f.ellipse(520, 110, 160, 80)        # centre x, y, width, height
    f.stroke("navy")
    f.stroke_width(4)
    f.line(40, 260, 600, 340)           # from (x1, y1) to (x2, y2)
    f.stroke_width(12)
    for x in range(60, 600, 60):
        f.point(x, 230)


f.run()
