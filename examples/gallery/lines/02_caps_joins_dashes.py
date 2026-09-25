"""Line ends, corners and dashes

stroke_cap sets how a line ends, stroke_join how corners look, and stroke_dash draws dashed
outlines. They are style, like fill: saved_state puts them back.
"""
import playground as p


def setup():
    p.size(640, 400)


def zigzag(x, y):
    p.begin_shape()
    p.vertex(x, y + 60)
    p.vertex(x + 40, y)
    p.vertex(x + 80, y + 60)
    p.end_shape()


def draw():
    p.background("white")
    p.fill("navy")                    # label colour (text uses the fill)
    p.stroke("navy")
    p.stroke_width(18)
    for i, cap in enumerate(["butt", "square", "round"]):
        with p.saved_state():
            p.stroke_cap(cap)
            p.line(60, 50 + i * 45, 260, 50 + i * 45)
        p.text(cap, 290, 40 + i * 45)

    p.no_fill()
    p.miter_limit(4)                  # sharp corners may stick out up to 4 x the stroke width
    for i, join in enumerate(["miter", "bevel", "round"]):
        with p.saved_state():
            p.stroke_join(join)
            zigzag(380 + i * 90, 50)
        p.text(join, 395 + i * 90, 130)

    p.stroke_width(4)
    with p.saved_state():
        p.stroke_dash([16, 8])
        p.rect(60, 220, 240, 130)
    p.stroke_dash([2, 10])
    p.stroke("tomato")
    p.circle(470, 285, 140)
    p.no_dash()                       # solid again
    p.line(380, 370, 560, 370)


p.run()
