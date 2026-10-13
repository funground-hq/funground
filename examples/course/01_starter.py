# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

X = 180
Y = 150
DIAMETER = 48

f.size(360, 300)
f.background("#f3efe6")
f.no_stroke()
f.fill("#264653")
f.circle(X, Y, DIAMETER)
f.save("01_starter.png")
f.show()
