"""Four ways to say a colour

A name, an (r, g, b) tuple from 0 to 255, a hex string, or an (r, g, b, a) tuple whose last
number is the opacity. Overlapping translucent circles mix.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.no_stroke()
    p.fill("tomato")                 # a name
    p.rect(40, 40, 120, 120)
    p.fill((0, 180, 100))            # red, green, blue
    p.rect(190, 40, 120, 120)
    p.fill("#6A5ACD")                # hex
    p.rect(340, 40, 120, 120)
    p.fill("gray50")
    p.rect(490, 40, 120, 120)

    p.fill((255, 0, 0, 120))         # red, green, blue, opacity
    p.circle(260, 305, 150)
    p.fill((0, 0, 255, 120))
    p.circle(360, 305, 150)
    p.fill((0, 200, 0, 120))
    p.circle(310, 245, 150)


p.run()
