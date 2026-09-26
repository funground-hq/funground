import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background((245, 245, 240))
    f.fill("tomato")
    f.stroke("navy")
    f.circle(100, 100, 80)

    f.fill((0, 180, 100))
    f.rect(200, 60, 120, 80)

    f.fill("#F05A45")
    f.stroke("#203040")
    f.ellipse(450, 100, 140, 80)

    f.fill("gray25")
    f.circle(100, 280, 60)
    f.fill("tomato3")
    f.circle(250, 280, 60)
    f.fill("darkslategrey")
    f.circle(400, 280, 60)
    f.fill("aqua")
    f.circle(550, 280, 60)


f.run()
