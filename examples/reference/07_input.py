import playground as p

x = 320


def setup():
    p.size(640, 400)


def draw():
    global x

    p.background("white")

    # Mouse: live values, read once before each draw().
    if p.mouse_pressed:
        p.fill("tomato")
    else:
        p.fill("skyblue")
    p.circle(p.mouse_x, p.mouse_y, 40)

    # Keyboard: key_down() is True while the key is held.
    if p.key_down("left"):
        x -= 3
    if p.key_down("right"):
        x += 3
    if p.key_down("space"):
        p.fill("gold")
    else:
        p.fill("tomato")
    p.circle(x, 300, 60)

    p.fill("black")
    p.text_size(16)
    p.text(f"mouse ({p.mouse_x}, {p.mouse_y})   left/right move the ball, space colours it", 10, 10)


p.run()
