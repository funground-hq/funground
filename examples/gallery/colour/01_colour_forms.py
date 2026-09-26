"""Four ways to say a colour

A name, an (r, g, b) tuple from 0 to 255, a hex string, or an (r, g, b, a) tuple whose last
number is the opacity. Overlapping translucent circles mix.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.no_stroke()
    f.fill("tomato")                 # a name
    f.rect(40, 40, 120, 120)
    f.fill((0, 180, 100))            # red, green, blue
    f.rect(190, 40, 120, 120)
    f.fill("#6A5ACD")                # hex
    f.rect(340, 40, 120, 120)
    f.fill("gray50")
    f.rect(490, 40, 120, 120)

    f.fill((255, 0, 0, 120))         # red, green, blue, opacity
    f.circle(260, 305, 150)
    f.fill((0, 0, 255, 120))
    f.circle(360, 305, 150)
    f.fill((0, 200, 0, 120))
    f.circle(310, 245, 150)


f.run()
