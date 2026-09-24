import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    p.fill("gold")
    p.stroke("black")
    p.stroke_width(3)
    p.circle(200, 120, 100)

    p.no_fill()
    p.stroke("tomato")
    p.rect(300, 70, 120, 100)

    p.fill("skyblue")
    p.no_stroke()
    p.ellipse(200, 300, 160, 80)

    p.stroke("navy")
    p.stroke_width(8)
    p.line(320, 250, 600, 350)
    p.point(560, 260)


p.run()
