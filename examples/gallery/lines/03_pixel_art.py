"""Pixel art with no_smooth

no_smooth() turns off the soft edges, so every pixel is either the shape's colour or not. Draw
big and blocky with scale() and it looks like a retro game. smooth() switches back: compare the
two white circles.
"""
import funground as f

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
    f.size(640, 400)
    f.no_smooth()


def draw():
    f.background("black")
    f.no_stroke()
    f.fill("lime")
    with f.saved_state():
        f.translate(100, 80)
        f.scale(30)
        for row, line in enumerate(INVADER):
            for col, ch in enumerate(line):
                if ch == "X":
                    f.rect(col, row, 1, 1)
    f.fill("white")
    f.circle(520, 330, 41)            # a jagged circle: no anti-aliasing
    f.smooth()                        # smooth edges again for the rest of this frame
    f.circle(590, 330, 41)


f.run()
