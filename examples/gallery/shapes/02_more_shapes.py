"""More shapes

square, triangle, quad and polygon for straight-sided shapes; arc for part of an ellipse, with
angles in degrees turning clockwise from the right, in three modes: open, chord and pie.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.stroke("black")
    f.stroke_width(2)
    f.fill("skyblue")
    f.square(30, 30, 100)                                  # top-left corner and size
    f.fill("gold")
    f.triangle(170, 130, 270, 130, 220, 30)
    f.fill("seagreen")
    f.quad(310, 40, 420, 30, 400, 130, 330, 120)
    f.fill("orchid")
    f.polygon([(520, 30), (600, 70), (580, 130), (480, 130), (460, 70)])

    f.fill("tomato")
    f.arc(100, 280, 140, 140, 0, 270)                      # open (the default)
    f.arc(280, 280, 140, 140, 0, 270, "chord")
    f.arc(460, 280, 140, 140, 0, 270, "pie")
    f.fill("black")
    f.text_size(16)
    for x, label in ((60, "open"), (250, "chord"), (440, "pie")):
        f.text(label, x, 365)


f.run()
