from funground import *

brush = 8
colour = colors.NAVY


def setup():
    size(640, 400)
    background(colors.WHITE)             # once: the drawing stays on the canvas


def draw():
    no_stroke()
    fill(colors.WHITE)
    rect(0, 360, 640, 40)
    fill(colors.BLACK)
    text_size(14)
    text(f"drag to paint  |  wheel: brush {brush}  |  r g b: colour  |  c: clear  |  last key: {key}", 10, 372)


def mouse_dragged():
    stroke(colour)
    stroke_width(brush)
    line(pmouse_x, pmouse_y, mouse_x, mouse_y)


def mouse_pressed():
    if mouse_button == RIGHT:         # right-click drops a dot
        no_stroke()
        fill(colour)
        circle(mouse_x, mouse_y, brush * 3)


def mouse_wheel(delta):
    global brush
    brush = int(constrain(brush - delta, 1, 40))


def key_pressed():
    global colour
    if key == "c":
        background(colors.WHITE)
    colour = {"r": colors.TOMATO, "g": colors.SEAGREEN, "b": colors.NAVY}.get(key, colour)


def key_typed():
    print("typed", key, key_code, is_key_pressed)
