"""Moving the paper, step 6: push and pop

The same loop of petals twice. On the left, without push() and pop(), every turn adds to all the turns before it,
and the petals end up bunched and lopsided. On the right, push() saves the paper before each turn and pop() puts
it back, so every petal starts from the same unturned paper. This is step 6 of the project Moving the paper in the
guide.

How it works:
- The loop asks for turns of -90, -75, -60 ... 90 degrees, 15 apart.
- Left: the turns add up. The paper is turned -90 in all, then -165 (-90 - 75), then -225, -270, -300, -315, -315,
  -300, -270, -225, -165, -90 and finally 0. Some petals land on top of each other and some directions get none.
- Right: push() remembers the paper as it is, rotate() turns it for one petal, and pop() brings back the
  remembered paper. Each petal gets exactly the angle the loop asks for.
- The arrows, drawn after the right-hand loop, show that pop() left the paper unturned.
- push() also saves the fill, the stroke, the opacity and the other drawing settings, and pop() brings them back.

Make it yours:
- On the right, move pop() above the ellipse line. What is drawn, and why?
- On the left, change range(-90, 91, 15) to range(0, 181, 15). Is the left flower still lopsided?
- Make the left flower right without push() and pop(): turn once to -90 before the loop, then rotate(15) each time.
"""
import funground as f


def axes(faded=False, size=80):
    """Draw the paper's x arrow (orange) and y arrow (turquoise) from its (0, 0)."""
    f.push()                                  # axes() tidies up after itself, the same way
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
f.opacity(180)

f.translate(150, 200)             # left: no push and pop
for angle in range(-90, 91, 15):
    f.rotate(angle)               # adds to every turn before it
    f.ellipse(0, -60, 24, 120)

f.reset_matrix()
f.translate(450, 200)             # right: push and pop around each petal
for angle in range(-90, 91, 15):
    f.push()                      # remember the paper as it is
    f.rotate(angle)               # turn it for this petal only
    f.ellipse(0, -60, 24, 120)
    f.pop()                       # bring back the remembered paper
axes()                            # still unturned

f.reset_matrix()
f.opacity(255)
f.text_size(16)
f.fill("white")
f.text("without push and pop", 70, 360)
f.text("with push and pop", 385, 360)
f.show()
