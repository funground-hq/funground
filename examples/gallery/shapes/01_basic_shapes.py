"""The basic shapes

rect is placed by its top-left corner; circle and ellipse by their centre. line joins two
points; point is a dot in the stroke colour.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("skyblue")
    p.rect(40, 60, 160, 100)            # top-left x, y, width, height
    p.fill("tomato")
    p.circle(320, 110, 100)             # centre x, y, diameter
    p.fill("gold")
    p.ellipse(520, 110, 160, 80)        # centre x, y, width, height
    p.stroke("navy")
    p.stroke_width(4)
    p.line(40, 260, 600, 340)           # from (x1, y1) to (x2, y2)
    p.stroke_width(12)
    for x in range(60, 600, 60):
        p.point(x, 230)


p.run()
