# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")
for i, (title_size, detail_size, mark_size) in enumerate([(34, 14, 30), (20, 20, 30), (20, 14, 110)]):
    left = 20 + i * 295
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, 35, 270, 245)
    f.no_stroke()
    f.fill("#e76f51")
    f.circle(left + 195, 164, mark_size)
    f.fill("#264653")
    f.text_style("bold")
    f.text_size(title_size)
    f.text_align("left", "top")
    f.text("OPEN DAY", left + 18, 68)
    f.text_style("normal")
    f.text_size(detail_size)
    f.text("Saturday · 10 am", left + 18, 242)
    f.text_size(16)
    f.text(["Title leads", "Similar text sizes", "Image leads"][i], left, 298)

f.save("02_hierarchy.png")
f.show()
