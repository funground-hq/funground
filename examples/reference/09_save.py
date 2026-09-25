import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("white")
    p.fill("gold")
    p.stroke("black")
    p.stroke_width(4)
    p.circle(320, 200, 200)
    p.fill("black")
    p.text_size(24)
    p.text("press s to save", 30, 30)

    # save() writes this frame once it is complete:
    # .png is pixels, .pdf and .svg are vector drawings of the same frame.
    if p.key_down("s"):
        p.save("my_sketch.png")
        p.save("my_sketch.pdf")


p.run()
