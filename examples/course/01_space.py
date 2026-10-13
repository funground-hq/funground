# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")

for i, scale in enumerate([0.55, 1.0, 1.65]):
    left = 20 + i * 295
    cx, cy = left + 135, 158
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, 35, 270, 245)
    f.no_stroke()
    f.fill("#264653")
    f.circle(cx - 38 * scale, cy - 35 * scale, 50 * scale)
    f.fill("#e76f51")
    f.rect(cx + 14 * scale, cy - 15 * scale, 42 * scale, 42 * scale)
    f.fill("#2a9d8f")
    f.triangle(cx - 20 * scale, cy + 50 * scale,
               cx + 20 * scale, cy + 50 * scale, cx, cy + 10 * scale)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text(["Small group", "Medium group", "Large group"][i], left, 298)

f.save("01_space.png")
f.show()
