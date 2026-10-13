# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

palettes = [
    ("Pale paper", "#f4f1de", "#1d3557", "#e76f51"),
    ("Dark paper", "#16324f", "#f5f0dd", "#edc96b"),
    ("Soft palette", "#eef2e6", "#374939", "#9ab880"),
]
f.size(900, 330)
f.background("#ded8cc")
for i, (label, paper, ink, accent) in enumerate(palettes):
    left = 20 + i * 295
    f.no_stroke()
    f.fill(paper)
    f.rect(left, 20, 270, 250)
    f.fill(accent)
    f.circle(left + 210, 75, 45)
    f.fill(ink)
    f.text_align("left", "top")
    f.text_style("bold")
    f.text_size(28)
    f.text("READ", left + 20, 130)
    f.text_style("normal")
    f.text_size(15)
    f.text("Saturday at 10 am", left + 20, 195)
    f.fill("#264653")
    f.text_size(15)
    f.text(label, left, 290)
f.save("03_palettes.png")
f.show()
