import playground as p

x = 320


def setup():
    p.size(640, 400)


def draw():
    global x

    p.background("white")

    if p.key_down("left"):
        x -= 3
    if p.key_down("right"):
        x += 3
    if p.key_down("space"):
        p.fill("gold")
    else:
        p.fill("tomato")

    p.circle(x, 200, 60)


p.run()
