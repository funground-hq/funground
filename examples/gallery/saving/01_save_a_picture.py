"""Saving your work

f.save("name.png") writes the frame when it is finished. Use .pdf or .svg for a picture made of
shapes that stays sharp at any size.
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.background("ivory")
    f.fill("tomato")
    f.circle(320, 200, 200)
    f.fill("black")
    f.text_size(24)
    f.text("saved as my_picture.png and my_picture.pdf", 90, 340)
    if f.frame_count == 0:           # save the first frame once
        f.save("my_picture.png")
        f.save("my_picture.pdf")


f.run()
