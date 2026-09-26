import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background((245, 245, 240))    # an RGB tuple, each value 0-255

    f.fill("tomato")                 # a named colour (see the appendix)
    f.stroke("navy")
    f.circle(100, 100, 80)

    f.fill((0, 180, 100))            # RGB
    f.rect(200, 60, 120, 80)

    f.fill("#F05A45")                # hex string
    f.stroke("#203040")
    f.ellipse(450, 100, 140, 80)

    # Alpha is honoured (v0.6): a fourth value 0-255, or "#RRGGBBAA".
    f.no_stroke()
    f.fill((0, 0, 255, 90))
    f.circle(140, 290, 130)
    f.fill("#FF000060")
    f.circle(230, 290, 130)
    f.fill((255, 200, 0, 120))
    f.circle(185, 220, 130)

    # Every pygame-ce colour name works, on every platform (capitals and spaces are ignored).
    for i, name in enumerate(["gray25", "tomato3", "darkslategrey", "aqua"]):
        f.fill(name)
        f.circle(390 + i * 70, 290, 50)


f.run()
