import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("tomato")
    p.circle(320, 200, 80)


p.run()
