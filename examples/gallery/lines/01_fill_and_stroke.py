"""Fill and stroke

fill is the inside, stroke the outline. no_fill() and no_stroke() switch either off; the
stroke is centred on the edge, half outside and half inside.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("whitesmoke")
    f.fill("gold")
    f.stroke("black")
    f.stroke_width(3)
    f.circle(120, 140, 140)

    f.no_fill()                      # outline only
    f.stroke("tomato")
    f.stroke_width(10)
    f.rect(240, 70, 140, 140)

    f.fill("skyblue")
    f.no_stroke()                    # inside only
    f.ellipse(520, 140, 160, 100)

    for i in range(1, 9):            # stroke widths 1 to 8
        f.stroke("navy")
        f.stroke_width(i)
        f.line(60 + i * 60, 280, 60 + i * 60, 360)


f.run()
