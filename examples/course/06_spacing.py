# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

message = "Look closely. A familiar street can offer unfamiliar shapes, colours and rhythms."
f.size(900, 360)
f.background("#f3efe6")
for i, leading in enumerate([17, 25, 37]):
    left = 20 + i * 295
    f.no_stroke()
    f.fill("#264653")
    f.text_align("left", "top")
    f.text_style("normal")
    f.text_size(20)
    f.text_leading(leading)
    rest = f.text_box(message, left + 20, 65, 220, 230)
    if rest:
        raise ValueError("The text did not fit; give it more room.")
    f.text_size(15)
    f.text("Line distance: " + str(leading), left, 325)
f.save("06_spacing.png")
f.show()
