# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

# Change positions first. Keep these sizes and colours fixed for the first three versions.
CIRCLE_X, CIRCLE_Y = 115, 130
SQUARE_X, SQUARE_Y = 230, 170  # square uses its top-left corner
TRIANGLE_X, TRIANGLE_Y = 260, 95
VERSION = "a"  # change to "b" or "c" before saving the next version

f.size(360, 300)
f.background("#f3efe6")
f.no_stroke()
f.fill("#264653")
f.circle(CIRCLE_X, CIRCLE_Y, 54)
f.fill("#e76f51")
f.rect(SQUARE_X, SQUARE_Y, 42, 42)
f.fill("#2a9d8f")
f.triangle(TRIANGLE_X - 22, TRIANGLE_Y + 20,
           TRIANGLE_X + 22, TRIANGLE_Y + 20, TRIANGLE_X, TRIANGLE_Y - 20)
f.save("01_exercise_" + VERSION + ".png")
f.show()
