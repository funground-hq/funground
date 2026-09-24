import playground as p

x = 0


def setup():
    p.size(640, 400)


def draw():
    global x

    p.background("white")
    p.circle(x, 200, 40)

    # move at about 120 pixels per second
    x += 120 * p.delta_time
    if x > p.width:
        x = 0


p.run()
