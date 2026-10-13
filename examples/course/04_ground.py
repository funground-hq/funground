# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 330)
f.background("#ded8cc")
settings = [
    ("Dark figure", "#f3efe6", "#264653", False),
    ("Light figure", "#264653", "#f3efe6", False),
    ("A gap becomes part of the figure", "#f3efe6", "#264653", True),
]
for i, (label, paper, ink, cut) in enumerate(settings):
    left = 20 + i * 295
    f.no_stroke()
    f.fill(paper)
    f.rect(left, 20, 270, 245)
    f.fill(ink)
    f.rect(left + 123, 150, 24, 87)
    f.circle(left + 135, 110, 110)
    if cut:
        f.fill(paper)
        f.triangle(left + 135, 88, left + 175, 55, left + 184, 118)
    f.fill("#264653")
    f.text_size(13)
    f.text_align("left", "top")
    f.text(label, left, 286)
f.save("04_ground.png")
f.show()
