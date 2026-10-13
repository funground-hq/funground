# Original Funground course sketch. CC0; see ../LICENSE.
import funground as f

# Edit one variable at a time, then save another version.
HEADING_SIZE = 36
DETAIL_SIZE = 16
MARK_SIZE = 50
HEADING_Y = 50
MARK_X, MARK_Y = 270, 170
VERSION = "a"

f.size(360, 300)
f.background("#f3efe6")
f.no_stroke()
f.fill("#e76f51")
f.circle(MARK_X, MARK_Y, MARK_SIZE)
f.fill("#264653")
f.text_align("left", "top")
f.text_style("bold")
f.text_size(HEADING_SIZE)
f.text("OPEN DAY", 30, HEADING_Y)
f.text_style("normal")
f.text_size(DETAIL_SIZE)
f.text("Saturday · 10 am", 30, 250)
f.save("02_exercise_" + VERSION + ".png")
f.show()
