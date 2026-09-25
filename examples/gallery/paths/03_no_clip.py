"""Clipping on and off

no_clip() removes clipping until the end of the saved_state block; when the block ends, the
clip that was there before comes back.
"""
import playground as p

porthole = p.path().move_to(200, 60).line_to(440, 60).line_to(440, 340).line_to(200, 340).close()


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    with p.saved_state():
        p.clip(porthole)
        for i in range(16):                       # stripes: only visible inside the porthole
            p.fill("navy" if i % 2 else "skyblue")
            p.rect(i * 40, 0, 40, 400)
        with p.saved_state():
            p.no_clip()                           # this circle ignores the clip
            p.fill((255, 99, 71, 200))
            p.circle(160, 200, 160)
        p.fill("gold")                            # clipped again
        p.circle(470, 200, 160)


p.run()
