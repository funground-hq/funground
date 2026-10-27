"""Moving the paper, step 1: where is (0, 0)?

Two petals and the paper's own arrows. The orange arrow is the paper's x direction, the turquoise arrow its y
direction, and the white dot is where both are 0. This is the first step of the project Moving the paper in the
guide.

How it works:
- axes() draws the arrows from (0, 0). Every step of the project has it, so you can always see where the paper is.
- (0, 0) is the top-left corner of the canvas. x grows to the right, y grows downwards.
- ellipse(x, y, width, height) puts the middle of the ellipse at (x, y). The first petal's middle is (0, 0), so
  three quarters of it are off the canvas: only the part to the right of and below the corner shows.
- The second petal's middle is (300, 200), the middle of the canvas.

Make it yours:
- Move the first petal to (60, 60). Which way did it move?
- Change the second petal's width and height to 120 and 24. Which way does it lie now?
- Draw a third petal at (600, 400). How much of it can you see, and why?
"""
import funground as f


def axes(faded=False, size=80):
    """Draw the paper's x arrow (orange) and y arrow (turquoise) from its (0, 0)."""
    f.push()                                  # axes() tidies up after itself; step 6 shows how
    f.opacity(70 if faded else 255)
    f.stroke_width(3)
    f.stroke("orange")
    f.line(0, 0, size, 0)
    f.line(size, 0, size - 10, -6)
    f.line(size, 0, size - 10, 6)
    f.stroke("turquoise")
    f.line(0, 0, 0, size)
    f.line(0, size, -6, size - 10)
    f.line(0, size, 6, size - 10)
    f.stroke("white")
    f.stroke_width(10)
    f.point(0, 0)                             # the paper's (0, 0): a round dot, whatever drawing mode is chosen
    f.no_stroke()
    f.text_size(16)
    f.fill("orange")
    f.text("x", size - 8, 8)
    f.fill("turquoise")
    f.text("y", 10, size - 18)
    f.pop()


f.size(600, 400)
f.background("navy")
f.no_stroke()
f.fill("pink")
f.ellipse(0, 0, 24, 120)          # middle at (0, 0): mostly off the canvas
f.ellipse(300, 200, 24, 120)      # middle at (300, 200): the middle of the canvas
axes()                            # last, so the arrows are on top
f.show()
