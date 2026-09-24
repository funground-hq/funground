import playground as p

x = 50


def setup():
    p.size(640, 400)


def draw():
    global x

    p.background("white")
    p.fill("tomato")
    p.circle(x, p.height / 2, 40)

    x += 2


p.run()
