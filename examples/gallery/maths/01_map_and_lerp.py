"""Mapping and blending numbers

map_range re-scales a number from one range to another; lerp finds a point part of the way
between two numbers; norm says how far along a range a number is; mag measures an arrow.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    for i in range(12):
        x = f.map_range(i, 0, 11, 40, 600)                 # 0..11 spread across the window
        shade = f.map_range(i, 0, 11, 230, 30)             # and from light to dark
        f.fill((shade, shade, 255))
        f.circle(x, 80, 40)

    start, end = (60, 300), (580, 180)
    f.stroke("gray70")
    f.line(*start, *end)                                   # the arrow mag() measures
    f.no_stroke()
    for i in range(9):
        t = i / 8
        x, y = f.lerp(start[0], end[0], t), f.lerp(start[1], end[1], t)
        f.fill("tomato" if f.norm(x, start[0], end[0]) < 0.5 else "seagreen")
        f.circle(x, y, 24)
    f.fill("black")
    f.text(f"that arrow is {f.mag(end[0] - start[0], end[1] - start[1]):.0f} pixels long", 60, 340)


f.run()
