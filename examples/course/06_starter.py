# Original Funground course sketch. CC0; see ../LICENSE.

import funground as f

MARGIN = 30
TITLE_SIZE = 42
DETAIL_SIZE = 18

f.size(420, 300)
f.background("#f4f1de")
f.fill("#1d3557")
f.text_align("left", "top")
f.text_style("bold")
f.text_size(TITLE_SIZE)
f.text("FIELD NOTES", MARGIN, 65)
f.text_style("normal")
f.text_size(DETAIL_SIZE)
f.text("Small observations from everyday walks", MARGIN, 145)
f.text_size(14)
f.text("A notebook for noticing", MARGIN, 235)
f.save("06_starter.png")
f.show()
