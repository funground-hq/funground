import playground as p

x = 50
speed = 3


def setup():
    p.size(640, 400)


def draw():
    global x, speed

    p.background("white")
    p.circle(x, p.height / 2, 40)

    x += speed
    if x > p.width - 20 or x < 20:
        speed = -speed


p.run()
