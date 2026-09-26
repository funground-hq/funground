import funground as f

x = 320


def setup():
    f.size(640, 400)


def draw():
    global x

    f.background("white")

    # Mouse: live values, read once before each draw().
    if f.is_mouse_pressed:
        f.fill("tomato")
    else:
        f.fill("skyblue")
    f.circle(f.mouse_x, f.mouse_y, 40)

    # Keyboard: key_down() is True while the key is held.
    if f.key_down("left"):
        x -= 3
    if f.key_down("right"):
        x += 3
    if f.key_down("space"):
        f.fill("gold")
    else:
        f.fill("tomato")
    f.circle(x, 300, 60)

    f.fill("black")
    f.text_size(16)
    f.text(f"mouse ({f.mouse_x}, {f.mouse_y})   left/right move the ball, space colours it", 10, 10)


f.run()
