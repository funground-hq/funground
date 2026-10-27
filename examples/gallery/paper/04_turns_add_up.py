"""Moving the paper, step 4: turns add up

Four petals from the same ellipse call, with rotate(30) between them. Each rotate turns the paper from where the
last one left it, so the petals fan out 30 degrees apart. This is step 4 of the project Moving the paper in the
guide.

How it works:
- The first petal is drawn before any turn: straight up.
- Each rotate(30) adds 30 degrees to the turns before it: 30, then 60, then 90 in all.
- The arrows, drawn at the end, show the paper after all three turns: x points down and y points left.
- translate() adds up in the same way: two translate(100, 0) are one translate(200, 0).

Make it yours:
- Change the three 30s to 15. How wide is the fan now?
- Write the same thing as a loop: for i in range(4), with a petal and a rotate(30) inside. Then try range(12).
- What does a loop of rotate(1) and a petal, 180 times, draw? Predict first, then try it.
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
f.translate(300, 260)
f.no_stroke()
f.fill("pink")
f.opacity(180)
f.ellipse(0, -60, 24, 120)        # no turn yet: straight up
f.rotate(30)
f.ellipse(0, -60, 24, 120)        # 30 degrees in all
f.rotate(30)
f.ellipse(0, -60, 24, 120)        # 60 in all: this rotate adds to the one before
f.rotate(30)
f.ellipse(0, -60, 24, 120)        # 90 in all
axes()                            # the paper after all three turns
f.show()
