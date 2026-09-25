import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    p.text_size(28)                  # a 28-pixel em (v0.6); the font is DejaVu Sans
    p.fill("black")
    p.text("Hello", 30, 30)          # (x, y) is the top-left of the text
    p.text(p.frame_count, 30, 70, color="navy")   # any object: str() is applied

    p.text_size(20)
    p.no_fill()
    p.stroke("tomato")
    p.text("stroke colour when there is no fill", 30, 130)

    # text_width() measures a message at the current size, e.g. to centre it.
    p.text_size(48)
    p.fill("gold")
    message = "centred"
    x = (p.width - p.text_width(message)) / 2
    p.text(message, x, 200)

    # The size is the em: text_size(48) reserves 48 pixels of line height;
    # capital letters come out about three-quarters of that.
    p.stroke("silver")
    p.stroke_width(1)
    p.line(x - 10, 200, x - 10, 248)
    p.text_size(14)
    p.fill("gray40")
    p.text("48 px", x - 60, 216)


p.run()
