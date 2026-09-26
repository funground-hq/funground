import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    f.text_size(28)                  # a 28-pixel em (v0.6); the font is DejaVu Sans
    f.fill("black")
    f.text("Hello", 30, 30)          # (x, y) is the top-left of the text
    f.text(f.frame_count, 30, 70, color="navy")   # any object: str() is applied

    f.text_size(20)
    f.no_fill()
    f.stroke("tomato")
    f.text("stroke colour when there is no fill", 30, 130)

    # text_width() measures a message at the current size, e.g. to centre it.
    f.text_size(48)
    f.fill("gold")
    message = "centred"
    x = (f.width - f.text_width(message)) / 2
    f.text(message, x, 200)

    # The size is the em: text_size(48) reserves 48 pixels of line height;
    # capital letters come out about three-quarters of that.
    f.stroke("silver")
    f.stroke_width(1)
    f.line(x - 10, 200, x - 10, 248)
    f.text_size(14)
    f.fill("gray40")
    f.text("48 px", x - 60, 216)


f.run()
