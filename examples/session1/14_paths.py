import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    # A star: list the corners between begin_shape() and end_shape(close=True).
    # The pentagram crosses itself, and its centre is filled too (non-zero rule).
    p.fill("gold")
    p.stroke("darkorange")
    p.stroke_width(3)
    p.begin_shape()
    for i in range(5):
        angle = p.radians(-90 + i * 144)        # every second corner of a pentagon
        p.vertex(120 + 80 * math.cos(angle), 120 + 80 * math.sin(angle))
    p.end_shape(close=True)

    # An open shape is stroked but never filled: a wave from two curve_vertex() calls.
    # Each curve_vertex takes two control points, then the point the curve ends at.
    p.no_fill()
    p.stroke("steelblue")
    p.stroke_width(4)
    p.begin_shape()
    p.vertex(260, 120)
    p.curve_vertex(320, 20, 380, 220, 440, 120)
    p.curve_vertex(500, 20, 560, 220, 620, 120)
    p.end_shape()

    # A reusable path: build a leaf once, then draw it wherever the origin is.
    leaf = p.path().move_to(0, 0).curve_to(30, -40, 70, -40, 90, 0).curve_to(70, 40, 30, 40, 0, 0).close()
    p.fill("yellowgreen")
    p.stroke("darkgreen")
    p.stroke_width(2)
    for i in range(4):
        with p.saved_state():
            p.translate(40 + i * 110, 270)
            p.rotate(-20 + i * 15)
            p.draw_path(leaf)

    # Clipping: inside a saved_state() block, clip() limits everything drawn until the block ends.
    window = p.path().move_to(560, 200).line_to(630, 270).line_to(560, 340).line_to(490, 270).close()
    with p.saved_state():
        p.clip(window)
        p.no_stroke()
        for i in range(12):
            p.fill("tomato" if i % 2 == 0 else "navy")
            p.rect(480, 200 + i * 12, 160, 12)  # stripes wider than the window are cropped
    p.no_fill()
    p.stroke("black")
    p.stroke_width(1)
    p.draw_path(window)                          # the outline, drawn after the clip is lifted

    p.text("paths", 20, 350, "black")


p.run()
