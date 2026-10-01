"""Loading and drawing an image

f.load_image() reads a picture file (PNG, JPEG, GIF, BMP, TGA) and gives you a picture.
f.image() draws it, at its own size or stretched. It follows f.translate(), f.rotate()
and f.opacity() like any other drawing.
"""
import funground as f

photo = f.load_image("data/photo.jpg")       # found next to this file


def setup():
    f.size(640, 400)


def draw():
    f.background("ivory")

    f.image(photo, 20, 20)                    # full size: 400 x 300
    f.fill("black")
    f.text_size(16)
    f.text("full size", 20, 330)

    with f.saved_state():                     # a smaller copy, turned
        f.translate(530, 105)
        f.rotate(-10)
        f.image(photo, -80, -60, 160, 120)
    f.text("smaller and turned", 450, 180)

    f.no_stroke()                             # a stripe, to see through the copy
    f.fill("tomato")
    f.rect(440, 225, 180, 40)
    with f.saved_state():
        f.opacity(128)
        f.image(photo, 440, 215, 180, 135)
    f.fill("black")
    f.text("half see-through", 450, 360)


f.run()
