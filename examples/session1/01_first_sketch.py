import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("tomato")
    f.circle(320, 200, 80)


f.run()
