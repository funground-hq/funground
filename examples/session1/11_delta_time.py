import funground as f

x = 0


def setup():
    f.size(640, 400)


def draw():
    global x

    f.background("white")
    f.circle(x, 200, 40)

    # move at about 120 pixels per second
    x += 120 * f.delta_time
    if x > f.width:
        x = 0


f.run()
