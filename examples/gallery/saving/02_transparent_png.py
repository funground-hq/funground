"""A picture with a transparent background

clear() makes every pixel transparent. A PNG saved afterwards keeps the transparency, so the
shape can be placed on any background later. (The window shows transparent as black.)
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.clear()
    f.fill("tomato")
    f.stroke("black")
    f.stroke_width(6)
    f.circle(320, 200, 260)
    if f.frame_count == 0:
        f.save("sticker.png")


f.run()
