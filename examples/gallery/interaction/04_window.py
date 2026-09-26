"""The window: cursor, size and full screen

p.cursor() picks the mouse pointer - here a hand over the button, crosshairs elsewhere - and
p.no_cursor() hides it. Press f for p.full_screen(), where p.width and p.height become the
screen's size, and 1, 2 or 3 for p.resize_canvas(). Everything is placed using p.width and
p.height, so the drawing fits whatever the size.
"""
import playground as p

SIZES = {"1": (640, 400), "2": (800, 500), "3": (400, 400)}


def setup():
    p.size(640, 400)
    p.cursor("cross")


def over_button():
    return abs(p.mouse_x - p.width / 2) < 90 and abs(p.mouse_y - p.height / 2) < 30


def draw():
    p.background("lavender")
    p.cursor("hand" if over_button() else "cross")
    p.no_stroke()
    p.fill("slateblue" if over_button() else "mediumpurple")
    p.rect(p.width / 2 - 90, p.height / 2 - 30, 180, 60)
    p.fill("white")
    p.text_size(20)
    p.text_align("center", "center")
    p.text("a button", p.width / 2, p.height / 2)
    p.fill("black")
    p.text_size(14)
    p.text_align("left", "bottom")
    p.text(f"{p.width} x {p.height}   f: full screen   1, 2, 3: sizes   h: hide the pointer",
           10, p.height - 10)


def key_pressed():
    if p.key == "f":
        p.full_screen()
    elif p.key in SIZES:
        p.resize_canvas(*SIZES[p.key])
    elif p.key == "h":
        p.no_cursor()


p.run()
