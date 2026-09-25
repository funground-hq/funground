"""Pixel art with no_smooth

no_smooth() turns off the soft edges, so every pixel is either the shape's colour or not. Draw
big and blocky with scale() and it looks like a retro game. smooth() switches back: compare the
two white circles.
"""
import playground as p

INVADER = [
    "..X.....X..",
    "...X...X...",
    "..XXXXXXX..",
    ".XX.XXX.XX.",
    "XXXXXXXXXXX",
    "X.XXXXXXX.X",
    "X.X.....X.X",
    "...XX.XX...",
]


def setup():
    p.size(640, 400)
    p.no_smooth()


def draw():
    p.background("black")
    p.no_stroke()
    p.fill("lime")
    with p.saved_state():
        p.translate(100, 80)
        p.scale(30)
        for row, line in enumerate(INVADER):
            for col, ch in enumerate(line):
                if ch == "X":
                    p.rect(col, row, 1, 1)
    p.fill("white")
    p.circle(520, 330, 41)            # a jagged circle: no anti-aliasing
    p.smooth()                        # smooth edges again for the rest of this frame
    p.circle(590, 330, 41)


p.run()
