import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")

    p.text_size(28)
    p.fill("black")
    p.text("Hello", 30, 40)
    p.text(p.frame_count, 30, 80, color="navy")

    p.text_size(20)
    p.no_fill()
    p.stroke("tomato")
    p.text("stroke colour when there is no fill", 30, 140)

    p.text_size(48)
    p.fill("gold")
    p.text(3.5, 30, 200)


p.run()
