# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

PAPER = "#f4f1de"
INK = "#1d3557"
ACCENT = "#e76f51"

def marks(cx, cy, size):
    f.no_stroke()
    f.fill(ACCENT)
    f.circle(cx-size, cy, size)
    f.circle(cx, cy-size*0.55, size)
    f.circle(cx+size, cy, size)

def piece(width, height, margin, title_size, subtitle, footer, name):
    f.size(width, height)
    f.background(PAPER)
    f.fill(INK)
    f.text_align("left", "top")
    f.text_style("bold")
    f.text_size(title_size)
    f.text("LOOK", margin, margin)
    f.text("AGAIN", margin, margin+title_size*1.2)
    marks(width/2, height*0.52, width*0.09)
    f.fill(INK)
    f.text_style("normal")
    f.text_size(max(11, width*0.045))
    f.text(subtitle, margin, height-90)
    f.text_size(max(10, width*0.035))
    f.text(footer, margin, height-45)
    f.save(name)

piece(320, 450, 26, 48, "A field notebook", "City observations", "11_cover.png")
piece(420, 540, 30, 65, "Sunday · 7 am", "Meet at the town library", "11_poster.png")
piece(160, 480, 16, 25, "Notice one thing", "Keep this place", "11_bookmark.png")

f.size(800, 480)
f.background("#ded8cc")
for name, x, y, width, height, caption in [
    ("11_cover.png", 25, 30, 250, 351, "Notebook"),
    ("11_poster.png", 310, 30, 280, 360, "Invitation"),
    ("11_bookmark.png", 645, 30, 100, 300, "Bookmark"),
]:
    f.image(f.load_image(name), x, y, width, height)
    f.fill(INK)
    f.text_align("left", "top")
    f.text_style("normal")
    f.text_size(17)
    f.text(caption, x, 415)
f.save("11_starter.png")
f.show()
