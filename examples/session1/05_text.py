import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")

    f.text_size(28)
    f.fill("black")
    f.text("Hello", 30, 40)
    f.text(f.frame_count, 30, 80, color="navy")

    f.text_size(20)
    f.no_fill()
    f.stroke("tomato")
    f.text("stroke colour when there is no fill", 30, 140)

    f.text_size(48)
    f.fill("gold")
    f.text(3.5, 30, 200)


f.run()
