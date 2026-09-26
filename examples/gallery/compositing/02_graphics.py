"""Off-screen graphics: a trail

f.create_graphics() makes a picture: an off-screen canvas with the same drawing commands as
the window. Painting a translucent rectangle over it every frame, instead of clearing it, makes
older drawing fade instead of vanish - a comet trail, the same trick Processing's PGraphics is
used for. f.image() then places the picture wherever you like, at any size.
"""
import math

import funground as f

trail = None


def setup():
    global trail
    f.size(640, 400)
    trail = f.create_graphics(400, 400)


def draw():
    f.background("black")

    trail.no_stroke()
    trail.fill((0, 0, 0, 24))          # translucent: painted over the old trail, it fades
    trail.rect(0, 0, trail.width, trail.height)

    angle = f.radians(f.frame_count * 6)
    x = trail.width / 2 + math.cos(angle) * 150
    y = trail.height / 2 + math.sin(angle) * 150
    trail.fill("gold")
    trail.circle(x, y, 24)

    f.image(trail, 0, 0)                    # full size
    f.image(trail, 480, 20, 140, 140)       # a second, smaller copy: image() can scale


f.run()
