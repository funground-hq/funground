# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 300)
f.background("#f3efe6")
for i, ink in enumerate([205, 125, 35]):
    left = 20 + i * 295
    f.no_stroke()
    f.fill(235)
    f.rect(left, 30, 270, 215)
    f.fill(ink)
    f.text_size(29)
    f.text_style("bold")
    f.text_align("left", "top")
    f.text("READ", left + 20, 80)
    f.text_style("normal")
    f.text_size(16)
    f.text("Saturday at 10 am", left + 20, 155)
    f.fill("#264653")
    f.text_size(15)
    f.text("Ink grey: " + str(ink), left, 265)
f.save("03_values.png")
f.show()
