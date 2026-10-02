"""Sliders, a checkbox and a button

A slider, a checkbox and a button sit in a panel below the canvas. Make each one once in setup(),
keep it in a variable, and ask it for its value in draw(). Here the sliders set the number and the
length of the petals, the checkbox makes the flower spin, and the button picks the next colour.
"""
import funground as f

COLOURS = [(255, 99, 71), (240, 180, 20), (46, 139, 87), (65, 105, 225), (186, 85, 211)]
shade = 0           # which colour is showing
turn = 0            # how far the flower has spun, in degrees


def setup():
    global petals, length, spin, next_colour
    f.size(480, 360)
    petals = f.create_slider(3, 24, 9, step=1, label="petals")
    length = f.create_slider(40, 150, 110, label="length")
    spin = f.create_checkbox("spin")
    next_colour = f.create_button("next colour")


def draw():
    global shade, turn
    if next_colour.clicked():             # true once for each click
        shade = (shade + 1) % len(COLOURS)
    if spin.checked():
        turn += 1.5

    f.background(252, 248, 240)
    f.no_stroke()
    f.translate(f.width / 2, f.height / 2)
    count = petals.value()
    for i in range(count):
        f.push()
        f.rotate(turn + 360 * i / count)
        red, green, blue = COLOURS[shade]
        f.fill(red, green, blue, 150)
        f.ellipse(0, -length.value() / 2, 36, length.value())
        f.pop()
    f.fill("black")
    f.circle(0, 0, 18)


f.run()
