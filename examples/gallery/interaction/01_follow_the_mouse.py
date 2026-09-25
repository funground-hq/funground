"""Follow the mouse

p.mouse_x and p.mouse_y are where the mouse is; p.mouse_pressed is True while a button is held;
p.key_down("left") is True while that key is held.
"""
import playground as p

size = 60


def setup():
    p.size(640, 400)


def draw():
    global size
    p.background("white")
    if p.key_down("up"):
        size += 2
    if p.key_down("down"):
        size = max(10, size - 2)
    p.fill("tomato" if p.mouse_pressed else "skyblue")
    p.circle(p.mouse_x, p.mouse_y, size)
    p.fill("black")
    p.text("move the mouse, press a button, use the up/down keys", 20, 360)


p.run()
