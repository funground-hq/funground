import math

import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    # A shape from its corners: begin_shape(), a vertex() per corner, end_shape().
    # close=True joins the last corner to the first and fills the shape.
    f.fill("gold")
    f.stroke("darkorange")
    f.stroke_width(3)
    f.begin_shape()
    for i in range(5):
        a = f.radians(-90 + i * 144)           # a pentagram: every second corner
        f.vertex(110 + 80 * math.cos(a), 110 + 80 * math.sin(a))
    f.end_shape(close=True)                    # it crosses itself and is filled right through

    # An open shape is stroked, never filled. bezier_vertex() takes two control
    # points, then the point the curve ends at.
    f.no_fill()
    f.stroke("steelblue")
    f.stroke_width(4)
    f.begin_shape()
    f.vertex(240, 110)
    f.bezier_vertex(300, 10, 360, 210, 420, 110)
    f.bezier_vertex(480, 10, 540, 210, 600, 110)
    f.end_shape()

    # f.path() builds a reusable path: move_to, line_to, curve_to, quad_to, close.
    leaf = f.path().move_to(0, 0).curve_to(30, -40, 70, -40, 90, 0).curve_to(70, 40, 30, 40, 0, 0).close()
    f.fill("yellowgreen")
    f.stroke("darkgreen")
    f.stroke_width(2)
    for i in range(4):
        with f.saved_state():
            f.translate(30 + i * 100, 280)
            f.rotate(-30 + i * 20)
            f.draw_path(leaf)                  # filled (it is closed) then stroked

    # clip(path) limits later drawing to the inside of the path until the
    # enclosing pop() / the end of the with f.saved_state() block.
    window = f.path().move_to(540, 200).line_to(620, 280).line_to(540, 360).line_to(460, 280).close()
    with f.saved_state():
        f.clip(window)
        f.no_stroke()
        for i in range(14):
            f.fill("tomato" if i % 2 == 0 else "navy")
            f.rect(450, 200 + i * 12, 180, 12)  # wider than the window: cropped
    f.no_fill()
    f.stroke("black")
    f.stroke_width(1)
    f.draw_path(window)                        # the outline, once the clip is lifted


f.run()
