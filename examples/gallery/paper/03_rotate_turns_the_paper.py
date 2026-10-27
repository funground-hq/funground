"""Moving the paper, step 3: rotate turns the paper around its (0, 0)

A petal pointing up from the white dot, before and after the paper turns by 30 degrees. The petal swings around
the dot, not around its own middle. This is step 3 of the project Moving the paper in the guide.

How it works:
- translate(300, 240) first slides the paper so that its (0, 0) is in view.
- ellipse(0, -60, 24, 120) is a petal 120 long whose middle is 60 above (0, 0): up is negative y. So the petal
  starts at the dot and points up.
- The faded petal and arrows are the paper before the turn.
- rotate(30) turns the paper 30 degrees clockwise around its (0, 0). Angles are in degrees, and a positive angle
  turns clockwise on the screen.
- The same ellipse call, made again on the turned paper, draws the bright petal.

Make it yours:
- Change 30 to 90, to 180, to -30 and to 360. Which way does a negative angle turn?
- Remove the translate() line. The paper now turns around the top-left corner of the canvas: where did the petal go?
- Change the petal to ellipse(0, 0, 24, 120). Why does the turn now look like a spin in place?
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
f.translate(300, 240)             # slide the paper first, so its (0, 0) is in view
f.no_stroke()
f.fill("pink")
f.opacity(70)
f.ellipse(0, -60, 24, 120)        # before the turn: a petal pointing up from (0, 0)
axes(faded=True)
f.rotate(30)                      # turn the paper 30 degrees clockwise around its (0, 0)
f.opacity(255)
f.ellipse(0, -60, 24, 120)        # the same call, on the turned paper
axes()
f.show()
