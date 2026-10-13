# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

patterns = [
    ("Steady", [42, 42, 42, 42, 42, 42]),
    ("A longer pause", [30, 30, 90, 30, 30, 30]),
    ("Intervals grow", [18, 27, 36, 45, 54, 63]),
]
f.size(650, 330)
f.background("#f3efe6")
f.no_stroke()
for row, (label, gaps) in enumerate(patterns):
    y = 60 + row * 100
    f.fill("#264653")
    f.text_align("left", "top")
    f.text_size(17)
    f.text(label, 20, y - 9)
    x = 210
    f.circle(x, y, 18)
    for gap in gaps:
        x += gap
        f.circle(x, y, 18)
f.save("05_rhythms.png")
f.show()
