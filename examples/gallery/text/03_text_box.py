"""Text in boxes and columns

f.text_box() wraps text inside a box and gives back whatever did not fit, so the rest can
flow on into the next box - the way DrawBot's textBox() works. A "\n" inside f.text() starts
a new line, and f.text_leading() sets the distance from one line to the next.
"""
import funground as f

STORY = (
    "A sketch is a small program that draws. It starts with setup(), which runs once, and "
    "then draw() runs again and again, many times a second. Each time, the picture is made "
    "fresh: shapes, colours and words placed with numbers. Change a number and the picture "
    "changes with it. That is the whole trick, and it goes a very long way.\n"
    "Text is drawn with the same care as shapes. It can be lined up left, right or centred, "
    "and when a box is full the words carry on in the next one."
)


def setup():
    f.size(640, 400)


def draw():
    f.background("ivory")
    f.fill("darkslategray")
    f.text_size(34)
    f.text_leading(36)
    f.text("Columns\nof words", 30, 24)

    f.text_size(15)
    f.text_leading(None)                     # back to automatic: 1.25 x the text size
    f.no_fill()
    f.stroke("lightgray")
    f.rect(30, 130, 280, 240)
    f.rect(330, 130, 280, 240)

    f.no_stroke()
    f.fill("black")
    rest = f.text_box(STORY, 42, 142, 256, 216)      # returns what did not fit...
    rest = f.text_box(rest, 342, 142, 256, 216)      # ...which flows on into the next box
    if rest:
        f.fill("firebrick")
        f.text("(more did not fit)", 342, 376)


f.run()
