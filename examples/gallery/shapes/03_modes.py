"""Placing shapes by their centre or corners

The same four numbers, drawn under each drawing mode. The red dot marks (x, y) in every box.
rect_mode and ellipse_mode have four modes each. image_mode has three.
"""
import funground as f

X, Y, A, B = 80, 50, 40, 25          # the numbers every shape below is given


def make_picture():
    pic = f.create_graphics(30, 20)
    pic.background("gold")
    pic.fill("seagreen")
    pic.circle(15, 10, 14)
    return pic


def cell(column, row, label):
    """Move to a box, draw its frame and its label, and mark (X, Y)."""
    f.translate(column * 160, row * 133)
    f.no_fill()
    f.stroke("lightgray")
    f.stroke_width(1)
    f.rect(2, 2, 156, 129)
    f.fill("black")
    f.no_stroke()
    f.text_size(12)
    f.text(label, 8, 6)


def dot():
    f.fill("red")
    f.no_stroke()
    f.circle(X, Y, 6)


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.stroke("black")
    f.stroke_width(2)
    picture = make_picture()

    for column, mode in enumerate(("corner", "corners", "center", "radius")):
        with f.saved_state():
            cell(column, 0, f'rect_mode("{mode}")')
            f.rect_mode(mode)
            f.fill("skyblue")
            f.stroke("black")
            f.stroke_width(2)
            f.rect(X, Y, A, B)
            dot()

    for column, mode in enumerate(("center", "radius", "corner", "corners")):
        with f.saved_state():
            cell(column, 1, f'ellipse_mode("{mode}")')
            f.ellipse_mode(mode)
            f.fill("orchid")
            f.stroke("black")
            f.stroke_width(2)
            f.ellipse(X, Y, A, B)
            dot()

    for column, mode in enumerate(("corner", "corners", "center")):
        with f.saved_state():
            cell(column, 2, f'image_mode("{mode}")')
            f.image_mode(mode)
            f.image(picture, X, Y, A, B)
            dot()

    with f.saved_state():
        cell(3, 2, "numbers: x, y, 40, 25")
        f.fill("black")
        f.text_size(12)
        f.text("Corners mode reads", 8, 40)
        f.text("the last two numbers", 8, 56)
        f.text("as a second corner,", 8, 72)
        f.text("in any order.", 8, 88)


f.run()
