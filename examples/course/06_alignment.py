# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 330)
f.background("#f3efe6")
for i, align in enumerate(["left", "center", "right"]):
    left = 20 + i * 295
    x = left + {"left": 20, "center": 135, "right": 250}[align]
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.line(x, 40, x, 250)
    f.no_stroke()
    f.fill("#264653")
    f.text_align(align, "top")
    f.text_style("bold")
    f.text_size(25)
    f.text("FIELD NOTES", x, 70)
    f.text_style("normal")
    f.text_size(16)
    f.text("A book of walks", x, 135)
    f.text("Keep looking.", x, 175)
    f.text_align("left", "top")
    f.text(align + " alignment", left, 290)
f.save("06_alignment.png")
f.show()
