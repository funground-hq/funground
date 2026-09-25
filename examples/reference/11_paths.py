import math

import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    # A shape from its corners: begin_shape(), a vertex() per corner, end_shape().
    # close=True joins the last corner to the first and fills the shape.
    p.fill("gold")
    p.stroke("darkorange")
    p.stroke_width(3)
    p.begin_shape()
    for i in range(5):
        a = p.radians(-90 + i * 144)           # a pentagram: every second corner
        p.vertex(110 + 80 * math.cos(a), 110 + 80 * math.sin(a))
    p.end_shape(close=True)                    # it crosses itself and is filled right through

    # An open shape is stroked, never filled. bezier_vertex() takes two control
    # points, then the point the curve ends at.
    p.no_fill()
    p.stroke("steelblue")
    p.stroke_width(4)
    p.begin_shape()
    p.vertex(240, 110)
    p.bezier_vertex(300, 10, 360, 210, 420, 110)
    p.bezier_vertex(480, 10, 540, 210, 600, 110)
    p.end_shape()

    # p.path() builds a reusable path: move_to, line_to, curve_to, quad_to, close.
    leaf = p.path().move_to(0, 0).curve_to(30, -40, 70, -40, 90, 0).curve_to(70, 40, 30, 40, 0, 0).close()
    p.fill("yellowgreen")
    p.stroke("darkgreen")
    p.stroke_width(2)
    for i in range(4):
        with p.saved_state():
            p.translate(30 + i * 100, 280)
            p.rotate(-30 + i * 20)
            p.draw_path(leaf)                  # filled (it is closed) then stroked

    # clip(path) limits later drawing to the inside of the path until the
    # enclosing pop() / the end of the with p.saved_state() block.
    window = p.path().move_to(540, 200).line_to(620, 280).line_to(540, 360).line_to(460, 280).close()
    with p.saved_state():
        p.clip(window)
        p.no_stroke()
        for i in range(14):
            p.fill("tomato" if i % 2 == 0 else "navy")
            p.rect(450, 200 + i * 12, 180, 12)  # wider than the window: cropped
    p.no_fill()
    p.stroke("black")
    p.stroke_width(1)
    p.draw_path(window)                        # the outline, once the clip is lifted


p.run()
