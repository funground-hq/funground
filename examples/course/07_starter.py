# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

PAPER = "#16324f"
INK = "#f4f1de"
ACCENT = "#e9c46a"
MARGIN = 28

f.size(320, 480)
f.background(PAPER)
f.no_stroke()
f.fill(ACCENT)
f.circle(235, 265, 82)
f.stroke(INK)
f.stroke_width(3)
for row in range(4):
    f.line(MARGIN, 320 + row*18, 292, 350 + row*18)
f.no_stroke()
f.fill(INK)
f.text_align("left", "top")
f.text_style("bold")
f.text_size(48)
f.text("NIGHT", MARGIN, 45)
f.text("WALK", MARGIN, 105)
f.text_style("normal")
f.text_size(17)
f.text("Notes from a city after dark", MARGIN, 190)
f.text_size(14)
f.text("A fictional field notebook", MARGIN, 433)
f.save("07_starter.png")
f.save("07_starter.pdf")
f.show()
