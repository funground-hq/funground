# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")
for i, size in enumerate([22, 48, 82]):
    left = 20 + i * 295
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, 35, 270, 245)
    f.no_stroke()
    f.fill("#264653")
    f.circle(left + 78, 160, 96)
    f.fill("#e76f51")
    f.circle(left + 215, 123, size)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text("Accent diameter: " + str(size), left, 298)

f.save("02_size.png")
f.show()
