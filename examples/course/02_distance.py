# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")
for i, x in enumerate([137, 190, 245]):
    left = 20 + i * 295
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, 35, 270, 245)
    f.no_stroke()
    f.fill("#264653")
    f.circle(left + 78, 165, 96)
    f.fill("#e76f51")
    f.circle(left + x, 114, 30)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text(["Closer to the large circle", "Farther apart", "Near the outer edge"][i], left, 298)

f.save("02_distance.png")
f.show()
