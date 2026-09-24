import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    for _ in range(20):
        x = p.random(p.width)
        y = p.random(p.height)
        x = p.constrain(x, 20, p.width - 20)
        y = p.constrain(y, 20, p.height - 20)
        d = p.distance(x, y, p.width / 2, p.height / 2)
        if d < 150:
            p.fill("tomato")
        else:
            p.fill("skyblue")
        p.circle(x, y, 20)


p.run()
