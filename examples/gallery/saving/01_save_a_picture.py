"""Saving your work

p.save("name.png") writes the frame when it is finished. Use .pdf or .svg for a picture made of
shapes that stays sharp at any size.
"""
import playground as p


def setup():
    p.size(640, 400)


def draw():
    p.background("ivory")
    p.fill("tomato")
    p.circle(320, 200, 200)
    p.fill("black")
    p.text_size(24)
    p.text("saved as my_picture.png and my_picture.pdf", 90, 340)
    if p.frame_count == 0:           # save the first frame once
        p.save("my_picture.png")
        p.save("my_picture.pdf")


p.run()
