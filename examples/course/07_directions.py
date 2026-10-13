# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

f.size(900, 470)
f.background("#ded8cc")
for i in range(3):
    left = 20 + i*295
    f.no_stroke()
    f.fill("#16324f")
    f.rect(left, 20, 270, 390)
    f.fill("#e9c46a")
    cx, cy, diameter = [(135, 145, 135), (218, 290, 32), (190, 185, 115)][i]
    f.circle(left+cx, cy, diameter)
    f.stroke("#f4f1de")
    f.stroke_width(2)
    for row in range(3):
        f.line(left+20, 275+row*18, left+250, 298+row*18)
    f.no_stroke()
    f.fill("#f4f1de")
    f.text_align("left", "top")
    f.text_style("bold")
    title_size, title_y = [(29, 325), (57, 74), (40, 52)][i]
    f.text_size(title_size)
    f.text("NIGHT", left+20, title_y)
    f.text("WALK", left+20, title_y+title_size*1.2)
    f.text_style("normal")
    f.fill("#264653")
    f.text_size(15)
    f.text(["Image leads", "Title leads", "Shared emphasis"][i], left, 430)
f.save("07_directions.png")
f.show()
