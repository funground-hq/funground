"""The window: cursor, size and full screen

f.cursor() picks the mouse pointer - here a hand over the button, crosshairs elsewhere - and
f.no_cursor() hides it. Press f for f.full_screen(), where f.width and f.height become the
screen's size, and 1, 2 or 3 for f.resize_canvas(). Everything is placed using f.width and
f.height, so the drawing fits whatever the size.
"""
import funground as f

SIZES = {"1": (640, 400), "2": (800, 500), "3": (400, 400)}


def setup():
    f.size(640, 400)
    f.cursor("cross")


def over_button():
    return abs(f.mouse_x - f.width / 2) < 90 and abs(f.mouse_y - f.height / 2) < 30


def draw():
    f.background("lavender")
    f.cursor("hand" if over_button() else "cross")
    f.no_stroke()
    f.fill("slateblue" if over_button() else "mediumpurple")
    f.rect(f.width / 2 - 90, f.height / 2 - 30, 180, 60)
    f.fill("white")
    f.text_size(20)
    f.text_align("center", "center")
    f.text("a button", f.width / 2, f.height / 2)
    f.fill("black")
    f.text_size(14)
    f.text_align("left", "bottom")
    f.text(f"{f.width} x {f.height}   f: full screen   1, 2, 3: sizes   h: hide the pointer",
           10, f.height - 10)


def key_pressed():
    if f.key == "f":
        f.full_screen()
    elif f.key in SIZES:
        f.resize_canvas(*SIZES[f.key])
    elif f.key == "h":
        f.no_cursor()


f.run()
