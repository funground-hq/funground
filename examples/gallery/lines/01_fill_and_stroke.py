"""Fill and stroke

fill is the inside, stroke the outline. no_fill() and no_stroke() switch either off; the
stroke is centred on the edge, half outside and half inside.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("whitesmoke")
    p.fill("gold")
    p.stroke("black")
    p.stroke_width(3)
    p.circle(120, 140, 140)

    p.no_fill()                      # outline only
    p.stroke("tomato")
    p.stroke_width(10)
    p.rect(240, 70, 140, 140)

    p.fill("skyblue")
    p.no_stroke()                    # inside only
    p.ellipse(520, 140, 160, 100)

    for i in range(1, 9):            # stroke widths 1 to 8
        p.stroke("navy")
        p.stroke_width(i)
        p.line(60 + i * 60, 280, 60 + i * 60, 360)


p.run()
