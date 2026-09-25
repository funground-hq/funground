"""Reusable paths and clipping

p.path() builds a shape you can draw many times with draw_path(). clip(path) keeps later
drawing inside the path until the end of the saved_state block.
"""
import playground as p

leaf = p.path().move_to(0, -40).line_to(24, 0).line_to(0, 40).line_to(-24, 0).close()


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("seagreen")
    p.stroke("darkgreen")
    for i in range(6):
        with p.saved_state():
            p.translate(60 + i * 50, 120)
            p.rotate(i * 15)
            p.draw_path(leaf)

    window = p.path().move_to(420, 60).line_to(600, 60).line_to(600, 340).line_to(420, 340).close()
    with p.saved_state():
        p.clip(window)
        p.no_stroke()
        for i in range(12):
            p.fill("tomato" if i % 2 else "gold")
            p.circle(420 + i * 20, 200, 90)
    p.no_fill()
    p.stroke("black")
    p.draw_path(window)


p.run()
