# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

LARGE_X, LARGE_Y, LARGE_SIZE = 110, 150, 110
SMALL_X, SMALL_Y, SMALL_SIZE = 270, 115, 34

f.size(360, 300)
f.background("#f3efe6")
f.no_stroke()
f.fill("#264653")
f.circle(LARGE_X, LARGE_Y, LARGE_SIZE)
f.fill("#e76f51")
f.circle(SMALL_X, SMALL_Y, SMALL_SIZE)
f.save("02_starter.png")
f.show()
