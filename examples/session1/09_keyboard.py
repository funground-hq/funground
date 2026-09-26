import funground as f

x = 320


def setup():
    f.size(640, 400)


def draw():
    global x

    f.background("white")

    if f.key_down("left"):
        x -= 3
    if f.key_down("right"):
        x += 3
    if f.key_down("space"):
        f.fill("gold")
    else:
        f.fill("tomato")

    f.circle(x, 200, 60)


f.run()
