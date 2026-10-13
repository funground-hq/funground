# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")

arrangements = [
    [(78, 110), (160, 145), (215, 80)],
    [(105, 125), (153, 151), (173, 112)],
    [(40, 60), (220, 185), (205, 60)],
]
for i, positions in enumerate(arrangements):
    left = 20 + i * 295
    top = 35
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, top, 270, 245)
    f.no_stroke()
    x, y = positions[0]
    f.fill("#264653")
    f.circle(left + x, top + y, 54)
    x, y = positions[1]
    f.fill("#e76f51")
    f.rect(left + x - 21, top + y - 21, 42, 42)
    x, y = positions[2]
    f.fill("#2a9d8f")
    f.triangle(left + x - 22, top + y + 20,
               left + x + 22, top + y + 20, left + x, top + y - 20)
    f.fill("#264653")
    f.text_size(16)
    f.text_align("left", "top")
    f.text(["Spread apart", "Gathered together", "Pulled to the edges"][i], left, 298)

f.save("01_composition.png")
f.show()
