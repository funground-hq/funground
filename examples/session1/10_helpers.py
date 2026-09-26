import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    for _ in range(20):
        x = f.random(f.width)
        y = f.random(f.height)
        x = f.constrain(x, 20, f.width - 20)
        y = f.constrain(y, 20, f.height - 20)
        d = f.distance(x, y, f.width / 2, f.height / 2)
        if d < 150:
            f.fill("tomato")
        else:
            f.fill("skyblue")
        f.circle(x, y, 20)


f.run()
