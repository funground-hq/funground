# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(700, 290)
f.background("#f3efe6")
for cx, cy, scale in [(170, 95, 1.0), (370, 130, 0.35), (530, 130, 0.15)]:
    f.no_stroke()
    f.fill("#264653")
    f.rect(cx - 13*scale, cy + 40*scale, 26*scale, 82*scale)
    f.circle(cx, cy, 108*scale)
f.text_align("left", "top")
f.text_size(16)
f.text("Same proportions at 100%, 35% and 15%", 30, 245)
f.save("04_small.png")
f.show()
