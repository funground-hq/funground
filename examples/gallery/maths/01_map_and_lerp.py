"""Mapping and blending numbers

map_range re-scales a number from one range to another; lerp finds a point part of the way
between two numbers; norm says how far along a range a number is; mag measures an arrow.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    for i in range(12):
        x = p.map_range(i, 0, 11, 40, 600)                 # 0..11 spread across the window
        shade = p.map_range(i, 0, 11, 230, 30)             # and from light to dark
        p.fill((shade, shade, 255))
        p.circle(x, 80, 40)

    start, end = (60, 300), (580, 180)
    p.stroke("gray70")
    p.line(*start, *end)                                   # the arrow mag() measures
    p.no_stroke()
    for i in range(9):
        t = i / 8
        x, y = p.lerp(start[0], end[0], t), p.lerp(start[1], end[1], t)
        p.fill("tomato" if p.norm(x, start[0], end[0]) < 0.5 else "seagreen")
        p.circle(x, y, 24)
    p.fill("black")
    p.text(f"that arrow is {p.mag(end[0] - start[0], end[1] - start[1]):.0f} pixels long", 60, 340)


p.run()
