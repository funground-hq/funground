import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    f.fill("gold")
    f.stroke("black")
    f.stroke_width(3)
    f.circle(200, 120, 100)

    f.no_fill()
    f.stroke("tomato")
    f.rect(300, 70, 120, 100)

    f.fill("skyblue")
    f.no_stroke()
    f.ellipse(200, 300, 160, 80)

    f.stroke("navy")
    f.stroke_width(8)
    f.line(320, 250, 600, 350)
    f.point(560, 260)


f.run()
