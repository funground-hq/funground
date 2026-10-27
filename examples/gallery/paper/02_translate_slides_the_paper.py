"""Moving the paper, step 2: translate slides the paper

The same petal as step 1, drawn with the same call, ellipse(0, 0, 24, 120), lands in the middle of the canvas.
The petal did not move: the paper moved under the pen. This is step 2 of the project Moving the paper in the guide.

How it works:
- The faded arrows show the paper before the move, with (0, 0) in the corner.
- translate(300, 200) slides the paper 300 to the right and 200 down. Its (0, 0), the white dot, is now in the
  middle of the canvas.
- Everything drawn after translate() is drawn on the moved paper, so (0, 0) now means the middle.
- The bright arrows show the paper after the move. They still point the same way: sliding does not turn.

Make it yours:
- Change translate(300, 200) to translate(100, 300). Where does the petal go?
- Add a second translate(100, 0) after the first. Do the two moves add up?
- Try a negative number: translate(-100, 0) after the first. Which way does the paper go?
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
axes(faded=True)                  # the paper before the move: (0, 0) in the corner
f.translate(300, 200)             # slide the paper 300 to the right and 200 down
f.no_stroke()
f.fill("pink")
f.ellipse(0, 0, 24, 120)          # the same call as step 1's first petal
axes()                            # the paper after the move
f.show()
