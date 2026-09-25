"""A paint program

Callbacks are functions you define with special names; Playground calls them when something
happens. mouse_dragged draws, mouse_wheel changes the brush, key_pressed clears or picks a
colour, and pmouse_x/pmouse_y (last frame's mouse) join the strokes up smoothly.
"""
import playground as p

brush = 8
colour = "navy"


def setup():
    p.size(640, 400)
    p.background("white")             # once: the drawing stays on the canvas


def draw():
    p.no_stroke()
    p.fill("white")
    p.rect(0, 360, 640, 40)
    p.fill("black")
    p.text_size(14)
    p.text(f"drag to paint  |  wheel: brush {brush}  |  r g b: colour  |  c: clear  |  last key: {p.key}", 10, 372)


def mouse_dragged():
    p.stroke(colour)
    p.stroke_width(brush)
    p.line(p.pmouse_x, p.pmouse_y, p.mouse_x, p.mouse_y)


def mouse_pressed():
    if p.mouse_button == "right":     # right-click drops a dot
        p.no_stroke()
        p.fill(colour)
        p.circle(p.mouse_x, p.mouse_y, brush * 3)


def mouse_wheel(delta):
    global brush
    brush = int(p.constrain(brush - delta, 1, 40))


def key_pressed():
    global colour
    if p.key == "c":
        p.background("white")
    colour = {"r": "tomato", "g": "seagreen", "b": "navy"}.get(p.key, colour)


def key_typed():
    print("typed", p.key, p.key_code, p.is_key_pressed)


p.run()
