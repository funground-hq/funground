import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    if p.is_mouse_pressed:
        p.fill("tomato")
    else:
        p.fill("skyblue")
    p.circle(p.mouse_x, p.mouse_y, 40)

    if p.mouse_x < p.width / 2:
        p.fill("tomato")
    else:
        p.fill("skyblue")
    p.rect(p.width / 2 - 20, p.height - 60, 40, 40)


p.run()
