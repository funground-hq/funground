import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    if f.is_mouse_pressed:
        f.fill("tomato")
    else:
        f.fill("skyblue")
    f.circle(f.mouse_x, f.mouse_y, 40)

    if f.mouse_x < f.width / 2:
        f.fill("tomato")
    else:
        f.fill("skyblue")
    f.rect(f.width / 2 - 20, f.height - 60, 40, 40)


f.run()
