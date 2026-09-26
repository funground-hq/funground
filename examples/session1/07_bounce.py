import funground as f

x = 50
speed = 3


def setup():
    f.size(640, 400)


def draw():
    global x, speed

    f.background("white")
    f.circle(x, f.height / 2, 40)

    x += speed
    if x > f.width - 20 or x < 20:
        speed = -speed


f.run()
