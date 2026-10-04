"""A picture with a transparent background

f.clear() makes every pixel transparent. A PNG saved afterwards keeps the transparency, so the
shape can go on any background later. The window shows transparent as black.

How it works:
- f.clear() makes the whole canvas see-through. f.background() would paint it a solid colour.
- f.fill(), f.stroke() and f.stroke_width() set the look of the circle, and f.circle() draws it.
- f.save("sticker.png") writes the frame. A PNG can hold transparency. Pixels the circle did not
  cover stay see-through.
- The save runs once, on the first frame, because of f.frame_count == 0.
- To see it, open sticker.png in a program that shows transparency, or place it on a coloured page.

Make it yours:
- Change the colours in f.fill() and f.stroke().
- Make a different sticker: draw a few shapes, or some text, in place of the circle.
- Make part of it half see-through: use f.fill(255, 99, 71, 128). The last number is the alpha.
- Change the size: f.circle(320, 200, 260) has a diameter of 260.
- Change the file name in f.save().
"""
import funground as f


def setup():
    f.size(640, 400)


def draw():
    f.clear()
    f.fill("tomato")
    f.stroke("black")
    f.stroke_width(6)
    f.circle(320, 200, 260)
    if f.frame_count == 0:
        f.save("sticker.png")


f.run()
