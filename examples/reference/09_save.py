import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("white")
    f.fill("gold")
    f.stroke("black")
    f.stroke_width(4)
    f.circle(320, 200, 200)
    f.fill("black")
    f.text_size(24)
    f.text("press s to save", 30, 30)

    # save() writes this frame once it is complete:
    # .png is pixels, .pdf and .svg are vector drawings of the same frame.
    if f.key_down("s"):
        f.save("my_sketch.png")
        f.save("my_sketch.pdf")


f.run()
