"""Moving the paper, step 5: order matters

The same two lines, translate(300, 160) and rotate(30), in two orders. Slide then turn puts the pink petal at
(300, 160), tilted. Turn then slide puts the gold one somewhere else, because the paper slides along its own turned
arrows. This is step 5 of the project Moving the paper in the guide.

How it works:
- Pink, translate first: the paper slides to (300, 160), then turns there.
- Gold, rotate first: the paper turns around the corner of the canvas (the faded arrows), then slides 300 along
  its turned x arrow and 160 along its turned y arrow. It ends lower and further left.
- reset_matrix() puts the paper back where it started, so the second try begins from the corner. Step 6 shows
  push() and pop(), a tidier way to go back.

Make it yours:
- Change both 30s to 0. Is there any difference between the two orders now? Why not?
- Change both 30s to 90. Where does the gold petal go?
- Add scale(2) in each order, once before translate() and once after. Does the order of scale and translate matter
  too?
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
f.translate(300, 160)             # slide, then turn
f.rotate(30)
f.ellipse(0, -60, 24, 120)
axes()

f.reset_matrix()                  # back to the plain paper
f.fill("gold")
f.rotate(30)                      # turn, then slide
axes(faded=True)                  # the turned paper, still at the corner
f.translate(300, 160)
f.ellipse(0, -60, 24, 120)
axes()

f.reset_matrix()
f.text_size(16)
f.fill("pink")
f.text("translate, then rotate", 380, 330)
f.fill("gold")
f.text("rotate, then translate", 380, 355)
f.show()
