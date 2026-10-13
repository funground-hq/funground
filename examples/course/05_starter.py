# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

COUNT = 6
GAP = 60
DIAMETER = 24

f.size(420, 230)
f.background("#f3efe6")
f.no_stroke()
f.fill("#264653")
for index in range(COUNT):
    x = 50 + index * GAP
    f.circle(x, 115, DIAMETER)
f.save("05_starter.png")
f.show()
