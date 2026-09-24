import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background((245, 245, 240))
    p.fill("tomato")
    p.stroke("navy")
    p.circle(100, 100, 80)

    p.fill((0, 180, 100))
    p.rect(200, 60, 120, 80)

    p.fill("#F05A45")
    p.stroke("#203040")
    p.ellipse(450, 100, 140, 80)

    p.fill("gray25")
    p.circle(100, 280, 60)
    p.fill("tomato3")
    p.circle(250, 280, 60)
    p.fill("darkslategrey")
    p.circle(400, 280, 60)
    p.fill("aqua")
    p.circle(550, 280, 60)


p.run()
