"""Follow the mouse

f.mouse_x and f.mouse_y are where the mouse is; f.is_mouse_pressed is True while a button is held;
f.key_down("left") is True while that key is held.
"""
import funground as f

size = 60


def setup():
    f.size(640, 400)


def draw():
    global size
    f.background("white")
    if f.key_down("up"):
        size += 2
    if f.key_down("down"):
        size = max(10, size - 2)
    f.fill("tomato" if f.is_mouse_pressed else "skyblue")
    f.circle(f.mouse_x, f.mouse_y, size)
    f.fill("black")
    f.text("move the mouse, press a button, use the up/down keys", 20, 360)


f.run()
