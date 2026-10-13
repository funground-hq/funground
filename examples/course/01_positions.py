# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

f.size(900, 340)
f.background("#f3efe6")

positions = [(32, 32), (140, 115), (140, 198)]
captions = ["Near two edges", "In the middle", "Low in the frame"]

for i, ((x, y), caption) in enumerate(zip(positions, captions)):
    left = 20 + i * 295
    top = 35
    f.no_fill()
    f.stroke("#b8afa0")
    f.stroke_width(1)
    f.rect(left, top, 270, 245)
    f.no_stroke()
    f.fill("#264653")
    f.circle(left + x, top + y, 42)
    f.text_size(16)
    f.text_align("left", "top")
    f.text(caption, left, 298)

f.save("01_positions.png")
f.show()
