# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 330)
f.background("#f3efe6")
for i in range(3):
    left = 20 + i * 295
    f.no_stroke()
    f.fill("#264653")
    f.rect(left + 123, 130, 24, 112)
    if i == 0:
        f.circle(left + 98, 125, 65)
        f.circle(left + 170, 122, 65)
        f.circle(left + 134, 91, 85)
    elif i == 1:
        f.circle(left + 135, 116, 113)
    else:
        f.triangle(left + 75, 162, left + 195, 162, left + 135, 52)
    f.text_align("left", "top")
    f.text_size(15)
    f.text(["Several canopy parts", "One round canopy", "One pointed canopy"][i], left, 283)
f.save("04_reduction.png")
f.show()
