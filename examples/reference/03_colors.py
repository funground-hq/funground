import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background((245, 245, 240))    # an RGB tuple, each value 0-255

    p.fill("tomato")                 # a named colour (see the appendix)
    p.stroke("navy")
    p.circle(100, 100, 80)

    p.fill((0, 180, 100))            # RGB
    p.rect(200, 60, 120, 80)

    p.fill("#F05A45")                # hex string
    p.stroke("#203040")
    p.ellipse(450, 100, 140, 80)

    # Alpha is honoured (v0.6): a fourth value 0-255, or "#RRGGBBAA".
    p.no_stroke()
    p.fill((0, 0, 255, 90))
    p.circle(140, 290, 130)
    p.fill("#FF000060")
    p.circle(230, 290, 130)
    p.fill((255, 200, 0, 120))
    p.circle(185, 220, 130)

    # Every pygame-ce colour name works, on every platform, spelt in lowercase.
    for i, name in enumerate(["gray25", "tomato3", "darkslategrey", "aqua"]):
        p.fill(name)
        p.circle(390 + i * 70, 290, 50)


p.run()
