"""Line ends, corners and dashes

stroke_cap sets how a line ends, stroke_join how corners look, and stroke_dash draws dashed
outlines. They are style, like fill: saved_state puts them back.
"""
import funground as f


def setup():
    f.size(640, 400)


def zigzag(x, y):
    f.begin_shape()
    f.vertex(x, y + 60)
    f.vertex(x + 40, y)
    f.vertex(x + 80, y + 60)
    f.end_shape()


def draw():
    f.background("white")
    f.fill("navy")                    # label colour (text uses the fill)
    f.stroke("navy")
    f.stroke_width(18)
    for i, cap in enumerate(["butt", "square", "round"]):
        with f.saved_state():
            f.stroke_cap(cap)
            f.line(60, 50 + i * 45, 260, 50 + i * 45)
        f.text(cap, 290, 40 + i * 45)

    f.no_fill()
    f.miter_limit(4)                  # sharp corners may stick out up to 4 x the stroke width
    for i, join in enumerate(["miter", "bevel", "round"]):
        with f.saved_state():
            f.stroke_join(join)
            zigzag(380 + i * 90, 50)
        f.text(join, 395 + i * 90, 130)

    f.stroke_width(4)
    with f.saved_state():
        f.stroke_dash([16, 8])
        f.rect(60, 220, 240, 130)
    f.stroke_dash([2, 10])
    f.stroke("tomato")
    f.circle(470, 285, 140)
    f.no_dash()                       # solid again
    f.line(380, 370, 560, 370)


f.run()
