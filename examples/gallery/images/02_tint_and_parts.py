"""Tinting a picture and drawing part of it

f.tint() colours every picture drawn after it: the red, green and blue of each pixel are
multiplied by the tint, and its alpha too. f.no_tint() stops it. To draw only part of a
picture, give image() four more numbers: the left, top, width and height of the part.
"""
import funground as f

photo = f.load_image("data/photo.jpg")       # found next to this file


def setup():
    f.size(640, 400)


def label(words, x, y):
    f.fill("black")
    f.text_size(14)
    f.text(words, x, y)


def draw():
    f.background("ivory")

    # A stripe behind the third picture, to see through it.
    f.no_stroke()
    f.fill("tomato")
    f.rect(440, 50, 190, 40)

    # Row 1: the same photo with three tints.
    f.tint(255, 170, 120)                    # warm: less blue and green
    f.image(photo, 10, 10, 200, 150)
    f.tint(120, 170, 255)                    # cool: less red and green
    f.image(photo, 220, 10, 200, 150)
    f.tint(255, 120)                         # white, half see-through
    f.image(photo, 430, 10, 200, 150)
    f.no_tint()
    label("warm", 10, 168)
    label("cool", 220, 168)
    label("half see-through", 430, 168)

    # Row 2: three parts of the photo, each drawn bigger than it is.
    # image(picture, x, y, width, height, sx, sy, sw, sh)
    f.image(photo, 10, 215, 200, 150, 130, 160, 100, 75)    # the house
    f.image(photo, 220, 215, 200, 150, 215, 115, 105, 79)   # the sun
    f.tint("gold")
    f.image(photo, 430, 215, 200, 150, 10, 10, 120, 90)     # the stars, tinted too
    f.no_tint()
    label("the house", 10, 376)
    label("the sun", 220, 376)
    label("the stars, with a tint", 430, 376)


f.run()
