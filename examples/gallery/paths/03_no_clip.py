"""Clipping on and off

no_clip() removes clipping until the end of the saved_state block; when the block ends, the
clip that was there before comes back.
"""
import funground as f

porthole = f.path().move_to(200, 60).line_to(440, 60).line_to(440, 340).line_to(200, 340).close()


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    with f.saved_state():
        f.clip(porthole)
        for i in range(16):                       # stripes: only visible inside the porthole
            f.fill("navy" if i % 2 else "skyblue")
            f.rect(i * 40, 0, 40, 400)
        with f.saved_state():
            f.no_clip()                           # this circle ignores the clip
            f.fill((255, 99, 71, 200))
            f.circle(160, 200, 160)
        f.fill("gold")                            # clipped again
        f.circle(470, 200, 160)


f.run()
