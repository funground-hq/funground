# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(720, 400)
f.background("#f3efe6")
f.no_stroke()
for panel in range(2):
    left = 25 + panel * 355
    f.fill("#264653")
    for row in range(5):
        for col in range(5):
            with f.saved_state():
                f.translate(left + 30 + col * 60, 55 + row * 60)
                angle = 40
                if panel == 1 and (row + col) % 2:
                    angle = -40
                f.rotate(angle)
                f.rect(-17, -4, 34, 8)
    f.text_size(16)
    f.text_align("left", "top")
    f.text(["One direction", "Alternating direction"][panel], left, 360)
f.save("05_patterns.png")
f.show()
