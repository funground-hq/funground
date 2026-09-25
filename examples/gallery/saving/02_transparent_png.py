"""A picture with a transparent background

clear() makes every pixel transparent. A PNG saved afterwards keeps the transparency, so the
shape can be placed on any background later. (The window shows transparent as black.)
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.clear()
    p.fill("tomato")
    p.stroke("black")
    p.stroke_width(6)
    p.circle(320, 200, 260)
    if p.frame_count == 0:
        p.save("sticker.png")


p.run()
