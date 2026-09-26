import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    # A star: list the corners between begin_shape() and end_shape(close=True).
    # The pentagram crosses itself, and its centre is filled too (non-zero rule).
    f.fill("gold")
    f.stroke("darkorange")
    f.stroke_width(3)
    f.begin_shape()
    for i in range(5):
        angle = f.radians(-90 + i * 144)        # every second corner of a pentagon
        f.vertex(120 + 80 * math.cos(angle), 120 + 80 * math.sin(angle))
    f.end_shape(close=True)

    # An open shape is stroked but never filled: a wave from two bezier_vertex() calls.
    # Each bezier_vertex takes two control points, then the point the curve ends at.
    f.no_fill()
    f.stroke("steelblue")
    f.stroke_width(4)
    f.begin_shape()
    f.vertex(260, 120)
    f.bezier_vertex(320, 20, 380, 220, 440, 120)
    f.bezier_vertex(500, 20, 560, 220, 620, 120)
    f.end_shape()

    # A reusable path: build a leaf once, then draw it wherever the origin is.
    leaf = f.path().move_to(0, 0).curve_to(30, -40, 70, -40, 90, 0).curve_to(70, 40, 30, 40, 0, 0).close()
    f.fill("yellowgreen")
    f.stroke("darkgreen")
    f.stroke_width(2)
    for i in range(4):
        with f.saved_state():
            f.translate(40 + i * 110, 270)
            f.rotate(-20 + i * 15)
            f.draw_path(leaf)

    # Clipping: inside a saved_state() block, clip() limits everything drawn until the block ends.
    window = f.path().move_to(560, 200).line_to(630, 270).line_to(560, 340).line_to(490, 270).close()
    with f.saved_state():
        f.clip(window)
        f.no_stroke()
        for i in range(12):
            f.fill("tomato" if i % 2 == 0 else "navy")
            f.rect(480, 200 + i * 12, 160, 12)  # stripes wider than the window are cropped
    f.no_fill()
    f.stroke("black")
    f.stroke_width(1)
    f.draw_path(window)                          # the outline, drawn after the clip is lifted

    f.text("paths", 20, 350, "black")


f.run()
