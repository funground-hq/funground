import funground as f

x = 50


def setup():
    f.size(640, 400)


def draw():
    global x

    f.background("white")
    f.fill("tomato")
    f.circle(x, f.height / 2, 40)

    x += 2


f.run()
