# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 270)
f.background("#f3efe6")
patterns = [[40, 100, 160, 220, 280, 340], [80, 108, 136, 260, 288, 316]]

for i, positions in enumerate(patterns):
    left = 20 + i * 445
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, 30, 420, 175)
    f.no_stroke()
    f.fill("#264653")
    for x in positions:
        f.circle(left + x, 118, 18)
    f.text_size(16)
    f.text_align("left", "top")
    f.text(["Even intervals", "Two clusters"][i], left, 222)

f.save("01_grouping.png")
f.show()
