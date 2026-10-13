# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

PAPER = "#f4f1de"
INK = "#1d3557"
ACCENT = "#e76f51"

f.size(420, 300)
f.background(PAPER)
f.no_stroke()
f.fill(ACCENT)
f.circle(340, 75, 55)
f.fill(INK)
f.text_align("left", "top")
f.text_style("bold")
f.text_size(40)
f.text("READ TOGETHER", 28, 125)
f.text_style("normal")
f.text_size(18)
f.text("A weekend reading circle", 28, 185)
f.save("03_starter.png")
f.show()
