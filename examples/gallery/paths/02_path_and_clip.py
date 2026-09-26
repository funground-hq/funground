"""Reusable paths and clipping

f.path() builds a shape you can draw many times with draw_path(). clip(path) keeps later
drawing inside the path until the end of the saved_state block.
"""
import funground as f

leaf = f.path().move_to(0, -40).line_to(24, 0).line_to(0, 40).line_to(-24, 0).close()


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("seagreen")
    f.stroke("darkgreen")
    for i in range(6):
        with f.saved_state():
            f.translate(60 + i * 50, 120)
            f.rotate(i * 15)
            f.draw_path(leaf)

    window = f.path().move_to(420, 60).line_to(600, 60).line_to(600, 340).line_to(420, 340).close()
    with f.saved_state():
        f.clip(window)
        f.no_stroke()
        for i in range(12):
            f.fill("tomato" if i % 2 else "gold")
            f.circle(420 + i * 20, 200, 90)
    f.no_fill()
    f.stroke("black")
    f.draw_path(window)


f.run()
