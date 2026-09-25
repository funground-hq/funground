"""More shapes

square, triangle, quad and polygon for straight-sided shapes; arc for part of an ellipse, with
angles in degrees turning clockwise from the right, in three modes: open, chord and pie.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.stroke("black")
    p.stroke_width(2)
    p.fill("skyblue")
    p.square(30, 30, 100)                                  # top-left corner and size
    p.fill("gold")
    p.triangle(170, 130, 270, 130, 220, 30)
    p.fill("seagreen")
    p.quad(310, 40, 420, 30, 400, 130, 330, 120)
    p.fill("orchid")
    p.polygon([(520, 30), (600, 70), (580, 130), (480, 130), (460, 70)])

    p.fill("tomato")
    p.arc(100, 280, 140, 140, 0, 270)                      # open (the default)
    p.arc(280, 280, 140, 140, 0, 270, "chord")
    p.arc(460, 280, 140, 140, 0, 270, "pie")
    p.fill("black")
    p.text_size(16)
    for x, label in ((60, "open"), (250, "chord"), (440, "pie")):
        p.text(label, x, 365)


p.run()
