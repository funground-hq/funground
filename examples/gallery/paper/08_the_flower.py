"""Moving the paper, step 8: the flower

Everything from the project in one picture: a half flower with petals from -90 to 90 degrees, a gold middle, a
stem and two leaves. Each part slides and turns the paper for itself and puts it back with push() and pop(). This
is the last step of the project Moving the paper in the guide.

How it works:
- translate(300, 230) moves the paper's (0, 0) to the middle of the flower. Every number after it is measured from
  there: the stem runs from (0, 0) down to (0, 170).
- Each leaf is a push(), a translate() down the stem, a rotate() and a pop(). The leaf is drawn pointing up from
  its own (0, 0), so the turn swings it out from the stem.
- The petals are the loop from step 6: push(), rotate(angle), a petal pointing up, pop(). -90 points left, 0 up and
  90 right.
- The middle is drawn last, on the unturned paper, so it covers the ends of the petals.

Make it yours:
- Change range(-90, 91, 15) to range(0, 360, 15) for a whole flower, then move the stem behind it.
- Change PETALS to 20 or to 7: the angle between petals is worked out from it.
- Draw a smaller ring of petals in another colour inside the first.
- Put the whole flower in a function flower(x, y) and draw three of them in a row.
"""
import funground as f

PETAL_LENGTH = 140
PETALS = 13                                     # from -90 to 90, both included
STEP = 180 / (PETALS - 1)                       # degrees between two petals


def leaf(down, angle):
    """A leaf growing from the stem, `down` below the flower's middle, turned by `angle` degrees."""
    f.push()
    f.translate(0, down)
    f.rotate(angle)
    f.ellipse(0, -30, 20, 60)                   # pointing up from its own (0, 0)
    f.pop()


f.size(600, 400)
f.background("navy")
f.translate(300, 230)                           # the flower's middle

f.stroke("mediumseagreen")                      # the stem
f.stroke_width(6)
f.line(0, 0, 0, 170)
f.no_stroke()
f.fill("mediumseagreen")
leaf(90, -55)
leaf(125, 50)

f.fill("pink")                                  # the petals
f.opacity(180)
for i in range(PETALS):
    f.push()
    f.rotate(-90 + i * STEP)
    f.ellipse(0, -PETAL_LENGTH / 2, 26, PETAL_LENGTH)
    f.pop()

f.opacity(255)                                  # the middle
f.fill("gold")
f.circle(0, 0, 36)
f.show()
